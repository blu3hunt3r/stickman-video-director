"""His room (animator B): the Bass cut's amber stage, furnished.

The Bass cut's room shot (B.draw_room) is an amber field with an ink floor at y = 1560 and the
two figures at B.ROOM_FS. The full film furnishes it (one stage, used by s03, s04 and s09):

    his door        in the back wall, far left (off the quarrel's frame; s09 opens it)
    the phone table a little pedestal table, his rotary telephone on it, a chair tucked in
    the lamp        a pendant lamp over the middle of the room, its cone on the wall
    the counter     right of the victim; the knife lies on it, its handle toward the room

Everything is drawn in STAGE px (the Bass room's frame at zoom 1, y down): a shot places the
stage with `stage_cam(c, z, cx, cy)` (stage point (cx, cy) at the frame centre, zoom z).

    draw_wall(c)                 the amber field, the lamp's cone, the lamp
    draw_set(c, ...)             door, phone corner, counter (+ the knife on it, + its ring)
    draw_floor(c)                the ink floor
    knife(c, at, ang, s, ...)    THE knife: the Bass cut's blade (B._BLADE, the one in his fist
                                 in s04) on a full handle; `at` = the front of the grip
    phone_side(c, ...)           the telephone in profile; handset_side(c, ...) the handset

The quarrel's performances (mocap 80_48 for both) are here too, so the reflection in her eye
and the knife insert can show the room at any moment of s03.
"""
import math
from functools import lru_cache

import cairo

from engine import bass, mocap as mc, paperdoll as pd
from engine.core import clamp, hash01, lerp
from films.opposite_bass import world as B
from films.opposite_full import kit as K

INK, PAPER, AMBER, RED = K.INK, K.PAPER, K.AMBER, B.RED
W, H = K.W, K.H
FLOOR = B.ROOM_FLOOR
FS = B.ROOM_FS
MAN_X, VIC_X = B.MAN_X, B.VIC_X
k = B.k
twos = B.twos


def _sn(*a):
    return hash01(*a) * 2.0 - 1.0


def P(pts, dx=0.0, dy=0.0, s=1.0, seed=0, amp=0.5, max_len=40.0, sag=0.5):
    """A precisely cut piece: local points (scaled, moved) re-snipped by hand."""
    q = [(dx + x * s, dy + y * s) for x, y in pts]
    return bass.orient(bass.scissor(q, seed=seed, sag=sag, amp=amp, max_len=max_len, corner=38.0), True)


def R(x0, y0, x1, y1, seed=0, amp=0.6):
    return bass.orient(bass.cut_rect(x0, y0, x1, y1, seed=seed, amp=amp, seg=(30.0, 90.0)), True)


def stage_cam(c, z=1.0, cx=540.0, cy=960.0, rot=0.0):
    """Place the stage: stage point (cx, cy) at the frame centre, zoom z, roll rot deg."""
    c.translate(540.0, 960.0)
    if rot:
        c.rotate(math.radians(rot))
    c.scale(z, z)
    c.translate(-cx, -cy)


def cut_lines(c, lines, width=4.0, color=AMBER):
    """Seams: thin lines of light between two cut pieces of the same ink."""
    c.save()
    c.set_source_rgb(*color)
    c.set_line_width(width)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    for ln in lines:
        c.new_path()
        bass.draw.poly(c, ln, close=False)
        c.stroke()
    c.restore()


# ============================================================================ the layout (stage px)
DOOR = (-372.0, 618.0, -82.0, FLOOR)           # the doorway (x0, top, x1, floor)
LANDING_LIT = (0.80, 0.765, 0.70)              # the landing beyond it, its bare bulb on (s09)
LANDING_RAIL = (0.55, 0.52, 0.47)
TABLE_X = 168.0                                # the phone table's column
TABLE_TOP = FLOOR - 288.0                      # its top (62 cm)
PHONE_X = 160.0                                # the telephone's middle, on the table
CHAIR_X = 34.0                                 # the chair's middle (tucked in at the table, facing it)
LAMP = (560.0, 470.0)                          # the lamp's bulb
COUNTER_X0 = 818.0                             # the counter's left end (its top's nose)
COUNTER_TOP = 1150.0                           # the counter top
KNIFE_AT = (896.0, COUNTER_TOP - 10.5)         # the knife lying on the counter (its origin: the front of the grip)
KNIFE_S = 1.0                                  # knife units -> stage px on the counter
RING_C = (946.0, COUNTER_TOP - 14.0)           # the marker ring round it
RING_RX, RING_RY = 154.0, 54.0
RING_TILT, RING_SEED = -5.0, 3


# ============================================================================ the knife
# knife units: x along the blade from the middle of the grip, y down when the edge is down.
# The blade is the Bass cut's (the one in his fist in s04); the handle is the part his fist
# hides: a slim grip swelling to a rounded butt, a bolster, three rivets.
_HANDLE = [(-74.0, -6.0), (-70.0, -9.0), (-62.0, -10.0), (-40.0, -9.0), (-12.0, -9.0), (2.0, -10.0),
           (2.0, 10.0), (-12.0, 9.5), (-40.0, 9.5), (-60.0, 11.5), (-70.0, 11.0), (-75.0, 7.0), (-76.0, 1.0)]
_BOLSTER = [(2.0, -12.0), (15.5, -13.5), (15.5, 13.5), (2.0, 12.0)]
_RIVETS = ((-58.0, 0.5), (-36.0, 0.0), (-14.0, 0.0))


