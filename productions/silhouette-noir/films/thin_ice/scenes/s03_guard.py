"""s03 GUARD (32-48): the guard in his hut; the watch and the photograph; out into the wind; the
scrap on the barb; the prints, big and small; the whistle; into the woods after them.

  0.0-2.0   The guardhouse in section: a small hut under the moon, snow on its roof, the stove's
            firebox glowing AMBER, a window full of night, the bench, the lantern lit on the floor.
            The guard warms his hands at the stove.
  2.0-2.4   He takes out his pocket watch.
  2.4-4.75  CU: the watch in his glove. It springs open (2.5, click): 11:58, the seconds ticking,
            and in the lid a small oval photograph of a girl in a pompom hat. His thumb moves over
            it (3.1-4.1). He closes it (4.5, click).
  4.75-7.0  The hut: he pockets it, turns, stoops for the lantern, crosses to the door; the wind
            throws it open (6.2), snow streams in, the fire flares; he goes out into the night.
  7.0-9.0   The fence view (s02's camera, closer). Beyond the wire he walks along the fence from
            the right, the lantern swinging, its pool on the snow, his hobnailed steps. He stops at
            the barb and raises the lantern.
  9.0-10.0  CU: his gloved fingers lift the scrap off the barb in the lantern light.
  10.0-11.0 The page: he lowers the lantern and its pool slides over the prints, big and small,
            leading away north.
  11.0-12.0 CU, from above: his glove touches a small print.
  12.0-12.75 CU, his profile: he blows his whistle, twice (12.0, 12.4).
  12.75-14.0 The page, wide: far off along the fence, lanterns wake one by one (13.0, 13.25, 13.5);
            the searchlight leaves its sweep and swings north over the woods.
  14.0-16.0 The page: he follows the prints into the woods; the trees close over him and his
            lantern's glow sinks into the black, smaller and smaller. Cut.
"""
import math

from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.thin_ice import cast as C
from films.thin_ice import faces as F
from films.thin_ice import kit as K
from films.thin_ice import world as W
from films.thin_ice.scenes import _lib_dir as L
from films.thin_ice.scenes.s02_fence import (PRINT_C, SNAG_X, TROUGH_G, TROUGH_M, approach_prints, trough_top,
                                             woods_edge)

FILM_T0 = 32.0
T_WATCH = 2.0                # he takes out the watch
T_CU_W = (2.4, 4.75)         # the watch close-up
T_OPEN_W, T_SHUT_W = 2.5, 4.5
T_THUMB = (3.1, 4.1)
T_TURN = 5.1                 # he turns from the stove ...
T_STOOP = (5.1, 5.4)         # ... stoops for the lantern ...
T_TO_DOOR = (5.4, 6.1)       # ... crosses to the door
T_DOOR = 6.2                 # the wind throws it open
T_OUT = (6.35, 7.0)
T_FENCE = 7.0
T_STOP = 8.7
T_RAISE = (8.72, 8.95)
T_CU_S = 9.0                 # the glove takes the scrap
T_PINCH = (9.25, 9.4)
T_LIFT = (9.45, 9.95)
T_PAGE = 10.0
T_CU_P = 11.0                # the glove on a small print
T_TOUCH = 11.45
T_WHISTLE = (12.0, 12.4)
T_WIDE = 12.75
T_WAKE = (13.0, 13.25, 13.5)
T_SWING = (12.9, 13.9)       # the searchlight swings north
T_WOODS = 14.0

# his prints: along the fence to the crossing (s03's stage), then up the path to the woods
GF_FENCE = tuple(W.walk_prints([(W.GUARDHOUSE[0] - 1.0, W.GUARDHOUSE[1] - 2.4), (W.CROSS[0] + 1.2, W.FENCE_N + 1.0),
                                (W.CROSS[0] + 1.0, W.FENCE_N + 2.2)], "guard", 0.74, 0.4, seed=10))
G_ROUTE = W.offset_path(list(W.PATH), -0.55)
GF_PATH = tuple(W.walk_prints(G_ROUTE, "guard", 0.74, 0.45, seed=11, s1=11.0))
G_STAND = (W.CROSS[0] + 1.05, W.FENCE_N + 2.0)     # where he stands over their prints
FAR_LAMPS = ((12.0, -128.7), (69.0, -128.7), (26.5, -127.4))


# ============================================================================ the guardhouse, in section
HUT_PPM = 260.0
FLOOR = 1500.0
IN_L, IN_R = 300.0, 1040.0   # the walls' inner faces
WALL_W = 40.0
EAVE = 900.0
APEX = 640.0
DOOR_Y = 990.0               # the door's head, in the left wall
STOVE = (830.0, 980.0)       # the stove's body
STOVE_TOP = 1270.0
FIREBOX = (905.0, 1385.0)
WINDOW = (430.0, 610.0, 990.0, 1150.0)
LAMP_FLOOR = (585.0, FLOOR)
WALL_IN = lerp(K.NIGHT, K.INK, 0.45)
MOON_HUT = (850.0, 330.0)


