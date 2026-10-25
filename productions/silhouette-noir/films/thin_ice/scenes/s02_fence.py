"""s02 FENCE (14-32): the moon comes out; the searchlight; under the wire; the music box; the light
again; the scrap on the barb; into the zone; the prints from above.

  0.0-2.0   Wide, the fence view (from behind them, looking north). The mother and the girl crouch
            in front of the drift, backs to us; the fence across the frame, the tower left, the
            guardhouse right, the woods beyond; the moon behind its cloud; the searchlight's beam
            far off to the left. The last flake falls past the mother's head. Their breath.
  2.0-3.0   CU, her profile: she holds out her mitten, palm up. Nothing falls. She looks up (2.7);
            the cloud's edge silvers.
  3.0-4.0   The fence view, closer. The moon slides out of the cloud: the snow brightens, every
            post throws a long shadow toward us, and so do they. Her breath stops (3.3). At the
            left edge the searchlight's patch comes along the zone.
  4.0-6.0   Wide. The patch slides toward them. She pulls the girl down flat (4.3-4.75); its edge
            rides over the drift's crest above them (passing at 5.0) and goes on east.
  6.0-8.0   Closer, on the gap: she lifts the bottom wire; the girl crawls under it, away from us,
            and lies flat beyond it; she lets the wire down. The patch at the right edge.
  8.0-9.25  The searchlight reverses with a clank (8.0). CU on the snow beyond the wire: the music
            box that slipped out of the girl's pocket springs open (8.25): three notes (8.25, 8.5,
            8.75), the paper dancer turning. The mother's mitten slaps it shut (9.0).
  9.25-10.0 CU, her profile: the mitten pressed to her lips.
  10.0-12.0 The page, from above: the girl flat beyond the wire, the mother this side. The patch
            slides over them right to left; the red scarf burns in it (the heartbeat, 10.75 and
            11.25). It moves on.
  12.0-13.0 Closer, on the gap: the mother crawls under the wire; her coat catches on a barb (12.4);
            she tugs (12.5, 12.62); it rips (12.75); the wire springs back, quivering.
  13.0-14.0 CU: the scrap of her coat on the barb, stirring; the wire still quivering.
  14.0-16.0 Wide: they run hand in hand into the zone toward the woods, their long shadows trailing
            back to us, their prints behind them; smaller and smaller.
  16.0-18.0 The page from above: the two lines of prints, big and small, from the drift under the
            wire and into the trees; the scrap on the wire; the tower's long shadow; the beam far
            off west. Hold. Cut.
"""
import math

from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.thin_ice import cast as C
from films.thin_ice import faces as F
from films.thin_ice import kit as K
from films.thin_ice import world as W
from films.thin_ice.scenes import _lib_dir as L
from films.thin_ice.scenes.s01_title import APPROACH

FILM_T0 = 14.0
# the shots (scene time)
T_B, T_C, T_D, T_E, T_F, T_G, T_H, T_I, T_J, T_K, T_L = 2.0, 3.0, 4.0, 6.0, 8.0, 9.25, 10.0, 12.0, 13.0, 14.0, 16.0
T_UP = 2.7                   # she looks up
T_MOON = (3.0, 3.5)          # the cloud slides off the moon
T_LIT = (3.05, 3.55)         # the snow brightens
T_POSTS = (3.15, 3.7)        # the long shadows grow toward us
T_HOLD = 3.3                 # her breath stops
T_DOWN = (4.3, 4.65)         # she drops flat ...
T_DOWN_G = (4.4, 4.75)       # ... pulling the girl down
T_LIFT = (6.1, 6.45)         # she lifts the bottom wire
T_CRAWL = (6.35, 7.7)        # the girl crawls under
T_LOWER = (7.7, 7.95)        # she lets the wire down
T_CLANK = 8.0
T_OPEN = 8.25
NOTES = (8.25, 8.5, 8.75)
T_SLAP = 9.0
T_BEATS = (10.75, 11.25)     # the heartbeat
T_SNAG = 12.4
T_TUGS = (12.5, 12.62)
T_RIP = 12.75

M_X, G_X = 40.0, 40.62       # where they crouch (map x) ...
NEAR_D = -1.9                # ... in front of the drift (metres beyond the wire: this side)
G_FAR = (40.6, 0.8)          # the girl, flat beyond the wire (x, d)
M_CROSS = 40.15              # where the mother goes under (her coat catches: W.SCRAP)
LIFT_G = 540.0 + (G_FAR[0] - L.FV_X) * L.fv_s(0.0)       # the wire lifted for the girl (frame x, zoom 1)
# the barb nearest the mother's crossing: the snag and, after it, the scrap
_BARBS = [x + 12.0 * K._sn(4, j) for j, x in enumerate(range(-60, 1180, 48))]
SNAG_X = min(_BARBS, key=lambda v: abs(v - (540.0 + (M_CROSS - L.FV_X) * L.fv_s(0.0))))
WIRE_PRINTS = (W.walk_prints([(40.0, -133.0), (40.0, -131.2)], "mother", 0.6, 0.3, seed=1) +
               W.walk_prints([(40.6, -133.0), (40.6, -131.4)], "girl", 0.42, 0.3, seed=2))
