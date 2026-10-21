"""S01 - The Lineup (golden hook).

"Seven witnesses saw the killer's face. Not one of them could describe it.
 Because in this city... nobody has a face."

Shot plan
  0.00-0.35  black; the bare bulb stutters on
  0.35-3.30  tight on the swinging bulb, tilt down its cone onto five identical figures
  3.30-6.00  the witness's trembling hand enters huge in the foreground, pointing figure to figure
  6.00-9.88  dolly into the center figure's hollow head; bulb flickers on "nobody", dies on "face";
             darkness, then the ring returns alone -> OUT: white ring at screen center, r ~ 260 px
"""
import math

from engine import *

L = sets.LINEUP
SWING_PERIOD = 3.2
END_ZOOM = 260.0 / rig.SEG["head_r"]          # head ring ends ~260 px on screen


def _bulb_on(t, T):
    """Stutter on at the start, flicker on 'nobody', dies on 'face' (2nd occurrence)."""
    if t < 0.12 or 0.18 <= t < 0.27:
        return 0.0
    death = T.at("face", 1)
    fl = T.at("nobody")
    for a, b in ((fl + 0.04, fl + 0.10), (fl + 0.26, fl + 0.31), (fl + 0.47, fl + 0.50)):
        if a <= t < b:
            return 0.15
    if t >= death:
        return 0.0
    return 0.93 + 0.07 * flicker(t, 3, rate=12, depth=0.6)


def _swing(t, T):
    amp = tween(t, 5.6, 8.0, 16.0, 5.0, "inout")
    return amp * math.sin(2 * math.pi * t / SWING_PERIOD)


def _figures(t):
    poses = []
    for k, x in enumerate(L["xs"]):
        p = rig.stand(x, L["floor_y"], facing=0)
        p = p.copy(la=6 + 3 * (k % 2), ra=6 + 2 * ((k + 1) % 2))
        poses.append(rig.breathe(p, t, amt=0.9, seed=11 + 7 * k))
    return poses


def _camera(t, T, head):
    tilt = Track([(0.0, (540.0, 806.0, 3.1)), (0.5, (540.0, 812.0, 3.0)),
                  (3.3, (540.0, 1185.0, 1.32), "inout3"), (6.0, (540.0, 1195.0, 1.38), "inout")])
    x, y, z = tilt(t)
    if t > 6.0:
        k = ease("inout3", inv_lerp(6.0, 9.15, t))
        x = lerp(x, head[0], k)
        y = lerp(y, head[1], ease("inout", inv_lerp(6.0, 8.9, t)))
        z = math.exp(lerp(math.log(z), math.log(END_ZOOM), k))
    cam = Camera(x, y, z)
    if t < 6.0:
        cam = cam.shaken(t, amp=2.2, rot_amp=0.15, freq=0.7, seed=21)
    return cam


def _witness_arm(f, t, T, poses, cam):
    """Huge foreground arm of the witness (out of focus, screen space)."""
    t_in = T.at("not") - 0.15
    if t < t_in or t > 7.4:
        return
    rise = ease("out3", inv_lerp(t_in, t_in + 0.55, t))
    drop = ease("in3", inv_lerp(6.4, 7.4, t))
    targets = Track([(t_in, 0), (3.95, 0), (4.15, 1, "out3"), (4.55, 1), (4.75, 3, "out3"),
                     (5.0, 3), (5.2, 2, "out3"), (5.55, 2), (5.75, 4, "out3"), (6.1, 4), (6.35, 2, "out3")])
    k = targets(t)
    i0, i1 = int(math.floor(k)), min(4, int(math.floor(k)) + 1)
    J0 = rig.solve(poses[i0])
    J1 = rig.solve(poses[i1])
    fr = k - i0
    tgt_w = lerp(J0["head"], J1["head"], fr)
    tgt = cam.to_screen(tgt_w)
    shoulder = (1010.0, 2260.0)
    tremble = (10 * fbm1(t * 7.5, 41) + 4 * noise1(t * 21, 43), 8 * fbm1(t * 6.5, 47))
    hand = (500 + 0.2 * (tgt[0] - 540) + tremble[0], 1455 + tremble[1])
    hand = (lerp(shoulder[0], hand[0], rise), lerp(shoulder[1], hand[1], rise) + 520 * drop)
    ux, uy = vnorm((tgt[0] - hand[0], tgt[1] - hand[1]))
    elbow = (hand[0] - ux * 300, hand[1] - uy * 300)
    with f.screen():
        with f.blurred(4.0):
            draw.stroke(f, [shoulder, elbow, hand], 24.0, WHITE, 0.9)


def render(f, t, T):
    poses = _figures(t)
    head = rig.solve(poses[2])["head"]
    cam = _camera(t, T, head)
    f.set_camera(cam)
    on = _bulb_on(t, T)
    swing = _swing(t, T)
    death = T.at("face", 1)

    ax, ay = L["bulb_anchor"]
    bdir = 90 - swing
    bc = (ax + math.cos(math.radians(bdir)) * (L["cord"] + 46), ay + math.sin(math.radians(bdir)) * (L["cord"] + 46))

    lights = []
    if on > 0:
        lights = [Light.cone(bc, bdir, 74, 1100, intensity=on), Light.radial(bc, 260, intensity=0.7 * on)]
    after = clamp((t - death) / 0.25)
    ambient = lerp(0.12, 0.0, after) * (1.0 if on > 0.5 or t < death else 0.6)

    if on > 0:
        fx.light_cone(f, bc, bdir, 70, 1050, AMBER, 0.11 * on, glow=0.35 * on)
    with f.lit(lights, ambient=ambient, soften=4.0):
        sets.lineup_room(f, glass=False)
        fx.dust(f, t, (120, 640, 960, 1420), n=110, seed=17, alpha=0.6)
        for p in poses:
            rig.draw_figure(f, p)
    props.bulb(f, L["bulb_anchor"], L["cord"], swing=swing, on=on, t=t, glow_r=150)

    # the ring returns alone after the blackout (afterimage -> next scene's moon)
    ring = ease("inout", inv_lerp(death + 0.32, death + 0.62, t))
    if ring > 0:
        J = rig.solve(poses[2])
        rig_w = rig.FIG_LW * poses[2].s ** 0.5
        draw.circle(f, J["head"], J["head_r"], rig_w, WHITE, ring)

    _witness_arm(f, t, T, poses, cam)


def cues(T):
    c = [Cue(0.10, "bulb_flicker", gain_db=-6, pan=0.0),
         Cue(0.27, "bulb_hum", gain_db=-14, dur=T.at("face", 1) - 0.27)]
    for k in range(6):
        tc = 0.8 + 1.6 * k
        if tc < T.at("face", 1) - 0.3:
            c.append(Cue(tc, "bulb_creak", gain_db=-16 + (2 if k % 2 else 0), pan=0.25 if k % 2 else -0.25))
    fl = T.at("nobody")
    c += [Cue(fl + 0.03, "bulb_flicker", gain_db=-8), Cue(fl + 0.25, "bulb_flicker", gain_db=-9),
          Cue(T.at("face", 1) - 0.01, "bulb_pop", gain_db=-7)]
    c.append(Cue(T.at("not") - 0.1, "whoosh", gain_db=-20, size=0.3))
    return c
