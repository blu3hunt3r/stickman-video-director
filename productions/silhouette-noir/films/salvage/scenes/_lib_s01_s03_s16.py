"""Shared helpers for SALVAGE s01 (red_line), s03 (descent) and s16 (sea_keeps).

Everything here is a pure function of its arguments (plus caches of deterministic data):
  * Sampled            cache an expensive function of time on a grid, interpolate between
  * hose_rope / draw_hose   the red air hose (physics.Rope with the bible's settings) and its
                       smooth filled band
  * fedora_pts         the client's fedora as a prop outline (costume._HATS), any yaw/tilt
  * helmet_valve       where the exhaust bubbles leave the Mark V helmet
  * line_band_pts      the Bass red line (bass.curl_pts) with an optional sag profile
  * crew               the 31 paper tick-figures hanging on the line (s01)
  * screen_glow        soft screen-space light pools (backlight behind a silhouette)
  * post_blend         interpolate Frame.post between a Bass setup and a live setup
"""
import bisect
import math

import cairo
import numpy as np

from engine import bass, costume, draw
from engine.core import H, W, clamp, hash01, lerp, noise1, smoothstep
from engine.palette import PAPER, RED, SALVAGE
from engine.physics import Rope

INK = SALVAGE.ink
D2R = math.pi / 180.0


# ----------------------------------------------------------------------------- time sampling
class Sampled:
    """fn(t) -> tuple/float sampled on [t0, t1] at `hz`, linearly interpolated (built lazily,
    once per process). Use it for things the rope simulation or a particle emitter asks for
    many times (a helmet point from an Actor skeleton)."""

    def __init__(self, fn, t0, t1, hz=60.0):
        self.fn, self.t0, self.t1, self.hz = fn, float(t0), float(t1), float(hz)
        self._tab = None

    def _build(self):
        n = int(math.ceil((self.t1 - self.t0) * self.hz)) + 2
        ts = self.t0 + np.arange(n) / self.hz
        self._tab = np.array([np.atleast_1d(np.asarray(self.fn(float(t)), np.float64)) for t in ts])

    def __call__(self, t):
        if self._tab is None:
            self._build()
        x = (min(max(t, self.t0), self.t1) - self.t0) * self.hz
        i = min(int(x), len(self._tab) - 2)
        u = x - i
        v = self._tab[i] * (1.0 - u) + self._tab[i + 1] * u
        return tuple(float(a) for a in v) if v.size > 1 else float(v[0])


def track(keys, t):
    """Piecewise interpolation through [(t, value, ease_into_key)] (values: floats)."""
    from engine.core import ease
    if t <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        if t <= keys[i][0]:
            t0, v0 = keys[i - 1][0], keys[i - 1][1]
            t1, v1 = keys[i][0], keys[i][1]
            e = keys[i][2] if len(keys[i]) > 2 else "inout"
            return lerp(v0, v1, ease(e, (t - t0) / max(t1 - t0, 1e-9)))
    return keys[-1][1]


def integ(fn, a, b, n=48):
    """Simpson integral of fn over [a, b] (camera travel from a speed curve)."""
    if b == a:
        return 0.0
    if n % 2:
        n += 1
    h = (b - a) / n
    s = fn(a) + fn(b)
    for i in range(1, n):
        s += (4 if i % 2 else 2) * fn(a + i * h)
    return s * h / 3.0


# ----------------------------------------------------------------------------- the red hose
HOSE_W = 10.0           # bible: ~10 px thick at zoom 1


def hose_rope(a, b, length, n=40, t0=-2.0, t1=20.0, current=None, collide=None, release=None,
              length_fn=None, init=None, gravity=(0.0, 60.0), drag=1.8, stiffness=0.3, iters=14):
    """The air hose as physics.Rope with the bible's settings (stiffness 0.3, gravity ~(0, 60),
    drag ~1.8, a current toward +x)."""
    cur = current if current is not None else (lambda t, x, y: (34.0 + 14.0 * math.sin(0.37 * t + y / 900.0), 0.0))
    return Rope(n, length, a, b, t0=t0, t1=t1, gravity=gravity, drag=drag, current=cur, collide=collide,
                release=release, length_fn=length_fn, iters=iters, stiffness=stiffness, init=init)


