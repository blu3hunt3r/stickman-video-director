"""RED sets: props. World coords, y down, zoom-1 px (the girl is ~380 px tall).

    Lantern      iron lantern; anchor = top of the handle ring; lit glass glows; swings; breaks
    swing_angle  pendulum response of a carried / hung lantern to its anchor's motion
    lantern_burst  the lantern smashed: glass shards, a burst of fire, burning oil on the snow
    Basket       wicker basket with bread, wine and the lantern; anchor = handle top (grip)
    basket_spill deterministic spill of the contents onto a terrain
    hood_poly / draw_hood   the red hood silhouette (worn-shape, hanging on a thread, lying)
    hood_on_branch          a red hood caught on a branch, swaying
    Doorway      the mother's doorway: wall, open door, warm interior, light spilling on snow
    draw_stake   a snow-covered stake (see sets_terrain.stake_shape)

Every draw takes `f` (Frame) for glow/light and a cairo context (usually a layer) for the
silhouette. Colors come from the mood (ink, snow, lamp amber) and HOOD_RED.
"""
import math

import cairo
import numpy as np

from engine import draw
from engine.core import clamp, lerp, hash01, fbm1, smoothstep
from .sets_common import (get_mood, mix, INK, SNOW, AMBER, HOOD_RED, glow, light_pool, flick, rnd, srnd,
                          soft_layer, fogged)
from .sets_terrain import stake_shape

G_PX = 2800.0          # gravity in px/s^2 at zoom 1 (1 m ~ 316 px)


# ============================================================================ lantern
class Lantern:
    """An iron hand lantern. `size` 1.0 ~ 74 px from handle top to base (the girl's lantern);
    village post lanterns use ~1.5. Local frame: anchor (handle top) at (0, 0), +y down.

    Anchors (local, size 1, before rotation): handle top (0, 0); flame (0, 46); base (0, 74)."""

    def __init__(self, size=1.0):
        self.size = size

    def _local(self):
        s = self.size
        ink = []
        # handle ring (a thick arc)
        ring = []
        for i in range(13):
            th = math.pi * (1.0 + i / 12.0)
            ring.append((math.cos(th) * 11 * s, 11 * s + math.sin(th) * 11 * s))
        inner = []
        for i in range(12, -1, -1):
            th = math.pi * (1.0 + i / 12.0)
            inner.append((math.cos(th) * 8 * s, 11.5 * s + math.sin(th) * 8 * s))
        ink.append(ring + inner)
        # cap: a little roof with a finial and vent
        ink.append([(-17 * s, 26 * s), (-6 * s, 15 * s), (-3 * s, 11 * s), (3 * s, 11 * s), (6 * s, 15 * s),
                    (17 * s, 26 * s), (13 * s, 29 * s), (-13 * s, 29 * s)])
        # cage frame: two side bars, middle bar, a top band and the base
        ink.append([(-13 * s, 28 * s), (-10 * s, 28 * s), (-10 * s, 64 * s), (-13 * s, 64 * s)])
        ink.append([(10 * s, 28 * s), (13 * s, 28 * s), (13 * s, 64 * s), (10 * s, 64 * s)])
        ink.append([(-1.2 * s, 28 * s), (1.2 * s, 28 * s), (1.2 * s, 64 * s), (-1.2 * s, 64 * s)])
        ink.append([(-15 * s, 62 * s), (15 * s, 62 * s), (17 * s, 70 * s), (12 * s, 74 * s), (-12 * s, 74 * s), (-17 * s, 70 * s)])
        glass = [(-10 * s, 29 * s), (10 * s, 29 * s), (10 * s, 63 * s), (-10 * s, 63 * s)]
        flame = (0.0, 47 * s)
        return ink, glass, flame

    def geometry(self, anchor, angle=0.0):
        """World geometry for a lantern hanging from `anchor` (x, y), rotated `angle` degrees
        (positive = swung clockwise, the base moves left->right... i.e. toward +x when > 0
        means the body swings to the LEFT; use swing_angle()'s sign convention)."""
        ink, glass, flame = self._local()
        a = math.radians(angle)
        ca, sa = math.cos(a), math.sin(a)

        def T(p):
            return (anchor[0] + p[0] * ca - p[1] * sa, anchor[1] + p[0] * sa + p[1] * ca)

        return dict(ink=[[T(p) for p in poly] for poly in ink], glass=[T(p) for p in glass], flame=T(flame),
                    base=T((0, 74 * self.size)))

    def draw(self, f, ctx, anchor, angle=0.0, lit=1.0, t=0.0, mood=None, par=1.0, glow_r=None, seed=0,
             tint=0.0, light=True):
        """Draw the lantern. lit 0..1 (flame strength). tint: pre-fog amount for far lanterns.
        Adds an emissive core + halo (f.emit) and a warm room-light (soft additive) when lit.
        Returns the world position of the flame (for light pools, ignition, etc.)."""
        mood = get_mood(mood)
        g = self.geometry(anchor, angle)
        ink = fogged(mood, tint) if tint > 0 else mood.ink
        fl = lit * flick(t, seed + 3) if lit > 0 else 0.0
        # glass: lit = hot amber, unlit = smoked dark glass
        if fl > 0.01:
            hot = mix(mood.lamp, SNOW, 0.45)
            col = mix(mix(INK, mood.lamp, 0.5), hot, clamp(fl))
            if tint > 0:
                col = mix(col, mood.fog_at(tint), tint * 0.5)
        else:
            col = mix(ink, mood.fog_at(0.4), 0.35)
        draw.poly(ctx, g["glass"])
        draw.fill(ctx, col)
        # the flame silhouette inside the glass (a darker teardrop core reads as a wick flame)
        if fl > 0.01:
            fx, fy = g["flame"]
            s = self.size
            draw.ellipse(ctx, (fx, fy + 3 * s), 3.2 * s, 7.5 * s * (0.8 + 0.3 * fl))
            draw.fill(ctx, mix(SNOW, mood.lamp, 0.15))
        for p in g["ink"]:
            draw.poly(ctx, p)
        draw.fill(ctx, ink)
        if fl > 0.01 and f is not None:
            gain = mood.lamp_gain * fl * (1.0 - 0.7 * tint)
            r = glow_r or 70 * self.size
            with f.emit(par=par) as G:
                glow(G, g["flame"], r * 0.55, mood.lamp, 0.9 * gain)
                glow(G, g["flame"], r * 1.4, mood.lamp, 0.25 * gain)
        return g["flame"]


