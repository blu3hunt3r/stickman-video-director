"""DOUBLE CROSS: the close-ups. Three profiles cut like cameos, and the hands that set the pieces.

    F.her(c, at, s, look=0.0, t=t)          # the Architect, facing right, on the lamp's gold
    F.cracker(c, at, s, glint=u, t=t)       # the Cracker, facing right, on steel
    F.knight(c, at, s, draw=u, t=t)         # the Knight, facing LEFT, in the dark, his ember lit
    F.hand(c, who, wrist, grip, s, ...)     # a hand coming in from `wrist` pinching a piece at `grip`

`at` is the profile's anchor in frame px: the bottom of the neck at the front (where the collar
opens). Profiles are drawn in face units (the head about 600 tall) scaled by s. Each returns a
dict of landmarks in frame px: 'eye', 'mouth', 'ear', 'nose'.
"""
import math
from functools import lru_cache

from engine import bass, draw as D
from engine.core import clamp, ease, lerp
from films.double_cross import kit as K


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
def _shape(key, pts, seed, sag=1.2, amp=0.8, max_len=46.0, corner=40.0):
    """A cut-paper outline through control points (curved by a spline, then scissor-cut)."""
    return bass.orient(bass.scissor(spline(pts), seed=seed, sag=sag, amp=amp, max_len=max_len, corner=corner), True)


def _poly(key, pts, seed):
    """A straight-cut polygon (corners kept)."""
    return _shape(key, tuple(pts), seed, sag=0.6, amp=0.6, max_len=60.0, corner=12.0)


def _edged(c, polys, color, edge, w):
    c.save()
    c.new_path()
    for p in polys:
        D.poly(c, p)
    c.set_source_rgb(*edge)
    c.set_line_width(w)
    c.set_line_join(1)
    c.stroke()
    c.restore()
    bass.fill_polys(c, polys, color)


def _eye(c, centre, w, h, look, lid=1.0, color=K.PAPER, pupil=K.INK, down=0.0, squint=0.0):
    """An almond eye in profile (facing +x): look -1..1 moves the pupil from back to front and
    down (+) a little; lid 0..1 opens it; down 0..1 drops the pupil and the upper lid with it
    (looking at the floor); squint 0..1 lifts the lower lid (a smile in the eye)."""
    if lid <= 0.02:
        bass.line_band(c, [(centre[0] - w * 0.5, centre[1]), (centre[0] + w * 0.55, centre[1] + 1.0)], K.INK, width=4.0)
        return
    x, y = centre
    hh = h * lid
    up, lo = hh * (1.0 - 0.4 * down), hh * (1.0 - 0.45 * squint)
    pts = [(x + w * 0.55, y + 1.0), (x + w * 0.2, y - up * 0.55), (x - w * 0.2, y - up * 0.6), (x - w * 0.5, y - up * 0.1),
           (x - w * 0.35, y + lo * 0.4), (x + w * 0.15, y + lo * 0.42)]
    bass.fill_polys(c, [bass.orient(pts, True)], color)
    c.save()
    c.new_path()
    D.poly(c, pts)
    c.clip()
    px = x + w * (0.12 + 0.22 * look)
    py = y + hh * (0.05 + 0.18 * max(0.0, look) + 0.32 * down)
    bass.fill_polys(c, [D.circle_pts((px, py), h * 0.5, n=20)], pupil)
    c.restore()
    # the upper lid's line, flicking past the outer corner
    bass.line_band(c, [(x - w * 0.52, y - up * 0.08), (x - w * 0.2, y - up * 0.62), (x + w * 0.2, y - up * 0.58),
                       (x + w * 0.62, y - 2.0)], K.INK, width=max(3.0, h * 0.28), taper=(0.4, 1.0))


def _place(c, at, s, facing=1):
    c.translate(*at)
    c.scale(s * facing, s)
    # face units: the anchor (the front of the neck's base) is at (400, 860)
    c.translate(-400.0, -860.0)


def _out(c, pts):
    return {k: c.user_to_device(*v) for k, v in pts.items()}


def _back(c, d):
    return {k: c.device_to_user(*v) for k, v in d.items()}


