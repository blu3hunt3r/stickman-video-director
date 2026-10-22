"""SHADOW PLAY - the building across the street (the film's main set), her building, the
neighbouring blocks, the far skyline and the night sky.

THE FACADE is an old eight-storey brick tenement:
  * 40 windows, 5 columns x 8 rows, numbered row-major from the top-left (1..40):
        row 1:  1  2  3  4  5        window 4  = row 1, col 4 (dances alone)
        row 2:  6  7  8  9 10        window 9  = row 2, col 4 (the shadow play)
        row 3: 11 12 13 14 15        window 12 = row 3, col 2 (talks to her cat)
        ...                          window 30 = row 6, col 5 (cries on Sundays)
        row 8: 36 37 38 39 40
  * a Rear Window fire escape zig-zagging over columns 1-2 (a landing under every row),
    a bracketed cornice and parapet, a wooden water tank on stilts, chimneys, an antenna,
    drainpipes, a ground floor with a stoop entrance (lantern sconces, lit transom) and two
    shopfronts under an awning.

LOCAL UNITS: the design is FW x FH = 2261 x 3940 units (scale 1), y down from the parapet
top; the rooftop objects rise to about -540. One storey = 400 units = 3 m, so an adult seen
in a window is ~233 units tall (`Facade.person_h`). `Facade(origin, scale)` places the
bottom-centre of the facade (the sidewalk line under the entrance) at world `origin`.
At scale 1 the facade is 2.05 screen heights tall.

FACADE LOCK (bible): with `Facade.camera_lock()` the 40 windows sit exactly on the Bass grid
of s01 / s11: column centres x = 230 385 540 695 850, row centres y = 440 590 ... 1490,
windows 96 x 120 px (`LOCK_COLS`, `LOCK_ROWS`, `LOCK_SIZE`, `lock_rect(i)`).
"""
import math

import cairo

from engine import draw
from engine.core import W, H, clamp, lerp, hash01, fbm1

from .sets_base import (PAL, INK, AMBER, HOT, mix, mul, layer_spec, opened, view_box,
                        boxes_overlap, record, put, fill_path, local_matrix, rrect, level_of,
                        shadow_screen, rain_glints, glow, texture_surface, camera_for)

COLS, ROWS = 5, 8
#: the facade lock (bible, "World"): window centres on screen and window size in px
LOCK_COLS = (230.0, 385.0, 540.0, 695.0, 850.0)
LOCK_ROWS = (440.0, 590.0, 740.0, 890.0, 1040.0, 1190.0, 1340.0, 1490.0)
LOCK_SIZE = (96.0, 120.0)
LOCK_ZOOM = 0.375                 # screen px per local unit at the lock (x facade scale)
PX, PY = 155.0 / LOCK_ZOOM, 150.0 / LOCK_ZOOM     # column pitch 413.3, storey pitch 400
WW, WH = 96.0 / LOCK_ZOOM, 120.0 / LOCK_ZOOM      # window 256 x 320 (tall 2-over-2 sashes)
MX, MY = 176.0, 250.0             # left margin, top of row 1
FW = 2 * MX + (COLS - 1) * PX + WW   # facade width 2261.3
FH = 3940.0                       # parapet top (0) to sidewalk (FH)
_SX = FW / 1840.0                 # horizontal re-spacing of the hand-placed rooftop objects
PERSON = 233.0                    # adult height in local units (storey = 3 m)
FLOOR_BELOW_SILL = 48.0           # room floor is 0.36 m below the (low) sill

# --------------------------------------------------------------------------- window table
# Default dressing of the 40 windows (continuity: every scene sees the same building).
# curtain kinds: 'open', 'drapes', 'blind', 'shade', 'sheer', 'sheers_open', 'sheet', 'closed'
_CURTAINS = {
    1: ("blind", 0.5), 2: ("drapes", 0), 3: ("shade", 0.3), 4: ("sheers_open", 0), 5: ("blind", 0.8),
    6: ("sheer", 0), 7: ("blind", 0.4), 8: ("drapes", 0), 9: ("sheet", 0), 10: ("shade", 0.6),
    11: ("drapes", 0), 12: ("drapes", 0), 13: ("blind", 0.6), 14: ("open", 0), 15: ("shade", 0.5),
    16: ("blind", 0.3), 17: ("sheer", 0), 18: ("drapes", 0), 19: ("shade", 0.35), 20: ("blind", 0.7),
    21: ("shade", 0.8), 22: ("drapes", 0), 23: ("blind", 0.5), 24: ("sheer", 0), 25: ("drapes", 0),
    26: ("open", 0), 27: ("blind", 0.6), 28: ("shade", 0.4), 29: ("drapes", 0), 30: ("shade", 0.45),
    31: ("drapes", 0), 32: ("sheer", 0), 33: ("blind", 0.4), 34: ("closed", 0), 35: ("drapes", 0),
    36: ("blind", 0.5), 37: ("drapes", 0), 38: ("shade", 0.6), 39: ("blind", 0.3), 40: ("sheer", 0),
}
_FLOWER_BOXES = (5, 17, 23, 38)
_SASH_OPEN = {14: 0.24, 26: 0.2, 33: 0.15}
_DRESSING = {2: "pendant", 7: "lamp", 12: "lamp", 15: "pendant", 19: "frame", 23: "door",
             26: "pendant", 30: "lamp", 33: "frame", 37: "door", 14: "pendant", 1: "lamp",
             21: "frame", 28: "pendant", 35: "lamp", 40: "frame", 10: "door", 17: "pendant"}

#: Default night: the 9 lit windows of s01/s02 (window 9 is dark until Tuesday at eleven).
NIGHT = {2: 0.75, 4: 1.0, 7: 0.6, 12: 0.95, 19: 0.85, 23: 0.55, 26: 0.9, 30: 0.85, 37: 0.7}
#: Late night: only the regulars are up.
LATE = {4: 1.0, 12: 0.9, 30: 0.8, 19: 0.5}

#: Her building (variant 'hers'): her window, seen from window 9 in S08.
HER_WINDOW = 13
_CURTAINS_HERS = dict(_CURTAINS)
_CURTAINS_HERS.update({13: ("hers", 0), 9: ("blind", 0.5), 12: ("shade", 0.5), 14: ("drapes", 0)})


def rowcol(i):
    """Window number 1..40 -> (row, col), both 1-based."""
    return (i - 1) // COLS + 1, (i - 1) % COLS + 1


def index(row, col):
    """(row, col) 1-based -> window number."""
    return (row - 1) * COLS + col


def _win_local(i):
    r, c = rowcol(i)
    x0 = MX + (c - 1) * PX
    y0 = MY + (r - 1) * PY
    return x0, y0, x0 + WW, y0 + WH


def _curtain_spec(table, i, override=None):
    kind, drop = table.get(i, ("open", 0))
    spec = dict(kind=kind, drop=drop if drop else 0.55)
    if override is not None:
        if isinstance(override, str):
            spec = dict(kind=override, drop=spec["drop"] if override in ("blind", "shade") else 0.55)
        else:
            spec.update(override)
    return spec


