"""SALVAGE sets - E. THE MERIDIAN, exterior: a 63 m steamer lying on her PORT side.

The wreck is a small 2.5D silhouette model (sections swept along her length, rods, plates)
placed in the deep world and projected with sets_deep.View, so she recedes into the murk:
her stern lies just behind the action plane under the boat (DIVE_X), her bow is lost
~17 000 px away in the fog. On her side, her DECK faces the camera's left: the bridge
house, the stump of the funnel, the masts, boat davits and ventilators stick out toward
the open water, the rails that crossed her decks now stand VERTICAL, and her starboard side
is the roof of the wreck. Every lifeboat is still in its davits.

Near the action plane, at the stern (where the story happens):
  * the ship's BELL hangs from a bracket on the poop deckhouse roof (bell_point()), swaying;
  * the captain's cabin is in that deckhouse; the winch line enters through a starboard
    port (line_entry());
  * three holes in her starboard bilge plating with steel PETALS BENT OUTWARD (holes()):
    they stick up from the wreck's roof edge, a clear silhouette against the light above.

Ship coordinates: s = metres*333 from the counter (stern) toward the bow, b = transverse
(+ starboard = world UP now), h = height above the keel (+ = toward the deck = world left,
toward the camera). Wreck.W(s, b, h) -> world (x, y, z).

S06 close-up of the cut plating is a separate set, HullPlating, with hole_push() for the
camera that pushes into a hole (into S08).

    wreck = Wreck()
    world = DeepWorld(wreck=wreck)
    deep_backdrop(f, t, glow=(700, 500, 900, 0.6))
    view = world.draw(f, t, wreck_kw=dict(bell=True))
    X, Y, k = wreck.bell_screen(view, t)   # where the bell hangs this frame (action-plane coords)
"""
import math

from engine import draw
from engine.core import W, H, clamp, lerp, hash01, noise1, fbm1, smoothstep
from engine.frame import Camera

from .sets_common import (PAL, INK, DIVE_X, SEABED_Y, mix, oriented, jag, riveted_edge, round_rect,
                          hole_circle, solid_circle, line, sag_curve, sway, shape, put, paint)
from .sets_deep import View, rod3, prism3, card, convex_hull, fill_grad, seabed_y
from .sets_props import draw_bell, bell_swing, BELL_H


def _ss(a, b, x):
    return smoothstep(a, b, x)


class _MainPass:
    """Painter proxy: items added through it are never treated as front occluders."""

    def __init__(self, P):
        self.P = P

    def add(self, z, fn):
        self.P.add(z, fn, front=False)


