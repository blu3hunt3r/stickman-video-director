"""s09 CHOICE (film 122-136, 14 s): her eyes; the split: the way out, the drowning man; she turns
to go; the girl holds out her scarf; she takes it.

  A  0.0- 2.0  CU in the reeds: her profile, eyes wide, holding her breath; the girl beside her.
               Her heart thuds (PAPER rings).
  B  2.0- 6.0  The split, a horizontal mirror: above, the way out (the river upstream, white all
               across under the searchlight, the farmhouse light); below, the hole as she sees it,
               his hands clawing up toward her, one slipping; between them her eyes, going up,
               down, up. The rings thud through both halves.
  C  6.0- 8.7  The bank view: she rises, takes the girl's hand, turns upstream (left) and goes: one
               step, two; the girl doesn't move; their arms stretch taut between them. The girl
               is looking at the hole.
  D  8.7- 9.7  The hole as she saw it: his west glove drags to the edge and goes under.
  E  9.7-12.2  CU the girl: she unwinds her red scarf and holds it up to her mother.
  F 12.2-14.0  CU the mother: she looks at the scarf, at the hole, and takes it. Her heart stops
               thudding. Last frame: her mitten closing on the red.
"""
import math

from engine import bass
from engine.core import clamp, ease, hash01, lerp
from engine.timing import Cue
from films.thin_ice import cast as C
from films.thin_ice import faces as F
from films.thin_ice import kit as K
from films.thin_ice import world as W
from films.thin_ice.scenes import _lib_dir as L

SID = "s09"
FILM_T0 = K.film_start(SID)

T_SPLIT = 2.0
T_UP1 = 2.45                  # her eyes go up: the way out
T_DOWN = 3.75                 # ... down: the hole
T_SLIP = 4.35                 # a glove slips back, and grips again
T_UP2 = 5.15                  # ... up again
T_LIDS = 5.65                 # her eyes narrow: she has decided
T_BANK = 6.0
T_RISE = (6.12, 6.7)
T_TAKE = 6.5                  # her hand finds the girl's
T_TURN = 6.86                 # she turns upstream
T_STEPS = (7.0, 7.95)         # two steps; the arms go taut at the end of the second
T_TAUT = 7.88
T_LOOK = 8.05                 # the girl's look to the hole
T_HOLE = 8.7
T_UNDER = (8.86, 9.42)        # his west glove: to the edge, and under
T_GIRL = 9.7
T_UNWIND = (9.88, 10.86)
T_OFFER = (10.9, 11.45)
T_MOTHER = 12.2
T_SEE = 12.32                 # she looks at the scarf ...
T_HOLE_LOOK = 12.86           # ... at the hole ...
T_GRAB = (13.12, 13.45)       # ... and takes it
HEART_BPM = 96.0
HEART_STOP = 13.45

PRINTS = W.prints_before(SID)
HOLES = W.holes_before(SID)


# ============================================================================ small things
def heart(c, p, t, alpha=0.32, r1=560.0, width=9.0, stop=HEART_STOP):
    """Her heart: PAPER rings thudding out of p, lub-dub at HEART_BPM (beats at t = k * 0.625);
    none born after `stop`."""
    beat = 60.0 / HEART_BPM
    life = 1.3
    for k in range(int(math.floor((t - life) / beat)) - 1, int(math.floor(t / beat)) + 1):
        for j, off in enumerate((0.0, 0.24)):
            t0 = k * beat + off
            if t0 < 0.0 or t0 > stop:
                continue
            a = (t - t0) / life
            if not 0.0 <= a <= 0.93:
                continue
            r = lerp(46.0, r1, ease("out3", a))
            w = width * max(0.3, (1.0 - a) ** 1.3) * (1.0 if j == 0 else 0.6)
            bass.ring(c, p, r, w, K.PAPER, seed=k * 7 + j, n=72, alpha=alpha)


def puff(c, mouth, t, t0, facing=1, s=1.0, life=1.4, alpha=0.4, seed=0):
    """One long breath let out (after holding it): a shaky puff drifting forward and up."""
    a = (t - t0) / life
    if not 0.0 <= a < 1.0:
        return
    for lobe in range(4):
        g = ease("out3", clamp(a * 1.15 - 0.05 * lobe))
        r = s * (8.0 + 30.0 * g) * (0.8 + 0.3 * hash01(seed, lobe))
        x = mouth[0] + facing * s * (10.0 + 90.0 * g + 14.0 * lobe) + s * 3.0 * math.sin(t * 40.0 + lobe)
        y = mouth[1] - s * (4.0 + 50.0 * g + 8.0 * (lobe - 1.5))
        K.dot(c, (x, y), r, K.PAPER, seed=seed * 31 + lobe, alpha=alpha * (1.0 - a) ** 1.4)


