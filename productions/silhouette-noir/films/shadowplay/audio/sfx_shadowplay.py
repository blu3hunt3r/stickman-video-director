"""SHADOW PLAY - this film's own sounds, built on audio.dsp and the shared audio.sfx catalog.

    render(name, dur=None, params=None, seed=0) -> float32 (n, 2) at 48 kHz

Names registered here take precedence; every other name falls through to audio.sfx (the
shared catalog: match_strike, bulb_hum, bulb_pop, footstep, radio_static, keys, car_away ...).
Level convention = audio.sfx: every sound renders at REF_LUFS (-16, about narration level) by
its loudest 400 ms (one-shots) or its integrated loudness (sustained), never above a true-peak
cap; parameter-dependent level (distance, size) is applied after the cap. A cue's gain_db
then places it in the mix.

Families
  light switches ... switch_click, lamp_switch, bulb_on, light_out, window_lights
  hands & paper .... binocular_lift, coat_flare, cloth_snap, cloth_rustle, cloth_slide,
                     sheet_rip, knife_whoosh, doll_flutter, rod_tap, pin_creak, lamp_set,
                     sheet_snap, doll_clamp, curtain_rings
  the trap ......... handle_turn, door_burst, door_slam, key_lock, door_hammer, lamp_crash
  outside & stairs . police_radio, siren_whoop, siren_wail, flashlight_click, wood_step,
                     stair_steps, steps_seq, umbrella_pass, radiator_tick, phonograph_waltz,
                     flame_flicker
  the shadow murder  string_stab, scream_pull, glint, breath
  Bass graphics .... paper_pop, paper_slide, paper_flip, grid_snap, heart_pulse, slash_whoosh,
                     iris_close, bars_wipe, tear_big

Every sound is layered (transient + body + tail), band-limited per source, seed-varied (a new
seed is a new take) and faded on every edge. ir(kind) gives this film's synthesized rooms
(her_room, apt9, stairwell, hallway, killer) for the mixer, the beds and the score.
"""
from __future__ import annotations

import functools
import math

import numpy as np

from audio import dsp
from audio import sfx as lib
from audio.dsp import (SR, TWO_PI, ar_env, bandpass, biquad, crackle, db2lin, exp_env, fade, friction,
                       mix_into, modal, n_of, onepole_lp, pan_mono, pink, saturate, saw, smooth_noise, sos,
                       t_axis, to_stereo, tv_bandpass, tv_lowpass, white)
from audio.sfx import _N, _burst, _click, _drop, _hit, _place, _sum, _thump, _wide

REF_LUFS = lib.REF_LUFS
PEAK_CAP_DBTP = lib.PEAK_CAP_DBTP
HIT_PEAK_CAP_DBTP = lib.HIT_PEAK_CAP_DBTP
SUSTAINED_PEAK_CAP_DBTP = lib.SUSTAINED_PEAK_CAP_DBTP
_REG: dict = {}
_CACHE: dict = {}


def _sfx(name, kind="oneshot", norm="max", default_dur=None, space=1.0, hit=False, trim=0.0):
    """Register a sound. space: factor for the mixer's reverb send (0 = carries its own
    acoustics). hit: designed hit (lightly ducked under the narration)."""
    def deco(fn):
        _REG[name] = dict(fn=fn, kind=kind, norm=norm, default_dur=default_dur, space=space, hit=hit,
                          trim=trim, name=name, own=True)
        return fn
    return deco


def names(own_only=True):
    return sorted(_REG) if own_only else sorted(set(_REG) | set(lib.names()))


def exists(name):
    return name in _REG or lib.exists(name)


def spec(name):
    return _REG[name] if name in _REG else lib.spec(name)


def _measure(x, mode):
    if mode == "int" and len(x) >= n_of(0.8):
        v = dsp.loudness_integrated(x)
        if np.isfinite(v):
            return v
    y = x if len(x) >= n_of(0.4) else dsp.pad_to(x, n_of(0.4))
    _, lk = dsp.loudness_curve(y, win=0.4, hop=0.05)
    return float(np.max(lk)) if len(lk) else -70.0


def render(name, dur=None, params=None, seed=0):
    """Render a sound as float32 (n, 2). dur: exact length for sustained sounds; for one-shots
    an optional maximum (truncated with a short fade). Unknown names go to audio.sfx."""
    if name not in _REG:
        return lib.render(name, dur=dur, params=params, seed=seed)
    sp = _REG[name]
    p = dict(params or {})
    key = (name, None if dur is None else round(float(dur), 4), tuple(sorted((k, str(v)) for k, v in p.items())),
           int(seed))
    if key in _CACHE:
        return _CACHE[key].copy()
    rng = np.random.default_rng(dsp.stable_seed("shadowplay", name, seed))
    d = dur if (dur is not None and sp["kind"] == "sustained") else sp["default_dur"]
    if sp["kind"] == "sustained":
        d = max(0.05, float(d if d is not None else 3.0))
    res = sp["fn"](d, p, rng)
    extra = 0.0
    if isinstance(res, tuple):
        res, extra = res
    x = to_stereo(np.asarray(res, dtype=np.float64))
    x = sos(x, "highpass", 18.0, 2)                    # DC / subsonic blocker
    if sp["kind"] == "sustained":
        x = dsp.pad_to(x, n_of(d))
    else:
        x = fade(x, 0.00015, 0.012, shape="lin")
    lvl = _measure(x, sp["norm"])
    if np.isfinite(lvl) and lvl > -120:
        x = x * db2lin(REF_LUFS + sp["trim"] - lvl)
    cap = (HIT_PEAK_CAP_DBTP if sp["hit"] else PEAK_CAP_DBTP) if sp["kind"] == "oneshot" else SUSTAINED_PEAK_CAP_DBTP
    tp = dsp.true_peak_db(x)
    if tp > cap:
        x = x * db2lin(cap - tp)
    x = x * db2lin(extra)
    if sp["kind"] == "oneshot":
        if dur is not None and dur > 0 and n_of(dur) < len(x):
            x = fade(x[:n_of(dur)], 0.0, min(0.03, dur / 3))
    else:
        x = fade(x, 0.0005, 0.003)
    out = x.astype(np.float32)
    if len(_CACHE) > 300:
        _CACHE.clear()
    _CACHE[key] = out
    return out.copy()


# ============================================================================ rooms
# This film's spaces, synthesized like dsp.make_ir (frequency-dependent decay, early reflections,
# flutter echoes between bare parallel walls). t60 mid (s), low / high decay multipliers,
# predelay, ER count / span / gain, brightness LP, flutter period (0 = none).
_ROOMS = {
    "her_room":  dict(t60=0.45, lo=1.1, hi=0.5, pre=0.002, er=10, er_span=0.022, er_g=0.5, lp=6500, flutter=0.0),
    "apt9":      dict(t60=0.95, lo=1.05, hi=0.72, pre=0.004, er=14, er_span=0.032, er_g=0.62, lp=8200, flutter=0.0118),
    "stairwell": dict(t60=2.4, lo=1.15, hi=0.5, pre=0.014, er=16, er_span=0.09, er_g=0.5, lp=5600, flutter=0.023),
    "hallway":   dict(t60=1.15, lo=1.05, hi=0.6, pre=0.006, er=12, er_span=0.045, er_g=0.55, lp=6800, flutter=0.0165),
    "killer":    dict(t60=0.55, lo=1.1, hi=0.45, pre=0.003, er=10, er_span=0.026, er_g=0.45, lp=5200, flutter=0.0),
}
ROOM_KINDS = tuple(_ROOMS) + dsp.IR_KINDS


@functools.lru_cache(maxsize=16)
def ir(kind, seed=0):
    """Stereo impulse response (unit energy per channel) for this film's rooms; any dsp kind
    (street, hall, plate, small_room ...) falls through to dsp.make_ir."""
    if kind not in _ROOMS:
        return dsp.make_ir(kind)
    sp = _ROOMS[kind]
    rng = np.random.default_rng(dsp.stable_seed("sp_ir", kind, seed))
    t60 = sp["t60"]
    length = min(6.0, t60 * 1.25 + sp["pre"] + 0.05)
    n = n_of(length)
    t = t_axis(n)
    out = np.zeros((n, 2))
    for ch in range(2):
        nz = rng.standard_normal(n)
        lo = sos(nz, "lowpass", 400.0, 2)
        hi = sos(nz, "highpass", 3200.0, 2)
        mid = nz - lo - hi
        tail = (lo * np.power(10.0, -3.0 * t / (t60 * sp["lo"])) + mid * np.power(10.0, -3.0 * t / t60)
                + hi * np.power(10.0, -3.0 * t / (t60 * sp["hi"])))
        tail *= 1.0 - np.exp(-t / max(0.004, 0.06 * t60))
        tail = onepole_lp(tail, sp["lp"])
        er = np.zeros(n)
        times = np.sort(rng.uniform(0.0015, sp["er_span"], sp["er"]))
        gains = sp["er_g"] * rng.uniform(0.4, 1.0, sp["er"]) * np.exp(-times / max(sp["er_span"], 1e-3))
        gains *= rng.choice([-1.0, 1.0], sp["er"])
        for tt, gg in zip(times, gains):
            i = n_of(tt)
            if i < n:
                er[i] += gg
        if sp["flutter"]:
            per = sp["flutter"] * (1.0 + 0.025 * (ch - 0.5))
            k = 1
            while k * per < t60 * 0.6:
                i = n_of(k * per)
                if i < n:
                    er[i] += 0.5 * sp["er_g"] * math.pow(10.0, -3.0 * k * per / (t60 * 0.55)) * (1 if k % 2 else -1)
                k += 1
        er = onepole_lp(er, sp["lp"] * 0.8)
        tail /= max(1e-12, np.sqrt(np.sum(tail ** 2)))
        e_er = np.sqrt(np.sum(er ** 2))
        if e_er > 0:
            er = er / e_er * 0.55
        c = np.concatenate([np.zeros(n_of(sp["pre"])), tail + er])[:n]
        ramp = n_of(0.002)
        c[:ramp] *= np.linspace(0, 1, ramp)
        c = fade(c, 0.0, min(0.25, length * 0.2))
        out[:, ch] = c / max(1e-12, np.sqrt(np.sum(c ** 2)))
    return out


def reverb(x, kind, wet_db=-12.0, dry=1.0):
    """Dry + convolution wet in one of this film's rooms (output keeps the tail)."""
    x = to_stereo(np.asarray(x, dtype=np.float64))
    wet = dsp.convolve(x.mean(axis=1), ir(kind)) * db2lin(wet_db)
    out = np.zeros((len(wet), 2))
    out[:len(x)] += x * dry
    out += wet
    return out


# ============================================================================ helpers
def _distance(x, d, rng):
    """Push a close sound across the street (d 0..1): the top end closes, a little low cut,
    the street's reverb grows and the direct sound falls. Returns (stereo, level_db)."""
    d = float(np.clip(d, 0.0, 1.0))
    x = np.asarray(x, dtype=np.float64)
    if d <= 0.01:
        return to_stereo(x), 0.0
    m = dsp.mono(x)
    y = sos(m, "lowpass", 9500.0 * (1 - d) + 2300.0 * d, 2)
    y = sos(y, "highpass", 50.0 + 150.0 * d, 2)
    wet = dsp.convolve(y, dsp.make_ir("street")) * (0.1 + 0.32 * d)
    out = np.zeros((len(wet), 2))
    out[:len(y)] += to_stereo(y) * (1.0 - 0.45 * d)
    out += wet
    return out, -15.0 * d


def _pan_sweep(x, pan0, pan1, shape=None):
    """Mono -> stereo, equal-power pan moving pan0 -> pan1 over the sound (or along `shape`)."""
    x = np.asarray(x, dtype=np.float64)
    u = np.linspace(0.0, 1.0, len(x)) if shape is None else shape
    pan = np.clip(pan0 + (pan1 - pan0) * u, -1, 1)
    th = (pan + 1.0) * np.pi / 4.0
    return np.stack([x * np.cos(th), x * np.sin(th)], axis=1)


def _imp_train(rate, n, rng, spread=0.6, polarity=True):
    """Impulses at a time-varying rate (per-sample array), log-normal amplitudes."""
    ph = np.cumsum(np.asarray(rate, dtype=np.float64)) / SR
    idx = np.nonzero(np.diff(np.floor(ph), prepend=0.0) > 0)[0]
    out = np.zeros(n)
    a = np.exp(rng.normal(0.0, spread, len(idx)))
    if polarity:
        a *= rng.choice([-1.0, 1.0], len(idx))
    out[idx] = a
    return out


def _bell(t, center, rise, fall):
    """Asymmetric bell envelope (gaussian sides) peaking at `center`."""
    w = np.where(t < center, rise, fall)
    return np.exp(-0.5 * ((t - center) / np.maximum(w, 1e-4)) ** 2)


def _flutter(n, rate, rng, depth=0.6):
    """Cloth / card flap modulation: a rectified oscillator at `rate` Hz (array ok), smoothed."""
    ph = np.cumsum(np.broadcast_to(np.asarray(rate, dtype=np.float64), (n,))) / SR
    sq = 0.5 + 0.5 * np.sign(np.sin(TWO_PI * ph + rng.uniform(0, TWO_PI)))
    return (1.0 - depth) + depth * onepole_lp(sq, 70.0)


def _hz(midi):
    return 440.0 * 2.0 ** ((np.asarray(midi, dtype=np.float64) - 69.0) / 12.0)


# ============================================================================ light switches
def _switch(rng, off=False):
    """A 1950s bakelite toggle: lever travel, the snap (contacts + spring), the plate's thock,
    a second settle tick."""
    k = 0.9 if off else 1.0
    n = _N(0.3)
    out = np.zeros(n)
    m = _N(0.008)
    trav = friction(m, 900, rng, jitter=0.3, body=[(3800, 6, 1.0)]) * np.hanning(m)
    _place(out, trav, 0.0, 0.25)
    ts = 0.006 + rng.uniform(0, 0.003)
    _place(out, _hit(rng, np.array([2650, 4100, 6300, 8900]) * k, [0.012, 0.01, 0.008, 0.006], spread=0.03, click=1.0), ts, 1.0)
    _place(out, _hit(rng, np.array([520, 1180, 1900]) * k, [0.03, 0.02, 0.015], click=0.0), ts, 0.6 if off else 0.5)
    _place(out, _thump(_N(0.05), 260 * k, 180 * k, 0.005, 0.02), ts, 0.35)
    _place(out, modal([4480.0 * k], [0.06], [1.0], _N(0.1)), ts + 0.001, 0.05)
    _place(out, _hit(rng, np.array([3100, 5200]) * k, [0.006, 0.005], click=0.8, n=_N(0.02)), ts + rng.uniform(0.012, 0.02), 0.28)
    return out


@_sfx("switch_click", space=0.6)
def _switch_click(dur, p, rng):
    """Wall light switch (bakelite toggle). off 0/1 (a shade lower, more thock). dist 0..1:
    0 close, 1 heard from across the street (S08: her light going off)."""
    out = _switch(rng, bool(p.get("off", 0)))
    return _distance(out, float(p.get("dist", 0.0)), rng)


@_sfx("lamp_switch", space=0.6)
def _lamp_switch(dur, p, rng):
    """The show lamp's brass socket switch: fingers on the knob, two detents ratcheting, then the
    spring-loaded snap with the brass shell ringing, a tick of the cord against the stand."""
    n = _N(0.5)
    out = np.zeros(n)
    m = _N(0.05)
    _place(out, bandpass(white(m, rng), 1500, 6000, 2) * np.hanning(m), 0.0, 0.05)
    for k in range(2):
        _place(out, _hit(rng, [3300, 5600], [0.004, 0.003], click=0.7, n=_N(0.012)), 0.03 + 0.022 * k, 0.22 + 0.08 * k)
    ts = 0.085 + rng.uniform(0, 0.01)
    _place(out, _hit(rng, [2900, 4650, 7200, 9800], [0.05, 0.04, 0.03, 0.02], spread=0.02, click=1.0), ts, 1.0)
    _place(out, _thump(_N(0.06), 340, 220, 0.006, 0.025), ts, 0.35)
    _place(out, modal([2920.0, 6100.0], [0.25, 0.12], [1.0, 0.4], _N(0.3), phases=rng.uniform(0, 6, 2)), ts + 0.001, 0.05)
    _place(out, _hit(rng, [1700, 2600], [0.02, 0.015], click=0.3, n=_N(0.04)), ts + 0.03 + rng.uniform(0, 0.02), 0.12)
    return out


@_sfx("bulb_on", space=0.6)
def _bulb_on(dur, p, rng):
    """A bare bulb flickering on: contact tick, three stuttering 120 Hz buzz bursts with crackles
    at their edges, the filament 'ping' (a thin metallic ring gliding up a hair as the coil
    heats), the first breath of the hum. dist 0..1 pushes it across the street."""
    n = _N(1.45)
    t = t_axis(n)
    out = np.zeros(n)
    _place(out, _click(rng, 2500, 0.0015, _N(0.006)), 0.0, 0.6)
    gate = np.zeros(n)
    for a, L, lv in ((0.0, 0.022, 0.55), (0.05 + rng.uniform(0, 0.01), 0.03, 0.75), (0.105, 0.016, 0.5), (0.15, 9.0, 1.0)):
        gate[n_of(a):min(n, n_of(a + L))] = lv
    gate = onepole_lp(gate, 350)
    buzz = sos(saturate(np.sin(TWO_PI * 120 * t), 4.0, asym=0.2), "bandpass", (120, 4500), 2)
    hum = np.sin(TWO_PI * 120 * t) + 0.45 * np.sin(TWO_PI * 240 * t + 1.0) + 0.2 * np.sin(TWO_PI * 360 * t + 2.0)
    decay = np.exp(-np.maximum(t - 0.15, 0) / 0.12)
    out += 0.5 * buzz * gate * (0.04 + 0.96 * decay) + 0.12 * hum * gate * (0.12 + 0.88 * decay)
    edges = np.abs(np.diff(gate, prepend=0.0)) > 0.004
    out += 0.5 * sos(crackle(n, 160, rng) * edges, "highpass", 1500, 2)
    m = _N(1.25)
    tm = t_axis(m)
    glide = 1.0 + 0.006 * (1.0 - np.exp(-tm / 0.12))
    ping = np.zeros(m)
    for f, a, t60 in ((6120, 1.0, 0.75), (8890, 0.5, 0.45), (11730, 0.22, 0.3), (3410, 0.16, 0.5)):
        ff = f * rng.uniform(0.98, 1.02)
        ping += a * np.sin(TWO_PI * np.cumsum(ff * glide) / SR + rng.uniform(0, TWO_PI)) * np.power(10.0, -3 * tm / t60)
    ping[:_N(0.002)] *= np.linspace(0, 1, _N(0.002))
    _place(out, ping, 0.152, 0.2)
    out = fade(out, 0.0, 0.3)
    return _distance(out, float(p.get("dist", 0.0)), rng)


