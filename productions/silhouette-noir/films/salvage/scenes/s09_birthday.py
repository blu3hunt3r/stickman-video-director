"""s09 · BIRTHDAY: dial -> spiral (9.0 s).

IN  (match cut from s08): the safe's dial close-up (sets.DialCloseup) centred at screen
    (540, 960), radius 260 px, dial at 0, lit from the upper left, light marine snow; the
    push goes on to r = 420 by 1.5 s (starting gently, ~75 px/s of radius).
Beats (scene-local s; L14 0.80-4.48):
    0.20-0.83       his right glove comes in from the lower right and grips the knob (0.55)
    0.86-[didn't]   a small searching turn that stops dead on [didn't@1.04]; he holds
    [birthday@3.51] right, left, right: 7 - 14 - 29, tumbler clicks at 3.90, 4.60, 5.30
    3.92-4.30       on the first click the room drops into ink; the dial's 100 ticks lift
                    off as PAPER and unwind into a Bass spiral (a spiral rule with tick teeth)
    4.60, 5.30      each click snaps the spiral (a ratchet kick) and pulses it inward; the
                    combination stamps below, 7 · 14 · 29 (his birthday)
    5.30-7.20       the spiral flows inward (turning clockwise) while it slowly grows: Vertigo
    7.20-7.55       it collapses to a point; an iris opens from that point: live again
    7.55-8.35       the safe door swings open toward the camera (it sweeps past the lens);
                    darkness inside; 7.95-8.55 the helmet beam slides in and finds the logbook
OUT (dissolve 0.75 s, 8.625-9.375): pushing into the safe; the closed logbook centred at
    (540, 960), ~620 x 540 px, in the beam's warm pool, darkness around.
"""
import math

import cairo

from engine import atmos, bass, draw
from engine.core import clamp, ease, lerp, hash01
from engine.palette import PAPER
from engine.timing import Cue
from films.salvage import sets as S

PAL = S.PAL
INK = PAL.ink
WARM = PAL.light
DC = S.DialCloseup()
LAMP = (-0.62, -0.78)
C = (540.0, 960.0)                        # screen centre: the dial, the spiral, the book

COMBO = (7, 14, 29)
CLICKS = (3.90, 4.60, 5.30)
INK_IN = (3.92, 0.36)                     # the live shot drops into ink
UNWIND = (3.96, 0.70)                     # ticks -> spiral
FILL = (4.24, 0.52)                       # the ticks widen into one band
COLLAPSE = (7.20, 0.35)
IRIS = (7.42, 0.34)
DOOR = (7.55, 0.80)
BEAM = (7.95, 0.60)
PUSH = (7.62, 1.76)                       # into the safe, to 9.38
TURNS_SP = 3.25                           # turns of the spiral
RHO = 0.07                                # inner / outer radius of the spiral
BOOK = (40.0, 160.0, -4.0, 2.8)           # the logbook in the safe: DialCloseup's placement
BOOK_Z = 900.0
S08_END = 10.0                            # s08's clock at the match cut (its snow continues)


def _k(t, t0, dur, e="inout"):
    if t <= t0:
        return 0.0
    if dur <= 0 or t >= t0 + dur:
        return 1.0
    return ease(e, (t - t0) / dur)


def _words(T):
    return dict(didnt=T.at("didn't"), birthday=T.at("birthday"))


# ----------------------------------------------------------------------------- the dial
def _turns(w):
    """(t0, t1, from, to) of the dial moves: the search that stops on [didn't], then right to
    7, left to 14 (passing it once), right to 29. Clockwise = increasing angle."""
    a7 = S.dial_angle_for(COMBO[0]) % 360.0                    # 334.8
    a14 = S.dial_angle_for(COMBO[1]) % 360.0 - 360.0           # -50.4
    a29 = S.dial_angle_for(COMBO[2]) % 360.0                   # 255.6
    return [(0.86, w["didnt"], 0.0, 14.0), (w["birthday"], CLICKS[0], 14.0, a7),
            (CLICKS[0], CLICKS[1], a7, a14), (CLICKS[1], CLICKS[2], a14, a29)]


