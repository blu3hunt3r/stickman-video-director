"""Shared props - ONE design per object for the whole film (continuity).

White line art for ordinary objects; accents only where the story assigns them:
  AMBER   flames, bulbs, lamps, lit windows, embers      (light / clues)
  CRIMSON the red umbrella, red string, pins, crossings  (the killer / guilt)
  BLUE    badge, police light bars, police flashlights   (the law)
No text, numbers or logos on any prop (clocks use tick marks only).
Angles: degrees, screen convention (0 = +x right, 90 = down, -90 = up).
"""
import math

from .core import WHITE, AMBER, CRIMSON, BLUE, BLACK, fbm1, noise1, hash01, clamp, rad, siren as _siren
from . import draw


def _pt(c, ang, d):
    a = rad(ang)
    return (c[0] + math.cos(a) * d, c[1] + math.sin(a) * d)


def _xf(pts, c, ang=0.0, s=1.0, mirror=1):
    """Transform local points (x right, y down) by mirror, scale, rotation, translation."""
    a = rad(ang)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for x, y in pts:
        x, y = x * s * mirror, y * s
        out.append((c[0] + x * ca - y * sa, c[1] + x * sa + y * ca))
    return out


# ----------------------------------------------------------------------------- flame / match
def flame(f, base, size=1.0, t=0.0, seed=0, intensity=1.0, glow_r=None):
    """Amber teardrop flame rising from `base`. Returns the light center."""
    if intensity <= 0:
        return base
    fl = 0.85 + 0.15 * fbm1(t * 7.0, seed) + 0.08 * noise1(t * 23.0, seed + 3)
    h = 34 * size * fl * (0.6 + 0.4 * intensity)
    wd = 11 * size * (0.9 + 0.1 * noise1(t * 11, seed + 5))
    sway = 5 * size * fbm1(t * 3.1, seed + 9)
    pts = []
    n = 14
    for i in range(n + 1):
        u = i / n
        prof = math.sin(math.pi * min(1.0, u * 1.08)) ** 0.75 * (1 - u) ** 0.35
        pts.append((base[0] - wd * prof + sway * u * u, base[1] - h * u))
    for i in range(n, -1, -1):
        u = i / n
        prof = math.sin(math.pi * min(1.0, u * 1.08)) ** 0.75 * (1 - u) ** 0.35
        pts.append((base[0] + wd * prof + sway * u * u, base[1] - h * u))
    draw.fill(f, pts, AMBER, 0.92 * intensity, glow=1.0)
    core = [(base[0] + (p[0] - base[0]) * 0.45, base[1] + (p[1] - base[1]) * 0.5) for p in pts]
    draw.fill(f, core, WHITE, 0.85 * intensity)
    c = (base[0] + sway * 0.3, base[1] - h * 0.35)
    draw.glow_dot(f, c, (glow_r or 120) * size * (0.85 + 0.15 * fl), AMBER, 0.75 * intensity, core=False)
    return c


def match(f, base, angle=-90.0, length=52.0, s=1.0, lit=0.0, burnt=0.0, ember=0.0, flare=0.0,
          smoke_amt=0.0, t=0.0, seed=0, alpha=1.0):
    """A wooden match held at `base`, pointing along `angle` (deg). Returns tip position.
    lit: flame 0..1 · flare: ignition burst 0..1 · burnt: charred, curled tip · ember: glowing tip."""
    L = length * s
    tip = _pt(base, angle, L * (1 - 0.18 * burnt))
    if burnt > 0:
        mid = _pt(base, angle, L * 0.72)
        curl = _pt(mid, angle + 35 * burnt, L * 0.22)
        draw.stroke(f, [base, mid], 3.2 * s ** 0.5, WHITE, alpha)
        draw.stroke(f, [mid, curl], 3.0 * s ** 0.5, WHITE, alpha * (1 - 0.65 * burnt))
        tip = curl
    else:
        draw.line(f, base, tip, 3.2 * s ** 0.5, WHITE, alpha)
        draw.ellipse(f, tip, 5.2 * s, 4.0 * s, angle, 2.4, WHITE, alpha, fill_it=(lit <= 0))
    if ember > 0:
        draw.glow_dot(f, tip, 14 * s, AMBER, 0.9 * ember)
        draw.circle(f, tip, 3.2 * s, 1, AMBER, ember, fill_it=True, glow=0.8)
    if flare > 0:
        for k in range(9):
            a = hash01(seed, k) * 360
            d = (18 + 40 * hash01(seed, k, 1)) * s * flare
            p0 = _pt(tip, a, d * 0.4)
            p1 = _pt(tip, a, d)
            draw.line(f, p0, p1, 2.0, AMBER, flare * 0.9, glow=1.0)
        draw.glow_dot(f, tip, 200 * s * flare, AMBER, 0.95 * flare, core=False)
    light = tip
    if lit > 0:
        light = flame(f, tip, size=s * (1 + 0.6 * flare), t=t, seed=seed, intensity=lit)
    if smoke_amt > 0:
        from .fx import smoke
        smoke(f, tip[0], tip[1] - 4, t, seed=seed + 1, height=150 * s, alpha=0.4 * smoke_amt, w=1.8)
    return tip if lit <= 0 else light


