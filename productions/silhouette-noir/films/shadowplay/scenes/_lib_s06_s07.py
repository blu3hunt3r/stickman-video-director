"""Shared helpers for SHADOW PLAY s06 CROSSING and s07 THE SHOW (one animator).

* timing:   k_ (eased progress), env (rise / hold / fall), keys (piecewise eased values)
* her:      her_look (the RED trench, darkened where no light falls), figures drawn through an
            affine map (canonical Actor -> world, perspective depth), rims, emit occlusion
* s06:      FlyingCoat (the coat swung off the hook and onto her shoulders: a Rope spine with a
            cloth outline that opens when it flies); top_figure (her, seen straight down the
            stairwell)
* s07:      the paper dolls of the show on the table rig (the same puppets as
            _lib_shadow_show: drawn as pale paper objects, or as shadow casters), the red paper
            splash scraps, light falloff in apartment 9, the caster remap (several depths
            through one shadow homothety)
"""
import math
from functools import lru_cache

import cairo

from engine import draw
from engine import figure as FG
from engine.core import clamp, ease, hash01, lerp, noise1, smoothstep
from engine.palette import PAPER, RED, SHADOWPLAY as PAL
from engine.physics import Rope
from films.shadowplay import cast, sets
from films.shadowplay.sets_base import PX_M, mix, mul

try:                                       # the Bass designer's murder show (s03, s05)
    from films.shadowplay.scenes import _lib_shadow_show as SHOW
except Exception:                          # noqa: BLE001 - optional neighbour module
    SHOW = None

INK = PAL.ink
AMBER = PAL.light
HOT = PAL.lamp_hot
COLD = mix(PAL.fog_at(1.0), PAL.rain, 0.45)


# ----------------------------------------------------------------------------- timing
def k_(t, t0, dur, e="inout"):
    """Eased 0..1 progress of a move that starts at t0 and lasts dur (exact 0 / 1 outside)."""
    if t <= t0:
        return 0.0
    if dur <= 0 or t >= t0 + dur:
        return 1.0
    return ease(e, (t - t0) / dur)


def env(t, a0, a1, b0, b1, e="inout"):
    """0 before a0, rises to 1 over a0..a1, holds, falls to 0 over b0..b1."""
    return k_(t, a0, a1 - a0, e) * (1.0 - k_(t, b0, b1 - b0, e))


def keys(t, ks):
    """Piecewise eased value: ks = [(t, v), (t, v, ease), ...] (ease of the segment ending
    at that key; default 'inout'). Holds the first / last value outside."""
    if t <= ks[0][0]:
        return ks[0][1]
    for i in range(1, len(ks)):
        k1 = ks[i]
        if t <= k1[0]:
            k0 = ks[i - 1]
            e = k1[2] if len(k1) > 2 else "inout"
            return lerp(k0[1], k1[1], k_(t, k0[0], k1[0] - k0[0], e))
    return ks[-1][1]


def keys2(t, ks):
    """keys() for 2D points: ks = [(t, (x, y)), (t, (x, y), ease), ...]."""
    xs = [(k[0], k[1][0]) + tuple(k[2:]) for k in ks]
    ys = [(k[0], k[1][1]) + tuple(k[2:]) for k in ks]
    return (keys(t, xs), keys(t, ys))


# ----------------------------------------------------------------------------- looks
def her_look(coat=True, coat_k=1.0, flow=0.0, eyes=True):
    """Her (cast.her). coat_k < 1 darkens the RED toward ink: in a dark room the red only
    burns where light falls on it."""
    lk = cast.her(coat=coat)
    lk.colors = dict(lk.colors)
    if coat:
        lk.colors["coat"] = mix(INK, RED, clamp(coat_k))
    lk.opts = dict(lk.opts or {})
    if flow:
        lk.opts["flow"] = flow
    lk.eyes = eyes
    return lk


def plain(lk):
    """A copy of a Look with no part colours (masks, rims, shadows)."""
    import copy
    q = copy.copy(lk)
    q.colors = {}
    return q


# ----------------------------------------------------------------------------- figure through a map
def place_matrix(foot, k, x0=0.0, y0=0.0):
    """Canonical -> world: the canonical point (x0, y0) lands on world `foot`, scaled by k."""
    return cairo.Matrix(xx=k, yy=k, x0=foot[0] - k * x0, y0=foot[1] - k * y0)