@lru_cache(maxsize=4)
def _knife_parts(seed=0):
    handle = P(_HANDLE, seed=900 + seed, amp=0.15, max_len=14.0, sag=0.2)
    bolster = bass.orient(_BOLSTER, True)
    return handle, bolster


def knife(c, at, ang=0.0, s=1.0, edge_w=None, blood=0.0, rivets=True, alpha=1.0, flip=False, outline=None,
          outline_w=4.0):
    """THE knife, the front of its grip (where the bolster begins) at `at`, the blade pointing
    `ang` deg (0 = +x), s units -> px.
    The blade is paper with an ink edge, the handle ink; blood (0..1) reddens the blade from
    the tip. flip mirrors it about its own axis (the edge up). outline: a colour laid round
    the whole knife (outline_w px), so its ink handle shows on an ink floor."""
    handle, bolster = _knife_parts()
    c.save()
    c.translate(*at)
    c.rotate(math.radians(ang))
    c.scale(s, -s if flip else s)
    if outline is not None:
        c.save()
        c.new_path()
        for p in (B._BLADE, handle, bolster):
            bass.draw.poly(c, p)
        c.set_source_rgb(*outline)
        c.set_line_width(2.0 * outline_w / s)
        c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.stroke()
        c.restore()
    px = edge_w if edge_w is not None else 3.0 * max(1.0, s) ** 0.7       # the blade's ink edge, in px
    B.edged(c, [B._BLADE], PAPER, INK, px / s)
    if blood > 0.0:
        c.save()
        c.new_path()
        bass.draw.poly(c, B._BLADE)
        c.clip()
        x0 = lerp(172.0, 60.0, clamp(blood))
        bass.fill_polys(c, [bass.orient([(x0, -20.0), (x0 + 30.0, -20.0), (180.0, -20.0), (180.0, 20.0),
                                         (x0 + 12.0, 20.0)], True)], RED)
        c.restore()
    bass.fill_polys(c, [handle, bolster], INK)
    if rivets and s >= 0.7:
        for i, (x, y) in enumerate(_RIVETS):
            bass.disc(c, (x, y), 2.6, AMBER if s < 2.0 else PAPER, seed=910 + i, n=14)
    c.restore()


_BUTT = [(-30.0, -9.0), (-24.0, -11.5), (-12.0, -11.0), (-6.0, -9.5), (-6.0, 9.5), (-12.0, 11.0), (-24.0, 12.5),
         (-31.0, 9.0), (-33.0, 1.0)]


def fist_knife(ang):
    """B.knife_hold for THIS knife (s04, the Bass knife shot): his fist round the grip, the blade
    (B._BLADE, as in the Bass cut) pointing at world angle `ang`, the bolster just out of the
    little-finger side of his fist and the rounded butt of the handle out of the thumb side."""
    butt = bass.orient(_BUTT, True)

    def fn(c, Hd):
        a = ang if Hd["facing"] > 0 else 180.0 - ang
        c.save()
        c.translate(*Hd["hc"])
        c.rotate(math.radians(a))
        B.edged(c, [B._BLADE], PAPER, INK, 7.0)
        bass.fill_polys(c, [bass.orient(_BOLSTER, True), butt, B._HILT], INK)
        c.restore()
    return fn


# ============================================================================ the set pieces
@lru_cache(maxsize=1)
def _counter_polys():
    x0, top = COUNTER_X0, COUNTER_TOP
    x1 = 1760.0
    slab = R(x0, top, x1, top + 20.0, seed=1201, amp=0.4)
    body = P([(x0 + 14.0, top + 18.0), (x1, top + 18.0), (x1, FLOOR - 40.0), (x0 + 30.0, FLOOR - 40.0),
              (x0 + 30.0, FLOOR), (x0 + 14.0, FLOOR)], seed=1202, amp=0.4)
    kick = R(x0 + 30.0, FLOOR - 40.0, x1, FLOOR, seed=1203, amp=0.3)
    return [slab, body, kick]


def counter_seams():
    """The counter's drawers and doors: seams of light through the ink, and their knobs."""
    x0, top = COUNTER_X0, COUNTER_TOP
    y_d = top + 86.0
    seams = [[(x0 + 22.0, y_d), (1760.0, y_d)],
             [(x0 + 22.0, FLOOR - 46.0), (1760.0, FLOOR - 46.0)],
             [(x0 + 170.0, y_d), (x0 + 170.0, FLOOR - 46.0)],
             [(x0 + 330.0, top + 26.0), (x0 + 330.0, FLOOR - 46.0)]]
    knobs = [(x0 + 96.0, top + 54.0), (x0 + 250.0, top + 54.0), (x0 + 150.0, y_d + 60.0), (x0 + 190.0, y_d + 60.0)]
    return seams, knobs


def draw_counter(c):
    bass.fill_polys(c, _counter_polys(), INK)
    seams, knobs = counter_seams()
    cut_lines(c, seams, 3.0)
    for i, p in enumerate(knobs):
        bass.disc(c, p, 6.0, AMBER, seed=1210 + i, n=12)


