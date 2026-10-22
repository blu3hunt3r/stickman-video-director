"""Silhouette humans: anatomical proportions, pseudo-3D skeleton (turns smoothly between
profile, three-quarter, front and back), filled body shapes, costumes and Limbo eyes.

    body = Body.adult_m(height=620)          # height in world px (feet to crown)
    look = Look(hat="fedora", coat="trench", eyes=True)
    sk = solve(pose, body)                    # Pose -> Skeleton (world joints)
    draw_figure(f, sk, look, layer_ctx)       # filled silhouette (+ glowing eyes)

Angles are degrees. Sagittal angles are measured from straight DOWN toward the body's
FORWARD direction (so +30 hip = thigh swung forward, +30 shoulder = arm swung forward).
Spine bends: + = bend forward. yaw: 0 = facing screen right, 180 = facing left,
90 = facing the camera, -90 = back to camera. Usually you do not build Poses by hand:
use engine.motion.Actor, which produces them from walks, runs, stands and keyed poses.
"""
import math
from copy import deepcopy

from . import draw
from .core import clamp, lerp, lerp_angle, hash01

D2R = math.pi / 180.0


# ----------------------------------------------------------------------------- body
class Body:
    """Proportions as fractions of total height (Drillis & Contini-style anthropometry),
    and silhouette radii for profile (front-back depth) and front (side-to-side) views."""

    def __init__(self, height=600.0, **kw):
        self.height = float(height)
        p = dict(
            hip=0.530, thigh=0.245, shin=0.246, ankle_h=0.039,
            heel_back=0.040, ball=0.104, toe=0.046,
            spine=(0.092, 0.100, 0.098), neck=0.048, head=0.134,
            shoulder_w=0.106, hip_w=0.052, shoulder_drop=0.016,
            upper_arm=0.186, forearm=0.146, hand=0.108,
            # radii (fraction of height)
            r_thigh=(0.060, 0.038), r_shin=(0.038, 0.021), calf=0.044,
            r_upper=(0.036, 0.027), r_fore=(0.028, 0.019), r_neck=0.031,
            # torso half-thickness in PROFILE (front of body, back of body) and half-width in
            # FRONT view, at six levels: seat, pelvis, waist, chest, shoulder, neck base
            torso_front=(0.034, 0.050, 0.050, 0.066, 0.050, 0.034),
            torso_back=(0.074, 0.066, 0.044, 0.058, 0.054, 0.036),
            torso_w=(0.100, 0.098, 0.084, 0.104, 0.130, 0.056),
            head_len=0.84, head_w=0.68, foot_scale=1.0, hand_scale=1.0,
        )
        p.update(kw)
        self.__dict__.update(p)

    def px(self, frac):
        return frac * self.height

    @property
    def leg(self):
        return (self.thigh + self.shin) * self.height

    @staticmethod
    def adult_m(height=620.0, **kw):
        return Body(height, **kw)

    @staticmethod
    def adult_f(height=590.0, **kw):
        d = dict(shoulder_w=0.096, hip_w=0.058, torso_w=(0.110, 0.104, 0.074, 0.094, 0.116, 0.050),
                 torso_front=(0.034, 0.046, 0.042, 0.076, 0.048, 0.032),
                 torso_back=(0.078, 0.068, 0.040, 0.052, 0.050, 0.034),
                 r_upper=(0.031, 0.023), r_fore=(0.024, 0.016), r_thigh=(0.062, 0.036),
                 r_shin=(0.035, 0.019), calf=0.040, r_neck=0.027, foot_scale=0.9, hand_scale=0.9)
        d.update(kw)
        return Body(height, **d)

    @staticmethod
    def child(height=380.0, **kw):
        """About seven years old: big head, short legs, slim limbs."""
        d = dict(hip=0.470, thigh=0.215, shin=0.219, ankle_h=0.036,
                 spine=(0.090, 0.098, 0.090), neck=0.040, head=0.165,
                 shoulder_w=0.098, hip_w=0.054, upper_arm=0.170, forearm=0.135, hand=0.100,
                 r_thigh=(0.058, 0.036), r_shin=(0.036, 0.022), calf=0.040,
                 r_upper=(0.033, 0.026), r_fore=(0.027, 0.020), r_neck=0.034,
                 torso_front=(0.036, 0.052, 0.058, 0.060, 0.050, 0.040),
                 torso_back=(0.062, 0.058, 0.046, 0.056, 0.054, 0.040),
                 torso_w=(0.092, 0.090, 0.088, 0.096, 0.128, 0.060), head_w=0.74, head_len=0.86,
                 foot_scale=1.05, hand_scale=1.05)
        d.update(kw)
        return Body(height, **d)

    @staticmethod
    def old_f(height=540.0, **kw):
        b = Body.adult_f(height, **kw)
        b.torso_back = (0.074, 0.066, 0.046, 0.066, 0.064, 0.044)     # rounded upper back
        return b

    @staticmethod
    def heavy_m(height=630.0, **kw):
        d = dict(shoulder_w=0.116, hip_w=0.058, torso_w=(0.112, 0.116, 0.118, 0.124, 0.142, 0.064),
                 torso_front=(0.040, 0.064, 0.088, 0.082, 0.056, 0.040),
                 torso_back=(0.078, 0.070, 0.052, 0.064, 0.060, 0.042),
                 r_thigh=(0.068, 0.042), r_shin=(0.042, 0.024), r_upper=(0.042, 0.032),
                 r_fore=(0.033, 0.023), r_neck=0.040)
        d.update(kw)
        return Body(height, **d)


