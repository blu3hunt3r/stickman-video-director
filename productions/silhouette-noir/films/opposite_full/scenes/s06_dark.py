"""s06 · DARK (66-76): her in the dark; straight down: he crosses toward her; the chain; out of
the window.

Shots (scene time):
  A 0.0-2.0   IN THE DARK, from the floor (rooms.draw_window_view, dark). Her window is a NIGHT
              slot over the dark wall. Crouched under it, back to the wall, she is only two
              small PAPER eyes; they blink, go to the door, come back. She turns to the
              window (her eyes slide away round her head) and rises to peek over the sill:
              an INK head against the teal, its crown caught in cold light.
  B 2.0-5.0   STRAIGHT DOWN, her view from the fourth floor: the street from above, the lamp's
              AMBER pool, the curbs, her fire escape's gratings under her. His door opens and
              throws a slab of light; he steps out (hat brim and shoulders, from above), the
              door swings to behind him; he crosses toward her building, a RED dot at each
              footfall, on the beat; under the lamp he stops, looks up: two tiny red glints.
              The view tightens on him on the beat.
  C 5.0-6.5   THE CHAIN, close: the edge of her door in the dark, the chain's slotted track;
              her hand brings the knob to the slot and slides it home, trembling. A small
              ripple when it seats.
  D 6.5-8.5   THE WINDOW (rooms.draw_stage, dark, the window and her fire escape): she squats
              at the sash and heaves it up (the body from CMU 56_03, "lift open window"); it
              sticks, then goes, and hits home at the top (a small ripple). The night comes in
              (the curtain billows, the lamp's cord sways). She ducks into the opening, gets a
              knee on the sill, and her head and shoulders go out over the platform, in front
              of the ladder from the fifth floor. Her broken mug lies by the glass where s08's
              keyhole has it.
  E 8.5-10.0  LOW ANGLE from the street, down the block (a real perspective): her building's
              corner and dark facade, the fire escape seen from under its gratings, its ladders
              zig-zagging (the section's zig-zag) against the night and a big moon. She comes
              up out of her window behind the railing, steps out onto the fourth-floor
              platform, goes to the rail and looks down over it, against the moon. The
              ironwork behind her is a shade lighter than her ink; the camera pushes in.
              (s07 picks her up there: her paper dot goes down the fire escape.)
"""
import math
from dataclasses import replace
from functools import lru_cache

import cairo

from engine import bass, mocap as mc, paperdoll as pd
from engine.core import clamp, ease, hash01, lerp
from engine.palette import RED
from engine.timing import Cue
from films.opposite_bass import world as B
from films.opposite_full import kit as K
from films.opposite_full import rooms as R

k = K.k
INK, PAPER, AMBER, NIGHT, STEEL, DEEP, SHUT = K.INK, K.PAPER, K.AMBER, K.NIGHT, K.STEEL, K.DEEP, K.SHUT

# ---------------------------------------------------------------- beats (scene time)
T_BREATH = (0.1, 1.05)        # her breath (in the dark)
T_BLINK = 0.5                 # her eyes blink, on the beat
T_GLANCE = (0.7, 1.0)         # her eyes go to the door, and come back
T_TURN = 1.12                 # she turns to the window ...
T_RISE = (1.2, 1.9)           # ... and rises to peek over the sill
T_DOWN = 2.0                  # cut: straight down
T_DOOR = 2.5                  # his door opens: a slab of light
T_OUT = 2.72                  # he steps out
T_STEPS = (3.0, 3.5, 4.0)     # his footfalls, on the beat (red dots)
T_STOP = 4.22                 # under the lamp he stops ...
T_LOOK = 4.5                  # ... and looks up: two tiny red glints (the view tightens)
T_SHUT = 3.3                  # his door swings to behind him
T_CHAIN = 5.0                 # cut: the chain, close
T_SLIDE = (5.32, 6.02)        # her hand slides the chain along its track ...
T_HOME = 6.02                 # ... and it seats
T_WINDOW = 6.5                # cut: the window
T_LIFT = (6.68, 7.2)          # the sash goes up
T_WIND = 7.12                 # the night comes in
T_DUCK = 7.35                 # she ducks into the opening ...
T_KNEE = 7.96                 # ... a knee on the sill
T_LOW = 8.5                   # cut: the low angle from the street
T_STEP_OUT = 8.62             # she steps out onto the platform: the near leg over the sill ...
T_PLANT = (8.90, 9.22, 9.40)  # ... her feet come down on the grating (near, far), a step to the rail
T_LOOK_DOWN = 9.5             # ... and looks down
FILM0 = 66.0                  # film time at t = 0


def twos(t):
    return K.twos(t)


# ================================================================ A: in the dark, from the floor
CAM_A = (R.Cam(540.0, 1190.0, 1.0), R.Cam(548.0, 1150.0, 1.07))
NAPE_A = ((580.0, 1900.0), (700.0, 1560.0))      # her nape, view px: crouched, risen (by the curtain, clear of the lamp)
S_A = (1.72, 1.52)                                # her head's scale (smaller as she goes to the glass)
EYE_DX, EYE_Y = 36.0, -150.0                      # her eyes in head units (front view)


def cam_a(t):
    return R.cam_lerp(CAM_A[0], CAM_A[1], k(t, 0.0, T_DOWN, "inout"))


def turn_a(t):
    """0 facing us .. 1 her back to us (on twos: three drawings)."""
    return k(twos(t), T_TURN, 0.25, "inout")


def her_a(t):
    """(nape px in view space, scale) of her head and shoulders."""
    tt = twos(t)
    u = k(tt, T_RISE[0], T_RISE[1] - T_RISE[0], "inout")
    breath = 7.0 * math.sin(2.0 * math.pi * 0.95 * tt) * (1.0 - 0.6 * u)        # quick, scared
    x = lerp(NAPE_A[0][0], NAPE_A[1][0], u)
    y = lerp(NAPE_A[0][1], NAPE_A[1][1], u) - breath
    # rising, she comes up a little ahead of herself, and settles (outback)
    y -= 10.0 * math.sin(math.pi * clamp((tt - T_RISE[1] + 0.12) / 0.3)) * (tt > T_RISE[1] - 0.12)
    return (x, y), lerp(S_A[0], S_A[1], u)


def eyes_a(c, t, base, s):
    """Her two small paper eyes, while she faces us: almonds with ink pupils, a blink on the
    beat, a glance at the door; as she turns they slide away round her head and go."""
    th = math.pi * turn_a(t)
    if th >= math.pi * 0.75:
        return
    tt = twos(t)
    blink = 1.0 - (k(tt, T_BLINK, 0.06) - k(tt, T_BLINK + 0.08, 0.08))
    gl = k(tt, T_GLANCE[0], 0.08, "out") * (1.0 - k(tt, T_GLANCE[1], 0.1, "inout"))
    gaze = -0.75 * gl
    for side in (-1.0, 1.0):
        a = side * math.radians(24.0) + th
        if math.cos(a) <= 0.08:
            continue
        x = 92.0 * math.sin(a)
        w = math.cos(a)
        cx, cy = base[0] + s * x, base[1] + s * EYE_Y
        rx, ry = 15.0 * s * w, 7.8 * s * blink
        if ry < 1.0:
            continue
        bass.fill_polys(c, [bass.orient(_almond((cx, cy), rx, ry), True)], PAPER)
        px = cx + s * (gaze * 7.5 + 3.0 * (1.0 - w)) * w
        c.save()
        c.new_path()
        bass.draw.poly(c, _almond((cx, cy), rx, ry))
        c.clip()
        K.dot(c, (px, cy + 0.6 * s), 4.6 * s, INK, seed=int(side) + 3)
        c.restore()


def _almond(p, rx, ry, n=20):
    out = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        x = math.cos(a)
        y = math.sin(a) * (1.0 - 0.18 * x * x)
        out.append((p[0] + rx * x, p[1] + ry * y * (1.0 if y < 0 else 0.8)))
    return out


def draw_a(c, t):
    cam = cam_a(t)
    room = R.Room(lit=False, mug=False, kettle=True, film_t=FILM0 + t)
    R.draw_window_view(c, t, room, cam=cam, his_lit=True, lamp_on=True)
    nape, s = her_a(t)
    base = cam.to_frame(nape)
    sz = s * cam.z
    # the cold light from the window catches her crown, then her: ink
    R.draw_back(c, "her", (base[0] + 1.0, base[1] - 4.5), sz, t=t, color=STEEL)
    R.draw_back(c, "her", base, sz, t=t, color=INK)
    eyes_a(c, t, base, sz)


# ================================================================ the scene
def render(f, t, T):
    K.scene_setup(f)
    with f.screen() as c:
        if t < T_DOWN:
            draw_a(c, t)
        elif t < T_CHAIN:
            draw_b(c, t)
        elif t < T_WINDOW:
            draw_c(c, t)
        elif t < T_LOW:
            draw_d(c, t)
        else:
            draw_e(c, t)


# ================================================================ B: straight down
# A plan of the street seen from above (plan px: 1 m = PX_M px at the base view): the foot of
# his building at the top with his door, his sidewalk and curb, the road, her curb at the
# bottom. Things that stand up are drawn as their tops: the lamp's head over its own pool.
PX_M = 128.0
HIS_FACE_Y = 330.0            # his facade (plan y); his sidewalk below it to the curb
HIS_CURB_Y = 664.0
HER_CURB_Y = 1560.0
NADIR = (540.0, 1990.0)       # straight under her eye: the foot of her own facade (plan px)
EYE_H = 10.6                  # her eye above the street (m)
DOOR_X = (646.0, 756.0)       # his street door (plan x), hinged on the left, opening out
LAMP_POST = (402.0, 640.0)    # the lamp's post, at his curb ...
LAMP_HEAD = (402.0, 760.0)    # ... its arm reaching out over the road to the head
POOL_R = 300.0
STOP_P = (508.0, 590.0)       # where he stops, under the lamp (the centre of his shoulders)
PATH_B = ((702.0, 290.0), (700.0, 384.0), (662.0, 452.0), (588.0, 520.0), STOP_P)    # the door .. the stop
CAM_B = (R.Cam(540.0, 990.0, 1.0), R.Cam(536.0, 900.0, 1.1), R.Cam(500.0, 668.0, 1.72))   # wide, creeping, on him
HIM_S = 1.22                  # his figure from above, a little larger than life (he is the subject)


def cam_b(t):
    creep = R.cam_lerp(CAM_B[0], CAM_B[1], k(t, T_DOWN, T_STOP - T_DOWN, "inout"))
    return R.cam_lerp(creep, CAM_B[2], k(t, T_LOOK, 0.42, "outback"))


def his_track(t):
    """(centre, heading rad, stride phase, moving 0..1) of him on the plan: out of the door,
    one stride per beat to the lamp."""
    keys = [(T_OUT - 0.15, PATH_B[0]), (T_OUT + 0.12, PATH_B[1]), (T_STEPS[0], PATH_B[2]), (T_STEPS[1], PATH_B[3]),
            (T_STOP, PATH_B[4])]
    tt = twos(t)
    if tt <= keys[0][0]:
        p, i = keys[0][1], 0
    elif tt >= keys[-1][0]:
        p, i = keys[-1][1], len(keys) - 2
    else:
        for i in range(len(keys) - 1):
            if keys[i][0] <= tt < keys[i + 1][0]:
                break
        u = (tt - keys[i][0]) / (keys[i + 1][0] - keys[i][0])
        a, b = keys[i][1], keys[i + 1][1]
        p = (lerp(a[0], b[0], u), lerp(a[1], b[1], u))
    a, b = keys[i][1], keys[i + 1][1]
    head = math.atan2(b[1] - a[1], b[0] - a[0])
    if tt >= T_STOP:
        # stopped: he turns to face her window squarely (straight under her eye), then looks up
        face = math.atan2(NADIR[1] - p[1], NADIR[0] - p[0])
        head = lerp(head, face, k(tt, T_STOP, 0.2, "inout"))
    moving = clamp((tt - keys[0][0]) / 0.1) * (1.0 - k(tt, T_STOP - 0.05, 0.15))
    phase = (tt - T_OUT) / K.BEAT * math.pi
    return p, head, phase, moving


