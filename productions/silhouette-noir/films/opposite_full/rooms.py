"""OPPOSITE (the full Bass cut): HER ROOM, the shared set (animator A).

Her room is the SECTION's storey-4 room (`K.her_room()`), seen close as a side stage, in
profile: the door in the left wall (to the stair landing), the window in the right wall (to
the street). Furniture sits where the section puts it (`K.HER_SET`), left to right: the stove
with the kettle, the small table with the rotary phone, the pendant lamp with its pull cord;
the wall clock on the back wall; a curtain on a rod inside the window. The floors above and
below are the section's own slabs and dark rooms (the stage is drawn ON the kit's section), so
the doll's-house world stays continuous with s01's push-in.

Two views of the set, plus helpers:

  STAGE   (profile)  draw_stage(c, t, room, cam=CANON, figures=None)
  WINDOW  (face on, from inside, looking across the street)
                     draw_window_view(c, t, room, cam=WCANON, far=None, ...)

COORDINATES
  Stage px: frame px of the canonical stage framing (1080 x 1920, y down). The floor line is
  y = FLOOR = 1560 (the Bass cut's room floor). The stage is the section scaled by S = 4.4:
      to_stage(p) / to_section(p)       section px <-> stage px
      ROOM   = (87.0, 697.6, 993.4, 1560.0)   inside of the room
      DOOR   = (25.4, 961.6, 87.0, 1560.0)    the doorway in the left wall (to the landing)
      WINDOW = (993.4, 917.6, 1055.0, 1401.6) the window opening in the right wall
      PLATFORM_Y = 1577.6                     her fire-escape platform, outside (x 1055..1337)
  Cameras: Cam(x, y, z, rot) shows stage point (x, y) at the frame centre, zoom z (rot deg).
      CANON = Cam()                 the room wall to wall
      section_cam(zs, centre=None)  = the SECTION at zoom zs centred on her room (section px)
      S01_END = section_cam(3.2)    where s01's push-in ends and s02 begins (the hand-off)
      cam_lerp(a, b, u)             eased pushes: centre lerped, zoom log-lerped

ROOM STATE  Room(...) (a dataclass; use dataclasses.replace to vary it)
  lit      True: lamp on, the room AMBER, furniture INK.  False: DEEP, the window a NIGHT
           slot, edges caught in cold light (STEEL rims on the window side), moonlight wedge
  window   0..1  the lower sash raised
  wind     0..1  the curtain billows in (and the lamp's pull cord sways)
  door     0..1  the door leaf swung into the room (0 shut, 1 = wide, ~100 deg)
  chain    "off" hanging from the frame | "on" in its slot (taut when the door is ajar) |
           "snapped" (gone; scenes fly the links themselves, see chain_links())
  hall     0..1  the landing light: under the door when shut, a beam through it when open
  kettle   kettle on the stove (False: a scene draws it in her hand with draw_kettle)
  flame    the gas lit under the kettle (PAPER tongues)
  steam    0..1 steam curling off the kettle's whistle; whistle 0..1 the whistle blowing
  mug      her mug on the stove top (False: in her hand, B.mug_hold)
  clock    (h, m, s) on the wall clock, or None: clock_time(film_t) with film_t = room.film_t
           (it ticks on the beat: the second hand jumps half a second every beat, 120 bpm)
  film_t   film time (s) for the clock when clock is None

FIGURES IN THE ROOM (her, him) are the Bass cut's cut-outs at FIG_S = 0.80 on the stage; the
  section draws its people at FIG_S / S (folk.SEC_FS), so the cut from the section (s01's push)
  to the stage keeps everyone's size and place.
      c.save(); B.place(c, x, FLOOR, FIG_S)
      B.draw_cutout(c, fig, st, pose, INK, facing=f, edge=bg, outline=bg, ow=8.0)
      c.restore()
  with bg = room_bg(room) (AMBER lit, DEEP dark). At FIG_S she is about 524 px tall and he 572 px
  (his hat clears the 598 px doorway by 26 px). In the dark use rim_cutout(...) for the cold
  edge. draw_stage takes two figure callbacks and an overlay, all in stage px:
      figures(c)  inside the room (clipped to it), after the furniture, before the walls
      outside(c)  not clipped: drawn behind the cut walls and sashes but over the window slot,
                  so a body half through the window shows only through the opening (s06's
                  climb), and out on the fire escape it stands behind the railings
      overlay(c)  over everything (the walls, the fire escape's ironwork): annotations that
                  ride the set, or a figure redrawn clipped where it is in front of the iron
  Marks (pelvis x, stage px):
      SPOT_STOVE = 403.8     her place at the stove, facing -1 (where s01 leaves her)
      SPOT_WINDOW = 785.0    at the glass, facing +1 (a mug held at her chest clears the curtain)
      X_DOOR = 87.0          the inside face of the doorway
      SPOT_PLATFORM = 1170.0 out on the fire escape (stand on PLATFORM_Y)
  NEIGHBOURS: the storeys above and below are the section's dark rooms, peopled as s01 leaves
  them (folk.asleep: the woman asleep in her chair below, the old man at his radio two floors
  down). draw_stage does this by default; pass others(c, b, n, rect) to draw them yourself.
  In the SECTION (s01, s07) use section_room(c, t, room) inside your K.draw_section people
  callback for (HER_B, 4): it draws this set at section scale, so the push-in arrives on the
  same room the stage shows (or section_people(...) for a whole callback).

THE WINDOW VIEW (s02 over her shoulder; s10 mirrors it over his; s06 from the floor; s08
through the keyhole)
  draw_window_view(c, t, room, cam=WCANON, far=None, tb=None, his_lit=True, windows=None,
                   sky_lit=0.0, lamp=True, moon=True, facade=True)
  Her window seen face on from inside: the wall round it (AMBER lit / DEEP dark), the casing,
  the two sashes (the lower one raised by room.window), the curtain on its rod (billowing with
  room.wind), and through the glass the night: the far city, the moon, the street lamp in the
  gap, and his building's facade, the Bass cut's right-hand slab (B.RIGHT_B, B.RIGHT_WIN, as
  K.draw_elevation shows it) with his window lit, one floor up.
  Two layers, with parallax when the camera moves:
      near  view px = frame px at WCANON (= Cam()): the wall, the window, the curtain
      far   the Bass ELEVATION px (B.LEFT_B / B.RIGHT_B space), mapped so B.HIS_WIN sits in
            the upper sash (FAR_AT, FAR_F); it moves FAR_PAR as much as the near layer
  far(c, rect, t) draws what is in his window: it is called in elevation px, clipped to
  rect = B.HIS_WIN, so B.draw_room_small(c, tb) (the couple, s02) or any figure placed with
  B.place(c, x, B.HIS_WIN[3] + 6, B.WIN_FS) (her, s10) drops straight in. tb: the Bass time
  for the far windows' colours (K.window_color); windows(i, r) -> rgb or None overrides one.
  WV (a dict, view px at WCANON): 'glass' the opening, 'his_win' his window, 'sill_y', 'rod_y',
  'stool' (the inside sill), 'eye_level' (a standing eye line). view_point(cam, p, layer)
  maps a near (view px) or far (elevation px) point to the frame.
  draw_back(c, who, base, s, edge=None, t=0, turn=0) draws a head and shoulders from behind
  ("her": the bob; "him": the hat brim and the turned-up collar) for the foreground of those
  shots; base is the nape (px), s the scale (1: a head 230 px high). Returns anchors: 'eye'
  (the point a sight line leaves from), 'crown', 'nape', 'shoulders' (left, right), 'ears'
  (left, right). back_marks(who, base, s, t, turn) returns the same anchors without drawing
  (for a look or a shout that must pass behind the head).

OTHER HELPERS
  draw_kettle(c, base, s, tilt, t, steam=..., whistle=...)   the kettle (base = its foot, px; on the
                                                              stage it is drawn at KETTLE_S)
  draw_mug(c, hc, s, facing, t, steam)                        B.mug_shape (handle at hc)
  draw_clock(c, p, r, hms, face, ink)                         the wall clock with a second hand
  clock_time(film_t) -> (h, m, s)                             11:46:00 at film 12.0, real time
  chain_links(...)                                            link centres of the door chain
  hall_beam_pts(room)                                         the landing light's wedge (stage)
"""
import math
from dataclasses import dataclass
from functools import lru_cache

import cairo

from engine import bass
from engine.core import clamp, ease, hash01, lerp
from engine.palette import RED  # noqa: F401  (re-exported for scenes)
from films.opposite_bass import world as B
from films.opposite_full import folk as F
from films.opposite_full import kit as K

INK, PAPER, AMBER = K.INK, K.PAPER, K.AMBER
NIGHT, STEEL, DEEP, SHUT = K.NIGHT, K.STEEL, K.DEEP, K.SHUT
GLASS = lerp(NIGHT, PAPER, 0.28)          # a pane edge catching light

# ============================================================================ stage <-> section
S = 4.4                                   # stage px per section px
SEC_X0, SEC_FLOOR = 160.0, 1056.0         # her room's left wall (inside face) and floor, section px
X0, FLOOR = 87.0, 1560.0                  # ... on the stage
FIG_S = 0.80                              # figures on the stage (B.place scale); the section's are FIG_S / S (folk.SEC_FS)


def to_stage(p):
    return (X0 + (p[0] - SEC_X0) * S, FLOOR + (p[1] - SEC_FLOOR) * S)