def matchbook(f, c, angle=0.0, s=1.0, open_=1.0, n=10, missing=(), alpha=1.0, highlight=None):
    """Open cardboard matchbook seen from the front. `missing`: indices (0 = leftmost) of
    matches already torn out - they leave short stubs. `highlight`: indices tinted amber."""
    W_, H_ = 170.0, 92.0
    body = _xf([(-W_ / 2, 0), (W_ / 2, 0), (W_ / 2, H_), (-W_ / 2, H_)], c, angle, s)
    draw.stroke(f, body, 3.0, WHITE, alpha, closed=True)
    strip = _xf([(-W_ / 2 + 8, H_ - 18), (W_ / 2 - 8, H_ - 18)], c, angle, s)
    draw.line(f, strip[0], strip[1], 2.0, WHITE, alpha * 0.8)
    for i in range(12):
        x = -W_ / 2 + 12 + i * (W_ - 24) / 11
        a, b = _xf([(x, H_ - 14), (x + 6, H_ - 6)], c, angle, s)
        draw.line(f, a, b, 1.6, WHITE, alpha * 0.7)
    for i in range(n):
        x = -W_ / 2 + 14 + i * (W_ - 28) / (n - 1)
        top = -60.0 * open_
        if i in missing:
            a, b = _xf([(x, 0), (x, -8)], c, angle, s)
            draw.line(f, a, b, 3.0, WHITE, alpha * 0.8)
            continue
        col = AMBER if (highlight and i in highlight) else WHITE
        a, b = _xf([(x, 0), (x, top)], c, angle, s)
        draw.line(f, a, b, 3.0, col, alpha)
        draw.ellipse(f, b, 5.5 * s, 7.0 * s, angle, 2.0, col, alpha, fill_it=True)
    if open_ < 1.0:
        cov = _xf([(-W_ / 2, 0), (W_ / 2, 0), (W_ / 2, -70 * (1 - open_)), (-W_ / 2, -70 * (1 - open_))], c, angle, s)
        draw.stroke(f, cov, 3.0, WHITE, alpha, closed=True)
    else:
        cov = _xf([(-W_ / 2, H_), (W_ / 2, H_), (W_ / 2 - 6, H_ + 26), (-W_ / 2 + 6, H_ + 26)], c, angle, s)
        draw.stroke(f, cov, 2.6, WHITE, alpha * 0.85, closed=True)


# ----------------------------------------------------------------------------- umbrellas
def umbrella(f, hand, angle=-90.0, R=120.0, open_=1.0, color=WHITE, fill_alpha=None,
             alpha=1.0, wobble=0.0, t=0.0, seed=0, handle=True):
    """Side-view umbrella held at `hand`. The shaft points from the hand along `angle`
    (default straight up); the canopy domes over the far end. color=CRIMSON for THE red
    umbrella (filled canopy). open_=0 gives a furled umbrella. Returns the canopy apex."""
    shaft_len = R * (1.22 if open_ > 0.3 else 1.55)
    apex = _pt(hand, angle, shaft_len)
    axis = rad(angle)
    ux, uy = math.cos(axis), math.sin(axis)          # along shaft, toward apex
    px, py = -uy, ux                                 # perpendicular
    half = R * (0.10 + 0.90 * open_)
    depth = R * (0.50 * open_ + 1.05 * (1 - open_))  # apex-to-rim distance
    wob = wobble * 0.06 * R * fbm1(t * 2.0, seed)
    rc = (apex[0] - ux * depth, apex[1] - uy * depth)   # rim center (toward the hand)

    def at(k, h):  # k: -1..1 across, h: height above rim (toward apex)
        return (rc[0] + px * (half * k + wob * k) + ux * h, rc[1] + py * (half * k + wob * k) + uy * h)
    dome = [at(-1 + 2 * i / 24, depth * (1 - (-1 + 2 * i / 24) ** 2) ** 0.55) for i in range(25)]
    ribs = 6
    tips = [at(-1 + 2 * i / ribs, -0.06 * depth * abs(-1 + 2 * i / ribs)) for i in range(ribs + 1)]
    edge = []
    for i in range(ribs):
        a, b = tips[i], tips[i + 1]
        m = ((a[0] + b[0]) / 2 + ux * depth * 0.10, (a[1] + b[1]) / 2 + uy * depth * 0.10)
        edge += draw.bezier_pts(a, m, m, b, 6)[:-1]
    edge.append(tips[-1])
    outline = dome + edge[::-1]
    filled = color is not WHITE or fill_alpha is not None
    if filled:
        draw.fill(f, outline, color, alpha * (fill_alpha if fill_alpha is not None else 0.92), glow=0.3)
    draw.stroke(f, outline, 3.0, color, alpha, closed=True)
    rib_col = BLACK if filled else color
    for tp in tips[1:-1]:
        draw.line(f, apex, tp, 2.0, rib_col, alpha * (0.6 if filled else 0.75))
    draw.line(f, hand, _pt(apex, angle, R * 0.12), 3.0, WHITE, alpha)
    if handle:
        ang_p = math.degrees(math.atan2(py, px))
        c = (hand[0] + px * 11, hand[1] + py * 11)
        draw.arc(f, c, 11, ang_p + 180, ang_p + 360, 3.0, WHITE, alpha)
    return apex