def footfalls_b():
    """(plan point, time) of each red dot: his feet, left and right of his line."""
    out = []
    pts = list(PATH_B[1:])
    times = [T_OUT + 0.12] + list(T_STEPS)
    for j, (p, tf) in enumerate(zip(pts, times)):
        a = pts[max(j - 1, 0)]
        q = pts[min(j + 1, len(pts) - 1)]
        d = (q[0] - a[0], q[1] - a[1])
        dl = math.hypot(*d) or 1.0
        n = (-d[1] / dl, d[0] / dl)
        side = 1.0 if j % 2 == 0 else -1.0
        out.append(((p[0] + n[0] * 14.0 * side + d[0] / dl * 20.0, p[1] + n[1] * 14.0 * side + d[1] / dl * 20.0), tf))
    # the stop: the other foot comes up beside the last
    p = PATH_B[-1]
    out.append(((p[0] - 12.0, p[1] + 24.0), T_STOP))
    return out


def door_open(t):
    """His door's swing, 0 shut .. 1 open (out over the sidewalk)."""
    return k(t, T_DOOR, 0.3, "out3") * (1.0 - k(t, T_SHUT, 0.45, "inout"))


def draw_street_plan(c, t):
    """The street from above: his building's foot, his sidewalk, the curbs, the road with a
    manhole and a drain, her sidewalk."""
    side = lerp(NIGHT, STEEL, 0.42)
    K.fill(c, NIGHT)
    bass.fill_polys(c, [bass.cut_rect(-300.0, -600.0, 1380.0, HIS_CURB_Y, seed=901, amp=0.5)], side)
    bass.fill_polys(c, [bass.cut_rect(-300.0, HER_CURB_Y, 1380.0, 2600.0, seed=902, amp=0.5)], side)
    # the curbs: the stone edge catching the light, the gutter's shade
    edge = lerp(STEEL, PAPER, 0.22)
    gutter = lerp(NIGHT, INK, 0.45)
    bass.fill_polys(c, [bass.cut_rect(-300.0, HIS_CURB_Y - 6.0, 1380.0, HIS_CURB_Y, seed=903, amp=0.3)], edge)
    bass.fill_polys(c, [bass.cut_rect(-300.0, HIS_CURB_Y, 1380.0, HIS_CURB_Y + 16.0, seed=904, amp=0.3)], gutter)
    bass.fill_polys(c, [bass.cut_rect(-300.0, HER_CURB_Y, 1380.0, HER_CURB_Y + 6.0, seed=905, amp=0.3)], edge)
    bass.fill_polys(c, [bass.cut_rect(-300.0, HER_CURB_Y - 16.0, 1380.0, HER_CURB_Y, seed=906, amp=0.3)], gutter)
    # the paving joints, faint
    c.save()
    c.set_source_rgba(*NIGHT, 0.6)
    c.set_line_width(2.2)
    for x in range(-60, 1300, 160):
        for (y0, y1) in ((HIS_FACE_Y, HIS_CURB_Y - 6.0), (HER_CURB_Y + 6.0, 2400.0)):
            c.move_to(x, y0)
            c.line_to(x + 3.0, y1)
    c.stroke()
    c.restore()
    # a manhole in the road, a drain at his curb
    mh = (760.0, 1180.0)
    bass.fill_polys(c, [bass.ring_pts(mh, 50.0, seed=910, n=64, amp=0.3)], gutter)
    bass.fill_polys(c, [bass.ring_pts(mh, 42.0, seed=911, n=64, amp=0.3)], lerp(NIGHT, STEEL, 0.3))
    for j in range(-2, 3):
        w = math.sqrt(max(0.0, 36.0 ** 2 - (j * 14.0) ** 2))
        bass.fill_polys(c, [bass.cut_rect(mh[0] - w, mh[1] + j * 14.0 - 2.5, mh[0] + w, mh[1] + j * 14.0 + 2.5,
                                          seed=912 + j, amp=0.2)], gutter)
    dr = (220.0, HIS_CURB_Y + 36.0)
    bass.fill_polys(c, [bass.cut_rect(dr[0] - 46.0, dr[1] - 13.0, dr[0] + 46.0, dr[1] + 13.0, seed=915, amp=0.3)], INK)
    for j in range(-3, 4):
        bass.fill_polys(c, [bass.cut_rect(dr[0] + j * 11.0 - 2.0, dr[1] - 9.0, dr[0] + j * 11.0 + 2.0, dr[1] + 9.0,
                                          seed=916 + j, amp=0.1)], lerp(NIGHT, STEEL, 0.25))
    # his building's foot: ink, its base course catching a little light
    bass.fill_polys(c, [bass.cut_rect(-300.0, -600.0, 1380.0, HIS_FACE_Y, seed=920, amp=0.5)], INK)
    bass.fill_polys(c, [bass.cut_rect(-300.0, HIS_FACE_Y - 20.0, 1380.0, HIS_FACE_Y - 11.0, seed=921, amp=0.4)],
                    lerp(INK, STEEL, 0.3))
    # his doorstep
    bass.fill_polys(c, [bass.cut_rect(DOOR_X[0] - 16.0, HIS_FACE_Y, DOOR_X[1] + 16.0, HIS_FACE_Y + 22.0, seed=922, amp=0.3)],
                    lerp(NIGHT, STEEL, 0.6))


def draw_door_light(c, t):
    """His doorway: the hall light behind it; while it is open, the slab of light it throws
    out across his sidewalk past the leaf, and the leaf itself swinging on its hinge."""
    u = door_open(t)
    x0, x1 = DOOR_X
    y = HIS_FACE_Y
    if u <= 0.0:
        # shut: a thread of light under the door
        bass.fill_polys(c, [bass.cut_rect(x0 + 6.0, y - 5.0, x1 - 6.0, y + 1.0, seed=930, amp=0.2)], AMBER, 0.9)
        return
    a = math.radians(100.0 * u)                    # the leaf, hinged at x0, swinging out
    tip = (x0 + (x1 - x0) * math.cos(a), y + (x1 - x0) * math.sin(a))
    L = 470.0 * min(1.0, u * 1.2)
    far = (x1 + 150.0 * u, y + L)
    near = (tip[0] + (tip[0] - x0) * 0.5 * u - 30.0 * u, y + L * 0.95)
    bass.fill_polys(c, [bass.orient([tip, (x1, y), far, near], True)], AMBER, 0.36)
    bass.fill_polys(c, [bass.cut_rect(x0, y - 12.0, x1, y + 1.0, seed=931, amp=0.2)], AMBER)
    bass.fill_polys(c, [bass.orient(bass.line_pts([(x0, y), tip], width=12.0, seed=932), True)], INK)


def draw_pool(c):
    bass.fill_polys(c, [bass.ring_pts(LAMP_HEAD, POOL_R, seed=940, n=96, amp=0.6)], AMBER, 0.3)
    bass.fill_polys(c, [bass.ring_pts(LAMP_HEAD, POOL_R * 0.52, seed=941, n=80, amp=0.4)], AMBER, 0.18)


def draw_lamp_top(c):
    """The street lamp from above: the post's cap at the curb, the arm out over the road, the
    head's ink cap with a cold rim."""
    bass.fill_polys(c, [bass.ring_pts(LAMP_POST, 13.0, seed=950, n=28, amp=0.2)], INK)
    bass.fill_polys(c, [bass.orient(bass.line_pts([LAMP_POST, LAMP_HEAD], width=9.0, seed=951), True)], INK)
    bass.fill_polys(c, [bass.ring_pts(LAMP_HEAD, 37.0, seed=952, n=48, amp=0.3)], lerp(INK, STEEL, 0.6))
    bass.fill_polys(c, [bass.ring_pts(LAMP_HEAD, 33.0, seed=953, n=48, amp=0.3)], INK)
    bass.fill_polys(c, [bass.ring_pts(LAMP_HEAD, 9.0, seed=954, n=20, amp=0.2)], lerp(INK, STEEL, 0.5))


def draw_him_top(c, t, p, head, phase, moving, look):
    """Him from above: the long coat and the shoulders, the arms swinging, the hat's brim and
    dented crown. look 0..1: his head tips back to look up; the brim lifts at the front and
    his face shows under it, with two tiny red glints."""
    sw = math.sin(phase) * moving
    c.save()
    c.translate(*p)
    c.rotate(head + math.pi / 2.0)          # local: -y = forward
    c.scale(HIM_S, HIM_S)
    for sgn in (-1.0, 1.0):                 # his feet, out ahead and behind in the stride
        fy = -sgn * 24.0 * sw
        bass.fill_polys(c, [bass.orient(bass.capsule_pts((sgn * 11.0, fy - 7.0), (sgn * 11.0, fy + 9.0), 7.0, 6.5, 6), True)],
                        INK)
    coat = [(-31.0, -6.0), (-38.0, 10.0), (-32.0, 32.0), (0.0, 40.0), (32.0, 32.0), (38.0, 10.0), (31.0, -6.0), (0.0, -15.0)]
    bass.fill_polys(c, [R._S(R._closed_spline(coat, 5), 960, sag=0.4, amp=0.3)], INK)
    bass.fill_polys(c, [bass.orient(bass.draw.ellipse_pts((0.0, 0.0), 42.0, 18.0, n=44), True)], INK)
    for sgn in (-1.0, 1.0):                 # the arms, swinging fore and aft
        a = (sgn * 39.0, 0.0)
        b = (sgn * 41.0, -sgn * 22.0 * sw + 6.0)
        bass.fill_polys(c, [bass.orient(bass.capsule_pts(a, b, 8.5, 7.5, 6), True)], INK)
    lk = clamp(look)
    if lk > 0.0:
        # his face, tipped up into the lamp's light (a warm ink)
        face = (0.0, -15.0 - 10.0 * lk)
        bass.fill_polys(c, [bass.orient(bass.draw.ellipse_pts(face, 13.5, 6.0 + 9.5 * lk, n=28), True)],
                        lerp(INK, AMBER, 0.2 * lk))
    brim_c = (0.0, 5.0 * lk)
    bass.fill_polys(c, [bass.orient(bass.draw.ellipse_pts(brim_c, 28.0, 26.0 - 8.0 * lk, n=48), True)], INK)
    crown_c = (0.0, 2.0 + 6.0 * lk)
    crown = bass.draw.ellipse_pts(crown_c, 15.5, 14.0 - 3.0 * lk, n=36)
    c.set_source_rgb(*lerp(INK, STEEL, 0.8))
    c.set_line_width(2.3)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.new_path()
    bass.draw.poly(c, crown)
    c.stroke()
    c.move_to(crown_c[0], crown_c[1] - 8.5)
    c.line_to(crown_c[0], crown_c[1] + 8.5)
    c.stroke()
    if lk > 0.45:
        g = ease("outback", clamp((lk - 0.45) / 0.35))
        for sgn in (-1.0, 1.0):
            K.dot(c, (sgn * 5.8, -19.0 - 10.0 * lk), 3.3 * g, RED, seed=970 + int(sgn))
    c.restore()


def _shadow(c, p, src, L, alpha, seed):
    d = (p[0] - src[0], p[1] - src[1])
    c.save()
    c.translate(*p)
    c.rotate(math.atan2(d[1], d[0]))
    w = 27.0 * HIM_S
    pts = [(0.0, -w), (L * 0.7, -0.8 * w), (L, -0.45 * w), (L + 15.0, 0.0), (L, 0.45 * w), (L * 0.7, 0.8 * w), (0.0, w),
           (-10.0, 0.0)]
    bass.fill_polys(c, [R._S(R._closed_spline(pts, 4), seed, sag=0.4, amp=0.3)], INK, alpha)
    c.restore()


