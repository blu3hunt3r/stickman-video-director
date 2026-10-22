# Silhouette Noir engine: API for scene authors

You are writing a **scene module**, `films/<film>/scenes/sNN_<slug>.py`. The engine is
small and readable, so read the source of anything you use. Style rules are in
`STYLE.md`. Your scene's story beats, timing and handoff contracts are in
`films/<film>/docs/bible.md`.

## 1. Scene contract

```python
"""s05 · THE MERIDIAN: one-line description."""
from engine.frame import Camera
from engine.motion import Actor
from engine import atmos, draw
from films.salvage import cast, sets          # your film's cast and sets

def render(f, t, T):        # required. f: Frame, t: scene seconds, T: SceneTiming
    ...

def cues(T):                # optional: sound cues for the sound team
    return [Cue(T.at('tugs'), 'line tug', gain_db=-3)]

def motion_blur(t, T):      # optional: sub-frames (1 = none) for fast moments
    return 3 if 5.0 < t < 5.6 else 1
```

**Rules:**

- **Handles.** `render` must work for `-T.handle_in <= t < T.duration + T.handle_out`.
  - Transitions are composited from both scenes' handles, so keep the world animating naturally there.
  - Clamp keyed animation, but keep particles, water and drift moving.
- **Pure function of `t`.** No state between calls: frames render in any order, in several processes.
  - Build expensive objects (Actors, Ropes, cached geometry) once at module level or in a `functools.lru_cache` function. Ropes and Pendulums cache their own simulation.
- **Performance.** At scale 1.0 a frame should take 1.5 s or less on one core. Most layers in this film are cheap. Blurred layers cost about 30–60 ms each.
- **Palette.** `f.pal` is the film's palette. Use `pal.ink`, `pal.fog_at(d)`, `pal.light` and the palette's named lights. `RED` and `PAPER` come from `engine.palette`.

## 2. Timing: `engine.timing.SceneTiming` (passed as `T`)

| Attribute / call | Meaning |
|---|---|
| `T.duration`, `T.frames` | Scene length |
| `T.start` | Film time of the scene's frame 0 |
| `T.handle_in`, `T.handle_out` | Seconds rendered before 0 and after the duration |
| `T.trans_in`, `T.trans_out` | Transition dicts (`kind`, `dur`, …), or None |
| `T.at('word', n=0)`, `T.end('word')` | Scene-local start/end of the n-th occurrence of a narration word. Includes lines from neighbouring scenes that reach into the handles, so check `T.lines`. |
| `T.line(n)` | `(t0, t1)` of narration line n, scene-local |
| `T.lines`, `T.words` | Raw lists |
| `T.speaking(t, pad)` | True while the narrator speaks |

`Cue(t, sfx, gain_db=0, pan=0, dur=None, **params)` is a sound cue at scene time t. `sfx`
is a short description, e.g. `'helmet clank'` or `'knife slash'`.

## 3. Frame and camera: `engine.frame`

```python
f.set_camera(Camera(x, y, zoom=1.0, rot=0.0))   # world point at screen center
cam.shaken(t, amp=3, rot_amp=0.2, freq=1.3, seed)   # handheld drift
f.sky(top, bottom, mid=None, mid_at=0.5)         # screen-space gradient
f.sky_world([(world_y, rgb), ...], par=0.0)      # world-anchored gradient (depth zones)
with f.layer(par=0.4, blur=6, fog=0.7) as L: ... # depth layer: draw in ink, it gets fogged and blurred
with f.layer() as L: ...                         # action plane (sharp, pure ink)
with f.layer(par=1.6, blur=18) as L: ...         # foreground occluder
with f.light(par=1, blur=8, alpha=1) as A: ...   # ADDITIVE light (rays, beams, glows)
with f.emit(par=1) as G: ...                     # emissive cores (eyes, bulbs, embers) -> bloom
with f.group(alpha=0.5) as Gp: ...               # offscreen group with alpha
with f.screen() as S: ...                        # screen-space drawing (1080x1920)
f.haze(color, alpha, y0, y1, feather, tex, tex_scale, scroll, seed, par, screen, x0, x1)
f.darken(alpha, y0, y1, ...)
f.post[...]   # grain, vignette, bloom, bloom_threshold, glow, grade, fade, fade_color,
              # flash, flash_color, flicker, poster (Bass flatten), paper, exposure
```