def _dial(t, w):
    """Dial rotation (deg, clockwise) at t; each move lands exactly on its click."""
    d = 0.0
    for i, (t0, t1, a, b) in enumerate(_turns(w)):
        if t <= t0:
            break
        e = "out" if i == 0 else "inout3"
        d = lerp(a, b, _k(t, t0, t1 - t0, e))
    return d


# ----------------------------------------------------------------------------- camera (live)
def _r_screen(t):
    """The dial's on-screen radius in the first live part: the s08 push carries on."""
    k = 0.65 * _k(t, 0.0, 1.5, "inout") + 0.35 * _k(t, 0.0, 1.5, "out")
    r = lerp(260.0, 420.0, k)
    return r + 34.0 * _k(t, 1.5, 2.4, "inout")


def _camera(t, w):
    if t < 6.0:
        return DC.camera(r_screen=_r_screen(t), rot=0.0)
    k = _k(t, PUSH[0], PUSH[1], "inout")
    r = lerp(500.0, 600.0, k)
    cx, cy = lerp(0.0, BOOK_CENTRE[0], k), lerp(0.0, BOOK_CENTRE[1], k)
    return DC.camera(r_screen=r, rot=0.0, cx=cx, cy=cy)


def _door(t):
    return _k(t, DOOR[0], DOOR[1], "inout")


# ----------------------------------------------------------------------------- the glove
def _glove_polys():
    """The diver's right glove on the knob (world coords, knob at the origin, the hand from
    the lower right): a three-finger diving mitt - index finger over the knob's upper-right
    rim, the mitt of the other three fingers over its right rim, the thumb under its lower-
    left rim - the back of the hand and the cuff. Capsules (a, b, ra, rb) per part; each part
    has a twist factor (the fingers turn the knob, the cuff hardly moves)."""
    return [
        ("cuff", 0.45, [((600.0, 500.0), (1120.0, 1110.0), 176.0, 200.0)]),
        ("hand", 0.9, [((360.0, 110.0), (540.0, 360.0), 118.0, 150.0)]),
        ("index", 1.0, [((350.0, 10.0), (262.0, -128.0), 43.0, 39.0),        # hooked over the
                        ((262.0, -128.0), (152.0, -116.0), 39.0, 33.0)]),     # upper-right rim
        ("mitt", 1.0, [((390.0, 100.0), (262.0, 20.0), 60.0, 54.0),           # the other three,
                       ((262.0, 20.0), (214.0, 30.0), 54.0, 50.0)]),          # curled on the rim
        ("thumb", 1.0, [((360.0, 300.0), (236.0, 196.0), 46.0, 41.0),        # pinching the
                        ((236.0, 196.0), (150.0, 126.0), 41.0, 34.0)]),       # lower-right rim
    ]


_GL = _glove_polys()


def _glove_path(ctx, curl, rot, dx=0.0, dy=0.0):
    """The glove as one path (curl 0 = fingers open and back, 1 = gripping; rot = the knob
    twist in degrees, shared out by the parts' twist factors)."""
    op = 1.0 - curl
    for key, tf, caps in _GL:
        ang = math.radians(rot * tf)
        if key in ("index", "mitt", "thumb"):
            ang += math.radians({"index": -24.0, "mitt": -16.0, "thumb": 20.0}[key] * op)
        ca, sa = math.cos(ang), math.sin(ang)
        pv = (380.0, 160.0) if key in ("index", "mitt", "thumb") else (0.0, 0.0)
        tw = math.radians(rot * tf) if key in ("index", "mitt", "thumb") else 0.0

        def xf(p, ca=ca, sa=sa, pv=pv, tw=tw):
            if pv != (0.0, 0.0):
                # the digit opens about the hand, then the whole digit twists about the knob
                co, so = math.cos(ang - tw), math.sin(ang - tw)
                x, y = p[0] - pv[0], p[1] - pv[1]
                p = (pv[0] + x * co - y * so, pv[1] + x * so + y * co)
                ct, st = math.cos(tw), math.sin(tw)
                return (p[0] * ct - p[1] * st + dx, p[0] * st + p[1] * ct + dy)
            return (p[0] * ca - p[1] * sa + dx, p[0] * sa + p[1] * ca + dy)
        for a, b, ra, rb in caps:
            ctx.new_sub_path()
            draw.capsule(ctx, xf(a), xf(b), ra, rb)


