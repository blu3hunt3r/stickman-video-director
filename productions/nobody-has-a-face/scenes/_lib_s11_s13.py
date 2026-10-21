"""Shared toolkit for S11 The Chase, S12 The Trap and S13 Blackout.

Everything here is built from the shared engine (draw / rig / props / sets / fx) so props and
figures stay identical to the rest of the film. All functions are pure functions of their
arguments (static geometry is cached with lru_cache, which is deterministic).

Contents
  * shot helpers           - cut lists, local time, eased keys, mechanical ticks
  * Persp                  - tiny pinhole camera for pseudo-3D sets (true dolly parallax)
  * alley_*                - one-point-perspective night alleys (walls, windows, fire escapes,
                             puddles, laundry sheets, dead-end wall, far cross street)
  * front_run / run_limp   - run cycles (front/back view and profile) with the detective's limp
  * figure_cut             - white figure with a thin black occlusion gap (line-art depth)
  * car interior + street  - S12 / S13 car set, wipers with rain droplets, juror street
"""
import math
from functools import lru_cache

from engine import (W, H, WHITE, AMBER, CRIMSON, BLUE, BLACK, clamp, lerp, inv_lerp, ease,
                    hash01, fbm1, noise1, Light, Camera, draw, rig, props, fx, sets)
from engine.rig import Pose


# ----------------------------------------------------------------------------- shot helpers
def shot_of(t, cuts):
    """cuts = [t0, t1, ..., tn]. Returns (index, local_t, t_start, t_end) for the shot holding t."""
    for i in range(len(cuts) - 1):
        if t < cuts[i + 1] or i == len(cuts) - 2:
            return i, t - cuts[i], cuts[i], cuts[i + 1]
    return len(cuts) - 2, t - cuts[-2], cuts[-2], cuts[-1]


def ek(t, t0, t1, a, b, e="inout3"):
    """Eased key: a at t0 -> b at t1 (held outside)."""
    return lerp(a, b, ease(e, inv_lerp(t0, t1, t)))


def tick_step(t, t_hit, dur=0.14):
    """Mechanical clock tick 0 -> 1 landing at t_hit with a small overshoot and settle."""
    if t < t_hit - dur * 0.35:
        return 0.0
    u = clamp((t - (t_hit - dur * 0.35)) / dur)
    return ease("outback", u)


def speed_ramp(u, slow=0.6):
    """Time remap 0..1 -> 0..1 that runs slow in the middle (slow-motion apex) and fast at the ends."""
    return u - slow * math.sin(2 * math.pi * u) / (2 * math.pi)


def flash_env(t, t0, peaks=((0.0, 1.0), (0.11, 0.7), (0.24, 0.45)), decay=0.07):
    """Lightning-style multi-flash envelope (sum of fast-decaying spikes)."""
    v = 0.0
    for dt, a in peaks:
        tt = t - (t0 + dt)
        if tt >= 0:
            v = max(v, a * math.exp(-tt / decay))
    return clamp(v)


def police_blue(t, rate=1.45, phase=0.0):
    """Blue police flicker (double flash) with a soft tail, 0..1. Flash peak at t = 0 when phase=0."""
    p = (t * rate + phase) % 1.0
    v = 0.0
    for c in (0.0, 0.17):
        d = p - c
        if 0 <= d < 0.12:
            v = max(v, 1.0 - d / 0.12 * 0.35)
        elif 0.12 <= d < 0.3:
            v = max(v, 0.65 * math.exp(-(d - 0.12) / 0.05))
    return v


