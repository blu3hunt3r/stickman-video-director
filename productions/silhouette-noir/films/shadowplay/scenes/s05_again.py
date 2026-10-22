"""s05 · AGAIN: the stacked split screen. Window 9's sheet on Tuesday (top) and on Wednesday
(bottom): the same shadow murder runs in both panels, to the frame. The lights snap out, the
film rewinds, a red line ties the same second, the bottom panel slides over the top one (one
arm), the silent scream, then the push into the elbow: a pin joint and a wire, a puppet. The
pin turns on every word of "People don't die the same way twice", the arm cocks, and the last
stab becomes the slash cut into s06.

Both panels are the facade's window 9 (sets.Facade) seen close, rendered into an offscreen
frame and blitted into their viewports; the murder is films/shadowplay/scenes/_lib_shadow_show.
"""
import math

from engine import bass, draw
from engine.core import clamp, ease, lerp, hash01
from engine.frame import Frame, Camera
from engine.palette import PAPER, RED
from engine.timing import Cue
from films.shadowplay import sets
from films.shadowplay.scenes import _lib_shadow_show as show

INK = sets.INK
FAC = sets.Facade()
WIN = FAC.window_rect(9)
WC = ((WIN[0] + WIN[2]) / 2.0, (WIN[1] + WIN[3]) / 2.0)
Z0, Z1, Z2 = 1.8, 3.35, 8.0           # panel, single view, pin close-up
TOP = (0.0, 0.0, 1080.0, 955.0)
BOT = (0.0, 965.0, 1080.0, 1920.0)
U_FREEZE = 1.71                      # the replay freezes here: knife raised, before the strike
PUSH_ARM = (250.0, 258.0, 112.0)     # the arm the camera pushes into (elbow clear of the muntin)
TICK = 5.5                           # degrees the pin turns per tick
LABEL_Y = 880.0                      # caption centre under the window, in panel coords
LEVEL = 0.85                         # the lamp behind the sheet (keeps the sheet amber)


def _k(t, t0, dur, e="inout"):
    if t <= t0:
        return 0.0
    if dur <= 0 or t >= t0 + dur:
        return 1.0
    return ease(e, (t - t0) / dur)


def _words(T):
    return dict(on=T.at("On"), wed=T.at("Wednesday"), again=T.at("again"), same=T.at("Same"),
                second=T.at("second"), arm=T.at("arm"), scream=T.at("scream"), people=T.at("People"),
                ticks=(T.at("die"), T.at("same", 3), T.at("way"), T.at("twice")))


# ----------------------------------------------------------------------------- the show clock
def _u0(w):
    """Scene time of show time 0: the third stab lands on 'again'."""
    return w["again"] - show.SPLASH_T


def _state(t, w):
    """Show time u and the (possibly edited) show pose at scene time t."""
    U0 = _u0(w)
    rw0 = w["same"]
    if t < rw0:                                        # real time, both nights in sync
        u = t - U0
        return u, show.pose(u)
    if t < rw0 + 0.30:                                 # the film rewinds
        u = lerp(show.SHOW_LEN, U_FREEZE, ease("inout", (t - rw0) / 0.30))
        return u, show.pose(u)
    r0 = w["scream"] - 0.31
    if t < r0:                                         # freeze: the same second
        return U_FREEZE, show.pose(U_FREEZE)
    s = w["scream"]
    if t < s:                                          # slow-motion strike onto 'scream'
        u = lerp(U_FREEZE, show.STAB_TIMES[0], (t - r0) / (s - r0))
        return u, show.pose(u)
    u = show.STAB_TIMES[0] + 0.05 * _k(t, s, 0.7, "out")
    p = show.pose(u)                                   # her scream, held
    p["arm"] = _arm_after(t, w, p["arm"])
    return u, p


