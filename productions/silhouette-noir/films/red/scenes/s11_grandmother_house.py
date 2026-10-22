"""s11 · GRANDMOTHER'S HOUSE: decades later, dusk (15.0 s). The film's last scene.

IN   (from white): the cottage in the clearing, mended, no web; a warm window, chimney smoke,
     snow falling. A new path of lanterns climbs to it out of the forest on the left.
L21 1.5-4.8   the camera moves in to the door. Old Red (long red cape and hood, a cane) stands
     in the open, lit doorway with a lit taper; the old grey-muzzled wolf dozes by the step.
L22 6.0-7.5   she reaches up and lights the last lantern by the door: it catches on [one@6.94].
7.5-13.0  a small child in a red hood walks up the lantern path. The old wolf opens its eyes
     and lifts its head; Old Red raises her light to her.
L23 10.4-13.0 the camera cranes up and back over the clearing: the lantern path is a line of
     light through the dark trees, the child's red hood at its end.
13.0-15.0 flatten to Bass: the image goes flat, the paper comes up and the line of lights is
     a black cut-paper line; the plane turns (s01's turn, reversed): the line swings up into
     s01's path from the top of the frame, the hood lies down and is the small RED triangle
     at its end (s01's triangle, same place, same angle). Hold. Hard cut: the film ends.

Camera: wide (0.34) -> in to the door (0.78 at 4.6 s, creeping to 0.84) -> back (0.50 at
10.1 s) -> crane up and back (0.30 at 13.0 s); after that the frame is flat paper.
Layers: CLEARING back (sky, fogged forest, far lantern lights) > plane (trees, cottage, lantern
posts, the open lit doorway painted here) > wolf, Old Red (+ cane, taper), child > snow lip,
light pools > falling snow > the Bass overlay (screen space).
"""
import math

import cairo

from engine import atmos, bass, draw
from engine.core import H, clamp, hash01, lerp
from engine.creatures import Wolf
from engine.frame import GLOW_DS
from engine.motion import Actor
from engine.palette import PAPER, RED
from engine.timing import Cue
from films.red import cast
from films.red import sets as S
from films.red.scenes import _lib_s09_s11 as L
from films.red.sets_common import SNOW, glow, light_pool, mix

C = S.CLEARING_SET
TER = S.CLEARING
MOOD = S.LATER
G = TER.ground_y
INK = MOOD.ink

OLD_X = -40.0            # Old Red in the doorway (door x -150..150)
WOLF_X = 398.0           # the old wolf's root: it lies at her feet, head across the lit doorway
WOLF_OFF = 6.0           # the wolf's clock runs ahead: already lying when the scene opens
CHILD_X0 = -2450.0       # the child, out of shot down the path until ~9 s
CHILD_X1 = -360.0

FLAT = 13.0              # the flatten begins
TURN0, TURN_DUR = 13.45, 0.7
LAND = TURN0 + TURN_DUR  # the triangle lands at s01's stop
LIVE_END = 13.6          # after this the frame is all paper: the set is not drawn


def _words(T):
    return dict(they=T.at("they"), house=T.at("house"), so=T.at("so"), one=T.at("one"),
                which=T.at("which"), path=T.at("path"), never=T.at("never"), leave=T.at("leave"))


_C = {}


def _door():
    C._ensure()
    return C.cottage.anchors("new")["door"]          # (x0, ground, x1, top)