TROUGH_G = ((40.6, -131.35), (40.6, -130.6), (40.58, -129.7))      # crawled under the wire (map)
TROUGH_M = ((40.05, -131.15), (40.12, -130.4), (40.15, -129.4))
M_FLAT = (40.0, -131.95)     # the page: where they lie (body centres)
G_FLAT = (40.58, -129.15)


# ============================================================================ the fence view
def _crest_light(c, cam, ft):
    """The patch's near edge riding over the drift's crest (only near the crossing)."""
    x = L.search_x(ft)
    u = (x - W.CROSS[0]) / L.SWEEP_A
    half = 4.6 ** 2 - (4.5 + u * u) ** 2
    if half <= 0.0:
        return
    k = L.fv_s(-1.5)
    cx = 540.0 + (x - L.FV_X) * k
    c.save()
    L.clip_drift(c, cam)
    K.lit_patch(c, cam.xf((cx, W.drift_y(cx) - 6.0), 1.3), math.sqrt(half) * k * cam.s(1.3), 64.0 * cam.s(1.3),
                alpha=0.85)
    c.restore()


def _shadow_down(c, base, s, w, length, color, alpha=1.0):
    """A figure's long moon shadow falling toward us from its base (frame px; length in metres of
    frame at the base's scale: it runs off the bottom of the frame)."""
    x, y = base
    sk = 0.12 * length * s
    K.poly(c, [(x - w * s, y - 0.03 * s), (x + w * s, y - 0.03 * s), (x + w * 2.4 * s + sk, y + length * s),
               (x - w * 2.4 * s + sk, y + length * s)], color, alpha)


def _pose_near(t, t0, t1):
    u = clamp((t - t0) / (t1 - t0))
    if u <= 0.0:
        return "crouch", 1.0, 1.0
    if u < 1.0:
        return "drop", u, lerp(1.0, 0.25, ease("inout", u))
    return "flat", 1.0, 0.25


def _fence_near(c, t, cam):
    """Shots A, C, D: the two of them crouched in front of the drift."""
    ft = FILM_T0 + t
    moon_u = ease("inout", clamp((t - T_MOON[0]) / (T_MOON[1] - T_MOON[0])))
    lit = ease("inout", clamp((t - T_LIT[0]) / (T_LIT[1] - T_LIT[0])))
    ps = ease("out", clamp((t - T_POSTS[0]) / (T_POSTS[1] - T_POSTS[0])))
    sp = L.search_fv(ft)
    W.draw_fence(c, ft, cam, moonlit=lit, search=sp, moon_out=moon_u, posts_shadow=ps if ps > 0.0 else None,
                 under=lambda c_: L.beam_fv(c_, cam, sp))
    snow_c = lerp(K.SNOW_DIM, W.SNOW, lit)
    shade_c = lerp(lerp(snow_c, K.PAPER, 0.18), K.SHADOW, 0.85)
    L.post_shadows_on_drift(c, cam, ps, shade_c)
    _crest_light(c, cam, ft)
    rim = lerp(lerp(K.STEEL, K.NIGHT, 0.25), K.PAPER, lit)
    s = L.fv_s(NEAR_D) * cam.s(1.45)
    pm, um, hm = _pose_near(t, *T_DOWN)
    pg, ug, hg = _pose_near(t, *T_DOWN_G)
    pa = {who: cam.xf(L.fv(x, NEAR_D), 1.45) for who, x in (("mother", M_X), ("girl", G_X))}
    if ps > 0.0:
        _shadow_down(c, pa["girl"], s * 0.66, 0.24, 1.5 * hg * ps, shade_c)
        _shadow_down(c, pa["mother"], s, 0.26, 1.5 * hm * ps, shade_c)
    mg = L.back(c, "girl", pa["girl"], s, pg, ft, ug, rim=rim, rim_w=3.5)
    # her arm goes round the girl's back as she pulls her down
    reach = clamp((t - (T_DOWN[0] - 0.12)) / 0.12) * (1.0 - clamp((t - T_DOWN_G[1]) / 0.12))
    hand = None
    if reach > 0.0:
        rest = (pa["mother"][0] + 0.28 * s, pa["mother"][1] - 0.5 * s)
        hand = (lerp(rest[0], mg["nape"][0] - 0.02 * s, reach), lerp(rest[1], mg["nape"][1] + 0.02 * s, reach))
    mm = L.back(c, "mother", pa["mother"], s, pm, ft, um, rim=rim, rim_w=4.0, hand=hand)
    if pm == "crouch":
        L.back_breath(c, mm["head"], s, ft, rate=0.9, phase=0.2, stop=FILM_T0 + T_HOLD)
    if pg == "crouch":
        L.back_breath(c, mg["head"], s * 0.7, ft, rate=0.6, phase=0.05, strength=0.8)
    # the last flake of the snowfall, past her head
    if t < T_B:
        K.disc(c, (290.0 + 120.0 * t + 22.0 * math.sin(2.3 * t), 720.0 + 470.0 * t), 6.5, K.PAPER, seed=3)
        K.disc(c, (720.0 + 70.0 * t, 420.0 + 330.0 * t), 3.0, K.PAPER, seed=4, alpha=0.7)


