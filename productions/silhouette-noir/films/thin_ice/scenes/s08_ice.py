"""s08 ICE (108-122): the crack; the break; under the ice the lantern sinks away; up to the hole; he
clings to an edge that keeps breaking.

  0.0-0.5   The page, close: his second step comes down on the black band and the crack bursts out
            round his boots, a jagged PAPER star (0.25, CRACK). Shake.
  0.5-1.0   Silence. Nothing moves but the lamp's flame; a ring of fine cracks creeps round him.
  1.0-2.0   The section, at the hole: the slab gives (1.08) into tilting plates and he drops through
            with the lantern (Dutch tilt); spray; his head goes under (1.8); the hat stays on the
            water.
  2.0-7.0   Under the ice: the black water, the ice above with the hole bright in it, moonlight
            slanting down. He sinks, the greatcoat billowing. The lantern slips from his hand (2.55)
            and sinks past him, turning, glowing, to the riverbed, where its light shrinks and goes
            out; the rifle slides off his back (3.7) and follows. Bubbles. He looks up (5.0): the
            hole; he kicks for it.
  7.0-9.0   The section: he bursts up through the hole (gasp), grabs the far edge; it breaks off
            (7.62); under; up again (8.2), he turns and grabs the near edge, by the white ice: it
            holds.
  9.0-11.0  CU, his profile at the edge: hat gone, hair plastered, breath clouds coming hard, his
            gloves clawing at ice that cracks under them; a piece breaks away (10.2).
  11.0-14.0 The page, pulling back: the black hole in the black band, the trail of prints running
            into it, his head and arms in it, his hat floating; at the bottom, in the reeds, two
            pairs of eyes open (12.4). Last frame: that view.
"""
import math

from engine.core import clamp, ease, hash01, lerp
from engine import bass
from engine.paperdoll import Pose
from engine.timing import Cue
from films.thin_ice import cast as C
from films.thin_ice import faces as F
from films.thin_ice import kit as K
from films.thin_ice import world as W
from films.thin_ice.scenes import _lib_dir as L

FILM_T0 = 108.0
T_STEP = 0.25                # his second step: the crack
T_SILENCE = (0.5, 1.0)
T_SECTION = 1.0
T_BREAK = 1.08               # the slab gives
T_UNDER_HEAD = 1.8           # his head goes under
T_UNDER = 2.0                # under the ice
T_LAMP_GO = 2.55             # the lantern slips from his hand
T_RIFLE_GO = 3.7             # the rifle slides off his back
T_LAMP_BED = 4.75            # the lantern settles on the riverbed
T_LOOK = 5.0                 # he looks up: the hole
T_KICK = 5.5                 # he kicks for it
T_BURST = 7.0                # up through the hole
T_GRAB1 = 7.45               # the far edge ...
T_GIVE = 7.62                # ... breaks off
T_UP2 = 8.2                  # up again
T_GRAB2 = 8.45               # the near edge holds
T_CU = 9.0
T_CHUNK = 10.2               # a piece of the edge breaks away under his glove
T_PAGE = 11.0
T_EYES = 12.4                # her eyes open in the reeds

STEP2 = (13.27, 11.02)       # where his second step lands (on the black band)
PRINT2 = (STEP2[0], STEP2[1], 2.0, "guard", -1, 0.6)
STAR = K.crack_tree(W.HOLE, 1.75, seed=83, branches=12, heading=None, depth=0, jag=0.3, segs=5)
PRINTS = W.prints_before("s08")


def _ring_arcs():
    """The fine cracks that creep round him during the silence: short jagged arcs (map metres)."""
    out = []
    for k in range(7):
        a0 = 6.283 * (k + 0.15 * K._sn(k, 71)) / 7.0
        pts = []
        for j in range(6):
            a = a0 + 0.55 * j / 5.0
            r = 0.82 + 0.06 * K._sn(k, j, 72)
            pts.append((W.HOLE[0] + r * math.cos(a), W.HOLE[1] + r * math.sin(a)))
        out.append(((tuple(pts), 0.0, 1.0),))
    return out


RING = _ring_arcs()


# ============================================================================ the page, close (0-1)
CAM_A = W.Plan(13.32, 10.1, 250.0)
CAM_A2 = W.Plan(13.3, 10.55, 290.0)


def _guard_top_pos(t):
    """His body's map point from above, and his stride phase (the second step, 0-0.25)."""
    u = ease("inout", clamp(t / T_STEP))
    return (lerp(13.5, 13.36, u), lerp(9.98, 10.68, u)), 0.25 + 0.25 * u


def _page_close(c, t):
    cam = W.plan_lerp(CAM_A, CAM_A2, ease("inout", clamp((t - T_SILENCE[0]) / 0.5)))
    g = clamp((t - T_STEP) / 0.18)
    star = [(STAR, ease("out3", g))] if t >= T_STEP else []
    prints = PRINTS + ((PRINT2,) if t >= T_STEP else ())
    W.draw_page(c, cam, FILM_T0 + t, prints=prints, holes=("stone",), band_cracks=star)
    if t >= T_STEP:
        # the star flashes as it bursts (a thicker, brighter pass over it for a beat)
        fl = 1.0 - clamp((t - T_STEP) / 0.2)
        if fl > 0.0:
            K.crack(c, STAR, ease("out3", g), K.PAPER, width=max(1.6, 0.05 * cam.ppm) * (1.0 + 1.2 * fl), xf=cam.px,
                    alpha=0.9)
        # a ring of cracks across the arms as it bursts, and in the silence it creeps on round him
        cr = 0.45 * ease("out3", clamp((t - T_STEP - 0.06) / 0.2)) + 0.55 * ease("inout", clamp((t - T_SILENCE[0]) / 0.5))
        if cr > 0.0:
            for k, tree in enumerate(RING):
                K.crack(c, tree, clamp(cr * 1.3 - 0.05 * k), K.PAPER, width=max(1.2, 0.025 * cam.ppm), xf=cam.px,
                        alpha=0.9)
    pos, ph = _guard_top_pos(t)
    lamp = (pos[0] + 0.32, pos[1] + 0.32)
    W.lamp_pool(c, cam, lamp, 1.5, 1.0, FILM_T0 + t, seed=3)
    C.top(c, "guard", cam.px(pos), cam.screen_heading(-6.0), cam.ppm, t, phase=ph,
          speed=0.6 if t < T_STEP else 0.0, lantern=1.0)


# ============================================================================ the section: the break (1-2)
CAM_B = W.Dio(10.95, -0.5, 320.0, eye=-0.42)
MOON_B = (820.0, 560.0)
G_STAND = (10.7, W.ICE_Z)                    # his root as he stands, the feet at 10.35 and 11.05
PLATES = ((10.105, 10.62, 10.105, 1), (10.62, 11.36, None, 0), (11.36, 11.995, 11.995, -1))


def _drop(t):
    """How far his pelvis has dropped below standing (m), from the break."""
    return L.track(t, [(T_BREAK, 0.0), (1.2, 0.12, "in"), (1.3, 0.36, "in"), (1.42, 0.82, "linear"),
                       (1.56, 1.32, "linear"), (1.72, 1.78, "out"), (1.88, 2.06, "out"), (2.0, 2.22, "out")])


