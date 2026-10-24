"""s08 LOCKED (96-108). Inside the shut vault, in the dark.
  The match: black, and his ragged breath. A match scratches (sparks), then strikes, and its
    light opens in gold rings on her profile, calm, and on the Cracker beyond her, leaning on
    the door. He rears back ...
  The pounding: ... and we cut on his first blow. He beats on the door and his shadow, twice his
    size, beats with him. The flame shivers at every blow.
  Her eye, close: steady. Her look drops to the floor in a white dotted line, the corner of her
    mouth lifts, and the camera whips down after her look ...
  The hollow floor: ... to where it lands, a ring on the floor at her heel. A tap, then a hollow
    knock. Below the floor line the frame opens into a blueprint section: the slab, the earth,
    the sewer pipe. The knock rings down through it, and exactly under her heel the chalk dot
    from s03 glows. A lens joins it to the dot on the plan.
  The tracing paper: the Cracker turns round. She brings a roll up from her coat, lets it fall
    open before her face, then lifts the sheet to us until it fills the frame, the match glowing
    through it. s09 begins on this sheet (roll_shot at T_END).
"""
import math

import cairo

from engine import bass
from engine import draw as D
from engine import paperdoll as pd
from engine.core import clamp, ease, hash01, lerp
from engine.timing import Cue
from films.double_cross import cast as C
from films.double_cross import faces as F
from films.double_cross import kit as K
from films.double_cross import plan as P
from films.double_cross import shots as S

SHOTS = ((0.0, "match"), (2.85, "pound"), (3.9, "eye"), (5.1, "whip"), (5.35, "floor"), (8.0, "roll"))
T_END = 12.0
T_SPARK = 0.85                # a scratch: sparks, no flame
T_STRIKE = 1.4                # the match catches, and its light opens in rings
T_WIND = 2.4                  # he rears back from the door ...
THUDS = (2.85, 3.3, 3.75)     # ... and beats on it (we cut on the first blow)
T_GLANCE = 4.3                # her eye drops to the floor ...
T_SMILE = 4.65                # ... and the corner of her mouth lifts
WHIP = (5.1, 5.35)            # the camera whips down after her look
TAPS = (5.75, 6.25)           # her heel: a tap, then the hollow knock
T_OPEN = (6.25, 6.85)         # the floor opens into the section, top down
T_DOT = 6.95                  # the dot glows under her heel
T_LENS = 7.25                 # a lens joins it to the dot on the plan
T_TURN = (8.3, 8.8)           # the Cracker turns round to her (a paper turn)
T_ROLL = (8.2, 8.85)          # she brings the roll up from her coat ...
T_RAISE = (8.85, 9.4)         # ... to her eye ...
T_FALL = (9.45, 9.95)         # ... lets it fall open ...
T_LIFT = (10.1, 11.2)         # ... and lifts the sheet to us

# the two-shot: her profile close, the match before her mouth, the Cracker at the door beyond
FLAME = (800.0, 1400.0)
HER_AT, HER_S = (520.0, 1960.0), 1.45
FLOOR2 = 1240.0
DOOR_C, DOOR_R = (1130.0, 690.0), 500.0
CRACKER_X, CRACKER_S = 880.0, 0.55
R_LIT = 1150.0
# the pounding, from behind him: his back, his fists on the door, her match low behind him
POUND_DOOR = ((540.0, 760.0), 860.0)
POUND_LIGHT = (200.0, 2900.0)
BACK_AT, BACK_S = (540.0, 1330.0), 1.9
SHADOW_K = 1.35
# her eye, close (the eye at (430, 820))
EYE_S = 3.6
EYE_AT = (430.0 - (466.0 - 400.0) * EYE_S, 820.0 + (860.0 - 298.0) * EYE_S)
EYE_LIGHT = (1150.0, 1600.0)
# the floor, at floor level; and the section under it
FL = 1060.0
TOE = (906.0, FL)
HEEL_X = TOE[0] - 395.0       # where the heel's tip comes down
BALL = (TOE[0] - 150.0, FL)   # the foot rocks about the ball
FLOOR_LIGHT = (200.0, 400.0)
SLAB_B = FL + 60.0
CROWN, INVERT, WATER = 1520.0, 1780.0, 1748.0
LENS_C, LENS_R = (820.0, 1290.0), 185.0
# the sheet, as it hangs before her face, and as it fills the frame
SHEET0 = (400.0, 724.0, 1034.0)          # x0, x1, top (her fingers)
SHEET1 = (-160.0, 1240.0, -260.0, 2300.0)

DIM_GOLD = lerp(K.INK, K.GOLD, 0.45)
WALL = lerp(K.INK, K.NAVY, 0.7)
STEEL_D = lerp(K.NAVY, K.STEEL, 0.25)


def motion_blur(t, T):
    return 1


def _shot(t):
    name = SHOTS[0][1]
    for s0, nm in SHOTS:
        if t >= s0:
            name = nm
    return name


def _about(c, p, z):
    c.translate(*p)
    c.scale(z, z)
    c.translate(-p[0], -p[1])


# ============================================================================ light
def flicker(t, seed=0):
    """The flame's breath, about 1, shivering after each blow on the door."""
    tt = K.twos(t)
    f = 1.0 + 0.05 * math.sin(tt * 17.0 + seed) + 0.03 * math.sin(tt * 41.0 + 2.0 * seed)
    for th in THUDS:
        if th <= t < th + 0.5:
            f -= 0.12 * (1.0 - (t - th) / 0.5) * (0.5 + 0.5 * math.sin((t - th) * 60.0))
    return f


