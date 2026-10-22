"""Saul Bass motion-graphics kit: hand-cut titles, cut-paper motifs and graphic animation.

STYLE.md rule 6: interludes, titles and transitions are flat cut paper. Everything here is a
filled polygon with scissor-cut edges in flat PAPER / ink / RED, and every function is a pure
function of its arguments and integer seeds (deterministic, frame to frame).

Conventions
  * Drawing happens in WORLD coordinates (1080x1920 frame px, y down) on any cairo context,
    usually a Frame layer:  `with f.layer() as L: bass.draw_title(L, T, (540, 900), RED)`.
  * Progress arguments `u` / `p` run 0..1 and are clamped: 0 = not started, 1 = at rest.
  * Colors are RGB tuples 0..1 (palette.RED, palette.PAPER, pal.ink). Angles are degrees.
  * Polygons are lists of (x, y) tuples (implicitly closed). `*_pts` functions return
    outlines, `*_path` functions add to the current cairo path (for ctx.clip() masks), the
    plain names fill.
  * `seed` fixes the scissor cuts. Keep it constant over a shot and edges never boil.
    Shapes that grow (spiral extent, bar length, arm grow) are cut once and revealed, so
    their edges stay put while they animate.

Sections: fonts and hand-cut titles / scissor cuts / animation helpers / motifs (bars,
spiral, circles, arm, hand, cut-out people, grid, triangles, panels, slash, heartbeat, loop,
lines, paper fields) / morphing / posterize presets and the Bass scene setup.
"""
import math
import os
import subprocess

import cairo
import numpy as np

from . import draw
from .core import (EASES, W, H, clamp, ease as _ease, hash01, inv_lerp, lerp, noise1,
                   noise_grid)
from .palette import PAPER, RED, PALETTES, Palette

INK = (0.012, 0.012, 0.014)          # neutral ink for when no palette is at hand
FULL = (0.0, 0.0, float(W), float(H))
_D2R = math.pi / 180.0


def _h(*a):
    return hash01(*a)


def _sn(*a):
    """Signed deterministic noise in [-1, 1)."""
    return hash01(*a) * 2.0 - 1.0


def _ez(name, t):
    """Ease with a name, a callable, or None (= linear)."""
    if name is None:
        return clamp(t)
    if callable(name):
        return name(clamp(t))
    return _ease(name, t)


def _col(c):
    return c if c is not None else INK


def _cols(c):
    """A color argument as a list of colors: rgb -> [rgb]; list of rgbs / None entries kept."""
    if c is None:
        return [None]
    if len(c) and isinstance(c[0], (int, float)):
        return [c]
    return list(c)


def _set(ctx, rgb, alpha=1.0):
    if len(rgb) == 4:
        ctx.set_source_rgba(rgb[0], rgb[1], rgb[2], rgb[3] * alpha)
    else:
        ctx.set_source_rgba(rgb[0], rgb[1], rgb[2], alpha)


# ============================================================================ polygon utils
def poly_area(pts):
    """Signed area (> 0 = clockwise on screen, y down)."""
    a = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return 0.5 * a


def orient(pts, cw=True):
    """Return pts ordered clockwise (cw=True) or counter-clockwise on screen."""
    a = poly_area(pts)
    if (a >= 0) == cw:
        return list(pts)
    return list(reversed(pts))


def centroid(pts):
    a = poly_area(pts)
    if abs(a) < 1e-9:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (sum(xs) / len(xs), sum(ys) / len(ys))
    cx = cy = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        k = x0 * y1 - x1 * y0
        cx += (x0 + x1) * k
        cy += (y0 + y1) * k
    return (cx / (6 * a), cy / (6 * a))


def bbox(polys):
    xs = [p[0] for c in polys for p in c]
    ys = [p[1] for c in polys for p in c]
    return (min(xs), min(ys), max(xs), max(ys))


def xform(pts, dx=0.0, dy=0.0, rot=0.0, sx=1.0, sy=None, pivot=(0.0, 0.0)):
    """Scale (sx, sy) and rotate (deg) about pivot, then translate by (dx, dy)."""
    sy = sx if sy is None else sy
    ca, sa = math.cos(rot * _D2R), math.sin(rot * _D2R)
    px, py = pivot
    out = []
    for x, y in pts:
        x, y = (x - px) * sx, (y - py) * sy
        out.append((px + dx + x * ca - y * sa, py + dy + x * sa + y * ca))
    return out


def clip_halfplane(pts, a, b):
    """Part of polygon pts on the LEFT of the directed line a->b (Sutherland-Hodgman)."""
    def side(p):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    out = []
    n = len(pts)
    for i in range(n):
        p, q = pts[i], pts[(i + 1) % n]
        sp, sq = side(p), side(q)
        if sp <= 0:
            out.append(p)
        if (sp < 0 < sq) or (sq < 0 < sp):
            k = sp / (sp - sq)
            out.append((p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k))
    return out


def path_polys(ctx, polys):
    for c in polys:
        if len(c) >= 2:
            draw.poly(ctx, c)


def fill_polys(ctx, polys, color, alpha=1.0, evenodd=False):
    """Fill a list of contours as one shape (nonzero winding unless evenodd)."""
    if alpha <= 0:
        return
    ctx.new_path()
    path_polys(ctx, polys)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD if evenodd else cairo.FILL_RULE_WINDING)
    _set(ctx, color, alpha)
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)


def _bigrect(m=4000.0):
    return [(-m, -m), (W + m, -m), (W + m, H + m), (-m, H + m)]


# ============================================================================ scissor cuts
def scissor(pts, seed=0, sag=1.6, amp=1.0, max_len=80.0, corner=32.0, closed=True):
    """Re-cut a finely sampled outline (curves) as straight scissor cuts.

    The outline is split at its corners (turns sharper than `corner` deg, which are kept), and
    each run between corners is replaced by straight chords that stay within a random
    tolerance (`sag` px, varied per cut) of the true curve and are at most ~`max_len` px long.
    Every resulting vertex is then nudged by up to `amp` px. Curves become faceted, straight
    edges stay straight but slightly broken: the look of letters cut from paper by hand.
    """
    P = []
    for p in pts:
        if not P or abs(p[0] - P[-1][0]) + abs(p[1] - P[-1][1]) > 1e-6:
            P.append((float(p[0]), float(p[1])))
    if closed and len(P) > 1 and abs(P[0][0] - P[-1][0]) + abs(P[0][1] - P[-1][1]) < 1e-6:
        P.pop()
    n = len(P)
    if n < 3:
        return P
    cth = corner * _D2R
    if closed:
        corners = []
        for i in range(n):
            a, b, c = P[i - 1], P[i], P[(i + 1) % n]
            d = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(b[1] - a[1], b[0] - a[0])
            d = (d + math.pi) % (2 * math.pi) - math.pi
            if abs(d) > cth:
                corners.append(i)
        if not corners:
            corners = [0]
        s = corners[0]
        R = P[s:] + P[:s]
        anchors = [(c - s) % n for c in corners] + [n]
        R = R + [R[0]]
    else:
        R = P
        anchors = [0]
        for i in range(1, n - 1):
            a, b, c = P[i - 1], P[i], P[i + 1]
            d = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(b[1] - a[1], b[0] - a[0])
            d = (d + math.pi) % (2 * math.pi) - math.pi
            if abs(d) > cth:
                anchors.append(i)
        anchors.append(n - 1)
    out = [R[0]]
    k = 0
    for ai in range(len(anchors) - 1):
        i, end = anchors[ai], anchors[ai + 1]
        while i < end:
            k += 1
            tol = sag * (0.35 + 1.3 * _h(seed, k, 11))
            mlen = max_len * (0.45 + 1.0 * _h(seed, k, 12))
            best = i + 1
            j = i + 2
            while j <= end:
                ax, ay = R[i]
                bx, by = R[j]
                dx, dy = bx - ax, by - ay
                L = math.hypot(dx, dy)
                if L > mlen:
                    break
                ok = True
                if L > 1e-9:
                    for q in range(i + 1, j):
                        if abs((R[q][0] - ax) * dy - (R[q][1] - ay) * dx) / L > tol:
                            ok = False
                            break
                if not ok:
                    break
                best = j
                j += 1
            out.append(R[best])
            i = best
    if closed:
        out.pop()                     # last == first
    if amp > 0:
        out = [(x + amp * _sn(seed, q, 21), y + amp * _sn(seed, q, 22)) for q, (x, y) in enumerate(out)]
    return out


def cut(pts, seed=0, amp=1.8, seg=(22.0, 64.0), close=True):
    """Scissor-cut a straight-edged polygon (thin wrapper of draw.cut_paper)."""
    return draw.cut_paper(pts, seed=seed, amp=amp, seg=seg, close=close)


def cut_rect(x0, y0, x1, y1, seed=0, amp=1.8, seg=(26.0, 80.0)):
    return draw.cut_paper([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], seed=seed, amp=amp, seg=seg)


def cut_ellipse(c, rx, ry, seed=0, angle=0.0, sag=None, amp=None, max_len=None):
    """An ellipse cut from paper: faceted by straight snips (stable for a given seed)."""
    r = max(rx, ry)
    n = max(24, int(2 * math.pi * r / 2.0))
    pts = draw.ellipse_pts(c, rx, ry, n=n, angle=angle)
    sag = sag if sag is not None else clamp(0.012 * r, 0.25, 3.2)
    amp = amp if amp is not None else clamp(0.006 * r, 0.15, 1.6)
    max_len = max_len if max_len is not None else max(6.0, 0.55 * r)
    return scissor(pts, seed=seed, sag=sag, amp=amp, max_len=max_len, corner=60.0)


def ring_pts(c, r, seed=0, n=None, amp=None, phase=0.0):
    """A cut circle with a FIXED vertex count (pass n= to keep facets stable while r animates)."""
    n = n or int(clamp(round(2 * math.pi * r / 34.0), 18, 120))
    amp = amp if amp is not None else min(3.0, 0.012 * r + 0.6)
    out = []
    for i in range(n):
        th = 2 * math.pi * (i + 0.42 * _sn(seed, i, 1)) / n + phase * _D2R
        rr = r + amp * _sn(seed, i, 2)
        out.append((c[0] + rr * math.cos(th), c[1] + rr * math.sin(th)))
    return out


# ============================================================================ fonts
FONT_QUERY = "Inter Display:style=Black"
_FONT_FALLBACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
_FONTS = {}


def font_path(query=FONT_QUERY):
    """Font file for an fc-match query (Inter Display Black by default)."""
    key = ("path", query)
    if key not in _FONTS:
        p = None
        try:
            p = subprocess.run(["fc-match", "-f", "%{file}", query], capture_output=True,
                               text=True, timeout=10).stdout.strip()
        except Exception:
            p = None
        fam = query.split(":")[0].replace(" ", "").lower()
        if not p or not os.path.exists(p) or fam not in os.path.basename(p).lower().replace("-", ""):
            p = _FONT_FALLBACK if query == FONT_QUERY and os.path.exists(_FONT_FALLBACK) else p
        if not p:
            raise RuntimeError("font not found: %s" % query)
        _FONTS[key] = p
    return _FONTS[key]


class _Font:
    """Glyph outlines (flattened, font units, y up), advances and GPOS pair kerning."""

    def __init__(self, path):
        from fontTools.ttLib import TTFont
        self.tt = TTFont(path)
        self.upm = float(self.tt["head"].unitsPerEm)
        os2 = self.tt["OS/2"]
        self.cap = float(getattr(os2, "sCapHeight", 0) or 0.7 * self.upm)
        self.cmap = self.tt.getBestCmap()
        self.gs = self.tt.getGlyphSet()
        self.hmtx = self.tt["hmtx"]
        self._outl = {}
        self._kc = {}
        self._kern = self._load_kern()

    def gname(self, ch):
        return self.cmap.get(ord(ch), ".notdef")

    def advance(self, g):
        return float(self.hmtx[g][0])

    def outline(self, g):
        if g not in self._outl:
            from fontTools.pens.basePen import BasePen
            step = self.upm / 400.0

            class Pen(BasePen):
                def __init__(s, gs):
                    BasePen.__init__(s, gs)
                    s.contours, s.cur = [], []

                def _moveTo(s, p):
                    s._flush()
                    s.cur = [p]

                def _lineTo(s, p):
                    s.cur.append(p)

                def _curveToOne(s, p1, p2, p3):
                    p0 = s._getCurrentPoint()
                    L = math.dist(p0, p1) + math.dist(p1, p2) + math.dist(p2, p3)
                    m = max(2, min(96, int(L / step) + 1))
                    for i in range(1, m + 1):
                        t = i / m
                        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
                        s.cur.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                                      a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))

                def _closePath(s):
                    s._flush()

                def _endPath(s):
                    s._flush()

                def _flush(s):
                    c = s.cur
                    if len(c) > 2:
                        if math.dist(c[0], c[-1]) < 1e-6:
                            c = c[:-1]
                        s.contours.append(c)
                    s.cur = []

            pen = Pen(self.gs)
            self.gs[g].draw(pen)
            pen._flush()
            self._outl[g] = pen.contours
        return self._outl[g]

    def _load_kern(self):
        subs = []
        if "GPOS" not in self.tt:
            return subs
        gpos = self.tt["GPOS"].table
        idx = set()
        for fr in gpos.FeatureList.FeatureRecord:
            if fr.FeatureTag == "kern":
                idx.update(fr.Feature.LookupListIndex)
        for li in sorted(idx):
            lk = gpos.LookupList.Lookup[li]
            tabs = []
            for st in lk.SubTable:
                if lk.LookupType == 9:
                    if getattr(st, "ExtensionLookupType", 0) != 2:
                        continue
                    st = st.ExtSubTable
                elif lk.LookupType != 2:
                    continue
                cov = {g: i for i, g in enumerate(st.Coverage.glyphs)}
                tabs.append((st, cov, {}))
            subs.append(tabs)
        return subs

    def kern(self, l, r):
        key = (l, r)
        if key in self._kc:
            return self._kc[key]
        total = 0.0
        for tabs in self._kern:
            for st, cov, cache in tabs:
                if l not in cov:
                    continue
                if st.Format == 1:
                    if l not in cache:
                        d = {}
                        for rec in st.PairSet[cov[l]].PairValueRecord:
                            v = rec.Value1
                            d[rec.SecondGlyph] = float(getattr(v, "XAdvance", 0) or 0) if v is not None else 0.0
                        cache[l] = d
                    if r in cache[l]:
                        total += cache[l][r]
                        break
                elif st.Format == 2:
                    c1 = st.ClassDef1.classDefs.get(l, 0)
                    c2 = st.ClassDef2.classDefs.get(r, 0)
                    v = st.Class1Record[c1].Class2Record[c2].Value1
                    total += float(getattr(v, "XAdvance", 0) or 0) if v is not None else 0.0
                    break
        self._kc[key] = total
        return total