@lru_cache(maxsize=1)
def _table_polys():
    x, top = TABLE_X, TABLE_TOP
    s = [P([(x - 74.0, top), (x + 74.0, top), (x + 70.0, top + 13.0), (x - 70.0, top + 13.0)], seed=1301, amp=0.3),
         P([(x - 30.0, top + 13.0), (x + 30.0, top + 13.0), (x + 22.0, top + 24.0), (x - 22.0, top + 24.0)],
           seed=1302, amp=0.3),
         P([(x - 7.0, top + 22.0), (x + 7.0, top + 22.0), (x + 8.0, FLOOR - 56.0), (x + 13.0, FLOOR - 40.0),
            (x - 13.0, FLOOR - 40.0), (x - 8.0, FLOOR - 56.0)], seed=1303, amp=0.3),
         # the tripod: two feet splayed out, a third toward us (a stub)
         P([(x - 13.0, FLOOR - 46.0), (x - 64.0, FLOOR - 8.0), (x - 70.0, FLOOR), (x - 58.0, FLOOR),
            (x - 2.0, FLOOR - 30.0)], seed=1304, amp=0.3),
         P([(x + 13.0, FLOOR - 46.0), (x + 64.0, FLOOR - 8.0), (x + 70.0, FLOOR), (x + 58.0, FLOOR),
            (x + 2.0, FLOOR - 30.0)], seed=1305, amp=0.3)]
    return s


# --- the telephone (a 1950s desk set), in profile, facing +x: phone units = px at s 1
_BASE = [(-50.0, 0.0), (-52.0, -10.0), (-50.0, -28.0), (-44.0, -40.0), (-30.0, -46.0), (14.0, -46.0), (30.0, -40.0),
         (44.0, -26.0), (52.0, -8.0), (54.0, 0.0)]
_PRONGS = [[(-34.0, -45.0), (-30.0, -54.0), (-24.0, -55.0), (-21.0, -45.0)],
           [(18.0, -45.0), (21.0, -55.0), (27.0, -54.0), (31.0, -44.0)]]


def handset_pts(L=110.0):
    """The handset in profile, in handset units: the handle along +x from the earpiece's middle
    (0, 0) to the mouthpiece's (L, 0); both cups hang below it (y down), the mouthpiece tipped
    toward the mouth."""
    ear = [(-16.0, -6.0), (-12.0, -11.0), (14.0, -11.0), (24.0, -8.0), (L - 22.0, -8.0), (L - 12.0, -11.0),
           (L + 14.0, -11.0), (L + 18.0, -6.0), (L + 20.0, 4.0), (L + 16.0, 18.0), (L + 6.0, 22.0),
           (L - 14.0, 20.0), (L - 20.0, 8.0), (L - 24.0, 2.0), (24.0, 2.0), (18.0, 8.0), (14.0, 20.0),
           (-8.0, 22.0), (-16.0, 18.0), (-19.0, 6.0)]
    return ear


@lru_cache(maxsize=8)
def _handset_poly(L, seed):
    return P(handset_pts(L), seed=seed, amp=0.2, max_len=10.0, sag=0.25)


def handset_side(c, at, ang=0.0, s=1.0, L=110.0, seed=1400, color=INK, edge=None, edge_w=6.0):
    """The handset in profile: earpiece middle at `at`, the handle pointing ang deg."""
    c.save()
    c.translate(*at)
    c.rotate(math.radians(ang))
    c.scale(s, s)
    poly = _handset_poly(L, seed)
    if edge is not None:
        B.edged(c, [poly], color, edge, edge_w / s)
    else:
        bass.fill_polys(c, [poly], color)
    c.restore()


def coil(a, b, turns=9, amp=6.0, sag=18.0):
    """A coiled telephone cord from a to b as a zigzag polyline sagging under its weight."""
    pts = []
    n = turns * 2
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    for i in range(n + 1):
        u = i / n
        s = amp * (1 if i % 2 else -1) if 0 < i < n else 0.0
        y_sag = sag * math.sin(math.pi * u)
        pts.append((a[0] + dx * u + nx * s, a[1] + dy * u + ny * s + y_sag))
    return pts


def phone_side(c, foot, s=1.0, handset=True, cord_to=None, facing=1):
    """The telephone in profile standing at `foot` (the middle of its base on the table)."""
    c.save()
    c.translate(*foot)
    c.scale(s * facing, s)
    bass.fill_polys(c, [P(_BASE, seed=1410, amp=0.2, max_len=12.0, sag=0.25)] + [bass.orient(p, True) for p in _PRONGS],
                    INK)
    # the dial's rim, a sliver on the sloped front
    bass.fill_polys(c, [bass.orient([(36.0, -34.0), (46.0, -26.0), (52.0, -12.0), (47.0, -10.0), (41.0, -24.0),
                                     (32.0, -31.0)], True)], INK)
    cut_lines(c, [[(33.0, -33.0), (44.0, -22.0), (49.0, -10.0)]], 2.0)
    if handset:
        handset_side(c, (-47.0, -52.0), 0.0, 0.92, L=106.0)
    # the cord: from the back of the base, a few coils down to the table
    c.set_source_rgb(*INK)
    c.set_line_width(2.6)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.new_path()
    end = cord_to if cord_to is not None else (-80.0, 0.0)
    bass.draw.poly(c, coil((-50.0, -14.0), end, turns=6, amp=4.0, sag=10.0), close=False)
    c.stroke()
    c.restore()