def _hand_state(t, w):
    """(on, (dx, dy), rot, curl): the glove's presence, slide-in offset, twist about the knob
    and grip. It turns the small search, twists into the first spin, then lets the dial run
    (the room drops into ink before the second turn)."""
    k_in = _k(t, 0.20, 0.60, "out3")
    off = ((1.0 - k_in) * 760.0, (1.0 - k_in) * 820.0)
    curl = 0.2 + 0.8 * _k(t, 0.55, 0.28, "out3")             # grips as it lands (sound: 0.55)
    rot = min(_dial(t, w), 14.0)                              # the search turn: the hand turns it
    rot += 28.0 * _k(t, w["birthday"], 0.15, "out3")          # the first spin: a hard twist
    rot -= 28.0 * _k(t, CLICKS[0], 0.14, "inout")             # and back for the left turn
    curl -= 0.3 * _k(t, w["birthday"] + 0.13, 0.12, "out")    # the dial runs on under the fingertips
    curl += 0.3 * _k(t, CLICKS[0] - 0.05, 0.06, "out")
    return k_in > 0.0, off, rot, clamp(curl)


def _glove_ghost(f, t, w, alpha):
    """The glove as a flat ink silhouette in front of the lifted PAPER ticks while the room
    drops into ink (it melts into the dark)."""
    on, off, rot, curl = _hand_state(t, w)
    if not on or alpha <= 0.0:
        return
    with f.layer() as c:
        c.new_path()
        _glove_path(c, curl, rot, off[0], off[1])
        c.set_source_rgba(*INK, alpha)
        c.fill()


def _draw_glove(f, t, w):
    on, off, rot, curl = _hand_state(t, w)
    if not on:
        return
    lx, ly = LAMP
    with f.layer() as c:
        # its shadow on the door (the lamp is upper left)
        c.new_path()
        _glove_path(c, curl, rot, off[0] - lx * 46.0, off[1] - ly * 46.0)
        c.set_source_rgba(*INK, 0.5)
        c.fill()
        # the glove: a warm rim along the lamp side, ink everywhere else
        c.new_path()
        _glove_path(c, curl, rot, off[0], off[1])
        c.set_source_rgb(*S.mix(INK, WARM, 0.55))
        c.fill_preserve()
        c.save()
        c.clip()
        c.new_path()
        _glove_path(c, curl, rot, off[0] - lx * 13.0, off[1] - ly * 13.0)
        c.set_source_rgb(*S.mix(INK, PAL.mid, 0.10))
        c.fill()
        c.restore()
        # the cuff's seam ring
        ang = math.radians(rot * 0.45)
        ca, sa = math.cos(ang), math.sin(ang)

        def xf(p):
            return (p[0] * ca - p[1] * sa + off[0], p[0] * sa + p[1] * ca + off[1])
        c.new_path()
        draw.capsule(c, xf((760.0, 560.0)), xf((610.0, 710.0)), 26.0, 26.0)
        c.set_source_rgb(*INK)
        c.fill()


# ----------------------------------------------------------------------------- the safe's inside
def _book_centre():
    """Action-plane point of the logbook's centre with the camera centred there (the view's
    vanishing point is the camera centre, so a thing at depth projects onto it)."""
    x, y, ang, s = BOOK
    return (x - math.sin(math.radians(ang)) * 58.0 * s, y + math.cos(math.radians(ang)) * 58.0 * s)


BOOK_CENTRE = _book_centre()