# ============================================================================ the Architect
_HER = ((280, 40), (370, 48), (440, 88), (484, 150), (500, 215), (505, 262), (495, 290), (502, 318), (530, 360),
        (557, 392), (548, 405), (522, 410), (520, 424), (533, 440), (517, 456), (529, 470), (512, 490), (508, 502),
        (522, 528), (512, 552), (476, 572), (430, 584), (412, 620), (402, 700), (400, 800), (236, 800), (238, 700),
        (230, 640), (200, 596), (140, 560), (96, 500), (72, 420), (68, 330), (86, 230), (128, 140), (190, 76))
_BUN = ((60, 520), (90, 482), (150, 474), (210, 496), (230, 548), (214, 600), (160, 624), (96, 614), (58, 574))
_PENCIL = ((-26, 494), (8, 492), (214, 572), (208, 588), (2, 512))
_COAT = ((20, 920), (60, 800), (120, 724), (200, 694), (252, 714), (270, 790), (300, 840), (380, 830), (404, 772),
         (430, 744), (470, 772), (520, 840), (560, 920))


def her(c, at, s=1.0, look=0.4, lid=1.0, t=0.0, field=K.GOLD, edge=None, down=0.0, squint=0.0):
    """The Architect in profile, facing right: a smooth sweep of hair into a low chignon with a
    pencil through it, a drop earring, the trench coat's collar turned up. look: where her
    pupil is (-1 back .. 1 forward and down)."""
    edge = field if edge is None else edge
    c.save()
    _place(c, at, s)
    head = _shape("her", _HER, 811)
    bass.fill_polys(c, [head], K.INK)
    _edged(c, [_shape("bun", _BUN, 812)], K.INK, edge, 5.0)
    # the twist of the chignon: two thin arcs of the field's colour
    for k, (r0, a0, a1) in enumerate(((52.0, 200.0, 330.0), (28.0, 210.0, 350.0))):
        pts = [(144 + r0 * math.cos(math.radians(a)), 552 + r0 * 0.85 * math.sin(math.radians(a)))
               for a in [a0 + (a1 - a0) * i / 12 for i in range(13)]]
        bass.line_band(c, pts, edge, width=4.0, seed=813 + k, alpha=0.8)
    _edged(c, [_poly("pencil", _PENCIL, 814)], K.INK, edge, 4.0)
    bass.line_band(c, [(-22, 494), (-4, 496)], K.PAPER, width=5.0)   # its point
    # the drop earring
    bass.line_band(c, [(286, 408), (287, 438)], K.GOLD, width=4.0)
    K.dot(c, (287, 450), 11.0, K.PAPER, seed=815)
    _edged(c, [_poly("coat", _COAT, 816)], K.INK, edge, 5.0)
    _eye(c, (466, 298), 46.0, 18.0, look, lid, down=down, squint=squint)
    marks = _out(c, {"eye": (480.0, 300.0), "mouth": (520.0, 458.0), "ear": (286.0, 360.0), "nose": (557.0, 392.0),
                     "bun": (144.0, 552.0)})
    c.restore()
    return _back(c, marks)


# ============================================================================ the Cracker
_CRACKER = ((150, 150), (460, 160), (480, 230), (482, 262), (470, 290), (478, 310), (522, 368), (566, 412),
            (560, 426), (528, 432), (546, 446), (552, 474), (524, 484), (504, 470), (500, 490), (508, 522), (496, 550),
            (452, 568), (418, 580), (404, 620), (398, 680), (396, 760), (246, 760), (248, 660), (226, 596), (150, 560),
            (100, 500), (76, 420), (74, 330), (92, 240), (120, 180))
_BOWLER = ((96, 180), (100, 100), (150, 40), (250, 10), (350, 14), (420, 56), (452, 120), (462, 180))
_BRIM = ((56, 166), (80, 184), (300, 196), (510, 186), (534, 166), (526, 200), (300, 214), (74, 204))
_FROCK = ((0, 920), (40, 806), (120, 750), (230, 726), (262, 766), (300, 806), (380, 796), (400, 756), (440, 764),
          (500, 822), (540, 920))
_WING = ((392, 716), (430, 704), (446, 736), (414, 738))
_BOW = ((410, 744), (456, 724), (460, 770), (432, 756), (412, 762), (390, 782), (386, 736))
_BROW = ((424, 252), (466, 238), (502, 250), (474, 260), (446, 262))


