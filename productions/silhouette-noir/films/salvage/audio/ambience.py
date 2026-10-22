"""SALVAGE beds: the places the film sounds in.

    render_beds(C, seed=0) -> (amb float32 (N, 2), info)

    underwater  the pressure world: a dark rumble that deepens and thickens with depth (cutoff
                falls, sub rises), water movement and a faint fizz of the surface when shallow,
                far creaks and pings of the wreck when near it
    wreck       inside the capsized hull: the steel enclosure's resonances (87/141/233/389/612 Hz)
                breathing slowly, far knocks and creaks inside the ship
    dusk        the surface at dusk (s02-s03): the swell against the hull, wind, the boat's creaks,
                distant gulls (s02 only)
    night       the night deck (s12, s14, s15): a calmer swell, a light breeze, rope and davit
                creaks - and the davit creaking with the bell's swing after it is hauled up

Each bed is calibrated to a target loudness over its own active spans, then automated (dB
breakpoints) with crossfades across the cuts and transitions from the timeline. Paper scenes
(s01 open, s04, s07) have no bed: the paper world is dry and silent but for the score.
"""
from __future__ import annotations

import math

import numpy as np

from audio import dsp
from audio.dsp import SR, TWO_PI, bandpass, brown, db2lin, n_of, pink, resonator_bank, smooth_noise, sos, white

from . import cuesheet as CS
from . import sfx_salvage as S

TARGET = dict(underwater=-31.0, wreck=-31.5, dusk=-28.5, night=-31.5)


def _curve(points, t, off=-80.0):
    """dB automation from (t, dB) breakpoints (sorted), off before the first / after the last."""
    if not points:
        return np.full(len(t), off)
    pts = sorted(points)
    return np.interp(t, [p[0] for p in pts], [p[1] for p in pts], left=pts[0][1], right=pts[-1][1])


def _spans(points, thresh=-70.0):
    """Active (t0, t1) spans of a dB automation."""
    pts = sorted(points)
    out = []
    for (ta, va), (tb, vb) in zip(pts, pts[1:]):
        if max(va, vb) > thresh:
            if out and abs(out[-1][1] - ta) < 1e-6:
                out[-1][1] = tb
            else:
                out.append([ta, tb])
    return out


def _seg(n, rng, fn):
    return fn(n, rng)


# ============================================================================ bed generators
def underwater_seg(n, rng, depth):
    """depth: per-sample array 0..1."""
    d = np.clip(depth, 0, 1)
    # shallow: brighter rumble + moving water + surface fizz
    sh = sos(brown(n, rng), "lowpass", 380.0, 2) * 0.8
    mv = bandpass(pink(n, rng), 130.0, 850.0, 2) * (0.55 + 0.45 * smooth_noise(n, 0.18, rng)) * 0.45
    fz = bandpass(pink(n, rng), 1400.0, 4200.0, 2) * (0.6 + 0.4 * smooth_noise(n, 0.5, rng)) * 0.05
    # deep: dark pressure, sub, slow swells
    dp = sos(brown(n, rng), "lowpass", 120.0, 2)
    sub = sos(white(n, rng), "lowpass", 45.0, 4)
    sub = sub / max(1e-9, np.std(sub)) * 0.55
    swell = 0.7 + 0.3 * smooth_noise(n, 0.05, rng)
    shallow = sh + mv + fz * (1 - d)[:] ** 2
    deep = (dp + sub) * swell
    x = shallow * np.sqrt(1 - d) + deep * np.sqrt(d) * 1.15
    return dsp.decorrelate(x, rng, amount=0.55)


def wreck_seg(n, rng):
    base = sos(brown(n, rng), "lowpass", 150.0, 2)
    ex = pink(n, rng)
    modes = [87.0, 141.0, 233.0, 389.0, 612.0]
    res = resonator_bank(ex, modes, [30.0, 35.0, 40.0, 45.0, 50.0], [1.0, 0.8, 0.6, 0.4, 0.25])
    res = res / max(1e-9, np.std(res)) * (0.55 + 0.45 * smooth_noise(n, 0.07, rng)) * 0.5
    mv = bandpass(pink(n, rng), 120.0, 600.0, 2) * (0.5 + 0.5 * smooth_noise(n, 0.12, rng)) * 0.3
    x = base / max(1e-9, np.std(base)) + res + mv
    return dsp.decorrelate(x, rng, amount=0.6)


def wind_seg(n, rng, strength=1.0):
    g = np.clip(0.45 + 0.55 * smooth_noise(n, 0.11, rng) + 0.25 * smooth_noise(n, 0.4, rng), 0.15, 1.2) * strength
    x = bandpass(pink(n, rng), 220.0, 2600.0, 2) * g
    wh = dsp.tv_bandpass(white(n, rng), 950.0 * (1.0 + 0.25 * smooth_noise(n, 0.2, rng)), q=7.0, block=256) * g ** 2 * 0.25
    return x + wh


