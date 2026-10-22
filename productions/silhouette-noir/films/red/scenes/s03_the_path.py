"""s03 · THE PATH: the title, and the walk down into the quiet forest (14.0 s).

IN (dissolve from s02, 1.5 s): the same walk as s02's last seconds (one Actor timeline,
    girl_base(15, 800)): she walks right, small, feet at screen (540, 1350), camera zoom 0.42
    on her mean walking x. The forest begins: trunks in four fog layers, sparse at first.
0.50-1.37 the title RED: three hand-cut red paper letters spring up out of the far snow (R, E,
          D, 0.16 s apart, outback) and stand between the far trunks, 300 px tall, above her
          (their feet at screen y ~1130-1170). She walks on under them; they drift slowly left.
3.50-4.32 they fall over backwards into the snow, one, two, three (puffs of snow); crows burst
          from the trees; a fog bank rolls in over the fallen letters.
4.5-8.3   the Limbo walk: side-scrolling, the stakes and the rope of the path, the trail going
          down; light shafts, snow, her footprints.
8.30-12.0 push in to zoom 1.0 (her feet stay at (540, 1350)): the foreground trunks close in;
          [deeper] 8.78 the light darkens toward DEEP (mix 0.6 by 11.7);
          [quieter] 10.39 the snow thins to nothing and the shafts fade out (by 11.6): a hush.
          She sinks into her hood a little (head down 10.6-12.9).
OUT (dissolve to s04, 1.0 s): L.s03_cam(t) = Camera(x, PATH.ground_y(x) - 390, 1.0) with
    x = L.s03_girl_x(t) (5604.5 at t 14.0); L.s03_mood(t) = mood_mix(DAY, DEEP, 0.6) with
    shaft_a 0; L.s03_snow(t) = 0. She walks right in profile, basket in her near (right)
    hand, feet at (540, 1350).
"""
import math
from functools import lru_cache

from engine import atmos, bass, creatures, draw
from engine import figure as F
from engine.core import clamp, ease, hash01, lerp, smoothstep
from engine.timing import Cue, SceneTiming
from films.red import sets as S
from films.red.scenes import _lib_s02_s06 as L

FOREST = S.FOREST
PATH = S.PATH
DT, DX = L.S03_DT, L.S03_DX

# the title
TP = 0.27                               # its parallax plane: between the ghost and far trees
T_RISE = (0.50, 0.66, 0.82)             # each letter springs up out of the snow ...
T_FALL = (3.50, 3.68, 3.86)             # ... and falls over backwards into it
RISE_DUR, FALL_DUR = 0.55, 0.46
FLAT = 0.09                             # camera height / distance: a fallen letter is a sliver this tall
DIST = 4.2                              # the letters' distance in letter heights (keystone as they tip)
T_SCREEN = (540.0, 2.25)                # the title's centre is at screen x 540 at t 2.25
T_SINK = 10.0                           # letters stand this deep in the snow (layer px)
CROW_PAR = 0.56


@lru_cache(maxsize=None)
def _W():
    T = SceneTiming("red", "s03")
    return dict(path=T.at("path"), down=T.at("down"), valley=T.at("valley"), deeper=T.at("deeper"),
                quieter=T.at("quieter"), world=T.at("world"), became=T.at("became"))


# ----------------------------------------------------------------------------- the girl
@lru_cache(maxsize=None)
def girl():
    a = L.girl_base(DT, DX)
    L.carry(a, L.S02_TAKE - DT, 60.0 - DT, fade=0.3)
    # she looks up at the trees as the forest begins; later she sinks into her hood
    a.key("head", [(1.10, 0.0), (1.75, -13.0), (2.9, -11.0), (3.55, 0.0)], fade=0.3)
    a.key("head", [(10.55, 0.0), (11.25, 9.0), (12.3, 8.0), (12.95, 0.0)], fade=0.3)
    a.key("spine", [(10.55, 0.0), (11.25, 3.0), (12.3, 3.0), (12.95, 0.0)], fade=0.3)
    a.blink(2.35)
    a.blink(6.85)
    a.blink(11.7)
    return a


def _swing():
    return L.basket_pendulum(DT, DX)


@lru_cache(maxsize=None)
def prints():
    """Her footprints: every footfall from the forest edge on."""
    return L.walk_prints(L.girl_base(DT, DX), t0=-4.0, t1=16.0, size=40.0)


# ----------------------------------------------------------------------------- the title
def _lcam(t, par):
    return L.s03_cam(t).parallax(par)


