"""SHADOW PLAY ambience beds.

    render_beds(sync, N) -> (amb float32 (N, 2), info)

Rain in five perspectives - the open street (hiss, wash, patter, puddle plinks), her window
glass from inside (dull wash, taps on the pane, a rivulet), the stairwell (rain on a skylight
far above, the shaft's long reverb), apartment 9 (the glass in a hollow, bare room) and,
further off, the hallway and the killer's room. Under them: gutters (a downspout gurgling),
distant traffic (outside / through glass), room tones (her room, apartment 9's empty hollow,
the hallway's lamp hum, the killer's dead room), her radiator ticking, wind over the rooftops
for the crane up the facade, and the sirens of s04 / s10-s11.

Every bed is an on/off envelope with equal-power edges (crossfades follow the transitions in
timeline.json: hard cuts 30-50 ms, iris / bars / tear 1 s, dissolve 1.25 s) times a level
automation in dB. Levels are set as integrated LUFS at 0 dB (narration sits at -16).
"""
from __future__ import annotations

import math
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np  # noqa: E402
from scipy import signal as _sg  # noqa: E402

from audio import dsp, sfx  # noqa: E402
from audio.dsp import SR, TWO_PI, bandpass, brown, db2lin, n_of, pink, sos, white  # noqa: E402
from films.shadowplay.audio import sfx_shadowplay as SP  # noqa: E402

CTRL = 1000

# integrated loudness of each bed at 0 dB (pre-master)
LUFS = dict(rain_street=-27.0, rain_glass=-31.0, rain_stair=-33.0, rain_apt9=-34.0, rain_hall=-38.0, rain_killer=-39.0,
            gutter_ext=-37.0, gutter_int=-45.0, traffic_ext=-37.0, traffic_int=-44.0,
            tone_her=-47.0, tone_apt9=-45.0, tone_hall=-45.0, tone_killer=-48.0, wind=-33.0)


# ---------------------------------------------------------------------------- envelopes
class Bed:
    """On/off spans with equal-power edges x a dB automation, at the control rate."""

    def __init__(self, total):
        self.n = int(math.ceil(total * CTRL)) + 2
        self.t = np.arange(self.n) / CTRL
        self.onoff = np.zeros(self.n)
        self.auto = []

    def on(self, t0, t1, fi=0.2, fo=0.2):
        """Present from t0 to t1; the fade-in is centred on t0 (fi wide), the fade-out on t1."""
        t = self.t
        up = np.clip((t - (t0 - fi / 2)) / max(fi, 1e-3), 0, 1)
        dn = np.clip(((t1 + fo / 2) - t) / max(fo, 1e-3), 0, 1)
        self.onoff = np.maximum(self.onoff, np.sin(0.5 * np.pi * up) * np.sin(0.5 * np.pi * dn))
        return self

    def level(self, *pts):
        """(t, dB) breakpoints, linear in dB between them; held at the ends."""
        self.auto.extend(pts)
        return self

    def env(self):
        if self.auto:
            pts = sorted(self.auto)
            db = np.interp(self.t, [p[0] for p in pts], [p[1] for p in pts])
        else:
            db = np.zeros(self.n)
        return self.onoff * db2lin(db)


def _to_audio(ctrl, a, b):
    return np.interp(np.arange(a, b) / SR, np.arange(len(ctrl)) / CTRL, ctrl)


def _spans(env, N, pad=0.6, gap=3.0):
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
    return [(max(0, int(a / CTRL * SR) - n_of(pad)), min(N, int(b / CTRL * SR) + n_of(pad))) for a, b in out]


# ---------------------------------------------------------------------------- generators
_BANK_IR = {}


def _bank(imp, freqs, qs, gains):
    """Resonator bank on a sparse impulse train via its impulse response (FFT convolution)."""
    key = (tuple(freqs), tuple(qs), tuple(gains))
    ir = _BANK_IR.get(key)
    if ir is None:
        L = n_of(max(0.02, 3.0 * max(q / (np.pi * f) for f, q in zip(freqs, qs))))
        d = np.zeros(L)
        d[0] = 1.0
        ir = dsp.resonator_bank(d, freqs, qs, gains)
        _BANK_IR[key] = ir
    return _sg.oaconvolve(imp, ir)[:len(imp)]


