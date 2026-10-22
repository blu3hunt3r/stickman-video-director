"""RED sets: the giant web as DATA, and the fire that races along it (S06-S09).

A Web is a list of Strands: polylines in world coords, each with a kind and a width. Strands
that touch or cross are linked (junctions), so the web is a graph: fire lit anywhere spreads
along the silk and jumps at every junction. A burn is precomputed once per ignition list
(Dijkstra over the vertex graph), so every frame is a cheap, exact function of t.

    web = CLEARING_SET.web                     # or: w = Web(); w.add(pts, kind, width); w.finalize()
    burn = web.ignite([(x, y, t0)])            # cached per argument set
    web.draw(f, t, mood, burn=burn, lights=[(x, y, radius, strength)])

    burn.arrival[i]          time the fire reaches vertex i (inf: never)
    burn.state(t)            per vertex: 0 intact, 1 burning, 2 charred, 3 gone
    burn.progress(t)         (n_strands,) fraction of each strand's length the fire has passed
    burn.fronts(t)           [(x, y)] where the fire fronts are now (sparks, sound cues)
    burn.flames(t)           [(x, y, heat)] burning points (lights, smoke)
    burn.light_sources(t)    up to n (x, y, radius, strength): the firelight
    burn.heat(t)             px of silk burning now (drive the scene's firelight with it)
    burn.release_time(sid)   when strand sid has burnt through (what hangs from it falls)
    burn.t_done              when the last silk stops burning

    web.draw_remnants(f, t, mood)    S09: charred threads left hanging after the fire

Strand kinds: frame, radial, spiral (orb webs), wrap (the cocoon over the cottage), veil
(across the door and window), tangle, anchor (guy lines to trees, ground and canopy), thread
(single hanging threads: Grandmother's line, hood threads).
"""
import heapq
import math

import numpy as np

from engine import draw
from .sets_common import get_mood, mix, SNOW, glow, plane, rnd, srnd, soft_layer

try:
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import dijkstra as _sp_dijkstra
except Exception:          # pragma: no cover - scipy is optional
    _sp_dijkstra = None

KINDS = ("frame", "radial", "spiral", "wrap", "veil", "tangle", "anchor", "thread")


def _vhash(k, s=0.0):
    """Vectorized hash -> [0, 1)."""
    v = np.sin(np.asarray(k, dtype=float) * 12.9898 + s * 78.233) * 43758.5453
    return v - np.floor(v)


class Strand:
    """One silk line: pts (n, 2) world coords, kind (see KINDS), width (px at zoom 1), tag."""
    __slots__ = ("id", "pts", "kind", "width", "v0", "v1", "length", "tag")

    def __init__(self, sid, pts, kind, width, tag=None):
        self.id = sid
        self.pts = np.asarray(pts, dtype=float)
        self.kind = kind
        self.width = float(width)
        self.tag = tag
        d = np.hypot(*np.diff(self.pts, axis=0).T) if len(self.pts) > 1 else np.zeros(0)
        self.length = float(d.sum())
        self.v0 = self.v1 = 0           # vertex index range in the web's flat arrays

    def point_at(self, u):
        """Point at fraction u (0..1) of the strand's length."""
        seg = np.hypot(*np.diff(self.pts, axis=0).T)
        c = np.concatenate([[0.0], np.cumsum(seg)])
        s = float(np.clip(u, 0, 1)) * c[-1]
        i = min(max(int(np.searchsorted(c, s, side="right")) - 1, 0), len(seg) - 1)
        k = (s - c[i]) / max(seg[i], 1e-9)
        return tuple((self.pts[i] + (self.pts[i + 1] - self.pts[i]) * k).tolist())

    def __repr__(self):
        return f"Strand({self.id}, {self.kind}, n={len(self.pts)}, L={self.length:.0f}, tag={self.tag})"


def densify(pts, step=26.0):
    """Resample a polyline so no segment is longer than `step` (the fire's resolution).
    Original vertices are kept, so strands built through shared points join exactly."""
    out = [tuple(pts[0])]
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(math.ceil(L / step)))
        for i in range(1, n + 1):
            u = i / n
            out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    return out


