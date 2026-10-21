"""Shared helpers for s14_the_mirror and s15_blue_lights.

Everything here is a pure function of its arguments (no state between frames).
World coordinates are the shared OFFICE set (sets.OFFICE): the evidence board, its clue
cards, the red strings and the round mirror sit at the same place in both scenes, so the
board seen in s15 is exactly the board s14 left behind (photo torn away, strings taut).
"""
import math

import cairo

from engine import *

OF = sets.OFFICE
FLOOR = OF["floor_y"]
BX, BY, BW, BH = OF["board"]
BC = (BX + BW / 2.0, BY + BH / 2.0)          # (500, 665): board centre == mirror centre
MIRROR_R = 50.0                              # props.mirror outer ring = 1.12 * r = 56
CARD_W, CARD_H = 124.0, 152.0                # "the killer's portrait", pinned over the mirror
CORNER = dict(tl=(BC[0] - 52.0, BC[1] - 66.0), tr=(BC[0] + 52.0, BC[1] - 66.0),
              br=(BC[0] + 52.0, BC[1] + 66.0), bl=(BC[0] - 52.0, BC[1] + 66.0))

RAIN_C, RAIN_WH = (372.0, 580.0), (92.0, 104.0)          # rain-cloud icon card (top left)
WATCH_C, WATCH_R = (628.0, 594.0), 36.0                  # his pocket watch, 3:07 (top right)
FOOT_C, FOOT_WH = (628.0, 760.0), (92.0, 100.0)          # short-long footprint card (bottom right)
VBL_C, VBL_WH = (372.0, 762.0), (80.0, 96.0)             # victim photo (bottom left)
VML_C, VMR_C, VM_WH = (343.0, 670.0), (657.0, 670.0), (48.0, 60.0)   # small victim photos
PIN = dict(rain=(372.0, 534.0), watch=(628.0, 546.0), foot=(628.0, 716.0), vbl=(372.0, 720.0),
           vml=(343.0, 646.0), vmr=(657.0, 646.0), top=(500.0, 528.0), bot=(500.0, 802.0))
# (anchor pin, other end in the loose web, corner of the portrait it converges on, stagger)
STRINGS = [("rain", "watch", "tl", 0.00), ("top", "foot", "tr", 0.30), ("watch", "vbl", "tr", 0.12),
           ("vmr", "vml", "br", 0.42), ("foot", "vbl", "br", 0.18), ("bot", "rain", "bl", 0.36),
           ("vbl", "vml", "bl", 0.06), ("vml", "top", "tl", 0.24)]
FOOT_PRINTS = [("l", (-13.0, 30.0)), ("r", (11.0, 9.0)), ("l", (-13.0, -36.0))]   # short gap, long gap

DESK_X, DESK_TOP, DESK_W, DESK_H = OF["desk"]
WINDOW = OF["window"]
DOOR = OF["door"]


# ----------------------------------------------------------------------------- small utils
def box_poly(c, w, h, ang=0.0, s=1.0):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        x, y = x * s, y * s
        out.append((c[0] + x * ca - y * sa, c[1] + x * sa + y * ca))
    return out


def clip_outside(polys):
    """path_fn for f.clipped(): everything EXCEPT the given polygons (even-odd)."""
    def fn(c):
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        c.rectangle(-20000, -20000, 40000, 40000)
        for pts in polys:
            c.move_to(*pts[0])
            for p in pts[1:]:
                c.line_to(*p)
            c.close_path()
    return fn


