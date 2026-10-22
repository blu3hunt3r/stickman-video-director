"""s07 · THE PRICE: the crime re-enacted as a Saul Bass flashback (11.5 s, flat graphic).

IN  (hard cut from s06's black hole): 100 % ink.
0.06-0.78 a RED jagged torch line cuts a circle (r 330 at (540, 760)) from inside the
          black, clockwise from the top, a white-hot spark at its head.
0.86-1.18 the cut disk falls toward the camera, revealing PAPER through a hole whose steel
          petals are bent outward (dark teeth pointing into the opening); the hot rim cools.
[She]     the MERIDIAN slides in on the paper; 1.32-1.72 the hole irises open to full PAPER.
[twice]   a second identical ship slides out from behind her (x2).
[worth]   a black fist slides in from the right holding a fan of banknotes; the fan doubles.
5.45-6.08 Psycho ink bars slide in from alternating sides and black the frame out.
[Thirty-one] 30 PAPER crew cut-outs pop onto the ink in 4 rows; the captain, larger, in the
          middle of the top row, pops last on [men].
[part]    flat dark-water bars rise from the bottom, one per row, swallowing them row by row;
          the captain's head goes under last, on [price]. Bubbles rise through the handle.
OUT (bars, 1.0 s, axis 'v', frm 'end'): ink above y 448, five dark-teal water bands below;
    seven ink columns rise from the bottom over them into s08.
"""
import math

from engine import bass
from engine.core import W, H, clamp, hash01, lerp
from engine.palette import PAPER, RED
from engine.timing import Cue

from ._lib_bass_scenes import (DEEP, INK, SEA_HI, SEA_LO, TEAL, banknote_frame, banknote_polys, draw_meridian, fist_polys, k, petal_hole,
                               put, sn, torch_band, torch_pts)

C7, R7 = (540.0, 760.0), 330.0          # the torch circle
HOT = (1.0, 0.44, 0.16)
SPARK = (1.0, 0.80, 0.50)
SHIP_L = 760.0
GRIP = (610.0, 1580.0)                  # where the fist holds the notes
NOTE_S = 1.75
NOTE_DK = (0.045, 0.165, 0.195)          # every other note a shade darker, so the fan reads
ROW_Y = (760.0, 1000.0, 1240.0, 1480.0)
CREW_H, CAPT_H = 176.0, 252.0
#: the water bands (slot top, color), bottom to top: the same flat sea tones as s04's bars
BANDS = ((1292.0, (0.016, 0.052, 0.066)), (1052.0, SEA_LO), (812.0, (0.040, 0.140, 0.165)), (574.0, DEEP),
         (448.0, SEA_HI))
SURFACE = BANDS[-1][0]


def _words(T):
    return dict(she=T.at("she"), twice=T.at("twice"), worth=T.at("worth"), worth_end=T.end("worth"),
                thirty=T.at("thirty-one"), men=T.at("men"), part=T.at("part"), the=T.at("the"),
                price=T.at("price"))


# ----------------------------------------------------------------------------- the cut
def _torch(c, f, t):
    """The red torch line on the black (0.06-0.86) with its spark."""
    pts = torch_pts(C7, R7, seed=3)
    u = clamp((t - 0.06) / 0.72)
    if u <= 0:
        return
    band, head = torch_band(pts, u, width=8.0, seed=3)
    if band is None:
        return
    glow = 1.0 if u < 1 else 1.0 + 1.6 * math.exp(-14.0 * (t - 0.78))
    bass.fill_polys(c, [band], RED)
    with f.emit() as g:
        bass.fill_polys(g, [band], HOT, min(1.0, 0.55 * glow))
        if u < 1:
            bass.disc(g, head, 30.0, HOT, seed=5, n=16)
            bass.disc(g, head, 13.0, SPARK, seed=6, n=12)
    if u >= 1:
        return
    bass.disc(c, head, 6.0, (1.0, 0.97, 0.9), seed=7, n=10)
    fr = int(t * 24 + 0.5)                          # sparks change every frame (deterministic)
    a = math.atan2(head[1] - C7[1], head[0] - C7[0])
    for i in range(7):
        d = a + 1.3 * sn(fr, i, 1) + (0.0 if i % 2 else math.pi)  # both sides of the plate
        L = 18.0 + 46.0 * hash01(fr, i, 2)
        p0 = (head[0] + 6.0 * math.cos(d), head[1] + 6.0 * math.sin(d))
        p1 = (head[0] + L * math.cos(d), head[1] + L * math.sin(d) + 10.0 * hash01(fr, i, 3))
        c.set_source_rgb(*SPARK)
        c.set_line_width(2.4)
        c.move_to(*p0)
        c.line_to(*p1)
        c.stroke()


def _disk(c, t):
    """The cut disk falls toward the camera (0.86-1.18): drops, grows, tips."""
    e = k(t, 0.86, 0.32, "in3")
    if e <= 0 or e >= 1:
        return
    pts = torch_pts(C7, R7, seed=3)
    band, _ = torch_band(pts, 1.0, width=8.0, seed=3)
    c.save()
    c.translate(C7[0], C7[1] + 1250.0 * e)
    c.rotate(math.radians(-14.0 * e))
    c.scale(1.0 + 1.5 * e, (1.0 + 1.5 * e) * (1.0 - 0.38 * e))
    c.translate(-C7[0], -C7[1])
    bass.fill_polys(c, [pts[:-1]], INK)
    bass.fill_polys(c, [band], RED)
    c.restore()


