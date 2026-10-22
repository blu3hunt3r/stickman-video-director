"""SHADOW PLAY: the murder shadow play, one choreography for every scene that shows it
(s03 live through the binoculars, s05 twice in the split screen, pieces later).

Two paper-doll puppets on rods behind window 9's sheet, lit by a bare bulb: the bowler man
(cast.doll_man) and the bob woman (cast.doll_woman). Their life-size shadows act a murder.

    u (s)              beat
    < 0                the tableau holds: he (right) and she (left) face each other
    0.45 - 0.85        TURN_T       she turns away (a flat doll flipping on its rod)
    1.00 - 1.55        RAISE_T      his jagged Golden-Arm arm dips, then rises, knife in an
                                    ice-pick grip (overshoot, settle)
    1.85  2.25  2.65   STAB_TIMES   three stabs (knife contact). SCREAM_T = the first: her
                                    head snaps back, mouth open, a hand flies up (silent)
    2.65               SPLASH_T     the last stab: a RED cut-paper splash bursts on the sheet
    2.85 - 3.50        FALL_T       she folds at the waist and drops out of sight
    4.30               LIGHT_OUT_T  the bulb snaps out (lamp_level)
    4.50               SHOW_LEN     everything holds after this

u is seconds since the show started (u < 0 holds the tableau). In s03 the show starts at
8.0 (light out at 12.3). Outside view (from the street, s03/s05) the man stands RIGHT,
facing left; mirror=True gives the view from inside apartment 9 (man LEFT, as on the
table rig, Apartment9.RODS).

Puppet tells, always there, legible when s05 pushes in: the knife arm is two jagged
cut-paper pieces on round pin joints (shoulder, elbow) with a slotted pin in a ring of
light, a thin wire from the crank hooked to the forearm, and each doll stands on a rod.

USE
    from films.shadowplay.scenes import _lib_shadow_show as show

  * Facade window 9 (s03): the facade already draws the sheet and casts interiors as
    shadows (sets.shadow_screen), so pass the show as window 9's interior:
        start = 8.0
        fac.draw(f, t, lit={9: lambda t: sets.switch(t, T.at('light'), kind='flicker', seed=9)
                                          * show.lamp_level(t - start)},
                 curtains={9: show.CURTAIN}, interiors={9: show.interior(lambda t: t - start)},
                 emit=0.4)
    Keep the facade's `emit` low when window 9 is big on screen: the emissive rectangle is
    added after everything and washes the shadows out.
  * Any lit sheet you painted yourself (s05 panels, s07, s10 ...):
        show.draw_show(ctx, u, box, region=sheet_path_fn, lamp_center=(x, y), soft=2.0)
  * Raw casters: show.casters(ctx, u, box) draws opaque ink and the RED gel in world
    coords. It uses OPERATOR_CLEAR for the pin gaps and her open mouth, so draw it only
    into a shadow buffer (shadow_screen / the facade's shadow mode), never onto a frame.
  * Geometry: show.anchors(u, box) -> world points 'knife_tip', 'blade_root', 'fist',
    'elbow' (the pin), 'shoulder', 'wire_hook', 'his_head', 'her_head', 'her_back', 'splash',
    plus 'S' (stage unit, world px) for camera targets, red lines and sound pans.
  * Overrides: p = show.pose(u); p['arm'] = (sh, el, blade) degrees (screen angles in the
    outside view: 0 = +x, 90 = down); show.casters(..., pose=p) / anchors(..., pose=p).
    show.arm_angles(u) is the knife arm alone; keys REST, RAISED, CONTACT, DONE.

box = (x0, y0, x1, y1), the world rect the show is staged in (the window glass, the sheet).
The man is 0.74 x box height tall, feet 3.5 % of the box above its bottom (behind the
window's bottom rail on the facade), centred; stage=(ox, oy, S) sets the placement freely
(ox, oy = world point of the floor under the middle, S = the man's height in world px).
"""
import math

import cairo

