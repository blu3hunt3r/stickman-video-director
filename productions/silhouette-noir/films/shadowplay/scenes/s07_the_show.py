"""s07 · THE SHOW (12.5 s). Inside apartment 9: no murder. A lamp, a sheet, two paper dolls.
She switches the lamp on and her own giant shadow is thrown across the sheet.

IN   window shape from s06 (1.0 s, centred on 0): the cut-paper window grows from window 9's
     rect (444, 840)-(636, 1080). We are already inside: the camera starts with apartment
     9's window (behind the hanging sheet) on that same rect, then pans to the door.
-0.05-0.75 the door creaks open (left wall): she stands in the doorway against the hall
           light, her shadow in the wedge across the floor; 0.55 she steps in
1.45       she strikes a match (flare); a small warm flame moves through the dark room
           L16 "There was no murder. Just a lamp... a sheet... and two paper dolls."
3.08       [lamp]  the match lifted to the bare bulb on its tripod: the glass catches it
4.14       [sheet] she turns to the hanging sheet; the flame's glow swims on the cloth
5.78       [dolls] the match held out over the table: two paper dolls on their rods (the
           show's puppets: the bowler man, jagged knife arm raised; the woman folded over her
           rod) and the red paper splash scraps. In the matchlight their shadows stand up
           faintly on the sheet behind them: the show, small and wavering
7.18       she shakes the match out: dark (hall light, the street's glow through the sheet)
           L17 "It was never a crime. It was a show."
9.08-9.69  in the dark she reaches back to the bulb's socket
9.63       [show] click: the lamp is on, the sheet blazes, and her own GIANT shadow is thrown
           across it, the man doll's knife arm raised against it; her coat goes RED
10.30-11.28 she turns from the sheet toward the window and walks round it; her shadow slides
           off the sheet
11.28      cut: window 9 from inside (NineWindow, the sheet pushed aside on its wire): she
           stands at the glass looking out, three-quarter back; the show lamp's warmth behind
           her; across the rainy street her own building, her window lit
OUT  hard cut to s08 (over her shoulder through the same window, closer).
"""
import math
from functools import lru_cache

import cairo
import numpy as np

from engine import atmos, draw
from engine.core import clamp, ease, fbm1, smoothstep
from engine.frame import Camera
from engine.motion import Actor
from engine.palette import PAPER, SHADOWPLAY as PAL
from engine.timing import Cue
from films.shadowplay import cast, sets
from films.shadowplay.sets_base import PX_M
from films.shadowplay.scenes import _lib_s06_s07 as L

INK = PAL.ink
AMBER = PAL.light
HOT = PAL.lamp_hot
COLD = L.COLD

APT = sets.Apartment9((540.0, 880.0), 1.0)
R = APT.room
LAMP3 = APT.bulb3d("front")                   # (0.45, 1.62, 2.15)
BULB = APT.bulb("front")
TX, TZ, TW, TD, TH = APT.TABLE
DOLLS3 = (0.0, 1.35, TZ)
MAN3 = (TX + APT.RODS["man"][0], 1.50, TZ)
WOMAN3 = (TX + APT.RODS["woman"][0], 1.42, TZ)
SCRAPS3 = (0.05, TH, 2.80)
CLIP_Y = R.P(0.0, TH + 0.07, TZ - 0.08)[1]   # nothing of the dolls below the rig block

T_STRIKE = 1.45
T_OUT = 7.18                                  # match shaken out
T_WIN = 11.28                                 # cut to the window
T_HOOK = 2.2                                  # before: she is drawn after the door; after: after the props


def _times(T):
    def at(w, d):
        try:
            return T.at(w)
        except Exception:                     # noqa: BLE001
            return d
    return dict(lamp=at("lamp", 3.084), sheet=at("sheet", 4.14), dolls=at("dolls", 5.777),
                show=at("show", 9.632), crime=at("crime", 8.332))


# =========================================================================== her (room)
PXM = PX_M
Z_KEYS = [(-3.0, 1.75), (0.55, 1.75), (1.30, 1.80), (1.62, 1.80), (3.05, 2.00, "inout"), (4.45, 2.00),
          (5.35, 2.60, "inout"), (7.80, 2.60), (8.60, 2.50, "inout"), (10.55, 2.50), (11.45, 3.25, "in")]


def _z(t):
    return L.keys(t, Z_KEYS)