@_sfx("light_out", space=0.6)
def _light_out(dur, p, rng):
    """The light snapping OUT: the switch (off), the hum's last grain cut dead, and the cooling
    filament's tiny 'tink' a beat later. dist 0..1."""
    n = _N(0.7)
    t = t_axis(n)
    out = np.zeros(n)
    _place(out, _switch(rng, True), 0.0, 1.0)
    m = _N(0.03)
    hum = sos(saturate(np.sin(TWO_PI * 120 * t_axis(m)), 3.0), "bandpass", (120, 3000), 2) * np.linspace(1, 0, m) ** 2
    _place(out, hum, 0.0, 0.12)
    _place(out, modal([7400.0, 10300.0], [0.12, 0.08], [1.0, 0.5], _N(0.15), phases=rng.uniform(0, 6, 2)), 0.09 + rng.uniform(0, 0.03), 0.05)
    _place(out, _hit(rng, [5200, 7600], [0.01, 0.008], click=0.2, n=_N(0.03)), 0.33 + rng.uniform(0, 0.08), 0.04)
    del t
    return _distance(out, float(p.get("dist", 0.0)), rng)


@_sfx("window_lights", space=0.0)
def _window_lights(dur, p, rng):
    """Far windows switching on (or off) in a stagger across the facade: n tiny distant clicks
    over span seconds, scattered in the stereo field, with the street's air on them.
    times/pans (optional, sequences): the exact switch-on offsets (s) and pans of each window,
    each then with the filament's flicker (a dip and a catch, 40 / 100 ms later)."""
    off = bool(p.get("off", 0))
    if p.get("times") is not None:
        times = np.array([float(v) for v in p["times"]])
        times -= times.min()
        pans = [float(v) for v in p.get("pans", [0.0] * len(times))]
        span = float(times.max())
    else:
        cnt = int(p.get("n", 9))
        span = float(p.get("span", 0.8))
        times = np.linspace(0, span, cnt) + rng.uniform(-0.25, 0.25, cnt) * span / max(cnt, 1)
        times = np.clip(np.sort(times), 0, span)
        pans = None
    n = _N(span + 0.4)
    dry = np.zeros((n, 2))
    k = 0.9 if off else 1.0
    for j, tt in enumerate(times):
        c = _sum(_hit(rng, np.array([2300, 3900, 6100]) * k * rng.uniform(0.9, 1.1), [0.012, 0.009, 0.006], click=0.8, n=_N(0.04)),
                 0.4 * _thump(_N(0.04), 520, 360, 0.004, 0.015))
        c = sos(c, "lowpass", 3800, 2)
        pan = rng.uniform(-0.75, 0.75) if pans is None else pans[j]
        mix_into(dry, pan_mono(c, pan), n_of(tt), rng.uniform(0.45, 1.0) if pans is None else rng.uniform(0.7, 1.0))
        if pans is not None and not off:
            for dt, gk in ((0.04, 0.16), (0.1, 0.28)):
                fl = sos(_hit(rng, np.array([3100, 5200]) * rng.uniform(0.9, 1.1), [0.004, 0.003], click=0.5, n=_N(0.012)), "lowpass", 4200, 2)
                mix_into(dry, pan_mono(fl, pan), n_of(tt + dt), gk)
    wet = dsp.convolve(dry.mean(axis=1), dsp.make_ir("street"))[:n] * 0.6
    return dry + wet


# ============================================================================ hands & cloth
@_sfx("binocular_lift", space=0.6)
def _binocular_lift(dur, p, rng):
    """Her 7x50 binoculars lifted to the eyes: hands on the rubber armour, sleeve rustle, the
    leather strap creaking, eyecups meeting the brow, the knurled focus wheel ticking.
    lower=1: the reverse (rub, strap swings back, a buckle tick, the hands settle). length s:
    the motion (the brow contact lands at 0.95 length)."""
    lower = bool(p.get("lower", 0))
    L = float(p.get("length", 0.6))                 # the eyecups meet the brow at 0.95 L
    n = _N(L + 0.45)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    mot = np.sin(np.pi * u) ** 1.2 * (t < L)
    rub = bandpass(white(n, rng), 700, 3800, 2) * (0.5 + 0.5 * smooth_noise(n, 18, rng)) * mot * 0.3
    sleeve = bandpass(crackle(n, 500, rng), 900, 5000, 2) * mot * 0.7
    strap = friction(n, 35 + 50 * mot, rng, jitter=0.3, body=[(520, 4, 1.0), (1250, 6, 0.5), (2600, 8, 0.2)]) * mot * 1.4
    out = rub + sleeve + strap
    if not lower:
        _place(out, _sum(_thump(_N(0.08), 260, 170, 0.006, 0.03), _burst(_N(0.04), rng, 200, 1500, t60=0.015, attack=0.001)), L * 0.95, 0.8)
        for k in range(4):
            _place(out, _hit(rng, [3900, 6200], [0.006, 0.004], click=0.6, n=_N(0.015)), L + 0.12 + 0.045 * k + rng.uniform(0, 0.01), 0.16)
    else:
        _place(out, _hit(rng, [2900, 4400], [0.03, 0.02], click=0.4, n=_N(0.06)), L * 0.9, 0.22)
        _place(out, _burst(_N(0.06), rng, 150, 1200, t60=0.03, attack=0.003), L, 0.5)
    return _wide(out, rng, 0.25)


@_sfx("coat_flare", space=0.8)
def _coat_flare(dur, p, rng):
    """Her heavy wool trench coat pulled off its hook and swung on: the collar loop scraping off
    the cast-iron hook, a big cloth whoosh whose flutter quickens as it flares at the top of the
    swing (with a low flap), the coat dropping on her shoulders, arms into the sleeves, a buckle
    clink. Times from the start (s): flare (the flap, default 0.42), land (on the shoulders,
    1.02), sleeves (start, 0.64) + sleeve_len (0.36); hook 0/1 (the scrape off the hook at 0)."""
    fl = float(p.get("flare", 0.42))
    land = float(p.get("land", 1.02))
    s0, sl = float(p.get("sleeves", 0.64)), float(p.get("sleeve_len", 0.36))
    n = _N(max(land, s0 + sl) + 0.55)
    t = t_axis(n)
    out = np.zeros(n)
    if p.get("hook", 1):
        m = _N(0.09)
        hk = friction(m, 260, rng, jitter=0.3, body=[(1900, 10, 1.0), (3300, 14, 0.5)]) * np.hanning(m)
        _place(out, hk, 0.0, 0.6)
        _place(out, _hit(rng, [1650, 2900], [0.05, 0.03], click=0.5, n=_N(0.08)), 0.085, 0.25)
    e = _bell(t, fl, 0.14 * fl / 0.42 + 0.02, 0.12)
    flut = _flutter(n, 8 + 10 * e, rng, 0.5)
    cloth = bandpass(white(n, rng), 160, 2400, 2) * flut
    air = sos(pink(n, rng), "lowpass", 480, 2)
    out += (cloth * 0.75 + air * 1.0) * e
    _place(out, _burst(_N(0.09), rng, 110, 1600, t60=0.045, attack=0.0015), fl + 0.03, 0.9)
    _place(out, _thump(_N(0.15), 120, 70, 0.01, 0.06), fl + 0.03, 0.45)
    m = _N(sl)
    w = np.sin(np.pi * np.linspace(0, 1, m)) ** 1.3
    slv = bandpass(crackle(m, 700, rng), 700, 4500, 2) * w * 0.9 + bandpass(pink(m, rng), 250, 1400, 2) * 0.2 * w
    _place(out, slv, s0, 1.0)
    _place(out, _burst(_N(0.07), rng, 120, 1100, t60=0.03, attack=0.003), land, 0.55)
    _place(out, _hit(rng, [3100, 4700, 6900], [0.06, 0.05, 0.03], click=0.5, n=_N(0.1)), land + 0.03, 0.12)
    u = np.clip(t / max(land + 0.08, 0.2), 0, 1)
    return _pan_sweep(out, -0.45, 0.35, u)


@_sfx("cloth_snap", space=0.8)
def _cloth_snap(dur, p, rng):
    """A collar flipped up / a flap of heavy cloth: a short flutter into a snap."""
    n = _N(0.4)
    t = t_axis(n)
    e = _bell(t, 0.09, 0.05, 0.03)
    x = bandpass(white(n, rng), 200, 2600, 2) * _flutter(n, 16, rng, 0.5) * e * 0.6
    _place(x, _burst(_N(0.05), rng, 160, 2200, t60=0.02, attack=0.0008), 0.1, 1.0)
    _place(x, _thump(_N(0.08), 160, 100, 0.006, 0.03), 0.1, 0.3)
    return x


@_sfx("cloth_rustle", space=0.8)
def _cloth_rustle(dur, p, rng):
    """Her coat against the wall as she flattens herself behind the door: a soft wool rustle
    with a little shoulder scrape. length s."""
    L = float(p.get("length", 0.8))
    n = _N(L + 0.1)
    t = t_axis(n)
    mot = np.clip(0.6 + 0.45 * smooth_noise(n, 4.0, rng), 0.2, None) * np.sin(np.pi * np.clip(t / L, 0, 1)) ** 0.8
    x = bandpass(crackle(n, 650, rng, amp_spread=1.0), 600, 4500, 2) * 1.2 + bandpass(pink(n, rng), 200, 1600, 2) * 0.3
    sc = friction(n, 40 + 30 * mot, rng, jitter=0.4, body=[(380, 3, 1.0), (900, 4, 0.5)]) * 0.6
    return _wide((x + sc) * mot, rng, 0.3)


@_sfx("cloth_slide", space=0.8)
def _cloth_slide(dur, p, rng):
    """Her back sliding down the wooden door to the floor: wool on painted wood (a slow stick-slip
    rumble with the door panel answering), a rough rustle, then she sits: a soft body thump."""
    L = float(p.get("length", 1.3))
    n = _N(L + 0.5)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    mot = np.sin(np.pi * u) ** 0.6 * (t < L)
    fr = friction(n, 30 + 55 * mot, rng, jitter=0.45, body=[(180, 3, 1.0), (420, 4, 0.7), (900, 5, 0.4)]) * 1.4
    rus = bandpass(crackle(n, 500, rng), 500, 4000, 2) * 0.8 + bandpass(pink(n, rng), 150, 1200, 2) * 0.35
    out = (fr + rus) * mot
    _place(out, _sum(_thump(_N(0.3), 95, 52, 0.02, 0.12), _burst(_N(0.08), rng, 70, 900, t60=0.04, attack=0.004)), L, 0.9)
    _place(out, _burst(_N(0.15), rng, 300, 2500, t60=0.08, attack=0.01), L + 0.02, 0.3)
    return out


@_sfx("breath", space=0.6)
def _breath(dur, p, rng):
    """A held breath let go: a shaky exhale (aspiration through an open vowel: noise through four
    formants, a 6-8 Hz tremor), very soft. kind 'out' or 'in' (a sharp, frightened intake)."""
    kind = p.get("kind", "out")
    L = float(p.get("length", 1.1 if kind == "out" else 0.45))
    n = _N(L + 0.1)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    src = white(n, rng)
    F = [(680, 6, 1.0), (1180, 8, 0.6), (2550, 10, 0.32), (3450, 12, 0.18)] if kind == "out" else \
        [(420, 5, 0.8), (1900, 9, 0.7), (2700, 11, 0.4), (3600, 12, 0.25)]
    v = dsp.resonator_bank(src, [f for f, _, _ in F], [q for _, q, _ in F], [g for *_, g in F])
    v += 0.22 * bandpass(src, 1500, 6500, 2)
    if kind == "out":
        env = np.clip(u / 0.12, 0, 1) ** 0.7 * (1 - u) ** 1.4
        trem = 1 + 0.42 * np.sin(TWO_PI * np.cumsum(6.5 + 1.5 * smooth_noise(n, 2, rng)) / SR) * np.clip(u / 0.2, 0, 1)
    else:
        env = (u ** 1.6) * (t < L)
        trem = 1 + 0.25 * np.sin(TWO_PI * np.cumsum(9.0 + 2 * smooth_noise(n, 3, rng)) / SR)
    out = sos(v * env * trem, "lowpass", 6500, 2)
    return fade(out, 0.01, 0.03)


@_sfx("sheet_rip", space=0.9)
def _sheet_rip(dur, p, rng):
    """The knife through the taut sheet: the punch (blade through stretched cotton - a 'thup' with
    the sheet's membrane boom and a fibre crack), then the rip: a coarse, buzzy run of breaking
    threads (lower and rougher than paper: 300 Hz-3 kHz grain with a 120-200 Hz zip), slowing as
    the blade drags down; the torn flap flutters. size 0..1 (rip length 0.2-0.6 s, or length);
    punch=0: the rip alone (the blade already through, dragged down)."""
    s = float(np.clip(p.get("size", 0.6), 0, 1))
    L = float(p.get("length", 0.2 + 0.4 * s))
    n = _N(L + 0.55)
    out = np.zeros(n)
    if p.get("punch", 1):
        _place(out, _burst(_N(0.05), rng, 180, 1400, t60=0.022, attack=0.0005), 0.0, 1.0)
        memb = modal(np.array([92, 148, 211, 302]) * rng.uniform(0.95, 1.05), [0.09, 0.07, 0.05, 0.04], [1.0, 0.7, 0.5, 0.3],
                     _N(0.15), phases=rng.uniform(0, 6, 4))
        _place(out, memb, 0.0, 0.7)
        _place(out, _click(rng, 2200, 0.002, _N(0.008)), 0.0015, 0.6)
    m = _N(L)
    tr = t_axis(m)
    u = tr / L
    rate = 2600 * (1 - 0.55 * u) * (0.8 + 0.4 * np.abs(smooth_noise(m, 25, rng)))
    grain = bandpass(_imp_train(rate, m, rng, 0.6), 300, 3200, 2)
    fz = 170 * (1 - 0.3 * u) * (1 + 0.08 * smooth_noise(m, 30, rng))
    zip_ = bandpass(_imp_train(fz, m, rng, 0.35, polarity=False), 250, 2000, 2) * 2.2
    body = bandpass(white(m, rng), 200, 900, 2) * 0.35
    env = np.clip(tr / 0.01, 0, 1) * (1 - 0.35 * u) * np.where(u > 0.85, (1 - u) / 0.15, 1.0)
    _place(out, (grain * 1.4 + zip_ + body) * env, 0.012, 1.0)
    k = _N(0.4)
    tk = t_axis(k)
    fl = bandpass(white(k, rng), 200, 1800, 2) * _flutter(k, 13, rng, 0.6) * np.exp(-tk / 0.12)
    _place(out, fl, L + 0.02, 0.22)
    return out, 3.0 * (s - 0.5)


@_sfx("knife_whoosh", space=0.3)
def _knife_whoosh(dur, p, rng):
    """A knife swung hard: a short, sharp blade swish rising 1.4 -> 6 kHz with a body of air."""
    n = _N(0.32)
    t = t_axis(n)
    L = 0.16
    u = np.clip(t / L, 0, 1)
    x = tv_bandpass(white(n, rng), 1400 * 4.5 ** u, q=1.6, block=32)
    x += 0.5 * tv_bandpass(pink(n, rng), 400 + 900 * u, q=0.8, block=32)
    env = np.where(u < 0.8, (u / 0.8) ** 2.3, np.exp(-(t - 0.8 * L) / 0.03))
    return _pan_sweep(x * env, -0.3, 0.3)


@_sfx("doll_flutter", space=0.8)
def _doll_flutter(dur, p, rng):
    """A paper doll on its rod knocked about: stiff card flapping (slower and lower than paper:
    a 'tok' in each flap) and the thin wooden rod tapping. length s."""
    L = float(p.get("length", 0.7))
    n = _N(L + 0.25)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    env = np.sin(np.pi * u) ** 1.2 * (t < L)
    flaps = _imp_train(np.full(n, 11.0) * (1 + 0.25 * smooth_noise(n, 3, rng)), n, rng, 0.4, polarity=False)
    flap = dsp.resonator_bank(flaps, [650, 1250, 2300, 3600], [3, 4, 5, 6], [1.0, 0.8, 0.5, 0.3]) * 3.0
    grain = bandpass(crackle(n, 900, rng), 1200, 6000, 2) * 0.6
    card = bandpass(white(n, rng), 500, 3500, 2) * _flutter(n, 11, rng, 0.7) * 0.25
    out = (flap + grain + card) * env
    for tt in (0.04 + rng.uniform(0, 0.03), 0.2 + rng.uniform(0, 0.1), L * 0.8):
        _place(out, _hit(rng, np.array([1100, 2300, 3700]) * rng.uniform(0.9, 1.1), [0.04, 0.03, 0.02], click=0.7, n=_N(0.06)), tt, rng.uniform(0.35, 0.6))
    return _wide(out, rng, 0.3)


@_sfx("rod_tap", space=0.8)
def _rod_tap(dur, p, rng):
    """The puppet rods knocking: two or three dry taps of thin wooden dowels."""
    n = _N(0.45)
    out = np.zeros(n)
    tt = 0.0
    for k in range(int(rng.integers(2, 4))):
        f = rng.uniform(0.85, 1.15)
        _place(out, _hit(rng, np.array([980, 2100, 3500, 5200]) * f, [0.05, 0.035, 0.025, 0.015], spread=0.03, click=0.9, n=_N(0.08)), tt, 1.0 - 0.25 * k)
        tt += rng.uniform(0.07, 0.15)
    return out


@_sfx("pin_creak", space=0.6, hit=True)
def _pin_creak(dur, p, rng):
    """The puppet's pin joint turning: a brass split pin twisting in card - a thin, high
    stick-slip squeak that rises as it turns (metal resonances 2.4 / 3.9 / 6.1 kHz), the card
    flexing underneath (low creak), and the pin seating with a tiny tick. Close and exposed.
    length s."""
    L = float(p.get("length", 0.8))
    n = _N(L + 0.25)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    sw = np.sin(np.pi * u) ** 0.7 * (t < L)
    sq = friction(n, 220 + 380 * u ** 1.3, rng, jitter=0.1,
                  body=[(2450 * rng.uniform(0.95, 1.05), 22, 1.0), (3900, 26, 0.6), (6100, 30, 0.3), (1200, 8, 0.3)])
    flex = friction(n, 60 + 80 * sw, rng, jitter=0.35, body=[(650, 4, 1.0), (1400, 6, 0.5)])
    out = (sq * 0.9 + flex * 0.5) * sw
    _place(out, _hit(rng, [5200, 7900], [0.02, 0.015], click=0.3, n=_N(0.04)), L * 0.98, 0.12)
    return out