@lru_cache(maxsize=2)
def _chair_polys(over=False):
    """The chair in profile facing +x (toward the table), its middle at x 0, on the floor 0.
    Overturned, it lies on its back where it fell, the legs in the air."""
    parts = [
        # the back post: the back leg running up into the back, raked
        [(-78.0, 0.0), (-66.0, 0.0), (-66.0, -208.0), (-72.0, -300.0), (-84.0, -414.0), (-98.0, -412.0),
         (-86.0, -300.0), (-80.0, -208.0)],
        # the seat
        [(-82.0, -210.0), (88.0, -210.0), (92.0, -200.0), (88.0, -194.0), (-80.0, -194.0)],
        # the front leg
        [(72.0, -196.0), (84.0, -196.0), (82.0, 0.0), (70.0, 0.0)],
        # the stretcher
        [(-66.0, -82.0), (72.0, -82.0), (72.0, -76.0), (-66.0, -76.0)],
        # the back rails, seen end on
        [(-92.0, -404.0), (-74.0, -406.0), (-70.0, -372.0), (-88.0, -370.0)],
        [(-86.0, -330.0), (-70.0, -332.0), (-68.0, -308.0), (-84.0, -306.0)],
    ]
    out = []
    for i, p in enumerate(parts):
        if over:
            # fallen backward about the foot of the back leg, then settled on the back rail
            ang = math.radians(-78.0)
            px, py = -72.0, 0.0
            ca, sa = math.cos(ang), math.sin(ang)
            p = [(px + (x - px) * ca - (y - py) * sa, py + (x - px) * sa + (y - py) * ca) for x, y in p]
        out.append(p)
    if over:
        ymax = max(y for p in out for x, y in p)
        out = [[(x, y - ymax) for x, y in p] for p in out]
    return [P(p, seed=1500 + i, amp=0.3, max_len=30.0) for i, p in enumerate(out)]


def chair(c, x, over=False, s=FS * 0.86):
    c.save()
    c.translate(x, FLOOR)
    c.scale(s, s)
    bass.fill_polys(c, _chair_polys(over), INK)
    c.restore()


CHAIR_OVER_X = 760.0                           # where the chair lies after the killing (knocked over, on its
                                               # back between the table and the counter: x 272..719)


def draw_phone_corner(c, chair_state="up", handset=True):
    """The pedestal table with the telephone; the chair tucked in at it ("up"), or knocked
    over and lying on its back on the floor out in the room ("over"), or gone (None)."""
    if chair_state == "up":
        chair(c, CHAIR_X)
    elif chair_state == "over":
        chair(c, CHAIR_OVER_X, over=True)
    bass.fill_polys(c, _table_polys(), INK)
    if chair_state == "up":
        # the seat runs in under the table top: one seam of light keeps them apart
        cut_lines(c, [[(TABLE_X - 74.0, TABLE_TOP + 14.5), (CHAIR_X + 80.0 * FS * 0.86, TABLE_TOP + 14.5)]], 3.0)
    phone_side(c, (PHONE_X, TABLE_TOP), s=1.0, handset=handset, cord_to=(-86.0, 26.0))


def draw_door(c, open_u=0.0, beyond=None, lit=False):
    """His door in the back wall: frame, two panels, the knob. open_u (0..1) swings the leaf in
    (it narrows toward its hinge on the left), opening on the landing: dark, or lit by its
    bare bulb (lit: a pale field a figure stands black against); beyond(c, rect) draws
    whoever stands in the doorway (clipped to it)."""
    x0, y0, x1, y1 = DOOR
    fr = 18.0
    # the frame: an ink architrave
    bass.fill_polys(c, [P([(x0 - fr, y1), (x0 - fr, y0 - fr), (x1 + fr, y0 - fr), (x1 + fr, y1), (x1, y1),
                           (x1, y0), (x0, y0), (x0, y1)], seed=1601, amp=0.4, max_len=60.0)], INK)
    if open_u > 0.0:
        # the landing beyond: its bulb, and the stair rail going up
        far, rail_c = (LANDING_LIT, LANDING_RAIL) if lit else (K.DEEP, K.SHUT)
        bass.fill_polys(c, [R(x0, y0, x1, y1, seed=1602, amp=0.3)], far)
        bx = lerp(x0, x1, 0.22 if lit else 0.62)
        c.save()
        B.clip_rect(c, (x0, y0, x1, y1))
        bass.fill_polys(c, [bass.orient([(bx - 1.5, y0), (bx + 1.5, y0), (bx + 1.5, y0 + 70.0), (bx - 1.5, y0 + 70.0)],
                                        True)], rail_c)
        if lit:
            bass.disc(c, (bx, y0 + 80.0), 30.0, PAPER, seed=1605, n=28, alpha=0.5)
            bass.disc(c, (bx, y0 + 80.0), 13.0, PAPER, seed=1603, n=18)
        else:
            bass.fill_polys(c, [bass.orient([(bx - 80.0, y0 + 70.0), (bx + 80.0, y0 + 70.0), (bx + 340.0, y1 + 40.0),
                                             (bx - 340.0, y1 + 40.0)], True)], AMBER, 0.07)
            bass.disc(c, (bx, y0 + 78.0), 9.0, AMBER, seed=1603, n=16)
        # the banister: a rail climbing away to the left, its balusters
        rail = [(x1 + 10.0, y1 - 250.0), (x0 - 10.0, y1 - 520.0)]
        bass.line_band(c, rail, rail_c, width=10.0, seed=1604)
        for j in range(7):
            u = (j + 0.5) / 7.0
            px, py = lerp(rail[0][0], rail[1][0], u), lerp(rail[0][1], rail[1][1], u)
            bass.fill_polys(c, [R(px - 3.0, py, px + 3.0, py + 210.0 + 40.0 * u, seed=1610 + j, amp=0.2)], rail_c)
        if beyond is not None:
            beyond(c, (x0, y0, x1, y1))
        c.restore()
    # the leaf: swinging in on its left hinge, seen narrowing (a cut-paper door turns on twos)
    wl = (x1 - x0) * math.cos(math.radians(84.0 * clamp(open_u)))
    if wl > 2.0:
        lx1 = x0 + wl
        bass.fill_polys(c, [R(x0, y0, lx1, y1, seed=1620, amp=0.4)], INK)
        f = wl / (x1 - x0)
        seams = [[(x0 + 34.0 * f, y0 + 50.0), (lx1 - 34.0 * f, y0 + 50.0), (lx1 - 34.0 * f, y0 + 420.0),
                  (x0 + 34.0 * f, y0 + 420.0), (x0 + 34.0 * f, y0 + 50.0)],
                 [(x0 + 34.0 * f, y0 + 500.0), (lx1 - 34.0 * f, y0 + 500.0), (lx1 - 34.0 * f, y1 - 60.0),
                  (x0 + 34.0 * f, y1 - 60.0), (x0 + 34.0 * f, y0 + 500.0)]]
        if f > 0.25:
            cut_lines(c, seams, 3.0)
        bass.disc(c, (lx1 - 30.0 * f, y0 + 470.0), 8.0, AMBER, seed=1621, n=14)


