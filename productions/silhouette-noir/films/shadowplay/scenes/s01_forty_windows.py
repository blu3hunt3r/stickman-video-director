"""s01 · FORTY WINDOWS: Saul Bass opening, North by Northwest's facade grid (9.0 s, flat).

0.0-1.35  PAPER field. Thin ink grid lines slide in from the edges (verticals from the top,
          horizontals from alternating sides), then 39 ink windows pop in row by row (0.03 s
          stagger, outback), a little loose, at the FACADE LOCK (bible section 3).
[forty]   window 9 slides in along its row's line and lands; the whole grid snaps tight.
4.40-5.51 venetian flip, eight row bands top to bottom: PAPER -> the night facade in flat
          tones (sky, wall, roof silhouettes, ground floor). The windows become dark holes,
          the horizontal grid lines become ledges; the 9 NIGHT windows bulb-flicker on, amber.
[every]   a counting glint runs over all forty windows.  [heart] the lit windows pulse twice.
7.70-     flat diagonal rain streaks begin, and keep falling through the handle.
OUT (flatten, 1.0 s): the flat facade with the 40 windows on the lock rects (96 x 120 at
    x 230..850 / y 440..1490), lit = sets_facade.NIGHT, resolving into s02's live facade.
"""
import math

from engine import bass
from engine.core import W, H, ease, hash01, lerp
from engine.palette import PAPER, SHADOWPLAY
from engine.timing import Cue
from films.shadowplay.sets_facade import LOCK_COLS, LOCK_ROWS, LOCK_SIZE, NIGHT

INK = SHADOWPLAY.ink
SKY = (0.125, 0.135, 0.175)          # night ink-blue
WALL = (0.058, 0.062, 0.082)
LEDGE = (0.15, 0.16, 0.21)           # the shadowplay Bass mid tone
STREET = (0.030, 0.032, 0.045)
GLINT = (0.36, 0.38, 0.47)
FAC = (116.0, 286.2, 964.0, 1763.8)  # the facade at the lock (screen px, from sets_facade)
V_LINES = tuple((LOCK_COLS[i] + LOCK_COLS[i + 1]) / 2 for i in range(4))
V_LINES = (LOCK_COLS[0] - 77.5,) + V_LINES + (LOCK_COLS[-1] + 77.5,)
H_LINES = tuple(LOCK_ROWS[0] - 75.0 + 150.0 * i for i in range(9))
BANDS = (0.0, 515.0, 665.0, 815.0, 965.0, 1115.0, 1265.0, 1415.0, H)
LIGHT_ORDER = (4, 12, 30, 2, 19, 26, 7, 23, 37)


def _k(t, t0, dur, e="out3"):
    if t <= t0:
        return 0.0
    if t >= t0 + dur:
        return 1.0
    return ease(e, (t - t0) / dur)


def _sn(*a):
    return hash01(*a) * 2.0 - 1.0


def _words(T):
    return dict(forty=T.at("forty"), every=T.at("every"), them_end=T.end("them"), heart=T.at("heart"))


def _rect(i):
    r, c = (i - 1) // 5, (i - 1) % 5
    cx, cy = LOCK_COLS[c], LOCK_ROWS[r]
    return cx, cy, r, c


# ----------------------------------------------------------------------------- PAPER side
def _lines(c, t):
    """North by Northwest grid lines sliding in from the edges."""
    for j, x in enumerate(V_LINES):
        p = _k(t, 0.02 + 0.05 * j, 0.42, "out3")
        if p > 0:
            c.rectangle(x - 1.5, -10.0, 3.0, (H + 20.0) * p)
    for j, y in enumerate(H_LINES):
        p = _k(t, 0.08 + 0.045 * j, 0.42, "out3")
        if p > 0:
            L = (W + 20.0) * p
            c.rectangle(-10.0 if j % 2 == 0 else W + 10.0 - L, y - 1.5, L, 3.0)
    c.set_source_rgb(*INK)
    c.fill()