def to_section(p):
    return (SEC_X0 + (p[0] - X0) / S, SEC_FLOOR + (p[1] - FLOOR) / S)


def _rect_stage(r):
    a, b = to_stage((r[0], r[1])), to_stage((r[2], r[3]))
    return (a[0], a[1], b[0], b[1])


ROOM = _rect_stage(K.her_room())                          # (87.0, 697.6, 993.4, 1560.0)
DOOR = _rect_stage(K.HER_B.door(K.HER_FLOOR))             # (25.4, 961.6, 87.0, 1560.0)
WINDOW = _rect_stage(K.her_window())                      # (993.4, 917.6, 1055.0, 1401.6)
CEIL = ROOM[1]
PLATFORM_Y = to_stage((0.0, K.level(K.HER_FLOOR) - 4.0))[1]       # 1577.6
PLATFORM_X = (to_stage((K.ESCAPE_X[0], 0.0))[0], to_stage((K.ESCAPE_X[1], 0.0))[0])
ROOM_CENTRE_SEC = ((K.her_room()[0] + K.her_room()[2]) / 2.0, (K.her_room()[1] + K.her_room()[3]) / 2.0)

SPOT_STOVE = 403.8          # her pelvis x at the stove, facing -1: section x 232, where s01 leaves her
SPOT_WINDOW = 785.0         # her pelvis x at the window, facing +1 (a mug held at her chest clears the curtain)
X_DOOR = DOOR[2]            # the inside face of the doorway
SPOT_PLATFORM = 1170.0      # out on the fire escape (stand on PLATFORM_Y)

# the furniture marks, from the section (K.HER_SET: x from the room's left wall, section px)
_SET = dict((kind, X0 + dx * S) for kind, dx in K.HER_SET)
X_STOVE, X_TABLE, X_LAMP = _SET["stove"], _SET["phone"], _SET["lamp"]    # 201.4, 491.8, 747.0
CLOCK_P, CLOCK_R = (X_TABLE + 4.0, 958.0), 47.0
KETTLE_BASE = (250.0, 1284.0)             # the kettle's foot on the stove's right burner
KETTLE_S = 0.8                            # the kettle's scale on the stage (kettle units -> stage px)
MUG_HC = (164.0, 1269.0)                  # her mug on the stove top (handle centre), under the spout
MUG_S = 1.35 * FIG_S                      # mug units -> stage px (as in her hand, B.mug_hold)


# ============================================================================ cameras
@dataclass(frozen=True)
class Cam:
    """Shows stage (or view) point (x, y) at the frame centre, zoomed z, turned rot deg."""
    x: float = 540.0
    y: float = 960.0
    z: float = 1.0
    rot: float = 0.0

    def apply(self, c):
        c.translate(540.0, 960.0)
        if self.rot:
            c.rotate(math.radians(self.rot))
        c.scale(self.z, self.z)
        c.translate(-self.x, -self.y)

    def matrix(self):
        m = cairo.Matrix()
        m.translate(540.0, 960.0)
        if self.rot:
            m.rotate(math.radians(self.rot))
        m.scale(self.z, self.z)
        m.translate(-self.x, -self.y)
        return m

    def to_frame(self, p):
        return self.matrix().transform_point(*p)

    def from_frame(self, p):
        m = self.matrix()
        m.invert()
        return m.transform_point(*p)


CANON = Cam()
WCANON = Cam()


def section_cam(zs, centre=None):
    """The camera that shows the SECTION at zoom zs (section px -> frame px) centred on
    `centre` (section px; default her room's centre)."""
    cx, cy = to_stage(centre or ROOM_CENTRE_SEC)
    return Cam(cx, cy, zs / S)


S01_END = section_cam(3.2)


def cam_lerp(a, b, u):
    """A push between two cameras: the frame-centre point moves so the zoom feels even
    (log-lerped zoom; the centre follows the zoom so the move does not swing)."""
    u = clamp(u)
    za, zb = a.z, b.z
    z = math.exp(lerp(math.log(za), math.log(zb), u))
    # weight the centre by how far the zoom has gone, so a push-in glides toward its target
    w = u if abs(zb - za) < 1e-6 else (1.0 / z - 1.0 / za) / (1.0 / zb - 1.0 / za)
    return Cam(lerp(a.x, b.x, w), lerp(a.y, b.y, w), z, lerp(a.rot, b.rot, u))


# ============================================================================ state
@dataclass(frozen=True)
class Room:
    lit: bool = True
    window: float = 0.0
    wind: float = 0.0
    door: float = 0.0
    chain: str = "off"
    hall: float = 0.0
    kettle: bool = True
    flame: bool = False
    steam: float = 0.0
    whistle: float = 0.0
    mug: bool = True
    clock: tuple = None
    film_t: float = 12.0


def room_bg(room):
    return AMBER if room.lit else DEEP


def clock_time(film_t):
    """Her wall clock: 11:46:00 when s02 starts (film 12.0 s), running in real time, ticking on
    the beat (0.5 s at 120 bpm): each beat the second hand jumps half a second (a quick
    overshoot and settle) and the minute hand gives a small kick. Returns (h, m, s): minutes
    and the second hand's position in seconds, both floats for the hands' angles."""
    beat = K.BEAT
    secs = 46 * 60.0 + (film_t - 12.0)
    n = math.floor(secs / beat + 1e-6)
    frac = (secs - n * beat) / 0.09
    jump = ease("outback", clamp(frac)) if frac < 1.0 else 1.0
    s_hand = ((n - 1) * beat + jump * beat) % 60.0
    kick = 0.25 * math.sin(math.pi * clamp(frac)) * (1.0 - clamp(frac))       # minutes (1.5 deg)
    m = ((n * beat) / 60.0 + kick) % 60.0
    return (11, m, s_hand)


# ============================================================================ shapes
def _P(pts, seed, amp=0.6, seg=(18.0, 46.0)):
    return bass.orient(bass.cut(pts, seed=seed, amp=amp, seg=seg), True)


def _R(x0, y0, x1, y1, seed, amp=0.6):
    return bass.orient(bass.cut_rect(x0, y0, x1, y1, seed=seed, amp=amp, seg=(16.0, 44.0)), True)


def _S(pts, seed, sag=0.6, amp=0.4, max_len=22.0):
    """A curved outline, scissor cut."""
    return bass.orient(bass.scissor(pts, seed=seed, sag=sag, amp=amp, max_len=max_len, corner=40.0), True)


def _arc(cx, cy, rx, ry, a0, a1, n=24):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def _cap(a, b, ra, rb, cap=6):
    return bass.orient(bass.capsule_pts(a, b, ra, rb, cap), True)


@lru_cache(maxsize=1)
def stove_polys():
    """The gas range against the left wall, front to the right (toward her): splashback with a
    shelf and a canister, the top plate, the body, two feet, a knob and the oven handle."""
    x0, x1 = X_STOVE - 102.0, X_STOVE + 100.0           # 99.4 .. 301.4
    top = 1292.0
    P = [
        _R(x0 - 4.0, 1110.0, x0 + 6.0, top + 2.0, 1),                      # splashback
        _R(x0 - 4.0, 1104.0, x0 + 40.0, 1111.0, 2),                         # its shelf
        _P([(x0 + 10.0, 1104.0), (x0 + 30.0, 1104.0), (x0 + 30.0, 1078.0), (x0 + 26.0, 1072.0),
            (x0 + 14.0, 1072.0), (x0 + 10.0, 1078.0)], 3),                  # a canister on it
        _R(x0 - 6.0, top, x1 + 6.0, top + 10.0, 4),                         # top plate
        _R(x0 + 2.0, top + 9.0, x1, FLOOR - 15.0, 5),                       # body
        _R(x0 + 10.0, FLOOR - 16.0, x0 + 22.0, FLOOR, 6),                   # feet
        _R(x1 - 20.0, FLOOR - 16.0, x1 - 8.0, FLOOR, 7),
        _P([(x1 - 1.0, top + 18.0), (x1 + 8.0, top + 17.0), (x1 + 11.0, top + 22.0), (x1 + 8.0, top + 28.0),
            (x1 - 1.0, top + 28.0)], 8, amp=0.3),                           # a knob
        _R(x1 - 1.0, top + 64.0, x1 + 7.0, top + 70.0, 9, amp=0.3),           # oven handle standoff
        _cap((x1 + 9.0, top + 58.0), (x1 + 9.0, top + 76.0), 4.0, 4.0, 4),  # oven handle
        _R(x1 - 1.0, top + 214.0, x1 + 3.0, top + 220.0, 10, amp=0.2),      # the drawer lip
    ]
    # the burner grates: low crowns on the top plate
    for j, (a, b) in enumerate(((x0 + 18.0, x0 + 92.0), (x0 + 112.0, x1 - 12.0))):
        pts = [(a, top), (a, top - 6.0)]
        n = 5
        for i in range(n):
            u0, u1 = (i + 0.25) / n, (i + 0.75) / n
            pts += [(lerp(a, b, u0), top - 6.0), (lerp(a, b, u0), top - 9.0), (lerp(a, b, u1), top - 9.0),
                    (lerp(a, b, u1), top - 6.0)]
        pts += [(b, top - 6.0), (b, top)]
        P.append(bass.orient(pts, True))
    return P


