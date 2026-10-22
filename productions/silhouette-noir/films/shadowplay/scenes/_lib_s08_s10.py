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
    red = mix(INK, RED, clamp(coat_k))
    lk.colors["coat"] = red
    lk.colors["arm"] = red                 # the sleeves are the coat (cast.her: one red shape)
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



BULB_H = 1.62 * 542.0 / 520.0          # the drawn BareLamp's bulb centre above its base (m)


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


class Walker:
    """A figure moving through a one-point-perspective room (Room3D coords, metres).

    The engine Actor performs in its own canonical space (feet on y = 0, 1 m = PX_M px).
    Walks are planned there along x by max(lateral part, 0.3 x distance) with the yaw of the
    real 3-D heading (the engine shortens steps the same way when a figure walks in depth),
    and the room position (X, Z) follows the canonical root's progress, so planted feet stay
    planted. matrix(t) maps canonical -> world. yaw_at(t) is the body yaw without solving a
    pose (for props that follow the figure: no recursion through reach targets)."""

    def __init__(self, body, room, X, Z, yaw, seed=0, t0=-6.0, look=None):
        self.room = room
        self.a = Actor(body, look, x=X * PX_M, ground=0.0, facing=float(yaw), t0=t0, seed=seed)
        self.X0, self.Z0 = X, Z
        self.X, self.Z = X, Z
        self.legs = []
        self.places = []                 # (t, X, Z): instant moves (a cut)
        self.yaws = [(t0, float(yaw))]

    @property
    def cursor(self):
        return self.a.cursor

    def _ykey(self, t, y):
        py = self.yaws[-1][1]
        self.yaws.append((t, py + _wrap(y - py)))

    def stand(self, until, **kw):
        if until > self.a.cursor + 0.005:
            self.a.stand(until=until, **kw)
        return self

    def turn(self, yaw, dur=0.35, at=None, via=90.0):
        t0 = self.a.cursor if at is None else at
        self.a.turn(yaw, dur=dur, at=t0, via=via)
        seg = self.a.segs[-1]
        y0 = self.yaws[-1][1]
        self.yaws.append((t0, y0))
        self.yaws.append((t0 + dur, y0 + (seg.b - seg.a)))
        return self

    def go(self, X, Z, dur, at=None, gait="brisk", yaw=None, min_lat=0.3, blend=0.2):
        """Walk to room (X, Z) taking `dur` seconds. Returns the end time."""
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
        a = self.a
        n0, st0, c0 = len(a.segs), a.state, a.cursor
        for _ in range(6):                  # the engine adds a closing step + settle: fit dur
            a.walk(to=x1, gait=gait, speed=max(sp, 0.05), at=t0, yaw=yw, turn=0, blend=blend)
            took = a.cursor - t0
            if abs(took - dur) < 0.03 * dur + 0.01:
                break
            del a.segs[n0:]
            a.state = dict(st0, feet=dict(st0["feet"]))
            a.cursor = c0
            sp *= took / max(dur, 0.05)
        else:
            a.walk(to=x1, gait=gait, speed=max(sp, 0.05), at=t0, yaw=yw, turn=0, blend=blend)
        self.last_speed = sp
        t1 = a.cursor
        self.legs.append((t0, t1, x0, x1, (self.X, self.Z), (X, Z)))
        self.yaws.append((t0, self.yaws[-1][1]))
        self._ykey(t0 + blend, yw)
        self._ykey(t1, yw)
        self.X, self.Z = X, Z
        return t1

    def place(self, t, X, Z):
        """Jump to (X, Z) at t (between shots)."""
        self.places.append((t, X, Z))
        return self

    def yaw_at(self, t):
        ks = self.yaws
        if t <= ks[0][0]:
            return ks[0][1]
        for i in range(1, len(ks)):
            if t <= ks[i][0]:
                t0, y0 = ks[i - 1]
                t1, y1 = ks[i]
                if t1 - t0 < 1e-6:
                    return y1
                return lerp(y0, y1, ease("inout", (t - t0) / (t1 - t0)))
        return ks[-1][1]

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

    def ahead(self, t, fwd, right):
        """Room (X, Z) of a point `fwd` m ahead of the figure and `right` m to its right."""
        X, Z, _ = self.pos(t)
        a = math.radians(self.yaw_at(t))
        dx, dz = math.cos(a), -math.sin(a)
        rx, rz = -math.sin(a), -math.cos(a)
        return X + fwd * dx + right * rx, Z + fwd * dz + right * rz