def _window_ink(c, t, W_):
    snap = _k(t, W_["forty"] - 0.01, 0.2, "outback")
    rank = 0
    for i in range(1, 41):
        cx, cy, r, col = _rect(i)
        if i == 9:
            # the last window slides in along row 2's line and lands on [forty]
            p = _k(t, W_["forty"] - 0.24, 0.24, "in")       # accelerates and slams home on the word
            if p <= 0:
                continue
            cx = lerp(W + 140.0, cx, p)
            s = 1.0
            ox = bass.settle(t, W_["forty"], amp=-9.0, freq=5.0, decay=13.0)
            oy = rot = 0.0
        else:
            s = bass.pop(t, 0.3 + 0.03 * rank, 0.22)
            rank += 1
            if s <= 0:
                continue
            loose = 1.0 - snap
            ox = loose * (6.0 * _sn(3, i, 1) + 2.0 * math.sin(0.9 * t + 6.0 * hash01(3, i, 4)))
            oy = loose * (5.0 * _sn(3, i, 2) + 2.0 * math.sin(0.7 * t + 6.0 * hash01(3, i, 5)))
            rot = loose * 2.6 * _sn(3, i, 3)
        w, h = LOCK_SIZE[0] * s, LOCK_SIZE[1] * s
        poly = bass.cut_rect(-LOCK_SIZE[0] / 2, -LOCK_SIZE[1] / 2, LOCK_SIZE[0] / 2, LOCK_SIZE[1] / 2,
                             seed=100 + i, amp=1.0)
        c.save()
        c.translate(cx + ox, cy + oy)
        c.rotate(math.radians(rot))
        c.scale(w / LOCK_SIZE[0], h / LOCK_SIZE[1])
        bass.fill_polys(c, [poly], INK)
        c.restore()


def _paper(c, t, W_):
    bass.paper_field(c, PAPER)
    _lines(c, t)
    _window_ink(c, t, W_)


# ----------------------------------------------------------------------------- night side
def _roof(c):
    """Flat ink silhouettes of the rooftop (the live facade's objects, at the lock)."""
    shapes = [
        [(721.0, 301.0), (721.0, 223.0), (725.0, 223.0), (725.0, 301.0)],      # tank stand legs
        [(807.0, 301.0), (807.0, 223.0), (811.0, 223.0), (811.0, 301.0)],
        [(710.0, 226.0), (822.0, 226.0), (822.0, 221.0), (710.0, 221.0)],      # platform beam
        [(725.0, 221.0), (806.0, 221.0), (806.0, 130.0), (725.0, 130.0)],      # tank body
        [(719.0, 131.0), (812.0, 131.0), (788.0, 116.0), (766.0, 101.0), (743.0, 116.0)],   # cone
        [(764.0, 104.0), (768.0, 104.0), (768.0, 88.0), (764.0, 88.0)],        # finial
        [(256.0, 301.0), (256.0, 233.0), (295.0, 233.0), (295.0, 301.0)],      # chimney
        [(253.0, 233.0), (298.0, 233.0), (298.0, 229.0), (253.0, 229.0)],
        [(262.0, 229.0), (271.0, 229.0), (271.0, 212.0), (262.0, 212.0)],      # pots
        [(279.0, 229.0), (288.0, 229.0), (288.0, 218.0), (279.0, 218.0)],
        [(561.0, 301.0), (561.0, 252.0), (585.0, 252.0), (585.0, 301.0)],      # second chimney
        [(408.0, 301.0), (408.0, 230.0), (489.0, 238.0), (489.0, 301.0)],      # stair bulkhead
        [(405.0, 233.0), (492.0, 233.0), (492.0, 229.0), (405.0, 229.0)],
        [(622.0, 301.0), (622.0, 163.0), (624.5, 163.0), (624.5, 301.0)],      # antenna mast
    ]
    for yy, half in ((167.0, 20.0), (176.0, 15.0), (186.0, 11.0), (196.0, 8.0)):
        shapes.append([(623.0 - half, yy), (623.0 + half, yy), (623.0 + half, yy + 1.6), (623.0 - half, yy + 1.6)])
    bass.fill_polys(c, [bass.orient(s, True) for s in shapes], INK)


def _level(i, t, W_, on_t):
    """Brightness 0..1.3 of lit window i: bulb flicker-on, a TV-ish shimmer, the heartbeat."""
    if i not in NIGHT or t < on_t:
        return 0.0, 0.0
    dt = t - on_t
    b = 1.0 if dt < 0.04 else (0.12 if dt < 0.1 else 1.0)
    b *= 0.72 + 0.28 * NIGHT[i]
    if i in (19, 23):
        b *= 1.0 + 0.05 * math.sin(19.0 * t + i) * math.sin(5.3 * t + 2 * i)
    beat = 0.0
    for t0, amp in ((W_["heart"], 1.0), (W_["heart"] + 0.27, 0.7)):
        if t >= t0:
            beat += amp * math.exp(-9.0 * (t - t0)) * min(1.0, (t - t0) / 0.03)
    return b, beat