# ---------------------------------------------------------------------------- E: under the wire
def _shot_lift(c, t):
    ft = FILM_T0 + t
    cam = W.FenceCam(1.8 + 0.05 * (t - T_E), (540.0, 1240.0))
    up = ease("out3", clamp((t - T_LIFT[0]) / (T_LIFT[1] - T_LIFT[0])))
    down = ease("inout", clamp((t - T_LOWER[0]) / (T_LOWER[1] - T_LOWER[0])))
    lift = 80.0 * up * (1.0 - down)
    cu = clamp((t - T_CRAWL[0]) / (T_CRAWL[1] - T_CRAWL[0]))
    gd = lerp(-0.6, G_FAR[1], ease("sine", cu))
    gx = lerp(G_X, G_FAR[0], cu)
    gpose = "crawl" if cu < 1.0 else "flat"
    sp = L.search_fv(ft)
    m_at, m_s = L.fv_at(cam, M_X, -0.4)
    wire_pt = cam.xf((LIFT_G, W.wire_y(4, LIFT_G, lift, LIFT_G)), 1.0)
    reach = clamp((t - T_E) / 0.12) * (1.0 - clamp((t - T_LOWER[1]) / 0.05))
    rest = (m_at[0] + 0.3 * m_s, m_at[1] - 0.25 * m_s)
    hand = (lerp(rest[0], wire_pt[0], reach), lerp(rest[1], wire_pt[1], reach)) if reach > 0.0 else None

    def girl(c_):
        L.shadow_fv(c_, cam, gx, gd, 0.25 if gpose == "flat" else 0.3, 0.16)
        p, s = L.fv_at(cam, gx, gd)
        L.back(c_, "girl", p, s, gpose, ft, (t - T_CRAWL[0]) / 0.55 if gpose == "crawl" else 1.0, rim=K.PAPER,
               rim_w=3.0)

    def under(c_):
        L.beam_fv(c_, cam, sp)
        if gd >= -0.2:
            girl(c_)

    def mid(c_):
        L.shadow_fv(c_, cam, M_X, -0.4, 1.0, 0.3)
        L.back(c_, "mother", m_at, m_s, "crouch", ft, 1.0, rim=K.PAPER, rim_w=3.5, hand=hand)
        if gd < -0.2:
            girl(c_)

    W.draw_fence(c, ft, cam, moonlit=1.0, search=sp, lift=lift, lift_x=LIFT_G, posts_shadow=1.0, under=under, mid=mid)
    L.post_shadows_on_drift(c, cam, 1.0, lerp(lerp(W.SNOW, K.PAPER, 0.18), K.SHADOW, 0.85))


# ---------------------------------------------------------------------------- I: the snag
def _shot_snag(c, t):
    ft = FILM_T0 + t
    cam = W.FenceCam(1.85, (540.0, 1240.0))
    # she crawls from d -0.5; the coat holds her at the wire (12.4-12.75); torn free she lurches on
    if t < T_SNAG:
        d = lerp(-0.5, -0.02, ease("sine", (t - T_I) / (T_SNAG - T_I)))
    elif t < T_RIP:
        d = -0.02 + sum(0.05 * math.exp(-((t - tt - 0.04) / 0.04) ** 2) for tt in T_TUGS)
    else:
        d = lerp(-0.02, 0.75, ease("out3", clamp((t - T_RIP) / 0.25)))
    x = M_CROSS
    # the wire rides on her back while she is under it; the tugs jerk it; the rip lets it spring back
    if t < T_RIP:
        under_u = clamp((d + 0.35) / 0.2)
        lift = 28.0 * under_u + sum(18.0 * math.exp(-((t - tt - 0.04) / 0.05) ** 2) for tt in T_TUGS)
        if t >= T_SNAG:
            lift += 8.0 * clamp((t - T_SNAG) / 0.1)
    else:
        q = t - T_RIP
        lift = 30.0 * math.exp(-5.0 * q) * math.cos(2.0 * math.pi * 7.0 * q)
    def mother(c_):
        L.shadow_fv(c_, cam, x, d, 0.3, 0.26)
        p, s = L.fv_at(cam, x, d)
        if T_SNAG <= t < T_RIP:
            # the coat's hem caught on the barb, stretched back to it
            b = cam.xf((SNAG_X, W.wire_y(4, SNAG_X, lift, SNAG_X)), 1.0)
            K.poly(c_, [b, (p[0] - 0.12 * s, p[1] - 0.28 * s), (p[0] + 0.14 * s, p[1] - 0.3 * s)], K.INK)
        L.back(c_, "mother", p, s, "crawl", ft, (t - T_I) / 0.6, rim=K.PAPER, rim_w=3.5)

    def under(c_):
        L.shadow_fv(c_, cam, G_FAR[0], G_FAR[1], 0.25, 0.16)
        p, s = L.fv_at(cam, *G_FAR)
        L.back(c_, "girl", p, s, "flat", ft, 1.0, rim=K.PAPER, rim_w=3.0)
        if d >= -0.3:
            mother(c_)

    def mid(c_):
        if d < -0.3:
            mother(c_)

    W.draw_fence(c, ft, cam, moonlit=1.0, search=L.search_fv(ft), lift=lift, lift_x=SNAG_X, posts_shadow=1.0,
                 under=under, mid=mid, scrap=(SNAG_X, W.wire_y(4, SNAG_X, lift, SNAG_X) + 2.0) if t >= T_RIP else None)
    L.post_shadows_on_drift(c, cam, 1.0, lerp(lerp(W.SNOW, K.PAPER, 0.18), K.SHADOW, 0.85))


