"""s01 · TITLE: a Saul Bass card. A red cut-paper flame on a warm paper field; black
trunks slide in around it and crowd the light; THE LANTERN rises between them; the trunks
close over the title until only the flame is left, and the iris opens out of the flame
into the forest (s02 starts on the lantern's flame at the same spot).

    0.2   the flame pops in, flickering on twos
    0.6   trunks slide in, alternating from the ground and the canopy
    1.7   THE / LANTERN rises in the clearing between them
    4.0   the trunks close in on the flame and grow over the title
    5.5   iris out of the flame (timeline transition, centre FLAME)
"""
import math

from engine import bass
from engine.core import clamp, lerp, ease, hash01, noise1
from engine.palette import PAPER, RED
from engine.timing import Cue

FLAME = (540.0, 1040.0)
FIELD = (0.80, 0.765, 0.70)        # the forest fog colour, flattened to paper

# trunks: (x centre, width, from 'b'ottom or 't'op, reach y, seed)
TRUNKS = []
for i, (x, w) in enumerate([(40, 70), (150, 46), (250, 88), (352, 34), (420, 58),
                            (668, 62), (742, 30), (840, 96), (950, 40), (1046, 72)]):
    side = "b" if i % 3 != 1 else "t"
    reach = 700.0 + 70.0 * hash01(i, 3) if side == "b" else 300.0 - 80.0 * hash01(i, 4)
    TRUNKS.append((float(x), float(w), side, reach, i))


def k(t, t0, dur, e="inout3"):
    return ease(e, clamp((t - t0) / dur))


def flame_pts(c, r, sway, seed):
    """A teardrop flame: round at the bottom, a swaying tip at the top."""
    cx, cy = c
    top = cy - 2.7 * r
    n = 26
    right, left = [], []
    for i in range(n + 1):
        v = i / n                                   # 0 = tip .. 1 = bottom
        y = lerp(top, cy + r, v)
        hw = r * (1.0 - (1.0 - v) ** 1.7) ** 0.55
        if v > 0.72:
            hw *= math.sqrt(max(0.0, 1.0 - ((v - 0.72) / 0.28) ** 2))
        x = cx + sway * (1.0 - v) ** 2
        right.append((x + hw, y))
        left.append((x - hw, y))
    return bass.scissor(right + left[::-1], seed=seed, sag=0.8, amp=0.6, max_len=30.0, corner=50.0)


def draw_flame(c, t, scale):
    tw = bass.on_twos(t)
    sway = 26.0 * noise1(tw * 1.7, seed=2) * scale
    r = 70.0 * scale * (1.0 + 0.05 * noise1(tw * 3.1, seed=5))
    seed = int(tw * 12.0) % 6
    bass.fill_polys(c, [flame_pts(FLAME, r, sway, seed)], RED)
    core = (FLAME[0] + 0.12 * sway, FLAME[1] + 0.18 * r)
    bass.fill_polys(c, [flame_pts(core, r * 0.42, sway * 0.5, seed + 7)], PAPER)


def draw_trunks(c, t):
    close = k(t, 4.0, 1.4, "inout3")
    polys = []
    for j, (x, w, side, reach, i) in enumerate(TRUNKS):
        u = k(t, 0.6 + 0.09 * j, 0.55, "out5")
        if u <= 0:
            continue
        # closing in: every trunk slides toward the flame, the gap around it narrows
        gap = 120.0 - 30.0 * close
        dx = x - FLAME[0]
        xs = FLAME[0] + math.copysign(gap + (abs(dx) - 120.0) * (1.0 - 0.30 * close), dx)
        ww = w * (1.0 + 0.25 * close)
        if side == "b":
            y_top = lerp(reach, -60.0, close)
            off = (1.0 - u) * 1500.0
            p = bass.cut_rect(xs - ww / 2, y_top + off, xs + ww / 2, 2000.0 + off, seed=40 + i, amp=1.6)
        else:
            y_bot = lerp(reach, 1980.0, close)
            off = -(1.0 - u) * 1500.0
            p = bass.cut_rect(xs - ww / 2, -80.0 + off, xs + ww / 2, y_bot + off, seed=40 + i, amp=1.6)
        polys.append(p)
        # a stub of a dead bough on a few
        if hash01(i, 9) < 0.5:
            yb = (y_top + 140.0 + 120 * hash01(i, 10)) if side == "b" else (y_bot - 160.0)
            sgn = -1 if dx > 0 else 1
            L = 90.0 + 60.0 * hash01(i, 11)
            yb += off
            polys.append(bass.cut([(xs, yb), (xs + sgn * L, yb - 0.75 * L), (xs + sgn * (L + 10), yb - 0.75 * L + 12),
                                   (xs, yb + 26)], seed=60 + i, amp=1.2))
    return polys


def render(f, t, T):
    bass.bass_scene(f, field=FIELD, paper=0.8, vignette=0.18, mottle=0.05)
    with f.screen() as c:
        # the flame: pops in, then holds; swells a little as the iris opens out of it
        p = bass.pop(t, 0.2, 0.45)
        if p > 0:
            draw_flame(c, t, p * (1.0 + 0.25 * k(t, 5.2, 0.8, "in3")))
        # the title rises in the clearing, then the trunks grow over it
        Tt = bass.title_glyphs("THE\nLANTERN", width=760.0, leading=1.08, seed=3, rough=1.0, jitter=0.7)
        u = clamp((t - 1.7) / 1.2)
        if u > 0:
            bass.draw_title(c, Tt, (540.0, 520.0), f.pal.ink, u=u, anim="rise", order="ltr", overlap=0.7)
        for p_ in draw_trunks(c, t):          # one by one: overlaps stay solid
            bass.fill_polys(c, [p_], f.pal.ink)


def cues(T):
    return [Cue(0.2, "match strike and a small flame catching", gain_db=-8),
            Cue(0.6, "deep low wooden knocks, one per trunk, staggered", gain_db=-12, dur=1.2),
            Cue(1.7, "soft low string swell", gain_db=-14, dur=3.0),
            Cue(3.7, "wood creaking closer, branches crowding", gain_db=-12, dur=1.6)]
