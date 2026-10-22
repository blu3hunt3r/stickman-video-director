"""s11 · FORTY DOLLS · 10.0 s · the killer's room (one continuous shot).

His wall: 40 PAPER dolls pinned in the 5 x 8 grid at the facade lock (sets_rooms.KillerRoom,
lock camera, the s01 rhyme), every doll a different cut-paper silhouette (_lib_s11_s12).
Dark room; a cop's torch from below-left does the looking.

  < 0.32   (tear IN from s10) black wall, the police light bar strobing blue/red through
           the venetian blinds at the top right throws slatted stripes over the top rows.
  0.32     the torch clicks on low on the bottom rows (31, 36).
  1.00-    L25 "They found forty paper dolls in his room. One for every window."
           The beam sweeps: along rows 7/6 to THE CRIER (30) at 1.85, up across the grid to
           THE CAT LADY (12) at 3.15, up to THE DANCER (4) at 3.95. The strobe fades out.
  [window] 4.03: a press photographer's flashbulb. For three frames the grid IS the facade
           (s01's Bass print: PAPER field, the 40 ink windows, a paper doll in each), then the
           real wall, every doll at once, decaying to dark in ~0.6 s. The one red doll shows.
  4.4-6.0  the beam searches back down and left, then swings onto doll 9.
  6.00     L26 "One of them was holding binoculars." The beam lands on doll 9 (her: RED paper
           trench coat, ink binoculars) and the camera pushes in (6.0-8.1, log zoom 1 -> 3.6)
           to her, then creeps on (zoom 3.9 at 10.625). She trembles on her pin.
  OUT      dissolve 1.25 s to s12 (t 9.375-10.625): doll 9's pin (head centre) sits at screen
           (540, 905), the doll ~420 px tall (crown y ~878, heels y ~1300), arms up in a W.
"""
import math

import cairo

from engine import bass, draw
from engine.core import W, H, clamp, ease, fbm1, hash01, lerp, noise1, siren
from engine.frame import Camera
from engine.palette import PAPER, RED
from engine.timing import Cue
from films.shadowplay.sets_base import BLUE, HOT, INK, PAL, cone, glow, mix, mul, shadow_screen
from films.shadowplay.sets_facade import LOCK_COLS, LOCK_ROWS
from films.shadowplay.sets_rooms import KillerRoom
from films.shadowplay.scenes import _lib_s11_s12 as lib

ROOM = KillerRoom((540.0, 965.0), 1.0)
LOCK = Camera(540.0, 960.0, 1.0)

TORCH_ON = 0.32
HER = 9
PUSH = (6.0, 8.1)
Z_PUSH, Z_END, T_END = 3.6, 3.9, 10.625
PIN_SCREEN = (540.0, 905.0)          # where doll 9's pin sits at the end (s12 match)
GFX = 0.15                           # the facade-print flash frames after [window]
TORCH_COL = (1.0, 0.91, 0.76)
FLASH_COL = (1.0, 0.985, 0.96)
TORCH_HAND = (112.0, 1868.0)         # the cop's torch head, par 1.6 (his arm comes in bottom left)
TORCH_PAR = 1.6
FLASH_AT = (930.0, 1418.0)           # the photographer's bulb (his flashgun's dish), bottom right
FG_BLUR = 14.0                       # the two men in the foreground (par 1.6, out of focus)

# s01's Bass grid (ink lines between the windows)
V_LINES = (LOCK_COLS[0] - 77.5,) + tuple((LOCK_COLS[i] + LOCK_COLS[i + 1]) / 2 for i in range(4)) + (LOCK_COLS[-1] + 77.5,)
H_LINES = tuple(LOCK_ROWS[0] - 75.0 + 150.0 * i for i in range(9))


def _k(t, t0, dur, e="inout"):
    return ease(e, (t - t0) / dur) if dur > 0 else float(t >= t0)


# ----------------------------------------------------------------------------- timing
def _beats(T):
    return dict(window=T.at("window"), one=T.at("One", 1), bino=T.end("binoculars"))


