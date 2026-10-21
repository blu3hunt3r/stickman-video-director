"""S07 - Left Hand (8.083 s).

"Every match was torn from the left side of the book. He was left-handed.
 That narrowed it down to half the city."

Shot plan (scene seconds; word hits come from T.at)
  0.00-0.92  IN: S06's last frame exactly (same camera, light pooled on his LEFT hand at the hip -
             front view: screen-right). The same hand comes up out of the coat pocket with the open
             matchbook while the camera pushes into a macro (log-space zoom) and the light opens up;
             rack focus from him (now soft background) onto the matchbook
  0.42-2.01  his right hand comes up from behind the desk with a magnifier; macro track right -> left
             along the matches (inout3) while the lens insert (f.clipped, 2.1x) glides over the intact
             matches and reaches the torn stubs on the LEFT exactly on "left" - they glow amber
  2.11-2.79  he puts the magnifier away; his right hand takes the book
  2.79-3.36  "...book.": the LEFT hand tears the next match (from the left side), lifts it, swings it
             back to the striker (anticipation)
  3.36-4.88  "He was left-handed.": slow-motion LEFT-hand swipe along the striker, flare on "left-",
             slow sparks, the flame lights his hollow head from below; slight orbit (roll 0 -> 8 deg)
  4.878      SMASH CUT on "That": a straight-down crowd of umbrellas in the rain (sets.crowd_top)
  6.225      "half": every umbrella in the left half of the frame turns amber (highlight_amt ramps),
             an amber split line draws down the middle
  6.75-8.08  OUT: on "city" the crowd scatters (nobody new arrives; everyone hurries to the nearest
             edge) and the amber dissolves back to white; wet pavement and a trail of wet footprints
             emerge; the last five umbrellas walk out at the edges. This converges exactly on S08's
             opening (its EXITERS and PRINTS). Camera: straight down, Camera(540, 960, 1.0, 0),
             settled from 7.7 s
"""
import math
from contextlib import nullcontext

from engine import *

from scenes._lib_s05_s07 import (cam_for, zlerp, glow_scaled, stub_glow, matchbook_slot, striker_pts,
                                 sparks, rain_top, pavement_top, crowd_top_exit, office_dust, MB_W, MB_H)
from scenes import s06_three_oh_seven as S06

O = sets.OFFICE
DET_X, DET_S = S06.DET_X, S06.DET_S
POCKET = S06.POCKET
BOOK_C = (650.0, 1150.0)                 # top-edge centre of the open book, held at chest height
BOOK_A = -3.0
BOOK_S = 0.5
MISSING = {0, 1, 2, 3, 4}                # torn from the LEFT side of the book
TORN = 5                                 # the match he tears now (leftmost remaining)
MATCH_S = BOOK_S * 60 / 52               # same length as the matches in the book
CROWD = dict(n=62, seed=5, speed=74.0)   # seed 5: no lane within 16 px of the centre line
SPLIT_X = 540.0

# S08 opens on the same straight-down camera: its last five umbrellas ("EXITERS": x, y at S08 t=0,
# vy px/s, R, rot; they accelerate outward at 260 px/s^2) and its trail of wet footprints. S07's
# last frames converge on exactly that state. Read from S08 when available (stays in sync).
try:
    from scenes import s08_the_limp as _S08
    EXITERS = list(_S08.EXITERS)
    PRINTS = [(p["c"], p["ang"], p["side"]) for p in _S08.PRINTS]
    PRINT_S = float(_S08.FP_S)
except Exception:                                  # pragma: no cover - fallback = S08 as of today
    EXITERS = [(250.0, 170.0, -300.0, 52.0, 9.0), (842.0, 310.0, -290.0, 56.0, 20.0),
               (705.0, 1690.0, 290.0, 54.0, 3.0), (300.0, 1830.0, 260.0, 50.0, 14.0),
               (958.0, 1260.0, 330.0, 49.0, 30.0)]
    PRINTS = []
    PRINT_S = 1.55
EXIT_ACC, EXIT_WALK = 260.0, 60.0


def _local(p):
    """Book-local point (x right, y down, unscaled) -> world."""
    a = math.radians(BOOK_A)
    x, y = p[0] * BOOK_S, p[1] * BOOK_S
    return (BOOK_C[0] + x * math.cos(a) - y * math.sin(a), BOOK_C[1] + x * math.sin(a) + y * math.cos(a))


