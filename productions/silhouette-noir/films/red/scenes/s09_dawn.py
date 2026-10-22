"""s09 · DAWN: the clearing at dawn (14.0 s). One continuous shot.

IN   (flash from s08, warm white): dawn light, smoke, the burnt web hanging in black threads.
0.0-2.0   every red hood lets go of the burnt web and the trees and drifts down through the
          smoke like leaves (CLEARING_SET release=0.0). She stands by the cottage, looking up.
L16 2.0-5.9   the wolf lies wounded in the snow right of the cottage, breathing hard, eyes
          shut. She walks to it.
L17 6.6-9.4   she kneels by its head.
L18 10.4-13.5 she reaches out; on [never@12.21] her hand touches its muzzle and its eyes open.
OUT  dissolve (1.5 s) on the close two-shot, her hand on its muzzle.

Camera: a single eased move from the wide hood-fall (zoom 0.40) down and in: the walk
(0.62 at 6.4 s), the kneeling two-shot (0.90 at 10 s), then a slow creep in on the touch
(1.32 at 14.75).
Layers: CLEARING back (sky, fogged forest, hood trees) > plane (trees, cottage, web
remnants, hoods) > wolf, girl > snow lip, smoke, brambles > falling ash.
"""
import math

from engine import atmos
from engine.creatures import Wolf
from engine.motion import Actor
from engine.timing import Cue
from films.red import cast
from films.red import sets as S
from films.red.scenes import _lib_s09_s11 as L
from films.red.sets_common import mix

C = S.CLEARING_SET
TER = S.CLEARING
MOOD = S.DAWN_M
G = TER.ground_y

GIRL_X0 = 700.0          # where she stands when the light comes back
GIRL_STOP = 1120.0       # end of her walk
KNEEL_X = 1148.0         # her pelvis when kneeling
WOLF_X = 1655.0          # the wolf's root before it settles (muzzle tip lands at ~1275)
WOLF_OFF = 6.0           # the wolf's clock runs ahead: it is already lying at t = -0.5


def _words(T):
    return dict(every=T.at("every"), wolf=T.at("wolf"), path0=T.at("path"), and_=T.at("and"),
                ran=T.at("ran"), because=T.at("because"), never=T.at("never"), leave=T.at("leave"),
                path1=T.at("path", 1))


_CACHE = {}


def _cast(T):
    if "girl" in _CACHE:
        return _CACHE["girl"], _CACHE["wolf"]
    W_ = _words(T)
    t_touch = W_["never"]                                      # 12.21
    # ---- the wolf: already down, eyes shut, heavy fast breathing; the eyes open after the touch
    w = Wolf(WOLF_X, G, facing=-1, size=330.0, seed=3)
    w.lie(60.0, head_down=0.78, eyes=0.0, breath=2.4)
    t_open = t_touch + 0.62                                    # fully open (fade-in 0.6 s)
    w.overlay("eyes", t_open + WOLF_OFF, 30.0, open=1.0)
    w.overlay("look", t_touch + 1.25 + WOLF_OFF, 30.0, turn=6.0, head=-2.0, neck=-17.0)
    wolf = L.WolfRig(w, WOLF_OFF)
    # ---- the girl
    g = Actor(cast.RED_GIRL, cast.red(), x=GIRL_X0, ground=G, facing=1, seed=9, name="red")
    g.stand(until=2.55, at=-1.0, idle=0.8)
    g.walk(to=GIRL_STOP, gait="child_walk", speed=0.40)        # ~2.9 s, arrives ~5.45
    g.stand(until=6.75)
    kneel_t0 = 6.75
    L.kneel(g, kneel_t0, 60.0, x=KNEEL_X, t_in=1.05, lean=16.0, head=10.0, arms=(-22.0, 24.0))
    # she looks up at the falling hoods, then at the wolf
    g.look_at(-1.0, 2.15, (980.0, 250.0), fade=0.5)
    head = lambda t: wolf.head(t)["eye"]
    g.look_at(2.6, 30.0, head, fade=0.6)
    # leaning in while kneeling, more for the reach
    g.key("pitch", [(8.2, 0.0), (9.6, 5.0, "inout"), (11.2, 6.0), (12.1, 13.0, "inout"), (20.0, 13.0)],
          mode="add")
    g.key("spine.2", [(11.2, 0.0), (12.1, 6.0, "inout"), (20.0, 6.0)], mode="add")
    # the reach: slow, a hesitation half way, the touch lands on [never]
    tgt0 = lambda t: _hand_target(wolf, t, 0.0)

    def tgt(t):
        u = L.k01(t, 11.05, t_touch - 11.05, "inout")
        hes = 0.06 * math.sin(math.pi * L.k01(t, 11.4, 0.5, "inout"))
        p_far = _rest_hand(g, t)
        p_on = tgt0(t)
        k = u - hes
        return (p_far[0] + (p_on[0] - p_far[0]) * k, p_far[1] + (p_on[1] - p_far[1]) * k)
    g.reach("R", 11.05, 30.0, tgt, fade=0.25, grip=0.15)
    g.arm("L", 11.2, 30.0, fade=0.5, sh=-38.0, elbow=46.0)          # the other hand stays on her knee
    g.blink(4.2)
    g.blink(9.1)
    _CACHE["girl"], _CACHE["wolf"] = g, wolf
    return g, wolf


