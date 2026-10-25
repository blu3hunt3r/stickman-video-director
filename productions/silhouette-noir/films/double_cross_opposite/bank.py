"""DOUBLE CROSS, the OPPOSITE cut: the bank's interiors at night (forked from films/double_cross/bank.py;
the kit's palette is OPPOSITE's: NAVY is the teal NIGHT, GOLD is AMBER, STEEL the teal steel). The
street itself, in elevation and section, is street.py; use these sets for the close stages: the
hall (corridor), vault_door, vault, door_inside, sewer, and the props. The tilt helpers (eye_cam,
plan_cam_for, TiltSet, popped) and the chalk edges belong to the blueprint version: do not use them.

COORDINATES (read this first)
-----------------------------
Every set is drawn in SET px and placed on the frame by an explicit camera:

    cam = Bk.Cam(x=545.0, y=-420.0, zoom=1.15)   # the set point (x, y) sits at the frame centre
    Bk.front_street(c, cam, t)                    # each set function applies cam itself
    with cam.on(c):                               # draw your own things (figures) in set px
        C.draw(c, "knight", st, pose, x, 0.0, Bk.FIG_S, 1, bg=K.NAVY, rim_w=4.0 / cam.zoom)
    fx, fy = cam.to_frame((Bk.MANHOLE_X, 0.0))   # a set point in frame px

SET px are plan px turned on their side: y is DOWN and y = 0 is the set's ground line (the
street, or the floor of a room); heights are negative y, the underground is positive y. The
horizontal axis depends on which way the set looks:

  * NORTH-LOOKING sets (front_street, sewer(view="main"), corridor, vault_door, vault_through):
    x IS the plan's x (east to the right). Seen from the TILT camera at eye level these line up
    with the plan exactly: eye_cam(plancam) gives the Cam that matches a PlanCam at phi 0, yaw 0.
  * EAST-LOOKING sections (vault, sewer(view="branch")): x is the plan's y (NORTH TO THE LEFT,
    south to the right), so the vault door is at the right end and walking north is walking left.
  * door_inside is SOUTH-LOOKING (from inside the vault at its door): x = 1080 - plan x (east
    on the left), so the door's hinge is on the left.

The cast stand on y = 0 at scale FIG_S (figure units -> set px): the Architect is ~132 set px
tall, about 76 set px to the metre. Inside a Cam, pass rim_w = 4.0 / cam.zoom to C.draw so the
rims stay ~4 frame px.

Everything is a pure function of its arguments (no state); static geometry is cut once and
cached. Colours are the kit's: NAVY night, STEEL moonlit stone and iron, INK, DEEP rooms, GOLD
light, PAPER chalk, RED for him.

EXPORTS
-------
Cameras
  Cam(x, y, zoom)                 set point (x, y) at the frame centre, `zoom` frame px per set px.
    .on(c)                        context manager: draw in set px.
    .to_frame(p) / .to_set(p)     convert points.  .view(margin) -> (x0, y0, x1, y1) set rect seen.
    Cam.lerp(a, b, u)             blend two cameras (zoom blends geometrically; pass an eased u).
    Cam.toward(a, b, u, p)        an AIMED push from a to b: set point p glides along a straight
                                  frame line from where a sees it to where b does, zoom geometric.
  eye_cam(pc, ground=0.0)         the Cam matching PlanCam pc at eye level (phi 0, yaw 0): a plan
                                  point at height z lands where set (x, ground - z) does.
  plan_cam_for(cam, cy, phi=0.0)  the inverse: a PlanCam tuple (cx, cy, zoom, phi, yaw, fx, fy) that
                                  sees what `cam` sees at phi 0, tilting about plan depth cy (for a
                                  tilt from the world up into the plan: lerp it toward a plan view).
  TiltSet(pc, plan_y, stand=False)
                                  a north-looking set standing on the plan at depth plan_y, seen
                                  through PlanCam pc mid-tilt: `with TiltSet(pc, 860).on(c):` draw
                                  in set px (corridor_px(..., bg=False), figures). stand: figures
                                  keep pc.stand() of their height (the plan's cheat). .to_frame(p),
                                  .zoom, .m (the cairo Matrix). At phi 0 it equals eye_cam(pc).

Places (set px; see the constants below for the full list)
  FIG_S; the street: FACADE_X, FACADE_H, WING_X, PORTICO_X, DOOR_X, ALLEY_X, LAMP_X, CAR_X, MOON_AT,
  BELL_SET, MANHOLE_X, SHAFT_A, ROAD, PIPE (crown, invert), WATER (the water line in the pipe),
  HATCH_X, HATCH_SHAFT, RUNG_STEP, STORE_X, ROOM_H; the corridor: CORR_X, CORR_H, MOUTH_X, MOUTH_H,
  PIPE_X, PIPE_Y, CRATES, CAT_SEAT, CAN_SEAT, GUARD_DESK, GUARD_LAMP; the vault door: VDOOR_C,
  VDOOR_R, FRAME_R, HINGE_X, DIAL_C, DIAL_R, WHEEL_C; the vault (east-looking): VAULT_U, VAULT_IN,
  VAULT_H, BOX_U, BOX_ROWS, RUBY_BOX, VDOOR_U, TRAP_U, TILE_U, VSLAB, BRANCH, BRANCH_WATER, GOLD_U,
  MANHOLE_B_U, HATCH_U.
  CRATES are three (x0, y0, x1, y1) boxes WEST of the mouth (two on the floor, one on top, its
  west end at 340): the cat sits at CAT_SEAT on the top crate's east end, the tin can at CAN_SEAT
  on its west end, so whatever falls off falls west, toward the guard and away from the crew.
  shaft_rect(name)                (x0, y0, x1, y1) inside a shaft ('a', 'hatch', 'trap', 'b'), for
                                  clipping a climber to it.
  open_rects(cut, above=True)     the street section's open parts at `cut` (set px rects: above the
                                  road, shaft A so far, the pipe so far, the hatch shaft).
  clip_open(c, cut, above=True)   context manager: clip to open_rects (inside cam.on).
  window_rect(u)                  the cutaway window round the store room at u (x0, y0, x1, y1).
  LID_L, LID_HOME                 manhole A's lid: its length and its east edge when shut.
  lid_pose(lid) -> (pivot_x, angle)
                                  the lid as its east edge on the road and its west edge's lift
                                  (deg); lid 0..1 is the canned move, or pass a (pivot_x, angle).
  lid_edge(lid)                   the raised west edge, set px (for a hand on it).
  ROUTE_STREET, ROUTE_IN_E        Plan A's route as the north-looking street section sees it: along
                                  the curb from the car to manhole A; and down shaft A, east along
                                  the pipe, up the hatch shaft into the store room.
  drip_times(t0, t1, view)        [(t, x)]: when and where drips hit the water (for the cues).

Sets (each takes c, a Cam and the time t, and applies the camera itself)
  front_street(c, cam, t, pop=None, lid=0.0, cut=0.0, lamp=1.0, headlights=0.0, bell=0.0,
               above="street", car_on=True, chalk=0.0, hatch=0.0, window=0.0, car_door=0.0,
               car_x=CAR_X, sky=SKY)
      The front street at night (north-looking elevation) with the ground in section below it:
      moon, the neighbours, the bank's classical front (rusticated wing with three barred
      windows; a portico of four columns on the doors, pediment, round clock), the steps, the
      street lamp, the alley mouth (its alarm bell high on the wall), manhole A, the car.
      pop: {element: 0..1} pop-up progress (0 folded flat on its base line, 1 standing, with an
           outback overshoot) for 'facade', 'portico', 'pediment', 'clock', 'lamp', 'moon',
           'car', 'neighbours'. Missing keys are standing.
      lid: manhole A's cover, 0 shut .. 0.5 levered up on edge .. 1 dragged aside and dropped.
      cut: 0 solid earth .. 1 the street cut open: shaft A opens top-down (0..0.45), then the
           sewer pipe from the shaft outward (0.45..1), the cuts edged in chalk while they open.
      hatch: the hatch's lid in the store room floor, 0 shut .. 1 thrown open.
      window: 0..1 a cutaway window opens in the bank's wing round the store room (you see in:
           the shelves, the hatch, the door to the corridor).
      above: 'street' (the facade) or 'section' (the bank cut open along the street).
      headlights: 0 off .. 1 on (they flare). bell: the alarm bell's ring (0 still; > 0 rocks).
      chalk: 0..1 a PAPER chalk edge round the facade. car_door: the car's rear door, 0..1 open.
      sky: the sky's colour (None: leave what is there).
      pop also takes 'alley' (the alley mouth and its bell). Its parts, each in set px inside a
      cam.on, for a scene composing its own street: facade(c, t, pop=None, chalk=0.0),
      car(c, t, headlights=0.0, u=1.0, x=CAR_X, door=0.0), street_lamp(c, u=1.0, on=1.0),
      moon(c, u=1.0), neighbours(c, u=1.0), clock(c, t, u=1.0), alarm_bell(c, ring_=0.0, t=0.0),
      manhole_lid(c, lid), hatch_lid(c, u), ground(c, t, cut=0.0, lid=0.0).
      popped(c, base_y, u): context manager; draw an element popping up off its base line.
  water(c, cam, t, view="main", x0=None, x1=None)
      The water's front edge, to draw AFTER figures standing in the pipe (stand them on
      WATER + 8) so their feet are under it.
  splash(c, cam, p, t, t0, s=1.0)
      A water ring and two flecks at set point p (on the water line) from t0 (a footstep).
  sewer(c, cam, t, view="main", cut=1.0, hatch=0.0, trapdoor=0.0, drips=True, above="section",
        manhole_b=0.0, lid=1.0)
      The sewer in section: the earth, the long NAVY pipe, the black water line, drips with
      ripples, iron rungs up each shaft. view='main' is the front street's sewer, north-looking:
      exactly front_street's underground, cut open. view='branch' is the branch north under the
      bank, east-looking (north left): manhole B's shaft at MANHOLE_B_U up to the back street,
      the trapdoor shaft at TRAP_U up to the vault floor (the bank cut open above it), the hatch
      at HATCH_U. hatch / trapdoor / manhole_b: their lids, 0 shut .. 1 open.
  corridor(c, cam, t, lamp=1.0, can=None, on_wall=None, door_dot=0.0)
      The cross corridor inside the bank (north-looking side elevation): the guard's post on the
      left (desk, chair, a small GOLD lamp), the long far wall with its pipes, the dark mouth of
      the corridor to the vault (the alcove, MOUTH_X: the vault door is just visible far down it,
      black on black), the vertical pipe beside it (PIPE_X: the stethoscope's clank), crates
      (CRATES; the cat sits at CAT_SEAT). can: (x, y, angle) of the tin can, None on its crate.
      on_wall(c): called in set px after the far wall is painted and before what stands in front
      of it (pipes, desk, crates), to lay a flashlight's patch ON the wall. door_dot: 0..1 a chalk
      dot on the far door's dial, seen down the mouth (the cut to s06): the far door is drawn at
      the vault door's own coordinates, so a Cam on DIAL_C match-cuts to vault_door with that Cam.
  corridor_px(c, t, lamp=1.0, can=None, on_wall=None, door_dot=0.0, bg=True)
      The same in set px with no camera of its own (inside a TiltSet). bg=False: no INK fill.
  vault_door(c, cam, t, open=0.0, bolts=0.0, wheel=0.0, dial=0.0, light="dark", inside=None,
             dial_color=None, glow=None, face=None, numerals=False)
      The great round door in the vault's south wall (north-looking): frame ring, the door with
      its rings, the spoked wheel (`wheel` degrees), the dial (`dial` degrees), twelve radial
      bolts (bolts: 0 shot home .. 1 withdrawn; they go one after another round the rim), the
      hinge on the east. open: 0 shut .. 1 swung 88 degrees toward the camera on its hinge (the
      circle narrows to an ellipse and the door's thickness shows on its free edge). light:
      'dark' or 'gold' (the opening is gold and gold spills out round it on the wall, and in a
      stepped pool on the floor toward us, SPILL_POOL); inside(c): draws what is seen through the
      opening (set px, clipped to it; vault_through is one). glow: 0..1 the spill's strength
      (default: how far it is open). dial_color: the dial's ticks (PAPER, or RED). face: the
      door's steel colour (default STEEL; pass a darker one for a dark shot). numerals: the
      dial's 0 10 20 30 (for a close-up).
  spill_shadow(c, x, g, half=7.0, seed=0)
      A figure's shadow in the gold's floor pool (set px, after vault_door, before the figure):
      from its feet at x toward us, fanning out from the opening's middle; g the spill (0..1).
  door_face(c, t, bolts=0.0, wheel=0.0, dial=0.0, dial_color=None, face=None, numerals=False)
      Only the shut door's outer face (set px, about VDOOR_C), for a scene drawing it itself.
  vault_through(c, t, light="gold", gold=1.0)
      The vault seen through its door, north-looking (for vault_door's inside): the far wall of
      deposit boxes (8 x 6), the floor running back to its foot, a pyramid of gold bars on it.
  lock_cutaway(c, centre, scale, wheels, dots=(0, 0, 0), line=0.0, fence=0.0, bolt=0.0,
               color=K.PAPER, alpha=1.0, spindle=None, seed=0)
      The lock as a chalk diagram (frame px, centred on `centre`, scale 1 = ~660 px wide): three
      wheels side by side with their gates (wheels: their angles in degrees, clockwise; a gate is
      at the top, under the fence, at angle 0 mod 360), ticks round each rim, a chalk dot popping
      in each gate (dots 0..1, outback), the straight chalk line joining the dots (line 0..1, left
      to right), the fence above (fence 0 up .. 1 dropped into the gates), the bolt at the right
      in its keeper (bolt 0 shot .. 1 withdrawn). spindle: a frame point (the dial) the dashed
      spindle runs to from the wheels' axle. Returns {'gates': [3 points], 'bolt', 'fence'}.
  dial_face(c, p, r, angle, color=K.PAPER, face=K.INK, bezel=K.STEEL, seed=0, alpha=1.0,
            numerals=False, index=True)
      The combination dial (in whatever space c is in), turned by `angle` degrees clockwise: the
      plan's dial (s03's lens): bezel, face, 40 ticks (a long one every 5), numerals 0 10 20 30
      when asked (numerals=True), the knob, the index mark above it (fixed).
  vault(c, cam, t, light=None, door=0.0, box=0.0, glint=0.0, tile=0.0, floor_cut=0.0, gold=1.0)
      The vault inside (EAST-looking section, north left): the deposit wall behind (6 x 5 boxes;
      the ruby box is RUBY_BOX), the gold stacked at GOLD_U, the cut north and south walls, the
      door's opening at the right end with the great door outside it.
      light: None (lit by the gold: the GOLD look), 'dark' (black: only a faint edge), or
             ('match', (x, y), r): dark, lit in stepped gold rings round a match at set point
             (x, y) out to radius r (the scene draws the flame: K.flame).
      door: 0 open (the door stands outside, its back face on) .. 1 shut (in the opening).
      box: the ruby box's little door, 0 shut .. 1 open; glint: the RED glint in it (0..1).
      tile: the floor tile over the trapdoor, 0 down .. 1 lifted aside (black below).
      floor_cut: 0..1 the floor cut away below the room: the slab, the void under the trapdoor,
           the sewer branch pipe running north-south (left-right) with its water.
      gold: how much gold is still on the stacks (1 all .. 0 none: the bags are full).
  door_inside(c, cam, t, light=None, bolts=0.0)
      The inside of the shut door (SOUTH-looking, from inside the vault; hinge on the left): the
      round back plate, the gearbox, twelve bolt bars running out to the bolts in the frame
      (bolts: 0 shot .. 1 withdrawn), the hinge knuckles; the room's walls either side, the box
      wall's end on the left, gold stacked on the right. light: as vault().
  match_rings(c, cam, p, r, t, strength=1.0, seed=0)
      Only the stepped gold rings of a match's light round set point p (radius r set px).

Props and small things
  ladder_pose(who, h, facing=1, rung=RUNG_STEP, reach=1.0) -> (st, pose)
      A procedural climbing pose (iron rungs; the figure in profile facing the ladder): h is how
      far (set px) the feet are above the ladder's foot. Draw it with C.draw(c, who, st, pose, x,
      foot_y, FIG_S, facing), foot_y the shaft's bottom (WATER for the sewer's shafts): the
      shafts' rungs are RUNG_STEP apart from there up, and the feet and hands step from rung to
      rung, near and far sides alternating. Animate h (up or down) to climb.
  hold_sack(fill=0.0, seed=0, floor=None)
                                  a pose.hold fn: a canvas sack hanging from the fist (fill 0
                                  empty and slack .. 1 stuffed with gold, bar ends showing).
                                  floor: the floor's y in figure units: a sack that would hang
                                  through it slumps on it instead.
  sack(c, p, fill, s=1.0, color=K.INK, rim=None, seed=0)
                                  a sack standing on the floor (set px, p its base centre).
  bar(c, p, s=1.0, angle=0.0, color=K.GOLD, edge=K.INK, shine=K.PAPER)
                                  one gold bar in elevation (p its base centre, s 1 = 24 px long).
  gold_stacks(c, gold=1.0, ...)   the vault's gold stacks (east-looking set px).
  stethoscope(c, ear, piece, s=1.0, color=K.INK, rim=None, piece_color=K.STEEL)
                                  the Cracker's stethoscope: the tube from his ear (any space)
                                  looping down to the chest-piece at `piece`.
  tin_can(c, p, angle=0.0, color=None)
                                  the corridor's tin can (p its centre).
  ghost_route(c, pts, lit=0.0, gap=24.0, r=5.5, color=K.PAPER, ghost=0.28, seed=0, head=True,
              t=0.0, lit_t=None, xf=None, alpha=1.0)
                                  Plan A's chalk route laid on the world (any space): dots along
                                  pts, dim (alpha `ghost`) ahead and bright where the crew have
                                  reached (lit: the first `lit` px of its length, or a function
                                  s -> 0..1), an arrowhead at the end. lit_t(s): when the dot at
                                  arc length s lit (it pops then). xf: maps pts' space into c's
                                  (dots stay on the world, r stays a size in c's space). alpha:
                                  the whole route's opacity.
  footfalls(perf, t0, t1, step=1/12, lift=15.0, land=8.0) -> [(t, side, x)]
                                  the frames (on twos) where a mocap Performance's feet land:
                                  for footstep cues (x in figure units, as perf's own x).

Drawing helpers (any space; jittered cut-paper edges, `seed` fixes the jitter)
  rect(c, r, color), poly(c, pts, color), disc(c, p, r, color), ring(c, p, r, w, color),
  band(c, a, b, w, color), ellipse(c, p, rx, ry, color, alpha), fill_all(c, color),
  clipped(c, r) (context manager: clip to rect r).
"""
import math
from contextlib import contextmanager
from functools import lru_cache

