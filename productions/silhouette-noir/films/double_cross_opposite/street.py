"""DOUBLE CROSS, the OPPOSITE cut: the street, the diagram the heist is drawn on.

One street, seen the ways OPPOSITE sees its street:

  * SECTION (`draw_section`, frame px, no camera): the street cut across like a doll's house.
    Left, the TENEMENT: five storeys, the stairs up the far side, a room per storey facing the
    street (the crew's is storey 4), the street door on storey 1, the water tank on the roof.
    Right, the BANK: one tall HALL on the ground floor (the HATCH in the dark corner by the street
    wall, the guard's desk and lamp in the middle, crates and the cat) and the VAULT at its far
    end behind thick walls and the round door (the gold, the deposit boxes on its far wall, the
    floor tile over the trapdoor); two dark office storeys above; the cornice and the pitched roof
    (the pediment's line). In the bank's street wall, the SIDE DOOR, and the ALARM BELL high over
    it outside. Between them the street: the tenement's curb with the lamp, MANHOLE B by that
    curb, MANHOLE A in the road, the Knight's CAR end-on at the bank's curb, the GULLY grating
    beside its tyre. Under it all, the SEWER: one tunnel from under manhole B to under the vault,
    and the shafts up to manhole B, manhole A, the gully, the hatch (and, once `trap_shaft`, the
    trapdoor she cut).
  * ELEVATION (`draw_elevation`, frame px): the two fronts flat on the night field with the
    same x layout and outlines, the street a gap between them: the tenement's windows (the crew's
    at storey 4, nearest the street), the bank's rusticated base with its barred windows (lit low
    by the guard's lamp), the side door and the bell, the colonnade, the pediment and its clock.
  * The FRONTS, face on, in set px for a `Bk.Cam` (y up is negative, the road at 0, figures at
    `Bk.FIG_S`): `bank_front` (from the crew's window, s02; the side door's BANG, s07; the
    arrest, s10) and `tenement_front` (from the bank's curb, s10). Cars in profile: `car_side`.

Figures in the section are DOUBLE CROSS's cast at `FIG_S` (about 140 px tall): `fig(...)`.
Neighbours are OPPOSITE's folk: `neighbour(...)`. Scenes zoom into the section with
`zoom_on(c, p, z)`.
"""
import math
from contextlib import contextmanager
from functools import lru_cache

from engine import bass, draw
from engine import paperdoll as pd
from engine.core import clamp, ease, hash01, lerp
from films.double_cross_opposite import bank as Bk
from films.double_cross_opposite import cast as C
from films.double_cross_opposite import kit as K
from films.opposite_full import folk as FO

W, H = K.W, K.H
INK, PAPER, AMBER, RED = K.INK, K.PAPER, K.AMBER, K.RED
NIGHT, STEEL, DEEP, SHUT, POLICE = K.NIGHT, K.STEEL, K.DEEP, K.SHUT, K.POLICE

DARK_INK = lerp(DEEP, INK, 0.6)              # furniture and people in a dark room
DOOR_LEAF = lerp(INK, STEEL, 0.32)           # a shut door, seen cut
SLAB_CUT = lerp(INK, STEEL, 0.30)            # the road slab, cut
TUNNEL = NIGHT                               # the sewer's air
LINING = lerp(NIGHT, STEEL, 0.55)
WATER_EDGE = lerp(STEEL, NIGHT, 0.35)
IRON = STEEL
RAIL = lerp(STEEL, NIGHT, 0.4)
HEAVY = INK                                  # the vault's walls, cut
LINE_V = lerp(STEEL, INK, 0.35)              # the steel lining on their inside faces
STONE = STEEL
STONE_SH = lerp(STEEL, NIGHT, 0.5)
STONE_DK = lerp(STEEL, INK, 0.5)
FACE_TONE = lerp(INK, STEEL, 0.22)           # the bank's classical members on the elevation
GOLD_ROOM = lerp(AMBER, INK, 0.55)           # the vault's inside in the gold's light
GOLD_BOX = lerp(AMBER, INK, 0.30)
GOLD_SEAM = lerp(AMBER, INK, 0.72)
BOX_DARK = lerp(DEEP, STEEL, 0.22)
GLASS = lerp(NIGHT, STEEL, 0.25)
LOW_LAMP = lerp(INK, AMBER, 0.42)            # a window lit low by the guard's lamp

FIG_S = 0.2                                  # cast figure units -> section px

# ============================================================================ levels
GROUND = 1400.0                              # street level
FH = 212.0                                   # the tenement's floor to floor
SLAB = 16.0
WALL = 14.0
STAIR_W = 92.0
CREW_FLOOR = 4
FEET = GROUND - SLAB / 2.0                   # where feet stand on a ground floor (both buildings)


def level(n):
    """y of the floor of the tenement's storey n (1 = the street floor)."""
    return GROUND - (n - 1) * FH


class Building:
    """The tenement in section (OPPOSITE's Building on this street's ground). side +1: the
    street is on its right. The stairs run up the side away from the street; the rooms face it,
    each with a window in the street wall and a door into the stairwell."""

    def __init__(self, x0, x1, floors, side, seed):
        self.x0, self.x1, self.floors, self.side, self.seed = x0, x1, floors, side, seed
        self.roof = level(floors + 1)
        if side > 0:
            self.stair = (x0 + WALL, x0 + WALL + STAIR_W)
            self.part = (self.stair[1], self.stair[1] + WALL)
            self.rooms = (self.part[1], x1 - WALL)
            self.street = (x1 - WALL, x1)
        else:
            self.stair = (x1 - WALL - STAIR_W, x1 - WALL)
            self.part = (self.stair[0] - WALL, self.stair[0])
            self.rooms = (x0 + WALL, self.part[0])
            self.street = (x0, x0 + WALL)

    @property
    def face(self):
        return self.x1 if self.side > 0 else self.x0

    def room(self, n):
        """Inside of storey n's room: (x0, y0, x1, y1)."""
        return (self.rooms[0], level(n + 1) + SLAB / 2, self.rooms[1], level(n) - SLAB / 2)

    def floor_y(self, n):
        return level(n) - SLAB / 2

    def window(self, n):
        """The window opening in the street wall of storey n."""
        return (self.street[0], level(n + 1) + 58.0, self.street[1], level(n) - 44.0)

    def door(self, n):
        return (self.part[0], self.floor_y(n) - 136.0, self.part[1], self.floor_y(n))

    def street_door(self):
        return (self.street[0], GROUND - 150.0, self.street[1], GROUND - SLAB / 2)

    def landing(self, n):
        x = self.stair[1] - 20.0 if self.side > 0 else self.stair[0] + 20.0
        return (x, self.floor_y(n))

    def mid(self, n):
        x = self.stair[0] + 20.0 if self.side > 0 else self.stair[1] - 20.0
        return (x, self.floor_y(n) - FH / 2.0)

    def stair_route(self, n0, n1):
        """Where feet go up (or down) the stairs from storey n0's landing to storey n1's."""
        pts = []
        lo, hi = min(n0, n1), max(n0, n1)
        for n in range(lo, hi):
            pts += [self.landing(n), self.mid(n)]
        pts.append(self.landing(hi))
        return pts if n0 <= n1 else pts[::-1]


TEN = Building(10.0, 310.0, 5, +1, seed=600)

# ============================================================================ the street
STREET = (TEN.x1, 620.0)                     # the gap between the fronts
CURB = 34.0
CURB_H = 10.0
ROAD = (STREET[0] + CURB, STREET[1] - CURB)  # (344, 586)
LAMP_X = STREET[0] + 18.0                    # the lamp post, on the tenement's sidewalk
LAMP_HEAD = (LAMP_X + 44.0, GROUND - 322.0)  # its lantern, out over the road
MH_B = 372.0                                 # manhole B, in the road by the tenement's curb
MH_A = 446.0                                 # manhole A, in the road
MH_R = 24.0                                  # half a manhole's opening
CAR = (476.0, 570.0)                         # the Knight's car, end-on, at the bank's curb
CAR_C = (CAR[0] + CAR[1]) / 2.0
GULLY = (572.0, 586.0)                       # the gully grating by its tyre, at the bank's curb
GULLY_C = (GULLY[0] + GULLY[1]) / 2.0

# ============================================================================ the bank
BANK = (620.0, 1070.0)
BW = 18.0                                    # its street wall
HALL_H = 230.0                               # the hall, floor to floor
HALL = (BANK[0] + BW, 866.0)                 # the hall's inside, x
BANK_FLOORS = 3


def bank_level(n):
    """y of the floor of the bank's storey n (1 = the hall)."""
    return GROUND if n <= 1 else GROUND - HALL_H - (n - 2) * FH


BANK_ROOF = bank_level(BANK_FLOORS + 1)      # 746
CORNICE = 30.0
PED_APEX = (845.0, BANK_ROOF - CORNICE - 106.0)
VAULT = (866.0, 1070.0)                      # the vault, outer
VW = 26.0
VAULT_IN = (VAULT[0] + VW, VAULT[1] - VW)    # (892, 1044)
VAULT_TOP = bank_level(2) + 34.0             # the inside of its ceiling (a thick slab under the hall's)
VSLAB = 32.0                                 # the vault's floor slab (y FEET .. FEET + VSLAB)
VDOOR = (VAULT[0], GROUND - 178.0, VAULT[0] + VW, FEET)     # the round door's slot in the vault's wall
SIDE_DOOR = (BANK[0], GROUND - 150.0, BANK[0] + BW, FEET)
BELL = (BANK[0] - 15.0, bank_level(2) + 34.0)              # the alarm bell, outside, high over the side door
HATCH = (650.0, 698.0)                       # the hatch in the hall's floor, by the street wall
HATCH_C = (HATCH[0] + HATCH[1]) / 2.0
DESK_X = 776.0                               # the guard's desk (its middle)
GUARD_LAMP = (DESK_X - 18.0, FEET - 46.0 * 0.9)     # the desk lamp's foot on the desk top
CRATES = ((816.0, FEET - 34.0, 846.0, FEET), (847.0, FEET - 34.0, 864.0, FEET), (820.0, FEET - 62.0, 852.0, FEET - 34.0))
CAT_SEAT = (842.0, FEET - 62.0)
TILE = (996.0, 1032.0)                       # the floor tile over the trapdoor
TRAP_C = (TILE[0] + TILE[1]) / 2.0
GOLD_STACKS = (906.0, 934.0, 962.0)          # the gold, three stacks on the vault's floor
BOX_GRID = (976.0, VAULT_TOP + 14.0, 1040.0, VAULT_TOP + 124.0)   # the deposit boxes on its far wall
BOX_COLS, BOX_ROWS = 4, 5
RUBY_BOX = (0, 2)                            # (col, row) of the box with the ruby

# ============================================================================ underground
ROAD_SLAB = 18.0
CROWN, INVERT, WATER = 1610.0, 1780.0, 1758.0
TUNNEL_X = (334.0, VAULT_IN[1])
SEWER_FEET = INVERT - 8.0                    # where feet stand, wading
RUNG_STEP = 30.0
SHAFTS = {                                   # (x0, x1, top): the inside of each shaft
    "b": (MH_B - MH_R, MH_B + MH_R, GROUND),
    "a": (MH_A - MH_R, MH_A + MH_R, GROUND),
    "gully": (GULLY[0] + 2.0, GULLY[1] - 2.0, GROUND),
    "hatch": (HATCH[0], HATCH[1], GROUND + SLAB / 2),
    "trap": (TRAP_C - MH_R, TRAP_C + MH_R, FEET + VSLAB),
}


def shaft_rect(name):
    """The inside of a shaft down to the tunnel's floor (x0, y0, x1, y1): clip a climber to it."""
    x0, x1, top = SHAFTS[name]
    return (x0, top - 600.0, x1, INVERT)


def open_rects(trap_shaft=False, above=True):
    """Where a figure underground can be seen: the tunnel and the shafts (and everything above
    the ground if `above`). Clip to these with `clip_open`."""
    out = [(-100.0, -100.0, W + 100.0, GROUND)] if above else []
    out.append((TUNNEL_X[0], CROWN, TUNNEL_X[1], INVERT + 4.0))
    for k, (x0, x1, top) in SHAFTS.items():
        if k == "trap" and not trap_shaft:
            continue
        out.append((x0, top - 4.0, x1, CROWN + 2.0))
    return out


