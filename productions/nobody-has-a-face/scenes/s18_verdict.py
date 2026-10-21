"""S18 - Your Verdict (12.5 s) - the question to the audience.

"In a city without faces, the hardest one to see is your own.
 So you tell me. Was I the killer... or the perfect suspect?"

Shot plan (scene seconds)
  0.00-5.40  IN: darkness; the small high barred cell window (S17's red umbrella vanished at the same
             spot): the moon - a white ring - and rain beyond the bars; a cell door clangs. Moonlight
             falls through the window in barred stripes and reveals the cell: strong vertical bars in
             the foreground, a chained bench, him sitting. Slow push between the bars (parallax, rack
             focus to him). On "hardest" he slowly lifts his LEFT hand and studies it.
  5.40-8.62  "So you tell me. Was I the killer...": vertical split - him behind the bars (top) / far
             below, the red umbrella crossing a wet street (bottom); the light alternates: amber on
             him ("So you tell me", "Was I"), crimson on the umbrella ("me...", "the killer").
  8.62-12.50 "...or the perfect suspect?": black. One match strikes at the centre and lights a hollow
             head that could be anyone; slow final push; the flame dies ~11.4; pure black to the end
             (clean negative space for an optional post overlay). Last sound: a strike in the dark.
"""
import math

from engine import *
from engine.timing import SceneTiming
from scenes._lib_s16_s18 import Gait, Persp, ek, log_zoom, tglob

T_LAST = 12.4583                         # last frame (299 / 24)

# ================================================================ the cell (world coords)
WIN_C = (560.0, 430.0)                   # the small high window: opening 170 x 130
WIN_X0, WIN_X1, WIN_Y0, WIN_Y1 = 475.0, 645.0, 365.0, 495.0
WIN_BARS = [518.0, 560.0, 602.0]
MOON_C, MOON_R = (590.0, 400.0), 30.0
FLOOR = 1520.0
SEAT_Y = 1385.0
BENCH = (300.0, 780.0)
HE_X = 540.0
LIGHT_DX = -0.06                         # moonlight slant (x per y) - the moon is high
BARS = [65.0, 255.0, 445.0, 635.0, 825.0, 1015.0]   # foreground cell bars (near layer)
BAR_DEPTH = 1.35

CAM0 = Camera(560.0, 970.0, 1.0)         # window high in frame (screen ~(560, 420))
CAM1 = Camera(545.0, 1215.0, 1.75)       # pushed in between the bars
TOP_CAM = Camera(548.0, 1449.0, 2.0)     # the split's top panel: him, medium

_T = SceneTiming("s18")
T_SPLIT0 = _T.at("so") - 0.235           # 5.30: the split opens into "So you tell me"
T_SPLIT1 = T_SPLIT0 + 0.36
T_BLACK = _T.at("or") - 0.06             # 8.62: black on "or"


def _seated(t, beats):
    """Front view, sitting on the bench; LEFT hand (screen-right) rises to his face on 'hardest'."""
    hardest, own, so, was = beats["hardest"], beats["own"], beats["so"], beats["was"]
    p = Pose(x=HE_X, y=SEAT_Y, s=1.0, facing=0, ll=33, lk=33, rl=33, rk=33, la=14, ra=14)
    p = rig.breathe(p, t, amt=0.7, seed=81)
    J = rig.solve(p)
    # both hands rest on the knees
    p = rig.reach(p, "r", (J["rk"][0] + 4, J["rk"][1] - 10))
    rest = (J["lk"][0] - 4, J["lk"][1] - 10)
    face = (J["head"][0] + 74, J["head"][1] + 2)              # held up beside his head, looked at
    lift = ek("inout", hardest - 0.05, own + 0.15, t)
    study = (6 * math.sin(1.7 * (t - own)) * ek("inout", own, own + 0.6, t),
             5 * math.sin(1.2 * (t - own) + 1.0) * ek("inout", own, own + 0.6, t))
    lower = ek("inout", was - 0.25, was + 0.45, t)
    tgt = lerp(rest, face, lift)
    tgt = (tgt[0] + study[0], tgt[1] + study[1])
    tgt = lerp(tgt, (J["head"][0] + 40, J["head"][1] + 120), lower)
    p = rig.reach(p, "l", tgt)
    # head: a weary tilt, then toward the raised hand, then up on "Was I"
    head = -5 + 17 * lift - 14 * lower
    return p.copy(head=p.head + head)


