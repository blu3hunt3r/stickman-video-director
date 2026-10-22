"""RED: continuous ambience beds (bible section 5), crossfaded across the timeline's transitions.

    render_beds(seed=0) -> (amb float64 (N, 2), info)

Beds (each a generator rendered only where its level automation is non-zero):
  cold_air ....... s01: the paper world - a faint cold air (continuity into the village)
  village_wind ... s02 / s10: gusty wind between steep roofs, eave whistles on strong gusts
  hearth ......... s02: warm crackle from the open doorway (fades as she walks away)
  lanterns ....... s02 posts / s11 lantern path: oil flames fluttering
  forest_hush .... s03: snow hush (absorbed, close air), treetop air; darkens towards 'deeper'
  dark_forest .... s04: lower, closer, a pressure rumble, no birds
  run_air ........ s04-s05 chase: air rushing past the tracking camera
  ridge_wind ..... s05: open, gusting, spindrift hiss
  valley_wind .... s06: wide, high, distant wind over the valley; thins as the hoods flatten
  hoods_sway ..... s06: many hoods swaying in the trees (soft cloth flutter, wide)
  still ......... s07-s08: 'the forest goes still' - near-silent pressure
  fire ........... s08 from 'fire': the burning web (roar, flutter, crackle, pops)
  dawn ........... s09: hush, smouldering embers, cooling threads ticking
  morning_wind ... s10: grey morning, colder and steadier than the night
  dusk ........... s11: soft pine air at dusk
  silence_floor .. s03 THE SILENCE: a barely-there hush so the drop reads as designed, not a dropout
Events: dog barks (s02, s10), sign creaks (s02, s10), crows (s03, s06), branch creaks and snow
plops (s03, s04), a winter bird (s09), an owl (s11). Events sit in narration gaps.

THE SILENCE itself (s03 'quieter', 34.39 -> ~37.4) is applied by mix.py to music, SFX and beds
together; this module only provides the floor.
"""
from __future__ import annotations

import math

import numpy as np

from .common import A, END, N, S, SR, place  # noqa: F401
from . import sfx_red
from audio import dsp
from audio.dsp import bandpass, brown, db2lin, n_of, onepole_lp, pink, smooth_noise, sos, tv_bandpass, tv_lowpass, white

CTRL = 1000                      # envelope control rate (Hz)
TOTAL = N / SR

# integrated loudness of each bed at automation level 1.0 (pre-master; narration sits at -16)
BED_LUFS = dict(cold_air=-46.0, village_wind=-33.0, hearth=-43.0, lanterns=-41.0, forest_hush=-41.0,
                dark_forest=-41.0, run_air=-37.0, ridge_wind=-30.0, valley_wind=-34.0, hoods_sway=-39.0,
                still=-45.0, fire=-25.0, dawn=-41.0, morning_wind=-34.0, dusk=-39.0, silence_floor=-58.0)
EVENT_MAX = dict(dog_bark=-35.0, sign_creak=-35.0, crow_caw=-32.0, crow_flap=-38.0, branch_creak=-36.0,
                 snow_plop=-40.0, bird_chirp=-40.0, owl_hoot=-35.0)


# ============================================================================ envelopes
def envelope(points):
    """Control-rate envelope from [(t, gain)] breakpoints, raised-cosine between points,
    held before the first / after the last."""
    n = int(math.ceil(TOTAL * CTRL)) + 2
    pts = sorted(points)
    t = np.arange(n) / CTRL
    if not pts:
        return np.zeros(n)
    ts = np.array([p[0] for p in pts])
    vs = np.array([p[1] for p in pts], dtype=np.float64)
    i = np.clip(np.searchsorted(ts, t, side="right") - 1, 0, len(ts) - 1)
    j = np.minimum(i + 1, len(ts) - 1)
    span = np.maximum(ts[j] - ts[i], 1e-9)
    u = np.clip((t - ts[i]) / span, 0, 1)
    u = 0.5 - 0.5 * np.cos(np.pi * u)
    out = vs[i] + (vs[j] - vs[i]) * u
    out[t < ts[0]] = vs[0]
    out[t >= ts[-1]] = vs[-1]
    return out


def to_audio(ctrl, a, b):
    return np.interp(np.arange(a, b) / SR, np.arange(len(ctrl)) / CTRL, ctrl)


