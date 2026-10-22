"""SALVAGE sets - G. PROPS. Every prop is a filled silhouette drawn on a cairo ctx in world
coords; (x, y) is a documented anchor, `angle` in degrees (clockwise on screen), `s` scale.
They return a dict of useful world points (hand grips, glints, line attachment...).

    a, c = bell_swing(t, seed=1)                    # current sway + lagging clapper
    pts = draw_bell(ctx, x, y, angle=a, clapper=c)   # (x, y) = top of the crown loop
    g = draw_knife(ctx, x, y, angle=-30)            # g["glint"] -> f.emit flash
    x, y, ang, landed = sink(t, t0=2.0, p0=(...), floor_y=seabed_y(...))
"""
import math

from engine import draw
from engine.core import clamp, lerp, hash01, noise1, smoothstep

from .sets_common import (PAL, INK, RED, mix, shape, put, paint, oriented, round_rect, hole_circle,
                          solid_circle, ell, xf, sway, lit_paper)


def _col(color):
    return color if color is not None else INK


def _frame(ctx, x, y, angle, s, flip=False):
    ctx.save()
    ctx.translate(x, y)
    if angle:
        ctx.rotate(math.radians(angle))
    ctx.scale(-s if flip else s, s)


def _pt(x, y, angle, s, p, flip=False):
    px = -p[0] if flip else p[0]
    return xf((px, p[1]), x, y, angle, s)


# ----------------------------------------------------------------------------- the bell
BELL_H = 160.0          # crown top to lip, world px at s = 1 (a 45 cm ship's bell)


def _bell_body(c):
    # crown loop (see-through)
    solid_circle(c, (0, 13), 13)
    hole_circle(c, (0, 13), 6.5)
    draw.poly(c, oriented([(-9, 20), (9, 20), (11, 30), (-11, 30)]))
    # shoulder -> waist -> flared sound bow -> lip
    pts = [(-30, 30), (-22, 26), (0, 24), (22, 26), (30, 30), (36, 44), (37, 70), (40, 96), (49, 118), (61, 134),
           (66, 142), (60, 146), (0, 141), (-60, 146), (-66, 142), (-61, 134), (-49, 118), (-40, 96), (-37, 70),
           (-36, 44)]
    draw.smooth(c, oriented(pts), close=True, tension=0.42)
    # the lip bead (a slim ridge that catches the outline)
    draw.poly(c, oriented([(-67, 136), (67, 136), (69, 143), (-69, 143)]))


def draw_bell(ctx, x, y, angle=0.0, clapper=0.0, s=1.0, color=None, yoke=False):
    """The ship's BELL. (x, y) = top of the crown loop (hang it from a hook/bracket there).
    angle: swing of the bell (0 = plumb); clapper: clapper angle relative to the bell
    (swings independently; its ball shows under the lip). yoke: draw a small mounting yoke
    above the loop (when it hangs on the wreck's bracket).
    Returns dict(crown, lip (centre of the mouth), ball (clapper ball), top)."""
    col = _col(color)
    _frame(ctx, x, y, angle, s)
    ctx.new_path()
    ctx.append_path(shape("bell_body", _bell_body))
    if yoke:
        round_rect(ctx, -26, -10, 26, 2, 4)
        draw.poly(ctx, oriented([(-4, -2), (4, -2), (4, 8), (-4, 8)]))
    # clapper: rod + ball, pivoting just under the crown
    ctx.save()
    ctx.translate(0, 34)
    ctx.rotate(math.radians(clapper))
    draw.capsule(ctx, (0, 0), (0, 104), 4.5, 5.5)
    solid_circle(ctx, (0, 112), 13)
    ctx.restore()
    ctx.restore()
    paint(ctx, col)
    a = math.radians(clapper)
    ball_local = (math.sin(-a) * 112, 34 + math.cos(a) * 112)
    return dict(top=(x, y), crown=_pt(x, y, angle, s, (0, 13)), lip=_pt(x, y, angle, s, (0, 141)),
                ball=_pt(x, y, angle, s, ball_local))


def bell_swing(t, seed=1, amp=5.0, period=4.6, clapper_gain=2.6):
    """(bell_angle, clapper_angle) for a bell hanging in the current: a slow sway, the
    clapper lagging and overshooting (so it reads as a separate, heavy part)."""
    a = sway(t, seed, amp, period)
    a_lag = sway(t - 0.55, seed, amp, period)
    cl = -(a - a_lag) * clapper_gain + 1.5 * noise1(t * 0.6, seed + 77)
    return a, cl