class K:
    pass


def keys(T):
    k = K()
    k.rise0, k.rise1 = 0.0, 0.92
    k.track0, k.track1 = 0.92, 2.25
    k.left = T.at("left")
    k.book = T.at("book")
    k.mag_off0, k.mag_off1 = k.left + 0.10, k.left + 0.36        # magnifier put away (right hand)
    k.take0, k.take1 = k.mag_off1 - 0.04, k.mag_off1 + 0.23     # right hand takes the book
    k.pluck0 = k.take1                                          # left hand reaches the next match
    k.tear = k.book + 0.06                                      # tears it on "book"
    k.lift1 = k.tear + 0.26
    k.strike = T.at("left", 1) + 0.01          # "left-handed": the head flares on "left-"
    k.swipe0 = k.strike - 0.26
    k.aim0 = k.tear + 0.2                      # anticipation: swings the match back to the striker
    k.cut = T.at("that")                       # smash cut
    k.half = T.at("half")
    k.exit0 = T.at("city") - 0.04              # the crowd scatters on "city"
    k.white0, k.white1 = T.end("city") - 0.15, T.end("city") + 0.35
    k.settle = 7.70
    return k


# ----------------------------------------------------------------------------- the hands (front view)
def hands_pose(t, k):
    """His pose and the torn match (hand, angle). Front view: his LEFT hand is screen-right."""
    p = rig.stand(DET_X, O["floor_y"], facing=0, s=DET_S)
    p = rig.breathe(p, t + _T06().duration, amt=0.8, seed=12)      # continuous with S06's breathing
    p = p.copy(head=p.head * 0.4)
    rise = ease("inout3", inv_lerp(k.rise0, k.rise1, t))
    hold_l = _local((86, 104))                # left hand at the book's bottom-right corner
    hold_r = _local((-86, 104))               # right hand at its bottom-left corner
    start_l = (POCKET[0] + 6, POCKET[1])
    base, top = matchbook_slot(BOOK_C, BOOK_A, BOOK_S, TORN)
    s0, s1 = striker_pts(BOOK_C, BOOK_A, BOOK_S)
    ml = 52 * MATCH_S
    head_from = (s1[0] + 2, s1[1] - 1)        # strike: the head runs right -> left along the striker
    head_to = (s0[0] - 4, s0[1] + 1)
    tj = t + _T06().duration                  # S06's tiny hand drift, continued across the cut
    jit = (1.5 * fbm1(tj * 0.8, 3), 1.5 * fbm1(tj * 0.8, 7))
    start_l = (start_l[0] + jit[0], start_l[1] + jit[1])
    L = lerp(start_l, hold_l, rise)
    match = None
    if t >= k.pluck0:                          # reaches up to the leftmost remaining match
        L = lerp(hold_l, (base[0], base[1] + 2), ease("inout3", inv_lerp(k.pluck0, k.tear - 0.06, t)))
    if t >= k.tear - 0.06:                     # tears it off and lifts it (slow)
        u = ease("out3", inv_lerp(k.tear - 0.06, k.lift1, t))
        lifted = (base[0] + 34, base[1] - 30)
        L = lerp((base[0], base[1] + 2), lifted, u)
        match = (L, -90.0)
        if t >= k.aim0:                        # turns it toward the striker (anticipation)
            v = ease("inout3", inv_lerp(k.aim0, k.swipe0, t))
            aim_hand = (head_from[0] + ml + 10, head_from[1] - 8)
            L = lerp(lifted, aim_hand, v)
            match = (L, lerp(-90.0, -184.0, v))
        if t >= k.swipe0:                      # the swipe, in slow motion, accelerating
            w = ease("in", inv_lerp(k.swipe0, k.strike, t))
            head = lerp(head_from, head_to, w)
            ang = lerp(-184.0, -178.0, w)
            L = (head[0] - math.cos(math.radians(ang)) * ml, head[1] - math.sin(math.radians(ang)) * ml)
            match = (L, ang)
        if t >= k.strike:                      # flare; slow-motion follow-through, flame up
            f_ = ease("out3", inv_lerp(k.strike, k.strike + 1.0, t))
            ang0 = -178.0
            h0 = (head_to[0] - math.cos(math.radians(ang0)) * ml, head_to[1] - math.sin(math.radians(ang0)) * ml)
            L = lerp(h0, (BOOK_C[0] + 46, BOOK_C[1] - 26), f_)
            match = (L, lerp(-178.0, -96.0, f_))
    R = lerp(S06.DESK_REST, PICKUP, ease("inout3", inv_lerp(PICK_T[0], PICK_T[1], t)))
    m = magnifier_state(t, k)
    if m is not None:                          # comes up with the magnifier and glides it
        R = magnifier_grip(m)
    if t >= k.take0:                           # ... then takes the book
        u = ease("outback", inv_lerp(k.take0, k.take1, t))
        R = lerp(magnifier_grip(magnifier_state(k.mag_off1 - 1e-3, k)), hold_r, u)
    p = rig.reach(p, "l", L)
    p = rig.reach(p, "r", R)
    return p, match, rise