@contextmanager
def clip_open(c, trap_shaft=False, above=True):
    c.save()
    c.new_path()
    for x0, y0, x1, y1 in open_rects(trap_shaft, above):
        c.rectangle(x0, y0, x1 - x0, y1 - y0)
    c.clip()
    try:
        yield c
    finally:
        c.restore()


# ============================================================================ routes (where feet go)
STREET_CROSS = [(TEN.x1 + 8.0, GROUND), (MH_A - 30.0, GROUND)]
WAY_IN = [(MH_A, GROUND), (MH_A, SEWER_FEET), (HATCH_C, SEWER_FEET), (HATCH_C, FEET), (HALL[0] + 30.0, FEET)]
TO_VAULT = [(HALL[0] + 30.0, FEET), (VAULT[0] - 10.0, FEET)]
HIS_OUT = [(VAULT[0] - 10.0, FEET), (HALL[0] + 6.0, FEET), (BANK[0] - 10.0, GROUND), (CAR[1] + 8.0, GROUND)]
HER_OUT = [(TRAP_C, FEET), (TRAP_C, SEWER_FEET), (MH_B, SEWER_FEET), (MH_B, GROUND + 36.0)]

PLACES = {
    "crew_room": TEN.room(CREW_FLOOR), "crew_window": TEN.window(CREW_FLOOR), "crew_floor": TEN.floor_y(CREW_FLOOR),
    "street_door": (TEN.x1, GROUND), "lamp": LAMP_HEAD, "mh_b": (MH_B, GROUND), "mh_a": (MH_A, GROUND),
    "car": (CAR_C, GROUND - 50.0), "gully": (GULLY_C, GROUND), "side_door": ((SIDE_DOOR[0] + SIDE_DOOR[2]) / 2.0, GROUND - 75.0),
    "bell": BELL, "hatch": (HATCH_C, FEET), "desk": (DESK_X, FEET), "guard": (DESK_X + 22.0, FEET), "cat": CAT_SEAT,
    "vault_door": (VAULT[0] + VW / 2.0, GROUND - 90.0), "gold": (GOLD_STACKS[1], FEET - 22.0),
    "vault": ((VAULT_IN[0] + VAULT_IN[1]) / 2.0, (VAULT_TOP + FEET) / 2.0), "tile": (TRAP_C, FEET),
}


def box_rect(col, row):
    x0, y0, x1, y1 = BOX_GRID
    w, h = (x1 - x0) / BOX_COLS, (y1 - y0) / BOX_ROWS
    return (x0 + col * w + 1.5, y0 + row * h + 1.5, x0 + (col + 1) * w - 1.5, y0 + (row + 1) * h - 1.5)


PLACES["ruby"] = ((box_rect(*RUBY_BOX)[0] + box_rect(*RUBY_BOX)[2]) / 2.0, (box_rect(*RUBY_BOX)[1] + box_rect(*RUBY_BOX)[3]) / 2.0)


# ============================================================================ small helpers
def _r(x0, y0, x1, y1, seed, amp=0.5):
    return bass.cut_rect(x0, y0, x1, y1, seed=seed, amp=amp)


def zoom_on(c, p, z, at=(W / 2.0, H / 2.0)):
    """Transform c so section point p lands at frame point `at`, magnified z times."""
    c.translate(at[0], at[1])
    c.scale(z, z)
    c.translate(-p[0], -p[1])


def to_frame(p, centre, z, at=(W / 2.0, H / 2.0)):
    """Where section point p lands under zoom_on(c, centre, z, at)."""
    return (at[0] + z * (p[0] - centre[0]), at[1] + z * (p[1] - centre[1]))


def fig(c, who, st, pose, x, floor_y, facing=1, lit=None, s=FIG_S, rim=None, **kw):
    """A cast member in the section, standing on floor_y. lit: the light of the place they
    stand in (their edge colour), or None for the dark (DEEP)."""
    bg = lit if lit is not None else DEEP
    return C.draw(c, who, st, pose, x, floor_y, s=s, facing=facing, bg=bg, rim=rim, rim_w=2.4, **kw)


# ============================================================================ furniture
def _furn(kind, x, fy, s=1.0):
    """OPPOSITE's cut-paper furniture at room x on floor fy (unscaled px, y up negative)."""
    def P(pts):
        return bass.orient([(x + px * s, fy + py * s) for px, py in pts], True)
    if kind == "lamp":
        return [P([(-3, 0), (3, 0), (3, -96), (-3, -96)]), P([(-18, -96), (18, -96), (11, -124), (-11, -124)]),
                P([(-14, 0), (14, 0), (10, -6), (-10, -6)])]
    if kind == "table":
        return [P([(-34, -44), (34, -44), (34, -50), (-34, -50)]), P([(-30, 0), (-25, 0), (-25, -44), (-30, -44)]),
                P([(25, 0), (30, 0), (30, -44), (25, -44)])]
    if kind == "desk":
        return [P([(-34, -44), (34, -44), (34, -50), (-34, -50)]), P([(-32, 0), (-6, 0), (-6, -44), (-32, -44)]),
                P([(26, 0), (31, 0), (31, -44), (26, -44)])]
    if kind == "chair":
        return [P([(-12, -30), (12, -30), (12, -35), (-12, -35)]), P([(-12, 0), (-8, 0), (-8, -30), (-12, -30)]),
                P([(8, 0), (12, 0), (12, -72), (8, -72)])]
    if kind == "chair_l":                        # a chair with its back to the left
        return [P([(-12, -30), (12, -30), (12, -35), (-12, -35)]), P([(8, 0), (12, 0), (12, -30), (8, -30)]),
                P([(-12, 0), (-8, 0), (-8, -72), (-12, -72)])]
    if kind == "armchair":
        return [P([(-30, 0), (30, 0), (30, -30), (24, -36), (24, -64), (14, -70), (14, -40), (-24, -40),
                   (-24, -50), (-30, -50)])]
    if kind == "bed":
        return [P([(-60, 0), (60, 0), (60, -30), (-60, -30)]), P([(-60, 0), (-54, 0), (-54, -56), (-60, -56)]),
                P([(-50, -30), (-24, -30), (-24, -40), (-50, -40)])]
    if kind == "shelf":
        return [P([(-24, 0), (24, 0), (24, -118), (-24, -118)])]
    if kind == "cabinet":
        return [P([(-18, 0), (18, 0), (18, -96), (-18, -96)])]
    if kind == "plant":
        return [P([(-10, 0), (10, 0), (13, -22), (-13, -22)]), P([(0, -22), (-26, -60), (-6, -40), (2, -74),
                                                                    (8, -42), (28, -58), (6, -24)])]
    if kind == "radio":
        return [P([(-16, -44), (16, -44), (16, -66), (-16, -66)])] + _furn("table", x, fy, s)
    if kind == "desk_lamp":
        return [P([(-9, 0), (9, 0), (7, -4), (-7, -4)]), P([(-1.5, -4), (1.5, -4), (9, -30), (6, -31)]),
                P([(0, -34), (18, -24), (16, -20), (-2, -30)])]
    return []


TEN_SETS = {                                 # storey -> [(kind, x from the room's back wall)]
    2: (("radio", 36.0), ("armchair", 104.0)),
    3: (("shelf", 26.0), ("lamp", 66.0), ("armchair", 116.0)),
    4: (("chair_l", 46.0), ("table", 84.0)),
    5: (("bed", 64.0), ("chair_l", 146.0)),
}
OFFICE_SETS = {2: (("cabinet", 40.0), ("desk", 110.0), ("chair_l", 150.0), ("desk", 230.0), ("cabinet", 330.0)),
               3: (("cabinet", 40.0), ("desk", 140.0), ("shelf", 260.0), ("desk", 340.0))}


def furniture(where, n):
    """[(kind, x, polys)] of a room's furniture: where 'ten' (storeys 2..5) or 'office' (2, 3)."""
    if where == "ten":
        if n not in TEN_SETS:
            return []
        x0, _, _, fy = TEN.room(n)
        return [(kind, x0 + dx, _furn(kind, x0 + dx, fy, 0.9)) for kind, dx in TEN_SETS[n]]
    x0 = HALL[0]
    fy = bank_level(n) - SLAB / 2
    return [(kind, x0 + dx, _furn(kind, x0 + dx, fy, 0.9)) for kind, dx in OFFICE_SETS.get(n, ())]


LAMP_TOP = (TEN.room(CREW_FLOOR)[0] + 84.0, TEN.room(CREW_FLOOR)[1])     # where the crew's lamp hangs from
LAMP_LEN = 70.0
CORD_LEN = 34.0


def pendant(c, t, lit=True, swing=0.0, pull=0.0, color=None):
    """The crew's lamp, hanging over their table, with its pull cord (pull 0..1: drawn down).
    swing: degrees it sways (on a slow pendulum). Returns (shade centre, the cord's end)."""
    top = LAMP_TOP
    a = math.radians(swing * math.sin(2.0 * math.pi * 0.5 * t))
    p = (top[0] + LAMP_LEN * math.sin(a), top[1] + LAMP_LEN * math.cos(a))
    col = color if color is not None else (INK if lit else DARK_INK)
    bass.fill_polys(c, [bass.line_pts([top, p], width=2.0, seed=650)], col)
    c.save()
    c.translate(*p)
    c.rotate(-a)
    bass.fill_polys(c, [bass.orient([(-6.0, 0.0), (6.0, 0.0), (17.0, 15.0), (-17.0, 15.0)], True)], col)
    if lit:
        K.dot(c, (0.0, 16.0), 4.0, PAPER, seed=651)
    L = CORD_LEN + 6.0 * clamp(pull)
    bass.fill_polys(c, [bass.line_pts([(11.0, 12.0), (11.0, 12.0 + L)], width=1.2, seed=652)], col)
    K.dot(c, (11.0, 13.0 + L), 1.8, col, seed=653)
    end = c.user_to_device(11.0, 13.0 + L)
    c.restore()
    return p, c.device_to_user(*end)


CLOCK_AT = (TEN.room(CREW_FLOOR)[0] + 24.0, TEN.room(CREW_FLOOR)[1] + 28.0)    # the crew's wall clock


def wall_clock(c, hh, mm, lit=True):
    """The crew's wall clock on their back wall."""
    x0, y0, _, _ = TEN.room(CREW_FLOOR)
    K.clock_face(c, CLOCK_AT, 12.0, hh, mm, face=PAPER if lit else lerp(DEEP, PAPER, 0.25),
                 ink=INK, seed=652)


def _stairs(c, b, color):
    polys = []
    for n in range(1, b.floors + 1):
        top = n < b.floors
        lx, ly = b.landing(n)
        if top:
            mx, my = b.mid(n)
            ex = b.stair[0] if b.side > 0 else b.stair[1]
            polys.append(bass.orient([(ex, my), (mx + 18.0 * b.side, my), (mx + 18.0 * b.side, my + 10.0),
                                      (ex, my + 10.0)], True))
            for (ax, ay), (bx2, by2) in (((lx, ly), (mx, my)), ((mx, my), b.landing(n + 1))):
                steps = 9
                pts = []
                for i in range(steps + 1):
                    f = i / steps
                    x = ax + (bx2 - ax) * f
                    y = ay + (by2 - ay) * f
                    pts.append((x, y))
                    if i < steps:
                        pts.append((ax + (bx2 - ax) * (i + 1) / steps, y))
                d = 11.0
                under = [(x, y + d) for x, y in pts[::-1]]
                polys.append(bass.orient(pts + [(pts[-1][0], pts[-1][1] + d)] + under, True))
    bass.fill_polys(c, polys, color)