def bell_haul(t, t0, t1, p0, p1, jerk=0.0, seed=2):
    """Bell hanging from a hauled line, rising from p0 (at t0) to p1 (at t1):
    returns (x, y, angle, clapper). jerk > 0 adds the winch's pull-and-swing rhythm."""
    u = clamp((t - t0) / max(t1 - t0, 1e-6))
    e = u * u * (3 - 2 * u)
    x = lerp(p0[0], p1[0], e)
    y = lerp(p0[1], p1[1], e)
    pull = jerk * math.sin(t * 5.2) * (1 - abs(2 * u - 1)) if 0 < u < 1 else 0.0
    y -= pull * 14
    ang = 4.0 * math.sin(t * 1.3 + seed) * (0.4 + 0.6 * (0 < u < 1)) + pull * 3
    cl = -6.0 * math.sin(t * 1.3 + seed - 0.7) - pull * 9
    return x, y, ang, cl


# ----------------------------------------------------------------------------- safe
SAFE = dict(w=250.0, h=310.0, door=(22.0, 30.0, 228.0, 270.0), dial=(125.0, 112.0, 34.0),
            handle=(125.0, 200.0, 26.0), hinge_x=18.0)


def _safe_body(c):
    w, h = SAFE["w"], SAFE["h"]
    for fx in (16, w - 44):                                   # feet
        round_rect(c, fx, h - 6, fx + 28, h + 16, 4)
    round_rect(c, -6, h - 30, w + 6, h, 6)                    # plinth
    round_rect(c, 0, 0, w, h - 24, 16)                        # body
    round_rect(c, -5, -10, w + 5, 12, 7)                      # top moulding
    for hy in (60, 220):                                      # hinge knuckles proud of the side
        round_rect(c, -14, hy, 4, hy + 46, 5)


def draw_safe(ctx, x, y, angle=0.0, s=1.0, door=0.0, lit=0.0, dial_angle=0.0, color=None, inside=None,
              light=None):
    """The captain's iron SAFE. (x, y) = top-left corner of the body (local box 250 x 310,
    feet below). angle = 90 lays it on its side (as found in the capsized cabin).
    door: 0 shut .. 1 swung wide open on its left hinge (shows the dark inside).
    lit: 0..1 the lamp lights its front face (dial, handle and door seam become readable).
    inside: callable(ctx) drawing what is inside (local coords, door opening 22..228 x 30..270).
    Returns dict(dial (world centre), handle, door_edge, inside_centre)."""
    col = _col(color)
    light = light or PAL.light
    _frame(ctx, x, y, angle, s)
    ctx.new_path()
    ctx.append_path(shape("safe_body", _safe_body))
    paint(ctx, col)
    x0, y0, x1, y1 = SAFE["door"]
    if lit > 0:
        face = mix(col, mix(PAL.fog_at(0.6), light, 0.45), 0.55 * lit)
        round_rect(ctx, 0, 0, SAFE["w"], SAFE["h"] - 24, 16)
        ctx.set_source_rgb(*face)
        ctx.fill()
        # door seam + recess (ink, thin), drawn as the gap around the door
        round_rect(ctx, x0 - 6, y0 - 6, x1 + 6, y1 + 6, 10)
        round_rect(ctx, x0, y0, x1, y1, 7, hole=True)
        paint(ctx, mix(col, face, 0.25))
    op = clamp(door)
    if op > 0:
        round_rect(ctx, x0, y0, x1, y1, 7)                    # the dark inside
        paint(ctx, mix(col, (0, 0, 0), 0.5))
        if inside is not None:
            ctx.save()
            ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
            ctx.clip()
            inside(ctx)
            ctx.restore()
        # the door, swung toward the camera on its left hinge: narrows, then shows its edge
        a = op * math.pi * 0.62
        wd = (x1 - x0) * math.cos(a)
        th = 34 * math.sin(a)
        dx0, dx1 = x0 - th * 0.6, x0 + wd
        pts = [(x0, y0 - 4), (dx1, y0 - 4 - 30 * math.sin(a)), (dx1, y1 + 4 + 30 * math.sin(a)), (x0, y1 + 4)]
        if wd < 0:
            pts = [(x0, y0 - 4), (x0 - th, y0 - 10 - 20 * math.sin(a)), (dx1, y0 - 4 - 30 * math.sin(a)),
                   (dx1, y1 + 4 + 30 * math.sin(a)), (x0 - th, y1 + 10 + 20 * math.sin(a)), (x0, y1 + 4)]
        draw.poly(ctx, oriented(pts))
        paint(ctx, col)
        dial_c = ((x0 + dx1) / 2 if wd > 0 else dx1 + 20, SAFE["dial"][1])
    else:
        dial_c = SAFE["dial"][:2]
    if op < 0.35:
        dx, dy, dr = SAFE["dial"]
        cx = dx if op <= 0 else lerp(x0, x0 + (x1 - x0) * math.cos(op * math.pi * 0.62), (dx - x0) / (x1 - x0))
        sq = math.cos(op * math.pi * 0.62) if op > 0 else 1.0
        ctx.save()
        ctx.translate(cx, dy)
        ctx.scale(sq, 1.0)
        _dial_small(ctx, dr, dial_angle)
        ctx.restore()
        hx, hy, hr = SAFE["handle"]
        hxx = hx if op <= 0 else lerp(x0, x0 + (x1 - x0) * sq, (hx - x0) / (x1 - x0))
        ctx.save()
        ctx.translate(hxx, hy)
        ctx.scale(sq, 1.0)
        _handle_small(ctx, hr, dial_angle * 0.0)
        ctx.restore()
        paint(ctx, col)
    ctx.restore()
    return dict(dial=_pt(x, y, angle, s, SAFE["dial"][:2]), handle=_pt(x, y, angle, s, SAFE["handle"][:2]),
                door_edge=_pt(x, y, angle, s, (x1, (y0 + y1) / 2)),
                inside_centre=_pt(x, y, angle, s, ((x0 + x1) / 2, (y0 + y1) / 2)))


