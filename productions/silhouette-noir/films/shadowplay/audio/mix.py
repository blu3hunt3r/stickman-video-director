"""SHADOW PLAY re-recording mix.

    python3 films/shadowplay/audio/mix.py            # -> films/shadowplay/out/audio_master.wav (+ stems, report, overview)
    python3 films/shadowplay/audio/mix.py --no-vo    # music & effects only -> out/audio_master_novo.wav
                                                     # (same gains and ducking as the full mix)

Exactly 153.5 s x 48000 = 7 368 000 samples, 48 kHz stereo 24-bit.

  a. narration: every timeline `vo` line cut from vo/narration_full.wav at src_t0..src_t1,
     padded 40 ms each side with 8 ms fades, placed at the line's film start minus the pad;
     HPF 80 Hz, 2.5:1 compression, -16 LUFS, a dialogue limiter at -3 dBTP.
  b. SFX: cuesheet.build_cues (word anchors + storyboard beats; the scenes' own cues(T), when
     they exist, retime / extend it), each sent to the room of its stretch of film.
  c. ambience beds (ambience.py) and the score (score.py: main + hits buses); the designed
     silences (cuesheet.sfx_silences: s10's fuse, the very end) gate the SFX and the beds.
  d. ducking from the narration (word times OR'd with its envelope, 60 ms look-ahead, gaps
     under 300 ms bridged): music -8 dB, music hits -2, SFX -3, SFX hits -1.5, beds -2; 30 ms
     attack, 250 ms release. (The bible asks -6 dB for the music; the brief's -8 dB wins.)
  e. master: HPF 30 Hz, glue compression 1.6:1, look-ahead true-peak limiter, -14 LUFS
     integrated (iterated), ceiling -1 dBTP.
  f. out/audio_master.wav, out/stems/{vo,music,sfx,amb}.wav (post-duck, at the master's
     pre-limiter gain: they sum to the master before glue and limiting), out/audio_report.json,
     out/audio_overview.png.
"""
from __future__ import annotations

import json
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402

from audio import dsp  # noqa: E402
from audio.dsp import SR, db2lin, n_of  # noqa: E402
from engine.timing import timeline  # noqa: E402
from films.shadowplay.audio import ambience, cuesheet, qa, score  # noqa: E402
from films.shadowplay.audio import sfx_shadowplay as SP  # noqa: E402

FILM = "shadowplay"
FDIR = os.path.join(_ROOT, "films", FILM)
OUT = os.path.join(FDIR, "out")

VO_TARGET = -16.0
VO_PEAK_DBTP = -6.5            # the master adds ~+4.5 dB: speech peaks then pass under its ceiling
VO_PAD, VO_FADE = 0.040, 0.008
MASTER_LUFS = -14.0
CEILING_DBTP = -1.0
LIMIT_AT = -1.25
DUCK = dict(music=-8.0, music_hits=-2.0, sfx=-3.0, sfx_hits=-1.5, amb=-2.0)
ATTACK, RELEASE = 0.030, 0.250
LOOKAHEAD, BRIDGE = 0.060, 0.300
# stem balance (dB) on top of each module's own calibration
GAIN = dict(music=6.0, music_hits=2.0, sfx=0.0, sfx_hits=0.0, amb=-2.0)
# the loudness arc we want (short-term, master): (t0, t1, LUFS)
# the dramatic arc, as M&E (music + sfx + beds) short-term loudness: the narration sits on top at
# a constant level for intelligibility, so the arc lives in everything under it.
# intimate night -> the murder stabs -> procedural tension -> the second murder -> the crossing ->
# dread -> the faster clock -> the wordless trap's peak -> the killer's room -> a quiet, open end
ARC = [(0.0, 9.0, -20.0), (9.0, 24.0, -21.0), (33.0, 37.0, -14.0), (41.0, 52.5, -20.0), (52.5, 66.5, -19.0),
       (66.5, 79.5, -17.0), (79.5, 106.5, -23.0), (106.5, 120.5, -21.0), (120.5, 131.5, -14.0), (131.5, 141.5, -22.0),
       (141.5, 153.5, -24.0)]

