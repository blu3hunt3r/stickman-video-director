# Engine API — "Nobody Has a Face" (Style 1 Dark noir, 9:16)

Python 3 + pycairo + numpy/scipy. Every frame is a pure function of time:
`render(f, t, T)` must not keep state between calls (frames render in parallel, in any order).
Randomness only through `hash01(seed, ...)`, `noise1`, `fbm1` with constant seeds.

Run everything from the production root: `productions/nobody-has-a-face/`.

```bash
python3 -m engine.render s05 --sheet 12            # contact sheet -> qa/s05_sheet.png  (look at it with the Read tool)
python3 -m engine.render s05 --times 0,1.5,4.2      # half-res stills -> qa/s05/
python3 -m engine.render s05 --scale 0.5            # half-res preview mp4 -> out/scenes/s05_x0.5.mp4
python3 -m engine.render s05                        # full-res scene mp4
```

## 1. Hard style rules (non-negotiable — the reviewer checks every one)

1. **Canvas**: flat pitch-black. Never paint the background any other color, no gradients/vignettes/grain/paper on it.
2. **Figures**: only via `rig.draw_figure` (frozen anchor: hollow circle head, no face, no hair, no clothing, no filled body, uniform line weight, exactly two arms + two legs, one current pose per limb). **Always WHITE** (`alpha` may dim them in shadow/flashback; never recolor). No hats, coats, eyes, mouths, hands/feet shapes. All figures look identical — that is the story.
3. **Accents**: only `AMBER` (light/clues), `CRIMSON` (the killer/guilt: red umbrella, red string, pins, X marks), `BLUE` (the law: police lights, badge, police flashlights). Used only on props and light effects. Everything else is white line art. No other hues.
4. **No visible text, letters, numbers, logos** anywhere (clocks use tick marks only; papers/photos/posters are blank or icon-only; no signage).
5. **Narration is audio-only**: no speech bubbles, no captions, no mouths moving.
6. **No gore**: chalk outlines, falls and implications only. No blood pools; a muzzle flash is the most violent image.
7. **9:16 composition**: keep key action inside the safe box `SAFE = (90, 240, 990, 1500)` (x0, y0, x1, y1 in screen px). Platform UI covers the bottom ~420 px and the right edge. Use vertical depth, vertical reveals, stacked motion.
8. **Pacing**: a perceptible visual change every 2–3 s; three beats per scene (setup / escalation / payoff + outgoing transition); never an idle figure (use `rig.breathe`).

## 2. Coordinates, camera, line widths

* World units = frame pixels at zoom 1 (frame 1080×1920, origin top-left, y down). Camera `Camera(x, y, zoom, rot_deg)` centers the view on world (x, y).
* `f.set_camera(cam)` once at the top of `render`, or `with f.camera(cam2): ...` for parallax layers (`cam.parallax(depth)`; depth<1 farther, >1 nearer).
* `cam.shaken(t, amp=6, rot_amp=0.3, freq=1.3, seed)` handheld; `cam.moved(dx, dy, dzoom, drot)`; `cam.to_screen(p)` / `cam.to_world(p)`.
* Widths passed to draw helpers are **screen pixels at zoom 1**; on-screen width grows only as zoom**0.35 (keeps the "uniform medium line" look when the camera pushes in). Figure line width = 7.5 px × s**0.5.
* Angles for props: degrees, 0 = +x (right), 90 = down, −90 = up.

## 3. Frame (`f`)

