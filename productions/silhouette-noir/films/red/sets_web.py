"""RED sets: the giant web as DATA, and fire racing along it.

A Web is a list of Strands (polylines in world coords). Strands that touch share vertices
(junctions), so the web is a graph: fire lit at any point spreads along strands and jumps at
junctions. The burn is precomputed once per ignition set (Dijkstra over the vertex graph),
so every frame is a cheap, deterministic function of t.

    web = CLEARING_WEB (sets_cottage) or Web.from_strands([...])
    burn = web.ignite([(x, y, t0)], speed=560)      # cached per ignition list
    burn.progress(t)        -> (n_strands,) fraction of each strand's length burnt
    burn.state(t)           -> per-vertex state: 0 intact, 1 burning, 2 charred, 3 gone
    burn.fronts(t)          -> [(x, y)] current fire-front points (for sparks / sound cues)
    burn.flames(t, step)    -> [(x, y, heat)] points along burning strands (lights, embers)
    burn.heat(t)            -> total burning length (px): drive the scene's firelight with it
    burn.t_done             -> time the last strand finishes burning
    web.draw(f, t, mood, burn=burn, lights=[(x, y, radius, strength)])

Strand kinds: frame, radial, spiral, anchor (guy lines to trees / ground), wrap (cocoon over
the cottage), veil (across door and windows), tangle (near the ground), thread (single
hanging threads: the spider's drop line, hood threads).
"""
import heapq
import math

import numpy as np

from engine import draw
from engine.core import clamp, hash01, fbm1, lerp
from .sets_common import get_mood, mix, SNOW, INK, glow, soft_layer, flick, rnd, srnd, fogged

try:
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import dijkstra as _sp_dijkstra
except Exception:          # pragma: no cover - scipy is optional
    _sp_dijkstra = None


class Strand:
    """One silk line: pts (n, 2) world coords, kind, width (px at zoom 1)."""
    __slots__ = ("id", "pts", "kind", "width", "v0", "v1", "length", "tag")

    def __init__(self, sid, pts, kind, width, tag=None):
        self.id = sid
        self.pts = np.asarray(pts, dtype=float)
        self.kind = kind
        self.width = width
        self.tag = tag
        d = np.hypot(*np.diff(self.pts, axis=0).T) if len(self.pts) > 1 else np.zeros(0)
        self.length = float(d.sum())
        self.v0 = self.v1 = 0           # vertex index range in the web's flat arrays

    def __repr__(self):
        return f"Strand({self.id}, {self.kind}, n={len(self.pts)}, L={self.length:.0f})"


def densify(pts, step=26.0):
    """Resample a polyline so no segment is longer than `step` (fire resolution)."""
    out = [tuple(pts[0])]
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(math.ceil(L / step)))
        for i in range(1, n + 1):
            u = i / n
            out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    return out