import cairo

from engine import bass, draw
from engine import paperdoll as pd
from engine.core import clamp, ease, hash01, lerp
from films.double_cross_opposite import cast as C
from films.double_cross_opposite import kit as K

W, H = K.W, K.H


# ============================================================================ the camera
class Cam:
    """A 2D camera on a set: the set point (x, y) at the frame centre, zoom frame px per set px."""

    def __init__(self, x=540.0, y=-300.0, zoom=1.0):
        self.x, self.y, self.zoom = float(x), float(y), float(zoom)

    def tuple(self):
        return (self.x, self.y, self.zoom)

    @staticmethod
    def lerp(a, b, u):
        z = math.exp(lerp(math.log(a.zoom), math.log(b.zoom), u))
        return Cam(lerp(a.x, b.x, u), lerp(a.y, b.y, u), z)

    @staticmethod
    def toward(a, b, u, p):
        """An aimed push from a to b: set point p glides in a straight frame line while zoom goes geometric."""
        z = math.exp(lerp(math.log(a.zoom), math.log(b.zoom), u))
        fa, fb = a.to_frame(p), b.to_frame(p)
        fx, fy = lerp(fa[0], fb[0], u), lerp(fa[1], fb[1], u)
        return Cam(p[0] - (fx - W / 2.0) / z, p[1] - (fy - H / 2.0) / z, z)

    def matrix(self):
        return cairo.Matrix(self.zoom, 0.0, 0.0, self.zoom, W / 2.0 - self.zoom * self.x, H / 2.0 - self.zoom * self.y)

    @contextmanager
    def on(self, c):
        c.save()
        c.transform(self.matrix())
        try:
            yield c
        finally:
            c.restore()

    def to_frame(self, p):
        return (W / 2.0 + self.zoom * (p[0] - self.x), H / 2.0 + self.zoom * (p[1] - self.y))

    def to_set(self, p):
        return (self.x + (p[0] - W / 2.0) / self.zoom, self.y + (p[1] - H / 2.0) / self.zoom)

    def view(self, margin=0.0):
        hw, hh = W / 2.0 / self.zoom + margin, H / 2.0 / self.zoom + margin
        return (self.x - hw, self.y - hh, self.x + hw, self.y + hh)

    def __repr__(self):
        return f"Cam({self.x:.1f}, {self.y:.1f}, {self.zoom:.3f})"


def eye_cam(pc, ground=0.0):
    """The Cam equivalent to PlanCam pc at eye level (phi 0, yaw 0): a plan point at height z
    lands where the set point (x, ground - z) does."""
    z = pc.zoom
    return Cam(pc.cx + (W / 2.0 - pc.fx) / z, ground + (H / 2.0 - pc.fy) / z, z)


def plan_cam_for(cam, cy, phi=0.0):
    """A PlanCam tuple (cx, cy, zoom, phi, yaw, fx, fy) that sees what Cam `cam` sees when phi is 0,
    pivoting about plan depth cy as it tilts (the inverse of eye_cam, with fx = W/2)."""
    return (cam.x, cy, cam.zoom, phi, 0.0, W / 2.0, H / 2.0 - cam.zoom * cam.y)


class TiltSet:
    """A north-looking set standing upright on the plan at plan depth plan_y (set x = plan x, set y
    = minus the height), seen through a P.PlanCam pc: a set during a tilt between the world and
    the plan. stand: draw it pc.stand() tall (the cheat that keeps figures readable from high up)
    instead of foreshortened. At phi 0, yaw 0 it is eye_cam(pc).

        with Bk.TiltSet(pc, 860.0).on(c):      # draw in set px
            Bk.corridor_px(c, t, bg=False)"""

    def __init__(self, pc, plan_y, stand=False):
        a = math.radians(pc.yaw)
        z, fl = pc.zoom, pc.flat()
        up = pc.stand() if stand else pc.upright()
        dy = plan_y - pc.cy
        self.zoom = z
        self.m = cairo.Matrix(z * math.cos(a), z * fl * math.sin(a), 0.0, z * up,
                              pc.fx + z * (-pc.cx * math.cos(a) - dy * math.sin(a)),
                              pc.fy + z * fl * (-pc.cx * math.sin(a) + dy * math.cos(a)))

    @contextmanager
    def on(self, c):
        c.save()
        c.transform(self.m)
        try:
            yield c
        finally:
            c.restore()

    def to_frame(self, p):
        return self.m.transform_point(*p)


# ============================================================================ tones
SKY = K.NAVY
STONE = K.STEEL                                   # moonlit stone
STONE_SH = lerp(K.STEEL, K.NAVY, 0.5)             # stone in shadow (recesses)
STONE_DK = lerp(K.STEEL, K.INK, 0.5)              # deep joints, under the cornice
NEIGH = lerp(K.NAVY, K.STEEL, 0.38)               # the neighbours, farther
NEIGH_DK = lerp(K.NAVY, K.INK, 0.35)
EARTH = K.INK
SLAB = lerp(K.INK, K.STEEL, 0.30)                 # a cut slab of road or floor
TUNNEL = K.NAVY
LINING = lerp(K.NAVY, K.STEEL, 0.55)
VOID = lerp(K.INK, K.NAVY, 0.55)                  # an empty shaft seen in section
IRON = K.STEEL
ROOM = K.DEEP
WALL_IN = lerp(K.NAVY, K.DEEP, 0.30)              # a dark interior wall at night
GLASS = lerp(K.NAVY, K.STEEL, 0.25)
GOLD_WALL = lerp(K.GOLD, K.INK, 0.50)             # the vault's walls in the gold's light
GOLD_BOX = lerp(K.GOLD, K.INK, 0.32)
GOLD_SEAM = lerp(K.GOLD, K.INK, 0.72)
LID = lerp(K.STEEL, K.PAPER, 0.12)
LID_LIT = lerp(K.STEEL, K.PAPER, 0.34)              # a lid lifted into the light

# ============================================================================ places (set px)
FIG_S = 0.2                    # figure units -> set px
GROUND = 0.0

# the front street (north-looking)
FACADE_X = (170.0, 910.0)
FACADE_H = 600.0               # the cornice line (4 x the plan's exterior wall height)
WING_X = (170.0, 560.0)        # the plain wing: three barred windows
PORTICO_X = (560.0, 910.0)     # the portico: four columns on the doors
COLS = (592.0, 672.0, 818.0, 886.0)
COL_W = 40.0
DOOR_X = (700.0, 790.0)        # the front doors, as on the plan
STEP_H = 12.0
STEPS_Y = -3 * STEP_H          # the portico floor
PED_H = 140.0                  # the pediment's rise
CLOCK_AT = (745.0, -FACADE_H - 50.0)
ALLEY_X = (910.0, 1004.0)
BELL_SET = (957.0, -232.0)     # the alarm bell, high in the alley (on the side door's wall)
LAMP_X = 100.0
CAR_X = 935.0                  # the car's middle, at the alley mouth (the plan's CAR)
CAR_L = 236.0
MOON_AT = (872.0, -1060.0)
MANHOLE_X = 250.0
MANHOLE_R = 30.0               # half the opening
ROAD = 30.0                    # the road slab, cut (y 0..ROAD)
PIPE = (210.0, 400.0)          # the sewer pipe's crown and invert
WATER = 380.0                  # the water line in the pipe
SHAFT_A = (MANHOLE_X - 28.0, MANHOLE_X + 28.0)
HATCH_X = 450.0
HATCH_SHAFT = (HATCH_X - 26.0, HATCH_X + 26.0)
RUNG_STEP = 34.0               # rungs are at (shaft bottom) - k * RUNG_STEP, k = 1, 2, ...
STORE_X = (186.0, 495.0)       # the store room, in section (above the hatch)
ROOM_H = 250.0                 # floor to ceiling inside the bank

# the corridor (north-looking): the cross corridor and the mouth of the corridor to the vault
CORR_X = (186.0, 894.0)
CORR_H = 250.0
MOUTH_X = (505.0, 575.0)       # the vault corridor's mouth: the dark alcove
MOUTH_H = 206.0
PIPE_X = 590.0                 # the vertical pipe beside the mouth (the stethoscope's clank)
PIPE_Y = (-226.0, -212.0)      # the two horizontal pipes along the far wall
CRATES = ((346.0, 0.0, 420.0, -64.0), (424.0, 0.0, 492.0, -64.0), (340.0, -64.0, 418.0, -124.0))   # west of the mouth
CAT_SEAT = (402.0, -124.0)     # where the cat sits (on the top crate, its east end)
CAN_SEAT = (356.0, -124.0)     # the tin can, on the top crate's west end
GUARD_DESK = (196.0, 276.0)
GUARD_LAMP = (212.0, -84.0)

# the vault door (north-looking)
VDOOR_R = 96.0
VDOOR_C = (540.0, -VDOOR_R - 14.0)
FRAME_R = 116.0
HINGE_X = VDOOR_C[0] + VDOOR_R + 6.0
DOOR_T = 44.0                  # the door's thickness
DIAL_C = (540.0, VDOOR_C[1] - 50.0)
DIAL_R = 19.0
WHEEL_C = VDOOR_C
WHEEL_R = 40.0
N_BOLTS = 12
VWALL_X = (300.0, 780.0)       # the vault's south wall face, seen from its corridor

# the vault inside (EAST-looking: u = plan y, north left)
VAULT_U = (430.0, 700.0)       # outer faces of the north and south walls
VAULT_IN = (460.0, 670.0)      # the room inside
VAULT_H = 236.0
BOX_U = (470.0, 662.0)         # the deposit wall's boxes: six columns (the plan's six rows)
BOX_ROWS = (-206.0, -36.0)     # ... and five rows
RUBY_BOX = (502.0, -138.0, 534.0, -104.0)    # column 1, row 2: the plan's RUBY (680, 518)
VDOOR_U = (670.0, 700.0)       # the door's opening in the south wall
TRAP_U = 600.0                 # the trapdoor (Plan B), under a floor tile
TILE_U = (578.0, 622.0)
VSLAB = 34.0                   # the vault's floor slab
BRANCH = (330.0, 520.0)        # the branch pipe under the vault: crown, invert
BRANCH_WATER = 500.0
GOLD_U = (466.0, 560.0)        # the gold, stacked on the near side (the plan's three stacks)
MANHOLE_B_U = 280.0            # manhole B in the back street (east-looking u)
HATCH_U = 1150.0


def shaft_rect(name):
    """The inside of a shaft (x0, y0, x1, y1) in set px, to clip a climber to it."""
    if name == "a":
        return (SHAFT_A[0], -400.0, SHAFT_A[1], PIPE[1])
    if name == "hatch":
        return (HATCH_SHAFT[0], -400.0, HATCH_SHAFT[1], PIPE[1])
    if name == "trap":
        return (TRAP_U - 24.0, -400.0, TRAP_U + 24.0, BRANCH[1])
    if name == "b":
        return (MANHOLE_B_U - 26.0, -400.0, MANHOLE_B_U + 26.0, BRANCH[1])
    raise ValueError(name)


# Plan A's route, seen from the front street (north-looking set px): along the curb from the
# car to manhole A (the plan's ROUTE_OUT[6:] walked backwards); then down shaft A, east along
# the pipe to the branch, up the hatch shaft into the store room, out of its door.
ROUTE_STREET = [(880.0, -8.0), (MANHOLE_X, -8.0)]
ROUTE_IN_E = [(MANHOLE_X, -8.0), (MANHOLE_X, WATER - 14.0), (HATCH_X, WATER - 14.0), (HATCH_X, -8.0), (500.0, -8.0)]


# ============================================================================ cut-paper helpers
@lru_cache(maxsize=8192)
def _rect_pts(x0, y0, x1, y1, seed, amp):
    return tuple(bass.orient(bass.cut_rect(x0, y0, x1, y1, seed=seed, amp=amp, seg=(30.0, 90.0)), True))


def rect(c, r, color, seed=0, amp=0.6, alpha=1.0):
    x0, y0, x1, y1 = r
    if amp <= 0.0:
        bass.fill_polys(c, [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]], color, alpha)
        return
    bass.fill_polys(c, [list(_rect_pts(round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1), seed, amp))], color,
                    alpha)


@lru_cache(maxsize=4096)
def _poly_pts(pts, seed, amp):
    return tuple(bass.orient(bass.cut(list(pts), seed=seed, amp=amp, seg=(24.0, 70.0)), True))


def poly(c, pts, color, seed=0, amp=0.5, alpha=1.0):
    bass.fill_polys(c, [list(_poly_pts(tuple((round(x, 1), round(y, 1)) for x, y in pts), seed, amp))], color, alpha)


@lru_cache(maxsize=4096)
def _disc_pts(x, y, r, seed, n):
    return tuple(bass.ring_pts((x, y), r, seed=seed, n=n, amp=min(0.8, 0.01 * r + 0.2)))


def disc(c, p, r, color, seed=0, n=None, alpha=1.0):
    if r <= 0.2:
        return
    n = n or int(clamp(r * 0.9, 16, 96))
    bass.fill_polys(c, [list(_disc_pts(round(p[0], 1), round(p[1], 1), round(r, 2), seed, n))], color, alpha)


def ring(c, p, r, w, color, seed=0, n=None, alpha=1.0):
    n = n or int(clamp(r * 0.9, 18, 96))
    bass.ring(c, p, r, w, color, seed=seed, n=n, alpha=alpha)


