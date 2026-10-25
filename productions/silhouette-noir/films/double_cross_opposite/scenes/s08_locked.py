"""s08 · LOCKED (114-128): black, and a match: her profile, calm, the Cracker beyond her by the door.
His panic (the spiral, the heartbeat, the film's one Dutch tilt) and his fists on the door. Through
the walls, faint, the bell; the corner of her mouth lifts. Her eye, the match in it; the dive into her
eye: the night before, she is on a ladder under the vault floor cutting the trapdoor up through it,
and sets the block back so that from above it is only a floor tile. Back in the vault her look drops
to her heel: a tap, and a hollow knock.

The vault is the street section's (door on its left wall, the tile at its far end), seen close."""
import math

import cairo

from engine import bass, draw as D, paperdoll as pd
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.double_cross_opposite import bank as Bk
from films.double_cross_opposite import cast as C
from films.double_cross_opposite import faces as F
from films.double_cross_opposite import kit as K
from films.double_cross_opposite import street as St
from films.opposite_bass import world as BW

k = K.k
INK, PAPER, AMBER, RED, NIGHT, STEEL, DEEP = K.INK, K.PAPER, K.AMBER, K.RED, K.NIGHT, K.STEEL, K.DEEP
T0 = K.film_start("s08")                  # film time of this scene's t = 0

# ---------------------------------------------------------------- beats (scene time)
T_SCRATCH, T_STRIKE = 1.2, 1.6            # the match scratches, and strikes
T_PANIC = 2.0                             # his face: the spiral, the heartbeat, the tilt comes in
T_DOOR = 3.4                              # his fists on the door
T_BLOWS = (3.5, 4.0, 4.5)
T_LEVEL = 6.0                             # level again; through the walls, faint, the bell
T_FACE = 6.5                              # her profile, close
T_SMILE = 6.9                             # the corner of her mouth lifts
T_EYE = 7.25                              # her eye, level and steady, the match in it
T_DIVE = (8.0, 8.5)                       # into her eye
T_CUTS = ((9.0, 9.6), (9.75, 10.35))      # the night before: two cuts up through the slab
T_PUSH = (10.5, 10.9)                     # she pushes the block up a crack: the gold's light
T_SET = (11.2, 11.5)                      # and sets it back
T_EYE_OUT = (11.75, 12.0)                 # out of her eye
T_BACK = 12.0                             # the vault again
T_GLANCE = 12.1                           # her look drops to her heel
T_TAP, T_KNOCK = 12.4, 12.75              # a tap; a hollow knock
T_TURN = 13.25                            # the Cracker turns to her
TILT = -7.0                               # the one Dutch tilt (deg)

# ---------------------------------------------------------------- the vault as the section has it
VAULT_CAM = ((955.0, 1300.0), 5.4)
DOOR_CAM = ((905.0, 1300.0), 8.0)
HER_X = St.TRAP_C - 4.0                   # she stands on the tile
CR_X = St.VAULT_IN[0] + 18.0              # the Cracker, at the door
MATCH_REL = (15.0, -108.0)                # the match in her raised hand, from her floor point (section px)
AFTER = dict(lit={}, hall_lamp=1.0, vault_lit=0.0, gold_glow=0.0, gold=0.0, ruby_box=1.0, ruby=False, vault_door=0.0,
             side_door=1.0, hatch=0.0, lid_a=1.0, trap_shaft=True, bell_ring=1.0, car=dict(lights=1.0), beams=False,
             sky_lit=0.0, lamp_on=1.0, clock=(12, 20), drips=True)      # the hatch shut and manhole A open, as s04 left them


def motion_blur(t, T):
    return 1


# ================================================================ light
def flicker(t):
    """The flame's breath, about 1, shivering after each blow on the door."""
    tt = K.twos(T0 + t)
    f = 1.0 + 0.05 * math.sin(tt * 17.0) + 0.03 * math.sin(tt * 41.0)
    for th in T_BLOWS:
        if th <= t < th + 0.5:
            f -= 0.12 * (1.0 - (t - th) / 0.5) * (0.5 + 0.5 * math.sin((t - th) * 60.0))
    return f


def darkness(c, p, r, steps=((1.0, 0.45), (1.16, 0.75), (1.34, 1.0)), seed=0):
    """The dark beyond the light: INK laid over everything outside radius r of p, in three cut
    steps (no blur)."""
    for kk, a in steps:
        rr = r * kk
        pts = [(p[0] + rr * (1.0 + 0.012 * math.sin(i * 1.7 + seed)) * math.cos(2.0 * math.pi * i / 96.0),
                p[1] + rr * (1.0 + 0.012 * math.sin(i * 1.7 + seed)) * math.sin(2.0 * math.pi * i / 96.0))
               for i in range(96)]
        c.save()
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        c.new_path()
        c.rectangle(-4000.0, -4000.0, 9000.0, 9000.0)
        D.poly(c, pts)
        c.set_source_rgba(*INK, a)
        c.fill()
        c.restore()