def _dial_small(c, r, ang):
    """Small-scale dial: knurled disc + index bump (appends paths, local centre 0,0)."""
    n = 28
    pts = []
    for i in range(n * 2):
        a = math.radians(ang) + math.pi * i / n
        rr = r * (1.0 if i % 2 == 0 else 0.9)
        pts.append((math.cos(a) * rr, math.sin(a) * rr))
    draw.poly(c, oriented(pts))
    draw.poly(c, oriented([(-5, -r - 12), (5, -r - 12), (0, -r - 3)]))


def _handle_small(c, r, ang):
    solid_circle(c, (0, 0), r * 0.32)
    for k in range(3):
        a = math.radians(ang) + 2 * math.pi * k / 3 - math.pi / 2
        draw.capsule(c, (0, 0), (math.cos(a) * r, math.sin(a) * r), 4, 3.5)
        solid_circle(c, (math.cos(a) * r, math.sin(a) * r), 7)


# ----------------------------------------------------------------------------- the big dial (S09)
def dial_tick_angle(number, ticks=100, zero_at=-90.0, dial_angle=0.0):
    """Screen angle (deg) where dial number `number` sits for a given dial rotation."""
    return zero_at + dial_angle + 360.0 * number / ticks


def dial_angle_for(number, ticks=100, index_at=-90.0, zero_at=-90.0):
    """Dial rotation that puts `number` under the index mark (for keyframing the combination)."""
    return index_at - zero_at - 360.0 * number / ticks