def draw_sk(ctx, sk, look, M=None, color=None, alpha=1.0):
    """draw_figure through the map M (no eyes: their bloom would land in the wrong place)."""
    ctx.save()
    if M is not None:
        ctx.transform(M)
    FG.draw_figure(None, sk, look, ctx, color=color or INK, eyes=False, alpha=alpha)
    ctx.restore()


def rim(A, sk, look, M, color, alpha, offset):
    """A crescent of light on the figure's edge facing away from `offset` (world px): the
    silhouette minus a copy of itself shifted by offset. A: an additive light context."""
    if alpha <= 0.005:
        return
    A.push_group()
    draw_sk(A, sk, look, M, color=color)
    A.set_operator(cairo.OPERATOR_DEST_OUT)
    A.save()
    A.translate(offset[0], offset[1])
    draw_sk(A, sk, look, M, color=(0.0, 0.0, 0.0))
    A.restore()
    A.set_operator(cairo.OPERATOR_OVER)
    A.pop_group_to_source()
    A.paint_with_alpha(clamp(alpha))


def occlude(f, par, sk, look, M=None):
    """Black out the emissive buffer under a figure (f.emit glows are added after every
    layer, so a silhouette in front of a lit window or bulb must cut its bloom)."""
    with f.emit(par=par) as G:
        G.save()
        G.set_operator(cairo.OPERATOR_SOURCE)
        draw_sk(G, sk, plain(look), M, color=(0.0, 0.0, 0.0))
        G.restore()


def eye_glints(f, sk, look, M, par=1.0, level=1.0, color=(1.0, 0.96, 0.88)):
    """Her eyes catching the light, drawn where the mapped figure really is (emissive)."""
    if level <= 0.01:
        return
    pts = FG.eye_points(sk, look)
    if not pts:
        return
    k = math.sqrt(abs(M.xx * M.yy)) if M is not None else 1.0
    with f.emit(par=par) as G:
        for p in pts:
            q = M.transform_point(*p) if M is not None else p
            draw.circle(G, q, max(1.2, 2.6 * k))
            draw.fill(G, color, 0.9 * clamp(level))


