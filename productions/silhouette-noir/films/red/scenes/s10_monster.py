"""s10 · MONSTER: the village, grey morning (14.0 s). One continuous shot.

IN   (dissolve from s09): the village gate in grey morning light. She walks home along the
     path toward the gate; far behind her the wolf stands at the forest edge, watching.
L19 1.5-4.0   she comes through the gate into the street. Villagers stand in their doorways
     across the street, silent, eyes on her. A man by the well holds a lantern.
L20 5.0-8.0   they recoil: they step back and the doors shut one by one ([looked], [me],
     [like]); on [monster] the man raises his lantern at her.
8.0-14.0  her mother's door bangs open; the mother runs out, drops to her knees and holds
     her (two silhouettes become one). The camera drifts right: at the forest edge the
     wolf turns away and goes back into the trees.
OUT  dip to snow-white (2.0 s): years pass.

Camera: tracks left with her through the gate (zoom 0.40 -> 0.48), holds on the street for
the recoil and the mother's run, then eases right and out (0.42) to put the embrace and the
wolf in one frame.
"""
import math

from engine import atmos
from engine.creatures import Wolf
from engine.motion import Actor
from engine.timing import Cue
from films.red import cast
from films.red import sets as S
from films.red.scenes import _lib_s09_s11 as L
from films.red.sets_common import fogged, mix

V = S.VILLAGE
TER = S.PATH
MOOD = S.MORNING
G = TER.ground_y

GIRL_X0 = 600.0          # on the trail outside the gate when the dissolve starts
GIRL_STOP = -180.0       # where she stops in the street, just inside the gate
WOLF_X = 1350.0          # the wolf down the trail at the forest edge
MAN_X = -540.0           # the man with the lantern, in the street by the well
MOTHER_X = V.door_x      # -1650, her door
EMBRACE_X = GIRL_STOP - 150.0
_NEAR_G = V.layers[2]["g"]             # ground of the near row of houses (par 0.8)

#: villagers in the doorways across the street: (door id, Body, Look, facing yaw, seed, scale k)
DOORS = (("m3", cast.VILLAGER_F, cast.villager_f(), 75.0, 31, 0.92),
         ("n3", cast.VILLAGER_M, cast.villager_m("flatcap"), 105.0, 32, 0.90),
         ("m4", cast.VILLAGER_M, cast.villager_m("cap"), 115.0, 33, 0.92))


def _words(T):
    return dict(when=T.at("when"), walked=T.at("walked"), nobody=T.at("nobody"), cheered=T.at("cheered"),
                they=T.at("they"), looked=T.at("looked"), me=T.at("me"), like=T.at("like"),
                monster=T.at("monster"), monster_end=T.end("monster"))


_C = {}