def umbrella_top(f, c, R=60.0, rot=0.0, color=WHITE, fill_alpha=None, alpha=1.0, ribs=8):
    """Umbrella seen from directly above: scalloped octagon with ribs."""
    tips = [_pt(c, rot + 360 * i / ribs, R) for i in range(ribs)]
    edge = []
    for i in range(ribs):
        a, b = tips[i], tips[(i + 1) % ribs]
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        inward = ((c[0] - m[0]) * 0.10, (c[1] - m[1]) * 0.10)
        mm = (m[0] + inward[0], m[1] + inward[1])
        edge += draw.bezier_pts(a, mm, mm, b, 5)[:-1]
    filled = color is not WHITE or fill_alpha is not None
    if filled:
        draw.fill(f, edge, color, alpha * (fill_alpha if fill_alpha is not None else 0.92), glow=0.45)
    draw.stroke(f, edge, 2.6, color, alpha, closed=True)
    for tp in tips:
        draw.line(f, c, tp, 1.8, BLACK if filled else color, alpha * 0.7)
    draw.circle(f, c, 3.0, 1, BLACK if filled else color, alpha, fill_it=True)


# ----------------------------------------------------------------------------- time
def clock_face(f, c, r, hour, minute, w=3.0, color=WHITE, alpha=1.0, style="pocket", second=None,
               glow=0.0, chain=None, tick_alpha=1.0):
    """Clock / watch face with tick marks only (no numerals).
    style: 'pocket' (crown + bow on top), 'wall' (double rim), 'tower' (heavy rim), 'dash'."""
    draw.circle(f, c, r, w, color, alpha, glow=glow)
    if style == "wall":
        draw.circle(f, c, r * 1.12, w * 0.8, color, alpha * 0.8)
    if style == "tower":
        draw.circle(f, c, r * 1.15, w * 1.4, color, alpha)
    if style == "pocket":
        top = (c[0], c[1] - r)
        draw.rect(f, top[0] - r * 0.09, top[1] - r * 0.2, r * 0.18, r * 0.2, w * 0.7, color, alpha)
        draw.circle(f, (top[0], top[1] - r * 0.34), r * 0.14, w * 0.7, color, alpha)
        if chain:
            draw.stroke(f, draw.bezier_pts((top[0], top[1] - r * 0.48), chain[0], chain[1], chain[2], 20),
                        w * 0.6, color, alpha * 0.8, dash=(6, 6))
    for i in range(60 if style in ("wall", "tower") else 12):
        if style in ("wall", "tower") and i % 5:
            a = i * 6 - 90
            draw.line(f, _pt(c, a, r * 0.9), _pt(c, a, r * 0.95), w * 0.4, color, alpha * 0.6 * tick_alpha)
            continue
        k = i // 5 if style in ("wall", "tower") else i
        a = k * 30 - 90
        long = k % 3 == 0
        draw.line(f, _pt(c, a, r * (0.74 if long else 0.82)), _pt(c, a, r * 0.92), w * (0.9 if long else 0.6),
                  color, alpha * tick_alpha)
    ma = (minute % 60) / 60 * 360 - 90
    ha = ((hour % 12) + (minute % 60) / 60) / 12 * 360 - 90
    draw.line(f, c, _pt(c, ha, r * 0.48), w * 1.3, color, alpha)
    draw.line(f, c, _pt(c, ma, r * 0.76), w * 0.85, color, alpha)
    if second is not None:
        sa = (second % 60) / 60 * 360 - 90
        draw.line(f, _pt(c, sa + 180, r * 0.15), _pt(c, sa, r * 0.82), w * 0.45, color, alpha)
    draw.circle(f, c, w * 1.1, 1, color, alpha, fill_it=True)


THREE_OH_SEVEN = (3, 7)


