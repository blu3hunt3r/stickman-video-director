"""SHADOW PLAY - interiors.

Room3D       a one-point-perspective box room with per-pixel lighting (bulbs, torches,
             light through a window or a doorway, with mullions and the shadows of blockers).
Apartment9   the theatre (S04, S07, S09, S10): bare room, window, the sheet on its wire, the
             bare-bulb lamp (in front of the sheet for the show, behind it for her trap), the
             table with the puppet rig, the door to the hallway in the left wall.
HerRoom      her dark room seen from inside, looking out through her window (S02, S12):
             sash and mullions, a heavy curtain she can draw (and part a crack), sill with
             plant, mug and binoculars, radiator, armchair, floor lamp, rain on the glass.
NineWindow   window 9 from inside (S08 over her shoulder): the same wall, bare.
HerEntry     her front door from inside with the RED coat on its hook (S06).
her_room_interior(...)  her room as seen from ACROSS the street (S08), for Facade(variant='hers').
KillerRoom   his room (S11): 40 paper dolls pinned on the facade lock, a torch beam finds them.

Room coordinates (Room3D) are metres: X right (0 = middle), Y up (0 = floor), Z into the
room (back wall at Z = depth). Room3D.P(X, Y, Z) gives the world point; Room3D.place(X, Z)
gives (x, floor_y, k) to stand a figure there (k = scale relative to a 600-px adult).
"""
import math

import cairo
import cv2
import numpy as np

from engine import draw
from engine.core import W, H, clamp, lerp, hash01, noise1, fbm1, siren
from engine.frame import array_surface, surf_array
from engine.palette import RED, PAPER

from .sets_base import (PAL, INK, AMBER, HOT, BLUE, PX_M, mix, mul, layer_spec, opened, glow, glow_ellipse,
                        shadow_screen, rrect, camera_for, texture_surface, occlude_emit)
from .sets_props import (binoculars as draw_binoculars, BareLamp, Sheet, Door, flashlight_beam, lamp_light,
                         red_coat, coat_hook, paper_blood)