# the torch's aim (world, on the wall): (t, (x, y), ease into this key)
_AIM = [
    (TORCH_ON, (322.0, 1478.0)),
    (0.95, (300.0, 1372.0), "out"),
    (1.85, (812.0, 1214.0), "inout"),
    (2.45, (846.0, 1152.0), "inout"),
    (3.15, (408.0, 760.0), "inout"),
    (3.55, (398.0, 728.0), "inout"),
    (3.95, (668.0, 452.0), "inout"),
    (4.40, (650.0, 430.0), "out"),
    (4.95, (402.0, 512.0), "inout"),
    (5.45, (448.0, 668.0), "inout"),
    (5.92, (702.0, 586.0), "inout3"),
]


def _aim(t):
    ks = _AIM
    if t <= ks[0][0]:
        p = ks[0][1]
    elif t >= ks[-1][0]:
        p = ks[-1][1]
    else:
        p = ks[-1][1]
        for i in range(1, len(ks)):
            if t <= ks[i][0]:
                t0, a = ks[i - 1][0], ks[i - 1][1]
                t1, b = ks[i][0], ks[i][1]
                e = ks[i][2] if len(ks[i]) > 2 else "inout"
                u = ease(e, (t - t0) / (t1 - t0))
                p = (lerp(a[0], b[0], u), lerp(a[1], b[1], u))
                break
    x, y = p
    # landing on her: a small overshoot and settle, then a steady but living hand
    if t > 5.92:
        d = t - 5.92
        sp = math.exp(-d / 0.22) * math.sin(d * 2 * math.pi * 1.7)
        x += -9.0 * sp
        y += 5.0 * sp
        x += (695.0 - 702.0) * _k(t, 5.92, 0.6, "inout")
        y += (612.0 - 586.0) * _k(t, 5.92, 1.6, "inout")
    amp = 5.0 if t < 5.9 else 2.2
    x += amp * fbm1(t * 1.7, 41) + 1.2 * noise1(t * 9.0, 43)
    y += amp * fbm1(t * 1.5, 47) + 1.2 * noise1(t * 8.0, 49)
    return (x, y)


def _torch_level(t):
    if t < TORCH_ON:
        return 0.0
    d = t - TORCH_ON
    # a cheap torch: a stutter as the switch catches, then steady
    if d < 0.12:
        return (0.0, 0.7, 0.25, 0.9, 1.0)[min(4, int(d / 0.024))]
    return 1.0 - 0.04 * abs(noise1(t * 6.0, 5))


def _radius(t):
    return lerp(205.0, 150.0, _k(t, 5.9, 2.4, "inout")) + 12.0 * fbm1(t * 0.5, 61)


def _police(t):
    return 0.85 * (1.0 - _k(t, 1.2, 1.6, "inout"))


def _flash(t, B):
    d = t - B["window"]
    if d < 0:
        return 0.0
    return math.exp(-d / 0.24)


# ----------------------------------------------------------------------------- camera
def _push_state(t):
    """(pin screen point of doll 9, zoom)."""
    pin = ROOM.pin(HER)
    p0 = LOCK.to_screen(pin)
    u = _k(t, PUSH[0], PUSH[1] - PUSH[0], "inout3")
    z = math.exp(lerp(0.0, math.log(Z_PUSH), u))
    if t > PUSH[1]:
        z = math.exp(lerp(math.log(Z_PUSH), math.log(Z_END), _k(t, PUSH[1], T_END - PUSH[1], "out")))
    ps = (lerp(p0[0], PIN_SCREEN[0], u), lerp(p0[1], PIN_SCREEN[1], u))
    return ps, z


def camera(t):
    pin = ROOM.pin(HER)
    ps, z = _push_state(t)
    cam = Camera(pin[0] + (W / 2 - ps[0]) / z, pin[1] + (H / 2 - ps[1]) / z, z)
    amp = 2.6 if t < PUSH[0] else lerp(2.6, 1.6, _k(t, PUSH[0], 2.0))
    return cam.shaken(t, amp=amp, rot_amp=0.12, freq=0.55, seed=11)


