"""DOUBLE CROSS, the OPPOSITE cut: the crew's room (the tenement's storey 4).

The room is the SECTION's storey-4 room seen close, the way OPPOSITE's full cut sees her room: the
stage is the section itself under a zoom, so s01's push-in arrives on the same room the stage
shows, and the floors above and below are the section's own rooms with their neighbours asleep.

  * STAGE (profile): `draw_stage(c, t, cam, ...)`. The door to the stairs in the left wall, the
    window in the right; the table (its chair at the left end), the pendant lamp over it with its
    pull cord, the wall clock top left. The crew are DOUBLE CROSS's cast at `St.FIG_S` in section
    px, drawn by the caller's `crew(c, rect)` (inside the room, before its walls); `overlay(c)`
    draws over everything, still in section px (annotations that ride the set).
  * WINDOW VIEW (face on from inside, over her shoulder, s02): `window_view(c, t, ...)`. The
    bank across the street through the crew's window (`St.bank_front`, the road seen from above),
    the window's frame, and her head and shoulders from behind (`her_back`).

Cameras are (centre, zoom) pairs in section px, eased with `cam_lerp`:
    S01_END   the section at 3.2x on the room: where s01's push-in ends and s02 begins
    STAGE     the room wall to wall
    TABLE     close on the table and the three round it
Marks (section px, feet on `FLOOR`): KNIGHT_WALL, KNIGHT_TABLE, CRACKER_SEAT, HER_WINDOW,
HER_TABLE; TABLE_X / TABLE_TOP; `plan_on_table(c, u, lit)` the plan spread on it (edge on).
"""
import math
from functools import lru_cache

import cairo

from engine import bass, paperdoll as pd
from engine.core import clamp, ease, lerp
from films.double_cross_opposite import bank as Bk
from films.double_cross_opposite import cast as C
from films.double_cross_opposite import kit as K
from films.double_cross_opposite import street as St

W, H = K.W, K.H
INK, PAPER, AMBER, RED, NIGHT, STEEL, DEEP = K.INK, K.PAPER, K.AMBER, K.RED, K.NIGHT, K.STEEL, K.DEEP

ROOM = St.TEN.room(St.CREW_FLOOR)                 # (130, 560, 296, 756)
FLOOR = ROOM[3]
CENTRE = ((ROOM[0] + ROOM[2]) / 2.0, (ROOM[1] + ROOM[3]) / 2.0)
WINDOW = St.TEN.window(St.CREW_FLOOR)
DOOR = St.TEN.door(St.CREW_FLOOR)

S01_END = (CENTRE, 3.2)
STAGE = ((CENTRE[0] + 4.0, CENTRE[1] + 10.0), 5.6)
TABLE = ((ROOM[0] + 90.0, FLOOR - 70.0), 7.4)

TABLE_X = ROOM[0] + 84.0                          # the table's middle
TABLE_HALF = 34.0 * 0.9
TABLE_TOP = FLOOR - 50.0 * 0.9                    # its top surface
KNIGHT_WALL = ROOM[0] + 16.0                      # leaning by the door
KNIGHT_TABLE = ROOM[0] + 30.0                     # at the table's end, behind the Cracker
CRACKER_SEAT = ROOM[0] + 46.0                     # the chair at the table's left end (he faces right)
HER_WINDOW = ROOM[2] - 16.0                       # at the glass, facing right
HER_TABLE = TABLE_X + TABLE_HALF + 10.0           # the table's right end, facing left


def cam_lerp(a, b, u):
    """Ease between two (centre, zoom) cameras: the zoom geometric, the centre weighted by how far
    the zoom has gone (an aimed push)."""
    (ac, az), (bc, bz) = a, b
    z = math.exp(lerp(math.log(az), math.log(bz), u))
    if abs(bz - az) < 1e-6:
        w = u
    else:
        w = (1.0 / z - 1.0 / az) / (1.0 / bz - 1.0 / az)
    return (lerp(ac[0], bc[0], w), lerp(ac[1], bc[1], w)), z


def to_frame(p, cam):
    (cx, cy), z = cam
    return St.to_frame(p, (cx, cy), z)