# ----------------------------------------------------------------------------- s06: the flying coat
class FlyingCoat:
    """The red trench swung off its hook and round her shoulders. A Rope is the coat's spine
    (collar -> hem), driven at the collar by collar(t) -> (x, y); the cloth is a ribbon round
    it, as wide as her hands hold the collar at the top and flaring at the hem when it flies.

    FlyingCoat(collar, spread, length, t0, t1, hang=(x, y)) where spread(t) = half the collar
    width (her hands apart) and hang = the collar point when it hangs on the hook at t0."""

    def __init__(self, collar, spread, length=330.0, t0=-1.0, t1=4.0, seed=6):
        self.collar = collar
        self.spread = spread
        self.length = float(length)
        self.n = 9
        self.seed = seed
        c0 = collar(t0)
        n, L = self.n, self.length

        def init(_t):
            return [(c0[0], c0[1] + L * i / (n - 1)) for i in range(n)]
        self.rope = Rope(n, L, collar, t0=t0, t1=t1, gravity=(0.0, 2500.0), drag=1.9, stiffness=0.28, init=init,
                         iters=12)

    def nodes(self, t):
        return [tuple(p) for p in self.rope.points(t)]

    def speed(self, t, h=1.0 / 30.0):
        """Mean node speed (world px / s): how hard the cloth is flying."""
        a = self.rope.points(t)
        b = self.rope.points(t - h)
        s = 0.0
        for p, q in zip(a, b):
            s += math.hypot(p[0] - q[0], p[1] - q[1])
        return s / (len(a) * h)

    def outline(self, t, flare=None):
        """Closed outline (world) of the cloth at time t."""
        pts = self.nodes(t)
        n = len(pts)
        sp = self.spread(t)
        fl = clamp(self.speed(t) / 1400.0) if flare is None else flare
        left, right = [], []
        for i in range(n):
            v = i / (n - 1)
            p = pts[i]
            q0 = pts[max(i - 1, 0)]
            q1 = pts[min(i + 1, n - 1)]
            tx, ty = q1[0] - q0[0], q1[1] - q0[1]
            Ln = math.hypot(tx, ty) or 1.0
            nx, ny = -ty / Ln, tx / Ln
            if nx < 0:                                  # keep 'left' on screen-left when hanging
                nx, ny = -nx, -ny
            # the top row is the collar held level between her hands
            blend = smoothstep(0.0, 0.35, v)
            ax, ay = lerp(1.0, nx, blend), lerp(0.0, ny, blend)
            al = math.hypot(ax, ay) or 1.0
            ax, ay = ax / al, ay / al
            hw = lerp(sp, sp + 46.0 + 120.0 * fl, v ** 0.8)
            wob = (10.0 + 26.0 * fl) * v * math.sin(v * 7.0 + t * 13.0 + self.seed)
            left.append((p[0] - ax * (hw + wob), p[1] - ay * (hw + wob)))
            right.append((p[0] + ax * (hw - wob), p[1] + ay * (hw - wob)))
        # a ragged, fluttering hem between the two bottom corners
        hem = []
        a, b = left[-1], right[-1]
        tip = pts[-1]
        tx, ty = tip[0] - pts[-2][0], tip[1] - pts[-2][1]
        Ln = math.hypot(tx, ty) or 1.0
        for j in range(1, 6):
            u = j / 6.0
            x, y = lerp(a[0], b[0], u), lerp(a[1], b[1], u)
            d = (6.0 + 22.0 * fl) * math.sin(u * math.pi * 3.0 + t * 17.0 + self.seed)
            hem.append((x + tx / Ln * d, y + ty / Ln * d))
        return left + hem + right[::-1]

    def draw(self, ctx, t, color=RED, alpha=1.0, flare=None):
        pts = self.outline(t, flare)
        ctx.new_path()
        draw.smooth(ctx, pts, close=True, tension=0.35)
        draw.fill(ctx, color, alpha)
        # the shadowed inside of the cloth: a darker band down one side of the spine
        nodes = self.nodes(t)
        sp = self.spread(t)
        side = []
        for i, p in enumerate(nodes):
            v = i / (len(nodes) - 1)
            side.append((p[0] - 0.15 * sp * (1 - v), p[1]))
        for i in range(len(nodes) - 1, -1, -1):
            v = i / (len(nodes) - 1)
            p = nodes[i]
            side.append((p[0] - (0.15 * sp + 18.0 + 40.0 * v) * (1 - 0.3 * v), p[1] + 4.0 * v))
        ctx.new_path()
        draw.smooth(ctx, side, close=True, tension=0.3)
        draw.fill(ctx, mix(color, INK, 0.38), alpha * 0.8)