# ----------------------------------------------------------------------------- pseudo 3D
class Persp:
    """Pinhole camera for pseudo-3D sets. World: X right, Y down (ground Y = 0, up negative),
    Z forward (depth). The eye is at (ex, ey, ez) looking along +Z; (cx, cy) is the screen point
    of the vanishing point (shifted lens keeps verticals vertical)."""

    def __init__(self, ex=0.0, ey=-420.0, ez=0.0, F=1000.0, cx=540.0, cy=560.0, near=45.0, fog=6500.0):
        self.ex, self.ey, self.ez, self.F, self.cx, self.cy = ex, ey, ez, F, cx, cy
        self.near, self.fogd = near, fog

    def d(self, Z):
        return Z - self.ez

    def k(self, Z):
        return self.F / max(Z - self.ez, self.near)

    def p(self, X, Y, Z):
        k = self.F / max(Z - self.ez, self.near)
        return (self.cx + (X - self.ex) * k, self.cy + (Y - self.ey) * k)

    def fog(self, Z):
        return clamp(1.12 - (Z - self.ez) / self.fogd, 0.16, 1.0)

    def wk(self, Z):
        return clamp((self.F / max(Z - self.ez, self.near)) ** 0.45, 0.5, 2.4)

    def clip_seg(self, A, B):
        n = self.ez + self.near
        if A[2] < n and B[2] < n:
            return None
        if A[2] < n:
            u = (n - A[2]) / (B[2] - A[2])
            A = (A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u, n)
        elif B[2] < n:
            u = (n - B[2]) / (A[2] - B[2])
            B = (B[0] + (A[0] - B[0]) * u, B[1] + (A[1] - B[1]) * u, n)
        return A, B

    def clip_poly(self, pts):
        n = self.ez + self.near
        out = []
        m = len(pts)
        for i in range(m):
            A, B = pts[i], pts[(i + 1) % m]
            ina, inb = A[2] >= n, B[2] >= n
            if ina:
                out.append(A)
            if ina != inb:
                u = (n - A[2]) / (B[2] - A[2])
                out.append((A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u, n))
        return out

    # drawing ------------------------------------------------------------------
    def line(self, f, A, B, w=2.4, alpha=1.0, color=WHITE, glow=0.0):
        c = self.clip_seg(A, B)
        if c is None:
            return
        A, B = c
        zm = 0.5 * (A[2] + B[2])
        a = alpha * self.fog(zm)
        if a <= 0.01:
            return
        draw.line(f, self.p(*A), self.p(*B), w * self.wk(zm), color, a, glow=glow)

    def poly(self, f, pts, w=2.4, alpha=1.0, color=WHITE, fill=None, fill_alpha=1.0, glow=0.0,
             closed=True, min_px=0.0):
        P = self.clip_poly(pts) if closed else pts
        if len(P) < 2:
            return None
        zm = sum(q[2] for q in P) / len(P)
        S = [self.p(*q) for q in P]
        if min_px > 0:
            xs = [q[0] for q in S]
            ys = [q[1] for q in S]
            if max(xs) - min(xs) < min_px and max(ys) - min(ys) < min_px:
                return S
        if max(q[0] for q in S) < -200 or min(q[0] for q in S) > W + 200 or \
                max(q[1] for q in S) < -200 or min(q[1] for q in S) > H + 200:
            return S
        fg = self.fog(zm)
        if fill is not None and len(S) >= 3:
            draw.fill(f, S, fill, fill_alpha * (fg if fill is not BLACK else 1.0), glow=glow)
        if w > 0 and alpha > 0:
            draw.stroke(f, S, w * self.wk(zm), color, alpha * fg, closed=closed)
        return S

    def ground_circle(self, X, Z, r, n=18, Y=0.0):
        return [(X + r * math.cos(2 * math.pi * i / n), Y, Z + r * math.sin(2 * math.pi * i / n))
                for i in range(n)]


def pose_at(P, X, Z, pose, Y=0.0):
    """Place a rig Pose (built with x=0) standing on the 3D ground point (X, Y, Z): scale from depth."""
    gx, gy = P.p(X, Y, Z)
    s = P.k(Z)
    p = pose.copy(x=gx, s=pose.s * s)
    return rig.on_ground(p, gy), s


# ----------------------------------------------------------------------------- alley geometry
@lru_cache(maxsize=32)
def alley_geom(seed=1, hw=450.0, L=4200.0, z0=350.0, fire=0.4, far=True, lit=0.06, rows=4, skip=0.3):
    """Static geometry of a one-point-perspective alley (cached). Returns dict of lists."""
    segs, quads, lits, pipes, fires, doors = [], [], [], [], [], []
    for side in (-1, 1):
        X = side * hw
        z, i = z0, 0
        while z < L - 10:
            ln = 650 + 520 * hash01(seed, side, i)
            z1 = min(L, z + ln)
            h = 1450 + 1000 * hash01(seed, side, i, 1)
            segs.append(((X, 0, z), (X, -h, z), 2.8, 1.0))
            segs.append(((X, 0, z1), (X, -h, z1), 2.8, 1.0))
            segs.append(((X, -h, z), (X, -h, z1), 2.8, 1.0))
            segs.append(((X, -h + 34, z), (X, -h + 34, z1), 1.6, 0.55))          # cornice
            # windows
            n = max(1, int((z1 - z - 220) / 270))
            r = 0
            while 330 + r * 280 + 170 < h - 160 and r < rows:
                yb = -(330 + r * 280)
                for c in range(n):
                    zc = z + 110 + (c + 0.5) * (z1 - z - 220) / n
                    hh = hash01(seed, side, i, r, c)
                    if hh < skip:
                        continue
                    q = [(X, yb, zc - 62), (X, yb - 168, zc - 62), (X, yb - 168, zc + 62), (X, yb, zc + 62)]
                    if hh > 1 - lit and zc > 1500:
                        lits.append(q)
                    else:
                        quads.append((q, 1.6, 0.42))
                r += 1
            # door at ground level
            if hash01(seed, side, i, 3) < 0.55 and z1 - z > 500:
                zd = z + 160 + 120 * hash01(seed, side, i, 4)
                q = [(X, 0, zd), (X, -270, zd), (X, -270, zd + 150), (X, 0, zd + 150)]
                doors.append((q, zd + 75, side))
            # drain pipe
            if hash01(seed, side, i, 6) < 0.6:
                zp = z + 40
                pipes.append(((X - side * 14, 0, zp), (X - side * 14, -h + 40, zp)))
            # fire escape
            if hash01(seed, side, i, 5) < fire and z1 - z > 620 and z > 1250:
                za = z + 140
                zb = min(z1 - 90, za + 400)
                Xo = side * (hw - 135)
                Xm = side * (hw - 70)
                levels = []
                r = 0
                while 560 + r * 280 < h - 260 and r < 4:
                    levels.append(-(560 + r * 280))
                    r += 1
                fires.append(dict(X=X, Xo=Xo, Xm=Xm, za=za, zb=zb, levels=levels))
            z = z1 + 30
            i += 1
    return dict(segs=segs, quads=quads, lits=lits, pipes=pipes, fires=fires, doors=doors,
                hw=hw, L=L, z0=z0, seed=seed)