@lru_cache(maxsize=8)
def _ten_shell(open_windows=(), street_door_open=False):
    b = TEN
    polys = []
    top = b.roof
    for n in range(1, b.floors + 2):
        y = level(n)
        polys.append(_r(b.x0, y - SLAB / 2, b.x1, y + SLAB / 2, b.seed + n, 0.6))
    polys.append(_r(b.x0, top, b.x0 + WALL, GROUND + SLAB / 2, b.seed + 20, 0.6))
    for n in range(1, b.floors + 1):
        y0, y1 = level(n + 1) + SLAB / 2, level(n) - SLAB / 2
        if n == 1:
            sd = b.street_door()
            polys.append(_r(b.street[0], y0, b.street[1], sd[1], b.seed + 41))
        else:
            wx0, wy0, wx1, wy1 = b.window(n)
            polys.append(_r(b.street[0], y0, b.street[1], wy0, b.seed + 40 + n))
            polys.append(_r(b.street[0], wy1, b.street[1], y1, b.seed + 60 + n))
            if n not in open_windows:
                mx = (wx0 + wx1) / 2.0
                polys.append(_r(mx - 2.5, wy0, mx + 2.5, wy1, b.seed + 80 + n, 0.3))
        d = b.door(n)
        polys.append(_r(b.part[0], y0, b.part[1], d[1], b.seed + 100 + n))
        if n > 1:
            polys.append(_r(b.part[0] + 4.0, d[1], b.part[1] - 4.0, d[3], b.seed + 120 + n, 0.4))
    polys.append(_r(b.x0 - 6.0, top - 26.0, b.x1 + 6.0, top, b.seed + 140, 0.6))
    x = b.x0 + 70.0
    t2 = top - 26.0
    polys.append(bass.orient(bass.cut([(x, t2), (x + 8, t2), (x + 8, t2 - 60), (x + 82, t2 - 60), (x + 82, t2), (x + 90, t2),
                                       (x + 90, t2 - 64), (x + 96, t2 - 64), (x + 96, t2 - 74), (x + 92, t2 - 74),
                                       (x + 92, t2 - 150), (x + 76, t2 - 168), (x + 14, t2 - 168), (x - 2, t2 - 150),
                                       (x - 2, t2 - 74), (x - 6, t2 - 74), (x - 6, t2 - 64), (x, t2 - 64)],
                                      seed=b.seed + 150, amp=0.6), True))
    return polys


def _street_door_leaf(c, u):
    """The tenement's street door: shut (a leaf in the opening) .. open (u 1: gone, swung in)."""
    sd = TEN.street_door()
    if u < 1.0:
        w = (sd[2] - sd[0] - 4.0) * (1.0 - ease("inout", clamp(u)))
        if w > 0.5:
            bass.fill_polys(c, [_r(sd[0] + 2.0, sd[1], sd[0] + 2.0 + w, sd[3], 661, 0.3)], DOOR_LEAF)


def beam(c, n, color=AMBER, alpha=0.16, reach=None):
    """The light of the tenement's lit storey-n window thrown across the street, a flat wedge."""
    wx0, wy0, wx1, wy1 = TEN.window(n)
    x = TEN.face
    reach = reach if reach is not None else (STREET[1] - STREET[0])
    xe = x + reach
    spread = 0.38 * reach
    bass.fill_polys(c, [bass.orient([(x, wy0), (xe, wy0 - 0.25 * spread), (xe, wy1 + 0.75 * spread), (x, wy1)], True)],
                    color, alpha)


def floor_numbers(c, color, lit=None, size=36.0):
    """1, 2, 3 ... beside the tenement's storeys, on its far side. lit: {storey: rgb}."""
    for n in range(1, TEN.floors + 1):
        K.numeral(c, str(n), ((TEN.stair[0] + TEN.stair[1]) / 2.0, level(n + 1) + 46.0), size, (lit or {}).get(n, color),
                  seed=40 + n)


# ============================================================================ neighbours (OPPOSITE's folk)
def neighbour(c, n, t, state="asleep"):
    """The tenement's little lives, in their storey-n rooms: 2 the old man (bald) by his radio,
    3 the woman (bun) in her armchair, 5 the man (cap) in his bed. state: 'up' (lit, living),
    'asleep' (dark), 'woken' (lit, at the window looking out). Returns the head (px) or None."""
    x0, y0, x1, fy = TEN.room(n)
    lit = AMBER if state in ("up", "woken") else None
    kind = {2: "bald", 3: "bun", 5: "cap"}.get(n)
    if kind is None:
        return None
    f = FO.small(kind)
    if state == "woken":
        st = pd.standing(f, 0.0, 12.0)
        p = pd.Pose(lean=4.0, head=4.0, arms={"near": ("ang", 30.0, 70.0), "far": ("ang", 24.0, 60.0)})
        out = FO.draw(c, f, st, p, x1 - 26.0, fy, 1, lit)
        return out["head_at"]
    if n == 5:
        if state == "asleep":
            FO.sleeper(c, x0 + 61.0, fy, K.twos(t), None, seed=3)
            return None
        st = FO.seated(f, 0.0, 1, 30.0)
        p = pd.Pose(lean=4.0, head=-6.0, arms={"near": ("ang", 40.0, 80.0), "far": ("ang", 30.0, 70.0)})
        out = FO.draw(c, f, st, p, x0 + 146.0 - 4.0, fy, 1, lit)
        return out["head_at"]
    seat = (x0 + TEN_SETS[n][-1][1], 36.0)
    if state == "asleep":
        head = -26.0 if n == 2 else 16.0
        p = pd.Pose(lean=-5.0 if n == 2 else -14.0, head=head,
                    arms={"near": ("ang", 8.0, 30.0), "far": ("ang", 4.0, 28.0)})
    else:
        p = pd.Pose(lean=-6.0, head=-4.0 if n == 2 else -14.0,
                    arms={"near": ("ang", 30.0, 70.0), "far": ("ang", 20.0, 60.0)})
    out = FO.draw(c, f, FO.seated(f, 0.0, -1, seat[1]), p, seat[0] + 6.0, fy, -1, lit)
    return out["head_at"]


# ============================================================================ the bank in section
def _bank_inside(c, t, lit, people, hall_lamp, vault_lit, gold_glow, gold, ruby_box, ruby):
    """The bank's insides (before its walls): the hall in the dark with the guard's lamp, the
    vault, the dark offices."""
    bass.fill_polys(c, [_r(BANK[0], BANK_ROOF, BANK[1], GROUND, 701)], DEEP)
    # offices
    for n in (2, 3):
        r = (HALL[0], bank_level(n + 1) + SLAB / 2, BANK[1] - WALL, bank_level(n) - SLAB / 2)
        col = lit.get(("bank", n))
        if col is not None:
            bass.fill_polys(c, [_r(*r, seed=710 + n)], col)
        for kind, x, polys in furniture("office", n):
            bass.fill_polys(c, polys, INK if col is not None else DARK_INK)
        if people is not None:
            people(c, "office", n, r)
    # the hall: dark, the guard's lamp on his desk
    hall = (HALL[0], bank_level(2) + SLAB / 2, HALL[1], FEET)
    hcol = lit.get("hall")
    if hcol is not None:
        bass.fill_polys(c, [_r(*hall, seed=720)], hcol)
    fcol = INK if (hcol is not None or hall_lamp > 0.0) else DARK_INK
    lamp_on = hall_lamp > 0.0
    if lamp_on:
        c.save()
        c.rectangle(hall[0], hall[1], hall[2] - hall[0], hall[3] - hall[1])
        c.clip()
        K.pool(c, (GUARD_LAMP[0] + 10.0, FEET - 30.0), 130.0, 80.0, AMBER, 0.22 * hall_lamp)
        c.restore()
    bass.fill_polys(c, _furn("desk", DESK_X, FEET, 0.9), fcol)
    bass.fill_polys(c, _furn("desk_lamp", GUARD_LAMP[0], GUARD_LAMP[1], 1.0), fcol)
    if lamp_on:
        K.dot(c, (GUARD_LAMP[0] + 9.0, GUARD_LAMP[1] - 21.0), 3.2, lerp(AMBER, PAPER, 0.5), seed=721)
    bass.fill_polys(c, [_r(*r, seed=730 + i, amp=0.4) for i, r in enumerate(CRATES)], fcol)
    for i, r in enumerate(CRATES):                 # the slats
        bass.fill_polys(c, [_r(r[0] + 3.0, (r[1] + r[3]) / 2.0 - 1.0, r[2] - 3.0, (r[1] + r[3]) / 2.0 + 1.0, 735 + i, 0.2)],
                        lerp(fcol, STEEL, 0.18))
    # the vault's inside
    v = (VAULT_IN[0], VAULT_TOP, VAULT_IN[1], FEET)
    vcol = lerp(DEEP, GOLD_ROOM, clamp(vault_lit))
    bass.fill_polys(c, [_r(*v, seed=740)], vcol)
    bc = lerp(BOX_DARK, GOLD_BOX, clamp(vault_lit))
    seam = lerp(lerp(DEEP, INK, 0.5), GOLD_SEAM, clamp(vault_lit))
    x0, y0, x1, y1 = BOX_GRID
    bass.fill_polys(c, [_r(x0 - 2.0, y0 - 2.0, x1 + 2.0, y1 + 2.0, 741, 0.3)], seam)
    for col in range(BOX_COLS):
        for row in range(BOX_ROWS):
            r = box_rect(col, row)
            if (col, row) == RUBY_BOX and ruby_box > 0.0:
                bass.fill_polys(c, [_r(*r, seed=742 + col * 7 + row, amp=0.2)], INK)
                if ruby:
                    K.dot(c, ((r[0] + r[2]) / 2.0, r[3] - 5.0), 2.6, RED, seed=743)
                continue
            bass.fill_polys(c, [_r(*r, seed=742 + col * 7 + row, amp=0.2)], bc)
            K.dot(c, (r[2] - 3.5, (r[1] + r[3]) / 2.0), 1.1, seam, seed=744)
    if gold_glow > 0.0 and gold > 0.0:
        c.save()
        c.rectangle(v[0], v[1], v[2] - v[0], v[3] - v[1])
        c.clip()
        K.pool(c, (GOLD_STACKS[1], FEET - 12.0), 96.0, 54.0, AMBER, 0.30 * gold_glow * (0.5 + 0.5 * clamp(gold * 2.0)))
        c.restore()
    _gold(c, gold, gold_glow)
    if people is not None:
        people(c, "hall", 1, hall)
        people(c, "vault", 1, v)


def _gold(c, amount, glow):
    """The gold: three stacks of bars on the vault's floor; `amount` 0..1 of it still there (the
    stacks go from the right as he bags them)."""
    if amount <= 0.0:
        return
    bars = []
    for i, sx in enumerate(GOLD_STACKS):
        for row, n in enumerate((3, 2, 1)):
            for k in range(n):
                bx = sx - (n - 1) * 5.5 + k * 11.0
                by = FEET - row * 7.0
                bars.append((bx, by, i * 10 + row * 3 + k))
    keep = int(round(len(bars) * clamp(amount)))
    face = lerp(GOLD_SEAM, AMBER, clamp(0.35 + 0.65 * glow))
    for bx, by, s in bars[:keep]:
        bass.fill_polys(c, [bass.orient([(bx - 5.0, by), (bx + 5.0, by), (bx + 3.5, by - 6.0), (bx - 3.5, by - 6.0)], True)],
                        face)
        bass.fill_polys(c, [bass.orient([(bx - 5.0, by), (bx + 5.0, by), (bx + 5.0, by - 1.2), (bx - 5.0, by - 1.2)], True)],
                        GOLD_SEAM)