def _map(a, t):
    """(foot world point, k, xc): her canonical frame -> world at time t (k = scale)."""
    xc = a.root(t)[0]
    Z = _z(t)
    return R.P(xc / PXM, 0.0, Z), R.ppm(Z) / PXM, xc


def _to_canon(a, t, w):
    foot, k, xc = _map(a, t)
    return ((w[0] - foot[0]) / k + xc, (w[1] - foot[1]) / k)


@lru_cache(maxsize=4)
def _her(show=9.632):
    a = Actor(cast.HER, L.her_look(), x=-1.95 * PXM, ground=0.0, facing=1, seed=71)
    a.stand(until=0.55, at=-3.0, idle=0.3)
    a.walk(to=-1.25 * PXM, gait="walk", at=0.55)                 # into the room
    a.stand(until=1.62, idle=0.2)
    a.walk(to=0.0, gait="walk", speed=0.56, at=1.62)            # the flame through the dark
    a.stand(until=3.95, idle=0.2)
    a.turn(-55.0, dur=0.45, at=3.95, via=-28.0)                  # to the sheet
    a.walk(to=0.76 * PXM, gait="stroll", yaw=-55.0, at=4.45)     # round the lamp to the table's end
    a.turn(-150.0, dur=0.45, at=5.30, via=-90.0)                 # faces the dolls (left, away)
    a.stand(until=7.35, idle=0.15)
    a.turn(-95.0, dur=0.5, at=7.35, via=-120.0)                  # in the dark: her back to us
    a.walk(to=0.24 * PXM, gait="stroll", yaw=-95.0, at=7.80, turn=0)
    a.stand(until=10.30, idle=0.12)
    a.turn(-30.0, dur=0.45, at=10.30, via=-90.0)                 # toward the window
    a.walk(to=1.20 * PXM, gait="walk", yaw=-30.0, at=10.55, turn=0)
    a.stand(until=30.0)
    # the strike: matchbox in the left hand, the right strikes across it
    a.key("arm.L.sh", [(1.05, 4.0), (1.30, 40.0, "inout"), (1.62, 34.0), (1.95, 6.0, "inout")], fade=0.2)
    a.key("arm.L.elbow", [(1.05, 10.0), (1.30, 100.0, "inout"), (1.62, 96.0), (1.95, 14.0, "inout")], fade=0.2)
    a.key("arm.R.sh", [(1.05, 4.0), (1.32, 46.0, "inout"), (1.45, 30.0, "in"), (1.62, 60.0, "out3"),
                       (2.95, 62.0)], fade=0.2)
    a.key("arm.R.elbow", [(1.05, 10.0), (1.32, 76.0, "inout"), (1.45, 46.0, "in"), (1.62, 70.0, "out3"),
                          (2.95, 66.0)], fade=0.2)
    a.key("arm.R.wrist", [(7.06, 0.0), (7.12, -45.0, "out3"), (7.18, 35.0, "inout"), (7.24, -25.0, "inout"),
                          (7.34, 0.0, "inout")], fade=0.08)

    # the match lifted to the bulb [lamp], held out over the dolls [dolls]; the switch [show]
    def at_bulb(t):
        return _to_canon(a, t, (BULB[0] - 10.0, BULB[1] + 26.0))

    def at_dolls(t):
        return _to_canon(a, t, R.P(0.30, 1.10, 2.80))

    def at_socket(t):
        return _to_canon(a, t, (BULB[0] + 4.0, BULB[1] + 18.0))
    a.reach("R", 3.02, 3.82, at_bulb, fade=0.32, grip=0.9)
    a.key("arm.R.sh", [(3.85, 62.0), (4.30, 70.0, "inout"), (5.25, 70.0)], fade=0.3)
    a.key("arm.R.elbow", [(3.85, 50.0), (4.30, 40.0, "inout"), (5.25, 40.0)], fade=0.3)
    a.reach("R", 5.62, 7.06, at_dolls, fade=0.34, grip=0.9)
    a.key("arm.R.sh", [(7.10, 40.0), (7.40, 6.0, "inout")], fade=0.12)
    a.key("arm.R.elbow", [(7.10, 40.0), (7.40, 12.0, "inout")], fade=0.12)
    a.reach("R", show - 0.25, show + 0.06, at_socket, fade=0.30, grip=0.8)
    # looks: up at the bulb, across at the sheet, down at the dolls, up at her shadow
    a.key("head", [(2.95, 0.0), (3.20, -20.0, "inout"), (3.80, -16.0), (4.25, -4.0, "inout"), (5.45, 6.0),
                   (5.85, 22.0, "inout"), (7.15, 20.0), (7.55, 2.0, "inout"), (show + 0.05, 0.0),
                   (show + 0.45, -18.0, "inout"), (10.25, -14.0), (10.55, 0.0, "inout")], fade=0.3)
    a.key("pitch", [(5.50, 0.0), (5.90, 10.0, "inout"), (7.10, 9.0), (7.50, 0.0, "inout")], fade=0.3)
    a.key("head_yaw", [(show + 0.05, 0.0), (show + 0.40, 10.0, "inout"), (10.25, 10.0), (10.50, 0.0)], fade=0.2)
    a.key("arm.L.abd", [(show + 0.10, 6.0), (show + 0.30, 16.0, "out3"), (10.25, 12.0), (10.50, 6.0, "inout")],
          fade=0.15)
    a.key("arm.L.elbow", [(show + 0.10, 12.0), (show + 0.30, 30.0, "out3"), (10.25, 24.0), (10.50, 12.0, "inout")],
          fade=0.15)
    a.key("y", [(show + 0.04, 0.0), (show + 0.16, 5.0, "out3"), (show + 0.50, 0.0, "inout")], mode="add")
    return a


