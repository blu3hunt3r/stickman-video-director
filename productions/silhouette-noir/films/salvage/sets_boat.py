"""SALVAGE sets - B. THE BOAT: a small 1930s-50s working diving tender (~1880 px long).

Silhouette pieces, bow to stern: rope bow fender, cowl ventilator and mooring bitt on the
foredeck, the wheelhouse (see-through windows, mast with crosstree, stovepipe stack,
searchlight), then the stern working deck: the diver's hand-cranked AIR PUMP (box + two big
spoked flywheels with crank knobs), the red hose coil, the WINCH (holed drum flange + gear),
the gooseneck DAVIT with its block over the stern, a hurricane LANTERN, a life ring on the
railing and the diving LADDER hooked over the transom. Below the waterline: keel, propeller
in its aperture and the rudder - the hull underside for the split shots.

LOCAL frame: origin = waterline amidships, bow toward -x, y down. The boat rides the swell
(heave + pitch from sets_surface.sea_y). All anchors are returned in WORLD coords for time t.

    boat = Boat()                       # x=BOAT_X, davit sheave right above DIVE_X
    with f.layer() as L:
        boat.draw(L, t, pump_angle=200 * t, winch_angle=-90 * t, line_to=(60, 900))
    boat.draw_lights(f, t, lantern=1.0, window=0.6)
    feet_y = boat.deck_y(300, t)        # stand a figure on the deck at world x=300
    hand = boat.pump_crank(t, 200 * t)["near"]
"""
import math

from engine import draw
from engine.core import clamp, lerp, hash01, noise1, flicker

from .sets_common import (PAL, INK, RED, DIVE_X, shape, put, paint, round_rect, hole_circle,
                          solid_circle, oriented, line, xf, mix, sag_curve)
from .sets_surface import float_pose, sea_y

# ----------------------------------------------------------------------------- local layout
# Deck / sheer line (top of the hull outline), bow to stern.
SHEER = [(-962, -262), (-900, -251), (-800, -237), (-700, -225), (-640, -217), (-560, -180),
         (-190, -165), (200, -158), (600, -161), (905, -170)]
BOW = (-962.0, -262.0)
TRANSOM = (912.0, -110.0)
WH = dict(x0=-628.0, x1=-176.0, roof=-796.0, win_y=(-712.0, -572.0),
          wins=((-585.0, -489.0), (-469.0, -373.0), (-353.0, -257.0)))
MAST = (-505.0, -1290.0)          # masthead
STACK = (-300.0, -1062.0)         # stack top
PUMP = dict(box=(70.0, 250.0), box_h=192.0, R=122.0, squash=0.42, axle_y=-336.0, spokes=6,
            outlet=(236.0, -196.0), handle=40.0)
WINCH = dict(c=(565.0, -330.0), r=95.0, core=58.0, gear=(604.0, -352.0, 74.0))
DAVIT = dict(base=(800.0, -160.0), tip=(1042.0, -790.0), block=(1050.0, -742.0), drop=(1062.0, -718.0),
             fair=(806.0, -720.0))
LANTERN_HOOK = (772.0, -574.0)
HOSE = dict(coil=(368.0, -160.0), exit=(908.0, -178.0))
LADDER = dict(top=(899.0, -236.0), bottom=(980.0, 720.0), off=(24.0, -15.0), pitch=70.0)
LIFE_RING = (690.0, -236.0, 42.0, 25.0)
RAIL_H = 150.0
LENGTH = 1880.0
BOAT_X = DIVE_X - DAVIT["drop"][0]     # default origin: the line drops right at DIVE_X


def deck_local(lx):
    """Local y of the deck surface (where feet stand) at local x. On the foredeck this is
    the bulwark top minus 40 (feet stand behind the bulwark)."""
    pts = SHEER
    if lx <= pts[0][0]:
        y = pts[0][1]
    elif lx >= pts[-1][0]:
        y = pts[-1][1]
    else:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if lx <= x1:
                y = lerp(y0, y1, (lx - x0) / (x1 - x0))
                break
    if lx < -560:
        y += 40.0 * clamp((-560 - lx) / 60.0)
    return y


