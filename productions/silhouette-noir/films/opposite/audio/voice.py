"""OPPOSITE: procedural voices, no recordings and no words: screams, gasps, panicked breath,
whimpers, a man's grunt and breathing, and a quarrel heard through glass.

Every voice is source -> filter: a band-limited glottal pulse train on an f0 contour (with
vibrato, jitter and, for screams, subharmonic roughness), plus breath noise, through formant
resonators, a soft clip and an envelope. Mono float64 arrays at dsp.SR.
"""
from __future__ import annotations

import numpy as np
from scipy import signal

from audio import dsp, sfx
from audio.dsp import SR, n_of

# open "aah" at a high pitch: F1 rides up toward f0
SCREAM_F = [(1050.0, 4.0, 1.0), (1650.0, 6.0, 0.75), (2950.0, 9.0, 0.5), (3900.0, 10.0, 0.3), (5200.0, 8.0, 0.12)]
GASP_F = [(820.0, 5.0, 1.0), (1350.0, 6.0, 0.8), (2700.0, 8.0, 0.5), (4200.0, 6.0, 0.3)]
HUM_F = [(290.0, 6.0, 1.0), (1100.0, 8.0, 0.18), (2300.0, 8.0, 0.25), (3200.0, 8.0, 0.1)]
GRUNT_F = [(560.0, 5.0, 1.0), (1150.0, 6.0, 0.6), (2500.0, 8.0, 0.3), (3400.0, 8.0, 0.12)]


def _rms_norm(x):
    return x / (np.sqrt(np.mean(x ** 2)) + 1e-9)


def _contour(points, n):
    """f0 (Hz) through (t, hz) breakpoints, interpolated in log frequency."""
    ts, hz = zip(*points)
    return np.exp(np.interp(np.arange(n) / SR, ts, np.log(hz)))


def _bank(x, formants):
    f, q, g = zip(*formants)
    return dsp.resonator_bank(x, list(f), list(q), list(g))


def _voice(f0, rng, formants, breath=0.12, rough=0.0, jitter=0.012, vib=(6.0, 0.02), drive=2.2, src_mix=0.12,
           wobble=0.0, chaos=0.0):
    """Voiced sound on contour f0 through fixed formants; unit-ish level, soft clipped.
    wobble: slow irregular pitch drift (a strained voice); chaos: noisy fast AM (harshness)."""
    n = len(f0)
    t = np.arange(n) / SR
    f = f0 * (1.0 + vib[1] * np.sin(2 * np.pi * vib[0] * t + rng.uniform(0, 2 * np.pi)) * (0.4 + 0.6 * np.clip(t / 0.35, 0, 1)))
    f = f * (1.0 + jitter * dsp.smooth_noise(n, 25.0, rng) + wobble * dsp.smooth_noise(n, 7.0, rng))
    src = dsp.pulse_train(f, n, SR, rng=rng)
    if rough > 0.0:
        # period doubling (a subharmonic) and fast AM: the tearing edge of a real scream
        src *= 1.0 + rough * np.sin(np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * dsp.smooth_noise(n, 3.0, rng))
        src *= 1.0 + 0.5 * rough * np.sin(2 * np.pi * np.cumsum(60.0 + 25.0 * dsp.smooth_noise(n, 2.0, rng)) / SR)
    if chaos > 0.0:
        src *= 1.0 + chaos * dsp.smooth_noise(n, 140.0, rng)
    src = _rms_norm(src)
    noise = _rms_norm(dsp.bandpass(dsp.white(n, rng), 900.0, 7000.0, 2))
    x = src + breath * noise
    y = _rms_norm(_bank(x, formants) + src_mix * src)
    return np.tanh(drive * 0.35 * y)


def scream(points, env, seed=0, rough=0.5, breath=0.3, formants=SCREAM_F, drive=3.0):
    """A scream on an f0 contour [(t, hz)] with an amplitude envelope [(t, level)]."""
    rng = dsp.rng_for("opp-scream", seed)
    n = n_of(points[-1][0])
    y = _voice(_contour(points, n), rng, formants, breath=breath, rough=rough, jitter=0.02, vib=(6.4, 0.012),
               drive=drive, wobble=0.03, chaos=0.4)
    return dsp.sos(y * dsp.env_bp(env, n), "highpass", 220.0, 2)


def gasp(seed=0, dur=0.45, pitch=560.0):
    """A sharp in-breath: bright noise through an open vowel, a thin squeak of voice on top."""
    rng = dsp.rng_for("opp-gasp", seed)
    n = n_of(dur)
    air = _rms_norm(_bank(dsp.white(n, rng), GASP_F))
    v = _voice(_contour([(0.0, pitch), (dur * 0.3, pitch * 1.18), (dur, pitch * 0.92)], n), rng, GASP_F,
               breath=0.4, drive=1.4)
    y = air + 0.45 * v * dsp.env_bp([(0.0, 0.0), (0.03, 1.0), (0.14, 0.25), (dur, 0.0)], n)
    return y * dsp.env_bp([(0.0, 0.0), (0.02, 1.0), (0.11, 0.6), (dur, 0.0)], n)


def whimper(seed=0, dur=0.55, f_hi=520.0, f_lo=380.0):
    """A shut-mouth whimper ("mm"), falling."""
    rng = dsp.rng_for("opp-whimper", seed)
    n = n_of(dur)
    f0 = _contour([(0.0, f_hi * 0.9), (0.08, f_hi), (dur, f_lo)], n)
    y = _voice(f0, rng, HUM_F, breath=0.25, rough=0.12, vib=(7.5, 0.04), drive=1.6, src_mix=0.05)
    return dsp.sos(y * dsp.env_bp([(0.0, 0.0), (0.06, 1.0), (dur * 0.6, 0.7), (dur, 0.0)], n), "lowpass", 3000.0, 2)