def draw_dial(ctx, c, r, dial_angle=0.0, ticks=100, index_at=-90.0, face=None, color=None, knob=True,
              lit=1.0):
    """Close-up safe DIAL (S09): a fixed bezel with the index notch, the rotating dial ring
    with `ticks` notches cut into its rim (every 10th long, every 5th medium, zero a deep
    vee), a knurled centre knob. c = centre (world), r = outer radius of the dial ring.
    Draw the lamp-lit door surface behind it first (face colour shows through the notches);
    pass face=rgb to also paint a disc of door surface under the dial.
    dial_angle: rotation (deg, clockwise); index_at: screen angle of the index mark.
    Returns dict(index = world point of the index mark, number_under_index (float))."""
    col = _col(color)
    cx, cy = c
    if face is not None:
        solid_circle(ctx, c, r * 1.45)
        ctx.set_source_rgb(*face)
        ctx.fill()
    # fixed bezel ring with the index notch (a vee cut into its outer edge)
    ia = math.radians(index_at)
    ring_o, ring_i = r * 1.30, r * 1.06
    pts = []
    n = 180
    for i in range(n):
        a = 2 * math.pi * i / n
        d = abs(math.atan2(math.sin(a - ia), math.cos(a - ia)))
        notch = max(0.0, 1 - d / 0.055) * r * 0.16
        pts.append((cx + math.cos(a) * (ring_o - notch), cy + math.sin(a) * (ring_o - notch)))
    draw.poly(ctx, oriented(pts))
    inner = [(cx + math.cos(2 * math.pi * i / 90) * ring_i, cy + math.sin(2 * math.pi * i / 90) * ring_i)
             for i in range(90)]
    draw.poly(ctx, oriented(inner, cw=False))
    paint(ctx, col)
    # the rotating ring: notches cut into its rim
    pts = []
    da = math.radians(dial_angle)
    zero = math.radians(-90.0)
    for i in range(ticks):
        a0 = zero + da + 2 * math.pi * i / ticks
        depth = r * (0.20 if i % 10 == 0 else 0.13 if i % 5 == 0 else 0.075)
        half = (math.pi / ticks) * (0.34 if i % 10 else 0.42)
        if i == 0:
            depth, half = r * 0.30, math.pi / ticks * 0.9
        for a, rr in ((a0 - math.pi / ticks, r), (a0 - half, r), (a0 - half * 0.55, r - depth), (a0 + half * 0.55, r - depth),
                      (a0 + half, r), ):
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    draw.poly(ctx, oriented(pts))
    paint(ctx, col)
    if knob:
        # a gap ring between dial and knob (face shows), then the knurled knob
        if face is not None:
            solid_circle(ctx, c, r * 0.66)
            ctx.set_source_rgb(*mix(face, col, 0.55))
            ctx.fill()
        n = 40
        kp = []
        for i in range(n * 2):
            a = da + math.pi * i / n
            rr = r * (0.56 if i % 2 == 0 else 0.52)
            kp.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        draw.poly(ctx, oriented(kp))
        paint(ctx, col)
        if face is not None:            # a sheen arc on the knob: a lit sliver, reads as metal
            ctx.new_path()
            ctx.arc(cx, cy, r * 0.42, math.radians(200), math.radians(250))
            ctx.set_line_width(r * 0.05)
            ctx.set_source_rgba(*face, 0.45 * lit)
            ctx.stroke()
    num = ((index_at - (-90.0) - dial_angle) / 360.0 * ticks) % ticks
    return dict(index=(cx + math.cos(ia) * ring_o, cy + math.sin(ia) * ring_o), number_under_index=num)


# ----------------------------------------------------------------------------- paper props
def _book_pages(c, open_):
    sp = 6.0 * open_
    for side in (-1, 1):
        pts = [(side * sp, 4), (side * 150, -2), (side * 154, 6), (side * 152, 108), (side * sp, 112)]
        if side > 0:
            draw.smooth(c, oriented(pts), close=True, tension=0.25)
        else:
            draw.smooth(c, oriented(pts), close=True, tension=0.25)


def draw_logbook(ctx, x, y, angle=0.0, s=1.0, open_=1.0, light=1.0, scribble=0.55, color=None):
    """The ship's LOGBOOK. open_=1: lying open, two pale pages (lit by `light`) on a dark
    cover; faint hand-written lines (not legible) if scribble > 0. open_=0: closed (a dark
    slab with pale page edges). (x, y) = centre of the spine at the top edge; book 310 x 120.
    Returns dict(left_page, right_page (centres), spine)."""
    col = _col(color)
    pale = lit_paper(light)
    _frame(ctx, x, y, angle, s)
    if open_ > 0.5:
        round_rect(ctx, -164, -8, 164, 124, 8)               # cover
        paint(ctx, col)
        ctx.new_path()
        _book_pages(ctx, 1.0)
        draw.linear(ctx, (-160, 0), (160, 0), [(0, pale, 1), (0.46, mix(pale, col, 0.35), 1),
                                                (0.54, mix(pale, col, 0.35), 1), (1, pale, 1)])
        ctx.fill()
        if scribble > 0:
            for side in (-1, 1):
                for i in range(9):
                    yy = 16 + i * 10.5
                    xa = side * 18
                    L = 112 - 30 * hash01(i, side, 3)
                    pts = []
                    for k in range(14):
                        u = k / 13
                        pts.append((xa + side * L * u, yy + 1.4 * math.sin(u * 23 + i * 2.1 + side)))
                    ctx.new_path()
                    ctx.move_to(*pts[0])
                    for p in pts[1:]:
                        ctx.line_to(*p)
                    ctx.set_line_width(1.6)
                    ctx.set_source_rgba(*col, 0.55 * scribble)
                    ctx.stroke()
    else:
        round_rect(ctx, -82, -8, 82, 124, 8)
        paint(ctx, col)
        round_rect(ctx, 74, 0, 80, 116, 2)
        paint(ctx, mix(col, pale, 0.6))
    ctx.restore()
    return dict(left_page=_pt(x, y, angle, s, (-78, 55)), right_page=_pt(x, y, angle, s, (78, 55)),
                spine=(x, y))