# ---------------------------------------------------------------------------- K: into the zone
def _runner(who, t):
    """(x, d) of a runner at scene time t: up from the snow beyond the wire and away north."""
    u = clamp((t - T_K) / 2.0)
    d = lerp(0.9, 9.0, u * (0.65 + 0.35 * u))
    x = lerp(M_CROSS, 39.0, u) + (0.55 if who == "girl" else 0.0)
    return x, d


def _run_prints(who, t):
    step = 0.62 if who == "mother" else 0.44
    _, d_now = _runner(who, t)
    out, d, i = [], 1.2, 0
    while d < d_now - 0.3:
        u = 0.0
        # invert d(u) for the print's x (a few Newton-free steps are plenty)
        lo, hi = 0.0, 1.0
        for _ in range(18):
            u = (lo + hi) / 2.0
            if lerp(0.9, 9.0, u * (0.65 + 0.35 * u)) < d:
                lo = u
            else:
                hi = u
        x = lerp(M_CROSS, 39.0, u) + (0.55 if who == "girl" else 0.0) + (0.09 if i % 2 else -0.09)
        out.append((x, d))
        d += step
        i += 1
    return out


def _shot_run(c, t):
    ft = FILM_T0 + t
    cam = W.FenceCam(1.0, (540.0, 1300.0))
    print_c = lerp(W.SNOW, K.SHADOW, 0.85)
    sp = L.search_fv(ft)

    def under(c_):
        L.beam_fv(c_, cam, sp)
        for who in ("mother", "girl"):
            for x, d in _run_prints(who, t):
                p, s = L.fv_at(cam, x, d)
                K.ellipse(c_, p, (0.08 if who == "mother" else 0.06) * s, 0.035 * s, print_c)
        marks = {}
        for who in ("girl", "mother"):
            x, d = _runner(who, t)
            L.shadow_fv(c_, cam, x, d, 1.7 if who == "mother" else 1.15, 0.17 if who == "mother" else 0.12)
            p, s = L.fv_at(cam, x, d)
            ph = (t - T_K) / (0.66 if who == "mother" else 0.48)
            hand = None
            if who == "mother":
                gp, gs = L.fv_at(cam, *_runner("girl", t))
                hand = (gp[0] - 0.16 * gs, gp[1] - 0.6 * gs)
            marks[who] = L.back(c_, who, p, s, "run", ft, ph, rim=K.PAPER, rim_w=2.5, hand=hand)

    W.draw_fence(c, ft, cam, moonlit=1.0, search=sp, posts_shadow=1.0, under=under,
                 scrap=(SNAG_X, W.wire_y(4, SNAG_X) + 2.0))
    L.post_shadows_on_drift(c, cam, 1.0, lerp(lerp(W.SNOW, K.PAPER, 0.18), K.SHADOW, 0.85))


# ============================================================================ close-ups
def _drift_fg(c, color, y0=1420.0, amp=60.0, seed=0.0):
    pts = [(x, y0 - amp * math.exp(-((x - 300.0) / 420.0) ** 2) + 18.0 * math.sin(x * 0.012 + seed))
           for x in range(-40, 1141, 40)]
    K.poly(c, pts + [(1140.0, 1980.0), (-40.0, 1980.0)], color)


def _night_sky(c, ft, moon_u, moon_at=(830.0, 330.0)):
    K.fill(c, K.NIGHT)
    K.stars(c, ft, y1=1000.0)
    K.moon(c, moon_at, r=92.0)
    if moon_u < 1.0:
        cp = (moon_at[0] - 640.0 * ease("inout", moon_u) + 40.0, moon_at[1] + 52.0)
        if moon_u > 0.0:     # the cloud's edge silvers as the moon slides out
            K.cloud(c, (cp[0] + 10.0, cp[1] - 8.0), 760.0, 170.0, K.PAPER, seed=4, alpha=0.7 * clamp(moon_u * 6.0))
        K.cloud(c, cp, 760.0, 170.0, lerp(K.NIGHT, K.STEEL, 0.55), seed=4)


def _cu_mitten(c, t):
    """B: she holds out her mitten; nothing falls; she looks up."""
    ft = FILM_T0 + t
    up = ease("inout", clamp((t - T_UP) / 0.18))
    silver = clamp((t - 2.82) / 0.18)
    _night_sky(c, ft, 0.06 * silver)
    rim = lerp(lerp(K.STEEL, K.NIGHT, 0.2), K.PAPER, 0.25 + 0.6 * silver)
    at = (380.0, 1250.0)
    c.save()
    c.translate(at[0] + 20.0, at[1] - 300.0)
    c.rotate(math.radians(-9.0 * up))           # her head tips back to the sky
    c.translate(-(at[0] + 20.0), -(at[1] - 300.0))
    m = F.mother(c, at, 1.2, look=lerp(0.55, 0.35, up), down=lerp(0.65, -1.0, up), t=ft, rim=rim, light=(0.55, -0.85),
                 rim_w=5.0)
    c.restore()
    # breath from her lips, one puff, drifting up
    a = clamp((t - 2.15) / 0.8)
    if 0.0 < a < 1.0:
        mp = m["mouth"]
        K.disc(c, (mp[0] + 40.0 + 90.0 * a, mp[1] - 10.0 - 60.0 * a), 14.0 + 36.0 * a, K.PAPER, seed=7,
               alpha=0.35 * (1.0 - a) ** 1.3)
    # the mitten held out, palm up, then curling a little as she gives up on it
    curl = 0.35 * clamp((t - 2.55) / 0.2)
    F.mitten(c, (520.0, 1240.0), (880.0, 1150.0 + 30.0 * up), 1.15, rim=rim, light=(0.55, -0.85), thumb=0.8,
             curl=curl)
    _drift_fg(c, lerp(K.SNOW_DIM, K.STEEL, 0.25), 1430.0, 50.0)