def _on_times(W_):
    out = {}
    for n, i in enumerate(LIGHT_ORDER):
        cx, cy, r, col = _rect(i)
        band_done = 4.40 + 0.11 * r + 0.34
        out[i] = max(band_done + 0.04, 5.02 + 0.075 * n)
    return out


def _night(c, f, t, W_, glow=1.0):
    """The flat night facade. glow scales the emissive halo of the lit windows (0 = none:
    the venetian flip draws this once per slat and adds the halos itself)."""
    pal = f.pal
    bass.paper_field(c, SKY)
    _roof(c)
    x0, y0, x1, y1 = FAC
    c.rectangle(0.0, y1, W, H - y1)
    c.set_source_rgb(*STREET)
    c.fill()
    bass.fill_polys(c, [bass.cut_rect(x0, y0, x1, y1, seed=7, amp=0.8)], WALL)
    # parapet coping + cornice, the floor ledges (the old grid lines), the belt course
    for (a, b, ya, yb) in ((x0 - 3, x1 + 3, y0, y0 + 5), (x0 - 13, x1 + 13, y0 + 21, y0 + 40),
                           (x0 - 4, x1 + 4, 1564.0, 1582.0)):
        bass.fill_polys(c, [bass.cut_rect(a, ya, b, yb, seed=int(ya), amp=0.6)], LEDGE)
    for y in H_LINES[1:8]:
        bass.fill_polys(c, [bass.cut_rect(x0 - 6, y - 3.0, x1 + 6, y + 3.0, seed=int(y), amp=0.5)], LEDGE)
    # ground floor: two shopfronts (the right one lit), the door with its lit transom
    bass.fill_polys(c, [bass.cut_rect(172.3, 1606.2, 441.8, 1718.8, seed=31, amp=0.6)], INK)
    shop = tuple(lerp(WALL[j], pal.light[j], 0.82) for j in range(3))
    bass.fill_polys(c, [bass.cut_rect(638.2, 1606.2, 907.8, 1718.8, seed=32, amp=0.6)], shop)
    for xm in (728.0, 818.0):
        c.rectangle(xm - 2.0, 1606.2, 4.0, 112.6)
    c.rectangle(638.2, 1650.0, 269.6, 3.0)
    c.set_source_rgb(*WALL)
    c.fill()
    bass.fill_polys(c, [bass.cut_rect(504.8, 1621.2, 575.2, 1734.5, seed=33, amp=0.5)], INK)
    bass.fill_polys(c, [bass.cut_rect(510.0, 1626.0, 570.0, 1640.0, seed=34, amp=0.3)], pal.light)
    # the forty windows: dark holes; nine lit in flat amber
    on = _on_times(W_)
    hot = pal.lamp_hot
    for i in range(1, 41):
        cx, cy, r, col = _rect(i)
        hw, hh = LOCK_SIZE[0] / 2, LOCK_SIZE[1] / 2
        b, beat = _level(i, t, W_, on.get(i, 99.0))
        s = 1.0 + 0.07 * beat
        poly = bass.cut_rect(-hw, -hh, hw, hh, seed=100 + i, amp=1.0)
        c.save()
        c.translate(cx, cy)
        c.scale(s, s)
        if b <= 0:
            bass.fill_polys(c, [poly], INK)
        else:
            col_ = tuple(min(1.0, lerp(INK[j], pal.light[j], b) + (hot[j] - pal.light[j]) * min(1.0, beat))
                         for j in range(3))
            bass.fill_polys(c, [poly], col_)
            # sash frame: the meeting rail and the centre bar, flat ink
            c.rectangle(-hw, -2.5, 2 * hw, 5.0)
            c.rectangle(-1.5, -hh, 3.0, 2 * hh)
            c.set_source_rgb(*INK)
            c.fill()
        c.restore()
        if b > 0 and glow > 0:
            with f.emit() as g:
                g.rectangle(cx - hw * s, cy - hh * s, 2 * hw * s, 2 * hh * s)
                g.set_source_rgba(*pal.light, glow * min(1.0, 0.18 * b + 0.55 * beat))
                g.fill()
    # "I know every one of them": a counting glint runs over the forty windows
    for i in range(1, 41):
        g0 = W_["every"] + 0.018 * (i - 1)
        if g0 <= t < g0 + 0.2:
            a = 1.0 - (t - g0) / 0.2
            cx, cy, r, col = _rect(i)
            c.rectangle(cx - 50.0, cy - 62.0, 100.0, 124.0)
            c.set_source_rgba(*GLINT, 0.9 * a)
            c.set_line_width(3.0)
            c.stroke()


