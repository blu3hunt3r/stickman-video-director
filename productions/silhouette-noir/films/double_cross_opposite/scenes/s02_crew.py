"""s02 · CREW (14-30): the crew's room, where s01's push-in arrived; the three in profile cameos;
over her shoulder through the window, the bank across the street: her look goes to the guard's
lit window (he passes inside with his light), up to the alarm bell over the side door (a lens;
one damped tink), down to the manhole in the road (a dot ring); she turns from the window; at the
table she spreads the plan, the two men come in close, and she begins."""
import math

from engine import bass, paperdoll as pd
from engine.core import clamp, ease, lerp
from engine.timing import Cue
from films.double_cross_opposite import bank as Bk
from films.double_cross_opposite import cast as C
from films.double_cross_opposite import faces as F
from films.double_cross_opposite import kit as K
from films.double_cross_opposite import room as R
from films.double_cross_opposite import street as St

k = K.k
INK, PAPER, AMBER, RED, NIGHT, STEEL, DEEP = K.INK, K.PAPER, K.AMBER, K.RED, K.NIGHT, K.STEEL, K.DEEP
T0 = K.film_start("s02")                  # film time of this scene's t = 0

# ---------------------------------------------------------------- beats (scene time)
T_STAGE = 2.0                             # the room, wide, where s01's push ended (to here)
T_HER, T_CRACKER, T_KNIGHT = 2.0, 3.5, 5.0    # the three cameos, 1.5 s each, cut on the beat
T_HER_LOOK = 2.55                         # in her cameo her look leaves the frame toward the window
T_GLINT = 4.25                            # a glint crosses his spectacles
T_DRAW = 5.6                              # the Knight draws on his cigarette
T_OTS = 6.5                               # over her shoulder
T_LOOK = (7.0, 8.25, 9.5)                 # her look: the guard's window, the bell, the manhole
LOOK_OFF = 1.1                            # each look's tail runs off this long after it flew
T_LENS = (8.45, 9.3)                      # the bell's lens opens .. closes
T_TINK = 8.6                              # one damped tink: the alarm's own note, muted
T_RING_MH = 9.75                          # a dot ring round the manhole's lid
T_TURN = (10.75, 0.55)                    # she turns from the window
T_TABLE = 11.5                            # the table, from the side, under the lamp
T_STEP = (11.5, 0.4)                      # she steps in to the table's end
T_SPREAD = (12.0, 0.75)                   # she spreads the plan
T_KNIGHT_IN = (12.25, 0.65)               # the Knight comes off the wall to the table's end
T_LEAN_IN = (12.6, 0.5)                   # the Cracker leans in
T_BEGIN = 14.0                            # she leans over it and begins (the murmur)

GUARD_X = (200.0, 112.0)                  # the guard behind the wing's windows: x at T_OTS, px/s (walking right)
MOON_S = St.MOON_S
NIGHT_SECTION = dict(sky_lit=0.0, moon_at=MOON_S, under=1.0, gold_glow=1.0, car=dict(lights=0.0), lamp_on=1.0)
TABLE_CAMS = (((207.0, 702.0), 8.2), ((208.0, 704.0), 8.8))


def motion_blur(t, T):
    return 1


# ---------------------------------------------------------------- 0-2: the room
def draw_room(c, t):
    tf = T0 + t
    z = math.exp(lerp(math.log(R.S01_END[1]), math.log(3.45), k(t, 0.0, T_STAGE, "inout")))
    R.draw_stage(c, tf, cam=(R.S01_END[0], z), crew=lambda cc, rect: R.crew_rest(cc, tf, rect), neighbours="asleep",
                 **NIGHT_SECTION)