# =========================================================================== static geometry
class _Design:
    """Recorded cairo paths of one facade variant, in local units."""

    def __init__(self, variant):
        self.variant = variant
        self.fire_cols = (1, 2) if variant == "across" else (4, 5)
        self.curtains = _CURTAINS if variant == "across" else _CURTAINS_HERS
        self.openings = [_win_local(i) for i in range(1, 41)]
        # ground floor openings: (kind, rect)
        cx = FW / 2
        self.door = (cx - 94.0, 3560.0, cx + 94.0, 3862.0)
        self.transom = (cx - 94.0, 3488.0, cx + 94.0, 3546.0)
        self.shops = [(150.0, 3520.0, cx - 262.0, 3820.0), (cx + 262.0, 3520.0, FW - 150.0, 3820.0)]
        self.sconces = [(cx - 142.0, 3640.0), (cx + 142.0, 3640.0)]
        self.wall = record(self._wall)
        self.trim = record(self._trim)
        self.frames = record(self._frames)
        self.sills = record(self._sills)
        self.fire = record(self._fire_escape)
        self.pipes = record(self._pipes)
        self.roof = record(self._roof)
        self.ground = record(self._ground)
        self.glass_dark = record(self._glass_dark)

    # ----------------------------------------------------------------- wall with holes
    def _wall(self, c):
        # outline with corner quoins (toothed edge where the facade meets the sky)
        pts = [(0, 56)]
        y = 200.0
        k = 0
        right = []
        while y < 3410:
            d = 7.0 if k % 2 == 0 else 0.0
            pts += [(-d, y), (-d, y + 62)]
            right += [(FW + d, y), (FW + d, y + 62)]
            y += 62
            k += 1
        pts += [(0, FH), (FW, FH)] + right[::-1] + [(FW, 56)]
        draw.poly(c, pts)
        for (x0, y0, x1, y1) in self.openings:
            draw.rect(c, x0, y0, x1, y1)
        draw.rect(c, *self.door)
        draw.rect(c, *self.transom)
        for s in self.shops:
            draw.rect(c, *s)

    def _glass_dark(self, c):
        for (x0, y0, x1, y1) in self.openings:
            draw.rect(c, x0, y0, x1, y1)

    # ----------------------------------------------------------------- trim: parapet, cornice, bands
    def _trim(self, c):
        hers = self.variant == "hers"
        # parapet with coping
        draw.rect(c, -8, 0, FW + 8, 12)
        draw.rect(c, 0, 12, FW, 60)
        if not hers:
            # stepped crown moulding projecting past the facade
            draw.rect(c, -36, 56, FW + 36, 72)
            draw.rect(c, -28, 72, FW + 28, 90)
            draw.rect(c, -18, 90, FW + 18, 106)
            # consoles (brackets) with scrolled feet, dentils between them
            n = 23
            for k in range(n + 1):
                x = -10 + k * (FW + 20) / n
                draw.poly(c, [(x - 13, 104), (x + 13, 104), (x + 13, 150), (x + 8, 168),
                              (x - 2, 176), (x - 9, 170), (x - 13, 158)])
            x = 12.0
            while x < FW - 12:
                draw.rect(c, x, 104, x + 10, 118)
                x += 20.0
            # frieze band under the consoles
            draw.rect(c, -6, 182, FW + 6, 196)
        else:
            # her building: plainer cornice with a shallow pediment over the centre
            draw.rect(c, -24, 56, FW + 24, 80)
            draw.rect(c, -14, 80, FW + 14, 96)
            draw.poly(c, [(FW / 2 - 300, 0), (FW / 2, -90), (FW / 2 + 300, 0)])
            x = 0.0
            while x <= FW:
                draw.rect(c, x - 8, 96, x + 8, 126)
                x += FW / 12.0
        # belt course over the ground floor
        draw.rect(c, -12, 3408, FW + 12, 3446)
        draw.rect(c, -6, 3446, FW + 6, 3456)

    # ----------------------------------------------------------------- window sash frames
    def _frames(self, c):
        for i, (x0, y0, x1, y1) in enumerate(self.openings, start=1):
            cx = (x0 + x1) / 2
            ym = y0 + WH * 0.5
            up = _SASH_OPEN.get(i, 0.0) * WH
            draw.rect(c, x0, y0, x0 + 8, y1)                 # jambs
            draw.rect(c, x1 - 8, y0, x1, y1)
            draw.rect(c, x0, y0, x1, y0 + 9)                 # head
            draw.rect(c, x0, y1 - 11, x1, y1)                # bottom rail / stool
            draw.rect(c, x0, ym - 6, x1, ym + 5)             # meeting rail (upper sash)
            draw.rect(c, cx - 3, y0, cx + 3, ym)             # upper muntin
            if up > 0:
                # raised lower sash: overlaps the upper one, open gap below it
                draw.rect(c, x0 + 3, ym - up - 6, x1 - 3, ym - up + 5)
                draw.rect(c, x0 + 3, y1 - up - 12, x1 - 3, y1 - up)
                draw.rect(c, cx - 3, ym - up, cx + 3, y1 - up)
            else:
                draw.rect(c, cx - 3, ym, cx + 3, y1)
        # ground floor: door, transom and shop window mullions
        x0, y0, x1, y1 = self.door
        cx = (x0 + x1) / 2
        draw.rect(c, x0, y0, x1, y0 + 12)
        draw.rect(c, cx - 5, y0, cx + 5, y1)
        for (a, b) in ((x0, cx - 5), (cx + 5, x1)):          # two leaves: glazed top, solid bottom
            draw.rect(c, a, y0 + 150, b, y1)
            draw.rect(c, a, y0, a + 12, y1)
            draw.rect(c, b - 12, y0, b, y1)
        tx0, ty0, tx1, ty1 = self.transom
        for k in range(1, 4):
            xx = tx0 + (tx1 - tx0) * k / 4
            draw.rect(c, xx - 3, ty0, xx + 3, ty1)
        for (sx0, sy0, sx1, sy1) in self.shops:
            for k in range(1, 3):
                xx = sx0 + (sx1 - sx0) * k / 3
                draw.rect(c, xx - 5, sy0, xx + 5, sy1)
            draw.rect(c, sx0, sy0 + 62, sx1, sy0 + 70)        # transom bar

    # ----------------------------------------------------------------- sills, lintels, flower boxes
    def _sills(self, c):
        # a continuous sill course under every row: the grid lines of s01 become ledges
        for r in range(ROWS):
            y1 = MY + r * PY + WH
            draw.rect(c, -6, y1 + 2, FW + 6, y1 + 11)
        for i, (x0, y0, x1, y1) in enumerate(self.openings, start=1):
            cx = (x0 + x1) / 2
            draw.rect(c, x0 - 14, y1, x1 + 14, y1 + 13)              # sill
            draw.rect(c, x0 - 10, y1 + 13, x1 + 10, y1 + 18)         # drip
            draw.rect(c, x0 - 12, y0 - 28, x1 + 12, y0)              # lintel
            draw.rect(c, x0 - 18, y0 - 36, x1 + 18, y0 - 28)         # cap
            draw.poly(c, [(cx - 16, y0 - 46), (cx + 16, y0 - 46), (cx + 11, y0 + 3), (cx - 11, y0 + 3)])
            if i in _FLOWER_BOXES and self.variant == "across":
                bx0, bx1 = x0 - 6, x1 + 6
                draw.poly(c, [(bx0, y1 - 30), (bx1, y1 - 30), (bx1 - 4, y1 + 2), (bx0 + 4, y1 + 2)])
                # stems and leaves poking above the box: the outline is the detail
                for k in range(9):
                    u = (k + 0.5) / 9
                    x = bx0 + 10 + (bx1 - bx0 - 20) * u
                    hgt = 26 + 30 * hash01(i, k, 3)
                    lean = (hash01(i, k, 4) - 0.5) * 18
                    draw.capsule(c, (x, y1 - 28), (x + lean, y1 - 28 - hgt), 3.2, 1.2)
                    draw.ellipse(c, (x + lean, y1 - 30 - hgt), 7 + 5 * hash01(i, k, 5), 4.5, angle=lean * 2)

    # ----------------------------------------------------------------- fire escape
    def fire_extent(self):
        ca, cb = self.fire_cols
        xa = MX + (ca - 1) * PX - 62
        xb = MX + (cb - 1) * PX + WW + 62
        return xa, xb

    def landing_y(self, row):
        return MY + (row - 1) * PY + WH + 18

    def _fire_escape(self, c):
        xa, xb = self.fire_extent()
        for r in range(1, ROWS + 1):
            yp = self.landing_y(r)
            draw.rect(c, xa, yp, xb, yp + 9)                          # grated platform
            draw.rect(c, xa, yp - 104, xb, yp - 98)                   # top rail
            draw.rect(c, xa, yp - 30, xb, yp - 27)                    # low rail
            x = xa + 4
            while x < xb - 4:
                draw.rect(c, x, yp - 100, x + 3.2, yp)                 # balusters
                x += 19.0
            for xx in (xa, xb - 7):
                draw.rect(c, xx, yp - 112, xx + 7, yp + 9)             # end posts
                draw.circle(c, (xx + 3.5, yp - 114), 5.5)              # post knobs
            for xx in (xa + 26, (xa + xb) / 2, xb - 30):
                draw.poly(c, [(xx - 3, yp + 9), (xx + 3, yp + 9), (xx + 2, yp + 74), (xx - 2, yp + 74)])
            # stair down to the next landing (zig-zag)
            if r < ROWS:
                run = (xb - xa) * 0.47
                if r % 2 == 1:
                    xs, xe = xa + 84, xa + 84 + run
                else:
                    xs, xe = xb - 84, xb - 84 - run
                self._stair(c, xs, yp, xe, yp + PY)
        # drop ladder under the lowest landing (retracted)
        y8 = self.landing_y(ROWS)
        lx = xb - 150 if self.fire_cols[0] == 1 else xa + 110
        draw.rect(c, lx, y8 + 9, lx + 5, y8 + 300)
        draw.rect(c, lx + 44, y8 + 9, lx + 49, y8 + 300)
        y = y8 + 34
        while y < y8 + 296:
            draw.rect(c, lx, y, lx + 49, y + 4)
            y += 30
        # gooseneck ladder over the parapet from the top landing
        y1 = self.landing_y(1)
        gx = xb - 130 if self.fire_cols[0] == 1 else xa + 80
        for xx in (gx, gx + 46):
            draw.rect(c, xx, -40, xx + 5, y1)
            c.new_sub_path()
            c.arc(xx + 30, -40, 27.5, math.pi, 1.5 * math.pi)
            c.arc_negative(xx + 30, -40, 22.5, 1.5 * math.pi, math.pi)
            c.close_path()
        y = -20.0
        while y < y1 - 10:
            draw.rect(c, gx, y, gx + 51, y + 4)
            y += 32

    @staticmethod
    def _stair(c, xs, ys, xe, ye):
        n = 11
        dx = (xe - xs) / n
        dy = (ye - ys) / n
        top = [(xs, ys)]
        for k in range(n):
            x = xs + k * dx
            y = ys + k * dy
            top += [(x + dx, y), (x + dx, y + dy)]
        th = 20.0
        bottom = [(xe, ye + th), (xs, ys + th)]
        draw.poly(c, top + bottom)
        # handrail with posts
        rh = 92.0
        draw.capsule(c, (xs, ys - rh), (xe, ye - rh), 3.0, 3.0)
        for u in (0.0, 0.5, 1.0):
            x = xs + (xe - xs) * u
            y = ys + (ye - ys) * u
            draw.rect(c, x - 2, y - rh, x + 2, y + 4)

    # ----------------------------------------------------------------- drainpipes
    def _pipes(self, c):
        for x in (22.0, FW - 22.0):
            draw.poly(c, [(x - 18, 180), (x + 18, 180), (x + 9, 222), (x - 9, 222)])   # leader head
            draw.rect(c, x - 7, 222, x + 7, FH - 40)
            draw.poly(c, [(x - 7, FH - 40), (x + 7, FH - 40), (x + 7, FH - 28), (x + 24, FH - 14),
                          (x + 24, FH - 4), (x - 7, FH - 4)])                         # shoe
            y = 330.0
            while y < FH - 80:
                draw.rect(c, x - 12, y, x + 12, y + 8)
                y += 290.0

    # ----------------------------------------------------------------- rooftop objects
    def _roof(self, c):
        state = {"open": False}

        def at(x_old):
            """Move the next rooftop group (hand-placed for an 1840-wide facade) so the
            groups keep their sizes but spread over the full width."""
            if state["open"]:
                c.restore()
            c.save()
            c.translate(x_old * (_SX - 1.0), 0)
            state["open"] = True

        if self.variant == "across":
            # wooden water tank on a steel stand
            at(1410.0)
            l0, l1 = 1290.0, 1530.0
            for lx in (l0, l1):
                draw.rect(c, lx - 6, -168, lx + 6, 40)
            draw.rect(c, 1406, -168, 1412, 40)                                  # rear leg
            for (a, b) in (((l0, -160), (l1, 0)), ((l1, -160), (l0, 0))):
                draw.capsule(c, a, b, 2.4, 2.4)                                  # cross bracing
            draw.rect(c, l0 - 6, -84, l1 + 6, -78)
            draw.rect(c, 1258, -178, 1562, -166)                                # platform beam
            body = [(1302, -178), (1518, -178)]
            hoops = [-205, -255, -305, -355, -398]
            right, left = [], []
            for hy in hoops:
                right += [(1518 + 0.06 * (hy + 178) * -0.1, hy + 6), (1522, hy + 3), (1522, hy - 3),
                          (1518, hy - 6)]
                left += [(1302, hy - 6), (1298, hy - 3), (1298, hy + 3), (1302, hy + 6)]
            draw.poly(c, body + right + [(1514, -420), (1306, -420)] + left[::-1])
            draw.poly(c, [(1288, -418), (1532, -418), (1468, -456), (1412, -496), (1352, -456)])
            draw.rect(c, 1409, -526, 1415, -490)
            draw.circle(c, (1412, -530), 7)
            # tank ladder
            for xx in (1270.0, 1284.0):
                draw.rect(c, xx, -440, xx + 3.5, -168)
            y = -430.0
            while y < -170:
                draw.rect(c, 1270, y, 1287, y + 3)
                y += 22
            # chimney stack with pots
            at(352.0)
            draw.rect(c, 300, -140, 404, 40)
            draw.rect(c, 294, -152, 410, -140)
            draw.rect(c, 316, -196, 342, -152)
            draw.rect(c, 312, -202, 346, -194)
            draw.rect(c, 362, -182, 386, -152)
            draw.rect(c, 358, -188, 390, -180)
            at(992.0)
            draw.rect(c, 960, -88, 1024, 40)
            draw.rect(c, 955, -98, 1029, -88)
            # stair bulkhead with a shed roof
            at(728.0)
            draw.poly(c, [(620, 40), (620, -150), (836, -128), (836, 40)])
            draw.rect(c, 612, -158, 844, -148)
            draw.rect(c, 760, -186, 772, -150)                                   # vent pipe
            draw.rect(c, 754, -192, 778, -184)
            # TV antenna
            at(1100.0)
            draw.rect(c, 1098, -330, 1102, 10)
            for (yy, half) in ((-318, 52), (-292, 40), (-266, 30), (-240, 22)):
                draw.rect(c, 1100 - half, yy, 1100 + half, yy + 2.5)
            draw.capsule(c, (1100, -200), (1150, 0), 1.4, 1.4)
            draw.capsule(c, (1100, -200), (1046, 0), 1.4, 1.4)
        else:
            for (x0, x1, top) in ((260.0, 352.0, -170.0), (1460.0, 1560.0, -150.0)):
                at((x0 + x1) / 2)
                draw.rect(c, x0, top, x1, 40)
                draw.rect(c, x0 - 6, top - 12, x1 + 6, top)
                draw.rect(c, x0 + 16, top - 50, x0 + 40, top - 12)
            at(1170.0)
            draw.poly(c, [(1060, 40), (1060, -170), (1280, -170), (1280, 40)])
            draw.poly(c, [(1050, -170), (1170, -230), (1290, -170)])
            at(702.0)
            draw.rect(c, 700, -260, 704, 10)
            for (yy, half) in ((-250, 46), (-228, 34), (-206, 24)):
                draw.rect(c, 702 - half, yy, 702 + half, yy + 2.5)
            # rooftop clothesline poles
            at(660.0)
            for x in (420.0, 900.0):
                draw.rect(c, x - 3, -120, x + 3, 30)
                draw.rect(c, x - 26, -124, x + 26, -118)
            c.new_sub_path()
            c.move_to(400, -120)
            c.curve_to(560, -96, 760, -96, 920, -120)
            c.line_to(920, -117)
            c.curve_to(760, -93, 560, -93, 400, -117)
            c.close_path()
        if state["open"]:
            c.restore()

    # ----------------------------------------------------------------- ground floor
    def _ground(self, c):
        x0, y0, x1, y1 = self.door
        cx = (x0 + x1) / 2
        # door surround with a hood on brackets
        draw.rect(c, x0 - 34, y0 - 96, x0 - 10, FH - 78)
        draw.rect(c, x1 + 10, y0 - 96, x1 + 34, FH - 78)
        draw.poly(c, [(x0 - 58, y0 - 112), (x1 + 58, y0 - 112), (x1 + 44, y0 - 96), (x0 - 44, y0 - 96)])
        draw.rect(c, x0 - 66, y0 - 128, x1 + 66, y0 - 112)
        # stoop: steps widening toward the street, newel posts with ball caps
        steps = [(FH - 78, 120), (FH - 52, 138), (FH - 26, 156)]
        for (yy, half) in steps:
            draw.rect(c, cx - half, yy, cx + half, yy + 27)
        for s in (-1, 1):
            nx = cx + s * 180
            draw.rect(c, nx - 9, FH - 150, nx + 9, FH)
            draw.circle(c, (nx, FH - 162), 13)
            # sloping handrail from the newel up to the door surround
            draw.capsule(c, (nx, FH - 150), (cx + s * 120, y1 - 120), 3.5, 3.5)
            for k in range(1, 5):
                u = k / 5
                bx = lerp(nx, cx + s * 120, u)
                by = lerp(FH - 150, y1 - 120, u)
                draw.rect(c, bx - 1.6, by, bx + 1.6, FH - 78 + (y1 - 120 - (FH - 150)) * 0 + 0)
        # lantern sconces
        for (sx, sy) in self.sconces:
            draw.rect(c, sx - 3, sy - 52, sx + 3, sy - 30)
            draw.poly(c, [(sx - 16, sy - 30), (sx + 16, sy - 30), (sx + 10, sy - 40), (sx - 10, sy - 40)])
            draw.rect(c, sx - 14, sy + 14, sx + 14, sy + 20)
            draw.poly(c, [(sx - 8, sy + 20), (sx + 8, sy + 20), (sx, sy + 32)])
        # shopfront bulkheads, pilasters, awning with a scalloped valance
        for (sx0, sy0, sx1, sy1) in self.shops:
            draw.rect(c, sx0 - 16, sy1, sx1 + 16, sy1 + 16)
            draw.rect(c, sx0 - 22, sy0 - 20, sx0, FH)
            draw.rect(c, sx1, sy0 - 20, sx1 + 22, FH)
        ax0, ax1 = self.shops[0][0] - 20.0, self.shops[0][2] + 20.0
        if self.variant == "across":
            pts = [(ax0 - 6, 3458), (ax1 + 6, 3458), (ax1 + 22, 3536)]
            n = 9
            for k in range(n):
                xa = ax1 + 22 - (ax1 + 22 - (ax0 - 22)) * k / n
                xb = ax1 + 22 - (ax1 + 22 - (ax0 - 22)) * (k + 1) / n
                xm = (xa + xb) / 2
                pts += [(xa, 3536), (xm, 3556), (xb, 3536)]
            pts += [(ax0 - 22, 3536)]
            draw.poly(c, pts)
        # areaway railing along the sidewalk on the right
        y = FH - 96
        rx0, rx1 = self.shops[1][0] - 10.0, self.shops[1][2] + 12.0
        draw.rect(c, rx0, y, rx1, y + 5)
        x = rx0 + 4.0
        while x < rx1:
            draw.rect(c, x, y, x + 3.5, FH)
            draw.poly(c, [(x - 2, y), (x + 5.5, y), (x + 1.75, y - 12)])
            x += 22
        # trash cans by the stoop
        for (tx, s) in ((cx - 260, 1.0), (cx - 318, 0.92)):
            draw.poly(c, [(tx - 26 * s, FH), (tx + 26 * s, FH), (tx + 30 * s, FH - 92 * s), (tx - 30 * s, FH - 92 * s)])
            draw.poly(c, [(tx - 34 * s, FH - 92 * s), (tx + 34 * s, FH - 92 * s), (tx + 24 * s, FH - 104 * s),
                          (tx - 24 * s, FH - 104 * s)])
            draw.rect(c, tx - 7 * s, FH - 112 * s, tx + 7 * s, FH - 104 * s)