def draw_fire_escape(f, P, fe, alpha=1.0):
    X, Xo, Xm, za, zb = fe["X"], fe["Xo"], fe["Xm"], fe["za"], fe["zb"]
    lv = fe["levels"]
    side = 1 if X > 0 else -1
    for j, Y in enumerate(lv):
        P.poly(f, [(Xo, Y, za), (Xo, Y, zb), (X, Y, zb)], 2.0, alpha * 0.8, closed=False, min_px=3)
        P.line(f, (Xo, Y - 88, za), (Xo, Y - 88, zb), 1.6, alpha * 0.7)
        for zz in (za, zb):
            P.line(f, (Xo, Y, zz), (Xo, Y - 88, zz), 1.3, alpha * 0.6)
        if j + 1 < len(lv):
            Y2 = lv[j + 1]
            if j % 2 == 0:
                a, b = (zb - 40, Y), (za + 40, Y2)
            else:
                a, b = (za + 40, Y), (zb - 40, Y2)
            Xs = side * (hw_of(X) - 70)
            P.line(f, (Xs, a[1], a[0]), (Xs, b[1], b[0]), 1.8, alpha * 0.75)
            for s_ in range(1, 5):
                u = s_ / 5
                zz = a[0] + (b[0] - a[0]) * u
                yy = a[1] + (b[1] - a[1]) * u
                P.line(f, (side * (hw_of(X) - 30), yy, zz), (side * (hw_of(X) - 110), yy, zz), 1.1, alpha * 0.45)
    if lv:
        Y = lv[0]
        Xs = side * (hw_of(X) - 70)
        P.line(f, (Xs, Y, za + 60), (Xs, -230, za + 60), 1.3, alpha * 0.6)


def hw_of(X):
    return abs(X)


def draw_alley(f, P, G, t=0.0, alpha=1.0, far=True, far_lit=0.12, ground=True, puddles=(), zmax=None):
    """Draw alley geometry G (from alley_geom) through Persp P."""
    hw, L, z0 = G["hw"], G["L"], G["z0"]
    zlim = zmax if zmax is not None else L
    # ground seams + gutter
    if ground:
        for side in (-1, 1):
            P.line(f, (side * hw, 0, max(z0, P.ez + P.near)), (side * hw, 0, zlim), 3.0, alpha)
        P.line(f, (0, 0, max(z0, P.ez + P.near)), (0, 0, zlim), 1.4, alpha * 0.28)
    for A, B, w, a in G["segs"]:
        if A[2] <= zlim + 1:
            P.line(f, A, (B[0], B[1], min(B[2], zlim)), w, alpha * a)
    for q, w, a in G["quads"]:
        if q[0][2] < zlim:
            P.poly(f, q, w, alpha * a, min_px=2.5)
    for q in G["lits"]:
        if q[0][2] < zlim:
            S = P.poly(f, q, 0, 0, fill=AMBER, fill_alpha=0.55 * alpha, glow=0.5, min_px=0)
    for A, B in G["pipes"]:
        if A[2] < zlim:
            P.line(f, A, B, 2.0, alpha * 0.75)
    for q, zc, side in G["doors"]:
        if q[0][2] < zlim:
            P.poly(f, q, 2.4, alpha * 0.9, min_px=3)
    for fe in G["fires"]:
        if fe["za"] < zlim:
            draw_fire_escape(f, P, fe, alpha)
    for (X, Z, r) in puddles:
        P.poly(f, P.ground_circle(X, Z, r, 30), 1.4, alpha * 0.32)


def draw_cross_street(f, P, G, t=0.0, alpha=1.0, depth=900.0, lit=0.12, seed=7):
    """The far cross street seen through the alley's open end: ground line + facade across."""
    L = G["L"]
    zf = L + depth
    P.line(f, (-2600, 0, zf), (2600, 0, zf), 2.4, alpha)
    P.line(f, (-2600, 0, L + 60), (-G["hw"], 0, L + 60), 1.6, alpha * 0.6)
    P.line(f, (G["hw"], 0, L + 60), (2600, 0, L + 60), 1.6, alpha * 0.6)
    for c in range(-6, 7):
        for r in range(6):
            x0 = c * 300 - 70
            yb = -(320 + r * 290)
            if hash01(seed, c, r) < 0.15:
                continue
            q = [(x0, yb, zf), (x0, yb - 170, zf), (x0 + 140, yb - 170, zf), (x0 + 140, yb, zf)]
            if hash01(seed, c, r, 1) < lit:
                P.poly(f, q, 0, 0, fill=AMBER, fill_alpha=0.5 * alpha, glow=0.4)
            else:
                P.poly(f, q, 1.4, alpha * 0.55, min_px=2)


def draw_dead_end(f, P, hw, z, h=2100.0, alpha=1.0, seed=5):
    """Brick dead-end wall closing the alley at depth z."""
    P.poly(f, [(-hw, 0, z), (-hw, -h, z), (hw, -h, z), (hw, 0, z)], 3.0, alpha)
    rows = 26
    for r in range(1, rows):
        y = -r * 64
        if -y > h - 30:
            break
        shown = hash01(seed, r) < 0.55 or r < 9
        if not shown:
            continue
        x0 = -hw + (hw * 2) * (0.1 * hash01(seed, r, 1))
        x1 = hw - (hw * 2) * (0.25 * hash01(seed, r, 2))
        P.line(f, (x0, y, z), (x1, y, z), 1.3, alpha * (0.42 if r < 9 else 0.25))
        off = 60 if r % 2 else 0
        for c in range(-4, 5):
            if hash01(seed, r, c) < 0.5:
                xx = c * 120 + off
                if x0 < xx < x1:
                    P.line(f, (xx, y, z), (xx, y + 64, z), 1.1, alpha * 0.3)
    # a shut metal door and a pipe
    P.poly(f, [(-260, 0, z - 2), (-260, -300, z - 2), (-100, -300, z - 2), (-100, 0, z - 2)], 2.4, alpha * 0.9)
    P.line(f, (-130, -150, z - 2), (-118, -150, z - 2), 3.0, alpha)
    P.line(f, (300, 0, z - 2), (300, -h, z - 2), 2.0, alpha * 0.7)


