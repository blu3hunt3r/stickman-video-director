"""Motion capture for the paper figures: real human motion (CMU Graphics Lab Motion Capture
Database, BVH conversion by B. Hahne / cgspeed) projected to a side view and retargeted onto
engine.paperdoll figures, so fights, falls, flinches and walks keep their true range of motion.

    clip = Clip.load("80_48")                       # assets/mocap/80_48.bvh (Y up, 120 fps)
    perf = Performance(fig, facing=1, x=0.0, near="Right", segments=[
        Seg(clip, 2.0, 5.5, at=0.0),                # source seconds 2.0..5.5 played from t=0
        Seg(Clip.load("76_02"), 6.1, 7.4, at=3.3, blend=0.25),
    ])
    st, pose = perf(t)                              # paperdoll state + pose (figure units)
    fig.draw(ctx, st, pose, colors, facing=perf.facing)

Projection: each frame is seen from the side of the performer's own heading (smoothed), so a
performer who turns a little stays in profile; root travel is measured along the heading of
the segment's first frame. Arms are solved so the wrist lands where the actor's wrist was
(relative to the shoulder), with the elbow on the side the actor's elbow was.
"""
import math
import os
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

from . import paperdoll as pd
from .core import clamp, lerp

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "mocap")


# ----------------------------------------------------------------------------- BVH
def _parse(path):
    with open(path) as fh:
        tok = fh.read().split()
    joints, stack, i = [], [], 0
    chans = 0
    while tok[i] != "MOTION":
        w = tok[i]
        if w in ("ROOT", "JOINT"):
            joints.append(dict(name=tok[i + 1], parent=stack[-1] if stack else -1, offset=None, ch=[], c0=0))
            i += 2
        elif w == "End":
            joints.append(dict(name=joints[stack[-1]]["name"] + "_end", parent=stack[-1], offset=None, ch=[], c0=0))
            i += 2
        elif w == "{":
            stack.append(len(joints) - 1)
            i += 1
        elif w == "}":
            stack.pop()
            i += 1
        elif w == "OFFSET":
            joints[stack[-1]]["offset"] = np.array([float(v) for v in tok[i + 1:i + 4]])
            i += 4
        elif w == "CHANNELS":
            n = int(tok[i + 1])
            joints[stack[-1]]["ch"] = tok[i + 2:i + 2 + n]
            joints[stack[-1]]["c0"] = chans
            chans += n
            i += 2 + n
        else:
            i += 1
    nf = int(tok[i + 2])
    ft = float(tok[i + 5])
    data = np.array(tok[i + 6:i + 6 + nf * chans], dtype=np.float64).reshape(nf, chans)
    return joints, data, ft


