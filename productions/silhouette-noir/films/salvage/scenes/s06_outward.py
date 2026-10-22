"""s06 · OUTWARD: the holes in her hull were cut from the inside (8.0 s).

IN  (whip left from s05, 0.5 s): mid-whip, the camera still racing right along her bilge
    plating and braking onto the big hole (settled by ~0.4 s); the lamp's pool slides in
    with it, the beam coming from the lower left (his helmet, just off frame).
Beats (scene-local s):
  0.0-1.2     the main hole, close: steel petals bent OUTWARD toward us, dark torn tongues
              over the lamp's warm pool, their shadows thrown up-right across the plate
  [holes@1.46]  the beam swings up: a second hole; then down past the first: a third
              (the camera eases back to hold all three, 1.2-2.9)
  2.9-3.6     the pool returns to the big hole; the camera leans in
  [cut@3.61]  his gloved hand comes in from the lower left and a fingertip touches the tip
              of a torn petal (its shadow meets it on the plate); he runs it along the edge
  [inside@4.52]  the camera pushes into the big hole; the hand drops away; darkness fills
              the frame (the lamp's pool slides off the plate)
OUT (hard cut): 100 % black from 7.70 to 8.0 (the hole's interior), into s07's black.
"""
import math

from engine import atmos, draw
from engine.core import H, W, clamp, ease, hash01, lerp, noise1, smoothstep
from engine.frame import Camera
from engine.timing import Cue
from films.salvage import sets as S
from films.salvage.scenes import _lib_s05_s06_s08 as LIB

PAL = S.PAL
INK = PAL.ink
HP = S.HullPlating()
HOLE0 = HP.HOLES[0]                 # (0, 0, 230): the big one
HOLE1 = HP.HOLES[1]                 # (-250, -880, 150): above
HOLE2 = HP.HOLES[2]                 # (170, 820, 175): below


def _beats(T):
    def at(w, d):
        try:
            return T.at(w)
        except Exception:
            return d
    return dict(holes=at("holes", 1.462), cut=at("cut", 3.61), inside=at("inside", 4.516))


# ============================================================================= the touch
_TIPS = HP.petal_tips(0, 0.0)
TIP = min(_TIPS, key=lambda p: math.hypot(p[0] + 380.0, p[1] - 140.0))      # the left tongue
SHOULDER = (-1250.0, 1450.0)
T_IN = 2.95                         # the arm starts in
T_TOUCH = 3.61
T_DROP = 5.0


def _hand_target(t):
    """Where the index fingertip is: in from the lower left on an arc, a soft landing on the
    tongue's tip, a slow stroke along its torn edge, then it falls away."""
    tip = TIP
    if t < T_TOUCH:
        u = ease("out", clamp((t - T_IN) / (T_TOUCH - T_IN)))
        a = (-1050.0, 1250.0)
        mid = (-760.0, 520.0)
        p = ((1 - u) ** 2 * a[0] + 2 * u * (1 - u) * mid[0] + u * u * tip[0],
             (1 - u) ** 2 * a[1] + 2 * u * (1 - u) * mid[1] + u * u * tip[1])
        return p
    s = t - T_TOUCH
    # stroke along the edge toward the hole (the tongue's side), then hold
    run = ease("inout", clamp(s / 0.9))
    edge = (tip[0] + 70.0 * run, tip[1] - 28.0 * run - 6.0 * math.sin(math.pi * run))
    if t < T_DROP:
        return edge
    v = ease("in", clamp((t - T_DROP) / 1.1))
    return (edge[0] - 380.0 * v, edge[1] + 900.0 * v)


def _arm(f, t, zoom):
    """The diver's arm and its shadow on the plate (thrown up-right, away from the lamp; it
    meets the finger where the finger touches)."""
    if t < T_IN or t > T_DROP + 1.2:
        return
    tgt = _hand_target(t)
    curl = 0.25 * smoothstep(T_TOUCH - 0.05, T_TOUCH + 0.15, t)
    # the shadow first: the same arm pushed away from the lamp, more the farther from the plate
    lamp = _lamp_src(t)
    sh_dx, sh_dy = LIB.unit(tgt[0] - lamp[0], tgt[1] - lamp[1])
    gap = 1.0 - smoothstep(T_TOUCH - 0.5, T_TOUCH, t) * (1.0 - smoothstep(T_DROP, T_DROP + 0.4, t))
    pool = _pool(t)
    k = clamp(1.2 - math.hypot(tgt[0] - pool[0], tgt[1] - pool[1]) / pool[2]) * _power(t)
    if k > 0.01:
        with f.layer(blur=5.0) as L:
            L.push_group()
            L.translate(tgt[0], tgt[1])
            L.scale(1.08, 1.08)
            L.translate(-tgt[0] + sh_dx * (24.0 + 120.0 * gap), -tgt[1] + sh_dy * (24.0 + 120.0 * gap))
            LIB.glove_arm(L, SHOULDER, tgt, 600.0, 560.0, r=(132.0, 112.0, 84.0), hand=235.0, curl=curl, seed=5)
            L.pop_group_to_source()
            L.paint_with_alpha(0.5 * min(k, 1.0))
    with f.layer() as L:
        LIB.glove_arm(L, SHOULDER, tgt, 600.0, 560.0, r=(132.0, 112.0, 84.0), hand=235.0, curl=curl, seed=5)


# ============================================================================= light
LAMP_SRC = (-1250.0, 1500.0)        # his helmet lamp, off frame lower left


