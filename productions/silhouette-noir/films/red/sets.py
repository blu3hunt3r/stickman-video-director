"""RED - recurring sets and props (public API). Everything is re-exported here:

    from films.red import sets as S

World coords, y DOWN, zoom-1 px (adult ~600 px, the girl 380, the wolf ~330 at the shoulder).
Every draw is a deterministic function of (frame, mood, t). Static geometry is built once
and cached (the clearing builds lazily, ~0.3-0.8 s, on first use).

TERRAINS (sets_terrain): exact walkable ground, one coordinate system per segment.
    S.PATH       the village street (x < 0) and the trail through the gate at x = 0, down
                 through the forest (endless).  Landmarks: S.PATH_MARKS.
    S.RIDGE      S05: off the trail at x = 0, deep snow up to the crest at RIDGE.crest_x.
    S.CLEARING   S07-S09, S11: the cottage door at x = 0.
    t.ground_y(x) firm footing (plant feet/paws here: Actor(..., ground=S.RIDGE.ground_y))
    t.snow_y(x)   visible snow top (= ground_y - depth(x)); t.slope / angle / normal / point
    S.ground_y    = S.PATH.ground_y (the default street/trail ground)
    S.terrain_for(scene) -> the terrain of "s02".."s11"

THE SANDWICH (every side-scrolling set):
    SET.draw_back(f, mood, ...)     sky, fog layers, everything far
    SET.draw_plane(f, mood, ...)    the action plane behind the characters
    ... characters (feet on the set's terrain.ground_y) ...
    SET.draw_front(f, mood, ...)    snow lip (hides sunk feet / legs in deep snow), near
                                    stakes, light pools, blurred foreground occluders

SETS
    S.VILLAGE        s02 (NIGHT), s10 (MORNING). Mother's door V.threshold / V.door_x, well,
                     gate (x = 0), lanterns. Doors across the street: V.doorways(f),
                     V.doors_near(V.door_x, 3, f=f), draw_back(doors=V.door_schedule({id: t}))
                     shuts them one by one (the light wedges vanish).
    S.FOREST         s03, s04 (mood=None: DAY near the village -> DEEP in the thicket).
                     FOREST.eye_track(xw) / thicket_has_cover(xw): where the wolf's eyes are.
    S.RIDGE_SET      s05: the climb in deep snow, crest, lee drop, spindrift.
    S.VALLEY_VIEW    s06: her POV, a 2.5D matte. V.camera("start"|"path"|"house"|"hoods"|
                     "wide"), V.cam_lerp(a, b, u), V.draw(f, mood, t, hoods=0..1),
                     V.hood_screen_positions(f, t) for the Bass grid, V.crest_y(x) where she
                     stands (back to camera) for the s05 OUT / s06 IN.
    S.CLEARING_SET   s07-s09, s11. eras "web" | "burnt" | "later". C.ignite(t0) -> Burn;
                     C.smash_point, C.spider_top / spider_end, C.web, C.hoods, C.lanterns,
                     C.cottage (threshold, anchors(state)).

THE WEB (sets_web): a graph of Strands (polylines with kind/width/tag). burn =
    C.ignite(12.66): per-vertex arrival times (Dijkstra), burn.state(t), progress(t),
    fronts(t), flames(t), heat(t), light_sources(t), release_time(sid), t_done.

MOODS (sets_common): DAY, DEEP, DUSK, NIGHT, DAWN_M, MORNING, LATER; mood_mix(a, b, u).
PROPS (sets_props): Lantern, swing_angle, lantern_burst, Basket, basket_spill, draw_spill,
    hood_poly / draw_hood / hood_on_branch / hood_sway, Doorway, draw_stake; hood_fall,
    Hoods, LanternPath (sets_cottage); Footprints, PathMarkers (sets_terrain).

EXAMPLE: forest walk (s03)
    girl = Actor(cast.RED_GIRL, cast.red(), x=3400, ground=S.PATH.ground_y, facing=1)
    girl.walk(to=5000)
    x = girl.root(t)[0]
    f.set_camera(Camera(x=x + 60, y=S.PATH.ground_y(x) - 470, zoom=1.0))
    m = S.FOREST.mood_at(f.cam.x)                       # or a scripted mood_mix(DAY, DEEP, u)
    S.FOREST.draw_back(f, m)
    S.FOREST.draw_plane(f, m)
    with f.layer() as L:
        girl.draw(f, t, L)
    S.FOREST.draw_front(f, m, keep_clear=(380, 700))    # fades occluders off the subject

EXAMPLE: the web fire (s08, the lantern smashed at 12.66 s)
    C = S.CLEARING_SET
    burn = C.ignite(12.66) if t >= 12.66 else None      # cached; spreads from C.smash_point
    f.set_camera(Camera(x=520, y=40, zoom=0.40))
    C.draw_back(f, S.NIGHT, era="web", t=t)
    C.draw_plane(f, S.NIGHT, era="web", t=t, burn=burn)  # web hoods fall as threads burn
    with f.layer() as L:
        ...wolf, spider, girl...
        if burn:
            S.lantern_burst(f, L, C.smash_point, t, 12.66, S.NIGHT, S.CLEARING)
    C.draw_front(f, S.NIGHT, era="web", t=t, burn=burn)  # snow lip + firelight wash
    s09: era="burnt", mood=S.DAWN_M, release=0.0 (every hood falls over ~2 s from t = 0)
"""
from .sets_common import *          # noqa: F401,F403
from .sets_terrain import *         # noqa: F401,F403
from .sets_props import *           # noqa: F401,F403
from .sets_forest import *          # noqa: F401,F403
from .sets_village import *         # noqa: F401,F403
from .sets_web import *             # noqa: F401,F403
from .sets_cottage import *         # noqa: F401,F403
from .sets_valley import *          # noqa: F401,F403
from .sets_common import MORNING, tinted                         # noqa: F401
from .sets_terrain import PATH, RIDGE, CLEARING

ground_y = PATH.ground_y
"""Default ground (the village street and the forest trail). Other segments:
RIDGE.ground_y, CLEARING.ground_y."""

SCENE_TERRAIN = {
    "s01": PATH, "s02": PATH, "s03": PATH, "s04": PATH, "s05": RIDGE, "s06": RIDGE,
    "s07": CLEARING, "s08": CLEARING, "s09": CLEARING, "s10": PATH, "s11": CLEARING,
}


def terrain_for(scene):
    """The terrain (ground functions) of a scene id "s01".."s11"."""
    return SCENE_TERRAIN[scene.lower()[:3]]