@_sfx("lamp_set", space=0.8)
def _lamp_set(dur, p, rng):
    """She lifts the show lamp and sets it behind the sheet: the cord dragging, the tripod's three
    steel feet landing on the boards (metal taps + wood knock), the bulb's filament rattling."""
    n = _N(0.9)
    out = np.zeros(n)
    m = _N(0.3)
    _place(out, friction(m, 70, rng, jitter=0.5, body=[(800, 3, 1.0), (1800, 4, 0.4)]) * np.hanning(m), 0.0, 0.4)
    t0 = 0.3
    for k in range(3):
        tt = t0 + 0.028 * k + rng.uniform(0, 0.01)
        _place(out, _hit(rng, np.array([900, 2100, 3600, 5100]) * rng.uniform(0.95, 1.05), [0.08, 0.06, 0.04, 0.03], click=0.8, n=_N(0.15)), tt, 0.6)
        _place(out, _thump(_N(0.1), 190, 120, 0.008, 0.04), tt, 0.4)
    for k in range(4):
        _place(out, _hit(rng, [rng.uniform(5000, 8000)], [0.01], click=0.3, n=_N(0.02)), t0 + 0.04 + rng.uniform(0, 0.08), 0.1)
    return out


@_sfx("sheet_snap", space=0.8)
def _sheet_snap(dur, p, rng):
    """She pulls the sheet straight: cloth swept tight (a quickening flutter), the snap as it goes
    taut, the clothes-pins clicking on the wire, and the wire itself answering with a low twang."""
    n = _N(1.0)
    t = t_axis(n)
    e = _bell(t, 0.24, 0.1, 0.05)
    x = bandpass(white(n, rng), 180, 2600, 2) * _flutter(n, 10 + 18 * e, rng, 0.55) * e * 0.7
    x += sos(pink(n, rng), "lowpass", 600, 2) * e * 0.5
    _place(x, _burst(_N(0.06), rng, 150, 2500, t60=0.03, attack=0.0008), 0.27, 1.0)
    _place(x, _thump(_N(0.1), 150, 90, 0.008, 0.04), 0.27, 0.35)
    for tt in (0.29, 0.33 + rng.uniform(0, 0.03)):
        _place(x, _hit(rng, np.array([1900, 3300, 4800]) * rng.uniform(0.9, 1.1), [0.03, 0.02, 0.015], click=0.8, n=_N(0.05)), tt, 0.3)
    m = _N(0.7)
    tw = dsp.karplus_strong(108.0 * rng.uniform(0.95, 1.05), 0.7, t60=0.6, brightness=0.3, rng=rng)
    tw = sos(tw[:m], "bandpass", (90, 1800), 2)
    _place(x, tw / (np.max(np.abs(tw)) + 1e-9), 0.28, 0.15)
    return _wide(x, rng, 0.25)


@_sfx("doll_clamp", space=0.8)
def _doll_clamp(dur, p, rng):
    """The woman doll clamped on its rod in front of the lamp: a wooden spring clamp squeaks open
    and snaps shut, the rod taps the table, the card shivers."""
    n = _N(0.8)
    out = np.zeros(n)
    m = _N(0.07)
    _place(out, friction(m, 500, rng, jitter=0.15, body=[(2300, 12, 1.0)]) * np.hanning(m), 0.0, 0.3)
    _place(out, _hit(rng, np.array([1500, 2700, 4100]) * rng.uniform(0.95, 1.05), [0.035, 0.025, 0.018], click=1.0, n=_N(0.07)), 0.09, 1.0)
    _place(out, _hit(rng, [1050, 2250, 3600], [0.05, 0.035, 0.025], click=0.8, n=_N(0.08)), 0.16 + rng.uniform(0, 0.03), 0.45)
    m = _N(0.35)
    tm = t_axis(m)
    sh = bandpass(white(m, rng), 600, 4000, 2) * _flutter(m, 17, rng, 0.7) * np.exp(-tm / 0.1)
    _place(out, sh, 0.12, 0.25)
    return out


@_sfx("curtain_rings", space=0.8)
def _curtain_rings(dur, p, rng):
    """The curtain drawn along its rod: a row of brass rings scraping and chattering along the
    metal pole (bunching with little clinks at the end) over the swish of heavy fabric.
    part=1: her fingers parting it a crack (two rings, a whisper of cloth). length s; pan0 ->
    pan1 the direction it is drawn."""
    part = bool(p.get("part", 0))
    L = float(p.get("length", 0.35 if part else 0.95))
    n = _N(L + 0.35)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    out = np.zeros(n)
    nr = 2 if part else int(rng.integers(8, 12))
    for k in range(nr):
        t0 = (k / max(nr, 1)) * L * 0.55 + rng.uniform(0, 0.04)
        m = _N(L * rng.uniform(0.35, 0.6))
        tm = t_axis(m)
        sc = friction(m, rng.uniform(600, 1200) * (1 + 0.3 * np.sin(np.pi * tm / (m / SR))), rng, jitter=0.25,
                      body=[(2900 * rng.uniform(0.9, 1.1), 14, 1.0), (4300, 18, 0.5), (6100, 20, 0.25)])
        sc *= np.sin(np.pi * tm / (m / SR)) ** 1.5
        _place(out, sc, t0, rng.uniform(0.15, 0.3))
    for k in range(2 if part else int(rng.integers(5, 9))):
        tt = (L * rng.uniform(0.75, 1.0)) if not part else rng.uniform(0.05, L)
        f = rng.uniform(3500, 6800)
        _place(out, _hit(rng, [f, f * 1.43, f * 2.07], [0.05, 0.035, 0.02], click=0.5, n=_N(0.08)), tt, rng.uniform(0.2, 0.45))
    sw = tv_bandpass(pink(n, rng), 500 + 1700 * np.sin(np.pi * u), q=0.7, block=64)
    sw *= np.sin(np.pi * u) ** 1.2 * (t < L) * (0.22 if part else 0.5)
    out += sw
    return _pan_sweep(out, float(p.get("pan0", -0.3 if part else -0.5)), float(p.get("pan1", 0.0 if part else 0.4)))


# ============================================================================ the trap
@_sfx("handle_turn", space=0.8)
def _handle_turn(dur, p, rng):
    """A brass door knob turned slowly from the other side: dry metal friction in the rose, the
    spindle's intermittent squeak, the latch spring compressing (a creak rising with the
    tension), spindle-play clicks, and the latch bolt clearing the strike plate (clack).
    length s (the clack lands at `length`)."""
    L = float(p.get("length", 1.2))
    n = _N(L + 0.45)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    out = np.zeros(n)
    turning = onepole_lp((t < L).astype(float), 30)
    _place(out, _hit(rng, [2800, 4300], [0.02, 0.015], click=0.6, n=_N(0.04)), 0.0, 0.3)
    rate = 45 + 60 * u + 25 * np.abs(smooth_noise(n, 3, rng))
    fr = friction(n, rate, rng, jitter=0.35, body=[(1850, 9, 1.0), (3050, 12, 0.6), (4700, 14, 0.3), (720, 4, 0.4)])
    out += fr * turning * 1.8
    gate = np.clip(smooth_noise(n, 2.5, rng) * 2.0, 0, 1) * turning
    sq = friction(n, 380 + 180 * u, rng, jitter=0.08, body=[(2650, 28, 1.0), (5300, 30, 0.3)])
    out += sq * gate * 0.6
    sp = friction(n, 70 + 220 * u ** 1.4, rng, jitter=0.2, body=[(950, 7, 1.0), (1750, 9, 0.6)])
    out += sp * u ** 1.5 * turning * 1.1
    for k in range(int(rng.integers(3, 6))):
        _place(out, _hit(rng, [rng.uniform(2200, 4200), rng.uniform(4500, 7000)], [0.008, 0.006], click=0.8, n=_N(0.02)),
               rng.uniform(0.1, L * 0.9), rng.uniform(0.15, 0.35))
    _place(out, _hit(rng, [1350, 2550, 3800, 5200], [0.05, 0.04, 0.03, 0.02], spread=0.02, click=0.6), L, 0.5)
    _place(out, _thump(_N(0.08), 260, 170, 0.006, 0.03), L, 0.3)
    return out


def _door_panel(rng, n, scale=1.0):
    """A solid wooden door's body: low panel modes (a boom), a few mids."""
    f = np.array([86, 139, 224, 351, 537, 820]) * rng.uniform(0.96, 1.04) * scale
    return modal(f, np.array([0.3, 0.24, 0.17, 0.12, 0.08, 0.05]), np.array([1.0, 0.8, 0.6, 0.4, 0.25, 0.15]), n,
                 phases=rng.uniform(0, TWO_PI, len(f)))


@_sfx("door_burst", space=0.5, hit=True, trim=1.5)
def _door_burst(dur, p, rng):
    """The door flung open: the latch tongue ripping out of the strike (wood splinter crack +
    metal clank), a slab of air, the hinge shrieking, the door slamming back into the wall (or
    her) with a deep panel boom, then everything on it rattling. ti: s from the crack to the
    boom (the leaf hitting its stop)."""
    n = _N(1.9)
    out = np.zeros((n, 2))
    cr = _sum(sos(crackle(_N(0.12), 700, rng, amp_spread=1.0), "bandpass", (800, 6500), 2) * exp_env(_N(0.12), 0.08) * 2.5,
              _hit(rng, [900, 1700, 2600, 3900], [0.1, 0.08, 0.06, 0.04], spread=0.03, click=1.0),
              _burst(_N(0.06), rng, 150, 4000, t60=0.03, attack=0.0003))
    mix_into(out, pan_mono(cr, -0.15), 0, 1.0)
    m = _N(0.3)
    tm = t_axis(m)
    air = sos(pink(m, rng), "lowpass", 650, 2) * np.sin(np.pi * np.clip(tm / 0.24, 0, 1)) ** 1.5
    mix_into(out, _pan_sweep(air, -0.4, 0.5), n_of(0.01), 0.8)
    m = _N(0.2)
    tm = t_axis(m)
    hs = friction(m, 900 - 500 * tm / 0.2, rng, jitter=0.08, body=[(2200, 20, 1.0), (3400, 22, 0.4)]) * np.sin(np.pi * tm / 0.2)
    mix_into(out, pan_mono(hs, -0.3), n_of(0.02), 0.35)
    ti = float(p.get("ti", 0.2))
    boom = _sum(_thump(_N(0.6), 115, 52, 0.02, 0.3), _door_panel(rng, _N(0.9)) * 0.7,
                _burst(_N(0.1), rng, 60, 1600, t60=0.05, attack=0.0005))
    mix_into(out, pan_mono(boom, 0.45), n_of(ti), 1.25)
    mix_into(out, pan_mono(_sum(_thump(_N(0.25), 90, 55, 0.02, 0.1), _burst(_N(0.06), rng, 80, 700, t60=0.03, attack=0.002)), 0.5), n_of(ti + 0.004), 0.5)
    for k in range(7):
        r = _hit(rng, [rng.uniform(900, 2400), rng.uniform(2600, 4800)], [0.05, 0.03], click=0.4, n=_N(0.08))
        mix_into(out, pan_mono(r, rng.uniform(0.0, 0.7)), n_of(ti + 0.02 + rng.exponential(0.12)), rng.uniform(0.1, 0.25))
    out = reverb(out, "apt9", wet_db=-9.0)[:n]
    return fade(out, 0.0, 0.3)


@_sfx("door_slam", space=0.5, hit=True, trim=1.0)
def _door_slam(dur, p, rng):
    """She slams the door on him: the slab's air thump, a big panel boom, the latch clacking home
    and the frame rattling, heard from the hallway."""
    n = _N(1.4)
    out = np.zeros(n)
    m = _N(0.12)
    _place(out, sos(pink(m, rng), "lowpass", 500, 2) * np.linspace(0, 1, m) ** 2, 0.0, 0.5)
    t0 = 0.11
    _place(out, _thump(_N(0.5), 125, 58, 0.018, 0.25), t0, 1.0)
    _place(out, _door_panel(rng, _N(0.9)) * 0.75, t0, 1.0)
    _place(out, _burst(_N(0.08), rng, 70, 1500, t60=0.04, attack=0.0005), t0, 1.0)
    _place(out, _hit(rng, [1500, 2800, 4100], [0.05, 0.04, 0.03], click=0.9), t0 + 0.008, 0.5)
    for k in range(4):
        _place(out, _hit(rng, [rng.uniform(600, 1300), rng.uniform(1400, 2600)], [0.04, 0.03], click=0.0), t0 + 0.04 + 0.03 * k + rng.uniform(0, 0.02), 0.12)
    out = reverb(out, "hallway", wet_db=-9.0)[:n]
    return fade(out, 0.0, 0.3)


@_sfx("key_lock", space=0.7, hit=True, trim=-2.0)
def _key_lock(dur, p, rng):
    """The key turned in the lock: teeth ratcheting over the pins as it goes in (insert=1), the
    turn (a dry metal creak), the cam's click and the deadbolt thrown home - 'ka-CHUNK' - at
    bolt_at (s from the start), the key ring's small jingle."""
    ins = bool(p.get("insert", 1))
    c0 = 0.17 if ins else 0.0
    bolt_at = float(p.get("bolt_at", c0 + 0.35))
    n = _N(bolt_at + 0.6)
    out = np.zeros(n)
    if ins:
        tt, gap = 0.0, 0.024
        for k in range(6):
            _place(out, _hit(rng, [rng.uniform(3000, 4200), rng.uniform(5200, 7200)], [0.01, 0.007], click=0.8, n=_N(0.025)), tt, 0.35)
            tt += gap
            gap *= 0.85
        m = _N(0.13)
        _place(out, bandpass(white(m, rng), 2000, 7000, 2) * np.hanning(m) * 0.15, 0.0)
    Lc = max(0.08, bolt_at - c0 - 0.07)
    m = _N(Lc)
    tm = t_axis(m)
    cr = friction(m, 150 + 160 * tm / Lc, rng, jitter=0.2, body=[(2100, 12, 1.0), (3400, 15, 0.5)]) * np.sin(np.pi * tm / Lc)
    _place(out, cr, c0, 0.5)
    _place(out, _hit(rng, [1300, 2400, 3600], [0.05, 0.04, 0.03], click=0.9), bolt_at - 0.07, 0.7)
    bolt = _sum(_thump(_N(0.2), 165, 92, 0.01, 0.08), _hit(rng, [600, 1100, 1900, 2900], [0.09, 0.07, 0.05, 0.03], click=0.6))
    _place(out, sos(bolt, "lowpass", 7000, 2), bolt_at, 1.0)        # a 'chunk', not a digital tick
    for k in range(int(rng.integers(5, 9))):
        f = rng.uniform(3000, 7500)
        _place(out, _hit(rng, [f, f * 1.37, f * 2.1], [0.08, 0.05, 0.03], click=0.2, n=_N(0.12)), bolt_at + 0.04 + rng.uniform(0, 0.3),
               rng.uniform(0.06, 0.15))
    return out


def _hammer_blow(rng, strength=1.0):
    n = _N(0.65)
    out = np.zeros(n)
    _place(out, _thump(_N(0.35), 125 * rng.uniform(0.95, 1.05), 62, 0.012, 0.16), 0.0, 1.0)
    _place(out, _door_panel(rng, _N(0.6), rng.uniform(0.97, 1.03)), 0.0, 0.7)
    _place(out, _burst(_N(0.08), rng, 70, 1300, t60=0.035, attack=0.0008), 0.0, 1.0)
    for j in range(3):
        _place(out, _hit(rng, [1250 + 800 * rng.uniform(), 2400 + 1200 * rng.uniform()], [0.03, 0.02], click=0.4, n=_N(0.05)),
               0.012 + 0.018 * j + rng.uniform(0, 0.01), 0.16)
    return out * strength


@_sfx("door_hammer", kind="sustained", norm="max", default_dur=2.0, space=0.6, hit=True)
def _door_hammer(dur, p, rng):
    """Fists pounding the locked door from the other side, heard from the hallway: each blow a
    heavy panel boom with the bolt and latch chattering, in desperate irregular groups. rate =
    blows per second inside a group; or times = the exact blow offsets (s). rattle 0..1: the
    lever handle rattling in its rose after each blow."""
    n = _N(dur)
    out = np.zeros(n)
    rattle = float(p.get("rattle", 0.0))
    if p.get("times") is not None:
        blows = [(float(v), rng.uniform(0.85, 1.0)) for v in p["times"]]
    else:
        rate = float(p.get("rate", 3.4))
        blows, tt = [], 0.0
        while tt < dur - 0.3:
            for j in range(int(rng.integers(2, 5))):
                if tt >= dur - 0.3:
                    break
                blows.append((tt, rng.uniform(0.7, 1.0) * (1.0 if j == 0 else 0.88)))
                tt += (1.0 / rate) * rng.uniform(0.8, 1.2)
            tt += rng.uniform(0.18, 0.45)
    for tt, g in blows:
        _place(out, _hammer_blow(rng), tt, g)
        if rattle > 0:
            m = _N(0.16)
            tm = t_axis(m)
            r = friction(m, 140 + 60 * rng.uniform(), rng, jitter=0.6, body=[(2300, 9, 1.0), (3700, 11, 0.6), (5600, 14, 0.3)])
            r *= np.exp(-tm / 0.05) * np.clip(tm / 0.004, 0, 1)
            _place(out, r, tt + 0.006, 0.35 * rattle)
    out = reverb(out, "hallway", wet_db=-10.0)[:n]
    return fade(out, 0.0, 0.08)