from engine import bass, draw
from engine.core import clamp, ease, lerp
from engine.figure import Pose, solve, draw_figure, head_point
from engine.palette import RED

from films.shadowplay import cast
from films.shadowplay.sets import shadow_screen, paper_blood

# ----------------------------------------------------------------------------- the clock
TURN_T = (0.45, 0.85)
RAISE_T = (1.00, 1.55)
STAB_TIMES = (1.85, 2.25, 2.65)
SCREAM_T = STAB_TIMES[0]
SPLASH_T = STAB_TIMES[-1]
FALL_T = 2.85
LIGHT_OUT_T = 4.30
SHOW_LEN = 4.50

STRIKE = 0.11            # raised -> contact (accelerating)
HOLD = 0.05              # the knife stays in
RECOVER = 0.19           # contact -> raised

#: recommended facade curtain for window 9 (crisper shadows than the default sheet)
CURTAIN = dict(kind="sheet", soft=2.0, density=0.92)

SHADOW = (0.0, 0.0, 0.0)          # any opaque colour casts a full shadow
MAN_X, WOMAN_X = 0.205, -0.20     # stage x of the rods (outside view; 1 = the man's height)
HER_H = 0.95

# knife-arm dimensions (stage units)
L1, L2 = 0.200, 0.165             # shoulder->elbow, elbow->wrist
FIST = 0.036                      # wrist -> fist centre
BLADE = 0.160
R_SH, R_EL = 0.044, 0.042         # joint discs (round lobes wider than the arm)
R_PIN, R_HOLE = 0.0112, 0.0138    # pin head inside a thin ring of light
CRANK = (MAN_X + 0.03, 0.62)      # where the wire comes from (below the sheet)

# arm keys: (upper arm, forearm, blade) screen angles, degrees, outside view (facing left).
# The values are unwrapped so that lerp() swings the arm forward-and-over, never backward.
REST = (97.0, 104.0, 100.0)
DIP = (86.0, 97.0, 95.0)
RAISED = (298.0, 258.0, 112.0)
CONTACT = (200.0, 118.0, 112.0)
DONE = (128.0, 108.0, 102.0)

_LOOK_MAN = cast.doll_man(ink=None)
_LOOK_WOMAN = cast.doll_woman(ink=None)
_MAN_BODY, _WOMAN_BODY = cast.DOLL_MAN, cast.DOLL_WOMAN
_HIP = 0.533                      # pelvis height above the floor / body height (figure rig)
_SHOULDER = 0.274                 # shoulder above the pelvis / body height


def _k(u, t0, dur, e="inout"):
    """Eased 0..1 progress of a move starting at t0 (exact 0 and 1 outside it)."""
    if u <= t0:
        return 0.0
    if dur <= 0 or u >= t0 + dur:
        return 1.0
    return ease(e, (u - t0) / dur)


def _mix3(a, b, k):
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k))


# ----------------------------------------------------------------------------- stage
class Stage:
    """Stage units -> world: x right (outside view), y down, 1 unit = the man's height S.
    (0, 0) is the floor under the middle of the sheet. m = -1 mirrors (inside view)."""

    def __init__(self, ox, oy, S, m=1.0):
        self.ox, self.oy, self.S, self.m = float(ox), float(oy), float(S), float(m)

    def P(self, x, y):
        """Stage point -> world point, in the OUTSIDE-view drawing frame (no mirror)."""
        return (self.ox + x * self.S, self.oy + y * self.S)

    def out(self, p):
        """World point of the outside-view frame -> world point as shown (mirror applied)."""
        if self.m > 0:
            return p
        return (2 * self.ox - p[0], p[1])


def _stage_for(box, mirror=False, size=0.74, floor=0.035):
    """The default stage for a box (x0, y0, x1, y1): the man 0.74 x its height tall, feet
    3.5 % above its bottom, centred."""
    x0, y0, x1, y1 = box
    h = y1 - y0
    return Stage((x0 + x1) / 2.0, y1 - floor * h, size * h, -1.0 if mirror else 1.0)


