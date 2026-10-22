"""s05 · AGAIN: the stacked split screen. Window 9's sheet on Tuesday (top) and on Wednesday
(bottom): the same shadow murder runs in both panels, to the frame, and the third stab lands on
[again]. The lights snap out, the film rewinds, a red line ties the same second, the bottom
panel slides up over the top one (one arm), the silent scream, then the push into the elbow: a
slotted pin in a ring of light and a rod wire, a puppet. The pin ticks round on die / same /
way / twice, the arm cocks, and the last stab lands on the slash line into s06.

Window 9 is the facade's (sets.Facade), rendered into an offscreen frame (the Tuesday panel's
view; Wednesday is the same frame moved down 965 px) and blitted into the panels; the murder
is films/shadowplay/scenes/_lib_shadow_show (the same choreography as s03).

Handoffs: IN (bars from s04, from t = -0.5) two stacked 1080x955 panels split by an ink bar at
y 955-965, window 9 dark, centred at (540, 477.5) and (540, 1442.5), 461 x 576 px each, with
TUESDAY / WEDNESDAY captions centred at y 880 / 1845. OUT (slash, 13.625-14.375) the elbow
pin at screen centre (540, 960), zoom ~10.6; forearm and knife from the pin down-left along
the slash cut's -58 deg line.
"""
import math

from engine import bass, draw
from engine.core import clamp, ease, lerp
from engine.frame import Frame, Camera
from engine.palette import PAPER, RED
from engine.timing import Cue
from films.shadowplay import sets
from films.shadowplay.scenes import _lib_shadow_show as show

INK = sets.INK
FAC = sets.Facade()
WIN = FAC.window_rect(9)
WC = ((WIN[0] + WIN[2]) / 2.0, (WIN[1] + WIN[3]) / 2.0)
Z0, Z1, Z2 = 1.8, 3.35, 10.0          # panel, single view, pin close-up
TOP = (0.0, 0.0, 1080.0, 955.0)       # the Tuesday panel (screen rect)
BOT = (0.0, 965.0, 1080.0, 1920.0)    # the Wednesday panel, under a thin ink bar
SHIFT = 965.0                          # Wednesday = Tuesday's frame moved down by this
PANEL_Y = 477.5                        # screen y of window 9's centre in the Tuesday panel
U_FREEZE = 1.71                      # the replay freezes here: knife raised, before the strike
PUSH_ARM = (250.0, 296.0, 190.0)     # the arm the camera pushes into: knife up and clear of the muntin
TICK = 7.0                           # degrees the pin turns per tick (the forearm winds back)
COCK = (250.0, 340.0, 250.0)         # the arm raised for the last stab
STRIKE = (250.0, 122.0, 122.0)       # the last stab: forearm and blade on the slash line (-58 deg)
STAB_T = (13.43, 13.61)              # the last stab (lands as the slash cut starts at 13.625)
CRANK = (0.95, 0.62)                 # s05 runs the arm wire out to the right: a visible rod line
PIN = 1.2                            # pin-joint size for the close-up
LABEL_Y = 880.0                      # caption centre under the window (Tuesday panel; +SHIFT)
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
    u, p = _state_raw(t, w)
    p["crank"] = CRANK
    p["pin"] = PIN
    return u, p


def _state_raw(t, w):
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
    """The knife arm after the scream: it lifts off her, the pin ticks round on the words
    (the forearm winding back), the arm cocks, and the last stab lands on the slash line."""
    k = _k(t, w["people"] - 0.6, 0.6, "inout")
    sh, el, bl = (lerp(a, b, k) for a, b in zip(contact, PUSH_ARM))
    for tk in w["ticks"]:
        d = TICK * _k(t, tk - 0.02, 0.13, "outback")
        el += d
        bl += d
    c = _k(t, 12.80, 0.50, "out3")
    sh, el, bl = lerp(sh, COCK[0], c), lerp(el, COCK[1], c), lerp(bl, COCK[2], c)
    st = _k(t, STAB_T[0], STAB_T[1] - STAB_T[0], "in3")
    sh, el, bl = lerp(sh, STRIKE[0], st), lerp(el, STRIKE[1], st), lerp(bl, STRIKE[2], st)
    ft = 4.0 * _k(t, STAB_T[1], 0.10, "out3")
    return (sh, el - ft, bl - ft)


def _lamp(t, t_on, w):
    """The bulb behind window 9's sheet in one panel."""
    if t < w["same"]:
        return LEVEL * sets.switch(t, t_on, kind="flicker", seed=9) * show.lamp_level(t - _u0(w))
    return LEVEL * sets.switch(t, w["same"], kind="bulb")


# ----------------------------------------------------------------------------- cameras
def _win_cam(y, z):
    """A camera putting window 9's centre at screen (540, y), at zoom z."""
    return Camera(WC[0], WC[1] + (960.0 - y) / z, z)


def _pin(t, w):
    """World position of the elbow pin in the push-in pose."""
    u, p = _state(max(t, w["people"]), w)
    q = dict(p)
    q["arm"] = PUSH_ARM
    return show.anchors(u, WIN, pose=q)["elbow"]


