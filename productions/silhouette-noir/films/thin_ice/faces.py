"""THIN ICE: the close-ups. Profiles cut like cameos, a frontal girl (the photograph and the match
cut), eyes, hands, boots and the props seen up close (the watch, the music box, the scrap).

    F.mother(c, at, s, look=0.0, lid=1.0, fear=0.0, t=t)     # her profile, facing right
    F.girl(c, at, s, look=0.0, t=t, scarf=1.0)                 # the girl's profile (the red scarf)
    F.guard(c, at, s, look=0.0, hat=True, wet=0.0, t=t)        # the guard's profile
    F.eyes(c, who, at, s, look=(dx, dy), lid=1.0, fear=0.0)    # a frontal strip of face: two eyes
    F.front_girl(c, at, s, scarf=K.RED, look=(0, 0))           # the girl face-on (photo / match cut)
    F.mitten(c, wrist, tip, s, who=...) / F.glove(c, wrist, tip, s, curl=...)
    F.boot(c, at, s, who, pitch=0.0)                          # a boot in profile, the sole at `at`
    F.watch(c, at, r, t, lid=1.0, hands=(11, 58), wet=0.0)    # the pocket watch, face-on
    F.music_box(c, at, s, open_u, t, spin)                    # the box, its lid, the paper dancer
    F.scrap(c, at, s, t)                                      # the torn scrap of her coat on a barb

Profiles face right (facing=-1 flips them) and are drawn in face units (the head about 600 tall),
scaled by s px per unit; `at` is the anchor in frame px: the front of the neck's base. Each
returns landmarks in frame px: 'eye', 'mouth', 'nose', 'chin', 'top'. rim: the moonlit edge
(offset toward `light`); edge: the colour of the thin cut lines inside the silhouette (where the
headscarf meets the cheek, the hat's fold).
"""
import math
from functools import lru_cache

from engine import bass, draw as D
from engine.core import clamp, ease, hash01, lerp
from films.thin_ice import kit as K


def spline(pts, n=8, closed=True):
    """A Catmull-Rom curve through pts, n samples per span."""
    P = list(pts)
    m = len(P)
    out = []
    spans = m if closed else m - 1
    for i in range(spans):
        p0 = P[(i - 1) % m] if closed else P[max(i - 1, 0)]
        p1, p2 = P[i % m], P[(i + 1) % m]
        p3 = P[(i + 2) % m] if closed else P[min(i + 2, m - 1)]
        for k in range(n):
            u = k / n
            u2, u3 = u * u, u * u * u
            out.append(tuple(0.5 * ((2 * b) + (-a + c_) * u + (2 * a - 5 * b + 4 * c_ - d) * u2 + (-a + 3 * b - 3 * c_ + d) * u3)
                             for a, b, c_, d in zip(p0, p1, p2, p3)))
    if not closed:
        out.append(P[-1])
    return out


@lru_cache(maxsize=None)
def _shape(pts, seed, sag=1.2, amp=0.8, max_len=46.0, corner=40.0):
    """A cut-paper outline through control points (curved by a spline, then scissor-cut)."""
    return bass.orient(bass.scissor(spline(pts), seed=seed, sag=sag, amp=amp, max_len=max_len, corner=corner), True)


@lru_cache(maxsize=None)
def _poly(pts, seed):
    """A straight-cut polygon (corners kept)."""
    return bass.orient(bass.scissor(list(pts), seed=seed, sag=0.6, amp=0.6, max_len=60.0, corner=12.0), True)


@lru_cache(maxsize=None)
def _fur(pts, seed, depth=7.0, step=9.0):
    """A fur edge round a spline outline: the outline, notched every `step` units."""
    base = spline(pts, n=10)
    out = []
    for i, (a, b) in enumerate(zip(base, base[1:] + base[:1])):
        L = math.dist(a, b)
        k = max(1, int(L / step))
        nx, ny = (b[1] - a[1]) / (L or 1.0), -(b[0] - a[0]) / (L or 1.0)
        for j in range(k):
            u = j / k
            d = depth * (hash01(seed, i, j) * 0.8 + 0.2) * (1 if j % 2 else -0.3)
            out.append((lerp(a[0], b[0], u) + nx * d, lerp(a[1], b[1], u) + ny * d))
    return bass.orient(out, True)


def _fill(c, polys, color, alpha=1.0):
    bass.fill_polys(c, polys, color, alpha)


def _line(c, pts, color, width, alpha=1.0, taper=(1.0, 1.0)):
    bass.line_band(c, pts, color, width=width, alpha=alpha, taper=taper)


def _eye(c, centre, w, h, look=0.0, lid=1.0, fear=0.0, down=0.0, color=K.PAPER, pupil=K.INK, light=None):
    """An almond eye in profile (facing +x). look -1..1: the pupil from back to front; down
    -1..1: up .. down; lid 0..1 opens it; fear 0..1 opens it wide (white all round a small
    pupil). light: an extra colour washed over the white (the lantern's light), or None."""
    x, y = centre
    if lid <= 0.04:
        _line(c, [(x - w * 0.5, y + 1.0), (x + w * 0.6, y + 2.0)], K.INK, max(3.0, h * 0.3))
        return
    hh = h * lid * (1.0 + 0.45 * fear)
    up, lo = hh * (1.0 - 0.25 * max(0.0, down)), hh * (1.0 + 0.1 * fear)
    pts = [(x + w * 0.58, y + 1.0), (x + w * 0.22, y - up * 0.58), (x - w * 0.2, y - up * 0.64), (x - w * 0.5, y - up * 0.1),
           (x - w * 0.36, y + lo * 0.42), (x + w * 0.16, y + lo * 0.44)]
    _fill(c, [bass.orient(pts, True)], color)
    if light is not None:
        _fill(c, [bass.orient(pts, True)], light[0], light[1])
    c.save()
    c.new_path()
    D.poly(c, pts)
    c.clip()
    r = h * 0.5 * (1.0 - 0.35 * fear)
    px = x + w * (0.1 + 0.26 * look)
    py = y + hh * (0.04 + 0.34 * down)
    _fill(c, [D.circle_pts((px, py), r, n=20)], pupil)
    _fill(c, [D.circle_pts((px + r * 0.35, py - r * 0.4), r * 0.28, n=10)], K.PAPER, 0.9)     # the catchlight
    c.restore()
    # the upper lid's line, flicking past the outer corner
    _line(c, [(x - w * 0.52, y - up * 0.08), (x - w * 0.2, y - up * 0.66), (x + w * 0.22, y - up * 0.6), (x + w * 0.64, y - 2.0)],
          K.INK, max(3.0, h * 0.26), taper=(0.4, 1.0))