def deck_seg(n, rng, period, calm, wind):
    sw = S.swell_track(n, rng, period=period, slap_rate=1.0, calm=calm)
    sw = sw / max(1e-9, np.std(sw))
    wd = wind_seg(n, rng, wind)
    wd = wd / max(1e-9, np.std(wd)) * 0.55 * wind
    x = dsp.decorrelate(sw, rng, amount=0.5) + dsp.decorrelate(wd, rng, amount=0.8)
    return x


# ============================================================================ the map
def automation(C):
    g, w = C.g, C.w
    tr = C.trans
    uw = [(g("s01", 4.2), -80), (g("s01", 5.7), 0), (g("s02", 0.2), 0), (g("s02", 0.95), -80),
          (g("s03", 4.9), -80), (g("s03", 5.9), -2), (tr("s03")[0], 0), (tr("s03")[1] - 0.2, -80),
          (tr("s04")[0] + 0.2, -80), (tr("s04")[1], 0), (w("s06", "inside"), 0), (w("s06", "inside") + 1.2, -7),
          (C.end("s06") - 0.02, -7), (C.end("s06"), -80),
          (C.start("s11") - 0.05, -80), (C.start("s11") + 0.05, 0), (g("s11", 9.2), -1), (tr("s11")[1] - 0.3, -80),
          (g("s12", 7.9), -80), (g("s12", 8.6), -3), (C.start("s13"), -6), (g("s13", 1.2), -10), (g("s13", 8.0), -10),
          (g("s13", 9.6), -6), (C.start("s14"), -6), (g("s14", 8.4), -6), (g("s14", 8.9), -14), (C.end("s14") - 0.03, -14),
          (C.end("s14"), -80),
          (g("s16", -0.2), -80), (g("s16", 1.6), 0), (g("s16", 12.6), 0), (g("s16", 13.6), -8), (g("s16", 15.0), -80)]
    wreck = [(w("s06", "inside") - 0.2, -80), (w("s06", "inside") + 1.0, -4), (C.end("s06") - 0.02, -4), (C.end("s06"), -80),
             (tr("s07")[0], -80), (tr("s07")[1], 0), (g("s09", 3.9), 0), (g("s09", 4.4), -13), (g("s09", 7.1), -13),
             (g("s09", 7.6), 0), (C.end("s10") - 0.05, 0), (C.end("s10") + 0.05, -80)]
    dusk = [(g("s02", 0.45), -80), (g("s02", 1.25), 0), (C.end("s02"), 0), (g("s03", 1.0), -1.5), (g("s03", 4.9), -3),
            (g("s03", 6.2), -80)]
    night = [(tr("s11")[0] + 0.5, -80), (tr("s11")[1], 0), (g("s12", 6.0), 0), (g("s12", 6.4), -2),
             (g("s12", 7.6), -2), (g("s12", 8.4), -80),
             (tr("s13")[0], -80), (tr("s13")[1], -2), (C.end("s14"), -1), (C.start("s15"), 0), (tr("s15")[0], 0),
             (tr("s15")[1] - 0.2, -80)]
    return dict(underwater=uw, wreck=wreck, dusk=dusk, night=night)


def _far_events(C, rng, spans, kinds, rate, gain_db, fc):
    """Sparse far-away wreck sounds inside the given spans (mono, muffled)."""
    out = []
    for t0, t1 in spans:
        tt = t0 + rng.uniform(0.5, 2.0)
        while tt < t1 - 1.0:
            name = kinds[int(rng.integers(0, len(kinds)))]
            out.append((tt, name, gain_db + rng.uniform(-4, 2), fc))
            tt += rng.exponential(1.0 / rate) + 2.0
    return out


