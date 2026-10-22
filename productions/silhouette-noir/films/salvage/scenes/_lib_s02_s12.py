"""Shared helpers for SALVAGE s02 (cash) and s12 (the cut).

The client's KNIFE is one prop in both scenes: it glints on his belt in s02 and he draws it in
s12. Use knife_on_belt(sk) for the sheathed knife on any client skeleton so it sits in the
same place in every shot:

    from films.salvage import sets as S
    from films.salvage.scenes import _lib_s02_s12 as K
    kw = K.knife_on_belt(sk)                 # sk = client skeleton (Actor.draw / .skeleton)
    S.draw_knife(L, **kw)                    # ink silhouette, sheathed, on his right hip
    pts = K.knife_points(kw)                 # pommel / grip / glint / sheath tip (world)
    S.knife_glint(f, pts["glint"], t, t0)    # the moonlight glint on the pommel

Worn on the client's RIGHT hip, the sheath angled down and back along the hip, the handle
pointing forward and up so that it sticks out ~20-30 px (at zoom 1) in front of his coat. In
profile it shows in silhouette ahead of his belt line. Pure functions of the skeleton.
"""
import math

D2R = math.pi / 180.0

KNIFE_S = 0.46        # knife scale for the 640 px client (sets_props.draw_knife units)
KNIFE_TILT = 40.0     # sheath angle below the horizontal, pointing back (deg)
BELT_U = 0.38         # belt height: fraction of the way from the pelvis joint up to the waist joint
BELT_FWD = 0.042      # mouth of the sheath ahead of the spine line (fraction of height, profile)

# local points of the sheathed knife (sets_props.draw_knife, sheathed=True)
_POMMEL = (-102.0, -6.0)      # = its glint point
_GRIP = (-60.0, 0.0)
_TIP = (140.0, 2.0)
_MOUTH = (-22.0, 0.0)


def _forward(sk):
    """(screen-x sign of facing, unit up-the-spine vector, unit forward normal)."""
    J = sk.j
    fx = math.cos(sk.pose.yaw * D2R)
    sgn = 1.0 if fx >= 0 else -1.0
    p, w = J["pelvis"], J["waist"]
    ux, uy = w[0] - p[0], w[1] - p[1]
    L = math.hypot(ux, uy) or 1.0
    ux, uy = ux / L, uy / L
    nx, ny = -uy, ux
    if nx * sgn < 0:
        nx, ny = -nx, -ny
    return fx, (ux, uy), (nx, ny)


def knife_on_belt(sk, side="R", scale=KNIFE_S, tilt=KNIFE_TILT, fwd=BELT_FWD, color=None):
    """kwargs for sets_props.draw_knife: the client's sheathed knife on his belt.

    sk    : the client's skeleton (any pose: it follows the pelvis and the lean of the spine).
    side  : which hip ("R" = his right; near the camera when he faces right).
    Returns dict(x, y, angle, s, flip, sheathed=True[, color]) -> S.draw_knife(ctx, **kw).
    Draw it with the figure's layer, after the figure if the hip is the near one (sk.z)."""
    J = sk.j
    H = sk.H
    fx, (ux, uy), (nx, ny) = _forward(sk)
    p, w = J["pelvis"], J["waist"]
    hip = J["hip_" + side]
    k = max(abs(fx), 0.25)                     # foreshortened forward offset when turned
    bx = p[0] + BELT_U * (w[0] - p[0]) + (hip[0] - p[0]) + nx * fwd * H * k
    by = p[1] + BELT_U * (w[1] - p[1]) + (hip[1] - p[1]) + ny * fwd * H * k
    lean = math.degrees(math.atan2(ux, -uy))   # + = spine leaning toward +x (clockwise)
    s = scale * H / 640.0
    if fx < 0:      # facing left: sheath (local +x) points down-right (back), handle up-left
        kw = dict(x=bx, y=by, angle=tilt + lean, s=s, flip=False, sheathed=True)
    else:           # facing right: mirrored
        kw = dict(x=bx, y=by, angle=-tilt + lean, s=s, flip=True, sheathed=True)
    if color is not None:
        kw["color"] = color
    return kw


def knife_point(kw, local):
    """World point of a local knife point for knife_on_belt kwargs (as draw_knife maps it)."""
    px = -local[0] if kw.get("flip") else local[0]
    a = math.radians(kw.get("angle", 0.0))
    ca, sa = math.cos(a), math.sin(a)
    s = kw.get("s", 1.0)
    return (kw["x"] + (px * ca - local[1] * sa) * s, kw["y"] + (px * sa + local[1] * ca) * s)