def spans(env, pad=0.6, gap=4.0):
    nz = np.nonzero(env > 1e-4)[0]
    if len(nz) == 0:
        return []
    out = []
    start = prev = nz[0]
    for k in nz[1:]:
        if (k - prev) / CTRL > gap:
            out.append((start, prev))
            start = k
        prev = k
    out.append((start, prev))
    return [(max(0, int(a / CTRL * SR) - n_of(pad)), min(N, int(b / CTRL * SR) + n_of(pad))) for a, b in out]


# ============================================================================ generators
def _gusts(n, rng, rate=0.18, floor=0.35, peaky=1.6):
    g = np.clip(smooth_noise(n, rate, rng) * 0.5 + 0.55, 0, 1.2)
    g = floor + (1 - floor) * g ** peaky
    return g * (1 + 0.08 * smooth_noise(n, 1.7, rng))


def wind(n, rng, strength=0.7, bright=1.0, whistle=0.0, spindrift=0.0, rate=0.18, floor=0.35):
    """Gusty wind: pink noise through a gust-driven low-pass, a low rumble, optional eave
    whistles (narrow resonances on strong gusts) and spindrift hiss. Stereo, decorrelated."""
    out = np.zeros((n, 2))
    base = _gusts(n, rng, rate, floor)
    for ch in range(2):
        g = np.roll(base, n_of(0.35) * (1 if ch else 0)) * (1 + 0.06 * smooth_noise(n, 0.9, rng))
        x = tv_lowpass(pink(n, rng), (380 + 1500 * bright * g ** 1.3), q=0.6, block=256)
        x = sos(x, "highpass", 70, 2) * g ** 1.4
        rum = sos(sos(brown(n, rng), "lowpass", 160, 2), "highpass", 35, 2) * g ** 1.2 * 0.6
        y = x + rum
        if whistle > 0:
            fc = 760 * (1 + 0.25 * smooth_noise(n, 0.15, rng)) * (0.9 + 0.25 * g)
            wh = tv_bandpass(white(n, rng), fc, q=26, block=256) * np.clip(g - 0.65, 0, None) ** 2.0
            y += whistle * 6.0 * wh
        if spindrift > 0:
            sd = bandpass(white(n, rng), 3000, 9500, 2) * np.clip(g - 0.5, 0, None) ** 1.5
            y += spindrift * 0.8 * sd
        out[:, ch] = y * strength
    return out


def forest_hush(n, rng, dark=0.0):
    """Snow hush: absorbed close air, faint treetop air drifting, (dark) a pressure rumble."""
    out = np.zeros((n, 2))
    for ch in range(2):
        air = bandpass(pink(n, rng), 90, 2200 - 1300 * dark, 2)
        tops = tv_bandpass(pink(n, rng), 520 * (1 + 0.3 * smooth_noise(n, 0.08, rng)), q=0.9, block=256)
        tops *= 0.5 + 0.5 * np.clip(smooth_noise(n, 0.12, rng) + 0.3, 0, 1)
        rum = sos(sos(brown(n, rng), "lowpass", 110, 2), "highpass", 30, 2)
        sift = bandpass(white(n, rng), 4000, 10000, 2) * (1 - dark)
        out[:, ch] = air + 0.7 * tops * (1 - 0.6 * dark) + rum * (0.3 + 1.2 * dark) + 0.04 * sift
    return out


def run_air(n, rng):
    """Air rushing past a running, tracking camera: low turbulent band with pace flutter."""
    out = np.zeros((n, 2))
    for ch in range(2):
        x = tv_bandpass(pink(n, rng), 300 * (1 + 0.4 * smooth_noise(n, 0.6, rng)), q=0.5, block=256)
        x *= 1 + 0.35 * np.sin(2 * np.pi * 2.4 * np.arange(n) / SR + ch) * (0.5 + 0.5 * smooth_noise(n, 0.4, rng))
        out[:, ch] = sos(x, "highpass", 60, 2)
    return out