def _font(path=None):
    p = path or font_path()
    if p not in _FONTS:
        _FONTS[p] = _Font(p)
    return _FONTS[p]


# ============================================================================ hand-cut titles
class Glyph:
    """One hand-cut letter. polys: contours in TITLE space (title centered on (0, 0)), already
    cut and misaligned; pivot: the letter's own center (animations rotate/scale about it)."""

    __slots__ = ("ch", "index", "line", "polys", "pivot", "bbox", "height")

    def __init__(self, ch, index, line, polys, height):
        self.ch, self.index, self.line, self.polys, self.height = ch, index, line, polys, height
        self.bbox = bbox(polys)
        self.pivot = ((self.bbox[0] + self.bbox[2]) / 2, (self.bbox[1] + self.bbox[3]) / 2)

    @property
    def width(self):
        return self.bbox[2] - self.bbox[0]

    def path(self, ctx, at=(0.0, 0.0), dx=0.0, dy=0.0, rot=0.0, sx=1.0, sy=1.0):
        """Add this letter to ctx's path at title origin `at`, moved by (dx, dy), rotated
        (deg) and scaled about its pivot."""
        px, py = self.pivot
        plain = rot == 0 and sx == 1 and sy == 1
        ctx.save()
        ctx.translate(at[0] + dx, at[1] + dy)
        if not plain:
            ctx.translate(px, py)
            if rot:
                ctx.rotate(rot * _D2R)
            if sx != 1 or sy != 1:
                ctx.scale(sx if abs(sx) > 1e-4 else 1e-4, sy if abs(sy) > 1e-4 else 1e-4)
            ctx.translate(-px, -py)
        path_polys(ctx, self.polys)
        ctx.restore()


class Title(list):
    """List of Glyph (spaces dropped) + layout metrics: text, height (cap height px),
    bbox (x0, y0, x1, y1) in title space (centered on 0, 0), width, block_h."""

    def __init__(self, glyphs, text, height, bb):
        super().__init__(glyphs)
        self.text, self.height, self.bbox = text, height, bb
        self.width = bb[2] - bb[0]
        self.block_h = bb[3] - bb[1]
        nl = 1 + max((g.line for g in glyphs), default=0)
        self.lines_bb = []          # per line (x0, y0, x1, y1) in title space
        for li in range(nl):
            gl = [c for g in glyphs if g.line == li for c in g.polys]
            self.lines_bb.append(bbox(gl) if gl else (0.0, 0.0, 0.0, 0.0))

    def outline(self, center=(0.0, 0.0)):
        """All contours moved to `center` (world), e.g. for a mask or a morph source."""
        return [[(x + center[0], y + center[1]) for x, y in c] for g in self for c in g.polys]

    def path(self, ctx, center, scale=1.0, rot=0.0):
        ctx.save()
        ctx.translate(*center)
        if rot:
            ctx.rotate(rot * _D2R)
        if scale != 1:
            ctx.scale(scale, scale)
        for g in self:
            path_polys(ctx, g.polys)
        ctx.restore()