def _place(c, at, s, facing, anchor):
    c.translate(*at)
    c.scale(s * facing, s)
    c.translate(-anchor[0], -anchor[1])


def _marks(c, d):
    return {k: c.user_to_device(*v) for k, v in d.items()}


def _back(c, d):
    return {k: c.device_to_user(*v) for k, v in d.items()}


def _rimmed(c, polys, rim, light, w):
    if rim is None:
        return
    c.save()
    c.translate(light[0] * w, light[1] * w)
    _fill(c, polys, rim)
    c.restore()


def _breath_drops(c, pts, t, s, seed):
    """Water running off: drops that swell, fall and are replaced."""
    for i, (x, y) in enumerate(pts):
        ph = (t * (0.9 + 0.3 * hash01(seed, i)) + hash01(seed, i, 2)) % 1.0
        dy = 260.0 * ph * ph
        r = 7.0 + 5.0 * hash01(seed, i, 3)
        a = 1.0 - clamp((ph - 0.7) / 0.3)
        _fill(c, [D.ellipse_pts((x, y + dy), r * 0.8, r * (1.0 + 0.6 * ph), n=12)], K.PAPER, 0.85 * a)


# ============================================================================ the mother
_M_FACE = ((470, 150), (494, 205), (502, 255), (497, 286), (503, 318), (528, 362), (550, 395), (546, 407), (524, 413),
           (522, 428), (533, 444), (520, 456), (531, 468), (514, 488), (518, 516), (504, 543), (472, 556), (440, 568),
           (424, 620), (414, 720), (404, 860), (230, 860), (236, 720), (250, 620), (300, 520), (320, 300), (390, 170))
_M_SCARF = ((486, 170), (472, 118), (420, 70), (330, 40), (230, 48), (150, 90), (96, 160), (70, 250), (66, 350), (80, 440),
            (108, 520), (126, 566), (98, 616), (70, 700), (50, 802), (122, 722), (184, 644), (246, 604), (330, 592),
            (404, 588), (442, 580), (470, 566), (460, 544), (422, 534), (384, 500), (362, 440), (370, 360), (400, 290),
            (442, 228))
_M_KNOT = ((424, 566), (462, 556), (486, 576), (470, 600), (448, 604), (440, 650), (420, 652), (424, 604), (408, 590))
_M_COAT = ((-60, 1040), (10, 850), (100, 784), (210, 752), (232, 650), (300, 640), (326, 730), (404, 770), (440, 690),
           (480, 702), (522, 800), (600, 1040))
_M_EDGE = ((486, 172), (444, 228), (402, 290), (372, 360), (364, 440), (386, 500), (424, 534))


def mother(c, at, s=1.0, look=0.3, lid=1.0, fear=0.0, down=0.0, t=0.0, facing=1, rim=K.PAPER, light=(0.8, -0.6),
           rim_w=5.0, edge=K.STEEL, eye_light=None, coat=True):
    """The mother in profile, facing right: the headscarf knotted under her chin, its point down
    the back of her neck, the coat's collar. look: where her pupil is (-1 back .. 1 forward)."""
    c.save()
    _place(c, at, s, facing, (400, 860))
    polys = [_shape(_M_FACE, 911), _shape(_M_SCARF, 912), _shape(_M_KNOT, 913, max_len=30.0)]
    if coat:
        polys.append(_poly(_M_COAT, 914))
    _rimmed(c, polys, rim, (light[0] * facing, light[1]), rim_w / max(s, 1e-3))
    _fill(c, polys, K.INK)
    if edge is not None:
        _line(c, spline(_M_EDGE, n=4, closed=False), edge, 3.0 / max(s, 0.2) * 0.6, alpha=0.9)
        if coat:
            _line(c, [(326, 730), (404, 770)], edge, 3.0 / max(s, 0.2) * 0.6, alpha=0.9)
    _eye(c, (466, 300), 44.0, 17.0, look, lid, fear, down, light=eye_light)
    m = _marks(c, {"eye": (470.0, 300.0), "mouth": (528.0, 458.0), "nose": (550.0, 396.0), "chin": (512.0, 530.0),
                   "top": (330.0, 40.0), "ear": (330.0, 400.0)})
    c.restore()
    return _back(c, m)


# ============================================================================ the girl
_G_FACE = ((486, 236), (500, 270), (497, 298), (508, 326), (522, 348), (530, 362), (520, 374), (512, 388), (517, 401),
           (506, 410), (513, 421), (500, 438), (494, 458), (470, 472), (440, 478), (420, 504), (410, 560), (404, 640),
           (230, 640), (234, 560), (150, 500), (100, 420), (88, 330), (110, 240), (170, 160), (260, 120), (380, 130))
_G_HAT = ((528, 246), (520, 170), (468, 92), (370, 46), (262, 44), (160, 84), (96, 160), (70, 244), (72, 316), (180, 300),
          (300, 278), (420, 258))