# ---------------------------------------------------------------- 2-6.5: the three cameos
def draw_cameo(c, t):
    tf = T0 + t
    if t < T_CRACKER:
        u = ease("inout", clamp((t - T_HER) / 1.5))
        K.fill(c, AMBER)
        m = F.her(c, (lerp(630.0, 614.0, u), 1590.0), lerp(1.22, 1.29, u), look=lerp(0.15, 0.75, u), t=tf, field=AMBER)
        K.sight_line(c, m["eye"], (1230.0, m["eye"][1] + 40.0), t, T_HER_LOOK, PAPER, dur=0.5)
    elif t < T_KNIGHT:
        u = ease("inout", clamp((t - T_CRACKER) / 1.5))
        K.fill(c, STEEL)
        g = clamp((t - T_GLINT) / 0.4)
        m = F.cracker(c, (lerp(600.0, 588.0, u), 1600.0), lerp(1.24, 1.31, u), look=0.3, glint=g if 0.0 < g < 1.0 else 0.0,
                      t=tf, field=STEEL)
        if T_GLINT + 0.15 <= t < T_GLINT + 0.6:
            K.twinkle(c, (m["lens"][0] + 30.0, m["lens"][1] - 34.0), 46.0 * math.sin(math.pi * (t - T_GLINT - 0.15) / 0.45),
                      PAPER)
    else:
        u = ease("inout", clamp((t - T_KNIGHT) / 1.5))
        K.fill(c, DEEP)
        F.knight(c, (lerp(460.0, 476.0, u), 1600.0), lerp(1.24, 1.32, u), look=0.6,
                 draw=clamp((t - (T_DRAW - 0.25)) / 0.9), t=tf, smoke=1.0)


# ---------------------------------------------------------------- 6.5-11.5: over her shoulder
TARGETS = ((366.0, -318.0), St.BELL_F, St.LID_ABOVE)      # the guard's window, the bell, the manhole (set px)
LENS_C = (330.0, 560.0)                                    # the bell's lens, in the sky over the side bay
LENS_R = 150.0
LENS_Z = 4.2


def guard_x(t):
    return GUARD_X[0] + GUARD_X[1] * (t - T_OTS)


BELL_DOME = ((-16.0, 6.0), (-14.0, -4.0), (-10.0, -12.0), (0.0, -16.0), (10.0, -12.0), (14.0, -4.0), (16.0, 6.0),
             (20.0, 9.0), (-20.0, 9.0))                   # K.bell's dome, in bell units


def bell_close(c, p, s, ring=0.0):
    """The bell as the lens sees it: a steel dome edged in PAPER, its clapper under it, rocking by `ring` deg."""
    a = math.radians(ring)
    ca, sa = math.cos(a), math.sin(a)

    def tf(q):
        return (p[0] + s * (q[0] * ca - q[1] * sa), p[1] + s * (q[0] * sa + q[1] * ca))
    dome = bass.orient(bass.cut([tf(q) for q in BELL_DOME], seed=1343, amp=0.4 * s, seg=(6.0 * s, 12.0 * s)), True)
    K.edged(c, [dome], lerp(STEEL, PAPER, 0.22), PAPER, 9.0)
    K.dot(c, tf((0.0, 14.0)), 4.5 * s, PAPER, seed=1344)


def bell_lens(t):
    """What the lens shows: the bell close, on its bracket over the side door; the tink rocks it once."""
    def inside(c):
        cam = Bk.Cam(St.BELL_F[0] - (LENS_C[0] - K.W / 2.0) / LENS_Z, St.BELL_F[1] + 6.0 - (LENS_C[1] - K.H / 2.0) / LENS_Z,
                     LENS_Z)
        K.fill(c, NIGHT)
        St.bank_front(c, cam, T0 + t, clock=(11, 58), low=1.0, road="above", moon=False, car=False)
        p = cam.to_frame(St.BELL_F)
        dt = t - T_TINK
        rock = 7.0 * math.sin(2.0 * math.pi * 6.0 * dt) * math.exp(-dt / 0.1) if dt > 0.0 else 0.0
        bell_close(c, p, 1.35 * LENS_Z, rock)
        K.ripple(c, (p[0], p[1] - 4.0 * 1.35 * LENS_Z), t, T_TINK, PAPER, n=2, every=0.14, life=0.6, r0=30.0, r1=120.0,
                 width=6.0, seed=21)
    return inside


