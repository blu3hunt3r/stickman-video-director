"""Frame: the drawing surface for one rendered frame, plus camera and compositing.

A Frame owns three cairo surfaces:
  * main  (full res)    - all sharp line art and props, black background
  * glow  (1/4 res)     - emissive light (flames, bulbs, windows, sirens); blurred and
                          added on top at finish()
  * groups              - temporary offscreen groups for light-reveal masks and blur

Coordinates: world units are 1080x1920 "frame pixels" at zoom 1. A Camera maps world to
screen. Line widths given to drawing helpers are screen pixels at zoom 1; f.lw() keeps
them close to constant on screen when the camera zooms (mild zoom**0.35 growth).
"""
import math
from contextlib import contextmanager

import cairo
import numpy as np
from scipy.ndimage import gaussian_filter

from .core import W, H, BLACK, clamp

GLOW_DS = 4          # glow / light-mask resolution divisor
LW_EXP = 0.35        # on-screen line width grows as zoom**LW_EXP


class Camera:
    """2D camera: center (x, y) in world units, zoom, roll in degrees."""

    def __init__(self, x=W / 2, y=H / 2, zoom=1.0, rot=0.0):
        self.x, self.y, self.zoom, self.rot = float(x), float(y), float(zoom), float(rot)

    def copy(self, **kw):
        c = Camera(self.x, self.y, self.zoom, self.rot)
        for k, v in kw.items():
            setattr(c, k, float(v))
        return c

    def moved(self, dx=0.0, dy=0.0, dzoom=1.0, drot=0.0):
        return Camera(self.x + dx, self.y + dy, self.zoom * dzoom, self.rot + drot)

    def shaken(self, t, amp=6.0, rot_amp=0.3, freq=1.3, seed=0):
        """Handheld-style smooth shake (amp in screen px)."""
        from .core import fbm1
        k = amp / max(self.zoom, 1e-6)
        return Camera(self.x + k * fbm1(t * freq, seed), self.y + k * fbm1(t * freq, seed + 17),
                      self.zoom, self.rot + rot_amp * fbm1(t * freq * 0.8, seed + 31))

    def parallax(self, depth, origin=(W / 2, H / 2)):
        """Camera for a layer at `depth` (1 = main plane, <1 farther, >1 nearer)."""
        ox, oy = origin
        return Camera(ox + (self.x - ox) * depth, oy + (self.y - oy) * depth,
                      max(1e-3, 1.0 + (self.zoom - 1.0) * depth), self.rot)

    def matrix(self, scale=1.0):
        m = cairo.Matrix()
        m.scale(scale, scale)
        m.translate(W / 2, H / 2)
        m.rotate(math.radians(self.rot))
        m.scale(self.zoom, self.zoom)
        m.translate(-self.x, -self.y)
        return m

    def to_screen(self, p):
        return self.matrix().transform_point(p[0], p[1])

    def to_world(self, p):
        m = self.matrix()
        m.invert()
        return m.transform_point(p[0], p[1])


# ----------------------------------------------------------------------------- lights
class Light:
    """Light shapes for Frame.lit() reveal masks (world coordinates)."""

    def __init__(self, kind, **kw):
        self.kind, self.kw = kind, kw

    @staticmethod
    def cone(apex, angle, spread, length, intensity=1.0, falloff=0.85):
        """angle: direction in degrees (0 = right, 90 = down). spread: full cone width in degrees."""
        return Light("cone", apex=apex, angle=angle, spread=spread, length=length,
                     intensity=intensity, falloff=falloff)

    @staticmethod
    def radial(center, radius, intensity=1.0, hard=0.0):
        return Light("radial", center=center, radius=radius, intensity=intensity, hard=hard)

    @staticmethod
    def rect(x0, y0, x1, y1, intensity=1.0):
        return Light("rect", box=(x0, y0, x1, y1), intensity=intensity)

    @staticmethod
    def poly(points, intensity=1.0):
        return Light("poly", points=points, intensity=intensity)

    @staticmethod
    def full(intensity=1.0):
        return Light("full", intensity=intensity)

    def draw(self, ctx):
        k, a = self.kind, self.kw
        if k == "full":
            ctx.set_source_rgba(1, 1, 1, a["intensity"])
            ctx.paint()
        elif k == "radial":
            cx, cy = a["center"]
            r = a["radius"]
            g = cairo.RadialGradient(cx, cy, r * a["hard"], cx, cy, r)
            g.add_color_stop_rgba(0, 1, 1, 1, a["intensity"])
            g.add_color_stop_rgba(1, 1, 1, 1, 0)
            ctx.set_source(g)
            ctx.arc(cx, cy, r, 0, 2 * math.pi)
            ctx.fill()
        elif k == "cone":
            ax, ay = a["apex"]
            ang, sp, L = math.radians(a["angle"]), math.radians(a["spread"]) / 2, a["length"]
            g = cairo.RadialGradient(ax, ay, 0, ax, ay, L)
            g.add_color_stop_rgba(0, 1, 1, 1, a["intensity"])
            g.add_color_stop_rgba(a["falloff"], 1, 1, 1, a["intensity"] * 0.55)
            g.add_color_stop_rgba(1, 1, 1, 1, 0)
            ctx.set_source(g)
            ctx.move_to(ax, ay)
            n = 16
            for i in range(n + 1):
                th = ang - sp + 2 * sp * i / n
                ctx.line_to(ax + L * math.cos(th), ay + L * math.sin(th))
            ctx.close_path()
            ctx.fill()
        elif k == "rect":
            x0, y0, x1, y1 = a["box"]
            ctx.set_source_rgba(1, 1, 1, a["intensity"])
            ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
            ctx.fill()
        elif k == "poly":
            pts = a["points"]
            ctx.set_source_rgba(1, 1, 1, a["intensity"])
            ctx.move_to(*pts[0])
            for p in pts[1:]:
                ctx.line_to(*p)
            ctx.close_path()
            ctx.fill()