def _torch_hand(t):
    """The torch head in the cop's fist (par 1.6 world): his arm follows the aim a little."""
    a = _aim(t)
    return (TORCH_HAND[0] + 14.0 * fbm1(t * 0.6, 3) + 0.035 * (a[0] - 540.0),
            TORCH_HAND[1] + 10.0 * fbm1(t * 0.5, 7) + 0.030 * (a[1] - 960.0))


def _torch_origin(f, t):
    """The torch lens (held by a cop near the camera, par 1.6) as a point on the wall plane."""
    cf = f.cam.parallax(TORCH_PAR)
    return f.cam.to_world(cf.to_screen(_torch_hand(t)))


# ----------------------------------------------------------------------------- the dolls
def _sway(i, t, B):
    c = ROOM.center(i)
    a = 0.55 * noise1(t * 0.35 + i * 7.13, 101)
    # the draft from the door the police left open: a wave across the wall from the left
    t0 = -0.35 + c[0] / 900.0 + 0.04 * hash01(i, 3)
    if t > t0:
        d = t - t0
        a += 2.4 * math.exp(-d / 0.9) * math.sin(d * 2 * math.pi * (1.3 + 0.3 * hash01(i, 5)))
    if i == HER:
        # she breathes on her pin while we look at her
        a += 0.7 * _k(t, 6.2, 1.5) * math.sin((t - 6.2) * 2 * math.pi * 0.42)
    return a


def _doll_xf(i, t, B):
    d = lib.dolls()[i]
    return ROOM.pin(i), d.hang + _sway(i, t, B)


def _paper_col(i):
    d = lib.dolls()[i]
    warm = hash01(i, 9)
    return mix(mul(PAPER, d.tone), (0.97, 0.90, 0.78), 0.25 * warm)


def _shadows(L, t, B, origin):
    """All forty dolls' soft shadows on the wallpaper (KillerRoom's own pass uses the doll
    colour as a gel, so PAPER dolls cast none: done here in ink)."""
    D = lib.dolls()
    fl = _flash(t, B)
    tl = _torch_level(t)
    w_flash = fl / max(fl + 0.6 * tl, 1e-6) if fl > 0.02 else 0.0
    passes = []
    if w_flash < 0.98:
        passes.append((origin, 0.62 * (1.0 - w_flash)))
    if w_flash > 0.02:
        passes.append((FLASH_AT, 0.62 * w_flash))
    for src, dens in passes:
        def casters(c):
            for i in range(1, 41):
                pin, ang = _doll_xf(i, t, B)
                D[i].draw(c, pin, lib.K_DOLL, ang, solid=INK)
        box = (ROOM.o[0] - 470.0, ROOM.o[1] - 640.0, ROOM.o[0] + 470.0, ROOM.o[1] + 640.0)
        shadow_screen(L, casters, region=None, bbox=box, soft=2.6, density=dens, mag=1.0065, center=src)


def _dolls_fn(t, B, origin):
    D = lib.dolls()

    def fn(ctx, i, center, size, tt):
        if i == 1:
            _shadows(ctx, t, B, origin)
        pin, ang = _doll_xf(i, t, B)
        D[i].draw(ctx, pin, lib.K_DOLL, ang, paper=_paper_col(i))
    return fn