def sag_line(a, b, sag=0.04, step=26.0):
    """Silk from a to b hanging under gravity (parabolic sag = sag * length, downward)."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(2, int(L / step) + 1)
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n + 4 * sag * L * (i / n) * (1 - i / n))
            for i in range(n + 1)]


class Web:
    """The web graph. Build with add(...) then finalize(); then ignite / draw."""

    def __init__(self, junction_tol=7.0):
        self.strands = []
        self.tol = junction_tol
        self._burns = {}
        self._cache = {}
        self.final = False
        self.anchors = {}            # named points (filled by the set that builds the web)

    def add(self, pts, kind="tangle", width=2.0, tag=None, step=26.0):
        """Add a strand through pts (densified to `step`). Returns the Strand."""
        assert not self.final, "web already finalized"
        assert kind in KINDS, kind
        pts = densify(pts, step)
        if len(pts) < 2:
            return None
        s = Strand(len(self.strands), pts, kind, width, tag)
        self.strands.append(s)
        return s

    def by_kind(self, kind):
        return [s for s in self.strands if s.kind == kind]

    def by_tag(self, tag):
        return [s for s in self.strands if s.tag == tag]

    # ------------------------------------------------------------ graph
    def finalize(self):
        P, owner = [], []
        for s in self.strands:
            s.v0 = len(P)
            P.extend(map(tuple, s.pts))
            owner.extend([s.id] * len(s.pts))
            s.v1 = len(P)
        self.P = np.asarray(P, dtype=float)
        self.owner = np.asarray(owner, dtype=np.int32)
        self.V = len(P)
        # segments: start vertex index, width, kind index, strand id
        self.sa = np.concatenate([np.arange(s.v0, s.v1 - 1) for s in self.strands]).astype(np.int64)
        self.sid = self.owner[self.sa]
        self.sw = np.array([self.strands[i].width for i in self.sid])
        self.sk = np.array([KINDS.index(self.strands[i].kind) for i in self.sid], dtype=np.int16)
        self.vk = np.array([KINDS.index(self.strands[i].kind) for i in self.owner], dtype=np.int16)
        seg_len = np.hypot(*(self.P[self.sa + 1] - self.P[self.sa]).T)
        jr, jc, jw = self._near_pairs()        # shared anchor points
        cr, cc, cw = self._crossings()         # strands crossing each other
        r = np.concatenate([self.sa, jr, cr]).astype(np.int64)
        c = np.concatenate([self.sa + 1, jc, cc]).astype(np.int64)
        ww = np.concatenate([seg_len, jw, cw]).astype(float)
        self._edges = (r, c, np.maximum(ww, 1e-3))
        self.n_junctions = len(jr) + len(cr)
        self.final = True
        return self

    def _near_pairs(self):
        cell = self.tol
        keys = np.floor(self.P / cell).astype(np.int64)
        grid = {}
        for i, (kx, ky) in enumerate(keys.tolist()):
            grid.setdefault((kx, ky), []).append(i)
        jr, jc, jw = [], [], []
        P, own = self.P, self.owner
        for (kx, ky), members in grid.items():
            cand = []
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    cand.extend(grid.get((kx + dx, ky + dy), ()))
            for i in members:
                for j in cand:
                    if j <= i or own[i] == own[j]:
                        continue
                    d = math.hypot(P[i, 0] - P[j, 0], P[i, 1] - P[j, 1])
                    if d <= self.tol:
                        jr.append(i)
                        jc.append(j)
                        jw.append(d + 1.0)
        return np.array(jr, dtype=np.int64), np.array(jc, dtype=np.int64), np.array(jw, dtype=float)

    def _crossings(self, cell=64.0):
        """Crossing segments of different strands: link their nearest vertices."""
        P, sa = self.P, self.sa
        a0, a1 = P[sa], P[sa + 1]
        lo = np.floor(np.minimum(a0, a1) / cell).astype(np.int64)
        hi = np.floor(np.maximum(a0, a1) / cell).astype(np.int64)
        grid = {}
        for i, (x0, y0, x1, y1) in enumerate(np.concatenate([lo, hi], axis=1).tolist()):
            for gx in range(x0, x1 + 1):
                for gy in range(y0, y1 + 1):
                    grid.setdefault((gx, gy), []).append(i)
        pa, pb = [], []
        for m in grid.values():
            if len(m) < 2:
                continue
            mm = np.asarray(m)
            ii, jj = np.triu_indices(len(mm), 1)
            A, B = mm[ii], mm[jj]
            keep = self.sid[A] != self.sid[B]
            pa.append(A[keep])
            pb.append(B[keep])
        empty = (np.zeros(0, np.int64), np.zeros(0, np.int64), np.zeros(0))
        if not pa:
            return empty
        A, B = np.concatenate(pa), np.concatenate(pb)
        if len(A) == 0:
            return empty
        key = np.minimum(A, B) * len(sa) + np.maximum(A, B)
        _, u = np.unique(key, return_index=True)
        A, B = A[u], B[u]
        p, r = a0[A], a1[A] - a0[A]
        q, s = a0[B], a1[B] - a0[B]
        den = r[:, 0] * s[:, 1] - r[:, 1] * s[:, 0]
        ok = np.abs(den) > 1e-9
        den = np.where(ok, den, 1.0)
        qp = q - p
        tt = (qp[:, 0] * s[:, 1] - qp[:, 1] * s[:, 0]) / den
        uu = (qp[:, 0] * r[:, 1] - qp[:, 1] * r[:, 0]) / den
        hit = ok & (tt >= 0) & (tt <= 1) & (uu >= 0) & (uu <= 1)
        ia = sa[A[hit]] + (tt[hit] > 0.5)
        ib = sa[B[hit]] + (uu[hit] > 0.5)
        w = np.hypot(*(P[ia] - P[ib]).T) + 1.0
        return ia.astype(np.int64), ib.astype(np.int64), w

    def nearest(self, p, kinds=None):
        """Nearest vertex to p: (strand, vertex_index, (x, y), distance)."""
        d = np.hypot(self.P[:, 0] - p[0], self.P[:, 1] - p[1])
        if kinds:
            d = np.where(np.isin(self.vk, [KINDS.index(k) for k in kinds]), d, np.inf)
        i = int(np.argmin(d))
        return self.strands[int(self.owner[i])], i, tuple(self.P[i].tolist()), float(d[i])

    def bounds(self):
        return (float(self.P[:, 0].min()), float(self.P[:, 1].min()), float(self.P[:, 0].max()),
                float(self.P[:, 1].max()))

    # ------------------------------------------------------------ fire
    def ignite(self, ignitions, speed=560.0, burn_time=0.75, char_time=2.6, radius=40.0, jitter=0.25, seed=0):
        """Precompute a burn. ignitions: [(x, y, t0), ...]. The fire travels `speed` px/s along
        the silk (each strand varies by +-jitter; anchor lines are faster), lights every vertex
        within `radius` of an ignition point, keeps silk in flame for `burn_time` s, leaves a
        charred thread for `char_time` s, then the silk is gone. Cached by arguments."""
        key = (tuple((round(a, 2), round(b, 2), round(c, 4)) for a, b, c in ignitions), speed, burn_time,
               char_time, radius, jitter, seed)
        if key not in self._burns:
            self._burns[key] = Burn(self, ignitions, speed, burn_time, char_time, radius, jitter, seed)
        return self._burns[key]

    # ------------------------------------------------------------ drawing
    def _displaced(self, t, tremble, sway):
        P = self.P
        if tremble <= 0 and sway <= 0:
            return P
        x, y = P[:, 0], P[:, 1]
        dx = sway * np.sin(t * 0.7 + y * 0.002)
        dy = tremble * np.sin(t * 23.0 + x * 0.05) * np.sin(t * 17.0 + y * 0.031)
        return np.stack([x + dx, y + dy], axis=1)

    def silk_color(self, mood, tint=0.0):
        mood = get_mood(mood)
        base = mix(mood.fog_at(1.0), SNOW, 0.55) if mood.night > 0.4 else SNOW
        return mix(base, mood.fog_at(tint), tint) if tint > 0 else base

    def draw(self, f, t, mood=None, burn=None, lights=(), tremble=0.0, sway=0.0, par=1.0, alpha=1.0,
             kinds=None, min_px=0.9, ctx=None, scale=1.0, tint=0.0, glints=True, flames=True):
        """Draw the web at time t.
        burn     a Burn (None: intact silk)
        lights   [(x, y, radius, strength)]: silk near a light catches it (lantern, fire);
                 the burn's own firelight is added automatically
        glints   True (lights are warm lamp/fire light), an rgb (e.g. SNOW: daylight), False
        tremble  px of high-frequency shiver (Grandmother moving on it); sway: slow drift px
        kinds    subset of KINDS to draw; tint: pre-fog (a far copy)
        ctx      draw on this context instead of the plane of `par` (e.g. a scaled miniature;
                 pass its extra `scale` so line widths stay crisp)"""
        mood = get_mood(mood)
        if ctx is None:
            with plane(f, par) as c:
                self._draw(f, c, t, mood, burn, lights, tremble, sway, par, alpha, kinds, min_px, scale, tint,
                           glints, flames, True)
        else:
            self._draw(f, ctx, t, mood, burn, lights, tremble, sway, par, alpha, kinds, min_px, scale, tint,
                       glints, flames, False)

    def _draw(self, f, c, t, mood, burn, lights, tremble, sway, par, alpha, kinds, min_px, scale, tint, glints,
              flames, own=True):
        zoom = max(f.lcam(par).zoom * scale, 1e-3)
        wmin = min_px / zoom
        P = self._displaced(t, tremble, sway)
        sa = self.sa
        m = np.ones(len(sa), bool) if not kinds else np.isin(self.sk, [KINDS.index(k) for k in kinds])
        silk = self.silk_color(mood, tint)
        a_silk = alpha * (0.68 + 0.1 * (1 - mood.night))
        lights = list(lights)
        if burn is None:
            # intact silk: each strand one polyline, thinned out when it is small on screen
            stride = max(1, int(LOD_PX / max(26.0 * zoom, 1e-3)))
            polys = self._polylines(P, stride, kinds)
            for w, (lines, bb) in polys.items():
                _stroke_lines(c, lines, silk, a_silk, max(w, wmin))
            if glints and lights:
                self._glints_lines(c, polys, lights, mood, alpha, wmin, None if glints is True else glints)
            return
        arr = burn.arrival
        ta, tb = arr[sa], arr[sa + 1]
        lo, hi = np.minimum(ta, tb), np.maximum(ta, tb)
        bt, ct = burn.burn_time, burn.char_time
        intact = m & (t < lo)
        front = m & (lo <= t) & (t < hi)
        burning = m & (hi <= t) & (t < lo + bt)
        charred = m & ~intact & ~front & ~burning & (t < hi + bt + ct)
        # split the segments that the fire front is inside
        fi = np.where(front)[0]
        s0 = sa[fi]
        p0, p1 = P[s0], P[s0 + 1]
        a0, a1 = ta[fi], tb[fi]
        u = np.clip((t - a0) / np.where(a1 != a0, a1 - a0, 1.0), 0.0, 1.0)[:, None]
        pf = p0 + (p1 - p0) * u
        fwd = (a1 > a0)[:, None]
        later = np.where(fwd, p1, p0)
        earlier = np.where(fwd, p0, p1)
        ii = np.where(intact)[0]
        A = np.concatenate([P[sa[ii]], pf])
        B = np.concatenate([P[sa[ii] + 1], later])
        W = np.concatenate([self.sw[ii], self.sw[fi]])
        # intact silk as polylines (runs of consecutive intact segments), the partly burnt
        # segments at the fire fronts as single segments
        for w, lines in self._runs(P, ii).items():
            _stroke_lines(c, lines, silk, a_silk, max(w, wmin))
        _stroke_segs(c, pf, later, self.sw[fi], silk, a_silk, wmin)
        fl = burn.light_sources(t)
        if glints and (lights or fl):
            self._glints_flat(c, A, B, W, lights + fl, mood, alpha, wmin, None if glints is True else glints)
        # charred: drooping, fading dark threads
        ci = np.where(charred)[0]
        if len(ci):
            age = np.clip(t - (0.5 * (ta[ci] + tb[ci]) + bt), 0, None)
            droop = (age ** 1.5) * 26.0
            Ac, Bc = P[sa[ci]].copy(), P[sa[ci] + 1].copy()
            Ac[:, 1] += droop
            Bc[:, 1] += droop
            fade = np.clip(1.0 - age / ct, 0, 1)
            col = mix(mood.ink, mood.lamp, 0.10)
            Wc = self.sw[ci] * 0.8
            for lvl in (0.25, 0.5, 0.75, 1.0):
                sel = (fade > lvl - 0.25) & (fade <= lvl)
                if sel.any():
                    _stroke_segs(c, Ac[sel], Bc[sel], Wc[sel], col, alpha * lvl, wmin)
        # burning silk: hot cores, then flames, glow and embers
        bi = np.where(burning)[0]
        Ab = np.concatenate([P[sa[bi]], earlier])
        Bb = np.concatenate([P[sa[bi] + 1], pf])
        Wb = np.concatenate([self.sw[bi], self.sw[fi]])
        if len(Ab):
            if own and f is not None:
                # glow hugging the burning lines (additive, low-res): lines of fire, not blobs
                with soft_layer(f, par, k=4, op="add", blur=9.0) as Lg:
                    _stroke_segs(Lg, Ab, Bb, Wb * 0 + 1.0, mood.lamp, 0.35 * alpha, 15.0 / zoom)
                    _stroke_segs(Lg, Ab, Bb, Wb * 0 + 1.0, mix(mood.lamp, SNOW, 0.4), 0.3 * alpha, 5.0 / zoom)
            _stroke_segs(c, Ab, Bb, Wb, mix(mood.lamp, SNOW, 0.7), alpha, max(2.2 / zoom, wmin), wmul=2.4)
        if flames:
            vm = np.ones(self.V, bool) if not kinds else np.isin(self.vk, [KINDS.index(k) for k in kinds])
            self._flames(f, c, t, mood, burn, vm, P, par, zoom)

    def _runs(self, P, segs):
        """{width: [polylines]} joining consecutive segments (sorted indices into sa) of the
        same strand into runs."""
        out = {}
        if len(segs) == 0:
            return out
        sa, sid = self.sa, self.sid
        brk = np.where((np.diff(segs) != 1) | (sid[segs[1:]] != sid[segs[:-1]]))[0]
        starts = np.concatenate([[segs[0]], segs[brk + 1]])
        ends = np.concatenate([segs[brk], [segs[-1]]])
        for s0, s1 in zip(starts.tolist(), ends.tolist()):
            out.setdefault(float(self.sw[s0]), []).append(P[sa[s0]:sa[s1] + 2].tolist())
        return out

    def _polylines(self, P, stride, kinds=None):
        """{width: (lines, bboxes)}: every strand (of `kinds`) as one polyline through every
        `stride`-th vertex (ends kept); bboxes (n, 4) x0, y0, x1, y1. Cached at rest."""
        key = (stride, tuple(kinds) if kinds else None)
        static = P is self.P
        if static and key in self._cache:
            return self._cache[key]
        out = {}
        for st in self.strands:
            if (kinds and st.kind not in kinds) or st.v1 - st.v0 < 2:
                continue
            idx = np.arange(st.v0, st.v1, stride)
            if idx[-1] != st.v1 - 1:
                idx = np.append(idx, st.v1 - 1)
            q = P[idx]
            lines, bb = out.setdefault(st.width, ([], []))
            lines.append(q.tolist())
            bb.append((q[:, 0].min(), q[:, 1].min(), q[:, 0].max(), q[:, 1].max()))
        out = {w: (lines, np.asarray(bb, dtype=float)) for w, (lines, bb) in out.items()}
        if static:
            self._cache[key] = out
        return out

    def _glints_lines(self, c, polys, lights, mood, alpha, wmin, col=None):
        """_glints for the polyline path: re-stroke the strands near each light."""
        lamp = col if col is not None else mood.lamp
        hot = mix(lamp, SNOW, 0.55)
        for (lx, ly, lr, ls) in lights[:5]:
            if ls <= 0.02:
                continue
            a = min(ls, 1.0) * alpha
            for w, (lines, bb) in polys.items():
                sel = np.where((bb[:, 0] < lx + lr) & (bb[:, 2] > lx - lr) & (bb[:, 1] < ly + lr) & (bb[:, 3] > ly - lr))[0]
                if not len(sel):
                    continue
                for i in sel.tolist():
                    pts = lines[i]
                    c.move_to(*pts[0])
                    for q in pts[1:]:
                        c.line_to(*q)
                draw.radial(c, (lx, ly), 0, lr, [(0, hot, a), (0.45, lamp, 0.5 * a), (1, lamp, 0.0)])
                c.set_line_width(max(w * 1.25, wmin * 1.2))
                c.stroke()

    def _glints_flat(self, c, A, B, W, lights, mood, alpha, wmin, col=None, levels=5):
        """_glints with every segment lit once: the summed light at its middle, quantized to
        a few levels (flat colors: one stroke per level and width instead of a gradient
        stroke per light). Segments are short, so the falloff still reads smooth."""
        if len(A) == 0:
            return
        M = 0.5 * (A + B)
        I = np.zeros(len(M))
        for (lx, ly, lr, ls) in lights[:6]:
            if ls <= 0.02:
                continue
            d = np.hypot(M[:, 0] - lx, M[:, 1] - ly) / lr
            I += min(ls, 1.0) * np.clip(1.0 - d, 0.0, 1.0) ** 1.6
        I = np.clip(I, 0.0, 1.0) * alpha
        q = np.ceil(I * levels - 0.35).astype(int)
        lamp = col if col is not None else mood.lamp
        hot = mix(lamp, SNOW, 0.55)
        for k in range(1, levels + 1):
            sel = q == k
            if sel.any():
                u = k / levels
                _stroke_segs(c, A[sel], B[sel], W[sel], mix(lamp, hot, u), 0.25 + 0.75 * u, wmin * 1.2, wmul=1.25)

    def _glints(self, c, A, B, W, lights, mood, alpha, wmin, col=None):
        """Re-stroke silk near each light with a radial gradient: strands catching light
        (warm lamp light by default; col: another light color, e.g. SNOW for daylight)."""
        if len(A) == 0:
            return
        M = 0.5 * (A + B)
        lamp = col if col is not None else mood.lamp
        hot = mix(lamp, SNOW, 0.55)
        for (lx, ly, lr, ls) in lights[:5]:
            if ls <= 0.02:
                continue
            sel = np.hypot(M[:, 0] - lx, M[:, 1] - ly) < lr
            if not sel.any():
                continue
            a = min(ls, 1.0) * alpha
            for w in np.unique(W[sel]):
                s2 = sel & (W == w)
                for (x0, y0), (x1, y1) in zip(A[s2].tolist(), B[s2].tolist()):
                    c.move_to(x0, y0)
                    c.line_to(x1, y1)
                draw.radial(c, (lx, ly), 0, lr, [(0, hot, a), (0.45, lamp, 0.5 * a), (1, lamp, 0.0)])
                c.set_line_width(max(w * 1.25, wmin * 1.2))
                c.stroke()

    def _flames(self, f, c, t, mood, burn, vmask, P, par, zoom, max_tongues=520):
        """Flame tongues licking up from burning silk, emissive glow, falling and rising embers."""
        arr = burn.arrival
        idx = np.where(vmask & (arr <= t) & (t < arr + burn.burn_time))[0]
        if len(idx) == 0:
            return
        idx = idx[::max(1, len(idx) // max_tongues)]
        x, y = P[idx, 0], P[idx, 1]
        life = np.clip(1.0 - (t - arr[idx]) / burn.burn_time, 0, 1)
        key = np.floor(x * 0.37 + y * 0.53)
        zf = max(zoom, 0.35) ** 0.35
        h = (16 + 34 * _vhash(key, 1)) * life * (0.7 + 0.3 * np.sin(t * 13 + key)) / zf
        sw = 5 * np.sin(t * 9 + key * 0.7)
        bw = 4.5 / zf
        for xi, yi, hi, si in zip(x.tolist(), y.tolist(), h.tolist(), sw.tolist()):
            if hi < 2:
                continue
            draw.smooth(c, [(xi - bw, yi + 1), (xi - bw * 0.45 + si * 0.3, yi - hi * 0.5), (xi + si, yi - hi),
                            (xi + bw * 0.65 + si * 0.3, yi - hi * 0.45), (xi + bw, yi + 1)], close=True, tension=0.5)
        draw.fill(c, mix(mood.lamp, SNOW, 0.3), 0.95)
        g = idx[::4]
        if f is not None and len(g):
            with f.emit(par=par) as G:
                for xi, yi, li in zip(P[g, 0].tolist(), P[g, 1].tolist(), life[::4].tolist()):
                    glow(G, (xi, yi - 10), 44, mood.lamp, 0.32 * li)
        # embers: some fall (burning drips), some rise on the heat
        e = idx[::2][:260]
        if len(e):
            k = np.floor(P[e, 0] * 13.1 + P[e, 1] * 7.7)
            ph = (t * (0.7 + 0.5 * _vhash(k, 2)) + _vhash(k, 3)) % 1.0
            up = _vhash(k, 4) < 0.45
            ex = P[e, 0] + 34 * np.sin(ph * 6.0 + k) + 24 * (_vhash(k, 5) - 0.5)
            ey = P[e, 1] + np.where(up, -ph * 260, ph * 170)
            r = (1.9 / max(zoom, 0.25)) * (1 - ph)
            for xi, yi, ri in zip(ex.tolist(), ey.tolist(), r.tolist()):
                if ri > 0.2:
                    draw.circle(c, (xi, yi), ri)
            draw.fill(c, mix(mood.lamp, SNOW, 0.45), 0.9)

    # ------------------------------------------------------------ after the fire
    def remnants(self, keep=0.62, seed=3):
        """Charred fragments left after the fire (S09), deterministic and cached. Each is
        dict(kind="span", pts) still spanning and sagging low, or dict(kind="hang", anchor,
        length, bend) broken and hanging from its higher end."""
        key = ("rem", keep, seed)
        if key in self._cache:
            return self._cache[key]
        bias = dict(anchor=1.25, frame=1.2, wrap=1.0, veil=1.15, radial=0.8, spiral=0.45, tangle=0.9, thread=1.1)
        out = []
        for s in self.strands:
            if s.length < 40 or rnd(seed, s.id, 1) > keep * bias[s.kind]:
                continue
            pts = s.pts
            if rnd(seed, s.id, 2) < 0.35 and s.length < 2200:
                sag = 0.10 + 0.12 * rnd(seed, s.id, 3)
                out.append(dict(kind="span", pts=np.asarray(sag_line(tuple(pts[0]), tuple(pts[-1]), sag, step=30.0)),
                                w=s.width, seed=s.id))
            else:
                end = 0 if pts[0][1] < pts[-1][1] else -1
                L = min(s.length * (0.25 + 0.5 * rnd(seed, s.id, 4)), 900.0)
                out.append(dict(kind="hang", anchor=tuple(pts[end].tolist()), length=L, w=s.width, seed=s.id,
                                bend=srnd(seed, s.id, 5)))
        self._cache[key] = out
        return out

    def draw_remnants(self, f, t, mood=None, keep=0.62, seed=3, par=1.0, alpha=1.0, wind=1.0, ctx=None, scale=1.0):
        """S09: the charred web, black threads still spanning (sagging low) or hanging broken
        from their anchors, stirring in the dawn air."""
        mood = get_mood(mood)
        rem = self.remnants(keep, seed)
        if ctx is None:
            with plane(f, par) as c:
                self._draw_rem(f, c, t, mood, rem, par, alpha, wind, scale)
        else:
            self._draw_rem(f, ctx, t, mood, rem, par, alpha, wind, scale)

    def _draw_rem(self, f, c, t, mood, rem, par, alpha, wind, scale):
        zoom = max(f.lcam(par).zoom * scale, 1e-3)
        groups = {}
        for r in rem:
            sd = r["seed"]
            if r["kind"] == "span":
                pts = r["pts"].copy()
                u = np.linspace(0, 1, len(pts))
                pts[:, 1] += wind * (4 + 6 * rnd(sd, 7)) * np.sin(t * (0.7 + 0.3 * rnd(sd, 8)) + sd) * np.sin(np.pi * u)
            else:
                L = r["length"]
                u = np.linspace(0, 1, max(4, int(L / 26)))
                sw = wind * (6 + 16 * rnd(sd, 9)) * np.sin(t * (0.6 + 0.5 * rnd(sd, 10)) + sd * 1.7) * u ** 1.6
                ax, ay = r["anchor"]
                pts = np.stack([ax + r["bend"] * 0.22 * L * np.sin(u * np.pi * 0.5) + sw, ay + L * u], axis=1)
            groups.setdefault(r["w"], []).append(pts)
        for w, runs in groups.items():
            for pts in runs:
                pl = pts.tolist()
                c.move_to(*pl[0])
                for q in pl[1:]:
                    c.line_to(*q)
            draw.stroke(c, mood.ink, max(w * 1.6, 1.5 / zoom), a=alpha)


LOD_PX = 10.0       # intact silk is drawn through vertices >= ~this many screen px apart


def _stroke_lines(c, lines, rgb, alpha, width):
    """Stroke a list of polylines (lists of (x, y)) in one go."""
    if not lines or alpha <= 0:
        return
    for pts in lines:
        c.move_to(*pts[0])
        for q in pts[1:]:
            c.line_to(*q)
    draw.stroke(c, rgb, width, a=alpha)


def _stroke_segs(c, A, B, W, rgb, alpha, wmin, wmul=1.0):
    """Stroke segments A[i]->B[i] grouped by width (one stroke per width class)."""
    if len(A) == 0 or alpha <= 0:
        return
    for w in np.unique(W):
        sel = W == w
        for (x0, y0), (x1, y1) in zip(A[sel].tolist(), B[sel].tolist()):
            c.move_to(x0, y0)
            c.line_to(x1, y1)
        draw.stroke(c, rgb, max(w * wmul, wmin), a=alpha)


class Burn:
    """A precomputed fire on a Web (see Web.ignite). All queries are functions of t."""

    def __init__(self, web, ignitions, speed, burn_time, char_time, radius, jitter, seed):
        self.web = web
        self.ignitions = list(ignitions)
        self.speed = speed
        self.burn_time = burn_time
        self.char_time = char_time
        P, V = web.P, web.V
        fac = np.array([1.0 + jitter * (2 * rnd(seed, s.id) - 1) + (0.25 if s.kind == "anchor" else 0.0)
                        for s in web.strands])
        r, c, w = web._edges
        same = web.owner[r] == web.owner[c]
        w2 = np.where(same, w / fac[web.owner[r]], w)
        t_min = min(t0 for _, _, t0 in ignitions)
        src = V
        sr, sc_, sw = [], [], []
        for (x, y, t0) in ignitions:
            d = np.hypot(P[:, 0] - x, P[:, 1] - y)
            near = np.where(d <= radius)[0]
            if len(near) == 0:
                near = np.array([int(np.argmin(d))])
            for i in near:
                sr.append(src)
                sc_.append(int(i))
                sw.append((t0 - t_min) * speed + d[i] + 1e-3)
        rr = np.concatenate([r, c, sr]).astype(np.int64)
        cc = np.concatenate([c, r, sc_]).astype(np.int64)
        ww = np.concatenate([w2, w2, sw]).astype(float)
        if _sp_dijkstra is not None:
            G = coo_matrix((ww, (rr, cc)), shape=(V + 1, V + 1)).tocsr()
            dist = _sp_dijkstra(G, directed=True, indices=src)[:V]
        else:
            dist = _dijkstra(V + 1, rr, cc, ww, src)[:V]
        self.arrival = t_min + dist / speed
        self.arr = self.arrival
        fin = self.arrival[np.isfinite(self.arrival)]
        self.t_start = t_min
        self.t_done = float(fin.max() + burn_time) if len(fin) else t_min
        self.t_gone = self.t_done + char_time

    def state(self, t):
        """Per-vertex state at t: 0 intact, 1 burning, 2 charred, 3 gone."""
        a = self.arrival
        s = np.zeros(len(a), dtype=np.int8)
        s[a <= t] = 1
        s[a + self.burn_time <= t] = 2
        s[a + self.burn_time + self.char_time <= t] = 3
        return s

    def progress(self, t):
        """(n_strands,) fraction of each strand's length that the fire has passed."""
        out = np.zeros(len(self.web.strands))
        for s in self.web.strands:
            arr = self.arrival[s.v0:s.v1]
            if arr.min() > t:
                continue
            if arr.max() <= t:
                out[s.id] = 1.0
                continue
            seg = np.hypot(*np.diff(s.pts, axis=0).T)
            lo, hi = np.minimum(arr[:-1], arr[1:]), np.maximum(arr[:-1], arr[1:])
            frac = np.clip((t - lo) / np.maximum(hi - lo, 1e-6), 0, 1)
            out[s.id] = float((seg * frac).sum() / max(s.length, 1e-6))
        return out

    def release_time(self, sid):
        """When strand sid has burnt through (its first vertex finishes burning): whatever
        hangs from it falls then. inf if the fire never reaches it."""
        s = self.web.strands[sid]
        return float(np.min(self.arrival[s.v0:s.v1]) + self.burn_time)

    def released(self, sid, t):
        return t >= self.release_time(sid)

    def fronts(self, t):
        """Points where the fire fronts currently are (interpolated inside segments)."""
        web = self.web
        sa = web.sa
        ta, tb = self.arrival[sa], self.arrival[sa + 1]
        sel = (np.minimum(ta, tb) <= t) & (t < np.maximum(ta, tb))
        if not sel.any():
            return []
        a0, a1 = ta[sel], tb[sel]
        u = np.clip((t - a0) / np.where(a1 != a0, a1 - a0, 1.0), 0, 1)[:, None]
        p = web.P[sa[sel]] + (web.P[sa[sel] + 1] - web.P[sa[sel]]) * u
        return [tuple(q) for q in p.tolist()]

    def flames(self, t, step=3):
        """[(x, y, heat 0..1)] sampled on burning vertices."""
        a = self.arrival
        idx = np.where((a <= t) & (t < a + self.burn_time))[0][::max(1, step)]
        heat = 1.0 - (t - a[idx]) / self.burn_time
        P = self.web.P
        return [(float(P[i, 0]), float(P[i, 1]), float(h)) for i, h in zip(idx, heat)]

    def heat(self, t):
        """Px of silk burning at t (a scalar to drive firelight and sound)."""
        a = self.arrival
        return float(((a <= t) & (t < a + self.burn_time)).sum()) * 22.0

    def light_sources(self, t, n=4, radius=900.0):
        """Up to n (x, y, radius, strength) lights at the hottest fire clusters."""
        a = self.arrival
        idx = np.where((a <= t) & (t < a + self.burn_time))[0]
        if len(idx) == 0:
            return []
        P = self.web.P[idx]
        h = 1.0 - (t - a[idx]) / self.burn_time
        keys = np.floor(P / (radius * 0.8)).astype(np.int64)
        buckets = {}
        for (kx, ky), (x, y), hh in zip(keys.tolist(), P.tolist(), h.tolist()):
            b = buckets.setdefault((kx, ky), [0.0, 0.0, 0.0])
            b[0] += x * hh
            b[1] += y * hh
            b[2] += hh
        best = sorted(buckets.values(), key=lambda b: -b[2])[:n]
        return [(b[0] / b[2], b[1] / b[2], radius, min(1.0, b[2] / 12.0)) for b in best if b[2] > 0]