def book_pos(t, k):
    """The book rides with whichever hand holds it (left first, then right)."""
    rise = ease("inout3", inv_lerp(k.rise0, k.rise1, t))
    off = lerp((POCKET[0] + 6 - _local((86, 104))[0], POCKET[1] - _local((86, 104))[1]), (0.0, 0.0), rise)
    return (BOOK_C[0] + off[0], BOOK_C[1] + off[1])


# ----------------------------------------------------------------------------- macro camera
def macro_cam(t, k):
    end06 = S06.watch_cam(10.0, S06.keys(_T06()))           # S06's final framing (settled)
    if t < k.rise1:
        u = ease("inout3", inv_lerp(0.0, k.rise1, t))
        tgt_w = lerp(end06.to_world((540.0, 960.0)), _local((60, 30)), u)
        z = zlerp(end06.zoom, 5.6, u)
        return Camera(tgt_w[0], tgt_w[1], z)
    # track right -> left along the matches
    u = ease("inout3", inv_lerp(k.track0, k.track1, t))
    x = lerp(_local((60, 30))[0], _local((-52, 10))[0], u)
    y = lerp(_local((60, 30))[1], _local((-52, 10))[1], u)
    z = zlerp(5.6, 6.6, u)
    if t > k.track1:
        u2 = ease("inout3", inv_lerp(k.book - 0.1, k.swipe0, t))
        x = lerp(x, _local((10, 40))[0], u2)
        y = lerp(y, _local((10, 40))[1], u2)
        z = zlerp(6.6, 6.0, u2)
    rot = 0.0
    if t > k.swipe0:
        o = ease("inout", inv_lerp(k.swipe0, k.cut, t))
        rot = 8.0 * o
        z *= 1 + 0.16 * o
        x += -8 * o
        y += -14 * o
    cam = Camera(x, y, z, rot)
    fl = pulse(t, k.strike, 0.02, 0.25)
    if fl > 0:
        cam = cam.shaken(t, amp=5 * fl, rot_amp=0.3 * fl, freq=9, seed=7)
    return cam


_T06_CACHE = []


def _T06():
    if not _T06_CACHE:
        from engine.timing import SceneTiming
        _T06_CACHE.append(SceneTiming("s06"))
    return _T06_CACHE[0]


def draw_book(f, c, glow_amt, torn_gone):
    """Opaque matchbook (hides the torso line behind it) + amber stub glow."""
    missing = set(MISSING)
    if torn_gone:
        missing.add(TORN)
    a = math.radians(BOOK_A)

    def L(q):
        x, y = q[0] * BOOK_S, q[1] * BOOK_S
        return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))
    body = [L((-MB_W / 2, 0)), L((MB_W / 2, 0)), L((MB_W / 2, MB_H)), L((MB_W / 2 - 6, MB_H + 26)),
            L((-MB_W / 2 + 6, MB_H + 26)), L((-MB_W / 2, MB_H))]
    draw.fill(f, body, BLACK, 1.0)                       # the card is opaque (hides his torso line)
    props.matchbook(f, c, BOOK_A, BOOK_S, open_=1.0, missing=missing)
    stub_glow(f, c, BOOK_A, BOOK_S, sorted(MISSING), glow_amt)


def stub_amt(t, k):
    return 0.95 * ease("out3", inv_lerp(k.left - 0.03, k.left + 0.12, t)) * (1 - 0.55 * ease("inout", inv_lerp(k.strike, k.strike + 0.5, t)))


MAG_R, MAG_A = 40.0, 112.0