def draw_photo(ctx, x, y, angle=0.0, s=1.0, light=1.0, color=None):
    """An old PHOTO: white-bordered print (130 x 96) showing, in silhouette, a captain in his
    cap with a small boy at his side (the diver as a child). (x, y) = centre."""
    col = _col(color)
    pale = lit_paper(light)
    _frame(ctx, x, y, angle, s)
    round_rect(ctx, -65, -48, 65, 48, 3)
    paint(ctx, pale)
    img = mix(pale, col, 0.28)
    round_rect(ctx, -56, -39, 56, 34, 1)
    paint(ctx, img)
    ink = mix(col, img, 0.15)
    # the captain: shoulders, head, peaked cap
    draw.poly(ctx, oriented([(-44, 34), (-40, 0), (-28, -8), (-8, -8), (4, 0), (8, 34)]))
    solid_circle(ctx, (-18, -18), 10)
    draw.poly(ctx, oriented([(-31, -24), (-6, -27), (-4, -21), (2, -19), (-30, -19)]))
    # the boy: small, at his side, looking up
    draw.poly(ctx, oriented([(14, 34), (16, 12), (24, 7), (34, 8), (40, 14), (42, 34)]))
    solid_circle(ctx, (28, 0), 7.5)
    paint(ctx, ink)
    ctx.restore()
    return dict(centre=(x, y))


def draw_envelope(ctx, x, y, angle=0.0, s=1.0, pale=0.0, fat=1.0, color=None):
    """Fat ENVELOPE of cash (160 x 92, flap up). (x, y) = centre. pale 0..1 lightens it
    toward lit paper (it is ink by default, read by its flap notch and bulge).
    Returns dict(grip = where a hand holds it (left end))."""
    col = mix(_col(color), lit_paper(1.0), clamp(pale))
    _frame(ctx, x, y, angle, s)
    b = 6 * fat
    pts = [(-80, -46), (80, -46), (82 + b * 0.5, 0), (80, 46), (0, 46 + b), (-80, 46), (-82 - b * 0.5, 0)]
    draw.smooth(ctx, oriented(pts), close=True, tension=0.18)
    paint(ctx, col)
    # flap edge: a thin notch line that lets the shape read as an envelope
    ctx.new_path()
    ctx.move_to(-78, -44)
    ctx.line_to(0, 6)
    ctx.line_to(78, -44)
    ctx.set_line_width(4.0)
    ctx.set_source_rgb(*mix(col, PAL.sky_bottom if pale < 0.5 else INK, 0.55))
    ctx.stroke()
    # bank strap
    round_rect(ctx, 22, -48, 40, 48 + b, 2)
    paint(ctx, mix(col, INK, 0.5) if pale > 0.3 else mix(col, PAL.sky_bottom, 0.25))
    ctx.restore()
    return dict(grip=_pt(x, y, angle, s, (-66, 0)), centre=(x, y))


# ----------------------------------------------------------------------------- knife
def _knife(c):
    # handle with finger grooves, guard, clip-point blade (pointing +x), pommel
    draw.smooth(c, oriented([(-118, -8), (-108, -12), (-90, -10), (-78, -13), (-62, -10), (-46, -12), (-30, -10),
                             (-30, 10), (-46, 12), (-62, 9), (-78, 13), (-90, 10), (-108, 12), (-118, 8)]),
                close=True, tension=0.3)
    solid_circle(c, (-120, 0), 10)
    round_rect(c, -32, -20, -22, 20, 3)
    draw.poly(c, oriented([(-23, -10), (60, -11), (96, -6), (128, 2), (104, 1), (88, 9), (40, 11), (-23, 10)]))