def _door_clip(c, view, door):
    """Even-odd clip that excludes the swinging door (as DialCloseup draws it)."""
    x0, y0, x1, y1 = DC.PLATE
    a = math.radians(clamp(door) * 100.0)

    def P3(x, y, z=0.0):
        xr = DC.HINGE_X + (x - DC.HINGE_X) * math.cos(a)
        zr = z - (x - DC.HINGE_X) * math.sin(a)
        return view.P(xr, y, zr)
    c.new_path()
    c.rectangle(-20000.0, -20000.0, 40000.0, 40000.0)
    draw.poly(c, [P3(x0, y0), P3(x1, y0), P3(x1, y1), P3(x0, y1)])
    draw.poly(c, [P3(x1, y0), P3(x1, y1), P3(x1, y1, 140.0), P3(x1, y0, 140.0)])
    c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    c.clip()
    c.set_fill_rule(cairo.FILL_RULE_WINDING)


def _draw_book(c, light, spot):
    """The closed logbook seen face on (cover to us): a dark cloth cover with a lighter spine
    band and corner pieces, a pale label, the pale fore-edge of the pages; the beam's warm
    pool (spot = local point, light 0..1) lights it."""
    x, y, ang, s = BOOK
    c.save()
    c.translate(x, y)
    c.rotate(math.radians(ang))
    c.scale(s, s)
    cover = S.mix(INK, PAL.mid, 0.14)
    lit = S.mix(S.mix(INK, PAL.mid, 0.30), WARM, 0.55)
    S.round_rect(c, -84, -10, 84, 126, 7)                    # the board
    c.set_source_rgb(*cover)
    c.fill()
    c.save()
    S.round_rect(c, -84, -10, 84, 126, 7)
    c.clip()
    if light > 0:
        g = cairo.RadialGradient(spot[0], spot[1], 0.0, spot[0], spot[1], 150.0)
        g.add_color_stop_rgba(0.0, *lit, 0.95 * light)
        g.add_color_stop_rgba(0.45, *lit, 0.55 * light)
        g.add_color_stop_rgba(1.0, *lit, 0.0)
        c.rectangle(-90, -20, 180, 160)
        c.set_source(g)
        c.fill()
    # the spine band (left) and the cloth corners: darker
    c.rectangle(-84, -10, 26, 136)
    c.set_source_rgba(*INK, 0.55)
    c.fill()
    for (cx, cy, sx, sy) in ((84, -10, -1, 1), (84, 126, -1, -1)):
        draw.poly(c, [(cx, cy), (cx + sx * 30, cy), (cx, cy + sy * 30)])
        c.set_source_rgba(*INK, 0.5)
        c.fill()
    c.restore()
    # the label on the cover
    S.round_rect(c, -14, 18, 50, 46, 2)
    c.set_source_rgb(*S.lit_paper(0.12 + 0.62 * light))
    c.fill()
    for i in range(2):
        c.rectangle(-6, 26 + i * 9, 48 - 14 * i, 3)
    c.set_source_rgba(*INK, 0.35 + 0.3 * light)
    c.fill()
    # the pages' fore-edge (right) and tail (bottom), pale
    S.round_rect(c, 78, -4, 86, 120, 2)
    S.round_rect(c, -56, 118, 84, 125, 2)
    c.set_source_rgb(*S.lit_paper(0.10 + 0.75 * light))
    c.fill()
    c.restore()


def _draw_inside(f, t, cam):
    """The logbook in the dark inside of the safe, behind the door's sweep, lit by the beam."""
    door = _door(t)
    if door <= 0.0:
        return 0.0
    view = S.InteriorView(f, lens=DC.LENS)
    kb = _k(t, BEAM[0], BEAM[1], "inout")
    # the spot slides from the inside's upper-left wall onto the cover
    spot = (lerp(-150.0, -6.0, kb), lerp(-60.0, 52.0, kb))
    with f.layer() as c:
        _door_clip(c, view, door)
        with S.at_depth(c, view, BOOK_Z):
            _draw_book(c, kb, spot)
    return kb