# ----------------------------------------------------------------------------- static shapes
def _hull(c):
    c.move_to(-962, -262)
    c.curve_to(-860, -246, -720, -229, -640, -217)
    c.line_to(-560, -180)
    c.curve_to(-300, -168, 300, -153, 600, -161)
    c.line_to(905, -170)
    c.curve_to(921, -120, 919, -40, 893, 16)                  # transom
    c.curve_to(874, 44, 842, 64, 790, 74)                     # counter
    c.line_to(753, 80)
    c.line_to(749, 262)                                       # sternpost
    c.line_to(640, 268)
    c.curve_to(200, 262, -300, 250, -520, 236)                # keel with drag aft
    c.curve_to(-700, 222, -826, 150, -884, 60)                # forefoot
    c.curve_to(-914, 0, -942, -150, -962, -262)               # raked stem
    c.close_path()
    # rudder + stock, skeg shoe under the propeller aperture
    pts = [(797, 56), (813, 56), (813, 74), (866, 78), (889, 120), (889, 228), (869, 268), (797, 268)]
    draw.poly(c, oriented(pts))
    draw.poly(c, oriented([(744, 258), (802, 262), (802, 275), (744, 271)]))
    # propeller: hub and two blades seen from the side
    solid_circle(c, (773, 168), 15)
    draw.ellipse(c, (776, 127), 12, 40, angle=8)
    draw.ellipse(c, (770, 208), 12, 38, angle=-6)
    # rope bow fender (the "beard") along the stem
    pts = [(-958, -232), (-978, -206), (-984, -150), (-974, -80), (-954, -14), (-930, 30), (-914, 0), (-934, -90),
           (-944, -170)]
    draw.smooth(c, oriented(pts), close=True, tension=0.45)
    # rubbing strake: a slim band proud of the hull just under the sheer (catches the outline at bow/stern)
    pts = [(-958, -238), (-640, -196), (-560, -158), (600, -140), (918, -150), (918, -134), (600, -124),
           (-560, -142), (-640, -180), (-956, -220)]
    draw.poly(c, oriented(pts))


def _wheelhouse(c):
    c.move_to(-628, -186)
    c.line_to(-604, -756)
    c.line_to(-633, -761)
    c.curve_to(-636, -776, -630, -790, -616, -793)
    c.curve_to(-450, -803, -300, -803, -156, -793)
    c.line_to(-154, -768)
    c.line_to(-176, -764)
    c.line_to(-176, -176)
    c.close_path()
    y0, y1 = WH["win_y"]
    for wx0, wx1 in WH["wins"]:
        round_rect(c, wx0, y0, wx1, y1, 9, hole=True)
    # roof gear: mast, crosstree, masthead lamp housing, stack + cap, searchlight, aerial post
    mx, my = MAST
    draw.poly(c, oriented([(mx - 9, -798), (mx + 9, -798), (mx + 4.5, my), (mx - 4.5, my)]))
    draw.poly(c, oriented([(mx - 62, -1170), (mx + 62, -1170), (mx + 58, -1162), (mx - 58, -1162)]))
    round_rect(c, mx - 9, my - 26, mx + 9, my + 2, 4)
    sx, sy = STACK
    draw.poly(c, oriented([(sx - 18, -798), (sx + 18, -798), (sx + 17, sy), (sx - 17, sy)]))
    round_rect(c, sx - 30, sy - 20, sx + 30, sy - 13, 3)
    draw.poly(c, oriented([(sx - 12, sy - 14), (sx - 9, sy - 14), (sx - 9, sy), (sx - 12, sy)]))
    draw.poly(c, oriented([(sx + 9, sy - 14), (sx + 12, sy - 14), (sx + 12, sy), (sx + 9, sy)]))
    round_rect(c, -600, -846, -560, -818, 10)
    draw.poly(c, oriented([(-584, -820), (-576, -820), (-576, -798), (-584, -798)]))
    draw.poly(c, oriented([(-614, -834), (-600, -838), (-600, -826), (-614, -830)]))
    draw.poly(c, oriented([(-196, -796), (-188, -796), (-188, -880), (-196, -880)]))