def _imp(n, rate, rng, spread=0.9):
    return dsp.crackle(n, rate, rng, amp_spread=spread)


def rain_street(n, rng):
    """Rain on the open street: broadband hiss, low wash, close patter on asphalt and car roofs,
    puddle plinks, the odd fat drip from a ledge."""
    out = np.zeros((n, 2))
    gust = 1.0 + 0.16 * dsp.smooth_noise(n, 0.12, rng)
    for ch in range(2):
        hiss = bandpass(pink(n, rng), 450, 11000, 2) * 0.55
        wash = sos(brown(n, rng), "lowpass", 360, 2) * 0.35
        pat = _bank(_imp(n, 260, rng), [1900, 3300, 5600, 8200], [5, 7, 9, 6], [1.0, 0.8, 0.6, 0.35]) * 1.6
        pat += sos(_imp(n, 480, rng, 1.2), "highpass", 2500, 2) * 0.5
        roof = _bank(_imp(n, 70, rng, 0.8), [1150, 1720, 2480], [9, 10, 12], [1.0, 0.7, 0.4]) * 0.5
        plink = _bank(_imp(n, 13, rng, 0.7), [640, 910, 1260], [18, 22, 25], [1.0, 0.8, 0.6]) * 1.8
        drips = _bank(_imp(n, 1.6, rng, 0.4), [380, 520], [30, 35], [1.0, 0.7]) * 2.5
        out[:, ch] = (hiss + wash + pat * 0.35 + roof * 0.25 + plink * 0.25 + drips * 0.2) * gust
    return out


def rain_glass(n, rng):
    """Her window from inside: the street's rain dulled by the glass, drops tapping the pane
    (small glassy ticks), a rivulet running down it."""
    out = np.zeros((n, 2))
    for ch in range(2):
        wash = sos(pink(n, rng), "bandpass", (110, 1500), 2) * 0.7 + sos(brown(n, rng), "lowpass", 240, 2) * 0.3
        taps = _bank(_imp(n, 42, rng, 0.8), [2600, 3700, 4900], [6, 8, 9], [1.0, 0.7, 0.4]) * 0.45
        taps += _bank(_imp(n, 6, rng, 0.5), [5200, 7400], [14, 16], [1.0, 0.5]) * 0.25
        riv = bandpass(white(n, rng), 300, 1000, 2) * np.clip(0.5 + 0.7 * dsp.smooth_noise(n, 0.9, rng), 0, None) * 0.05
        out[:, ch] = wash + taps + riv
    return out * (1.0 + 0.1 * dsp.smooth_noise(n, 0.1, rng))[:, None]


def rain_stair(n, rng):
    """The stairwell: rain on a skylight at the top of the shaft, far and dull, smeared by the
    shaft's long reverb."""
    x = sos(rain_glass(n, rng), "lowpass", 1800, 2) * 0.7
    wet = dsp.convolve(x.mean(axis=1), SP.ir("stairwell"))[:n] * 0.6
    return x + wet


def rain_apt9(n, rng):
    """Apartment 9: the same rain through the glass in a bare, hollow room (its flutter)."""
    x = sos(rain_glass(n, rng), "lowpass", 2600, 2)
    wet = dsp.convolve(x.mean(axis=1), SP.ir("apt9"))[:n] * 0.45
    return x + wet


def rain_hall(n, rng):
    """The hallway: rain somewhere beyond the end window - far, low, reverberant."""
    x = sos(rain_glass(n, rng), "lowpass", 800, 2)
    wet = dsp.convolve(x.mean(axis=1), SP.ir("hallway"))[:n] * 0.6
    return x + wet


def rain_killer(n, rng):
    """The killer's room: blinds down, rain behind them, close and dead."""
    x = sos(rain_glass(n, rng), "lowpass", 1100, 2)
    wet = dsp.convolve(x.mean(axis=1), SP.ir("killer"))[:n] * 0.35
    return x + wet