def swing_angle(t, anchor_x, length=60.0, damping=1.6, t0=None, dt=1.0 / 240.0, kick=0.0, seed=0, wind=0.0):
    """Pendulum angle (degrees) of a lantern hanging `length` px below an anchor whose x is
    anchor_x(t) (a function of time, e.g. the girl's hand). Integrated deterministically from
    t0 (default t - 5 s). Positive angle = body swung toward -x (left). kick: extra random
    sway amplitude (degrees) for wind / walking jitter."""
    if t0 is None:
        t0 = t - 5.0
    gL = G_PX / max(length, 1.0)
    th, w = 0.0, 0.0
    tt = t0
    h = 1e-3
    n = int((t - t0) / dt)
    for i in range(max(n, 0)):
        acc = (anchor_x(tt + h) - 2 * anchor_x(tt) + anchor_x(tt - h)) / (h * h)
        # pendulum driven by horizontal pivot acceleration: th'' = -(g/L) sin th - (a/L) cos th
        dw = -gL * math.sin(th) + (acc / length) * math.cos(th) - damping * w + wind * gL * 0.02
        w += dw * dt
        th += w * dt
        tt += dt
    return math.degrees(th) + kick * fbm1(t * 1.3, seed)


def lantern_burst(f, ctx, pos, t, t0, mood=None, terrain=None, size=1.0, seed=5, par=1.0):
    """The lantern smashed at world `pos` at time t0: glass shards fly (ink), a burst of fire
    blooms (emissive + additive light) and burning oil spreads on the snow, then gutters.
    Returns dict(fire=0..1 intensity, center=(x, y), radius) for lighting / ignition."""
    mood = get_mood(mood)
    if t < t0:
        return dict(fire=0.0, center=pos, radius=0.0)
    a = t - t0
    gy = float(terrain.snow_y(pos[0])) if terrain is not None else pos[1] + 40
    # shards (ink triangles, ballistic, land on the snow)
    shards = []
    for i in range(14):
        vx = srnd(seed, i, 1) * 520 * size
        vy = -(260 + 420 * rnd(seed, i, 2)) * size
        x = pos[0] + vx * a
        y = pos[1] + vy * a + 0.5 * G_PX * a * a
        gyx = float(terrain.snow_y(x)) if terrain is not None else gy
        if y > gyx:
            # landed: find time of landing, then stay
            A, B, C = 0.5 * G_PX, vy, pos[1] - gyx
            disc = max(B * B - 4 * A * C, 0.0)
            tl = (-B + math.sqrt(disc)) / (2 * A)
            x = pos[0] + vx * tl
            y = float(terrain.snow_y(x)) if terrain is not None else gy
            rot = rnd(seed, i, 3) * 360
        else:
            rot = rnd(seed, i, 3) * 360 + a * 900 * srnd(seed, i, 4)
        r = (4 + 6 * rnd(seed, i, 5)) * size
        tri = [(x + math.cos(math.radians(rot + k * 120 + 25 * srnd(seed, i, k))) * r,
                y + math.sin(math.radians(rot + k * 120 + 25 * srnd(seed, i, k))) * r * 0.7) for k in range(3)]
        shards.append(tri)
    for tri in shards:
        draw.poly(ctx, tri)
    draw.fill(ctx, mood.ink)
    # fire: fast bloom, then a pool of burning oil that gutters over ~6 s
    bloom = math.exp(-a / 0.18) * clamp(a / 0.03)
    pool = clamp(a / 0.25) * math.exp(-max(a - 1.5, 0.0) / 5.0)
    fl = flick(t, seed + 9, rate=11.0, depth=0.35)
    R = (60 + 160 * clamp(a / 0.4)) * size
    cx, cy = pos[0], lerp(pos[1], gy, clamp(a / 0.25))
    # flame tongues (crisp, hot) over the pool
    n = 9
    for i in range(n):
        u = (i + 0.5) / n - 0.5
        x = cx + u * R * 1.3
        hgt = (30 + 70 * rnd(seed, i, 7)) * size * pool * fl * (0.6 + 0.4 * math.sin(t * (9 + i) + i))
        if hgt < 3:
            continue
        base_y = float(terrain.snow_y(x)) if terrain is not None else cy
        sw = 8 * math.sin(t * 7 + i * 2.1) * size
        flame = [(x - 10 * size, base_y), (x - 6 * size + sw * 0.3, base_y - hgt * 0.5), (x + sw, base_y - hgt),
                 (x + 6 * size + sw * 0.3, base_y - hgt * 0.45), (x + 10 * size, base_y)]
        draw.smooth(ctx, flame, close=True, tension=0.5)
    draw.fill(ctx, mix(mood.lamp, SNOW, 0.35))
    inten = max(bloom * 1.6, pool * 0.9) * fl
    if f is not None and inten > 0.01:
        with f.emit(par=par) as G:
            glow(G, (cx, cy - 30 * size), R * 0.9, mood.lamp, 0.8 * inten)
            glow(G, (cx, cy - 20 * size), R * 0.35, mix(mood.lamp, SNOW, 0.4), 0.9 * inten)
        with soft_layer(f, par, k=6, op="add", blur=30.0) as A:
            light_pool(A, (cx, gy), R * 2.6, R * 0.6, mood.lamp, 0.35 * inten)
            glow(A, (cx, cy - 60 * size), R * 3.2, mood.lamp, 0.22 * inten)
    return dict(fire=inten, center=(cx, cy), radius=R)