stage = _stage_for


def _stage_of(box, mirror, place=None):
    if place is None:
        return _stage_for(box, mirror)
    ox, oy, S = place
    return Stage(ox, oy, S, -1.0 if mirror else 1.0)


# ----------------------------------------------------------------------------- choreography
def arm_angles(u):
    """(upper arm, forearm, blade) screen angles of the knife arm at show time u."""
    r0, r1 = RAISE_T
    if u <= r0:
        return REST
    if u < r0 + 0.12:
        return _mix3(REST, DIP, _k(u, r0, 0.12, "inout"))
    s_first = STAB_TIMES[0] - STRIKE
    if u < s_first:
        return _mix3(DIP, RAISED, _k(u, r0 + 0.12, r1 - r0 - 0.12, "outback"))
    n = len(STAB_TIMES)
    for i, ts in enumerate(STAB_TIMES):
        s0 = ts - STRIKE
        if u < s0:
            return RAISED
        if u < ts:
            return _mix3(RAISED, CONTACT, _k(u, s0, STRIKE, "in3"))
        if i == n - 1:
            if u < ts + 0.22:
                return CONTACT
            return _mix3(CONTACT, DONE, _k(u, ts + 0.22, 0.5, "inout"))
        if u < ts + HOLD:
            return CONTACT
        if u < ts + HOLD + RECOVER:
            return _mix3(CONTACT, RAISED, _k(u, ts + HOLD, RECOVER, "out3"))
    return DONE


def _impact(u, ts, decay=0.09):
    """A jolt envelope at a stab: snaps up in the last frames of the strike, then decays."""
    if u < ts - 0.04:
        return 0.0
    if u < ts:
        return (u - ts + 0.04) / 0.04
    return math.exp(-(u - ts) / decay)


def _pose_at(u):
    """Every animated value of the show at time u (a fresh dict you may edit)."""
    u = min(float(u), SHOW_LEN)
    turn = _k(u, TURN_T[0], TURN_T[1] - TURN_T[0], "inout3")
    scream = _k(u, SCREAM_T - 0.03, 0.10, "out3")
    jolt = sum(_impact(u, ts) for ts in STAB_TIMES)
    fold = _k(u, FALL_T, 0.30, "in")
    drop = _k(u, FALL_T + 0.10, 0.52, "in")
    lean = sum(_impact(u, ts, 0.16) for ts in STAB_TIMES)
    splash = _k(u, SPLASH_T - 0.01, 0.13, "outback")
    breathe = math.sin(u * 2.1 + 0.4)
    return dict(
        u=u, arm=arm_angles(u), turn=turn, flip=math.cos(math.pi * turn), scream=scream,
        jolt=jolt, fold=fold, drop=drop, lean=lean, splash=splash, breathe=breathe,
        mouth=scream, lamp=lamp_level(u),
    )


pose = _pose_at


def lamp_level(u):
    """The bulb behind the sheet: on through the show, then it snaps out at LIGHT_OUT_T."""
    if u < LIGHT_OUT_T:
        return 1.0
    return math.exp(-(u - LIGHT_OUT_T) / 0.045)