def _plate_angle(i, t):
    """Each plate's tilt (degrees, + clockwise on screen) as the slab gives and they float back."""
    u = t - T_BREAK
    if u <= 0.0:
        return 0.0
    if i == 0:
        a = 38.0 * ease("out3", clamp(u / 0.22))
        return a - 26.0 * ease("inout", clamp((u - 0.45) / 0.5)) + 3.0 * math.sin(u * 7.0) * clamp((u - 0.5) / 0.4)
    if i == 2:
        a = -44.0 * ease("out3", clamp(u / 0.25))
        return a + 31.0 * ease("inout", clamp((u - 0.5) / 0.5)) - 3.0 * math.sin(u * 6.0 + 1.0) * clamp((u - 0.55) / 0.4)
    return 70.0 * ease("in", clamp(u / 0.3)) + 40.0 * ease("out", clamp((u - 0.3) / 0.5))


def _plates(c, cam, t, d=0.0):
    """The broken plates in the hole (section): thin slabs tilting on their outer edges; the middle
    one goes down under his boots and comes up on its side."""
    th = W.THIN_T
    for i, (a, b, hinge, _) in enumerate(PLATES):
        ang = math.radians(_plate_angle(i, t))
        if hinge is None:
            sink = 0.9 * ease("inout", clamp((t - T_BREAK) / 0.35)) - 0.75 * ease("inout", clamp((t - 1.5) / 0.45))
            hn, hz = 0.5 * (a + b), W.ICE_Z - th * 0.5 - sink
            base = [(a - hn, th * 0.5), (b - hn, th * 0.5), (b - hn, -th * 0.5), (a - hn, -th * 0.5)]
        else:
            hn, hz = hinge, W.ICE_Z
            base = [(a - hn, 0.0), (b - hn, 0.0), (b - hn, -th), (a - hn, -th)]
        # clockwise on screen is clockwise in (n, -z): turn in (n, z) by -ang
        ca, sa = math.cos(-ang), math.sin(-ang)
        pts = [cam.px(hn + x * ca - y * sa, hz + x * sa + y * ca, d) for x, y in base]
        K.poly(c, pts, W.THIN)
        K.band(c, pts[:2], lerp(W.THIN, K.PAPER, 0.35), max(1.2, 0.01 * cam.ppm), seed=40 + i)


def _section_cracks(c, cam, t):
    """Before it gives: the star's cracks on the ice behind the cut, and through the slab's face."""
    hy = cam.px(0.0, W.ICE_Z)[1]
    c.save()
    c.new_path()
    c.rectangle(-100.0, -100.0, 1300.0, hy + 100.0)
    c.clip()
    K.crack(c, STAR, 1.0, K.PAPER, width=max(1.5, 0.018 * cam.ppm),
            xf=lambda p: cam.px(p[1], W.ICE_Z, W.SECTION_X - p[0]), alpha=0.85)
    c.restore()
    for k, n in enumerate((10.25, 10.6, 11.3, 11.75)):
        a, b = cam.px(n, W.ICE_Z), cam.px(n + 0.04 * K._sn(k, 3), W.ICE_Z - W.THIN_T)
        K.band(c, [a, ((a[0] + b[0]) / 2 + 4.0 * K._sn(k, 4), (a[1] + b[1]) / 2), b], K.PAPER, 2.5, seed=k)


def _guard_fall_pose(t):
    """Startled, then grabbing at air as he goes down, the lantern flung up."""
    u = clamp((t - T_BREAK) / 0.25)
    sp = 70.0 * ease("out3", u)
    flail = 12.0 * math.sin((t - T_BREAK) * 14.0) * clamp((t - 1.3) / 0.2)
    arms = {"near": ("ang", lerp(30.0, 150.0, ease("out3", u)) + flail, lerp(40.0, 20.0, u)),
            "far": ("ang", lerp(-20.0, 160.0, ease("out3", clamp(u * 1.2))) - flail, lerp(30.0, 30.0, u))}
    head = lerp(-24.0, 22.0, ease("out3", u))
    return Pose(lean=lerp(4.0, -6.0, u), head=head, arms=arms,
                hold={"near": C.hold_lantern(t, 1.0, swing=lerp(0.0, -sp, u))}, springs=dict(C.REST),
                eye=1.0, gaze=0.0)


def _section_break(c, t):
    tilt = 7.0 * ease("out3", clamp((t - T_BREAK) / 0.3))
    sx, sy = L.shake(t, T_BREAK, amp=12.0, dur=0.3)
    with L.tilted(c, tilt):
        c.translate(sx, sy)
        cam = CAM_B
        broke = t >= T_BREAK
        W.draw_river(c, cam, FILM_T0 + t, holes=("stone", "guard_small") if broke else ("stone",), moon_at=MOON_B)
        if not broke:
            _section_cracks(c, cam, t)
        dz = _drop(t)
        m = C.M_PER_UNIT["guard"]
        if not broke:
            st = L.stance("guard", 0.7)
            pose = Pose(lean=4.0, head=-24.0, arms={"near": ("ang", 30.0, 40.0), "far": ("ang", -20.0, 30.0)},
                        hold={"near": C.hold_lantern(t, 1.0)}, springs=dict(C.REST))
            j = L.figure(c, cam, "guard", st, pose, G_STAND[0], G_STAND[1], 0.0, 1,
                         under=lambda c_, j_: K.glow(c_, j_["flame"], 1.0 * cam.ppm, 0.8, FILM_T0 + t, seed=4,
                                                     ry=0.55 * cam.ppm) if "flame" in j_ else None)
        else:
            k = clamp((t - T_BREAK) / 0.3)
            st = L.free_state("guard", (lerp(0.35, 0.12, k), lerp(0.74, 0.7, k)), (lerp(-0.35, -0.16, k), lerp(0.74, 0.68, k)),
                              pitch=(-20.0 * k, -35.0 * k))
            pose = _guard_fall_pose(t)
            zp = W.ICE_Z + 0.75 - dz
            glow = 0.75 if t < T_UNDER_HEAD else 0.5
            j = L.figure(c, cam, "guard", st, pose, G_STAND[0] + 0.12 * k, zp, 0.0, 1,
                         under=lambda c_, j_: K.glow(c_, j_["flame"], 0.85 * cam.ppm, glow, FILM_T0 + t, seed=4)
                         if "flame" in j_ else None)
            under = t >= T_UNDER_HEAD
            # the river over the part of him that is under
            L.wash(c, cam, 10.105, 11.995, alpha=0.62)
            _plates(c, cam, t)
            L.waterline(c, cam, 10.105, 11.995, FILM_T0 + t, seed=3, amp=1.0 + 2.0 * clamp(1.0 - (t - 1.3) / 0.6))
            L.spray(c, cam.px(10.8, W.ICE_Z), t, 1.26, cam.ppm, n=22, seed=5, power=1.2)
            L.spray(c, cam.px(11.0, W.ICE_Z), t, 1.42, cam.ppm, n=26, seed=6, power=1.5, spread=1.3)
            if t >= 1.6:
                L.spray(c, cam.px(10.9, W.ICE_Z), t, 1.76, cam.ppm, n=12, seed=7, power=0.7)
            # the hat stays on the water when his head goes under
            if under:
                bob = 0.015 * math.sin((t - T_UNDER_HEAD) * 6.0)
                L.prop(c, "hat", cam.px(11.15 + 0.2 * (t - T_UNDER_HEAD), W.ICE_Z + 0.07 + bob), C.scale("guard", cam.ppm),
                       -15.0 + 8.0 * math.sin(t * 3.0), rim=L.RIM, rim_w=2.0)
                L.bubbles(c, lambda tb: cam.px(10.95, W.ICE_Z - 0.4), t, T_UNDER_HEAD - 0.1, 2.0, cam.px(0, W.ICE_Z)[1],
                          cam.ppm, rate=26.0, seed=8, rise=1.4, size=1.4, spread=0.25)