@lru_cache(maxsize=None)
def _title():
    """(glyphs, X_T, cap height): RED cut at 300 px on screen at zoom 0.42 on plane TP."""
    lz = L.S03_Z0 ** TP
    h = 300.0 / lz
    T = bass.title_glyphs("RED", height=h, tracking=0.05, seed=5, rough=1.0, jitter=1.3)
    lc = _lcam(T_SCREEN[1], TP)
    X = lc.x + (T_SCREEN[0] - 540.0) / lc.zoom
    return T, X, h


def _tground(xl):
    """The snow the letters stand on (layer coords of TP), following the trail's slope."""
    return float(S.plane_ground(PATH, TP, 0.0)(xl))


def _theta(t, i):
    """Tilt of letter i (radians, + = leaning back, away from us; pi/2 = lying in the snow),
    or None before it rises."""
    tr, tf = T_RISE[i], T_FALL[i]
    if t < tr:
        return None
    if t < tf:
        u = clamp((t - tr) / RISE_DUR)
        return 0.5 * math.pi * (1.0 - ease("outback", u))      # springs up, over-leans, settles
    u = (t - tf) / FALL_DUR
    if u < 1.0:
        return 0.5 * math.pi * u ** 2.1                     # it tips over, faster and faster
    v = t - tf - FALL_DUR                                   # one small bounce on the snow
    return 0.5 * math.pi - 0.16 * math.exp(-9.0 * v) * abs(math.sin(14.0 * v))


def _letter_geom(i):
    T, X, h = _title()
    g = T[i]
    x0, y0, x1, y1 = g.bbox
    xc = X + 0.5 * (x0 + x1)
    base = _tground(xc) + T_SINK
    return g, X, xc, base, (x0, x1), y1


def _puff(c, x0, x1, y, t, t0, seed, col, n=16, alpha=0.9, sc=1.0):
    """A burst of snow lumps thrown up along [x0, x1] at ground y from t0 (pure function)."""
    dt0 = t - t0
    if dt0 < 0.0 or dt0 > 1.6:
        return
    for i in range(n):
        h = [hash01(seed, i, j) for j in range(7)]
        dt = dt0 - 0.08 * h[5]
        life = 0.6 + 0.7 * h[4]
        if dt <= 0.0 or dt > life:
            continue
        vx = (h[2] - 0.5) * 260.0 * sc
        vy = -(110.0 + 300.0 * h[3]) * sc
        px = lerp(x0, x1, h[1]) + vx * dt * (1.0 - 0.3 * dt)
        py = min(y + vy * dt + 0.5 * 620.0 * sc * dt * dt, y + 4.0)
        r = (6.0 + 11.0 * h[6]) * sc * (0.55 + 0.9 * dt / life)
        a = alpha * (1.0 - dt / life) ** 1.4
        c.new_path()
        c.arc(px, py, r, 0.0, 2.0 * math.pi)
        c.set_source_rgba(*col, a)
        c.fill()


def _draw_title(f, t, mood):
    if t < T_RISE[0] - 0.05 or t > 9.5:
        return
    lz = f.lcam(TP).zoom
    sc = 1.0 / lz
    red = S.HOOD_RED
    drift = S.fogged(mood, 0.80, mood.snow)
    puff = S.mix(mood.snow, drift, 0.35)
    with S.plane(f, TP) as c:
        for i in range(3):
            th = _theta(t, i)
            g, X, xc, base, (x0, x1), yb = _letter_geom(i)
            land = T_FALL[i] + FALL_DUR
            sink = ease("inout", (t - land - 0.15) / 1.5)    # snow and fog take the fallen letter
            if th is not None and sink < 1.0:
                # tipped back by th about its foot, seen from a little above: it foreshortens
                # (cos th + FLAT sin th) and its top narrows as it goes away (keystone)
                hg = max(yb - g.bbox[1], 1.0)
                ct, st = math.cos(th), math.sin(th)
                xm = 0.5 * (x0 + x1)
                c.new_path()
                for poly in g.polys:
                    for j, (px, py) in enumerate(poly):
                        v = (yb - py) / hg
                        k = 1.0 / max(0.2, 1.0 + v * st / DIST)
                        x = X + xm + (px - xm) * k
                        y = base - v * hg * (ct + FLAT * st) * k
                        (c.move_to if j == 0 else c.line_to)(x, y)
                    c.close_path()
                c.set_fill_rule(1)                     # even-odd: the counters of R and D
                c.set_source_rgb(*S.mix(red, drift, sink))
                c.fill()
            # a drift heaped against the letter's foot (it hides the cut edge in the snow)
            if t >= T_RISE[i]:
                w = (x1 - x0) + 70.0
                hgt = 26.0 * smoothstep(T_RISE[i], T_RISE[i] + 0.2, t)
                c.new_path()
                S.snow_mound(c, xc, lambda xx, b=base: b - T_SINK + 2.0, w, hgt, seed=40 + i)
                c.set_source_rgb(*drift)
                c.fill()
            _puff(c, X + x0, X + x1, base - T_SINK, t, T_RISE[i] + 0.05, 70 + i, puff, n=10, alpha=0.75, sc=sc * 0.8)
            _puff(c, X + x0 - 20, X + x1 + 20, base - T_SINK - 6.0, t, T_FALL[i] + FALL_DUR - 0.02,
                  80 + i, puff, n=18, alpha=0.9, sc=sc)
    # fog rolls in over the fallen letters (from the left)
    a = 0.7 * ease("inout", (t - 3.85) / 1.9) * (1.0 - ease("inout", (t - 6.6) / 2.4))
    if a > 0.003:
        T, X, h = _title()
        base = _tground(X)
        front = X + T.bbox[0] - 500.0 + (T.width + 900.0) * ease("out3", (t - 3.85) / 2.4)
        f.haze(mood.mist, a, y0=base - 0.95 * h, y1=base + 80.0, feather=320.0, tex=0.85, tex_scale=0.8,
               scroll=(32.0, -3.0), seed=12, par=TP, x0=X + T.bbox[0] - 1400.0, x1=front)