def _flicker(t, k=1.0):
    tt = K.twos(t)
    return 1.0 + k * (0.08 * math.sin(tt * 17.0) + 0.05 * math.sin(tt * 31.0 + 1.0))


def _room(c):
    c.new_path()
    for i, p in enumerate([(IN_L, EAVE), (650.0, APEX + 46.0), (IN_R, EAVE), (IN_R, FLOOR), (IN_L, FLOOR)]):
        (c.move_to if i == 0 else c.line_to)(*p)
    c.close_path()


def _hut(c, t, door=0.0, fire=1.0, inside=None):
    """The guardhouse cut through, looking north: the night and the moon over it, the snow round
    it, the room, the stove's light; inside(c) draws the guard; then the cut walls and the roof."""
    ft = FILM_T0 + t
    K.fill(c, K.NIGHT)
    K.stars(c, ft, y1=1400.0)
    K.moon(c, MOON_HUT, r=64.0)
    K.poly(c, [(-40.0, FLOOR - 6.0), (1120.0, FLOOR - 6.0), (1120.0, FLOOR + 46.0), (-40.0, FLOOR + 46.0)], W.SNOW)
    K.poly(c, [(-40.0, FLOOR + 40.0), (1120.0, FLOOR + 40.0), (1120.0, 1980.0), (-40.0, 1980.0)], K.INK)
    # the room: boards on the back wall
    K.poly(c, [(IN_L, EAVE), (650.0, APEX + 46.0), (IN_R, EAVE), (IN_R, FLOOR), (IN_L, FLOOR)], WALL_IN)
    seam = lerp(WALL_IN, K.INK, 0.5)
    for i in range(1, 8):
        x = IN_L + i * (IN_R - IN_L) / 8.0
        K.band(c, [(x, EAVE - (x - IN_L if x < 650 else IN_R - x) * 0.74 + 40.0), (x, FLOOR)], seam, 3.0, seed=i)
    # the window: the night outside, the far woods, frost in the corners
    x0, x1, y0, y1 = WINDOW
    K.poly(c, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lerp(K.NIGHT, K.STEEL, 0.25))
    for i in range(6):
        bx = x0 + 10.0 + i * 34.0
        W.spruce_side(c, (bx, y1), 70.0 + 30.0 * K._sn(i, 3), 26.0, lerp(K.STEEL, K.INK, 0.4), seed=i)
    for (cx, cy) in ((x0, y1), (x1, y1)):
        K.ellipse(c, (cx, cy), 46.0, 20.0, lerp(K.PAPER, K.STEEL, 0.4), alpha=0.35)
    K.band(c, [((x0 + x1) / 2.0, y0), ((x0 + x1) / 2.0, y1)], K.INK, 9.0, seed=1)
    K.band(c, [(x0, (y0 + y1) / 2.0), (x1, (y0 + y1) / 2.0)], K.INK, 9.0, seed=2)
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        K.band(c, [a, b], K.INK, 14.0, seed=3)
    # the bench along the left wall
    K.poly(c, [(IN_L + 6.0, 1330.0), (IN_L + 230.0, 1330.0), (IN_L + 230.0, 1352.0), (IN_L + 6.0, 1352.0)], K.INK)
    for x in (IN_L + 30.0, IN_L + 200.0):
        K.band(c, [(x, 1350.0), (x, FLOOR)], K.INK, 12.0, seed=int(x))
    # the stove, its pipe through the roof, the firebox door open on the fire
    sx0, sx1 = STOVE
    K.poly(c, [(sx0, STOVE_TOP), (sx1, STOVE_TOP), (sx1, FLOOR - 50.0), (sx0, FLOOR - 50.0)], K.INK)
    for x in (sx0 + 14.0, sx1 - 14.0):
        K.band(c, [(x, FLOOR - 52.0), (x + (6.0 if x > 900 else -6.0), FLOOR)], K.INK, 12.0, seed=int(x))
    K.poly(c, [(sx0 - 10.0, STOVE_TOP - 16.0), (sx1 + 10.0, STOVE_TOP - 16.0), (sx1 + 10.0, STOVE_TOP + 2.0),
               (sx0 - 10.0, STOVE_TOP + 2.0)], K.INK)
    K.band(c, [(930.0, STOVE_TOP - 10.0), (930.0, APEX - 10.0)], K.INK, 26.0, seed=4)
    fl = _flicker(ft, 1.0 + 1.5 * fire)
    fx, fy = FIREBOX
    K.poly(c, [(fx - 46.0, fy - 38.0), (fx + 46.0, fy - 38.0), (fx + 46.0, fy + 38.0), (fx - 46.0, fy + 38.0)],
           lerp(K.AMBER, K.PAPER, 0.25 * (fl - 0.9)))
    for i in range(3):
        h = 30.0 + 14.0 * math.sin(K.twos(ft) * (11.0 + 3.0 * i) + i)
        K.poly(c, [(fx - 34.0 + 26.0 * i, fy + 36.0), (fx - 18.0 + 26.0 * i, fy + 36.0 - h * fire), (fx - 4.0 + 26.0 * i, fy + 36.0)],
               lerp(K.AMBER, K.RED, 0.35))
    # the firelight on the room (it stays inside the walls)
    c.save()
    _room(c)
    c.clip()
    K.glow(c, (fx, fy), 600.0, 0.42 * fire * fl, ft, color=K.AMBER)
    if door > 0.0:     # moonlight falls in through the open door across the floor
        K.poly(c, [(IN_L, DOOR_Y + 40.0), (IN_L, FLOOR), (IN_L + 420.0 * door, FLOOR), (IN_L + 120.0 * door, DOOR_Y + 200.0)],
               K.PAPER, 0.16 * door)
    c.restore()
    if inside is not None:
        inside(c)
    # the cut: walls, the roof and its snow, the floor
    wl = [(IN_L - WALL_W, EAVE - 30.0), (IN_L, EAVE - 30.0), (IN_L, FLOOR + 40.0), (IN_L - WALL_W, FLOOR + 40.0)]
    if door > 0.0:
        K.poly(c, [(IN_L - WALL_W, EAVE - 30.0), (IN_L, EAVE - 30.0), (IN_L, DOOR_Y), (IN_L - WALL_W, DOOR_Y)], K.INK)
        # the door, flung out into the night on its hinge
        hx = IN_L - WALL_W
        w = 120.0 * math.sin(0.5 * math.pi * clamp(door))
        K.poly(c, [(hx, DOOR_Y), (hx - w, DOOR_Y - 22.0 * door), (hx - w, FLOOR + 18.0 * door), (hx, FLOOR)], K.INK)
        K.band(c, [(hx - w, DOOR_Y - 22.0 * door), (hx - w, FLOOR + 18.0 * door)], K.STEEL, 3.0, seed=5)
    else:
        K.poly(c, wl, K.INK)
        K.band(c, [(IN_L - WALL_W + 6.0, DOOR_Y), (IN_L - 6.0, DOOR_Y)], K.STEEL, 2.5, seed=6, alpha=0.7)
    K.poly(c, [(IN_R, EAVE - 30.0), (IN_R + WALL_W, EAVE - 30.0), (IN_R + WALL_W, FLOOR + 40.0), (IN_R, FLOOR + 40.0)], K.INK)
    K.poly(c, [(IN_L - WALL_W, FLOOR), (IN_R + WALL_W, FLOOR), (IN_R + WALL_W, FLOOR + 40.0), (IN_L - WALL_W, FLOOR + 40.0)],
           K.INK)
    roof = [(IN_L - WALL_W - 60.0, EAVE - 10.0), (650.0, APEX - 20.0), (IN_R + WALL_W + 60.0, EAVE - 10.0),
            (IN_R + WALL_W + 60.0, EAVE + 24.0), (650.0, APEX + 46.0), (IN_L - WALL_W - 60.0, EAVE + 24.0)]
    K.poly(c, roof, K.INK)
    K.poly(c, [(IN_L - WALL_W - 70.0, EAVE - 8.0), (650.0, APEX - 22.0), (IN_R + WALL_W + 70.0, EAVE - 8.0),
               (IN_R + WALL_W + 70.0, EAVE - 34.0), (650.0, APEX - 62.0), (IN_L - WALL_W - 70.0, EAVE - 34.0)], W.SNOW)
    # smoke from the pipe, leaning in the wind
    for k in range(4):
        a = ((ft * 0.6 + k * 0.25) % 1.0)
        K.disc(c, (930.0 + 120.0 * a, APEX - 40.0 - 160.0 * a), 16.0 + 40.0 * a, K.STEEL, seed=k, alpha=0.5 * (1.0 - a))