def hoods_sway(n, rng, count=9):
    """Many cloth hoods swaying in the wind on branches: slow sways, soft flutters, wide."""
    out = np.zeros((n, 2))
    for k in range(count):
        sway = np.clip(smooth_noise(n, rng.uniform(0.25, 0.5), rng) + 0.2, 0, 1) ** 2
        fl = bandpass(pink(n, rng), rng.uniform(300, 500), rng.uniform(2200, 3400), 2)
        fl *= 0.3 + 0.7 * np.abs(smooth_noise(n, rng.uniform(14, 24), rng))
        x = fl * sway
        p = -0.9 + 1.8 * k / max(count - 1, 1)
        out += dsp.pan_mono(x, p)
    return out


def still_air(n, rng):
    """'The forest goes still': a held-breath pressure (very low band) and almost no air."""
    out = np.zeros((n, 2))
    for ch in range(2):
        pr = sos(sos(brown(n, rng), "lowpass", 120, 2), "highpass", 32, 2) * (1 + 0.2 * smooth_noise(n, 0.1, rng))
        air = bandpass(pink(n, rng), 200, 1500, 2) * 0.08
        out[:, ch] = pr + air
    return out


def dawn_bed(n, rng):
    """Dawn after the fire: hush, smouldering embers thinning out, cooling threads ticking."""
    t = np.arange(n) / SR
    hush = forest_hush(n, rng, dark=0.2) * 0.8
    emb = sfx_red.ember_bed(n, rng, 0.9)
    emb = emb / max(1e-9, np.max(np.abs(emb)))
    thin = np.clip(1.0 - t / (n / SR) * 0.6, 0.3, 1.0)
    ticks = dsp.resonator_bank(dsp.crackle(n, 1.5, rng, amp_spread=0.6), [3100, 5200, 7400], [14, 16, 18], [1, 0.6, 0.3])
    return hush + emb * 0.35 * thin[:, None] + dsp.to_stereo(ticks) * 0.05


def dusk_bed(n, rng):
    """Dusk in the clearing: soft pine air breathing in slow swells."""
    out = np.zeros((n, 2))
    for ch in range(2):
        sw = 0.55 + 0.45 * np.clip(smooth_noise(n, 0.09, rng) + 0.2, 0, 1)
        x = tv_bandpass(pink(n, rng), 900 * (0.8 + 0.4 * sw), q=0.6, block=256) * sw
        out[:, ch] = sos(x, "highpass", 90, 2) + 0.15 * sos(sos(brown(n, rng), "lowpass", 120, 2), "highpass", 30, 2)
    return out


def hearth(n, rng):
    """A hearth through the open doorway: low-passed small fire, a little room."""
    x = sfx_red.fire_bed(n, rng, 0.35)
    x = sos(x, "lowpass", 2600, 2)
    return x


def lanterns(n, rng, count=3):
    out = np.zeros((n, 2))
    for k in range(count):
        x = sfx_red.flutter_bed(n, rng, 0.5)
        out += dsp.pan_mono(x, -0.6 + 1.2 * k / max(count - 1, 1))
    return out


def silence_floor(n, rng):
    """THE SILENCE floor: the faintest high hush (not nothing - held breath)."""
    out = np.zeros((n, 2))
    for ch in range(2):
        out[:, ch] = bandpass(pink(n, rng), 1500, 7000, 2) + 0.3 * bandpass(pink(n, rng), 100, 400, 2)
    return out


GEN = dict(cold_air=lambda n, r: wind(n, r, 0.5, bright=0.5, rate=0.12, floor=0.5),
           village_wind=lambda n, r: wind(n, r, 0.8, bright=0.9, whistle=0.6, rate=0.2),
           hearth=hearth, lanterns=lanterns,
           forest_hush=lambda n, r: forest_hush(n, r, 0.0),
           dark_forest=lambda n, r: forest_hush(n, r, 1.0),
           run_air=run_air,
           ridge_wind=lambda n, r: wind(n, r, 1.0, bright=1.2, whistle=0.25, spindrift=1.0, rate=0.25, floor=0.3),
           valley_wind=lambda n, r: wind(n, r, 0.8, bright=1.4, whistle=0.15, rate=0.12, floor=0.45),
           hoods_sway=hoods_sway, still=still_air,
           fire=lambda n, r: sfx_red.fire_bed(n, r, 1.0),
           dawn=dawn_bed,
           morning_wind=lambda n, r: wind(n, r, 0.8, bright=0.8, whistle=0.3, rate=0.14, floor=0.5),
           dusk=dusk_bed, silence_floor=silence_floor)