def draw_shadow_top(c, t, p):
    """His shadow on the ground: thrown ahead of him by the hall light while he is in the
    doorway's slab, then from the lamp's head (long when he is far from it)."""
    u = door_open(t)
    door = ((DOOR_X[0] + DOOR_X[1]) / 2.0, HIS_FACE_Y - 30.0)
    dd = math.dist(p, door)
    if u > 0.05 and dd < 330.0:
        _shadow(c, p, door, 40.0 + 1.1 * dd, 0.5 * min(1.0, u * 1.5) * (1.0 - clamp((dd - 170.0) / 160.0)), 981)
    dist = math.dist(p, LAMP_HEAD)
    if dist < POOL_R + 40.0:
        _shadow(c, p, LAMP_HEAD, 26.0 + 0.8 * dist, 0.5 * (1.0 - clamp((dist - POOL_R + 40.0) / 80.0)), 980)


def up(p, h):
    """A plan point h metres above the street, as her eye sees it (pushed out from the nadir)."""
    f = EYE_H / (EYE_H - h)
    return (NADIR[0] + (p[0] - NADIR[0]) * f, NADIR[1] + (p[1] - NADIR[1]) * f)


def _quad_up(x0, y0, x1, y1, h, seed, amp=0.25):
    pts = [up(q, h) for q in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    return bass.orient(bass.cut(pts, seed=seed, amp=amp, seg=(14.0, 40.0)), True)


ESC_X = (424.0, 656.0)        # her fire escape's platforms (plan x), either side of her window
ESC_D = 0.9 * PX_M            # how far they stand out from her facade
ESC_H = {2: 3.06, 3: 6.06}    # the platforms under hers (m above the street)
RAIL_H = 0.95                 # the top rail over a platform (m)


def _post_up(p, h0, h1, w, seed):
    a, b = up(p, h0), up(p, h1)
    return bass.orient(bass.line_pts([a, b], width=w * EYE_H / (EYE_H - h1), seed=seed), True)


def draw_fire_escape_top(c):
    """Her fire escape from above, under her: the storey-3 platform close under her (big), the
    storey-2 one further down (smaller), each a grating of slats in a frame, its railing a
    U of posts and rails; the ladder slanting from one down to the other. The lamp catches the
    far edges (cold rims)."""
    xa, xb = ESC_X
    yf = NADIR[1]
    yo = yf - ESC_D
    for n in (2, 3):
        h = ESC_H[n]
        hr = h + RAIL_H
        under, frame, rails = [], [], []
        for j in range(1, 6):                                                   # the slats
            y = yo + j * ESC_D / 6.0
            under.append(_quad_up(xa + 4.0, y - 2.6, xb - 4.0, y + 2.6, h, 1030 + 10 * n + j, amp=0.12))
        frame.append(_quad_up(xa - 2.0, yo - 4.0, xb + 2.0, yo + 4.0, h, 1000 + n))        # the outer edge
        frame.append(_quad_up(xa - 2.0, yo, xa + 6.0, yf, h, 1010 + n))                    # the ends
        frame.append(_quad_up(xb - 6.0, yo, xb + 2.0, yf, h, 1020 + n))
        # the railing: a top rail along the outer edge and back along both ends; posts
        rails.append(_quad_up(xa - 2.0, yo - 3.0, xb + 2.0, yo + 3.0, hr, 1050 + n))
        rails.append(_quad_up(xa - 3.0, yo, xa + 3.0, yf, hr, 1052 + n))
        rails.append(_quad_up(xb - 3.0, yo, xb + 3.0, yf, hr, 1054 + n))
        for i, (x, y) in enumerate(((xa, yo), (xb, yo), ((xa + xb) / 2.0, yo), (xa, yo + ESC_D * 0.5),
                                    (xb, yo + ESC_D * 0.5))):
            rails.append(_post_up((x, y), h, hr, 3.6, 1060 + 10 * n + i))
        bass.fill_polys(c, under, INK)
        c.save()
        c.translate(0.0, -3.0)
        bass.fill_polys(c, [frame[0], rails[0]], lerp(STEEL, PAPER, 0.12))           # the far edges, caught
        c.restore()
        bass.fill_polys(c, frame + rails, INK)
        if n == 2:
            # the ladder from 3 down to 2 (under the storey-3 grating): two stringers, the rungs
            h3 = ESC_H[3]
            a0, a1 = (xb - 70.0, yo + 22.0), (xb - 70.0, yf - 22.0)
            b0, b1 = (xa + 50.0, yo + 22.0), (xa + 50.0, yf - 22.0)
            for (p, q, s) in ((a0, b0, 1071), (a1, b1, 1072)):
                bass.fill_polys(c, [bass.orient(bass.line_pts([up(p, h3), up(q, h)], width=6.0, seed=s), True)], INK)
            for j in range(1, 8):
                u = j / 8.0
                hh = lerp(h3, h, u)
                p = (lerp(a0[0], b0[0], u), a0[1])
                q = (lerp(a1[0], b1[0], u), a1[1])
                bass.fill_polys(c, [bass.orient(bass.line_pts([up(p, hh), up(q, hh)], width=3.4 * EYE_H / (EYE_H - hh),
                                                               seed=1080 + j), True)], INK)


def draw_b(c, t):
    cam = cam_b(t)
    p, head, phase, moving = his_track(t)
    look = k(t, T_LOOK, 0.3, "out3")
    shown = t >= T_OUT - 0.15
    c.save()
    cam.apply(c)
    draw_street_plan(c, t)
    draw_pool(c)
    draw_door_light(c, t)
    if shown:
        draw_shadow_top(c, t, p)
    # the footfalls: a red dot at each, on the beat
    ff = footfalls_b()
    K.step_dots(c, [q for q, _ in ff], [tf for _, tf in ff], t, RED, r=8.0, seed=21)
    if shown:
        c.save()
        if t < T_OUT + 0.1:
            # still in the doorway: only what is out past the facade shows
            K.clip_rect(c, (-200.0, HIS_FACE_Y - 14.0, 1280.0, 2400.0))
        draw_him_top(c, t, p, head, phase, moving, look)
        c.restore()
    draw_lamp_top(c)
    draw_fire_escape_top(c)
    c.restore()


# ================================================================ C: the chain, close
# Frame px. Her door's inside face, close: the casing on the left, the leaf's edge, the chain's
# slotted track on the leaf and its anchor on the casing; below them the door's knob and the
# keyhole. The moon, through the window behind her, lays a slab of cold light across the door
# (the shadow of the sash's meeting rail across it); her hand is a silhouette in it, and its
# shadow trembles with it on the door.
DOOR_C = lerp(DEEP, STEEL, 0.16)          # her door's inside face, in the dark
CASE_C = lerp(DEEP, INK, 0.35)            # the casing round it
CASE_X = (96.0, 236.0)                    # the casing (frame px); the leaf's edge just right of it
EDGE_X = 242.0
TRACK_Y = 842.0                           # the chain's slotted track on the leaf
TRACK_X = (300.0, 560.0)                  # the plate
SEAT_X = 326.0                            # the slot's closed end (the knob seats here)
HOLE_X = 528.0                            # the round hole at its open end
ANCHOR = (166.0, 850.0)                   # the chain's anchor plate on the casing (its eye)
CHAIN_L = 470.0                           # the chain's length (eye to knob)
N_LINKS = 12
KNOB_R = 13.0
DOORKNOB = (392.0, 1286.0)                # the door's own knob ...
KEYHOLE = (392.0, 1452.0)                 # ... and its keyhole, under it
MOON_SLAB = [(318.0, 330.0), (1180.0, 236.0), (1180.0, 1560.0), (150.0, 1720.0)]
RAIL_SHADOW = [(150.0, 1044.0), (1180.0, 930.0), (1180.0, 978.0), (150.0, 1094.0)]
SHADOW_D = (-30.0, 44.0)                  # her hand's shadow on the door, from the moon
KNOB_FROM = (836.0, 1092.0)               # where her hand brings the knob up from


def knob_at(t):
    """The chain's knob, in her fingers: brought up to the hole, in, and slid along the slot
    to its seat (a hitch halfway, where it catches), trembling."""
    tt = twos(t)
    if tt < T_SLIDE[0]:
        u = k(tt, T_CHAIN - 0.05, T_SLIDE[0] - T_CHAIN + 0.05, "out")
        x = lerp(KNOB_FROM[0], HOLE_X + 6.0, u)
        y = lerp(KNOB_FROM[1], TRACK_Y, ease("inout", u)) - 30.0 * math.sin(math.pi * u)
    else:
        # in: along the slot to the seat, with a hitch where it catches
        a = k(tt, T_SLIDE[0], 0.3, "inout")
        b = k(tt, T_SLIDE[0] + 0.4, T_HOME - T_SLIDE[0] - 0.4, "inout")
        x = lerp(HOLE_X, lerp(HOLE_X, SEAT_X, 0.48), a)
        x = lerp(x, SEAT_X, b)
        catch = k(tt, T_SLIDE[0] + 0.28, 0.06) * (1.0 - k(tt, T_SLIDE[0] + 0.4, 0.06))
        x += 5.0 * catch * math.sin(tt * 90.0)
        y = TRACK_Y
    return (x, y)


def tremble(t, amp=1.0):
    """Her hand's tremor (on twos): (dx, dy, deg)."""
    i = int(round(twos(t) * 12.0))
    return ((hash01(i, 601) - 0.5) * 5.0 * amp, (hash01(i, 602) - 0.5) * 5.0 * amp, (hash01(i, 603) - 0.5) * 1.8 * amp)


def catenary(a, b, L, n):
    """n + 1 points spaced evenly along a chain of length L hanging from a to b (y down)."""
    x1, y1 = a[0], -a[1]
    x2, y2 = b[0], -b[1]
    if x2 < x1:
        pts = catenary(b, a, L, n)
        return pts[::-1]
    h, v = x2 - x1, y2 - y1
    d = math.hypot(h, v)
    if L <= d * 1.001 or h < 1.0:
        return [(lerp(a[0], b[0], i / n), lerp(a[1], b[1], i / n)) for i in range(n + 1)]
    target = math.sqrt(L * L - v * v)
    lo, hi = 1e-2, 1e7
    for _ in range(90):
        mid = math.sqrt(lo * hi)
        if 2.0 * mid * math.sinh(min(h / (2.0 * mid), 300.0)) > target:
            lo = mid
        else:
            hi = mid
    A = math.sqrt(lo * hi)
    x0 = (x1 + x2) / 2.0 - A * math.asinh(v / (2.0 * A * math.sinh(h / (2.0 * A))))
    C = y1 - A * math.cosh((x1 - x0) / A)
    s1 = A * math.sinh((x1 - x0) / A)
    out = []
    for i in range(n + 1):
        si = s1 + L * i / n
        x = x0 + A * math.asinh(si / A)
        out.append((x, -(A * math.cosh((x - x0) / A) + C)))
    return out


def chain_pts(t, knob):
    """The chain's link joints from the anchor's eye to the knob: hanging, and swinging a
    little after it seats."""
    pts = catenary(ANCHOR, knob, CHAIN_L, N_LINKS)
    d = max(0.0, t - T_HOME)
    sway = 0.3 * math.exp(-d / 0.32) * math.sin(2.0 * math.pi * d / 0.52) * (t >= T_HOME)
    out = []
    for i, (x, y) in enumerate(pts):
        u = i / N_LINKS
        yl = lerp(ANCHOR[1], knob[1], u)
        out.append((x + sway * (y - yl), y))
    return out


def draw_chain(c, pts, color=INK, glint=True):
    """The links between successive joints: one face on (an oval ring), the next edge on (a
    bar), the moon catching the rings."""
    rings, bars, glints = [], [], []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        m = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        L = math.dist(a, b)
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        ca, sa = math.cos(ang), math.sin(ang)
        if i % 2 == 0:
            for rx, ry, sign in ((L / 2.0 + 8.0, 12.5, True), (L / 2.0 - 1.5, 5.0, False)):
                ring = []
                for j in range(18):
                    th = 2.0 * math.pi * j / 18
                    x, y = rx * math.cos(th), ry * math.sin(th)
                    ring.append((m[0] + x * ca - y * sa, m[1] + x * sa + y * ca))
                rings.append(bass.orient(ring, sign))
            glints.append((m[0] - 6.0 * ca + 8.0 * sa, m[1] - 6.0 * sa - 8.0 * ca))
        else:
            bars.append(bass.orient(bass.capsule_pts((m[0] - (L / 2.0 + 5.0) * ca, m[1] - (L / 2.0 + 5.0) * sa),
                                                     (m[0] + (L / 2.0 + 5.0) * ca, m[1] + (L / 2.0 + 5.0) * sa),
                                                     5.4, 5.4, 4), True))
    bass.fill_polys(c, bars, color)
    bass.fill_polys(c, rings, color)
    if glint:
        for g in glints:
            K.dot(c, g, 2.4, lerp(STEEL, PAPER, 0.5), seed=int(g[0]))


# --- her hand, close: the Bass cut's close-up hand (B.cu_hand: palm 170 px, wrist 104), in a
# local frame: the wrist at (0, 0), the hand pointing +x, the thumb on the +y side. Joints are
# (x, y, radius); each finger runs knuckle, middle joint, last joint, tip.
_PALM_BACK = [(0.0, -38.0), (62.0, -48.0), (124.0, -53.0), (158.0, -49.0), (172.0, -28.0), (178.0, -4.0),
              (174.0, 22.0), (154.0, 42.0), (104.0, 52.0), (44.0, 50.0), (0.0, 40.0)]
_POSES = {
    # the knob held between the thumb's pad and the hooked index; the other fingers curled
    # loosely in behind it
    "pinch": dict(
        index=((166.0, 28.0, 16.5), (218.0, 26.0, 15.0), (246.0, 42.0, 13.5), (244.0, 66.0, 12.0)),
        middle=((176.0, 6.0, 17.0), (230.0, 0.0, 15.5), (262.0, 10.0, 14.0), (278.0, 28.0, 12.5)),
        ring=((174.0, -17.0, 16.5), (224.0, -24.0, 15.0), (254.0, -18.0, 13.5), (270.0, -2.0, 12.0)),
        pinky=((164.0, -38.0, 14.5), (202.0, -46.0, 13.0), (226.0, -42.0, 12.0), (240.0, -30.0, 11.0)),
        thumb=((54.0, 42.0, 25.0), (112.0, 72.0, 20.0), (156.0, 82.0, 16.5), (196.0, 77.0, 14.5)),
        grip=(222.0, 84.0)),
    # letting go: the fingers lift off it, the thumb drops away
    "open": dict(
        index=((166.0, 28.0, 16.5), (224.0, 30.0, 15.0), (266.0, 42.0, 13.5), (294.0, 58.0, 12.0)),
        middle=((176.0, 6.0, 17.0), (234.0, 4.0, 15.5), (274.0, 14.0, 14.0), (300.0, 30.0, 12.5)),
        ring=((174.0, -17.0, 16.5), (228.0, -21.0, 15.0), (264.0, -13.0, 13.5), (288.0, 2.0, 12.0)),
        pinky=((164.0, -38.0, 14.5), (206.0, -43.0, 13.0), (236.0, -37.0, 12.0), (256.0, -25.0, 11.0)),
        thumb=((54.0, 42.0, 25.0), (116.0, 80.0, 20.0), (162.0, 98.0, 16.5), (202.0, 108.0, 14.5)),
        grip=(222.0, 84.0)),
}
FOREARM = ((0.0, 0.0, 38.0), (-460.0, 30.0, 56.0))


def _finger_polys(joints):
    out = []
    for (ax, ay, ar), (bx, by, br) in zip(joints, joints[1:]):
        out.append(bass.orient(bass.capsule_pts((ax, ay), (bx, by), ar, br, 7), True))
    return out


def hand_polys(pose, u=0.0):
    """(polys, cuts) of her hand in its local frame. pose 'pinch' | 'open' (u blends pinch to
    open) | 'flat' (laid flat, the Bass cut's open hand, fingers nearly together)."""
    if pose == "flat":
        polys, cuts = B.cu_hand((0.0, 0.0), 0.0, 0.18)
        return polys, cuts
    a, b = _POSES["pinch"], _POSES["open"]
    J = {}
    for name in ("index", "middle", "ring", "pinky", "thumb"):
        J[name] = [(lerp(p[0], q[0], u), lerp(p[1], q[1], u), lerp(p[2], q[2], u)) for p, q in zip(a[name], b[name])]
    polys = [bass.orient(R._closed_spline(_PALM_BACK, 5), True)]
    for name in ("pinky", "ring", "middle", "index", "thumb"):
        polys += _finger_polys(J[name])
    cuts = []
    # the divisions between the fingers: from just past the knuckles, along between them
    for f0, f1 in (("pinky", "ring"), ("ring", "middle")):
        mids = [((p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0) for p, q in zip(J[f0][:3], J[f1][:3])]
        a0 = (lerp(mids[0][0], mids[1][0], 0.3), lerp(mids[0][1], mids[1][1], 0.3))
        a2 = (lerp(mids[1][0], mids[2][0], 0.7), lerp(mids[1][1], mids[2][1], 0.7))
        cuts.append([a0, mids[1], a2])
    # the thumb off the hand
    t0, t1 = J["thumb"][0], J["thumb"][1]
    cuts.append([(lerp(t0[0], t1[0], 0.35), lerp(t0[1], t1[1], 0.35) - 16.0),
                 (lerp(t0[0], t1[0], 0.85), lerp(t0[1], t1[1], 0.85) - 14.0)])
    return polys, cuts


def hand_matrix(at, ang, scale=1.0, flip=True, grip=None):
    """Local hand frame -> frame px: the grip point (or the wrist) at `at`, pointing ang deg;
    flip puts the thumb on the other side (her right hand, back to us, pointing left)."""
    m = cairo.Matrix()
    m.translate(*at)
    m.rotate(math.radians(ang))
    m.scale(scale, -scale if flip else scale)
    if grip is not None:
        m.translate(-grip[0], -grip[1])
    return m


def draw_hand(c, at, ang, pose, u=0.0, scale=1.0, edge=None, knob=False, color=INK, alpha=1.0, flip=True):
    """Her hand and forearm (see hand_polys) placed by hand_matrix; returns the matrix."""
    polys, cuts = hand_polys(pose, u)
    grip = _POSES["pinch"]["grip"] if pose != "flat" else None
    m = hand_matrix(at, ang, scale, flip, grip)
    arm = bass.orient(bass.capsule_pts(FOREARM[0][:2], FOREARM[1][:2], FOREARM[0][2], FOREARM[1][2], 8), True)
    wp = [[m.transform_point(*q) for q in poly] for poly in [arm] + polys]
    if knob:
        K.dot(c, at, KNOB_R, lerp(STEEL, PAPER, 0.2), seed=611)
    if edge is not None:
        B.edged(c, wp, color, edge, 5.0)
    else:
        bass.fill_polys(c, wp, color, alpha)
    if cuts and alpha >= 1.0:
        c.save()
        c.set_source_rgb(*(edge if edge is not None else DOOR_C))
        c.set_line_width(3.0)
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        for ln in cuts:
            c.new_path()
            bass.draw.poly(c, [m.transform_point(*q) for q in ln], close=False)
            c.stroke()
        c.restore()
    return m


def draw_door_face(c, t):
    """The door close, in the dark: the wall and the casing, the leaf with its panel's
    moulding, the chain's anchor plate and slotted track, the knob and the keyhole; then the
    moon's slab across it all, the sash's meeting rail a bar of shadow in it."""
    K.fill(c, DEEP)
    bass.fill_polys(c, [bass.cut_rect(EDGE_X, -100.0, 1300.0, 2100.0, seed=620, amp=0.5)], DOOR_C)
    bass.fill_polys(c, [bass.cut_rect(CASE_X[0], -100.0, CASE_X[1], 2100.0, seed=621, amp=0.5)], CASE_C)
    # the casing's moulding (two cuts) and the crack between it and the leaf
    for x, col, w in ((CASE_X[0] + 26.0, INK, 3.0), (CASE_X[0] + 34.0, lerp(CASE_C, STEEL, 0.35), 2.0),
                      (CASE_X[1] - 18.0, INK, 3.0)):
        bass.fill_polys(c, [bass.cut_rect(x - w / 2.0, -100.0, x + w / 2.0, 2100.0, seed=622 + int(x), amp=0.2)], col)
    bass.fill_polys(c, [bass.cut_rect(CASE_X[1], -100.0, EDGE_X + 2.0, 2100.0, seed=625, amp=0.2)], INK)
    # the leaf's panels: a sunk panel above the lock rail and one below, their mouldings
    # catching the light on the window side
    for (x0, y0, x1, y1, sd) in ((330.0, 120.0, 1180.0, 700.0, 630), (330.0, 1140.0, 1180.0, 2100.0, 634)):
        bass.fill_polys(c, [bass.cut_rect(x0, y0, x1, y1, seed=sd, amp=0.4)], lerp(DOOR_C, INK, 0.25))
        bass.fill_polys(c, [bass.cut_rect(x0 + 14.0, y0 + 14.0, x1, y1, seed=sd + 1, amp=0.4)], DOOR_C)
        bass.fill_polys(c, [bass.cut_rect(x0 + 14.0, y0 + 14.0, x0 + 18.0, y1, seed=sd + 2, amp=0.2)],
                        lerp(DOOR_C, STEEL, 0.4))
    # the anchor plate on the casing, its eye; two screws
    ax, ay = ANCHOR
    plate = bass.cut_rect(ax - 26.0, ay - 52.0, ax + 26.0, ay + 22.0, seed=640, amp=0.3)
    bass.fill_polys(c, [plate], INK)
    bass.fill_polys(c, [bass.cut_rect(ax - 26.0, ay - 52.0, ax + 26.0, ay - 48.0, seed=641, amp=0.2)],
                    lerp(INK, STEEL, 0.5))
    for sy in (ay - 36.0, ay + 8.0):
        K.dot(c, (ax, sy), 5.0, lerp(INK, STEEL, 0.55), seed=642 + int(sy))
    bass.fill_polys(c, [bass.ring_pts((ax, ay), 11.0, seed=644, n=20, amp=0.2),
                        bass.orient(bass.ring_pts((ax, ay), 5.0, seed=645, n=12, amp=0.1), False)], INK)
    # the track: a plate with the slot cut through it, the hole at its open end
    x0, x1 = TRACK_X
    y = TRACK_Y
    tp = R._closed_spline([(x0, y - 22.0), (x1, y - 22.0), (x1 + 6.0, y), (x1, y + 22.0), (x0, y + 22.0), (x0 - 6.0, y)], 4)
    slot = bass.capsule_pts((SEAT_X, y), (HOLE_X, y), 6.5, 6.5, 6)
    hole = bass.ring_pts((HOLE_X, y), 16.0, seed=652, n=24, amp=0.2)
    bass.fill_polys(c, [bass.orient(tp, True)], INK)
    bass.fill_polys(c, [bass.cut_rect(x0, y - 22.0, x1, y - 18.5, seed=651, amp=0.2)], lerp(INK, STEEL, 0.55))
    bass.fill_polys(c, [bass.orient(slot, True), bass.orient(hole, True)], lerp(DOOR_C, INK, 0.45))
    for sx in (x0 + 14.0, x1 - 6.0):
        K.dot(c, (sx, y + (12.0 if sx < x1 - 10 else -12.0)), 4.6, lerp(INK, STEEL, 0.55), seed=653 + int(sx))
    # the door's own knob, on its rose, and the keyhole on its plate under it
    kx, ky = DOORKNOB
    bass.fill_polys(c, [bass.ring_pts((kx, ky), 62.0, seed=660, n=48, amp=0.3)], INK)
    bass.fill_polys(c, [bass.ring_pts((kx + 3.0, ky - 4.0), 44.0, seed=661, n=48, amp=0.3)], lerp(INK, STEEL, 0.45))
    bass.fill_polys(c, [bass.ring_pts((kx, ky), 42.0, seed=662, n=48, amp=0.3)], INK)
    hx, hy = KEYHOLE
    bass.fill_polys(c, [bass.orient(R._closed_spline([(hx - 26.0, hy - 58.0), (hx + 26.0, hy - 58.0), (hx + 30.0, hy),
                                                     (hx + 26.0, hy + 58.0), (hx - 26.0, hy + 58.0), (hx - 30.0, hy)], 4), True)],
                    INK)
    keyhole = [bass.ring_pts((hx, hy - 12.0), 9.5, seed=665, n=20, amp=0.1),
               bass.orient([(hx - 4.5, hy - 8.0), (hx + 4.5, hy - 8.0), (hx + 7.0, hy + 22.0), (hx - 7.0, hy + 22.0)], True)]
    bass.fill_polys(c, keyhole, lerp(INK, NIGHT, 0.5))


def moon_slab(c, alpha=0.2):
    bass.fill_polys(c, [bass.orient(MOON_SLAB, True)], lerp(STEEL, PAPER, 0.3), alpha)
    bass.fill_polys(c, [bass.orient(RAIL_SHADOW, True)], INK, 0.3)


def _in_slab(c):
    c.new_path()
    bass.draw.poly(c, MOON_SLAB)
    c.clip()


def hand_pose_c(t):
    """(pose u, hand point, angle, knob) of her hand in the chain shot: the pinch on the knob
    (bringing it up, sliding it home), then letting go and pulling away out of the frame."""
    tt = twos(t)
    dx, dy, da = tremble(t, 1.0 + 0.6 * k(tt, T_SLIDE[0] + 0.25, 0.2))
    if tt < T_HOME:
        kb = knob_at(t)
        ang = lerp(206.0, 194.0, k(tt, T_CHAIN, T_SLIDE[0] - T_CHAIN))
        ang += 6.0 * k(tt, T_SLIDE[0], T_HOME - T_SLIDE[0], "inout")
        return 0.0, (kb[0] + dx, kb[1] + dy), ang + da, kb
    kb = (SEAT_X, TRACK_Y)
    jolt = 3.0 * (1.0 - k(tt, T_HOME, 0.08))
    u = k(tt, T_HOME + 0.14, 0.12, "out")
    w = k(tt, T_HOME + 0.22, 0.24, "in")
    at = (kb[0] - jolt + dx + 640.0 * w, kb[1] + dy + 300.0 * w)
    return u, at, 200.0 + 14.0 * w + da, kb


CAM_C = ((470.0, 902.0, 1.42), (396.0, 912.0, 1.54))      # close on the track; it follows the knob home


def cam_c(t):
    u = k(t, T_CHAIN, T_WINDOW - T_CHAIN, "inout")
    a, b = CAM_C
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u))