# ============================================================================ under the ice (2-7)
# A composed set in metres (the hole drawn smaller and the river deeper than the map's): the ice
# above with the hole of light in it, the black water, the riverbed.
U_HOLE = (10.55, 11.55)        # the hole's span (u)
U_CEIL = -0.99                 # the ice's underside
U_BED = -5.15                  # the riverbed


def _cam_u(t):
    return L.dio_at(t, [(T_UNDER, W.Dio(11.05, -2.95, 333.0, eye=0.0)), (3.4, W.Dio(11.0, -3.15, 330.0, eye=0.0)),
                        (4.8, W.Dio(10.95, -3.35, 326.0, eye=0.0)), (5.6, W.Dio(11.0, -3.05, 330.0, eye=0.0)),
                        (7.0, W.Dio(11.05, -2.75, 336.0, eye=0.0))])


def _bed_z(u):
    return U_BED + 0.12 * math.sin(u * 2.1) + 0.06 * math.sin(u * 5.3 + 1.0)


def _under_set(c, cam, t):
    K.fill(c, K.WATER)
    # the riverbed and its stones
    us = [cam.u_at(-60.0 + 1200.0 * i / 60.0) for i in range(61)]
    K.poly(c, [cam.px(u, _bed_z(u)) for u in us] + [(1140.0, 2000.0), (-60.0, 2000.0)], K.INK)
    for i in range(26):
        u = cam.u_at(-40.0 + 1160.0 * hash01(i, 301))
        r = (0.06 + 0.12 * hash01(i, 302)) * cam.ppm
        p = cam.px(u, _bed_z(u))
        K.ellipse(c, (p[0], p[1] + r * 0.25), r * 1.3, r * 0.7, lerp(K.INK, K.WATER, 0.45 + 0.2 * hash01(i, 303)))
    # the ice above: thick white ice to the left of the band, the band's thin black ice, and above
    # the ice the night, seen only through the hole
    top = cam.px(0.0, U_CEIL)[1]
    K.poly(c, [(-60.0, -60.0), (1140.0, -60.0), (1140.0, top), (-60.0, top)], lerp(W.THIN, K.WATER, 0.25))
    xw = cam.px(9.99, 0.0)[0]
    if xw > -60.0:
        K.poly(c, [(-60.0, -60.0), (xw, -60.0), (xw - 10.0, top + 0.28 * cam.ppm), (-60.0, top + 0.3 * cam.ppm)],
               lerp(W.ICE, K.WATER, 0.45))
    # the underside's ripples of frozen ice
    for i in range(14):
        u = cam.u_at(-60.0 + 90.0 * i)
        a, b = cam.px(u, U_CEIL), cam.px(u + 0.22, U_CEIL)
        K.ellipse(c, ((a[0] + b[0]) / 2, a[1]), (b[0] - a[0]) / 2, 0.025 * cam.ppm, lerp(W.THIN, K.WATER, 0.1))
    # the hole of light: through its broken edges the night sky and the moon
    hl, hr = cam.px(U_HOLE[0], U_CEIL), cam.px(U_HOLE[1], U_CEIL)
    hole = []
    for i in range(9):                                   # the left edge, broken, up out of the frame
        y = lerp(hl[1], -80.0, i / 8.0)
        hole.append((hl[0] + 26.0 * K._sn(i, 311) + (14.0 if i % 2 else -10.0), y))
    for i in range(9):                                   # the right edge, down
        y = lerp(-80.0, hr[1], i / 8.0)
        hole.append((hr[0] + 26.0 * K._sn(i, 312) + (12.0 if i % 2 else -12.0), y))
    for i in range(1, 12):                               # the water's surface, seen from under it
        hole.append((lerp(hr[0], hl[0], i / 12.0), hr[1] + 6.0 * math.sin(i * 1.7 + t * 4.0)))
    K.poly(c, hole, lerp(K.NIGHT, W.ICE, 0.55))
    c.save()
    c.new_path()
    bass.draw.poly(c, hole)
    c.clip()
    K.moon(c, (hl[0] + 0.62 * (hr[0] - hl[0]), hl[1] - 0.95 * cam.ppm), r=0.42 * cam.ppm)
    c.restore()
    K.band(c, [(hl[0] - 30.0, hl[1]), (hr[0] + 30.0, hr[1])], K.PAPER, 3.0, seed=5, alpha=0.6)
    K.glow(c, ((hl[0] + hr[0]) / 2, hl[1] + 20.0), 1.1 * cam.ppm, 0.45, FILM_T0 + t, color=K.PAPER, ry=0.35 * cam.ppm,
           steps=3, seed=9)
    L.shafts(c, hl, hr, 4.6 * cam.ppm, t, strength=1.6, seed=2)
    return hl, hr


def _sink(t):
    """His pelvis (u, z) and the body's roll as he sinks, hangs, looks up and kicks for the hole."""
    u = L.track(t, [(T_UNDER, 11.0), (3.5, 10.85), (5.0, 10.8), (5.5, 10.85), (7.0, 11.02)])
    z = L.track(t, [(T_UNDER, -1.55), (2.6, -2.25, "out"), (3.6, -2.7, "out"), (5.0, -2.85), (5.5, -2.8),
                    (6.3, -2.1, "inout"), (7.0, -1.35, "in")])
    roll = L.track(t, [(T_UNDER, 0.0), (3.0, -14.0), (4.5, -24.0), (5.2, -10.0), (5.8, 4.0), (7.0, 0.0)])
    return (u, z), roll


def _sink_pose(t):
    """Arms up and drifting, then a slow struggle; looking up; the breaststroke kick for the hole."""
    if t < T_KICK:
        w = math.sin(t * 2.2)
        k = clamp((t - T_UNDER) / 0.6)
        near = ("ang", lerp(165.0, 120.0, k) + 14.0 * w, 30.0 + 10.0 * math.sin(t * 2.9))
        far = ("ang", lerp(170.0, 135.0, k) - 12.0 * w, 26.0 + 8.0 * math.sin(t * 2.5 + 1.0))
        head = L.track(t, [(T_UNDER, 10.0), (3.0, -10.0), (T_LOOK, -14.0), (T_LOOK + 0.35, 38.0, "out")])
    else:
        q = ((t - T_KICK) / 0.75) % 1.0          # one stroke every 0.75 s
        reach = math.cos(2.0 * math.pi * q)
        near = ("ang", 115.0 + 60.0 * reach, 20.0 + 30.0 * max(0.0, -reach))
        far = ("ang", 120.0 + 55.0 * reach, 24.0 + 26.0 * max(0.0, -reach))
        head = 34.0
    hold = {"near": C.hold_lantern(t, 1.0, swing=-40.0)} if t < T_LAMP_GO else {}
    return Pose(lean=-4.0, head=head, arms={"near": near, "far": far}, hold=hold, springs=dict(C.REST), eye=1.0)


def _sink_feet(t):
    if t < T_KICK:
        w = math.sin(t * 1.7)
        return (0.07 + 0.04 * w, 0.73), (-0.09 - 0.03 * w, 0.71), (-62.0, -70.0)
    q = ((t - T_KICK) / 0.75) % 1.0
    kick = math.sin(2.0 * math.pi * q)
    return (0.04 + 0.12 * kick, 0.7 - 0.05 * abs(kick)), (-0.04 - 0.12 * kick, 0.7 - 0.05 * abs(kick)), (-70.0, -70.0)