def plan_on_table(c, u, lit=True):
    """The plan on the table, edge on: rolled up at her end (u 0) .. spread flat (u 1)."""
    if u <= 0.0:
        return
    x0, x1 = TABLE_X - TABLE_HALF + 3.0, TABLE_X + TABLE_HALF - 3.0
    g = ease("out3", clamp(u))
    roll_x = lerp(x1 - 2.0, x0 + 1.0, g)
    col = PAPER if lit else lerp(DEEP, PAPER, 0.3)
    bass.fill_polys(c, [St._r(roll_x, TABLE_TOP - 1.6, x1, TABLE_TOP + 0.2, 1601, 0.1)], col)
    if g < 0.98:
        K.dot(c, (roll_x, TABLE_TOP - 2.6), 2.6 * (1.0 - 0.6 * g) + 0.6, col, seed=1602)


def draw_stage(c, t, cam=STAGE, lit=True, swing=1.5, pull=0.0, clock=(11, 58), crew=None, plan=0.0,
               neighbours="asleep", overlay=None, lamp_col=None, field=NIGHT, others=None, lit_extra=None, **kw):
    """The crew's room as the section shows it, through camera cam ((centre, zoom), section px).
    t is FILM time (the lamp's swing, the drips, the breathing carry across the cuts).
    lit: their lamp on; swing: its sway (deg); pull: the cord drawn down; crew(c, rect): draws
    the three; neighbours: the other rooms' folk state ('asleep' | 'up' | 'woken' | None);
    others(c, where, n, rect): draws everyone else yourself instead (every people call but the
    crew's room); lit_extra: more lit rooms for St.draw_section's `lit`; **kw: St.draw_section's
    other keywords (car, beams, sky_lit, moon_at, numbers, gold_glow, ...)."""
    (cx, cy), z = cam
    c.save()
    St.zoom_on(c, (cx, cy), z)

    def people(cc, where, n, rect):
        if where == "ten" and n == St.CREW_FLOOR:
            plan_on_table(cc, plan, lit)
            if crew is not None:
                crew(cc, rect)
        elif others is not None:
            others(cc, where, n, rect)
        elif where == "ten" and neighbours is not None:
            St.neighbour(cc, n, t, neighbours)

    lit_map = {("ten", St.CREW_FLOOR): AMBER} if lit else {}
    if neighbours in ("up", "woken") and others is None:
        lit_map.update({("ten", n): AMBER for n in (2, 3, 5)})
    if lit_extra:
        lit_map.update(lit_extra)
    lamp = (lit, swing, pull) if lamp_col is None else (lit, swing, pull, lamp_col)
    args = dict(car=dict(lights=0.6), beams={St.CREW_FLOOR} if lit else False)
    args.update(kw)
    St.draw_section(c, t, lit=lit_map, people=people, crew_lamp=lamp, clock=clock, field=field, **args)
    if overlay is not None:
        overlay(c)
    c.restore()


# ---------------------------------------------------------------------------- the crew at rest
SEAT_PX = 35.0 * 0.9                              # chair_l's seat height (section px)


def seated(who, facing=1, seat_px=SEAT_PX, s=St.FIG_S, reach=0.95):
    """A state for a cast member sitting on a seat seat_px high (px at scale s), feet planted forward."""
    f = C.fig(who)
    seat = seat_px / s
    fx = facing * reach * f.thigh
    return dict(pelvis=(0.0, -seat - 20.0), feet={"near": (fx + facing * 8.0, 0.0, 0.0), "far": (fx - facing * 8.0, 0.0, 0.0)},
                phase=0.0, speed=0.0, run=0.0, stride=0.0)


def on_table(x, at, lift=0.0):
    """An ik target (figure units, from the figure's floor point at x) on the table top at room x `at`."""
    return ((at - x) / St.FIG_S, (TABLE_TOP - 1.5 - lift - FLOOR) / St.FIG_S)


def crew_rest(c, t, rect, lit=True):
    """Where s01's push-in finds them and s02 begins (t: film time): the Knight leaning by the door,
    smoking; the Cracker in his chair at the table's end, his hands on it; her at the window,
    looking out. Returns their joints {'knight', 'cracker', 'architect'}."""
    fy = rect[3]
    L = AMBER if lit else None
    tt = K.twos(t)
    out = {}
    pose = pd.Pose(lean=-5.0, head=-3.0, arms={"near": ("ang", -6.0, 16.0), "far": ("ang", 4.0, 12.0)})
    out["knight"] = St.fig(c, "knight", C.standing("knight"), pose, KNIGHT_WALL, fy, 1, L)
    C.cigarette(c, out["knight"], t, St.FIG_S, facing=1)
    nod = 2.5 * math.sin(2.0 * math.pi * 0.25 * tt)
    pose = pd.Pose(lean=14.0, head=-12.0 + nod, arms={"near": ("ik", on_table(CRACKER_SEAT, TABLE_X - 14.0)),
                                                      "far": ("ik", on_table(CRACKER_SEAT, TABLE_X - 22.0))})
    out["cracker"] = St.fig(c, "cracker", seated("cracker"), pose, CRACKER_SEAT, fy, 1, L)
    pose = pd.Pose(head=2.0, lean=2.0, arms={"near": ("ang", 8.0, 16.0), "far": ("ang", 3.0, 10.0)})
    out["architect"] = St.fig(c, "architect", C.standing("architect"), pose, HER_WINDOW, fy, 1, L)
    return out