@lru_cache(maxsize=16)
def _bank_shell(side_door_open, vault_door_open, open_windows=()):
    polys = []
    x0, x1 = BANK
    for n in (1, 2, 3, 4):
        y = bank_level(n)
        if n == 1:                                      # the hall's floor, round the hatch
            polys.append(_r(x0, y - SLAB / 2, HATCH[0], y + SLAB / 2, 751, 0.6))
            polys.append(_r(HATCH[1], y - SLAB / 2, VAULT[0], y + SLAB / 2, 750, 0.6))
        else:
            polys.append(_r(x0, y - SLAB / 2, x1, y + SLAB / 2, 751 + n, 0.6))
    # the street wall: whole but for the side door and the office windows
    polys.append(_r(x0, SIDE_DOOR[3] - 1.0, x0 + BW, GROUND + SLAB / 2, 760, 0.4))
    polys.append(_r(x0, bank_level(2), x0 + BW, SIDE_DOOR[1], 761))
    for n in (2, 3):
        y0, y1 = bank_level(n + 1) + SLAB / 2, bank_level(n) - SLAB / 2
        wy0, wy1 = y0 + 50.0, y1 - 44.0
        polys.append(_r(x0, y0 - SLAB / 2, x0 + BW, wy0, 762 + n))
        polys.append(_r(x0, wy1, x0 + BW, y1 + SLAB / 2, 764 + n))
        if n not in open_windows:
            polys.append(_r(x0 + BW / 2 - 2.5, wy0, x0 + BW / 2 + 2.5, wy1, 766 + n, 0.3))
    # the back wall
    polys.append(_r(x1 - WALL, BANK_ROOF, x1, GROUND + SLAB / 2, 770, 0.5))
    # cornice, both faces, and the pitched roof on the pediment's line
    yc = BANK_ROOF - CORNICE
    polys.append(_r(x0 - 14.0, yc, x1 + 14.0, BANK_ROOF - 6.0, 771, 0.5))
    polys.append(_r(x0 - 6.0, BANK_ROOF - 6.0, x1 + 6.0, BANK_ROOF + 2.0, 772, 0.4))
    polys.append(bass.orient(bass.cut([(x0 - 8.0, yc), PED_APEX, (x1 + 8.0, yc)], seed=773, amp=0.5, seg=(40.0, 90.0)),
                             True))
    return polys


@lru_cache(maxsize=4)
def _vault_walls(door_open):
    """The vault's thick walls, ceiling and floor slab, cut (HEAVY)."""
    polys = [_r(VAULT[0], bank_level(2) - SLAB / 2, VAULT[1], VAULT_TOP, 780, 0.5),        # ceiling
             _r(VAULT[0], FEET, VAULT[1], FEET + VSLAB, 781, 0.4),                          # floor slab
             _r(VAULT_IN[1], VAULT_TOP - 2.0, VAULT[1], FEET + 2.0, 782, 0.4),              # far wall
             _r(VAULT[0], VAULT_TOP - 2.0, VAULT_IN[0], VDOOR[1], 783, 0.4)]                # over the door
    return polys


def _vault_door(c, u, light):
    """The round door's slot: shut (the steel door in it, its wheel's hub on the hall side) .. open
    (u >= 0.5: an empty slot; the gold's light floods out across the hall's floor)."""
    x0, y0, x1, y1 = VDOOR
    if u < 0.5:
        bass.fill_polys(c, [_r(x0 - 7.0, y0 + 4.0, x1 + 7.0, y1, 790, 0.3)], lerp(INK, STEEL, 0.12))
        bass.fill_polys(c, [_r(x0 - 7.0, y0 + 4.0, x0 - 4.0, y1, 791, 0.2)], STEEL)
        bass.fill_polys(c, [bass.ring_pts((x0 - 7.0, (y0 + y1) / 2.0), 9.0, seed=792, n=16, amp=0.3)], STEEL)
        bass.fill_polys(c, [bass.ring_pts((x0 - 7.0, (y0 + y1) / 2.0), 4.0, seed=793, n=10, amp=0.2)], INK)
    elif light > 0.0:
        bass.fill_polys(c, [bass.orient([(x1, y0 + 8.0), (x1, y1), (HALL[0] + 60.0, y1), (x0 - 4.0, y0 + 30.0)], True)],
                        AMBER, 0.16 * light)


def _hatch_lid(c, u):
    """The hatch's lid in the hall's floor, hinged on its street-side edge: 0 shut, 0.15 pushed
    up a crack, 1 thrown open."""
    hx = HATCH[0] - 2.0
    ang = 104.0 * (ease("outback", clamp(u)) if 0.0 < u < 1.0 else clamp(u))
    c.save()
    c.translate(hx, FEET + 1.0)
    c.rotate(math.radians(-ang))
    bass.fill_polys(c, [_r(0.0, -4.0, HATCH[1] - HATCH[0] + 4.0, 6.0, 795, 0.3)], lerp(STEEL, INK, 0.35))
    bass.fill_polys(c, [_r(8.0, -4.0, 11.0, 6.0, 796, 0.2)], INK)
    c.restore()


def _tile(c, u, open_hole):
    """The floor tile over the trapdoor: 0 in place (a hairline seam) .. 1 lifted and laid aside."""
    x0, x1 = TILE
    if u <= 0.0:
        for xx in (x0, x1):
            bass.fill_polys(c, [_r(xx - 0.8, FEET, xx + 0.8, FEET + 8.0, 797, 0.1)], lerp(HEAVY, PAPER, 0.15))
        return
    g = ease("inout", clamp(u))
    bass.fill_polys(c, [_r(x0, FEET - 1.0, x1, FEET + VSLAB + 1.0, 798, 0.2)], TUNNEL if open_hole else lerp(INK, NIGHT, 0.55))
    # the tile itself, up and over to the left, laid flat on the floor
    tx = lerp(x0, x0 - (x1 - x0) - 6.0, g)
    ty = FEET - 30.0 * math.sin(math.pi * g)
    bass.fill_polys(c, [_r(tx, ty - 8.0, tx + (x1 - x0), ty, 799, 0.2)], lerp(HEAVY, STEEL, 0.35))


def bell(c, t, ringing=0.0, quiet_col=None):
    """The alarm bell on the bank's street wall, outside, high over the side door: a bracket and
    the dome turned to the street. ringing 0..1 rocks it and turns it RED."""
    bx, by = BELL
    col = lerp(quiet_col or STEEL, RED, clamp(ringing * 1.5))
    rock = 13.0 * math.sin(t * 2.0 * math.pi * 9.0) * clamp(ringing)
    bass.fill_polys(c, [_r(bx - 3.0, by - 21.0, BANK[0] + 1.0, by - 16.0, 801, 0.2),
                        _r(BANK[0] - 5.0, by - 28.0, BANK[0], by - 8.0, 802, 0.2)], INK)
    K.bell(c, (bx, by), 1.1, col, seed=803, ring=rock)


# ============================================================================ the street in section
def _lid(c, cx, u, seed=0):
    """A manhole's lid, edge on, in the road over the opening at cx: 0 shut .. 0.35 levered up
    on its right edge .. 0.8 dragged left out of the hole .. 1 dropped flat beside it (left)."""
    L = 2.0 * MH_R + 10.0
    home = cx + MH_R + 5.0
    u = clamp(u)
    if u < 0.35:
        px, ang = home, 35.0 * ease("out", u / 0.35)
    elif u < 0.8:
        g = ease("inout", (u - 0.35) / 0.45)
        px, ang = lerp(home, cx - MH_R + 2.0, g), lerp(35.0, 55.0, g)
    else:
        g = (u - 0.8) / 0.2
        px, ang = lerp(cx - MH_R + 2.0, cx - MH_R - 4.0, g), 55.0 * (1.0 - g * g)
    c.save()
    c.translate(px, GROUND - 1.0)
    c.rotate(math.radians(ang))
    bass.fill_polys(c, [_r(-L, -4.0, 0.0, 3.0, 810 + seed, 0.2)], lerp(STEEL, INK, 0.30))
    c.restore()


def lid_edge(cx, u):
    """Where a manhole lid's raised edge is (for a hand on it), section px."""
    L = 2.0 * MH_R + 10.0
    home = cx + MH_R + 5.0
    u = clamp(u)
    if u < 0.35:
        px, ang = home, 35.0 * ease("out", u / 0.35)
    elif u < 0.8:
        g = ease("inout", (u - 0.35) / 0.45)
        px, ang = lerp(home, cx - MH_R + 2.0, g), lerp(35.0, 55.0, g)
    else:
        g = (u - 0.8) / 0.2
        px, ang = lerp(cx - MH_R + 2.0, cx - MH_R - 4.0, g), 55.0 * (1.0 - g * g)
    a = math.radians(ang)
    return (px - L * math.cos(a), GROUND - 1.0 - L * math.sin(a))


def _rungs(c, x0, x1, y0, y1, seed=0):
    """Iron rungs and the rails they hang on, up a shaft from y1 to y0."""
    bass.fill_polys(c, [_r(x0 + 4.0, y0, x0 + 7.0, y1, seed, 0.2), _r(x1 - 7.0, y0, x1 - 4.0, y1, seed + 1, 0.2)], RAIL)
    y = y1 - RUNG_STEP
    polys = []
    i = 0
    while y > y0 + 4.0:
        polys.append(_r(x0 + 3.0, y - 1.8, x1 - 3.0, y + 1.8, seed + 2 + i, 0.2))
        y -= RUNG_STEP
        i += 1
    bass.fill_polys(c, polys, IRON)


_DRIPS = tuple((x, 1.1 + 0.9 * hash01(i, 801), 3.0 * hash01(i, 802))
               for i, x in enumerate((404.0, 498.0, 612.0, 742.0, 828.0, 952.0)))
G_DRIP = 2600.0


def _fall_time():
    return math.sqrt(2.0 * (WATER - CROWN - 8.0) / G_DRIP)


def drip_times(t0, t1):
    """Every drip in the tunnel that hits the water between scene times t0 and t1: [(t, x)]."""
    ft = _fall_time()
    out = []
    for x, per, ph in _DRIPS:
        k = math.ceil((t0 - ft - ph) / per)
        while True:
            hit = ph + k * per + ft
            if hit > t1:
                break
            if hit >= t0:
                out.append((round(hit, 4), x))
            k += 1
    return sorted(out)


def _drips(c, t):
    ft = _fall_time()
    for i, (x, per, ph) in enumerate(_DRIPS):
        k = math.floor((t - ph) / per)
        s = t - (ph + k * per)
        if s > per - 0.5:
            r = 1.6 + 2.2 * clamp((s - per + 0.5) / 0.5)
            K.dot(c, (x, CROWN + 2.0 + r), r, PAPER, seed=820 + i, alpha=0.7)
        if s < ft:
            y = CROWN + 6.0 + 0.5 * G_DRIP * s * s
            L = 5.0 + 8.0 * clamp(s / ft)
            bass.fill_polys(c, [bass.orient([(x, y - L), (x + 2.0, y - 1.0), (x, y + 2.0), (x - 2.0, y - 1.0)], True)],
                            PAPER, 0.75)
        elif s < ft + 0.6:
            a = (s - ft) / 0.6
            water_ring(c, (x, WATER + 1.0), a, 26.0)


def water_ring(c, p, a, size):
    """A ring spreading on the black water (a 0..1)."""
    rx = 5.0 + size * ease("out3", a)
    pts = draw.ellipse_pts(p, rx, rx * 0.16, n=28)
    inner = draw.ellipse_pts(p, max(1.0, rx - 2.2 * (1 - a) - 0.6), max(0.4, (rx - 2.2) * 0.16), n=28)
    bass.fill_polys(c, [bass.orient(pts, True), bass.orient(inner, False)], PAPER, 0.7 * (1.0 - a))


def splash(c, p, t, t0, s=1.0):
    """A step into the water at p: a ring and two flecks (from t0)."""
    a = (t - t0) / 0.6
    if not 0.0 <= a < 1.0:
        return
    water_ring(c, (p[0], WATER + 1.0), a, 24.0 * s)
    if a < 0.25:
        h = 11.0 * s * math.sin(math.pi * a / 0.25)
        for d in (-1, 1):
            K.dot(c, (p[0] + d * 6.0 * s, WATER - h), 1.6 * s, PAPER, seed=850 + d, alpha=0.85)


def water_edge(c, x0=None, x1=None):
    """The water's near edge, drawn after figures wading in the tunnel: their feet go under."""
    x0 = TUNNEL_X[0] if x0 is None else x0
    x1 = TUNNEL_X[1] if x1 is None else x1
    bass.fill_polys(c, [[(x0, WATER + 2.0), (x1, WATER + 2.0), (x1, INVERT), (x0, INVERT)]], INK)
    bass.fill_polys(c, [_r(x0, WATER, x1, WATER + 2.6, 861, 0.2)], WATER_EDGE)