def _cu_hush(c, t):
    """G: the mitten pressed to her lips."""
    ft = FILM_T0 + t
    _night_sky(c, ft, 1.0)
    m = F.mother(c, (380.0, 1250.0), 1.2, look=0.95, fear=0.35, t=ft, rim=K.PAPER, light=(0.55, -0.85), rim_w=5.0)
    mp = m["mouth"]
    k = ease("out3", clamp((t - T_G) / 0.15))
    F.mitten(c, (mp[0] + 90.0, mp[1] + 640.0), (mp[0] + 8.0, lerp(mp[1] + 240.0, mp[1] - 10.0, k)), 1.0, rim=K.PAPER,
             light=(0.55, -0.85), thumb=0.6, flip=True)
    _drift_fg(c, lerp(W.SNOW, K.PAPER, 0.15), 1450.0, 50.0)


def _cu_box(c, t):
    """F: the music box springs open in the snow; the mitten slaps it shut."""
    ft = FILM_T0 + t
    jolt = 7.0 if T_SLAP <= t < T_SLAP + 0.05 else 0.0
    c.save()
    c.translate(0.0, jolt)
    # beyond: the zone's snow up to the woods' line under the night
    K.fill(c, K.NIGHT)
    K.stars(c, ft, y1=330.0)
    for i in range(22):
        x = -40.0 + 54.0 * i + 14.0 * K._sn(i, 5)
        W.spruce_side(c, (x, 380.0), 110.0 + 45.0 * K._sn(i, 6), 46.0 + 12.0 * K._sn(i, 7), lerp(K.STEEL, K.INK, 0.3),
                      seed=i)
    K.poly(c, [(-40.0, 378.0), (1120.0, 378.0), (1120.0, 1980.0), (-40.0, 1980.0)], lerp(W.SNOW, K.STEEL, 0.3))
    K.poly(c, [(-40.0, 620.0), (1120.0, 610.0), (1120.0, 1980.0), (-40.0, 1980.0)], W.SNOW)
    # the near snow the box lies on
    K.poly(c, [(x, 1400.0 + 16.0 * math.sin(x * 0.017)) for x in range(-40, 1141, 40)] + [(1140.0, 1980.0), (-40.0, 1980.0)],
           lerp(W.SNOW, K.PAPER, 0.15))
    # the girl lying beyond it: her coat's hem and the pocket it slipped from, at the right edge
    hem = [(1120.0, 1030.0), (1010.0, 1050.0), (930.0, 1110.0), (880.0, 1200.0), (862.0, 1300.0), (872.0, 1400.0),
           (915.0, 1470.0), (990.0, 1505.0), (1120.0, 1515.0)]
    K.poly(c, [(x + 3.0, y - 4.0) for x, y in hem], K.PAPER)
    K.poly(c, hem, K.INK)
    K.band(c, [(905.0, 1260.0), (980.0, 1236.0), (1060.0, 1240.0)], K.STEEL, 4.0, seed=2)
    # the bottom strand across the top of the shot
    ys = lambda x: 540.0 + 34.0 * math.sin(math.pi * (x + 120.0) / 1400.0)
    K.band(c, [(x, ys(x)) for x in range(-40, 1141, 60)], K.INK, 12.0, seed=9)
    for bx in (60.0, 470.0, 880.0):
        by, s = ys(bx), 26.0
        K.band(c, [(bx - s, by - s), (bx + s, by + s)], K.INK, 8.5, seed=1)
        K.band(c, [(bx - s, by + s), (bx + s, by - s)], K.INK, 8.5, seed=2)
    # the box: closed, then it springs open
    s = 2.1
    corner = (250.0, 1440.0)
    open_u = ease("outback", clamp((t - T_OPEN) / 0.14)) * (1.0 - clamp((t - (T_SLAP - 0.04)) / 0.04))
    hop = 12.0 * math.sin(math.pi * clamp((t - T_OPEN) / 0.12))
    F.music_box(c, (corner[0], corner[1] - hop), s, open_u=open_u, t=ft, spin=9.0 * max(0.0, t - T_OPEN), rim=K.PAPER)
    top = (corner[0] + 110.0 * s, corner[1] - 110.0 * s)
    # each note: a ring of paper light off the box
    for tn in NOTES:
        a = clamp((t - tn) / 0.3)
        if 0.0 < a < 1.0 and t < T_SLAP:
            K.ellipse(c, (top[0], top[1] - 40.0), 140.0 + 300.0 * a, 46.0 + 100.0 * a, K.PAPER, alpha=0.25 * (1.0 - a))
    # the mitten comes in under the wire and slaps it shut
    k = clamp((t - 8.62) / 0.3)
    if k > 0.0:
        hover = (top[0] + 30.0, top[1] - 230.0)
        press = (top[0] + 40.0, top[1] - 8.0)
        if t < T_SLAP - 0.06:
            tip = (lerp(-160.0, hover[0], ease("out3", k)), lerp(1900.0, hover[1], ease("out3", k)))
        else:
            v = clamp((t - (T_SLAP - 0.06)) / 0.06)
            tip = (lerp(hover[0], press[0], v), lerp(hover[1], press[1], v))
        F.mitten(c, (tip[0] - 460.0, tip[1] + 560.0), tip, 1.35, rim=K.PAPER, light=(0.8, -0.6), thumb=0.7, curl=0.15)
    # the slap kicks up snow
    a = clamp((t - T_SLAP) / 0.25)
    if 0.0 < a < 1.0:
        for i in range(8):
            ang = math.pi * (0.08 + 0.84 * i / 7.0)
            r = 70.0 + 190.0 * ease("out3", a)
            K.disc(c, (top[0] - math.cos(ang) * r * 1.5, corner[1] - math.sin(ang) * r * 0.6), 11.0 * (1.0 - a) + 3.0,
                   K.PAPER, seed=i, alpha=0.8 * (1.0 - a))
    c.restore()