T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.1f}s] {msg}", flush=True)


# ============================================================================ scene cues
def scene_cues(tl):
    """The scenes' own cues(T) on the film clock (scenes that do not exist yet are skipped)."""
    out, errs, found = [], [], []
    try:
        from engine import render
    except Exception as e:                       # pragma: no cover - the engine is optional here
        return out, [f"engine.render import failed: {e!r}"], found
    for s in tl["scenes"]:
        if render.scene_path(FILM, s["id"]) is None:
            continue
        found.append(s["id"])
        try:
            mod, T = render.scene_module(FILM, s["id"])
            if mod is not None and hasattr(mod, "cues"):
                for c in mod.cues(T):
                    c = dict(c)
                    c["scene"] = s["id"]
                    c["t"] = round(float(c["t"]) + s["start"], 4)
                    out.append(c)
        except Exception as e:
            errs.append(f"{s['id']}: {e!r}")
    return sorted(out, key=lambda c: c["t"]), errs, found


# ============================================================================ narration
def load_vo(tl, N):
    path = os.path.join(FDIR, tl.get("vo_src", "audio/vo/narration_full.wav"))
    src, _ = dsp.read_audio(path, sr_out=SR)
    src = dsp.mono(src)
    info = dict(path=os.path.relpath(path, _ROOT), source_seconds=round(len(src) / SR, 3))
    src = dsp.sos(src, "highpass", 80.0, 2)
    lv = dsp.loudness_integrated(np.stack([src, src], 1))
    src = src * db2lin(-20.0 - lv)
    src = dsp.compressor(src, thresh_db=-24.0, ratio=2.5, attack_ms=8.0, release_ms=120.0, knee_db=6.0, mode="rms")
    vo = np.zeros(N)
    edges = []
    for ln in tl["vo"]:
        a = max(0.0, ln["src_t0"] - VO_PAD)
        b = min(len(src) / SR, ln["src_t1"] + VO_PAD)
        seg = dsp.fade(src[n_of(a):n_of(b)].copy(), VO_FADE, VO_FADE)
        at = ln["start"] - (ln["src_t0"] - a)
        dsp.mix_into(vo, seg, n_of(at))
        edges.append(dict(n=ln["n"], t_in=round(at, 4), t_out=round(at + len(seg) / SR, 4)))
    vo2 = np.stack([vo, vo], 1)
    lv = dsp.loudness_integrated(vo2)
    vo2 *= db2lin(VO_TARGET - lv)
    vo2, vg = dsp.limiter(vo2, VO_PEAK_DBTP, lookahead_ms=1.5, release_ms=60.0, return_gain=True)
    info["dialogue_limiter_gr_db_max"] = round(float(-dsp.lin2db(np.min(vg))), 2)
    vo2 *= db2lin(VO_TARGET - dsp.loudness_integrated(vo2))
    info.update(lines=len(edges), stem_lufs=round(dsp.loudness_integrated(vo2), 2), edges=edges)
    return vo2, info


def vo_proxy(tl, N, rng):
    """Speech-shaped noise on the word times: a stand-in for level decisions when the narration
    file is missing."""
    x = dsp.bandpass(dsp.pink(N, rng), 140.0, 5000.0, 2)
    x *= 0.35 + 0.65 * np.abs(dsp.smooth_noise(N, 4.5, rng))
    gate = np.zeros(N)
    for ln in tl["vo"]:
        for w in ln["words"]:
            gate[n_of(w["t0"]):n_of(w["t1"])] = 1.0
    x = np.stack([x * dsp.onepole_lp(gate, 25.0)] * 2, 1)
    return x * db2lin(VO_TARGET - dsp.loudness_integrated(x))