def draw_hose(ctx, pts, width=HOSE_W, color=RED, alpha=1.0):
    """The hose as one smooth filled band (a round-capped stroke of a Catmull-Rom curve)."""
    if len(pts) < 2:
        return
    ctx.save()
    ctx.new_path()
    if len(pts) >= 3:
        draw.smooth(ctx, pts, close=False, tension=0.5)
    else:
        draw.poly(ctx, pts, close=False)
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*color[:3], alpha)
    ctx.stroke()
    ctx.restore()


def polyline_len(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def cut_polyline(pts, s0, s1):
    """Sub-polyline between arc lengths s0 < s1."""
    out = []
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L <= 1e-9:
            continue
        lo, hi = acc, acc + L
        if hi >= s0 and lo <= s1:
            u0 = clamp((s0 - lo) / L)
            u1 = clamp((s1 - lo) / L)
            pa = (lerp(a[0], b[0], u0), lerp(a[1], b[1], u0))
            pb = (lerp(a[0], b[0], u1), lerp(a[1], b[1], u1))
            if not out:
                out.append(pa)
            out.append(pb)
        acc = hi
    return out


# ----------------------------------------------------------------------------- diver helpers
def helmet_valve(sk):
    """World point just above the helmet's top valve (where the exhaust bubbles leave)."""
    c, R, vp, vr, inlet = costume.helmet_frame(sk)
    w = sk.side_w
    fwd = 1.0 if math.cos((sk.pose.yaw + sk.pose.head_yaw) * D2R) >= 0 else -1.0
    return (c[0] + fwd * R * 0.35 * (1 - w) - 0.18 * R * w, c[1] - R * 1.05)


def port_center(sk):
    """Centre of the helmet's front glass (the port the eyes glow through)."""
    c, R, vp, vr, inlet = costume.helmet_frame(sk)
    fwd = 1.0 if math.cos((sk.pose.yaw + sk.pose.head_yaw) * D2R) >= 0 else -1.0
    w = sk.side_w
    port_c = lerp((c[0] + fwd * R * 0.98, vp[1]), vp, w)
    return lerp(vp, port_c, 0.5), vr


# ----------------------------------------------------------------------------- the fedora prop
_FED_PROF, _FED_FRONT = costume._HATS["fedora"]
_FED_PIVOT = (0.0, 0.80)          # head units: middle of the brim


def fedora_pts(c, size, yaw=0.0, tilt=0.0):
    """The client's fedora as a world outline. c = middle of the brim (world), size = head
    height px (the client's ~86 at zoom 1), yaw: 0 = profile facing right, 90 = front,
    180 = profile facing left (blends like costume does), tilt: degrees (clockwise)."""
    w = abs(math.sin(yaw * D2R))
    fac = 1.0 if math.cos(yaw * D2R) >= 0 else -1.0
    ca, sa = math.cos(tilt * D2R), math.sin(tilt * D2R)
    out = []
    for (px, py), (qx, qy) in zip(_FED_PROF, _FED_FRONT):
        x = lerp(px * fac, qx * fac, w) - _FED_PIVOT[0]       # mirror both, or the blend collapses
        y = -(lerp(py, qy, w) - _FED_PIVOT[1])          # head units, y down
        out.append((c[0] + (x * ca - y * sa) * size, c[1] + (x * sa + y * ca) * size))
    return out


def draw_fedora(ctx, c, size, yaw=0.0, tilt=0.0, color=INK, alpha=1.0):
    pts = fedora_pts(c, size, yaw, tilt)
    ctx.new_path()
    draw.poly(ctx, pts)
    ctx.set_source_rgba(*color[:3], alpha)
    ctx.fill()
    return pts


# ----------------------------------------------------------------------------- the Bass red line
def line_band_pts(c, length, width, u, rot=0.0, seed=0, n=160, up=True, sag=None, scale=1.0):
    """bass.curl_pts (a straight cut band that curls into a ring) plus: sag(x) -> dy added to
    the band while it is straight (u == 0), and a uniform scale about c."""
    polys = bass.curl_pts(c, length, width, u, rot=rot, seed=seed, n=n, up=up)
    if sag is not None and u <= 0.0:
        polys = [[(x, y + sag(x)) for x, y in P] for P in polys]
    if scale != 1.0:
        polys = [[(c[0] + (x - c[0]) * scale, c[1] + (y - c[1]) * scale) for x, y in P] for P in polys]
    return polys


def fill_polys(ctx, polys, color, alpha=1.0):
    bass.fill_polys(ctx, polys, color, alpha)


# ----------------------------------------------------------------------------- 31 crew cut-outs
def crew_layout(n=31, x0=74.0, x1=1006.0, seed=41):
    """The 31 men on the line: x, height, kind, flip, swing seed. The captain is last."""
    out = []
    kinds = ("man", "worker", "man", "man", "worker")
    for i in range(n):
        u = (i + 0.5) / n
        x = lerp(x0, x1, u) + 3.0 * (hash01(seed, i, 1) - 0.5)
        h = 63.0 + 7.0 * (hash01(seed, i, 2) - 0.5)
        kind = "captain" if i == n - 1 else kinds[int(hash01(seed, i, 3) * len(kinds)) % len(kinds)]
        if i == n - 1:
            h = 68.0
        out.append(dict(i=i, x=x, h=h, kind=kind, flip=hash01(seed, i, 4) < 0.5, seed=seed * 31 + i))
    return out


def draw_hanging_cutout(ctx, kind, peg, height, color, angle=0.0, scale=1.0, flip=False, seed=0, alpha=1.0):
    """A cut-out man hanging from `peg` (the top of his head), rotated by angle (deg) about
    the peg and scaled about it (pop-on)."""
    if scale <= 0.01:
        return
    ctx.save()
    ctx.translate(peg[0], peg[1])
    if angle:
        ctx.rotate(angle * D2R)
    ctx.scale(scale, scale)
    top = 103.0 if kind == "captain" else 100.0
    bass.draw_cutout(ctx, kind, (0.0, height * top / 100.0), height, color, seed=seed, flip=flip, alpha=alpha)
    ctx.restore()


# ----------------------------------------------------------------------------- light helpers
def screen_glow(f, c, r, color, a, par=0.0, blur=30.0, core=0.0):
    """A soft additive pool of light in SCREEN space (a backlight behind a silhouette)."""
    with f.light(par=par, blur=blur) as A:
        A.save()
        A.identity_matrix()
        A.scale(A.get_target().get_width() / W, A.get_target().get_height() / H)
        draw.glow_disc(A, c, r, color, a, core)
        A.restore()


def screen_band(f, y0, y1, color, a0, a1, blur=0.0):
    """Additive vertical gradient band (screen space): a0 at y0 -> a1 at y1."""
    with f.light(par=0.0, blur=blur) as A:
        A.save()
        A.identity_matrix()
        A.scale(A.get_target().get_width() / W, A.get_target().get_height() / H)
        draw.linear(A, (0, y0), (0, y1), [(0, color, a0), (1, color, a1)])
        A.rectangle(0, min(y0, y1), W, abs(y1 - y0))
        A.fill()
        A.restore()


# ----------------------------------------------------------------------------- post blending
BASS_POST = dict(paper=0.75, vignette=0.16, bloom=0.0, flicker=0.006, grain=0.045)


def post_blend(f, k, bass_post=None):
    """k = 1: Bass print (paper fibres, light vignette, no bloom); k = 0: the live defaults."""
    if k <= 0.0:
        return
    bp = bass_post or BASS_POST
    for key, v in bp.items():
        f.post[key] = lerp(f.post[key], v, clamp(k))


# ----------------------------------------------------------------------------- misc
def lerp2(a, b, t):
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t))