_DESIGNS = {}


def _design(variant):
    if variant not in _DESIGNS:
        _DESIGNS[variant] = _Design(variant)
    return _DESIGNS[variant]


# =========================================================================== window info
class WindowInfo:
    """What an interior callback gets: fn(ctx, win). Draw in WORLD coords on ctx (already
    clipped to the opening). Silhouettes in ink read as people in a lit room; behind a
    shade / sheet / sheer the same drawing becomes a soft shadow automatically.

    i, row, col      window number and grid position (1-based)
    rect             (x0, y0, x1, y1) world rect of the glass opening
    cx, cy, w, h     centre and size (world)
    sill_y           world y of the sill (bottom of the opening)
    floor_y          world y of the room floor seen through it (feet stand here)
    person_h         world height of an adult in this window (~0.87 x window height)
    level            light level 0..1(+) ;  t, f, par: time, Frame, layer parallax
    mode             'direct' (sharp silhouettes) or 'shadow' (drawing into a shadow mask:
                     skip emissive extras there)
    curtain          the resolved curtain spec dict
    """

    __slots__ = ("i", "row", "col", "rect", "cx", "cy", "w", "h", "sill_y", "floor_y", "person_h",
                 "level", "t", "f", "par", "mode", "curtain", "facade")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))


# =========================================================================== the facade
class Facade:
    """The tenement across the street (variant 'across') or her building ('hers').

    Facade(origin=(540, 3940), scale=1.0, variant='across')
        origin: world point of the bottom-centre of the facade (sidewalk line at the stoop).
        scale:  1.0 -> 2261 x 3940 world px (2.05 screen heights); 0.25 fits the whole
                building inside her window in the POV shots.
    camera_lock() puts the 40 windows exactly on the bible's facade lock.
    """

    def __init__(self, origin=(540.0, 3940.0), scale=1.0, variant="across", seed=0):
        self.origin = (float(origin[0]), float(origin[1]))
        self.scale = float(scale)
        self.variant = variant
        self.seed = seed
        self.d = _design(variant)
        self.M = local_matrix(self.origin, self.scale, anchor=(FW / 2, FH))

    # ------------------------------------------------------------------ coordinates
    def to_world(self, p):
        s = self.scale
        return (self.origin[0] + (p[0] - FW / 2) * s, self.origin[1] + (p[1] - FH) * s)

    def to_local(self, p):
        s = self.scale
        return ((p[0] - self.origin[0]) / s + FW / 2, (p[1] - self.origin[1]) / s + FH)

    def _rect_world(self, r):
        a = self.to_world((r[0], r[1]))
        b = self.to_world((r[2], r[3]))
        return (a[0], a[1], b[0], b[1])

    @property
    def x0(self):
        return self.to_world((0, 0))[0]

    @property
    def x1(self):
        return self.to_world((FW, 0))[0]

    @property
    def top_y(self):
        """World y of the parapet top (the rooftop objects rise ~520 x scale above it)."""
        return self.to_world((0, 0))[1]

    @property
    def roof_y(self):
        """World y of the highest point (water tank finial)."""
        return self.to_world((0, -540))[1]

    @property
    def ground_y(self):
        return self.origin[1]

    @property
    def width(self):
        return FW * self.scale

    @property
    def height(self):
        return FH * self.scale

    @property
    def person_h(self):
        """Height of an adult inside a window / on the fire escape, world px."""
        return PERSON * self.scale

    @staticmethod
    def rowcol(i):
        return rowcol(i)

    @staticmethod
    def index(row, col):
        return index(row, col)

    def window_rect(self, i):
        """World rect (x0, y0, x1, y1) of window i's glass opening."""
        return self._rect_world(_win_local(i))

    def window_center(self, i):
        x0, y0, x1, y1 = self.window_rect(i)
        return ((x0 + x1) / 2, (y0 + y1) / 2)

    def sill_point(self, i):
        """World point at the middle of window i's sill top (where a cat sits)."""
        x0, y0, x1, y1 = _win_local(i)
        return self.to_world(((x0 + x1) / 2, y1))

    def floor_y(self, i):
        """World y of the room floor behind window i (for people standing inside)."""
        return self.to_world((0, _win_local(i)[3] + FLOOR_BELOW_SILL))[1]

    def landing(self, row):
        """Fire-escape landing in front of `row`: (x0, x1, y_platform_top) in world."""
        xa, xb = self.d.fire_extent()
        y = self.d.landing_y(row)
        a = self.to_world((xa, y))
        b = self.to_world((xb, y))
        return (a[0], b[0], a[1])

    def entrance(self):
        """World rect of the front door opening (the stoop leads up to its sill)."""
        return self._rect_world(self.d.door)

    def shop_rect(self, i):
        """World rect of shopfront i's glass (0 = left, 1 = right: the late diner)."""
        return self._rect_world(self.d.shops[i])

    def stoop_top(self):
        """World point at the top of the stoop, in front of the door."""
        x0, y0, x1, y1 = self.d.door
        return self.to_world(((x0 + x1) / 2, FH - 78))

    def sconces(self):
        return [self.to_world(p) for p in self.d.sconces]

    def curtain(self, i, override=None):
        """Resolved curtain spec of window i (defaults + override)."""
        return _curtain_spec(self.d.curtains, i, override)

    # ------------------------------------------------------------------ cameras
    def camera_full(self, par=1.0, margin=0.04, include_roof=True):
        """Camera framing the whole facade (and roof) for a layer with parallax `par`."""
        top = self.roof_y if include_roof else self.top_y
        h = (self.ground_y - top) * (1 + 2 * margin)
        z = H / h
        cx = (self.x0 + self.x1) / 2
        cy = (self.ground_y + top) / 2
        return camera_for((cx, cy), z, par)

    def camera_lock(self, par=1.0, dx=0.0, dy=0.0, zoom=1.0):
        """The facade-lock camera (s01 -> s02 handoff, s11 rhyme): window centres land on
        LOCK_COLS x LOCK_ROWS and every window is LOCK_SIZE px. dx, dy (screen px) and
        zoom (relative) offset it for drifts that start from the lock."""
        z = LOCK_ZOOM / self.scale * zoom
        cy = MY + 3 * PY + WH / 2 + (960.0 - LOCK_ROWS[3]) / LOCK_ZOOM
        p = self.to_world((FW / 2, cy))
        return camera_for((p[0] - dx / z, p[1] - dy / z), z, par)

    @staticmethod
    def lock_rect(i):
        """Screen rect (x0, y0, x1, y1) of window i at the facade lock."""
        r, c = rowcol(i)
        cx, cy = LOCK_COLS[c - 1], LOCK_ROWS[r - 1]
        return (cx - LOCK_SIZE[0] / 2, cy - LOCK_SIZE[1] / 2, cx + LOCK_SIZE[0] / 2, cy + LOCK_SIZE[1] / 2)

    def camera_on(self, i, fill=0.5, par=1.0, dx=0.0, dy=0.0, rot=0.0):
        """Camera centred on window i so that the window spans `fill` of the screen height."""
        x0, y0, x1, y1 = self.window_rect(i)
        z = fill * H / (y1 - y0)
        return camera_for(((x0 + x1) / 2 + dx, (y0 + y1) / 2 + dy), z, par, rot)

    # ------------------------------------------------------------------ light sources
    def light_sources(self, t=0.0, lit=None, entrance=1.0, shops=(0.0, 0.0)):
        """Lit rectangles for street reflections: [dict(rect, color, level)] in world."""
        lit = NIGHT if lit is None else lit
        out = []
        for r, lv in zip(self.d.shops, shops):
            if lv > 0.01:
                out.append(dict(rect=self._rect_world(r), color=AMBER, level=0.9 * lv))
        for i, v in lit.items():
            l = level_of(v, t)
            if l > 0.02:
                out.append(dict(rect=self.window_rect(i), color=AMBER, level=l))
        if entrance > 0:
            out.append(dict(rect=self._rect_world(self.d.transom), color=AMBER, level=0.8 * entrance))
            for (sx, sy) in self.d.sconces:
                out.append(dict(rect=self._rect_world((sx - 12, sy - 28, sx + 12, sy + 12)), color=HOT,
                                level=1.0 * entrance))
        return out

    # ------------------------------------------------------------------ drawing
    def draw(self, f, t, layer=None, lit=None, interiors=None, curtains=None, *, dressing=True,
             rain=1.0, halo=1.0, emit=1.0, entrance=1.0, shops=(0.0, 0.0), parts=None, wall_tone=1.0,
             texture=True, glints=True):
        """Draw the facade.

        layer      spec dict(par, blur, fog, alpha) (default: action plane). The facade opens
                   its own ink layer, then an additive light layer (halos, spill on the sills,
                   rain caught in the window light) and the emissive glow, in that order.
                   May also be a cairo.Context already opened by the caller: then only the
                   ink and the glow are drawn and the returned callable must be called AFTER
                   the caller's layer is closed to add the light pass.
        lit        {i: level or callable(t)} (default NIGHT). Use sets.switch() for flicker-ons.
        interiors  {i: fn(ctx, WindowInfo)} silhouettes inside lit windows.
        curtains   {i: kind | dict(kind=..., drop=..., soft=..., density=..., mag=...)}
                   overrides the default dressing. kinds: open, drapes, blind, shade, sheer,
                   sheers_open, sheet, closed (and 'hers' on her building). A 'sheet' may
                   also take ghost=0..1: how pale it reads while the window is dark.
        dressing   furniture silhouettes in lit windows without an interior callback.
        rain       brightness of rain glints in window light (0 = none).
        halo/emit  strength of the soft window halos / emissive bloom.
        entrance   lobby transom + lantern sconces level.
        shops      (left, right) shopfront light levels (default dark; a late diner if lit).
        parts      subset of {'windows', 'wall', 'details', 'fire_escape', 'roof', 'ground'}.
        Returns a callable that draws the light pass (already called when layer is a spec).
        """
        spec = None if isinstance(layer, cairo.Context) else layer_spec(layer)
        par = spec["par"] if spec else 1.0
        fog = spec["fog"] if spec else 0.0
        lit = NIGHT if lit is None else lit
        interiors = interiors or {}
        curtains = curtains or {}
        parts = set(parts) if parts is not None else {"windows", "wall", "details", "fire_escape", "roof", "ground"}
        vb = view_box(f, par, margin=40)
        levels = {}
        for i in range(1, 41):
            levels[i] = max(0.0, level_of(lit.get(i), t)) if i in lit else 0.0
        visible = [i for i in range(1, 41) if boxes_overlap(self.window_rect(i), vb)]

        with opened(f, layer) as L:
            if "windows" in parts:
                self._draw_windows(f, L, t, visible, levels, interiors, curtains, par, dressing)
            if "ground" in parts:
                self._draw_ground_glass(L, entrance, shops)
            if "wall" in parts:
                self._draw_wall(L, wall_tone, texture)
            if "details" in parts:
                fill_path(L, self.d.frames, INK, M=self.M)
                self._fill_stone(L, self.d.sills, wall_tone)
                self._fill_stone(L, self.d.trim, wall_tone, k=1.12)
                fill_path(L, self.d.pipes, INK, M=self.M)
            if "ground" in parts:
                fill_path(L, self.d.ground, INK, M=self.M)
            if "fire_escape" in parts:
                # wet iron: a hairline of sky caught on every top edge, then the ink
                off = 1.3 / max(f.lcam(par).zoom * f.scale, 1e-3) * f.scale
                L.save()
                L.translate(0, -off)
                fill_path(L, self.d.fire, mix(INK, PAL.fog_at(1.0), 0.95), 0.85, M=self.M)
                L.restore()
                fill_path(L, self.d.fire, INK, M=self.M)
            if "roof" in parts:
                fill_path(L, self.d.roof, INK, M=self.M)

        if emit > 0 and "windows" in parts:
            with f.emit(par=par) as G:
                k = emit * (1.0 - 0.8 * fog)
                for i in visible:
                    l = levels[i]
                    if l > 0.02:
                        x0, y0, x1, y1 = self.window_rect(i)
                        G.rectangle(x0, y0, x1 - x0, y1 - y0)
                        draw.fill(G, AMBER, 0.30 * min(l, 1.0) * k)
                if entrance > 0 and "ground" in parts:
                    for (sx, sy) in self.d.sconces:
                        p = self.to_world((sx, sy))
                        draw.circle(G, p, 15 * self.scale)
                        draw.fill(G, HOT, 0.9 * entrance * k)
                if "ground" in parts:
                    for r, lv in zip(self.d.shops, shops):
                        if lv > 0.01:
                            x0, y0, x1, y1 = self._rect_world(r)
                            G.rectangle(x0, y0, x1 - x0, y1 - y0)
                            draw.fill(G, AMBER, 0.22 * lv * k)

        def light_pass():
            if "windows" not in parts and "ground" not in parts:
                return
            k = 1.0 - 0.75 * fog
            blur = max(5.0, (spec["blur"] if spec else 0.0) + 3.0)
            with f.light(par=par, blur=blur) as A:
                if "windows" in parts:
                    self._draw_window_light(A, t, visible, levels, halo * k, rain * k, glints)
                if entrance > 0 and "ground" in parts:
                    self._draw_entrance_light(A, t, entrance * k)
                if "ground" in parts:
                    self._draw_shop_light(A, shops, k)

        if spec is not None:
            light_pass()
        return light_pass

    # ------------------------------------------------------------------ internals
    def _draw_wall(self, L, wall_tone, texture):
        top = mix(INK, PAL.fog_at(1.0), 0.40 * wall_tone)
        bot = mix(INK, PAL.fog_at(1.0), 0.17 * wall_tone)
        L.new_path()
        put(L, self.d.wall, self.M)
        L.save()
        L.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        L.transform(self.M)          # the path is already in device space; this only maps the gradient
        draw.linear(L, (0, 0), (0, FH), [(0, top, 1), (0.55, mix(top, bot, 0.6), 1), (1, bot, 1)])
        if texture:
            L.fill_preserve()
            L.clip()
            # rain-stained brick: soft vertical streaks, slightly lighter and darker patches
            tex = texture_surface("facade_wall", 230, 492, 9.0, 5 + self.seed, PAL.fog_at(0.6), 0.0, 0.10,
                                  streak=3.0)
            pat = cairo.SurfacePattern(tex)
            pat.set_filter(cairo.FILTER_BILINEAR)
            pat.set_extend(cairo.EXTEND_REPEAT)
            pat.set_matrix(cairo.Matrix(xx=230.0 / FW, yy=492.0 / FH))
            L.set_source(pat)
            L.paint()
            dark = texture_surface("facade_wall_dk", 160, 340, 6.0, 9 + self.seed, (0, 0, 0), 0.0, 0.22, streak=2.0)
            pat = cairo.SurfacePattern(dark)
            pat.set_filter(cairo.FILTER_BILINEAR)
            pat.set_extend(cairo.EXTEND_REPEAT)
            pat.set_matrix(cairo.Matrix(xx=160.0 / FW, yy=340.0 / FH))
            L.set_source(pat)
            L.paint()
        else:
            L.fill()
        L.restore()
        L.new_path()

    def _fill_stone(self, L, path, wall_tone, k=1.0):
        """Stone trim (sills, lintels, cornice): a shade lighter than the brick, wet and
        catching the sky, so the facade's rhythm reads without a single drawn line."""
        L.new_path()
        put(L, path, self.M)
        L.save()
        L.transform(self.M)
        draw.linear(L, (0, -100), (0, FH), [(0, mix(INK, PAL.fog_at(1.0), 0.62 * wall_tone * k), 1),
                                            (0.6, mix(INK, PAL.fog_at(1.0), 0.40 * wall_tone * k), 1),
                                            (1, mix(INK, PAL.fog_at(1.0), 0.28 * wall_tone * k), 1)])
        L.fill()
        L.restore()

    def _draw_ground_glass(self, L, entrance, shops=(0.0, 0.0)):
        d = self.d
        L.save()
        L.transform(self.M)
        # lobby: the door glass and transom glow when the lobby light is on
        for r in (d.door, d.transom):
            x0, y0, x1, y1 = r
            g = mix((0.03, 0.033, 0.045), mul(AMBER, 0.62), clamp(entrance))
            draw.linear(L, (0, y0), (0, y1), [(0, mix(g, mul(HOT, 0.8), 0.3 * entrance), 1), (1, g, 1)])
            L.rectangle(x0, y0, x1 - x0, y1 - y0)
            L.fill()
        # shop windows: dark glass reflecting the street, or a late diner's warm light
        for (x0, y0, x1, y1), lv in zip(d.shops, shops):
            dk = [(0, (0.05, 0.055, 0.075), 1), (0.6, (0.022, 0.025, 0.036), 1), (1, (0.04, 0.042, 0.055), 1)]
            if lv > 0.01:
                lk = clamp(lv)
                dk = [(0, mix(dk[0][1], HOT, lk), 1), (0.45, mix(dk[1][1], mul(AMBER, 0.8), lk), 1),
                      (1, mix(dk[2][1], mul(AMBER, 0.45), lk), 1)]
            draw.linear(L, (0, y0), (0, y1), dk)
            L.rectangle(x0, y0, x1 - x0, y1 - y0)
            L.fill()
            if lv > 0.01:
                # counter, stools and three pendant lamps: a diner after hours
                col = mix((0.03, 0.03, 0.04), mul(AMBER, 0.22), clamp(lv))
                w = x1 - x0
                draw.rect(L, x0, y0 + 190, x1, y1)
                draw.rect(L, x0, y0 + 178, x1, y0 + 192)
                for k in range(7):
                    sx = x0 + w * (k + 0.5) / 7
                    draw.rect(L, sx - 3, y0 + 236, sx + 3, y1)
                    draw.ellipse(L, (sx, y0 + 236), 20, 7)
                draw.fill(L, col)
                for k in range(3):
                    px = x0 + w * (k + 0.5) / 3
                    draw.rect(L, px - 1.5, y0, px + 1.5, y0 + 92)
                    draw.poly(L, [(px - 10, y0 + 92), (px + 10, y0 + 92), (px + 34, y0 + 118), (px - 34, y0 + 118)])
                    draw.fill(L, col)
                    draw.ellipse(L, (px, y0 + 120), 20, 6)
                    draw.fill(L, HOT, clamp(lv))
        L.restore()

    def _draw_shop_light(self, A, shops, k):
        s = self.scale
        for r, lv in zip(self.d.shops, shops):
            if lv <= 0.01:
                continue
            x0, y0, x1, y1 = self._rect_world(r)
            rrect(A, x0 - 8 * s, y0 - 8 * s, x1 + 8 * s, y1 + 8 * s, 12 * s)
            draw.fill(A, AMBER, 0.16 * lv * k)
            glow(A, ((x0 + x1) / 2, (y0 + y1) / 2), (x1 - x0) * 0.75, AMBER, 0.12 * lv * k)
            # spill on the wet sidewalk in front of the glass
            A.save()
            A.translate((x0 + x1) / 2, self.ground_y)
            A.scale(1.0, 0.16)
            glow(A, (0, 0), (x1 - x0) * 0.7, AMBER, 0.35 * lv * k)
            A.restore()

    def _draw_windows(self, f, L, t, visible, levels, interiors, curtains, par, dressing):
        d = self.d
        dark_top = (0.062, 0.070, 0.098)
        dark_bot = (0.020, 0.024, 0.037)
        # 1) all dark glass at once (a repeating vertical gradient = sky reflection in every pane)
        L.save()
        L.transform(self.M)
        g = draw.linear(L, (0, MY), (0, MY + PY), [(0, dark_top, 1), (WH / PY * 0.55, mix(dark_top, dark_bot, 0.7), 1),
                                                   (WH / PY, dark_bot, 1), (1, dark_bot, 1)])
        g.set_extend(cairo.EXTEND_REPEAT)
        for i in visible:
            if levels[i] <= 0.02:
                x0, y0, x1, y1 = _win_local(i)
                L.rectangle(x0, y0, x1 - x0, y1 - y0)
        L.fill()
        L.restore()
        # 2) lit windows: glowing room, dressing, interior, curtain
        for i in visible:
            l = levels[i]
            spec = _curtain_spec(d.curtains, i, curtains.get(i))
            if l > 0.02:
                self._lit_window(f, L, t, i, l, spec, interiors.get(i), par, dressing)
            else:
                self._dark_curtain(L, t, i, spec)

    def _lit_window(self, f, L, t, i, l, spec, interior, par, dressing):
        x0, y0, x1, y1 = _win_local(i)
        w, h = x1 - x0, y1 - y0
        lu = 0.28 + 0.44 * hash01(self.seed, i, 11)
        lv = 0.50 + 0.35 * hash01(self.seed, i, 12)
        lc = (x0 + w * lu, y0 + h * lv)
        lk = min(l, 1.0)
        dark = (0.03, 0.034, 0.05)
        c_hot = mix(dark, HOT, lk)
        c_mid = mix(dark, mul(AMBER, 0.86), lk)
        c_far = mix(dark, mul(AMBER, 0.46), lk)
        kind = spec["kind"]
        L.save()
        L.transform(self.M)
        L.rectangle(x0, y0, w, h)
        L.clip()
        draw.radial(L, lc, 0, h * 1.05, [(0, c_hot, 1), (0.32, c_mid, 1), (1, c_far, 1)])
        L.paint()
        if dressing and interior is None:
            self._dressing(L, i, x0, y0, x1, y1, lk, lc, kind)
        L.restore()

        # interior callback: direct for clear glass, as shadows behind translucent curtains
        if interior is not None:
            info = self._info(f, t, i, l, par, spec)
            covered = self._covered_rect(spec, x0, y0, x1, y1)      # local rect under a translucent curtain
            if kind in ("sheer",):
                covered = (x0, y0, x1, y1)
            # direct part
            direct = None
            if covered is None:
                direct = (x0, y0, x1, y1)
            elif covered[3] < y1 - 1:
                direct = (x0, covered[3], x1, y1)
            if direct is not None:
                info.mode = "direct"
                L.save()
                r = self._rect_world(direct)
                L.rectangle(r[0], r[1], r[2] - r[0], r[3] - r[1])
                L.clip()
                interior(L, info)
                L.restore()
            if covered is not None:
                self._curtain(L, t, i, spec, lk, lc, only_panel=True)
                info.mode = "shadow"
                soft = spec.get("soft", {"shade": 0.035, "sheet": 0.016, "sheer": 0.012}.get(kind, 0.02) * w) * self.scale
                dens = spec.get("density", {"shade": 0.80, "sheet": 0.9, "sheer": 0.62}.get(kind, 0.85))
                mag = spec.get("mag", 1.0)
                cw = self._rect_world(covered)
                lw = self.to_world(lc)
                region = self._curtain_region(t, i, spec)
                shadow_screen(L, lambda c, info=info: interior(c, info), region=region, bbox=cw,
                              soft=soft, density=dens, mag=mag, center=lw)
                self._curtain(L, t, i, spec, lk, lc, only_details=True)
                return
        self._curtain(L, t, i, spec, lk, lc)

    def _info(self, f, t, i, l, par, spec):
        r = self.window_rect(i)
        row, col = rowcol(i)
        return WindowInfo(i=i, row=row, col=col, rect=r, cx=(r[0] + r[2]) / 2, cy=(r[1] + r[3]) / 2,
                          w=r[2] - r[0], h=r[3] - r[1], sill_y=r[3], floor_y=self.floor_y(i),
                          person_h=self.person_h, level=l, t=t, f=f, par=par, mode="direct",
                          curtain=spec, facade=self)

    @staticmethod
    def _covered_rect(spec, x0, y0, x1, y1):
        kind = spec["kind"]
        if kind == "shade":
            return (x0, y0, x1, y0 + (y1 - y0) * clamp(spec.get("drop", 0.55)))
        if kind == "sheet":
            return (x0, y0, x1, y1)
        if kind == "sheer":
            return (x0, y0, x1, y1)
        return None

    def _curtain_region(self, t, i, spec):
        """Callable building the world path of the translucent panel of window i."""
        kind = spec["kind"]
        x0, y0, x1, y1 = _win_local(i)
        M = self.M

        def region(ctx):
            ctx.save()
            ctx.transform(M)
            if kind == "sheet":
                draw.poly(ctx, self._sheet_outline(t, i, x0, y0, x1, y1))
            elif kind == "shade":
                draw.rect(ctx, x0, y0, x1, y0 + (y1 - y0) * clamp(spec.get("drop", 0.55)))
            else:
                draw.rect(ctx, x0, y0, x1, y1)
            ctx.restore()
        return region

    def _sheet_outline(self, t, i, x0, y0, x1, y1):
        """Hanging sheet inside a window: pinned to a wire at 4 points, sagging between pins,
        hem swaying a little."""
        pins = 4
        top = []
        for k in range(pins):
            xa = lerp(x0 + 10, x1 - 10, k / (pins - 1))
            top.append((xa, y0 + 14))
            if k < pins - 1:
                xb = lerp(x0 + 10, x1 - 10, (k + 1) / (pins - 1))
                top.append(((xa + xb) / 2, y0 + 22))
        sw = 2.0 * fbm1(t * 0.5, 90 + i)
        hem = []
        n = 6
        for k in range(n + 1):
            u = k / n
            x = lerp(x1 - 8, x0 + 8, u) + sw * 1.5
            y = y1 - 16 + 3.5 * math.sin(u * 7.0 + t * 0.9 + i) + sw
            hem.append((x, y))
        return top + [(x1 - 6 + sw * 0.5, (y0 + y1) / 2)] + hem + [(x0 + 6 + sw * 0.5, (y0 + y1) / 2)]

    def _dressing(self, L, i, x0, y0, x1, y1, lk, lc, kind):
        """Back-of-room furniture silhouettes (dark amber, inside the glow)."""
        typ = _DRESSING.get(i)
        if not typ or kind in ("closed", "sheet"):
            return
        w, h = x1 - x0, y1 - y0
        col = mix((0.03, 0.03, 0.04), mul(AMBER, 0.30), lk)
        side = -1 if hash01(self.seed, i, 21) < 0.5 else 1
        if typ == "lamp":
            bx = x0 + w * (0.24 if side < 0 else 0.76)
            draw.rect(L, bx - 2, y0 + h * 0.48, bx + 2, y1)
            draw.poly(L, [(bx - 24, y0 + h * 0.50), (bx + 24, y0 + h * 0.50), (bx + 15, y0 + h * 0.34),
                          (bx - 15, y0 + h * 0.34)])
            draw.fill(L, col)
            draw.ellipse(L, (bx, y0 + h * 0.53), 26, 10)
            draw.fill(L, mix(col, HOT, 0.65 * lk))
        elif typ == "pendant":
            bx = x0 + w * (0.5 + 0.12 * side)
            draw.rect(L, bx - 1.2, y0, bx + 1.2, y0 + h * 0.22)
            draw.poly(L, [(bx - 9, y0 + h * 0.22), (bx + 9, y0 + h * 0.22), (bx + 26, y0 + h * 0.32),
                          (bx - 26, y0 + h * 0.32)])
            draw.fill(L, col)
            draw.ellipse(L, (bx, y0 + h * 0.335), 14, 5)
            draw.fill(L, HOT, 0.9 * lk)
        elif typ == "frame":
            fx = x0 + w * (0.30 if side < 0 else 0.62)
            draw.rect(L, fx, y0 + h * 0.20, fx + w * 0.22, y0 + h * 0.38)
            draw.fill(L, col)
        elif typ == "door":
            dx = x0 + w * (0.18 if side < 0 else 0.60)
            draw.rect(L, dx, y0 + h * 0.18, dx + w * 0.26, y1)
            draw.fill(L, mix(col, mul(AMBER, 0.55), 0.5))
            draw.rect(L, dx + w * 0.03, y0 + h * 0.22, dx + w * 0.23, y1)
            draw.fill(L, mix(mul(AMBER, 0.75), HOT, 0.3), lk)

    def _curtain(self, L, t, i, spec, lk, lc, only_panel=False, only_details=False):
        """Curtain of a LIT window (local units through self.M)."""
        kind = spec["kind"]
        if kind == "open":
            return
        x0, y0, x1, y1 = _win_local(i)
        w, h = x1 - x0, y1 - y0
        L.save()
        L.transform(self.M)
        L.rectangle(x0, y0, w, h)
        L.clip()
        dim = mix((0.02, 0.02, 0.03), mul(AMBER, 0.20), lk)
        if kind in ("drapes", "hers"):
            self._drapes(L, t, i, x0, y0, x1, y1, dim)
        elif kind == "sheers_open":
            for s in (-1, 1):
                xa = x0 if s < 0 else x1
                xi = x0 + w * 0.24 if s < 0 else x1 - w * 0.24
                xm = x0 + w * 0.13 if s < 0 else x1 - w * 0.13
                sw = 3.0 * fbm1(t * 0.6, i * 3 + s)
                draw.smooth(L, [(xa, y0), (xi + sw, y0), (xm + sw * 1.8, y0 + h * 0.5), (xi + sw * 2.5, y1),
                                (xa, y1)], close=True, tension=0.4)
                draw.fill(L, mix(mul(AMBER, 0.9), HOT, 0.4), 0.42 * lk)
        elif kind == "blind":
            drop = clamp(spec.get("drop", 0.5))
            yb = y0 + h * drop
            pitch = h / 26.0
            y = y0
            L.new_path()
            while y < yb - pitch * 0.4:
                draw.rect(L, x0, y, x1, y + pitch * 0.64)
                y += pitch
            draw.fill(L, mix(INK, mul(AMBER, 0.12), lk * 0.5), 0.95)
            draw.rect(L, x0 - 2, yb - pitch * 0.5, x1 + 2, yb + pitch * 0.9)
            draw.fill(L, INK)
            for cx in (x0 + w * 0.25, x0 + w * 0.75):
                draw.rect(L, cx - 0.8, y0, cx + 0.8, yb)
                draw.fill(L, INK, 0.7)
        elif kind == "shade":
            drop = clamp(spec.get("drop", 0.55))
            yb = y0 + h * drop
            if not only_details:
                draw.radial(L, (lc[0], min(lc[1], yb)), 0, h * 0.9,
                            [(0, mix(dim, mix(AMBER, HOT, 0.7), 0.95 * lk), 1),
                             (1, mix(dim, mul(AMBER, 0.62), 0.95 * lk), 1)])
                L.rectangle(x0, y0, w, yb - y0)
                L.fill()
            if not only_panel:
                draw.rect(L, x0, yb - 3, x1, yb + 4)
                draw.fill(L, INK)
                cx = x0 + w * 0.5
                L.new_path()
                draw.rect(L, cx - 0.9, yb + 4, cx + 0.9, yb + 16)
                L.new_sub_path()
                L.arc(cx, yb + 21, 5.5, 0, 2 * math.pi)
                L.new_sub_path()
                L.arc_negative(cx, yb + 21, 3.2, 2 * math.pi, 0)
                draw.fill(L, INK)
        elif kind == "sheer":
            if not only_details:
                draw.linear(L, (x0, 0), (x1, 0), [(k / 8, mix(AMBER, HOT, 0.35), 0.28 + 0.12 * ((k % 2) * 2 - 1))
                                                   for k in range(9)])
                L.rectangle(x0, y0, w, h)
                L.fill()
        elif kind == "sheet":
            if not only_details:
                pts = self._sheet_outline(t, i, x0, y0, x1, y1)
                draw.poly(L, pts)
                draw.radial(L, lc, 0, h * 0.95, [(0, mix(dim, HOT, lk), 1), (0.45, mix(dim, mix(AMBER, HOT, 0.3), lk), 1),
                                                 (1, mix(dim, mul(AMBER, 0.55), lk), 1)])
                L.fill()
            if not only_panel:
                for k in range(4):                      # clothes pins
                    xa = lerp(x0 + 10, x1 - 10, k / 3)
                    draw.rect(L, xa - 2.5, y0 + 6, xa + 2.5, y0 + 20)
                draw.rect(L, x0, y0 + 9, x1, y0 + 11.5)    # the wire
                draw.fill(L, INK)
        elif kind == "closed":
            draw.rect(L, x0 + 3, y0, x1 - 3, y1)
            draw.fill(L, INK)
        L.restore()

    def _drapes(self, L, t, i, x0, y0, x1, y1, col):
        w, h = x1 - x0, y1 - y0
        for s in (-1, 1):
            xa = x0 if s < 0 else x1
            xt = x0 + w * 0.30 if s < 0 else x1 - w * 0.30
            xk = x0 + w * 0.10 if s < 0 else x1 - w * 0.10
            xb = x0 + w * 0.22 if s < 0 else x1 - w * 0.22
            yk = y0 + h * 0.60
            pts = [(xa, y0), (xt, y0), (lerp(xt, xk, 0.6), y0 + h * 0.36), (xk, yk),
                   (lerp(xk, xb, 0.55), y0 + h * 0.8), (xb, y1), (xa, y1)]
            draw.smooth(L, pts, close=True, tension=0.35)
            draw.fill(L, col)
            # tie-back knot
            draw.ellipse(L, (xk - s * 3, yk), 5, 7)
            draw.fill(L, INK)
        # scalloped valance
        pts = [(x0, y0), (x1, y0), (x1, y0 + h * 0.08)]
        n = 4
        for k in range(n):
            xa = x1 - w * k / n
            xb = x1 - w * (k + 1) / n
            pts.append(((xa + xb) / 2, y0 + h * 0.13))
            pts.append((xb, y0 + h * 0.08))
        draw.poly(L, pts)
        draw.fill(L, INK)

    def _dark_curtain(self, L, t, i, spec):
        """Curtains of a dark window: barely there (dark on dark), a sheet is a pale ghost."""
        kind = spec["kind"]
        x0, y0, x1, y1 = _win_local(i)
        L.save()
        L.transform(self.M)
        L.rectangle(x0, y0, x1 - x0, y1 - y0)
        L.clip()
        if kind in ("drapes", "hers"):
            self._drapes(L, t, i, x0, y0, x1, y1, (0.014, 0.015, 0.022))
        elif kind == "blind":
            drop = clamp(spec.get("drop", 0.5))
            pitch = (y1 - y0) / 26.0
            y = y0
            while y < y0 + (y1 - y0) * drop:
                draw.rect(L, x0, y, x1, y + pitch * 0.64)
                y += pitch
            draw.fill(L, INK, 0.55)
        elif kind == "shade":
            drop = clamp(spec.get("drop", 0.55))
            draw.rect(L, x0, y0, x1, y0 + (y1 - y0) * drop)
            draw.fill(L, (0.045, 0.048, 0.062))
        elif kind == "sheet":
            # spec 'ghost' 0..1 (default 0): how pale the unlit sheet reads (street light on it)
            g = clamp(spec.get("ghost", 0.0))
            draw.poly(L, self._sheet_outline(t, i, x0, y0, x1, y1))
            draw.linear(L, (0, y0), (0, y1), [(0, mix((0.085, 0.09, 0.115), (0.30, 0.31, 0.345), g), 1),
                                              (1, mix((0.045, 0.05, 0.068), (0.16, 0.17, 0.20), g), 1)])
            L.fill()
        elif kind == "closed":
            draw.rect(L, x0 + 3, y0, x1 - 3, y1)
            draw.fill(L, INK)
        L.restore()

    def _draw_window_light(self, A, t, visible, levels, halo, rain, glints):
        s = self.scale
        for i in visible:
            l = levels[i]
            if l <= 0.02:
                continue
            lk = min(l, 1.2)
            x0, y0, x1, y1 = self.window_rect(i)
            w, h = x1 - x0, y1 - y0
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            if halo > 0:
                # light bleeding out of the opening into the wet air
                rrect(A, x0 - 7 * s, y0 - 7 * s, x1 + 7 * s, y1 + 7 * s, 10 * s)
                draw.fill(A, AMBER, 0.22 * lk * halo)
                glow(A, (cx, cy + h * 0.08), h * 1.05, AMBER, 0.11 * lk * halo)
                # the sill top catches the light
                A.rectangle(x0 - 14 * s, y1 - 1.5 * s, w + 28 * s, 5 * s)
                draw.fill(A, mix(AMBER, HOT, 0.5), 0.55 * lk * halo)
                # spill falling outward and down into the rain
                draw.linear(A, (0, y1), (0, y1 + h * 0.9), [(0, AMBER, 0.10 * lk * halo), (1, AMBER, 0.0)])
                draw.poly(A, [(x0, y1), (x1, y1), (x1 + w * 0.45, y1 + h * 0.9), (x0 - w * 0.45, y1 + h * 0.9)])
                A.fill()
            if rain > 0 and glints:
                rx, ry = w * 1.1, h * 1.0

                def wgt(x, y, cx=cx, cy=cy + h * 0.25, rx=rx, ry=ry):
                    d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                    return math.exp(-1.6 * d)
                rain_glints(A, t, (x0 - w * 0.6, y0 - h * 0.25, x1 + w * 0.6, y1 + h * 1.1),
                            color=mix(HOT, (1, 1, 1), 0.2), alpha=0.75 * lk * rain, density=1.3 / (s * s),
                            seed=1000 + i, speed=1250 * s, length=34 * s, width=max(0.8, 1.6 * s), wind=0.14,
                            weight=wgt)

    def _draw_entrance_light(self, A, t, k):
        s = self.scale
        for (sx, sy) in self.d.sconces:
            p = self.to_world((sx, sy))
            glow(A, p, 120 * s, AMBER, 0.32 * k)
            glow(A, p, 34 * s, HOT, 0.55 * k)
        x0, y0, x1, y1 = self._rect_world(self.d.door)
        glow(A, ((x0 + x1) / 2, y0), (x1 - x0) * 1.1, AMBER, 0.16 * k)
        # light pool on the stoop and sidewalk
        st = self.stoop_top()
        A.save()
        A.translate(st[0], self.ground_y)
        A.scale(1.0, 0.22)
        glow(A, (0, 0), 420 * s, AMBER, 0.22 * k)
        A.restore()