# ----------------------------------------------------------------------------- s06: her, from above
def top_figure(ctx, p, ppm, heading, phase, coat=RED, flare=0.0, rail=None, lean=0.0):
    """Her seen straight down the stairwell: the bob, the RED shoulders and the coat's hem
    flaring behind her, arms swinging, heels flicking out from under the hem.
    p world point, ppm world px per metre at her depth, heading screen angle (deg) of travel,
    phase = step phase (radians), rail = 1 / -1: the side her hand slides on the banister."""
    a = math.radians(heading)
    fx, fy = math.cos(a), math.sin(a)                   # forward
    sx, sy = -fy, fx                                    # her right
    k = ppm

    def P(f_, s_):
        return (p[0] + fx * f_ * k + sx * s_ * k, p[1] + fy * f_ * k + sy * s_ * k)

    st = math.sin(phase)
    ink = INK
    # feet: heels flick out behind the hem, alternately
    for side, sg in (("L", -1.0), ("R", 1.0)):
        sw = st * sg
        f0 = 0.10 + 0.26 * sw
        draw.capsule(ctx, P(f0 - 0.05, sg * 0.10), P(f0 + 0.10, sg * 0.10), 0.035 * k, 0.04 * k)
    draw.fill(ctx, ink)
    # coat hem: a fan behind her that swings with the stride and flares with speed
    hem = []
    span = 0.30 + 0.10 * flare
    back = 0.30 + 0.16 * flare
    for i in range(9):
        u = i / 8.0
        s_ = lerp(-span, span, u)
        bulge = back * (1.0 - 0.55 * (2 * u - 1) ** 2) + 0.03 * math.sin(u * 9.0 + phase * 2.0) * flare
        hem.append(P(-bulge + 0.04 * st * (2 * u - 1), s_ + 0.03 * st))
    body = [P(0.05, -0.21), P(0.10, 0.0), P(0.05, 0.21)] + hem[::-1]
    ctx.new_path()
    draw.smooth(ctx, body, close=True, tension=0.4)
    draw.fill(ctx, mix(coat, INK, 0.25))
    # arms (ink sleeves) swinging opposite the legs; the rail hand stays on the banister
    for side, sg in (("L", -1.0), ("R", 1.0)):
        sh = P(0.0, sg * 0.20)
        if rail is not None and sg == rail:
            hand = P(0.16, sg * 0.36)
        else:
            sw = -st * sg
            hand = P(0.05 + 0.22 * sw, sg * 0.27)
        draw.capsule(ctx, sh, hand, 0.055 * k, 0.04 * k)
    draw.fill(ctx, ink)
    # shoulders: the red yoke, the collar up
    yoke = [P(0.09, -0.20), P(0.11, 0.0), P(0.09, 0.20), P(-0.06, 0.23), P(-0.10, 0.0), P(-0.06, -0.23)]
    ctx.new_path()
    draw.smooth(ctx, yoke, close=True, tension=0.45)
    draw.fill(ctx, coat)
    coll = [P(0.04, -0.11), P(0.08, 0.0), P(0.04, 0.11), P(-0.05, 0.12), P(-0.05, -0.12)]
    ctx.new_path()
    draw.smooth(ctx, coll, close=True, tension=0.4)
    draw.fill(ctx, mix(coat, INK, 0.45))
    # the head: a dark bob, a sliver of parting
    hc = P(0.03 + 0.04 * lean, 0.0)
    draw.ellipse(ctx, hc, 0.105 * k, 0.095 * k)
    draw.fill(ctx, ink)


# ----------------------------------------------------------------------------- s07: room light
def falloff(d, r0):
    """Inverse-square-ish falloff of a small light (1 at the source, 0.5 at r0)."""
    return 1.0 / (1.0 + (d / max(r0, 1e-6)) ** 2)


