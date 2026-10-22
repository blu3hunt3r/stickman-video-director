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