_G_FOLD = ((532, 206), (430, 214), (300, 236), (180, 258), (74, 276))
_G_COAT = ((-40, 900), (30, 700), (140, 610), (240, 586), (420, 586), (520, 620), (620, 900))
_G_WRAP = ((420, 478), (474, 486), (488, 524), (476, 586), (400, 606), (300, 602), (226, 586), (214, 524), (256, 494),
           (340, 486))
_G_END_FRONT = ((436, 560), (484, 560), (500, 700), (494, 760), (452, 772), (440, 700))
_G_END_BACK = ((240, 520), (150, 534), (60, 576), (0, 620), (58, 616), (16, 676), (110, 626), (236, 584))


def girl(c, at, s=1.0, look=0.4, lid=1.0, fear=0.0, down=0.0, t=0.0, facing=1, rim=K.PAPER, light=(0.8, -0.6),
         rim_w=5.0, edge=K.STEEL, scarf=1.0, scarf_lift=0.0, pompom=0.0, eye_light=None, coat=True):
    """The girl in profile, facing right: the pompom hat over her ears, the RED scarf wound once
    (scarf 0..1: how much of it is still round her neck; 0 = she has unwound it), her big eye.
    scarf_lift: degrees the trailing end lifts; pompom: degrees it swings."""
    c.save()
    _place(c, at, s, facing, (400, 640))
    head = [_shape(_G_FACE, 921), _shape(_G_HAT, 922)]
    pp = bass.orient([(300 + (66 + 6 * math.cos(i * 2.1)) * math.cos(6.283 * i / 30),
                       -6 + (62 + 6 * math.cos(i * 2.1)) * math.sin(6.283 * i / 30)) for i in range(30)], True)
    polys = head + ([_poly(_G_COAT, 924)] if coat else [])
    _rimmed(c, polys + [pp], rim, (light[0] * facing, light[1]), rim_w / max(s, 1e-3))
    _fill(c, polys, K.INK)
    c.save()
    c.translate(300, 40)
    c.rotate(math.radians(pompom))
    c.translate(-300, -40)
    _fill(c, [pp], K.INK)
    _fill(c, [_poly(((290, 40), (310, 40), (306, 64), (294, 64)), 925)], K.INK)
    c.restore()
    if edge is not None:
        _line(c, spline(_G_FOLD, n=4, closed=False), edge, 1.8 / max(s, 0.2), alpha=0.9)
    if scarf > 0.0:
        k = clamp(scarf)
        _fill(c, [_shape(_G_WRAP, 926)], K.RED)
        c.save()
        c.translate(240, 540)
        c.rotate(math.radians(-scarf_lift))
        c.translate(-240, -540)
        _fill(c, [_shape(_G_END_BACK, 927)], K.RED)
        c.restore()
        if k > 0.5:
            _fill(c, [_shape(_G_END_FRONT, 928)], K.RED)
    _eye(c, (466, 316), 54.0, 25.0, look, lid, fear, down, light=eye_light)
    m = _marks(c, {"eye": (470.0, 316.0), "mouth": (510.0, 408.0), "nose": (530.0, 362.0), "chin": (494.0, 456.0),
                   "top": (300.0, -60.0), "neck": (350.0, 540.0)})
    c.restore()
    return _back(c, m)


# ============================================================================ the guard
_GU_FACE = ((470, 196), (498, 228), (516, 262), (512, 282), (500, 298), (508, 322), (540, 370), (562, 404), (560, 418),
            (540, 430), (528, 478), (534, 492), (522, 510), (526, 536), (510, 562), (480, 580), (440, 592), (424, 640),
            (414, 740), (404, 860), (230, 860), (236, 720), (240, 620), (180, 560), (110, 480), (80, 380), (86, 280),
            (130, 190), (220, 140), (330, 128), (420, 148))
# bareheaded (s08-s11): the same face, the skull smaller and flatter under wet hair
_GU_FACE_BARE = _GU_FACE[:21] + ((240, 620), (196, 566), (150, 490), (128, 400), (130, 312), (160, 236), (226, 186),
                                 (318, 168), (408, 176), (452, 192))
_GU_MOUSTACHE = ((514, 432), (546, 430), (568, 444), (576, 474), (558, 470), (540, 482), (520, 476), (506, 462))
_GU_BROW = ((436, 262), (500, 246), (530, 260), (502, 278), (452, 280))
_GU_CROWN = ((50, 236), (40, 140), (70, 60), (150, 16), (290, 0), (420, 14), (490, 56), (512, 140), (500, 220),
             (300, 238), (150, 248))
_GU_FLAP = ((436, 226), (500, 224), (528, 182), (534, 100), (516, 58), (470, 54), (448, 120))
_GU_EARFLAP = ((170, 70), (262, 36), (340, 64), (318, 176), (206, 196))
_GU_COLLAR = ((222, 700), (232, 600), (300, 586), (400, 600), (452, 612), (474, 690), (478, 780), (230, 790))
_GU_COAT = ((-80, 1060), (0, 860), (100, 778), (226, 740), (436, 746), (526, 796), (620, 1060))
_GU_HAIR = ((130, 196), (180, 140), (260, 110), (360, 106), (440, 130), (478, 180), (470, 200), (420, 160), (330, 140),
            (230, 150), (160, 196))