# ----------------------------------------------------------------------------- pose
class Pose:
    """Joint angles + root. legs: each leg is either {'ik': (ax, ay), 'pitch': deg, 'toe': deg}
    (ankle world position, foot pitch relative to horizontal: + toes up) or FK angles
    {'hip': , 'abd': , 'knee': , 'ankle': , 'toe': }."""

    def __init__(self, x=0.0, y=0.0, yaw=0.0):
        self.x, self.y = float(x), float(y)       # pelvis center, world px
        self.yaw = float(yaw)
        self.pitch = 0.0                          # whole-trunk lean forward at the hips
        self.spine = [0.0, 0.0, 0.0]              # lower, mid, upper back bends (+ forward)
        self.neck = 0.0
        self.head = 0.0                           # head pitch (+ nod forward/down)
        self.head_yaw = 0.0                       # head turn relative to the body
        self.head_roll = 0.0
        self.arms = {"L": dict(sh=6.0, abd=5.0, elbow=12.0, wrist=0.0, grip=0.3),
                     "R": dict(sh=-4.0, abd=5.0, elbow=10.0, wrist=0.0, grip=0.3)}
        self.legs = {"L": dict(hip=0.0, abd=3.0, knee=2.0, ankle=0.0, toe=0.0),
                     "R": dict(hip=0.0, abd=3.0, knee=2.0, ankle=0.0, toe=0.0)}
        self.eyes = dict(open=1.0, glow=1.0, look=0.0)   # look: -1..1 gaze shift
        self.scale = 1.0                          # extra uniform scale (fake depth moves)
        self.extra = {}                           # free slot for scene data (e.g. prop angles)

    def copy(self):
        return deepcopy(self)


def _lerp_leg(a, b, t, ik_solve=None):
    if "ik" in a and "ik" in b:
        return dict(ik=lerp(a["ik"], b["ik"], t), pitch=lerp(a.get("pitch", 0.0), b.get("pitch", 0.0), t),
                    toe=lerp(a.get("toe", 0.0), b.get("toe", 0.0), t),
                    abd=lerp(a.get("abd", 3.0), b.get("abd", 3.0), t))
    if "ik" in a or "ik" in b:
        a = ik_solve(a) if "ik" in a else a
        b = ik_solve(b) if "ik" in b else b
    return {k: lerp(a.get(k, 0.0), b.get(k, 0.0), t) for k in ("hip", "abd", "knee", "ankle", "toe")}


def blend(a, b, t, body=None):
    """Interpolate two poses (t = 0 -> a, 1 -> b). IK legs blend in world space."""
    if t <= 0.0:
        return a
    if t >= 1.0:
        return b
    p = a.copy()
    p.x, p.y = lerp(a.x, b.x, t), lerp(a.y, b.y, t)
    p.yaw = lerp_angle(a.yaw, b.yaw, t)
    p.pitch = lerp(a.pitch, b.pitch, t)
    p.spine = [lerp(x, y, t) for x, y in zip(a.spine, b.spine)]
    for k in ("neck", "head", "head_yaw", "head_roll", "scale"):
        setattr(p, k, lerp(getattr(a, k), getattr(b, k), t))
    for s in ("L", "R"):
        p.arms[s] = {k: lerp(a.arms[s].get(k, 0.0), b.arms[s].get(k, 0.0), t) for k in set(a.arms[s]) | set(b.arms[s])}

        def ik_solve(leg, pose_src=None, s=s):
            src = a if leg is a.legs[s] else b
            return leg_ik_angles(src, s, body) if body is not None else dict(hip=0, abd=3, knee=0, ankle=0, toe=0)
        p.legs[s] = _lerp_leg(a.legs[s], b.legs[s], t, ik_solve)
    for k in set(a.eyes) | set(b.eyes):
        p.eyes[k] = lerp(a.eyes.get(k, 0.0), b.eyes.get(k, 0.0), t)
    return p


# ----------------------------------------------------------------------------- skeleton solve
def _dir(phi_deg):
    """Sagittal direction for an angle measured from straight down toward forward."""
    r = phi_deg * D2R
    return math.sin(r), -math.cos(r)        # (forward, up)