def _cast(T):
    if _C:
        return _C
    W_ = _words(T)
    lit = W_["one"]
    # ---- the old wolf: dozing by the step; wakes when the child comes up the path
    w = Wolf(WOLF_X, G, facing=-1, size=292.0, seed=8, old=True)
    w.lie(60.0, head_down=0.62, eyes=0.0, breath=0.75)
    w.overlay("eyes", 9.35 + WOLF_OFF, 30.0, open=1.0)
    w.overlay("look", 9.85 + WOLF_OFF, 30.0, turn=8.0, head=4.0, neck=32.0)
    wolf = L.WolfRig(w, WOLF_OFF)
    # ---- Old Red: in the doorway, a lit taper in her near (left) hand, the cane in the other
    r = Actor(cast.OLD_RED, cast.old_red(), x=OLD_X, ground=G, facing=-1, seed=12, name="old_red")
    r.stand(until=30.0, at=-1.0, idle=0.55)
    r.arm("R", -1.0, 30.0, fade=0.3, sh=8.0, elbow=30.0, abd=8.0, wrist=-8.0, grip=0.9)    # on the cane
    r.key("arm.L.sh", [(-1.0, 18.0), (lit + 0.9, 18.0), (lit + 1.5, 22.0, "inout"),
                       (10.35, 22.0), (11.15, 128.0, "inout"), (30.0, 128.0)], fade=0.3)
    r.key("arm.L.elbow", [(-1.0, 104.0), (lit + 0.9, 104.0), (lit + 1.5, 100.0, "inout"),
                          (10.35, 100.0), (11.15, 38.0, "inout"), (30.0, 38.0)], fade=0.3)
    r.key("arm.L.grip", [(-1.0, 0.85), (30.0, 0.85)], fade=0.3)
    lantern = _lantern_flame()
    r.reach("L", lit - 0.75, lit + 0.4, lambda t: (lantern[0] + 30.0, lantern[1] + 30.0), fade=0.55)
    r.key("pitch", [(lit - 1.2, 0.0), (lit - 0.5, 7.0, "inout"), (lit + 0.5, 7.0), (lit + 1.2, 0.0, "inout")],
          mode="add")
    r.look_at(lit - 1.3, lit + 0.7, lantern, fade=0.45)
    child = lambda t: _C["child"].root(t)
    r.look_at(9.4, 30.0, lambda t: (child(t)[0], child(t)[1] - 120.0), fade=0.6)
    r.blink(2.6)
    r.blink(8.8)
    # ---- the child: up the lantern path toward the door
    k = Actor(cast.NEW_CHILD, cast.new_child(), x=CHILD_X0, ground=G, facing=1, seed=14, name="child")
    k.stand(until=6.2, at=-1.0)
    k.walk(to=CHILD_X1, gait="child_walk", speed=0.74)
    k.stand(until=30.0)
    k.look_at(10.6, 30.0, (OLD_X, 1100.0), fade=0.6, amount=0.7)
    _C.update(wolf=wolf, red=r, child=k, lit=lit, lantern=lantern)
    return _C


def _lit_fn(t_lit):
    """Every lantern burns; the last one (by the door) glows faintly until she lights it."""
    def lit(i, t):
        if i == len(C.lanterns.posts) - 1:
            return max(0.07, clamp((t - t_lit) / 0.35))
        return 1.0
    return lit


def _lantern_flame():
    """World position of the last lantern's flame (by the door)."""
    C._ensure()
    return tuple(C.lanterns.flames(0.0)[-1])


# ----------------------------------------------------------------------------- camera
CAM_KEYS = [                  # (t, x, y offset above the threshold, zoom[, ease])
    (-1.0, -470.0, 1100.0, 0.34),
    (1.2, -430.0, 1060.0, 0.36, "inout"),
    (4.6, -150.0, 560.0, 0.78, "inout"),
    (7.6, -170.0, 585.0, 0.84, "inout"),
    (10.1, -700.0, 820.0, 0.50, "inout"),
    (13.0, -1150.0, 1415.0, 0.30, "inout"),
    (16.0, -1150.0, 1415.0, 0.30),
]
_GD = 1565.52
CAM = L.CamPath([(k[0], k[1], _GD - k[2], k[3]) + tuple(k[4:]) for k in CAM_KEYS])


# ----------------------------------------------------------------------------- the set extras
def _open_door(f, t):
    """The cottage door stands open on a warm room: Old Red is a silhouette against it."""
    x0, gy, x1, ytop = _door()
    lamp = MOOD.lamp
    hot = mix(mix(INK, lamp, 0.86), mix(lamp, SNOW, 0.18), 0.45)
    deep = mix(INK, lamp, 0.46)
    fl = 1.0 + 0.04 * math.sin(t * 7.1) + 0.03 * math.sin(t * 12.7 + 1.3)
    with S.plane(f, 1.0) as c:
        draw.rect(c, x0 + 6, ytop + 6, x1 - 6, gy)
        draw.linear(c, (0.0, ytop), (0.0, gy), [(0.0, deep, 1.0), (0.5, mix(deep, hot, 0.8), 1.0),
                                                (1.0, mix(hot, SNOW, 0.12 * fl), 1.0)])
        c.fill()
        # the room: a back-wall shadow, a shelf with a jug, the floor
        draw.rect(c, x0 + 6, gy - 26, x1 - 6, gy)
        draw.fill(c, mix(INK, lamp, 0.3))
        draw.rect(c, x1 - 120, ytop + 190, x1 - 6, ytop + 202)
        draw.fill(c, mix(INK, lamp, 0.35))
        draw.poly(c, [(x1 - 92, ytop + 190), (x1 - 96, ytop + 158), (x1 - 86, ytop + 148), (x1 - 70, ytop + 148),
                      (x1 - 62, ytop + 160), (x1 - 66, ytop + 190)])
        draw.fill(c, mix(INK, lamp, 0.35))
        # the door leaf swung in against the left jamb
        draw.poly(c, [(x0 + 6, ytop + 6), (x0 + 70, ytop + 34), (x0 + 70, gy - 20), (x0 + 6, gy)])
        draw.fill(c, mix(INK, lamp, 0.12))
        # jambs and lintel
        for (a, b) in (((x0 - 4, ytop - 6), (x0 + 8, gy)), ((x1 - 8, ytop - 6), (x1 + 4, gy))):
            draw.rect(c, a[0], a[1], b[0], b[1])
        draw.rect(c, x0 - 10, ytop - 10, x1 + 10, ytop + 8)
        draw.fill(c, INK)
    with S.soft_layer(f, 1.0, k=6, op="add", blur=26.0) as A:
        glow(A, (0.0, gy - 260.0), 520.0, lamp, 0.24 * fl)
        glow(A, (170.0, gy - 70.0), 320.0, lamp, 0.20 * fl)


