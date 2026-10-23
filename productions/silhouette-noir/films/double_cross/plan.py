"""DOUBLE CROSS: the plan. The bank, its streets and its sewer as the Architect drew them, the
four routes, the camera that looks at the plan, and the drawing of it all.

Plan px, north up. At PlanCam(540, 960, 1.0, 90) the sheet fills the frame (x 70-1010,
y 150-1770). The camera is orthographic: phi is its elevation (90 = straight down, ~55 = the
table view, 0 = eye level), yaw turns the plan about the vertical. At phi < 90 upright things
(walls, pieces) stand up by cos(phi) and the ground is foreshortened by sin(phi).

    cam = P.PlanCam(540, 960, 1.0, phi=60)
    with cam.ground(c):                 # draw in plan px on the (foreshortened) paper
        P.draw_sheet(c); P.draw_plan(c)
    x, y = cam.to_view(P.X_VAULT)       # a plan point in frame px (z = height above the paper)
    K.piece(c, "queen", cam.to_view(p), 90 * cam.zoom, K.PAPER, squash=cam.upright())
"""
import math
from contextlib import contextmanager

import cairo

from engine import bass, draw
from engine.core import clamp, ease, lerp
from films.double_cross import kit as K

# ============================================================================ geometry
SHEET = (70.0, 150.0, 1010.0, 1770.0)
BACK_ST = (230.0, 330.0)               # the back street's curbs (y)
FRONT_ST = (1350.0, 1450.0)            # the front street's curbs (y)
ALLEY_X = (910.0, 1004.0)
BANK = (170.0, 380.0, 910.0, 1300.0)
VAULT = (360.0, 430.0, 720.0, 700.0)
X_VAULT = (540.0, 565.0)               # X marks the spot: the vault's middle
VAULT_DOOR = (540.0, 700.0)
DOOR_GAP = (482.0, 598.0)              # the round door's opening in the vault's south wall
MANHOLE_A = (250.0, 1400.0)            # in the front street: the way in
MANHOLE_B = (450.0, 280.0)             # in the back street: her way out
HATCH = (450.0, 1150.0)                # the sewer's hatch, in the store room floor
STORE_DOOR = (500.0, 1150.0)
GUARD_POST = (240.0, 900.0)
INTERSECTION = (200.0, 860.0, 880.0, 940.0)
SIDE_DOOR = (910.0, 1100.0)
BELL_AT = (944.0, 1060.0)              # the alarm bell, outside the side door
CAR = (930.0, 1400.0)                  # the getaway car, at the alley's mouth
RUBY = (680.0, 518.0)                  # the one deposit box that matters
TRAPDOOR = (450.0, 600.0)              # under the vault floor, on the sewer branch (Plan B)
DOT = TRAPDOOR                         # the chalk dot she leaves there in s03
SEWER_MAIN = [(70.0, 1400.0), (1010.0, 1400.0)]
SEWER_BRANCH = [(450.0, 1400.0), (450.0, 280.0)]

# walls: (x0, y0, x1, y1), kind; draw-on groups for the title
_EXT = [(170.0, 380.0, 910.0, 396.0), (894.0, 380.0, 910.0, 1080.0), (894.0, 1120.0, 910.0, 1300.0),
        (790.0, 1284.0, 910.0, 1300.0), (170.0, 1284.0, 700.0, 1300.0), (170.0, 380.0, 186.0, 1300.0)]
_VAULT = [(360.0, 430.0, 720.0, 460.0), (690.0, 430.0, 720.0, 700.0), (598.0, 670.0, 720.0, 700.0),
          (360.0, 670.0, 482.0, 700.0), (360.0, 430.0, 390.0, 700.0)]
_INT = [(495.0, 700.0, 505.0, 850.0), (575.0, 700.0, 585.0, 850.0),
        (186.0, 850.0, 505.0, 860.0), (575.0, 850.0, 894.0, 860.0),
        (186.0, 940.0, 505.0, 950.0), (575.0, 940.0, 894.0, 950.0),
        (495.0, 950.0, 505.0, 1130.0), (495.0, 1170.0, 505.0, 1284.0),
        (575.0, 950.0, 585.0, 1080.0), (575.0, 1120.0, 585.0, 1284.0)]
