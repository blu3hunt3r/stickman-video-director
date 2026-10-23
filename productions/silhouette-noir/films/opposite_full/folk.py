"""OPPOSITE (full): the people in the section's rooms, drawn small.

The three leads are the Bass cut's cut-outs (`B.win_fig`: her, him, the victim). The
neighbours, the little lives behind the other windows, are cut the same way (paperdoll
pieces, always in profile) but never mistaken for them: a bun, curls, a bald head, a cloth
cap. Nobody else wears her bob, his hat or the victim's long hair.

Poses: `F.seated(...)` and `pd.standing(...)` states, or mocap performances. Draw with
`F.draw(c, fig, st, pose, x, floor_y, facing, lit)` at the section's scale `SEC_FS`.
"""
import math
from dataclasses import replace
from functools import lru_cache

from engine import bass, paperdoll as pd
from engine.core import lerp
from films.opposite_bass import world as B
from films.opposite_full import kit as K

SEC_FS = 0.8 / 4.4                # figure units -> px in the section's rooms (rooms.FIG_S / rooms.S: the stage's figures)
DARK_INK = lerp(K.DEEP, K.INK, 0.6)   # furniture and people in a room whose light is off


def _curls(c, rx, ry, seed, a0=-48.0, a1=-226.0, n=40, bumps=7):
    """A mass of curls round the top and back of the head: a bumpy arc, closed at c."""
    pts = [c]
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        g = 1.0 + 0.11 * abs(math.sin(bumps * a * 1.7))
        pts.append((c[0] + rx * g * math.cos(a), c[1] + ry * g * math.sin(a)))
    return pd._cut(pts, seed, amp=0.3)


@lru_cache(maxsize=None)
def figure(kind):
    """A neighbour: 'bun', 'curls' (women), 'bald', 'cap' (men)."""
    if kind in ("bun", "curls"):
        f = pd.woman(None, 5)
        skull = pd._ellipse((8, -318), 36, 43, 951)
        if kind == "bun":
            hair = [pd._cut([(44, -338), (30, -356), (6, -365), (-18, -360), (-34, -342), (-40, -316), (-32, -298),
                             (-24, -318), (-8, -338), (14, -346), (34, -344)], 952),
                    pd._ellipse((-34, -364), 27, 24, 953)]
            # a long dress, straight to the calf (hers is slim and to the knee)
            torso = [(pd._cut([(-24, -258), (30, -258), (42, -200), (34, -110), (42, -20), (58, 206), (-50, 206),
                               (-36, -20), (-30, -110), (-38, -200)], 954), "ink"), f.torso[1]]
        else:
            hair = [_curls((2, -328), 56, 52, 955)]
            # a blouse over slacks: the legs show to the hip
            torso = [(pd._cut([(-26, -258), (32, -258), (44, -200), (38, -110), (42, -30), (40, 12), (-34, 12),
                               (-36, -30), (-32, -110), (-40, -200)], 956), "ink"), f.torso[1]]
        return replace(f, name=kind, head=[(skull, "ink")] + [(h, "ink") for h in hair], torso=torso)
    f = pd.man(None, 5)
    skull = pd._ellipse((10, -338), 38, 45, 961)
    # shirtsleeves to the hips, not his long coat
    torso = [(pd._cut([(-40, -272), (46, -272), (60, -212), (64, -120), (56, -40), (56, 14), (-50, 14), (-48, -60),
                       (-52, -212)], 962), "ink"),
             (pd._cut([(-12, -302), (22, -302), (24, -268), (-14, -268)], 963), "ink")]
    head = [(skull, "ink")]
    if kind == "cap":
        head.append((pd._cut([(-38, -350), (-30, -372), (0, -384), (32, -378), (50, -362), (86, -356), (86, -348),
                              (44, -350), (-36, -342)], 965), "ink"))
    return replace(f, name=kind, head=head, torso=torso)