# ----------------------------------------------------------------------------- crows
@lru_cache(maxsize=None)
def _flock():
    """Crows startled out of the trees by the falling letters (on the mid fog plane)."""
    keys = [(3.95, 760.0, 1010.0), (4.6, 840.0, 760.0), (5.6, 1000.0, 470.0), (6.9, 1260.0, 230.0)]

    def path(t):
        # screen path -> layer coords of CROW_PAR at time t
        for (ta, xa, ya), (tb, xb, yb) in zip(keys[:-1], keys[1:]):
            if t <= tb:
                u = clamp((t - ta) / (tb - ta))
                break
        else:
            (ta, xa, ya), (tb, xb, yb) = keys[-2], keys[-1]
            u = (t - ta) / (tb - ta)
        p = (lerp(xa, xb, u), lerp(ya, yb, u))
        return _lcam(t, CROW_PAR).to_world(p)
    return creatures.CrowFlock(path, n=6, seed=9, size=58.0, spread=(150.0, 70.0), el=0.25)


def _draw_crows(f, t, mood):
    if not (3.95 <= t <= 7.2):
        return
    col = S.fogged(mood, 0.40)
    with S.plane(f, CROW_PAR) as c:
        _flock().draw(f, t, c, color=col)


# ----------------------------------------------------------------------------- render
def render(f, t, T):
    cam = L.s03_cam(t)
    f.set_camera(cam)
    mood = L.s03_mood(t)

    def hook(f_, i, Ly):
        if i == 1:
            _draw_title(f_, t, mood)
        elif i == 2:
            _draw_crows(f_, t, mood)

    FOREST.draw_back(f, mood, hook=hook)
    FOREST.draw_plane(f, mood)
    prints().draw(f, PATH, t, mood)
    a = girl()
    sk = a.skeleton(t)
    grip = L.basket_hand(sk, L.BASKET_SIDE)
    ang = -math.degrees(_swing().angle(t))
    with f.layer() as c:
        F.draw_figure(f, sk, a.look, c)
        L.draw_basket(c, grip, ang, mood.ink)
    hw = 230.0 * cam.zoom + 60.0
    FOREST.draw_front(f, mood, keep_clear=(540.0 - hw, 540.0 + hw))
    L.snow(f, mood, density=L.s03_snow(t), wind=20.0, gust=9.0, t=t, seed=23)


def cues(T):
    W = _W()
    return [
        Cue(-0.75, "forest ambience: snow hush, faint wind in the high branches, distant crows", -14, dur=11.1),
        Cue(-0.75, "small footsteps in snow, steady walk (continues from s02 into s04)", -15, dur=15.25),
        Cue(T_RISE[0], "paper title: three crisp paper snaps, the letters spring up (R, E, D)", -9, dur=0.5),
        Cue(T_FALL[0] + FALL_DUR, "the letters fall: three soft paper slaps into snow, one, two, three", -10, dur=0.9),
        Cue(T_FALL[0] + FALL_DUR + 0.08, "crows burst from the trees: wing claps, two caws, flying off up-right", -12,
            pan=0.35, dur=2.6),
        Cue(W["deeper"], "a long low branch creak, far off", -18, pan=-0.4),
        Cue(W["quieter"], "MIX: the hush. Drop the forest ambience to near silence for 3 s; keep only her "
            "footsteps in snow and a faint basket creak", -30, dur=3.0),
    ]