def reed_blades(c, t, specs, color=K.INK, rim=None):
    """Close-up reeds: (x_base, y_base, height, lean, width, seed) blades in frame px, swaying."""
    for (x, y, h, lean, w, seed) in specs:
        sway = 14.0 * math.sin(t * (1.1 + 0.4 * hash01(seed, 1)) + seed)
        tip = (x + lean * h + sway, y - h)
        mid = (x + 0.45 * lean * h + 0.4 * sway + 6.0 * K._sn(seed, 2), y - 0.5 * h)
        if rim is not None:
            K.band(c, [(x + 3.0, y), (mid[0] + 3.0, mid[1] - 3.0), (tip[0] + 2.0, tip[1] - 3.0)], rim, w, seed=seed,
                   taper=(1.0, 0.12), alpha=0.7)
        K.band(c, [(x, y), mid, tip], color, w, seed=seed, taper=(1.0, 0.12))


def _blade_specs(seed, n, x0, x1, y, h0, h1, w0, w1, lean=0.12):
    return [(x0 + (x1 - x0) * hash01(seed, i), y + 40.0 * hash01(seed, i, 2), lerp(h0, h1, hash01(seed, i, 3)),
             lean * K._sn(seed, i, 4), lerp(w0, w1, hash01(seed, i, 5)), seed * 100 + i) for i in range(n)]


REEDS_A_BACK = _blade_specs(3, 26, -40.0, 1120.0, 1560.0, 260.0, 520.0, 7.0, 12.0)
REEDS_A_FRONT = _blade_specs(4, 12, -60.0, 1140.0, 1960.0, 520.0, 980.0, 16.0, 26.0, lean=0.08)
REEDS_A_CROSS = [(560.0, 1960.0, 1250.0, -0.06, 14.0, 901), (1000.0, 1960.0, 1500.0, -0.1, 16.0, 902),
                 (90.0, 1960.0, 1150.0, 0.12, 18.0, 903)]


def _backdrop_cu(c, t, horizon=860.0, band=(950.0, 995.0), hole_x=930.0, facing=1):
    """The close-ups' world behind them: the night, the far bank's treeline, the white river with
    the black band across it and (facing them) the hole with him in it, small and far."""
    ft = FILM_T0 + t
    K.fill(c, K.NIGHT)
    K.stars(c, ft, y1=horizon - 140.0)
    # the far bank and its spruces
    for i in range(16):
        x = -40.0 + 75.0 * i + 30.0 * K._sn(i, 61)
        h = 120.0 + 90.0 * hash01(i, 62)
        W.spruce_side(c, (x, horizon + 4.0), h, h * 0.42, lerp(W.STEEL, K.NIGHT, 0.2), seed=i)
    K.poly(c, [(-60.0, horizon), (1140.0, horizon - 6.0), (1140.0, horizon + 26.0), (-60.0, horizon + 30.0)],
           lerp(W.SHADOW, K.NIGHT, 0.3))
    # the river: white ice, the band
    K.poly(c, [(-60.0, horizon + 28.0), (1140.0, horizon + 24.0), (1140.0, 2000.0), (-60.0, 2000.0)], W.ICE)
    K.poly(c, [(-60.0, band[0] + 6.0), (1140.0, band[0] - 6.0), (1140.0, band[1] - 4.0), (-60.0, band[1] + 4.0)], W.THIN)
    if hole_x is not None:
        y = 0.5 * (band[0] + band[1]) + 6.0
        K.ellipse(c, (hole_x, y), 64.0, 13.0, K.WATER)
        bob = 1.5 * math.sin(ft * 3.1)
        K.ellipse(c, (hole_x - 4.0 * facing, y - 9.0 + bob), 9.0, 10.0, K.INK)            # his head
        K.band(c, [(hole_x - 26.0, y + 6.0), (hole_x - 44.0, y + 12.0)], K.INK, 4.0, seed=1)
        K.band(c, [(hole_x + 18.0, y + 6.0), (hole_x + 38.0, y + 11.0)], K.INK, 4.0, seed=2)