@lru_cache(maxsize=None)
def small(kind):
    """A neighbour with arms and hands a little thicker, so they read at a fifth of the size."""
    f = figure(kind)
    return replace(f, arm_w=tuple(w * 1.4 for w in f.arm_w), hand_r=f.hand_r * 1.3)


def seated(fig, x, facing, seat_px, reach=0.95):
    """A state for fig sitting at x (figure units) on a seat seat_px high (px at SEC_FS):
    the pelvis on the seat, the feet planted forward."""
    seat = seat_px / SEC_FS
    fx = x + facing * reach * fig.thigh
    return dict(pelvis=(x, -seat - 20.0), feet={"near": (fx + facing * 8.0, 0.0, 0.0), "far": (fx - facing * 8.0, 0.0, 0.0)},
                phase=0.0, speed=0.0, run=0.0, stride=0.0)


def draw(c, fig, st, pose, x, floor_y, facing, lit, scale=SEC_FS, color=None, eyes=None):
    """Draw fig at room x (px) standing on floor_y. lit: the room's light colour, or None
    for a dark room (the figure goes as dark as the furniture, and shuts its eyes unless
    `eyes` says otherwise)."""
    col = color if color is not None else (K.INK if lit is not None else DARK_INK)
    edge = lit if lit is not None else K.DEEP
    if not (eyes if eyes is not None else lit is not None):
        pose.eye = 0.0
    c.save()
    B.place(c, x, floor_y, scale)
    out = B.draw_cutout(c, fig, st, pose, col, facing=facing, edge=edge, outline=edge, ow=10.0)
    head = c.user_to_device(*out["head"])
    c.restore()
    out["head_at"] = c.device_to_user(*head)          # the head, in the caller's px (for sight lines)
    return out


def asleep(c, b, n, room, t):
    """The neighbours after their lights are out (s01's end onward, until s10 wakes them):
    the old man dozing in front of the radio, the woman asleep in her chair, the sleeper in
    his bed; the other rooms are empty. Call from a section's people(c, b, n, room) for a
    dark neighbour's room."""
    fy = room[3]
    if b is K.HER_B and n == 2:
        fig = small("bald")
        p = pd.Pose(lean=-5.0, head=-26.0, arms={"near": ("ang", 8.0, 30.0), "far": ("ang", 4.0, 28.0)})
        draw(c, fig, seated(fig, 0.0, -1, 36.0), p, 276.0, fy, -1, None)
    elif b is K.HER_B and n == 3:
        fig = small("bun")
        p = pd.Pose(lean=-14.0, head=16.0, arms={"near": ("ang", 14.0, 66.0), "far": ("ang", 8.0, 62.0)})
        draw(c, fig, seated(fig, 0.0, -1, 36.0), p, 282.0, fy, -1, None)
    elif b is K.HIS_B and n == 2:
        sleeper(c, 769.0, fy, B.twos(t), None)


def sleeper(c, x, floor_y, t, lit, seed=0):
    """Someone asleep in the bed at x (the section's bed, head on the pillow at its left
    end): a head and a blanket that rises and falls."""
    col = K.INK if lit is not None else DARK_INK
    top = floor_y - 0.9 * 30.0
    br = 1.6 * math.sin(2.0 * math.pi * 0.28 * t + seed)
    pts = [(x - 26.0, top + 1.0), (x - 20.0, top - 11.0 - 0.4 * br), (x + 4.0, top - 15.0 - br), (x + 26.0, top - 12.0 - 0.6 * br),
           (x + 42.0, top - 9.0), (x + 48.0, top - 14.0), (x + 53.0, top - 8.0), (x + 54.0, top + 1.0)]
    bass.fill_polys(c, [bass.orient(bass.cut(pts, seed=970 + seed, amp=0.4), True)], col)
    K.dot(c, (x - 33.0, top - 11.0), 8.5, col, seed=971 + seed)