| member | use |
|---|---|
| `f.ctx`, `f.g` | raw cairo contexts (main sharp layer, 1/4-res glow layer). Prefer the helpers. |
| `with f.lit(lights, ambient=0.22, soften=3):` | **noir light reveal** — everything drawn inside shows at `ambient` brightness except where `Light` shapes fall. Lights: `Light.cone(apex, angle, spread, length)`, `Light.radial(center, radius)`, `Light.rect(x0,y0,x1,y1)`, `Light.poly(pts)`, `Light.full(i)` (lightning flash). |
| `with f.blurred(radius_px, alpha=1):` | depth of field / soft focus / rack focus (animate radius). |
| `with f.clipped(lambda c: c.arc(x, y, r, 0, 6.2832)):` | clip (e.g. magnifier lens insert, mirror reflection, iris). |
| `with f.alpha(a):` | group opacity (fades of whole layers). |
| `with f.screen():` | draw in screen space ignoring the camera. |
| `f.fade = 0..1` | fade to black at finish. |
| `f.whip = (dx, dy)` | directional motion streak for whip pans (screen px). |
| `f.bloom` (0.16), `f.glow_strength` (1.0) | global halo / emissive strength. |

## 4. draw (`from engine import draw`)

`stroke(f, pts, w, color, alpha, closed, glow, dash)` · `line(f, a, b, w, ...)` · `fill(f, pts, color, alpha, glow)` (accent props only) · `circle(f, c, r, w, color, alpha, fill_it, glow)` · `arc(f, c, r, a0, a1, ...)` · `ellipse(f, c, rx, ry, angle, w, ...)` · `rect(f, x, y, w, h, w_line, color, alpha, fill_it, radius, glow, angle)` · `bezier(f, p0, p1, p2, p3, ...)` · `bezier_pts(...)` · `glow_dot(f, c, r, color, alpha, core)` (emissive halo) · `gradient_fill(...)`.
`glow=k` additionally paints into the emissive layer (bloom). Use glow for light sources and accents, not for ordinary white line art.

## 5. rig — the stick figure (`from engine import rig, Pose`)