def glow(c, p, r, a):
    """The match's light on what it falls on (light adds)."""
    K.pool(c, p, r, r, AMBER, a, steps=5)


def rim(c, draw_fn, color, off, alpha=1.0):
    """draw_fn's silhouette laid in `color` and shifted by off: the edge the light catches."""
    c.save()
    c.push_group()
    draw_fn(c)
    m = c.pop_group()
    c.translate(*off)
    c.set_source_rgba(*color, alpha)
    c.mask(m)
    c.restore()


def match_stick(c, p, t, lit, s=1.0, ang=-8.0):
    """The match in her fingers (p its head): the stick down to the fingertips, the head and, lit,
    the flame."""
    a = math.radians(90.0 + ang)
    base = (p[0] + 92.0 * s * math.cos(a), p[1] + 92.0 * s * math.sin(a))
    bass.line_band(c, [base, p], lerp(PAPER, AMBER, 0.35), width=7.0 * s, seed=901)
    K.dot(c, p, 6.0 * s, INK, seed=902)
    K.dot(c, base, 15.0 * s, INK, seed=903)           # her gloved fingertips
    if lit:
        K.flame(c, (p[0], p[1] + 2.0 * s), T0 + t, s=1.15 * s * flicker(t), seed=4)


def sparks(c, p, t, t0, n=14, life=0.32, spread=1.0, g=2600.0, seed=0, s=1.0):
    """A spray of sparks from p, born from t0 over a short burst, falling."""
    for i in range(n):
        born = t0 + 0.05 * (i % 5) + 0.01 * i
        a = (t - born) / life
        if not 0.0 <= a < 1.0:
            continue
        age = t - born
        ang = math.radians(-160.0 + 140.0 * K.hash01(i, seed) * spread + (1.0 - spread) * 70.0)
        v = (380.0 + 420.0 * K.hash01(i, seed + 1)) * s
        x = p[0] + v * math.cos(ang) * age
        y = p[1] + v * math.sin(ang) * age + 0.5 * g * s * age * age
        K.dot(c, (x, y), (3.5 + 3.0 * K.hash01(i, seed + 2)) * s * (1.0 - a), PAPER if i % 3 else AMBER, seed=seed + i)


# ================================================================ the vault, close (section)
def _fig(c, who, st, pose, x, fy, facing, rim_col=AMBER, light=(0.9, -0.4), rim_w=1.0, eye=True):
    return C.draw(c, who, st, pose, x, fy, s=St.FIG_S, facing=facing, bg=DEEP, rim=rim_col, rim_w=rim_w, light=light,
                  eye=eye)


def match_at(t):
    return (HER_X + MATCH_REL[0], St.FEET + MATCH_REL[1])


def her_figure(c, t, heel=0.0, look_down=0.0):
    """Her in the vault, on the tile, the match held up before her face. heel: her near heel's lift
    (0..1); look_down: her head bowing to the floor."""
    st = C.standing("architect", spread=14.0)
    if heel > 0.0:
        f = st["feet"]["near"]
        st["feet"]["near"] = (f[0], f[1], 18.0 * heel)
    pose = pd.Pose(lean=1.0, head=-4.0 - 22.0 * look_down,
                   arms={"near": ("ik", (MATCH_REL[0] / St.FIG_S, MATCH_REL[1] / St.FIG_S)), "far": ("ang", 4.0, 14.0)})
    return _fig(c, "architect", st, pose, HER_X, St.FEET, 1)


def cracker_figure(c, t, slump=0.0, listen=0.0, turn=0.0):
    st = C.standing("cracker", spread=12.0)
    face = 1 if turn >= 0.5 else -1
    pose = pd.Pose(lean=8.0 + 14.0 * slump - 8.0 * listen, head=-6.0 - 16.0 * slump + 18.0 * listen,
                   arms={"near": ("ang", 8.0 + 30.0 * slump, 30.0 + 40.0 * slump), "far": ("ang", 4.0 + 24.0 * slump, 26.0)})
    if slump > 0.0 and turn < 0.5:
        door = St.VAULT_IN[0] + 1.0
        pose.arms = {"near": ("ik", ((door - CR_X) / St.FIG_S, (-96.0 + 6.0 * slump) / St.FIG_S)),
                     "far": ("ik", ((door - CR_X) / St.FIG_S, (-84.0 + 6.0 * slump) / St.FIG_S))}
    lx = 1.0 if face < 0 else -0.6
    return _fig(c, "cracker", st, pose, CR_X, St.FEET, face, light=(lx * 0.9, -0.4), rim_w=0.9)


def vault_shot(c, t, cam, people, under=0.0, light_r=130.0, strength=1.0, overlay=None):
    """The vault in section through cam, lit only by the match (section px r)."""
    tf = T0 + t
    (cx, cy), z = cam
    c.save()
    St.zoom_on(c, (cx, cy), z)

    def ppl(cc, where, n, rect):
        if where == "vault":
            people(cc)
    St.draw_section(c, tf, people=ppl, moon_at=St.MOON_S, under=under, **AFTER)
    m = match_at(t)
    fl = flicker(t)
    glow(c, m, light_r * 0.8 * fl, 0.12 * strength)
    K.match_light(c, m, tf, r=light_r * fl, strength=strength)
    darkness(c, m, light_r * 1.05 * fl)
    if overlay is not None:
        overlay(c)
    c.restore()