def ss(a, b, x):
    return smoothstep(a, b, x)


def wobble(t, seed, amp=1.0, rate=0.3):
    return amp * noise1(t * rate, seed)


# ============================================================================= s14 / s15: the stern at night
# One clock for the bell: tau = s14 scene time (s15 passes t + S15_OFFSET). The boat rides the
# same swell on that clock, so the davit, the bell and the deck are continuous across the cut.
from films.salvage import sets as S          # noqa: E402
from films.salvage import sets_props as SP   # noqa: E402

S15_OFFSET = 11.0
NIGHT_MOON = (430.0, 560.0)       # (screen x, height above the horizon) for s12/s14/s15
NIGHT_MOON_R = 62.0
NIGHT_BRIGHT = 0.62               # night water (sets_surface default for dusk 0)
PALE = S.mix(PAPER, S.PAL.surface, 0.30)      # the pale lifting line (as the deep scenes draw it)
MOONLIT = S.mix(S.PAL.moon, S.PAL.surface, 0.25)

BELL_S = 1.8                      # the wreck draws it at 1.8 (288 px crown to lip)
BELL_LIP = 254.0                  # crown-loop top -> lip centre at BELL_S
BELL_HALF = 119.0                 # half width of the lip at BELL_S
L_TOP = 110.0                     # sheave -> crown loop when hauled right up
T_STOP = 9.75                     # the winch stops (the client freezes): the first TOLL
SW_HALF = 1.15                    # half period of the swing on the davit
# (tau, strength): s14 9.75 (outboard), s14 10.90 (inboard, its echo carries the cut),
# s15 6.80 (inboard, the loudest)
TOLLS = ((T_STOP, 1.0), (T_STOP + SW_HALF, 0.8), (T_STOP + 7 * SW_HALF, 1.4))
_AMP = ((6.5, 0.0), (9.0, 0.0), (9.75, 24.0), (10.9, 22.0), (12.05, 18.5), (13.2, 16.0), (14.35, 14.5),
        (15.5, 15.0), (16.65, 19.5), (17.8, 26.0), (18.95, 22.0), (20.1, 19.0), (21.25, 16.5), (24.0, 13.0))