def lamp_cone(c, alpha=0.085):
    """The lamp's light on the wall: a flat cone of paper light, from the shade to the floor."""
    x, y = LAMP
    bass.fill_polys(c, [bass.orient([(x - 46.0, y + 6.0), (x + 46.0, y + 6.0), (x + 520.0, FLOOR),
                                     (x - 520.0, FLOOR)], True)], PAPER, alpha)


def draw_lamp(c, swing=0.0):
    """A pendant lamp: the flex down from the ceiling, a cut tin shade, the bulb under it."""
    x, y = LAMP
    c.save()
    c.translate(x, -400.0)
    c.rotate(math.radians(swing))
    c.translate(-x, 400.0)
    bass.fill_polys(c, [bass.orient([(x - 2.0, -400.0), (x + 2.0, -400.0), (x + 2.0, y - 70.0), (x - 2.0, y - 70.0)], True),
                        P([(x - 12.0, y - 74.0), (x + 12.0, y - 74.0), (x + 16.0, y - 58.0), (x + 70.0, y - 6.0),
                           (x + 74.0, y + 2.0), (x - 74.0, y + 2.0), (x - 70.0, y - 6.0), (x - 16.0, y - 58.0)],
                          seed=1701, amp=0.3, max_len=24.0)], INK)
    c.save()
    c.new_path()
    c.rectangle(x - 80.0, y + 1.0, 160.0, 60.0)
    c.clip()
    bass.disc(c, (x, y + 2.0), 21.0, PAPER, seed=1702, n=28)
    c.restore()
    c.restore()


def draw_wall(c, lamp=True, cone=True):
    B.fill(c, AMBER)
    if cone:
        lamp_cone(c)


def draw_set(c, door=0.0, beyond=None, chair_state="up", knife_on=True, handset=True, lamp=True, counter=True,
             door_lit=False):
    """Everything standing against the back wall, behind the figures."""
    draw_door(c, door, beyond, lit=door_lit)
    draw_phone_corner(c, chair_state, handset=handset)
    if counter:
        draw_counter(c)
    if knife_on:
        knife(c, KNIFE_AT, 0.0, KNIFE_S)
    if lamp:
        draw_lamp(c)


def draw_floor(c):
    bass.fill_polys(c, [bass.cut_rect(-1400.0, FLOOR, 2600.0, H + 1400.0, seed=51, amp=2.0)], INK)


def stage(c, z=1.0, cx=600.0, cy=1080.0, rot=0.0, figures=None, after=None, door=0.0, beyond=None,
          chair_state="up", knife_on=True, handset=True, lamp=True, ring_u=0.0, ring_w=14.0):
    """The whole room through the stage camera: wall, set, figures(c) (stage px, in front of
    the set), the floor, the ring round the knife, then after(c) (the annotations)."""
    c.save()
    stage_cam(c, z, cx, cy, rot)
    draw_wall(c)
    draw_set(c, door, beyond, chair_state, knife_on, handset, lamp)
    if figures is not None:
        figures(c)
    draw_floor(c)
    if ring_u > 0.0:
        ring(c, ring_u, width=ring_w)
    if after is not None:
        after(c)
    c.restore()


def placed(p, fx, s=FS, floor=FLOOR):
    """A point in figure units (of a figure placed at fx on the floor, scale s) -> stage px."""
    return (fx + p[0] * s, floor + p[1] * s)


def shifted(st, dx):
    """A walker state moved dx along the floor (pelvis and feet)."""
    out = dict(st)
    P = st["pelvis"]
    out["pelvis"] = (P[0] + dx, P[1])
    out["feet"] = {k_: (f[0] + dx, f[1], f[2]) for k_, f in st["feet"].items()}
    return out


def ring(c, u, center=RING_C, rx=RING_RX, ry=RING_RY, width=14.0, alpha=1.0):
    """The red marker ring round the knife (u 0..1 draws it on)."""
    K.marker_ring(c, center, rx, ry, u, RED, width=width, tilt=RING_TILT, seed=RING_SEED, alpha=alpha)


_TURNS, _START = 1.16, -128.0         # K.marker_ring's stroke: one loop and a bit, from upper left, clockwise


