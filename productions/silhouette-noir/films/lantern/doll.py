"""THE LANTERN's girl as a Saul Bass paper doll: flat cut-paper pieces hinged at pins.

Every piece is cut once (scissor edges, fixed seeds) in local coordinates and placed with
cairo transforms, so edges never boil while she moves. Animate her on twos.

    pose = Pose(hip_f=20, hip_b=-20, sh_f=60, el_f=-20, ...)
    hand = draw_girl(ctx, (x, ground_y), pose, ink, red)    # returns the front hand position

Local frame: feet on y = 0, facing +x, height about 620 px at scale 1.
"""
import math
from dataclasses import dataclass
from functools import lru_cache

from engine import bass, draw

LEG = 232.0          # hip pin to sole
HIP_Y = -244.0
SHOULDER = (2.0, -462.0)
UPPER, FORE = 118.0, 108.0


@dataclass
class Pose:
    hip_f: float = 0.0       # degrees from straight down, + = forward (toward +x)
    hip_b: float = 0.0
    knee_f: float = 0.0      # bend of the lower leg (+ = foot swings back)
    knee_b: float = 0.0
    sh_f: float = 10.0       # front arm (the lantern arm)
    el_f: float = 0.0        # + = forearm swings forward/up
    sh_b: float = -10.0
    el_b: float = 0.0
    lean: float = 0.0        # whole body, + = forward
    head: float = 0.0        # head tilt, + = looks up
    pony: float = 0.0        # ponytail swing, + = flies back/up
    scarf: float = 0.0       # scarf tail lift, + = streams out
    bob: float = 0.0         # extra vertical offset (px, + = down)
    toy: bool = False        # the back arm hugs the toy horse


def _cut(pts, seed, amp=1.2):
    return bass.cut(pts, seed=seed, amp=amp, seg=(14.0, 40.0))


@lru_cache(maxsize=1)
def parts():
    P = {}
    P["head"] = bass.cut_ellipse((10.0, -548.0), 58.0, 64.0, seed=11)
    P["neck"] = _cut([(-12, -494), (16, -494), (16, -470), (-12, -470)], 12)
    P["dress"] = _cut([(-40, -484), (46, -484), (70, -362), (110, -236), (-104, -236), (-66, -362)], 13)
    # ponytail: a teardrop hanging from its pin at the back of the head (local to the pin)
    P["pony"] = bass.scissor([(0, 0), (-18, 6), (-52, 40), (-66, 96), (-54, 128), (-40, 96), (-22, 46), (-4, 14)],
                             seed=14, sag=1.0, amp=0.8, max_len=26.0)
    P["bow"] = _cut([(-6, -10), (14, -22), (12, 8), (-6, 4), (-22, 16), (-20, -14)], 15)
    P["eye"] = bass.cut_ellipse((42.0, -556.0), 7.0, 9.0, seed=16)
    # scarf: wrap at the neck and a two-tailed end (tail local to its pin at the nape)
    P["wrap"] = _cut([(-48, -500), (54, -500), (56, -466), (-50, -464)], 17)
    P["tail"] = _cut([(0, -8), (-60, -14), (-128, -4), (-150, 12), (-112, 14), (-130, 34), (-70, 22), (0, 22)], 18)
    # a leg: strip from the hip pin (0, 0) down to the knee, shin from the knee pin, a boot
    P["thigh"] = _cut([(-19, -6), (19, -6), (17, 122), (-17, 122)], 19)
    P["shin"] = _cut([(-17, -4), (17, -4), (15, LEG - 120 - 20), (-15, LEG - 120 - 20)], 20)
    P["boot"] = _cut([(-18, LEG - 140), (16, LEG - 140), (20, LEG - 128), (44, LEG - 124), (46, LEG - 112),
                      (-18, LEG - 112)], 21)
    P["upper"] = _cut([(-12, -6), (12, -6), (11, UPPER), (-11, UPPER)], 22)
    P["fore"] = _cut([(-11, -4), (11, -4), (10, FORE), (-10, FORE)], 23)
    P["hand"] = bass.cut_ellipse((0.0, FORE + 10.0), 17.0, 19.0, seed=24)
    P["toy"] = toy_polys(25)
    return P