def _grip_vec():
    a = math.radians(MAG_A)
    return (math.cos(a) * MAG_R * 2.05, math.sin(a) * MAG_R * 2.05)


PICKUP = (640.0, 1334.0)                   # behind the desk front: where the magnifier lies
PICK_T = (0.12, 0.42)                      # right hand goes down for it


def magnifier_state(t, k):
    """Lens centre (world). His RIGHT hand leaves the desk edge, dips behind the desk and comes up
    with the magnifier (it rises from behind the desk front into the light), glides it right ->
    left over the matches, reaches the torn stubs exactly on "left", then puts it away (off frame)."""
    if t < PICK_T[1] or t > k.mag_off1:
        return None
    gv = _grip_vec()
    y = _local((0, -28))[1]
    p_start = (_local((175, 0))[0], y + 60)
    p_stub = (_local((-40, 0))[0], y)
    p_end = (_local((-260, 0))[0], y + 170)
    a = k.track0 - 0.05
    if t < a:                                   # rising with the hand from behind the desk
        u = ease("inout3", inv_lerp(PICK_T[1], a, t))
        return lerp((PICKUP[0] - gv[0], PICKUP[1] - gv[1]), p_start, u)
    if t <= k.left:
        u = ease("inout", inv_lerp(a, k.left, t))
        x, yy = lerp(p_start, p_stub, u)
        return (x, yy - 15 * math.sin(math.pi * u) + 3 * math.sin((t - a) * 2.3))
    if t <= k.mag_off0:
        return (p_stub[0], p_stub[1] + 3 * math.sin((t - a) * 2.3))
    return lerp((p_stub[0], p_stub[1] + 3 * math.sin((k.mag_off0 - a) * 2.3)), p_end,
                ease("in3", inv_lerp(k.mag_off0, k.mag_off1, t)))


def magnifier_grip(m):
    """Where the right hand holds the magnifier's handle."""
    gv = _grip_vec()
    return (m[0] + gv[0], m[1] + gv[1])


def draw_macro(f, t, k):
    cam = f.set_camera(macro_cam(t, k))
    p, match, rise = hands_pose(t, k)
    J = rig.solve(p)
    c = book_pos(t, k)
    torn = t >= k.tear - 0.06
    fl = pulse(t, k.strike, 0.03, 0.42)
    lit = clamp((t - k.strike) / 0.06) if t >= k.strike else 0.0
    tip = None
    if match is not None:
        tip = (match[0][0] + math.cos(math.radians(match[1])) * 52 * MATCH_S,
               match[0][1] + math.sin(math.radians(match[1])) * 52 * MATCH_S)
    # light: S06's closing pool on the hand opens up into the blind stripes + a key on the book
    open_k = ease("inout", inv_lerp(0.05, 0.9, t))
    lights = [Light.radial(J["lh"], lerp(150, 260, open_k), 0.95)]
    lights += [Light.poly(q, 0.75 * open_k) for q in _STRIPES]
    lights.append(Light.radial(_local((0, 40)), 190, 0.8 * open_k))
    if lit > 0 and tip is not None:
        lights.append(Light.radial(tip, 240 * (1 + 0.8 * fl), 1.0))
    amb = lerp(0.0, 0.12, open_k) + 0.25 * fl
    with f.lit(lights, ambient=amb, soften=3):
        with glow_scaled(f, 0.3 * open_k):
            sets.office(f, t, umbrella=True, lamp_on=0.0, window_light_alpha=0.09 * open_k)
        office_dust(f, t + _T06().duration, 0.5 * (1 - smoothstep(0.08, 0.6, t)))   # continues S06's motes
        focus = ease("inout", inv_lerp(0.15, 0.95, t))          # rack focus: him -> the matchbook
        if focus > 0.02:
            with f.blurred(7.5 * focus, alpha=1.0 - 0.4 * focus):
                rig.draw_figure(f, p)
        else:
            rig.draw_figure(f, p)
        m = magnifier_state(t, k)
        if m is not None and t < k.track0 - 0.05:            # coming up from behind the desk
            props.magnifier(f, m, MAG_R, angle=MAG_A)
        x, ty, w, h = O["desk"]
        draw.fill(f, [(x - 22, ty + 2), (x + w + 22, ty + 2), (x + w + 22, ty + h + 4), (x - 22, ty + h + 4)], BLACK, 1.0)
        sets.desk(f)
        bk = smoothstep(0.06, 0.32, t)          # out of the coat pocket
        with f.alpha(bk) if bk < 0.999 else nullcontext():
            draw_book(f, c, stub_amt(t, k), torn)
        if match is not None and lit <= 0:
            props.match(f, match[0], angle=match[1], length=52, s=MATCH_S, t=t, seed=7)
    if match is not None and lit > 0:
        props.match(f, match[0], angle=match[1], length=52, s=MATCH_S, lit=lit, flare=fl, t=t * 0.35, seed=7)
        sparks(f, t, k.strike, tip, n=18, seed=11, speed=190, slow=0.33, life=1.1, grav=260, s=0.9)
    # magnifier gliding over the matches (lens = 2.1x insert of the book)
    m = magnifier_state(t, k)
    if m is not None and t >= k.track0 - 0.05:
        r = MAG_R
        with f.clipped(lambda cc, m=m: cc.arc(m[0], m[1], r * 0.9, 0, 2 * math.pi)):
            draw.circle(f, m, r * 0.9, 1, BLACK, 1.0, fill_it=True)
            mag = cam_for(m, cam.to_screen(m), cam.zoom * 2.1)
            with f.camera(mag):
                with f.lit([Light.radial(m, 200, 1.0)], ambient=0.5, soften=2):
                    draw_book(f, c, stub_amt(t, k), torn)
        with f.lit(lights, ambient=amb, soften=3):          # emerges from the dark into the light
            props.magnifier(f, m, r, angle=MAG_A)
            draw.arc(f, m, r * 0.78, 200, 250, 2.0, WHITE, 0.45)