def _darkness(c, p, r, steps=((1.0, 0.45), (1.16, 0.75), (1.34, 1.0)), seed=0):
    """The dark beyond the light: INK laid over everything outside radius r of p, in three cut
    steps (no blur)."""
    for k, a in steps:
        rr = r * k
        pts = [(p[0] + rr * (1.0 + 0.012 * math.sin(i * 1.7 + seed)) * math.cos(2.0 * math.pi * i / 96.0),
                p[1] + rr * (1.0 + 0.012 * math.sin(i * 1.7 + seed)) * math.sin(2.0 * math.pi * i / 96.0)) for i in range(96)]
        c.save()
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        c.new_path()
        c.rectangle(-400.0, -400.0, K.W + 800.0, K.H + 800.0)
        D.poly(c, pts)
        c.set_source_rgba(*K.INK, a)
        c.fill()
        c.restore()


def _glow(c, p, r, a):
    """The match's gold on what it falls on (light adds)."""
    K.pool(c, p, r, r, K.GOLD, a, steps=5)


def _rim(c, draw_fn, color, off, alpha=1.0):
    """draw_fn's silhouette laid in `color` and shifted by off: the edge the light catches."""
    c.save()
    c.push_group()
    draw_fn(c)
    m = c.pop_group()
    c.translate(*off)
    c.set_source_rgba(*color, alpha)
    c.mask(m)
    c.restore()


def _match(c, p, t, lit):
    """The match in her fingers: the stick, the charred head and (lit) the flame, flaring as it
    catches."""
    bass.line_band(c, [(p[0] + 8.0, p[1] + 96.0), (p[0] + 1.0, p[1] + 4.0)], lerp(K.PAPER, K.GOLD, 0.35), width=7.0,
                   seed=901)
    K.dot(c, (p[0] + 1.0, p[1] + 2.0), 6.0, K.INK, seed=902)
    if lit:
        u = t - T_STRIKE
        flare = 1.0 + 0.7 * (1.0 - ease("out", clamp(u / 0.45)))
        grow = ease("outback", clamp(u / 0.12))
        if grow > 0.0:
            K.flame(c, p, t, flare * grow, seed=3)


def _sparks(c, p, t):
    """The scratch that does not catch: a spray of sparks off the head and a blink of light."""
    u = (t - T_SPARK) / 0.35
    if not 0.0 <= u < 1.0:
        return
    K.pool(c, p, 120.0, 120.0, K.GOLD, 0.3 * (1.0 - u), steps=3)
    for i in range(9):
        a = math.radians(-160.0 + 140.0 * hash01(i, 903))
        v = 300.0 + 260.0 * hash01(i, 904)
        q = (p[0] + math.cos(a) * v * u * 0.35, p[1] + math.sin(a) * v * u * 0.35 + 340.0 * (u * 0.35) ** 2)
        K.dot(c, q, 4.5 * (1.0 - u) + 1.0, K.GOLD, seed=905 + i)


# ============================================================================ the door, the Cracker
def _door(c, centre, r, seed=0):
    """The vault door from inside: a great steel disc in its jamb, rings, twelve bolt housings
    round its rim and a spoked wheel at its hub."""
    dark = lerp(STEEL_D, K.INK, 0.55)
    bass.fill_polys(c, [D.circle_pts(centre, r * 1.07, n=140)], lerp(WALL, K.INK, 0.4))
    bass.fill_polys(c, [D.circle_pts(centre, r, n=140)], STEEL_D)
    for k, rr in enumerate((0.93, 0.74, 0.4)):
        bass.ring(c, centre, r * rr, max(4.0, r * 0.012), dark, seed=seed + k, n=120)
    for i in range(12):
        a = 2.0 * math.pi * i / 12.0 + 0.13
        ca, sa = math.cos(a), math.sin(a)
        p0 = (centre[0] + ca * r * 0.78, centre[1] + sa * r * 0.78)
        p1 = (centre[0] + ca * r * 0.9, centre[1] + sa * r * 0.9)
        bass.line_band(c, [p0, p1], dark, width=r * 0.055, seed=seed + 10 + i)
    hub = r * 0.2
    bass.ring(c, centre, hub, r * 0.022, dark, seed=seed + 30)
    for i in range(6):
        a = 2.0 * math.pi * i / 6.0 + 0.4
        bass.line_band(c, [centre, (centre[0] + hub * math.cos(a), centre[1] + hub * math.sin(a))], dark,
                       width=r * 0.018, seed=seed + 31 + i)


# poses at the door (figure units, x toward the door): leaning on it, wound up, the blow landed
SLUMP = (16.0, -26.0, (118.0, -612.0), (100.0, -578.0))
WOUND = (-6.0, -8.0, (34.0, -722.0), (14.0, -700.0))
BLOW = (14.0, -2.0, (206.0, -636.0), (196.0, -606.0))


def _swing(t):
    """0 wound up .. 1 landed, through the three blows (after the last he sags on the door)."""
    h = 0.0
    for th in THUDS:
        if th - 0.14 <= t < th:
            h = ease("in3", (t - (th - 0.14)) / 0.14)
        elif th <= t < th + 0.12:
            h = 1.0
        elif th + 0.12 <= t < th + 0.32:
            h = 1.0 - ease("inout", (t - (th + 0.12)) / 0.2)
    if t >= THUDS[-1]:
        h = 1.0 - 0.4 * ease("inout", clamp((t - (THUDS[-1] + 0.12)) / 0.5))
    return h