def _bench(f):
    x0, x1 = BENCH
    draw.line(f, (x0, SEAT_Y + 5), (x1, SEAT_Y + 5), 3.4, WHITE)
    draw.line(f, (x0 + 6, SEAT_Y + 20), (x1 - 6, SEAT_Y + 20), 2.0, WHITE, 0.7)
    for x in (x0 + 24, x1 - 24):                        # chains up to the wall
        draw.line(f, (x, SEAT_Y + 5), (x, SEAT_Y - 330), 2.0, WHITE, 0.55, dash=(8, 7))
        draw.circle(f, (x, SEAT_Y - 334), 5, 2.0, WHITE, 0.6)


def _window(f, t, alpha=1.0):
    """Window frame, its bars, the moon ring and the rain beyond (clipped to the opening)."""
    if alpha <= 0:
        return
    with f.clipped(lambda c: c.rectangle(WIN_X0, WIN_Y0, WIN_X1 - WIN_X0, WIN_Y1 - WIN_Y0)):
        draw.circle(f, MOON_C, MOON_R, 3.2, WHITE, alpha, glow=0.25 * alpha)
        fx.rain(f, t, density=1.0, wind=10, seed=23, alpha=0.8 * alpha)
    draw.rect(f, WIN_X0, WIN_Y0, WIN_X1 - WIN_X0, WIN_Y1 - WIN_Y0, 3.0, WHITE, alpha)
    draw.rect(f, WIN_X0 - 12, WIN_Y0 - 12, WIN_X1 - WIN_X0 + 24, WIN_Y1 - WIN_Y0 + 24, 2.0, WHITE, 0.55 * alpha)
    draw.line(f, (WIN_X0 - 24, WIN_Y1 + 13), (WIN_X1 + 24, WIN_Y1 + 13), 2.6, WHITE, 0.8 * alpha)
    for x in WIN_BARS:
        draw.line(f, (x, WIN_Y0), (x, WIN_Y1), 4.6, WHITE, alpha)


def _moon_stripes(intensity):
    """Moonlight through the window: one light strip per gap between the window bars."""
    edges = [WIN_X0] + [b for x in WIN_BARS for b in (x - 2.5, x + 2.5)] + [WIN_X1]
    out = []
    for i in range(0, len(edges), 2):
        x0, x1 = edges[i], edges[i + 1]
        dy = FLOOR + 40 - WIN_Y1
        spread = 0.16 * dy * 0.5 / 4
        out.append(Light.poly([(x0, WIN_Y1), (x1, WIN_Y1),
                               (x1 + LIGHT_DX * dy + spread, FLOOR + 40), (x0 + LIGHT_DX * dy - spread, FLOOR + 40)],
                              intensity))
    return out


def _amber_stripes(intensity):
    """Corridor lamp light thrown through the cell bars onto him and the wall (top panel)."""
    out = []
    for i in range(len(BARS) - 1):
        x0, x1 = BARS[i] + 14, BARS[i + 1] - 14
        out.append(Light.poly([(x0 - 60, 900), (x1 - 60, 900), (x1 + 40, 1600), (x0 + 40, 1600)], intensity))
    return out


DRIPS = [(1.15, 512.0), (3.35, 604.0)]   # (release time, x) of drops falling from the sill


def _drip_y(t, t0):
    dt = t - t0
    return WIN_Y1 + 14 + 0.5 * 1930.0 * dt * dt


def _drip_land(t0):
    return t0 + math.sqrt(2 * (FLOOR - WIN_Y1 - 14) / 1930.0)


def _cell(f, t, beats, amber=0.0, moon=1.0, he=True):
    """The cell interior inside its light reveal."""
    lights = _moon_stripes(moon)
    ambient = 0.05 * min(1.0, moon + amber)
    if amber > 0:
        lights += _amber_stripes(amber)
        lights.append(Light.radial((HE_X + 10, 1240), 360, 0.6 * amber))
    with f.lit(lights, ambient=ambient, soften=3.0):
        draw.line(f, (-300, FLOOR), (1400, FLOOR), 3.0, WHITE)
        draw.line(f, (-300, SEAT_Y - 330), (1400, SEAT_Y - 330), 1.2, WHITE, 0.3)
        _bench(f)
        fx.dust(f, t, (420, 520, 720, 1500), n=70, seed=12, alpha=0.6, size=2.0)
        if he:
            rig.draw_figure(f, _seated(t, beats))
        for (t0, x) in DRIPS:                                   # water dripping through the bars
            if t0 < t < _drip_land(t0):
                y = _drip_y(t, t0)
                draw.line(f, (x, y - 10), (x, y + 6), 2.2, WHITE, 0.9)
            k = (t - _drip_land(t0)) / 0.35
            if 0 <= k < 1:
                for sx in (-1, 1):
                    draw.line(f, (x + sx * 4, FLOOR - 2), (x + sx * (8 + 14 * k), FLOOR - 6 - 10 * math.sin(math.pi * k)),
                              1.6, WHITE, 0.8 * (1 - k))
    if amber > 0:                                               # warm haze through the bars
        for i in range(len(BARS) - 1):
            x0, x1 = BARS[i] + 14, BARS[i + 1] - 14
            pts = [(x0 - 60, 900), (x1 - 60, 900), (x1 + 40, 1600), (x0 + 40, 1600)]
            draw.gradient_fill(f, pts, [(0.0, AMBER, 0.13 * amber), (1.0, AMBER, 0.0)],
                               (HE_X, 1240), None, radial=True, r0=0, r1=520, glow=0.3 * amber)


