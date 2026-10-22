"""Costume pieces for figure.draw_figure.

    pieces(sk, look) -> {slot: [(path_fn, color, even_odd), ...]}

Slots, in paint order (see figure.draw_figure):
    back      behind everything (a cloak seen from the front, long hair behind the back)
    behind    after the far limbs, before the torso
    over_legs after torso + near leg (coats, dresses, cloaks in profile)
    head      after the head (hair, hood + face, hats, helmet, beard)
    over_arm  after the near arm (capelets, a cloak seen from behind)
    top       last

Head pieces are defined twice, in PROFILE (x forward) and FRONT view, with the same number
of points in the same order, and blended by the head's yaw (figure.head_map). Units are
head heights: chin y=0, crown y=1. Body pieces are built from the solved joints.

Look options used here (Look(...) arguments):
    hair   : None | 'short' | 'slick' | 'bob' | 'long' | 'bun' | 'ponytail' | 'curly'
    hat    : None | 'fedora' | 'peaked' (captain/police) | 'flatcap' | 'watch' (beanie)
             | 'kerchief' (headscarf) | 'bowler'
    hood   : True for a pointed hood (with face cut-out), colored by colors['hood']
    cape   : None | 'capelet' | 'cloak' | 'long'   (colors['cape'])
    coat   : None | 'jacket' | 'trench' | 'long'   (colors['coat'])
    dress  : None | 'knee' | 'mid' | 'floor'       (colors['dress'])
    scarf  : True                                    (colors['scarf'])
    helmet : 'diver' (Mark V diving helmet + corselet; use shoes='lead', limb_scale~1.3)
    beard  : True
    opts   : {'glass': rgb (helmet port glass), 'weights': bool (diver's chest weights),
              'flow': 0..1 extra cloth flutter, 'collar': bool (trench collar up)}
Cloth flutter uses pose.extra['vel'] (world px/s, set by motion.Actor) and opts['flow'].
"""
import math

from . import draw
from .core import clamp, lerp, noise1

D2R = math.pi / 180.0


# ----------------------------------------------------------------------------- helpers
def _figure():
    from . import figure
    return figure


def _pairs(prof, front):
    assert len(prof) == len(front), (len(prof), len(front))
    return prof, front


def _line(pts, n):
    """n points spaced evenly along an open polyline."""
    return draw.resample(pts, n, closed=False)


def _hm(sk, prof, front, scale=1.0, flow=0.0):
    """Head-local shape -> world, with optional flutter of the low points (hair/hood tails)."""
    if flow:
        prof = [(x - flow * clamp(0.35 - y, 0.0, 1.2) * 0.55, y + flow * 0.05 * clamp(0.35 - y, 0, 1))
                for x, y in prof]
    return _figure().head_map(sk, prof, front, scale=scale)


def _smooth_path(pts, tension=0.5):
    return lambda c: draw.smooth(c, pts, close=True, tension=tension)


def _poly_path(pts):
    return lambda c: draw.poly(c, pts)


def _speed(sk):
    """Horizontal speed (world px/s, + = moving in the facing direction) and |v| in body heights/s."""
    v = sk.pose.extra.get("vel", (0.0, 0.0))
    fwd = math.cos(sk.pose.yaw * D2R)
    sgn = 1.0 if fwd >= 0 else -1.0
    vf = v[0] * sgn
    return vf, abs(vf) / max(sk.H, 1.0)


def _flow(sk, look, seed=0):
    """Cloth flutter amount 0..~1.2 from speed + wind, with a little noise."""
    vf, vh = _speed(sk)
    t = sk.pose.extra.get("t", 0.0)
    base = clamp(vh / 1.6, 0.0, 1.0) + look.opts.get("flow", 0.0)
    return base * (0.85 + 0.25 * noise1(t * 2.3, seed)) + 0.04 * noise1(t * 0.7, seed + 3)