def _dijkstra(n, rr, cc, ww, src):
    """Plain heapq Dijkstra (fallback when scipy is missing)."""
    adj = [[] for _ in range(n)]
    for a, b, w in zip(rr.tolist(), cc.tolist(), ww.tolist()):
        adj[a].append((b, w))
    dist = np.full(n, np.inf)
    dist[src] = 0.0
    h = [(0.0, src)]
    while h:
        d, u = heapq.heappop(h)
        if d > dist[u]:
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(h, (nd, v))
    return dist


# ============================================================================ builders
def build_orb(web, hub, frame, n_radials=30, ring0=70.0, ring_dr=46.0, seed=5, tatter=0.12, width=2.2,
              broken=0.08):
    """An orb web: `frame` (closed polygon of anchor points), radials from the hub to the
    frame, a capture spiral of rings (tattered: missing spans, a few snapped radials
    dangling). Radial, ring and frame vertices coincide exactly, so every crossing is a
    junction. Returns the radial ends [(angle, radius, frame_edge, u)]."""
    hx, hy = hub
    F = list(frame) + [frame[0]]
    ends = []
    for i in range(n_radials):
        th = 2 * math.pi * (i + 0.35 * srnd(seed, i, 1)) / n_radials
        dx, dy = math.cos(th), math.sin(th)
        best = None
        for j in range(len(F) - 1):
            ax, ay = F[j]
            bx, by = F[j + 1]
            ex, ey = bx - ax, by - ay
            den = dx * ey - dy * ex
            if abs(den) < 1e-9:
                continue
            tt = ((ax - hx) * ey - (ay - hy) * ex) / den
            uu = ((ax - hx) * dy - (ay - hy) * dx) / den
            if tt > 0 and 0 <= uu <= 1 and (best is None or tt < best[0]):
                best = (tt, j, uu)
        if best:
            ends.append((th, best[0], best[1], best[2]))
    for j in range(len(F) - 1):
        on = sorted([(e[3], (hx + math.cos(e[0]) * e[1], hy + math.sin(e[0]) * e[1])) for e in ends if e[2] == j])
        web.add([F[j]] + [p for _, p in on] + [F[j + 1]], "frame", width * 1.6, step=30.0)
    rings = {}
    for i, (th, R, j, u) in enumerate(ends):
        dx, dy = math.cos(th), math.sin(th)
        pts = [(hx, hy)]
        r = ring0
        k = 0
        while r < R - 20:
            p = (hx + dx * r, hy + dy * r * (1.0 + 0.02 * srnd(seed, i, k)))
            pts.append(p)
            rings.setdefault(k, {})[i] = p
            r += ring_dr * (1.0 + 0.25 * srnd(seed, i, k, 3)) * (1 + r / 2200.0)
            k += 1
        end = (hx + dx * R, hy + dy * R)
        if rnd(seed, i, 2) < broken and len(pts) > 4:
            cut = len(pts) // 2 + 1
            web.add(pts[:cut], "radial", width)
            last = pts[cut - 1]
            web.add([last, (last[0] + 30 * srnd(seed, i, 7), last[1] + 160 + 120 * rnd(seed, i, 8))], "thread",
                    width * 0.8)
            for kk in list(rings.keys()):
                if kk >= cut - 1:
                    rings[kk].pop(i, None)
        else:
            web.add(pts + [end], "radial", width)
    order = list(range(len(ends)))
    for k, by_rad in rings.items():
        run = []
        for a in order + [order[0]]:
            p = by_rad.get(a)
            if p is None or rnd(seed, k, a, 9) < tatter:
                if len(run) >= 2:
                    web.add(_sagged(run, (hx, hy)), "spiral", width * 0.8, step=40.0)
                run = [p] if p is not None else []
                continue
            run.append(p)
        if len(run) >= 2:
            web.add(_sagged(run, (hx, hy)), "spiral", width * 0.8, step=40.0)
    return ends


def _sagged(run, hub):
    """Polyline through ring points, each span pulled slightly toward the hub (silk sag)."""
    out = [run[0]]
    for a, b in zip(run[:-1], run[1:]):
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        out.append((m[0] + (hub[0] - m[0]) * 0.06, m[1] + (hub[1] - m[1]) * 0.06 + 3))
        out.append(b)
    return out