def band(c, a, b, w, color, seed=0, alpha=1.0):
    """A straight strip of paper from a to b, w wide (square ends)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * w / 2.0, dx / L * w / 2.0
    bass.fill_polys(c, [bass.orient([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny),
                                     (a[0] - nx, a[1] - ny)], True)], color, alpha)


def ellipse(c, p, rx, ry, color, alpha=1.0, n=48):
    if rx <= 0.05 or ry <= 0.05:
        return
    bass.fill_polys(c, [draw.ellipse_pts(p, rx, ry, n=n)], color, alpha)


def fill_all(c, color, alpha=1.0):
    """Paint the whole frame (works inside any transform)."""
    c.save()
    c.identity_matrix()
    c.rectangle(-10.0, -10.0, W * 4.0, H * 4.0)
    c.set_source_rgba(*color, alpha)
    c.fill()
    c.restore()


@contextmanager
def clipped(c, r):
    c.save()
    c.new_path()
    c.rectangle(r[0], r[1], r[2] - r[0], r[3] - r[1])
    c.clip()
    try:
        yield c
    finally:
        c.restore()


@contextmanager
def popped(c, base_y, u):
    """Pop-up: draw an element squashed onto its base line y = base_y (u 0 flat .. 1 standing,
    overshooting a little with outback). Yields False when there is nothing to draw."""
    g = ease("outback", clamp(u)) if u < 1.0 else 1.0
    if g <= 0.004:
        yield False
        return
    c.save()
    c.translate(0.0, base_y)
    c.scale(1.0, g)
    c.translate(0.0, -base_y)
    try:
        yield True
    finally:
        c.restore()


def _pop(pop, key):
    if pop is None:
        return 1.0
    return pop.get(key, 1.0)


# ============================================================================ the sky and the neighbours
def moon(c, u=1.0):
    if u <= 0.0:
        return
    g = ease("outback", clamp(u)) if u < 1.0 else 1.0
    disc(c, MOON_AT, 58.0 * g, K.PAPER, seed=3, n=64)


@lru_cache(maxsize=1)
def _neighbours():
    """The buildings either side of the bank and the far city behind: [(polys, colour)]."""
    out = []
    far = []
    x = -460.0
    i = 0
    while x < 1560.0:
        w = 90.0 + 120.0 * hash01(i, 31)
        top = -560.0 - 420.0 * hash01(i, 32)
        far.append(bass.cut_rect(x, top, x + w, 40.0, seed=300 + i, amp=0.8))
        x += w + 4.0
        i += 1
    out.append((far, lerp(K.NAVY, K.STEEL, 0.16)))
    left = [bass.cut_rect(-460.0, -470.0, FACADE_X[0], 20.0, seed=320, amp=0.8),
            bass.cut_rect(-460.0, -486.0, FACADE_X[0] + 4.0, -470.0, seed=321, amp=0.5)]
    out.append((left, NEIGH))
    lw = []
    for row in range(3):
        for col in range(5):
            x0 = -420.0 + col * 128.0
            y0 = -420.0 + row * 140.0
            if x0 + 48.0 < FACADE_X[0] - 30.0:
                lw.append(bass.cut_rect(x0, y0, x0 + 48.0, y0 + 82.0, seed=330 + row * 7 + col, amp=0.5))
    out.append((lw, NEIGH_DK))
    right = [bass.cut_rect(ALLEY_X[1], -900.0, 1560.0, 20.0, seed=340, amp=0.8),
             bass.cut_rect(ALLEY_X[1] - 4.0, -916.0, 1560.0, -900.0, seed=341, amp=0.5)]
    out.append((right, NEIGH))
    rw = []
    for row in range(5):
        for col in range(4):
            x0 = ALLEY_X[1] + 40.0 + col * 120.0
            y0 = -850.0 + row * 150.0
            rw.append(bass.cut_rect(x0, y0, x0 + 50.0, y0 + 86.0, seed=350 + row * 5 + col, amp=0.5))
    out.append((rw, NEIGH_DK))
    return out


def neighbours(c, u=1.0):
    with popped(c, 0.0, u) as ok:
        if ok:
            for polys, col in _neighbours():
                bass.fill_polys(c, polys, col)


# ============================================================================ the bank's front
@lru_cache(maxsize=1)
def _wing():
    """The plain wing (x 170..560): wall, rusticated base, frieze, three barred windows."""
    x0, x1 = FACADE_X[0], PORTICO_X[0]
    out = [([bass.cut_rect(x0, -FACADE_H, x1 + 6.0, 0.0, seed=401, amp=0.7)], STONE)]
    joints = []
    for i in range(1, 4):                                    # rustication: the base's courses
        y = -16.0 * i
        joints.append(bass.cut_rect(x0, y - 1.6, x1, y + 1.6, seed=402 + i, amp=0.3))
    for xj in range(int(x0) + 46, int(x1), 74):
        for i in range(4):
            xx = xj + (37.0 if i % 2 else 0.0)
            if xx < x1 - 6:
                joints.append(bass.cut_rect(xx - 1.4, -16.0 * (i + 1), xx + 1.4, -16.0 * i, seed=410 + i + xj, amp=0.2))
    out.append((joints, STONE_DK))
    out.append(([bass.cut_rect(x0, -FACADE_H + 40.0, x1, -FACADE_H + 52.0, seed=420, amp=0.4)], STONE_SH))
    wins, bars, sills = [], [], []
    for i, cx in enumerate((256.0, 366.0, 476.0)):
        w, top, bot = 58.0, -452.0, -188.0
        pts = [(cx - w / 2, bot), (cx - w / 2, top + 22.0)]
        for k in range(1, 8):
            a = math.pi * k / 8.0
            pts.append((cx - w / 2 * math.cos(a), top + 22.0 - 22.0 * math.sin(a)))
        pts.append((cx + w / 2, top + 22.0))
        pts.append((cx + w / 2, bot))
        wins.append(bass.cut(pts, seed=430 + i, amp=0.4, seg=(20.0, 50.0)))
        for k in (-1, 0, 1):
            bars.append(bass.cut_rect(cx + k * 15.0 - 1.8, top + 6.0, cx + k * 15.0 + 1.8, bot, seed=440 + i * 3 + k, amp=0.2))
        bars.append(bass.cut_rect(cx - w / 2, -330.0, cx + w / 2, -326.0, seed=446 + i, amp=0.2))
        sills.append(bass.cut_rect(cx - w / 2 - 8.0, bot, cx + w / 2 + 8.0, bot + 8.0, seed=450 + i, amp=0.3))
        sills.append(bass.cut_rect(cx - 9.0, top - 14.0, cx + 9.0, top + 6.0, seed=455 + i, amp=0.3))   # keystone
    out.append((wins, K.INK))
    out.append((bars, lerp(K.STEEL, K.INK, 0.25)))
    out.append((sills, STONE))
    return out


@lru_cache(maxsize=1)
def _portico():
    """The portico (x 560..910): the shadowed wall behind, the doors, the four columns."""
    x0, x1 = PORTICO_X
    out = [([bass.cut_rect(x0 - 6.0, -FACADE_H, x1, STEPS_Y, seed=461, amp=0.6)], STONE_SH)]
    d0, d1 = DOOR_X
    out.append(([bass.cut_rect(d0, -292.0, d1, STEPS_Y, seed=462, amp=0.4)], K.INK))
    panels = []
    for k, (a, b) in enumerate(((d0 + 8.0, (d0 + d1) / 2 - 3.0), ((d0 + d1) / 2 + 3.0, d1 - 8.0))):
        panels.append(bass.cut_rect(a, -270.0, b, -170.0, seed=463 + k, amp=0.3))
        panels.append(bass.cut_rect(a, -150.0, b, STEPS_Y - 12.0, seed=465 + k, amp=0.3))
    out.append((panels, lerp(K.INK, K.NAVY, 0.6)))
    out.append(([bass.cut_rect(d0 - 14.0, -312.0, d1 + 14.0, -292.0, seed=467, amp=0.4)], STONE))
    lun = [(d0 + 10.0, -330.0)]
    for k in range(1, 10):
        a = math.pi * k / 10.0
        lun.append(((d0 + d1) / 2 - (d1 - d0 - 20.0) / 2 * math.cos(a), -330.0 - 40.0 * math.sin(a)))
    lun.append((d1 - 10.0, -330.0))
    out.append(([bass.cut(lun, seed=468, amp=0.3, seg=(18.0, 40.0))], K.INK))
    out.append(([bass.cut_rect(x0 - 6.0, STEPS_Y, x1, 0.0, seed=469, amp=0.4)], STONE_DK))
    cols, flutes = [], []
    for i, cx in enumerate(COLS):
        w = COL_W
        top, bot = -FACADE_H + 62.0, STEPS_Y
        cols.append(bass.cut([(cx - w / 2 + 3.0, top), (cx + w / 2 - 3.0, top), (cx + w / 2, bot), (cx - w / 2, bot)],
                             seed=470 + i, amp=0.3, seg=(40.0, 120.0)))
        cols.append(bass.cut_rect(cx - w / 2 - 7.0, bot - 12.0, cx + w / 2 + 7.0, bot, seed=475 + i, amp=0.3))
        cols.append(bass.cut_rect(cx - w / 2 - 9.0, top - 14.0, cx + w / 2 + 9.0, top, seed=480 + i, amp=0.3))
        cols.append(bass.cut_rect(cx - w / 2 - 4.0, top, cx + w / 2 + 4.0, top + 7.0, seed=485 + i, amp=0.3))
        for k in (-1, 1):
            flutes.append(bass.cut_rect(cx + k * 8.0 - 1.5, top + 12.0, cx + k * 8.0 + 1.5, bot - 16.0, seed=490 + i * 2 + k,
                                        amp=0.2))
        flutes.append(bass.cut_rect(cx + w / 2 - 9.0, top + 10.0, cx + w / 2 - 1.0, bot - 14.0, seed=497 + i, amp=0.3))
    out.append((cols, STONE))
    out.append((flutes, STONE_SH))
    return out


@lru_cache(maxsize=1)
def _entablature():
    x0, x1 = FACADE_X
    return [([bass.cut_rect(x0 - 10.0, -FACADE_H - 12.0, x1 + 10.0, -FACADE_H + 6.0, seed=501, amp=0.5)], STONE),
            ([bass.cut_rect(x0 - 4.0, -FACADE_H + 6.0, x1 + 4.0, -FACADE_H + 14.0, seed=502, amp=0.3)], STONE_DK),
            ([bass.cut_rect(PORTICO_X[0] - 6.0, -FACADE_H + 14.0, x1, -FACADE_H + 52.0, seed=503, amp=0.4)], STONE),
            ([bass.cut_rect(PORTICO_X[0] - 6.0, -FACADE_H + 52.0, x1, -FACADE_H + 58.0, seed=504, amp=0.3)], STONE_DK)]


@lru_cache(maxsize=1)
def _pediment():
    x0, x1 = PORTICO_X[0] - 14.0, FACADE_X[1] + 12.0
    apex = ((x0 + x1) / 2.0, -FACADE_H - 12.0 - PED_H)
    base = -FACADE_H - 12.0
    outer = bass.cut([(x0, base), (apex[0], apex[1]), (x1, base)], seed=511, amp=0.5, seg=(30.0, 80.0))
    k = 0.78
    inner = [(lerp(apex[0], x0, k) + 14.0, base - 8.0), (apex[0], apex[1] + 22.0), (lerp(apex[0], x1, k) - 14.0, base - 8.0)]
    return [([outer], STONE), ([bass.cut(inner, seed=512, amp=0.4, seg=(30.0, 80.0))], STONE_SH)]


def clock(c, t, u=1.0):
    """The round clock in the pediment: a paper face, twelve ticks, the hands at ten to two."""
    if u <= 0.0:
        return
    g = ease("outback", clamp(u)) if u < 1.0 else 1.0
    p, r = CLOCK_AT, 34.0 * g
    disc(c, p, r + 6.0, STONE_DK, seed=520, n=48)
    disc(c, p, r, K.PAPER, seed=521, n=48)
    for i in range(12):
        a = math.radians(i * 30.0 - 90.0)
        L = 0.2 if i % 3 == 0 else 0.11
        band(c, (p[0] + r * (0.92 - L) * math.cos(a), p[1] + r * (0.92 - L) * math.sin(a)),
             (p[0] + r * 0.92 * math.cos(a), p[1] + r * 0.92 * math.sin(a)), 2.4 if i % 3 == 0 else 1.6, K.INK, seed=522 + i)
    for ang, L, w in ((1.0 * 30.0 + 25.0, 0.52, 4.0), (50.0 * 6.0, 0.8, 2.8)):
        a = math.radians(ang - 90.0)
        band(c, p, (p[0] + L * r * math.cos(a), p[1] + L * r * math.sin(a)), w, K.INK, seed=530)
    disc(c, p, 2.6, K.INK, seed=531, n=10)


@lru_cache(maxsize=1)
def _steps():
    return [bass.cut_rect(DOOR_X[0] - 8.0 - 12.0 * (2 - i), -STEP_H * i - STEP_H, DOOR_X[1] + 8.0 + 12.0 * (2 - i),
                          -STEP_H * i, seed=540 + i, amp=0.3) for i in range(3)]


def facade(c, t, pop=None, chalk=0.0):
    """The bank's front (back to front: wing, portico, entablature, pediment, clock, steps)."""
    with popped(c, 0.0, _pop(pop, "facade")) as ok:
        if ok:
            for polys, col in _wing():
                bass.fill_polys(c, polys, col)
            for polys, col in _entablature():
                bass.fill_polys(c, polys, col)
    with popped(c, 0.0, _pop(pop, "portico")) as ok:
        if ok:
            for polys, col in _portico():
                bass.fill_polys(c, polys, col)
            bass.fill_polys(c, _steps(), STONE)
            for i in range(3):
                y = -STEP_H * i
                band(c, (DOOR_X[0] - 8.0 - 12.0 * (2 - i), y - 1.0), (DOOR_X[1] + 8.0 + 12.0 * (2 - i), y - 1.0), 2.0,
                     STONE_DK, seed=545 + i)
    with popped(c, -FACADE_H - 12.0, _pop(pop, "pediment")) as ok:
        if ok:
            for polys, col in _pediment():
                bass.fill_polys(c, polys, col)
    clock(c, t, _pop(pop, "clock"))
    if chalk > 0.0:
        x0, x1 = FACADE_X
        K.chalk_line(c, [(x0, 0.0), (x0, -FACADE_H), (x1, -FACADE_H), (x1, 0.0)], 1.0, 3.0, K.PAPER, seed=550,
                     alpha=0.9 * chalk)


# ============================================================================ the street furniture
@lru_cache(maxsize=1)
def _lamp_polys():
    x, top = LAMP_X, -330.0
    post = [bass.orient([(x - 5.0, 0.0), (x + 5.0, 0.0), (x + 3.5, top + 20.0), (x - 3.5, top + 20.0)], True),
            bass.cut_rect(x - 14.0, -16.0, x + 14.0, 0.0, seed=601, amp=0.3),
            bass.cut_rect(x - 9.0, -40.0, x + 9.0, -16.0, seed=602, amp=0.3),
            bass.orient([(x - 18.0, top + 22.0), (x + 18.0, top + 22.0), (x + 12.0, top + 30.0), (x - 12.0, top + 30.0)], True),
            bass.orient([(x - 20.0, top - 8.0), (x + 20.0, top - 8.0), (x + 4.0, top - 30.0), (x - 4.0, top - 30.0)], True),
            bass.orient([(x - 2.0, top - 30.0), (x + 2.0, top - 30.0), (x + 2.0, top - 40.0), (x - 2.0, top - 40.0)], True)]
    glass = bass.orient([(x - 15.0, top - 8.0), (x + 15.0, top - 8.0), (x + 11.0, top + 22.0), (x - 11.0, top + 22.0)], True)
    beam = bass.orient([(x - 12.0, top + 30.0), (x + 12.0, top + 30.0), (x + 150.0, 0.0), (x - 150.0, 0.0)], True)
    return post, glass, beam


def street_lamp(c, u=1.0, on=1.0):
    """The cast-iron lamp on the sidewalk, its gold lantern and the flat light it throws."""
    post, glass, beam = _lamp_polys()
    with popped(c, 0.0, u) as ok:
        if not ok:
            return
        if on > 0.0:
            bass.fill_polys(c, [beam], K.GOLD, 0.10 * on)
            ellipse(c, (LAMP_X, 0.0), 168.0, 10.0, K.GOLD, 0.22 * on, n=40)
        bass.fill_polys(c, post, K.INK)
        bass.fill_polys(c, [glass], lerp(K.INK, K.GOLD, 0.25 + 0.75 * on))
        band(c, (LAMP_X, -338.0), (LAMP_X, -308.0), 2.0, K.INK, seed=603)


@lru_cache(maxsize=1)
def _car_polys():
    """The car in profile, nose west, centred on x = 0 (wheels on y = 0)."""
    L = CAR_L
    x0, x1 = -L / 2, L / 2
    body = [(x0 + 8.0, -14.0), (x0, -26.0), (x0 + 4.0, -44.0), (x0 + 30.0, -50.0), (x0 + 66.0, -54.0),
            (x0 + 92.0, -86.0), (x0 + 112.0, -94.0), (x1 - 82.0, -94.0), (x1 - 60.0, -84.0), (x1 - 36.0, -58.0),
            (x1 - 6.0, -52.0), (x1, -38.0), (x1 - 4.0, -14.0)]
    rim = bass.orient(bass.cut([(px, py - 3.0) for px, py in body], seed=611, amp=0.3, seg=(30, 70)), True)
    shell = bass.orient(bass.cut(body, seed=612, amp=0.3, seg=(30, 70)), True)
    wins = [bass.orient([(x0 + 98.0, -84.0), (x0 + 116.0, -90.0), (x0 + 150.0, -90.0), (x0 + 150.0, -60.0),
                         (x0 + 84.0, -60.0)], True),
            bass.orient([(x0 + 156.0, -90.0), (x1 - 84.0, -90.0), (x1 - 66.0, -78.0), (x1 - 52.0, -60.0),
                         (x0 + 156.0, -60.0)], True)]
    return rim, shell, wins