def _billow(c, pivot, s, t, k, roll, facing=1):
    """The greatcoat's skirt floating up round his legs like a bell (k 0..1), wavering at the hem;
    drawn in the body's turned frame (figure units from the pelvis, x forward, y down)."""
    w1, w2 = math.sin(t * 2.4), math.sin(t * 3.1 + 1.0)
    fx, fy = 70.0 + 95.0 * k, 178.0 - 125.0 * k + 10.0 * w1
    bx, by = -66.0 - 95.0 * k, 178.0 - 115.0 * k - 10.0 * w2
    pts = [(-64.0, -36.0), (68.0, -36.0), (lerp(70.0, 128.0, k), lerp(70.0, 2.0, k)), (fx, fy)]
    for i in range(1, 6):                                   # the hem, waving
        u = i / 6.0
        pts.append((lerp(fx, bx, u), lerp(fy, by, u) + 22.0 * math.sin(u * 9.0 + t * 3.0) * k))
    pts += [(bx, by), (lerp(-66.0, -124.0, k), lerp(70.0, 8.0, k))]
    out = [L.turn_pt((pivot[0] + facing * x * s, pivot[1] + y * s), pivot, roll) for x, y in pts]
    K.poly(c, [(x + L.LIGHT[0] * 2.5, y + L.LIGHT[1] * 2.5) for x, y in out], L.RIM_WET)
    K.poly(c, out, K.INK)


def _lamp_path(t, home):
    """The lantern after it slips: down past him, turning, to the riverbed; (point, swing)."""
    u = t - T_LAMP_GO
    p0 = home
    bed = (10.55, U_BED + 0.12)
    k = clamp(u / (T_LAMP_BED - T_LAMP_GO))
    e = k * k * (1.6 - 0.6 * k)
    x = lerp(p0[0], bed[0], e) + 0.12 * math.sin(u * 2.6)
    z = lerp(p0[1], bed[1], e)
    swing = -40.0 + 210.0 * ease("inout", k) + 25.0 * math.sin(u * 3.1)
    if t >= T_LAMP_BED:
        swing = 170.0 + 85.0 * ease("out3", clamp((t - T_LAMP_BED) / 0.4))     # it tips over on the stones
    return (x, z), swing


def _rifle_path(t, home, home_ang):
    u = t - T_RIFLE_GO
    bed = (11.45, U_BED + 0.1)
    k = clamp(u / 1.35)
    e = k * k
    p = (lerp(home[0], bed[0], e) + 0.08 * math.sin(u * 2.0), lerp(home[1], bed[1], e))
    ang = home_ang + lerp(0.0, 64.0, ease("inout", k)) + (24.0 * ease("out3", clamp((u - 1.35) / 0.3)) if u > 1.35 else 0.0)
    return p, ang


def _body_at(cam, t):
    """His state, pose, root (frame px) and roll at t, under the ice."""
    pos, roll = _sink(t)
    near, far, pitch = _sink_feet(t)
    return L.free_state("guard_wet", near, far, pitch, skirt=False), _sink_pose(t), cam.px(*pos), roll


def _under(c, t):
    cam = _cam_u(t)
    hl, hr = _under_set(c, cam, t)
    ceil_y = hl[1]
    s = C.scale("guard", cam.ppm)
    pos, roll = _sink(t)
    near, far, pitch = _sink_feet(t)
    st = L.free_state("guard_wet", near, far, pitch, skirt=False)
    pose = _sink_pose(t)
    at = cam.px(*pos)
    # the hat floating on the water in the hole, a dark shape against the light
    hb = 0.02 * math.sin(t * 4.0)
    L.prop(c, "hat", cam.px(11.25 + 0.06 * (t - T_UNDER), U_CEIL + 0.12 + hb), s * 0.95, 160.0 + 6.0 * math.sin(t * 2.0))
    # the rifle: on his back until it slides off
    r_home, r_ang = L.prop_home("rifle", st, pose, at, s, 1, roll, (at[0], at[1]))
    if t >= T_RIFLE_GO:
        # where it was on his back when it came off, then down to the riverbed
        st0, pose0, at0, roll0 = _body_at(cam, T_RIFLE_GO)
        hp, ha = L.prop_home("rifle", st0, pose0, at0, s, 1, roll0, at0)
        rp, ra = _rifle_path(t, (cam.u_at(hp[0]), cam.z_at(hp[1])), ha)
        L.prop(c, "rifle", cam.px(*rp), s, ra, rim=L.RIM_WET, rim_w=2.5)
    # the lantern, from his hand when it slipped, sinking past him
    lamp = None
    if t >= T_LAMP_GO:
        st0, pose0, at0, roll0 = _body_at(cam, T_LAMP_GO)
        c.push_group()
        j0 = L.figure_at(c, "guard_wet", st0, pose0, at0, s, 1, roll0)
        c.pop_group()
        hand = j0.get("hand_near", at0)
        lp, sw = _lamp_path(t, (cam.u_at(hand[0]), cam.z_at(hand[1])))
        lamp = (cam.px(*lp), sw)
        dim = 1.0 - ease("inout", clamp((t - T_LAMP_BED - 0.2) / 1.4))
        size = lerp(1.25, 0.5, clamp((t - T_LAMP_GO) / (T_LAMP_BED - T_LAMP_GO + 0.8)))
        if dim > 0.0:
            K.glow(c, lamp[0], 0.75 * size * cam.ppm * (0.5 + 0.5 * dim), 0.75 * dim, FILM_T0 + t, seed=4)
            if t >= T_LAMP_BED:
                bp = cam.px(lp[0], U_BED + 0.05)
                K.glow(c, bp, 0.9 * cam.ppm * dim, 0.9 * dim, FILM_T0 + t, ry=0.18 * cam.ppm, seed=5)
    # him
    k_bill = clamp((t - T_UNDER) / 0.8) * (1.0 - 0.55 * clamp((t - T_KICK) / 0.6))
    _billow(c, at, s, t, k_bill, roll)
    j = L.figure_at(c, "guard_wet", st, pose, at, s, 1, roll, rim=L.RIM_WET)
    if t < T_RIFLE_GO:
        L.prop(c, "rifle", r_home, s, r_ang, rim=L.RIM_WET, rim_w=2.5)
    if t < T_LAMP_GO and j.get("flame") is not None:
        K.glow(c, j["flame"], 0.8 * cam.ppm, 0.7, FILM_T0 + t, seed=4)
    if lamp is not None:
        p, sw = lamp
        lit = 1.0 - ease("inout", clamp((t - T_LAMP_BED - 0.2) / 1.4))
        K.lantern(c, p, s=1.15 * s, lit=lit, swing=sw, t=FILM_T0 + t)
    # bubbles: the air coming out of his coat as he goes in, a held breath leaking, the breath he
    # lets go when he sees the hole, the stream as he swims up
    mouth = j.get("mouth", at)
    L.bubbles(c, lambda tb: cam.px(*_sink(tb)[0]), t, T_UNDER, 2.5, ceil_y, cam.ppm, rate=30.0, seed=11, rise=1.3,
              size=1.3, spread=0.2)
    for k0 in (2.9, 3.6, 4.3):
        L.bubbles(c, lambda tb: mouth, t, k0, k0 + 0.15, ceil_y, cam.ppm, rate=24.0, seed=int(k0 * 10), rise=0.9)
    L.bubbles(c, lambda tb: mouth, t, T_LOOK + 0.1, T_LOOK + 0.45, ceil_y, cam.ppm, rate=40.0, seed=13, rise=1.1, size=1.4)
    L.bubbles(c, lambda tb: cam.px(_sink(tb)[0][0], _sink(tb)[0][1] + 0.9), t, T_KICK, 7.0, ceil_y, cam.ppm, rate=14.0,
              seed=14, rise=1.0)
    if t >= T_LAMP_GO and lamp is not None and t < T_LAMP_BED + 0.6:
        L.bubbles(c, lambda tb: lamp[0], t, T_LAMP_GO, T_LAMP_BED + 0.3, ceil_y, cam.ppm, rate=6.0, seed=15, rise=0.8,
                  size=0.8)
    # he sees the hole
    if t >= T_LOOK + 0.15:
        eye = j.get("eye", at)
        K.sight_line(c, eye, ((hl[0] + hr[0]) / 2, ceil_y + 30.0), t, T_LOOK + 0.15, color=K.PAPER, dur=0.4, off=T_KICK + 0.4)