def _arm_after(t, w, contact):
    """The knife arm after the scream: it lifts off her, the pin ticks round on the words,
    the arm cocks back, and the last stab swings through the slash line."""
    lift0 = w["people"] - 0.6
    sh, el, bl = contact
    k = _k(t, lift0, 0.6, "inout")
    sh, el, bl = lerp(sh, PUSH_ARM[0], k), lerp(el, PUSH_ARM[1], k), lerp(bl, PUSH_ARM[2], k)
    for tk in w["ticks"]:
        d = TICK * _k(t, tk - 0.02, 0.13, "outback")
        el -= d
        bl -= d
    cock = _k(t, 12.80, 0.50, "out3")
    el = lerp(el, 300.0, cock)
    bl = lerp(bl, 154.0, cock)
    st = _k(t, 13.45, 0.18, "in3")
    el = lerp(el, 122.0, st)
    bl = lerp(bl, 122.0, st)
    ft = _k(t, 13.63, 0.12, "out3")
    return (sh, el - 12.0 * ft, bl - 12.0 * ft)


def _lamp(t, t_on, w):
    """The bulb behind window 9's sheet in one panel."""
    if t < w["same"]:
        return LEVEL * sets.switch(t, t_on, kind="flicker", seed=9) * show.lamp_level(t - _u0(w))
    return LEVEL * sets.switch(t, w["same"], kind="bulb")


# ----------------------------------------------------------------------------- cameras
def _pin(t, w):
    """World position of the elbow pin in the push-in pose."""
    u, p = _state(max(t, w["people"]), w)
    q = dict(p)
    q["arm"] = PUSH_ARM
    return show.anchors(u, WIN, pose=q)["elbow"]


def _camera(t, w):
    """The panel camera (sub-frame) at time t."""
    a = w["arm"]
    if t < a + 0.45:
        return Camera(WC[0], WC[1], Z0)
    if t < w["people"]:
        k = _k(t, a + 0.45, 0.75, "inout3")
        return Camera(WC[0], WC[1], Z0 * (Z1 / Z0) ** k)
    pin = _pin(t, w)
    k = _k(t, w["people"], 2.2, "inout3")
    z = Z1 * (Z2 / Z1) ** k
    s0 = ((pin[0] - WC[0]) * Z1, (pin[1] - WC[1]) * Z1)
    cx = pin[0] - s0[0] * (1 - k) / z
    cy = pin[1] - s0[1] * (1 - k) / z
    z *= 1.0 + 0.06 * _k(t, 12.8, 0.8, "inout")
    cam = Camera(cx, cy, z)
    if t > 13.6:
        j = math.exp(-(t - 13.63) / 0.12) if t > 13.63 else (t - 13.6) / 0.03
        cam = Camera(cx + 7.0 / z * j * math.sin(t * 91.0), cy + 5.0 / z * j * math.cos(t * 77.0), z)
    return cam


def _viewports(t, w):
    """[(rect, sub-frame centre offset y, alpha, which)] in draw order, plus the bar rect."""
    a = w["arm"]
    if t < a:
        return [(TOP, 0.0, 1.0, "top"), (BOT, 0.0, 1.0, "bot")], (0.0, 955.0, 1080.0, 965.0)
    if t < a + 0.45:
        k = _k(t, a, 0.45, "inout3")
        dy = -965.0 * k
        bot = (BOT[0], BOT[1] + dy, BOT[2], BOT[3] + dy)
        alpha = 0.58 if k < 0.999 else 1.0
        return [(TOP, 0.0, 1.0, "top"), (bot, 0.0, alpha, "bot")], (0.0, 955.0 + dy, 1080.0, 965.0 + dy)
    k = _k(t, a + 0.45, 0.75, "inout3")
    return [((0.0, 0.0, 1080.0, lerp(955.0, 1920.0, k)), 0.0, 1.0, "bot")], None