def _foredeck(c):
    # cowl ventilator: a tube rising from the deck, curving to a flared mouth facing forward
    pts = [(-772, -222), (-748, -222), (-748, -330), (-752, -366), (-770, -392), (-796, -404), (-812, -440),
           (-834, -436), (-842, -400), (-830, -362), (-806, -348), (-780, -340), (-772, -320)]
    draw.smooth(c, oriented(pts), close=True, tension=0.35)
    # mooring bitt with a cross pin
    draw.poly(c, oriented([(-892, -246), (-866, -244), (-866, -312), (-892, -314)]))
    round_rect(c, -906, -306, -852, -296, 4)
    solid_circle(c, (-879, -316), 15)


def _railing(c):
    xs = [-150.0 + 118.0 * i for i in range(8)] + [893.0]
    for x in xs:
        if 730 < x < 860:
            continue
        y = deck_local(x)
        draw.poly(c, oriented([(x - 4, y + 2), (x + 4, y + 2), (x + 3.5, y - RAIL_H), (x - 3.5, y - RAIL_H)]))
    for off, w in ((RAIL_H, 7.0), (RAIL_H * 0.52, 5.0)):
        pts = [(x, deck_local(x) - off) for x in (-170, 50, 300, 600, 760)] + [(898, deck_local(898) - off)]
        top = [(x, y - w / 2) for x, y in pts]
        bot = [(x, y + w / 2) for x, y in pts]
        draw.poly(c, oriented(top + bot[::-1]))
    # life ring hanging on the rail (a ring you can see through)
    x, y, R, r = LIFE_RING
    solid_circle(c, (x, y), R)
    hole_circle(c, (x, y), r)


def _davit(c):
    # tapered gooseneck: centreline points with widths
    cl = [(800, -160, 36), (800, -420, 33), (801, -620, 30), (808, -700, 28), (836, -762, 26), (900, -796, 24),
          (980, -800, 22), (1042, -790, 22)]
    left, right = [], []
    for i, (x, y, w) in enumerate(cl):
        q0 = cl[max(i - 1, 0)]
        q1 = cl[min(i + 1, len(cl) - 1)]
        tx, ty = q1[0] - q0[0], q1[1] - q0[1]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L, tx / L
        left.append((x + nx * w / 2, y + ny * w / 2))
        right.append((x - nx * w / 2, y - ny * w / 2))
    draw.smooth(c, oriented(left + right[::-1]), close=True, tension=0.4)
    # base plate and the diagonal brace forward
    draw.poly(c, oriented([(770, -156), (832, -156), (826, -176), (776, -176)]))
    draw.poly(c, oriented([(796, -430), (806, -414), (726, -160), (712, -164)]))
    # end fitting at the tip
    solid_circle(c, (1042, -790), 15)


def _pump_box(c):
    x0, x1 = PUMP["box"]
    y0 = -158.0 - PUMP["box_h"]
    round_rect(c, x0 - 10, -172, x1 + 10, -150, 3)                    # skids
    round_rect(c, x0 + 6, y0 + 12, x1 - 6, -160, 4)                   # chest
    round_rect(c, x0, y0, x1, y0 + 18, 5)                             # lid lip
    xm = (x0 + x1) / 2
    draw.poly(c, oriented([(xm - 4, y0), (xm + 4, y0), (xm + 4, y0 - 36), (xm - 4, y0 - 36)]))
    solid_circle(c, (xm, y0 - 52), 19)                                # pressure gauge
    hole_circle(c, (xm, y0 - 52), 11)
    solid_circle(c, (xm, y0 - 52), 4)
    ox, oy = PUMP["outlet"]
    round_rect(c, ox - 10, oy - 9, ox + 22, oy + 9, 5)                # air outlet nozzle
    # bearing pedestals at both ends
    for cx in (x0, x1):
        draw.poly(c, oriented([(cx - 16, y0 + 10), (cx + 16, y0 + 10), (cx + 7, PUMP["axle_y"]),
                               (cx - 7, PUMP["axle_y"])]))


def _flywheel(R, spokes=6):
    """Spoked flywheel in its own plane (unit: px), centred at 0; drawn foreshortened."""
    def b(c):
        solid_circle(c, (0, 0), R)
        hole_circle(c, (0, 0), R - 16)
        solid_circle(c, (0, 0), 22)
        for k in range(spokes):
            a = 2 * math.pi * k / spokes
            ca, sa = math.cos(a), math.sin(a)
            na, nb = -sa, ca
            w0, w1 = 8.0, 5.5
            pts = [(ca * 16 + na * w0, sa * 16 + nb * w0), (ca * (R - 10) + na * w1, sa * (R - 10) + nb * w1),
                   (ca * (R - 10) - na * w1, sa * (R - 10) - nb * w1), (ca * 16 - na * w0, sa * 16 - nb * w0)]
            draw.poly(c, oriented(pts))
    return b