def _guard_in(c, t, st, pose, x, facing=1):
    """The guard in the hut, his root at frame x on the floor."""
    s = C.scale("guard", HUT_PPM)
    if x < IN_L:        # out in the night: the moon's edge
        return C.draw(c, "guard", st, pose, (x, FLOOR), s, facing, rim=K.PAPER, rim_w=3.0, light=(0.6, -0.8))
    return C.draw(c, "guard", st, pose, (x, FLOOR), s, facing, rim=K.AMBER, rim_w=3.0,
                  light=(1.0 if x < FIREBOX[0] else -1.0, -0.25))


def _shot_hut(c, t):
    ft = FILM_T0 + t
    stand = C.standing("guard")
    if t < T_TURN:
        # at the stove, hands to the fire; then the watch from his coat and back again
        w = clamp((t - T_WATCH) / 0.3) * (1.0 - clamp((t - T_CU_W[1]) / 0.2))
        arms = {"near": ("ang", lerp(72.0, 40.0, w), lerp(18.0, 80.0, w)), "far": ("ang", lerp(66.0, 30.0, w), lerp(16.0, 40.0, w))}
        hold = {"near": C.hold_watch()} if 0.3 < w and t < T_CU_W[1] else {}
        pose = C.still_pose("guard", lean=lerp(7.0, 3.0, w), head=lerp(4.0, 18.0, w), arms=arms, hold=hold, t=ft)
        _hut(c, t, inside=lambda c_: _guard_in(c_, t, stand, pose, 735.0, 1))
        # the lantern on the floor by the bench
        p = K.lantern(c, (LAMP_FLOOR[0], LAMP_FLOOR[1] - 1.15 * 92.0 * 0.95), s=1.1, lit=1.0, t=ft)
        K.glow(c, p, 120.0, 0.5, ft)
        return
    # he turns, stoops for the lantern, crosses to the door and goes out into the wind
    door = ease("outback", clamp((t - T_DOOR) / 0.22))
    fire = 1.0 + 0.8 * clamp((t - T_DOOR) / 0.1) * math.exp(-max(0.0, t - T_DOOR) * 2.0)
    wind = clamp((t - T_DOOR) / 0.15)
    stoop = math.sin(math.pi * clamp((t - T_STOOP[0]) / (T_STOOP[1] - T_STOOP[0])))
    has = t >= (T_STOOP[0] + T_STOOP[1]) / 2.0
    x0, x1 = 735.0, IN_L - 120.0
    wk = C.walker("guard", [(T_TO_DOOR[0], 0.0), (T_TO_DOOR[0] + 0.1, 1.8), (T_TO_DOOR[1], 1.8), (T_DOOR, 0.4),
                            (T_OUT[0], 1.6), (T_OUT[1], 1.8)], t0=T_TURN, t1=8.0)
    st = wk.state(t)
    x = x0 - (wk.x(t) - wk.x(T_TURN)) * C.M_PER_UNIT["guard"] * HUT_PPM
    swing = 18.0 * math.sin(ft * 6.0) * clamp((t - T_TO_DOOR[0]) / 0.2) + 25.0 * wind * math.exp(-max(0.0, t - T_DOOR) * 3.0)
    hold = {"near": C.hold_lantern(ft, lit=1.0, swing=swing)} if has else {}
    if t < T_TO_DOOR[0]:
        arms = {"near": ("ang", lerp(8.0, 30.0, stoop), 8.0), "far": ("ang", -4.0, 10.0)}
        pose = C.still_pose("guard", lean=34.0 * stoop, crouch=70.0 * stoop, arms=arms, hold=hold, t=ft)
    else:
        pose = C.walk_pose("guard", st, arms={"near": ("ang", 10.0, 8.0)}, hold=hold, t=ft)

    def inside(c_):
        out = _guard_in(c_, t, st, pose, x, -1)
        if "flame" in out:
            K.glow(c_, out["flame"], 140.0, 0.55, ft)
        if wind > 0.0:   # the snow the wind throws in
            for i in range(26):
                a = ((ft - FILM_T0 - T_DOOR) * (1.4 + 0.5 * K._sn(i, 2)) + i / 26.0) % 1.0
                px = IN_L + a * (700.0 + 200.0 * K._sn(i, 3))
                py = lerp(DOOR_Y + 40.0, FLOOR - 10.0, (i * 0.37) % 1.0) + 80.0 * math.sin(a * 6.0 + i) * a
                K.disc(c_, (px, py), 4.0 + 3.0 * K._sn(i, 4), K.PAPER, seed=i, alpha=0.8 * wind * (1.0 - a))

    _hut(c, t, door=door, fire=fire, inside=inside)
    if not has:
        p = K.lantern(c, (LAMP_FLOOR[0], LAMP_FLOOR[1] - 1.15 * 92.0 * 0.95), s=1.1, lit=1.0, t=ft)
        K.glow(c, p, 120.0, 0.5, ft)
    if x < IN_L - WALL_W:       # out past the wall and the open door, into the night
        out = _guard_in(c, t, st, pose, x, -1)
        if "flame" in out:
            K.glow(c, out["flame"], 140.0, 0.55, ft)


