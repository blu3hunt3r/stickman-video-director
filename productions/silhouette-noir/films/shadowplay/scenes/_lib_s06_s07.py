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
def her_look(coat=True, coat_k=1.0, flow=0.0, eyes=True, sleeves=True):
    """Her (cast.her). coat_k < 1 darkens the RED toward ink: in a dark room the red only
    burns where light falls on it. sleeves: the trench's sleeves in the coat's red too (the
    cast look leaves the arms ink, which reads as a sleeveless dress)."""
    lk = cast.her(coat=coat)
    lk.colors = dict(lk.colors)
    if coat:
        lk.colors["coat"] = mix(INK, RED, clamp(coat_k))
        if sleeves:
            lk.colors["arm"] = mix(INK, mix(RED, INK, 0.12), clamp(coat_k))
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


def eye_glints(f, sk, look, M, par=1.0, level=1.0, color=None):
    """Her eyes (the engine's Limbo eyes: two bright dots and a soft halo) drawn where the
    mapped figure really is: draw_figure's own eyes would land unmapped. Hidden when her
    back is turned, like figure.draw_eyes."""
    if level <= 0.01:
        return
    e1, e2, r, w, front = FG.eye_points(sk, look)
    if front < -0.35:
        return
    vis = clamp((front + 0.35) / 0.35) if front < 0 else 1.0
    op = clamp(sk.pose.eyes.get("open", 1.0))
    g = clamp(level) * vis * sk.pose.eyes.get("glow", 1.0)
    if op <= 0.02 or g <= 0.01:
        return
    col = color or look.eye_color
    k = math.sqrt(abs(M.xx * M.yy)) if M is not None else 1.0
    pts = [M.transform_point(*e) if M is not None else e for e in (e1, e2)]
    with f.layer(par=par) as c:
        for i, q in enumerate(pts):
            rr = r * k * (1.0 if i == 0 else lerp(0.82, 1.0, w))
            draw.ellipse(c, q, rr * 0.9, rr * op)
            draw.fill(c, col, g)
    with f.emit(par=par) as G:
        for q in pts:
            draw.glow_disc(G, q, r * k * 5.5, col, 0.5 * g * op)


