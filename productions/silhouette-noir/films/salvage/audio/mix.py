"""SALVAGE re-recording mix: narration + score + SFX + layers + beds -> the master.

    python3 films/salvage/audio/mix.py              # narration from films/salvage/audio/vo/narration_full.wav
    python3 films/salvage/audio/mix.py --no-vo      # music / SFX / beds only (M&E); ducking still follows the words
    options: --no-scenes (designed cue sheet only), --no-plot, --outdir DIR, --vo PATH

Outputs, exactly frames / fps * 48000 = 8,712,000 samples (181.5 s), under films/salvage/out/:
    audio_master.wav               48 kHz stereo 24-bit PCM, -14 LUFS integrated, <= -1 dBTP
    stems/{vo,music,sfx,amb}.wav   32-bit float, post-ducking, at the master gain, pre-limiter
    audio_report.json              loudness, true peak, per-scene levels, cue list, merge log, arc, QA
    audio_overview.png             loudness curve, scene boundaries, the hit list, designed silences
--no-vo writes audio_master_no_vo.wav, audio_report_no_vo.json, audio_overview_no_vo.png and
stems_no_vo/, so an M&E pass never overwrites the master.

Signal flow
    narration  per line: the take's src_t0..src_t1 padded 40 ms each side (8 ms fades), placed at the
               line's film start - 40 ms; HPF 80 Hz, 2.2:1 compression, -16 LUFS, dialogue limiter -4 dBTP
    cues       cuesheet.build(): the designed cue sheet merged with the scenes' cues; each rendered
               from sfx_salvage with its anchor on the cue time, panned, low-passed through the water
               when heard underwater (the cutoff falls with depth), sent to its acoustic space's reverb
    layers     helmet breathing + exhaust bubbles, the free-flow hiss, the deck pump, the winch,
               bubble streams, the breathing heard up the hose on deck (it stops dead at the cut)
    beds       ambience.render_beds(); score.render_score() (main + feature buses, the heartbeat)
    ducking    from the narration's word times + envelope: music -8 dB, feature -4, SFX -3, layers -4,
               beds -2, designed hits -1.5; 30 ms attack, 250 ms release, 60 ms look-ahead
    master     HPF 30 Hz, glue compressor, gain iterated to -14 LUFS through a 4x-oversampled
               true-peak limiter at -1.25 dBTP (ceiling -1 dBTP), end fade
Without narration a speech-shaped proxy on the word times stands in for the voice when the master
gain is computed, so music / SFX / beds come out at their final levels.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402

from audio import dsp  # noqa: E402
from audio.dsp import SR, db2lin, n_of  # noqa: E402
from films.salvage.audio import ambience as AM  # noqa: E402
from films.salvage.audio import cuesheet as CS  # noqa: E402
from films.salvage.audio import qa as QA  # noqa: E402
from films.salvage.audio import score as SC  # noqa: E402
from films.salvage.audio import sfx_salvage as S  # noqa: E402

OUT = os.path.join(ROOT, "films", "salvage", "out")
VO_DEFAULT = os.path.join(HERE, "vo", "narration_full.wav")

VO_TARGET = -16.0            # narration stem, integrated (pre-master)
VO_PEAK_DBTP = -4.0          # dialogue limiter: plosives are held here, not by the master limiter
VO_PAD, VO_FADE, VO_HPF = 0.040, 0.008, 80.0
VO_LEVEL_KEEP = 0.6          # line leveller: each line keeps 60 % of its deviation from the median line

BUS_DB = dict(music=1.5, feature=0.0, sfx=0.0, hits=0.0, layers=0.0, amb=0.0)      # bus trims
DUCK = dict(music=-8.0, feature=-4.0, sfx=-3.0, hits=-1.5, layers=-4.0, amb=-2.0)
ATTACK, RELEASE, LOOKAHEAD, BRIDGE, RATE = 0.03, 0.25, 0.06, 0.30, 1000
MASTER_LUFS, CEILING_DBTP, LIMIT_AT = -14.0, -1.0, -1.25
END_GATE = (180.6, 181.25)   # the last sounds decay into the black (from 180.7), then silence

# reverb send (wet dB for a sound with spec space 1.0) per acoustic space
SEND_DB = dict(dusk_air=-12.0, night_air=-10.0, underwater=-6.0, wreck=-4.0, paper=-16.0)
# continuous layers: loudness of each generated track at span gain 0 dB (LUFS, active parts)
LAYER_LUFS = dict(breath=-24.0, bubbles=-27.0, hiss=-33.0, hose=-28.0, pump=-20.0, winch=-21.0)

_T0 = [time.time()]


def log(msg):
    print(f"[mix {time.time() - _T0[0]:6.1f}s] {msg}", flush=True)


# ============================================================================ helpers
def _lufs(x):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    return dsp.loudness_integrated(x) if len(x) >= n_of(0.4) else -np.inf


def _calib(x, target, ref=None):
    """Scale x so that its (or ref's) integrated loudness is `target`."""
    lv = _lufs(x if ref is None else ref)
    return (x * db2lin(target - lv), lv) if np.isfinite(lv) else (x, lv)


def _span_env(n, fin, fout):
    e = np.ones(n)
    a, b = min(n, n_of(fin)), min(n, n_of(fout))
    if a > 1:
        e[:a] = np.sin(0.5 * np.pi * np.linspace(0.0, 1.0, a))
    if b > 1:
        e[n - b:] *= np.cos(0.5 * np.pi * np.linspace(0.0, 1.0, b))
    return e


def _db_curve(points, t, default=0.0):
    if not points:
        return np.full(len(t), default)
    pts = sorted(points)
    return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])