def _door_spill(f, t):
    """Warm light thrown out of the doorway onto the snow (after the snow lip)."""
    x0, gy, x1, ytop = _door()
    with S.soft_layer(f, 1.0, k=6, op="add", blur=30.0) as A:
        light_pool(A, (-30.0, gy + 26.0), 420.0, 80.0, MOOD.lamp, 0.30)


def _light_flare(f, pos, t, lit):
    """The last lantern catching: a brief flare on [one]."""
    u = (t - lit) / 0.6
    if 0.0 <= u <= 1.0:
        a = math.sin(math.pi * min(1.0, u * 2.2)) * (1.0 - u) ** 0.5
        with f.emit() as E:
            glow(E, pos, 70.0, MOOD.lamp, 0.55 * a)
            glow(E, pos, 220.0, MOOD.lamp, 0.18 * a)


# ----------------------------------------------------------------------------- the Bass ending
INK_B = (0.012, 0.012, 0.012)           # s01's ink (RED_FILM.ink)
_TANG = L.path_tangent_deg(L.Y_STOP)
PSTOP = (L.path_x(L.Y_STOP), L.Y_STOP)
N_LINE = 96


def _s01_full():
    """s01's path points exactly as s01 builds them (y -60 .. H + 60, step 12)."""
    n = int((H + 60.0 - (-60.0)) / 12.0)
    return [(L.path_x(-60.0 + i * 12.0), -60.0 + i * 12.0) for i in range(n + 1)]


_S01 = _s01_full()


def _u_stop():
    seg = [math.dist(_S01[i], _S01[i + 1]) for i in range(len(_S01) - 1)]
    tot = sum(seg)
    acc = 0.0
    for i, (a, b) in enumerate(zip(_S01, _S01[1:])):
        if b[1] >= L.Y_STOP:
            acc += seg[i] * (L.Y_STOP - a[1]) / (b[1] - a[1])
            break
        acc += seg[i]
    return acc / tot


U_STOP = _u_stop()
_TARGET = L.resample(list(reversed(L.path_pts(-60.0, L.Y_STOP, 6.0))), N_LINE)   # from the stop up


def _hood_screen(f, cs, t):
    """Screen position of the child's cloak centre and her on-screen scale (side view)."""
    k = cs["child"]
    x, _ = k.root(t)
    gy = float(G(x))
    cam = f.cam
    z = cam.zoom
    ks = 370.0 / 100.0 * z                 # the cut-out figure is 100 units tall
    feet = cam.to_screen((x, gy))
    return (feet[0], feet[1] - 62.0 * ks), ks


def _live_line(f, cs, t):
    """The line of light on screen: from the child's hood back along the lanterns behind her,
    continued off the left edge (resampled to N_LINE points, the hood first)."""
    hood, _ = _hood_screen(f, cs, t)
    cx = cs["child"].root(t)[0]
    fl = [p for p in C.lanterns.flames(t) if p[0] < cx - 40.0]
    pts = [hood] + [f.cam.to_screen(p) for p in reversed(fl)]
    if len(pts) < 2:
        pts.append((hood[0] - 400.0, hood[1] + 60.0))
    a, b = pts[-2], pts[-1]
    d = math.dist(a, b) or 1.0
    ext = 900.0
    pts.append((b[0] + (b[0] - a[0]) / d * ext, b[1] + (b[1] - a[1]) / d * ext))
    pts = L.smooth_pts(pts, 2)
    return L.resample(pts, N_LINE)


def _rot(p, a):
    ca, sa = math.cos(a), math.sin(a)
    return (p[0] * ca - p[1] * sa, p[0] * sa + p[1] * ca)