def _rotm(axis, deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    o, z = np.ones_like(a), np.zeros_like(a)
    if axis == "X":
        m = [[o, z, z], [z, c, -s], [z, s, c]]
    elif axis == "Y":
        m = [[c, z, s], [z, o, z], [-s, z, c]]
    else:
        m = [[c, -s, z], [s, c, z], [z, z, o]]
    return np.moveaxis(np.array(m), (0, 1), (-2, -1))


def _fk(joints, data):
    nf = len(data)
    R = [None] * len(joints)
    P = [None] * len(joints)
    for j, J in enumerate(joints):
        loc = np.broadcast_to(np.eye(3), (nf, 3, 3)).copy()
        pos = np.zeros((nf, 3))
        for k, c in enumerate(J["ch"]):
            col = data[:, J["c0"] + k]
            if c.endswith("position"):
                pos[:, "XYZ".index(c[0])] = col
            else:
                loc = loc @ _rotm(c[0], col)
        if J["parent"] < 0:
            P[j] = J["offset"] + pos
            R[j] = loc
        else:
            p = J["parent"]
            P[j] = P[p] + np.einsum("fij,j->fi", R[p], J["offset"])
            R[j] = R[p] @ loc
    return {J["name"]: P[j] for j, J in enumerate(joints)}


# ----------------------------------------------------------------------------- clips
SIDES = ("Left", "Right")


class Clip:
    """One BVH take: joint positions (frames x 3, Y up) and a side-view projection."""

    def __init__(self, name, path):
        self.name = name
        joints, data, self.dt = _parse(path)
        self.P = _fk(joints, data)
        self.n = len(data)
        self.dur = (self.n - 1) * self.dt
        # heading: horizontal forward from the hips' left->right line, smoothed over ~0.3 s
        lat = self.P["LeftUpLeg"] - self.P["RightUpLeg"]
        fwd = np.stack([-lat[:, 2], np.zeros(self.n), lat[:, 0]], axis=1)          # lat x up
        fwd /= np.linalg.norm(fwd, axis=1, keepdims=True) + 1e-9
        k = max(1, int(0.15 / self.dt))
        ker = np.ones(2 * k + 1) / (2 * k + 1)
        for c in (0, 2):
            fwd[:, c] = np.convolve(np.pad(fwd[:, c], k, mode="edge"), ker, mode="valid")
        self.fwd = fwd / (np.linalg.norm(fwd, axis=1, keepdims=True) + 1e-9)
        foot = np.minimum(np.minimum(self.P["LeftToeBase"][:, 1], self.P["RightToeBase"][:, 1]),
                          np.minimum(self.P["LeftFoot"][:, 1], self.P["RightFoot"][:, 1]))
        self.floor = float(np.percentile(foot, 3))
        self.thigh = float(np.linalg.norm(self.P["LeftLeg"][0] - self.P["LeftUpLeg"][0]))
        self.shin = float(np.linalg.norm(self.P["LeftFoot"][0] - self.P["LeftLeg"][0]))
        self.ankle_h = float(np.median(np.minimum(self.P["LeftFoot"][:, 1], self.P["RightFoot"][:, 1])) - self.floor)

    @classmethod
    @lru_cache(maxsize=64)
    def load(cls, name):
        return cls(name, os.path.join(ASSETS, name + ".bvh"))

    def _i(self, s):
        f = clamp(s / self.dt, 0.0, self.n - 1.001)
        a = int(f)
        return a, f - a

    def at(self, joint, s):
        a, u = self._i(s)
        A = self.P[joint]
        return A[a] * (1 - u) + A[a + 1] * u

    def heading(self, s):
        a, u = self._i(s)
        h = self.fwd[a] * (1 - u) + self.fwd[a + 1] * u
        return h / (np.linalg.norm(h) + 1e-9)

    def side2d(self, s, head=None):
        """2D side view at source time s: {joint: (fwd, up)} relative to the root (hips) in
        the frame of `head` (default: this frame's heading)."""
        h = self.heading(s) if head is None else head
        root = self.at("Hips", s)
        out = {}
        for j in ("Hips", "Spine1", "Neck1", "Head", "Head_end", "LeftArm", "LeftForeArm", "LeftHand",
                  "RightArm", "RightForeArm", "RightHand", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase",
                  "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase"):
            d = self.at(j, s) - root
            out[j] = (float(d[0] * h[0] + d[2] * h[2]), float(d[1]))
        out["_root"] = (root, float(root[1] - self.floor))
        return out


# ----------------------------------------------------------------------------- performance
@dataclass
class Seg:
    clip: Clip
    src0: float               # source seconds in
    src1: float               # source seconds out
    at: float                 # film/scene time the segment starts
    speed: float = 1.0
    blend: float = 0.25       # crossfade in from the previous segment (s)
    travel: float = 1.0       # root travel multiplier (0 = in place)
    lean: float = 0.0         # extra trunk lean (deg), e.g. to aim a gesture
    near: str = None          # which of the actor's sides faces the camera (default: the performance's)
    mods: dict = field(default_factory=dict)   # arm overrides: side -> fn(t, (sh, el)) -> (sh, el)

    @property
    def end(self):
        return self.at + (self.src1 - self.src0) / self.speed


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


class Performance:
    """A figure's motion as a chain of mocap segments with crossfades; callable at time t."""

    def __init__(self, fig, segments, facing=1, x=0.0, near="Right"):
        self.fig = fig
        self.segs = sorted(segments, key=lambda s: s.at)
        self.facing = facing
        self.x0 = x
        self.near = near
        # root continuity: each segment starts where the previous one was at that moment
        self.anchor = [x]
        for i in range(1, len(self.segs)):
            prev = self.segs[i - 1]
            self.anchor.append(self._root_x(i - 1, self.segs[i].at))

    def _src(self, i, t):
        g = self.segs[i]
        return clamp(g.src0 + (t - g.at) * g.speed, g.src0, g.src1)

    def _root_x(self, i, t):
        g = self.segs[i]
        h0 = g.clip.heading(g.src0)
        d = g.clip.at("Hips", self._src(i, t)) - g.clip.at("Hips", g.src0)
        return self.anchor[i] + self.facing * self._scale(g) * g.travel * float(d[0] * h0[0] + d[2] * h0[2])

    def _scale(self, g):
        return (self.fig.thigh + self.fig.shin) / (g.clip.thigh + g.clip.shin)

    def _raw(self, i, t):
        """(pelvis, feet, lean, head, arms) for segment i at time t, in figure units."""
        g = self.segs[i]
        F, s, fc = self.fig, self._scale(g), self.facing
        near = g.near or self.near
        sides = (("near", near), ("far", "Left" if near == "Right" else "Right"))
        src = self._src(i, t)
        J = g.clip.side2d(src)
        root, hy = J["_root"]
        px = self._root_x(i, t)
        hip_dy = 0.5 * (J["LeftUpLeg"][1] + J["RightUpLeg"][1])          # hip joints sit below the root
        py = -(hy + hip_dy) * s + 4.0
        feet = {}
        for side, key in sides:
            ank = J[key + "Foot"]
            toe = J[key + "ToeBase"]
            pitch = math.degrees(math.atan2(toe[1] - ank[1], toe[0] - ank[0])) + 19.0
            sole = -(hy + ank[1] - g.clip.ankle_h) * s
            feet[side] = (px + fc * ank[0] * s, min(sole, 0.0), pitch)
        sp = J["Neck1"]
        lean = math.degrees(math.atan2(sp[0], sp[1])) + g.lean
        hv = (J["Head_end"][0] - J["Neck1"][0], J["Head_end"][1] - J["Neck1"][1])
        head = -(math.degrees(math.atan2(hv[0], hv[1])) - (lean - g.lean))
        arms = {}
        P = (px, py)
        for side, key in sides:
            sh_m, el_m, wr_m = J[key + "Arm"], J[key + "ForeArm"], J[key + "Hand"]
            q = pd._rot(F.shoulder, lean)
            S = (P[0] + fc * q[0], P[1] + q[1])
            rel = ((wr_m[0] - sh_m[0]) * s, -(wr_m[1] - sh_m[1]) * s)
            T = (S[0] + fc * rel[0], S[1] + rel[1])
            E_m = (S[0] + fc * (el_m[0] - sh_m[0]) * s, S[1] - (el_m[1] - sh_m[1]) * s)
            best = None
            for fw in (1.0, -1.0):
                e, w = pd.ik2(S, T, F.upper, F.fore, forward=fw)
                d = math.dist(e, E_m)
                if best is None or d < best[0]:
                    best = (d, e, w)
            _, e, w = best
            a1 = math.degrees(math.atan2(fc * (e[0] - S[0]), e[1] - S[1]))
            a2 = math.degrees(math.atan2(fc * (w[0] - e[0]), w[1] - e[1]))
            arms[side] = (_wrap(a1 - lean), _wrap(a2 - a1))
        return dict(pelvis=P, feet=feet, lean=lean, head=head, arms=arms)

    def raw(self, t):
        """Blended raw pose at t."""
        i = 0
        while i + 1 < len(self.segs) and t >= self.segs[i + 1].at:
            i += 1
        cur = self._raw(i, t)
        g = self.segs[i]
        if i > 0 and t < g.at + g.blend:
            prev = self._raw(i - 1, t)
            u = clamp((t - g.at) / g.blend)
            u = u * u * (3 - 2 * u)
            cur = _mix(prev, cur, u)
        for side, fn in g.mods.items():
            cur["arms"][side] = fn(t, cur["arms"][side])
        return cur

    def __call__(self, t, pose=None):
        r = self.raw(t)
        st = dict(pelvis=r["pelvis"], feet=r["feet"], phase=0.0, speed=0.0, run=0.0, stride=0.0)
        p = pose or pd.Pose()
        p.lean = r["lean"]
        p.head = r["head"]
        for side, (sh, el) in r["arms"].items():
            p.arms[side] = ("ang", sh, el)
        return st, p


def _mix(a, b, u):
    out = dict(pelvis=(lerp(a["pelvis"][0], b["pelvis"][0], u), lerp(a["pelvis"][1], b["pelvis"][1], u)),
               feet={k: tuple(lerp(x, y, u) for x, y in zip(a["feet"][k], b["feet"][k])) for k in a["feet"]},
               lean=lerp(a["lean"], b["lean"], u), head=lerp(a["head"], b["head"], u), arms={})
    for k in a["arms"]:
        (s0, e0), (s1, e1) = a["arms"][k], b["arms"][k]
        out["arms"][k] = (s0 + _wrap(s1 - s0) * u, e0 + _wrap(e1 - e0) * u)
    return out
