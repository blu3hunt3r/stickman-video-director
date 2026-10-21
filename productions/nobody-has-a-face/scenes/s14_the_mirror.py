"""S14 - The Mirror (14.083 s).

IN : lands out of s13's whip pan (image streaking left, camera travelling right/up, 8 deg roll):
     a 2.2-frame motion streak (<= 520 px, s13's convention) decays to a clean landing on the
     evidence board by ~0.25 s. The streak is an in-scene smear along the camera path (L.smear),
     not f.whip, because f.whip's np.roll wraps edge content onto the opposite edge.
0.35-7.7  clue montage, one hard hit per narrated clue, each object flashing AMBER on its word:
          Rain (rain-cloud card) | Three-oh-seven (his pocket watch, 3:07, three step-pushes) |
          A left hand (reverse angle: his LEFT hand rises with the burnt match, ember flares) |
          A limp (short-long footprint card, prints light in a limping rhythm) |
          A red umbrella by my own door (whip to the coat rack: THE red umbrella, crimson pulse,
          dripping; track left to reveal his own door).
7.8-11.0  back to the board, over his shoulder: every red string slides in and tightens on the
          portrait at the centre; on "portrait" the photo tears away -> a round mirror.
11.0-14.08 "It was a mirror.": he steps close (his reflection grows, limping), vertigo dolly-zoom
          (the board swells while the mirror holds), on "mirror" the ring snaps to fill the frame
          (BRAAM), near-silence hold, then the ring flashes BLUE.
OUT: mirror ring centred at screen (540, 960), outer radius ~445 px, blazing BLUE.
"""
import math

from engine import *
from scenes import _lib_s14_s15 as L


def _K(T):
    return dict(
        rain=T.at("rain"), three=T.at("three"), oh=T.at("oh"), seven=T.at("seven"),
        a1=T.at("a", 0), left=T.at("left"), hand=T.at("hand"),
        a2=T.at("a", 1), limp=T.at("limp"),
        a3=T.at("a", 2), red=T.at("red"), umbrella=T.at("umbrella"), own=T.at("own"),
        door=T.at("door"), door_end=T.end("door"),
        id=T.at("i'd"), drawing=T.at("drawing"), portrait=T.at("portrait"),
        it=T.at("it"), mirror=T.at("mirror"), mirror_end=T.end("mirror"),
        end=T.duration,
    )


def _cut_f(K):
    return K["door_end"] + 0.04


BOARD_AMBIENT = 0.3
HIT_LEAD = 0.002          # hits are already at full strength on the word time itself


def _hit(t, t0, amp=1.0):
    return amp * pulse(t, t0 - HIT_LEAD, 0.001, 0.17)


def _pop(t, t0, amp=0.5):
    """Two-frame exposure pop that makes a clue hit land like a hard cut."""
    return Light.full(amp * pulse(t, t0 - HIT_LEAD, 0.001, 0.06))


def _office(f, t, alpha=1.0):
    sets.office(f, t, alpha=alpha, lamp_on=alpha, window_light=AMBER, window_light_alpha=0.13 * alpha)


def _board(f, t, flash_rain=0.0, flash_watch=0.0, foot=(0.0, 0.0, 0.0), alpha=1.0):
    _office(f, t, alpha)
    L.board_cards(f, flash_rain, flash_watch, foot, alpha=alpha)
    L.portrait(f, alpha=alpha)
    L.red_strings(f, t, alpha=alpha)
    L.pins(f, alpha=alpha)


# ============================================================================ shot A: Rain
def _cam_rain(t, K):
    u = ease("out3", inv_lerp(0.0, 0.25, t))          # ~330 px/frame at t=0, like s13's last frame
    push = ease("inout3", inv_lerp(0.42, K["three"], t))
    # continues s13's whip: camera travelling right and up (image streaks left), dutch roll 8 -> 0
    return Camera(388.0 - 200.0 * (1 - u) + 18 * push, 606.0 + 60.0 * (1 - u) - 4 * push,
                  3.3 * (1 + 0.07 * push), 8.0 * (1 - u) - 1.2 * push)


