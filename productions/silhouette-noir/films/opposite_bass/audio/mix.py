"""OPPOSITE, the Bass cut: score and sound, locked to the beats in films/opposite_bass/world.py.

    python3 films/opposite_bass/audio/mix.py   -> films/opposite_bass/out/audio_master.wav (48 kHz, -16 LUFS)

Bass cut his titles to the music, so this one has a score that leads: a Herrmann-style string
ostinato (staccato chords on the Psycho chord, Bb minor with a major seventh) at 120 bpm, the
same beat the pictures snap to. It ticks under the title, goes to pizzicato on the street,
to a high tremolo in her eye, drives in sixteenths through the quarrel, and stabs once per
cut of the knife. On the red line every footfall is a plucked note: down his stairs, one
note across the street, and up hers a semitone a step, a whole octave to her door.

Voices and real-world foley are the generated recordings of the first cut
(films/opposite/audio/gen), reused: the quarrel, her scream, gasps, breath, his breath, the
mug, stairs, the street and the handle.
"""
from __future__ import annotations

import json
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import numpy as np  # noqa: E402

from audio import dsp  # noqa: E402
from audio.dsp import SR, db2lin, n_of  # noqa: E402
from films.opposite.audio.mix import (env_db, fx, gen, glass, mono, piano, put, shrieks,  # noqa: E402
                                      step_bank)
from films.opposite_bass import world as Wd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "timeline", "timeline.json")) as fh:
    TL = json.load(fh)
DUR = TL["duration"]
N = int(round(DUR * SR))
E8 = Wd.BEAT / 2.0

BB2 = 116.54
SEMI = 2.0 ** (1.0 / 12.0)


def note(semis, base=BB2):
    return base * SEMI ** semis


# the Psycho chord: Bb Db F A (minor, major seventh)
CHORD = (0, 3, 7, 11)


# ----------------------------------------------------------------------------- strings
def bowed(f0, dur, vel=0.7, seed=0, stacc=True, vib=0.003):
    """One string-section note: detuned saws, a bowed body, a little rosin noise."""
    rng = dsp.rng_for("ob-bow", seed, int(f0 * 10))
    n = n_of(dur + (0.12 if stacc else 0.3))
    t = np.arange(n) / SR
    f = f0 * (1.0 + vib * np.sin(2 * np.pi * 5.6 * t + rng.uniform(0, 6.3)) * np.clip((t - 0.12) / 0.2, 0, 1))
    x = sum(dsp.saw(f * d, n) for d in (1.0, 1.0035, 0.9968, 1.0071))
    x = dsp.bandpass(x, max(f0 * 0.9, 90.0), 6500.0, 2)
    x = dsp.biquad(dsp.biquad(x, "peak", 1100.0, 1.2, 4.0), "peak", 2700.0, 1.5, 3.0)
    x = x + 0.05 * dsp.bandpass(dsp.white(n, rng), 2200.0, 7000.0, 2) * np.max(np.abs(x))
    if stacc:
        env = dsp.env_bp([(0.0, 0.0), (0.008, 1.0), (0.05, 0.55), (dur, 0.0), (n / SR, 0.0)], n)
    else:
        env = dsp.env_bp([(0.0, 0.0), (0.06, 1.0), (dur, 0.9), (dur + 0.3, 0.0)], n)
    x = x * env
    return vel * x / (np.max(np.abs(x)) + 1e-9)


def chord(semis, dur, vel=0.7, seed=0, octave=0, stacc=True, spread=(0, 12)):
    out = None
    for i, s in enumerate(semis):
        for o in spread:
            y = bowed(note(s + 12 * octave + o), dur, vel * (1.0 if o == 0 else 0.55), seed + 7 * i + o, stacc)
            out = y if out is None else out[: len(y)] + y[: len(out)]
    return out / len(semis)


def sip(seed=0):
    """A small sip from a hot mug: an airy slurp, then a swallow."""
    rng = dsp.rng_for("ob-sip", seed)
    n = n_of(0.55)
    t = np.arange(n) / SR
    air = dsp.bandpass(rng.standard_normal(n).astype(np.float32), 1600.0, 5200.0, 2)
    air *= np.clip(t / 0.04, 0, 1) * np.exp(-np.clip(t - 0.1, 0, None) / 0.06)
    air *= 0.55 + 0.45 * np.sin(2 * np.pi * 34.0 * t + rng.uniform(0, 6.28))     # it bubbles a little
    g = t - 0.32
    gulp = np.where(g > 0, np.sin(2 * np.pi * (150.0 - 70.0 * np.clip(g / 0.09, 0, 1)) * g) * np.exp(-g / 0.045), 0.0)
    x = (0.6 * air / (np.max(np.abs(air)) + 1e-9) + 0.4 * gulp).astype(np.float32)
    return x