def underground(c, t, trap_shaft=False, drips=True):
    """The earth, cut: the tunnel, its water, the shafts and their rungs."""
    x0, x1 = TUNNEL_X
    bass.fill_polys(c, [[(x0 - 10.0, CROWN - 10.0), (x1 + 10.0, CROWN - 10.0), (x1 + 10.0, INVERT + 10.0),
                         (x0 - 10.0, INVERT + 10.0)]], LINING)
    bass.fill_polys(c, [[(x0, CROWN), (x1, CROWN), (x1, INVERT), (x0, INVERT)]], TUNNEL)
    jx = x0 + 70.0
    joints = []
    while jx < x1 - 20.0:
        joints.append(_r(jx - 1.0, CROWN, jx + 1.0, WATER, 870 + int(jx) % 97, 0.2))
        jx += 110.0
    bass.fill_polys(c, joints, lerp(TUNNEL, INK, 0.45))
    for k, (sx0, sx1, top) in SHAFTS.items():
        if k == "trap" and not trap_shaft:
            continue
        bass.fill_polys(c, [[(sx0 - 6.0, top), (sx1 + 6.0, top), (sx1 + 6.0, CROWN), (sx0 - 6.0, CROWN)]], LINING)
        bass.fill_polys(c, [[(sx0, top - 1.0), (sx1, top - 1.0), (sx1, CROWN + 1.0), (sx0, CROWN + 1.0)]], TUNNEL)
        if k != "gully":
            _rungs(c, sx0, sx1, top + 2.0, WATER, seed=880 + 10 * len(k))
    bass.fill_polys(c, [[(x0, WATER), (x1, WATER), (x1, INVERT), (x0, INVERT)]], INK)
    bass.fill_polys(c, [_r(x0, WATER, x1, WATER + 2.4, 890, 0.2)], WATER_EDGE)
    if drips:
        _drips(c, t)


def lamp(c, on=1.0):
    """The street lamp on the tenement's sidewalk; its light falls flat on the road."""
    hx, hy = LAMP_HEAD
    if on > 0.0:
        c.save()
        c.rectangle(STREET[0], 0.0, STREET[1] - STREET[0], GROUND)
        c.clip()
        bass.fill_polys(c, [bass.orient([(hx - 9.0, hy + 8.0), (hx + 9.0, hy + 8.0), (hx + 104.0, GROUND),
                                         (hx - 74.0, GROUND)], True)], AMBER, 0.13 * on)
        c.restore()
        K.pool(c, (hx + 14.0, GROUND), 90.0, 9.0, AMBER, 0.30 * on)
    lx = LAMP_X
    bass.fill_polys(c, [bass.orient([(lx - 4.0, GROUND - CURB_H), (lx + 4.0, GROUND - CURB_H), (lx + 3.0, hy - 16.0),
                                     (lx - 3.0, hy - 16.0)], True),
                        _r(lx - 9.0, GROUND - CURB_H - 22.0, lx + 9.0, GROUND - CURB_H, 902, 0.3),
                        bass.line_pts([(lx, hy - 14.0), (lx + 12.0, hy - 30.0), (hx, hy - 24.0)], width=5.0, seed=903),
                        bass.orient([(hx - 14.0, hy - 6.0), (hx + 14.0, hy - 6.0), (hx + 9.0, hy - 22.0),
                                     (hx - 9.0, hy - 22.0)], True)], INK)
    bass.fill_polys(c, [bass.orient([(hx - 10.0, hy - 6.0), (hx + 10.0, hy - 6.0), (hx + 6.0, hy + 6.0), (hx - 6.0, hy + 6.0)],
                                    True)], lerp(INK, AMBER, 0.2 + 0.8 * clamp(on)))


def car_rear(c, cx, t, s=1.0, lights=1.0, boot=0.0, cough=0.0, rock=0.0, gy=GROUND, police=False, color=INK):
    """A car end-on from behind, its wheels on gy, centred on cx: the Knight's (RED tail lights)
    or a police car (`police`: a light bar on its roof). boot 0..1 opens the boot lid upward;
    cough 0..1 puffs from the exhaust; rock (deg) tilts the body on its springs."""
    c.save()
    c.translate(cx, gy)
    c.scale(s, s)
    for d in (-1, 1):                                   # the tyres, under the body
        bass.fill_polys(c, [_r(d * 44.0 - 9.0, -26.0, d * 44.0 + 9.0, 0.0, 905 + d, 0.3)], INK)
    c.save()
    c.translate(0.0, -14.0)
    c.rotate(math.radians(rock))
    body = [(-50.0, 0.0), (50.0, 0.0), (52.0, -10.0), (50.0, -40.0), (44.0, -48.0), (34.0, -52.0), (28.0, -78.0),
            (18.0, -88.0), (-18.0, -88.0), (-28.0, -78.0), (-34.0, -52.0), (-44.0, -48.0), (-50.0, -40.0), (-52.0, -10.0)]
    bass.fill_polys(c, [bass.orient([(x * 1.04, y * 1.03 - 1.5) for x, y in body], True)], STEEL if color is INK else color)
    bass.fill_polys(c, [bass.orient(bass.cut(body, seed=907, amp=0.3, seg=(16.0, 40.0)), True)], color)
    bass.fill_polys(c, [bass.orient([(-22.0, -56.0), (22.0, -56.0), (16.0, -78.0), (-16.0, -78.0)], True)], GLASS)
    bass.fill_polys(c, [_r(-52.0, -14.0, 52.0, -7.0, 908, 0.3)], STEEL)          # the bumper
    bass.fill_polys(c, [_r(-12.0, -30.0, 12.0, -20.0, 909, 0.2)], lerp(INK, STEEL, 0.35))   # the plate (blank)
    if boot > 0.0:                                       # the boot lid, hinged at the rear window's foot
        g = ease("outback", clamp(boot)) if boot < 1.0 else 1.0
        bass.fill_polys(c, [_r(-36.0, -50.0, 36.0, -18.0, 910, 0.2)], DEEP)
        c.save()
        c.translate(0.0, -52.0)
        c.scale(1.0, 1.0 - 1.9 * g)
        bass.fill_polys(c, [_r(-38.0, 0.0, 38.0, 32.0, 911, 0.2)], color)
        c.restore()
    for d in (-1, 1):
        K.dot(c, (d * 43.0, -38.0), 4.4, RED if not police else lerp(RED, INK, 0.3), seed=912 + d,
              alpha=0.55 + 0.45 * clamp(lights))
    if police:
        K.light_bar(c, (0.0, -88.0), t, s=1.15, seed=913)
    c.restore()
    if cough > 0.0:                                      # the exhaust coughs: two puffs rising
        for i in range(3):
            a = clamp(cough * 1.4 - i * 0.2)
            if 0.0 < a < 1.0:
                K.dot(c, (34.0 + 10.0 * a + 6.0 * i, -8.0 - 26.0 * a), 4.0 + 9.0 * a, lerp(STEEL, PAPER, 0.3), seed=915 + i,
                      alpha=0.55 * (1.0 - a))
    bass.fill_polys(c, [_r(28.0, -12.0, 40.0, -8.0, 914, 0.2)], STEEL)            # the exhaust pipe
    c.restore()


def gully(c):
    """The gully grating in the road by the bank's curb, edge on: three bars over the drain."""
    x0, x1 = GULLY
    bass.fill_polys(c, [_r(x0, GROUND - 2.0, x1, GROUND + 3.0, 916, 0.2)], lerp(STEEL, INK, 0.25))
    for i in range(3):
        xx = x0 + 3.0 + i * (x1 - x0 - 6.0) / 2.0
        bass.fill_polys(c, [_r(xx - 1.0, GROUND - 2.0, xx + 1.0, GROUND + 12.0, 917 + i, 0.1)], INK)


def street_ground(c, t, under=1.0, lid_a=0.0, lid_b=0.0, trap_shaft=False, drips=True):
    """The street's ground in section: the earth (cut open down to `under` 0..1 of the way to
    the tunnel's floor), the road slab, the curbs, the manhole lids, the gully."""
    bass.fill_polys(c, [[(-20.0, GROUND), (W + 20.0, GROUND), (W + 20.0, H + 20.0), (-20.0, H + 20.0)]], INK)
    if under > 0.0:
        yb = lerp(GROUND, INVERT + 14.0, ease("out3", clamp(under)))
        c.save()
        c.rectangle(-20.0, GROUND - 2.0, W + 40.0, yb - GROUND + 2.0)
        c.clip()
        underground(c, t, trap_shaft, drips and under >= 1.0)
        c.restore()
    bass.fill_polys(c, [[(STREET[0], GROUND + 1.0), (STREET[1], GROUND + 1.0), (STREET[1], GROUND + ROAD_SLAB),
                         (STREET[0], GROUND + ROAD_SLAB)]], SLAB_CUT)
    for k in ("b", "a", "gully"):                       # the slab is cut through where the shafts are
        sx0, sx1, top = SHAFTS[k]
        bass.fill_polys(c, [[(sx0, GROUND - 1.0), (sx1, GROUND - 1.0), (sx1, GROUND + ROAD_SLAB + 1.0),
                             (sx0, GROUND + ROAD_SLAB + 1.0)]], TUNNEL if under > 0.02 else INK)
    bass.fill_polys(c, [_r(STREET[0], GROUND - CURB_H, STREET[0] + CURB, GROUND + 2.0, 921, 0.4),
                        _r(STREET[1] - CURB, GROUND - CURB_H, STREET[1], GROUND + 2.0, 922, 0.4)], INK)
    bass.fill_polys(c, [_r(STREET[0], GROUND - 1.5, STREET[1], GROUND + 1.5, 923, 0.2)], lerp(STEEL, NIGHT, 0.25))
    _lid(c, MH_B, lid_b, seed=1)
    _lid(c, MH_A, lid_a, seed=2)
    gully(c)


# ============================================================================ the section
MOON_S = (858.0, 286.0)                       # the moon in the section, over the bank's roof
MOON_E = (465.0, 330.0)                       # ... and in the elevation, in the gap between the fronts