def _shot_rain(f, t, K):
    hit = _hit(t, K["rain"])
    shake = lambda c: c.copy(zoom=c.zoom * (1 + 0.06 * hit)).shaken(t, amp=1.5 + 10 * hit, rot_amp=0.1 + 0.5 * hit, seed=21)
    cam = shake(_cam_rain(t, K))
    f.set_camera(cam)
    fr = pulse(t, K["rain"] - HIT_LEAD, 0.001, 0.55) + 0.12 * smoothstep(K["rain"], K["rain"] + 0.3, t)
    lights = [Light.radial(L.BC, 430, 0.55), Light.radial(L.RAIN_C, 160, 0.3 + 0.7 * min(1.0, fr)),
              _pop(t, K["rain"])]
    with f.lit(lights, ambient=BOARD_AMBIENT):
        # s13's whip carries through the cut: streak 2.2 frames long, capped 520 px (as s13)
        L.smear(f, lambda x: shake(_cam_rain(x, K)), t, lambda a: _board(f, t, flash_rain=min(1.0, fr), alpha=a))


# ============================================================================ shot B: 3:07
def _shot_watch(f, t, K):
    step = lambda tk: ease("outexpo", inv_lerp(tk, tk + 0.09, t))
    push = ease("inout", inv_lerp(K["seven"], K["a1"], t))
    z = 4.0 * (1 + 0.1 * step(K["oh"]) + 0.1 * step(K["seven"])) * (1 + 0.05 * push)
    cam = Camera(628.0 - 6 * push, 598.0, z, -4.0 + 1.6 * step(K["oh"]) + 1.6 * step(K["seven"]))
    hit = _hit(t, K["three"]) + 0.5 * _hit(t, K["oh"]) + 0.6 * _hit(t, K["seven"])
    cam = cam.shaken(t, amp=1.5 + 9 * hit, rot_amp=0.1 + 0.4 * hit, seed=22)
    f.set_camera(cam)
    fw = max(pulse(t, K["three"] - HIT_LEAD, 0.001, 0.6), 0.5 * pulse(t, K["oh"] - HIT_LEAD, 0.001, 0.25),
             0.7 * pulse(t, K["seven"] - HIT_LEAD, 0.001, 0.4)) + 0.1
    lights = [Light.radial(L.BC, 430, 0.5), Light.radial(L.WATCH_C, 150, 0.3 + 0.7 * min(1.0, fw)),
              _pop(t, K["three"]), _pop(t, K["oh"], 0.2), _pop(t, K["seven"], 0.25)]
    with f.lit(lights, ambient=BOARD_AMBIENT):
        _board(f, t, flash_watch=min(1.0, fw))


# ============================================================================ shot C: a left hand
def _hand_pose(t, K):
    p = L.detective_rest(540.0, 2.0)
    rise = ease("outback", inv_lerp(K["a1"] + 0.01, K["left"] + 0.03, t))
    dip = 0.12 * math.sin(math.pi * inv_lerp(K["a1"] - 0.02, K["a1"] + 0.07, t))   # anticipation
    look = ease("inout3", inv_lerp(K["left"] + 0.1, K["hand"] + 0.3, t))
    up = p.copy(la=32.0, le=136.0)
    p = p.blend(up, rise - dip * (1 - rise))
    p = p.copy(head=13.0 * look, lean=3.0 * look, ra=p.ra + 2.0 * look)
    return rig.breathe(p, t, 0.5, seed=14)


def _shot_hand(f, t, K):
    push = ease("inout", inv_lerp(K["a1"], K["a2"], t))
    hit = _hit(t, K["left"])
    cam = Camera(584.0 + 6 * push, 990.0 - 10 * push, 2.5 * (1 + 0.06 * push) * (1 + 0.04 * hit), 1.5)
    cam = cam.shaken(t, amp=1.5 + 9 * hit, rot_amp=0.1 + 0.4 * hit, seed=23)
    f.set_camera(cam)
    p = _hand_pose(t, K)
    J = rig.solve(p)
    fa = L.forearm_angle(J, "l")
    flare = pulse(t, K["left"] - HIT_LEAD, 0.001, 0.7)
    ember = clamp(0.22 + 0.78 * flare + 0.05 * fbm1(t * 9, 3))
    tip = (J["lh"][0] + math.cos(math.radians(fa)) * 52 * 1.9 * 0.85,
           J["lh"][1] + math.sin(math.radians(fa)) * 52 * 1.9 * 0.85)
    band_pts = [[(250, 800 + 130 * i), (950, 610 + 130 * i), (950, 655 + 130 * i), (250, 845 + 130 * i)]
                for i in range(5)]
    lights = [Light.radial(tip, 330 * (0.5 + 0.7 * ember)), _pop(t, K["left"], 0.35)] + \
        [Light.poly(b, 0.42) for b in band_pts]
    for b in band_pts:                     # blind-light shafts hanging in the dark behind him
        draw.fill(f, b, AMBER, 0.035, glow=0.15)
    with f.lit(lights, ambient=0.13):
        rig.draw_figure(f, p)
        props.match(f, J["lh"], angle=fa, length=52, s=1.9, burnt=1.0, ember=ember, t=t, seed=7)
    draw.glow_dot(f, tip, 120 * (0.35 + 0.9 * flare), AMBER, 0.35 + 0.6 * flare, core=False)