# ---------------------------------------------------------------------------- the watch
def _cu_watch(c, t):
    ft = FILM_T0 + t
    K.fill(c, lerp(K.INK, K.NIGHT, 0.5))
    K.glow(c, (1000.0, 1500.0), 1100.0, 0.35 * _flicker(ft), ft, color=K.AMBER)
    lid = ease("out3", clamp((t - T_OPEN_W) / 0.12)) * (1.0 - ease("in", clamp((t - (T_SHUT_W - 0.08)) / 0.08)))
    # the watch in his palm, the glove from the lower right
    F.glove(c, (1360.0, 1760.0), (520.0, 1200.0), 2.3, curl=0.3, rim=K.AMBER, light=(0.6, -0.8), rim_w=5.0)
    sec = (17 + int(math.floor(ft - (FILM_T0 + T_CU_W[0])))) % 60
    out = F.watch(c, (720.0, 1000.0), 215.0, t=ft, lid=lid, hands=(11, 58), seconds=sec, rim=K.AMBER, light=(0.6, -0.8))
    # his other thumb strokes the photograph
    k = clamp((t - T_THUMB[0]) / 0.3) * (1.0 - clamp((t - T_THUMB[1]) / 0.25))
    if k > 0.0 and "photo" in out:
        px, py = out["photo"]
        stroke = 30.0 * math.sin((t - T_THUMB[0]) * 4.0)
        tip = (px + 30.0 + stroke * 0.3, py + 40.0 + stroke)
        base = (lerp(-260.0, px - 330.0, ease("out3", k)), lerp(1500.0, py + 520.0, ease("out3", k)))
        F.glove(c, base, tip, 1.6, curl=0.85, rim=K.AMBER, light=(0.6, -0.8), rim_w=4.0, thumb=1.0)