def cracker(c, at, s=1.0, look=0.2, glint=0.0, t=0.0, field=K.STEEL, edge=None):
    """The Cracker in profile, facing right: a bowler, round spectacles (glint 0..1 sweeps a
    light across the lens), a drooping moustache, a wing collar and bow tie, and his
    stethoscope round his neck in gold."""
    edge = field if edge is None else edge
    c.save()
    _place(c, at, s)
    bass.fill_polys(c, [_shape("cr", _CRACKER, 821)], K.INK)
    _edged(c, [_poly("frock", _FROCK, 820)], K.INK, edge, 5.0)
    bass.fill_polys(c, [_shape("bowler", _BOWLER + ((300, 190),), 822)], K.INK)
    _edged(c, [_shape("brim", _BRIM, 823)], K.INK, edge, 4.0)
    # the hatband: a thin line of the field across the crown's foot
    bass.line_band(c, [(102, 160), (300, 166), (458, 160)], edge, width=5.0, seed=824, alpha=0.7)
    # an old man's white eyebrow; wing collar (paper) and bow tie
    bass.fill_polys(c, [_shape("brow", _BROW, 819)], K.PAPER, 0.92)
    bass.fill_polys(c, [_poly("wing", _WING, 825)], K.PAPER)
    _edged(c, [_poly("bow", _BOW, 826)], K.INK, edge, 3.0)
    # the stethoscope: the tube round the back of the neck, over the collar, down the chest
    tube = spline([(240, 716), (290, 744), (350, 768), (410, 800), (440, 852), (446, 900)], n=6, closed=False)
    bass.line_band(c, tube, K.GOLD, width=10.0, seed=827)
    bass.fill_polys(c, [D.circle_pts((446, 912), 22.0, n=28)], K.GOLD)
    bass.fill_polys(c, [D.circle_pts((446, 912), 11.0, n=20)], K.INK)
    # the eye behind the lens, and the lens
    _eye(c, (452, 298), 36.0, 13.0, look, 0.8)
    lens_c, lens_r = (458.0, 300.0), 36.0
    bass.fill_polys(c, [D.circle_pts(lens_c, lens_r, n=40)], K.PAPER, 0.16)
    bass.line_band(c, [(lens_c[0] - lens_r, 296.0), (318.0, 290.0)], K.PAPER, width=4.0, seed=828)   # the arm
    bass.ring(c, lens_c, lens_r, 6.0, K.PAPER, seed=829, n=48)
    if 0.0 < glint < 1.0:
        c.save()
        c.new_path()
        D.poly(c, D.circle_pts(lens_c, lens_r - 2.0, n=40))
        c.clip()
        x = lens_c[0] - lens_r * 1.6 + 3.2 * lens_r * ease("inout", glint)
        for off, w in ((0.0, 16.0), (22.0, 6.0)):
            bass.fill_polys(c, [bass.orient([(x + off - w, lens_c[1] + 50.0), (x + off + w, lens_c[1] + 50.0),
                                              (x + off + w + 40.0, lens_c[1] - 50.0), (x + off - w + 40.0, lens_c[1] - 50.0)],
                                             True)], K.PAPER, 0.9)
        c.restore()
    marks = _out(c, {"eye": (470.0, 300.0), "mouth": (510.0, 476.0), "ear": (300.0, 360.0), "nose": (566.0, 410.0),
                     "lens": lens_c})
    c.restore()
    return _back(c, marks)


# ============================================================================ the Knight
_KNIGHT = ((120, 170), (470, 172), (488, 210), (508, 252), (492, 280), (502, 300), (522, 318), (542, 352),
           (562, 380), (550, 396), (522, 402), (524, 420), (511, 436), (522, 450), (528, 490), (524, 530), (502, 560),
           (446, 578), (428, 612), (424, 700), (424, 780), (160, 780), (164, 690), (150, 600), (100, 540), (70, 450),
           (66, 350), (80, 250), (104, 190))
_CAP = ((84, 196), (96, 130), (170, 84), (300, 62), (420, 76), (488, 118), (520, 150), (580, 160), (586, 176),
        (500, 186), (300, 188), (90, 206))