def _sheath(c):
    draw.smooth(c, oriented([(-22, -14), (70, -14), (120, -6), (140, 2), (122, 10), (70, 15), (-22, 15)]),
                close=True, tension=0.25)
    round_rect(c, -34, -18, -20, 18, 3)
    draw.poly(c, oriented([(-10, -14), (6, -14), (6, -30), (-10, -30)]))       # belt loop


def draw_knife(ctx, x, y, angle=0.0, s=1.0, sheathed=False, flip=False, color=None):
    """The client's KNIFE. Drawn: (x, y) = the grip centre (where the hand closes), blade
    toward +x rotated by angle. Sheathed: (x, y) = the belt-loop end of the sheath, the
    handle out of the sheath's mouth. Returns dict(glint = world point for an emissive
    highlight (blade spine near the tip), tip, grip)."""
    col = _col(color)
    _frame(ctx, x, y, angle, s, flip)
    ctx.new_path()
    if sheathed:
        ctx.append_path(shape("sheath", _sheath))
        ctx.save()
        ctx.translate(-14, 0)
        ctx.scale(0.55, 0.8)
        ctx.translate(-10, 0)
        ctx.restore()
        draw.smooth(ctx, oriented([(-100, -9), (-40, -10), (-22, -11), (-22, 11), (-40, 10), (-100, 9)]), close=True,
                    tension=0.3)
        solid_circle(ctx, (-102, 0), 9)
        paint(ctx, col)
        ctx.restore()
        return dict(glint=_pt(x, y, angle, s, (-102, -6), flip), tip=_pt(x, y, angle, s, (140, 2), flip),
                    grip=_pt(x, y, angle, s, (-60, 0), flip))
    ctx.save()
    ctx.translate(74, 0)          # local knife origin is mid-handle (-74 in shape coords)
    ctx.append_path(shape("knife", _knife))
    ctx.restore()
    paint(ctx, col)
    ctx.restore()
    return dict(glint=_pt(x, y, angle, s, (74 + 90, -8), flip), tip=_pt(x, y, angle, s, (74 + 128, 2), flip),
                grip=(x, y))


def knife_glint(f, p, t, t0, dur=0.35, size=1.0):
    """A quick emissive star-glint at world point p, peaking at t0 (moonlight on steel)."""
    u = (t - t0) / dur
    if u < -1 or u > 1:
        return
    a = max(0.0, 1 - abs(u)) ** 1.5
    with f.emit() as G:
        draw.glow_disc(G, p, 34 * size, PAL.moon, 0.9 * a)
        for ang in (0, 90):
            G.save()
            G.translate(*p)
            G.rotate(math.radians(ang + 20))
            G.scale(70 * size * a + 1, 2.2 * size)
            G.arc(0, 0, 1, 0, 2 * math.pi)
            G.restore()
            G.set_source_rgba(*PAL.moon, 0.9 * a)
            G.fill()


# ----------------------------------------------------------------------------- diving lead
def _weight(c):
    """Chest/back lead weight: a heavy rounded slab with a hanging lug."""
    solid_circle(c, (0, -6), 12)
    hole_circle(c, (0, -6), 6)
    draw.smooth(c, oriented([(-46, 6), (46, 6), (54, 30), (50, 92), (30, 112), (0, 118), (-30, 112), (-50, 92),
                             (-54, 30)]), close=True, tension=0.35)


def draw_lead_weight(ctx, x, y, angle=0.0, s=1.0, color=None):
    """A diver's lead WEIGHT (the pair hangs on chest and back). (x, y) = the lug."""
    col = _col(color)
    _frame(ctx, x, y, angle, s)
    ctx.new_path()
    ctx.append_path(shape("weight", _weight))
    ctx.restore()
    paint(ctx, col)


def _boot(c):
    """Lead diving boot, toe toward +x, sole on y = 0, ankle opening up."""
    draw.smooth(c, oriented([(-40, -150), (24, -150), (30, -96), (52, -70), (96, -52), (118, -30), (120, -12),
                             (-58, -12), (-60, -60), (-46, -100)]), close=True, tension=0.3)
    round_rect(c, -66, -16, 128, 4, 5)          # lead sole
    round_rect(c, 84, -46, 126, -8, 10)         # toe cap
    round_rect(c, -48, -136, 32, -118, 4)       # strap


def draw_lead_boot(ctx, x, y, angle=0.0, s=1.0, flip=False, color=None):
    """A lead diving BOOT. (x, y) = sole centre; flip mirrors (toe to -x)."""
    col = _col(color)
    _frame(ctx, x, y, angle, s, flip)
    ctx.new_path()
    ctx.append_path(shape("boot", _boot))
    ctx.restore()
    paint(ctx, col)