# ----------------------------------------------------------------------------- s06: the flying coat
class KeyedCoat:
    """The red trench swung off its hook and round her shoulders, art-directed: the collar
    is held between her hands (collar_ends(t) -> (CL, CR), world), the hem flies on keyed
    offsets from the collar (hem(t) -> (dx, dy, half_width, flare)). The cloth is a ribbon
    along a sagging spine from collar to hem: a hanging coat, a flag, a bell."""

    def __init__(self, collar_ends, hem, seed=6):
        self.ends = collar_ends
        self.hem = hem
        self.seed = seed

    def outline(self, t, n=11):
        CL, CR = self.ends(t)
        dx, dy, hw, fl = self.hem(t)
        C = ((CL[0] + CR[0]) / 2.0, (CL[1] + CR[1]) / 2.0)
        Hm = (C[0] + dx, C[1] + dy)
        span = math.hypot(dx, dy) or 1.0
        sag = 0.28 * abs(dx)                               # a flying coat sags in the middle
        Q = ((C[0] + Hm[0]) / 2.0, (C[1] + Hm[1]) / 2.0 + sag)
        sp = 0.5 * math.hypot(CR[0] - CL[0], CR[1] - CL[1])
        cx, cy = (CR[0] - CL[0]) / (2 * sp or 1.0), (CR[1] - CL[1]) / (2 * sp or 1.0)
        left, right = [], []
        for i in range(n):
            v = i / (n - 1)
            a, b, c = (1 - v) ** 2, 2 * v * (1 - v), v * v
            p = (a * C[0] + b * Q[0] + c * Hm[0], a * C[1] + b * Q[1] + c * Hm[1])
            tx = 2 * (1 - v) * (Q[0] - C[0]) + 2 * v * (Hm[0] - Q[0])
            ty = 2 * (1 - v) * (Q[1] - C[1]) + 2 * v * (Hm[1] - Q[1])
            tl = math.hypot(tx, ty) or 1.0
            nx, ny = -ty / tl, tx / tl                     # perpendicular to the spine
            if nx * cx + ny * cy < 0:                      # point the same way as CL -> CR
                nx, ny = -nx, -ny
            w = smoothstep(0.0, 0.32, v)
            ax, ay = lerp(cx, nx, w), lerp(cy, ny, w)
            al = math.hypot(ax, ay) or 1.0
            ax, ay = ax / al, ay / al
            wd = lerp(sp, hw, v ** 0.85) + (0.10 + 0.22 * fl) * span * math.sin(math.pi * v) * 0.35
            wob = (4.0 + 16.0 * fl) * v * math.sin(v * 6.0 + t * 11.0 + self.seed)
            left.append((p[0] - ax * (wd + wob), p[1] - ay * (wd + wob)))
            right.append((p[0] + ax * (wd - wob), p[1] + ay * (wd - wob)))
        return left, right, C, Hm, Q

    def draw(self, ctx, t, color=RED, alpha=1.0):
        left, right, C, Hm, Q = self.outline(t)
        poly = left[::-1] + right
        # hem between the two bottom corners
        _, _, hw, fl = self.hem(t)
        a, b = right[-1], left[-1]
        ux, uy = (Hm[0] - Q[0]), (Hm[1] - Q[1])
        ul = math.hypot(ux, uy) or 1.0
        for j in range(1, 8):
            u = j / 8.0
            x, y = lerp(a[0], b[0], u), lerp(a[1], b[1], u)
            d = (5.0 + 20.0 * fl) * math.sin(u * math.pi * 3.0 + t * 15.0 + self.seed) + 4.0 * math.sin(u * 23.0)
            poly.append((x + ux / ul * d, y + uy / ul * d))
        ctx.push_group()
        ctx.new_path()
        draw.smooth(ctx, poly, close=True, tension=0.3)
        draw.fill(ctx, color)
        # the shadowed inside of the cloth: a darker fold down from the collar
        fold = []
        n = len(left)
        for i in range(n):
            v = i / (n - 1)
            fold.append((lerp(left[i][0], right[i][0], 0.30 + 0.05 * v), lerp(left[i][1], right[i][1], 0.30 + 0.05 * v)))
        for i in range(n - 1, -1, -1):
            v = i / (n - 1)
            fold.append((lerp(left[i][0], right[i][0], 0.45 + 0.10 * v), lerp(left[i][1], right[i][1], 0.45 + 0.10 * v)))
        ctx.new_path()
        draw.smooth(ctx, fold, close=True, tension=0.3)
        draw.fill(ctx, mix(color, INK, 0.32), 0.85)
        # the near edge of the cloth (lining) catches less light
        edge = [left[i] for i in range(n)] + [(lerp(left[i][0], right[i][0], 0.10), lerp(left[i][1], right[i][1], 0.10))
                                              for i in range(n - 1, -1, -1)]
        ctx.new_path()
        draw.smooth(ctx, edge, close=True, tension=0.3)
        draw.fill(ctx, mix(color, INK, 0.45), 0.9)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(clamp(alpha))


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
DOLL_SIZE = 0.45          # the man doll's height (m): Apartment9.puppet_scale, as _lib_s08_s10 uses


def doll_stages(apt, size=DOLL_SIZE):
    """{'man': (ox, oy, S), 'woman': (...)}: show stages putting each puppet's pelvis on the
    top of its own rod on Apartment9's table rig, seen from the room (mirror=True: the man
    on the left). Same convention as _lib_s08_s10.doll_stage (continuity with s09/s10)."""
    X, Z = apt.TABLE[0], apt.TABLE[1]
    S = size * apt.room.ppm(Z)
    out = {}
    for kind in ("man", "woman"):
        rx, ry = apt.RODS[kind]
        px, py = apt.P(X + rx, ry, Z)
        if SHOW is not None:
            sx, hip = (SHOW.WOMAN_X, SHOW._HIP * SHOW.HER_H) if kind == "woman" else (SHOW.MAN_X, SHOW._HIP)
        else:
            sx, hip = (-0.20, 0.506) if kind == "woman" else (0.205, 0.533)
        out[kind] = (px + sx * S, py + hip * S, S)
    return out