def bust_base(c, at, s, x0, x1, y0, facing=1, rim=None):
    """The rest of a close-up's body below its coat's edge (face units x0..x1 at y0), down out of
    frame."""
    X = lambda u: at[0] + facing * (u - 400.0) * s
    yb = at[1] + (y0 - 860.0 if x1 > 560 else y0 - 640.0) * s
    pts = [(X(x0), yb - 2.0), (X(x1), yb - 2.0), (X(x1 + 40.0), 2000.0), (X(x0 - 40.0), 2000.0)]
    K.poly(c, pts, K.INK)


# ============================================================================ A: in the reeds (0-2)
def _reeds_cu(c, t):
    ft = FILM_T0 + t
    _backdrop_cu(c, t)
    reed_blades(c, t, REEDS_A_BACK, color=lerp(K.INK, W.STEEL, 0.25))
    heart(c, (190.0, 1330.0), t, alpha=0.28)
    flick = ease("inout", clamp((t - 1.55) / 0.14)) * (1.0 - ease("inout", clamp((t - 1.88) / 0.1)))
    bust_base(c, (330.0, 1190.0), 0.98, -60.0, 600.0, 1040.0)
    m = F.mother(c, (330.0, 1190.0), 0.98, look=lerp(0.88, -0.6, flick), fear=1.0, t=ft, rim=K.PAPER,
                 light=(0.55, -0.85), rim_w=5.0)
    K.poly(c, [(400.0, 1780.0), (960.0, 1780.0), (1000.0, 2000.0), (360.0, 2000.0)], K.INK)
    g = F.girl(c, (770.0, 1560.0), 0.84, look=0.95, fear=0.35, t=ft, rim=K.PAPER, light=(0.55, -0.85), rim_w=4.0,
               scarf=1.0)
    # her held breath let go, shaking; the girl's small quick ones
    puff(c, m["mouth"], t, 1.3, facing=1, s=1.1, seed=4)
    K.breath(c, g["mouth"], t, rate=1.6, facing=1, s=0.9, phase=0.15, strength=0.75, seed=3)
    reed_blades(c, t, REEDS_A_FRONT)
    reed_blades(c, t, REEDS_A_CROSS)


# ============================================================================ B: the split (2-6)
STRIP_S = 0.8                                  # the eyes strip: face units -> px
STRIP_TOP, STRIP_BOT = 960.0 - 250.0 * STRIP_S, 960.0 + 260.0 * STRIP_S
CAM_WAY = W.Dio(12.5, -2.8, 70.0, eye=6.34)    # upstream from high over the trail: the river to the light
CAM_HOLE = W.Plan(13.3, 10.6, 260.0, rot=180.0)   # the hole as she sees it (south up), drawn 600 px low
HOLE_DY = 600.0


def _farm_window(cam):
    d = W.SECTION_X - W.FARM[0]
    base = cam.px(W.FARM[1] - 3.0, 0.0, d)
    sc = cam.scale(d)
    return (base[0] - 9.0 * sc * 0.22, base[1] - 3.2 * sc * 0.55)


def _way_out(c, t):
    ft = FILM_T0 + t
    c.save()
    c.rectangle(0.0, 0.0, 1080.0, STRIP_TOP + 1.0)
    c.clip()
    W.draw_river(c, CAM_WAY, ft, holes=HOLES, moon_at=(905.0, 150.0), search=L.cross_light(ft), trunk=True)
    c.restore()


def _hole_pov(c, t, cam, dy, drags=(0.0, 0.0), under=(0.0, 0.0), dip=0.0, top=0.0):
    """The hole from the bank's side, from above (south up): the trail running into it, him at its
    near edge reaching toward us. Drawn `dy` px lower than the camera's centre."""
    ft = FILM_T0 + t
    c.save()
    c.rectangle(0.0, top, 1080.0, 1920.0 - top)
    c.clip()
    c.translate(0.0, dy)
    W.draw_page(c, cam, ft, prints=_out_of_hole(PRINTS), holes=HOLES)
    L.hat_top(c, cam, ft)
    L.hole_guard(c, cam, ft, drags=drags, under=under, dip=dip)
    c.restore()


def _out_of_hole(prints):
    (hx, hn), r = W.HOLE_BIG, W.HOLE_R[1]
    return tuple(p for p in prints if math.hypot(p[0] - hx, p[1] - hn) > r * 1.05)