def _bars(f, cam, alpha, blur):
    """Foreground cell bars: near parallax layer, out of focus once we focus on him."""
    if alpha <= 0:
        return
    pc = cam.parallax(BAR_DEPTH)

    def draw_bars():
        for x in BARS:
            draw.line(f, (x, -900), (x, 2900), 9.0, WHITE, alpha)
        for y in (250.0, 1690.0):
            draw.line(f, (-300, y), (1400, y), 7.0, WHITE, alpha)
    with f.camera(pc):
        if blur > 0.5:
            with f.blurred(blur):
                draw_bars()
        else:
            draw_bars()


# ================================================================ the street far below (bottom panel)
ST = Persp((540.0, 1010.0), 2110.0, 0.9)
K_CROSS = 0.42                           # depth of the crosswalk he crosses
ROAD_X, WALL_X = 520.0, 760.0
GAIT = Gait(0.0, 0.0, ST.s0 * K_CROSS, 1, limp=0.85, stride=0.9, arm=0.0, t0=5.45, h0=1.0,
            cycle=0.78)                  # the engine's limp rhythm: quick stance on the LEFT leg
_GX0 = GAIT.pose(T_SPLIT0).x
CROSS_X0 = 405.0                         # screen x where he is when the panel opens


def _street_panel(f, t, crimson, dim):
    """Static high view down a wet street; THE red umbrella limps across the crosswalk."""
    s = ST.s0 * K_CROSS
    g = GAIT.pose(t)
    feet = ST.P(0, 0, K_CROSS)
    p = g.copy(x=CROSS_X0 + (g.x - _GX0), y=g.y + feet[1])
    J = rig.solve(p)
    p = rig.reach(p, "r", (J["neck"][0] + 14 * s, J["neck"][1] - 4 * s))
    J = rig.solve(p)
    lamps = [(-640.0, 0.62, 1), (640.0, 0.42, -1), (-640.0, 0.27, 1), (640.0, 0.17, -1), (-640.0, 0.10, 1)]
    lights = []
    for (X, k, fc) in lamps:
        b = ST.P(X, 0, k)
        lp = (b[0] + fc * 120 * k, b[1] - 880 * k + 62 * k)
        lights.append(Light.cone(lp, 90, 60, 900 * k, intensity=dim))
    lights.append(Light.radial(J["head"], 300, intensity=crimson))
    with f.lit(lights, ambient=0.1 * dim, soften=3.0):
        for sx in (-1, 1):
            draw.line(f, ST.P(sx * ROAD_X, 0, 1.0), ST.P(sx * ROAD_X, 0, 0.02), 2.6, WHITE, 0.9)
            draw.line(f, ST.P(sx * WALL_X, 0, 1.0), ST.P(sx * WALL_X, 0, 0.02), 2.0, WHITE, 0.6)
        for i in range(9):                                    # the zebra crossing
            X0 = -440 + i * 104
            quad = [ST.P(X0, 0, K_CROSS + 0.035), ST.P(X0 + 56, 0, K_CROSS + 0.035),
                    ST.P(X0 + 56, 0, K_CROSS - 0.035), ST.P(X0, 0, K_CROSS - 0.035)]
            draw.stroke(f, quad, 2.0, WHITE, 0.7, closed=True)
        for (X, k, fc) in lamps:
            props.streetlamp(f, ST.P(X, 0, k), height=880, s=k, on=dim, facing=fc, t=t, seed=int(k * 90),
                             glow_r=240)
        fx.rain(f, t, density=0.9, wind=6, seed=41, alpha=0.8)
        fx.ripples(f, t, 60, ST.P(0, 0, 0.3)[1], 1020, ST.P(0, 0, 0.6)[1], rate=0.6, seed=8, alpha=0.4)
        rig.draw_figure(f, p)
    # the red umbrella (accent), its crimson pool and reflection on the wet street
    if crimson > 0:
        fx.light_pool(f, (J["hip"][0], feet[1]), 170, 40, CRIMSON, 0.22 * crimson, glow=0.5 * crimson)
    props.umbrella(f, J["rh"], angle=-88, R=118 * s, open_=1.0, color=CRIMSON, t=t, seed=9, wobble=0.6,
                   alpha=0.55 + 0.45 * max(crimson, 0.4 * dim))
    fx.reflection(f, J["head"][0], feet[1] + 4, length=150, width=40, color=CRIMSON,
                  alpha=0.25 + 0.4 * crimson, t=t, seed=3)
    return GAIT