def rim_offset(center, light, px):
    """Offset for rim(): the crescent lands on the side of the figure facing `light`."""
    dx, dy = light[0] - center[0], light[1] - center[1]
    n = math.hypot(dx, dy) or 1.0
    return (-dx / n * px, -dy / n * px)


def draw_walker(f, t, w, look, color=None, rims=(), eyes=0.0, eye_open=None, eye_size=1.0, occlude=True,
                sk=None, alpha=1.0):
    """Draw a Walker's figure at t (main layer): ink silhouette with the look's part colours,
    additive rims [(rgb, alpha, offset px)], Limbo eyes (glow `eyes`), and erase the bloom
    under it (f.emit glows drawn before it are hidden behind it). Returns (skeleton, M)."""
    M = w.matrix(t)
    sk = sk or w.a.skeleton(t)
    with f.layer() as Lc:
        draw_skeleton(Lc, sk, look, M, color=color, alpha=alpha)
    if occlude:
        occlude_figure(f, 1.0, sk, look, M)
    live = [r for r in rims if r[1] > 0.005]
    if live:
        with f.light() as A:
            for (col, a, off) in live:
                rim(A, sk, look, M, col, a, off)
    if eyes > 0.01:
        with f.layer() as Lc:
            draw_eyes(f, sk, look, Lc, M, par=1.0, glow_k=eyes, open_=eye_open, size=eye_size)
    return sk, M


# ============================================================================= paper dolls (the show's)
def doll_stage_at(pelvis, S, kind="woman", mirror=False):
    """Show stage (ox, oy, S) that puts a show doll's pelvis (its rod top) on world `pelvis`;
    S = the man doll's height in world px (the woman is SHOW.HER_H of it)."""
    px, py = pelvis
    if SHOW is None:
        return (px, py, S)
    if kind == "woman":
        sx, hip = SHOW.WOMAN_X, SHOW._HIP * SHOW.HER_H
    else:
        sx, hip = SHOW.MAN_X, SHOW._HIP
    ox = px + sx * S if mirror else px - sx * S
    return (ox, py + hip * S, S)


def doll_stage(room, X, Y_pelvis, Z, kind="woman", mirror=False, size=0.45):
    """Show stage for a doll whose pelvis is at room (X, Y, Z); size = the man doll's height (m)."""
    return doll_stage_at(room.P(X, Y_pelvis, Z), size * room.ppm(Z), kind, mirror)


def _doll_pose(stage, mirror, u, crank_world):
    if SHOW is None or crank_world is None:
        return None
    ox, oy, S = stage
    p = SHOW.pose(u)
    wx, wy = crank_world
    xo = 2 * ox - wx if mirror else wx
    p["crank"] = ((xo - ox) / S, (wy - oy) / S)
    return p


def doll_casters(c, stage, kind="woman", mirror=False, u=-1.0, cuts=True, crank_world=None):
    """The show's doll (and its rod) as opaque ink: for shadow buffers."""
    if SHOW is not None:
        SHOW.casters(c, u, (0, 0, 1, 1), mirror=mirror, stage=stage, pose=_doll_pose(stage, mirror, u, crank_world),
                     cuts=cuts, blood=False, man=(kind == "man"), woman=(kind == "woman"))
        return
    ox, oy, S = stage
    draw_doll(c, (ox, oy), S * 0.95, kind=kind, color=(0, 0, 0))


def doll_object(c, stage, color, kind="woman", mirror=False, u=-1.0, clip_y=None, crank_world=None, alpha=1.0):
    """The same doll as a cut-paper object in `color` (pin holes stay holes). clip_y: hide
    what is below this world y (the rod going into the table)."""
    c.push_group()
    doll_casters(c, stage, kind, mirror, u, cuts=True, crank_world=crank_world)
    pat = c.pop_group()
    c.save()
    if clip_y is not None:
        c.rectangle(-1e5, -1e5, 2e5, 1e5 + clip_y)
        c.clip()
    c.set_source_rgba(color[0], color[1], color[2], alpha)
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
def sets_mix(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k)