# ============================================================================ basket
class Basket:
    """Wicker basket with a cloth, a loaf, a wine bottle and the lantern sticking out.
    Anchor (local (0, 0)) = top of the handle, where the hand grips. size 1 ~ 84 px wide.
    Local anchors (size 1): handle top (0, 0); rim center (0, 56); bottom (0, 104)."""

    ITEMS = ("bread", "bottle", "lantern", "cloth")

    def __init__(self, size=1.0):
        self.size = size

    def _body(self):
        s = self.size
        body = [(-42 * s, 54 * s), (42 * s, 54 * s), (38 * s, 66 * s), (33 * s, 96 * s), (28 * s, 104 * s),
                (-28 * s, 104 * s), (-33 * s, 96 * s), (-38 * s, 66 * s)]
        # rim lip and weave notches along the outline (detail in the silhouette)
        notch = []
        for i in range(7):
            x = -30 * s + i * 10 * s
            notch.append([(x - 2 * s, 104 * s), (x + 2 * s, 104 * s), (x, 108 * s)])
        handle_o, handle_i = [], []
        for i in range(17):
            th = math.pi * (1 + i / 16.0)
            handle_o.append((math.cos(th) * 36 * s, 56 * s + math.sin(th) * 56 * s))
        for i in range(16, -1, -1):
            th = math.pi * (1 + i / 16.0)
            handle_i.append((math.cos(th) * 30 * s, 56 * s + math.sin(th) * 50 * s))
        return body, notch, handle_o + handle_i

    def _contents(self, items):
        s = self.size
        out = {}
        if "bread" in items:
            out["bread"] = draw.ellipse_pts((-20 * s, 48 * s), 24 * s, 15 * s, n=20, angle=-14)
        if "bottle" in items:
            # tilted wine bottle: shoulders, long neck, cork
            b = [(12 * s, 58 * s), (14 * s, 30 * s), (19 * s, 22 * s), (21 * s, -2 * s), (20 * s, -8 * s),
                 (27 * s, -8 * s), (26 * s, -2 * s), (27 * s, 22 * s), (33 * s, 30 * s), (32 * s, 58 * s)]
            out["bottle"] = b
        if "lantern" in items:
            # the lantern's cap and ring peeking out at the back
            out["lantern"] = [(-4 * s, 54 * s), (-4 * s, 40 * s), (-9 * s, 40 * s), (0, 30 * s), (9 * s, 40 * s),
                              (4 * s, 40 * s), (4 * s, 54 * s)]
        if "cloth" in items:
            out["cloth"] = [(-40 * s, 54 * s), (-10 * s, 50 * s), (-30 * s, 74 * s), (-36 * s, 70 * s)]
        return out

    def draw(self, ctx, grip, angle=0.0, items=ITEMS, mood=None, ink=None):
        """Draw the basket hanging from `grip` (world), rotated `angle` degrees."""
        mood = get_mood(mood)
        ink = ink or mood.ink
        a = math.radians(angle)
        ca, sa = math.cos(a), math.sin(a)

        def T(p):
            return (grip[0] + p[0] * ca - p[1] * sa, grip[1] + p[0] * sa + p[1] * ca)

        body, notch, handle = self._body()
        polys = [body, handle] + notch + list(self._contents(items).values())
        for p in polys:
            draw.poly(ctx, [T(q) for q in p])
        draw.fill(ctx, ink)

    def item_poly(self, name):
        """Local outline of a loose item (centered at its own center) for spills."""
        s = self.size
        if name == "bread":
            return draw.ellipse_pts((0, 0), 22 * s, 13 * s, n=18)
        if name == "bottle":
            return [(-7 * s, 26 * s), (-8 * s, -4 * s), (-4 * s, -12 * s), (-3 * s, -26 * s), (3 * s, -26 * s),
                    (4 * s, -12 * s), (8 * s, -4 * s), (7 * s, 26 * s)]
        if name == "lantern":
            ink, glass, flame = Lantern(size=s)._local()
            return [(x, y - 37 * s) for x, y in glass]
        if name == "cloth":
            return [(-26 * s, 3 * s), (-8 * s, -6 * s), (20 * s, -4 * s), (28 * s, 4 * s), (6 * s, 8 * s)]
        return draw.ellipse_pts((0, 0), 10 * s, 10 * s, n=10)


