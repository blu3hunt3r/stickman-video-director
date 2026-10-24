"""DOUBLE CROSS v2: the shot types borrowed from the reference edit, cut to this film's paper
(docs/SHOT_TYPES.md says what was taken, what was changed and what was left).

A scene keeps its own drawing as render_plain(f, t, T), lists its shots as INSERTS (not SHOTS:
some scenes already name their cuts that), and plays them:

    INSERTS = (S.Flash(11.0, 2, K.GOLD), S.Punch(11.375, 5, can_frame, 5.0, seed=51))
    def render(f, t, T):
        S.play(f, t, T, render_plain, INSERTS)

    Punch(t0, n, at, zoom)   the extreme close-up: the scene's own frame redrawn `zoom` times
                             closer on one detail (at: frame px, or t -> frame px). Vector, so
                             its lines thicken as it comes in; it shakes on the hit; cut-paper
                             wedges rush in from the frame's edges toward the detail (Bass's
                             radiating strips, in place of manga speed lines)
    Flash(t0, n, colour)     a flat frame of paper colour, the cymbal crash for the eyes; no
                             sound words on it (the film is wordless)
    Slip(t0, n, amount)      the rewind's glitch: strips of the finished frame slide sideways,
                             a few go flat ink or paper, a paper hairline marks some seams; no
                             colour split, so the palette holds
    Insert(t0, n, draw)      another frame altogether: draw(f, t, k) (the Knight on his sunburst)

Each shot covers n frames from the first frame at or after t0. Other scenes that replay this
one (the s09 rewind) call render_plain, so the shots happen once, where they belong.
"""
import math
from collections import namedtuple
from contextlib import contextmanager

import cairo
import numpy as np

from engine import bass
from engine.core import clamp, ease, hash01, lerp
from engine.frame import surf_array
from films.double_cross import kit as K

FPS = 24
W, H = K.W, K.H

Punch = namedtuple("Punch", "t0 n at zoom seed accent", defaults=(0, None))
Flash = namedtuple("Flash", "t0 n colour")
Slip = namedtuple("Slip", "t0 n amount seed", defaults=(0,))
Insert = namedtuple("Insert", "t0 n draw")


def frame_k(t, t0, n):
    """Which frame of a shot (t0, n frames) the frame at t is, or None outside it."""
    k = int(round(t * FPS)) - int(math.ceil(t0 * FPS - 1e-6))
    return k if 0 <= k < n else None


def active(t, shots):
    """(shot, k) of the first shot covering t that replaces the frame (not a Slip), or None."""
    for s in shots:
        if isinstance(s, Slip):
            continue
        k = frame_k(t, s.t0, s.n)
        if k is not None:
            return s, k
    return None


def play(f, t, T, plain, shots):
    """Render frame t of a scene through its shots (see the module docstring)."""
    hit = active(t, shots)
    if hit is None:
        plain(f, t, T)
    else:
        s, k = hit
        if isinstance(s, Flash):
            flash(f, s.colour)
        elif isinstance(s, Insert):
            s.draw(f, t, k)
        else:
            punch(f, t, T, plain, s, k)
    for s in shots:
        if isinstance(s, Slip):
            k = frame_k(t, s.t0, s.n)
            if k is not None:
                slip(f, s.amount, s.seed * 7 + k)


# ============================================================================ the punch-in
@contextmanager
def viewed(f, m):
    """Inside, every f.screen() draws through m (frame px -> frame px): the same drawing, seen
    through another lens. (DOUBLE CROSS draws everything through f.screen().)"""
    @contextmanager
    def screen():
        f.ctx.save()
        f.ctx.set_matrix(m.multiply(cairo.Matrix(xx=f.scale, yy=f.scale)))
        try:
            yield f.ctx
        finally:
            f.ctx.restore()

    f.screen = screen
    try:
        yield
    finally:
        del f.screen


def punch_matrix(at, zoom, k, n, seed):
    """The lens for frame k of n: `zoom` times closer on `at`, snapping in over the first two
    frames and still creeping after, shaken hard on the hit and settling. The window is kept on
    the frame, so nothing past the scene's edges shows."""
    u = k / max(1, n - 1)
    z = zoom * lerp(0.82, 1.0, ease("out3", clamp(k / 1.5))) * (1.0 + 0.05 * u)
    hw, hh = W / (2.0 * z) * 1.05, H / (2.0 * z) * 1.05
    cx, cy = clamp(at[0], hw, W - hw), clamp(at[1], hh, H - hh)
    dec = (1.0 - u) ** 1.5
    dx = (2.0 * hash01(seed, k, 1) - 1.0) * 28.0 * dec
    dy = (2.0 * hash01(seed, k, 2) - 1.0) * 28.0 * dec
    rot = (2.0 * hash01(seed, k, 3) - 1.0) * 1.8 * dec
    m = cairo.Matrix()
    m.translate(W / 2.0 + dx, H / 2.0 + dy)
    m.rotate(math.radians(rot))
    m.scale(z, z)
    m.translate(-cx, -cy)
    return m