class Skeleton:
    """World-space joints of a solved pose. Points are (x, y) world px; .z holds depth
    (+ toward the camera) for draw ordering. Use .j['wrist_R'] etc. for props."""

    def __init__(self):
        self.j = {}
        self.z = {}

    def __getitem__(self, k):
        return self.j[k]


def _project(pose, body, f_, u_, l_):
    """Body-local (forward, up, left) in body-height units -> world (x, y) and depth z."""
    H = body.height * pose.scale
    yaw = pose.yaw * D2R
    cy, sy = math.cos(yaw), math.sin(yaw)
    # forward F = (cos yaw, 0, sin yaw); left L = (sin yaw, 0, -cos yaw); up = -y
    x = pose.x + H * (f_ * cy + l_ * sy)
    z = H * (f_ * sy - l_ * cy)
    y = pose.y - H * u_
    return (x, y), z


def leg_ik_angles(pose, side, body):
    """Convert an IK leg ({'ik': ankle world pos}) to FK angles for this pose."""
    leg = pose.legs[side]
    if "ik" not in leg:
        return leg
    H = body.height * pose.scale
    cyaw = math.cos(pose.yaw * D2R)
    sgn = 1.0 if cyaw >= 0 else -1.0
    k = max(abs(cyaw), 0.25)
    ax, ay = leg["ik"]
    # target in sagittal local units relative to the hip joint (hip at pelvis height)
    tf = (ax - pose.x) / (H * k) * sgn
    tu = (pose.y - ay) / H
    L1, L2 = body.thigh, body.shin
    d = math.hypot(tf, tu)
    d = clamp(d, abs(L1 - L2) + 1e-4, (L1 + L2) * 0.9995)
    phi_v = math.atan2(tf, -tu) / D2R
    cosb = clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1.0, 1.0)
    beta = math.acos(cosb) / D2R
    hip = phi_v + beta
    kf, ku = _dir(hip)
    kf, ku = kf * L1, ku * L1
    shin = math.atan2(tf - kf, -(tu - ku)) / D2R
    knee = hip - shin
    pitch = leg.get("pitch", 0.0)
    ankle = (90.0 + pitch) - shin - 90.0
    return dict(hip=hip, abd=leg.get("abd", 3.0), knee=knee, ankle=ankle, toe=leg.get("toe", 0.0))