def basket_spill(t, t0, origin, terrain, direction=1, size=1.0, seed=3, items=Basket.ITEMS, vel=(0.0, 0.0)):
    """Spill of the basket's contents, thrown from world `origin` at time t0 toward
    `direction` (+1 right / -1 left) with extra initial velocity `vel`. Returns a dict
    name -> (x, y, angle_deg, state) where state is 'air' | 'rolling' | 'rest'. y is the item
    center; resting items sit on terrain.snow_y. The lantern item also reports 'impact_t'."""
    out = {}
    for i, name in enumerate(items):
        if t < t0:
            out[name] = (origin[0], origin[1], 0.0, "held")
            continue
        vx = (direction * (180 + 320 * rnd(seed, i, 1)) + vel[0]) * (0.7 + 0.3 * size)
        vy = (-(320 + 380 * rnd(seed, i, 2)) + vel[1])
        spin = srnd(seed, i, 3) * 720
        half_h = {"bread": 12, "bottle": 7, "lantern": 17, "cloth": 4}.get(name, 8) * size
        x0, y0 = origin
        a = t - t0
        # time of landing on the terrain (bisection on the ballistic arc)
        def y_at(tt):
            return y0 + vy * tt + 0.5 * G_PX * tt * tt

        def gap(tt):
            x = x0 + vx * tt
            return y_at(tt) + half_h - float(terrain.snow_y(x))
        lo, hi = 0.0, 3.0
        if gap(1e-3) > 0:
            tl = 0.0
        else:
            for _ in range(36):
                mid = 0.5 * (lo + hi)
                if gap(mid) > 0:
                    hi = mid
                else:
                    lo = mid
            tl = hi
        if a < tl:
            out[name] = (x0 + vx * a, y_at(a), spin * a, "air")
            continue
        xl = x0 + vx * tl
        rolls = name in ("bottle", "bread", "lantern")
        roll_t = 0.9 if rolls else 0.15
        v0 = vx * (0.45 if rolls else 0.15)
        b = a - tl
        if b < roll_t:
            dx = v0 * (b - 0.5 * b * b / roll_t)
            state = "rolling"
        else:
            dx = v0 * 0.5 * roll_t
            state = "rest"
        x = xl + dx
        ang = spin * tl + (dx / max(half_h, 1.0)) * 57.3 if rolls else spin * tl
        ang_rest = 90.0 if name == "bottle" else (ang if name != "lantern" else 0.0)
        if state == "rest" and name in ("bottle",):
            ang = ang_rest
        out[name] = (x, float(terrain.snow_y(x)) - half_h * (0.75 if name != "cloth" else 0.3), ang, state)
        if name == "lantern":
            out["lantern_impact_t"] = t0 + tl
    return out