# ================================================================ the last match
FIG = rig.stand(540.0, 1500.0, facing=0, s=1.0)
MATCH_S = 0.95


def _last_pose(t):
    """Front view; the LEFT hand (screen-right) holds the match up beside his face."""
    p = rig.breathe(FIG, t, amt=0.6, seed=97)
    J = rig.solve(p)
    hand = (J["shoulder"][0] + 52 + 2 * fbm1(t * 0.7, 9), J["shoulder"][1] - 4 + 2 * fbm1(t * 0.6, 13))
    return rig.reach(p, "l", hand)


def _last_match(t, strike):
    """(lit, flare, ember) of the final match; out at ~11.4."""
    if t < strike - 0.02:
        return 0.0, 0.0, 0.0
    flare = pulse(t, strike, 0.03, 0.3)
    lit = ek("out", strike - 0.02, strike + 0.08, t)
    gutter = 1.0 - 0.45 * ek("inout", 11.05, 11.3, t) * (0.5 + 0.5 * math.sin(t * 60))
    lit *= gutter * (1.0 - ek("in", 11.3, 11.42, t))
    ember = ek("inout", 11.36, 11.44, t) * (1.0 - ek("inout", 11.45, 11.8, t))
    return lit, flare, ember


def render(f, t, T):
    beats = dict(hardest=T.at("hardest"), own=T.at("own"), so=T.at("so"), tell=T.at("tell"),
                 me=T.at("me"), was=T.at("was"), killer=T.at("killer"), or_=T.at("or"),
                 perfect=T.at("perfect"))
    if t >= T_BLACK:
        _shot_match(f, t, T, beats)
        return
    if t < T_SPLIT0:
        _shot_cell(f, t, T, beats)
        return
    _shot_split(f, t, T, beats)


def _cell_cam(t):
    k = ek("inout", 0.7, 5.3, t)
    return Camera(lerp(CAM0.x, CAM1.x, k), lerp(CAM0.y, CAM1.y, k), log_zoom(CAM0.zoom, CAM1.zoom, k))


def _shot_cell(f, t, T, beats):
    cam = _cell_cam(t)
    f.set_camera(cam)
    win = 0.5 + 0.5 * ek("out", 0.0, 0.3, t)                 # cut in from S17's darkness
    moon = ek("inout", 0.35, 2.2, t)
    _cell(f, t, beats, moon=moon)
    _window(f, t, win)
    _bars(f, cam, 0.8 * ek("inout", 0.9, 2.4, t), 7.0 * ek("inout", 2.2, 4.0, t))


def _amber_crimson(t, beats):
    """Alternating key light: amber on him / crimson on the umbrella (word-synced)."""
    so, me, was, killer = beats["so"], beats["me"], beats["was"], beats["killer"]
    amber = Track([(T_SPLIT0, 0.25), (so - 0.05, 1.0, "inout"), (me + 0.15, 1.0), (me + 0.4, 0.2, "inout"),
                   (was - 0.1, 0.2), (was + 0.08, 1.0, "inout"), (killer - 0.1, 1.0), (killer + 0.12, 0.2, "inout")])(t)
    crimson = Track([(T_SPLIT0, 0.2), (me + 0.15, 0.2), (me + 0.4, 1.0, "inout"), (was - 0.1, 1.0),
                     (was + 0.08, 0.25, "inout"), (killer - 0.1, 0.25), (killer + 0.12, 1.0, "inout")])(t)
    return amber, crimson