class Wreck:
    """The Meridian on the seabed. heading: angle of her length to the view axis (negative =
    the bow recedes to the left and the deck faces the camera); z0: distance of her stern
    keel behind the action plane; bell_x: world x where the bell hangs (default DIVE_X,
    right under the boat's davit)."""

    D = 2330.0          # keel to main deck
    BEAM = 3500.0
    LEN = 21000.0
    POOP = 250.0
    FOC = 280.0
    BURY = 230.0        # her port side is sunk this deep into the silt

    BELL_SBH = (260.0, -930.0, 2580.0 + 430.0)    # end of the bell's bracket arm (s, b, h): low on her
                                                  # port quarter, a diver's reach above the silt
    BELL_SCALE = 1.5                              # the bell prop is drawn at this size (k * 1.5)
    LINE_SH = (1750.0, 1900.0)                    # the starboard port (facing up) over the captain's cabin
    HOLES = ((3350.0, 560.0, 150.0), (4250.0, 760.0, 185.0), (5150.0, 600.0, 130.0))   # (s, h, radius)

    def __init__(self, heading=24.0, bell_z=150.0, bell_x=None, heel=90.0):
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
    def bell_point(self, t=0.0):
        """World (x, y, z) of the bell bracket's end - the bell's crown hangs here."""
        return self.W(*self.BELL_SBH)

    def bell_screen(self, view, t=0.0):
        """(X, Y, k): the bell's hanging point in action-plane coords this frame and the
        scale to draw props there (draw_bell(ctx, X, Y, s=k * Wreck.BELL_SCALE, ...))."""
        x, y, z = self.bell_point(t)
        X, Y = view.P(x, y, z)
        return X, Y, view.k(z)

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
        # stern rail (now vertical): stanchions + rails across the poop at the stern
        def rail_across(s, b0, b1, h0, step, r=24.0):
            items = []
            nb = max(2, int((b1 - b0) / step))
            for i in range(nb + 1):
                bb = lerp(b0, b1, i / nb)
                items.append((W_(s, bb, h0), W_(s, bb, h0 + 330), r, r * 0.8))
            for hh in (h0 + 330, h0 + 175):
                items.append((W_(s, b0, hh), W_(s, b1, hh), r * 0.8, r * 0.8))
            return items
        rails = rail_across(90, -1180, 1180, dp, 260)
        # starboard rails along the deck edge (receding comb on the wreck's roof edge)
        def rail_along(s0, s1, h0, step, r=24.0):
            items = []
            n = max(2, int((s1 - s0) / step))
            prev = None
            for i in range(n + 1):
                s = lerp(s0, s1, i / n)
                bb = self.hb_deck(s) - 30
                bot, top = W_(s, bb, h0), W_(s, bb, h0 + 330)
                items.append((bot, top, r, r * 0.8))
                if prev is not None:
                    items.append((prev, top, r * 0.8, r * 0.8))
                prev = top
            return items
        rails += rail_along(200, 3150, dp, 330)
        rails += rail_along(3260, 18200, D, 520)
        for a3, b3, r0, r1 in rails:
            P.add((a3[2] + b3[2]) / 2 - 60, lambda ctx, view, a3=a3, b3=b3, r0=r0, r1=r1: rod3(ctx, view, a3, b3, r0, r1))
        # ensign staff at the stern, bent
        a3, b3, c3 = W_(60, 0, dp), W_(60, 0, dp + 900), W_(60, -260, dp + 1500)
        P.add(a3[2] - 100, lambda ctx, view: (rod3(ctx, view, a3, b3, 30, 24), rod3(ctx, view, b3, c3, 24, 16)))
        # the bell's bracket: an arm out of her port quarter (now horizontal, low over the silt) + a brace
        s_, b_, h_ = self.BELL_SBH
        br0, br1 = W_(s_, b_, dp - 10), W_(s_, b_, h_ + 20)
        brace0, brace1 = W_(s_, b_ + 320, dp - 10), W_(s_, b_, dp + 300)
        bs = self.BELL_SCALE

        def bracket(ctx, view, t=t):
            rod3(ctx, view, br0, br1, 34, 28)
            rod3(ctx, view, brace0, brace1, 20, 18)
            if bell:
                X, Y = view.Pp(br1)
                k = view.k(br1[2])
                ang, cl = bell_swing(t, seed=1) if bell_angle is None else (bell_angle, clapper or 0.0)
                draw_bell(ctx, X, Y - 6 * k, angle=ang, clapper=cl, s=k * bs, color=view.tone(br1[2], Y), yoke=True)
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
        lo, hi = cyl(8600, 0, D + 820, D + 2050, 470)
        P.add(sum(p[2] for p in lo + hi) / (2 * len(lo)) - 160, lambda ctx, view, lo=lo, hi=hi: prism3(ctx, view, lo, hi))
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
        P.add((f0[2] + f1[2]) / 2 - 300, lambda ctx, view: (rod3(ctx, view, f0, f1, 70, 38), rod3(ctx, view, c0, c1, 28, 28)))
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

    def draw(self, f, t, view=None, **kw):
        """Draw the wreck alone (no seabed) - e.g. over a custom backdrop."""
        from .sets_deep import Painter
        view = view or View(f)
        P = Painter()
        self.add_items(P, t, **kw)
        P.render(f, view)
        return view


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
            a = 2 * math.pi * (i + 0.45 * hash01(seed, i)) / n
            L = r * (0.55 + 0.75 * hash01(seed, i, 1))
            curl = 0.35 + 0.6 * hash01(seed, i, 2)
            wb = r * (0.55 + 0.35 * hash01(seed, i, 3))
            ca, sa = math.cos(a), math.sin(a)
            px, py = -sa, ca
            base = (hx + ca * r * 0.92, hy + sa * r * 0.92)
            # the tongue bends toward the camera: in projection it reaches outward and curls
            tip = (base[0] + ca * L + px * L * 0.35 * (hash01(seed, i, 4) - 0.5),
                   base[1] + sa * L + py * L * 0.35 * (hash01(seed, i, 4) - 0.5))
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
            out.append((jag(pts, seed=seed * 31 + i, amp=4.0, step=14.0), curl))
        return out

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
        # holes: black, with their petals bent toward us overhanging the lit plate
        for hx, hy, r, seed in self.HOLES:
            pts = jag([(hx + math.cos(2 * math.pi * i / 20) * r, hy + math.sin(2 * math.pi * i / 20) * r) for i in range(20)],
                      seed=seed, amp=9.0, step=22.0)
            draw.poly(c, pts)
            c.set_source_rgb(*mix(pal.ink, (0, 0, 0), 0.6))
            c.fill()
            for pts, curl in self.petal_shapes(hx, hy, r, seed, t):
                draw.poly(c, pts)
            c.set_source_rgb(*pal.ink)
            c.fill()
        # rim light on the petal tips that curl into the beam (thin warm edges), additive
        with f.light(blur=2.0) as A:
            for hx, hy, r, seed in self.HOLES:
                d = math.hypot(hx - lamp[0], hy - lamp[1])
                k = clamp(1 - d / (beam_r * 1.2)) * power
                if k <= 0:
                    continue
                for pts, curl in self.petal_shapes(hx, hy, r, seed, t):
                    tip = pts[len(pts) // 2]
                    line(A, pts[len(pts) // 2 - 2: len(pts) // 2 + 1], 3.0, pal.light, 0.5 * k * curl)
        return self.HOLES[0]


def hole_push(t, t0, t1, hole=(0.0, 0.0, 230.0), start=None, zoom_end=14.0, e="inout"):
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