def guard(c, at, s=1.0, look=0.3, lid=1.0, fear=0.0, down=0.0, t=0.0, facing=1, rim=K.PAPER, light=(0.8, -0.6),
          rim_w=5.0, edge=K.STEEL, hat=True, wet=0.0, eye_light=None, coat=True, mouth_open=0.0):
    """The guard in profile, facing right: the ushanka (front flap turned up, ear flaps tied on
    top), a heavy brow, a big nose, the moustache, the greatcoat's high collar. hat=False: his
    cropped hair, wet (s08). wet 0..1: water running off him. mouth_open: gasping."""
    c.save()
    _place(c, at, s, facing, (400, 860))
    polys = [_shape(_GU_FACE if hat else _GU_FACE_BARE, 931), _shape(_GU_MOUSTACHE, 932, max_len=24.0),
             _shape(_GU_BROW, 933, max_len=24.0), _shape(_GU_COLLAR, 934)]
    if hat:
        polys += [_fur(_GU_CROWN, 935), _fur(_GU_FLAP, 936, depth=5.0), _fur(_GU_EARFLAP, 937, depth=5.0)]
        polys.append(bass.orient(D.circle_pts((262, 8), 30, n=16), True))
    else:
        polys.append(_fur(tuple((x, y + 40.0) for x, y in _GU_HAIR), 938, depth=6.0, step=7.0))
    if coat:
        polys.append(_poly(_GU_COAT, 939))
    _rimmed(c, polys, rim, (light[0] * facing, light[1]), rim_w / max(s, 1e-3))
    _fill(c, polys, K.INK)
    if mouth_open > 0.02:
        # the open mouth: a dark gap under the moustache (a cut of the background through the jaw)
        o = clamp(mouth_open)
        _fill(c, [bass.orient([(524, 476), (536, 480), (534, 480 + 26 * o), (518, 486 + 22 * o)], True)], edge or K.STEEL)
    if edge is not None:
        w = 1.8 / max(s, 0.2)
        if hat:
            _line(c, spline(((444, 222), (452, 130), (472, 60)), n=4, closed=False), edge, w, alpha=0.9)
            _line(c, spline(((176, 76), (210, 190), (318, 174)), n=4, closed=False), edge, w, alpha=0.9)
            _line(c, [(60, 230), (300, 234), (484, 214)], edge, w, alpha=0.9)
        _line(c, spline(((452, 614), (466, 700), (474, 780)), n=4, closed=False), edge, w, alpha=0.9)
    _eye(c, (462, 302), 40.0, 14.0, look, lid, fear, down, light=eye_light)
    if wet > 0.0:
        _breath_drops(c, [(560, 420), (526, 540), (496, 576), (430, 140), (300, 120), (180, 170)][: max(1, int(6 * wet))], t,
                      1.0, 939)
    m = _marks(c, {"eye": (466.0, 302.0), "mouth": (540.0, 486.0), "nose": (562.0, 410.0), "chin": (520.0, 540.0),
                   "top": (280.0, 10.0) if hat else (310.0, 150.0), "ear": (300.0, 400.0)})
    c.restore()
    return _back(c, m)


# ============================================================================ the eyes, face-on
_EYES = {"mother": dict(w=118.0, h=46.0, gap=220.0, brow=True), "girl": dict(w=126.0, h=64.0, gap=240.0, brow=False),
         "guard": dict(w=104.0, h=34.0, gap=232.0, brow=True)}


def eyes(c, who, at, s=1.0, look=(0.0, 0.0), lid=1.0, fear=0.0, rim=None, edge=K.STEEL, light=None, t=0.0,
         field=None, frame_w=1080.0):
    """A strip of `who`'s face, face-on, centred at `at`: the INK face across the frame, the two
    PAPER eyes, the headscarf's edge (mother), the hat's brim (girl), the fur (guard) above.
    look: (dx, dy) -1..1; light: (colour, alpha) washed over the whites (the lantern)."""
    spec = _EYES[who]
    c.save()
    c.translate(*at)
    c.scale(s, s)
    W_ = frame_w / max(s, 1e-3)
    # the face band
    _fill(c, [[(-W_, -250.0), (W_, -250.0), (W_, 260.0), (-W_, 260.0)]], K.INK)
    # above: the headscarf's edge / the hat's brim / the fur, a cut line in `edge`
    if edge is not None:
        if who == "mother":
            _line(c, spline(((-W_, -40), (-380, -150), (0, -200), (380, -150), (W_, -40)), n=6, closed=False), edge, 5.0)
        elif who == "girl":
            _line(c, [(-W_, -150), (W_, -150)], edge, 5.0)
            for i in range(-12, 13):
                _line(c, [(i * 60.0, -150), (i * 60.0, -250)], edge, 2.5, alpha=0.6)
        else:
            _line(c, [(-W_, -170), (W_, -170)], edge, 5.0)
    w, h, gap = spec["w"], spec["h"], spec["gap"]
    dx, dy = look
    for side in (-1, 1):
        x = side * gap * 0.5
        hh = h * clamp(lid) * (1.0 + 0.5 * fear)
        if hh < 3.0:
            _line(c, [(x - w * 0.55, 0.0), (x + w * 0.55, 0.0)], edge or K.STEEL, 4.0)
            continue
        pts = []
        for i in range(32):
            a = 2.0 * math.pi * i / 32
            ca, sa = math.cos(a), math.sin(a)
            yy = (hh * 0.5 * sa) * (1.15 if sa < 0 else 0.9)
            pts.append((x + w * 0.5 * ca * (1.0 - 0.08 * side * sa), yy))
        _fill(c, [bass.orient(pts, True)], K.PAPER)
        if light is not None:
            _fill(c, [bass.orient(pts, True)], light[0], light[1])
        c.save()
        c.new_path()
        D.poly(c, pts)
        c.clip()
        r = h * 0.42 * (1.0 - 0.35 * fear)
        _fill(c, [D.circle_pts((x + dx * w * 0.3, dy * hh * 0.25), r, n=24)], K.INK)
        _fill(c, [D.circle_pts((x + dx * w * 0.3 + r * 0.35, dy * hh * 0.25 - r * 0.4), r * 0.25, n=10)], K.PAPER, 0.9)
        c.restore()
        if spec["brow"]:
            by = -h * 0.95 - 10.0 * fear
            _line(c, [(x - w * 0.55, by + 8.0 * side * 0), (x, by - 10.0 - 8.0 * fear), (x + w * 0.55, by + 4.0)],
                  edge or K.STEEL, 6.0, alpha=0.8)
    if rim is not None:
        _fill(c, [[(-W_, -250.0), (W_, -250.0), (W_, -244.0), (-W_, -244.0)]], rim, 0.9)
    m = _marks(c, {"left": (-gap * 0.5, 0.0), "right": (gap * 0.5, 0.0)})
    c.restore()
    return _back(c, m)