def lamp_cord(t, swing=1.5, pull=0.0):
    """(shade, cord end) of the crew's lamp in section px, without drawing it."""
    a = math.radians(swing * math.sin(2.0 * math.pi * 0.5 * t))
    top = St.LAMP_TOP
    p = (top[0] + St.LAMP_LEN * math.sin(a), top[1] + St.LAMP_LEN * math.cos(a))
    L = St.CORD_LEN + 6.0 * clamp(pull)
    ca, sa = math.cos(-a), math.sin(-a)
    ex, ey = 11.0, 13.0 + L
    return p, (p[0] + ex * ca - ey * sa, p[1] + ex * sa + ey * ca)


# ============================================================================ the window view (over her shoulder)
WIN = (96.0, 250.0, 1010.0, 1392.0)               # the glass, frame px (face on, from inside)
WIN_MULLION = 722.0                               # the casement bar (between the bank's wing and portico)
WIN_TRANSOM = 430.0                               # the transom bar (over the pediment)
OTS_CAM = Bk.Cam(370.0, -250.0, 0.96)             # the bank across the street, seen through it
OTS_MOON = (880.0, 330.0)                         # the moon in the transom light (frame px)
HER_NAPE = (205.0, 1640.0)                        # her, from behind, in the corner of the frame
HER_S = 1.3
GUARD_FLOOR = -40.0                               # where the guard's feet go behind the wing's windows


def ots_to_frame(p):
    return OTS_CAM.to_frame(p)


@lru_cache(maxsize=1)
def _wing_windows():
    """The wing's three window shapes and their bars (set px), from Bk._wing()."""
    out = Bk._wing()
    return out[3][0], out[4][0]


def guard_behind(c, t, gx, facing=1):
    """The guard passing behind the wing's barred windows (set px): his cap and shoulders low in
    the windows, the patch of his flashlight thrown on the wall ahead of him. Clipped to the
    windows, the bars over him."""
    wins, bars = _wing_windows()
    c.save()
    c.new_path()
    for w in wins:
        bass.draw.poly(c, w)
    c.clip()
    bob = 1.6 * math.sin(2.0 * math.pi * 1.0 * K.twos(t))
    K.dot(c, (gx + facing * 74.0, -286.0), 50.0, PAPER, seed=1630, alpha=0.30)
    K.dot(c, (gx + facing * 74.0, -286.0), 26.0, PAPER, seed=1631, alpha=0.30)
    st = C.standing("guard")
    pose = pd.Pose(lean=4.0, arms={"near": ("ang", 70.0, 10.0)})
    C.draw(c, "guard", st, pose, gx, GUARD_FLOOR + bob, s=0.34, facing=facing, bg=St.LOW_LAMP, rim_w=2.4)
    c.restore()
    bass.fill_polys(c, bars, lerp(STEEL, INK, 0.25))


def _glass_polys():
    x0, y0, x1, y1 = WIN
    return [(x0, y0, WIN_MULLION - 9.0, WIN_TRANSOM - 9.0), (WIN_MULLION + 9.0, y0, x1, WIN_TRANSOM - 9.0),
            (x0, WIN_TRANSOM + 9.0, WIN_MULLION - 9.0, y1), (WIN_MULLION + 9.0, WIN_TRANSOM + 9.0, x1, y1)]