def _cu_scrap(c, t):
    """J: the scrap of her coat on the barb, stirring; the wire still quivering."""
    ft = FILM_T0 + t
    K.fill(c, W.SNOW)
    # a post's long shadow across the snow
    K.poly(c, [(930.0, -20.0), (1060.0, -20.0), (60.0, 1980.0), (-150.0, 1980.0)], lerp(W.SNOW, K.SHADOW, 0.6))
    q = t - T_RIP
    wob = 24.0 * math.exp(-3.5 * q) * math.sin(2.0 * math.pi * 6.0 * q)
    ys = lambda x: 760.0 + 46.0 * math.sin(math.pi * (x + 260.0) / 1600.0) + wob * math.exp(-((x - 540.0) / 420.0) ** 2)
    # the strand's own shadow on the snow below it
    K.band(c, [(x, ys(x) + 330.0) for x in range(-40, 1141, 30)], lerp(W.SNOW, K.SHADOW, 0.6), 10.0, seed=6)
    K.band(c, [(x, ys(x)) for x in range(-40, 1141, 30)], K.INK, 13.0, seed=5)
    for bx in (120.0, 540.0, 960.0):
        by, s = ys(bx), 30.0
        K.band(c, [(bx - s, by - s), (bx + s, by + s)], K.INK, 9.5, seed=1)
        K.band(c, [(bx - s, by + s), (bx + s, by - s)], K.INK, 9.5, seed=2)
    F.scrap(c, (548.0, ys(548.0) + 18.0), 1.7, t=ft, wind=1.2, rim=K.PAPER)


# ============================================================================ the page
PRINT_C = lerp(W.SHADOW, K.INK, 0.3)      # the prints at the page's smaller sizes


def approach_prints(c, cam, color=W.SHADOW):
    """The trail they came by (s01), half filled by the snowfall, the older the more."""
    for n0, n1, cov in ((-138.0, -133.2, 0.08), (-144.0, -138.0, 0.2), (-152.0, -144.0, 0.35), (-170.0, -152.0, 0.5)):
        W.draw_prints(c, cam, [q for q in APPROACH if n0 <= q[1] < n1], cover=cov, page=W.SNOW, color=color)


def woods_edge(c, cam, n_edge=-117.4):
    """The woods' edge along the top of the page: one cut-paper canopy with a fringe of spruce tips,
    and the path's mouth where their trail goes in."""
    x0, x1, n0, n1 = cam.bounds(4.0)
    pts, i, x = [], 0, x0
    while x <= x1:
        tip = (1.3 if i % 2 == 0 else 0.35) + 0.3 * K._sn(i, 77)
        pts.append((x, n_edge - tip + 0.6 * math.sin(x * 0.21)))
        x += 0.7
        i += 1
    K.poly(c, cam.pts(pts + [(x1, n1 + 5.0), (x0, n1 + 5.0)]), K.INK)
    K.band(c, cam.pts([(39.3, -120.5), (38.7, -117.0), (37.6, -113.0), (36.6, -108.0)]), W.SNOW, 2.4 * cam.ppm,
           seed=23, taper=(1.0, 0.7))


def trough_top(c, cam, pts, w):
    K.band(c, cam.pts(pts), lerp(W.SNOW, W.SHADOW, 0.7), w * cam.ppm, seed=31)


def _prone(c, cam, who, at, ft, shade_c):
    p = cam.px(at)
    C.top_prone(c, who, (p[0], p[1] + 0.12 * cam.ppm), -90.0, cam.ppm, ft, color=shade_c)    # the moon shadow, south
    C.top_prone(c, who, p, -90.0, cam.ppm, ft)