def knife_points(kw):
    """World points of the sheathed knife: pommel (= glint), grip (where a hand closes on
    the handle to draw it), mouth (sheath throat), tip (sheath end), handle_dir (unit vector
    from the mouth out along the handle: the direction it is drawn)."""
    pommel = knife_point(kw, _POMMEL)
    mouth = knife_point(kw, _MOUTH)
    dx, dy = pommel[0] - mouth[0], pommel[1] - mouth[1]
    L = math.hypot(dx, dy) or 1.0
    return dict(pommel=pommel, glint=pommel, grip=knife_point(kw, _GRIP), mouth=mouth,
                tip=knife_point(kw, _TIP), handle_dir=(dx / L, dy / L))


# ============================================================================= s02 helpers
# (everything below is used by s02; s12 may reuse it but nothing above depends on it)
import copy                                   # noqa: E402

import cairo                                  # noqa: E402

from engine import costume, draw              # noqa: E402
from engine import figure as F                # noqa: E402
from engine.core import clamp, hash01, lerp, noise1, smoothstep   # noqa: E402
from films.salvage.sets_common import PAL   # noqa: E402

BLACK = (0.0, 0.0, 0.0)


def hermite(p0, v0, p1, v1, t0, t1, t):
    """Cubic Hermite between (t0, p0, v0) and (t1, p1, v1); p/v are tuples (v per second)."""
    T = max(t1 - t0, 1e-9)
    u = clamp((t - t0) / T)
    h00 = 2 * u ** 3 - 3 * u ** 2 + 1
    h10 = u ** 3 - 2 * u ** 2 + u
    h01 = -2 * u ** 3 + 3 * u ** 2
    h11 = u ** 3 - u ** 2
    return tuple(h00 * a + h10 * T * va + h01 * b + h11 * T * vb for a, va, b, vb in zip(p0, v0, p1, v1))