# ----------------------------------------------------------------------------- lights
def bulb(f, anchor, cord_len=260.0, swing=0.0, on=1.0, s=1.0, t=0.0, seed=0, glow_r=300.0):
    """Bare hanging bulb on a cord from `anchor` (ceiling). swing: degrees from vertical.
    Returns the bulb center (use it for Light.cone / Light.radial)."""
    a = 90 - swing
    end = _pt(anchor, a, cord_len)
    draw.line(f, anchor, end, 2.2, WHITE, 1.0)
    ax = rad(a)
    ux, uy = math.cos(ax), math.sin(ax)
    px, py = -uy, ux
    sock = [(end[0] + px * 9 * s, end[1] + py * 9 * s), (end[0] - px * 9 * s, end[1] - py * 9 * s),
            (end[0] - px * 9 * s + ux * 22 * s, end[1] - py * 9 * s + uy * 22 * s),
            (end[0] + px * 9 * s + ux * 22 * s, end[1] + py * 9 * s + uy * 22 * s)]
    draw.stroke(f, sock, 2.4, WHITE, 1.0, closed=True)
    bc = (end[0] + ux * 46 * s, end[1] + uy * 46 * s)
    if on > 0:
        draw.circle(f, bc, 24 * s, 1, AMBER, 0.35 * on, fill_it=True, glow=1.0)
    draw.circle(f, bc, 24 * s, 2.4, WHITE if on < 0.5 else AMBER, 1.0, glow=0.6 * on)
    fil = [(bc[0] - px * 8 * s - ux * 4 * s, bc[1] - py * 8 * s - uy * 4 * s)]
    for k in range(5):
        fil.append((bc[0] + px * (-6 + 3 * k) * s + ux * (4 if k % 2 else -2) * s,
                    bc[1] + py * (-6 + 3 * k) * s + uy * (4 if k % 2 else -2) * s))
    draw.stroke(f, fil, 1.8, AMBER if on > 0 else WHITE, 1.0, glow=1.2 * on)
    if on > 0:
        draw.glow_dot(f, bc, glow_r * s, AMBER, 0.85 * on, core=False)
    return bc


def streetlamp(f, base, height=880.0, s=1.0, on=1.0, facing=1, t=0.0, seed=0, alpha=1.0, glow_r=260.0):
    """Cast-iron noir streetlamp standing on `base` (ground point). Returns the lamp light point."""
    x, y = base
    top = (x, y - height * s)
    draw.line(f, (x, y), top, 4.0, WHITE, alpha)
    draw.stroke(f, [(x - 22 * s, y), (x - 14 * s, y - 40 * s), (x + 14 * s, y - 40 * s), (x + 22 * s, y)],
                3.0, WHITE, alpha)
    draw.line(f, (x - 12 * s, y - 90 * s), (x + 12 * s, y - 90 * s), 3.0, WHITE, alpha)
    arm_end = (x + facing * 120 * s, top[1] + 26 * s)
    draw.bezier(f, top, (x, top[1] - 34 * s), (x + facing * 80 * s, top[1] - 40 * s), arm_end, 3.6, WHITE, alpha)
    shade = [(arm_end[0] - 34 * s, arm_end[1] + 30 * s), (arm_end[0] - 12 * s, arm_end[1]),
             (arm_end[0] + 12 * s, arm_end[1]), (arm_end[0] + 34 * s, arm_end[1] + 30 * s)]
    draw.stroke(f, shade, 3.0, WHITE, alpha, closed=True)
    lp = (arm_end[0], arm_end[1] + 36 * s)
    if on > 0:
        fl = on * (0.92 + 0.08 * fbm1(t * 5, seed))
        draw.ellipse(f, lp, 20 * s, 9 * s, 0, 1, AMBER, 0.9 * fl, fill_it=True, glow=1.2)
        draw.glow_dot(f, lp, glow_r * s, AMBER, 0.8 * fl, core=False)
    return lp


# ----------------------------------------------------------------------------- city
def building(f, x, ground_y, w, h, seed=0, lit=0.16, t=0.0, alpha=1.0, lw=3.0, roof="flat",
             win_w=None, cols=None, rows=None, window_alpha=0.45, lit_override=None):
    """Line-art tower: outline, window grid, some amber-lit windows (deterministic).
    lit_override: dict {(col,row): 0..1} forcing particular windows on/off."""
    top = ground_y - h
    draw.rect(f, x, top, w, h, lw, WHITE, alpha)
    cols = cols or max(2, int(w / 70))
    rows = rows or max(3, int(h / 92))
    mx, my = w * 0.12, 60.0
    cw = (w - 2 * mx) / cols
    rh = (h - my - 40) / rows
    ww = win_w or cw * 0.48
    wh = rh * 0.52
    for ci in range(cols):
        for ri in range(rows):
            wx = x + mx + ci * cw + (cw - ww) / 2
            wy = top + my + ri * rh
            on = hash01(seed, ci, ri) < lit
            if on:
                per = 6 + 10 * hash01(seed, ci, ri, 3)
                on = ((t + per * hash01(seed, ci, ri, 4)) % per) > per * 0.08
            lv = 1.0 if on else 0.0
            if lit_override and (ci, ri) in lit_override:
                lv = lit_override[(ci, ri)]
            if lv > 0:
                draw.rect(f, wx, wy, ww, wh, 1, AMBER, alpha * 0.85 * lv, fill_it=True, glow=0.9 * lv)
            else:
                draw.rect(f, wx, wy, ww, wh, lw * 0.5, WHITE, alpha * window_alpha)
    if roof == "water":
        tx = x + w * 0.62
        draw.rect(f, tx, top - 90, 70, 60, lw * 0.8, WHITE, alpha)
        draw.stroke(f, [(tx + 35, top - 120), (tx - 4, top - 90), (tx + 74, top - 90)], lw * 0.8, WHITE, alpha, closed=True)
        for k in (8, 35, 62):
            draw.line(f, (tx + k, top - 30), (tx + k, top), lw * 0.6, WHITE, alpha)
    elif roof == "tower":
        draw.rect(f, x + w * 0.2, top - 120, w * 0.6, 120, lw, WHITE, alpha)
        draw.rect(f, x + w * 0.35, top - 220, w * 0.3, 100, lw, WHITE, alpha)
        draw.line(f, (x + w * 0.5, top - 220), (x + w * 0.5, top - 330), lw * 0.7, WHITE, alpha)
    elif roof == "antenna":
        draw.line(f, (x + w * 0.3, top), (x + w * 0.3, top - 140), lw * 0.7, WHITE, alpha)
        draw.line(f, (x + w * 0.3 - 20, top - 100), (x + w * 0.3 + 20, top - 100), lw * 0.6, WHITE, alpha)
    return (x, top, w, h)


