"""The stick-figure rig - the frozen Style 1 Dark character anchor, enforced in code.

Character DNA (identical for EVERY figure in the film - that sameness is the story):
  minimalist two-dimensional white line figure; hollow circular head with no face, no eyes,
  no mouth, no hair; no clothing; no filled body; single-line torso; connected line limbs;
  uniform medium line weight; stable proportions; exactly two arms and two legs, each limb
  drawn only in its current pose (a raised arm replaces the lowered one, never both).
  The figure is always white; accents live only on props and light.

Pose angles (degrees):
  * Upper limbs (la, ra = upper arms; ll, rl = thighs) are ABSOLUTE angles measured from
    straight down; positive = toward the facing direction (forward). In front view
    (facing=0) positive = outward from the body (the figure's LEFT side is screen-right).
  * le / re (elbow bend): positive rotates the forearm further forward/up.
  * lk / rk (knee bend): positive rotates the shin backward (natural knee flexion).
  * lean: torso angle from vertical, positive = forward. head: extra head tilt, + = nod forward.
  * x, y: HIP position in world units. s: figure scale (1.0 = 344 px tall standing).
"""
import math
from dataclasses import dataclass, fields, replace

from .core import WHITE, lerp, rad, deg
from . import draw

SEG = dict(head_r=34.0, neck=10.0, torso=112.0, shoulder_drop=14.0,
           upper=66.0, fore=62.0, thigh=78.0, shin=76.0)
FIG_LW = 7.5
LEG = SEG["thigh"] + SEG["shin"]
HEIGHT = 2 * SEG["head_r"] + SEG["neck"] + SEG["torso"] + LEG   # 344


@dataclass
class Pose:
    x: float = 540.0
    y: float = 1200.0
    s: float = 1.0
    facing: int = 1
    lean: float = 0.0
    head: float = 0.0
    la: float = 6.0
    le: float = 8.0
    ra: float = -6.0
    re: float = 8.0
    ll: float = 3.0
    lk: float = 3.0
    rl: float = -3.0
    rk: float = 3.0

    def copy(self, **kw):
        return replace(self, **kw)

    def blend(self, other, t):
        """Interpolate every numeric field (facing switches at t >= 0.5)."""
        kw = {}
        for fd in fields(self):
            a, b = getattr(self, fd.name), getattr(other, fd.name)
            kw[fd.name] = (b if t >= 0.5 else a) if fd.name == "facing" else lerp(a, b, t)
        return Pose(**kw)


def _signs(p):
    if p.facing in (1, -1):
        return p.facing, p.facing, p.facing
    return 1, 1, -1          # front view: lean sign, left-limb sign, right-limb sign


def _dir(a, sign):
    r = rad(a)
    return (math.sin(r) * sign, math.cos(r))


def solve(p):
    """Return joint positions: hip, neck, head (center), head_r, shoulder, le, lh, re, rh,
    lk, lf, rk, rf (elbows/hands/knees/feet), plus 'up' (torso unit vector)."""
    s = p.s
    ls, sl, sr = _signs(p)
    lean = rad(p.lean)
    up = (math.sin(lean) * ls, -math.cos(lean))
    hip = (p.x, p.y)
    neck = (hip[0] + up[0] * SEG["torso"] * s, hip[1] + up[1] * SEG["torso"] * s)
    ha = rad(p.lean + p.head)
    hd = (math.sin(ha) * ls, -math.cos(ha))
    hr = SEG["head_r"] * s
    head = (neck[0] + hd[0] * (SEG["neck"] * s + hr), neck[1] + hd[1] * (SEG["neck"] * s + hr))
    sh = (neck[0] - up[0] * SEG["shoulder_drop"] * s, neck[1] - up[1] * SEG["shoulder_drop"] * s)
    J = dict(hip=hip, neck=neck, head=head, head_r=hr, head_dir=hd, shoulder=sh, up=up)
    for side, sign in (("l", sl), ("r", sr)):
        ua, eb = getattr(p, side + "a"), getattr(p, side + "e")
        d1 = _dir(ua, sign)
        el = (sh[0] + d1[0] * SEG["upper"] * s, sh[1] + d1[1] * SEG["upper"] * s)
        d2 = _dir(ua + eb, sign)
        hand = (el[0] + d2[0] * SEG["fore"] * s, el[1] + d2[1] * SEG["fore"] * s)
        th, kb = getattr(p, side + "l"), getattr(p, side + "k")
        d3 = _dir(th, sign)
        kn = (hip[0] + d3[0] * SEG["thigh"] * s, hip[1] + d3[1] * SEG["thigh"] * s)
        d4 = _dir(th - kb, sign)
        ft = (kn[0] + d4[0] * SEG["shin"] * s, kn[1] + d4[1] * SEG["shin"] * s)
        J[side + "e"], J[side + "h"], J[side + "k"], J[side + "f"] = el, hand, kn, ft
    return J