def draw_spill(f, ctx, t, t0, origin, terrain, direction=1, size=1.0, seed=3, mood=None, lantern_lit=1.0,
               basket_angle=None, skip=()):
    """Draw the spilled items (and the tipped basket lying where it landed)."""
    mood = get_mood(mood)
    st = basket_spill(t, t0, origin, terrain, direction, size, seed)
    B = Basket(size)
    for name in Basket.ITEMS:
        if name in skip or name not in st:
            continue
        x, y, ang, state = st[name]
        if name == "lantern":
            Lantern(size).draw(f, ctx, (x, y - 37 * size), ang, lit=lantern_lit, t=t, mood=mood)
            continue
        poly = B.item_poly(name)
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        draw.poly(ctx, [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in poly])
        draw.fill(ctx, mood.ink)
    return st


# ============================================================================ hoods
def hood_poly(anchor, size=70.0, angle=0.0, crumple=0.0, seed=0, worn=False):
    """The red hood silhouette. Hanging (default): hung by its peak at `anchor`, the cape
    flaring below; size = peak-to-hem height. crumple 0..1 morphs to a heap lying on the snow
    (anchor then = the heap's center on the ground). Returns a closed polygon (world)."""
    s = size / 70.0
    j = lambda k, a=1.0: srnd(seed, k) * a * s
    hang = [(0, 0), (8 * s + j(1), 8 * s), (13 * s + j(2), 20 * s), (12 * s, 29 * s), (7 * s, 34 * s),   # hood back
            (10 * s, 42 * s), (17 * s + j(3, 2), 56 * s), (22 * s + j(4, 2), 72 * s),                        # cape
            (13 * s, 68 * s + j(5, 2)), (7 * s, 74 * s), (-2 * s, 67 * s + j(6, 2)), (-10 * s, 71 * s),
            (-19 * s + j(7, 2), 64 * s), (-15 * s, 50 * s), (-8 * s, 39 * s), (-4 * s, 34 * s),
            (-9 * s, 30 * s), (-4 * s, 22 * s), (-12 * s + j(8), 15 * s), (-7 * s, 6 * s)]       # face opening
    heap = [(-30 * s, 0), (-24 * s, -8 * s), (-12 * s, -12 * s + j(9, 2)), (-2 * s, -9 * s), (6 * s, -16 * s + j(10, 2)),
            (16 * s, -10 * s), (26 * s, -7 * s), (32 * s, 0), (24 * s, 3 * s), (14 * s, 1 * s), (2 * s, 3 * s),
            (-6 * s, 1 * s), (-14 * s, 3 * s), (-22 * s, 2 * s), (-28 * s, 3 * s), (-32 * s, 1 * s), (-30 * s, 0),
            (-31 * s, 0), (-30 * s, 0), (-30 * s, 0)]
    pts = [lerp(p, q, crumple) for p, q in zip(hang, heap)] if crumple > 0 else hang
    a = math.radians(angle * (1 - crumple))
    ca, sa = math.cos(a), math.sin(a)
    return [(anchor[0] + x * ca - y * sa, anchor[1] + x * sa + y * ca) for x, y in pts]


