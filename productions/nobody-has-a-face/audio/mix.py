"""Re-recording mix for "Nobody Has a Face".

    python3 -m audio.mix                     # narration from audio/vo/narration_full.wav if present
    python3 -m audio.mix --vo PATH           # any narration file (wav/mp3/...; resampled to 48 kHz)
    python3 -m audio.mix --no-vo             # music/sfx/amb only (ducking still follows the words)
    python3 -m audio.mix --scenes s01,s02    # only these scenes' cues (QA)

Outputs (exactly total_frames / fps * 48000 samples):
    out/audio_master.wav          48 kHz stereo 24-bit PCM, -14 LUFS integrated, <= -1 dBTP
    out/stems/{vo,music,sfx,amb}.wav   32-bit float, post-ducking, at the master gain, pre-limiter
    out/audio_report.json         loudness, true peak, per-scene levels, missing scenes, unknown cues, QA
    out/audio_overview.png        loudness curve with scene boundaries, designed hits and silences

Signal flow: VO (HPF, light compression, normalised to -16 LUFS) + score (main/feature) + SFX cues
(per-scene acoustic space reverb; designed hits on their own bus) + ambience beds -> word-time
ducking (music -9 dB, feature -5 dB, SFX -3 dB, beds -2 dB, designed hits only above 900 Hz, the match
strike never)
-> hard silence at the S12 smash to black -> master: HPF 30 Hz, glue compressor, loudness
normalisation, 4x-oversampled true-peak limiter at -1 dBTP (iterated to -14.0 LUFS).
Without narration a speech-shaped proxy on the word times stands in for the voice when the
master gain is computed, so music/SFX/beds come out at their final levels.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402

from audio import ambience, dsp, qa, score, sfx  # noqa: E402
from audio.dsp import SR, db2lin, n_of  # noqa: E402

OUT = os.path.join(ROOT, "out")
VO_DEFAULT = os.path.join(ROOT, "audio", "vo", "narration_full.wav")

VO_TARGET = -16.0            # narration stem, integrated (pre-master)
MUSIC_TARGET = -19.0         # score (main + feature) integrated before ducking
SFX_BUS_DB = 0.0             # SFX are library-level (-16 LUFS at gain 0); scenes set gain_db
AMB_BUS_DB = 0.0
DUCK = dict(music=-9.0, feature=-5.0, sfx=-3.0, amb=-2.0, hits_hi=-4.0)
ATTACK, RELEASE, LOOKAHEAD, BRIDGE = 0.03, 0.25, 0.06, 0.30
MASTER_LUFS = -14.0
CEILING_DBTP = -1.0
LIMIT_AT = -1.25             # limiter ceiling (true-peak domain) with margin
MAX_GAIN_DB = 6.0            # safety clamp on cue gain_db

# acoustic space per scene (scene time, IR kind, wet dB) for SFX cues
SPACES = {
    "s01": [(0.0, "small_room", -15)],
    "s02": [(0.0, "street", -14)],
    "s03": [(0.0, "office", -16)],
    "s04": [(0.0, "street", -14)],
    "s05": [(0.0, "office", -17)],
    "s06": [(0.0, "street", -14), (4.4, "office", -17)],
    "s07": [(0.0, "office", -19), (4.9, "street", -14)],
    "s08": [(0.0, "street", -14)],
    "s09": [(0.0, "cell", -17), (5.6, "street", -12)],
    "s10": [(0.0, "office", -17), (4.6, "court", -11), (6.4, "alley", -12)],
    "s11": [(0.0, "alley", -12)],
    "s12": [(0.0, "street", -14), (5.4, "car", -16)],
    "s13": [(0.0, "street", -13)],
    "s14": [(0.0, "office", -17)],
    "s15": [(0.0, "office", -16)],
    "s16": [(0.0, "small_room", -15)],
    "s17": [(0.0, "street", -14)],
    "s18": [(0.0, "cell", -13)],
}

# designed hits from the score plan (production bible section 7): added when a scene does not
# already cue the same sound within +-0.35 s of the anchor word.
REQUIRED_HITS = [
    ("s01", "sub_drop", ("face", 1), -2.0, {}),
    ("s09", "stinger", ("red", 0), -1.0, {}),
    ("s09", "sub_drop", ("red", 0), -3.0, {}),
    ("s14", "impact", ("rain", 0), -5.0, {"size": 0.55}),
    ("s14", "impact", ("three", 0), -5.0, {"size": 0.55}),
    ("s14", "impact", ("a", 0), -5.0, {"size": 0.55}),
    ("s14", "impact", ("a", 1), -5.0, {"size": 0.6}),
    ("s14", "impact", ("a", 2), -4.0, {"size": 0.7}),
    ("s14", "braam", ("mirror", 0), 0.0, {}),
    ("s16", "stinger", ("walk", 0), -7.0, {}),
]
HIT_TOL = 0.35

# designed silences that also cut SFX (scene, start, end or None = scene end)
HARD_SILENCES = [("s12", 9.7, None)]

YIELD_SUSTAINED = ("room_tone", "city_far", "crowd_walla", "siren_far", "tinnitus")
SIGNATURE = ("match_strike",)    # never ducked at all (identical in S2, S7, S17, S18)


def log(msg):
    print(msg, flush=True)


def warn_box(lines):
    bar = "!" * 78
    print("\n" + bar, flush=True)
    for ln in lines:
        print("!!  " + ln, flush=True)
    print(bar + "\n", flush=True)


# ============================================================================ cues
def collect_cues(tl, only=None):
    from engine.render import scene_module
    from engine.timing import SceneTiming
    cues, missing, errored, unknown, bad, no_cues = [], [], [], [], [], []
    timings = {}
    for s in tl["scenes"]:
        sid = s["id"]
        timings[sid] = SceneTiming(sid)
        if only and sid not in only:
            continue
        try:
            mod, T = scene_module(sid)
        except FileNotFoundError:
            missing.append(sid)
            continue
        except Exception as e:  # noqa: BLE001
            errored.append(dict(scene=sid, stage="import", error=repr(e)[:300]))
            continue
        if not hasattr(mod, "cues"):
            no_cues.append(sid)
            continue
        try:
            lst = list(mod.cues(T) or [])
        except Exception as e:  # noqa: BLE001
            errored.append(dict(scene=sid, stage="cues()", error=repr(e)[:300]))
            continue
        for i, c in enumerate(lst):
            if not isinstance(c, dict) or "sfx" not in c or "t" not in c:
                bad.append(dict(scene=sid, index=i, cue=repr(c)[:120]))
                continue
            name = c["sfx"]
            if not sfx.exists(name):
                unknown.append(dict(scene=sid, index=i, sfx=name, t=c["t"]))
                continue
            cues.append(dict(sid=sid, idx=i, name=name, t=float(c["t"]), g=T.start + float(c["t"]),
                             gain_db=float(c.get("gain_db", 0.0)), pan=float(c.get("pan", 0.0)),
                             dur=c.get("dur"), params=dict(c.get("params") or {}), source="scene"))
    return cues, dict(missing=missing, errored=errored, unknown=unknown, bad=bad, no_cues=no_cues), timings


def add_required_hits(cues, timings, status):
    added, satisfied = [], []
    for sid, name, (word, k), gain, params in REQUIRED_HITS:
        T = timings[sid]
        try:
            t = T.at(word, k)
        except KeyError:
            continue
        g = T.start + t
        have = [c for c in cues if c["sid"] == sid and c["name"] == name and abs(c["g"] - g) <= HIT_TOL]
        if have:
            satisfied.append(dict(scene=sid, sfx=name, word=word, at=round(t, 3), by_cue=round(have[0]["t"], 3)))
            continue
        cues.append(dict(sid=sid, idx=1000 + len(added), name=name, t=t, g=g, gain_db=gain, pan=0.0, dur=None,
                         params=dict(params), source="auto"))
        added.append(dict(scene=sid, sfx=name, word=word, at=round(t, 3), gain_db=gain))
    return added, satisfied


def space_at(tl, g):
    sc = [s for s in tl["scenes"] if s["start"] <= g + 1e-6]
    s = sc[-1] if sc else tl["scenes"][0]
    sp = SPACES.get(s["id"], [(0.0, "small_room", -18)])
    cur = sp[0]
    for e in sp:
        if g - s["start"] >= e[0] - 1e-6:
            cur = e
    return cur[1], cur[2]


def render_cues(tl, cues, N):
    """Render every cue into the SFX bus (or the designed-hit bus), with per-space reverb."""
    bus = np.zeros((N, 2))
    hits = np.zeros((N, 2))
    sig = np.zeros((N, 2))
    problems, clamped = [], []
    for c in cues:
        name = c["name"]
        sp = sfx.spec(name)
        try:
            x = sfx.render(name, dur=c["dur"], params=c["params"],
                           seed=dsp.stable_seed(c["sid"], c["idx"], name) % (1 << 31)).astype(np.float64)
        except Exception as e:  # noqa: BLE001
            problems.append(dict(scene=c["sid"], index=c["idx"], sfx=name, error=repr(e)[:200]))
            continue
        gdb = c["gain_db"]
        if gdb > MAX_GAIN_DB:
            clamped.append(dict(scene=c["sid"], index=c["idx"], sfx=name, gain_db=gdb, used=MAX_GAIN_DB))
            gdb = MAX_GAIN_DB
        x = dsp.pan_stereo(x, float(np.clip(c["pan"], -1, 1))) * db2lin(gdb + SFX_BUS_DB)
        if sp["space"] > 0:
            kind, wet_db = space_at(tl, c["g"])
            wet = dsp.convolve(x.mean(axis=1), dsp.make_ir(kind)) * db2lin(wet_db) * sp["space"]
            y = np.zeros((len(wet), 2))
            y[:len(x)] += x
            y += wet
            x = y
        c["rendered_len"] = len(x) / SR
        dsp.mix_into(sig if name in SIGNATURE else hits if sp["hit"] else bus, x, n_of(c["g"]))
    return bus, hits, sig, problems, clamped


def cue_spans(cues):
    spans, scenes = {}, {}
    for c in cues:
        scenes.setdefault(c["name"], set()).add(c["sid"])
        if c["name"] in YIELD_SUSTAINED or c["name"] == "heartbeat":
            d = c["dur"] if c["dur"] is not None else (sfx.spec(c["name"])["default_dur"] or 2.0)
            spans.setdefault(c["name"], []).append((c["g"], c["g"] + float(d)))
    return spans, scenes


# ============================================================================ narration
def load_vo(path, tl, N):
    src, sr = dsp.read_audio(path, sr_out=SR)
    src = dsp.mono(src)
    info = dict(path=os.path.relpath(path, ROOT), source_seconds=round(len(src) / SR, 3))
    exp = tl.get("vo_source", {}).get("duration")
    if exp and abs(len(src) / SR - exp) > 2.0:
        info["warning"] = f"source is {len(src) / SR:.1f}s, timeline expects {exp:.1f}s - check the file"
    # light dialogue chain: HPF, gentle 2.5:1 compression on the take
    src = dsp.sos(src, "highpass", 75.0, 2)
    lv = dsp.loudness_integrated(np.stack([src, src], 1))
    src = src * db2lin(-20.0 - lv) if np.isfinite(lv) else src
    src = dsp.compressor(src, thresh_db=-24.0, ratio=2.5, attack_ms=8.0, release_ms=120.0, knee_db=6.0, mode="rms")
    vo = np.zeros(N)
    pieces = 0
    edges = []
    for s in tl["scenes"]:
        for p in s["vo_pieces"]:
            a_src = max(0.0, p["src_in"])
            b_src = min(len(src) / SR, p["src_out"])
            if b_src <= a_src:
                continue
            seg = src[n_of(a_src):n_of(b_src)].copy()
            edge_db = (float(dsp.rms_db(seg[:n_of(0.02)])), float(dsp.rms_db(seg[-n_of(0.02):])))
            seg = dsp.fade(seg, 0.008, 0.008)
            dst = p["g_at"] + (a_src - p["src_in"])
            dsp.mix_into(vo, seg, n_of(dst))
            edges.append(dict(scene=s["id"], t_in=round(dst, 4), t_out=round(dst + len(seg) / SR, 4),
                              src_in=round(a_src, 3), src_out=round(b_src, 3),
                              src_level_in_db=round(edge_db[0], 1), src_level_out_db=round(edge_db[1], 1)))
            pieces += 1
    vo2 = np.stack([vo, vo], 1)
    lv = dsp.loudness_integrated(vo2)
    vo2 *= db2lin(VO_TARGET - lv)
    info.update(pieces=pieces, stem_lufs=round(dsp.loudness_integrated(vo2), 2), source_lufs=round(lv, 2) if np.isfinite(lv) else None)
    info["edges"] = edges
    return vo2, info


def vo_proxy(tl, N, rng):
    """Speech-shaped noise on the word times (VO stand-in for gain staging only)."""
    x = dsp.pink(N, rng)
    x = dsp.bandpass(x, 140.0, 5000.0, 2)
    x = 0.55 * x + 0.45 * dsp.onepole_lp(x, 1200.0)
    x *= 0.35 + 0.65 * np.abs(dsp.smooth_noise(N, 4.5, rng))
    gate = np.zeros(N)
    for s in tl["scenes"]:
        for w in s["words"]:
            gate[n_of(w["g0"]):n_of(w["g1"])] = 1.0
    gate = dsp.onepole_lp(gate, 25.0)
    x = np.stack([x * gate] * 2, 1)
    return x * db2lin(VO_TARGET - dsp.loudness_integrated(x))


# ============================================================================ ducking
def vo_activity(tl, N, vo=None, rate=1000):
    """0/1 voice activity at `rate` Hz from the word times (look-ahead, gaps < BRIDGE bridged),
    OR'd with the narration's own envelope when the narration is present."""
    from scipy.ndimage import binary_closing
    n = int(N / SR * rate) + 2
    act = np.zeros(n, dtype=bool)
    for s in tl["scenes"]:
        for w in s["words"]:
            a = max(0, int((w["g0"] - LOOKAHEAD) * rate))
            b = min(n, int(w["g1"] * rate) + 1)
            act[a:b] = True
    if vo is not None:
        hop = SR // rate
        m = dsp.mono(vo)[: (len(vo) // hop) * hop].reshape(-1, hop)
        lv = dsp.lin2db(np.sqrt(np.mean(m * m, axis=1)))
        thr = np.max(lv) - 32.0
        env_act = np.zeros(n, dtype=bool)
        env_act[:len(lv)] = lv > thr
        k = int(LOOKAHEAD * rate)
        env_act = np.concatenate([env_act[k:], np.zeros(k, dtype=bool)]) | env_act
        act |= env_act
    act = binary_closing(act, structure=np.ones(int(BRIDGE * rate)))
    return act.astype(np.float64)


def duck_curve(act, depth_db, N, rate=1000):
    g = dsp.duck_gain(act, depth_db, ATTACK, RELEASE, rate)
    return np.interp(np.arange(N) / SR, np.arange(len(g)) / rate, g)


# ============================================================================ measurements
def vo_music_balance(vo, music, act, tl, rate=1000):
    """Narration vs music level while the narration speaks: momentary (400 ms) loudness of each
    stem on blocks that lie fully inside voice activity; median / IQR of L_vo - L_music, the same
    for each scene, a gated integrated comparison over the voice-active samples, and the measured
    ducking depth (music under the voice vs the music in the gaps)."""
    t, lv = dsp.loudness_curve(vo, win=0.4, hop=0.1)
    _, lm = dsp.loudness_curve(music, win=0.4, hop=0.1)
    ta = np.arange(len(act)) / rate
    inside = np.array([act[max(0, int((x - 0.2) * rate)):int((x + 0.2) * rate)].min() > 0.5 for x in t])
    ok = inside & (lv > -60) & (lm > -70)
    d = lv[ok] - lm[ok]
    res = dict(blocks=int(ok.sum()), median_lu=round(float(np.median(d)), 2),
               iqr_lu=[round(float(np.percentile(d, 25)), 2), round(float(np.percentile(d, 75)), 2)])
    actn = np.interp(np.arange(len(vo)) / SR, ta, act) > 0.5
    lv_g = dsp.loudness_integrated(vo[actn])
    lm_g = dsp.loudness_integrated(music[actn])
    lm_gap = dsp.loudness_integrated(music[~actn])
    res["gated_lu"] = round(lv_g - lm_g, 2)
    res["music_under_voice_lufs"] = round(lm_g, 2)
    res["music_in_gaps_lufs"] = round(lm_gap, 2)
    res["duck_depth_measured_db"] = round(lm_g - lm_gap, 2)
    per = {}
    for s in tl["scenes"]:
        m = ok & (t >= s["start"]) & (t < s["start"] + s["duration"])
        if m.sum() >= 3:
            per[s["id"]] = round(float(np.median(lv[m] - lm[m])), 1)
    res["per_scene_median_lu"] = per
    return res


def boundary_check(master, vo, edges, clicks):
    """Every vo_piece edge: the source level at the cut, the largest sample step of the narration
    stem within +-10 ms (dBFS), and any detected master click within 30 ms of the edge."""
    rows, worst = [], -200.0
    for e in edges:
        for side, tt, lvl in (("in", e["t_in"], e["src_level_in_db"]), ("out", e["t_out"], e["src_level_out_db"])):
            a, b = max(0, n_of(tt - 0.01)), min(len(vo), n_of(tt + 0.01))
            step = float(dsp.lin2db(np.max(np.abs(np.diff(vo[a:b, 0])))) if b - a > 2 else -200.0)
            worst = max(worst, step)
            rows.append(dict(scene=e["scene"], edge=side, t=tt, src_level_db=lvl, vo_max_step_dbfs=round(step, 1)))
    near = [c for c in clicks for r in rows if abs(c["t"] - r["t"]) < 0.03]
    return dict(count=len(rows), worst_step_db=round(worst, 1), clicks_near_edges=near, edges=rows)


# ============================================================================ master
def master_chain(pre, ref):
    """pre: the mix to master; ref: the same mix with the narration (or its proxy) used for every
    level decision. Returns (master, info, gain_pre_limiter)."""
    info = {}
    pre = dsp.sos(pre, "highpass", 30.0, 2)
    ref = dsp.sos(ref, "highpass", 30.0, 2)
    l0 = dsp.loudness_integrated(ref)
    g1 = db2lin(-18.0 - l0)
    _, cg = dsp.compressor(ref * g1, thresh_db=-14.0, ratio=1.6, attack_ms=20.0, release_ms=300.0, knee_db=8.0,
                           mode="rms", return_gain=True)
    info["glue_gr_db_max"] = round(float(-dsp.lin2db(np.min(cg))), 2)
    pre = pre * g1 * cg[:, None]
    ref = ref * g1 * cg[:, None]
    gain_db = MASTER_LUFS - dsp.loudness_integrated(ref)
    for it in range(4):
        r_lim = dsp.limiter(ref * db2lin(gain_db), LIMIT_AT, lookahead_ms=2.5, release_ms=90.0)
        lv = dsp.loudness_integrated(r_lim)
        info[f"iter{it}"] = dict(gain_db=round(gain_db, 3), lufs=round(lv, 3))
        if abs(lv - MASTER_LUFS) < 0.05:
            break
        gain_db += MASTER_LUFS - lv
    out, lim_g = dsp.limiter(pre * db2lin(gain_db), LIMIT_AT, lookahead_ms=2.5, release_ms=90.0, return_gain=True)
    info["limiter_gr_db_max"] = round(float(-dsp.lin2db(np.min(lim_g))), 2)
    tp = dsp.true_peak_db(out)
    if tp > CEILING_DBTP:
        out *= db2lin(CEILING_DBTP - 0.05 - tp)
        info["post_trim_db"] = round(CEILING_DBTP - 0.05 - tp, 3)
    out = dsp.fade(out, 0.002, 0.25)      # the last match flare is swallowed by the dark
    return out, info, g1 * cg * db2lin(gain_db)


# ============================================================================ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vo", default=None, help="narration file (default audio/vo/narration_full.wav)")
    ap.add_argument("--no-vo", action="store_true", help="mix without narration")
    ap.add_argument("--scenes", default="", help="comma-separated scene ids whose cues to use (default all)")
    ap.add_argument("--outdir", default=OUT, help="output folder (default out/)")
    ap.add_argument("--no-plot", action="store_true")
    a = ap.parse_args(argv)
    out_dir = os.path.abspath(a.outdir)
    a.out = os.path.join(out_dir, "audio_master.wav")
    t_start = time.time()
    from engine.timing import timeline
    tl = timeline()
    N = int(round(tl["total_frames"] * SR / tl["fps"]))
    report = dict(title=tl["title"], samples=N, seconds=N / SR, sample_rate=SR)
    log(f"[mix] {tl['title']}: {tl['total_frames']} frames @ {tl['fps']} fps -> {N} samples ({N / SR:.4f} s)")

    # ---- cues
    only = set(a.scenes.split(",")) if a.scenes else None
    cues, st, timings = collect_cues(tl, only)
    added, satisfied = add_required_hits(cues, timings, st)
    report.update(missing_scenes=st["missing"], errored_scenes=st["errored"], unknown_cues=st["unknown"],
                  malformed_cues=st["bad"], scenes_without_cues=st["no_cues"], auto_hits=added,
                  hits_already_cued=satisfied)
    if st["missing"]:
        log(f"[mix] WARNING missing scene modules (skipped): {', '.join(st['missing'])}")
    for e in st["errored"]:
        log(f"[mix] WARNING scene {e['scene']} failed at {e['stage']}: {e['error']}")
    for u in st["unknown"]:
        log(f"[mix] WARNING unknown SFX {u['sfx']!r} in {u['scene']} cue #{u['index']} (t={u['t']}) - skipped")
    log(f"[mix] {len(cues)} cues ({len(added)} designed hits added from the score plan)")

    # ---- SFX
    t0 = time.time()
    sfx_bus, hit_bus, sig_bus, problems, clamped = render_cues(tl, cues, N)
    report.update(cue_render_errors=problems, cue_gain_clamped=clamped)
    for p in problems:
        log(f"[mix] WARNING cue {p['scene']}#{p['index']} {p['sfx']}: {p['error']}")
    log(f"[mix] sfx rendered in {time.time() - t0:.1f}s")

    # ---- beds + score (with yields to picture-synced cues)
    spans, scenes_by_name = cue_spans(cues)
    t0 = time.time()
    amb, amb_info = ambience.render_beds(tl, spans, scenes_by_name)
    amb = amb.astype(np.float64) * db2lin(AMB_BUS_DB)
    log(f"[mix] ambience rendered in {time.time() - t0:.1f}s")
    t0 = time.time()
    m_main, m_feat, sc_info = score.render_score(tl, scenes_by_name)
    m_main = m_main.astype(np.float64)
    m_feat = m_feat.astype(np.float64)
    lm = dsp.loudness_integrated(m_main + m_feat)
    mg = db2lin(MUSIC_TARGET - lm)
    m_main *= mg
    m_feat *= mg
    log(f"[mix] score rendered in {time.time() - t0:.1f}s")
    report["ambience"] = dict(beds=amb_info["beds"], yields=amb_info["yields"], silences=amb_info["silences"])
    report["score"] = dict(piano_notes=sc_info["notes"], heartbeat=sc_info["heartbeat"],
                           silences=sc_info["silences"], marks=[(round(t, 3), m) for t, m in sc_info["marks"]])

    # ---- narration
    vo_path = a.vo or VO_DEFAULT
    vo, vo_info = None, dict(path=os.path.relpath(vo_path, ROOT), present=False)
    if not a.no_vo and os.path.exists(vo_path):
        try:
            vo, vi = load_vo(vo_path, tl, N)
            vo_info.update(vi, present=True)
            log(f"[mix] narration: {vi['pieces']} pieces from {vi['path']} -> {vi['stem_lufs']} LUFS")
            if "warning" in vi:
                log("[mix] WARNING " + vi["warning"])
        except Exception as e:  # noqa: BLE001
            vo_info["error"] = repr(e)[:300]
            warn_box([f"Could not read the narration {vo_path}: {e!r}", "Mixing WITHOUT narration."])
    else:
        why = "--no-vo given" if a.no_vo else f"{os.path.relpath(vo_path, ROOT)} does not exist"
        warn_box(["NO NARRATION IN THIS MIX (" + why + ").",
                  "Music/SFX/beds are still ducked on the timeline word times and the master gain is",
                  "computed against a speech-shaped stand-in, so their levels are final. Re-run",
                  "`python3 -m audio.mix` once audio/vo/narration_full.wav exists."])
    report["vo"] = vo_info

    # ---- ducking
    act = vo_activity(tl, N, vo)
    g_music = duck_curve(act, DUCK["music"], N)
    g_feat = duck_curve(act, DUCK["feature"], N)
    g_sfx = duck_curve(act, DUCK["sfx"], N)
    g_amb = duck_curve(act, DUCK["amb"], N)
    g_hi = duck_curve(act, DUCK["hits_hi"], N)
    music = m_main * g_music[:, None] + m_feat * g_feat[:, None]
    del m_main, m_feat
    hit_hi = dsp.sos(hit_bus, "highpass", 900.0, 2)
    hits = (hit_bus - hit_hi) + hit_hi * g_hi[:, None]
    sfx_st = sfx_bus * g_sfx[:, None] + hits + sig_bus
    del sfx_bus, hit_bus, hit_hi, hits, sig_bus
    amb = amb * g_amb[:, None]
    report["ducking"] = dict(depth_db=DUCK, attack_s=ATTACK, release_s=RELEASE, lookahead_s=LOOKAHEAD,
                             bridge_s=BRIDGE, voice_active_s=round(float(act.sum()) / 1000.0, 2))

    # ---- hard silences (the S12 smash to black: everything but the voice)
    gate = np.ones(N)
    for sid, t0s, t1s in HARD_SILENCES:
        T = timings[sid]
        a_, b_ = n_of(T.start + t0s), n_of(T.start + (t1s if t1s is not None else T.duration))
        gate[a_:b_] = 0.0
        r = n_of(0.004)
        gate[max(0, a_ - r):a_] = np.minimum(gate[max(0, a_ - r):a_], np.linspace(1, 0, min(r, a_)))
    sfx_st *= gate[:, None]
    music *= gate[:, None]
    amb *= gate[:, None]

    # ---- master
    vo_stem = vo if vo is not None else np.zeros((N, 2))
    pre = vo_stem + music + sfx_st + amb
    if vo is not None:
        ref = pre
        report["loudness_reference"] = "narration"
    else:
        proxy = vo_proxy(tl, N, np.random.default_rng(1770))
        ref = pre + proxy
        report["loudness_reference"] = "speech-shaped proxy on the word times (no narration)"
    t0 = time.time()
    master, minfo, g_pre = master_chain(pre, ref)
    log(f"[mix] mastered in {time.time() - t0:.1f}s")
    del ref
    stems = dict(vo=vo_stem * g_pre[:, None], music=music * g_pre[:, None], sfx=sfx_st * g_pre[:, None],
                 amb=amb * g_pre[:, None])
    del pre

    # ---- write
    os.makedirs(os.path.join(out_dir, "stems"), exist_ok=True)
    dsp.write_wav(a.out, master, SR, bits=24)
    for k, x in stems.items():
        dsp.write_wav(os.path.join(out_dir, "stems", f"{k}.wav"), x, SR, bits=32)
    log(f"[mix] wrote {a.out} and {os.path.join(out_dir, 'stems')}/{{vo,music,sfx,amb}}.wav")

    # ---- report + QA
    chk = qa.check_master(master, SR, N)
    report["master"] = dict(path=a.out, format="WAV PCM 24-bit 48 kHz stereo",
                            integrated_lufs=chk["integrated_lufs"], true_peak_dbtp=chk["true_peak_dbtp"],
                            sample_peak_dbfs=chk["sample_peak_dbfs"], length_ok=chk["length_ok"],
                            finite=chk["finite"], dc_offset=chk["dc_offset"], clicks=chk["clicks"], chain=minfo)
    if vo is not None:
        report["vo_music_balance"] = vo_music_balance(stems["vo"], stems["music"], act, tl)
        report["vo_piece_boundaries"] = boundary_check(master, stems["vo"], vo_info.get("edges", []), report["master"]["clicks"])
        b = report["vo_music_balance"]
        log(f"[mix] narration vs music under the voice: median {b['median_lu']} LU (IQR {b['iqr_lu']}), "
            f"gated {b['gated_lu']} LU; music ducked {b['duck_depth_measured_db']} dB")
        nb = report["vo_piece_boundaries"]
        log(f"[mix] vo_piece boundaries: {nb['count']} edges, worst VO-stem step {nb['worst_step_db']} dBFS, "
            f"clicks near edges: {len(nb['clicks_near_edges'])}")
    for ck in report["master"]["clicks"]:
        onset = sorted((c for c in cues if -0.03 <= ck["t"] - c["g"] <= 0.15), key=lambda c: abs(ck["t"] - c["g"]))
        inside = [c for c in cues if sfx.spec(c["name"])["kind"] == "oneshot"
                  and 0 <= ck["t"] - c["g"] <= c.get("rendered_len", 0.3)]
        if onset:
            ck["source"] = f"onset of {onset[0]['name']} ({onset[0]['sid']} t={onset[0]['t']:.2f})"
        elif inside:
            ck["source"] = f"inside {inside[-1]['name']} ({inside[-1]['sid']} t={inside[-1]['t']:.2f})"
        else:
            ck["source"] = "unexplained - check"
    if vo is None:
        report["master"]["note"] = ("No narration: integrated loudness is below -14 LUFS by design; with the "
                                    "narration the same gain staging lands on -14.0 LUFS.")
    per = []
    for s in tl["scenes"]:
        a_, b_ = n_of(s["start"]), n_of(s["start"] + s["duration"])
        row = dict(scene=s["id"], slug=s["slug"], start=s["start"], rms_db=round(dsp.rms_db(master[a_:b_]), 2))
        _, st_l = dsp.loudness_curve(master[a_:b_], win=3.0, hop=0.25) if b_ - a_ > n_of(3.0) else (None, [np.nan])
        row["short_term_max_lufs"] = round(float(np.max(st_l)), 2)
        for k, x in stems.items():
            row[f"{k}_rms_db"] = round(dsp.rms_db(x[a_:b_]), 2)
        row["cues"] = sum(1 for c in cues if c["sid"] == s["id"])
        per.append(row)
    report["per_scene"] = per
    report["cues"] = [dict(scene=c["sid"], t=round(c["t"], 3), sfx=c["name"], gain_db=c["gain_db"], pan=c["pan"],
                           dur=c["dur"], params=c["params"], source=c["source"]) for c in cues]
    report["render_seconds"] = round(time.time() - t_start, 1)
    with open(os.path.join(out_dir, "audio_report.json"), "w") as fh:
        json.dump(report, fh, indent=1, default=lambda o: o if not isinstance(o, set) else sorted(o))
    if not a.no_plot:
        try:
            evs = [dict(t=c["g"], label=c["name"], color="#e04050") for c in cues if c["source"] == "auto"]
            evs += [dict(t=t, label=m, color="#5090ff") for t, m in sc_info["marks"]]
            qa.overview(master, stems, tl["scenes"], os.path.join(out_dir, "audio_overview.png"), evs,
                        title=f"Nobody Has a Face - master {chk['integrated_lufs']} LUFS, {chk['true_peak_dbtp']} dBTP"
                              + ("" if vo is not None else "  (NO NARRATION)"))
        except Exception:  # noqa: BLE001
            traceback.print_exc()
    log(f"[mix] master: {chk['integrated_lufs']} LUFS integrated, {chk['true_peak_dbtp']} dBTP, "
        f"length ok {chk['length_ok']}, finite {chk['finite']}, clicks {len(chk['clicks'])}")
    log(f"[mix] done in {time.time() - t_start:.0f}s -> {os.path.join(out_dir, 'audio_report.json')}")
    return report


if __name__ == "__main__":
    main()
