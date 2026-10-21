"""Shared sets used by several scenes. Fixed layouts in world coords = continuity.

LINEUP  - police lineup room (S1, S16)
OFFICE  - the detective's office (S5, S14, S15; the evidence board also S10)
crowd_top() - river of umbrellas seen from above (S2, S7, S9, S17)
street()    - wet street at night (S2, S11, S13, S17)
apartment() - the last juror's building (S12, S13)
"""
import math

from .core import WHITE, AMBER, CRIMSON, BLUE, hash01, fbm1, clamp
from . import draw, props


# ----------------------------------------------------------------------------- lineup room
LINEUP = dict(
    floor_y=1400.0,
    xs=[180.0, 360.0, 540.0, 720.0, 900.0],       # five standing positions (hip x)
    chart_top=960.0,
    bulb_anchor=(540.0, 430.0), cord=330.0,
    glass=(40.0, 380.0, 1000.0, 1460.0),            # one-way glass frame (x0,y0,x1,y1)
)


def lineup_room(f, alpha=1.0, glass=True):
    """Height-chart wall (lines only, no numbers), floor, optional one-way glass frame."""
    fy, top = LINEUP["floor_y"], LINEUP["chart_top"]
    n = 12
    for i in range(n + 1):
        y = fy - (fy - top) * i / n
        major = i % 3 == 0
        draw.line(f, (60, y), (1020, y), 2.6 if major else 1.3, WHITE, alpha * (0.7 if major else 0.38))
    draw.line(f, (-200, fy), (1280, fy), 3.4, WHITE, alpha)
    for x in LINEUP["xs"]:
        draw.line(f, (x - 30, fy + 26), (x + 30, fy + 26), 2.0, WHITE, alpha * 0.45)   # floor marks
    if glass:
        x0, y0, x1, y1 = LINEUP["glass"]
        draw.rect(f, x0, y0, x1 - x0, y1 - y0, 3.0, WHITE, alpha * 0.55)
        draw.line(f, (x0 + 60, y0 + 40), (x0 + 200, y0 + 180), 1.6, WHITE, alpha * 0.25)   # glass glint
        draw.line(f, (x0 + 60, y0 + 90), (x0 + 140, y0 + 170), 1.2, WHITE, alpha * 0.2)


# ----------------------------------------------------------------------------- office
OFFICE = dict(
    floor_y=1560.0, ceil_y=380.0,
    door=(40.0, 860.0, 210.0, 700.0),               # x, y, w, h  (left wall)
    rack_x=330.0,                                   # coat rack with THE red umbrella
    board=(300.0, 500.0, 400.0, 330.0),             # evidence board x, y, w, h
    window=(730.0, 470.0, 280.0, 470.0),            # blinds window x, y, w, h
    desk=(400.0, 1290.0, 600.0, 270.0),             # x, top_y, w, front-panel height
    lamp=(930.0, 1290.0),
    watch=(560.0, 1276.0),                          # the pocket watch lies here (stopped 3:07)
    chair_x=700.0,
)


def coat_rack(f, x, floor_y, alpha=1.0, umbrella=True, umbrella_color=CRIMSON, t=0.0):
    top = floor_y - 540
    draw.line(f, (x, floor_y), (x, top), 4.0, WHITE, alpha)
    for dx in (-46, 46):
        draw.line(f, (x, floor_y - 8), (x + dx, floor_y), 3.0, WHITE, alpha)
    for dx in (-34, 34):
        draw.bezier(f, (x, top + 30), (x + dx * 0.6, top + 20), (x + dx, top + 10), (x + dx, top + 34), 3.0, WHITE, alpha)
    draw.circle(f, (x, top - 8), 8, 3.0, WHITE, alpha)
    if umbrella:
        hook = (x + 34, top + 34)
        sway = 2.0 * fbm1(t * 0.4, 5)
        props.umbrella(f, (hook[0] + 2, hook[1] + 14), angle=90 + sway, R=118, open_=0.0,
                       color=umbrella_color, alpha=alpha, handle=True)
    return (x + 34, top + 34)


def desk(f, alpha=1.0):
    x, ty, w, h = OFFICE["desk"]
    draw.line(f, (x - 20, ty), (x + w + 20, ty), 4.0, WHITE, alpha)
    draw.line(f, (x, ty + 10), (x + w, ty + 10), 2.0, WHITE, alpha * 0.6)
    draw.rect(f, x, ty + 10, w, h - 10, 3.0, WHITE, alpha)
    draw.line(f, (x + w * 0.62, ty + 10), (x + w * 0.62, ty + h), 2.0, WHITE, alpha * 0.7)
    for k in range(3):
        yy = ty + 40 + k * 70
        draw.rect(f, x + w * 0.66, yy, w * 0.3, 50, 2.0, WHITE, alpha * 0.7)
        draw.line(f, (x + w * 0.79, yy + 25), (x + w * 0.83, yy + 25), 3.0, WHITE, alpha * 0.8)