# ============================================================================ the map
def automation():
    """Level automation per bed: {bed: [(film t, level)]}. Crossfades follow the transitions."""
    q = A(5, "quieter")
    fire = A(15, "fire")
    L = {}
    # s01 paper world -> s02 village (ink 8.375-9.625)
    L["cold_air"] = [(0.0, 0.0), (0.8, 1.0), (8.4, 1.0), (9.6, 0.0)]
    L["village_wind"] = [(8.2, 0.0), (9.4, 1.0), (19.6, 1.0), (21.0, 1.25), (23.25, 1.15), (24.75, 0.0)]
    L["hearth"] = [(8.6, 0.0), (9.6, 1.0), (18.6, 1.0), (21.5, 0.25), (23.4, 0.0)]
    L["lanterns"] = [(8.6, 0.0), (9.8, 0.8), (21.0, 0.8), (23.4, 0.0)]
    # s03 forest (dissolve 23.25-24.75), darkening into 'deeper'; s04 dark (dissolve 37.5-38.5)
    L["forest_hush"] = [(23.25, 0.0), (24.75, 1.0), (A(5, "deeper"), 1.0), (q - 0.2, 0.75), (q + 0.6, 0.6),
                        (38.0, 0.0)]
    L["dark_forest"] = [(A(5, "deeper") - 0.5, 0.0), (q, 0.5), (37.4, 0.5), (38.5, 1.0), (44.4, 1.0), (46.0, 0.7),
                        (51.75, 0.6), (52.25, 0.0)]
    L["run_air"] = [(44.3, 0.0), (45.3, 1.0), (50.1, 1.0), (50.9, 0.3), (51.75, 0.5), (52.25, 1.0),
                    (A(8, "snow") - 0.1, 1.0), (A(8, "snow") + 0.4, 0.0)]
    # s05 ridge (whip 51.75-52.25), rising with the climb; swell into the hard cut at 66.5
    L["ridge_wind"] = [(51.75, 0.0), (52.25, 0.75), (A(8, "ridge"), 0.75), (A(8, "ridge") + 1.5, 1.0),
                       (A(8, "stopped"), 1.0), (61.0, 1.1), (64.0, 1.0), (66.3, 1.35), (66.56, 0.0)]
    # s06 valley (hard cut at 66.5): wide, thins into the Bass grid; flatten 80.5-81.5
    L["valley_wind"] = [(66.44, 0.0), (66.52, 1.0), (77.2, 1.0), (78.6, 0.35), (80.5, 0.3), (81.4, 0.0)]
    L["hoods_sway"] = [(A(11, "hoods") - 0.5, 0.0), (A(11, "hoods") + 0.6, 1.0), (77.0, 1.0), (78.2, 0.0)]
    # s07 still -> s08 fight -> fire
    L["still"] = [(80.5, 0.0), (81.5, 1.0), (fire + 0.2, 1.0), (fire + 1.0, 0.0)]
    L["fire"] = [(fire - 0.05, 0.0), (fire + 0.35, 0.8), (fire + 1.6, 1.0), (110.4, 1.15), (111.1, 0.35),
                 (112.2, 0.0)]
    # s09 dawn (flash 110.5-111.5) -> s10 (dissolve 124.25-125.75)
    L["dawn"] = [(110.9, 0.0), (111.6, 1.0), (124.25, 1.0), (125.75, 0.0)]
    L["morning_wind"] = [(124.25, 0.0), (125.75, 1.0), (133.0, 1.0), (138.0, 0.8), (139.4, 0.0)]
    # s11 dusk (dip 138-140), out as the world flattens into paper (152.0)
    L["dusk"] = [(138.6, 0.0), (140.0, 1.0), (151.6, 1.0), (153.2, 0.0)]
    L["lanterns"] += [(138.8, 0.0), (140.2, 1.0), (151.6, 1.0), (153.0, 0.0)]
    L["silence_floor"] = [(q + 0.1, 0.0), (q + 0.7, 1.0), (37.3, 1.0), (38.0, 0.0)]
    return L