# ---------------------------------------------------------------- 0-2: the match
HER_A = (640.0, 1930.0)                   # her profile in the foreground, facing right
HER_A_S = 1.0
MATCH_A = (930.0, 1330.0)


def draw_match_shot(c, t):
    K.fill(c, INK)
    if t < T_STRIKE:
        sparks(c, MATCH_A, t, T_SCRATCH, n=22, seed=40, s=1.7)
        if t >= T_SCRATCH:
            match_stick(c, MATCH_A, t, False, s=1.6)
        return
    u = ease("out3", clamp((t - T_STRIKE) / 0.45))
    fl = flicker(t)
    # beyond her, the vault, and the Cracker by its door
    (cx, cy), z = VAULT_CAM
    c.save()
    St.zoom_on(c, (cx, cy), z)
    St.draw_section(c, T0 + t, people=lambda cc, where, n, rect: cracker_figure(cc, t) if where == "vault" else None,
                    moon_at=St.MOON_S, under=0.0, **AFTER)
    c.restore()
    r = 940.0 * u * fl
    glow(c, MATCH_A, r * 0.7, 0.14)
    K.match_light(c, MATCH_A, T0 + t, r=r)
    darkness(c, MATCH_A, max(r, 1.0) * 1.02)
    # her, close, calm, the match before her face
    fn = (lambda cc: F.her(cc, HER_A, HER_A_S, look=0.55, t=T0 + t, field=DEEP))
    rim(c, fn, AMBER, (9.0, -3.0), alpha=u)
    fn(c)
    match_stick(c, MATCH_A, t, True, s=1.6)
    sparks(c, MATCH_A, t, T_STRIKE - 0.02, n=12, life=0.25, seed=60, s=1.5)


# ---------------------------------------------------------------- 2-6: his panic (tilted)
CR_EYE = (430.0, 860.0)
CR_S = 1.12


def tilt_on(c, t):
    """The film's one Dutch tilt, eased in from his face and held through the blows."""
    a = TILT * k(t, T_PANIC, 0.6, "inout")
    c.translate(K.W / 2.0, K.H / 2.0)
    c.rotate(math.radians(a))
    c.scale(1.14, 1.14)
    c.translate(-K.W / 2.0, -K.H / 2.0)


def cracker_mirrored(c, t, eye, s, look=-0.2):
    """His profile turned to face left (faces.cracker faces right), its eye at `eye`."""
    at = (eye[0] + 70.0 * s, eye[1] + 560.0 * s)
    c.save()
    c.translate(2.0 * eye[0], 0.0)
    c.scale(-1.0, 1.0)
    m = F.cracker(c, at, s, look=look, t=T0 + t, field=DEEP)
    c.restore()
    return {key: (2.0 * eye[0] - v[0], v[1]) for key, v in m.items()}


def draw_panic(c, t):
    K.fill(c, DEEP)
    u = t - T_PANIC
    z = math.exp(0.42 * u)
    bass.spiral(c, c=(CR_EYE[0] + 40.0, CR_EYE[1] + 80.0), r0=14.0 * z, r1=1500.0, turns=4.0, width=70.0 * z,
                color=lerp(DEEP, STEEL, 0.28), arms=2, rot=-80.0 * u, seed=70)
    chest = (CR_EYE[0] + 40.0, CR_EYE[1] + 820.0)
    K.heartbeat(c, chest, T0 + t, AMBER, bpm=150.0, r0=60.0, r1=560.0, width=20.0, life=1.0, seed=71)
    fn = (lambda cc: cracker_mirrored(cc, t, CR_EYE, CR_S, look=-0.35))
    rim(c, fn, AMBER, (10.0, -2.0))
    fn(c)


def blow_state(t):
    """(which fists strike: 0 left, 1 right, 2 both; how far the fist is wound back 0..1; the
    shake of the hit) for the blows."""
    for i, tb in enumerate(T_BLOWS):
        if tb - 0.22 <= t < tb + 0.3:
            if t < tb - 0.06:
                return i, ease("out", (t - (tb - 0.22)) / 0.16), 0.0
            if t < tb:
                return i, 1.0 - ease("in3", (t - (tb - 0.06)) / 0.06), 0.0
            return i, 0.0, math.exp(-(t - tb) / 0.08)
    return None, 0.0, 0.0


# the door from inside the vault: its round steel face square to us, and him with his back to us
DOOR_C = (540.0, 1000.0)
DOOR_R = 500.0
FLOOR_Y = 1640.0
FX = 560.0                                # his centre line
LIGHT_W = (1320.0, 1060.0)                # her match, behind us and off to the right, cast onto the door
SHADOW_K = 1.24                           # his shadow on the door, that much bigger than he is


