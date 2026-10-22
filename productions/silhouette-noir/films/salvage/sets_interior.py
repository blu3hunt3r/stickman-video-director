"""SALVAGE sets - F. INSIDE THE MERIDIAN (s08-s10): the capsized passage (now a vertical
shaft), the captain's cabin lying on its side, and the close-up of the safe's dial.

A separate little world with its own origin, drawn with the deep world's 2.5D View so the
shaft has true perspective while the camera follows the diver down:
    x right, y DOWN (gravity), z into the screen (z = 0: where the diver hangs).
    SHAFT: the athwartships passage, now vertical, 2.1 m wide: walls at x = +-SHAFT_HW, back
      wall (an old bulkhead, with a door on its side and two ports) at z = SHAFT_BACK, the
      walls' near edges at z = -NEAR (soft occluders). Its top (y = SHAFT_TOP) is the hull
      plating with the cut hole the diver came in by (cold light); it drops to y = SHAFT_BOT.
    CABIN: below it, x from CABIN_X0 to CABIN_X1 (her old floor-to-ceiling height, now
      sideways), y from SHAFT_BOT to CABIN_BOT, back wall at z = CABIN_BACK. Her former FLOOR
      is the RIGHT wall (the desk and the SAFE are bolted to it), the former ceiling is the
      LEFT wall (the lamp hangs off it), the hull's port side is the floor now (two black
      portholes), the starboard side is the ceiling: the shaft opens through it, and behind
      that a broken skylight - the "hull opening above" the winch line comes down through in
      s10 (Interior.skylight()).

It is black in there: walls are barely there until the helmet lamp finds them, and things in
front of the lit pool read as ink silhouettes (the Inside flashlight trick). Per frame:

    view = InteriorView(f)                      # this frame's projector (dark, no haze)
    inn = Interior()
    inn.draw(f, t, view)                        # walls, far details, the cold glow from the hole
    inn.draw_lit(f, t, view, lamp, aim)         # the lamp's warm pool on the walls (additive)
    a = inn.draw_mid(f, t, view, safe_lit=0.8)  # pipes, cables, door leaf, chair, desk, lamp, safe
    ... diver (figure.py) ...
    inn.draw_front(f, t, view)                  # near wall edges, soft

    dc = DialCloseup()                          # s08 end / s09: the dial fills the frame
    f.set_camera(dc.camera(r_screen=260))       # dial centred at (540, 960), on-screen radius 260
    dc.draw(f, t, dial_angle, door=0.0)         # door 0..1 swings it open toward the camera
"""
import math
from contextlib import contextmanager

import cairo

from engine import draw
from engine.core import clamp, lerp, hash01
from engine.frame import Camera

from .sets_common import PAL, INK, mix, oriented, jag, line, sag_curve, sway, round_rect, solid_circle, hole_circle
from .sets_deep import View, Painter, rod3, prism3, fill_grad, convex_hull
from .sets_props import draw_safe, draw_dial, draw_logbook, draw_captain_cap, SAFE

# ----------------------------------------------------------------------------- layout
SHAFT_HW = 350.0          # half width of the shaft (wall to wall 2.1 m)
SHAFT_TOP = -600.0        # the hull plating with the hole the diver came in by
SHAFT_BOT = 3600.0        # the shaft opens into the cabin here
SHAFT_BACK = 420.0        # z of the shaft's back wall
NEAR = 900.0              # the walls' near edges at z = -NEAR (in front of the diver)
CABIN_X0, CABIN_X1 = -460.0, 460.0
CABIN_BOT = 5200.0
CABIN_BACK = 900.0

INT_BG = mix(INK, PAL.deep, 0.55)          # the darkness in there (fog colour)
BACK_C = mix(INK, PAL.mid, 0.17)           # bulkheads, barely visible
SIDE_C = mix(INK, PAL.mid, 0.10)           # the walls seen at a grazing angle
WOOD_C = mix(mix(INK, PAL.mid, 0.14), PAL.light, 0.06)
COLD = mix(PAL.mid, PAL.surface, 0.35)     # the water light coming in through the hole


class InteriorView(View):
    """View for the inside of the wreck: no depth haze, everything sinks into INT_BG."""

    def __init__(self, f, lens=6000.0, fog_len=5200.0, vp=None):
        super().__init__(f, lens=lens, fog_len=fog_len, fog_gamma=1.0, fog_max=0.9, vp=vp, down_fog=0.0)

    def bg(self, Y):
        return INT_BG


@contextmanager
def at_depth(ctx, view, z):
    """Draw flat world-coord art inside this block and it appears at distance z."""
    k = view.k(z)
    ctx.save()
    ctx.translate(view.vx * (1 - k), view.vy * (1 - k))
    ctx.scale(k, k)
    try:
        yield k
    finally:
        ctx.restore()


def _quad(view, pts3):
    return [view.Pp(p) for p in pts3]


