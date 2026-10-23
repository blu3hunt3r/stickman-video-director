"""OPPOSITE: a procedural score, sound design and voices (no words), synced to the beat times
in films/opposite/world.py (film time).

    python3 films/opposite/audio/mix.py      -> films/opposite/out/audio_master.wav (48 kHz stereo, -16 LUFS)

Title: paper swishes as the grid lines slide in, low thuds as the facades rise, one felt-piano
note per window lighting (a falling minor figure), air as the title rides in. s02: the city far
off, a clock ticking under everything (Herrmann tension), whooshes and whips on the camera's
moves; the quarrel heard through glass, rising; the knife's ring, her scream, his grunt, string
shrieks on the slash, the body going down, ringing ears; her gasp, a scream stifled behind her
hand, the cup, panicked breath and her heartbeat; his steps and his run, a door slammed across
the street, the cord of her lamp; his footsteps down, across, up (faster); his breathing behind
her door, her held breath, the handle tried twice, a whimper, the eye; her scream over black,
cut dead.
"""
from __future__ import annotations

import json
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import numpy as np  # noqa: E402

from audio import dsp, sfx  # noqa: E402
from audio.dsp import SR, db2lin, n_of  # noqa: E402
from engine import paperdoll as pd  # noqa: E402
from films.opposite import world as Wd  # noqa: E402
from films.opposite.audio import voice as V  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "timeline", "timeline.json")) as fh:
    TL = json.load(fh)
DUR = TL["duration"]
N = int(round(DUR * SR))
BLACK = Wd.T_BLACK
CUT = BLACK + 0.65               # her scream runs on over black, then is cut dead


def put(bus, x, at, gain_db=0.0, pan=0.0):
    x = np.asarray(x, np.float32)
    if x.ndim == 1:
        x = dsp.pan_mono(x, pan)
    dsp.mix_into(bus, x * db2lin(gain_db), int(round(at * SR)))


def put_track(bus, x, at, gain_db, pos, every=0.05):
    """Mono x panned with world point pos as the camera moves."""
    x = np.asarray(x, np.float64)
    ts = np.arange(0.0, len(x) / SR + every, every)
    p = np.interp(np.arange(len(x)) / SR, ts, [screen_x(pos, at + t) for t in ts])
    th = (p + 1.0) * np.pi / 4.0
    st = np.stack([x * np.cos(th), x * np.sin(th)], axis=1) * db2lin(gain_db)
    dsp.mix_into(bus, st.astype(np.float32), int(round(at * SR)))


def fx(name, dur=None, seed=0, **p):
    return sfx.render(name, dur=dur, params=p, seed=seed)


def piano(f0, dur=2.4, vel=0.6, seed=0):
    return np.asarray(sfx._felt_piano_note(f0, n_of(dur), vel=vel, rng=dsp.rng_for("opp-piano", seed)), np.float32)


def screen_x(p, t):
    """Pan from where a thing sits on screen (-1 left .. 1 right)."""
    s = Wd.to_screen(Wd.camera(t), p)
    return float(np.clip((s[0] - 540.0) / 600.0, -0.8, 0.8))


def steps(t0, t1, n, accel=1.0):
    """n footfall times from t0 to t1; accel > 1 speeds up toward the end."""
    u = np.linspace(0.0, 1.0, n)
    return list(t0 + (t1 - t0) * (u ** (1.0 / accel)))


def mono(x):
    x = np.asarray(x, np.float64)
    return x.mean(axis=1) if x.ndim == 2 else x


def muffle(x, lp=1500.0):
    """Across the street, behind glass."""
    return dsp.sos(mono(x), "lowpass", lp, 4)


def knife_ring(seed=0):
    """The blade catching the light: a swipe of air and a thin metal ring."""
    rng = dsp.rng_for("opp-knife", seed)
    n = n_of(0.9)
    ring = dsp.modal([3150.0, 4620.0, 6230.0, 7900.0], [0.5, 0.35, 0.22, 0.14], [1.0, 0.7, 0.45, 0.3], n)
    air = dsp.bandpass(dsp.white(n, rng), 2500.0, 9000.0, 2) * dsp.env_bp([(0.0, 0.0), (0.07, 1.0), (0.16, 0.0), (0.9, 0.0)], n)
    return 0.6 * ring / (np.max(np.abs(ring)) + 1e-9) + 0.5 * air / (np.max(np.abs(air)) + 1e-9)