def _mix(a, b, u):
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u), lerp(a[3], b[3], u))


def _cracker_pose(t):
    """The Cracker's pose at the door, and whether he has turned round to her."""
    breath = math.sin(t * 5.2)
    if t >= SHOTS[5][0]:                                   # after: forehead on the door, then he turns
        if t < (T_TURN[0] + T_TURN[1]) / 2.0:
            return pd.Pose(lean=20.0 + 2.0 * breath, head=-30.0, arms={"near": ("ang", 18.0, 26.0),
                                                                       "far": ("ang", 12.0, 22.0)}), False
        return pd.Pose(lean=5.0 + 1.0 * breath, head=-10.0, arms={"near": ("ang", 6.0, 16.0),
                                                                   "far": ("ang", -2.0, 12.0)}), True
    if t < T_WIND:
        lean, head, near, far = SLUMP
        lean += 2.5 * breath
        head += 3.0 * breath
    elif t < THUDS[0] - 0.14:
        lean, head, near, far = _mix(SLUMP, WOUND, ease("inout", clamp((t - T_WIND) / 0.3)))
    else:
        h, hf = _swing(t), _swing(t - 0.06)
        lean, head, near, _ = _mix(WOUND, BLOW, h)
        far = _mix(WOUND, BLOW, hf)[3]
    return pd.Pose(lean=lean, head=head, arms={"near": ("ik", near), "far": ("ik", far)}), False


def _cracker(c, t, x, floor, s, light, rim_w, bg=K.INK, rim=K.GOLD, color=K.INK):
    """The Cracker at x; through T_TURN he turns round (squashed through edge-on, cut-paper
    style) to face her."""
    pose, turned = _cracker_pose(t)
    sx = 1.0
    if T_TURN[0] <= t < T_TURN[1]:
        sx = math.cos(math.pi * ease("inout", (t - T_TURN[0]) / (T_TURN[1] - T_TURN[0])))
    elif t >= T_TURN[1]:
        sx = -1.0
    if abs(sx) < 0.03:
        sx = math.copysign(0.03, sx)
    c.save()
    c.translate(x, 0.0)
    c.scale(sx, 1.0)
    c.translate(-x, 0.0)
    lt = (light[0] * math.copysign(1.0, sx), light[1])
    j = C.draw(c, "cracker", C.standing("cracker"), pose, x, floor, s, 1, bg=bg, rim=rim, rim_w=rim_w, light=lt,
               color=color)
    c.restore()
    return j, turned


# ============================================================================ the two-shot
def two_zoom(t):
    if t < SHOTS[5][0]:
        return 1.0 + 0.035 * ease("inout", clamp((t - T_STRIKE) / 1.45))
    return 1.0 + 0.05 * ease("inout", clamp((t - SHOTS[5][0]) / (T_END - SHOTS[5][0])))


def _her_face(c, at, s, t, rim_off, look=0.55, lid=1.0, down=0.0, squint=0.0):
    def fn(cc):
        return F.her(cc, at, s, look=look, lid=lid, t=t, edge=DIM_GOLD, down=down, squint=squint)
    _rim(c, fn, K.GOLD, rim_off)
    return fn(c)


def _match_hand(c, at):
    F.hand(c, "architect", (at[0] - 600.0, at[1] + 1300.0), (at[0] + 10.0, at[1] + 104.0), 0.62, rim=K.GOLD,
           rim_off=(4.0, -3.0))


def two_shot(c, t, extra=None):
    """Her profile by the match, the Cracker at the door beyond. extra(c) draws in the scene,
    before the dark (her roll)."""
    fl = flicker(t)
    lit = t >= T_STRIKE
    c.save()
    _about(c, FLAME, two_zoom(t))
    if lit:
        bass.fill_polys(c, [[(-300.0, -300.0), (K.W + 300.0, -300.0), (K.W + 300.0, FLOOR2), (-300.0, FLOOR2)]], WALL)
        bass.fill_polys(c, [[(-300.0, FLOOR2), (K.W + 300.0, FLOOR2), (K.W + 300.0, K.H + 300.0), (-300.0, K.H + 300.0)]],
                        lerp(K.INK, K.STEEL, 0.22))
        _door(c, DOOR_C, DOOR_R, seed=910)
        _glow(c, FLAME, R_LIT * fl, 0.26)
        K.pool(c, (FLAME[0] + 120.0, FLOOR2 + 30.0), 520.0 * fl, 70.0 * fl, K.GOLD, 0.2, steps=3)   # on the floor
        bass.line_band(c, [(560.0, FLOOR2), (K.W + 200.0, FLOOR2)], DIM_GOLD, width=3.0, seed=912)
        _cracker(c, t, CRACKER_X, FLOOR2, CRACKER_S, (-0.31, 0.95), 4.0)
    _her_face(c, HER_AT, HER_S, t, (7.0, 4.0), look=0.55 if t < SHOTS[5][0] else 0.7)
    if t >= T_SPARK - 0.5:
        _match_hand(c, FLAME)
        _match(c, FLAME, t, lit)
    if extra is not None:
        extra(c)
    if lit:
        u = clamp((t - T_STRIKE) / 0.9)
        _darkness(c, FLAME, (R_LIT + 120.0) * ease("out3", u) * fl + 30.0)
    else:
        _darkness(c, FLAME, 1.0)
        _sparks(c, FLAME, t)
    c.restore()


