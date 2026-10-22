"""SALVAGE - recurring sets and props (public API). `from films.salvage import sets as S`.

Everything is a deterministic function of t drawn with pycairo in WORLD coordinates
(x right, y DOWN, an adult ~600 px tall at zoom 1, M = 333 px per metre). No people here:
figures are figure.py's (films/salvage/cast.py); scenes draw them between the set passes.

ONE WORLD (sets_common)
    y = 0 mean sea level (sky y < 0, water y > 0); the seabed at SEABED_Y = 9000 (~27 m).
    DIVE_X = 0: the shot line. The boat's davit sheave hangs above it, the Meridian's stern and
    BELL lie below it. A camera can travel from the boat to the bell without a cut.
    Separate little worlds with their own origins: the wreck INTERIOR (Interior), the S06
    hull-plating close-up (HullPlating) and the dial close-up (DialCloseup).

MODULES
    sets_common    layout constants, colours (water_at, depth_light, tone), cached shapes,
                   ropes (line, sag_curve), current (sway, pendulum), torn edges (jag,
                   riveted_edge), legacy parallax helpers (proj/unproj for f.layer(par)).
    sets_surface   A. the sea: sea_y/sea_slope/float_pose (the swell), night_sky + moon,
                   far_sea in perspective, underwater (section water), surface_glow,
                   water_front, and sea_world() = all of it for a waterline split shot.
    sets_boat      B. Boat: the diving tender riding the swell; anchors in world coords.
    sets_deep      C/D. the deep: deep_backdrop (water by depth), depth_info, View (2.5D lens
                   projector with depth fog), Painter, DeepWorld (seabed strips, sea grass,
                   reef walls, debris, front occluders), seabed_y(x, z), rod3/prism3/card.
    sets_wreck     E. Wreck (the Meridian on her port side) + HullPlating/hole_push (S06).
    sets_interior  F. Interior (vertical shaft, the captain's cabin on its side, the safe),
                   InteriorView, at_depth, DialCloseup (S08 end - S09).
    sets_props     G. bell (draw_bell, bell_swing, bell_haul), safe (draw_safe, SAFE,
                   draw_dial, dial_angle_for), logbook, photo, envelope, knife (+ knife_glint),
                   lead weight / boot (+ sink), hook, rope coil, captain's cap.

THE TWO COORDINATE SPACES OF THE DEEP
    World (x, y, z): true position plus distance z behind the action plane (z < 0 = in front).
    Action plane (X, Y) = view.P(x, y, z): where to draw it with the normal camera (f.layer()
    / f.ctx); size there = world size * view.k(z). Figures stand in the action plane (z = 0),
    feet at seabed_y(x). Every wreck/interior anchor is given in world (x, y, z): convert
    with view.Pp(p3) and scale with view.k(z).

KEY ANCHORS (world coords; all functions of t where things move)
    Boat()                 x = BOAT_X = -1062; deck_y(x, t) (feet), davit_tip(t), sheave(t)
                           (lifting line leaves the block ~ (-2, -723)), winch_drum(t) ->
                           (centre, flange r, core r), pump_crank(t, angle) -> dict(left, right,
                           hub_left, hub_right, R), lantern_pos(t), hose_exit(t) (where the red
                           hose goes over the stern ~ (-154, -183): the cut), ladder(t) ->
                           dict(top, bottom, rungs, hooks), stations(t) -> named deck points
                           (bow, wheelhouse_aft, pump_left, coil, winch_fwd, stern, ladder_top..)
    Wreck()                bell_pose(t) / bell_point(t) (crown ~ (26, 8254, 150)),
                           bell_screen(view, t) -> dict(X, Y, s, k, angle, clapper, pivot),
                           bracket_point(), line_entry() (the port the line goes in), holes(),
                           stern_top(), roof_y(s), transom(), funnel_pose(), W(s, b, h)
    HullPlating()          HOLES (main hole at the origin), petal_tips(hole, t)
    Interior()             entry() (the cut hole at the shaft top), holds() (hand holds down
                           the shaft), safe_pose(), safe_dial(view) -> (p3, (X, Y)),
                           safe_outline(view), skylight(), lamp_pose(t), door_angle(t, wake),
                           chair_pose(t); draw_mid() returns the safe's action-plane anchors
    DialCloseup()          camera(r_screen, rot), draw(...) -> dict(dial, index, number)

ORDER OF PASSES (the engine's Frame): backdrop -> set (main pass, far to near, blurred by
depth) -> figures -> lit / additive set passes (draw_lit, draw_lights) -> front occluders.

EXAMPLE - a wide boat shot on the waterline split at night (S02 / S04 / S14):

    f = Frame(t=t, scale=scale, pal=SALVAGE)
    boat = S.Boat()
    f.set_camera(Camera(x=boat.x + 330, y=-330, zoom=0.5))
    S.sea_world(f, t, moon=(905, 700), moon_r=56, dusk=0.15, veil=0.6)
    with f.layer() as L:
        boat.draw(L, t, pump_angle=200 * t, line_to=(40, 1250), line_sag=-50)
        st = boat.stations(t)          # client at st["stern"], diver below at (x, y > 0)
        ... figures; the red hose from boat.hose_exit(t) to the diver's helmet ...
    S.water_front(f, t, alpha=0.07)    # the near water over the hull below the line
    boat.draw_lights(f, t, lantern=1.0, window=0.7, masthead=1.0)

EXAMPLE - the wreck reveal (S05): the lamp finds her stern, her name and the bell:

    f.set_camera(Camera(x=250, y=7250, zoom=0.3))
    S.deep_backdrop(f, t, glow=[(300, 560, 1250, 1.3), (250, 1450, 520, 0.7)], murk=0.28)
    wreck = S.Wreck()
    world = S.DeepWorld(wreck=wreck, reef=False)
    view = world.draw(f, t, view=S.View(f, murk=0.28, vp=(540, 1150)))   # low vp: she towers
    ... diver at (x, S.seabed_y(x)) in f.layer(); his lamp point `lamp` ...
    aim = (tx - lamp[0], ty - lamp[1])                 # e.g. (tx, ty) = view.Pp(wreck.W(0, 120, 2050))
    wreck.draw_lit(f, t, view, lamp, aim, spread=15)   # warm pool, rivets, MERIDIAN on the transom
    ... beam (atmos) ...
    world.draw_front(f, t, view)
    b = wreck.bell_screen(view, t)                     # tie the line at (b["X"], b["Y"])

    Descents (S03): DeepWorld(wreck=None, reef=S.REEF + S.REEF_FRONT, front=()) with
    View(f, down_fog=1.6); the camera y follows the diver, depth_info(cam.y) fades rays,
    snow and lamp. Cabin (S08): InteriorView + Interior passes (see sets_interior). The
    cabin's safe lies on its side (drawn at angle -90, index mark to the left): for a match
    cut, start DialCloseup.camera(r_screen >= 360, rot=-90) and turn it upright (rot -> 0).

COSTS (scale 0.5, one process): set layers 15-170 ms per frame (see the QA report); cache
nothing per frame yourself - static geometry is cached inside the modules.
"""
from .sets_common import *          # noqa: F401,F403
from .sets_surface import *         # noqa: F401,F403
from .sets_boat import *            # noqa: F401,F403
from .sets_deep import *            # noqa: F401,F403
from .sets_wreck import *           # noqa: F401,F403
from .sets_props import *           # noqa: F401,F403
from .sets_interior import *        # noqa: F401,F403