def draw_figure(f, p, color=WHITE, alpha=1.0, lw=None, glow=0.0):
    """Draw one figure. Returns the solved joints (for attaching props to hands)."""
    J = solve(p)
    w = (lw or FIG_LW) * (p.s ** 0.5)
    hd, hr, head = J["head_dir"], J["head_r"], J["head"]
    chin = (head[0] - hd[0] * hr, head[1] - hd[1] * hr)
    draw.circle(f, head, hr, w, color, alpha, glow=glow)
    draw.stroke(f, [chin, J["neck"], J["hip"]], w, color, alpha, glow=glow)
    for side in ("l", "r"):
        draw.stroke(f, [J["shoulder"], J[side + "e"], J[side + "h"]], w, color, alpha, glow=glow)
        draw.stroke(f, [J["hip"], J[side + "k"], J[side + "f"]], w, color, alpha, glow=glow)
    return J


# ----------------------------------------------------------------------------- IK
def _ik(root, target, l1, l2, sign, knee):
    dx, dy = target[0] - root[0], target[1] - root[1]
    d = math.hypot(dx, dy)
    d = max(abs(l1 - l2) + 1e-3, min(l1 + l2 - 1e-3, d))
    base = math.atan2(dx * sign, dy)
    alpha = math.acos(max(-1, min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    beta = math.pi - math.acos(max(-1, min(1, (l1 * l1 + l2 * l2 - d * d) / (2 * l1 * l2))))
    upper = base + alpha if knee else base - alpha
    return deg(upper), deg(beta)


def reach(p, side, target):
    """Copy of pose with arm `side` ('l'/'r') bent so the hand reaches `target`."""
    J = solve(p)
    _, sl, sr = _signs(p)
    sign = sl if side == "l" else sr
    ua, eb = _ik(J["shoulder"], target, SEG["upper"] * p.s, SEG["fore"] * p.s, sign, knee=False)
    return p.copy(**{side + "a": ua, side + "e": eb})


def plant(p, side, target):
    """Copy of pose with leg `side` bent so the foot lands on `target` (knee forward)."""
    J = solve(p)
    _, sl, sr = _signs(p)
    sign = sl if side == "l" else sr
    th, kb = _ik(J["hip"], target, SEG["thigh"] * p.s, SEG["shin"] * p.s, sign, knee=True)
    return p.copy(**{side + "l": th, side + "k": kb})


def on_ground(p, ground_y):
    """Copy of pose moved vertically so its lowest foot touches ground_y."""
    J = solve(p)
    low = max(J["lf"][1], J["rf"][1])
    return p.copy(y=p.y + (ground_y - low))


# ----------------------------------------------------------------------------- locomotion
STEP_A = 22.0


def _walk_angles(base, ph, limp, stride, arm):
    p = base.copy()
    if limp > 0:
        ph = (ph + 0.07 * limp * math.sin(2 * math.pi * ph)) % 1.0
    c = math.cos(2 * math.pi * ph)
    aL = STEP_A * stride * (1 - 0.40 * limp)        # injured LEFT leg takes the short step
    aR = STEP_A * stride * (1 + 0.10 * limp)
    p.ll, p.rl = aL * c, -aR * c

    def knee(phl, extra):
        if phl < 0.5:
            return 5 + extra + 6 * math.sin(math.pi * phl / 0.5)
        return 8 + 50 * math.sin(math.pi * (phl - 0.5) / 0.5)
    p.lk = knee(ph, 12 * limp)                      # dip onto the bad leg
    p.rk = knee((ph + 0.5) % 1.0, 0.0)
    p.la, p.ra = -15 * arm * c + base.la * 0.3, 15 * arm * c + base.ra * 0.3
    p.le, p.re = 14 + 10 * arm * max(0, -c), 14 + 10 * arm * max(0, c)
    p.lean = base.lean + 3
    p.head = base.head + 6 * limp * max(0.0, math.sin(2 * math.pi * ph))
    return p


def _foot_dx(p, side):
    J = solve(p.copy(x=0.0, y=0.0))
    return J[side + "f"][0]


def walk(t, x0, ground_y, speed, facing=1, s=1.0, limp=0.0, stride=1.0, arm=1.0,
         lean=0.0, head=0.0, phase0=0.0):
    """Planted-foot walk. Returns a Pose at time t for a figure that started with its hip
    near x0 and walks at `speed` px/s (world) in the facing direction on ground_y.
    The stance foot stays fixed on the ground (no sliding); the hip moves naturally."""
    base = Pose(x=0, y=0, s=s, facing=facing, lean=lean, head=head)
    pa = _walk_angles(base, 0.0, limp, stride, arm)
    pb = _walk_angles(base, 0.5, limp, stride, arm)
    s_rl = abs(_foot_dx(pa, "l") - _foot_dx(pa, "r"))      # step that lands the left foot
    s_lr = abs(_foot_dx(pb, "r") - _foot_dx(pb, "l"))      # step that lands the right foot
    cyc = s_rl + s_lr
    P = phase0 + max(0.0, speed * t) / cyc
    k = math.floor(P * 2.0)
    ph = (P * 2.0 - k) * 0.5 + (0.5 if k % 2 else 0.0)
    pose = _walk_angles(base, ph, limp, stride, arm)
    # planted x of the current stance foot
    n_full = k // 2
    xk = n_full * cyc + (s_lr if k % 2 else 0.0)
    stance = "r" if k % 2 else "l"
    hip_x = x0 + facing * (xk - facing * _foot_dx(pose, stance) + facing * _foot_dx(pa, "l"))
    pose = pose.copy(x=hip_x, y=0.0)
    return on_ground(pose, ground_y)


def run(t, x0, ground_y, speed, facing=1, s=1.0, lean=14.0, phase0=0.0, bounce=10.0):
    """Run cycle (approximate planting, with flight bounce)."""
    cyc = 300.0 * s
    P = phase0 + speed * t / cyc
    ph = P % 1.0
    c = math.cos(2 * math.pi * ph)
    p = Pose(x=x0 + facing * speed * t, y=0, s=s, facing=facing, lean=lean)
    p.ll, p.rl = 36 * c, -36 * c

    def knee(phl):
        if phl < 0.5:
            return 18 + 14 * math.sin(math.pi * phl / 0.5)
        return 20 + 85 * math.sin(math.pi * (phl - 0.5) / 0.5)
    p.lk, p.rk = knee(ph), knee((ph + 0.5) % 1.0)
    p.la, p.ra = -38 * c - 5, 38 * c - 5
    p.le, p.re = 85, 85
    p = on_ground(p, ground_y)
    return p.copy(y=p.y - bounce * s * abs(math.sin(2 * math.pi * ph)))


# ----------------------------------------------------------------------------- presets
def stand(x, ground_y, facing=1, s=1.0, **kw):
    if facing == 0:   # front view: symmetric, slightly outward limbs (defaults are profile-oriented)
        for k, v in (("la", 7.0), ("ra", 7.0), ("ll", 5.0), ("rl", 5.0), ("lk", 1.0), ("rk", 1.0)):
            kw.setdefault(k, v)
    return on_ground(Pose(x=x, y=0, s=s, facing=facing, **kw), ground_y)


def breathe(p, t, amt=1.0, seed=0):
    """Subtle idle life: tiny lean/head/arm drift so a standing figure is never frozen."""
    from .core import fbm1
    return p.copy(lean=p.lean + 1.2 * amt * fbm1(t * 0.6, seed),
                  head=p.head + 2.0 * amt * fbm1(t * 0.5, seed + 3),
                  la=p.la + 2.0 * amt * fbm1(t * 0.7, seed + 5),
                  ra=p.ra + 2.0 * amt * fbm1(t * 0.7, seed + 9))


def hands_up(p):
    """Surrender pose. Profile: both arms high. Front view: elbows out at shoulder height,
    forearms up (goalpost) so the arms never cross the hollow head."""
    return p.copy(la=165, le=-10, ra=165, re=-10) if p.facing else p.copy(la=118, le=48, ra=118, re=48)


def sit(x, seat_y, facing=1, s=1.0, **kw):
    """Seated: hip on seat_y, thighs forward, shins down."""
    return Pose(x=x, y=seat_y, s=s, facing=facing, ll=88, lk=88, rl=84, rk=84, **kw)


def lying(x, y, s=1.0, rot=0.0):
    """A figure lying on its back seen from above (for chalk outlines): spread limbs.
    rot rotates the whole figure (degrees). Returns a list of polylines (world coords)."""
    p = Pose(x=0, y=0, s=s, facing=0, la=128, le=-25, ra=60, re=35, ll=18, lk=-10, rl=28, rk=22)
    J = solve(p)
    from .core import rotate as _rot

    def T(q):
        q2 = _rot(q, rot)
        return (q2[0] + x, q2[1] + y)
    lines = [[T(J["neck"]), T(J["hip"])],
             [T(J["shoulder"]), T(J["le"]), T(J["lh"])],
             [T(J["shoulder"]), T(J["re"]), T(J["rh"])],
             [T(J["hip"]), T(J["lk"]), T(J["lf"])],
             [T(J["hip"]), T(J["rk"]), T(J["rf"])]]
    return lines, T(J["head"]), J["head_r"]
