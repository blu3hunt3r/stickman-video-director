"""Core constants, math, easing, keyframe tracks and deterministic noise.

Silhouette Noir engine (Saul Bass x Limbo x Inside). World units are frame pixels of the
1080x1920 (9:16) canvas at camera zoom 1; y grows downward.
"""
import math

import numpy as np

W, H, FPS = 1080, 1920, 24

# Safe area for 9:16 social platforms (TikTok / Shorts / Reels UI). Keep key action inside.
SAFE = (90, 240, 990, 1500)   # x0, y0, x1, y1


# ----------------------------------------------------------------------------- math
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    if isinstance(a, (tuple, list)):
        return tuple(lerp(x, y, t) for x, y in zip(a, b))
    return a + (b - a) * t


def inv_lerp(a, b, v):
    """Normalized position of v in [a, b], clamped to 0..1."""
    if b == a:
        return 1.0 if v >= b else 0.0
    return clamp((v - a) / (b - a))


def remap(v, a, b, c, d):
    return lerp(c, d, inv_lerp(a, b, v))


def smoothstep(e0, e1, x):
    t = inv_lerp(e0, e1, x)
    return t * t * (3 - 2 * t)


def rad(d):
    return d * math.pi / 180.0


def deg(r):
    return r * 180.0 / math.pi


def vec(a, b):
    return (b[0] - a[0], b[1] - a[1])


def vadd(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k)


def vlen(v):
    return math.hypot(v[0], v[1])


def vnorm(v):
    l = vlen(v) or 1.0
    return (v[0] / l, v[1] / l)


def rotate(p, ang_deg, origin=(0.0, 0.0)):
    a = rad(ang_deg)
    c, s = math.cos(a), math.sin(a)
    x, y = p[0] - origin[0], p[1] - origin[1]
    return (origin[0] + x * c - y * s, origin[1] + x * s + y * c)


# ----------------------------------------------------------------------------- easing
def _pow_in(p):
    return lambda t: t ** p


def _pow_out(p):
    return lambda t: 1 - (1 - t) ** p


def _pow_inout(p):
    def f(t):
        return 0.5 * (2 * t) ** p if t < 0.5 else 1 - 0.5 * (2 - 2 * t) ** p
    return f


def _out_back(s=1.70158):
    def f(t):
        t -= 1
        return t * t * ((s + 1) * t + s) + 1
    return f


def _out_elastic(t):
    if t in (0.0, 1.0):
        return t
    return 2 ** (-10 * t) * math.sin((t - 0.075) * (2 * math.pi) / 0.3) + 1


EASES = {
    "linear": lambda t: t,
    "in": _pow_in(2), "out": _pow_out(2), "inout": _pow_inout(2),
    "in3": _pow_in(3), "out3": _pow_out(3), "inout3": _pow_inout(3),
    "in5": _pow_in(5), "out5": _pow_out(5), "inout5": _pow_inout(5),
    "sine": lambda t: 0.5 - 0.5 * math.cos(math.pi * t),
    "outback": _out_back(), "outelastic": _out_elastic,
    "outexpo": lambda t: 1.0 if t >= 1 else 1 - 2 ** (-10 * t),
    "inexpo": lambda t: 0.0 if t <= 0 else 2 ** (10 * t - 10),
    "step": lambda t: 1.0 if t >= 1 else 0.0,
}


def ease(name, t):
    t = clamp(t)
    if t <= 0.0:
        return 0.0          # exact endpoints, whatever the curve's float error
    if t >= 1.0:
        return 1.0
    return EASES[name](t)


def tween(t, t0, t1, a, b, e="inout"):
    """Value going from a (at t0) to b (at t1) with easing; held outside the interval."""
    return lerp(a, b, ease(e, inv_lerp(t0, t1, t)))


class Track:
    """Keyframe track: Track([(t, value), (t, value, 'ease_into_this_key'), ...]).

    Values may be floats or tuples. The ease on a key is used for the segment that
    ENDS at that key (default 'inout'). Holds before the first and after the last key.
    """

    def __init__(self, keys):
        self.keys = sorted(keys, key=lambda k: k[0])

    def __call__(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1]
        for i in range(1, len(ks)):
            if t <= ks[i][0]:
                t0, v0 = ks[i - 1][0], ks[i - 1][1]
                t1, v1 = ks[i][0], ks[i][1]
                e = ks[i][2] if len(ks[i]) > 2 else "inout"
                return lerp(v0, v1, ease(e, inv_lerp(t0, t1, t)))
        return ks[-1][1]