def draw_section(c, t, lit=None, people=None, field=NIGHT, city=True, sky_lit=0.0, moon_at=MOON_S, beams=True,
                 numbers=None, hall_lamp=1.0, vault_lit=0.0, gold_glow=1.0, gold=1.0, ruby_box=0.0, ruby=True,
                 vault_door=0.0, side_door=0.0, hatch=0.0, tile=0.0, trap_shaft=False, lid_a=0.0, lid_b=0.0,
                 under=1.0, drips=True, car=None, bell_ring=0.0, lamp_on=1.0, street_door=0.0, open_windows=(),
                 crew_lamp=None, clock=(11, 58), bank_clock=None):
    """The street cut open at time t.

    lit:     {("ten", storey) | ("bank", storey) | "hall": rgb}, rooms whose light is on
             (default: the crew's room, AMBER)
    people(c, where, n, rect): draws whoever is inside, after the furniture and before the walls;
             called for ("ten", 1..5), ("office", 2..3), ("hall", 1) and ("vault", 1)
    beams:   lit tenement windows throw their light across the street (True / False / set of storeys)
    hall_lamp: the guard's desk lamp 0..1; vault_lit: the gold's light filling the vault 0..1;
             gold_glow: the gold's own glow; gold: how much of it is still there; ruby_box: its
             box open; ruby: the ruby still in it
    vault_door / side_door / hatch / tile: 0 shut .. 1 open (see the helpers); trap_shaft: the
             shaft she cut under the vault exists (s08 on)
    lid_a / lid_b: the manholes' lids (0 shut .. 1 off); under: the earth cut open 0..1
    car:     None (none), or a dict of car_rear's keywords (cx defaults to CAR_C)
    crew_lamp: None (the crew's pendant lit if their room is lit) or (lit, swing[, pull[, colour]])
    clock:   the crew's wall clock (hh, mm); bank_clock: the bank's, in its gable (default: clock)
    """
    K.fill(c, field)
    if city:
        K.skyline(c, lit=sky_lit)
        K.moon(c, moon_at)
    lit = {("ten", CREW_FLOOR): AMBER} if lit is None else lit
    street_ground(c, t, under, lid_a, lid_b, trap_shaft, drips)      # first: the buildings stand on it
    # --- the tenement
    b = TEN
    bass.fill_polys(c, [_r(b.x0, b.roof, b.x1, GROUND, b.seed + 1)], DEEP)
    for n in range(1, b.floors + 1):
        col = lit.get(("ten", n))
        if col is not None:
            bass.fill_polys(c, [_r(*b.room(n), seed=b.seed + 200 + n)], col)
        for kind, x, polys in furniture("ten", n):
            bass.fill_polys(c, polys, INK if col is not None else DARK_INK)
        if n == CREW_FLOOR:
            lamp_args = crew_lamp if crew_lamp is not None else (col is not None, 0.0)
            pendant(c, t, *lamp_args)
            wall_clock(c, clock[0], clock[1], col is not None)
        if people is not None:
            people(c, "ten", n, b.room(n))
    _stairs(c, b, INK)
    bass.fill_polys(c, _ten_shell(tuple(sorted(open_windows)), street_door >= 1.0), INK)
    _street_door_leaf(c, street_door)
    if numbers is not None:
        floor_numbers(c, lerp(NIGHT, PAPER, 0.35), lit=numbers)
    # --- the bank
    _bank_inside(c, t, lit, people, hall_lamp, vault_lit, gold_glow, gold, ruby_box, ruby)
    bass.fill_polys(c, _bank_shell(side_door >= 1.0, vault_door >= 0.5), INK)
    bass.fill_polys(c, _vault_walls(vault_door >= 0.5), HEAVY)
    bc = clock if bank_clock is None else bank_clock               # the clock in the gable, as on the front
    K.clock_face(c, CLOCK_E, 24.0, bc[0], bc[1], seed=993)
    lin = lerp(LINE_V, AMBER, 0.45 * clamp(vault_lit))
    bass.fill_polys(c, [_r(VAULT_IN[0], VAULT_TOP - 3.0, VAULT_IN[1], VAULT_TOP, 785, 0.2),
                        _r(VAULT_IN[1] - 3.0, VAULT_TOP, VAULT_IN[1], FEET, 786, 0.2),
                        _r(VAULT_IN[0], FEET, VAULT_IN[1], FEET + 3.0, 787, 0.2),
                        _r(VAULT_IN[0], VAULT_TOP, VAULT_IN[0] + 3.0, VDOOR[1], 788, 0.2)], lin)
    _vault_door(c, vault_door, vault_lit)
    if side_door < 1.0:
        w = (BW - 4.0) * (1.0 - ease("inout", clamp(side_door)))
        if w > 0.5:
            bass.fill_polys(c, [_r(SIDE_DOOR[0] + 2.0, SIDE_DOOR[1], SIDE_DOOR[0] + 2.0 + w, SIDE_DOOR[3], 931, 0.3)],
                            DOOR_LEAF)
    if under >= 1.0:                                     # the hatch's shaft comes up through the floor
        bass.fill_polys(c, [[(HATCH[0], FEET), (HATCH[1], FEET), (HATCH[1], GROUND + SLAB / 2 + 1.0),
                             (HATCH[0], GROUND + SLAB / 2 + 1.0)]], TUNNEL)
    _hatch_lid(c, hatch)
    _tile(c, tile, trap_shaft and under >= 1.0)
    bell(c, t, bell_ring)
    # --- the street
    if beams:
        c.save()
        c.rectangle(STREET[0], 0.0, STREET[1] - STREET[0], GROUND)
        c.clip()
        for key, col in lit.items():
            if isinstance(key, tuple) and key[0] == "ten" and key[1] > 1 and (beams is True or key[1] in beams):
                beam(c, key[1], col)
        c.restore()
    lamp(c, lamp_on)
    if car is not None:
        kw = dict(car)
        car_rear(c, kw.pop("cx", CAR_C), t, **kw)


# ============================================================================ the elevation
TEN_WIN_X = ((36.0, 86.0), (128.0, 178.0), (232.0, 282.0))     # the tenement's window columns
CREW_WIN = (CREW_FLOOR, 2)                                       # the crew's window: storey 4, nearest the street
TEN_DOOR_E = (236.0, GROUND - 146.0, 284.0, GROUND)
BANK_WIN_E = ((750.0, 794.0), (850.0, 894.0), (950.0, 994.0))   # the barred, arched hall windows
SIDE_DOOR_E = (640.0, GROUND - 150.0, 690.0, GROUND)
BELL_E = (665.0, GROUND - 190.0)
PILASTERS_E = (632.0, 728.0, 838.0, 948.0, 1048.0)
OFFICE_WIN_E = ((660.0, 700.0), (760.0, 806.0), (870.0, 916.0), (980.0, 1020.0))
CLOCK_E = (PED_APEX[0], BANK_ROOF - CORNICE - 36.0)


def ten_window_e(n, j):
    """The tenement's window (storey n, column j) on the elevation."""
    x0, x1 = TEN_WIN_X[j]
    return (x0, level(n + 1) + 60.0, x1, level(n) - 62.0)


def elevation_windows():
    """Every window on the elevation: [(key, rect)] (the title's letters become these)."""
    out = []
    for n in range(2, TEN.floors + 1):
        for j in range(3):
            out.append((("ten", n, j), ten_window_e(n, j)))
    out.append((("ten", 1, 0), (40.0, GROUND - 130.0, 128.0, GROUND - 44.0)))
    for j, (x0, x1) in enumerate(BANK_WIN_E):
        out.append((("bank", 1, j), (x0, GROUND - 178.0, x1, GROUND - 48.0)))
    for n in (2, 3):
        for j, (x0, x1) in enumerate(OFFICE_WIN_E):
            y0, y1 = bank_level(n + 1) + 56.0, bank_level(n) - 52.0
            out.append((("bank", n, j), (x0, y0, x1, y1)))
    return out


def _arch(r, seed):
    x0, y0, x1, y1 = r
    w = x1 - x0
    pts = [(x0, y1), (x0, y0 + w / 2.0)]
    for k in range(1, 10):
        a = math.pi * k / 10.0
        pts.append(((x0 + x1) / 2.0 - w / 2.0 * math.cos(a), y0 + w / 2.0 - w / 2.0 * math.sin(a)))
    pts += [(x1, y0 + w / 2.0), (x1, y1)]
    return bass.orient(bass.cut(pts, seed=seed, amp=0.3, seg=(14.0, 40.0)), True)


@lru_cache(maxsize=1)
def _bank_face_polys():
    """The bank's front on the elevation, in INK and the members' tone: [(polys, colour)]."""
    x0, x1 = BANK
    out = [([_r(x0, BANK_ROOF, x1, GROUND, 940, 0.6),
             _r(x0 - 14.0, BANK_ROOF - CORNICE, x1 + 14.0, BANK_ROOF, 941, 0.5),
             bass.orient(bass.cut([(x0 - 8.0, BANK_ROOF - CORNICE), PED_APEX, (x1 + 8.0, BANK_ROOF - CORNICE)],
                                  seed=942, amp=0.5, seg=(40.0, 90.0)), True)], INK)]
    m = []
    for i in range(1, 6):                               # the base's rustication
        y = GROUND - 38.0 * i
        if y > bank_level(2):
            m.append(_r(x0 + 4.0, y - 1.5, x1 - 4.0, y + 1.5, 943 + i, 0.3))
    m.append(_r(x0, bank_level(2) - 10.0, x1, bank_level(2) + 2.0, 950, 0.4))              # the string course
    for i, px in enumerate(PILASTERS_E):                # the colonnade
        m.append(_r(px - 11.0, BANK_ROOF + 14.0, px + 11.0, bank_level(2) - 10.0, 951 + i, 0.4))
        m.append(_r(px - 15.0, BANK_ROOF + 4.0, px + 15.0, BANK_ROOF + 14.0, 957 + i, 0.3))
    m.append(_r(x0 - 4.0, BANK_ROOF - 6.0, x1 + 4.0, BANK_ROOF + 4.0, 962, 0.3))
    k = 0.80
    yc = BANK_ROOF - CORNICE - 6.0
    m.append(bass.orient(bass.cut([(lerp(PED_APEX[0], x0, k) + 12.0, yc), (PED_APEX[0], PED_APEX[1] + 18.0),
                                   (lerp(PED_APEX[0], x1, k) - 12.0, yc)], seed=963, amp=0.4, seg=(30.0, 80.0)), True))
    out.append((m, FACE_TONE))
    return out


def bank_face(c, t, windows=None, low=1.0, guard_x=None, clock=(11, 58), bell_ring=0.0, side_door=0.0):
    """The bank's front on the elevation. windows: {key: rgb} overrides; low: the guard's lamp
    lighting the hall's windows low (0..1); guard_x: where his flashlight's patch is (x), or None."""
    for polys, col in _bank_face_polys():
        bass.fill_polys(c, polys, col)
    windows = windows or {}
    for key, r in elevation_windows():
        if key[0] != "bank":
            continue
        if key[1] == 1:
            col = windows.get(key, lerp(SHUT, LOW_LAMP, clamp(low)))
            shape = _arch(r, 965 + key[2])
            bass.fill_polys(c, [shape], col)
            if guard_x is not None and abs(guard_x - (r[0] + r[2]) / 2.0) < 70.0:
                c.save()
                c.new_path()
                for x, y in shape:
                    c.line_to(x, y)
                c.close_path()
                c.clip()
                K.dot(c, (guard_x, r[3] - 40.0), 26.0, PAPER, seed=968, alpha=0.30)
                c.restore()
            bars = [_r(xx - 1.4, r[1] + 6.0, xx + 1.4, r[3], 969 + key[2] * 3 + i, 0.2)
                    for i, xx in enumerate((r[0] + (r[2] - r[0]) * f for f in (0.25, 0.5, 0.75)))]
            bars.append(_r(r[0], (r[1] + r[3]) / 2.0 + 6.0, r[2], (r[1] + r[3]) / 2.0 + 9.0, 978 + key[2], 0.2))
            bass.fill_polys(c, bars, lerp(STEEL, INK, 0.45))
        else:
            bass.fill_polys(c, [_r(*r, seed=980 + key[1] * 5 + key[2], amp=0.4)], windows.get(key, SHUT))
    d0 = SIDE_DOOR_E
    bass.fill_polys(c, [_r(d0[0] - 6.0, d0[1] - 8.0, d0[2] + 6.0, d0[3], 990, 0.3)], FACE_TONE)
    g = ease("inout", clamp(side_door))
    bass.fill_polys(c, [_r(*d0, seed=991, amp=0.3)], DEEP if g > 0.0 else lerp(INK, STEEL, 0.12))
    if g > 0.0:
        bass.fill_polys(c, [_r(d0[0], d0[1], d0[0] + (d0[2] - d0[0]) * (1.0 - g), d0[3], 992, 0.3)], lerp(INK, STEEL, 0.12))
    K.clock_face(c, CLOCK_E, 24.0, clock[0], clock[1], seed=993)
    col = lerp(lerp(STEEL, NIGHT, 0.1), RED, clamp(bell_ring * 1.5))
    rock = 13.0 * math.sin(t * 2.0 * math.pi * 9.0) * clamp(bell_ring)
    bass.fill_polys(c, [_r(BELL_E[0] - 14.0, BELL_E[1] - 16.0, BELL_E[0] + 14.0, BELL_E[1] - 12.0, 994, 0.2)], INK)
    K.bell(c, BELL_E, 0.9, col, seed=995, ring=rock)