@_sfx("lamp_crash", space=0.5, hit=True, trim=1.0)
def _lamp_crash(dur, p, rng):
    """The show lamp knocked over: a tripod foot scraping, the head and shade hitting the boards
    (metal clank + floor thump), the bulb bursting (filament snap, zap, glass; pop=0 keeps it
    alive - it pops later, separately), the steel legs clattering and bouncing, a last roll and
    settle."""
    n = _N(2.4)
    out = np.zeros((n, 2))
    m = _N(0.16)
    mix_into(out, pan_mono(friction(m, 90, rng, jitter=0.5, body=[(900, 4, 1.0), (2100, 6, 0.4)]) * np.hanning(m), -0.2), 0, 0.4)
    ti = 0.17
    head = _sum(_hit(rng, np.array([480, 1130, 1950, 3100, 4600]) * rng.uniform(0.95, 1.05), [0.45, 0.35, 0.25, 0.18, 0.12], spread=0.02, click=0.8),
                _thump(_N(0.3), 140, 70, 0.012, 0.12), _burst(_N(0.07), rng, 80, 2000, t60=0.03, attack=0.0004))
    mix_into(out, pan_mono(head, 0.2), n_of(ti), 1.0)
    s_pop = int(rng.integers(1 << 30))
    s_gl = int(rng.integers(1 << 30))
    if p.get("pop", 1):
        pop = lib.render("bulb_pop", seed=s_pop).astype(np.float64)
        mix_into(out, pop, n_of(ti + 0.006), 0.8)
        gl = lib.render("glass_break", seed=s_gl).astype(np.float64)[:_N(1.2)]
        gl = fade(sos(gl, "highpass", 1500, 2), 0.0, 0.4)
        mix_into(out, gl, n_of(ti + 0.008), 0.35)
        m = _N(0.09)
        zap = sos(saturate(np.sin(TWO_PI * 120 * t_axis(m)), 6.0), "bandpass", (200, 6000), 2) * exp_env(m, 0.08)
        mix_into(out, pan_mono(zap, 0.2), n_of(ti), 0.3)
    tube = np.array([830, 2290, 4480, 7400])
    tt, gap, a = ti + 0.07, 0.11, 0.8
    for k in range(6):
        f = tube * rng.uniform(0.8, 1.25)
        h = _hit(rng, f, [0.35, 0.25, 0.15, 0.1], spread=0.02, click=0.6, n=_N(0.5))
        mix_into(out, pan_mono(h, rng.uniform(-0.5, 0.6)), n_of(tt), a)
        tt += gap * rng.uniform(0.8, 1.2)
        gap *= 0.8
        a *= 0.72
    m = _N(0.6)
    roll = friction(m, 60, rng, jitter=0.6, body=[(830, 8, 1.0), (2290, 10, 0.5)]) * np.hanning(m)
    mix_into(out, pan_mono(roll, 0.4), n_of(tt + 0.05), 0.25)
    mix_into(out, pan_mono(_hit(rng, tube * rng.uniform(0.9, 1.1), [0.2, 0.15, 0.1, 0.06], click=0.5, n=_N(0.4)), 0.5), n_of(tt + 0.6), 0.25)
    out = reverb(out, "apt9", wet_db=-9.0)[:n]
    return fade(out, 0.0, 0.3)


# ============================================================================ outside & stairs
@_sfx("police_radio", space=0.4)
def _police_radio(dur, p, rng):
    """A 1950s police-car radio: carrier thump, squelch, a crushed dispatcher (the shared
    radio_static babble, narrower and more driven, a 60 Hz tube hum under it), the squelch tail.
    dist 0..1 (0 = in the car / close)."""
    x = lib.render("radio_static", seed=int(rng.integers(1 << 30))).astype(np.float64)
    m = dsp.mono(x)
    m = bandpass(m, 380, 2900, 3)
    m = saturate(m / (np.max(np.abs(m)) + 1e-9) * 2.0, 2.5) * 0.5
    n = len(m)
    t = t_axis(n)
    m += 0.02 * np.sin(TWO_PI * 60 * t) * (np.abs(m) > 0.02)
    out = np.zeros(n + _N(0.05))
    _place(out, _thump(_N(0.05), 180, 120, 0.004, 0.02), 0.0, 0.3)
    _place(out, m, 0.01, 1.0)
    return _distance(out, float(p.get("dist", 0.3)), rng)


def _siren_tone(speed, rng, n):
    """Mechanical siren (a rotor chopping air through a stator): the pitch follows the rotor speed
    (0..1); rich harmonics, slightly driven; air noise around the second harmonic."""
    f0 = 140.0 + 1000.0 * np.asarray(speed, dtype=np.float64)
    ph = np.cumsum(f0) / SR
    tone = np.zeros(n)
    for k, a in ((1, 1.0), (2, 0.55), (3, 0.4), (4, 0.22), (5, 0.15), (6, 0.08)):
        lim = np.clip((15000.0 - k * f0) / 2000.0, 0, 1)
        tone += a * lim * np.sin(TWO_PI * k * ph + rng.uniform(0, TWO_PI))
    tone = saturate(tone * 0.8, 1.6)
    air = tv_bandpass(white(n, rng), np.clip(f0 * 2.0, 200, 9000), q=3.0, block=128) * 0.25
    return tone + air


@_sfx("siren_whoop", space=0.0)
def _siren_whoop(dur, p, rng):
    """A police-car siren 'whoop': the rotor spun up hard in a third of a second and let go, the
    pitch sagging back down. dist 0..1."""
    n = _N(1.7)
    t = t_axis(n)
    up = 0.3
    speed = np.where(t < up, np.sin(0.5 * np.pi * np.clip(t / up, 0, 1)) ** 1.2, 0.3 + 0.7 * np.exp(-(t - up) / 0.45))
    amp = np.clip(t / 0.03, 0, 1) * np.where(t < up, 0.6 + 0.4 * (t / up), np.exp(-(t - up) / 0.55))
    x = _siren_tone(speed, rng, n) * amp
    return _distance(x, float(p.get("dist", 0.4)), rng)


@_sfx("siren_wail", kind="sustained", norm="max", default_dur=4.0, space=0.0)
def _siren_wail(dur, p, rng):
    """Mechanical police sirens wailing (cars = 1-2, each its own period and pan). mode
    'approach' (far -> near: level up 22 dB, the top end opening, reverb giving way), 'far'
    (steady, distant, dull), 'away' (the reverse of approach), 'winddown' (one siren running down
    to a growl and stopping, as the car pulls up)."""
    mode = p.get("mode", "approach")
    cars = int(p.get("cars", 2))
    n = _N(dur)
    t = t_axis(n)
    u = np.clip(t / dur, 0, 1)
    out = np.zeros((n, 2))
    for c in range(cars):
        per = float(p.get("period", 3.2)) * (1 + 0.13 * c)
        ph = (t / per + rng.uniform()) % 1.0
        wail = np.where(ph < 0.4, np.sin(0.5 * np.pi * ph / 0.4), 0.5 + 0.5 * np.cos(np.pi * (ph - 0.4) / 0.6))
        speed = 0.45 + 0.55 * wail
        if mode == "winddown":
            speed = np.clip(0.9 * (1 - u) ** 1.2 + 0.05 * wail, 0.0, 1.0)
            lev = np.clip((1 - u) ** 0.6, 0, 1) * np.clip(t / 0.2, 0, 1)
            lp = np.full(n, 3500.0)
        elif mode == "far":
            lev = np.full(n, 1.0)
            lp = np.full(n, 1700.0)
        else:
            k = u if mode == "approach" else 1 - u
            lev = db2lin(-22.0 * (1 - k) ** 1.3)
            lp = 1300 + 5200 * k ** 1.5
        x = _siren_tone(speed, rng, n) * lev
        x = tv_lowpass(x, lp, q=0.7, block=256)
        out += pan_mono(x, (-0.35 + 0.7 * c) if cars > 1 else 0.1) * (1.0 if c == 0 else 0.8)
    wet = dsp.convolve(out.mean(axis=1), dsp.make_ir("street"))[:n]
    far_amt = {"far": 1.0, "winddown": 0.5}.get(mode, None)
    if far_amt is None:
        k = u if mode == "approach" else 1 - u
        far_amt = (1 - 0.7 * k)[:, None]
    return fade(out * 0.8 + wet * far_amt * 0.9, 0.3, 0.3)


@_sfx("flashlight_click", space=0.7)
def _flashlight_click(dur, p, rng):
    """A long 4-cell steel police torch switched on: the thumb pushing the slide (a short dry
    scrape), the switch clacking home in the tube (steel ring), the spring's small boing."""
    n = _N(0.35)
    out = np.zeros(n)
    m = _N(0.03)
    _place(out, friction(m, 260, rng, jitter=0.3, body=[(2600, 8, 1.0)]) * np.hanning(m), 0.0, 0.35)
    _place(out, _hit(rng, np.array([1750, 3150, 4900, 6800]) * rng.uniform(0.95, 1.05), [0.05, 0.04, 0.03, 0.02], spread=0.02, click=0.9), 0.03, 1.0)
    _place(out, modal([3600.0], [0.08], [1.0], _N(0.12)), 0.031, 0.05)
    _place(out, _thump(_N(0.05), 300, 200, 0.005, 0.02), 0.03, 0.25)
    return out


def _wood_step(rng, who="her", weight=0.6, creak=0.0, stair=True):
    """One step on old wooden boards. her: a 1950s pump - a hard heel 'click' then the sole;
    him: a heavy leather heel, deep, the sole slapping. Stair treads boom over the void."""
    n = _N(0.95)
    out = np.zeros(n)
    w = float(weight)
    pitch = rng.uniform(0.93, 1.07)
    if who == "her":
        _place(out, _hit(rng, np.array([1650, 2900, 4400, 6200]) * pitch, [0.025, 0.02, 0.014, 0.01], spread=0.04, click=1.0), 0.0, 0.8 + 0.3 * w)
        _place(out, _burst(_N(0.05), rng, 300, 3500, t60=0.015, attack=0.0005), 0.0, 0.5)
        _place(out, _burst(_N(0.05), rng, 200, 2500, t60=0.02, attack=0.001), 0.05 + 0.03 * rng.uniform(), 0.35)
        tg = 0.45
    else:
        _place(out, _thump(_N(0.3), (125 + 20 * w) * pitch, (60 + 8 * w) * pitch, 0.012, 0.08 + 0.06 * w), 0.0, 0.8 + 0.4 * w)
        _place(out, _burst(_N(0.08), rng, 80, 1500, t60=0.035, attack=0.0008), 0.0, 0.7 + 0.4 * w)
        _place(out, _burst(_N(0.06), rng, 350, 4000, t60=0.02, attack=0.0006), 0.06 + 0.04 * rng.uniform(), 0.35)
        tg = 0.9
    tread = modal(np.array([118, 187, 296, 455, 690]) * rng.uniform(0.9, 1.1), np.array([0.12, 0.1, 0.08, 0.06, 0.04]) * (1.3 if stair else 0.8),
                  [1.0, 0.8, 0.6, 0.4, 0.25], _N(0.3), phases=rng.uniform(0, TWO_PI, 5))
    _place(out, tread, 0.001, tg * (1.0 if stair else 0.6))
    if creak > 0 and rng.uniform() < creak:
        L = rng.uniform(0.18, 0.42)
        m = _N(L)
        tm = t_axis(m)
        sw = np.sin(np.pi * tm / L) ** 0.8
        cr = friction(m, (45 + 70 * sw) * rng.uniform(0.8, 1.25), rng, jitter=0.3,
                      body=[(rng.uniform(240, 340), 6, 1.0), (rng.uniform(600, 800), 8, 0.7), (rng.uniform(1300, 1700), 10, 0.35)])
        _place(out, cr * sw, 0.02 + rng.uniform(0, 0.05), rng.uniform(0.25, 0.5))
    return out


@_sfx("wood_step", space=1.0)
def _wood_step_sfx(dur, p, rng):
    """One footstep on wooden boards / a stair tread. who 'her'|'him', weight 0..1, creak prob,
    stair 0/1."""
    return _wood_step(rng, p.get("who", "her"), float(p.get("weight", 0.6)), float(p.get("creak", 0.3)), bool(p.get("stair", 0)))


@_sfx("stair_steps", kind="sustained", norm="max", default_dur=2.0, space=0.0)
def _stair_steps(dur, p, rng):
    """Footsteps on the wooden spiral stairs with their own stairwell: rate (steps/s), who
    ('her' quick heels / 'him' slow, heavy), d0 -> d1 distance (0 near .. 1 far: level, top end,
    reverb), creak probability, spin (turns per second of the spiral: the pan circles)."""
    rate = float(p.get("rate", 4.0))
    who = p.get("who", "her")
    d0, d1 = float(p.get("d0", 0.2)), float(p.get("d1", 0.8))
    creak = float(p.get("creak", 0.35))
    spin = float(p.get("spin", 0.3))
    weight = float(p.get("weight", 0.6 if who == "her" else 0.85))
    n = _N(dur)
    dry = np.zeros((n, 2))
    send = np.zeros(n)
    tt, k = 0.02, 0
    ph0 = rng.uniform(0, TWO_PI)
    while tt < dur - 0.12:
        d = d0 + (d1 - d0) * (tt / dur)
        s = _wood_step(rng, who, weight, creak, stair=True)
        s = sos(s, "lowpass", 9500 * (1 - d) + 1700 * d, 2)
        g = db2lin(-20.0 * d) * rng.uniform(0.85, 1.0) * (1.0 if k % 2 == 0 else 0.9)
        pan = 0.55 * math.sin(TWO_PI * spin * tt + ph0)
        mix_into(dry, pan_mono(s, pan), n_of(tt), g * (1.0 - 0.45 * d))
        mix_into(send, s, n_of(tt), g * (0.35 + 0.65 * d))
        tt += (1.0 / rate) * rng.uniform(0.9, 1.1)
        k += 1
    wet = dsp.convolve(send, ir("stairwell"))[:n] * db2lin(-5.0)
    return fade(dry + wet, 0.01, 0.2)


@_sfx("steps_seq", kind="sustained", norm="max", default_dur=2.0, space=1.0)
def _steps_seq(dur, p, rng):
    """A short walk: kind 'wet' (the shared footstep on wet asphalt, splashing) or 'floor'
    (wooden boards); rate steps/s, who/weight, pan0 -> pan1, g0 -> g1 dB across the walk."""
    kind = p.get("kind", "floor")
    rate = float(p.get("rate", 2.0))
    who = p.get("who", "her")
    weight = float(p.get("weight", 0.6))
    pan0, pan1 = float(p.get("pan0", 0.0)), float(p.get("pan1", 0.0))
    g0, g1 = float(p.get("g0", 0.0)), float(p.get("g1", 0.0))
    creak = float(p.get("creak", 0.25))
    n = _N(dur)
    out = np.zeros((n, 2))
    tt, k = 0.02, 0
    while tt < dur - 0.1:
        u = tt / dur
        if kind == "wet":
            s = lib.render("footstep_run" if p.get("run") else "footstep", params=dict(weight=weight, wet=1),
                           seed=int(rng.integers(1 << 30))).astype(np.float64)
            s = dsp.mono(s)
        else:
            s = _wood_step(rng, who, weight, creak, stair=False)
            s = s / (np.max(np.abs(s)) + 1e-9) * 0.5
        mix_into(out, pan_mono(s, pan0 + (pan1 - pan0) * u), n_of(tt), db2lin(g0 + (g1 - g0) * u) * (1.0 if k % 2 == 0 else 0.92))
        tt += (1.0 / rate) * rng.uniform(0.92, 1.08)
        k += 1
    return fade(out, 0.005, 0.15)


@_sfx("umbrella_pass", kind="sustained", norm="max", default_dur=2.5, space=0.0)
def _umbrella_pass(dur, p, rng):
    """An umbrella going by in the rain, heard from above: drops drumming on the taut canopy
    (fabric-drum resonances), runoff dripping from its rim onto the puddles, footsteps under it;
    swelling as it passes pan0 -> pan1. dist 0..1."""
    n = _N(dur)
    t = t_axis(n)
    u = np.clip(t / dur, 0, 1)
    near = np.sin(np.pi * u) ** 1.5
    drum = dsp.resonator_bank(_imp_train(np.full(n, 330.0) * (1 + 0.3 * smooth_noise(n, 5, rng)), n, rng, 0.8),
                              [1050, 1650, 2550, 3800], [4, 5, 6, 7], [1.0, 0.8, 0.55, 0.3]) * 1.6
    drum += 0.25 * bandpass(white(n, rng), 1500, 6000, 2) * (0.5 + 0.5 * np.abs(smooth_noise(n, 20, rng)))
    out = drum * near
    for tt in np.sort(rng.uniform(0.0, dur, int(dur * 9))):
        _place(out, _drop(rng, rng.uniform(900, 2600), rng.uniform(0.004, 0.01), 0.6) * near[min(n - 1, n_of(tt))], tt, rng.uniform(0.1, 0.3))
    st = 0.15 + rng.uniform(0, 0.2)
    while st < dur - 0.3:
        s = dsp.mono(lib.render("footstep", params=dict(weight=0.55, wet=1), seed=int(rng.integers(1 << 30))).astype(np.float64))
        _place(out, s * 0.35 * near[min(n - 1, n_of(st))], st)
        st += rng.uniform(0.5, 0.6)
    y = _pan_sweep(out, float(p.get("pan0", -0.7)), float(p.get("pan1", 0.7)))
    d = float(p.get("dist", 0.6))
    y = sos(y, "lowpass", 9000 * (1 - d) + 2500 * d, 2)
    wet = dsp.convolve(y.mean(axis=1), dsp.make_ir("street"))[:n] * (0.3 + 0.5 * d)
    return fade(y + wet, 0.2, 0.3)


@_sfx("radiator_tick", space=0.8)
def _radiator_tick(dur, p, rng):
    """The cast-iron radiator under her window, expanding: a small metallic ping-knock (or a
    double one), very quiet in the mix."""
    n = _N(0.6)
    out = np.zeros(n)
    f = np.array([620, 1350, 2240, 3100]) * rng.uniform(0.85, 1.2)
    _place(out, _hit(rng, f, [0.25, 0.18, 0.12, 0.08], spread=0.03, click=0.7), 0.0, 1.0)
    if rng.uniform() < 0.4:
        _place(out, _hit(rng, f * rng.uniform(0.97, 1.03), [0.2, 0.14, 0.1, 0.06], click=0.6), rng.uniform(0.08, 0.2), 0.5)
    return out


