"""SALVAGE sets - E. THE MERIDIAN, exterior: a 63 m steamer lying over on her PORT side.

The wreck is a small 2.5D model (hull sections swept along her length, rods, plates) set in
the deep world and projected with sets_deep.View (lens perspective + depth fog), so she
recedes into the murk. Default pose Wreck(heading=0, heel=70, bell_z=150):
  * her length runs straight away from the camera: the STERN (s = 0) sits just behind the
    action plane under the boat (DIVE_X); the bow is lost ~21 000 px deep in the fog;
  * heeled 70 deg to port: her starboard side is the wreck's ROOF (the cut holes, the line
    port), her DECK faces the camera's left: bridge house, funnel stump (the funnel lies
    fallen on the silt), masts with crosstree, shrouds and derricks leaning out over open
    water, lifeboats still in their davits, broken rails standing nearly vertical;
  * her transom faces the camera with her NAME in raised letters (draw_lit reveals it).

Story anchors, all near the action plane, as world (x, y, z) (feed them to view.P / view.k):
  * bell_pose(t) / bell_point(t) / bell_screen(view, t): the ship's BELL hangs on a short
    chain from a bracket arm out of her port quarter, low over the silt (a diver's reach),
    swaying in the current. Crown ~ (26, 8254, 150), bracket end (0, 7925, 150);
  * line_entry() ~ (1887, 5840, 1640): the starboard port (facing up) over the captain's
    cabin where the winch line goes in (S07-S08);
  * holes(): three holes cut from INSIDE in her starboard bilge, z 3240..5040, steel petals
    BENT OUTWARD (up), a torn silhouette on her roof edge against the light above;
  * stern_top(), roof_y(s), transom(), funnel_pose(), bracket_point().

Ship coordinates: s = along her length from the counter (stern) toward the bow (333 px/m),
b = transverse (+ starboard = world UP after the heel), h = height above the keel (+ toward
the deck = world LEFT). Wreck.W(s, b, h) -> world (x, y, z).

S06's close-up of the cut plating is its own little set, HullPlating, with hole_push() for
the camera that pushes into the main hole (cut to S08 when its darkness fills the frame).

    wreck = Wreck()
    world = DeepWorld(wreck=wreck, reef=False)
    f.set_camera(Camera(x=250, y=7250, zoom=0.3))
    deep_backdrop(f, t, glow=[(300, 560, 1250, 1.3)], murk=0.28)
    view = world.draw(f, t, view=View(f, murk=0.28, vp=(540, 1150)), wreck_kw=dict(bell=True))
    ...  action plane: the diver at seabed_y(x), his lamp ...
    wreck.draw_lit(f, t, view, lamp, aim)            # warm pool, rivets, NAME on the transom
    world.draw_front(f, t, view)                      # foreground silt / rocks (z < 0)
    b = wreck.bell_screen(view, t)                    # (b["X"], b["Y"]) = bell crown on screen
"""
import math

import cairo

from engine import draw
from engine.core import clamp, lerp, hash01, fbm1, smoothstep
from engine.frame import Camera

from .sets_common import DIVE_X, SEABED_Y, mix, oriented, jag, riveted_edge, solid_circle, line, sway
from .sets_deep import View, rod3, prism3, convex_hull
from .sets_props import draw_bell, bell_swing


def _ss(a, b, x):
    return smoothstep(a, b, x)


_TEXT = {}