def toy_polys(seed=25, k=1.0):
    """Her brother's wooden horse on wheels, feet on y = 0, about 100 px tall at k = 1."""
    S = lambda pts: [(x * k, y * k) for x, y in pts]
    return [
        bass.cut_ellipse((0.0, -56.0 * k), 38.0 * k, 17.0 * k, seed=seed),
        bass.cut(S([(20, -66), (34, -104), (48, -114), (66, -104), (64, -94), (46, -92), (36, -60)]), seed=seed + 1, amp=1.0),
        bass.cut(S([(34, -108), (38, -126), (44, -110)]), seed=seed + 2, amp=0.6),
        bass.cut(S([(-36, -64), (-58, -52), (-62, -32), (-48, -50), (-34, -50)]), seed=seed + 3, amp=0.8),
        bass.cut(S([(-28, -48), (-20, -48), (-20, -22), (-28, -22)]), seed=seed + 4, amp=0.6),
        bass.cut(S([(-12, -48), (-4, -48), (-4, -22), (-12, -22)]), seed=seed + 5, amp=0.6),
        bass.cut(S([(12, -48), (20, -48), (20, -22), (12, -22)]), seed=seed + 6, amp=0.6),
        bass.cut(S([(26, -48), (34, -48), (34, -22), (26, -22)]), seed=seed + 7, amp=0.6),
        bass.cut(S([(-46, -24), (46, -24), (46, -14), (-46, -14)]), seed=seed + 8, amp=0.6),
        bass.cut_ellipse((-30.0 * k, -9.0 * k), 10.0 * k, 10.0 * k, seed=seed + 9),
        bass.cut_ellipse((30.0 * k, -9.0 * k), 10.0 * k, 10.0 * k, seed=seed + 10),
    ]


def _xf(ctx, x, y, deg):
    ctx.translate(x, y)
    ctx.rotate(math.radians(deg))


def _fill(ctx, polys, rgb):
    bass.fill_polys(ctx, polys, rgb)


def _leg(ctx, hip_x, hip_deg, knee_deg, ink):
    ctx.save()
    _xf(ctx, hip_x, HIP_Y, -hip_deg)          # + forward = counter-clockwise toward +x
    _fill(ctx, [parts()["thigh"]], ink)
    _xf(ctx, 0.0, 118.0, knee_deg)
    _fill(ctx, [parts()["shin"], parts()["boot"]], ink)
    ctx.restore()


def _arm(ctx, sh_deg, el_deg, ink, extra=None):
    """Draw an arm from the shoulder pin; returns the hand centre in the doll's local frame."""
    ctx.save()
    _xf(ctx, SHOULDER[0], SHOULDER[1], -sh_deg)
    _fill(ctx, [parts()["upper"]], ink)
    _xf(ctx, 0.0, UPPER, -el_deg)
    _fill(ctx, [parts()["fore"], parts()["hand"]], ink)
    if extra is not None:
        extra(ctx)
    ctx.restore()
    a1 = math.radians(sh_deg)
    a2 = math.radians(sh_deg + el_deg)
    ex = SHOULDER[0] + math.sin(a1) * UPPER
    ey = SHOULDER[1] + math.cos(a1) * UPPER
    return ex + math.sin(a2) * (FORE + 10.0), ey + math.cos(a2) * (FORE + 10.0)