def draw_ots(c, t):
    tf = T0 + t
    turn = k(t, T_TURN[0], T_TURN[1], "inout")
    mk = R.her_marks(turn=turn)

    def inside(cc):
        mh = R.ots_to_frame(St.LID_ABOVE)
        g = ease("outback", clamp((t - T_RING_MH) / 0.3))
        if g > 0.0:
            bass.ring(cc, mh, 58.0 * g, 4.0, PAPER, seed=23, n=48)

    def look(cc):
        for i, t0 in enumerate(T_LOOK):
            tp = R.ots_to_frame(TARGETS[i])
            K.sight_line(cc, R.look_from_head(mk, tp), tp, t, t0, PAPER, dur=0.45, off=t0 + LOOK_OFF, off_dur=0.25,
                         seed=30 + i)
        lu = k(t, T_LENS[0], 0.3, "out3") * (1.0 - k(t, T_LENS[1], 0.2, "in3"))
        if lu > 0.0:
            K.callout(cc, R.ots_to_frame(St.BELL_F), LENS_C, LENS_R, bell_lens(t), u=lu, color=PAPER, ring_w=8.0, dot_r=7.0,
                      line_w=4.0, seed=24)

    R.window_view(c, tf, guard_x=guard_x(t), clock=(11, 58), inside=inside, look=look,
                  her=lambda cc: R.her_back(cc, turn=turn, t=tf))


# ---------------------------------------------------------------- 11.5-16: the table
def _fig(c, who, st, pose, x, fy, facing, rim_w=1.4):
    return C.draw(c, who, st, pose, x, fy, s=St.FIG_S, facing=facing, bg=AMBER, rim_w=rim_w)


def table_crew(t, tf):
    def fn(c, rect):
        fy = rect[3]
        tt = K.twos(tf)
        # the Knight, off the wall to the table's end (behind the Cracker), his head going down to it
        u = k(t, T_KNIGHT_IN[0], T_KNIGHT_IN[1], "inout")
        kx = lerp(R.KNIGHT_WALL, R.KNIGHT_TABLE, u)
        stride = math.sin(math.pi * u)
        st = C.standing("knight", spread=16.0 + 70.0 * stride)
        down = k(t, T_BEGIN - 0.3, 0.6, "inout")
        pose = pd.Pose(lean=lerp(-5.0, 7.0, u), head=lerp(-3.0, -14.0, u) - 6.0 * down,
                       arms={"near": ("ang", -6.0 + 10.0 * stride, 16.0), "far": ("ang", 4.0 - 8.0 * stride, 12.0)})
        out = _fig(c, "knight", st, pose, kx, fy - 1.5 * stride, 1)
        C.cigarette(c, out, tf, St.FIG_S, facing=1)
        # the Cracker in his chair, leaning in over the plan
        li = k(t, T_LEAN_IN[0], T_LEAN_IN[1], "inout")
        nod = 2.5 * math.sin(2.0 * math.pi * 0.25 * tt)
        pose = pd.Pose(lean=14.0 + 8.0 * li, head=-12.0 - 8.0 * li + nod,
                       arms={"near": ("ik", R.on_table(R.CRACKER_SEAT, R.TABLE_X - 14.0 + 6.0 * li)),
                             "far": ("ik", R.on_table(R.CRACKER_SEAT, R.TABLE_X - 22.0 + 6.0 * li))})
        _fig(c, "cracker", R.seated("cracker"), pose, R.CRACKER_SEAT, fy, 1)
        # her: a step in to the table's end, the plan pushed open from her end, then over it
        su = k(t, T_STEP[0], T_STEP[1], "inout")
        hx = lerp(R.HER_TABLE + 14.0, R.HER_TABLE, su)
        st = C.standing("architect", spread=16.0 + 60.0 * math.sin(math.pi * su))
        sp = k(t, T_SPREAD[0], T_SPREAD[1], "out3")
        push = math.sin(math.pi * clamp((t - T_SPREAD[0]) / (T_SPREAD[1] + 0.35)))
        over = k(t, T_BEGIN, 0.5, "inout")
        if t < T_SPREAD[0] - 0.15:
            arms = {"near": ("ang", 6.0, 12.0), "far": ("ang", 2.0, 10.0)}
        else:
            x1 = R.TABLE_X + R.TABLE_HALF
            follow = lerp(x1 - 6.0, R.TABLE_X + 8.0, sp)          # the near hand rides the roll open, then comes home
            near = lerp(lerp(x1 - 4.0, follow, push), R.TABLE_X + 14.0, over)
            far = lerp(x1 - 9.0, R.TABLE_X + 24.0, over)
            arms = {"near": ("ik", R.on_table(hx, near)), "far": ("ik", R.on_table(hx, far))}
        pose = pd.Pose(lean=3.0 + 13.0 * push * (1.0 - over) + 11.0 * over, crouch=8.0 * push + 10.0 * over,
                       head=-6.0 - 8.0 * over, arms=arms)
        _fig(c, "architect", st, pose, hx, fy - 1.2 * math.sin(math.pi * su), -1)
    return fn


