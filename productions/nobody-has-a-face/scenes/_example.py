"""Reference scene (NOT in the film) showing the conventions every scene module follows.

Pattern: compute everything from t (pure function), build the camera from Tracks,
draw background -> lit group (environment + figures + rain) -> emissive props -> fx,
and sync key beats to narration words through T.at('word').
"""
from engine import *


def render(f, t, T):
    strike = T.at("I'm") if any(w["w"] == "I'm" for w in T.words) else 2.0
    # camera: slow push-in, then a small shake on the flare
    cam = Camera(540, Track([(0, 900), (T.duration, 1060)])(t), Track([(0, 1.0), (T.duration, 1.6, "inout3")])(t))
    if t > strike:
        cam = cam.shaken(t, amp=6 * pulse(t, strike, 0.02, 0.4), seed=3)
    f.set_camera(cam)

    ground = 1500
    lamp = props.streetlamp(f, (820, ground), height=900, facing=-1, t=t)
    fx.light_cone(f, lamp, 100, 50, 1100, AMBER, 0.12)

    p = rig.walk(t, 260, ground, 90, facing=1, limp=0.5)            # the detective's limp
    if t > strike - 0.6:                                               # raise the LEFT hand to strike
        k = ease("out3", inv_lerp(strike - 0.6, strike - 0.1, t))
        hand_target = (p.x + 40, p.y - 150)
        p = p.blend(rig.reach(p, "l", hand_target), k)
    lights = [Light.cone(lamp, 100, 54, 1200)]
    J = rig.solve(p)
    flare = pulse(t, strike, 0.03, 0.35)
    lit = clamp((t - strike) / 0.08) if t >= strike else 0.0
    if lit > 0:
        lights.append(Light.radial(J["lh"], 330 * (1 + 0.5 * flare)))

    with f.lit(lights, ambient=0.2):
        sets.street(f, ground)
        fx.rain(f, t)
        rig.draw_figure(f, p)
    fx.splashes(f, t, ground, -100, 1180)
    fx.reflection(f, lamp[0], ground + 46, 280, 40, AMBER, 0.45, t)
    props.match(f, J["lh"], angle=-80, lit=lit, flare=flare, t=t, seed=1)


def cues(T):
    strike = 2.0
    return [Cue(strike - 0.05, "match_strike", gain_db=-1, pan=-0.1),
            Cue(strike + 0.02, "match_flare", gain_db=-4)]


def motion_blur(t, T):
    return 1