def _crank_points(angle):
    """Local crank geometry for both flywheels: [(rim point, grip end, side)] left then right.
    The two cranks are 180 degrees apart; the handles stick out from the box ends."""
    R, q = PUMP["R"], PUMP["squash"]
    out = []
    for cx, side, off in ((PUMP["box"][0], -1.0, 0.0), (PUMP["box"][1], 1.0, 180.0)):
        a = math.radians(angle + off)
        rim = (cx + q * R * math.cos(a), PUMP["axle_y"] + R * math.sin(a))
        grip = (rim[0] + side * PUMP["handle"], rim[1])
        out.append((rim, grip, side))
    return out


def _winch_frame(c):
    cx, cy = WINCH["c"]
    pts = [(cx - 70, -158), (cx + 70, -158), (cx + 26, cy - 18), (cx - 26, cy - 18)]
    draw.poly(c, oriented(pts))
    round_rect(c, cx - 84, -172, cx + 84, -152, 4)
    gx, gy, gr = WINCH["gear"]
    draw.poly(c, oriented([(gx - 10, -160), (gx + 40, -160), (gx + 8, gy), (gx - 6, gy)]))


def _winch_flange(c):
    R = WINCH["r"]
    solid_circle(c, (0, 0), R)
    for k in range(5):
        a = 2 * math.pi * k / 5
        hole_circle(c, (math.cos(a) * R * 0.58, math.sin(a) * R * 0.58), R * 0.19)


def _gear(R, teeth=22):
    def b(c):
        pts = []
        for k in range(teeth * 4):
            a = 2 * math.pi * k / (teeth * 4)
            r = R if (k % 4) in (1, 2) else R - 10
            pts.append((math.cos(a) * r, math.sin(a) * r))
        draw.poly(c, oriented(pts))
        hole_circle(c, (0, 0), R * 0.55)
        solid_circle(c, (0, 0), R * 0.22)
        for k in range(4):
            a = math.pi / 2 * k
            ca, sa = math.cos(a), math.sin(a)
            draw.poly(c, oriented([(ca * R * 0.15 - sa * 5, sa * R * 0.15 + ca * 5),
                                   (ca * R * 0.6 - sa * 5, sa * R * 0.6 + ca * 5),
                                   (ca * R * 0.6 + sa * 5, sa * R * 0.6 - ca * 5),
                                   (ca * R * 0.15 + sa * 5, sa * R * 0.15 - ca * 5)]))
    return b


def _lantern(c):
    """Hurricane lantern, hanging point at (0, 0): bail, cap, glass globe cage, fount."""
    pts = [(-14, 4), (-8, -2), (8, -2), (14, 4), (10, 8), (-10, 8)]
    draw.poly(c, oriented(pts))                                           # bail / ring
    round_rect(c, -15, 8, 15, 22, 6)                                     # cap
    draw.poly(c, oriented([(-12, 20), (12, 20), (19, 46), (12, 70), (-12, 70), (-19, 46)]))  # globe
    round_rect(c, -21, 68, 21, 92, 7)                                    # fount
    draw.poly(c, oriented([(-23, 44), (-19, 44), (-15, 70), (-19, 70)]))    # guard wire bulges
    draw.poly(c, oriented([(19, 44), (23, 44), (19, 70), (15, 70)]))


LANTERN_GLASS = (0.0, 45.0, 13.0, 21.0)   # local centre x, y, half width, half height


def _block(c):
    """Sheave block hanging from the davit tip (local origin at the pin above it)."""
    round_rect(c, -6, 0, 6, 16, 3)
    draw.poly(c, oriented([(-18, 14), (18, 14), (24, 40), (18, 66), (-18, 66), (-24, 40)]))
    solid_circle(c, (0, 40), 23)