def plan_u(t):
    return k(t, T_SPREAD[0], T_SPREAD[1], "out3")


def draw_table(c, t):
    tf = T0 + t
    cam = R.cam_lerp(TABLE_CAMS[0], TABLE_CAMS[1], k(t, T_TABLE, 16.0 - T_TABLE, "inout"))
    R.draw_stage(c, tf, cam=cam, crew=table_crew(t, tf), plan=plan_u(t), neighbours="asleep", **NIGHT_SECTION)


# ---------------------------------------------------------------- the scene
def render(f, t, T):
    if t < T_STAGE:
        K.scene_setup(f, NIGHT)
    elif t < T_OTS:
        K.scene_setup(f, (AMBER, STEEL, DEEP)[0 if t < T_CRACKER else (1 if t < T_KNIGHT else 2)])
    else:
        K.scene_setup(f, AMBER if t < T_TABLE else NIGHT)
    with f.screen() as c:
        if t < T_STAGE:
            draw_room(c, t)
        elif t < T_OTS:
            draw_cameo(c, t)
        elif t < T_TABLE:
            draw_ots(c, t)
        else:
            draw_table(c, t)


def cues(T):
    return [
        Cue(0.0, "the crew's room: the wall clock ticking on the beat, the lamp's chain creaking softly", gain_db=-14,
            dur=T_STAGE),
        Cue(0.6, "the Knight's cigarette: a faint crackle", gain_db=-22),
        Cue(T_HER, "her cameo: a pizzicato note, high (D)", gain_db=-9),
        Cue(T_CRACKER, "the Cracker's cameo: a pizzicato note, middle", gain_db=-9),
        Cue(T_GLINT, "a glint across his spectacles: a soft high string harmonic flick", gain_db=-16),
        Cue(T_KNIGHT, "the Knight's cameo: a pizzicato note, low (C sharp)", gain_db=-8),
        Cue(T_DRAW - 0.2, "the cigarette crackles as he draws on it", gain_db=-14),
        Cue(T_OTS, "over her shoulder: the night street through the glass, a far wind", gain_db=-20, dur=T_TABLE - T_OTS),
        Cue(T_LOOK[0] + 0.2, "a far footstep: the guard on his round inside the bank", gain_db=-22, pan=0.2),
        Cue(T_LOOK[0] + 0.7, "a far footstep: the guard", gain_db=-23, pan=0.25),
        Cue(T_TINK, "one damped tink: the alarm bell's own note, muted by a finger", gain_db=-12, pan=-0.3),
        Cue(T_RING_MH, "a pencil circles the manhole: a soft scratch", gain_db=-18, pan=-0.1),
        Cue(T_TURN[0], "she turns from the window: a coat's rustle", gain_db=-16),
        Cue(T_STEP[0] + 0.1, "her heels: two steps on the boards", gain_db=-14, pan=0.2),
        Cue(T_SPREAD[0], "paper: the plan unrolled and smoothed flat on the table", gain_db=-10),
        Cue(T_KNIGHT_IN[0] + 0.1, "the Knight's heavy steps off the wall: two", gain_db=-13, pan=-0.3),
        Cue(T_LEAN_IN[0], "the Cracker's chair creaks as he leans in", gain_db=-16, pan=-0.2),
        Cue(T_BEGIN, "her murmur, low and close, no words (the DOUBLE CROSS voice take)", gain_db=-8, dur=2.0),
    ]