# =========================================================================== neighbours + skyline
class Block:
    """A plainer neighbouring tenement (or any far building): wall, window grid, a cornice,
    rooftop clutter. Cheap; meant for the sides of wide shots and for far layers.

    Block(x0, x1, top_y, ground_y, seed, scale=1.0, cols=None, lit_frac=0.18)
    All coordinates are WORLD (x0..x1 wide, top_y..ground_y tall)."""

    def __init__(self, x0, x1, top_y, ground_y, seed=0, scale=1.0, cols=None, lit_frac=0.18,
                 tone=0.0, water_tank=False):
        self.x0, self.x1, self.top, self.ground = float(x0), float(x1), float(top_y), float(ground_y)
        self.seed, self.s = seed, float(scale)
        s = self.s
        pitch_x = 280 * s
        pitch_y = 380 * s
        wcols = cols or max(1, int((self.x1 - self.x0 - 120 * s) / pitch_x))
        mx = (self.x1 - self.x0 - (wcols - 1) * pitch_x - 150 * s) / 2
        self.windows = []
        y = self.top + 230 * s
        r = 0
        while y + 240 * s < self.ground - 420 * s:
            for c in range(wcols):
                x = self.x0 + mx + c * pitch_x
                self.windows.append((x, y, x + 150 * s, y + 240 * s, r, c))
            y += pitch_y
            r += 1
        self.lit_frac = lit_frac
        self.tone = tone
        self.water_tank = water_tank

    def lit_windows(self, t=0.0):
        out = []
        for k, wnd in enumerate(self.windows):
            h = hash01(self.seed, k, 77)
            if h < self.lit_frac:
                out.append((wnd, 0.45 + 0.55 * hash01(self.seed, k, 78)))
        return out

    def light_sources(self, t=0.0):
        return [dict(rect=w[:4], color=AMBER, level=l) for (w, l) in self.lit_windows(t)]

    def draw(self, f, t, L, glow_k=1.0):
        s = self.s
        lit = {w[:4]: l for (w, l) in self.lit_windows(t)}
        # glass
        for wnd in self.windows:
            x0, y0, x1, y1 = wnd[:4]
            l = lit.get(wnd[:4], 0.0)
            if l > 0:
                lu = x0 + (x1 - x0) * (0.3 + 0.4 * hash01(self.seed, int(x0), 3))
                draw.radial(L, (lu, y0 + (y1 - y0) * 0.7), 0, (y1 - y0), [(0, mix((0.03, 0.03, 0.04), HOT, l * 0.9), 1),
                                                                         (1, mix((0.03, 0.03, 0.04), mul(AMBER, 0.45), l), 1)])
            else:
                draw.linear(L, (0, y0), (0, y1), [(0, (0.055, 0.062, 0.085), 1), (1, (0.02, 0.024, 0.036), 1)])
            L.rectangle(x0, y0, x1 - x0, y1 - y0)
            L.fill()
            if l > 0 and hash01(self.seed, int(y0), 9) < 0.5:
                # a drawn blind
                draw.rect(L, x0, y0, x1, y0 + (y1 - y0) * (0.3 + 0.5 * hash01(self.seed, int(x0), 4)))
                draw.fill(L, mix(INK, mul(AMBER, 0.5), 0.35 * l))
        # wall with holes (brick a shade off the facade's, so the blocks separate)
        L.new_path()
        draw.rect(L, self.x0, self.top, self.x1, self.ground)
        for wnd in self.windows:
            x0, y0, x1, y1 = wnd[:4]
            draw.rect(L, x0, y0, x1, y1)
        L.save()
        L.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        draw.linear(L, (0, self.top), (0, self.ground),
                    [(0, mix(INK, PAL.fog_at(1.0), 0.34 + self.tone), 1), (1, mix(INK, PAL.fog_at(1.0), 0.12 + self.tone * 0.5), 1)])
        L.fill()
        L.restore()
        # frames, sills, cornice
        for wnd in self.windows:
            x0, y0, x1, y1 = wnd[:4]
            cx = (x0 + x1) / 2
            ym = (y0 + y1) / 2
            draw.rect(L, x0, ym - 4 * s, x1, ym + 4 * s)
            draw.rect(L, cx - 2.5 * s, y0, cx + 2.5 * s, y1)
            draw.rect(L, x0 - 12 * s, y1, x1 + 12 * s, y1 + 12 * s)
            draw.rect(L, x0 - 8 * s, y0 - 18 * s, x1 + 8 * s, y0)
        draw.fill(L, INK)
        draw.rect(L, self.x0 - 20 * s, self.top - 10 * s, self.x1 + 20 * s, self.top + 30 * s)
        draw.rect(L, self.x0 - 10 * s, self.top + 30 * s, self.x1 + 10 * s, self.top + 46 * s)
        draw.rect(L, self.x0, self.ground - 400 * s, self.x1, self.ground - 370 * s)
        if self.water_tank:
            tx = self.x0 + (self.x1 - self.x0) * 0.35
            draw.rect(L, tx - 70 * s, self.top - 120 * s, tx - 64 * s, self.top)
            draw.rect(L, tx + 64 * s, self.top - 120 * s, tx + 70 * s, self.top)
            draw.rect(L, tx - 80 * s, self.top - 330 * s, tx + 80 * s, self.top - 120 * s)
            draw.poly(L, [(tx - 90 * s, self.top - 326 * s), (tx + 90 * s, self.top - 326 * s), (tx, self.top - 400 * s)])
        else:
            cx = self.x0 + (self.x1 - self.x0) * (0.25 + 0.5 * hash01(self.seed, 5))
            draw.rect(L, cx, self.top - 120 * s, cx + 70 * s, self.top)
            draw.rect(L, cx - 5 * s, self.top - 130 * s, cx + 75 * s, self.top - 120 * s)
        draw.fill(L, INK)

    def draw_light(self, A, t, k=1.0):
        s = self.s
        for (wnd, l) in self.lit_windows(t):
            x0, y0, x1, y1 = wnd[:4]
            rrect(A, x0 - 6 * s, y0 - 6 * s, x1 + 6 * s, y1 + 6 * s, 8 * s)
            draw.fill(A, AMBER, 0.18 * l * k)
            A.rectangle(x0 - 12 * s, y1 - 1.5 * s, x1 - x0 + 24 * s, 4 * s)
            draw.fill(A, AMBER, 0.4 * l * k)