def draw_c(c, t):
    cx, cy, z = cam_c(t)
    c.save()
    c.translate(540.0, 960.0)
    c.scale(z, z)
    c.translate(-cx, -cy)
    draw_door_face(c, t)
    moon_slab(c)
    u, at, ang, kb = hand_pose_c(t)
    links = chain_pts(t, kb)
    gone = at[0] > 1600.0
    # their shadows on the door, where the moon falls on it
    c.save()
    _in_slab(c)
    c.translate(*SHADOW_D)
    c.push_group()
    draw_chain(c, links, INK, glint=False)
    if not gone:
        draw_hand(c, at, ang, "pinch", u=u, flip=True, knob=False)
    c.pop_group_to_source()
    c.paint_with_alpha(0.34)
    c.restore()
    # the knob's neck in the slot, the chain, the knob, her hand
    K.dot(c, kb, 6.5, INK, seed=612)
    draw_chain(c, links)
    if t >= T_HOME:
        K.dot(c, (kb[0] + 1.5, kb[1] - 1.5), KNOB_R + 1.5, lerp(STEEL, PAPER, 0.25), seed=613)
    K.dot(c, kb, KNOB_R, INK, seed=611)
    if not gone:
        draw_hand(c, at, ang, "pinch", u=u, flip=True, knob=False)
    if t >= T_HOME:
        K.ripple(c, kb, t, T_HOME, lerp(STEEL, PAPER, 0.4), n=2, every=0.1, life=0.45, r0=16.0, r1=84.0, width=3.5,
                 seed=615)
    c.restore()