def marker_arc(center, rx, ry, a0, a1, width=14.0, tilt=RING_TILT, seed=RING_SEED, turns=_TURNS, start=_START):
    """A piece of the finished marker ring (exactly K.marker_pts' stroke, same samples and
    noise), from stroke angle a0 to a1 (deg along the stroke, 0 .. 360 * turns): the ring cut
    apart. Its ends are square: snipped, not drawn."""
    total = 360.0 * turns
    n = int(total / 4.0)
    ca, sa = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))

    def sample(a, i):
        f = a / total
        g = 1.0 + 0.085 * f + 0.022 * math.sin(math.radians(2.0 * a) + seed) + 0.004 * _sn(seed, i, 3)
        th = math.radians(start + a)
        x, y = rx * g * math.cos(th), ry * g * math.sin(th)
        w = width * (0.22 + 0.78 * math.sin(math.pi * f) ** 0.45) + 0.6 * _sn(seed, i, 4)
        return (center[0] + x * ca - y * sa, center[1] + x * sa + y * ca), w

    a0, a1 = clamp(a0, 0.0, total), clamp(a1, 0.0, total)
    if a1 - a0 < 1.0:
        return []
    i0 = int(math.ceil(a0 / total * n))
    i1 = int(math.floor(a1 / total * n))
    pts, ws = [], []
    p, w = sample(a0, max(i0 - 1, 0))
    pts.append(p)
    ws.append(w)
    for i in range(i0, i1 + 1):
        a = total * i / n
        if a0 < a < a1:
            p, w = sample(a, i)
            pts.append(p)
            ws.append(w)
    p, w = sample(a1, i1)
    pts.append(p)
    ws.append(w)
    return bass.orient(bass.draw.ribbon(pts, ws), True)


def ring_halves(center=RING_C, rx=RING_RX, ry=RING_RY, width=14.0, split=(-90.0, 90.0)):
    """The finished ring cut in two at the angles `split` (deg on the ellipse, y down: -90 the
    top, 90 the bottom): (left half, right half), each a list of ribbon pieces (the stroke
    crosses the cuts more than once: one loop and a bit)."""
    total = 360.0 * _TURNS
    cuts = sorted({a for s in split for a in ((s - _START) % 360.0 + 360.0 * j for j in range(3)) if 0.0 < a < total})
    bounds = [0.0] + cuts + [total]
    left, right = [], []
    for a0, a1 in zip(bounds, bounds[1:]):
        if a1 - a0 < 1.0:
            continue
        mid = math.radians(_START + 0.5 * (a0 + a1) + RING_TILT)
        piece = marker_arc(center, rx, ry, a0, a1, width)
        if piece:
            (left if math.cos(mid) < 0.0 else right).append(piece)
    return left, right


# ============================================================================ the figures' faces
def head_point(fig, st, pose, facing, gap, local):
    """A point of the head (figure units, pelvis frame, unturned) where draw_cutout puts it:
    turned with the head about the neck, lifted by the gap, leaned, faced."""
    P0 = st["pelvis"]
    P0 = (P0[0], P0[1] + pose.crouch)
    q = pd._rot((local[0] - fig.neck[0], local[1] - fig.neck[1]), -pose.head)
    q = (q[0] + fig.neck[0], q[1] + fig.neck[1] - gap * 1.2)
    q = pd._rot(q, pose.lean)
    return (P0[0] + facing * q[0], P0[1] + q[1])


def eye_point(fig, st, pose, facing, gap):
    return head_point(fig, st, pose, facing, gap, fig.eye[0])


def cheek_point(fig, st, pose, facing, gap):
    (ex, ey), _, _ = fig.eye
    return head_point(fig, st, pose, facing, gap, (ex - 6.0, ey + 24.0))


# ============================================================================ the quarrel (s03)
@lru_cache(maxsize=1)
def quarrel_perfs():
    """Both of them arguing (80_48), offset so they never mirror each other. s03 time."""
    C = mc.Clip.load
    her, man, vic = B.figs()
    man_p = mc.Performance(man, [
        mc.Seg(C("80_48"), 0.9, 5.9, at=0.0, speed=1.0),
        mc.Seg(C("80_48"), 8.55, 9.45, at=5.25, speed=0.32, blend=0.35),          # still: he has seen it
    ], facing=1, near="Left")
    vic_p = mc.Performance(vic, [
        mc.Seg(C("80_48"), 0.2, 6.4, at=0.0, speed=1.0),
        mc.Seg(C("80_48"), 8.6, 9.4, at=6.4, speed=0.3, blend=0.3),
    ], facing=-1, near="Left")
    return man_p, vic_p


# ============================================================================ after the killing (s09)
# She lies on her back where she fell, downstage of the phone table, her head toward the door:
# her near arm flung out along the floor over her head (toward the door and the phone), her
# near knee up under the full skirt, her hair spread on the floor, her eyes shut. One flat
# body of cut paper (Anatomy of a Murder), each piece edged: drawn in LYING units (her figure
# units, laid down): x along the floor toward her feet, y up (negative), the floor at y = 0.
LIE_X = 687.0                  # her pelvis (stage px): she lies under the lamp
LIE_Y = FLOOR + 360.0          # the floor under her: downstage, well in front of the back wall
LIE_S = FS * 1.2               # nearer us, so a little larger than a figure at the wall
LIE_PELVIS = (0.0, -35.0)      # her pelvis above the floor (lying units)
LIE_TILT = 14.0                # her head tipped back (deg), chin up
LIE_GAP = 8.0                  # the paper between the pieces (lying units)
LIE_KNEE_FOOT = 176.0          # the near foot, planted (its knee up)
LIE_ARM = ((-350.0, -13.0), (-449.0, -9.0))    # far elbow, wrist: flung out along the floor over her head
LIE_NEAR_ARM = ((-138.0, -16.0), (-58.0, -76.0))   # near elbow, wrist: her hand on her stomach
POOL = (-64.0, 100.0, 30.0)    # the pool (lying units along her, stage px): x, half-length, half-depth
FLOOR_KNIFE = (96.0, LIE_Y + 150.0, 12.0)      # the knife where it fell: grip front (stage x, y), angle