def window_view(c, t, guard_x=None, guard_facing=1, bell_ring=0.0, clock=(11, 58), lit=True, inside=None, look=None,
                her=None, lamp_on=1.0, car=True):
    """Face on to the crew's window from inside: the bank across the street through it (the road
    seen from above), the frame, the lit wall round it.
      inside(c): drawn over the view, clipped to the glass (frame px; set points via ots_to_frame);
      look(c):   drawn over the frame, under her (sight lines leave from behind her head);
      her(c):    drawn last (`her_back`)."""
    wall = AMBER if lit else DEEP
    K.fill(c, wall)
    x0, y0, x1, y1 = WIN
    c.save()
    c.rectangle(x0, y0, x1 - x0, y1 - y0)
    c.clip()
    K.fill(c, NIGHT)
    K.moon(c, OTS_MOON, 46.0)

    def extra(cc):
        if guard_x is not None:
            guard_behind(cc, t, guard_x, guard_facing)

    St.bank_front(c, OTS_CAM, t, clock=clock, bell_ring=bell_ring, low=1.0, guard_x=None, road="above",
                  lamp_on=lamp_on, moon=False, sky=None, extra=extra, car=car)
    if inside is not None:
        inside(c)
    # the glass: the lamp's warm reflection on it, two faint streaks
    for g in _glass_polys():
        poly = bass.orient([(g[0], g[1]), (g[2], g[1]), (g[2], g[3]), (g[0], g[3])], True)
        bass.fill_polys(c, [poly], AMBER if lit else STEEL, 0.10 if lit else 0.05)
        c.save()
        c.rectangle(g[0], g[1], g[2] - g[0], g[3] - g[1])
        c.clip()
        for o, w in ((0.20, 34.0), (0.34, 12.0)):
            ox = lerp(g[0], g[2], o)
            bass.fill_polys(c, [bass.orient([(ox, g[1]), (ox + w, g[1]), (ox + w - 220.0, g[3]), (ox - 220.0, g[3])], True)],
                            PAPER, 0.045)
        c.restore()
    c.restore()
    # the casing, the casement bar and the transom, the sill
    frame = lerp(INK, wall, 0.10)
    polys = [St._r(x0 - 30.0, y0 - 30.0, x1 + 30.0, y0, 1610, 0.6), St._r(x0 - 30.0, y1, x1 + 30.0, y1 + 22.0, 1611, 0.6),
             St._r(x0 - 30.0, y0, x0, y1, 1612, 0.6), St._r(x1, y0, x1 + 30.0, y1, 1613, 0.6),
             St._r(WIN_MULLION - 9.0, y0, WIN_MULLION + 9.0, y1, 1614, 0.4),
             St._r(x0, WIN_TRANSOM - 9.0, x1, WIN_TRANSOM + 9.0, 1615, 0.4),
             St._r(x0 - 56.0, y1 + 22.0, x1 + 56.0, y1 + 46.0, 1616, 0.5)]
    bass.fill_polys(c, polys, frame)
    if look is not None:
        look(c)
    if her is not None:
        her(c)


# --- her head and shoulders from behind (OPPOSITE's draw_back, cut for the Architect: the hair
# swept back smooth into a low chignon with the pencil through it, the trench coat's collar
# turned up). Local units: origin at the nape, y down; s = 1: a head about 206 px high.
def _sym(half):
    return half + [(-x, y) for x, y in reversed(half)]


_PROFILE = ((-57.0, -73.0), (-94.0, -42.0), (-99.0, -10.0), (-122.0, 26.0), (-96.0, 36.0), (-101.0, 55.0), (-91.0, 68.0),
            (-94.0, 83.0), (-68.0, 104.0), (-31.0, 94.0))      # brow, nose, lips, chin: offsets from the head's centre
HEAD_C = (0.0, -182.0)
HEAD_R = (92.0, 104.0)