def _send(sends, space, mono, at, gain=1.0):
    """Add a mono signal to an acoustic space's reverb send (one return per space, on the SFX bus)."""
    if space not in SEND_DB:
        return
    if space not in sends:
        sends[space] = np.zeros(sends["_N"], dtype=np.float32)
    dsp.mix_into(sends[space], np.asarray(mono, dtype=np.float32), at, gain)


def _r(v, k=2):
    return None if v is None or not np.isfinite(v) else round(float(v), k)


# ============================================================================ narration
def load_vo(path, C, N):
    """The narration stem (N, 2) float32, centred, -16 LUFS, and its info / edit list."""
    src, sr = dsp.read_audio(path, sr_out=SR)
    src = dsp.mono(src)
    info = dict(path=os.path.relpath(path, ROOT), source_seconds=round(len(src) / SR, 3))
    src = dsp.sos(src, "highpass", VO_HPF, 2)
    lv = _lufs(src)
    if np.isfinite(lv):
        src = src * db2lin(-20.0 - lv)
    src = dsp.compressor(src, thresh_db=-24.0, ratio=2.2, attack_ms=8.0, release_ms=120.0, knee_db=6.0, mode="rms")
    vo = np.zeros(N)
    edits, pieces = [], []
    for v in C.tl["vo"]:
        a = max(0.0, float(v["src_t0"]) - VO_PAD)
        b = min(len(src) / SR, float(v["src_t1"]) + VO_PAD)
        if b <= a:
            continue
        seg = dsp.fade(src[n_of(a):n_of(b)], VO_FADE, VO_FADE)
        dst = float(v["start"]) - (float(v["src_t0"]) - a)
        pieces.append((v, a, b, dst, seg, _lufs(seg)))
    # gentle line leveller: the performance's shape stays, the outliers come 40 % of the way in
    lv_ok = [p[5] for p in pieces if np.isfinite(p[5])]
    med = float(np.median(lv_ok)) if lv_ok else 0.0
    for v, a, b, dst, seg, lvl in pieces:
        gdb = (VO_LEVEL_KEEP - 1.0) * (lvl - med) if np.isfinite(lvl) else 0.0
        dsp.mix_into(vo, seg * db2lin(gdb), n_of(dst))
        edits.append(dict(line=v["n"], film_in=round(dst, 3), film_out=round(dst + len(seg) / SR, 3),
                          src_in=round(a, 3), src_out=round(b, 3), level_db=_r(gdb), text=v["text"][:48]))
    vo2 = np.stack([vo, vo], axis=1)
    del vo
    lv = dsp.loudness_integrated(vo2)
    vo2 *= db2lin(VO_TARGET - lv)
    vo2, vg = dsp.limiter(vo2, VO_PEAK_DBTP, lookahead_ms=1.5, release_ms=60.0, return_gain=True)
    info["dialogue_limiter_gr_db_max"] = _r(-dsp.lin2db(np.min(vg)))
    vo2 *= db2lin(VO_TARGET - dsp.loudness_integrated(vo2))
    info.update(lines=len(edits), stem_lufs=_r(dsp.loudness_integrated(vo2)), stem_tp=_r(dsp.true_peak_db(vo2)))
    info["edits"] = edits
    return vo2.astype(np.float32), info


def vo_proxy(C, N):
    """Speech-shaped noise on the word times: the voice's stand-in for the master gain (--no-vo)."""
    rng = np.random.default_rng(dsp.stable_seed("salvage-vo-proxy"))
    x = dsp.bandpass(dsp.pink(N, rng), 140.0, 5000.0, 2)
    x = 0.55 * x + 0.45 * dsp.onepole_lp(x, 1200.0)
    x *= 0.35 + 0.65 * np.abs(dsp.smooth_noise(N, 4.5, rng))
    gate = np.zeros(N)
    for v in C.tl["vo"]:
        for w in v["words"]:
            gate[n_of(w["t0"]):n_of(w["t1"])] = 1.0
    x *= dsp.onepole_lp(gate, 25.0)
    x = np.stack([x, x], axis=1)
    return (x * db2lin(VO_TARGET - dsp.loudness_integrated(x))).astype(np.float32)