def flame_polys(t):
    """The gas under the kettle: a row of small PAPER tongues, flickering on twos."""
    tt = B.twos(t)
    out = []
    x0, x1 = KETTLE_BASE[0] - 30.0, KETTLE_BASE[0] + 30.0
    y = 1292.0 - 7.0
    for i in range(6):
        x = lerp(x0, x1, (i + 0.5) / 6.0)
        h = 8.0 + 4.0 * hash01(i, int(tt * 12.0), 41)
        w = 3.2
        out.append(bass.orient([(x - w, y), (x + w, y), (x + 0.6, y - h), (x - 0.6, y - h)], True))
    return out


# --- the kettle: a squat whistling kettle, spout to the left (toward the mug), a bail handle
# with a grip bar over the top. Kettle units = stage px at s = 1, origin at the middle of its
# foot, y up negative.
def _spline(pts, n=6):
    """Catmull-Rom through pts (open), sampled n points per span."""
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            u = k / n
            u2, u3 = u * u, u * u * u
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * u + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u3) for j in (0, 1)))
    out.append(pts[-1])
    return out


_KETTLE_SIDE = [(44.0, 0.0), (50.0, -4.0), (54.0, -12.0), (55.5, -22.0), (54.0, -34.0), (50.0, -45.0), (43.0, -55.0),
                (34.0, -63.0), (24.0, -69.0), (14.0, -73.0), (11.0, -76.0)]
_KETTLE_ARCH = [(-25.0, -64.0), (-24.0, -92.0), (-12.0, -112.0), (8.0, -120.0), (28.0, -114.0), (40.0, -96.0),
                (44.0, -74.0), (41.0, -56.0)]


@lru_cache(maxsize=None)
def kettle_local(fine=1.0):
    """(body, spout, whistle cap, handle band, grip, lid knob) outlines in kettle units: a squat
    whistling kettle, the spout low on the belly rising to the left with its whistle cap, a
    fixed handle arching over the top with a grip. fine > 1 cuts finer (close-ups)."""
    ml = 16.0 / fine
    sag = 0.22 / fine
    right = _spline(_KETTLE_SIDE, 5)
    body = right + [(-x, y) for x, y in reversed(right)]
    body = _S(body, 701, sag=sag, amp=0.2 / fine ** 0.5, max_len=ml)
    # the spout: a tapered tube from the belly up to the left, its underside a little bowed
    lo = _spline([(-48.0, -10.0), (-62.0, -24.0), (-76.0, -42.0), (-86.0, -57.0)], 6)
    hi = _spline([(-43.0, -42.0), (-58.0, -51.0), (-70.0, -60.0), (-78.0, -67.0)], 6)
    spout = _S(lo + hi[::-1], 702, sag=sag, amp=0.15 / fine ** 0.5, max_len=ml)
    # the whistle cap over the mouth, and its little lever
    a, b = (-83.0, -62.0), (-94.0, -72.0)
    cap = _cap(a, b, 8.5, 7.5, 5)
    lever = bass.orient([(-87.0, -74.0), (-83.0, -79.0), (-75.0, -81.0), (-77.0, -76.0)], True)
    arch = _spline(_KETTLE_ARCH, 6)
    handle = bass.orient(_ribbon(arch, 5.0), True)
    grip = bass.orient(_ribbon(_spline([(-14.0, -115.5), (0.0, -120.0), (14.0, -120.5), (26.0, -116.0)], 4), 13.0), True)
    knob = _S(_arc(0.0, -77.0, 9.0, 7.0, 180.0, 360.0, 12) + [(9.0, -75.0), (-9.0, -75.0)], 703, sag=0.2 / fine,
              amp=0.1, max_len=ml)
    return body, spout, bass.orient(cap + [], True), lever, handle, grip, knob


def _ribbon(pts, w):
    return bass.draw.ribbon(pts, [w] * len(pts))


KETTLE_GRIP = (6.0, -118.0)               # the middle of the grip bar (kettle units)
KETTLE_SPOUT = (-96.0, -74.0)             # the whistle's mouth (kettle units)
KETTLE_MOUTH = (-88.0, -60.0)             # where the water leaves the spout, cap open (kettle units)


def kettle_xf(base, s, tilt):
    """Kettle units -> px: foot at base, scale s, tipped `tilt` deg about the foot's front
    edge (positive tips the spout down)."""
    m = cairo.Matrix()
    m.translate(*base)
    m.scale(s, s)
    piv = (-46.0, 0.0)
    m.translate(*piv)
    m.rotate(math.radians(-tilt))
    m.translate(-piv[0], -piv[1])
    return m


def draw_kettle(c, base, s=1.0, tilt=0.0, t=0.0, steam=0.0, whistle=0.0, color=INK, edge=None, fine=1.0,
                xf=None):
    """The kettle at `base` (its foot, px), scale s, tipped `tilt` deg toward the spout.
    steam 0..1: a curl from the whistle; whistle 0..1: the steam jets hard (the whistle).
    Returns {'grip': px, 'spout': px} for a hand and for the pour."""
    m = xf or kettle_xf(base, s, tilt)
    polys = list(kettle_local(fine))
    c.save()
    c.transform(m)
    if edge is not None:
        B.edged(c, polys, color, edge, 3.0 / max(s, 0.2))
    else:
        bass.fill_polys(c, polys, color)
    c.restore()
    out = {"grip": m.transform_point(*KETTLE_GRIP), "spout": m.transform_point(*KETTLE_SPOUT)}
    if steam > 0.0 or whistle > 0.0:
        _kettle_steam(c, out["spout"], t, s, steam, whistle, tilt)
    return out


def _kettle_steam(c, tip, t, s, steam, whistle, tilt):
    """Steam off the whistle: lazy curls (steam), and when it blows (whistle) a jet of puffs
    shooting up and out of the cap, swelling and thinning as they go. INK on the amber, like
    the mug's steam."""
    tt = B.twos(t)
    c.save()
    c.translate(*tip)
    c.scale(s, s)
    c.rotate(math.radians(-tilt))
    if whistle > 0.0:
        a = math.radians(-118.0)
        d = (math.cos(a), math.sin(a))
        for j in range(7):
            ph = (tt * 2.2 + j / 7.0) % 1.0
            dist = 8.0 + 92.0 * ph * (0.55 + 0.45 * whistle)
            side = 7.0 * math.sin(9.0 * ph + 2.3 * j) * ph
            p = (d[0] * dist - d[1] * side, d[1] * dist + d[0] * side)
            r = 3.0 + 9.0 * ph
            bass.fill_polys(c, [bass.ring_pts(p, r, seed=700 + j, n=12, amp=0.3)], INK,
                            0.7 * whistle * (1.0 - ph) ** 1.3)
    if steam > 0.0:
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        for j, x0 in enumerate((-6.0, 6.0)):
            c.new_path()
            for i in range(14):
                u = i / 13.0
                x = x0 - 12.0 * u + 6.0 * math.sin(2 * math.pi * (u * 1.1 - tt * 0.8) + j * 2.0) * u
                y = -10.0 - 52.0 * u
                c.line_to(x, y) if i else c.move_to(x, y)
            c.set_line_width(3.0)
            c.set_source_rgba(*INK, 0.75 * steam * (1.0 - 0.6 * whistle))
            c.stroke()
    c.restore()


def draw_mug(c, hc, s=MUG_S, facing=-1, t=0.0, steam=0.0, color=INK, edge=None, tilt=0.0):
    """Her mug (B.mug_shape) upright with its handle centre at hc, scale s; facing -1 puts the
    body to the left of the handle. steam 0..1 rises off the rim. Returns the rim (px)."""
    c.save()
    c.translate(*hc)
    c.scale(s * facing, s)
    c.rotate(math.radians(-tilt))
    B.mug_shape(c, color, edge=edge, edge_w=2.0 / max(s, 0.3))
    rim = c.user_to_device(*B._MUG_RIM)
    c.restore()
    rim = c.device_to_user(*rim)
    if steam > 0.02:
        B.steam(c, rim, B.twos(t), INK, alpha=steam, scale=s / 1.35)
    return rim


@lru_cache(maxsize=1)
def table_polys():
    """The small telephone table: a thick top, an apron, two splayed legs, a shelf with the
    phone book."""
    x = X_TABLE
    top = 1326.0
    return [
        _R(x - 82.0, top, x + 82.0, top + 12.0, 21),
        _R(x - 74.0, top + 11.0, x + 74.0, top + 28.0, 22),
        _P([(x - 70.0, top + 27.0), (x - 55.0, top + 27.0), (x - 66.0, FLOOR), (x - 78.0, FLOOR)], 23, amp=0.4),
        _P([(x + 55.0, top + 27.0), (x + 70.0, top + 27.0), (x + 78.0, FLOOR), (x + 66.0, FLOOR)], 24, amp=0.4),
        _R(x - 66.0, 1466.0, x + 66.0, 1476.0, 25),
        _R(x - 44.0, 1440.0, x + 38.0, 1466.0, 26),
    ]