def _hole_r(t):
    return lerp(R7, 1450.0, k(t, 1.32, 0.4, "in3"))


def _plate(c, f, t):
    """The black plate with the petal hole, and the cooling rim."""
    R = _hole_r(t)
    if R >= 1449.0:
        return
    hole = [(C7[0] + R * x, C7[1] + R * y) for x, y in petal_hole(5)]
    c.save()
    c.new_path()
    c.rectangle(-50, -50, W + 100, H + 100)
    bass.path_polys(c, [hole])
    c.set_fill_rule(1)                              # even-odd: the plate minus the hole
    c.set_source_rgb(*INK)
    c.fill()
    c.restore()
    cool = k(t, 0.86, 1.0, "out3")
    if cool < 1:
        col = tuple(lerp(HOT[j], RED[j], min(1.0, 2.2 * cool)) for j in range(3))
        c.save()
        c.new_path()
        bass.path_polys(c, [hole])
        c.set_source_rgba(*col, 1.0 - cool)
        c.set_line_width(5.0)
        c.stroke()
        c.restore()
        with f.emit() as g:
            g.new_path()
            bass.path_polys(g, [hole])
            g.set_source_rgba(*HOT, 0.9 * (1.0 - cool) ** 2)
            g.set_line_width(9.0)
            g.stroke()


# ----------------------------------------------------------------------------- paper act
def _ships(c, t, W_):
    x = lerp(-720.0, C7[0], k(t, W_["she"] - 0.02, 0.44, "out5"))
    split = k(t, W_["twice"] - 0.03, 0.32, "out5")
    bob = 3.0 * math.sin(2.0 * math.pi * t / 2.6)
    rock = 0.8 * math.sin(2.0 * math.pi * t / 3.1)
    y1 = 790.0 - 160.0 * split + bob
    y2 = 790.0 + 230.0 * split + bob
    if split > 0:
        draw_meridian(c, (x, y2), SHIP_L, INK, rot=rock, seed=2)
    draw_meridian(c, (x, y1), SHIP_L, INK, rot=rock, seed=2)


