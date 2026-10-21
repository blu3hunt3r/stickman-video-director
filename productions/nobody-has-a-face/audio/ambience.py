"""Continuous ambience beds from the ambience map (production bible section 6).

    render_beds(tl, cue_spans=None) -> (amb float32 (N, 2), info dict)

Rain variants: exterior (layered hiss + wash + droplet patter + puddle plinks + gutter drips),
window (muffled through glass + taps on the pane), car (drumming on a steel roof + windscreen
taps), slow (the exterior rain rendered at half speed: S9's slowed, muffled memory) and cell
(high barred window, far and dull). Extra beds: room tones (per space), distant city + far
thunder (S2), faint precinct walla (S3), police radio bursts (S4), crowd walla (S7), far
sirens (S11, S15), tinnitus (S13) and cell drips (S18).

Director notes honoured: NO bulb-hum bed (S1/S9/S16 hum is picture-synced and comes from the
scenes' `bulb_hum` cues). Cuts: beds crossfade over ~200 ms; where the space changes the next
bed J-cuts in ~150 ms before the picture. Designed silences: S12 hard cut at 9.7 s (to the end
of the scene), S13 silence + tinnitus until the rain fades in from 1.2 s, S14 silence
12.1-13.5 s, S18 fade to silence at the end.

Beds yield to picture-synced cues of the same name (room_tone, city_far, crowd_walla,
siren_far, tinnitus: ducked out under the cue span; thunder, radio_static, drip: the bed's own
events are dropped for that scene).
"""
from __future__ import annotations

import math

import numpy as np

from . import dsp, sfx
from .dsp import SR, bandpass, db2lin, n_of, onepole_lp, pink, brown, sos, white

CTRL = 1000                      # control rate (Hz) for envelopes
XF = 0.20                        # crossfade across cuts (s)
JCUT = 0.15                      # J-cut lead where the space changes (s)

# ---------------------------------------------------------------------------- the map
# rain: [(scene_t, kind, level[, ramp_s])] - kind in ext/window/car/slow/cell; level 0..1 (linear
#       amplitude); an optional ramp_s makes a level change start at scene_t and last ramp_s
# room: [(scene_t, kind or None, level)]; extras: named beds / events
AMB_MAP = {
    "s01": dict(rain=[(0.0, "window", 0.25)], room=[(0.0, "lineup", 1.0)]),
    "s02": dict(rain=[(0.0, "ext", 0.9)], city=0.9, thunder=[(1.3, 0.9), (6.9, 0.95)]),
    "s03": dict(rain=[(0.0, "window", 0.2)], room=[(0.0, "precinct", 1.0)], walla=[(0.0, 0.32)]),
    "s04": dict(rain=[(0.0, "ext", 0.7)], radio=[1.05, 3.75, 8.1]),
    "s05": dict(rain=[(0.0, "window", 0.35)], room=[(0.0, "office", 1.0)]),
    "s06": dict(rain=[(0.0, "ext", 0.6), (4.4, "window", 0.3)], room=[(0.0, None, 0.0), (4.4, "office", 1.0)]),
    "s07": dict(rain=[(0.0, "window", 0.3), (4.9, "ext", 0.8)], room=[(0.0, "office", 0.8), (4.9, None, 0.0)],
                walla=[(0.0, 0.0), (4.9, 1.0)]),
    "s08": dict(rain=[(0.0, "ext", 0.6)]),
    "s09": dict(rain=[(0.0, "window", 0.2), (5.6, "slow", 0.8)], room=[(0.0, "interrogation", 1.0), (5.6, None, 0.0)]),
    "s10": dict(rain=[(0.0, "window", 0.3), (4.6, "window", 0.1), (6.4, "ext", 0.8)],
                room=[(0.0, "office", 1.0), (4.6, "court", 1.0), (6.4, None, 0.0)]),
    "s11": dict(rain=[(0.0, "ext", 1.0)], siren=[(0.0, 0.8)]),
    "s12": dict(rain=[(0.0, "ext", 0.8), (5.4, "car", 0.8)], hard_silence=9.7),
    "s13": dict(rain=[(0.0, "ext", 0.0), (1.2, "ext", 1.0, 2.7)], tinnitus=(0.0, 1.9)),
    "s14": dict(rain=[(0.0, "window", 0.3)], room=[(0.0, "office", 1.0)], silence=(12.1, 13.5)),
    "s15": dict(rain=[(0.0, "window", 0.3)], room=[(0.0, "office", 1.0)], siren=[(0.0, 1.0)]),
    "s16": dict(rain=[(0.0, "window", 0.25)], room=[(0.0, "lineup", 1.0)]),
    "s17": dict(rain=[(0.0, "ext", 0.9)]),
    "s18": dict(rain=[(0.0, "cell", 0.25)], room=[(0.0, "cell", 1.0)], drips=True, fade_out=(8.6, 11.6)),
}