def solve(pose, body):
    """Pose -> Skeleton with world joint positions (and limb angle info for drawing)."""
    sk = Skeleton()
    sk.pose, sk.body = pose, body
    J, Z = sk.j, sk.z
    sp = body.spine
    a = pose.pitch + pose.spine[0]
    pts = [(0.0, 0.0)]
    angs = []
    for i, L in enumerate(sp):
        if i > 0:
            a += pose.spine[i]
        angs.append(a)
        f0, u0 = pts[-1]
        df, du = math.sin(a * D2R), math.cos(a * D2R)
        pts.append((f0 + df * L, u0 + du * L))
    chest_ang = angs[-1]
    neck_ang = chest_ang + pose.neck
    nf, nu = pts[-1]
    hb = (nf + math.sin(neck_ang * D2R) * body.neck, nu + math.cos(neck_ang * D2R) * body.neck)
    head_ang = neck_ang + pose.head
    names = ["pelvis", "waist", "chest", "neck"]
    for nm, (f_, u_) in zip(names, pts):
        J[nm], Z[nm] = _project(pose, body, f_, u_, 0.0)
    J["head_base"], Z["head_base"] = _project(pose, body, hb[0], hb[1], 0.0)
    sk.spine_angs = angs
    sk.head_ang = head_ang
    sk.local = dict(spine=pts, head_base=hb)
    # shoulders / arms
    sd = body.shoulder_drop
    sh_f = nf - math.sin(chest_ang * D2R) * sd
    sh_u = nu - math.cos(chest_ang * D2R) * sd
    for s, side in (("L", 1.0), ("R", -1.0)):
        arm = pose.arms[s]
        l0 = side * body.shoulder_w
        J["shoulder_" + s], Z["shoulder_" + s] = _project(pose, body, sh_f, sh_u, l0)
        abd = arm.get("abd", 8.0) * D2R
        phi_u = chest_ang + arm.get("sh", 0.0)
        df, du = _dir(phi_u)
        ef, eu, el = sh_f + df * math.cos(abd) * body.upper_arm, sh_u + du * math.cos(abd) * body.upper_arm, \
            l0 + side * math.sin(abd) * body.upper_arm
        J["elbow_" + s], Z["elbow_" + s] = _project(pose, body, ef, eu, el)
        phi_f = phi_u + arm.get("elbow", 0.0)
        df2, du2 = _dir(phi_f)
        wf, wu, wl = ef + df2 * math.cos(abd) * body.forearm, eu + du2 * math.cos(abd) * body.forearm, \
            el + side * math.sin(abd) * body.forearm
        J["wrist_" + s], Z["wrist_" + s] = _project(pose, body, wf, wu, wl)
        phi_h = phi_f + arm.get("wrist", 0.0)
        df3, du3 = _dir(phi_h)
        hl = body.hand * body.hand_scale
        J["hand_" + s], Z["hand_" + s] = _project(pose, body, wf + df3 * hl * 0.55, wu + du3 * hl * 0.55, wl)
        J["fingers_" + s], Z["fingers_" + s] = _project(pose, body, wf + df3 * hl, wu + du3 * hl, wl)
        sk.__dict__["hand_ang_" + s] = phi_h
        sk.__dict__["fore_ang_" + s] = phi_f
    # legs
    for s, side in (("L", 1.0), ("R", -1.0)):
        leg = leg_ik_angles(pose, s, body) if "ik" in pose.legs[s] else pose.legs[s]
        l0 = side * body.hip_w
        J["hip_" + s], Z["hip_" + s] = _project(pose, body, 0.0, 0.0, l0)
        abd = leg.get("abd", 3.0) * D2R
        phi_t = leg["hip"]
        df, du = _dir(phi_t)
        kf, ku, kl = df * math.cos(abd) * body.thigh, du * math.cos(abd) * body.thigh, l0 + side * math.sin(abd) * body.thigh
        J["knee_" + s], Z["knee_" + s] = _project(pose, body, kf, ku, kl)
        phi_s = phi_t - leg["knee"]
        df2, du2 = _dir(phi_s)
        af, au, al = kf + df2 * math.cos(abd) * body.shin, ku + du2 * math.cos(abd) * body.shin, \
            kl + side * math.sin(abd) * body.shin
        J["ankle_" + s], Z["ankle_" + s] = _project(pose, body, af, au, al)
        phi_foot = phi_s + 90.0 + leg.get("ankle", 0.0)
        sk.__dict__["foot_ang_" + s] = phi_foot
        sk.__dict__["toe_ang_" + s] = phi_foot + leg.get("toe", 0.0)
        sk.__dict__["shin_ang_" + s] = phi_s
        sk.__dict__["foot_local_" + s] = (af, au, al)
        fdf, fdu = _dir(phi_foot)
        J["ball_" + s], Z["ball_" + s] = _project(pose, body, af + fdf * body.ball + fdu * body.ankle_h,
                                                  au + fdu * body.ball - fdf * body.ankle_h, al)
        J["heel_" + s], Z["heel_" + s] = _project(pose, body, af - fdf * body.heel_back + fdu * body.ankle_h,
                                                  au - fdu * body.heel_back - fdf * body.ankle_h, al)
    # head center & eyes (local)
    hh = body.head
    hf = hb[0] + math.sin(head_ang * D2R) * hh * 0.42
    hu = hb[1] + math.cos(head_ang * D2R) * hh * 0.42
    J["head"], Z["head"] = _project(pose, body, hf, hu, 0.0)
    J["crown"], Z["crown"] = _project(pose, body, hb[0] + math.sin(head_ang * D2R) * hh * 0.9,
                                      hb[1] + math.cos(head_ang * D2R) * hh * 0.9, 0.0)
    sk.H = body.height * pose.scale
    sk.facing = 1.0 if math.cos(pose.yaw * D2R) >= 0 else -1.0
    sk.side_w = abs(math.sin(pose.yaw * D2R))         # 0 profile .. 1 front/back
    sk.front = math.sin(pose.yaw * D2R)               # + facing camera, - back to camera
    return sk


# ----------------------------------------------------------------------------- head shapes
# Profile (facing +x), units of head height, chin y=0 .. crown y=1, origin under the skull.
_HEAD_PROFILE = [
    (0.00, 1.00), (0.17, 0.975), (0.29, 0.90), (0.35, 0.79), (0.37, 0.67), (0.385, 0.60),
    (0.345, 0.555), (0.375, 0.50), (0.44, 0.405), (0.385, 0.36), (0.37, 0.31), (0.39, 0.265),
    (0.355, 0.225), (0.375, 0.185), (0.33, 0.135), (0.355, 0.06), (0.30, 0.00), (0.17, 0.02),
    (0.06, 0.09), (-0.06, 0.15), (-0.24, 0.20), (-0.40, 0.36), (-0.47, 0.52), (-0.46, 0.70),
    (-0.38, 0.86), (-0.22, 0.96),
]
# Front view (symmetric), same point count / order (crown, right side down, chin, left up)
_HEAD_FRONT = [
    (0.00, 1.00), (0.15, 0.98), (0.26, 0.92), (0.32, 0.83), (0.34, 0.72), (0.345, 0.62),
    (0.36, 0.56), (0.355, 0.47), (0.32, 0.40), (0.30, 0.33), (0.27, 0.26), (0.23, 0.18),
    (0.17, 0.10), (0.09, 0.03), (0.0, 0.0), (-0.09, 0.03), (-0.17, 0.10),
    (-0.23, 0.18), (-0.27, 0.26), (-0.32, 0.40), (-0.355, 0.47), (-0.36, 0.56),
    (-0.345, 0.62), (-0.34, 0.72), (-0.32, 0.83), (-0.20, 0.95),
]
_HEAD_PIVOT = (-0.06, 0.17)        # where the neck meets the skull (head-local)


