"""s02 · AMBER (12-26): a quarter to midnight in her room. The kettle sings; she lifts it and
pours; she carries her mug to the window and looks up and across; the Bass sip; over her
shoulder, her look flies to his lit window, and the first shout jumps back out of it.

Shots (scene time):
  A 0.0-3.0   WIDE on her room (rooms.draw_stage), continuing s01's push from rooms.S01_END.
              The kettle steams, then whistles (PAPER ripples on the beat); the clock ticks
              on the beat (a callout lens shows 11:46); she takes the kettle at T_REACH and
              lifts it at T_LIFT, the gas goes off, she brings it over her mug.
  B 3.0-5.0   CLOSE ON THE POUR: the spout tips over her mug, an INK stream, steam; she sets
              the kettle back on the burner.
  C 5.0-8.0   WIDE: she walks to the window with the mug (mocap 137_26), stops at the glass,
              looks up and across.
  D 8.0-10.0  THE SIP: the Bass sip close-up at tb = 5.6 + (t - 8.0), held to 10.0.
  E 10.0-14.0 OVER HER SHOULDER (rooms.draw_window_view): his lit window across the street,
              the couple quarrelling in it; her PAPER sight line flies to it and marches; the
              first red zigzag of shouting jumps out of it at T_BOLT[0].
"""
import math
from dataclasses import replace
from functools import lru_cache

import cairo

from engine import bass, mocap as mc, paperdoll as pd
from engine.core import clamp, ease, lerp
from engine.palette import RED
from engine.timing import Cue
from films.opposite_bass import world as B
from films.opposite_full import kit as K
from films.opposite_full import rooms as R

k = K.k
INK, PAPER, AMBER = K.INK, K.PAPER, K.AMBER

# ---------------------------------------------------------------- beats (scene time)
T_STEAM = 0.3                 # the kettle starts to sing ...
T_WHISTLE = 1.0               # ... and whistles full
T_RIPPLES = (0.5, 1.0, 1.5)   # the whistle's rings, on the beat
CLOCK_IN, CLOCK_OUT = 0.45, 2.6   # the callout lens on the wall clock opens / closes
T_REACH = 1.4                 # her hand goes to the kettle's grip
T_LIFT = 2.0                  # she lifts it off the flame: the whistle dies
T_GAS = 2.25                  # the gas off
T_TIP = 2.7                   # the kettle tips toward the mug
T_CU = 3.0                    # cut: close on the pour
T_POUR = 3.22                 # the stream reaches the mug
T_POUR_END = 4.42             # the kettle tips back, the stream's tail falls
T_SET = 4.52                  # the kettle goes back on the burner ...
T_DOWN = 4.76                 # ... and lands
T_GRAB = 4.6                  # her other hand comes in for the mug ...
T_GRIP = 4.8                  # ... closes on its handle ...
T_MUG_UP = 4.86               # ... and lifts it (the cut is on the lift)
T_WIDE = 5.0                  # cut: wide, she walks to the window
T_LOOK = 7.35                 # stopped at the glass, she looks up and across
T_SIP = 8.0                   # cut: the Bass sip
SIP_TB = 5.6                  # ... at tb = SIP_TB + (t - T_SIP)
T_OTS = 10.0                  # cut: over her shoulder
T_SIGHT = 10.6                # her sight line flies to his window
T_BOLT = (12.6, 13.5)         # red zigzags of shouting out of his window
QUARREL_TB = 3.4              # the couple in his window at Bass time t - QUARREL_TB

S01_FILM = 12.0               # film time at t = 0 (the clock, s01's sway)


def twos(t):
    return K.twos(t)


# ---------------------------------------------------------------- her figure on the stage
@lru_cache(maxsize=1)
def fig():
    """Her cut-out as s01 draws her in the section (the arms a little thicker)."""
    return B.win_fig(0)


def to_fig(p, x0):
    """Stage px -> figure units for a figure placed at stage x0 on the floor."""
    return ((p[0] - x0) / R.FIG_S, (p[1] - R.FLOOR) / R.FIG_S)


def to_stage(p, x0):
    return (x0 + p[0] * R.FIG_S, R.FLOOR + p[1] * R.FIG_S)