def _haul_v(tau):
    """Winch speed (px of line per s): steady, then eager, then slowing to a stop."""
    if tau >= T_STOP:
        return 0.0
    return (210.0 + 310.0 * smoothstep(5.5, 7.8, tau)) * (1.0 - smoothstep(9.2, T_STOP, tau))


_HDT = 1.0 / 240.0
_HT = np.arange(-3.0, T_STOP + 2 * _HDT, _HDT)
_HV = np.array([_haul_v(float(x)) for x in _HT])
_HC = np.concatenate([[0.0], np.cumsum(0.5 * (_HV[1:] + _HV[:-1]) * _HDT)])
_HR = _HC[-1] - _HC                  # line still to haul in at each grid time


def haul_left(tau):
    """Line (px) still to be hauled in before the bell reaches the top (0 after T_STOP)."""
    if tau >= T_STOP:
        return 0.0
    return float(np.interp(tau, _HT, _HR))


def crank_deg(tau):
    """Winch crank angle (deg, clockwise on screen): ~0.95 deg per px of line."""
    return 0.95 * (float(_HR[0]) - haul_left(max(tau, -3.0))) + 35.0


def _smooth_keys(keys, x):
    if x <= keys[0][0]:
        return keys[0][1]
    for (x0, y0), (x1, y1) in zip(keys, keys[1:]):
        if x <= x1:
            u = (x - x0) / (x1 - x0)
            u = u * u * (3 - 2 * u)
            return y0 + (y1 - y0) * u
    return keys[-1][1]


def bell_amp(tau):
    return _smooth_keys(_AMP, tau)


def _theta_sw(tau):
    return bell_amp(tau) * math.cos(math.pi * (tau - T_STOP) / SW_HALF)


def _line_len(tau):
    stretch = 0.0
    if tau > T_STOP:
        u = tau - T_STOP
        stretch = 10.0 * math.exp(-u / 0.2) * math.sin(math.pi * min(u / 0.12, 1.0) + max(0.0, u - 0.12) * 22.0)
    return L_TOP + haul_left(tau) + stretch


def _theta_uw(tau, ell):
    xo = lerp(40.0, 100.0, smoothstep(730.0, 2900.0, ell))      # the current leans it outboard
    return math.degrees(math.asin(clamp(xo / ell, -0.9, 0.9))) + 0.6 * math.sin(0.7 * tau + 0.4)


_BREAK = None


def bell_break():
    """tau at which the crown loop breaks the surface (~8.29)."""
    global _BREAK
    if _BREAK is None:
        boat = S.Boat()
        tb = 8.3
        for k in range(2400):
            tt = 5.0 + k / 240.0
            st = bell_state(tt, boat, _probe=True)
            if st["top"][1] <= S.sea_y(st["top"][0], tt):
                tb = tt
                break
        _BREAK = tb
    return _BREAK


def _toll_pulse(tau, tk):
    if tau < tk:
        return smoothstep(tk - 0.14, tk, tau)
    return 1.0 - smoothstep(tk + 0.03, tk + 0.32, tau)