def car_side(f, x, ground_y, s=1.0, facing=1, police=False, t=0.0, wheel_turn=0.0, headlights=0.0,
             door_open=0.0, alpha=1.0, siren_on=1.0, brake=0.0):
    """1940s sedan in profile. x = center of the car. Returns dict of anchor points
    (driver_window, door_hinge, roof, headlight, seat)."""
    m = facing
    L = [(-260, -40), (-250, -75), (-200, -88), (-150, -95), (-112, -160), (-40, -178), (60, -176),
         (118, -150), (150, -104), (230, -96), (262, -78), (268, -42), (250, -30), (-250, -30)]
    body = _xf(L, (x, ground_y - 36 * s), 0, s, m)
    draw.stroke(f, body, 3.4, WHITE, alpha, closed=True)
    win1 = _xf([(-100, -150), (-36, -168), (-36, -104), (-118, -104)], (x, ground_y - 36 * s), 0, s, m)
    win2 = _xf([(-24, -168), (54, -166), (104, -112), (-24, -104)], (x, ground_y - 36 * s), 0, s, m)
    draw.stroke(f, win1, 2.6, WHITE, alpha, closed=True)
    draw.stroke(f, win2, 2.6, WHITE, alpha, closed=True)
    d0 = _xf([(-30, -104), (-30, -36)], (x, ground_y - 36 * s), 0, s, m)
    d1 = _xf([(92, -104), (96, -40)], (x, ground_y - 36 * s), 0, s, m)
    if door_open > 0:
        hinge = _xf([(96, -104)], (x, ground_y - 36 * s), 0, s, m)[0]
        dw = 126 * s * (1 - 0.65 * door_open)
        door = [(hinge[0] - m * 0 * s, hinge[1]), (hinge[0] + m * dw * 0.15, hinge[1] - 2),
                (hinge[0] + m * dw * 0.15, hinge[1] + 64 * s), (hinge[0], hinge[1] + 64 * s)]
        draw.stroke(f, [hinge, (hinge[0] + m * dw * 0.9, hinge[1] - 8 * s), (hinge[0] + m * dw * 0.9, hinge[1] + 60 * s),
                        (hinge[0], hinge[1] + 66 * s)], 3.0, WHITE, alpha, closed=True)
    draw.line(f, d0[0], d0[1], 2.2, WHITE, alpha * 0.8)
    draw.line(f, d1[0], d1[1], 2.2, WHITE, alpha * 0.8)
    hnd = _xf([(14, -88), (34, -88)], (x, ground_y - 36 * s), 0, s, m)
    draw.line(f, hnd[0], hnd[1], 3.0, WHITE, alpha)
    bump_f = _xf([(250, -30), (280, -30)], (x, ground_y - 36 * s), 0, s, m)
    bump_r = _xf([(-250, -30), (-276, -30)], (x, ground_y - 36 * s), 0, s, m)
    draw.line(f, bump_f[0], bump_f[1], 4.0, WHITE, alpha)
    draw.line(f, bump_r[0], bump_r[1], 4.0, WHITE, alpha)
    hl = _xf([(254, -70)], (x, ground_y - 36 * s), 0, s, m)[0]
    draw.circle(f, hl, 11 * s, 2.4, AMBER if headlights > 0 else WHITE, alpha, glow=0.8 * headlights)
    if headlights > 0:
        draw.glow_dot(f, hl, 90 * s, AMBER, 0.8 * headlights, core=False)
    tl = _xf([(-252, -64)], (x, ground_y - 36 * s), 0, s, m)[0]
    if brake > 0:
        draw.circle(f, tl, 8 * s, 1, CRIMSON, brake, fill_it=True, glow=0.8 * brake)
    else:
        draw.circle(f, tl, 7 * s, 2.0, WHITE, alpha)
    for wxl in (-170, 168):
        wc = _xf([(wxl, 0)], (x, ground_y - 36 * s), 0, s, m)[0]
        arc_pts = _xf([(wxl - 58 + 116 * i / 12, -36 - 34 * math.sin(math.pi * i / 12)) for i in range(13)],
                      (x, ground_y - 36 * s), 0, s, m)
        draw.stroke(f, arc_pts, 3.0, WHITE, alpha)
        draw.circle(f, wc, 36 * s, 3.4, WHITE, alpha)
        draw.circle(f, wc, 16 * s, 2.2, WHITE, alpha)
        for k in range(4):
            a = math.degrees(wheel_turn) + k * 90
            draw.line(f, _pt(wc, a, 5 * s), _pt(wc, a, 15 * s), 1.6, WHITE, alpha * 0.8)
    out = dict(
        driver_window=_xf([(-60, -136)], (x, ground_y - 36 * s), 0, s, m)[0],
        seat=_xf([(-40, -90)], (x, ground_y - 36 * s), 0, s, m)[0],
        door_hinge=_xf([(96, -104)], (x, ground_y - 36 * s), 0, s, m)[0],
        roof=_xf([(0, -178)], (x, ground_y - 36 * s), 0, s, m)[0],
        headlight=hl,
    )
    if police:
        r = out["roof"]
        bar = [(r[0] - 46 * s, r[1] - 2), (r[0] + 46 * s, r[1] - 2), (r[0] + 40 * s, r[1] - 20 * s), (r[0] - 40 * s, r[1] - 20 * s)]
        draw.stroke(f, bar, 2.4, WHITE, alpha, closed=True)
        b, rr = _siren(t)
        b *= siren_on
        rr *= siren_on
        lb, lr = (r[0] - 22 * s * m, r[1] - 11 * s), (r[0] + 22 * s * m, r[1] - 11 * s)
        draw.circle(f, lb, 9 * s, 1, BLUE, 0.35 + 0.65 * b, fill_it=True, glow=1.4 * b)
        draw.circle(f, lr, 9 * s, 1, CRIMSON, 0.35 + 0.65 * rr, fill_it=True, glow=1.4 * rr)
        if b > 0:
            draw.glow_dot(f, lb, 300 * s, BLUE, 0.9 * b, core=False)
        if rr > 0:
            draw.glow_dot(f, lr, 300 * s, CRIMSON, 0.8 * rr, core=False)
    return out