# ============================================================================ ducking
def activity(C, N, vo=None):
    """0/1 voice activity at RATE Hz: the words (60 ms look-ahead), OR'd with the narration's own
    envelope when present; gaps shorter than BRIDGE are bridged."""
    from scipy.ndimage import binary_closing
    n = int(N / SR * RATE) + 2
    act = np.zeros(n, dtype=bool)
    for v in C.tl["vo"]:
        for w in v["words"]:
            act[max(0, int((w["t0"] - LOOKAHEAD) * RATE)):min(n, int(w["t1"] * RATE) + 1)] = True
    if vo is not None:
        hop = SR // RATE
        m = vo[: (len(vo) // hop) * hop, 0].astype(np.float64).reshape(-1, hop)
        lv = dsp.lin2db(np.sqrt(np.mean(m * m, axis=1)))
        env = np.zeros(n, dtype=bool)
        env[:len(lv)] = lv > np.max(lv) - 32.0
        k = int(LOOKAHEAD * RATE)
        act |= np.concatenate([env[k:], np.zeros(k, dtype=bool)]) | env
    act = binary_closing(act, structure=np.ones(int(BRIDGE * RATE)))
    return act.astype(np.float64)


def duck_curves(act, N):
    ta = np.arange(len(act)) / RATE
    tn = np.arange(N) / SR
    out = {}
    for k, depth in DUCK.items():
        g = dsp.duck_gain(act, depth, ATTACK, RELEASE, RATE)
        out[k] = np.interp(tn, ta, g).astype(np.float32)
    return out


# ============================================================================ cues
def _xwater(x, t_place, t_sw, dur):
    """The bell keeps ringing as the camera goes under: the dry bell crossfades (equal power, from
    t_sw over dur) into its low-passed version in the bell_water reverb."""
    n = len(x)
    k0 = n_of(t_sw - t_place)
    if k0 >= n:
        return x
    u = np.clip((np.arange(n) - k0) / max(1, n_of(dur)), 0.0, 1.0)
    uw = S.underwater(x, 700.0, lift_db=0.0)
    uw = uw * db2lin(-8.0) + S.wet(uw, "bell_water", -16.0)[:n]       # an echo under s16's narration
    return x * np.cos(0.5 * np.pi * u)[:, None] + uw * np.sin(0.5 * np.pi * u)[:, None]


def _fade_window(x, t_place, ta, tb):
    n = len(x)
    t = t_place + np.arange(n) / SR
    g = np.cos(0.5 * np.pi * np.clip((t - ta) / max(tb - ta, 1e-3), 0.0, 1.0))
    k = min(n, max(0, n_of(tb - t_place) + 1))
    return (x * g[:, None])[:k]


def render_cues(C, cues, N, sends):
    buses = dict(sfx=np.zeros((N, 2), dtype=np.float32), hits=np.zeros((N, 2), dtype=np.float32))
    rows, problems = [], []
    for c in cues:
        name = c["name"]
        sp = S.spec(name)
        try:
            x = S.render(name, dur=c.get("dur"), params=c.get("params") or None, seed=int(c.get("seed") or 0))
        except Exception as e:                    # noqa: BLE001 - one bad cue must not stop the mix
            problems.append(dict(t=c["t"], name=name, error=f"{type(e).__name__}: {e}"[:200]))
            continue
        x = x.astype(np.float64)
        anc = S.anchor(name, c.get("params"))
        t0 = float(c["t"]) - anc
        space = c.get("space") or CS.space_at(C, c["t"])
        muffled = space in CS.UNDERWATER and sp.get("muffle", True)
        if muffled:
            x = S.underwater(x, CS.muffle_fc(CS.depth_at(C, c["t"])))
        if c.get("pan"):
            x = dsp.pan_stereo(x, float(np.clip(c["pan"], -1, 1)))
        x *= db2lin(float(c["gain_db"]))
        if c.get("xwater"):
            x = _xwater(x, t0, *c["xwater"])
        if c.get("fade"):
            x = _fade_window(x, t0, *c["fade"])
        bus = c.get("bus") if c.get("bus") in buses else ("hits" if sp.get("hit") else "sfx")
        dsp.mix_into(buses[bus], x.astype(np.float32), n_of(t0))
        f = float(sp.get("space", 1.0) or 0.0)
        if f > 0 and space in SEND_DB:
            _send(sends, space, x.mean(axis=1), n_of(t0), f)
        rows.append(dict(t=round(float(c["t"]), 3), name=name, label=c.get("label") or name, gain_db=round(float(c["gain_db"]), 1),
                         kind=c.get("kind"), src=c.get("src"), scene=c.get("scene") or C.scene_at(c["t"]), bus=bus,
                         space=space, muffled=bool(muffled), anchor=round(anc, 3), seconds=round(len(x) / SR, 2),
                         params=c.get("params") or {}))
    return buses, rows, problems


# ============================================================================ continuous layers
def render_layers(C, built, N, sends):
    """lay (breathing, bubbles, hiss, hose breath: the 'layers' bus) and deck (pump, winch: SFX bus)."""
    lay = np.zeros((N, 2), dtype=np.float32)
    deck = np.zeros((N, 2), dtype=np.float32)
    rng = np.random.default_rng(dsp.stable_seed("salvage-mix-layers"))
    L = CS.layers(C)
    info = {}

    # ---- the diver's breathing (inside the helmet) and his exhaust bubbles (outside)
    ev, gain = CS.breath_events(C, sync=built["breath_sync"])
    br, bub = S.breathing_track(ev, N, seed=7)
    br, lb = _calib(br, LAYER_LUFS["breath"])
    bub, lu = _calib(bub, LAYER_LUFS["bubbles"])
    g = db2lin(_db_curve(gain, np.arange(N) / SR))
    br *= g
    bub *= g
    del g
    lay += br.astype(np.float32)[:, None]
    del br
    lay += dsp.decorrelate(bub, rng, amount=0.35).astype(np.float32)
    _send(sends, "underwater", bub, 0, db2lin(-1.0))
    del bub
    info["breathing"] = dict(events=len(ev), raw_lufs=[_r(lb), _r(lu)], synced_to=built["breath_sync"])

    # ---- free-flow hiss (pulsing with the pump), ducked through the s09 spiral
    for k, sp in enumerate(L["hiss"]):
        a, b = max(0, n_of(sp["t0"])), min(N, n_of(sp["t1"]))
        n = b - a
        if n <= n_of(0.5):
            continue
        x, _ = _calib(S.hiss_track(n, rng, 26.0), LAYER_LUFS["hiss"])
        x *= _span_env(n, sp["fin"], sp["fout"]) * db2lin(sp["gain"])
        pts = [(0.0, 0.0), (C.duration, 0.0)]
        for d0, d1, ddb in L["hiss_duck"]:
            pts += [(d0 - 0.3, 0.0), (d0, ddb), (d1, ddb), (d1 + 0.3, 0.0)]
        x *= db2lin(_db_curve(pts, (a + np.arange(n)) / SR))
        dsp.mix_into(lay, dsp.decorrelate(x, rng, amount=0.3).astype(np.float32), a)
    info["hiss_spans"] = [(round(s["t0"], 2), round(s["t1"], 2), s["gain"]) for s in L["hiss"]]

    # ---- the deck pump (s02-s03 dusk, s12 night: blowing out of the cut hose, running down)
    for k, sp in enumerate(L["pump"]):
        a, b = max(0, n_of(sp["t0"])), min(N, n_of(sp["t1"]))
        n = b - a
        t0 = a / SR
        ra = None if sp.get("rundown_at") is None else sp["rundown_at"] - t0
        oa = None if sp.get("open_after") is None else sp["open_after"] - t0
        x = S.pump_track(n, rng, 26.0, sp.get("spinup", 1.5), ra, sp.get("rundown", 3.2), oa)
        ref = x[:n_of(ra)] if ra is not None and n_of(ra) > n_of(1.0) else None
        x, _ = _calib(x, LAYER_LUFS["pump"], ref)
        x *= _span_env(n, sp["fin"], sp["fout"]) * db2lin(sp["gain"])
        xs = dsp.pan_stereo(dsp.decorrelate(x, rng, amount=0.25), -0.25)
        dsp.mix_into(deck, xs.astype(np.float32), a)
        _send(sends, sp["space"], x, a)
    # ---- the winch (s12 hauling the line tight; s14 hauling up the "safe")
    for k, sp in enumerate(L["winch"]):
        a, b = max(0, n_of(sp["t0"])), min(N, n_of(sp["t1"]))
        n = b - a
        x = dsp.sos(S.winch_track(n, rng, sp["rate"], sp["load"]), "lowpass", 6500.0, 2)
        x, _ = _calib(x, LAYER_LUFS["winch"])
        x *= _span_env(n, sp["fin"], sp["fout"]) * db2lin(sp["gain"])
        xs = dsp.pan_stereo(dsp.decorrelate(x, rng, amount=0.2), 0.2)
        dsp.mix_into(deck, xs.astype(np.float32), a)
        _send(sends, sp["space"], x, a)
    # ---- bubble streams (s01 rising to the surface, s11 up the line)
    for k, sp in enumerate(L["bubbles"]):
        a, b = max(0, n_of(sp["t0"])), min(N, n_of(sp["t1"]))
        n = b - a
        x = S.render("bubble_stream", dur=n / SR, params=dict(density=sp["density"]), seed=40 + k).astype(np.float64)[:n]
        x *= (_span_env(len(x), sp["fin"], sp["fout"]) * db2lin(sp["gain"]))[:, None]
        dsp.mix_into(lay, x.astype(np.float32), a)
        _send(sends, "underwater", x.mean(axis=1), a, 0.4)

    # ---- s12: his breathing heard up the hose on deck - it stops dead on the cut
    ev, t_cut = CS.hose_breath_events(C)
    t0 = C.g("s12", 0.0)
    a = n_of(t0)
    n = n_of(t_cut + 0.4) - a
    br, _ = S.breathing_track([dict(e, t=e["t"] - t0) for e in ev], n, seed=12)
    br = dsp.bandpass(br, 300.0, 3000.0, 2)
    k = n_of(t_cut - t0)
    br, _ = _calib(br, LAYER_LUFS["hose"], br[:k])
    env = _span_env(n, 0.6, 0.0)
    r = n_of(0.005)
    env[k - r:k] *= np.cos(0.5 * np.pi * np.linspace(0.0, 1.0, r))
    env[k:] = 0.0
    dsp.mix_into(lay, dsp.pan_mono(br * env, -0.1).astype(np.float32), a)
    info["hose_breath"] = dict(events=len(ev), stops_at=round(t_cut, 3))
    return lay, deck, info


def apply_sends(sends, bus):
    """Convolve each space's send (active regions only) into the SFX bus; returns LUFS per return."""
    info = {}
    for space in sorted(k for k in sends if k != "_N"):
        send = sends[space]
        if not np.any(send):
            continue
        wet = AM.sparse_wet(send, space, SEND_DB[space])
        bus += wet.astype(np.float32)
        info[space] = _r(_lufs(wet))
        del wet
    return info


def precut_silences(C, built, N):
    """A scene's 'silence' instruction in the last second before a hard cut: everything but the
    voice drops out there (60 ms) and stays out until the cut. Returns (gate float32, windows)."""
    gate = np.ones(N, dtype=np.float32)
    wins = []
    for e in built["log"]:
        if e.get("event") != "instruction" or "silen" not in e.get("text", "").lower():
            continue
        sd = next((x for x in C.scenes if x["id"] == e["scene"]), None)
        if sd is None or sd.get("trans_out") or not sd.get("next"):
            continue
        cut = sd["start"] + sd["duration"]
        t = float(e["t"])
        if not (0.0 < cut - t <= 1.0):
            continue
        a, b = n_of(t), n_of(cut)
        f = min(n_of(0.06), b - a)
        gate[a:a + f] = np.minimum(gate[a:a + f], np.cos(0.5 * np.pi * np.linspace(0.0, 1.0, f)))
        gate[a + f:b] = 0.0
        wins.append((round(t, 3), round(cut, 3)))
    return gate, wins


# ============================================================================ master
def master_chain(pre, ref):
    """pre: the mix to master; ref: the same mix with the narration (or its proxy), used for every
    level decision. Returns (master, info, per-sample gain applied before the limiter)."""
    info = {}
    pre = dsp.sos(pre, "highpass", 30.0, 2)
    ref = dsp.sos(ref, "highpass", 30.0, 2)
    l0 = dsp.loudness_integrated(ref)
    g1 = db2lin(-18.0 - l0)
    _, cg = dsp.compressor(ref * g1, thresh_db=-12.0, ratio=1.6, attack_ms=20.0, release_ms=300.0, knee_db=8.0,
                           mode="rms", return_gain=True)
    info["glue_gr_db_max"] = _r(-dsp.lin2db(np.min(cg)))
    pre *= g1 * cg[:, None]
    ref *= g1 * cg[:, None]
    gain_db = MASTER_LUFS - dsp.loudness_integrated(ref)
    for it in range(5):
        lv = dsp.loudness_integrated(dsp.limiter(ref * db2lin(gain_db), LIMIT_AT, lookahead_ms=2.5, release_ms=90.0))
        info[f"iter{it}"] = dict(gain_db=_r(gain_db, 3), lufs=_r(lv, 3))
        if abs(lv - MASTER_LUFS) < 0.03:
            break
        gain_db += MASTER_LUFS - lv
    del ref
    out, lim_g = dsp.limiter(pre * db2lin(gain_db), LIMIT_AT, lookahead_ms=2.5, release_ms=90.0, return_gain=True)
    info["limiter_gr_db_max"] = _r(-dsp.lin2db(np.min(lim_g)))
    info["limiter_active_seconds"] = _r(float(np.sum(lim_g < db2lin(-0.1))) / SR, 2)
    tp = dsp.true_peak_db(out)
    if tp > CEILING_DBTP - 0.02:
        out *= db2lin(CEILING_DBTP - 0.05 - tp)
        info["post_trim_db"] = _r(CEILING_DBTP - 0.05 - tp, 3)
    out = dsp.fade(out, 0.002, 0.25)
    info["gain_db"] = _r(gain_db + dsp.lin2db(g1), 3)
    return out, info, (g1 * cg * db2lin(gain_db)).astype(np.float32)


# ============================================================================ measurement
def _seg_lufs(x, a, b):
    return dsp.loudness_integrated(x[max(0, n_of(a)):n_of(b)]) if n_of(b) - n_of(a) >= n_of(0.4) else -np.inf


def _curve_at(t, l, a, b, fn=np.max):
    m = (t >= a) & (t <= b)
    return float(fn(l[m])) if m.any() else -np.inf


def onsets(x, a, b, rise_db=9.0, floor_db=-50.0):
    """Count transient onsets (20 ms RMS rising > rise_db within 100 ms, 120 ms refractory)."""
    seg = np.asarray(x[n_of(a):n_of(b)], dtype=np.float64)
    if seg.ndim == 2:
        seg = seg.mean(axis=1)
    hop = n_of(0.02)
    k = len(seg) // hop
    if k < 6:
        return 0
    e = dsp.lin2db(np.sqrt(np.mean(seg[:k * hop].reshape(k, hop) ** 2, axis=1)))
    cnt, last = 0, -100
    for i in range(5, k):
        if e[i] > floor_db and e[i] - np.min(e[i - 5:i]) > rise_db and i - last > 6:
            cnt += 1
            last = i
    return cnt


def annotate_clicks(clicks, rows, vo_info):
    """Name the likely source of each detected transient: the cue sounding there (nearest onset),
    else the narration, else the score / beds. Designed transients (pawls, pops, strikes) are
    expected; an unexplained one is worth a listen."""
    edits = (vo_info or {}).get("edits", [])
    out = []
    for c in clicks:
        t = c["t"]
        near = [r for r in rows if r["t"] - r["anchor"] - 0.03 <= t <= r["t"] - r["anchor"] + r["seconds"]]
        near.sort(key=lambda r: abs(r["t"] - r["anchor"] - t))
        if near:
            src = f"{near[0]['name']} @{near[0]['t']}"
        elif any(e["film_in"] <= t <= e["film_out"] for e in edits):
            src = "narration"
        else:
            src = "score/beds"
        out.append(dict(c, source=src))
    return out


def measure(C, master, stems, act, cue_rows, sinfo):
    rep = {}
    tm, lm = dsp.loudness_curve(master, win=0.4, hop=0.05)
    ts, ls = dsp.loudness_curve(master, win=3.0, hop=0.1)
    nonvo = stems["music"].astype(np.float64) + stems["sfx"] + stems["amb"]
    # ---- per scene
    per = {}
    for s in C.scenes:
        a, b = s["start"], s["start"] + s["duration"]
        row = dict(start=a, end=b, lufs=_r(_seg_lufs(master, a, b)), short_term_max=_r(_curve_at(ts, ls, a, b)),
                   momentary_max=_r(_curve_at(tm, lm, a, b)),
                   true_peak=_r(dsp.true_peak_db(master[n_of(a):n_of(b)])))
        for k, x in stems.items():
            row[f"{k}_lufs"] = _r(_seg_lufs(x, a, b))
        row["no_vo_lufs"] = _r(_seg_lufs(nonvo, a, b))
        per[s["id"]] = row
    rep["per_scene"] = per
    # ---- narration vs music while the narration speaks
    if np.any(stems["vo"]):
        tv, lv = dsp.loudness_curve(stems["vo"], win=0.4, hop=0.1)
        _, lmu = dsp.loudness_curve(stems["music"], win=0.4, hop=0.1)
        ins = np.array([act[max(0, int((x - 0.2) * RATE)):int((x + 0.2) * RATE)].min() > 0.5 for x in tv])
        ok = ins & (lv > -60) & (lmu > -70)
        d = lv[ok] - lmu[ok]
        _, lsf = dsp.loudness_curve(stems["sfx"].astype(np.float64) + stems["amb"], win=0.4, hop=0.1)
        ok2 = ins & (lv > -60) & (lsf > -70)
        d2 = lv[ok2] - lsf[ok2]
        rep["vo_balance"] = dict(blocks=int(ok.sum()), vo_minus_music_median_lu=_r(np.median(d)) if len(d) else None,
                                 vo_minus_music_iqr=[_r(np.percentile(d, 25)), _r(np.percentile(d, 75))] if len(d) else None,
                                 vo_minus_sfx_amb_median_lu=_r(np.median(d2)) if len(d2) else None)
    # ---- the loudness arc
    g, w = C.g, C.w
    arc = {}
    arc["hook_s01"] = dict(lufs=per["s01"]["lufs"], momentary_max=per["s01"]["momentary_max"], onsets=onsets(nonvo, 0, 10))
    lowb = dsp.sos((stems["music"].astype(np.float64) + stems["amb"]).mean(axis=1), "lowpass", 120.0, 4)
    wins = [("s03 surface", g("s03", 1.0), g("s03", 5.0)), ("s03 descent", g("s03", 6.0), g("s03", 13.0)),
            ("s05 the wreck", g("s05", 0.5), g("s05", 13.0)), ("s06 the holes", g("s06", 0.0), g("s06", 7.9)),
            ("s08 the shaft", g("s08", 1.0), g("s08", 9.5)), ("s11 two tugs", g("s11", 0.0), g("s11", 7.0))]
    arc["descending_pressure_low_band_db"] = {nm: _r(dsp.rms_db(lowb[n_of(a):n_of(b)]), 1) for nm, a, b in wins}
    del lowb
    arc["paper_rhythm_onsets_per_10s"] = {sid: round(onsets(nonvo, C.start(sid), C.end(sid)) * 10.0 / (C.end(sid) - C.start(sid)), 1)
                                          for sid in ("s03", "s04", "s05", "s07", "s08", "s09")}
    safe = next((c["t"] for c in cue_rows if c["name"] == "safe_open"), g("s09", 7.45))
    arc["discovery_s09"] = dict(safe_open=round(safe, 2), momentary_at_door=_r(_curve_at(tm, lm, safe - 0.2, safe + 0.8)),
                                s08_short_term_median=_r(_curve_at(ts, ls, C.start("s08"), C.end("s08"), np.median)))
    cut = w("s12", "cut")
    _, lmus = dsp.loudness_curve(stems["music"], win=0.4, hop=0.05)
    tn, lnv = dsp.loudness_curve(nonvo, win=0.4, hop=0.05)
    arc["the_cut"] = dict(t=round(cut, 3), music_before=_r(_curve_at(tm, lmus, cut - 1.5, cut - 0.3, np.median)),
                          music_after=_r(_curve_at(tm, lmus, cut + 0.3, cut + 9.0, np.max)),
                          no_vo_momentary_peak_at_cut=_r(_curve_at(tn, lnv, cut - 0.1, cut + 0.5)),
                          no_vo_s13_median=_r(_curve_at(tn, lnv, C.start("s13") + 0.3, w("s13", "calm"), np.median)),
                          no_vo_film_median=_r(float(np.median(lnv[lnv > -70]))))
    b_in = next((c["t"] for c in cue_rows if c["name"] == "breath_single" and c["params"].get("phase") == "in"), None)
    b_out = next((c["t"] for c in cue_rows if c["name"] == "breath_single" and c["params"].get("phase") == "out"), None)
    if b_in and b_out:
        _, lsx = dsp.loudness_curve(stems["sfx"], win=0.4, hop=0.05)
        arc["one_breath_s13"] = dict(t_in=round(b_in, 2), t_out=round(b_out, 2), sfx_in=_r(_curve_at(tm, lsx, b_in, b_in + 1.0)),
                                     sfx_out=_r(_curve_at(tm, lsx, b_out, b_out + 1.4)),
                                     sfx_before=_r(_curve_at(tm, lsx, b_in - 3.0, b_in - 0.3, np.median)))
    tolls = [c["t"] for c in cue_rows if c["name"] == "meridian_bell"]
    i_max = int(np.argmax(lm))
    arc["the_bell"] = dict(tolls=[round(t, 3) for t in tolls],
                           momentary_at_tolls=[_r(_curve_at(tm, lm, t - 0.1, t + 1.2)) for t in tolls],
                           film_momentary_max=_r(lm[i_max]), film_momentary_max_at=round(float(tm[i_max]), 2),
                           toll2_is_loudest=bool(tolls and abs(float(tm[i_max]) - tolls[-1]) < 1.5))
    if tolls:
        far = np.abs(tm - tolls[-1]) > 2.0
        arc["the_bell"]["toll2_margin_over_rest_lu"] = _r(_curve_at(tm, lm, tolls[-1] - 0.1, tolls[-1] + 1.2) - float(np.max(lm[far])))
    arc["resonant_fade_s16"] = dict(short_term={f"{t:.0f}": _r(_curve_at(ts, ls, t - 0.05, t + 0.05)) for t in (167, 171, 175, 178, 180)},
                                    last_0_8s_momentary_max=_r(_curve_at(tm, lm, C.duration - 0.6, C.duration)))
    rep["arc"] = arc
    return rep


# ============================================================================ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vo", default=VO_DEFAULT, help="narration file (default films/salvage/audio/vo/narration_full.wav)")
    ap.add_argument("--no-vo", action="store_true", help="mix without narration (M&E)")
    ap.add_argument("--no-scenes", action="store_true", help="ignore the scenes' cues (designed cue sheet only)")
    ap.add_argument("--outdir", default=OUT)
    ap.add_argument("--no-plot", action="store_true")
    a = ap.parse_args(argv)
    _T0[0] = time.time()
    sfx_ = "_no_vo" if a.no_vo else ""
    out_dir = os.path.abspath(a.outdir)
    stem_dir = os.path.join(out_dir, "stems" + sfx_)
    os.makedirs(stem_dir, exist_ok=True)

    C = CS.Clock()
    N = int(round(C.frames * SR / C.fps))
    report = dict(film="salvage", title="SALVAGE", frames=C.frames, fps=C.fps, samples=N, seconds=N / SR, sample_rate=SR,
                  with_vo=not a.no_vo)
    log(f"SALVAGE: {C.frames} frames @ {C.fps:g} fps -> {N} samples ({N / SR:.3f} s)")

    # ---- narration
    vo = None
    if not a.no_vo:
        if not os.path.exists(a.vo):
            raise SystemExit(f"narration not found: {a.vo} (use --no-vo for an M&E mix)")
        vo, report["vo"] = load_vo(a.vo, C, N)
        log(f"narration: {report['vo']['lines']} lines, {report['vo']['stem_lufs']} LUFS, TP {report['vo']['stem_tp']} dBTP")
    act = activity(C, N, vo)

    # ---- cue sheet (designed + scenes)
    built = CS.build(C, use_scenes=not a.no_scenes)
    ev_count = {}
    for e in built["log"]:
        ev_count[e["event"]] = ev_count.get(e["event"], 0) + 1
    report["cue_merge"] = dict(scenes_with_cues=built["have"], events=ev_count, breath_sync=built["breath_sync"],
                               heartbeat_sync=built["heart"], log=built["log"])
    log(f"cues: {len(built['cues'])} (scenes with cues: {', '.join(built['have']) or 'none'}; {ev_count})")
    sends = {"_N": N}
    buses, rows, problems = render_cues(C, built["cues"], N, sends)
    report["cue_problems"] = problems
    log(f"cues rendered ({len(rows)} ok, {len(problems)} failed)")

    # ---- layers
    lay, deck, linfo = render_layers(C, built, N, sends)
    buses["layers"] = lay
    buses["sfx"] += deck
    del deck
    report["layers"] = linfo
    log("layers rendered")
    report["sends_lufs"] = apply_sends(sends, buses["sfx"])
    del sends
    log("reverb sends convolved")

    # ---- beds and score
    amb, binfo = AM.render_beds(C)
    report["beds"] = binfo.get("beds")
    log(f"beds rendered ({_r(_lufs(amb))} LUFS)")
    beats, strengths = CS.heartbeat_plan(C)
    if built["heart"]:
        beats = sync_heart(beats, built["heart"])
    main_m, feat, sinfo = SC.render_score(C, heart=(beats, strengths))
    report["score"] = dict(events=sinfo["events"], strings=sinfo["strings"], silences=sinfo["silences"],
                           marks=[(round(t, 3), lb) for t, lb in sinfo["marks"]], heartbeats=len(beats),
                           heartbeat_span=[round(beats[0], 2), round(beats[-1], 2)] if beats else None)
    log(f"score rendered ({sinfo['events']} one-shots, {sinfo['strings']} string notes)")

    # ---- trims, ducking, end gate
    duck = duck_curves(act, N)
    end = np.ones(N, dtype=np.float32)
    ea, eb = n_of(END_GATE[0]), n_of(END_GATE[1])
    end[ea:eb] = np.cos(0.5 * np.pi * np.linspace(0.0, 1.0, eb - ea))
    end[eb:] = 0.0
    pc, pc_wins = precut_silences(C, built, N)
    end *= pc
    report["precut_silences"] = pc_wins
    for nm, x in (("music", main_m), ("feature", feat), ("amb", amb)):
        x *= (duck[nm] * end * np.float32(db2lin(BUS_DB[nm])))[:, None]
    for nm in ("sfx", "hits", "layers"):
        buses[nm] *= (duck[nm] * end * np.float32(db2lin(BUS_DB[nm])))[:, None]
    report["ducking_db"] = DUCK
    report["voice_active_seconds"] = _r(float(np.sum(act)) / RATE, 1)
    del duck, end
    music = main_m + feat
    del main_m, feat
    sfx = buses["sfx"] + buses["hits"] + buses["layers"]
    stems_pre = dict(vo=vo if vo is not None else np.zeros((N, 2), dtype=np.float32), music=music, sfx=sfx, amb=amb)
    report["stems_pre_master_lufs"] = {k: _r(_lufs(x)) for k, x in stems_pre.items()}
    report["buses_pre_master_lufs"] = {k: _r(_lufs(x)) for k, x in buses.items()}
    del buses
    log(f"stems pre-master LUFS: {report['stems_pre_master_lufs']}")

    # ---- master
    pre = music.astype(np.float64) + sfx + amb
    if vo is not None:
        pre += vo
        ref = pre.copy()
    else:
        ref = pre + vo_proxy(C, N)
    master, minfo, gain = master_chain(pre, ref)
    del pre, ref
    master = dsp.pad_to(master, N)
    report["master_chain"] = minfo
    log(f"mastered: gain {minfo['gain_db']} dB, limiter GR max {minfo['limiter_gr_db_max']} dB")
    stems = {}
    for k, x in stems_pre.items():
        stems[k] = (x * gain[:, None]).astype(np.float32)
    del stems_pre, music, sfx, amb, vo

    # ---- write
    p_master = os.path.join(out_dir, f"audio_master{sfx_}.wav")
    dsp.write_wav(p_master, master, bits=24)
    for k, x in stems.items():
        if k == "vo" and a.no_vo:
            continue                      # an M&E pass has no narration stem
        dsp.write_wav(os.path.join(stem_dir, f"{k}.wav"), x, bits=32)
    log(f"wrote {os.path.relpath(p_master, ROOT)} + {os.path.relpath(stem_dir, ROOT)}/")

    # ---- QA + report
    chk = QA.check_master(master, SR, N)
    report["master"] = chk
    report["stems_lufs"] = {k: _r(_lufs(x)) for k, x in stems.items()}
    report["stems_true_peak"] = {k: _r(dsp.true_peak_db(x)) for k, x in stems.items()}
    chk["clicks"] = annotate_clicks(chk["clicks"], rows, report.get("vo"))
    report.update(measure(C, master, stems, act, rows, sinfo))
    hits = [dict(t=r["t"], what=r["label"], sound=r["name"]) for r in rows if r["kind"] == "story"]
    hits += [dict(t=round(t, 3), what=lb, sound="score") for t, lb in sinfo["marks"]]
    report["hit_list"] = sorted(hits, key=lambda h: h["t"])
    report["cues"] = rows
    report["elapsed_s"] = round(time.time() - _T0[0], 1)
    p_rep = os.path.join(out_dir, f"audio_report{sfx_}.json")
    with open(p_rep, "w") as fh:
        json.dump(report, fh, indent=1, default=_json_default)
    if not a.no_plot:
        evs = [dict(t=r["t"], label=r["label"][:22], color="#e04050") for r in rows if r["kind"] == "story"]
        evs += [dict(t=t, label=lb[:22], color="#5090ff") for t, lb in sinfo["marks"]]
        evs.sort(key=lambda e: e["t"])
        QA.overview(master, stems, C.scenes, os.path.join(out_dir, f"audio_overview{sfx_}.png"), events=evs,
                    silences=list(sinfo["silences"]) + pc_wins, title=f"SALVAGE{' (no VO)' if a.no_vo else ''} - master "
                    f"{chk['integrated_lufs']} LUFS / {chk['true_peak_dbtp']} dBTP")
    log(f"master: {chk['samples']} samples (length ok: {chk['length_ok']}), finite {chk['finite']}, "
        f"{chk['integrated_lufs']} LUFS, TP {chk['true_peak_dbtp']} dBTP, clicks {len(chk['clicks'])}")
    log(f"report: {os.path.relpath(p_rep, ROOT)}")
    return report


def sync_heart(beats, sync, tol=0.6):
    """Shift the planned heartbeat so a beat lands on each scene heartbeat cue (the shift carries
    forward, the tempo is kept)."""
    beats = list(beats)
    for ts in sorted(sync):
        if not beats:
            break
        i = int(np.argmin([abs(b - ts) for b in beats]))
        d = ts - beats[i]
        if abs(d) <= tol:
            beats = beats[:i] + [b + d for b in beats[i:]]
    return beats


def _json_default(o):
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (set, tuple)):
        return list(o)
    return str(o)


if __name__ == "__main__":
    main()