@lru_cache(maxsize=1)
def phone_parts():
    """The rotary telephone (shown in its readable face-on silhouette, Bass's way): the body,
    the handset on its cradle, the dial (paper), the coiled cord. Returns (ink polys, dial
    centre, dial radius)."""
    x = X_TABLE
    base = 1326.0
    body = _S([(x - 40.0, base), (x + 40.0, base), (x + 36.0, base - 10.0), (x + 28.0, base - 30.0),
               (x + 18.0, base - 38.0), (x - 18.0, base - 38.0), (x - 28.0, base - 30.0), (x - 36.0, base - 10.0)],
              31, sag=0.3, amp=0.2, max_len=12.0)
    prongs = [_R(x - 26.0, base - 46.0, x - 18.0, base - 37.0, 32, 0.2), _R(x + 18.0, base - 46.0, x + 26.0, base - 37.0, 33, 0.2)]
    # the handset: a bar with a cup at each end, lying across the cradle
    bar = _cap((x - 34.0, base - 52.0), (x + 34.0, base - 52.0), 6.0, 6.0, 5)
    cups = [_S(_arc(x - 40.0, base - 50.0, 12.0, 10.0, 90.0, 270.0, 10) + [(x - 30.0, base - 60.0), (x - 30.0, base - 40.0)][::-1],
               34, sag=0.2, amp=0.15, max_len=8.0),
            _S(_arc(x + 40.0, base - 50.0, 12.0, 10.0, -90.0, 90.0, 10) + [(x + 30.0, base - 40.0), (x + 30.0, base - 60.0)][::-1],
               35, sag=0.2, amp=0.15, max_len=8.0)]
    # the coiled cord: from the mouthpiece down the side to the body
    coil = []
    for i in range(29):
        u = i / 28.0
        ang = u * 6.0 * 2 * math.pi
        cx = x - 46.0 - 6.0 * math.sin(math.pi * u)
        cy = lerp(base - 42.0, base - 8.0, u)
        coil.append((cx + 4.0 * math.cos(ang), cy + 2.0 * math.sin(ang)))
    cord = bass.orient(_ribbon(coil, 2.2), True)
    return [body] + prongs + [bar] + cups + [cord], (x, base - 20.0), 11.0


def dial_polys(c0, r, seed=36):
    """The dial seen small: a paper disc with ten finger holes cut in it (holes in ink)."""
    disc = bass.orient(bass.ring_pts(c0, r, seed=seed, n=28, amp=0.15), True)
    holes = []
    for i in range(10):
        a = math.radians(-60.0 + 30.0 * i)
        holes.append(bass.orient(bass.ring_pts((c0[0] + 0.66 * r * math.cos(a), c0[1] + 0.66 * r * math.sin(a)),
                                               0.17 * r, seed=seed + i, n=8, amp=0.05), True))
    return disc, holes


@lru_cache(maxsize=1)
def lamp_polys():
    """The pendant: a ceiling rose, the flex, a coolie shade with a rolled rim, the socket."""
    x = X_LAMP
    y0 = CEIL
    shade_top, shade_bot = 878.0, 944.0
    out = [_R(x - 14.0, y0 - 2.0, x + 14.0, y0 + 9.0, 41, 0.3),
           bass.orient([(x - 1.6, y0 + 8.0), (x + 1.6, y0 + 8.0), (x + 1.6, shade_top), (x - 1.6, shade_top)], True)]
    shade = [(x - 10.0, shade_top), (x + 10.0, shade_top)]
    for i in range(1, 13):
        u = i / 12.0
        hw = 10.0 + 58.0 * u ** 1.35
        shade.append((x + hw, lerp(shade_top, shade_bot, u)))
    shade += [(x + 70.0, shade_bot + 3.0), (x - 70.0, shade_bot + 3.0)]
    for i in range(12, 0, -1):
        u = i / 12.0
        hw = 10.0 + 58.0 * u ** 1.35
        shade.append((x - hw, lerp(shade_top, shade_bot, u)))
    out.append(_S(shade, 42, sag=0.3, amp=0.25, max_len=16.0))
    out.append(_R(x - 7.0, shade_bot - 8.0, x + 7.0, shade_bot + 8.0, 43, 0.2))
    return out


LAMP_BULB = (X_LAMP, 957.0)
CORD_TOP = (X_LAMP - 40.0, 950.0)         # (to the stove side: she stands at the window clear of it)
CORD_LEN = 236.0


def cord_end(room, t):
    """The bead at the end of the lamp's pull cord (it sways when the wind is in)."""
    sw = room.wind * (0.6 * math.sin(B.twos(t) * 3.1) + 0.4 * math.sin(B.twos(t) * 5.3 + 1.0))
    a = math.radians(10.0 * sw)
    return (CORD_TOP[0] + CORD_LEN * math.sin(a), CORD_TOP[1] + CORD_LEN * math.cos(a))


def draw_clock(c, p, r, hms, face=PAPER, ink=INK, rim=None, seed=50):
    """Her wall clock: K.clock_face (a paper disc, twelve dots, two hands) with a thin ink
    rim and a second hand that ticks."""
    if rim is not None:
        bass.fill_polys(c, [bass.ring_pts(p, r + 4.0, seed=seed + 1, n=48, amp=0.3)], rim)
    h, m, s = hms
    K.clock_face(c, p, r, h, m, face=face, ink=ink, seed=seed)
    a = math.radians(s * 6.0 - 90.0)
    tip = (p[0] + 0.84 * r * math.cos(a), p[1] + 0.84 * r * math.sin(a))
    tail = (p[0] - 0.22 * r * math.cos(a), p[1] - 0.22 * r * math.sin(a))
    bass.fill_polys(c, [_cap(tail, tip, max(0.9, 0.028 * r), max(0.6, 0.016 * r), 3)], ink)
    K.dot(c, p, r * 0.07, ink, seed=seed + 2)


# --- the curtain: one panel hanging inside the window from a rod, seen edge on (the rod runs
# along the wall, so we see its end: a bracket and a finial)
ROD_Y = 902.0
ROD_X = 966.0                             # the rod's end (the finial), over the panel
CURTAIN_TOP, CURTAIN_HEM = ROD_Y + 9.0, FLOOR - 18.0
CURTAIN_LEN = CURTAIN_HEM - CURTAIN_TOP


def _curtain_spine(room, t, n=40):
    """The panel's centre line (top to hem) and its width along it, stage px. At rest it hangs
    straight, gathered under the rod and flaring a little to the hem. With wind it swings into
    the room about the rod like a sail: the lower it is, the further it is blown, the hem
    lifting, fluttering on twos."""
    tt = B.twos(t)
    b = clamp(room.wind)
    ds = CURTAIN_LEN / n
    x, y = ROD_X - 2.0, CURTAIN_TOP
    spine, width = [(x, y)], [13.0]
    for i in range(1, n + 1):
        u = i / n
        flut = b * u * (7.0 * math.sin(2.0 * math.pi * (1.3 * tt - 1.6 * u)) + 3.5 * math.sin(2.0 * math.pi * (2.9 * tt - 3.4 * u) + 1.0))
        th = math.radians(0.8 + b * (5.4 + 72.0 * u ** 1.7) + flut)
        x -= ds * math.sin(th)
        y += ds * math.cos(th)
        spine.append((x, y))
        width.append(13.0 + 13.0 * min(1.0, u / 0.12) + 6.0 * u + b * (10.0 * u + 64.0 * math.sin(math.pi * min(1.0, u * 1.1)) ** 1.5))
    return spine, width


def _offset(spine, width, f):
    """Points offset from the spine by f x its width, along the normal (f > 0 toward the window)."""
    out = []
    for i, (p, w) in enumerate(zip(spine, width)):
        q0, q1 = spine[max(0, i - 1)], spine[min(len(spine) - 1, i + 1)]
        dx, dy = q1[0] - q0[0], q1[1] - q0[1]
        d = math.hypot(dx, dy) or 1.0
        nx, ny = dy / d, -dx / d                   # the normal on the window side
        out.append((p[0] + nx * w * f, p[1] + ny * w * f))
    return out


def curtain_pts(room, t):
    """Outline of the curtain panel in profile (stage px)."""
    spine, width = _curtain_spine(room, t)
    right = _offset(spine, width, 0.5)
    left = _offset(spine, width, -0.5)
    # the hem: a soft curve across the bottom, rolled toward the room
    (xl, yl), (xr, yr) = left[-1], right[-1]
    tt = B.twos(t)
    hem = [(lerp(xr, xl, u), lerp(yr, yl, u) + (4.0 + 6.0 * room.wind * math.sin(tt * 5.0)) * math.sin(math.pi * u))
           for u in (0.25, 0.5, 0.75)]
    return bass.orient(right + hem + left[::-1], True)


def curtain_pleats(room, t):
    """The fold lines inside the panel: two cuts that run with it (drawn in the room's colour)."""
    spine, width = _curtain_spine(room, t)
    lines = []
    for f, a, z in ((-0.16, 0.05, 0.96), (0.2, 0.09, 0.9)):
        pts = _offset(spine, width, f)
        i0, i1 = int(a * (len(pts) - 1)), int(z * (len(pts) - 1))
        lines.append(pts[i0:i1 + 1])
    return lines


def curtain_rod_polys():
    """The rod's bracket off the window wall, the rod's end (a finial) and the rings."""
    return [_R(ROD_X, ROD_Y - 3.0, WINDOW[0] + 1.0, ROD_Y + 3.0, 61, 0.2),                    # bracket arm
            _R(WINDOW[0] - 7.0, ROD_Y - 12.0, WINDOW[0] + 1.0, ROD_Y + 12.0, 63, 0.2),           # its plate
            bass.orient(bass.ring_pts((ROD_X, ROD_Y), 8.5, seed=62, n=14, amp=0.2), True),       # the finial
            _R(ROD_X - 11.0, ROD_Y + 5.0, ROD_X + 7.0, CURTAIN_TOP + 3.0, 64, 0.2)]                # the rings


# --- the window in the right wall, seen in section: sills, the two sashes in their tracks
SASH_IN = (1009.0, 1021.0)               # the lower sash's track (inside)
SASH_OUT = (1028.0, 1040.0)              # the upper sash's track (outside)
MEET_Y = 1158.0                          # the meeting rails, shut
LIFT = 216.0                             # how far the lower sash rises