# ============================================================================ the section: up, and clinging (7-9)
CAM_D = W.Dio(11.15, -1.0, 400.0, eye=-0.5)
MOON_D = (760.0, 330.0)
EDGE_N, EDGE_S = 11.995, 10.105          # the hole's far and near edges in the cut (it breaks to 12.496)


def _cling(t):
    """His pelvis (u, z), facing, roll, and the arms' targets (n, z) or None, through the burst,
    the far edge breaking, under, up and the near edge."""
    zs = W.ICE_Z
    z = L.track(t, [(T_BURST, -1.75), (7.12, -1.28, "out"), (7.45, -1.22), (T_GIVE, -1.25), (7.75, -1.75, "in"),
                    (8.0, -2.0, "out"), (T_UP2, -1.7), (8.32, -1.24, "out"), (T_GRAB2, -1.2), (9.0, -1.18)])
    if t < 8.08:
        u = L.track(t, [(T_BURST, 11.05), (7.45, 11.35), (8.0, 11.4)])
        return (u, z), 1, L.track(t, [(T_BURST, 0.0), (7.45, 14.0), (T_GIVE, 18.0), (7.8, 30.0), (8.0, 0.0)])
    u = L.track(t, [(8.08, 11.2), (T_GRAB2, 10.62), (9.0, 10.58)])
    return (u, z), -1, L.track(t, [(8.08, 0.0), (T_GRAB2, 16.0), (9.0, 12.0)])


def _edge_piece(t):
    """The far edge's broken piece (n 11.995-12.496): tilting down on its far end, sinking, floating
    back up on its side; returns its polygon in (n, z) or None while it is whole."""
    if t < T_GIVE:
        return None
    u = t - T_GIVE
    ang = math.radians(-(48.0 * ease("out3", clamp(u / 0.2)) - 30.0 * ease("inout", clamp((u - 0.4) / 0.5))))
    sink = 0.25 * ease("out", clamp(u / 0.25)) - 0.2 * ease("inout", clamp((u - 0.4) / 0.6))
    hn, hz = 12.496, W.ICE_Z - sink
    base = [(EDGE_N - hn, 0.0), (0.0, 0.0), (0.0, -W.THIN_T), (EDGE_N - hn, -W.THIN_T)]
    ca, sa = math.cos(ang), math.sin(ang)
    return [(hn + x * ca - y * sa, hz + x * sa + y * ca) for x, y in base]


def _cling_section(c, t):
    cam = CAM_D
    broke = t >= T_GIVE
    W.draw_river(c, cam, FILM_T0 + t, holes=("stone", "guard" if broke else "guard_small"), moon_at=MOON_D)
    if broke:
        # the cut face of the big hole leaves the piece's span open: fill it with water to the
        # surface, then lay the piece on it
        K.poly(c, L.water_poly(cam, EDGE_N, 12.496), K.WATER)
    # floating shards from the break
    for k, (n, w, a0) in enumerate(((10.5, 0.22, 12.0), (11.65, 0.3, -18.0))):
        bob = 0.01 * math.sin(t * 5.0 + k)
        ang = math.radians(a0 + 6.0 * math.sin(t * 3.0 + k))
        ca, sa = math.cos(ang), math.sin(ang)
        base = [(-w / 2, 0.02), (w / 2, 0.02), (w / 2, -0.06), (-w / 2, -0.06)]
        K.poly(c, [cam.px(n + x * ca - y * sa, W.ICE_Z + bob + x * sa + y * ca) for x, y in base], W.THIN)
    piece = _edge_piece(t)
    (u, z), facing, roll = _cling(t)
    s = C.scale("guard", cam.ppm)
    # arms: thrashing, then reaching for the far edge, gripping it, going down with it; up again,
    # thrashing, and the near edge
    if t < 8.08:
        k = clamp((t - 7.12) / 0.33)
        tgt = [(EDGE_N + 0.03, W.ICE_Z + 0.03), (EDGE_N + 0.18, W.ICE_Z + 0.03)]
        if piece is not None:
            tgt = [piece[0], ((piece[0][0] + piece[1][0]) / 2, (piece[0][1] + piece[1][1]) / 2)]
    else:
        k = clamp((t - 8.26) / 0.19)
        tgt = [(EDGE_S - 0.05, W.ICE_Z + 0.03), (EDGE_S - 0.16, W.ICE_Z + 0.03)]
    k = ease("inout", k)
    st = L.free_state("guard_wet", (0.15 + 0.1 * math.sin(t * 6.0), 0.6), (-0.1 - 0.1 * math.sin(t * 6.0), 0.58),
                      (-50.0, -50.0), skirt=True)
    pv = cam.px(u, z)
    F = C.fig("guard_wet")
    reach = 0.86 * (F.upper + F.fore)
    arms = {}
    for side, tg in zip(("near", "far"), tgt):
        # the 'ik' target is in figure units from the root (here the pelvis), x to screen right
        p = L.turn_pt(cam.px(*tg), pv, -roll)           # into the body's turned frame
        grab = ((p[0] - pv[0]) / s, (p[1] - pv[1]) / s)
        # the thrash: the near hand clawing up and forward, the far one beating out to the side
        a0, amp, ph = (140.0, 38.0, 0.0) if side == "near" else (88.0, 46.0, 2.6)
        a = math.radians(a0 + amp * math.sin(t * 8.5 + ph))
        flail = (facing * (F.shoulder[0] + math.sin(a) * reach), F.shoulder[1] + math.cos(a) * reach)
        arms[side] = ("ik", (lerp(flail[0], grab[0], k), lerp(flail[1], grab[1], k)))
    pose = Pose(lean=8.0, head=L.track(t, [(T_BURST, 30.0), (7.3, 10.0), (8.25, 30.0), (8.5, 5.0)]), arms=arms,
                springs=dict(C.REST), eye=1.0)
    j = L.figure(c, cam, "guard_wet", st, pose, u, z, 0.0, facing, roll, rim=L.RIM)
    n1 = 12.496 if broke else EDGE_N
    L.wash(c, cam, EDGE_S, n1, alpha=0.62)
    if piece is not None:
        pts = [cam.px(*p) for p in piece]
        K.poly(c, pts, W.THIN)
        K.band(c, pts[:2], lerp(W.THIN, K.PAPER, 0.35), 2.0, seed=51)
    L.waterline(c, cam, EDGE_S, n1, FILM_T0 + t, seed=5, amp=2.5)
    for t0, n, pw in ((T_BURST, 11.1, 1.6), (T_GIVE + 0.05, 11.7, 1.3), (T_UP2 + 0.05, 11.1, 1.4)):
        L.spray(c, cam.px(n, W.ICE_Z), t, t0, cam.ppm, n=24, seed=int(t0 * 10), power=pw, spread=1.2)
    # his breath: a gasp as he comes up, then ragged
    for t0 in (T_BURST + 0.08, T_UP2 + 0.1):
        if t0 <= t < t0 + 1.0:
            K.breath(c, j["mouth"], t, rate=1.0, facing=facing, s=1.6 * s / 0.5 * 0.5, phase=t0, strength=1.0, seed=7)
    if t >= T_GRAB2 + 0.1:
        K.breath(c, j["mouth"], t, pant=2.2, facing=facing, s=1.4, phase=T_GRAB2, strength=0.9, seed=8)
    # under: bubbles
    L.bubbles(c, lambda tb: cam.px(11.45, -1.6), t, T_GIVE + 0.1, T_UP2, cam.px(0, W.ICE_Z)[1], cam.ppm, rate=30.0,
              seed=17, rise=1.3, size=1.2, spread=0.2)
    # the hat, drifting on the water
    L.prop(c, "hat", cam.px(11.75 + 0.12 * (t - T_BURST), W.ICE_Z + 0.06 + 0.012 * math.sin(t * 5.0)), s * 0.95,
           -20.0 + 6.0 * math.sin(t * 2.2), rim=L.RIM, rim_w=2.0)