def desk_lamp(f, on=1.0, t=0.0, alpha=1.0):
    bx, by = OFFICE["lamp"]
    draw.line(f, (bx - 40, by - 4), (bx + 40, by - 4), 3.0, WHITE, alpha)
    draw.line(f, (bx, by - 4), (bx - 30, by - 120), 3.0, WHITE, alpha)
    draw.line(f, (bx - 30, by - 120), (bx - 90, by - 170), 3.0, WHITE, alpha)
    shade = [(bx - 120, by - 150), (bx - 60, by - 200), (bx - 40, by - 172), (bx - 100, by - 122)]
    draw.stroke(f, shade, 3.0, WHITE, alpha, closed=True)
    lp = (bx - 88, by - 132)
    if on > 0:
        draw.glow_dot(f, lp, 140, AMBER, 0.45 * on * alpha, core=False)
        draw.circle(f, lp, 9, 1, AMBER, on * alpha, fill_it=True, glow=1.0)
    return lp


def chair(f, x, floor_y, facing=1, alpha=1.0):
    seat_y = floor_y - 220
    draw.line(f, (x - 70, seat_y), (x + 70, seat_y), 3.4, WHITE, alpha)
    bx = x - facing * 70
    draw.line(f, (bx, seat_y), (bx, seat_y - 230), 3.4, WHITE, alpha)
    draw.line(f, (x - 60, seat_y), (x - 70, floor_y), 3.0, WHITE, alpha)
    draw.line(f, (x + 60, seat_y), (x + 70, floor_y), 3.0, WHITE, alpha)
    return seat_y


def door(f, open_=0.0, alpha=1.0, light=None):
    x, y, w, h = OFFICE["door"]
    draw.rect(f, x, y, w, h, 3.4, WHITE, alpha)
    if open_ <= 0:
        draw.rect(f, x + 26, y + 30, w - 52, h * 0.42, 2.0, WHITE, alpha * 0.6)
        draw.circle(f, (x + w - 30, y + h * 0.55), 9, 2.6, WHITE, alpha)
    else:
        ww = w * (1 - 0.82 * open_)
        if light:
            draw.fill(f, [(x + ww, y), (x + w, y), (x + w, y + h), (x + ww, y + h)], light, 0.25 * open_, glow=0.8)
        draw.stroke(f, [(x, y), (x + ww, y + 26 * open_), (x + ww, y + h - 26 * open_), (x, y + h)], 3.4, WHITE, alpha, closed=True)


def office(f, t=0.0, alpha=1.0, umbrella=True, lamp_on=1.0, door_open=0.0, door_light=None,
           blinds_tilt=0.55, board=True, window_light=AMBER, window_light_alpha=0.16, stripes_offset=0.0):
    """The detective's office, full set. Draw figures/props after (or between) as needed.
    window_light: color of the light leaking through the blinds (AMBER streetlight by default,
    BLUE / CRIMSON for police strobes). Returns dict of anchor points."""
    fy, cy = OFFICE["floor_y"], OFFICE["ceil_y"]
    draw.line(f, (-300, fy), (1380, fy), 3.4, WHITE, alpha)
    draw.line(f, (-300, cy), (1380, cy), 2.4, WHITE, alpha * 0.6)
    wx, wy, ww, wh = OFFICE["window"]
    if window_light is not None and window_light_alpha > 0:
        quad = [(wx + 10, wy + 20), (wx + ww, wy + 10), (wx - 120, fy - 40), (wx - 520, fy + 30)]
        props.blind_light(f, quad, n=10, duty=0.45, color=window_light, alpha=window_light_alpha,
                          glow=0.4, offset=stripes_offset)
    props.blinds(f, wx, wy, ww, wh, slats=13, tilt=blinds_tilt, alpha=alpha)
    if board:
        bx, by, bw, bh = OFFICE["board"]
        props.board(f, bx, by, bw, bh, alpha)
    door(f, door_open, alpha, light=door_light)
    hook = coat_rack(f, OFFICE["rack_x"], fy, alpha, umbrella=umbrella, t=t)
    desk(f, alpha)
    lp = desk_lamp(f, lamp_on, t, alpha)
    return dict(lamp=lp, hook=hook, watch=OFFICE["watch"])


# ----------------------------------------------------------------------------- street
def street(f, ground_y=1500.0, x0=-400.0, x1=1480.0, alpha=1.0, crosswalk=False, curb_drop=46.0):
    """Sidewalk edge + curb + road line. ground_y is the sidewalk where figures stand."""
    draw.line(f, (x0, ground_y), (x1, ground_y), 3.4, WHITE, alpha)
    draw.line(f, (x0, ground_y + curb_drop), (x1, ground_y + curb_drop), 2.4, WHITE, alpha * 0.7)
    for k in range(int((x1 - x0) / 160)):
        xx = x0 + k * 160
        draw.line(f, (xx, ground_y), (xx + 20, ground_y + curb_drop), 1.4, WHITE, alpha * 0.25)
    if crosswalk:
        for k in range(7):
            xx = 160 + k * 120
            draw.rect(f, xx, ground_y + curb_drop + 30, 70, 120, 2.0, WHITE, alpha * 0.5)