# ----------------------------------------------------------------------------- puppet geometry
def _band(L, w0, w1, kink, seed, teeth=3):
    """A jagged arm piece from (0, 0) to (L, 0) in local units: a broken centreline, saw
    teeth along both edges (The Man with the Golden Arm), scissor-cut."""
    cl = [(0.0, 0.0), (0.42 * L, kink), (0.63 * L, -0.7 * kink), (L, 0.0)]
    top, bot = [], []
    for i, (x, y) in enumerate(cl):
        a = cl[max(i - 1, 0)]
        b = cl[min(i + 1, len(cl) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n, dx / n
        hw = 0.5 * lerp(w0, w1, x / L)
        top.append((x + nx * hw, y + ny * hw))
        bot.append((x - nx * hw, y - ny * hw))

    def saw(edge, sgn, s2):
        out = [edge[0]]
        for i in range(len(edge) - 1):
            a, b = edge[i], edge[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / n * sgn, dx / n * sgn
            m = 1 + int(bass._h(seed, s2, i, 4) * teeth * 0.75)
            for q in range(m):
                f0 = (q + 0.2 + 0.3 * bass._h(seed, s2, i, q, 5)) / (m + 0.4)
                f1 = min(0.97, f0 + 0.14 + 0.1 * bass._h(seed, s2, i, q, 6))
                d = (0.20 + 0.25 * bass._h(seed, s2, i, q, 7)) * w0 * 0.5
                out.append((a[0] + dx * f0, a[1] + dy * f0))
                out.append((a[0] + dx * (f0 + f1) * 0.5 + nx * d, a[1] + dy * (f0 + f1) * 0.5 + ny * d))
                out.append((a[0] + dx * f1, a[1] + dy * f1))
            out.append(b)
        return out
    top = saw(top, 1.0, 1)
    bot = saw(bot, -1.0, 2)
    poly = top + bot[::-1]
    return bass.orient(bass.cut(poly, seed=seed, amp=0.0016, seg=(0.010, 0.026)), True)


def _fist():
    """Angular fist round the wrist end (local: forearm along +x, wrist at 0)."""
    pts = [(-0.010, -0.032), (0.024, -0.044), (0.056, -0.038), (0.074, -0.020), (0.068, -0.004),
           (0.080, 0.008), (0.070, 0.026), (0.048, 0.038), (0.018, 0.038), (-0.008, 0.028)]
    return bass.orient(bass.cut(pts, seed=71, amp=0.0012, seg=(0.008, 0.018)), True)


def _blade():
    """Knife blade + guard (local: root at 0, blade along +x)."""
    blade = [(-0.004, -0.012), (0.050, -0.0135), (0.112, -0.010), (BLADE, 0.0015), (0.118, 0.010),
             (0.060, 0.0125), (-0.004, 0.012)]
    guard = [(-0.010, -0.022), (0.002, -0.021), (0.003, 0.021), (-0.009, 0.022)]
    return [bass.orient(bass.cut(blade, seed=73, amp=0.0008, seg=(0.010, 0.03)), True), bass.orient(guard, True)]


_GEOM = {}


def _geom():
    if not _GEOM:
        _GEOM["upper"] = _band(L1, 0.078, 0.064, 0.022, seed=61)
        _GEOM["fore"] = _band(L2, 0.064, 0.052, -0.019, seed=67)
        _GEOM["fist"] = _fist()
        _GEOM["blade"] = _blade()
        _GEOM["sh_disc"] = bass.orient(bass.ring_pts((0.0, 0.0), R_SH, seed=81, n=26, amp=0.0012), True)
        _GEOM["el_disc"] = bass.orient(bass.ring_pts((0.0, 0.0), R_EL, seed=83, n=26, amp=0.0012), True)
    return _GEOM


def _xf(pts, at, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(at[0] + x * ca - y * sa, at[1] + x * sa + y * ca) for x, y in pts]


def _dir(deg):
    a = math.radians(deg)
    return math.cos(a), math.sin(a)


def _man_pose(st, p):
    """Figure Pose of the man doll (world, outside-view frame)."""
    S = st.S
    sc = S / _MAN_BODY.height
    x, y = st.P(MAN_X, -_HIP)
    q = Pose(x, y, 180.0)
    q.scale = sc
    q.pitch = 6.0 * p["lean"] + 0.6 * p["breathe"]
    q.head = 7.0
    q.arms["L"] = dict(sh=2.0, abd=4.0, elbow=6.0, wrist=0.0, grip=0.5)
    q.arms["R"] = dict(sh=-3.0, abd=4.0, elbow=8.0, wrist=0.0, grip=0.5)
    q.legs["L"] = dict(hip=4.0, abd=2.0, knee=3.0, ankle=0.0, toe=0.0)
    q.legs["R"] = dict(hip=-5.0, abd=2.0, knee=2.0, ankle=0.0, toe=0.0)
    return q


def _woman_pose(st, p):
    """Figure Pose of the woman doll, drawn facing +x (the flip mirrors her)."""
    S = st.S * HER_H
    sc = S / _WOMAN_BODY.height
    sc0, fd = p["scream"], p["fold"]
    x, y = st.P(WOMAN_X - 0.05 * fd, -_HIP * HER_H + 0.98 * p["drop"])
    q = Pose(x, y, 0.0)
    q.scale = sc
    q.pitch = -3.0 * sc0 * (1 - fd) + 6.0 * p["jolt"] * (1 - fd) + 92.0 * fd + 0.5 * p["breathe"]
    q.spine = [11.0 * fd, 13.0 * fd, 9.0 * fd]
    q.neck = -16.0 * sc0 * (1 - fd) + 22.0 * fd
    q.head = -38.0 * sc0 * (1 - fd) + 34.0 * fd
    q.arms["R"] = dict(sh=lerp(lerp(-6.0, 142.0, sc0), -75.0, fd), abd=6.0, elbow=lerp(lerp(10.0, 34.0, sc0), 10.0, fd),
                       wrist=lerp(0.0, -20.0, sc0), grip=lerp(0.3, 0.05, sc0))
    q.arms["L"] = dict(sh=lerp(lerp(8.0, -32.0, sc0), -70.0, fd), abd=6.0, elbow=lerp(12.0, 24.0, sc0),
                       wrist=0.0, grip=0.3)
    q.legs["L"] = dict(hip=lerp(3.0, 12.0, fd), abd=2.0, knee=lerp(2.0, 30.0, fd), ankle=0.0, toe=0.0)
    q.legs["R"] = dict(hip=lerp(-4.0, 4.0, fd), abd=2.0, knee=lerp(2.0, 22.0, fd), ankle=0.0, toe=0.0)
    return q


def _arm_points(st, p, sk_man):
    """Knife-arm joints in the outside-view drawing frame (world)."""
    S = st.S
    sh = sk_man.j["shoulder_R"]
    sh = (sh[0] - 0.006 * S, sh[1] + 0.004 * S)
    a_sh, a_el, a_bl = p["arm"]
    d1, d2, d3 = _dir(a_sh), _dir(a_el), _dir(a_bl)
    el = (sh[0] + d1[0] * L1 * S, sh[1] + d1[1] * L1 * S)
    wr = (el[0] + d2[0] * L2 * S, el[1] + d2[1] * L2 * S)
    fi = (wr[0] + d2[0] * FIST * S, wr[1] + d2[1] * FIST * S)
    root = (fi[0] + d3[0] * 0.012 * S, fi[1] + d3[1] * 0.012 * S)
    tip = (root[0] + d3[0] * BLADE * S, root[1] + d3[1] * BLADE * S)
    hook = (el[0] + d2[0] * 0.075 * S - d2[1] * 0.016 * S, el[1] + d2[1] * 0.075 * S + d2[0] * 0.016 * S)
    return dict(shoulder=sh, elbow=el, wrist=wr, fist=fi, blade_root=root, knife_tip=tip, wire_hook=hook)


def _splash_center(st):
    """Where the last stab enters her back (fixed: the splash is pinned there)."""
    sk = solve(_man_pose(st, dict(lean=1.0, breathe=0.0)), _MAN_BODY)
    a = _arm_points(st, dict(arm=CONTACT), sk)
    r, tp = a["blade_root"], a["knife_tip"]
    return (lerp(r[0], tp[0], 0.42), lerp(r[1], tp[1], 0.42))


# ----------------------------------------------------------------------------- drawing
def _fill(ctx, polys, rgb=SHADOW):
    ctx.new_path()
    for pts in polys:
        draw.poly(ctx, pts)
    draw.fill(ctx, rgb, 1.0)


def _clear(ctx, build):
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.new_path()
    build(ctx)
    ctx.fill()
    ctx.restore()


def _rod(ctx, top, bottom_y, w):
    ctx.new_path()
    ctx.rectangle(top[0] - w / 2, top[1], w, bottom_y - top[1])
    draw.fill(ctx, SHADOW)


def _draw_knife_arm(ctx, st, p, A, cuts):
    G = _geom()
    S = st.S
    a_sh, a_el, a_bl = (math.radians(v) for v in p["arm"])
    sh, el, fi, root = A["shoulder"], A["elbow"], A["fist"], A["blade_root"]

    def to_w(pts, at, ang):
        return [(at[0] + x * S * math.cos(ang) - y * S * math.sin(ang),
                 at[1] + x * S * math.sin(ang) + y * S * math.cos(ang)) for x, y in pts]
    # the crank wire first (it hooks under the forearm)
    cw = st.P(*CRANK)
    hook = A["wire_hook"]
    dx, dy = cw[0] - hook[0], cw[1] - hook[1]
    n = math.hypot(dx, dy) or 1.0
    ww = 0.0026 * S
    nx, ny = -dy / n * ww / 2, dx / n * ww / 2
    _fill(ctx, [[(hook[0] + nx, hook[1] + ny), (cw[0] + nx, cw[1] + ny), (cw[0] - nx, cw[1] - ny),
                 (hook[0] - nx, hook[1] - ny)]])
    polys = [to_w(G["upper"], sh, a_sh), to_w(G["sh_disc"], sh, a_sh), to_w(G["el_disc"], el, a_sh),
             to_w(G["fore"], el, a_el), to_w(G["fist"], A["wrist"], a_el)]
    polys += [to_w(b, root, a_bl) for b in G["blade"]]
    _fill(ctx, polys)
    # eyelet where the wire hooks on
    draw.circle(ctx, hook, 0.0068 * S)
    draw.fill(ctx, SHADOW)
    if not cuts:
        return
    # pin joints: a slotted pin in a ring of light (the slot turns with the forearm)
    for c, ang in ((el, a_el),):
        def ring(cx, c=c):
            cx.new_sub_path()
            cx.arc(c[0], c[1], R_HOLE * S, 0, 2 * math.pi)
            cx.new_sub_path()
            cx.arc_negative(c[0], c[1], R_PIN * S, 2 * math.pi, 0)
        _clear(ctx, ring)

        def slot(cx, c=c, ang=ang):
            ca, sa = math.cos(ang), math.sin(ang)
            hl, hw = R_PIN * 0.82 * S, 0.0022 * S
            draw.poly(cx, [(c[0] - ca * hl + sa * hw, c[1] - sa * hl - ca * hw),
                           (c[0] + ca * hl + sa * hw, c[1] + sa * hl - ca * hw),
                           (c[0] + ca * hl - sa * hw, c[1] + sa * hl + ca * hw),
                           (c[0] - ca * hl - sa * hw, c[1] - sa * hl + ca * hw)])
        _clear(ctx, slot)
    # the eyelet's hole
    _clear(ctx, lambda cx: draw.circle(cx, hook, 0.0032 * S))


def _draw_man(ctx, st, p, cuts):
    q = _man_pose(st, p)
    sk = solve(q, _MAN_BODY)
    _rod(ctx, sk.j["pelvis"], st.P(0, 0.7)[1], 0.007 * st.S)
    draw_figure(None, sk, _LOOK_MAN, ctx, color=SHADOW, eyes=False)
    A = _arm_points(st, p, sk)
    _draw_knife_arm(ctx, st, p, A, cuts)
    return sk, A


def _draw_woman(ctx, st, p, cuts):
    q = _woman_pose(st, p)
    sk = solve(q, _WOMAN_BODY)
    rx = st.P(WOMAN_X, 0)[0]
    _rod(ctx, (rx, sk.j["pelvis"][1]), st.P(0, 0.7 + 1.0)[1], 0.007 * st.S)
    sx = p["flip"]
    sx = math.copysign(max(abs(sx), 0.03), sx if sx != 0 else 1.0)
    ctx.save()
    ctx.translate(rx, 0)
    ctx.scale(sx, 1.0)
    ctx.translate(-rx, 0)
    draw_figure(None, sk, _LOOK_WOMAN, ctx, color=SHADOW, eyes=False)
    if cuts and p["mouth"] > 0.02:
        m = p["mouth"]

        def mouth(cx):
            pts = [head_point(sk, 0.17, 0.25), head_point(sk, 0.47, 0.25 + 0.10 * m),
                   head_point(sk, 0.44, 0.25 - 0.11 * m)]
            draw.poly(cx, pts)
        _clear(ctx, mouth)
    ctx.restore()
    return sk


def casters(ctx, u, box, mirror=False, stage=None, pose=None, cuts=True, blood=True, man=True,
            woman=True):
    """Draw the show's shadow casters at show time u (world coords on ctx): opaque ink for
    the dolls, rods and wire, RED (a gel) for the splash. stage=(ox, oy, S) places the show
    freely; pose= a dict from show.pose(u) you edited. See the module docstring."""
    st = _stage_of(box, mirror, stage)
    p = pose if pose is not None else _pose_at(u)
    ctx.save()
    if st.m < 0:
        ctx.translate(2 * st.ox, 0)
        ctx.scale(-1, 1)
    if blood and p["splash"] > 0.0:
        c = _splash_center(st)
        paper_blood(ctx, c, 0.0024 * st.S, seed=5, grow=p["splash"], angle=-18.0, color=RED)
    if woman:
        _draw_woman(ctx, st, p, cuts)
    if man:
        _draw_man(ctx, st, p, cuts)
    ctx.restore()


def interior(u_of_t, mirror=False, **kw):
    """A Facade interior callback fn(ctx, win) playing the show at u = u_of_t(win.t) in the
    window's glass rect (cuts only when the facade casts it as shadows)."""
    def fn(ctx, win):
        casters(ctx, u_of_t(win.t), win.rect, mirror=mirror, cuts=(win.mode == "shadow"), **kw)
    return fn


def draw_show(f_or_ctx, u, box, region=None, lamp_center=None, soft=2.0, density=0.92, mag=1.0,
              mirror=False, bbox=None, gel=1.0, **kw):
    """Cast the show (sets.shadow_screen: multiplied shadows, RED splash as a gel) onto
    whatever is already painted on the context (a lit sheet) at show time u.
    f_or_ctx: a cairo context in world coords (or a Frame: drawn on its main canvas).
    region: callable building the sheet's world path (or a cairo.Path) to clip to;
    bbox: the screen's world rect (default: box). lamp_center/mag: magnify about the lamp."""
    ctx = f_or_ctx if isinstance(f_or_ctx, cairo.Context) else f_or_ctx.ctx
    shadow_screen(ctx, lambda c: casters(c, u, box, mirror=mirror, **kw), region=region,
                  bbox=bbox or box, soft=soft, density=density, mag=mag, center=lamp_center, gel=gel)


# ----------------------------------------------------------------------------- anchors
def anchors(u, box, mirror=False, stage=None, pose=None):
    """World points of the show at time u (as shown, mirror applied) + 'S' (stage unit)."""
    st = _stage_of(box, mirror, stage)
    p = pose if pose is not None else _pose_at(u)
    skm = solve(_man_pose(st, p), _MAN_BODY)
    A = _arm_points(st, p, skm)
    skw = solve(_woman_pose(st, p), _WOMAN_BODY)
    rx = st.P(WOMAN_X, 0)[0]
    sx = p["flip"]

    def fl(pt):
        return (rx + (pt[0] - rx) * sx, pt[1])
    out = {k: st.out(v) for k, v in A.items()}
    out["his_head"] = st.out(skm.j["head"])
    out["her_head"] = st.out(fl(skw.j["head"]))
    ch = skw.j["chest"]
    out["her_back"] = st.out(fl((ch[0] - 0.06 * st.S, ch[1])))
    out["splash"] = st.out(_splash_center(st))
    out["S"] = st.S
    return out