# ================================================================ D: the window
# The stage, dark, close on her window. She squats at the sash with both hands on its lift
# and heaves it up (the body from CMU 56_03, "lift open window"; her hands held on the lift);
# it sticks, then goes. The night comes in: the curtain billows into the room behind her, the
# lamp's cord sways. She ducks into the opening, her hands on the sills, and gets a knee up on
# the sill; her head and shoulders go out over the platform. Her broken mug lies at her feet
# where s04 dropped it (as s08's keyhole shows it).
D_X0 = 1075.0                 # the 56_03 performance's root (her figure units: stage x / FIG_S)
SASH_STICK = 0.14             # the sash jumps this far, sticks, then goes
CAM_D = (R.Cam(936.0, 1300.0, 1.52), R.Cam(1034.0, 1290.0, 1.68))
MUG_X = 831.0                 # her broken mug (s08's MUG_AT: 162 px out from the window wall)


def sash_w(t):
    """The lower sash, 0 shut .. 1 up (moved by her hands: on twos)."""
    tt = twos(t)
    a = SASH_STICK * k(tt, T_LIFT[0], 0.1, "out")
    b = k(tt, T_LIFT[0] + 0.16, T_LIFT[1] - T_LIFT[0] - 0.16, "out3")
    return clamp(a + (1.0 - SASH_STICK) * b)


def wind_d(t):
    return k(t, T_WIND, 0.32, "out")


def cam_d(t):
    return R.cam_lerp(CAM_D[0], CAM_D[1], k(t, T_DUCK - 0.1, T_LOW - T_DUCK + 0.1, "inout"))


def fu(p):
    """stage px -> her figure units (placed at x 0 on the floor, FIG_S)."""
    return (p[0] / R.FIG_S, (p[1] - R.FLOOR) / R.FIG_S)


@lru_cache(maxsize=1)
def lift_perf():
    her = B.figs()[0]
    return mc.Performance(her, [mc.Seg(mc.Clip.load("56_03"), 22.2, 23.3, at=T_LIFT[0] - 0.2, speed=1.25)],
                          facing=1, x=D_X0, near="Right")


LIFT_FEET = ((918.0, 1560.0, 0.0), (874.0, 1560.0, 8.0))        # her feet planted at the sash (stage px, pitch)


def _lift_targets(w):
    y = R.WINDOW[3] - 13.0 - R.LIFT * w            # the lift on the sash's bottom rail
    return (992.0, y + 7.0), (985.0, y + 11.0)


def her_lift(t):
    """Squatting at the sash, then heaving it up: 56_03's body, her hands on the lift."""
    st, p = lift_perf()(twos(t))
    st = dict(st)
    w = sash_w(t)
    p.crouch += 96.0 * (1.0 - w) ** 1.15
    p.lean += 6.0 * (1.0 - w)
    st["feet"] = {"near": fu(LIFT_FEET[0][:2]) + (LIFT_FEET[0][2],), "far": fu(LIFT_FEET[1][:2]) + (LIFT_FEET[1][2],)}
    nh, fh = _lift_targets(w)
    p.arms = {"near": ("ik", fu(nh)), "far": ("ik", fu(fh))}
    p.head += 8.0 * w
    return st, p


# the climb, after the lift: keys (t, pelvis, lean, head, near foot, far foot, near wrist, far wrist), stage px
CLIMB = (
    (7.50, (900.0, 1352.0), 38.0, -2.0, (918.0, 1560.0, 0.0), (874.0, 1560.0, 10.0), (1066.0, 1392.0), (994.0, 1392.0)),
    (7.70, (926.0, 1358.0), 60.0, -8.0, (934.0, 1526.0, 30.0), (880.0, 1560.0, 14.0), (1070.0, 1394.0), (998.0, 1394.0)),
    (T_KNEE, (968.0, 1340.0), 70.0, -14.0, (938.0, 1447.0, -70.0), (896.0, 1560.0, 18.0), (1074.0, 1394.0), (1002.0, 1394.0)),
    (8.26, (1000.0, 1328.0), 74.0, -20.0, (946.0, 1449.0, -76.0), (916.0, 1557.0, 24.0), (1078.0, 1394.0), (1004.0, 1394.0)),
    (8.56, (1024.0, 1322.0), 76.0, -24.0, (952.0, 1450.0, -80.0), (930.0, 1551.0, 30.0), (1080.0, 1394.0), (1006.0, 1394.0)),
)
T_CLIMB0 = 7.3                # the climb takes over from the lift

# ... and on out of the window in E (the low angle): the near leg over the sill, planted on the
# platform, the far leg over; up, and to the railing; she looks down over it
STEP = (
    (8.72, (1042.0, 1366.0), 56.0, -16.0, (1118.0, 1500.0, -26.0), (934.0, 1549.0, 30.0), (1094.0, 1396.0), (1010.0, 1394.0)),
    (T_PLANT[0], (1076.0, 1362.0), 44.0, -10.0, (1130.0, 1577.6, 0.0), (968.0, 1452.0, -74.0), (1104.0, 1398.0), (1022.0, 1396.0)),
    (9.06, (1116.0, 1336.0), 26.0, -6.0, (1134.0, 1577.6, 0.0), (1092.0, 1470.0, -32.0), (1176.0, 1360.0), (1040.0, 1330.0)),
    (T_PLANT[1], (1166.0, 1338.0), 12.0, -2.0, (1146.0, 1577.6, 0.0), (1192.0, 1577.6, 8.0), (1230.0, 1380.0), (1110.0, 1350.0)),
    (T_PLANT[2], (1214.0, 1354.0), 18.0, -8.0, (1244.0, 1577.6, 0.0), (1190.0, 1577.6, 8.0), (1318.0, 1390.0), (1296.0, 1394.0)),
    (9.64, (1226.0, 1366.0), 26.0, -30.0, (1246.0, 1577.6, 0.0), (1192.0, 1577.6, 8.0), (1320.0, 1392.0), (1298.0, 1395.0)),
    (10.0, (1228.0, 1368.0), 27.0, -32.0, (1246.0, 1577.6, 0.0), (1192.0, 1577.6, 8.0), (1320.0, 1392.0), (1298.0, 1395.0)),
)


def _lift_key():
    """The lift's last state as a climb key (stage px)."""
    st, p = her_lift(T_CLIMB0)
    P = st["pelvis"]
    sp = (P[0] * R.FIG_S, R.FLOOR + (P[1] + p.crouch) * R.FIG_S)
    nh, fh = _lift_targets(1.0)
    return (T_CLIMB0, sp, p.lean, p.head, LIFT_FEET[0], LIFT_FEET[1], nh, fh)