def bezier(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        u = i / n
        a, b, c, d = (1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def resample(pts, n):
    """n points evenly spaced along an open polyline."""
    if len(pts) < 2:
        return list(pts) * n
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    tot = sum(seg) or 1.0
    out, acc, i = [], 0.0, 0
    for k in range(n):
        s = tot * k / (n - 1)
        while i < len(seg) - 1 and acc + seg[i] < s:
            acc += seg[i]
            i += 1
        u = clamp((s - acc) / (seg[i] or 1.0))
        a, b = pts[i], pts[i + 1]
        out.append((lerp(a[0], b[0], u), lerp(a[1], b[1], u)))
    return out


def no_extras(look):
    """A copy of a Look without its extras (for silhouette masks)."""
    L = copy.copy(look)
    L.extras = []
    return L


def emit_mask(f, paint_fns):
    """Black out the emissive buffer under silhouettes standing in front of emitters (the
    moon disc, the lantern): each fn(G) appends a path in world coords; filled black."""
    with f.emit() as G:
        for fn in paint_fns:
            G.new_path()
            fn(G)
            G.set_source_rgb(*BLACK)
            G.fill()


def figure_mask(f, sk, look):
    """Black out the emissive buffer under a figure's silhouette (call before drawing the
    figure itself, so its own eyes / ember still glow)."""
    with f.emit() as G:
        F.draw_figure(None, sk, no_extras(look), G, color=BLACK, eyes=False)


# ----------------------------------------------------------------------------- the Mark V bonnet
class Bonnet:
    """The diver's helmet BONNET (dome, ports, valves, inlet) as a rigid prop, cut from the
    worn helmet of a reference skeleton. The breastplate (corselet) stays on the diver (see
    corselet()). place: centre c (world), rotation ang (deg), flip (mirror about the centre)."""

    N_CORSELET = 3            # costume._helmet: corselet, studs, weights come first

    def __init__(self, ref_sk, look):
        self.look = look
        ps = costume._helmet(ref_sk, look)
        n = self.N_CORSELET if look.opts.get("weights", False) else 2
        self.pieces = ps[n:]
        c, R, vp, vr, inlet = costume.helmet_frame(ref_sk)
        self.c0, self.R, self.inlet0, self.port0 = c, R, inlet, vp

    def _xf(self, c, ang, flip):
        m = cairo.Matrix()
        m.translate(c[0], c[1])
        m.rotate(math.radians(ang))
        if flip:
            m.scale(-1.0, 1.0)
        m.translate(-self.c0[0], -self.c0[1])
        return m

    def point(self, p, c, ang=0.0, flip=False):
        return self._xf(c, ang, flip).transform_point(*p)

    def inlet(self, c, ang=0.0, flip=False):
        return self.point(self.inlet0, c, ang, flip)

    def draw(self, ctx, c, ang=0.0, flip=False, color=None, glass=None, path_only=False):
        """Fill the bonnet at centre c. glass: port glass colour (None = the look's)."""
        ctx.save()
        ctx.transform(self._xf(c, ang, flip))
        for fn, col, eo in self.pieces:
            ctx.new_path()
            fn(ctx)
            if path_only:
                ctx.set_source_rgb(*BLACK)
            elif col is not None:
                ctx.set_source_rgb(*(glass if glass is not None else col))
            else:
                ctx.set_source_rgb(*(color or (0.02, 0.025, 0.035)))
            ctx.fill()
        ctx.restore()


def corselet(sk, look):
    """The breastplate pieces (path fns) of the Mark V for skeleton sk, worn without the bonnet."""
    ps = costume._helmet(sk, look)
    n = Bonnet.N_CORSELET if look.opts.get("weights", False) else 2
    return ps[:n]


# ----------------------------------------------------------------------------- the client's coat
def coat_flap(sk, look, open_k, t, cover=None, seed=5):
    """The trench's loose front panel as a world polygon (ink). Hanging (open_k 0) it falls
    from the chest past the belt, a little ahead of it (covering point `cover`, e.g. the
    knife pommel); open_k 1: the wind presses it back flat against him. Draw over the figure."""
    H = sk.H
    J = sk.j
    fx = math.cos(sk.pose.yaw * D2R)
    fwd = 1.0 if fx >= 0 else -1.0
    prof = 1.0 - sk.side_w
    tor = F._torso_outline(sk, look, pad=0.012)
    chest_f, waist_f, pel_f, seat_f = tor[9], tor[10], tor[11], tor[12]
    hull = costume._skirt(sk, look, 0.66, 0.024, 3)
    lowest = max(p[1] for p in hull)
    low = [p for p in hull if p[1] > lowest - 0.06 * H]
    hem_f = max(low, key=lambda p: p[0] * fwd)
    # hanging: the panel bulges a little ahead of the belt (enough to hide what is there)
    belt_y = lerp(pel_f[1], waist_f[1], 0.45)
    bulge = 0.026 * H * prof
    bx = max(waist_f[0] * fwd, pel_f[0] * fwd) + bulge
    if cover is not None:
        bx = max(bx, cover[0] * fwd + 7.0 * prof)
        belt_y = min(belt_y, cover[1] + 4.0)
    hang = [(bx * fwd, belt_y - 0.02 * H), (bx * fwd - fwd * 0.004 * H, belt_y + 0.07 * H),
            (lerp(bx * fwd, hem_f[0], 0.55), lerp(belt_y + 0.07 * H, hem_f[1], 0.55)),
            (hem_f[0] + fwd * 0.004 * H, hem_f[1] - 0.004 * H)]
    # pressed back: flat on the body line (just behind its front), the lower panel streaming
    flat = [(waist_f[0] - fwd * 0.006 * H, belt_y - 0.02 * H), (pel_f[0] - fwd * 0.008 * H, belt_y + 0.07 * H),
            (lerp(seat_f[0], hem_f[0], 0.5) - fwd * 0.018 * H, lerp(belt_y + 0.07 * H, hem_f[1], 0.55)),
            (hem_f[0] - fwd * 0.02 * H, hem_f[1] - 0.03 * H)]
    k = clamp(open_k)
    pts = []
    for i, (a, b) in enumerate(zip(hang, flat)):
        fl = (0.010 * H * k * (1.0 - k * 0.5)) * noise1(t * 3.3 + i * 0.7, seed + i) * (i / 3.0)
        pts.append((lerp(a[0], b[0], k) + fl * fwd, lerp(a[1], b[1], k) - abs(fl) * 0.4))
    top = (chest_f[0] - fwd * 0.004 * H, chest_f[1])
    inner = [(J["pelvis"][0], hem_f[1] - 0.05 * H), (J["pelvis"][0], J["pelvis"][1]),
             (J["waist"][0], J["waist"][1]), (J["chest"][0], J["chest"][1])]
    return [top] + pts + inner


# ----------------------------------------------------------------------------- smoke
def smoke(f, t, src, t0, dur, n=7, wind=(-40.0, -14.0), seed=3, color=None, alpha=0.16, size=1.0):
    """A slow puff of cigar smoke from src (world) released over [t0, t0 + dur], drifting
    with `wind` (px/s), swelling and fading. Faint additive light (moonlit smoke)."""
    if t < t0:
        return
    col = color or PAL.moon
    with f.light(blur=7.0) as A:
        for i in range(n):
            te = t0 + dur * i / max(n - 1, 1)
            age = t - te
            if age < 0 or age > 3.2:
                continue
            h1, h2 = hash01(seed, i, 1), hash01(seed, i, 2)
            x = src[0] + wind[0] * age + 14.0 * size * noise1(age * 0.9 + i, seed) + (h1 - 0.5) * 10
            y = src[1] + wind[1] * age - 8.0 * size * age * h2
            r = size * (5.0 + 16.0 * age ** 0.8) * (0.8 + 0.4 * h2)
            a = alpha * smoothstep(0.0, 0.15, age) * (1.0 - smoothstep(0.8, 3.2, age))
            draw.glow_disc(A, (x, y), r, col, a, 0.35)