# ============================================================================ the girl, face-on
_FG_HAT = ((-176, -40), (-170, -130), (-120, -210), (-40, -246), (40, -246), (120, -210), (170, -130), (176, -40))
_FG_BUST = ((-330, 420), (-300, 300), (-200, 220), (-90, 190), (90, 190), (200, 220), (300, 300), (330, 420))


def front_girl(c, at, s=1.0, scarf=K.RED, look=(0.0, 0.0), lid=1.0, color=K.INK, eye_color=K.PAPER, rim=None,
               light=(0.8, -0.6), rim_w=4.0, edge=None, t=0.0, pompom=0.0):
    """A girl face-on, head and shoulders (the face's centre at `at`): the pompom hat, big eyes;
    `scarf` the scarf's colour (K.RED for her, INK in the photograph). The photograph in his watch
    and the real girl match: same shape, same place."""
    c.save()
    c.translate(*at)
    c.scale(s, s)
    head = bass.orient(D.ellipse_pts((0.0, 10.0), 150.0, 160.0, n=60), True)
    hat = _shape(_FG_HAT + ((150, -30), (0, -20), (-150, -30)), 941)
    brim = bass.orient(spline(((-182, -64), (0, -84), (182, -64), (184, -10), (0, -30), (-184, -10)), n=6), True)
    pp = bass.orient([(0 + (60 + 6 * math.cos(i * 2.3)) * math.cos(6.283 * i / 28),
                       -296 + (56 + 6 * math.cos(i * 2.3)) * math.sin(6.283 * i / 28)) for i in range(28)], True)
    bust = _shape(_FG_BUST + ((330, 900), (-330, 900)), 942)
    neck = bass.orient([(-60, 140), (60, 140), (70, 220), (-70, 220)], True)
    polys = [head, hat, brim, bust, neck]
    if rim is not None:
        c.save()
        c.translate(light[0] * rim_w / s, light[1] * rim_w / s)
        _fill(c, polys + [pp], rim)
        c.restore()
    _fill(c, polys, color)
    c.save()
    c.translate(0, -246)
    c.rotate(math.radians(pompom))
    c.translate(0, 246)
    _fill(c, [pp], color)
    c.restore()
    if edge is not None:
        _line(c, spline(((-182, -64), (0, -84), (182, -64)), n=6, closed=False), edge, 4.0)
    # the scarf: the wrap, one end hanging
    if scarf is not None:
        wrap = _shape(((-150, 160), (0, 150), (150, 160), (160, 236), (0, 250), (-160, 236)), 943)
        end = _shape(((50, 220), (120, 222), (132, 420), (118, 470), (66, 470), (60, 380)), 944)
        _fill(c, [wrap, end], scarf)
        if edge is not None and scarf == color:
            _line(c, spline(((-150, 160), (0, 150), (150, 160)), n=6, closed=False), edge, 3.0)
    # the eyes
    for side in (-1, 1):
        x, y = side * 56.0, 34.0
        hh = 26.0 * clamp(lid)
        if hh < 2.0:
            _line(c, [(x - 22, y), (x + 22, y)], eye_color, 4.0)
            continue
        _fill(c, [D.ellipse_pts((x, y), 21.0, hh, n=24)], eye_color)
        _fill(c, [D.circle_pts((x + look[0] * 8.0, y + look[1] * 8.0), 11.0, n=16)], color)
    m = _marks(c, {"face": (0.0, 10.0), "top": (0.0, -350.0), "chin": (0.0, 170.0)})
    c.restore()
    return _back(c, m)


# ============================================================================ hands
_MITT = ((0, -46), (60, -54), (130, -56), (176, -40), (196, -6), (186, 30), (150, 50), (96, 54), (40, 50), (0, 44))
_MITT_THUMB = ((54, 40), (96, 50), (126, 80), (124, 104), (100, 104), (70, 80), (46, 56))
_CUFF = ((-30, -58), (12, -54), (12, 54), (-30, 60))


def mitten(c, wrist, tip, s=1.0, rim=K.PAPER, light=(0.8, -0.6), rim_w=4.0, thumb=1.0, curl=0.0, sleeve_w=1.0,
           flip=False, color=K.INK, edge=K.STEEL, sleeve=True):
    """A mittened hand coming in from `wrist` (frame px; put it off-frame for a reach) with its
    tip at `tip`: the sleeve, the knitted cuff, the mitt, the thumb (thumb 0..1 out from the
    mitt; flip puts it on the other side). curl 0..1 closes the mitt round something."""
    dx, dy = tip[0] - wrist[0], tip[1] - wrist[1]
    L = math.hypot(dx, dy) or 1.0
    ang = math.atan2(dy, dx)
    k = s
    c.save()
    c.translate(*tip)
    c.rotate(ang)
    c.scale(k, k * (-1.0 if flip else 1.0))
    c.translate(-196.0, 0.0)
    cu = clamp(curl)
    mitt = [(x * (1.0 - 0.25 * cu * clamp(x / 196.0)), y + 30.0 * cu * clamp((x - 100) / 96.0) * (1 if y > 0 else 0.4))
            for x, y in spline(_MITT, n=4)]
    th = [(lerp(54 + 0.3 * (x - 54), x, thumb), lerp(48, y, thumb)) for x, y in spline(_MITT_THUMB, n=3)]
    far = -L / k - 40.0
    polys = [bass.orient(mitt, True), bass.orient(th, True), bass.orient(list(_CUFF), True)]
    if sleeve:
        polys.append(bass.orient([(far, -70.0 * sleeve_w), (-24.0, -66.0), (-24.0, 66.0), (far, 70.0 * sleeve_w)], True))
    if rim is not None:
        c.save()
        lx = light[0] * math.cos(ang) + light[1] * math.sin(ang)
        ly = -light[0] * math.sin(ang) + light[1] * math.cos(ang)
        c.translate(lx * rim_w / k, ly * rim_w / k * (-1.0 if flip else 1.0))
        _fill(c, polys, rim)
        c.restore()
    _fill(c, polys, color)
    if edge is not None:
        _line(c, [(12, -54), (12, 54)], edge, 2.5 / max(k, 0.2) * 0.8, alpha=0.8)
        if thumb > 0.3:
            _line(c, spline(((60, 44), (90, 52), (118, 78)), n=3, closed=False), edge, 2.0 / max(k, 0.2) * 0.8, alpha=0.7)
    c.restore()