def _cast(T):
    if _C:
        return _C
    W_ = _words(T)
    # ---- the mother: bursts out of her door on 8.0, runs, drops to her knees and holds her
    m = Actor(cast.MOTHER, cast.mother(), x=MOTHER_X, ground=G, facing=1, seed=4, name="mother")
    m.stand(until=7.98, at=-1.0)
    m.walk(to=EMBRACE_X - 10.0, gait="run", speed=2.05)
    t_down = m.end
    L.kneel(m, t_down, 30.0, x=EMBRACE_X, t_in=0.55, lean=24.0, head=12.0, delay=(0.0, 0.12),
            arms=(60.0, 50.0))
    gx = lambda t: _C["girl"].root(t)[0]
    m.reach("R", t_down + 0.25, 30.0, lambda t: (gx(t) + 22.0, G(gx(t)) - 230.0), fade=0.35)
    m.reach("L", t_down + 0.35, 30.0, lambda t: (gx(t) + 30.0, G(gx(t)) - 190.0), fade=0.35)
    m.key("pitch", [(t_down + 1.0, 0.0), (t_down + 2.6, 3.0, "sine"), (t_down + 4.2, 0.0, "sine"),
                    (t_down + 5.8, 3.0, "sine"), (t_down + 7.4, 0.0, "sine")], mode="add")      # rocking her
    m.eyes(t_down + 0.8, 30.0, fade=0.5, open=0.0)                           # eyes shut, holding her
    # ---- the girl: a slow, tired walk home; stops in the street; held by her mother
    g = Actor(cast.RED_GIRL, cast.red(), x=GIRL_X0, ground=G, facing=-1, seed=9, name="red")
    g.walk(to=GIRL_STOP, gait="child_walk", speed=0.36, at=-1.0)          # arrives ~5.0
    t_meet = t_down - 0.2
    g.stand(until=t_meet - 0.25)
    g.walk(to=GIRL_STOP - 40.0, gait="child_walk", speed=0.5)               # one step into her arms
    g.stand(until=30.0)
    g.look_at(1.6, 4.4, lambda t: (-300.0, 1050.0), fade=0.6, amount=0.6)   # glances up at the doors
    g.key("head", [(5.2, 0.0), (5.8, 14.0, "inout"), (8.2, 14.0), (8.6, 0.0, "inout")], mode="add")   # head down
    g.key("pitch", [(t_meet - 0.1, 0.0), (t_meet + 0.5, 14.0, "inout"), (30.0, 14.0)], mode="add")
    g.arm("L", t_meet + 0.05, 30.0, fade=0.45, sh=128.0, elbow=58.0, abd=14.0)
    g.arm("R", t_meet + 0.15, 30.0, fade=0.45, sh=118.0, elbow=66.0, abd=10.0)
    g.blink(3.1)
    g.blink(7.6)
    # ---- the man with the lantern
    man = Actor(cast.VILLAGER_M, cast.villager_m("flatcap"), x=MAN_X, ground=G, facing=1, seed=21, name="man")
    man.stand(until=30.0, at=-1.0)
    tm = W_["monster"]
    man.key("arm.R.sh", [(-1.0, 12.0), (tm - 0.45, 12.0), (tm + 0.05, 104.0, "out3"), (8.6, 100.0),
                         (9.4, 30.0, "inout"), (30.0, 22.0)], fade=0.3)
    man.key("arm.R.elbow", [(-1.0, 22.0), (tm - 0.45, 22.0), (tm + 0.05, 6.0, "out3"), (8.6, 8.0),
                            (9.4, 30.0, "inout"), (30.0, 26.0)], fade=0.3)
    man.key("pitch", [(tm - 0.5, 0.0), (tm + 0.1, -7.0, "out3"), (8.6, -6.0), (9.4, 0.0, "inout")], mode="add")
    man.key("x", [(tm - 0.5, 0.0), (tm + 0.25, -22.0, "out3"), (30.0, -22.0)], mode="add")
    # ---- a woman in the street who turns her back and goes in
    wom = Actor(cast.VILLAGER_F, cast.villager_f(), x=-960.0, ground=G, facing=1, seed=22, name="woman")
    wom.stand(until=W_["like"] - 0.2, at=-1.0)
    wom.walk(to=-2300.0, gait="walk", speed=0.62)
    # ---- the wolf at the forest edge: watches her go, then turns away into the trees
    w = Wolf(WOLF_X, G, facing=-1, size=330.0, seed=3)
    w.stand(12.15, look=0.0)
    w.turn(1.1)
    w.walk(to=2900.0, dur=4.5)
    # ---- villagers in the doorways: watch, step back, the doors shut on them
    shut = {"m3": W_["looked"] + 0.2, "n3": W_["me"] + 0.15, "m4": W_["like"] + 0.1}
    _C.update(girl=g, mother=m, man=man, woman=wom, wolf=w, shut=shut, t_meet=t_meet, t_down=t_down,
              doors=V.door_schedule(shut, dur=0.32))
    return _C


CAM_KEYS = [                      # (t, x, ground line on screen, zoom[, ease])
    (-0.9, 560.0, 1470.0, 0.42),
    (0.8, 480.0, 1470.0, 0.43, "inout"),
    (5.4, -120.0, 1450.0, 0.60, "inout"),
    (9.3, -170.0, 1450.0, 0.62, "inout"),
    (11.3, -265.0, 1420.0, 0.74, "inout"),
    (13.5, 585.0, 1470.0, 0.50, "inout"),
    (15.2, 620.0, 1475.0, 0.49, "inout"),
]
CAM = L.CamPath([(k[0], k[1], G(k[1]) - (k[2] - 960.0) / k[3], k[3]) + tuple(k[4:]) for k in CAM_KEYS])


def _doorway_rect(d, o):
    """The visible opening of a row doorway (layer coords) when open by o."""
    s = 1.45 * d["sc"]
    dw, dh = 150.0 * s, 420.0 * s
    lw = dw * (1.0 - 0.82 * o)
    return d["x"] - dw / 2 + lw, d["y"] - dh, d["x"] + dw / 2, d["y"] + 2.0


_DOOR_ACTORS = {}


def _door_actor(d, body, look, yaw, seed, k, T, shut_t):
    key = d["id"]
    if key not in _DOOR_ACTORS:
        sc = d["sc"] * k
        a = Actor(body, look, x=d["x"], ground=d["y"] - 4.0, facing=yaw, scale=sc, seed=seed)
        a.stand(until=30.0, at=-1.0, idle=0.7)
        # they watch her (heads follow), then flinch back and turn in as the door swings
        a.key("head_yaw", [(-1.0, -10.0), (2.0, 4.0, "inout"), (4.0, 14.0, "inout")], fade=0.4)
        a.key("pitch", [(shut_t - 0.45, 0.0), (shut_t - 0.2, -9.0, "out3"), (30.0, -9.0)], mode="add")
        a.key("yaw", [(shut_t - 0.35, yaw), (shut_t + 0.05, yaw + 100.0, "inout"), (30.0, yaw + 100.0)], fade=0.2)
        a.key("scale", [(shut_t - 0.45, 0.0), (shut_t + 0.1, -0.07 * sc, "inout"), (30.0, -0.07 * sc)], mode="add")
        _DOOR_ACTORS[key] = a
    return _DOOR_ACTORS[key]