def neighbours(facade, left_top=-760.0, right_top=640.0, width=1180.0):
    """The two neighbouring blocks flush with a Facade (taller on the left, lower on the
    right), in the facade's world coords. Returns [Block, Block]."""
    s = facade.scale
    g = facade.ground_y
    top = facade.top_y
    return [Block(facade.x0 - width * s, facade.x0, top + left_top * s, g, seed=31, scale=s, lit_frac=0.16,
                  tone=0.05, water_tank=True),
            Block(facade.x1, facade.x1 + width * s, top + right_top * s, g, seed=47, scale=s, lit_frac=0.2,
                  tone=-0.04)]


def draw_blocks(f, t, blocks, layer=None, light=1.0):
    """Draw neighbour Blocks on one layer + their window light."""
    spec = layer_spec(layer)
    with opened(f, spec) as L:
        for b in blocks:
            b.draw(f, t, L)
    if light > 0:
        with f.light(par=spec["par"], blur=max(5.0, spec["blur"] + 3)) as A:
            for b in blocks:
                b.draw_light(A, t, light * (1 - 0.75 * spec["fog"]))
        with f.emit(par=spec["par"]) as G:
            for b in blocks:
                for (wnd, l) in b.lit_windows(t):
                    x0, y0, x1, y1 = wnd[:4]
                    G.rectangle(x0, y0, x1 - x0, y1 - y0)
                    draw.fill(G, AMBER, 0.25 * l * light)


