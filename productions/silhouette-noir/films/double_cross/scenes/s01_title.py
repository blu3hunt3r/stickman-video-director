"""s01 TITLE (0-16). The bank at night, at eye level (s04's street): four chalk dots tick in at
the corners of its front and dotted lines join them: the bank, marked, held a bar while the
camera pushes in. The street folds flat,
back to front (s04's pop-up run backwards: the moon, the neighbours and the lamp, then the clock,
the pediment, the front), as the camera tilts up over it to straight down, and the chalk outline
lies down with the front onto the paper that was under the street all along: the blueprint, the
night lifting off it. The outline is the bank's on the plan, and the plan rules itself in from it,
one part per beat (the sewer's branch drawn running right under the vault: the plant). A white
strip slashes across the frame and a red one crosses it: the title X, DOUBLE above, CROSS below.
The words lift away, the X shrinks onto the vault and lands as the plan's chalk X, a gold lens
opens off it on what it marks (the vault's gold, through its door) and holds there with the plan
still, the gold glinting twice; then the camera tilts down to the table as the lamp comes on,
which is where s02 begins (the lens closes there).

v5 is v3's opening given time: v3 ran it in 12 s, which read as rushed. Each part now has its own
bar (the bank marked 0-4, the fold 4-6, the plan 6-9.4, the title 10-12, the gold 13-14.5).
"""
import math

from engine import bass
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.double_cross import bank as Bk
from films.double_cross import kit as K
from films.double_cross import plan as P

T_FADE = 0.2                           # in from black
T_DOTS = (0.5, 1.0, 1.5, 2.0)          # the bank front's corners, clockwise from the top left
T_JOIN = (2.0, 2.5)                    # dotted lines join them: the bank, marked (held to 4.0)
FOLDS = (("moon", 4.0), ("neighbours", 4.0), ("alley", 4.0), ("lamp", 4.0), ("clock", 4.25), ("pediment", 4.5),
         ("portico", 4.75), ("facade", 4.75))      # the street folds flat, back to front (s04's pops run backwards)
FOLD_DUR = 0.3
T_UP = (4.25, 6.0)                     # the camera tilts up over the street to the plan, straight down
T_LIE = (4.3, 5.95)                    # the chalk outline lies down with the front: the bank's outline on the plan
T_DAWN = (4.5, 5.9)                    # the night lifts off the paper
T_GROUPS = (("bank", 6.0), ("vault", 6.5), ("rooms", 7.0), ("streets", 7.5), ("manholes", 8.0),
            ("sewer", 8.5), ("side", 9.0))
GROUP_DUR = 0.42
T_DIM = 9.75                           # the plan dims under the title
T_STRIP_W = 10.0                       # the white strip lands (she)
T_STRIP_R = 10.5                       # the red strip lands across it (he)
STRIP_IN = 0.24                        # each slashes in over this long, landing on its beat
T_DOUBLE = 11.0
T_CROSS = 11.5
T_LIFT = 12.0                          # the words lift away, the X starts to shrink
T_LAND = 13.0                          # the X lands on the vault as the chalk X
T_GOLD = 13.1                          # a gold lens opens off it: the gold it marks, held with the plan still
T_GLINTS = (13.5, 14.5)                # a glint off the top bar, on the beat, twice
T_TILT = (14.5, 16.0)                  # the camera tilts down to the table (s02 starts there)
T_LAMP = 14.75                         # the lamp comes on

# the street (s04's eye level, its plan depths) and the camera's way up off it
FACADE_Y = 1300.0                      # the bank's front (plan y)
ROUTE_Y = 1368.0                       # the road
EYE = Bk.eye_cam(P.PlanCam(545.0, 1300.0, 1.15, 0.0, 0.0, 540.0, 1480.0))     # s04's eye level (its TILT_TO)
EYE0 = Bk.Cam(EYE.x, EYE.y + 12.0, EYE.zoom * 0.94)                           # a touch wider: the slow push in
C0 = (540.0, 960.0)                    # the title X's crossing, frame px
STRIP_W = 118.0
CAM0 = P.PlanCam(540.0, 960.0, 0.965, 90.0, 0.0)
CAM1 = P.PlanCam(540.0, 960.0, 1.0, 90.0, 0.0)
_DIAG = math.atan2(1920.0, 1080.0)     # the frame's diagonal