def _sash(x, y0, y1, seed, glass=GLASS):
    rails = [_R(x[0], y0, x[1], y0 + 20.0, seed, 0.2), _R(x[0], y1 - 20.0, x[1], y1, seed + 1, 0.2)]
    pane = bass.orient([(x[0] + 4.5, y0 + 20.0), (x[1] - 4.5, y0 + 20.0), (x[1] - 4.5, y1 - 20.0),
                        (x[0] + 4.5, y1 - 20.0)], True)
    return rails, pane


def window_polys(room):
    """(ink polys, glass polys, lower sash bottom-rail y) of the window in profile."""
    w0, w1 = WINDOW[1], WINDOW[3]
    ink, glass = [], []
    r, g = _sash(SASH_OUT, w0, MEET_Y + 8.0, 71)
    ink += r
    glass.append(g)
    dy = -LIFT * clamp(room.window)
    r, g = _sash(SASH_IN, MEET_Y - 8.0 + dy, w1 + dy, 73)
    ink += r
    glass.append(g)
    ink += [
        _R(WINDOW[0] - 16.0, w1 - 4.0, WINDOW[0] + 8.0, w1 + 10.0, 75, 0.3),                     # stool
        _P([(WINDOW[2] - 8.0, w1 - 2.0), (WINDOW[2] + 22.0, w1 + 5.0), (WINDOW[2] + 22.0, w1 + 14.0),
            (WINDOW[2] - 8.0, w1 + 12.0)], 76, amp=0.3),                                          # outer sill
        _R(SASH_IN[0] - 7.0, w1 - 18.0 + dy, SASH_IN[0], w1 - 8.0 + dy, 77, 0.2),               # the lift
        _R(SASH_IN[0] - 6.0, MEET_Y - 4.0 + dy, SASH_IN[0], MEET_Y + 2.0 + dy, 78, 0.2),        # the catch
        _R(WINDOW[0], w0 - 2.0, WINDOW[2], w0 + 6.0, 79, 0.2),                                    # head
    ]
    return ink, glass, w1 + dy


def sash_lift_y(room):
    """y of the lower sash's lift (where her fingers take it), stage px."""
    return WINDOW[3] - 13.0 - LIFT * clamp(room.window)


# --- the door: in the left wall, opening into the room
DOOR_W = 285.0                            # the leaf's width (0.9 m), seen face on when open
LEAF = (50.0, DOOR[1] + 2.0, 74.0, FLOOR - 2.0)
KNOB_Y = FLOOR - 296.0
CHAIN_Y = FLOOR - 368.0


def door_angle(room):
    return 100.0 * clamp(room.door)


def door_polys(room):
    """(leaf polys drawn in the room (open), polys in the doorway (shut leaf, stop, knob))."""
    th = math.radians(door_angle(room))
    stop = _R(DOOR[2] - 12.0, DOOR[1], DOOR[2], FLOOR, 81, 0.3)
    if th < 1e-3:
        leaf = _R(*LEAF, 82, 0.3)
        knob = _P([(LEAF[2], KNOB_Y - 4.0), (LEAF[2] + 18.0, KNOB_Y - 7.0), (LEAF[2] + 22.0, KNOB_Y),
                   (LEAF[2] + 18.0, KNOB_Y + 7.0), (LEAF[2], KNOB_Y + 4.0)], 83, amp=0.2)
        plate = _R(DOOR[2], CHAIN_Y - 7.0, DOOR[2] + 5.0, CHAIN_Y + 7.0, 84, 0.2)
        return [], [stop, leaf, knob, plate]
    # open: the leaf turns about its hinge on the jamb; we see its face, foreshortened
    xw = DOOR[2] + DOOR_W * math.sin(th) + 24.0 * abs(math.cos(th))
    leaf = _R(DOOR[2] - 2.0, LEAF[1], xw, LEAF[3], 85, 0.4)
    kx = DOOR[2] + DOOR_W * 0.86 * math.sin(th)
    knob = bass.orient(bass.ring_pts((kx, KNOB_Y), 8.0, seed=86, n=12, amp=0.2), True)
    return [leaf], [stop, knob]


def chain_links(room, t=0.0, n=7):
    """Link centres of the door chain in profile: from its anchor on the frame to the slide
    on the leaf. Shut with the chain on, or off: it hangs in a loop; ajar on the chain: taut."""
    a = (DOOR[2] + 2.0, CHAIN_Y)
    th = math.radians(door_angle(room))
    if room.chain == "on" and th > 1e-3:
        b = (DOOR[2] + DOOR_W * 0.9 * math.sin(th), CHAIN_Y)
        sag = 4.0
    else:
        b = (DOOR[2] + 4.0, CHAIN_Y + 4.0)
        sag = 46.0
    out = []
    for i in range(n):
        u = (i + 0.5) / n
        out.append((lerp(a[0], b[0], u), lerp(a[1], b[1], u) + sag * math.sin(math.pi * u)))
    return out


def hall_beam_pts(room):
    """The landing light thrown into the room through the open door: a flat wedge (stage px)."""
    th = clamp(room.door)
    reach = 520.0 * th
    x = DOOR[2]
    return [(x, DOOR[1] + 6.0), (x + reach, DOOR[1] + 6.0 + 0.55 * reach), (x + reach * 1.25, FLOOR), (x, FLOOR)]


# ============================================================================ drawing the stage
def _rim(c, polys, dx=2.6, dy=-1.8, color=STEEL):
    """Cold light catching the window-side edges of an ink shape (dark room)."""
    c.save()
    c.translate(dx, dy)
    bass.fill_polys(c, polys, color)
    c.restore()


def draw_interior(c, t, room, figures=None):
    """Her room inside its walls, in stage px: the field, the light, the furniture, the
    curtain, the open door leaf, then `figures(c)`."""
    lit = room.lit
    bg = room_bg(room)
    pad = 10.0
    bass.fill_polys(c, [bass.cut_rect(ROOM[0] - pad, ROOM[1] - pad, ROOM[2] + pad, ROOM[3] + pad, seed=11, amp=0.5)], bg)
    ink = INK
    # the light: the lamp's cone (lit), the moon through the window (dark), the landing
    if lit:
        x = X_LAMP
        bass.fill_polys(c, [bass.orient([(x - 64.0, 950.0), (x + 64.0, 950.0), (x + 236.0, FLOOR), (x - 236.0, FLOOR)],
                                        True)], PAPER, 0.10)
    else:
        w0, w1 = WINDOW[1] + 8.0, sash_lift_y(room) + 13.0
        bass.fill_polys(c, [bass.orient([(WINDOW[0], w0), (WINDOW[0], WINDOW[3]), (WINDOW[0] - 520.0, FLOOR),
                                         (WINDOW[0] - 760.0, FLOOR)], True)], STEEL, 0.20)
    if room.hall > 0.0 and room.door > 0.0:
        bass.fill_polys(c, [bass.orient(hall_beam_pts(room), True)], AMBER, 0.26 * room.hall)
    # the clock on the back wall
    hms = room.clock or clock_time(room.film_t)
    draw_clock(c, CLOCK_P, CLOCK_R, hms, face=PAPER if lit else lerp(STEEL, PAPER, 0.25), ink=ink,
               rim=ink)
    # furniture
    stove = stove_polys()
    table = table_polys()
    phone, dial_c, dial_r = phone_parts()
    lamp = lamp_polys()
    rod = curtain_rod_polys()
    furn = stove + table + phone + lamp + rod
    if not lit:
        _rim(c, furn)
    bass.fill_polys(c, furn, ink)
    disc, holes = dial_polys(dial_c, dial_r)
    bass.fill_polys(c, [disc], PAPER if lit else STEEL)
    bass.fill_polys(c, holes, ink)
    # the bulb and the pull cord
    K.dot(c, LAMP_BULB, 12.0, PAPER if lit else lerp(DEEP, STEEL, 0.5), seed=44)
    ce = cord_end(room, t)
    bass.line_band(c, [CORD_TOP, ce], ink, width=2.6, seed=45)
    K.dot(c, ce, 5.0, ink, seed=46)
    if room.flame and room.kettle:
        bass.fill_polys(c, flame_polys(t), PAPER)
    if room.kettle:
        draw_kettle(c, KETTLE_BASE, KETTLE_S, 0.0, t, steam=room.steam, whistle=room.whistle, edge=None if lit else STEEL)
    if room.mug:
        draw_mug(c, MUG_HC, MUG_S, -1, t, steam=0.0, edge=bg)
    # the curtain, and the cuts of its folds
    cp = curtain_pts(room, t)
    if not lit:
        _rim(c, [cp], dx=3.5, dy=-1.0)
    bass.fill_polys(c, [cp], ink)
    c.save()
    c.set_source_rgb(*(lerp(bg, ink, 0.35) if lit else lerp(STEEL, ink, 0.45)))
    c.set_line_width(2.4)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    for ln in curtain_pleats(room, t):
        c.new_path()
        bass.draw.poly(c, ln, close=False)
        c.stroke()
    c.restore()
    # the open door leaf (behind whoever comes through)
    leaf_room, _ = door_polys(room)
    if leaf_room:
        if room.hall > 0.0:
            _rim(c, leaf_room, dx=-3.0, dy=0.0, color=lerp(INK, AMBER, 0.6 * room.hall))
        bass.fill_polys(c, leaf_room, ink)
    if figures is not None:
        figures(c)