@_sfx("phonograph_waltz", kind="sustained", norm="int", default_dur=4.0, space=0.0)
def _phonograph_waltz(dur, p, rng):
    """Window 4's record player heard from across the street through glass: a little music-box
    waltz in C (oom-pah-pah under a felt-piano tune), 78-rpm surface crackle and hiss, a narrow
    tinny band, a wobble of wow, the street's air."""
    beat = 60.0 / 168.0
    n = _N(dur)
    out = np.zeros(n)
    melody = [(76, 3), (79, 2), (77, 1), (76, 3), (74, 2), (72, 1), (74, 3), (77, 2), (76, 1), (74, 6),
              (76, 3), (79, 2), (77, 1), (76, 3), (81, 2), (79, 1), (77, 3), (76, 2), (74, 1), (72, 6)]
    chords = [(48, [64, 67]), (43, [62, 65, 67]), (43, [62, 65, 67]), (48, [64, 67]),
              (48, [64, 67]), (45, [64, 69]), (43, [62, 65, 67]), (48, [64, 67])]
    tt = 0.0
    for midi, beats in melody:
        if tt >= dur:
            break
        m = _N(min(beats * beat + 0.4, dur - tt + 0.4))
        _place(out, lib._felt_piano_note(float(_hz(midi)), m, 0.7, rng) * 0.5, tt)
        tt += beats * beat
    bar = 0
    tb = 0.0
    while tb < dur:
        bass, ch = chords[bar % len(chords)]
        _place(out, lib._felt_piano_note(float(_hz(bass)), _N(beat * 1.2), 0.6, rng) * 0.45, tb)
        for b in (1, 2):
            for c in ch:
                _place(out, lib._felt_piano_note(float(_hz(c)), _N(beat * 0.8), 0.45, rng) * 0.18, tb + b * beat)
        tb += 3 * beat
        bar += 1
    out = dsp.pad_to(out, n)
    t = t_axis(n)
    wow = 40.0 * np.sin(TWO_PI * 0.55 * t)          # +-40 samples: about 0.3 % pitch wow
    idx = np.clip(np.arange(n) + wow, 0, n - 1)
    out = np.interp(idx, np.arange(n), out)
    out = bandpass(out, 350, 3000, 2)
    out = saturate(out * 2.0, 1.5) * 0.5
    out += 0.05 * bandpass(crackle(n, 60, rng, amp_spread=1.0), 1200, 6000, 2) + 0.006 * bandpass(white(n, rng), 2000, 6000, 2)
    out = sos(out, "lowpass", 2600, 2)
    wet = dsp.convolve(out, dsp.make_ir("street"))[:n] * 0.7
    return fade(to_stereo(out * 0.6) + wet, 0.4, 0.8)


@_sfx("flame_flicker", kind="sustained", norm="int", default_dur=3.0, space=0.6)
def _flame_flicker(dur, p, rng):
    """A held match burning as she carries it through the dark room: a soft breathy hiss that
    flickers, a few tiny crackles."""
    n = _N(dur)
    t = t_axis(n)
    flick = np.clip(1.0 + 0.5 * smooth_noise(n, 9.0, rng) + 0.2 * smooth_noise(n, 2.0, rng), 0.2, None)
    x = bandpass(white(n, rng), 180, 1500, 2) * flick * 0.5
    ck = np.convolve(crackle(n, 7, rng, amp_spread=1.0), np.hanning(_N(0.0006)))[:n]
    x += bandpass(ck, 1500, 6000, 2) * 0.5
    x *= 1.0 - 0.3 * np.exp(-t / 0.5)
    return fade(x, 0.15, 0.25)


# ============================================================================ the shadow murder
def _string_cluster(midis, n, rng, bend, voices=5, cents=9.0):
    """Violin ensemble on a cluster: per note `voices` detuned PolyBLEP saws (per channel), the
    per-sample pitch multiplier `bend` shared by all."""
    out = np.zeros((n, 2))
    for i, mm in enumerate(midis):
        f = float(_hz(mm))
        for ch in range(2):
            v = np.zeros(n)
            for k in range(voices):
                v += saw(f * 2 ** (rng.normal(0, cents) / 1200) * bend, n, phase0=rng.uniform())
            out[:, ch] += v / voices * (1.0 if i < 2 else 0.8)
    return out


@_sfx("string_stab", space=0.0, hit=True, trim=2.0)
def _string_stab(dur, p, rng):
    """The shrill string stab, one per knife blow (a Psycho echo, our own): violins divisi in a
    tight cluster high up (B5 C6 F6, + `step` semitones: the stabs climb), hammered down-bow - a
    scratch of rosin, a savage attack that scoops down from a quarter-tone sharp, then shrieks
    DOWN a semitone as the bow drags; cellos and basses slap a low thud under it (the blow). A
    short hall. size 0..1."""
    step = float(p.get("step", 0.0))
    s = float(np.clip(p.get("size", 0.7), 0, 1))
    n = _N(1.4)
    t = t_axis(n)
    L = 0.2 + 0.1 * s
    bend = 2.0 ** ((0.45 * np.exp(-t / 0.012) - 1.15 * np.clip((t - 0.06) / L, 0, 1) ** 1.5) / 12.0)
    env = np.clip(t / 0.004, 0, 1) * (0.55 + 0.45 * np.exp(-t / 0.05)) * np.where(t < L, 1.0, np.exp(-(t - L) / 0.06))
    x = _string_cluster(np.array([83, 84, 89]) + step, n, rng, bend)
    x = sos(x, "lowpass", 9000, 2)
    x = biquad(x, "peak", 2700, 1.0, 4.0)
    x = biquad(x, "peak", 520, 1.2, 2.5)
    x *= env[:, None]
    x += to_stereo(bandpass(white(n, rng), 1800, 9000, 2) * ar_env(n, 0.001, 0.05) * 0.9)
    low = _sum(_thump(_N(0.5), 110, 52, 0.02, 0.25), _burst(_N(0.06), rng, 60, 900, t60=0.03, attack=0.0008),
               _hit(rng, [110, 220, 330], [0.15, 0.1, 0.07], click=0.4) * 0.5)
    mix_into(x, to_stereo(low), 0, 0.7 + 0.3 * s)
    x = saturate(x * 0.9, 1.3)
    x = dsp.reverb(x, "hall", wet_db=-9.0, dry=1.0)[:n]
    return fade(x, 0.0, 0.3), 3.0 * (s - 0.7)


@_sfx("scream_pull", space=0.0, hit=True)
def _scream_pull(dur, p, rng):
    """The silent scream: air sucked in - a rising, inhaling rush (noise swept 400 Hz -> 5 kHz,
    swelling), a reversed-reverb 'suck' into the moment, a thin whistle climbing with it - and then
    nothing: it cuts off dead at `length` (the mouth is open, no sound comes)."""
    L = float(p.get("length", 0.95))
    n = _N(L + 0.06)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    out = np.zeros((n, 2))
    for ch in range(2):
        x = tv_bandpass(white(n, rng), 400 * (12.5 ** (u ** 1.6)), q=1.4, block=64)
        x += 0.4 * tv_bandpass(pink(n, rng), 250 + 900 * u, q=0.8, block=64)
        out[:, ch] = x * u ** 2.5
    m = _N(0.25)
    hit = bandpass(white(m, rng), 600, 6000, 2) * exp_env(m, 0.15)
    rv = dsp.convolve(hit, dsp.make_ir("hall"))[::-1]
    k = min(len(rv), n)
    out[n - k:] += rv[-k:] * 0.9 if k == len(rv) else rv[len(rv) - k:] * 0.9
    wh = np.sin(TWO_PI * np.cumsum(1800 + 1600 * u ** 1.3 + 20 * np.sin(TWO_PI * 6 * t)) / SR) * u ** 3 * 0.12
    out += to_stereo(wh)
    cut = n_of(L)
    out[cut:] = 0.0
    out[max(0, cut - _N(0.008)):cut] *= np.linspace(1, 0, cut - max(0, cut - _N(0.008)))[:, None]
    return out


@_sfx("glint", space=0.0)
def _glint(dur, p, rng):
    """A cold glint off a lens: a high glassy ping (inharmonic bar partials beating slowly, a
    shade different in each ear) with a fleck of sparkle. pitch multiplies the partials, decay
    scales the ring, attack (s) softens the strike (a lens ring rather than a glint)."""
    dk = float(p.get("decay", 1.0))
    n = _N(0.4 + 1.5 * dk)
    t = t_axis(n)
    f1 = 2637.0 * float(p.get("pitch", 1.0)) * rng.uniform(0.995, 1.005)
    x = np.zeros((n, 2))
    for ratio, a, t60 in ((1.0, 1.0, 1.5), (2.32, 0.38, 0.9), (4.25, 0.18, 0.5), (5.4, 0.08, 0.3)):
        if f1 * ratio > 17000:
            continue
        for ch in range(2):
            beat = 0.7 + 0.5 * ch
            x[:, ch] += a * 0.5 * (np.sin(TWO_PI * (f1 * ratio - beat) * t + rng.uniform(0, 6))
                                   + np.sin(TWO_PI * (f1 * ratio + beat) * t + rng.uniform(0, 6))) * np.power(10.0, -3 * t / (t60 * dk))
    ka = _N(max(0.0015, float(p.get("attack", 0.0015))))
    x[:ka] *= (np.linspace(0, 1, ka) ** 1.5)[:, None]
    sp = bandpass(white(_N(0.2), rng), 6000, 14000, 2) * exp_env(_N(0.2), 0.12) * 0.25
    x[:len(sp)] += sp[:, None]
    return fade(x, 0.0, 0.4)


@_sfx("red_line", space=0.0)
def _red_line(dur, p, rng):
    """S05's thin red line drawn between the panels: a fine 'tsing' (a high glassy tone, slightly
    rising, with a shimmer of its octave) over the faint grain of a pen line, centred."""
    n = _N(1.3)
    t = t_axis(n)
    f = 2960.0 * rng.uniform(0.99, 1.01) * (1 + 0.012 * np.clip(t / 0.25, 0, 1))
    ph = np.cumsum(f) / SR
    env = np.clip(t / 0.03, 0, 1) ** 1.5 * np.power(10.0, -3 * np.maximum(t - 0.03, 0) / 1.0)
    x = (np.sin(TWO_PI * ph) + 0.22 * np.sin(TWO_PI * 2.003 * ph + 1.0) + 0.08 * np.sin(TWO_PI * 3.01 * ph)) * env
    trem = 1 + 0.12 * np.sin(TWO_PI * 7.0 * t)
    m = _N(0.22)
    pen = bandpass(crackle(m, 3000, rng, amp_spread=0.6), 2500, 9000, 2) * np.sin(np.pi * np.linspace(0, 1, m)) * 0.25
    out = x * trem * 0.5
    _place(out, pen, 0.0, 1.0)
    return _wide(out, rng, 0.35)


# ============================================================================ Bass graphics
@_sfx("paper_pop", space=0.5)
def _paper_pop(dur, p, rng):
    """A cut-paper rectangle landing on the paper field: a soft card 'tup', a crisp edge tick and
    a breath of air. pitch scales the card (row by row)."""
    k = float(p.get("pitch", 1.0)) * rng.uniform(0.94, 1.06)
    n = _N(0.14)
    out = np.zeros(n)
    _place(out, _thump(_N(0.08), 420 * k, 260 * k, 0.006, 0.025), 0.0, 0.7)
    _place(out, _burst(_N(0.05), rng, 250 * k, 2200 * k, t60=0.018, attack=0.0006), 0.0, 0.9)
    _place(out, _click(rng, 2800, 0.0016, _N(0.006)), 0.0005, 0.35)
    _place(out, _burst(_N(0.06), rng, 1800, 7000, t60=0.03, attack=0.002), 0.004, 0.08)
    return out


@_sfx("paper_slide", space=0.5)
def _paper_slide(dur, p, rng):
    """Card sliding over paper (the title letters, the split-screen panels): toothy friction
    grain whose band follows the speed, panning pan0 -> pan1, a soft stop tap. length s.
    shape: 'sym' (ease in-out), 'out' (flicked: fast start, coasting stop - a strip whisking in),
    'in' (accelerating into a dead stop - a card shot home along a rail)."""
    L = float(p.get("length", 0.45))
    n = _N(L + 0.15)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    shape = str(p.get("shape", "sym"))
    if shape == "out":
        speed = (1.0 - u) ** 1.6 * np.clip(t / 0.006, 0, 1) * (t < L)
    elif shape == "in":
        speed = u ** 1.6 * np.clip((L - t) / 0.004, 0, 1) * (t < L)
    else:
        speed = np.sin(np.pi * u) ** 0.8 * (t < L)
    grain = bandpass(crackle(n, 2600, rng, amp_spread=0.8), 900, 6500, 2) * 1.6
    grain += 0.35 * tv_bandpass(white(n, rng), 1200 + 3000 * speed, q=0.7, block=64)
    body = 0.25 * bandpass(pink(n, rng), 200, 900, 2)
    x = (grain + body) * speed
    if p.get("tap", 1):
        _place(x, _burst(_N(0.04), rng, 300, 2500, t60=0.015, attack=0.0008), L * 0.97, 0.5)
    return _pan_sweep(x, float(p.get("pan0", -0.6)), float(p.get("pan1", 0.3)), u)


@_sfx("paper_splash", space=0.4)
def _paper_splash(dur, p, rng):
    """The red cut-paper splash bursting onto the sheet on the last stab (outback, 0.13 s): a
    card flap snapping open, a spray of paper flecks settling, a soft low pat under it. tear
    0..1: a short wet tear under it (s03's third stab)."""
    n = _N(0.5)
    t = t_axis(n)
    out = np.zeros(n)
    _place(out, _burst(_N(0.16), rng, 300, 4500, t60=0.08, attack=0.002), 0.0, 1.0)
    flecks = bandpass(crackle(n, 1400, rng, amp_spread=1.0), 2000, 8000, 2) * np.exp(-t / 0.09) * np.clip((t - 0.008) / 0.004, 0, 1)
    out += 1.6 * flecks
    _place(out, _thump(_N(0.12), 150, 85, 0.004, 0.05), 0.012, 0.7)
    for k in range(3):
        _place(out, _hit(rng, [rng.uniform(2500, 5000)], [0.01], click=0.6, n=_N(0.02)), 0.11 + 0.05 * k + rng.uniform(0, 0.02), 0.12)
    if p.get("tear", 0):                     # the wet tear: a short soggy rip under the flap
        m = _N(0.2)
        tm = t_axis(m)
        rate = 1800 * (1 - 0.6 * tm / 0.2)
        tr = bandpass(_imp_train(rate, m, rng, 0.7), 500, 3800, 2) * np.clip(tm / 0.01, 0, 1) * (1 - tm / 0.2) ** 0.7
        sq = bandpass(white(m, rng), 300, 1300, 2) * np.exp(-tm / 0.05) * 0.5
        _place(out, (tr * 1.2 + sq), 0.004, 0.8 * float(p.get("tear", 1)))
    return out


@_sfx("body_fold", space=0.5)
def _body_fold(dur, p, rng):
    """The paper body folding at the waist and dropping out of sight: the card creasing (a dry
    stick-slip crackle that quickens), the air of the drop, a soft flat thud as it lands.
    land: s from the cue to the landing."""
    land = float(p.get("land", 0.62))
    n = _N(land + 0.45)
    t = t_axis(n)
    u = np.clip(t / 0.3, 0, 1)
    env = u ** 1.5 * np.clip((0.32 - t) / 0.03, 0, 1)
    crease = friction(n, 40 + 160 * u, rng, jitter=0.35, body=[(900, 5, 1.0), (1800, 7, 0.6), (3500, 9, 0.3)]) * env
    v = np.clip((t - 0.1) / max(land - 0.1, 1e-3), 0, 1)
    air = sos(pink(n, rng), "lowpass", 900, 2) * np.sin(np.pi * v) ** 2 * (t < land) * 0.25
    out = 1.2 * crease + air
    _place(out, _sum(_thump(_N(0.2), 120, 60, 0.006, 0.07), 0.5 * _burst(_N(0.05), rng, 200, 1800, t60=0.02, attack=0.001)), land, 0.9)
    return out


@_sfx("rewind", space=0.3)
def _rewind(dur, p, rng):
    """The show's projector restarting: a mechanical clack, the film scrubbing back - sprocket
    chatter racing in a band of noise that falls in pitch and rate - and a second clack as it
    catches. length s (the scrub)."""
    L = float(p.get("length", 0.3))
    n = _N(L + 0.25)
    t = t_axis(n)
    out = np.zeros(n)
    clack = _sum(_hit(rng, [1700, 3100, 4700], [0.03, 0.02, 0.012], click=0.7), 0.5 * _thump(_N(0.06), 300, 180, 0.002, 0.02))
    _place(out, sos(clack, "lowpass", 8000, 2), 0.0, 1.0)
    u = np.clip((t - 0.03) / L, 0, 1)
    ph = np.cumsum(70.0 - 45.0 * u) / SR
    chatter = (0.5 + 0.5 * np.sin(TWO_PI * ph)) ** 3
    band = tv_bandpass(white(n, rng), 3200.0 - 2200.0 * u, q=1.2, block=64)
    out += 0.9 * band * chatter * np.sin(np.pi * u) ** 0.6 * (t > 0.03)
    _place(out, sos(_hit(rng, [1500, 2900], [0.025, 0.015], click=0.5), "lowpass", 7000, 2), 0.03 + L, 0.6)
    return out


@_sfx("count_ticks", space=0.5)
def _count_ticks(dur, p, rng):
    """The counting glint running over the forty windows: one tiny glassy tick per row of
    windows, each a little lower (a soft abacus), under a faint high shimmer of light.
    n ticks, gap s, pan0 -> pan1."""
    cnt = int(p.get("n", 8))
    gap = float(p.get("gap", 0.09))
    span = gap * cnt
    n = _N(span + 0.25)
    t = t_axis(n)
    out = np.zeros(n)
    for k in range(cnt):
        f = (1.0 - 0.035 * k) * rng.uniform(0.97, 1.03)
        _place(out, _hit(rng, np.array([2350, 3900, 6100]) * f, [0.03, 0.02, 0.012], spread=0.02, click=0.5, n=_N(0.06)),
               k * gap + rng.uniform(0, 0.004), 0.8 - 0.035 * k)
    out += bandpass(white(n, rng), 6000, 11000, 2) * _bell(t, span * 0.45, span * 0.45, 0.15) * 0.05
    return _pan_sweep(out, float(p.get("pan0", -0.45)), float(p.get("pan1", 0.45)), np.clip(t / span, 0, 1))


@_sfx("paper_flip", space=0.4)
def _paper_flip(dur, p, rng):
    """The whole paper field flipping over to night: a big card whooshing through the air with a
    flexing flutter, landing flat with a low 'whump'."""
    n = _N(0.95)
    t = t_axis(n)
    L = 0.55
    u = np.clip(t / L, 0, 1)
    sw = tv_bandpass(pink(n, rng), 300 + 1600 * np.sin(np.pi * u), q=0.8, block=64)
    env = np.sin(np.pi * u) ** 1.6 * (t < L)
    flex = 1 + 0.6 * np.sin(TWO_PI * 17 * t) * smooth_noise(n, 6, rng)
    out = sw * env * flex + 0.45 * sos(pink(n, rng), "lowpass", 500, 2) * env
    _place(out, _burst(_N(0.06), rng, 150, 2600, t60=0.025, attack=0.0008), L, 1.2)
    _place(out, _thump(_N(0.2), 110, 55, 0.012, 0.09), L, 0.8)
    return _pan_sweep(out, -0.35, 0.35, u)