def _cr(p0, p1, p2, p3, u):
    """Catmull-Rom between p1 and p2 (tuples)."""
    u2, u3 = u * u, u * u * u
    return tuple(0.5 * ((2.0 * b) + (-a + c) * u + (2.0 * a - 5.0 * b + 4.0 * c - d) * u2 + (-a + 3.0 * b - 3.0 * c + d) * u3)
                 for a, b, c, d in zip(p0, p1, p2, p3))


def her_climb(t):
    keys = (_lift_key(),) + CLIMB + STEP
    tt = twos(t)
    if tt >= keys[-1][0]:
        i, u = len(keys) - 2, 1.0
    elif tt <= keys[0][0]:
        i, u = 0, 0.0
    else:
        i = max(j for j in range(len(keys) - 1) if keys[j][0] <= tt)
        u = ease("inout", (tt - keys[i][0]) / (keys[i + 1][0] - keys[i][0]))
    ks = [keys[max(0, min(len(keys) - 1, i + d))] for d in (-1, 0, 1, 2)]
    flat = [tuple(list(kk[1]) + [kk[2], kk[3]] + list(kk[4]) + list(kk[5]) + list(kk[6]) + list(kk[7])) for kk in ks]
    v = _cr(*flat, u)
    pel, lean, head = (v[0], v[1]), v[2], v[3]
    nf, ff, nh, fh = v[4:7], v[7:10], v[10:12], v[12:14]
    her = B.figs()[0]
    st = pd.standing(her, 0.0)
    st["pelvis"] = fu(pel)
    st["feet"] = {"near": fu(nf[:2]) + (nf[2],), "far": fu(ff[:2]) + (ff[2],)}
    p = pd.Pose(lean=lean, head=head, arms={"near": ("ik", fu(nh)), "far": ("ik", fu(fh))})
    return st, p


def her_d(t):
    return her_lift(t) if twos(t) < T_CLIMB0 else her_climb(t)


def draw_mug_side(c):
    """Her broken mug on the floor at the glass, in profile (stage px): the spill a dark lens on
    the boards, the base standing with its broken rim, the snapped-off handle on its edge, the
    chips; their window-side edges catch the moon. s08 has the same pieces from the keyhole."""
    y = R.FLOOR
    X = MUG_X
    spill = [bass.orient([(X - 64.0, y), (X - 30.0, y - 3.2), (X + 20.0, y - 3.6), (X + 30.0, y - 1.5), (X + 34.0, y),
                          (X - 64.0, y + 1.0)], True),
             bass.orient(bass.draw.ellipse_pts((X - 76.0, y - 0.8), 7.0, 1.6, n=10), True),
             bass.orient(bass.draw.ellipse_pts((X + 46.0, y - 0.8), 9.0, 1.8, n=10), True)]
    bass.fill_polys(c, spill, lerp(INK, DEEP, 0.2))
    bass.line_band(c, [(X - 50.0, y - 2.6), (X - 18.0, y - 3.4), (X + 12.0, y - 3.2)], lerp(STEEL, PAPER, 0.15),
                   width=1.6, seed=1241, alpha=0.6)
    base = [(X - 4.0 + x, y - h) for x, h in ((-16.0, 0.0), (16.0, 0.0), (16.6, 6.0), (13.5, 12.0), (10.0, 7.5), (5.5, 23.0),
                                                (1.5, 14.0), (-3.5, 17.0), (-8.5, 8.0), (-12.5, 11.5), (-16.6, 6.5))]
    handle = []
    hc = (X + 16.0, y - 12.5)
    for i in range(15):
        a = math.radians(lerp(-110.0, 160.0, i / 14.0))
        handle.append((hc[0] + 11.5 * math.cos(a), hc[1] + 12.5 * math.sin(a)))
    for i in range(15):
        a = math.radians(lerp(160.0, -110.0, i / 14.0))
        handle.append((hc[0] + 6.5 * math.cos(a), hc[1] + 7.5 * math.sin(a)))
    chips = [[(X - 58.0, y), (X - 46.0, y), (X - 52.0, y - 6.0)],
             [(X + 34.0, y), (X + 46.0, y), (X + 41.0, y - 4.5)],
             [(X - 34.0, y), (X - 25.0, y), (X - 31.0, y - 5.0)],
             [(X + 52.0, y), (X + 60.0, y), (X + 55.0, y - 3.5)]]
    pieces = [bass.orient(base, True), bass.orient(handle, True)] + [bass.orient(ch, True) for ch in chips]
    c.save()
    c.translate(2.0, -2.5)
    bass.fill_polys(c, pieces, lerp(STEEL, PAPER, 0.15))
    c.restore()
    bass.fill_polys(c, pieces, INK)


# --- her figure with the dress cut at the hips, so that the skirt hangs from her hips and lies
# over her thighs when she bends double (the Bass cut's figure has the dress in one piece with
# the torso, which is right while she stands)
SKIRT = [(-35.0, -26.0), (40.0, -26.0), (46.0, 60.0), (50.0, 146.0), (-42.0, 146.0), (-38.0, 60.0)]
SKIRT_PIVOT = (3.0, -14.0)


@lru_cache(maxsize=1)
def her_upper():
    her = B.figs()[0]
    upper = pd._cut([(-24.0, -258.0), (30.0, -258.0), (42.0, -200.0), (34.0, -110.0), (40.0, -20.0), (37.0, 10.0),
                     (-31.0, 10.0), (-34.0, -20.0), (-30.0, -110.0), (-38.0, -200.0)], 341)
    return replace(her, torso=[(upper, "ink"), her.torso[1]])


@lru_cache(maxsize=1)
def _skirt_polys():
    return [bass.orient(pd._cut(SKIRT, 342), True),
            bass.orient(bass.draw.ellipse_pts(SKIRT_PIVOT, 37.0, 33.0, n=28), True)]


def skirt_angle(fig, st, pose, facing=1):
    """The skirt's hang (deg, like lean): mostly along her thighs, a little with her back."""
    lean = pose.lean
    P = (st["pelvis"][0], st["pelvis"][1] + pose.crouch)
    q = pd._rot((0.0, -4.0), lean)
    hip = (P[0] + facing * q[0], P[1] + q[1])
    angs = []
    for side in ("far", "near"):
        foot = st["feet"][side]
        knee, _ = pd.ik2(hip, (foot[0], foot[1] - fig.ankle), fig.thigh, fig.shin, forward=facing)
        angs.append(math.degrees(math.atan2(facing * (knee[0] - hip[0]), knee[1] - hip[1])))
    th = 0.62 * angs[0] + 0.38 * angs[1]
    # (a hanging piece turned by +a swings its hem back: the rigid dress swings back by lean)
    return lerp(lean, -th, 0.75)


def _draw_skirt(c, st, pose, ang, color, facing=1):
    P = (st["pelvis"][0], st["pelvis"][1] + pose.crouch)
    c.save()
    c.translate(*P)
    c.scale(facing, 1.0)
    c.translate(*SKIRT_PIVOT)
    c.rotate(math.radians(ang))
    c.translate(-SKIRT_PIVOT[0], -SKIRT_PIVOT[1])
    bass.fill_polys(c, _skirt_polys(), color)
    c.restore()


def _only_near_arm(name, centre):
    return (0.0, 0.0, 0.0) if name.endswith("_near") and name.split("_")[0] in ("upper", "fore", "hand") else (1e5, 0.0, 0.0)


def _her_pass(c, st, pose, fig, ang, col, outline, facing=1, edge=None):
    kw = dict(facing=facing, edge=edge if edge is not None else outline, outline=outline, ow=8.0)
    B.draw_cutout(c, fig, st, pose, col, hide=("near",), **kw)
    _draw_skirt(c, st, pose, ang, col, facing)
    return B.draw_cutout(c, fig, st, pose, col, burst=_only_near_arm, **kw)


def draw_her_cut(c, st, pose, bg, facing=1, rim=STEEL, dx=3.0, dy=-2.0):
    """Her cut-out in the dark (inside B.place): a cold edge on the window side, then ink; the
    skirt hung from the hips between her body and her near arm (edged in bg, so that it shows
    across her)."""
    fig = her_upper()
    ang = skirt_angle(fig, st, pose, facing)
    c.save()
    c.translate(dx, dy)
    _her_pass(c, st, pose, fig, ang, rim, None, facing, edge=bg)
    c.restore()
    return _her_pass(c, st, pose, fig, ang, INK, bg, facing)


def draw_d(c, t):
    room = R.Room(lit=False, mug=False, kettle=True, window=sash_w(t), wind=wind_d(t), film_t=FILM0 + t)
    st, p = her_d(t)
    cam = cam_d(t)

    def outside(cc):
        draw_mug_side(cc)
        # the night through the opening, once the sash is up: a brighter wedge on the floor
        w = room.window
        if w > 0.02:
            cc.save()
            K.clip_rect(cc, R.ROOM)
            top = R.sash_lift_y(room) + 13.0
            bass.fill_polys(cc, [bass.orient([(R.WINDOW[0], top), (R.WINDOW[0], R.WINDOW[3]), (473.0, R.FLOOR),
                                              (lerp(473.0, 233.0, (R.WINDOW[3] - top) / (R.WINDOW[3] - R.WINDOW[1])), R.FLOOR)],
                                             True)], STEEL, 0.18 * clamp(w * 1.5))
            cc.restore()
        cc.save()
        B.place(cc, 0.0, R.FLOOR, R.FIG_S)
        draw_her_cut(cc, st, p, R.room_bg(room))
        cc.restore()

    def over(cc):
        # out past the wall she is in front of the fire escape's ironwork (the ladder from 5):
        # a hair of the night round her parts her from it
        cc.save()
        K.clip_rect(cc, (R.WINDOW[2] + 1.0, 0.0, 2400.0, R.WINDOW[3] - 14.0))
        B.place(cc, 0.0, R.FLOOR, R.FIG_S)
        fig = her_upper()
        ang = skirt_angle(fig, st, p)
        d = 2.4 / (R.FIG_S * cam.z)
        for i in range(8):
            a = math.radians(45.0 * i)
            cc.save()
            cc.translate(d * math.cos(a), d * math.sin(a))
            _her_pass(cc, st, p, fig, ang, NIGHT, None)
            cc.restore()
        cc.restore()
        cc.save()
        K.clip_rect(cc, (R.WINDOW[2] + 1.0, 0.0, 2400.0, R.PLATFORM_Y - 10.0))
        B.place(cc, 0.0, R.FLOOR, R.FIG_S)
        draw_her_cut(cc, st, p, R.room_bg(room))
        cc.restore()
        # the sash goes home at the top: a small ripple off its rail
        K.ripple(cc, (1015.0, R.WINDOW[1] + 14.0), t, T_LIFT[1], lerp(STEEL, PAPER, 0.3), n=2, every=0.1,
                 life=0.34, r0=8.0, r1=54.0, width=3.6, seed=661)

    R.draw_stage(c, t, room, cam=cam, outside=outside, overlay=over)