# ============================================================================ shot D: a limp
def _shot_limp(f, t, K):
    push = ease("inout", inv_lerp(K["a2"], K["a3"], t))
    hit = _hit(t, K["limp"])
    cam = Camera(624.0, 758.0 - 4 * push, 4.3 * (1 + 0.07 * push) * (1 + 0.05 * hit), 4.5 - 1.5 * push)
    cam = cam.shaken(t, amp=1.5 + 9 * hit, rot_amp=0.1 + 0.4 * hit, seed=24)
    f.set_camera(cam)
    lights_on = []
    for d in (0.0, 0.17, 0.53):      # short step, long step
        t0 = K["limp"] + d
        lights_on.append(min(1.0, pulse(t, t0 - HIT_LEAD, 0.001, 0.8) + 0.3 * smoothstep(t0, t0 + 0.4, t)))
    lights = [Light.radial(L.BC, 430, 0.5), Light.radial(L.FOOT_C, 150, 0.3 + 0.7 * max(lights_on)),
              _pop(t, K["limp"])]
    with f.lit(lights, ambient=BOARD_AMBIENT):
        _board(f, t, foot=tuple(lights_on))


# ============================================================================ shot E: the red umbrella
UMB_TIP = (366.0, 1265.0)
UMB_MID = (366.0, 1165.0)


def _cam_limp_end(K):
    return Camera(624.0, 754.0, 4.3 * 1.07, 3.0)


def _cam_umbrella(t, K):
    a = _cam_limp_end(K)
    b = Camera(372.0, 1150.0, 2.75, -1.5)
    c = Camera(284.0, 1136.0, 2.05, 0.0)
    if t < K["red"]:
        w = ease("inout3", inv_lerp(K["a3"], K["red"], t))
        z = math.exp(lerp(math.log(a.zoom), math.log(b.zoom), w))
        return Camera(lerp(a.x, b.x, w), lerp(a.y, b.y, w), z, lerp(a.rot, b.rot, w))
    w = ease("inout3", inv_lerp(K["umbrella"] + 0.05, K["door"] + 0.3, t))
    settle = 1 + 0.035 * (1 - ease("out3", inv_lerp(K["red"], K["red"] + 0.35, t)))
    return Camera(lerp(b.x, c.x, w), lerp(b.y, c.y, w), lerp(b.zoom, c.zoom, w) * settle, lerp(b.rot, c.rot, w))


def _drips(f, t):
    """Rain water dripping off THE umbrella's ferrule into a small puddle (it was just outside)."""
    fy = L.FLOOR
    draw.ellipse(f, (UMB_TIP[0] + 4, fy - 2), 40, 6, 0, 1.8, WHITE, 0.45)
    for i in range(5):
        td = 5.25 + 0.86 * i
        form = inv_lerp(td - 0.35, td, t)
        if 0 < form < 1:
            draw.circle(f, (UMB_TIP[0], UMB_TIP[1] + 3 + 4 * form), 2.0 + 2.5 * form, 1, WHITE, 0.85, fill_it=True)
        dt = t - td
        if 0 <= dt < 0.42:
            y = UMB_TIP[1] + 6 + 0.5 * 3200 * dt * dt
            if y < fy - 4:
                draw.line(f, (UMB_TIP[0], y - 10 - 900 * dt * 0.05), (UMB_TIP[0], y), 3.0, WHITE, 0.85)
        lt = t - (td + 0.42)
        if 0 <= lt < 0.6:
            r = 6 + 50 * lt
            draw.ellipse(f, (UMB_TIP[0] + 2, fy - 2), r, r * 0.16, 0, 1.6, WHITE, 0.7 * (1 - lt / 0.6))
            if lt < 0.12:
                k = lt / 0.12
                for s in (-1, 1):
                    draw.line(f, (UMB_TIP[0] + s * 4, fy - 3), (UMB_TIP[0] + s * (6 + 10 * k), fy - 3 - 12 * math.sin(math.pi * k)),
                              1.6, WHITE, 0.7)


