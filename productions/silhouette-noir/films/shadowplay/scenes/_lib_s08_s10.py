"""Shared helpers for SHADOW PLAY s08 THE OTHER SIDE, s09 NINETY SECONDS and s10 THE TRAP.

* Puppet: an engine Actor performed in its own canonical space (ground y = 0) and drawn
  through an affine map into the world: a figure in a far window (s08), or a figure in the
  one-point-perspective room of apartment 9 (s09, s10), where the map follows its depth.
  Eyes are drawn by hand so their bloom lands where the figure is (figure.draw_eyes always
  glows at par 1 in untransformed coordinates).
* Room helpers for Apartment9: stage x <-> room X, perspective scale of a figure at depth Z.
* Paper doll and the jagged knife arm (Saul Bass, The Man with the Golden Arm). When the
  shadow-show module (_lib_shadow_show.py) exists, its doll and arm drawing are used, so the
  trap's woman and the killer's arm match s03 / s05.
"""
import math
from functools import lru_cache

import cairo

from engine import draw, bass
from engine import figure as FG
from engine.core import clamp, lerp, ease, hash01, noise1, fbm1
from engine.figure import Look
from engine.palette import RED, PAPER, SHADOWPLAY as PAL
from films.shadowplay import cast
from films.shadowplay.sets_base import PX_M, mix, mul, glow

INK = PAL.ink
AMBER = PAL.light
HOT = PAL.lamp_hot

try:                                       # the Bass designer's shadow show (s03, s05)
    from films.shadowplay.scenes import _lib_shadow_show as SHOW
except Exception:                          # noqa: BLE001 - optional neighbour module
    SHOW = None


# ----------------------------------------------------------------------------- timing
def k_(t, t0, dur, e="inout"):
    """Eased 0..1 progress of a move that starts at t0 and lasts dur."""
    if dur <= 0:
        return 1.0 if t >= t0 else 0.0
    return ease(e, (t - t0) / dur)


def env(t, a0, a1, b0, b1, e="inout"):
    """0 before a0, rises to 1 over a0..a1, holds, falls to 0 over b0..b1."""
    return k_(t, a0, a1 - a0, e) * (1.0 - k_(t, b0, b1 - b0, e))


# ----------------------------------------------------------------------------- looks
def her_look(coat_k=1.0):
    """Her in the RED trench coat. coat_k < 1 darkens the red toward ink (a dark room:
    the red only burns where light falls on it)."""
    lk = cast.her(coat=True)
    lk.colors = dict(lk.colors)
    lk.colors["coat"] = mix(INK, RED, clamp(coat_k))
    return lk


def him_look(flow=0.0):
    return cast.him(coat_flow=flow)


# ----------------------------------------------------------------------------- puppet
class Puppet:
    """An Actor drawn through a world map M (cairo.Matrix: canonical -> world).

    The Actor lives in its own canonical space: feet on y = 0, x in px at the body's own
    scale (an adult ~600 px). M usually is translate(foot point) * scale(k) * translate(-x0, 0).
    """

    def __init__(self, actor, look, eyes=True):
        self.a = actor
        self.look = look
        self.eyes = eyes

    def skeleton(self, t):
        return self.a.skeleton(t)

    def world(self, M, p):
        return M.transform_point(p[0], p[1])

    def joint(self, t, name, M):
        return self.world(M, self.a.joint(t, name))

    def draw(self, f, t, ctx, M, par=1.0, color=None, eyes=None, eye_glow=1.0, eye_open=None, look=None,
             sk=None, emit=True):
        """Draw the figure on ctx (already in world coords of layer `par`) through M.
        Returns the skeleton (canonical coords)."""
        sk = sk or self.a.skeleton(t)
        lk = look or self.look
        ctx.save()
        ctx.transform(M)
        FG.draw_figure(None, sk, lk, ctx, color=color, eyes=False)
        ctx.restore()
        if eyes is None:
            eyes = self.eyes
        if eyes and lk.eyes and eye_glow > 0.01:
            draw_eyes(f, sk, lk, ctx, M, par=par, glow_k=eye_glow, open_=eye_open, emit=emit)
        return sk