class Skyline:
    """Far city rooftops for the back layers: a strip of buildings of varied heights with
    water tanks, chimneys, antennas and a sprinkling of tiny lit windows.

    Skyline(x0, x1, base_y, seed=0, scale=1.0, height=(500, 1500), lit=0.06)
    Draw it on a fogged far layer: sky.draw(f, t, layer=dict(par=0.35, blur=5, fog=0.7))."""

    def __init__(self, x0=-2500.0, x1=3600.0, base_y=3940.0, seed=0, scale=1.0, height=(600.0, 1700.0), lit=0.06):
        self.x0, self.x1, self.base, self.seed, self.s = x0, x1, base_y, seed, scale
        self.height = height
        self.lit = lit
        self._path = None
        self._wins = None

    def _build(self):
        s = self.s
        bld = []
        x = self.x0
        k = 0
        while x < self.x1:
            w = (260 + 520 * hash01(self.seed, k, 1)) * s
            hgt = (self.height[0] + (self.height[1] - self.height[0]) * hash01(self.seed, k, 2) ** 1.4) * s
            bld.append((x, w, hgt, k))
            x += w - 6 * s
            k += 1
        wins = []

        def build(c):
            for (bx, w, hgt, k) in bld:
                top = self.base - hgt
                draw.rect(c, bx, top, bx + w, self.base + 10)
                draw.rect(c, bx - 8 * s, top - 10 * s, bx + w + 8 * s, top + 6 * s)
                r = hash01(self.seed, k, 3)
                if r < 0.28:     # water tank
                    tx = bx + w * (0.2 + 0.6 * hash01(self.seed, k, 4))
                    draw.rect(c, tx - 44 * s, top - 70 * s, tx - 40 * s, top)
                    draw.rect(c, tx + 40 * s, top - 70 * s, tx + 44 * s, top)
                    draw.rect(c, tx - 50 * s, top - 210 * s, tx + 50 * s, top - 70 * s)
                    draw.poly(c, [(tx - 58 * s, top - 206 * s), (tx + 58 * s, top - 206 * s), (tx, top - 262 * s)])
                elif r < 0.55:   # chimneys
                    for j in range(1 + int(hash01(self.seed, k, 5) * 2.5)):
                        cx = bx + w * hash01(self.seed, k, 6 + j)
                        ch = (40 + 80 * hash01(self.seed, k, 9 + j)) * s
                        draw.rect(c, cx - 16 * s, top - ch, cx + 16 * s, top)
                elif r < 0.7:    # antenna
                    ax = bx + w * hash01(self.seed, k, 12)
                    draw.rect(c, ax - 2 * s, top - 220 * s, ax + 2 * s, top)
                    draw.rect(c, ax - 34 * s, top - 200 * s, ax + 34 * s, top - 197 * s)
                    draw.rect(c, ax - 22 * s, top - 176 * s, ax + 22 * s, top - 173 * s)
                elif r < 0.8:    # stepped top
                    draw.rect(c, bx + w * 0.2, top - 120 * s, bx + w * 0.8, top)
                    draw.rect(c, bx + w * 0.38, top - 190 * s, bx + w * 0.62, top - 120 * s)
                # windows (lit ones only, tiny)
                cols = max(1, int(w / (95 * s)))
                rows = max(1, int(hgt / (140 * s)))
                for i in range(cols):
                    for j in range(rows):
                        if hash01(self.seed, k, i, j) < self.lit:
                            wx = bx + (i + 0.5) * w / cols
                            wy = top + 90 * s + j * 140 * s
                            if wy < self.base - 60 * s:
                                wins.append((wx - 16 * s, wy, wx + 16 * s, wy + 44 * s,
                                             0.4 + 0.6 * hash01(self.seed, k, i, j, 2)))
        self._path = record(build)
        self._wins = wins

    def draw(self, f, t, layer=None, light=1.0):
        if self._path is None:
            self._build()
        spec = layer_spec(layer)
        with opened(f, spec) as L:
            L.new_path()
            put(L, self._path)
            draw.fill(L, INK)
            for (x0, y0, x1, y1, l) in self._wins:
                L.rectangle(x0, y0, x1 - x0, y1 - y0)
                draw.fill(L, mix(INK, AMBER, 0.85 * l * light))
        if light > 0:
            with f.emit(par=spec["par"]) as G:
                for (x0, y0, x1, y1, l) in self._wins:
                    G.rectangle(x0, y0, x1 - x0, y1 - y0)
                    draw.fill(G, AMBER, 0.3 * l * light * (1 - 0.6 * spec["fog"]))