def shoulder(f, st, p, facing):
    P = st["pelvis"]
    q = pd._rot(f.shoulder, p.lean)
    return (P[0] + facing * q[0], P[1] + p.crouch + q[1])


def wrist_fk(f, sh, spec, lean, facing):
    a1 = spec[1] + lean
    a2 = a1 + spec[2]
    el = (sh[0] + facing * math.sin(math.radians(a1)) * f.upper, sh[1] + math.cos(math.radians(a1)) * f.upper)
    return (el[0] + facing * math.sin(math.radians(a2)) * f.fore, el[1] + math.cos(math.radians(a2)) * f.fore)


def ik_ang(f, sh, target, lean, facing, down=True):
    """An ("ang", sh, el) arm that puts the wrist on target with the elbow below the line from
    shoulder to wrist (down) or above it."""
    best = None
    for fw in (1.0, -1.0):
        e, w = pd.ik2(sh, target, f.upper, f.fore, forward=fw)
        if best is None or ((e[1] > best[0][1]) == down):
            best = (e, w)
    e, w = best
    a1 = math.degrees(math.atan2(facing * (e[0] - sh[0]), e[1] - sh[1]))
    a2 = math.degrees(math.atan2(facing * (w[0] - e[0]), w[1] - e[1]))
    return ("ang", mc._wrap(a1 - lean), mc._wrap(a2 - a1))


def wrist_for_hand(f, sh, hc):
    """The wrist target that puts the centre of her fist on hc (figure units)."""
    L = 1.75 * f.hand_r
    d = math.dist(sh, hc) or 1.0
    u = ((hc[0] - sh[0]) / d, (hc[1] - sh[1]) / d)
    return (hc[0] - u[0] * 0.5 * L, hc[1] - u[1] * 0.5 * L)


def draw_her(c, st, p, x0, facing, bg):
    c.save()
    B.place(c, x0, R.FLOOR, R.FIG_S)
    out = B.draw_cutout(c, fig(), st, p, INK, facing=facing, edge=bg, outline=bg, ow=10.0)
    c.restore()
    return out


# ---------------------------------------------------------------- the kettle's journey (stage px)
def kettle_matrix(grip, tilt, s=R.KETTLE_S):
    """Kettle units -> px: the grip at `grip`, tipped `tilt` deg (spout down) about it."""
    m = cairo.Matrix()
    m.translate(*grip)
    m.rotate(math.radians(-tilt))
    m.scale(s, s)
    m.translate(-R.KETTLE_GRIP[0], -R.KETTLE_GRIP[1])
    return m


def grip_for_mouth(mouth, tilt):
    """Where the grip must be for the spout's mouth to be at `mouth` at this tilt."""
    q = kettle_matrix((0.0, 0.0), tilt).transform_point(*R.KETTLE_MOUTH)
    return (mouth[0] - q[0], mouth[1] - q[1])


KETTLE_REST_GRIP = R.kettle_xf(R.KETTLE_BASE, R.KETTLE_S, 0.0).transform_point(*R.KETTLE_GRIP)
GRIP_UP = (KETTLE_REST_GRIP[0] - 14.0, KETTLE_REST_GRIP[1] - 30.0)     # lifted clear of the burner
MUG_RIM = (R.MUG_HC[0] - 20.0 * R.MUG_S, R.MUG_HC[1] - 26.0 * R.MUG_S)
TILT_POUR = 40.0
GRIP_POUR = grip_for_mouth((MUG_RIM[0] + 6.0, MUG_RIM[1] - 24.0), TILT_POUR)      # over the mug, tipped