@_sfx("grid_snap", space=0.3, hit=True)
def _grid_snap(dur, p, rng):
    """The grid of forty snapping tight: a cluster of paper ticks inside 50 ms, a solid card
    'thock' and a soft low thud."""
    n = _N(0.75)
    out = np.zeros((n, 2))
    for k in range(14):
        c = _sum(_click(rng, 2500, 0.0015, _N(0.006)) * 0.5, _burst(_N(0.03), rng, 400, 3500, t60=0.01, attack=0.0004))
        mix_into(out, pan_mono(c, rng.uniform(-0.7, 0.7)), n_of(rng.uniform(0, 0.045)), rng.uniform(0.2, 0.5))
    th = _sum(_thump(_N(0.12), 240, 150, 0.006, 0.04), _burst(_N(0.06), rng, 200, 2600, t60=0.02, attack=0.0005))
    mix_into(out, to_stereo(th), n_of(0.045), 1.0)
    mix_into(out, to_stereo(_thump(_N(0.5), 85, 42, 0.02, 0.22)), n_of(0.045), 0.9)
    return out


@_sfx("heart_pulse", space=0.0)
def _heart_pulse(dur, p, rng):
    """The lit windows pulsing twice like a heartbeat: two soft low thumps (lub, dub), with a
    little upper harmonic so phones hear them. gap s."""
    gap = float(p.get("gap", 0.3))
    n = _N(gap + 0.7)
    out = np.zeros(n)
    for t0, g in ((0.0, 1.0), (gap, 0.75)):
        _place(out, _sum(_thump(_N(0.4), 72, 44, 0.03, 0.2), 0.35 * _burst(_N(0.1), rng, hi=150, t60=0.05, attack=0.004)), t0, g)
    out = sos(out, "lowpass", 220, 2)
    out += 0.2 * sos(saturate(out * 3, 2.0), "bandpass", (90, 420), 2)
    return out


@_sfx("slash_whoosh", space=0.0, hit=True)
def _slash_whoosh(dur, p, rng):
    """The slash cut: a steel 'shing' as the red sliver cuts the frame diagonally (first 0.15 s),
    a dry crack as the cut opens, then the two paper halves sliding apart (paper grain + air),
    the whole thing travelling top-left to bottom-right."""
    n = _N(1.1)
    out = np.zeros((n, 2))
    m = _N(0.6)
    tm = t_axis(m)
    f = 2300 * (1 + 0.25 * (1 - np.exp(-tm / 0.05)))
    sh = dsp.fm_op(f, m, ratio=1.414, index=3.0, mod_env=np.exp(-tm / 0.15)) * np.power(10.0, -3 * tm / 0.5)
    sh += 0.5 * tv_bandpass(white(m, rng), 3000 + 6000 * np.clip(tm / 0.12, 0, 1), q=2.0, block=32) * np.exp(-tm / 0.08)
    sh[:_N(0.002)] *= np.linspace(0, 1, _N(0.002))
    mix_into(out, _pan_sweep(sh, -0.8, 0.8, np.clip(tm / 0.15, 0, 1)), 0, 0.6)
    crack = _sum(_burst(_N(0.03), rng, 800, 9000, t60=0.01, attack=0.0002), 0.5 * _thump(_N(0.1), 180, 90, 0.008, 0.04))
    mix_into(out, to_stereo(crack), n_of(0.15), 0.7)
    for pan0, pan1 in ((-0.1, -0.8), (0.1, 0.8)):
        L = 0.45
        k = _N(L + 0.05)
        tk = t_axis(k)
        uk = np.clip(tk / L, 0, 1)
        g = bandpass(crackle(k, 2200, rng, amp_spread=0.8), 900, 6000, 2) * 1.2 + 0.4 * tv_bandpass(pink(k, rng), 500 + 2000 * uk, q=0.8, block=64)
        g *= np.sin(np.pi * uk) ** 1.2
        mix_into(out, _pan_sweep(g, pan0, pan1, uk), n_of(0.3), 0.5)
    m = _N(0.7)
    tm = t_axis(m)
    air = tv_bandpass(pink(m, rng), 300 + 1500 * np.clip(tm / 0.2, 0, 1), q=0.8, block=64) * _bell(tm, 0.18, 0.08, 0.2)
    mix_into(out, _pan_sweep(air, -0.6, 0.6), 0, 0.6)
    return fade(out, 0.0, 0.2)


@_sfx("iris_close", space=0.0)
def _iris_close(dur, p, rng):
    """An iris closing (the binocular mask; rect=1: window 9's rectangle opening like a box lid):
    a soft closing whoosh whose band falls, the leaves meeting with a tiny tick (or a dull
    wooden thock for the rect)."""
    rect = bool(p.get("rect", 0))
    n = _N(1.0)
    t = t_axis(n)
    L = 0.7
    u = np.clip(t / L, 0, 1)
    x = tv_bandpass(pink(n, rng), (1800 * (1 - u) + 380 * u) if not rect else (400 + 1400 * u), q=0.9, block=64)
    x *= np.sin(np.pi * u) ** 1.5 * (t < L)
    x += 0.4 * sos(pink(n, rng), "lowpass", 300, 2) * np.sin(np.pi * u) ** 2 * (t < L)
    if rect:
        _place(x, _sum(_thump(_N(0.15), 160, 95, 0.01, 0.06), _burst(_N(0.05), rng, 120, 1500, t60=0.02, attack=0.001)), L * 0.95, 0.9)
    else:
        _place(x, _hit(rng, [3200, 5100], [0.02, 0.015], click=0.6, n=_N(0.04)), L * 0.97, 0.3)
    return _wide(x, rng, 0.3)


@_sfx("bars_wipe", space=0.0)
def _bars_wipe(dur, p, rng):
    """Two horizontal panels sliding in from opposite sides (the split screen): two card slides,
    the top one from the left, the bottom one from the right (t2 s later), each sliding for
    length s and ending in a thock."""
    L = float(p.get("length", 0.5))
    t2 = float(p.get("t2", 0.18))
    n = _N(t2 + L + 0.6)
    out = np.zeros((n, 2))
    for k, (t0, pan0, pan1) in enumerate(((0.0, -0.8, 0.0), (t2, 0.8, 0.0))):
        m = _N(L + 0.1)
        tm = t_axis(m)
        um = np.clip(tm / L, 0, 1)
        sp = np.sin(np.pi * um) ** 0.8 * (tm < L)
        g = bandpass(crackle(m, 2400, rng, amp_spread=0.8), 900, 6000, 2) * 1.3 + 0.35 * bandpass(pink(m, rng), 250, 1200, 2)
        g *= sp
        _place(g, _sum(_thump(_N(0.1), 200 - 30 * k, 130, 0.008, 0.035), _burst(_N(0.04), rng, 200, 2200, t60=0.015, attack=0.0006)), L, 1.4)
        mix_into(out, _pan_sweep(g, pan0, pan1, np.clip(t_axis(len(g)) / L, 0, 1)), n_of(t0), 1.0)
    return out


@_sfx("tear_big", space=0.0, hit=True)
def _tear_big(dur, p, rng):
    """The paper-tear transition: a long rip travelling down a big sheet of card - fibre breaks
    accelerating then slowing, a fibrous low layer, the shared paper_tear on top - and the torn
    half flapping away."""
    L = float(p.get("length", 0.85))
    n = _N(L + 0.5)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    rate = (900 + 2800 * np.sin(np.pi * u) ** 0.7) * (t < L)
    fib = bandpass(_imp_train(rate, n, rng, 0.7), 450, 5500, 2) * 1.3
    low = bandpass(white(n, rng), 150, 750, 2) * 0.4 * np.sin(np.pi * u) * (t < L)
    out = to_stereo((fib + low) * np.clip(t / 0.02, 0, 1))
    top = lib.render("paper_tear", params=dict(size=1.0), seed=int(rng.integers(1 << 30))).astype(np.float64)
    mix_into(out, top, n_of(max(0.0, L - len(top) / SR * 0.9)), 0.03)
    m = _N(0.45)
    tm = t_axis(m)
    flap = bandpass(white(m, rng), 200, 2500, 2) * _flutter(m, 12, rng, 0.6) * np.sin(np.pi * np.clip(tm / 0.4, 0, 1)) ** 1.5
    mix_into(out, _pan_sweep(flap, 0.0, 0.7), n_of(L), 0.5)
    return _pan_sweep(dsp.mono(out), -0.4, 0.4, np.clip(t_axis(len(out)) / L, 0, 1))


# ============================================================================ voices (far, muffled)
# Formant targets (F1, F2, F3 Hz) for the babble: never words, only the shape of speech.
_VOWELS = dict(a=(800, 1250, 2500), e=(500, 1850, 2600), i=(330, 2250, 2950), o=(520, 900, 2450),
               u=(360, 820, 2300), ax=(560, 1450, 2500), ae=(700, 1650, 2550))


def _voice(f0, F, A, n, rng, bw=(90.0, 120.0, 170.0), breath=0.12, tilt=1.1, fmax=6500.0, amps=(1.0, 0.7, 0.35)):
    """Additive voice: harmonics of f0 (Hz per sample, with jitter and shimmer) under a three-
    formant envelope F (3, n) (Hz per sample) and a glottal roll-off k^-tilt, plus aspiration
    noise through the same formants (breath); A: amplitude per sample. Mono, peak 1."""
    f0 = np.broadcast_to(np.asarray(f0, dtype=np.float64), (n,)) * (1.0 + 0.005 * smooth_noise(n, 25.0, rng))
    ph = np.cumsum(f0) / SR
    F = np.asarray(F, dtype=np.float64)
    out = np.zeros(n)
    K = int(fmax / max(60.0, float(np.min(f0))))
    for k in range(1, K + 1):
        fk = k * f0
        g = np.zeros(n)
        for j in range(3):
            g += amps[j] / (1.0 + ((fk - F[j]) / bw[j]) ** 2)
        g *= k ** (-tilt) * (fk < fmax)
        out += g * np.sin(TWO_PI * k * ph + rng.uniform(0, TWO_PI))
    out /= np.max(np.abs(out)) + 1e-9
    if breath > 0:
        nz = white(n, rng)
        asp = np.zeros(n)
        for j in range(3):
            asp += amps[j] * tv_bandpass(nz, np.clip(F[j], 80, 9000), q=4.0, block=64)
        asp /= np.max(np.abs(asp)) + 1e-9
        out = out + breath * asp
    out *= np.asarray(A, dtype=np.float64) * (1.0 + 0.06 * smooth_noise(n, 18.0, rng))
    return out / (np.max(np.abs(out)) + 1e-9)


def _glass(x, lp=1100.0, hp=140.0):
    """A closed window between us and a voice: the top gone, the bottom thin."""
    y = sos(x, "lowpass", lp, 4)
    return sos(y, "highpass", hp, 2)


@_sfx("chatter", kind="sustained", norm="int", default_dur=1.8, space=0.0)
def _chatter(dur, p, rng):
    """The old woman in window 12 chatting to her cat, through her glass and across the street:
    one voice (additive, about 205 Hz, a little tremulous), syllables at about five a second in
    little words, an accent here and there, a question rising at the end - never a word you
    could make out. dist 0..1."""
    n = _N(dur)
    t = t_axis(n)
    F = np.tile(np.array(_VOWELS["ax"], dtype=np.float64)[:, None], (1, n))
    A = np.zeros(n)
    acc = np.zeros(n)
    tt = 0.06
    while tt < dur - 0.18:
        for k in range(int(rng.integers(1, 4))):
            L = rng.uniform(0.11, 0.2)
            i0, i1 = n_of(tt), min(n, n_of(tt + L))
            if i1 - i0 > 8:
                w = np.sin(np.pi * np.linspace(0, 1, i1 - i0)) ** 0.6
                strong = rng.uniform() < 0.3
                A[i0:i1] = np.maximum(A[i0:i1], w * (1.0 if strong else rng.uniform(0.55, 0.8)))
                F[:, i0:i1] = np.array(_VOWELS[str(rng.choice(list(_VOWELS)))], dtype=np.float64)[:, None]
                if strong:
                    acc[i0:i1] = np.maximum(acc[i0:i1], w)
            tt += L + rng.uniform(0.0, 0.03)
        tt += rng.uniform(0.07, 0.2)
    F = np.stack([onepole_lp(F[j], 22.0) for j in range(3)])
    A = onepole_lp(A, 45.0)
    u = t / dur
    f0 = 228.0 - 40.0 * u + 30.0 * np.clip((u - 0.82) / 0.18, 0, 1) ** 1.5      # declining, a question at the end
    f0 = f0 * (1.0 + 0.12 * onepole_lp(acc, 12.0)) * (1.0 + 0.02 * np.sin(TWO_PI * 5.6 * t))
    x = _voice(f0, F, A, n, rng, breath=0.18, tilt=1.15)
    x = reverb(_glass(x, 1150.0, 150.0), "her_room", wet_db=-9.0)[:n]
    return _distance(x, float(p.get("dist", 0.75)), rng)


@_sfx("cat_meow", space=0.0)
def _cat_meow(dur, p, rng):
    """The cat on window 12's sill answering her, behind the glass across the street: 'mi-aow' -
    a voiced cry rising 520 -> 760 Hz and falling to 470, the mouth opening from a nasal 'm' to a
    bright 'e-a' and rounding to 'ow'. length s, dist 0..1."""
    L = float(p.get("length", 0.62))
    n = _N(L + 0.05)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    k = rng.uniform(0.93, 1.07)
    f0 = np.interp(u, [0, 0.12, 0.35, 0.7, 1.0], [520, 600, 760, 620, 470]) * k * (1 + 0.012 * np.sin(TWO_PI * 6.5 * t))
    F = np.stack([np.interp(u, [0, 0.12, 0.3, 0.6, 1.0], [350, 700, 950, 750, 600]),
                  np.interp(u, [0, 0.12, 0.3, 0.6, 1.0], [1300, 2000, 1700, 1250, 1000]),
                  np.full(n, 3200.0)])
    A = (np.clip(u / 0.06, 0, 1) ** 1.5 * np.clip((1 - u) / 0.25, 0, 1) ** 1.2 * (t < L)
         * np.interp(u, [0, 0.12, 0.3, 1.0], [0.4, 0.9, 1.0, 0.8]))
    x = _voice(f0, F, A, n, rng, bw=(120.0, 160.0, 250.0), breath=0.08, tilt=0.8, fmax=9000.0)
    x = reverb(_glass(x, 1700.0, 260.0), "her_room", wet_db=-10.0)
    return _distance(x, float(p.get("dist", 0.75)), rng)


@_sfx("sobbing", kind="sustained", norm="int", default_dur=1.6, space=0.0)
def _sobbing(dur, p, rng):
    """The woman crying on the end of her bed (window 30), through her glass across the street:
    shuddering catch-breaths (two to four quick sharp intakes) and a wavering, breathy whimper
    falling away, again. dist 0..1."""
    n = _N(dur)
    out = np.zeros(n)
    tt = rng.uniform(0.0, 0.12)
    while tt < dur - 0.25:
        for k in range(int(rng.integers(2, 5))):
            m = _N(0.075)
            tm = t_axis(m)
            c = tv_bandpass(white(m, rng), 1800.0 + 900.0 * tm / 0.075, q=2.0, block=32) + 0.5 * bandpass(white(m, rng), 400, 1200, 2)
            c *= np.sin(np.pi * tm / 0.075) ** 0.7
            _place(out, c, tt, 0.35 + 0.08 * k)
            tt += rng.uniform(0.085, 0.13)
        L = rng.uniform(0.45, 0.8)
        m = _N(L)
        tm = t_axis(m)
        u = tm / L
        f0 = (335.0 - 75.0 * u) * rng.uniform(0.92, 1.08) * (1 + 0.035 * np.sin(TWO_PI * 7.0 * tm))
        F = np.stack([np.interp(u, [0, 1], [520, 430]), np.interp(u, [0, 1], [1150, 860]), np.full(m, 2600.0)])
        A = np.sin(np.pi * u) ** 0.8 * (1 + 0.3 * np.sin(TWO_PI * 7.0 * tm))
        _place(out, _voice(f0, F, A, m, rng, breath=0.5, tilt=1.4, fmax=5000.0), tt, 0.7)
        tt += L + rng.uniform(0.18, 0.4)
    x = reverb(_glass(out, 1300.0, 180.0), "her_room", wet_db=-9.0)[:n]
    return _distance(x, float(p.get("dist", 0.8)), rng)


def _breath_unit(kind, L, rng, nasal=True, trem=0.0, catches=0):
    """One breath: noise through nose / mouth resonances under its envelope. kind 'in' | 'out'.
    trem: tremor depth (6-9 Hz); catches: stutters in an intake."""
    n = _N(L + 0.05)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    src = white(n, rng)
    if nasal:
        fs, qs, gs = [620, 1250, 2500, 3600], [4, 6, 9, 11], [1.0, 0.5, 0.25, 0.12]
    else:
        fs, qs, gs = ([680, 1180, 2550, 3450], [6, 8, 10, 12], [1.0, 0.6, 0.32, 0.18]) if kind == "out" else \
            ([420, 1900, 2700, 3600], [5, 9, 11, 12], [0.8, 0.7, 0.4, 0.25])
    v = dsp.resonator_bank(src, fs, qs, gs) + (0.05 if nasal else 0.12) * bandpass(src, 1200, 4500, 2)
    if kind == "in":
        env = np.clip(u / 0.25, 0, 1) ** 1.2 * np.clip((1 - u) / 0.12, 0, 1)
    else:
        env = np.clip(u / 0.1, 0, 1) ** 0.8 * (1 - u) ** 1.6
    if trem > 0:
        env = env * (1 + trem * np.sin(TWO_PI * np.cumsum(7.0 + 1.5 * smooth_noise(n, 2.0, rng)) / SR))
    if catches:
        gate = np.ones(n)
        for k in range(catches):
            a = (k + 1) / (catches + 1)
            gate *= 1 - 0.85 * np.exp(-0.5 * ((u - a) / 0.035) ** 2)
        env = env * gate
    return sos(v * env * (t < L), "lowpass", 2600 if nasal else 5200, 4)