def _split(c, t):
    ft = FILM_T0 + t
    _way_out(c, t)
    # below: his west glove slips back toward the water, and bites again
    slip = 0.22 * ease("out3", clamp((t - T_SLIP) / 0.12)) * (1.0 - ease("inout", clamp((t - T_SLIP - 0.32) / 0.3)))
    _hole_pov(c, t, CAM_HOLE, HOLE_DY, drags=(slip, 0.04 * slip), top=STRIP_BOT - 1.0)
    # her eyes: up to the way out, down to him, up again; narrowing
    up = ease("inout", clamp((t - T_UP1) / 0.12))
    down = ease("inout", clamp((t - T_DOWN) / 0.12))
    up2 = ease("inout", clamp((t - T_UP2) / 0.12))
    dy = -up + 2.0 * down - 2.0 * up2 * 0.85
    dx = 0.15 * math.sin(t * 9.0) * clamp((t - T_DOWN) / 0.3) * (1.0 - up2)      # the eyes tremble on him
    lid = lerp(1.0, 0.62, ease("inout", clamp((t - T_LIDS) / 0.25)))
    blink = 2.0 + 0.2
    if blink <= t < blink + 0.16:
        lid *= abs(math.cos(math.pi * (t - blink) / 0.16))
    F.eyes(c, "mother", (540.0, 960.0), STRIP_S, look=(dx, dy), lid=lid, fear=lerp(1.0, 0.55, clamp((t - T_LIDS) / 0.3)),
           edge=K.STEEL, t=ft, rim=K.PAPER)
    # the looks
    win = _farm_window(CAM_WAY)
    K.sight_line(c, (540.0, STRIP_TOP - 8.0), (win[0] - 10.0, win[1] + 26.0), t, T_UP1 + 0.08, color=K.PAPER, dur=0.5,
                 off=T_DOWN - 0.1)
    hand = (540.0 - 0.0, CAM_HOLE.px(L.G_IN_HOLE)[1] + HOLE_DY - 0.3 * CAM_HOLE.ppm)
    K.sight_line(c, (540.0, STRIP_BOT + 8.0), hand, t, T_DOWN + 0.08, color=K.PAPER, dur=0.45, off=T_UP2 - 0.1)
    K.sight_line(c, (540.0, STRIP_TOP - 8.0), (win[0] - 10.0, win[1] + 26.0), t, T_UP2 + 0.08, color=K.PAPER,
                 dur=0.4, off=6.2)
    # her heart, through both halves
    heart(c, (540.0, 960.0), t, alpha=0.3, r1=900.0, width=10.0)


# ============================================================================ C: the bank view (6-8.7)
CAM_C = L.Bank(7.7, -4.1, 14.0, 560.0, 1.59, eye=2.8, u0=-0.25)
CAM_C2 = L.Bank(7.6, -4.1, 14.0, 560.0, 1.59, eye=2.8, u0=-0.35)
M_AT = (7.45, -2.55)                       # her place in the reeds
G_AT = (7.95, -2.45)                       # the girl's: she stays there
M_GO = (7.12, -2.62)                       # two steps upstream and the arms are taut
CLEAR = ((7.7, -2.45, 0.95, 0.75), (7.62, -3.7, 1.25, 0.9))
GIRL_HAND = 0.36                           # the girl's hand: how far out to her left (m) when taut


def _m_pos(t):
    k = ease("inout", clamp((t - T_STEPS[0]) / (T_STEPS[1] - T_STEPS[0])))
    # two steps: each lands with a check, the second one jerked short
    k = k + 0.04 * math.sin(math.pi * clamp((t - T_STEPS[0]) / 0.47) * 2.0) * (1.0 - k)
    jerk = 0.03 * math.exp(-max(0.0, t - T_TAUT) * 9.0) * (t >= T_TAUT)
    return (lerp(M_AT[0], M_GO[0], k) + jerk, lerp(M_AT[1], M_GO[1], k))