def pizz(f0, vel=0.8, seed=0):
    rng = dsp.rng_for("ob-pizz", seed)
    y = dsp.karplus_strong(f0, 0.9, t60=0.6, brightness=0.45, rng=rng)
    y = dsp.sos(y, "lowpass", 3500.0, 2)
    return vel * y / (np.max(np.abs(y)) + 1e-9)


def tremolo(semis, dur, vel=0.6, seed=0, octave=2):
    """High violins, bowed tremolo (fast repeated bow strokes) on a cluster."""
    x = chord(semis, dur, vel, seed, octave=octave, stacc=False, spread=(0,))
    t = np.arange(len(x)) / SR
    am = 0.55 + 0.45 * np.abs(np.sin(np.pi * 13.0 * t))
    return x * am


def ostinato(bus, t0, t1, step=E8, semis=CHORD, octave=0, vel=(0.4, 0.9), accent=(0, 3), lift=None, seed=0, gain=-14.0):
    """Repeated staccato chords from t0 to t1 (crescendo vel[0] -> vel[1]); accents on the
    given steps of each bar; lift(t) -> semitones shifts the chord as it goes."""
    i = 0
    t = t0
    per_bar = int(round(2.0 / step))
    while t < t1 - 1e-6:
        u = (t - t0) / max(t1 - t0, 1e-6)
        v = vel[0] + (vel[1] - vel[0]) * u
        if i % per_bar in accent:
            v *= 1.35
        sh = lift(t) if lift else 0
        put(bus, chord([s + sh for s in semis], step * 0.6, v, seed + i % 4, octave), t, gain)
        t += step
        i += 1