def car_top(f, c, angle=0.0, s=1.0, police=False, t=0.0, alpha=1.0, headlights=0.0, siren_on=1.0):
    """Sedan seen from above, nose pointing along `angle` (0 = right)."""
    body = _xf([(-250, -88), (190, -92), (250, -60), (262, 0), (250, 60), (190, 92), (-250, 88), (-266, 0)], c, angle, s)
    draw.stroke(f, body, 3.2, WHITE, alpha, closed=True)
    roof = _xf([(-120, -70), (70, -70), (110, 0), (70, 70), (-120, 70), (-150, 0)], c, angle, s)
    draw.stroke(f, roof, 2.6, WHITE, alpha, closed=True)
    ws = _xf([(70, -70), (130, -80), (150, 0), (130, 80), (70, 70)], c, angle, s)
    draw.stroke(f, ws, 2.0, WHITE, alpha * 0.8)
    rw = _xf([(-120, -70), (-170, -78), (-190, 0), (-170, 78), (-120, 70)], c, angle, s)
    draw.stroke(f, rw, 2.0, WHITE, alpha * 0.8)
    if headlights > 0:
        for side in (-1, 1):
            hp = _xf([(256, side * 52)], c, angle, s)[0]
            draw.glow_dot(f, hp, 44 * s, AMBER, 0.7 * headlights)
    if police:
        b, rr = _siren(t)
        lb, lr = _xf([(-20, -34), (-20, 34)], c, angle, s)
        draw.circle(f, lb, 12 * s, 1, BLUE, (0.35 + 0.65 * b * siren_on) * alpha, fill_it=True, glow=1.4 * b * siren_on)
        draw.circle(f, lr, 12 * s, 1, CRIMSON, (0.35 + 0.65 * rr * siren_on) * alpha, fill_it=True, glow=1.4 * rr * siren_on)
        if b * siren_on > 0:
            draw.glow_dot(f, lb, 320 * s, BLUE, 0.5 * b * siren_on, core=False)
        if rr * siren_on > 0:
            draw.glow_dot(f, lr, 320 * s, CRIMSON, 0.4 * rr * siren_on, core=False)


# ----------------------------------------------------------------------------- interiors
def blinds(f, x, y, w, h, slats=13, tilt=0.55, alpha=1.0, frame=True):
    """Venetian-blind window. tilt 0 = closed flat slats, 1 = open (thin slats)."""
    if frame:
        draw.rect(f, x - 10, y - 10, w + 20, h + 20, 3.4, WHITE, alpha)
        draw.line(f, (x - 18, y + h + 10), (x + w + 18, y + h + 10), 3.4, WHITE, alpha)
    gap = h / slats
    th = gap * (0.85 - 0.6 * tilt)
    for i in range(slats):
        yy = y + i * gap
        draw.rect(f, x, yy, w, th, 2.0, WHITE, alpha * 0.9)
    for cx in (x + w * 0.2, x + w * 0.8):
        draw.line(f, (cx, y), (cx, y + h), 1.2, WHITE, alpha * 0.5)