def _hand_target(wolf, t, dx):
    """The wrist when her palm rests on the muzzle bridge."""
    h = wolf.head(t)
    bx, by = h["nose"]
    return (bx - 18.0 + dx, by - 7.0)


def _rest_hand(g, t):
    """Where the reaching hand starts: in front of her knees."""
    x, y = g.root(t)
    return (x + 40.0, y + 20.0)


CAM = L.CamPath([
    (-0.6, 900.0, 140.0, 0.40),
    (2.0, 950.0, 210.0, 0.42, "inout"),
    (6.4, 1180.0, 760.0, 0.62, "inout"),
    (10.0, 1290.0, 990.0, 0.90, "inout"),
    (14.75, 1300.0, 1150.0, 1.32, "inout"),
])


def _camera(t):
    return CAM.at(t)


def render(f, t, T):
    girl, wolf = _cast(T)
    f.set_camera(_camera(t))
    C.draw_back(f, MOOD, era="burnt", t=t, release=0.0)
    C.draw_plane(f, MOOD, era="burnt", t=t, release=0.0)
    with f.layer() as c:
        wolf.draw(f, t, c, far_shade=0.25)
        girl.draw(f, t, c)
    # the eyes opening: a soft bloom on the eye as it opens (the touch)
    W_t = T.at("never")
    op = L.k01(t, W_t + 0.05, 0.6, "inout")
    if op > 0:
        e = wolf.head(t)["eye"]
        L.eye_flare(f, e, op * (1.0 - 0.45 * L.k01(t, W_t + 0.8, 1.2, "inout")), size=1.0)
    C.draw_front(f, MOOD, era="burnt", t=t)
    # ash still drifting down after the fire
    atmos.snow(f, density=0.22, wind=14.0, t=t, seed=19, color=mix(MOOD.fog_at(0.55), MOOD.ink, 0.35),
               size=0.75, speed=0.42, alpha=0.75)


def motion_blur(t, T):
    return 1


def cues(T):
    W_ = _words(T)
    tn = W_["never"]
    return [
        Cue(0.0, "red hoods let go and drift down through the smoke: soft cloth flutter, many, "
                 "close and far, like falling leaves", -10, dur=2.4),
        Cue(0.9, "hoods landing softly in the snow, scattered soft pats", -16, dur=3.6),
        Cue(0.0, "dawn air after the fire: smouldering crackle dying away, thin wind", -18, dur=14.0),
        Cue(0.4, "the wolf's breathing: heavy, fast, wet (wounded), steady under the scene", -14, dur=12.2),
        Cue(2.55, "small footsteps in snow, slow, hesitant", -14, dur=2.9),
        Cue(6.8, "she kneels in the snow: soft crunch", -12),
        Cue(tn, "her hand touches the fur: a hush", -14),
        Cue(tn + 0.1, "the wolf's breath catches and slows", -12, dur=1.6),
        Cue(tn + 0.35, "its eyes open: a low soft tone", -12, dur=1.2),
    ]