def _lay(p):
    """A point of the standing figure (figure units, pelvis frame) laid on her back."""
    return (p[1] + LIE_PELVIS[0], -p[0] + LIE_PELVIS[1])


def _xfm(pts, ang, piv, at):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(at[0] + (x - piv[0]) * ca - (y - piv[1]) * sa, at[1] + (x - piv[0]) * sa + (y - piv[1]) * ca)
            for x, y in pts]


def _floored(pts, y_max=-0.5):
    return [(x, min(y, y_max)) for x, y in pts]


def lying_hand(wr, u, curl=0.0):
    """Her open hand on the floor, palm up, the fingers loosely curled (curl 0..1 closes them
    further): lying units, the wrist at wr, pointing along u (the fingers' way)."""
    n = (u[1], -u[0])                     # 'up' off the floor for a hand pointing left
    if n[1] > 0.0:
        n = (-n[0], -n[1])
    c1 = 1.0 + 0.6 * curl
    loc = [(0.0, 6.5), (12.0, 7.5), (22.0, 7.5), (32.0, 6.5), (40.0, 3.0 - 2.0 * curl),
           (44.0 - 6.0 * curl, -3.0 * c1), (42.0 - 7.0 * curl, -8.0 * c1), (37.0 - 5.0 * curl, -6.0 * c1),
           (31.0 - 2.0 * curl, -3.0 - 2.0 * curl), (24.0, -4.5), (18.0, -9.0), (13.0, -14.5), (8.0, -14.0),
           (6.0, -8.0), (0.0, -6.5)]
    return [(wr[0] + u[0] * x + n[0] * y, wr[1] + u[1] * x + n[1] * y) for x, y in loc]


@lru_cache(maxsize=4)
def lying_pieces(curl=0.0):
    """Her body as cut pieces, back to front: [(name, polygon)], lying units."""
    v = B.figs()[2]
    g = LIE_GAP
    out = []
    # the head, tipped back about the neck, lifted to rest on the floor, a gap off the neck
    neck = _lay(v.neck)
    head = _xfm(v.head[0][0], -90.0 - LIE_TILT, v.neck, (neck[0] - g * 1.2, neck[1]))
    lift = max(0.0, max(y for _, y in head) + 1.0)
    head = [(x, y - lift) for x, y in head]
    hx = sum(x for x, _ in head) / len(head)
    hair = _floored(_xfm(v.head[1][0], -90.0 - LIE_TILT, v.neck, (neck[0] - g * 1.2, neck[1] - lift)))
    # her long hair, spread on the floor round her crown and away past it in loose waves
    spill = [(hx + 30.0, 0.0), (hx + 18.0, -10.0), (hx - 10.0, -24.0), (hx - 30.0, -42.0), (hx - 46.0, -52.0),
             (hx - 60.0, -47.0), (hx - 72.0, -35.0), (hx - 88.0, -30.0), (hx - 102.0, -35.0), (hx - 117.0, -27.0),
             (hx - 131.0, -15.0), (hx - 144.0, -13.0), (hx - 156.0, -5.0), (hx - 162.0, 0.0)]
    out.append(("hair_spill", P(spill, seed=1801, amp=0.4, max_len=16.0)))
    # her far arm, flung out along the floor over her head: behind her head, over her hair
    sh = _lay(v.shoulder)
    el, wr = LIE_ARM
    aw0, aw1, aw2 = v.arm_w
    a2, b2 = B._shorten(sh, el, g)
    out.append(("upper_far", bass.orient(bass.capsule_pts(a2, b2, aw0 / 2, aw1 / 2, cap=8), True)))
    a2, b2 = B._shorten(el, wr, g)
    out.append(("fore_far", bass.orient(bass.capsule_pts(a2, b2, aw1 / 2, aw2 / 2, cap=8), True)))
    d = math.dist(el, wr)
    u = ((wr[0] - el[0]) / d, (wr[1] - el[1]) / d)
    out.append(("hand_far", bass.orient(lying_hand((wr[0] + u[0] * g * 0.6, wr[1] + u[1] * g * 0.6), u, curl), True)))
    out.append(("hair", hair))
    # the far leg, straight along the floor; its shin and foot show past the skirt
    fk, fa = (152.0, -17.0), (277.0, -15.0)
    a2, b2 = B._shorten(fk, fa, g)
    out.append(("shin_far", bass.orient(bass.capsule_pts(a2, b2, 10.5, 7.5, cap=8), True)))
    foot = _xfm(v.foot, -72.0, (0.0, 0.0), (fa[0] + g * 0.6, fa[1]))
    out.append(("foot_far", bass.orient(_floored(foot), True)))
    # her near knee is up: the dress (bodice and full skirt, one piece, as she wears it) runs
    # from her shoulders over the bust, tents from the hip over that knee, falls from it to the
    # floor in a drape, and lies low over the far knee
    hip = (LIE_PELVIS[0] - 4.0, LIE_PELVIS[1])
    ank = (LIE_KNEE_FOOT, -v.ankle)
    knee, _ = pd.ik2(hip, ank, v.thigh, v.shin, forward=1.0)
    if knee[1] > hip[1]:                       # (the IK picks the knee up; make sure)
        knee = (knee[0], 2.0 * hip[1] - knee[1])
    kx, ky = knee
    dress = [(-262.0, -1.0), (-265.0, -44.0), (-254.0, -58.0), (-238.0, -69.0), (-220.0, -79.0), (-204.0, -84.0),
             (-189.0, -81.0), (-175.0, -72.0), (-158.0, -65.0), (-132.0, -61.0), (-110.0, -62.0), (-84.0, -72.0),
             (-50.0, -83.0), (-10.0, -99.0), (kx - 60.0, ky + 28.0), (kx - 22.0, ky - 4.0), (kx - 2.0, ky - 18.0),
             (kx + 14.0, ky - 16.0), (kx + 24.0, ky + 4.0), (kx + 27.0, ky + 20.0), (kx + 15.0, ky + 32.0),
             (kx + 3.0, ky + 56.0), (kx - 9.0, ky + 86.0), (kx - 14.0, ky + 106.0), (kx + 14.0, -31.0),
             (kx + 36.0, -29.0), (kx + 48.0, -17.0), (kx + 51.0, -1.0)]
    out.append(("dress", P(dress, seed=1813, amp=0.45, max_len=22.0)))
    # the neck, arched (her head is tipped back)
    out.append(("neck", P([(-252.0, -12.0), (-254.0, -44.0), (-296.0, -54.0), (-298.0, -20.0)], seed=1814,
                          amp=0.3, max_len=20.0)))
    a2, b2 = B._shorten((kx + 6.0, ky + 6.0), ank, g)
    w0, w1, w2 = v.leg_w
    out.append(("shin_near", bass.orient(bass.capsule_pts(a2, b2, w1 / 2 + 1.0, w2 / 2, cap=8), True)))
    nf = [(ank[0] + x, ank[1] + y + g * 0.6) for x, y in v.foot]
    out.append(("foot_near", bass.orient(_floored(nf), True)))
    out.append(("head", head))
    # her near arm: down along her side, the forearm up over her, the hand on her stomach
    el, wr = LIE_NEAR_ARM
    a2, b2 = B._shorten(sh, el, g)
    out.append(("upper_near", bass.orient(bass.capsule_pts(a2, b2, aw0 / 2, aw1 / 2, cap=8), True)))
    a2, b2 = B._shorten(el, wr, g)
    out.append(("fore_near", bass.orient(bass.capsule_pts(a2, b2, aw1 / 2, aw2 / 2, cap=8), True)))
    hand = [(wr[0] + 2.0, wr[1] + 3.0), (wr[0] + 8.0, wr[1] - 9.0), (wr[0] + 20.0, wr[1] - 15.0),
            (wr[0] + 36.0, wr[1] - 20.0), (wr[0] + 44.0, wr[1] - 21.0), (wr[0] + 46.0, wr[1] - 16.0),
            (wr[0] + 40.0, wr[1] - 11.0), (wr[0] + 26.0, wr[1] - 5.0), (wr[0] + 14.0, wr[1] + 4.0)]
    out.append(("hand_near", bass.orient(hand, True)))
    return tuple(out)