def _beam(f, t, cam, kb):
    """The helmet beam, from the upper left out of frame, sliding into the safe."""
    if kb <= 0.0:
        return None
    view = S.InteriorView(f, lens=DC.LENS)
    x, y, ang, s = BOOK
    tgt0 = view.P(-560.0, -420.0, BOOK_Z)
    tgt1 = view.P(BOOK_CENTRE[0] - 20.0, BOOK_CENTRE[1] - 60.0, BOOK_Z)
    tgt = (lerp(tgt0[0], tgt1[0], kb), lerp(tgt0[1], tgt1[1], kb))
    apex = cam.to_world((-260.0, -520.0))
    ang = math.degrees(math.atan2(tgt[1] - apex[1], tgt[0] - apex[0]))
    L = math.hypot(tgt[0] - apex[0], tgt[1] - apex[1]) * 1.08
    cone = atmos.beam(f, apex, ang, length=L, half_angle=9.0, intensity=0.42 * kb, falloff=0.6, soft=0.6,
                      core=0.35, fog=0.5, glare=0.0, dust=0.0, seed=4, t=t)
    atmos.light_pool(f, tgt, 190.0 / max(cam.zoom, 0.1) * 1.4, 150.0 / max(cam.zoom, 0.1) * 1.4,
                     intensity=0.28 * kb, t=t)
    return cone


def _live(f, t, w):
    cam = _camera(t, w)
    f.set_camera(cam)
    f.fill(S.INT_BG)
    DC.draw(f, t, dial_angle=_dial(t, w), lamp=LAMP, power=1.0, door=_door(t), book=False)
    kb = _draw_inside(f, t, cam)
    if t < 6.0:
        _draw_glove(f, t, w)
    cone = _beam(f, t, cam, kb)
    glow = atmos.Glow(cam.to_world((140.0, 260.0)), 520.0 / cam.zoom, intensity=0.5, color=WARM)
    # s08's snow carried on across the match cut (same specks on s08's clock); the lamp's
    # warmth on them comes up only after the cut
    gain = 2.5 if cone is not None else 2.5 * _k(t, 0.0, 1.5, "inout")
    atmos.marine_snow(f, density=0.45, t=t + S08_END, seed=19, sink=9.0, current=(6.0, 0.0), alpha=0.6,
                      size=1.4, lit=cone if cone is not None else glow, lit_gain=gain, lit_color=WARM)


# ----------------------------------------------------------------------------- the spiral
_TICKS = 100


def _tick_depth(i):
    if i == 0:
        return 0.30
    return 0.20 if i % 10 == 0 else 0.13 if i % 5 == 0 else 0.075


def _tick_half(i):
    if i == 0:
        return 0.9
    return 0.42 if i % 10 == 0 else 0.34


def _spiral_state(t, w):
    """(R, scale, theta_ref, u, fill): ring radius (screen px), overall scale, the screen
    angle of tick 0 (deg), unwinding 0..1 and band fill 0..1."""
    R = DC.DIAL_R * _r_screen(min(t, 3.92)) / DC.DIAL_R
    u = _k(t, UNWIND[0], UNWIND[1], "inout")
    fill = _k(t, FILL[0], FILL[1], "inout")
    rot = -90.0 + _dial(t, w)
    # each click: a ratchet kick that settles (the spiral snaps), then the inward flow
    for tc in CLICKS[1:]:
        rot += bass.settle(t, tc, amp=11.0, freq=5.5, decay=9.0) + 14.0 * _k(t, tc, 0.10, "outback")
    flow = max(0.0, t - CLICKS[2])
    rot += 70.0 * flow + 26.0 * flow * flow                   # clockwise = the arms flow inward
    sc = 1.0 + 0.24 * _k(t, 4.6, 2.6, "inout")              # the Vertigo push
    for tc in CLICKS[1:]:
        if t > tc:
            sc *= 1.0 - 0.085 * math.exp(-(t - tc) / 0.10) * min(1.0, (t - tc) / 0.02)
    kc = _k(t, COLLAPSE[0], COLLAPSE[1], "in3")
    sc *= 1.0 - kc
    rot += 540.0 * _k(t, COLLAPSE[0], COLLAPSE[1], "in")
    return R, sc, rot, u, fill