def draw_box(f, P, x0, x1, z0, z1, h, alpha=1.0, w=2.2):
    """A crate / dumpster: 3D box on the ground."""
    c = [(x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1),
         (x0, -h, z0), (x1, -h, z0), (x1, -h, z1), (x0, -h, z1)]
    for a, b in ((0, 1), (1, 2), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)):
        P.line(f, c[a], c[b], w, alpha)


def draw_can(f, P, X, Z, r=60.0, h=150.0, alpha=1.0):
    top = [(X + r * math.cos(a), -h, Z + r * math.sin(a)) for a in [2 * math.pi * i / 14 for i in range(14)]]
    P.poly(f, top, 2.0, alpha)
    P.line(f, (X - r, 0, Z), (X - r, -h, Z), 2.0, alpha)
    P.line(f, (X + r, 0, Z), (X + r, -h, Z), 2.0, alpha)
    bot = [(X + r * math.cos(a), 0, Z + r * math.sin(a)) for a in [math.pi * i / 10 for i in range(11)]]
    P.poly(f, bot, 2.0, alpha * 0.8, closed=False)


def puddle_ripples(f, P, t, X, Z, r, seed=0, alpha=0.5, n=3):
    for i in range(n):
        per = 0.7 + 0.5 * hash01(seed, i)
        tau = (t / per + hash01(seed, i, 1)) % 1.0
        cyc = int(t / per + hash01(seed, i, 1))
        xx = X + (hash01(seed, i, cyc) - 0.5) * r
        zz = Z + (hash01(seed, i, cyc, 2) - 0.5) * r * 0.8
        rr = 8 + r * 0.32 * tau
        P.poly(f, P.ground_circle(xx, zz, rr, 12), 1.2, alpha * (1 - tau) ** 1.6)


# ----------------------------------------------------------------------------- laundry
def sheet_pts(X0, X1, Ytop, Z, hang, t, seed=0, gust=1.0, n=7):
    """Hanging sheet outline (3D points) on a clothesline across the alley, fluttering in wind."""
    pts = []
    sw = gust * (34 + 30 * hash01(seed, 1)) * fbm1(t * 0.9, seed + 3)
    for i in range(n + 1):                                   # top edge (pinned)
        u = i / n
        pts.append((X0 + (X1 - X0) * u, Ytop + 6 * math.sin(math.pi * u), Z))
    for i in range(n, -1, -1):                               # bottom edge, wavy and swinging in Z
        u = i / n
        wav = 18 * math.sin(2 * math.pi * (u * 1.6 + t * 1.3 + hash01(seed, 2)))
        zsw = sw * 4.0 * (0.6 + 0.4 * math.sin(math.pi * u)) + 40 * gust * math.sin(t * 2.1 + u * 3 + seed)
        pts.append((X0 + (X1 - X0) * u + 10 * math.sin(t * 1.7 + u * 5), Ytop + hang + wav, Z + zsw))
    return pts