def drip_land_times():
    return [5.25 + 0.86 * i + 0.42 for i in range(5)]


def _shot_umbrella(f, t, K):
    hit = _hit(t, K["red"], 1.2)
    shake = lambda c: c.copy(zoom=c.zoom * (1 + 0.05 * hit)).shaken(t, amp=1.5 + 11 * hit, rot_amp=0.1 + 0.5 * hit, seed=25)
    cam = shake(_cam_umbrella(t, K))
    f.set_camera(cam)
    cp = min(1.4, pulse(t, K["red"] - HIT_LEAD, 0.001, 0.6) + 0.4 * pulse(t, K["umbrella"], 0.05, 0.6))
    door_k = ease("inout3", inv_lerp(K["own"] - 0.25, K["door"] + 0.1, t))
    x, y, w, h = L.DOOR
    lights = [Light.radial(UMB_MID, 240, 0.55 + 0.45 * min(1.0, cp)), Light.radial(L.BC, 430, 0.4),
              Light.rect(x - 10, y - 10, x + w + 10, y + h, 0.75 * door_k), _pop(t, K["red"], 0.4)]
    lights += [Light.poly(q, 0.35) for q in L.stripe_quads(0.0)]
    draw.glow_dot(f, UMB_MID, 230 * (0.8 + 0.4 * cp), CRIMSON, 0.1 + 0.5 * cp, core=False)
    with f.lit(lights, ambient=0.24):
        def content(a):
            _board(f, t, alpha=a)
            with f.alpha(a):
                _drips(f, t)
        if t < K["red"] + 0.1:
            L.smear(f, lambda x: shake(_cam_umbrella(x, K)), t, content, frames=1.6)
        else:
            content(1.0)


# ============================================================================ shots F-G: the mirror
def _main_cam(t, K):
    cf = _cut_f(K)
    tr = Track([(cf, (500.0, 702.0, 1.95)),
                (K["id"], (500.0, 699.0, 2.0), "inout"),
                (K["portrait"] - 0.05, (500.0, 684.0, 2.45), "inout3"),
                (11.0, (500.0, 668.0, 3.4), "inout3"),
                (K["mirror"], (500.0, 665.0, 3.85), "inout"),
                (K["mirror"] + 0.3, (500.0, 665.0, 7.55), "outback"),      # crash zoom, slight overshoot
                (K["end"], (500.0, 665.0, 7.95), "inout")])
    x, y, z = tr(t)
    roll = -2.6 * math.sin(math.pi * inv_lerp(11.0, K["mirror"], t))
    return Camera(x, y, z, roll)


def _board_k(t, K):
    """Board-layer zoom relative to the mirror layer: the vertigo dolly-zoom (board swells while
    the mirror holds), then it keeps rushing outward on the snap."""
    a = ease("inout3", inv_lerp(11.0, K["mirror"], t))
    b = ease("out5", inv_lerp(K["mirror"], K["mirror"] + 0.27, t))
    return 1.0 + 0.42 * a + 0.5 * b


def _blue_flash(t, K):
    e = K["end"]
    return max(0.4 * pulse(t, e - 0.56, 0.02, 0.07), 0.65 * pulse(t, e - 0.42, 0.02, 0.08),
               ease("in3", inv_lerp(e - 0.24, e - 0.045, t)))


def _detective_back(t, K):
    """His real head in the near foreground, back to us (a front-view figure reads the same)."""
    p = L.detective_rest(500.0, 2.0)
    rise = ease("inout3", inv_lerp(K["id"], K["portrait"] - 0.2, t))       # straightens, drawn in
    flinch = pulse(t, K["portrait"], 0.03, 0.28)
    dip = 9.0 * math.exp(-((t - 11.12) / 0.09) ** 2)                       # his short (left) step
    p = p.copy(y=p.y - 10 * rise + 12 * flinch + dip, head=-6 * flinch, la=p.la + 6 * rise, ra=p.ra + 6 * rise)
    return rig.breathe(p, t, 0.6, seed=8)