- `par` is parallax: 1 is the action plane, below 1 is farther, above 1 is nearer.
- Layers draw in **world** coordinates through the parallax camera. The camera rotation applies to all layers.
- `Frame.finish()` is called by the renderer: do not call it in a scene.

## 4. Drawing: `engine.draw` (cairo helpers; path builders, then `fill`/`stroke`)

- **Paths:** `poly`, `smooth` (Catmull-Rom), `circle`, `ellipse`, `rect`, `capsule(a, b, ra, rb)`, `chain(pts, radii)`, `ribbon(pts, widths)` → polygon points.
- **Point lists:** `circle_pts`, `ellipse_pts`, `transform_pts`.
- **Bass paper edges:** `cut_paper(pts, seed, amp, seg)` and `cut_circle(c, r, seed)` (deterministic scissor-cut polygons).
- **Morphing:** `resample(pts, n)` and `morph(a, b, t)` (outline A → outline B).
- **Fill styles:** `linear`, `radial`, `glow_disc(ctx, c, r, rgb, a, core)`.
- **Painting:** `fill(ctx, rgb, a)`, `stroke(ctx, rgb, width, a)`.

`engine.core` provides:

- constants `W, H, FPS, SAFE`;
- math: `clamp`, `lerp`, `inv_lerp`, `remap`, `smoothstep`;
- easing: `ease(name, t)` and `tween(t, t0, t1, a, b, e)`. Ease names: linear, in, out, inout, in3, out3, inout3, in5, out5, inout5, sine, outback, outelastic, outexpo, inexpo, step;
- `Track([(t, v, ease), ...])` keyframes;
- deterministic noise: `hash01`, `noise1`, `fbm1`, `noise2`, `noise_grid`;
- signal helpers: `flicker`, `siren`, `pulse`, `spring`.

## 5. People: `engine.figure` + `engine.costume` + `engine.motion`

Characters come from your film's `cast.py`:

```python
from engine.motion import Actor
from films.salvage import cast
diver = Actor(cast.DIVER, cast.diver(), x=300, ground=sets.seabed_y, facing=1, t0=0.0, seed=3)
diver.stand(dur=1.0).walk(to=800, gait="heavy").stand(until=6.0).turn(yaw=90, dur=0.6)
diver.reach("R", 4.0, 5.5, target=lambda t: knob_pos(t), grip=0.8)
diver.look_at(2.0, 4.0, target=(900, 1200))
diver.key("spine", [(6.0, 0, "inout"), (6.4, 25, "out3")], mode="add")
diver.draw(f, t, L)                       # draw on the action-plane layer ctx
sk = diver.skeleton(t); diver.joint(t, "wrist_R"); diver.root(t)
```

**Facing / yaw:**

| yaw | Direction |
|---|---|
| 0 | facing right |
| 180 | facing left |
| 90 | toward the camera |
| −90 | away from the camera |

`facing=1` means yaw 0 and `facing=-1` means yaw 180. Turns blend through 3/4 views.

**Ground:** a y value or a function `ground(x)`. Feet plant exactly on it: heel-to-toe
rocker contact on slopes, no sliding.

**Segment methods.** Each chains from the previous segment's end, or starts at `at=` seconds:

| Method | Notes |
|---|---|
| `stand(dur / until, idle, crouch)` | |
| `walk(to, gait, speed, path, yaw, turn)` | |
| `run(...)` | |
| `sneak(...)` | |
| `turn(yaw, dur, via)` | |
| `face(yaw)` | |
| `jump(to, height, dur)` | |
| `free(dur, path(t) → (x, y), pose(t, u) → Pose)` | Free-form motion: floating, falling, climbing. Build Poses by hand or modify `dangle(...)`. |

**Gaits** (`engine.motion.GAITS`): walk, stroll, brisk, sneak, run, sprint, child_walk,
child_run, old, heavy (diver suit), trudge (deep snow).
`gait("walk").but(step=0.35, speed=0.5)` makes a variant.

**Layered channels** (`set` or `add`, with fades):

- `key(name, keys)`, `channel(name, fn, t0, t1)`;
- `arm(side, t0, t1, sh=, abd=, elbow=, wrist=, grip=)`;
- `pose_keys(t0, t1, pitch=, spine=, neck=, head=, head_yaw=, ...)`;
- `reach(side, t0, t1, target)` (2-bone IK; target is a point or a function of t);
- `look_at(t0, t1, target | 'camera')`;
- `eyes(t0, t1, open=, glow=, look=)`;
- `blink(t)`.