# =========================================================================== Room3D
class Room3D:
    """One-point-perspective box room; the camera eye is inside it, looking down +Z.

    Room3D(origin, scale=1.0, width=3.8, height=2.9, depth=4.2, eye_h=1.5, eye_back=2.2, focal=1100)
      origin  world point of the vanishing point (eye axis)
      focal   px per metre at 1 m from the eye (x scale)
    """

    def __init__(self, origin=(540.0, 880.0), scale=1.0, width=3.8, height=2.9, depth=4.2, eye_h=1.5,
                 eye_back=2.2, focal=1100.0):
        self.ox, self.oy = float(origin[0]), float(origin[1])
        self.F = focal * scale
        self.hw, self.h, self.zb = width / 2.0, height, depth
        self.E = (0.0, eye_h, -eye_back)

    def P(self, X, Y, Z):
        d = max(Z - self.E[2], 1e-3)
        return (self.ox + self.F * (X - self.E[0]) / d, self.oy - self.F * (Y - self.E[1]) / d)

    def ppm(self, Z):
        """World px per metre at depth Z."""
        return self.F / max(Z - self.E[2], 1e-3)

    def place(self, X, Z):
        """(x, floor_y, k): where a figure standing at (X, Z) touches the floor and its scale
        relative to a 600-px adult."""
        x, y = self.P(X, 0.0, Z)
        return x, y, self.ppm(Z) / PX_M

    def surfaces(self, z_near=None):
        """World polygons of back wall, left wall, right wall, floor, ceiling."""
        hw, h, zb = self.hw, self.h, self.zb
        zn = z_near if z_near is not None else self.E[2] + 0.25
        P = self.P
        return dict(
            back=[P(-hw, 0, zb), P(hw, 0, zb), P(hw, h, zb), P(-hw, h, zb)],
            left=[P(-hw, 0, zn), P(-hw, 0, zb), P(-hw, h, zb), P(-hw, h, zn)],
            right=[P(hw, 0, zb), P(hw, 0, zn), P(hw, h, zn), P(hw, h, zb)],
            floor=[P(-hw, 0, zn), P(hw, 0, zn), P(hw, 0, zb), P(-hw, 0, zb)],
            ceiling=[P(-hw, h, zb), P(hw, h, zb), P(hw, h, zn), P(-hw, h, zn)],
        )

    # ------------------------------------------------------------------ per-pixel light
    def light_map(self, f, lights, par=1.0, ds=4, albedo=None, ambient=0.0, blur=1.2, gain=1.0, holes=(),
                  bounce=0.3):
        """Light the room's surfaces: for every low-res pixel, cast the eye ray into the box,
        find the wall / floor / ceiling point it hits, and sum the lights. ADDED to the frame.

        lights: list of dicts
          point  dict(kind='point', pos=(X,Y,Z), color, power, r0=0.25)      bare bulb
          spot   dict(kind='spot', pos, dir=(dx,dy,dz), cone=deg, soft=deg, color, power)   torch
          window dict(kind='window', src=(X,Y,Z) outside, rect=(x0,y0,x1,y1) on the back wall,
                      mullions=[('v', x, half), ('h', y, half)], color, power,
                      filt=(x0, y0, x1, y1, z, transmission) e.g. the sheet in front of it)
          door   dict(kind='door', src=(X,Y,Z) in the hallway, z0, z1, top, color, power,
                      mask=fn(u, v)->0..1 blocker (u along the opening 0..1, v up 0..1))
          area   dict(kind='area', pos, normal, color, power, r0)            glowing sheet
        albedo: dict(back, walls, floor, ceiling) reflectances.
        holes:  openings that reflect nothing (the window, a doorway):
                ('back', X0, Y0, X1, Y1) | ('left' / 'right', Z0, Y0, Z1, Y1).
        bounce: one-bounce fill: this fraction of the mean light on the walls lights every
                surface again (so the box still reads where no light falls directly)."""
        alb = dict(back=0.5, walls=0.45, floor=0.30, ceiling=0.55)
        if albedo:
            alb.update(albedo)
        cam = f.lcam(par)
        w, h = max(1, f.pw // ds), max(1, f.ph // ds)
        m = cam.matrix()
        m.invert()
        xs = (np.arange(w, dtype=np.float32) + 0.5) * (W / w)
        ys = (np.arange(h, dtype=np.float32) + 0.5) * (H / h)
        SX, SY = np.meshgrid(xs, ys)
        wx = m.xx * SX + m.xy * SY + m.x0
        wy = m.yx * SX + m.yy * SY + m.y0
        dx = (wx - self.ox) / self.F
        dy = -(wy - self.oy) / self.F
        ex, ey, ez = self.E
        big = np.float32(1e9)
        with np.errstate(divide="ignore", invalid="ignore"):
            tx = np.where(dx > 1e-9, (self.hw - ex) / dx, np.where(dx < -1e-9, (-self.hw - ex) / dx, big))
            ty = np.where(dy > 1e-9, (self.h - ey) / dy, np.where(dy < -1e-9, (0.0 - ey) / dy, big))
        tz = np.full_like(tx, self.zb - ez)
        T = np.minimum(np.minimum(tx, ty), tz)
        on_x = (tx <= ty) & (tx <= tz)
        on_y = (~on_x) & (ty <= tz)
        on_z = ~(on_x | on_y)
        Px = ex + T * dx
        Py = ey + T * dy
        Pz = ez + T
        nx = np.where(on_x, -np.sign(dx), 0.0).astype(np.float32)
        ny = np.where(on_y, -np.sign(dy), 0.0).astype(np.float32)
        nz = np.where(on_z, -1.0, 0.0).astype(np.float32)
        A = np.where(on_z, alb["back"], np.where(on_x, alb["walls"], np.where(dy < 0, alb["floor"], alb["ceiling"])))
        for (pl, a0, b0, a1, b1) in holes:
            if pl == "back":
                m = on_z & (Px > a0) & (Px < a1) & (Py > b0) & (Py < b1)
            else:
                side = (dx < 0) if pl == "left" else (dx > 0)
                m = on_x & side & (Pz > a0) & (Pz < a1) & (Py > b0) & (Py < b1)
            A = np.where(m, 0.0, A)
        acc = np.zeros((h, w, 3), np.float32)
        for L in lights:
            kind = L.get("kind", "point")
            col = np.array(L.get("color", AMBER), np.float32)
            pw_ = L.get("power", 1.0)
            if pw_ <= 0:
                continue
            if kind in ("point", "spot", "area"):
                lx, ly, lz = L["pos"]
                vx, vy, vz = lx - Px, ly - Py, lz - Pz
                d2 = vx * vx + vy * vy + vz * vz
                inv = 1.0 / np.sqrt(d2 + 1e-6)
                cosn = np.clip((nx * vx + ny * vy + nz * vz) * inv, 0, 1)
                r0 = L.get("r0", 0.25)
                E = pw_ * cosn / (d2 + r0 * r0)
                if kind == "spot":
                    ddx, ddy, ddz = L["dir"]
                    dn = math.sqrt(ddx * ddx + ddy * ddy + ddz * ddz) or 1.0
                    cs = -(vx * ddx + vy * ddy + vz * ddz) * inv / dn
                    c_in = math.cos(math.radians(L.get("cone", 12.0)))
                    c_out = math.cos(math.radians(L.get("cone", 12.0) + L.get("soft", 6.0)))
                    sp = np.clip((cs - c_out) / max(c_in - c_out, 1e-4), 0, 1)
                    E = E * sp * sp * (3 - 2 * sp)
                if kind == "area":
                    anx, any_, anz = L.get("normal", (0, 0, -1))
                    E = E * np.clip(-(vx * anx + vy * any_ + vz * anz) * inv, 0, 1)
            elif kind == "window":
                sx, sy, sz = L["src"]
                x0, y0, x1, y1 = L["rect"]
                den = sz - Pz
                u = np.where(np.abs(den) > 1e-6, (self.zb - Pz) / den, -1.0)
                qx = Px + u * (sx - Px)
                qy = Py + u * (sy - Py)
                inside = (u > 1e-4) & (qx > x0) & (qx < x1) & (qy > y0) & (qy < y1)
                for (kd, pos, half) in L.get("mullions", ()):
                    if kd == "v":
                        inside &= np.abs(qx - pos) > half
                    else:
                        inside &= np.abs(qy - pos) > half
                vx, vy, vz = sx - Px, sy - Py, sz - Pz
                inv = 1.0 / np.sqrt(vx * vx + vy * vy + vz * vz + 1e-6)
                cosn = np.clip((nx * vx + ny * vy + nz * vz) * inv, 0, 1)
                E = pw_ * cosn * inside
                filt = L.get("filt")
                if filt is not None:
                    fx0, fy0, fx1, fy1, fz, tr = filt
                    uf = np.where(np.abs(den) > 1e-6, (fz - Pz) / den, -1.0)
                    fxq = Px + uf * (sx - Px)
                    fyq = Py + uf * (sy - Py)
                    hit = (uf > 0) & (fxq > fx0) & (fxq < fx1) & (fyq > fy0) & (fyq < fy1)
                    E = np.where(hit, E * tr, E)
                # gentle falloff away from the window
                E = E / (1.0 + 0.08 * (self.zb - Pz) ** 2)
            elif kind == "door":
                sx, sy, sz = L["src"]
                z0, z1, top = L["z0"], L["z1"], L["top"]
                den = sx - Px
                u = np.where(np.abs(den) > 1e-6, (-self.hw - Px) / den, -1.0)
                qz = Pz + u * (sz - Pz)
                qy = Py + u * (sy - Py)
                inside = (u > 1e-4) & (qz > z0) & (qz < z1) & (qy > 0) & (qy < top)
                mask = L.get("mask")
                E = None
                vx, vy, vz = sx - Px, sy - Py, sz - Pz
                d2 = vx * vx + vy * vy + vz * vz
                inv = 1.0 / np.sqrt(d2 + 1e-6)
                cosn = np.clip((nx * vx + ny * vy + nz * vz) * inv, 0, 1)
                E = pw_ * cosn * inside / (0.6 + 0.12 * d2)
                if mask is not None:
                    uu = np.clip((z1 - qz) / max(z1 - z0, 1e-6), 0, 1)
                    vv = np.clip(qy / max(top, 1e-6), 0, 1)
                    E = E * (1.0 - np.clip(mask(uu, vv), 0, 1))
            else:
                continue
            acc += E[..., None] * col[None, None, :]
        if bounce > 0:
            fill = acc.reshape(-1, 3).mean(axis=0) * bounce
            acc += fill[None, None, :]
        acc *= A[..., None] * gain
        if ambient > 0:
            acc += ambient * A[..., None]
        out = np.zeros((h, w, 4), np.float32)
        out[..., 0] = acc[..., 2]
        out[..., 1] = acc[..., 1]
        out[..., 2] = acc[..., 0]
        out[..., :3] = np.clip(out[..., :3], 0, 1) * 255.0
        out[..., 3] = out[..., :3].max(axis=2)          # keep it a valid premultiplied pixel
        if blur > 0:
            out = cv2.GaussianBlur(out, (0, 0), blur)
        surf = array_surface(out)
        with f.screen() as S:
            S.set_operator(cairo.OPERATOR_ADD)
            pat = cairo.SurfacePattern(surf)
            pat.set_filter(cairo.FILTER_BILINEAR)
            pat.set_matrix(cairo.Matrix(xx=w / float(W), yy=h / float(H)))
            S.set_source(pat)
            S.paint()

    def draw_box(self, ctx, tones=None):
        """Fill the five surfaces with their dark base tones (ink lifted a little)."""
        tn = dict(back=0.20, left=0.13, right=0.13, floor=0.08, ceiling=0.10)
        if tones:
            tn.update(tones)
        S = self.surfaces()
        for k in ("ceiling", "floor", "left", "right", "back"):
            draw.poly(ctx, S[k])
            draw.fill(ctx, mix(INK, PAL.fog_at(1.0), tn[k]))


# =========================================================================== apartment 9
class Apartment9:
    """Apartment 9: the theatre. Front view of the room, looking at the window wall.

    Apartment9(origin=(540, 880), scale=1.0)   origin = vanishing point (eye level, middle)

    Layout (metres, Room3D coords; back wall Z = 4.2):
      window      X -0.55..0.55, Y 0.85..2.45 on the back wall
      sheet       on a wire across the room at Z = 3.55, X -0.95..0.95, Y 2.55 down to 0.5
      door        left wall, Z 1.30..2.20 (hinge at Z 2.20, opens into the room)
      table       X 0, Z 2.95 (0.76 m tall) with the puppet rig: two rods to Y 1.45
      lamp        LAMP_FRONT (X 0.45, Z 2.15) for the show; LAMP_BEHIND (X 0.25, Z 3.92)
                  for her trap (between the sheet and the window)
    Anchors: .P(X,Y,Z), .place(X,Z), .rod_tip('man'|'woman'), .crank_point(angle),
             .bulb(lamp_at), .sheet (a Sheet), .door (a Door).

    draw(f, t, **state) draws everything in order; the pieces are also public so people
    can be inserted between them: draw_room, draw_window, draw_behind_sheet, draw_sheet,
    draw_props, draw_door, draw_air (beams, halos, dust)."""

    WINDOW = (-0.55, 0.85, 0.55, 2.45)
    SHEET_Z = 3.55
    SHEET = (-0.95, 2.55, 0.95, 0.50)
    DOOR_Z = (1.30, 2.20)
    DOOR_H = 2.10
    TABLE = (0.0, 2.95, 1.10, 0.60, 0.76)        # X, Z, width, depth, height
    RODS = {"man": (-0.20, 1.45), "woman": (0.22, 1.40)}
    LAMP_FRONT = (0.45, 2.15)
    LAMP_BEHIND = (0.25, 3.92)
    BULB_Y = 1.62

    def __init__(self, origin=(540.0, 880.0), scale=1.0):
        self.room = Room3D(origin, scale)
        self.s = scale
        r = self.room
        X0, Ytop, X1, Yhem = self.SHEET
        zs = self.SHEET_Z
        self.sheet = Sheet(r.P(X0, Ytop, zs), r.P(X1, Ytop, zs), (Ytop - Yhem) * r.ppm(zs), pins=6, seed=9)
        z0, z1 = self.DOOR_Z
        k = (z1 - z0) / 310.0                         # door px -> metres

        def proj(u, n, v, k=k, z1=z1):
            return r.P(-r.hw + n * k, v * k, z1 - u * k)
        self.door = Door(r.P(-r.hw, 0, z1), width=310.0, height=self.DOOR_H / k, swing=-1, project=proj)
        self._door_k = k

    # ------------------------------------------------------------------ anchors
    def P(self, X, Y, Z):
        return self.room.P(X, Y, Z)

    def place(self, X, Z):
        return self.room.place(X, Z)

    def lamp_pos(self, lamp_at="front"):
        if lamp_at == "front":
            return self.LAMP_FRONT
        if lamp_at == "behind":
            return self.LAMP_BEHIND
        return lamp_at

    def bulb3d(self, lamp_at="front", tilt=0.0):
        X, Z = self.lamp_pos(lamp_at)
        a = math.radians(tilt)
        return (X + math.sin(a) * self.BULB_Y, self.BULB_Y * math.cos(a), Z)

    def bulb(self, lamp_at="front", tilt=0.0):
        """World point of the bulb."""
        return self.room.P(*self.bulb3d(lamp_at, tilt))

    def rod_tip(self, who="man"):
        """World point where a puppet is fixed on its rod (top of the rod)."""
        X, Y = self.RODS[who]
        return self.room.P(self.TABLE[0] + X, Y, self.TABLE[1])

    def puppet_scale(self):
        """World px per metre at the puppets' depth (a 0.45 m paper doll -> 0.45 * this)."""
        return self.room.ppm(self.TABLE[1])

    def crank_point(self, angle):
        """World point on the rim of the crank wheel at `angle` degrees (drives the arm wire)."""
        cx, cy, cz = self._crank_center()
        a = math.radians(angle)
        return self.room.P(cx + 0.07 * math.cos(a), cy + 0.07 * math.sin(a), cz)

    def _crank_center(self):
        return (self.TABLE[0] - 0.42, self.TABLE[4] + 0.16, self.TABLE[1] - 0.05)

    def shadow_map(self, caster_z, lamp3d, screen_z=None):
        """(centre, mag, soft) mapping shapes drawn at depth caster_z (as the camera sees
        them) onto their shadow on the sheet plane, for a lamp at lamp3d. Exact for a
        pinhole camera: a homothety about `centre`. soft = penumbra in world px."""
        r = self.room
        zs = screen_z if screen_z is not None else self.SHEET_Z
        lx, ly, lz = lamp3d
        ex, ey, ez = r.E
        if abs(caster_z - lz) < 1e-3:
            caster_z = lz + 1e-3
        k = (zs - lz) / (caster_z - lz)
        m = k * (caster_z - ez) / (zs - ez)
        # translation part: s = C + A + m (p - C), A = (1-k) F (L - E)/(zs - ez)
        Ax = (1 - k) * r.F * (lx - ex) / (zs - ez)
        Ay = -(1 - k) * r.F * (ly - ey) / (zs - ez)
        C = (r.ox, r.oy)
        if abs(1 - m) < 1e-6:
            center = C
        else:
            center = (C[0] + Ax / (1 - m), C[1] + Ay / (1 - m))
        bulb_r = 0.012                    # a clear bulb: the filament is the source
        pen = 2 * bulb_r * abs(zs - caster_z) / max(abs(caster_z - lz), 1e-3)
        soft = pen * r.ppm(zs) * 0.3      # Gaussian sigma ~ a third of the penumbra's width
        return center, m, soft

    # ------------------------------------------------------------------ lights
    def lights(self, t, lamp=0.0, lamp_at="front", lamp_tilt=0.0, sheet=True, street=0.35, police=0.0,
               door_open=0.0, hall=0.0, door_mask=None, flashlights=(), sheet_glow=None):
        """The light list for Room3D.light_map in this room's state."""
        L = []
        X0, Y0, X1, Y1 = self.WINDOW
        mull = [("v", 0.0, 0.03), ("h", (Y0 + Y1) / 2, 0.035)]
        sX0, sYt, sX1, sYh = self.SHEET
        filt = (sX0, sYh, sX1, sYt, self.SHEET_Z, 0.3) if sheet else None
        if street > 0:
            # the streetlamp seven floors down: the window's pattern lands on the ceiling
            L.append(dict(kind="window", src=(0.9, -16.0, self.room.zb + 9.0), rect=self.WINDOW, mullions=mull,
                          color=AMBER, power=0.55 * street, filt=filt))
        if police > 0:
            b, r = siren(t, rate=1.6)
            if b > 0:
                L.append(dict(kind="window", src=(-3.0, -16.0, self.room.zb + 8.0), rect=self.WINDOW, mullions=mull,
                              color=BLUE, power=1.1 * police * b, filt=filt))
            if r > 0:
                L.append(dict(kind="window", src=(2.0, -16.0, self.room.zb + 8.5), rect=self.WINDOW, mullions=mull,
                              color=RED, power=0.75 * police * r, filt=filt))
        if lamp > 0.01:
            L.append(dict(kind="point", pos=self.bulb3d(lamp_at, lamp_tilt), color=mix(AMBER, HOT, 0.5),
                          power=2.2 * lamp, r0=0.3))
        if sheet_glow is not None and sheet_glow > 0.01:
            L.append(dict(kind="area", pos=(0.0, 1.5, self.SHEET_Z - 0.05), normal=(0, 0, -1), color=AMBER,
                          power=1.1 * sheet_glow, r0=0.6))
        if hall > 0.01 and door_open > 0.01:
            z0, z1 = self.DOOR_Z
            # the hallway bulb hangs just outside, toward the stairs: the light comes through
            # the doorway at a slant and lies across the floor as a long wedge
            L.append(dict(kind="door", src=(-self.room.hw - 1.1, 2.75, z0 - 0.7), z0=z0, z1=z1,
                          top=self.DOOR_H, color=mix(AMBER, HOT, 0.3), power=2.6 * hall,
                          mask=self._door_mask(door_open, door_mask)))
        for fl in flashlights:
            L.append(dict(kind="spot", pos=fl["pos"], dir=fl["dir"], cone=fl.get("cone", 9.0), soft=fl.get("soft", 7.0),
                          color=fl.get("color", mix(HOT, (1, 1, 1), 0.2)), power=fl.get("power", 2.4), r0=0.2))
        return L

    @staticmethod
    def match_light(pos, level=1.0, t=0.0, seed=0):
        """A struck match at room point pos=(X, Y, Z): a small, flickering warm point light
        for extra_lights (draw the flame itself with sets.match_flame at P(*pos))."""
        fl = 0.8 + 0.2 * noise1(t * 9.0, seed) + 0.08 * math.sin(t * 31.0 + seed)
        return dict(kind="point", pos=pos, color=mix(AMBER, HOT, 0.6), power=0.55 * level * fl, r0=0.18)

    def _door_mask(self, door_open, mask):
        """Blocker for the doorway light: the leaf (partly open) plus an optional
        caller mask(u, v) (e.g. the killer standing in the doorway)."""
        op = clamp(door_open)

        def m(u, v):
            # u: 0 at the hinge (far edge) .. 1 at the free edge; the open part grows from u = 1
            leaf = np.clip((1.0 - op * 1.15 - u) / 0.04, 0, 1)
            out = leaf
            if mask is not None:
                out = np.maximum(out, mask(u, v))
            return out
        return m

    # ------------------------------------------------------------------ drawing
    def draw(self, f, t, layer=None, lamp=0.0, lamp_at="front", lamp_tilt=0.0, lamp_broken=False, sheet=True,
             table=True, rig=True, crank=0.0, puppets=None, casters=None, caster_z=None, door_open=0.0, hall=0.0,
             door_mask=None, locked=0.0, street=0.35, police=0.0, flashlights=(), outside=None, tears=(),
             sheet_hit=None, sheet_fall=0.0, blood=(), hooks=None, dust=1.0, lamp_stand=True, extra_lights=(),
             feet=()):
        """Draw apartment 9 in a given state.

        lamp        bulb level (sets.switch for the flicker-on); lamp_at 'front' | 'behind' | (X, Z)
        lamp_stand  False: no lamp in the room at all (S04: the police find it empty)
        lamp_tilt   degrees the stand leans (the crash in S10); lamp_broken: the bulb is gone
        sheet/table/rig  which props are present (S04: all False: the room is empty)
        crank       crank-wheel angle (deg) of the rig (drives the arm wire)
        puppets     fn(ctx, apt) drawing the paper dolls at apt.rod_tip(...) (as the camera sees them)
        casters     fn(ctx) drawing what throws shadows on the sheet, at depth caster_z
                    (default: the puppets + rods at the table's depth)
        door_open   0..1 (sets.door_swing / slam); hall 0..1 hallway light; locked 0..1
        feet        positions (door px from the hinge, 0..310) of feet outside the closed door:
                    they break the line of light under it (S09 end)
        door_mask   fn(u, v) -> blocker in the doorway (u 0 hinge..1 free edge, v 0 floor..1 top)
        street      cold street light through the window; police 0..1 strobes through it
        flashlights [dict(pos=(X,Y,Z), dir=(dx,dy,dz), cone, power)] torch beams (S04)
        outside     fn(ctx, rect) to paint the view through the window (default: night + far windows)
        tears / sheet_hit / sheet_fall   see Sheet
        blood       [(X, Y, Z, scale, seed, grow)] red paper splashes on the floor/table
        hooks       {'after_room', 'after_sheet', 'after_props', 'after_door': fn(f, t)} to insert
                    people between the planes.
        extra_lights more Room3D light dicts (her match: Apartment9.match_light(...))."""
        hooks = hooks or {}
        spec = layer_spec(layer)
        par = spec["par"]
        lamp_xz = self.lamp_pos(lamp_at)
        lamp3d = self.bulb3d(lamp_at, lamp_tilt)
        behind = lamp_xz[1] > self.SHEET_Z
        lv = 0.0 if (lamp_broken or not lamp_stand) else lamp
        sheet_glow = lv * (0.9 if behind else 0.5) if sheet else 0.0
        # 1) the box, lit
        with opened(f, spec) as L:
            self.room.draw_box(L)
            self.draw_window(f, t, L, outside=outside, street=street, police=police)
        lights = self.lights(t, lamp=lv, lamp_at=lamp_at, lamp_tilt=lamp_tilt, sheet=sheet, street=street,
                             police=police, door_open=door_open, hall=hall, door_mask=door_mask,
                             flashlights=flashlights, sheet_glow=sheet_glow if behind else None)
        lights += list(extra_lights)
        z0, z1 = self.DOOR_Z
        holes = [("back",) + tuple(self.WINDOW), ("left", z0, 0.0, z1, self.DOOR_H)]
        self.room.light_map(f, lights, par=par, ambient=0.012, holes=holes)
        if "after_room" in hooks:
            hooks["after_room"](f, t)
        # 2) behind the sheet (the trap: lamp + doll on its rod between sheet and window)
        with opened(f, spec) as L:
            if behind and lamp_stand:
                self._draw_lamp(f, t, L, lamp_at, lv, lamp_tilt, lamp_broken, spec, emit=not sheet)
            # 3) the sheet with its shadows
            if sheet:
                self.draw_sheet(f, t, L, lamp=lv, lamp_at=lamp_at, lamp_tilt=lamp_tilt, casters=casters,
                                caster_z=caster_z, puppets=puppets, rig=rig, crank=crank, tears=tears, hit=sheet_hit,
                                fall=sheet_fall)
        if sheet and lv > 0:
            self.sheet.light(f, t, self.bulb(lamp_at, lamp_tilt), level=lv * (1.0 if behind else 0.6), par=par,
                             back=behind)
        if "after_sheet" in hooks:
            hooks["after_sheet"](f, t)
        # 4) table, rig, puppets, lamp in front, blood
        with opened(f, spec) as L:
            for b in blood:
                self._blood(L, *b)
            if table:
                self.draw_table(L)
            if rig and table:
                self.draw_rig(L, crank)
            if puppets is not None and table:
                puppets(L, self)
            if not behind and lamp_stand:
                self._draw_lamp(f, t, L, lamp_at, lv, lamp_tilt, lamp_broken, spec)
        if "after_props" in hooks:
            hooks["after_props"](f, t)
        # 5) the door
        with opened(f, spec) as L:
            self.door.draw(f, t, L, open=door_open, hall=hall, locked=locked, key=False, feet=feet)
        self.door.light(f, t, open=door_open, hall=hall, par=par, spill=0.0, feet=feet)
        if "after_door" in hooks:
            hooks["after_door"](f, t)
        # 6) air: lamp halo, torch beams, dust
        self.draw_air(f, t, lamp=lv, lamp_at=lamp_at, lamp_tilt=lamp_tilt, flashlights=flashlights, par=par,
                      sheet=sheet, dust=dust)

    def draw_window(self, f, t, L, outside=None, street=0.35, police=0.0):
        r = self.room
        X0, Y0, X1, Y1 = self.WINDOW
        zb = r.zb
        glass = [r.P(X0, Y0, zb), r.P(X1, Y0, zb), r.P(X1, Y1, zb), r.P(X0, Y1, zb)]
        xs = [p[0] for p in glass]
        ys = [p[1] for p in glass]
        rect = (min(xs), min(ys), max(xs), max(ys))
        L.save()
        draw.poly(L, glass)
        L.clip()
        if outside is not None:
            outside(L, rect)
        else:
            # night over the street: her building's windows far off, rain-blurred
            draw.linear(L, (0, rect[1]), (0, rect[3]), [(0, mix(PAL.sky_bottom, PAL.fog_at(1.0), 0.5), 1),
                                                        (1, mix(INK, PAL.fog_at(0.6), 0.5), 1)])
            L.paint()
            for k in range(14):
                u, v = hash01(5, k, 1), hash01(5, k, 2)
                if hash01(5, k, 3) < 0.4:
                    x = lerp(rect[0], rect[2], u)
                    y = lerp(rect[1], rect[3], 0.15 + 0.8 * v)
                    ww = (rect[2] - rect[0]) * 0.06
                    draw.rect(L, x, y, x + ww, y + ww * 1.5)
                    draw.fill(L, mix(INK, AMBER, 0.55))
        if police > 0:
            b, rr = siren(t, rate=1.6)
            draw.linear(L, (0, rect[3]), (0, rect[1]), [(0, BLUE, 0.6 * b * police), (1, BLUE, 0.0)])
            L.paint()
            draw.linear(L, (0, rect[3]), (0, rect[1]), [(0, RED, 0.5 * rr * police), (1, RED, 0.0)])
            L.paint()
        L.restore()
        # sash frame and mullions (ink)
        ym = (Y0 + Y1) / 2
        fw = 0.045
        bars = [(X0, Y0, X1, Y0 + fw), (X0, Y1 - fw, X1, Y1), (X0, Y0, X0 + fw, Y1), (X1 - fw, Y0, X1, Y1),
                (X0, ym - 0.035, X1, ym + 0.035), (-0.03, Y0, 0.03, Y1)]
        for (a, b, c, d) in bars:
            draw.poly(L, [r.P(a, b, zb), r.P(c, b, zb), r.P(c, d, zb), r.P(a, d, zb)])
        # sill
        draw.poly(L, [r.P(X0 - 0.08, Y0 - 0.05, zb - 0.12), r.P(X1 + 0.08, Y0 - 0.05, zb - 0.12),
                      r.P(X1 + 0.08, Y0, zb), r.P(X0 - 0.08, Y0, zb)])
        draw.fill(L, INK)

    def window_rect(self):
        r = self.room
        X0, Y0, X1, Y1 = self.WINDOW
        a = r.P(X0, Y1, r.zb)
        b = r.P(X1, Y0, r.zb)
        return (a[0], a[1], b[0], b[1])

    def _shadow_casters(self, puppets, rig, crank):
        def fn(c):
            if rig:
                self.draw_rig(c, crank, rods_only=True)
            if puppets is not None:
                puppets(c, self)
        return fn

    def draw_sheet(self, f, t, L, lamp=0.0, lamp_at="front", lamp_tilt=0.0, casters=None, caster_z=None,
                   puppets=None, rig=True, crank=0.0, tears=(), hit=None, fall=0.0):
        behind = self.lamp_pos(lamp_at)[1] > self.SHEET_Z
        bulb = self.bulb(lamp_at, lamp_tilt)
        # hot spot: where the lamp's axis meets the sheet
        lx, ly, lz = self.bulb3d(lamp_at, lamp_tilt)
        hot = self.room.P(lx, ly, self.SHEET_Z)
        self.sheet.draw(f, t, L, light=hot, level=lamp, back=behind, tears=tears, hit=hit, fall=fall,
                        base=mix(INK, PAL.fog_at(1.0), 0.42))
        if lamp > 0.02:
            if casters is None:
                casters = self._shadow_casters(puppets, rig, crank)
                cz = self.TABLE[1]
            else:
                cz = caster_z if caster_z is not None else self.TABLE[1]
            center, mag, soft = self.shadow_map(cz, (lx, ly, lz))
            self.sheet.shadow(L, t, casters, lamp=center, mag=mag, soft=max(1.0, soft), density=0.9 * min(1.0, lamp),
                              hit=hit, fall=fall)

    def draw_table(self, L):
        r = self.room
        X, Z, w, d, h = self.TABLE
        P = r.P
        top = [P(X - w / 2, h, Z - d / 2), P(X + w / 2, h, Z - d / 2), P(X + w / 2, h, Z + d / 2), P(X - w / 2, h, Z + d / 2)]
        draw.poly(L, top)
        draw.poly(L, [P(X - w / 2, h, Z - d / 2), P(X + w / 2, h, Z - d / 2), P(X + w / 2, h - 0.05, Z - d / 2),
                      P(X - w / 2, h - 0.05, Z - d / 2)])
        for (lx, lz) in ((X - w / 2 + 0.05, Z - d / 2 + 0.05), (X + w / 2 - 0.05, Z - d / 2 + 0.05),
                         (X - w / 2 + 0.05, Z + d / 2 - 0.05), (X + w / 2 - 0.05, Z + d / 2 - 0.05)):
            a = P(lx - 0.025, h, lz)
            b = P(lx + 0.025, 0, lz)
            draw.rect(L, a[0], a[1], b[0], b[1])
        # the timer on the wall socket by the table leg, cord to the lamp
        draw.fill(L, INK)

    def draw_rig(self, L, crank=0.0, rods_only=False):
        """The puppet rig on the table: a wooden block, two rods (man, woman), a crank wheel
        with a clockwork motor and the wire that works the man's knife arm."""
        r = self.room
        P = r.P
        X, Z, w, d, h = self.TABLE
        if not rods_only:
            # base block
            draw.poly(L, [P(X - 0.30, h, Z - 0.08), P(X + 0.34, h, Z - 0.08), P(X + 0.34, h + 0.07, Z - 0.08),
                          P(X - 0.30, h + 0.07, Z - 0.08)])
        for who, (rx, ry) in self.RODS.items():
            a = P(X + rx - 0.008, h + 0.07, Z)
            b = P(X + rx + 0.008, ry, Z)
            draw.rect(L, a[0], b[1], b[0], a[1])
            c = P(X + rx, h + 0.11, Z)
            k = r.ppm(Z)
            draw.rect(L, c[0] - 0.03 * k, c[1] - 0.02 * k, c[0] + 0.03 * k, c[1] + 0.03 * k)     # clamp
        # crank wheel with spokes (a hole you see light through), motor box, wire to the arm
        cx, cy, cz = self._crank_center()
        cc = P(cx, cy, cz)
        k = r.ppm(cz)
        R = 0.085 * k
        if not rods_only:
            L.new_sub_path()
            L.arc(cc[0], cc[1], R, 0, 2 * math.pi)
            L.new_sub_path()
            L.arc_negative(cc[0], cc[1], R * 0.78, 2 * math.pi, 0)
            for sp in range(4):
                a = math.radians(crank + sp * 90)
                draw.capsule(L, cc, (cc[0] + R * 0.8 * math.cos(a), cc[1] - R * 0.8 * math.sin(a)), 0.006 * k, 0.006 * k)
            draw.circle(L, cc, 0.014 * k)
            mb = P(cx - 0.06, h, cz)
            draw.rect(L, mb[0] - 0.09 * k, mb[1] - 0.12 * k, mb[0] + 0.05 * k, mb[1])
            # winding key on the motor box
            kc = (mb[0] - 0.02 * k, mb[1] - 0.12 * k)
            draw.rect(L, kc[0] - 0.004 * k, kc[1] - 0.04 * k, kc[0] + 0.004 * k, kc[1])
            draw.ellipse(L, (kc[0], kc[1] - 0.05 * k), 0.025 * k, 0.012 * k)
            draw.capsule(L, cc, P(cx, h + 0.07, cz), 0.01 * k, 0.012 * k)
        # the wire from the wheel rim up to the man's arm
        rim = self.crank_point(crank)
        tip = self.arm_wire_end(crank)
        draw.capsule(L, rim, tip, 0.0035 * k, 0.0035 * k)
        draw.fill(L, INK)

    def arm_wire_end(self, crank):
        """World point where the wire reaches the man's arm (the director's puppet should
        pin its knife arm here). Moves up and down with the crank."""
        X, Z = self.TABLE[0] + self.RODS["man"][0], self.TABLE[1]
        a = math.radians(crank)
        return self.room.P(X + 0.12, 1.30 + 0.07 * math.sin(a), Z)

    def _draw_lamp(self, f, t, L, lamp_at, lv, tilt, broken, spec, emit=True):
        r = self.room
        X, Z = self.lamp_pos(lamp_at)
        k = r.ppm(Z) * self.BULB_Y / 520.0
        lampo = BareLamp(r.P(X, 0, Z), height=520.0, scale=k)
        sock = r.P(-r.hw + 0.02, 0.32, Z + 0.4)
        # stand + bulb glass on L; light only if requested (behind the sheet it shows as glow)
        lampo.draw(f, t, L, on=lv if emit else 0.0, tilt=tilt, broken=broken, cord_to=(sock[0], r.P(X, 0, Z)[1]))
        if not emit and lv > 0:
            lamp_light(f, lampo.bulb(tilt), lv * 0.35, scale=k, par=spec["par"])

    def _blood(self, L, X, Y, Z, scale=1.0, seed=0, grow=1.0):
        p = self.room.P(X, Y, Z)
        k = self.room.ppm(Z) / PX_M
        L.save()
        L.translate(p[0], p[1])
        L.scale(1.0, 0.35 if Y < 0.05 or abs(Y - self.TABLE[4]) < 0.03 else 1.0)
        paper_blood(L, (0, 0), scale * k * 0.5, seed=seed, grow=grow)
        L.restore()

    def draw_air(self, f, t, lamp=0.0, lamp_at="front", lamp_tilt=0.0, flashlights=(), par=1.0, sheet=True, dust=1.0):
        r = self.room
        for i, fl in enumerate(flashlights):
            X, Y, Z = fl["pos"]
            dx, dy, dz = fl["dir"]
            n = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
            dist = fl.get("reach", 3.0)
            end = (X + dx / n * dist, Y + dy / n * dist, Z + dz / n * dist)
            o = r.P(X, Y, Z)
            e = r.P(*end)
            ang = math.degrees(math.atan2(e[1] - o[1], e[0] - o[0]))
            length = math.hypot(e[0] - o[0], e[1] - o[1])
            flashlight_beam(f, o, ang, length=length, spread=fl.get("cone", 9.0) * 0.8, level=fl.get("power", 2.4) / 2.4,
                            par=par, hit=False, t=t, dust=dust, scale=r.ppm(Z) / PX_M, seed=i)


# =========================================================================== her room
class HerRoom:
    """Her room seen from inside, looking out through her window (S02 reveal, S12). An
    elevation of the window wall in the action-plane scale (1 m = 343 px at scale 1). Draw the
    world outside (sky, facade, rain) FIRST: the wall is drawn with the glass left open.

    HerRoom(origin=(540, 1800), scale=1.0)   origin = floor point under the window centre
      .glass           world rect of the glass (1.5 x 1.9 m, the facade windows' 4:5)
      .sill_y          world y of the sill top        .floor_y   the floor
      .binocular_rest  her binoculars' grip point, standing on their objectives on the sill
      .chair_seat      a point on the armchair seat (her hips when she sits watching)
      .lamp_bulb       the floor lamp's bulb          .curtain_edge(close, gap)  leading edge x
    draw(f, t, layer=None, curtain=0.0, gap=0.0, gap_at=0.55, rain=1.0, binoculars=True,
         plant=True, mug=True, radiator=True, lamp=0.0, chair=True, outside_light=1.0,
         condensation=1.0, room_light=0.0, wipe=None)
      condensation  0..1 the steamed lower pane (blurs and lifts what is behind it)
      wipe     (u, v, r) a patch she wiped clear (glass fractions, r in px at scale 1)
      curtain  0 = open (gathered right of the window) .. 1 = drawn across the glass (S12)
      gap      0..1 a crack held open in the drawn curtain at gap_at (fraction of the glass
               width from the left): her fingers part it (S12 "Mostly.")
      lamp     her floor lamp (S08 seen from outside it is on; inside she keeps it off)
      room_light  a warm fill on the wall from a light behind the camera
    draw_chair(f, t, layer) the armchair alone (a blurred foreground occluder for dollies)."""

    def __init__(self, origin=(540.0, 1800.0), scale=1.0):
        self.o = (float(origin[0]), float(origin[1]))
        self.s = s = float(scale)
        ox, oy = self.o
        self.floor_y = oy
        self.glass = (ox - 257 * s, oy - 858 * s, ox + 257 * s, oy - 206 * s)
        self.sill_y = oy - 206 * s
        self.binocular_rest = (ox + 120 * s, self.sill_y - 33 * s)     # grip point, standing on the sill
        self.chair_seat = (ox - 400 * s, oy - 154 * s)
        self.lamp_bulb = (ox + 500 * s, oy - 500 * s)
        self.rod_y = self.glass[1] - 80 * s

    # ------------------------------------------------------------------ geometry
    def curtain_edge(self, close=0.0):
        """World x of the drawn curtain's leading edge (it slides from the right)."""
        x0, y0, x1, y1 = self.glass
        return lerp(x1 + 30 * self.s, x0 - 30 * self.s, clamp(close))

    def _wall(self, c):
        s = self.s
        ox, oy = self.o
        x0, y0, x1, y1 = self.glass
        draw.rect(c, ox - 4000 * s, oy - 4000 * s, ox + 4000 * s, oy + 2000 * s)
        draw.rect(c, x0, y0, x1, y1)

    # ------------------------------------------------------------------ drawing
    def draw(self, f, t, layer=None, curtain=0.0, gap=0.0, gap_at=0.55, rain=1.0, binoculars=True, plant=True,
             mug=True, radiator=True, lamp=0.0, chair=True, outside_light=1.0, condensation=1.0, room_light=0.0,
             dressing="hers", wipe=None):
        spec = layer_spec(layer)
        par = spec["par"]
        s = self.s
        ox, oy = self.o
        x0, y0, x1, y1 = self.glass
        gw, gh = x1 - x0, y1 - y0
        hers = dressing == "hers"
        # glass: condensation creeping up from the bottom (it blurs the street behind it and
        # catches its light, so whatever stands on the sill reads against it), drops of rain
        self._frost(f, par, condensation, wipe)
        if rain > 0:
            self._rain_on_glass(f, t, par, rain)
        cover = clamp(curtain) if hers else 0.0
        occlude_emit(f, par, self._wall, even_odd=True)
        with opened(f, spec) as L:
            L.new_path()
            self._wall(L)
            L.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            base = 0.05 if hers else 0.09
            warm = mix(AMBER, PAL.fog_at(1.0), 0.55)
            wall = mix(INK, warm, base + 0.25 * lamp)
            if room_light > 0:
                # a light behind the camera, low and to the left: the wall falls off upward
                draw.radial(L, (ox - 260 * s, oy + 120 * s), 0, 1500 * s,
                            [(0, mix(INK, warm, base + 0.42 * room_light), 1), (0.55, mix(INK, warm, base + 0.2 * room_light), 1),
                             (1, wall, 1)])
                L.fill()
            else:
                draw.fill(L, wall)
            L.set_fill_rule(cairo.FILL_RULE_WINDING)
            if not hers:
                # apartment 9: bare plaster with damp stains, a nail and the sheet's wire
                self._stains(L)
            self._sash(L)
            self._sill(L)
            if radiator:
                self._radiator(L)
            rim = (mix(PAL.fog_at(1.0), PAL.rain, 0.35), 0.5 * outside_light * (1.0 - 0.9 * cover))
            if hers and plant:
                self._rimmed(L, lambda c: self._plant(c, t), rim)
            if hers and mug:
                self._rimmed(L, self._mug, rim)
            if hers and binoculars:
                bx, by = self.binocular_rest
                self._rimmed(L, lambda c: draw_binoculars(c, (bx, by), angle=90.0, scale=s * 1.05, view="pair"), rim)
            if hers:
                self._lamp(L, lamp)
                self._curtain(L, t, cover, gap, gap_at)
                if cover > 0.01:
                    x_edge = self.curtain_edge(cover)
                    occlude_emit(f, par, lambda c: c.rectangle(x_edge, self.rod_y, x1 + 200 * s - x_edge,
                                                               oy - self.rod_y))
                if chair:
                    self._chair(L)
            else:
                # the sheet's wire, strung wall to wall in front of the window top
                draw.capsule(L, (x0 - 600 * s, y0 - 46 * s), (x1 + 600 * s, y0 - 40 * s), 1.4 * s, 1.4 * s)
                draw.fill(L, INK)
        # light from outside: sill, reveal, the pale patch on the floor (less as she closes it)
        k = outside_light * (1.0 - 0.92 * cover)
        with f.light(par=par, blur=4.0) as A:
            if k > 0.01:
                A.rectangle(x0 - 50 * s, self.sill_y - 2 * s, gw + 100 * s, 4 * s)
                draw.fill(A, PAL.fog_at(1.0), 0.8 * k)
                # the wet-looking sill top under the glass and the bottom rail's glint
                draw.linear(A, (0, self.sill_y - 1 * s), (0, self.sill_y + 18 * s), [(0, PAL.fog_at(1.0), 0.45 * k),
                                                                                     (1, PAL.fog_at(1.0), 0.0)])
                A.rectangle(x0 - 40 * s, self.sill_y - 1 * s, gw + 80 * s, 19 * s)
                A.fill()
                # the casing catches the light round the glass
                cw = 36 * s
                for (p0, p1, rc) in (((x0, 0), (x0 - cw, 0), (x0 - cw, y0 - cw, cw, gh + cw)),
                                     ((x1, 0), (x1 + cw, 0), (x1, y0 - cw, cw, gh + cw)),
                                     ((0, y0), (0, y0 - cw), (x0 - cw, y0 - cw, gw + 2 * cw, cw))):
                    draw.linear(A, p0, p1, [(0, PAL.fog_at(1.0), 0.20 * k), (1, PAL.fog_at(1.0), 0.0)])
                    A.rectangle(*rc)
                    A.fill()
                if radiator:
                    # the radiator's top catches the window light
                    rt = oy - 176 * s
                    A.save()
                    A.new_path()
                    self._radiator(A, fill=False)
                    A.clip()
                    draw.linear(A, (0, rt), (0, rt + 40 * s), [(0, PAL.fog_at(1.0), 0.32 * k), (1, PAL.fog_at(1.0), 0.0)])
                    A.rectangle(ox - 240 * s, rt, 480 * s, 40 * s)
                    A.fill()
                    A.restore()
                glow_ellipse(A, ((x0 + x1) / 2, self.sill_y + 10 * s), gw * 0.8, 40 * s, PAL.fog_at(1.0), 0.25 * k)
                # light bounced off the sill and the floor onto the wall round the window
                glow_ellipse(A, ((x0 + x1) / 2, (y0 + y1) / 2 + gh * 0.2), gw * 1.25, gh * 0.95, PAL.fog_at(1.0), 0.07 * k)
                # the window's four panes thrown on the floor (foreshortened, the mullions dark)
                d0, d1 = oy + 26 * s, oy + 210 * s
                draw.linear(A, (0, d0), (0, d1), [(0, PAL.fog_at(1.0), 0.42 * k), (1, PAL.fog_at(1.0), 0.05 * k)])
                xm = (x0 + x1) / 2
                for (ua, ub) in ((0.0, 0.48), (0.52, 1.0)):
                    for (va, vb) in ((0.0, 0.46), (0.54, 1.0)):
                        ya, yb = lerp(d0, d1, va), lerp(d0, d1, vb)
                        wa, wb = 1.0 + 0.5 * va, 1.0 + 0.5 * vb
                        draw.poly(A, [(xm + (lerp(x0, x1, ua) - xm) * wa, ya), (xm + (lerp(x0, x1, ub) - xm) * wa, ya),
                                      (xm + (lerp(x0, x1, ub) - xm) * wb, yb), (xm + (lerp(x0, x1, ua) - xm) * wb, yb)])
                A.fill()
            if hers and cover < 0.98:
                # rim light down the curtain's leading edge
                ex = self.curtain_edge(cover)
                draw.linear(A, (ex - 14 * s, 0), (ex + 6 * s, 0), [(0, PAL.fog_at(1.0), 0.0), (0.7, PAL.fog_at(1.0), 0.5 * outside_light),
                                                                   (1, PAL.fog_at(1.0), 0.0)])
                A.rectangle(ex - 14 * s, self.rod_y, 20 * s, oy - self.rod_y)
                A.fill()
            if hers and gap > 0.01 and cover > 0.3:
                gx = lerp(x0, x1, gap_at)
                gwid = 26 * s * gap
                draw.linear(A, (gx - gwid, 0), (gx + gwid, 0), [(0, PAL.fog_at(1.0), 0), (0.5, PAL.fog_at(1.0), 0.75 * outside_light),
                                                                (1, PAL.fog_at(1.0), 0)])
                A.rectangle(gx - gwid, self.rod_y + 10 * s, 2 * gwid, oy - self.rod_y - 10 * s)
                A.fill()
                glow_ellipse(A, (gx, oy + 30 * s), 90 * s * gap, 20 * s, PAL.fog_at(1.0), 0.3 * outside_light)
            if room_light > 0:
                glow(A, (ox - 260 * s, oy + 200 * s), 900 * s, AMBER, 0.06 * room_light)
        if lamp > 0.01 and hers:
            lamp_light(f, self.lamp_bulb, lamp, scale=s * 1.2, par=par, radius=1200)

    def draw_chair(self, f, t, layer=None, at=None, rim=0.0):
        """The armchair alone (at=(x, floor_y) to move it), e.g. as a blurred foreground;
        rim = window light along its top edges."""
        with opened(f, layer) as L:
            self._rimmed(L, lambda c: self._chair(c, at), (PAL.fog_at(1.0), rim), clip=False, d=3.0 * self.s)

    def _rimmed(self, L, fn, rim, clip=True, d=None):
        """Draw fn's ink silhouette with a hairline of window light on its top edges (the
        light comes from behind it, through the glass)."""
        col, a = rim
        if a <= 0.01:
            fn(L)
            return
        L.push_group()
        fn(L)
        pat = L.pop_group()
        x0, y0, x1, y1 = self.glass
        d = 1.3 * max(self.s, 0.5) if d is None else d
        L.save()
        if clip:
            L.rectangle(x0 - 6 * self.s, y0, x1 - x0 + 12 * self.s, y1 - y0 + 4 * self.s)     # only against the glass
            L.clip()
        L.translate(0, -d)
        draw.rgba(L, col, a)
        L.mask(pat)
        L.restore()
        L.set_source(pat)
        L.paint()

    def _mug(self, L):
        s = self.s
        ox, oy = self.o
        mx, my = ox + 205 * s, self.sill_y
        draw.poly(L, [(mx - 15 * s, my - 34 * s), (mx + 15 * s, my - 34 * s), (mx + 13 * s, my), (mx - 13 * s, my)])
        L.new_sub_path()
        L.arc(mx + 18 * s, my - 18 * s, 9 * s, -math.pi / 2, math.pi / 2)
        L.arc_negative(mx + 18 * s, my - 18 * s, 4.5 * s, math.pi / 2, -math.pi / 2)
        L.close_path()
        draw.fill(L, INK)

    # ------------------------------------------------------------------ pieces
    def _sash(self, L):
        s = self.s
        x0, y0, x1, y1 = self.glass
        cx = (x0 + x1) / 2
        ym = y0 + (y1 - y0) * 0.5
        cw = 36 * s
        draw.rect(L, x0 - cw, y0 - cw, x1 + cw, y0)
        draw.rect(L, x0 - cw, y0, x0, y1)
        draw.rect(L, x1, y0, x1 + cw, y1)
        draw.rect(L, x0 - cw - 10 * s, y0 - cw - 14 * s, x1 + cw + 10 * s, y0 - cw)
        bars = [(x0, y0, x1, y0 + 16 * s), (x0, y1 - 18 * s, x1, y1), (x0, y0, x0 + 16 * s, y1), (x1 - 16 * s, y0, x1, y1),
                (x0, ym - 13 * s, x1, ym + 13 * s), (cx - 6 * s, y0, cx + 6 * s, y1)]
        for b in bars:
            draw.rect(L, *b)
        draw.ellipse(L, (cx, ym - 14 * s), 14 * s, 6 * s)       # sash lock on the meeting rail
        draw.fill(L, INK)

    def _curtain(self, L, t, close, gap, gap_at):
        """A heavy drape on a rod with ball finials. Open it gathers right of the window;
        drawn, it covers the glass; `gap` holds a crack open at gap_at."""
        s = self.s
        x0, y0, x1, y1 = self.glass
        ox, oy = self.o
        ry = self.rod_y
        draw.capsule(L, (x0 - 200 * s, ry), (x1 + 210 * s, ry), 5 * s, 5 * s)
        for ex in (x0 - 204 * s, x1 + 214 * s):
            draw.circle(L, (ex, ry), 11 * s)
        draw.fill(L, INK)
        right = x1 + 190 * s
        edge = self.curtain_edge(close)
        sw = 8 * s * fbm1(t * 0.35, 21)
        hem = oy - 10 * s
        panels = [(edge, right)]
        if gap > 0.01 and close > 0.3:
            gx = lerp(x0, x1, gap_at)
            gw = 26 * s * gap
            if edge < gx - gw:
                panels = [(edge, gx - gw), (gx + gw, right)]
        for (a, b) in panels:
            pts = [(a, ry + 4 * s), (b, ry + 4 * s), (b + sw * 0.3, hem), (a + sw, hem)]
            draw.poly(L, pts)
            draw.fill(L, INK, 0.94)
            # folds: tone bands, deeper when gathered; the ones nearest the glass catch its light
            n = max(2, int((b - a) / (34 * s)))
            gather = 1.0 - 0.6 * clamp(close)
            for j in range(n):
                fx = a + (b - a) * (j + 0.5) / n
                near = math.exp(-max(0.0, fx - x1) / (160 * s)) if close < 0.5 else 0.5
                ka = (0.06 + 0.16 * near) * gather
                draw.linear(L, (fx - 14 * s, 0), (fx + 14 * s, 0),
                            [(0, PAL.fog_at(1.0), 0.0), (0.6, PAL.fog_at(1.0), ka), (1, PAL.fog_at(1.0), 0.0)])
                L.rectangle(fx - 14 * s, ry + 6 * s, 28 * s, hem - ry - 6 * s)
                L.fill()
        # curtain rings on the rod
        for (a, b) in panels:
            n = max(2, int((b - a) / (30 * s)))
            for j in range(n + 1):
                draw.circle(L, (lerp(a, b, j / n), ry), 7 * s)
        draw.fill(L, INK)

    def _sill(self, L):
        s = self.s
        ox, oy = self.o
        y = self.sill_y
        draw.rect(L, ox - 320 * s, y, ox + 320 * s, y + 20 * s)
        draw.rect(L, ox - 290 * s, y + 20 * s, ox + 290 * s, y + 44 * s)
        draw.fill(L, INK)

    def _radiator(self, L, fill=True):
        s = self.s
        ox, oy = self.o
        top, bot = oy - 176 * s, oy - 30 * s
        x = ox - 200 * s
        while x < ox + 200 * s:
            rrect(L, x, top, x + 20 * s, bot, 9 * s)
            x += 26 * s
        draw.rect(L, ox - 204 * s, bot - 26 * s, ox + 204 * s, bot - 16 * s)
        draw.rect(L, ox - 204 * s, top + 14 * s, ox + 204 * s, top + 24 * s)
        for fx in (ox - 184 * s, ox + 172 * s):
            draw.rect(L, fx, bot, fx + 12 * s, oy)
        draw.rect(L, ox + 204 * s, top + 40 * s, ox + 236 * s, top + 52 * s)
        draw.circle(L, (ox + 236 * s, top + 34 * s), 13 * s)
        if fill:
            draw.fill(L, INK)

    def _plant(self, L, t):
        s = self.s
        x0 = self.glass[0]
        px, py = x0 + 60 * s, self.sill_y
        draw.poly(L, [(px - 44 * s, py - 70 * s), (px + 44 * s, py - 70 * s), (px + 32 * s, py), (px - 32 * s, py)])
        draw.rect(L, px - 50 * s, py - 80 * s, px + 50 * s, py - 66 * s)
        sw = 3 * s * math.sin(t * 0.7)
        leaves = [(-70, -250, -30), (-20, -310, -8), (40, -270, 25), (75, -190, 50), (-95, -170, -60),
                  (10, -200, 5), (-45, -150, -35), (60, -130, 70)]
        for (lx, ly, ang) in leaves:
            tip = (px + lx * s + sw, py + ly * s)
            base = (px + lx * 0.15 * s, py - 75 * s)
            draw.capsule(L, base, tip, 2.4 * s, 1.6 * s)
            a = math.radians(ang - 90)
            ca, sa = math.cos(a), math.sin(a)
            leaf = []
            for (u, v) in ((0, 0), (14, 20), (34, 18), (56, 0), (34, -18), (14, -20)):
                leaf.append((tip[0] + (u * ca - v * sa) * s * 0.9, tip[1] + (u * sa + v * ca) * s * 0.9))
            draw.smooth(L, leaf, close=True, tension=0.45)
        draw.fill(L, INK)

    def _lamp(self, L, lamp):
        """Floor lamp with a drum shade (1.6 m), right of the window."""
        s = self.s
        ox, oy = self.o
        lx = self.lamp_bulb[0]
        draw.ellipse(L, (lx, oy - 6 * s), 62 * s, 11 * s)
        draw.rect(L, lx - 5 * s, oy - 470 * s, lx + 5 * s, oy - 6 * s)
        draw.fill(L, INK)
        shade = [(lx - 88 * s, oy - 463 * s), (lx + 88 * s, oy - 463 * s), (lx + 66 * s, oy - 549 * s), (lx - 66 * s, oy - 549 * s)]
        draw.poly(L, shade)
        if lamp > 0.01:
            draw.linear(L, (0, oy - 549 * s), (0, oy - 463 * s), [(0, mix(INK, AMBER, 0.65 * lamp), 1),
                                                                   (1, mix(INK, HOT, 0.9 * lamp), 1)])
            L.fill()
        else:
            draw.fill(L, INK)

    def _chair(self, L, at=None):
        """Wingback armchair seen from behind, facing the window (1.05 m back)."""
        s = self.s
        cx, cy = self.chair_seat
        ox, oy = self.o
        if at is not None:
            cx, oy = at
        top = oy - 360 * s
        back = [(cx - 150 * s, oy - 10 * s), (cx - 166 * s, oy - 130 * s), (cx - 184 * s, oy - 250 * s),
                (cx - 170 * s, top + 30 * s), (cx - 110 * s, top + 8 * s), (cx - 40 * s, top),
                (cx + 40 * s, top), (cx + 110 * s, top + 8 * s), (cx + 170 * s, top + 30 * s),
                (cx + 184 * s, oy - 250 * s), (cx + 166 * s, oy - 130 * s), (cx + 150 * s, oy - 10 * s)]
        draw.smooth(L, back, close=True, tension=0.28)
        for fx in (cx - 140 * s, cx + 128 * s):
            draw.rect(L, fx, oy - 30 * s, fx + 14 * s, oy)
        draw.fill(L, INK)

    def _stains(self, L):
        """Apartment 9's wall: damp stains and a pale rectangle where a picture hung."""
        s = self.s
        ox, oy = self.o
        x0, y0, x1, y1 = self.glass
        draw.rect(L, x1 + 160 * s, y0 + 40 * s, x1 + 330 * s, y0 + 250 * s)
        draw.fill(L, PAL.fog_at(1.0), 0.06)
        draw.circle(L, (x1 + 245 * s, y0 + 30 * s), 4 * s)                   # the nail
        draw.fill(L, INK)
        for k in range(5):
            cx = x0 - 300 * s + 700 * s * hash01(41, k, 1)
            draw.ellipse(L, (cx, y0 - 120 * s + 80 * s * hash01(41, k, 2)), (40 + 90 * hash01(41, k, 3)) * s,
                         (60 + 160 * hash01(41, k, 4)) * s)
            draw.fill(L, INK, 0.10)

    def _frost(self, f, par, amount, wipe=None):
        """Steamed lower pane: blur what is already drawn behind the glass's lower part and
        lift it a little; the top edge is ragged and climbs into the corners. wipe=(u, v, r)
        keeps a smeared patch clear (she wiped it to watch)."""
        if amount <= 0.01:
            return
        s = self.s
        x0, y0, x1, y1 = self.glass
        gw, gh = x1 - x0, y1 - y0
        M = f.lcam(par).matrix(f.scale)
        top = y1 - gh * 0.46
        corners = [M.transform_point(x, y) for (x, y) in ((x0, top), (x1, top), (x1, y1), (x0, y1))]
        sig = max(1.0, 13.0 * s * abs(M.xx))
        pad = int(3 * sig) + 2
        bx0 = max(0, int(min(p[0] for p in corners)) - pad)
        bx1 = min(f.pw, int(max(p[0] for p in corners)) + pad + 1)
        by0 = max(0, int(min(p[1] for p in corners)) - pad)
        by1 = min(f.ph, int(max(p[1] for p in corners)) + pad + 1)
        if bx1 - bx0 < 4 or by1 - by0 < 4:
            return
        w, h = bx1 - bx0, by1 - by0
        ms = cairo.ImageSurface(cairo.FORMAT_A8, w, h)
        mc = cairo.Context(ms)
        mc.translate(-bx0, -by0)
        mc.transform(M)
        mc.rectangle(x0, y0, gw, gh)
        mc.clip()
        # ragged edge, higher in the corners; density grows toward the bottom rail
        n = 48
        pts = []
        for j in range(n + 1):
            u = j / n
            corner = (abs(u - 0.5) * 2) ** 3
            y = top + gh * (0.12 - 0.16 * corner + 0.05 * (fbm1(u * 9.0, 61) - 0.5))
            pts.append((lerp(x0, x1, u), y))
        pts += [(x1, y1 + 4 * s), (x0, y1 + 4 * s)]
        draw.poly(mc, pts)
        g = cairo.LinearGradient(0, top - gh * 0.04, 0, y1)
        g.add_color_stop_rgba(0.0, 0, 0, 0, 0.0)
        g.add_color_stop_rgba(0.30, 0, 0, 0, 0.55 * amount)
        g.add_color_stop_rgba(1.0, 0, 0, 0, min(1.0, 1.0 * amount))
        mc.set_source(g)
        mc.fill()
        if wipe:
            u, v, r = wipe
            cx, cy = lerp(x0, x1, u), lerp(y0, y1, v)
            r *= s
            mc.set_operator(cairo.OPERATOR_DEST_OUT)
            for j in range(9):                     # a few overlapping hand strokes
                a = (j - 4) * 0.11
                ex = cx + r * 0.9 * math.sin(a * 3.0)
                ey = cy + r * 0.12 * (j - 4) * 0.5
                rg = cairo.RadialGradient(ex, ey, r * 0.25, ex, ey, r * (0.75 + 0.1 * hash01(62, j)))
                rg.add_color_stop_rgba(0, 0, 0, 0, 0.32)
                rg.add_color_stop_rgba(1, 0, 0, 0, 0.0)
                mc.set_source(rg)
                mc.arc(ex, ey, r, 0, 2 * math.pi)
                mc.fill()
        ms.flush()
        stride = ms.get_stride()
        mask = np.ndarray((h, stride), dtype=np.uint8, buffer=ms.get_data())[:, :w].astype(np.float32) / 255.0
        region = surf_array(f.surf)[by0:by1, bx0:bx1]
        # blur at 1/d resolution (it is a soft blur anyway): ~10x cheaper than full res
        d = max(1, int(sig / 4.0))
        sw_, sh_ = max(2, w // d), max(2, h // d)
        small = cv2.resize(region, (sw_, sh_), interpolation=cv2.INTER_AREA)
        bl = cv2.resize(cv2.GaussianBlur(small, (0, 0), sig / d), (w, h), interpolation=cv2.INTER_LINEAR)
        msk = cv2.resize(cv2.GaussianBlur(cv2.resize(mask, (sw_, sh_), interpolation=cv2.INTER_AREA), (0, 0),
                                          sig * 1.2 / d), (w, h), interpolation=cv2.INTER_LINEAR)
        mm = np.minimum(1.0, msk * 1.6)
        out = cv2.blendLinear(region, bl, 1.0 - mm, mm)
        fc = PAL.fog_at(1.0)
        lift = (msk * (0.55 * 255.0))[..., None] * np.array([fc[2], fc[1], fc[0], 0.0], np.float32)
        region[...] = cv2.add(out, lift.astype(np.uint8))
        f.surf.mark_dirty()

    def _rain_on_glass(self, f, t, par, k):
        """Drops beading on the pane and a few running down (catching the outside light)."""
        s = self.s
        x0, y0, x1, y1 = self.glass
        gw, gh = x1 - x0, y1 - y0
        with f.light(par=par, blur=1.2) as A:
            n = 110
            for j in range(n):
                u, v = hash01(77, j, 1), hash01(77, j, 2)
                x = x0 + u * gw
                y = y0 + v * gh
                r = (1.6 + 3.8 * hash01(77, j, 3) ** 2) * s
                if j % 9 == 0:
                    # stick-slip runners: a few drops slide down in bursts, leaving a trail
                    per = 3.0 + 3.0 * hash01(77, j, 4)
                    ph = (t / per + hash01(77, j, 5)) % 1.0
                    run = (ph ** 3) * gh * 0.8
                    y = y0 + ((v * gh + run) % gh)
                    r *= 1.6
                    draw.capsule(A, (x, max(y0, y - run * 0.6)), (x + 2 * s, y), 0.8 * s, r * 0.5)
                    draw.fill(A, PAL.fog_at(1.0), 0.18 * k)
                draw.circle(A, (x, y), r)
                draw.fill(A, PAL.fog_at(1.0), 0.20 * k)
                draw.circle(A, (x - r * 0.35, y + r * 0.35), r * 0.38)
                draw.fill(A, mix(PAL.rain, HOT, 0.4), 0.55 * k)


class NineWindow(HerRoom):
    """Window 9 seen from inside apartment 9 (S07 end, S08 over her shoulder): the same
    window wall as HerRoom but bare: stained plaster, no curtain, plant or chair, the
    sheet's wire strung across above it. room_light = the show lamp glowing behind her.

    NineWindow(origin, scale).draw(f, t, layer=None, rain=1.0, room_light=0.6, ...)"""

    def draw(self, f, t, layer=None, rain=1.0, room_light=0.6, radiator=True, outside_light=1.0, condensation=0.6,
             **kw):
        HerRoom.draw(self, f, t, layer=layer, rain=rain, radiator=radiator, outside_light=outside_light,
                     condensation=condensation, room_light=room_light, dressing="bare", **kw)


class HerEntry:
    """Her front door from inside (S06 opens here): the door with a transom over it, a row
    of coat hooks with her RED coat, a hat and an umbrella, the light switch; the hallway
    light leaks round the door; cold window light slants across the wall.

    HerEntry(origin=(540, 1800), scale=1.0)    origin = floor point at the door's centre
      .coat_hook   world point where the coat hangs (she takes it from here)
      .switch      world point of the light switch     .door  the Door prop
    draw(f, t, layer=None, coat=True, coat_sway=0.0, door_open=0.0, hall=0.6, window=1.0)"""

    def __init__(self, origin=(540.0, 1800.0), scale=1.0):
        self.o = (float(origin[0]), float(origin[1]))
        self.s = s = float(scale)
        ox, oy = self.o
        self.door = Door((ox - 155 * s, oy), width=310 * s, height=727 * s, swing=1)
        self.coat_hook = (ox - 420 * s, oy - 600 * s)
        self.switch = (ox + 250 * s, oy - 420 * s)
        self.transom = (ox - 155 * s, oy - 727 * s - 150 * s, ox + 155 * s, oy - 727 * s - 40 * s)

    def draw(self, f, t, layer=None, coat=True, coat_sway=0.0, door_open=0.0, hall=0.6, window=1.0):
        spec = layer_spec(layer)
        par = spec["par"]
        s = self.s
        ox, oy = self.o
        tx0, ty0, tx1, ty1 = self.transom
        with opened(f, spec) as L:
            L.rectangle(ox - 3000 * s, oy - 3000 * s, 6000 * s, 3000 * s)
            draw.fill(L, mix(INK, PAL.fog_at(1.0), 0.07))
            L.rectangle(ox - 3000 * s, oy, 6000 * s, 1200 * s)
            draw.fill(L, mix(INK, PAL.fog_at(1.0), 0.03))
            draw.rect(L, ox - 3000 * s, oy - 30 * s, ox + 3000 * s, oy)                 # skirting
            draw.fill(L, INK)
            # transom: hallway light through it
            draw.rect(L, tx0, ty0, tx1, ty1)
            draw.fill(L, mix(INK, mul(AMBER, 0.75), clamp(hall)))
            for k in range(1, 3):
                xx = lerp(tx0, tx1, k / 3)
                draw.rect(L, xx - 3 * s, ty0, xx + 3 * s, ty1)
            draw.rect(L, tx0 - 30 * s, ty0 - 30 * s, tx1 + 30 * s, ty0)
            draw.rect(L, tx0 - 30 * s, ty1, tx1 + 30 * s, ty1 + 14 * s)
            draw.fill(L, INK)
            self.door.draw(f, t, L, open=door_open, hall=hall, locked=0.0)
            # chain lock and peephole
            dx1 = ox + 155 * s
            draw.capsule(L, (dx1 - 30 * s, oy - 470 * s), (dx1 + 34 * s, oy - 452 * s), 2.2 * s, 2.2 * s)
            draw.rect(L, dx1 + 22 * s, oy - 476 * s, dx1 + 40 * s, oy - 440 * s)
            draw.fill(L, INK)
            # coat rack: a board with three hooks
            hx, hy = self.coat_hook
            draw.rect(L, hx - 170 * s, hy - 70 * s, hx + 170 * s, hy - 40 * s)
            draw.fill(L, INK)
            for dxh in (-120, 0, 120):
                coat_hook(L, (hx + dxh * s, hy), s)
            # hat on the left hook, umbrella leaning below the rack
            hp = (hx - 120 * s, hy)
            draw.ellipse(L, (hp[0] + 8 * s, hp[1] + 4 * s), 48 * s, 9 * s)
            draw.smooth(L, [(hp[0] - 26 * s, hp[1] + 2 * s), (hp[0] - 20 * s, hp[1] - 40 * s), (hp[0] + 36 * s, hp[1] - 40 * s),
                            (hp[0] + 42 * s, hp[1] + 2 * s)], close=True, tension=0.3)
            draw.fill(L, INK)
            ub = (hx + 150 * s, oy)
            draw.poly(L, [(ub[0] - 6 * s, ub[1]), (ub[0] + 6 * s, ub[1]), (ub[0] + 46 * s, ub[1] - 560 * s),
                          (ub[0] + 26 * s, ub[1] - 600 * s), (ub[0] + 6 * s, ub[1] - 560 * s)])
            draw.capsule(L, (ub[0] + 26 * s, ub[1] - 600 * s), (ub[0] + 27 * s, ub[1] - 660 * s), 3 * s, 2 * s)
            L.new_sub_path()
            L.arc(ub[0] + 12 * s, ub[1] - 660 * s, 15 * s, math.pi, 2 * math.pi)
            L.arc_negative(ub[0] + 12 * s, ub[1] - 660 * s, 9 * s, 2 * math.pi, math.pi)
            L.close_path()
            draw.fill(L, INK)
            if coat:
                red_coat(L, (hx, hy), s, sway=coat_sway, t=t, hook_too=False)
            # light switch plate
            sx, sy = self.switch
            rrect(L, sx - 22 * s, sy - 36 * s, sx + 22 * s, sy + 36 * s, 5 * s)
            draw.fill(L, mix(INK, PAL.fog_at(1.0), 0.32))
            draw.rect(L, sx - 4 * s, sy - 12 * s, sx + 4 * s, sy + 12 * s)
            draw.fill(L, INK)
        self.door.light(f, t, open=door_open, hall=hall, par=par)
        with f.light(par=par, blur=10.0) as A:
            if hall > 0.01:
                glow(A, ((tx0 + tx1) / 2, (ty0 + ty1) / 2), 380 * s, AMBER, 0.20 * hall)
                glow(A, ((tx0 + tx1) / 2, ty1 + 200 * s), 1100 * s, AMBER, 0.07 * hall)
            if window > 0.01:
                # her window (off to the left) throws a cold slanting pane on the wall
                for (a0, a1) in ((0.0, 0.47), (0.53, 1.0)):
                    xa, xb = ox - 1100 * s + 380 * s * a0, ox - 1100 * s + 380 * s * a1
                    draw.poly(A, [(xa, oy - 1250 * s), (xb, oy - 1250 * s), (xb + 520 * s, oy - 260 * s),
                                  (xa + 520 * s, oy - 260 * s)])
                draw.fill(A, PAL.fog_at(1.0), 0.30 * window)
        with f.emit(par=par) as G:
            if hall > 0.01:
                G.rectangle(tx0, ty0, tx1 - tx0, ty1 - ty0)
                draw.fill(G, AMBER, 0.35 * hall)


def her_room_interior(lamp=1.0, man=None, chair=True):
    """Interior callback for HER window seen from across the street (S08):
        hers = Facade(..., variant='hers')
        hers.draw(f, t, lit={HER_WINDOW: level}, interiors={HER_WINDOW: her_room_interior(man=fn)})
    Draws her floor lamp (shade glowing; left of the window from out here), the armchair
    facing the glass, then man(ctx, win) (the director's figure, in win.person_h scale)."""
    def fn(ctx, win):
        x0, y0, x1, y1 = win.rect
        w, h = x1 - x0, y1 - y0
        k = win.person_h / 1.75                   # world px per metre in that window
        fy = win.floor_y
        if win.mode == "direct":
            lx = x0 + w * 0.18
            draw.rect(ctx, lx - 0.015 * k, fy - 1.37 * k, lx + 0.015 * k, fy)
            draw.fill(ctx, INK)
            shade = [(lx - 0.26 * k, fy - 1.35 * k), (lx + 0.26 * k, fy - 1.35 * k), (lx + 0.19 * k, fy - 1.6 * k),
                     (lx - 0.19 * k, fy - 1.6 * k)]
            draw.poly(ctx, shade)
            draw.fill(ctx, mix(INK, HOT, 0.85 * clamp(win.level * lamp)))
        if chair:
            cx = x0 + w * 0.72
            ch = [(cx - 0.44 * k, fy), (cx - 0.48 * k, fy - 0.45 * k), (cx - 0.54 * k, fy - 0.8 * k), (cx - 0.34 * k, fy - 1.05 * k),
                  (cx + 0.34 * k, fy - 1.05 * k), (cx + 0.54 * k, fy - 0.8 * k), (cx + 0.48 * k, fy - 0.45 * k), (cx + 0.44 * k, fy)]
            draw.smooth(ctx, ch, close=True, tension=0.28)
            draw.fill(ctx, mix(INK, AMBER, 0.10 * clamp(win.level)))
        if man is not None:
            man(ctx, win)
    return fn


# =========================================================================== killer's room
class KillerRoom:
    """His room (S11): forty paper dolls pinned to the wallpaper in a 5 x 8 grid, one for
    every window, laid out exactly on the facade lock (the s01 rhyme); a desk with scissors,
    paper and half-cut dolls below; venetian blinds at the right. Dark: a cop's torch beam
    finds the dolls (everything outside the beam stays black).

    KillerRoom(origin=(540, 965), scale=1.0)   origin = centre of the doll grid. With
      origin (540, 965), scale 1 and Camera(540, 960) (= camera_lock()) every doll centre
      sits on the bible's lock positions (230..850 x 440..1490).
      .center(i)        world centre of doll i's cell (1..40, row-major like the windows)
      .pin(i)           world point of the pin through doll i's head
      .doll_size        (w, h) world px of a doll (the director draws them)
      .camera_lock(par) the lock camera
    draw(f, t, layer=None, dolls=None, beam=None, ambient=0.04, flash=0.0, police=0.0,
         shadows=True, desk=True, blinds=True)
      dolls   fn(ctx, i, center, size, t) draws doll i (PAPER colour; their shadows on the
              wall come for free)
      beam    dict(target=(x, y) world, radius=px, level=1, origin=(x, y) world of the torch,
              cone=True): the pool of torch light that reveals the wall
      flash   0..1 the whole grid lights at once ("On [window] the grid flashes")"""

    COLS, ROWS = 5, 8
    _LOCK_X = (230.0, 385.0, 540.0, 695.0, 850.0)
    _LOCK_Y = (440.0, 590.0, 740.0, 890.0, 1040.0, 1190.0, 1340.0, 1490.0)

    def __init__(self, origin=(540.0, 965.0), scale=1.0):
        self.o = (float(origin[0]), float(origin[1]))
        self.s = s = float(scale)
        self.doll_size = (88.0 * s, 116.0 * s)
        ox, oy = self.o
        self.desk_y = oy + 640 * s
        self.blinds = (ox + 470 * s, oy - 900 * s, ox + 900 * s, oy - 100 * s)

    def center(self, i):
        r, c = (i - 1) // self.COLS, (i - 1) % self.COLS
        return (self.o[0] + (self._LOCK_X[c] - 540.0) * self.s, self.o[1] + (self._LOCK_Y[r] - 965.0) * self.s)

    def pin(self, i):
        cx, cy = self.center(i)
        return (cx, cy - self.doll_size[1] * 0.43)

    def camera_lock(self, par=1.0):
        return camera_for((self.o[0], self.o[1] - 5.0 * self.s), 1.0 / self.s, par)

    def draw(self, f, t, layer=None, dolls=None, beam=None, ambient=0.04, flash=0.0, police=0.0, shadows=True,
             desk=True, blinds=True):
        spec = layer_spec(layer)
        par = spec["par"]
        s = self.s
        ox, oy = self.o
        wall_box = (ox - 3000 * s, oy - 3000 * s, ox + 3000 * s, self.desk_y)
        with opened(f, spec) as L:
            # wallpaper: faded vertical stripes (tone only), damp stains
            L.rectangle(wall_box[0], wall_box[1], wall_box[2] - wall_box[0], wall_box[3] - wall_box[1])
            draw.fill(L, mix(mul(PAPER, 0.42), PAL.fog_at(1.0), 0.35))
            x = wall_box[0]
            while x < wall_box[2]:
                L.rectangle(x, wall_box[1], 34 * s, wall_box[3] - wall_box[1])
                x += 96 * s
            draw.fill(L, INK, 0.12)
            tex = texture_surface("killer_wall", 160, 280, 7.0, 13, (0, 0, 0), 0.0, 0.30, streak=2.5)
            pat = cairo.SurfacePattern(tex)
            pat.set_filter(cairo.FILTER_BILINEAR)
            pat.set_extend(cairo.EXTEND_REPEAT)
            pat.set_matrix(cairo.Matrix(xx=160.0 / (1200 * s), yy=280.0 / (2100 * s), x0=-ox * 160.0 / (1200 * s)))
            L.save()
            L.rectangle(wall_box[0], wall_box[1], wall_box[2] - wall_box[0], wall_box[3] - wall_box[1])
            L.clip()
            L.set_source(pat)
            L.paint()
            L.restore()
            if blinds:
                self._blinds(L)
            # the dolls' shadows (the torch is close: a soft offset copy on the paper)
            if dolls is not None and shadows:
                src = (beam or {}).get("origin") or (ox - 900 * s, oy + 1400 * s)

                def casters(c):
                    for i in range(1, 41):
                        dolls(c, i, self.center(i), self.doll_size, t)
                shadow_screen(L, casters, region=lambda c: c.rectangle(wall_box[0], wall_box[1], wall_box[2] - wall_box[0],
                                                                       wall_box[3] - wall_box[1]),
                              bbox=(ox - 420 * s, oy - 640 * s, ox + 420 * s, oy + 640 * s), soft=3.5 * s, density=0.75,
                              mag=1.025, center=src)
            # pins, then the dolls
            for i in range(1, 41):
                p = self.pin(i)
                draw.circle(L, (p[0] + 1.5 * s, p[1] + 2 * s), 4.0 * s)
                draw.fill(L, INK, 0.5)
            if dolls is not None:
                for i in range(1, 41):
                    dolls(L, i, self.center(i), self.doll_size, t)
            for i in range(1, 41):
                p = self.pin(i)
                draw.circle(L, p, 4.2 * s)
                draw.fill(L, mix(INK, PAL.fog_at(1.0), 0.5))
                draw.circle(L, (p[0] - 1.2 * s, p[1] - 1.2 * s), 1.4 * s)
                draw.fill(L, PAPER, 0.8)
            if desk:
                self._desk(L, t)
        # darkness: everything outside the torch's pool (and any flash) falls to black
        self._light_mask(f, beam, ambient, flash, par)
        with f.light(par=par, blur=6.0) as A:
            if beam:
                tg = beam["target"]
                glow(A, tg, beam.get("radius", 260.0) * 0.6, mix(HOT, (1, 1, 1), 0.2), 0.12 * beam.get("level", 1.0))
            if police > 0:
                self._police_stripes(A, t, police)
        if beam and beam.get("cone", True) and beam.get("origin"):
            o, tg = beam["origin"], beam["target"]
            ang = math.degrees(math.atan2(tg[1] - o[1], tg[0] - o[0]))
            length = math.hypot(tg[0] - o[0], tg[1] - o[1])
            spread = math.degrees(math.atan2(beam.get("radius", 260.0), max(length, 1.0)))
            flashlight_beam(f, o, ang, length=length, spread=spread, level=0.55 * beam.get("level", 1.0), par=par,
                            hit=False, t=t, dust=0.6, scale=s)

    def _light_mask(self, f, beam, ambient, flash, par):
        """MULTIPLY the frame by the light: ambient + the beam's pool (+ flash)."""
        cam = f.lcam(par)
        ds = 4
        w, h = max(1, f.pw // ds), max(1, f.ph // ds)
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        c = cairo.Context(surf)
        base = clamp(ambient + flash)
        c.set_source_rgb(base, base, base)
        c.paint()
        c.set_matrix(cam.matrix(f.scale * w / f.pw))
        if beam:
            tg = beam["target"]
            r = beam.get("radius", 260.0)
            lv = beam.get("level", 1.0)
            o = beam.get("origin")
            ang, el = 0.0, 1.0
            if o:
                ang = math.degrees(math.atan2(tg[1] - o[1], tg[0] - o[0]))
                d = math.hypot(tg[0] - o[0], tg[1] - o[1])
                el = 1.0 + 0.35 * clamp(d / (6 * r))           # oblique torch: a stretched pool
            c.set_operator(cairo.OPERATOR_ADD)
            c.save()
            c.translate(tg[0], tg[1])
            c.rotate(math.radians(ang))
            c.scale(el, 1.0)
            k = clamp(lv)
            draw.radial(c, (0, 0), 0, r, [(0, (k, k * 0.97, k * 0.9), 1), (0.55, (0.8 * k, 0.77 * k, 0.7 * k), 1),
                                          (0.8, (0.35 * k, 0.33 * k, 0.3 * k), 1), (1, (0, 0, 0), 1)])
            c.arc(0, 0, r, 0, 2 * math.pi)
            c.fill()
            c.restore()
        with f.screen() as S:
            S.set_operator(cairo.OPERATOR_MULTIPLY)
            pat = cairo.SurfacePattern(surf)
            pat.set_filter(cairo.FILTER_BILINEAR)
            pat.set_matrix(cairo.Matrix(xx=w / float(W), yy=h / float(H)))
            S.set_source(pat)
            S.paint()

    def _desk(self, L, t):
        s = self.s
        ox, oy = self.o
        y = self.desk_y
        draw.rect(L, ox - 3000 * s, y, ox + 3000 * s, y + 900 * s)
        draw.fill(L, INK)
        # the desk top's edge catches a little light; paper, scissors, half-cut dolls
        draw.rect(L, ox - 3000 * s, y, ox + 3000 * s, y + 6 * s)
        draw.fill(L, mix(INK, PAL.fog_at(1.0), 0.25))
        draw.poly(L, [(ox - 330 * s, y + 4 * s), (ox - 110 * s, y - 2 * s), (ox - 90 * s, y + 20 * s), (ox - 320 * s, y + 26 * s)])
        draw.fill(L, mul(PAPER, 0.8))
        sx, sy = ox + 150 * s, y + 10 * s
        for a in (-9, 11):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            blade = [(0, -3), (150, -1), (150, 2), (0, 4)]
            draw.poly(L, [(sx + (u * ca - v * sa) * s, sy + (u * sa + v * ca) * s * 0.35) for u, v in blade])
        for dxs in (-26, -6):
            L.new_sub_path()
            L.arc(sx + dxs * s, sy, 13 * s, 0, 2 * math.pi)
            L.new_sub_path()
            L.arc_negative(sx + dxs * s, sy, 7 * s, 2 * math.pi, 0)
        draw.fill(L, mix(INK, PAL.fog_at(1.0), 0.45))

    def _blinds(self, L):
        s = self.s
        x0, y0, x1, y1 = self.blinds
        draw.rect(L, x0 - 24 * s, y0 - 24 * s, x1 + 24 * s, y1 + 30 * s)
        draw.fill(L, INK)
        y = y0
        while y < y1:
            draw.rect(L, x0, y + 10 * s, x1, y + 15 * s)
            y += 17 * s
        draw.fill(L, mix(INK, PAL.fog_at(1.0), 0.45))

    def _police_stripes(self, A, t, k):
        """Strobe light through the blinds: slatted stripes thrown across the wall."""
        b, r = siren(t, rate=1.6)
        s = self.s
        x0, y0, x1, y1 = self.blinds
        for col, v in ((BLUE, b), (RED, r)):
            if v <= 0.01:
                continue
            y = y0
            while y < y1:
                q = [(x0, y + 10 * s), (x0, y + 15 * s), (x0 - 1300 * s, y + 340 * s + 20 * s), (x0 - 1300 * s, y + 340 * s)]
                draw.poly(A, q)
                y += 17 * s
            draw.fill(A, col, 0.20 * v * k)
            A.rectangle(x0, y0, x1 - x0, y1 - y0)
            draw.fill(A, col, 0.35 * v * k)