# ================================================================ E: the low angle
# A real perspective, from the street up her fire escape. World units are section px: X across
# the street (her facade at X 380, the platforms out to 444), Y up from the street (Y = 1700 -
# section y), Z along the street toward the camera; the section's plane (through her window and
# the middle of the fire escape) is Z 0. Her building ends at a corner just past the fire escape,
# so above and beyond her is open night, and the moon. The ladders zig-zag between the platforms
# as in the section (from the wall end of one down to the far end of the next), at the far end
# of the platforms, behind her. She is a profile cut-out in the plane Z = Z_HER, laid in by the
# projection's local affine; the stage's climb keys go on into the step-out, so D and E are one
# performance.
GY = K.GROUND
FACE_X = K.HER_B.face                       # 380: her facade
WALL_T = K.WALL                             # 14
ROOF_Y = GY - K.HER_B.roof                  # 1060 (the coping 26 above, 6 proud)
CORNER_Z = -88.0                            # her building's corner, just past the fire escape
NEAR_Z = 1400.0                             # the facade runs on past the camera
ESC_X1 = K.ESCAPE_X[1]                      # 444: the platforms' outer edge
ESC_Z = 64.0                                # the platforms run Z -64 .. 64 (2:1, as in B)
WIN_Z = 30.0                                # the windows: Z -30 .. 30 (and the bays toward the camera)
WIN_BAYS = (0.0, 172.0, 344.0, 516.0)
LAD_Z = (-58.0, -30.0)                      # the ladders' stringers
Z_HER = 4.0                                 # her cut-out's plane
OPEN_Y = GY - R.to_section((0.0, R.WINDOW[3] - R.LIFT))[1]     # 729: under her raised sash
RIM_E = lerp(STEEL, PAPER, 0.22)            # the moon's edge on things
IRON_FAR = lerp(INK, STEEL, 0.28)           # the ironwork behind her (further off, a shade lighter)


def ptop(n):
    """The walking surface of her fire escape's platform at storey n (Y)."""
    return GY - K.level(n) + 4.0


def win_y(n):
    """(sill, head) of storey n's windows (Y)."""
    w = K.HER_B.window(n)
    return GY - w[3], GY - w[1]


def _v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _v_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _v_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _v_norm(a):
    L = math.sqrt(_v_dot(a, a)) or 1.0
    return (a[0] / L, a[1] / L, a[2] / L)


class Cam3:
    """A pinhole camera at C looking at T, rolled (deg), focal length f (frame px)."""

    NEAR = 8.0

    def __init__(self, C, T, roll=0.0, f=3000.0, cx=540.0, cy=960.0):
        w = _v_norm(_v_sub(T, C))
        r = _v_norm(_v_cross(w, (0.0, 1.0, 0.0)))
        u = _v_cross(r, w)
        a = math.radians(roll)
        ca, sa = math.cos(a), math.sin(a)
        self.r = tuple(ca * r[i] + sa * u[i] for i in range(3))
        self.u = tuple(-sa * r[i] + ca * u[i] for i in range(3))
        self.w = w
        self.C, self.f, self.cx, self.cy = C, f, cx, cy

    def cam(self, P):
        v = _v_sub(P, self.C)
        return (_v_dot(v, self.r), _v_dot(v, self.u), _v_dot(v, self.w))

    def scr(self, q):
        return (self.cx + self.f * q[0] / q[2], self.cy - self.f * q[1] / q[2])

    def p(self, P):
        return self.scr(self.cam(P))

    def poly(self, pts):
        """A world polygon on the frame, clipped at the near plane."""
        qs = [self.cam(P) for P in pts]
        out = []
        n = len(qs)
        for i in range(n):
            a, b = qs[i], qs[(i + 1) % n]
            ina, inb = a[2] >= self.NEAR, b[2] >= self.NEAR
            if ina:
                out.append(a)
            if ina != inb:
                s = (self.NEAR - a[2]) / (b[2] - a[2])
                out.append(tuple(a[j] + (b[j] - a[j]) * s for j in range(3)))
        return bass.orient([self.scr(q) for q in out], True) if len(out) >= 3 else None

    def bar(self, A, B, w):
        """A straight bar (iron) of world thickness w from A to B, as a band on the frame."""
        qa, qb = self.cam(A), self.cam(B)
        if qa[2] < self.NEAR or qb[2] < self.NEAR:
            return None
        a, b = self.scr(qa), self.scr(qb)
        wa, wb = 0.5 * self.f * w / qa[2], 0.5 * self.f * w / qb[2]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        return bass.orient([(a[0] + nx * wa, a[1] + ny * wa), (b[0] + nx * wb, b[1] + ny * wb),
                            (b[0] - nx * wb, b[1] - ny * wb), (a[0] - nx * wa, a[1] - ny * wa)], True)

    def ray(self, sx, sy):
        """The world direction through a frame point."""
        x, y = (sx - self.cx) / self.f, -(sy - self.cy) / self.f
        return _v_norm(tuple(self.r[i] * x + self.u[i] * y + self.w[i] for i in range(3)))


def _wcut(pts, seed, amp=0.5, step=20.0):
    """A planar world polygon re-cut by hand: its edges broken into short straight snips,
    nudged in the plane (fixed in the world, so the cut never boils as the camera moves)."""
    n = len(pts)
    nx = ny = nz = 0.0
    for i in range(n):                                       # Newell's normal
        a, b = pts[i], pts[(i + 1) % n]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    N = _v_norm((nx, ny, nz))
    out = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        e = _v_sub(b, a)
        L = math.sqrt(_v_dot(e, e))
        out.append(a)
        m = int(L / step)
        if m < 1:
            continue
        p = _v_norm(_v_cross(N, e))
        for j in range(1, m + 1):
            s = j / (m + 1.0) + 0.25 * bass._sn(seed, i, j, 3) / (m + 1.0)
            o = amp * bass._sn(seed, i, j, 4)
            out.append(tuple(a[q] + e[q] * s + p[q] * o for q in range(3)))
    return out


def _box_x(x, y0, y1, z0, z1):
    """A face in the plane X = x."""
    return [(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)]


def _box_y(y, x0, x1, z0, z1):
    """A face in the plane Y = y."""
    return [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]


def _box_z(z, x0, x1, y0, y1):
    """A face in the plane Z = z."""
    return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]


# --- the camera: on the street, low, up the fire escape; it tilts up with her as she rises
CAM_E = (((566.0, 40.0, 1050.0), (424.0, 694.0, 0.0), -3.0, 5000.0),
         ((566.0, 40.0, 1040.0), (426.0, 716.0, 0.0), -3.5, 6900.0))


def cam_e(t):
    u = k(t, T_LOW, T_LOOK_DOWN + 0.2 - T_LOW, "inout")
    (C0, T0, r0, f0), (C1, T1, r1, f1) = CAM_E
    C = tuple(lerp(a, b, u) for a, b in zip(C0, C1))
    T = tuple(lerp(a, b, u) for a, b in zip(T0, T1))
    return Cam3(C, T, lerp(r0, r1, u), lerp(f0, f1, u))


def moon_e():
    """The moon's direction (at infinity): behind her head and shoulders at the end."""
    cam = cam_e(10.0)
    return cam.ray(*MOON_AT)


MOON_AT = (650.0, 1010.0)     # where the moon sits on the frame at the end
MOON_R = 440.0


def draw_sky_e(c, cam):
    """The night, and the moon (at infinity, so it keeps its place as the camera tilts; it grows
    with the zoom). Returns (centre, radius) on the frame."""
    K.fill(c, NIGHT)
    d = moon_e()
    m = cam.p(tuple(cam.C[i] + 1e6 * d[i] for i in range(3)))
    r = MOON_R * cam.f / CAM_E[1][3]
    for rr, a in ((r * 1.9, 0.035), (r * 1.4, 0.05)):
        bass.fill_polys(c, [bass.ring_pts(m, rr, seed=61, n=120, amp=0.0)], PAPER, a)
    bass.fill_polys(c, [bass.ring_pts(m, r, seed=62, n=120, amp=0.6)], PAPER)
    return m, r


def _clip_off_moon(c, m, r):
    """Clip to everything but the moon's disc (frame coordinates)."""
    c.new_path()
    c.rectangle(-200.0, -200.0, 1480.0, 2320.0)
    bass.draw.poly(c, bass.ring_pts(m, r + 1.5, seed=62, n=120, amp=0.0))
    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    c.clip()
    c.set_fill_rule(cairo.FILL_RULE_WINDING)


def _lit(c, polys, m, color=INK, rim=RIM_E, off=2.6):
    """Fill polys in ink over copies of them nudged toward the moon: their moonward edges caught
    (except where they stand against the moon itself). m: (centre, radius) of the moon."""
    polys = [p for p in polys if p]
    if not polys:
        return
    m, mr = m
    c.save()
    _clip_off_moon(c, m, mr)
    for q in polys:
        cx = sum(v[0] for v in q) / len(q)
        cy = sum(v[1] for v in q) / len(q)
        d = (m[0] - cx, m[1] - cy)
        L = math.hypot(*d) or 1.0
        c.save()
        c.translate(off * d[0] / L, off * d[1] / L)
        bass.fill_polys(c, [q], rim)
        c.restore()
    c.restore()
    bass.fill_polys(c, polys, color)


@lru_cache(maxsize=1)
def facade_world():
    """Her building: the facade, the coping, in world polygons (cut once)."""
    face = _wcut([(FACE_X, -40.0, CORNER_Z), (FACE_X, ROOF_Y, CORNER_Z), (FACE_X, ROOF_Y, NEAR_Z),
                  (FACE_X, -40.0, NEAR_Z)], 1501, amp=0.0)
    coping = [_wcut(_box_x(FACE_X + 6.0, ROOF_Y - 2.0, ROOF_Y + 26.0, CORNER_Z - 6.0, NEAR_Z), 1502, amp=0.5),
              _box_y(ROOF_Y - 2.0, FACE_X, FACE_X + 6.0, CORNER_Z - 6.0, NEAR_Z)]
    return face, coping


def draw_window_e(c, cam, n, z, m, open_=False):
    """One window in the facade, seen from below at a slant: the far jamb's reveal, the head's
    soffit, the glass (the sky in it) with the sashes' rails, the sill."""
    y0, y1 = win_y(n)
    z0, z1 = z - WIN_Z, z + WIN_Z
    back = FACE_X - 8.0                       # the sashes, set back in the wall
    reveal = lerp(INK, DEEP, 0.55)
    hole = cam.poly(_box_x(FACE_X, y0, y1, z0, z1))
    if hole is None:
        return
    c.save()
    c.new_path()
    bass.draw.poly(c, hole)
    c.clip()
    bass.fill_polys(c, [hole], reveal)
    glass = cam.poly(_box_x(back, y0, y1, z0, z1))
    sky = lerp(SHUT, NIGHT, 0.45)
    if open_:
        top = OPEN_Y
        bass.fill_polys(c, [cam.poly(_box_x(back, top, y1, z0, z1))], sky)
        bass.fill_polys(c, [cam.poly(_box_x(FACE_X - WALL_T, y0, top, z0, z1))], DEEP)
        rails = [cam.poly(_box_x(back + 0.5, top, top + 5.0, z0, z1)),                # the raised sash's bottom rail
                 cam.poly(_box_x(back + 0.5, y1 - 6.0, y1 - 1.0, z0, z1))]
    else:
        bass.fill_polys(c, [glass], sky)
        mid = (y0 + y1) / 2.0
        rails = [cam.poly(_box_x(back + 0.5, mid - 2.5, mid + 2.5, z0, z1)),
                 cam.poly(_box_x(back + 0.5, y0, y0 + 5.0, z0, z1)),
                 cam.poly(_box_x(back + 0.5, y1 - 6.0, y1 - 1.0, z0, z1))]
    # a streak of the moon in the upper pane
    bass.fill_polys(c, [cam.poly([(back + 0.6, y1 - 12.0, z0 + 6.0), (back + 0.6, y1 - 30.0, z0 + 6.0),
                                  (back + 0.6, y1 - 46.0, z0 + 16.0), (back + 0.6, y1 - 28.0, z0 + 16.0)])],
                    lerp(STEEL, PAPER, 0.35), 0.5)
    bass.fill_polys(c, [r for r in rails if r], INK)
    bass.fill_polys(c, [cam.poly(_box_y(y1, back, FACE_X, z0, z1))], lerp(INK, DEEP, 0.3))    # the soffit
    c.restore()
    # the sill: proud of the wall, its underside toward us
    sill = [cam.poly(_box_y(y0 - 3.0, FACE_X, FACE_X + 6.0, z0 - 4.0, z1 + 4.0)),
            cam.poly(_box_x(FACE_X + 6.0, y0 - 3.0, y0 + 0.5, z0 - 4.0, z1 + 4.0))]
    _lit(c, sill, m)