# the gold lens (frame px); s02 closes it over GOLD_SHUT (s02 time)
GOLD_C = (790.0, 320.0)
GOLD_R = 185.0
GOLD_SHUT = (0.35, 0.55)
GOLD_IN = (548.0, -36.0, 3.1)          # what the lens shows: Bk.vault_through's point at its centre (the gold
                                       # pile), and the zoom
GLINT_AT = ((557.0, -52.0), (521.0, -36.0))   # where the two glints catch: the top bar, a bar below it


def motion_blur(t, T):
    return 1


# ============================================================================ the cameras
def street_cam(t):
    """The set camera on the street (to T_UP[0]): a slow push in to s04's eye level."""
    return Bk.Cam.lerp(EYE0, EYE, ease("inout", clamp(t / T_UP[0])))


EYE_PC = P.PlanCam(*Bk.plan_cam_for(EYE, FACADE_Y))      # = s04's TILT_TO


def cam_at(t):
    """The camera as a P.PlanCam all the way: on the street (the set camera's equivalent), the
    tilt up to straight down, a slow drift in over the plan, the tilt down to the table."""
    if t < T_UP[0]:
        return P.PlanCam(*Bk.plan_cam_for(street_cam(t), FACADE_Y))
    if t < T_UP[1]:
        return P.PlanCam.lerp(EYE_PC, CAM0, ease("inout3", (t - T_UP[0]) / (T_UP[1] - T_UP[0])))
    top = P.PlanCam.lerp(CAM0, CAM1, ease("inout", clamp((t - T_UP[1]) / (T_TILT[0] - T_UP[1]))))
    u = clamp((t - T_TILT[0]) / (T_TILT[1] - T_TILT[0]))
    return P.PlanCam.lerp(top, P.TABLE, ease("inout3", u))


# ============================================================================ the street, folding flat
def _pops(t):
    """Each part of the street standing (1) .. folded flat (0)."""
    d = {name: 1.0 - clamp((t - t0) / FOLD_DUR) for name, t0 in FOLDS}
    d["car"] = 0.0
    return d


def _street(c, t):
    """The bank at night, at eye level, on the set camera (to T_UP[0])."""
    Bk.front_street(c, street_cam(t), t, pop=_pops(t), car_on=False)


def _folding(c, t, pc):
    """The street under the camera as it tilts up (T_UP): the earth in section below the road (gone
    as the paper opens), the road line, the lid, the bank's front folding flat on its line."""
    ea = 1.0 - ease("inout", clamp(pc.phi / 40.0))
    if ea > 0.0:
        a, b = pc.to_view((-3000.0, P.SHEET[3])), pc.to_view((4000.0, P.SHEET[3]))
        bass.fill_polys(c, [bass.orient([a, b, (b[0], 4000.0), (a[0], 4000.0)], True)], Bk.EARTH, ea)
        with Bk.TiltSet(pc, ROUTE_Y).on(c):
            Bk.band(c, (-400.0, 1.0), (1500.0, 1.0), 4.0, lerp(K.STEEL, K.NAVY, 0.25), seed=711, alpha=ea)
    with Bk.TiltSet(pc, P.MANHOLE_A[1]).on(c):
        Bk.manhole_lid(c, 0.0)
    with Bk.TiltSet(pc, FACADE_Y).on(c):
        Bk.facade(c, t, _pops(t))


def _flap(t):
    """The chalk outline's fold: its angle off the ground (radians) and its length (plan px), from
    standing on the bank's front to lying on the plan as the bank's outline."""
    u = ease("inout", clamp((t - T_LIE[0]) / (T_LIE[1] - T_LIE[0])))
    return math.radians(90.0 * (1.0 - u)), lerp(Bk.FACADE_H, FACADE_Y - P.BANK[1], u)


def _corners(t, pc):
    """The outline's corners in frame px, clockwise from the top left (the front's top two first)."""
    th, L = _flap(t)
    x0, x1 = Bk.FACADE_X
    y, z = FACADE_Y - L * math.cos(th), L * math.sin(th)
    return [pc.to_view((x0, y), z), pc.to_view((x1, y), z), pc.to_view((x1, FACADE_Y)), pc.to_view((x0, FACADE_Y))]


SIDE_DOTS = (31, 38, 31, 38)           # dots along each side (top, right, bottom, left): the plan's spacing