def vo_activity(tl, N, vo=None, rate=1000):
    from scipy.ndimage import binary_closing
    n = int(N / SR * rate) + 2
    act = np.zeros(n, dtype=bool)
    for ln in tl["vo"]:
        for w in ln["words"]:
            act[max(0, int((w["t0"] - LOOKAHEAD) * rate)):min(n, int(w["t1"] * rate) + 1)] = True
    if vo is not None:
        hop = SR // rate
        mm = dsp.mono(vo)[: (len(vo) // hop) * hop].reshape(-1, hop)
        lv = dsp.lin2db(np.sqrt(np.mean(mm * mm, axis=1)))
        env_act = np.zeros(n, dtype=bool)
        env_act[:len(lv)] = lv > (np.max(lv) - 32.0)
        k = int(LOOKAHEAD * rate)
        act |= np.concatenate([env_act[k:], np.zeros(k, dtype=bool)]) | env_act
    act = binary_closing(act, structure=np.ones(int(BRIDGE * rate)))
    return act.astype(np.float64)


def duck_curve(act, depth_db, N, rate=1000):
    gc = dsp.duck_gain(act, depth_db, ATTACK, RELEASE, rate)
    return np.interp(np.arange(N) / SR, np.arange(len(gc)) / rate, gc)


# ============================================================================ SFX
def _persp(x, kind):
    if kind == "behind_door":           # through a solid door: the low end only, and the hallway
        return dsp.sos(x, "lowpass", 900.0, 4) * db2lin(-2.0), 4.0
    if kind == "through_window":
        return dsp.sos(x, "lowpass", 2200.0, 2) * db2lin(-3.0), 0.0
    if kind == "hall_door":             # the stairs heard through the closed door
        return dsp.sos(x, "lowpass", 2500.0, 2) * db2lin(-2.0), 0.0
    return x, 0.0


def render_sfx(cues, spaces, N):
    """Every cue rendered, panned, given its perspective and its room. Returns
    {'sfx': (N, 2), 'hit': (N, 2)}, per-cue info."""
    bus = {"sfx": np.zeros((N, 2)), "hit": np.zeros((N, 2))}
    rows = []
    for c in cues:
        try:
            x = SP.render(c["name"], dur=c.get("dur"), params=c.get("params") or None, seed=int(c.get("seed", 0))).astype(np.float64)
        except Exception as e:
            rows.append(dict(t=c["t"], name=c["name"], error=repr(e)))
            continue
        sp = SP.spec(c["name"])
        x = x * db2lin(c["gain_db"])
        if abs(c.get("pan", 0.0)) > 1e-6:
            x = dsp.pan_stereo(x, c["pan"])
        x, send_extra = _persp(x, c.get("persp"))
        b = c.get("bus") or ("hit" if sp.get("hit") else "sfx")
        at = n_of(c["t"])
        dsp.mix_into(bus[b], x, at)
        room, sdb = next(((k, d) for a, z, k, d in spaces if a <= c["t"] < z), (None, -99.0))
        space = float(sp.get("space", 1.0))
        if room and space > 0:
            g = db2lin(sdb + c.get("send_db", 0.0) + send_extra) * space
            if c.get("persp") == "behind_door":
                room = "hallway"
            wet = dsp.convolve(x.mean(axis=1), SP.ir(room)) * g
            dsp.mix_into(bus[b], wet, at)
        rows.append(dict(t=c["t"], name=c["name"], gain_db=round(c["gain_db"], 1), bus=b, room=room,
                         len_s=round(len(x) / SR, 2), src=c.get("src", "sheet")))
    return bus, rows


def silence_gate(spans, N):
    """Per-sample gain: 0 inside each (t0, t1, fade_out, fade_in) span (silent from t0 to t1, the
    fade-out ending at t0, the fade-in starting at t1), 1 elsewhere."""
    gate = np.ones(N)
    for t0, t1, fo, fi in spans:
        a, b = n_of(max(0.0, t0 - fo)), min(N, n_of(t1 + fi))
        if b <= a:
            continue
        st = np.arange(a, b) / SR
        gdn = np.clip((t0 - st) / max(fo, 1e-4), 0, 1)
        gup = np.clip((st - t1) / max(fi, 1e-4), 0, 1)
        gate[a:b] = np.minimum(gate[a:b], np.maximum(gdn, gup))
    return gate


# ============================================================================ master
def master_chain(pre, ref):
    """pre: the mix to master; ref: the same mix with the narration, for every level decision.
    Returns (master, info, per-sample gain before the limiter)."""
    info = {}
    pre = dsp.sos(pre, "highpass", 30.0, 2)
    ref = dsp.sos(ref, "highpass", 30.0, 2)
    g1 = db2lin(-18.0 - dsp.loudness_integrated(ref))
    _, cg = dsp.compressor(ref * g1, thresh_db=-14.0, ratio=1.6, attack_ms=20.0, release_ms=300.0, knee_db=8.0,
                           mode="rms", return_gain=True)
    info["glue_gr_db_max"] = round(float(-dsp.lin2db(np.min(cg))), 2)
    pre = pre * g1 * cg[:, None]
    ref = ref * g1 * cg[:, None]
    gain_db = MASTER_LUFS - dsp.loudness_integrated(ref)
    for it in range(5):
        r_lim = dsp.limiter(ref * db2lin(gain_db), LIMIT_AT, lookahead_ms=2.5, release_ms=90.0)
        lv = dsp.loudness_integrated(r_lim)
        info[f"iter{it}"] = dict(gain_db=round(gain_db, 3), lufs=round(lv, 3))
        if abs(lv - MASTER_LUFS) < 0.05:
            break
        gain_db += MASTER_LUFS - lv
    del ref
    out, lim_g = dsp.limiter(pre * db2lin(gain_db), LIMIT_AT, lookahead_ms=2.5, release_ms=90.0, return_gain=True)
    info["limiter_gr_db_max"] = round(float(-dsp.lin2db(np.min(lim_g))), 2)
    info["limiter_gr_over_1db_s"] = round(float(np.sum(lim_g < db2lin(-1.0)) / SR), 3)
    # the limiter's biggest moments (50 ms blocks), for QA
    hop = n_of(0.05)
    nb = len(lim_g) // hop
    gr = -dsp.lin2db(lim_g[:nb * hop].reshape(nb, hop).min(axis=1))
    top = []
    for k in np.argsort(gr)[::-1]:
        if gr[k] < 1.0 or len(top) >= 12:
            break
        if all(abs(k - j) > 10 for j, _ in top):
            top.append((int(k), float(gr[k])))
    info["limiter_top"] = [dict(t=round(k * 0.05, 2), gr_db=round(v, 2)) for k, v in sorted(top)]
    tp = dsp.true_peak_db(out)
    if tp > CEILING_DBTP - 0.02:
        out *= db2lin(CEILING_DBTP - 0.05 - tp)
        info["post_trim_db"] = round(CEILING_DBTP - 0.05 - tp, 3)
    out = dsp.fade(out, 0.002, 0.05)
    return out, info, g1 * cg * db2lin(gain_db)


# ============================================================================ measurements
def scene_loudness(master, tl):
    ts, ls = dsp.loudness_curve(master, win=3.0, hop=0.1)
    tm, lm = dsp.loudness_curve(master, win=0.4, hop=0.05)
    out = {}
    for s in tl["scenes"]:
        a, b = s["start"], s["start"] + s["duration"]
        k = (ts >= a) & (ts < b)                        # t = window centre
        j = (tm >= a) & (tm < b)
        ok = ls[k][ls[k] > -70]
        out[s["id"]] = dict(short_term_median=round(float(np.median(ok)), 1) if len(ok) else None,
                            short_term_max=round(float(np.max(ls[k])), 1) if k.any() else None,
                            momentary_max=round(float(np.max(lm[j])), 1) if j.any() else None,
                            integrated=round(dsp.loudness_integrated(master[n_of(a):n_of(b)]), 1))
    return out


def vo_music_balance(vo, music, act, tl, rate=1000):
    t, lv = dsp.loudness_curve(vo, win=0.4, hop=0.1)
    _, lm = dsp.loudness_curve(music, win=0.4, hop=0.1)
    inside = np.array([act[max(0, int((x - 0.2) * rate)):max(1, int((x + 0.2) * rate))].min() > 0.5 for x in t])   # t = centre
    ok = inside & (lv > -60) & (lm > -70)
    d = lv[ok] - lm[ok]
    res = dict(blocks=int(ok.sum()))
    if len(d):
        res.update(median_lu=round(float(np.median(d)), 2),
                   iqr_lu=[round(float(np.percentile(d, 25)), 2), round(float(np.percentile(d, 75)), 2)])
    per = {}
    for s in tl["scenes"]:
        mm = ok & (t >= s["start"]) & (t < s["start"] + s["duration"])
        if mm.sum() >= 3:
            per[s["id"]] = round(float(np.median(lv[mm] - lm[mm])), 1)
    res["per_scene_median_lu"] = per
    return res


def _d2_near(x, k, half=96, ctx=960):
    """Largest 2nd difference of the 7 kHz-high-passed signal within +-half samples of k."""
    a, b = max(0, k - ctx), min(len(x), k + ctx)
    hp = dsp.sos(np.asarray(x[a:b], dtype=np.float64), "highpass", 7000.0, 4)
    d2 = np.abs(np.diff(hp, n=2, axis=0))
    d2 = d2.max(axis=1) if d2.ndim > 1 else d2
    j = k - a - 1
    return float(d2[max(0, j - half): j + half].max()) if len(d2) else 0.0


def explain_clicks(clicks, cues, rows, onsets, ainfo, vinfo, stems=None, master=None):
    """Attribute every detected transient to a designed onset (an SFX cue, a score note / hit /
    silence edge, a bed event), else to the texture of the stem that carries it (a consonant in
    the narration, a raindrop in a bed, a crackle in an SFX), or flag it UNEXPLAINED: a
    discontinuity no stem has, i.e. made by the mix itself."""
    lens = {(r["t"], r["name"]): r.get("len_s", 1.0) for r in rows}
    beds = []
    for e in ainfo.get("events", []):
        if "@" in e:
            try:
                beds.append((float(e.split("@")[1].split("-")[0]), e.split("@")[0]))
            except ValueError:
                pass
    out = []
    for c in clicks:
        t = c["t"]
        cand = [(t - to, f"score:{kind}@{to}") for (to, kind) in onsets if -0.01 <= t - to <= 0.04]
        cand += [(t - cu["t"], f"sfx:{cu['name']}@{cu['t']}") for cu in cues
                 if -0.01 <= t - cu["t"] <= lens.get((cu["t"], cu["name"]), 1.0)]
        cand += [(t - tb, f"bed:{nm}@{tb}") for (tb, nm) in beds if -0.01 <= t - tb <= 0.4]
        src = min(cand, key=lambda d: abs(d[0]))[1] if cand else None
        if src is None and stems is not None:
            k = int(round(t * SR)) - 1
            dm = _d2_near(master, k)
            ks = [nm for nm, x in stems.items() if _d2_near(x, k) >= 0.5 * dm]
            src = ("texture:" + "+".join(ks)) if ks else None
        out.append(dict(c, source=src or "UNEXPLAINED"))
    return out


# ============================================================================ main
def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    no_vo = "--no-vo" in argv
    tl = timeline(FILM)
    N = int(round(tl["duration"] * SR))
    assert N == 7368000, N
    os.makedirs(os.path.join(OUT, "stems"), exist_ok=True)
    report = dict(film=FILM, duration_s=tl["duration"], samples=N, sr=SR, no_vo=no_vo,
                  ducking=dict(DUCK, attack_s=ATTACK, release_s=RELEASE, lookahead_s=LOOKAHEAD, bridge_s=BRIDGE,
                               note="music -8 dB per the brief (the bible says -6 dB)"))

    # ---- picture sync
    sc, errs, found = scene_cues(tl)
    sync, notes = cuesheet.sync_points(sc)
    cues = cuesheet.build_cues(sync, notes["extras"])
    spaces = cuesheet.sfx_spaces(sync)
    report["scene_cues"] = dict(scenes_found=found, cues=len(sc), errors=errs,
                                **{k: v for k, v in notes.items() if k != "extras"})
    report["sync"] = {k: v for k, v in sorted(sync.items(), key=lambda kv: kv[1])}
    log(f"{len(sc)} scene cues from {len(found)} scene files; {len(cues)} SFX cues")

    # ---- narration
    vo_path = os.path.join(FDIR, tl.get("vo_src", "audio/vo/narration_full.wav"))
    if os.path.exists(vo_path):
        vo, vinfo = load_vo(tl, N)
    else:
        vo, vinfo = vo_proxy(tl, N, np.random.default_rng(5)), dict(proxy=True)
    report["vo"] = {k: v for k, v in vinfo.items() if k != "edges"}
    act = vo_activity(tl, N, vo if not vinfo.get("proxy") else None)
    log(f"narration: {vinfo.get('stem_lufs')} LUFS, limiter {vinfo.get('dialogue_limiter_gr_db_max')} dB")

    # ---- SFX
    sbus, rows = render_sfx(cues, spaces, N)
    report["sfx_cues"] = rows
    log("SFX rendered")

    # ---- beds
    amb, ainfo = ambience.render_beds(sync, N)
    amb = amb.astype(np.float64)
    report["ambience"] = ainfo
    log("beds rendered")

    # ---- score
    m_main, m_hits, sinfo = score.render_score(sync, N)
    report["score"] = dict(notes=sinfo["notes"], string_voices=sinfo["strings"], brass_voices=sinfo["brass"],
                           silences=sinfo["silences"])
    hits = [dict(t=t, label=lb) for t, lb, layer in sinfo["marks"] if layer in ("hits", "main")]
    report["score_hits"] = hits
    log("score rendered")

    # ---- designed silences: every effect and bed (and their reverbs) cut dead
    sil = cuesheet.sfx_silences(sync)
    gate = silence_gate(sil, N)[:, None]
    sbus["sfx"] *= gate
    sbus["hit"] *= gate
    amb *= gate
    del gate
    report["sfx_silences"] = [dict(t0=round(a, 3), t1=round(b, 3)) for a, b, _, _ in sil]

    # ---- ducking
    music = m_main.astype(np.float64) * duck_curve(act, DUCK["music"], N)[:, None] * db2lin(GAIN["music"])
    music += m_hits.astype(np.float64) * duck_curve(act, DUCK["music_hits"], N)[:, None] * db2lin(GAIN["music_hits"])
    del m_main, m_hits
    sfx_st = sbus["sfx"] * duck_curve(act, DUCK["sfx"], N)[:, None] * db2lin(GAIN["sfx"])
    sfx_st += sbus["hit"] * duck_curve(act, DUCK["sfx_hits"], N)[:, None] * db2lin(GAIN["sfx_hits"])
    del sbus
    amb *= (duck_curve(act, DUCK["amb"], N) * db2lin(GAIN["amb"]))[:, None]
    # peak control on the music and SFX stems: the designed hits are peaky (door boom, knife
    # stabs); a fast stem limiter set where the master gain will put them just under the ceiling
    # keeps the master limiter from ducking the narration and the beds on every blow
    est = MASTER_LUFS - dsp.loudness_integrated(vo + music + sfx_st + amb)
    ceil = CEILING_DBTP - est - 0.8
    pc = {}
    for k in ("music", "sfx"):
        x = music if k == "music" else sfx_st
        y, gg = dsp.limiter(x, ceil, lookahead_ms=2.0, release_ms=45.0, return_gain=True)
        pc[k] = dict(ceiling_dbtp=round(ceil, 2), gr_db_max=round(float(-dsp.lin2db(np.min(gg))), 2),
                     gr_over_1db_s=round(float(np.sum(gg < db2lin(-1.0)) / SR), 3))
        if k == "music":
            music = y
        else:
            sfx_st = y
    report["stem_peak_control"] = pc
    report["stems_pre_master_lufs"] = {k: round(dsp.loudness_integrated(x), 2) for k, x in
                                       (("vo", vo), ("music", music), ("sfx", sfx_st), ("amb", amb))}
    report["vo_music_balance"] = vo_music_balance(vo, music, act, tl)
    log(f"stems: {report['stems_pre_master_lufs']}")

    # ---- master
    ref = vo + music + sfx_st + amb
    pre = ref if not no_vo else (music + sfx_st + amb)
    master, minfo, gpre = master_chain(pre, ref)
    del ref, pre
    report["master_chain"] = minfo
    name = "audio_master_novo.wav" if no_vo else "audio_master.wav"
    dsp.write_wav(os.path.join(OUT, name), master, SR, bits=24)
    log(f"wrote {name}")
    stems = {}
    for k, x in (("vo", vo), ("music", music), ("sfx", sfx_st), ("amb", amb)):
        y = dsp.sos(x, "highpass", 30.0, 2) * gpre[:, None]
        if k == "vo" and no_vo:
            continue
        dsp.write_wav(os.path.join(OUT, "stems", f"{k}.wav"), y.astype(np.float32), SR, bits=24)
        stems[k] = y.astype(np.float32)
    del vo, music, sfx_st, amb

    # ---- checks
    chk = qa.check_master(master, SR, N)
    onsets = sinfo.get("onsets", []) + [(round(t, 4), "sfx_silence") for a, b, _, _ in sil for t in (a, b)]
    chk["clicks"] = explain_clicks(chk["clicks"], cues, rows, onsets, ainfo, vinfo, stems, master)
    every = explain_clicks(qa.find_clicks(master, SR, max_report=10 ** 6), cues, rows, onsets, ainfo, vinfo, stems, master)
    chk["clicks_by_source"] = {}
    for c in every:
        kk = c["source"].split(":")[0] if not c["source"].startswith("texture") else c["source"]
        chk["clicks_by_source"][kk] = chk["clicks_by_source"].get(kk, 0) + 1
    chk["clicks_unexplained"] = [c for c in every if c["source"] == "UNEXPLAINED"]
    chk["clicks_explained_of_total"] = [len(every) - len(chk["clicks_unexplained"]), len(every)]
    report["master"] = chk
    report["scene_loudness"] = scene_loudness(master, tl)
    report["scene_loudness_me"] = scene_loudness(sum(stems[k] for k in ("music", "sfx", "amb")), tl)
    report["arc_targets"] = [dict(t0=a, t1=b, target=v) for a, b, v in ARC]
    log(f"master: {chk['integrated_lufs']} LUFS, TP {chk['true_peak_dbtp']} dBTP, transients explained {chk['clicks_explained_of_total']}")
    ev = [dict(t=h["t"], label=h["label"][:22], color="#e04050") for h in hits if "silence" not in h["label"] and "tick" not in h["label"]]
    qa.overview(master, stems, tl["scenes"], os.path.join(OUT, "audio_overview.png" if not no_vo else "audio_overview_novo.png"),
                events=ev, title=f"SHADOW PLAY - {chk['integrated_lufs']} LUFS, TP {chk['true_peak_dbtp']} dBTP", arc=ARC)
    report["render_seconds"] = round(time.time() - T0, 1)
    with open(os.path.join(OUT, "audio_report.json" if not no_vo else "audio_report_novo.json"), "w") as fh:
        json.dump(report, fh, indent=1, default=float)
    log("done")
    return report


if __name__ == "__main__":
    main()