def _bank_shot(c, t):
    ft = FILM_T0 + t
    cam = L.bank_lerp(CAM_C, CAM_C2, ease("inout", clamp((t - T_TURN) / 1.4)))
    L.draw_bank(c, cam, ft, holes=HOLES, prints=PRINTS, moon_at=None)
    L.bank_guard(c, cam, ft)
    mx, mn = _m_pos(t)
    gx, gn = G_AT
    dm, dg = cam.depth(mx, mn), cam.depth(gx, gn)
    L.bank_reeds(c, cam, ft, d0=max(dm, dg) + 0.2, clear=CLEAR, rim=L.RIM)
    sm, sg = cam.scale(mx, mn), cam.scale(gx, gn)
    at_m, at_g = cam.px(mx, mn, 0.0), cam.px(gx, gn, 0.0)
    rise_m = ease("inout", clamp((t - T_RISE[0]) / (T_RISE[1] - T_RISE[0])))
    rise_g = ease("inout", clamp((t - T_RISE[0] - 0.25) / (T_RISE[1] - T_RISE[0])))
    reach = ease("inout", clamp((t - (T_TAKE - 0.2)) / 0.25))
    # the girl, from behind: standing her ground, leaning back toward the hole as the pull comes
    taut = clamp((t - T_TAUT + 0.25) / 0.25)
    lean = 7.0 * taut + 2.0 * math.sin(t * 7.0) * taut
    # the hands meet between them
    g_sh = (at_g[0] - 0.2 * 0.66 * sg, at_g[1] - lerp(0.62, 1.32, 1.0 - 0.0) * 0.66 * sg)
    hand_out = lerp(0.12, GIRL_HAND, max(reach * 0.4, taut))
    meet = (at_g[0] - (0.13 + hand_out) * sg, at_g[1] - lerp(0.62, 0.86, rise_g) * sg)
    c.save()
    c.translate(at_g[0], at_g[1])
    c.rotate(math.radians(lean))
    c.translate(-at_g[0], -at_g[1])
    gm = L.back(c, "girl", at_g, sg, "crouch", t=ft, u=lerp(0.8, 0.0, rise_g), rim=L.RIM, rim_w=3.0,
                hand=meet if reach > 0.0 else None, hand_side=-1)
    c.restore()
    meet = L.turn_pt(meet, at_g, lean)
    # the mother: from behind as she rises, then in profile, going upstream
    if t < T_TURN:
        hand = (lerp(at_m[0] + 0.25 * sm, meet[0], reach), lerp(at_m[1] - 0.8 * sm, meet[1], reach)) if reach > 0.0 else None
        mm = L.back(c, "mother", at_m, sm, "crouch", t=ft, u=1.0 - rise_m, rim=L.RIM, rim_w=3.0, hand=hand)
        L.back_breath(c, mm["head"], sm, t, rate=0.75, strength=0.8)
    else:
        u, d = cam.ud(mx, mn)
        walk = clamp((t - T_STEPS[0]) / (T_STEPS[1] - T_STEPS[0]))
        st = L.stance("mother", step=0.32 * math.sin(math.pi * clamp(walk * 2.0 % 1.0 if walk < 1.0 else 0.0)), spread=14.0)
        s_fig = C.scale("mother", cam.dio.scale(d))
        # her near arm back to the girl's hand (figure units from her root, x to screen right)
        tgt = ((meet[0] - at_m[0]) / s_fig, (meet[1] - at_m[1]) / s_fig)
        strain = clamp((t - T_TAUT + 0.1) / 0.2)
        pose = C.still_pose("mother", lean=lerp(4.0, 14.0, strain), head=lerp(0.0, 6.0, strain), t=ft,
                            arms={"near": ("ik", tgt), "far": ("ang", lerp(10.0, 35.0, walk), 18.0)})
        j = L.figure(c, cam.dio, "mother", st, pose, u, 0.0, d, -1, 0.0, rim=L.RIM, light=L.BANK_LIGHT)
        K.breath(c, j["mouth"], t, rate=1.4, facing=-1, s=0.9, phase=T_TURN, strength=0.85, seed=5)
    L.back_breath(c, gm["head"], sg * 0.7, t, rate=0.9, phase=0.2, strength=0.7)
    # the reeds in front of them
    L.bank_reeds(c, cam, ft, d1=min(dm, dg) - 0.15, clear=CLEAR, rim=L.RIM)
    # the girl is looking at the hole
    hole = cam.px(L.G_IN_HOLE[0], L.G_IN_HOLE[1], W.ICE_Z + 0.25)
    K.sight_line(c, (gm["head"][0] + 0.12 * sg, gm["head"][1]), hole, t, T_LOOK, color=K.PAPER, dur=0.4, off=T_HOLE + 0.5,
                 r=5.0, gap=19.0, head=20.0)