# =========================================================================== sky
def night_sky(f, t, horizon=None, glow=1.0, clouds=0.7, lightning=0.0, spread=520.0, glow_y=None, par=0.05):
    """Rainy city night sky (screen space, behind everything). Blue-black at the top; low
    clouds lit from below by the city, brightest at screen y `horizon` (px): put it at or
    just below the roofline so cornices and water tanks stand out against it (default
    0.55 H; or give glow_y, a world y seen through layer `par`). Drifting cloud texture;
    lightning 0..1 lights the clouds only (flash the set separately)."""
    f.sky(PAL.sky_top, mix(PAL.sky_top, PAL.sky_bottom, 0.7), mid=mix(PAL.sky_top, PAL.sky_bottom, 0.25), mid_at=0.4)
    if horizon is None:
        horizon = f.lcam(par).to_screen((W / 2, glow_y))[1] if glow_y is not None else H * 0.55
    hz = float(horizon)
    sp = float(spread)
    if glow > 0:
        # the city's glow on the underside of the clouds, rising from behind the roofs
        f.haze(PAL.fog_at(1.0), 0.80 * glow, y0=hz - sp * 0.15, y1=H + 600, feather=sp * 1.2, screen=True)
        f.haze(mix(PAL.fog_at(1.0), AMBER, 0.16), 0.30 * glow, y0=hz + sp * 0.05, y1=H + 600, feather=sp * 0.6,
               screen=True)
    if clouds > 0:
        # cloud banks: brighter where they catch the glow, darker rifts higher up
        f.haze(mix(PAL.fog_at(1.0), PAL.rain, 0.25), 0.50 * clouds, y0=hz - sp * 2.2, y1=hz + sp * 0.2,
               feather=sp * 1.3, tex=1.0, tex_scale=0.75, scroll=(7.0, 0.0), seed=4, screen=True)
        f.haze(PAL.sky_top, 0.55 * clouds, y0=-600, y1=hz - sp * 1.3, feather=sp * 1.2, tex=1.0, tex_scale=0.55,
               scroll=(4.0, 0.0), seed=8, screen=True)
    if lightning > 0:
        f.haze(PAL.lightning, 0.55 * lightning, y0=hz - sp * 3.0, y1=hz + sp * 0.4, feather=sp * 1.4, tex=0.8,
               tex_scale=0.6, scroll=(7.0, 0.0), seed=4, screen=True)