def shrieks(n_stabs=5, every=0.13, f0=1318.5, seed=0):
    """Violins stabbing on one high note, bowed hard, each with a little downward slide."""
    out = np.zeros(n_of(every * n_stabs + 0.4))
    for i in range(n_stabs):
        m = n_of(0.24)
        tt = np.arange(m) / SR
        f = f0 * (1.0 + 0.012 * i) * (1.0 + 0.045 * np.exp(-tt / 0.025)) * (1.0 + 0.01 * np.sin(2 * np.pi * 7.0 * tt))
        x = sum(dsp.saw(f * d, m) for d in (1.0, 1.007, 0.994))
        x = dsp.bandpass(x, 900.0, 7500.0, 2)
        x *= dsp.env_bp([(0.0, 0.0), (0.006, 1.0), (0.05, 0.6), (0.22, 0.0), (0.24, 0.0)], m)
        dsp.mix_into(out, x, n_of(i * every))
    out /= np.max(np.abs(out)) + 1e-9
    return dsp.reverb(out, "hall", wet_db=-9.0, seed=seed)


def main():
    music = np.zeros((N, 2), np.float32)
    efx = np.zeros((N, 2), np.float32)
    amb = np.zeros((N, 2), np.float32)
    vox = np.zeros((N, 2), np.float32)
    her_scream = np.zeros((N, 2), np.float32)        # the one sound that survives the cut to black

    # ---------------------------------------------------------------- title
    xs, ys = Wd.grid_lines()
    for i in range(0, len(xs), 3):
        put(efx, fx("brush_swish", seed=10 + i), 0.10 + 0.045 * i, -20, pan=-0.6 + 1.2 * i / len(xs))
    for j in range(0, len(ys), 2):
        put(efx, fx("brush_swish", seed=40 + j), 0.30 + 0.06 * j, -21, pan=0.5 if j % 4 == 0 else -0.5)
    for i, (b, pan) in enumerate((("A", -0.5), ("B", 0.5))):
        put(efx, fx("impact", seed=3 + i, size=0.12)[: n_of(1.2)], 1.30 + 0.15 * i + 0.55, -13, pan=pan)
    put(efx, fx("whoosh", seed=5, size=0.45), 1.95, -15, pan=-0.3)
    # one note per window: a falling minor line, then the last (hers) held
    notes = [659.26, 587.33, 523.25, 493.88, 440.0, 392.0, 349.23, 329.63, 293.66, 440.0]
    for (key, t_on), f0 in zip(Wd.TITLE_ON, notes):
        p = screen_x(Wd.centre(Wd.rect_of(key)), t_on)
        put(music, piano(f0 / 2.0, vel=0.5 if key != Wd.HER else 0.75, seed=int(f0)), t_on, -12, pan=p)
        put(efx, fx("clock_tick", seed=int(f0) % 9), t_on, -24, pan=p)
    put(music, fx("drone_swell", dur=5.0, seed=2), 1.2, -16)

    # ---------------------------------------------------------------- the street at night
    city = fx("city_far", dur=BLACK, seed=1)
    env = dsp.env_bp_db([(0.0, -40), (1.0, -6), (Wd.T_DOOR_PUSH, -6), (Wd.T_DOOR_PUSH + 1.6, -22), (BLACK, -24)], len(city))
    put(amb, city * env[:, None], 0.0, -10)
    room = fx("room_tone", dur=BLACK - Wd.T_DOOR_PUSH, seed=2)
    put(amb, room * dsp.env_bp_db([(0.0, -40), (1.4, 0), (BLACK - Wd.T_DOOR_PUSH, 0)], len(room))[:, None], Wd.T_DOOR_PUSH, -14)
    siren = fx("siren_far", dur=8.0, seed=2)
    put(amb, siren * dsp.env_bp_db([(0.0, -40), (1.5, 0), (6.0, 0), (8.0, -60)], len(siren))[:, None], 18.4, -22)
    # a clock under everything from the push into her window; it stops when the handle turns
    tick = fx("clock_ticking", dur=Wd.T_KNOB[0] - 5.4, seed=3, bpm=96)
    tick *= dsp.env_bp_db([(0.0, -40), (1.5, 0), (len(tick) / SR - 0.05, 0), (len(tick) / SR, -80)], len(tick))[:, None]
    put(music, tick, 5.4, -15)
    # the camera: glides, whips, pushes
    for t0, pan, size, g in ((Wd.T_PUSH, 0.0, 0.3, -18), (Wd.T_GLIDE_OUT + 0.3, 0.5, 0.3, -18), (18.0, 0.0, 0.25, -20),
                             (18.85, 0.4, 0.3, -17), (21.65, 0.5, 0.35, -17)):
        put(efx, fx("whoosh", seed=int(t0 * 10), size=size), t0, g, pan=pan)
    for t0, pan in ((Wd.T_GLIDE_BACK + 0.12, -0.5), (20.9, -0.5)):              # whip pans
        put(efx, fx("whip", seed=int(t0 * 10)), t0, -11, pan=pan)
        put(efx, fx("whoosh", seed=int(t0 * 10) + 1, size=0.5), t0 - 0.05, -14, pan=pan)

    # ---------------------------------------------------------------- the quarrel, the knife
    q = V.through_glass(V.quarrel(Wd.T_RAISE + 0.15 - Wd.T_HEAR, seed=1), lp=1400.0)
    q *= dsp.env_bp_db([(0.0, -60), (0.5, -16), (Wd.T_GLIDE_OUT - Wd.T_HEAR, -12), (12.0 - Wd.T_HEAR, -2),
                        (Wd.T_RAISE - Wd.T_HEAR, 0), (len(q) / SR - 0.05, -2), (len(q) / SR, -60)], len(q))
    put_track(vox, q, Wd.T_HEAR, -4, Wd.HIS_C)
    put(efx, fx("whoosh", seed=31, size=0.5), Wd.T_RAISE - 0.06, -12)          # the crash zoom
    put(efx, knife_ring(1), Wd.T_RAISE + 0.08, -20, pan=-0.15)
    put(music, fx("string_tighten", seed=4)[: n_of(1.6)], Wd.T_RAISE - 0.55, -10)
    t_vs = Wd.T_RAISE + 0.12                                                    # her scream, through his glass
    rel = Wd.T_SLASH - t_vs
    vs = V.scream([(0.0, 540.0), (0.1, 760.0), (rel - 0.05, 800.0), (rel, 830.0), (rel + 0.06, 1060.0),
                   (rel + 0.25, 990.0), (rel + 0.42, 600.0)],
                  [(0.0, 0.0), (0.05, 0.8), (rel - 0.02, 0.85), (rel + 0.03, 1.0), (rel + 0.28, 0.9), (rel + 0.42, 0.0)], seed=1)
    put(vox, V.through_glass(vs, lp=2800.0, wet_db=-8.0), t_vs, -3, pan=0.1)
    put(vox, V.through_glass(V.grunt(1), lp=1800.0), Wd.T_SLASH - 0.05, -9, pan=-0.12)
    put(music, fx("stinger", seed=6), Wd.T_SLASH, -4)
    put(music, shrieks(seed=1), Wd.T_SLASH - 0.01, -11)
    put(efx, fx("whip", seed=7), Wd.T_SLASH - 0.03, -9, pan=0.3)
    t_land = Wd.T_SLASH + 0.45                                                  # she goes down
    put(efx, muffle(fx("body_fall", seed=2, wet=0), 1600.0), t_land, -6, pan=0.15)
    put(efx, muffle(fx("impact", seed=12, size=0.2)[: n_of(1.0)], 900.0), t_land + 0.02, -10, pan=0.15)
    put(efx, muffle(fx("glass_break", seed=13)[: n_of(1.2)], 2600.0), t_land + 0.08, -17, pan=0.25)
    ring = fx("tinnitus", dur=2.8, seed=2)
    put(music, ring * dsp.env_bp_db([(0.0, -30), (0.3, 0), (1.2, -6), (2.8, -60)], len(ring))[:, None], Wd.T_SLASH + 0.15, -22)
    put(efx, fx("clock_tick", seed=2), Wd.T_HIS_OFF, -11, pan=0.1)              # his light: off
    put(music, fx("sub_drop", seed=1), Wd.T_HIS_OFF, -8)

    # ---------------------------------------------------------------- her: the cup, the breath
    put(vox, V.gasp(1), Wd.T_CUP - 0.05, -6)
    st = V.scream([(0.0, 500.0), (0.06, 720.0), (0.4, 690.0), (0.55, 520.0)],
                  [(0.0, 0.0), (0.04, 1.0), (0.4, 0.7), (0.55, 0.0)], seed=3, rough=0.4)
    put(vox, dsp.sos(st, "lowpass", 900.0, 4), Wd.T_CUP + 0.14, -6)           # behind her hand
    put(efx, fx("glass_break", seed=8)[: n_of(1.4)], Wd.T_SHATTER, -12, pan=-0.1)
    for j, t in enumerate((Wd.T_STEP, Wd.T_STEP + 0.2)):                        # she backs off on bare boards
        put(efx, fx("footstep", seed=170 + j, weight=0.4, wet=0), t + 0.22, -22)
    put(efx, fx("chair_creak", seed=9)[: n_of(0.5)], Wd.T_STEP + 0.45, -26)
    hb = fx("heartbeat", dur=Wd.T_DOOR_PUSH - Wd.T_STEP, seed=1, bpm=84, bpm_end=128)
    put(music, hb * dsp.env_bp_db([(0.0, -30), (0.6, 0), (len(hb) / SR, 0)], len(hb))[:, None], Wd.T_STEP, -9)
    b1 = V.breaths(21.9 - (Wd.T_STEP + 0.5), rate0=2.2, rate1=3.1, seed=1)
    b1 *= dsp.env_bp_db([(0.0, -30), (0.4, 0), (len(b1) / SR - 0.6, 0), (len(b1) / SR, -40)], len(b1))
    put_track(vox, b1, Wd.T_STEP + 0.5, -12, Wd.HER_C)
    put(efx, fx("clock_tick", seed=4), Wd.T_HIS_ON, -12, pan=0.4)             # his light: on again
    for j, t in enumerate((Wd.T_POINT - 0.5, Wd.T_POINT - 0.3)):                # his steps toward the glass
        put(efx, muffle(fx("footstep", seed=180 + j, weight=0.9, wet=0)), t + 0.2, -16, pan=0.3)
    put(music, fx("braam", seed=2), Wd.T_POINT + 0.1, -8)
    put(vox, V.whimper(1, dur=0.5, f_hi=640.0, f_lo=430.0), Wd.T_POINT + 0.08, -10, pan=-0.2)
    # his turn and his run out of the room; a door slammed over there
    W = Wd.man_runner()
    falls = sorted(W.t0 + i / pd.HZ for side in W.plants for i, _ in W.plants[side])
    for j, t in enumerate(x for x in falls if Wd.T_RUN + 0.05 < x < Wd.T_RUN + 1.0):
        put(efx, muffle(fx("footstep_run", seed=190 + j, weight=0.9, wet=0), 1700.0), t, -13, pan=0.45)
    put(efx, muffle(fx("door_close", seed=6), 1300.0), Wd.T_RUN + 0.95, -12, pan=0.6)
    put(efx, dsp.sos(mono(fx("keys", seed=7))[: n_of(0.3)], "highpass", 2500.0, 2), Wd.T_REACH + 0.32, -26, pan=-0.1)
    put(efx, fx("clock_tick", seed=6), Wd.T_HER_OFF, -8, pan=-0.1)            # her light: off

    # ---------------------------------------------------------------- his way to her door
    for i, t in enumerate(steps(Wd.T_STAIR_B[0], Wd.T_DOOR_B - 0.15, 9)):
        s = fx("footstep", seed=60 + i, weight=0.8, wet=0)
        put(efx, dsp.sos(s, "lowpass", 1800, 2), t, -16, pan=0.55)
        if i % 3 == 1:
            put(efx, dsp.sos(fx("chair_creak", seed=60 + i), "lowpass", 2400, 2)[: n_of(0.4)], t + 0.03, -26, pan=0.55)
    put(efx, fx("door_open", seed=3), Wd.T_DOOR_B - 0.05, -14, pan=0.6)
    put(efx, fx("door_close", seed=5), Wd.T_DOOR_B + 0.35, -15, pan=0.6)
    for i, t in enumerate(steps(Wd.T_LINE[0] + 0.1, Wd.T_LINE[1], 6)):
        put(efx, fx("footstep_run", seed=80 + i, weight=0.85, wet=0), t, -14, pan=float(np.interp(t, Wd.T_LINE, [0.6, -0.6])))
    put(efx, fx("door_creak", seed=4), Wd.T_DOOR_A - 0.05, -17, pan=-0.6)
    put(efx, fx("door_close", seed=4), Wd.T_DOOR_A + 0.25, -14, pan=-0.6)
    for i, t in enumerate(steps(Wd.T_STAIR_A[0], Wd.T_HALL + 0.4, 9, accel=1.6)):
        s = fx("footstep", seed=100 + i, weight=0.85, wet=0)
        put(efx, s, t, -14 + 0.8 * i, pan=-0.4)
        if i % 3 == 2:
            put(efx, fx("chair_creak", seed=100 + i)[: n_of(0.4)], t + 0.03, -24, pan=-0.4)
    put(music, fx("riser", dur=Wd.T_FEET - Wd.T_HALL, seed=5), Wd.T_HALL, -16)

    # ---------------------------------------------------------------- at her door
    b2 = V.breaths(Wd.T_FEET - 0.15 - Wd.T_DOOR_PUSH, rate0=2.8, rate1=3.4, seed=2)
    b2 *= dsp.env_bp_db([(0.0, -40), (0.6, -2), (len(b2) / SR - 0.08, 0), (len(b2) / SR, -60)], len(b2))
    put(vox, b2, Wd.T_DOOR_PUSH, -10)                                           # she holds her breath at the feet
    for j in range(2):                                                          # he stops at her door
        put(efx, fx("footstep", seed=140 + j, weight=0.9, wet=0), Wd.T_FEET + 0.12 * j, -7)
    hv = V.heavy_breath(Wd.T_EYE - 0.1 - (Wd.T_FEET + 0.25), seed=1)
    hv *= dsp.env_bp_db([(0.0, -40), (0.3, 0), (len(hv) / SR, 0)], len(hv))
    put(vox, dsp.sos(hv, "lowpass", 1400.0, 2), Wd.T_FEET + 0.25, -10)
    for j, t0 in enumerate(Wd.T_KNOB):
        put(efx, fx("door_open", seed=20 + j)[: n_of(0.45)], t0, -5)
    put(vox, dsp.sos(V.whimper(2, dur=0.45, f_hi=560.0, f_lo=420.0), "lowpass", 1400.0, 2), Wd.T_KNOB[1] + 0.42, -14)

    # ---------------------------------------------------------------- the eye, her scream
    put(music, fx("reverse_swell", dur=Wd.T_EYE - Wd.T_KEY_PUSH, seed=6), Wd.T_KEY_PUSH, -10)
    put(music, fx("stinger", seed=9), Wd.T_EYE, -5)
    put(music, fx("impact", seed=11, size=0.6)[: n_of(0.9)], Wd.T_EYE + 0.98, -6)
    t_hs = Wd.T_EYE + 0.62
    L = CUT - t_hs
    hs = V.scream([(0.0, 640.0), (0.07, 980.0), (0.3, 1040.0), (L, 1010.0)],
                  [(0.0, 0.0), (0.03, 1.0), (L, 1.0)], seed=2, rough=0.55)
    put(her_scream, dsp.reverb(hs, "small_room", wet_db=-14.0, seed=3), t_hs, 0)

    # ---------------------------------------------------------------- bus, cuts, master
    mix = music + efx + amb + vox

    def cut(x, t):
        a = int(t * SR)
        r = np.linspace(1.0, 0.0, n_of(0.008))
        x[a: a + len(r)] *= r[:, None]
        x[a + len(r):] = 0.0

    cut(mix, BLACK)
    cut(her_scream, CUT)
    mix += her_scream
    tail = fx("tinnitus", dur=DUR - CUT, seed=1)
    put(mix, tail * dsp.env_bp_db([(0.0, -24), (0.5, -34), (DUR - CUT, -70)], len(tail))[:, None], CUT + 0.05, -20)
    mix = dsp.sos(mix, "highpass", 30, 2)
    lufs = dsp.loudness_integrated(mix)
    mix *= db2lin(-16.0 - lufs)
    mix = dsp.limiter(mix, ceiling_db=-1.0)
    mix = dsp.fade(mix, 0.01, 0.02)
    out = os.path.join(ROOT, "out")
    os.makedirs(out, exist_ok=True)
    import soundfile as sf
    path = os.path.join(out, "audio_master.wav")
    sf.write(path, mix[:N].astype(np.float32), SR, subtype="PCM_24")
    print(path, "LUFS", round(dsp.loudness_integrated(mix), 2), "TP", round(dsp.true_peak_db(mix), 2),
          "dur", round(len(mix[:N]) / SR, 3))


if __name__ == "__main__":
    main()