def _spiral_polys(t, w):
    """The dial's ticks, lifted, unwound and widened into a spiral rule (screen px)."""
    R, sc, rot, u, fill = _spiral_state(t, w)
    if sc <= 1e-3:
        return []
    span = 1.0 + u * (TURNS_SP - 1.0)                       # angular stretch of the ring

    def at(sv, depth_frac, shrink):
        th = math.radians(rot - 360.0 * sv * span)
        r = R * (1.0 - u * sv * (1.0 - RHO)) * sc
        rr = r - depth_frac * R * sc * shrink
        return (C[0] + rr * math.cos(th), C[1] + rr * math.sin(th))
    out = []
    band = 0.105
    for i in range(_TICKS):
        sv = ((_TICKS - i) % _TICKS) / float(_TICKS)
        shrink = (1.0 - u * sv * (1.0 - RHO)) ** 0.75
        d0 = _tick_depth(i)
        d1 = 0.21 if i == 0 else max(band, d0 * 0.9 if i % 5 == 0 else band)
        depth = lerp(d0, d1, fill)
        half = lerp(_tick_half(i) / (2.0 * _TICKS), 0.5 / _TICKS * 1.08, fill)   # in turns of the ring
        hin = half * lerp(0.55, 1.0, fill)                    # a notch narrows inward
        j = 1.2 * (hash01(i, 3) - 0.5)
        p = [at(sv - half, 0.0, shrink), at(sv + half, 0.0, shrink), at(sv + hin, depth, shrink),
             at(sv - hin, depth, shrink)]
        out.append([(x + j, y - j) for x, y in p])
    return out


def _index_wedge(t, w):
    """The bezel's index notch lifted as a PAPER wedge at the top, pointing at the spiral."""
    R, sc, rot, u, fill = _spiral_state(t, w)
    pop = bass.pop(t, INK_IN[0], 0.22)
    kick = 1.0 + sum(0.28 * math.exp(-(t - tc) / 0.09) for tc in CLICKS[1:] if t > tc)
    s = pop * kick * (1.0 - _k(t, COLLAPSE[0], COLLAPSE[1], "in3"))
    if s <= 1e-3:
        return None
    k = 1.0 - _k(t, COLLAPSE[0], COLLAPSE[1], "in3")
    y = C[1] - R * 1.24 * lerp(1.0, 0.0, 1.0 - k)
    h, wd = 0.15 * R * s, 0.11 * R * s
    return [(C[0] - wd, y - h), (C[0] + wd, y - h), (C[0], y + 0.15 * h)]


_NUM_H = 92.0


def _num_xs(gap=0.95):
    """Centres of 7 · 14 · 29 set as one centred line (equal gaps between the numbers)."""
    ws = [bass.title_width(str(n), height=_NUM_H, tracking=0.06) for n in COMBO]
    g = gap * _NUM_H
    x = C[0] - (sum(ws) + g * (len(ws) - 1)) / 2.0
    out = []
    for wd in ws:
        out.append(x + wd / 2.0)
        x += wd + g
    return tuple(out), g


_NUM_XS, _NUM_GAP = _num_xs()