def draw_eyes(f, sk, look, ctx, M, par=1.0, glow_k=1.0, open_=None, emit=True, size=1.0, halo=1.0):
    """Limbo eyes of a canonical skeleton drawn through M (dots on ctx, halo on f.emit(par))."""
    e1, e2, r, w, front = FG.eye_points(sk, look)
    if front < -0.35:
        return
    vis = clamp((front + 0.35) / 0.35) if front < 0 else 1.0
    op = clamp(sk.pose.eyes.get("open", 1.0) if open_ is None else open_)
    g = sk.pose.eyes.get("glow", 1.0) * vis * glow_k
    if op <= 0.02 or g <= 0.01:
        return
    k = math.sqrt(abs(M.xx * M.yy - M.xy * M.yx))
    col = look.eye_color
    pts = [M.transform_point(*e1), M.transform_point(*e2)]
    rr = r * k * size
    for i, e in enumerate(pts):
        ri = rr * (1.0 if i == 0 else lerp(0.82, 1.0, w))
        draw.ellipse(ctx, e, ri * 0.9, max(ri * op, 0.3))
        draw.fill(ctx, col, clamp(g))
    if emit and f is not None:
        with f.emit(par=par) as G:
            for e in pts:
                draw.glow_disc(G, e, max(rr * 5.5, 3.0) * halo, col, 0.5 * clamp(g) * op)


def place_matrix(foot, k, x0=0.0, flip=False):
    """Canonical -> world: the canonical point (x0, 0) lands on world `foot`, scaled by k."""
    m = cairo.Matrix(xx=-k if flip else k, yy=k, x0=foot[0] + (k if flip else -k) * x0, y0=foot[1])
    return m


# ----------------------------------------------------------------------------- drawing helpers
def plain_look(lk):
    """A copy of a Look with no part colours (shadows, masks, rims)."""
    import copy
    q = copy.copy(lk)
    q.colors = {}
    return q


def draw_skeleton(ctx, sk, look, M, color=None, alpha=1.0):
    """draw_figure through the canonical -> world map M (no eyes)."""
    ctx.save()
    ctx.transform(M)
    FG.draw_figure(None, sk, look, ctx, color=color or INK, eyes=False, alpha=alpha)
    ctx.restore()


def occlude_figure(f, par, sk, look, M):
    """Black out the emissive buffer under a figure (f.emit glows are added after every
    layer, so a silhouette in front of a lit window must cut its bloom)."""
    with f.emit(par=par) as G:
        G.save()
        G.set_operator(cairo.OPERATOR_SOURCE)
        draw_skeleton(G, sk, plain_look(look), M, color=(0.0, 0.0, 0.0))
        G.restore()


def rim(A, sk, look, M, color, alpha, offset):
    """A crescent of light on the figure's edge facing away from `offset` (world px): the
    silhouette minus a copy of itself shifted by offset. A: an additive light context."""
    if alpha <= 0.005:
        return
    A.push_group()
    A.set_operator(cairo.OPERATOR_OVER)
    draw_skeleton(A, sk, look, M, color=color)
    A.set_operator(cairo.OPERATOR_DEST_OUT)
    A.save()
    A.translate(offset[0], offset[1])
    draw_skeleton(A, sk, look, M, color=(0.0, 0.0, 0.0))
    A.restore()
    A.pop_group_to_source()
    A.paint_with_alpha(clamp(alpha))


# ----------------------------------------------------------------------------- room helpers
class RoomMap:
    """Maps a canonical Actor (feet on y = 0, 1 m = PX_M px) into Apartment9's perspective.

    Canonical x / PX_M is the room X (metres). Depth Z is given per frame (a track); the whole
    figure is scaled by the perspective at its root depth (an affine approximation: the body is
    shallow compared with its distance to the eye). Feet planted while Z is constant never slide."""

    def __init__(self, apt):
        self.apt = apt
        self.room = apt.room

    def matrix(self, X, Z, x_canon=None):
        """World map for a figure whose root is at room (X, Z)."""
        r = self.room
        foot = r.P(X, 0.0, Z)
        k = r.ppm(Z) / PX_M
        xc = X * PX_M if x_canon is None else x_canon
        return place_matrix(foot, k, xc), k

    def scale(self, Z):
        return self.room.ppm(Z) / PX_M


# ----------------------------------------------------------------------------- paper doll
def doll_woman_pts_cache():
    return None


@lru_cache(maxsize=4)
def _doll_actor(kind):
    from engine.motion import Actor
    body = cast.DOLL_WOMAN if kind == "woman" else cast.DOLL_MAN
    a = Actor(body, None, x=0.0, ground=0.0, facing=1 if kind == "man" else -1, seed=7)
    a.stand(until=1e6, at=-1e6, idle=0.0)
    return a