# ============================================================================ D: the glove goes under (8.7-9.7)
CAM_D = W.Plan(13.32, 10.25, 380.0, rot=180.0)


def _glove_under(c, t):
    ft = FILM_T0 + t
    go = ease("in", clamp((t - T_UNDER[0]) / (T_UNDER[1] - T_UNDER[0])))
    dip = math.sin(math.pi * clamp((t - T_UNDER[1] + 0.15) / 0.55)) * 0.8
    _hole_pov(c, t, CAM_D, 260.0, drags=(0.0, 0.06 * go), under=(go, 0.0), dip=dip)
    edge = CAM_D.px((L.G_IN_HOLE[0] - 0.42, L.G_IN_HOLE[1] + 0.02))
    edge = (edge[0], edge[1] + 260.0)
    L.rings(c, edge, t, T_UNDER[0] + 0.32, 0.5 * CAM_D.ppm, 0.36 * CAM_D.ppm, n=3, every=0.2, life=1.0,
            width=4.0, seed=7, alpha=0.8)
    L.spray(c, edge, t, T_UNDER[0] + 0.3, CAM_D.ppm * 0.5, n=12, seed=17, power=0.5, life=0.5)


# ============================================================================ E: the girl and her scarf (9.7-12.2)
G_CU = (760.0, 1170.0)
G_S = 1.1
SCARF_W = 64.0
STRIPE = lerp(K.RED, K.INK, 0.38)


def scarf_strip(c, pts, t, width=SCARF_W, fringe=True, seed=0):
    """The red scarf along a polyline (frame px), its last point the free end: two knitted stripes
    near the end and a fringe of short strands swinging there."""
    K.band(c, pts, K.RED, width, seed=11 + seed, taper=(1.0, 1.0))
    if len(pts) < 2:
        return
    (ax, ay), (bx, by) = pts[-2], pts[-1]
    L_ = math.hypot(bx - ax, by - ay) or 1.0
    ux, uy = (bx - ax) / L_, (by - ay) / L_
    nx, ny = -uy, ux
    for k, back in enumerate((0.55, 0.9)):              # stripes across, just above the end
        cx, cy = bx - ux * width * back, by - uy * width * back
        K.band(c, [(cx - nx * width * 0.5, cy - ny * width * 0.5), (cx + nx * width * 0.5, cy + ny * width * 0.5)],
               STRIPE, width * 0.13, seed=31 + k)
    if fringe:
        for i in range(6):
            off = (i / 5.0 - 0.5) * width * 0.85
            base = (bx + nx * off, by + ny * off)
            sw = 0.25 * math.sin(t * 6.0 + i * 1.3 + seed)
            ln = width * (0.55 + 0.2 * hash01(seed, i))
            tip = (base[0] + (ux + nx * sw) * ln, base[1] + (uy + ny * sw) * ln)
            K.band(c, [base, tip], K.RED, max(3.0, width * 0.09), seed=41 + i, taper=(1.0, 0.5))


def hanging(top, length, t, swing=1.0, phase=0.0, n=9):
    """A scarf hanging from `top` (frame px), swinging a little from where it is held."""
    a = swing * (0.05 * math.sin(t * 2.2 + phase) + 0.02 * math.sin(t * 5.3 + 2.0 * phase))
    out = []
    for i in range(n + 1):
        u = i / n
        bend = a * (u ** 1.4)
        out.append((top[0] + math.sin(bend) * length * u + 6.0 * math.sin(t * 7.0 + 5.0 * u) * u, top[1] + length * u))
    return out