def draw_hood(ctx, anchor, size=70.0, angle=0.0, crumple=0.0, seed=0, color=HOOD_RED, alpha=1.0):
    draw.smooth(ctx, hood_poly(anchor, size, angle, crumple, seed), close=True, tension=0.35)
    draw.fill(ctx, color, alpha)


def hood_sway(t, seed=0, amp=7.0, freq=0.55):
    """Gentle pendulum sway angle (degrees) for a hanging hood."""
    return amp * (0.75 * math.sin(2 * math.pi * freq * t + 6.28 * hash01(seed, 1)) + 0.4 * fbm1(t * 0.7, seed + 3))


def hood_on_branch(ctx, f, branch_pt, t, size=70.0, seed=0, mood=None, tint=0.0, thread=18.0):
    """A red hood caught on a branch: a short tie from `branch_pt`, swaying. tint pre-fogs
    the red for far layers. Returns the hood's hang point."""
    mood = get_mood(mood)
    ang = hood_sway(t, seed, amp=5.0)
    a = math.radians(ang)
    hang = (branch_pt[0] - math.sin(a) * thread, branch_pt[1] + math.cos(a) * thread)
    ctx.move_to(*branch_pt)
    ctx.line_to(*hang)
    draw.stroke(ctx, fogged(mood, tint) if tint > 0 else mood.ink, max(1.5, size * 0.03))
    col = mix(HOOD_RED, mood.fog_at(tint), tint) if tint > 0 else HOOD_RED
    draw_hood(ctx, hang, size, ang, seed=seed, color=col)
    return hang


