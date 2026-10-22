"""SALVAGE sets - A. sea surface, night/dusk sky, moon and the waterline split.

The surface world is drawn as an Inside-style CROSS-SECTION: above y = 0 is air, below it
is the water volume seen in section, so the boat sits on a wavy waterline and the diver
hangs in aqua light beneath it. The far sea is drawn in perspective between the horizon
and the near waterline:

    camera above water : horizon at eye level (screen y = 960), far sea between the
                         horizon and the near waterline, section water below.
    camera below water : the horizon sits ON the near waterline (the far sea collapses),
                         so a camera rising through the surface is continuous.

Typical split shot (S02, S14, S15):

    info = sea_world(f, t, moon=(760, 820), dusk=0.3)      # sky, moon, far sea, water
    with f.light(blur=14) as A: ...                         # god rays (engine/atmos)
    with f.layer() as L:
        boat.draw(L, t, pump_angle=..)                      # boat crossing the waterline
        ... figures: client on deck, diver below ...
    water_front(f, t)                                       # waterline seen across the hull
    boat.draw_lights(f, t)                                  # lantern, window, masthead
"""
import math

from engine import draw
from engine.core import W, H, clamp, lerp, hash01, noise1, smoothstep

from .sets_common import (PAL, SEA_Y, mix, water_at, sky_at, line)

# ----------------------------------------------------------------------------- the swell
# (amplitude px, wavelength px, period s, phase, direction). A calm night swell: the boat
# pitches 1-3 degrees. Sum of travelling sines: deterministic, periodic, cheap.
SWELL = (
    (15.0, 2300.0, 7.4, 0.0, +1),
    (8.0, 1270.0, 5.3, 1.9, +1),
    (4.0, 690.0, 3.7, 4.2, -1),
    (1.8, 310.0, 2.3, 2.6, +1),
)


def sea_y(x, t, amp=1.0):
    """World y of the water surface at world x, time t (0 = mean sea level, y down).
    Everything that floats (boat, buoy, hose, a surfacing diver) should ride this."""
    y = 0.0
    for A, L, T, ph, d in SWELL:
        y += A * math.sin(2 * math.pi * (x / L - d * t / T) + ph)
    return SEA_Y + amp * y


def sea_slope(x, t, amp=1.0):
    """dy/dx of the surface at x (for pitching objects: angle = atan(slope))."""
    s = 0.0
    for A, L, T, ph, d in SWELL:
        s += A * (2 * math.pi / L) * math.cos(2 * math.pi * (x / L - d * t / T) + ph)
    return amp * s


def sea_pts(x0, x1, t, step=10.0, amp=1.0):
    """[(x, sea_y)] samples of the surface from x0 to x1."""
    n = max(2, int(abs(x1 - x0) / step) + 1)
    return [(lerp(x0, x1, i / (n - 1)), sea_y(lerp(x0, x1, i / (n - 1)), t, amp)) for i in range(n)]


def float_pose(x, t, length=200.0, amp=1.0, lag=0.25):
    """(y, angle_deg) for a floating body of `length` centred at x: heave = mean surface
    under it, pitch = slope across it, both lagging the water a little (inertia)."""
    tt = t - lag
    xs = (x - length / 2, x - length / 4, x, x + length / 4, x + length / 2)
    ys = [sea_y(xx, tt, amp) for xx in xs]
    y = (ys[0] + 2 * ys[1] + 2 * ys[2] + 2 * ys[3] + ys[4]) / 8.0
    ang = math.degrees(math.atan2(ys[4] - ys[0], length))
    return y, ang


# ----------------------------------------------------------------------------- horizon
def waterline_screen_y(f):
    """Screen y of mean sea level in the action plane (ignores roll)."""
    return H / 2 + (SEA_Y - f.cam.y) * f.cam.zoom


def horizon_y(f):
    """Screen y of the horizon: eye level when the camera is above the sea, else the near
    waterline (see module doc)."""
    return min(H / 2.0, waterline_screen_y(f))


# ----------------------------------------------------------------------------- sky
_CLOUDS = (   # (height as a fraction of the moon's height, x offset from the moon, length,
              #  thickness, drift px/s, seed)
    (1.30, -330.0, 1500.0, 110.0, 2.4, 1),
    (0.80, 300.0, 1250.0, 62.0, 3.1, 2),
    (0.47, -560.0, 900.0, 34.0, 1.6, 4),
)