def draw_walls(c, t, room):
    """What lies over the figures in stage px: the window's sills and sashes, the door in its
    doorway, the chain, the light under the door."""
    ink, glass, _ = window_polys(room)
    if not room.lit:
        _rim(c, ink, dx=-2.0, dy=0.0)
    bass.fill_polys(c, glass, GLASS, 0.55)
    bass.fill_polys(c, ink, INK)
    _, doorway = door_polys(room)
    bass.fill_polys(c, doorway, INK)
    if room.chain != "snapped":
        links = chain_links(room, t)
        for i, p in enumerate(links):
            K.dot(c, p, 3.4, INK if room.lit else STEEL, seed=90 + i)
    if room.hall > 0.0 and room.door <= 0.0:
        # the landing light under the door, and its spill along her floor
        bass.fill_polys(c, [bass.cut_rect(LEAF[0], FLOOR - 5.0, DOOR[2], FLOOR, seed=91, amp=0.2)], AMBER, room.hall)
        bass.fill_polys(c, [bass.orient([(DOOR[2], FLOOR - 5.0), (DOOR[2] + 260.0, FLOOR - 1.0), (DOOR[2] + 260.0, FLOOR),
                                         (DOOR[2], FLOOR)], True)], AMBER, 0.6 * room.hall)


def section_lit(room, his=True):
    lit = {}
    if room.lit:
        lit[(K.HER_B, K.HER_FLOOR)] = AMBER
    if his:
        lit[(K.HIS_B, K.HIS_FLOOR)] = AMBER
    return lit


def _stage_matrix():
    """section px -> stage px."""
    m = cairo.Matrix()
    m.translate(X0 - SEC_X0 * S, FLOOR - SEC_FLOOR * S)
    m.scale(S, S)
    return m


def slot_color(room):
    """The window opening in the cut wall: the building's dark (as the section draws every
    window) while her lamp is on; the night itself once it is off."""
    return DEEP if room.lit else NIGHT


def section_room(c, t, room, figures=None, outside=None):
    """Her room drawn into the SECTION (c in section px): call it from a K.draw_section
    people callback for (K.HER_B, K.HER_FLOOR). It covers the kit's stand-in furniture with
    this set (clipped to the room), fills the window opening, then draws outside(c) unclipped;
    both callbacks draw in stage px."""
    sm = _stage_matrix()
    inv = cairo.Matrix(*sm)
    inv.invert()
    rect = K.her_room()
    c.save()
    c.new_path()
    c.rectangle(rect[0] - 1.0, rect[1] - 1.0, rect[2] - rect[0] + 2.0, rect[3] - rect[1] + 2.0)
    c.clip()
    c.transform(inv)
    draw_interior(c, t, room, figures)
    c.restore()
    c.save()
    c.transform(inv)
    bass.fill_polys(c, [bass.orient([(WINDOW[0] - 1.0, WINDOW[1] - 1.0), (WINDOW[2] + 1.0, WINDOW[1] - 1.0),
                                     (WINDOW[2] + 1.0, WINDOW[3] + 1.0), (WINDOW[0] - 1.0, WINDOW[3] + 1.0)], True)],
                    slot_color(room))
    if outside is not None:
        outside(c)
    c.restore()


def neighbours(t, lit):
    """The default `others`: the section's other rooms as s01 leaves them. A dark room is
    folk.asleep's (the woman asleep in her chair under her, the old man at his radio, the
    sleeper across the street); a lit one is left to the scene."""
    def cb(c, b, n, rect):
        if (b, n) not in lit:
            F.asleep(c, b, n, rect, t)
    return cb


def section_people(t, room, figures=None, others=None, lit=None, outside=None):
    """A `people` callback for K.draw_section that draws her room (this set) at section scale,
    with figures(c) / outside(c) in stage px, and hands every other room to
    others(c, b, n, rect) (default: neighbours(t, lit))."""
    if others is None:
        others = neighbours(t, section_lit(room) if lit is None else lit)

    def cb(c, b, n, rect):
        if b is K.HER_B and n == K.HER_FLOOR:
            section_room(c, t, room, figures, outside)
        else:
            others(c, b, n, rect)
    return cb


def draw_stage(c, t, room, cam=CANON, figures=None, others=None, his=True, beams=True, ladder=0.0,
               lamp_on=True, numbers=None, street_doors=(), overlay=None, outside=None, sky_lit=0.0):
    """The side stage: the kit's section around her room, her room on it, and the walls over
    the figures, through camera `cam` (stage px -> frame px). figures(c) and outside(c) draw
    in stage px (see FIGURES); overlay(c), if given, draws over everything in stage px
    (annotations that ride the set)."""
    c.save()
    cam.apply(c)
    c.save()
    c.transform(_stage_matrix())
    lit = section_lit(room, his)
    K.draw_section(c, t, lit=lit, people=section_people(t, room, figures, others, lit, outside),
                   open_windows={K.HER_B: {K.HER_FLOOR}}, open_doors={K.HER_B: {K.HER_FLOOR}},
                   street_doors=street_doors, beams=beams, ladder=ladder, numbers=numbers, lamp_on=lamp_on,
                   sky_lit=sky_lit)
    c.restore()
    draw_walls(c, t, room)
    if overlay is not None:
        overlay(c)
    c.restore()


# ============================================================================ the window view
# NEAR layer: view px (frame px at WCANON), her window face on from inside the room
WV_GLASS = (276.0, 340.0, 804.0, 1380.0)  # the opening inside the casing
CASE_W = 36.0                             # the casing's width
WV_MEET = 860.0                           # the meeting rails, shut
WV_LIFT = 470.0                           # the lower sash's travel (room.window = 1)
WV_ROD_Y = 276.0                          # the curtain rod over the casing
STILE, TOP_RAIL, MEET_RAIL, BOT_RAIL = 22.0, 24.0, 17.0, 34.0
# FAR layer: the Bass elevation, B.HIS_WIN's centre at FAR_AT (view px), scaled FAR_F
FAR_AT = (652.0, 640.0)
FAR_F = 1.0
FAR_PAR = 0.3                             # how much the far layer moves with the camera's zoom
FAR_INK = lerp(INK, NIGHT, 0.42)          # his facade at night, a shade off the ink of her window
FAR_MOON = (492.0, 394.0)                 # the moon, elevation px: up in the gap between the roofs
FAR_LAMP = (566.0, 1236.0)                # the street lamp's head, elevation px (in the gap, on his side)


def elev_to_view(p):
    hc = B.centre(B.HIS_WIN)
    return (FAR_AT[0] + (p[0] - hc[0]) * FAR_F, FAR_AT[1] + (p[1] - hc[1]) * FAR_F)


def _elev_matrix():
    hc = B.centre(B.HIS_WIN)
    m = cairo.Matrix()
    m.translate(FAR_AT[0] - hc[0] * FAR_F, FAR_AT[1] - hc[1] * FAR_F)
    m.scale(FAR_F, FAR_F)
    return m


def far_cam(cam):
    """The far layer's camera: the same aim point, a fraction of the zoom (a dolly's parallax)."""
    return Cam(cam.x, cam.y, 1.0 + (cam.z - 1.0) * FAR_PAR, cam.rot)


def view_point(cam, p, layer="near"):
    """A view point (near: view px; far: elevation px) -> frame px through `cam`."""
    if layer == "far":
        return far_cam(cam).to_frame(elev_to_view(p))
    return cam.to_frame(p)


def _hisw_view():
    a, b = elev_to_view(B.HIS_WIN[:2]), elev_to_view(B.HIS_WIN[2:])
    return (a[0], a[1], b[0], b[1])


WV = dict(glass=WV_GLASS, his_win=_hisw_view(), sill_y=WV_GLASS[3], rod_y=WV_ROD_Y,
          stool=(WV_GLASS[0] - CASE_W - 24.0, WV_GLASS[3], WV_GLASS[2] + CASE_W + 24.0, WV_GLASS[3] + 26.0),
          eye_level=700.0)


def view_lift(room):
    return WV_LIFT * clamp(room.window)


def _far_lamp(c, lamp_on=True):
    """The street lamp in the gap, in elevation px: its post, arm and hood, the bulb, and its
    light falling to the street (flat, translucent)."""
    hx, hy = FAR_LAMP
    if lamp_on:
        bass.fill_polys(c, [bass.orient([(hx - 9.0, hy + 4.0), (hx + 9.0, hy + 4.0), (hx + 150.0, 2400.0),
                                         (hx - 150.0, 2400.0)], True)], AMBER, 0.12)
    px = hx + 48.0
    bass.fill_polys(c, [bass.orient([(px - 4.0, hy - 20.0), (px + 4.0, hy - 20.0), (px + 5.0, 2400.0), (px - 5.0, 2400.0)], True),
                        bass.line_pts([(px, hy - 18.0), (px - 16.0, hy - 32.0), (hx, hy - 24.0)], width=5.0, seed=951),
                        bass.orient([(hx - 17.0, hy - 6.0), (hx + 17.0, hy - 6.0), (hx + 10.0, hy - 25.0),
                                     (hx - 10.0, hy - 25.0)], True)], FAR_INK)
    if lamp_on:
        K.dot(c, (hx, hy - 1.0), 7.5, AMBER, seed=952)