def render_beds(C, seed=0, debug=False):
    N = n_of(C.duration)
    rng = np.random.default_rng(dsp.stable_seed("salvage-beds", seed))
    t_all = None
    auto = automation(C)
    amb = np.zeros((N, 2), dtype=np.float32)
    info = dict(beds={}, events=[])
    layers = {}
    for name in ("underwater", "wreck", "dusk", "night"):
        pts = auto[name]
        spans = _spans(pts)
        bed = np.zeros((N, 2))
        for t0, t1 in spans:
            a, b = max(0, n_of(t0 - 0.5)), min(N, n_of(t1 + 0.5))
            n = b - a
            if n <= 0:
                continue
            tt = (np.arange(a, b)) / SR
            if name == "underwater":
                dep = np.interp(tt, [p[0] for p in CS.depth_points(C)], [p[1] for p in CS.depth_points(C)])
                x = underwater_seg(n, rng, dep)
            elif name == "wreck":
                x = wreck_seg(n, rng)
            elif name == "dusk":
                x = deck_seg(n, rng, period=5.2, calm=0.0, wind=1.0)
            else:
                x = deck_seg(n, rng, period=7.0, calm=0.6, wind=0.55)
            bed[a:b] += dsp.fade(x, 0.3, 0.3)
        # calibrate over the active spans, then automate
        tt = np.arange(N) / SR if t_all is None else t_all
        t_all = tt
        gdb = _curve(pts, tt)
        act = gdb > -40
        if act.any():
            lv = dsp.loudness_integrated(bed[act])
            if np.isfinite(lv):
                bed *= db2lin(TARGET[name] - lv)
        bed *= db2lin(gdb)[:, None]
        info["beds"][name] = dict(spans=[(round(a, 2), round(b, 2)) for a, b in spans], target=TARGET[name])
        amb += bed.astype(np.float32)
        if debug:
            layers[name] = bed.astype(np.float32)
        del bed

    # ---- point sounds owned by the beds: gulls (s02 only), boat creaks, far wreck sounds
    ev = []
    g = C.g
    ev += [(g("s02", 1.9), "gull_call", -15.0, -0.55, None), (g("s02", 6.1), "gull_call", -17.0, 0.6, None),
           (g("s02", 10.6), "gull_call", -18.0, -0.25, None)]
    erng = np.random.default_rng(dsp.stable_seed("salvage-bed-events", seed))
    for (t0, t1), lvl in (((g("s02", 1.5), C.end("s02")), -16.0), ((g("s12", 0.8), g("s12", 7.8)), -18.0),
                          ((g("s14", 0.4), g("s14", 8.2)), -19.0)):
        tt = t0 + erng.uniform(0.3, 1.5)
        while tt < t1:
            ev.append((tt, "deck_creak" if erng.uniform() < 0.5 else "rope_creak", lvl + erng.uniform(-4, 0),
                       erng.uniform(-0.6, 0.6), None))
            tt += erng.uniform(2.6, 5.5)
    # the davit creaking with the bell's swing (s14 after the toll, s15)
    tt = C.w("s14", "bell") + 1.9
    k = 0
    while tt < C.trans("s15")[0]:
        ev.append((tt, "rope_creak", -17.0 - 0.3 * k, 0.35 * (-1) ** k, None))
        tt += 1.7 + erng.uniform(-0.1, 0.1)
        k += 1
    # far wreck sounds while near it underwater
    wr_spans = [(C.start("s05") + 2.0, C.end("s06") - 1.0), (C.start("s11"), C.g("s11", 7.0)),
                (C.g("s16", 6.0), C.g("s16", 13.0))]
    for (tt, name, gdb, fc) in _far_events(C, erng, wr_spans, ("hull_ping", "metal_creak", "hull_groan"), 0.12, -15.0, 900.0):
        ev.append((tt, name, gdb, erng.uniform(-0.7, 0.7), fc))
    in_spans = [(C.trans("s07")[1], C.g("s09", 3.5)), (C.g("s10", 0.5), C.end("s10") - 1.0)]
    for (tt, name, gdb, fc) in _far_events(C, erng, in_spans, ("metal_creak", "hull_ping", "hull_groan"), 0.14, -14.0, 1300.0):
        ev.append((tt, name, gdb, erng.uniform(-0.8, 0.8), fc))
    wet_uw = np.zeros(N)
    wet_wr = np.zeros(N)
    for i, (tt, name, gdb, pan, fc) in enumerate(ev):
        x = S.render(name, params=dict(size=0.4, length=3.0) if name == "hull_groan" else None, seed=500 + i).astype(np.float64)
        if fc:
            x = S.underwater(x, fc, lift_db=1.5)
        x = dsp.pan_stereo(x, pan) * db2lin(gdb)
        dsp.mix_into(amb, x.astype(np.float32), n_of(tt))
        sp = CS.space_at(C, tt)
        if sp == "underwater":
            dsp.mix_into(wet_uw, dsp.mono(x), n_of(tt), 0.8)
        elif sp == "wreck":
            dsp.mix_into(wet_wr, dsp.mono(x), n_of(tt), 0.9)
        info["events"].append(dict(t=round(tt, 2), name=name, gain_db=round(gdb, 1)))
    for buf, kind, wdb in ((wet_uw, "underwater", -4.0), (wet_wr, "wreck", -3.0)):
        if np.any(buf):
            amb += dsp.pad_to(sparse_wet(buf, kind, wdb), N).astype(np.float32)
    if debug:
        info["layers"] = layers
    return amb, info


def sparse_wet(send, kind, wet_db, gap=2.0):
    """Wet stereo signal of a mono send in space `kind`, convolving only its active regions."""
    ir = S.space_ir(kind)
    N = len(send)
    out = np.zeros((N + len(ir), 2))
    act = np.abs(send) > 1e-7
    idx = np.nonzero(act)[0]
    if len(idx) == 0:
        return out[:N]
    brk = np.nonzero(np.diff(idx) > gap * SR)[0]
    starts = np.concatenate([[idx[0]], idx[brk + 1]])
    ends = np.concatenate([idx[brk], [idx[-1]]])
    for a, b in zip(starts, ends):
        y = dsp.convolve(send[a:b + 1], ir) * db2lin(wet_db)
        dsp.mix_into(out, y, a)
    return out[:N]


if __name__ == "__main__":
    import os
    import sys
    import time
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(here))))
    t0 = time.time()
    C = CS.Clock()
    amb, info = render_beds(C)
    print(f"beds rendered in {time.time() - t0:.1f}s; integrated {dsp.loudness_integrated(amb):.1f} LUFS, TP {dsp.true_peak_db(amb):.1f}")
    print(info["beds"])