class Room9:
    """Apartment 9 drawn from Apartment9's pieces, with what s09 / s10 need on top: the lamp
    anywhere (carried, set behind the sheet, crashing), the sheet bunched at the LEFT end of
    its wire or pulled straight, shadows from several depths at once (on the sheet and on the
    back wall), the rig with or without the woman's doll, people and props sorted by depth,
    a lever handle that turns.

    draw(f, t, st): st keys (all optional)
      lamp      dict(X, Z, on, tilt=0, lift=0, broken=False, stand=True)
      cover     sheet 0 (bunched at the left) .. 1 (straight);  sheet=False: no sheet
      hit, fall, tears   the stabbed sheet (Sheet); slashes: fn(f, t, ctx, sheet) drawn on it
      rig       dict(woman=True, dolls=True) or None (no table)
      door      dict(open, hall, feet, locked, lever (0..1 turned), spill, mask, hall_fn)
      street, police, extra_lights
      casters   [(z, fn(c))] shapes behind the sheet (as the camera sees them) -> its shadows
      wall_casters [(z, fn(c))] shapes in front of the back wall (lamp in front) -> its shadows
      items     [(z, fn(f, t))] people / things, drawn far -> near around the room's props
      after     fn(f, t) drawn last"""

    BUNCH = 0.35

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
        """Room X of the sheet's free (right) edge."""
        return lerp(self.apt.SHEET[0] + self.BUNCH, self.apt.SHEET[2], clamp(cover))

    def sheet_obj(self, cover):
        X0, Yt, X1, Yh = self.apt.SHEET
        xe = self.edge_X(cover)
        pins = 2 + int(round(4 * clamp(cover)))
        return Sheet(self.P(X0, Yt, SHEET_Z), self.P(xe, Yt, SHEET_Z), (Yt - Yh) * self.ppm(SHEET_Z), pins=pins, seed=9)

    def bulb3d(self, lamp):
        a = math.radians(lamp.get("tilt", 0.0))
        return (lamp["X"] + math.sin(a) * BULB_H, lamp.get("lift", 0.0) + BULB_H * math.cos(a), lamp["Z"])

    def lamp_obj(self, lamp):
        X, Z = lamp["X"], lamp["Z"]
        k = self.ppm(Z) * self.apt.BULB_Y / 520.0
        base = self.P(X, lamp.get("lift", 0.0), Z)
        return BareLamp(base, height=520.0, scale=k), k

    def hidden(self, lamp, cover, fall=0.0, sheet=True):
        """0..1: how much of the bulb the sheet hides from the camera."""
        if not sheet or lamp["Z"] <= SHEET_Z + 0.02:
            return 0.0
        X0 = self.apt.SHEET[0]
        b = self.P(*self.bulb3d(lamp))
        e0 = self.P(X0, 1.5, SHEET_Z)[0]
        e1 = self.P(self.edge_X(cover), 1.5, SHEET_Z)[0]
        rr = 0.04 * self.ppm(lamp["Z"])
        h = clamp((e1 - b[0] + rr) / (2 * rr)) * clamp((b[0] - e0 + rr) / (2 * rr))
        return h * (1.0 - clamp(fall * 1.4))

    def wall_path(self, c):
        """The back wall minus the window (use with the even-odd rule)."""
        S = self.r.surfaces()
        draw.poly(c, S["back"])
        X0, Y0, X1, Y1 = self.apt.WINDOW
        zb = self.r.zb
        draw.poly(c, [self.P(X0, Y0, zb), self.P(X1, Y0, zb), self.P(X1, Y1, zb), self.P(X0, Y1, zb)])

    # ---------------------------------------------------------------- the rig
    def draw_rig(self, L, woman=True):
        """Base block, rods (the woman's clamp empty when woman=False), crank wheel, motor."""
        r = self.r
        P = r.P
        X, Z, w, d, h = self.apt.TABLE
        draw.poly(L, [P(X - 0.30, h, Z - 0.08), P(X + 0.34, h, Z - 0.08), P(X + 0.34, h + 0.07, Z - 0.08),
                      P(X - 0.30, h + 0.07, Z - 0.08)])
        k = r.ppm(Z)
        for who, (rx, ry) in self.apt.RODS.items():
            c = P(X + rx, h + 0.11, Z)
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

    def crank_rim(self):
        return self.apt.crank_point(90.0)

    def draw_rig_dolls(self, L, woman=True, color=None, ink=False):
        """The two paper dolls on their rods (as the camera sees them). ink=True: opaque black
        (for shadow buffers)."""
        X, Z, w, d, h = self.apt.TABLE
        clip_y = self.P(X, h + 0.07, Z)[1]
        if ink:
            L.save()
            L.rectangle(-1e5, -1e5, 2e5, 1e5 + clip_y)
            L.clip()
            doll_casters(L, self.rig_stage("man"), kind="man", mirror=True, crank_world=self.crank_rim())
            if woman:
                doll_casters(L, self.rig_stage("woman"), kind="woman", mirror=True)
            L.restore()
            return
        col = color or sets_mix(INK, PAPER, 0.5)
        doll_object(L, self.rig_stage("man"), col, kind="man", mirror=True, clip_y=clip_y, crank_world=self.crank_rim())
        if woman:
            doll_object(L, self.rig_stage("woman"), col, kind="woman", mirror=True, clip_y=clip_y)

    def table_casters(self, c, woman=True):
        """The table, rig and dolls as opaque ink (shadow buffers)."""
        self.apt.draw_table(c)
        self.draw_rig(c, woman=woman)
        self.draw_rig_dolls(c, woman=woman, ink=True)

    # ---------------------------------------------------------------- the lever handle
    def lever_points(self, open_=0.0, turn=0.0, scale=1.0):
        d = self.door
        ang = math.radians(100 * clamp(open_))
        cu, sn = math.cos(ang), math.sin(ang)
        u0 = d.w - 34.0
        v0 = d.h * 0.46
        th = math.radians(40.0 * clamp(turn))
        Lv = 72.0 * scale

        def Q(u, v, n):
            return d.project(u * cu - n * sn, u * sn + n * cu, v)
        return Q, u0, v0, th, Lv

    def lever(self, c, open_=0.0, turn=0.0, scale=1.0, color=None, rim_col=None, rim_a=0.0):
        """A lever door handle on the room side of the leaf, through the door's projection: it
        dips as it turns (turn 0..1 = 0..40 deg). rim: a thin highlight on its top edge."""
        Q, u0, v0, th, Lv = self.lever_points(open_, turn, scale)
        rose = [Q(u0 - 14, v0 - 14, 2), Q(u0 + 14, v0 - 14, 2), Q(u0 + 14, v0 + 14, 2), Q(u0 - 14, v0 + 14, 2)]
        draw.poly(c, rose)
        n = 24.0
        top = [Q(u0 + 3, v0 + 6, n), Q(u0 - Lv * math.cos(th), v0 + 6 - Lv * math.sin(th), n)]
        bot = [Q(u0 - Lv * math.cos(th) - 2, v0 - 5 - Lv * math.sin(th), n), Q(u0 + 3, v0 - 6, n)]
        draw.poly(c, top + bot)
        draw.poly(c, [Q(u0 - 5, v0 - 6, 2), Q(u0 + 5, v0 - 6, 2), Q(u0 + 5, v0 + 6, n), Q(u0 - 5, v0 + 6, n)])
        draw.fill(c, color or INK)
        if rim_a > 0.01:
            draw.capsule(c, top[0], top[1], 2.4, 1.8)
            draw.fill(c, rim_col or AMBER, clamp(rim_a))
        return top[1]

    def door_leaks(self, f, t, hall=0.0, open_=0.0, lit=0.0, lit_col=None):
        """Hallway light leaking round a closed door (the latch edge, the top, the keyhole) and
        a little room light on its leaf (lit 0..1)."""
        d = self.door
        P = d.project
        if lit > 0.01:
            with f.light(blur=10.0) as A:
                draw.poly(A, d.leaf_quad(open_))
                draw.fill(A, lit_col or AMBER, 0.07 * lit)
        if hall <= 0.01 or open_ > 0.02:
            return
        w, h = d.w, d.h
        with f.light(blur=1.5) as A:
            draw.poly(A, [P(w - 2.5, 0, 6), P(w + 1.5, 0, 6), P(w + 1.5, 0, h), P(w - 2.5, 0, h)])
            draw.poly(A, [P(0, 0, h - 1.5), P(w, 0, h - 1.5), P(w, 0, h + 2.0), P(0, 0, h + 2.0)])
            draw.fill(A, HOT, 0.55 * hall)
            kh = P(w - 34.0, 0, h * 0.40 - 4.0)
            glow(A, kh, 7.0, HOT, 0.8 * hall)
        with f.emit() as G:
            kh = P(w - 34.0, 0, h * 0.40 - 4.0)
            draw.circle(G, kh, 2.0)
            draw.fill(G, HOT, 0.8 * hall)

    def _sheet_emit_shadows(self, f, t, st, sh, lamp, b3, lv, behind):
        """The sheet's bloom (and the hidden bulb's) is added at finish(), over the shadows:
        erase it under them so a shadow stays a shadow."""
        cs = [(z, fn) for (z, fn) in st.get("casters", ()) if SHEET_Z < z < lamp["Z"] - 0.01]
        if not behind or not cs:
            return
        with f.emit() as G:
            G.save()
            sh.path(G, t, hit=st.get("hit"), fall=st.get("fall", 0.0))
            G.clip()
            for (z, fn) in cs:
                center, mag, soft = self.apt.shadow_map(z, b3)
                mag = min(mag, 14.0)
                G.push_group()
                G.translate(center[0], center[1])
                G.scale(mag, mag)
                G.translate(-center[0], -center[1])
                fn(G)
                pat = G.pop_group()
                G.save()
                G.set_operator(cairo.OPERATOR_DEST_OUT)
                G.set_source_rgba(0, 0, 0, 0.92)
                G.mask(pat)
                G.restore()
            G.restore()

    # ---------------------------------------------------------------- drawing
    def draw(self, f, t, st):
        apt, r = self.apt, self.r
        lamp = st.get("lamp") or dict(X=apt.LAMP_FRONT[0], Z=apt.LAMP_FRONT[1], on=0.0)
        stand = lamp.get("stand", True)
        broken = lamp.get("broken", False)
        lv = 0.0 if (broken or not stand) else clamp(lamp.get("on", 0.0), 0.0, 1.3)
        b3 = self.bulb3d(lamp)
        behind = lamp["Z"] > SHEET_Z
        has_sheet = st.get("sheet", True)
        cover = clamp(st.get("cover", 1.0)) if has_sheet else 0.0
        fall = st.get("fall", 0.0)
        hide = self.hidden(lamp, cover, fall, has_sheet)
        door = st.get("door") or {}
        dop = door.get("open", 0.0)
        hall = door.get("hall", 0.0)
        street = st.get("street", 0.30)
        police = st.get("police", 0.0)
        # 1) the box and the window, then light
        with f.layer() as L:
            r.draw_box(L)
            apt.draw_window(f, t, L, street=street, police=police)
        lights = apt.lights(t, lamp=0.0, sheet=has_sheet and cover > 0.6, street=street, police=police,
                            door_open=dop, hall=hall, door_mask=door.get("mask"))
        cov = hide * (cover if has_sheet else 0.0)
        if lv > 0.01:
            lights.append(dict(kind="point", pos=b3, color=sets_mix(AMBER, HOT, 0.5),
                               power=2.2 * lv * (1.0 - 0.72 * cov), r0=0.3))
            if behind and has_sheet and cover > 0.05:
                bx = clamp(b3[0], apt.SHEET[0] + 0.2, self.edge_X(cover) - 0.2)
                lights.append(dict(kind="area", pos=(bx, 1.5, SHEET_Z - 0.05), normal=(0, 0, -1), color=AMBER,
                                   power=1.15 * lv * lerp(0.3, 1.0, cov) * clamp(cover * 1.5), r0=0.6))
        lights += list(st.get("extra_lights", ()))
        z0, z1 = apt.DOOR_Z
        holes = [("back",) + tuple(apt.WINDOW), ("left", z0, 0.0, z1, apt.DOOR_H)]
        r.light_map(f, lights, ambient=0.007, holes=holes, bounce=0.14,
                    albedo=dict(ceiling=0.26, floor=0.26, walls=0.42))
        S = r.surfaces()
        xs = [p[0] for p in S["back"]]
        ys = [p[1] for p in S["back"]]
        wall_bb = (min(xs), min(ys), max(xs), max(ys))

        def wall_region(c):
            self.wall_path(c)
            c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        # the lamp close to the back wall (behind the sheet): a hot pool on the wall
        if lv > 0.01 and lamp["Z"] > r.zb - 0.9:
            dz = max(r.zb - lamp["Z"], 0.08)
            p = self.P(b3[0], b3[1], r.zb)
            with f.light(blur=8.0) as A:
                A.save()
                wall_region(A)
                A.clip()
                glow(A, p, self.ppm(r.zb) * (0.5 + 2.2 * dz), sets_mix(AMBER, HOT, 0.45), 0.55 * lv * (0.9 - dz))
                A.restore()
        # 1b) shadows on the back wall from a lamp in front of the casters
        if lv > 0.02:
            for (z, fn) in st.get("wall_casters", ()):
                gap = z - lamp["Z"]
                if gap < 0.12 or z >= r.zb:
                    continue
                center, mag, soft = apt.shadow_map(z, b3, screen_z=r.zb - 0.01)
                dens = 0.62 * min(1.0, lv) * clamp((gap - 0.12) / 0.35)
                with f.layer() as L:
                    shadow_screen(L, fn, region=wall_region, bbox=wall_bb, soft=max(1.5, soft), density=dens,
                                  mag=mag, center=center)
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
                sock = self.P(r.hw - 0.02, 0.30, lamp["Z"] + 0.3)
                vis = 1.0 - hide
                with f_.layer() as L:
                    lo.draw(f_, t_, L, on=lv * vis if vis > 0.5 else 0.0, tilt=lamp.get("tilt", 0.0),
                            broken=broken, cord_to=(sock[0], self.P(lamp["X"], 0, lamp["Z"])[1]))
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
            hot = self.P(*b3) if behind else self.P(b3[0], b3[1], SHEET_Z)
            with f.layer() as L:
                sh.draw(f, t, L, light=hot, level=lv * (1.0 if behind else 0.55), back=behind,
                        base=sets_mix(INK, PAL.fog_at(1.0), 0.42), hit=st.get("hit"), fall=fall,
                        folds=lerp(2.4, 1.0, cover), tears=st.get("tears", ()))
                if lv > 0.02 and behind:
                    for (z, fn) in st.get("casters", ()):
                        if SHEET_Z < z < lamp["Z"] - 0.01:
                            center, mag, soft = apt.shadow_map(z, b3)
                            mag = min(mag, 14.0)
                            sh.shadow(L, t, fn, lamp=center, mag=mag, soft=max(1.0, soft),
                                      density=0.94 * min(1.0, lv), hit=st.get("hit"), fall=fall)
                slashes = st.get("slashes")
                if slashes:
                    slashes(f, t, L, sh)
            if lv > 0.01:
                if behind:
                    slev = 0.7 * lv * lerp(0.3, 1.0, cover) * lerp(0.5, 1.0, hide)
                else:
                    slev = lv * 0.4 * lerp(0.4, 1.0, cover)
                sh.light(f, t, hot, level=slev, back=behind)
                self._sheet_emit_shadows(f, t, st, sh, lamp, b3, lv, behind)
        for z, fn in near:
            fn(f, t)
        # the door and its handle
        with f.layer() as L:
            self.door.draw(f, t, L, open=dop, hall=hall, locked=door.get("locked", 0.0), key=False,
                           feet=door.get("feet", ()), hall_fn=door.get("hall_fn"))
            tip = self.lever(L, dop, door.get("lever", 0.0), rim_col=door.get("lever_rim_col"),
                             rim_a=door.get("lever_rim", 0.0))
        if door.get("lever_rim", 0.0) > 0.01:
            with f.light(blur=2.0) as A:
                glow(A, tip, 9.0, HOT, 0.55 * door.get("lever_rim", 0.0))
        self.door.light(f, t, open=dop, hall=hall, spill=door.get("spill", 0.0), feet=door.get("feet", ()))
        self.door_leaks(f, t, hall=hall, open_=dop, lit=door.get("lit", 0.0))
        after = st.get("after")
        if after is not None:
            after(f, t)
        return dict(hide=hide, bulb=self.P(*b3), b3=b3, lv=lv)