@_sfx("breathing", kind="sustained", norm="int", default_dur=3.0, space=0.6)
def _breathing(dur, p, rng):
    """Her breathing, close. mode 'calm' (slow nose breaths: in ~1.4 s, out ~2 s), 'held' (tiny,
    shallow, uneven nose breaths she is trying to stifle), 'shaky' (after the trap: shuddering
    intakes, long trembling exhales through the mouth). The first breath starts at `phase`
    ('in' | 'out')."""
    mode = p.get("mode", "calm")
    n = _N(dur)
    out = np.zeros(n)
    tt = float(p.get("start", 0.0))
    nxt = p.get("phase", "in")
    while tt < dur - 0.1:
        if mode == "calm":
            L = rng.uniform(1.2, 1.5) if nxt == "in" else rng.uniform(1.7, 2.2)
            x = _breath_unit(nxt, L, rng, nasal=True) * (0.8 if nxt == "in" else 0.6)
            gap = rng.uniform(0.05, 0.15) if nxt == "in" else rng.uniform(0.4, 0.8)
        elif mode == "held":
            L = rng.uniform(0.25, 0.4) if nxt == "in" else rng.uniform(0.3, 0.5)
            x = _breath_unit(nxt, L, rng, nasal=True) * rng.uniform(0.4, 0.7)
            gap = rng.uniform(0.02, 0.08) if nxt == "in" else rng.uniform(0.5, 1.1)
        else:
            L = rng.uniform(0.45, 0.65) if nxt == "in" else rng.uniform(0.9, 1.3)
            x = _breath_unit(nxt, L, rng, nasal=False, trem=0.45 if nxt == "out" else 0.25,
                             catches=int(rng.integers(2, 4)) if nxt == "in" else 0)
            gap = rng.uniform(0.0, 0.06) if nxt == "in" else rng.uniform(0.15, 0.35)
        _place(out, x, tt)
        tt += L + gap
        nxt = "out" if nxt == "in" else "in"
    return fade(out, 0.05, 0.1)


@_sfx("breath_catch", space=0.6)
def _breath_catch(dur, p, rng):
    """Her breath catching on the first blow: a sharp, short mouth intake with a glottal hitch."""
    x = _breath_unit("in", float(p.get("length", 0.2)), rng, nasal=False)
    _place(x, _hit(rng, [480, 1300], [0.01, 0.008], click=0.3, n=_N(0.02)), 0.0, 0.25)
    return x


@_sfx("grunt", space=0.6)
def _grunt(dur, p, rng):
    """A man's short effort grunt (the cop raising his torch): a glottal catch, a voiced 'hn'
    falling 125 -> 95 Hz through a half-closed mouth, a puff of breath. dist 0..1."""
    L = 0.3
    n = _N(L + 0.1)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    f0 = (125.0 - 30.0 * u) * rng.uniform(0.94, 1.06)
    F = np.stack([np.full(n, 430.0), np.full(n, 1250.0), np.full(n, 2450.0)])
    A = np.clip(t / 0.015, 0, 1) * (1 - u) ** 1.5 * (t < L)
    x = _voice(f0, F, A, n, rng, bw=(110.0, 140.0, 200.0), breath=0.35, tilt=1.3, fmax=4500.0)
    m = _N(0.03)
    _place(x, bandpass(white(m, rng), 300, 2000, 2) * exp_env(m, 0.015), 0.0, 0.3)
    return _distance(x, float(p.get("dist", 0.0)), rng)