def door_face(c):
    """The vault's back wall round the door, the jamb, and the door's inside face: rings, the bolt
    work (twelve bars from the hub out to the bolts in the jamb), the rivets."""
    bass.fill_polys(c, [bass.ring_pts(DOOR_C, DOOR_R + 64.0, seed=1200, n=120, amp=0.6)], lerp(STEEL, INK, 0.7))
    bass.fill_polys(c, [bass.ring_pts(DOOR_C, DOOR_R, seed=1201, n=120, amp=0.6)], lerp(STEEL, INK, 0.38))
    bass.fill_polys(c, [bass.ring_pts(DOOR_C, DOOR_R - 58.0, seed=1202, n=120, amp=0.6)], lerp(STEEL, INK, 0.5))
    bass.fill_polys(c, [bass.ring_pts(DOOR_C, DOOR_R - 82.0, seed=1203, n=120, amp=0.6)], lerp(STEEL, INK, 0.42))
    for i in range(12):
        a = 2.0 * math.pi * (i + 0.5) / 12.0
        p0 = (DOOR_C[0] + 70.0 * math.cos(a), DOOR_C[1] + 70.0 * math.sin(a))
        p1 = (DOOR_C[0] + (DOOR_R + 26.0) * math.cos(a), DOOR_C[1] + (DOOR_R + 26.0) * math.sin(a))
        bass.line_band(c, [p0, p1], lerp(STEEL, INK, 0.24), width=24.0, seed=1210 + i, taper=(0.7, 1.0))
        K.dot(c, p1, 22.0, lerp(STEEL, PAPER, 0.1), seed=1250 + i)          # the bolt's head, home in the jamb
    bass.disc(c, DOOR_C, 104.0, lerp(STEEL, INK, 0.3), seed=1204)
    bass.disc(c, DOOR_C, 56.0, lerp(STEEL, INK, 0.55), seed=1205)
    for i in range(32):
        a = 2.0 * math.pi * i / 32.0
        K.dot(c, (DOOR_C[0] + (DOOR_R - 30.0) * math.cos(a), DOOR_C[1] + (DOOR_R - 30.0) * math.sin(a)), 7.0,
              lerp(STEEL, PAPER, 0.12), seed=1230 + i)


def door_man(c, t, color):
    """The old man from behind, a cut-paper silhouette: bowler, coat, legs, his arms up and his
    fists on the door either side of his head; a blow winds a fist back (towards us: bigger, lower)
    and slams it in. After the last he sags, fists sliding down the steel."""
    i, back, _ = blow_state(t)
    slump = k(t, T_BLOWS[-1] + 0.4, 0.7, "inout")
    sink = 44.0 * slump
    x, fy = FX, FLOOR_Y
    polys = []
    for sx in (-1.0, 1.0):                                                  # legs and shoes
        polys.append(bass.orient([(x + sx * 18.0, fy - 260.0), (x + sx * 62.0, fy - 260.0),
                                  (x + sx * 66.0, fy - 10.0), (x + sx * 28.0, fy - 10.0)], True))
        polys.append(D.ellipse_pts((x + sx * 52.0, fy - 8.0), 34.0, 12.0, n=20))
    top = fy - 560.0 + sink                                                  # the collar
    hem = fy - 214.0 + sink * 0.4
    coat = [(x - 30.0, top), (x - 92.0, top + 18.0), (x - 114.0, top + 44.0), (x - 108.0, top + 120.0),
            (x - 126.0, hem), (x + 126.0, hem), (x + 108.0, top + 120.0), (x + 114.0, top + 44.0),
            (x + 92.0, top + 18.0), (x + 30.0, top)]
    polys.append(bass.orient(bass.cut(coat, seed=1260, amp=0.8, seg=(30.0, 70.0)), True))
    hc = (x, top - 44.0 + 22.0 * slump)                                      # the head, bowed as he sags
    polys.append(bass.ring_pts(hc, 46.0, seed=1261, n=28, amp=0.4))
    for sx in (-1.0, 1.0):
        polys.append(bass.ring_pts((hc[0] + sx * 45.0, hc[1] + 4.0), 9.0, seed=1262, n=10, amp=0.2))   # ears
    brim_y = hc[1] - 24.0
    polys.append(D.ellipse_pts((x, brim_y), 70.0, 11.0, n=32))
    dome = [(x - 48.0, brim_y)] + [(x - 48.0 * math.cos(math.pi * j / 14.0), brim_y - 52.0 * math.sin(math.pi * j / 14.0))
                                   for j in range(1, 14)] + [(x + 48.0, brim_y)]
    polys.append(bass.orient(dome, True))
    bass.fill_polys(c, polys, color)
    for n, sx in enumerate((-1.0, 1.0)):                                     # the arms
        striking = i is not None and (i == n or i == 2)
        a = back if striking else 0.0
        sh = (x + sx * 100.0, top + 30.0)
        rest_f = (x + sx * (140.0 - 6.0 * slump), top - 40.0 + 330.0 * slump)
        rest_e = (x + sx * (214.0 - 40.0 * slump), top + 110.0 + 150.0 * slump)
        fist = (lerp(rest_f[0], x + sx * 196.0, a), lerp(rest_f[1], rest_f[1] + 96.0, a))
        elbow = (lerp(rest_e[0], x + sx * 236.0, a), lerp(rest_e[1], rest_e[1] + 70.0, a))
        bass.line_band(c, [sh, elbow, fist], color, width=42.0, seed=1270 + n, taper=(1.0, 0.8))
        bass.disc(c, fist, 25.0 * (1.0 + 0.32 * a), color, seed=1272 + n)
    return {"fists": [(x - 140.0, top - 40.0), (x + 140.0, top - 40.0)]}