def head_frame(sk, extra_yaw=0.0):
    """(w, fac, hh, ca, sa, roll, hb): blend weight profile->front, facing sign, head
    height px, head pitch cos/sin, roll, head-base world point."""
    pose, body = sk.pose, sk.body
    yaw = (pose.yaw + pose.head_yaw + extra_yaw) * D2R
    w = abs(math.sin(yaw))
    fac = 1.0 if math.cos(yaw) >= 0 else -1.0
    hh = body.head * sk.H
    ang = sk.head_ang * D2R
    return w, fac, hh, math.cos(ang), math.sin(ang), pose.head_roll * D2R, sk.j["head_base"]


def head_map(sk, prof, front=None, extra_yaw=0.0, scale=1.0):
    """Map head-local points to world. prof: profile points (x forward, y up; head height
    units, chin y=0, crown y=1). front: matching front-view points (same count) or None
    (then the profile shape is reused, centered). Blends by the head's yaw."""
    w, fac, hh, ca, sa, roll, hb = head_frame(sk, extra_yaw)
    hh *= scale
    out = []
    front = front or prof
    for (px, py), (qx, qy) in zip(prof, front):
        # profile: rotate about the neck pivot by the head pitch
        x0, y0 = px - _HEAD_PIVOT[0], py - _HEAD_PIVOT[1]
        xp, yp = x0 * ca + y0 * sa, -x0 * sa + y0 * ca
        # front: nodding only foreshortens vertically
        y1 = qy - _HEAD_PIVOT[1]
        xf, yf = qx, y1 * ca
        x, y = lerp(xp, xf, w), lerp(yp, yf, w)
        if roll:
            x, y = x * math.cos(roll) - y * math.sin(roll), x * math.sin(roll) + y * math.cos(roll)
        out.append((hb[0] + fac * x * hh, hb[1] - y * hh))
    return out


def head_outline(sk, extra_yaw=0.0, scale=1.0):
    body = sk.body
    prof = [(x * body.head_len / 0.84, y) for x, y in _HEAD_PROFILE]
    front = [(x * body.head_w / 0.68, y) for x, y in _HEAD_FRONT]
    return head_map(sk, prof, front, extra_yaw, scale)


def head_point(sk, hx, hy, front_x=None, front_y=None):
    """World position of one head-local point (profile coords; front_x/front_y in front view)."""
    return head_map(sk, [(hx, hy)], [(front_x if front_x is not None else 0.0,
                                      front_y if front_y is not None else hy)])[0]


# ----------------------------------------------------------------------------- look / costume
class Look:
    """What the silhouette wears. Every part is filled with `ink` unless a color is given
    (e.g. hood=RED). Shapes are deliberately iconic: a figure must be recognizable from
    its outline alone (hat, coat, hood, helmet, hair)."""

    def __init__(self, ink=None, hair=None, hat=None, coat=None, dress=None, hood=None,
                 cape=None, scarf=None, shoes="shoe", eyes=True, eye_color=(1.0, 1.0, 0.97),
                 eye_size=1.0, gloves=False, colors=None, helmet=None, extras=None,
                 limb_scale=1.0, belly=0.0, beard=False, skirt_len=0.0, opts=None, paper=False):
        self.ink = ink
        self.hair, self.hat, self.coat, self.dress = hair, hat, coat, dress
        self.hood, self.cape, self.scarf = hood, cape, scarf
        self.shoes, self.eyes, self.eye_color, self.eye_size = shoes, eyes, eye_color, eye_size
        self.gloves, self.helmet = gloves, helmet
        self.colors = colors or {}          # part -> rgb, e.g. {"hood": RED, "cape": RED}
        self.extras = extras or []          # callables (ctx, sk, f, look) drawn after the body
        self.limb_scale = limb_scale        # >1 for bulky suits
        self.belly = belly
        self.beard = beard
        self.skirt_len = skirt_len
        self.opts = opts or {}              # costume options (see costume.py)
        self.paper = paper                  # paper-doll puppet: cut-paper edges, pin joints

    def col(self, part, default):
        return self.colors.get(part, self.ink if self.ink is not None else default)