def _hull(points):
    """Convex hull (Andrew's monotone chain), counter-clockwise."""
    pts = sorted(set((round(p[0], 3), round(p[1], 3)) for p in points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def leg_point(sk, s, u):
    """Point at fraction u along leg s: 0 hip, 0.5 knee, 1 ankle."""
    J = sk.j
    if u <= 0.5:
        return lerp(J["hip_" + s], J["knee_" + s], u / 0.5)
    return lerp(J["knee_" + s], J["ankle_" + s], (u - 0.5) / 0.5)


def _leg_radius(sk, u, look):
    b = sk.body
    if u <= 0.5:
        r = lerp(b.r_thigh[0], b.r_thigh[1], u / 0.5)
    else:
        r = lerp(b.calf, b.r_shin[1], (u - 0.5) / 0.5)
    return r * sk.H * look.limb_scale


def _leg_normal(sk, s, u):
    J = sk.j
    a, b = (J["hip_" + s], J["knee_" + s]) if u <= 0.5 else (J["knee_" + s], J["ankle_" + s])
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    return -dy / L, dx / L


# ----------------------------------------------------------------------------- hair
_HAIR = {
    "slick": _pairs(
        [(0.33, 0.86), (0.18, 1.00), (-0.08, 1.04), (-0.34, 0.95), (-0.50, 0.74), (-0.50, 0.50),
         (-0.40, 0.42), (-0.10, 0.62), (0.15, 0.80)],
        [(0.30, 0.84), (0.20, 1.00), (0.0, 1.04), (-0.20, 1.00), (-0.32, 0.86), (-0.35, 0.62),
         (-0.20, 0.70), (0.0, 0.80), (0.33, 0.70)]),
    "bob": _pairs(
        [(-0.32, 0.12), (-0.50, 0.24), (-0.55, 0.48), (-0.50, 0.74), (-0.32, 0.96), (-0.05, 1.06),
         (0.20, 1.02), (0.34, 0.90), (0.30, 0.80), (0.14, 0.78), (0.02, 0.70), (-0.06, 0.52),
         (-0.14, 0.32), (-0.20, 0.16)],
        [(0.44, 0.10), (0.50, 0.30), (0.50, 0.56), (0.45, 0.82), (0.28, 1.00), (0.0, 1.07),
         (-0.28, 1.00), (-0.45, 0.82), (-0.50, 0.56), (-0.50, 0.30), (-0.44, 0.10), (-0.34, 0.40),
         (0.0, 0.88), (0.34, 0.40)]),
    "long": _pairs(
        [(0.30, 0.92), (0.0, 1.07), (-0.36, 0.98), (-0.52, 0.72), (-0.56, 0.30), (-0.56, -0.20),
         (-0.50, -0.62), (-0.30, -0.66), (-0.24, -0.20), (-0.16, 0.20), (-0.04, 0.55), (0.12, 0.80)],
        [(0.0, 1.07), (0.40, 0.96), (0.50, 0.55), (0.54, -0.10), (0.52, -0.55), (0.36, -0.58),
         (0.34, 0.20), (0.0, 0.86), (-0.34, 0.20), (-0.36, -0.58), (-0.52, -0.55), (-0.54, -0.10)]),
    "bun": _pairs(
        [(0.32, 0.90), (0.10, 1.05), (-0.22, 1.04), (-0.42, 1.10), (-0.62, 1.04), (-0.66, 0.86),
         (-0.54, 0.74), (-0.48, 0.56), (-0.20, 0.60), (0.12, 0.80)],
        [(0.30, 0.86), (0.18, 1.02), (0.0, 1.06), (-0.12, 1.16), (0.0, 1.28), (0.14, 1.20),
         (0.06, 1.06), (-0.22, 1.00), (-0.32, 0.80), (0.0, 0.84)]),
    "ponytail": _pairs(
        [(0.32, 0.90), (0.06, 1.06), (-0.30, 1.00), (-0.46, 0.82), (-0.62, 0.70), (-0.72, 0.40),
         (-0.70, 0.05), (-0.60, 0.12), (-0.56, 0.48), (-0.40, 0.56), (-0.10, 0.66), (0.14, 0.80)],
        [(0.0, 1.06), (0.30, 1.00), (0.42, 0.80), (0.36, 0.60), (0.12, 0.86), (0.05, 0.98),
         (-0.05, 0.98), (-0.12, 0.86), (-0.36, 0.60), (-0.42, 0.80), (-0.30, 1.00), (-0.10, 1.06)]),
    "curly": _pairs(
        [(0.34, 0.86), (0.30, 1.04), (0.12, 1.16), (-0.12, 1.20), (-0.34, 1.14), (-0.52, 1.00),
         (-0.62, 0.80), (-0.62, 0.56), (-0.52, 0.38), (-0.30, 0.46), (-0.04, 0.64), (0.16, 0.80)],
        [(0.40, 0.70), (0.48, 0.90), (0.40, 1.08), (0.20, 1.20), (0.0, 1.22), (-0.20, 1.20),
         (-0.40, 1.08), (-0.48, 0.90), (-0.40, 0.70), (-0.20, 0.90), (0.0, 0.92), (0.20, 0.90)]),
}


# ----------------------------------------------------------------------------- hats
_HATS = {
    "fedora": _pairs(
        [(-0.62, 0.82), (-0.30, 0.76), (0.20, 0.74), (0.62, 0.70), (0.68, 0.72), (0.60, 0.76),
         (0.34, 0.80), (0.33, 1.02), (0.24, 1.17), (0.05, 1.13), (-0.18, 1.18), (-0.34, 1.10),
         (-0.38, 0.84), (-0.60, 0.86)],
        [(-0.66, 0.78), (-0.30, 0.74), (0.30, 0.74), (0.66, 0.78), (0.68, 0.81), (0.62, 0.83),
         (0.33, 0.84), (0.31, 1.02), (0.22, 1.16), (0.0, 1.12), (-0.22, 1.16), (-0.31, 1.02),
         (-0.33, 0.84), (-0.62, 0.83)]),
    "peaked": _pairs(
        [(0.66, 0.70), (0.52, 0.77), (0.36, 0.82), (0.37, 0.95), (0.48, 1.04), (0.30, 1.12),
         (-0.10, 1.13), (-0.44, 1.05), (-0.41, 0.95), (-0.40, 0.80), (-0.10, 0.78), (0.32, 0.73)],
        [(0.30, 0.72), (0.37, 0.79), (0.37, 0.84), (0.39, 0.96), (0.52, 1.04), (0.30, 1.11),
         (-0.30, 1.11), (-0.52, 1.04), (-0.39, 0.96), (-0.37, 0.84), (-0.37, 0.79), (0.0, 0.70)]),
    "flatcap": _pairs(
        [(0.60, 0.80), (0.42, 0.85), (0.30, 1.00), (0.02, 1.09), (-0.34, 1.04), (-0.48, 0.88),
         (-0.42, 0.78), (0.10, 0.78), (0.40, 0.76)],
        [(0.40, 0.80), (0.44, 0.92), (0.30, 1.06), (0.0, 1.10), (-0.30, 1.06), (-0.44, 0.92),
         (-0.40, 0.80), (0.0, 0.78), (0.20, 0.78)]),
    "watch": _pairs(
        [(0.35, 0.80), (0.30, 0.96), (0.10, 1.10), (-0.20, 1.10), (-0.42, 0.96), (-0.50, 0.74),
         (-0.46, 0.64), (-0.10, 0.70), (0.30, 0.74)],
        [(0.38, 0.74), (0.36, 0.94), (0.22, 1.08), (0.0, 1.12), (-0.22, 1.08), (-0.36, 0.94),
         (-0.38, 0.74), (0.0, 0.72), (0.20, 0.72)]),
    "bowler": _pairs(
        [(-0.52, 0.80), (0.0, 0.77), (0.56, 0.76), (0.52, 0.81), (0.33, 0.83), (0.30, 1.05),
         (0.08, 1.18), (-0.18, 1.16), (-0.34, 1.02), (-0.36, 0.84), (-0.50, 0.85)],
        [(-0.50, 0.80), (0.0, 0.78), (0.50, 0.80), (0.48, 0.84), (0.33, 0.85), (0.31, 1.04),
         (0.12, 1.17), (-0.12, 1.17), (-0.31, 1.04), (-0.33, 0.85), (-0.48, 0.84)]),
    "kerchief": _pairs(
        [(0.33, 0.90), (0.05, 1.08), (-0.40, 0.94), (-0.54, 0.62), (-0.48, 0.30), (-0.46, 0.04),
         (-0.38, -0.10), (-0.28, 0.10), (-0.04, 0.10), (0.16, 0.28), (0.20, 0.60), (0.27, 0.82)],
        [(0.0, 1.09), (0.44, 0.92), (0.50, 0.56), (0.42, 0.18), (0.20, -0.02), (0.06, -0.12),
         (-0.06, -0.12), (-0.20, -0.02), (-0.42, 0.18), (-0.50, 0.56), (-0.44, 0.92), (-0.20, 1.04)]),
}

# Hood (Little Red): drawn over the head, then the face is re-cut in ink on top.
_HOOD = _pairs(
    [(0.37, 0.93), (0.14, 1.12), (-0.24, 1.10), (-0.52, 0.98), (-0.74, 0.86), (-0.60, 0.70),
     (-0.56, 0.40), (-0.52, 0.06), (-0.46, -0.16), (-0.12, -0.22), (0.18, -0.18), (0.26, 0.10),
     (0.24, 0.50), (0.34, 0.80)],
    [(0.0, 1.15), (0.36, 1.06), (0.50, 0.82), (0.53, 0.50), (0.56, 0.18), (0.60, -0.08),
     (0.52, -0.20), (0.0, -0.22), (-0.52, -0.20), (-0.60, -0.08), (-0.56, 0.18), (-0.53, 0.50),
     (-0.50, 0.82), (-0.36, 1.06)])


def _face_mask():
    """Face region (profile: forehead, nose, lips, chin + jaw/cheek line; front: an oval)."""
    edge = [(0.30, 0.86), (0.35, 0.79), (0.37, 0.67), (0.385, 0.60), (0.345, 0.555), (0.375, 0.50),
            (0.44, 0.405), (0.385, 0.36), (0.37, 0.31), (0.39, 0.265), (0.355, 0.225), (0.375, 0.185),
            (0.33, 0.135), (0.355, 0.06), (0.30, 0.00)]
    inner = _line([(0.30, 0.00), (0.15, 0.03), (0.10, 0.30), (0.13, 0.62), (0.30, 0.86)], 17)[1:-1]
    prof = edge + inner
    n_right = len(edge)
    front = []
    for i in range(n_right):            # right half of an oval, top -> chin
        a = math.pi * i / (n_right - 1)
        front.append((0.27 * math.sin(a), 0.44 + 0.42 * math.cos(a)))
    m = len(inner)
    for i in range(m):                  # left half, chin -> top
        a = math.pi * (i + 1) / (m + 1)
        front.append((-0.27 * math.sin(a), 0.44 - 0.42 * math.cos(a)))
    return _pairs(prof, front)


_FACE = _face_mask()

_BEARD = _pairs(
    [(0.22, 0.42), (0.34, 0.30), (0.36, 0.10), (0.30, -0.12), (0.16, -0.20), (0.0, -0.10),
     (-0.10, 0.12), (-0.04, 0.42)],
    [(0.30, 0.45), (0.33, 0.12), (0.17, -0.18), (0.0, -0.24), (-0.17, -0.18), (-0.33, 0.12),
     (-0.30, 0.45), (0.0, 0.30)])


# ----------------------------------------------------------------------------- body pieces
def _skirt(sk, look, hem_u, flare, seed, top="waist"):
    """Skirt/coat-tail hull from the waist (or the chest for coats) down to hem_u along the legs."""
    fig = _figure()
    H = sk.H
    J = sk.j
    pts = []
    tor = fig._torso_outline(sk, look, pad=0.012)
    # torso outline: [crotch, back(seat, pelvis, waist, chest, shoulder, neck), front(neck..seat)]
    pts += [tor[1], tor[2], tor[3]]     # back: seat, pelvis, waist
    pts += [tor[-1], tor[-2], tor[-3]]  # front: seat, pelvis, waist
    fl = _flow(sk, look, seed)
    fwd = 1.0 if math.cos(sk.pose.yaw * D2R) >= 0 else -1.0
    for s in ("L", "R"):
        p = leg_point(sk, s, hem_u)
        nx, ny = _leg_normal(sk, s, hem_u)
        r = _leg_radius(sk, hem_u, look) + flare * H
        pts.append((p[0] + nx * r, p[1] + ny * r))
        pts.append((p[0] - nx * r, p[1] - ny * r))
    hull = _hull(pts)
    # flutter: push the trailing hem points backward and up a little
    if fl > 0.01:
        lowest = max(p[1] for p in hull)
        out = []
        for x, y in hull:
            k = clamp((y - (J["pelvis"][1] + 0.05 * H)) / max(lowest - J["pelvis"][1], 1.0))
            out.append((x - fwd * fl * 0.07 * H * k, y - fl * 0.025 * H * k))
        hull = out
    return hull


def _cloak(sk, look, kind):
    """Cloak hanging from the shoulders: (outline, slot)."""
    fig = _figure()
    H = sk.H
    J = sk.j
    body = sk.body
    w = sk.side_w
    fwd = 1.0 if math.cos(sk.pose.yaw * D2R) >= 0 else -1.0
    fl = _flow(sk, look, 11)
    t = sk.pose.extra.get("t", 0.0)
    length = {"capelet": 0.20, "cloak": 0.46, "long": 0.66}[kind] * H
    neck = J["neck"]
    chest = J["chest"]
    pel = J["pelvis"]
    top_y = neck[1] - 0.01 * H
    hem_y = neck[1] + length
    sw = body.shoulder_w * H * 1.25
    # ---- profile shape (x relative to neck, signed by facing)
    flutter = fl * 0.20 * H
    wave = noise1(t * 3.1, 5) * 0.025 * H * (0.3 + fl)
    prof = [
        (0.035 * H, top_y + 0.015 * H),                        # throat
        (0.075 * H, neck[1] + 0.06 * H),                        # front of shoulder
        (0.085 * H + 0.02 * H * fl, lerp(neck[1], hem_y, 0.55)),
        (0.070 * H + 0.03 * H * fl, hem_y),                     # front hem
        (-0.10 * H - flutter * 0.8, hem_y + 0.01 * H - fl * 0.06 * H + wave),
        (-0.15 * H - flutter, lerp(neck[1], hem_y, 0.82) - fl * 0.04 * H + wave),   # back hem corner
        (-0.12 * H - flutter * 0.5, lerp(neck[1], hem_y, 0.45)),
        (-0.075 * H - flutter * 0.1, neck[1] + 0.05 * H),       # back of shoulder
        (-0.03 * H, top_y),                                     # nape
    ]
    # ---- front shape (symmetric trapezoid hanging behind or over the body)
    hw = sw * (1.0 + 0.4 * (kind != "capelet"))
    front = [
        (0.30 * sw, top_y + 0.01 * H),
        (sw * 0.95, neck[1] + 0.06 * H),
        (hw * 1.05, lerp(neck[1], hem_y, 0.55)),
        (hw * 1.12, hem_y),
        (hw * 0.4, hem_y + 0.02 * H),
        (-hw * 0.4, hem_y + 0.02 * H),
        (-hw * 1.12, hem_y),
        (-sw * 0.95, neck[1] + 0.06 * H),
        (-0.30 * sw, top_y + 0.01 * H),
    ]
    pts = []
    for (px, py), (qx, qy) in zip(prof, front):
        x = lerp(px * fwd, qx, w)
        y = lerp(py, qy, w)
        pts.append((neck[0] + x, y))
    if w < 0.5:
        slot = "over_legs"
    elif sk.front > 0:
        slot = "back"
    else:
        slot = "over_arm"
    return pts, slot


def _scarf(sk, look):
    H = sk.H
    J = sk.j
    fwd = 1.0 if math.cos(sk.pose.yaw * D2R) >= 0 else -1.0
    fl = _flow(sk, look, 23)
    t = sk.pose.extra.get("t", 0.0)
    n0 = lerp(J["neck"], J["head_base"], 0.45)
    paths = [lambda c: draw.ellipse(c, n0, 0.052 * H, 0.030 * H)]
    # two tails trailing back
    for k in range(2):
        pts = [n0]
        x, y = n0
        ang = math.radians(100 + 18 * k - 55 * clamp(fl))   # from straight down toward back
        for i in range(1, 7):
            a = ang + 0.25 * noise1(t * 3.0 - i * 0.6, 31 + k) * (0.4 + fl)
            x += -fwd * math.sin(a) * 0.035 * H
            y += math.cos(a) * 0.035 * H
            pts.append((x, y))
        wid = [0.030 * H * (1 - 0.08 * i) for i in range(len(pts))]
        poly = draw.ribbon(pts, wid)
        paths.append(_poly_path(poly))
    return paths


# ----------------------------------------------------------------------------- diving dress
def helmet_frame(sk):
    """(center, R, viewport_center, viewport_r, inlet_point) of the Mark V helmet, world px."""
    fig = _figure()
    hh = sk.body.head * sk.H
    e1, e2, r, w, front = fig.eye_points(sk)
    center = fig.head_point(sk, -0.05, 0.50, front_x=0.0, front_y=0.50)
    vp = ((e1[0] + e2[0]) / 2, (e1[1] + e2[1]) / 2)
    vp = lerp(vp, center, 0.15)
    inlet = fig.head_point(sk, -0.78, 0.22, front_x=0.62, front_y=0.10)
    return center, 0.76 * hh, vp, 0.30 * hh, inlet


def helmet_inlet(sk):
    """World point where the air hose attaches (back of the helmet)."""
    return helmet_frame(sk)[4]


def helmet_lamp(sk):
    """(position, direction (unit), facing) of a lamp mounted on the helmet's top front."""
    fig = _figure()
    p = fig.head_point(sk, 0.40, 1.02, front_x=0.0, front_y=1.15)
    yaw = (sk.pose.yaw + sk.pose.head_yaw) * D2R
    ang = sk.head_ang * D2R
    fwd = math.cos(yaw)
    # aim along the head's forward axis, pitched by the head angle (+ = nod down)
    dx = math.cos(yaw) * math.cos(ang * 0.9)
    dy = math.sin(ang * 0.9) + 0.12
    L = math.hypot(dx, dy) or 1.0
    return p, (dx / L, dy / L), (1.0 if fwd >= 0 else -1.0)


def _helmet(sk, look):
    H = sk.H
    J = sk.j
    hh = sk.body.head * H
    w = sk.side_w
    fwd = 1.0 if math.cos((sk.pose.yaw + sk.pose.head_yaw) * D2R) >= 0 else -1.0
    c, R, vp, vr, inlet = helmet_frame(sk)
    out = []
    # corselet (breastplate) over the shoulders
    neck = J["neck"]
    chest = J["chest"]
    sw = sk.body.shoulder_w * H
    pw = lerp(0.115 * H, sw * 1.45, w)          # half width at the shoulders (profile: chest depth)
    top = c[1] + R * 0.55
    bot = lerp(neck[1], chest[1], 0.95)
    cx = lerp(neck[0], chest[0], 0.5) + lerp(0.008 * H * fwd, 0.0, w)
    cors = [(cx - pw * 0.55, top), (cx + pw * 0.55, top), (cx + pw * 1.0, top + (bot - top) * 0.35),
            (cx + pw * 0.92, bot), (cx - pw * 0.92, bot), (cx - pw * 1.0, top + (bot - top) * 0.35)]
    out.append((_smooth_path(cors, 0.25), None, False))
    # studs / wing nuts along the corselet rim (tiny bumps)
    def studs(ctx):
        for i in range(7):
            u = (i + 0.5) / 7
            x = cx + (u - 0.5) * 2 * pw * 0.95
            y = bot - 0.004 * H
            draw.circle(ctx, (x, y + 0.006 * H), 0.009 * H)
    out.append((studs, None, False))
    if look.opts.get("weights", False):
        def weights(ctx):
            for k in (-1, 1):
                x0 = cx + k * pw * lerp(0.95, 0.5, w) - 0.035 * H
                y0 = lerp(top, bot, 0.62)
                draw.rect(ctx, x0, y0, x0 + 0.07 * H, y0 + 0.075 * H)
        out.append((weights, None, False))
    # dome
    out.append((lambda ctx: draw.circle(ctx, c, R), None, False))
    # front port (protruding in profile, round in front view)
    port_c = lerp((c[0] + fwd * R * 0.98, vp[1]), vp, w)
    def port(ctx):
        # collar of the port: short cylinder seen from the side
        depth = R * 0.22 * (1 - w)
        draw.capsule(ctx, (port_c[0] - fwd * depth, port_c[1]), (port_c[0] + fwd * depth * 0.4, port_c[1]),
                     R * 0.46 * lerp(0.75, 1.0, w), R * 0.44 * lerp(0.75, 1.0, w))
    out.append((port, None, False))
    # side ports: bumps on the outline in front view, a ring in profile
    def sides(ctx):
        for k in (-1, 1):
            draw.circle(ctx, (c[0] + k * R * 0.98 * w, c[1] - R * 0.05), R * 0.30 * lerp(0.6, 1.0, w))
    out.append((sides, None, False))
    # top port / valve bump and the air inlet gooseneck at the back
    top_p = (c[0] + fwd * R * 0.35 * (1 - w), c[1] - R * 0.92)
    out.append((lambda ctx: draw.ellipse(ctx, top_p, R * 0.28, R * 0.20), None, False))
    out.append((lambda ctx: draw.capsule(ctx, lerp(c, inlet, 0.55), inlet, R * 0.13, R * 0.11), None, False))
    out.append((lambda ctx: draw.capsule(ctx, (c[0] - fwd * R * 0.80 * (1 - w), c[1] + R * 0.15),
                                         (c[0] - fwd * R * 1.08 * (1 - w), c[1] + R * 0.02), R * 0.11, R * 0.09),
                None, False))
    # viewport glass (lighter than ink) - eyes are drawn on top by figure.draw_eyes
    glass = look.opts.get("glass")
    if glass is not None:
        out.append((lambda ctx: draw.circle(ctx, lerp(vp, port_c, 0.5), vr), glass, False))
    return out


# ----------------------------------------------------------------------------- entry
def pieces(sk, look):
    """All costume pieces for this skeleton, grouped by paint slot."""
    S = {k: [] for k in ("back", "behind", "over_legs", "head", "over_arm", "top")}
    C = look.colors
    fig = _figure()
    H = sk.H
    w = sk.side_w
    # --- coats / dresses (body) -------------------------------------------------
    if look.dress:
        hem = {"knee": 0.52, "mid": 0.72, "floor": 0.98}.get(look.dress, 0.6)
        hull = _skirt(sk, look, hem, 0.030 if look.dress != "floor" else 0.045, 7)
        S["over_legs"].append((_smooth_path(hull, 0.18), C.get("dress"), False))
    if look.coat:
        hem = {"jacket": 0.22, "trench": 0.66, "long": 0.84}.get(look.coat, 0.6)
        hull = _skirt(sk, look, hem, 0.024, 3)
        tor = fig._torso_outline(sk, look, pad=0.012)
        col = C.get("coat")
        S["over_legs"].append((_smooth_path(tor, 0.42), col, False))
        S["over_legs"].append((_smooth_path(hull, 0.15), col, False))
        if look.coat == "trench" or look.opts.get("collar"):
            # popped collar points either side of the neck
            J = sk.j
            nk = J["neck"]
            hb = J["head_base"]
            fwd = 1.0 if math.cos(sk.pose.yaw * D2R) >= 0 else -1.0
            coll = [(nk[0] - fwd * 0.045 * H, nk[1] + 0.02 * H), (hb[0] - fwd * 0.055 * H, hb[1] - 0.012 * H),
                    (hb[0] - fwd * 0.012 * H, hb[1] + 0.012 * H), (nk[0] + fwd * 0.04 * H, nk[1] + 0.025 * H)]
            S["over_legs"].append((_poly_path(coll), col, False))
    # --- capes ------------------------------------------------------------------
    if look.cape:
        pts, slot = _cloak(sk, look, look.cape)
        if look.cape == "capelet" and slot == "over_legs":
            slot = "over_arm"
        S[slot].append((_smooth_path(pts, 0.35), C.get("cape"), False))
    if look.scarf:
        for p in _scarf(sk, look):
            S["over_arm"].append((p, C.get("scarf"), False))
    # --- head -------------------------------------------------------------------
    if look.helmet:
        S["head"] += _helmet(sk, look)
        return S
    fl = _flow(sk, look, 41)
    if look.hair in _HAIR:
        prof, front = _HAIR[look.hair]
        pts = _hm(sk, prof, front, flow=fl * (0.6 if look.hair in ("long", "ponytail") else 0.15))
        S["head"].append((_smooth_path(pts, 0.45), C.get("hair"), False))
    if look.beard:
        pts = _hm(sk, *_BEARD)
        S["head"].append((_smooth_path(pts, 0.45), C.get("beard"), False))
    if look.hood:
        pts = _hm(sk, *_HOOD, flow=fl * 0.35)
        S["head"].append((_smooth_path(pts, 0.42), C.get("hood"), False))
        if sk.front > -0.25:
            face = _hm(sk, *_FACE)
            S["head"].append((_smooth_path(face, 0.45), C.get("face", C.get("head")), False))
    if look.hat in _HATS:
        prof, front = _HATS[look.hat]
        pts = _hm(sk, prof, front)
        S["head"].append((_poly_path(pts) if look.hat in ("fedora", "peaked", "bowler") else _smooth_path(pts, 0.4),
                          C.get("hat"), False))
    return S
