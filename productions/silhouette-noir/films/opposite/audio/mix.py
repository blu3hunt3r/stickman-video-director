"""OPPOSITE: score, sound design and voices, synced to the beat times in
films/opposite/world.py (film time).

    python3 films/opposite/audio/mix.py      -> films/opposite/out/audio_master.wav (48 kHz stereo, -16 LUFS)

Voices and the foley that has to sound real (the quarrel, the screams, her gasp and her breath,
his breath behind the door, the mug, the body, the footsteps, the stairs, the handle) are
generated recordings in audio/gen/ (decoded at load). Footsteps are cut from them one at a time
and placed on the frames a foot comes down in the mocap. The score, the camera's whooshes and
the city stay procedural. It ends on the eye: a stinger, a hard cut to black, one low hit.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from functools import lru_cache

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
GEN = os.path.join(ROOT, "audio", "gen")


@lru_cache(maxsize=None)
def _gen(name):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", os.path.join(GEN, name + ".mp3"), "-f", "f32le",
                          "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def gen(name, a=0.0, b=None, fade=0.01, norm=None):
    """A slice [a, b) s of a generated sound, edges faded; norm scales its peak to norm dBFS."""
    x = _gen(name)
    x = x[n_of(a): (n_of(b) if b is not None else len(x))].copy()
    f = min(n_of(fade), len(x) // 2)
    if f > 0:
        r = np.linspace(0.0, 1.0, f)
        x[:f] *= r
        x[-f:] *= r[::-1]
    if norm is not None:
        x *= db2lin(norm) / (np.max(np.abs(x)) + 1e-9)
    return x


def hits(name, thr_db=-18.0, gap=0.12):
    """Onset times (s) of the separate hits in a generated sound (steps, rattles)."""
    x = _gen(name)
    hop = 240
    env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "same"))[::hop]
    db = 20.0 * np.log10(env + 1e-9)
    top = db.max()
    out, armed = [], True
    for i, v in enumerate(db):
        if armed and v > top + thr_db:
            if not out or i * hop / SR - out[-1] > gap:
                out.append(i * hop / SR)
            armed = False
        if v < top + thr_db - 6.0:
            armed = True
    return out


def step_bank(name, thr_db=-18.0, length=0.3):
    """The single footfalls of a generated sound, each normalised."""
    return [gen(name, max(0.0, o - 0.015), o + length, fade=0.006, norm=-1.0) for o in hits(name, thr_db)]


def glass(x, lp=1500.0, wet_db=-10.0, seed=0):
    """Across the street, behind his window: no top, a little of his room."""
    y = dsp.sos(dsp.sos(mono(x), "lowpass", lp, 4), "highpass", 160.0, 2)
    return dsp.reverb(y, "small_room", wet_db=wet_db, seed=seed).mean(axis=1)


def env_db(x, pts):
    return x * dsp.env_bp_db(pts, len(x))


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
    feet = np.zeros((N, 2), np.float32)

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
    put(amb, siren * dsp.env_bp_db([(0.0, -40), (1.5, 0), (6.0, 0), (8.0, -60)], len(siren))[:, None], Wd.T_CUP + 0.6, -22)
    # a clock under everything from the push into her window; it stops when the handle turns
    tick = fx("clock_ticking", dur=Wd.T_KNOB[0] - 5.4, seed=3, bpm=96)
    tick *= dsp.env_bp_db([(0.0, -40), (1.5, 0), (len(tick) / SR - 0.05, 0), (len(tick) / SR, -80)], len(tick))[:, None]
    put(music, tick, 5.4, -16)
    # the camera: glides, whips, pushes
    for t0, pan, size, g in ((Wd.T_PUSH, 0.0, 0.3, -18), (Wd.T_GLIDE_OUT + 0.3, 0.5, 0.3, -18), (Wd.S(18.0), 0.0, 0.25, -20),
                             (Wd.S(18.85), 0.4, 0.3, -17), (Wd.S(21.65), 0.5, 0.35, -17)):
        put(efx, fx("whoosh", seed=int(t0 * 10), size=size), t0, g, pan=pan)
    for t0, pan in ((Wd.T_GLIDE_BACK + 0.12, -0.5), (Wd.S(20.9), -0.5)):          # whip pans
        put(efx, fx("whip", seed=int(t0 * 10)), t0, -11, pan=pan)
        put(efx, fx("whoosh", seed=int(t0 * 10) + 1, size=0.5), t0 - 0.05, -14, pan=pan)

    # ---------------------------------------------------------------- her: the sip, the walk to the glass
    her_steps = step_bank("her_steps", thr_db=-28.0, length=0.32)
    her_falls = Wd.foot_contacts(lambda t: Wd.her_pose(t)[0], Wd.T_WALK - 0.1, Wd.T_CUP)
    walk = [Wd.T_WALK + 0.18] + [t for t in her_falls if t > Wd.T_WALK + 0.4]
    for j, t in enumerate(walk):
        put(feet, dsp.reverb(her_steps[j % len(her_steps)], "small_room", wet_db=-16.0, seed=j).mean(axis=1),
            t - 0.01, -5 - (2.0 if j == len(walk) - 1 else 0.0), pan=-0.15)
    put(efx, fx("chair_creak", seed=21)[: n_of(0.5)], walk[-1] + 0.35, -28, pan=-0.15)  # a board under her

    # ---------------------------------------------------------------- the quarrel, the knife
    # through his glass from the moment she hears it, getting louder until the knife goes up
    q1, q2 = gen("quarrel", 1.1, 6.0), gen("quarrel", 3.5, 6.0)
    xf = n_of(0.25)
    q = np.concatenate([q1[:-xf], q1[-xf:] * np.linspace(1, 0, xf) + q2[:xf] * np.linspace(0, 1, xf), q2[xf:]])
    q = q[: n_of(Wd.T_RAISE + 0.12 - Wd.T_HEAR)]
    L = len(q) / SR
    q = env_db(glass(q, lp=1700.0, seed=1), [(0.0, -60), (0.15, -9), (Wd.T_GLIDE_OUT - Wd.T_HEAR, -7),
                                            (Wd.T_QUARREL - Wd.T_HEAR, -3), (L - 0.4, 0), (L - 0.03, 0), (L, -60)])
    put_track(vox, q, Wd.T_HEAR, -3, Wd.HIS_C)
    man_falls = Wd.foot_contacts(lambda t: Wd.man_pose(t)[0], Wd.T_QUARREL - 1.2, Wd.T_SLASH)
    vic_falls = Wd.foot_contacts(lambda t: Wd.vic_perf()(t)[0], Wd.T_QUARREL - 1.2, Wd.T_SLASH)
    thuds = step_bank("stairs_up", length=0.25)
    for j, t in enumerate(sorted(man_falls + vic_falls)):
        put(feet, glass(thuds[j % len(thuds)], lp=1200.0, seed=j), t, -21, pan=0.35)
    put(efx, fx("whoosh", seed=31, size=0.5), Wd.T_RAISE - 0.06, -12)          # the crash zoom
    put(efx, knife_ring(1), Wd.T_RAISE + 0.08, -20, pan=-0.15)
    put(music, fx("string_tighten", seed=4)[: n_of(1.6)], Wd.T_RAISE - 0.55, -10)
    t_land = Wd.T_SLASH + 0.54                                                  # her back hits his floor
    sc = gen("scream_a", 0.08, 0.08 + (t_land - 0.05) - (Wd.T_RAISE + 0.08), fade=0.05)
    put(vox, glass(sc, lp=3200.0, wet_db=-9.0, seed=2), Wd.T_RAISE + 0.08, -2, pan=0.12)
    put(music, fx("stinger", seed=6), Wd.T_SLASH, -5)
    put(music, shrieks(seed=1), Wd.T_SLASH - 0.01, -12)
    put(efx, fx("whip", seed=7), Wd.T_SLASH - 0.03, -9, pan=0.3)
    put(efx, glass(gen("body_fall", 0.0, 1.3, fade=0.004), lp=2200.0, wet_db=-8.0, seed=3), t_land - 0.01, -3, pan=0.15)
    ring = fx("tinnitus", dur=2.8, seed=2)
    put(music, ring * dsp.env_bp_db([(0.0, -30), (0.3, 0), (1.2, -6), (2.8, -60)], len(ring))[:, None], Wd.T_SLASH + 0.15, -22)
    put(efx, fx("clock_tick", seed=2), Wd.T_HIS_OFF, -11, pan=0.1)              # his light: off
    put(music, fx("sub_drop", seed=1), Wd.T_HIS_OFF, -8)

    # ---------------------------------------------------------------- her: the mug, the breath
    put(vox, gen("gasp_b", 0.0, 0.9, fade=0.005), Wd.T_CUP - 0.06, -5)
    put(vox, dsp.sos(gen("stifled", 0.0, 1.6, fade=0.06), "lowpass", 2400.0, 2), Wd.T_CUP + 0.32, -9)   # behind her hand
    put(efx, gen("mug_smash", 0.0, 1.4, fade=0.003), Wd.T_SHATTER - 0.005, -4, pan=-0.1)
    back = [t for t in Wd.foot_contacts(lambda t: Wd.her_pose(t)[0], Wd.T_STEP - 0.2, Wd.T_HER_OFF) if t < Wd.T_REACH]
    for j, t in enumerate(back):                                               # she backs away on bare boards
        put(feet, her_steps[(j + 2) % len(her_steps)], t, -12, pan=-0.15)
    put(efx, fx("chair_creak", seed=9)[: n_of(0.5)], Wd.T_STEP + 0.45, -26)
    hb = fx("heartbeat", dur=Wd.T_DOOR_PUSH - Wd.T_STEP, seed=1, bpm=84, bpm_end=128)
    put(music, hb * dsp.env_bp_db([(0.0, -30), (0.6, 0), (len(hb) / SR, 0)], len(hb))[:, None], Wd.T_STEP, -9)
    b1 = gen("her_breath", 0.0, Wd.T_HER_OFF + 0.4 - (Wd.T_STEP + 0.4), fade=0.2)
    put_track(vox, env_db(b1, [(0.0, -20), (0.5, 0), (len(b1) / SR, 0)]), Wd.T_STEP + 0.4, -10, Wd.HER_C)
    put(efx, fx("clock_tick", seed=4), Wd.T_HIS_ON, -12, pan=0.4)             # his light: on again
    put(music, fx("braam", seed=2), Wd.T_POINT + 0.1, -8)
    put(vox, dsp.sos(gen("gasp_a", 0.0, 0.7, fade=0.005), "lowpass", 3000.0, 2), Wd.T_POINT + 0.1, -11, pan=-0.2)
    # his turn and his run out of the room; a door slammed over there
    runs = step_bank("street_run", thr_db=-14.0, length=0.2)
    falls = Wd.foot_contacts(lambda t: Wd.man_pose(t)[0], Wd.T_TURN - 0.2, Wd.T_RUN + 1.0)
    for j, t in enumerate(falls):
        put(feet, glass(runs[j % len(runs)], lp=1500.0, seed=10 + j), t, -14, pan=0.45)
    put(efx, glass(fx("door_close", seed=6), lp=1300.0, seed=4), Wd.T_RUN + 0.95, -9, pan=0.6)
    put(efx, dsp.sos(mono(fx("keys", seed=7))[: n_of(0.3)], "highpass", 2500.0, 2), Wd.T_REACH + 0.32, -26, pan=-0.1)
    put(efx, fx("clock_tick", seed=6), Wd.T_HER_OFF, -8, pan=-0.1)            # her light: off

    # ---------------------------------------------------------------- his way to her door: every step heard
    down = step_bank("stairs_down", length=0.26)
    for i, t in enumerate(steps(Wd.T_STAIR_B[0], Wd.T_DOOR_B - 0.12, 8)):
        put(feet, down[i % len(down)], t, -8, pan=0.55)
    put(efx, fx("door_open", seed=3), Wd.T_DOOR_B - 0.05, -12, pan=0.6)
    put(efx, fx("door_close", seed=5), Wd.T_DOOR_B + 0.3, -11, pan=0.6)
    street = gen("street_run", 0.08, 0.08 + Wd.T_LINE[1] + 0.1 - Wd.T_LINE[0], fade=0.04)
    n = len(street)
    pan = np.interp(np.arange(n) / SR, [0.0, n / SR], [0.6, -0.6])
    th = (pan + 1.0) * np.pi / 4.0
    dsp.mix_into(feet, (np.stack([street * np.cos(th), street * np.sin(th)], axis=1) * db2lin(-6)).astype(np.float32),
                 n_of(Wd.T_LINE[0]))
    put(efx, fx("door_creak", seed=4), Wd.T_DOOR_A - 0.05, -15, pan=-0.6)
    put(efx, fx("door_close", seed=4), Wd.T_DOOR_A + 0.25, -11, pan=-0.6)
    up = step_bank("stairs_up", length=0.26)
    for i, t in enumerate(steps(Wd.T_STAIR_A[0], Wd.T_HALL + 0.45, 8, accel=1.4)):
        put(feet, up[i % len(up)], t, -9 + 0.4 * i, pan=-0.4)
    put(music, fx("riser", dur=Wd.T_FEET - Wd.T_HALL, seed=5), Wd.T_HALL, -17)

    # ---------------------------------------------------------------- at her door: in the dark, she listens
    b2 = gen("her_breath", 2.4, 2.4 + Wd.T_FEET - 0.1 - Wd.T_DOOR_PUSH, fade=0.03)
    put(vox, env_db(b2, [(0.0, -30), (0.5, -3), (len(b2) / SR, 0)]), Wd.T_DOOR_PUSH, -11)   # held at the feet
    hall = steps(Wd.T_DOOR_PUSH + 0.5, Wd.T_FEET - 0.45, 4)                    # his steps down her hall
    for i, t in enumerate(hall):
        put(feet, dsp.sos(up[(i + 3) % len(up)], "lowpass", 1100.0 + 400.0 * i, 2), t, -17 + 3.0 * i)
    for j in range(2):                                                          # he stops at her door
        put(feet, dsp.sos(up[(j + 1) % len(up)], "lowpass", 2600.0, 2), Wd.T_FEET + 0.14 * j, -4 - 3.0 * j)
    hv = gen("his_breath", 0.9, 0.9 + Wd.T_EYE + 0.2 - (Wd.T_FEET + 0.3), fade=0.08)
    put(vox, dsp.sos(hv, "lowpass", 1500.0, 2), Wd.T_FEET + 0.3, -5)
    rattles = [(0.06, 0.9), (1.8, 2.55)]
    for (a, b), t0 in zip(rattles, Wd.T_KNOB):
        put(efx, gen("handle", a, b, fade=0.01, norm=-1.0), t0 - 0.05, -4)
    put(vox, dsp.sos(gen("gasp_a", 0.0, 0.6, fade=0.005), "lowpass", 1500.0, 2), Wd.T_KNOB[1] + 0.45, -16)

    # ---------------------------------------------------------------- the eye; cut to black
    put(music, fx("reverse_swell", dur=Wd.T_EYE - Wd.T_KEY_PUSH, seed=6), Wd.T_KEY_PUSH, -10)
    put(music, fx("stinger", seed=9), Wd.T_EYE, -5)

    # ---------------------------------------------------------------- bus, cut, master
    mix = music + efx + amb + vox + feet
    a = int(BLACK * SR)
    r = np.linspace(1.0, 0.0, n_of(0.008))
    mix[a: a + len(r)] *= r[:, None]
    mix[a + len(r):] = 0.0
    put(mix, fx("impact", seed=11, size=0.6), BLACK, -6)                         # one low hit, into silence
    mix = dsp.sos(mix, "highpass", 30, 2)
    lufs = dsp.loudness_integrated(mix)
    mix *= db2lin(-16.0 - lufs)
    mix = dsp.limiter(mix, ceiling_db=-1.0)
    mix = dsp.fade(mix, 0.01, 0.3)
    out = os.path.join(ROOT, "out")
    os.makedirs(out, exist_ok=True)
    import soundfile as sf
    path = os.path.join(out, "audio_master.wav")
    sf.write(path, mix[:N].astype(np.float32), SR, subtype="PCM_24")
    print(path, "LUFS", round(dsp.loudness_integrated(mix), 2), "TP", round(dsp.true_peak_db(mix), 2),
          "dur", round(len(mix[:N]) / SR, 3))


if __name__ == "__main__":
    main()