def draw_door(c, t):
    i, back, shake = blow_state(t)
    if shake > 0.0:
        c.translate(22.0 * shake * math.sin(t * 91.0), 14.0 * shake * math.cos(t * 77.0))
    K.fill(c, DEEP)
    door_face(c)
    fl = flicker(t)
    glow(c, LIGHT_W, 1050.0 * fl, 0.11)
    # his shadow, thrown up onto the door by the match
    c.save()
    c.rectangle(-400.0, -400.0, 2000.0, FLOOR_Y + 400.0)
    c.clip()
    c.translate(LIGHT_W[0], LIGHT_W[1])
    c.scale(SHADOW_K, SHADOW_K)
    c.translate(-LIGHT_W[0], -LIGHT_W[1])
    c.push_group()
    door_man(c, t, INK)
    c.pop_group_to_source()
    c.paint_with_alpha(0.5)
    c.restore()
    bass.fill_polys(c, [bass.cut_rect(-400.0, FLOOR_Y, 1500.0, 2400.0, seed=1280, amp=1.0)], lerp(INK, DEEP, 0.35))
    for n, tb in enumerate(T_BLOWS):                                         # the blows ring out across the steel
        hits = [0, 1] if n == 2 else [n]
        for h in hits:
            hp = (FX + (-140.0 if h == 0 else 140.0), FLOOR_Y - 560.0 - 40.0)
            K.ripple(c, hp, t, tb, AMBER, n=3, every=0.07, life=0.55, r0=20.0, r1=300.0, width=9.0, seed=int(tb * 10) + h)
    fn = (lambda cc: door_man(cc, t, INK))
    rim(c, fn, AMBER, (7.0, -3.0))
    fn(c)


# ---------------------------------------------------------------- 6-6.5: through the walls, the bell
def draw_listen(c, t):
    listen = k(t, T_LEVEL + 0.1, 0.3, "out3")

    def people(cc):
        cracker_figure(cc, t, slump=1.0 - listen, listen=listen)
        her_figure(cc, t)

    def bell(cc):
        b = St.BELL
        for j in range(3):
            K.ripple(cc, b, t, T_LEVEL - 0.6 + 0.5 * j, RED, n=1, life=1.3, r0=250.0, r1=520.0, width=3.0, seed=80 + j,
                     alpha=0.55)
    vault_shot(c, t, VAULT_CAM, people, overlay=bell)


# ---------------------------------------------------------------- 6.5-7.25: her smile
HER_E = (470.0, 1780.0)
HER_E_S = 1.12
MATCH_E = (860.0, 1150.0)


def face_pt(at, s, p):
    return (at[0] + (p[0] - 400.0) * s, at[1] + (p[1] - 860.0) * s)


def draw_smile(c, t):
    K.fill(c, DEEP)
    fl = flicker(t)
    glow(c, MATCH_E, 820.0 * fl, 0.10)
    K.match_light(c, MATCH_E, T0 + t, r=980.0 * fl)
    fn = (lambda cc: F.her(cc, HER_E, HER_E_S, look=0.5, t=T0 + t, field=DEEP))
    rim(c, fn, AMBER, (9.0, -3.0))
    fn(c)
    smile = ease("inout", clamp((t - T_SMILE) / 0.4))
    pts = [face_pt(HER_E, HER_E_S, p) for p in ((519.0, 457.0), (505.0, 461.0 - 2.0 * smile), (493.0, 460.0 - 7.0 * smile),
                                               (482.0, 456.0 - 13.0 * smile))]
    bass.line_band(c, pts, AMBER, width=8.0, seed=942, taper=(1.0, 0.45), alpha=0.9)
    if smile > 0.0:
        ch = [face_pt(HER_E, HER_E_S, (440.0 + 12.0 * i, 352.0 - 10.0 * smile - 3.0 * math.sin(math.pi * i / 4.0)))
              for i in range(5)]
        bass.line_band(c, ch, AMBER, width=6.0, seed=943, taper=(0.4, 0.4), alpha=0.55 * smile)
    match_stick(c, MATCH_E, t, True, s=1.25)
    darkness(c, MATCH_E, 1060.0 * fl)