def car(c, t, headlights=0.0, u=1.0, x=CAR_X, door=0.0):
    """The getaway car in profile at the alley mouth, nose to the west (left). headlights 0..1
    (they flare on with a small overshoot), the RED tail light always on."""
    with popped(c, 0.0, u) as ok:
        if not ok:
            return
        rim, shell, wins = _car_polys()
        L = CAR_L
        x0, x1 = -L / 2, L / 2
        c.save()
        c.translate(x, 0.0)
        on = clamp(headlights)
        if on > 0.0:
            g = ease("outback", on) if on < 1.0 else 1.0
            reach = 380.0 * g
            bass.fill_polys(c, [bass.orient([(x0 + 4.0, -38.0), (x0 + 4.0, -26.0), (x0 - reach, 6.0), (x0 - reach, -70.0)],
                                            True)], K.PAPER, 0.12 * on)
            bass.fill_polys(c, [bass.orient([(x0 + 4.0, -36.0), (x0 + 4.0, -28.0), (x0 - reach * 0.7, -4.0),
                                             (x0 - reach * 0.7, -50.0)], True)], K.PAPER, 0.12 * on)
            ellipse(c, (x0 - reach * 0.55, 0.0), reach * 0.5, 6.0, K.PAPER, 0.18 * on, n=32)
        bass.fill_polys(c, [rim], K.STEEL)
        bass.fill_polys(c, [shell], K.INK)
        bass.fill_polys(c, wins, GLASS)
        if door > 0.0:                                       # the rear door swung open (toward us)
            g = clamp(door)
            bass.fill_polys(c, [[(x0 + 156.0, -88.0), (x0 + 220.0, -88.0), (x0 + 220.0, -20.0), (x0 + 156.0, -20.0)]],
                            K.DEEP, g)
            bass.fill_polys(c, [bass.orient([(x0 + 152.0, -92.0), (x0 + 156.0 + 70.0 * (1 - g), -92.0),
                                             (x0 + 156.0 + 70.0 * (1 - g), -16.0), (x0 + 152.0, -16.0)], True)], K.INK)
            band(c, (x0 + 152.0, -92.0), (x0 + 152.0, -16.0), 3.0, K.STEEL, seed=619)
        band(c, (x0 - 4.0, -18.0), (x0 + 18.0, -18.0), 6.0, K.STEEL, seed=613)
        band(c, (x1 - 16.0, -18.0), (x1 + 4.0, -18.0), 6.0, K.STEEL, seed=614)
        band(c, (x0 + 30.0, -40.0), (x1 - 30.0, -40.0), 2.2, lerp(K.STEEL, K.INK, 0.3), seed=615)
        for i, wx in enumerate((x0 + 52.0, x1 - 50.0)):
            disc(c, (wx, -18.0), 20.0, K.INK, seed=640 + i, n=28)
            disc(c, (wx, -18.0), 8.0, K.STEEL, seed=642 + i, n=16)
        disc(c, (x0 + 4.0, -32.0), 6.5, lerp(lerp(K.STEEL, K.INK, 0.3), K.PAPER, on), seed=616, n=14)
        if on > 0.0:
            disc(c, (x0 + 4.0, -32.0), 16.0 * (0.7 + 0.5 * ease("outback", on)), K.PAPER, seed=617, n=24, alpha=0.25 * on)
        disc(c, (x1 - 2.0, -36.0), 5.0, K.RED, seed=618, n=12)
        c.restore()


def alarm_bell(c, ring_=0.0, t=0.0):
    """The alarm bell on the side door's wall, seen high in the alley. ring_ > 0: it rocks."""
    rock = 14.0 * math.sin(t * 2.0 * math.pi * 9.0) * clamp(ring_)
    band(c, (BELL_SET[0] - 22.0, BELL_SET[1] - 20.0), (BELL_SET[0] + 22.0, BELL_SET[1] - 20.0), 4.0, K.INK, seed=621)
    K.bell(c, BELL_SET, 1.1, lerp(K.STEEL, K.RED, clamp(ring_)), seed=620, ring=rock)


@lru_cache(maxsize=1)
def _alley():
    x0, x1 = ALLEY_X
    return [([bass.cut_rect(x0, -FACADE_H - 4.0, x1, 0.0, seed=630, amp=0.5)], K.INK),
            ([bass.cut_rect(x0, -FACADE_H, x0 + 8.0, 0.0, seed=631, amp=0.3)], STONE_SH),
            ([bass.cut_rect(x1 - 18.0, -FACADE_H + 30.0, x1 - 12.0, 0.0, seed=632, amp=0.2)], lerp(K.INK, K.STEEL, 0.3))]


# ============================================================================ the ground and what is under it
LID_L = 2.0 * MANHOLE_R + 10.0                 # the lid's diameter (it overlaps the rim 5 px each side)
LID_HOME = MANHOLE_X + MANHOLE_R + 5.0           # its east edge, shut


def lid_pose(lid):
    """(pivot_x, angle): manhole A's lid as its east edge on the road (pivot_x) and how far its
    west edge is raised off the road about that edge (degrees). lid is a number (the canned move:
    0 shut .. 0.35 levered up on the east edge .. 0.8 dragged west out of the hole .. 1 dropped
    flat west of it) or already a (pivot_x, angle) pair (a scene driving it from a hand)."""
    if isinstance(lid, tuple):
        return lid
    u = clamp(lid)
    if u < 0.35:
        return LID_HOME, 35.0 * ease("out", u / 0.35)
    if u < 0.8:
        g = ease("inout", (u - 0.35) / 0.45)
        return lerp(LID_HOME, MANHOLE_X - MANHOLE_R + 2.0, g), lerp(35.0, 55.0, g)
    g = (u - 0.8) / 0.2
    return lerp(MANHOLE_X - MANHOLE_R + 2.0, MANHOLE_X - MANHOLE_R - 4.0, g), 55.0 * (1.0 - g * g)


def lid_edge(lid):
    """Where the lid's raised (west) edge is, set px (for a hand on it)."""
    px, ang = lid_pose(lid)
    a = math.radians(ang)
    return (px - LID_L * math.cos(a), 1.5 - LID_L * math.sin(a))


def manhole_lid(c, lid):
    """Manhole A's cast-iron lid on the road (see lid_pose)."""
    px, ang = lid_pose(lid)
    if ang <= 0.01 and abs(px - LID_HOME) < 0.5:
        band(c, (px - LID_L, 1.5), (px, 1.5), 8.0, LID, seed=701)
        for k in (-1, 0, 1):
            band(c, (MANHOLE_X + k * 15.0 - 4.0, 1.5), (MANHOLE_X + k * 15.0 + 4.0, 1.5), 3.0, K.INK, seed=702 + k)
        return
    c.save()
    c.translate(px, 1.5)
    c.rotate(math.radians(ang))
    band(c, (-LID_L - 2.0, 0.0), (2.0, 0.0), 13.0, K.INK, seed=705)
    band(c, (-LID_L, 0.0), (0.0, 0.0), 9.0, LID_LIT, seed=703)
    band(c, (-LID_L + 6.0, -2.0), (-6.0, -2.0), 2.0, lerp(LID_LIT, K.INK, 0.45), seed=704)
    c.restore()


def ground(c, t, cut=0.0, lid=0.0, view_x=(-600.0, 1700.0)):
    """The street's ground in section (north-looking): solid earth, cut open by `cut` to show
    shaft A and the sewer pipe; the road slab; manhole A."""
    x0, x1 = view_x
    rect(c, (x0, 0.0, x1, 1600.0), EARTH, amp=0.0)
    if cut > 0.0:
        _underground_main(c, t, cut)
    band(c, (x0, 1.0), (x1, 1.0), 4.0, lerp(K.STEEL, K.NAVY, 0.25), seed=711)
    if cut > 0.0:
        a = clamp(cut * 3.0)
        rect(c, (x0, 3.0, x1, ROAD), SLAB, amp=0.0, alpha=a)
        rect(c, (SHAFT_A[0], -1.0, SHAFT_A[1], ROAD + 2.0), TUNNEL, amp=0.0, alpha=a)
    manhole_lid(c, lid)


def _rungs(c, x0, x1, y0, y1, seed=0, color=IRON):
    """Iron rungs up a shaft from its bottom y1 to its top y0 (one every RUNG_STEP above y1),
    and the rails they hang on."""
    band(c, (x0 + 6.0, y0), (x0 + 6.0, y1), 3.0, lerp(IRON, K.NAVY, 0.4), seed=seed)
    band(c, (x1 - 6.0, y0), (x1 - 6.0, y1), 3.0, lerp(IRON, K.NAVY, 0.4), seed=seed + 1)
    y = y1 - RUNG_STEP
    i = 0
    while y > y0 + 2.0:
        band(c, (x0 + 4.0, y), (x1 - 4.0, y), 4.0, color, seed=seed + 2 + i)
        y -= RUNG_STEP
        i += 1


def _pipe_run(c, x0, x1, crown, invert, water, seed=0, joints=130.0):
    rect(c, (x0, crown - 10.0, x1, invert + 10.0), LINING, amp=0.0)
    rect(c, (x0, crown, x1, invert), TUNNEL, amp=0.0)
    jx = math.floor(x0 / joints) * joints + 40.0
    while jx < x1:
        if x0 < jx < x1:
            band(c, (jx, crown), (jx, water), 2.0, lerp(TUNNEL, K.INK, 0.45), seed=seed + int(jx) % 97)
        jx += joints
    rect(c, (x0, water, x1, invert), K.INK, amp=0.0)
    band(c, (x0, water + 1.0), (x1, water + 1.0), 2.4, lerp(K.STEEL, K.NAVY, 0.35), seed=seed + 1)


def _underground_main(c, t, cut):
    """Shaft A, the pipe along the street and the hatch shaft, revealed by cut (0..1): the
    shaft opens top-down first (0..0.45), then the pipe from the shaft outward (0.45..1)."""
    a = clamp(cut / 0.45)
    b = clamp((cut - 0.45) / 0.55)
    if b > 0.0:
        half = 1500.0 * ease("out3", b) + 40.0
        px0, px1 = MANHOLE_X - half, MANHOLE_X + half
        _pipe_run(c, px0, px1, PIPE[0], PIPE[1], WATER, seed=720)
        if px0 < HATCH_X < px1:
            # the branch north: a dark arch in the back of the pipe, and the hatch shaft above it
            arch = [(HATCH_X - 38.0, WATER)]
            for k in range(0, 11):
                ang = math.pi * k / 10.0
                arch.append((HATCH_X - 38.0 * math.cos(ang), PIPE[0] + 52.0 - 44.0 * math.sin(ang)))
            arch.append((HATCH_X + 38.0, WATER))
            poly(c, arch, lerp(TUNNEL, K.INK, 0.6), seed=722, amp=0.3)
            rect(c, (HATCH_SHAFT[0], ROAD, HATCH_SHAFT[1], PIPE[0] + 6.0), TUNNEL, amp=0.0)
            _rungs(c, HATCH_SHAFT[0], HATCH_SHAFT[1], 0.0, WATER, seed=726)
        if b < 1.0:
            for xx in (px0, px1):
                K.chalk_line(c, [(xx, PIPE[0] - 10.0), (xx, PIPE[1] + 10.0)], 1.0, 2.5, K.PAPER, seed=727, alpha=0.8)
    if a > 0.0:
        bot = lerp(0.0, PIPE[0] + 6.0, ease("out3", a))
        rect(c, (SHAFT_A[0], 0.0, SHAFT_A[1], bot), TUNNEL, amp=0.0)
        c.save()
        c.rectangle(SHAFT_A[0], -2.0, SHAFT_A[1] - SHAFT_A[0], bot + 2.0 if b <= 0.0 else WATER + 2.0)
        c.clip()
        _rungs(c, SHAFT_A[0], SHAFT_A[1], 0.0, WATER, seed=731)
        c.restore()
        if a < 1.0 or b < 0.3:
            al = 1.0 - clamp((b - 0.1) / 0.2)
            for i, xx in enumerate(SHAFT_A):
                K.chalk_line(c, [(xx, 0.0), (xx, bot)], 1.0, 2.5, K.PAPER, seed=732 + i, alpha=0.8 * al)


def open_rects(cut, above=True):
    """The parts of the street's section that are open at `cut` (see front_street), set px
    rects: above the road (if `above`), shaft A as far as it has opened, the pipe as far as it
    has opened (and the hatch shaft once the pipe reaches it). Clip a climber to these."""
    out = [(-3000.0, -3000.0, 4000.0, 0.0)] if above else []
    a = clamp(cut / 0.45)
    b = clamp((cut - 0.45) / 0.55)
    if a > 0.0:
        bot = lerp(0.0, PIPE[0] + 6.0, ease("out3", a))
        out.append((SHAFT_A[0], -2.0, SHAFT_A[1], bot if b <= 0.0 else PIPE[1]))
    if b > 0.0:
        half = 1500.0 * ease("out3", b) + 40.0
        out.append((MANHOLE_X - half, PIPE[0], MANHOLE_X + half, PIPE[1] + 10.0))
        if MANHOLE_X - half < HATCH_X < MANHOLE_X + half:
            out.append((HATCH_SHAFT[0], -2.0, HATCH_SHAFT[1], PIPE[1]))
    return out


@contextmanager
def clip_open(c, cut, above=True):
    """Clip to open_rects(cut) (in the space c is in: call inside cam.on)."""
    c.save()
    c.new_path()
    for x0, y0, x1, y1 in open_rects(cut, above):
        c.rectangle(x0, y0, x1 - x0, y1 - y0)
    c.clip()
    try:
        yield c
    finally:
        c.restore()


# drip sources: (x, period, phase)
_DRIPS_MAIN = tuple((x, 1.1 + 0.9 * hash01(i, 801), 3.0 * hash01(i, 802))
                    for i, x in enumerate((96.0, 178.0, 318.0, 392.0, 514.0, 606.0, 688.0, 812.0, 930.0)))
_DRIPS_BRANCH = tuple((x, 1.0 + 1.0 * hash01(i, 811), 3.0 * hash01(i, 812))
                      for i, x in enumerate((236.0, 318.0, 402.0, 478.0, 556.0, 648.0, 760.0, 868.0, 990.0, 1090.0,
                                             1210.0, 1330.0)))
G_DRIP = 2600.0                                            # set px / s^2


def _fall_time(top, water):
    return math.sqrt(2.0 * (water - top - 8.0) / G_DRIP)


def drip_times(t0, t1, view="main"):
    """Every drip that hits the water between scene times t0 and t1: [(t, x)] (for the cues)."""
    src, top, water = (_DRIPS_MAIN, PIPE[0], WATER) if view == "main" else (_DRIPS_BRANCH, BRANCH[0], BRANCH_WATER)
    ft = _fall_time(top, water)
    out = []
    for x, per, ph in src:
        k = math.ceil((t0 - ft - ph) / per)
        while True:
            hit = ph + k * per + ft
            if hit > t1:
                break
            if hit >= t0:
                out.append((round(hit, 4), x))
            k += 1
    return sorted(out)


def _drips(c, t, src, top, water, x0, x1):
    ft = _fall_time(top, water)
    for i, (x, per, ph) in enumerate(src):
        if not x0 - 20.0 < x < x1 + 20.0:
            continue
        k = math.floor((t - ph) / per)
        s = t - (ph + k * per)                              # time since this drop let go
        if s > per - 0.5:                                   # the next drop swelling on the crown
            r = 2.0 + 3.0 * clamp((s - per + 0.5) / 0.5)
            disc(c, (x, top + 3.0 + r), r, K.PAPER, seed=820 + i, n=10, alpha=0.75)
        if s < ft:                                          # falling
            y = top + 8.0 + 0.5 * G_DRIP * s * s
            L = 6.0 + 10.0 * clamp(s / ft)
            bass.fill_polys(c, [bass.orient([(x, y - L), (x + 2.6, y - 1.0), (x, y + 2.4), (x - 2.6, y - 1.0)], True)],
                            K.PAPER, 0.8)
        elif s < ft + 0.7:                                  # the ring on the black water
            a = (s - ft) / 0.7
            _water_ring(c, (x, water + 1.0), a, 40.0)
            if s < ft + 0.12:                               # the splash: two flecks up
                h = 10.0 * math.sin(math.pi * (s - ft) / 0.12)
                for d in (-1, 1):
                    disc(c, (x + d * 5.0, water - h), 1.6, K.PAPER, seed=830 + i + d, n=8, alpha=0.8)


def _water_ring(c, p, a, size):
    rx = 6.0 + size * ease("out3", a)
    pts = draw.ellipse_pts(p, rx, rx * 0.16, n=28)
    inner = draw.ellipse_pts(p, max(1.0, rx - 2.6 * (1 - a) - 0.6), max(0.4, (rx - 2.6) * 0.16), n=28)
    bass.fill_polys(c, [bass.orient(pts, True), bass.orient(inner, False)], K.PAPER, 0.7 * (1.0 - a))


def water(c, cam, t, view="main", x0=None, x1=None):
    """The water's near edge, drawn after figures standing in the pipe: their feet are in it."""
    vx0, vy0, vx1, vy1 = cam.view(40.0)
    x0 = vx0 if x0 is None else x0
    x1 = vx1 if x1 is None else x1
    wl, inv = (WATER, PIPE[1]) if view == "main" else (BRANCH_WATER, BRANCH[1])
    with cam.on(c):
        rect(c, (x0, wl + 2.0, x1, inv), K.INK, amp=0.0)
        band(c, (x0, wl + 1.5), (x1, wl + 1.5), 2.4, lerp(K.STEEL, K.NAVY, 0.35), seed=741)