def dist3(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


# ----------------------------------------------------------------------------- s07: the dolls on the rig
def rig_stage(apt):
    """(ox, oy, S) placing the show's puppets on Apartment9's table rig, seen from the room
    (mirror=True puts the man on the left, as on the rig): the rods land on the rig's two
    rods and each doll's pelvis on its rod tip. S = the man doll's height in world px."""
    X, Z = apt.TABLE[0], apt.TABLE[1]
    xm, _ = apt.RODS["man"]
    xw, _ = apt.RODS["woman"]
    man_x, woman_x = (SHOW.MAN_X, SHOW.WOMAN_X) if SHOW is not None else (0.205, -0.20)
    S_m = (xw - xm) / (man_x - woman_x)                 # metres
    ox_m = xm + man_x * S_m                             # mirror: man at ox - MAN_X * S
    hip = 0.533
    floor_Y = apt.RODS["man"][1] - hip * S_m
    k = apt.room.ppm(Z)
    o = apt.P(X + ox_m, floor_Y, Z)
    return (o[0], o[1], S_m * k), floor_Y, S_m


def doll_pose(u_end=None):
    """The puppets as the show left them: his knife arm high, her doll folded over its rod
    (the drop undone: she still hangs above the table)."""
    if SHOW is None:
        return None
    p = SHOW.pose(SHOW.SHOW_LEN if u_end is None else u_end)
    p["drop"] = 0.12
    p["fold"] = 0.85
    p["arm"] = SHOW.RAISED
    p["splash"] = 0.0
    p["scream"] = 0.0
    p["mouth"] = 0.0
    p["jolt"] = 0.0
    p["lean"] = 0.0
    p["breathe"] = 0.0
    return p


def doll_mask(ctx, apt, pose, man=True, woman=True):
    """The puppets' silhouette (show.casters) in world coords on ctx: opaque, with the pin
    gaps cleared. Draw it into a group / buffer only (it uses OPERATOR_CLEAR)."""
    st, _, _ = rig_stage(apt)
    if SHOW is not None:
        SHOW.casters(ctx, 0.0, (0, 0, 1, 1), mirror=True, stage=st, pose=pose, cuts=True, blood=False, man=man,
                     woman=woman)
        return
    # fallback: stiff paper dolls on their rods
    ox, oy, S = st
    for who, xs, body, lk in (("man", -0.205, cast.DOLL_MAN, cast.doll_man(ink=None)),
                              ("woman", 0.20, cast.DOLL_WOMAN, cast.doll_woman(ink=None))):
        if (who == "man" and not man) or (who == "woman" and not woman):
            continue
        q = FG.Pose(ox + xs * S, oy - 0.533 * S, 180.0 if who == "woman" else 0.0)
        q.scale = S / body.height
        sk = FG.solve(q, body)
        FG.draw_figure(None, sk, lk, ctx, color=(0.0, 0.0, 0.0), eyes=False)
        ctx.rectangle(ox + xs * S - 0.0035 * S, sk.j["pelvis"][1], 0.007 * S, 0.6 * S)
        ctx.fill()


def draw_paper_dolls(ctx, apt, pose, light, warm=1.0, clip_y=None):
    """The two puppets as pale PAPER objects lit by `light` (0..~1.5: match / lamp at the
    table), with a darker cut edge so they read as card. clip_y: world y below which nothing
    is drawn (the table top: hides the show's crank wire where it would cross the table)."""
    lv = clamp(light, 0.0, 1.6)
    base = mix(INK, mix(PAPER, mul(AMBER, 1.05), 0.35 * warm), clamp(0.05 + 0.75 * lv))
    edge = mix(INK, base, 0.55)
    ctx.save()
    if clip_y is not None:
        ctx.rectangle(-5000, -5000, 10000, clip_y + 5000)
        ctx.clip()
    ctx.push_group()
    doll_mask(ctx, apt, pose)
    pat = ctx.pop_group()
    # a hairline darker rim (the card's cut edge), then the face of the card
    ctx.save()
    ctx.translate(1.2, 1.0)
    ctx.set_source_rgb(*edge)
    ctx.mask(pat)
    ctx.restore()
    ctx.set_source_rgb(*base)
    ctx.mask(pat)
    ctx.restore()


def doll_casters(ctx, apt, pose, M=None):
    """The puppets as shadow casters (opaque) for Sheet.shadow, optionally pre-mapped by M
    (the caster remap: see remap())."""
    ctx.save()
    if M is not None:
        ctx.transform(M)
    doll_mask(ctx, apt, pose)
    ctx.restore()


def remap(apt, z_from, z_to, lamp3d):
    """cairo.Matrix that pre-distorts shapes drawn at depth z_from so that the sheet's shadow
    homothety for casters at depth z_to throws them where depth z_from would: the shadow of
    several depths through one Sheet.shadow pass."""
    c1, m1, _ = apt.shadow_map(z_from, lamp3d)
    c2, m2, _ = apt.shadow_map(z_to, lamp3d)
    # H2^-1(H1(p)) = c2 + (c1 + m1 (p - c1) - c2) / m2  ->  scale s, offset
    s = m1 / m2
    ox = c2[0] + (c1[0] - m1 * c1[0] - c2[0]) / m2
    oy = c2[1] + (c1[1] - m1 * c1[1] - c2[1]) / m2
    return cairo.Matrix(xx=s, yy=s, x0=ox, y0=oy)


SCRAPS = [  # (X, Z on the table top, scale, seed, angle)
    (-0.36, 2.78, 0.42, 3, 20.0), (0.05, 2.74, 0.30, 7, -35.0), (0.31, 2.83, 0.36, 11, 70.0),
    (-0.12, 2.86, 0.22, 17, 5.0), (0.44, 2.73, 0.20, 19, -60.0),
]


def red_scraps(ctx, apt, light, grow=1.0):
    """The red paper splash scraps on the table top, foreshortened, lit by `light`."""
    lv = clamp(light, 0.0, 1.5)
    col = mix(mix(INK, RED, 0.20), RED, clamp(0.15 + 0.85 * lv))
    h = apt.TABLE[4]
    for (X, Z, sc, seed, ang) in SCRAPS:
        p = apt.P(X, h + 0.002, Z)
        k = apt.room.ppm(Z) / PX_M
        ctx.save()
        ctx.translate(p[0], p[1])
        ctx.scale(1.0, 0.16)
        sets.paper_blood(ctx, (0.0, 0.0), sc * k, seed=seed, grow=grow, angle=ang, color=col)
        ctx.restore()