# integrated loudness (LUFS) of each bed at level 1.0 (pre-master; narration sits at -16)
RAIN_LUFS = dict(ext=-24.0, window=-25.0, car=-23.5, slow=-25.0, cell=-27.0)
ROOM_LUFS = dict(lineup=-42.0, precinct=-43.0, office=-44.0, interrogation=-42.0, court=-43.0, cell=-41.0)
CITY_LUFS = -35.0
WALLA_LUFS = -31.0
SIREN_LUFS = dict(s11=-33.0, s15=-30.0)
TINNITUS_LUFS = -31.0
THUNDER_MAX = -27.0              # max momentary (LUFS)
RADIO_MAX = -29.0
DRIP_MAX = -33.0


# ---------------------------------------------------------------------------- envelopes
class Track:
    """A bed's level over the film, as (t, level) set-points joined by shaped transitions."""

    def __init__(self, total_s):
        self.total = total_s
        self.pts = []          # (t_start, t_end, a, b) transitions; flat segments implied

    def ramp(self, t0, t1, a, b):
        self.pts.append((t0, t1, a, b))

    def render(self):
        n = int(math.ceil(self.total * CTRL)) + 2
        out = np.zeros(n)
        if not self.pts:
            return out
        pts = sorted(self.pts, key=lambda p: p[0])
        t = np.arange(n) / CTRL
        cur = pts[0][2]
        last_t = 0.0
        for t0, t1, a, b in pts:
            m = (t >= last_t) & (t < t0)
            out[m] = cur
            m = (t >= t0) & (t < t1)
            u = (t[m] - t0) / max(t1 - t0, 1e-6)
            if a > 0 and b > 0:          # level change within a bed: linear in dB
                out[m] = np.exp(np.log(a) + (np.log(b) - np.log(a)) * u)
            elif b >= a:                 # fade in (equal power)
                out[m] = b * np.sin(0.5 * np.pi * u)
            else:                        # fade out
                out[m] = a * np.cos(0.5 * np.pi * u)
            cur = b
            last_t = t1
        out[t >= last_t] = cur
        return out


def _to_audio(ctrl, n, a=0, b=None):
    """Control-rate envelope -> audio-rate samples [a, b)."""
    b = n if b is None else b
    return np.interp(np.arange(a, b) / SR, np.arange(len(ctrl)) / CTRL, ctrl)


def _spans(env, n, pad=1.0, gap=3.0):
    """Active segments (audio sample ranges) of a control envelope, split on silences > gap."""
    nz = np.nonzero(env > 1e-5)[0]
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
    return [(max(0, int(a / CTRL * SR) - n_of(pad)), min(n, int(b / CTRL * SR) + n_of(pad))) for a, b in out]


# ---------------------------------------------------------------------------- generators
def _bank(imp, freqs, qs, gains):
    """Resonator bank applied to a sparse impulse train via its (precomputed) impulse response
    and FFT convolution - identical to filtering, far cheaper on long trains."""
    key = (tuple(freqs), tuple(qs), tuple(gains))
    ir = _BANK_IR.get(key)
    if ir is None:
        L = n_of(max(0.02, 3.0 * max(q / (np.pi * f) for f, q in zip(freqs, qs))))
        d = np.zeros(L)
        d[0] = 1.0
        ir = dsp.resonator_bank(d, freqs, qs, gains)
        _BANK_IR[key] = ir
    from scipy import signal as _sg
    return _sg.oaconvolve(imp, ir)[:len(imp)]


_BANK_IR = {}


def _impulses(n, rate, rng, spread=0.9):
    return dsp.crackle(n, rate, rng, amp_spread=spread)