def doll_skeleton(kind="woman"):
    """A stiff paper-doll pose (canonical, feet on y = 0, height = the doll body's height)."""
    a = _doll_actor(kind)
    p = a.pose(0.0)
    p = p.copy()
    # paper dolls: limbs a little apart from the body so the cut-out reads
    if kind == "woman":
        p.arms["L"].update(sh=-8.0, abd=14.0, elbow=10.0)
        p.arms["R"].update(sh=10.0, abd=14.0, elbow=14.0)
    else:
        p.arms["L"].update(sh=-6.0, abd=12.0, elbow=8.0)
        p.arms["R"].update(sh=8.0, abd=12.0, elbow=12.0)
    return FG.solve(p, a.body)


def draw_doll(ctx, foot, height, kind="woman", color=None, flip=False, paper=True):
    """A paper doll (cast.doll_woman / doll_man) standing on `foot` (world), `height` px tall.
    color None = PAPER (the object); pass INK for its shadow."""
    if SHOW is not None and hasattr(SHOW, "draw_doll"):
        try:
            SHOW.draw_doll(ctx, foot, height, kind=kind, color=color, flip=flip)
            return
        except TypeError:
            pass
    sk = doll_skeleton(kind)
    body = cast.DOLL_WOMAN if kind == "woman" else cast.DOLL_MAN
    lk = cast.doll_woman(ink=color or PAPER) if kind == "woman" else cast.doll_man(ink=color or PAPER)
    if not paper:
        lk.paper = False
    k = height / body.height
    M = place_matrix(foot, k, 0.0, flip=flip)
    ctx.save()
    ctx.transform(M)
    FG.draw_figure(None, sk, lk, ctx, color=color or PAPER, eyes=False)
    ctx.restore()


# ----------------------------------------------------------------------------- knife arm
def knife_arm(ctx, base, tip, color=None, width=26.0, grow=1.0, seed=3, knife=True, blade=1.0):
    """The killer's arm in Saul Bass cut paper (The Man with the Golden Arm) from the shoulder
    `base` to the fist `tip`, with a knife blade continuing past the fist. World coords."""
    col = color or INK
    if SHOW is not None and hasattr(SHOW, "knife_arm"):
        try:
            SHOW.knife_arm(ctx, base, tip, color=col, width=width, grow=grow, seed=seed)
            return
        except TypeError:
            pass
    bass.jagged_arm(ctx, base, tip, col, width=width, grow=grow, jags=3, jag=0.7, claw=1.1, seed=seed)
    if knife and grow > 0.98:
        ang = math.atan2(tip[1] - base[1], tip[0] - base[0])
        ca, sa = math.cos(ang), math.sin(ang)
        L = width * 3.6 * blade
        w = width * 0.36
        h0 = (tip[0] + ca * width * 0.9, tip[1] + sa * width * 0.9)
        nx, ny = -sa, ca
        pts = [(h0[0] + nx * w * 0.5, h0[1] + ny * w * 0.5), (h0[0] + ca * L * 0.78 + nx * w * 0.42, h0[1] + sa * L * 0.78 + ny * w * 0.42),
               (h0[0] + ca * L, h0[1] + sa * L), (h0[0] - nx * w * 0.5, h0[1] - ny * w * 0.5)]
        draw.poly(ctx, draw.cut_paper(pts, seed=seed + 4, amp=0.6, seg=(8.0, 20.0)))
        draw.fill(ctx, col)


# ============================================================================= figures in a room
from engine.motion import Actor                        # noqa: E402
from films.shadowplay import sets as SETS              # noqa: E402
from films.shadowplay.sets_base import shadow_screen, glow_ellipse   # noqa: E402
from films.shadowplay.sets_props import Sheet, BareLamp, lamp_light   # noqa: E402

SHEET_Z = 3.55