_COAT = ((-20, 920), (20, 760), (110, 700), (180, 660), (230, 700), (250, 780), (300, 820), (390, 810), (420, 740),
         (470, 700), (520, 760), (580, 920))


def knight(c, at, s=1.0, look=0.5, draw=0.0, t=0.0, field=K.DEEP, rim=K.RED, back=K.STEEL, smoke=1.0):
    """The Knight in profile, facing LEFT: a flat cap, a broken nose, a heavy jaw, the coat's
    collar up, a cigarette in his lips. draw 0..1: he draws on it (the ember flares, the glow
    widens); smoke curls up from the tip. His rim is red: the ember's light."""
    c.save()
    _place(c, at, s, facing=-1)
    polys = [_shape("kn", _KNIGHT, 831), _shape("cap", _CAP, 832), _poly("kcoat", _COAT, 833)]
    # two rims: cold moonlight on the back of him, the ember's red on his face
    for off, col in (((-7.0, -5.0), back), ((8.0, 6.0), rim)):
        c.save()
        c.translate(*off)
        bass.fill_polys(c, polys, col)
        c.restore()
    bass.fill_polys(c, polys[:2], K.INK)
    _edged(c, polys[2:], K.INK, field, 5.0)
    _eye(c, (468, 282), 34.0, 8.0, look, 0.6)
    # the cigarette, and its ember
    tip = (612.0, 455.0)
    bass.line_band(c, [(512.0, 438.0), tip], K.PAPER, width=11.0, seed=835)
    g = ease("out", clamp(draw)) * (1.0 - clamp((draw - 0.6) / 0.4) * 0.5) if draw > 0.0 else 0.0
    glow = 0.35 + 0.65 * g
    pulse = 0.08 * math.sin(K.twos(t) * 9.0)
    bass.fill_polys(c, [D.circle_pts(tip, 70.0 + 70.0 * g, n=40)], K.RED, 0.10 + 0.14 * glow + 0.03 * pulse)
    bass.fill_polys(c, [D.circle_pts(tip, 30.0 + 18.0 * g, n=28)], K.RED, 0.22 + 0.25 * glow)
    K.dot(c, tip, 10.0 + 3.0 * g, K.RED, seed=836)
    if g > 0.3:
        K.dot(c, tip, 5.0 * g, K.GOLD, seed=837)
    marks = _out(c, {"eye": (480.0, 284.0), "mouth": (512.0, 438.0), "tip": tip, "nose": (561.0, 380.0)})
    c.restore()
    marks = _back(c, marks)
    if smoke > 0.0:
        _smoke(c, marks["tip"], t, s, smoke)
    return marks


def _smoke(c, tip, t, s, a):
    """Cigarette smoke: thin paper wisps rising and curling from the tip, on twos."""
    tt = K.twos(t)
    for k in range(3):
        ph = (tt * 0.45 + k / 3.0) % 1.0
        pts = []
        for i in range(14):
            f = i / 13.0
            y = tip[1] - f * 520.0 * s - ph * 160.0 * s
            x = tip[0] + math.sin(f * 5.0 + tt * 1.7 + k * 2.1) * (18.0 + 70.0 * f) * s - 30.0 * f * s
            pts.append((x, y))
        bass.line_band(c, pts, K.PAPER, width=max(3.0, 13.0 * s), seed=838 + k, taper=(0.4, 1.4),
                       alpha=a * 0.2 * (1.0 - ph))


# ============================================================================ hands
HANDS = {"architect": dict(w=1.0, rim=K.PAPER, cuff=None, sleeve=(0.07, 0.08, 0.11)),
         "cracker": dict(w=0.86, rim=K.GOLD, cuff=K.PAPER, sleeve=K.INK),
         "knight": dict(w=1.3, rim=K.RED, cuff=None, sleeve=K.INK)}