def _plane(c, view, pts3, c_near, c_far):
    """Fill a receding wall quad (near edge first) with a near -> far gradient."""
    q = _quad(view, pts3)
    draw.poly(c, q)
    fill_grad(c, ((q[0][0] + q[1][0]) / 2, (q[0][1] + q[1][1]) / 2),
              ((q[2][0] + q[3][0]) / 2, (q[2][1] + q[3][1]) / 2), c_near, c_far)


# ----------------------------------------------------------------------------- the interior
class Interior:
    """The shaft and the captain's cabin. Anchors are world (x, y) at z = 0 unless noted."""

    DOOR = (-300.0, 1300.0, 330.0, 1560.0)          # opening on the shaft's back wall (on its side)
    PORTS = ((-150.0, 2480.0), (150.0, 2480.0))     # round ports in the shaft's back wall
    HOLE = (40.0, -60.0, 250.0)                     # entry hole in the plating at the top: (x, z, r)
    SAFE_S = 1.6
    SAFE_AT = (CABIN_X1 - (SAFE["h"] + 16.0) * 1.6, CABIN_BOT - 20.0, 260.0)   # draw_safe anchor (x, y, z)
    SKYLIGHT = (0.0, 640.0, 170.0)                  # (x, z, radius) of the broken skylight in the ceiling
    LAMP_MOUNT = (CABIN_X0, 4250.0)
    PORTHOLES = ((-200.0, 420.0), (180.0, 640.0))   # (x, z) of the portholes in the cabin floor

    # ---------------------------------------------------------------- anchors
    def holds(self, y0=SHAFT_TOP, y1=SHAFT_BOT, side=-1):
        """Hand holds for the descent 'hand over hand': brackets of the pipe on the left
        (side=-1) or right wall, world (x, y) at z ~ -140, top to bottom, 380 px apart."""
        x = side * (SHAFT_HW - 70.0)
        out = []
        y = math.ceil(y0 / 380.0) * 380.0
        while y <= y1:
            out.append((x, y))
            y += 380.0
        return out

    def entry(self):
        """World (x, y, z) of the cut hole at the top of the shaft (where the diver came in)."""
        x, z, r = self.HOLE
        return (x, SHAFT_TOP, z)

    def safe_pose(self):
        """draw_safe arguments of the safe on its side: dict(x, y, z, s, angle)."""
        x, y, z = self.SAFE_AT
        return dict(x=x, y=y, z=z, s=self.SAFE_S, angle=-90.0)

    def safe_dial(self, view=None):
        """World (x, y, z) of the safe's dial centre; with a view, also its (X, Y) on the
        action plane: returns (p3, (X, Y))."""
        x0, y0, z = self.SAFE_AT
        s = self.SAFE_S
        dx, dy = SAFE["dial"][:2]
        p = (x0 + dy * s, y0 - dx * s, z)                 # angle -90: local (x, y) -> (y, -x)
        return (p, view.Pp(p)) if view is not None else p

    def safe_outline(self, view):
        """The safe's silhouette (4 action-plane points) - for shadows and hit tests."""
        x0, y0, z = self.SAFE_AT
        sc = self.SAFE_S
        corners = ((-10.0, -10.0), (SAFE["w"] + 10.0, -10.0), (SAFE["w"] + 10.0, SAFE["h"] + 16.0), (-10.0, SAFE["h"] + 16.0))
        return [view.P(x0 + ly * sc, y0 - lx * sc, z) for lx, ly in corners]

    def skylight(self):
        """World (x, y, z) of the broken skylight in the cabin's ceiling - the 'hull opening
        above' the winch line comes down through in s10."""
        x, z, r = self.SKYLIGHT
        return (x, SHAFT_BOT, z)

    def lamp_pose(self, t):
        """(stem end, globe centre) of the cabin's hanging lamp, swaying on its chain."""
        mx, my = self.LAMP_MOUNT
        a = math.radians(sway(t, seed=61, amp=7.0, period=6.0))
        top = (mx + 130.0, my)
        L = 250.0
        return top, (top[0] + math.sin(a) * L, top[1] + math.cos(a) * L)

    @staticmethod
    def door_angle(t, wake=0.0):
        """Swing (deg, 0 = hanging shut) of the door on its side in the shaft's back wall: it
        hangs from its top hinge and breathes in the current; wake (0..1) = the diver passing
        - it swings open toward the camera."""
        return clamp(14.0 + 10.0 * sway(t, seed=73, amp=1.0, period=7.0) + 55.0 * wake, 0.0, 80.0)

    @staticmethod
    def chair_pose(t):
        """(x, y, z, angle) of the fallen chair turning slowly in the shaft."""
        return (90.0 + 60 * sway(t, 81, 1.0, 9.0), 2650.0 + 80 * sway(t, 82, 1.0, 11.0), -240.0,
                -35.0 + 9.0 * t + 25 * sway(t, 83, 1.0, 8.0))

    # ---------------------------------------------------------------- the dark walls
    def draw(self, f, t, view=None, cold=1.0):
        """Bulkheads and walls (dark) with their seams, the door opening, ports, panelling;
        the cold glow through the entry hole (cold = its strength) and the skylight."""
        view = view or InteriorView(f)
        with f.layer() as L:
            self._cabin_walls(L, view, t)
            self._shaft_walls(L, view, t)
        if cold > 0:
            with f.light(blur=26) as A:
                x, z, r = self.HOLE
                c = view.P(x, SHAFT_TOP, z)
                draw.glow_disc(A, c, 900 * view.k(z), COLD, 0.55 * cold)
                draw.glow_disc(A, c, 260 * view.k(z), COLD, 0.8 * cold)
                sx, sz, sr = self.SKYLIGHT
                c2 = view.P(sx, SHAFT_BOT, sz)
                draw.glow_disc(A, c2, 520 * view.k(sz), COLD, 0.30 * cold)
        return view

    def _cabin_walls(self, c, view, t):
        # back wall: panelled, a framed chart hanging askew, a clock, a coat on its hook
        with at_depth(c, view, CABIN_BACK):
            c.rectangle(CABIN_X0, SHAFT_BOT, CABIN_X1 - CABIN_X0, CABIN_BOT - SHAFT_BOT)
            draw.linear(c, (0, SHAFT_BOT), (0, CABIN_BOT), [(0, mix(WOOD_C, INK, 0.2), 1), (0.5, WOOD_C, 1),
                                                          (1, mix(WOOD_C, INK, 0.45), 1)])
            c.fill()
            for i in range(1, 7):
                x = lerp(CABIN_X0, CABIN_X1, i / 7)
                c.rectangle(x - 4, SHAFT_BOT, 8, CABIN_BOT - SHAFT_BOT)
            c.rectangle(CABIN_X1 - 300, SHAFT_BOT, 26, CABIN_BOT - SHAFT_BOT)       # the dado rail
            c.set_source_rgba(*INK, 0.26)
            c.fill()
            c.save()                                               # the chart, on its side
            c.translate(-120, 4180)
            c.rotate(math.radians(-90 + 8))
            round_rect(c, -210, -150, 210, 150, 6)
            round_rect(c, -188, -128, 188, 128, 3, hole=True)
            c.restore()
            solid_circle(c, (250, 4700), 70)                       # a clock
            hole_circle(c, (250, 4700), 54)
            c.set_source_rgb(*mix(INK, WOOD_C, 0.25))
            c.fill()
            # the captain's coat: hung on a hook, still hanging (gravity) along the wall
            c.save()
            c.translate(-250, 4560)
            draw.smooth(c, oriented([(-10, 0), (14, 0), (60, 60), (88, 260), (72, 420), (20, 440), (-30, 430),
                                     (-70, 380), (-62, 200), (-40, 60)]), close=True, tension=0.35)
            c.restore()
            c.set_source_rgb(*mix(INK, WOOD_C, 0.12))
            c.fill()
        # her old ceiling (left), floor (right), port side (bottom), starboard side (top)
        _plane(c, view, [(CABIN_X0, SHAFT_BOT, -NEAR), (CABIN_X0, CABIN_BOT, -NEAR), (CABIN_X0, CABIN_BOT, CABIN_BACK),
                         (CABIN_X0, SHAFT_BOT, CABIN_BACK)], INK, SIDE_C)
        _plane(c, view, [(CABIN_X1, SHAFT_BOT, -NEAR), (CABIN_X1, CABIN_BOT, -NEAR), (CABIN_X1, CABIN_BOT, CABIN_BACK),
                         (CABIN_X1, SHAFT_BOT, CABIN_BACK)], INK, mix(SIDE_C, WOOD_C, 0.5))
        _plane(c, view, [(CABIN_X0, CABIN_BOT, -NEAR), (CABIN_X1, CABIN_BOT, -NEAR), (CABIN_X1, CABIN_BOT, CABIN_BACK),
                         (CABIN_X0, CABIN_BOT, CABIN_BACK)], INK, SIDE_C)
        _plane(c, view, [(CABIN_X0, SHAFT_BOT, -NEAR), (CABIN_X1, SHAFT_BOT, -NEAR), (CABIN_X1, SHAFT_BOT, CABIN_BACK),
                         (CABIN_X0, SHAFT_BOT, CABIN_BACK)], INK, SIDE_C)
        # floorboards on her old floor (the right wall): lines receding
        k0 = view.k(0)
        for i in range(1, 10):
            y = lerp(SHAFT_BOT, CABIN_BOT, i / 10)
            line(c, [view.P(CABIN_X1, y, -NEAR * 0.5), view.P(CABIN_X1, y, CABIN_BACK)], max(5 * k0, 1), INK, 0.55)
        # portholes in her side (now the floor): black ellipses with rims, in perspective
        for (px, pz) in self.PORTHOLES:
            rim = [view.P(px + math.cos(a) * 120, CABIN_BOT, pz + math.sin(a) * 120) for a in
                   [2 * math.pi * i / 24 for i in range(24)]]
            glass = [view.P(px + math.cos(a) * 88, CABIN_BOT, pz + math.sin(a) * 88) for a in
                     [2 * math.pi * i / 24 for i in range(24)]]
            draw.poly(c, oriented(rim))
            draw.poly(c, oriented(glass, cw=False))
            c.set_source_rgb(*mix(INK, SIDE_C, 0.6))
            c.fill()
            draw.poly(c, glass)
            c.set_source_rgb(*INK)
            c.fill()
        # the broken skylight in the ceiling (beyond the shaft's mouth): a ragged hole
        sx, sz, sr = self.SKYLIGHT
        hole = jag([view.P(sx + math.cos(a) * sr * 1.3, SHAFT_BOT, sz + math.sin(a) * sr) for a in
                    [2 * math.pi * i / 16 for i in range(16)]], seed=17, amp=5.0, step=12.0)
        draw.poly(c, hole)
        c.set_source_rgb(*mix(INT_BG, COLD, 0.35))
        c.fill()

    def _shaft_walls(self, c, view, t):
        hw = SHAFT_HW
        with at_depth(c, view, SHAFT_BACK):
            c.rectangle(-hw, SHAFT_TOP, 2 * hw, SHAFT_BOT - SHAFT_TOP)
            draw.linear(c, (0, SHAFT_TOP), (0, SHAFT_BOT), [(0, mix(BACK_C, COLD, 0.22), 1), (0.3, BACK_C, 1),
                                                            (1, mix(BACK_C, INK, 0.35), 1)])
            c.fill()
            for j in range(-1, 8):                                  # strakes and frames
                y = j * 520.0 + 180
                c.rectangle(-hw, y - 5, 2 * hw, 10)
            for x in (-hw * 0.36, hw * 0.36):
                c.rectangle(x - 5, SHAFT_TOP, 10, SHAFT_BOT - SHAFT_TOP)
            c.set_source_rgba(*INK, 0.5)
            c.fill()
            x0, y0, x1, y1 = self.DOOR                               # the door frame on its side
            round_rect(c, x0 - 30, y0 - 30, x1 + 30, y1 + 30, 16)
            round_rect(c, x0, y0, x1, y1, 8, hole=True)
            c.set_source_rgb(*mix(INK, BACK_C, 0.3))
            c.fill()
            round_rect(c, x0, y0, x1, y1, 8)
            c.set_source_rgb(*INK)
            c.fill()
            for px, py in self.PORTS:                                # ports: rims with dogs
                solid_circle(c, (px, py), 96)
                hole_circle(c, (px, py), 68)
                for i in range(6):
                    a = 2 * math.pi * (i + 0.5) / 6
                    solid_circle(c, (px + math.cos(a) * 108, py + math.sin(a) * 108), 14)
            c.set_source_rgb(*mix(INK, BACK_C, 0.3))
            c.fill()
            for px, py in self.PORTS:
                solid_circle(c, (px, py), 68)
            c.set_source_rgb(*INK)
            c.fill()
        for side in (-1, 1):                                           # the side walls (old floor/deckhead)
            x = side * hw
            _plane(c, view, [(x, SHAFT_TOP, -NEAR), (x, SHAFT_BOT, -NEAR), (x, SHAFT_BOT, SHAFT_BACK),
                             (x, SHAFT_TOP, SHAFT_BACK)], INK, SIDE_C)
        # the plating at the top with the cut hole (cold water light beyond)
        x, z, r = self.HOLE
        top = [(-hw, SHAFT_TOP, -NEAR), (hw, SHAFT_TOP, -NEAR), (hw, SHAFT_TOP, SHAFT_BACK), (-hw, SHAFT_TOP, SHAFT_BACK)]
        draw.poly(c, _quad(view, top))
        hole = jag([view.P(x + math.cos(a) * r, SHAFT_TOP, z + math.sin(a) * r) for a in
                    [2 * math.pi * i / 18 for i in range(18)]], seed=23, amp=6.0, step=14.0)
        draw.poly(c, oriented(hole, cw=False))
        c.set_source_rgb(*INK)
        c.fill()
        draw.poly(c, hole)
        c.set_source_rgb(*mix(INT_BG, COLD, 0.55))
        c.fill()
        # the shaft's mouth into the cabin: the cabin ceiling either side of it
        for xa, xb in ((CABIN_X0, -hw), (hw, CABIN_X1)):
            n = [(xa, SHAFT_BOT - 90, -NEAR), (xb, SHAFT_BOT - 90, -NEAR), (xb, SHAFT_BOT, -NEAR), (xa, SHAFT_BOT, -NEAR)]
            prism3(c, view, n, [(p[0], p[1], SHAFT_BACK) for p in n], col=INK)

    # ---------------------------------------------------------------- the lamp
    def draw_lit(self, f, t, view, lamp, aim, spread=17.0, reach=1500.0, power=1.0, blur=2.0, shadows=None,
                 throw=0.32):
        """The helmet lamp's warm pool where the beam meets the walls (additive). Draw it after
        draw() and before draw_mid(), so the props in front read as silhouettes. lamp = (X, Y)
        action-plane position, aim = direction (dx, dy). shadows: polygons (action-plane) of
        things in the beam - their shadows are thrown onto the walls, `throw` further out from
        the lamp (default: the safe, in the cabin). Returns the pool centre."""
        if power <= 0:
            return None
        L = math.hypot(*aim) or 1.0
        ux, uy = aim[0] / L, aim[1] / L
        in_cabin = lamp[1] > view.P(0, SHAFT_BOT, 0)[1]
        xa, xb, zb = (CABIN_X0, CABIN_X1, CABIN_BACK) if in_cabin else (-SHAFT_HW, SHAFT_HW, SHAFT_BACK)
        X0, X1 = view.P(xa, 0, zb * 0.5)[0], view.P(xb, 0, zb * 0.5)[0]
        d = reach
        if ux < -1e-3:
            d = min(d, (X0 - lamp[0]) / ux)
        elif ux > 1e-3:
            d = min(d, (X1 - lamp[0]) / ux)
        d = max(d, 260.0)
        hit = (lamp[0] + ux * d, lamp[1] + uy * d)
        r = 160.0 + d * math.tan(math.radians(spread)) * 1.7
        lit = f.pal.light
        if shadows is None:
            shadows = [self.safe_outline(view)] if in_cabin else []
        mid = (lamp[0] + ux * d * 0.5, lamp[1] + uy * d * 0.5)
        with f.light(blur=blur) as A:
            # only touch the pixels the pool can reach (painting the full frame is slow at scale 1)
            bx0, by0 = min(hit[0] - r, mid[0] - 1.7 * r), min(hit[1] - r, mid[1] - 1.7 * r)
            bx1, by1 = max(hit[0] + r, mid[0] + 1.7 * r), max(hit[1] + r, mid[1] + 1.7 * r)
            A.rectangle(bx0, by0, bx1 - bx0, by1 - by0)
            A.clip()
            A.push_group()
            draw.radial(A, hit, 0, r, [(0, lit, 0.50 * power), (0.4, lit, 0.28 * power), (1, lit, 0.0)])
            A.paint()
            draw.radial(A, mid, 0, r * 1.7, [(0, lit, 0.09 * power), (1, lit, 0.0)])
            A.paint()
            if shadows:
                A.set_operator(cairo.OPERATOR_DEST_OUT)
                for poly in shadows:
                    sh = [(lamp[0] + (x - lamp[0]) * (1 + throw), lamp[1] + (y - lamp[1]) * (1 + throw)) for x, y in poly]
                    draw.poly(A, convex_hull(list(poly) + sh))
                    A.set_source_rgba(0, 0, 0, 0.82)
                    A.fill()
                A.set_operator(cairo.OPERATOR_OVER)
            A.pop_group_to_source()
            A.paint()
        return hit

    # ---------------------------------------------------------------- props in the dark
    def draw_mid(self, f, t, view, door=None, chair=True, safe_door=0.0, safe_lit=0.0, dial_angle=0.0,
                 safe_inside=None, cap=True):
        """Everything standing out of the walls, in ink: pipes and brackets, ribs, cables, the
        door on its side (door = its swing in deg; default door_angle(t)), the turning chair,
        the desk, the hanging lamp, the safe (safe_door 0..1, safe_lit 0..1, dial_angle) and the
        captain's cap. Returns dict(safe = draw_safe's anchors, in action-plane coords)."""
        P = Painter()
        self._mid_items(P, t, door if door is not None else self.door_angle(t), chair, cap)
        out = {}

        def safe_fn(ctx, v):
            x0, y0, z = self.SAFE_AT
            with at_depth(ctx, v, z) as k:
                a = draw_safe(ctx, x0, y0, angle=-90, s=self.SAFE_S, door=safe_door, lit=safe_lit,
                              dial_angle=dial_angle, inside=safe_inside)
            out["safe"] = {key: (v.vx + k * (p[0] - v.vx), v.vy + k * (p[1] - v.vy)) for key, p in a.items()}
        P.add(self.SAFE_AT[2], safe_fn, front=False)
        P.render(f, view, False, bins=((-1e9, 0.0),))
        return out

    def _mid_items(self, P, t, door_deg, chair, cap):
        hw = SHAFT_HW

        def add(z, fn):
            P.add(z, fn, front=False)
        # pipes along the shaft walls, with brackets (the hand holds)
        for (x, z, r) in ((-hw + 58, -140.0, 30.0), (-hw + 52, 170.0, 22.0), (hw - 50, 60.0, 26.0)):
            a3, b3 = (x, SHAFT_TOP, z), (x, SHAFT_BOT - 90, z)
            add(z, lambda c, v, a3=a3, b3=b3, r=r: rod3(c, v, a3, b3, r, r, col=INK))
            xb = -hw if x < 0 else hw
            for _, y in self.holds(SHAFT_TOP + 100, SHAFT_BOT - 200, side=-1 if x < 0 else 1):
                add(z - 1, lambda c, v, x=x, y=y, z=z, xb=xb: rod3(c, v, (xb, y, z), (x, y, z), 18, 18, col=INK))
        # ribs along both walls: flanges sticking into the shaft
        for side in (-1, 1):
            for j in range(6):
                y = j * 760.0 - 200.0
                n = [(side * hw, y, -NEAR), (side * (hw - 64), y, -NEAR), (side * (hw - 64), y + 26, -NEAR),
                     (side * hw, y + 26, -NEAR)]
                add(SHAFT_BACK * 0.5, lambda c, v, n=n: prism3(c, v, n, [(p[0], p[1], SHAFT_BACK) for p in n], col=INK))
        # a cable loom torn from its tray, looping off the right wall, and dangling ends
        def cables(c, v, t=t):
            for i, (a, b, sag, w) in enumerate((((hw - 30, 820), (hw - 40, 1620), 520.0, 15.0),
                                                ((hw - 30, 900), (hw - 70, 2050), 760.0, 11.0))):
                pts = sag_curve(a, b, sag, n=18, wobble=40.0, t=t, seed=90 + i)
                pts = [(x - 260 * math.sin(math.pi * k / 18) * (1 + 0.15 * i), y) for k, (x, y) in enumerate(pts)]
                line(c, [v.P(x, y, -60.0 * (i + 1)) for x, y in pts], w * v.k(-60), INK)
            for i, (x0, y0, L) in enumerate(((-hw + 40, 1650.0, 760.0), (-hw + 120, 3020.0, 420.0))):
                ang = math.radians(sway(t, seed=95 + i, amp=8.0, period=5.0))
                pts = [(x0 + 90 * u + math.sin(ang * u * 2) * L * u, y0 + L * u) for u in [k / 10 for k in range(11)]]
                line(c, [v.P(x, y, -30.0) for x, y in pts], 10 * v.k(-30), INK)
        add(-60.0, cables)
        # the door on its side, hanging from its top hinge, swinging toward the camera
        x0, y0, x1, y1 = self.DOOR
        a = math.radians(door_deg)
        hgt = y1 - y0

        def door_fn(c, v):
            zb = SHAFT_BACK - 6

            def D(x, u):                      # u = 0 at the hinge .. 1 at the free edge
                return v.P(x, y0 + hgt * u * math.cos(a), zb - hgt * u * math.sin(a))
            draw.poly(c, oriented([D(x0, 0), D(x1, 0), D(x1, 1), D(x0, 1)]))
            cx = (x0 + x1) / 2 + 130
            win = [D(cx + math.cos(w) * 54, 0.5 + math.sin(w) * 54 / hgt) for w in [2 * math.pi * i / 16 for i in range(16)]]
            draw.poly(c, oriented(win, cw=False))
            c.set_source_rgb(*INK)
            c.fill()
        add(SHAFT_BACK - 10, door_fn)
        if chair:                                                        # the chair, turning slowly
            def chair_fn(c, v, t=t):
                x, y, z, ang = self.chair_pose(t)
                with at_depth(c, v, z):
                    c.save()
                    c.translate(x, y)
                    c.rotate(math.radians(ang))
                    round_rect(c, -110, -14, 110, 14, 5)
                    round_rect(c, 80, -230, 108, -10, 5)
                    for yy in (-200, -150, -100):
                        round_rect(c, 70, yy, 112, yy + 18, 3)
                    for xx in (-96, 84):
                        round_rect(c, xx, 10, xx + 16, 190, 4)
                    round_rect(c, -90, 120, 90, 134, 3)
                    c.restore()
                    c.set_source_rgb(*INK)
                    c.fill()
            add(self.chair_pose(t)[2], chair_fn)

        # the cabin: the desk bolted to her old floor (the right wall)
        def desk_fn(c, v):
            s0, s1, z0, z1 = 3700.0, 4260.0, 80.0, 620.0
            top_n = [(CABIN_X1 - 300, s0, z0), (CABIN_X1 - 258, s0, z0), (CABIN_X1 - 258, s1, z0), (CABIN_X1 - 300, s1, z0)]
            prism3(c, v, top_n, [(p[0], p[1], z1) for p in top_n], col=INK)
            for yy in (s0 + 30, s1 - 64):
                n = [(CABIN_X1 - 270, yy, z0 + 30), (CABIN_X1, yy, z0 + 30), (CABIN_X1, yy + 34, z0 + 30),
                     (CABIN_X1 - 270, yy + 34, z0 + 30)]
                prism3(c, v, n, [(p[0], p[1], z0 + 64) for p in n], col=INK)
            n = [(CABIN_X1 - 262, s0 + 40, z0 + 90), (CABIN_X1 - 60, s0 + 40, z0 + 90), (CABIN_X1 - 60, s0 + 270, z0 + 90),
                 (CABIN_X1 - 262, s0 + 270, z0 + 90)]
            prism3(c, v, n, [(p[0], p[1], z1) for p in n], col=INK)
        add(80.0, desk_fn)

        def lamp_fn(c, v, t=t):                                         # the hanging lamp
            top, g = self.lamp_pose(t)
            mx, my = self.LAMP_MOUNT
            z = 330.0
            line(c, [v.P(mx, my, z), v.P(top[0], top[1], z)], 22 * v.k(z), INK)
            line(c, [v.P(top[0], top[1], z), v.P(g[0], g[1] - 40, z)], 7 * v.k(z), INK)
            with at_depth(c, v, z):
                c.save()
                c.translate(*g)
                c.rotate(-math.atan2(g[0] - top[0], g[1] - top[1]))
                draw.poly(c, oriented([(-26, -44), (26, -44), (72, 12), (-72, 12)]))
                solid_circle(c, (0, 26), 30)
                c.restore()
                c.set_source_rgb(*INK)
                c.fill()
        add(330.0, lamp_fn)
        if cap:                                                         # the captain's cap, papers
            def cap_fn(c, v):
                with at_depth(c, v, -60.0):
                    draw_captain_cap(c, -300, CABIN_BOT - 4, angle=8, s=1.25)
                    for i in range(4):
                        x = -230 + 120 * i + 40 * hash01(i, 7)
                        c.save()
                        c.translate(x, CABIN_BOT - 6)
                        c.rotate(math.radians(-6 + 12 * hash01(i, 8)))
                        c.rectangle(-55, -7, 110, 7)
                        c.restore()
                    c.set_source_rgb(*INK)
                    c.fill()
            add(-60.0, cap_fn)

    def draw_front(self, f, t, view, blur=10.0):
        """The walls' near edges: thick dark jambs framing the shaft and the cabin, soft."""
        z = -NEAR
        with f.layer(blur=blur) as L:
            for side in (-1, 1):
                x = side * SHAFT_HW
                L.new_sub_path()
                draw.poly(L, [view.P(x, SHAFT_TOP - 3000, z), view.P(x, SHAFT_BOT - 90, z),
                              view.P(x + side * 5000, SHAFT_BOT - 90, z), view.P(x + side * 5000, SHAFT_TOP - 3000, z)])
                xc = CABIN_X1 if side > 0 else CABIN_X0
                draw.poly(L, [view.P(xc, SHAFT_BOT - 90, z), view.P(xc + side * 5000, SHAFT_BOT - 90, z),
                              view.P(xc + side * 5000, CABIN_BOT + 4000, z), view.P(xc, CABIN_BOT + 4000, z)])
            draw.poly(L, [view.P(CABIN_X0 - 5000, CABIN_BOT, z), view.P(CABIN_X1 + 5000, CABIN_BOT, z),
                          view.P(CABIN_X1 + 5000, CABIN_BOT + 4000, z), view.P(CABIN_X0 - 5000, CABIN_BOT + 4000, z)])
            L.set_source_rgb(*INK)
            L.fill()