# ----------------------------------------------------------------------------- noise
def hash01(*args):
    """Deterministic pseudo-random float in [0, 1) from integers/floats."""
    h = 2166136261
    for a in args:
        v = int(a * 1000003) if isinstance(a, float) else int(a)
        h ^= v & 0xFFFFFFFF
        h = (h * 16777619) & 0xFFFFFFFF
        h ^= h >> 13
        h = (h * 1274126177) & 0xFFFFFFFF
    h ^= h >> 16
    return (h & 0xFFFFFF) / float(0x1000000)


def rand_range(a, b, *seed):
    return a + (b - a) * hash01(*seed)


def noise1(x, seed=0):
    """Smooth 1D value noise in [-1, 1]."""
    i = math.floor(x)
    f = x - i
    a = hash01(seed, i) * 2 - 1
    b = hash01(seed, i + 1) * 2 - 1
    u = f * f * (3 - 2 * f)
    return a + (b - a) * u


def fbm1(x, seed=0, octaves=3):
    v, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        v += amp * noise1(x * freq, seed + 101 * o)
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return v / norm


def flicker(t, seed=0, rate=9.0, depth=0.25, dropouts=0.0):
    """Light flicker multiplier around 1.0. dropouts>0 adds occasional near-off dips."""
    v = 1.0 - depth * (0.5 + 0.5 * fbm1(t * rate, seed))
    if dropouts > 0:
        k = math.floor(t * 6.0)
        if hash01(seed + 7, k) < dropouts:
            ph = t * 6.0 - k
            v *= 0.15 + 0.85 * abs(math.cos(ph * math.pi * 3))
    return clamp(v, 0.0, 1.2)


def siren(t, rate=1.6, phase=0.0):
    """Police light bar pattern. Returns (blue, red) intensities 0..1 (double-flash strobe)."""
    p = (t * rate + phase) % 1.0

    def dbl(x):
        return 1.0 if (0.0 <= x < 0.09) or (0.16 <= x < 0.25) else 0.0
    return dbl(p), dbl((p + 0.5) % 1.0)


def pulse(t, t0, attack=0.04, decay=0.5):
    """Envelope that spikes at t0 and decays (for flashes / impacts)."""
    if t < t0:
        return 0.0
    dt = t - t0
    if dt < attack:
        return dt / attack
    return math.exp(-(dt - attack) / max(decay, 1e-6))


def smoother(t):
    """Quintic smoothstep of t in 0..1."""
    t = clamp(t)
    return t * t * t * (t * (t * 6 - 15) + 10)


def spring(t, freq=2.0, damping=4.0):
    """Damped spring response 0 -> 1 for t >= 0 (overshoots and settles)."""
    if t <= 0:
        return 0.0
    return 1.0 - math.exp(-damping * t) * math.cos(2 * math.pi * freq * t)


def wrap_angle(a):
    """Wrap degrees to (-180, 180]."""
    a = (a + 180.0) % 360.0 - 180.0
    return 180.0 if a == -180.0 else a


def lerp_angle(a, b, t):
    return a + wrap_angle(b - a) * t


def frac(x):
    return x - math.floor(x)


def noise2(x, y, seed=0):
    """Smooth 2D value noise in [-1, 1] (scalar)."""
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    ux, uy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = hash01(seed, ix, iy) * 2 - 1
    b = hash01(seed, ix + 1, iy) * 2 - 1
    c = hash01(seed, ix, iy + 1) * 2 - 1
    d = hash01(seed, ix + 1, iy + 1) * 2 - 1
    return lerp(lerp(a, b, ux), lerp(c, d, ux), uy)


def noise_grid(w, h, feature=80.0, seed=0, beta=2.2, detail=4.0):
    """Seamlessly tileable fractal noise image (h, w) float32 in [0, 1], made by filtering
    white noise in the frequency domain (periodic by construction, so it scrolls/wraps
    without seams). feature: size of the main blobs in pixels; beta: spectral falloff
    (higher = smoother); detail: how far above the main frequency fine detail extends."""
    rng = np.random.default_rng(int(abs(hash(round(float(seed), 6))) % (2 ** 32)))
    white = rng.standard_normal((h, w)).astype(np.float32)
    spec = np.fft.rfft2(white)
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.rfftfreq(w)[None, :]
    f = np.sqrt(fx * fx + fy * fy)
    f0 = 1.0 / max(feature, 2.0)
    amp = (f0 * f0 + f * f) ** (-beta / 4.0) * np.exp(-(f / (f0 * detail)) ** 2)
    amp[0, 0] = 0.0
    out = np.fft.irfft2(spec * amp, s=(h, w)).astype(np.float32)
    lo, hi = np.percentile(out, 0.5), np.percentile(out, 99.5)
    return np.clip((out - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