def _outline(c, t, pc):
    """The four corner dots and the dotted lines joining them, on the front and then on the plan,
    going as the bank's walls rule in over them."""
    a = 1.0 - clamp((t - T_GROUPS[0][1]) / 0.45)
    if t < T_DOTS[0] or a <= 0.0:
        return
    pts = _corners(t, pc)
    z = pc.zoom
    ju = ease("inout", clamp((t - T_JOIN[0]) / (T_JOIN[1] - T_JOIN[0])))
    if ju > 0.0:
        total = sum(SIDE_DOTS)
        shown = ju * total
        k = 0
        for i, n in enumerate(SIDE_DOTS):
            p, q = pts[i], pts[(i + 1) % 4]
            for j in range(1, n):
                k += 1
                g = clamp(shown - k + 1.0)
                if g <= 0.0:
                    break
                f = j / n
                K.dot(c, (lerp(p[0], q[0], f), lerp(p[1], q[1], f)), 5.0 * z * ease("outback", g), K.PAPER,
                      seed=3 * 131 + k, alpha=a)
            k += 1
    for i, (p, ti) in enumerate(zip(pts, T_DOTS)):
        if t >= ti:
            K.dot(c, p, 11.0 * z * ease("outback", clamp((t - ti) / 0.22)), K.PAPER, seed=40 + i, alpha=a)


# ============================================================================ the plan
def _plan(c, t, cam):
    """The blueprint (the street's ground all along), the night lifting off it, the bank ruling
    itself in, the X, the lamp's pool."""
    if cam.flat() < 0.01:                                # edge-on at eye level: nothing to see (and no matrix)
        return
    night = 1.0 - ease("inout", clamp((t - T_DAWN[0]) / (T_DAWN[1] - T_DAWN[0])))
    with cam.ground(c):
        if t >= T_TILT[0] and cam.phi < 89.0:
            P.sheet_shadow(c, alpha=0.55 * clamp((90.0 - cam.phi) / 12.0))
        P.draw_sheet(c, 1.0)
        if night > 0.0:
            x0, y0, x1, y1 = P.SHEET
            bass.fill_polys(c, [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]], K.NAVY, 0.84 * night)
        if t >= T_GROUPS[0][1]:
            u = {name: clamp((t - t0) / GROUP_DUR) for name, t0 in T_GROUPS}
            P.draw_plan(c, u=u)
        if t >= T_LAND:
            K.xmark(c, P.X_VAULT, 56.0, seed=20)
        P.lamp(c, ease("out", clamp((t - T_LAMP) / 0.6)))


# ============================================================================ the title
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


# ============================================================================ the gold lens
def gold_lens(c, anchor, u, t):
    """The lens off the X (anchor, frame px): the vault seen through its open door, the gold
    stacked on its floor in its own light; a glint off the top bar, twice. u opens (and closes)
    it; t is s01's time (s02 passes its own plus s01's length)."""
    if u <= 0.0:
        return
    px, py, z = GOLD_IN

    def inside(cc):
        cc.save()
        cc.translate(GOLD_C[0], GOLD_C[1])
        cc.scale(z, z)
        cc.translate(-px, -py)
        Bk.vault_through(cc, t, light="gold", gold=1.0)
        cc.restore()
        for i, tg in enumerate(T_GLINTS):
            k = (t - tg) / 0.45
            if 0.0 < k < 1.0:
                bar = GLINT_AT[i]
                top = (GOLD_C[0] + z * (bar[0] - px), GOLD_C[1] + z * (bar[1] - py))
                K.twinkle(cc, top, 40.0 * math.sin(math.pi * k), K.PAPER, rot=15.0 * k)

    K.callout(c, anchor, GOLD_C, GOLD_R, inside, u=u, color=K.GOLD, ring_w=10.0, dot_r=9.0, line_w=4.5, seed=35)


