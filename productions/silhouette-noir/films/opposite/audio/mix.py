"""OPPOSITE (style test): a procedural score and sound design, no narration, synced to the
beat times in films/opposite/world.py (film time).

    python3 films/opposite/audio/mix.py      -> films/opposite/out/audio_master.wav (48 kHz stereo, -16 LUFS)

Title: paper swishes as the grid lines slide in, low thuds as the facades rise, one felt-piano
note per window lighting (a falling minor figure), air as the title rides in. s02: the city far
off, a clock ticking under everything (Herrmann tension), whooshes on the camera's glides,
strings tightening into the knife, the stinger on the slash, the click of his light, the cup,
her heartbeat, his footsteps down the stairs, across the street, up her stairs (faster), the
handle tried twice, a reverse swell into the eye, and silence on black.
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
from films.opposite import world as Wd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "timeline", "timeline.json")) as fh:
    TL = json.load(fh)
DUR = TL["duration"]
N = int(round(DUR * SR))
BLACK = Wd.T_BLACK


def put(bus, x, at, gain_db=0.0, pan=0.0):
    x = np.asarray(x, np.float32)
    if x.ndim == 1:
        x = dsp.pan_mono(x, pan)
    dsp.mix_into(bus, x * db2lin(gain_db), int(round(at * SR)))


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


def main():
    music = np.zeros((N, 2), np.float32)
    efx = np.zeros((N, 2), np.float32)
    amb = np.zeros((N, 2), np.float32)

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
    # a clock under everything from the push into her window; it stops when the handle turns
    tick = fx("clock_ticking", dur=Wd.T_KNOB[0] - 5.4, seed=3, bpm=96)
    tick *= dsp.env_bp_db([(0.0, -40), (1.5, 0), (len(tick) / SR - 0.05, 0), (len(tick) / SR, -80)], len(tick))[:, None]
    put(music, tick, 5.4, -15)
    # camera glides
    for t0, pan in ((Wd.T_PUSH, 0.0), (Wd.T_GLIDE_OUT + 0.3, 0.5), (Wd.T_GLIDE_BACK + 0.3, -0.5), (21.1, 0.0)):
        put(efx, fx("whoosh", seed=int(t0 * 10), size=0.3), t0, -18, pan=pan)

    # ---------------------------------------------------------------- the quarrel and the knife
    put(music, fx("string_tighten", seed=4)[: n_of(1.6)], Wd.T_RAISE - 0.55, -10)
    put(music, fx("stinger", seed=6), Wd.T_SLASH, -4)
    put(efx, fx("whip", seed=7), Wd.T_SLASH - 0.03, -10, pan=0.3)
    put(efx, fx("clock_tick", seed=2), Wd.T_HIS_OFF, -12, pan=0.2)        # his light: off
    put(music, fx("sub_drop", seed=1), Wd.T_HIS_OFF, -8)

    # ---------------------------------------------------------------- her: the cup, the heartbeat
    put(efx, fx("glass_break", seed=8)[: n_of(1.4)], Wd.T_SHATTER, -16, pan=-0.1)
    hb = fx("heartbeat", dur=Wd.T_DOOR_PUSH - Wd.T_STEP, seed=1, bpm=84, bpm_end=128)
    put(music, hb * dsp.env_bp_db([(0.0, -30), (0.6, 0), (len(hb) / SR, 0)], len(hb))[:, None], Wd.T_STEP, -9)
    put(efx, fx("clock_tick", seed=4), Wd.T_HIS_ON, -12, pan=0.4)          # his light: on again
    put(music, fx("braam", seed=2), Wd.T_POINT + 0.1, -9)
    put(efx, fx("clock_tick", seed=6), Wd.T_HER_OFF, -10, pan=-0.3)        # her light: off

    # ---------------------------------------------------------------- his way to her door
    for i, t in enumerate(steps(Wd.T_STAIR_B[0], Wd.T_DOOR_B - 0.15, 9)):
        s = fx("footstep", seed=60 + i, weight=0.8, wet=0)
        put(efx, dsp.sos(s, "lowpass", 1800, 2), t, -18, pan=0.55)
    put(efx, fx("door_open", seed=3), Wd.T_DOOR_B - 0.05, -16, pan=0.6)
    for i, t in enumerate(steps(Wd.T_LINE[0] + 0.1, Wd.T_LINE[1], 6)):
        put(efx, fx("footstep", seed=80 + i, weight=0.85, wet=0), t, -15, pan=float(np.interp(t, Wd.T_LINE, [0.6, -0.6])))
    put(efx, fx("door_close", seed=4), Wd.T_DOOR_A + 0.15, -14, pan=-0.6)
    for i, t in enumerate(steps(Wd.T_STAIR_A[0], Wd.T_HALL + 0.4, 9, accel=1.6)):
        s = fx("footstep", seed=100 + i, weight=0.85, wet=0)
        put(efx, s, t, -15 + 0.8 * i, pan=-0.4)
    put(music, fx("riser", dur=Wd.T_FEET - Wd.T_HALL, seed=5), Wd.T_HALL, -16)
    for j in range(2):                                                    # he stops at her door
        put(efx, fx("footstep", seed=140 + j, weight=0.9, wet=0), Wd.T_FEET + 0.12 * j, -8)
    for j, t0 in enumerate(Wd.T_KNOB):
        put(efx, fx("door_open", seed=20 + j)[: n_of(0.45)], t0, -6)

    # ---------------------------------------------------------------- the eye
    put(music, fx("reverse_swell", dur=Wd.T_EYE - Wd.T_KEY_PUSH, seed=6), Wd.T_KEY_PUSH, -10)
    put(music, fx("stinger", seed=9), Wd.T_EYE, -5)
    put(music, fx("impact", seed=11, size=0.6)[: n_of(0.9)], Wd.T_EYE + 0.98, -6)

    # ---------------------------------------------------------------- bus, cut, master
    mix = music + efx + amb
    nb = int(BLACK * SR)
    ramp = np.linspace(1.0, 0.0, n_of(0.01))
    mix[nb: nb + len(ramp)] *= ramp[:, None]
    mix[nb + len(ramp):] = 0.0
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