def punch(f, t, T, plain, s, k):
    at = s.at(t) if callable(s.at) else s.at
    m = punch_matrix(at, s.zoom, k, s.n, s.seed)
    with viewed(f, m):
        plain(f, t, T)
    with f.screen() as c:
        wedges(c, m.transform_point(*at), k / max(1, s.n - 1), s.seed, accent=s.accent)


def wedges(c, p, u, seed, n=16, colour=K.INK, accent=None):
    """Cut-paper wedges rushing in from the frame's edges toward p (frame px) as u runs 0..1
    through a punch-in: flat, hand-cut (a kink in each long edge), their tips flickering in."""
    R = max(math.dist(p, q) for q in ((0.0, 0.0), (W, 0.0), (0.0, H), (W, H))) + 80.0
    r_in = lerp(0.8, 0.5, ease("out3", u)) * min(R, 1150.0)
    polys, acc = [], []
    j_acc = int(hash01(seed, 9) * n)
    for i in range(n):
        a = 2.0 * math.pi * (i + 0.4 * (hash01(seed, i, 11) - 0.5)) / n + 0.37 * seed
        hw = math.pi / n * lerp(0.3, 0.6, hash01(seed, i, 12))
        ri = r_in * lerp(0.85, 1.2, hash01(seed, i, 13, int(u * 6.0)))
        ro = R * 1.3
        tip = (p[0] + ri * math.cos(a), p[1] + ri * math.sin(a))
        side = []
        for sgn, salt in ((-1.0, 14), (1.0, 15)):
            b = (p[0] + ro * math.cos(a + sgn * hw), p[1] + ro * math.sin(a + sgn * hw))
            v = 0.45 + 0.2 * hash01(seed, i, salt)
            nx, ny = -math.sin(a + sgn * hw), math.cos(a + sgn * hw)
            kink = 6.0 + 8.0 * hash01(seed, i, salt + 10)
            mid = (lerp(tip[0], b[0], v) + sgn * nx * kink, lerp(tip[1], b[1], v) + sgn * ny * kink)
            side.append((mid, b))
        poly = bass.orient([tip, side[0][0], side[0][1], side[1][1], side[1][0]], True)
        (acc if accent is not None and i == j_acc else polys).append(poly)
    bass.fill_polys(c, polys, colour)
    if acc:
        bass.fill_polys(c, acc, accent)


# ============================================================================ the flash
def flash(f, colour):
    """Flat paper colour: the film's own field, fibres and grain, nothing drawn on it."""
    K.scene_setup(f, colour)


# ============================================================================ the slip
def _bgra(rgb):
    return np.array([rgb[2] * 255.0, rgb[1] * 255.0, rgb[0] * 255.0, 255.0], np.uint8)


def slip(f, amount, seed):
    """Strips of the finished frame slide sideways, like a splice in a tape: the heavier the
    amount, the more strips and the farther; a few strips go flat ink or paper, a paper hairline
    marks some seams, and a heavy one jumps the whole picture a little (the tape's hold)."""
    a = surf_array(f.surf)
    h, w = a.shape[:2]
    s = f.scale
    paper, ink = _bgra(K.PAPER), _bgra(K.INK)
    if amount >= 0.7:
        a[...] = np.roll(a, int((2.0 * hash01(seed, 99) - 1.0) * 36.0 * s), axis=0)
    y, i = 0, 0
    while y < h:
        y1 = min(h, y + max(2, int((6.0 + 92.0 * hash01(seed, i, 1) ** 2.2) * s)))
        r = hash01(seed, i, 2)
        if r < 0.62 * amount:
            dx = int((2.0 * hash01(seed, i, 3) - 1.0) * (30.0 + 260.0 * amount) * s)
            a[y:y1] = np.roll(a[y:y1], dx, axis=1)
            if hash01(seed, i, 4) < 0.45:
                a[y:min(y1, y + max(1, int(round(2.0 * s))))] = paper
        elif r > 1.0 - 0.08 * amount:
            a[y:min(y1, y + max(1, int(14.0 * s)))] = paper if hash01(seed, i, 5) < 0.5 else ink
        y, i = y1, i + 1
    f.surf.mark_dirty()


# ============================================================================ the loud ground
def sunburst(c, p, colours, n=28, rot=0.0, r=3200.0):
    """Rays from p alternating through colours: the bold ground a silhouette is cut out against."""
    groups = [[] for _ in colours]
    for i in range(n):
        a0 = rot + 2.0 * math.pi * i / n
        a1 = rot + 2.0 * math.pi * (i + 1) / n
        groups[i % len(colours)].append(bass.orient([p, (p[0] + r * math.cos(a0), p[1] + r * math.sin(a0)),
                                                     (p[0] + r * math.cos(a1), p[1] + r * math.sin(a1))], True))
    for col, polys in zip(colours, groups):
        bass.fill_polys(c, polys, col)