def ten_face(c, t, windows=None, street_door=0.0):
    """The tenement's front on the elevation. windows: {("ten", n, j): rgb} (default: the crew's
    window AMBER, the rest SHUT)."""
    b = TEN
    windows = {("ten",) + CREW_WIN: AMBER} if windows is None else windows
    bass.fill_polys(c, [_r(b.x0, b.roof, b.x1, GROUND, 1001, 0.6)], INK)
    bass.fill_polys(c, [p for p in _ten_shell() if True][-2:], INK)     # parapet and tank
    for key, r in elevation_windows():
        if key[0] != "ten":
            continue
        bass.fill_polys(c, [_r(*r, seed=1002 + key[1] * 5 + key[2], amp=0.4)], windows.get(key, SHUT))
        bass.fill_polys(c, [_r(r[0] - 4.0, r[3], r[2] + 4.0, r[3] + 5.0, 1020 + key[1] * 5 + key[2], 0.3)],
                        lerp(INK, STEEL, 0.28))
    d = TEN_DOOR_E
    g = ease("inout", clamp(street_door))
    bass.fill_polys(c, [_r(*d, seed=1040, amp=0.3)], DEEP if g > 0.0 else lerp(INK, STEEL, 0.12))
    if g > 0.0:
        bass.fill_polys(c, [_r(d[0], d[1], d[0] + (d[2] - d[0]) * (1.0 - g), d[3], 1041, 0.3)], lerp(INK, STEEL, 0.12))
    bass.fill_polys(c, [_r(d[0] - 6.0, d[1] - 10.0, d[2] + 6.0, d[1], 1042, 0.3)], lerp(INK, STEEL, 0.28))


def draw_elevation(c, t, field=NIGHT, city=True, sky_lit=0.0, moon_at=MOON_E, windows=None, low=1.0, guard_x=None,
                   clock=(11, 58), bell_ring=0.0, side_door=0.0, street_door=0.0, car=None, lid_a=0.0, lid_b=0.0,
                   lamp_on=1.0, figures=None, under=0.0, trap_shaft=False):
    """The street's two fronts, flat on the night field (OPPOSITE's elevation), at time t.
    windows: {key: rgb} for the lit windows (keys from elevation_windows); car: None or a dict of
    car_rear's keywords; figures(c): drawn on the street before the lamp; under: the ground cut
    open below the road (as the section's)."""
    K.fill(c, field)
    if city:
        K.skyline(c, lit=sky_lit)
        if moon_at is not None:
            K.moon(c, moon_at)
    ten_face(c, t, None if windows is None else {k: v for k, v in windows.items() if k[0] == "ten"}, street_door)
    bank_face(c, t, None if windows is None else {k: v for k, v in windows.items() if k[0] == "bank"}, low, guard_x,
              clock, bell_ring, side_door)
    street_ground(c, t, under, lid_a, lid_b, trap_shaft)
    if car is not None:
        kw = dict(car)
        car_rear(c, kw.pop("cx", CAR_C), t, **kw)
    if figures is not None:
        figures(c)
    lamp(c, lamp_on)


# ============================================================================ the fronts, face on (set px for Bk.Cam)
SIDE_BAY = (30.0, 170.0)                      # the bank's side bay, left of the wing
SIDE_DOOR_F = (78.0, -200.0, 142.0, 0.0)      # the side door, face on
BELL_F = (110.0, -270.0)                      # the bell over it
CAR_FX = -60.0                                # the Knight's car (middle), face on, nose left
F_MOON = (872.0, -1060.0)


@lru_cache(maxsize=1)
def _front_neighbours():
    """The buildings either side of the bank's front and the far city behind it."""
    far = []
    x = -700.0
    i = 0
    while x < 1700.0:
        w = 90.0 + 120.0 * hash01(i, 31)
        top = -620.0 - 420.0 * hash01(i, 32)
        far.append(bass.cut_rect(x, top, x + w, 40.0, seed=1300 + i, amp=0.8))
        x += w + 4.0
        i += 1
    near = [bass.cut_rect(-700.0, -720.0, SIDE_BAY[0], 20.0, seed=1320, amp=0.8),
            bass.cut_rect(Bk.FACADE_X[1], -820.0, 1700.0, 20.0, seed=1321, amp=0.8)]
    wins = []
    for row in range(4):
        for col in range(5):
            x0 = -640.0 + col * 128.0
            if x0 + 48.0 < SIDE_BAY[0] - 24.0:
                wins.append(((x0, -660.0 + row * 160.0, x0 + 48.0, -578.0 + row * 160.0), ("L", row, col)))
            x1 = Bk.FACADE_X[1] + 50.0 + col * 128.0
            wins.append(((x1, -760.0 + row * 160.0, x1 + 48.0, -678.0 + row * 160.0), ("R", row, col)))
    return far, near, wins


def _side_bay(c, t, door, bell_ring, lit_inside=None):
    x0, x1 = SIDE_BAY
    Bk.rect(c, (x0, -Bk.FACADE_H, x1 + 2.0, 0.0), STONE, seed=1330, amp=0.6)
    joints = []
    for i in range(1, 5):
        joints.append(bass.cut_rect(x0, -16.0 * i - 1.6, x1, -16.0 * i + 1.6, seed=1331 + i, amp=0.3))
    bass.fill_polys(c, joints, STONE_DK)
    Bk.rect(c, (x0, -Bk.FACADE_H + 40.0, x1, -Bk.FACADE_H + 52.0), STONE_SH, seed=1336, amp=0.4)
    d = SIDE_DOOR_F
    Bk.rect(c, (d[0] - 12.0, d[1] - 16.0, d[2] + 12.0, d[3]), STONE_DK, seed=1337, amp=0.4)
    g = ease("outback", clamp(door)) if 0.0 < door < 1.0 else clamp(door)
    inside = lit_inside if lit_inside is not None else DEEP
    Bk.rect(c, d, inside if door > 0.0 else INK, seed=1338, amp=0.3)
    # the leaf swings out toward us, hinged on its left edge: it narrows, then shows its edge
    w = (d[2] - d[0]) * math.cos(math.radians(min(100.0, 100.0 * g)))
    if abs(w) > 0.6:
        lx1 = d[0] + max(w, 0.0)
        lx0 = d[0] + min(w, 0.0)
        Bk.rect(c, (lx0, d[1], max(lx1, lx0 + 4.0), d[3]), lerp(INK, STEEL, 0.18), seed=1339, amp=0.2)
        for k in (0.3, 0.7):
            Bk.band(c, (lx0, d[1] + (d[3] - d[1]) * k), (max(lx1, lx0 + 4.0), d[1] + (d[3] - d[1]) * k), 3.0,
                    lerp(STEEL, INK, 0.3), seed=1340)
    else:
        Bk.rect(c, (d[0] - 3.0, d[1], d[0] + 3.0, d[3]), lerp(INK, STEEL, 0.18), seed=1341, amp=0.2)
    col = lerp(lerp(STEEL, INK, 0.25), RED, clamp(bell_ring * 1.5))
    rock = 13.0 * math.sin(t * 2.0 * math.pi * 9.0) * clamp(bell_ring)
    Bk.band(c, (BELL_F[0] - 26.0, BELL_F[1] - 24.0), (BELL_F[0] + 26.0, BELL_F[1] - 24.0), 5.0, INK, seed=1342)
    K.bell(c, BELL_F, 1.35, col, seed=1343, ring=rock)


def _wing_lit(c, t, low, guard_x):
    """DOUBLE CROSS's wing (three barred, arched windows) with its windows lit low by the guard's
    lamp, and the patch of his flashlight passing behind them."""
    for i, (polys, col) in enumerate(Bk._wing()):
        if col is INK and len(polys) == 3:               # the windows
            for j, shape in enumerate(polys):
                bass.fill_polys(c, [shape], lerp(INK, LOW_LAMP, clamp(low)))
                if guard_x is not None:
                    c.save()
                    c.new_path()
                    for x, y in shape:
                        c.line_to(x, y)
                    c.close_path()
                    c.clip()
                    K.dot(c, (guard_x, -250.0), 58.0, PAPER, seed=1350, alpha=0.32)
                    K.dot(c, (guard_x, -250.0), 30.0, PAPER, seed=1351, alpha=0.30)
                    c.restore()
            continue
        bass.fill_polys(c, polys, col)


ROAD_DEPTH = 300.0                            # the road seen from above (bank_front road="above"): y 0..this
LID_ABOVE = (Bk.MANHOLE_X, 120.0)             # manhole A's lid on it


def road_above(c, vx0, vx1, lamp_on=1.0):
    """The street seen from high up (the crew's window): the road as a band below the bank's
    curb, manhole A's lid an ellipse on it, the lamp's pool at the near curb."""
    Bk.rect(c, (vx0 - 40.0, 0.0, vx1 + 40.0, ROAD_DEPTH + 900.0), lerp(NIGHT, INK, 0.55), amp=0.0)
    Bk.rect(c, (vx0 - 40.0, 0.0, vx1 + 40.0, 14.0), lerp(NIGHT, STEEL, 0.25), amp=0.0)          # the bank's curb
    Bk.rect(c, (vx0 - 40.0, ROAD_DEPTH, vx1 + 40.0, ROAD_DEPTH + 900.0), lerp(NIGHT, INK, 0.30), amp=0.0)   # our sidewalk
    Bk.band(c, (vx0 - 40.0, ROAD_DEPTH), (vx1 + 40.0, ROAD_DEPTH), 6.0, lerp(NIGHT, STEEL, 0.30), seed=1395)
    if lamp_on > 0.0:
        K.pool(c, (Bk.MANHOLE_X - 120.0, ROAD_DEPTH - 10.0), 300.0, 70.0, AMBER, 0.28 * lamp_on)
    Bk.ellipse(c, LID_ABOVE, 40.0, 13.0, lerp(STEEL, INK, 0.30), n=40)
    Bk.ellipse(c, LID_ABOVE, 34.0, 10.0, lerp(STEEL, INK, 0.45), n=40)


def bank_front(c, cam, t, clock=(11, 58), bell_ring=0.0, side_door=0.0, low=1.0, guard_x=None, car=True,
               car_x=CAR_FX, car_door=0.0, headlights=0.0, lid=0.0, cut=0.0, police=(), sky=NIGHT, moon=True,
               neighbour_lit=None, inside_lit=None, extra=None, road="section", lamp_on=1.0):
    """The bank's front face on (set px, the road at y 0): the side bay with the side door and the
    bell (left), DOUBLE CROSS's wing (its barred windows lit low by the guard's lamp), the portico,
    the pediment and its clock (hh, mm); manhole A in front of the wing; the Knight's car in
    profile at the curb (nose left). police: [dict(x=..., facing=..., ...)] police cars in profile.
    neighbour_lit: {("L"|"R", row, col): rgb}. extra(c): drawn in set px after the front, before
    the cars (figures on the pavement). road: "section" (the ground cut, as Bk.ground) or
    "above" (seen from high up: road_above)."""
    vx0, vy0, vx1, vy1 = cam.view(80.0)
    with cam.on(c):
        if vy0 < 40.0:
            if sky is not None:
                Bk.rect(c, (vx0 - 10.0, vy0 - 10.0, vx1 + 10.0, 2.0), sky, amp=0.0)
            far, near, wins = _front_neighbours()
            bass.fill_polys(c, far, lerp(NIGHT, STEEL, 0.16))
            if moon:
                Bk.disc(c, F_MOON, 58.0, PAPER, seed=3, n=64)
            bass.fill_polys(c, near, lerp(NIGHT, STEEL, 0.38))
            for r, key in wins:
                col = (neighbour_lit or {}).get(key, lerp(NIGHT, INK, 0.35))
                Bk.rect(c, r, col, seed=1360 + key[1] * 7 + key[2], amp=0.5)
            _side_bay(c, t, side_door, bell_ring, inside_lit)
            _wing_lit(c, t, low, guard_x)
            for polys, col in Bk._entablature():
                bass.fill_polys(c, polys, col)
            Bk.rect(c, (SIDE_BAY[0] - 10.0, -Bk.FACADE_H - 12.0, Bk.FACADE_X[0], -Bk.FACADE_H + 6.0), STONE, seed=1370,
                    amp=0.5)
            for polys, col in Bk._portico():
                bass.fill_polys(c, polys, col)
            bass.fill_polys(c, Bk._steps(), STONE)
            for polys, col in Bk._pediment():
                bass.fill_polys(c, polys, col)
            Bk.disc(c, Bk.CLOCK_AT, 40.0, STONE_DK, seed=1371, n=48)
            K.clock_face(c, Bk.CLOCK_AT, 34.0, clock[0], clock[1], seed=1372)
        if vy1 > -10.0:
            if road == "above":
                road_above(c, vx0, vx1, lamp_on)
            else:
                Bk.ground(c, t, cut, lid, view_x=(vx0 - 40.0, vx1 + 40.0))
        if extra is not None:
            extra(c)
        if vy0 < 40.0:
            if car:
                car_side(c, t, car_x, facing=-1, door=car_door, headlights=headlights)
            for pc in police:
                kw = dict(pc)
                car_side(c, t, kw.pop("x"), police=True, **kw)