def blind_light(f, quad, n=9, duty=0.5, color=AMBER, alpha=0.22, glow=0.5, offset=0.0):
    """Stripes of light thrown through blinds onto a surface. quad = 4 corners
    (top-left, top-right, bottom-right, bottom-left) of the lit patch; stripes run
    from the left edge to the right edge. offset (0..1) slides the stripes."""
    tl, tr, br, bl = quad
    for i in range(n):
        a0 = (i + offset) / n
        a1 = (i + offset + duty) / n
        if a0 >= 1:
            continue
        a1 = min(a1, 1.0)
        p0 = (tl[0] + (bl[0] - tl[0]) * a0, tl[1] + (bl[1] - tl[1]) * a0)
        p1 = (tr[0] + (br[0] - tr[0]) * a0, tr[1] + (br[1] - tr[1]) * a0)
        p2 = (tr[0] + (br[0] - tr[0]) * a1, tr[1] + (br[1] - tr[1]) * a1)
        p3 = (tl[0] + (bl[0] - tl[0]) * a1, tl[1] + (bl[1] - tl[1]) * a1)
        draw.fill(f, [p0, p1, p2, p3], color, alpha, glow=glow)


def footprint(f, c, angle=-90.0, side="l", s=1.0, alpha=1.0, w=2.4, color=WHITE, wet=0.0):
    """Shoe print (sole + heel) pointing along `angle` (walking direction)."""
    lat = -8 if side == "l" else 8
    sole_c = _xf([(lat * 0.3, -14)], c, angle + 90, s)[0]
    heel_c = _xf([(lat * 0.1, 22)], c, angle + 90, s)[0]
    draw.ellipse(f, sole_c, 13 * s, 22 * s, angle + 90, w, color, alpha)
    draw.ellipse(f, heel_c, 11 * s, 11 * s, angle + 90, w, color, alpha)
    if wet > 0:
        draw.ellipse(f, sole_c, 15 * s * (1 + wet * 0.3), 25 * s * (1 + wet * 0.3), angle + 90, 1.2, color, alpha * 0.4 * wet)


def pin(f, c, color=CRIMSON, s=1.0, alpha=1.0):
    draw.circle(f, c, 9 * s, 1, color, alpha, fill_it=True, glow=0.5)
    draw.circle(f, (c[0] - 3 * s, c[1] - 3 * s), 2.6 * s, 1, WHITE, alpha * 0.9, fill_it=True)


def photo_card(f, c, w=120.0, h=150.0, angle=0.0, s=1.0, alpha=1.0, crossed=0.0, pinned=True):
    """Polaroid-style photo of a faceless figure (hollow circle head + shoulders). No text.
    crossed 0..1 draws a crimson X across it (a victim)."""
    W_, H_ = w * s, h * s
    corners = _xf([(-W_ / 2, -H_ / 2), (W_ / 2, -H_ / 2), (W_ / 2, H_ / 2), (-W_ / 2, H_ / 2)], c, angle, 1)
    draw.stroke(f, corners, 2.6, WHITE, alpha, closed=True)
    inner = _xf([(-W_ / 2 + 9 * s, -H_ / 2 + 9 * s), (W_ / 2 - 9 * s, -H_ / 2 + 9 * s),
                 (W_ / 2 - 9 * s, H_ / 2 - 30 * s), (-W_ / 2 + 9 * s, H_ / 2 - 30 * s)], c, angle, 1)
    draw.stroke(f, inner, 1.6, WHITE, alpha * 0.7, closed=True)
    hc = _xf([(0, -H_ * 0.12)], c, angle, 1)[0]
    draw.circle(f, hc, W_ * 0.17, 2.4, WHITE, alpha)
    sh = _xf([(-W_ * 0.28, H_ * 0.22), (0, H_ * 0.06), (W_ * 0.28, H_ * 0.22)], c, angle, 1)
    draw.stroke(f, [sh[0], sh[1], sh[2]], 2.4, WHITE, alpha)
    nk = _xf([(0, -H_ * 0.12 + W_ * 0.17), (0, H_ * 0.06)], c, angle, 1)
    draw.line(f, nk[0], nk[1], 2.4, WHITE, alpha)
    if crossed > 0:
        a = _xf([(-W_ * 0.36, -H_ * 0.38), (W_ * 0.36, H_ * 0.22)], c, angle, 1)
        b = _xf([(W_ * 0.36, -H_ * 0.38), (-W_ * 0.36, H_ * 0.22)], c, angle, 1)
        k1 = clamp(crossed * 2)
        k2 = clamp(crossed * 2 - 1)
        draw.line(f, a[0], (a[0][0] + (a[1][0] - a[0][0]) * k1, a[0][1] + (a[1][1] - a[0][1]) * k1), 5, CRIMSON, alpha, glow=0.6)
        if k2 > 0:
            draw.line(f, b[0], (b[0][0] + (b[1][0] - b[0][0]) * k2, b[0][1] + (b[1][1] - b[0][1]) * k2), 5, CRIMSON, alpha, glow=0.6)
    if pinned:
        pin(f, _xf([(0, -H_ / 2 + 6 * s)], c, angle, 1)[0], s=s, alpha=alpha)