def splash(c, cam, p, t, t0, s=1.0):
    """A footstep in the water at set point p: a ring spreading and two flecks (from t0)."""
    a = (t - t0) / 0.6
    if not 0.0 <= a < 1.0:
        return
    with cam.on(c):
        _water_ring(c, (p[0], p[1] + 1.5), a, 30.0 * s)
        if a < 0.25:
            h = 14.0 * s * math.sin(math.pi * a / 0.25)
            for d in (-1, 1):
                disc(c, (p[0] + d * 7.0 * s, p[1] - h), 1.8 * s, K.PAPER, seed=750 + d, n=8, alpha=0.85)


# ============================================================================ above ground, cut open
def _store_room(c, t, hatch=0.0):
    """The store room in section (north-looking): its dark back wall, the shelves and boxes, the
    door to the corridor on the right, the floor slab with the hatch in it."""
    x0, x1 = STORE_X
    rect(c, (x0, -ROOM_H, x1, 0.0), ROOM, amp=0.0)
    shelf = []
    for k in range(3):
        y = -60.0 - 62.0 * k
        shelf.append(bass.cut_rect(200.0, y - 4.0, 330.0, y, seed=910 + k, amp=0.3))
    shelf.append(bass.cut_rect(200.0, -200.0, 205.0, 0.0, seed=914, amp=0.2))
    shelf.append(bass.cut_rect(325.0, -200.0, 330.0, 0.0, seed=915, amp=0.2))
    for k, (bx, by, bw, bh) in enumerate(((210.0, -64.0, 40.0, 30.0), (262.0, -64.0, 54.0, 40.0), (214.0, -126.0, 60.0, 28.0),
                                          (282.0, -126.0, 34.0, 44.0), (230.0, -188.0, 50.0, 36.0))):
        shelf.append(bass.cut_rect(bx, by - bh, bx + bw, by, seed=916 + k, amp=0.3))
    shelf.append(bass.cut_rect(352.0, -70.0, 404.0, 0.0, seed=922, amp=0.4))
    shelf.append(bass.cut_rect(360.0, -118.0, 398.0, -70.0, seed=923, amp=0.4))
    bass.fill_polys(c, shelf, K.INK)
    # the door to the corridor, ajar: a slot of the corridor's dark
    rect(c, (482.0, -190.0, 495.0, 0.0), lerp(ROOM, K.STEEL, 0.25), amp=0.2)
    rect(c, (x0, -ROOM_H - 26.0, x1 + 10.0, -ROOM_H), K.INK, amp=0.3)                  # the ceiling
    rect(c, (x0 - 16.0, -ROOM_H - 26.0, x0, 0.0), K.INK, amp=0.3)                      # the outer wall, cut
    rect(c, (x1, -ROOM_H - 26.0, x1 + 10.0, -196.0), K.INK, amp=0.3)                   # over the door
    rect(c, (x0 - 16.0, 0.0, x1 + 10.0, ROAD), SLAB, amp=0.3)
    rect(c, (HATCH_SHAFT[0], -1.0, HATCH_SHAFT[1], ROAD + 2.0), TUNNEL, amp=0.0)
    hatch_lid(c, hatch)


def _bank_section(c, t, hatch=0.0, x_range=(FACADE_X[0], FACADE_X[1])):
    """The bank cut open along the street (north-looking): dark rooms, cut walls."""
    x0, x1 = x_range
    rect(c, (x0, -FACADE_H, x1, 0.0), K.INK, amp=0.0)
    rect(c, (505.0, -ROOM_H, 575.0, 0.0), ROOM, amp=0.0)
    rect(c, (585.0, -ROOM_H, 894.0, 0.0), lerp(ROOM, K.NAVY, 0.4), amp=0.0)
    _store_room(c, t, hatch)


def hatch_lid(c, u):
    """The hatch's lid in the store room floor, hinged on its west edge: u 0 shut .. 1 thrown open."""
    hx = HATCH_SHAFT[0] - 2.0
    ang = 104.0 * (ease("outback", clamp(u)) if u < 1.0 else 1.0)
    c.save()
    c.translate(hx, 0.0)
    c.rotate(math.radians(-ang))
    rect(c, (0.0, -4.0, HATCH_SHAFT[1] - HATCH_SHAFT[0] + 4.0, 5.0), lerp(K.STEEL, K.INK, 0.2), amp=0.3)
    band(c, (8.0, -4.0), (8.0, 5.0), 3.0, K.INK, seed=931)
    c.restore()


WINDOW = (STORE_X[0], -ROOM_H - 26.0, STORE_X[1] + 10.0, 0.0)


def window_rect(u):
    """The cutaway window round the store room, opening out from the hatch (u 0..1)."""
    g = ease("out3", clamp(u))
    x0, y0, x1, y1 = WINDOW
    return (lerp(HATCH_X - 30.0, x0, g), lerp(-40.0, y0, g), lerp(HATCH_X + 30.0, x1, g), 0.0)


# ============================================================================ the front street
def front_street(c, cam, t, pop=None, lid=0.0, cut=0.0, lamp=1.0, headlights=0.0, bell=0.0, above="street",
                 car_on=True, chalk=0.0, hatch=0.0, window=0.0, car_door=0.0, car_x=CAR_X, sky=SKY):
    """The front street at night (north-looking), the ground in section below (see the module
    docstring for every parameter)."""
    vx0, vy0, vx1, vy1 = cam.view(80.0)
    with cam.on(c):
        if vy0 < 40.0:
            if sky is not None:
                rect(c, (vx0 - 10.0, vy0 - 10.0, vx1 + 10.0, 2.0), sky, amp=0.0)
            if above == "street":
                moon(c, _pop(pop, "moon"))
                neighbours(c, _pop(pop, "neighbours"))
                with popped(c, 0.0, _pop(pop, "alley")) as ok:
                    if ok:
                        for polys, col in _alley():
                            bass.fill_polys(c, polys, col)
                        alarm_bell(c, bell, t)
                facade(c, t, pop, chalk)
                if window > 0.0:
                    r = window_rect(window)
                    rect(c, (r[0] - 6.0, r[1] - 6.0, r[2] + 6.0, r[3]), K.INK, amp=0.0)
                    with clipped(c, r):
                        _store_room(c, t, hatch)
                    if window < 1.0:
                        K.chalk_rect(c, (r[0] - 6.0, r[1] - 6.0, r[2] + 6.0, r[3]), 1.0, 2.5, K.PAPER, seed=941,
                                     alpha=0.8 * (1.0 - clamp((window - 0.7) / 0.3)))
                street_lamp(c, _pop(pop, "lamp"), lamp)
            else:
                _bank_section(c, t, hatch)
        if vy1 > -10.0:
            ground(c, t, cut, lid, view_x=(vx0 - 40.0, vx1 + 40.0))
            if cut > 0.45:
                _drips(c, t, _DRIPS_MAIN, PIPE[0], WATER, vx0, vx1)
        if vy0 < 40.0 and above == "street" and car_on:
            car(c, t, headlights, _pop(pop, "car"), x=car_x, door=car_door)


def sewer(c, cam, t, view="main", cut=1.0, hatch=0.0, trapdoor=0.0, drips=True, above="section", manhole_b=0.0,
          lid=1.0):
    """The sewer in section (see the module docstring)."""
    if view == "main":
        front_street(c, cam, t, lid=lid, cut=cut, above=above, hatch=hatch)
        return
    vx0, vy0, vx1, vy1 = cam.view(80.0)
    with cam.on(c):
        _branch_view(c, t, trapdoor, hatch, manhole_b, drips, (vx0, vx1), above)


# ============================================================================ the branch (east-looking)
def _branch_view(c, t, trapdoor, hatch, manhole_b, drips, xr, above):
    """East-looking section along the branch: u = plan y (north left). Manhole B at u 280 under
    the back street, the vault (u 430..700) over the trapdoor, the hatch at u 1150."""
    x0, x1 = xr[0] - 10.0, xr[1] + 10.0
    MB = MANHOLE_B_U
    rect(c, (x0, -1500.0, x1, 0.0), SKY, amp=0.0)
    if above:
        disc(c, (MB - 90.0, -980.0), 52.0, K.PAPER, seed=951, n=56)
        rect(c, (x0, -540.0, 230.0, 0.0), NEIGH, amp=0.6)                                       # across the back street
        for k in range(3):
            for j in range(2):
                rect(c, (90.0 - 110.0 * j, -480.0 + 140.0 * k, 138.0 - 110.0 * j, -400.0 + 140.0 * k), NEIGH_DK,
                     seed=957 + k * 2 + j)
        rect(c, (380.0, -FACADE_H, 1300.0, 0.0), K.INK, amp=0.6)                                 # the bank, cut
        rect(c, (380.0, -FACADE_H - 12.0, 1300.0, -FACADE_H), STONE_DK, amp=0.4)
        rect(c, (VAULT_IN[0], -VAULT_H, VAULT_IN[1], 0.0), ROOM, amp=0.2)                        # the vault
        rect(c, (VAULT_U[1], -CORR_H, 850.0, 0.0), lerp(ROOM, K.NAVY, 0.3), amp=0.2)            # its corridor
        rect(c, (860.0, -CORR_H, 940.0, 0.0), lerp(ROOM, K.NAVY, 0.45), amp=0.2)                 # the cross corridor
        rect(c, (950.0, -CORR_H, 1130.0, 0.0), lerp(ROOM, K.NAVY, 0.25), amp=0.2)
        rect(c, (1136.0, -ROOM_H, 1284.0, 0.0), ROOM, amp=0.2)                                   # the store room
        heavy = lerp(K.INK, K.STEEL, 0.18)                                                        # the vault's walls
        rect(c, (VAULT_U[0], -VAULT_H - 30.0, VAULT_IN[0], 0.0), heavy, amp=0.3)
        rect(c, (VAULT_IN[1], -VAULT_H - 30.0, VAULT_U[1], -2.0 * VDOOR_R - 14.0), heavy, amp=0.3)
        rect(c, (VAULT_U[0], -VAULT_H - 30.0, VAULT_U[1], -VAULT_H), heavy, amp=0.3)
    rect(c, (x0, 0.0, x1, 1600.0), EARTH, amp=0.0)
    band(c, (x0, 1.0), (x1, 1.0), 4.0, lerp(K.STEEL, K.NAVY, 0.25), seed=958)
    rect(c, (x0, 3.0, x1, VSLAB), SLAB, amp=0.0)
    _pipe_run(c, x0, x1, BRANCH[0], BRANCH[1], BRANCH_WATER, seed=960)
    # the shafts: manhole B (north end), the void under the trapdoor, the hatch
    for i, (u, top) in enumerate(((MB, 0.0), (TRAP_U, VSLAB), (HATCH_U, 0.0))):
        if not x0 - 40.0 < u < x1 + 40.0:
            continue
        rect(c, (u - 26.0, top - (2.0 if i != 1 else 0.0), u + 26.0, BRANCH[0] + 6.0), TUNNEL if i != 1 else VOID, amp=0.0)
        _rungs(c, u - 26.0, u + 26.0, top, BRANCH_WATER, seed=968 + i * 10)
    for i, (u, w, val) in enumerate(((MB, 30.0, manhole_b), (TRAP_U, 22.0, trapdoor), (HATCH_U, 26.0, hatch))):
        ang = 100.0 * (ease("outback", clamp(val)) if val < 1.0 else 1.0)
        c.save()
        c.translate(u - w - 2.0, 0.0)
        c.rotate(math.radians(-ang))
        rect(c, (0.0, -4.0, 2.0 * w + 4.0, 6.0), lerp(K.STEEL, K.INK, 0.2) if i != 1 else lerp(K.STEEL, K.INK, 0.45),
             amp=0.3)
        c.restore()
    if drips:
        _drips(c, t, _DRIPS_BRANCH, BRANCH[0], BRANCH_WATER, x0, x1)


# ============================================================================ the corridor (north-looking)
@lru_cache(maxsize=1)
def _corridor_wall():
    x0, x1 = CORR_X
    out = [([bass.cut_rect(x0, -CORR_H, x1, 0.0, seed=1001, amp=0.4)], WALL_IN)]
    out.append(([bass.cut_rect(x0, -72.0, x1, 0.0, seed=1002, amp=0.3)], lerp(WALL_IN, K.INK, 0.35)))
    seams = []
    for i, x in enumerate(range(int(x0) + 70, int(x1), 84)):
        if MOUTH_X[0] - 8.0 < x < MOUTH_X[1] + 8.0:
            continue
        seams.append(bass.cut_rect(x - 1.0, -CORR_H + 6.0, x + 1.0, -76.0, seed=1003 + i, amp=0.2))
    out.append((seams, lerp(WALL_IN, K.INK, 0.45)))
    out.append(([bass.cut_rect(x0, -76.0, x1, -70.0, seed=1030, amp=0.2)], lerp(WALL_IN, K.STEEL, 0.35)))   # the rail
    return out


@lru_cache(maxsize=1)
def _corridor_front():
    """What stands in front of the far wall: pipes, the desk and chair, the crates."""
    out = []
    pipes, hi = [], []
    x0, x1 = CORR_X
    for i, y in enumerate(PIPE_Y):
        w = 12.0 if i == 0 else 8.0
        pipes.append(bass.cut_rect(x0, y - w / 2, x1, y + w / 2, seed=1040 + i, amp=0.2))
        hi.append(bass.cut_rect(x0, y - w / 2 + 1.0, x1, y - w / 2 + 2.6, seed=1042 + i, amp=0.1))
    for k, bx in enumerate(range(int(x0) + 40, int(x1), 120)):            # brackets
        pipes.append(bass.cut_rect(bx - 3.0, PIPE_Y[0] - 9.0, bx + 3.0, PIPE_Y[1] + 7.0, seed=1050 + k, amp=0.2))
    # the vertical pipe beside the mouth, its foot
    pipes.append(bass.cut_rect(PIPE_X - 5.0, PIPE_Y[0], PIPE_X + 5.0, 0.0, seed=1060, amp=0.2))
    hi.append(bass.cut_rect(PIPE_X - 4.0, PIPE_Y[0] + 6.0, PIPE_X - 2.4, -2.0, seed=1061, amp=0.1))
    pipes.append(bass.cut_rect(PIPE_X - 8.0, -16.0, PIPE_X + 8.0, 0.0, seed=1062, amp=0.2))
    out.append((pipes, lerp(K.STEEL, K.INK, 0.3)))
    out.append((hi, lerp(K.STEEL, K.PAPER, 0.15)))
    d0, d1 = GUARD_DESK
    desk = [bass.cut_rect(d0, -64.0, d1, -56.0, seed=1070, amp=0.3), bass.cut_rect(d0 + 4.0, -56.0, d0 + 10.0, 0.0, seed=1071, amp=0.2),
            bass.cut_rect(d1 - 10.0, -56.0, d1 - 4.0, 0.0, seed=1072, amp=0.2),
            bass.cut_rect(d1 - 34.0, -56.0, d1 - 10.0, -30.0, seed=1073, amp=0.2),
            bass.cut_rect(d1 + 14.0, -40.0, d1 + 44.0, -34.0, seed=1074, amp=0.2),       # the chair, pushed back
            bass.cut_rect(d1 + 40.0, -92.0, d1 + 45.0, 0.0, seed=1075, amp=0.2),
            bass.cut_rect(d1 + 15.0, -34.0, d1 + 19.0, 0.0, seed=1076, amp=0.2),
            bass.cut_rect(d0 + 30.0, -74.0, d0 + 52.0, -64.0, seed=1077, amp=0.2),       # a telephone, a logbook
            bass.cut_rect(d0 + 34.0, -80.0, d0 + 48.0, -74.0, seed=1078, amp=0.2)]
    out.append((desk, K.INK))
    crates, slats = [], []
    for i, (cx0, cy0, cx1, cy1) in enumerate(CRATES):
        crates.append(bass.cut_rect(cx0, cy1, cx1, cy0, seed=1080 + i, amp=0.4))
        for f in (0.33, 0.66):
            yy = lerp(cy1, cy0, f)
            slats.append(bass.cut_rect(cx0 + 3.0, yy - 1.2, cx1 - 3.0, yy + 1.2, seed=1084 + i, amp=0.2))
        slats.append(bass.orient([(cx0 + 4.0, cy0 - 4.0), (cx0 + 8.0, cy0 - 4.0), (cx1 - 4.0, cy1 + 4.0), (cx1 - 8.0, cy1 + 4.0)],
                                 True))
    out.append((crates, lerp(K.NAVY, K.STEEL, 0.35)))
    out.append((slats, lerp(K.NAVY, K.INK, 0.4)))
    return out