# ============================================================================ the pounding
def _pound_cam(t):
    z = 1.0 + 0.06 * ease("inout", clamp((t - SHOTS[1][0]) / (SHOTS[2][0] - SHOTS[1][0])))
    dx = dy = 0.0
    for th in THUDS:
        if th <= t < th + 0.4:
            k = math.exp(-(t - th) * 12.0)
            dy += 16.0 * k * math.sin((t - th) * 75.0)
            dx += 7.0 * k * math.sin((t - th) * 53.0 + 1.0)
    return z, dx, dy


def _ell(c0, rx, ry, a0=0.0, a1=360.0, n=36):
    return [(c0[0] + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             c0[1] + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


# the Cracker from behind (back units: the base of his neck at (0, 0), y down)
_BK_HAT = _ell((0.0, -128.0), 64.0, 70.0, 180.0, 360.0, 24)
_BK_BRIM = _ell((0.0, -124.0), 94.0, 13.0)
_BK_HEAD = _ell((0.0, -78.0), 50.0, 58.0)
_BK_COAT = [(-30, -6), (-110, 8), (-150, 34), (-160, 90), (-150, 200), (-128, 300), (-150, 420), (-180, 600), (-200, 900),
            (200, 900), (180, 600), (150, 420), (128, 300), (150, 200), (160, 90), (150, 34), (110, 8), (30, -6)]
_BK_COLLAR = [(-44, -22), (44, -22), (48, 12), (-48, 12)]
_BK_SHOULDER = (138.0, 50.0)
_BK_DOOR = ((232.0, -10.0), (146.0, -112.0))       # elbow, fist: on the door at head height
_BK_BACK = ((236.0, 34.0), (172.0, -56.0))         # pulled back toward us


def _back_arm(h, side):
    """(shoulder, elbow, fist, fist scale) for one arm, h 0 pulled back .. 1 on the door."""
    e = lerp(_BK_BACK[0], _BK_DOOR[0], h)
    f = lerp(_BK_BACK[1], _BK_DOOR[1], h)
    return ((side * _BK_SHOULDER[0], _BK_SHOULDER[1]), (side * e[0], e[1]), (side * f[0], f[1]), lerp(1.12, 1.0, h))


def _back_polys(t):
    """His back as polygons in back units, and his fists (back units)."""
    polys = [_BK_COAT, _BK_COLLAR, _BK_HEAD, _ell((-50.0, -84.0), 10.0, 18.0), _ell((50.0, -84.0), 10.0, 18.0),
             _BK_HAT, _BK_BRIM]
    fists = []
    for side, lag in ((-1, 0.0), (1, 0.05)):
        sh, el, fi, fs = _back_arm(_swing(t - lag), side)
        polys.append(bass.capsule_pts(sh, el, 27.0, 23.0, cap=6))
        polys.append(bass.capsule_pts(el, fi, 23.0, 20.0, cap=6))
        polys.append(_ell(fi, 40.0 * fs, 44.0 * fs))
        fists.append(fi)
    return polys, fists


def _back_at(p):
    return (BACK_AT[0] + p[0] * BACK_S, BACK_AT[1] + p[1] * BACK_S)


def _draw_back(c, polys, color=K.INK):
    bass.fill_polys(c, [bass.orient([_back_at(p) for p in poly], True) for poly in polys], color)


def pound_shot(c, t):
    fl = flicker(t)
    centre, r = POUND_DOOR
    z, dx, dy = _pound_cam(t)
    polys, fists = _back_polys(t)
    c.save()
    c.translate(dx, dy)
    _about(c, (540.0, 1000.0), z)
    K.fill(c, WALL)
    _door(c, centre, r, seed=920)
    _glow(c, POUND_LIGHT, 2300.0 * fl, 0.3)
    # his shadow on the door, looming over him
    c.save()
    c.new_path()
    D.poly(c, D.circle_pts(centre, r * 1.07, n=140))
    c.clip()
    c.push_group()
    _about(c, POUND_LIGHT, SHADOW_K)
    _draw_back(c, polys)
    c.pop_group_to_source()
    c.paint_with_alpha(0.7)
    c.restore()
    # his back, the match's edge on it
    _rim(c, lambda cc: _draw_back(cc, polys), K.GOLD, (-7.0, 5.0))
    _draw_back(c, polys)
    for th in THUDS:                                       # the blows, on the steel; dust shaken down
        for k, lag in enumerate((0.0, 0.05)):
            if th + lag <= t < th + lag + 0.6:
                K.ripple(c, _back_at(fists[k]), t, th + lag, K.PAPER, n=2, every=0.1, life=0.5, r0=30.0, r1=200.0,
                         width=7.0, alpha=0.85)
        u = (t - th) / 1.1
        if 0.0 <= u < 1.0:
            for i in range(14):
                x = 120.0 + 840.0 * hash01(i, th, 931)
                y = -40.0 + 160.0 * hash01(i, th, 932) + 1000.0 * (u * (0.5 + 0.5 * hash01(i, th, 933))) ** 1.6
                K.dot(c, (x, y), 3.0 + 2.5 * hash01(i, th, 934), K.PAPER, seed=935 + i, alpha=0.6 * (1.0 - u))
    _darkness(c, (POUND_LIGHT[0] + 200.0, POUND_LIGHT[1] - 600.0), 2400.0 * fl)
    c.restore()


# ============================================================================ her eye
def _face_pt(at, s, p):
    return (at[0] + (p[0] - 400.0) * s, at[1] + (p[1] - 860.0) * s)


def eye_zoom(t):
    return 1.0 + 0.08 * ease("inout", clamp((t - SHOTS[2][0]) / (WHIP[1] - SHOTS[2][0])))


def eye_shot(c, t):
    fl = flicker(t)
    down = ease("inout", clamp((t - T_GLANCE) / 0.3))
    smile = ease("inout", clamp((t - T_SMILE) / 0.45))
    c.save()
    _about(c, (430.0, 820.0), eye_zoom(t))
    K.fill(c, K.INK)
    _glow(c, EYE_LIGHT, 1100.0 * fl, 0.42)
    _her_face(c, EYE_AT, EYE_S, t, (9.0, 3.0), look=0.6, lid=1.0, down=down, squint=0.55 * smile)
    # the match in her eye
    pu = _face_pt(EYE_AT, EYE_S, (466.0 + 46.0 * (0.12 + 0.22 * 0.6) + 2.0, 298.0 + 18.0 * (0.05 + 0.108 + 0.32 * down)
                                  - 4.0))
    K.dot(c, pu, 6.0 * fl, K.GOLD, seed=941)
    # the light along her lips: the line of her mouth, whose corner lifts; her cheek rises
    pts = [_face_pt(EYE_AT, EYE_S, p) for p in ((517.0, 456.0), (503.0, 460.0 - 2.0 * smile),
                                               (491.0, 459.0 - 7.0 * smile), (481.0, 455.0 - 13.0 * smile))]
    bass.line_band(c, pts, K.GOLD, width=8.0, seed=942, taper=(1.0, 0.45), alpha=0.85)
    if smile > 0.0:
        ch = [_face_pt(EYE_AT, EYE_S, (440.0 + 12.0 * i, 350.0 - 10.0 * smile - 3.0 * math.sin(math.pi * i / 4.0)))
              for i in range(5)]
        bass.line_band(c, ch, K.GOLD, width=6.0, seed=943, taper=(0.4, 0.4), alpha=0.5 * smile)
    # her look, to the floor
    K.sight_line(c, pu, (pu[0] + 0.85 * 1700.0, pu[1] + 0.53 * 1700.0), t, T_GLANCE + 0.1, color=K.PAPER, dur=0.4,
                 seed=944)
    _darkness(c, EYE_LIGHT, 1500.0 * fl)
    c.restore()


# ============================================================================ the floor
def heel_angle(t):
    """Her heel's lift (degrees about the ball of the foot): up, tap; up, knock."""
    for t0, deg in zip(TAPS, (12.0, 17.0)):
        if t0 - 0.34 <= t < t0:
            up = ease("out", clamp((t - (t0 - 0.34)) / 0.2))
            down = ease("in3", clamp((t - (t0 - 0.1)) / 0.1))
            return deg * up * (1.0 - down)
    return 0.0


_SHOE = ((14, -10), (4, 0), (-70, 2), (-150, 0), (-206, -14), (-262, -46), (-314, -82), (-352, -100), (-372, -104),
         (-386, -40), (-389, 0), (-401, 0), (-404, -50), (-410, -106), (-422, -122), (-426, -150), (-418, -176),
         (-380, -172), (-340, -160), (-300, -150), (-240, -128), (-170, -96), (-100, -64), (-40, -38))
_LEG = ((-300, -150), (-318, -210), (-324, -300), (-334, -440), (-340, -600), (-338, -760), (-332, -900), (-326, -1100),
        (-432, -1100), (-440, -920), (-456, -800), (-470, -680), (-468, -580), (-446, -460), (-412, -330), (-404, -250),
        (-418, -170))
_HEM = ((-820, -1300), (220, -1300), (220, -940), (100, -912), (-40, -900), (-180, -914), (-330, -896), (-480, -910),
        (-640, -890), (-820, -930))


def _foot(c, t):
    """Her foot in a pump, her calf, the coat's hem; the foot rocks about the ball, the leg rides
    up with the ankle."""
    a = math.radians(heel_angle(t))
    ca, sa = math.cos(a), math.sin(a)
    bx = BALL[0] - TOE[0]

    def shoe_pt(p):
        x, y = p[0] - bx, p[1]
        return (TOE[0] + bx + x * ca - y * sa, TOE[1] + x * sa + y * ca)
    ank0 = (-370.0, -170.0)
    ank1 = shoe_pt(ank0)
    lift = (ank1[0] - (TOE[0] + ank0[0]), ank1[1] - (TOE[1] + ank0[1]))

    def fn(cc):
        bass.fill_polys(cc, [bass.orient([(TOE[0] + x + lift[0], TOE[1] + y + lift[1]) for x, y in _LEG], True)], K.INK)
        bass.fill_polys(cc, [bass.orient([shoe_pt(p) for p in _SHOE], True)], K.INK)
        bass.fill_polys(cc, [bass.orient([(TOE[0] + x, TOE[1] + y + 0.3 * lift[1]) for x, y in _HEM], True)], K.INK)
    _rim(c, fn, K.GOLD, (-5.0, -4.0))
    fn(c)
    hem = [(TOE[0] + x, TOE[1] + y + 0.3 * lift[1]) for x, y in _HEM[2:]]
    bass.line_band(c, hem, DIM_GOLD, width=4.0, seed=951)


def _section(c, t):
    """Below the floor line: the blueprint section, revealed top down: the slab, the earth, the
    pipe (dashed, as the plan draws what is underground), the knock ringing down, the dot."""
    u = ease("out3", clamp((t - T_OPEN[0]) / (T_OPEN[1] - T_OPEN[0])))
    if u <= 0.0:
        return
    y1 = lerp(FL, K.H + 10.0, u)
    c.save()
    c.new_path()
    c.rectangle(-10.0, FL, K.W + 20.0, y1 - FL)
    c.clip()
    K.fill(c, K.BLUE)
    for i in range(1, 12):                                 # the sheet's grid
        bass.line_band(c, [(90.0 * i, FL), (90.0 * i, K.H)], K.PAPER, width=1.5, seed=960 + i, alpha=0.1)
    for j in range(1, 10):
        bass.line_band(c, [(0.0, FL + 96.0 * j), (K.W, FL + 96.0 * j)], K.PAPER, width=1.5, seed=975 + j, alpha=0.1)
    # the slab, cut and hatched
    K.chalk_line(c, [(-10.0, FL + 3.0), (K.W + 10.0, FL + 3.0)], 1.0, 7.0, K.PAPER, seed=985)
    K.chalk_line(c, [(-10.0, SLAB_B), (K.W + 10.0, SLAB_B)], 1.0, 4.0, K.PAPER, seed=986)
    for i in range(-2, 28):
        x = 44.0 * i
        K.chalk_line(c, [(x, SLAB_B - 2.0), (x + 50.0, FL + 8.0)], 1.0, 2.0, K.PAPER, seed=987 + i, alpha=0.55)
    # the earth: a sparse stipple down to the pipe
    for i in range(70):
        x = K.W * hash01(i, 1010)
        y = SLAB_B + 30.0 + (CROWN - SLAB_B - 60.0) * hash01(i, 1011)
        K.dot(c, (x, y), 2.5 + 1.5 * hash01(i, 1012), K.PAPER, seed=1013 + i, alpha=0.3)
    # the pipe: its crown and invert dashed, the water in it
    for y, sd in ((CROWN, 1020), (INVERT, 1021)):
        K.dashes(c, [(-10.0, y), (K.W + 10.0, y)], K.PAPER, 5.0, 26.0, 16.0, 1.0, sd, 0.9)
    wav = [(x, WATER + 4.0 * math.sin(x * 0.03 + t * 3.0)) for x in range(-10, int(K.W) + 20, 30)]
    bass.line_band(c, wav, K.PAPER, width=2.5, seed=1022, alpha=0.5)
    # the knock, ringing down through it
    K.ripple(c, (HEEL_X, FL), t, TAPS[1], K.PAPER, n=3, every=0.16, life=0.9, r0=20.0, r1=760.0, width=6.0)
    # the dot: exactly under her heel, on the pipe, a plumb line down to it
    g = clamp((t - T_DOT) / 0.25)
    if g > 0.0:
        K.dashes(c, [(HEEL_X, SLAB_B + 14.0), (HEEL_X, SLAB_B + 14.0 + (CROWN - SLAB_B - 34.0) * ease("out", g))],
                 K.GOLD, 3.0, 14.0, 10.0, 1.0, 1024, 0.9)
        K.ripple(c, (HEEL_X, CROWN), t, T_DOT, K.GOLD, n=2, every=0.25, life=0.8, r0=14.0, r1=90.0, width=5.0)
        K.dot(c, (HEEL_X, CROWN), 13.0 * ease("outback", g), K.PAPER, seed=1023)
    c.restore()


LENS_CAM = (520.0, 590.0, 0.8)


def _plan_lens(c, t):
    cam = P.PlanCam(LENS_CAM[0], LENS_CAM[1], LENS_CAM[2], 90.0, 0.0, fx=LENS_C[0], fy=LENS_C[1])
    K.fill(c, K.DEEP)
    P.table(c, cam, 1.0, 1.0, 1.0)
    d = cam.to_view(P.DOT, 0.0)
    K.ripple(c, d, t, T_LENS + 0.15, K.GOLD, n=2, every=0.25, life=0.8, r0=10.0, r1=60.0, width=4.0)


def floor_shot(c, t):
    fl = flicker(t)
    K.fill(c, K.INK)
    _glow(c, FLOOR_LIGHT, 950.0 * fl, 0.26)
    bass.fill_polys(c, [bass.cut_rect(-10.0, FL, K.W + 10.0, K.H + 10.0, seed=990, amp=0.4)], K.INK)
    _darkness(c, FLOOR_LIGHT, 1150.0 * fl)
    bass.line_band(c, [(-10.0, FL), (K.W + 10.0, FL)], DIM_GOLD, width=3.0, seed=991)   # the floor's edge
    _section(c, t)
    # where her look lands: a ring on the floor at her heel
    ring_u = ease("out", clamp((t - (WHIP[1] - 0.02)) / 0.35))
    ring_a = 1.0 - clamp((t - (T_LENS + 0.2)) / 0.3)
    if ring_u > 0.0 and ring_a > 0.0:
        K.marker_ring(c, (HEEL_X, FL), 66.0, 15.0, u=ring_u, color=K.PAPER, width=7.0, tilt=0.0, seed=952, alpha=ring_a)
    _foot(c, t)
    K.sight_line(c, (250.0, -80.0), (HEEL_X - 4.0, FL - 10.0), t, WHIP[0] - 0.05, color=K.PAPER, dur=0.3,
                 off=TAPS[0] - 0.12, off_dur=0.25, seed=953)
    for t0 in TAPS:                                        # the taps, on the floor
        if t0 <= t < t0 + 0.4:
            K.ripple(c, (HEEL_X, FL), t, t0, K.GOLD, n=1, life=0.4, r0=10.0, r1=80.0, width=4.0)
    lu = min(clamp((t - T_LENS) / 0.3), 1.0 - clamp((t - (SHOTS[5][0] - 0.12)) / 0.12))
    if lu > 0.0:
        K.callout(c, (HEEL_X, CROWN), LENS_C, LENS_R, lambda cc: _plan_lens(cc, t), u=lu, color=K.PAPER, ring_w=8.0,
                  dot_r=0.0, line_w=4.0, seed=992)


# ============================================================================ the whip down
def _whip_dy(t):
    return K.H * ease("inout3", clamp((t - WHIP[0]) / (WHIP[1] - WHIP[0])))


def whip_shot(c, t, samples=8):
    """Her eye goes up out of frame and the floor comes up into it, smeared (box-averaged over
    one frame)."""
    for i in range(samples):
        tt = t - i / (24.0 * samples)
        dy = _whip_dy(tt)
        c.push_group()
        K.fill(c, K.INK)
        c.save()
        c.translate(0.0, -dy)
        eye_shot(c, tt)
        c.restore()
        c.save()
        c.translate(0.0, K.H - dy)
        floor_shot(c, tt)
        c.restore()
        c.pop_group_to_source()
        c.paint_with_alpha(1.0 / (i + 1))


# ============================================================================ the roll and the sheet
def _sway(t):
    if t < T_FALL[1]:
        return 0.0
    u = t - T_FALL[1]
    return 26.0 * math.sin(2.0 * math.pi * u / 1.1) * math.exp(-u * 1.6)


def _to_screen(p, z):
    return (FLAME[0] + (p[0] - FLAME[0]) * z, FLAME[1] + (p[1] - FLAME[1]) * z)


def _to_scene(p, z):
    return (FLAME[0] + (p[0] - FLAME[0]) / z, FLAME[1] + (p[1] - FLAME[1]) / z)


def sheet_quad(t):
    """The tracing sheet on screen as (top-left, top-right, bottom-right, bottom-left), or None
    before it falls open. It hangs in the scene from her fingers, then she lifts it to the lens."""
    if t < T_FALL[0]:
        return None
    x0, x1, top = SHEET0
    bot = lerp(top, 2200.0, ease("in", clamp((t - T_FALL[0]) / (T_FALL[1] - T_FALL[0]))))
    sw = _sway(t)
    z = two_zoom(t)
    q = [_to_screen(p, z) for p in ((x0, top), (x1, top), (x1 + sw, bot), (x0 + sw, bot))]
    u = ease("inout3", clamp((t - T_LIFT[0]) / (T_LIFT[1] - T_LIFT[0])))
    if u > 0.0:
        a0, a1, at, ab = SHEET1
        q = [lerp(q[0], (a0, at), u), lerp(q[1], (a1, at), u), lerp(q[2], (a1 + sw, ab), u), lerp(q[3], (a0 + sw, ab), u)]
    return tuple(q)


def _bilerp(q, u, v):
    a = lerp(q[0], q[1], u)
    b = lerp(q[3], q[2], u)
    return lerp(a, b, v)


def sheet(c, t, flame=None, alpha=0.26):
    """The translucent sheet: fibrous, crisp edged, a light behind it glowing through."""
    q = sheet_quad(t)
    if q is None:
        return
    c.save()
    c.new_path()
    D.poly(c, list(q))
    c.clip()
    K.fill(c, K.PAPER, alpha=alpha)
    if flame is not None:
        K.pool(c, flame, 300.0, 300.0, lerp(K.PAPER, K.GOLD, 0.5), 0.2, steps=4)
    for i in range(70):                                    # the fibres in it
        u0, v0 = hash01(i, 1051), hash01(i, 1052)
        ang = 2.0 * math.pi * hash01(i, 1053)
        L = 0.02 + 0.03 * hash01(i, 1054)
        fib = [_bilerp(q, u0 + L * math.cos(ang) * k / 3.0, v0 + 0.4 * L * math.sin(ang) * k / 3.0 + 0.004 * math.sin(k))
               for k in range(4)]
        bass.line_band(c, fib, K.PAPER, width=1.6, seed=1055 + i, alpha=0.16)
    c.restore()
    bass.line_band(c, [q[0], q[3]], K.PAPER, width=3.0, seed=1031, alpha=0.6)
    bass.line_band(c, [q[1], q[2]], K.PAPER, width=3.0, seed=1032, alpha=0.6)
    bass.line_band(c, [q[0], q[1]], K.PAPER, width=5.0, seed=1033, alpha=0.7)
    if q[3][1] < K.H + 60.0:                              # the roll, unrolling at the bottom edge
        _roll(c, q[3], q[2], 16.0)


def _roll(c, a, b, r):
    bass.fill_polys(c, [bass.orient(bass.capsule_pts(a, b, r, r, cap=4), True)], K.PAPER)
    bass.line_band(c, [(a[0] + 8.0, a[1] + r * 0.45), (b[0] - 8.0, b[1] + r * 0.45)], DIM_GOLD, width=4.0, seed=1041)
    for e in (a, b):
        bass.ring(c, e, r * 0.55, 2.0, DIM_GOLD, seed=1042, n=16)


def _roll_y(t):
    """The roll in her hand before it falls open: its height, or None."""
    if not T_ROLL[0] <= t < T_FALL[0]:
        return None
    y = lerp(2090.0, 1560.0, ease("out3", clamp((t - T_ROLL[0]) / (T_ROLL[1] - T_ROLL[0]))))
    return lerp(y, SHEET0[2], ease("inout", clamp((t - T_RAISE[0]) / (T_RAISE[1] - T_RAISE[0]))))


def roll_shot(c, t):
    x0, x1, _ = SHEET0
    xm = (x0 + x1) / 2.0

    def in_scene(cc):
        y = _roll_y(t)
        q = sheet_quad(t)
        if y is not None:                                  # the roll in her hand
            _roll(cc, (x0, y), (x1, y), 16.0)
            grip = (xm, y + 14.0)
        elif q is not None:                                # her fingers on its top edge, sliding to the
            u = ease("inout3", clamp((t - T_LIFT[0]) / (T_LIFT[1] - T_LIFT[0])))   # corner as she lifts it
            top_c = ((q[0][0] + q[1][0]) / 2.0, q[0][1] + 6.0)
            grip = _to_scene(lerp(top_c, (q[0][0] + 70.0, q[0][1] + 20.0), u), two_zoom(t))
        else:
            return
        F.hand(cc, "architect", (grip[0] - 380.0, grip[1] + 1300.0), grip, 0.62, rim=K.GOLD, rim_off=(4.0, -3.0))

    two_shot(c, t, in_scene)
    sheet(c, t, flame=FLAME)


# ============================================================================ render
def _fist_frame(t):
    """Where his near fist lands on the door at the second blow (frame px): the lens holds there
    while the fist bounces off it."""
    th = THUDS[1]
    z, dx, dy = _pound_cam(th)
    _, fists = _back_polys(th)
    x, y = _back_at(fists[0])
    return (540.0 + (x - 540.0) * z + dx, 1000.0 + (y - 1000.0) * z + dy)


INSERTS = (S.Punch(THUDS[1] - 0.01, 5, _fist_frame, 4.0, seed=81),)    # the second blow, close


def render(f, t, T):
    S.play(f, t, T, render_plain, INSERTS)


def render_plain(f, t, T):
    name = _shot(t)
    K.scene_setup(f, K.INK)
    with f.screen() as c:
        if name == "match":
            two_shot(c, t)
        elif name == "pound":
            pound_shot(c, t)
        elif name == "eye":
            eye_shot(c, t)
        elif name == "whip":
            whip_shot(c, t)
        elif name == "floor":
            floor_shot(c, t)
        else:
            roll_shot(c, t)


def cues(T):
    out = [Cue(0.0, "black, and the Cracker's ragged breathing, close; the alarm muffled away beyond the vault walls",
               gain_db=-14, dur=T_STRIKE),
           Cue(T_SPARK, "a match scratched on its box: sparks, no flame", gain_db=-10, pan=0.3),
           Cue(T_STRIKE, "the match strikes and flares (a hiss and a soft whump)", gain_db=-7, pan=0.3),
           Cue(T_STRIKE + 0.2, "the flame's small steady hiss, close", gain_db=-24, pan=0.3,
               dur=T.duration - T_STRIKE - 0.2),
           Cue(T_WIND, "his breath catches; cloth as he rears back", gain_db=-15, pan=0.4)]
    for i, th in enumerate(THUDS):
        out.append(Cue(th, "a fist on the vault door: a huge muffled steel BOOM", gain_db=-4 - 2 * i, pan=0.1))
    out += [Cue(SHOTS[2][0], "a single low piano note under the flame's hiss", gain_db=-14),
            Cue(T_GLANCE + 0.1, "a soft chalk tick: her look drops to the floor", gain_db=-20),
            Cue(T_SMILE, "the corner of her mouth lifts: the theme's first two notes, upright, on the vibraphone",
                gain_db=-13),
            Cue(WHIP[0], "a fast whoosh down", gain_db=-14, dur=WHIP[1] - WHIP[0]),
            Cue(WHIP[1], "chalk: the ring drawn on the floor", gain_db=-20, pan=-0.1),
            Cue(TAPS[0], "her heel taps the floor: a hard click on steel", gain_db=-9, pan=-0.1),
            Cue(TAPS[1], "the second tap: a hollow knock, deep and resonant, booming down into a void", gain_db=-5,
                pan=-0.1),
            Cue(T_OPEN[0], "paper drawn down fast: the floor opens into the section", gain_db=-15,
                dur=T_OPEN[1] - T_OPEN[0]),
            Cue(T_DOT, "a ting: the chalk dot glows under her heel", gain_db=-10, pan=-0.1),
            Cue(T_LENS, "a soft chalk tick: the lens opens on the plan's dot", gain_db=-18, pan=0.3),
            Cue(T_ROLL[0], "cloth: she reaches into her coat", gain_db=-18, pan=-0.3),
            Cue(T_TURN[0], "the Cracker turns round to her (a shuffle; his breath stops)", gain_db=-18, pan=0.3),
            Cue(T_RAISE[0], "a roll of paper drawn out", gain_db=-16, pan=-0.2),
            Cue(T_FALL[0], "tracing paper unrolling as it drops: a long crisp rustle", gain_db=-10,
                dur=T_FALL[1] - T_FALL[0] + 0.2),
            Cue(T_LIFT[0], "the sheet lifted toward us: a slow paper swish", gain_db=-14, dur=T_LIFT[1] - T_LIFT[0]),
            Cue(T_FALL[0], "the score gathers: a rising chord held into the rewind", gain_db=-14,
                dur=T.duration - T_FALL[0])]
    return out