# ----------------------------------------------------------------------------- light
def _light_mask(f, t, B, aim, radius, level, origin):
    """MULTIPLY the frame by the room's light (1/4 res): a breath of ambient, the torch pool,
    the photographer's flash, the strobe through the blinds."""
    ds = 2 if _police(t) > 0.01 else 4          # the slatted strobe needs the finer mask
    w, h = max(1, f.pw // ds), max(1, f.ph // ds)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
    c = cairo.Context(surf)
    amb = 0.022
    c.set_source_rgb(amb * 0.9, amb * 0.95, amb * 1.2)
    c.paint()
    c.set_matrix(f.cam.matrix(f.scale * w / f.pw))
    c.set_operator(cairo.OPERATOR_ADD)
    if level > 0.003:
        ang = math.degrees(math.atan2(aim[1] - origin[1], aim[0] - origin[0]))
        dist = math.hypot(aim[0] - origin[0], aim[1] - origin[1])
        el = 1.0 + 0.30 * clamp(dist / (6 * radius))
        k = level
        c.save()
        c.translate(aim[0], aim[1])
        c.rotate(math.radians(ang))
        c.scale(el, 1.0)
        col = TORCH_COL
        draw.radial(c, (0, 0), 0, radius, [(0, mul(col, 1.08 * k), 1), (0.42, mul(col, 0.92 * k), 1),
                                            (0.72, mul(col, 0.38 * k), 1), (0.9, mul(col, 0.10 * k), 1),
                                            (1, (0, 0, 0), 1)])
        c.arc(0, 0, radius, 0, 2 * math.pi)
        c.fill()
        c.restore()
        # spill: the cone grazes the wall below the pool
        c.save()
        c.translate(aim[0], aim[1])
        c.rotate(math.radians(ang))
        c.scale(2.4, 1.0)
        draw.radial(c, (0, 0), 0, radius * 1.5, [(0, mul(col, 0.10 * k), 1), (1, (0, 0, 0), 1)])
        c.arc(0, 0, radius * 1.5, 0, 2 * math.pi)
        c.fill()
        c.restore()
    fl = _flash(t, B)
    if fl > 0.003:
        c.save()
        c.identity_matrix()
        c.set_source_rgb(*mul(FLASH_COL, 0.80 * fl))
        c.paint()
        c.restore()
        draw.radial(c, FLASH_AT, 0, 1900.0, [(0, mul(FLASH_COL, 0.45 * fl), 1), (1, (0, 0, 0), 1)])
        c.paint()
    pv = _police(t)
    if pv > 0.01:
        b, r = siren(t + 0.13, rate=1.6)
        x0, y0, x1, y1 = ROOM.blinds
        for col, v in ((BLUE, b), (RED, r)):
            if v <= 0.01:
                continue
            # the light bar is down in the street: slats thrown up the wall and fanning out,
            # fading with distance from the window
            y = y0 + 6.0
            while y < y1:
                yf = y0 + 300.0 + (y - y0) * 1.5
                draw.poly(c, [(x0 + 40, y), (x0 + 40, y + 10), (x0 - 1500, yf + 15), (x0 - 1500, yf)])
                y += 26.0
            draw.linear(c, (x0, 0), (x0 - 1300, 0), [(0, col, 0.85 * v * pv), (0.55, col, 0.35 * v * pv),
                                                    (1, col, 0.0)])
            c.fill()
    surf.flush()
    with f.screen() as S:
        S.set_operator(cairo.OPERATOR_MULTIPLY)
        pat = cairo.SurfacePattern(surf)
        pat.set_filter(cairo.FILTER_BILINEAR)
        pat.set_matrix(cairo.Matrix(xx=w / float(W), yy=h / float(H)))
        S.set_source(pat)
        S.paint()


def _beam(f, t, aim, radius, level, origin):
    """The torch beam through the dusty air (additive), and the pool's bloom."""
    if level <= 0.003:
        return
    ang = math.degrees(math.atan2(aim[1] - origin[1], aim[0] - origin[0]))
    length = math.hypot(aim[0] - origin[0], aim[1] - origin[1])
    spread = math.degrees(math.atan2(radius * 0.92, length))
    col = mix(HOT, (1, 1, 1), 0.2)
    with f.light(par=1.0, blur=12.0) as A:
        cone(A, origin, ang, spread, length, col, 0.16 * level, r0=12.0, falloff=0.97, soft_edge=0.5)
        glow(A, aim, radius * 0.75, col, 0.07 * level)
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    with f.light(par=1.0, blur=1.2) as A:
        for k in range(44):
            u = hash01(k, 1, 77)
            d = length * (0.22 + 0.74 * u)
            half = d * math.tan(math.radians(spread)) * 0.85
            off = (hash01(k, 2, 77) * 2 - 1) * half
            px = origin[0] + ux * d - uy * off + 16.0 * noise1(t * 0.25 + k * 1.3, 81)
            py = origin[1] + uy * d + ux * off + 16.0 * noise1(t * 0.21 + k * 1.7, 83) - 9.0 * t
            tw = 0.55 + 0.45 * math.sin(t * 2.6 + k * 2.1)
            draw.circle(A, (px, py), 1.1 + 1.5 * hash01(k, 4, 77))
            draw.fill(A, col, 0.30 * level * tw * (1.0 - 0.5 * u))


def _strobe_air(f, t):
    """The light bar's glow leaking through the blinds (additive)."""
    pv = _police(t)
    if pv <= 0.01:
        return
    b, r = siren(t + 0.13, rate=1.6)
    x0, y0, x1, y1 = ROOM.blinds
    with f.light(par=1.0, blur=5.0) as A:
        for col, v in ((BLUE, b), (RED, r)):
            if v <= 0.01:
                continue
            y = y0
            while y < y1:
                A.rectangle(x0, y + 10, x1 - x0, 5)
                y += 17
            draw.fill(A, col, 0.55 * v * pv)
            glow(A, (x0 + 60, (y0 + y1) * 0.5), 520.0, col, 0.10 * v * pv)


def _flash_air(f, t, B):
    fl = _flash(t, B)
    if fl <= 0.01:
        return
    with f.light(par=1.0, blur=30.0) as A:
        glow(A, FLASH_AT, 900.0, FLASH_COL, 0.55 * fl)
    f.post["exposure"] = 1.0 + 0.25 * fl


# ----------------------------------------------------------------------------- foreground
def _cop(c, t):
    """The cop's arm and torch coming into the frame bottom left (he stands behind the
    camera): sleeve, fist, the barrel pointing at the wall (its head is the beam's origin)."""
    hx, hy = _torch_hand(t)
    a = _aim(t)
    ang = math.atan2(a[1] - hy, a[0] - hx)
    ux, uy = math.cos(ang), math.sin(ang)
    fist = (hx - ux * 74.0, hy - uy * 74.0)
    el = (fist[0] - 150.0, fist[1] + 170.0)
    draw.capsule(c, (el[0] - 140.0, el[1] + 120.0), el, 70.0, 58.0)
    draw.capsule(c, el, fist, 56.0, 40.0)
    draw.circle(c, fist, 40.0)
    draw.capsule(c, fist, (hx - ux * 14.0, hy - uy * 14.0), 19.0, 24.0)
    draw.circle(c, (hx, hy), 28.0)
    draw.fill(c, INK)


def _photographer(c, t):
    """The press photographer, bottom right: fedora, his Speed Graphic up at his face, the
    round reflector of the flashgun above it (its bulb is FLASH_AT)."""
    sway = 6.0 * fbm1(t * 0.4, 19)
    head = (1052.0 + sway, 1512.0)
    draw.smooth(c, [(800.0, 2100.0), (850.0, 1650.0), (980.0, 1590.0), (1120.0, 1580.0), (1270.0, 1650.0),
                    (1300.0, 2100.0)], close=True)
    draw.ellipse(c, head, 60.0, 70.0, -0.1)
    # fedora: brim and pinched crown
    bx, by = head[0] + 2.0, head[1] - 44.0
    draw.ellipse(c, (bx, by), 112.0, 17.0, -0.08)
    draw.poly(c, [(bx - 62.0, by + 4.0), (bx - 54.0, by - 62.0), (bx - 8.0, by - 52.0), (bx + 10.0, by - 68.0),
                  (bx + 58.0, by - 58.0), (bx + 64.0, by + 2.0)])
    # the camera up in front of his face, elbows out; the flashgun's dish on its bracket
    draw.capsule(c, (1172.0 + sway, 1620.0), (1124.0 + sway, 1530.0), 40.0, 30.0)
    draw.capsule(c, (930.0 + sway, 1640.0), (962.0 + sway, 1540.0), 40.0, 30.0)
    draw.rect(c, 948.0 + sway, 1482.0, 1088.0 + sway, 1554.0)
    fx, fy = FLASH_AT
    draw.capsule(c, (fx + 40.0, fy + 72.0), (fx + 6.0, fy + 8.0), 8.0, 8.0)
    draw.circle(c, (fx, fy), 60.0)
    draw.fill(c, INK)


def _foreground(f, t):
    with f.layer(par=TORCH_PAR, blur=FG_BLUR) as L:
        _cop(L, t)
        _photographer(L, t)


# ----------------------------------------------------------------------------- the print
def _facade_print(f, t, B):
    """[window]: three frames of s01's Bass print. PAPER field, ink grid lines, the forty ink
    windows at the lock, and in each window its paper doll."""
    bass.bass_scene(f, field=PAPER, paper=0.8, vignette=0.14, flicker=0.0)
    u = (t - B["window"]) / GFX
    z = 1.0 + 0.035 * (1.0 - ease("out3", u))
    f.set_camera(Camera(540.0, 960.0, z))
    c = f.ctx
    for x in V_LINES:
        c.rectangle(x - 1.6, -40.0, 3.2, H + 80.0)
    for y in H_LINES:
        c.rectangle(-40.0, y - 1.6, W + 80.0, 3.2)
    c.set_source_rgb(*INK)
    c.fill()
    for i in range(1, 41):
        cx, cy = ROOM.center(i)
        pts = bass.cut_rect(cx - 48.0, cy - 60.0, cx + 48.0, cy + 60.0, seed=i * 7 + 1, amp=1.2)
        draw.poly(c, pts)
    c.set_source_rgb(*INK)
    c.fill()
    D = lib.dolls()
    for i in range(1, 41):
        pin, ang = _doll_xf(i, t, B)
        D[i].draw(c, pin, lib.K_DOLL, ang, paper=PAPER)


# ----------------------------------------------------------------------------- render
def render(f, t, T):
    B = _beats(T)
    if B["window"] <= t < B["window"] + GFX:
        _facade_print(f, t, B)
        return
    f.set_camera(camera(t))
    level = _torch_level(t)
    aim = _aim(t)
    radius = _radius(t)
    origin = _torch_origin(f, t)
    f.fill(INK)
    ROOM.draw(f, t, layer=None, dolls=_dolls_fn(t, B, origin), beam=None, ambient=1.0, flash=0.0,
              police=0.0, shadows=False, desk=True, blinds=True)
    _light_mask(f, t, B, aim, radius, level, origin)
    _beam(f, t, aim, radius, level, origin)
    _strobe_air(f, t)
    _flash_air(f, t, B)
    _foreground(f, t)
    f.post["vignette"] = 0.62
    f.post["bloom"] = 0.26


def motion_blur(t, T):
    return 3 if 6.45 <= t <= 7.75 else 1


def cues(T):
    B = _beats(T)
    w = B["window"]
    return [
        Cue(-0.5, "police light bar strobing outside, radio chatter muffled through the window", -4.0, 0.6, dur=3.2),
        Cue(-0.35, "draft through the open door: forty paper dolls rustle on their pins, left to right",
            -10.0, -0.3, dur=1.6),
        Cue(TORCH_ON, "torch switch click, the bulb stutters on", -2.0, -0.6),
        Cue(1.0, "torch beam sweeps (soft whoosh of the cop's coat, slow footstep on boards)", -14.0, -0.4, dur=3.0),
        Cue(w - 0.12, "press camera flashgun: the bulb fires (pop) and the flash whines as it recharges", 0.0, 0.5),
        Cue(w, "score: muted brass stab on the facade print", -3.0, 0.0),
        Cue(w + 0.25, "spent flashbulb ejected, tinkles on the floorboards", -12.0, 0.6),
        Cue(5.9, "the beam finds her: paper flutter, one pin creaks", -12.0, 0.1),
        Cue(6.0, "score: low strings swell under the push in", -6.0, 0.0, dur=3.6),
        Cue(9.3, "rain on glass fades up (s12 dissolve)", -12.0, 0.0, dur=1.3),
    ]