def draw_girl(ctx, foot, pose, ink, red, scale=1.0):
    """Draw her at `foot` (screen px, the point between her feet). Returns the front hand in
    screen px (where the lantern's bail hangs) and the hand's total rotation (deg)."""
    P = parts()
    ctx.save()
    ctx.translate(foot[0], foot[1] + pose.bob)
    ctx.scale(scale, scale)
    # the body leans about the hips
    ctx.save()
    _leg(ctx, -6.0, pose.hip_b, pose.knee_b, ink)
    ctx.restore()
    ctx.save()
    _xf(ctx, 0.0, HIP_Y, pose.lean)
    ctx.translate(0.0, -HIP_Y)
    if pose.toy:
        def hug(c):
            c.translate(14.0, FORE + 4.0)
            c.rotate(math.radians(-pose.sh_b - pose.el_b - 8.0))
            _fill(c, P["toy"], ink)
        _arm(ctx, pose.sh_b, pose.el_b, ink, extra=hug)
    else:
        _arm(ctx, pose.sh_b, pose.el_b, ink)
    _fill(ctx, [P["neck"], P["dress"]], ink)
    # head, tilting about the neck
    ctx.save()
    _xf(ctx, 4.0, -488.0, -pose.head)
    ctx.translate(-4.0, 488.0)
    _fill(ctx, [P["head"]], ink)
    ctx.save()
    _xf(ctx, -40.0, -584.0, pose.pony)
    _fill(ctx, [P["pony"]], ink)
    ctx.restore()
    ctx.save()
    ctx.translate(-42.0, -590.0)
    _fill(ctx, [P["bow"]], red)
    ctx.restore()
    _fill(ctx, [P["eye"]], bass.PAPER)
    ctx.restore()
    # scarf over the neck
    _fill(ctx, [P["wrap"]], red)
    ctx.save()
    _xf(ctx, -40.0, -488.0, pose.scarf)
    _fill(ctx, [P["tail"]], red)
    ctx.restore()
    ctx.restore()
    _leg(ctx, 8.0, pose.hip_f, pose.knee_f, ink)
    # the front (lantern) arm last, in front of the dress
    ctx.save()
    _xf(ctx, 0.0, HIP_Y, pose.lean)
    ctx.translate(0.0, -HIP_Y)
    hx, hy = _arm(ctx, pose.sh_f, pose.el_f, ink)
    ctx.restore()
    ctx.restore()
    # local hand -> screen (rotate about the hip by lean, then scale and place)
    a = math.radians(pose.lean)
    dx, dy = hx, hy - HIP_Y
    rx = dx * math.cos(a) - dy * math.sin(a)
    ry = dx * math.sin(a) + dy * math.cos(a) + HIP_Y
    return (foot[0] + rx * scale, foot[1] + pose.bob + ry * scale)


def draw_toy(ctx, foot, ink, k=1.0, angle=0.0):
    ctx.save()
    ctx.translate(*foot)
    if angle:
        ctx.rotate(math.radians(angle))
    bass.fill_polys(ctx, toy_polys(25, k) if k != 1.0 else parts()["toy"], ink)
    ctx.restore()


def walk_pose(phase, stride=1.0, run=False):
    """Scissor-leg walk (phase in cycles): swing amplitude scales with stride (0 = stand)."""
    s = math.sin(2 * math.pi * phase)
    c = math.cos(2 * math.pi * phase)
    amp = (30.0 if run else 21.0) * stride
    p = Pose()
    p.hip_f = amp * s
    p.hip_b = -amp * s
    # the lifted leg bends its knee as it swings through
    p.knee_f = max(0.0, c) * (48.0 if run else 26.0) * stride
    p.knee_b = max(0.0, -c) * (48.0 if run else 26.0) * stride
    p.sh_b = -(28.0 if run else 18.0) * s * stride - (20.0 if run else 0.0) * stride
    p.el_b = (50.0 if run else 14.0) * stride
    p.lean = (12.0 if run else 3.0) * stride
    p.bob = -7.0 * abs(c) * stride          # up as the legs pass, down at the stride
    p.pony = 8.0 * math.sin(2 * math.pi * phase * 2 - 0.8) * stride + (24.0 if run else 6.0) * stride
    p.scarf = 6.0 * math.sin(2 * math.pi * phase * 2 - 1.2) * stride + (22.0 if run else 6.0) * stride
    return p