def bell_state(tau, boat, _probe=False):
    """The bell at tau: dict(pivot, top (crown-loop top, world), theta (deg, + = swung toward
    +x / outboard), angle (draw_bell angle), clapper, ring (0.. toll flash), wet (s since the lip
    left the water, < 0 before), under (0..1 how far it is below the surface), line_len)."""
    P = boat.sheave(tau)
    ell = _line_len(tau)
    w = smoothstep(8.7, 9.25, tau)
    th = lerp(_theta_uw(tau, ell), _theta_sw(tau), w)
    r = math.radians(th)
    top = (P[0] + ell * math.sin(r), P[1] + ell * math.cos(r))
    if _probe:
        return dict(top=top)
    # the bell's own tilt: wobbles on its crown loop in the water, aligned with the line in air
    wob = 3.0 * math.sin(1.3 * tau + 1.0) * (1.0 - w)
    jit, ring, clap = 0.0, 0.0, None
    c_free = -0.62 * _theta_sw(tau - 0.1) * w - 6.0 * math.sin(1.3 * tau + 0.3) * (1.0 - w)
    c = c_free
    for tk, sk in TOLLS:
        if tau >= tk:
            u = tau - tk
            jit += sk * 0.8 * math.exp(-u / 0.4) * math.sin(2 * math.pi * 7.3 * u)
            ring += sk * math.exp(-u / 0.6)
        pk = _toll_pulse(tau, tk)
        if pk > 0.0:
            wall = -24.0 if _theta_sw(tk) > 0 else 24.0
            c = lerp(c, wall, pk)
    ang = -(th + wob + jit)
    lip = (top[0] - BELL_LIP * math.sin(math.radians(ang)), top[1] + BELL_LIP * math.cos(math.radians(ang)))
    sea = S.sea_y(lip[0], tau)
    under = clamp((top[1] + 0.0 - S.sea_y(top[0], tau)) / 300.0, 0.0, 1.0)
    return dict(pivot=P, top=top, theta=th, angle=ang, clapper=c, ring=ring, lip=lip, line_len=ell,
                under=under, lip_sea=sea - lip[1], swing=w)


def bell_lip_clear():
    """tau at which the lip leaves the water."""
    return bell_break() + (BELL_LIP + 20.0) / 520.0


def bell_path(ctx, st, s=BELL_S):
    """Append the bell's body outline (crown loop, body, lip bead) to ctx's path."""
    ctx.save()
    ctx.translate(*st["top"])
    ctx.rotate(math.radians(st["angle"]))
    ctx.scale(s, s)
    ctx.append_path(S.shape("bell_body", SP._bell_body))
    ctx.restore()


def bell_point(st, local, s=BELL_S):
    """World point of a bell-local point (draw_bell coords at s = 1)."""
    a = math.radians(st["angle"])
    x, y = local[0] * s, local[1] * s
    return (st["top"][0] + x * math.cos(a) - y * math.sin(a), st["top"][1] + x * math.sin(a) + y * math.cos(a))


def draw_bell_lit(ctx, st, moon_dir, zoom, color=INK, rim=0.0, sheen=0.0, rim_col=None):
    """The bell in ink with moonlight on it: a thin rim on the edges facing the moon (an
    offset pale copy under the ink) and a wet sheen just inside them. moon_dir: unit vector
    (world) toward the moon. Returns draw_bell's dict."""
    rc = rim_col or MOONLIT
    if rim > 0.0:
        off = 2.6 / zoom
        ctx.save()
        ctx.translate(moon_dir[0] * off, moon_dir[1] * off)
        ctx.new_path()
        bell_path(ctx, st)
        ctx.set_source_rgba(rc[0], rc[1], rc[2], clamp(rim))
        ctx.fill()
        ctx.restore()
    out = SP.draw_bell(ctx, st["top"][0], st["top"][1], angle=st["angle"], clapper=st["clapper"], s=BELL_S,
                       color=color)
    if sheen > 0.0:
        c = bell_point(st, (0.0, 85.0))
        ctx.save()
        ctx.new_path()
        bell_path(ctx, st)
        ctx.clip()
        ctx.new_path()
        bell_path(ctx, st)
        ctx.set_line_width(2.0 * 7.0 / zoom)
        R = 150.0
        import cairo as _c
        g = _c.LinearGradient(c[0] + moon_dir[0] * R, c[1] + moon_dir[1] * R, c[0] - moon_dir[0] * R * 0.1,
                              c[1] - moon_dir[1] * R * 0.1)
        g.add_color_stop_rgba(0.0, rc[0], rc[1], rc[2], clamp(sheen))
        g.add_color_stop_rgba(0.55, rc[0], rc[1], rc[2], clamp(sheen) * 0.25)
        g.add_color_stop_rgba(1.0, rc[0], rc[1], rc[2], 0.0)
        ctx.set_source(g)
        ctx.stroke()
        ctx.restore()
    return out