# ----------------------------------------------------------------------------- the mix
def main():
    music = np.zeros((N, 2), np.float32)
    efx = np.zeros((N, 2), np.float32)
    amb = np.zeros((N, 2), np.float32)
    vox = np.zeros((N, 2), np.float32)
    feet = np.zeros((N, 2), np.float32)
    rev = lambda x, wet=-10.0, seed=0: dsp.reverb(mono(x), "hall", wet_db=wet, seed=seed)

    # ------------------------------------------------------------ TITLE
    ostinato(music, 0.0, Wd.T_TITLE_CUT, vel=(0.45, 0.85), octave=-1, seed=1, gain=0)
    for i, (t0, dur) in enumerate(Wd.STRIPS):                            # the strips: paper swishes
        put(efx, fx("brush_swish", seed=10 + i), t0 + 0.08, -20, pan=0.6 if i % 2 else -0.6)
    put(music, rev(chord(CHORD, 0.5, 1.0, 21, octave=1)), Wd.T_TITLE_CUT, -6)   # the red cut: sforzando
    put(music, shrieks(n_stabs=1, seed=2), Wd.T_TITLE_CUT, -12)
    put(efx, fx("whip", seed=3), Wd.T_TITLE_CUT - 0.02, -12)
    put(efx, fx("whoosh", seed=4, size=0.4), Wd.T_PART, -15, pan=-0.4)
    put(efx, fx("whoosh", seed=5, size=0.4), Wd.T_PART + 0.1, -15, pan=0.4)
    for j in range(6):                                                   # paper floods in
        put(efx, fx("brush_swish", seed=30 + j), Wd.T_FLOOD + 0.06 * j, -19, pan=-0.7 + 0.28 * j)
    for j in range(2):                                                   # the slabs rise
        put(efx, fx("impact", seed=40 + j, size=0.25)[: n_of(1.2)], Wd.T_RISE + 0.12 * j + 0.32, -10, pan=-0.5 + j)
    put(music, rev(chord(CHORD, 1.1, 0.8, 23, octave=-1, stacc=False, spread=(0, -12))), Wd.T_RISE + 0.3, -12)
    ostinato(music, Wd.T_MORPH, Wd.T_DARK, vel=(0.35, 0.55), octave=0, seed=5, gain=-4)
    put(music, piano(note(12 + 7) / 2.0, vel=0.7, seed=1), Wd.T_DARK + 0.1, -12, pan=-0.3)       # her light
    put(music, piano(note(12 + 11) / 2.0, vel=0.7, seed=2), Wd.T_DARK + 0.35, -12, pan=0.3)      # his
    for j in range(6):
        put(efx, fx("clock_tick", seed=50 + j), Wd.T_DARK + 0.06 * ((j * 5) % 8), -24, pan=-0.5 if j < 3 else 0.5)

    # ------------------------------------------------------------ STREET, HER EYE: the quarrel through glass
    city = fx("city_far", dur=Wd.T_EYE - Wd.T_DARK + 0.5, seed=1)
    put(amb, city * dsp.env_bp_db([(0.0, -40), (0.6, 0), (len(city) / SR - 0.4, 0), (len(city) / SR, -60)], len(city))[:, None],
        Wd.T_DARK, -16)
    tick = fx("clock_ticking", dur=Wd.T_ROOM - Wd.T_WIN, seed=3, bpm=120)
    put(music, tick, Wd.T_WIN, -19)
    for i in range(int((Wd.T_EYE - Wd.T_WIN) / Wd.BEAT)):                # pizzicato on the beat
        t = Wd.T_WIN + i * Wd.BEAT
        put(music, pizz(note(0 if i % 4 < 2 else -2, BB2 / 2.0), 0.8, seed=i), t, -10)
    put(music, tremolo((10, 11, 12), Wd.T_ROOM - Wd.T_EYE + 0.2, 0.7, seed=3), Wd.T_EYE, -7)
    put(efx, fx("brush_swish", seed=21), Wd.T_SIP[0] - 0.03, -24)            # in close on her: the sip
    put(vox, dsp.reverb(sip(1), "small_room", wet_db=-18.0, seed=3).mean(axis=1), 6.22, -7)
    q1 = gen("quarrel", 0.0, 6.0)
    q2 = gen("quarrel", Wd.QUARREL_LOOP[1], 6.0)
    q = np.zeros(n_of(Wd.T_RAISE + 0.15 - Wd.QUARREL_AT))
    dsp.mix_into(q, q1[: len(q)], 0)
    a = n_of(Wd.QUARREL_LOOP[0] - Wd.QUARREL_AT)
    xf = n_of(0.08)
    q[a: a + xf] *= np.linspace(1, 0, xf)
    q[a + xf:] = 0.0
    dsp.mix_into(q, q2[: len(q) - a] * np.concatenate([np.linspace(0, 1, xf), np.ones(max(0, len(q) - a - xf))])[: len(q2[: len(q) - a])], a)
    L = len(q) / SR
    t_in = Wd.T_ROOM - Wd.QUARREL_AT                                     # inside his room from here
    far = env_db(glass(q, lp=1700.0, seed=1), [(0.0, -60), (1.0, -60), (1.2, -6), (t_in - 0.05, -2), (t_in, -60), (L, -60)])
    near = env_db(dsp.reverb(dsp.sos(q, "highpass", 120.0, 2), "small_room", wet_db=-14.0, seed=2).mean(axis=1),
                  [(0.0, -60), (t_in - 0.05, -60), (t_in, -2), (L - 0.1, 2), (L - 0.02, 2), (L, -60)])
    put(vox, far + near[: len(far)], Wd.QUARREL_AT, -3)
    for tb in Wd.BOLTS:                                                  # each red zigzag: a tight whip
        put(efx, fx("whip", seed=int(tb * 10)), tb - 0.02, -21 if tb < Wd.T_ROOM else -17, pan=0.2)

    # ------------------------------------------------------------ QUARREL -> KNIFE
    put(efx, fx("whoosh", seed=61, size=0.5), Wd.T_ROOM - 0.35, -13)    # falling into the reflection
    ostinato(music, Wd.T_ROOM, 13.0, vel=(0.45, 0.75), octave=0, seed=7, gain=-2)
    ostinato(music, 13.0, Wd.T_RAISE, step=E8 / 2.0, vel=(0.6, 1.0), octave=0, seed=9, gain=-1,
             lift=lambda t: int((t - 13.0) / 0.25))
    for zt in (12.0, 12.5, 13.0, 13.5):                                  # the frame jumps in: a thud each
        put(efx, fx("impact", seed=int(zt * 10), size=0.08)[: n_of(0.5)], zt, -19)
    put(music, fx("string_tighten", seed=4)[: n_of(1.0)], Wd.T_RAISE - 0.3, -10)
    put(music, tremolo((11, 12, 13), Wd.T_SLASH[0] - Wd.T_RAISE, 0.9, seed=5, octave=2), Wd.T_RAISE, -13)
    sc = gen("scream_a", 0.08, 0.08 + 15.3 - (Wd.T_RAISE + 0.08), fade=0.06)
    put(vox, dsp.reverb(sc, "small_room", wet_db=-12.0, seed=4).mean(axis=1), Wd.T_RAISE + 0.08, -8)
    for j, ts in enumerate(Wd.STABS):                                    # each stab lands
        put(efx, fx("impact", seed=75 + j, size=0.1)[: n_of(0.4)], ts, -8, pan=0.1)
    for j, ts in enumerate(Wd.T_SLASH):                                  # one shriek per cut
        put(music, shrieks(n_stabs=2, every=0.09, f0=1318.5 * SEMI ** j, seed=10 + j), ts - 0.01, -12)
        put(efx, fx("whip", seed=70 + j), ts - 0.02, -8, pan=(-0.4, 0.4, 0.0)[j])
    put(music, fx("stinger", seed=6), Wd.T_SLASH[0], -12)
    put(efx, gen("body_fall", 0.0, 1.3, fade=0.004), Wd.T_SLASH[2] + 0.12, -10, pan=0.2)
    for j in range(9):                                                   # the bars close the window
        put(efx, fx("brush_swish", seed=80 + j), Wd.T_BARS + 0.05 * j, -18, pan=-0.6 if j % 2 else 0.6)
    put(music, rev(chord(CHORD, 0.4, 1.0, 31, octave=-1, spread=(0, -12))), Wd.T_BARS + 0.45, -9)
    put(music, fx("sub_drop", seed=1), Wd.T_BARS + 0.45, -8)

    # ------------------------------------------------------------ HER: the mug
    put(vox, gen("gasp_b", 0.0, 0.9, fade=0.005), Wd.T_GASP, -4)
    put(vox, dsp.sos(gen("stifled", 0.0, 1.5, fade=0.06), "lowpass", 2200.0, 2), Wd.T_HAND + 0.02, -8)
    put(efx, fx("whoosh", seed=91, size=0.25), Wd.T_DROP, -20, pan=0.4)
    put(efx, gen("mug_smash", 0.0, 1.4, fade=0.003), Wd.T_SMASH - 0.005, -3, pan=0.35)
    hb = fx("heartbeat", dur=Wd.T_PATH - Wd.T_SMASH + 0.2, seed=1, bpm=96, bpm_end=128)
    put(music, hb * dsp.env_bp_db([(0.0, -30), (0.4, 0), (len(hb) / SR - 0.3, 0), (len(hb) / SR, -40)], len(hb))[:, None],
        Wd.T_SMASH + 0.3, -12)

    # ------------------------------------------------------------ ARM
    city = fx("city_far", dur=Wd.T_OFF - Wd.T_ARM + 0.3, seed=2)
    put(amb, city * dsp.env_bp_db([(0.0, -30), (0.3, 0), (len(city) / SR, -10)], len(city))[:, None], Wd.T_ARM, -16)
    put(efx, fx("clock_tick", seed=4), Wd.T_HIS_ON, -10, pan=0.4)         # his light, on again
    put(music, rev(chord((0, 1), 2.6, 0.6, 41, octave=-1, stacc=False, spread=(0, -12)), -8.0), Wd.T_HIS_ON, -15)
    put(music, fx("braam", seed=2), Wd.T_GROW, -6)
    put(efx, fx("whoosh", seed=93, size=0.6), Wd.T_GROW - 0.05, -12, pan=-0.2)
    put(efx, fx("whoosh", seed=94, size=0.3), Wd.T_RETRACT - 0.03, -14, pan=0.4)
    runs = step_bank("street_run", thr_db=-14.0, length=0.2)
    for j, t in enumerate((Wd.T_RETRACT + 0.12, Wd.T_RETRACT + 0.3, Wd.T_RETRACT + 0.47)):
        put(feet, glass(runs[j], lp=1500.0, seed=20 + j), t, -14, pan=0.5)
    put(efx, glass(fx("door_close", seed=6), lp=1300.0, seed=5), Wd.T_GONE + 0.4, -10, pan=0.6)

    # ------------------------------------------------------------ OFF
    put(efx, dsp.sos(mono(fx("keys", seed=7))[: n_of(0.3)], "highpass", 2500.0, 2), Wd.T_PULL - 0.2, -24)
    put(efx, fx("clock_tick", seed=6), Wd.T_PULL, -5)
    put(music, fx("sub_drop", seed=3), Wd.T_PULL + 0.05, -12)

    # ------------------------------------------------------------ PATH: a note for every step
    down = step_bank("stairs_down", length=0.26)
    up = step_bank("stairs_up", length=0.26)
    steps = Wd.path_steps()
    for i, (t, _) in enumerate(steps):
        if i < 10:
            s, semis, pan = down[i % len(down)], 7 - i, 0.5
        elif i < 15:
            s, semis, pan = runs[(i - 10) % len(runs)], 0, 0.5 - 0.25 * (i - 10)
        elif i < 27:
            s, semis, pan = up[(i - 15) % len(up)], (i - 15) + 1, -0.4
        else:
            s, semis, pan = up[(i - 27 + 3) % len(up)], 12, -0.5
        put(feet, s, t - 0.01, -6, pan=pan)
        put(music, pizz(note(semis, BB2 / 2.0), 0.9, seed=100 + i), t - 0.01, -8, pan=pan * 0.5)
    put(music, rev(chord(CHORD, 0.6, 0.9, 51, octave=0)), steps[-1][0] + 0.25, -10)   # at her door
    put(efx, fx("door_open", seed=3)[: n_of(0.5)], steps[9][0] + 0.1, -16, pan=0.5)      # out of his building
    put(efx, fx("door_creak", seed=4)[: n_of(0.6)], steps[14][0] + 0.1, -17, pan=-0.4)   # into hers

    # ------------------------------------------------------------ DOOR
    b = gen("her_breath", 1.0, 1.0 + Wd.T_FEET - 0.05 - Wd.T_DOOR, fade=0.03)
    put(vox, env_db(b, [(0.0, -30), (0.4, 0), (len(b) / SR, 0)]), Wd.T_DOOR, -10)
    room = fx("room_tone", dur=Wd.T_END - Wd.T_DOOR, seed=2)
    put(amb, room, Wd.T_DOOR, -18)
    for i, t in enumerate(Wd.HALL_STEPS):                                # his steps down her hall
        put(feet, dsp.sos(up[(i + 4) % len(up)], "lowpass", 1100.0 + 500.0 * i, 2), t, -16 + 3.0 * i)
    for j in range(2):                                                   # he stops at her door
        put(feet, dsp.sos(up[(j + 1) % len(up)], "lowpass", 2600.0, 2), Wd.T_FEET + 0.14 * j, -4 - 3.0 * j)
    hv = gen("his_breath", 0.9, 0.9 + Wd.T_OPEN - (Wd.T_FEET + 0.3), fade=0.08)
    put(vox, dsp.sos(hv, "lowpass", 1500.0, 2), Wd.T_FEET + 0.3, -5)
    for (a0, b0), t0 in zip([(0.06, 0.9), (1.8, 2.55)], Wd.T_KNOB):
        put(efx, gen("handle", a0, b0, fade=0.01, norm=-1.0), t0 - 0.03, -4)
    put(vox, dsp.sos(gen("gasp_a", 0.0, 0.6, fade=0.005), "lowpass", 1500.0, 2), Wd.T_KNOB[1] + 0.5, -16)

    # ------------------------------------------------------------ HIS EYE, END
    put(music, fx("reverse_swell", dur=Wd.T_OPEN - Wd.T_KEY, seed=6), Wd.T_KEY, -9)
    put(music, fx("stinger", seed=9), Wd.T_OPEN, -4)
    put(music, shrieks(n_stabs=1, f0=1396.9, seed=20), Wd.T_OPEN, -10)
    put(music, rev(chord(CHORD, 0.7, 1.0, 61, octave=0, spread=(0, -12, 12))), Wd.T_END, -5)
    put(efx, fx("impact", seed=11, size=0.6), Wd.T_END, -6)
    put(music, shrieks(n_stabs=1, f0=1318.5, seed=21), Wd.T_END_SLASH, -9)
    put(efx, fx("whip", seed=99), Wd.T_END_SLASH - 0.02, -9, pan=0.3)

    # ------------------------------------------------------------ bus, cut, master
    mix = music + efx + amb + vox + feet
    a = int(Wd.T_BLACK * SR)
    r = np.linspace(1.0, 0.0, n_of(0.01))
    mix[a: a + len(r)] *= r[:, None]
    mix[a + len(r):] = 0.0
    mix = dsp.sos(mix, "highpass", 30, 2)
    mix *= db2lin(-16.0 - dsp.loudness_integrated(mix))
    mix = dsp.limiter(mix, ceiling_db=-1.0)
    mix = dsp.fade(mix, 0.01, 0.05)
    out = os.path.join(ROOT, "out")
    os.makedirs(out, exist_ok=True)
    import soundfile as sf
    path = os.path.join(out, "audio_master.wav")
    sf.write(path, mix[:N].astype(np.float32), SR, subtype="PCM_24")
    print(path, "LUFS", round(dsp.loudness_integrated(mix), 2), "TP", round(dsp.true_peak_db(mix), 2),
          "dur", round(len(mix[:N]) / SR, 3))


if __name__ == "__main__":
    main()
