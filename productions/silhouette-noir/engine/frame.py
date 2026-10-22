"""Frame: one rendered frame - camera, depth layers with atmospheric fog and depth of field,
emissive glow, additive light, haze, and the film look (grade, bloom, vignette, grain).

Coordinates: world units = 1080x1920 frame pixels at zoom 1 (y down). A Camera maps world to
screen. Layers take a parallax factor `par`: 1 = the action plane, < 1 farther (moves less),
> 1 nearer (foreground occluders, moves more). Draw back to front.

    f.sky(top, bottom)                         # background gradient (screen space)
    with f.layer(par=0.3, blur=6, fog=0.7) as L:   # far trees: drawn in ink, fogged + soft
        ...cairo drawing on L in world coords...
    f.haze(color, 0.5, y0=900, y1=1500, tex=0.6)   # drifting mist band between layers
    with f.light(blur=10) as A: ...            # additive light (god rays, lamp beams)
    with f.layer() as L: ...                   # action plane (sharp)
    with f.emit() as G: ...                    # emissive: eyes, flames, windows -> bloom
    with f.layer(par=1.6, blur=18) as L: ...   # out-of-focus foreground
    return  (renderer calls f.finish())
"""
import math
from contextlib import contextmanager

import cairo
import cv2
import numpy as np

from .core import W, H, clamp, fbm1, hash01, noise_grid
from .palette import Palette, SALVAGE

GLOW_DS = 4


# ----------------------------------------------------------------------------- camera
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
        """Handheld drift (amp in screen px)."""
        k = amp / max(self.zoom, 1e-6)
        return Camera(self.x + k * fbm1(t * freq, seed), self.y + k * fbm1(t * freq, seed + 17),
                      self.zoom, self.rot + rot_amp * fbm1(t * freq * 0.8, seed + 31))

    def parallax(self, par, origin=(W / 2, H / 2)):
        """Camera for a layer with parallax factor `par` (1 = action plane)."""
        ox, oy = origin
        # zoom ** par matches 1 + (zoom - 1) * par to first order near zoom 1, but
        # never flattens, reverses or collapses on deep zoom-outs (zoom < ~0.4)
        return Camera(ox + (self.x - ox) * par, oy + (self.y - oy) * par,
                      max(1e-3, self.zoom) ** par, self.rot)

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

    def view_rect(self, margin=0.0):
        """World-space bounding box (x0, y0, x1, y1) of what this camera sees."""
        pts = [self.to_world(p) for p in ((0, 0), (W, 0), (0, H), (W, H))]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin


# ----------------------------------------------------------------------------- array helpers
def surf_array(surf):
    """Writable numpy view (h, w, 4) uint8 BGRA (premultiplied) of an ARGB32 surface."""
    surf.flush()
    w, h, stride = surf.get_width(), surf.get_height(), surf.get_stride()
    buf = np.ndarray(shape=(h, stride // 4, 4), dtype=np.uint8, buffer=surf.get_data())
    return buf[:, :w, :]


def array_surface(arr):
    """uint8 (or float 0..255) HxWx4 premultiplied BGRA -> new ImageSurface (copy)."""
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    h, w = arr.shape[:2]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    surf_array(surf)[...] = arr
    surf.mark_dirty()
    return surf


def _blur(arr, sigma):
    if sigma <= 0.2:
        return arr
    return cv2.GaussianBlur(arr, (0, 0), sigmaX=float(sigma), sigmaY=float(sigma),
                            borderType=cv2.BORDER_REPLICATE)


_CACHE = {}


def cached(key, fn):
    """Per-process cache for expensive static textures."""
    if key not in _CACHE:
        _CACHE[key] = fn()
    return _CACHE[key]


def fog_texture(seed=0, w=512, h=512, feature=110.0):
    """Tileable soft noise (float32 0..1) for mist, water and smoke."""
    return cached(("fogtex", seed, w, h, feature), lambda: noise_grid(w, h, feature=feature, seed=seed))


# ----------------------------------------------------------------------------- frame
class Frame:
    def __init__(self, t=0.0, scale=1.0, pal=None, seed=0):
        self.t = float(t)
        self.scale = float(scale)
        self.pal = pal if isinstance(pal, Palette) else SALVAGE
        self.seed = seed
        self.pw, self.ph = int(round(W * scale)), int(round(H * scale))
        self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.pw, self.ph)
        self.ctx = cairo.Context(self.surf)
        self.ctx.set_source_rgb(0, 0, 0)
        self.ctx.paint()
        # ceil-sized so an exact 1/GLOW_DS scale covers the frame on both axes
        self.gw, self.gh = -(-self.pw // GLOW_DS), -(-self.ph // GLOW_DS)
        self.gsurf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.gw, self.gh)
        self.g = cairo.Context(self.gsurf)
        self.cam = Camera()
        self.post = dict(
            grain=self.pal.grain,          # film grain amplitude (0..~0.1)
            vignette=self.pal.vignette,    # 0..1
            bloom=0.22,                    # halo from bright areas
            bloom_threshold=0.55,
            glow=1.0,                      # strength of the emissive layer
            glow_sigma=(1.4, 5.5),         # in glow-res px (tight, wide)
            grade=self.pal.grade,
            fade=0.0, fade_color=(0, 0, 0),
            flash=0.0, flash_color=(1, 1, 1),
            flicker=0.012,                 # exposure flicker (old film)
            poster=None,                   # Saul Bass flatten: dict(amount, levels=[(lum, rgb), ...])
            paper=0.0,                     # paper-fibre texture amount (graphic scenes)
            exposure=1.0,
        )
        for c in (self.ctx, self.g):
            c.set_line_cap(cairo.LINE_CAP_ROUND)
            c.set_line_join(cairo.LINE_JOIN_ROUND)
        self.set_camera(self.cam)

    # ---------------------------------------------------------------- camera
    def set_camera(self, cam):
        self.cam = cam
        self.ctx.set_matrix(cam.matrix(self.scale))
        self.g.set_matrix(cam.matrix(self.scale / GLOW_DS))
        return cam

    def lcam(self, par=1.0):
        return self.cam if par == 1.0 else self.cam.parallax(par)

    @contextmanager
    def screen(self):
        """Draw directly on the main canvas in screen space (1080x1920 frame px)."""
        self.ctx.save()
        self.ctx.set_matrix(cairo.Matrix(xx=self.scale, yy=self.scale))
        try:
            yield self.ctx
        finally:
            self.ctx.restore()

    # ---------------------------------------------------------------- backgrounds
    def fill(self, rgb):
        self.ctx.save()
        self.ctx.identity_matrix()
        self.ctx.set_source_rgb(*rgb[:3])
        self.ctx.paint()
        self.ctx.restore()

    def sky(self, top, bottom, mid=None, mid_at=0.5, y0=0.0, y1=float(H)):
        """Vertical screen-space gradient over the whole frame."""
        c = self.ctx
        c.save()
        c.identity_matrix()
        g = cairo.LinearGradient(0, y0 * self.scale, 0, y1 * self.scale)
        g.add_color_stop_rgb(0, *top[:3])
        if mid is not None:
            g.add_color_stop_rgb(mid_at, *mid[:3])
        g.add_color_stop_rgb(1, *bottom[:3])
        c.set_source(g)
        c.paint()
        c.restore()

    def sky_world(self, stops, par=0.0):
        """Vertical gradient anchored in WORLD y (so it scrolls with a vertical camera move,
        e.g. sea depth zones). stops: [(world_y, rgb), ...]. par: how much it scrolls."""
        cam = self.lcam(par)
        m = cam.matrix(self.scale)
        c = self.ctx
        c.save()
        c.set_matrix(m)
        x0, y0, x1, y1 = cam.view_rect(50)
        g = cairo.LinearGradient(0, stops[0][0], 0, stops[-1][0])
        span = stops[-1][0] - stops[0][0] or 1.0
        for y, rgb in stops:
            g.add_color_stop_rgb((y - stops[0][0]) / span, *rgb[:3])
        c.set_source(g)
        c.rectangle(x0, y0, x1 - x0, y1 - y0)
        c.fill()
        c.restore()

    # ---------------------------------------------------------------- layers
    @contextmanager
    def layer(self, par=1.0, blur=0.0, fog=0.0, fog_color=None, alpha=1.0, op=None):
        """Draw a depth layer. Content is drawn in world coords through the parallax camera.
        fog: 0..1 tint of everything drawn toward fog_color (default: palette fog for that
        amount). blur: depth-of-field radius in screen px. alpha: layer opacity."""
        cam = self.lcam(par)
        blur_px = blur * self.scale
        fast = blur_px < 0.6 and fog <= 0.0 and alpha >= 1.0 and op is None
        if fast:
            c = self.ctx
            c.save()
            c.set_matrix(cam.matrix(self.scale))
            try:
                yield c
            finally:
                c.restore()
            return
        k = int(clamp(round(blur_px / 3.0), 1, 8)) if blur_px >= 0.6 else 1
        lw, lh = -(-self.pw // k), -(-self.ph // k)        # ceil: exact 1/k scale on both axes
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, lw, lh)
        c = cairo.Context(surf)
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.set_matrix(cam.matrix(self.scale / k))
        try:
            yield c
        finally:
            if fog > 0:
                col = fog_color or self.pal.fog_at(fog)
                c.identity_matrix()
                c.set_operator(cairo.OPERATOR_ATOP)
                c.set_source_rgba(col[0], col[1], col[2], clamp(fog))
                c.paint()
            if blur_px >= 0.6:
                arr = surf_array(surf)
                arr[...] = _blur(arr, blur_px / k)
                surf.mark_dirty()
            self._composite(surf, k, alpha, op)

    def _composite(self, surf, k, alpha=1.0, op=None):
        c = self.ctx
        c.save()
        c.identity_matrix()
        pat = cairo.SurfacePattern(surf)
        pat.set_filter(cairo.FILTER_BILINEAR if k > 1 else cairo.FILTER_FAST)
        pat.set_matrix(cairo.Matrix(xx=1.0 / k, yy=1.0 / k))
        if op is not None:
            c.set_operator(op)
        c.set_source(pat)
        c.paint_with_alpha(clamp(alpha))
        c.restore()

    @contextmanager
    def light(self, par=1.0, blur=6.0, alpha=1.0):
        """Additive light layer (god rays, beams, fog glow): drawn soft, then ADDed."""
        cam = self.lcam(par)
        blur_px = max(0.0, blur * self.scale)
        k = int(clamp(round(blur_px / 2.5), 1, 8)) if blur_px >= 1 else 1
        lw, lh = -(-self.pw // k), -(-self.ph // k)
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, lw, lh)
        c = cairo.Context(surf)
        c.set_operator(cairo.OPERATOR_ADD)
        c.set_matrix(cam.matrix(self.scale / k))
        try:
            yield c
        finally:
            if blur_px >= 1:
                arr = surf_array(surf)
                arr[...] = _blur(arr, blur_px / k)
                surf.mark_dirty()
            if not self._add_array(surf, k, alpha):
                self._composite(surf, k, alpha, cairo.OPERATOR_ADD)

    def _add_array(self, surf, k, alpha=1.0):
        """Fast path for an additive composite: cv2 upscale + saturating add straight into the
        canvas pixels (~3 ms instead of ~14 ms for cairo's bilinear ADD paint). Only when the
        main context draws to the canvas itself (no push_group) through no clip; returns False
        so the caller falls back to cairo otherwise."""
        c = self.ctx
        if c.get_group_target() != self.surf:
            return False
        c.save()
        c.identity_matrix()
        try:
            rects = c.copy_clip_rectangle_list()
        except cairo.Error:
            rects = None
        finally:
            c.restore()
        if not rects or len(rects) != 1:
            return False
        x, y, w, h = rects[0]
        if x > 0 or y > 0 or x + w < self.pw or y + h < self.ph:
            return False
        surf.flush()
        src = surf_array(surf)
        if k > 1:
            lh, lw = src.shape[:2]
            src = cv2.resize(src, (lw * k, lh * k), interpolation=cv2.INTER_LINEAR)
        src = src[:self.ph, :self.pw]
        self.surf.flush()
        dst = surf_array(self.surf)
        a = clamp(alpha)
        if a >= 1.0:
            cv2.add(dst, src, dst=dst)
        elif a > 0.0:
            cv2.addWeighted(dst, 1.0, src, a, 0.0, dst=dst)
        self.surf.mark_dirty()
        return True

    @contextmanager
    def emit(self, par=1.0):
        """Emissive layer (1/4 res): anything drawn here glows (blurred + added at finish).
        Draw the hot core on the main layer too if it must stay crisp."""
        cam = self.lcam(par)
        self.g.save()
        self.g.set_matrix(cam.matrix(self.scale / GLOW_DS))
        try:
            yield self.g
        finally:
            self.g.restore()

    @contextmanager
    def group(self, alpha=1.0, op=None, par=1.0):
        """Full-res offscreen group composited with alpha / operator (e.g. a fading prop)."""
        with self.layer(par=par, alpha=alpha, op=op, fog=0.0, blur=0.0) as c:
            yield c

    # ---------------------------------------------------------------- atmosphere
    def haze(self, color, alpha, y0=None, y1=None, feather=300.0, tex=0.0, tex_scale=1.0,
             scroll=(0.0, 0.0), seed=0, par=1.0, screen=False, x0=None, x1=None):
        """Mist: paint `color` over everything drawn so far, with opacity `alpha` inside a
        band y0..y1 (world y through layer `par`, or screen y if screen=True) and soft
        `feather` edges. tex (0..1) breaks it into drifting fog; scroll = (px/s, px/s)."""
        if alpha <= 0.002:
            return
        ds = 4
        w, h = -(-self.pw // ds), -(-self.ph // ds)
        ys = np.arange(h, dtype=np.float32) * ds / self.scale + ds / (2 * self.scale)   # screen y (frame px)
        xs = np.arange(w, dtype=np.float32) * ds / self.scale + ds / (2 * self.scale)
        if screen:
            wy = ys
            wx = xs
            zoom = 1.0
        else:
            cam = self.lcam(par)
            zoom = cam.zoom
            # screen -> world (ignoring roll for the band test)
            wy = (ys - H / 2) / cam.zoom + cam.y
            wx = (xs - W / 2) / cam.zoom + cam.x
        m = np.ones(h, np.float32)
        if y0 is not None:
            m *= np.clip((wy - (y0 - feather / 2)) / max(feather, 1e-3), 0, 1)
        if y1 is not None:
            m *= np.clip(((y1 + feather / 2) - wy) / max(feather, 1e-3), 0, 1)
        a = np.repeat(m[:, None], w, axis=1) * alpha
        if x0 is not None or x1 is not None:
            mx = np.ones(w, np.float32)
            if x0 is not None:
                mx *= np.clip((wx - (x0 - feather / 2)) / max(feather, 1e-3), 0, 1)
            if x1 is not None:
                mx *= np.clip(((x1 + feather / 2) - wx) / max(feather, 1e-3), 0, 1)
            a *= mx[None, :]
        if tex > 0:
            T = fog_texture(seed)
            th, tw = T.shape
            sx = (wx * tex_scale * 0.5 + scroll[0] * self.t) % tw
            sy = (wy * tex_scale * 0.5 + scroll[1] * self.t) % th
            ix = sx.astype(np.int32) % tw
            iy = sy.astype(np.int32) % th
            n = T[iy[:, None], ix[None, :]]
            a *= (1.0 - tex) + tex * (0.25 + 1.5 * n * n)
        a = np.clip(a, 0, 1)
        arr = np.empty((h, w, 4), np.float32)
        arr[..., 0] = color[2] * a * 255
        arr[..., 1] = color[1] * a * 255
        arr[..., 2] = color[0] * a * 255
        arr[..., 3] = a * 255
        surf = array_surface(arr)
        self._composite(surf, ds)

    def darken(self, alpha, y0=None, y1=None, feather=300.0, **kw):
        self.haze((0, 0, 0), alpha, y0, y1, feather, **kw)

    # ---------------------------------------------------------------- finish
    def finish(self):
        """Composite glow, bloom, grade, poster, vignette, grain, fades.
        Returns HxWx4 uint8 BGRA array (alpha 255)."""
        P = self.post
        out = surf_array(self.surf)[..., :3].astype(np.float32)
        # emissive glow
        g = surf_array(self.gsurf)[..., :3]
        if g.any() and P["glow"] > 0:
            gf = g.astype(np.float32)
            s1, s2 = P["glow_sigma"]
            # sigmas are full-resolution glow-buffer px: scale them so previews match
            gb = _blur(gf, s1 * self.scale) * 0.85 + _blur(gf, s2 * self.scale) * 1.25
            gb = cv2.resize(gb, (self.gw * GLOW_DS, self.gh * GLOW_DS),
                            interpolation=cv2.INTER_LINEAR)[:self.ph, :self.pw]
            out += gb * P["glow"]
        # bloom from bright areas
        if P["bloom"] > 0:
            k = 8
            small = cv2.resize(out, (max(1, self.pw // k), max(1, self.ph // k)), interpolation=cv2.INTER_AREA)
            thr = P["bloom_threshold"] * 255
            br = np.clip(small - thr, 0, None) * (255.0 / max(255 - thr, 1))
            br = _blur(br, 3.0 * self.scale) * 0.7 + _blur(br, 9.0 * self.scale) * 0.6
            out += cv2.resize(br, (self.pw, self.ph), interpolation=cv2.INTER_LINEAR) * P["bloom"]
        if P["exposure"] != 1.0:
            out *= P["exposure"]
        if P["flicker"] > 0:
            out *= 1.0 + P["flicker"] * fbm1(self.t * 7.0, 913)
        # Saul Bass flatten (posterize to flat paper colors)
        poster = P["poster"]
        if poster and poster.get("amount", 0) > 0:
            lum = np.clip((out[..., 2] * 0.2126 + out[..., 1] * 0.7152 + out[..., 0] * 0.0722) / 255.0, 0.0, 1.0)
            levels = poster["levels"]
            flat = np.zeros_like(out)
            prev = -1.0
            for k, (thr, rgb) in enumerate(levels):
                last = k == len(levels) - 1              # the brightest level is open-ended
                msk = (lum > prev) if last else ((lum > prev) & (lum <= thr))
                flat[msk] = (rgb[2] * 255, rgb[1] * 255, rgb[0] * 255)
                prev = thr
            if poster.get("keep_red", True):
                # saturated reds survive the flatten (the accent is sacred)
                r, gg, b = out[..., 2], out[..., 1], out[..., 0]
                red = (r > 90) & (r > gg * 2.2) & (r > b * 2.2)
                flat[red] = out[red]
            a = clamp(poster["amount"])
            out = out * (1 - a) + flat * a
        # paper fibre texture
        if P["paper"] > 0:
            T = cached(("paper", self.pw, self.ph), lambda: _paper_texture(self.pw, self.ph))
            out *= 1.0 - P["paper"] * T[..., None]
        # grade (per-channel lift / gamma / gain)
        gr = P["grade"]
        if gr:
            out = np.clip(out, 0, 255)
            lut = cached(("grade", tuple(map(tuple, (gr["lift"], gr["gamma"], gr["gain"])))), lambda: _grade_lut(gr))
            o8 = out.astype(np.uint8)
            out = cv2.LUT(o8, lut).astype(np.float32)
        # vignette
        if P["vignette"] > 0:
            V = cached(("vig", self.pw, self.ph, round(P["vignette"], 3)), lambda: _vignette(self.pw, self.ph, P["vignette"]))
            out *= V[..., None]
        # grain (luminance-weighted, soft 2px clumps)
        if P["grain"] > 0:
            idx = int(self.t * 24 + 0.5) % 12
            G = cached(("grain", self.pw, self.ph, idx), lambda: _grain(self.pw, self.ph, idx))
            lum = out[..., 1] * (1.0 / 255.0)
            wgt = 0.35 + 2.4 * lum * (1.0 - lum)
            out += (G * (P["grain"] * 255.0) * wgt)[..., None]
        if P["flash"] > 0:
            fc = P["flash_color"]
            a = clamp(P["flash"])
            out = out * (1 - a) + np.array([fc[2], fc[1], fc[0]], np.float32) * 255 * a
        if P["fade"] > 0:
            fc = P["fade_color"]
            a = clamp(P["fade"])
            out = out * (1 - a) + np.array([fc[2], fc[1], fc[0]], np.float32) * 255 * a
        res = np.empty((self.ph, self.pw, 4), np.uint8)
        res[..., :3] = np.clip(out, 0, 255)
        res[..., 3] = 255
        return res


# ----------------------------------------------------------------------------- post helpers
def _grade_lut(gr):
    x = np.arange(256, dtype=np.float32) / 255.0
    chans = []
    for i in (2, 1, 0):          # LUT order follows BGR channels
        lift, gamma, gain = gr["lift"][i], gr["gamma"][i], gr["gain"][i]
        y = np.clip(lift + (1 - lift) * x, 0, 1) ** (1.0 / gamma) * gain
        chans.append(np.clip(y * 255, 0, 255))
    lut = np.stack(chans, axis=-1).astype(np.uint8).reshape(256, 1, 3)
    return lut


def _vignette(w, h, strength):
    ys = (np.arange(h, dtype=np.float32) + 0.5) / h * 2 - 1
    xs = (np.arange(w, dtype=np.float32) + 0.5) / w * 2 - 1
    # oval for 9:16: weight x more so the sides darken like a lens
    r = np.sqrt((xs[None, :] * 1.05) ** 2 + (ys[:, None] * 0.82) ** 2)
    v = 1.0 - strength * np.clip((r - 0.55) / 0.75, 0, 1) ** 1.7
    return v.astype(np.float32)


def _grain(w, h, idx):
    rng = np.random.default_rng(1000 + idx)
    g = rng.standard_normal((max(1, h // 2), max(1, w // 2))).astype(np.float32)
    g = cv2.resize(g, (w, h), interpolation=cv2.INTER_LINEAR)
    return g * 0.75


def _paper_texture(w, h):
    a = noise_grid(max(64, w // 2), max(64, h // 2), feature=6.0, seed=77, beta=1.2, detail=6.0)
    b = noise_grid(max(64, w // 2), max(64, h // 2), feature=60.0, seed=78, beta=2.0)
    t = 0.6 * a + 0.4 * b
    t = cv2.resize(t, (w, h), interpolation=cv2.INTER_LINEAR)
    return (np.clip(t - 0.35, 0, 1) * 0.16).astype(np.float32)