def _numerals(f, t, w):
    """The combination stamps below the spiral on each click: 7 · 14 · 29."""
    kc = _k(t, COLLAPSE[0], COLLAPSE[1], "in3")
    if kc >= 1.0:
        return
    xs = _NUM_XS
    y = 1650.0
    with f.screen() as c:
        for i, (n, tc) in enumerate(zip(COMBO, CLICKS)):
            ts = max(tc, INK_IN[0] + 0.06)
            if t < ts:
                continue
            Tt = bass.title_glyphs(str(n), height=_NUM_H, tracking=0.06, seed=40 + i, rough=1.0, jitter=0.6)
            p = (lerp(xs[i], C[0], kc), lerp(y, C[1], kc))
            bass.draw_title(c, Tt, p, PAPER, u=_k(t, ts, 0.20, "linear"), anim="stamp", big=1.8,
                            scale=1.0 - kc)
            if i > 0:
                gx = xs[i] - bass.title_width(str(n), height=_NUM_H, tracking=0.06) / 2.0 - _NUM_GAP / 2.0
                dp = (lerp(gx, C[0], kc), lerp(y, C[1], kc))
                r = 9.0 * bass.pop(t, ts + 0.05, 0.2) * (1.0 - kc)
                if r > 0.5:
                    bass.disc(c, dp, r, PAPER, seed=60 + i)


def _graphic(f, t, w):
    """The ink field and the Bass spiral over the live shot."""
    k_ink = _k(t, INK_IN[0], INK_IN[1], "inout")
    iris = _k(t, IRIS[0], IRIS[1], "out3")
    if k_ink <= 0.0 or iris >= 1.0:
        return
    f.post["paper"] = 0.55 * k_ink * (1.0 - iris)
    with f.screen() as c:
        c.save()
        c.rectangle(0, 0, 1080, 1920)
        if iris > 0:
            draw.poly(c, bass.ring_pts(C, 1150.0 * iris, seed=21, n=64))
            c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        c.set_source_rgba(*INK, k_ink)
        c.fill()
        c.restore()
        polys = _spiral_polys(t, w)
        if polys:
            bass.fill_polys(c, [bass.orient(p, True) for p in polys], PAPER)
    if t < INK_IN[0] + INK_IN[1] + 0.02:
        _glove_ghost(f, t, w, 1.0 - k_ink)
    with f.screen() as c:
        wedge = _index_wedge(t, w)
        if wedge:
            bass.fill_polys(c, [wedge], PAPER)
    _numerals(f, t, w)


def render(f, t, T):
    w = _words(T)
    live = t < INK_IN[0] + INK_IN[1] + 0.02 or t >= IRIS[0]
    if live:
        _live(f, t, w)
    else:
        f.fill(INK)
    _graphic(f, t, w)


def motion_blur(t, T):
    w = _words(T)
    if w["birthday"] + 0.03 < t < CLICKS[0] - 0.02:      # the first spin (live)
        return 3
    if 7.92 < t < 8.16:                                    # the door sweeps past the lens
        return 3
    return 1


def cues(T):
    w = _words(T)
    return [
        Cue(0.55, "rubber glove on iron: fingers settle on the knob", -16, pan=0.3, dur=0.5),
        Cue(0.90, "dial turns a few notches: soft ratchet", -18, dur=0.15),
        Cue(w["didnt"], "the turning stops dead (silence under the voice)", -24),
        Cue(w["birthday"], "dial spin right: fast ratchet whirr", -10, dur=0.4),
        Cue(CLICKS[0], "tumbler click 1 (heavy, close): the room drops away", -4),
        Cue(INK_IN[0], "Bass interlude: plucked col legno ostinato starts", -10, dur=3.3),
        Cue(CLICKS[0] + 0.02, "dial spin left: ratchet whirr", -12, dur=0.68),
        Cue(CLICKS[1], "tumbler click 2", -4),
        Cue(CLICKS[1] + 0.02, "dial spin right: ratchet whirr", -12, dur=0.68),
        Cue(CLICKS[2], "tumbler click 3 (the last: a deeper clunk)", -3),
        Cue(CLICKS[2] + 0.1, "Vertigo swirl: rising string glissando", -12, dur=1.9),
        Cue(COLLAPSE[0], "everything sucked to a point: reversed whoosh", -8, dur=0.35),
        Cue(DOOR[0], "the safe door: bolts withdraw, a heavy iron creak", -6, dur=0.8),
        Cue(7.95, "the door sweeps past: water push, low thump", -9, dur=0.3),
        Cue(BEAM[0], "the beam finds the book: a soft held note", -14, dur=1.2),
    ]