_BUBBLES = {}


def _bubble_bank(rng_seed=17, k=10):
    if k not in _BUBBLES:
        r = np.random.default_rng(rng_seed)
        tpl = []
        for i in range(k):
            f0 = math.exp(r.uniform(math.log(380), math.log(1500)))
            tpl.append(sfx._drop(r, f0, r.uniform(0.005, 0.016), r.uniform(0.3, 0.9)))
        _BUBBLES[k] = tpl
    return _BUBBLES[k]


def gutter(n, rng):
    """A downspout running: water gurgling down a tin pipe (hollow pipe resonances, bubbles
    popping in the flow) and spilling from its shoe onto the pavement."""
    out = np.zeros((n, 2))
    flow = np.clip(0.65 + 0.35 * dsp.smooth_noise(n, 0.25, rng), 0.2, None)
    tpl = _bubble_bank()
    for ch in range(2):
        gur = _bank(_imp(n, 55, rng, 0.9) * flow, [290, 470, 760, 1150], [10, 12, 14, 16], [1.0, 0.8, 0.5, 0.3]) * 1.2
        bub = np.zeros(n)
        for t in tpl:
            imp = _imp(n, 2.2, rng, 0.6) * flow
            bub += _sg.oaconvolve(imp, t)[:n]
        spill = bandpass(white(n, rng), 700, 5000, 2) * (0.6 + 0.4 * flow) * 0.12
        body = sos(brown(n, rng), "bandpass", (80, 400), 2) * 0.25
        out[:, ch] = gur + bub * 0.5 + spill + body
    return out


def wind(n, rng):
    """Wind over the rooftops for the crane up the facade: a moving, hollow whistle-free air
    with slow gusts."""
    out = np.zeros((n, 2))
    gust = np.clip(0.55 + 0.45 * dsp.smooth_noise(n, 0.18, rng), 0.15, None)
    for ch in range(2):
        fc = 380 + 420 * (0.5 + 0.5 * dsp.smooth_noise(n, 0.25, rng))
        x = dsp.tv_bandpass(pink(n, rng), fc, q=0.9, block=256) * 1.2
        x += sos(brown(n, rng), "lowpass", 180, 2) * 0.5
        out[:, ch] = x * gust
    return out


def tone(n, rng, kind):
    """Room tones."""
    out = np.zeros((n, 2))
    t = np.arange(n) / SR
    for ch in range(2):
        if kind == "her":            # her flat: low building rumble, warm air, the radiator's faint hiss
            x = sos(brown(n, rng), "bandpass", (28, 240), 2) * 0.8 + sos(pink(n, rng), "bandpass", (250, 2500), 2) * 0.06
            x += bandpass(white(n, rng), 3000, 8000, 2) * 0.006
        elif kind == "apt9":         # the empty room: hollow - air through the room's modes
            a = pink(n, rng)
            x = sos(brown(n, rng), "bandpass", (32, 280), 2) * 0.7
            x += dsp.resonator_bank(a, [118, 176, 233, 410, 615], [7, 7, 8, 9, 10], [1.0, 0.8, 0.6, 0.4, 0.25]) * 0.5
        elif kind == "hall":         # hallway: air + the hall lamp's mains hum
            x = sos(brown(n, rng), "bandpass", (30, 260), 2) * 0.8 + sos(pink(n, rng), "bandpass", (200, 2000), 2) * 0.08
        else:                        # killer: dead, close
            x = sos(brown(n, rng), "bandpass", (25, 200), 2) * 0.8 + sos(pink(n, rng), "bandpass", (200, 1500), 2) * 0.04
        out[:, ch] = x
    if kind == "hall":
        out += (0.012 * np.sin(TWO_PI * 60 * t) + 0.007 * np.sin(TWO_PI * 120 * t + 1.0) + 0.002 * np.sin(TWO_PI * 180 * t))[:, None]
    return out