def _her_back_polys(turn):
    g = ease("inout", clamp(turn))
    hx = -14.0 * g
    cx, cy = hx + HEAD_C[0], HEAD_C[1]
    shoulders = _sym([(-40.0, -12.0), (-100.0, 8.0), (-168.0, 34.0), (-216.0, 64.0), (-238.0, 120.0), (-246.0, 300.0),
                      (-252.0, 660.0)])
    collar = [(-98.0, 30.0), (-96.0, -30.0), (-88.0, -88.0), (-50.0, -82.0), (-10.0, -74.0), (0.0, -66.0), (10.0, -74.0),
              (50.0, -82.0), (88.0, -88.0), (96.0, -30.0), (98.0, 30.0)]
    head = [(cx + HEAD_R[0] * math.cos(math.radians(a)) * (1.0 - 0.06 * math.sin(math.radians(a))),
             cy + HEAD_R[1] * math.sin(math.radians(a))) for a in range(0, 360, 10)]
    body = [shoulders, collar, head]
    if g > 0.01:
        face = []
        for ox, oy in _PROFILE:
            yy = clamp(oy / HEAD_R[1], -0.98, 0.98)
            ex = -HEAD_R[0] * 0.92 * math.sqrt(1.0 - yy * yy)
            face.append((cx + lerp(ex, ox, g), cy + oy))
        body.append([(cx - 30.0, cy - 80.0)] + face + [(cx - 20.0, cy + 90.0)])
    bun_c = (cx * 0.6 + 4.0, -112.0)
    bun = [(bun_c[0] + 50.0 * math.cos(math.radians(a)), bun_c[1] + 36.0 * math.sin(math.radians(a))) for a in range(0, 360, 12)]
    pencil = [(bun_c[0] - 100.0, bun_c[1] - 44.0), (bun_c[0] + 94.0, bun_c[1] + 36.0)]
    lines = [[(bun_c[0] - 30.0, bun_c[1] - 8.0), (bun_c[0], bun_c[1] - 20.0), (bun_c[0] + 32.0, bun_c[1] - 4.0)],
             [(bun_c[0] - 22.0, bun_c[1] + 12.0), (bun_c[0] + 6.0, bun_c[1] + 3.0), (bun_c[0] + 28.0, bun_c[1] + 16.0)],
             [(0.0, -66.0), (0.0, -24.0)]]
    sweep = [[(cx - 44.0, cy - 84.0), (cx - 40.0, cy - 30.0), (bun_c[0] - 34.0, bun_c[1] - 28.0)],
             [(cx + 40.0, cy - 88.0), (cx + 38.0, cy - 30.0), (bun_c[0] + 30.0, bun_c[1] - 30.0)]]
    eye = (cx - 62.0, cy - 16.0)
    return body, bun, pencil, lines, sweep, g, eye, (cx, cy)


def her_back(c, base=HER_NAPE, s=HER_S, turn=0.0, edge=PAPER, t=0.0, color=INK):
    """Her head and shoulders from behind, nape at `base` (px), scale s. turn 0..1 turns her
    head to her left (frame left, toward the room): her profile comes round. Breathes on twos.
    Returns {'head': the head's centre, 'r': its radius (px), 'nape', 'eye'} (px)."""
    body, bun, pencil, lines, sweep, g, eye, hc = _her_back_polys(turn)
    br = 1.0 + 0.006 * math.sin(2.0 * math.pi * 0.22 * K.twos(t))
    m = cairo.Matrix()
    m.translate(*base)
    m.scale(s, s * br)

    def cut(pts, seed):
        q = [m.transform_point(*p) for p in pts]
        return bass.orient(bass.scissor(q, seed=seed, sag=0.45, amp=0.25, max_len=40.0, corner=40.0), True)

    K.edged(c, [cut(p, 1640 + i) for i, p in enumerate(body)], color, edge, 5.0)

    def stroke(pts_list, w, alpha=1.0):
        c.save()
        c.set_source_rgba(*edge, alpha)
        c.set_line_width(w)
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        for ln in pts_list:
            c.new_path()
            bass.draw.poly(c, [m.transform_point(*p) for p in ln], close=False)
            c.stroke()
        c.restore()

    stroke(sweep, max(1.5, 2.2 * s), 0.55)
    K.edged(c, [cut(bun, 1648)], color, edge, 4.0)
    a, b = m.transform_point(*pencil[0]), m.transform_point(*pencil[1])
    bass.line_band(c, [a, b], edge, width=15.0 * s + 5.0, seed=1650)
    bass.line_band(c, [a, b], color, width=15.0 * s, seed=1651)
    stroke(lines, max(2.0, 3.0 * s))
    e = m.transform_point(*eye)
    if g > 0.55:
        K.dot(c, e, 9.0 * s * clamp((g - 0.55) / 0.3), PAPER, seed=1652)
    hcx, hcy = m.transform_point(*hc)
    return {"head": (hcx, hcy), "r": HEAD_R[0] * s, "nape": tuple(base), "eye": e}


def her_marks(base=HER_NAPE, s=HER_S, turn=0.0):
    """her_back's marks without drawing (for looks drawn under her head)."""
    g = ease("inout", clamp(turn))
    cx = -14.0 * g + HEAD_C[0]
    return {"head": (base[0] + cx * s, base[1] + HEAD_C[1] * s), "r": HEAD_R[0] * s, "nape": tuple(base)}


def look_from_head(mk, target, inset=0.55):
    """Where a look leaves her head toward target (behind the head: drawn under it)."""
    (hx, hy), r = mk["head"], mk["r"]
    dx, dy = target[0] - hx, target[1] - hy
    d = math.hypot(dx, dy) or 1.0
    return (hx + dx / d * r * inset, hy + dy / d * r * inset)