_QUAD = [(O["window"][0] + 10, O["window"][1] + 20), (O["window"][0] + O["window"][2], O["window"][1] + 10),
         (O["window"][0] - 120, O["floor_y"] - 40), (O["window"][0] - 520, O["floor_y"] + 30)]
_STRIPES = []
for _i in range(10):
    _a0, _a1 = _i / 10, min(1.0, (_i + 0.45) / 10)
    _STRIPES.append([lerp(_QUAD[0], _QUAD[3], _a0), lerp(_QUAD[1], _QUAD[2], _a0),
                     lerp(_QUAD[1], _QUAD[2], _a1), lerp(_QUAD[0], _QUAD[3], _a1)])


# ----------------------------------------------------------------------------- the city from above
def crowd_cam(t, k):
    z = 1.0 + 0.1 * (1 - ease("inout", inv_lerp(k.cut, k.settle, t)))
    z *= 1 + 0.04 * (1 - ease("out3", inv_lerp(k.cut, k.cut + 0.25, t)))      # smash-cut punch
    return Camera(540.0, 960.0, z, 0.0)


def exiter_state(i, t, T):
    """Position/rotation of S08's exiter i at S07 time t (continuous with S08's formula at the cut):
    walks outward at EXIT_WALK, then speeds up at EXIT_ACC exactly as S08 continues it."""
    ux, uy, vy, R, rot = EXITERS[i]
    sg = 1.0 if vy > 0 else -1.0
    tp = t - T.duration                              # S08 time (negative here)
    t0 = -(abs(vy) - EXIT_WALK) / EXIT_ACC           # when it started to hurry
    if tp >= t0:
        y = uy + vy * tp + 0.5 * EXIT_ACC * tp * tp * sg
    else:
        y0 = uy + vy * t0 + 0.5 * EXIT_ACC * t0 * t0 * sg
        y = y0 + sg * EXIT_WALK * (tp - t0)
    return (ux + 8 * fbm1(tp * 0.5, 40 + i), y), R, rot + 5 * fbm1(tp * 0.4, 50 + i)


def half_amt(t, k):
    """Amber on the left half: pops on "half", dissolves back to white after "city"."""
    return ease("out3", inv_lerp(k.half - 0.02, k.half + 0.16, t)) * (1 - ease("inout", inv_lerp(k.white0, k.white1, t)))