# ---------------------------------------------------------------- 7.25-8.5 and 11.75-12: her eye, the dive
DIVE_Z = K.W / 104.0                      # the dive lands the iris's window exactly on the frame


def iris_window():
    ic = (BW.EYE_C[0], BW.EYE_C[1] - 6.0)
    return ic, (ic[0] - 52.0, ic[1] - 92.4, ic[0] + 52.0, ic[1] + 92.4)


def into_rect(c, rect, fn):
    c.save()
    c.translate(rect[0], rect[1])
    c.scale((rect[2] - rect[0]) / K.W, (rect[3] - rect[1]) / K.H)
    fn(c)
    c.restore()


def reflect(t, before):
    """What the iris holds: the match's flame where the torch's flame will be; the night before
    comes up round it as we dive."""
    def fn(c, rect):
        def flame_only(cc):
            K.fill(cc, INK)
            sz = lerp(24.0, NB_FLAME_S, k(t, T_DIVE[0], T_DIVE[1] - T_DIVE[0], "inout"))
            K.flame(cc, NB_FLAME_AT, T0 + t, s=sz * flicker(t), seed=4)
        nb = clamp((t - T_DIVE[0]) / 0.3) if before else 1.0
        into_rect(c, rect, flame_only)
        if nb > 0.0:
            c.push_group()
            into_rect(c, rect, lambda cc: night_before(cc, max(t, T_DIVE[1]) if before else t))
            c.pop_group_to_source()
            c.paint_with_alpha(nb)
    return fn


def draw_eye(c, t):
    before = t < T_EYE_OUT[0]
    if before:
        dive = k(t, T_DIVE[0], T_DIVE[1] - T_DIVE[0] - 1.0 / 24.0, "in3")
    else:
        dive = 1.0 - k(t, T_EYE_OUT[0], T_EYE_OUT[1] - T_EYE_OUT[0], "out3") * 0.62
    z = math.exp(math.log(DIVE_Z) * dive)
    ic, _ = iris_window()
    pan = clamp(dive * 3.0)
    c.save()
    c.translate(540.0, 960.0)
    c.scale(z, z)
    c.translate(-lerp(540.0, ic[0], pan), -lerp(960.0, ic[1], pan))
    BW.draw_eye(c, T0 + t, 1.0, 0.0, INK, reflect=reflect(t, before), skin=AMBER)
    c.restore()


# ---------------------------------------------------------------- 8.5-11.75: the night before
NB_CAM = ((1010.0, 1500.0), 5.3)
NIGHT_BEFORE = dict(lit={}, hall_lamp=1.0, vault_lit=0.0, gold_glow=1.0, gold=1.0, vault_door=0.0, side_door=0.0,
                    hatch=0.0, trap_shaft=True, bell_ring=0.0, car=None, beams=False, sky_lit=0.0, lamp_on=1.0,
                    clock=(1, 10), drips=True)
NB_FEET_H = 180.0                         # her feet on the ladder, above the shaft's foot (the water)
SLAB_TOP, SLAB_BOT = St.FEET, St.FEET + St.VSLAB
NB_X = St.TRAP_C - 4.0


def nozzle(t):
    """The torch's nozzle under the slab (section px)."""
    x0, x1 = St.TILE
    mv = ease("inout", clamp((t - T_CUTS[0][1]) / (T_CUTS[1][0] - T_CUTS[0][1])))
    return (lerp(x0, x1, mv), SLAB_BOT + 1.0)


def nb_to_frame(p):
    (cx, cy), z = NB_CAM
    return St.to_frame(p, (cx, cy), z)


NB_FLAME_AT = (540.0, 960.0)              # set below, once nb_to_frame exists


def lift(t):
    return 4.5 * (k(t, T_PUSH[0], T_PUSH[1] - T_PUSH[0], "inout") - k(t, T_SET[0], T_SET[1] - T_SET[0], "inout"))


