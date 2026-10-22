"""SHADOW PLAY - interiors.

HerRoom      her dark room seen from inside, looking out through her window (S02, S12):
             wall with the window, sash and mullions, sheer curtain, sill with plant, mug and
             binoculars, radiator, armchair, floor lamp, rain on the glass.
her_room_interior(...)  her room as seen from ACROSS the street (S08), for Facade(variant='hers').
Room3D       a one-point-perspective box room with per-pixel lighting (bulbs, torches,
             light through a window or a door, with mullions and shadows of blockers).
Apartment9   the theatre (S04, S07, S09, S10): bare room, window, the sheet on its wire, the
             bare-bulb lamp, the table with the puppet rig, the door to the hallway.
KillerRoom   his room (S11): a 5 x 8 board of pinned paper dolls, desk, lamp, blinds.

Room coordinates (Room3D) are metres: X right (0 = middle), Y up (0 = floor), Z into the
room (back wall at Z = depth). Room3D.P(X, Y, Z) gives the world point; Room3D.place(X, Z)
gives (x, floor_y, k) to stand a figure there (k = scale relative to a 600-px adult).
"""
import math

import cairo
import cv2
import numpy as np

from engine import draw
from engine.core import W, H, clamp, lerp, hash01, noise1, fbm1, smoothstep, siren
from engine.frame import surf_array, array_surface, cached
from engine.palette import RED

from .sets_base import (PAL, INK, AMBER, HOT, RAIN, BLUE, PX_M, mix, mul, layer_spec, opened, view_box,
                        record, put, glow, glow_ellipse, cone, shadow_screen, rain_glints, rrect, local_matrix)