def draw_far(c, t, far=None, tb=None, his_lit=True, windows=None, sky_lit=0.0, lamp=True, moon=True,
             facade=True, lamp_on=True):
    """The far layer in elevation px: the night, the moon, the far city, the street lamp in the
    gap, his building with its windows, and far(c, B.HIS_WIN, t) in his window."""
    bass.fill_polys(c, [bass.cut_rect(-900.0, -900.0, 2000.0, 2900.0, seed=940, amp=0.5)], NIGHT)
    if moon:
        K.moon(c, FAR_MOON, r=66.0)
    K.skyline(c, lit=sky_lit)
    if lamp:
        _far_lamp(c, lamp_on)
    if not facade:
        return
    bass.fill_polys(c, [bass.cut_rect(B.RIGHT_B[0], B.RIGHT_B[1], B.RIGHT_B[2], 2900.0, seed=21)], FAR_INK)
    # the cornice and a string course: thin steel lines where the moon catches the facade
    bass.fill_polys(c, [bass.cut_rect(B.RIGHT_B[0] - 8.0, B.RIGHT_B[1] - 2.0, B.RIGHT_B[2] + 8.0, B.RIGHT_B[1] + 12.0,
                                      seed=941, amp=0.4)], FAR_INK)
    bass.fill_polys(c, [bass.cut_rect(B.RIGHT_B[0] - 8.0, B.RIGHT_B[1] - 2.0, B.RIGHT_B[2] + 8.0, B.RIGHT_B[1] + 2.0,
                                      seed=942, amp=0.3)], lerp(FAR_INK, STEEL, 0.6))
    for i, r in enumerate(B.RIGHT_WIN):
        col = windows(i, r) if windows is not None else None
        if col is None:
            if tb is not None:
                col = K.window_color(r, tb)
            else:
                col = AMBER if (r == B.HIS_WIN and his_lit) else SHUT
        bass.fill_polys(c, [bass.cut_rect(*r, seed=int(r[0] + r[1]))], col)
        # the sill under each window, its top edge in the moonlight
        bass.fill_polys(c, [bass.cut_rect(r[0] - 10.0, r[3], r[2] + 10.0, r[3] + 12.0, seed=int(r[0] + 3 * r[1]), amp=0.3)],
                        FAR_INK)
        bass.fill_polys(c, [bass.cut_rect(r[0] - 10.0, r[3], r[2] + 10.0, r[3] + 2.5, seed=int(r[0] + 5 * r[1]), amp=0.2)],
                        lerp(FAR_INK, STEEL, 0.5))
    if far is not None:
        c.save()
        K.clip_rect(c, B.HIS_WIN)
        far(c, B.HIS_WIN, t)
        c.restore()


def _wv_sash_polys(room):
    """(ink frames, glass rects, open rect or None) of the two sashes, view px."""
    x0, y0, x1, y1 = WV_GLASS
    lift = view_lift(room)
    ink, glass = [], []
    # the upper sash (outside track, behind)
    u0, u1 = y0, WV_MEET + MEET_RAIL / 2.0
    ink += [_R(x0, u0, x1, u0 + TOP_RAIL, 501, 0.3), _R(x0, u1 - MEET_RAIL, x1, u1, 502, 0.3),
            _R(x0, u0, x0 + STILE, u1, 503, 0.3), _R(x1 - STILE, u0, x1, u1, 504, 0.3)]
    glass.append((x0 + STILE, u0 + TOP_RAIL, x1 - STILE, u1 - MEET_RAIL))
    # the lower sash (inside track, in front), raised by `lift`
    l0, l1 = WV_MEET - MEET_RAIL / 2.0 - lift, y1 - lift
    ink += [_R(x0 - 3.0, l0, x1 + 3.0, l0 + MEET_RAIL, 505, 0.3), _R(x0 - 3.0, l1 - BOT_RAIL, x1 + 3.0, l1, 506, 0.3),
            _R(x0 - 3.0, l0, x0 + STILE, l1, 507, 0.3), _R(x1 - STILE, l0, x1 + 3.0, l1, 508, 0.3)]
    glass.append((x0 + STILE, l0 + MEET_RAIL, x1 - STILE, l1 - BOT_RAIL))
    # the lock on the meeting rail, the two lifts on the bottom rail
    mx = (x0 + x1) / 2.0
    ink.append(_P([(mx - 22.0, l0 + 2.0), (mx + 22.0, l0 + 2.0), (mx + 16.0, l0 - 9.0), (mx + 4.0, l0 - 14.0),
                   (mx - 10.0, l0 - 12.0), (mx - 22.0, l0 - 6.0)], 509, amp=0.2))
    for lx in (x0 + 74.0, x1 - 74.0):
        ink.append(_P([(lx - 15.0, l1 - BOT_RAIL + 6.0), (lx + 15.0, l1 - BOT_RAIL + 6.0), (lx + 15.0, l1 - BOT_RAIL + 14.0),
                       (lx + 8.0, l1 - BOT_RAIL + 14.0), (lx + 8.0, l1 - BOT_RAIL + 24.0), (lx - 8.0, l1 - BOT_RAIL + 24.0),
                       (lx - 8.0, l1 - BOT_RAIL + 14.0), (lx - 15.0, l1 - BOT_RAIL + 14.0)], 510 + int(lx), amp=0.15))
    opening = (x0, l1, x1, y1) if lift > 2.0 else None
    return ink, glass, opening


def _wv_casing_polys():
    x0, y0, x1, y1 = WV_GLASS
    w = CASE_W
    return [
        _R(x0 - w - 14.0, y0 - w - 14.0, x1 + w + 14.0, y0 - w + 2.0, 521, 0.4),          # the head's cap
        _R(x0 - w - 4.0, y0 - w, x1 + w + 4.0, y0 + 2.0, 522, 0.4),                       # the head casing
        _R(x0 - w, y0, x0 + 4.0, y1 + 4.0, 523, 0.4), _R(x1 - 4.0, y0, x1 + w, y1 + 4.0, 524, 0.4),
        _R(x0 - w - 24.0, y1, x1 + w + 24.0, y1 + 26.0, 525, 0.4),                        # the stool
        _R(x0 - w + 4.0, y1 + 25.0, x1 + w - 4.0, y1 + 64.0, 526, 0.4),                   # the apron
    ]


def _wv_curtain(room, t):
    """The curtain face on: one panel gathered at the right of the window, hanging from rings
    on the rod, past the bottom of the frame. With wind it swings in off the wall, its inner
    edge sweeping across the glass and its hem lifting into view, fluttering (on twos).
    Returns (outline, fold lines)."""
    tt = B.twos(t)
    b = clamp(room.wind)
    x0, y0, x1, y1 = WV_GLASS
    top = WV_ROD_Y + 10.0
    hem = 2060.0 - b * 760.0
    n = 36
    inner, outer, folds = [], [], [[], [], []]
    for i in range(n + 1):
        u = i / n
        y = lerp(top, hem, u)
        fl = b * u * (26.0 * math.sin(2.0 * math.pi * (1.2 * tt - 1.5 * u)) + 12.0 * math.sin(2.0 * math.pi * (2.7 * tt - 3.0 * u) + 0.7))
        swing = b * (330.0 * u ** 1.4) + fl
        xi = x1 - 40.0 + 10.0 * math.sin(u * 7.0) * (1.0 - b) - swing - 22.0 * u
        xo = x1 + 116.0 + 16.0 * u - b * (120.0 * u ** 1.8) + 0.4 * fl
        inner.append((xi, y))
        outer.append((xo, y))
        for j, f in enumerate((0.26, 0.5, 0.74)):
            folds[j].append((lerp(xi, xo, f + 0.04 * math.sin(u * 5.0 + j)), y))
    # the rings make a scalloped top; the hem a soft wave
    scallop = []
    for i in range(7):
        u = i / 6.0
        scallop.append((lerp(inner[0][0], outer[0][0], u), top - 4.0 * math.sin(math.pi * (u * 6.0 % 1.0))))
    wave = [(lerp(outer[-1][0], inner[-1][0], u), hem + (8.0 + 10.0 * b) * math.sin(math.pi * 3.0 * u + 4.0 * tt * b))
            for u in (0.2, 0.4, 0.6, 0.8)]
    outline = bass.orient(scallop + outer + wave + inner[::-1], True)
    lines = [f[2:-2] for f in folds]
    return outline, lines


def _wv_rod_polys():
    x0, y0, x1, y1 = WV_GLASS
    xa, xb = x0 - CASE_W - 70.0, x1 + CASE_W + 70.0
    out = [_R(xa, WV_ROD_Y - 5.0, xb, WV_ROD_Y + 5.0, 531, 0.2)]
    for x in (xa, xb):
        out.append(bass.orient(bass.ring_pts((x, WV_ROD_Y), 12.0, seed=532 + int(x), n=14, amp=0.2), True))
    for x in (x0 - CASE_W - 30.0, x1 + CASE_W + 30.0):                      # brackets
        out.append(_R(x - 7.0, WV_ROD_Y - 2.0, x + 7.0, WV_ROD_Y + 26.0, 534 + int(x), 0.2))
    return out