def _cloud_pts(cx, cy, length, thick, seed):
    """Long night cloud: lumpy rolling top, flatter ragged base, tapered ends."""
    n = 64
    top, bot = [], []
    for i in range(n + 1):
        u = i / n
        x = cx + (u - 0.5) * length
        env = math.sin(math.pi * u) ** 0.6
        lump = 0.45 + 0.5 * noise1(u * 3.0, seed) + 0.6 * max(0.0, noise1(u * 7.0, seed + 3)) \
            + 0.35 * max(0.0, noise1(u * 16.0, seed + 6))
        top.append((x, cy - thick * env * (0.30 + lump)))
        rag = 0.25 * noise1(u * 13.0, seed + 9) + 0.15 * noise1(u * 31.0, seed + 12)
        bot.append((x, cy + thick * 0.32 * env * (0.9 + rag)))
    return top + bot[::-1]


def night_sky(f, t, moon=(760.0, 820.0), moon_r=62.0, dusk=0.0, clouds=True, stars=True,
              veil=0.0):
    """Night (dusk > 0: afterglow) sky above the horizon, screen space, plus the moon.

    moon   : (screen x, height above the horizon) in frame px - the moon is at infinity, so
             it does not move with crane/truck moves; it slides away with the horizon when
             the camera goes under. None hides it.
    dusk   : 0 = night .. 1 = last light (amber afterglow on the horizon).
    veil   : 0..1 a thin cloud strand across the moon's face (noir).
    Returns the moon's screen centre (or None)."""
    hz = horizon_y(f)
    c = f.ctx
    with f.screen() as S:
        S.save()
        S.rectangle(0, -10, W, hz + 12)
        S.clip()
        stops = [(hz - 1900, mix(PAL.sky_top, PAL.ink, 0.62)), (hz - 1150, mix(PAL.sky_top, PAL.ink, 0.25)),
                 (hz - 560, PAL.sky_top), (hz - 200, sky_at(0.35)), (hz - 40, sky_at(0.06)), (hz, PAL.sky_bottom)]
        y0, y1 = stops[0][0], stops[-1][0]
        draw.linear(S, (0, y0), (0, y1), [((yy - y0) / (y1 - y0), col, 1.0) for yy, col in stops])
        S.paint()
        if stars:
            for i in range(70):
                sx = hash01(i, 11) * W
                sh = 380 + hash01(i, 12) ** 0.7 * 1500
                sy = hz - sh
                if sy < -4:
                    continue
                if moon is not None and math.hypot(sx - moon[0], sh - moon[1]) < 260:
                    continue
                tw = 0.6 + 0.4 * math.sin(t * (1.3 + hash01(i, 13) * 2.0) + i)
                a = (0.10 + 0.32 * hash01(i, 14) ** 2) * tw * (1 - 0.7 * dusk) * smoothstep(300, 800, sh)
                draw.circle(S, (sx, sy), 0.9 + 0.9 * hash01(i, 15))
                draw.fill(S, PAL.moon, a)
        S.restore()
    mc = None
    if moon is not None:
        mc = (moon[0], hz - moon[1])
        with f.screen() as S:
            S.save()
            S.rectangle(0, -10, W, hz)
            S.clip()
            draw.circle(S, mc, moon_r)
            draw.fill(S, mix(PAL.moon, PAL.sky_bottom, 0.04))
            S.restore()
    if clouds:
        with f.screen() as S:
            S.save()
            S.rectangle(0, -10, W, hz)
            S.clip()
            mx, mh = moon if moon is not None else (W / 2, 820.0)
            for fh, dx, length, thick, drift, seed in _CLOUDS:
                hgt = fh * mh
                x = mx + dx + drift * t + 0.02 * (W / 2 - f.cam.x)
                y = hz - hgt
                u = clamp(hgt / 1500.0)
                col = mix(PAL.ink, sky_at(u), lerp(0.62, 0.40, u))
                draw.poly(S, _cloud_pts(x, y, length, thick, seed))
                draw.fill(S, col)
            if mc is not None and veil > 0:
                pts = _cloud_pts(mc[0] + 40, mc[1] + moon_r * 0.25, moon_r * 7.0, 9.0 * veil + 3, 7)
                draw.poly(S, pts)
                draw.fill(S, mix(PAL.ink, PAL.sky_top, 0.7), clamp(veil))
            S.restore()
    # light: moon halo, dusk afterglow (additive, in screen space through a par-0 light layer)
    if True:
        with f.light(par=0.0, blur=24) as A:
            A.save()
            A.identity_matrix()
            A.scale(A.get_target().get_width() / W, A.get_target().get_height() / H)
            if mc is not None:
                draw.glow_disc(A, mc, moon_r * 9.0, PAL.moon, 0.13)
                draw.glow_disc(A, mc, moon_r * 3.6, PAL.moon, 0.20)
                draw.glow_disc(A, mc, moon_r * 1.6, PAL.moon, 0.25)
            # night-glow band on the horizon (the sky is always brightest at the sea's edge)
            draw.linear(A, (0, hz - 360), (0, hz + 2), [(0, PAL.moon, 0.0), (0.75, PAL.moon, 0.035), (1, PAL.moon, 0.09)])
            A.rectangle(0, hz - 360, W, 362)
            A.fill()
            if dusk > 0:
                draw.linear(A, (0, hz - 520), (0, hz + 4), [(0, PAL.light, 0.0), (0.7, PAL.light, 0.10 * dusk),
                                                              (1, PAL.light, 0.30 * dusk)])
                A.rectangle(0, hz - 520, W, 526)
                A.fill()
            A.restore()
        if mc is not None:
            with f.emit(par=0.0) as G:
                G.save()
                G.identity_matrix()
                G.scale(G.get_target().get_width() / W, G.get_target().get_height() / H)
                draw.circle(G, mc, moon_r * 0.98)
                draw.fill(G, PAL.moon, 0.55)
                G.restore()
    return mc