def moon_dir_world(cam, p, moon_screen):
    """Unit vector (world == screen orientation) from world point p toward the moon's disc."""
    sp = cam.to_screen(p)
    dx, dy = moon_screen[0] - sp[0], moon_screen[1] - sp[1]
    d = math.hypot(dx, dy) or 1.0
    return (dx / d, dy / d)


# ----------------------------------------------------------------------------- water off the bell
def bell_pour(f, tau, boat, t_clear, rate=1.0, color=None, seed=5, t_end=None):
    """Water pouring off the lip as the bell clears the surface, then drips: droplets leave
    the lip with the bell's velocity and fall (g = 3000) into the sea. tau: the bell clock."""
    col = color or S.mix(S.PAL.moon, S.PAL.surface, 0.35)
    g = 3000.0
    hz = 40.0
    t0 = t_clear - 0.55
    t1 = tau if t_end is None else min(tau, t_end)
    if t1 <= t0:
        return
    k0 = max(0, int((tau - 0.75 - t0) * hz))
    k1 = int((t1 - t0) * hz)
    c = f.ctx
    big, small = [], []
    for k in range(k0, k1 + 1):
        te = t0 + k / hz
        age_c = te - t_clear
        flow = 1.0 if age_c < 0.0 else math.exp(-age_c / 0.55) + 0.12 * math.exp(-age_c / 3.0)
        n = int(round(18 * flow * rate + 0.5))
        if n <= 0:
            continue
        st = bell_state(te, boat)
        st2 = bell_state(te + 0.02, boat)
        for i in range(n):
            if hash01(seed, k, i, 9) > flow * 1.2 + 0.08:
                continue
            u = (hash01(seed, k, i, 1) - 0.5) * 2.0
            u = math.copysign(abs(u) ** 0.6, u)        # more at the corners
            lp = (u * 66.0, 142.0 + 3.0 * hash01(seed, k, i, 2))
            p0 = bell_point(st, lp)
            p1 = bell_point(st2, lp)
            vx = (p1[0] - p0[0]) / 0.02 + 40.0 * (hash01(seed, k, i, 3) - 0.5) + u * 30.0
            vy = (p1[1] - p0[1]) / 0.02
            dt = tau - te
            if dt < 0.0:
                continue
            x = p0[0] + vx * dt
            y = p0[1] + vy * dt + 0.5 * g * dt * dt
            if y > S.sea_y(x, tau) + 6.0:
                continue
            r = 1.2 + 3.2 * hash01(seed, k, i, 4) ** 2
            sp = math.hypot(vx, vy + g * dt)
            (big if r > 2.6 else small).append((x, y, r, r * (1.0 + min(sp / 300.0, 4.0)),
                                                math.atan2(vy + g * dt, vx)))
    for grp, al in ((big, 0.55), (small, 0.75)):
        if not grp:
            continue
        c.new_path()
        for x, y, r, L, ang in grp:
            c.save()
            c.translate(x, y)
            c.rotate(ang)
            c.scale(L, r)
            c.new_sub_path()
            c.arc(0, 0, 1.0, 0, 2 * math.pi)
            c.restore()
        c.set_source_rgba(col[0], col[1], col[2], al)
        c.fill()


# ----------------------------------------------------------------------------- splash / foam
SPRAY = S.mix(S.PAL.moon, S.PAL.surface, 0.35)