def draw_facade_e(c, cam, m):
    face, coping = facade_world()
    _lit(c, [cam.poly(face)], m)
    for n in range(2, 6):
        for z in WIN_BAYS:
            draw_window_e(c, cam, n, z, m, open_=(n == K.HER_FLOOR and z == 0.0))
    _lit(c, [cam.poly(p) for p in coping], m)


def _railing(cam, n, part):
    """Bands for platform n's railing: part 'far' (the far end), 'front' (the outer side and the
    near end)."""
    y = ptop(n)
    top, mid = y + 42.0, y + 22.0
    x0, x1 = FACE_X, ESC_X1
    out = []
    if part == "far":
        z = -ESC_Z
        out.append(cam.bar((x0, top, z), (x1, top, z), 4.0))
        out.append(cam.bar((x0, mid, z), (x1, mid, z), 2.6))
        for j in range(1, 4):
            x = lerp(x0, x1, j / 4.0)
            out.append(cam.bar((x, y, z), (x, top, z), 2.2))
        out.append(cam.bar((x1, y - 4.0, z), (x1, top + 1.0, z), 4.0))
        return out
    out.append(cam.bar((x1, top, -ESC_Z), (x1, top, ESC_Z), 4.0))          # the top rail, out over the street
    out.append(cam.bar((x1, mid, -ESC_Z), (x1, mid, ESC_Z), 2.6))
    for j in range(1, 8):                                                   # the balusters
        z = lerp(-ESC_Z, ESC_Z, j / 8.0)
        out.append(cam.bar((x1, y, z), (x1, top, z), 2.2))
    for z in (0.0, ESC_Z):
        out.append(cam.bar((x1, y - 4.0, z), (x1, top + 1.0, z), 4.0))      # the posts
    z = ESC_Z
    out.append(cam.bar((x0, top, z), (x1, top, z), 4.0))                    # the near end
    out.append(cam.bar((x0, mid, z), (x1, mid, z), 2.6))
    for j in range(1, 4):
        x = lerp(x0, x1, j / 4.0)
        out.append(cam.bar((x, y, z), (x, top, z), 2.2))
    return out


def _floor(cam, n):
    """Platform n's grating seen from under it: the frame, the slats along it, the bearers and
    the brackets to the wall."""
    y = ptop(n)
    x0, x1 = FACE_X, ESC_X1
    out = [cam.poly(_box_x(x1, y - 8.0, y, -ESC_Z, ESC_Z)),                 # the outer channel
           cam.poly(_box_z(ESC_Z, x0, x1, y - 8.0, y)),                     # the near end
           cam.poly(_box_y(y - 8.0, x1 - 4.0, x1, -ESC_Z, ESC_Z)),
           cam.poly(_box_y(y - 8.0, x0, x1, ESC_Z - 4.0, ESC_Z)),
           cam.poly(_box_y(y - 8.0, x0, x1, -ESC_Z, -ESC_Z + 4.0))]
    for j in range(1, 7):                                                   # the slats
        x = lerp(x0, x1, j / 7.0)
        out.append(cam.bar((x, y - 2.0, -ESC_Z), (x, y - 2.0, ESC_Z), 3.0))
    for z in (-ESC_Z * 0.5, 0.0, ESC_Z * 0.5):                               # the bearers under them
        out.append(cam.bar((x0, y - 6.0, z), (x1, y - 6.0, z), 3.0))
    for z in (-ESC_Z + 6.0, ESC_Z - 6.0):                                   # the brackets
        out.append(cam.bar((x0, y - 62.0, z), (x1 - 3.0, y - 7.0, z), 3.4))
        out.append(cam.bar((x0, y - 66.0, z), (x0, y - 4.0, z), 3.0))
    return out


def _ladder(cam, n):
    """The ladder from platform n down to n-1 (the kit's zig-zag), at the far end."""
    (xa, ya), (xb, yb) = K.escape_ladder(n)
    A, B = (xa, GY - ya), (xb, GY - yb)
    out = []
    for z in LAD_Z:
        out.append(cam.bar((A[0], A[1] + 2.0, z), (B[0], B[1], z), 3.6))
    m = 9
    for j in range(1, m):
        u = j / float(m)
        x, y = lerp(A[0], B[0], u), lerp(A[1], B[1], u)
        out.append(cam.bar((x, y, LAD_Z[0]), (x, y, LAD_Z[1]), 2.6))
    return out


def her_e(t):
    return her_climb(t)


def stage_world(p):
    """A stage point (her plane) in the world."""
    s = R.to_section(p)
    return (s[0], GY - s[1], Z_HER)


def fig_world(p):
    """Her figure units (B.place at x 0 on the stage floor, FIG_S) in the world."""
    return stage_world((p[0] * R.FIG_S, R.FLOOR + p[1] * R.FIG_S))


def fig_matrix(cam, at):
    """The cairo matrix that lays her figure (units) into the frame around `at` (figure units):
    the projection's local affine there."""
    p0 = cam.p(fig_world(at))
    px = cam.p(fig_world((at[0] + 1.0, at[1])))
    py = cam.p(fig_world((at[0], at[1] + 1.0)))
    xx, yx = px[0] - p0[0], px[1] - p0[1]
    xy, yy = py[0] - p0[0], py[1] - p0[1]
    x0 = p0[0] - xx * at[0] - xy * at[1]
    y0 = p0[1] - yx * at[0] - yy * at[1]
    return cairo.Matrix(xx, yx, xy, yy, x0, y0)


def _clip_moon(c, m, r):
    c.new_path()
    bass.draw.poly(c, bass.ring_pts(m, r + 1.5, seed=62, n=120, amp=0.0))
    c.clip()


def draw_her_e(c, cam, t, m, mr):
    """Her, from the street: inside the room only through the opening (past both faces of the
    wall); outside the wall all of her. Against the night her moonward edge is caught; against
    the moon she is ink."""
    st, p = her_e(t)
    P = st["pelvis"]
    at = (P[0], P[1] + p.crouch)
    M = fig_matrix(cam, at)
    base = c.get_matrix()
    inv = cairo.Matrix(*M)
    inv.invert()
    pc = cam.p(fig_world(at))
    d = (m[0] - pc[0], m[1] - pc[1])
    L = math.hypot(*d) or 1.0
    rdx, rdy = inv.transform_distance(2.6 * d[0] / L, 2.6 * d[1] / L)
    fig = her_upper()
    ang = skirt_angle(fig, st, p)

    def under(clips, fn):
        c.save()
        for q in clips:
            c.new_path()
            bass.draw.poly(c, q)
            c.clip()
        fn()
        c.restore()

    y0, _ = win_y(K.HER_FLOOR)
    holes = [cam.poly(_box_x(FACE_X, y0, OPEN_Y, -WIN_Z, WIN_Z)),
             cam.poly(_box_x(FACE_X - WALL_T, y0, OPEN_Y, -WIN_Z, WIN_Z))]
    outside = cam.poly(_box_z(Z_HER, FACE_X, FACE_X + 600.0, -400.0, 2400.0))

    def inside_room():
        c.transform(M)
        _her_pass(c, st, p, fig, ang, INK, DEEP)

    if all(holes):
        under(holes, inside_room)
    if outside is None:
        return

    def off_moon():
        _clip_off_moon(c, m, mr)
        c.transform(M)
        c.save()
        c.translate(rdx, rdy)
        _her_pass(c, st, p, fig, ang, RIM_E, None)
        c.restore()
        _her_pass(c, st, p, fig, ang, INK, None)

    def on_moon():
        _clip_moon(c, m, mr)
        c.transform(M)
        _her_pass(c, st, p, fig, ang, INK, None)

    under([outside], off_moon)
    under([outside], on_moon)


def draw_e(c, t):
    cam = cam_e(t)
    m = draw_sky_e(c, cam)
    draw_facade_e(c, cam, m)
    # behind her (further off, a shade lighter): the platform over her, the ladder down from it,
    # the far end of hers
    _lit(c, _railing(cam, 5, "far") + _railing(cam, 5, "front") + _floor(cam, 5), m, color=IRON_FAR)
    _lit(c, _railing(cam, 4, "far"), m, color=IRON_FAR)
    _lit(c, _ladder(cam, 5), m, color=IRON_FAR)
    draw_her_e(c, cam, t, *m)
    _lit(c, _railing(cam, 4, "front") + _floor(cam, 4), m)
    _lit(c, _ladder(cam, 4), m)
    _lit(c, _railing(cam, 3, "far") + _railing(cam, 3, "front") + _floor(cam, 3), m)
    _lit(c, _ladder(cam, 3), m)
    _lit(c, _railing(cam, 2, "far") + _railing(cam, 2, "front") + _floor(cam, 2), m)


def motion_blur(t, T):
    return 1


def cues(T):
    """Sparse (the bible: heartbeat, breath, steps): her heart under it all, her breath in the
    dark, his heels on the street far below, the chain, the sash, the wind, the iron."""
    out = [Cue(0.0, "her heartbeat, low and close, felt more than heard (no music)", gain_db=-16, dur=T.duration,
               bpm0=72, bpm1=112, rise=(0.0, T_HOME)),
           Cue(T_BREATH[0], "her breath in the dark: shallow, held, let out", gain_db=-12,
               dur=T_BREATH[1] - T_BREATH[0]),
           Cue(T_DOOR, "far below across the street, his street door: the latch, a creak (a slab of light)",
               gain_db=-14),
           Cue(T_SHUT, "his door swings to behind him: a soft far thud", gain_db=-18)]
    out += [Cue(tf, "his heel on the street, far below (hard, on the beat)", gain_db=-12 if tf in T_STEPS else -15)
            for _, tf in footfalls_b()[:-1]]
    out += [Cue(T_STOP, "he stops: a last scuff of the sole", gain_db=-16),
            Cue(T_LOOK, "her breath catches (he looks up)", gain_db=-12),
            Cue(T_SLIDE[0] - 0.12, "the chain's links shiver as her hand brings the knob up", gain_db=-16),
            Cue(T_SLIDE[0], "the knob finds the slot: a small metal tick", gain_db=-14),
            Cue(T_SLIDE[0] + 0.04, "the chain slides along its track: a dry, trembling scrape", gain_db=-12,
                dur=T_HOME - T_SLIDE[0] - 0.04),
            Cue(T_HOME, "the chain seats: a click", gain_db=-10),
            Cue(T_LIFT[0], "the sash: it sticks (a wooden knock)", gain_db=-12),
            Cue(T_LIFT[0] + 0.16, "the sash grinds up in its track", gain_db=-10, dur=T_LIFT[1] - T_LIFT[0] - 0.16),
            Cue(T_LIFT[1], "the sash goes home at the top: a muffled bang", gain_db=-10),
            Cue(T_WIND, "the night comes in: wind, gusting (the curtain lifts), on into the low angle", gain_db=-14,
                dur=T.duration - T_WIND),
            Cue(T_KNEE - 0.04, "her knee on the sill: a soft knock; her breath, quick", gain_db=-16),
            Cue(T_PLANT[0], "iron creak: her weight comes onto the fire escape's grating", gain_db=-10),
            Cue(T_PLANT[1], "the grating rings faintly under her other foot", gain_db=-16),
            Cue(T_PLANT[2], "a step on the iron, careful", gain_db=-18),
            Cue(T_LOOK_DOWN, "she holds her breath (looking down; the heartbeat carries over into s07)", gain_db=-14,
                dur=T.duration - T_LOOK_DOWN)]
    for c in out:
        if "dur" in c:
            c["dur"] = round(c["dur"], 3)
    return sorted(out, key=lambda c: c["t"])
