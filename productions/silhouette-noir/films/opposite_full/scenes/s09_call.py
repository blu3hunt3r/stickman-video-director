"""s09 · CALL (104-116): his room; she finds the victim alive; the dial: 9-1-1; it rings.

Four shots (animator B; the room is his_room.py):

A  0.0-2.0   HIS ROOM, amber, wide. The chair on its back, the knife on the floor, the victim
             lying downstage in the lamp's pool with a small flat red pool by her. His door
             opens (T_DOOR..T_OPEN) on the lit landing: the light lays a wedge across the floor
             with the witness's long shadow in it, reaching for the outflung hand; the lamp
             sways in the draught. At T_SEE she freezes, her hand to her mouth, and her paper
             sight line goes down to the face. The frame creeps in.
B  2.0-5.0   THE HANDS, close and low on the floor, on her amber field. The victim's hand lies
             palm up, limp, a cut-paper hand seen from its little-finger side. Hers (rimmed in
             the landing's pale light) comes down from the top of the frame (T_REACH), stops
             just short, trembling (T_HOVER: the gap), and lays her fingertips in the palm
             (T_TOUCH). The victim's fingers twitch and hers flinch (T_TWITCH); then they curl
             up and close over hers (T_CLOSE..T_SHUT): alive. One faint paper ring from the
             wrist (T_PULSE).
C  5.0-10.0  THE DIAL, from straight above, filling the frame: his black telephone on the
             lamplit table, the empty cradle, the coiled cord. A paper finger wheel with ten
             holes over the hand-cut figures 1-0, the finger stop at four o'clock. Her finger
             dials 9-1-1 (DIGITS: in, round to the stop, out); a paper loop arrow follows each
             turn; the wheel runs back on its governor at ten pulses a second, and each pulse
             lands a paper dot in the tally arcing over the dial: nine, one, one. She takes her
             hand away (T_WITHDRAW); the tally holds.
D  10.0-12.0 THE RECEIVER at her ear, her profile close (the Bass close-up), her hand round the
             handle, her eyes down. Paper ripples ring out of the earpiece twice (T_RING); the
             ringing stops dead (T_CLICK: answered); she lifts her eyes to the window (T_LOOK)
             and the frame jumps in on her eye on the beat (T_JUMP).

Figures (and the dial under her finger) move on twos; the camera, the rings and the wheel's
run back move on ones.
"""
import math
from functools import lru_cache

import cairo

from engine import bass, mocap as mc, paperdoll as pd
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.opposite_bass import world as B
from films.opposite_full import his_room as HR
from films.opposite_full import kit as K

INK, PAPER, AMBER, RED = K.INK, K.PAPER, K.AMBER, B.RED
W, H = K.W, K.H
k = K.k
twos = K.twos

# ----------------------------------------------------------------------------- beats (scene s)
T_DOOR = 0.35              # the door starts to open (creak)
T_OPEN = 1.1               # ... open
T_SEE = 1.15               # she sees her: recoils and freezes; her look flies to the body
T_HANDS = 2.0              # cut: close on the hands
T_DIAL = 5.0               # cut: the dial, from above
T_EAR = 10.0               # cut: the receiver at her ear

# ============================================================================ A. the room
# The elevation of his room, wide: the door at the left, the phone table, the chair on its back,
# the counter's end; she lies downstage in the lamp's pool of light on the ink floor. The door
# opens on the lit landing: its light lays a wedge across the floor with the witness's long
# shadow in it, reaching for the outflung hand. She freezes; her look goes down to the face.
A_Z = (0.71, 0.75)                   # the creep in over the shot
A_ANCHOR = ((371.0, 1490.0), (540.0, 1150.0))   # stage point held at frame point while it creeps
DOOR_X = 0.5 * (HR.DOOR[0] + HR.DOOR[2])
WIT_X = DOOR_X + 6.0                 # the witness, standing in the doorway
LIGHT_SRC = (-521.0, 1160.0)         # the landing bulb's foot on the floor plane, behind the wall (stage px)
POOL_C = (560.0, HR.LIE_Y - 70.0)    # the lamp's pool of light on the floor (under the lamp)
POOL_R = (650.0, 262.0)
SHADOW_SY = 0.31                     # her shadow's foreshortening along the floor
SWAY = (2.2, 1.7)                    # the lamp swings in the draft: amplitude (deg), period (s)


def door_u(t):
    """The door swinging open (on twos: a cut-paper door turns in drawings)."""
    return 0.9 * k(twos(t), T_DOOR, T_OPEN - T_DOOR, "inout")


def a_cam(t):
    z = lerp(A_Z[0], A_Z[1], k(t, 0.0, T_HANDS, "inout"))
    (ax, ay), (fx, fy) = A_ANCHOR
    return z, ax - (fx - 540.0) / z, ay - (fy - 960.0) / z


def lamp_sway(t):
    """The draft from the door sets the lamp swinging, a little (deg)."""
    a, per = SWAY
    return a * k(t, T_OPEN - 0.3, 0.6, "inout") * math.sin(2.0 * math.pi * (t - T_OPEN + 0.3) / per)


@lru_cache(maxsize=1)
def _wit_perf():
    her = B.figs()[0]
    C = mc.Clip.load
    return mc.Performance(her, [
        mc.Seg(C("142_16"), 1.2, 1.9, at=0.0, speed=0.6, travel=0.0),
        mc.Seg(C("142_16"), 2.0, 2.45, at=T_SEE - 0.05, speed=1.4, travel=0.0, blend=0.12),     # she recoils
        mc.Seg(C("142_16"), 2.45, 2.5, at=T_SEE + 0.3, speed=0.05, travel=0.0, blend=0.2),     # ... frozen
    ], facing=1, near="Right")


def wit_pose(t):
    fig = B.figs()[0]
    st, p = _wit_perf()(twos(t))
    # her near hand flies to her mouth as she freezes (the elbow down at her chest)
    w = k(t, T_SEE + 0.12, 0.2, "out3")
    if w > 0.0:
        P = (st["pelvis"][0], st["pelvis"][1] + p.crouch)
        m = pd._rot((36.0, -32.0), -p.head)
        q = pd._rot((fig.neck[0] + m[0], fig.neck[1] + m[1]), p.lean)
        tgt = (P[0] + q[0] + 4.0, P[1] + q[1] + 30.0)
        sh = pd._rot(fig.shoulder, p.lean)
        S = (P[0] + sh[0], P[1] + sh[1])
        el, wr = pd.ik2(S, tgt, fig.upper, fig.fore, forward=1.0)
        a1 = math.degrees(math.atan2(el[0] - S[0], el[1] - S[1])) - p.lean
        a2 = math.degrees(math.atan2(wr[0] - el[0], wr[1] - el[1])) - p.lean - a1
        p.arms["near"] = B._toward(p.arms["near"], a1, a2, w)
    return st, p


def _ray_x(p, y):
    """Where the ray from the landing's light through stage point p reaches depth y."""
    sx, sy = LIGHT_SRC
    return sx + (p[0] - sx) * (y - sy) / (p[1] - sy)


def door_wedge(u, depth=1500.0):
    """The landing's light on the floor through the open door (stage px)."""
    x0, y0, x1, y1 = HR.DOOR
    wl = (x1 - x0) * math.cos(math.radians(84.0 * clamp(u / 0.9 * 0.9)))
    xl = x0 + wl
    y = y1 + depth
    return [(xl, y1), (x1, y1), (_ray_x((x1, y1), y), y), (_ray_x((xl, y1), y), y)]