def red_string(f, pts, sag=0.05, w=2.6, alpha=1.0, t=0.0, vib=0.0, grow=1.0):
    """Crimson string stretched between successive points with gravity sag.
    grow 0..1 reveals it progressively along its length (being pulled taut)."""
    path = []
    for (a, b) in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        for i in range(13):
            u = i / 12
            yy = a[1] + (b[1] - a[1]) * u + sag * d * 4 * u * (1 - u)
            xx = a[0] + (b[0] - a[0]) * u
            if vib:
                yy += vib * 6 * math.sin(u * math.pi) * math.sin(t * 40)
            path.append((xx, yy))
    if grow < 1.0:
        n = max(2, int(len(path) * clamp(grow)))
        path = path[:n]
    draw.stroke(f, path, w, CRIMSON, alpha, glow=0.7)


def board(f, x, y, w, h, alpha=1.0):
    """Evidence (cork) board: double frame, nothing written on it."""
    draw.rect(f, x, y, w, h, 3.6, WHITE, alpha)
    draw.rect(f, x + 14, y + 14, w - 28, h - 28, 1.6, WHITE, alpha * 0.55)


def badge(f, c, s=1.0, angle=0.0, alpha=1.0, glint=0.0):
    """Police badge: blue shield with a six-point star (icon only)."""
    sh = _xf([(0, -46), (34, -30), (30, 16), (0, 48), (-30, 16), (-34, -30)], c, angle, s)
    draw.fill(f, sh, BLUE, alpha * 0.85, glow=0.6)
    draw.stroke(f, sh, 2.6, WHITE, alpha, closed=True)
    star = []
    for i in range(12):
        r = 22 if i % 2 == 0 else 11
        star.append(_xf([(r * math.cos(rad(i * 30 - 90)), r * math.sin(rad(i * 30 - 90)) + 2)], c, angle, s)[0])
    draw.stroke(f, star, 2.2, WHITE, alpha, closed=True)
    if glint > 0:
        a, b = _xf([(-26, -20), (20, 26)], c, angle, s)
        draw.line(f, a, b, 4, WHITE, glint, glow=1.2)


def magnifier(f, c, r=90.0, angle=45.0, alpha=1.0, w=4.0):
    """Magnifying glass: lens ring + handle toward `angle`. Returns lens (center, radius)."""
    draw.circle(f, c, r, w, WHITE, alpha)
    draw.circle(f, c, r * 0.9, w * 0.4, WHITE, alpha * 0.5)
    h0 = _pt(c, angle, r)
    h1 = _pt(c, angle, r * 2.3)
    draw.line(f, h0, _pt(c, angle, r * 1.2), w * 1.2, WHITE, alpha)
    draw.line(f, _pt(c, angle, r * 1.2), h1, w * 2.2, WHITE, alpha)
    return c, r * 0.9


def mirror(f, c, r=70.0, alpha=1.0, glint=0.0):
    draw.circle(f, c, r, 4.0, WHITE, alpha)
    draw.circle(f, c, r * 1.12, 2.0, WHITE, alpha * 0.7)
    if glint > 0:
        draw.line(f, (c[0] - r * 0.5, c[1] - r * 0.2), (c[0] - r * 0.15, c[1] - r * 0.55), 3, WHITE, glint, glow=1.0)
        draw.line(f, (c[0] - r * 0.3, c[1] + 0.05 * r), (c[0] + 0.05 * r, c[1] - r * 0.3), 2, WHITE, glint * 0.7, glow=0.6)


def revolver(f, hand, angle=0.0, s=1.0, alpha=1.0, flash=0.0, seed=0):
    """Snub revolver silhouette held at `hand`, barrel along `angle`. flash 0..1 = muzzle flash."""
    pts = _xf([(0, 0), (8, -30), (60, -30), (64, -40), (102, -40), (102, -28), (40, -22), (26, 8), (6, 12)], hand, angle, s)
    draw.stroke(f, pts, 3.0, WHITE, alpha, closed=True)
    draw.circle(f, _xf([(44, -30)], hand, angle, s)[0], 9 * s, 2.0, WHITE, alpha)
    if flash > 0:
        m = _xf([(110, -34)], hand, angle, s)[0]
        for k in range(10):
            a = angle + (hash01(seed, k) - 0.5) * 70
            d = (40 + 80 * hash01(seed, k, 1)) * s * flash
            draw.line(f, m, _pt(m, a, d), 3.0, AMBER, flash, glow=1.4)
        draw.glow_dot(f, m, 220 * s * flash, AMBER, 0.9 * flash)


def gavel(f, c, angle=0.0, s=1.0, alpha=1.0):
    head = _xf([(-40, -20), (40, -20), (40, 20), (-40, 20)], c, angle, s)
    draw.stroke(f, head, 3.0, WHITE, alpha, closed=True)
    for k in (-26, 26):
        a, b = _xf([(k, -20), (k, 20)], c, angle, s)
        draw.line(f, a, b, 2.0, WHITE, alpha * 0.8)
    a, b = _xf([(0, 20), (0, 150)], c, angle, s)
    draw.line(f, a, b, 4.0, WHITE, alpha)