def night_before(c, t):
    tf = T0 + t
    (cx, cy), z = NB_CAM
    c.save()
    St.zoom_on(c, (cx, cy), z)
    St.draw_section(c, tf, moon_at=St.MOON_S, under=1.0, **NIGHT_BEFORE)
    x0, x1 = St.TILE
    # the cuts, glowing up through the slab, cooling after
    for i, (a, b) in enumerate(T_CUTS):
        g = clamp((t - a) / (b - a))
        if g <= 0.0:
            continue
        xx = (x0, x1)[i]
        cool = clamp((t - b) / 0.8)
        y_top = lerp(SLAB_BOT, SLAB_TOP, g)
        bass.fill_polys(c, [[(xx - 0.8, SLAB_BOT + 0.5), (xx + 0.8, SLAB_BOT + 0.5), (xx + 0.8, y_top), (xx - 0.8, y_top)]],
                        lerp(AMBER, lerp(INK, STEEL, 0.25), cool))
    # the block, pushed up a crack, the gold's light falling through on her
    d = lift(t)
    if d > 0.05:
        bass.fill_polys(c, [[(x0, SLAB_BOT - d), (x1, SLAB_BOT - d), (x1, SLAB_BOT + 0.5), (x0, SLAB_BOT + 0.5)]], St.TUNNEL)
        bass.fill_polys(c, [[(x0, SLAB_TOP - d), (x1, SLAB_TOP - d), (x1, SLAB_BOT - d), (x0, SLAB_BOT - d)]], St.HEAVY)
        a = clamp(d / 3.0)
        bass.fill_polys(c, [[(x0 - 0.5, SLAB_BOT), (x1 + 0.5, SLAB_BOT), (x1 + 12.0, SLAB_BOT + 120.0),
                             (x0 - 12.0, SLAB_BOT + 120.0)]], AMBER, 0.28 * a)
        for xx in (x0, x1):
            bass.fill_polys(c, [[(xx - 1.0, SLAB_TOP - d), (xx + 1.0, SLAB_TOP - d), (xx + 1.0, SLAB_BOT),
                                 (xx - 1.0, SLAB_BOT)]], AMBER, a)
    # her, on the ladder, the torch up to the slab
    st, pose = Bk.ladder_pose("architect", NB_FEET_H, facing=1, rung=St.RUNG_STEP, reach=1.0)
    n = nozzle(t)
    pushing = d > 0.05 or (T_PUSH[0] - 0.2 < t < T_SET[1] + 0.1)
    if pushing:
        tgt = ((x0 + 6.0 - NB_X) / St.FIG_S, (SLAB_BOT - d + 2.0 - St.WATER) / St.FIG_S)
        tgt2 = ((x1 - 6.0 - NB_X) / St.FIG_S, (SLAB_BOT - d + 2.0 - St.WATER) / St.FIG_S)
        pose.arms = {"near": ("ik", tgt2), "far": ("ik", tgt)}
    else:
        h = (n[0] - 3.0 - NB_X, n[1] + 24.0 - St.WATER)
        pose.arms = {"near": ("ik", (h[0] / St.FIG_S, h[1] / St.FIG_S)),
                     "far": ("ik", ((h[0] - 2.0) / St.FIG_S, (h[1] + 6.0) / St.FIG_S))}
    pose.head = -26.0
    lit_from = (0.3, -1.0)
    C.draw(c, "architect", st, pose, NB_X, St.WATER, s=St.FIG_S, facing=1, bg=St.TUNNEL, rim=PAPER, rim_w=0.9,
           light=lit_from)
    if not pushing:
        h = (n[0] - 3.0, n[1] + 24.0)
        bass.line_band(c, [h, n], INK, width=3.4, seed=1001)
        on = any(a <= t < b for a, b in T_CUTS)
        if on:
            c.save()
            c.translate(n[0], n[1])
            c.scale(0.22, 0.22)
            K.flame(c, (0.0, 0.0), tf, s=1.0, seed=5)
            c.restore()
            glow(c, n, 40.0, 0.12)
            for i, (a, b) in enumerate(T_CUTS):
                if a <= t < b:
                    for j in range(int((t - a) * 24.0) % 6, 40, 6):
                        sparks(c, n, t, a + j * 0.015, n=3, life=0.5, g=360.0, seed=300 + i * 50 + j, s=0.2)
        elif T_CUTS[0][0] - 0.6 < t < T_CUTS[0][0]:
            c.save()
            c.translate(n[0], n[1])
            c.scale(0.12, 0.12)
            K.flame(c, (0.0, 0.0), tf, s=1.0, seed=5)        # the pilot, before the cut
            c.restore()
    c.restore()


NB_FLAME_AT = nb_to_frame((St.TILE[0], SLAB_BOT + 1.0))
NB_FLAME_S = 0.22 * NB_CAM[1]             # the torch's flame, in frame px terms


# ---------------------------------------------------------------- 12-14: the hollow knock
def heel(t):
    for t0, h in ((T_TAP, 0.7), (T_KNOCK, 1.0)):
        if t0 - 0.24 <= t < t0:
            return h * ease("out", (t - (t0 - 0.24)) / 0.14) * (1.0 - ease("in3", clamp((t - (t0 - 0.08)) / 0.08)))
    return 0.0


def draw_knock(c, t):
    down = k(t, T_GLANCE, 0.3, "inout")
    turn = k(t, T_TURN, 0.2, "inout")
    under = k(t, T_KNOCK + 0.05, 0.5, "out3")
    marks = {}

    def people(cc):
        marks["her"] = her_figure(cc, t, heel=heel(t), look_down=down)
        cracker_figure(cc, t, slump=0.0, listen=1.0 - turn, turn=turn)

    def overlay(cc):
        hp = (HER_X + 3.0, St.FEET)
        if "her" in marks:
            eye = (marks["her"]["head"][0] + 3.0, marks["her"]["head"][1] - 1.0)
            K.sight_line(cc, eye, (hp[0] + 6.0, hp[1] - 1.0), t, T_GLANCE + 0.05, PAPER, dur=0.35, r=1.3, gap=4.6,
                         head=5.0, march=6.0, seed=1101)
        K.ripple(cc, hp, t, T_TAP, PAPER, n=1, life=0.35, r0=2.0, r1=12.0, width=0.9, seed=1102)
        cc.save()
        cc.rectangle(hp[0] - 200.0, St.FEET + 0.5, 400.0, 220.0)
        cc.clip()
        K.ripple(cc, hp, t, T_KNOCK, PAPER, n=4, every=0.12, life=0.9, r0=4.0, r1=46.0, width=1.5, seed=1103)
        cc.restore()
    vault_shot(c, t, VAULT_CAM, people, under=under, overlay=overlay)