# ============================================================================ doorway
class Doorway:
    """The mother's doorway: a timber wall section with a door frame, the door swung open
    inward-left, a step, a little porch roof heavy with snow, warm interior light and its
    spill across the snow. x = threshold center, terrain = ground (PATH street).

    Anchors: threshold (x, y) where the mother stands; inside = a point just inside the door;
    door is 150 px wide x 420 px tall at size 1 (an adult stoops slightly)."""

    def __init__(self, x, terrain, size=1.0, wall=(-520.0, 420.0), seed=4, wall_on=True):
        self.x, self.T, self.size, self.wall, self.seed = x, terrain, size, wall, seed
        self.wall_on = wall_on          # False when the doorway is set into a house drawn elsewhere

    @property
    def threshold(self):
        return (self.x, float(self.T.ground_y(self.x)) - 10 * self.size)

    def draw_back(self, f, ctx, mood=None, open_=1.0, light=1.0, t=0.0):
        """The wall and the lit opening (behind the mother)."""
        mood = get_mood(mood)
        s = self.size
        x, gy = self.x, float(self.T.ground_y(self.x))
        wx0, wx1 = x + self.wall[0] * s, x + self.wall[1] * s
        dw, dh = 150 * s, 420 * s
        top = gy - 760 * s
        # interior light (seen through the open door): warm, hot at the floor
        fl = light * flick(t, self.seed, rate=4.0, depth=0.12)
        hot = mix(mood.lamp, SNOW, 0.25)
        draw.rect(ctx, x - dw / 2, gy - dh, x + dw / 2, gy)
        draw.linear(ctx, (0, gy - dh), (0, gy), [(0, mix(INK, mood.lamp, 0.55 * fl), 1),
                                                 (1, mix(mix(INK, mood.lamp, 0.12), mix(mood.lamp, hot, 0.5), fl), 1)])
        ctx.fill()
        # wall with log-end teeth on its corners, and the door opening cut out (even-odd)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        if self.wall_on:
            pts = [(wx0, gy + 30)]
            for i in range(8, -1, -1):                      # log ends up the left corner
                y = top + i * 82 * s
                pts += [(wx0, y + 62 * s), (wx0 - 16 * s, y + 52 * s), (wx0 - 16 * s, y + 10 * s), (wx0, y)]
            pts += [(wx0, top), (wx1, top), (wx1, gy + 30)]
            draw.poly(ctx, pts)
            draw.rect(ctx, x - dw / 2, gy - dh, x + dw / 2, gy + 1)
            draw.fill(ctx, mood.ink)
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        # door leaf swung open into the room (seen as a dark slab inside the opening)
        if open_ > 0.01:
            lw = dw * (1 - 0.82 * open_)
            draw.poly(ctx, [(x - dw / 2, gy - dh), (x - dw / 2 + lw, gy - dh + 14 * s * open_),
                            (x - dw / 2 + lw, gy - 6 * s * open_), (x - dw / 2, gy)])
            draw.fill(ctx, mood.ink)
        else:
            draw.rect(ctx, x - dw / 2, gy - dh, x + dw / 2, gy)
            draw.fill(ctx, mood.ink)
        # frame, step and porch roof with snow
        draw.rect(ctx, x - dw / 2 - 14 * s, gy - dh - 22 * s, x + dw / 2 + 14 * s, gy - dh)
        draw.rect(ctx, x - dw / 2 - 30 * s, gy - 18 * s, x + dw / 2 + 30 * s, gy + 6)
        draw.fill(ctx, mood.ink)
        roof = [(x - dw * 0.95, gy - dh - 40 * s), (x, gy - dh - 120 * s), (x + dw * 0.95, gy - dh - 40 * s),
                (x + dw * 0.95, gy - dh - 28 * s), (x, gy - dh - 104 * s), (x - dw * 0.95, gy - dh - 28 * s)]
        draw.poly(ctx, roof)
        draw.fill(ctx, mood.ink)
        snow = [(x - dw * 1.02, gy - dh - 36 * s), (x - dw * 0.5, gy - dh - 92 * s), (x, gy - dh - 136 * s),
                (x + dw * 0.5, gy - dh - 92 * s), (x + dw * 1.02, gy - dh - 36 * s), (x + dw * 0.9, gy - dh - 44 * s),
                (x, gy - dh - 118 * s), (x - dw * 0.9, gy - dh - 44 * s)]
        draw.smooth(ctx, snow, close=True, tension=0.3)
        draw.fill(ctx, mood.snow)
        if f is not None and fl > 0.01:
            g = mood.lamp_gain * fl
            with f.emit() as G:
                glow(G, (x, gy - dh * 0.35), dw * 0.9, mood.lamp, 0.35 * g)

    def draw_spill(self, f, mood=None, light=1.0, t=0.0):
        """The warm light thrown from the open door across the snow. Call AFTER the terrain's
        draw_front (the snow lip would cover it otherwise)."""
        mood = get_mood(mood)
        s = self.size
        x, gy = self.x, float(self.T.ground_y(self.x))
        dw, dh = 150 * s, 420 * s
        fl = light * flick(t, self.seed, rate=4.0, depth=0.12)
        if fl <= 0.01:
            return
        g = mood.lamp_gain * fl
        with soft_layer(f, 1.0, k=6, op="add", blur=40.0) as A:
            draw.linear(A, (0, gy - 10), (0, gy + 340 * s), [(0, mood.lamp, 0.6 * g), (1, mood.lamp, 0.0)])
            draw.poly(A, [(x - dw * 0.5, gy - 4), (x + dw * 0.5, gy - 4), (x + dw * 2.6, gy + 340 * s),
                          (x - dw * 2.6, gy + 340 * s)])
            A.fill()
            glow(A, (x, gy - dh * 0.4), dw * 2.6, mood.lamp, 0.14 * g)


def draw_stake(ctx, base, h=110.0, w=18.0, tilt=0.0, seed=0, mood=None, ground=None):
    """A snow-covered stake planted at base (x, y on the snow surface)."""
    mood = get_mood(mood)
    ink, cap, mound = stake_shape(base, h, w, tilt, seed, ground=ground)
    draw.poly(ctx, ink)
    draw.fill(ctx, mood.ink)
    draw.poly(ctx, mound)
    draw.fill(ctx, mood.snow)
    draw.smooth(ctx, cap, close=True, tension=0.4)
    draw.fill(ctx, mood.snow)