def draw_shadow(c, t, u):
    """Her shadow, thrown by the landing's bulb along the floor toward us (stage px)."""
    fig = B.figs()[0]
    st, p = wit_pose(t)
    p.eye = 0.0
    x0, y0, x1, y1 = HR.DOOR
    wedge = door_wedge(u)
    c.save()
    c.new_path()
    bass.draw.poly(c, wedge)
    c.clip()
    # project: a point h up her figure lands along the floor, foreshortened, from her feet
    feet = (WIT_X, y1)
    dx = (feet[0] - LIGHT_SRC[0]) / (feet[1] - LIGHT_SRC[1])
    sy = SHADOW_SY
    c.translate(*feet)
    c.transform(cairo.Matrix(1.0, 0.0, -dx * sy, -sy, 0.0, 0.0))
    c.scale(HR.FS, HR.FS)
    B.draw_cutout(c, fig, st, p, INK, facing=1, gap=0.0, hide=("near", "far"))
    c.restore()


def draw_room(c, t):
    z, cx, cy = a_cam(t)
    u = door_u(t)
    look = {}
    sway = lamp_sway(t)
    lamp_dx = math.sin(math.radians(sway)) * (HR.LAMP[1] + 400.0)

    def beyond(cc, rect):
        st, p = wit_pose(t)
        fig = B.figs()[0]
        cc.save()
        B.place(cc, WIT_X, HR.FLOOR, HR.FS)
        # (her near arm takes an edge of the landing's light once it comes up across her chest)
        ol = HR.LANDING_LIT if t >= T_SEE + 0.12 else None
        B.draw_cutout(cc, fig, st, p, INK, facing=1, gap=8.0, edge=AMBER, outline=ol, ow=6.0)
        cc.restore()
        look["eye"] = HR.placed(HR.eye_point(fig, st, p, 1, 8.0), WIT_X)

    c.save()
    HR.stage_cam(c, z, cx, cy)
    B.fill(c, AMBER)
    # the lamp's cone on the wall, swinging with it
    lx, ly = HR.LAMP[0] + lamp_dx, HR.LAMP[1]
    bass.fill_polys(c, [bass.orient([(lx - 46.0, ly + 6.0), (lx + 46.0, ly + 6.0), (lx + 520.0, HR.FLOOR),
                                     (lx - 520.0, HR.FLOOR)], True)], PAPER, 0.085)
    HR.draw_set(c, door=u, beyond=beyond, chair_state="over", knife_on=False, door_lit=True, lamp=False)
    HR.draw_lamp(c, sway)
    HR.draw_floor(c)
    # the lamp's pool of light on the floor, round her
    px, py = POOL_C[0] + lamp_dx * 0.55, POOL_C[1]
    pool = bass.draw.ellipse_pts((px, py), POOL_R[0], POOL_R[1], n=96)
    bass.fill_polys(c, [HR.P(pool, seed=1903, amp=0.3, max_len=40.0)], AMBER)
    bass.fill_polys(c, [HR.P(pool, seed=1903, amp=0.3, max_len=40.0)], PAPER, 0.085)
    # the landing's light: under the door while it is shut (her feet break it), then out over
    # the floor through the open door, her shadow down the middle of it
    x0, y0, x1, y1 = HR.DOOR
    if u <= 0.0:
        bass.fill_polys(c, [HR.R(x0 + 4.0, y1 - 1.0, x1 - 4.0, y1 + 5.0, seed=1901)], HR.LANDING_LIT)
        for fx in (WIT_X - 26.0, WIT_X + 22.0):
            bass.fill_polys(c, [HR.R(fx - 18.0, y1 - 2.0, fx + 18.0, y1 + 6.0, seed=1902)], INK)
    else:
        bass.fill_polys(c, [bass.orient(door_wedge(u), True)], PAPER, 0.36)
        draw_shadow(c, t, u)
    HR.pool(c)
    HR.floor_knife(c)
    HR.draw_lying(c)
    c.restore()
    # her look: dots from her eye to the face on the floor
    if "eye" in look:
        def to_frame(p):
            return (540.0 + (p[0] - cx) * z, 960.0 + (p[1] - cy) * z)
        face = HR.lying_anchors()["face"]
        a, b = to_frame(look["eye"]), to_frame((face[0], face[1] - 26.0))
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        a = (a[0] + (b[0] - a[0]) / L * 16.0, a[1] + (b[1] - a[1]) / L * 16.0)   # clear of the eye itself
        K.sight_line(c, a, b, t, T_SEE + 0.15, PAPER, dur=0.35, r=6.0, gap=22.0, head=24.0, seed=9)


# ============================================================================ B. the hands
# Close on the floor, low, her close-up field of amber over the ink floor. The victim's hand
# lies palm up, limp, seen from its little-finger side, her forearm in from the right. Hers comes
# down from the top of the frame, stops just short (the gap), and lays her fingertips in the
# palm. The victim's fingers twitch (hers flinch), then curl up and close over hers: alive. One
# faint paper ring from the wrist. Each hand is a few smooth pieces of cut paper laid one on
# another with a fine edge: amber for the victim's, the landing's pale light for hers (she came
# in from the lit door). Hand units (HU, about a millimetre): the origin is the victim's wrist
# on the floor, her fingertips toward -x, up is -y.
T_REACH = 2.25             # her hand comes in
T_HOVER = 2.65             # ... stops short, just above (the gap), trembling
T_TOUCH = 3.15             # her fingertips in the palm
T_TWITCH = 3.45            # the victim's fingers twitch; hers flinch
T_CLOSE = 3.85             # ... and close on hers, slowly, the near finger first ...
V_LAG = {"little": 0.0, "ring": 0.05, "middle": 0.1, "index": 0.15}   # (each finger's start after T_CLOSE)
V_CLOSE = 0.7              # (each finger's close)
T_SHUT = T_CLOSE + V_LAG["index"] + V_CLOSE   # ... shut (4.70)
T_PULSE = 4.35             # one faint ring from the wrist
PULSE_DUR = 0.9
HOVER_GAP = 40.0           # HU up her arm from the touch, in the hover
B_O = (930.0, 1440.0)      # the victim's wrist on the floor, frame px
B_S = 4.4                  # frame px per HU
B_Z = (1.0, 1.06)          # the creep in, about the clasp
B_ZC = (560.0, 1180.0)
B_EDGE = 4.5               # the edge between laid pieces (frame px showing)


def _cr_open(pts, n=8):
    """Catmull-Rom through pts (open), n samples a span."""
    P_ = [(2 * pts[0][0] - pts[1][0], 2 * pts[0][1] - pts[1][1])] + list(pts) + \
         [(2 * pts[-1][0] - pts[-2][0], 2 * pts[-1][1] - pts[-2][1])]
    out = []
    for i in range(1, len(P_) - 2):
        out += _cr_span(P_[i - 1], P_[i], P_[i + 1], P_[i + 2], n)
    out.append(pts[-1])
    return out


def _cr_closed(pts, n=6):
    m = len(pts)
    out = []
    for i in range(m):
        out += _cr_span(pts[i - 1], pts[i], pts[(i + 1) % m], pts[(i + 2) % m], n)
    return out


def _cr_span(p0, p1, p2, p3, n):
    out = []
    for j in range(n):
        t = j / n
        t2, t3 = t * t, t * t * t
        out.append(tuple(0.5 * (2 * p1[q] + (-p0[q] + p2[q]) * t + (2 * p0[q] - 5 * p1[q] + 4 * p2[q] - p3[q]) * t2
                                + (-p0[q] + 3 * p1[q] - 3 * p2[q] + p3[q]) * t3) for q in range(2)))
    return out


def _chain(base, ang0, lens, flex):
    pts = [base]
    a = ang0
    for L, f in zip(lens, flex):
        a += f
        x, y = pts[-1]
        pts.append((x + L * math.cos(math.radians(a)), y + L * math.sin(math.radians(a))))
    return pts