GEN = dict(rain_street=rain_street, rain_glass=rain_glass, rain_stair=rain_stair, rain_apt9=rain_apt9,
           rain_hall=rain_hall, rain_killer=rain_killer, gutter_ext=gutter, wind=wind,
           tone_her=lambda n, r: tone(n, r, "her"), tone_apt9=lambda n, r: tone(n, r, "apt9"),
           tone_hall=lambda n, r: tone(n, r, "hall"), tone_killer=lambda n, r: tone(n, r, "killer"))


def _cal(x, target, mode="int"):
    if mode == "int":
        lv = dsp.loudness_integrated(x)
    else:
        lv = float(np.max(dsp.loudness_curve(dsp.pad_to(x, max(len(x), n_of(0.4))), win=0.4, hop=0.05)[1]))
    return x if not np.isfinite(lv) else x * db2lin(target - lv)


# ---------------------------------------------------------------------------- the map
def bed_map(S, total):
    """Every bed's envelope. S: sync points (film s) from cuesheet.sync_points."""
    B = {k: Bed(total) for k in list(GEN) + ["gutter_int", "traffic_ext", "traffic_int"]}
    slam, sirens = S["s10_slam"], S["s10_sirens"]
    pull = S["s12_pullout"]
    # her window glass: s02 dolly through the window -> s03; s05 -> s06 to the stairs; s12
    B["rain_glass"].on(16.6, 41.0, fi=1.2, fo=0.03).on(52.5, 70.3, fi=1.0, fo=0.15).on(141.5, pull + 1.0, fi=1.25, fo=2.0)
    B["rain_glass"].level((19.2, 0), (19.9, -5), (21.2, -5), (21.9, 0), (S["s03_light_on"], 0), (S["s03_light_on"] + 0.5, -2),
                          (S["s03_light_out"], -2), (S["s03_light_out"] + 0.6, -3), (40.0, -1), (52.5, -1))
    B["tone_her"].on(16.6, 41.0, fi=1.2, fo=0.03).on(52.5, 70.3, fi=1.0, fo=0.15).on(141.5, pull + 1.0, fi=1.25, fo=2.0)
    # s05's silent scream: every sound drops out on [scream] for 1.6 s, then the room returns
    sc5 = S["s05_scream"]
    for nm, base in (("rain_glass", -1.0), ("tone_her", 0.0), ("gutter_int", 0.0), ("traffic_int", -2.0)):
        B[nm].level((sc5 - 0.03, base), (sc5, -45.0), (sc5 + 1.6, -45.0), (sc5 + 2.2, base))
    # the open street: s01 rain streaks -> s02; the tilt down; s04 outside; s06 out of the door -> crane; s12 pull-out
    B["rain_street"].on(S["s01_rain"], 16.6, fi=1.8, fo=1.2).on(20.55, 21.4, fi=1.3, fo=1.0)
    B["rain_street"].on(S["s04_street"], 52.5, fi=0.3, fo=1.0)
    B["rain_street"].on(S["s06_street"], 79.5, fi=0.25, fo=1.0)
    B["rain_street"].on(pull + 1.0, 153.5, fi=2.0, fo=1.6)
    B["rain_street"].level((S["s01_rain"], -6), (9.5, 0), (20.0, -3), (21.4, -3), (S["s06_street"], 1.5), (S["s06_crane"], 1.5),
                           (S["s06_crane"] + 1.5, -2.5), (79.5, -3.5), (pull, -2), (pull + 2.5, 0))
    B["gutter_ext"].on(9.0, 16.6, fi=1.0, fo=1.2).on(20.55, 21.4, fi=1.3, fo=1.0).on(S["s04_street"], 52.5, fi=0.3, fo=1.0)
    B["gutter_ext"].on(S["s06_street"], S["s06_crane"] + 1.0, fi=0.25, fo=2.0).on(pull + 1.0, 153.5, fi=2.0, fo=1.6)
    B["gutter_int"].on(16.6, 41.0, fi=1.2, fo=0.03).on(52.5, 70.3, fi=1.0, fo=0.15).on(141.5, pull + 1.0, fi=1.25, fo=2.0)
    # traffic: the city at night (from the flip to night in s01), through glass indoors
    B["traffic_ext"].on(S["s01_flip"] + 0.5, 16.6, fi=2.0, fo=1.2).on(20.55, 21.4, fi=1.3, fo=1.0)
    B["traffic_ext"].on(S["s04_street"], 52.5, fi=0.3, fo=1.0).on(S["s06_street"], 79.5, fi=0.25, fo=1.0).on(pull + 1.0, 153.5, fi=2.0, fo=1.6)
    B["traffic_ext"].level((5.0, -8), (8.0, -3), (9.5, 0), (S["s06_crane"], 0), (S["s06_crane"] + 2.0, -4))
    B["traffic_int"].on(16.6, 41.0, fi=1.2, fo=0.03).on(41.0, S["s04_street"], fi=0.03, fo=0.3).on(52.5, 70.3, fi=1.0, fo=0.15)
    B["traffic_int"].on(79.5, slam, fi=1.0, fo=0.05).on(141.5, pull + 1.0, fi=1.25, fo=2.0)
    B["traffic_int"].level((79.5, -2), (92.0, -2), (92.05, 2), (106.5, 2), (106.55, -2))   # s08 at the glass
    # the stairwell
    B["rain_stair"].on(S["s06_stairs"], S["s06_street"], fi=0.15, fo=0.25)
    # wind over the roofs for the crane up the facade
    B["wind"].on(S["s06_crane"] + 0.6, 79.5, fi=2.2, fo=1.0)
    # apartment 9: s04 (dark, the police), s07 - s10 until the slam
    B["rain_apt9"].on(41.0, S["s04_street"], fi=0.03, fo=0.3).on(79.5, slam, fi=1.0, fo=0.05)
    B["tone_apt9"].on(41.0, S["s04_street"], fi=0.03, fo=0.3).on(79.5, slam, fi=1.0, fo=0.05)
    B["rain_apt9"].level((92.0, 0), (92.05, 3), (106.0, 3), (106.6, 0),           # s08 at the window
                         (S["s09_feet_stop"], 0), (S["s09_feet_stop"] + 0.3, -4), (S["s10_burst"], -4), (S["s10_burst"] + 0.05, 0))
    B["tone_apt9"].level((S["s09_feet_stop"], 0), (S["s09_feet_stop"] + 0.3, -4), (S["s10_burst"], -4), (S["s10_burst"] + 0.05, 0))
    # the hallway after the slam, until the tear
    B["rain_hall"].on(slam, 131.5, fi=0.05, fo=1.0)
    B["tone_hall"].on(slam, 131.5, fi=0.05, fo=1.0)
    # the killer's room
    B["rain_killer"].on(131.5, 141.5, fi=1.0, fo=1.25)
    B["tone_killer"].on(131.5, 141.5, fi=1.0, fo=1.25)
    # the end: everything out with the last windows
    for b in B.values():
        b.level((152.4, 0), (153.45, -40))
    return B