# ============================================================================ render
def render(f, t, T):
    up = clamp((t - T_UP[0]) / (T_UP[1] - T_UP[0]))
    K.scene_setup(f, lerp(K.NAVY, K.DEEP, ease("inout", up)))
    cam = cam_at(t)
    with f.screen() as c:
        if t <= T_UP[0]:
            _street(c, t)
        else:
            _plan(c, t, cam)
            if t < T_UP[1]:
                _folding(c, t, cam)
        _outline(c, t, cam)
        # the title: the plan dims, two strips cross, the words stamp in
        landed = t >= T_LAND
        dim = clamp((t - T_DIM) / 0.3) * (1.0 - clamp((t - (T_LIFT + 0.2)) / 0.7))
        if dim > 0.0:
            K.fill(c, K.NAVY, alpha=0.62 * dim)
        if t >= T_STRIP_W - STRIP_IN and not landed:
            for i, (a, b, w, col) in enumerate(_strips(t, cam)):
                bass.fill_polys(c, [_strip_poly(a, b, w, 60 + i)], col)
            _words(c, t)
        # the landing: a small chalk ripple off the X, and the lens on what it marks
        if T_LAND <= t < T_LAND + 0.7:
            K.ripple(c, cam.to_view(P.X_VAULT), t, T_LAND, K.PAPER, n=2, every=0.14, life=0.5, r0=24.0, r1=86.0,
                     width=4.0)
        gold_lens(c, cam.to_view(P.X_VAULT), clamp((t - T_GOLD) / 0.3), t)
        if t < T_FADE:
            K.fill(c, K.INK, alpha=1.0 - t / T_FADE)


def _pan(p):
    return round(clamp((p[0] - 540.0) / 540.0, -1.0, 1.0), 2)


def cues(T):
    out = [Cue(0.0, "night on the street: a distant city, the wind between the buildings (the bank at night)",
               gain_db=-24, dur=T_UP[1])]
    for i, ti in enumerate(T_DOTS):
        out.append(Cue(ti, "chalk tap: a dot pops at a corner of the bank's front", gain_db=-10,
                       pan=(-0.6, 0.6, 0.6, -0.6)[i]))
    out.append(Cue(T_JOIN[0], "a dry run of chalk ticks: dotted lines join the corners", gain_db=-18,
                   dur=T_JOIN[1] - T_JOIN[0]))
    xs = {"moon": Bk.MOON_AT[0], "neighbours": 540.0, "alley": Bk.ALLEY_X[0], "lamp": Bk.LAMP_X, "clock": Bk.CLOCK_AT[0],
          "pediment": 735.0, "portico": 735.0, "facade": 365.0}
    seen = set()
    for name, t0 in FOLDS:
        if t0 in seen:                                   # parts folding together: one snap
            continue
        seen.add(t0)
        names = [n for n, t1 in FOLDS if t1 == t0]
        x = sum(xs[n] for n in names) / len(names)
        out.append(Cue(t0, f"a card folds flat: the {', the '.join(names)} (a pop-up book closing)",
                       gain_db=-15 if "facade" in names else -18, pan=_pan(street_cam(t0).to_frame((x, -200.0)))))
    out.append(Cue(T_UP[0], "a paper whoosh: the camera tilts up over the street to the plan, straight down",
                   gain_db=-14, dur=T_UP[1] - T_UP[0]))
    out.append(Cue(T_LIE[1], "the chalk outline lies down on the plan (a soft paper settle)", gain_db=-20))
    for name, t0 in T_GROUPS:
        out.append(Cue(t0, f"chalk scratch: the {name} ruled in", gain_db=-12, dur=GROUP_DUR))
    out += [Cue(T_DIM, "the music drops a breath before the title", gain_db=-20),
            Cue(T_STRIP_W, "whoosh-thud: the white strip slashes across", gain_db=-6, pan=0.3),
            Cue(T_STRIP_R, "whoosh-thud, heavier: the red strip crosses it", gain_db=-5, pan=-0.3),
            Cue(T_DOUBLE, "title stamp: DOUBLE", gain_db=-6),
            Cue(T_CROSS, "title stamp: CROSS", gain_db=-6),
            Cue(T_LIFT, "the words lift away (paper whoosh up and down)", gain_db=-12),
            Cue(T_LAND, "thud: the X lands on the vault as the chalk X", gain_db=-8),
            Cue(T_GOLD, "a soft gold shimmer: the lens opens on the vault's gold (a vibraphone roll, a faint clink)",
                gain_db=-16, pan=_pan(GOLD_C)),
            Cue(T_GLINTS[0], "a glint off the gold (ting)", gain_db=-20, pan=_pan(GOLD_C)),
            Cue(T_GLINTS[1], "a second glint off the gold (ting, higher)", gain_db=-21, pan=_pan(GOLD_C)),
            Cue(T_LAMP, "the table lamp clicks on; a low warm hum", gain_db=-14, dur=T.duration - T_LAMP)]
    return out