WALLS = [(r, "ext") for r in _EXT] + [(r, "vault") for r in _VAULT] + [(r, "int") for r in _INT]
WALL_H = {"ext": 150.0, "vault": 160.0, "int": 120.0}

# the routes (plan px)
ROUTE_IN = [MANHOLE_A, (450.0, 1400.0), HATCH, (540.0, 1150.0), (540.0, 900.0), VAULT_DOOR, X_VAULT]
ROUTE_OUT = [X_VAULT, VAULT_DOOR, (540.0, 900.0), (540.0, 1150.0), HATCH, (450.0, 1400.0), MANHOLE_A,
             (250.0, 1368.0), (880.0, 1368.0), CAR]
ROUTE_KNIGHT = [VAULT_DOOR, (540.0, 1100.0), (960.0, 1100.0), (960.0, 1372.0), CAR]
ROUTE_B = [X_VAULT, TRAPDOOR, MANHOLE_B, (300.0, 280.0), (40.0, 280.0)]
# step numerals of the plan: (text, where)
STEPS = [("1", (196.0, 1478.0)), ("2", (400.0, 1086.0)), ("3", (612.0, 900.0)), ("4", (612.0, 760.0)),
         ("5", (760.0, 1478.0))]


# ============================================================================ the camera
class PlanCam:
    """An orthographic camera over the plan: (cx, cy) is the plan point at frame (fx, fy)."""

    def __init__(self, cx=540.0, cy=960.0, zoom=1.0, phi=90.0, yaw=0.0, fx=540.0, fy=960.0):
        self.cx, self.cy, self.zoom, self.phi, self.yaw, self.fx, self.fy = cx, cy, zoom, phi, yaw, fx, fy

    @staticmethod
    def lerp(a, b, u):
        return PlanCam(*(lerp(x, y, u) for x, y in zip(a.tuple(), b.tuple())))

    def tuple(self):
        return (self.cx, self.cy, self.zoom, self.phi, self.yaw, self.fx, self.fy)

    def flat(self):
        """How much the paper is foreshortened (1 straight down)."""
        return math.sin(math.radians(self.phi))

    def upright(self):
        """How tall upright things look (0 straight down, 1 at eye level)."""
        return math.cos(math.radians(self.phi))

    def stand(self):
        """How tall pieces and people are drawn: cos(phi)^0.5, a cheat so they stay readable
        when seen from high up (0 straight down)."""
        return max(0.0, self.upright()) ** 0.5

    def _rot(self, x, y):
        a = math.radians(self.yaw)
        dx, dy = x - self.cx, y - self.cy
        return dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)

    def to_view(self, p, z=0.0):
        xr, yr = self._rot(p[0], p[1])
        return (self.fx + self.zoom * xr, self.fy + self.zoom * (yr * self.flat() - z * self.upright()))

    def depth(self, p):
        """Larger is nearer the camera."""
        return self._rot(p[0], p[1])[1]

    def matrix(self):
        a = math.radians(self.yaw)
        z, s = self.zoom, self.flat()
        xx, xy = z * math.cos(a), -z * math.sin(a)
        yx, yy = z * s * math.sin(a), z * s * math.cos(a)
        return cairo.Matrix(xx, yx, xy, yy, self.fx - xx * self.cx - xy * self.cy, self.fy - yx * self.cx - yy * self.cy)

    @contextmanager
    def ground(self, c):
        """Draw in plan px on the paper (z = 0)."""
        c.save()
        c.transform(self.matrix())
        try:
            yield c
        finally:
            c.restore()


TOP = PlanCam()                                  # the whole sheet from straight above
TABLE = PlanCam(540.0, 1000.0, 0.92, 52.0, -14.0)   # the table view (s02)
PLAN_CAM = PlanCam(540.0, 860.0, 1.02, 72.0, -6.0)   # s03: nearer top-down, the whole bank in frame
HANDOFF_34 = PlanCam(560.0, 1150.0, 1.15, 60.0, -6.0)  # s03's last frame = s04's first (the tilt down begins)