def sink(t, t0, p0, v0=(0.0, 0.0), floor_y=None, vt=520.0, spin=140.0, seed=0, drift=60.0):
    """Trajectory of a heavy object released at t0 from p0 underwater: accelerates to the
    terminal velocity vt (px/s) with drag, tumbles (spin deg/s, decaying), drifts a little,
    and lands on floor_y (settles with a small rock). Returns (x, y, angle, landed_time or
    None). Before t0 it stays at p0."""
    if t <= t0:
        return p0[0], p0[1], 0.0, None
    tau = 0.45                      # drag time constant
    dt = t - t0
    y = p0[1] + vt * (dt - tau * (1 - math.exp(-dt / tau))) + v0[1] * tau * (1 - math.exp(-dt / tau))
    x = p0[0] + v0[0] * tau * (1 - math.exp(-dt / tau)) + drift * noise1(dt * 0.4, seed)
    ang = spin * tau * 2.0 * (1 - math.exp(-dt / (tau * 2.0))) * (1 if hash01(seed) > 0.5 else -1)
    landed = None
    if floor_y is not None and y >= floor_y:
        # solve landing time numerically (monotonic)
        lo, hi = t0, t
        for _ in range(30):
            mid = (lo + hi) / 2
            dm = mid - t0
            ym = p0[1] + vt * (dm - tau * (1 - math.exp(-dm / tau))) + v0[1] * tau * (1 - math.exp(-dm / tau))
            if ym < floor_y:
                lo = mid
            else:
                hi = mid
        landed = hi
        xl, _, angl, _ = sink(landed - 1e-4, t0, p0, v0, None, vt, spin, seed, drift)
        settle = math.exp(-(t - landed) * 3.0) * math.sin((t - landed) * 9.0) * 6.0
        return xl, floor_y, angl * 0.3 + settle, landed
    return x, y, ang, landed


# ----------------------------------------------------------------------------- rope, hook, cap
def _hook_shape(c):
    solid_circle(c, (0, 0), 10)
    hole_circle(c, (0, 0), 5)
    draw.smooth(c, oriented([(-6, 8), (6, 8), (7, 34), (17, 50), (15, 66), (0, 76), (-17, 70), (-22, 54), (-15, 49),
                             (-9, 60), (0, 64), (7, 57), (5, 45), (-6, 34)]), close=True, tension=0.3)


def draw_hook(ctx, x, y, angle=0.0, s=1.0, color=None):
    """The lifting line's cargo HOOK. (x, y) = the eye (tie the line here).
    Returns dict(eye, throat = where a load's ring sits)."""
    col = _col(color)
    _frame(ctx, x, y, angle, s)
    ctx.new_path()
    ctx.append_path(shape("hook_big", _hook_shape))
    ctx.restore()
    paint(ctx, col)
    return dict(eye=(x, y), throat=_pt(x, y, angle, s, (0, 66)))


def draw_rope_coil(ctx, x, y, s=1.0, turns=5, color=None):
    """A coil of rope lying on deck/silt, seen from the side: stacked loops. (x, y) = the
    bottom centre."""
    col = _col(color)
    _frame(ctx, x, y, 0.0, s)
    for i in range(turns):
        ell(ctx, (2 * (i % 2) - 1, -5 - i * 9.5), 74 - i * 3.5, 8)
    draw.poly(ctx, oriented([(-74, -5), (74, -5), (74 - turns * 3.5, -5 - turns * 9.5), (-74 + turns * 3.5,
                                                                                        -5 - turns * 9.5)]))
    ctx.restore()
    paint(ctx, col)


def draw_captain_cap(ctx, x, y, angle=0.0, s=1.0, color=None):
    """The captain's peaked cap lying in the silt of his cabin. (x, y) = bottom centre."""
    col = _col(color)
    _frame(ctx, x, y, angle, s)
    draw.smooth(ctx, oriented([(-60, -14), (-50, -40), (-10, -52), (40, -50), (64, -36), (58, -16), (30, -12)]),
                close=True, tension=0.35)
    draw.poly(ctx, oriented([(-62, -16), (30, -14), (82, -4), (78, 2), (-60, -2)]))     # peak
    round_rect(ctx, -56, -24, 56, -12, 3)                                                # band
    ctx.restore()
    paint(ctx, col)