def _hook(c):
    """Cargo hook, eye at (0, 0)."""
    solid_circle(c, (0, 0), 9)
    hole_circle(c, (0, 0), 4.5)
    pts = [(-5, 8), (5, 8), (6, 30), (14, 44), (12, 58), (0, 66), (-14, 60), (-18, 46), (-12, 42), (-8, 52), (0, 56),
           (6, 50), (4, 40), (-5, 30)]
    draw.smooth(c, oriented(pts), close=True, tension=0.3)


def _ladder(c):
    (x0, y0), (x1, y1) = LADDER["top"], LADDER["bottom"]
    ox, oy = LADDER["off"]
    for dx, dy in ((0.0, 0.0), (ox, oy)):
        draw.poly(c, oriented([(x0 + dx - 5, y0 + dy), (x0 + dx + 5, y0 + dy), (x1 + dx + 5, y1 + dy),
                               (x1 + dx - 5, y1 + dy)]))
        # hooks over the gunwale
        pts = [(x0 + dx - 5, y0 + dy + 4), (x0 + dx - 6, y0 + dy - 22), (x0 + dx - 26, y0 + dy - 30),
               (x0 + dx - 38, y0 + dy - 16), (x0 + dx - 31, y0 + dy - 12), (x0 + dx - 24, y0 + dy - 21),
               (x0 + dx + 5, y0 + dy - 14), (x0 + dx + 5, y0 + dy + 4)]
        draw.poly(c, oriented(pts))
    L = math.hypot(x1 - x0, y1 - y0)
    n = int(L / LADDER["pitch"])
    for i in range(1, n + 1):
        u = i * LADDER["pitch"] / L
        px, py = lerp(x0, x1, u), lerp(y0, y1, u)
        draw.poly(c, oriented([(px - 2, py - 4), (px + ox + 2, py + oy - 4), (px + ox + 2, py + oy + 4),
                               (px - 2, py + 4)]))


def _hose_coil(c):
    """Coil of hose lying on deck, seen from the side: stacked loops (local origin at the
    deck under its centre)."""
    for i, (dx, y, rx) in enumerate(((0, -6, 66), (3, -17, 63), (-2, -28, 60), (2, -38, 54))):
        draw.ellipse(c, (dx, y), rx, 7.5)
    draw.poly(c, oriented([(-66, -4), (66, -4), (60, -36), (-58, -36)]))