def breaths(dur, rate0=2.0, rate1=3.0, seed=0, voiced=0.3):
    """Panicked breathing: quick in-breaths and shaky out-breaths, speeding up from rate0 to
    rate1 breaths per second; some out-breaths catch in the throat (a little voice)."""
    rng = dsp.rng_for("opp-breath", seed)
    n = n_of(dur)
    out = np.zeros(n + n_of(1.0))
    t = 0.0
    i = 0
    while t < dur:
        rate = rate0 + (rate1 - rate0) * t / dur
        cyc = 1.0 / rate * rng.uniform(0.9, 1.1)
        lin, lout = cyc * 0.42, cyc * 0.55
        m = n_of(lin)
        x = dsp.bandpass(dsp.white(m, rng), 1300.0, 5200.0, 2)
        x = _rms_norm(x + 0.6 * dsp.biquad(x, "bandpass", 1700.0, 4.0))
        x *= dsp.env_bp([(0.0, 0.0), (lin * 0.7, 1.0), (lin, 0.0)], m)
        dsp.mix_into(out, x * 0.8, n_of(t))
        m = n_of(lout)
        x = dsp.bandpass(dsp.white(m, rng), 450.0, 2600.0, 2)
        x = _rms_norm(x + 0.7 * dsp.biquad(x, "bandpass", 900.0, 4.0))
        if rng.uniform() < voiced:
            f0 = _contour([(0.0, 470.0), (lout, 360.0)], m)
            x = x + 0.6 * _voice(f0, rng, HUM_F, breath=0.3, rough=0.15, vib=(8.0, 0.05), drive=1.3)
        x *= dsp.env_bp([(0.0, 0.0), (0.03, 1.0), (lout * 0.5, 0.6), (lout, 0.0)], m)
        dsp.mix_into(out, x * 0.6, n_of(t + lin + 0.02))
        t += cyc
        i += 1
    return out[:n] * dsp.env_bp([(0.0, 0.0), (0.2, 1.0), (dur - 0.05, 1.0), (dur, 0.0)], n)


def grunt(seed=0, dur=0.32):
    """A man's effort grunt as the knife comes down."""
    rng = dsp.rng_for("opp-grunt", seed)
    n = n_of(dur)
    f0 = _contour([(0.0, 150.0), (0.06, 165.0), (dur, 92.0)], n)
    y = _voice(f0, rng, GRUNT_F, breath=0.45, rough=0.55, jitter=0.03, vib=(5.0, 0.01), drive=2.4)
    return y * dsp.env_bp([(0.0, 0.0), (0.015, 1.0), (0.12, 0.8), (dur, 0.0)], n)


def heavy_breath(dur, seed=0, rate=0.9):
    """A big man breathing slowly and heavily through his nose, close behind a door."""
    rng = dsp.rng_for("opp-heavy", seed)
    n = n_of(dur)
    out = np.zeros(n + n_of(2.0))
    t = 0.0
    while t < dur:
        cyc = 1.0 / rate * rng.uniform(0.92, 1.08)
        for k, (lo, hi, frac, g) in enumerate(((250.0, 1500.0, 0.42, 0.8), (180.0, 1100.0, 0.5, 1.0))):
            m = n_of(cyc * frac)
            x = dsp.bandpass(dsp.white(m, rng), lo, hi, 2)
            x = _rms_norm(x + 0.8 * dsp.biquad(x, "bandpass", 520.0 if k else 700.0, 3.0))
            x *= dsp.env_bp([(0.0, 0.0), (cyc * frac * 0.55, 1.0), (cyc * frac, 0.0)], m)
            dsp.mix_into(out, x * g, n_of(t + (0.0 if k == 0 else cyc * 0.45)))
        t += cyc
    return out[:n]


def _formant_48k(n48, rng, f0, syl_rate):
    n16 = n48 // 3 + 4
    x = sfx._formant_voice(n16, rng, sr=16000, f0=f0, syl_rate=syl_rate, words=True)
    return signal.resample_poly(x, 3, 1)[:n48]


def quarrel(dur, seed=0):
    """A man and a woman shouting at each other, escalating: turns get shorter, voices higher
    and louder, and by the end they talk over each other. Dry and full band; the mix puts it
    behind glass."""
    rng = dsp.rng_for("opp-quarrel", seed)
    n = n_of(dur)
    out = np.zeros(n + n_of(2.0))
    t = 0.0
    who = 0
    while t < dur:
        u = t / dur
        L = (1.3 - 0.75 * u) * rng.uniform(0.8, 1.15)
        m = n_of(L)
        if who == 0:
            x = _formant_48k(m, rng, 112.0 + 45.0 * u, 5.0 + 1.5 * u)
        else:
            x = _formant_48k(m, rng, 225.0 + 110.0 * u, 6.0 + 2.0 * u)
        x = np.tanh(2.0 * _rms_norm(x) * (0.35 + 0.25 * u))
        x *= dsp.env_bp([(0.0, 0.0), (0.04, 1.0), (L - 0.08, 1.0), (L, 0.0)], m)
        dsp.mix_into(out, x * (0.55 + 0.45 * u), n_of(t))
        overlap = 0.05 + 0.35 * u
        t += L * (1.0 - overlap) + rng.uniform(0.02, 0.12) * (1.0 - u)
        who = 1 - who
    return out[:n]


def through_glass(x, lp=1500.0, wet_db=-9.0, seed=0):
    """Across the street and behind a window: no top, a little room."""
    y = dsp.sos(dsp.sos(x, "lowpass", lp, 4), "highpass", 160.0, 2)
    return dsp.reverb(y, "small_room", wet_db=wet_db, seed=seed).mean(axis=1)