# ----------------------------------------------------------------------------- far sea
_BANDS = (0.035, 0.08, 0.15, 0.26, 0.42, 0.64)


def far_sea(f, t, moon_x=None, dusk=0.0, amp=1.0):
    """The sea surface in perspective between the horizon and the near waterline: layered
    swell bands (lighter far, darker near) and the moon's glitter path. Screen space."""
    cam = f.cam
    hz = horizon_y(f)
    wl = waterline_screen_y(f)
    if wl - hz < 2.0:
        return
    far_c = mix(PAL.sky_bottom, PAL.ink, 0.18)
    near_c = mix(PAL.sky_top, PAL.ink, 0.70)
    with f.screen() as S:
        S.save()
        S.rectangle(0, hz - 60, W, H - hz + 60)
        S.clip()
        # the base: far sea right under the horizon
        draw.linear(S, (0, hz), (0, wl + 30), [(0, mix(PAL.sky_bottom, far_c, 0.5), 1), (1, near_c, 1)])
        S.rectangle(0, hz, W, H - hz)
        S.fill()
        for i, p in enumerate(_BANDS):
            base = hz + (wl - hz) * p
            if base > H + 40:
                break
            z = cam.zoom * p
            pts = []
            n = 72
            for k in range(n + 1):
                sx = -20 + (W + 40) * k / n
                wx = cam.x + (sx - W / 2) / max(z, 1e-4)
                pts.append((sx, base + sea_y(wx, t, amp) * z * 1.6 - 3.0 * p))
            pts += [(W + 20, H + 10), (-20, H + 10)]
            draw.poly(S, pts)
            draw.fill(S, mix(far_c, near_c, (i + 1) / len(_BANDS)))
        S.restore()
    # moon glitter on the far sea
    if moon_x is not None:
        with f.light(par=0.0, blur=3) as A:
            A.save()
            A.identity_matrix()
            A.scale(A.get_target().get_width() / W, A.get_target().get_height() / H)
            k = int(t * 8)
            for i in range(140):
                v = hash01(i, 21)
                y = hz + (wl - hz) * v ** 1.3
                if y > wl - 2:
                    continue
                spread = 14 + 300 * v ** 1.2
                x = moon_x + (hash01(i, 22, k % 5) * 2 - 1) * spread * (0.35 + 0.65 * hash01(i, 23))
                L = 6 + 46 * v * (0.3 + hash01(i, 24))
                a = (0.45 + 0.55 * hash01(i, 25, k)) * (1 - 0.45 * v) * (0.55 + 0.45 * math.sin(t * 3 + i))
                A.rectangle(x - L / 2, y - 0.8, L, 1.6 + 2.2 * v)
                A.set_source_rgba(*PAL.moon, min(a, 1.0))
                A.fill()
            A.restore()