def skyline(f, ground_y, seed=3, x0=-300, x1=1380, t=0.0, alpha=0.5, lw=2.2, lit=0.14, depth_scale=1.0):
    """A row of background towers (dimmer, thinner lines = atmospheric depth)."""
    x = x0
    i = 0
    while x < x1:
        w = (160 + 160 * hash01(seed, i)) * depth_scale
        h = (700 + 1100 * hash01(seed, i, 1)) * depth_scale
        roof = ("flat", "water", "antenna", "tower")[int(hash01(seed, i, 2) * 4)]
        props.building(f, x, ground_y, w, h, seed=seed * 100 + i, lit=lit, t=t, alpha=alpha, lw=lw, roof=roof)
        x += w + 18 * depth_scale
        i += 1


# ----------------------------------------------------------------------------- crowds
def crowd_top(f, t, area=(60.0, -200.0, 1020.0, 2120.0), n=46, seed=1, speed=70.0, R=(46.0, 60.0),
              two_way=True, red=None, alpha=1.0, highlight=None, highlight_color=AMBER,
              highlight_amt=0.0, slowmo=1.0):
    """River of umbrellas seen from straight above. Deterministic lanes.
    red: dict(index=i, reverse=True/False, amount=0..1) - that umbrella becomes THE red one
         (CRIMSON fill fades in by `amount`) and may walk against the flow.
    highlight: callable(i, x, y) -> bool  marks umbrellas to tint with highlight_color.
    Returns list of (x, y, R) per umbrella."""
    x0, y0, x1, y1 = area
    span = (y1 - y0) + 300
    out = []
    for i in range(n):
        lane = x0 + (x1 - x0) * hash01(seed, i)
        r = R[0] + (R[1] - R[0]) * hash01(seed, i, 1)
        d = 1 if (not two_way or hash01(seed, i, 2) < 0.6) else -1
        v = speed * (0.75 + 0.5 * hash01(seed, i, 3)) * slowmo
        is_red = red is not None and red.get("index") == i
        if is_red and red.get("reverse"):
            d = -1
        y = y0 - 150 + ((hash01(seed, i, 4) * span + d * v * t) % span)
        x = lane + 10 * fbm1(t * 0.4 + i, seed + i)
        rot = 22.5 * hash01(seed, i, 5) + 6 * fbm1(t * 0.5, seed + 3 * i)
        out.append((x, y, r))
        if is_red and red.get("amount", 1.0) > 0:
            k = red.get("amount", 1.0)
            props.umbrella_top(f, (x, y), r * 1.04, rot, WHITE, alpha=alpha * (1 - k))
            props.umbrella_top(f, (x, y), r * 1.04, rot, CRIMSON, alpha=alpha * k)
            continue
        hl = highlight is not None and highlight(i, x, y) and highlight_amt > 0
        if hl:
            props.umbrella_top(f, (x, y), r, rot, WHITE, alpha=alpha * (1 - highlight_amt))
            props.umbrella_top(f, (x, y), r, rot, highlight_color, fill_alpha=0.35, alpha=alpha * highlight_amt)
        else:
            props.umbrella_top(f, (x, y), r, rot, WHITE, alpha=alpha)
    return out


# ----------------------------------------------------------------------------- apartment
APARTMENT = dict(x=180.0, w=560.0, h=1500.0, cols=4, rows=9, juror=(2, 2))


def apartment(f, ground_y=1560.0, juror_on=1.0, t=0.0, alpha=1.0, others_lit=0.12):
    """The last juror's building. Her window (col 2, row 2 from the top) is lit until 3:07.
    Returns the juror window center (world)."""
    a = APARTMENT
    ov = {a["juror"]: juror_on}
    for ci in range(a["cols"]):
        for ri in range(a["rows"]):
            if (ci, ri) != a["juror"]:
                ov[(ci, ri)] = 1.0 if hash01(77, ci, ri) < others_lit else 0.0
    rect = props.building(f, a["x"], ground_y, a["w"], a["h"], seed=77, t=t, alpha=alpha, lw=3.2,
                          roof="water", cols=a["cols"], rows=a["rows"], lit_override=ov)
    x, top, w, h = rect
    # stoop + door
    draw.rect(f, x + w / 2 - 60, ground_y - 190, 120, 190, 3.0, WHITE, alpha)
    draw.line(f, (x + w / 2 - 110, ground_y - 4), (x + w / 2 + 110, ground_y - 4), 3.0, WHITE, alpha)
    mx, my = w * 0.12, 60.0
    cw = (w - 2 * mx) / a["cols"]
    rh = (h - my - 40) / a["rows"]
    ci, ri = a["juror"]
    return (x + mx + ci * cw + cw / 2, top + my + ri * rh + rh * 0.26)