def splash(f, t, xs, t0, n, scale, seed, color=SPRAY, alpha=1.0):
    """Spray thrown up from the surface at (xs, sea) at t0: ballistic droplets streaked along
    their velocity, falling back into the sea (as s03's plunge)."""
    tau0 = t - t0
    if tau0 < 0.0 or tau0 > 1.7 * math.sqrt(scale):
        return
    c = f.ctx
    g = 2600.0
    big, small = [], []
    for i in range(n):
        te = 0.22 * scale * hash01(seed, i, 1) ** 1.5
        tau = tau0 - te
        if tau <= 0.0:
            continue
        side = 1.0 if hash01(seed, i, 2) < 0.5 else -1.0
        r0 = hash01(seed, i, 3)
        x0 = xs + side * (10.0 + 70.0 * scale * r0)
        vx = side * (60.0 + 380.0 * hash01(seed, i, 4)) * scale ** 0.5
        vy = -(300.0 + 1050.0 * hash01(seed, i, 5) ** 1.4) * scale ** 0.5
        x = x0 + vx * tau
        y = S.sea_y(x0, t0) + vy * tau + 0.5 * g * tau * tau
        if y > S.sea_y(x, t) + 4.0:
            continue
        r = (1.3 + 4.2 * hash01(seed, i, 6) ** 3) * (0.55 + 0.45 * scale)
        vyt = vy + g * tau
        sp = math.hypot(vx, vyt)
        (big if r > 2.6 else small).append((x, y, r, r * (1.0 + min(sp / 420.0, 2.6)), math.atan2(vyt, vx)))
    for grp, al in ((big, 0.62), (small, 0.9)):
        if not grp:
            continue
        c.new_path()
        for x, y, r, L, ang in grp:
            c.save()
            c.translate(x, y)
            c.rotate(ang)
            c.scale(L, r)
            c.new_sub_path()
            c.arc(0, 0, 1.0, 0, 2 * math.pi)
            c.restore()
        c.set_source_rgba(color[0], color[1], color[2], al * alpha)
        c.fill()


def foam(f, t, xs, t0, width, seed, k=1.0, life=2.8, color=SPRAY, glow=True):
    """White water churned up on the surface at xs from t0: spreads and fades, an aerated
    cloud under it and ripples running away along the surface."""
    tau = t - t0
    if tau < 0.0 or tau > life:
        return
    a = (1.0 - smoothstep(0.4, life - 0.1, tau)) * k
    w = width * (0.35 + 0.9 * ease("out", tau / 1.4))
    pts = S.sea_pts(xs - w, xs + w, t, step=6.0)
    top, bot = [], []
    for x, y in pts:
        u = (x - xs) / w
        env = max(0.0, 1.0 - u * u) ** 0.6
        lump = 0.5 + 0.5 * noise1(x / 23.0 + 2.0 * tau, seed)
        top.append((x, y - (2.0 + 7.0 * lump) * env * (1.0 - 0.5 * smoothstep(0.0, 1.5, tau))))
        bot.append((x, y + (3.0 + 6.0 * noise1(x / 31.0 + tau, seed + 3)) * env))
    c = f.ctx
    c.new_path()
    draw.poly(c, top + bot[::-1])
    c.set_source_rgba(color[0], color[1], color[2], 0.8 * a)
    c.fill()
    if glow:
        with f.light(blur=24) as A:
            draw.ellipse(A, (xs, 90.0 + 80.0 * tau), w * 0.7, 130.0 + 70.0 * tau)
            draw.fill(A, S.PAL.surface, 0.2 * a)
        with f.light(blur=2.0) as A:
            for sgn in (-1.0, 1.0):
                for j, sp in enumerate((310.0, 200.0)):
                    xr = xs + sgn * (w * 0.6 + sp * tau)
                    ys = S.sea_y(xr, t)
                    S.line(A, [(xr - 24, ys + 1), (xr, ys - 1.5), (xr + 24, ys + 1)], 2.6, S.PAL.moon,
                           0.45 * a * (1.0 - 0.4 * j))


# ----------------------------------------------------------------------------- the client's hat as a prop
FEDORA = costume._HATS["fedora"]


def hat_on_head(sk):
    """The worn fedora's world outline for skeleton sk (exactly what costume draws)."""
    from engine import figure as _F
    return _F.head_map(sk, FEDORA[0], FEDORA[1])


def rigid(pts, c0, c1, ang):
    """pts moved rigidly: centroid c0 -> c1, rotated by ang (deg, clockwise) about it."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    out = []
    for x, y in pts:
        dx, dy = x - c0[0], y - c0[1]
        out.append((c1[0] + dx * ca - dy * sa, c1[1] + dx * sa + dy * ca))
    return out


def centroid(pts):
    n = float(len(pts))
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)