_PALM = ((0, -50), (70, -56), (120, -50), (124, 50), (70, 56), (0, 50))
_FINGERS = ((120, -48, 70), (124, -18, 80), (124, 12, 76), (120, 40, 60))      # base y, length


def glove(c, wrist, tip, s=1.0, curl=0.0, spread=0.0, rim=K.PAPER, light=(0.8, -0.6), rim_w=4.0, flip=False,
          color=K.INK, sleeve=True, sleeve_w=1.0, thumb=1.0):
    """The guard's gloved hand from `wrist` toward `tip` (the fingertips' reach): palm, four
    fingers (curl 0..1 bends them into a grip; spread 0..1 fans them: clawing), the thumb, the
    greatcoat's cuff."""
    dx, dy = tip[0] - wrist[0], tip[1] - wrist[1]
    L = math.hypot(dx, dy) or 1.0
    ang = math.atan2(dy, dx)
    k = s
    cu, sp = clamp(curl), clamp(spread)
    c.save()
    c.translate(*tip)
    c.rotate(ang)
    c.scale(k, k * (-1.0 if flip else 1.0))
    c.translate(-200.0, 0.0)
    polys = [bass.orient(spline(_PALM, n=3), True)]
    for i, (bx, by, ln) in enumerate(_FINGERS):
        a0 = math.radians((i - 1.5) * 9.0 * sp)
        a1 = a0 + math.radians(70.0 * cu)
        j1 = (bx + math.cos(a0) * ln * 0.55, by + math.sin(a0) * ln * 0.55 * 2.0 * (0.4 + sp))
        j2 = (j1[0] + math.cos(a1) * ln * 0.5, j1[1] + math.sin(a1) * ln * 0.5)
        polys.append(bass.orient(bass.capsule_pts((bx - 6, by), j1, 14.0, 13.0, cap=5), True))
        polys.append(bass.orient(bass.capsule_pts(j1, j2, 13.0, 11.0, cap=5), True))
    ta = math.radians(60.0 - 50.0 * cu)
    t0 = (40.0, 44.0)
    t1 = (t0[0] + math.cos(ta) * 60.0 * thumb, t0[1] + math.sin(ta) * 60.0 * thumb)
    polys.append(bass.orient(bass.capsule_pts(t0, t1, 18.0, 14.0, cap=5), True))
    far = -L / k - 40.0
    if sleeve:
        polys.append(bass.orient([(far, -84.0 * sleeve_w), (-10.0, -70.0), (-6.0, 70.0), (far, 84.0 * sleeve_w)], True))
        polys.append(bass.orient([(-60.0, -80.0), (-4.0, -66.0), (0.0, 66.0), (-60.0, 80.0)], True))
    if rim is not None:
        c.save()
        lx = light[0] * math.cos(ang) + light[1] * math.sin(ang)
        ly = -light[0] * math.sin(ang) + light[1] * math.cos(ang)
        c.translate(lx * rim_w / k, ly * rim_w / k * (-1.0 if flip else 1.0))
        _fill(c, polys, rim)
        c.restore()
    _fill(c, polys, color)
    c.restore()


# ============================================================================ boots
_BOOT = {
    # the mother's felt boot (valenki): tall, round toed, no heel; her coat's hem above
    "mother": ((-70, 0), (120, 0), (168, -10), (180, -40), (150, -72), (90, -96), (60, -150), (64, -430), (-72, -430),
               (-82, -200), (-84, -40)),
    # the girl's small boot
    "girl": ((-50, 0), (90, 0), (126, -10), (134, -36), (104, -60), (60, -78), (44, -120), (46, -260), (-52, -260),
             (-60, -120), (-60, -30)),
    # the guard's hobnailed boot: a heel, a thick sole, the greatcoat's hem above
    "guard": ((-90, 0), (-40, 0), (-38, -14), (150, -14), (152, 0), (200, 0), (206, -30), (176, -70), (110, -96),
              (70, -130), (68, -380), (-90, -380), (-96, -60)),
}
_HEM = {"mother": ((-160, -414), (150, -420), (104, -660), (-112, -660)),
        "girl": ((-110, -246), (100, -250), (70, -420), (-80, -420)),
        "guard": ((-180, -352), (170, -360), (120, -640), (-130, -640))}


def boot(c, at, s=1.0, who="mother", pitch=0.0, facing=1, rim=K.PAPER, light=(0.8, -0.6), rim_w=4.0, hem=True,
         nails=False, color=K.INK):
    """A boot in profile, facing right, the sole's heel end at `at` (frame px); pitch: degrees the
    toe tips up (+) or down. hem: the coat's hem above it. nails: the hobnails show (a lifted
    guard's sole)."""
    c.save()
    c.translate(*at)
    c.scale(s * facing, s)
    c.rotate(math.radians(-pitch))
    polys = [_poly(_BOOT[who], 951 + len(who))]
    if hem:
        polys.append(_poly(_HEM[who], 955 + len(who)))
    if rim is not None:
        c.save()
        c.translate(light[0] * facing * rim_w / s, light[1] * rim_w / s)
        _fill(c, polys, rim)
        c.restore()
    _fill(c, polys, color)
    if nails and who == "guard":
        for i in range(9):
            _fill(c, [D.circle_pts((-70.0 + i * 30.0, -3.0), 5.0, n=8)], K.PAPER, 0.85)
    c.restore()


