"""THE LANTERN (style test): a procedural sound bed, no narration.

    python3 films/lantern/audio/mix.py      -> films/lantern/out/audio_master.wav (48 kHz stereo, -16 LUFS)

s01 title: match strike, one wooden knock per trunk, a low string swell, creaking as the trunks
close in, air through the iris. s02: wind in the trees, her footsteps (found from the animation's
heel contacts), the lantern's creak on its bail, a felt-piano lullaby that thins out as the wood
darkens, a drone that rises under it, breathing and a heartbeat at the eyes, the flare, the run,
the leg's tap, then nothing at the cut to black.
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
from films.lantern import sets  # noqa: E402
from films.lantern.scenes import s01_title as S1, s02_into_the_woods as S2  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "timeline", "timeline.json")) as fh:
    TL = json.load(fh)
DUR = TL["duration"]
N = int(round(DUR * SR))
S2_AT = next(s["start"] for s in TL["scenes"] if s["id"] == "s02")
BLACK = S2_AT + S2.T_BLACK


def put(bus, x, at, gain_db=0.0, pan=0.0):
    x = np.asarray(x, np.float32)
    if x.ndim == 1:
        x = dsp.pan_mono(x, pan)
    dsp.mix_into(bus, x * db2lin(gain_db), int(round(at * SR)))


def fx(name, dur=None, seed=0, **p):
    return sfx.render(name, dur=dur, params=p, seed=seed)


def footsteps():
    """Her footfalls in s02: (film time, running?)."""
    return [(S2_AT + t, run) for t, run in S2.steps()]


def lullaby(n):
    """A small felt-piano tune, A minor, slow; fades as the wood closes in."""
    rng = dsp.rng_for("lullaby")
    notes = [("A4", 0.0), ("C5", 0.6), ("E5", 1.2), ("D5", 2.1), ("C5", 2.7), ("B4", 3.3), ("A4", 4.2),
             ("E4", 5.4), ("A4", 6.0), ("B4", 6.6), ("C5", 7.2), ("B4", 8.1)]
    hz = {"E4": 329.63, "A4": 440.0, "B4": 493.88, "C5": 523.25, "D5": 587.33, "E5": 659.26}
    out = np.zeros(n, np.float32)
    for name, t in notes:
        x = sfx._felt_piano_note(hz[name] / 2.0, n_of(2.6), vel=0.55, rng=rng)
        dsp.mix_into(out, np.asarray(x, np.float32), n_of(t))
    return out


def main():
    rng = dsp.rng_for("lantern-mix")
    music = np.zeros((N, 2), np.float32)
    efx = np.zeros((N, 2), np.float32)
    amb = np.zeros((N, 2), np.float32)

    # ---------------------------------------------------------------- s01: the title
    put(efx, fx("match_strike"), 0.12, -4)
    put(efx, fx("match_flare", seed=2), 0.32, -10)
    for j, (x, w, side, reach, i) in enumerate(S1.TRUNKS):
        knock = dsp.modal([150 + 40 * (i % 4), 390 + 30 * (i % 3), 830], [0.18, 0.09, 0.04], [1.0, 0.5, 0.25], n_of(0.4))
        knock = dsp.bandpass(knock, 70, 2500) * 0.5
        put(efx, knock, 0.6 + 0.09 * j + 0.18, -9 + (2 if w > 60 else -2), pan=(x - 540) / 700.0)
    put(music, fx("drone_swell", dur=4.6, seed=1), 1.4, -12)
    put(efx, fx("door_creak", seed=3), 4.0, -16, )
    put(efx, fx("chair_creak", seed=5), 4.6, -18)
    put(efx, fx("whoosh", seed=4, size=0.5), 5.25, -12)

    # ---------------------------------------------------------------- s02: the wood
    t0 = S2_AT - 0.5
    wind = fx("wind_gust", dur=BLACK - t0, seed=7)
    wind = dsp.sos(wind, "lowpass", 2400, 2)
    env = dsp.env_bp_db([(0.0, -40), (1.2, 0), (9.0, 0), (14.0, -6), (BLACK - t0 - 0.02, -8), (BLACK - t0, -80)], len(wind))
    put(amb, wind * env[:, None], t0, -14)
    # lullaby: from the pull-back until the wood darkens
    lul = lullaby(n_of(11.0))
    lul *= dsp.env_bp_db([(0.0, 0), (7.0, 0), (9.5, -10), (11.0, -60)], len(lul))
    put(music, dsp.reverb(lul, "hall", wet_db=-6, seed=2)[: len(lul) + n_of(2.0)], S2_AT + 0.8, -15, pan=0.0)
    # the dark rising: a drone from 9.6 to the end, swelling at the eyes and at the leg
    dr = fx("drone_swell", dur=BLACK - (S2_AT + 9.6), seed=9)
    put(music, dr, S2_AT + 9.6, -10)
    # footsteps on leaves and roots
    for i, (t, run) in enumerate(footsteps()):
        if t >= BLACK:
            continue
        name = "footstep_run" if run else "footstep"
        s = fx(name, seed=100 + i, weight=0.35 if not run else 0.5, wet=0)
        put(efx, s, t, -13 if not run else -10, pan=-0.05)
    # lantern creak: a squeak at each turn of the swing
    prev = None
    k = 0
    for i in range(int((S2.T_BLACK + 0.5) * 60)):
        t = -0.5 + i / 60.0
        a = float(S2.lantern_angle(t))
        if prev is not None and abs(a - prev[0]) > 1e-5:
            d = a - prev[0]
            if prev[1] is not None and np.sign(d) != np.sign(prev[1]) and abs(a) > 0.04:
                cr = fx("chair_creak", seed=200 + k)
                cr = dsp.sos(cr, "highpass", 900, 2)
                put(efx, cr[: n_of(0.35)], S2_AT + t, -26, pan=0.1)
                k += 1
            prev = (a, d)
        else:
            prev = (a, None)
    # the toy: wheels rattle as she picks it up
    put(efx, fx("keys", seed=4), S2_AT + S2.T_INSERT[0] + 0.7, -22)
    # she lifts the lantern: a soft flare
    put(efx, fx("match_flare", seed=8), S2_AT + S2.T_LIFT + 0.4, -18)
    # the eyes: something breathing, her heartbeat
    breath = dsp.bandpass(dsp.pink(n_of(2.4), rng), 90.0, 700.0)
    breath *= dsp.env_bp([(0.0, 0.0), (0.7, 1.0), (1.0, 0.2), (1.6, 0.9), (2.4, 0.0)], len(breath))
    put(efx, breath, S2_AT + S2.T_EYES - 0.1, -8, pan=0.4)
    put(efx, fx("stinger", seed=3), S2_AT + S2.T_EYES, -14)
    put(music, fx("heartbeat", dur=S2.T_THRUST - S2.T_EYES + 0.2, seed=1, bpm=96, bpm_end=128), S2_AT + S2.T_EYES + 0.3, -9)
    # the thrust: the flame flares, the eyes snap away
    put(efx, fx("match_flare", seed=11), S2_AT + S2.T_THRUST + 0.05, -6)
    put(efx, fx("whoosh", seed=12, size=0.7), S2_AT + S2.T_THRUST + 0.1, -9, pan=0.5)
    # each pair of eyes clicks open
    for j, e in enumerate(S2.EYES):
        put(efx, fx("drip", seed=40 + j), S2_AT + e[3], -16, pan=0.3 + 0.1 * j)
    # the legs: a reverse swell into the first stab, a stab each, the light snuffed
    for j, (t0, g, dx, base) in enumerate(S2.LEGS):
        land = S2_AT + t0 + g
        tap = fx("impact", seed=20 + j, size=0.3)
        put(efx, tap[: n_of(1.2)], land, -9 + 2 * j, pan=0.35)
        put(efx, fx("watch_crack", seed=30 + j), land, -11, pan=0.35)
    first = S2.LEGS[0][0] + S2.LEGS[0][1]
    put(music, fx("reverse_swell", dur=first - S2.T_LEG + 0.6, seed=6), S2_AT + S2.T_LEG - 0.6, -14)
    put(efx, fx("flame_out", seed=3), S2_AT + S2.T_CLOSE, -10)

    # ---------------------------------------------------------------- bus, cut, master
    mix = music + efx + amb
    nb = int(BLACK * SR)
    fade = np.linspace(1.0, 0.0, n_of(0.012))
    mix[nb: nb + len(fade)] *= fade[:, None]
    mix[nb + len(fade):] = 0.0
    tail = fx("tinnitus", dur=DUR - BLACK, seed=1)
    put(mix, tail * dsp.env_bp_db([(0.0, -30), (0.6, -40), (DUR - BLACK, -70)], len(tail))[:, None], BLACK, -18)
    mix = dsp.sos(mix, "highpass", 30, 2)
    lufs = dsp.loudness_integrated(mix)
    mix *= db2lin(-16.0 - lufs)
    mix = dsp.limiter(mix, ceiling_db=-1.0)
    mix = dsp.fade(mix, 0.01, 0.05)
    out = os.path.join(ROOT, "out")
    os.makedirs(out, exist_ok=True)
    import soundfile as sf
    path = os.path.join(out, "audio_master.wav")
    sf.write(path, mix[:N].astype(np.float32), SR, subtype="PCM_24")
    print(path, "LUFS", round(dsp.loudness_integrated(mix), 2), "TP", round(dsp.true_peak_db(mix), 2))


if __name__ == "__main__":
    main()
