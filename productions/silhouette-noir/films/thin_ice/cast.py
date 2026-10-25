"""THIN ICE: the cast. Cut-paper silhouettes in profile (paperdoll figures, drawn here with coats
that swing with the stride), and from above with their moon shadows.

    s = C.scale("mother", ppm)                 # px per figure unit at ppm px per metre
    Wk = C.walker("mother", [(t, m_per_s), ...], t0=-1, t1=20)   # planted footfalls (paperdoll.Walker)
    st, pose = Wk.state(t), C.pose("mother")   # or C.standing("mother"), or C.perf(...) for mocap
    out = C.draw_at(c, cam, "mother", st, pose, u, z, d=0.0, facing=1, rim=K.SNOW, edge=K.SNOW)
    out = C.draw(c, "mother", st, pose, (x, y), s, facing=1, ...)   # the same at a frame point
    C.top(c, "guard", p, heading, ppm, t, phase=..., lantern=1.0)   # from above, with its moon shadow

Figure units: origin at the pelvis, y up negative, facing +x (paperdoll convention). draw_at puts
the figure's root (the pelvis's x, the ground's z) at the diorama point (u, z, d); the state's
own pelvis x is subtracted, so a Walker's x(t) only moves the legs: move the figure in the world
with u(t) = u0 + Wk.x(t) * C.M_PER_UNIT[who] and the feet stay planted.

The cast:
  mother    1.70 m  a long coat to mid-calf, a headscarf knotted under the chin (its point down
                    the back of her neck), felt boots, mittens
  girl      1.15 m  a pompom hat, a short padded coat, the RED scarf (wound once, both ends out),
                    boots, mittens
  guard     1.86 m  a greatcoat to mid-shin, belted; an ushanka with its flaps tied up; a
                    moustache; a rifle slung across his back
  farmwife  1.62 m  a shawl over her head and shoulders, a long skirt

out (frame px): 'head', 'eye', 'mouth', 'neck', 'pelvis', 'hand_near', 'hand_far', 'shoulder_near',
'shoulder_far', 'knee_near', 'knee_far', 'ankle_near', 'ankle_far', 'back' (between the
shoulder blades, for the girl on the mother's back), 'scale'.
"""
import math
from dataclasses import replace
from functools import lru_cache

from engine import bass, draw as D, mocap as mc, paperdoll as pd
from engine.core import clamp, ease, hash01, lerp
from films.opposite_bass import world as B
from films.thin_ice import kit as K

Seg = mc.Seg
HEIGHT_M = {"mother": 1.70, "girl": 1.15, "guard": 1.86, "farmwife": 1.62}


def clip(name):
    return mc.Clip.load(name)


def _cut(pts, seed, amp=0.35):
    return pd._cut(pts, seed, amp=amp)


def _ell(c, rx, ry, seed):
    return pd._ellipse(c, rx, ry, seed)