def rain_ext(n, rng):
    """Exterior rain on a city street: hiss + wash + near patter + puddle plinks + gutter drips."""
    out = np.zeros((n, 2))
    gust = 1.0 + 0.18 * dsp.smooth_noise(n, 0.15, rng)
    for ch in range(2):
        hiss = bandpass(pink(n, rng), 450, 11000, 2) * 0.55
        wash = sos(brown(n, rng), "lowpass", 380, 2) * 0.35
        pat = _impulses(n, 260, rng)
        pat = _bank(pat, [1900, 3300, 5600, 8200], [5, 7, 9, 6], [1.0, 0.8, 0.6, 0.35]) * 1.6
        pat += sos(_impulses(n, 500, rng, 1.2), "highpass", 2500, 2) * 0.5
        plink = _bank(_impulses(n, 14, rng, 0.7), [650, 900, 1250], [18, 22, 25], [1.0, 0.8, 0.6]) * 1.8
        drips = _bank(_impulses(n, 1.8, rng, 0.4), [380, 520], [30, 35], [1.0, 0.7]) * 2.5
        out[:, ch] = (hiss + wash + pat * 0.35 + plink * 0.25 + drips * 0.2) * gust
    return out


def rain_window(n, rng):
    """Rain heard from inside through a window: dull wash + taps on the glass + trickle."""
    out = np.zeros((n, 2))
    for ch in range(2):
        wash = sos(pink(n, rng), "bandpass", (120, 1500), 2) * 0.7
        wash += sos(brown(n, rng), "lowpass", 260, 2) * 0.3
        taps = _bank(_impulses(n, 45, rng, 0.8), [2600, 3700, 4900], [6, 8, 9], [1.0, 0.7, 0.4]) * 0.45
        trickle = bandpass(white(n, rng), 300, 900, 2) * (0.5 + 0.5 * dsp.smooth_noise(n, 1.2, rng)) * 0.05
        out[:, ch] = wash + taps + trickle
    return out * (1.0 + 0.1 * dsp.smooth_noise(n, 0.1, rng))[:, None]


def rain_car(n, rng):
    """Inside the parked car: rain drumming on the steel roof (panel modes), muffled street
    outside, drops on the windscreen."""
    out = np.zeros((n, 2))
    for ch in range(2):
        drum = _impulses(n, 520, rng, 0.8)
        drum = _bank(drum, [235, 410, 610, 905, 1340, 1980], [7, 8, 9, 10, 11, 12], [1.0, 0.9, 0.8, 0.6, 0.4, 0.25]) * 1.4
        drum = sos(drum, "lowpass", 3000, 2)
        outside = sos(pink(n, rng), "bandpass", (150, 1100), 2) * 0.35
        cabin = sos(brown(n, rng), "lowpass", 150, 2) * 0.25
        glass = _bank(_impulses(n, 30, rng, 0.8), [3000, 4400], [7, 9], [1.0, 0.6]) * 0.25
        out[:, ch] = drum + outside + cabin + glass
    return out


def rain_slow(n, rng):
    """S9 memory: exterior rain generated at half speed (one octave down, slowed), dulled."""
    m = n // 2 + 2
    half = rain_ext(m, rng)
    x = dsp.resample(half, SR, 2 * SR)[:n]
    x = dsp.pad_to(x, n)
    x = sos(x, "lowpass", 2600, 2)
    return dsp.reverb(x, "hall", wet_db=-9.0, dry=1.0)[:n]


def rain_cell(n, rng):
    """S18: rain beyond a small high barred window - distant, dull, a little stone reverb."""
    x = rain_window(n, rng)
    x = sos(x, "lowpass", 900, 2)
    return dsp.reverb(x, "cell", wet_db=-8.0, dry=1.0)[:n]


RAIN_GEN = dict(ext=rain_ext, window=rain_window, car=rain_car, slow=rain_slow, cell=rain_cell)


def room_gen(n, rng, kind):
    """Room tones per space (HVAC rumble + air, colour per room)."""
    col = dict(lineup=(30, 260, 0.10, 60), precinct=(28, 300, 0.16, 60), office=(30, 240, 0.10, 0),
               interrogation=(32, 220, 0.08, 120), court=(25, 200, 0.12, 0), cell=(35, 300, 0.14, 0))[kind]
    lo, hi, air, hum = col
    out = np.zeros((n, 2))
    for ch in range(2):
        out[:, ch] = sos(brown(n, rng), "bandpass", (lo, hi), 2) * 0.8 + sos(pink(n, rng), "bandpass", (200, 3000), 2) * air
    if hum:
        t = np.arange(n) / SR
        out += (0.015 * np.sin(2 * np.pi * hum * t) + 0.006 * np.sin(2 * np.pi * 2 * hum * t))[:, None]
    return out