class Walker:
    """A figure moving through a one-point-perspective room (Room3D coords, metres).

    The engine Actor performs in its own canonical space (feet on y = 0, 1 m = PX_M px);
    walks are planned there along x by the LATERAL part of each move (so planted feet do not
    skate sideways) with the yaw of the real 3-D heading, while the room position (X, Z) is
    interpolated by the canonical root's progress. matrix(t) maps canonical -> world."""

    def __init__(self, body, room, X, Z, yaw, seed=0, t0=-6.0, look=None):
        self.room = room
        self.a = Actor(body, look, x=X * PX_M, ground=0.0, facing=float(yaw), t0=t0, seed=seed)
        self.X0, self.Z0 = X, Z
        self.X, self.Z = X, Z
        self.legs = []
        self.places = []                 # (t, X, Z): instant moves (a cut)

    @property
    def cursor(self):
        return self.a.cursor

    def stand(self, until, **kw):
        self.a.stand(until=until, **kw)
        return self

    def turn(self, yaw, dur=0.35, at=None, via=90.0):
        self.a.turn(yaw, dur=dur, at=at, via=via)
        return self

    def go(self, X, Z, dur, at=None, gait="brisk", yaw=None, min_lat=0.3):
        """Walk to room (X, Z) taking about `dur` seconds. Returns the end time."""
        t0 = self.a.cursor if at is None else at
        dX, dZ = X - self.X, Z - self.Z
        dist = math.hypot(dX, dZ)
        heading = math.degrees(math.atan2(-dZ, dX))
        yw = heading if yaw is None else yaw
        c = math.cos(math.radians(yw))
        sgn = 1.0 if c >= 0 else -1.0
        D = max(abs(dX), min_lat * dist) * PX_M
        x0 = self.a.state["x"]
        x1 = x0 + sgn * D
        sp = (dist * PX_M / self.a.H) / max(dur, 0.05)
        self.a.walk(to=x1, gait=gait, speed=max(sp, 0.05), at=t0, yaw=yw, turn=0)
        t1 = self.a.cursor
        self.legs.append((t0, t1, x0, x1, (self.X, self.Z), (X, Z)))
        self.X, self.Z = X, Z
        return t1

    def place(self, t, X, Z):
        """Jump to (X, Z) at t (between shots)."""
        self.places.append((t, X, Z))
        return self

    def pos(self, t):
        """Room (X, Z) and canonical root x at t."""
        xr = self.a.root(t)[0]
        X, Z = self.X0, self.Z0
        for (t0, t1, x0, x1, p0, p1) in self.legs:
            if t < t0:
                break
            if t <= t1:
                if abs(x1 - x0) > 1e-6:
                    u = clamp((xr - x0) / (x1 - x0))
                else:
                    u = clamp((t - t0) / max(t1 - t0, 1e-6))
                X, Z = lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u)
                break
            X, Z = p1
        for (tp, Xp, Zp) in self.places:
            if t >= tp:
                X, Z = Xp, Zp
        return X, Z, xr

    def matrix(self, t):
        X, Z, xr = self.pos(t)
        r = self.room
        return place_matrix(r.P(X, 0.0, Z), r.ppm(Z) / PX_M, xr)

    def world(self, t, p):
        """A canonical point -> world at t."""
        return self.matrix(t).transform_point(p[0], p[1])

    def canon(self, t, p):
        """A world point -> canonical at t (for reach targets)."""
        m = self.matrix(t)
        m.invert()
        return m.transform_point(p[0], p[1])


# ============================================================================= paper dolls (the show's)
def doll_stage(room, X, Y_pelvis, Z, kind="woman", mirror=False, size=0.45):
    """Show stage (ox, oy, S) placing a show doll's pelvis (its rod top) at room (X, Y, Z).
    size: the man doll's height in metres (the woman is SHOW.HER_H of it)."""
    S = size * room.ppm(Z)
    px, py = room.P(X, Y_pelvis, Z)
    if SHOW is None:
        return (px, py, S)
    if kind == "woman":
        sx, hip = SHOW.WOMAN_X, SHOW._HIP * SHOW.HER_H
    else:
        sx, hip = SHOW.MAN_X, SHOW._HIP
    ox = px + sx * S if mirror else px - sx * S
    return (ox, py + hip * S, S)


def doll_casters(c, stage, kind="woman", mirror=False, u=-1.0, cuts=True):
    """The show's doll (and its rod) as opaque ink: for shadow buffers."""
    if SHOW is not None:
        SHOW.casters(c, u, (0, 0, 1, 1), mirror=mirror, stage_=stage, cuts=cuts, blood=False,
                     man=(kind == "man"), woman=(kind == "woman"))
        return
    ox, oy, S = stage
    draw_doll(c, (ox, oy), S * 0.95, kind=kind, color=(0, 0, 0))