from .sets_props import (binoculars, BareLamp, Sheet, Door, flashlight_beam, lamp_light, red_coat, coat_hook,
                         paper_blood)


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
    def light_map(self, f, lights, par=1.0, ds=4, albedo=None, ambient=0.0, blur=1.2, gain=1.0):
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
        albedo: dict(back, walls, floor, ceiling) reflectances."""
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
        acc *= A[..., None] * gain
        if ambient > 0:
            acc += ambient * A[..., None]
        out = np.zeros((h, w, 4), np.float32)
        out[..., 0] = acc[..., 2]
        out[..., 1] = acc[..., 1]
        out[..., 2] = acc[..., 0]
        out[..., :3] = np.clip(out[..., :3], 0, 1) * 255.0
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
        bulb_r = 0.035
        pen = 2 * bulb_r * abs(zs - caster_z) / max(abs(caster_z - lz), 1e-3)
        soft = pen * r.ppm(zs) * 0.5
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
            zo = z1 - (z1 - z0) * clamp(door_open * 1.2)
            L.append(dict(kind="door", src=(-self.room.hw - 2.2, 2.5, (z0 + z1) / 2 - 0.3), z0=z0, z1=z1,
                          top=self.DOOR_H, color=mix(AMBER, HOT, 0.3), power=3.0 * hall,
                          mask=self._door_mask(door_open, door_mask)))
        for fl in flashlights:
            L.append(dict(kind="spot", pos=fl["pos"], dir=fl["dir"], cone=fl.get("cone", 9.0), soft=fl.get("soft", 7.0),
                          color=fl.get("color", mix(HOT, (1, 1, 1), 0.2)), power=fl.get("power", 2.4), r0=0.2))
        return L

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
             sheet_hit=None, sheet_fall=0.0, blood=(), hooks=None, dust=1.0):
        """Draw apartment 9 in a given state.

        lamp        bulb level (sets.switch for the flicker-on); lamp_at 'front' | 'behind' | (X, Z)
        lamp_tilt   degrees the stand leans (the crash in S10); lamp_broken: the bulb is gone
        sheet/table/rig  which props are present (S04: all False: the room is empty)
        crank       crank-wheel angle (deg) of the rig (drives the arm wire)
        puppets     fn(ctx, apt) drawing the paper dolls at apt.rod_tip(...) (as the camera sees them)
        casters     fn(ctx) drawing what throws shadows on the sheet, at depth caster_z
                    (default: the puppets + rods at the table's depth)
        door_open   0..1 (sets.door_swing / slam); hall 0..1 hallway light; locked 0..1
        door_mask   fn(u, v) -> blocker in the doorway (u 0 hinge..1 free edge, v 0 floor..1 top)
        street      cold street light through the window; police 0..1 strobes through it
        flashlights [dict(pos=(X,Y,Z), dir=(dx,dy,dz), cone, power)] torch beams (S04)
        outside     fn(ctx, rect) to paint the view through the window (default: night + far windows)
        tears / sheet_hit / sheet_fall   see Sheet
        blood       [(X, Y, Z, scale, seed, grow)] red paper splashes on the floor/table
        hooks       {'after_room', 'after_sheet', 'after_props', 'after_door': fn(f, t)} to insert
                    people between the planes."""
        hooks = hooks or {}
        spec = layer_spec(layer)
        par = spec["par"]
        lamp_xz = self.lamp_pos(lamp_at)
        lamp3d = self.bulb3d(lamp_at, lamp_tilt)
        behind = lamp_xz[1] > self.SHEET_Z
        lv = 0.0 if lamp_broken else lamp
        sheet_glow = lv * (0.9 if behind else 0.5) if sheet else 0.0
        # 1) the box, lit
        with opened(f, spec) as L:
            self.room.draw_box(L)
            self.draw_window(f, t, L, outside=outside, street=street, police=police)
        lights = self.lights(t, lamp=lv, lamp_at=lamp_at, lamp_tilt=lamp_tilt, sheet=sheet, street=street,
                             police=police, door_open=door_open, hall=hall, door_mask=door_mask,
                             flashlights=flashlights, sheet_glow=sheet_glow if behind else None)
        self.room.light_map(f, lights, par=par, ambient=0.012)
        if "after_room" in hooks:
            hooks["after_room"](f, t)
        # 2) behind the sheet (the trap: lamp + doll on its rod between sheet and window)
        with opened(f, spec) as L:
            if behind and not sheet:
                pass
            if behind:
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
            if not behind:
                self._draw_lamp(f, t, L, lamp_at, lv, lamp_tilt, lamp_broken, spec)
        if "after_props" in hooks:
            hooks["after_props"](f, t)
        # 5) the door
        with opened(f, spec) as L:
            self.door.draw(f, t, L, open=door_open, hall=hall, locked=locked, key=False)
        self.door.light(f, t, open=door_open, hall=hall, par=par, spill=0.0)
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
    """Her room seen from inside, looking out (S02 reveal, S12). An elevation view of the
    window wall; draw the outside world (sky, facade at a small scale) FIRST, then this.

    HerRoom(origin=(540, 1800), scale=1.0)   origin = floor point under the window centre
      .glass            world rect of the glass (the view out)
      .sill_y           world y of the sill top
      .binocular_rest   where her binoculars lie on the sill (world)
      .chair_seat       world point on the armchair seat (for her, sitting)
      .lamp_bulb        world point of the floor lamp's bulb
    draw(f, t, layer=None, curtain=1.0, rain=1.0, binoculars=True, plant=True, mug=True,
         radiator=True, lamp=0.0, chair=True, outside_light=1.0)
    draw_chair(f, t, layer) the armchair alone (e.g. as a blurred foreground occluder)."""

    def __init__(self, origin=(540.0, 1800.0), scale=1.0):
        self.o = (float(origin[0]), float(origin[1]))
        self.s = s = float(scale)
        ox, oy = self.o
        self.glass = (ox - 206 * s, oy - 978 * s, ox + 206 * s, oy - 292 * s)
        self.sill_y = oy - 292 * s
        self.binocular_rest = (ox + 96 * s, self.sill_y - 13 * s)
        self.chair_seat = (ox - 330 * s, oy - 170 * s)
        self.lamp_bulb = (ox + 420 * s, oy - 1010 * s)
        self.rod_y = self.glass[1] - 70 * s

    def _wall(self, c):
        s = self.s
        ox, oy = self.o
        x0, y0, x1, y1 = self.glass
        draw.rect(c, ox - 4000 * s, oy - 4000 * s, ox + 4000 * s, oy + 2000 * s)
        draw.rect(c, x0, y0, x1, y1)

    def draw(self, f, t, layer=None, curtain=1.0, rain=1.0, binoculars=True, plant=True, mug=True, radiator=True,
             lamp=0.0, chair=True, outside_light=1.0, condensation=1.0):
        spec = layer_spec(layer)
        par = spec["par"]
        s = self.s
        ox, oy = self.o
        x0, y0, x1, y1 = self.glass
        gw, gh = x1 - x0, y1 - y0
        # glass: condensation at the bottom, a faint cold sheen
        with f.light(par=par, blur=8.0) as A:
            draw.linear(A, (0, y1 - gh * 0.35), (0, y1), [(0, PAL.fog_at(1.0), 0.0), (1, PAL.fog_at(1.0), 0.20 * condensation)])
            A.rectangle(x0, y0, gw, gh)
            A.fill()
        if rain > 0:
            self._rain_on_glass(f, t, par, rain)
        with opened(f, spec) as L:
            # wall with the opening; a lamp-lit room lifts the wall
            L.new_path()
            self._wall(L)
            L.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            wall = mix(INK, mix(AMBER, PAL.fog_at(1.0), 0.6), 0.05 + 0.25 * lamp)
            draw.fill(L, wall)
            L.set_fill_rule(cairo.FILL_RULE_WINDING)
            self._sash(L)
            if curtain > 0:
                self._curtain(L, t, curtain)
            self._sill(L)
            if radiator:
                self._radiator(L)
            if plant:
                self._plant(L, t)
            if mug:
                mx, my = ox + 175 * s, self.sill_y
                draw.poly(L, [(mx - 15 * s, my - 34 * s), (mx + 15 * s, my - 34 * s), (mx + 13 * s, my), (mx - 13 * s, my)])
                L.new_sub_path()
                L.arc(mx + 18 * s, my - 18 * s, 9 * s, -math.pi / 2, math.pi / 2)
                L.arc_negative(mx + 18 * s, my - 18 * s, 4.5 * s, math.pi / 2, -math.pi / 2)
                L.close_path()
                draw.fill(L, INK)
            if binoculars:
                bx, by = self.binocular_rest
                binoculars(L, (bx, by), angle=180.0, scale=s * 1.05, view="side", flip=1, strap=0.8, t=t)
            self._lamp(L, lamp)
            if chair:
                self._chair(L)
        # light coming in through the window: sill top, reveal, curtain folds; lamp glow
        with f.light(par=par, blur=4.0) as A:
            k = outside_light
            A.rectangle(x0 - 50 * s, self.sill_y - 2 * s, gw + 100 * s, 4 * s)
            draw.fill(A, PAL.fog_at(1.0), 0.8 * k)
            draw.linear(A, (x0, 0), (x0 + 34 * s, 0), [(0, PAL.fog_at(1.0), 0.0), (1, PAL.fog_at(1.0), 0.35 * k)])
            A.rectangle(x0 - 34 * s, y0 - 34 * s, 34 * s, gh + 34 * s)
            A.fill()
            glow_ellipse(A, ((x0 + x1) / 2, self.sill_y + 10 * s), gw * 0.8, 40 * s, PAL.fog_at(1.0), 0.25 * k)
            glow_ellipse(A, ((x0 + x1) / 2, oy), gw * 1.1, 70 * s, PAL.fog_at(1.0), 0.12 * k)
            if curtain > 0:
                for j in range(5):
                    fx = x1 - gw * 0.05 + j * 30 * s
                    if fx < x1:
                        draw.linear(A, (fx - 8 * s, 0), (fx + 8 * s, 0), [(0, PAL.fog_at(1.0), 0), (0.5, PAL.fog_at(1.0), 0.18 * k),
                                                                          (1, PAL.fog_at(1.0), 0)])
                        A.rectangle(fx - 8 * s, y0, 16 * s, gh)
                        A.fill()
        if lamp > 0.01:
            lamp_light(f, self.lamp_bulb, lamp, scale=s * 1.3, par=par, radius=1300)

    def draw_chair(self, f, t, layer=None):
        with opened(f, layer) as L:
            self._chair(L)

    # ------------------------------------------------------------------ pieces
    def _sash(self, L):
        s = self.s
        x0, y0, x1, y1 = self.glass
        cx = (x0 + x1) / 2
        ym = y0 + (y1 - y0) * 0.5
        cw = 34 * s
        # casing (architrave) and the sash bars
        draw.rect(L, x0 - cw, y0 - cw, x1 + cw, y0)
        draw.rect(L, x0 - cw, y0, x0, y1)
        draw.rect(L, x1, y0, x1 + cw, y1)
        draw.rect(L, x0 - cw - 10 * s, y0 - cw - 14 * s, x1 + cw + 10 * s, y0 - cw)
        bars = [(x0, y0, x1, y0 + 16 * s), (x0, y1 - 18 * s, x1, y1), (x0, y0, x0 + 16 * s, y1), (x1 - 16 * s, y0, x1, y1),
                (x0, ym - 13 * s, x1, ym + 13 * s), (cx - 6 * s, y0, cx + 6 * s, y1)]
        for b in bars:
            draw.rect(L, *b)
        # window latch on the meeting rail
        draw.ellipse(L, (cx, ym - 14 * s), 14 * s, 6 * s)
        draw.fill(L, INK)

    def _curtain(self, L, t, k):
        """Sheer curtain on the right, from a rod with ball finials down to the floor."""
        s = self.s
        x0, y0, x1, y1 = self.glass
        ox, oy = self.o
        ry = self.rod_y
        draw.capsule(L, (x0 - 120 * s, ry), (x1 + 160 * s, ry), 5 * s, 5 * s)
        for ex in (x0 - 124 * s, x1 + 164 * s):
            draw.circle(L, (ex, ry), 11 * s)
        draw.fill(L, INK)
        sw = 10 * s * fbm1(t * 0.35, 21)
        pts = [(x1 - 110 * s, ry), (x1 + 150 * s, ry), (x1 + 160 * s + sw * 0.2, oy - 6 * s),
               (x1 - 30 * s + sw, oy - 4 * s), (x1 - 52 * s + sw * 0.8, (ry + oy) / 2 + 40 * s),
               (x1 - 96 * s + sw * 0.4, ry + 200 * s)]
        draw.smooth(L, pts, close=True, tension=0.3)
        draw.fill(L, INK, 0.55 * k)
        # deeper folds
        for j in range(4):
            fx = x1 - 70 * s + j * 52 * s
            pts = [(fx, ry + 6 * s), (fx + 14 * s, ry + 6 * s), (fx + 20 * s + sw * 0.6, oy - 8 * s), (fx + 2 * s + sw * 0.6, oy - 8 * s)]
            draw.poly(L, pts)
        draw.fill(L, INK, 0.35 * k)

    def _sill(self, L):
        s = self.s
        ox, oy = self.o
        y = self.sill_y
        draw.rect(L, ox - 270 * s, y, ox + 270 * s, y + 20 * s)
        draw.rect(L, ox - 240 * s, y + 20 * s, ox + 240 * s, y + 44 * s)
        draw.fill(L, INK)

    def _radiator(self, L):
        s = self.s
        ox, oy = self.o
        top, bot = oy - 236 * s, oy - 36 * s
        x = ox - 176 * s
        while x < ox + 176 * s:
            rrect(L, x, top, x + 20 * s, bot, 9 * s)
            x += 26 * s
        draw.rect(L, ox - 180 * s, bot - 30 * s, ox + 180 * s, bot - 18 * s)
        draw.rect(L, ox - 180 * s, top + 16 * s, ox + 180 * s, top + 26 * s)
        for fx in (ox - 160 * s, ox + 150 * s):
            draw.rect(L, fx, bot, fx + 12 * s, oy)
        # valve
        draw.rect(L, ox + 180 * s, top + 40 * s, ox + 214 * s, top + 52 * s)
        draw.circle(L, (ox + 214 * s, top + 34 * s), 13 * s)
        draw.fill(L, INK)

    def _plant(self, L, t):
        s = self.s
        x0 = self.glass[0]
        px, py = x0 + 50 * s, self.sill_y
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
        """Floor lamp with a drum shade, right of the window."""
        s = self.s
        ox, oy = self.o
        lx = ox + 420 * s
        draw.ellipse(L, (lx, oy - 6 * s), 70 * s, 12 * s)
        draw.rect(L, lx - 5 * s, oy - 980 * s, lx + 5 * s, oy - 6 * s)
        shade = [(lx - 92 * s, oy - 960 * s), (lx + 92 * s, oy - 960 * s), (lx + 70 * s, oy - 1110 * s), (lx - 70 * s, oy - 1110 * s)]
        draw.fill(L, INK)
        draw.poly(L, shade)
        if lamp > 0.01:
            draw.linear(L, (0, oy - 1110 * s), (0, oy - 960 * s), [(0, mix(INK, AMBER, 0.65 * lamp), 1),
                                                                   (1, mix(INK, HOT, 0.9 * lamp), 1)])
            L.fill()
        else:
            draw.fill(L, INK)

    def _chair(self, L):
        """Wingback armchair, seen from behind, facing the window."""
        s = self.s
        cx, cy = self.chair_seat
        ox, oy = self.o
        back = [(cx - 150 * s, oy - 10 * s), (cx - 168 * s, cy - 40 * s), (cx - 190 * s, cy - 250 * s),
                (cx - 176 * s, cy - 330 * s), (cx - 120 * s, cy - 352 * s), (cx - 40 * s, cy - 380 * s),
                (cx + 40 * s, cy - 380 * s), (cx + 120 * s, cy - 352 * s), (cx + 176 * s, cy - 330 * s),
                (cx + 190 * s, cy - 250 * s), (cx + 168 * s, cy - 40 * s), (cx + 150 * s, oy - 10 * s)]
        draw.smooth(L, back, close=True, tension=0.28)
        for fx in (cx - 140 * s, cx + 128 * s):
            draw.rect(L, fx, oy - 30 * s, fx + 14 * s, oy)
        draw.fill(L, INK)

    def _rain_on_glass(self, f, t, par, k):
        """Drops beading on the pane and a few running down (catching the outside light)."""
        s = self.s
        x0, y0, x1, y1 = self.glass
        gw, gh = x1 - x0, y1 - y0
        with f.light(par=par, blur=1.2) as A:
            n = 90
            for j in range(n):
                u, v = hash01(77, j, 1), hash01(77, j, 2)
                x = x0 + u * gw
                y = y0 + v * gh
                r = (1.6 + 3.8 * hash01(77, j, 3) ** 2) * s
                # stick-slip runners: a few drops slide down in bursts
                if j % 9 == 0:
                    per = 3.0 + 3.0 * hash01(77, j, 4)
                    ph = (t / per + hash01(77, j, 5)) % 1.0
                    run = (ph ** 3) * gh * 0.8
                    y = y0 + ((v * gh + run) % gh)
                    r *= 1.6
                    # its trail
                    draw.capsule(A, (x, max(y0, y - run * 0.6)), (x + 2 * s, y), 0.8 * s, r * 0.5)
                    draw.fill(A, PAL.fog_at(1.0), 0.18 * k)
                draw.circle(A, (x, y), r)
                draw.fill(A, PAL.fog_at(1.0), 0.20 * k)
                draw.circle(A, (x - r * 0.35, y + r * 0.35), r * 0.38)
                draw.fill(A, mix(PAL.rain, HOT, 0.4), 0.55 * k)


def her_room_interior(lamp=1.0, man=None, curtain=True):
    """Interior callback for her window seen from across the street (S08):
    Facade(variant='hers').draw(..., lit={HER_WINDOW: level}, interiors={HER_WINDOW: her_room_interior(man=fn)}).
    Draws her floor lamp (shade glowing), the armchair facing the window, then man(ctx, win)."""
    def fn(ctx, win):
        x0, y0, x1, y1 = win.rect
        w, h = x1 - x0, y1 - y0
        k = win.person_h / 600.0
        fy = win.floor_y
        if win.mode == "direct":
            # floor lamp at the right (mirror of the inside view), shade lit
            lx = x0 + w * 0.80
            draw.rect(ctx, lx - 3 * k, fy - 980 * k, lx + 3 * k, fy)
            shade = [(lx - 92 * k, fy - 960 * k), (lx + 92 * k, fy - 960 * k), (lx + 70 * k, fy - 1110 * k),
                     (lx - 70 * k, fy - 1110 * k)]
            draw.fill(ctx, INK)
            draw.poly(ctx, shade)
            draw.fill(ctx, mix(INK, HOT, 0.85 * clamp(win.level)))
        # armchair facing us at the left
        cx = x0 + w * 0.3
        chair = [(cx - 150 * k, fy), (cx - 168 * k, fy - 200 * k), (cx - 190 * k, fy - 420 * k), (cx - 120 * k, fy - 520 * k),
                 (cx + 120 * k, fy - 520 * k), (cx + 190 * k, fy - 420 * k), (cx + 168 * k, fy - 200 * k), (cx + 150 * k, fy)]
        draw.smooth(ctx, chair, close=True, tension=0.28)
        draw.fill(ctx, mix(INK, AMBER, 0.12 * clamp(win.level)))
        if man is not None:
            man(ctx, win)
    return fn


# =========================================================================== killer's room
class KillerRoom:
    """His room (S11): a 5 x 8 board of paper dolls, one for every window, pinned in rows,
    each hanging on a short string; a desk with a gooseneck lamp, scissors and paper; a
    window with venetian blinds (police light can stripe through it).

    KillerRoom(origin=(540, 1750), scale=1.0)   origin = floor point under the board centre
      .board               world rect of the board
      .anchor(i)           world pin point of doll i (1..40, row-major like the windows)
      .doll_h              suggested doll height (world px)
      .lamp_bulb           world point of the desk lamp's bulb
    draw(f, t, layer=None, dolls=None, lamp=1.0, police=0.0, sway=1.0, shadows=True)
      dolls = fn(ctx, i, anchor, doll_h, t) draws doll i hanging from `anchor`."""

    COLS, ROWS = 5, 8

    def __init__(self, origin=(540.0, 1750.0), scale=1.0):
        self.o = (float(origin[0]), float(origin[1]))
        self.s = s = float(scale)
        ox, oy = self.o
        self.board = (ox - 300 * s, oy - 1420 * s, ox + 300 * s, oy - 330 * s)
        bx0, by0, bx1, by1 = self.board
        self.cell = ((bx1 - bx0 - 60 * s) / self.COLS, (by1 - by0 - 60 * s) / self.ROWS)
        self.doll_h = self.cell[1] * 0.78
        self.lamp_bulb = (ox + 250 * s, oy - 420 * s)
        self.desk_y = oy - 262 * s

    def anchor(self, i):
        r, c = (i - 1) // self.COLS, (i - 1) % self.COLS
        bx0, by0, bx1, by1 = self.board
        cw, ch = self.cell
        return (bx0 + 30 * self.s + (c + 0.5) * cw, by0 + 30 * self.s + r * ch + 8 * self.s)

    def string_end(self, i, t=0.0, sway=1.0):
        """Where the doll hangs: below the pin on its short string (swaying a little)."""
        ax, ay = self.anchor(i)
        L = 16 * self.s
        a = math.radians(4.0 * sway * fbm1(t * 0.5 + i * 0.37, 7))
        return (ax + L * math.sin(a), ay + L * math.cos(a))

    def draw(self, f, t, layer=None, dolls=None, lamp=1.0, police=0.0, sway=1.0, shadows=True, blinds=True):
        spec = layer_spec(layer)
        par = spec["par"]
        s = self.s
        ox, oy = self.o
        bx0, by0, bx1, by1 = self.board
        with opened(f, spec) as L:
            # room: dark wall, floor line
            L.rectangle(ox - 4000 * s, oy - 4000 * s, 8000 * s, 6000 * s)
            draw.fill(L, mix(INK, PAL.fog_at(1.0), 0.10))
            L.rectangle(ox - 4000 * s, oy, 8000 * s, 2000 * s)
            draw.fill(L, INK)
            # the board (cork): lit by the desk lamp from below right
            lb = self.lamp_bulb
            draw.radial(L, (lb[0] - 40 * s, lb[1] - 60 * s), 0, (by1 - by0) * 1.25,
                        [(0, mix(mul(AMBER, 0.75), HOT, 0.3 * lamp), 1), (0.45, mul(AMBER, 0.42), 1),
                         (1, mix(INK, mul(AMBER, 0.12), 1.0), 1)])
            L.rectangle(bx0, by0, bx1 - bx0, by1 - by0)
            L.fill()
            if lamp < 1.0:
                L.rectangle(bx0, by0, bx1 - bx0, by1 - by0)
                draw.fill(L, INK, 1.0 - lamp)
            # the dolls' shadows on the board (thrown up and left by the low lamp)
            if dolls is not None and shadows and lamp > 0.02:
                def casters(c):
                    for i in range(1, 41):
                        dolls(c, i, self.string_end(i, t, sway), self.doll_h, t)
                shadow_screen(L, casters, region=lambda c: c.rectangle(bx0, by0, bx1 - bx0, by1 - by0),
                              bbox=self.board, soft=5 * s, density=0.55 * lamp, mag=1.06, center=(lb[0], lb[1] + 300 * s))
            # frame
            L.new_path()
            L.rectangle(bx0 - 18 * s, by0 - 18 * s, bx1 - bx0 + 36 * s, by1 - by0 + 36 * s)
            L.rectangle(bx0, by0, bx1 - bx0, by1 - by0)
            L.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            draw.fill(L, INK)
            L.set_fill_rule(cairo.FILL_RULE_WINDING)
            # pins and strings
            for i in range(1, 41):
                a = self.anchor(i)
                e = self.string_end(i, t, sway)
                draw.capsule(L, a, e, 0.9 * s, 0.9 * s)
                draw.fill(L, mix(INK, AMBER, 0.35))
                draw.circle(L, a, 4.5 * s)
                draw.fill(L, INK)
            # the dolls
            if dolls is not None:
                for i in range(1, 41):
                    dolls(L, i, self.string_end(i, t, sway), self.doll_h, t)
            # desk, lamp, scissors, paper
            self._desk(L, t, lamp)
            if blinds:
                self._blinds(L)
        with f.light(par=par, blur=5.0) as A:
            if lamp > 0.01:
                lb = self.lamp_bulb
                glow(A, lb, 60 * s, HOT, 0.8 * lamp)
                glow_ellipse(A, (lb[0] - 80 * s, self.desk_y), 360 * s, 40 * s, AMBER, 0.35 * lamp)
            if police > 0:
                self._police_stripes(A, t, police)
        if lamp > 0.01:
            with f.emit(par=par) as G:
                draw.circle(G, self.lamp_bulb, 14 * s)
                draw.fill(G, HOT, lamp)

    def _desk(self, L, t, lamp):
        s = self.s
        ox, oy = self.o
        y = self.desk_y
        draw.rect(L, ox - 520 * s, y, ox + 520 * s, y + 26 * s)
        for lx in (ox - 500 * s, ox + 480 * s):
            draw.rect(L, lx, y + 26 * s, lx + 22 * s, oy)
        draw.rect(L, ox + 200 * s, y + 26 * s, ox + 480 * s, y + 140 * s)
        # gooseneck lamp
        lb = self.lamp_bulb
        bx = ox + 330 * s
        draw.ellipse(L, (bx, y - 6 * s), 46 * s, 10 * s)
        draw.chain(L, [(bx, y - 8 * s), (bx + 4 * s, y - 70 * s), (bx - 20 * s, y - 130 * s), (lb[0] + 30 * s, lb[1] - 30 * s)],
                   [4 * s, 4 * s, 4 * s, 4 * s])
        draw.poly(L, [(lb[0] + 44 * s, lb[1] - 50 * s), (lb[0] + 10 * s, lb[1] - 64 * s), (lb[0] - 34 * s, lb[1] + 4 * s),
                      (lb[0] + 22 * s, lb[1] + 18 * s)])
        # scissors (open blades) and a stack of paper with cut-outs
        sx, sy = ox - 220 * s, y
        for a in (-12, 14):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            blade = [(0, -3), (130, -1), (130, 2), (0, 4)]
            draw.poly(L, [(sx + (u * ca - v * sa) * s, sy - 10 * s + (u * sa + v * ca) * s * 0.3) for u, v in blade])
        for dxs in (-24, -4):
            draw.circle(L, (sx + dxs * s, sy - 10 * s), 12 * s)
        draw.fill(L, INK)
        draw.rect(L, ox - 80 * s, y - 22 * s, ox + 60 * s, y)
        draw.fill(L, mix(INK, AMBER, 0.25 * lamp))
        draw.fill(L, INK)

    def _blinds(self, L):
        s = self.s
        ox, oy = self.o
        x0, x1 = ox - 820 * s, ox - 420 * s
        y0, y1 = oy - 1500 * s, oy - 700 * s
        draw.rect(L, x0 - 20 * s, y0 - 20 * s, x1 + 20 * s, y1 + 20 * s)
        draw.fill(L, INK)
        y = y0
        while y < y1:
            draw.rect(L, x0, y + 9 * s, x1, y + 14 * s)
            draw.fill(L, mix(INK, PAL.fog_at(1.0), 0.5))
            y += 16 * s

    def blinds_rect(self):
        s = self.s
        ox, oy = self.o
        return (ox - 820 * s, oy - 1500 * s, ox - 420 * s, oy - 700 * s)

    def _police_stripes(self, A, t, k):
        """Strobe light falling through the blinds onto the wall and the board in stripes."""
        b, r = siren(t, rate=1.6)
        s = self.s
        x0, y0, x1, y1 = self.blinds_rect()
        for col, v in ((BLUE, b), (RED, r)):
            if v <= 0.01:
                continue
            y = y0
            while y < y1:
                q = [(x1, y + 9 * s), (x1, y + 14 * s), (x1 + 1100 * s, y + 160 * s + 22 * s), (x1 + 1100 * s, y + 160 * s)]
                draw.poly(A, q)
                y += 16 * s
            draw.fill(A, col, 0.22 * v * k)