# ----------------------------------------------------------------------------- drawing
def _torso_outline(sk, look, pad=0.0):
    """Torso outline in WORLD space. Six levels along the projected spine (seat, pelvis,
    waist, chest, shoulder, neck base); at each, screen-space offsets on the facing side and
    the opposite side blend from profile thickness (chest ahead, back/buttocks behind) to
    frontal half-width by how much the body is turned toward/away from the camera.
    pad: extra thickness (fraction of height) all round, for coats."""
    body, pose = sk.body, sk.pose
    H = sk.H
    w = sk.side_w
    J = sk.j
    tf, tb, tw = body.torso_front, body.torso_back, body.torso_w
    belly = look.belly if look else 0.0
    bulk = (look.limb_scale - 1.0) * 0.6 + 1.0 if look else 1.0
    sp = [J["pelvis"], J["waist"], J["chest"], J["neck"]]
    # spine tangent (pointing up the spine) at the pelvis, for the seat level below it
    tx, ty = sp[1][0] - sp[0][0], sp[1][1] - sp[0][1]
    L = math.hypot(tx, ty) or 1.0
    ux, uy = tx / L, ty / L
    seat = (sp[0][0] - ux * 0.058 * H, sp[0][1] - uy * 0.058 * H)
    shoulder = lerp(sp[2], sp[3], 0.62)
    centers = [seat, sp[0], sp[1], sp[2], shoulder, sp[3]]
    # tangents for the normals: use the spine segment around each level
    seg = [(sp[0], sp[1]), (sp[0], sp[1]), (sp[0], sp[2]), (sp[1], sp[3]), (sp[2], sp[3]), (sp[2], sp[3])]
    fwd_x = math.cos(pose.yaw * D2R)
    front_side, back_side = [], []
    for i, p in enumerate(centers):
        a, b = seg[i]
        dx, dy = b[0] - a[0], b[1] - a[1]
        Ls = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / Ls, dx / Ls
        if nx * fwd_x < 0 or (abs(fwd_x) < 1e-6 and nx < 0):
            nx, ny = -nx, -ny
        ff = tf[i] + (belly if i == 2 else belly * 0.6 if i in (1, 3) else 0.0)
        fw = (lerp(ff, tw[i], w) * bulk + pad) * H
        bw = (lerp(tb[i], tw[i], w) * bulk + pad) * H
        front_side.append((p[0] + nx * fw, p[1] + ny * fw))
        back_side.append((p[0] - nx * bw, p[1] - ny * bw))
    crotch = (seat[0] - ux * 0.012 * H, seat[1] - uy * 0.012 * H)
    return [crotch] + back_side + front_side[::-1]


def _limb(ctx, a, b, ra, rb):
    draw.capsule(ctx, a, b, ra, rb)


def _foot_shape(sk, s, shoe="shoe"):
    """Shoe outline (world) for leg s, with toe bend at the ball."""
    body = sk.body
    H = sk.H * body.foot_scale
    ax, ay = sk.j["ankle_" + s]
    yaw = sk.pose.yaw * D2R
    cy = math.cos(yaw)
    k = abs(cy)
    sgn = 1.0 if cy >= 0 else -1.0
    phi = sk.__dict__["foot_ang_" + s]
    tphi = sk.__dict__["toe_ang_" + s]
    # foot axis in the sagittal plane, projected: forward component shrinks with k
    def P(fx, fy, ang):
        # (fx forward along foot, fy downward from the ankle) for a foot at sagittal angle ang
        dx, du = math.sin(ang * D2R), -math.cos(ang * D2R)      # direction of +fx
        nx, nu = -du, dx                                         # rotate 90: toward "up" side
        # downward = -n
        lf = dx * fx - nx * fy
        lu = du * fx - nu * fy
        return ax + sgn * lf * H * max(k, 0.32), ay - lu * H
    if shoe == "lead":       # diver's lead boot: big block
        sole = [(-0.055, -0.010), (0.02, -0.035), (0.11, -0.02), (0.16, 0.02), (0.165, 0.05),
                (-0.06, 0.05), (-0.07, 0.02)]
        return [P(x, y, phi) for x, y in sole]
    if shoe == "heel":
        heel = [(-0.030, -0.018), (0.03, -0.022), (0.085, 0.004)]
        toe = [(0.105, 0.012), (0.14, 0.03), (0.13, 0.040), (0.10, 0.036)]
        back = [(-0.010, 0.032), (-0.022, 0.050), (-0.036, 0.050), (-0.040, 0.010)]
    elif shoe == "boot":
        heel = [(-0.036, -0.06), (0.03, -0.065), (0.04, -0.01), (0.09, 0.006)]
        toe = [(0.105, 0.014), (0.142, 0.030), (0.138, 0.044), (0.104, 0.044)]
        back = [(-0.042, 0.044), (-0.046, 0.02)]
    elif shoe == "bare":
        heel = [(-0.025, -0.015), (0.03, -0.015), (0.08, 0.008)]
        toe = [(0.104, 0.016), (0.14, 0.030), (0.132, 0.040), (0.10, 0.040)]
        back = [(-0.03, 0.040), (-0.042, 0.022)]
    else:
        heel = [(-0.030, -0.016), (0.03, -0.022), (0.085, 0.004)]
        toe = [(0.104, 0.013), (0.140, 0.028), (0.136, 0.042), (0.104, 0.043)]
        back = [(-0.036, 0.043), (-0.044, 0.020)]
    out = [P(x, y, phi) for x, y in heel]
    # toe points bend around the ball (0.104, ~0.03)
    bx, by = 0.104, 0.03
    pfx, pfy = P(bx, by, phi)
    dx, du = math.sin(tphi * D2R), -math.cos(tphi * D2R)
    for x, y in toe:
        rx, ry = x - bx, y - by
        lf = dx * rx + du * ry
        lu = du * rx - dx * ry
        out.append((pfx + sgn * lf * H * max(k, 0.32), pfy - lu * H))
    out += [P(x, y, phi) for x, y in back]
    return out