def doll_object(c, stage, color, kind="woman", mirror=False, u=-1.0):
    """The same doll as a cut-paper object in `color` (pin holes stay holes)."""
    c.push_group()
    doll_casters(c, stage, kind, mirror, u, cuts=True)
    pat = c.pop_group()
    c.save()
    c.set_source_rgb(*color[:3])
    c.mask(pat)
    c.restore()


# ============================================================================= his Golden-Arm knife arm
def _to_w(pts, at, ang, S):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(at[0] + (x * ca - y * sa) * S, at[1] + (x * sa + y * ca) * S) for x, y in pts]


def golden_arm(c, sh, el, wr, color=None, blade_rel=150.0, blade=1.0, width=1.0):
    """The killer's real arm in the show's cut-paper Golden-Arm pieces (jagged upper arm and
    forearm, angular fist, knife), laid along his shoulder -> elbow -> wrist (world).
    blade_rel: knife angle relative to the forearm (deg; ~150 = ice-pick grip, pointing down
    when the arm is raised)."""
    col = color or INK
    a1 = math.atan2(el[1] - sh[1], el[0] - sh[0])
    a2 = math.atan2(wr[1] - el[1], wr[0] - el[0])
    L1 = math.hypot(el[0] - sh[0], el[1] - sh[1])
    L2 = math.hypot(wr[0] - el[0], wr[1] - el[1])
    if SHOW is None:
        bass.jagged_arm(c, sh, wr, col, width=0.35 * L1, jags=3, jag=0.7, claw=1.0, seed=3)
        return
    G = SHOW._geom()
    S1 = L1 / SHOW.L1
    S2 = L2 / SHOW.L2
    Sw1, Sw2 = S1 * width, S2 * width
    polys = [_to_w([(x, y * width) for x, y in G["upper"]], sh, a1, S1), _to_w(G["sh_disc"], sh, a1, Sw1),
             _to_w(G["el_disc"], el, a1, Sw1), _to_w([(x, y * width) for x, y in G["fore"]], el, a2, S2),
             _to_w(G["fist"], wr, a2, Sw2)]
    if blade > 0.01:
        a3 = a2 + math.radians(blade_rel)
        fi = (wr[0] + math.cos(a2) * SHOW.FIST * S2, wr[1] + math.sin(a2) * SHOW.FIST * S2)
        root = (fi[0] + math.cos(a3) * 0.012 * S2, fi[1] + math.sin(a3) * 0.012 * S2)
        for b in G["blade"]:
            polys.append(_to_w([(x * blade, y) for x, y in b], root, a3, S2))
    c.new_path()
    for p in polys:
        draw.poly(c, p)
    draw.fill(c, col)


def knife_tip(sh, el, wr, blade_rel=150.0):
    """World tip of the knife held by golden_arm()."""
    if SHOW is None:
        return wr
    a2 = math.atan2(wr[1] - el[1], wr[0] - el[0])
    L2 = math.hypot(wr[0] - el[0], wr[1] - el[1])
    S2 = L2 / SHOW.L2
    a3 = a2 + math.radians(blade_rel)
    fi = (wr[0] + math.cos(a2) * SHOW.FIST * S2, wr[1] + math.sin(a2) * SHOW.FIST * S2)
    L = (0.012 + SHOW.BLADE) * S2
    return (fi[0] + math.cos(a3) * L, fi[1] + math.sin(a3) * L)