# ----------------------------------------------------------------------------- drawing
def _render_panel(f, t, lv, u, p, cam):
    """Window 9 on the facade, seen by `cam`, into a fresh offscreen frame."""
    sub = Frame(t, f.scale, pal=f.pal)
    sub.set_camera(cam)
    sub.fill(INK)
    soft = max(0.3, 2.6 / cam.zoom)

    def interior(ctx, win):
        show.casters(ctx, u, win.rect, pose=p, cuts=(win.mode == "shadow"))
    FAC.draw(sub, t, lit={9: lv}, interiors={9: interior},
             curtains={9: dict(kind="sheet", soft=soft, density=0.92)}, halo=0.3, emit=0.0, rain=1.0)
    with sub.light(blur=0.0) as A:
        vb = cam.view_rect(40)
        sets.rain_glints(A, t, vb, color=sets.RAIN, alpha=0.10, density=0.35 / cam.zoom ** 2, seed=77,
                         speed=1300.0, length=34.0, width=1.3 / cam.zoom ** 0.5, wind=0.14)
    return sub.surf


def _blit(f, surf, rect, alpha=1.0):
    c = f.ctx
    s = f.scale
    c.save()
    c.identity_matrix()
    c.rectangle(rect[0] * s, rect[1] * s, (rect[2] - rect[0]) * s, (rect[3] - rect[1]) * s)
    c.clip()
    vc = (rect[1] + rect[3]) / 2.0
    c.set_source_surface(surf, 0.0, (vc - 960.0) * s)
    c.paint_with_alpha(clamp(alpha))
    c.restore()


def _label(text):
    return bass.title_glyphs(text, height=62.0, tracking=0.13, seed=11 if text[0] == "T" else 17, rough=1.0,
                             jitter=0.8)


def _labels(f, t, w, vps):
    """TUESDAY / WEDNESDAY captions under the windows (Bass cut paper); they leave before
    the overlay."""
    a = w["arm"]
    out = _k(t, a - 0.34, 0.30, "linear")
    if out >= 1.0:
        return
    with f.screen() as c:
        for rect, _, alpha, which in vps:
            text = "TUESDAY" if which == "top" else "WEDNESDAY"
            Tt = _label(text)
            cy = rect[1] + LABEL_Y
            c.save()
            c.rectangle(rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])
            c.clip()
            if which == "bot" and t < w["wed"] + 0.4:
                # WEDNESDAY settles as its panel lights (the letters jump once, staggered)
                def fx(i, g, pp, tr, t=t):
                    tr = tr or {}
                    q = _k(t, w["wed"] + 0.035 * i, 0.30, "linear")
                    tr["dy"] = tr.get("dy", 0.0) - 26.0 * math.sin(math.pi * q) * (1 - q)
                    return tr
                bass.draw_title(c, Tt, (540.0, cy), PAPER, u=1.0, fx=fx, alpha=alpha)
            elif out > 0:
                bass.draw_title(c, Tt, (540.0, cy), PAPER, u=1.0 - out, anim="slide", frm="alt", order="rtl",
                                overlap=0.6, dist=900.0, alpha=alpha)
            else:
                bass.draw_title(c, Tt, (540.0, cy), PAPER, alpha=alpha)
            c.restore()


def _tie(f, t, w, vps, u, p):
    """The red line on 'second': rings round both knife tips, a line between them; the
    overlay closes it to one ring, which then goes."""
    s = w["second"]
    if t < s - 0.02 or t > w["arm"] + 0.9:
        return
    cam = Camera(WC[0], WC[1], Z0)
    tip = show.anchors(u, WIN, pose=p)["knife_tip"]
    sx, sy = cam.to_screen(tip)
    pts = []
    for rect, _, _, which in vps:
        vc = (rect[1] + rect[3]) / 2.0
        pts.append((sx, sy + vc - 960.0))
    if len(pts) == 1:
        pts = pts * 2
    gone = _k(t, w["arm"] + 0.5, 0.35, "in3")
    r = 30.0 * bass.pop(t, s, 0.22) * (1.0 - gone)
    line = _k(t, s + 0.08, 0.26, "out3") * (1.0 - gone)
    with f.screen() as c:
        for i, q in enumerate(pts[:2]):
            rr = r * (1.0 if i == 0 else bass.pop(t, s + 0.06, 0.22) / max(bass.pop(t, s, 0.22), 1e-6))
            if rr > 1.0:
                bass.ring(c, q, rr, 5.0, RED, seed=31 + i, n=30)
        a, b = pts[0], pts[1]
        if line > 0 and b[1] - a[1] > 2 * r + 2:
            y0 = a[1] + r
            y1 = lerp(y0, b[1] - r, line)
            bass.line_band(c, [(a[0], y0), (a[0], y1)], RED, width=4.5, seed=37)