# ---------------------------------------------------------------------------- calibration
def _cal(x, target, mode="int"):
    if mode == "int":
        lv = dsp.loudness_integrated(x)
    else:
        lv = float(np.max(dsp.loudness_curve(dsp.pad_to(x, max(len(x), n_of(0.4))), win=0.4, hop=0.05)[1]))
    if not np.isfinite(lv):
        return x
    return x * db2lin(target - lv)


# ---------------------------------------------------------------------------- main
def _yield_mask(n_ctrl, spans):
    """1 outside the cue spans, 0 inside (200 ms equal-power edges), control rate."""
    m = np.ones(n_ctrl)
    t = np.arange(n_ctrl) / CTRL
    for a, b in spans:
        inside = np.clip(np.minimum((t - (a - 0.2)) / 0.2, ((b + 0.2) - t) / 0.2), 0, 1)
        m = np.minimum(m, np.cos(0.5 * np.pi * inside))
    return m


def render_beds(tl, cue_spans=None, cue_scenes=None, seed=0):
    """Render every bed over the whole film. cue_spans: {name: [(g0, g1), ...]} of the scenes'
    sustained cues; cue_scenes: {name: set(scene ids)} for event-type bed yields."""
    cue_spans = cue_spans or {}
    cue_scenes = cue_scenes or {}
    fps = tl["fps"]
    total = tl["total_frames"] / fps
    N = int(round(tl["total_frames"] * SR / fps))
    scenes = tl["scenes"]
    out = np.zeros((N, 2), dtype=np.float64)
    info = dict(beds=[], yields=[], silences=[])
    rng_root = seed

    # ---------------- rain + room tracks (per kind), with J-cuts on space changes
    rain_tracks = {k: Track(total) for k in RAIN_GEN}
    room_tracks = {k: Track(total) for k in ROOM_LUFS}
    prev_rain = None          # (kind, level)
    prev_room = None
    events = []               # (scene_t global, kind, level) in time order for rain
    for s in scenes:
        m = AMB_MAP.get(s["id"], {})
        for ev in m.get("rain", []):
            ts, kind, lvl = ev[:3]
            events.append((s["start"] + ts, "rain", kind, lvl, ev[3] if len(ev) > 3 else None))
        for (ts, kind, lvl) in m.get("room", [(0.0, None, 0.0)]):
            events.append((s["start"] + ts, "room", kind, lvl, None))
    for (g, typ, kind, lvl, ramp_s) in sorted(events, key=lambda e: (e[0], e[1])):
        tracks = rain_tracks if typ == "rain" else room_tracks
        prev = prev_rain if typ == "rain" else prev_room
        if prev is not None and prev[0] == kind and kind is not None:
            # same bed, level change: smooth 200 ms crossfade centred on the cut (or a timed ramp)
            if abs(prev[1] - lvl) > 1e-6:
                if ramp_s:
                    tracks[kind].ramp(g, g + ramp_s, prev[1], lvl)
                else:
                    tracks[kind].ramp(g - XF / 2, g + XF / 2, prev[1], lvl)
        else:
            j = JCUT if (prev is not None) else 0.0       # space changes: J-cut the incoming bed
            c = g - j
            if prev is not None and prev[0] is not None and prev[1] > 0:
                tracks[prev[0]].ramp(c - XF / 2, c + XF / 2, prev[1], 0.0)
            if kind is not None and lvl > 0:
                tracks[kind].ramp(c - XF / 2, c + XF / 2, 0.0, lvl)
        if typ == "rain":
            prev_rain = (kind, lvl)
        else:
            prev_room = (kind, lvl)

    # designed-silence gate shared by every bed (control rate)
    n_ctrl = int(math.ceil(total * CTRL)) + 2
    tc = np.arange(n_ctrl) / CTRL
    gate = np.ones(n_ctrl)
    for s in scenes:
        m = AMB_MAP.get(s["id"], {})
        if "hard_silence" in m:                       # S12: cut to nothing at 9.7 s, until the next scene
            a = s["start"] + m["hard_silence"]
            b = s["start"] + s["duration"]
            gate[(tc >= a) & (tc < b)] = 0.0
            ramp = (tc >= a - 0.004) & (tc < a)
            gate[ramp] = np.minimum(gate[ramp], (a - tc[ramp]) / 0.004)
            info["silences"].append(dict(scene=s["id"], kind="hard", t0=a, t1=b))
        if "silence" in m:                            # S14: out fast, back in gently
            a = s["start"] + m["silence"][0]
            b = s["start"] + m["silence"][1]
            g = np.ones(n_ctrl)
            g[(tc >= a) & (tc < b)] = 0.0
            r = (tc >= a - 0.06) & (tc < a)
            g[r] = np.cos(0.5 * np.pi * (tc[r] - (a - 0.06)) / 0.06)
            r = (tc >= b) & (tc < b + 0.45)
            g[r] = np.sin(0.5 * np.pi * (tc[r] - b) / 0.45)
            gate = np.minimum(gate, g)
            info["silences"].append(dict(scene=s["id"], kind="soft", t0=a, t1=b))
        if "fade_out" in m:                           # S18: fade to silence at the end
            a = s["start"] + m["fade_out"][0]
            b = s["start"] + m["fade_out"][1]
            g = np.ones(n_ctrl)
            r = (tc >= a) & (tc < b)
            g[r] = np.cos(0.5 * np.pi * (tc[r] - a) / (b - a)) ** 1.3
            g[tc >= b] = 0.0
            gate = np.minimum(gate, g)
            info["silences"].append(dict(scene=s["id"], kind="fade", t0=a, t1=b))
    s13_tin = AMB_MAP["s13"]["tinnitus"]

    def add_bed(name, x, env_ctrl, a=0, yield_name=None):
        """x covers samples [a, a+len(x)); env_ctrl is the full-film control envelope."""
        e = env_ctrl * gate
        if yield_name and cue_spans.get(yield_name):
            y = _yield_mask(n_ctrl, cue_spans[yield_name])
            lost = e * (1.0 - y)
            if np.max(lost) > 0.05:
                k = np.nonzero(lost > 0.05)[0]
                info["yields"].append(dict(bed=name, to=yield_name, t0=round(k[0] / CTRL, 2), t1=round(k[-1] / CTRL, 2)))
            e = e * y
        b = min(N, a + len(x))
        out[a:b] += x[:b - a] * _to_audio(e, N, a, b)[:, None]
        info["beds"].append(name)

    def add_event(x, g):
        a = n_of(g)
        b = min(N, a + len(x))
        if b > a:
            out[a:b] += x[:b - a] * _to_audio(gate, N, a, b)[:, None]

    # rain
    for kind, tr in rain_tracks.items():
        env = dsp.pad_to(tr.render()[:n_ctrl], n_ctrl)
        for k, (a, b) in enumerate(_spans(env, N)):
            x = RAIN_GEN[kind](b - a, dsp.rng_for("rain", kind, k, rng_root))
            x = _cal(x, RAIN_LUFS[kind])
            add_bed(f"rain_{kind}#{k}", x, env, a)
    # room tones
    for kind, tr in room_tracks.items():
        env = dsp.pad_to(tr.render()[:n_ctrl], n_ctrl)
        for k, (a, b) in enumerate(_spans(env, N)):
            x = _cal(room_gen(b - a, dsp.rng_for("room", kind, k, rng_root), kind), ROOM_LUFS[kind])
            add_bed(f"room_{kind}#{k}", x, env, a, yield_name="room_tone")

    def scene(sid):
        return next(s for s in scenes if s["id"] == sid)

    def window_env(g0, g1, lvl=1.0, fin=XF, fout=XF):
        tr = Track(total)
        tr.ramp(g0 - fin / 2, g0 + fin / 2, 0.0, lvl)
        tr.ramp(g1 - fout / 2, g1 + fout / 2, lvl, 0.0)
        return dsp.pad_to(tr.render()[:n_ctrl], n_ctrl)

    def put_sustained(name, sfx_name, g0, g1, target, lvl=1.0, fin=XF, fout=XF, params=None, seed=0, yield_name=None):
        a = max(0, n_of(g0 - 1.0))
        b = min(N, n_of(g1 + 1.0))
        x = sfx.render(sfx_name, dur=(b - a) / SR, params=params, seed=seed).astype(np.float64)
        x = _cal(x, target)
        add_bed(name, x, window_env(g0, g1, lvl, fin, fout), a, yield_name=yield_name)

    # S2 distant city + far thunder
    s = scene("s02")
    put_sustained("city_far", "city_far", s["start"] - JCUT, s["start"] + s["duration"], CITY_LUFS, AMB_MAP["s02"]["city"],
                  seed=2, yield_name="city_far")
    for k, (ts, d) in enumerate(AMB_MAP["s02"]["thunder"]):
        if "s02" in cue_scenes.get("thunder", set()):
            info["yields"].append(dict(bed="thunder_far", to="thunder", scene="s02"))
            break
        x = _cal(sfx.render("thunder", params=dict(distance=d), seed=20 + k).astype(np.float64), THUNDER_MAX - 3 * k, "max")
        g = s["start"] + ts
        add_event(x, g)
        info["beds"].append(f"thunder_far@{g:.2f}")
    # S3 faint precinct walla; S7 crowd from 4.9 s
    s = scene("s03")
    put_sustained("walla_precinct", "crowd_walla", s["start"] - JCUT, s["start"] + s["duration"], WALLA_LUFS - 9,
                  params=dict(voices=10), seed=3, yield_name="crowd_walla")
    s = scene("s07")
    g0 = s["start"] + 4.9 - JCUT
    put_sustained("walla_street", "crowd_walla", g0, s["start"] + s["duration"] + 0.6, WALLA_LUFS, fout=0.8,
                  params=dict(voices=16), seed=7, yield_name="crowd_walla")
    # S4 police radio bursts
    s = scene("s04")
    if "s04" in cue_scenes.get("radio_static", set()):
        info["yields"].append(dict(bed="radio_bursts", to="radio_static", scene="s04"))
    else:
        for k, ts in enumerate(AMB_MAP["s04"]["radio"]):
            x = _cal(sfx.render("radio_static", seed=40 + k).astype(np.float64), RADIO_MAX - (2 if k else 0), "max")
            x = dsp.pan_stereo(dsp.reverb(x, "street", wet_db=-8)[:len(x) + n_of(0.6)], [-0.55, 0.5, -0.3][k % 3])
            add_event(x, s["start"] + ts)
            info["beds"].append(f"radio@{s['start'] + ts:.2f}")
    # S11 / S15 sirens
    for sid in ("s11", "s15"):
        s = scene(sid)
        put_sustained(f"siren_{sid}", "siren_far", s["start"] - (0.3 if sid == "s15" else 0.0), s["start"] + s["duration"],
                      SIREN_LUFS[sid], AMB_MAP[sid]["siren"][0][1], fin=0.6 if sid == "s11" else 1.2, fout=0.4,
                      params=dict(period=4.4 if sid == "s11" else 3.6), seed=11 if sid == "s11" else 15, yield_name="siren_far")
    # S13 tinnitus (before the rain comes back)
    s = scene("s13")
    t0, t1 = s13_tin
    g0, g1 = s["start"] + t0, s["start"] + t1
    a, b = n_of(g0), n_of(g1)
    x = _cal(sfx.render("tinnitus", dur=(b - a) / SR, seed=13).astype(np.float64), TINNITUS_LUFS)
    tr = Track(total)
    tr.ramp(g0, g0 + 0.25, 0.0, 1.0)
    tr.ramp(g1 - 0.9, g1, 1.0, 0.0)
    env = dsp.pad_to(tr.render()[:n_ctrl], n_ctrl)
    if cue_spans.get("tinnitus"):
        y = _yield_mask(n_ctrl, cue_spans["tinnitus"])
        if np.max(env * (1 - y)) > 0.05:
            info["yields"].append(dict(bed="tinnitus", to="tinnitus"))
        env = env * y
    out[a:a + len(x)] += x * _to_audio(env, N, a, a + len(x))[:, None]   # tinnitus ignores the gate (it IS the silence)
    info["beds"].append("tinnitus")
    # S18 cell drips
    s = scene("s18")
    if "s18" in cue_scenes.get("drip", set()):
        info["yields"].append(dict(bed="drips", to="drip", scene="s18"))
    else:
        r = dsp.rng_for("drips", rng_root)
        tt = 0.6
        k = 0
        while tt < 9.2:
            x = _cal(sfx.render("drip", seed=180 + k).astype(np.float64), DRIP_MAX - r.uniform(0, 4), "max")
            x = dsp.pan_stereo(dsp.reverb(x, "cell", wet_db=-6), r.uniform(-0.4, 0.4))
            add_event(x, s["start"] + tt)
            tt += r.uniform(1.3, 2.9)
            k += 1
        info["beds"].append(f"drips x{k}")
    return out.astype(np.float32), info


if __name__ == "__main__":
    import sys
    import os
    import time
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from engine.timing import timeline
    t0 = time.time()
    amb, info = render_beds(timeline())
    print(f"beds rendered in {time.time() - t0:.1f}s: {info['beds']}")
    print("integrated", dsp.loudness_integrated(amb))
    dsp.write_wav(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out", "amb_preview.wav"), amb, bits=24)