def _guard_lamp(c, on):
    x, y = GUARD_LAMP
    if on > 0.0:
        ellipse(c, (x + 4.0, -64.0), 54.0, 6.0, K.GOLD, 0.35 * on)
        bass.fill_polys(c, [bass.orient([(x - 6.0, y + 6.0), (x + 14.0, y + 6.0), (x + 40.0, -64.0), (x - 30.0, -64.0)], True)],
                        K.GOLD, 0.12 * on)
        ellipse(c, (x + 4.0, y - 30.0), 46.0, 52.0, K.GOLD, 0.06 * on)
    bass.fill_polys(c, [bass.orient([(x - 1.5, -64.0), (x + 1.5, -64.0), (x + 1.5, y), (x - 1.5, y)], True),
                        bass.orient([(x - 8.0, -64.0), (x + 8.0, -64.0), (x + 6.0, -68.0), (x - 6.0, -68.0)], True)], K.INK)
    bass.fill_polys(c, [bass.orient([(x - 4.0, y - 12.0), (x + 4.0, y - 12.0), (x + 12.0, y + 6.0), (x - 12.0, y + 6.0)], True)],
                    lerp(K.INK, K.GOLD, 0.35 + 0.65 * on))


def tin_can(c, p, angle=0.0, color=None):
    """The tin can (on its side when it rolls): p its centre."""
    col = color or lerp(K.STEEL, K.PAPER, 0.2)
    c.save()
    c.translate(*p)
    c.rotate(math.radians(angle))
    rect(c, (-7.0, -9.0, 7.0, 9.0), col, amp=0.2)
    band(c, (-7.0, -4.0), (7.0, -4.0), 2.0, lerp(col, K.INK, 0.5), seed=1091)
    band(c, (-7.0, 4.0), (7.0, 4.0), 2.0, lerp(col, K.INK, 0.5), seed=1092)
    c.restore()


def corridor(c, cam, t, lamp=1.0, can=None, on_wall=None, door_dot=0.0):
    """The cross corridor (north-looking side elevation); see the module docstring."""
    with cam.on(c):
        corridor_px(c, t, lamp, can, on_wall, door_dot)


def corridor_px(c, t, lamp=1.0, can=None, on_wall=None, door_dot=0.0, bg=True):
    """corridor() drawn in set px with no camera of its own (e.g. inside a TiltSet). bg: fill
    everything round it with INK first (the building in section); False leaves what is there."""
    if True:
        if bg:
            fill_all(c, K.INK)
        for polys, col in _corridor_wall():
            bass.fill_polys(c, polys, col)
        # the mouth of the corridor to the vault: black, and far down it the door, black on black
        m0, m1 = MOUTH_X
        rect(c, (m0, -MOUTH_H, m1, 0.0), K.INK, amp=0.3)
        with clipped(c, (m0 + 2.0, -MOUTH_H + 2.0, m1 - 2.0, 0.0)):
            ring(c, VDOOR_C, FRAME_R - 8.0, 10.0, lerp(K.INK, K.STEEL, 0.16), seed=1094, n=72)
            ring(c, VDOOR_C, VDOOR_R * 0.55, 4.0, lerp(K.INK, K.STEEL, 0.12), seed=1095, n=48)
            disc(c, DIAL_C, DIAL_R, lerp(K.INK, K.STEEL, 0.14), seed=1096, n=24)
        if door_dot > 0.0:
            K.dot(c, DIAL_C, 4.0 * (ease("outback", clamp(door_dot)) if door_dot < 1 else 1.0), K.PAPER, seed=1097)
        rect(c, (m0 - 8.0, -MOUTH_H - 12.0, m1 + 8.0, -MOUTH_H), lerp(WALL_IN, K.STEEL, 0.3), amp=0.3)   # the lintel
        if on_wall is not None:
            on_wall(c)
        for polys, col in _corridor_front():
            bass.fill_polys(c, polys, col)
        _guard_lamp(c, lamp)
        if can is None:
            tin_can(c, (CAN_SEAT[0], CAN_SEAT[1] - 9.0))
        else:
            tin_can(c, (can[0], can[1]), can[2])
        rect(c, (CORR_X[0] - 16.0, -CORR_H - 26.0, CORR_X[0], 0.0), K.INK, amp=0.3)
        rect(c, (CORR_X[1], -CORR_H - 26.0, CORR_X[1] + 16.0, 0.0), K.INK, amp=0.3)
        band(c, (CORR_X[0] - 40.0, 1.0), (CORR_X[1] + 40.0, 1.0), 3.0, lerp(K.STEEL, K.INK, 0.3), seed=1098)
        band(c, (CORR_X[0] - 40.0, -CORR_H - 1.0), (CORR_X[1] + 40.0, -CORR_H - 1.0), 2.0, lerp(K.STEEL, K.INK, 0.55),
             seed=1099)


# ============================================================================ the vault door (north-looking)
@lru_cache(maxsize=1)
def _vault_wall():
    x0, x1 = VWALL_X
    plates = [bass.cut_rect(x0, -CORR_H, x1, 0.0, seed=1101, amp=0.4)]
    seams = []
    for i, x in enumerate(range(int(x0) + 60, int(x1), 60)):
        seams.append(bass.cut_rect(x - 1.2, -CORR_H, x + 1.2, 0.0, seed=1102 + i, amp=0.2))
    for i, y in enumerate((-190.0, -120.0, -50.0)):
        seams.append(bass.cut_rect(x0, y - 1.2, x1, y + 1.2, seed=1120 + i, amp=0.2))
    rivets = []
    for x in range(int(x0) + 30, int(x1), 30):
        for y in (-216.0, -150.0, -84.0, -18.0):
            if math.hypot(x - VDOOR_C[0], y - VDOOR_C[1]) > FRAME_R + 10.0:
                rivets.append(draw.circle_pts((float(x), y), 2.2, n=8))
    return plates, seams, rivets


def _bolt_u(bolts, k):
    """Progress of bolt k (0 shot .. 1 withdrawn) when the run is at `bolts`: they go one
    after another round the rim, clockwise from the top."""
    s = k / float(N_BOLTS) * 0.72
    return ease("inout", clamp((bolts - s) / 0.28))


def door_face(c, t, bolts=0.0, wheel=0.0, dial=0.0, dial_color=None, face=None, numerals=False):
    """The round door's outer face (set px, shut, about VDOOR_C): rings, bolts, wheel, dial."""
    face = face or IRON
    cx, cy = VDOOR_C
    disc(c, VDOOR_C, VDOOR_R, face, seed=1130, n=96)
    ring(c, VDOOR_C, VDOOR_R - 6.0, 3.0, lerp(face, K.PAPER, 0.10), seed=1131, n=96)
    disc(c, VDOOR_C, VDOOR_R * 0.80, lerp(face, K.NAVY, 0.35), seed=1132, n=96)
    disc(c, VDOOR_C, VDOOR_R * 0.74, face, seed=1133, n=96)
    ring(c, VDOOR_C, VDOOR_R * 0.50, 2.5, lerp(face, K.INK, 0.45), seed=1134, n=72)
    bolt_col = lerp(face, K.PAPER, 0.32)
    for k in range(N_BOLTS):
        a = math.radians(-90.0 + 15.0 + 30.0 * k)
        u = _bolt_u(bolts, k)
        r0, r1 = VDOOR_R * 0.80 - 22.0 * u, VDOOR_R + 12.0 - 26.0 * u
        ca, sa = math.cos(a), math.sin(a)
        band(c, (cx + r0 * ca, cy + r0 * sa), (cx + r1 * ca, cy + r1 * sa), 9.0, lerp(bolt_col, K.INK, 0.55), seed=1140 + k)
        band(c, (cx + r0 * ca, cy + r0 * sa), (cx + r1 * ca, cy + r1 * sa), 6.0, bolt_col, seed=1160 + k)
    rot = math.radians(wheel)
    for k in range(5):
        a = rot + 2 * math.pi * k / 5.0 - math.pi / 2
        tip = (WHEEL_C[0] + WHEEL_R * math.cos(a), WHEEL_C[1] + WHEEL_R * math.sin(a))
        band(c, WHEEL_C, tip, 7.0, lerp(face, K.INK, 0.6), seed=1180 + k)
        disc(c, tip, 7.0, lerp(face, K.PAPER, 0.25), seed=1185 + k, n=12)
    disc(c, WHEEL_C, 14.0, lerp(face, K.PAPER, 0.2), seed=1190, n=24)
    disc(c, WHEEL_C, 6.0, lerp(face, K.INK, 0.5), seed=1191, n=12)
    dial_face(c, DIAL_C, DIAL_R, dial, color=dial_color or K.PAPER, face=K.INK, bezel=lerp(face, K.PAPER, 0.2),
              seed=1192, numerals=numerals)


def vault_door(c, cam, t, open=0.0, bolts=0.0, wheel=0.0, dial=0.0, light="dark", inside=None, dial_color=None,
               glow=None, face=None, numerals=False):
    """The great round door (north-looking); see the module docstring."""
    face = face or IRON
    cx, cy = VDOOR_C
    th = math.radians(88.0 * clamp(open))
    with cam.on(c):
        fill_all(c, K.INK)
        plates, seams, rivets = _vault_wall()
        wall = lerp(face, K.NAVY, 0.45)
        bass.fill_polys(c, plates, wall)
        bass.fill_polys(c, seams, lerp(wall, K.INK, 0.4))
        bass.fill_polys(c, rivets, lerp(wall, K.PAPER, 0.12))
        band(c, (VWALL_X[0] - 60.0, 1.0), (VWALL_X[1] + 60.0, 1.0), 3.0, lerp(K.STEEL, K.INK, 0.3), seed=1201)
        ring(c, VDOOR_C, (VDOOR_R + FRAME_R) / 2.0 + 2.0, FRAME_R - VDOOR_R + 4.0, lerp(face, K.INK, 0.25), seed=1202, n=96)
        ring(c, VDOOR_C, FRAME_R, 3.0, lerp(face, K.PAPER, 0.12), seed=1203, n=96)
        g = clamp(open) if glow is None else glow
        if open > 0.0:
            c.save()
            c.new_path()
            c.arc(cx, cy, VDOOR_R + 1.0, 0.0, 2 * math.pi)
            c.clip()
            fill_all(c, K.GOLD if light == "gold" else K.INK)
            if inside is not None:
                inside(c)
            c.restore()
            if light == "gold" and g > 0.0:
                _gold_spill(c, g)
        ring(c, VDOOR_C, VDOOR_R + 1.0, 3.0, K.INK, seed=1204, n=96)
        cs, sn = math.cos(th), math.sin(th)
        if open > 0.0:
            xh = HINGE_X
            fc = xh + (cx - xh) * cs              # the face's centre after the swing
            back = fc - DOOR_T * sn
            edge_col = lerp(lerp(face, K.GOLD, 0.35), K.INK, 0.3) if light == "gold" else lerp(face, K.INK, 0.45)
            pts = []
            for i in range(0, 49):
                a = math.pi / 2 + math.pi * i / 48.0            # the back's left half (bottom, round the left)
                pts.append((back + VDOOR_R * cs * math.cos(a), cy + VDOOR_R * math.sin(a)))
            for i in range(0, 49):
                a = -math.pi / 2 + math.pi * i / 48.0           # the face's right half (top round to bottom)
                pts.append((fc + VDOOR_R * cs * math.cos(a), cy + VDOOR_R * math.sin(a)))
            bass.fill_polys(c, [bass.orient(pts, True)], edge_col)
            if DOOR_T * sn > 4.0:
                _door_edge(c, back, fc, cs, sn, edge_col, clamp((DOOR_T * sn - 4.0) / 10.0))
            if cs > 0.03:
                c.save()
                c.translate(xh, 0.0)
                c.scale(cs, 1.0)
                c.translate(-xh, 0.0)
                door_face(c, t, bolts, wheel, dial, dial_color, face, numerals)
                c.restore()
        else:
            door_face(c, t, bolts, wheel, dial, dial_color, face, numerals)
        for y in (cy - 62.0, cy + 46.0):
            rect(c, (HINGE_X - 4.0, y, HINGE_X + 14.0, y + 16.0), lerp(face, K.INK, 0.2), seed=1210 + int(abs(y)), amp=0.3)


def _door_edge(c, back, fc, cs, sn, col, alpha=1.0):
    """The swung door's thick edge (the band from its back to its face, seen on its near half):
    two machined steps and the ends of the six bolts on that half, so the slab reads as the
    door's edge and not a pillar."""
    cy = VDOOR_C[1]
    dark, lite = lerp(col, K.INK, 0.4), lerp(col, K.PAPER, 0.16)
    arc = [math.pi / 2 + math.pi * i / 40.0 for i in range(41)]
    for k in (0.3, 0.58):
        xk = back + k * (fc - back)
        for dx, w, tone in ((-2.6, 2.6, dark), (0.0, 1.8, lite)):      # a cut and its lit lip
            left = [(xk + dx + VDOOR_R * cs * math.cos(a), cy + VDOOR_R * math.sin(a)) for a in arc]
            bass.fill_polys(c, [bass.orient(left + [(x + w, y) for x, y in reversed(left)], True)], tone, alpha)
    xb = back + 0.8 * (fc - back)
    for k in range(N_BOLTS):
        a = math.radians(-90.0 + 15.0 + 30.0 * k)
        if math.cos(a) > -0.05:
            continue
        p = (xb + VDOOR_R * cs * math.cos(a), cy + VDOOR_R * math.sin(a))
        ry = 4.5 * abs(math.cos(a))
        ellipse(c, p, 6.0 * sn + 0.5, ry + 1.2, dark, alpha, n=20)
        ellipse(c, p, 4.2 * sn + 0.3, ry * 0.8, lite, alpha, n=20)


def _gold_spill(c, g):
    """The gold's light spilling out of the opening: flat stepped tints round it, above the floor
    line and below the ceiling (the cut above is nothing to light), and a pool on the floor in
    front (light adds to what it falls on)."""
    c.save()
    c.new_path()
    c.rectangle(VWALL_X[0], -CORR_H, VWALL_X[1] - VWALL_X[0], CORR_H + 2.0)
    c.clip()
    c.set_operator(cairo.OPERATOR_ADD)
    for i, (r, a) in enumerate(((VDOOR_R * 2.6, 0.05), (VDOOR_R * 1.9, 0.06), (VDOOR_R * 1.4, 0.08))):
        disc(c, VDOOR_C, r, K.GOLD, seed=1220 + i, n=72, alpha=a * g)
    c.restore()
    c.save()
    c.set_operator(cairo.OPERATOR_ADD)
    for i, (top, bot, d, a) in enumerate(SPILL_POOL):
        w0, w1 = top * (0.4 + 0.6 * g), bot * (0.4 + 0.6 * g)
        bass.fill_polys(c, [bass.orient([(VDOOR_C[0] - w0, 2.0), (VDOOR_C[0] + w0, 2.0), (VDOOR_C[0] + w1, 2.0 + d),
                                          (VDOOR_C[0] - w1, 2.0 + d)], True)], K.GOLD, a * g)
    ellipse(c, (VDOOR_C[0], 2.0), 230.0 * g + 40.0, 9.0, K.GOLD, 0.22 * g)
    ellipse(c, (VDOOR_C[0], 2.0), 130.0 * g + 24.0, 5.0, K.GOLD, 0.22 * g)
    c.restore()


SPILL_POOL = ((100.0, 200.0, 190.0, 0.045), (90.0, 150.0, 125.0, 0.05), (80.0, 112.0, 62.0, 0.06))


def spill_shadow(c, x, g, half=7.0, seed=0):
    """A figure's shadow in the gold's pool (set px, after vault_door, before the figure): from
    its feet at x on the floor toward us, fanning out from the opening's middle."""
    if g <= 0.0:
        return
    d = SPILL_POOL[0][2]
    k = (x - VDOOR_C[0]) * 0.55
    pts = [(x - half, 1.0), (x + half, 1.0), (x + k + half * 2.2, 2.0 + d), (x + k - half * 2.2, 2.0 + d)]
    bass.fill_polys(c, [bass.orient(pts, True)], K.INK, 0.8 * clamp(g))


def vault_through(c, t, light="gold", gold=1.0):
    """The vault seen through its open door, looking north (set px; for vault_door's inside): the
    far wall of deposit boxes, the floor running back to its foot, the gold stacked on the floor."""
    lit = light == "gold"
    wall = GOLD_WALL if lit else lerp(K.DEEP, K.NAVY, 0.3)
    boxc = GOLD_BOX if lit else lerp(K.DEEP, K.STEEL, 0.2)
    seam = GOLD_SEAM if lit else K.INK
    fill_all(c, wall)
    foot = -48.0                                       # the far wall's foot
    rect(c, (300.0, foot, 780.0, 0.0), lerp(wall, K.GOLD, 0.3) if lit else lerp(wall, K.INK, 0.3), amp=0.0)
    bw, bh = 25.0, 24.0
    x0, y0 = 540.0 - 4.0 * bw, foot - 8.0 - 6.0 * bh
    rect(c, (x0 - 3.0, y0 - 3.0, x0 + 8.0 * bw + 3.0, y0 + 6.0 * bh + 3.0), seam, amp=0.2)
    for i in range(8):
        for j in range(6):
            bx, by = x0 + i * bw, y0 + j * bh
            rect(c, (bx + 1.5, by + 1.5, bx + bw - 1.5, by + bh - 1.5), boxc, seed=1240 + i * 7 + j, amp=0.2)
            disc(c, (bx + bw / 2.0, by + bh / 2.0), 2.0, seam, seed=1290 + i * 7 + j, n=8)
    band(c, (300.0, foot), (780.0, foot), 2.0, seam, seed=1231)
    gcol = K.GOLD if lit else lerp(K.GOLD, K.INK, 0.7)
    edge = lerp(K.GOLD, K.INK, 0.75) if lit else K.INK
    n = 4
    for j in range(int(round(n * clamp(gold + 0.2)))):
        for k in range(n - j):
            bar(c, (548.0 + (k - (n - 1 - j) / 2.0) * 21.0, -24.0 - j * 8.0), 0.88, color=gcol, edge=edge,
                shine=K.PAPER if lit else None)