def _girl_cu(c, t):
    ft = FILM_T0 + t
    _backdrop_cu(c, t, horizon=900.0, band=(990.0, 1035.0), hole_x=None, facing=-1)
    reed_blades(c, t, REEDS_A_BACK, color=lerp(K.INK, W.STEEL, 0.25))
    unwind = ease("inout", clamp((t - T_UNWIND[0]) / (T_UNWIND[1] - T_UNWIND[0])))
    offer = ease("out3", clamp((t - T_OFFER[0]) / (T_OFFER[1] - T_OFFER[0])))
    look_up = ease("inout", clamp((t - (T_OFFER[0] + 0.15)) / 0.3))
    bust_base(c, G_CU, G_S, -40.0, 620.0, 900.0, facing=-1)
    g = F.girl(c, G_CU, G_S, look=lerp(0.6, 0.9, look_up), down=lerp(0.3, -0.6, look_up), fear=0.05, t=ft,
               facing=-1, rim=K.PAPER, light=(0.55, -0.85), rim_w=5.0, scarf=1.0 - unwind, scarf_lift=0.0)
    shoulder = (G_CU[0] + 30.0, G_CU[1] + 330.0)
    chin = (G_CU[0] - 80.0, G_CU[1] - 110.0)
    # her mitten takes the scarf's end at her chin and draws it off, round and out; then lifts it
    # high, up to her mother, all of it hanging from her hand
    loop = math.sin(math.pi * 2.0 * unwind)
    pull = (chin[0] - 70.0 - 200.0 * unwind + 50.0 * loop, chin[1] + 100.0 - 90.0 * loop + 80.0 * unwind)
    hold = (lerp(pull[0], 360.0, offer), lerp(pull[1], 640.0, offer))
    if offer <= 0.0:
        if unwind > 0.02:
            free = 220.0 + 520.0 * unwind
            mid = (lerp(chin[0], hold[0], 0.5), lerp(chin[1], hold[1], 0.5) + 60.0 * unwind)
            scarf_strip(c, [(chin[0] + 10.0, chin[1] + 40.0), mid, hold] + hanging(hold, free * 0.5, t)[1:], t)
    else:
        scarf_strip(c, hanging((hold[0] + 6.0, hold[1] + 24.0), lerp(560.0, 800.0, offer), t, swing=1.0 + offer), t)
    F.mitten(c, shoulder, (hold[0] + 26.0, hold[1] + 10.0), 0.9, rim=K.PAPER, light=(0.55, -0.85), thumb=0.85,
             curl=0.85, sleeve_w=0.72)
    K.breath(c, g["mouth"], t, rate=1.0, facing=-1, s=1.4, phase=0.3, strength=0.8, seed=9)
    reed_blades(c, t, REEDS_A_FRONT)


# ============================================================================ F: she takes it (12.2-14)
M_CU = (360.0, 1170.0)
M_S = 1.02
G_HOLD = (870.0, 700.0)        # the girl's mitten, up from the lower right, the scarf hanging from it


def _mother_cu(c, t):
    ft = FILM_T0 + t
    _backdrop_cu(c, t, horizon=840.0, band=(930.0, 975.0), hole_x=900.0)
    reed_blades(c, t, REEDS_A_BACK, color=lerp(K.INK, W.STEEL, 0.25))
    heart(c, (200.0, 1450.0), t, alpha=0.3)
    see = ease("inout", clamp((t - T_SEE) / 0.14))
    hole = ease("inout", clamp((t - T_HOLE_LOOK) / 0.14))
    grab = ease("out3", clamp((t - T_GRAB[0]) / (T_GRAB[1] - T_GRAB[0])))
    settle = ease("inout", clamp((t - T_GRAB[1]) / 0.4))
    look = lerp(lerp(0.7, 0.75, see), 0.95, hole)
    down = lerp(lerp(0.1, 0.55, see), -0.15, hole) * (1.0 - settle) + 0.3 * settle
    bust_base(c, M_CU, M_S, -60.0, 600.0, 1040.0)
    m = F.mother(c, M_CU, M_S, look=look, down=down, fear=lerp(0.9, 0.25, settle), t=ft, rim=K.PAPER,
                 light=(0.55, -0.85), rim_w=5.0)
    # the scarf held up to her, hanging from the girl's small mitten; it stills in her grip
    top = (G_HOLD[0] + 4.0 * math.sin(t * 8.0), G_HOLD[1] + 20.0)
    pts = hanging(top, 900.0, t, swing=1.0 - 0.8 * grab)
    grip_y = 1060.0
    if grab > 0.0:
        # held: below her fist it hangs straight down from it
        k = clamp((grip_y - top[1]) / 900.0)
        fist = (lerp(pts[3][0], top[0], 0.5 * grab), top[1] + k * 900.0)
        pts = [top, fist] + [(fist[0] + (p[0] - top[0]) * (1.0 - grab) * 0.3, p[1]) for p in pts if p[1] > fist[1] + 40.0]
    scarf_strip(c, pts, t)
    F.mitten(c, (1180.0, 1520.0), (G_HOLD[0] + 22.0, G_HOLD[1] + 8.0), 0.8, rim=K.PAPER, light=(0.55, -0.85),
             thumb=0.8, curl=0.85, sleeve_w=0.7, flip=True)
    # her mitten comes up and closes on the red
    if t >= T_GRAB[0] - 0.15:
        tip = (lerp(560.0, G_HOLD[0] - 20.0, grab), lerp(1900.0, grip_y + 30.0, grab))
        F.mitten(c, (190.0, 2120.0), tip, 1.1, rim=K.PAPER, light=(0.55, -0.85), thumb=0.9, curl=0.9 * grab,
                 sleeve_w=0.85)
    puff(c, m["mouth"], t, T_GRAB[1] + 0.05, facing=1, s=1.1, seed=12)
    reed_blades(c, t, REEDS_A_FRONT)