# a pinch seen from the side, the forearm coming from -x, the grip (a piece's crown) at (0, 0):
# the back of the hand, the knuckles, the index finger curling down to the grip, the thumb
# meeting it, the other fingers curled under the palm
_PINCH = [(-175, -100), (-128, -114), (-78, -116), (-36, -106), (-6, -90), (16, -68), (28, -42), (30, -16), (24, 0),
          (12, 4), (6, -10), (2, -28), (-6, -40), (-14, -28), (-18, -8), (-22, 4), (-36, 8), (-52, -2), (-62, -22),
          (-76, -18), (-98, -12), (-122, -22), (-150, -38), (-175, -46)]
_OPEN = [(-175, -100), (-128, -114), (-78, -116), (-36, -108), (0, -96), (30, -80), (52, -60), (60, -36), (54, -22),
         (42, -22), (38, -40), (24, -56), (-6, -58), (-26, -46), (-38, -26), (-44, -10), (-56, -6), (-66, -18),
         (-72, -34), (-82, -22), (-100, -14), (-122, -22), (-150, -38), (-175, -46)]
# a finger pointing (v5: her tap on the X), the fingertip at (0, 0): the back of the hand, the
# index finger straight out and down to the tip, the other fingers curled under, the thumb tucked
_POINT = [(-175, -100), (-130, -110), (-92, -104), (-66, -86), (-42, -58), (-22, -32), (-8, -14), (2, -4), (2, 6),
          (-8, 8), (-22, -6), (-38, -24), (-50, -34), (-58, -18), (-70, -4), (-88, 0), (-104, -6), (-114, -18),
          (-128, -24), (-150, -38), (-175, -46)]
HAND_LEN = 235.0            # hand units from the wrist to the fingertip


def hand(c, who, wrist, grip, s=1.0, open_u=0.0, rim_off=(-3.0, -3.0), flare=0.05, rim=None, point=False):
    """A hand reaching in from `wrist` (frame px, off the frame) to pinch a piece's crown (or a
    stick of chalk) at `grip`, seen from the side: the coat sleeve (widening toward the camera
    by `flare` per unit of length), the back of the hand, finger and thumb closing on the grip.
    open_u 0..1 opens them (letting go). s: px per hand unit (HAND_LEN * s is the hand's length;
    a hand is about one and a half chess pieces tall). rim: the rim's colour (default: the
    owner's; GOLD by a match). point: the index finger out, its tip at `grip` (a tap)."""
    spec = dict(HANDS[who])
    if rim is not None:
        spec["rim"] = rim
    k = s * spec["w"]
    dx, dy = grip[0] - wrist[0], grip[1] - wrist[1]
    ang = math.atan2(dy, dx)
    # the hand is drawn with its back up: flip it when the forearm comes from the right
    flip = -1.0 if math.cos(ang) < 0.0 else 1.0
    o = clamp(open_u)
    if point:
        pts = spline(_POINT, n=3)
    else:
        pts = spline([(lerp(a[0], b[0], o), lerp(a[1], b[1], o)) for a, b in zip(_PINCH, _OPEN)], n=3)
    L = math.hypot(dx, dy)
    c.save()
    c.translate(*grip)
    c.rotate(ang if flip > 0 else ang + math.pi)
    c.scale(k * flip, k)
    far = -170.0 - L / k - 60.0
    fl = min(150.0, flare * (-150.0 - far))
    sleeve = bass.orient([(far, -132.0 - fl), (-150.0, -132.0), (-146.0, -22.0), (far, -22.0 + fl)], True)
    handp = bass.orient(pts, True)
    c.save()
    c.translate(rim_off[0] / k * flip, rim_off[1] / k)
    bass.fill_polys(c, [sleeve, handp], spec["rim"])
    c.restore()
    bass.fill_polys(c, [handp], K.INK)
    bass.fill_polys(c, [sleeve], spec["sleeve"])
    if spec["cuff"] is not None:                 # the old man's shirt cuff and a gold link
        bass.fill_polys(c, [bass.orient([(-200, -136), (-150, -130), (-150, -24), (-200, -18)], True)], spec["cuff"])
        K.dot(c, (-176, -76), 9.0, K.GOLD)
    elif who == "architect":                     # the glove's flared cuff
        bass.fill_polys(c, [bass.orient([(-180, -140), (-148, -126), (-146, -24), (-180, -10)], True)], K.INK)
        bass.line_band(c, [(-180, -140), (-180, -10)], spec["rim"], width=4.0)
    c.restore()