def _camera(t, w):
    """The camera of the offscreen frame: the Tuesday panel's view (the Wednesday panel is the
    same frame moved down by SHIFT); after the overlay, the one view and the push-in."""
    a = w["arm"]
    if t < a + 0.45:
        return _win_cam(PANEL_Y, Z0)
    if t < w["people"]:
        k = _k(t, a + 0.45, 0.6, "inout")
        return _win_cam(lerp(PANEL_Y, 960.0, k), Z0 * (Z1 / Z0) ** k)
    pin = _pin(t, w)
    k = _k(t, w["people"], 2.2, "inout3")
    z = Z1 * (Z2 / Z1) ** k
    s0 = ((pin[0] - WC[0]) * Z1, (pin[1] - WC[1]) * Z1)
    cx = pin[0] - s0[0] * (1 - k) / z
    cy = pin[1] - s0[1] * (1 - k) / z
    z *= 1.0 + 0.06 * _k(t, 12.8, 0.8, "inout")
    hit = STAB_T[1]
    if t > hit:                                        # the impact jolts the frame
        j = math.exp(-(t - hit) / 0.10)
        return Camera(cx + 9.0 / z * j * math.sin((t - hit) * 95.0), cy + 6.0 / z * j * math.cos((t - hit) * 81.0), z)
    return Camera(cx, cy, z)


def _layout(t, w):
    """[(which, dy, clip, alpha)] in draw order: the 'top' (Tuesday) or 'bot' (Wednesday)
    frame, moved down by dy and clipped to the screen rect clip; plus the ink bar (or None).
    The Wednesday panel slides up over Tuesday on [arm]: translucent only where it lies over
    the Tuesday panel (the double exposure), solid below, and the street continues under it."""
    a = w["arm"]
    if t < a:
        return [("top", 0.0, TOP, 1.0), ("bot", SHIFT, BOT, 1.0)], (0.0, TOP[3], 1080.0, BOT[1])
    if t < a + 0.45:
        k = _k(t, a, 0.45, "inout3")
        y0 = BOT[1] - SHIFT * k                        # the sliding panel's top edge
        dy = SHIFT * (1.0 - k)
        out = [("top", 0.0, TOP, 1.0)]
        if y0 < TOP[3]:
            out.append(("bot", dy, (0.0, y0, 1080.0, TOP[3]), 0.55 if k < 0.999 else 1.0))
        out.append(("bot", dy, (0.0, max(y0, TOP[3]), 1080.0, 1920.0), 1.0))
        return out, (0.0, y0 - (BOT[1] - TOP[3]), 1080.0, y0)
    return [("bot", 0.0, (0.0, 0.0, 1080.0, 1920.0), 1.0)], None


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


def _blit(f, surf, dy, clip, alpha=1.0):
    """Paint an offscreen frame moved down by dy, clipped to the screen rect clip."""
    c = f.ctx
    s = f.scale
    c.save()
    c.identity_matrix()
    c.rectangle(clip[0] * s, clip[1] * s, (clip[2] - clip[0]) * s, (clip[3] - clip[1]) * s)
    c.clip()
    c.set_source_surface(surf, 0.0, dy * s)
    c.paint_with_alpha(clamp(alpha))
    c.restore()


def _label(text):
    return bass.title_glyphs(text, height=62.0, tracking=0.13, seed=11 if text[0] == "T" else 17, rough=1.0,
                             jitter=0.8)


def _panels(lay):
    """One (which, dy, clip) per panel (the first entry of each)."""
    seen, out = set(), []
    for which, dy, clip, alpha in lay:
        if which not in seen:
            seen.add(which)
            out.append((which, dy, clip, alpha))
    return out


def _labels(f, t, w, lay):
    """TUESDAY / WEDNESDAY captions under the windows (Bass cut paper); they leave before
    the overlay."""
    a = w["arm"]
    out = _k(t, a - 0.34, 0.30, "linear")
    if out >= 1.0:
        return
    with f.screen() as c:
        for which, dy, clip, alpha in _panels(lay):
            Tt = _label("TUESDAY" if which == "top" else "WEDNESDAY")
            cy = LABEL_Y + dy
            c.save()
            c.rectangle(clip[0], clip[1], clip[2] - clip[0], clip[3] - clip[1])
            c.clip()
            if which == "bot" and t < w["wed"] + 0.4:
                # WEDNESDAY jumps once (letter by letter) as its panel lights
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


def _tie(f, t, w, lay, u, p, cam):
    """The red line on 'second': rings round both knife tips, a line between them; the
    overlay closes it to one ring, which then goes."""
    s = w["second"]
    if t < s - 0.02 or t > w["arm"] + 0.9:
        return
    sx, sy = cam.to_screen(show.anchors(u, WIN, pose=p)["knife_tip"])
    pts = [(sx, sy + dy) for _, dy, _, _ in _panels(lay)]
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
    lay, bar = _layout(t, w)
    cam = _camera(t, w)
    lv = {"top": _lamp(t, w["on"], w), "bot": _lamp(t, w["wed"], w)}
    surfs = {}
    for which, dy, clip, alpha in lay:
        if which not in surfs:
            twin = [k for k in surfs if abs(lv[k] - lv[which]) < 1e-4]
            surfs[which] = surfs[twin[0]] if twin else _render_panel(f, t, lv[which], u, p, cam)
        _blit(f, surfs[which], dy, clip, alpha)
    if bar is not None:
        with f.screen() as c:
            c.rectangle(bar[0], bar[1], bar[2] - bar[0], bar[3] - bar[1])
            draw.fill(c, INK)
    _tie(f, t, w, lay, u, p, cam)
    _labels(f, t, w, lay)


def motion_blur(t, T):
    w = _words(T)
    if w["same"] < t < w["same"] + 0.32:          # the rewind
        return 3
    if STAB_T[0] + 0.03 < t < STAB_T[1] + 0.06:   # the last stab
        return 3
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
        Cue(STAB_T[1], "shrill string stab into the slash", -2),
    ]
    return out