def _shot_split(f, t, T, beats):
    w = ek("inout", T_SPLIT0, T_SPLIT1, t)
    div = lerp(1920.0, 960.0, w)                     # the divider rises from the bottom edge
    out = 1.0 - ek("inout", T_BLACK - 0.1, T_BLACK, t)
    amber, crimson = _amber_crimson(t, beats)
    # ---- top panel: him behind the bars
    c1 = _cell_cam(t)
    cam = Camera(lerp(c1.x, TOP_CAM.x, w), lerp(c1.y, TOP_CAM.y, w), log_zoom(c1.zoom, TOP_CAM.zoom, w))
    f.set_camera(cam)
    with f.alpha(out):
        with f.clipped(_screen_rect(cam, 0, 0, 1080, div - 8)):
            _cell(f, t, beats, amber=amber * w, moon=lerp(1.0, 0.22 + 0.25 * amber, w))
            _bars(f, cam, 0.8, 7.0)
    # ---- bottom panel: the street far below
    if div < 1915:
        dim = lerp(1.0, 0.35 + 0.65 * crimson, w)
        bc = Camera(540.0, 960.0 - (div - 960.0), 1.0)
        f.set_camera(bc)
        with f.alpha(out):
            with f.clipped(lambda c: c.rectangle(-10, div + 8, 1100, 2000)):
                _street_panel(f, t, crimson * w, dim)
        with f.screen():
            draw.line(f, (0, div), (1080, div), 1.6, WHITE, 0.45 * out)


def _screen_rect(cam, x, y, w, h):
    """Clip path for a screen rectangle, expressed in the world coords of camera `cam`."""
    pts = [cam.to_world(p) for p in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))]

    def path(c):
        c.move_to(*pts[0])
        for q in pts[1:]:
            c.line_to(*q)
        c.close_path()
    return path


def _shot_match(f, t, T, beats):
    strike = beats["perfect"] - 0.03
    lit, flare, ember = _last_match(t, strike)
    if lit <= 0 and ember <= 0:
        return                                           # pure black
    p = _last_pose(t)
    J = rig.solve(p)
    ang = -95.0 + 3 * math.sin(t * 0.8)
    tip = (J["lh"][0] + math.cos(math.radians(ang)) * 52 * MATCH_S,
           J["lh"][1] + math.sin(math.radians(ang)) * 52 * MATCH_S)
    flame_c = (tip[0], tip[1] - 14)
    k = ek("inout", strike, 11.4, t)
    z = log_zoom(3.3, 3.85, k)
    mid_x = 0.5 * (flame_c[0] + J["head"][0])              # frame the flame and the head together
    cam = Camera(mid_x + 2.0 * fbm1(t * 0.4, 3), flame_c[1] + 2.0 * fbm1(t * 0.35, 5), z)
    f.set_camera(cam)
    fl = flicker(t, 11, rate=9, depth=0.25)
    rad = (118 + 60 * flare) * (0.3 + 0.7 * lit) * fl + 36 * ember
    with f.lit([Light.radial(flame_c, rad, intensity=min(1.0, lit + 0.5 * ember))], ambient=0.0, soften=4.0):
        rig.draw_figure(f, p)
    props.match(f, J["lh"], angle=ang, length=52, s=MATCH_S, lit=lit, flare=0.45 * flare, ember=ember,
                burnt=ek("inout", 11.3, 11.5, t), smoke_amt=ember, t=tglob(T, t), seed=7)


def cues(T):
    hardest, so, killer = T.at("hardest"), T.at("so"), T.at("killer")
    strike = T.at("perfect") - 0.03
    c = [Cue(0.04, "cell_door", gain_db=-8, pan=-0.2),
         Cue(hardest - 0.05, "chair_creak", gain_db=-17, pan=0.0),
         Cue(T_SPLIT0, "whoosh", gain_db=-17, size=0.25)]
    for (t0, x) in DRIPS:
        c.append(Cue(_drip_land(t0), "drip", gain_db=-14, pan=(x - 540) / 600))
    for (tt, side, foot) in GAIT.footfalls(T_SPLIT0 + 0.2, T_BLACK - 0.1):   # far below, wet, uneven
        c.append(Cue(tt, "footstep", gain_db=-24 if side == "l" else -20, pan=0.1, weight=0.3 if side == "l" else 0.7, wet=1))
    c += [Cue(strike - 0.03, "match_strike", gain_db=-2, pan=0.0),
          Cue(strike + 0.03, "match_flare", gain_db=-6, pan=0.0),
          Cue(11.40, "flame_out", gain_db=-8, pan=0.0),
          Cue(12.10, "match_strike", gain_db=-4, pan=0.0)]        # the last sound: a strike, no light
    return c