def _money(c, t, W_):
    p = k(t, W_["worth"] - 0.03, 0.4, "out5")
    if p <= 0:
        return
    gx = lerp(GRIP[0] + 1100.0, GRIP[0], p)
    gy = GRIP[1] + 3.0 * math.sin(2.0 * math.pi * t / 2.2)
    dbl = bass.pop(t, W_["worth"] + 0.36, 0.26)            # the fan doubles
    note, win = banknote_polys(4)
    n = 8
    for i in range(n):
        # four notes fanned at first; the other four snap open between them
        a4 = -36.0 + 18.0 * (i // 2) if i % 2 == 0 else -36.0 + 18.0 * (i // 2)
        a8 = -66.0 + 14.0 * i
        if i % 2 == 1 and dbl <= 0:
            continue
        ang = lerp(a4, a8, dbl) + 1.5 * math.sin(2.0 * math.pi * t / 1.7 + i)
        sc = NOTE_S * (1.0 if i % 2 == 0 else max(0.001, dbl))
        c.save()
        c.translate(gx, gy)
        c.rotate(math.radians(ang))
        c.scale(sc, sc)
        bass.fill_polys(c, [note], TEAL if i % 2 == 0 else NOTE_DK)
        bass.fill_polys(c, banknote_frame(4), PAPER, 0.85)
        bass.fill_polys(c, [win], PAPER)
        c.restore()
    put(c, fist_polys(1), INK, (gx, gy), 0.0, 1.8)


_PSYCHO = bass.bar_rects((0.0, -10.0, W, H + 10.0), 9, "h", None, 0.0, 71, irregular=0.45)


def _bars(c, t):
    """Psycho bars: nine ink bars slide in from alternating sides (overlapping: no seams)."""
    for i, (x0, y0, x1, y1) in enumerate(_PSYCHO):
        p = k(t, 5.45 + 0.06 * ((i * 4) % 9), 0.3, "out5")
        if p <= 0:
            continue
        side = -1.0 if i % 2 == 0 else 1.0
        poly = bass.cut_rect(-40.0, y0 - 3.0, W + 40.0, y1 + 3.0, seed=710 + i, amp=1.2)
        put(c, [poly], INK, (side * (W + 200.0) * (1.0 - p), 0.0))


# ----------------------------------------------------------------------------- the crew
def _crew_layout():
    out = []
    kinds = ("man", "worker", "man", "worker", "man", "worker", "man", "worker")
    for j, x in enumerate((120.0, 240.0, 360.0, 540.0, 720.0, 840.0, 960.0)):
        cap = j == 3
        out.append(dict(row=0, x=x, kind="captain" if cap else kinds[j], h=CAPT_H if cap else CREW_H,
                        cap=cap, seed=40 + j, flip=j > 3))
    for r in (1, 2, 3):
        for j in range(8):
            x = 540.0 + (j - 3.5) * 124.0
            out.append(dict(row=r, x=x, kind=kinds[(j + r) % 8], h=CREW_H * (0.97 + 0.06 * hash01(r, j)),
                            cap=False, seed=50 + 10 * r + j, flip=(j + r) % 3 == 0))
    return out


CREW = _crew_layout()


def _crew(c, t, W_):
    rank = 0
    for d in CREW:
        if d["cap"]:
            p = bass.pop(t, W_["men"] - 0.03, 0.32)
        else:
            p = bass.pop(t, W_["thirty"] - 0.02 + 0.027 * rank, 0.2)
            rank += 1
        if p <= 0:
            continue
        foot = (d["x"], ROW_Y[d["row"]])
        bass.draw_cutout(c, d["kind"], foot, d["h"] * p, PAPER, seed=d["seed"], flip=d["flip"])


def _band_times(W_):
    """One bar per row from [part]; the captain's bar lands on [price]."""
    p0, p1 = W_["part"], W_["price"]
    return (p0, p0 + 0.17, p0 + 0.34, p0 + 0.51, p1)


def _water(c, t, W_):
    """The water bars rise from the bottom, each into its own slot."""
    times = _band_times(W_)
    for i, ((top, col), t0) in enumerate(zip(BANDS, times)):
        p = k(t, t0 - 0.02, 0.3, "out5")
        if p <= 0:
            continue
        bottom = H + 60.0 if i == 0 else BANDS[i - 1][0] + 8.0
        dy = (H + 80.0 - top) * (1.0 - p)
        poly = bass.cut_rect(-60.0, top, W + 60.0, bottom, seed=600 + i, amp=2.4)
        put(c, [poly], col, (0.0, dy))


def _bubbles(c, t, W_):
    t0 = W_["price"] + 0.12
    for i in range(18):
        tb = t0 + 0.085 * i + 0.05 * hash01(9, i)
        if t < tb:
            continue
        d = CREW[3] if i < 3 else CREW[int(hash01(9, i, 1) * len(CREW))]
        x0 = d["x"] + 30.0 * sn(9, i, 2)
        y0 = ROW_Y[d["row"]] - d["h"] * 0.9
        v = 300.0 + 220.0 * hash01(9, i, 3)
        y = y0 - v * (t - tb)
        r = 5.0 + 8.0 * hash01(9, i, 4)
        if y < SURFACE + r + 4.0:
            continue
        x = x0 + 7.0 * math.sin(9.0 * (t - tb) + 6.0 * hash01(9, i, 5))
        bass.ring(c, (x, y), r, max(2.5, 0.35 * r), PAPER, seed=i, n=12)


# ----------------------------------------------------------------------------- scene
def render(f, t, T):
    W_ = _words(T)
    bass.bass_scene(f, field=INK, paper=0.7, vignette=0.2)
    with f.screen() as c:
        if t < 6.1:
            if t >= 0.86:
                bass.paper_field(c, PAPER)
                _ships(c, t, W_)
                _money(c, t, W_)
                _plate(c, f, t)
                _disk(c, t)
                _bars(c, t)
            else:
                _torch(c, f, t)
        else:
            z = 1.0 + 0.035 * k(t, W_["thirty"], W_["part"] - W_["thirty"], "inout")   # a slow push-in
            c.translate(540.0, 1100.0)
            c.scale(z, z)
            c.translate(-540.0, -1100.0)
            _crew(c, t, W_)
            _water(c, t, W_)
            _bubbles(c, t, W_)


def cues(T):
    W_ = _words(T)
    bt = _band_times(W_)
    return [
        Cue(0.06, "cutting torch ignites and hisses around a circle", -4, dur=0.72),
        Cue(0.78, "torch cut closes: metallic ping", -6),
        Cue(0.86, "the cut disk falls toward us: heavy steel clang", -2, dur=0.35),
        Cue(1.32, "the hole irises open: paper whoosh", -8, dur=0.4),
        Cue(W_["she"], "paper slide: the ship glides in", -8),
        Cue(W_["twice"], "paper slide: a second ship slips out", -6),
        Cue(W_["worth"], "paper slide: the fist with the banknotes", -6),
        Cue(W_["worth"] + 0.36, "banknotes fan open: crisp paper riffle", -5),
        Cue(5.45, "Psycho bars slam in, staggered paper swishes", -5, dur=0.63),
        Cue(W_["thirty"], "thirty small paper pops, fast (the crew)", -7, dur=0.85),
        Cue(W_["men"], "paper pop: the captain, heavier", -4),
        Cue(bt[0], "dark water bar rises: low muffled surge", -4),
        Cue(bt[1], "dark water bar rises: low muffled surge", -4),
        Cue(bt[2], "dark water bar rises: low muffled surge", -4),
        Cue(bt[3], "dark water bar rises: low muffled surge", -4),
        Cue(bt[4], "the last bar closes over the captain: deep thud", -1),
        Cue(W_["price"] + 0.12, "bubbles rise and pop", -10, dur=1.3),
    ]