def sag_line(a, b, sag=0.04, n=None, step=26.0):
    """A silk line from a to b hanging under gravity (parabolic sag = sag * length)."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = n or max(2, int(L / step) + 1)
    pts = []
    for i in range(n + 1):
        u = i / n
        pts.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u + 4 * sag * L * u * (1 - u)))
    return pts


class Web:
    """The web graph. Build with add() then finalize() (or Web.from_strands)."""

    def __init__(self, junction_tol=7.0):
        self.strands = []
        self.tol = junction_tol
        self._burns = {}
        self.final = False
        self.anchors = {}

    @staticmethod
    def from_strands(strands, junction_tol=7.0):
        w = Web(junction_tol)
        for s in strands:
            w.add(*s) if isinstance(s, (tuple, list)) else w.add(**s)
        return w.finalize()

    def add(self, pts, kind="tangle", width=2.0, tag=None, step=26.0):
        assert not self.final, "web already finalized"
        pts = densify(pts, step)
        if len(pts) < 2:
            return None
        s = Strand(len(self.strands), pts, kind, width, tag)
        self.strands.append(s)
        return s

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
        V = len(P)
        rows, cols, w = [], [], []
        for s in self.strands:
            idx = np.arange(s.v0, s.v1 - 1)
            seg = np.hypot(*(self.P[idx + 1] - self.P[idx]).T)
            rows.extend(idx)
            cols.extend(idx + 1)
            w.extend(seg)
        # junctions: vertices of different strands within tol (spatial hash)
        cell = self.tol
        grid = {}
        keys = np.floor(self.P / cell).astype(np.int64)
        for i, (kx, ky) in enumerate(keys):
            grid.setdefault((int(kx), int(ky)), []).append(i)
        jr, jc, jw = [], [], []
        for (kx, ky), members in grid.items():
            cand = []
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    cand.extend(grid.get((kx + dx, ky + dy), ()))
            for i in members:
                for j in cand:
                    if j <= i or self.owner[i] == self.owner[j]:
                        continue
                    d = math.hypot(self.P[i, 0] - self.P[j, 0], self.P[i, 1] - self.P[j, 1])
                    if d <= self.tol:
                        jr.append(i)
                        jc.append(j)
                        jw.append(d + 2.0)
        self.junctions = list(zip(jr, jc))
        r = np.concatenate([rows, jr]).astype(np.int64)
        c = np.concatenate([cols, jc]).astype(np.int64)
        ww = np.concatenate([w, jw]).astype(float)
        self._edges = (r, c, np.maximum(ww, 1e-3))
        self.V = V
        self.final = True
        self.kinds = sorted(set(s.kind for s in self.strands))
        return self

    def nearest(self, p, kinds=None):
        """Nearest vertex to p: (strand, vertex_index, (x, y), distance)."""
        d = np.hypot(self.P[:, 0] - p[0], self.P[:, 1] - p[1])
        if kinds:
            mask = np.isin(np.array([self.strands[o].kind for o in self.owner]), list(kinds))
            d = np.where(mask, d, np.inf)
        i = int(np.argmin(d))
        return self.strands[int(self.owner[i])], i, tuple(self.P[i]), float(d[i])

    def bounds(self):
        return (float(self.P[:, 0].min()), float(self.P[:, 1].min()), float(self.P[:, 0].max()), float(self.P[:, 1].max()))

    def by_kind(self, kind):
        return [s for s in self.strands if s.kind == kind]

    # ------------------------------------------------------------ fire
    def ignite(self, ignitions, speed=560.0, burn_time=0.75, char_time=2.6, radius=40.0, jitter=0.25, seed=0):
        """Precompute a burn. ignitions: [(x, y, t0), ...]. Fire travels `speed` px/s along
        silk (each strand varies by +-jitter), lights every vertex within `radius` of an
        ignition point, keeps a vertex in flame for `burn_time` s, leaves a charred thread for
        `char_time` s, then the silk is gone. Cached by arguments."""
        key = (tuple((round(a, 2), round(b, 2), round(c, 4)) for a, b, c in ignitions), speed, burn_time,
               char_time, radius, jitter, seed)
        if key in self._burns:
            return self._burns[key]
        b = Burn(self, ignitions, speed, burn_time, char_time, radius, jitter, seed)
        self._burns[key] = b
        return b

    # ------------------------------------------------------------ drawing
    def _displaced(self, t, tremble, sway):
        P = self.P
        if tremble <= 0 and sway <= 0:
            return P
        x, y = P[:, 0], P[:, 1]
        dx = sway * np.sin(t * 0.7 + y * 0.002) * np.clip((1500 - y) / 2000.0, 0, 1)
        dy = tremble * np.sin(t * 23.0 + x * 0.05) * np.sin(t * 17.0 + y * 0.031)
        return np.stack([x + dx, y + dy], axis=1)

    def draw(self, f, t, mood=None, burn=None, lights=(), tremble=0.0, sway=0.0, par=1.0, alpha=1.0,
             kinds=None, min_px=0.9, tint=0.0, ctx=None, glints=True, embers=True):
        """Draw the web at time t. burn: a Burn (or None for intact silk). lights: list of
        (x, y, radius, strength) that make nearby silk catch light (lantern, fire).
        tremble: px of high-frequency shiver (the spider moving); sway: px of slow sway.
        kinds: subset of strand kinds to draw. tint: pre-fog for a far copy of the web."""
        mood = get_mood(mood)
        P = self._displaced(t, tremble, sway)
        c = ctx
        from .sets_common import plane
        own = c is None
        if own:
            cm = plane(f, par)
            c = cm.__enter__()
        try:
            zoom = f.lcam(par).zoom
            st = burn.state(t) if burn is not None else None
            silk = self._silk_color(mood, tint)
            # group intact segments by width class, one stroke each
            groups = {}
            charred = []
            burning = []
            for s in self.strands:
                if kinds and s.kind not in kinds:
                    continue
                i0, i1 = s.v0, s.v1
                if st is None:
                    groups.setdefault(s.width, []).append(P[i0:i1])
                    continue
                sv = st[i0:i1]
                if sv.max() == 0:
                    groups.setdefault(s.width, []).append(P[i0:i1])
                    continue
                if sv.min() == 3:
                    continue
                # split into runs of equal state at segment level, cutting at the front
                seg_state = np.maximum(sv[:-1], sv[1:])
                arr = burn.arr[i0:i1]
                k = 0
                n = len(seg_state)
                while k < n:
                    m = k
                    while m + 1 < n and seg_state[m + 1] == seg_state[k]:
                        m += 1
                    pts = P[i0 + k:i0 + m + 2]
                    stt = seg_state[k]
                    if stt == 0:
                        groups.setdefault(s.width, []).append(pts)
                    elif stt == 1:
                        burning.append((pts, s.width, arr[k:m + 2]))
                    elif stt == 2:
                        charred.append((pts, s.width, arr[k:m + 2]))
                    k = m + 1
                # partial segments at the fire front: intact part up to the front point
                if burn is not None:
                    for j in range(len(sv) - 1):
                        a0, a1 = arr[j], arr[j + 1]
                        if (a0 <= t < a1) or (a1 <= t < a0):
                            u = (t - a0) / (a1 - a0) if a1 != a0 else 0.0
                            p0, p1 = P[i0 + j], P[i0 + j + 1]
                            pf = p0 + (p1 - p0) * u
                            tail = p1 if a1 > a0 else p0
                            groups.setdefault(s.width, []).append(np.array([pf, tail]))
            # intact silk: base strokes
            for w, runs in groups.items():
                for pts in runs:
                    c.move_to(*pts[0])
                    for q in pts[1:]:
                        c.line_to(*q)
                draw.stroke(c, silk, max(w, min_px / zoom), a=alpha * self._silk_alpha(mood))
            # light catching: re-stroke intact silk with radial gradients around the lights
            if glints and lights:
                for (lx, ly, lr, ls) in lights[:4]:
                    if ls <= 0.02:
                        continue
                    for w, runs in groups.items():
                        for pts in runs:
                            if np.min(np.hypot(pts[:, 0] - lx, pts[:, 1] - ly)) > lr:
                                continue
                            c.move_to(*pts[0])
                            for q in pts[1:]:
                                c.line_to(*q)
                        hot = mix(mood.lamp, SNOW, 0.55)
                        draw.radial(c, (lx, ly), 0, lr, [(0, hot, clamp(ls) * alpha), (0.5, mood.lamp, 0.45 * clamp(ls) * alpha),
                                                          (1, mood.lamp, 0.0)])
                        c.set_line_width(max(w * 1.2, (min_px + 0.3) / zoom))
                        c.stroke()
            # charred threads: drooping, fading ink
            if charred:
                for pts, w, arr in charred:
                    age = np.clip(t - (arr + burn.burn_time), 0, None)
                    droop = (age ** 1.5) * 26.0
                    q = pts.copy()
                    q[:, 1] += droop[:len(q)]
                    a = clamp(1.0 - float(age.mean()) / burn.char_time)
                    if a <= 0.02:
                        continue
                    c.move_to(*q[0])
                    for r in q[1:]:
                        c.line_to(*r)
                    draw.stroke(c, mix(mood.ink, mood.lamp, 0.12), max(w * 0.8, min_px / zoom), a=alpha * a)
            # burning silk: hot cores here, glow + flames + embers in the emissive pass
            if burning:
                hot = mix(mood.lamp, SNOW, 0.6)
                for pts, w, arr in burning:
                    c.move_to(*pts[0])
                    for r in pts[1:]:
                        c.line_to(*r)
                draw.stroke(c, hot, max(w * 1.8, 1.6 / zoom), a=alpha)
                self._flames(f, c, burning, t, mood, par, zoom, embers)
        finally:
            if own:
                cm.__exit__(None, None, None)

    def _silk_color(self, mood, tint):
        base = mix(mood.fog_at(1.0), SNOW, 0.55) if mood.night > 0.4 else SNOW
        return mix(base, mood.fog_at(tint), tint) if tint > 0 else base

    def _silk_alpha(self, mood):
        return 0.5 + 0.25 * (1 - mood.night)

    def _flames(self, f, c, burning, t, mood, par, zoom, embers=True):
        """Flame tongues licking up from burning silk, emissive glow, falling embers."""
        tongues = []
        glow_pts = []
        for pts, w, arr in burning:
            n = len(pts)
            for i in range(0, n, 2):
                x, y = pts[i]
                age = t - arr[min(i, len(arr) - 1)]
                life = clamp(1.0 - age / 0.9)
                if life <= 0:
                    continue
                key = int(x * 0.37 + y * 0.53)
                h = (14 + 30 * hash01(key, 1)) * life * (0.7 + 0.3 * math.sin(t * 13 + key))
                sw = 5 * math.sin(t * 9 + key * 0.7)
                tongues.append([(x - 4.5, y + 1), (x - 2 + sw * 0.3, y - h * 0.5), (x + sw, y - h),
                                (x + 3 + sw * 0.3, y - h * 0.45), (x + 4.5, y + 1)])
                glow_pts.append((x, y, life))
        if tongues:
            for tg in tongues:
                draw.smooth(c, tg, close=True, tension=0.5)
            draw.fill(c, mix(mood.lamp, SNOW, 0.3), 0.95)
        if not glow_pts:
            return
        with f.emit(par=par) as G:
            for i, (x, y, life) in enumerate(glow_pts[::2]):
                glow(G, (x, y - 8), 46, mood.lamp, 0.55 * life)
        if embers:
            col = mix(mood.lamp, SNOW, 0.4)
            for i, (x, y, life) in enumerate(glow_pts[::3]):
                for k in range(2):
                    key = int(x * 13.1 + y * 7.7) + k * 101
                    ph = (t * (0.8 + 0.4 * hash01(key, 2)) + hash01(key, 3)) % 1.0
                    ex = x + 30 * math.sin(ph * 6.0 + key) + 20 * (hash01(key, 4) - 0.5)
                    ey = y + ph * 160
                    draw.circle(c, (ex, ey), 1.6 / max(zoom, 0.2) * (1 - ph))
            draw.fill(c, col, 0.85)


class Burn:
    """A precomputed fire on a Web (see Web.ignite)."""

    def __init__(self, web, ignitions, speed, burn_time, char_time, radius, jitter, seed):
        self.web = web
        self.ignitions = list(ignitions)
        self.speed = speed
        self.burn_time = burn_time
        self.char_time = char_time
        P = web.P
        V = web.V
        # per-strand speed variation (fire races faster up long dry anchor lines)
        fac = np.array([1.0 + jitter * (2 * hash01(seed, s.id) - 1) + (0.25 if s.kind == "anchor" else 0.0)
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
        self.arr = t_min + dist / speed                  # arrival time per vertex (inf = never)
        self.arr[~np.isfinite(self.arr)] = np.inf
        fin = self.arr[np.isfinite(self.arr)]
        self.t_start = t_min
        self.t_done = float(fin.max() + burn_time) if len(fin) else t_min
        self.t_gone = self.t_done + char_time
        L = []
        for s in web.strands:
            L.append(s.length)
        self._len = np.array(L)

    def state(self, t):
        """Per-vertex state at t: 0 intact, 1 burning, 2 charred, 3 gone."""
        a = self.arr
        s = np.zeros(len(a), dtype=np.int8)
        s[a <= t] = 1
        s[a + self.burn_time <= t] = 2
        s[a + self.burn_time + self.char_time <= t] = 3
        return s

    def progress(self, t):
        """(n_strands,) fraction of each strand's length that the fire has passed."""
        out = np.zeros(len(self.web.strands))
        for s in self.web.strands:
            arr = self.arr[s.v0:s.v1]
            if arr.min() > t:
                continue
            if arr.max() <= t:
                out[s.id] = 1.0
                continue
            pts = s.pts
            seg = np.hypot(*np.diff(pts, axis=0).T)
            a0, a1 = arr[:-1], arr[1:]
            lo, hi = np.minimum(a0, a1), np.maximum(a0, a1)
            frac = np.clip((t - lo) / np.maximum(hi - lo, 1e-6), 0, 1)
            out[s.id] = float((seg * frac).sum() / max(s.length, 1e-6))
        return out

    def strand_progress(self, sid, t):
        return float(self.progress(t)[sid])

    def released(self, sid, t):
        """True once strand `sid` has burnt through (whatever hung from it falls)."""
        s = self.web.strands[sid]
        return bool(np.any(self.arr[s.v0:s.v1] + self.burn_time <= t))

    def release_time(self, sid):
        s = self.web.strands[sid]
        return float(np.min(self.arr[s.v0:s.v1]) + self.burn_time)

    def fronts(self, t):
        """Points where the fire front currently is (interpolated along segments)."""
        out = []
        P = self.web.P
        for s in self.web.strands:
            arr = self.arr[s.v0:s.v1]
            if arr.min() > t or arr.max() <= t:
                continue
            for j in range(len(arr) - 1):
                a0, a1 = arr[j], arr[j + 1]
                if (a0 <= t < a1) or (a1 <= t < a0):
                    u = (t - a0) / (a1 - a0)
                    p = P[s.v0 + j] + (P[s.v0 + j + 1] - P[s.v0 + j]) * u
                    out.append((float(p[0]), float(p[1])))
        return out

    def flames(self, t, step=3):
        """[(x, y, heat 0..1)] sampled on burning vertices (for lights, embers, smoke)."""
        a = self.arr
        m = (a <= t) & (t < a + self.burn_time)
        idx = np.where(m)[0][::max(1, step)]
        P = self.web.P
        heat = 1.0 - (t - a[idx]) / self.burn_time
        return [(float(P[i, 0]), float(P[i, 1]), float(h)) for i, h in zip(idx, heat)]

    def heat(self, t):
        """Total length (px) of silk burning at t: a scalar to drive firelight."""
        a = self.arr
        m = (a <= t) & (t < a + self.burn_time)
        return float(m.sum()) * 22.0

    def light_sources(self, t, n=4, radius=900.0):
        """Up to n (x, y, radius, strength) lights at the hottest fire clusters, for
        Web.draw(lights=...) and for the scene's firelight."""
        fl = self.flames(t, step=1)
        if not fl:
            return []
        pts = np.array([(x, y) for x, y, h in fl])
        h = np.array([h for x, y, h in fl])
        out = []
        cell = radius * 0.8
        keys = np.floor(pts / cell).astype(int)
        buckets = {}
        for (kx, ky), p, hh in zip(keys, pts, h):
            b = buckets.setdefault((kx, ky), [0.0, 0.0, 0.0])
            b[0] += p[0] * hh
            b[1] += p[1] * hh
            b[2] += hh
        best = sorted(buckets.values(), key=lambda b: -b[2])[:n]
        for bx, by, bh in best:
            if bh <= 0:
                continue
            out.append((bx / bh, by / bh, radius, clamp(bh / 12.0)))
        return out