# ----------------------------------------------------------------------------- s09: the dial
class DialCloseup:
    """The safe's door face filling the frame, the big DIAL at the world origin (radius
    DIAL_R), the three-spoke handle below it, lit from the upper left by the helmet lamp.
    door (0..1) swings the whole door open toward the camera on its left hinge, showing the
    dark inside and the logbook lying in it (s09 end). Its own close lens (LENS) makes the
    door sweep past the camera."""

    DIAL_R = 300.0
    HINGE_X = -820.0
    PLATE = (-820.0, -1250.0, 780.0, 1450.0)          # the door plate (x0, y0, x1, y1)
    HANDLE = (0.0, 820.0, 230.0)
    LENS = 1900.0

    def camera(self, r_screen=260.0, rot=0.0, cx=0.0, cy=0.0):
        """Camera showing the dial centred at screen (540, 960) with on-screen radius r_screen
        (s08 OUT: 260; s09 pushes to ~420)."""
        return Camera(x=cx, y=cy, zoom=r_screen / self.DIAL_R, rot=rot)

    def draw(self, f, t, dial_angle=0.0, lamp=(-0.62, -0.78), power=1.0, door=0.0, book=True):
        """lamp: direction toward the light (screen; upper left by default); power 0..1.
        Returns dict(dial = centre, index = index mark point, number = the number under the
        index mark), in action-plane coords."""
        pal = f.pal
        view = InteriorView(f, lens=self.LENS)
        x0, y0, x1, y1 = self.PLATE
        lx, ly = lamp
        Lp = (lx * 1100.0, ly * 1100.0)
        dark = mix(INK, PAL.mid, 0.07)
        warm = mix(mix(INK, PAL.mid, 0.35), pal.light, 0.58)
        a = math.radians(clamp(door) * 100.0)

        def P3(x, y, z=0.0):
            xr = self.HINGE_X + (x - self.HINGE_X) * math.cos(a)
            zr = z - (x - self.HINGE_X) * math.sin(a)
            return view.P(xr, y, zr)
        with f.layer() as c:
            if door > 0:                     # behind the door: the safe's dark inside, the logbook
                c.rectangle(x0 - 3000, y0 - 3000, x1 - x0 + 6000, y1 - y0 + 6000)
                c.set_source_rgb(*INK)
                c.fill()
                with at_depth(c, view, 900.0):
                    round_rect(c, -700, -980, 700, 1250, 30)
                    c.set_source_rgb(*mix(INK, PAL.mid, 0.08))
                    c.fill()
                    if book:
                        k = clamp(door * 1.6 - 0.35)
                        draw_logbook(c, 40, 160, angle=-4, s=2.8, open_=0.0, light=0.15 + 0.7 * k)
            plate = [P3(x0, y0), P3(x1, y0), P3(x1, y1), P3(x0, y1)]
            draw.poly(c, plate)
            c.set_source_rgb(*dark)
            c.fill()
            c.save()                         # the lamp light on the plate, falling off to the lower right
            draw.poly(c, plate)
            c.clip()
            draw.radial(c, P3(*Lp), 0, 2500.0, [(0, warm, 1.0 * power), (0.3, warm, 0.78 * power),
                                                (0.62, warm, 0.30 * power), (1, warm, 0.0)])
            c.paint()
            # the door seam: a recessed gap just inside the plate's edge, and the hinge knuckles
            seam = [P3(x0 + 26, y0 + 26), P3(x1 - 26, y0 + 26), P3(x1 - 26, y1 - 26), P3(x0 + 26, y1 - 26)]
            line(c, seam + [seam[0]], 10 * view.k(0), INK, 0.7)
            for hy in (y0 + 260, y1 - 460):
                draw.poly(c, [P3(x0 - 40, hy), P3(x0 + 50, hy), P3(x0 + 50, hy + 200), P3(x0 - 40, hy + 200)])
            c.set_source_rgb(*INK)
            c.fill()
            edges = ((x0 + 70, y0 + 70, x1 - 70, y0 + 70), (x0 + 70, y1 - 70, x1 - 70, y1 - 70),
                     (x0 + 70, y0 + 70, x0 + 70, y1 - 70), (x1 - 70, y0 + 70, x1 - 70, y1 - 70))
            k0 = view.k(0)
            for i in range(25):              # rivets: a shadow under each head, then the lit head
                u = i / 24
                for (xa, ya, xb, yb) in edges:
                    p = P3(lerp(xa, xb, u), lerp(ya, yb, u))
                    draw.circle(c, (p[0] + 5 * k0, p[1] + 6 * k0), 13 * k0)
            c.set_source_rgba(*INK, 0.6)
            c.fill()
            for i in range(25):
                u = i / 24
                for (xa, ya, xb, yb) in edges:
                    draw.circle(c, P3(lerp(xa, xb, u), lerp(ya, yb, u)), 12 * k0)
            c.set_source_rgba(*warm, 0.45 * power)
            c.fill()
            draw.poly(c, [P3(-260, -820), P3(260, -820), P3(260, -600), P3(-260, -600)])   # the maker's plate
            c.set_source_rgba(*INK, 0.5)
            c.fill()
            for i in range(3):
                draw.poly(c, [P3(-200, -775 + i * 60), P3(200, -775 + i * 60), P3(200, -755 + i * 60),
                              P3(-200, -755 + i * 60)])
            c.set_source_rgba(*warm, 0.35 * power)
            c.fill()
            c.restore()
            # the dial and the handle, in the plate's (rotating) frame
            dc = P3(0, 0)
            kd = view.k(-(0 - self.HINGE_X) * math.sin(a))
            sq = max(math.cos(a), 0.02)
            c.save()
            c.translate(dc[0], dc[1])
            c.scale(sq * kd, kd)
            face = mix(dark, warm, 0.7 * power)
            res = draw_dial(c, (0, 0), self.DIAL_R, dial_angle=dial_angle, face=face, lit=power)
            # the lamp catches the bezel's upper-left shoulder: a thin warm arc (reads as metal)
            ang0 = math.degrees(math.atan2(ly, lx))
            c.new_path()
            c.arc(0, 0, self.DIAL_R * 1.19, math.radians(ang0 - 38), math.radians(ang0 + 38))
            c.set_line_width(self.DIAL_R * 0.035)
            c.set_source_rgba(*mix(warm, pal.light, 0.5), 0.75 * power)
            c.stroke()
            hx, hy, hr = self.HANDLE
            solid_circle(c, (hx, hy), hr * 0.3)
            for kk in range(3):
                an = math.radians(-90 + 120 * kk + 20)
                draw.capsule(c, (hx, hy), (hx + math.cos(an) * hr, hy + math.sin(an) * hr), 22, 18)
                solid_circle(c, (hx + math.cos(an) * hr, hy + math.sin(an) * hr), 40)
            c.set_source_rgb(*INK)
            c.fill()
            c.restore()
            ix, iy = res["index"]
            out = dict(dial=dc, index=(dc[0] + ix * sq * kd, dc[1] + iy * kd), number=res["number_under_index"])
            if door > 0:                     # the door's thickness at its free edge
                draw.poly(c, oriented([P3(x1, y0), P3(x1, y1), P3(x1, y1, 140.0), P3(x1, y0, 140.0)]))
                c.set_source_rgb(*INK)
                c.fill()
        return out