def _hand(t, sk, M):
    """(fingers world, match-tip world, room point of the flame)."""
    hw = sk.j["fingers_R"]
    wr = sk.j["wrist_R"]
    ang = math.atan2(hw[1] - wr[1], hw[0] - wr[0])
    ang += -0.5 if math.cos(ang) >= 0 else 0.5         # the stick tilts up out of the fingers
    stick = 0.055 * PXM
    tip_c = (hw[0] + math.cos(ang) * stick, hw[1] + math.sin(ang) * stick)
    tip = M.transform_point(*tip_c)
    fing = M.transform_point(*hw)
    Z = _z(t) - 0.10
    d = Z - R.E[2]
    return fing, tip, ((tip[0] - R.ox) * d / R.F, R.E[1] - (tip[1] - R.oy) * d / R.F, Z)


def _match_level(t):
    if t < T_STRIKE - 0.012 or t > T_OUT + 0.3:
        return 0.0
    if t < T_STRIKE:
        return (t - (T_STRIKE - 0.012)) / 0.012
    v = 1.0 + 1.1 * math.exp(-(t - T_STRIKE) / 0.09)
    v *= 1.0 - 0.25 * smoothstep(6.6, 7.1, t)
    if t > T_OUT:
        v *= math.exp(-(t - T_OUT) / 0.03)
    return v


def _lamp(t, W_):
    return sets.switch(t, W_["show"], kind="bulb", seed=7)


# =========================================================================== camera
def _cam_keys(W_):
    s = W_["show"]
    return [(-0.6, (540.0, 854.5), 1.016), (-0.30, (540.0, 854.5), 1.016), (0.95, (430.0, 900.0), 1.0),
            (1.60, (440.0, 905.0), 1.02), (3.05, (560.0, 880.0), 1.16), (4.30, (570.0, 885.0), 1.22),
            (5.90, (604.0, 930.0), 2.10), (7.30, (602.0, 934.0), 2.22), (8.90, (548.0, 880.0), 1.40),
            (s, (548.0, 880.0), 1.40),
            (s + 0.70, (540.0, 870.0), 1.52, "out"), (10.35, (545.0, 870.0), 1.54), (T_WIN, (600.0, 880.0), 1.46)]


def _camera(t, W_):
    ks = _cam_keys(W_)
    xs = [(k[0], k[1][0]) + tuple(k[3:]) for k in ks]
    ys = [(k[0], k[1][1]) + tuple(k[3:]) for k in ks]
    zs = [(k[0], math.log(k[2])) + tuple(k[3:]) for k in ks]
    cam = Camera(L.keys(t, xs), L.keys(t, ys), math.exp(L.keys(t, zs)))
    if t > -0.30:
        cam = cam.shaken(t, amp=1.6 * smoothstep(-0.30, 0.6, t), rot_amp=0.04, freq=0.35, seed=77)
    return cam


# =========================================================================== dolls
POSE = L.doll_pose()


def _doll_light(t, W_, m3, ml):
    """(man, woman) light on the dolls: the match (each by its own distance) + the lamp."""
    lv = _lamp(t, W_)
    out = []
    for p3 in (MAN3, WOMAN3):
        v = 1.6 * min(ml, 1.3) * L.falloff(L.dist3(m3, p3), 0.40) if ml > 0 else 0.0
        out.append(v + 1.0 * lv)
    return tuple(out)