def _shot_mirror(f, t, K):
    base = _main_cam(t, K)
    tear = K["portrait"]
    tear_hit = pulse(t, tear - HIT_LEAD, 0.001, 0.2)
    snap_hit = pulse(t, K["mirror"] - HIT_LEAD, 0.001, 0.35)
    cam = base.shaken(t, amp=1.2 + 8 * tear_hit + 10 * snap_hit, rot_amp=0.08 + 0.3 * tear_hit, seed=26)
    f.set_camera(cam)
    kb = _board_k(t, K)
    cam_b = cam.copy(zoom=cam.zoom * kb)
    cam_fg = Camera(cam.x, cam.y + 88.0, cam.zoom * 1.75, cam.rot)          # near layer: his head

    conv = inv_lerp(K["id"] - 0.1, tear - 0.12, t)
    vib = (0.18 * inv_lerp(9.2, tear, t) * (t < tear) + 1.1 * pulse(t, tear, 0.01, 0.22)
           + 0.35 * pulse(t, K["mirror"], 0.01, 0.3))
    u_tear = inv_lerp(tear, tear + 0.62, t) if t >= tear else -1.0
    revealed = t >= tear

    hold = smoothstep(11.0, K["mirror"] + 0.3, t)
    fade_red = 1.0 - 0.72 * smoothstep(K["mirror"], K["mirror"] + 0.9, t)   # pins/strings recede in the hold
    bf = _blue_flash(t, K)
    lights = [Light.radial(L.BC, 440, 0.6 * (1 - 0.75 * hold)),
              Light.radial(L.BC, L.MIRROR_R * (2.6 - 1.2 * hold), 0.55 + 0.45 * hold),
              Light.full(0.35 * bf), _pop(t, K["mirror"], 0.6), _pop(t, tear, 0.3)]
    ambient = lerp(BOARD_AMBIENT, 0.07, smoothstep(K["mirror"] - 0.2, K["mirror"] + 0.6, t))

    # reflection ("he steps close": it grows, dipping on his short left step)
    s_ref = Track([(tear, 0.44), (11.0, 0.46), (K["mirror"], 0.64, "inout3"),
                   (K["mirror"] + 0.3, 0.69, "out3"), (K["end"], 0.73, "inout")])(t)
    head_y = Track([(tear, 0.14), (11.0, 0.12), (K["mirror"], -0.04, "inout3"), (K["end"], -0.1, "inout")])(t)
    bob = L.MIRROR_R * (0.07 * math.exp(-((t - 11.3) / 0.1) ** 2) + 0.03 * math.exp(-((t - 11.76) / 0.1) ** 2)
                        - 0.04 * pulse(t, tear, 0.03, 0.25))
    tilt = Track([(12.75, 0.0), (13.45, -7.0, "inout3")])(t)

    card = None
    if u_tear < 1.0:
        if u_tear < 0:
            card = (L.BC, 1.3 * vib * math.sin(t * 31.0), 1.0, 1.0)
        else:
            u = u_tear
            card = ((L.BC[0] + 80 * u + 40 * u * u, L.BC[1] + 30 * u + 820 * u * u), 10 + 75 * u,
                    1.0 + 0.4 * u, 1.0 - smoothstep(0.55, 1.0, u))

    rack = ease("inout3", inv_lerp(_cut_f(K) + 0.08, _cut_f(K) + 0.62, t))   # focus: his head -> the board
    board_blur = 9.0 * (1.0 - rack)
    fg_blur = 1.0 + 6.0 * rack

    def board_plane():
        # --- board layer (the wall): swells around the mirror during the vertigo
        with f.camera(cam_b):
            _office(f, t)
            L.board_cards(f)
        # --- mirror layer
        if revealed:
            def glass():
                props.mirror(f, L.BC, L.MIRROR_R, glint=0.25)
                if bf > 0:
                    draw.circle(f, L.BC, L.MIRROR_R, 1, BLUE, 0.16 * bf, fill_it=True, glow=0.8 * bf)
                L.reflection(f, t, s_ref, head_y, tilt=tilt, bob=bob, glass=1.0 - 0.6 * bf)
                L.glint_sweep(f, inv_lerp(tear + 0.05, tear + 0.55, t), 1.0)
                L.glint_sweep(f, inv_lerp(12.45, 13.35, t), 0.6)
            if card is not None:
                with f.clipped(L.clip_outside([L.box_poly(card[0], L.CARD_W, L.CARD_H, card[1], card[2])])):
                    glass()
            else:
                glass()
            L.torn_scraps(f, fade_red)
            L.tear_fragments(f, inv_lerp(tear, tear + 0.45, t))
        else:
            L.portrait(f, L.BC, card[1], 1.0)
        # --- red strings: anchors on the board layer, ends on the mirror layer
        with f.screen():
            wpx = 2.6 * cam.zoom ** 0.35
            for i, (a, b, k) in enumerate(L.string_ends(conv)):
                pa = cam_b.to_screen(a)
                pb = cam.to_screen(b)
                sg = 0.085 * (1 - k) + 0.006 * math.sin(t * 1.3 + i * 1.7) * (1 - k)
                props.red_string(f, [pa, pb], sag=sg, w=wpx, alpha=fade_red, t=t + i * 0.37, vib=vib * cam.zoom)
        with f.camera(cam_b):
            L.pins(f, corners=False, alpha=fade_red)
        L.pins(f, anchors=False, alpha=fade_red)
        if revealed and card is not None:
            L.portrait(f, card[0], card[1], card[2], card[3])

    with f.lit(lights, ambient=ambient):
        if board_blur > 0.4:
            with f.blurred(board_blur):
                board_plane()
        else:
            board_plane()
        # --- blue flash on the ring
        if bf > 0:
            draw.circle(f, L.BC, L.MIRROR_R, 4.6, BLUE, bf, glow=1.8 * bf)
            draw.circle(f, L.BC, L.MIRROR_R * 1.12, 2.4, BLUE, bf, glow=1.2 * bf)
        # --- his real head in the near foreground until the push carries us past him
        if t < 11.0:
            with f.camera(cam_fg):
                with f.blurred(fg_blur):
                    rig.draw_figure(f, _detective_back(t, K), alpha=0.85)
    if bf > 0:
        draw.glow_dot(f, L.BC, L.MIRROR_R * 2.4, BLUE, 0.55 * bf, core=False)


