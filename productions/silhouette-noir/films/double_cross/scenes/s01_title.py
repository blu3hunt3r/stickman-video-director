"""s01 TITLE (0-12). Four chalk dots tick in at the corners of a sheet that is not there yet, and
dotted lines join them. The blueprint unrolls inside that outline, and the bank rules itself in
chalk, one part per beat (the sewer's branch drawn running right under the vault: the plant). A
white strip slashes across the frame and a red one crosses it: the title X, DOUBLE above, CROSS
below. The words lift away, the X shrinks onto the vault and lands as the plan's chalk X, and the
camera tilts down to the table as the lamp comes on, which is where s02 begins.
"""
import math

from engine import bass
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.double_cross import kit as K
from films.double_cross import plan as P

T_DOTS = (0.5, 1.0, 1.5, 2.0)          # the sheet's corners, clockwise from the top left
T_JOIN = (2.0, 2.5)                    # dotted lines join them
T_UNROLL = (2.5, 4.0)                  # the blueprint unrolls inside them
T_GROUPS = (("bank", 4.0), ("vault", 4.5), ("rooms", 5.0), ("streets", 5.5), ("manholes", 6.0),
            ("sewer", 6.5), ("side", 7.0))
GROUP_DUR = 0.42
T_DIM = 7.75                           # the plan dims under the title
T_STRIP_W = 8.0                        # the white strip lands (she)
T_STRIP_R = 8.5                        # the red strip lands across it (he)
STRIP_IN = 0.24                        # each slashes in over this long, landing on its beat
T_DOUBLE = 9.0
T_CROSS = 9.5
T_LIFT = 10.0                          # the words lift away, the X starts to shrink
T_LAND = 11.0                          # the X lands on the vault as the chalk X
T_TILT = (10.55, 12.0)                 # the camera tilts down to the table (s02 starts there)
T_LAMP = 10.75                         # the lamp comes on

C0 = (540.0, 960.0)                    # the title X's crossing, frame px
STRIP_W = 118.0
CAM0 = P.PlanCam(540.0, 960.0, 0.965, 90.0, 0.0)
CAM1 = P.PlanCam(540.0, 960.0, 1.0, 90.0, 0.0)
_DIAG = math.atan2(1920.0, 1080.0)     # the frame's diagonal


def motion_blur(t, T):
    return 1


def cam_at(t):
    top = P.PlanCam.lerp(CAM0, CAM1, ease("out", clamp(t / T_TILT[0])))
    u = clamp((t - T_TILT[0]) / (T_TILT[1] - T_TILT[0]))
    return P.PlanCam.lerp(top, P.TABLE, ease("inout3", u))


def _sheet_corners():
    x0, y0, x1, y1 = P.SHEET
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _strips(t, cam):
    """The two title strips at t: [(a, b, width, colour, alpha)] in frame px, white then red."""
    out = []
    land = clamp((t - T_LIFT) / (T_LAND - T_LIFT))
    e = ease("inout3", land)
    h = 28.0
    targets = [(cam.to_view((P.X_VAULT[0] - h, P.X_VAULT[1] - h)), cam.to_view((P.X_VAULT[0] + h, P.X_VAULT[1] + h))),
               (cam.to_view((P.X_VAULT[0] + h, P.X_VAULT[1] - h)), cam.to_view((P.X_VAULT[0] - h, P.X_VAULT[1] + h)))]
    for i, (t0, col) in enumerate(((T_STRIP_W, K.PAPER), (T_STRIP_R, K.RED))):
        if t < t0 - STRIP_IN:
            continue
        ang = _DIAG if i == 0 else math.pi - _DIAG
        d = (math.cos(ang), math.sin(ang))
        L = 1350.0
        # slash in along its own axis from off the frame, landing on the beat with a settle
        p = clamp((t - (t0 - STRIP_IN)) / STRIP_IN)
        slide = (1.0 - ease("outback", p)) * 2400.0
        sgn = -1.0
        a = (C0[0] - d[0] * L + sgn * d[0] * slide, C0[1] - d[1] * L + sgn * d[1] * slide)
        b = (C0[0] + d[0] * L + sgn * d[0] * slide, C0[1] + d[1] * L + sgn * d[1] * slide)
        w = STRIP_W
        if land > 0.0:
            ta, tb = targets[i]
            a = (lerp(a[0], ta[0], e), lerp(a[1], ta[1], e))
            b = (lerp(b[0], tb[0], e), lerp(b[1], tb[1], e))
            w = lerp(STRIP_W, 10.0 * cam.zoom, e)
        if i == 1 and land > 0.7:
            col = tuple(lerp(x, y, clamp((land - 0.7) / 0.3)) for x, y in zip(K.RED, K.PAPER))
        out.append((a, b, w, col))
    return out


def _strip_poly(a, b, w, seed):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    n = (-dy / L * w / 2.0, dx / L * w / 2.0)
    pts = [(a[0] + n[0], a[1] + n[1]), (b[0] + n[0], b[1] + n[1]), (b[0] - n[0], b[1] - n[1]), (a[0] - n[0], a[1] - n[1])]
    return bass.orient(bass.cut(pts, seed=seed, amp=0.9, seg=(60.0, 180.0)), True)