# ============================================================================= apartment 9 for s09 / s10
class Room9:
    """Apartment 9 drawn from Apartment9's pieces, with what s09 / s10 need on top: the lamp
    anywhere (carried, set behind the sheet, crashing), the sheet bunched at the right end of
    its wire or pulled straight, shadows from several depths at once, the rig without the
    woman's rod, people and props sorted by depth, a lever handle that turns.

    draw(f, t, st): st keys (all optional)
      lamp      dict(X, Z, on, tilt=0, lift=0, broken=False, stand=True)
      cover     sheet 0 (bunched at the right) .. 1 (straight);  sheet=False: no sheet
      hit, fall, slashes   the stabbed sheet (s10): slashes [(p0, p1, width, u, open)] room-free
                world points; fall 0..1
      rig       dict(woman=True, dolls=True, doll_col=None)
      door      dict(open, hall, feet, locked, lever (0..1 turned))
      street, police, extra_lights
      casters   [(z, fn(c))] shapes behind the sheet (as the camera sees them) -> shadows on it
      wall_casters [(z, fn(c))] shapes in front of the back wall (lamp in front) -> its shadows
      items     [(z, fn(f, t))] people / things, drawn far -> near around the room's props
      rim       callable(f, t) drawn last (rim lights etc.)"""

    def __init__(self):
        self.apt = SETS.Apartment9((540.0, 880.0), 1.0)
        self.r = self.apt.room
        self.door = self.apt.door

    # ---------------------------------------------------------------- geometry
    def P(self, X, Y, Z):
        return self.r.P(X, Y, Z)

    def ppm(self, Z):
        return self.r.ppm(Z)

    def k(self, Z):
        return self.r.ppm(Z) / PX_M

    def edge_X(self, cover):
        X0, Yt, X1, Yh = self.apt.SHEET
        return lerp(0.60, X0, clamp(cover))

    def sheet_obj(self, cover):
        X0, Yt, X1, Yh = self.apt.SHEET
        zs = SHEET_Z
        xe = self.edge_X(cover)
        pins = 2 + int(round(4 * clamp(cover)))
        return Sheet(self.P(xe, Yt, zs), self.P(X1, Yt, zs), (Yt - Yh) * self.ppm(zs), pins=pins, seed=9)

    def bulb3d(self, lamp):
        a = math.radians(lamp.get("tilt", 0.0))
        by = self.apt.BULB_Y
        return (lamp["X"] + math.sin(a) * by, by * math.cos(a) + lamp.get("lift", 0.0), lamp["Z"])

    def lamp_obj(self, lamp):
        X, Z = lamp["X"], lamp["Z"]
        k = self.ppm(Z) * self.apt.BULB_Y / 520.0
        base = self.P(X, lamp.get("lift", 0.0), Z)
        return BareLamp(base, height=520.0, scale=k), k

    def wall_path(self, c):
        """The back wall minus the window (even-odd)."""
        S = self.r.surfaces()
        draw.poly(c, S["back"])
        X0, Y0, X1, Y1 = self.apt.WINDOW
        zb = self.r.zb
        draw.poly(c, [self.P(X0, Y0, zb), self.P(X1, Y0, zb), self.P(X1, Y1, zb), self.P(X0, Y1, zb)])

    # ---------------------------------------------------------------- the rig
    def draw_rig(self, L, woman=True):
        r = self.r
        P = r.P
        X, Z, w, d, h = self.apt.TABLE
        draw.poly(L, [P(X - 0.30, h, Z - 0.08), P(X + 0.34, h, Z - 0.08), P(X + 0.34, h + 0.07, Z - 0.08),
                      P(X - 0.30, h + 0.07, Z - 0.08)])
        for who, (rx, ry) in self.apt.RODS.items():
            if who == "woman" and not woman:
                c = P(X + rx, h + 0.11, Z)
                k = r.ppm(Z)
                draw.rect(L, c[0] - 0.03 * k, c[1] - 0.02 * k, c[0] + 0.03 * k, c[1] + 0.03 * k)   # empty clamp
                continue
            a = P(X + rx - 0.008, h + 0.07, Z)
            b = P(X + rx + 0.008, ry, Z)
            draw.rect(L, a[0], b[1], b[0], a[1])
            c = P(X + rx, h + 0.11, Z)
            k = r.ppm(Z)
            draw.rect(L, c[0] - 0.03 * k, c[1] - 0.02 * k, c[0] + 0.03 * k, c[1] + 0.03 * k)
        cx, cy, cz = self.apt._crank_center()
        cc = P(cx, cy, cz)
        k = r.ppm(cz)
        R = 0.085 * k
        L.new_sub_path()
        L.arc(cc[0], cc[1], R, 0, 2 * math.pi)
        L.new_sub_path()
        L.arc_negative(cc[0], cc[1], R * 0.78, 2 * math.pi, 0)
        for sp in range(4):
            a = math.radians(sp * 90)
            draw.capsule(L, cc, (cc[0] + R * 0.8 * math.cos(a), cc[1] - R * 0.8 * math.sin(a)), 0.006 * k, 0.006 * k)
        draw.circle(L, cc, 0.014 * k)
        mb = P(cx - 0.06, h, cz)
        draw.rect(L, mb[0] - 0.09 * k, mb[1] - 0.12 * k, mb[0] + 0.05 * k, mb[1])
        draw.capsule(L, cc, P(cx, h + 0.07, cz), 0.01 * k, 0.012 * k)
        draw.fill(L, INK)

    def rig_stage(self, kind):
        X, Z, w, d, h = self.apt.TABLE
        rx, ry = self.apt.RODS[kind]
        return doll_stage(self.r, X + rx, ry, Z, kind=kind, mirror=True)

    def draw_rig_dolls(self, L, woman=True, color=None):
        col = color or sets_mix(INK, PAPER, 0.5)
        doll_object(L, self.rig_stage("man"), col, kind="man", mirror=True)
        if woman:
            doll_object(L, self.rig_stage("woman"), col, kind="woman", mirror=True)

    # ---------------------------------------------------------------- the lever handle
    def lever(self, c, open_=0.0, turn=0.0, scale=1.0):
        """A lever door handle on the room side of the leaf (door px through the door's own
        projection): it dips as it turns (turn 0..1 = 0..38 deg)."""
        d = self.door
        ang = math.radians(100 * clamp(open_))
        cu, sn = math.cos(ang), math.sin(ang)
        u0 = d.w - 34.0
        v0 = d.h * 0.46
        th = math.radians(38.0 * clamp(turn))
        Lv = 64.0 * scale

        def Q(u, v, n):
            return d.project(u * cu, u * sn + n, v)
        # rose plate
        rose = [Q(u0 - 13, v0 - 13, 2), Q(u0 + 13, v0 - 13, 2), Q(u0 + 13, v0 + 13, 2), Q(u0 - 13, v0 + 13, 2)]
        draw.poly(c, rose)
        # neck out of the door, then the lever toward the hinge, dipping as it turns
        pts = []
        for (du, dv) in ((0.0, 5.0), (-Lv * math.cos(th), 5.0 - Lv * math.sin(th)),
                         (-Lv * math.cos(th) - 3.0, -4.0 - Lv * math.sin(th)), (0.0, -5.0)):
            pts.append(Q(u0 + du, v0 + dv, 22.0))
        draw.poly(c, pts)
        draw.poly(c, [Q(u0 - 4, v0 - 5, 2), Q(u0 + 4, v0 - 5, 2), Q(u0 + 4, v0 - 5, 22), Q(u0 - 4, v0 - 5, 22),
                      Q(u0 - 4, v0 + 5, 22), Q(u0 - 4, v0 + 5, 2)])
        draw.fill(c, INK)

    # ---------------------------------------------------------------- drawing
    def draw(self, f, t, st):
        apt, r = self.apt, self.r
        lamp = st.get("lamp") or dict(X=apt.LAMP_FRONT[0], Z=apt.LAMP_FRONT[1], on=0.0)
        stand = lamp.get("stand", True)
        broken = lamp.get("broken", False)
        lv = 0.0 if (broken or not stand) else clamp(lamp.get("on", 0.0), 0.0, 1.2)
        b3 = self.bulb3d(lamp)
        behind = lamp["Z"] > SHEET_Z
        has_sheet = st.get("sheet", True)
        cover = clamp(st.get("cover", 1.0)) if has_sheet else 0.0
        fall = st.get("fall", 0.0)
        xe = self.edge_X(cover)
        # how much of the lamp the sheet hides (it slides across from the right)
        hide = 0.0
        if behind and has_sheet:
            hide = clamp((lamp["X"] + 0.06 - xe) / 0.12) * (1.0 - clamp(fall * 1.4))
        door = st.get("door") or {}
        dop = door.get("open", 0.0)
        hall = door.get("hall", 0.0)
        street = st.get("street", 0.30)
        police = st.get("police", 0.0)
        # 1) the box and the window
        with f.layer() as L:
            r.draw_box(L)
            apt.draw_window(f, t, L, street=street, police=police)
        lights = apt.lights(t, lamp=0.0, sheet=cover > 0.6, street=street, police=police, door_open=dop,
                            hall=hall, door_mask=door.get("mask"))
        if lv > 0.01:
            lights.append(dict(kind="point", pos=b3, color=sets_mix(AMBER, HOT, 0.5),
                               power=2.2 * lv * (1.0 - 0.45 * hide), r0=0.3))
            if behind and hide > 0.01:
                lights.append(dict(kind="area", pos=(lamp["X"], 1.5, SHEET_Z - 0.05), normal=(0, 0, -1),
                                   color=AMBER, power=1.0 * lv * hide * cover, r0=0.6))
        lights += list(st.get("extra_lights", ()))
        z0, z1 = apt.DOOR_Z
        holes = [("back",) + tuple(apt.WINDOW), ("left", z0, 0.0, z1, apt.DOOR_H)]
        r.light_map(f, lights, ambient=0.012, holes=holes)
        # 1b) shadows on the back wall from a lamp in front (her at the window)
        if lv > 0.02 and not behind:
            for (z, fn) in st.get("wall_casters", ()):
                if lamp["Z"] < z < r.zb:
                    center, mag, soft = apt.shadow_map(z, b3, screen_z=r.zb - 0.01)
                    S = r.surfaces()
                    xs = [p[0] for p in S["back"]]
                    ys = [p[1] for p in S["back"]]
                    with f.layer() as L:
                        shadow_screen(L, fn, region=lambda c: (self.wall_path(c), c.set_fill_rule(1)),
                                      bbox=(min(xs), min(ys), max(xs), max(ys)), soft=max(1.5, soft),
                                      density=0.55 * min(1.0, lv), mag=mag, center=center)
        # items, sorted far -> near; the table + rig and the lamp are items too
        items = list(st.get("items", ()))
        rig = st.get("rig")
        if rig is not None:
            def table_fn(f_, t_, rig=rig):
                with f_.layer() as L:
                    self.apt.draw_table(L)
                    self.draw_rig(L, woman=rig.get("woman", True))
                    if rig.get("dolls", True):
                        self.draw_rig_dolls(L, woman=rig.get("woman", True), color=rig.get("doll_col"))
            items.append((apt.TABLE[1], table_fn))
        if stand:
            def lamp_fn(f_, t_):
                lo, kk = self.lamp_obj(lamp)
                sock = self.P(-r.hw + 0.02, 0.32, lamp["Z"] + 0.4)
                vis = 1.0 - hide
                with f_.layer() as L:
                    lo.draw(f_, t_, L, on=lv * vis if vis > 0.5 else 0.0, tilt=lamp.get("tilt", 0.0), broken=broken,
                            cord_to=(sock[0], self.P(lamp["X"], 0, lamp["Z"])[1]))
                if hide > 0.5 and lv > 0:
                    lamp_light(f_, lo.bulb(lamp.get("tilt", 0.0)), lv * 0.35, scale=kk)
            items.append((lamp["Z"], lamp_fn))
        items.sort(key=lambda it: -it[0])
        far = [it for it in items if it[0] > SHEET_Z]
        near = [it for it in items if it[0] <= SHEET_Z]
        for z, fn in far:
            fn(f, t)
        # the sheet
        if has_sheet:
            sh = self.sheet_obj(cover)
            hot = self.P(b3[0], b3[1], SHEET_Z)
            with f.layer() as L:
                sh.draw(f, t, L, light=hot, level=lv * (1.0 if behind else 0.55), back=behind,
                        base=sets_mix(INK, PAL.fog_at(1.0), 0.42), hit=st.get("hit"), fall=fall,
                        folds=lerp(2.4, 1.0, cover), tears=st.get("tears", ()))
                if lv > 0.02 and behind:
                    for (z, fn) in st.get("casters", ()):
                        if SHEET_Z < z < lamp["Z"] - 0.005:
                            center, mag, soft = apt.shadow_map(z, b3)
                            sh.shadow(L, t, fn, lamp=center, mag=mag, soft=max(1.0, soft),
                                      density=0.9 * min(1.0, lv), hit=st.get("hit"), fall=fall)
                slashes = st.get("slashes")
                if slashes:
                    slashes(f, t, L, sh)
            if lv > 0.01:
                sh.light(f, t, hot, level=lv * (1.0 if behind else 0.6) * lerp(0.35, 1.0, cover), back=behind)
        for z, fn in near:
            fn(f, t)
        # the door and its handle
        with f.layer() as L:
            self.door.draw(f, t, L, open=dop, hall=hall, locked=door.get("locked", 0.0), key=False,
                           feet=door.get("feet", ()), hall_fn=door.get("hall_fn"))
            self.lever(L, dop, door.get("lever", 0.0))
        self.door.light(f, t, open=dop, hall=hall, spill=door.get("spill", 0.0), feet=door.get("feet", ()))
        after = st.get("after")
        if after is not None:
            after(f, t)


def sets_mix(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k)