# ============================================================================ the dial and the lock
def dial_face(c, p, r, angle, color=K.PAPER, face=K.INK, bezel=K.STEEL, seed=0, alpha=1.0, numerals=False, index=True):
    """The combination dial, turned by `angle` degrees clockwise (see the module docstring)."""
    ring(c, p, r * 1.1, r * 0.2, bezel, seed=seed, n=72)
    disc(c, p, r, face, seed=seed + 1, n=72)
    a0 = math.radians(angle)
    w = max(0.6, r * 0.022)
    for k in range(40):                       # the plan's dial: 40 numbers, a long tick every 5
        a = a0 + 2 * math.pi * k / 40.0 - math.pi / 2
        L = 0.24 if k % 10 == 0 else 0.15 if k % 5 == 0 else 0.08
        r1 = r * 0.94
        r0 = r1 - r * L
        band(c, (p[0] + r0 * math.cos(a), p[1] + r0 * math.sin(a)), (p[0] + r1 * math.cos(a), p[1] + r1 * math.sin(a)),
             w * (1.9 if k % 5 == 0 else 1.0), color, seed=seed + 2, alpha=alpha)
    if numerals:
        for i in range(4):                    # 0 10 20 30, as the plan's lens has them
            a = a0 + 0.5 * math.pi * i - math.pi / 2
            q = (p[0] + r * 0.55 * math.cos(a), p[1] + r * 0.55 * math.sin(a))
            c.save()                          # cut at a nominal 40 px and scaled (the cut's roughness is in px)
            c.translate(*q)
            c.scale(r * 0.2 / 40.0, r * 0.2 / 40.0)
            K.numeral(c, str(10 * i), (0.0, 0.0), 40.0, color, seed=seed + 5 + i, rot=angle + 90.0 * i, alpha=alpha)
            c.restore()
    disc(c, p, r * 0.36, bezel, seed=seed + 3, n=40)
    disc(c, p, r * 0.26, lerp(bezel, K.INK, 0.35), seed=seed + 4, n=32)
    a = a0 - math.pi / 2
    band(c, (p[0] + r * 0.1 * math.cos(a), p[1] + r * 0.1 * math.sin(a)),
         (p[0] + r * 0.34 * math.cos(a), p[1] + r * 0.34 * math.sin(a)), max(1.0, r * 0.06), color, seed=seed + 6,
         alpha=alpha)
    if index:
        tip = (p[0], p[1] - r * 1.04)
        bass.fill_polys(c, [bass.orient([tip, (p[0] - r * 0.09, p[1] - r * 1.3), (p[0] + r * 0.09, p[1] - r * 1.3)], True)],
                        color, alpha)


LOCK_R = 76.0
LOCK_WHEELS = (-230.0, -50.0, 130.0)


def lock_cutaway(c, centre, scale, wheels, dots=(0.0, 0.0, 0.0), line=0.0, fence=0.0, bolt=0.0, color=K.PAPER,
                 alpha=1.0, spindle=None, seed=0):
    """The lock as a chalk diagram, frame px (see the module docstring)."""
    out = {"gates": []}
    s = scale
    cx, cy = centre
    r = LOCK_R * s
    wk = 3.4 * s + 0.6
    axle = [(cx + LOCK_WHEELS[0] * s - r - 50.0 * s, cy), (cx + LOCK_WHEELS[2] * s, cy)]
    K.dashes(c, axle, color, max(2.0, 3.0 * s), 16.0 * s, 10.0 * s, 1.0, seed + 1, 0.6 * alpha)
    if spindle is not None:
        K.dashes(c, [axle[0], spindle], color, max(2.0, 3.0 * s), 16.0 * s, 10.0 * s, 1.0, seed + 2, 0.6 * alpha)
    gate_w = 15.0
    for i, wx in enumerate(LOCK_WHEELS):
        p = (cx + wx * s, cy)
        ga = wheels[i] - 90.0
        pts = [(p[0] + r * math.cos(math.radians(ga + gate_w / 2 + (360.0 - gate_w) * j / 60.0)),
                p[1] + r * math.sin(math.radians(ga + gate_w / 2 + (360.0 - gate_w) * j / 60.0))) for j in range(61)]
        K.chalk_line(c, pts, 1.0, wk, color, seed + 10 + i, alpha)
        rd = r - 15.0 * s
        a1, a2 = math.radians(ga - gate_w / 2), math.radians(ga + gate_w / 2)
        notch = [(p[0] + r * math.cos(a1), p[1] + r * math.sin(a1)), (p[0] + rd * math.cos(a1), p[1] + rd * math.sin(a1)),
                 (p[0] + rd * math.cos(a2), p[1] + rd * math.sin(a2)), (p[0] + r * math.cos(a2), p[1] + r * math.sin(a2))]
        K.chalk_line(c, notch, 1.0, wk * 0.8, color, seed + 20 + i, alpha)
        for k in range(12):
            a = math.radians(wheels[i] + 30.0 * k - 90.0 + 15.0)
            band(c, (p[0] + (r - 10.0 * s) * math.cos(a), p[1] + (r - 10.0 * s) * math.sin(a)),
                 (p[0] + (r - 4.0 * s) * math.cos(a), p[1] + (r - 4.0 * s) * math.sin(a)), max(1.2, 2.0 * s), color,
                 seed=seed + 30 + k, alpha=0.55 * alpha)
        K.chalk_circle(c, p, r * 0.2, 1.0, wk * 0.7, color, seed + 40 + i, alpha * 0.8)
        gp = (p[0] + (r - 7.0 * s) * math.cos(math.radians(ga)), p[1] + (r - 7.0 * s) * math.sin(math.radians(ga)))
        out["gates"].append(gp)
        if dots[i] > 0.0:
            K.dot(c, gp, 8.5 * s * (ease("outback", clamp(dots[i])) if dots[i] < 1.0 else 1.0), color, seed=seed + 50 + i,
                  alpha=alpha)
    if line > 0.0:
        K.chalk_line(c, out["gates"], clamp(line), 3.2 * s + 0.8, color, seed + 60, alpha)
    fy = cy - r - 30.0 * s + 22.0 * s * (ease("outback", clamp(fence)) if fence < 1.0 else 1.0)
    fx0, fx1 = cx + (LOCK_WHEELS[0] - 40.0) * s, cx + (LOCK_WHEELS[2] + 80.0) * s
    K.chalk_rect(c, (fx0, fy - 12.0 * s, fx1, fy), 1.0, wk, color, seed + 70, alpha)
    for i, wx in enumerate(LOCK_WHEELS):
        x = cx + wx * s
        K.chalk_line(c, [(x - 6.0 * s, fy), (x - 4.0 * s, fy + 14.0 * s), (x + 4.0 * s, fy + 14.0 * s), (x + 6.0 * s, fy)],
                     1.0, wk * 0.8, color, seed + 72 + i, alpha)
    bx = cx + 250.0 * s - 70.0 * s * ease("inout", clamp(bolt))
    K.chalk_line(c, [(fx1, fy - 6.0 * s), (bx + 10.0 * s, cy - 26.0 * s)], 1.0, wk * 0.8, color, seed + 80, alpha)
    K.chalk_rect(c, (bx, cy - 28.0 * s, bx + 120.0 * s, cy + 28.0 * s), 1.0, wk, color, seed + 81, alpha)
    for k in range(3):
        xx = bx + (30.0 + 30.0 * k) * s
        K.chalk_line(c, [(xx, cy - 20.0 * s), (xx - 14.0 * s, cy + 20.0 * s)], 1.0, 1.6 * s + 0.4, color, seed + 82 + k,
                     0.5 * alpha)
    kx = cx + 330.0 * s
    K.chalk_line(c, [(kx, cy - 44.0 * s), (kx, cy - 30.0 * s), (kx + 40.0 * s, cy - 30.0 * s)], 1.0, wk, color, seed + 86,
                 alpha * 0.8)
    K.chalk_line(c, [(kx, cy + 44.0 * s), (kx, cy + 30.0 * s), (kx + 40.0 * s, cy + 30.0 * s)], 1.0, wk, color, seed + 87,
                 alpha * 0.8)
    out["bolt"] = (bx + 120.0 * s, cy)
    out["fence"] = ((fx0 + fx1) / 2.0, fy)
    return out


# ============================================================================ the vault inside (east-looking)
def bar(c, p, s=1.0, angle=0.0, color=K.GOLD, edge=K.INK, shine=K.PAPER):
    """One gold bar in elevation: p the middle of its base, s 1 = 24 px long, 9 high."""
    c.save()
    c.translate(*p)
    if angle:
        c.rotate(math.radians(angle))
    c.scale(s, s)
    outer = [(-12.0, 0.6), (12.0, 0.6), (9.0, -9.0), (-9.0, -9.0)]
    inner = [(-10.6, -0.6), (10.6, -0.6), (8.0, -7.8), (-8.0, -7.8)]
    bass.fill_polys(c, [bass.orient(outer, True)], edge)
    bass.fill_polys(c, [bass.orient(inner, True)], color)
    if shine is not None:
        bass.fill_polys(c, [bass.orient([(-7.0, -7.4), (6.0, -7.4), (5.2, -6.0), (-6.4, -6.0)], True)], shine, 0.55)
    c.restore()


@lru_cache(maxsize=1)
def _gold_layout():
    """The gold stacks: bars [(x, y)] bottom to top (they are taken from the end of the list)."""
    bars = []
    for (x0, n) in ((GOLD_U[0], 4), (GOLD_U[0] + 50.0, 3)):
        for j in range(n):
            for k in range(n - j):
                bars.append((x0 + 11.0 + k * 22.0 + j * 11.0, -j * 9.0))
    bars.sort(key=lambda b: (-b[1], b[0]))
    return bars


def gold_stacks(c, gold=1.0, color=K.GOLD, edge=K.INK, shine=K.PAPER):
    """The gold on the near side of the vault (set px): the top bars go first as gold falls."""
    bars = _gold_layout()
    n = int(round(len(bars) * clamp(gold)))
    for p in bars[:n]:
        bar(c, p, 1.0, color=color, edge=edge, shine=shine)


def _palette(light):
    """(wall, box, seam, slab, gold, gold_edge, shine) for the vault's light."""
    if light is None or light == "gold":
        return GOLD_WALL, GOLD_BOX, GOLD_SEAM, K.INK, K.GOLD, lerp(K.GOLD, K.INK, 0.75), K.PAPER
    dark = light == "dark"
    wall = lerp(K.INK, K.DEEP, 0.4) if dark else K.DEEP
    return (wall, lerp(wall, K.STEEL, 0.14 if dark else 0.22), K.INK, K.INK, lerp(K.GOLD, K.INK, 0.82 if dark else 0.62),
            K.INK, None)


def vault(c, cam, t, light=None, door=0.0, box=0.0, glint=0.0, tile=0.0, floor_cut=0.0, gold=1.0):
    """The vault inside, EAST-looking (see the module docstring)."""
    wall, boxc, seam, slab, goldc, gedge, shine = _palette(light)
    with cam.on(c):
        fill_all(c, K.INK)
        rect(c, (VAULT_U[1], -CORR_H, 900.0, 0.0), lerp(wall, K.INK, 0.55), amp=0.0)   # the corridor outside
        rect(c, (VAULT_IN[0], -VAULT_H, VAULT_IN[1], 0.0), wall, amp=0.2)
        band(c, (VAULT_IN[0], -VAULT_H + 14.0), (VAULT_IN[1], -VAULT_H + 14.0), 3.0, seam, seed=1301)
        rows = 5
        bw = (BOX_U[1] - BOX_U[0]) / 6.0
        bh = (BOX_ROWS[1] - BOX_ROWS[0]) / rows
        rect(c, (BOX_U[0] - 4.0, BOX_ROWS[0] - 4.0, BOX_U[1] + 4.0, BOX_ROWS[1] + 4.0), seam, amp=0.2)
        for i in range(6):
            for j in range(rows):
                x0 = BOX_U[0] + i * bw
                y0 = BOX_ROWS[0] + j * bh
                rect(c, (x0 + 1.5, y0 + 1.5, x0 + bw - 1.5, y0 + bh - 1.5), boxc, seed=1310 + i * 7 + j, amp=0.2)
                disc(c, (x0 + bw / 2.0, y0 + bh / 2.0), 2.2, seam, seed=1350 + i * 7 + j, n=8)
        if box > 0.0:
            x0, y0, x1, y1 = RUBY_BOX
            rect(c, (x0 + 1.5, y0 + 1.5, x1 - 1.5, y1 - 1.5), K.INK, amp=0.0)
            if glint > 0.0:
                gp = ((x0 + x1) / 2.0, (y0 + y1) / 2.0 + 4.0)
                disc(c, gp, 3.2, K.RED, seed=1390, n=10)
                K.twinkle(c, gp, 13.0, K.RED, u=clamp(glint), rot=12.0 + 30.0 * K.twos(t))
            g = clamp(box)
            wdt = (x1 - x0 - 3.0) * math.cos(math.radians(100.0 * g))
            pts = [(x0 + 1.5, y0 + 1.5), (x0 + 1.5 + wdt, y0 + 1.5 - 3.0 * g), (x0 + 1.5 + wdt, y1 - 1.5 + 3.0 * g),
                   (x0 + 1.5, y1 - 1.5)]
            if abs(wdt) > 0.5:
                bass.fill_polys(c, [bass.orient(pts, True)], lerp(boxc, K.PAPER, 0.15) if wdt < 0 else boxc)
        band(c, (VAULT_IN[0], -1.0), (VAULT_IN[1], -1.0), 2.4, seam, seed=1302)
        gold_stacks(c, gold, goldc, gedge, shine)
        cutc = lerp(K.INK, K.STEEL, 0.12)
        rect(c, (VAULT_U[0], -VAULT_H - 30.0, VAULT_IN[0], 0.0), cutc, amp=0.3)
        rect(c, (VAULT_IN[1], -VAULT_H - 30.0, VAULT_U[1], -2.0 * VDOOR_R - 14.0), cutc, amp=0.3)
        rect(c, (VAULT_U[0] - 30.0, -VAULT_H - 30.0, VAULT_U[1] + 30.0, -VAULT_H), cutc, amp=0.3)
        rect(c, (VAULT_U[0] - 40.0, 0.0, VAULT_U[1] + 230.0, VSLAB), lerp(K.INK, K.STEEL, 0.2), amp=0.3)
        rect(c, (VAULT_IN[1], -6.0, VAULT_U[1], 0.0), cutc, amp=0.2)
        _vault_door_side(c, door, light)
        _tile(c, tile, wall)
        if floor_cut > 0.0:
            _floor_cut(c, t, floor_cut, tile)
    if isinstance(light, tuple) and light[0] == "match":
        match_rings(c, cam, light[1], light[2], t)


def _vault_door_side(c, door, light):
    """The great door seen from inside the vault looking east: open, it stands outside the
    opening with its back to us (u 704..896); shut, it plugs the opening."""
    lit = light is None or light == "gold"
    th = math.radians(90.0 * (1.0 - clamp(door)))
    w = VDOOR_R * math.sin(th)
    cy = VDOOR_C[1]
    plate = lerp(K.STEEL, K.INK, 0.25) if not lit else lerp(K.GOLD, K.INK, 0.55)
    if w > 2.0:
        cx = VAULT_U[1] + 4.0 + w
        ellipse(c, (cx, cy), w + 3.0, VDOOR_R + 3.0, K.INK, n=72)
        ellipse(c, (cx, cy), w, VDOOR_R, plate, n=72)
        ellipse(c, (cx, cy), w * 0.42, VDOOR_R * 0.42, lerp(plate, K.INK, 0.35), n=48)
        for k in range(8):
            a = 2 * math.pi * k / 8.0
            band(c, (cx + w * 0.42 * math.cos(a), cy + VDOOR_R * 0.42 * math.sin(a)),
                 (cx + w * 0.92 * math.cos(a), cy + VDOOR_R * 0.92 * math.sin(a)), 5.0, lerp(plate, K.INK, 0.45), seed=1400 + k)
    if door > 0.5:
        g = clamp((door - 0.5) / 0.5)
        rect(c, (VAULT_IN[1], -2.0 * VDOOR_R - 14.0, VAULT_IN[1] + 30.0 + 16.0 * g, -6.0),
             lerp(plate, K.INK, 0.25), amp=0.2, alpha=g)