def _text_path(text, face="DejaVu Serif", spacing=0.12):
    """Cached unit-size outline of `text` (letters spaced by `spacing`, baseline at y = 0.36,
    cap height ~0.73). Returns (cairo path, (width, 1.0))."""
    key = (text, face, spacing)
    if key not in _TEXT:
        S = 200.0                                   # lay out big (no hinting artefacts), then scale
        surf = cairo.ImageSurface(cairo.FORMAT_A8, 8, 8)
        c = cairo.Context(surf)
        fo = cairo.FontOptions()
        fo.set_hint_metrics(cairo.HINT_METRICS_OFF)
        fo.set_hint_style(cairo.HINT_STYLE_NONE)
        c.set_font_options(fo)
        c.select_font_face(face, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        c.set_font_size(S)
        x = 0.0
        for ch in text:
            e = c.text_extents(ch)
            c.move_to(x, 0.36 * S)
            c.text_path(ch)
            x += e.x_advance + spacing * S
        big = c.copy_path()
        c.new_path()
        for kind, pts in big:
            q = [v / S for v in pts]
            if kind == cairo.PATH_MOVE_TO:
                c.move_to(*q)
            elif kind == cairo.PATH_LINE_TO:
                c.line_to(*q)
            elif kind == cairo.PATH_CURVE_TO:
                c.curve_to(*q)
            else:
                c.close_path()
        _TEXT[key] = (c.copy_path(), ((x - spacing * S) / S, 1.0))
    return _TEXT[key]


class _MainPass:
    """Painter proxy: items added through it are never treated as front occluders."""

    def __init__(self, P):
        self.P = P

    def add(self, z, fn):
        self.P.add(z, fn, front=False)


class Wreck:
    """The Meridian on the seabed. heading: angle (deg) of her length to the view axis (0 = the
    bow recedes straight away; negative swings the bow to the left); heel: how far she lies
    over to port (deg; 90 = flat on her side); bell_z: distance of the bell's bracket behind
    the action plane; bell_x: world x of the bracket end (default DIVE_X, right under the
    boat's davit). The whole ship is placed from these so the bell is always within reach."""

    D = 2330.0          # keel to main deck
    BEAM = 3500.0
    LEN = 21000.0
    POOP = 250.0
    FOC = 280.0
    BURY = 230.0        # her port side is sunk this deep into the silt

    BELL_SBH = (260.0, -1150.0, 2580.0 + 380.0)   # end of the bell's bracket arm (s, b, h): out of her
                                                  # port quarter, low over the silt (a diver's reach)
    BELL_SCALE = 1.8                              # the bell prop is drawn at this size (k * 1.8)
    BELL_DROP = 330.0                             # chain from the bracket end to the bell's crown
    LINE_SH = (1750.0, 1900.0)                    # the starboard port (facing up) over the captain's cabin
    HOLES = ((3350.0, 560.0, 150.0), (4250.0, 760.0, 185.0), (5150.0, 600.0, 130.0))   # (s, h, radius)

    def __init__(self, heading=0.0, bell_z=150.0, bell_x=None, heel=70.0):
        th = math.radians(heading)
        ph = math.radians(heel)
        self.heading, self.heel = heading, heel
        self.Lx, self.Lz = math.sin(th), math.cos(th)
        Hx, Hz = -math.cos(th), math.sin(th)          # her port side's outward direction (level)
        cp, sp = math.cos(ph), math.sin(ph)
        # transverse (+ starboard) and vertical (+ toward the deck) axes after heeling to port
        self.Tx, self.Ty, self.Tz = -cp * Hx, -sp, -cp * Hz
        self.Vx, self.Vy, self.Vz = sp * Hx, -cp, sp * Hz
        self.ycl, self.ox, self.oz = 0.0, 0.0, 0.0
        # rest her on the silt: the lowest point of her midship section sits BURY deep
        low = max(self.W(9000.0, b, h)[1] for b, h in self.section(9000.0))
        self.ycl = SEABED_Y + self.BURY - low
        bx = DIVE_X if bell_x is None else bell_x
        x_b = self.W(*self.BELL_SBH)[0]
        self.ox = bx - x_b
        self.oz = bell_z - self.W(*self.BELL_SBH)[2]
        self._items_cache = None

    # ---------------------------------------------------------------- frame
    def W(self, s, b, h):
        """World (x, y, z) of ship point (s, b, h)."""
        return (self.ox + s * self.Lx + b * self.Tx + h * self.Vx,
                self.ycl + b * self.Ty + h * self.Vy,
                self.oz + s * self.Lz + b * self.Tz + h * self.Vz)

    def deck_h(self, s):
        if s < 3200:
            return self.D + self.POOP
        if s > 18300:
            return self.D + self.FOC
        return self.D

    def hb_deck(self, s):
        """Half-breadth at deck level along her length."""
        if s < 4200:
            return 1250 + 500 * _ss(0, 4000, s) ** 0.8
        if s > 16500:
            return max(60.0, 1750 * (1 - ((s - 16500) / 4600.0) ** 1.6))
        return 1750.0

    def _shape_params(self, s):
        """(h_bottom, w0 = bottom width fraction, p = bilge fullness) at station s."""
        if s < 700:                                   # the counter, overhanging the rudder
            return lerp(1180, 980, s / 700.0), 0.42, 1.6
        if s < 4200:                                  # the run: a narrow V aft fills out
            u = _ss(700, 4200, s)
            return 0.0, lerp(0.05, 0.74, u ** 1.3), lerp(1.7, 6.0, u)
        if s > 15000:                                 # the entrance and the forefoot
            u = _ss(15000, 21000, s)
            hb = 0.0 if s < 20000 else (s - 20000) / 1000.0 * 1700
            return hb, lerp(0.74, 0.03, u ** 0.8), lerp(6.0, 1.5, u)
        return 0.0, 0.74, 6.0

    def hb_at(self, s, h):
        """Half-breadth of the hull plating at station s, height h."""
        h0, w0, p = self._shape_params(s)
        dh = self.deck_h(s)
        u = clamp((h - h0) / max(dh - h0, 1.0))
        return self.hb_deck(s) * (w0 + (1 - w0) * (1 - (1 - u) ** p))

    def section(self, s):
        """Convex hull section at station s as [(b, h)], keel to deck: narrow 'wine glass' aft,
        a box with tight bilges amidships, a sharp vee forward."""
        h0, w0, p = self._shape_params(s)
        dh = self.deck_h(s)
        hd = self.hb_deck(s)
        right = []
        for u in (0.0, 0.02, 0.06, 0.12, 0.2, 0.3, 0.45, 0.65, 0.85, 1.0):
            h = lerp(h0, dh, u)
            right.append((hd * (w0 + (1 - w0) * (1 - (1 - u) ** p)), h))
        left = [(-b, h) for b, h in reversed(right)]
        return right + [(0.0, dh + 60.0)] + left

    def sec3(self, s):
        return [self.W(s, b, h) for b, h in self.section(s)]

    # ---------------------------------------------------------------- anchors
    def bracket_point(self):
        """World (x, y, z) of the end of the bell's bracket arm (the chain hangs from here)."""
        return self.W(*self.BELL_SBH)

    def bell_pose(self, t=0.0, bell_angle=None, clapper=None, seed=1):
        """The bell hanging on its short chain under the bracket, swaying in the current:
        dict(pivot = bracket end (x, y, z), crown = top of the bell (x, y, z), angle, clapper)."""
        px, py, pz = self.bracket_point()
        if bell_angle is None:
            ang, cl = bell_swing(t, seed=seed, amp=6.0, period=5.4)
        else:
            ang, cl = bell_angle, (0.0 if clapper is None else clapper)
        a = math.radians(ang)
        crown = (px - math.sin(a) * self.BELL_DROP, py + math.cos(a) * self.BELL_DROP, pz)
        return dict(pivot=(px, py, pz), crown=crown, angle=ang, clapper=cl)

    def bell_point(self, t=0.0):
        """World (x, y, z) of the bell's crown this frame (where a line gets tied)."""
        return self.bell_pose(t)["crown"]

    def bell_screen(self, view, t=0.0, bell_angle=None, clapper=None):
        """The bell this frame in action-plane coords: dict(X, Y = crown, s = prop scale for
        draw_bell, k = depth scale, angle, clapper, pivot = (X, Y) of the bracket end)."""
        bp = self.bell_pose(t, bell_angle, clapper)
        x, y, z = bp["crown"]
        X, Y = view.P(x, y, z)
        k = view.k(z)
        return dict(X=X, Y=Y, k=k, s=k * self.BELL_SCALE, angle=bp["angle"], clapper=bp["clapper"],
                    pivot=view.Pp(bp["pivot"]))

    def line_entry(self):
        """World (x, y, z) of the starboard port (now facing up) where the winch line enters
        the captain's deckhouse."""
        s, h = self.LINE_SH
        return self.W(s, self.hb_at(s, h), h)

    def holes(self):
        """[(world centre (x, y, z), radius)] of the three cut holes (petals outward = up)."""
        out = []
        for s, h, r in self.HOLES:
            b = self.hb_at(s, h)
            out.append((self.W(s, b, h), r))
        return out

    def stern_top(self):
        """World point at the top of the stern (starboard poop rail corner)."""
        return self.W(80.0, 1200.0, self.D + self.POOP)

    def roof_y(self, s):
        """World y of the wreck's roof (her starboard side) at station s."""
        return self.ycl - self.hb_deck(s)

    # ---------------------------------------------------------------- items
    def add_items(self, P, t, bell=True, bell_angle=None, clapper=None, petals=True, lines=True,
                  detail=1.0):
        """Add all wreck silhouette items to a sets_deep.Painter (all in the main pass, even the
        parts that come in front of the action plane)."""
        W_ = self.W
        P = _MainPass(P)
        # hull body: swept between stations
        st = [0, 300, 600, 1100, 1800, 2600, 3199, 3201, 4300, 6000, 8000, 10000, 12000, 14000, 15500,
              16800, 18299, 18301, 19300, 20100, 20700, 21000]
        for a, b in zip(st, st[1:]):
            near, far = self.sec3(a), self.sec3(b)
            zm = (sum(p[2] for p in near) + sum(p[2] for p in far)) / (len(near) + len(far)) + 300
            P.add(zm, lambda ctx, view, near=near, far=far: prism3(ctx, view, near, far))
        # rudder, sternpost shoe, propeller
        def box(s0, s1, b0, b1, h0, h1):
            n = [W_(s0, b0, h0), W_(s0, b1, h0), W_(s0, b1, h1), W_(s0, b0, h1)]
            f_ = [W_(s1, b0, h0), W_(s1, b1, h0), W_(s1, b1, h1), W_(s1, b0, h1)]
            return n, f_
        for (s0, s1, b0, b1, h0, h1) in ((150, 520, -48, 48, 70, 1150), (480, 900, -70, 70, 0, 110)):
            n, f_ = box(s0, s1, b0, b1, h0, h1)
            zm = sum(p[2] for p in n + f_) / 8
            P.add(zm - 50, lambda ctx, view, n=n, f_=f_: prism3(ctx, view, n, f_))
        hub = (650.0, 0.0, 640.0)
        R = 700.0
        def prop(ctx, view, rot=24.0):
            for i in range(4):
                a = math.radians(rot + 90 * i)
                ca, sa = math.cos(a), math.sin(a)
                blade = []
                for u, w in ((0.12, 90), (0.32, 200), (0.58, 235), (0.8, 190), (0.95, 100), (1.0, 20)):
                    blade.append((ca * R * u - sa * w, sa * R * u + ca * w))
                for u, w in ((0.99, -40), (0.9, -95), (0.62, -130), (0.35, -110), (0.12, -80)):
                    blade.append((ca * R * u - sa * w, sa * R * u + ca * w))
                pp = [view.Pp(W_(hub[0], hub[1] + bb, hub[2] + hh)) for bb, hh in blade]
                draw.smooth(ctx, oriented(pp), close=True, tension=0.45)
            c = view.Pp(W_(*hub))
            k = view.k(W_(*hub)[2])
            draw.circle(ctx, c, 150 * k)
            ctx.set_source_rgb(*view.tone(W_(*hub)[2], c[1]))
            ctx.fill()
        P.add(W_(*hub)[2] - 80, prop)

        D, PO = self.D, self.POOP
        dp = D + PO
        # poop: companion house + skylight over the captain's cabin (which is under the poop deck)
        for (s0, s1, b0, b1, h0, h1) in ((1350, 2350, -520, 520, dp, dp + 520), (1600, 2100, -260, 260, dp + 520, dp + 640)):
            n, f_ = box(s0, s1, b0, b1, h0, h1)
            zm = sum(p[2] for p in n + f_) / 8
            P.add(zm - 200, lambda ctx, view, n=n, f_=f_: prism3(ctx, view, n, f_))
        # stern rail (now standing on end): a few stanchions + two rails across the poop, bent and
        # broken in places (a regular rail reads as a ladder)
        def rail_across(s, b0, b1, h0, step, r=15.0, seed=5):
            items = []
            nb = max(2, int((b1 - b0) / step))
            tops = []
            for i in range(nb + 1):
                bb = lerp(b0, b1, i / nb)
                lean = 120 * (hash01(seed, i) - 0.5)
                top = W_(s - lean, bb, h0 + 330)
                tops.append(top)
                if hash01(seed, i, 1) > 0.18:
                    items.append((W_(s, bb, h0), top, r, r * 0.8))
            for i in range(nb):
                if hash01(seed, i, 2) > 0.3:
                    items.append((tops[i], tops[i + 1], r * 0.8, r * 0.8))
            return items
        rails = rail_across(90, -1180, 1180, dp, 520)
        # starboard rails along the deck edge (a receding comb on the wreck's upper edge)
        def rail_along(s0, s1, h0, step, r=15.0, seed=7):
            items = []
            n = max(2, int((s1 - s0) / step))
            prev = None
            for i in range(n + 1):
                s = lerp(s0, s1, i / n)
                bb = self.hb_deck(s) - 30
                bot, top = W_(s, bb, h0), W_(s, bb, h0 + 330)
                if hash01(seed, i) > 0.12:
                    items.append((bot, top, r, r * 0.8))
                if prev is not None and hash01(seed, i, 1) > 0.15:
                    items.append((prev, top, r * 0.8, r * 0.8))
                prev = top
            return items
        rails += rail_along(200, 3150, dp, 330)
        rails += rail_along(3260, 18200, D, 520)
        for a3, b3, r0, r1 in rails:
            P.add((a3[2] + b3[2]) / 2 - 60, lambda ctx, view, a3=a3, b3=b3, r0=r0, r1=r1: rod3(ctx, view, a3, b3, r0, r1))
        # ensign staff at the stern, bent
        a3, b3, c3 = W_(60, 0, dp), W_(60, 0, dp + 900), W_(60, -260, dp + 1500)
        P.add(a3[2] - 100, lambda ctx, view, a3=a3, b3=b3, c3=c3: (rod3(ctx, view, a3, b3, 30, 24),
                                                                   rod3(ctx, view, b3, c3, 24, 16)))
        # the bell's bracket: an arm out of her port quarter (now nearly level, low over the silt),
        # a brace, and the bell on a short chain (bell=False: the empty bracket, a broken chain end)
        s_, b_, h_ = self.BELL_SBH
        br0, br1 = W_(s_, b_, dp - 10), W_(s_, b_, h_ + 20)
        brace0, brace1 = W_(s_, b_ + 360, dp - 10), W_(s_, b_, dp + 280)
        bs = self.BELL_SCALE
        bp = self.bell_pose(t, bell_angle, clapper)

        def bracket(ctx, view, bp=bp):
            rod3(ctx, view, br0, br1, 34, 28)
            rod3(ctx, view, brace0, brace1, 20, 18)
            z = bp["pivot"][2]
            k = view.k(z)
            A = view.Pp(bp["pivot"])
            col = view.tone(z, A[1])
            draw.circle(ctx, A, 30 * k)                         # the shackle eye
            ctx.set_source_rgb(*col)
            ctx.fill()
            if bell:
                C = view.Pp(bp["crown"])
                line(ctx, [A, C], max(11 * k, 0.8), col)
                draw_bell(ctx, C[0], C[1], angle=bp["angle"], clapper=bp["clapper"], s=k * bs, color=col, yoke=False)
            else:
                C = (A[0] + 0.25 * (view.Pp(bp["crown"])[0] - A[0]) + 6 * k, A[1] + 110 * k)
                line(ctx, [A, C], max(11 * k, 0.8), col)
        P.add(br1[2] - 150, bracket)
        # mainmast (broken), crosstree, slack shrouds, hanging derricks
        sm = 4700.0
        m0, m1 = W_(sm, 0, D), W_(sm, 0, D + 3900)
        cr0, cr1 = W_(sm, -680, D + 3250), W_(sm, 680, D + 3250)
        def mainmast(ctx, view):
            rod3(ctx, view, m0, m1, 64, 46)
            rod3(ctx, view, cr0, cr1, 26, 26)
            # jagged break at the top
            A = view.Pp(m1)
            k = view.k(m1[2])
            ux, uy = view.Pp(W_(sm, 0, D + 3800))
            d = (A[0] - ux, A[1] - uy)
            L = math.hypot(*d) or 1.0
            nx, ny = d[0] / L, d[1] / L
            px, py = -ny, nx
            w = 46 * k
            pts = [(A[0] - px * w, A[1] - py * w), (A[0] + nx * 40 * k - px * w * 0.4, A[1] + ny * 40 * k - py * w * 0.4),
                   (A[0] + nx * 12 * k, A[1] + ny * 12 * k), (A[0] + nx * 64 * k + px * w * 0.3, A[1] + ny * 64 * k + py * w * 0.3),
                   (A[0] + px * w, A[1] + py * w)]
            draw.poly(ctx, oriented(pts))
            ctx.set_source_rgb(*view.tone(m1[2], A[1]))
            ctx.fill()
        P.add((m0[2] + m1[2]) / 2 - 300, mainmast)
        if lines:
            for i, (bb, ss) in enumerate(((1700, sm - 380), (1700, sm + 380), (1650, sm + 900))):
                a3 = W_(sm, 40, D + 3150)
                b3 = W_(ss, bb, D + 40)
                def shroud(ctx, view, a3=a3, b3=b3, i=i):
                    pts = []
                    for j in range(13):
                        u = j / 12
                        x = lerp(a3[0], b3[0], u)
                        y = lerp(a3[1], b3[1], u) + 520 * 4 * u * (1 - u) + 30 * sway(t + u * 2, seed=40 + i, amp=1)
                        z = lerp(a3[2], b3[2], u)
                        pts.append(view.P(x, y, z))
                    line(ctx, pts, max(9 * view.k(a3[2]), 0.8), view.tone((a3[2] + b3[2]) / 2, pts[6][1]))
                P.add((a3[2] + b3[2]) / 2 - 200, shroud)
        for i, (dx, dy, dz) in enumerate(((-700, 2300, -500), (300, 2500, -900))):
            a3 = W_(sm + 150, 160 * (1 - 2 * i), D + 380)
            b3 = (a3[0] + dx, a3[1] + dy, a3[2] + dz)
            P.add((a3[2] + b3[2]) / 2 - 250, lambda ctx, view, a3=a3, b3=b3: rod3(ctx, view, a3, b3, 40, 26))
        # cargo hatch coaming
        n, f_ = box(6000, 7300, -850, 850, D, D + 230)
        P.add(sum(p[2] for p in n + f_) / 8 - 100, lambda ctx, view, n=n, f_=f_: prism3(ctx, view, n, f_))
        # midship house, bridge, wheelhouse (with see-through windows), wings
        for (s0, s1, b0, b1, h0, h1) in ((7500, 11300, -1450, 1450, D, D + 820), (9100, 11300, -1150, 1150, D + 820, D + 1560),
                                          (11000, 11250, -1760, 1760, D + 1560, D + 1630)):
            n, f_ = box(s0, s1, b0, b1, h0, h1)
            P.add(sum(p[2] for p in n + f_) / 8 - 120, lambda ctx, view, n=n, f_=f_: prism3(ctx, view, n, f_))
        n, f_ = box(10300, 11150, -760, 760, D + 1560, D + 2250)
        wins = [((10300, bb - 150, D + 1830), (10300, bb + 150, D + 2120)) for bb in (-480, 0, 480)]
        def wheelhouse(ctx, view, n=n, f_=f_):
            pn = [view.Pp(p) for p in n]
            pf = [view.Pp(p) for p in f_]
            hull = convex_hull(pn + pf)
            draw.poly(ctx, hull)
            for (s0, b0, h0), (s1, b1, h1) in wins:
                q = [view.Pp(W_(s0, b0, h0)), view.Pp(W_(s0, b1, h0)), view.Pp(W_(s0, b1, h1)), view.Pp(W_(s0, b0, h1))]
                draw.poly(ctx, oriented(q, cw=False))
            zn = sum(p[2] for p in n) / 4
            ctx.set_source_rgb(*view.tone(zn, sum(p[1] for p in pn) / 4))
            ctx.fill()
        P.add(sum(p[2] for p in n + f_) / 8 - 140, wheelhouse)
        for bb in (-1700, 1700):
            for (s0, s1) in ((11050, 11250),):
                a3, b3 = W_(11120, bb, D + 1630), W_(11120, bb, D + 1950)
                P.add(a3[2] - 160, lambda ctx, view, a3=a3, b3=b3: rod3(ctx, view, a3, b3, 22, 20))
            a3, b3 = W_(11120, bb, D + 1950), W_(11120, bb * 0.5, D + 1950)
            P.add(a3[2] - 160, lambda ctx, view, a3=a3, b3=b3: rod3(ctx, view, a3, b3, 18, 18))
        # funnel stump (broken), ventilator cowls
        def cyl(s_c, b_c, h0, h1, r, n=14):
            lo = [W_(s_c + math.cos(2 * math.pi * i / n) * r, b_c + math.sin(2 * math.pi * i / n) * r, h0) for i in range(n)]
            hi = [W_(s_c + math.cos(2 * math.pi * i / n) * r, b_c + math.sin(2 * math.pi * i / n) * r, h1) for i in range(n)]
            return lo, hi
        lo, hi = cyl(8600, 0, D + 820, D + 1250, 470)          # the stump, torn off
        hi = [(x + 40 * (hash01(i, 3) - 0.5), y + 60 * (hash01(i, 4) - 0.5), z) for i, (x, y, z) in enumerate(hi)]
        P.add(sum(p[2] for p in lo + hi) / (2 * len(lo)) - 160, lambda ctx, view, lo=lo, hi=hi: prism3(ctx, view, lo, hi))
        for item in self._fallen_funnel():
            P.add(*item)
        for (s_c, b_c) in ((7900, 760), (7900, -760), (11550, 600)):
            lo, hi = cyl(s_c, b_c, D + 820 if s_c < 11300 else D, D + 1520, 110, 10)
            mouth = [W_(s_c - 40, b_c + math.cos(2 * math.pi * i / 16) * 230, D + 1660 + math.sin(2 * math.pi * i / 16) * 230)
                     for i in range(16)]
            back = [W_(s_c + 120, b_c + math.cos(2 * math.pi * i / 16) * 150, D + 1600 + math.sin(2 * math.pi * i / 16) * 150)
                    for i in range(16)]
            zz = sum(p[2] for p in hi) / len(hi) - 170
            P.add(zz, lambda ctx, view, lo=lo, hi=hi, mouth=mouth, back=back: (prism3(ctx, view, lo, hi),
                                                                               prism3(ctx, view, mouth, back)))
        # lifeboats in their davits (starboard on the roof, port half in the silt)
        for side in (1, -1):
            secs = []
            for s, wfac in ((7800, 0.05), (8200, 0.8), (9700, 0.8), (10100, 0.05)):
                bc = side * 1420
                hw = 340 * wfac + 20
                secs.append([W_(s, bc - hw, D + 860), W_(s, bc + hw, D + 860), W_(s, bc + hw * 1.05, D + 1180),
                             W_(s, bc - hw * 1.05, D + 1180)])
            for a, b in zip(secs, secs[1:]):
                P.add(sum(p[2] for p in a + b) / 8 - 180, lambda ctx, view, a=a, b=b: prism3(ctx, view, a, b))
            for s in (8050, 9850):
                p0 = W_(s, side * 1250, D + 820)
                p1 = W_(s, side * 1330, D + 1450)
                p2 = W_(s, side * 1600, D + 1700)
                p3 = W_(s, side * 1900, D + 1640)
                def davit(ctx, view, p0=p0, p1=p1, p2=p2, p3=p3):
                    rod3(ctx, view, p0, p1, 34, 30)
                    rod3(ctx, view, p1, p2, 30, 26)
                    rod3(ctx, view, p2, p3, 26, 22)
                    if lines:
                        A, B = view.Pp(p3), view.Pp(W_(s, side * 1500, D + 1180))
                        line(ctx, [A, B], max(6 * view.k(p3[2]), 0.7), view.tone(p3[2], A[1]))
                P.add(p1[2] - 200, davit)
        # foremast, crosstree
        sf = 16900.0
        f0, f1 = W_(sf, 0, D), W_(sf, 0, D + 6000)
        c0, c1 = W_(sf, -820, D + 4600), W_(sf, 820, D + 4600)
        P.add((f0[2] + f1[2]) / 2 - 300, lambda ctx, view, f0=f0, f1=f1, c0=c0, c1=c1: (rod3(ctx, view, f0, f1, 70, 38),
                                                                                       rod3(ctx, view, c0, c1, 28, 28)))
        # the cut holes: steel petals bent OUTWARD (up, off her starboard plating)
        if petals:
            for (c3, r), (s, h, _) in zip(self.holes(), self.HOLES):
                P.add(c3[2] - 120, self._petals_item(s, h, r))

    def _petals_item(self, s0, h0, r):
        W_ = self.W
        b0 = self.hb_at(s0, h0)
        n = 8
        petals = []
        for i in range(n):
            a = 2 * math.pi * (i + 0.37 * hash01(int(s0), i)) / n
            ca, sa = math.cos(a), math.sin(a)
            L = r * (1.0 + 0.9 * hash01(int(s0), i, 2))
            bend = 0.55 + 0.4 * hash01(int(s0), i, 3)          # how far it curls outward
            wid = r * 0.75
            # base on the rim (two points), tip out along the plate and up (+b)
            ba = (s0 + math.cos(a - 0.38) * r, h0 + math.sin(a - 0.38) * r)
            bb = (s0 + math.cos(a + 0.38) * r, h0 + math.sin(a + 0.38) * r)
            mid = (s0 + ca * (r + L * 0.45 * (1 - bend * 0.5)), h0 + sa * (r + L * 0.45 * (1 - bend * 0.5)))
            tip = (s0 + ca * (r + L * 0.55 * (1 - bend)), h0 + sa * (r + L * 0.55 * (1 - bend)))
            pts = [W_(ba[0], b0, ba[1]), W_(mid[0] - sa * wid * 0.3, b0 + L * 0.5 * bend, mid[1] + ca * wid * 0.3),
                   W_(tip[0], b0 + L * bend, tip[1]), W_(mid[0] + sa * wid * 0.3, b0 + L * 0.5 * bend, mid[1] - ca * wid * 0.3),
                   W_(bb[0], b0, bb[1])]
            petals.append(pts)
        rim = [W_(s0 + math.cos(2 * math.pi * i / 16) * r * 1.05, b0 + 6, h0 + math.sin(2 * math.pi * i / 16) * r * 1.05)
               for i in range(16)]

        def fn(ctx, view):
            zc = sum(p[2] for p in rim) / len(rim)
            for pts in petals:
                pp = [view.Pp(p) for p in pts]
                draw.poly(ctx, oriented(pp))
            ys = [view.Pp(p)[1] for p in rim]
            ctx.set_source_rgb(*view.tone(zc, sum(ys) / len(ys)))
            ctx.fill()
        return fn

    def funnel_pose(self):
        """(base, mouth) world points of the fallen funnel's axis: it broke off the midship house
        and lies across the silt beside her, its open mouth toward the stern."""
        bx, by, bz = self.W(8600, 0, self.D + 1300)
        from .sets_deep import seabed_y as _sy
        base = (bx - 250, _sy(bx - 250, bz - 300) - 520, bz - 300)
        mx = bx - 1900
        mouth = (mx, _sy(mx, bz - 2000) - 440, bz - 2000)
        return base, mouth

    def _fallen_funnel(self, R=470.0, n=16):
        base, mouth = self.funnel_pose()
        ax = [mouth[i] - base[i] for i in range(3)]
        L = math.sqrt(sum(v * v for v in ax))
        u = [v / L for v in ax]
        # a frame around the axis: e1 horizontal-ish, e2 = u x e1
        e1 = (-u[2], 0.0, u[0])
        n1 = math.hypot(e1[0], e1[2]) or 1.0
        e1 = (e1[0] / n1, 0.0, e1[2] / n1)
        e2 = (u[1] * e1[2] - u[2] * e1[1], u[2] * e1[0] - u[0] * e1[2], u[0] * e1[1] - u[1] * e1[0])

        def ring(c, r, wob=0.0, seed=0):
            out = []
            for i in range(n):
                a = 2 * math.pi * i / n
                rr = r * (1 + wob * (hash01(seed, i) - 0.5))
                out.append(tuple(c[q] + rr * (math.cos(a) * e1[q] + math.sin(a) * e2[q]) for q in range(3)))
            return out
        rings = [ring(base, R * 1.02, 0.12, 3), ring(tuple(base[q] + ax[q] * 0.5 for q in range(3)), R),
                 ring(mouth, R * 1.04, 0.05, 4)]
        items = []
        for r0, r1 in zip(rings, rings[1:]):
            zm = sum(p[2] for p in r0 + r1) / (2 * n)
            items.append((zm, lambda ctx, view, r0=r0, r1=r1: prism3(ctx, view, r0, r1)))
        # its mouth: the open black end with a thin rim (reads as a pipe, not a log)
        inner = ring(tuple(mouth[q] - u[q] * 30 for q in range(3)), R * 0.86)

        def mouth_fn(ctx, view, rim=rings[-1], inner=inner):
            pr = [view.Pp(p) for p in rim]
            pi = [view.Pp(p) for p in inner]
            draw.poly(ctx, oriented(pr))
            draw.poly(ctx, oriented(pi, cw=False))
            z = sum(p[2] for p in rim) / n
            ctx.set_source_rgb(*view.tone(z, sum(p[1] for p in pr) / n))
            ctx.fill()
            draw.poly(ctx, pi)
            ctx.set_source_rgb(*view.tone(z + 2500, sum(p[1] for p in pi) / n))
            ctx.fill()
        items.append((mouth[2] - 40, mouth_fn))
        return items

    # ---------------------------------------------------------------- the beam on her stern
    NAME = "MERIDIAN"

    def transom(self):
        """Her stern plate (the transom, s = 0) as world points, for lighting and decals."""
        return self.sec3(0.0)

    def draw_lit(self, f, t, view, lamp, aim, spread=17.0, length=3400.0, power=1.0, name=True, blur=1.2):
        """What the helmet lamp reveals on her stern: a warm pool on the transom with plate seams,
        rivet rows and the raised letters of her NAME (running up the plate - she is on her side).
        lamp = (X, Y) action-plane position of the lamp, aim = direction (dx, dy). Draw it after
        the wreck (it is additive light); the beam itself is atmos' job."""
        W_ = self.W
        L = math.hypot(*aim) or 1.0
        ux, uy = aim[0] / L, aim[1] / L
        sec = self.section(0.0)
        poly = [view.Pp(W_(0.0, b, h)) for b, h in sec]
        cx = sum(p[0] for p in poly) / len(poly)
        cy = sum(p[1] for p in poly) / len(poly)
        d = (cx - lamp[0]) * ux + (cy - lamp[1]) * uy
        if d <= 0 or power <= 0:
            return
        hit = (lamp[0] + ux * d, lamp[1] + uy * d)
        r = max(d * math.tan(math.radians(spread)) * 1.25, 60.0)
        fall = clamp(1.0 - d / length) ** 0.7 * power
        if fall <= 0.01:
            return
        lit = f.pal.light
        k = view.k(W_(0, 0, 2000)[2])
        h0, _, _ = self._shape_params(0.0)
        dh = self.deck_h(0.0)

        def surf(b, h):
            return view.Pp(W_(0.0, b, h))

        with f.light(blur=blur) as A:
            draw.poly(A, poly)                     # clip first: the group then only spans the transom
            A.clip()
            A.push_group()
            draw.radial(A, hit, 0, r, [(0, lit, 0.62 * fall), (0.45, lit, 0.34 * fall), (1, lit, 0.0)])
            A.paint()
            A.set_operator(cairo.OPERATOR_DEST_OUT)
            # plate seams (dark lines) - butts across, strakes along
            for bb in (-880.0, -300.0, 300.0, 880.0):
                hs = [lerp(h0, dh, i / 8) for i in range(9)]
                pts = [surf(bb + 25 * math.sin(h / 400.0), h) for h in hs]
                line(A, pts, max(7 * k, 1.0), (0, 0, 0), 0.75)
            for hh in (lerp(h0, dh, 0.36), lerp(h0, dh, 0.7)):
                pts = [surf(lerp(-1250, 1250, i / 12), hh) for i in range(13)]
                line(A, pts, max(7 * k, 1.0), (0, 0, 0), 0.75)
            if name:
                self._name_path(A, view, offset=(5 * k, 6 * k))
                A.set_source_rgba(0, 0, 0, 0.85)
                A.fill()
            A.set_operator(cairo.OPERATOR_OVER)
            A.pop_group_to_source()
            A.paint()
            # raised things catch the light: rivet heads and the letters (still clipped to the plate)
            src = [(0, lit, 0.95 * fall), (0.5, lit, 0.55 * fall), (1, lit, 0.0)]
            for bb in (-880.0, -300.0, 300.0, 880.0):
                for i in range(18):
                    h = lerp(h0 + 40, dh - 40, i / 17)
                    for side in (-1, 1):
                        draw.circle(A, surf(bb + 25 * math.sin(h / 400.0) + side * 30, h), max(7 * k, 0.7))
            for hh in (lerp(h0, dh, 0.36), lerp(h0, dh, 0.7)):
                for i in range(31):
                    draw.circle(A, surf(lerp(-1200, 1200, i / 30), hh + 28), max(7 * k, 0.7))
            draw.radial(A, hit, 0, r, src)
            A.fill()
            if name:
                self._name_path(A, view)
                draw.radial(A, hit, 0, r * 1.1, [(0, lit, 1.0 * fall), (0.55, lit, 0.6 * fall), (1, lit, 0.0)])
                A.fill()
            A.reset_clip()

    def _name_path(self, ctx, view, offset=(0.0, 0.0)):
        """Append the raised name's outline (on the transom, reading port to starboard = up)."""
        path, (w, hgt) = _text_path(self.NAME)
        h_c = self.deck_h(0.0) - 330.0
        size = 210.0
        b0 = -w * size / 2
        O = view.Pp(self.W(0.0, b0, h_c))
        Ub = view.Pp(self.W(0.0, b0 + 1.0, h_c))
        Uh = view.Pp(self.W(0.0, b0, h_c + 1.0))
        # text x -> along +b, text y (down) -> along -h
        xx, yx = (Ub[0] - O[0]) * size, (Ub[1] - O[1]) * size
        xy, yy = -(Uh[0] - O[0]) * size, -(Uh[1] - O[1]) * size
        ctx.save()
        ctx.transform(cairo.Matrix(xx, yx, xy, yy, O[0] + offset[0], O[1] + offset[1]))
        ctx.new_path()
        ctx.append_path(path)
        ctx.restore()

    def draw(self, f, t, view=None, **kw):
        """Draw the wreck alone (no seabed) - e.g. over a custom backdrop."""
        from .sets_deep import Painter
        view = view or View(f)
        P = Painter()
        self.add_items(P, t, **kw)
        P.render(f, view)
        return view


def _ring_mask(cx, cy, r0, r1):
    """A radial alpha pattern: 1 at r0 fading to 0 at r1 (for masking a bulge's shading)."""
    g = cairo.RadialGradient(cx, cy, r0, cx, cy, r1)
    g.add_color_stop_rgba(0, 0, 0, 0, 1.0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.0)
    return g


# ----------------------------------------------------------------------------- S06 hull plating close-up
class HullPlating:
    """S06: her starboard bilge plating seen face on, close (a separate little world: the
    plating fills the frame; origin at the centre of the main hole). Lit by the diver's
    lamp, three holes cut from INSIDE: the steel petals are bent OUTWARD, toward the camera,
    so they overhang the lit plate as dark torn tongues around each black hole.

        hp = HullPlating()
        hp.draw(f, t, lamp=(x, y), power=1.0)       # plate, light pool, holes, petals
        f.set_camera(hole_push(t, 1.0, 6.5))        # push into the main hole (into S08)

    World: x right, y down; plate seams run diagonally like strakes; the bilge (hull edge)
    curves off on the right, so the hull's riveted silhouette edge shows against the water."""

    HOLES = ((0.0, 0.0, 230.0, 1), (-250.0, -880.0, 150.0, 2), (170.0, 820.0, 175.0, 3))   # (x, y, r, seed)
    EDGE_X = 620.0          # the bilge turns away here: beyond it, open water

    def __init__(self):
        self._edge = None

    def edge_pts(self):
        """Riveted silhouette edge of the hull (where the plating curves away), top to bottom."""
        if self._edge is None:
            pts = []
            for i in range(41):
                y = -2600 + 5200 * i / 40
                x = self.EDGE_X + 180 * math.sin(y / 2100.0) + 60 * fbm1(y / 700.0, 5)
                pts.append((x, y))
            self._edge = riveted_edge(pts, pitch=30.0, r=5.0, plate=420.0, seed=3)
        return self._edge

    def petal_shapes(self, hx, hy, r, seed, t=0.0):
        """[(pts, depth)] torn steel tongues around a hole, bent toward the camera: their tips
        project outward past the rim (depth 0..1 = how far they come toward us)."""
        out = []
        n = 7 + seed % 3
        for i in range(n):
            a = 2 * math.pi * (i + 0.5 * hash01(seed, i)) / n
            L = r * (0.4 + 1.0 * hash01(seed, i, 1) ** 1.3)          # some torn short, some long
            curl = 0.35 + 0.6 * hash01(seed, i, 2)
            wb = r * (0.45 + 0.5 * hash01(seed, i, 3))
            ca, sa = math.cos(a), math.sin(a)
            px, py = -sa, ca
            base = (hx + ca * r * 0.92, hy + sa * r * 0.92)
            # the tongue bends toward the camera: in projection it reaches outward, twists, curls
            tw = 0.7 * (hash01(seed, i, 4) - 0.5)
            tip = (base[0] + ca * L + px * L * tw, base[1] + sa * L + py * L * tw)
            pts = [(base[0] - px * wb / 2 - ca * 10, base[1] - py * wb / 2 - sa * 10)]
            for k in range(1, 5):
                u = k / 5
                w = wb / 2 * (1 - u) ** 0.8
                cx = lerp(base[0], tip[0], u) + ca * curl * 30 * math.sin(math.pi * u)
                cy = lerp(base[1], tip[1], u) + sa * curl * 30 * math.sin(math.pi * u)
                pts.append((cx - px * w, cy - py * w))
            pts.append(tip)
            for k in range(4, 0, -1):
                u = k / 5
                w = wb / 2 * (1 - u) ** 0.8
                cx = lerp(base[0], tip[0], u) + ca * curl * 30 * math.sin(math.pi * u)
                cy = lerp(base[1], tip[1], u) + sa * curl * 30 * math.sin(math.pi * u)
                pts.append((cx + px * w, cy + py * w))
            pts.append((base[0] + px * wb / 2 - ca * 10, base[1] + py * wb / 2 - sa * 10))
            out.append((jag(pts, seed=seed * 31 + i, amp=6.0, step=11.0), curl))
        return out

    def petal_tips(self, hole=0, t=0.0):
        """World (x, y) tips of the petals around hole `hole` (0 = the big one) - where the
        gloved hand touches an edge in s06."""
        hx, hy, r, seed = self.HOLES[hole]
        return [pts[len(pts) // 2] for pts, curl in self.petal_shapes(hx, hy, r, seed, t)]

    def draw(self, f, t, lamp=(-300.0, -200.0), power=1.0, beam_r=900.0, water=None, rivets=True):
        """Plate (lit pool around `lamp` = where the beam hits), hull edge, the three holes and
        their petals. Draw the action plane (diver's hand/glove) after. Returns the main hole."""
        pal = f.pal
        c = f.ctx
        x0, y0, x1, y1 = f.cam.view_rect(200)
        water = water or mix(pal.deep, pal.mid, 0.35)
        f.fill(water)
        # plate (everything left of the riveted bilge edge)
        edge = self.edge_pts()
        plate_dark = mix(pal.ink, water, 0.18)
        c.new_path()
        c.move_to(x0 - 2000, edge[0][1])
        for p in edge:
            c.line_to(*p)
        c.line_to(x0 - 2000, edge[-1][1])
        c.close_path()
        c.set_source_rgb(*plate_dark)
        c.fill()
        # the lamp's pool of light on the plating (warm, soft) - part of the set's look
        lit = mix(plate_dark, pal.light, 0.55)
        c.save()
        c.new_path()
        c.move_to(x0 - 2000, edge[0][1])
        for p in edge:
            c.line_to(*p)
        c.line_to(x0 - 2000, edge[-1][1])
        c.close_path()
        c.clip()
        draw.radial(c, lamp, 0, beam_r, [(0, lit, 0.95 * power), (0.35, lit, 0.55 * power), (0.75, lit, 0.15 * power),
                                         (1, lit, 0.0)])
        c.paint()
        # strakes: lapped plate seams = thin shadow lines + rivet rows, only visible in the light
        if rivets:
            for j in range(-6, 7):
                yb = j * 520.0
                pts = [(x, yb + 0.22 * x + 18 * math.sin(x / 900.0)) for x in range(int(x0) - 400, int(min(x1, 800)) + 40, 40)]
                line(c, pts, 5.0, plate_dark, 0.55)
                for x, y in pts[::1]:
                    for dy in (16,):
                        solid_circle(c, (x + 20, y + dy + 0.22 * 20), 5.5)
                c.set_source_rgba(*plate_dark, 0.45)
                c.fill()
            for i in range(-8, 9):
                xb = i * 700.0 + 150
                pts = [(xb + 0.1 * y, y) for y in range(int(y0) - 200, int(y1) + 200, 60)]
                line(c, pts, 4.0, plate_dark, 0.35)
        c.restore()
        # the petals' shadows on the lit plate, thrown away from the lamp (longer for the curled ones)
        c.save()
        c.new_path()
        c.move_to(x0 - 2000, edge[0][1])
        for p in edge:
            c.line_to(*p)
        c.line_to(x0 - 2000, edge[-1][1])
        c.close_path()
        c.clip()
        for hx, hy, r, seed in self.HOLES:
            dxl, dyl = hx - lamp[0], hy - lamp[1]
            dl = math.hypot(dxl, dyl) or 1.0
            ux, uy = dxl / dl, dyl / dl
            kk = clamp(1.2 - dl / (beam_r * 1.4)) * power
            if kk <= 0:
                continue
            for pts, curl in self.petal_shapes(hx, hy, r, seed, t):
                sh = []
                for x, y in pts:
                    w = clamp((math.hypot(x - hx, y - hy) - r * 0.85) / (r * 1.2)) * (60.0 + 110.0 * curl)
                    sh.append((x + ux * w, y + uy * w))
                draw.poly(c, sh)
            c.set_source_rgba(*pal.ink, 0.55 * kk)
            c.fill()
        c.restore()
        # the plate is dished outward around each hole (it was pushed from inside): the side of
        # the bulge that faces the lamp catches it, the far side falls into shade
        for hx, hy, r, seed in self.HOLES:
            dxl, dyl = lamp[0] - hx, lamp[1] - hy
            dl = math.hypot(dxl, dyl) or 1.0
            kk = clamp(1.25 - dl / (beam_r * 1.5)) * power
            if kk <= 0:
                continue
            ux, uy = dxl / dl, dyl / dl
            R = r * 2.1
            c.save()
            c.new_path()
            c.arc(hx, hy, R, 0, 2 * math.pi)
            c.clip()
            c.push_group()
            draw.linear(c, (hx - ux * R, hy - uy * R), (hx + ux * R, hy + uy * R),
                        [(0, pal.ink, 0.42 * kk), (0.45, pal.ink, 0.0), (0.62, lit, 0.0), (0.85, lit, 0.22 * kk),
                         (1, lit, 0.0)])
            c.paint()
            c.pop_group_to_source()
            c.mask(_ring_mask(hx, hy, r * 0.9, R))
            c.restore()
        # holes: black, with their petals bent toward us overhanging the lit plate. Each petal
        # is shaded as a bent plate: its outer face tilts toward the hole's axis as it curls,
        # so the petals on the far side of a hole turn their faces to the lamp (lit steel over
        # the black hole) and the near ones turn away (dark tongues over the lit plate).
        Hl = 650.0                                     # the lamp's distance in front of the plate
        steel_dark = mix(pal.ink, plate_dark, 0.55)
        steel_lit = mix(plate_dark, pal.light, 0.80)
        edges = []
        for hx, hy, r, seed in self.HOLES:
            pts = jag([(hx + math.cos(2 * math.pi * i / 20) * r, hy + math.sin(2 * math.pi * i / 20) * r) for i in range(20)],
                      seed=seed, amp=9.0, step=22.0)
            draw.poly(c, pts)
            c.set_source_rgb(*mix(pal.ink, (0, 0, 0), 0.7))
            c.fill()
            for pts, curl in self.petal_shapes(hx, hy, r, seed, t):
                n = len(pts)
                tip = pts[n // 2]
                base = ((pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2)
                ra = math.atan2(base[1] - hy, base[0] - hx)
                ca, sa = math.cos(ra), math.sin(ra)
                stops = []
                fold = 0.3 + 0.2 * hash01(seed, int(ra * 100), 7)      # the crease where it bent
                for u in (0.0, fold - 0.01, fold + 0.01, 0.7, 1.0):
                    px, py = lerp(base[0], tip[0], u), lerp(base[1], tip[1], u)
                    beta = math.radians(80.0 * curl * (0.2 if u < fold else 0.55 + 0.45 * u))
                    nx, ny, nz = -ca * math.sin(beta), -sa * math.sin(beta), math.cos(beta)
                    lx, ly, lz = lamp[0] - px, lamp[1] - py, Hl
                    ll = math.sqrt(lx * lx + ly * ly + lz * lz)
                    dif = max(0.0, (nx * lx + ny * ly + nz * lz) / ll)
                    pool = clamp(1.0 - math.hypot(lamp[0] - px, lamp[1] - py) / beam_r) ** 0.8 * power
                    stops.append((u, mix(steel_dark, steel_lit, clamp(dif ** 2.2 * pool * 1.35)), 1.0))
                draw.poly(c, pts)
                draw.linear(c, base, tip, stops)
                c.fill()
                # the torn edges that face the lamp catch a thin hot line
                lx, ly = lamp[0] - tip[0], lamp[1] - tip[1]
                pool = clamp(1.0 - math.hypot(lx, ly) / (beam_r * 1.1)) * power
                if pool > 0.02:
                    run = []
                    sgn = 1.0 if sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(n)) < 0 else -1.0
                    for i in range(n - 1):
                        (ax, ay), (bx, by) = pts[i], pts[i + 1]
                        ex, ey = bx - ax, by - ay
                        el = math.hypot(ex, ey) or 1.0
                        nx_, ny_ = sgn * ey / el, -sgn * ex / el          # outward normal
                        mx, my = lamp[0] - (ax + bx) / 2, lamp[1] - (ay + by) / 2
                        ml = math.hypot(mx, my) or 1.0
                        face = (nx_ * mx + ny_ * my) / ml
                        if face > 0.25:
                            run.append((ax, ay))
                            run.append((bx, by))
                        elif run:
                            edges.append((run, pool))
                            run = []
                    if run:
                        edges.append((run, pool))
        with f.light(blur=1.6) as A:
            for run, pool in edges:
                line(A, run, 2.6, pal.light, min(0.85, 0.75 * pool))
        return self.HOLES[0]


def hole_push(t, t0, t1, hole=(0.0, 0.0, 230.0), start=None, zoom_end=6.5, e="inout"):
    """Camera for S06 -> S08: from `start` (Camera, default a framing of the three holes)
    push into the hole centre; zoom grows exponentially so the push feels constant, and the
    hole's darkness fills the frame by t1 (cut to S08 there)."""
    hx, hy, r = hole[:3]
    st = start or Camera(x=hx - 60, y=hy + 60, zoom=0.62)
    u = clamp((t - t0) / max(t1 - t0, 1e-6))
    from engine.core import ease
    v = ease(e, u)
    z = st.zoom * (zoom_end / st.zoom) ** v
    x = lerp(st.x, hx, ease("inout", min(1.0, u * 1.3)))
    y = lerp(st.y, hy, ease("inout", min(1.0, u * 1.3)))
    return Camera(x=x, y=y, zoom=z, rot=st.rot * (1 - v))