# ----------------------------------------------------------------------------- the water section
def underwater(f, t, bright=1.0, amp=1.0, x_margin=200.0):
    """The water volume below the near waterline, as a cross-section: aqua under the surface
    to teal to ink, world-anchored by depth (so it scrolls with a descent). bright < 1 for
    night. Draws on the main canvas through the camera."""
    x0, y0, x1, y1 = f.cam.view_rect(x_margin)
    if y1 < -60:
        return
    c = f.ctx
    top = max(y0 - 50, -80.0)
    stops = []
    ya, yb = max(top, -60.0), max(y1, 0.0) + 10
    n = 12
    for i in range(n):
        y = lerp(ya, yb, i / (n - 1))
        stops.append((y, water_at(y, bright)))
    pts = sea_pts(x0, x1, t, step=max(6.0, (x1 - x0) / 160), amp=amp)
    c.new_path()
    c.move_to(*pts[0])
    for p in pts[1:]:
        c.line_to(*p)
    c.line_to(x1, yb)
    c.line_to(x0, yb)
    c.close_path()
    span = (yb - ya) or 1.0
    draw.linear(c, (0, ya), (0, yb), [((y - ya) / span, col, 1.0) for y, col in stops])
    c.fill()


def surface_glow(f, t, bright=1.0, amp=1.0, width=1.0):
    """Light along the underside of the surface: the bright skin of the water (total
    internal reflection) and a soft glow band. Additive; call after underwater()."""
    x0, y0, x1, y1 = f.cam.view_rect(100)
    if y0 > 900 or y1 < -100:
        return
    pts = sea_pts(x0, x1, t, step=max(8.0, (x1 - x0) / 120), amp=amp)
    with f.light(blur=10) as A:
        line(A, [(x, y + 26 * width) for x, y in pts], 52 * width, PAL.surface, 0.16 * bright)
        line(A, [(x, y + 5) for x, y in pts], 9 * width, PAL.surface, 0.30 * bright)
    with f.light(blur=1.5) as A:
        line(A, [(x, y + 1.5) for x, y in pts], 2.6, PAL.moon, 0.55 * bright)


def water_front(f, t, alpha=0.16, bright=1.0, amp=1.0, meniscus=0.7):
    """The near water seen IN FRONT of whatever was drawn so far: a faint aqua veil below the
    waterline plus the crisp meniscus line, so the waterline reads across the boat's hull
    (Inside). Call after drawing the boat (and figures, if they should be veiled too)."""
    x0, y0, x1, y1 = f.cam.view_rect(100)
    if y1 < -60:
        return
    pts = sea_pts(x0, x1, t, step=max(6.0, (x1 - x0) / 160), amp=amp)
    c = f.ctx
    if alpha > 0:
        c.new_path()
        c.move_to(*pts[0])
        for p in pts[1:]:
            c.line_to(*p)
        yb = max(y1, 0.0) + 10
        c.line_to(x1, yb)
        c.line_to(x0, yb)
        c.close_path()
        ya = -40.0
        draw.linear(c, (0, ya), (0, ya + 1400), [(0, water_at(0, bright), alpha), (0.12, water_at(200, bright), alpha * 0.8),
                                                (1, water_at(1400, bright), alpha * 0.35)])
        c.fill()
    if meniscus > 0:
        with f.light(blur=2.0) as A:
            line(A, pts, 3.0, PAL.moon, 0.5 * meniscus * bright)
            line(A, [(x, y + 7) for x, y in pts], 10, PAL.surface, 0.18 * meniscus * bright)


def sea_world(f, t, moon=(760.0, 820.0), moon_r=62.0, dusk=0.0, bright=None, clouds=True,
              stars=True, veil=0.0, amp=1.0, glow=True):
    """Everything behind the action plane of a surface shot, in order: night sky + moon,
    far sea in perspective, the water section with its bright skin.
    bright: water brightness (default from dusk: 1.0 at dusk .. 0.62 at night).
    Returns dict(horizon=screen y, waterline=screen y, moon=screen centre or None)."""
    if bright is None:
        bright = lerp(0.62, 1.0, clamp(dusk))
    mc = None
    hz = horizon_y(f)
    if hz > -10:
        mc = night_sky(f, t, moon=moon, moon_r=moon_r, dusk=dusk, clouds=clouds, stars=stars, veil=veil)
        far_sea(f, t, moon_x=(mc[0] if mc else None), dusk=dusk, amp=amp)
    underwater(f, t, bright=bright, amp=amp)
    if glow:
        surface_glow(f, t, bright=bright, amp=amp)
    return dict(horizon=hz, waterline=waterline_screen_y(f), moon=mc, bright=bright)