# ============================================================================ the fence view
CAM_D = W.FenceCam(1.3, (540.0, 1240.0))
G_D = 1.0                    # he walks 1 m beyond the wire


def _guard_x(t):
    wk = C.walker("guard", [(T_FENCE - 1.0, 1.6), (T_STOP - 0.45, 1.6), (T_STOP, 0.0)], t0=T_FENCE - 1.0, t1=T_CU_S + 0.5)
    return wk, W.CROSS[0] + 1.2 + (wk.x(T_STOP + 0.3) - wk.x(t)) * C.M_PER_UNIT["guard"]


def _shot_fence(c, t):
    ft = FILM_T0 + t
    cam = CAM_D
    wk, x = _guard_x(t)
    st = wk.state(t)
    raise_u = ease("inout", clamp((t - T_RAISE[0]) / (T_RAISE[1] - T_RAISE[0])))
    swing = 22.0 * math.sin(ft * 5.2) * (1.0 - raise_u)
    hold = {"near": C.hold_lantern(ft, lit=1.0, swing=swing)}
    if t < T_STOP:
        pose = C.walk_pose("guard", st, arms={"near": ("ang", 12.0, 10.0)}, hold=hold, t=ft)
    else:
        pose = C.still_pose("guard", lean=6.0 * raise_u, head=14.0 * raise_u,
                            arms={"near": ("ang", lerp(12.0, 78.0, raise_u), lerp(10.0, -6.0, raise_u))}, hold=hold, t=ft)
    sp = L.search_fv(ft)

    def under(c_):
        L.beam_fv(c_, cam, sp)
        p, ppm = L.fv_at(cam, x, G_D)
        # his lamp's pool on the snow round his feet
        K.glow(c_, (p[0] - 30.0 * ppm / 130.0, p[1]), 1.6 * ppm, 0.55, ft, ry=0.32 * ppm)
        L.shadow_fv(c_, cam, x, G_D, 1.86, 0.2)
        out = C.draw(c_, "guard", st, pose, p, C.scale("guard", ppm), -1, rim=K.PAPER, light=(0.5, -0.85))
        if "flame" in out:
            K.glow(c_, out["flame"], 0.9 * ppm, 0.6, ft)

    W.draw_fence(c, ft, cam, moonlit=1.0, search=sp, posts_shadow=1.0, under=under,
                 scrap=(SNAG_X, W.wire_y(4, SNAG_X) + 2.0))
    L.post_shadows_on_drift(c, cam, 1.0, lerp(lerp(W.SNOW, K.PAPER, 0.18), K.SHADOW, 0.85))