def kettle_state(t):
    """(grip px, tilt deg, in_hand) of the kettle at t."""
    if t < T_LIFT:
        return KETTLE_REST_GRIP, 0.0, False
    if t >= T_DOWN:
        return KETTLE_REST_GRIP, 0.0, False
    up = k(t, T_LIFT, 0.3, "out3")
    over = k(t, T_LIFT + 0.3, 0.45, "inout")
    g = (lerp(KETTLE_REST_GRIP[0], GRIP_UP[0], up), lerp(KETTLE_REST_GRIP[1], GRIP_UP[1], up))
    g = (lerp(g[0], GRIP_POUR[0], over), lerp(g[1], GRIP_POUR[1], over))
    tilt = 12.0 * k(t, T_TIP, 0.3, "inout") + (TILT_POUR - 12.0) * k(t, T_CU, 0.2, "out3")
    tilt += 3.0 * k(t, T_POUR + 0.3, T_POUR_END - T_POUR - 0.3, "inout")          # tipping further as it empties
    back = k(t, T_POUR_END, 0.2, "inout")
    tilt *= 1.0 - back
    # back onto the burner
    sb = k(t, T_SET, T_DOWN - T_SET, "inout")
    g = (lerp(g[0], KETTLE_REST_GRIP[0], sb), lerp(g[1], KETTLE_REST_GRIP[1], sb) - 22.0 * math.sin(math.pi * sb))
    return g, tilt, True


def whistle_amt(t):
    return k(t, T_STEAM, T_WHISTLE - T_STEAM, "in") * (1.0 - k(t, T_LIFT, 0.25, "out"))


def room_at(t):
    """Her room's state through the scene."""
    _, _, in_hand = kettle_state(t)
    steam = 1.0 if t < T_LIFT else (0.0 if T_CU <= t < T_WIDE else 0.35)     # (in the close-up only the mug steams)
    return R.Room(lit=True, kettle=not in_hand, flame=t < T_GAS, steam=steam,
                  whistle=whistle_amt(t), mug=t < T_WIDE, film_t=S01_FILM + t)


# ---------------------------------------------------------------- A: the kettle sings
CAM_A = R.Cam(452.0, 1178.0, 0.97)


def cam_a(t):
    return R.cam_lerp(R.S01_END, CAM_A, k(t, 0.0, T_CU, "inout"))


def her_pose_a(t):
    """At the stove (where s01 leaves her, its pose and sway), then the kettle."""
    f = fig()
    tt = twos(S01_FILM + t)
    st = pd.standing(f, 0.0)
    sway = math.sin(2.0 * math.pi * 0.3 * tt)
    p = pd.Pose(lean=5.0 + 1.5 * sway, head=-10.0, arms={"near": ("ang", 34.0, 58.0), "far": ("ang", 18.0, 52.0)})
    x0 = R.SPOT_STOVE
    grip, tilt, in_hand = kettle_state(t)
    reach = k(t, T_REACH, 0.4, "inout")
    if reach > 0.0:
        # lean in to the kettle; the head goes down to it, and to the mug as she pours
        over = k(t, T_LIFT + 0.3, 0.45, "inout")              # (she leans in over the stove to pour)
        p.lean = lerp(p.lean, 8.0 + 6.0 * over + 3.0 * k(t, T_TIP, 0.3), reach)
        p.head = lerp(-10.0, -16.0 - 6.0 * k(t, T_TIP, 0.3), reach)
        sh = shoulder(f, st, p, -1)
        w0 = wrist_fk(f, sh, p.arms["near"], p.lean, -1)
        w1 = wrist_for_hand(f, sh, to_fig(grip, x0))
        p.arms["near"] = ik_ang(f, sh, (lerp(w0[0], w1[0], reach), lerp(w0[1], w1[1], reach)), p.lean, -1)
        # the gas: her far hand to the knob, then down at her side
        g = k(t, T_GAS - 0.18, 0.14, "out") * (1.0 - k(t, T_GAS + 0.08, 0.2, "inout"))
        rest = k(t, T_GAS + 0.08, 0.3, "inout")
        if rest > 0.0:
            p.arms["far"] = B._toward(p.arms["far"], 8.0 - p.lean, 24.0, rest)
        if g > 0.0:
            knob = to_fig((R.X_STOVE + 109.0, 1314.0), x0)
            w0f = wrist_fk(f, sh, p.arms["far"], p.lean, -1)
            p.arms["far"] = ik_ang(f, sh, (lerp(w0f[0], knob[0], g), lerp(w0f[1], knob[1], g)), p.lean, -1)
    if in_hand:
        def hold(c, H, grip=grip, tilt=tilt):
            m = kettle_matrix(H["hc"], tilt, R.KETTLE_S / R.FIG_S)
            R.draw_kettle(c, None, R.KETTLE_S / R.FIG_S, tilt, t, steam=0.35 * (1.0 - k(t, T_LIFT, 0.6)), xf=m)
        p.hold["near"] = hold
    return st, p, x0