def _draw_doorway_villagers(f, t, T, cs):
    ds = {d["id"]: d for d in V.doorways(f)}
    doors = cs["doors"]
    for (did, body, look, yaw, seed, k) in DOORS:
        d = ds.get(did)
        if d is None:
            continue
        o = V._door_amount(doors, did, t)
        if o <= 0.02:
            continue
        a = _door_actor(d, body, look, yaw, seed, k, T, cs["shut"][did])
        x0, y0, x1, y1 = _doorway_rect(d, o)
        depth = 0.22 if d["row"] == "near" else 0.46
        with S.plane(f, d["par"]) as c:
            c.save()
            c.rectangle(x0, y0, x1 - x0, y1 - y0)
            c.clip()
            a.draw(f, t, c, color=fogged(MOOD, depth * 0.55), eyes=True)
            c.restore()


def render(f, t, T):
    cs = _cast(T)
    f.set_camera(CAM.at(t))
    V.draw_back(f, MOOD, doors=cs["doors"], door_light=0.62, t=t)
    # the forest edge beyond the gate: a misty row, then the first trunks on the trail
    with S.depth_layer(f, MOOD, 0.8, 0.34, blur=1.6) as c:
        L.draw_trunks(c, L.edge_trunks(11, 1000.0, 4600.0), _NEAR_G, MOOD.ink, top=-4200.0)
    _draw_doorway_villagers(f, t, T, cs)
    t_open = 7.9
    door_open = L.k01(t, t_open, 0.22, "out3")
    V.draw_plane(f, MOOD, door_open=door_open, door_light=0.62 * door_open, t=t)
    S.FOREST.draw_plane(f, MOOD, ground=False, markers=True)
    with S.plane(f, 1.0) as c:
        L.draw_trunks(c, L.edge_trunks(5, 1560.0, 4600.0), G, MOOD.ink, top=-3600.0, snow=MOOD.snow)
    with f.layer() as c:
        cs["wolf"].draw(f, t, c, far_shade=0.2)
        cs["woman"].draw(f, t, c)
        man = cs["man"]
        sk = man.draw(f, t, c)
        _man_lantern(f, c, sk, t)
        if t >= t_open - 0.05:
            cs["mother"].draw(f, t, c)
        cs["girl"].draw(f, t, c)
    V.draw_front(f, MOOD, door_light=0.62 * door_open)
    S.FOREST.draw_front(f, MOOD, lip=False, near_markers=True, occluders=False)
    atmos.snow(f, density=0.45, wind=18.0, t=t, seed=41, color=mix(MOOD.snow, (1.0, 1.0, 1.0), 0.4), alpha=0.8)


def _man_lantern(f, c, sk, t):
    """His lantern hangs from his fist; it swings when he thrusts it up at her."""
    hand = sk.j["hand_R"]
    tm = 7.15
    ang = 2.0 * math.sin(t * 1.3)
    if t > tm:
        ang += 14.0 * math.sin((t - tm) * 6.0) * math.exp(-(t - tm) * 1.6)
    S.Lantern(1.15).draw(f, c, hand, ang, lit=1.0, t=t, mood=MOOD, seed=17)


def motion_blur(t, T):
    cs = _cast(T)
    return 2 if cs["t_down"] - 1.4 < t < cs["t_down"] + 0.1 else 1


def cues(T):
    W_ = _words(T)
    cs = _cast(T)
    sh = cs["shut"]
    return [
        Cue(-0.75, "grey morning in the village: still air, soft snowfall, a crow far off", -18, dur=14.75),
        Cue(-0.5, "small tired footsteps in snow, slow, coming through the gate", -14, dur=5.8),
        Cue(1.5, "silence of watching people: a cough stifled, a creak of a door frame", -20, dur=2.5),
        Cue(sh["m3"], "a wooden door shuts (far, muffled thud and latch)", -10, pan=-0.2),
        Cue(sh["n3"], "a wooden door shuts (nearer, heavier, bolt thrown)", -7, pan=0.25),
        Cue(sh["m4"], "a wooden door shuts (far right, quick slam)", -10, pan=0.6),
        Cue(W_["monster"], "a lantern lifted sharply on its iron handle: creak and swing", -10, pan=-0.35),
        Cue(7.9, "her mother's door bangs open", -6, pan=-0.6),
        Cue(8.05, "running footsteps in snow, adult, fast", -9, dur=1.4, pan=-0.4),
        Cue(cs["t_down"], "knees drop into snow; cloth rustle as she gathers the child in", -8),
        Cue(cs["t_down"] + 0.4, "a held breath, a small sob muffled in cloth", -14, dur=1.5),
        Cue(11.7, "at the forest edge: the wolf turns, soft paws in snow, receding", -18, dur=3.2, pan=0.7),
    ]