def draw_sheet(f, P, X0, X1, Ytop, Z, hang, t, seed=0, gust=1.0, alpha=1.0, blue=0.0):
    pts = sheet_pts(X0, X1, Ytop, Z, hang, t, seed, gust)
    S = P.poly(f, pts, 2.4, alpha, fill=BLACK, fill_alpha=1.0)
    if S is None:
        return
    if blue > 0:
        P.poly(f, pts, 0, 0, fill=BLUE, fill_alpha=0.10 * blue, glow=0.25 * blue)
    n = (len(pts) // 2)
    for k in (2, 4, 6):            # soft vertical folds
        if k < n:
            a, b = pts[k], pts[len(pts) - 1 - k]
            P.line(f, (a[0], a[1] + 30, a[2]), (b[0], b[1] - 40, b[2]), 1.2, alpha * 0.32)
    for k in (1, n - 1):          # clothes pins
        a = pts[k]
        P.line(f, (a[0], a[1] - 8, a[2]), (a[0], a[1] + 26, a[2]), 2.6, alpha * 0.9)


# ----------------------------------------------------------------------------- run cycles
def front_run(ph, s=1.0, limp=0.35, back=False, bounce=12.0, pump=1.0):
    """Front-view (facing=0) sprint pose at cycle phase ph (0..1); hip at (0, 0), feet not planted
    (use rig.on_ground). The LEFT leg recovers (knee up toward camera) during ph in [0.5, 1).
    limp shortens the left knee lift, dips the hip on the left stance and nods the head.
    back=True: the figure is seen from behind (its left side is screen-left)."""
    def leg(q, amp):
        if q < 0.5:                       # stance
            v = math.sin(math.pi * q / 0.5)
            return 4.0 + 2 * v, 6.0 + 12 * v
        v = math.sin(math.pi * (q - 0.5) / 0.5)
        return 5.0 + 12 * v * amp, 10.0 + 98 * v * amp
    qL, qR = ph % 1.0, (ph + 0.5) % 1.0
    ampL = 1.0 - 0.38 * limp
    llA, lkA = leg(qL, ampL)
    rlA, rkA = leg(qR, 1.0)
    vL = math.sin(math.pi * (qL - 0.5) / 0.5) if qL >= 0.5 else 0.0
    vR = math.sin(math.pi * (qR - 0.5) / 0.5) if qR >= 0.5 else 0.0
    # arm opposite to the recovering leg pumps up
    pumpR, pumpL = vL * pump, vR * pump
    la, le = 16 + 16 * pumpL, -(62 + 64 * pumpL)
    ra, re = 16 + 16 * pumpR, -(62 + 64 * pumpR)
    left_stance = qL < 0.5
    dip = limp * 0.7 * (math.sin(math.pi * qL / 0.5) if left_stance else 0.0)
    head = 7 * limp * (math.sin(math.pi * qL / 0.5) if left_stance else 0.0)
    lean = 3.5 * math.sin(2 * math.pi * ph) + head * 0.4
    p = Pose(x=0, y=0, s=s, facing=0, lean=lean, head=head,
             la=la, le=le, ra=ra, re=re, ll=llA, lk=lkA, rl=rlA, rk=rkA)
    if back:   # mirror: the figure's left limbs are drawn screen-left
        p = p.copy(la=ra, le=re, ra=la, re=le, ll=rlA, lk=rkA, rl=llA, rk=lkA, lean=-lean, head=-head)
    lift = bounce * s * abs(math.cos(2 * math.pi * ph)) + dip * 10 * s
    return p, lift


def run_limp(t, x0, ground_y, speed, facing=1, s=1.0, limp=0.35, lean=16.0, phase0=0.0, bounce=10.0):
    """rig.run with the detective's subtle limp: shorter left stride, head dip on the left foot."""
    p = rig.run(t, x0, ground_y, speed, facing, s, lean=lean, phase0=phase0, bounce=bounce)
    cyc = 300.0 * s
    ph = (phase0 + speed * t / cyc) % 1.0
    c = math.cos(2 * math.pi * ph)
    if c > 0:
        p = p.copy(ll=p.ll * (1 - 0.3 * limp))
    p = p.copy(head=p.head + 8 * limp * max(0.0, math.sin(2 * math.pi * ph)),
               y=p.y + 5 * s * limp * max(0.0, math.sin(2 * math.pi * ph)))
    return p


def figure_cut(f, pose, alpha=1.0, gap=7.0, gap_alpha=1.0):
    """Draw a WHITE figure with a thin black occlusion gap behind its lines so it reads in front of
    busy line work (line-art depth). Head stays hollow: only its ring gets a gap."""
    J = rig.solve(pose)
    w = rig.FIG_LW * (pose.s ** 0.5)
    g = w + 2 * gap * (pose.s ** 0.3)
    hd, hr, head = J["head_dir"], J["head_r"], J["head"]
    chin = (head[0] - hd[0] * hr, head[1] - hd[1] * hr)
    if gap_alpha > 0:
        draw.circle(f, head, hr, g, BLACK, gap_alpha)
        draw.stroke(f, [chin, J["neck"], J["hip"]], g, BLACK, gap_alpha)
        for side in ("l", "r"):
            draw.stroke(f, [J["shoulder"], J[side + "e"], J[side + "h"]], g, BLACK, gap_alpha)
            draw.stroke(f, [J["hip"], J[side + "k"], J[side + "f"]], g, BLACK, gap_alpha)
    return rig.draw_figure(f, pose, alpha=alpha)


def run_at(P, X, Z, phase, facing=1, limp=0.35, lean=16.0, bounce=10.0, s=1.0, Y=0.0):
    """Profile run pose (with limp) standing on the 3D ground point (X, Y, Z); phase in cycles."""
    k = P.k(Z)
    p = run_limp(0.0, 0.0, 0.0, 0.0, facing, s * k, limp=limp, lean=lean, phase0=phase, bounce=bounce)
    gx, gy = P.p(X, Y, Z)
    return p.copy(x=gx, y=p.y + gy), k


def wall_lamp(f, P, X, Y, Z, on=1.0, side=-1):
    """Caged bulb on a bracket sticking out of an alley wall. Returns (screen point, Light)."""
    P.line(f, (X, Y - 30, Z), (X - side * 60, Y - 30, Z), 2.2, 1.0)
    c = P.p(X - side * 60, Y, Z)
    k = P.k(Z)
    draw.circle(f, c, 14 * k, 2.0, AMBER, 1.0, glow=0.6 * on)
    if on > 0:
        draw.glow_dot(f, c, 110 * k ** 0.7, AMBER, 0.75 * on, core=True)
    return c, Light.radial(c, 360 * k ** 0.6, intensity=0.85 * on)


def on_slope(p, y_at):
    """Move pose vertically so its lowest foot (relative to the slope y_at(x)) touches the slope."""
    J = rig.solve(p)
    dy = min(y_at(J[s_ + "f"][0]) - J[s_ + "f"][1] for s_ in ("l", "r"))
    return p.copy(y=p.y + dy)


def moon(f, c, r, alpha=1.0, t=0.0, wisps=True):
    """THE ring motif as the full moon: a white ring with a soft halo and drifting cloud wisps."""
    draw.circle(f, c, r, 4.2, WHITE, alpha, glow=0.35)
    draw.circle(f, c, r * 0.965, 1.4, WHITE, alpha * 0.35)
    if wisps:
        for i in range(3):
            y = c[1] - r * 0.45 + i * r * 0.42
            x0 = c[0] - r * 1.4 + ((t * (22 + 9 * i) + 180 * i) % (r * 0.9))
            pts = draw.bezier_pts((x0, y), (x0 + r * 0.5, y - 14), (x0 + r * 0.9, y + 12), (x0 + r * 1.5, y - 4), 20)
            draw.stroke(f, pts, 2.0, WHITE, alpha * (0.32 - 0.07 * i))


def cheap_skyline(f, ground_y, x0, x1, seed=3, alpha=0.35, lit=0.1, scale=1.0):
    """Distant rooftop silhouette line + a few lit windows (cheap)."""
    x = x0
    i = 0
    pts = [(x0, ground_y)]
    wins = []
    while x < x1:
        w = (150 + 170 * hash01(seed, i)) * scale
        h = (380 + 620 * hash01(seed, i, 1)) * scale
        top = ground_y - h
        pts += [(x, top), (x + w, top)]
        if hash01(seed, i, 2) < 0.5:
            pts[-1:-1] = [(x + w * 0.4, top), (x + w * 0.4, top - 60 * scale), (x + w * 0.55, top - 60 * scale), (x + w * 0.55, top)]
        for r in range(int(h / (90 * scale))):
            for c in range(max(1, int(w / (60 * scale)))):
                if hash01(seed, i, r, c) < lit:
                    wins.append((x + 14 * scale + c * 60 * scale, top + 40 * scale + r * 90 * scale))
        x += w + 10 * scale
        i += 1
    pts.append((x, ground_y))
    draw.stroke(f, pts, 2.0, WHITE, alpha)
    for (wx, wy) in wins:
        draw.rect(f, wx, wy, 22 * scale, 32 * scale, 1, AMBER, alpha * 1.4, fill_it=True, glow=0.4)


# ----------------------------------------------------------------------------- S12 / S13 street
# Shared world layout (S12 and S13 show the same street, the same building, the same car):
#   sets.apartment at its fixed place (x 180..740, ground 1560), juror window (col 2, row 2)
#   neighbours left/right, sidewalk 1560, far curb 1600, near curb 2040
#   the detective's car (props.car_side) parked on the near side: x=600, ground 2000, s=2.0, nose LEFT
STREET_GROUND = 1560.0
CAR = dict(x=600.0, ground=2000.0, s=2.0, facing=-1)
LAMP_BASE = (930.0, 1580.0)


def juror_window():
    """World center of the juror's window (computed exactly like sets.apartment does)."""
    a = sets.APARTMENT
    x, w, h = a["x"], a["w"], a["h"]
    top = STREET_GROUND - h
    mx, my = w * 0.12, 60.0
    cw = (w - 2 * mx) / a["cols"]
    rh = (h - my - 40) / a["rows"]
    ci, ri = a["juror"]
    return (x + mx + ci * cw + cw / 2, top + my + ri * rh + rh * 0.26), (cw * 0.48, rh * 0.52)


def street_far(f, t, juror_on=1.0, alpha=1.0, reflections=True, others=1.0, lamp_alpha=1.0, frame_her=0.0):
    """Far side of the street: the juror's building with its neighbours, sidewalk, lamp.
    others < 1 fades everything except her window (used for the match cut from S11's ember).
    Returns dict(window=..., lamp=...)."""
    (wx, wy), (ww, wh) = juror_window()
    oa = alpha * others
    grp = f.alpha(oa) if oa < 0.999 else _null()
    with grp:
        props.building(f, -420, STREET_GROUND, 560, 1260, seed=91, lit=0.07, t=t, alpha=0.62,
                       lw=2.6, roof="antenna", cols=4, rows=7)
        props.building(f, 790, STREET_GROUND, 500, 1380, seed=92, lit=0.07, t=t, alpha=0.62,
                       lw=2.6, roof="flat", cols=3, rows=8)
        win = sets.apartment(f, STREET_GROUND, juror_on=juror_on, t=t)
        draw.line(f, (-900, STREET_GROUND), (2000, STREET_GROUND), 3.0, WHITE, 1.0)
        draw.line(f, (-900, STREET_GROUND + 40), (2000, STREET_GROUND + 40), 2.0, WHITE, 0.6)
        with (f.alpha(lamp_alpha) if lamp_alpha < 0.999 else _null()):
            lamp = props.streetlamp(f, LAMP_BASE, height=820, facing=-1, t=t)
        if frame_her > 0:     # her (dark) window frame caught by the light: the empty rectangle reads
            draw.rect(f, wx - ww / 2, wy - wh / 2, ww, wh, 2.4, WHITE, 0.8 * frame_her)
            draw.line(f, (wx - ww / 2 - 8, wy + wh / 2 + 6), (wx + ww / 2 + 8, wy + wh / 2 + 6), 2.2, WHITE, 0.6 * frame_her)
        if reflections:
            fx.reflection(f, lamp[0], STREET_GROUND + 50, 330, 60, AMBER, 0.42, t, seed=2)
    if oa < 0.999 and juror_on > 0:      # her window stays at full strength through the fade
        draw.rect(f, wx - ww / 2, wy - wh / 2, ww, wh, 1, AMBER, alpha * 0.85 * juror_on * (1 - oa),
                  fill_it=True, glow=0.9 * juror_on * (1 - oa))
    if reflections and juror_on > 0:
        fx.reflection(f, wx, STREET_GROUND + 52, 230, 34, AMBER, 0.28 * juror_on * alpha, t, seed=4)
    return dict(window=win, lamp=lamp)


class _null:
    def __enter__(self):
        return None

    def __exit__(self, *a):
        return False


def street_near(f, t, alpha=1.0, juror_on=1.0, win_x=None):
    """Road surface, the near curb and a wide puddle on the near sidewalk that mirrors the
    lamp and (while it is lit) her window."""
    g = CAR["ground"]
    draw.line(f, (-900, g + 40), (2000, g + 40), 3.0, WHITE, alpha)
    draw.line(f, (-900, g + 80), (2000, g + 80), 1.8, WHITE, alpha * 0.55)
    for i in range(6):
        x = -300 + i * 330
        draw.line(f, (x, 1800), (x + 140, 1800), 2.0, WHITE, alpha * 0.25)     # faded lane dashes
    pc = (560.0, 2235.0)
    draw.ellipse(f, pc, 430, 48, 0, 2.0, WHITE, alpha * 0.45)
    fx.puddle(f, pc, 400, 40, t, seed=6, alpha=0.55 * alpha)
    wx = win_x if win_x is not None else juror_window()[0][0]
    if juror_on > 0:
        fx.reflection(f, wx, pc[1] - 36, 70, 30, AMBER, 0.5 * juror_on * alpha, t, seed=9)
    fx.reflection(f, LAMP_BASE[0] - 120, pc[1] - 30, 64, 44, AMBER, 0.4 * alpha, t, seed=10)


def car(f, t, door_open=0.0, alpha=1.0, headlights=0.0):
    return props.car_side(f, CAR["x"], CAR["ground"], s=CAR["s"], facing=CAR["facing"], t=t,
                          door_open=door_open, alpha=alpha, headlights=headlights)


def car_window_poly(which="front"):
    """World polygon of the car's front side window (the driver's) for clipping."""
    s, m, x, g = CAR["s"], CAR["facing"], CAR["x"], CAR["ground"]
    pts = [(-24, -168), (54, -166), (104, -112), (-24, -104)] if which == "front" else \
          [(-100, -150), (-36, -168), (-36, -104), (-118, -104)]
    return [(x + px * s * m, g - 36 * s + py * s) for px, py in pts]


def driver_pose(t, nod=0.0, s=1.5):
    """The detective seated behind the wheel, seen in profile through the side window (car nose left)."""
    g = CAR["ground"]
    p = rig.sit(CAR["x"] - 20, g - 126, facing=-1, s=s, la=40, le=60, ra=34, re=64)
    p = p.copy(head=8 + 30 * nod, lean=4 + 10 * nod)
    return rig.breathe(p, t, amt=0.6, seed=12)


# ----------------------------------------------------------------------------- car interior (S12)
WS = [(110.0, 330.0), (970.0, 330.0), (1045.0, 980.0), (35.0, 980.0)]   # windshield (interior coords)
WIPERS = [((430.0, 985.0), 420.0), ((800.0, 985.0), 400.0)]            # pivot, blade reach
WIPE_P = 1.45                                                         # wiper period (s)
WIPE_A0, WIPE_A1 = -5.0, -112.0                                        # rest (parked right) / top (deg)


def wiper_angle(t, t0=0.0):
    """Wiper blade angle (deg) at time t: rest - sweep up - sweep down - rest."""
    u = ((t - t0) % WIPE_P) / WIPE_P
    if u < 0.12 or u > 0.86:
        k = 0.0
    elif u < 0.49:
        k = ease("sine", (u - 0.12) / 0.37)
    else:
        k = 1.0 - ease("sine", (u - 0.49) / 0.37)
    return WIPE_A0 + (WIPE_A1 - WIPE_A0) * k


def _pass_times(phi, t, t0=0.0):
    """Times (<= t) when a blade swept over angle phi most recently."""
    k = clamp((phi - WIPE_A0) / (WIPE_A1 - WIPE_A0), 0.0, 1.0)   # works for either sweep direction
    inv = math.acos(1 - 2 * k) / math.pi           # inverse of the sine ease
    up = 0.12 + 0.37 * inv
    dn = 0.49 + 0.37 * (1 - inv)
    c = math.floor((t - t0) / WIPE_P)
    best = -1e9
    for cc in (c, c - 1):
        for u in (up, dn):
            tt = t0 + (cc + u) * WIPE_P
            if tt <= t:
                best = max(best, tt)
    return best


def windshield_drops(f, t, t0=0.0, n=150, seed=5, alpha=0.55):
    """Rain droplets on the glass; wiped away where a blade passes, then re-accumulating."""
    x0, y0, x1, y1 = 60.0, 345.0, 1020.0, 975.0
    for i in range(n):
        x = x0 + (x1 - x0) * hash01(seed, i)
        y = y0 + (y1 - y0) * hash01(seed, i, 1)
        last = -1e9
        for (pv, R) in WIPERS:
            d = math.hypot(x - pv[0], y - pv[1])
            if d < R:
                phi = math.degrees(math.atan2(y - pv[1], x - pv[0]))
                if min(WIPE_A0, WIPE_A1) - 2 <= phi <= max(WIPE_A0, WIPE_A1) + 2:
                    last = max(last, _pass_times(phi, t, t0))
        age = t - last
        delay = 0.08 + 1.1 * hash01(seed, i, 2)
        if age < delay:
            continue
        r = 2.2 + 3.4 * hash01(seed, i, 3)
        grow = clamp((age - delay) / 0.25)
        draw.circle(f, (x, y), r * grow, 1.2, WHITE, alpha * 0.8)
        if hash01(seed, i, 4) < 0.25:                    # a few run down the glass
            run = 18 + 40 * hash01(seed, i, 5)
            draw.line(f, (x, y + r), (x - 3, y + r + run * grow), 1.2, WHITE, alpha * 0.45)


def draw_wipers(f, t, t0=0.0, alpha=1.0):
    a = wiper_angle(t, t0)
    for (pv, R) in WIPERS:
        tip = (pv[0] + math.cos(math.radians(a)) * R, pv[1] + math.sin(math.radians(a)) * R)
        mid = (pv[0] + math.cos(math.radians(a)) * R * 0.25, pv[1] + math.sin(math.radians(a)) * R * 0.25)
        draw.line(f, pv, mid, 4.0, WHITE, alpha)
        nx, ny = -math.sin(math.radians(a)), math.cos(math.radians(a))
        b0 = (mid[0] + nx * 8, mid[1] + ny * 8)
        b1 = (tip[0] + nx * 8, tip[1] + ny * 8)
        draw.line(f, mid, b0, 2.4, WHITE, alpha)
        draw.line(f, b0, b1, 5.0, WHITE, alpha)
        draw.circle(f, pv, 9, 2.4, WHITE, alpha)
    return a


def interior_frame(f, alpha=1.0):
    """Roof liner, A-pillars, rear-view mirror, dashboard top (interior coords)."""
    draw.bezier(f, (-60, 300), (300, 270), (780, 270), (1140, 300), 3.0, WHITE, alpha * 0.8)
    draw.stroke(f, WS, 3.2, WHITE, alpha, closed=True)
    draw.line(f, (110, 330), (-40, 1000), 9.0, WHITE, alpha * 0.9)
    draw.line(f, (970, 330), (1120, 1000), 9.0, WHITE, alpha * 0.9)
    draw.line(f, (640, 282), (640, 345), 3.0, WHITE, alpha)
    draw.rect(f, 545, 345, 190, 62, 3.0, WHITE, alpha, radius=22)
    draw.bezier(f, (-60, 985), (300, 965), (780, 965), (1140, 985), 3.4, WHITE, alpha)
    draw.bezier(f, (-60, 1010), (300, 990), (780, 990), (1140, 1010), 1.8, WHITE, alpha * 0.6)


CLOCK_IN = (610.0, 1028.0)   # dash clock (interior coords), right of the driver
CLOCK_R = 36.0
BENCH_TOP = [(-80, 1078), (200, 1086), (540, 1098), (880, 1086), (1160, 1078)]


def bench_seat(f, alpha=1.0):
    """The front bench-seat back seen from the back seat: one wide padded shape across the frame
    (black fill hides his body and the lower dash)."""
    poly = BENCH_TOP + [(1160, 2100), (-80, 2100)]
    draw.fill(f, poly, BLACK, 1.0)
    pts = draw.bezier_pts(BENCH_TOP[0], (200, 1060), (880, 1060), BENCH_TOP[-1], 30)
    draw.fill(f, pts + [(1160, 2100), (-80, 2100)], BLACK, 1.0)
    draw.stroke(f, pts, 3.4, WHITE, alpha)
    draw.stroke(f, draw.bezier_pts((-80, 1128), (200, 1112), (880, 1112), (1160, 1128), 30), 1.6, WHITE, alpha * 0.45)
    draw.line(f, (540, 1100), (540, 1560), 1.4, WHITE, alpha * 0.3)


def umbrella_lying(f, x, ground_y, angle, R, color=CRIMSON, t=0.0, alpha=1.0):
    """THE red umbrella dropped open on the ground (side view prop), resting on its lowest point.
    angle = shaft direction from handle to canopy (deg); rocking = vary angle. Returns apex."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    shaft = R * 1.22
    depth = R * 0.5
    apex = (ux * shaft, uy * shaft)
    rc = (apex[0] - ux * depth, apex[1] - uy * depth)
    low = 0.0                                    # the handle (hand point) at local y 0
    for i in range(25):
        k = -1 + 2 * i / 24
        h = depth * (1 - k * k) ** 0.55
        low = max(low, rc[1] + py * R * k + uy * h)
    for k in (-1.0, 1.0):
        low = max(low, rc[1] + py * R * k - uy * 0.06 * depth)
    hand = (x, ground_y - low)
    return props.umbrella(f, hand, angle=angle, R=R, open_=1.0, color=color, t=t, alpha=alpha, wobble=0.4)


def rack(f, radius, draw_fn, min_blur=6.0):
    """Draw draw_fn() with a defocus of `radius` px. Below min_blur the sharp and a min_blur version
    are cross-faded (cheap and smooth), at ~0 it is drawn sharp."""
    if radius >= min_blur:
        with f.blurred(radius):
            draw_fn()
    elif radius <= 0.35:
        draw_fn()
    else:
        c = radius / min_blur
        with f.alpha(1.0 - c):
            draw_fn()
        with f.blurred(min_blur, alpha=c):
            draw_fn()