def _fluffy(c, rx, ry, seed, bumps=14, depth=0.12, start=0.0, sweep=360.0, closed=True):
    """A fur or knitted edge: an ellipse with small round bumps (the ushanka, the pompom)."""
    pts = []
    n = bumps * 4
    for i in range(n + (0 if closed else 1)):
        a = math.radians(start + sweep * i / n)
        b = 1.0 + depth * (0.5 + 0.5 * math.cos(2.0 * math.pi * i / 4.0)) * (0.8 + 0.4 * hash01(seed, i // 4))
        pts.append((c[0] + rx * b * math.cos(a), c[1] + ry * b * math.sin(a)))
    return pd._cut(pts, seed, amp=0.25, max_len=10.0)


def _fur(c, rx, ry, seed, n=96, p=0.55, depth=0.022):
    """A boxy fur shape (the ushanka's crown): a superellipse with a fine ragged edge."""
    pts = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        b = 1.0 + depth * (hash01(seed, i) * 2.0 - 1.0)
        pts.append((c[0] + rx * b * math.copysign(abs(ca) ** p, ca), c[1] + ry * b * math.copysign(abs(sa) ** p, sa)))
    return pts


# ============================================================================ the figures
@lru_cache(maxsize=None)
def fig(who):
    if who == "mother":
        f = pd.woman(None, 11)
        s = 11100
        torso = [
            # the coat's body: shoulders to the waist, the skirt (SKIRT) swings below it
            (_cut([(-30, -262), (34, -262), (46, -232), (48, -196), (40, -146), (40, -96), (42, -60), (-44, -60),
                   (-40, -96), (-38, -146), (-44, -198), (-42, -238)], s + 1), "ink"),
            # a cloth belt knotted at the back, its ends hanging
            (_cut([(-40, -112), (44, -112), (45, -96), (-41, -96)], s + 2), "ink"),
            (_cut([(-38, -106), (-56, -70), (-48, -66), (-34, -98)], s + 3), "ink"),
            (_cut([(-38, -104), (-46, -60), (-40, -58), (-32, -98)], s + 4), "ink"),
            # the coat's collar, turned up
            (_cut([(-26, -258), (-20, -286), (2, -282), (22, -266), (28, -256), (-22, -248)], s + 5), "ink"),
        ]
        head = [
            (_ell((8, -318), 36, 43, s + 6), "ink"),
            # the profile: brow, nose, lips, chin
            (_cut([(30, -346), (42, -334), (44, -322), (53, -308), (44, -304), (46, -297), (42, -292), (43, -286),
                   (33, -279), (20, -283)], s + 7), "ink"),
            # the headscarf: domed over the crown and the back of the head, its edge framing the face
            (_cut([(32, -352), (22, -368), (0, -378), (-24, -372), (-44, -350), (-52, -320), (-50, -290), (-40, -276),
                   (-16, -272), (4, -276), (20, -284), (24, -300), (18, -320), (26, -338)], s + 8), "ink"),
            # the knot under the chin
            (_ell((18, -274), 12, 9, s + 9), "ink"),
        ]
        hair = [
            # the scarf's point, hanging down the back of her neck (a spring: it lifts as she hurries)
            (_cut([(-30, -290), (-52, -294), (-68, -246), (-58, -240), (-30, -270)], s + 10), "ink", (-36, -286),
             "kerchief"),
        ]
        foot = _cut([(-14, -12), (12, -12), (18, 4), (34, 10), (36, 22), (-16, 22), (-18, 6)], s + 12)
        return replace(f, name=who, torso=torso, head=head, hair=hair, foot=foot,
                       leg_w=(36.0, 30.0, 26.0), arm_w=(31.0, 26.0, 20.0), hand_r=15.0, eye=((32.0, -324.0), 4.5, 5.0))
    if who == "girl":
        f = pd.girl(None, 12)
        s = 11200
        torso = [
            # the padded coat, short and round (the skirt swings below)
            (_cut([(-34, -246), (38, -246), (52, -200), (58, -130), (60, -60), (-56, -60), (-52, -130), (-48, -200)],
                  s + 1), "ink"),
            (_cut([(-12, -262), (16, -262), (16, -238), (-12, -238)], s + 2), "ink"),
        ]
        head = [
            (_ell((10, -322), 60, 66, s + 3), "ink"),
            # a round cheek and a small nose
            (_cut([(58, -342), (70, -328), (72, -316), (64, -306), (62, -292), (50, -276), (40, -272)], s + 4), "ink"),
            # the pompom hat: a knitted dome down to the ears, a folded brim
            (_fluffy((6, -352), 64, 46, s + 5, bumps=18, depth=0.05, start=180.0, sweep=180.0, closed=False) +
             [(70, -346), (-58, -346)], "ink"),
            (_cut([(-60, -350), (70, -350), (72, -330), (-62, -330)], s + 6), "ink"),
        ]
        hair = [
            # the pompom, on a short spring
            (_fluffy((2, -414), 24, 22, s + 7, bumps=10, depth=0.18), "ink", (4, -396), "pompom"),
        ]
        front = [
            # the RED scarf: wound once round her neck, one end trailing behind, one hanging in front
            (_cut([(-40, -270), (50, -270), (52, -240), (-42, -238)], s + 8), "red", (0, 0), None),
            (_cut([(-30, -262), (-92, -268), (-150, -256), (-176, -242), (-140, -240), (-160, -220), (-98, -230),
                   (-30, -238)], s + 9), "red", (-30, -250), "scarf"),
            (_cut([(30, -246), (44, -246), (46, -180), (52, -168), (40, -166), (32, -178)], s + 10), "red", (36, -244),
             "scarf_front"),
        ]
        foot = _cut([(-16, -10), (12, -10), (18, 6), (38, 10), (40, 22), (-18, 22)], s + 11)
        return replace(f, name=who, torso=torso, head=head, hair=hair, front=front, foot=foot,
                       leg_w=(34.0, 29.0, 25.0), arm_w=(32.0, 28.0, 22.0), hand_r=17.0, eye=((44.0, -326.0), 7.0, 9.0))
    if who == "guard":
        f = pd.man(None, 13)
        s = 11300
        torso = [
            # the greatcoat's body, broad, to the belt (the skirt swings below)
            (_cut([(-50, -276), (56, -276), (70, -218), (66, -120), (60, -40), (-58, -40), (-56, -120), (-62, -218)],
                  s + 1), "ink"),
            (_cut([(-60, -50), (66, -50), (66, -28), (-60, -28)], s + 2), "ink"),        # the belt
            # the high collar
            (_cut([(-36, -306), (8, -318), (34, -300), (46, -272), (-44, -270)], s + 3), "ink"),
            # the rifle slung across his back: the muzzle up past his shoulder, the butt at his hip
            (_cut([(-74, -468), (-60, -468), (-58, -452), (-44, -128), (-62, -128)], s + 4, amp=0.12), "ink"),
            (_cut([(-64, -140), (-44, -140), (-30, 22), (-58, 36), (-68, 18)], s + 5, amp=0.2), "ink"),
        ]
        head = [
            (_ell((10, -338), 38, 45, s + 6), "ink"),
            # a big nose and a heavy moustache
            (_cut([(36, -362), (50, -346), (60, -330), (50, -324), (52, -314), (44, -302), (34, -296), (14, -296)],
                  s + 7), "ink"),
            (_cut([(30, -322), (60, -322), (66, -308), (52, -312), (40, -304), (28, -310)], s + 8), "ink"),
            # the ushanka: a boxy fur crown, the front flap turned up, the ear flaps tied on top
            (_fur((4, -394), 56, 40, s + 9), "ink"),
            (_cut([(26, -414), (56, -406), (70, -380), (66, -360), (30, -362)], s + 10), "ink"),
            (_ell((0, -436), 15, 8, s + 11), "ink"),
        ]
        foot = _cut([(-18, -10), (14, -10), (22, 4), (48, 8), (50, 22), (-20, 22)], s + 12)
        return replace(f, name=who, torso=torso, head=head, foot=foot, leg_w=(46.0, 40.0, 34.0), arm_w=(42.0, 35.0, 27.0),
                       hand_r=18.0, eye=((38.0, -342.0), 5.0, 3.6))
    if who == "guard_wet":
        # out of the river (s08-s11): the ushanka and the rifle gone, his cropped hair wet and
        # flat in clumps; the same body as the guard (and the same scale: m_per_unit)
        F = fig("guard")
        hair = (_cut([(44, -364), (30, -382), (6, -392), (-18, -388), (-36, -370), (-44, -342), (-40, -310), (-30, -296),
                      (-26, -312), (-20, -306), (-18, -330), (-8, -352), (4, -364), (20, -360), (32, -370)], 11315), "ink")
        return replace(F, name=who, torso=F.torso[:3], head=F.head[:3] + [hair])
    if who == "farmwife":
        f = pd.woman(None, 14)
        s = 11400
        torso = [
            (_cut([(-28, -258), (32, -258), (42, -210), (38, -110), (40, -60), (-42, -60), (-38, -110), (-40, -210)],
                  s + 1), "ink"),
            # the shawl: over her head and shoulders, falling to her elbows
            (_cut([(-40, -350), (20, -362), (40, -330), (54, -250), (60, -170), (-62, -170), (-56, -250), (-52, -330)],
                  s + 2), "ink"),
        ]
        head = [
            (_ell((8, -318), 36, 43, s + 3), "ink"),
            (_cut([(30, -346), (42, -334), (44, -322), (53, -308), (44, -304), (46, -297), (42, -292), (43, -286),
                   (33, -279), (20, -283)], s + 4), "ink"),
        ]
        return replace(f, name=who, torso=torso, head=head, arm_w=(28.0, 23.0, 18.0), eye=((32.0, -324.0), 4.5, 5.0))
    raise ValueError(who)


# the mouth (breath puffs come from here), in the head frame
MOUTH = {"mother": (48.0, -293.0), "girl": (68.0, -300.0), "guard": (60.0, -310.0), "farmwife": (48.0, -293.0)}

# the coats' swinging skirts: (waist y, hem as a fraction down the leg, back x, front x, flare)
SKIRT = {"mother": (-70.0, 0.76, -46.0, 44.0, 16.0), "girl": (-70.0, 0.30, -58.0, 62.0, 12.0),
         "guard": (-36.0, 0.73, -62.0, 66.0, 18.0), "farmwife": (-70.0, 0.96, -44.0, 42.0, 22.0)}


@lru_cache(maxsize=None)
def height_units(who):
    F = fig(who)
    top = max(-y for poly, _ in F.head for _, y in poly)
    top = max(top, max((-y for poly, _, _, _ in F.hair for _, y in poly), default=0.0))
    return F.leg * 0.965 + top


@lru_cache(maxsize=None)
def m_per_unit(who):
    if who == "guard_wet":
        return m_per_unit("guard")
    return HEIGHT_M[who] / height_units(who)


M_PER_UNIT = {w: m_per_unit(w) for w in HEIGHT_M}


def scale(who, ppm):
    """px per figure unit for a camera at ppm px per metre."""
    return ppm * m_per_unit(who)


# ============================================================================ motion
# gaits in snow: (stride per full cycle of two steps, duty, lift), figure units. The mother's walk
# is a 1.07 m cycle, her run 1.8 m; the guard trudges 1.1 m and runs 1.9 m; the girl's short legs
# take a 0.6 m cycle.
WALK = {"mother": (420.0, 0.62, 40.0), "girl": (360.0, 0.6, 40.0), "guard": (440.0, 0.64, 36.0),
        "farmwife": (380.0, 0.62, 30.0)}
RUN = {"mother": (700.0, 0.38, 70.0), "girl": (520.0, 0.36, 66.0), "guard": (760.0, 0.38, 70.0),
       "farmwife": (600.0, 0.38, 56.0)}

# the wet guard (s08-s11) moves and breathes with the guard's body
for _d in (HEIGHT_M, MOUTH, SKIRT, WALK, RUN, M_PER_UNIT):
    _d["guard_wet"] = _d["guard"]


def walker(who, speed, x0=0.0, t0=-2.0, t1=24.0, walk=None, run=None):
    """A paperdoll Walker for `who`. speed: [(t, metres per second), ...]."""
    k = 1.0 / m_per_unit(who)
    return pd.Walker(fig(who), x0=x0, speed=[(t, v * k) for t, v in speed], t0=t0, t1=t1,
                     walk=walk or WALK[who], run=run or RUN[who],
                     v_walk=WALK[who][0] * 0.8, v_run=RUN[who][0] * 1.1)


def perf(who, segs, facing=1, x=0.0, near="Right"):
    return mc.Performance(fig(who), segs, facing=facing, x=x, near=near)


def standing(who, x=0.0, spread=16.0):
    return pd.standing(fig(who), x, spread)


def pose(who, **kw):
    p = pd.Pose(**kw)
    return p


def _fwd(q, duty):
    """How far forward the near leg is (-1 back .. +1 forward) at stride phase q: it lands
    forward, travels back through the stance, swings forward again."""
    if q < duty:
        return 1.0 - 2.0 * q / duty
    s = (q - duty) / (1.0 - duty)
    return -1.0 + 2.0 * s * s * (3.0 - 2.0 * s)


# rest angles of each figure's springs (degrees): the scarf's long end hangs down her back
REST = {"scarf": -64.0, "scarf_front": 0.0, "pompom": 0.0, "kerchief": 0.0}


def walk_pose(who, st, amp=1.0, lean=None, head=0.0, arms=None, hold=None, springs=None, crouch=0.0, eye=1.0,
              gaze=0.0, t=0.0, wind=0.0):
    """A pose for a walking state: the arms swing against the legs (bent and pumping as the gait
    becomes a run), the body leans into the speed, springs ride the stride. arms: overrides per
    side; springs: overrides; wind: degrees the scarf and kerchief lift."""
    q = st["phase"] % 1.0
    r = st.get("run", 0.0)
    duty = lerp(WALK[who][1], RUN[who][1], r)
    k = clamp(st["speed"] / (WALK[who][0] * 0.8), 0.0, 1.3)
    f = _fwd(q, duty) * min(k, 1.0)
    A = lerp(20.0, 52.0, r) * amp * min(k, 1.0)
    E = lerp(12.0, 84.0, r)
    a = {"near": ("ang", -f * A, E + max(0.0, -f) * lerp(16.0, 10.0, r)),
         "far": ("ang", f * A * 0.85, E + max(0.0, f) * lerp(16.0, 10.0, r))}
    if arms:
        a.update(arms)
    bounce = math.sin(4.0 * math.pi * q)
    sp = {"scarf": REST["scarf"] + lerp(0.0, 34.0, min(k, 1.0)) + lerp(0.0, 30.0, r) + 5.0 * bounce * k + wind,
          "scarf_front": 6.0 * bounce * k - 10.0 * r,
          "pompom": 8.0 * bounce * k,
          "kerchief": lerp(0.0, 12.0, min(k, 1.0)) + 18.0 * r + 3.0 * bounce * k + wind * 0.5}
    if springs:
        sp.update(springs)
    ln = lean if lean is not None else lerp(2.0, 13.0, r) * min(k, 1.0)
    return pd.Pose(lean=ln, head=head, crouch=crouch, arms=a, hold=dict(hold or {}), springs=sp, eye=eye, gaze=gaze)


def still_pose(who, lean=0.0, head=0.0, arms=None, hold=None, springs=None, crouch=0.0, eye=1.0, gaze=0.0, t=0.0,
               breathe=1.0, wind=0.0):
    """A pose for standing still: the arms hang, the body breathes, the springs at rest."""
    b = math.sin(t * 2.0 * math.pi / 3.2) * breathe
    a = {"near": ("ang", 4.0 + 1.5 * b, 10.0), "far": ("ang", -3.0 + 1.5 * b, 8.0)}
    if arms:
        a.update(arms)
    sp = dict(REST)
    sp["scarf"] += wind + 2.0 * b
    sp["kerchief"] += wind * 0.5
    if springs:
        sp.update(springs)
    return pd.Pose(lean=lean + 0.8 * b, head=head, crouch=crouch + 2.0 * b, arms=a, hold=dict(hold or {}), springs=sp,
                   eye=eye, gaze=gaze)


def shift(st, dx):
    """A state moved dx figure units along x."""
    feet = {k: (v[0] + dx, v[1], v[2]) for k, v in st["feet"].items()}
    return dict(st, pelvis=(st["pelvis"][0] + dx, st["pelvis"][1]), feet=feet)


# ============================================================================ drawing
def _leg_point(hip, knee, ank, frac, F):
    L1, L2 = F.thigh, F.shin
    s = frac * (L1 + L2)
    if s <= L1:
        u = s / L1
        return (lerp(hip[0], knee[0], u), lerp(hip[1], knee[1], u))
    u = clamp((s - L1) / L2)
    return (lerp(knee[0], ank[0], u), lerp(knee[1], ank[1], u))


def _paint(c, polys, rgb, edge, ow):
    if edge is not None:
        B.edged(c, polys, rgb, edge, ow)
    else:
        bass.fill_polys(c, polys, rgb)


PARTS = ("far_arm", "far_leg", "near_leg", "body", "near_arm")


def draw_fig(c, who, st, pose, color=K.INK, facing=1, far=None, edge=None, ow=6.0, hide=(), red=K.RED,
             eye_color=K.PAPER, parts=PARTS):
    """Draw `who` at paperdoll state st / pose in the CURRENT cairo frame (figure units). Returns
    joints in that frame. edge: the colour behind the figure, laid round the near arm and leg so
    a limb across the body still shows. parts: which of PARTS to draw (joints are always
    returned)."""
    F = fig(who)
    if parts is not PARTS:
        c.push_group()
    P = st["pelvis"]
    P = (P[0], P[1] + pose.crouch)
    lean = pose.lean
    far = far or color
    cols = {"ink": color, "red": red if color == K.INK else color}

    def Wd(p):
        q = pd._rot((p[0], p[1]), lean)
        return (P[0] + facing * q[0], P[1] + q[1])

    out = {}
    legs = {}
    for side in ("far", "near"):
        foot = st["feet"][side]
        hip = Wd((0.0, -4.0))
        knee, ank = pd.ik2(hip, (foot[0], foot[1] - F.ankle), F.thigh, F.shin, forward=facing)
        legs[side] = (hip, knee, ank, foot[2])
        out["knee_" + side] = knee
        out["ankle_" + side] = ank

    def arm(side):
        spec = pose.arms.get(side, ("ang", 0.0, 0.0))
        sh = Wd(F.shoulder)
        if spec[0] == "rel":
            el, wr = pd.ik2(sh, Wd(spec[1]), F.upper, F.fore, forward=-facing)
        elif spec[0] == "ik":
            el, wr = pd.ik2(sh, spec[1], F.upper, F.fore, forward=-facing)
        else:
            a1 = spec[1] + lean
            a2 = a1 + spec[2]
            el = (sh[0] + facing * math.sin(math.radians(a1)) * F.upper, sh[1] + math.cos(math.radians(a1)) * F.upper)
            wr = (el[0] + facing * math.sin(math.radians(a2)) * F.fore, el[1] + math.cos(math.radians(a2)) * F.fore)
        return sh, el, wr

    def draw_leg(side, rgb, e):
        hip, knee, ank, pitch = legs[side]
        w0, w1, w2 = F.leg_w
        polys = [bass.orient(bass.capsule_pts(hip, knee, w0 / 2, w1 / 2, cap=8), True),
                 bass.orient(bass.capsule_pts(knee, ank, w1 / 2, w2 / 2, cap=8), True)]
        foot = [(ank[0] + facing * x, ank[1] + y) for x, y in [pd._rot(p, -pitch) for p in F.foot]]
        polys.append(bass.orient(foot, True))
        _paint(c, polys, rgb, e, ow)

    def draw_arm(side, rgb, e):
        sh, el, wr = arm(side)
        out["shoulder_" + side] = sh
        out["elbow_" + side] = el
        if side in hide:
            return
        w0, w1, w2 = F.arm_w
        d = math.dist(wr, el) or 1.0
        u = ((wr[0] - el[0]) / d, (wr[1] - el[1]) / d)
        hold = pose.hold.get(side)
        n1 = (-u[1], u[0])
        sc = n1[0] * facing - 0.6 * n1[1]
        n = n1 if sc >= 0 else (-n1[0], -n1[1])
        hp, L = B.hand_poly(F, "fist" if hold is not None else "open", wr, u, n, thumb=clamp(abs(sc) * 3.0))
        hc = (wr[0] + u[0] * 0.5 * L, wr[1] + u[1] * 0.5 * L)
        out["hand_" + side] = hc
        out["wrist_" + side] = wr
        if hold is not None:
            hold(c, dict(hc=hc, wrist=wr, u=u, n=n, facing=facing, edge=edge, rim=None if color == K.INK else color))
        polys = [bass.orient(bass.capsule_pts(sh, el, w0 / 2, w1 / 2, cap=8), True),
                 bass.orient(bass.capsule_pts(el, wr, w1 / 2, w2 / 2, cap=8), True), hp]
        _paint(c, polys, rgb, e, ow)

    def keep(name):
        return parts is PARTS or name in parts

    def part(name, fn):
        if keep(name):
            fn()
        else:
            c.push_group()
            fn()
            c.pop_group()

    part("far_arm", lambda: draw_arm("far", far, None))
    part("far_leg", lambda: draw_leg("far", far, None))
    part("near_leg", lambda: draw_leg("near", color, edge))
    if not keep("body"):
        c.push_group()
    # the coat's skirt, swinging with the legs
    sk = SKIRT.get(who) if st.get("skirt", True) else None
    if sk:
        wy, frac, bx, fx, flare = sk
        pts = [_leg_point(*legs[s][:3], frac, F) for s in ("far", "near")]
        kn = [legs[s][1] for s in ("far", "near")]
        front = max(pts, key=lambda p: facing * p[0])
        back = min(pts, key=lambda p: facing * p[0])
        hem_y = max(p[1] for p in pts) + 4.0
        kf = max(kn, key=lambda p: facing * p[0])
        kb = min(kn, key=lambda p: facing * p[0])
        wb, wf = Wd((bx, wy)), Wd((fx, wy))
        mid_f = (lerp(wf[0], kf[0] + facing * (flare * 0.8 + F.leg_w[1] * 0.5), 0.75), lerp(wf[1], kf[1], 0.75))
        mid_b = (lerp(wb[0], kb[0] - facing * (flare * 0.8 + F.leg_w[1] * 0.5), 0.75), lerp(wb[1], kb[1], 0.75))
        hem_f = (front[0] + facing * (flare + F.leg_w[1] * 0.5), hem_y)
        hem_b = (back[0] - facing * (flare + F.leg_w[1] * 0.5), hem_y + 2.0)
        bass.fill_polys(c, [bass.orient([wb, wf, mid_f, hem_f, hem_b, mid_b], True)], color)
    # torso, front pieces, head (in the pelvis frame)
    c.save()
    c.translate(*P)
    c.scale(facing, 1.0)
    c.rotate(math.radians(lean))
    for poly, key in F.torso:
        bass.fill_polys(c, [poly], cols[key])
    c.save()
    c.translate(*F.neck)
    c.rotate(math.radians(-pose.head))
    c.translate(-F.neck[0], -F.neck[1])
    for poly, key, pin, spring in F.hair:
        c.save()
        c.translate(*pin)
        c.rotate(math.radians(pose.springs.get(spring, 0.0)))
        c.translate(-pin[0], -pin[1])
        bass.fill_polys(c, [poly], cols.get(key, color))
        c.restore()
    for poly, key in F.head:
        bass.fill_polys(c, [poly], cols[key])
    if F.eye is not None and pose.eye > 0.02 and color == K.INK:
        (ex, ey), rx, ry = F.eye
        bass.fill_polys(c, [D.ellipse_pts((ex + pose.gaze * rx * 0.4, ey), rx * 1.15, ry * 1.15 * pose.eye, n=20)],
                        eye_color)
    eye_dev = c.user_to_device(*(F.eye[0] if F.eye else (30.0, -320.0)))
    mouth_dev = c.user_to_device(*MOUTH[who])
    head_dev = c.user_to_device(F.neck[0] + 6.0, F.neck[1] - 64.0)
    c.restore()
    for poly, key, pin, spring in F.front:
        c.save()
        c.translate(*pin)
        c.rotate(math.radians(pose.springs.get(spring, 0.0) if spring else 0.0))
        c.translate(-pin[0], -pin[1])
        bass.fill_polys(c, [poly], cols.get(key, color))
        c.restore()
    back_dev = c.user_to_device(-30.0, -200.0)
    neck_dev = c.user_to_device(*F.neck)
    c.restore()
    out["eye"] = c.device_to_user(*eye_dev)
    out["mouth"] = c.device_to_user(*mouth_dev)
    out["head"] = c.device_to_user(*head_dev)
    out["back"] = c.device_to_user(*back_dev)
    out["neck"] = c.device_to_user(*neck_dev)
    if not keep("body"):
        c.pop_group()
    part("near_arm", lambda: draw_arm("near", color, edge))
    out["pelvis"] = P
    if parts is not PARTS:
        c.pop_group_to_source()
        c.paint()
    return out


def draw(c, who, st, pose, at, s, facing=1, rim=None, rim_w=None, light=(0.8, -0.6), color=K.INK, edge=None,
         ow=None, hide=(), shift_root=True, red=K.RED, parts=PARTS, under=None):
    """Draw `who` with its root (the state's pelvis x, the ground) at frame point `at`, s px per
    figure unit. rim: the moonlit edge's colour (None: none), laid rim_w px toward `light` (a unit
    vector in frame px). under(c, joints): drawn first, beneath the figure, from the joints it is
    about to have (a lantern's glow: joints['flame']). Returns the joints in frame px (and 'scale';
    'flame' when it holds a lit lantern)."""
    if shift_root:
        st = shift(st, -st["pelvis"][0])
    # the cut lines scale with the figure (a thin line on a small figure)
    rim_w = clamp(4.0 * s, 1.5, 3.5) if rim_w is None else rim_w
    ow = clamp(5.0 * s, 1.5, 4.0) if ow is None else ow
    if under is not None:
        c.push_group()
        j = draw(c, who, st, pose, at, s, facing, color=color, hide=hide, shift_root=False, parts=parts)
        c.pop_group()
        under(c, j)
    if rim is not None:
        c.save()
        c.translate(light[0] * rim_w, light[1] * rim_w)
        c.translate(*at)
        c.scale(s, s)
        holds = pose.hold
        pose.hold = {k: _rimmed(fn, rim) for k, fn in holds.items()}
        draw_fig(c, who, st, pose, rim, facing, hide=hide, red=rim, parts=parts)
        pose.hold = holds
        c.restore()
    c.save()
    c.translate(*at)
    c.scale(s, s)
    out = draw_fig(c, who, st, pose, color, facing, edge=edge, ow=ow / max(s, 1e-3), hide=hide, red=red, parts=parts)
    joints = {k: c.user_to_device(*v) for k, v in out.items() if isinstance(v, tuple) and len(v) == 2}
    c.restore()
    res = {k: c.device_to_user(*v) for k, v in joints.items()}
    res["scale"] = s
    for fn in pose.hold.values():
        w = getattr(fn, "where", None)
        if w and "flame" in w:
            res["flame"] = c.device_to_user(*w["flame"])
    return res


def _rimmed(fn, rim):
    def g(c, info):
        fn(c, dict(info, rim=rim))
    return g


def draw_at(c, cam, who, st, pose, u, z, d=0.0, facing=1, **kw):
    """draw() with the root at diorama point (u, z, d) (cam: world.Dio), scaled for that depth."""
    s = scale(who, cam.scale(d))
    return draw(c, who, st, pose, cam.px(u, z, d), s, facing, **kw)


# ============================================================================ the girl on her mother's back
def frame_point(who, st, pose, p, at, s, facing=1, shift_root=True):
    """Where a point of `who`'s pelvis frame (figure units, before the head turns) lands in frame
    px when drawn by draw(c, who, st, pose, at, s, facing)."""
    P = st["pelvis"]
    x0 = P[0] if shift_root else 0.0
    q = pd._rot(p, pose.lean)
    return (at[0] + s * (P[0] - x0 + facing * q[0]), at[1] + s * (P[1] + pose.crouch + q[1]))


# where her pelvis rides on her mother's back (the mother's pelvis frame): high, so her head is
# clear of her mother's, above and behind it
SEAT = (-94.0, -180.0)


def carried_pose(t=0.0, look=0.0, lean=-2.0, bounce=0.0, wind=0.0):
    """The girl riding piggyback: sitting up on her mother's back, arms round her neck."""
    sway = 1.5 * math.sin(t * 2.0)
    return pd.Pose(lean=lean + sway, head=look, crouch=0.0,
                   arms={"near": ("rel", (184.0, -104.0)), "far": ("rel", (172.0, -96.0))},
                   springs={"scarf": REST["scarf"] + 28.0 + 6.0 * bounce + wind, "scarf_front": -6.0 + 4.0 * bounce,
                            "pompom": 8.0 * bounce})


def carried_state():
    """Her legs round her mother's waist (her figure units, pelvis over the origin): her boots poke
    out in front of her mother's hips; her seat is drawn as one round piece."""
    F = fig("girl")
    y = -F.leg * 0.6
    return dict(pelvis=(0.0, y), feet={"near": (222.0, y + 62.0, -8.0), "far": (210.0, y + 56.0, -12.0)},
                phase=0.0, speed=0.0, run=0.0, stride=0.0, skirt=False)


def carry_arms(t=0.0):
    """The mother's arms hooked under the girl's knees at her sides (elbows back)."""
    return {"near": ("rel", (22.0, -124.0 + 2.0 * math.sin(t * 2.0))), "far": ("rel", (14.0, -118.0))}


def piggyback(c, st, pose, at, s, facing=1, t=0.0, rim=None, rim_w=None, light=(0.8, -0.6), edge=None, look=0.0,
              girl_pose=None, shift_root=True):
    """The mother (state st, pose) with the girl on her back, root at `at`, s px per mother unit.
    The girl is drawn behind her mother, then her near arm over her mother's shoulder (laid on
    with an `edge` stroke so it reads). Returns (mother joints, girl joints)."""
    rim_w = clamp(4.0 * s, 1.5, 3.5) if rim_w is None else rim_w
    q = st.get("phase", 0.0) % 1.0
    bounce = math.sin(4.0 * math.pi * q) * clamp(st.get("speed", 0.0) / 300.0)
    gp = frame_point("mother", st, pose, SEAT, at, s, facing, shift_root)
    sg = s * m_per_unit("girl") / m_per_unit("mother")
    gst = carried_state()
    gpose = girl_pose or carried_pose(t, look, bounce=bounce)
    gpose = replace(gpose, lean=gpose.lean + pose.lean)
    g_at = (gp[0], gp[1] - gst["pelvis"][1] * sg + 6.0 * bounce * sg)
    kw = dict(rim=rim, rim_w=rim_w, light=light, shift_root=False)
    girl = draw(c, "girl", gst, gpose, g_at, sg, facing, parts=("far_arm", "far_leg", "body"), **kw)
    # her seat: one round piece behind her mother's back, under her coat
    seat = frame_point("girl", gst, gpose, (22.0, -18.0), g_at, sg, facing, False)
    if rim is not None:
        K.ellipse(c, (seat[0] + light[0] * rim_w, seat[1] + light[1] * rim_w), 80.0 * sg, 66.0 * sg, rim,
                  angle=gpose.lean * facing)
    K.ellipse(c, seat, 80.0 * sg, 66.0 * sg, K.INK, angle=gpose.lean * facing)
    mother = draw(c, "mother", st, pose, at, s, facing, edge=edge, shift_root=shift_root, rim=rim, rim_w=rim_w,
                  light=light)
    draw(c, "girl", gst, gpose, g_at, sg, facing, parts=("near_leg", "near_arm"), edge=edge or K.SNOW,
         shift_root=False)
    return mother, girl


# ============================================================================ props held in a hand
def hold_lantern(t=0.0, lit=1.0, swing=0.0, size=1.0):
    """The lantern hanging from the fist by its bail; fn.where['flame'] is the flame (device
    coordinates) after drawing: use flame_at(c, fn) for the glow."""
    where = {}

    def fn(c, info):
        hc = info["hc"]
        col = info.get("rim") or K.INK
        sw = swing(t) if callable(swing) else swing
        p = K.lantern(c, (hc[0], hc[1] - 6.0), s=1.15 * size, lit=0.0 if info.get("rim") else lit, swing=sw,
                      color=col, t=t)
        if not info.get("rim"):
            where["flame"] = c.user_to_device(*p)
    fn.where = where
    return fn


def flame_at(c, hold):
    w = hold.where
    return c.device_to_user(*w["flame"]) if "flame" in w else None


def hold_stone(size=1.0):
    def fn(c, info):
        hc, u = info["hc"], info["u"]
        col = info.get("rim") or K.INK
        p = (hc[0] + u[0] * 10.0, hc[1] + u[1] * 10.0)
        bass.fill_polys(c, [bass.orient(bass.ring_pts(p, 13.0 * size, seed=5, n=8, amp=3.0), True)], col)
    return fn


def hold_end():
    """The scarf's end in her fist (the scene draws the scarf from out['hand_*'])."""
    def fn(c, info):
        return None
    return fn


def hold_watch(open_u=0.0):
    """The pocket watch in his palm (wide shots; the close-up is faces.watch)."""
    def fn(c, info):
        hc, u = info["hc"], info["u"]
        col = info.get("rim") or K.INK
        p = (hc[0] + u[0] * 6.0, hc[1] - 10.0)
        bass.fill_polys(c, [bass.orient(bass.ring_pts(p, 12.0, seed=7, n=14, amp=0.5), True)], col)
        if not info.get("rim"):
            bass.fill_polys(c, [bass.orient(bass.ring_pts(p, 8.0, seed=8, n=12, amp=0.4), True)], K.PAPER, 0.85)
    return fn


def whistle(c, out, t, t0, s, facing=1):
    """His whistle at his mouth, and its rays (from t0)."""
    m = out["mouth"]
    tip = (m[0] + facing * 34.0 * s, m[1] + 6.0 * s)
    K.band(c, [m, tip], K.INK, max(2.0, 12.0 * s), seed=2)
    K.whistle(c, (tip[0] + facing * 8.0 * s, tip[1]), t, t0, r0=20.0 * s * 2, r1=110.0 * s * 2, width=max(2.5, 9.0 * s),
              facing=facing)


# ============================================================================ from above
def _ell_m(cx, cy, rx, ry, n=20):
    return [(cx + rx * math.cos(6.283 * i / n), cy + ry * math.sin(6.283 * i / n)) for i in range(n)]


def _xf(pts, p, ang, ppm):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(p[0] + (x * ca - y * sa) * ppm, p[1] + (x * sa + y * ca) * ppm) for x, y in pts]


def top(c, who, p, heading, ppm, t=0.0, phase=0.0, speed=1.0, carry=False, lantern=0.0, shadow=True,
        shadow_dir=90.0, crouch=0.0, color=K.INK, shade=K.SHADOW, scarf=True, look=0.0, shadow_alpha=1.0):
    """`who` seen from above at frame point p, facing screen angle `heading` (degrees: 0 = +x,
    -90 = up the frame), ppm px per metre. phase: stride phase (feet and arms swing, scaled by
    speed 0..1); carry: the girl on the mother's back; lantern: its glow strength (guard);
    shadow_dir: the moon shadow's screen angle (90 = down the frame, south); crouch 0..1."""
    big = {"mother": 1.0, "girl": 0.7, "guard": 1.18, "farmwife": 0.95}[who]
    sw = math.sin(2.0 * math.pi * phase) * speed
    # ---- the moon shadow: a frontal silhouette laid along the snow
    if shadow:
        L = HEIGHT_M[who] * (1.0 - 0.45 * crouch) * K_SHADOW
        legs = 0.47 * L
        sh = []
        for side in (-1, 1):
            off = 0.07 * big * side
            stride = 0.05 * sw * side
            sh.append([(0.0 + stride, off - 0.035), (legs, off * 1.25 - 0.04), (legs, off * 1.25 + 0.04),
                       (0.0 + stride, off + 0.035)])
        body = [(legs * 0.92, -0.17 * big), (L * 0.83, -0.22 * big), (L * 0.88, -0.12 * big), (L * 0.88, 0.12 * big),
                (L * 0.83, 0.22 * big), (legs * 0.92, 0.17 * big)]
        sh.append(body)
        hr = (0.13 if who == "guard" else 0.1) * big
        sh.append(_ell_m(L * 0.88 + hr * 1.3, 0.0, hr * 1.4, hr))
        if who == "guard":
            sh.append([(L * 0.5, 0.2), (L * 1.02, -0.05), (L * 1.03, -0.02), (L * 0.52, 0.23)])      # the rifle
        if carry:
            sh.append(_ell_m(L * 0.97 + 0.08, 0.13, 0.1, 0.08))
        K.polys(c, [_xf(q, p, shadow_dir, ppm) for q in sh], shade, shadow_alpha)
    # ---- the figure
    ps = []
    reds = []
    if who in ("mother", "farmwife", "girl", "guard"):
        sr = {"mother": (0.13, 0.24), "girl": (0.09, 0.165), "guard": (0.16, 0.29), "farmwife": (0.13, 0.25)}[who]
        hem = {"mother": (0.2, 0.27), "girl": (0.12, 0.18), "guard": (0.24, 0.31), "farmwife": (0.24, 0.28)}[who]
        hem = (hem[0] * (1.0 + 0.4 * crouch), hem[1] * (1.0 + 0.15 * crouch))
        # feet peeking out in front, alternately
        if speed > 0.02 and crouch < 0.5:
            for side in (-1, 1):
                fx = 0.12 * big + 0.12 * big * sw * side
                ps.append(_ell_m(fx, 0.085 * big * side, 0.06 * big, 0.04 * big, 10))
        ps.append(_ell_m(-0.02, 0.0, hem[0], hem[1]))
        ps.append(_ell_m(0.0, 0.0, sr[0], sr[1]))
        # arms swinging at the sides (or forward round the lantern / crouched)
        for side in (-1, 1):
            sw_a = -0.16 * sw * side
            sh_p = (0.0, sr[1] * 0.85 * side)
            hand = (sw_a, sr[1] * 1.15 * side)
            ps.append(bass.capsule_pts(sh_p, hand, 0.05 * big, 0.045 * big, cap=4))
        if who == "guard":
            ps.append(list(_fluffy_m(0.02, 0.0, 0.16, 0.15, 7)))                       # the ushanka
            ps.append([(-0.2, -0.36), (-0.17, -0.38), (0.03, 0.52), (0.0, 0.53)])         # the rifle across his back
            if lantern > 0.0:
                ps.append(_ell_m(0.08, sr[1] * 1.3, 0.05, 0.05, 8))
        elif who == "girl":
            ps.append(_ell_m(0.02, 0.0, 0.095, 0.095))
            if scarf:
                reds.append(_ring_m(0.0, 0.0, 0.11, 0.07))
                reds.append([(-0.05, 0.02), (-0.42, 0.06 + 0.05 * math.sin(t * 4.0)), (-0.43, 0.1 + 0.05 * math.sin(t * 4.0)),
                             (-0.05, 0.06)])
        else:
            ps.append(_ell_m(0.02, 0.0, 0.1, 0.1))
            ps.append([(-0.05, -0.06), (-0.2, 0.0), (-0.05, 0.06)])                     # the kerchief's point
        if carry:
            ps.append(_ell_m(-0.2, 0.0, 0.085, 0.085))                                   # her head at her mother's back
            for side in (-1, 1):
                ps.append(bass.capsule_pts((-0.2, 0.06 * side), (0.02, 0.14 * side), 0.03, 0.03, cap=4))
            reds.append(_ring_m(-0.2, 0.0, 0.1, 0.06))
            reds.append([(-0.24, 0.03), (-0.5, 0.08 + 0.04 * math.sin(t * 4.0)), (-0.51, 0.11 + 0.04 * math.sin(t * 4.0)),
                         (-0.24, 0.07)])
    K.polys(c, [_xf(q, p, heading, ppm) for q in ps], color)
    if reds and color == K.INK:
        K.polys(c, [_xf(q, p, heading, ppm) for q in reds], K.RED)


K_SHADOW = 1.0 / math.tan(math.radians(33.0))


def _fluffy_m(cx, cy, rx, ry, seed, bumps=10):
    pts = []
    n = bumps * 3
    for i in range(n):
        a = 6.283 * i / n
        b = 1.0 + 0.1 * (0.5 + 0.5 * math.cos(6.283 * i / 3.0))
        pts.append((cx + rx * b * math.cos(a), cy + ry * b * math.sin(a)))
    return pts


def _ring_m(cx, cy, r, w, n=20):
    outer = [(cx + r * math.cos(6.283 * i / n), cy + r * math.sin(6.283 * i / n)) for i in range(n + 1)]
    inner = [(cx + (r - w) * math.cos(6.283 * i / n), cy + (r - w) * math.sin(6.283 * i / n)) for i in range(n + 1)]
    return outer + inner[::-1]


def top_prone(c, who, p, heading, ppm, t=0.0, reach=0.0, color=K.INK, shade=K.SHADOW, kick=0.0):
    """`who` lying flat on the snow or ice, from above (crawling: reach 0..1 swings the arms
    forward alternately; kick moves the legs). Head toward `heading`."""
    big = {"mother": 1.0, "girl": 0.7, "guard": 1.18, "farmwife": 0.95}[who]
    L = HEIGHT_M[who]
    ps = []
    # body from feet (-L/2) to head (+L/2)
    ps.append(_ell_m(0.08 * L, 0.0, 0.26 * L, 0.2 * big))                # torso
    ps.append(_ell_m(-0.2 * L, 0.0, 0.2 * L, 0.16 * big))                # hips and coat
    for side in (-1, 1):
        k = 0.06 * L * math.sin(6.283 * kick + (0 if side > 0 else 3.14))
        ps.append(bass.capsule_pts((-0.3 * L, 0.08 * big * side), (-0.5 * L + k, 0.12 * big * side), 0.06 * big, 0.05 * big,
                                   cap=4))
        a = 6.283 * reach + (0.0 if side > 0 else math.pi)
        hx = 0.3 * L + 0.14 * L * (0.5 + 0.5 * math.sin(a))
        ps.append(bass.capsule_pts((0.22 * L, 0.18 * big * side), (hx, 0.24 * big * side), 0.05 * big, 0.045 * big,
                                   cap=4))
    hr = (0.16 if who == "guard" else 0.1) * big
    ps.append(_ell_m(0.36 * L, 0.0, hr, hr))
    K.polys(c, [_xf(q, p, heading, ppm) for q in ps], color)