def render(f, t, T):
    w = _words(T)
    f.fill(INK)
    f.post["vignette"] = 0.42
    u, p = _state(t, w)
    vps, bar = _viewports(t, w)
    cam = _camera(t, w)
    lv_top = _lamp(t, w["on"], w)
    lv_bot = _lamp(t, w["wed"], w)
    same = abs(lv_top - lv_bot) < 1e-4
    surf_bot = _render_panel(f, t, lv_bot, u, p, cam)
    surf_top = surf_bot if same else _render_panel(f, t, lv_top, u, p, cam)
    for rect, _, alpha, which in vps:
        _blit(f, surf_top if which == "top" else surf_bot, rect, alpha)
    if bar is not None:
        with f.screen() as c:
            c.rectangle(bar[0], bar[1], bar[2] - bar[0], bar[3] - bar[1])
            draw.fill(c, INK)
    _labels(f, t, w, vps)
    _tie(f, t, w, vps, u, p)


def motion_blur(t, T):
    w = _words(T)
    if w["same"] < t < w["same"] + 0.32:          # the rewind
        return 3
    if 13.48 < t < 13.72:                          # the last stab
        return 4
    U0 = _u0(w)
    for ts in show.STAB_TIMES:                     # the three stabs, both nights
        if U0 + ts - show.STRIKE < t < U0 + ts + 0.03:
            return 3
    return 1


def cues(T):
    w = _words(T)
    U0 = _u0(w)
    out = [
        Cue(w["on"], "window 9 light flickers on (Tuesday): switch click, old filament", -8, pan=0.0, dur=0.72),
        Cue(w["wed"], "the same flicker, Wednesday: identical", -8, pan=0.0, dur=0.72),
        Cue(U0 + show.TURN_T[0], "paper doll turns on its rod (both nights)", -16, dur=0.4),
        Cue(U0 + show.RAISE_T[0], "rod creak: the arm rises", -14, dur=0.55),
    ]
    for i, ts in enumerate(show.STAB_TIMES):
        out.append(Cue(U0 + ts, "shrill string stab (Psycho), both panels as one", -3 if i == 2 else -5))
    out += [
        Cue(U0 + show.SPLASH_T, "red paper splash", -10),
        Cue(U0 + show.FALL_T, "a paper body folds: soft thud", -14),
        Cue(U0 + show.LIGHT_OUT_T, "both lights snap out: click", -8),
        Cue(w["same"], "projector restarts: click, tape rewind scrub", -9, dur=0.3),
        Cue(w["second"], "red pencil tick: the same second", -12, dur=0.3),
        Cue(w["arm"] - 0.34, "captions slide away: paper whisk", -16, dur=0.3),
        Cue(w["arm"], "the bottom panel slides over the top: paper slide", -11, dur=0.45),
        Cue(w["scream"] - 0.31, "slow-motion stab: low string swell", -12, dur=0.31),
        Cue(w["scream"], "silence: every sound drops out (the silent scream)", 0, dur=1.6),
        Cue(w["people"], "push in: a held string note", -14, dur=2.2),
    ]
    for tk in w["ticks"]:
        out.append(Cue(tk, "pin-joint creak: the pin turns one tick", -9))
    out += [
        Cue(12.80, "rod creak: the arm cocks back", -10, dur=0.5),
        Cue(13.60, "shrill string stab into the slash", -2),
    ]
    return out