# ---------------------------------------------------------------------------- render
def render_beds(S, N, seed=0):
    total = N / SR
    B = bed_map(S, total)
    out = np.zeros((N, 2))
    info = dict(beds=[], events=[])

    def add(name, x, env, a):
        b = min(N, a + len(x))
        out[a:b] += x[:b - a] * _to_audio(env, a, b)[:, None]
        info["beds"].append(f"{name}@{a / SR:.1f}-{b / SR:.1f}")

    for name, gen in GEN.items():
        env = B[name].env()
        for k, (a, b) in enumerate(_spans(env, N)):
            x = gen(b - a, dsp.rng_for("sp_bed", name, k, seed))
            add(name, _cal(x, LUFS[name]), env, a)
    # gutter / traffic through glass: dulled versions of the exterior beds
    for name, src, lp in (("gutter_int", "gutter_ext", 900.0),):
        env = B[name].env()
        for k, (a, b) in enumerate(_spans(env, N)):
            x = sos(gutter(b - a, dsp.rng_for("sp_bed", name, k, seed)), "lowpass", lp, 2)
            add(name, _cal(x, LUFS[name]), env, a)
    env_e, env_i = B["traffic_ext"].env(), B["traffic_int"].env()
    both = np.maximum(env_e, env_i)
    for k, (a, b) in enumerate(_spans(both, N, gap=6.0)):
        x = sfx.render("city_far", dur=(b - a) / SR, seed=31 + k).astype(np.float64)
        add("traffic_ext", _cal(x, LUFS["traffic_ext"]), env_e, a)
        xi = sos(x, "lowpass", 700, 2)
        add("traffic_int", _cal(xi, LUFS["traffic_int"]), env_i, a)
        del x, xi

    # her radiator ticking (her room only, between the words where possible)
    rr = dsp.rng_for("sp_radiator", seed)
    for k, tt in enumerate((26.9, 33.0, 38.6, 55.6, 68.1, 144.9, 147.2)):
        x = SP.render("radiator_tick", seed=900 + k).astype(np.float64)
        x = SP.reverb(x, "her_room", wet_db=-8.0)
        x = dsp.pan_stereo(_cal(x, -41.0 - rr.uniform(0, 3), "max"), 0.55)
        dsp.mix_into(out, x, n_of(tt))
        info["events"].append(f"radiator@{tt}")

    # sirens: s04 the arriving car's siren winding down outside apartment 9's window
    t0 = S["s04_burst"] - 0.4
    x = SP.render("siren_wail", dur=3.2, params=dict(mode="winddown", cars=1), seed=41).astype(np.float64)
    x = sos(x, "lowpass", 2400, 2)
    x = SP.reverb(x, "apt9", wet_db=-10.0)[:len(x) + n_of(0.8)]
    x = dsp.pan_stereo(_cal(x, -27.0, "max"), 0.35)
    dsp.mix_into(out, dsp.fade(x, 0.25, 0.4), n_of(t0))
    info["events"].append(f"siren_winddown@{t0:.2f}")
    # s10: two cars approaching (the hallway window floods blue / red), then far in s11
    ta = S["s10_sirens"] - 0.1
    tb = S["s11_dissolve"] - 4.0
    x = SP.render("siren_wail", dur=S["s10_tear"] + 0.6 - ta, params=dict(mode="approach", cars=2, period=3.0), seed=101).astype(np.float64)
    x = sos(x, "lowpass", 5000, 2)
    x = _cal(x, -23.0, "max")
    dsp.mix_into(out, dsp.fade(x, 0.8, 0.9), n_of(ta))
    xf = SP.render("siren_wail", dur=tb - (S["s10_tear"] - 0.2), params=dict(mode="far", cars=2, period=3.4), seed=111).astype(np.float64)
    xf = sos(xf, "lowpass", 1400, 2)
    xf = SP.reverb(xf, "killer", wet_db=-12.0)[:len(xf)]
    xf = _cal(xf, -33.0, "int")
    g = np.ones(len(xf))
    tt = np.arange(len(xf)) / SR
    g *= np.clip(1.0 - (tt - (len(xf) / SR - 3.0)) / 3.0, 0, 1) ** 1.5
    dsp.mix_into(out, dsp.fade(xf * g[:, None], 0.9, 0.2), n_of(S["s10_tear"] - 0.2))
    info["events"].append(f"sirens@{ta:.2f}-{tb:.2f}")
    return out.astype(np.float32), info


if __name__ == "__main__":
    import time
    from engine.timing import timeline
    from films.shadowplay.audio import cuesheet
    tl = timeline("shadowplay")
    N = int(round(tl["duration"] * SR))
    sync, _ = cuesheet.sync_points([])
    t0 = time.time()
    amb, info = render_beds(sync, N)
    print(f"beds in {time.time() - t0:.1f}s; integrated {dsp.loudness_integrated(amb):.1f} LUFS, TP {dsp.true_peak_db(amb):.1f}")
    out = os.path.join(_ROOT, "films", "shadowplay", "out")
    os.makedirs(out, exist_ok=True)
    dsp.write_wav(os.path.join(out, "amb_preview.wav"), amb, bits=24)