def clock_lens(c, t, cam):
    """The callout: a lens on the wall clock, 11:46, its second hand ticking on the beat."""
    u = k(t, CLOCK_IN, 0.3, "linear") * (1.0 - k(t, CLOCK_OUT, 0.18, "linear"))
    if u <= 0.0:
        return
    anchor = cam.to_frame((R.CLOCK_P[0] - 20.0, R.CLOCK_P[1] - 32.0))
    centre, r = (300.0, 560.0), 168.0
    hms = R.clock_time(S01_FILM + t)

    def inside(c):
        K.fill(c, AMBER)
        R.draw_clock(c, centre, 128.0, hms, face=PAPER, ink=INK, rim=INK, seed=51)
    K.callout(c, anchor, centre, r, inside, u=u, ring_w=10.0, dot_r=8.0, line_w=4.0, seed=52)


def draw_a(c, t):
    cam = cam_a(t)
    room = room_at(t)
    st, p, x0 = her_pose_a(t)

    def figures(c):
        draw_her(c, st, p, x0, -1, R.room_bg(room))

    def overlay(c):
        # the whistle: rings out of the cap, on the beat, while it blows
        if room.kettle and room.whistle > 0.05:
            tip = R.kettle_xf(R.KETTLE_BASE, R.KETTLE_S, 0.0).transform_point(*R.KETTLE_SPOUT)
            for t0 in T_RIPPLES:
                if t0 <= t < T_LIFT + 0.1:
                    K.ripple(c, (tip[0] - 8.0, tip[1] - 6.0), t, t0, PAPER, n=2, every=0.12, life=0.5, r0=8.0, r1=74.0,
                             width=5.0, seed=int(t0 * 10), alpha=min(1.0, room.whistle * 1.3))

    R.draw_stage(c, t, room, cam=cam, figures=figures, overlay=overlay)
    clock_lens(c, t, cam)


# ---------------------------------------------------------------- B: the pour, close
CU_Z = B.CU_S / R.MUG_S         # the close-up's zoom: her mug at the Bass close-ups' scale
CAM_B = (R.Cam(184.0, 1202.0, CU_Z), R.Cam(178.0, 1212.0, CU_Z))


def cam_b(t):
    return R.cam_lerp(CAM_B[0], CAM_B[1], k(t, T_CU, T_WIDE - T_CU, "inout"))


# her fist round the kettle's grip bar, in kettle units (the bar runs along y = -118, x -14..26):
# a closed fist seen from the back of the hand, the bar through it, the fingers curled down
# its near face and tucked under it (their divisions only cut in at the knuckles and the
# tips), the thumb wrapped over the front, the back of the hand rising to the wrist
FIST = [(-11.0, -129.0), (-7.0, -133.5), (0.0, -135.5), (9.0, -136.0), (17.0, -135.0), (23.0, -132.0), (26.5, -126.0),
        (27.0, -114.0), (25.0, -107.0), (20.0, -103.5), (12.0, -102.5), (4.0, -102.5), (-3.0, -103.0), (-9.0, -105.5),
        (-12.5, -111.0), (-13.0, -122.0)]
HAND_BACK = [(-6.0, -132.0), (4.0, -141.0), (17.0, -148.0), (30.0, -152.5), (38.5, -151.0), (40.0, -144.0),
             (35.0, -136.0), (27.0, -129.0), (14.0, -128.0)]
THUMB = ((-5.0, -133.0), (-15.5, -124.5), 5.2, 4.4)
FINGER_X = (-1.5, 7.5, 16.0)                       # the divisions between the four fingers
WRIST = (37.0, -147.0)