# ============================================================================ the window people & the camera
@_sfx("music_box", kind="sustained", norm="int", default_dur=3.0, space=0.0)
def _music_box(dur, p, rng):
    """The dancer's music box in window 4 (behind her glass, across the street): the little waltz
    on a steel comb - tines with a bright pin pluck, the cantilever's high partial and a warm
    fundamental - the cylinder's soft whirr under it. dist 0..1."""
    beat = 60.0 / 176.0
    n = _N(dur)
    out = np.zeros(n)
    melody = [(88, 3), (91, 2), (89, 1), (88, 3), (86, 2), (84, 1), (86, 3), (89, 2), (88, 1), (86, 6),
              (88, 3), (91, 2), (89, 1), (88, 3), (93, 2), (91, 1), (89, 3), (88, 2), (86, 1), (84, 6)]
    bass = [72, 67, 67, 72, 72, 69, 67, 72]
    tt = -float(p.get("offset", 0.0))                    # where in the tune we come in
    beats_done = 0
    notes = []
    for midi, beats in melody * 2:
        if tt >= dur:
            break
        notes.append((tt, midi, 1.0))
        for b in range(beats):
            bt = tt + b * beat
            pos = (beats_done + b) % 3
            root = bass[((beats_done + b) // 3) % len(bass)]
            if pos == 0:
                notes.append((bt, root, 0.55))
            else:
                notes.append((bt, root + (7 if pos == 1 else 12), 0.3))
        tt += beats * beat
        beats_done += beats
    for tt, mm, a in notes:
        if tt < -1.6:
            continue
        f = float(_hz(mm)) * rng.uniform(0.998, 1.002)
        m = _N(1.6)
        tm = t_axis(m)
        note = np.sin(TWO_PI * f * tm) * np.power(10.0, -3 * tm / 1.4) + 0.35 * np.sin(TWO_PI * 2.0 * f * tm) * np.power(10.0, -3 * tm / 0.5)
        if 6.27 * f < 18000:
            note += 0.25 * np.sin(TWO_PI * 6.27 * f * tm) * np.power(10.0, -3 * tm / 0.08)
        note[:_N(0.0015)] *= np.linspace(0, 1, _N(0.0015))
        pin = _hit(rng, [f * 3.1, f * 4.7], [0.006, 0.004], click=0.6, n=_N(0.015))
        note[:len(pin)] += 0.12 * pin
        mix_into(out, note, n_of(tt), a * rng.uniform(0.85, 1.0))
    t = t_axis(n)
    whirr = bandpass(white(n, rng), 250, 900, 2) * (0.6 + 0.4 * np.sin(TWO_PI * 13.0 * t)) * 0.03
    out = dsp.pad_to(out, n) + whirr
    out = reverb(_glass(out, 3600.0, 300.0), "her_room", wet_db=-8.0)[:n]
    y, extra = _distance(out, float(p.get("dist", 0.8)), rng)
    return fade(y, 0.25, 0.4), extra


@_sfx("swish", space=0.6)
def _swish(dur, p, rng):
    """A short swish of cloth or air - a skirt in a pirouette, a cat's tail, a coat whipped round,
    a match shaken out: band-passed noise under a bell, its centre gliding f0 -> f1; flutter
    (Hz, 0 = smooth air) for cloth; weight 0..1 adds the low body of a heavy garment. length s,
    peak (0..1 of length), dist 0..1."""
    L = float(p.get("length", 0.3))
    n = _N(L + 0.08)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    f0, f1 = float(p.get("f0", 700.0)), float(p.get("f1", 2200.0))
    pk = float(p.get("peak", 0.5))
    env = _bell(u, pk, pk / 2.2, (1 - pk) / 2.2) * (t < L)
    x = tv_bandpass(white(n, rng), f0 * (f1 / f0) ** u, q=float(p.get("q", 0.9)), block=32)
    fl = float(p.get("flutter", 0.0))
    if fl > 0:
        x = x * _flutter(n, fl * (0.8 + 0.4 * env), rng, 0.5)
    w = float(p.get("weight", 0.2))
    x = x + w * 1.5 * sos(pink(n, rng), "lowpass", 420, 2)
    return _distance(x * env, float(p.get("dist", 0.0)), rng)


@_sfx("pull_whoosh", kind="sustained", norm="max", default_dur=1.9, space=0.0)
def _pull_whoosh(dur, p, rng):
    """The camera pulled back across the street through the rain: a long low air movement
    swelling and leaving, the rain's hiss rising with it, drops streaking past close (glassy
    ticks flicking left and right)."""
    n = _N(dur)
    t = t_axis(n)
    u = np.clip(t / dur, 0, 1)
    sw = _bell(u, 0.45, 0.22, 0.3)
    out = np.zeros((n, 2))
    for ch in range(2):
        air = tv_bandpass(pink(n, rng), 160 + 500 * sw, q=0.7, block=128) * 1.3 + sos(dsp.brown(n, rng), "lowpass", 140, 2)
        hiss = bandpass(pink(n, rng), 1800, 9000, 2) * 0.35
        out[:, ch] = (air + hiss) * sw
    for tt in np.sort(rng.uniform(0.1, dur - 0.1, int(dur * 16))):
        d = _drop(rng, rng.uniform(1800, 4200), rng.uniform(0.003, 0.006), 0.3) * sw[min(n - 1, n_of(tt))]
        mix_into(out, pan_mono(d, rng.uniform(-0.9, 0.9)), n_of(tt), rng.uniform(0.05, 0.16))
    return fade(out, 0.2, 0.4)


@_sfx("pane_through", space=0.0)
def _pane_through(dur, p, rng):
    """The camera passing through a pane of her window. dir 'in' (from the rain into the room: the
    hiss sucked down to a dull hush with a soft pressure 'whump', a few drops tapping the glass
    right at us) or 'out' (from the room into the night: a wet rush opening up, a gust)."""
    d = p.get("dir", "in")
    n = _N(0.9)
    t = t_axis(n)
    out = np.zeros(n)
    if d == "in":
        e = np.exp(-np.maximum(t - 0.05, 0) / 0.12) * np.clip(t / 0.05, 0, 1)
        out += tv_bandpass(pink(n, rng), 3000 * np.exp(-t / 0.08) + 300, q=0.8, block=64) * e * 0.8
        _place(out, _thump(_N(0.2), 90, 55, 0.01, 0.09), 0.05, 0.6)
        for k in range(4):
            f = rng.uniform(2400, 4800)
            _place(out, _hit(rng, [f, f * 1.47], [0.02, 0.014], click=0.5, n=_N(0.04)), 0.12 + 0.11 * k + rng.uniform(0, 0.05), rng.uniform(0.12, 0.25))
    else:
        u = np.clip(t / 0.5, 0, 1)
        e = u ** 1.6 * np.exp(-np.maximum(t - 0.5, 0) / 0.15)
        out += tv_bandpass(pink(n, rng), 400 * 12.0 ** u, q=0.7, block=64) * e
        out += bandpass(white(n, rng), 2500, 9000, 2) * e * 0.4
        out += sos(pink(n, rng), "lowpass", 300, 2) * e * 0.6
    return _wide(out, rng, 0.4)


@_sfx("focus_click", space=0.0)
def _focus_click(dur, p, rng):
    """The binoculars' knurled focus wheel turned a notch: two or three tiny detent ticks and a
    rub of the thumb."""
    n = _N(0.25)
    out = np.zeros(n)
    m = _N(0.1)
    _place(out, bandpass(white(m, rng), 1500, 6000, 2) * np.hanning(m) * 0.05, 0.0)
    for k in range(int(rng.integers(2, 4))):
        f = rng.uniform(3600, 5200)
        _place(out, _hit(rng, [f, f * 1.6], [0.006, 0.004], click=0.7, n=_N(0.015)), 0.02 + 0.032 * k + rng.uniform(0, 0.006), 1.0 - 0.2 * k)
    return out


@_sfx("stab_thud", space=0.0)
def _stab_thud(dur, p, rng):
    """A knife blow on the far side of the street, through two panes: a muffled body thud (a
    dull low thump and the flat slap of cloth), the street's air on it. dist 0..1."""
    n = _N(0.5)
    out = np.zeros(n)
    _place(out, _thump(_N(0.3), 105, 55, 0.008, 0.11), 0.0, 1.0)
    _place(out, _burst(_N(0.06), rng, 120, 900, t60=0.03, attack=0.001), 0.0, 0.7)
    out = sos(out, "lowpass", 700, 2)
    return _distance(out, float(p.get("dist", 0.7)), rng)


# ============================================================================ rooms, doors, lamps
@_sfx("board_creak", space=0.9)
def _board_creak(dur, p, rng):
    """A bare floorboard creaking under a shifted weight (no step): a slow stick-slip groan
    through the board's modes. length s, pitch, dist 0..1."""
    L = float(p.get("length", 0.35))
    n = _N(L + 0.1)
    t = t_axis(n)
    sw = np.sin(np.pi * np.clip(t / L, 0, 1)) ** 0.8 * (t < L)
    k = float(p.get("pitch", 1.0)) * rng.uniform(0.85, 1.15)
    cr = friction(n, (40 + 65 * sw) * k, rng, jitter=0.3,
                  body=[(rng.uniform(240, 340) * k, 6, 1.0), (rng.uniform(600, 800) * k, 8, 0.7), (rng.uniform(1300, 1700) * k, 10, 0.35)])
    return _distance(cr * sw, float(p.get("dist", 0.0)), rng)


@_sfx("hook_creak", space=0.8)
def _hook_creak(dur, p, rng):
    """Her hand closing on the coat's collar on its cast-iron hook: a fistful of wool, the hook
    creaking in its screws as the coat's weight shifts."""
    n = _N(0.55)
    out = np.zeros(n)
    m = _N(0.18)
    w = np.sin(np.pi * np.linspace(0, 1, m)) ** 1.2
    _place(out, (bandpass(crackle(m, 650, rng), 700, 4500, 2) * 0.9 + bandpass(pink(m, rng), 200, 1400, 2) * 0.3) * w, 0.0, 1.0)
    m = _N(0.32)
    tm = t_axis(m)
    sq = friction(m, 90 + 70 * tm / 0.32, rng, jitter=0.25, body=[(1450, 12, 1.0), (2650, 16, 0.6), (820, 6, 0.4)])
    _place(out, sq * np.sin(np.pi * tm / 0.32) ** 0.9, 0.12, 0.7)
    return out


@_sfx("body_hit", space=0.5, hit=True)
def _body_hit(dur, p, rng):
    """His whole weight thrown into the locked door from inside, right at us: a deep shoulder
    thump through the panel (lower and longer than a fist), the bolt and the frame jarring."""
    n = _N(1.0)
    out = np.zeros(n)
    _place(out, _thump(_N(0.5), 95, 44, 0.02, 0.24), 0.0, 1.0)
    _place(out, _door_panel(rng, _N(0.8), 0.92), 0.0, 0.85)
    _place(out, _burst(_N(0.1), rng, 50, 1100, t60=0.05, attack=0.001), 0.0, 1.0)
    for j in range(5):
        _place(out, _hit(rng, [rng.uniform(900, 1900), rng.uniform(2200, 4200)], [0.04, 0.03], click=0.5, n=_N(0.06)),
               0.01 + 0.022 * j + rng.uniform(0, 0.01), 0.22)
    out = reverb(out, "hallway", wet_db=-10.0)[:n]
    return fade(out, 0.0, 0.2)


@_sfx("heel_pivot", space=0.8)
def _heel_pivot(dur, p, rng):
    """She whips round on bare boards: a heel twisting on the wood (a short leather squeak), the
    knock of the heel as the weight lands, the coat swinging after her."""
    n = _N(0.5)
    out = np.zeros(n)
    m = _N(0.11)
    tm = t_axis(m)
    _place(out, friction(m, 380 + 300 * tm / 0.11, rng, jitter=0.12, body=[(1900, 14, 1.0), (3100, 18, 0.5)]) * np.sin(np.pi * tm / 0.11), 0.0, 0.5)
    _place(out, _hit(rng, np.array([1650, 2900, 4400]) * rng.uniform(0.95, 1.05), [0.025, 0.02, 0.014], click=1.0), 0.1, 0.8)
    _place(out, _burst(_N(0.05), rng, 200, 2500, t60=0.02, attack=0.001), 0.1, 0.4)
    m = _N(0.3)
    tm = t_axis(m)
    sw = bandpass(white(m, rng), 300, 2400, 2) * _flutter(m, 14, rng, 0.5) * np.sin(np.pi * tm / 0.3) ** 1.5
    _place(out, sw, 0.06, 0.35)
    return out


@_sfx("lamp_lift", space=0.8)
def _lamp_lift(dur, p, rng):
    """She grabs the show lamp and lifts it: the tripod's steel feet scraping off the boards, the
    stand's joints knocking, the cord dragging, and the hot bulb's filament ringing - a thin
    metallic shimmer that wavers as it swings."""
    n = _N(1.0)
    t = t_axis(n)
    out = np.zeros(n)
    for k in range(3):
        m = _N(rng.uniform(0.1, 0.18))
        tm = t_axis(m)
        sc = friction(m, rng.uniform(160, 260), rng, jitter=0.35, body=[(rng.uniform(1800, 2600), 9, 1.0), (rng.uniform(3800, 5200), 12, 0.5)])
        _place(out, sc * np.sin(np.pi * tm / (m / SR)) ** 1.2, 0.03 + 0.04 * k + rng.uniform(0, 0.02), 0.45)
    _place(out, _hit(rng, np.array([700, 1650, 2900]) * rng.uniform(0.95, 1.05), [0.06, 0.04, 0.03], click=0.6, n=_N(0.1)), 0.02, 0.5)
    fil = np.zeros(n)
    for f, a, t60 in ((5320, 1.0, 0.7), (7810, 0.5, 0.5), (10260, 0.25, 0.35)):
        ff = f * rng.uniform(0.97, 1.03) * (1 + 0.004 * np.sin(TWO_PI * 5.5 * t))
        fil += a * np.sin(TWO_PI * np.cumsum(ff) / SR + rng.uniform(0, 6)) * np.power(10.0, -3 * t / t60)
    fil *= 1 + 0.5 * np.sin(TWO_PI * 3.3 * t)
    _place(out, fil, 0.05, 0.08)
    m = _N(0.6)
    _place(out, friction(m, 60, rng, jitter=0.5, body=[(800, 3, 1.0), (1800, 4, 0.4)]) * np.hanning(m), 0.15, 0.25)
    return out


@_sfx("pins_rasp", space=0.8)
def _pins_rasp(dur, p, rng):
    """The sheet pulled across on its wire: the wooden clothes pins and their springs rasping and
    knocking along the steel wire (a scraping run with little catches), the wire singing faintly,
    the sheet's cloth swishing over the lamp. length s."""
    L = float(p.get("length", 1.15))
    n = _N(L + 0.3)
    t = t_axis(n)
    u = np.clip(t / L, 0, 1)
    mot = np.sin(np.pi * u) ** 0.6 * (t < L)
    out = np.zeros(n)
    for k in range(int(rng.integers(5, 8))):
        a = rng.uniform(0.0, L * 0.3)
        m = _N(L - a)
        tm = t_axis(m)
        sc = friction(m, rng.uniform(70, 130) * (1 + 0.3 * smooth_noise(m, 3, rng)), rng, jitter=0.4,
                      body=[(rng.uniform(1100, 1600), 8, 1.0), (rng.uniform(2400, 3300), 10, 0.6), (rng.uniform(4300, 5600), 14, 0.3)])
        _place(out, sc * np.sin(np.pi * np.clip(tm / (m / SR), 0, 1)) ** 0.7, a, rng.uniform(0.12, 0.22))
    for k in range(int(rng.integers(6, 11))):
        _place(out, _hit(rng, np.array([1300, 2600, 4100]) * rng.uniform(0.85, 1.2), [0.03, 0.02, 0.015], click=0.7, n=_N(0.05)),
               rng.uniform(0.05, L), rng.uniform(0.15, 0.35))
    wire = sum(a * np.sin(TWO_PI * f * rng.uniform(0.98, 1.02) * t + rng.uniform(0, 6)) for f, a in ((610, 1.0), (1225, 0.5), (1850, 0.25)))
    out += wire * mot * 0.03
    out += tv_bandpass(pink(n, rng), 500 + 1300 * mot, q=0.7, block=64) * mot * 0.35
    return _pan_sweep(out, float(p.get("pan0", 0.35)), float(p.get("pan1", -0.25)), u)


@_sfx("wall_bump", space=0.8)
def _wall_bump(dur, p, rng):
    """Her back meeting the plaster wall: a soft, low body thud, the coat's wool crushed against
    it, a grain of plaster ticking."""
    n = _N(0.5)
    out = np.zeros(n)
    _place(out, _thump(_N(0.25), 115, 62, 0.012, 0.09), 0.0, 1.0)
    _place(out, _burst(_N(0.06), rng, 120, 1300, t60=0.03, attack=0.002), 0.0, 0.6)
    m = _N(0.25)
    _place(out, bandpass(crackle(m, 700, rng), 600, 4000, 2) * np.sin(np.pi * np.linspace(0, 1, m)) * 0.5, 0.01, 1.0)
    _place(out, _hit(rng, [rng.uniform(3000, 5000)], [0.01], click=0.4, n=_N(0.02)), 0.05 + rng.uniform(0, 0.05), 0.1)
    return out


@_sfx("timer_switch", space=0.6)
def _timer_switch(dur, p, rng):
    """The hallway's push-button timer light: the button pressed home (a heavy bakelite clunk),
    the clockwork catching and starting to whirr, the lamp's contact ticking on."""
    n = _N(0.8)
    t = t_axis(n)
    out = np.zeros(n)
    _place(out, _hit(rng, [900, 2100, 3400], [0.05, 0.035, 0.025], click=0.8), 0.0, 1.0)
    _place(out, _thump(_N(0.08), 220, 150, 0.006, 0.03), 0.0, 0.45)
    m = _N(0.6)
    tm = t_axis(m)
    wr = bandpass(_imp_train(np.full(m, 38.0), m, rng, 0.3, polarity=False), 2000, 6000, 2) * np.exp(-tm / 0.35) * 0.6
    _place(out, wr, 0.03, 0.5)
    _place(out, _hit(rng, [4100, 6300], [0.01, 0.008], click=0.6, n=_N(0.02)), 0.07, 0.3)
    return out


@_sfx("pins_pop", space=0.8, hit=True)
def _pins_pop(dur, p, rng):
    """The torn sheet tearing its pins off the wire one after another: each a sprung wooden pin
    snapping off ('tock') and clattering on the boards, the wire twanging, and the sheet slumping
    down - a heavy cloth fall ending soft on the floor at `slump` s."""
    slump = float(p.get("slump", 0.42))
    n = _N(slump + 0.6)
    t = t_axis(n)
    out = np.zeros(n)
    tt, gap = 0.0, 0.085
    for k in range(int(rng.integers(5, 8))):
        if tt > slump:
            break
        f = rng.uniform(0.85, 1.2)
        _place(out, _hit(rng, np.array([1200, 2500, 3900]) * f, [0.035, 0.025, 0.018], click=1.0, n=_N(0.06)), tt, 0.9 - 0.06 * k)
        _place(out, _hit(rng, np.array([1500, 3100]) * rng.uniform(0.9, 1.1), [0.03, 0.02], click=0.6, n=_N(0.05)),
               tt + rng.uniform(0.12, 0.25), rng.uniform(0.15, 0.3))
        tt += gap * rng.uniform(0.8, 1.2)
        gap *= 0.82
    tw = dsp.karplus_strong(96.0 * rng.uniform(0.95, 1.05), 0.8, t60=0.7, brightness=0.35, rng=rng)
    _place(out, sos(tw[:_N(0.8)], "bandpass", (80, 1800), 2) / (np.max(np.abs(tw)) + 1e-9), 0.01, 0.12)
    e = _bell(t, slump * 0.6, slump * 0.35, 0.08) * (t < slump + 0.05)
    out += (tv_bandpass(pink(n, rng), 900 - 500 * np.clip(t / slump, 0, 1), q=0.7, block=64) * 0.6
            + bandpass(white(n, rng), 300, 2200, 2) * _flutter(n, 11, rng, 0.5) * 0.3) * e
    _place(out, _sum(_thump(_N(0.2), 110, 60, 0.012, 0.08), _burst(_N(0.07), rng, 100, 1200, t60=0.035, attack=0.003)), slump, 0.55)
    return out


@_sfx("electric_fizz", space=0.5)
def _electric_fizz(dur, p, rng):
    """The smashed lamp's filament arcing on the floor: an electric fizz, 120 Hz buzz and crackle
    stuttering on and off, until it stops dead at `length`."""
    L = float(p.get("length", 0.55))
    n = _N(L + 0.02)
    t = t_axis(n)
    gate = np.zeros(n)
    tt = 0.0
    while tt < L:
        on = rng.uniform(0.02, 0.07)
        gate[n_of(tt):min(n, n_of(tt + on))] = rng.uniform(0.5, 1.0)
        tt += on + rng.uniform(0.01, 0.06)
    gate = onepole_lp(gate, 400.0) * (t < L)
    buzz = sos(saturate(np.sin(TWO_PI * 120 * t) + 0.3 * np.sin(TWO_PI * 60 * t), 5.0, asym=0.3), "bandpass", (100, 5000), 2)
    arc = bandpass(crackle(n, 900, rng, amp_spread=1.0), 1500, 9000, 2)
    x = (0.6 * buzz + 0.8 * arc) * gate
    k = _N(0.004)
    x[-k:] *= np.linspace(1, 0, k)
    return x


@_sfx("fuse_click", space=0.3, hit=True)
def _fuse_click(dur, p, rng):
    """The fuse going: a hard, dry 'tock' of the breaker / fuse holder with a tiny electric snap -
    and nothing after it."""
    n = _N(0.12)
    out = np.zeros(n)
    _place(out, _hit(rng, [1150, 2600, 4300, 6900], [0.02, 0.015, 0.01, 0.007], spread=0.02, click=1.0, n=_N(0.06)), 0.0, 1.0)
    _place(out, _thump(_N(0.04), 300, 200, 0.004, 0.012), 0.0, 0.3)
    m = _N(0.012)
    _place(out, sos(saturate(np.sin(TWO_PI * 120 * t_axis(m)), 6.0), "highpass", 2000, 2) * np.linspace(1, 0, m), 0.0, 0.25)
    return out


@_sfx("dolls_rustle", kind="sustained", norm="max", default_dur=1.6, space=0.8)
def _dolls_rustle(dur, p, rng):
    """A draught through the open door running over forty paper dolls pinned to his wall: a wave
    of stiff little card flutters passing left to right, pins ticking here and there."""
    n = _N(dur)
    out = np.zeros((n, 2))
    for k in range(40):
        col = k % 5
        row = k // 5
        x = col / 4.0
        tt = (0.08 + 0.72 * x + 0.03 * row) * (dur / 1.6) + rng.uniform(-0.05, 0.05)
        L = rng.uniform(0.18, 0.35)
        m = _N(L)
        tm = t_axis(m)
        flaps = _imp_train(np.full(m, rng.uniform(16, 26)), m, rng, 0.4, polarity=False)
        f = dsp.resonator_bank(flaps, np.array([900, 1700, 3100]) * rng.uniform(0.85, 1.2), [3, 4, 5], [1.0, 0.7, 0.4])
        f = f + bandpass(crackle(m, 700, rng), 1500, 7000, 2) * 0.4
        f *= np.sin(np.pi * tm / L) ** 1.3
        f /= np.max(np.abs(f)) + 1e-9
        mix_into(out, pan_mono(f, -0.8 + 1.6 * x), n_of(max(0.0, tt)), rng.uniform(0.25, 0.5))
        if rng.uniform() < 0.25:
            mix_into(out, pan_mono(_hit(rng, [rng.uniform(3500, 6500)], [0.02], click=0.5, n=_N(0.03)), -0.8 + 1.6 * x),
                     n_of(max(0.0, tt + rng.uniform(0, L))), 0.08)
    return fade(out, 0.1, 0.3)


@_sfx("flashgun", space=0.5, hit=True)
def _flashgun(dur, p, rng):
    """The press photographer's flashgun: the shutter's 'click-clack' (at 0) and, `pop` s later,
    the flashbulb firing - a bright foil 'pff' with a crack and a low puff - then the flash unit's
    thin whine climbing as it recharges, fading off."""
    pop = float(p.get("pop", 0.0))
    n = _N(pop + 2.0)
    t = t_axis(n)
    out = np.zeros(n)
    _place(out, _hit(rng, [2100, 3700, 5600], [0.012, 0.01, 0.007], click=0.9, n=_N(0.03)), 0.0, 0.5)
    _place(out, _hit(rng, [1700, 2900, 4800], [0.015, 0.012, 0.008], click=0.8, n=_N(0.03)), 0.035, 0.4)
    m = _N(0.09)
    tm = t_axis(m)
    pf = bandpass(white(m, rng), 800, 9000, 2) * np.exp(-tm / 0.025) + bandpass(crackle(m, 4000, rng), 2000, 10000, 2) * np.exp(-tm / 0.03) * 0.6
    _place(out, pf, pop, 1.0)
    _place(out, _thump(_N(0.12), 170, 90, 0.004, 0.05), pop, 0.5)
    _place(out, _click(rng, 3000, 0.002, _N(0.008)), pop, 0.5)
    tw = np.clip((t - pop - 0.05) / 1.8, 0, 1)
    fw = 1800.0 * (4.2 ** tw)
    wh = np.sin(TWO_PI * np.cumsum(fw) / SR) + 0.25 * np.sin(TWO_PI * 2 * np.cumsum(fw) / SR)
    wh *= np.clip((t - pop - 0.05) / 0.2, 0, 1) * np.clip((pop + 1.95 - t) / 0.6, 0, 1) * 0.035
    return out + wh


@_sfx("bulb_eject", space=0.8)
def _bulb_eject(dur, p, rng):
    """The spent flashbulb thumbed out of the reflector: the ejector's click, then the hot little
    glass bulb hitting the floorboards and bouncing - light glassy tinks with a woody knock,
    each lower and closer together - and a short roll."""
    n = _N(1.2)
    out = np.zeros(n)
    _place(out, _hit(rng, [2600, 4300], [0.012, 0.008], click=0.8, n=_N(0.025)), 0.0, 0.45)
    tt, gap, a = 0.22, 0.17, 1.0
    for k in range(5):
        f = rng.uniform(4200, 5600) * (1 - 0.03 * k)
        _place(out, _hit(rng, [f, f * 1.52, f * 2.3], [0.06, 0.04, 0.025], click=0.5, n=_N(0.1)), tt, a)
        _place(out, _hit(rng, [820, 1700], [0.02, 0.015], click=0.3, n=_N(0.04)), tt, 0.3 * a)
        tt += gap * rng.uniform(0.85, 1.1)
        gap *= 0.62
        a *= 0.62
    m = _N(0.3)
    _place(out, friction(m, 110, rng, jitter=0.6, body=[(4300, 18, 1.0), (6600, 20, 0.4)]) * np.hanning(m), tt, 0.06)
    return out


@_sfx("bino_set", space=0.8)
def _bino_set(dur, p, rng):
    """Her binoculars set down on the wooden sill: the rubber armour's dull knock on the wood, a
    tiny metal tick of the strap's buckle, the strap settling."""
    n = _N(0.5)
    out = np.zeros(n)
    _place(out, _sum(_thump(_N(0.12), 260, 180, 0.006, 0.04), _hit(rng, [340, 760, 1300], [0.04, 0.03, 0.02], click=0.3, n=_N(0.08))), 0.0, 1.0)
    _place(out, _thump(_N(0.1), 240, 170, 0.006, 0.03), 0.045 + rng.uniform(0, 0.02), 0.35)
    _place(out, _hit(rng, [4100, 6300], [0.02, 0.015], click=0.5, n=_N(0.03)), 0.09 + rng.uniform(0, 0.04), 0.15)
    m = _N(0.25)
    _place(out, bandpass(crackle(m, 400, rng), 800, 4000, 2) * np.hanning(m) * 0.3, 0.1, 1.0)
    return out


@_sfx("rings_home", space=0.8)
def _rings_home(dur, p, rng):
    """The curtain's brass rings knocking home against the end of the rod: a bunched clatter of
    ring on ring and on the wooden finial, a little ringing after."""
    n = _N(0.7)
    out = np.zeros(n)
    tt = 0.0
    for k in range(int(rng.integers(5, 8))):
        f = rng.uniform(2800, 5200)
        _place(out, _hit(rng, [f, f * 1.43, f * 2.07], [0.12, 0.08, 0.05], click=0.6, n=_N(0.2)), tt, rng.uniform(0.4, 1.0))
        tt += rng.uniform(0.008, 0.025)
    _place(out, _hit(rng, [620, 1350, 2400], [0.04, 0.03, 0.02], click=0.6, n=_N(0.08)), 0.004, 0.5)
    return out


@_sfx("lamp_die", space=0.0)
def _lamp_die(dur, p, rng):
    """The street lamp below going out: its tired buzz dropping and cut, the filament's cooling
    tick. Far (dist 0..1)."""
    n = _N(0.5)
    t = t_axis(n)
    f = 120.0 * (1 - 0.06 * np.clip(t / 0.12, 0, 1))
    b = sos(saturate(np.sin(TWO_PI * np.cumsum(f) / SR), 4.0), "bandpass", (110, 3500), 2)
    b *= np.clip(1 - t / 0.12, 0, 1) ** 1.5
    out = b * 0.5
    _place(out, _hit(rng, [6200, 8900], [0.03, 0.02], click=0.2, n=_N(0.05)), 0.16 + rng.uniform(0, 0.05), 0.15)
    return _distance(out, float(p.get("dist", 0.8)), rng)


@_sfx("glass_tick", space=0.4)
def _glass_tick(dur, p, rng):
    """The faintest glass tick - a hot bulb's glass catching a match flame: one tiny, very high
    glassy ping."""
    n = _N(0.3)
    f = rng.uniform(5200, 6600)
    return _hit(rng, [f, f * 1.38, f * 2.12], [0.12, 0.07, 0.04], click=0.2, n=n)


@_sfx("pull_chain", space=0.0)
def _pull_chain(dur, p, rng):
    """A lamp's pull-chain switch: the little bead chain rattling, the socket's ratchet snapping
    over (the click), the chain swinging back against the brass. dist 0..1."""
    n = _N(0.45)
    out = np.zeros(n)
    for k in range(6):
        _place(out, _hit(rng, [rng.uniform(4500, 7500)], [0.008], click=0.5, n=_N(0.015)), rng.uniform(0.0, 0.05), rng.uniform(0.1, 0.25))
    ts = 0.05
    _place(out, _hit(rng, [2300, 3900, 6100], [0.02, 0.015, 0.01], spread=0.02, click=1.0), ts, 1.0)
    _place(out, _thump(_N(0.04), 400, 260, 0.004, 0.015), ts, 0.3)
    for k in range(4):
        _place(out, _hit(rng, [rng.uniform(5000, 8000)], [0.01], click=0.4, n=_N(0.02)), ts + 0.04 + 0.05 * k + rng.uniform(0, 0.02), 0.12)
    return _distance(out, float(p.get("dist", 0.0)), rng)


@_sfx("beacon_hum", kind="sustained", norm="int", default_dur=5.0, space=0.0)
def _beacon_hum(dur, p, rng):
    """The police car's rotating beacon down in the street, heard through apartment 9's glass:
    the little motor's hum swelling and fading as the lamp turns (about 1.3 turns a second)."""
    n = _N(dur)
    t = t_axis(n)
    f = 180.0 * (1 + 0.004 * smooth_noise(n, 0.5, rng))
    ph = np.cumsum(f) / SR
    x = np.sin(TWO_PI * ph) + 0.5 * np.sin(2 * TWO_PI * ph + 1.0) + 0.3 * np.sin(3 * TWO_PI * ph + 2.0) + 0.15 * np.sin(5 * TWO_PI * ph)
    x *= 0.65 + 0.35 * np.sin(TWO_PI * 1.3 * t) ** 2
    x += 0.15 * bandpass(white(n, rng), 300, 1500, 2)
    return fade(_glass(x, 900.0, 120.0), 0.3, 0.3)


@_sfx("far_radio", kind="sustained", norm="int", default_dur=3.0, space=0.0)
def _far_radio(dur, p, rng):
    """A radio playing high up in a lit window as the camera cranes past: a little dance band
    (muted trumpet line, piano comping, brushes, a walking bass) through a tinny speaker and an
    open window, far."""
    n = _N(dur)
    out = np.zeros(n)
    beat = 60.0 / 128.0
    walk = [45, 48, 52, 55, 57, 55, 52, 48, 50, 53, 57, 60, 52, 55, 59, 62]
    tune = [(69, 1.5), (72, 0.5), (76, 1.0), (74, 1.0), (72, 2.0), (69, 1.0), (67, 1.0), (69, 2.0), (64, 2.0)]
    tt = 0.0
    k = 0
    while tt < dur:
        f = float(_hz(walk[k % len(walk)] + 12))
        _place(out, lib._felt_piano_note(f, _N(beat * 1.1), 0.6, rng) * 0.5, tt)
        if k % 2 == 1:
            m = _N(0.12)
            _place(out, bandpass(white(m, rng), 2500, 7000, 2) * np.hanning(m) * 0.3, tt, 1.0)
            for c in (64, 67, 71):
                _place(out, lib._felt_piano_note(float(_hz(c)), _N(0.25), 0.4, rng) * 0.15, tt)
        tt += beat
        k += 1
    tt = 0.25
    for mm, b in tune * 2:
        if tt >= dur:
            break
        L = b * beat
        m = _N(L + 0.1)
        tm = t_axis(m)
        f = float(_hz(mm)) * (1 + 0.006 * np.sin(TWO_PI * 5.5 * tm) * np.clip(tm / 0.2, 0, 1))
        tr = saw(f, m) * np.clip(tm / 0.03, 0, 1) * np.clip((L - tm) / 0.05, 0, 1)
        _place(out, biquad(tr, "peak", 1800, 2.0, 9.0) * 0.12, tt)
        tt += L
    out = bandpass(out, 380, 2800, 3)
    out = saturate(out / (np.max(np.abs(out)) + 1e-9) * 2.0, 1.8) * 0.5
    out += 0.02 * bandpass(white(n, rng), 800, 4000, 2)
    y, extra = _distance(reverb(out, "small_room", wet_db=-8.0)[:n], float(p.get("dist", 0.9)), rng)
    return fade(y, 0.4, 0.5), extra