# ============================================================================ CU: his face at the edge (9-11)
CU_WATER = 1062.0                  # the water's surface in the close-up (frame y)
CU_ICE_TOP = 992.0                 # the far side of the ice's top surface, seen a little from above
CU_GUARD = (720.0, 1330.0)         # his face's anchor (the collar), facing left
CU_S = 1.1


SLAB_TOP = (930.0, 1000.0)          # the slab's top surface: its far side, its broken near edge
SLAB_C = lerp(W.ICE, K.PAPER, 0.4)   # the thick white ice by the hole: it holds
SLAB_FACE = lerp(W.ICE, K.STEEL, 0.3)


def _cu_edge_x(y, t):
    """The slab's broken edge (x at frame y, from its top surface down under the water); a piece
    breaks away under his glove at T_CHUNK."""
    gone = 60.0 * ease("out3", clamp((t - T_CHUNK) / 0.12)) * clamp((y - 990.0) / 20.0)
    return 455.0 + 10.0 * math.sin(y * 0.07) + 4.0 * K._sn(int(y) // 31, 541) - 0.2 * (y - SLAB_TOP[1]) - gone


def _cu_backdrop(c, t):
    K.fill(c, K.NIGHT)
    K.stars(c, FILM_T0 + t, y1=560.0, n=30, seed=8)
    # the far bank's spruces, low across the river, and the white ice out to them
    for i in range(16):
        x = -40.0 + 75.0 * i + 30.0 * K._sn(i, 501)
        h = 90.0 + 80.0 * hash01(i, 502)
        W.spruce_side(c, (x, 712.0), h, h * 0.45, K.STEEL, seed=i)
    K.poly(c, [(-60.0, 700.0), (1140.0, 700.0), (1140.0, 716.0), (-60.0, 716.0)], K.STEEL)
    K.poly(c, [(-60.0, 714.0), (1140.0, 714.0), (1140.0, CU_WATER), (-60.0, CU_WATER)], lerp(W.ICE, K.NIGHT, 0.55))
    K.poly(c, [(-60.0, CU_WATER), (1140.0, CU_WATER), (1140.0, 2000.0), (-60.0, 2000.0)], K.WATER)


def _cu_hair(c, t):
    """Wet hair plastered to his skull, in clumps, a strand down over his brow."""
    ax, ay = CU_GUARD
    X = lambda ux, uy: (ax - (ux - 400.0) * CU_S, ay - (860.0 - uy) * CU_S)
    clumps = []
    arc = ((476, 204), (448, 166), (400, 140), (340, 126), (280, 126), (220, 138), (166, 166), (122, 210), (96, 262))
    for i, ((x0, y0), (x1, y1)) in enumerate(zip(arc, arc[1:])):
        mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        nx, ny = -(y1 - y0), (x1 - x0)
        L_ = math.hypot(nx, ny) or 1.0
        out = 14.0 + 8.0 * hash01(i, 521)
        tip = (mx + nx / L_ * out + 10.0, my + ny / L_ * out + 12.0)
        clumps.append([X(x0, y0), X(*tip), X(x1, y1), X(mx - nx / L_ * 10.0, my - ny / L_ * 10.0)])
    clumps.append([X(470, 196), X(512, 252 + 4.0 * math.sin(t * 3.0)), X(500, 262), X(452, 214)])   # over the brow
    K.polys(c, clumps, K.INK)


def _cu_face(c, t):
    _cu_backdrop(c, t)
    pant = 0.5 + 0.5 * math.sin(t * 2.0 * math.pi * 2.3)
    m = F.guard(c, CU_GUARD, CU_S, look=-0.3, lid=1.0, fear=1.0, down=0.1, t=t, facing=-1, rim=L.RIM, rim_w=5.0,
                hat=False, wet=1.0, mouth_open=0.3 + 0.55 * pant)
    _cu_hair(c, t)
    # the river over his collar and shoulders
    K.poly(c, [(-60.0, CU_WATER), (1140.0, CU_WATER), (1140.0, 2000.0), (-60.0, 2000.0)], K.WATER, 0.62)
    # the slab in front of him: its top surface, its broken face down to the water and on under it
    ys = [SLAB_TOP[1] + (1500.0 - SLAB_TOP[1]) * i / 24.0 for i in range(25)]
    edge = [(_cu_edge_x(y, t), y) for y in ys]
    above = [p for p in edge if p[1] <= CU_WATER] + [(_cu_edge_x(CU_WATER, t), CU_WATER)]
    K.poly(c, [(-60.0, SLAB_TOP[1])] + edge + [(-60.0, 1500.0)], lerp(SLAB_FACE, K.WATER, 0.82))      # under the water
    K.poly(c, [(-60.0, SLAB_TOP[1])] + above + [(-60.0, CU_WATER)], SLAB_FACE)
    top = [(-60.0, SLAB_TOP[0]), (edge[0][0] - 40.0, SLAB_TOP[0] + 8.0), (edge[0][0] + 8.0, SLAB_TOP[1]),
           (-60.0, SLAB_TOP[1])]
    K.poly(c, top, SLAB_C)
    K.band(c, [top[2], top[3]], K.PAPER, 2.5, seed=4, alpha=0.8)
    # the piece that breaks away under his glove, tipping into the water
    if t >= T_CHUNK:
        u = clamp((t - T_CHUNK) / 0.5)
        ang = math.radians(-75.0 * ease("out3", u))
        pv = (_cu_edge_x(1000.0, T_CHUNK - 0.01) - 30.0, 1000.0)
        base = [(0.0, 0.0), (64.0, -4.0), (70.0, 66.0), (8.0, 72.0)]
        ca, sa = math.cos(ang), math.sin(ang)
        pts = [(pv[0] + x * ca - y * sa, pv[1] + 90.0 * u * u + x * sa + y * ca) for x, y in base]
        K.poly(c, pts, SLAB_FACE)
        K.band(c, pts[:2], K.PAPER, 2.0, seed=6, alpha=0.8)
        L.spray(c, (pv[0] + 30.0, CU_WATER), t, T_CHUNK + 0.08, 420.0, n=16, seed=21, power=0.7)
    # cracks running out from under his fingers across the top of the slab
    for i, (t0, x0) in enumerate(((9.15, 300.0), (9.55, 200.0), (9.95, 340.0), (10.45, 230.0), (10.8, 150.0))):
        tree = K.crack_tree((x0, SLAB_TOP[1] - 22.0 + 10.0 * K._sn(i, 8)), 170.0 + 50.0 * hash01(i, 9), seed=90 + i,
                            heading=182.0 + 6.0 * K._sn(i, 9), depth=1, jag=0.6, segs=6)
        K.crack(c, tree, ease("out3", clamp((t - t0) / 0.22)), lerp(W.THIN, K.INK, 0.4), width=3.5, alpha=0.95)
    # the water lapping at the slab and at him
    K.band(c, [(-60.0, CU_WATER + 2.0 * math.sin(t * 7.0)), (540.0, CU_WATER - 1.5 * math.sin(t * 5.0)),
               (1140.0, CU_WATER - 2.0 * math.sin(t * 6.0))], K.PAPER, 3.0, seed=2, alpha=0.75)
    # his gloves clawing at it, out of the water onto the ice
    for side, (wrist, tip0, ph) in enumerate((((500.0, 1080.0), (270.0, 978.0), 0.0),
                                             ((600.0, 1095.0), (370.0, 990.0), 1.9))):
        claw = 0.5 + 0.5 * math.sin(t * 6.5 + ph)
        slip = 0.0
        if side == 1:
            slip = 80.0 * ease("out3", clamp((t - T_CHUNK) / 0.14)) * (1.0 - ease("inout", clamp((t - T_CHUNK - 0.3) / 0.35)))
        tip = (tip0[0] + 24.0 * claw + slip, tip0[1] + 4.0 * claw + 0.7 * slip)
        F.glove(c, wrist, tip, s=1.05, curl=0.2 + 0.65 * claw, spread=0.75 * (1.0 - claw), rim=L.RIM, rim_w=3.0,
                sleeve_w=0.8)
    # breath coming hard
    K.breath(c, m["mouth"], t, pant=2.3, facing=-1, s=2.4, strength=1.0, seed=6)


# ============================================================================ the page, pulling back (11-14)
CAM_F0 = W.Plan(13.32, 10.2, 330.0)          # on him in the hole, the trunk's tip in the corner
CAM_F1 = W.Plan(11.0, 4.5, 98.0)
G_IN_HOLE = (13.32, 10.3)                # his head, at the near edge of the hole
HAT_AT = (13.55, 11.85)


def _prints_out_of_hole(prints):
    (hx, hn), r = W.HOLE_BIG, W.HOLE_R[1]
    return tuple(p for p in prints if math.hypot(p[0] - hx, p[1] - hn) > r * 1.05)


PRINTS_F = _prints_out_of_hole(PRINTS + (PRINT2,))


def guard_in_hole(c, cam, t, slip=0.0):
    """Him in the hole from above: his bare head and shoulders at the near edge, his arms out on
    the ice, the gloves clawing (slip 0..1 drags them back toward the water) and scoring it; a
    pale wet line where he comes out of the water; rings."""
    ppm = cam.ppm
    hx, hn = G_IN_HOLE
    P = lambda x, n: cam.px((x, n))
    L.rings(c, P(hx, hn + 0.15), t, 0.0, 0.9 * ppm, 0.9 * ppm, n=3, every=0.6, life=1.8, width=max(1.2, 0.015 * ppm),
            seed=3, alpha=0.5)
    rw = max(2.0, 0.02 * ppm)
    arms, hands = [], []
    for k, side in enumerate((-1, 1)):
        claw = 0.5 + 0.5 * math.sin(t * 5.0 + k * 1.9)
        drag = 0.05 * claw + 0.25 * slip                  # how far back toward the water the hand is
        # spread wide, his weight on the ice: shoulder, elbow out, wrist
        sh = (hx + 0.2 * side, hn + 0.06)
        el = (hx + 0.4 * side, hn - 0.12 + 0.5 * drag)
        wr = (hx + 0.42 * side, hn - 0.36 + drag)
        arms.append(bass.capsule_pts(P(*sh), P(*el), 0.07 * ppm, 0.06 * ppm, cap=4))
        arms.append(bass.capsule_pts(P(*el), P(*wr), 0.06 * ppm, 0.05 * ppm, cap=4))
        palm = (wr[0], wr[1] - 0.055)
        hands.append(D_ell(P(*palm), 0.05 * ppm, 0.058 * ppm))
        curl = 0.25 + 0.6 * claw
        digits = [(side * (-24.0 + 16.0 * i) * (1.0 - 0.4 * curl), (0.075 - 0.01 * abs(i - 1.5)) * (1.0 - 0.45 * curl))
                  for i in range(4)] + [(-side * 62.0, 0.05)]          # four fingers toward the bank; the thumb in
        for i, (a, ln) in enumerate(digits):
            a = math.radians(a)
            base = (palm[0] + 0.035 * math.sin(a), palm[1] - 0.04 * math.cos(a))
            tip = (base[0] + ln * math.sin(a), base[1] - ln * math.cos(a))
            hands.append(bass.capsule_pts(P(*base), P(*tip), 0.016 * ppm, 0.013 * ppm, cap=3))
            if i < 4 and drag > 0.01:
                # the fingers score the ice as they drag: from where they bit to where they are
                K.band(c, [P(tip[0], tip[1] - drag), P(*tip)], lerp(W.ICE, K.INK, 0.45), max(1.0, 0.008 * ppm),
                       seed=40 + 4 * k + i, alpha=0.8)
    shoulders = (P(hx, hn + 0.1), 0.3 * ppm, 0.17 * ppm)
    head = (P(hx, hn), 0.12 * ppm, 0.13 * ppm)
    # where he comes out of the water: a wet, pale line round his head and shoulders
    K.polys(c, [D_ell(p, rx + 1.6 * rw, ry + 1.6 * rw) for p, rx, ry in (shoulders, head)], L.RIM_WET, 0.9)
    polys = arms + hands + [D_ell(*shoulders)]
    K.polys(c, [[(x, y - rw) for x, y in q] for q in polys], L.RIM)
    K.polys(c, polys, K.INK)
    # his skull from above, wet hair in clumps, its own moonlit rim so it stands off his shoulders
    hair = []
    for i in range(18):
        q = 6.283 * i / 18
        r = 1.0 + 0.12 * hash01(i, 77)
        hair.append((head[0][0] + head[1] * r * math.cos(q), head[0][1] + head[2] * r * math.sin(q)))
    K.poly(c, [(x + 0.8 * rw, y - 0.9 * rw) for x, y in hair], L.RIM)
    K.poly(c, hair, K.INK)


def D_ell(p, rx, ry, n=20):
    return [(p[0] + rx * math.cos(6.283 * i / n), p[1] + ry * math.sin(6.283 * i / n)) for i in range(n)]


def hat_top(c, cam, t, at=HAT_AT):
    """His ushanka floating in the hole, turning slowly."""
    ppm = cam.ppm
    a = 0.35 * t
    p = cam.px((at[0] + 0.05 * math.sin(t * 0.7), at[1] + 0.03 * math.cos(t * 0.9)))
    pts = []
    for i in range(30):
        q = 6.283 * i / 30
        r = 0.17 * ppm * (1.0 + 0.1 * (0.5 + 0.5 * math.cos(3.0 * q * 3.0)))
        pts.append((p[0] + r * math.cos(q + a), p[1] + r * 0.92 * math.sin(q + a)))
    K.poly(c, pts, K.INK)
    K.ellipse(c, (p[0] + 0.04 * ppm * math.cos(a), p[1] + 0.04 * ppm * math.sin(a)), 0.05 * ppm, 0.035 * ppm,
              lerp(K.INK, K.STEEL, 0.6), angle=math.degrees(a))
    L.rings(c, p, t, 0.3, 0.4 * ppm, 0.4 * ppm, n=2, every=1.1, life=2.0, width=max(1.0, 0.01 * ppm), seed=9, alpha=0.4)


def reed_eyes(c, cam, t, t0, look=(0.0, -0.6), blink=None, size=1.0):
    """Two pairs of eyes in the reeds at the hiding place (hers, wider; the girl's, rounder) on the
    dark of the two of them crouched there, opening at t0; a blink at `blink`."""
    if t < t0 - 0.3:
        return
    k = size * max(1.0, cam.ppm / 110.0)
    for dx, dn, r in ((-0.3, 0.05, 0.36), (0.3, -0.06, 0.28)):
        cx, cy = cam.px((W.HIDE[0] + dx, W.HIDE[1] + dn))
        pts = [(cx + r * cam.ppm * (1.0 + 0.12 * K._sn(i, 531)) * math.cos(6.283 * i / 18),
                cy + r * cam.ppm * 0.8 * (1.0 + 0.12 * K._sn(i, 532)) * math.sin(6.283 * i / 18)) for i in range(18)]
        K.poly(c, pts, K.INK)
    W.draw_reeds(c, cam, (W.HIDE[0] - 0.9, W.HIDE[0] + 0.9, W.HIDE[1] - 0.7, W.HIDE[1] + 0.7))
    if t < t0:
        return
    lid = ease("out3", clamp((t - t0) / 0.2))
    if blink is not None and blink <= t < blink + 0.18:
        lid *= abs(math.cos(math.pi * (t - blink) / 0.18))
    for (dx, dn, w, h, gap) in ((-0.3, 0.05, 26.0, 12.0, 40.0), (0.3, -0.06, 22.0, 17.0, 36.0)):
        cx, cy = cam.px((W.HIDE[0] + dx, W.HIDE[1] + dn))
        for side in (-1, 1):
            x = cx + side * gap * 0.5 * k
            hh = h * k * lid
            if hh < 1.5:
                continue
            K.ellipse(c, (x, cy), w * k * 0.5, hh * 0.5, K.PAPER)
            K.ellipse(c, (x + look[0] * w * 0.2 * k, cy + look[1] * hh * 0.22), h * 0.3 * k, min(hh, h * k) * 0.3,
                      K.INK)


def _page_wide(c, t):
    u = ease("inout", clamp((t - T_PAGE - 0.45) / 2.4))
    cam = W.plan_lerp(CAM_F0, CAM_F1, u)
    W.draw_page(c, cam, FILM_T0 + t, prints=PRINTS_F, holes=("stone", "guard"))
    hat_top(c, cam, t)
    guard_in_hole(c, cam, t, slip=0.3 * clamp((t - 12.8) / 0.4) * (1.0 - clamp((t - 13.3) / 0.3)))
    reed_eyes(c, cam, t, T_EYES, look=(0.15, -0.7), blink=13.4)


# ============================================================================ render
def render(f, t, T):
    K.scene_setup(f, K.NIGHT)
    with f.screen() as c:
        if t < T_SECTION:
            sx, sy = L.shake(t, T_STEP, amp=16.0, dur=0.32)
            c.translate(sx, sy)
            _page_close(c, t)
        elif t < T_UNDER:
            _section_break(c, t)
        elif t < T_BURST:
            _under(c, t)
        elif t < T_CU:
            _cling_section(c, t)
        elif t < T_PAGE:
            _cu_face(c, t)
        else:
            _page_wide(c, t)


def motion_blur(t, T):
    return 1


def cues(T):
    return [
        Cue(0.05, "boot_ice", gain_db=-14, dc="a hobnailed boot set down on bare ice: a hard, careful knock"),
        Cue(T_STEP, "ice_crack", gain_db=-1, dc="the ice cracks under him: a huge, ringing CRACK, the star bursting out"),
        Cue(T_SILENCE[0], "silence", gain_db=-60, dur=0.5, dc="everything drops out: dead silence for half a second"),
        Cue(T_BREAK, "ice_break", gain_db=-2, dc="the slab gives way: shattering, crunching ice"),
        Cue(1.3, "plunge", gain_db=-3, dc="a heavy body plunging into black water"),
        Cue(1.42, "splash", gain_db=-8, dc="the water slaps up round him"),
        Cue(T_UNDER, "underwater_roar", gain_db=-10, dur=T_BURST - T_UNDER,
            dc="under the ice: a muffled, heavy roar of the current, everything far away"),
        Cue(T_UNDER, "heartbeat_slow", gain_db=-8, dur=T_BURST - T_UNDER, dc="his heartbeat, slow and huge, under water"),
        Cue(T_UNDER, "bubbles", gain_db=-12, dur=0.6, dc="a rush of bubbles out of his coat"),
        Cue(T_LAMP_GO, "lantern_sink", gain_db=-20, dur=2.0, dc="the lantern's glass ticking as it sinks, muffled"),
        Cue(T_LAMP_BED, "clunk_under", gain_db=-16, dc="the lantern settling on the stones of the riverbed, a muffled clunk"),
        Cue(T_RIFLE_GO + 1.35, "clunk_under", gain_db=-18, dc="the rifle hitting the riverbed, muffled"),
        Cue(T_LOOK + 0.1, "bubbles", gain_db=-10, dur=0.5, dc="a breath let go: a burst of bubbles"),
        Cue(T_LOOK + 0.2, "string_rise", gain_db=-16, dur=1.8, dc="a single string note rising as he sees the hole"),
        Cue(T_KICK, "swim_strokes", gain_db=-16, dur=T_BURST - T_KICK, dc="heavy strokes through water, muffled"),
        Cue(T_BURST, "surface_burst", gain_db=-4, dc="he bursts up through the surface: water crashing off him"),
        Cue(T_BURST + 0.08, "gasp_man", gain_db=-4, dc="a man's gasp for air, ragged and loud (a recorded gasp)"),
        Cue(T_GRAB1, "glove_ice", gain_db=-12, dc="wet gloves slapping onto ice"),
        Cue(T_GIVE, "ice_snap", gain_db=-5, dc="the edge snaps off under his hands"),
        Cue(T_GIVE + 0.05, "splash", gain_db=-6, dc="he goes under again"),
        Cue(T_UP2, "surface_burst", gain_db=-6, dc="up again, water pouring off him"),
        Cue(T_UP2 + 0.1, "gasp_man", gain_db=-5, dc="another gasp, desperate"),
        Cue(T_GRAB2, "glove_ice", gain_db=-10, dc="his gloves hit the near edge and hold"),
        Cue(T_CU, "panting_man", gain_db=-8, dur=T_PAGE - T_CU, dc="his breath coming hard and ragged, close"),
        Cue(T_CU, "ice_scrape", gain_db=-14, dur=T_PAGE - T_CU, dc="gloved fingers clawing and scraping at ice"),
        Cue(T_CHUNK, "ice_crack_small", gain_db=-9, dc="a piece of the edge cracks and breaks away"),
        Cue(T_PAGE, "water_lap", gain_db=-18, dur=T - T_PAGE, dc="water slopping in the hole as he clings"),
        Cue(T_PAGE, "wind_low", gain_db=-24, dur=T - T_PAGE, dc="the night wind over the river, low"),
        Cue(T_PAGE + 0.4, "panting_man", gain_db=-20, dur=T - T_PAGE - 0.4, dc="his gasps, smaller, far off"),
        Cue(T_EYES, "heartbeat", gain_db=-12, dur=T - T_EYES, dc="her heartbeat, quick and close"),
    ]