def fist_polys():
    polys = [bass.orient(R._closed_spline(FIST, 5), True), bass.orient(R._closed_spline(HAND_BACK, 5), True)]
    a, b, ra, rb = THUMB
    polys.append(bass.orient(bass.capsule_pts(a, b, ra, rb, 6), True))
    cuts = []
    for x in FINGER_X:
        cuts.append([(x + 0.4, -102.8), (x, -110.0)])               # between the fingertips
        cuts.append([(x - 0.8, -135.6), (x - 0.5, -131.0)])         # between the knuckles
    cuts.append([(-3.0, -131.5), (-12.0, -124.0)])                  # the thumb off the hand
    return polys, cuts


def draw_cu_hand(c, grip, tilt, elbow):
    """Her fist on the grip and her forearm out to `elbow` (stage px), edged in the room's light."""
    m = kettle_matrix(grip, tilt)
    polys, cuts = fist_polys()
    wp = [[m.transform_point(*q) for q in poly] for poly in polys]
    wr = m.transform_point(*WRIST)
    arm = bass.orient(bass.capsule_pts(wr, elbow, 5.6, 7.6, 8), True)
    B.edged(c, [arm] + wp, INK, AMBER, 1.3)
    c.save()
    c.set_source_rgb(*AMBER)
    c.set_line_width(0.8)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for ln in cuts:
        c.new_path()
        bass.draw.poly(c, [m.transform_point(*q) for q in ln], close=False)
        c.stroke()
    c.restore()


def stream_pts(t, mouth, rim, d):
    """The water: from the spout's mouth along the spout, falling into the mug (a quadratic
    curve), wobbling a little on ones. Shown between `tail` and `head` (0..1)."""
    head = clamp((t - T_POUR + 0.1) / 0.1)
    tail = clamp((t - T_POUR_END) / 0.14)
    if head <= 0.0 or tail >= 1.0:
        return None
    ctrl = (mouth[0] + d[0] * 26.0, mouth[1] + d[1] * 26.0)
    end = (rim[0] + 3.0, rim[1] + 4.0)
    n = 18
    pts, ws = [], []
    for i in range(n + 1):
        u = lerp(tail, head, i / n)
        a, b2 = (1 - u) ** 2, u * u
        x = a * mouth[0] + 2 * (1 - u) * u * ctrl[0] + b2 * end[0]
        y = a * mouth[1] + 2 * (1 - u) * u * ctrl[1] + b2 * end[1]
        x += 0.5 * math.sin(t * 41.0 + u * 9.0) * u
        pts.append((x, y))
        ws.append(lerp(5.0, 3.6, u) * (0.6 + 0.4 * min(1.0, (u - tail) * 8.0)))
    return pts, ws


def mug_lift(t):
    """How far (stage px) her mug has been lifted off the stove at the end of the close-up."""
    return 34.0 * k(t, T_MUG_UP, T_WIDE - T_MUG_UP + 0.1, "in")


def draw_mug_grab(c, t, cam):
    """Her other hand comes in from the right, closes round the mug's handle (the Bass
    close-ups' fist, at their scale) and lifts it: drawn in frame px over the stage."""
    if t < T_GRAB:
        return
    hc = cam.to_frame((R.MUG_HC[0], R.MUG_HC[1] - mug_lift(t)))
    come = k(t, T_GRAB, T_GRIP - T_GRAB, "out3")
    off = (lerp(150.0, 0.0, come), lerp(560.0, 0.0, come))
    h = (hc[0] + off[0], hc[1] + off[1])
    polys, cuts, wr = B.cu_grip(h, 0.0)
    el = (wr[0] + 170.0, wr[1] + 620.0)        # her forearm rises from below the frame (as in the sip)
    B.edged(c, [B._capsule(wr, el, 40.0, 58.0)] + polys, INK, AMBER, 9.0)
    B.cut_lines(c, cuts)