def _hand(ctx, sk, s, look, grip=0.3):
    """Mitten hand: palm capsule + fingers (curled by grip 0..1) + thumb."""
    body = sk.body
    H = sk.H * body.hand_scale
    w = sk.j["wrist_" + s]
    ang = sk.__dict__["hand_ang_" + s]
    yaw = sk.pose.yaw * D2R
    cy = math.cos(yaw)
    k = max(abs(cy), 0.45)
    sgn = 1.0 if cy >= 0 else -1.0

    def P(f_, u_):
        return w[0] + sgn * f_ * H * k, w[1] - u_ * H

    df, du = _dir(ang)
    palm = 0.056
    kn = P(df * palm, du * palm)
    r0 = body.r_fore[1] * sk.H * 0.95 * look.limb_scale
    _limb(ctx, w, kn, r0, r0 * 1.02)
    # fingers curl toward the palm side (forward/up for a relaxed hand)
    curl = lerp(10.0, 120.0, clamp(grip))
    fa = ang + curl * 0.6
    f1f, f1u = _dir(fa)
    fl = 0.045 * (1 - 0.35 * grip)
    tip = (kn[0] + sgn * f1f * fl * H * k, kn[1] - f1u * fl * H)
    _limb(ctx, kn, tip, r0 * 0.92, r0 * 0.72)
    # thumb
    ta = ang + 55.0
    t1f, t1u = _dir(ta)
    th0 = P(df * 0.02, du * 0.02)
    th1 = (th0[0] + sgn * t1f * 0.035 * H * k, th0[1] - t1u * 0.035 * H)
    _limb(ctx, th0, th1, r0 * 0.55, r0 * 0.42)


def _near_far(sk, a, b):
    """Return (far, near) of two limb keys by depth."""
    za = sk.z.get(a, 0.0)
    zb = sk.z.get(b, 0.0)
    return (a, b) if za <= zb else (b, a)


def _leg_path(ctx, sk, s, look):
    body, H, ls = sk.body, sk.H, look.limb_scale
    J = sk.j
    hip, knee, ank = J["hip_" + s], J["knee_" + s], J["ankle_" + s]
    rt0, rt1 = body.r_thigh
    rs0, rs1 = body.r_shin
    _limb(ctx, hip, knee, rt0 * H * ls, rt1 * H * ls)
    mid = lerp(knee, ank, 0.32)
    _limb(ctx, knee, mid, rs0 * H * ls, body.calf * H * ls)
    _limb(ctx, mid, ank, body.calf * H * ls, rs1 * H * ls)


def _arm_path(ctx, sk, s, look):
    body, H, ls = sk.body, sk.H, look.limb_scale
    J = sk.j
    sh, el, wr = J["shoulder_" + s], J["elbow_" + s], J["wrist_" + s]
    ru0, ru1 = body.r_upper
    rf0, rf1 = body.r_fore
    _limb(ctx, sh, el, ru0 * H * ls, ru1 * H * ls)
    _limb(ctx, el, wr, rf0 * H * ls, rf1 * H * ls)


def _torso_path(ctx, sk, look):
    body, H = sk.body, sk.H
    draw.smooth(ctx, _torso_outline(sk, look), close=True, tension=0.42)
    _limb(ctx, sk.j["neck"], sk.j["head_base"], body.r_neck * H * look.limb_scale * 1.1, body.r_neck * H * 0.95)