def car_side(c, t, x, facing=-1, door=0.0, headlights=0.0, police=False, lurch=0.0, gy=0.0):
    """A car in profile (DOUBLE CROSS's), wheels on gy, its middle at x, nose toward `facing`
    (-1 left). door 0..1: the driver's door swung open toward us. police: a light bar on the
    roof and a pale stripe. lurch (deg): the body pitches (the brake, the start)."""
    rim, shell, wins = Bk._car_polys()
    L = Bk.CAR_L
    x0, x1 = -L / 2, L / 2
    c.save()
    c.translate(x, gy)
    if facing > 0:
        c.scale(-1.0, 1.0)
    on = clamp(headlights)
    if on > 0.0:
        g = ease("outback", on) if on < 1.0 else 1.0
        reach = 380.0 * g
        bass.fill_polys(c, [bass.orient([(x0 + 4.0, -38.0), (x0 + 4.0, -26.0), (x0 - reach, 6.0), (x0 - reach, -70.0)],
                                        True)], PAPER, 0.12 * on)
        Bk.ellipse(c, (x0 - reach * 0.55, 0.0), reach * 0.5, 6.0, PAPER, 0.18 * on, n=32)
    c.save()
    c.translate(0.0, -18.0)
    c.rotate(math.radians(lurch))
    c.translate(0.0, 18.0)
    bass.fill_polys(c, [rim], STEEL)
    bass.fill_polys(c, [shell], INK)
    bass.fill_polys(c, wins, GLASS)
    if police:
        Bk.band(c, (x0 + 10.0, -36.0), (x1 - 8.0, -36.0), 7.0, lerp(PAPER, STEEL, 0.35), seed=1380)
        c.save()
        c.translate(-6.0, -96.0)
        if facing > 0:
            c.scale(-1.0, 1.0)
        K.light_bar(c, (0.0, 0.0), t, s=1.5, seed=1381 + int(x) % 7)
        c.restore()
    if door > 0.0:                                       # the driver's door, toward us
        g = clamp(door)
        dx0, dx1 = x0 + 92.0, x0 + 152.0
        bass.fill_polys(c, [[(dx0, -86.0), (dx1, -86.0), (dx1, -20.0), (dx0, -20.0)]], DEEP, g)
        bass.fill_polys(c, [bass.orient([(dx0 - 4.0, -90.0), (dx0 + (dx1 - dx0) * (1.0 - g) + 2.0, -90.0),
                                         (dx0 + (dx1 - dx0) * (1.0 - g) + 2.0, -16.0), (dx0 - 4.0, -16.0)], True)], INK)
        Bk.band(c, (dx0 - 4.0, -90.0), (dx0 - 4.0, -16.0), 3.0, STEEL, seed=1382)
    Bk.band(c, (x0 - 4.0, -18.0), (x0 + 18.0, -18.0), 6.0, STEEL, seed=1383)
    Bk.band(c, (x1 - 16.0, -18.0), (x1 + 4.0, -18.0), 6.0, STEEL, seed=1384)
    Bk.disc(c, (x0 + 4.0, -32.0), 6.5, lerp(lerp(STEEL, INK, 0.3), PAPER, on), seed=1385, n=14)
    Bk.disc(c, (x1 - 2.0, -36.0), 5.0, RED, seed=1386, n=12)
    c.restore()
    for i, wx in enumerate((x0 + 52.0, x1 - 50.0)):
        Bk.disc(c, (wx, -18.0), 20.0, INK, seed=1387 + i, n=28)
        Bk.disc(c, (wx, -18.0), 8.0, STEEL, seed=1389 + i, n=16)
    c.restore()


# --- the tenement's front, face on
TF_X = (60.0, 1020.0)
TF_BAYS = (170.0, 355.0, 540.0, 725.0, 910.0)
TF_DOOR = (502.0, -176.0, 578.0, 0.0)
TF_CREW = (CREW_FLOOR, 2)                     # the crew's window: storey 4, over the street door
TF_LAMP = 300.0
TF_MH_B = 540.0                               # manhole B, face on: in the road before the door
TF_LID_L = 58.0


def tf_window(n, j):
    """The tenement's front, face on: storey n's window in bay j (set px)."""
    cx = TF_BAYS[j]
    return (cx - 38.0, -n * FH + 52.0, cx + 38.0, -(n - 1) * FH - 46.0)


@lru_cache(maxsize=1)
def _tf_static():
    x0, x1 = TF_X
    roof = -5.0 * FH
    far = []
    x = -700.0
    i = 0
    while x < 1800.0:
        w = 90.0 + 120.0 * hash01(i, 41)
        top = roof - 120.0 - 380.0 * hash01(i, 42)
        far.append(bass.cut_rect(x, top, x + w, 40.0, seed=1400 + i, amp=0.8))
        x += w + 4.0
        i += 1
    near = [bass.cut_rect(-700.0, roof + 160.0, x0, 20.0, seed=1420, amp=0.8),
            bass.cut_rect(x1, roof + 60.0, 1800.0, 20.0, seed=1421, amp=0.8)]
    body = [bass.cut_rect(x0, roof, x1, 0.0, seed=1422, amp=0.7), bass.cut_rect(x0 - 10.0, roof - 28.0, x1 + 10.0, roof,
                                                                                  seed=1423, amp=0.5)]
    tank = bass.orient(bass.cut([(220.0, roof - 28.0), (230.0, roof - 90.0), (330.0, roof - 90.0), (340.0, roof - 28.0)],
                                seed=1424, amp=0.4), True)
    tank2 = bass.cut_rect(214.0, roof - 200.0, 346.0, roof - 90.0, seed=1425, amp=0.5)
    sills = []
    for n in range(2, 6):
        for j in range(5):
            r = tf_window(n, j)
            sills.append(bass.cut_rect(r[0] - 6.0, r[3], r[2] + 6.0, r[3] + 7.0, seed=1430 + n * 5 + j, amp=0.3))
            sills.append(bass.cut_rect(r[0] - 4.0, r[1] - 8.0, r[2] + 4.0, r[1], seed=1460 + n * 5 + j, amp=0.3))
    for n in range(2, 6):
        y = -(n - 1) * FH
        sills.append(bass.cut_rect(x0, y - 4.0, x1, y + 2.0, seed=1490 + n, amp=0.3))
    return far, near, body, [tank, tank2], sills


def _lamp_face(c, x, on=1.0):
    """The cast-iron street lamp, face on, at x (Bk's lamp moved)."""
    post, glass, beam_ = Bk._lamp_polys()
    c.save()
    c.translate(x - Bk.LAMP_X, 0.0)
    if on > 0.0:
        bass.fill_polys(c, [beam_], AMBER, 0.10 * on)
        Bk.ellipse(c, (Bk.LAMP_X, 0.0), 168.0, 10.0, AMBER, 0.22 * on, n=40)
    bass.fill_polys(c, post, INK)
    bass.fill_polys(c, [glass], lerp(INK, AMBER, 0.25 + 0.75 * on))
    c.restore()


def lid_face(c, x, u):
    """Manhole B's lid on the road face on, sliding off to the left: u 0 shut .. 1 off."""
    g = ease("inout", clamp(u))
    lx = x - TF_LID_L / 2.0 - g * (TF_LID_L + 14.0)
    Bk.band(c, (lx, 1.5), (lx + TF_LID_L, 1.5), 8.0, lerp(STEEL, PAPER, 0.12 + 0.2 * g), seed=1500)


def tenement_front(c, cam, t, windows=None, at_window=None, lid=0.0, lamp_on=1.0, street_door=0.0, sky=NIGHT,
                   moon=True, extra=None, far_lit=0.0):
    """The tenement's front face on (set px, the road at y 0), seen from the bank's curb: five
    storeys of windows (the crew's, storey 4, over the street door), the street door, the lamp on
    the curb, manhole B in the road before the door. windows: {(n, j): rgb} lit windows (the rest
    dark); at_window(c, n, j, rect): draws a neighbour in a window; extra(c): figures on the
    pavement, drawn before the lamp."""
    vx0, vy0, vx1, vy1 = cam.view(80.0)
    far, near, body, tank, sills = _tf_static()
    windows = windows or {}
    with cam.on(c):
        if sky is not None:
            Bk.rect(c, (vx0 - 10.0, vy0 - 10.0, vx1 + 10.0, 2.0), sky, amp=0.0)
        bass.fill_polys(c, far, lerp(NIGHT, STEEL, 0.16))
        if far_lit > 0.0:
            for i, p in enumerate(far):
                if hash01(i, 77) < far_lit:
                    xs = [q[0] for q in p]
                    ys = [q[1] for q in p]
                    cx, cy = (min(xs) + max(xs)) / 2.0, min(ys) + 60.0
                    Bk.rect(c, (cx - 12.0, cy, cx + 12.0, cy + 30.0), AMBER, seed=1510 + i, amp=0.4)
        if moon:
            Bk.disc(c, (200.0, -1300.0), 58.0, PAPER, seed=3, n=64)
        bass.fill_polys(c, near, lerp(NIGHT, STEEL, 0.38))
        bass.fill_polys(c, body + tank, INK)
        bass.fill_polys(c, sills, lerp(INK, STEEL, 0.26))
        for n in range(2, 6):
            for j in range(5):
                r = tf_window(n, j)
                col = windows.get((n, j), SHUT)
                Bk.rect(c, r, col, seed=1520 + n * 5 + j, amp=0.4)
                if at_window is not None and (n, j) in windows:
                    c.save()
                    c.rectangle(r[0], r[1], r[2] - r[0], r[3] - r[1])
                    c.clip()
                    at_window(c, n, j, r)
                    c.restore()
                Bk.band(c, ((r[0] + r[2]) / 2.0, r[1]), ((r[0] + r[2]) / 2.0, r[3]), 3.0, INK, seed=1550)
                Bk.band(c, (r[0], (r[1] + r[3]) / 2.0), (r[2], (r[1] + r[3]) / 2.0), 3.0, INK, seed=1551)
        for j in (0, 1, 3, 4):                           # the shop windows on the street floor
            cx = TF_BAYS[j]
            Bk.rect(c, (cx - 60.0, -150.0, cx + 60.0, -40.0), windows.get((1, j), SHUT), seed=1560 + j, amp=0.4)
        d = TF_DOOR
        g = ease("inout", clamp(street_door))
        Bk.rect(c, (d[0] - 10.0, d[1] - 14.0, d[2] + 10.0, d[3]), lerp(INK, STEEL, 0.26), seed=1570, amp=0.4)
        Bk.rect(c, d, DEEP if g > 0.0 else lerp(INK, STEEL, 0.12), seed=1571, amp=0.3)
        if g > 0.0:
            Bk.rect(c, (d[0], d[1], d[0] + (d[2] - d[0]) * (1.0 - g), d[3]), lerp(INK, STEEL, 0.12), seed=1572, amp=0.3)
        # the road
        Bk.rect(c, (vx0 - 40.0, 0.0, vx1 + 40.0, 1600.0), INK, amp=0.0)
        Bk.band(c, (vx0 - 40.0, 1.0), (vx1 + 40.0, 1.0), 4.0, lerp(STEEL, NIGHT, 0.25), seed=1573)
        lid_face(c, TF_MH_B, lid)
        if extra is not None:
            extra(c)
        _lamp_face(c, TF_LAMP, lamp_on)