Channel names: pitch, spine, spine.N, neck, head, head_yaw, head_roll, yaw, x, y, scale,
arm.S.(sh|abd|elbow|wrist|grip), leg.S.(hip|abd|knee|ankle|toe),
foot.S.(x|y|pitch|toe), eyes.(open|glow|look), extra.*.

**Sagittal angles** are degrees measured from straight down toward the body's forward
direction (+ = forward). Spine and pitch: + bends forward.

**Look options** (`costume.py` docstring):

| Option | Values |
|---|---|
| hair | short, slick, bob, long, bun, ponytail, curly |
| hat | fedora, peaked, flatcap, watch, kerchief, bowler |
| hood | True |
| cape | capelet, cloak, long |
| coat | jacket, trench, long |
| dress | knee, mid, floor |
| scarf | True |
| helmet | `'diver'` |
| beard | True |
| colors | `{part: rgb}` |
| opts | glass, weights, flow, collar |
| paper | True (paper-doll puppet) |
| extras | callables `(ctx, sk, f, look)` |

**Helpers:**

- `costume.helmet_frame(sk)`, `helmet_inlet(sk)` (hose attach point), `helmet_lamp(sk)` → `(pos, dir, facing)`, `leg_point`.
- `figure.head_point(sk, hx, hy)` and `figure.eye_points(sk)`.
- `figure.draw_figure(f, sk, look, ctx, color=None, eyes=True, alpha=1)` draws a skeleton directly (e.g. a shadow: pass `color`, `eyes=False`).

**Scale:** an adult is about 600 px tall at zoom 1, and a 7-year-old 380 px. For a figure
far away, use the Actor's `scale=` or draw on a farther layer.

## 6. Physics: `engine.physics`

- `Rope(n, length, a(t), b(t)|None, t0, t1, gravity, drag, current(t, x, y), collide(x, y) → y_max, length_fn(t), release(t) → bool, stiffness 0..1, init)`.
  - `.points(t)` → node list a → b; `.tension(t)` → stretch ratio.
  - Use it for the air hose, lifting line, threads, web strands and cables.
  - Simulated once per process from t0 at 120 Hz, then cached.
- `Pendulum(pivot(t), length, t0, t1, damping, gravity, theta0, kick(t))`, with `.angle(t)` and `.bob(t)`. Use it for a lamp swinging from a hand, a bell, or a hanging doll.

Both are deterministic. Set t0 to at least `-T.handle_in - 1` so the simulation is settled
when the scene starts.

## 7. Rendering and QA (run from the production root)

```bash
RENDER_WORKERS=1 python3 -m engine.render --film salvage s05 --sheet 12          # contact sheet
RENDER_WORKERS=1 python3 -m engine.render --film salvage s05 --times 0,3.2,7.5   # stills
RENDER_WORKERS=1 python3 -m engine.render --film salvage s05 --scale 0.5         # preview mp4
RENDER_WORKERS=1 python3 -m engine.render --film salvage s05 --scale 0.5 --handles
RENDER_WORKERS=1 python3 -m engine.render --film salvage --cut s05 --scale 0.5   # transition in
python3 -m engine.render --film salvage --cues                                   # all cues, JSON
```

Outputs go to `films/<film>/qa/` and `films/<film>/out/` (both git-ignored). Look at your
frames with an image viewer (the Read tool) and iterate. Scenes that don't exist yet
render as grey slates, so the whole film can always be assembled.

## 8. Shared libraries (see each module's docstring for the full API)

- `engine.atmos`: light shafts, volumetric beams, lamps and flicker, particles (snow, rain, bubbles, marine snow, dust, embers), the water surface, waterline and caustics, lightning, moon, ground mist, fire and burning lines, underwater depth color.
- `engine.bass`: Saul Bass kit. Hand-cut titles, motifs (bars, spiral, rings, jagged arm, pointing hand, cut-out figures, grids, triangles, slash, loop), stagger/snap animation helpers, shape morph, posterize presets.
- `engine.transitions`: `apply(kind, A, B, u, t, **params)`, used by the renderer from the timeline. Scenes do not call it.
- `engine.creatures`: wolf, giant spider, fish school, birds, cat.
- `films/<film>/sets*.py`: each film's sets and props, with ground functions and anchor points.