# ================================================================ the scene
def render(f, t, T):
    if t < T_PANIC:
        K.scene_setup(f, INK)
    elif t < T_LEVEL:
        K.scene_setup(f, DEEP)
    elif t < T_EYE:
        K.scene_setup(f, DEEP)
    elif t < T_DIVE[1] or T_EYE_OUT[0] <= t < T_BACK:
        K.scene_setup(f, AMBER)
    elif t < T_EYE_OUT[0]:
        K.scene_setup(f, NIGHT)
    else:
        K.scene_setup(f, DEEP)
    with f.screen() as c:
        if t < T_PANIC:
            draw_match_shot(c, t)
        elif t < T_LEVEL:
            c.save()
            tilt_on(c, t)
            if t < T_DOOR:
                draw_panic(c, t)
            else:
                draw_door(c, t)
            c.restore()
        elif t < T_FACE:
            draw_listen(c, t)
        elif t < T_EYE:
            draw_smile(c, t)
        elif t < T_DIVE[1] or T_EYE_OUT[0] <= t < T_BACK:
            draw_eye(c, t)
        elif t < T_EYE_OUT[0]:
            night_before(c, t)
        else:
            draw_knock(c, t)


def cues(T):
    return [
        Cue(0.0, "black: the old man's ragged breath, close", gain_db=-12, dur=1.6),
        Cue(T_SCRATCH, "a match scratches on its box", gain_db=-8, pan=0.3),
        Cue(T_STRIKE, "the match flares", gain_db=-8, pan=0.3),
        Cue(T_STRIKE + 0.1, "the flame's soft breath", gain_db=-20, pan=0.3, dur=0.3),
        Cue(T_PANIC, "his heartbeat, fast and loud", gain_db=-6, dur=T_LEVEL - T_PANIC),
        Cue(T_PANIC, "a high held string, rising", gain_db=-12, dur=T_LEVEL - T_PANIC),
        Cue(T_BLOWS[0], "a fist on the steel door: a muffled BOOM", gain_db=-4, pan=-0.4),
        Cue(T_BLOWS[1], "a fist on the steel door: a muffled BOOM", gain_db=-4, pan=-0.4),
        Cue(T_BLOWS[2], "a fist on the steel door: a muffled BOOM", gain_db=-3, pan=-0.4),
        Cue(T_BLOWS[2] + 0.5, "he sags against the door: a breath, cloth on steel", gain_db=-16, pan=-0.4),
        Cue(T_LEVEL, "far off through the walls, the alarm bell, faint and steady", gain_db=-18, pan=-0.6, dur=2.0),
        Cue(T_SMILE, "her breath of a laugh (the DOUBLE CROSS voice take)", gain_db=-10),
        Cue(T_EYE, "a low held note under her eye", gain_db=-16, dur=0.75),
        Cue(T_DIVE[0], "into her eye: a deep rising whoosh", gain_db=-8, dur=0.5),
        Cue(T_DIVE[1], "the night before: drips in a hollow shaft", gain_db=-18, dur=T_EYE_OUT[0] - T_DIVE[1]),
        Cue(T_CUTS[0][0] - 0.3, "the torch lights: a pop and a hiss", gain_db=-12, pan=0.1),
        Cue(T_CUTS[0][0], "the torch's roar and hiss as it cuts up through stone, sparks spitting", gain_db=-9, pan=0.1,
            dur=0.6),
        Cue(T_CUTS[1][0], "the torch's roar and hiss as it cuts again", gain_db=-9, pan=0.15, dur=0.6),
        Cue(T_PUSH[0], "stone grinding as the block lifts a crack; a shimmer on the gold above", gain_db=-12, dur=0.4),
        Cue(T_SET[0], "the block set back: stone settling, a soft knock", gain_db=-12),
        Cue(T_EYE_OUT[0], "out of her eye: a reverse whoosh", gain_db=-10, dur=0.25),
        Cue(T_BACK, "the vault: the bell faint through the walls, the match's breath", gain_db=-20, dur=2.0),
        Cue(T_TAP, "her heel taps the floor: a click", gain_db=-10, pan=0.2),
        Cue(T_KNOCK, "a hollow knock: the floor rings hollow under her heel", gain_db=-4, pan=0.2),
        Cue(T_TURN, "the old man turns: a sharp intake of breath", gain_db=-14, pan=-0.3),
    ]
