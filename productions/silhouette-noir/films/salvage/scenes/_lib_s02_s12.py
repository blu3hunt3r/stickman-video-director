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