`Pose(x, y, s=1, facing=1|-1|0, lean, head, la, le, ra, re, ll, lk, rl, rk)` — `x, y` is the **hip**. Standing height = 344 × s.
Angles: upper arm `la/ra` and thigh `ll/rl` are absolute from straight down, + = forward (front view `facing=0`: + = outward; the figure's LEFT side is screen-right). `le/re` elbow bend (+ = forearm forward/up). `lk/rk` knee bend (+ = shin back). `lean` torso (+ forward), `head` nod.

* `J = rig.draw_figure(f, pose, alpha=1)` → joints dict: `hip, neck, head, head_r, shoulder, le, lh, re, rh, lk, lf, rk, rf` (lh = left hand, rf = right foot …). Attach props to `J['lh']` etc.
* `rig.solve(pose)` joints without drawing · `pose.copy(**kw)` · `poseA.blend(poseB, k)`.
* IK: `rig.reach(pose, 'l', target)` (hand to point), `rig.plant(pose, 'r', target)` (foot to point), `rig.on_ground(pose, ground_y)`.
* Locomotion: `rig.walk(t, x0, ground_y, speed, facing, s, limp=0..1, stride, arm, lean)` planted-foot walk (limp shortens the LEFT step and dips the hip) · `rig.run(t, x0, ground_y, speed, facing, s)`.
* Presets: `rig.stand(x, ground_y, facing, s)`, `rig.breathe(pose, t, amt, seed)` (idle life), `rig.hands_up(pose)`, `rig.sit(x, seat_y, facing, s)`, `rig.lying(x, y, s, rot)` → `(polylines, head_c, head_r)` for chalk outlines / top-down bodies.
* Rule: a limb has one pose. Animate by changing angles over time (Track / tween), never by drawing a second arm.

## 6. props (`from engine import props`)

| prop | notes |
|---|---|
| `match(f, base, angle=-90, length=52, s, lit, burnt, ember, flare, smoke_amt, t, seed)` → tip/light point | the detective's signature. `flare` = ignition burst; `lit` = flame; `burnt` = charred curled tip; `ember` = glowing tip. Pair `lit` with `Light.radial(tip, ~300*s)` in an `f.lit` group so the match lights the scene. |
| `flame(f, base, size, t, seed, intensity)` | bare flame |
| `matchbook(f, c, angle, s, open_, n=10, missing={...}, highlight={...})` | matches torn from the LEFT side = indices 0,1,2… (`missing`) |
| `umbrella(f, hand, angle=-90, R=120, open_=1, color=WHITE or CRIMSON, t, wobble)` → apex | side view; furled when `open_=0`. **THE red umbrella = `color=CRIMSON`** |
| `umbrella_top(f, c, R, rot, color)` | seen from above |
| `clock_face(f, c, r, hour, minute, style='pocket'/'wall'/'tower'/'dash', second, chain)` | tick marks only. 3:07 → `hour=3, minute=7` (`props.THREE_OH_SEVEN`) |
| `bulb(f, anchor, cord_len, swing_deg, on, s, t)` → bulb center | bare interrogation/lineup bulb |
| `streetlamp(f, base, height, s, on, facing, t)` → light point | cast-iron lamp |
| `building(f, x, ground_y, w, h, seed, lit, t, alpha, lw, roof, cols, rows, lit_override)` | line-art tower with amber windows |
| `car_side(f, x, ground_y, s, facing, police, t, wheel_turn, headlights, door_open, brake)` → anchors | 1940s sedan; police = blue/crimson light bar |
| `car_top(f, c, angle, s, police, t, headlights)` | from above |
| `blinds(f, x, y, w, h, slats, tilt)` · `blind_light(f, quad, n, duty, color, alpha, offset)` | venetian blinds + striped light |
| `footprint(f, c, angle, side, s, alpha, wet)` | shoe print |
| `pin`, `photo_card(f, c, w, h, angle, s, crossed)`, `red_string(f, pts, sag, grow, vib, t)`, `board(...)` | evidence board kit (photos show a faceless head + shoulders) |
| `badge(f, c, s, angle, glint)` | blue shield + star |
| `magnifier(f, c, r, angle)` → (lens_c, lens_r) | combine with `f.clipped` for a magnified insert |
| `mirror(f, c, r, glint)` | the round mirror at the center of the board (S14) |
| `revolver(f, hand, angle, s, flash)` | flashback only (S10) |
| `gavel(f, c, angle, s)` | courtroom (S10) |

## 7. fx (`from engine import fx`)

`rain(f, t, density=1, wind=7, seed, alpha, slowmo=1)` (world-anchored layered rain with parallax — draw it inside `f.lit` to get rain that glows in lamp light) · `splashes(f, t, ground_y, x0, x1, rate)` · `ripples(f, t, x0, y0, x1, y1)` · `light_cone(f, apex, angle, spread, length, color, alpha)` (visible haze; pair with `Light.cone`) · `light_pool(f, c, rx, ry, color, alpha)` · `reflection(f, x, y_ground, length, width, color, alpha, t)` (wet-pavement light streak) · `smoke(f, x, y, t, seed, height, alpha)` · `puddle(f, c, rx, ry, t)` · `lightning(f, a, b, seed, alpha)` · `chalk_outline(f, polylines, head_c, head_r)` · `eyelid(f, openness)` (blink transition) · `iris(f, cx, cy, r)` (iris in/out, screen px).
Core helpers (`from engine import *`): `clamp, lerp, inv_lerp, remap, smoothstep, tween(t, t0, t1, a, b, ease)`, `Track([(t, v), (t, v, 'out3'), ...])`, eases `linear in out inout in3 out3 inout3 in5 out5 inout5 sine outback outelastic outexpo inexpo step`, `hash01, rand_range, noise1, fbm1, flicker(t, seed, rate, depth, dropouts)`, `siren(t)` → (blue, red) strobe, `pulse(t, t0, attack, decay)`.

## 8. sets (`from engine import sets`) — shared layouts (continuity across scenes)

* `sets.LINEUP` + `sets.lineup_room(f)` — S1 & S16. Five positions `LINEUP['xs']`, floor `LINEUP['floor_y']`, bulb `LINEUP['bulb_anchor'], LINEUP['cord']`. The detective stands at position index 2 (center) in S16.
* `sets.OFFICE` + `sets.office(f, t, umbrella, lamp_on, door_open, door_light, window_light, window_light_alpha, stripes_offset)` — S5, S10 (board), S14, S15. Board `OFFICE['board']`, window, door, coat rack with THE red umbrella (`umbrella=True`), desk, lamp, pocket watch spot `OFFICE['watch']`, chair `sets.chair(...)`.
* `sets.crowd_top(f, t, area, n, seed, speed, red=dict(index, reverse, amount), highlight=fn, highlight_amt)` — S2, S7, S9, S17.
* `sets.street(f, ground_y, ...)`, `sets.skyline(f, ground_y, seed, t, alpha, lw, lit)` — exteriors.
* `sets.apartment(f, ground_y, juror_on, t)` → juror window center — S12 & S13.

## 9. Timing (`T` passed into render/cues)

`T.duration`, `T.frames`, `T.vo_start`, `T.vo_end`, `T.words` (scene-relative `t0/t1`), `T.at('red')`, `T.end('face', n=1)` (n-th occurrence), `T.word('limp')` → (t0, t1). Sync key visual hits to narration words with these, never with hard-coded guesses.

## 10. Scene module contract — `scenes/sNN_<slug>.py`

```python
from engine import *

def render(f, t, T):
    f.set_camera(Camera(...))
    ...

def cues(T):                       # SFX synced to the picture (scene-relative seconds)
    return [Cue(T.at('match') - 0.1, 'match_strike', gain_db=-2, pan=0.1), ...]

def motion_blur(t, T):             # optional: sub-frames during fast moves (cost x n)
    return 5 if 3.2 < t < 3.6 else 1
```

Performance budget: average ≤ 0.7 s per full-res frame on one core (check with a few `--times` renders). Prefer lines/props; `f.lit`, `f.blurred`, `chalk_outline` each cost ~30–90 ms.

## 11. SFX catalog (names for `Cue`)

Sustained (give `dur`): `bulb_hum`, `room_tone`, `city_far`, `crowd_walla` (nonverbal), `clock_ticking` (params: bpm), `heartbeat` (params: bpm), `tinnitus`, `riser`, `reverse_swell`, `drone_swell`, `siren_far`, `siren_approach`, `siren_pass`, `wipers` (params: period), `pencil_scratch`, `engine_idle`, `car_away`, `wind_gust`.
One-shots: `match_strike` (THE signature sound — identical every time), `match_flare`, `flame_out`, `ember_sizzle`, `bulb_creak`, `bulb_flicker`, `bulb_pop`, `footstep` (params: weight 0..1, wet 0/1), `footstep_run`, `umbrella_open`, `umbrella_flap`, `paper_rustle`, `paper_tear`, `page_flip`, `photo_pin`, `string_twang`, `string_tighten`, `brush_swish`, `camera_shutter`, `radio_static`, `car_door_open`, `car_door_close`, `car_brake`, `wiper_thunk`, `clock_tick`, `clock_stop`, `watch_crack`, `bell_toll` (params: count), `thunder` (params: distance 0..1), `impact` (params: size 0..1), `braam`, `sub_drop`, `whoosh` (params: size), `whip`, `stinger`, `glass_ring`, `glass_break`, `gunshot_far`, `body_fall`, `badge_clatter`, `gavel`, `door_creak`, `door_open`, `door_close`, `cell_door`, `blinds_rattle`, `blinds_snap`, `metal_clang`, `land_thud`, `laundry_flap`, `tape_measure`, `handcuffs`, `chair_creak`, `drip`, `keys`.
Do **not** add music, voices, breaths or grunts — the score, rain beds and room ambience are laid globally by the sound designer from the ambience map in `docs/production-bible.md`.