def _cu_scrap(c, t):
    """The glove lifts the scrap off the barb in the lantern light."""
    ft = FILM_T0 + t
    K.fill(c, W.SNOW)
    K.glow(c, (820.0, 300.0), 1200.0, 0.5 * _flicker(ft), ft, color=K.AMBER)
    lift = ease("inout", clamp((t - T_LIFT[0]) / (T_LIFT[1] - T_LIFT[0])))
    q = t - T_LIFT[0]
    wob = (16.0 * math.exp(-4.0 * q) * math.sin(2.0 * math.pi * 6.0 * q)) if q > 0.0 else 0.0
    ys = lambda x: 900.0 + 46.0 * math.sin(math.pi * (x + 260.0) / 1600.0) + wob * math.exp(-((x - 540.0) / 420.0) ** 2)
    K.band(c, [(x, ys(x) + 330.0) for x in range(-40, 1141, 30)], lerp(W.SNOW, K.SHADOW, 0.6), 10.0, seed=6)
    K.band(c, [(x, ys(x)) for x in range(-40, 1141, 30)], K.INK, 13.0, seed=5)
    for bx in (120.0, 540.0, 960.0):
        by, s = ys(bx), 30.0
        K.band(c, [(bx - s, by - s), (bx + s, by + s)], K.INK, 9.5, seed=1)
        K.band(c, [(bx - s, by + s), (bx + s, by - s)], K.INK, 9.5, seed=2)
    barb = (548.0, ys(548.0) + 18.0)
    held = (barb[0] + 260.0 * lift, barb[1] - 520.0 * lift)
    F.scrap(c, held, 1.7, t=ft, wind=1.2 * (1.0 - 0.6 * lift), rim=K.AMBER)
    # the glove: in from the right, pinching the scrap's top, lifting it away
    reach = ease("out3", clamp((t - T_CU_S) / 0.25))
    pinch = clamp((t - T_PINCH[0]) / (T_PINCH[1] - T_PINCH[0]))
    tip = (lerp(1300.0, held[0] + 30.0, reach), lerp(260.0, held[1] - 10.0, reach))
    F.glove(c, (tip[0] + 520.0, tip[1] - 300.0), tip, 1.7, curl=0.15 + 0.5 * pinch, rim=K.AMBER, light=(-0.6, -0.8),
            rim_w=5.0, flip=True)
    # the lantern above, its light on everything
    p = K.lantern(c, (880.0, -40.0), s=3.2, lit=1.0, swing=4.0 * math.sin(ft * 3.0), t=ft)
    K.glow(c, p, 260.0, 0.6, ft)


# ============================================================================ the page
def _guard_top(c, cam, p, heading, t, phase=0.0, speed=0.0, crouch=0.0):
    C.top(c, "guard", cam.px(p), heading, cam.ppm, t, phase=phase, speed=speed, lantern=0.0, crouch=crouch,
          shadow=True)


def _page_close(c, t):
    """The lantern's pool slides over their prints."""
    ft = FILM_T0 + t
    cam = W.Plan(40.6, -128.3, 125.0)
    shade_c = lerp(W.SNOW, W.SHADOW, 0.55)
    W.draw_page(c, cam, ft, moonlit=1.0, prints=(), fence_on=False, scrap=False, shadows=0.0)
    approach_prints(c, cam)
    W.draw_prints(c, cam, tuple(W.FENCE_PRINTS) + GF_FENCE, page=W.SNOW, color=W.SHADOW)
    trough_top(c, cam, TROUGH_G, 0.32)
    trough_top(c, cam, TROUGH_M, 0.42)
    W.draw_fence_top(c, cam, ft, shade_c, scrap=False)
    u = ease("inout", clamp((t - T_PAGE) / 0.8))
    pool = (lerp(G_STAND[0] - 0.1, 40.15, u), lerp(G_STAND[1] + 0.1, -127.0, u))
    W.lamp_pool(c, cam, pool, lerp(0.9, 1.7, u), strength=lerp(0.55, 0.85, u), t=ft)
    _guard_top(c, cam, G_STAND, -150.0, ft, crouch=0.25 * u)