def _scarf_top(c, cam, at, ft, glow=0.0):
    """The girl's red scarf from above, round her neck, its end lying across her shoulder."""
    Lg = C.HEIGHT_M["girl"]
    p = cam.px(at)
    knot = C._xf([(0.31 * Lg + 0.04 * math.cos(6.283 * i / 14), 0.1 * math.sin(6.283 * i / 14)) for i in range(14)], p,
                 -90.0, cam.ppm)
    tail = C._xf([(0.31 * Lg, 0.04), (0.31 * Lg, 0.09), (0.12 * Lg, 0.2 + 0.01 * math.sin(ft * 5.0)),
                  (0.1 * Lg, 0.15)], p, -90.0, cam.ppm)
    if glow > 0.0:
        K.glow(c, cam.px((at[0], at[1] + 0.31 * Lg)), 0.55 * cam.ppm, 0.7 * glow, ft, color=K.RED)
    K.polys(c, [knot, tail], K.RED)


def _page_light(c, t):
    """H: the patch slides over them on the page."""
    ft = FILM_T0 + t
    cam = W.Plan(40.3, -130.5, 128.0)
    shade_c = lerp(W.SNOW, W.SHADOW, 0.55)
    W.draw_page(c, cam, ft, moonlit=1.0, prints=(), fence_on=False, scrap=False, shadows=0.0)
    # the searchlight: the beam from the tower (off the left edge) to its patch, here drawn for the
    # page close (r 2.4 m about the wire, so it crosses them in the shot)
    sp = (L.search_x(ft), -129.6)
    d = (sp[0] - W.TOWER[0], sp[1] - W.TOWER[1])
    dl = math.hypot(*d) or 1.0
    side = (-d[1] / dl * 2.2, d[0] / dl * 2.2)
    K.beam(c, cam.px(W.TOWER), cam.px((sp[0] + side[0], sp[1] + side[1])), cam.px((sp[0] - side[0], sp[1] - side[1])),
           K.PAPER, alpha=0.14)
    W.search_patch(c, cam, sp, 2.4, alpha=0.88, heading=L.search_heading(ft))
    approach_prints(c, cam)
    W.draw_prints(c, cam, WIRE_PRINTS, page=W.SNOW, color=W.SHADOW)
    trough_top(c, cam, TROUGH_G, 0.32)
    W.draw_fence_top(c, cam, ft, shade_c, scrap=False)
    for i in range(-24, 25):        # the barbs, seen from above
        p = cam.px((40.3 + 0.24 * i + 0.03 * K._sn(i, 4), W.FENCE_N))
        r = 0.07 * cam.ppm
        K.band(c, [(p[0] - r, p[1] - r), (p[0] + r, p[1] + r)], K.INK, 2.6, seed=i)
        K.band(c, [(p[0] - r, p[1] + r), (p[0] + r, p[1] - r)], K.INK, 2.6, seed=i + 50)
    _prone(c, cam, "mother", M_FLAT, ft, shade_c)
    _prone(c, cam, "girl", G_FLAT, ft, shade_c)
    # the scarf burns in the light, and with each heartbeat
    lx = (G_FLAT[0] - sp[0]) / (2.4 * 1.25)
    ln = (G_FLAT[1] + 0.35 - sp[1]) / 2.4
    lit = clamp(1.4 * (1.0 - math.hypot(lx, ln)))
    beat = sum(math.exp(-((t - tb - 0.06) / 0.07) ** 2) for tb in T_BEATS)
    _scarf_top(c, cam, G_FLAT, ft, glow=lit * (0.6 + 0.6 * beat))


def _page_end(c, t):
    """L: the page, from above, as they left it."""
    ft = FILM_T0 + t
    u = ease("inout", clamp((t - T_L) / 2.0))
    cam = W.Plan(32.8, -134.0, lerp(48.0, 50.0, u))           # the tower left, their trail right, the woods' edge
    shade_c = lerp(W.SNOW, W.SHADOW, 0.55)
    # at this size the woods' long shadows would flood the zone: the page keeps the tower's and the posts'
    W.draw_page(c, cam, ft, moonlit=1.0, prints=(), scrap=False, woods_on=False, shadows=0.0)
    woods_edge(c, cam)
    # the beam far off west
    sp = (L.search_x(ft), L.search_n(ft))
    d = (sp[0] - W.TOWER[0], sp[1] - W.TOWER[1])
    dl = math.hypot(*d) or 1.0
    side = (-d[1] / dl * 3.6, d[0] / dl * 3.6)
    K.beam(c, cam.px(W.TOWER), cam.px((sp[0] + side[0], sp[1] + side[1])), cam.px((sp[0] - side[0], sp[1] - side[1])),
           K.PAPER, alpha=0.16)
    W.search_patch(c, cam, sp, 4.2, alpha=0.8, heading=L.search_heading(ft))
    W.draw_tower_top(c, cam, shade_c)
    W.draw_fence_top(c, cam, ft, shade_c, scrap=False)
    approach_prints(c, cam, PRINT_C)
    W.draw_prints(c, cam, W.FENCE_PRINTS, page=W.SNOW, color=PRINT_C)
    trough_top(c, cam, TROUGH_G, 0.32)
    trough_top(c, cam, TROUGH_M, 0.42)
    # the scrap on the wire, a fleck the page keeps
    p = cam.px(W.SCRAP)
    r = 0.4 * cam.ppm
    K.poly(c, [(p[0] - r * 0.6, p[1] - r * 0.3), (p[0] + r * 0.7, p[1] - r * 0.5), (p[0] + r * 0.4, p[1] + r),
               (p[0] - r * 0.2, p[1] + r * 0.7)], K.INK)