def _flip_glow(f, t, W_):
    """Halos of the lit windows during the venetian flip (once, squashed with their slat)."""
    on = _on_times(W_)
    for i in NIGHT:
        cx, cy, r, col = _rect(i)
        b, beat = _level(i, t, W_, on[i])
        p = _k(t, 4.40 + 0.11 * r, 0.34, "inout")
        if b <= 0 or p < 0.5:
            continue
        sy = -math.cos(math.pi * p)
        mid = (BANDS[r] + BANDS[r + 1]) / 2.0
        with f.emit() as g:
            g.rectangle(cx - 48.0, mid + (cy - 60.0 - mid) * sy, 96.0, 120.0 * sy)
            g.set_source_rgba(*f.pal.light, min(1.0, 0.18 * b))
            g.fill()


def _rain(c, f, t):
    dens = _k(t, 7.7, 0.6, "out3")
    if dens <= 0:
        return
    vx, vy = -300.0, 1650.0
    L0 = math.hypot(vx, vy)
    ux, uy = vx / L0, vy / L0
    c.set_line_width(2.0)
    for i in range(110):
        if hash01(17, i) > dens:
            continue
        x0 = hash01(17, i, 1) * (W + 500.0)
        y0 = hash01(17, i, 2) * (H + 600.0)
        sp = 0.8 + 0.4 * hash01(17, i, 3)
        x = (x0 + vx * sp * t) % (W + 500.0) - 100.0
        y = (y0 + vy * sp * t) % (H + 600.0) - 300.0
        L = 60.0 + 90.0 * hash01(17, i, 4)
        c.move_to(x, y)
        c.line_to(x + ux * L, y + uy * L)
        c.set_source_rgba(*f.pal.rain, 0.22 + 0.22 * hash01(17, i, 5))
        c.stroke()


# ----------------------------------------------------------------------------- scene
def render(f, t, T):
    W_ = _words(T)
    bass.bass_scene(f, field=PAPER, paper=0.75)
    with f.screen() as c:
        if t < 4.40:
            _paper(c, t, W_)
        elif t >= 5.52:
            _night(c, f, t, W_)
        else:
            # venetian flip, row band by row band, top to bottom
            bass.paper_field(c, INK)
            for i in range(8):
                a, b = BANDS[i], BANDS[i + 1]
                p = _k(t, 4.40 + 0.11 * i, 0.34, "inout")
                mid = (a + b) / 2.0
                c.save()
                c.rectangle(-10.0, a, W + 20.0, b - a)
                c.clip()
                sy = math.cos(math.pi * p) if p < 0.5 else -math.cos(math.pi * p)
                c.translate(0.0, mid)
                c.scale(1.0, max(sy, 1e-3))
                c.translate(0.0, -mid)
                c.rectangle(-10.0, a, W + 20.0, b - a)     # only this band's own slat turns
                c.clip()
                if p < 0.5:
                    _paper(c, t, W_)
                else:
                    _night(c, f, t, W_, glow=0.0)
                c.restore()
            _flip_glow(f, t, W_)
        _rain(c, f, t)


def cues(T):
    W_ = _words(T)
    return [
        Cue(0.02, "thin paper strips whisk in from the edges", -10, dur=1.0),
        Cue(0.30, "39 small paper taps, row by row (typewriter rhythm)", -8, dur=1.2),
        Cue(W_["forty"] - 0.24, "a paper card shoots along a rail", -6, dur=0.24),
        Cue(W_["forty"], "the last window lands: everything clicks tight (wooden clack)", -2),
        Cue(4.40, "venetian blind flip, eight slats top to bottom", -5, dur=1.1),
        Cue(5.02, "nine light switches / bulbs flickering on, scattered", -9, dur=0.75),
        Cue(W_["every"], "soft counting ticks across the windows", -14, dur=0.75),
        Cue(W_["heart"], "heartbeat: lub-dub", -3, dur=0.5),
        Cue(7.70, "rain begins: soft hiss on the street", -12, dur=1.8),
    ]