def draw_window_view(c, t, room, cam=WCANON, far=None, tb=None, his_lit=True, windows=None, sky_lit=0.0,
                     lamp=True, moon=True, facade=True, lamp_on=True, curtain=True):
    """Her window face on from inside (see THE WINDOW VIEW), through camera `cam`."""
    bg = room_bg(room)
    lit = room.lit
    ink_frames, glass, opening = _wv_sash_polys(room)
    # the wall
    c.save()
    cam.apply(c)
    bass.fill_polys(c, [bass.cut_rect(-2600.0, -2600.0, 3700.0, 4600.0, seed=500, amp=0.5)], bg)
    c.restore()
    # the night through the opening (the far layer, its own camera)
    c.save()
    cam.apply(c)
    K.clip_rect(c, WV_GLASS)
    cam_inv = cam.matrix()
    cam_inv.invert()
    c.transform(cam_inv)
    far_cam(cam).apply(c)
    c.transform(_elev_matrix())
    draw_far(c, t, far=far, tb=tb, his_lit=his_lit, windows=windows, sky_lit=sky_lit, lamp=lamp, moon=moon,
             facade=facade, lamp_on=lamp_on)
    c.restore()
    c.save()
    cam.apply(c)
    # the glass: her lamp's warm reflection on it while lit; a cold sheen in the dark
    for g in glass:
        poly = bass.orient([(g[0], g[1]), (g[2], g[1]), (g[2], g[3]), (g[0], g[3])], True)
        bass.fill_polys(c, [poly], AMBER if lit else STEEL, 0.13 if lit else 0.07)
        c.save()
        K.clip_rect(c, g)
        for k_, (o, w) in enumerate(((0.18, 34.0), (0.32, 12.0))):
            ox = lerp(g[0], g[2], o)
            bass.fill_polys(c, [bass.orient([(ox, g[1]), (ox + w, g[1]), (ox + w - 260.0, g[3]), (ox - 260.0, g[3])], True)],
                            PAPER, 0.05 if lit else 0.04)
        c.restore()
    # sashes and casing, with a cold rim on the window side in the dark
    case = _wv_casing_polys()
    if not lit:
        _rim(c, case, dx=-3.0, dy=-2.5)
    bass.fill_polys(c, ink_frames + case, INK)
    if curtain:
        outline, lines = _wv_curtain(room, t)
        if not lit:
            _rim(c, [outline], dx=-4.0, dy=0.0)
        bass.fill_polys(c, [outline], INK)
        c.set_source_rgb(*(lerp(bg, INK, 0.45) if lit else lerp(STEEL, INK, 0.5)))
        c.set_line_width(3.0)
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        for ln in lines:
            c.new_path()
            bass.draw.poly(c, ln, close=False)
            c.stroke()
    bass.fill_polys(c, _wv_rod_polys(), INK)
    c.restore()


# --- heads and shoulders from behind, for the over-the-shoulder shots. Local units: origin at
# the nape (where the neck meets the shoulders), y down, s = 1: a head about 230 px high.
def _closed_spline(pts, n=6):
    """Catmull-Rom through pts as a closed loop."""
    P = list(pts)
    m = len(P)
    out = []
    for i in range(m):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % m], P[(i + 2) % m]
        for k_ in range(n):
            u = k_ / n
            u2, u3 = u * u, u * u * u
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * u + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u3) for j in (0, 1)))
    return out


def _sym(half):
    """A left-right symmetric outline from its left half (top to bottom, x < 0)."""
    return half + [(-x, y) for x, y in reversed(half)]


def _back_her(turn):
    """Her from behind, cut like the Bass close-ups' bob: a faceted crown, straight sides flaring
    a little to a blunt cut, the hem of the hair marked where it lies over her neck."""
    hx = 5.0 * turn
    shoulders = _sym([(-40.0, -12.0), (-100.0, 8.0), (-168.0, 34.0), (-216.0, 64.0), (-238.0, 120.0), (-246.0, 300.0),
                      (-252.0, 660.0)])
    neck = [(-33.0, 4.0), (-30.0, -80.0), (30.0, -80.0), (33.0, 4.0)]
    bob = [(hx + x, y) for x, y in _sym([(-26.0, -281.0), (-70.0, -266.0), (-98.0, -232.0), (-108.0, -180.0),
                                         (-112.0, -110.0), (-114.0, -62.0), (-104.0, -46.0), (-40.0, -44.0)])]
    lines = [[(hx - 36.0, -47.0), (hx + 36.0, -47.0)],                       # the hair's hem over her neck
             [(-58.0, 10.0), (0.0, 19.0), (58.0, 10.0)]]                    # the back of her dress at the nape
    return [shoulders, neck, bob], lines, (hx + 30.0, -160.0), (hx, -281.0), (shoulders[0], shoulders[-1])


def _back_him(turn):
    """Him from behind: the hat (brim, dented crown, band), the turned-up collar, the shoulders."""
    hx = 5.0 * turn
    shoulders = _sym([(-110.0, 8.0), (-204.0, 30.0), (-270.0, 68.0), (-300.0, 130.0), (-312.0, 300.0), (-326.0, 660.0)])
    collar = [(-112.0, 26.0), (-110.0, -40.0), (-104.0, -112.0), (-58.0, -104.0), (-8.0, -98.0), (0.0, -88.0), (8.0, -98.0),
              (58.0, -104.0), (104.0, -112.0), (110.0, -40.0), (112.0, 26.0)]
    head = [(hx + x, y) for x, y in _sym([(-64.0, -86.0), (-72.0, -132.0), (-75.0, -178.0), (-68.0, -214.0)])]
    ears = [[(hx - 72.0, -172.0), (hx - 85.0, -164.0), (hx - 86.0, -146.0), (hx - 78.0, -134.0), (hx - 70.0, -138.0)],
            [(hx + 72.0, -172.0), (hx + 85.0, -164.0), (hx + 86.0, -146.0), (hx + 78.0, -134.0), (hx + 70.0, -138.0)]]
    brim = [(hx - 186.0, -216.0), (hx - 120.0, -206.0), (hx, -200.0), (hx + 120.0, -206.0), (hx + 186.0, -216.0),
            (hx + 188.0, -221.0), (hx + 120.0, -232.0), (hx, -237.0), (hx - 120.0, -232.0), (hx - 188.0, -221.0)]
    crown = [(hx + x, y) for x, y in [(-94.0, -226.0), (-91.0, -288.0), (-74.0, -334.0), (-40.0, -352.0),
                                      (-12.0, -350.0), (0.0, -340.0), (12.0, -350.0), (40.0, -352.0),
                                      (74.0, -334.0), (91.0, -288.0), (94.0, -226.0), (0.0, -222.0)]]
    lines = [[(hx - 93.0, -252.0), (hx, -248.0), (hx + 93.0, -252.0)],       # the hat band
             [(0.0, -86.0), (0.0, -30.0)]]                                   # the collar's back seam
    return [shoulders, collar, head] + ears + [brim, crown], lines, (hx + 26.0, -160.0), (hx, -352.0), (shoulders[0], shoulders[-1])


def _back_matrix(base, s, t):
    br = 1.0 + 0.006 * math.sin(2.0 * math.pi * 0.22 * B.twos(t))
    m = cairo.Matrix()
    m.translate(*base)
    m.scale(s, s * br)
    return m


def back_marks(who, base, s, t=0.0, turn=0.0):
    """Where draw_back(...) puts her eye, crown, nape, shoulders and ears (px), without drawing:
    for a look or a shout that must pass behind the head."""
    _, _, eye, crown, shp = (_back_her if who == "her" else _back_him)(turn)
    m = _back_matrix(base, s, t)
    hx = 5.0 * turn
    ear = 108.0 if who == "her" else 80.0
    return {"eye": m.transform_point(*eye), "crown": m.transform_point(*crown), "nape": tuple(base),
            "shoulders": (m.transform_point(*shp[0]), m.transform_point(*shp[1])),
            "ears": (m.transform_point(hx - ear, -150.0), m.transform_point(hx + ear, -150.0))}


def draw_back(c, who, base, s, edge=None, t=0.0, turn=0.0, color=INK, cut=None):
    """A head and shoulders from behind, nape at `base` (px), scale s (see above): "her" (the
    bob) or "him" (the hat, the turned-up collar). edge strokes the outline (so it reads on a
    field of its own colour); cut is the colour of the cut lines (the bob's turned-under tips,
    the hat band; default: edge). turn (-1..1) shifts the head a little, as if she turned it.
    Breathes (on twos). Returns {'eye', 'crown', 'nape', 'shoulders', 'ears'} in px."""
    polys, lines, eye, crown, shp = (_back_her if who == "her" else _back_him)(turn)
    m = _back_matrix(base, s, t)
    cut_polys = []
    for i, pts in enumerate(polys):
        q = [m.transform_point(*p) for p in pts]
        cut_polys.append(_S(q, 560 + i, sag=0.45, amp=0.25, max_len=40.0))
    if edge is not None:
        B.edged(c, cut_polys, color, edge, 5.0)
    else:
        bass.fill_polys(c, cut_polys, color)
    cc = cut if cut is not None else edge
    if cc is not None:
        c.save()
        c.set_source_rgb(*cc)
        c.set_line_width(max(2.0, 3.2 * s))
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        for ln in lines:
            pts = _spline([m.transform_point(*p) for p in ln], 6) if len(ln) > 2 else [m.transform_point(*p) for p in ln]
            c.new_path()
            bass.draw.poly(c, pts, close=False)
            c.stroke()
        c.restore()
    return back_marks(who, base, s, t, turn)


def rim_cutout(c, fig, st, pose, facing=1, dx=3.0, dy=-2.0, rim=STEEL, **kw):
    """A cut-out in the dark: a cold edge on the window side, then the figure in ink.
    Draw inside B.place(...) (dx, dy are figure units)."""
    c.save()
    c.translate(dx, dy)
    B.draw_cutout(c, fig, st, pose, rim, facing=facing, **kw)
    c.restore()
    return B.draw_cutout(c, fig, st, pose, INK, facing=facing, **kw)
