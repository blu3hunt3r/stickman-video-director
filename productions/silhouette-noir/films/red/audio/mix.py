"""RED: the re-recording mix.

    python3 films/red/audio/mix.py                 # narration from films/red/audio/vo/narration_full.wav
    python3 films/red/audio/mix.py --no-vo         # music/SFX/beds only (levels still set against the voice)
    python3 films/red/audio/mix.py --no-scenes     # ignore the scenes' cues(T) hints (designed sheet only)
    python3 films/red/audio/mix.py --hints F.json  # merge a cue list from a JSON file instead (QA of the merge)
    python3 films/red/audio/mix.py --fresh         # ignore the score / beds render cache

Outputs (exactly frames / fps * 48000 = 7 392 000 samples) under films/red/out/:
    audio_master.wav           48 kHz stereo 24-bit PCM, -14 LUFS integrated, <= -1 dBTP
    stems/{vo,music,sfx,amb}.wav   32-bit float, post-ducking, at the master gain, pre-limiter
    audio_report.json          loudness, true peak, arc, balance, hits, cue merge, QA
    audio_overview.png         loudness curve, scene boundaries, hit markers, the silence

Signal flow
  narration: each line src_t0..src_t1 of narration_full.wav, +-40 ms pad, 8 ms fades, placed at
    the line's film start - pad; HPF 80 Hz, phase rotator, light 2:1 compression, -16 LUFS,
    peak limiter at -4.5 dBTP
  score (main / feat / hits) with fader rides (MUSIC_RIDE), SFX cue sheet (+ scene hints) with
    per-scene acoustic space (designed hits on their own bus), ambience beds (+ THE SILENCE floor)
  ducking from the words + the narration's envelope (30 ms attack, 250 ms release):
    score main -8 dB above 200 Hz / -3 below, feat -4, hits -3 / -1; SFX -3, SFX hits -1.5, beds -2
  THE SILENCE (s03 'quieter' 34.39 -> 37.25, back by 38.1): score -60 dB, beds -32 dB, SFX -10 dB
    (her footsteps survive, tiny), the floor hush stays; the voice is untouched
  master: HPF 30 Hz, glue compressor (-14 dB, 1.6:1), loudness to -14 LUFS through a 4x
    oversampled true-peak limiter at -1.25 dBTP (iterated), trim to <= -1 dBTP, edge fades
Without narration a speech-shaped proxy on the word times stands in for the voice whenever a level
is decided, so music, SFX and beds come out at their final levels.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    __package__ = "films.red.audio"

import numpy as np  # noqa: E402

from films.red.audio import ambience, common, cuesheet, qa, score, sfx_red  # noqa: E402
from films.red.audio.common import A, N, OUT, SR, TL, VO_WAV  # noqa: E402
from audio import dsp  # noqa: E402
from audio.dsp import db2lin, n_of  # noqa: E402

VO_TARGET = -16.0
VO_PAD, VO_FADE = 0.040, 0.008
VO_PEAK_DBTP = -4.5
# phase rotator: six all-passes 120..520 Hz make the (asymmetric) voiced waveform symmetric -> ~2 dB less
# crest factor with no audible change, so the peak limiter barely works and speech never drives the master
VO_ROTATOR = [("allpass", f, 0.6) for f in (120.0, 180.0, 250.0, 330.0, 420.0, 520.0)]
# ducking depths (dB) under the voice; the score's main and hits buses are split at XOVER so the low dread
# (choir, trombones, timpani, booms) only gives way a little while the speech band clears
DUCK = dict(main=-8.0, main_lo=-3.0, feat=-4.0, mhits=-3.0, mhits_lo=-1.0, sfx=-3.0, shits=-1.5, amb=-2.0)
XOVER = 200.0
ATTACK, RELEASE, LOOKAHEAD, BRIDGE = 0.03, 0.25, 0.06, 0.30
# fader rides on the whole score (dB breakpoints, cosine between): the chase under line 8 down, the dread
# under the s06/s07 lines and the s10 lines up, the wordless embrace (s10 133.2-139) up
MUSIC_RIDE = [(0.0, 0.0), (52.55, 0.0), (52.95, -4.0), (61.7, -4.0), (62.1, 0.0),
              (66.9, 0.0), (67.2, 3.0), (79.9, 3.0), (81.0, 0.0),
              (81.5, 0.0), (81.9, 4.0), (87.4, 4.0), (91.0, 0.0),
              (126.3, 0.0), (126.6, 2.0), (133.1, 2.0), (133.7, 4.0), (138.9, 4.0), (139.4, 0.0)]
MASTER_LUFS, CEILING_DBTP, LIMIT_AT = -14.0, -1.0, -1.25
SILENCE = dict(t0=A(5, "quieter"), fall=0.45, hold=37.25, back=38.1, music=-60.0, amb=-32.0, sfx=-10.0)

# acoustic space for SFX per scene: (from film time, kind, wet dB)
SPACES = [(0.0, "paper", -17.0), (9.0, "village", -13.0), (24.0, "snow_forest", -13.0), (38.0, "dark_forest", -12.0),
          (52.0, "ridge", -14.0), (66.5, "valley", -11.0), (81.0, "dark_forest", -12.0), (94.0, "dark_forest", -13.0),
          (111.0, "clearing", -13.0), (125.0, "village", -13.0), (139.0, "clearing", -14.0), (152.0, "paper", -17.0)]
MAX_CUE_GAIN_DB = 6.0


def log(msg):
    print(msg, flush=True)


def space_at(t):
    cur = SPACES[0]
    for s in SPACES:
        if t >= s[0] - 1e-6:
            cur = s
    return cur[1], cur[2]


# ============================================================================ narration
def load_vo(path=VO_WAV):
    src, _ = dsp.read_audio(path, sr_out=SR)
    src = dsp.mono(src).astype(np.float64)
    info = dict(path=os.path.relpath(path, common.ROOT), source_seconds=round(len(src) / SR, 3))
    src = dsp.sos(src, "highpass", 80.0, 2)
    src = dsp.biquad_chain(src, VO_ROTATOR)
    lv = dsp.loudness_integrated(np.stack([src, src], 1))
    if np.isfinite(lv):
        src = src * db2lin(-20.0 - lv)
    src = dsp.compressor(src, thresh_db=-24.0, ratio=2.0, attack_ms=8.0, release_ms=120.0, knee_db=6.0, mode="rms")
    vo = np.zeros(N)
    edges = []
    for line in sorted(TL["vo"], key=lambda v: v["start"]):
        a_src = max(0.0, line["src_t0"] - VO_PAD)
        b_src = min(len(src) / SR, line["src_t1"] + VO_PAD)
        seg = src[n_of(a_src):n_of(b_src)].copy()
        lv_in, lv_out = float(dsp.rms_db(seg[:n_of(0.02)])), float(dsp.rms_db(seg[-n_of(0.02):]))
        seg = dsp.fade(seg, VO_FADE, VO_FADE)
        dst = line["start"] - (line["src_t0"] - a_src)
        dsp.mix_into(vo, seg, n_of(dst))
        edges.append(dict(line=line["n"], t_in=round(dst, 4), t_out=round(dst + len(seg) / SR, 4),
                          src_in=round(a_src, 3), src_out=round(b_src, 3), edge_db=[round(lv_in, 1), round(lv_out, 1)]))
    vo2 = np.stack([vo, vo], 1)
    vo2 *= db2lin(VO_TARGET - dsp.loudness_integrated(vo2))
    vo2, g = dsp.limiter(vo2, VO_PEAK_DBTP, lookahead_ms=1.5, release_ms=60.0, return_gain=True)
    info["plosive_limiter_gr_db_max"] = round(float(-dsp.lin2db(np.min(g))), 2)
    vo2 *= db2lin(VO_TARGET - dsp.loudness_integrated(vo2))
    info.update(lines=len(edges), stem_lufs=round(dsp.loudness_integrated(vo2), 2), edges=edges)
    return vo2, info


def vo_proxy(rng):
    """Speech-shaped noise on the word times (gain staging stand-in for --no-vo)."""
    x = dsp.bandpass(dsp.pink(N, rng), 140.0, 5000.0, 2)
    x = 0.55 * x + 0.45 * dsp.onepole_lp(x, 1200.0)
    x *= 0.35 + 0.65 * np.abs(dsp.smooth_noise(N, 4.5, rng))
    gate = np.zeros(N)
    for a, b in common.word_spans():
        gate[n_of(a):n_of(b)] = 1.0
    x = np.stack([x * dsp.onepole_lp(gate, 25.0)] * 2, 1)
    return x * db2lin(VO_TARGET - dsp.loudness_integrated(x))


# ============================================================================ ducking / gates
def vo_activity(vo=None, rate=1000):
    from scipy.ndimage import binary_closing
    n = int(N / SR * rate) + 2
    act = np.zeros(n, dtype=bool)
    for a, b in common.word_spans():
        act[max(0, int((a - LOOKAHEAD) * rate)):min(n, int(b * rate) + 1)] = True
    if vo is not None and np.any(vo):
        hop = SR // rate
        m = dsp.mono(vo)[: (len(vo) // hop) * hop].reshape(-1, hop)
        lv = dsp.lin2db(np.sqrt(np.mean(m * m, axis=1)))
        env = np.zeros(n, dtype=bool)
        env[:len(lv)] = lv > (np.max(lv) - 32.0)
        k = int(LOOKAHEAD * rate)
        act |= np.concatenate([env[k:], np.zeros(k, dtype=bool)]) | env
    act = binary_closing(act, structure=np.ones(int(BRIDGE * rate)))
    return act.astype(np.float64)


def duck_curve(act, depth_db, rate=1000):
    g = dsp.duck_gain(act, depth_db, ATTACK, RELEASE, rate)
    return np.interp(np.arange(N) / SR, np.arange(len(g)) / rate, g).astype(np.float32)


def silence_gain(depth_db):
    """THE SILENCE gate (gain curve): 0 dB -> depth over `fall` from 'quieter', hold, back by `back`."""
    s = SILENCE
    return gain_curve([(0.0, 0.0), (s["t0"], 0.0), (s["t0"] + s["fall"], depth_db), (s["hold"], depth_db),
                       (s["back"], 0.0)])


def gain_curve(pts):
    """Linear gain per sample from (t, dB) breakpoints, cosine-shaped between them, flat after the last."""
    pts = list(pts) + [(N / SR + 1.0, pts[-1][1])]
    t = np.arange(N) / SR
    ts = np.array([p[0] for p in pts])
    vs = np.array([p[1] for p in pts])
    i = np.clip(np.searchsorted(ts, t, side="right") - 1, 0, len(ts) - 2)
    u = np.clip((t - ts[i]) / np.maximum(ts[i + 1] - ts[i], 1e-9), 0, 1)
    u = 0.5 - 0.5 * np.cos(np.pi * u)
    return db2lin(vs[i] + (vs[i + 1] - vs[i]) * u).astype(np.float32)


# ============================================================================ SFX
def render_cues(cues):
    bus = np.zeros((N, 2), np.float32)
    hits = np.zeros((N, 2), np.float32)
    sends = {}
    problems, clamped = [], []
    for c in cues:
        name = c["sfx"]
        try:
            x, sync = sfx_red.render_sync(name, dur=c["dur"], params=c["params"], seed=c["seed"])
        except Exception as e:  # noqa: BLE001
            problems.append(dict(t=c["t"], sfx=name, error=repr(e)[:200]))
            continue
        sp = sfx_red.spec(name)
        g = c["gain_db"]
        if g > MAX_CUE_GAIN_DB:
            clamped.append(dict(t=c["t"], sfx=name, gain_db=g))
            g = MAX_CUE_GAIN_DB
        x = x.astype(np.float64) * db2lin(g)
        if abs(c["pan"]) > 1e-6:
            x = dsp.pan_stereo(x, float(np.clip(c["pan"], -1, 1)))
        at = n_of(c["t"] - sync)
        key = "hits" if sp["hit"] else "bus"
        dsp.mix_into(hits if key == "hits" else bus, x.astype(np.float32), at)
        if sp["space"] > 0:
            kind, wet_db = space_at(c["t"])
            s = sends.setdefault((kind, key), np.zeros(N, np.float32))
            dsp.mix_into(s, (x.mean(axis=1) * sp["space"] * db2lin(wet_db)).astype(np.float32), at)
        c["placed_at"], c["placed_len"] = round(at / SR, 4), round(len(x) / SR, 3)
    for (kind, key), s in sends.items():
        wet = common.sparse_convolve(s.astype(np.float64), common.make_space_ir(kind))
        (hits if key == "hits" else bus)[:] += wet.astype(np.float32)
    return bus, hits, problems, clamped


# ============================================================================ cached renders
def cached(name, fn, files, fresh=False):
    key = common.source_key(*files)
    if not fresh:
        hit = common.cache_load(name, key)
        if hit is not None:
            return hit[0], hit[1], True
    x, info = fn()
    common.cache_save(name, key, x, info)
    return x, info, False


def get_score(fresh):
    def fn():
        b, info = score.render_score()
        return np.stack([b["main"], b["feat"], b["hits"]], 0), info
    x, info, was = cached("score", fn, ["score.py"], fresh)
    return dict(main=x[0], feat=x[1], hits=x[2]), info, was


def get_beds(fresh):
    def fn():
        beds, floor, info = ambience.render_beds()
        return np.stack([beds, floor], 0), info
    x, info, was = cached("beds", fn, ["ambience.py", "sfx_red.py"], fresh)
    return x[0], x[1], info, was


# ============================================================================ master
def master_chain(pre, ref):
    info = {}
    pre = dsp.sos(pre, "highpass", 30.0, 2)
    ref = dsp.sos(ref, "highpass", 30.0, 2)
    g1 = db2lin(-18.0 - dsp.loudness_integrated(ref))
    _, cg = dsp.compressor(ref * g1, thresh_db=-14.0, ratio=1.6, attack_ms=20.0, release_ms=300.0, knee_db=8.0,
                           mode="rms", return_gain=True)
    info["glue_gr_db_max"] = round(float(-dsp.lin2db(np.min(cg))), 2)
    pre = pre * (g1 * cg)[:, None]
    ref = ref * (g1 * cg)[:, None]
    gain_db = MASTER_LUFS - dsp.loudness_integrated(ref)
    for it in range(5):
        lv = dsp.loudness_integrated(dsp.limiter(ref * db2lin(gain_db), LIMIT_AT, lookahead_ms=2.5, release_ms=90.0))
        info[f"iter{it}"] = dict(gain_db=round(gain_db, 3), lufs=round(lv, 3))
        if abs(lv - MASTER_LUFS) < 0.04:
            break
        gain_db += MASTER_LUFS - lv
    out, lim = dsp.limiter(pre * db2lin(gain_db), LIMIT_AT, lookahead_ms=2.5, release_ms=90.0, return_gain=True)
    info["limiter_gr_db_max"] = round(float(-dsp.lin2db(np.min(lim))), 2)
    info["limiter_gr_over_1db_seconds"] = round(float(np.sum(lim < db2lin(-1.0)) / SR), 2)
    tp = dsp.true_peak_db(out)
    if tp > CEILING_DBTP - 0.02:
        out *= db2lin(CEILING_DBTP - 0.05 - tp)
        info["post_trim_db"] = round(CEILING_DBTP - 0.05 - tp, 3)
    out = dsp.fade(out, 0.005, 0.35)
    return out, info, g1 * cg * db2lin(gain_db)


# ============================================================================ measurements
def balance(vo, music, act, rate=1000):
    t, lv = dsp.loudness_curve(vo, win=0.4, hop=0.1)
    _, lm = dsp.loudness_curve(music, win=0.4, hop=0.1)
    inside = np.array([act[max(0, int((x - 0.2) * rate)):int((x + 0.2) * rate)].min() > 0.5 for x in t])
    ok = inside & (lv > -60) & (lm > -70)
    d = lv[ok] - lm[ok]
    res = dict(blocks=int(ok.sum()))
    if ok.any():
        res.update(median_lu=round(float(np.median(d)), 2), p10_lu=round(float(np.percentile(d, 10)), 2),
                   p90_lu=round(float(np.percentile(d, 90)), 2))
        per = {}
        for s in TL["scenes"]:
            mm = ok & (t >= s["start"]) & (t < s["start"] + s["duration"])
            if mm.sum() >= 3:
                per[s["id"]] = round(float(np.median(lv[mm] - lm[mm])), 1)
        res["per_scene_median_lu"] = per
    return res


def scene_levels(master):
    out = {}
    for s in TL["scenes"]:
        seg = master[n_of(s["start"]):n_of(s["start"] + s["duration"])]
        lv = dsp.loudness_integrated(seg)
        _, st = dsp.loudness_curve(seg, win=3.0, hop=0.25)
        out[s["id"]] = dict(lufs=round(lv, 1) if np.isfinite(lv) else None,
                            short_term_max=round(float(np.max(st)), 1) if len(st) else None)
    return out


def attribute_clicks(clicks, stems, cues, marks):
    """For each flagged transient: the stem carrying it (largest 7 kHz 2nd difference there) and the SFX
    cue onsets / score marks within 60 ms - designed transients (stakes, chitin, steps, the music box
    mechanism) show up here; a flag with no cue and no mark nearby would be a real discontinuity."""
    out = []
    for c in clicks:
        k = n_of(c["t"])
        a, b = max(0, k - n_of(0.012)), min(N, k + n_of(0.012))
        lv = {}
        for name, x in stems.items():
            if x is None:
                continue
            seg = dsp.sos(np.asarray(x[max(0, a - n_of(0.02)):b], dtype=np.float64), "highpass", 7000.0, 4)
            seg = seg[a - max(0, a - n_of(0.02)):]
            lv[name] = float(dsp.lin2db(np.max(np.abs(np.diff(seg, n=2, axis=0))) + 1e-12))
        src = max(lv, key=lv.get) if lv else None
        near = sorted((abs(c["t"] - q["placed_at"]), f"{q['sfx']}@{q['placed_at']:.3f}") for q in cues
                      if "placed_at" in q and q["placed_at"] - 0.06 <= c["t"] <= q["placed_at"] + q["placed_len"])
        near = [s for _, s in near[:4]]
        mk = [m[1][:40] for m in marks if abs(m[0] - c["t"]) < 0.06]
        out.append(dict(c, stem=src, stem_db={k: round(v, 1) for k, v in lv.items()}, active_cues=near, marks=mk))
    return out


def silence_measure(master, vo):
    s = SILENCE
    a, b = max(s["t0"] + s["fall"], max(e for _, e in common.word_spans() if e < s["hold"]) + 0.15), s["hold"]
    seg = master[n_of(a):n_of(b)]
    pre = master[n_of(s["t0"] - 3.0):n_of(s["t0"])]
    return dict(window=[round(a, 2), round(b, 2)], rms_dbfs=round(dsp.rms_db(seg), 1),
                momentary_max_lufs=round(float(np.max(dsp.loudness_curve(seg, win=0.4, hop=0.05)[1])), 1),
                before_rms_dbfs=round(dsp.rms_db(pre), 1))


# ============================================================================ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-vo", action="store_true")
    ap.add_argument("--no-scenes", action="store_true")
    ap.add_argument("--hints", default=None, help="JSON list of scene cue hints (scene, t scene-local, sfx, ...)")
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--outdir", default=OUT)
    ap.add_argument("--no-plot", action="store_true")
    a = ap.parse_args(argv)
    t_start = time.time()
    out_dir = os.path.abspath(a.outdir)
    os.makedirs(os.path.join(out_dir, "stems"), exist_ok=True)
    rep = dict(film="red", samples=N, seconds=N / SR, sample_rate=SR, frames=common.FRAMES, fps=common.FPS)
    log(f"[mix] RED: {common.FRAMES} frames @ {common.FPS} fps -> {N} samples ({N / SR:.3f} s)")

    # ---- narration
    rng = dsp.rng_for("red-mix")
    if a.no_vo or not os.path.exists(VO_WAV):
        vo = None
        ref_vo = vo_proxy(rng)
        rep["vo"] = dict(present=False, note="speech-shaped proxy used for level decisions")
        log("[mix] narration: none (proxy for gain staging)")
    else:
        vo, vinfo = load_vo()
        ref_vo = vo
        rep["vo"] = dict(present=True, **vinfo)
        log(f"[mix] narration: {vinfo['lines']} lines, stem {vinfo['stem_lufs']} LUFS, "
            f"plosive limiter {vinfo['plosive_limiter_gr_db_max']} dB")

    # ---- cues
    hints = None
    if a.hints:
        with open(a.hints) as fh:
            raw = json.load(fh)
        hints = [dict(scene=h["scene"], idx=i, t=float(h["t"]) + common.SCENES[h["scene"]]["start"], text=h["sfx"],
                      gain_db=float(h.get("gain_db", 0.0)), pan=float(h.get("pan", 0.0)), dur=h.get("dur"),
                      params=dict(h.get("params") or {})) for i, h in enumerate(raw)]
    cues, crep = cuesheet.cues(use_scenes=not a.no_scenes, hints=hints)
    t0 = time.time()
    sfx_bus, sfx_hits, problems, clamped = render_cues(cues)
    log(f"[mix] SFX: {len(cues)} cues ({crep['designed']} designed, {crep['hints']} scene hints; "
        f"{len(crep['snapped'])} snapped, {len(crep['added'])} added, {len(crep['unknown'])} unknown) "
        f"in {time.time() - t0:.1f}s")
    rep["cues"] = dict(total=len(cues), designed=crep["designed"], scene_hints=crep["hints"], snapped=crep["snapped"],
                       kept_word_locked=crep["kept_word_locked"], added_from_scenes=crep["added"],
                       replaced_sequences=crep["replaced_sequences"], expanded_step_cues=crep.get("expanded_step_cues", []),
                       unknown_scene_cues=crep["unknown"], scene_status=crep["status"], render_problems=problems,
                       clamped=clamped)

    # ---- beds and score
    t0 = time.time()
    beds, floor, binfo, bc = get_beds(a.fresh)
    log(f"[mix] beds {'(cache)' if bc else ''} {time.time() - t0:.1f}s")
    t0 = time.time()
    sc, sinfo, scc = get_score(a.fresh)
    log(f"[mix] score {'(cache)' if scc else ''} {time.time() - t0:.1f}s; calibration {sinfo.get('calibration')}")

    # ---- ducking and THE SILENCE
    act = vo_activity(vo)
    d = {k: duck_curve(act, v) for k, v in DUCK.items()}
    sil_m, sil_a, sil_s = silence_gain(SILENCE["music"]), silence_gain(SILENCE["amb"]), silence_gain(SILENCE["sfx"])
    sil_m *= gain_curve(MUSIC_RIDE)
    music = sc["feat"] * (d["feat"] * sil_m)[:, None]
    for bus, hi, lo in (("main", "main", "main_lo"), ("hits", "mhits", "mhits_lo")):
        x_lo = dsp.sos(sc[bus].astype(np.float64), "lowpass", XOVER, 2, zero_phase=True).astype(np.float32)
        music += (sc[bus] - x_lo) * (d[hi] * sil_m)[:, None] + x_lo * (d[lo] * sil_m)[:, None]
        del x_lo
    sfx = sfx_bus * (d["sfx"] * sil_s)[:, None] + sfx_hits * (d["shits"] * sil_s)[:, None]
    amb = beds * (d["amb"] * sil_a)[:, None] + floor
    del sc, sfx_bus, sfx_hits, beds, floor, d
    bed = music.astype(np.float64) + sfx + amb
    pre = bed + (vo if vo is not None else 0.0)
    ref = bed + ref_vo

    # ---- master
    t0 = time.time()
    master, minfo, g = master_chain(pre, ref)
    del pre, ref, bed
    log(f"[mix] master chain {time.time() - t0:.1f}s: {minfo}")
    dsp.write_wav(os.path.join(out_dir, "audio_master.wav"), master, bits=24)
    hp = lambda x: dsp.sos(np.asarray(x, dtype=np.float64), "highpass", 30.0, 2) * g[:, None]  # noqa: E731
    stems = dict(vo=hp(vo) if vo is not None else None, music=hp(music), sfx=hp(sfx), amb=hp(amb))
    for k, x in stems.items():
        dsp.write_wav(os.path.join(out_dir, "stems", f"{k}.wav"), x if x is not None else np.zeros((N, 2)), bits=32)

    # ---- QA
    chk = qa.check_master(master, SR, N)
    rep["master"] = chk
    rep["master_chain"] = minfo
    rep["arc"] = qa.arc_table(master)
    rep["scenes"] = scene_levels(master)
    rep["silence"] = silence_measure(master, vo)
    if stems["vo"] is not None:
        rep["vo_music_balance"] = balance(stems["vo"], stems["music"], act)
        rep["vo_bed_balance"] = balance(stems["vo"], stems["music"] + stems["sfx"] + stems["amb"], act)
        clicks = chk["clicks"]
        worst = -200.0
        for e in rep["vo"]["edges"]:
            for tt in (e["t_in"], e["t_out"]):
                a0, b0 = max(0, n_of(tt - 0.01)), min(N, n_of(tt + 0.01))
                worst = max(worst, float(dsp.lin2db(np.max(np.abs(np.diff(stems["vo"][a0:b0, 0]))) + 1e-12)))
        rep["vo_edges"] = dict(count=2 * len(rep["vo"]["edges"]), worst_step_dbfs=round(worst, 1),
                               clicks_near_edges=[c for c in clicks for e in rep["vo"]["edges"]
                                                  if min(abs(c["t"] - e["t_in"]), abs(c["t"] - e["t_out"])) < 0.03])
    rep["master"]["clicks"] = attribute_clicks(chk["clicks"], stems, cues, sinfo.get("marks", []))
    stem_lufs = {k: (round(dsp.loudness_integrated(x), 2) if x is not None else None) for k, x in stems.items()}
    rep["stems_lufs"] = stem_lufs
    hits = [dict(t=m[0], label=m[1], src="score") for m in sinfo.get("marks", [])]
    hits += [dict(t=c["t"], label=f"{c['sfx']}: {c['tag']}", src=c["source"]) for c in cues
             if sfx_red.spec(c["sfx"])["hit"] or c["lock"] == "word"]
    rep["hits"] = sorted(hits, key=lambda h: h["t"])
    rep["score"] = dict(calibration=sinfo.get("calibration"), counts=sinfo.get("counts"), cached=scc)
    rep["beds"] = dict(spans=binfo.get("beds"), events=binfo.get("events"), cached=bc)
    rep["elapsed_s"] = round(time.time() - t_start, 1)
    with open(os.path.join(out_dir, "audio_report.json"), "w") as fh:
        json.dump(rep, fh, indent=1, default=float)
    if not a.no_plot:
        word_locked = {round(c["t"], 3) for c in cues if c["lock"] == "word"}
        ev = [dict(t=h["t"], label=h["label"][:34], color="#5090ff" if h["src"] == "score" else "#e04050")
              for h in rep["hits"] if h["src"] == "score" or round(h["t"], 3) in word_locked]
        ev.append(dict(t=SILENCE["t0"], label="THE SILENCE", color="#40c080"))
        qa.overview(master, {k: v for k, v in stems.items()}, os.path.join(out_dir, "audio_overview.png"),
                    events=ev, title="RED - audio overview (master short-term / momentary loudness, stems)")
    log(f"[mix] master: {chk['integrated_lufs']} LUFS, {chk['true_peak_dbtp']} dBTP, length_ok={chk['length_ok']}, "
        f"finite={chk['finite']}, dc={chk['dc_offset']}, clicks={len(chk['clicks'])}; stems {stem_lufs}")
    log(f"[mix] silence: {rep['silence']}")
    if "vo_music_balance" in rep:
        log(f"[mix] vo/music balance: {rep['vo_music_balance'].get('median_lu')} LU median")
    log(f"[mix] done in {rep['elapsed_s']} s -> {out_dir}")
    return rep


if __name__ == "__main__":
    main()