# ============================================================================ the sheet
def draw_sheet(c, unroll=1.0, color=K.BLUE, grid=True, border=True, seed=0):
    """The blueprint (plan px): the blue sheet, its grid, a ruled border, a north arrow and an
    empty title block; revealed from the top to fraction `unroll`, with the roll at the edge."""
    x0, y0, x1, y1 = SHEET
    yb = lerp(y0, y1, clamp(unroll))
    if yb - y0 < 1.0:
        return
    c.save()
    bass.fill_polys(c, [bass.cut_rect(x0, y0, x1, yb + 2.0, seed=seed, amp=1.0)], color)
    c.new_path()
    c.rectangle(x0, y0, x1 - x0, yb - y0)
    c.clip()
    if grid:
        x = x0 + 40.0
        while x < x1:
            major = abs((x - x0) % 200.0) < 1.0
            bass.fill_polys(c, [[(x - 0.8, y0), (x + 0.8, y0), (x + 0.8, y1), (x - 0.8, y1)]], K.PAPER,
                            0.11 if major else 0.05)
            x += 40.0
        y = y0 + 40.0
        while y < y1:
            major = abs((y - y0) % 200.0) < 1.0
            bass.fill_polys(c, [[(x0, y - 0.8), (x1, y - 0.8), (x1, y + 0.8), (x0, y + 0.8)]], K.PAPER,
                            0.11 if major else 0.05)
            y += 40.0
    if border:
        for inset, w in ((18.0, 4.0), (28.0, 1.6)):
            K.chalk_rect(c, (x0 + inset, y0 + inset, x1 - inset, y1 - inset), 1.0, w, K.PAPER, seed + 1, 0.6)
        tb = (x1 - 250.0, y1 - 130.0, x1 - 28.0, y1 - 28.0)
        K.chalk_rect(c, tb, 1.0, 2.0, K.PAPER, seed + 2, 0.5)
        for f in (0.33, 0.66):
            yy = lerp(tb[1], tb[3], f)
            K.chalk_line(c, [(tb[0], yy), (tb[2], yy)], 1.0, 1.6, K.PAPER, seed + 3, 0.4)
        K.chalk_line(c, [(tb[0] + 90.0, tb[1]), (tb[0] + 90.0, tb[3])], 1.0, 1.6, K.PAPER, seed + 4, 0.4)
        na = (x0 + 92.0, y0 + 98.0)
        K.chalk_circle(c, na, 30.0, 1.0, 2.0, K.PAPER, seed + 5, 0.55)
        bass.fill_polys(c, [bass.orient([(na[0], na[1] - 38.0), (na[0] + 11.0, na[1] + 6.0), (na[0], na[1] - 2.0),
                                         (na[0] - 11.0, na[1] + 6.0)], True)], K.PAPER, 0.7)
    c.restore()
    if unroll < 1.0:
        # the roll: a cylinder lying across the sheet at the reveal edge
        r = 34.0
        bass.fill_polys(c, [bass.cut_rect(x0 - 8.0, yb - r * 0.4, x1 + 8.0, yb + r * 1.6, seed=seed + 7, amp=0.8)],
                        color)
        for f, a in ((0.15, 0.22), (0.55, 0.12), (0.9, 0.3)):
            yy = yb - r * 0.4 + 2.0 * r * f
            bass.fill_polys(c, [[(x0 - 8.0, yy - 1.5), (x1 + 8.0, yy - 1.5), (x1 + 8.0, yy + 1.5), (x0 - 8.0, yy + 1.5)]],
                            K.PAPER, a)
        bass.fill_polys(c, [bass.cut_rect(x0 - 8.0, yb + r * 1.6 - 5.0, x1 + 8.0, yb + r * 1.6, seed=seed + 8, amp=0.4)],
                        K.INK, 0.5)


# ============================================================================ the plan
GROUPS = ("bank", "vault", "rooms", "streets", "manholes", "sewer", "side")


def _wall(c, r, u, color, seed, alpha=0.95):
    """One wall (a solid chalk band), struck on along its long side to u."""
    x0, y0, x1, y1 = r
    if u <= 0.0:
        return
    if x1 - x0 >= y1 - y0:
        x1 = lerp(x0, x1, clamp(u))
    else:
        y1 = lerp(y0, y1, clamp(u))
    bass.fill_polys(c, [bass.cut_rect(x0, y0, x1, y1, seed=seed, amp=0.5, seg=(18.0, 50.0))], color, alpha)