# ============================================================================ the watch
def _hand_poly(c0, ang, L, w, tail=0.18):
    a = math.radians(ang - 90.0)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    tip = (c0[0] + ux * L, c0[1] + uy * L)
    back = (c0[0] - ux * L * tail, c0[1] - uy * L * tail)
    return bass.orient([(back[0] + nx * w * 0.5, back[1] + ny * w * 0.5), (c0[0] + nx * w, c0[1] + ny * w), tip,
                        (c0[0] - nx * w, c0[1] - ny * w), (back[0] - nx * w * 0.5, back[1] - ny * w * 0.5)], True)


def watch(c, at, r, t=0.0, lid=1.0, hands=(11, 58), seconds=None, wet=0.0, drain=0.0, photo=True, rim=K.PAPER,
          light=(0.8, -0.6), field=K.INK, thumb=None):
    """The pocket watch face-on at `at`, radius r px: the case and its bow, the PAPER dial, twelve
    ticks, the hands at `hands` (h, m) and a small seconds hand (seconds: its value, or None for
    none). lid 0..1: the lid swings open on its hinge (left) and shows the oval photograph of the
    girl in the pompom hat. wet: water on the glass and the photograph; drain 0..1: the water
    running out (s11). Returns {'photo': centre, 'photo_r': (rx, ry), 'dial': centre}."""
    x, y = at
    out = {"dial": at}
    # the bow and crown at twelve
    _fill(c, [D.ellipse_pts((x, y - r * 1.18), r * 0.16, r * 0.11, n=16)], K.INK)
    ring = [(x + r * 0.24 * math.cos(a), y - r * 1.36 + r * 0.2 * math.sin(a)) for a in [6.283 * i / 24 for i in range(24)]]
    inner = [(x + r * 0.15 * math.cos(a), y - r * 1.36 + r * 0.11 * math.sin(a)) for a in [6.283 * i / 24 for i in range(24)]]
    _fill(c, [bass.orient(ring + [ring[0]] + inner[::-1] + [inner[-1]], True)], K.INK)
    if rim is not None:
        _fill(c, [D.circle_pts((x + light[0] * r * 0.03, y + light[1] * r * 0.03), r * 1.04, n=64)], rim)
    _fill(c, [D.circle_pts((x, y), r * 1.02, n=64)], K.INK)
    # the dial
    u = clamp(lid)
    _fill(c, [D.circle_pts((x, y), r * 0.86, n=64)], K.PAPER)
    for i in range(12):
        a = math.radians(i * 30.0 - 90.0)
        L0, L1 = r * (0.7 if i % 3 else 0.62), r * 0.8
        _line(c, [(x + math.cos(a) * L0, y + math.sin(a) * L0), (x + math.cos(a) * L1, y + math.sin(a) * L1)], K.INK,
              r * (0.05 if i % 3 else 0.075))
    h, mnt = hands
    _fill(c, [_hand_poly((x, y), (h % 12 + mnt / 60.0) * 30.0, r * 0.42, r * 0.055)], K.INK)
    _fill(c, [_hand_poly((x, y), mnt * 6.0, r * 0.62, r * 0.04)], K.INK)
    if seconds is not None:
        sc = (x, y + r * 0.38)
        _fill(c, [D.circle_pts(sc, r * 0.16, n=24)], K.INK)
        _fill(c, [D.circle_pts(sc, r * 0.13, n=24)], K.PAPER)
        _fill(c, [_hand_poly(sc, seconds * 6.0, r * 0.12, r * 0.018, 0.1)], K.INK)
    _fill(c, [D.circle_pts((x, y), r * 0.06, n=16)], K.INK)
    if wet > 0.0:
        # water inside the glass, its level dropping as it drains; a few beads
        lvl = y + r * 0.86 * (1.0 - 2.0 * (1.0 - clamp(drain)) * 0.45 * wet)
        c.save()
        c.new_path()
        D.poly(c, D.circle_pts((x, y), r * 0.86, n=64))
        c.clip()
        _fill(c, [[(x - r, lvl), (x + r, lvl + r * 0.04), (x + r, y + r), (x - r, y + r)]], K.WATER, 0.45 * wet)
        c.restore()
        for i in range(5):
            a = math.radians(200 + 32 * i)
            p = (x + math.cos(a) * r * 0.55 * (0.6 + 0.4 * hash01(5, i)), y + math.sin(a) * r * 0.5)
            _fill(c, [D.circle_pts(p, r * 0.03, n=10)], K.PAPER, 0.9 * wet)
        if drain > 0.0:
            # water running out of the case's bottom
            for i in range(4):
                ph = (t * 1.4 + i * 0.27) % 1.0
                py = y + r * 1.02 + ph * ph * r * 2.2
                _fill(c, [D.ellipse_pts((x - r * 0.1 + i * r * 0.07, py), r * 0.035, r * 0.05 * (1 + ph), n=10)], K.PAPER,
                      (1.0 - ph) * clamp(drain * 3.0) * clamp((1.0 - drain) * 4.0))
    # the lid, hinged at nine o'clock: closed it covers the dial; open it lies to the left,
    # its inside up, the photograph in it
    ang = math.pi * ease("inout", u)
    sx = math.cos(ang)
    hinge = (x - r * 1.02, y)
    c.save()
    c.translate(*hinge)
    c.scale(sx if abs(sx) > 1e-3 else 1e-3, 1.0)
    c.translate(-hinge[0], -hinge[1])
    if sx > 0.0:
        _fill(c, [D.circle_pts((x, y), r * 1.02, n=64)], K.INK)
        _line(c, [(x + r * 0.78 * math.cos(a), y + r * 0.78 * math.sin(a)) for a in [6.283 * i / 48 for i in range(49)]],
              K.STEEL, r * 0.03)
    else:
        # the inside of the lid (mirrored to the left of the hinge)
        cx = x
        _fill(c, [D.circle_pts((cx, y), r * 1.02, n=64)], K.INK)
        if photo:
            rx, ry = r * 0.6, r * 0.74
            _fill(c, [D.ellipse_pts((cx, y), rx, ry, n=48)], lerp(K.PAPER, K.SHADOW, 0.25 * wet))
            c.save()
            c.new_path()
            D.poly(c, D.ellipse_pts((cx, y), rx, ry, n=48))
            c.clip()
            front_girl(c, (cx, y + ry * 0.05), ry / 470.0, scarf=K.INK, look=(0.0, 0.0), edge=None)
            if wet > 0.0:
                for i in range(4):
                    p = (cx + rx * (hash01(9, i) - 0.5), y + ry * (hash01(9, i, 1) - 0.4))
                    _fill(c, [D.circle_pts(p, r * 0.035, n=10)], K.PAPER, 0.7 * wet)
            c.restore()
            _line(c, [(cx + rx * math.cos(a), y + ry * math.sin(a)) for a in [6.283 * i / 48 for i in range(49)]], K.STEEL,
                  r * 0.025)
    c.restore()
    if sx < 0.0:
        px = hinge[0] + (hinge[0] - x) * (-sx) * -1.0
        out["photo"] = (hinge[0] - (x - hinge[0]) * (-sx), y)
        out["photo_r"] = (r * 0.6 * (-sx), r * 0.74)
    return out