def draw_figure(f, sk, look=None, ctx=None, color=None, eyes=True, alpha=1.0):
    """Draw a solved Skeleton as a filled silhouette on `ctx` (a layer context) with its
    costume, plus glowing Limbo eyes (dots on ctx, halo on f.emit()).

    Paint order (far to near): back costume -> far leg/arm -> behind costume -> torso ->
    near leg -> coat/dress -> head -> hair/hood/hat -> near arm -> capelet -> top.
    alpha < 1 fades the whole figure as one shape (no darker overlaps)."""
    from . import costume
    look = look or Look()
    pal = f.pal if f is not None else None
    ink = color or look.ink or (pal.ink if pal is not None else (0, 0, 0))
    ctx = ctx if ctx is not None else f.ctx
    slots = costume.pieces(sk, look)
    grouped = alpha < 0.999
    if grouped:
        ctx.push_group()
    seed = [0]

    def paint(fn, col, even_odd=False):
        if even_odd:
            ctx.set_fill_rule(1)       # cairo.FILL_RULE_EVEN_ODD
        fn(ctx)
        if look.paper:
            polys = draw.flatten_path(ctx)
            ctx.new_path()
            for poly in polys:
                if len(poly) >= 3:
                    seed[0] += 1
                    draw.poly(ctx, draw.cut_paper(poly, seed=seed[0] * 13 + 5, amp=1.2 * sk.H / 600.0,
                                                  seg=(9.0 * sk.H / 600.0, 22.0 * sk.H / 600.0)))
        draw.fill(ctx, col or ink, 1.0)
        if even_odd:
            ctx.set_fill_rule(0)

    def slot(name):
        for item in slots.get(name, []):
            paint(*item)

    C = look.colors
    far_leg, near_leg = [k[-1] for k in _near_far(sk, "knee_L", "knee_R")]
    far_arm, near_arm = [k[-1] for k in _near_far(sk, "elbow_L", "elbow_R")]
    slot("back")
    paint(lambda c: _leg_path(c, sk, far_leg, look), C.get("leg"))
    paint(lambda c: draw.poly(c, _foot_shape(sk, far_leg, look.shoes)), C.get("foot"))
    paint(lambda c: _arm_path(c, sk, far_arm, look), C.get("arm"))
    paint(lambda c: _hand(c, sk, far_arm, look, sk.pose.arms[far_arm].get("grip", 0.3)), C.get("hand"))
    slot("behind")
    paint(lambda c: _torso_path(c, sk, look), C.get("torso"))
    paint(lambda c: _leg_path(c, sk, near_leg, look), C.get("leg"))
    paint(lambda c: draw.poly(c, _foot_shape(sk, near_leg, look.shoes)), C.get("foot"))
    slot("over_legs")
    if not look.helmet:
        paint(lambda c: draw.smooth(c, head_outline(sk), close=True, tension=0.5), C.get("head"))
    slot("head")
    paint(lambda c: _arm_path(c, sk, near_arm, look), C.get("arm"))
    paint(lambda c: _hand(c, sk, near_arm, look, sk.pose.arms[near_arm].get("grip", 0.3)), C.get("hand"))
    slot("over_arm")
    slot("top")
    for ex in look.extras:
        ex(ctx, sk, f, look)
    if grouped:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(clamp(alpha))
    if eyes and look.eyes:
        draw_eyes(f, sk, look, ctx, alpha=alpha)


def eye_points(sk, look=None):
    """World positions of the two eyes (near, far), radius, profile->front weight, facing."""
    pose = sk.pose
    yaw = (pose.yaw + pose.head_yaw) * D2R
    w = abs(math.sin(yaw))
    gaze = pose.eyes.get("look", 0.0) * 0.04
    r = 0.046 * sk.body.head * sk.H * (look.eye_size if look else 1.0)
    e1 = head_point(sk, 0.255 + gaze, 0.555, front_x=0.135 + gaze)
    e2 = head_point(sk, 0.115 + gaze, 0.565, front_x=-0.135 + gaze)
    return e1, e2, r, w, math.sin(yaw)


def draw_eyes(f, sk, look, ctx, emit=True, alpha=1.0):
    """Limbo eyes: two small bright dots with a soft halo. Hidden when the back is turned."""
    e1, e2, r, w, front = eye_points(sk, look)
    pose = sk.pose
    if front < -0.35:
        return
    vis = clamp((front + 0.35) / 0.35) if front < 0 else 1.0
    op = clamp(pose.eyes.get("open", 1.0))
    glow = pose.eyes.get("glow", 1.0) * vis * alpha
    if op <= 0.02 or glow <= 0.01:
        return
    col = look.eye_color
    for i, e in enumerate((e1, e2)):
        rr = r * (1.0 if i == 0 else lerp(0.82, 1.0, w))
        draw.ellipse(ctx, e, rr * 0.9, rr * op)
        draw.fill(ctx, col, glow)
    if f is not None and emit:
        with f.emit() as G:
            for e in (e1, e2):
                draw.glow_disc(G, e, r * 5.5, col, 0.5 * glow * op)