def _print_cu(c, heel, ppm, kind, side, ang=0.0):
    """A boot print in the snow, close: the sole and the heel pressed in, the tread, the lit rim."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    X = lambda q: (heel[0] + (q[0] * ca - q[1] * sa) * ppm, heel[1] - (q[0] * sa + q[1] * ca) * ppm)
    pts = [X(q) for q in K.print_pts(kind, side)]
    L = K._PRINT[kind][0]
    K.poly(c, [(x - 5.0, y - 6.0) for x, y in pts], K.PAPER, 0.8)
    K.poly(c, pts, lerp(W.SHADOW, K.INK, 0.2))
    for u in (0.31, 0.36):             # the heel's edge
        K.band(c, [X((-0.06, u * L)), X((0.06, u * L))], lerp(W.SHADOW, W.SNOW, 0.5), 0.006 * ppm, seed=int(u * 100))
    for i in range(5):                 # the tread across the sole
        u = 0.55 + 0.085 * i
        K.band(c, [X((-0.035, u * L)), X((0.035, u * L))], lerp(W.SHADOW, W.SNOW, 0.35), 0.0045 * ppm, seed=i)
    return X((0.0, L))


def _cu_print(c, t):
    """From above: his glove touches a small print."""
    ft = FILM_T0 + t
    K.fill(c, W.SNOW)
    K.glow(c, (620.0, 1080.0), 900.0, 0.42 * _flicker(ft), ft, color=K.AMBER)
    ppm = 1500.0
    _print_cu(c, (330.0, 1720.0), ppm, "mother", -1, ang=4.0)
    toe = _print_cu(c, (720.0, 1330.0), ppm, "girl", 1, ang=-6.0)
    k = ease("out3", clamp((t - T_CU_P) / (T_TOUCH - T_CU_P)))
    tip = (lerp(1250.0, toe[0] + 20.0, k), lerp(-200.0, toe[1] + 30.0, k))
    F.glove(c, (tip[0] + 640.0, tip[1] - 520.0), tip, 2.0, curl=0.1, spread=0.15, rim=K.AMBER, light=(-0.6, 0.8),
            rim_w=5.0)


def _cu_whistle(c, t):
    ft = FILM_T0 + t
    K.fill(c, K.NIGHT)
    K.stars(c, ft, y1=1100.0)
    K.moon(c, (860.0, 360.0), r=86.0)
    for i in range(24):
        x = -40.0 + 50.0 * i + 12.0 * K._sn(i, 5)
        W.spruce_side(c, (x, 1500.0), 220.0 + 80.0 * K._sn(i, 6), 80.0, lerp(K.STEEL, K.INK, 0.35), seed=i)
    K.poly(c, [(-40.0, 1496.0), (1120.0, 1496.0), (1120.0, 1980.0), (-40.0, 1980.0)], lerp(W.SNOW, K.STEEL, 0.25))
    m = F.guard(c, (360.0, 1330.0), 1.2, look=0.9, t=ft, rim=K.PAPER, light=(0.55, -0.85), rim_w=5.0,
                eye_light=(K.AMBER, 0.25))
    K.glow(c, (560.0, 1900.0), 700.0, 0.3, ft, color=K.AMBER)
    mp = m["mouth"]
    tip = (mp[0] + 70.0, mp[1] + 8.0)
    K.band(c, [(mp[0] - 6.0, mp[1]), tip], K.INK, 20.0, seed=2)
    for t0 in T_WHISTLE:
        K.whistle(c, (tip[0] + 14.0, tip[1]), t, t0, r0=40.0, r1=300.0, width=12.0)


def _page_wide(c, t):
    """Lanterns wake along the fence; the searchlight swings north over the woods."""
    ft = FILM_T0 + t
    cam = W.Plan(40.0, -121.0, 15.5)
    shade_c = lerp(W.SNOW, W.SHADOW, 0.55)
    W.draw_page(c, cam, ft, moonlit=1.0, prints=(), scrap=False, shadows=0.0, woods_mass_a=1.0)
    W.draw_tower_top(c, cam, shade_c)
    W.draw_fence_top(c, cam, ft, shade_c, scrap=False)
    W.draw_prints(c, cam, W.FENCE_PRINTS, page=W.SNOW, color=PRINT_C)
    # the searchlight leaves its sweep and swings up over the woods
    u = ease("inout", clamp((t - T_SWING[0]) / (T_SWING[1] - T_SWING[0])))
    a = (L.search_x(FILM_T0 + T_SWING[0]), L.search_n(FILM_T0 + T_SWING[0]))
    sp = (lerp(a[0], 41.0, u), lerp(a[1], -108.0, u))
    d = (sp[0] - W.TOWER[0], sp[1] - W.TOWER[1])
    dl = math.hypot(*d) or 1.0
    side = (-d[1] / dl * 3.6, d[0] / dl * 3.6)
    K.beam(c, cam.px(W.TOWER), cam.px((sp[0] + side[0], sp[1] + side[1])), cam.px((sp[0] - side[0], sp[1] - side[1])),
           K.PAPER, alpha=0.16)
    W.search_patch(c, cam, sp, 4.2, alpha=0.8, heading=math.degrees(math.atan2(d[0], d[1])))
    # his lantern at the crossing, and the others waking far along the fence
    W.lamp_pool(c, cam, G_STAND, 2.6, strength=0.8, t=ft)
    K.dot(c, cam.px(G_STAND), 4.0, K.AMBER)
    for i, (p, tw) in enumerate(zip(FAR_LAMPS, T_WAKE)):
        k = ease("outback", clamp((t - tw) / 0.25))
        if k > 0.0:
            W.lamp_pool(c, cam, p, 2.6 * k, strength=0.8, t=ft, seed=i + 1)
            K.dot(c, cam.px(p), 4.0 * k, K.AMBER)


def _page_woods(c, t):
    """He follows their prints into the woods; the trees close over his lantern."""
    ft = FILM_T0 + t
    cam = W.Plan(38.9, -121.2, 72.0)
    shade_c = lerp(W.SNOW, W.SHADOW, 0.55)
    W.draw_page(c, cam, ft, moonlit=1.0, prints=(), scrap=False, woods_on=False, shadows=0.0)
    W.draw_fence_top(c, cam, ft, shade_c, scrap=False)
    approach_prints(c, cam, PRINT_C)
    trough_top(c, cam, TROUGH_G, 0.32)
    trough_top(c, cam, TROUGH_M, 0.42)
    s = lerp(6.5, 12.8, (t - T_WOODS) / 2.0)
    (gx, gn), u = W.poly_at(G_ROUTE, s)
    W.draw_prints(c, cam, tuple(W.FENCE_PRINTS) + GF_FENCE + tuple(q for q in GF_PATH if q[1] < gn - 0.25), page=W.SNOW,
                  color=PRINT_C)
    deep = clamp((gn - (-117.4)) / 1.6)          # how far into the trees he is
    W.lamp_pool(c, cam, (gx - 0.25, gn + 0.3), 1.4, strength=0.8 * (1.0 - deep), t=ft)
    C.top(c, "guard", cam.px((gx, gn)), math.degrees(math.atan2(-u[1], u[0])), cam.ppm, ft, phase=(t - T_WOODS) / 0.62,
          speed=1.0, lantern=0.0, shadow=True)
    woods_edge(c, cam)
    # under the trees his lantern is a glow in the black, sinking away
    if deep > 0.0:
        K.glow(c, cam.px((gx - 0.25, gn + 0.3)), lerp(1.4, 0.7, deep) * cam.ppm, 0.7 * (1.0 - 0.55 * deep), ft)


# ---------------------------------------------------------------------------- render
def render(f, t, T):
    K.scene_setup(f, K.NIGHT)
    with f.screen() as c:
        if t < T_CU_W[0] or T_CU_W[1] <= t < T_FENCE:
            _shot_hut(c, t)
        elif t < T_CU_W[1]:
            _cu_watch(c, t)
        elif t < T_CU_S:
            _shot_fence(c, t)
        elif t < T_PAGE:
            _cu_scrap(c, t)
        elif t < T_CU_P:
            _page_close(c, t)
        elif t < T_WHISTLE[0]:
            _cu_print(c, t)
        elif t < T_WIDE:
            _cu_whistle(c, t)
        elif t < T_WOODS:
            _page_wide(c, t)
        else:
            _page_woods(c, t)


def motion_blur(t, T):
    return 1


def cues(T):
    return [
        Cue(0.0, "stove_crackle", gain_db=-18, dur=T_FENCE, dc="a wood stove: crackle and a low roar of the draught"),
        Cue(0.0, "wind_outside", gain_db=-24, dur=T_DOOR, dc="the wind outside the hut, muffled by the walls"),
        Cue(0.6, "hands_rub", gain_db=-22, dur=0.8, dc="gloved hands rubbed together over the stove"),
        Cue(T_WATCH, "cloth_rustle", gain_db=-24, dc="he draws the watch from his greatcoat"),
        Cue(T_OPEN_W, "watch_click", gain_db=-10, dc="the watch lid springs open: a small, crisp click"),
        Cue(T_OPEN_W, "watch_tick", gain_db=-20, dur=T_SHUT_W - T_OPEN_W, dc="the watch ticking, very close"),
        Cue(2.7, "string_low", gain_db=-20, dur=2.0, dc="a single low string note under the photograph"),
        Cue(T_SHUT_W, "watch_click", gain_db=-12, dc="the lid snapped shut"),
        Cue(T_STOOP[0] + 0.2, "lantern_creak", gain_db=-20, dc="the lantern's bail creaks as he lifts it"),
        Cue(T_DOOR, "door_open", gain_db=-10, dc="the latch lifts and the wind slams the door open against the wall"),
        Cue(T_DOOR, "wind_burst", gain_db=-12, dur=T_FENCE - T_DOOR, dc="the wind howls in, snow hissing across the floor"),
        Cue(T_FENCE, "boots_snow", gain_db=-14, dur=T_STOP - T_FENCE, pan=0.4,
            dc="heavy hobnailed boots crunching in snow, every 0.55 s, coming from the right"),
        Cue(T_FENCE, "lantern_squeak", gain_db=-24, dur=T_STOP - T_FENCE, dc="the lantern swinging on its bail"),
        Cue(T_PINCH[1], "cloth_tug", gain_db=-16, dc="cloth pulled free of the barb"),
        Cue(T_PAGE, "lantern_hiss", gain_db=-24, dur=2.0, dc="the lantern's flame hissing, close"),
        Cue(T_TOUCH, "snow_kneel", gain_db=-18, dc="a knee into the snow; a glove brushing snow"),
        Cue(T_WHISTLE[0], "whistle", gain_db=-4, dc="a police whistle: one long shrill blast"),
        Cue(T_WHISTLE[1], "whistle", gain_db=-4, dc="a second shrill blast"),
        Cue(T_WAKE[0], "far_whistle", gain_db=-22, pan=-0.6, dc="a far whistle answering"),
        Cue(T_WAKE[1], "far_whistle", gain_db=-24, pan=0.7, dc="another far whistle answering"),
        Cue(T_WAKE[2], "far_whistle", gain_db=-23, pan=-0.3, dc="a third, nearer"),
        Cue(T_SWING[0], "searchlight_swing", gain_db=-18, dur=1.5, dc="the searchlight's motor revs as it swings north"),
        Cue(T_WOODS, "boots_snow", gain_db=-16, dur=2.0, dc="his boots jogging away into the woods, receding"),
        Cue(T_WOODS, "wind_low", gain_db=-26, dur=2.0, dc="the wind in the pines"),
    ]