class _LRU(dict):
    """Small bounded cache (oldest entries dropped first)."""

    def __init__(self, n):
        super().__init__()
        self.n = n

    def __setitem__(self, k, v):
        if k not in self and len(self) >= self.n:
            for old in list(self.keys())[: max(1, self.n // 8)]:
                del self[old]
        super().__setitem__(k, v)


_TITLES = _LRU(256)        # laid-out titles
_GEOM = _LRU(2048)         # cut geometry: letter pieces, spirals, arms, cut-outs


def title_width(text, height=100.0, tracking=0.07, kern=True, space=0.62, font=None):
    """Width in px of the widest line of `text` set at cap height `height` (no roughening)."""
    F = _font(font)
    k = height / F.cap
    best = 0.0
    for line in text.split("\n"):
        pen, prev, n = 0.0, None, 0
        for ch in line:
            if ch == " ":
                pen += space * height
                prev = None
                continue
            g = F.gname(ch)
            if kern and prev is not None:
                pen += F.kern(prev, g) * k
            pen += F.advance(g) * k + tracking * height
            prev = g
            n += 1
        best = max(best, pen - (tracking * height if n else 0.0))
    return best


def title_glyphs(text, height=180.0, tracking=0.07, seed=0, rough=1.0, jitter=1.0, leading=1.3,
                 align="center", kern=True, space=0.62, font=None, width=None):
    """Lay out `text` as hand-cut letters (Inter Display Black outlines, via fontTools).

    height: cap height in px. width: if given, the cap height is chosen so the widest line is
    `width` px wide (and `height` is ignored). tracking: extra letter spacing as a fraction
    of height. rough: scissor-cut strength (0 = clean outlines). jitter: per-letter
    misalignment (rotation, baseline, scale; 0 = none). '\\n' makes extra lines (leading x
    height apart), aligned left / center / right. space: word space as a fraction of height.
    Returns a Title (list of Glyph). Results are cached: do not mutate them.
    """
    if width is not None:
        height = 100.0 * width / max(title_width(text, 100.0, tracking, kern, space, font), 1e-6)
    key = (text, round(float(height), 3), tracking, seed, rough, jitter, leading, align, kern, space, font)
    if key in _TITLES:
        return _TITLES[key]
    F = _font(font)
    k = height / F.cap
    lines = text.split("\n")
    placed = []           # (ch, line, contours px y-down baseline 0, pen_x)
    widths = []
    gi = 0
    for li, line in enumerate(lines):
        pen = 0.0
        prev = None
        items = []
        for ch in line:
            if ch == " ":
                pen += space * height
                prev = None
                continue
            g = F.gname(ch)
            if kern and prev is not None:
                pen += F.kern(prev, g) * k
            cont = [[(pen + x * k, -y * k) for x, y in c] for c in F.outline(g)]
            if cont:
                items.append((ch, cont))
            pen += F.advance(g) * k + tracking * height
            prev = g
        lw = pen - (tracking * height if items else 0.0)
        widths.append(lw)
        placed.append(items)
    total_h = height + (len(lines) - 1) * leading * height
    glyphs = []
    sag = rough * max(0.7, 0.0085 * height)
    amp = rough * max(0.45, 0.0075 * height)
    mlen = max(10.0, 0.40 * height)
    for li, items in enumerate(placed):
        lw = widths[li]
        ox = {"left": 0.0, "right": -lw}.get(align, -lw / 2.0)
        if align == "left":
            ox = -max(widths) / 2.0
        elif align == "right":
            ox = max(widths) / 2.0 - lw
        oy = -total_h / 2.0 + height + li * leading * height
        for ch, cont in items:
            s = (seed * 7919 + gi * 131 + 17) % 100003
            cont = [[(x + ox, y + oy) for x, y in c] for c in cont]
            if rough > 0:
                cont = [scissor(c, seed=s * 31 + ci, sag=sag, amp=amp, max_len=mlen) for ci, c in enumerate(cont)]
            bb = bbox(cont)
            piv = ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2)
            if jitter > 0:
                rot = jitter * 3.2 * _sn(s, 1)
                dy = jitter * 0.04 * height * _sn(s, 2)
                dx = jitter * 0.014 * height * _sn(s, 3)
                sc = 1.0 + jitter * 0.035 * _sn(s, 4)
                sh = jitter * 0.035 * _sn(s, 6)            # stems not quite parallel to the others
                cont = [[(x + sh * (y - piv[1]), y) for x, y in c] for c in cont]
                cont = [xform(c, dx, dy, rot, sc * (1.0 + jitter * 0.03 * _sn(s, 7)),
                              sc * (1.0 + jitter * 0.03 * _sn(s, 5)), piv) for c in cont]
            glyphs.append(Glyph(ch, gi, li, cont, height))
            gi += 1
    bb = bbox([c for g in glyphs for c in g.polys]) if glyphs else (0, 0, 0, 0)
    T = Title(glyphs, text, float(height), bb)
    _TITLES[key] = T
    return T


# ----------------------------------------------------------------------------- title animation
_DIRS = {"left": (-1.0, 0.0), "right": (1.0, 0.0), "top": (0.0, -1.0), "bottom": (0.0, 1.0),
         "up": (0.0, -1.0), "down": (0.0, 1.0)}


def _drop_ease(p):
    """Gravity fall (accelerating) that lands at p=0.7, then one small paper bounce."""
    p = clamp(p)
    if p < 0.7:
        return (p / 0.7) ** 2
    q = (p - 0.7) / 0.3
    return 1.0 - 0.07 * math.sin(math.pi * q) * (1 - q * 0.4)


def _letter_fx(anim, g, i, p, e, kw, seed, T):
    """Per-letter transform for the simple (unclipped) title animations."""
    if anim in (None, "none"):
        return {}
    if p <= 0.0 and kw.get("hide", True):
        return None
    if anim == "slide":
        frm = kw.get("frm", "alt")
        if frm == "alt":
            v = (-1.0 if i % 2 == 0 else 1.0, 0.0)
        elif frm == "altv":
            v = (0.0, -1.0 if i % 2 == 0 else 1.0)
        elif isinstance(frm, (int, float)):
            v = (math.cos(frm * _D2R), math.sin(frm * _D2R))
        else:
            v = _DIRS[frm]
        q = 1.0 - _ez(e or "out5", p)
        d = kw.get("dist", 1300.0)
        return dict(dx=v[0] * d * q, dy=v[1] * d * q)
    if anim == "drop":
        q = 1.0 - _drop_ease(p) if e is None else 1.0 - _ez(e, p)
        r0 = kw.get("spin", 14.0) * _sn(seed, i, 41)
        return dict(dy=-kw.get("dist", 1100.0) * q, rot=r0 * min(1.0, q * 3.0))
    if anim == "pop":
        s = _ez(e or "outback", p)
        return dict(sx=s, sy=s, rot=kw.get("spin", 30.0) * _sn(seed, i, 43) * (1 - _ez("out3", p)))
    if anim == "stamp":
        s = lerp(kw.get("big", 2.6), 1.0, _ez(e or "in3", min(1.0, p / 0.75)))
        if p > 0.75:
            s = 1.0 - 0.05 * math.sin(math.pi * (p - 0.75) / 0.25)
        return dict(sx=s, sy=s)
    if anim == "flip":
        a = (1.0 - _ez(e or "outback", p)) * 90.0
        return dict(sx=max(0.02, math.cos(min(89.0, a) * _D2R)) if a > 0 else 1.0)
    if anim == "rise":
        q = 1.0 - _ez(e or "out5", p)
        return dict(dy=q * T.height * kw.get("depth", 1.35))
    if anim == "scatter":
        q = 1.0 - _ez(e or "out5", p)
        d = kw.get("dist", 700.0)
        a = _h(seed, i, 51) * 2 * math.pi
        return dict(dx=math.cos(a) * d * q, dy=math.sin(a) * d * q, rot=_sn(seed, i, 52) * 120 * q)
    raise ValueError("unknown title anim %r" % anim)


def ranks(n, order="ltr", seed=0):
    """Reveal rank per item and the number of distinct steps: (ranks, steps).
    order: ltr, rtl, center (middle first), edges (ends first), random, or a list."""
    if isinstance(order, (list, tuple)):
        r = list(order)
        return r, max(r) + 1 if r else 1
    if order == "rtl":
        return [n - 1 - i for i in range(n)], n
    if order in ("center", "edges"):
        c = (n - 1) / 2.0
        d = [abs(i - c) for i in range(n)]
        m = max(d) if d else 0
        r = [x if order == "center" else m - x for x in d]
        return r, m + 1
    if order == "random":
        idx = sorted(range(n), key=lambda i: _h(seed, i, 97))
        r = [0] * n
        for k, i in enumerate(idx):
            r[i] = k
        return r, n
    return list(range(n)), n


def draw_title(ctx, T, center, color, u=1.0, anim=None, order="ltr", overlap=0.75, ease=None,
               alpha=1.0, scale=1.0, rot=0.0, clip=None, seed=0, fx=None, **kw):
    """Draw a Title at `center` (world) in flat `color`, animated by progress u (1 = at rest).

    anim (per-letter, staggered by `order`/`overlap`; letters not started are hidden):
      None    static
      'slide' letters slide in. frm='alt' (alternate left/right), 'altv', 'left', 'right',
              'top', 'bottom' or an angle in deg (direction they come FROM); dist=1300
      'drop'  fall from above with a paper bounce (dist=1100, spin=14)
      'pop'   scale up from nothing with overshoot and a spin snap (spin=30)
      'stamp' slam down from big=2.6x
      'flip'  rotate in about each letter's vertical axis
      'rise'  rise from behind a line: line=y offset in title space (default the baseline);
              depth=1.35 (x height)
      'scatter' letters fly in from scattered positions and angles (dist=700)
      'assemble' each letter is cut into pieces=3 that fly in and snap together (dist=1.6 x h)
      'split' u = how far apart (0 = intact): the title is cut by strips=2 parallel lines at
              angle=0 deg and the strips slide apart alternately by dist=700 (+ gap=0
              perpendicular). Psycho.
      'waterline' level=world y of the surface: above it the letters are drawn in `color`;
              below it in below=(rgb or None to hide), sliced into bands=7 refraction strips
              shifted by +-shift=10 px (phase= to animate the ripple) and pushed down by sink=0.
    fx(i, glyph, p, tr) -> tr: optional hook to edit/replace each letter's transform dict
    (dx, dy, rot, sx, sy, alpha, color); return None to hide the letter.
    clip: optional world rect (x0, y0, x1, y1) the title is clipped to (slide out of an edge).
    scale/rot transform the whole title about `center`.
    """
    n = len(T)
    if n == 0 or alpha <= 0:
        return
    rk, steps = ranks(n, order, seed)
    ctx.save()
    if clip is not None:
        ctx.new_path()
        ctx.rectangle(clip[0], clip[1], clip[2] - clip[0], clip[3] - clip[1])
        ctx.clip()
    if anim == "waterline":
        _title_waterline(ctx, T, center, color, alpha, scale, rot, kw)
        ctx.restore()
        return
    ctx.translate(*center)
    if rot:
        ctx.rotate(rot * _D2R)
    if scale != 1:
        ctx.scale(scale, scale)
    if anim == "split":
        _title_split(ctx, T, color, u, alpha, kw, seed, ease)
    elif anim == "assemble":
        _title_assemble(ctx, T, color, u, rk, steps, overlap, ease, alpha, kw, seed)
    else:
        line = kw.get("line", None)
        for i, g in enumerate(T):
            p = stagger(u, rk[i], steps, overlap=overlap, ease="linear")
            tr = _letter_fx(anim, g, i, p, ease, kw, seed, T)
            if fx is not None:
                tr = fx(i, g, p, dict(tr) if tr is not None else None)
            if tr is None:
                continue
            ctx.new_path()
            if anim == "rise":
                ctx.save()
                ly = line if line is not None else T.lines_bb[g.line][3] + 0.02 * T.height
                ctx.rectangle(-1e5, -1e5, 2e5, 1e5 + ly)
                ctx.clip()
            g.path(ctx, (0, 0), tr.get("dx", 0.0), tr.get("dy", 0.0), tr.get("rot", 0.0),
                   tr.get("sx", 1.0), tr.get("sy", 1.0))
            _set(ctx, tr.get("color", color), alpha * tr.get("alpha", 1.0))
            ctx.fill()
            if anim == "rise":
                ctx.restore()
    ctx.restore()


def _title_split(ctx, T, color, u, alpha, kw, seed, ease=None):
    e = _ez(ease or "inout5", u)
    if e <= 0.0:
        ctx.new_path()
        for g in T:
            path_polys(ctx, g.polys)
        _set(ctx, color, alpha)
        ctx.fill()
        return
    m = max(2, int(kw.get("strips", 2)))
    ang = kw.get("angle", 0.0) * _D2R
    dirv = (math.cos(ang), math.sin(ang))
    nrm = (-dirv[1], dirv[0])
    x0, y0, x1, y1 = T.bbox
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    proj = [c[0] * nrm[0] + c[1] * nrm[1] for c in corners]
    lo, hi = min(proj) - 2, max(proj) + 2
    cuts = [lo]
    for k in range(1, m):
        f = k / m + (kw.get("irregular", 0.25) / m) * _sn(seed, k, 61)
        cuts.append(lo + (hi - lo) * f)
    cuts.append(hi)
    cuts[0], cuts[-1] = -1e5, 1e5
    dist = kw.get("dist", 700.0)
    gap = kw.get("gap", 0.0)
    BIG = 1e5
    for k in range(m):
        a, b = cuts[k], cuts[k + 1]
        sgn = -1.0 if k % 2 == 0 else 1.0
        off = sgn * dist * e
        push = (k - (m - 1) / 2.0) * gap * e
        region = [(dirv[0] * -BIG + nrm[0] * a, dirv[1] * -BIG + nrm[1] * a),
                  (dirv[0] * BIG + nrm[0] * a, dirv[1] * BIG + nrm[1] * a),
                  (dirv[0] * BIG + nrm[0] * b, dirv[1] * BIG + nrm[1] * b),
                  (dirv[0] * -BIG + nrm[0] * b, dirv[1] * -BIG + nrm[1] * b)]
        ctx.save()
        ctx.translate(dirv[0] * off + nrm[0] * push, dirv[1] * off + nrm[1] * push)
        ctx.new_path()
        draw.poly(ctx, region)
        ctx.clip()
        ctx.new_path()
        for g in T:
            path_polys(ctx, g.polys)
        _set(ctx, color, alpha)
        ctx.fill()
        ctx.restore()


def _letter_pieces(g, pieces, seed):
    """Split a letter's bbox into `pieces` convex regions by random straight cuts (cached)."""
    key = ("pieces", tuple(round(v, 2) for v in g.bbox), g.index, pieces, seed)
    if key in _GEOM:
        return _GEOM[key]
    x0, y0, x1, y1 = g.bbox
    m = 3.0
    regs = [[(x0 - m, y0 - m), (x1 + m, y0 - m), (x1 + m, y1 + m), (x0 - m, y1 + m)]]
    for k in range(pieces - 1):
        regs.sort(key=lambda r: -abs(poly_area(r)))
        r = regs.pop(0)
        c = centroid(r)
        c = (c[0] + 0.15 * g.width * _sn(seed, g.index, k, 1), c[1] + 0.12 * g.height * _sn(seed, g.index, k, 2))
        th = (25 + 130 * _h(seed, g.index, k, 3)) * _D2R
        a = (c[0] - math.cos(th) * 1e4, c[1] - math.sin(th) * 1e4)
        b = (c[0] + math.cos(th) * 1e4, c[1] + math.sin(th) * 1e4)
        A = clip_halfplane(r, a, b)
        B = clip_halfplane(r, b, a)
        regs += [p for p in (A, B) if len(p) >= 3]
    regs.sort(key=lambda r: centroid(r)[1] + 0.3 * centroid(r)[0])
    _GEOM[key] = regs
    return regs


def _title_assemble(ctx, T, color, u, rk, steps, overlap, e, alpha, kw, seed):
    pieces = int(kw.get("pieces", 3))
    dist = kw.get("dist", 1.6 * T.height)
    spin = kw.get("spin", 75.0)
    for i, g in enumerate(T):
        p = stagger(u, rk[i], steps, overlap=overlap, ease="linear")
        if p >= 1.0:
            ctx.new_path()
            path_polys(ctx, g.polys)
            _set(ctx, color, alpha)
            ctx.fill()
            continue
        if p <= 0.0:
            continue
        regs = _letter_pieces(g, pieces, seed)
        for k, reg in enumerate(regs):
            pk = stagger(p, k, len(regs), overlap=0.55, ease=e or "out3")
            if pk <= 0.0:
                continue
            q = 1.0 - pk
            a = _h(seed, i, k, 71) * 2 * math.pi
            c = centroid(reg)
            ctx.save()
            ctx.translate(c[0] + math.cos(a) * dist * q, c[1] + math.sin(a) * dist * q)
            ctx.rotate(spin * _sn(seed, i, k, 72) * q * _D2R)
            ctx.translate(-c[0], -c[1])
            ctx.new_path()
            draw.poly(ctx, reg)
            ctx.clip()
            ctx.new_path()
            path_polys(ctx, g.polys)
            _set(ctx, color, alpha)
            ctx.fill()
            ctx.restore()


def _title_waterline(ctx, T, center, color, alpha, scale, rot, kw):
    level = kw.get("level", center[1])
    below = kw.get("below", None)
    sink = kw.get("sink", 0.0)

    def body(dx=0.0, dy=0.0):
        ctx.save()
        ctx.translate(center[0] + dx, center[1] + dy)
        if rot:
            ctx.rotate(rot * _D2R)
        if scale != 1:
            ctx.scale(scale, scale)
        ctx.new_path()
        for g in T:
            path_polys(ctx, g.polys)
        ctx.restore()

    ctx.save()
    ctx.new_path()
    ctx.rectangle(-1e5, -1e5, 2e5, 1e5 + level)
    ctx.clip()
    body(0.0, sink)
    _set(ctx, color, alpha)
    ctx.fill()
    ctx.restore()
    if below is None:
        return
    bands = max(1, int(kw.get("bands", 7)))
    shift = kw.get("shift", 10.0)
    phase = kw.get("phase", 0.0)
    y1 = center[1] + sink + T.bbox[3] * scale + 40
    bh = max(4.0, (y1 - level) / bands)
    for b in range(bands + 1):
        ya = level + b * bh
        ctx.save()
        ctx.new_path()
        ctx.rectangle(-1e5, ya, 2e5, bh + (0.6 if b < bands else 1e5))
        ctx.clip()
        body(shift * math.sin(1.9 * b + phase), sink + kw.get("drop", 0.0))
        _set(ctx, below, alpha)
        ctx.fill()
        ctx.restore()


# ============================================================================ animation helpers
def stagger(t, i, n, start=0.0, dur=1.0, overlap=0.5, ease="out3"):
    """Eased local progress (0..1) of item i of n whose reveals share the window
    [start, start + dur]. overlap: 0 = one after another, 1 = all together. i may be a float
    rank (see ranks())."""
    n = max(float(n), 1.0)
    w = dur / (1.0 + (n - 1.0) * (1.0 - overlap))
    s = start + i * w * (1.0 - overlap)
    return _ez(ease, inv_lerp(s, s + w, t))


def snap(t, t0, dur, a, b, ease="outback"):
    """Value a -> b over [t0, t0 + dur] with overshoot (default) or any crisp ease."""
    k = _ez(ease, inv_lerp(t0, t0 + dur, t))
    return lerp(a, b, k)


def slide(t, t0, dur, frm, to, ease="out5"):
    """Point (or tuple) frm -> to: a crisp graphic slide."""
    return snap(t, t0, dur, tuple(frm), tuple(to), ease)


def spin(t, t0, dur, a0, a1, ease="outback"):
    """Angle a0 -> a1 (deg) with overshoot: a snap rotation."""
    return snap(t, t0, dur, a0, a1, ease)


def pop(t, t0, dur, overshoot=1.70158):
    """Scale 0 -> 1 with overshoot (outback): shapes popping onto the paper."""
    x = inv_lerp(t0, t0 + dur, t)
    if x <= 0:
        return 0.0
    x -= 1.0
    return x * x * ((overshoot + 1) * x + overshoot) + 1.0


def settle(t, t0, amp=1.0, freq=3.0, decay=7.0):
    """Damped wobble after an impact at t0 (0 before t0): add it to a position or angle."""
    if t < t0:
        return 0.0
    d = t - t0
    return amp * math.exp(-decay * d) * math.sin(2 * math.pi * freq * d)


def on_twos(t, fps=12.0):
    """Quantize time to stop-motion steps (12 fps = 'on twos'): cut-paper animation feel."""
    return math.floor(t * fps + 1e-6) / fps


def shuffle_step(t, rate=6.0, seed=0, n=4):
    """Integer 0..n-1 that changes `rate` times a second (pick which cut-out shows)."""
    return int(_h(seed, math.floor(t * rate)) * n)


# ============================================================================ motifs
# ----------------------------------------------------------------------------- bars
def bar_rects(rect=FULL, n=7, axis="h", sizes=None, gap=0.0, seed=0, irregular=0.45):
    """Slots for n bars across rect: axis 'h' = horizontal bars stacked vertically, 'v' =
    vertical bars side by side. sizes: relative thicknesses (default random, seeded)."""
    x0, y0, x1, y1 = rect
    span = (y1 - y0) if axis == "h" else (x1 - x0)
    if sizes is None:
        sizes = [1.0 + irregular * _sn(seed, i, 81) for i in range(n)]
    tot = sum(sizes)
    avail = span - gap * (n - 1)
    out = []
    pos = 0.0
    for i, s in enumerate(sizes):
        th = avail * s / tot
        a = pos
        b = pos + th
        pos = b + gap
        if axis == "h":
            out.append((x0, y0 + a, x1, y0 + b))
        else:
            out.append((x0 + a, y0, x0 + b, y1))
    return out


def bars(ctx, u, rect=FULL, n=7, axis="h", colors=(INK,), sizes=None, gap=0.0, frm="alt",
         mode="slide", overlap=0.6, ease="out5", seed=0, cut=1.0, lengths=None, alpha=1.0):
    """Bass bars: n flat cut-paper bars that slide / grow into their slots, staggered.

    axis 'h': horizontal bars that move horizontally ('v': vertical bars moving vertically).
    frm: 'alt' (alternate sides), 'start' (left/top), 'end', 'random'.
    mode: 'slide' (in from off-frame; u=1 at rest), 'grow' (extend from the side through a
    clean cut), 'out' (leave, continuing their travel; u=1 gone), 'inout' (u<.5 in, u>.5 out).
    lengths: None = full span; 'random' = Psycho-style strips of random length/offset; or a
    list of (start_frac, end_frac). Returns the bars' rest rects.
    """
    slots = bar_rects(rect, n, axis, sizes, gap, seed)
    rk, steps = ranks(n, "random" if frm == "random" else "ltr", seed)
    x0, y0, x1, y1 = rect
    span = (x1 - x0) if axis == "h" else (y1 - y0)
    travel = span + 300.0
    for i, (a0, b0, a1, b1) in enumerate(slots):
        if lengths == "random":
            s0 = 0.55 * _h(seed, i, 83)
            s1 = min(1.0, s0 + 0.35 + 0.6 * _h(seed, i, 84))
        elif lengths:
            s0, s1 = lengths[i % len(lengths)]
        else:
            s0, s1 = -0.01, 1.01
        if axis == "h":
            r = (x0 + span * s0, b0, x0 + span * s1, b1)
        else:
            r = (a0, y0 + span * s0, a1, y0 + span * s1)
        if frm == "alt":
            side = -1.0 if i % 2 == 0 else 1.0
        elif frm == "end":
            side = 1.0
        elif frm == "random":
            side = -1.0 if _h(seed, i, 85) < 0.5 else 1.0
        else:
            side = -1.0
        if mode == "inout":
            pin = stagger(u * 2.0, rk[i], steps, overlap=overlap, ease=ease)
            pout = stagger(u * 2.0 - 1.0, rk[i], steps, overlap=overlap, ease=_flip_ease(ease))
            off = side * travel * (1.0 - pin) - side * travel * pout
            if pin <= 0 or pout >= 1:
                continue
        elif mode == "out":
            p = stagger(u, rk[i], steps, overlap=overlap, ease=_flip_ease(ease))
            if p >= 1:
                continue
            off = -side * travel * p
        else:
            p = stagger(u, rk[i], steps, overlap=overlap, ease=ease)
            if p <= 0:
                continue
            off = side * travel * (1.0 - p) if mode == "slide" else 0.0
        poly = cut_rect(*r, seed=seed * 101 + i, amp=1.8 * cut) if cut > 0 else \
            [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]
        cl = _cols(colors)
        col = cl[i % len(cl)]
        ctx.save()
        if mode == "grow":
            if axis == "h":
                L = (r[2] - r[0]) * p
                cx = r[0] if side < 0 else r[2] - L
                ctx.rectangle(cx - 2, r[1] - 50, L + 4, r[3] - r[1] + 100)
            else:
                L = (r[3] - r[1]) * p
                cy = r[1] if side < 0 else r[3] - L
                ctx.rectangle(r[0] - 50, cy - 2, r[2] - r[0] + 100, L + 4)
            ctx.clip()
        elif axis == "h":
            ctx.translate(off, 0.0)
        else:
            ctx.translate(0.0, off)
        fill_polys(ctx, [poly], col, alpha)
        ctx.restore()
    return slots


def _flip_ease(e):
    """The 'leaving' twin of an arrival ease (out5 -> in5, outback -> in3, ...)."""
    if not isinstance(e, str):
        return e
    if e.startswith("out") and e != "outback" and e != "outelastic":
        return "in" + e[3:]
    if e in ("outback", "outelastic"):
        return "in3"
    return e


# ----------------------------------------------------------------------------- spiral
def _spiral_thetas(r0, r1, turns, facet, seed, kind):
    key = ("spth", round(r0, 2), round(r1, 2), round(turns, 4), round(facet, 2), seed, kind)
    if key in _GEOM:
        return _GEOM[key]
    tmax = 2 * math.pi * turns
    th = [0.0]
    k = 0
    while th[-1] < tmax:
        f = th[-1] / tmax
        r = r0 + (r1 - r0) * f if kind == "arch" else r0 * (r1 / max(r0, 1e-3)) ** f
        step = facet * (0.6 + 0.8 * _h(seed, k, 91)) / max(r, 4.0)
        th.append(th[-1] + min(step, 0.9))
        k += 1
    th[-1] = tmax
    _GEOM[key] = th
    return th


def spiral_pts(c=(540.0, 960.0), r0=12.0, r1=460.0, turns=3.0, width=48.0, taper=(0.15, 1.0),
               rot=0.0, extent=1.0, start=0.0, kind="arch", seed=0, facet=46.0, amp=1.6):
    """Outline of a cut-paper spiral band (Vertigo). r0 -> r1 over `turns` (Archimedean
    'arch' or logarithmic 'log'); band `width` tapered by taper=(inner, outer) factors;
    rot = rotation (deg). extent/start (0..1) reveal part of the band (draw-on): the facet
    positions are fixed along the spiral, so growing it does not make the edges boil."""
    th = _spiral_thetas(r0, r1, turns, facet, seed, kind)
    tmax = th[-1]
    ta, tb = tmax * clamp(start), tmax * clamp(extent)
    if tb - ta < 1e-3:
        return []
    ts = [ta] + [t for t in th if ta < t < tb] + [tb]
    ro = rot * _D2R
    outer, inner = [], []
    for j, t in enumerate(ts):
        f = t / tmax if tmax > 0 else 0
        r = r0 + (r1 - r0) * f if kind == "arch" else r0 * (r1 / max(r0, 1e-3)) ** f
        w = width * lerp(taper[0], taper[1], f) * 0.5
        kk = int(t * 1000)
        ja, jb = amp * _sn(seed, kk, 1), amp * _sn(seed, kk, 2)
        ca, sa = math.cos(t + ro), math.sin(t + ro)
        outer.append((c[0] + (r + w + ja) * ca, c[1] + (r + w + ja) * sa))
        inner.append((c[0] + (r - w + jb) * ca, c[1] + (r - w + jb) * sa))
    return outer + inner[::-1]


def spiral(ctx, c=(540.0, 960.0), r0=12.0, r1=460.0, turns=3.0, width=48.0, color=INK,
           arms=1, rot=0.0, alpha=1.0, seed=0, **kw):
    """Fill a spiral (arms > 1 interleaves copies rotated 360/arms). kw -> spiral_pts."""
    polys = [spiral_pts(c, r0, r1, turns, width, rot=rot + 360.0 * a / arms, seed=seed + a * 13, **kw)
             for a in range(arms)]
    fill_polys(ctx, [p for p in polys if p], color, alpha)


def spiral_path(ctx, c=(540.0, 960.0), r0=12.0, r1=460.0, turns=3.0, width=48.0, arms=1, rot=0.0,
                seed=0, **kw):
    """Add the spiral band(s) to the path (then ctx.clip() to use it as a mask)."""
    for a in range(arms):
        p = spiral_pts(c, r0, r1, turns, width, rot=rot + 360.0 * a / arms, seed=seed + a * 13, **kw)
        if p:
            draw.poly(ctx, p)


# ----------------------------------------------------------------------------- circles
def disc(ctx, c, r, color, seed=0, n=None, alpha=1.0):
    """A flat cut-paper disc."""
    fill_polys(ctx, [ring_pts(c, r, seed, n)], color, alpha)


def ring_band_pts(c, r, width, seed=0, n=None, amp=None, phase=0.0):
    """(outer, inner) contours of a cut-paper annulus: both edges share the same snips and
    wobble together (one strip of paper), with a slight width variation."""
    n = n or int(clamp(round(2 * math.pi * (r + width / 2.0) / 34.0), 18, 120))
    amp = amp if amp is not None else min(2.6, 0.01 * r + 0.5)
    outer, inner = [], []
    for i in range(n):
        th = 2 * math.pi * (i + 0.42 * _sn(seed, i, 1)) / n + phase * _D2R
        rr = r + amp * _sn(seed, i, 2)
        hw = width / 2.0 + min(1.4, 0.05 * width) * _sn(seed, i, 3)
        ca, sa = math.cos(th), math.sin(th)
        outer.append((c[0] + (rr + hw) * ca, c[1] + (rr + hw) * sa))
        ri = max(0.5, rr - hw)
        inner.append((c[0] + ri * ca, c[1] + ri * sa))
    return orient(outer, True), orient(inner, False)


def ring(ctx, c, r, width, color, seed=0, n=None, alpha=1.0):
    """A cut-paper annulus from r - width/2 to r + width/2."""
    o, i = ring_band_pts(c, r, width, seed, n)
    fill_polys(ctx, [o, i], color, alpha)


def rings(ctx, c, radii, width, color, seed=0, alpha=1.0):
    """Concentric cut rings (radii list; width scalar or list)."""
    for k, r in enumerate(radii):
        w = width[k] if isinstance(width, (list, tuple)) else width
        ring(ctx, c, r, w, color, seed + 7 * k, alpha=alpha)


def iris_path(ctx, c, r, seed=0, n=None):
    """Add a cut circle to the path (mask / clip for an iris)."""
    draw.poly(ctx, ring_pts(c, r, seed, n))


def hole(ctx, c, r, color, seed=0, rect=FULL, n=None, alpha=1.0):
    """A flat field with a cut circular hole (iris / helmet port / porthole mask)."""
    x0, y0, x1, y1 = rect
    outer = orient([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], True)
    fill_polys(ctx, [outer, orient(ring_pts(c, r, seed, n), False)], color, alpha)


def binocular_pts(c, r, sep, seed=0, n=None):
    """Outline of two overlapping circles (binocular view): centers c +- sep/2 on x."""
    d = sep / 2.0
    if d >= r:
        return [ring_pts((c[0] - d, c[1]), r, seed, n), ring_pts((c[0] + d, c[1]), r, seed + 1, n)]
    phi = math.acos(d / r)                     # angle of the intersection seen from a center
    m = n or int(clamp(round(2 * math.pi * r / 34.0), 18, 120))
    pts = []
    # right lens outer arc: from -(pi - phi) .. (pi - phi) through 0
    a0, a1 = -(math.pi - phi), (math.pi - phi)
    k = max(6, int(m * (a1 - a0) / (2 * math.pi)))
    for i in range(k + 1):
        a = a0 + (a1 - a0) * i / k
        rr = r + 1.4 * _sn(seed, i, 3)
        pts.append((c[0] + d + rr * math.cos(a), c[1] + rr * math.sin(a)))
    b0, b1 = phi, 2 * math.pi - phi
    for i in range(k + 1):
        a = b0 + (b1 - b0) * i / k
        rr = r + 1.4 * _sn(seed, i, 4)
        pts.append((c[0] - d + rr * math.cos(a), c[1] + rr * math.sin(a)))
    return [pts]


def binoculars(ctx, c, r, sep, color, seed=0, rect=FULL, alpha=1.0):
    """A flat field with a binocular-shaped hole (SHADOW PLAY point of view)."""
    x0, y0, x1, y1 = rect
    outer = orient([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], True)
    holes = [orient(p, False) for p in binocular_pts(c, r, sep, seed)]
    fill_polys(ctx, [outer] + holes, color, alpha)


def aperture(ctx, c, r, opening, color, blades=7, rot=0.0, seed=0, seam=None, seam_w=3.0, alpha=1.0):
    """Camera-iris: a cut disc of radius r with a polygonal opening (opening 0..1 of r) and
    blade seams. The blades turn as it opens."""
    ro = max(0.0, clamp(opening)) * r * 0.98
    turn = rot + (1.0 - clamp(opening)) * 55.0
    V = [(c[0] + ro * math.cos((turn + 360.0 * k / blades) * _D2R),
          c[1] + ro * math.sin((turn + 360.0 * k / blades) * _D2R)) for k in range(blades)]
    outer = orient(ring_pts(c, r, seed), True)
    polys = [outer]
    if ro > 0.5:
        polys.append(orient(V, False))
    fill_polys(ctx, polys, color, alpha)
    if seam is not None and ro > 0.5:
        ctx.save()
        ctx.new_path()
        draw.poly(ctx, outer)
        ctx.clip()
        for k in range(blades):
            a, b = V[k - 1], V[k]
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1.0
            ctx.move_to(*b)
            ctx.line_to(b[0] + dx / L * r * 2, b[1] + dy / L * r * 2)
        _set(ctx, seam, alpha)
        ctx.set_line_width(seam_w)
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        ctx.stroke()
        ctx.restore()


# ----------------------------------------------------------------------------- jagged arm
def jagged_arm_parts(base, tip, width=90.0, jags=4, jag=1.0, claw=0.6, seed=0):
    """Parts of The-Man-with-the-Golden-Arm arm: (arm_band, [hand polys], length, angle).
    Built in a local frame (x from 0 at `base` to L at the wrist `tip`, y across), already
    scissor-cut; jagged_arm() places and animates them."""
    L = math.dist(base, tip)
    key = ("arm", round(L, 1), round(width, 1), jags, round(jag, 3), round(claw, 3), seed)
    if key not in _GEOM:
        w = width
        # zigzag centreline with uneven elbows
        cl = [(0.0, 0.0)]
        for k in range(1, jags):
            x = L * (k + 0.28 * _sn(seed, k, 1)) / jags
            y = jag * w * (0.55 + 0.6 * _h(seed, k, 2)) * (1 if k % 2 else -1)
            cl.append((x, y))
        cl.append((L, 0.0))
        wid = [w * (0.78 + 0.45 * _h(seed, k, 3)) for k in range(len(cl))]
        wid[-1] = w * 0.62
        top, bot = [], []
        for k, (x, y) in enumerate(cl):
            a = cl[max(k - 1, 0)]
            b = cl[min(k + 1, len(cl) - 1)]
            t1 = math.atan2(y - a[1], x - a[0]) if k > 0 else math.atan2(b[1] - y, b[0] - x)
            t2 = math.atan2(b[1] - y, b[0] - x) if k < len(cl) - 1 else t1
            tm = (t1 + t2) / 2.0
            half = abs(((t2 - t1 + math.pi) % (2 * math.pi)) - math.pi) / 2.0
            mit = min(2.2, 1.0 / max(0.25, math.cos(half)))
            nx, ny = -math.sin(tm), math.cos(tm)
            hw = wid[k] / 2.0 * mit
            top.append((x - nx * hw, y - ny * hw))
            bot.append((x + nx * hw, y + ny * hw))
        # saw teeth along both edges (the arm is torn, angular, broken)
        def teeth(edge, sgn, s2):
            out = [edge[0]]
            for k in range(len(edge) - 1):
                a, b = edge[k], edge[k + 1]
                m = 1 + int(_h(seed, s2, k, 4) * 2.2)
                for q in range(m):
                    f0 = (q + 0.15 + 0.25 * _h(seed, s2, k, q, 5)) / (m + 0.3)
                    f1 = f0 + 0.10 + 0.08 * _h(seed, s2, k, q, 6)
                    dx, dy = b[0] - a[0], b[1] - a[1]
                    Lk = math.hypot(dx, dy) or 1.0
                    nx, ny = -dy / Lk * sgn, dx / Lk * sgn
                    d = w * (0.10 + 0.22 * _h(seed, s2, k, q, 7))
                    out.append((a[0] + dx * f0, a[1] + dy * f0))
                    out.append((a[0] + dx * (f0 + f1) / 2 + nx * d, a[1] + dy * (f0 + f1) / 2 + ny * d))
                    out.append((a[0] + dx * f1, a[1] + dy * f1))
                out.append(b)
            return out
        top = teeth(top, -1.0, 1)
        bot = teeth(bot, 1.0, 2)
        band = [(-w * 0.4, top[0][1])] + top + bot[::-1] + [(-w * 0.4, bot[0][1])]
        band = cut(band, seed=seed + 5, amp=1.6, seg=(30.0, 90.0))
        # hand: angular palm + four splayed clawing fingers + thumb
        hw = w * 0.62
        palm = [(L - w * 0.12, -hw * 0.62), (L + w * 0.95, -hw * 1.02), (L + w * 1.25, hw * 0.10),
                (L + w * 1.05, hw * 1.12), (L - w * 0.12, hw * 0.66)]
        hand = [cut(palm, seed + 9, 1.4, (20.0, 50.0))]
        fl = [1.75, 2.05, 1.95, 1.5]
        for f in range(4):
            fa = (-44.0 + 28.0 * f + 6.0 * _sn(seed, f, 8)) * _D2R
            root = (L + w * (0.98 + 0.1 * f), -hw * 0.95 + f * hw * 0.68)
            ln = w * fl[f] * 0.55
            fw = w * (0.20 + 0.03 * _h(seed, f, 9))
            j1 = (root[0] + math.cos(fa) * ln, root[1] + math.sin(fa) * ln)
            fb = fa + claw * (0.9 + 0.35 * _h(seed, f, 10))       # curl toward the palm side
            j2 = (j1[0] + math.cos(fb) * ln * 0.9, j1[1] + math.sin(fb) * ln * 0.9)
            for a, b, ra, rb in ((root, j1, fw, fw * 0.92), (j1, j2, fw * 0.92, fw * 0.45)):
                dx, dy = b[0] - a[0], b[1] - a[1]
                Lk = math.hypot(dx, dy) or 1.0
                nx, ny = -dy / Lk, dx / Lk
                ex, ey = dx / Lk, dy / Lk
                seg = [(a[0] - ex * ra * 0.5 + nx * ra, a[1] - ey * ra * 0.5 + ny * ra),
                       (b[0] + nx * rb, b[1] + ny * rb), (b[0] + ex * rb * 0.9, b[1] + ey * rb * 0.9),
                       (b[0] - nx * rb, b[1] - ny * rb),
                       (a[0] - ex * ra * 0.5 - nx * ra, a[1] - ey * ra * 0.5 - ny * ra)]
                hand.append(orient(seg, True))
        th = [(L + w * 0.25, -hw * 0.55), (L + w * 0.75, -hw * 1.85), (L + w * 1.02, -hw * 1.72),
              (L + w * 0.82, -hw * 0.75)]
        hand.append(orient(cut(th, seed + 11, 1.2, (16.0, 40.0)), True))
        _GEOM[key] = (orient(band, True), [orient(p, True) for p in hand])
    band, hand = _GEOM[key]
    ang = math.degrees(math.atan2(tip[1] - base[1], tip[0] - base[0]))
    return band, hand, L, ang


def jagged_arm(ctx, base, tip, color, width=90.0, grow=1.0, jags=4, jag=1.0, claw=0.6, seed=0, alpha=1.0):
    """The Man with the Golden Arm: a jagged, broken arm from `base` reaching to `tip` and a
    clawing hand. grow (0..1) extends it from the base (the hand rides the growing end)."""
    band, hand, L, ang = jagged_arm_parts(base, tip, width, jags, jag, claw, seed)
    g = clamp(grow)
    if g <= 0:
        return
    ctx.save()
    ctx.translate(*base)
    ctx.rotate(ang * _D2R)
    ctx.save()
    ctx.new_path()
    ctx.rectangle(-width * 2, -width * 6, width * 2 + L * g + 1.0, width * 12)
    ctx.clip()
    fill_polys(ctx, [band], color, alpha)
    ctx.restore()
    ctx.translate(-(1.0 - g) * L, 0.0)
    fill_polys(ctx, hand, color, alpha)
    ctx.restore()


# ----------------------------------------------------------------------------- pointing hand
def capsule_pts(a, b, ra, rb, cap=5):
    """Angular capsule outline from a (radius ra) to b (radius rb) with `cap` facets per
    rounded end (a paper-cut finger, limb or tube)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ang = math.atan2(dy, dx)
    pts = []
    for k in range(cap + 1):
        t = ang + math.pi / 2 - math.pi * k / cap
        pts.append((b[0] + rb * math.cos(t), b[1] + rb * math.sin(t)))
    for k in range(cap + 1):
        t = ang - math.pi / 2 - math.pi * k / cap
        pts.append((a[0] + ra * math.cos(t), a[1] + ra * math.sin(t)))
    return orient(pts, True)


def _hand_parts():
    # manicule pointing +x; units: cuff end x=-100 .. fingertip x=+52; y down
    P = [
        [(-100, -13), (-64, -15), (-64, 15), (-100, 13)],                    # sleeve
        [(-67, -20), (-51, -21), (-50, 21), (-67, 20)],                      # cuff
        [(-53, -15), (-30, -19.5), (-9, -18), (-3, -10), (-5, 17), (-20, 22.5), (-53, 17)],   # back of hand
        capsule_pts((-12, -11.0), (45.5, -10.5), 7.4, 6.2, 4),                # index finger
        capsule_pts((-38, -17.5), (-5, -24.5), 7.0, 5.8, 4),                  # thumb, raised along the top
        capsule_pts((-14, -0.5), (3.5, 0.0), 6.0, 6.0, 4),                    # three curled fingers
        capsule_pts((-14, 8.5), (1.5, 9.0), 5.8, 5.8, 4),
        capsule_pts((-16, 17.0), (-2, 17.5), 5.4, 5.4, 4),
    ]
    return [orient(p, True) for p in P]


def pointing_hand_pts(c, size=300.0, angle=0.0, seed=0, flip=False):
    """A cut-paper pointing hand (manicule, index finger along +x before rotation) as a list
    of parts. c = the knuckles; size = sleeve-to-fingertip length; flip = thumb down."""
    k = size / 152.0
    out = []
    for q, part in enumerate(_hand_parts()):
        pts = [(x * k, (-y if flip else y) * k) for x, y in part]
        if len(part) > 6:            # rounded parts: re-snip the curve, gently
            pts = scissor(pts, seed=seed * 37 + q, sag=0.6 + 0.002 * size, amp=0.3 + 0.0015 * size,
                          max_len=0.1 * size)
        else:
            pts = cut(pts, seed=seed * 37 + q, amp=0.5 + 0.003 * size, seg=(0.08 * size, 0.25 * size))
        out.append(orient(xform(pts, c[0], c[1], angle), True))
    return out


def pointing_hand(ctx, c, size, color, angle=0.0, seed=0, flip=False, alpha=1.0):
    fill_polys(ctx, pointing_hand_pts(c, size, angle, seed, flip), color, alpha)


# ----------------------------------------------------------------------------- cut-out people
def _mirror(right):
    left = [(-x, y) for (x, y) in reversed(right[1:-1])]
    return right + left


_MAN_R = [(0.0, -85.5), (2.9, -85.5), (3.2, -82.4), (10.6, -80.4), (13.7, -78.2),
          (15.0, -72.5), (15.6, -61.5), (16.0, -50.0), (16.4, -46.0), (15.2, -42.6),
          (13.3, -43.0), (12.7, -47.0), (12.3, -57.5), (12.0, -68.6),
          (11.1, -68.8), (10.4, -57.5), (10.9, -44.5), (10.1, -42.2),
          (8.9, -42.0), (8.5, -22.0), (8.0, -3.6), (10.9, -2.4), (11.0, 0.0),
          (1.9, 0.0), (1.8, -3.6), (1.3, -22.0), (0.7, -37.5), (0.0, -38.8)]
_CAPT_R = [(0.0, -85.5), (2.9, -85.5), (3.2, -82.4), (10.0, -80.8), (11.6, -80.8), (11.8, -79.8),
           (14.9, -79.4), (15.2, -72.5), (15.8, -61.5), (16.2, -50.0), (16.6, -46.0), (15.4, -42.6),
           (13.5, -43.0), (12.9, -47.0), (12.5, -57.5), (12.2, -68.6),
           (11.2, -68.8), (10.6, -58.0), (12.6, -32.6), (11.6, -30.8),
           (8.6, -30.6), (8.3, -20.0), (7.9, -3.6), (10.8, -2.4), (10.9, 0.0),
           (1.9, 0.0), (1.8, -3.6), (1.3, -20.0), (0.9, -30.4), (0.0, -31.0)]
_WORK_R = [(0.0, -85.0), (3.3, -85.0), (3.6, -82.0), (12.0, -80.2), (15.2, -77.6),
           (16.6, -71.5), (17.4, -61.0), (17.7, -55.6), (16.7, -55.0), (16.9, -48.5),
           (17.3, -45.0), (15.9, -41.8), (14.1, -42.4), (13.7, -46.5), (13.5, -55.0), (13.1, -68.0),
           (12.1, -68.2), (11.5, -58.0), (11.9, -50.0), (11.3, -48.6),
           (10.3, -48.4), (10.2, -24.0), (10.0, -4.2), (12.9, -2.9), (13.1, 0.0),
           (2.4, 0.0), (2.4, -4.2), (2.0, -24.0), (1.0, -40.0), (0.0, -41.0)]
_WOMAN_R = [(0.0, -86.0), (2.2, -86.0), (2.5, -82.8), (9.2, -80.8), (11.2, -78.6),
            (12.0, -73.0), (12.6, -62.0), (13.0, -52.0), (13.2, -48.6), (12.2, -45.4),
            (10.8, -46.0), (10.4, -50.0), (10.1, -61.0), (9.9, -69.0),
            (9.1, -69.2), (7.4, -60.5), (8.4, -55.5), (14.2, -24.8), (13.0, -23.4),
            (5.4, -23.4), (5.0, -12.0), (4.4, -3.0), (7.0, -1.2), (7.1, 0.0),
            (2.4, 0.0), (2.0, -3.0), (1.6, -12.0), (1.2, -23.2), (0.0, -23.4)]
_CHILD_R = [(0.0, -77.0), (3.0, -77.0), (3.4, -74.6), (10.0, -72.8), (12.2, -70.2),
            (13.2, -63.0), (14.0, -52.0), (14.6, -45.5), (13.4, -42.4), (11.6, -43.0), (11.2, -47.0),
            (10.8, -54.0), (10.6, -60.8),
            (9.7, -61.0), (9.6, -52.0), (12.4, -33.0), (11.4, -31.6),
            (7.8, -31.4), (7.4, -16.0), (7.0, -3.6), (9.8, -2.4), (9.9, 0.0),
            (2.2, 0.0), (2.0, -3.6), (1.6, -16.0), (1.2, -31.0), (0.0, -31.4)]


def _limb(a, b, ra, rb, ext=0.5):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    ex, ey = dx / L, dy / L
    nx, ny = -ey, ex
    return orient([(a[0] - ex * ra * ext + nx * ra, a[1] - ey * ra * ext + ny * ra),
                   (b[0] + ex * rb * ext + nx * rb, b[1] + ey * rb * ext + ny * rb),
                   (b[0] + ex * rb * ext - nx * rb, b[1] + ey * rb * ext - ny * rb),
                   (a[0] - ex * ra * ext - nx * ra, a[1] - ey * ra * ext - ny * ra)], True)


def _oct(c, r, n=7):
    return orient([(c[0] + r * math.cos(2 * math.pi * k / n + 0.3), c[1] + r * math.sin(2 * math.pi * k / n + 0.3))
                   for k in range(n)], True)


def _falling():
    parts = []
    parts.append(("body", draw.ellipse_pts((3.5, -87.0), 6.2, 7.6, n=40, angle=18.0)))
    parts.append(("body", [(-9.5, -77.5), (2.0, -80.0), (12.5, -76.5), (12.0, -63.0), (9.0, -49.0),
                           (-5.5, -47.0), (-9.0, -58.0)]))
    parts.append(("body", [(-0.5, -78.5), (2.5, -79.5), (-8.5, -93.5), (-11.5, -92.0)]))   # flying tie
    parts.append(("body", [(-3.0, -49.5), (-8.0, -60.0), (-19.5, -66.5), (-14.0, -50.0)]))  # coat tails
    parts.append(("body", [(4.0, -49.5), (9.5, -60.0), (17.0, -67.0), (13.0, -49.0)]))
    J = dict(sR=(10.5, -75.5), eR=(21.5, -89.0), hR=(19.0, -104.0),
             sL=(-8.0, -76.0), eL=(-21.0, -84.5), hL=(-30.5, -98.0),
             pR=(5.0, -49.0), kR=(17.0, -31.0), aR=(11.0, -10.0),
             pL=(-3.5, -49.0), kL=(-12.5, -28.0), aL=(-24.5, -15.5))
    for a, b, ra, rb in (("sR", "eR", 2.9, 2.5), ("eR", "hR", 2.5, 2.0), ("sL", "eL", 2.9, 2.5),
                         ("eL", "hL", 2.5, 2.0), ("pR", "kR", 4.2, 3.2), ("kR", "aR", 3.2, 2.4),
                         ("pL", "kL", 4.2, 3.2), ("kL", "aL", 3.2, 2.4)):
        parts.append(("body", _limb(J[a], J[b], ra, rb)))
    for j in ("eR", "eL", "kR", "kL"):
        parts.append(("body", _oct(J[j], 3.0)))
    parts.append(("body", draw.ellipse_pts((20.0, -106.5), 2.6, 3.6, n=16, angle=-20)))      # hands
    parts.append(("body", draw.ellipse_pts((-32.0, -100.0), 2.6, 3.6, n=16, angle=30)))
    parts.append(("body", _limb((10.5, -10.0), (17.5, -6.5), 2.4, 1.8)))                    # shoes
    parts.append(("body", _limb((-24.5, -15.5), (-29.5, -10.0), 2.4, 1.8)))
    return parts


CUTOUT_KINDS = ("man", "captain", "worker", "woman", "child", "hood", "falling")


def cutout_parts(kind="man", seed=0):
    """Cut-paper silhouette of a person in LOCAL units: height 100, feet center at (0, 0),
    head up (y = -100). Returns [(role, polygon)], role 'body' or 'accent' (hat, hood).
    Kinds: man, captain (peaked cap, long coat, epaulettes), worker (flat cap, wrench),
    woman (bob, A-line coat, handbag), child, hood (RED's triangle cloak), falling (Vertigo)."""
    key = ("cutout", kind, seed)
    if key in _GEOM:
        return _GEOM[key]
    K = 6.0                                   # cut at a nominal 600 px tall
    parts = []
    if kind == "man":
        parts = [("body", _mirror(_MAN_R)), ("head", (0.0, -92.6, 6.1, 7.4))]
    elif kind == "captain":
        parts = [("body", _mirror(_CAPT_R)), ("head", (0.0, -92.4, 6.0, 7.2)),
                 ("accent", [(-8.6, -101.6), (-6.0, -103.0), (6.0, -103.0), (8.6, -101.6), (9.0, -100.2),
                             (6.6, -96.4), (-6.6, -96.4), (-9.0, -100.2)]),
                 ("accent", [(-6.6, -96.8), (6.6, -96.8), (6.9, -94.8), (4.2, -93.6), (-4.2, -93.6), (-6.9, -94.8)])]
    elif kind == "worker":
        parts = [("body", _mirror(_WORK_R)), ("head", (0.0, -92.2, 6.4, 7.4)),
                 ("accent", [(-7.4, -96.4), (-6.4, -99.6), (-2.6, -101.4), (3.4, -101.2), (7.2, -99.0),
                             (8.0, -96.6), (12.6, -95.6), (12.4, -94.2), (6.4, -94.6), (-7.0, -95.0)]),
                 ("body", [(14.4, -43.5), (16.2, -43.8), (18.8, -27.0), (17.0, -26.6)]),
                 ("body", [(15.2, -27.8), (20.4, -28.6), (21.6, -22.6), (19.8, -21.4), (19.2, -24.6),
                           (17.0, -24.4), (17.0, -21.6), (15.4, -22.4)])]
    elif kind == "woman":
        parts = [("body", _mirror(_WOMAN_R)), ("head", (0.0, -92.4, 5.1, 6.6)),
                 ("accent", [(-6.8, -94.6), (-6.0, -98.8), (-3.2, -101.0), (0.4, -101.6), (3.6, -101.0),
                             (6.2, -98.6), (6.8, -94.6), (7.4, -87.2), (5.0, -86.6), (4.4, -90.0),
                             (-4.4, -90.0), (-5.0, -86.6), (-7.4, -87.2)]),
                 ("body", [(-16.6, -45.6), (-9.4, -45.6), (-8.8, -36.4), (-17.2, -36.4)]),
                 ("body", [(-14.6, -49.6), (-11.4, -49.6), (-10.6, -45.0), (-15.4, -45.0)])]
    elif kind == "child":
        parts = [("body", _mirror(_CHILD_R)), ("head", (0.0, -87.4, 8.0, 9.4))]
    elif kind == "hood":
        parts = [("accent", [(0.6, -104.0), (6.0, -84.0), (19.5, -27.5), (17.0, -24.6), (-17.0, -24.6),
                             (-19.5, -27.5), (-5.6, -84.0)]),
                 ("body", [(-7.0, -25.5), (-2.4, -25.5), (-2.6, -3.0), (-1.6, 0.0), (-8.6, 0.0), (-7.2, -3.0)]),
                 ("body", [(2.4, -25.5), (7.0, -25.5), (7.2, -3.0), (8.6, 0.0), (1.6, 0.0), (2.6, -3.0)]),
                 ("body", [(16.0, -33.0), (25.5, -33.0), (24.0, -24.0), (17.5, -24.0)]),
                 ("body", [(17.0, -33.0), (18.6, -40.5), (22.8, -40.5), (24.4, -33.0), (23.0, -33.0),
                           (21.8, -38.8), (19.6, -38.8), (18.4, -33.0)])]
    elif kind == "falling":
        parts = _falling()
    else:
        raise ValueError("unknown cut-out kind %r" % kind)
    out = []
    for q, (role, p) in enumerate(parts):
        s = seed * 977 + q * 31 + 5
        if role == "head":
            cx, cy, rx, ry = p
            pts = cut_ellipse((cx * K, cy * K), rx * K, ry * K, seed=s)
            role = "body"
        elif len(p) > 24:
            pts = scissor([(x * K, y * K) for x, y in p], seed=s, sag=1.4, amp=0.9, max_len=40.0)
        else:
            pts = cut([(x * K, y * K) for x, y in p], seed=s, amp=1.3, seg=(16.0, 46.0))
        out.append((role, orient([(x / K, y / K) for x, y in pts], True)))
    _GEOM[key] = out
    return out


def draw_cutout(ctx, kind, foot, height, color, accent=None, seed=0, angle=0.0, flip=False,
                alpha=1.0, sx=1.0):
    """Fill a cut-out person standing at `foot` (world), `height` px tall. accent colors the
    hat / hood parts (default = color). angle rotates about the figure's middle; flip mirrors;
    sx squashes horizontally (e.g. a paper doll turning)."""
    k = height / 100.0
    parts = cutout_parts(kind, seed)
    ctx.save()
    ctx.translate(foot[0], foot[1])
    if angle:
        ctx.translate(0, -50 * k)
        ctx.rotate(angle * _D2R)
        ctx.translate(0, 50 * k)
    ctx.scale(k * (-1.0 if flip else 1.0) * (sx if abs(sx) > 1e-3 else 1e-3), k)
    body = [p for r, p in parts if r != "accent" or accent is None]
    acc = [p for r, p in parts if r == "accent" and accent is not None]
    fill_polys(ctx, body, color, alpha)
    if acc:
        fill_polys(ctx, acc, accent, alpha)
    ctx.restore()


def crowd_layout(n=31, rect=(110.0, 760.0, 970.0, 1460.0), rows=3, kinds=("man", "worker", "man", "worker", "man"),
                 height=None, seed=0, captain=True, depth=0.16):
    """Arrange n cut-outs in rows (back rows smaller and higher). Returns a list of dicts
    {kind, foot, height, seed, flip, index} ordered back to front. With captain=True the
    middle of the front row is a 'captain'."""
    x0, y0, x1, y1 = rect
    per = [n // rows + (1 if r < n % rows else 0) for r in range(rows)]
    hb = height or (y1 - y0) / (0.7 + 0.42 * rows)
    out = []
    idx = 0
    for r in range(rows):
        m = per[r]
        f = r / max(rows - 1, 1)
        sc = 1.0 - depth * (1.0 - f) * (rows - 1)
        fy = lerp(y0 + hb * 0.85, y1, f)
        span = (x1 - x0) * (0.86 + 0.14 * f)
        cx = (x0 + x1) / 2.0 + (0.5 - (r % 2)) * span / max(m, 1) * 0.5
        for j in range(m):
            xx = cx - span / 2.0 + span * (j + 0.5) / m + 6.0 * _sn(seed, r, j, 1)
            hh = hb * sc * (0.92 + 0.12 * _h(seed, r, j, 2))
            kind = kinds[int(_h(seed, r, j, 3) * len(kinds)) % len(kinds)]
            if captain and r == rows - 1 and j == m // 2:
                kind = "captain"
                hh *= 1.04
            out.append(dict(kind=kind, foot=(xx, fy + 4.0 * _sn(seed, r, j, 4)), height=hh,
                            seed=seed * 131 + idx, flip=_h(seed, r, j, 5) < 0.5, index=idx))
            idx += 1
    return out


def draw_crowd(ctx, layout, color, u=1.0, sink=0.0, water=None, accent=None, order="random",
               overlap=0.85, seed=0, ease="outback", alpha=1.0):
    """Draw a crowd from crowd_layout(). u (0..1): figures pop up into place (staggered).
    sink (0..1): figures sink one by one below `water` (world y; default their own feet) and
    are clipped there: 31 men going down with the ship."""
    n = len(layout)
    rk, steps = ranks(n, order, seed)
    for i, d in enumerate(layout):
        p = stagger(u, rk[i], steps, overlap=overlap, ease="linear")
        if p <= 0:
            continue
        s = stagger(sink, rk[n - 1 - i] if order == "random" else rk[i], steps, overlap=overlap, ease="in3")
        if s >= 1:
            continue
        k = _ez(ease, p)
        fx, fy = d["foot"]
        hh = d["height"]
        lvl = water if water is not None else fy + 1.0
        ctx.save()
        if s > 0 or water is not None:
            ctx.new_path()
            ctx.rectangle(-1e5, -1e5, 2e5, 1e5 + lvl)
            ctx.clip()
        # pop up from the feet (scale with overshoot), then sink straight down past the level
        foot = (fx, fy + s * (hh * 1.1 + max(0.0, lvl - fy)))
        draw_cutout(ctx, d["kind"], foot, hh * max(k, 0.001), color, accent, d["seed"],
                    flip=d["flip"], alpha=alpha)
        ctx.restore()


# ----------------------------------------------------------------------------- grid
def grid_cells(rect, rows, cols, gap=12.0):
    """Row-major cell rects (x0, y0, x1, y1) of a rows x cols grid inside rect."""
    x0, y0, x1, y1 = rect
    cw = (x1 - x0 - gap * (cols - 1)) / cols
    ch = (y1 - y0 - gap * (rows - 1)) / rows
    return [(x0 + c * (cw + gap), y0 + r * (ch + gap), x0 + c * (cw + gap) + cw, y0 + r * (ch + gap) + ch)
            for r in range(rows) for c in range(cols)]


def grid(ctx, u, rect=(110.0, 300.0, 970.0, 1480.0), rows=8, cols=5, gap=16.0, color=INK, colors=None,
         order="random", overlap=0.9, reveal="pop", ease=None, seed=0, cut_amp=1.6, cell=None, alpha=1.0):
    """A grid of cut-paper cells with staggered reveals (SHADOW PLAY's 40 windows = 8 x 5).

    colors: None, a list (cycled), or a callable (i, row, col) -> rgb or None (skip cell).
    reveal: 'pop' (scale with overshoot), 'cut' (switch on, like a light), 'wipe' (a blind
    dropping), 'drop' (fall into place), 'flip' (turn about the vertical axis), 'slide'.
    order: as ranks() ('random', 'ltr' (row-major), 'center', ...).
    cell(ctx, i, rect, p): optional callback drawn after each visible cell (contents).
    Returns the cell rects."""
    cells = grid_cells(rect, rows, cols, gap)
    n = len(cells)
    rk, steps = ranks(n, order, seed)
    for i, r in enumerate(cells):
        p = stagger(u, rk[i], steps, overlap=overlap, ease="linear")
        if p <= 0:
            continue
        col = color
        if callable(colors):
            col = colors(i, i // cols, i % cols)
            if col is None:
                continue
        elif colors:
            cl = _cols(colors)
            col = cl[i % len(cl)]
            if col is None:
                continue
        poly = cut_rect(*r, seed=seed * 409 + i, amp=cut_amp, seg=(24.0, 70.0))
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        ctx.save()
        if reveal == "pop":
            s = _ez(ease or "outback", p)
            ctx.translate(cx, cy)
            ctx.scale(max(s, 1e-3), max(s, 1e-3))
            ctx.translate(-cx, -cy)
        elif reveal == "flip":
            s = max(0.02, math.cos((1 - _ez(ease or "outback", p)) * 89 * _D2R))
            ctx.translate(cx, cy)
            ctx.scale(s, 1.0)
            ctx.translate(-cx, -cy)
        elif reveal == "wipe":
            ctx.new_path()
            ctx.rectangle(r[0] - 10, r[1] - 10, r[2] - r[0] + 20, (r[3] - r[1] + 20) * _ez(ease or "out3", p))
            ctx.clip()
        elif reveal == "drop":
            ctx.translate(0, -(1 - _drop_ease(p)) * (r[3] - r[1]) * 3.0)
        elif reveal == "slide":
            ctx.translate(-(1 - _ez(ease or "out5", p)) * 1300.0, 0)
        fill_polys(ctx, [poly], col, alpha)
        if cell is not None:
            cell(ctx, i, r, p)
        ctx.restore()
    return cells


# ----------------------------------------------------------------------------- triangles
def triangle_pts(base_c, size, angle=0.0, seed=0, ratio=0.78):
    """Isosceles cut-paper triangle standing on base center base_c, `size` tall, apex up
    (angle rotates about the base center). ratio = base width / height."""
    b = size * ratio / 2.0
    pts = [(base_c[0], base_c[1] - size), (base_c[0] + b, base_c[1]), (base_c[0] - b, base_c[1])]
    pts = cut(pts, seed=seed, amp=1.0 + 0.006 * size, seg=(18.0, 60.0))
    return orient(xform(pts, 0, 0, angle, 1.0, None, base_c), True)


def triangles(ctx, u, rect=(80.0, 300.0, 1000.0, 1500.0), n=26, size=(70.0, 210.0), color=INK, accent=None,
              accent_frac=0.12, mode="scatter", order="random", overlap=0.85, ease="outback", seed=0,
              cols=6, gap=0.14, density=1.0, alpha=1.0):
    """Triangle field (RED). mode 'scatter': n triangles on a jittered lattice, sizes in
    `size`; 'grid': a tessellation of up/down triangles in `cols` columns, each inset by
    `gap` (fraction) with ~`density` of the cells filled. Each pops in (staggered).
    accent (e.g. RED) colors ~accent_frac of them. Returns [(anchor, size, angle, is_accent)]."""
    x0, y0, x1, y1 = rect
    items = []
    if mode == "grid":
        tw = (x1 - x0) / cols
        th = tw * 0.9
        nr = max(1, int((y1 - y0) // th))
        for r in range(nr):
            for c in range(-1, cols * 2 + 1):
                up = (c + r) % 2 == 0
                bx = x0 + tw * c / 2.0
                if up:
                    tri = [(bx, y0 + th * r), (bx + tw / 2, y0 + th * (r + 1)), (bx - tw / 2, y0 + th * (r + 1))]
                else:
                    tri = [(bx - tw / 2, y0 + th * r), (bx + tw / 2, y0 + th * r), (bx, y0 + th * (r + 1))]
                if _h(seed, r, c, 7) > density:
                    continue
                items.append((tri, th, 0.0, None))
    else:
        cols_s = max(1, int(round(math.sqrt(n * (x1 - x0) / (y1 - y0)))))
        rows_s = int(math.ceil(n / cols_s))
        k = 0
        for r in range(rows_s):
            for c in range(cols_s):
                if k >= n:
                    break
                sz = lerp(size[0], size[1], _h(seed, k, 1) ** 1.5)
                bx = x0 + (c + 0.5 + 0.35 * _sn(seed, k, 2)) * (x1 - x0) / cols_s
                by = y0 + (r + 0.9 + 0.25 * _sn(seed, k, 3)) * (y1 - y0) / rows_s
                items.append(((bx, by), sz, 5.0 * _sn(seed, k, 4), 0.78))
                k += 1
        items.sort(key=lambda it: it[0][1])
    m = len(items)
    rk, steps = ranks(m, order, seed)
    out = []
    for i, (bc, sz, ang, ratio) in enumerate(items):
        is_acc = accent is not None and _h(seed, i, 5) < accent_frac
        p = stagger(u, rk[i], steps, overlap=overlap, ease="linear")
        if ratio is None:                       # grid cell: bc is the triangle itself
            cpt = centroid(bc)
            k = 1.0 - gap
            pts = cut([(cpt[0] + (x - cpt[0]) * k, cpt[1] + (y - cpt[1]) * k) for x, y in bc],
                      seed=seed * 53 + i, amp=1.0 + 0.004 * sz, seg=(18.0, 60.0))
            pts = orient(pts, True)
            pivot = cpt
            out.append((cpt, sz, ang, is_acc))
        else:
            pts = triangle_pts(bc, sz, ang, seed * 53 + i, ratio)
            pivot = bc
            out.append((bc, sz, ang, is_acc))
        if p <= 0:
            continue
        s = _ez(ease, p)
        if s != 1.0:
            pts = xform(pts, 0, 0, 0, max(s, 1e-3), None, pivot)
        fill_polys(ctx, [pts], accent if is_acc else color, alpha)
    return out


# ----------------------------------------------------------------------------- panels
def panels(ctx, u, rect=FULL, n=3, axis="h", gutter=14.0, colors=(INK,), frm="alt", overlap=0.6,
           ease="out5", seed=0, content=None, cut_amp=1.6, sizes=None, alpha=1.0):
    """Split-screen panels sliding in (staggered) with paper gutters between them.
    axis 'h': horizontal panels stacked vertically (slide in from the sides); 'v': columns
    (slide in from top/bottom). content(ctx, i, rect, p): draws inside panel i, clipped to it
    and moving with it. Returns the panel rects."""
    rects = bar_rects(rect, n, axis, sizes or [1.0] * n, gutter, seed)
    rk, steps = ranks(n, "ltr", seed)
    span = (rect[2] - rect[0]) if axis == "h" else (rect[3] - rect[1])
    for i, r in enumerate(rects):
        p = stagger(u, rk[i], steps, overlap=overlap, ease=ease)
        if p <= 0:
            continue
        side = (-1.0 if i % 2 == 0 else 1.0) if frm == "alt" else (1.0 if frm == "end" else -1.0)
        off = side * (span + 200.0) * (1.0 - p)
        ctx.save()
        ctx.translate(off if axis == "h" else 0.0, 0.0 if axis == "h" else off)
        poly = cut_rect(*r, seed=seed * 211 + i, amp=cut_amp)
        cl = _cols(colors)
        col = cl[i % len(cl)]
        if col is not None:
            fill_polys(ctx, [poly], col, alpha)
        if content is not None:
            ctx.new_path()
            draw.poly(ctx, poly)
            ctx.clip()
            content(ctx, i, r, p)
        ctx.restore()
    return rects


# ----------------------------------------------------------------------------- slash
def slash_pts(p0, p1, width=26.0, u=1.0, tail=0.0, belly=0.42, seed=0):
    """A knife slash: a sharp lens-shaped sliver along p0 -> p1. The visible part runs from
    `tail` to `u` (fractions of the length), so animate u (and later tail) to cut across."""
    a, b = clamp(tail), clamp(u)
    if b - a < 1e-3:
        return []
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1.0
    ex, ey = dx / L, dy / L
    nx, ny = -ey, ex
    m = 14
    top, bot = [], []
    for k in range(m + 1):
        f = k / m
        s = lerp(a, b, f)
        # lens profile over the visible part, fattest at `belly`
        g = f / belly if f < belly else (1 - f) / (1 - belly)
        w = width * 0.5 * (max(g, 0.0) ** 0.75) * (1 + 0.12 * _sn(seed, k, 1))
        x, y = p0[0] + dx * s, p0[1] + dy * s
        top.append((x + nx * w, y + ny * w))
        bot.append((x - nx * w * 0.8, y - ny * w * 0.8))
    return orient(top + bot[::-1][1:-1], True)


def slash(ctx, p0, p1, color=RED, width=26.0, u=1.0, tail=0.0, seed=0, alpha=1.0):
    pts = slash_pts(p0, p1, width, u, tail, seed=seed)
    if pts:
        fill_polys(ctx, [pts], color, alpha)


# ----------------------------------------------------------------------------- heartbeat
def heartbeat(ctx, c, t, color=RED, bpm=62.0, r0=70.0, r1=820.0, width=26.0, life=1.9, core=True,
              dub=0.26, seed=0, alpha=1.0):
    """Concentric heartbeat circles: each beat (lub + dub) sends a cut ring outward, thinning
    as it goes; the core disc thumps (scale kick with overshoot). Pure function of t."""
    beat = 60.0 / bpm
    k0 = int(math.floor((t - life) / beat)) - 1
    k1 = int(math.floor(t / beat))
    for k in range(k0, k1 + 1):
        for j, off in enumerate((0.0, dub)):
            t0 = k * beat + off
            a = (t - t0) / life
            if not (0.0 <= a <= 0.93):          # rings snap off at the end (no hairlines)
                continue
            r = lerp(r0 * 1.15, r1, _ez("out3", a))
            w = width * max(0.3, (1.0 - a) ** 1.3) * (1.0 if j == 0 else 0.6)
            ring(ctx, c, r, w, color, seed=seed + k * 7 + j, n=72, alpha=alpha)
    if core:
        ph = (t % beat)
        kick = max(_kick(ph), 0.6 * _kick(ph - dub))
        disc(ctx, c, r0 * (1.0 + 0.16 * kick), color, seed=seed + 1, n=40, alpha=alpha)


def _kick(dt):
    if dt < 0:
        return 0.0
    if dt < 0.06:
        return dt / 0.06
    return math.exp(-(dt - 0.06) * 9.0)


# ----------------------------------------------------------------------------- loop arrow
def loop_pts(c, r, width=40.0, u=1.0, start=-90.0, sweep=318.0, head=2.1, seed=0):
    """Circular arrow (a loop): an arc band of radius r sweeping sweep*u deg from `start`
    (clockwise on screen), ending in an arrowhead. Facets are fixed along the circle."""
    sw = sweep * clamp(u)
    if sw < 1.0:
        return []
    hl = head * width * 0.95                        # arrowhead length along the arc (px)
    ha = min(sw * 0.6, hl / r / _D2R)
    a0, a1 = start, start + sw - ha
    step = 4.0
    angs = [a0]
    k = 0
    while angs[-1] + step < a1:
        k += 1
        angs.append(start + k * step + 1.4 * _sn(seed, k, 1))
    angs.append(a1)
    ro, ri = r + width / 2.0, r - width / 2.0
    outer = [(c[0] + (ro + 0.9 * _sn(seed, int(a * 10), 2)) * math.cos(a * _D2R),
              c[1] + (ro + 0.9 * _sn(seed, int(a * 10), 2)) * math.sin(a * _D2R)) for a in angs]
    inner = [(c[0] + (ri + 0.9 * _sn(seed, int(a * 10), 3)) * math.cos(a * _D2R),
              c[1] + (ri + 0.9 * _sn(seed, int(a * 10), 3)) * math.sin(a * _D2R)) for a in angs]
    hw = head * width / 2.0
    ae = (start + sw) * _D2R
    ab = a1 * _D2R
    head_pts = [(c[0] + (r + hw) * math.cos(ab), c[1] + (r + hw) * math.sin(ab)),
                (c[0] + r * math.cos(ae), c[1] + r * math.sin(ae)),
                (c[0] + (r - hw) * math.cos(ab), c[1] + (r - hw) * math.sin(ab))]
    return orient(outer + head_pts + inner[::-1], True)


def loop_arrow(ctx, c, r, color, width=40.0, u=1.0, rot=0.0, sweep=318.0, head=2.1, seed=0, alpha=1.0):
    pts = loop_pts(c, r, width, u, -90.0 + rot, sweep, head, seed)
    if pts:
        fill_polys(ctx, [pts], color, alpha)


# ----------------------------------------------------------------------------- lines
def line_pts(pts, width=18.0, u=1.0, seed=0, taper=(1.0, 1.0), amp=1.0):
    """Cut-paper band along a polyline (the red air hose, the black path), drawn on to u.
    The band is resampled at fixed arc positions, so drawing it on does not boil."""
    if len(pts) < 2 or u <= 0:
        return []
    seglen = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(seglen) or 1.0
    step = 26.0
    m = max(2, int(total / step))
    show = total * clamp(u)
    samples = []
    acc, i = 0.0, 0
    for k in range(m + 1):
        s = min(total, k * total / m + (0.3 * step * _sn(seed, k, 1) if 0 < k < m else 0.0))
        if s > show:
            break
        samples.append(s)
    if not samples or samples[-1] < show:
        samples.append(show)
    out = []
    for s in samples:
        while i < len(seglen) - 1 and acc + seglen[i] < s:
            acc += seglen[i]
            i += 1
        f = (s - acc) / (seglen[i] or 1.0)
        a, b = pts[i], pts[i + 1]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    if len(out) < 2:
        return []
    widths = [width * lerp(taper[0], taper[1], s / total) + amp * _sn(seed, k, 2) for k, s in enumerate(samples)]
    return orient(draw.ribbon(out, widths), True)


def line_band(ctx, pts, color, width=18.0, u=1.0, seed=0, taper=(1.0, 1.0), alpha=1.0):
    band = line_pts(pts, width, u, seed, taper)
    if band:
        fill_polys(ctx, [band], color, alpha)


# ----------------------------------------------------------------------------- paper fields
def paper_field(ctx, color, rect=None, seed=0, cut_amp=2.0, alpha=1.0):
    """A flat field of paper: the whole clip (rect=None) or a cut-edged rectangle."""
    if rect is None:
        _set(ctx, color, alpha)
        ctx.paint()
        return
    fill_polys(ctx, [cut_rect(*rect, seed=seed, amp=cut_amp)], color, alpha)


def edge_pts(y, x0=-40.0, x1=W + 40.0, seed=0, amp=4.0, seg=(40.0, 140.0), tilt=0.0):
    """A long hand-cut horizontal edge at height y (a few straight snips, slightly off level)."""
    pts = []
    x = x0
    k = 0
    while x < x1:
        pts.append((x, y + amp * _sn(seed, k, 1) + tilt * (x - (x0 + x1) / 2) / 1000.0))
        x += seg[0] + (seg[1] - seg[0]) * _h(seed, k, 2)
        k += 1
    pts.append((x1, y + amp * _sn(seed, k, 1) + tilt * (x1 - (x0 + x1) / 2) / 1000.0))
    return pts


def tide(ctx, level, color, seed=0, amp=4.0, above=False, tilt=0.0, alpha=1.0):
    """A paper field below (or above) a cut horizontal edge at world y = level: rising
    darkness, a waterline, a horizon. Move `level` to animate (the edge keeps its cuts)."""
    e = edge_pts(level, seed=seed, amp=amp, tilt=tilt)
    far = -4000.0 if above else H + 4000.0
    pts = e + [(e[-1][0], far), (e[0][0], far)]
    fill_polys(ctx, [orient(pts, True)], color, alpha)


_TEX = {}


def _texture_surface(seed, feature, size=256):
    key = (seed, feature, size)
    if key not in _TEX:
        T = noise_grid(size, size, feature=feature, seed=seed, beta=1.6, detail=5.0)
        T = np.clip((T - 0.35) / 0.65, 0, 1)
        a = (T * 255).astype(np.uint8)
        stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_A8, size)
        buf = np.zeros((size, stride), np.uint8)
        buf[:, :size] = a
        surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_A8, size, size, stride)
        _TEX[key] = (surf, buf)
    return _TEX[key][0]


def texture(ctx, amount=0.10, seed=3, feature=24.0, color=(0, 0, 0), scale=1.0):
    """Mottle the current clip like ink printed on paper (multiply-ish darkening through a
    tileable noise mask). Use small amounts (0.05..0.15) over flat fields; f.post['paper']
    already adds the fibres."""
    if amount <= 0:
        return
    pat = cairo.SurfacePattern(_texture_surface(seed, feature))
    pat.set_extend(cairo.EXTEND_REPEAT)
    pat.set_filter(cairo.FILTER_GOOD)
    m = cairo.Matrix(xx=1.0 / scale, yy=1.0 / scale)
    pat.set_matrix(m)
    _set(ctx, color, amount)
    ctx.mask(pat)


# ============================================================================ morphing
def morph_outline(a, b, u, n=180, align="best"):
    """Morph outline a -> b (u 0..1). Both are resampled to n points by arc length, made
    clockwise, and b's start is rotated to match a's: align='best' (least squares over all
    cyclic shifts), 'left' (both start at their leftmost point) or 'top'."""
    A = np.array(draw.resample(orient(a, True), n), np.float64)
    B = np.array(draw.resample(orient(b, True), n), np.float64)
    if align in ("left", "top"):
        ax = 0 if align == "left" else 1
        A = np.roll(A, -int(np.argmin(A[:, ax])), axis=0)
        B = np.roll(B, -int(np.argmin(B[:, ax])), axis=0)
    else:
        ca, cb = A.mean(0), B.mean(0)
        A0, B0 = A - ca, B - cb
        best, bk = None, 0
        for k in range(n):
            d = float(((A0 - np.roll(B0, -k, axis=0)) ** 2).sum())
            if best is None or d < best:
                best, bk = d, k
        B = np.roll(B, -bk, axis=0)
    k = clamp(u)
    M = A * (1 - k) + B * k
    return [tuple(p) for p in M]


def outline_of(polys, res=2.0, eps=0.6):
    """Single outer outline (list of points) of a multi-part shape (the union of polys), by
    rasterizing at 1/res px and tracing the largest external contour. Use it to morph
    composite cut-outs (hands, figures, letters) with morph_outline()."""
    import cv2
    x0, y0, x1, y1 = bbox(polys)
    m = 4
    w, h = int((x1 - x0) / res) + 2 * m, int((y1 - y0) / res) + 2 * m
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_A8, w)
    buf = np.zeros((h, stride), np.uint8)
    surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_A8, w, h, stride)
    c = cairo.Context(surf)
    c.translate(m - x0 / res, m - y0 / res)
    c.scale(1.0 / res, 1.0 / res)
    path_polys(c, polys)
    c.fill()
    surf.flush()
    mask = (buf[:, :w] > 127).astype(np.uint8)
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        return []
    cont = max(cs, key=cv2.contourArea)
    cont = cv2.approxPolyDP(cont, eps, True)
    return orient([((float(p[0][0]) + 0.5 - m) * res + x0, (float(p[0][1]) + 0.5 - m) * res + y0) for p in cont], True)


def curl_pts(c, length, width, u, rot=0.0, seed=0, n=160, up=True):
    """A straight band `length` px long that curls into a ring (u=0 a line, u=1 a closed
    ring of circumference `length`), kept centered on c. Returns a list of contours (one
    band, or outer + inner ring once closed; both built from the same samples so the cut
    edge does not pop). The SALVAGE red line -> helmet port / moon / safe dial."""
    k = clamp(u)
    L = float(length)
    kap = max(k, 1e-6) * 2 * math.pi / L
    R = 1.0 / kap
    pts = []
    for j in range(n + 1):
        s = -L / 2.0 + L * j / n
        if k < 1e-6:
            pts.append((s, 0.0))
        else:
            th = s * kap
            pts.append((R * math.sin(th), (R - R * math.cos(th)) * (-1.0 if up else 1.0)))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
    if k > 0.5:
        # once it closes up, keep the would-be ring centre on c (no drift at the end)
        cy = lerp(cy, -R if up else R, smooth01((k - 0.5) / 0.5))
    pts = [(x - cx, y - cy) for x, y in pts]
    widths = [width + 0.8 * _sn(seed, j, 3) for j in range(n + 1)]
    if k >= 0.999:
        m = n                                   # closed: drop the duplicate end, wrap normals
        outer, inner = [], []
        for j in range(m):
            a, b = pts[(j - 1) % m], pts[(j + 1) % m]
            tx, ty = b[0] - a[0], b[1] - a[1]
            tl = math.hypot(tx, ty) or 1.0
            nx, ny = -ty / tl, tx / tl
            hw = widths[j] / 2.0
            outer.append((pts[j][0] + nx * hw, pts[j][1] + ny * hw))
            inner.append((pts[j][0] - nx * hw, pts[j][1] - ny * hw))
        return [orient(xform(outer, c[0], c[1], rot), True), orient(xform(inner, c[0], c[1], rot), False)]
    band = draw.ribbon(pts, widths)
    band = xform(band, c[0], c[1], rot)
    return [orient(band, True)]


def smooth01(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


# ============================================================================ posterize / scene
_POSTER_TONES = {
    # dark, mid, light tones (2-3 flat inks) and default luminance thresholds
    "salvage": dict(tones=[(0.006, 0.016, 0.022), (0.07, 0.25, 0.29), PAPER], thr=(0.07, 0.24)),
    "shadowplay": dict(tones=[(0.010, 0.010, 0.016), (0.15, 0.16, 0.21), (1.0, 0.76, 0.45)], thr=(0.06, 0.30)),
    "red": dict(tones=[(0.012, 0.012, 0.012), (0.62, 0.62, 0.62), PAPER], thr=(0.22, 0.66)),
}


def poster_tones(pal):
    """(tones, thresholds) for a palette (object or name)."""
    name = pal.name if isinstance(pal, Palette) else str(pal)
    d = _POSTER_TONES.get(name, dict(tones=[INK, (0.45, 0.45, 0.44), PAPER], thr=(0.18, 0.55)))
    return list(d["tones"]), tuple(d["thr"])


def poster(pal, amount=1.0, tones=3, thr=None, light=None, keep_red=True):
    """A dict for f.post['poster']: flatten the frame into 2-3 flat inks (Bass print), keeping
    saturated reds. tones=2 drops the mid tone. light overrides the light tone (e.g. PAPER).
    thr overrides the luminance thresholds (dark/mid, mid/light)."""
    T, th = poster_tones(pal)
    th = thr or th
    if light is not None:
        T[2] = light
    if tones == 2:
        levels = [(th[0] + (th[1] - th[0]) * 0.5, T[0]), (99.0, T[2])]
    else:
        levels = [(th[0], T[0]), (th[1], T[1]), (99.0, T[2])]
    return dict(amount=amount, levels=levels, keep_red=keep_red)


POSTER = {name: poster(p) for name, p in PALETTES.items()}


def bass_scene(f, field=PAPER, paper=0.75, grain=None, vignette=0.16, bloom=0.0, flicker=0.006,
               poster_amount=0.0, glow=None, mottle=0.0):
    """Set a Frame up as a Saul Bass graphic: flat paper field, paper fibres, light grain, a
    whisper of vignette, no bloom. poster_amount > 0 also flattens what gets drawn (palette
    preset). mottle > 0 adds printed-ink unevenness to the field. Draw the motifs after."""
    f.fill(field)
    f.post["paper"] = paper
    f.post["vignette"] = vignette
    f.post["bloom"] = bloom
    f.post["flicker"] = flicker
    f.post["grain"] = min(f.pal.grain, 0.045) if grain is None else grain
    if glow is not None:
        f.post["glow"] = glow
    if poster_amount > 0:
        f.post["poster"] = poster(f.pal, poster_amount)
    if mottle > 0:
        with f.screen() as c:
            texture(c, mottle, seed=5, feature=40.0)
    return f