def draw_crowd(f, t, k, T):
    cam = f.set_camera(crowd_cam(t, k))
    view = (cam.to_world((0, 0))[0], cam.to_world((0, 0))[1], cam.to_world((W, H))[0], cam.to_world((W, H))[1])
    # the pavement settles to S08's opening exposure (its lit group starts at ambient 0.62)
    pv = 1.0 - 0.38 * ease("inout", inv_lerp(k.exit0 + 0.3, T.duration, t))
    pavement_top(f, t, alpha=pv, ripple_box=(-80.0, -80.0, 1160.0, 2000.0), ripple_rate=0.5)
    pk = ease("inout", inv_lerp(k.exit0 + 0.15, k.exit0 + 0.95, t))          # the wet trail emerges
    if pk > 0.01:
        for c, ang, side in PRINTS:
            if -120 < c[1] < 2040:
                props.footprint(f, c, ang, side, s=PRINT_S, alpha=0.9 * pv * pk, w=2.4, wet=1.0)
    hl = half_amt(t, k)
    left_half = (lambda i, x, y: x < SPLIT_X)
    if t < k.exit0:
        sets.crowd_top(f, t, n=CROWD["n"], seed=CROWD["seed"], speed=CROWD["speed"],
                       highlight=left_half, highlight_amt=hl)
    else:
        crowd_top_exit(f, t, n=CROWD["n"], seed=CROWD["seed"], speed=CROWD["speed"],
                       highlight=left_half, highlight_amt=hl, exit_t0=k.exit0, exit_spread=0.3,
                       exit_acc=2300.0, view=view, exit_to_edge=True)
    for i in range(len(EXITERS)):                     # the last five, still walking in the crowd
        c, R, rot = exiter_state(i, t, T)
        if -2 * R < c[1] < 1920 + 2 * R:
            if c[0] < SPLIT_X and hl > 0:
                props.umbrella_top(f, c, R, rot, WHITE, alpha=1 - hl)
                props.umbrella_top(f, c, R, rot, AMBER, fill_alpha=0.35, alpha=hl)
            else:
                props.umbrella_top(f, c, R, rot)
    rain_top(f, t, n=120, seed=3, alpha=0.45)
    # the amber split line: draws down the middle on "half", then fades as the crowd scatters
    if t >= k.half - 0.02:
        d = ease("out3", inv_lerp(k.half - 0.02, k.half + 0.2, t))
        a = 0.9 * (1 - ease("inout", inv_lerp(k.exit0 - 0.2, k.exit0 + 0.4, t)))
        if a > 0.01:
            with f.screen():
                draw.line(f, (540, 0), (540, 1920 * d), 3.0, AMBER, a, glow=0.8)


# ----------------------------------------------------------------------------- render
def render(f, t, T):
    k = keys(T)
    if t >= k.cut:
        draw_crowd(f, t, k, T)
        return
    draw_macro(f, t, k)


def motion_blur(t, T):
    k = keys(T)
    if k.exit0 + 0.35 < t < k.exit0 + 1.0:      # the crowd scatters fast
        return 4
    if k.exit0 + 0.12 < t < k.exit0 + 1.15:
        return 2
    if k.swipe0 + 0.1 < t < k.strike + 0.02:
        return 2
    return 1


def cues(T):
    k = keys(T)
    c = [Cue(0.05, "paper_rustle", gain_db=-14, pan=0.1),
         Cue(k.track0 + 0.05, "whoosh", gain_db=-24, size=0.15, pan=0.4),
         Cue(k.left, "impact", gain_db=-16, size=0.12, pan=-0.2),
         Cue(k.take0 + 0.05, "paper_rustle", gain_db=-16, pan=-0.15),
         Cue(k.tear - 0.08, "paper_tear", gain_db=-6, pan=0.1),
         Cue(k.strike - 0.06, "match_strike", gain_db=-1, pan=0.05),   # same placement as every strike
         Cue(k.strike + 0.01, "match_flare", gain_db=-4),
         Cue(k.cut, "crowd_walla", gain_db=-9, dur=k.exit0 + 0.85 - k.cut),
         Cue(k.cut + 0.12, "umbrella_flap", gain_db=-16, pan=-0.4),
         Cue(k.half, "string_twang", gain_db=-7, pan=-0.35),
         Cue(k.exit0 + 0.05, "whoosh", gain_db=-14, size=0.45)]
    for i, dt in enumerate((0.15, 0.42, 0.66, 0.88)):
        c.append(Cue(k.exit0 + dt, "footstep", gain_db=-16 - 3 * i, pan=0.5 - 0.3 * i, weight=0.6, wet=1))
    return c