def rect_poly(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def circle_poly(c, r, n=28):
    return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def cone_zone(apex, ang, spread, length, margin):
    """Polygon covering a light cone plus `margin` around it (keeps other accents out of it)."""
    a = math.radians(ang)
    d = (math.cos(a), math.sin(a))
    back = (apex[0] - d[0] * margin, apex[1] - d[1] * margin)
    half = math.radians(spread / 2) + math.atan2(margin, max(length, 1.0))
    pts = [back]
    for i in range(9):
        th = a - half + 2 * half * i / 8
        pts.append((apex[0] + (length + margin) * math.cos(th), apex[1] + (length + margin) * math.sin(th)))
    p1 = (back[0] + margin * math.cos(a - math.pi / 2), back[1] + margin * math.sin(a - math.pi / 2))
    p2 = (back[0] + margin * math.cos(a + math.pi / 2), back[1] + margin * math.sin(a + math.pi / 2))
    return [p2] + pts + [p1]


# Zones kept free of other accent light so colours never mix in a pixel (palette QA):
BOARD_ZONE = rect_poly(BX - 50, BY - 50, BX + BW + 60, BY + BH + 40)       # crimson pins / strings / X
UMB_BOX = rect_poly(300.0, 1000.0, 440.0, 1330.0)                         # THE red umbrella on the rack


def window_stripes(f, color, alpha, offset=0.0, exclude=(), glow=0.4):
    """Exactly sets.office's blind-light stripes (same quad, props.blind_light), drawn with dark
    zones so an accent never lands on another accent (no amber on crimson pins, no crimson
    across a blue beam). Call it BEFORE sets.office(window_light=None) so the blinds sit on top."""
    if color is None or alpha <= 0:
        return
    wx, wy, ww, wh = WINDOW
    quad = [(wx + 10, wy + 20), (wx + ww, wy + 10), (wx - 120, FLOOR - 40), (wx - 520, FLOOR + 30)]
    if exclude:
        with f.clipped(clip_outside(exclude)):
            props.blind_light(f, quad, n=10, duty=0.45, color=color, alpha=alpha, glow=glow, offset=offset)
    else:
        props.blind_light(f, quad, n=10, duty=0.45, color=color, alpha=alpha, glow=glow, offset=offset)


def clip_circle(c0, r):
    return lambda c: c.arc(c0[0], c0[1], r, 0, 2 * math.pi)


def afterglow(fn, t, decay=0.12, span=0.36, step=1.0 / 96.0):
    """Max of fn(t - d) * exp(-d / decay) over d in [0, span] - a xenon-style flash
    with a short afterglow (keeps 24 fps strobes readable, never aliased)."""
    best = 0.0
    n = int(span / step)
    for j in range(n + 1):
        d = j * step
        v = fn(t - d)
        if v > 0:
            best = max(best, v * math.exp(-d / decay))
    return best


def strobe(t, rate=1.45, decay=0.11):
    """Police light bar (core.siren double-flash pattern) with afterglow -> (blue, red)."""
    b = afterglow(lambda x: siren(x, rate)[0], t, decay)
    r = afterglow(lambda x: siren(x, rate)[1], t, decay)
    return b, r


def stripe_quads(offset, n=10, duty=0.45):
    """The exact light stripes sets.office() throws through the blinds (for Light.poly)."""
    wx, wy, ww, wh = WINDOW
    tl, tr, br, bl = (wx + 10, wy + 20), (wx + ww, wy + 10), (wx - 120, FLOOR - 40), (wx - 520, FLOOR + 30)
    out = []
    for i in range(n):
        a0 = (i + offset) / n
        a1 = (i + offset + duty) / n
        if a0 >= 1:
            continue
        a1 = min(a1, 1.0)
        out.append([lerp(tl, bl, a0), lerp(tr, br, a0), lerp(tr, br, a1), lerp(tl, bl, a1)])
    return out


# ----------------------------------------------------------------------------- clue cards
def _cloud_pts(c, k=1.0):
    circ = [(-16.0, 4.0, 12.0), (0.0, -6.0, 17.0), (17.0, 3.0, 11.0)]
    top, bot = [], []
    for i in range(33):
        x = -28.0 + 56.0 * i / 32
        tops = [cy - math.sqrt(max(0.0, r * r - (x - cx) ** 2)) for cx, cy, r in circ if abs(x - cx) <= r]
        bots = [cy + math.sqrt(max(0.0, r * r - (x - cx) ** 2)) for cx, cy, r in circ if abs(x - cx) <= r]
        if not tops:
            continue
        top.append((c[0] + x * k, c[1] + min(tops) * k))
        bot.append((c[0] + x * k, c[1] + min(13.0, max(bots)) * k))
    return top + bot[::-1]


def rain_card(f, flash=0.0, alpha=1.0):
    c = RAIN_C
    w, h = RAIN_WH
    draw.rect(f, c[0] - w / 2, c[1] - h / 2, w, h, 2.6, WHITE, alpha)
    draw.rect(f, c[0] - w / 2 + 7, c[1] - h / 2 + 7, w - 14, h - 14, 1.2, WHITE, alpha * 0.45)
    cl = _cloud_pts((c[0], c[1] - 12))
    drops = [((c[0] + x, c[1] + 12 + (i % 2) * 5), (c[0] + x - 6, c[1] + 28 + (i % 2) * 5))
             for i, x in enumerate((-18.0, -6.0, 6.0, 18.0))]
    if flash > 0:
        draw.glow_dot(f, (c[0], c[1] - 6), 66, AMBER, 0.34 * flash * alpha, core=False)
        draw.fill(f, cl, AMBER, 0.85 * flash * alpha, glow=0.75 * flash)
    draw.stroke(f, cl, 2.6, WHITE, alpha, closed=True)
    for a, b in drops:
        draw.line(f, a, b, 2.4, WHITE, alpha)
        if flash > 0:
            draw.line(f, a, b, 2.6, AMBER, alpha * flash, glow=1.0 * flash)
    if flash > 0:
        draw.rect(f, c[0] - w / 2, c[1] - h / 2, w, h, 2.6, AMBER, alpha * flash, glow=0.7 * flash)


def foot_card(f, lights=(0.0, 0.0, 0.0), alpha=1.0):
    c = FOOT_C
    w, h = FOOT_WH
    draw.rect(f, c[0] - w / 2, c[1] - h / 2, w, h, 2.6, WHITE, alpha)
    mx = c[0] + 33
    draw.line(f, (mx, c[1] + 30), (mx, c[1] - 36), 1.3, WHITE, 0.55 * alpha)
    for _, (dx, dy) in FOOT_PRINTS:
        draw.line(f, (mx - 5, c[1] + dy), (mx + 5, c[1] + dy), 1.3, WHITE, 0.7 * alpha)
    for (side, (dx, dy)), k in zip(FOOT_PRINTS, lights):
        pc = (c[0] + dx, c[1] + dy)
        props.footprint(f, pc, angle=-90, side=side, s=0.5, alpha=alpha, w=2.2)
        if k > 0:
            draw.glow_dot(f, pc, 34, AMBER, 0.5 * k * alpha, core=False)
            props.footprint(f, pc, angle=-90, side=side, s=0.5, alpha=alpha * k, w=2.6, color=AMBER, wet=k)
    kk = max(lights)
    if kk > 0:
        draw.rect(f, c[0] - w / 2, c[1] - h / 2, w, h, 2.6, AMBER, alpha * kk, glow=0.6 * kk)


def watch(f, flash=0.0, alpha=1.0):
    chain = [(654.0, 548.0), (680.0, 604.0), (668.0, 648.0)]
    props.clock_face(f, WATCH_C, WATCH_R, 3, 7, style="pocket", chain=chain, alpha=alpha)
    if flash > 0:
        draw.glow_dot(f, WATCH_C, WATCH_R * 2.3, AMBER, 0.4 * flash * alpha, core=False)
        props.clock_face(f, WATCH_C, WATCH_R, 3, 7, w=3.4, color=AMBER, alpha=alpha * flash,
                         style="pocket", glow=1.0 * flash)


def portrait(f, c=BC, ang=0.0, s=1.0, alpha=1.0):
    """The killer's portrait: a faceless head-and-shoulders photo (props.photo_card)."""
    props.photo_card(f, c, CARD_W, CARD_H, angle=ang, s=s, pinned=False, alpha=alpha)


def tear_fragments(f, u, alpha=1.0):
    """Paper flecks thrown off the four corners when the photo rips (u: 0..1 over ~0.45 s)."""
    if u <= 0 or u >= 1:
        return
    sx, sy = CARD_W / 2, CARD_H / 2
    for i in range(12):
        kx, ky = ((-1, -1), (1, -1), (1, 1), (-1, 1))[i % 4]
        ang = math.atan2(ky, kx) + (hash01(31, i) - 0.5) * 1.6
        d = (18 + 60 * hash01(31, i, 1)) * ease("out3", u)
        c = (BC[0] + kx * sx + math.cos(ang) * d, BC[1] + ky * sy + math.sin(ang) * d + 40 * u * u)
        draw.stroke(f, box_poly(c, 7 + 5 * hash01(31, i, 2), 4 + 3 * hash01(31, i, 3), 400 * u * (hash01(31, i, 4) - 0.5)),
                    1.4, WHITE, alpha * (1 - u), closed=True)


def torn_scraps(f, alpha=1.0):
    """Little triangles of photo left under the four corner pins after the tear."""
    sx, sy = CARD_W / 2, CARD_H / 2
    for (kx, ky) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        cx, cy = BC[0] + kx * sx, BC[1] + ky * sy
        pts = [(cx, cy), (cx - kx * 24, cy), (cx - kx * 15, cy - ky * 7), (cx - kx * 9, cy - ky * 12),
               (cx, cy - ky * 26)]
        draw.stroke(f, pts, 1.8, WHITE, alpha * 0.8, closed=True)


def string_ends(conv):
    """(anchor, end) world points of every red string at convergence progress conv 0..1."""
    out = []
    for anchor, start, corner, dl in STRINGS:
        k = ease("inout3", clamp((conv - dl * 0.5) / 0.5))
        out.append((PIN[anchor], lerp(PIN[start], CORNER[corner], k), k))
    return out


def red_strings(f, t, conv=0.0, sag=0.085, vib=0.0, alpha=1.0, w=2.6, sway=1.0):
    for i, (a, b, k) in enumerate(string_ends(conv)):
        sg = sag * (1.0 - k) + 0.006 * sway * math.sin(t * 1.3 + i * 1.7) * (1.0 - k)
        props.red_string(f, [a, b], sag=sg, w=w, alpha=alpha, t=t + i * 0.37, vib=vib)


def clip_poly(pts):
    def fn(c):
        c.move_to(*pts[0])
        for p in pts[1:]:
            c.line_to(*p)
        c.close_path()
    return fn


def crimson_dimmed(f, zone, k, draw_fn):
    """draw_fn(alpha) for crimson props: full strength outside `zone`; inside it (where an AMBER
    clue flash lights the board) the crimson is washed out while the flash is strong and only
    returns once the amber has faded (k < 0.22), so amber and crimson are never comparable in
    one pixel (that mix is an off-palette orange)."""
    if zone is None or k <= 0.01:
        draw_fn(1.0)
        return
    with f.clipped(clip_outside([zone])):
        draw_fn(1.0)
    a = 1.0 - smoothstep(0.1, 0.22, k)
    if a > 0.004:
        with f.clipped(clip_poly(zone)):
            draw_fn(a)


PIN_S = 0.72


def pins(f, alpha=1.0, corners=True, anchors=True):
    if anchors:
        for k in ("rain", "watch", "top", "bot", "foot", "vbl", "vml", "vmr"):
            props.pin(f, PIN[k], s=PIN_S, alpha=alpha)
    if corners:
        for k in ("tl", "tr", "br", "bl"):
            props.pin(f, CORNER[k], s=PIN_S, alpha=alpha)


def board_cards(f, flash_rain=0.0, flash_watch=0.0, foot_lights=(0.0, 0.0, 0.0), alpha=1.0):
    rain_card(f, flash_rain, alpha)
    watch(f, flash_watch, alpha)
    foot_card(f, foot_lights, alpha)
    # their pins are drawn by pins() (same spots), so a clue flash can wash them out with the strings
    props.photo_card(f, VBL_C, VBL_WH[0], VBL_WH[1], crossed=1.0, alpha=alpha, pinned=False)
    props.photo_card(f, VML_C, VM_WH[0], VM_WH[1], crossed=1.0, alpha=alpha, pinned=False)
    props.photo_card(f, VMR_C, VM_WH[0], VM_WH[1], crossed=1.0, alpha=alpha, pinned=False)


# ----------------------------------------------------------------------------- the mirror
def reflection(f, t, s_ref, head_y, tilt=0.0, alpha=1.0, bob=0.0, glass=1.0, c=BC, R=MIRROR_R):
    """His own hollow head and shoulders inside the mirror (front view), clipped to the glass.
    head_y: head centre offset in mirror radii (negative = up)."""
    hy = c[1] + head_y * R + bob
    # bust pose: upper arms spread like the shoulders of the portrait photo, forearms hanging
    p = Pose(x=c[0], y=hy + 156.0 * s_ref, s=s_ref, facing=0, la=56, le=-44, ra=56, re=-44, head=tilt)
    p = rig.breathe(p, t, 0.35, seed=41)
    with f.clipped(clip_circle(c, R * 0.965)):
        if glass > 0:   # the blinds behind him, reflected: two faint amber bands across the glass
            for i in range(2):
                y0 = c[1] - 0.15 * R + i * 0.62 * R
                band = [(c[0] - 1.3 * R, y0 + 0.35 * R), (c[0] + 1.3 * R, y0 - 0.45 * R),
                        (c[0] + 1.3 * R, y0 - 0.27 * R), (c[0] - 1.3 * R, y0 + 0.53 * R)]
                draw.fill(f, band, AMBER, 0.07 * glass)
        J = rig.draw_figure(f, p, alpha=alpha)
    return J


def glint_sweep(f, u, alpha=1.0, c=BC, R=MIRROR_R):
    """A diagonal highlight sweeping across the glass, u: 0..1."""
    if u <= 0 or u >= 1:
        return
    with f.clipped(clip_circle(c, R * 0.965)):
        x = c[0] + (-1.5 + 3.0 * u) * R
        a = alpha * math.sin(math.pi * u)
        draw.line(f, (x - 0.9 * R, c[1] + 0.9 * R), (x + 0.9 * R, c[1] - 0.9 * R), 5, WHITE, 0.55 * a, glow=0.9 * a)
        draw.line(f, (x - 0.55 * R, c[1] + 0.9 * R), (x + 1.25 * R, c[1] - 0.9 * R), 2, WHITE, 0.4 * a, glow=0.5 * a)


# ----------------------------------------------------------------------------- the detective
def detective_rest(x=540.0, s=2.0):
    """Front view, standing on the office floor (hip y ~ 1252 at s=2)."""
    return rig.stand(x, FLOOR, facing=0, s=s)


def surrender(p):
    """Hands-up target. Starts from rig.hands_up(p) but opens the elbows outward: in front view
    the preset's upper arms (la=150) pass through the head ring, which reads as a rig glitch."""
    return rig.hands_up(p).copy(la=118.0, le=48.0, ra=118.0, re=48.0)


def forearm_angle(J, side):
    """Screen angle (deg) of a forearm, elbow -> hand."""
    e, h = J[side + "e"], J[side + "h"]
    return math.degrees(math.atan2(h[1] - e[1], h[0] - e[0]))


def flashlight(f, hand, ang, on=1.0, s=1.0, alpha=1.0):
    """A plain police flashlight (white body, BLUE lens). Returns the lens point."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    tail = (hand[0] - ux * 18 * s, hand[1] - uy * 18 * s)
    lens = (hand[0] + ux * 30 * s, hand[1] + uy * 30 * s)
    draw.line(f, tail, lens, 7.0 * s ** 0.5, WHITE, alpha)
    draw.circle(f, lens, 6.5 * s, 1, BLUE, alpha * (0.4 + 0.6 * on), fill_it=True, glow=1.2 * on)
    return lens


def board_after(f, t, glass_color=None, glass_v=0.0, alpha=1.0):
    """The board exactly as s14 leaves it: photo torn away, strings taut on the mirror's pins."""
    board_cards(f, alpha=alpha)
    props.mirror(f, BC, MIRROR_R, alpha=alpha, glint=0.3)
    if glass_color is not None and glass_v > 0:
        draw.circle(f, BC, MIRROR_R, 1, glass_color, 0.22 * glass_v * alpha, fill_it=True, glow=0.9 * glass_v)
    torn_scraps(f, alpha)
    red_strings(f, t, conv=1.0, alpha=alpha)
    pins(f, alpha=alpha)


def smear(f, cam_fn, t, draw_fn, frames=2.2, cap=520.0, n=14, soften=True):
    """Whip-pan motion streak WITHOUT f.whip's wrap-around (f.whip uses np.roll, so content near
    one edge bleeds onto the opposite edge). draw_fn(alpha) is drawn under n cameras sampled
    along the real camera path over a virtual shutter of `frames` frames (streak capped at `cap`
    screen px), each at 1/n opacity, then softened so the samples merge into one streak.
    Returns the streak length in screen px (0 = no smear needed)."""
    c0 = cam_fn(t)
    p = c0.to_world((W / 2, H / 2))
    dt = 1.0 / 48.0
    a, b = cam_fn(t - dt).to_screen(p), cam_fn(t + dt).to_screen(p)
    v = math.hypot(a[0] - b[0], a[1] - b[1]) * 24.0                 # screen px per second
    span = frames / 24.0
    if v * span > cap:
        span = cap / v
    length = v * span
    if length < 8:
        draw_fn(1.0)
        return 0.0
    k = max(4, min(n, int(length / 20) + 2))
    spacing = length / k

    def body():
        for i in range(k):
            ts = t + span * ((i + 0.5) / k - 0.5)
            with f.camera(cam_fn(ts)):
                draw_fn(1.0 / k)
    if soften and spacing > 7.0:          # samples further apart than a line width: merge them
        with f.blurred(clamp(0.45 * spacing, 6.0, 14.0)):     # >= 6 px keeps f.blurred downsampled
            body()
    else:
        body()
    return length