def draw_b(c, t):
    cam = cam_b(t)
    room = room_at(t)
    if t >= T_GRIP:
        room = replace(room, mug=False)
    grip, tilt, in_hand = kettle_state(t)
    mug_rim = MUG_RIM

    def figures(c):
        # her forearm comes from up and to the right, toward her elbow; her fist stays on the
        # grip once the kettle is down (until the cut)
        elbow = (grip[0] + 108.0, grip[1] - 6.0)
        if not in_hand:
            draw_cu_hand(c, grip, tilt, elbow)
            return
        m = kettle_matrix(grip, tilt)
        R.draw_kettle(c, None, R.KETTLE_S, tilt, t, xf=m, fine=5.0)
        mouth = m.transform_point(*R.KETTLE_MOUTH)
        back = m.transform_point(R.KETTLE_MOUTH[0] + 10.0, R.KETTLE_MOUTH[1] - 6.0)
        d = (mouth[0] - back[0], mouth[1] - back[1])
        dl = math.hypot(*d) or 1.0
        d = (d[0] / dl, d[1] / dl)
        s = stream_pts(t, mouth, mug_rim, d)
        if s is not None:
            pts, ws = s
            bass.fill_polys(c, [bass.orient(bass.draw.ribbon(pts, ws), True)], INK)
        draw_cu_hand(c, grip, tilt, elbow)

    def overlay(c):
        lift = mug_lift(t)
        if t >= T_GRIP:
            R.draw_mug(c, (R.MUG_HC[0], R.MUG_HC[1] - lift), R.MUG_S, -1, t, edge=AMBER)
        # steam off the filling mug
        a = k(t, T_POUR + 0.2, 0.5) if t < T_POUR_END + 0.3 else 1.0
        B.steam(c, (mug_rim[0], mug_rim[1] - lift), twos(t), INK, alpha=0.85 * a, scale=R.MUG_S / 1.35)

    R.draw_stage(c, t, room, cam=cam, figures=figures, overlay=overlay)
    draw_mug_grab(c, t, cam)


# ---------------------------------------------------------------- C: to the window
CAM_C = (R.Cam(600.0, 1150.0, 0.98), R.Cam(652.0, 1142.0, 1.02))
WALK = (4.2, 6.5, 1.15)       # 137_26 source in (in stride), out (the clip's own stop), speed: stove to glass


@lru_cache(maxsize=1)
def walk_perf():
    C = mc.Clip.load("137_26")
    p = mc.Performance(fig(), [mc.Seg(C, WALK[0], WALK[1], at=T_WIDE, speed=WALK[2])], facing=1, x=0.0, near="Right")
    # where she ends: her pelvis at the glass
    end = p(T_WIDE + 3.0)[0]["pelvis"][0]
    return p, R.SPOT_WINDOW - end * R.FIG_S


@lru_cache(maxsize=1)
def footfalls():
    """Scene times her feet come down in the walk (for her steps)."""
    p, _ = walk_perf()
    out = []
    prev = {}
    for i in range(int(3.0 * 48) + 1):
        t = T_WIDE + i / 48.0
        st, _ = p(t)
        for side in ("near", "far"):
            y = st["feet"][side][1]
            up = y < -6.0
            if prev.get(side) and not up:
                out.append(round(t, 3))
            prev[side] = up
    return tuple(out)


def her_pose_c(t):
    p_, x0 = walk_perf()
    st, p = p_(twos(t))
    p.hold["near"] = B.mug_hold(t)
    # the mug at her chest, forearm level (as the Bass sip begins)
    p.arms["near"] = B._toward(p.arms["near"], 14.0 - p.lean, 84.0, 1.0)
    look = k(t, T_LOOK, 0.45, "inout")
    p.head = lerp(p.head, 21.0, look)
    p.lean = lerp(p.lean, -2.5, look)
    return st, p, x0


def draw_c(c, t):
    cam = R.cam_lerp(CAM_C[0], CAM_C[1], k(t, T_WIDE, T_SIP - T_WIDE, "inout"))
    room = room_at(t)
    st, p, x0 = her_pose_c(t)
    R.draw_stage(c, t, room, cam=cam, figures=lambda c: draw_her(c, st, p, x0, 1, R.room_bg(room)))


# ---------------------------------------------------------------- D: the sip
def draw_d(c, t):
    B.draw_sip_shot(c, SIP_TB + (t - T_SIP))


# ---------------------------------------------------------------- E: over her shoulder
CAM_E = (R.Cam(566.0, 920.0, 1.02), R.Cam(598.0, 872.0, 1.1))
FG_PAR = 1.35                 # her head is nearer than the window: it moves this much more
NAPE = (318.0, 1650.0)        # her nape, view px
BACK_S = 2.35