def lying_point(p):
    """A point of her (lying units) -> stage px."""
    return (LIE_X + p[0] * LIE_S, LIE_Y + p[1] * LIE_S)


def lying_anchors():
    """Stage px of her head, face, near hand (wrist), and pelvis."""
    pieces = dict(lying_pieces())
    hd = pieces["head"]
    hx = sum(x for x, _ in hd) / len(hd)
    hy = sum(y for _, y in hd) / len(hd)
    top = min(hd, key=lambda q: q[1])
    return {"head": lying_point((hx, hy)), "face": lying_point(top), "wrist": lying_point(LIE_ARM[1]),
            "hand": lying_point((LIE_ARM[1][0] - 22.0, LIE_ARM[1][1])), "pelvis": lying_point(LIE_PELVIS)}


def draw_lying(c, rim=AMBER, rim_w=7.0, color=INK, curl=0.0, skip=()):
    """Her, lying (stage px): every piece laid on over an edge of `rim` (rim_w lying units
    wide, half of it showing), so she reads on the ink floor and the light alike."""
    c.save()
    c.translate(LIE_X, LIE_Y)
    c.scale(LIE_S, LIE_S)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    for name, poly in lying_pieces(round(curl, 3)):
        if name in skip:
            continue
        if rim is not None:
            c.new_path()
            bass.draw.poly(c, poly)
            c.set_source_rgb(*rim)
            c.set_line_width(rim_w)
            c.stroke()
        bass.fill_polys(c, [poly], color)
    c.restore()


def pool(c, u=1.0):
    """The small flat red pool on the floor at her side, spread from under her (u 0..1)."""
    if u <= 0.0:
        return
    x, rx, ry = POOL
    cx, cy = lying_point((x, 0.0))
    rx, ry = rx * LIE_S * (0.35 + 0.65 * u), ry * (0.5 + 0.5 * u)
    pts = []
    for i in range(44):
        a = 2.0 * math.pi * i / 44.0
        w = 1.0 + 0.07 * math.sin(3.0 * a + 0.6) + 0.05 * math.sin(5.0 * a + 2.1)
        pts.append((cx + rx * w * math.cos(a), cy + ry * 0.55 + ry * w * math.sin(a)))
    bass.fill_polys(c, [P(pts, seed=1802, amp=0.3, max_len=24.0)], RED)


def floor_knife(c, s=1.15, outline=AMBER):
    """The knife on the floor where it fell, its blade red to the bolster."""
    x, y, a = FLOOR_KNIFE
    knife(c, (x, y), a, s, blood=1.0, outline=outline, outline_w=3.0)
