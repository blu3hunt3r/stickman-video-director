"""SHADOW PLAY - sets and props (public API). Scene modules do:

    from films.shadowplay import sets

Everything is a deterministic function of t, drawn in WORLD coordinates (y down) through
the frame's layers; filled ink silhouettes, light added in f.light()/f.emit(). On the
action plane an adult is 600 px tall (1 m = 343 px, sets.PX_M).

THE FACADE (s01-s03, s06, s12)                                   sets_facade.py
    fac = sets.Facade(origin=(540, 3940), scale=1.0)   bottom-centre on the sidewalk
    f.set_camera(fac.camera_lock())        the bible's FACADE LOCK: window i lands on
                                           sets.Facade.lock_rect(i) (96 x 120 px)
    fac.draw(f, t, layer=None, lit=sets.NIGHT, interiors={4: fn}, curtains={9: 'sheet'})
        lit       {i: level | fn(t)}; sets.switch(t, t_on, kind='flicker') turns one on
        interiors {i: fn(ctx, win)}: silhouettes in world coords, clipped to the window;
                  behind a shade/sheet they become shadows (win.mode == 'shadow')
        win       sets.WindowInfo: rect, cx, cy, w, h, sill_y, floor_y, person_h, level, t
    fac.window_rect(i), window_center(i), sill_point(i), floor_y(i), landing(row),
    camera_on(i, fill), camera_full(), light_sources(t, lit) (for the street reflections)
    sets.Facade(..., variant='hers')       her building; her window is sets.HER_WINDOW
    sets.neighbours(fac) + sets.draw_blocks(...), sets.Skyline(...), sets.night_sky(f, t)

HER APARTMENT                                                     sets_rooms.py
    sets.HerRoom(origin, scale)            the window wall from inside (curtain, sill,
                                           binoculars, plant, radiator, armchair, lamp,
                                           rain on the glass, a steamed lower pane with a
                                           wiped patch: condensation=, wipe=); draw the
                                           outside FIRST (the frost blurs what is there)
    sets.HerEntry(origin, scale)           her door, coat hooks with the RED coat
    sets.her_room_interior(man=fn)         her window seen from across the street (s08)

THE STREET (s02, s04, s06)                                        sets_street.py
    sets.Street(ground_y, depth=...)       wet asphalt mirroring every light source
        .draw(f, t, sources=fac.light_sources(t, lit) + car.light_sources(t), ...)
                                           (a source dict may carry ground=y: a light standing
                                           in the street, e.g. the police bar, reflects from there)
        .reflect(f, t, fn, foot_y, bbox)   a figure's broken reflection (her red coat)
    sets.Streetlamp(base, height), sets.Car(pos), sets.PoliceCar(pos) (+ strobe_wash)

THE STAIRS (s06, s09, s10)                                        sets_stairs.py
    sets.Stairwell(center, stretch=1.2)    straight down the square spiral (Vertigo); stretch
                                           lengthens it to fill 9:16. .draw(f, t, cam_h, focal,
                                           roll, bottom=, windows=, police=, hooks={storey: fn}),
                                           .vertigo(u) dolly-zoom, .path_point(u) her position
    sets.Hallway(origin)                   the landing outside apartment 9: door 9, light
                                           under it and through the keyhole, police window

APARTMENT 9 (s03-s05 from outside via the facade, s04, s07, s09, s10)   sets_rooms.py
    apt = sets.Apartment9(origin=(540, 880), scale=1.0)   origin = vanishing point
    apt.draw(f, t, lamp=..., lamp_at='front'|'behind', puppets=fn, casters=fn,
             caster_z=Z, door_open=..., hall=..., feet=(...), flashlights=[...], police=...,
             hooks={...})      a caster 10 cm in front of the bulb behind the sheet throws a
                               life-size shadow (see qa/shadowplay_sets/sf4_apt9.py)
    apt.P(X, Y, Z), apt.place(X, Z) -> (x, floor_y, k); rod_tip('man'|'woman'),
    arm_wire_end(crank), shadow_map(caster_z, lamp3d) (the exact shadow homothety)
    sets.NineWindow(origin, scale)         window 9 from inside (s08 over her shoulder)

HIS ROOM (s11)                                                    sets_rooms.py
    kr = sets.KillerRoom(); f.set_camera(kr.camera_lock())  dolls on the facade lock
    kr.draw(f, t, dolls=fn(ctx, i, center, size, t), beam=dict(target, radius, origin))

PROPS                                                             sets_props.py
    binoculars (view side|front|pair), binocular_glints, binocular_view (the mask), BareLamp,
    lamp_light, Sheet (shadow screen, tears, hits, fall), flashlight, flashlight_beam,
    Door (open / slam / lock, light under it), door_swing, slam, lock_closeup, coat_hook,
    red_coat (RED), match_flame, paper_blood (RED)

TOOLS                                                             sets_base.py
    switch(t, t_on, t_off, kind) light switches, shadow_screen (shadows + RED gels on any
    surface), occlude_emit (hide bloom behind a wall), camera_for (centre a layer point),
    glow, glow_ellipse, cone, rain_glints, add_streaks, layer_spec, mix, mul.
"""
from .sets_base import (PAL, INK, AMBER, HOT, RAIN, BLUE, LIGHTNING, PX_M, mix, mul, tone, layer_spec,
                        switch, level_of, shadow_screen, occlude_emit, rain_glints, add_streaks, glow,
                        glow_ellipse, cone, camera_for)
from .sets_facade import (Facade, WindowInfo, Block, neighbours, draw_blocks, Skyline, night_sky, NIGHT, LATE,
                          HER_WINDOW, rowcol, index, LOCK_COLS, LOCK_ROWS, LOCK_SIZE, LOCK_ZOOM)
from .sets_street import Street, Streetlamp, Car, PoliceCar, strobe_wash
from .sets_props import (binoculars, binocular_glints, binocular_view, BareLamp, lamp_light, Sheet, flashlight,
                         flashlight_beam, door_swing, slam, Door, lock_closeup, coat_hook, red_coat, match_flame,
                         paper_blood)
from .sets_rooms import Room3D, Apartment9, HerRoom, NineWindow, HerEntry, her_room_interior, KillerRoom
from .sets_stairs import Stairwell, Hallway

__all__ = [
    "PAL", "INK", "AMBER", "HOT", "RAIN", "BLUE", "LIGHTNING", "PX_M", "mix", "mul", "tone", "layer_spec",
    "switch", "level_of", "shadow_screen", "occlude_emit", "rain_glints", "add_streaks", "glow", "glow_ellipse",
    "cone", "camera_for",
    "Facade", "WindowInfo", "Block", "neighbours", "draw_blocks", "Skyline", "night_sky", "NIGHT", "LATE",
    "HER_WINDOW", "rowcol", "index", "LOCK_COLS", "LOCK_ROWS", "LOCK_SIZE", "LOCK_ZOOM",
    "Street", "Streetlamp", "Car", "PoliceCar", "strobe_wash",
    "binoculars", "binocular_glints", "binocular_view", "BareLamp", "lamp_light", "Sheet", "flashlight",
    "flashlight_beam", "door_swing", "slam", "Door", "lock_closeup", "coat_hook", "red_coat", "match_flame",
    "paper_blood",
    "Room3D", "Apartment9", "HerRoom", "NineWindow", "HerEntry", "her_room_interior", "KillerRoom",
    "Stairwell", "Hallway",
]