def events():
    """[(film t, sfx name, params, seed, pan)] - ambient events, in narration gaps."""
    E = []
    E += [(16.3, "dog_bark", dict(count=2, dist=0.9), 21, -0.5), (22.7, "dog_bark", dict(count=3, dist=0.95), 22, 0.6)]
    E += [(9.9, "sign_creak", {}, 31, 0.55), (13.5, "sign_creak", {}, 32, 0.55), (17.0, "sign_creak", {}, 33, 0.5),
          (21.3, "sign_creak", {}, 34, 0.45)]
    E += [(25.3, "crow_caw", dict(count=3, dist=0.85), 41, -0.6), (28.95, "crow_caw", dict(count=2, dist=0.5), 42, 0.5),
          (29.25, "crow_flap", {}, 43, 0.4)]
    E += [(26.7, "snow_plop", dict(dist=0.5), 51, 0.0), (31.5, "snow_plop", dict(dist=0.7), 52, 0.0),
          (40.9, "snow_plop", dict(dist=0.6), 53, 0.0)]
    E += [(27.9, "branch_creak", dict(dist=0.6), 61, 0.0), (32.3, "branch_creak", dict(dist=0.4), 62, 0.0),
          (38.8, "branch_creak", dict(dist=0.7), 63, 0.0), (42.4, "branch_creak", dict(dist=0.5), 64, 0.0)]
    E += [(68.3, "crow_caw", dict(count=2, dist=1.0), 71, -0.3)]
    E += [(117.0, "bird_chirp", {}, 91, -0.4), (120.6, "bird_chirp", {}, 92, 0.5)]
    E += [(126.0, "crow_caw", dict(count=1, dist=1.0), 101, 0.6), (129.25, "dog_bark", dict(count=2, dist=0.95), 102, -0.6)]
    E += [(125.9, "sign_creak", {}, 103, 0.5), (129.6, "sign_creak", {}, 104, 0.5), (134.4, "sign_creak", {}, 105, 0.45)]
    E += [(143.95, "owl_hoot", {}, 111, -0.4)]
    return E


# ============================================================================ render
def _cal(x, target, mode="int"):
    if mode == "int":
        lv = dsp.loudness_integrated(x)
    else:
        y = dsp.pad_to(x, max(len(x), n_of(0.4)))
        lv = float(np.max(dsp.loudness_curve(y, win=0.4, hop=0.05)[1]))
    if not np.isfinite(lv) or lv < -100:
        return x
    return x * db2lin(target - lv)


def render_beds(seed=0):
    """-> (beds float32 (N, 2), floor float32 (N, 2), info). The floor (THE SILENCE's hush) is
    kept apart so the mix's silence gate does not take it away."""
    out = np.zeros((N, 2))
    floor = np.zeros((N, 2))
    info = dict(beds=[], events=[])
    auto = automation()
    for name, pts in auto.items():
        env = envelope(pts)
        dst = floor if name == "silence_floor" else out
        for k, (a, b) in enumerate(spans(env)):
            rng = dsp.rng_for("red-amb", name, k, seed)
            x = GEN[name](b - a, rng)
            x = _cal(x, BED_LUFS[name])
            dst[a:b] += x * to_audio(env, a, b)[:, None]
            info["beds"].append(dict(bed=name, t0=round(a / SR, 2), t1=round(b / SR, 2)))
    for (t, name, prm, sd, pan) in events():
        x = sfx_red.render(name, params=prm, seed=sd).astype(np.float64)
        x = _cal(x, EVENT_MAX[name] - (3.0 * prm.get("dist", 0.5) if "dist" in prm else 0.0), "max")
        x = dsp.pan_stereo(x, pan)
        dsp.mix_into(out, x, n_of(t))
        info["events"].append(dict(t=t, sfx=name))
    return out.astype(np.float32), floor.astype(np.float32), info


if __name__ == "__main__":
    import os
    import time
    from .common import OUT
    t0 = time.time()
    amb, floor, info = render_beds()
    amb = amb + floor
    print(f"beds rendered in {time.time() - t0:.1f}s; {len(info['beds'])} bed spans, {len(info['events'])} events")
    print("integrated", round(dsp.loudness_integrated(amb), 2), "TP", round(dsp.true_peak_db(amb), 2))
    os.makedirs(OUT, exist_ok=True)
    dsp.write_wav(os.path.join(OUT, "amb_preview.wav"), amb, bits=24)