def doll_pose(u_end=None):
    """The puppets as the show left them, standing on their rods: his jagged knife arm
    raised, her doll folded over its rod (the drop undone)."""
    if SHOW is None:
        return None
    p = SHOW.pose(SHOW.SHOW_LEN if u_end is None else u_end)
    p["drop"] = 0.0
    p["fold"] = 0.85
    p["arm"] = SHOW.RAISED
    p["splash"] = 0.0
    p["scream"] = 0.0
    p["mouth"] = 0.0
    p["jolt"] = 0.0
    p["lean"] = 0.0
    p["breathe"] = 0.0
    return p


def doll_mask(ctx, apt, pose, man=True, woman=True, crank=0.0):
    """The puppets' silhouette (show.casters) in world coords on ctx: opaque, with the pin
    gaps cleared. Draw it into a group / buffer only (it uses OPERATOR_CLEAR). The man's arm
    wire runs down to where the rig's own wire ends (Apartment9.arm_wire_end)."""
    st = doll_stages(apt)
    if SHOW is not None:
        if woman:
            SHOW.casters(ctx, 0.0, (0, 0, 1, 1), mirror=True, stage=st["woman"], pose=pose, cuts=True, blood=False,
                         man=False, woman=True)
        if man:
            ox, oy, S = st["man"]
            w = apt.arm_wire_end(crank)
            p = dict(pose)
            p["crank"] = ((ox - w[0]) / S, (w[1] - oy) / S)      # outside-view stage coords (mirrored)
            SHOW.casters(ctx, 0.0, (0, 0, 1, 1), mirror=True, stage=st["man"], pose=p, cuts=True, blood=False,
                         man=True, woman=False)
        return
    # fallback: stiff paper dolls on their rods
    for who, body, lk in (("man", cast.DOLL_MAN, cast.doll_man(ink=None)),
                          ("woman", cast.DOLL_WOMAN, cast.doll_woman(ink=None))):
        if (who == "man" and not man) or (who == "woman" and not woman):
            continue
        ox, oy, S = st[who]
        rx, ry = apt.RODS[who]
        px, py = apt.P(apt.TABLE[0] + rx, ry, apt.TABLE[1])
        q = FG.Pose(px, py, 180.0 if who == "woman" else 0.0)
        q.scale = S / body.height
        sk = FG.solve(q, body)
        FG.draw_figure(None, sk, lk, ctx, color=(0.0, 0.0, 0.0), eyes=False)
        ctx.rectangle(px - 0.0035 * S, py, 0.007 * S, 0.6 * S)
        ctx.fill()


def draw_paper_dolls(ctx, apt, pose, light, warm=1.0, clip_y=None, crank=0.0):
    """The two puppets as pale PAPER objects lit by `light` (0..~1.5: match / lamp at the
    table; a number, or (man, woman) to light them apart), with a darker cut edge so they
    read as card. clip_y: world y below which nothing is drawn (hides the show's long rods
    and wire where they would cross the table and the rig's block)."""
    lights = light if isinstance(light, (tuple, list)) else (light, light)
    ctx.save()
    if clip_y is not None:
        ctx.rectangle(-5000, -5000, 10000, clip_y + 5000)
        ctx.clip()
    for who, lv in (("woman", lights[1]), ("man", lights[0])):
        lv = clamp(lv, 0.0, 1.6)
        base = mix(INK, mix(PAPER, mul(AMBER, 1.05), 0.35 * warm), clamp(0.05 + 0.75 * lv))
        edge = mix(INK, base, 0.55)
        ctx.push_group()
        doll_mask(ctx, apt, pose, man=(who == "man"), woman=(who == "woman"), crank=crank)
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


def doll_casters(ctx, apt, pose, M=None, crank=0.0):
    """The puppets as shadow casters (opaque) for Sheet.shadow, optionally pre-mapped by M
    (the caster remap: see remap()). Isolated in a group (the pin gaps are cleared)."""
    ctx.save()
    if M is not None:
        ctx.transform(M)
    ctx.push_group()
    doll_mask(ctx, apt, pose, crank=crank)
    ctx.pop_group_to_source()
    ctx.paint()
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
        ctx.scale(1.0, 0.24)
        sets.paper_blood(ctx, (0.0, 0.0), 1.3 * sc * k, seed=seed, grow=grow, angle=ang, color=col)
        ctx.restore()