# ============================================================================ the music box
def music_box(c, at, s=1.0, open_u=0.0, t=0.0, spin=0.0, color=K.INK, rim=K.PAPER, light=(0.8, -0.6), dancer=True):
    """The little music box in profile, its front-bottom corner at `at`: the box, the lid
    hinged at the back (open_u 0..1 springs it up past upright), and the paper dancer on her
    spindle rising out of it (spin: radians she has turned)."""
    c.save()
    c.translate(*at)
    c.scale(s, s)
    box = _poly(((0, 0), (220, 0), (220, -110), (0, -110)), 961)
    a = math.radians(-112.0 * clamp(open_u))
    c.save()
    if rim is not None:
        c.save()
        c.translate(light[0] * 4.0 / s, light[1] * 4.0 / s)
        _fill(c, [box], rim)
        c.restore()
    _fill(c, [box], color)
    _line(c, [(14, -60), (206, -60)], K.STEEL, 3.0, alpha=0.8)
    # the key on the side
    _fill(c, [bass.orient([(224, -58), (250, -64), (262, -52), (250, -40), (224, -46)], True)], color)
    c.restore()
    # the dancer, rising with the lid
    if dancer and open_u > 0.05:
        rise = 70.0 * ease("out3", clamp(open_u * 1.4))
        base = (110.0, -110.0 - rise)
        _line(c, [(110.0, -110.0), base], color, 6.0)
        sx = math.cos(spin)
        c.save()
        c.translate(*base)
        c.scale(sx if abs(sx) > 0.05 else 0.05, 1.0)
        tutu = bass.orient([(-34, -40), (34, -40), (24, -26), (-24, -26)], True)
        body = bass.orient([(-7, -40), (7, -40), (6, -70), (-6, -70)], True)
        head = bass.orient(D.circle_pts((0, -80), 9, n=14), True)
        arms = bass.orient(spline(((-26, -98), (0, -112), (26, -98), (22, -94), (0, -104), (-22, -94)), n=3), True)
        leg = bass.orient([(-3, -26), (3, -26), (2, 0), (-2, 0)], True)
        _fill(c, [tutu, body, head, arms, leg], K.PAPER)
        c.restore()
    # the lid, hinged at the back-top corner (0, -110)
    c.save()
    c.translate(0.0, -110.0)
    c.rotate(a)
    lid = _poly(((0, 0), (226, 0), (226, -26), (0, -26)), 962)
    _fill(c, [lid], color)
    if open_u > 0.3:
        _fill(c, [bass.orient([(16, -3), (210, -3), (210, -5), (16, -5)], True)], K.STEEL, 0.6)
    c.restore()
    c.restore()


# ============================================================================ the scrap on the barb
def scrap(c, at, s=1.0, t=0.0, wind=1.0, color=K.INK, rim=K.PAPER, light=(0.8, -0.6)):
    """A torn scrap of her coat hanging from a barb at `at` (the barb's point), stirring."""
    c.save()
    c.translate(*at)
    c.scale(s, s)
    sway = wind * (6.0 * math.sin(t * 2.3) + 3.0 * math.sin(t * 5.1 + 1.0))
    c.rotate(math.radians(sway))
    pts = [(-8, -6), (40, -14), (70, 4), (86, 40), (74, 96), (80, 130), (58, 150), (50, 122), (34, 156), (16, 126),
           (-4, 148), (-12, 108), (-30, 120), (-26, 60), (-34, 20)]
    poly = _poly(tuple(pts), 971)
    if rim is not None:
        c.save()
        c.translate(light[0] * 3.0 / s, light[1] * 3.0 / s)
        _fill(c, [poly], rim)
        c.restore()
    _fill(c, [poly], color)
    # frayed threads at the torn edge
    for i in range(5):
        x0 = -20 + i * 22
        _line(c, [(x0, 130 + 10 * (i % 2)), (x0 + 4 * math.sin(t * 3 + i), 170 + 12 * hash01(3, i))], color, 2.5)
    c.restore()