def finger(joints, widths, n=7, knuck=0.08, pad=0.06, tip=1.2, back=8.0, back_dir=None, palm_skip=0.0):
    """A finger (or thumb) as one smooth piece through its joints [base, ..., tip centre] with
    a width at each. The palmar side is +n (n = the direction turned +90 deg on screen): the pads
    swell it between the joints and crease it at them; the knuckles bump the dorsal side; the
    tip is a long round pad. The base runs `back` HU into the palm (straight back, or along
    `back_dir` deg, so a bent knuckle rounds off inside the palm). Returns (outline, the
    outline without its base: the edge that shows where it is laid over something; palm_skip
    leaves that share of the palmar side out of it too, from the base)."""
    J = list(joints)
    if back_dir is None:
        d0 = (J[1][0] - J[0][0], J[1][1] - J[0][1])
        L0 = math.hypot(*d0) or 1.0
        J.insert(0, (J[0][0] - d0[0] / L0 * back, J[0][1] - d0[1] / L0 * back))
    else:
        J.insert(0, (J[0][0] + back * math.cos(math.radians(back_dir)), J[0][1] + back * math.sin(math.radians(back_dir))))
    widths = (widths[0],) + tuple(widths)
    C = _cr_open(J, n)
    s_ = [0.0]
    for i in range(1, len(C)):
        s_.append(s_[-1] + math.dist(C[i - 1], C[i]))
    js = [0.0]
    for i in range(1, len(J)):
        js.append(js[-1] + math.dist(J[i - 1], J[i]))
    js = [v * s_[-1] / js[-1] for v in js]

    def width_at(v):
        for i in range(len(js) - 1):
            if v <= js[i + 1] or i == len(js) - 2:
                return lerp(widths[i], widths[i + 1], clamp((v - js[i]) / max(js[i + 1] - js[i], 1e-6)))

    def bump(v, cs, sig):
        return sum(math.exp(-((v - c0) / sig) ** 2) for c0 in cs)

    inner = js[1:-1]
    mids = [0.5 * (js[i] + js[i + 1]) for i in range(1, len(js) - 1)]
    sg = 0.11 * s_[-1]
    side_p, side_d = [], []
    for i, c0 in enumerate(C):
        a_, b_ = C[min(i + 1, len(C) - 1)], C[max(i - 1, 0)]
        dx, dy = a_[0] - b_[0], a_[1] - b_[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        w = width_at(s_[i]) / 2.0
        wd = w * (1.0 + knuck * bump(s_[i], inner, sg * 0.7))
        wp = w * (1.0 + pad * bump(s_[i], mids, sg) - pad * 0.8 * bump(s_[i], inner, sg * 0.5))
        side_p.append((c0[0] + nx * wp, c0[1] + ny * wp))
        side_d.append((c0[0] - nx * wd, c0[1] - ny * wd))
    e = C[-1]
    dx, dy = C[-1][0] - C[-3][0], C[-1][1] - C[-3][1]
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    r = widths[-1] / 2.0
    cap = []
    for j in range(1, 14):
        th = math.pi * j / 14.0
        rr = r * (1.0 + 0.08 * math.sin(th))
        cap.append((e[0] + nx * rr * math.cos(th) + ux * rr * tip * math.sin(th),
                    e[1] + ny * rr * math.cos(th) + uy * rr * tip * math.sin(th)))
    k0 = max(1, int(n * 0.9))
    kp = k0 + int(palm_skip * (len(side_p) - k0))
    return side_p + cap + list(reversed(side_d)), side_p[kp:] + cap + list(reversed(side_d))[:-k0]


def _cut(pts, seed, max_len=10.0):
    return bass.orient(bass.scissor(pts, seed=seed, sag=0.3, amp=0.22, max_len=max_len, corner=40.0), True)


def _mix(a, b, u):
    return tuple(lerp(x, y, u) for x, y in zip(a, b))


def _add(a, b, u=1.0):
    return tuple(x + y * u for x, y in zip(a, b))


# --- the victim's hand: palm up, seen from its little-finger side and a touch from above, so
# the far fingers sit a little higher. A finger: its knuckle, its direction open and shut (deg;
# 180 points to the fingertips' side), phalanx lengths, widths at the joints and the tip.
V_FINGERS = {
    "index": ((-101.0, -36.0), 192.0, 184.0, (40.0, 24.0, 19.0), (16.0, 14.5, 13.0, 11.0)),
    "middle": ((-104.0, -27.0), 184.0, 182.0, (44.0, 27.0, 20.0), (16.5, 15.0, 13.5, 11.5)),
    "ring": ((-99.0, -18.0), 176.0, 180.0, (41.0, 26.0, 19.0), (15.5, 14.0, 12.5, 10.5)),
    "little": ((-90.0, -10.0), 168.0, 178.0, (33.0, 19.0, 17.0), (13.5, 12.0, 10.5, 9.0)),
}
V_ORDER = ("index", "middle", "ring", "little")             # far to near
V_REST = {"index": (6.0, 10.0, 5.0), "middle": (8.0, 12.0, 6.0), "ring": (10.0, 15.0, 7.0),
          "little": (13.0, 18.0, 9.0)}
V_TWITCH = {"index": (10.0, 12.0, 5.0), "middle": (8.0, 10.0, 5.0), "ring": (4.0, 6.0, 3.0),
            "little": (2.0, 3.0, 1.0)}
V_SHUT = {"index": (75.0, 65.0, 25.0), "middle": (72.0, 70.0, 30.0), "ring": (70.0, 78.0, 34.0),
          "little": (56.0, 66.0, 36.0)}        # each curl nests on the next: no gaps for the far ones to show in
V_THUMB = ((-4.0, -38.0), 197.0, (34.0, 27.0, 21.0), (26.0, 19.0, 16.0, 13.0))
V_THUMB_REST, V_THUMB_SHUT = (0.0, 4.0, 6.0), (-8.0, 7.0, 10.0)
V_PALM = [(10.0, 0.0), (-20.0, 0.0), (-55.0, 0.0), (-80.0, -1.0), (-93.0, -5.0), (-102.0, -13.0), (-107.0, -23.0),
          (-107.0, -33.0), (-101.0, -40.0), (-86.0, -42.0), (-66.0, -42.0), (-46.0, -43.0), (-26.0, -46.0),
          (-8.0, -48.0), (0.0, -46.5), (6.0, -42.0), (8.0, -20.0)]     # its heel tucks in under the wrist's edge
V_FORE = [(2.0, 1.0), (2.0, -46.0), (22.0, -46.5), (60.0, -48.0), (150.0, -54.0), (300.0, -62.0), (520.0, -68.0),
          (520.0, 1.0)]
V_WRIST = (14.0, -24.0)    # where the pulse rings from

# --- her hand: palm down, from its little-finger side. Local units: origin her wrist, +x along
# the hand to the knuckles, +y her palm side; placed by her wrist and the hand's angle below the
# horizontal. Her forearm comes down to the wrist from the top of the frame.
W_FINGERS = {
    "index": ((93.0, -8.0), -1.0, (37.0, 22.5, 17.5), (15.0, 13.5, 12.0, 10.0)),
    "middle": ((96.0, -2.5), 0.5, (41.0, 25.0, 18.5), (15.5, 14.0, 12.5, 10.5)),
    "ring": ((93.0, 3.0), 2.0, (38.0, 22.5, 17.5), (14.5, 13.0, 11.5, 9.5)),
    "little": ((86.0, 8.0), 4.0, (30.0, 18.0, 15.5), (13.0, 12.0, 10.5, 9.0)),
}
W_ORDER = ("index", "middle", "ring", "little")             # far to near
W_REACH = {"index": (14.0, 20.0, 10.0), "middle": (12.0, 18.0, 9.0), "ring": (15.0, 21.0, 10.0),
           "little": (19.0, 24.0, 12.0)}
W_LAID = {"index": (4.0, 9.0, 5.0), "middle": (5.0, 10.0, 6.0), "ring": (8.0, 12.0, 7.0),
          "little": (12.0, 15.0, 8.0)}
W_FLINCH = (-6.0, -8.0, -4.0)        # added at the flinch: the fingers spring open a little
W_PRESS = (4.0, 6.0, 3.0)            # added in the clasp: she holds on
W_THUMB = ((36.0, 8.0), 12.0, (28.0, 24.0, 19.0), (21.0, 17.5, 15.0, 12.5))
W_THUMB_FLEX = (-3.0, 6.0, 5.0)
W_ANG = 38.0                   # her hand, deg below the horizontal, laid
W_FORE = 74.0                  # her forearm, deg below the horizontal (up-left from the wrist)
W_TOUCH = (-60.0, -43.0)       # where her middle fingertip comes to rest, in the palm
W_ARM = ((40.0, 17.5), (80.0, 19.0), (150.0, 22.0), (300.0, 26.0), (700.0, 32.0))   # (s up the arm, half-width)
W_HAND_RIM = [(14.0, -17.0), (40.0, -19.0), (62.0, -19.2), (82.0, -17.5), (94.0, -12.0), (99.0, -4.0), (99.0, 5.0),
              (93.0, 12.0), (70.0, 15.5), (45.0, 18.5), (24.0, 21.0), (8.0, 21.5)]   # the hand's part of the arm's outline


def _place(wrist, ang):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return lambda pts: [(wrist[0] + x * ca - y * sa, wrist[1] + x * sa + y * ca) for x, y in pts]


@lru_cache(maxsize=1)
def _w_wrist():
    """Her wrist (HU) when her middle fingertip rests on W_TOUCH, laid."""
    b_, a0, lens, wid = W_FINGERS["middle"]
    J = _chain(b_, a0, lens, W_LAID["middle"])
    d = math.radians(a0 + sum(W_LAID["middle"]))
    pad = (J[-1][0] + wid[-1] * 0.5 * (-math.sin(d)) + wid[-1] * 0.4 * math.cos(d),
           J[-1][1] + wid[-1] * 0.5 * math.cos(d) + wid[-1] * 0.4 * math.sin(d))
    px, py = _place((0.0, 0.0), W_ANG)([pad])[0]
    return (W_TOUCH[0] - px, W_TOUCH[1] - py)


def victim_flex(t):
    """{finger: flexion}, thumb flexion, {finger: shut (0..1)}: the victim's hand at scene time t
    (on twos). The fingers close one after another, near to far (overlapping: a weak grip)."""
    tt = twos(t)
    tw = k(tt, T_TWITCH, 0.06, "out") * (1.0 - k(tt, T_TWITCH + 0.1, 0.16, "inout"))
    out, sh = {}, {}
    for name in V_FINGERS:
        sh[name] = k(tt, T_CLOSE + V_LAG[name], V_CLOSE, "inout")
        out[name] = _add(_mix(V_REST[name], V_SHUT[name], sh[name]), V_TWITCH[name], tw)
    return out, _mix(V_THUMB_REST, V_THUMB_SHUT, k(tt, T_CLOSE + 0.1, T_SHUT - T_CLOSE - 0.1, "inout")), sh


def witness_place(t):
    """Her wrist (HU), hand angle (deg), finger blend reach->laid (0..1), flinch (0..1), press (0..1)."""
    tt = twos(t)
    a = k(tt, T_REACH, T_HOVER - T_REACH, "out3")
    b = k(tt, T_TOUCH - 0.2, 0.2, "inout")
    fa = math.radians(180.0 + W_FORE)
    ux, uy = math.cos(fa), math.sin(fa)                # up her forearm
    back = lerp(lerp(620.0, HOVER_GAP, a), 0.0, b)     # slid back up her arm, off frame
    ang = W_ANG + lerp(lerp(-10.0, -6.0, a), 0.0, b)
    fl = k(tt, T_TWITCH + 0.04, 0.06, "out") * (1.0 - k(tt, T_TWITCH + 0.14, 0.3, "inout"))
    ww = _w_wrist()
    wx, wy = ww[0] + ux * back, ww[1] + uy * back - 7.0 * fl
    ang -= 4.0 * fl
    if 0.0 < a and b < 1.0:                            # a tremble in the hover
        wy += 1.4 * math.sin(tt * 41.0) * (1.0 - b)
        ang += 0.8 * math.sin(tt * 31.0 + 1.3) * (1.0 - b)
    press = k(tt, T_CLOSE + 0.35, 0.4, "inout")
    return (wx, wy), ang, b, fl, press


def victim_hand(t):
    """[(kind, poly, open edge)] of the victim's hand, back to front, in HU, split where hers
    goes in between: (behind, in front)."""
    fl, th, shut = victim_flex(t)
    b_, a0, lens, wid = V_THUMB
    poly, op = finger(_chain(b_, a0, lens, th), wid, knuck=-0.04, pad=0.03, back=16.0)
    behind = [("fill", _cut(poly, 2204), None),
              ("fill", _cut(V_FORE, 2211, 30.0), None), ("fill", _cut(_cr_closed(V_PALM, 6), 2210, 14.0), None)]
    front = []
    for i, name in enumerate(V_ORDER):
        b_, d0, d1, lens, wid = V_FINGERS[name]
        sh = shut[name]
        a1 = lerp(d0, d1, sh) + fl[name][0]          # the first phalanx's heading
        # its base runs back into the palm halfway between straight back and along the palm, so
        # a curled knuckle rounds off inside the palm (no fold on the inside of the bend); curled,
        # the far fingers' palm sides sink out of sight behind the near ones: their edge there
        # goes (so no slivers of line inside the grip)
        poly, op = finger(_chain(b_, lerp(d0, d1, sh), lens, fl[name]), wid, tip=1.35, back=12.0,
                          back_dir=0.5 * (a1 - 180.0), palm_skip=(0.0 if name == "little" else 0.5 * sh))
        front.append(("seam", _cut(poly, 2200 + i), op))
    return behind, front


def witness_hand(t):
    (wx, wy), ang, laid, fl, press = witness_place(t)
    X = _place((wx, wy), ang)
    fa = math.radians(180.0 + W_FORE)
    ux, uy = math.cos(fa), math.sin(fa)
    nx, ny = -uy, ux
    dors = [(wx + ux * s + nx * w, wy + uy * s + ny * w) for s, w in reversed(W_ARM)]
    palm = [(wx + ux * s - nx * w, wy + uy * s - ny * w) for s, w in W_ARM]
    arm = _cr_closed(dors + X(W_HAND_RIM) + palm, 5)
    b_, a0, lens, wid = W_THUMB
    tpoly, _ = finger(_chain(b_, a0, lens, W_THUMB_FLEX), wid, knuck=-0.04, pad=0.03, back=14.0)
    out = [("edge", [_cut(X(tpoly), 2304), _cut(arm, 2310, 14.0)], None)]
    for i, name in enumerate(W_ORDER):
        b_, a0, lens, wid = W_FINGERS[name]
        f = _add(_add(_mix(W_REACH[name], W_LAID[name], laid), W_FLINCH, fl), W_PRESS, press)
        poly, op = finger(_chain(b_, a0, lens, f), wid, tip=1.35, back=10.0)
        out.append(("seam", _cut(X(poly), 2300 + i), X(op)))
    return out


def _lay(c, pieces, F, edge):
    """Lay pieces on in order: 'fill' plain; 'edge' over a full edge; 'seam' over an edge along
    the open outline only (so its base runs on into the palm with no line)."""
    for kind, poly, op in pieces:
        polys = poly if (poly and not isinstance(poly[0][0], float)) else [poly]
        fp = [F(q) for q in polys]
        if kind == "fill":
            bass.fill_polys(c, fp, INK)
        elif kind == "edge":
            B.edged(c, fp, INK, edge, 2.0 * B_EDGE)
        else:
            c.save()
            c.new_path()
            bass.draw.poly(c, F(op), close=False)
            c.set_source_rgb(*edge)
            c.set_line_width(2.0 * B_EDGE)
            c.set_line_join(cairo.LINE_JOIN_ROUND)
            c.set_line_cap(cairo.LINE_CAP_ROUND)
            c.stroke()
            c.restore()
            bass.fill_polys(c, fp, INK)


def b_frame(z):
    """HU -> frame px through the creep (zoom z about B_ZC)."""
    ox, oy = B_O
    zx, zy = B_ZC
    return lambda pts: [(zx + (ox + x * B_S - zx) * z, zy + (oy + y * B_S - zy) * z) for x, y in pts]


def draw_hands(c, t):
    z = lerp(B_Z[0], B_Z[1], k(t, T_HANDS, T_DIAL - T_HANDS, "inout"))
    F = b_frame(z)
    B.fill(c, AMBER)
    fy = F([(0.0, -1.5)])[0][1]           # the floor's edge: the back of her hand and her arm sink into it
    bass.fill_polys(c, [bass.cut_rect(-60.0, fy, W + 60.0, H + 60.0, seed=2101, amp=1.0)], INK)
    behind, front = victim_hand(t)
    _lay(c, behind, F, AMBER)
    if t >= T_REACH:
        _lay(c, witness_hand(t), F, HR.LANDING_LIT)
    _lay(c, front, F, AMBER)
    # alive: one faint ring of paper from her wrist
    wr = F([V_WRIST])[0]
    a = (t - T_PULSE) / PULSE_DUR
    if 0.0 <= a < 1.0:
        r = lerp(30.0, 520.0, ease("out3", a))
        bass.ring(c, wr, r, 10.0 * (1.0 - a) + 1.0, PAPER, seed=2102, n=120, alpha=0.6 * (1.0 - 0.6 * a))


# ============================================================================ C. the dial
# From straight above, the dial fills the frame: his black telephone on the lamplit table, the
# empty cradle at the top (the receiver is at her ear), its cord running off. A paper finger
# wheel with ten holes; through them the hand-cut figures 1-0 show on the black plate beneath,
# and slide out of sight as the wheel turns. The finger stop at four o'clock. Her finger (rimmed
# in the landing's light, as in the hands) dials 9-1-1: in, round to the stop, out. A paper loop
# arrow follows each turn. The wheel runs back on its governor at ten pulses a second, and each
# pulse lands a paper dot in the tally that arcs over the dial: nine, one, one.
D_C = (540.0, 1030.0)      # the dial's centre, frame px
D_RW = 430.0               # the finger wheel
D_RH = 312.0               # the circle of the holes
D_RHOLE = 72.0             # a hole
D_RC = 150.0               # the hub; the centre card inside it
D_STOP = 30.0              # where a hole stops (screen deg: 0 = three o'clock, clockwise)
D_RATE = 300.0             # the run back, deg/s: ten pulses a second, 30 deg a pulse
D_Z = (1.0, 1.07)          # the creep in over the shot
D_MM = 8.0                 # frame px per mm of her hand
D_ARM = (1500.0, 2500.0)   # her elbow, below the frame: her hand points back at it
D_TALLY_R = 548.0          # the tally's arc
D_ARROW_R = 486.0          # the loop arrow's arc
DIGITS = (                 # (digit, finger in from, wind from, at the stop, let go)
    ("9", 5.1, 5.4, 6.12, 6.2),
    ("1", 7.22, 7.42, 7.66, 7.72),
    ("1", 7.96, 8.12, 8.36, 8.42),
)
T_WITHDRAW = 8.5           # her hand goes


def hole_ang(d):
    """The rest angle of digit d's hole (screen deg)."""
    return -30.0 * (10 if d == "0" else int(d))


def wind_of(d):
    return D_STOP - hole_ang(d)


def wheel_phi(t):
    """The finger wheel's turn (deg, clockwise) at scene time t: wound on twos with her
    finger, run back on ones by the governor."""
    for d, t_in, t0, t1, t_rel in DIGITS:
        Wd = wind_of(d)
        if t < t0:
            return 0.0
        if t < t1:
            return Wd * ease("inout", clamp((twos(t) - t0) / (t1 - t0)))
        if t < t_rel:
            return Wd
        back = Wd - D_RATE * (t - t_rel)
        if back > 0.0:
            return back
    return 0.0


def pulse_times():
    """Every dial pulse (scene s): digit n gives n pulses as the wheel runs back."""
    out = []
    for d, t_in, t0, t1, t_rel in DIGITS:
        n = 10 if d == "0" else int(d)
        out.append([t_rel + (15.0 + 30.0 * i) / D_RATE for i in range(n)])
    return out


def _hole_xy(ang, r=D_RH):
    return (D_C[0] + r * math.cos(math.radians(ang)), D_C[1] + r * math.sin(math.radians(ang)))


def finger_at(t):
    """Her fingertip (frame px, before the creep) and how far it is lifted (0 in the hole, 1 up)."""
    tt = twos(t)
    off = (D_C[0] + 120.0, H + 260.0)
    prev, lift_prev = off, 1.0
    for j, (d, t_in, t0, t1, t_rel) in enumerate(DIGITS):
        home = _hole_xy(hole_ang(d))
        if tt < t_in:
            return prev, 1.0
        if tt < t0:
            u = k(tt, t_in, t0 - t_in, "inout")
            p = (lerp(prev[0], home[0], u), lerp(prev[1], home[1], u) - 26.0 * math.sin(math.pi * u))
            return p, 1.0 - k(tt, t0 - 0.12, 0.12, "in")
        if tt < t_rel:
            p = _hole_xy(hole_ang(d) + wheel_phi(t))
            return (p[0] + 1.6 * math.sin(tt * 47.0), p[1] + 1.6 * math.cos(tt * 39.0)), 0.0
        at_stop = _hole_xy(D_STOP)
        out = (at_stop[0] + 30.0, at_stop[1] + 46.0)          # lifted out, drawn back a little
        u = k(tt, t_rel, 0.12, "out")
        prev = (lerp(at_stop[0], out[0], u), lerp(at_stop[1], out[1], u))
        if j + 1 < len(DIGITS) and tt < DIGITS[j + 1][1]:
            # she hovers toward the next hole while the wheel runs back under her
            nxt = _hole_xy(hole_ang(DIGITS[j + 1][0]))
            hov = (nxt[0] + 34.0, nxt[1] + 40.0)
            v = k(tt, t_rel + 0.12, DIGITS[j + 1][1] - t_rel - 0.12, "inout")
            return (lerp(prev[0], hov[0], v), lerp(prev[1], hov[1], v)), u
        if j + 1 < len(DIGITS):
            nxt = _hole_xy(hole_ang(DIGITS[j + 1][0]))
            prev = (nxt[0] + 34.0, nxt[1] + 40.0)
            continue
        v = k(tt, T_WITHDRAW, 0.5, "in")
        return (lerp(prev[0], off[0], v), lerp(prev[1], off[1], v)), u
    return off, 1.0


# her hand from above, palm down, the index finger out (mm: origin the fingertip's tip centre,
# the finger pointing -y, the hand toward +y; a right hand, so the thumb is on the left)
D_INDEX = ([(0.0, 78.0), (0.0, 35.0), (0.0, 13.0), (0.0, 5.0)], (15.5, 14.5, 13.5, 12.5))
D_FIST = [(-27.0, 440.0), (-23.0, 300.0), (-21.0, 236.0), (-25.0, 192.0), (-30.0, 150.0), (-28.0, 118.0),
          (-17.0, 96.0), (-8.0, 84.0), (8.0, 74.0), (13.0, 66.0), (21.0, 61.0), (29.0, 62.0), (35.0, 66.0),
          (41.0, 64.0), (48.0, 67.0), (52.0, 73.0), (57.0, 75.0), (62.0, 81.0), (64.0, 92.0), (64.0, 116.0),
          (60.0, 156.0), (55.0, 204.0), (53.0, 250.0), (57.0, 320.0), (62.0, 440.0)]


@lru_cache(maxsize=1)
def _dial_hand_local():
    fist = _cr_closed(D_FIST, 5)
    ix, op = finger(*D_INDEX, knuck=0.04, pad=0.03, tip=1.25, back=16.0)
    return (_cut(fist, 2501, 14.0), _cut(ix, 2503, 10.0), op)


def draw_dial_hand(c, t):
    p, lift = finger_at(t)
    if p[1] > H + 200.0:
        return
    fist, ix, op = _dial_hand_local()
    dx, dy = D_ARM[0] - p[0], D_ARM[1] - p[1]
    rot = math.atan2(dy, dx) - math.pi / 2.0                # local +y points at her elbow
    s = D_MM * (1.0 + 0.05 * lift)                           # lifted: a touch nearer the lens
    c.save()
    c.translate(*p)
    c.rotate(rot)
    c.scale(s, s)
    ew = 2.0 * B_EDGE / s
    B.edged(c, [fist], INK, HR.LANDING_LIT, ew)
    c.new_path()
    bass.draw.poly(c, op, close=False)
    c.set_source_rgb(*HR.LANDING_LIT)
    c.set_line_width(ew)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.stroke()
    bass.fill_polys(c, [ix], INK)
    c.restore()


@lru_cache(maxsize=1)
def _phone_top():
    """The telephone from above: the body (its front edge below the dial, the cradle at the top
    with the plungers up), and the receiver's cord running off at the top left."""
    cx = D_C[0]
    top, front = 300.0, D_C[1] + D_RW + 118.0
    body = [(-200.0, front - 40.0), (-200.0, top + 60.0), (cx - 470.0, top - 10.0), (cx - 380.0, top - 70.0),
            (cx - 290.0, top - 92.0), (cx - 210.0, top - 70.0), (cx - 160.0, top - 6.0), (cx - 60.0, top + 18.0),
            (cx + 60.0, top + 18.0), (cx + 160.0, top - 6.0), (cx + 210.0, top - 70.0), (cx + 290.0, top - 92.0),
            (cx + 380.0, top - 70.0), (cx + 470.0, top - 10.0), (W + 200.0, top + 60.0), (W + 200.0, front - 40.0),
            (cx + 420.0, front - 6.0), (cx, front + 10.0), (cx - 420.0, front - 6.0)]
    plungers = [bass.cut_rect(cx - 120.0, top - 34.0, cx - 60.0, top + 4.0, seed=2611, amp=0.8),
                bass.cut_rect(cx + 60.0, top - 34.0, cx + 120.0, top + 4.0, seed=2612, amp=0.8)]
    # the cord: a coil seen from above, loop after loop, from the body's back corner off the top
    a, b = (cx - 340.0, top - 50.0), (-60.0, -90.0)
    L = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    path = []
    for i in range(361):
        u = i / 360.0
        th = 2.0 * math.pi * 14.0 * u
        bow = 60.0 * math.sin(math.pi * u)
        r = 17.0
        x = a[0] + ux * L * u + uy * bow + ux * r * 0.55 * math.cos(th) - uy * r * math.sin(th)
        y = a[1] + uy * L * u - ux * bow + uy * r * 0.55 * math.cos(th) + ux * r * math.sin(th)
        path.append((x, y))
    return _cut(_cr_closed(body, 4), 2610, 30.0), plungers, path


@lru_cache(maxsize=1)
def _stop_poly():
    """The finger stop: a slim hook from the bezel over the wheel's rim, its end on the holes'
    circle just where a finger in a hole at D_STOP meets it."""
    tip = D_STOP + math.degrees(D_RHOLE / D_RH) + 1.0
    spine = [_hole_xy(tip, D_RH - 18.0), _hole_xy(tip - 0.5, D_RH + 40.0), _hole_xy(tip - 2.5, D_RW - 20.0),
             _hole_xy(tip - 6.5, D_RW + 30.0)]
    side_a, side_b = [], []
    for i, (x, y) in enumerate(spine):
        j0, j1 = max(0, i - 1), min(len(spine) - 1, i + 1)
        dx, dy = spine[j1][0] - spine[j0][0], spine[j1][1] - spine[j0][1]
        L = math.hypot(dx, dy) or 1.0
        w = lerp(11.0, 15.0, i / (len(spine) - 1))
        side_a.append((x - dy / L * w, y + dx / L * w))
        side_b.append((x + dy / L * w, y - dx / L * w))
    return _cut(_cr_closed(side_a + side_b[::-1], 5), 2660, 8.0)


def draw_dial(c, t):
    B.fill(c, AMBER)
    body, plungers, cord = _phone_top()
    c.save()
    c.new_path()
    bass.draw.poly(c, cord, close=False)
    c.set_source_rgb(*INK)
    c.set_line_width(7.0)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.stroke()
    c.restore()
    bass.fill_polys(c, [body], INK)
    bass.fill_polys(c, plungers, PAPER)
    # the bezel catches the lamp: an amber sliver round the upper left
    bass.fill_polys(c, [bass.loop_pts(D_C, D_RW + 16.0, 7.0, 1.0, 196.0, 96.0, 0.01, seed=2620)], AMBER)
    # the figures, on the plate beneath the wheel
    for i in range(10):
        d = "0" if i == 9 else str(i + 1)
        K.numeral(c, d, _hole_xy(hole_ang(d)), 64.0, PAPER, seed=2630 + i)
    # the finger wheel: a paper disc with ten holes and the hub cut out of it
    phi = wheel_phi(t)
    holes = [bass.orient(bass.ring_pts(_hole_xy(-30.0 * (i + 1) + phi), D_RHOLE, seed=2640 + i, n=40, amp=0.5),
                         False) for i in range(10)]
    wheel = bass.orient(bass.ring_pts(D_C, D_RW, seed=2650, n=96, amp=0.8, phase=phi), True)
    hub = bass.orient(bass.ring_pts(D_C, D_RC, seed=2651, n=56, amp=0.5, phase=phi), False)
    bass.fill_polys(c, [wheel, hub] + holes, PAPER)
    bass.disc(c, D_C, D_RC - 22.0, PAPER, seed=2652, n=56)
    # the finger stop: a hook from the bezel over the wheel's rim, its end on the holes' circle
    bass.fill_polys(c, [_stop_poly()], INK)
    # the loop arrow: drawn on round the outside with each turn, gone soon after she lets go
    for d, t_in, t0, t1, t_rel in DIGITS:
        if t0 <= t < t_rel + 0.3:
            u = clamp(wheel_phi(t) / wind_of(d)) if t < t_rel else 1.0
            al = 1.0 - k(t, t_rel + 0.08, 0.22, "in")
            bass.fill_polys(c, [bass.loop_pts(D_C, D_ARROW_R, 18.0, u, hole_ang(d), wind_of(d) - 4.0, 2.2,
                                              seed=2670)], PAPER, al)
    # the tally: a paper dot for each pulse, in an arc over the dial
    draw_tally(c, t)
    draw_dial_hand(c, t)


def tally_slots():
    """Arc angles (deg) of the tally's dots: one group a digit."""
    out = []
    a = 0.0
    for j, ts in enumerate(pulse_times()):
        if j:
            a += 10.5
        for i in range(len(ts)):
            out.append((a, ts[i]))
            a += 4.6
    a -= 4.6
    return [(270.0 - a / 2.0 + s, ti) for s, ti in out]


def draw_tally(c, t):
    for i, (ang, ti) in enumerate(tally_slots()):
        if t >= ti:
            g = ease("outback", clamp((t - ti) / 0.12))
            K.dot(c, _hole_xy(ang, D_TALLY_R), 13.0 * g, PAPER, seed=2680 + i)


def draw_dial_shot(c, t):
    z = lerp(D_Z[0], D_Z[1], k(t, T_DIAL, T_EAR - T_DIAL, "inout"))
    c.save()
    c.translate(*D_C)
    c.scale(z, z)
    c.translate(-D_C[0], -D_C[1])
    draw_dial(c, t)
    c.restore()


# ============================================================================ D. the receiver
# Her profile close on her amber field (the Bass close-up: B.PROFILE, the bob, the eye), his
# receiver at her ear, her hand round its handle, the cord hanging; her eyes still down on the
# floor. Paper ripples ring out of the earpiece twice (the ringback). The ringing stops (a click:
# someone answers) and she lifts her eyes to the window; the frame jumps in on her eye on the beat.
T_RING = (10.12, 10.78)    # the ringback, twice
T_CLICK = 11.35            # the ringing stops: answered
T_LOOK = 11.4              # she lifts her eyes to the window
T_JUMP = 11.5              # the frame jumps in on her eye (on the beat)
E_EAR = (497.0, 770.0)     # the earpiece's middle, at her ear (B's close-up frame)
E_ANG = 40.0               # the handle, deg below the horizontal: the mouthpiece out before her lips
E_S = 3.4                  # handset units -> px
E_ELBOW = (575.0, 1665.0)  # her elbow, tucked in low before her chest
E_SHOULDER = (405.0, 1440.0)   # in her, at the foot of her neck (the upper arm comes at us: short)
E_FORE_HW = ((0.0, 52.0), (0.35, 58.0), (0.8, 67.0), (1.0, 64.0))   # (share from the wrist, half-width px)
E_UPPER_HW = ((0.0, 64.0), (0.5, 72.0), (1.0, 72.0))
E_RIM = (0.0, 0.8)         # how far up the upper arm the light runs: its inner edge, its outer edge
E_Z = (1.0, 1.035, 1.2)    # the creep, then the jump
E_NECK = (560.0, 1300.0)   # her head comes up about here as she lifts her eyes ...
E_LIFT = 2.5               # ... by this much (deg)


def _hs(pts, ang=E_ANG, at=E_EAR, s=E_S):
    """Handset units (x along the handle from the earpiece, y toward the cups) -> frame px."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(at[0] + s * (x * ca - y * sa), at[1] + s * (x * sa + y * ca)) for x, y in pts]


# her right hand round the handle, in handset units: a compact fist on the near end of the
# handle, the knuckles on its outer side, the fingers wrapped over it (seams), the heel of the
# hand on the inner side, where the wrist goes down to the forearm.
E_FIST = [(25.0, -9.0), (28.0, -20.0), (34.5, -26.5), (45.0, -28.5), (56.0, -27.0), (64.5, -22.5), (70.0, -12.0),
          (71.0, 1.0), (67.0, 11.0), (57.0, 17.5), (44.0, 19.5), (32.0, 16.0), (25.5, 5.0)]
E_FINGER_SEAMS = [[(39.5, -27.0), (38.0, -14.0), (39.0, -2.0), (41.0, 6.0)],
                  [(50.5, -27.5), (49.5, -14.0), (50.5, -1.0), (52.0, 7.0)],
                  [(60.5, -25.0), (59.5, -12.5), (60.0, -1.0), (61.0, 6.0)]]
E_THUMB = ([(36.0, -19.0), (22.0, -20.5), (10.0, -19.0), (2.0, -17.0)], (15.0, 13.0, 11.5, 10.5))
E_WRIST = (57.5, 11.3)     # in the heel of her hand: the forearm goes down from it


def ear_eyes(t):
    """(lid, look forward, look up): down on the floor, then lifted to the window (on twos)."""
    u = k(twos(t), T_LOOK, 0.17, "out")
    return lerp(0.5, 1.1, u), lerp(0.3, 1.0, u), lerp(-0.9, 0.9, u)


def draw_ear_eye(c, lid, lx, ly, wide=1.0):
    c0 = (B.EYE_P[0], B.EYE_P[1] - 10.0 * (wide - 1.0))
    eye = B.almond(c0, 84.0, 40.0 * wide, lid)
    bass.fill_polys(c, [eye], PAPER)
    pc = (B.EYE_P[0] + 20.0 + 8.0 * lx, B.EYE_P[1] - 4.0 + 6.0 * (1.0 - lid) - 7.0 * ly)
    c.save()
    c.new_path()
    bass.draw.poly(c, eye)
    c.clip()
    bass.fill_polys(c, [bass.ring_pts(pc, 11.0 * (2.0 - wide * 0.6), seed=312, n=20, amp=0.2)], INK)
    c.restore()
    top = eye[: len(eye) // 2 + 1]
    for f, L, a in ((0.86, 54.0, -36.0), (0.94, 52.0, -17.0)):
        b = top[int(f * (len(top) - 1))]
        tip = (b[0] + math.cos(math.radians(a)) * L, b[1] + math.sin(math.radians(a)) * L)
        bass.fill_polys(c, [bass.orient([(b[0] - 8.0, b[1] + 3.0), (b[0] + 8.0, b[1] + 2.0), tip], True)], INK)


def _prof(prof, u):
    """A piecewise-linear width profile [(u, w), ...] at u."""
    for (u0, w0), (u1, w1) in zip(prof, prof[1:]):
        if u <= u1:
            return lerp(w0, w1, clamp((u - u0) / ((u1 - u0) or 1.0), 0.0, 1.0))
    return prof[-1][1]


def _band(p0, p1, prof, n=16, ext0=0.0):
    """The two edges of a tapered band from p0 to p1 (starting ext0 behind p0): the edge on
    the side of the direction turned +90 deg, and the other."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    a, b = [], []
    for i in range(n + 1):
        s = lerp(-ext0, L, i / n)
        w = _prof(prof, clamp(s / L, 0.0, 1.0))
        x, y = p0[0] + ux * s, p0[1] + uy * s
        a.append((x - uy * w, y + ux * w))
        b.append((x + uy * w, y - ux * w))
    return a, b


def _crossing(a, b):
    """The first place polyline a crosses polyline b: (index in a, index in b, the point)."""
    for i in range(len(a) - 1):
        p, q = a[i], a[i + 1]
        for j in range(len(b) - 1):
            r, s_ = b[j], b[j + 1]
            d1, d2 = (q[0] - p[0], q[1] - p[1]), (s_[0] - r[0], s_[1] - r[1])
            den = d1[0] * d2[1] - d1[1] * d2[0]
            if abs(den) < 1e-9:
                continue
            u = ((r[0] - p[0]) * d2[1] - (r[1] - p[1]) * d2[0]) / den
            v = ((r[0] - p[0]) * d1[1] - (r[1] - p[1]) * d1[0]) / den
            if 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0:
                return i, j, (p[0] + d1[0] * u, p[1] + d1[1] * u)
    raise ValueError("the arm's edges do not cross")


def _upto(pts, share):
    """The first `share` of a polyline, by length."""
    cum = [0.0]
    for p, q in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    goal = cum[-1] * share
    out = [pts[0]]
    for i in range(1, len(pts)):
        if cum[i] >= goal:
            u = (goal - cum[i - 1]) / ((cum[i] - cum[i - 1]) or 1.0)
            out.append((lerp(pts[i - 1][0], pts[i][0], u), lerp(pts[i - 1][1], pts[i][1], u)))
            return out
        out.append(pts[i])
    return out


def _fold_arm(wr, elbow, shoulder):
    """Her arm folded at the elbow, as one cut piece: the forearm from the wrist (its end
    tucked in under the fist) down to the elbow, the upper arm back up into her at the
    shoulder. Returns (outline, inner edge, outer edge); the edges run from the wrist: the
    inner one down the forearm into the crook and up the upper arm, the outer one down the
    forearm, round the point of the elbow and up the underside of the upper arm."""
    fa, fb = _band(wr, elbow, E_FORE_HW, n=18, ext0=50.0)     # fa: the crook's side
    ua, ub = _band(elbow, shoulder, E_UPPER_HW, n=12)
    i, j, x = _crossing(fa, ua)
    fore_in, up_in = fa[: i + 1] + [x], [x] + ua[j + 1:]
    a0 = math.atan2(fb[-1][1] - elbow[1], fb[-1][0] - elbow[0])
    a1 = math.atan2(ub[0][1] - elbow[1], ub[0][0] - elbow[0])
    sweep = (a1 - a0) % (2.0 * math.pi)
    if sweep > math.pi:                     # round the outside of the elbow, the short way
        sweep -= 2.0 * math.pi
    r = _prof(E_FORE_HW, 1.0)
    arc = [(elbow[0] + r * math.cos(a0 + sweep * m / 10.0), elbow[1] + r * math.sin(a0 + sweep * m / 10.0))
           for m in range(1, 10)]
    fore_out = fb + arc
    outline = fore_in + up_in[1:] + (fore_out + ub)[::-1]
    return outline, (fore_in, up_in), (fore_out, ub)


def _fading(c, pts, width, color, fade=150.0, step=6.0):
    """A rim line that thins away to nothing over its last `fade` px (the light runs off the edge)."""
    pts = _resample(pts, step)
    cum = [0.0]
    for p, q in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    total = cum[-1]
    c.save()
    c.set_source_rgb(*color)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    full = [p for p, s_ in zip(pts, cum) if total - s_ >= fade]
    if len(full) > 1:
        c.new_path()
        bass.draw.poly(c, full, close=False)
        c.set_line_width(width)
        c.stroke()
    for p, q, s_ in zip(pts, pts[1:], cum):
        w = width * clamp((total - s_) / fade, 0.0, 1.0)
        if total - s_ >= fade or w < 0.5:
            continue
        c.new_path()
        c.move_to(*p)
        c.line_to(*q)
        c.set_line_width(w)
        c.stroke()
    c.restore()


def _resample(pts, step):
    out = [pts[0]]
    for p, q in zip(pts, pts[1:]):
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        m = max(1, int(math.ceil(L / step)))
        out += [(lerp(p[0], q[0], i / m), lerp(p[1], q[1], i / m)) for i in range(1, m + 1)]
    return out


@lru_cache(maxsize=1)
def _ear_pieces():
    """The arm, the fist and its seams, the thumb (frame px; only the tremble moves them)."""
    wr = _hs([E_WRIST])[0]
    arm, (fore_in, up_in), (fore_out, up_out) = _fold_arm(wr, E_ELBOW, E_SHOULDER)
    # past the shoulder the arm runs on into her (no edge there): its light runs off the edges
    rims = tuple(fore + (_upto(up, share)[1:] if share > 0.0 else [])
                 for fore, up, share in ((fore_in, up_in, E_RIM[0]), (fore_out, up_out, E_RIM[1])))
    fist = _cut(_cr_closed(_hs(E_FIST), 4), 2701, 12.0)
    seams = [_cr_open(_hs(s_), 4) for s_ in E_FINGER_SEAMS]
    th, th_op = finger(_hs(E_THUMB[0]), tuple(w * E_S for w in E_THUMB[1]), knuck=0.03, pad=0.04, tip=1.15, back=8.0)
    return (_cut(arm, 2700, 20.0), rims), fist, seams, (_cut(th, 2702, 8.0), th_op)


def ear_ripples(c, t, p):
    if t >= T_CLICK:                     # answered: the ringing stops dead
        return
    for t0 in T_RING:
        K.ripple(c, p, t, t0, PAPER, n=3, every=0.1, life=0.55, r0=40.0, r1=330.0, width=10.0, seed=2710)


def draw_ear(c, t):
    B.fill(c, AMBER)
    # her shoulders run on below the frame
    bass.fill_polys(c, [bass.orient([(300.0, 1940.0), (1200.0, 1580.0), (1700.0, 1500.0), (1700.0, 2600.0),
                                     (250.0, 2600.0)], True)], INK)
    bass.fill_polys(c, [bass.orient(B.PROFILE, True)], INK)
    B.edged(c, [bass.orient(B.BOB, True)], INK, AMBER, 9.0)
    lid, lx, ly = ear_eyes(t)
    draw_ear_eye(c, lid, lx, ly)
    (arm, rims), fist, seams, (th, th_op) = _ear_pieces()
    tt = twos(t)
    jx, jy = 1.2 * math.sin(tt * 43.0), 1.2 * math.cos(tt * 37.0)       # her hand is not quite still
    c.save()
    c.translate(jx, jy)
    HR.handset_side(c, E_EAR, E_ANG, E_S, L=110.0, seed=1400, color=INK, edge=AMBER, edge_w=9.0)
    for rim in rims:
        _fading(c, rim, 9.0, HR.LANDING_LIT)
    B.edged(c, [fist], INK, HR.LANDING_LIT, 9.0)
    bass.fill_polys(c, [arm], INK)
    HR.cut_lines(c, seams, 4.5, HR.LANDING_LIT)
    c.new_path()
    bass.draw.poly(c, th_op, close=False)
    c.set_source_rgb(*HR.LANDING_LIT)
    c.set_line_width(9.0)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.stroke()
    bass.fill_polys(c, [th], INK)
    c.restore()
    ear_ripples(c, t, (E_EAR[0] + jx, E_EAR[1] + jy))


def draw_ear_shot(c, t):
    z = lerp(E_Z[0], E_Z[1], k(t, T_EAR, T_JUMP - T_EAR, "inout"))
    z = lerp(z, E_Z[2], k(t, T_JUMP, 0.08, "out"))
    c.save()
    c.translate(*B.EYE_P)
    c.scale(z, z)
    c.translate(-B.EYE_P[0], -B.EYE_P[1])
    # her head comes up a little with her eyes (on twos), about her neck
    c.translate(*E_NECK)
    c.rotate(math.radians(-E_LIFT * k(twos(t), T_LOOK, 0.25, "out")))
    c.translate(-E_NECK[0], -E_NECK[1])
    draw_ear(c, t)
    c.restore()


# ============================================================================ the scene
def draw_at(c, t):
    if t < T_HANDS:
        draw_room(c, t)
    elif t < T_DIAL:
        draw_hands(c, t)
    elif t < T_EAR:
        draw_dial_shot(c, t)
    else:
        draw_ear_shot(c, t)


def render(f, t, T):
    K.scene_setup(f)
    with f.screen() as c:
        draw_at(c, t)


def motion_blur(t, T):
    return 1


def cues(T):
    out = [
        Cue(T_DOOR, "his door creaks open, slow, onto the lit landing", gain_db=-8, pan=-0.5, dur=round(T_OPEN - T_DOOR, 3)),
        Cue(T_OPEN - 0.3, "the lamp sways in the draught: its chain creaks, faint", gain_db=-22, dur=1.0),
        Cue(T_SEE, "her breath catches", gain_db=-6, pan=-0.4),
        Cue(T_REACH, "her sleeve: a soft rustle as her hand comes down", gain_db=-18),
        Cue(T_TOUCH, "her fingertips touch the palm: the faintest skin sound", gain_db=-20),
        Cue(T_TWITCH, "the fingers twitch: a tiny dry flick", gain_db=-14),
        Cue(T_TWITCH + 0.05, "her breath in, startled", gain_db=-12),
        Cue(T_CLOSE, "the hand closes on hers: a soft squeeze", gain_db=-14, dur=round(T_SHUT - T_CLOSE, 3)),
        Cue(T_PULSE, "a faint breath (the woman on the floor): alive", gain_db=-10),
    ]
    for (d, t_in, t0, t1, t_rel), pulses in zip(DIGITS, pulse_times()):
        out += [Cue(t0, f"the dial winds round to the stop ({d}): the wheel's ratchet under her finger", gain_db=-12,
                    dur=round(t1 - t0, 3)),
                Cue(t1, "the finger stop: a small hard clack", gain_db=-10),
                Cue(t_rel, "the dial runs back on its governor: a soft whirr under the pulses", gain_db=-16,
                    dur=round(wind_of(d) / D_RATE, 3))]
        out += [Cue(tp, "rotary-dial pulse: a sharp click", gain_db=-6, digit=d, pulse=i + 1, of=len(pulses))
                for i, tp in enumerate(pulses)]
    out += [Cue(t0, "ringback in the earpiece: a burred ring, small and far", gain_db=-10, pan=-0.1, dur=0.45)
            for t0 in T_RING]
    out.append(Cue(T_CLICK, "the line clicks open: answered (the ringing stops dead)", gain_db=-8, pan=-0.1))
    return sorted(out, key=lambda c: c["t"])