def _whip_dx(t):
    """How far the camera still is from its landing (world px; < 0 = left of it)."""
    if t >= 0.42:
        return 0.0
    u = clamp((t + 0.30) / 0.72)
    return -1500.0 * (1.0 - u) ** 3


def _lamp_src(t):
    """His helmet lamp: off frame, lower left, riding with the camera through the whip."""
    return (LAMP_SRC[0] + _whip_dx(t) + 30.0 * noise1(t * 0.4, 3), LAMP_SRC[1] + 20.0 * noise1(t * 0.35, 4))


def _pool(t):
    """(x, y, radius) of the lamp's pool on the plating."""
    keys = [(0.30, (-220.0, 150.0, 660.0)),
            (1.25, (-250.0, 140.0, 680.0)),
            (1.62, (-380.0, -700.0, 760.0), "inout"),
            (2.05, (-300.0, -620.0, 780.0)),
            (2.55, (-120.0, 760.0, 780.0), "inout"),
            (2.90, (-160.0, 700.0, 800.0)),
            (3.45, (-300.0, 190.0, 880.0), "inout"),
            (4.6, (-280.0, 170.0, 900.0)),
            (6.2, (-60.0, 60.0, 700.0), "inout"),
            (7.4, (500.0, -300.0, 500.0), "in")]
    x, y, r = LIB.track(keys, t)
    if t < 0.42:                       # the beam leads the whip and brakes onto the hole
        x += _whip_dx(t + 0.06)
    j = 14.0 * noise1(t * 0.7, 9)
    return (x + j, y + 0.7 * j, r)


def _power(t):
    return 1.0 - 0.9 * smoothstep(5.6, 7.3, t)


# ============================================================================= camera
def _cam(t, b):
    land = (-30.0, 80.0, math.log(0.95))
    wide = (-60.0, -20.0, math.log(0.60))
    lean = (-230.0, 150.0, math.log(0.78))
    if t < 0.42:
        c = (land[0] + _whip_dx(t), land[1], land[2])
    elif t < 1.2:
        c = land
    elif t < 2.9:
        u = ease("inout", (t - 1.2) / 1.7)
        c = tuple(lerp(a, bb, u) for a, bb in zip(land, wide))
    elif t < b["inside"]:
        u = ease("inout", (t - 2.9) / (b["inside"] - 2.9))
        c = tuple(lerp(a, bb, u) for a, bb in zip(wide, lean))
    else:
        # push into the big hole: the zoom grows exponentially so the push feels constant
        u = clamp((t - b["inside"]) / (7.7 - b["inside"]))
        v = ease("in", u) * 0.35 + 0.65 * ease("inout", u)
        z = lean[2] + (math.log(9.0) - lean[2]) * v
        k = ease("inout", min(1.0, u * 1.4))
        c = (lerp(lean[0], HOLE0[0] + 10.0, k), lerp(lean[1], HOLE0[1] + 10.0, k), z)
    roll = 1.5 * math.sin(0.5 * t) * (1.0 - smoothstep(4.5, 6.0, t)) + 6.0 * smoothstep(b["inside"], 7.7, t)
    cam = Camera(c[0], c[1], math.exp(c[2]), rot=roll)
    if 0.3 < t < 4.6:
        cam = cam.shaken(t, amp=2.0, rot_amp=0.12, freq=0.9, seed=6)
    return cam


# ============================================================================= render
def render(f, t, T):
    b = _beats(T)
    cam = _cam(t, b)
    f.set_camera(cam)
    pool = _pool(t)
    pw = _power(t)
    HP.draw(f, t, lamp=(pool[0], pool[1]), power=pw, beam_r=pool[2])
    # the beam from his helmet (off frame, lower left) to the pool
    src = _lamp_src(t)
    cone = LIB.lamp_beam(f, t, src, (pool[0], pool[1]), stop="perp", half=10.0, intensity=0.42 * pw, pool=0.0,
                         dust=0.55, seed=7, fog=0.5, core=0.3)
    _arm(f, t, cam.zoom)
    # his breath: bubbles rising across the plate from below left
    atmos.breathing(f, (src[0] + 120.0, src[1] - 260.0), period=4.0, phase=0.9, n=14, t=t, seed=21,
                    size=(2.0, 10.0), rise=(300.0, 460.0), spread=60.0, current=50.0, height=3600.0, alpha=0.65,
                    lit=cone)
    atmos.marine_snow(f, density=0.9, t=t, seed=16, sink=7.0, current=(12.0, 0.0), alpha=0.85, lit=cone)
    # the darkness of the hole takes the frame
    f.post["vignette"] = lerp(f.post["vignette"], 0.55, 0.8)
    f.post["fade"] = max(f.post.get("fade", 0.0), smoothstep(6.9, 7.7, t))


def motion_blur(t, T):
    return 5 if t < 0.25 else 1


def cues(T):
    b = _beats(T)
    return [
        Cue(-0.2, "whip lands: the water rush brakes, a low metallic hum of the hull", gain_db=-10, dur=0.8),
        Cue(0.3, "torn steel creaks faintly in the current", gain_db=-16, dur=2.0),
        Cue(b["holes"], "a second, then a third hole: two low pulses", gain_db=-11, dur=1.2),
        Cue(b["cut"], "glove on torn steel: a soft scrape, a tiny metallic tick", gain_db=-8, dur=0.9),
        Cue(b["inside"], "the push in: the drone drops, the sound closes in", gain_db=-9, dur=3.0),
        Cue(7.7, "silence: into the dark of the hull", gain_db=-20, dur=0.3),
    ]