def _words(c, t):
    """DOUBLE in the X's top triangle and CROSS in its bottom one: stamped on their beats,
    lifting away (up and down) from T_LIFT."""
    lift = clamp((t - T_LIFT) / 0.55)
    for word, t0, y, frm in (("DOUBLE", T_DOUBLE, 286.0, "top"), ("CROSS", T_CROSS, 1648.0, "bottom")):
        if t < t0 - 0.2 or lift >= 1.0:
            continue
        g = bass.title_glyphs(word, width=530.0 if word == "DOUBLE" else 490.0, tracking=0.06, seed=7, rough=0.8,
                              jitter=0.6)
        if lift <= 0.0:
            u = clamp((t - (t0 - 0.2)) / 0.32)
            bass.draw_title(c, g, (540.0, y), K.PAPER, u=u, anim="stamp", order="center", overlap=0.85, big=2.2)
        else:
            bass.draw_title(c, g, (540.0, y), K.PAPER, u=1.0 - lift, anim="slide", frm=frm, order="center",
                            overlap=0.6, dist=900.0, ease="in3")


def render(f, t, T):
    K.scene_setup(f, K.DEEP)
    cam = cam_at(t)
    with f.screen() as c:
        un = ease("inout", clamp((t - T_UNROLL[0]) / (T_UNROLL[1] - T_UNROLL[0])))
        x0, y0, x1, y1 = P.SHEET
        yb = lerp(y0, y1, un)
        landed = t >= T_LAND
        with cam.ground(c):
            if cam.phi < 89.0:
                P.sheet_shadow(c, alpha=0.55 * clamp((90.0 - cam.phi) / 12.0))
            P.draw_sheet(c, un)
            if t >= T_GROUPS[0][1]:
                u = {name: clamp((t - t0) / GROUP_DUR) for name, t0 in T_GROUPS}
                P.draw_plan(c, u=u)
            if landed:
                K.xmark(c, P.X_VAULT, 56.0, seed=20)
            # the corner dots and the dotted outline, eaten by the sheet as it unrolls past them
            corners = _sheet_corners()
            if t < T_UNROLL[1] + 0.1:
                ju = clamp((t - T_JOIN[0]) / (T_JOIN[1] - T_JOIN[0]))
                if ju > 0.0:
                    c.save()
                    c.new_path()
                    top = yb + 14.0 if un > 0.0 else y0 - 60.0
                    c.rectangle(x0 - 60.0, top, x1 - x0 + 120.0, y1 - top + 80.0)
                    c.clip()
                    K.route(c, corners + [corners[0]], ease("inout", ju), K.PAPER, r=5.0, gap=24.0, head=0.0, seed=3)
                    c.restore()
                for i, (p, ti) in enumerate(zip(corners, T_DOTS)):
                    if t < ti:
                        continue
                    pop = ease("outback", clamp((t - ti) / 0.22))
                    gone = clamp((yb - p[1] + 20.0) / 30.0) if un > 0.0 else 0.0
                    if gone < 1.0:
                        K.dot(c, p, 11.0 * pop, K.PAPER, seed=40 + i, alpha=1.0 - gone)
            P.lamp(c, ease("out", clamp((t - T_LAMP) / 0.6)))
        # the title: the plan dims, two strips cross, the words stamp in
        dim = clamp((t - T_DIM) / 0.3) * (1.0 - clamp((t - (T_LIFT + 0.2)) / 0.7))
        if dim > 0.0:
            K.fill(c, K.NAVY, alpha=0.62 * dim)
        if t >= T_STRIP_W - STRIP_IN and not landed:
            for i, (a, b, w, col) in enumerate(_strips(t, cam)):
                bass.fill_polys(c, [_strip_poly(a, b, w, 60 + i)], col)
            _words(c, t)
        # the landing: a small chalk ripple off the X
        if T_LAND <= t < T_LAND + 0.7:
            K.ripple(c, cam.to_view(P.X_VAULT), t, T_LAND, K.PAPER, n=2, every=0.14, life=0.5, r0=24.0, r1=86.0,
                     width=4.0)


def cues(T):
    out = []
    for i, ti in enumerate(T_DOTS):
        out.append(Cue(ti, "chalk tap: a dot pops at a corner of the sheet", gain_db=-10, pan=(-0.6, 0.6, 0.6, -0.6)[i]))
    out += [Cue(T_JOIN[0], "a dry run of chalk ticks: dotted lines join the corners", gain_db=-18, dur=T_JOIN[1] - T_JOIN[0]),
            Cue(T_UNROLL[0], "the blueprint unrolls (paper unrolling, the roll bumps down)", gain_db=-10,
                dur=T_UNROLL[1] - T_UNROLL[0])]
    for name, t0 in T_GROUPS:
        out.append(Cue(t0, f"chalk scratch: the {name} ruled in", gain_db=-12, dur=GROUP_DUR))
    out += [Cue(T_DIM, "the music drops a breath before the title", gain_db=-20),
            Cue(T_STRIP_W, "whoosh-thud: the white strip slashes across", gain_db=-6, pan=0.3),
            Cue(T_STRIP_R, "whoosh-thud, heavier: the red strip crosses it", gain_db=-5, pan=-0.3),
            Cue(T_DOUBLE, "title stamp: DOUBLE", gain_db=-6),
            Cue(T_CROSS, "title stamp: CROSS", gain_db=-6),
            Cue(T_LIFT, "the words lift away (paper whoosh up and down)", gain_db=-12),
            Cue(T_LAND, "thud: the X lands on the vault as the chalk X", gain_db=-8),
            Cue(T_LAMP, "the table lamp clicks on; a low warm hum", gain_db=-14, dur=T.duration - T_LAMP)]
    return out