def _tile(c, tile, wall):
    x0, x1 = TILE_U
    if tile <= 0.0:
        band(c, (x0, -0.5), (x0, 3.0), 1.4, K.INK, seed=1410)
        band(c, (x1, -0.5), (x1, 3.0), 1.4, K.INK, seed=1411)
        return
    g = clamp(tile)
    rect(c, (x0, -1.0, x1, VSLAB), K.INK, amp=0.0, alpha=min(1.0, g * 3.0))
    lift = clamp(g / 0.5)
    slide = clamp((g - 0.5) / 0.5)
    ang = 80.0 * ease("out3", lift) * (1.0 - ease("inout", slide))
    px = x1 + 44.0 * ease("inout", slide)
    c.save()
    c.translate(px, -1.0)
    c.rotate(math.radians(ang))
    rect(c, (-(x1 - x0), -5.0, 0.0, 0.0), lerp(wall, K.STEEL, 0.25), amp=0.2)
    c.restore()


def _floor_cut(c, t, u, tile):
    """The cutaway below the vault floor: the slab, the void under the trapdoor, the branch."""
    g = ease("out3", clamp(u))
    x0, x1 = VAULT_U[0] - 30.0, VAULT_U[1] + 30.0
    top = VSLAB
    bot = lerp(VSLAB, BRANCH[1] + 30.0, g)
    with clipped(c, (x0, top, x1, bot)):
        rect(c, (x0, top, x1, BRANCH[1] + 40.0), lerp(K.INK, K.NAVY, 0.2), amp=0.0)
        _pipe_run(c, x0, x1, BRANCH[0], BRANCH[1], BRANCH_WATER, seed=1420)
        rect(c, (TRAP_U - 24.0, top, TRAP_U + 24.0, BRANCH[0] + 6.0), VOID, amp=0.0)
        _rungs(c, TRAP_U - 24.0, TRAP_U + 24.0, top, BRANCH_WATER, seed=1430)
        _drips(c, t, _DRIPS_BRANCH, BRANCH[0], BRANCH_WATER, x0, x1)
    K.chalk_line(c, [(x0, top), (x0, bot)], 1.0, 2.5, K.PAPER, seed=1440, alpha=0.7)
    K.chalk_line(c, [(x1, top), (x1, bot)], 1.0, 2.5, K.PAPER, seed=1441, alpha=0.7)
    if u < 1.0:
        K.chalk_line(c, [(x0, bot), (x1, bot)], 1.0, 2.5, K.PAPER, seed=1442, alpha=0.7)
    if tile > 0.0:                                     # the trapdoor's opening through the slab
        rect(c, (TILE_U[0], -1.0, TILE_U[1], VSLAB + 1.0), K.INK, amp=0.0)


def match_rings(c, cam, p, r, t, strength=1.0, seed=0):
    """The stepped gold rings of a match's light round set point p (radius r set px)."""
    K.match_light(c, cam.to_frame(p), t, r * cam.zoom, strength, seed)


# ============================================================================ the inside of the door (south-looking)
def door_inside(c, cam, t, light=None, bolts=0.0):
    """The inside of the shut door, SOUTH-looking (see the module docstring)."""
    wall, boxc, seam, slab, goldc, gedge, shine = _palette(light)
    lit = light is None or light == "gold"
    plate = lerp(K.GOLD, K.INK, 0.55) if lit else lerp(wall, K.STEEL, 0.3)
    dark = lerp(plate, K.INK, 0.45)
    cx, cy = VDOOR_C
    with cam.on(c):
        fill_all(c, K.INK)
        rect(c, (390.0, -VAULT_H, 690.0, 0.0), wall, amp=0.2)
        band(c, (390.0, -VAULT_H + 14.0), (690.0, -VAULT_H + 14.0), 3.0, seam, seed=1501)
        rect(c, (390.0, -206.0, 428.0, -36.0), boxc, amp=0.2)
        for k in range(1, 5):
            band(c, (390.0, lerp(-206.0, -36.0, k / 5.0)), (428.0, lerp(-206.0, -36.0, k / 5.0)), 2.0, seam, seed=1502 + k)
        ring(c, VDOOR_C, VDOOR_R + 8.0, 14.0, lerp(plate, K.INK, 0.3), seed=1510, n=96)
        disc(c, VDOOR_C, VDOOR_R, plate, seed=1511, n=96)
        ring(c, VDOOR_C, VDOOR_R - 10.0, 3.0, dark, seed=1512, n=96)
        for k in range(N_BOLTS):
            a = math.radians(-90.0 + 15.0 + 30.0 * k)
            u = _bolt_u(bolts, k)
            ca, sa = math.cos(a), math.sin(a)
            r0, r1 = 34.0, VDOOR_R + 10.0 - 24.0 * u
            band(c, (cx + r0 * ca, cy + r0 * sa), (cx + r1 * ca, cy + r1 * sa), 7.0, dark, seed=1520 + k)
            band(c, (cx + (r1 - 16.0) * ca, cy + (r1 - 16.0) * sa), (cx + r1 * ca, cy + r1 * sa), 11.0,
                 lerp(plate, K.PAPER, 0.25), seed=1540 + k)
        rect(c, (cx - 38.0, cy - 30.0, cx + 38.0, cy + 30.0), dark, seed=1560, amp=0.3)     # the gearbox
        rect(c, (cx - 30.0, cy - 22.0, cx + 30.0, cy + 22.0), lerp(plate, K.INK, 0.2), seed=1561, amp=0.3)
        for k in range(4):
            disc(c, (cx - 22.0 + 44.0 * (k % 2), cy - 14.0 + 28.0 * (k // 2)), 3.0, dark, seed=1562 + k, n=8)
        hx = 1080.0 - HINGE_X
        for y in (cy - 62.0, cy + 46.0):
            rect(c, (hx - 14.0, y, hx + 4.0, y + 16.0), dark, seed=1570 + int(abs(y)), amp=0.3)
        for j in range(3):                                                                  # gold, on the right
            for k in range(3 - j):
                bar(c, (612.0 + 11.0 + k * 22.0 + j * 11.0, -j * 9.0), 1.0, color=goldc, edge=gedge, shine=shine)
        cutc = lerp(K.INK, K.STEEL, 0.12)
        rect(c, (360.0, -VAULT_H - 30.0, 390.0, 0.0), cutc, amp=0.3)
        rect(c, (690.0, -VAULT_H - 30.0, 720.0, 0.0), cutc, amp=0.3)
        rect(c, (330.0, -VAULT_H - 30.0, 750.0, -VAULT_H), cutc, amp=0.3)
        rect(c, (330.0, 0.0, 750.0, VSLAB), lerp(K.INK, K.STEEL, 0.2), amp=0.3)
        band(c, (390.0, -1.0), (690.0, -1.0), 2.4, seam, seed=1580)
    if isinstance(light, tuple) and light[0] == "match":
        match_rings(c, cam, light[1], light[2], t)


# ============================================================================ props
def _limb_h(p, R):
    """A climbing limb's height above the foot of the ladder, at climb phase p (cycles): it rests
    on a rung, then moves up two rungs (2R) during the first half of each cycle."""
    q = p - math.floor(p)
    return 2.0 * R * math.floor(p) + (2.0 * R * ease("inout", q / 0.5) if q < 0.5 else 2.0 * R)


def ladder_pose(who, h, facing=1, rung=RUNG_STEP, reach=1.0):
    """A procedural climbing pose (see the module docstring). Figure units: the ladder's foot at
    y = 0, the rungs every `rung` set px above it, in front of the figure (toward `facing`)."""
    F = C.fig(who)
    U = 1.0 / FIG_S
    R = rung * U
    p = max(0.0, h) * U / (2.0 * R)
    near_f = _limb_h(p, R)
    far_f = max(0.0, _limb_h(p + 0.5, R) - R)
    leg = F.thigh + F.shin
    feet = {"near": (facing * 30.0, -near_f, -6.0), "far": (facing * 36.0, -far_f, -6.0)}
    lo, hi = min(near_f, far_f), max(near_f, far_f)
    pel_y = -(lo + 0.5 * (hi - lo) + leg * 0.80)
    st = dict(pelvis=(-facing * 8.0, pel_y), feet=feet, phase=0.0, speed=0.0, run=0.0, stride=0.0)
    sh_y = pel_y + F.shoulder[1]
    top = sh_y - 60.0 * reach
    # the hands go opposite to the feet: the near hand moves with the far foot
    hn = top - (_limb_h(p + 0.5, R) - R - lo) * 0.85
    hf = top - (near_f - lo) * 0.85
    pose = pd.Pose(lean=-3.0, head=10.0)
    pose.arms["near"] = ("ik", (facing * (54.0 + 6.0 * reach), hn))
    pose.arms["far"] = ("ik", (facing * (60.0 + 6.0 * reach), hf))
    return st, pose


@lru_cache(maxsize=64)
def _sack_pts(fill, seed=0):
    """A sack hanging from its gathered neck at (0, 0), figure units (fill rounded to 0.05)."""
    f = clamp(fill)
    w = lerp(50.0, 150.0, f)
    h = lerp(200.0, 172.0, f)
    rb = w / 2.0 * lerp(0.35, 0.8, f)
    right = []
    for k in range(9):
        s = k / 8.0
        shape = lerp(0.3 + 0.7 * s, math.sin(0.5 * math.pi * min(1.0, s / 0.6)), f)
        right.append((max(10.0, w / 2.0 * shape), 16.0 + (h - 16.0 - rb) * s))
    bottom = [(w / 2.0 * math.cos(math.pi * k / 8.0), h - rb + rb * math.sin(math.pi * k / 8.0)) for k in range(1, 8)]
    left = [(-x, y) for x, y in reversed(right)]
    pts = [(-8.0, 0.0), (8.0, 0.0)] + right + bottom + left
    return tuple(bass.orient(bass.cut(pts, seed=seed, amp=0.8, seg=(14.0, 30.0)), True))


def hold_sack(fill=0.0, seed=0, floor=None):
    """A pose.hold fn: a canvas sack hanging from the fist (fill 0 empty, slack .. 1 stuffed).
    floor: the floor's y in figure units (0 for a figure drawn on its floor): a sack that would
    hang through it slumps on it instead."""
    f = round(clamp(fill) * 20.0) / 20.0

    def fn(c, info):
        hc = info["hc"]
        col = info.get("rim") or K.INK
        c.save()
        c.translate(hc[0], hc[1] + 8.0)
        if floor is not None:
            h = lerp(200.0, 172.0, f)
            room = floor - (hc[1] + 8.0)
            if room < h:
                c.scale(1.0 + 0.4 * clamp(1.0 - room / h), max(0.12, room / h))
        bass.fill_polys(c, [list(_sack_pts(f, seed))], col)
        if not info.get("rim") and f > 0.4:
            g = clamp((f - 0.4) / 0.6)
            for k, (x, y) in enumerate(((-20.0, 30.0), (6.0, 24.0), (26.0, 34.0))):
                bass.fill_polys(c, [bass.orient([(x - 10.0 * g, y), (x + 10.0 * g, y), (x + 8.0 * g, y - 9.0 * g),
                                                 (x - 8.0 * g, y - 9.0 * g)], True)], K.GOLD)
        c.restore()
    return fn


def sack(c, p, fill, s=1.0, color=K.INK, rim=None, seed=0):
    """A sack standing on the floor, set px: p the middle of its base."""
    f = clamp(fill)
    w, h = lerp(36.0, 40.0, f) * s, lerp(9.0, 40.0, f) * s
    pts = [(-w / 2.0, 0.0), (w / 2.0, 0.0)]
    for k in range(1, 8):
        a = math.pi * k / 8.0
        pts.append(((w / 2.0) * math.cos(a), -h * 0.78 * math.sin(a) - (h * 0.18 if k == 4 else 0.0)))
    neck = [(-3.0 * s, -h * 0.9), (3.0 * s, -h * 0.9), (4.0 * s, -h - 6.0 * s), (-4.0 * s, -h - 6.0 * s)]
    c.save()
    c.translate(*p)
    if rim:
        c.save()
        c.translate(-1.5, -1.5)
        bass.fill_polys(c, [bass.orient(pts, True), bass.orient(neck, True)], rim)
        c.restore()
    bass.fill_polys(c, [bass.orient(pts, True), bass.orient(neck, True)], color)
    if f > 0.6:
        for k, x in enumerate((-8.0, 6.0)):
            bar(c, (x * s, -h * 0.78), 0.45 * s, angle=-20.0 + 30.0 * k, edge=K.INK)
    c.restore()


def stethoscope(c, ear, piece, s=1.0, color=K.INK, rim=None, piece_color=K.STEEL):
    """The Cracker's stethoscope: the tube from his ear down round the neck, then slack to the
    chest-piece at `piece` (a sagging curve: it bows down, or forward when the piece hangs)."""
    a1 = (ear[0] - 2.0 * s, ear[1] + 12.0 * s)
    vx, vy = piece[0] - a1[0], piece[1] - a1[1]
    d = math.hypot(vx, vy) or 1.0
    nx, ny = -vy / d, vx / d
    if (abs(ny) < 0.25 and nx * vx < 0.0) or (abs(ny) >= 0.25 and ny < 0.0):
        nx, ny = -nx, -ny
    sag = 3.0 * s + 0.14 * d
    q = ((a1[0] + piece[0]) / 2.0 + nx * sag, (a1[1] + piece[1]) / 2.0 + ny * sag)
    pts = [ear]
    for i in range(13):
        u = i / 12.0
        pts.append(((1 - u) ** 2 * a1[0] + 2 * u * (1 - u) * q[0] + u * u * piece[0],
                    (1 - u) ** 2 * a1[1] + 2 * u * (1 - u) * q[1] + u * u * piece[1]))
    if rim:
        K.band(c, [(x - 1.2, y - 1.2) for x, y in pts], rim, max(1.2, 3.0 * s), seed=1601)
    K.band(c, pts, color, max(1.2, 3.0 * s), seed=1602)
    disc(c, piece, 5.0 * s, color, seed=1603, n=12)
    disc(c, piece, 3.2 * s, piece_color, seed=1604, n=10)


# ============================================================================ annotation on the world
def ghost_route(c, pts, lit=0.0, gap=24.0, r=5.5, color=K.PAPER, ghost=0.28, seed=0, head=True, t=0.0, lit_t=None,
                xf=None, alpha=1.0):
    """Plan A's chalk route on the world: dots every `gap` along pts, dim (alpha `ghost`) ahead and
    bright where the crew have reached. lit: how far along it is lit (px), or a function s -> 0..1
    (each dot's brightness at arc length s). lit_t(s): the time the dot at s lit (it pops then).
    xf: maps a point of pts' space to c's space (dots stay put on the world while r stays a size
    in c's space, e.g. cam.to_frame with frame px r)."""
    L = K.poly_len(pts)
    s = gap * 0.5
    i = 0
    on_at = lit if callable(lit) else (lambda q: clamp((lit - q) / (gap * 0.8)))
    while s < L - 4.0:
        p, _ = K.poly_at(pts, s)
        on = on_at(s)
        rr = r * (1.0 + 0.35 * on)
        if lit_t is not None and on > 0.0:
            a = clamp((t - lit_t(s)) / 0.25)
            rr = r * (1.0 + 0.35 * on + 0.5 * math.sin(math.pi * a) * (1.0 - a))
        q = xf(p) if xf else p
        K.dot(c, q, rr, color, seed=seed * 131 + i, alpha=alpha * (ghost + (0.95 - ghost) * on))
        s += gap
        i += 1
    if head and L > 30.0:
        p, d = K.poly_at(pts, L)
        on = on_at(L - gap * 0.5)
        if xf:
            q, q2 = xf(p), xf((p[0] - d[0], p[1] - d[1]))
            dd = (q[0] - q2[0], q[1] - q2[1])
            n = math.hypot(*dd) or 1.0
            p, d = q, (dd[0] / n, dd[1] / n)
        K.arrowhead(c, p, d, r * 3.6, color, seed=seed, alpha=alpha * (ghost + (0.95 - ghost) * on))


def footfalls(perf, t0, t1, step=1.0 / 12.0, lift=15.0, land=8.0):
    """[(t, side, x)]: the frames (sampled on twos) where a Performance's feet come down: a foot
    that has swung higher than `lift` figure units lands on the first frame it is back within
    `land` of the floor."""
    out = []
    swing = {"near": False, "far": False}
    n = int(math.ceil((t1 - t0) / step - 1e-9))
    for i in range(n + 1):
        t = t0 + i * step
        st, _ = perf(t)
        for side in ("near", "far"):
            y = st["feet"][side][1]
            if y < -lift:
                swing[side] = True
            elif swing[side] and y >= -land:
                out.append((round(t, 4), side, st["feet"][side][0]))
                swing[side] = False
    return out