def _ribbon(c, pts, width, color=INK_B, seed=7):
    """A cut-paper band along pts with a stable edge (no boil while the line morphs)."""
    wd = [max(0.5, width + 1.0 * (hash01(seed, k, 2) * 2.0 - 1.0)) for k in range(len(pts))]
    poly = bass.orient(draw.ribbon(pts, wd), True)
    bass.fill_polys(c, [poly], color)


LINE_LIGHT = mix(MOOD.lamp, SNOW, 0.55)


def _flat_amounts(t):
    """13.00-13.30 the line of light draws on through the lanterns (hood first); 13.12-13.22
    the line goes from light to ink; 13.20-13.32 the scene flattens to a two-ink print;
    13.34-13.50 the print gives way to bare paper; 13.30-13.60 the hood lies down flat;
    13.45-14.15 the plane turns."""
    return dict(draw=L.k01(t, FLAT, 0.3, "out3"),
                ink=L.k01(t, FLAT + 0.12, 0.1, "inout"),
                poster=L.k01(t, FLAT + 0.2, 0.12, "inout"),
                paper=L.k01(t, FLAT + 0.34, 0.16, "inout"),
                width=L.k01(t, FLAT + 0.2, 0.4, "inout"),
                lie=L.k01(t, FLAT + 0.3, 0.3, "inout"),
                turn=L.k01(t, TURN0, TURN_DUR, "inout3"))


def _post(f, t):
    """The film look -> s01's Bass look (paper .75, vignette .14, no bloom, light grain)."""
    if t < FLAT:
        return
    e = L.k01(t, FLAT + 0.1, 0.45, "inout")
    P = f.post
    P["bloom"] = lerp(P["bloom"], 0.0, L.k01(t, FLAT + 0.1, 0.25, "inout"))
    P["glow"] = lerp(P["glow"], 0.0, L.k01(t, FLAT + 0.18, 0.2, "inout"))
    P["paper"] = 0.75 * e
    P["vignette"] = lerp(P["vignette"], 0.14, e)
    P["flicker"] = lerp(P["flicker"], 0.006, e)
    P["grain"] = lerp(P["grain"], min(f.pal.grain, 0.045), e)
    po = _flat_amounts(t)["poster"]
    P["poster"] = bass.poster(f.pal, po, tones=2, thr=(0.07, 0.09), light=PAPER) if po > 0.001 else None


def _bass(f, t, cs, live):
    """The flatten overlay (screen space), from FLAT on."""
    a = _flat_amounts(t)
    with f.screen() as c:
        if a["paper"] > 0.0:
            c.save()
            c.identity_matrix()
            c.set_source_rgba(*PAPER, a["paper"])
            c.paint()
            c.restore()
        if t < LAND:
            t0 = min(t, TURN0)                # the start shape follows the child until the turn
            hood0, ks = _hood_screen(f, cs, t0)
            src = _live_line(f, cs, t0)
            dl = src[-1][0] - hood0[0], src[-1][1] - hood0[1]
            alpha_l = math.atan2(dl[1], dl[0])
            delta = (-math.pi / 2.0) - alpha_l
            while delta < -math.pi:
                delta += 2 * math.pi
            while delta > math.pi:
                delta -= 2 * math.pi
            e = a["turn"]
            cen = (lerp(hood0[0], PSTOP[0], e), lerp(hood0[1], PSTOP[1], e))
            pts = []
            for p, q in zip(src, _TARGET):
                d0 = _rot((p[0] - hood0[0], p[1] - hood0[1]), delta * e)
                d1 = (q[0] - PSTOP[0], q[1] - PSTOP[1])
                pts.append((cen[0] + lerp(d0[0], d1[0], e), cen[1] + lerp(d0[1], d1[1], e)))
            if a["draw"] > 0.0:
                n = max(2, int(round(len(pts) * a["draw"])))
                col = mix(LINE_LIGHT, INK_B, a["ink"])
                _ribbon(c, pts[:n], lerp(7.0, 18.0, a["width"]), col)
                gl = (1.0 - a["ink"]) * a["draw"]
                if live and gl > 0.01:
                    with f.emit() as E:
                        E.save()
                        E.set_matrix(cairo.Matrix(xx=f.scale / GLOW_DS, yy=f.scale / GLOW_DS))
                        for p in pts[:n:3]:
                            glow(E, p, 30.0, MOOD.lamp, 0.42 * gl)
                        E.restore()
            # the hood: the child's red cloak lies down flat and rides the turn to s01's stop
            kk = lerp(lerp(ks, L.HOOD_K, a["lie"]), L.HOOD_K, e)
            ang = 90.0 * a["lie"] + _TANG * e
            show = L.k01(t, FLAT + 0.16, 0.14, "inout")
            if show > 0.0:
                L.draw_triangle(c, cen, ang, kk * (0.8 + 0.2 * show), RED)
        else:
            band = bass.line_pts(_S01, 18.0, U_STOP, seed=7)
            if band:
                bass.fill_polys(c, [band], INK_B)
            rock = bass.settle(t, LAND, amp=7.0, freq=3.2, decay=7.0)
            L.draw_triangle(c, PSTOP, _TANG + 90.0, L.HOOD_K, RED, rock=rock)