# =========================================================================== door
def _door_open(t):
    return sets.door_swing(t, [(-0.05, 0.0), (0.75, 0.86, "creak")])


def _door_mask(a, t):
    """Her body blocking the hall light: her long shadow in the wedge on the floor."""
    if t > 2.4:
        return None
    X = a.root(t)[0] / PXM
    Z = _z(t)
    z0, z1 = APT.DOOR_Z
    src = (-R.hw - 1.1, 2.75, z0 - 0.7)
    Xd = -R.hw
    s = (X - src[0]) / (Xd - src[0])

    def m(u, v):
        Zd = z1 - u * (z1 - z0)
        Yd = v * APT.DOOR_H
        Zp = src[2] + (Zd - src[2]) * s
        Yp = src[1] + (Yd - src[1]) * s
        dz = np.abs(Zp - Z)
        body = (dz < 0.19) & (Yp < 1.45) & (Yp > 0.0)
        head = (dz < 0.10) & (Yp >= 1.45) & (Yp < 1.74)
        return (body | head).astype(np.float32) * 0.9
    return m


# =========================================================================== lamp over her
def _lamp_stand(c, lv):
    """The show lamp's stand and glass again, over her when she is behind it (same geometry
    as Apartment9._draw_lamp / BareLamp.draw, so it lands exactly on the first pass)."""
    X, Z = APT.LAMP_FRONT
    s = R.ppm(Z) * APT.BULB_Y / 520.0
    base = R.P(X, 0.0, Z)
    h = 520.0 * s

    def P(x, y):
        return (base[0] + x, base[1] - y)
    pts = [P(math.sin(q) * (17 if q < math.pi * 0.62 or q > math.pi * 1.38 else 11) * s, h + 22 * s + math.cos(q) * 21 * s)
           for q in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
    draw.smooth(c, pts, close=True, tension=0.5)
    draw.fill(c, sets.mix((0.05, 0.05, 0.06), HOT, clamp(lv)))
    for sx in (-1, 0, 1):
        foot = P(sx * 120 * s, 0) if sx else P(16 * s, 0)
        draw.capsule(c, P(0, 150 * s), foot, 4 * s, 3 * s)
    draw.capsule(c, P(0, 40 * s), P(0, h - 8 * s), 4.5 * s, 3.5 * s)
    draw.capsule(c, P(0, 150 * s), P(0, 175 * s), 8 * s, 8 * s)
    draw.capsule(c, P(0, h * 0.62), P(0, h * 0.62 + 14 * s), 7 * s, 7 * s)
    draw.poly(c, [P(-9 * s, h - 10 * s), P(9 * s, h - 10 * s), P(8 * s, h + 8 * s), P(-8 * s, h + 8 * s)])
    draw.fill(c, INK)


# =========================================================================== room shot
def _render_room(f, t, W_):
    f.set_camera(_camera(t, W_))
    a = _her(W_["show"])
    sk = a.skeleton(t)
    foot, k, xc = _map(a, t)
    M = L.place_matrix(foot, k, xc, 0.0)
    X, Z = xc / PXM, _z(t)
    fing, tip, m3 = _hand(t, sk, M)
    ml = _match_level(t)
    lv = _lamp(t, W_)
    op = _door_open(t)
    lights = []
    if ml > 0.01:
        lights.append(APT.match_light(m3, level=1.4 * min(ml, 1.3), t=t, seed=7))
    dl = _doll_light(t, W_, m3, ml)
    sc_l = (1.6 * min(ml, 1.3) * L.falloff(L.dist3(m3, SCRAPS3), 0.30) if ml > 0 else 0.0) + 0.9 * lv
    lk = _her_look(ml, lv, X, Z)
    st = dict(a=a, sk=sk, M=M, X=X, Z=Z, ml=ml, lv=lv, op=op, fing=fing, tip=tip, lk=lk)

    def puppets(c, apt):
        if POSE is not None:
            L.draw_paper_dolls(c, apt, POSE, dl, clip_y=CLIP_Y)
        L.red_scraps(c, apt, sc_l)

    def casters(c):
        # one shadow pass at her depth: the rig's rods and the puppets are pre-mapped from the
        # table's depth so the same homothety throws them where they belong
        Mt = L.remap(APT, TZ, Z, LAMP3)
        c.save()
        c.transform(Mt)
        APT.draw_rig(c, 0.0, rods_only=True)
        c.restore()
        if POSE is not None:
            L.doll_casters(c, APT, POSE, M=Mt)
        L.draw_sk(c, sk, L.plain(lk), M, color=(0.0, 0.0, 0.0))

    def after_sheet(f_, t_):
        if ml > 0.01:
            _match_on_sheet(f_, t_, m3, ml)

    def after_props(f_, t_):
        if t_ >= T_HOOK:
            _draw_her(f_, t_, st)

    def after_door(f_, t_):
        if t_ < T_HOOK:
            _draw_her(f_, t_, st)

    APT.draw(f, t, lamp=lv, lamp_at="front", sheet=True, table=True, rig=True, crank=0.0, puppets=puppets,
             casters=casters, caster_z=Z, door_open=op, hall=1.0, door_mask=_door_mask(a, t), street=0.35,
             extra_lights=lights, hooks={"after_sheet": after_sheet, "after_props": after_props,
                                         "after_door": after_door}, dust=1.0)
    # the bulb's glass catching the match as she lifts it [lamp]
    if lv < 0.2 and ml > 0:
        # the clear glass catches the flame: a specular point toward the match (always, while
        # it burns), and when the match is close [lamp] the whole bulb glows from it
        g = clamp(1.8 * min(ml, 1.2) * L.falloff(L.dist3(m3, LAMP3), 0.22))
        sp = 0.55 * clamp(min(ml, 1.0)) + 0.45 * g
        s = R.ppm(LAMP3[2]) * APT.BULB_Y / 520.0
        dx, dy = tip[0] - BULB[0], tip[1] - BULB[1]
        n = math.hypot(dx, dy) or 1.0
        hp = (BULB[0] + dx / n * 7.0 * s, BULB[1] + dy / n * 9.0 * s)
        with f.light(blur=1.0) as A:
            if g > 0.01:
                A.save()
                A.translate(BULB[0], BULB[1])
                A.scale(1.0, 21.0 / 17.0)
                sets.glow(A, (0.0, 0.0), 19.0 * s, sets.mix(AMBER, HOT, 0.5), 0.55 * g)
                A.restore()
                sets.glow(A, BULB, 70.0 * s, AMBER, 0.22 * g)
            sets.glow(A, hp, 5.0 * s, (1.0, 0.97, 0.9), 0.9 * sp)
        with f.emit() as G:
            draw.circle(G, hp, 1.8 * s)
            draw.fill(G, HOT, 0.6 * sp)


def _her_look(ml, lv, X, Z):
    near = L.falloff(L.dist3((X, 1.3, Z), LAMP3), 0.55)
    match = clamp(min(ml, 1.0) * 0.22)
    lamp = clamp(1.25 * lv * near)
    return L.her_look(coat_k=0.08 + match + 0.80 * lamp, eyes=False)


def _match_on_sheet(f, t, m3, ml):
    """The match's glow swimming on the sheet, with the dolls' shadows standing up in it."""
    d = max(APT.SHEET_Z - m3[2], 0.1)
    c = R.P(m3[0], m3[1], APT.SHEET_Z)
    lvl = 1.9 * min(ml, 1.2) * L.falloff(d, 1.0)
    rr = 1.25 * R.ppm(APT.SHEET_Z)
    fl = 0.9 + 0.1 * math.sin(t * 23.0) + 0.06 * fbm1(t * 7.0, 3)
    with f.light(blur=7.0) as A:
        A.push_group()
        A.save()
        draw.poly(A, APT.sheet.outline(t))
        A.clip()
        sets.glow(A, c, rr, sets.mix(AMBER, HOT, 0.25), lvl * fl)
        A.restore()
        if POSE is not None and m3[2] < TZ - 0.1:
            cen, mag, soft = APT.shadow_map(TZ, m3)
            A.push_group()
            A.set_operator(cairo.OPERATOR_OVER)
            A.save()
            A.translate(cen[0], cen[1])
            A.scale(mag, mag)
            A.translate(-cen[0], -cen[1])
            APT.draw_rig(A, 0.0, rods_only=True)
            L.doll_casters(A, APT, POSE)
            A.restore()
            mask = A.pop_group()
            A.set_operator(cairo.OPERATOR_DEST_OUT)
            A.set_source(mask)
            A.paint_with_alpha(0.88)
            A.set_operator(cairo.OPERATOR_OVER)
        A.pop_group_to_source()
        A.paint()


def _draw_her(f, t, st):
    if t > T_WIN:
        return
    sk, M, X, Z, lk = st["sk"], st["M"], st["X"], st["Z"], st["lk"]
    ml, lv, op, fing, tip = st["ml"], st["lv"], st["op"], st["fing"], st["tip"]
    plain = L.plain(lk)
    in_door = X < -1.82
    with f.layer() as c:
        c.save()
        if in_door:
            c.new_path()
            draw.poly(c, APT.door.opening_quad())
            c.clip()
        c.push_group()
        L.draw_sk(c, sk, lk, M)
        if in_door and op < 0.5:
            c.set_operator(cairo.OPERATOR_DEST_OUT)
            draw.poly(c, APT.door.leaf_quad(op))
            draw.fill(c, (0, 0, 0))
            c.set_operator(cairo.OPERATOR_OVER)
        c.pop_group_to_source()
        c.paint()
        c.restore()
        if Z > LAMP3[2] + 0.02 and t >= T_HOOK:
            _lamp_stand(c, lv)
    L.occlude(f, 1.0, sk, plain, M)
    if X > -1.85 and t < 4.6:
        # her eyes, wide, in the dark (only while she faces across the room)
        L.eye_glints(f, sk, cast.her(coat=True), M, level=0.9)
    # light on her: the hall light behind her in the doorway, the match, the lamp
    with f.light(blur=2.0) as A:
        if op > 0.05 and X < -0.6:
            w = op * (1.0 - L.k_(X, -1.5, 0.9))
            A.save()
            if in_door:
                draw.poly(A, APT.door.opening_quad())
                A.clip()
            L.rim(A, sk, plain, M, sets.mix(AMBER, HOT, 0.3), 0.75 * w, (7.0, 1.0))
            A.restore()
        if ml > 0.01:
            dx = 1.0 if tip[0] >= M.transform_point(*sk.j["pelvis"])[0] else -1.0
            L.rim(A, sk, plain, M, sets.mix(AMBER, HOT, 0.25), 0.30 * clamp(ml), (-5.0 * dx, 2.0))
        if lv > 0.01:
            near = L.falloff(L.dist3((X, 1.3, Z), LAMP3), 0.55)
            A.push_group()
            L.draw_sk(A, sk, plain, M, color=(1.0, 1.0, 1.0))
            mask = A.pop_group()
            col = sets.mix(AMBER, HOT, 0.4)
            A.set_source_rgba(col[0], col[1], col[2], clamp(0.22 * lv * near))
            A.mask(mask)
    _smoke(f, t, st)
    # the match itself (hidden while her body is between it and us: the far hand)
    if ml > 0.01:
        s = 0.80 * R.ppm(Z) / 343.0
        occ = _covered(sk, M, plain, tip, 5.0 * s + 2.0) if sk.z.get("hand_R", 0.0) < 0.0 else 0.0
        vis = min(1.0, ml) * (1.0 - occ)
        ang = math.degrees(math.atan2(tip[1] - fing[1], tip[0] - fing[0]))
        if vis > 0.01:
            sets.match_flame(f, t, tip, level=min(1.5, ml) * (1.0 - occ), scale=s, seed=7, stick_angle=ang,
                             stick=False)
            with f.layer() as c:
                c.push_group()
                draw.capsule(c, fing, tip, 1.2 * s + 0.6, 1.5 * s + 0.6)
                draw.fill(c, INK)
                c.pop_group_to_source()
                c.paint_with_alpha(1.0 - occ)
        if occ > 0.01:
            # its light still spills round her edges
            with f.light(blur=4.0) as A:
                sets.glow(A, tip, 300.0 * s, AMBER, 0.16 * min(1.0, ml) * occ)


def _smoke(f, t, st):
    """A thread of smoke from the dead match, curling up through the hall light (7.2 - 8.2)."""
    u = (t - T_OUT) / 1.0
    if u <= 0.0 or u >= 1.0:
        return
    a = st["a"]
    sk0 = a.skeleton(T_OUT)
    foot, k, xc = _map(a, T_OUT)
    M0 = L.place_matrix(foot, k, xc, 0.0)
    _, tip0, _ = _hand(T_OUT, sk0, M0)
    s = R.ppm(_z(T_OUT)) / 343.0
    pts = []
    n = 14
    for i in range(n):
        v = i / (n - 1)
        h = (40.0 + 260.0 * u) * v * s
        x = tip0[0] + (14.0 * math.sin(v * 5.0 + t * 1.7) + 26.0 * v * v * math.sin(t * 0.9 + 1.0)) * s * (0.3 + u)
        pts.append((x, tip0[1] - h))
    with f.light(blur=3.0 * s + 1.0) as A:
        A.new_path()
        A.move_to(*pts[0])
        for p in pts[1:]:
            A.line_to(*p)
        A.set_line_width(2.2 * s + 0.6)
        g = 0.10 * (1.0 - u) * min(1.0, u * 6.0)
        A.set_source_rgba(0.75, 0.72, 0.68, g)
        A.stroke()


def _covered(sk, M, plain, p, r):
    """Fraction of a small disc round world point p covered by her silhouette."""
    n = 8
    surf = cairo.ImageSurface(cairo.FORMAT_A8, n, n)
    c = cairo.Context(surf)
    k = n / (2.0 * r)
    c.scale(k, k)
    c.translate(-p[0] + r, -p[1] + r)
    L.draw_sk(c, sk, plain, M, color=(0.0, 0.0, 0.0))
    surf.flush()
    a = np.frombuffer(surf.get_data(), np.uint8).reshape(n, surf.get_stride())[:, :n]
    return float(a.mean()) / 255.0


# =========================================================================== window shot
NS = 1.0
NINE = sets.NineWindow((600.0, 1700.0), NS)
GX0, GY0, GX1, GY1 = NINE.glass
SF = 0.22
WIN = (712.0, 1268.0)                         # her window across the street (13), centre
HERS = sets.Facade(origin=(WIN[0], WIN[1] + 2730.0 * SF), scale=SF, variant="hers", seed=31)
HER_W = 13
BLOCKS = sets.neighbours(HERS)
OTHERS = {9: 0.36, 17: 0.28, 2: 0.22, 24: 0.25}
HER_K = 1.16
HER_FOOT = (440.0, 1830.0)


@lru_cache(maxsize=1)
def _her_win():
    """She comes in from the left (the cut lands mid-stride, her screen direction kept from
    the room), stops at the glass and lifts her eyes to her own window: at 12.5 she holds
    s08's pose (yaw -50, head -5, head_yaw 10, the same arms)."""
    a = Actor(cast.HER, None, x=-200.0, ground=0.0, facing=-38.0, seed=81)
    a.stand(until=10.85, at=-2.0, idle=0.3)
    a.walk(to=0.0, gait="brisk", yaw=-38.0, at=10.85, turn=0)           # ends ~11.95
    a.turn(-50.0, dur=0.35, at=a.cursor, via=-44.0)
    a.stand(until=30.0, idle=0.4)
    a.key("head", [(-2.0, 4.0), (11.90, 8.0), (12.35, -5.0, "inout"), (30.0, -5.0)])
    a.key("head_yaw", [(-2.0, 18.0), (11.90, 18.0), (12.35, 10.0, "inout"), (30.0, 10.0)])
    a.arm("R", 11.95, 30.0, fade=0.4, sh=10.0, abd=8.0, elbow=34.0)
    a.arm("L", 11.95, 30.0, fade=0.4, sh=6.0, abd=8.0, elbow=20.0)
    return a


def _bunched_sheet(c, t):
    """The show sheet pushed aside: bunched on its wire right of the glass (as in s08)."""
    s = NINE.s
    y0 = GY0 - 44 * s
    x0 = GX1 + 30 * s
    sway = 3.0 * s * fbm1(t * 0.3, 41)
    pts = [(x0 - 20 * s, y0), (x0 + 160 * s, y0 - 2 * s), (x0 + 175 * s + sway, y0 + 300 * s),
           (x0 + 168 * s + sway * 1.5, y0 + 700 * s), (x0 + 185 * s + sway * 2, NINE.floor_y - 30 * s),
           (x0 + 30 * s + sway * 2, NINE.floor_y - 40 * s), (x0 + 5 * s + sway, y0 + 640 * s), (x0 - 12 * s, y0 + 260 * s)]
    draw.smooth(c, pts, close=True, tension=0.35)


def _render_window(f, t, W_):
    u = clamp((t - T_WIN) / (12.5 - T_WIN))
    z = 1.20 * (1.0 + 0.03 * ease("out", u))
    f.set_camera(Camera(592.0, 1290.0, z).shaken(t, amp=1.2, rot_amp=0.03, freq=0.3, seed=707))
    lit = {HER_W: 1.0}
    lit.update(OTHERS)
    sets.night_sky(f, t, glow_y=HERS.top_y + 40.0, spread=300.0, par=0.25, clouds=0.8)
    f.haze(PAL.fog_at(0.9), 0.20, y0=HERS.top_y - 200, y1=HERS.top_y + 600, feather=400, par=0.6)
    sets.draw_blocks(f, t, BLOCKS, layer=dict(par=1.0, fog=0.42, blur=1.0), light=0.55)
    HERS.draw(f, t, layer=dict(par=1.0, fog=0.10, blur=0.0), lit=lit,
              interiors={HER_W: sets.her_room_interior(lamp=1.0, man=None, chair=True)}, emit=0.5, halo=0.9)
    wr = HERS.window_rect(HER_W)
    glows = [atmos.Glow(((wr[0] + wr[2]) / 2, (wr[1] + wr[3]) / 2 + 10.0), 70.0, 0.9, AMBER)]
    atmos.rain(f, density=0.7, speed=2100.0, angle=6.0, t=t, seed=88, alpha=0.9, lit=glows, lit_gain=2.4)
    NINE.draw(f, t, layer=dict(par=1.0, blur=0.0), rain=0.55, room_light=0.62, condensation=0.0, outside_light=1.0)
    with f.layer(par=1.0) as c:
        _bunched_sheet(c, t)
        draw.fill(c, sets.mix(INK, sets.mix(PAPER, AMBER, 0.4), 0.16))
    # her, three-quarter back, at the glass
    a = _her_win()
    sk = a.skeleton(t)
    M = L.place_matrix(HER_FOOT, HER_K, 0.0, 0.0)
    lk = L.her_look(coat_k=0.36, eyes=False)
    plain = L.plain(lk)
    ysh = M.transform_point(*sk.j["shoulder_R"])[1]
    L.occlude(f, 1.0, sk, plain, M)
    with f.layer(par=1.0) as c:
        # the window and the lamp behind her catch her collar and shoulders; below, the
        # coat sinks toward ink (as s08's over-the-shoulder has her)
        L.draw_sk(c, sk, plain, M, color=INK)
        c.push_group()
        L.draw_sk(c, sk, lk, M)
        pat = c.pop_group()
        g = cairo.LinearGradient(0, ysh - 60.0, 0, ysh + 330.0)
        g.add_color_stop_rgba(0.0, 0, 0, 0, 1.0)
        g.add_color_stop_rgba(1.0, 0, 0, 0, 0.30)
        c.set_source(pat)
        c.mask(g)
    with f.light(blur=3.0) as A:
        L.rim(A, sk, plain, M, COLD, 0.55, (-8.0, 6.0))       # the glass, up and right of her
        L.rim(A, sk, plain, M, AMBER, 0.20, (8.0, 3.0))       # the show lamp behind her, left


# =========================================================================== render
def render(f, t, T):
    W_ = _times(T)
    if t < T_WIN:
        _render_room(f, t, W_)
    else:
        _render_window(f, t, W_)


def motion_blur(t, T):
    """Sub-frames: the strike, and the flick that shakes the match out."""
    if 1.38 <= t <= 1.52:
        return 3
    if 7.04 <= t <= 7.36:
        return 2
    return 1


def cues(T):
    W_ = _times(T)
    return [
        Cue(-0.40, "room tone: an empty flat, rain on the window behind the sheet", -20, dur=1.0),
        Cue(-0.05, "the door creaks open, slowly, in steps; the hallway's hum spills in", -8, pan=-0.6, dur=0.85),
        Cue(0.62, "two careful steps on bare boards", -14, pan=-0.5, dur=0.6),
        Cue(T_STRIKE - 0.02, "match strike: scrape and flare", -4, pan=-0.2),
        Cue(T_STRIKE + 0.12, "the match burning: a tiny breathing hiss", -24, dur=T_OUT - T_STRIKE - 0.1),
        Cue(W_["lamp"], "the faintest glass tick (the bulb catching the flame)", -26, pan=0.1),
        Cue(W_["dolls"] - 0.15, "paper rustle: a doll stirs on its rod in the match's draught", -22, pan=0.0),
        Cue(T_OUT - 0.06, "match shaken out: a soft whip, then the dark", -12, pan=0.15),
        Cue(W_["show"], "lamp switch: a hard click; the bulb's filament hum", -3, pan=0.15),
        Cue(W_["show"] + 0.04, "a low swell under the giant shadow", -10, dur=1.3),
        Cue(10.55, "her steps toward the window, boards", -16, pan=0.35, dur=0.8),
        Cue(T_WIN, "at the glass: rain on window 9, the street below, a car hissing past", -10, dur=1.22),
    ]