# ----------------------------------------------------------------------------- helpers
def _surface_to_array(surf):
    surf.flush()
    w, h, stride = surf.get_width(), surf.get_height(), surf.get_stride()
    buf = np.ndarray(shape=(h, stride // 4, 4), dtype=np.uint8, buffer=surf.get_data())
    return buf[:, :w, :]


def _array_to_surface(arr):
    """arr: float or uint8 HxWx4 premultiplied BGRA -> new ImageSurface (copy)."""
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    h, w = arr.shape[:2]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    dst = _surface_to_array(surf)
    dst[...] = arr
    surf.mark_dirty()
    return surf


class Frame:
    def __init__(self, t=0.0, scale=1.0, bloom=0.16, glow_strength=1.0):
        self.t = t
        self.scale = scale
        self.pw, self.ph = int(round(W * scale)), int(round(H * scale))
        self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.pw, self.ph)
        self.ctx = cairo.Context(self.surf)
        self.ctx.set_source_rgb(*BLACK)
        self.ctx.paint()
        self.gw, self.gh = max(1, self.pw // GLOW_DS), max(1, self.ph // GLOW_DS)
        self.gsurf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.gw, self.gh)
        self.g = cairo.Context(self.gsurf)
        self.bloom = bloom
        self.glow_strength = glow_strength
        self.glow_sigma = (1.6, 6.0)      # glow blur sigmas in glow-res pixels (tight, wide)
        self.fade = 0.0                   # black overlay 0..1 applied at finish
        self.whip = None                  # (dx, dy) screen-px motion streak at finish
        self.cam = Camera()
        self._lwk = 1.0
        for c in (self.ctx, self.g):
            c.set_line_cap(cairo.LINE_CAP_ROUND)
            c.set_line_join(cairo.LINE_JOIN_ROUND)
        self.set_camera(self.cam)

    # ---------------------------------------------------------------- camera
    def set_camera(self, cam):
        self.cam = cam
        self.ctx.set_matrix(cam.matrix(self.scale))
        self.g.set_matrix(cam.matrix(self.scale * self.gw / self.pw))
        self._lwk = cam.zoom ** (LW_EXP - 1.0)
        return cam

    @contextmanager
    def camera(self, cam):
        """Temporarily draw with another camera (e.g. a parallax layer)."""
        prev = self.cam
        self.set_camera(cam)
        try:
            yield cam
        finally:
            self.set_camera(prev)

    @contextmanager
    def screen(self):
        """Draw in screen space (1080x1920 frame pixels), ignoring the camera."""
        with self.camera(Camera()):
            yield

    def lw(self, w):
        """User-space line width for a desired on-screen width w (at zoom 1)."""
        return w * self._lwk

    # ---------------------------------------------------------------- groups
    @contextmanager
    def lit(self, lights, ambient=0.22, soften=3.0):
        """Everything drawn inside is visible at `ambient` brightness, and fully
        bright where the given Light shapes fall (soft-edged). Classic noir reveal."""
        self.ctx.push_group()
        try:
            yield
        finally:
            pat = self.ctx.pop_group()          # pattern matrix == current CTM
            mask = self._light_mask(lights, ambient, soften)
            mpat = cairo.SurfacePattern(mask)
            mm = cairo.Matrix(*self.ctx.get_matrix())
            mpat.set_matrix(mm.multiply(cairo.Matrix(xx=self.gw / self.pw, yy=self.gh / self.ph)))
            mpat.set_filter(cairo.FILTER_BILINEAR)
            self.ctx.set_source(pat)
            self.ctx.mask(mpat)

    def _light_mask(self, lights, ambient, soften):
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.gw, self.gh)
        c = cairo.Context(surf)
        c.set_matrix(self.cam.matrix(self.scale * self.gw / self.pw))
        c.set_operator(cairo.OPERATOR_ADD)
        for L in lights:
            L.draw(c)
        arr = _surface_to_array(surf).astype(np.float32)[..., 3] / 255.0
        if soften > 0:
            arr = gaussian_filter(arr, soften)
        a = np.clip(ambient + (1.0 - ambient) * np.clip(arr, 0, 1), 0, 1) * 255.0
        out = np.empty((self.gh, self.gw, 4), np.float32)
        out[..., 0] = out[..., 1] = out[..., 2] = out[..., 3] = a
        return _array_to_surface(out)

    @contextmanager
    def blurred(self, radius, alpha=1.0):
        """Draw content blurred by `radius` screen px (depth of field / soft focus)."""
        self.ctx.push_group()
        try:
            yield
        finally:
            pat = self.ctx.pop_group()          # pattern matrix == current CTM
            ctm = cairo.Matrix(*self.ctx.get_matrix())
            r = radius * self.scale
            k = max(1, int(r / 3))
            sw, sh = max(1, self.pw // k), max(1, self.ph // k)
            down = cairo.Matrix(xx=sw / self.pw, yy=sh / self.ph)
            small = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw, sh)
            sc = cairo.Context(small)
            sc.set_matrix(ctm.multiply(down))
            sc.set_source(pat)
            sc.paint()
            arr = _surface_to_array(small).astype(np.float32)
            sig = max(0.5, r / k)
            arr = gaussian_filter(arr, (sig, sig, 0))
            bp = cairo.SurfacePattern(_array_to_surface(arr))
            bp.set_matrix(cairo.Matrix(*self.ctx.get_matrix()).multiply(down))
            bp.set_filter(cairo.FILTER_BILINEAR)
            self.ctx.set_source(bp)
            self.ctx.paint_with_alpha(alpha)

    @contextmanager
    def clipped(self, path_fn):
        """Clip drawing to a path built by path_fn(ctx) in current world coords."""
        self.ctx.save()
        self.g.save()
        path_fn(self.ctx)
        self.ctx.clip()
        path_fn(self.g)
        self.g.clip()
        try:
            yield
        finally:
            self.ctx.restore()
            self.g.restore()

    @contextmanager
    def alpha(self, a):
        """Draw a group at reduced opacity (main and glow)."""
        self.ctx.push_group()
        self.g.push_group()
        try:
            yield
        finally:
            self.g.pop_group_to_source()
            self.g.paint_with_alpha(clamp(a))
            self.ctx.pop_group_to_source()
            self.ctx.paint_with_alpha(clamp(a))

    # ---------------------------------------------------------------- finish
    def finish(self):
        """Composite glow, bloom, whip and fade. Returns HxWx4 uint8 BGRA array (a copy)."""
        ctx = self.ctx
        ctx.save()
        ctx.identity_matrix()
        # glow layer
        garr = _surface_to_array(self.gsurf).astype(np.float32)
        if garr.any():
            s1, s2 = self.glow_sigma
            g = gaussian_filter(garr, (s1, s1, 0)) * 0.9 + gaussian_filter(garr, (s2, s2, 0)) * 1.4
            gs = _array_to_surface(g)
            gp = cairo.SurfacePattern(gs)
            m = cairo.Matrix()
            m.scale(self.gw / self.pw, self.gh / self.ph)
            gp.set_matrix(m)
            gp.set_filter(cairo.FILTER_BILINEAR)
            ctx.set_operator(cairo.OPERATOR_ADD)
            ctx.set_source(gp)
            ctx.paint_with_alpha(clamp(self.glow_strength, 0, 4) / 2.0)
            ctx.paint_with_alpha(clamp(self.glow_strength, 0, 4) / 2.0)
        # global bloom (soft halo on all light lines)
        if self.bloom > 0:
            k = 8
            sw, sh = max(1, self.pw // k), max(1, self.ph // k)
            small = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw, sh)
            sc = cairo.Context(small)
            sc.scale(sw / self.pw, sh / self.ph)
            sc.set_source_surface(self.surf)
            sc.paint()
            arr = gaussian_filter(_surface_to_array(small).astype(np.float32), (2.2, 2.2, 0))
            bp = cairo.SurfacePattern(_array_to_surface(arr * 1.6))
            m = cairo.Matrix()
            m.scale(sw / self.pw, sh / self.ph)
            bp.set_matrix(m)
            bp.set_filter(cairo.FILTER_BILINEAR)
            ctx.set_operator(cairo.OPERATOR_ADD)
            ctx.set_source(bp)
            ctx.paint_with_alpha(clamp(self.bloom))
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.restore()
        arr = _surface_to_array(self.surf)
        if self.whip:
            dx, dy = self.whip
            n = int(min(24, max(4, math.hypot(dx, dy) / 6)))
            acc = np.zeros(arr.shape, np.float32)
            for i in range(n):
                f = (i / (n - 1) - 0.5)
                acc += np.roll(arr, (int(round(dy * f * self.scale)), int(round(dx * f * self.scale))), axis=(0, 1))
            arr = (acc / n)
        out = np.array(arr, dtype=np.float32 if self.fade > 0 else arr.dtype, copy=True)
        if self.fade > 0:
            out *= (1.0 - clamp(self.fade))
        out = np.clip(out, 0, 255).astype(np.uint8)
        out[..., 3] = 255
        return out