# ----------------------------------------------------------------------------- the boat
class Boat:
    """The diving tender. x: world x of the local origin (waterline amidships); default puts
    the davit's line drop at DIVE_X. flip=True turns her around (bow to the right).
    amp: swell amplitude multiplier (0 = flat calm), rock: extra pitch multiplier."""

    def __init__(self, x=None, flip=False, amp=1.0, rock=1.0):
        self.x = BOAT_X if x is None else float(x)
        self.flip = bool(flip)
        self.amp = amp
        self.rock = rock

    # ---------------------------------------------------------------- pose / transforms
    def pose(self, t):
        """(origin_x, origin_y, pitch_deg) of the boat at time t (riding the swell)."""
        y, ang = float_pose(self.x, t, length=LENGTH * 0.85, amp=self.amp, lag=0.35)
        bob = 1.5 * math.sin(t * 1.9)        # small extra heave from chop
        return self.x, y + bob * self.amp, ang * self.rock

    def to_world(self, p, t, pose=None):
        """World point of local point p at time t."""
        ox, oy, ang = pose or self.pose(t)
        lx = -p[0] if self.flip else p[0]
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        return (ox + lx * ca - p[1] * sa, oy + lx * sa + p[1] * ca)

    def to_local(self, p, t, pose=None):
        ox, oy, ang = pose or self.pose(t)
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        dx, dy = p[0] - ox, p[1] - oy
        lx, ly = dx * ca + dy * sa, -dx * sa + dy * ca
        return (-lx if self.flip else lx, ly)

    def angle(self, t):
        """Pitch in degrees (rotate deck-mounted things by this)."""
        return self.pose(t)[2]

    def _begin(self, ctx, pose):
        ox, oy, ang = pose
        ctx.save()
        ctx.translate(ox, oy)
        ctx.rotate(math.radians(ang))
        if self.flip:
            ctx.scale(-1, 1)

    # ---------------------------------------------------------------- anchors (world)
    def deck_y(self, x, t):
        """World y of the deck surface under world x (feet go here)."""
        pose = self.pose(t)
        lx = self.to_local((x, pose[1] - 160), t, pose)[0]
        for _ in range(2):
            w = self.to_world((lx, deck_local(lx)), t, pose)
            lx += (x - w[0]) * (-1 if self.flip else 1)
        return self.to_world((lx, deck_local(lx)), t, pose)[1]

    def deck_point(self, lx, t):
        """World point on the deck at LOCAL x (stations: see BOW, WH, PUMP, WINCH, DAVIT)."""
        return self.to_world((lx, deck_local(lx)), t)

    def davit_tip(self, t):
        return self.to_world(DAVIT["tip"], t)

    def sheave(self, t, swing=None):
        """World point where the lifting line leaves the block and drops toward the sea."""
        piv = self.to_world(DAVIT["tip"], t)
        sw = self._block_swing(t) if swing is None else swing
        d = (DAVIT["drop"][0] - DAVIT["tip"][0], DAVIT["drop"][1] - DAVIT["tip"][1])
        d = (-d[0] if self.flip else d[0], d[1])
        a = math.radians(sw)
        return (piv[0] + d[0] * math.cos(a) - d[1] * math.sin(a), piv[1] + d[0] * math.sin(a) + d[1] * math.cos(a))

    def winch_drum(self, t):
        """(centre, flange radius, core radius) of the winch drum, world."""
        return self.to_world(WINCH["c"], t), WINCH["r"], WINCH["core"]

    def pump_crank(self, t, angle):
        """Air-pump cranks for a crank angle (deg): dict(left, right = world grip points for
        the hands (handles stick out of the box ends; the two cranks are 180 deg apart),
        hub_left, hub_right, R). Animate `angle` and pass the same value to
        draw(pump_angle=...)."""
        (r0, g0, _), (r1, g1, _) = _crank_points(angle)
        return dict(left=self.to_world(g0, t), right=self.to_world(g1, t),
                    hub_left=self.to_world((PUMP["box"][0], PUMP["axle_y"]), t),
                    hub_right=self.to_world((PUMP["box"][1], PUMP["axle_y"]), t), R=PUMP["R"])

    def lantern_pos(self, t):
        """World centre of the lantern's glass (the light source)."""
        hook = self.to_world(LANTERN_HOOK, t)
        a = math.radians(self._lantern_swing(t))
        gx, gy = LANTERN_GLASS[0], LANTERN_GLASS[1]
        return (hook[0] + gx * math.cos(a) - gy * math.sin(a), hook[1] + gx * math.sin(a) + gy * math.cos(a))

    def hose_exit(self, t):
        """World point where the red air hose goes over the stern into the sea (the cut point)."""
        return self.to_world(HOSE["exit"], t)

    def pump_outlet(self, t):
        return self.to_world(PUMP["outlet"], t)

    def ladder(self, t):
        """dict(top, bottom (world, near rail), rungs=[world centre of each rung], hooks)."""
        (x0, y0), (x1, y1) = LADDER["top"], LADDER["bottom"]
        ox, oy = LADDER["off"]
        L = math.hypot(x1 - x0, y1 - y0)
        rungs = []
        for i in range(1, int(L / LADDER["pitch"]) + 1):
            u = i * LADDER["pitch"] / L
            rungs.append(self.to_world((lerp(x0, x1, u) + ox / 2, lerp(y0, y1, u) + oy / 2), t))
        return dict(top=self.to_world((x0, y0), t), bottom=self.to_world((x1, y1), t), rungs=rungs,
                    hooks=self.to_world((x0 - 20, y0 - 26), t))

    def masthead(self, t):
        return self.to_world((MAST[0], MAST[1] - 12), t)

    def window_centers(self, t):
        y0, y1 = WH["win_y"]
        return [self.to_world(((a + b) / 2, (y0 + y1) / 2), t) for a, b in WH["wins"]]

    def stations(self, t):
        """Handy world points: where people stand and where things are."""
        return dict(
            bow=self.to_world(BOW, t), transom=self.to_world(TRANSOM, t),
            wheelhouse_aft=self.deck_point(-150, t),      # stand just aft of the wheelhouse
            pump_left=self.deck_point(-10, t),            # crank the pump from here (left handle)
            coil=self.deck_point(HOSE["coil"][0], t),
            winch_fwd=self.deck_point(470, t),            # work the winch from here
            stern=self.deck_point(720, t),                # stand at the stern, by the davit
            ladder_top=self.deck_point(880, t),
        )

    # ---------------------------------------------------------------- motion of hanging things
    def _lantern_swing(self, t):
        """Lantern angle (deg, world): hangs plumb, lagging the boat's pitch a little."""
        a_now = self.pose(t)[2]
        a_lag = self.pose(t - 0.45)[2]
        return 1.6 * (a_now - a_lag) * 4.0 + 0.8 * math.sin(t * 2.3)

    def _block_swing(self, t):
        a_now = self.pose(t)[2]
        a_lag = self.pose(t - 0.6)[2]
        return 1.2 * (a_now - a_lag) * 4.0 + 0.6 * math.sin(t * 1.7 + 1.0)

    # ---------------------------------------------------------------- drawing
    def draw(self, ctx, t, color=None, pump_angle=0.0, winch_angle=0.0, hose_coil=1.0, hose=True,
             line_to=None, line_sag=0.0, hook=True, lantern=True, ladder=True, rail=True):
        """Draw the whole boat silhouette on ctx (world coords, action plane).

        pump_angle  : flywheel crank angle (deg). Same value -> pump_crank(t, angle).
        winch_angle : drum rotation (deg); hauling in = negative.
        hose_coil   : 0..1 how much hose is still coiled on deck (red); hose=False hides
                      the deck run of the hose (pump -> coil -> stern) and the coil.
        line_to     : world point where the lifting line ends (it drops from sheave(t));
                      None = only the block. line_sag bows it (current). hook: draw the
                      cargo hook at the end.
        Returns dict of a few world anchors (sheave, hose_exit, lantern)."""
        col = color or INK
        pose = self.pose(t)
        ang = pose[2]
        self._begin(ctx, pose)
        ctx.new_path()
        put(ctx, shape("boat_hull", _hull))
        put(ctx, shape("boat_wh", _wheelhouse))
        put(ctx, shape("boat_fore", _foredeck))
        put(ctx, shape("boat_davit", _davit))
        put(ctx, shape("boat_pump", _pump_box))
        put(ctx, shape("boat_winch", _winch_frame))
        if ladder:
            put(ctx, shape("boat_ladder", _ladder))
        paint(ctx, col)
        # flywheels at both box ends (foreshortened discs), crank pins + handles
        R, q = PUMP["R"], PUMP["squash"]
        for (rim, grip, side), cx in zip(_crank_points(pump_angle), PUMP["box"]):
            ctx.save()
            ctx.translate(cx, PUMP["axle_y"])
            ctx.scale(q, 1.0)
            ctx.rotate(math.radians(pump_angle + (0.0 if side < 0 else 180.0)))
            ctx.append_path(shape(("fly", R), _flywheel(R, PUMP["spokes"])))
            ctx.restore()
            draw.capsule(ctx, rim, grip, 7, 7)
            solid_circle(ctx, grip, 11)
            paint(ctx, col)
        gx, gy, gr = WINCH["gear"]
        put(ctx, shape(("gear", gr), _gear(gr)), gx, gy, -winch_angle * WINCH["r"] / gr * 0.5)
        cx, cy = WINCH["c"]
        put(ctx, shape("flange", _winch_flange), cx, cy, winch_angle)
        solid_circle(ctx, (cx, cy), 16)
        a = math.radians(-winch_angle * 0.5)
        draw.capsule(ctx, (gx, gy), (gx + math.cos(a) * 62, gy + math.sin(a) * 62), 7, 6)
        solid_circle(ctx, (gx + math.cos(a) * 62, gy + math.sin(a) * 62), 11)
        paint(ctx, col)
        # block and lantern hang plumb (counter-rotate the pitch)
        bs = self._block_swing(t)
        tx, ty = DAVIT["tip"]
        put(ctx, shape("block", _block), tx + 6, ty + 4, (bs - ang) * (-1 if self.flip else 1))
        if lantern:
            hx, hy = LANTERN_HOOK
            draw.capsule(ctx, (DAVIT["base"][0], hy - 10), (hx, hy - 4), 4, 3.5)
            put(ctx, shape("lantern", _lantern), hx, hy, (self._lantern_swing(t) - ang) * (-1 if self.flip else 1))
        paint(ctx, col)
        # lifting line: drum -> fairlead -> along the arm -> over the sheave
        drum_top = (cx, cy - WINCH["core"])
        line(ctx, [drum_top, DAVIT["fair"], (900, -808), (1046, -770)], 5.0, col)
        # hose: deck run (red), coil
        if hose:
            ox_, oy_ = PUMP["outlet"]
            kx, ky = HOSE["coil"]
            ex, ey = HOSE["exit"]
            line(ctx, [(ox_ + 18, oy_), (ox_ + 40, oy_ + 18), (kx - 52, -168)], 9.0, RED)
            line(ctx, [(kx + 55, -166), (600, -166), (840, -172), (ex, ey)], 9.0, RED)
            if hose_coil > 0.02:
                put(ctx, shape("coil", _hose_coil), kx, ky, 0.0, 1.0, sy=0.35 + 0.65 * clamp(hose_coil))
                paint(ctx, RED)
        if rail:        # the near-side railing is in front of everything on deck
            put(ctx, shape("boat_rail", _railing))
            paint(ctx, col)
        ctx.restore()
        sheave = self.sheave(t, bs)
        if line_to is not None:
            pts = sag_curve(sheave, line_to, 0.0, 12) if not line_sag else self._bowed(sheave, line_to, line_sag)
            line(ctx, pts, 5.0, col)
            if hook:
                put(ctx, shape("hook", _hook), line_to[0], line_to[1] - 2, 0.0)
                paint(ctx, col)
        return dict(sheave=sheave, hose_exit=self.hose_exit(t), lantern=self.lantern_pos(t))

    @staticmethod
    def _bowed(a, b, sag, n=16):
        out = []
        for i in range(n + 1):
            u = i / n
            out.append((lerp(a[0], b[0], u) + sag * 4 * u * (1 - u), lerp(a[1], b[1], u)))
        return out

    def draw_lights(self, f, t, lantern=1.0, window=0.0, masthead=0.0, flick=True):
        """Warm emissive lights: the lantern (glass + halo), lit wheelhouse windows (window
        0..1 fills the see-through windows with lamplight), a masthead light. Call after the
        action plane is drawn."""
        pose = self.pose(t)
        k = flicker(t, seed=31, rate=7.0, depth=0.22) if flick else 1.0
        if window > 0:
            y0, y1 = WH["win_y"]
            c = f.ctx
            self._begin(c, pose)
            for wx0, wx1 in WH["wins"]:
                round_rect(c, wx0, y0, wx1, y1, 9)
            c.restore()
            draw.linear(c, self.to_world((0, y0), t), self.to_world((0, y1), t),
                        [(0, mix(PAL.ink, PAL.light, 0.55), window), (1, mix(PAL.ink, PAL.light, 0.85), window)])
            c.fill()
            with f.emit() as G:
                for wc in self.window_centers(t):
                    draw.glow_disc(G, wc, 70, PAL.light, 0.25 * window)
        if lantern > 0:
            p = self.lantern_pos(t)
            a = math.radians(self._lantern_swing(t))
            c = f.ctx
            c.save()
            c.translate(*p)
            c.rotate(a)
            draw.ellipse(c, (0, 0), LANTERN_GLASS[2], LANTERN_GLASS[3])
            c.restore()
            draw.fill(c, mix(PAL.light, (1, 1, 1), 0.35), clamp(lantern))
            with f.emit() as G:
                draw.glow_disc(G, p, 38, PAL.light, 0.9 * lantern * k)
                draw.circle(G, p, 9)
                draw.fill(G, (1.0, 0.95, 0.85), lantern * k)
            with f.light(blur=16) as A:
                draw.glow_disc(A, p, 330, PAL.light, 0.22 * lantern * k)
                draw.glow_disc(A, p, 120, PAL.light, 0.20 * lantern * k)
        if masthead > 0:
            p = self.masthead(t)
            with f.emit() as G:
                draw.glow_disc(G, p, 26, PAL.light, 0.8 * masthead)
            c = f.ctx
            draw.circle(c, p, 5)
            draw.fill(c, mix(PAL.light, (1, 1, 1), 0.5), masthead)