# ============================================================================ entry points
def render(f, t, T):
    K = _K(T)
    if t < K["three"]:
        _shot_rain(f, t, K)
    elif t < K["a1"]:
        _shot_watch(f, t, K)
    elif t < K["a2"]:
        _shot_hand(f, t, K)
    elif t < K["a3"]:
        _shot_limp(f, t, K)
    elif t < _cut_f(K):
        _shot_umbrella(f, t, K)
    else:
        _shot_mirror(f, t, K)


def cues(T):
    K = _K(T)
    c = [
        Cue(0.0, "whoosh", gain_db=-11, pan=-0.35, size=0.45),                 # tail of s13's whip
        Cue(K["rain"], "impact", gain_db=-3, pan=-0.15, size=0.7),
        Cue(K["three"], "impact", gain_db=-3, pan=0.15, size=0.75),
        Cue(K["oh"], "clock_tick", gain_db=-7, pan=0.15),
        Cue(K["seven"], "clock_tick", gain_db=-5, pan=0.15),
        Cue(K["left"], "impact", gain_db=-3, pan=0.1, size=0.7),
        Cue(K["left"] + 0.03, "ember_sizzle", gain_db=-13, pan=0.2),
        Cue(K["limp"], "impact", gain_db=-3, pan=0.15, size=0.7),
        Cue(K["limp"] + 0.17, "footstep", gain_db=-16, pan=0.15, weight=0.3, wet=0),
        Cue(K["limp"] + 0.53, "footstep", gain_db=-13, pan=0.15, weight=0.65, wet=0),
        Cue(K["a3"] - 0.02, "whip", gain_db=-4, pan=-0.3),
        Cue(K["red"], "impact", gain_db=-2, pan=-0.3, size=0.85),
        Cue(_cut_f(K), "paper_rustle", gain_db=-15),
        Cue(K["portrait"] - 0.02, "string_twang", gain_db=-5),
        Cue(K["portrait"], "paper_tear", gain_db=-2),
        Cue(K["portrait"] + 0.1, "glass_ring", gain_db=-5),
        Cue(K["mirror"], "braam", gain_db=0),
        Cue(K["mirror"], "sub_drop", gain_db=-3),
        Cue(K["end"] - 0.6, "siren_far", gain_db=-17, dur=0.62),
    ]
    for td in drip_land_times():
        if K["red"] < td < _cut_f(K):
            c.append(Cue(td, "drip", gain_db=-14, pan=-0.3))
    # the strings reel in and tighten one after another
    cf = K["id"] - 0.1
    span = (K["portrait"] - 0.12) - cf
    for k, g in ((0.35, -12), (0.55, -10), (0.75, -8), (0.92, -6)):
        c.append(Cue(cf + k * span, "string_tighten", gain_db=g))
    return c


def motion_blur(t, T):
    # Whips are smeared in-scene along the real camera path (L.smear: no f.whip edge wrap, ~3x
    # cheaper than sub-frames); the "mirror" crash zoom stays crisp on purpose (3 sub-frames of a
    # 2x zoom read as three ghost rings, not as blur).
    return 1