# ============================================================================ render
def render(f, t, T):
    K.scene_setup(f, K.NIGHT)
    with f.screen() as c:
        if t < T_SPLIT:
            _reeds_cu(c, t)
        elif t < T_BANK:
            _split(c, t)
        elif t < T_HOLE:
            _bank_shot(c, t)
        elif t < T_GIRL:
            _glove_under(c, t)
        elif t < T_MOTHER:
            _girl_cu(c, t)
        else:
            _mother_cu(c, t)


def motion_blur(t, T):
    return 1


def cues(T):
    return [
        Cue(0.0, "heartbeat", gain_db=-6, dur=HEART_STOP,
            dc="her heartbeat, close and loud: lub-dub at 96 bpm, the first beat at the cue, a beat every 0.625 s; "
               "it stops dead at the end (she takes the scarf)"),
        Cue(0.0, "string_high", gain_db=-20, dur=HEART_STOP, dc="one held high string note (E6), very quiet, trembling"),
        Cue(0.0, "wind_low", gain_db=-22, dur=14.0, dc="the wind over the river, low"),
        Cue(1.3, "her_breath", gain_db=-12, dc="the breath she was holding, let out shaking (a recorded breath)"),
        Cue(T_SPLIT, "paper_slide", gain_db=-20, dc="the frame splits: a soft slide of paper"),
        Cue(T_SPLIT + 0.2, "searchlight_hum", gain_db=-24, dur=3.8, pan=-0.3, dc="the searchlight's motor, far upstream"),
        Cue(T_DOWN, "panting_man", gain_db=-16, dur=1.4, pan=0.2, dc="his ragged panting, across the ice"),
        Cue(T_SLIP, "glove_slip", gain_db=-10, dc="a wet glove sliding on ice"),
        Cue(T_SLIP + 0.02, "ice_scrape", gain_db=-14, dc="fingers scraping across ice"),
        Cue(T_SLIP + 0.42, "glove_ice", gain_db=-14, dc="the glove bites the ice again"),
        Cue(T_RISE[0], "reeds_rustle", gain_db=-12, dc="she rises through dry reeds"),
        Cue(T_TAKE, "mitten_grab", gain_db=-16, dc="mitten taking mitten"),
        Cue(T_STEPS[0] + 0.1, "snow_step_mother", gain_db=-12, pan=-0.3, dc="her boot in the snow, soft and quick"),
        Cue(T_STEPS[0] + 0.58, "snow_step_mother", gain_db=-12, pan=-0.4, dc="her second step"),
        Cue(T_TAUT, "cloth_stretch", gain_db=-14, dc="the arms go taut: coats pull, a boot digs in"),
        Cue(T_TAUT + 0.02, "snow_scuff_girl", gain_db=-14, pan=0.1, dc="the girl's small boots dig into the snow"),
        Cue(T_UNDER[0], "glove_slip", gain_db=-8, pan=0.3, dc="his glove slides off the edge"),
        Cue(T_UNDER[0] + 0.32, "splash_small", gain_db=-8, pan=0.3, dc="his hand goes into the water"),
        Cue(T_UNDER[0] + 0.4, "gasp_man", gain_db=-12, pan=0.3, dc="a choked gasp, further away (a recorded gasp)"),
        Cue(T_UNWIND[0], "scarf_unwind", gain_db=-12, dur=T_UNWIND[1] - T_UNWIND[0], dc="wool sliding off a small neck"),
        Cue(T_GRAB[1], "mitten_grab", gain_db=-12, dc="her mitten closes on the scarf"),
        Cue(T_GRAB[1] + 0.05, "music_box_note", gain_db=-14,
            dc="one note of the lullaby on the music box, E5, alone in the silence where the heartbeat was"),
    ]