# ---------------------------------------------------------------------------- render
CAM_A = lambda t: W.FenceCam(lerp(1.0, 1.03, t / 2.0), (540.0, 1400.0))
CAM_C = lambda t: W.FenceCam(lerp(1.15, 1.2, t - T_C), (540.0, 1450.0))
CAM_D = lambda t: W.FenceCam(lerp(1.0, 1.03, (t - T_D) / 2.0), (540.0, 1400.0))


def render(f, t, T):
    K.scene_setup(f, K.NIGHT)
    with f.screen() as c:
        if t < T_B:
            _fence_near(c, t, CAM_A(t))
        elif t < T_C:
            _cu_mitten(c, t)
        elif t < T_D:
            _fence_near(c, t, CAM_C(t))
        elif t < T_E:
            _fence_near(c, t, CAM_D(t))
        elif t < T_F:
            _shot_lift(c, t)
        elif t < T_G:
            _cu_box(c, t)
        elif t < T_H:
            _cu_hush(c, t)
        elif t < T_I:
            _page_light(c, t)
        elif t < T_J:
            _shot_snag(c, t)
        elif t < T_K:
            _cu_scrap(c, t)
        elif t < T_L:
            _shot_run(c, t)
        else:
            _page_end(c, t)


def motion_blur(t, T):
    return 1


def cues(T):
    out = [
        Cue(0.0, "wind_low", gain_db=-28, dur=T, dc="a faint winter wind over the snow; the snowfall is over"),
        Cue(0.0, "searchlight_hum", gain_db=-26, dur=T,
            dc="the searchlight's motor, far: it swells as the beam passes them (5.0, 11.0) and fades as it swings away "
               "west (from 13.0)"),
        Cue(0.0, "her_breath", gain_db=-26, dur=T_HOLD, dc="the mother's quiet, frightened breathing; it stops at 3.3"),
        Cue(0.0, "girl_breath", gain_db=-30, dur=T_DOWN_G[0], dc="the girl's quick little breaths"),
        Cue(T_B, "mitten_rustle", gain_db=-24, dur=0.6, dc="wool rustle: the mitten held out to the sky"),
        Cue(T_MOON[0], "moon_reveal", gain_db=-20, dur=2.0, dc="a cold high string harmonic: the moon comes out"),
        Cue(T_HOLD, "held_breath", gain_db=-18, dc="her breath catches and stops: a held breath"),
        Cue(T_DOWN[0], "snow_thump", gain_db=-16, pan=-0.05, dc="two bodies dropping flat into soft snow"),
        Cue(4.7, "beam_pass", gain_db=-18, dur=1.2, dc="the beam passes over them: the motor swells, a faint electric sizzle"),
        Cue(T_LIFT[0], "wire_creak", gain_db=-16, dur=1.5, dc="barbed wire lifted: a taut metallic creak"),
        Cue(T_CRAWL[0], "snow_crawl", gain_db=-22, dur=T_CRAWL[1] - T_CRAWL[0], dc="a child crawling through snow"),
        Cue(T_LOWER[0], "wire_creak", gain_db=-22, dur=0.3, dc="the wire let down gently"),
        Cue(T_CLANK, "motor_clank", gain_db=-12, pan=0.5, dc="the searchlight reverses at the end of its swing: a heavy "
                                                             "metal clank, far, echoing"),
    ]
    for i, tn in enumerate(NOTES):
        out.append(Cue(tn, "music_box", gain_db=-10, note=i,
                       dc="a music box note (E5, C5, D5): the lullaby's first three notes, loud in the silence"))
    out += [
        Cue(T_SLAP, "snap", gain_db=-8, dc="a mitten slaps the lid shut: a muffled wooden snap; then silence"),
        Cue(T_BEATS[0], "heartbeat", gain_db=-10, dc="a heartbeat, deep and close"),
        Cue(T_BEATS[1], "heartbeat", gain_db=-10, dc="a heartbeat, deep and close"),
        Cue(T_I, "snow_crawl", gain_db=-20, dur=0.4, dc="crawling under the wire"),
        Cue(T_SNAG, "wire_snag", gain_db=-14, dc="barbs catching wool: the wire jerks"),
        Cue(T_TUGS[0], "wire_twang", gain_db=-16, dc="the wire jerks as she tugs"),
        Cue(T_TUGS[1], "wire_twang", gain_db=-15, dc="the wire jerks as she tugs"),
        Cue(T_RIP, "rip", gain_db=-6, dc="a short, sharp cloth rip"),
        Cue(T_RIP + 0.03, "wire_twang", gain_db=-12, dur=1.0, dc="the wire springs back and quivers"),
        Cue(T_J, "wind_gust", gain_db=-22, dur=1.0, dc="a breath of wind: the scrap stirs on the barb"),
        Cue(T_K, "run_steps", gain_db=-14, dur=2.0,
            dc="running in snow, two rhythms: hers every 0.33 s, the girl's every 0.24 s, receding"),
        Cue(T_K, "her_breath", gain_db=-24, dur=2.0, dc="her running breath, receding"),
        Cue(T_L, "page_tone", gain_db=-22, dur=2.0, dc="a still, cold sustained tone over the page; the motor far off"),
    ]
    return out