def _dijkstra(n, rr, cc, ww, src):
    """Plain heapq Dijkstra (fallback when scipy is missing)."""
    adj = [[] for _ in range(n)]
    for a, b, w in zip(rr, cc, ww):
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


# ============================================================================ the clearing web
def build_orb(web, hub, frame, n_radials=30, ring0=70.0, ring_dr=46.0, seed=5, tatter=0.12, width=2.2):
    """An orb web: frame polygon (list of points, closed), radials from the hub to the frame,
    a spiral of capture rings, tattered (missing segments, a few broken radials dangling).
    Radial / ring / frame vertices coincide exactly, so junctions are exact."""
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
    # frame threads with the radial ends inserted as vertices
    for j in range(len(F) - 1):
        on = sorted([(e[3], (hx + math.cos(e[0]) * e[1], hy + math.sin(e[0]) * e[1])) for e in ends if e[2] == j])
        pts = [F[j]] + [p for _, p in on] + [F[j + 1]]
        web.add(pts, "frame", width * 1.6, step=30.0)
    # radials with ring crossings as exact vertices
    rings = {}
    for i, (th, R, j, u) in enumerate(ends):
        dx, dy = math.cos(th), math.sin(th)
        broken = rnd(seed, i, 2) < 0.08
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
        if broken and len(pts) > 4:
            # snapped radial: the outer part hangs from the last ring it reached
            cut = len(pts) // 2 + 1
            web.add(pts[:cut], "radial", width)
            last = pts[cut - 1]
            web.add([last, (last[0] + 30 * srnd(seed, i, 7), last[1] + 160 + 120 * rnd(seed, i, 8))], "thread", width * 0.8)
            for kk in list(rings.keys()):
                if kk >= cut - 1:
                    rings[kk].pop(i, None)
        else:
            web.add(pts + [end], "radial", width)
    # capture spiral: ring k joins neighbouring radials (with a soft inward sag)
    order = list(range(len(ends)))
    for k, pts_by_rad in rings.items():
        run = []
        for a in order + [order[0]]:
            p = pts_by_rad.get(a)
            if p is None or rnd(seed, k, a, 9) < tatter:
                if len(run) >= 2:
                    web.add(_sagged(run, hub), "spiral", width * 0.8, step=40.0)
                run = [p] if p is not None else []
                continue
            run.append(p)
        if len(run) >= 2:
            web.add(_sagged(run, hub), "spiral", width * 0.8, step=40.0)
    return ends


def _sagged(run, hub):
    """Polyline through ring points with each span pulled slightly toward the hub."""
    out = [run[0]]
    for a, b in zip(run[:-1], run[1:]):
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        out.append((m[0] + (hub[0] - m[0]) * 0.06, m[1] + (hub[1] - m[1]) * 0.06 + 3))
        out.append(b)
    return out