# ----------------------------------------------------------------------------- scene
def render(f, t, T):
    cs = _cast(T)
    f.set_camera(CAM.at(t))
    if t >= LIVE_END:
        bass.bass_scene(f, field=PAPER, paper=0.75, vignette=0.14)
        _bass(f, t, cs, live=False)
        return
    lit = _lit_fn(cs["lit"])
    C.draw_back(f, MOOD, era="later", t=t)
    C.draw_plane(f, MOOD, era="later", t=t, lit=lit)
    _open_door(f, t)
    wolf = cs["wolf"]
    rim = mix(MOOD.lamp, SNOW, 0.25)
    L.rim(f, 1.0, lambda c, col: wolf.draw(f, t, c, color=col, eyes=False), -5.0, -6.0, rim, alpha=0.8,
          blur=3.0)
    with f.layer() as c:
        wolf.draw(f, t, c, far_shade=0.25)
        r = cs["red"]
        sk = r.draw(f, t, c)
        _props(f, c, sk, t, cs)
        cs["child"].draw(f, t, c)
    C.draw_front(f, MOOD, era="later", t=t, lit=lit, occluders=False)
    _door_spill(f, t)
    _light_flare(f, cs["lantern"], t, cs["lit"])
    atmos.snow(f, density=0.32, wind=10.0, t=t, seed=23, color=mix(MOOD.snow, SNOW, 0.5), size=0.85,
               speed=0.55, alpha=0.85)
    crane = L.k01(t, 10.4, 2.6, "inout") * (1.0 - L.k01(t, FLAT + 0.1, 0.1))
    if crane > 0.0:
        C.canopy_shade(f, MOOD, strength=0.55 * crane, depth=0.5)
    if t >= FLAT:
        _post(f, t)
        _bass(f, t, cs, live=True)


def _props(f, c, sk, t, cs):
    """Old Red's cane (far hand) and her lit taper (near hand)."""
    J = sk.j
    hr = J["hand_R"]
    L.cane(c, hr, lambda x: float(G(x)), 300.0, lean=10.0, d=-1.0, width=8.0)
    lit = cs["lit"]
    reach = L.k01(t, lit - 0.75, 0.55, "inout") * (1.0 - L.k01(t, lit + 0.4, 0.55, "inout"))
    hand = J["hand_L"]
    fx, fy = cs["lantern"]
    aim = math.degrees(math.atan2(fx - hand[0], -(fy - hand[1])))       # 0 = up, + toward +x
    ang = lerp(-8.0, aim, reach)
    L.taper(f, c, hand, ang, length=56.0, flame=1.0, t=t, mood=MOOD)


def motion_blur(t, T):
    return 1


def cues(T):
    W_ = _words(T)
    lit = W_["one"]
    return [
        Cue(-1.0, "a still snowy evening in the clearing: soft wind high in the trees, a hearth "
                  "crackling inside the open door", -18, dur=14.0),
        Cue(0.5, "the old wolf's slow, deep breathing by the step", -22, dur=8.8, pan=0.2),
        Cue(lit - 0.8, "an old woman reaching up: cloth rustle, the lantern's little door creaks open", -16),
        Cue(lit, "the last lantern lights: the wick catches with a soft whump, warm glass ring", -8),
        Cue(7.6, "small light footsteps in snow coming up the lantern path, far then nearer", -18,
            dur=5.4, pan=-0.5),
        Cue(9.4, "the old wolf wakes: a low huff, it lifts its head", -18, pan=0.25),
        Cue(10.4, "air opening up over the treetops as the view rises", -20, dur=2.6),
        Cue(FLAT, "everything hushes to paper: a dry rustle as the image flattens", -12, dur=0.6),
        Cue(TURN0, "the page turns over: paper whoosh (s01's turn, in reverse)", -6, dur=TURN_DUR),
        Cue(LAND, "the red paper triangle settles on the line: a soft paper tap", -12),
    ]