def cam_e(t):
    return R.cam_lerp(CAM_E[0], CAM_E[1], k(t, T_OTS, 14.0 - T_OTS, "inout"))


def couple(t):
    tb = t - QUARREL_TB
    return lambda c, r, tt: B.draw_room_small(c, tb)


def flinch(t):
    return sum(k(t, t0 + 0.08, 0.1, "out3") * (1.0 - k(t, t0 + 0.35, 0.5, "inout")) for t0 in T_BOLT)


def draw_e(c, t):
    cam = cam_e(t)
    room = R.Room(lit=True, kettle=True, steam=0.25, mug=False, film_t=S01_FILM + t)
    R.draw_window_view(c, t, room, cam=cam, far=couple(t), tb=t - QUARREL_TB)
    fg = R.Cam(cam.x, cam.y, 1.0 + (cam.z - 1.0) * FG_PAR, cam.rot)
    fl = flinch(t)
    base = fg.to_frame((NAPE[0], NAPE[1] - 8.0 * fl))
    s, turn = BACK_S * fg.z, -0.7 * fl
    marks = R.back_marks("her", base, s, t, turn)
    hw = B.HIS_WIN
    # her look: out from behind her head (from her eyes) to his window, landing on its sill
    # under the couple (so they stay clear)
    target = R.view_point(cam, (hw[0] + 44.0, hw[3] + 20.0), "far")
    K.sight_line(c, marks["eye"], target, t, T_SIGHT, PAPER, dur=0.45, march=34.0, r=9.0, gap=30.0, head=34.0, seed=21)
    # the shouting: red zigzags out of his window, at her (they hit her face, behind her head)
    mouth = R.view_point(cam, (hw[0] + 52.0, hw[1] + 62.0), "far")
    ear = marks["ears"][1]
    for j, t0 in enumerate(T_BOLT):
        if t >= t0:
            b = (ear[0] - 40.0 - 26.0 * j, ear[1] + 10.0 + 30.0 * j)
            B.bolt(c, mouth, b, t, t0, dur=0.3, width=16.0, seed=40 + j, amp=30.0, n=6)
    R.draw_back(c, "her", base, s, edge=AMBER, t=t, turn=turn)


# ---------------------------------------------------------------- the scene
def render(f, t, T):
    K.scene_setup(f)
    with f.screen() as c:
        if t < T_CU:
            draw_a(c, t)
        elif t < T_WIDE:
            draw_b(c, t)
        elif t < T_SIP:
            draw_c(c, t)
        elif t < T_OTS:
            draw_d(c, t)
        else:
            draw_e(c, t)


def motion_blur(t, T):
    return 1


def cues(T):
    out = [Cue(0.0, "the clock ticks on the beat (every 0.5 s), dry and close, under the scene", gain_db=-16,
               dur=T_OTS),
           Cue(0.0, "a tender celesta motif over pizzicato (the scene's music)", gain_db=-10, dur=T.duration),
           Cue(T_STEAM, "the kettle begins to sing, rising to a full whistle", gain_db=-10, dur=T_LIFT - T_STEAM),
           Cue(CLOCK_IN, "the lens opens on the clock: a soft glass tick", gain_db=-18),
           Cue(T_LIFT, "the kettle lifted off the flame: the whistle dies away", gain_db=-12),
           Cue(T_GAS, "the gas knob: a click, the flame's hiss gone", gain_db=-16),
           Cue(T_POUR, "pouring into the mug (the pitch rises as it fills)", gain_db=-8, dur=T_POUR_END - T_POUR),
           Cue(T_DOWN, "the kettle set down on the iron burner: a soft clunk", gain_db=-14)]
    out += [Cue(ft, "her step (stockinged, soft on the boards)", gain_db=-18) for ft in footfalls()]
    out += [Cue(T_SIP + 0.4, "the sip", gain_db=-12),
            Cue(T_SIGHT, "her look flies across the street: a soft rising whoosh", gain_db=-14),
            Cue(T_BOLT[0], "a muffled shout through the glass (his voice)", gain_db=-8),
            Cue(T_BOLT[1], "a second muffled shout", gain_db=-10)]
    return out