def _arc(c, centre, r, a0, a1, u=1.0, width=2.0, color=K.PAPER, seed=0, alpha=0.7):
    n = 16
    pts = [(centre[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
            centre[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    K.chalk_line(c, pts, u, width, color, seed, alpha)


def manhole(c, p, r=20.0, u=1.0, color=K.PAPER, seed=0, alpha=0.9):
    K.chalk_circle(c, p, r, u, 4.0, color, seed, alpha)
    if u >= 1.0:
        K.chalk_line(c, [(p[0] - r * 0.6, p[1] - r * 0.25), (p[0] + r * 0.6, p[1] - r * 0.25)], 1.0, 2.0, color, seed + 1, 0.6)
        K.chalk_line(c, [(p[0] - r * 0.6, p[1] + r * 0.25), (p[0] + r * 0.6, p[1] + r * 0.25)], 1.0, 2.0, color, seed + 2, 0.6)


def vault_door(c, open_u=0.0, color=K.PAPER, seed=0, alpha=0.95):
    """The round door in plan: a thick slab across the gap that swings out on its east hinge,
    with its swing arc."""
    hinge = (DOOR_GAP[1], VAULT_DOOR[1] + 4.0)
    L = DOOR_GAP[1] - DOOR_GAP[0]
    a = math.radians(180.0 - 90.0 * clamp(open_u))
    end = (hinge[0] + L * math.cos(a), hinge[1] + L * math.sin(a))
    bass.line_band(c, [hinge, end], color, width=16.0, seed=seed, alpha=alpha)
    _arc(c, hinge, L, 180.0, 90.0, 1.0, 2.0, color, seed + 1, 0.45)


BOXES = (652.0, 470.0, 690.0, 662.0)    # the deposit boxes: 2 columns x 6 rows on the vault's east wall


def box_rect(col, row):
    x0, y0, x1, y1 = BOXES
    w, h = (x1 - x0) / 2.0, (y1 - y0) / 6.0
    return (x0 + w * col, y0 + h * row, x0 + w * (col + 1), y0 + h * (row + 1))


def deposit_boxes(c, color=K.PAPER, seed=0, alpha=0.7):
    x0, y0, x1, y1 = BOXES
    K.chalk_rect(c, BOXES, 1.0, 2.5, color, seed, alpha)
    K.chalk_line(c, [((x0 + x1) / 2.0, y0), ((x0 + x1) / 2.0, y1)], 1.0, 2.0, color, seed + 1, alpha)
    for r in range(1, 6):
        y = y0 + (y1 - y0) * r / 6.0
        K.chalk_line(c, [(x0, y), (x1, y)], 1.0, 2.0, color, seed + 2 + r, alpha)


def draw_plan(c, u=None, door=0.0, bell=False, color=K.PAPER, seed=0, sewer_edge=K.BLUE):
    """The bank, streets and sewer in chalk (plan px). u: {group: progress 0..1} to draw groups
    on (the title); missing groups are fully drawn. door: the vault door's swing (0 shut)."""
    g = {name: 1.0 for name in GROUPS}
    if u is not None:
        g.update(u)
    # streets
    if g["streets"] > 0.0:
        for y in BACK_ST + FRONT_ST:
            K.chalk_line(c, [(SHEET[0] + 30.0, y), (SHEET[2] - 30.0, y)], g["streets"], 3.0, color, seed + 10, 0.75)
        K.chalk_line(c, [(ALLEY_X[1], BACK_ST[1]), (ALLEY_X[1], FRONT_ST[0])], g["streets"], 3.0, color, seed + 11, 0.6)
        for i in range(3):                                # the front steps
            y = BANK[3] + 10.0 + 12.0 * i
            K.chalk_line(c, [(704.0 - 6.0 * i, y), (786.0 + 6.0 * i, y)], g["streets"], 2.0, color, seed + 12 + i, 0.6)
    # walls
    for key, kind in (("bank", "ext"), ("vault", "vault"), ("rooms", "int")):
        if g[key] <= 0.0:
            continue
        rects = [r for r, kd in WALLS if kd == kind]
        n = len(rects)
        for i, r in enumerate(rects):
            _wall(c, r, clamp(g[key] * n - i * 0.6), color, seed + 30 + i)
    # the sewer: dashed (underground) and drawn over the walls it passes under, each dash edged
    # in the paper's blue so it shows across a wall; the branch runs right under the vault
    if g["sewer"] > 0.0:
        for pts, sd in ((SEWER_MAIN, 20), (SEWER_BRANCH, 21)):
            K.dashes(c, pts, sewer_edge, 10.0, 22.0, 14.0, g["sewer"], seed + sd, 1.0)
            K.dashes(c, pts, color, 4.0, 22.0, 14.0, g["sewer"], seed + sd, 0.8)
    if g["vault"] >= 1.0:
        vault_door(c, door, color, seed + 50)
        deposit_boxes(c, color, seed + 60)
        for i in range(3):                                # gold: three stacks of bars
            for j in range(3):
                bx, by = 400.0 + 27.0 * i, 478.0 + 19.0 * j
                bass.fill_polys(c, [bass.cut_rect(bx, by, bx + 22.0, by + 13.0, seed=seed + 80 + i * 3 + j, amp=0.3)],
                                color, 0.5)
    if g["rooms"] >= 1.0:
        _arc(c, (STORE_DOOR[0], 1170.0), 40.0, 270.0, 180.0, 1.0, 2.0, color, seed + 90)   # the store room door
        hs = 18.0
        K.chalk_rect(c, (HATCH[0] - hs, HATCH[1] - hs, HATCH[0] + hs, HATCH[1] + hs), 1.0, 3.0, color, seed + 91, 0.85)
        K.chalk_line(c, [(HATCH[0] - hs, HATCH[1] - hs), (HATCH[0] + hs, HATCH[1] + hs)], 1.0, 2.0, color, seed + 92, 0.6)
    if g["manholes"] > 0.0:
        manhole(c, MANHOLE_A, 20.0, g["manholes"], color, seed + 100)
        manhole(c, MANHOLE_B, 20.0, g["manholes"], color, seed + 101)
    if g["side"] > 0.0:
        _arc(c, (SIDE_DOOR[0], 1120.0), 40.0, 270.0, 360.0, g["side"], 2.0, color, seed + 110)
        for hinge, a0, a1 in (((700.0, BANK[3]), 0.0, -90.0), ((790.0, BANK[3]), 180.0, 270.0)):   # the front doors
            _arc(c, hinge, 45.0, a0, a1, g["side"], 2.0, color, seed + 111)
    if bell:
        K.bell(c, BELL_AT, 1.0, color, seed + 120)


def draw_walls_3d(c, cam, h=1.0, face=K.NAVY, side=K.STEEL, top=K.PAPER, edge=K.PAPER, ew=2.5, alpha=1.0,
                  kinds=("ext", "vault", "int")):
    """The plan's walls extruded to h x their height and seen through cam (frame px): the
    blueprint rising into the building. Back to front; each wall shows its top, its face toward
    the camera and the end the camera can see, edged in chalk."""
    if h <= 0.0:
        return
    a = math.radians(cam.yaw)
    boxes = [(r, kd) for r, kd in WALLS if kd in kinds]
    boxes.sort(key=lambda b: cam.depth(((b[0][0] + b[0][2]) / 2.0, (b[0][1] + b[0][3]) / 2.0)))
    for (x0, y0, x1, y1), kd in boxes:
        z = WALL_H[kd] * h
        V = cam.to_view
        faces = []
        if math.cos(a) > 0:                     # the south face
            faces.append(([V((x0, y1)), V((x1, y1)), V((x1, y1), z), V((x0, y1), z)], face))
        if math.sin(a) > 1e-3:                  # the east end
            faces.append(([V((x1, y1)), V((x1, y0)), V((x1, y0), z), V((x1, y1), z)], side))
        elif math.sin(a) < -1e-3:               # the west end
            faces.append(([V((x0, y0)), V((x0, y1)), V((x0, y1), z), V((x0, y0), z)], side))
        faces.append(([V((x0, y0), z), V((x1, y0), z), V((x1, y1), z), V((x0, y1), z)], top))
        for pts, col in faces:
            pts = bass.orient(pts, True)
            if edge is not None:
                _edged(c, pts, col, edge, ew, alpha)
            else:
                bass.fill_polys(c, [pts], col, alpha)


def _edged(c, pts, color, edge, width, alpha=1.0):
    c.save()
    c.new_path()
    draw.poly(c, pts)
    c.set_source_rgba(*edge, alpha)
    c.set_line_width(width)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.stroke()
    c.restore()
    bass.fill_polys(c, [pts], color, alpha)


# ============================================================================ on the plan
def piece_on(c, cam, kind, p, h=100.0, color=K.PAPER, edge=K.INK, facing=1, tilt=0.0, lift=0.0, shadow=0.38,
             seed=0, ew=5.0, light=None):
    """A chess piece standing on the plan at plan point p, seen through cam: its shadow on the
    paper (cast away from `light`, a plan point: the lamp), then the piece upright (h plan px
    tall, drawn cam.stand() of that). lift raises it off the paper (a hand carrying it in)."""
    light = LAMP_AT if light is None else light
    if shadow > 0.0:
        dx, dy = p[0] - light[0], p[1] - light[1]
        d = math.hypot(dx, dy) or 1.0
        ux, uy = dx / d, dy / d
        off = 0.16 * h + 0.3 * lift
        sc = (p[0] + ux * off, p[1] + uy * off)
        with cam.ground(c):
            bass.fill_polys(c, [draw.ellipse_pts(sc, 0.42 * h + 0.2 * lift, 0.27 * h, n=40,
                                                 angle=math.degrees(math.atan2(uy, ux)))], K.INK,
                            shadow * clamp(1.0 - lift / 260.0))
    v = cam.to_view(p)
    st = cam.stand()
    top = (v[0], v[1] - lift * cam.zoom * st)
    if st < 0.12:                                       # straight down: the piece's crown in plan
        K.piece_disc(c, top, 0.33 * h * cam.zoom, color, edge, 1.0, seed)
        return
    K.piece(c, kind, top, h * cam.zoom * st, color, edge, facing=facing, tilt=tilt, seed=seed, ew=ew)


def sheet_shadow(c, alpha=0.55, off=(10.0, 16.0)):
    """The sheet's shadow on the table (plan px, inside cam.ground)."""
    x0, y0, x1, y1 = SHEET
    bass.fill_polys(c, [bass.cut_rect(x0 + off[0], y0 + off[1], x1 + off[0], y1 + off[1], seed=5, amp=1.0)], K.INK, alpha)


# ============================================================================ Plan A, as drawn
# Where the pieces stand when the plan is finished (s03's end, s04's first frame)
PIECES_A = [("pawn", GUARD_POST, K.INK, K.PAPER, 1), ("queen", (512.0, 590.0), K.PAPER, K.INK, 1),
            ("bishop", (590.0, 614.0), K.GOLD, K.INK, -1), ("knight", (836.0, 1410.0), K.RED, K.INK, 1)]
LAMP_AT = (560.0, 820.0)                    # the table lamp's pool on the plan (plan px)


def lamp(c, a=1.0, centre=LAMP_AT, r=760.0):
    """The table lamp's gold pool on the paper (plan px, inside cam.ground)."""
    if a > 0.0:
        K.pool(c, centre, r, r, K.GOLD, 0.16 * a, steps=3)


CHEVRON_AT = MANHOLE_A                       # step 1's mark: down here
DIAL_AT = (540.0, 728.0)                     # step 4's mark: the dial at the vault door
RING_R = 46.0                                # the timing ring round the guard's pawn
CONE_BAND = (186.0, 860.0, 894.0, 940.0)     # the corridor his light sweeps (between its walls)
PLAN_A_PARTS = ("in", "out", "n1", "n2", "n3", "n4", "n5", "chevron", "cone", "ring", "dial", "car", "bell", "dot")


def draw_plan_a(c, a=1.0, cone_ang=0.0, prog=None, door=0.0):
    """Plan A as she leaves it (plan px, inside cam.ground): the bank, both routes, the steps
    (1)-(5), the X, the guard's cone and its timing ring, the dial at the vault door, the chalk
    car, the bell on the side door and the dot. prog: {part: 0..1} draws parts on (s03; the
    parts are P.PLAN_A_PARTS); missing parts are fully drawn. door: the vault door's swing."""
    g = dict.fromkeys(PLAN_A_PARTS, 1.0)
    if prog:
        g.update(prog)
    draw_plan(c, door=door)
    if g["chevron"] > 0.0:
        K.chevron(c, CHEVRON_AT, 22.0 * ease("outback", g["chevron"]), (0.0, 1.0), K.PAPER, width=4.0, seed=131,
                  alpha=a)
    K.route(c, ROUTE_IN, g["in"], K.PAPER, seed=3, alpha=a)
    K.route(c, ROUTE_OUT[6:], g["out"], K.PAPER, seed=4, alpha=a)
    for i, (txt, p) in enumerate(STEPS):
        K.circled(c, txt, p, 26.0, g["n%d" % (i + 1)], seed=10 + i, alpha=a)
    K.xmark(c, X_VAULT, 56.0, seed=20, alpha=a)
    if g["cone"] > 0.0:                          # the guard's light, kept inside the corridor's walls
        c.save()
        c.rectangle(CONE_BAND[0], CONE_BAND[1], CONE_BAND[2] - CONE_BAND[0], CONE_BAND[3] - CONE_BAND[1])
        c.clip()
        K.cone(c, (GUARD_POST[0] + 24.0, GUARD_POST[1]), cone_ang, 22.0 * ease("out3", g["cone"]),
               320.0 * ease("out3", g["cone"]), alpha=0.16 * a)
        c.restore()
    if g["ring"] > 0.0:
        K.chalk_circle(c, GUARD_POST, RING_R, g["ring"], 2.5, K.PAPER, seed=132, alpha=0.8 * a, start=-90.0)
        for i in range(4):
            if g["ring"] >= 0.25 * (i + 1):
                ang = math.radians(-90.0 + 90.0 * i)
                p0 = (GUARD_POST[0] + (RING_R - 7.0) * math.cos(ang), GUARD_POST[1] + (RING_R - 7.0) * math.sin(ang))
                p1 = (GUARD_POST[0] + (RING_R + 7.0) * math.cos(ang), GUARD_POST[1] + (RING_R + 7.0) * math.sin(ang))
                K.chalk_line(c, [p0, p1], 1.0, 3.0, K.PAPER, seed=133 + i, alpha=0.8 * a)
    if g["dial"] > 0.0:
        K.chalk_circle(c, DIAL_AT, 12.0, g["dial"], 2.5, K.PAPER, seed=137, alpha=0.9 * a)
        if g["dial"] >= 1.0:
            K.chalk_line(c, [DIAL_AT, (DIAL_AT[0] + 6.0, DIAL_AT[1] - 8.0)], 1.0, 2.5, K.PAPER, seed=138, alpha=0.9 * a)
    if g["car"] > 0.0:
        K.car(c, CAR, 180.0, 0.8 * ease("outback", g["car"]), K.INK, K.PAPER, alpha=a)
    if g["bell"] > 0.0:
        K.bell(c, BELL_AT, ease("outback", g["bell"]), K.PAPER, seed=120, alpha=a)
    if g["dot"] > 0.0:
        K.dot(c, DOT, 9.0 * ease("outback", g["dot"]), K.PAPER, alpha=a)


def draw_pieces(c, cam, pieces=PIECES_A, h=100.0):
    """Pieces [(kind, plan point, colour, edge, facing)], back to front."""
    for kind, p, col, edge, fc in sorted(pieces, key=lambda it: cam.depth(it[1])):
        piece_on(c, cam, kind, p, h, col, edge, facing=fc)


def table(c, cam, lamp_a=1.0, sheet=1.0, plan_a=0.0, on_plan=None):
    """The table shot: the sheet's shadow, the sheet, Plan A at strength plan_a (if > 0), then
    on_plan(c) (more chalk, in plan px), and the lamp's pool over it all. (The field under it is
    K.DEEP: the table in the dark.)"""
    with cam.ground(c):
        if cam.phi < 89.0:
            sheet_shadow(c)
        draw_sheet(c, sheet)
        if plan_a > 0.0:
            draw_plan_a(c, plan_a)
        if on_plan is not None:
            on_plan(c)
        lamp(c, lamp_a)


def along(route, s):
    """Point and direction at arc length s (plan px) along a route."""
    return K.poly_at(route, s)


def route_len(route):
    return K.poly_len(route)
