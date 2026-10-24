# The film-making system: a working manual

How the films in this repository are made, end to end: where everything lives, what each engine
module does, how a scene is written, timed, rendered, scored, checked and delivered, how the work
is split between the director and agents, and the traps we have already fallen into.

**Paths.** The production root is `productions/silhouette-noir/` (called ROOT). Paths in this
manual are relative to ROOT unless they start with `productions/`. Run every command from ROOT.

## Index

| Document | Read it for |
|---|---|
| [SYSTEM.md](SYSTEM.md) | This manual: layout, engine, scene contract, timing, render CLI, audio, QA, delivery, agents, gotchas. |
| [FILMS.md](FILMS.md) | Every film so far, in order: logline, structure, devices, what it introduced, where its files are. DOUBLE CROSS in depth. |
| [CRAFT.md](CRAFT.md) | How we direct: choosing stories, the visual language, how shots connect, camera, rhythm, sound, freedom and its limits, review. |
| [SHOT_TYPES.md](SHOT_TYPES.md) | The shot and transition vocabulary with timestamps, the reference shot types we adopted, adapted or skipped, and how each adopted type is built. |
| [../STYLE.md](../STYLE.md) | The trilogy's binding style contract (ten rules: silhouettes, fog, light, eyes, the one red, Bass graphics, camera, motion, texture, performance). |
| [../engine/API.md](../engine/API.md) | The scene author's API: contract, `SceneTiming`, `Frame` and camera, drawing, people, physics, render and QA commands. |
| [ANIMATOR_BRIEF.md](ANIMATOR_BRIEF.md) | The brief given to animator agents on the trilogy: read order, the bar, process, rules, final report. |
| Film bibles | `films/double_cross/docs/BIBLE.md`, `films/opposite_full/docs/BIBLE.md`, `films/salvage/docs/bible.md`, `films/shadowplay/docs/bible.md`, `films/red/docs/bible.md` (the trilogy also has `script.txt`). |
| `productions/nobody-has-a-face/README.md` | The first film (stickman noir). It has its own engine, bible (`docs/production-bible.md`) and tools. |

---

## 1. What the system is

- **Picture.** Every frame is drawn in Python: pycairo for vector shapes, numpy and OpenCV for
  compositing and post, ffmpeg for encoding. There is no image or video generation and no stock
  media.
- **Sound.** Score, foley and ambience are synthesised in numpy/scipy. There are two exceptions:
  - the narration of the narrated films (Nobody Has a Face and the trilogy), generated through
    Magnific with ElevenLabs Turbo v2.5;
  - fifteen generated recordings in `films/opposite/audio/gen/` (screams, gasps, breaths, steps,
    a handle, a mug smash, a quarrel), made through Magnific for OPPOSITE v3 and reused since.
- **A frame is a pure function of time.** A scene's `render(f, t, T)` draws scene time `t` with no
  state carried between frames. So frames can be rendered out of order in many processes, and a
  scene can be played backwards: DOUBLE CROSS s09 rewinds the film by calling earlier scenes'
  renderers at decreasing times.
- **Format.** 1080×1920 (9:16) at 24 fps: `W, H, FPS = 1080, 1920, 24` in `engine/core.py`. The
  social-UI safe area is `SAFE = (90, 240, 990, 1500)` (x0, y0, x1, y1).

## 2. Repository layout

```
stickman-video-director/
├── skills/directing-stickman-videos/   the upstream skill: stickman styles, narrative engine
├── productions/
│   ├── nobody-has-a-face/              film 1, stickman noir: own engine/, scenes/, audio/, tools/
│   └── silhouette-noir/                ROOT for everything below
│       ├── STYLE.md                    the trilogy style contract
│       ├── engine/                     the shared renderer and drawing kit (section 3)
│       ├── audio/                      shared sound: dsp.py (primitives, metering), sfx.py (catalogue)
│       ├── films/<film>/               one package per film (below)
│       ├── tools/                      deliver.py, qa_cuts.py, smoke.py
│       ├── assets/mocap/               CMU motion-capture clips (BVH) + README.md (credits)
│       ├── docs/                       ANIMATOR_BRIEF.md and these four documents
│       └── qa/                         engine test sheets (atmos/, bass/, creatures/, red_sets/); git-ignored
└── .gitignore                          .worktrees/
```

A film package, `films/<film>/`:

| Path | Contents |
|---|---|
| `scenes/sNN_<slug>.py` | One module per scene (section 4). The trilogy also has shared `scenes/_lib_<scenes>.py` files. |
| `timeline/build_timeline.py` | Writes `timeline.json` from the scene list (and, for narrated films, `vo_lines.json` + `vo_words.txt`). |
| `timeline/timeline.json` | The locked edit: scene starts, durations, transitions, handles, narration words. |
| `docs/` | The bible (`BIBLE.md` or `bible.md`), and `script.txt` for the narrated trilogy. |
| `audio/mix.py` | The film's score and mix. The trilogy splits it into `score.py`, `sfx_<film>.py`, `ambience.py`, `cuesheet.py`, `qa.py` and `vo/` (narration FLAC; the WAV is ignored). |
| film libraries | Shared drawing for the film's scenes: `kit.py` (palette and devices), `world.py`, `sets*.py`, `cast.py`, and in DOUBLE CROSS `plan.py`, `bank.py`, `faces.py`, `shots.py`. |
| `out/` | Renders: `scenes/`, `ranges/`, `seg_x1/` segments, `<film>_master.mp4`, `audio_master.wav`. Git-ignored. |
| `qa/` | Stills and contact sheets. Git-ignored. |
| `final/` | Delivered files. `*_preview.mp4` is git-ignored; SRT files are tracked. |

What git keeps (`productions/silhouette-noir/.gitignore`): code, docs, timelines, narration FLACs,
and only the mocap clips a film uses (force-added). Ignored: `out/`, `qa/`, `__pycache__/`,
`*.pyc`, narration WAVs, `films/*/out/`, `films/*/qa/`, `films/*/final/*_preview.mp4`,
`assets/mocap/*.bvh`.

### The films on disk

| `--film` | Length | Scenes | Scene joins | In `final/` |
|---|---|---|---|---|
| `salvage` | 3:01.5 (4,356 frames) | 16 | scroll, flatten, ink, whip, bars, dissolve, dip, cuts | `salvage.en.srt` only; never rendered to a preview |
| `shadowplay` | 2:33.5 (3,684) | 12 | flatten, shape (binocular, window), bars, slash, dip, tear, dissolve, cuts | `shadowplay_9x16_preview.mp4`, `shadowplay.en.srt` |
| `red` | 2:34 (3,696) | 11 | ink, dissolve, whip, flatten, flash, dip, cut | `red_9x16_preview.mp4`, `red.en.srt` |
| `lantern` | 0:26 (624) | 2 | iris | `lantern_test`, `lantern_bass_test`, `lantern_v2` previews |
| `opposite` | 0:34.5 (828) | 2 | cut | `opposite_test`, `opposite_v2`, `opposite_v3` previews |
| `opposite_bass` | 0:36 (864) | 1 | none | `opposite_bass_cut_preview.mp4` |
| `opposite_full` | 2:24 (3,456) | 11 | hard cuts | `opposite_full_preview.mp4` |
| `double_cross` | 2:24 (3,456) | 11 | hard cuts | `double_cross_preview.mp4` (v1), `double_cross_v2_preview.mp4` (v2) |

The `--film` choices come from `PALETTES` in `engine/palette.py`. (`engine/timing.py` also has a
`FILMS` tuple of five names; no tool reads it.)

---

## 3. The engine, module by module

| Module | Lines | Role | What you call |
|---|---|---|---|
| `core.py` | 276 | Constants, math, easing, keyframes, deterministic noise | `W, H, FPS, SAFE`, `ease`, `tween`, `Track`, `hash01`, `noise1`, `fbm1`, `noise2`, `noise_grid`, `pulse`, `spring`, `flicker`, `siren` |
| `frame.py` | 527 | The canvas, camera, layers, light, post-processing | `Frame`, `Camera`, `f.screen()`, `f.layer()`, `f.light()`, `f.emit()`, `f.post`, `f.finish()` |
| `timing.py` | 198 | Timelines and scene timing | `SceneTiming` (`T`), `Cue`, `build`, `summary`, `timeline`, `film_dir` |
| `render.py` | 474 | The renderer CLI, compositing, segments, QA images | `python3 -m engine.render` (section 6) |
| `transitions.py` | 907 | Composited scene-to-scene transitions | `apply(kind, A, B, u, t, **params)`, `shape_*` factories |
| `bass.py` | 2,176 | The Saul Bass kit: hand-cut titles, scissor-cut shapes, motifs, posterize, scene setup | `scissor`, `cut_rect`, `ring_pts`, `fill_polys`, `line_band`, `draw_title`, `bars`, `spiral`, `rings`, `binoculars`, `jagged_arm`, `pointing_hand`, `slash`, `heartbeat`, `loop_arrow`, `texture`, `poster`, `bass_scene` |
| `draw.py` | 267 | Low-level cairo path helpers | `poly`, `smooth`, `circle`, `circle_pts`, `ellipse_pts`, `capsule`, `cut_paper`, `cut_circle`, `glow_disc`, `resample`, `morph` |
| `paperdoll.py` | 433 | Cut-paper figures animated on ones | `Figure`, `Pose`, `Walker`, `Spring`, `ik2`, `woman`, `man`, `girl`, `standing` |
| `mocap.py` | 297 | CMU motion capture projected to a side view and retargeted onto paperdoll figures | `Clip.load`, `Seg`, `Performance` |
| `palette.py` | 149 | Film palettes | `Palette`, `PALETTES`, `RED`, `PAPER` |
| `figure.py` | 681 | The trilogy's silhouette rig with Limbo eyes | `figure.draw_eyes` and the rig |
| `costume.py` | 514 | The trilogy's costume shapes | e.g. `costume.helmet_inlet` |
| `motion.py` | 975 | The trilogy's `Actor` and gaits | `Actor.walk(speed=...)` (body heights per second) |
| `physics.py` | 196 | Verlet ropes and pendulums | `Rope`, `Pendulum` |
| `atmos.py` | 2,814 | Light, beams, particles, water, weather, fire | see its docstring |
| `creatures.py` | 4,787 | Wolf, spider, fish school, crows, cat, moths | `Wolf`, `Spider`, `FishSchool`, `Crow`, `CrowFlock`, `Cat`, `Moths` |

The trilogy used the whole engine. The Bass films (THE LANTERN onward) mostly use `core`, `frame`,
`timing`, `render`, `bass`, `draw`, `paperdoll`, `mocap` and `palette`.

### 3.1 `core.py`

- **Eases** (`core.EASES`): `linear`, `in`, `out`, `inout` (quadratic), `in3`, `out3`, `inout3`,
  `in5`, `out5`, `inout5`, `sine`, `outback`, `outelastic`, `outexpo`, `inexpo`, `step`.
  `ease(name, t)` clamps `t` and returns exactly 0.0 and 1.0 at the ends.
- `tween(t, t0, t1, a, b, e="inout")` holds outside its interval. `Track([(t, v), (t, v, ease)])`
  is a keyframe track; the ease on a key applies to the segment that ends at it.
- **Noise.** `hash01(*args)` is a deterministic float in [0, 1) from integers and floats (FNV-style).
  `noise1`, `fbm1`, `noise2` and `noise_grid` are seeded value noise. Never use unseeded `random`.
- **Envelopes.** `pulse(t, t0, attack, decay)` spikes and decays (flashes, impacts).
  `spring(t, freq, damping)` overshoots and settles. `flicker(t, ...)` is a light multiplier.
  `siren(t, rate, phase)` returns the (blue, red) double-flash strobe of a police bar.

### 3.2 `frame.py`

A `Frame(t, scale, pal)` owns a full-size ARGB canvas (`f.ctx`) and an emissive glow canvas at a
quarter of the resolution (`GLOW_DS = 4`). World units are frame px at zoom 1, y down.

- **Camera.** `Camera(x, y, zoom, rot)` with `matrix(scale)`, `shaken(t, amp, rot_amp, freq,
  seed)`, `parallax(par)`, `to_screen`, `to_world` and `view_rect`. Set it with `f.set_camera(cam)`.
- **Screen space.** `with f.screen() as c:` draws straight onto the canvas in 1080×1920 frame px
  (the matrix is just the preview scale). The Bass films draw everything this way and move their
  own "camera" with `c.translate` / `c.scale`.
- **Layers** (the trilogy's depth stack). `f.layer(par, blur, fog, fog_color, alpha, op)` draws
  into a temporary surface that is fogged toward `pal.fog_at(fog)` and blurred, then composited.
  `f.light(par, blur, alpha)` is additive light. `f.emit(par)` draws onto the glow canvas.
  `f.group(alpha, op, par)` composites a group. `f.fill`, `f.sky`, `f.sky_world`, `f.haze` and
  `f.darken` paint backgrounds.
- **Post (`f.post`)**, defaults in brackets: `grain` [`pal.grain`], `grain_fps` [24.0],
  `vignette` [`pal.vignette`], `bloom` [0.22], `bloom_threshold` [0.55], `glow` [1.0], `glow_sigma`
  [(1.4, 5.5)], `grade` [`pal.grade`], `fade` [0.0] with `fade_color` [black], `flash` [0.0] with
  `flash_color` [white], `flicker` [0.012], `poster` [None], `paper` [0.0], `exposure` [1.0].
- **`f.finish()`** composites, in this order:
  1. the glow canvas, blurred at two sigmas and scaled up ×4;
  2. bloom from bright areas (computed at 1/8 resolution);
  3. exposure, then the old-film exposure flicker;
  4. the poster flatten (Bass print): luminance bands mapped to flat inks, with saturated reds kept
     (`keep_red`, "the accent is sacred");
  5. paper fibres;
  6. the grade (per-channel lift, gamma and gain, as a LUT);
  7. the vignette;
  8. grain: one of 12 cached textures, changing `grain_fps` times a second, weighted toward
     mid-tones;
  9. **flash**, then **fade**: both mix the finished image toward a flat colour.

  Because flash and fade come after the grain, `f.post["flash"] = 1.0` gives a perfectly flat,
  grainless colour frame. The result is an H×W×4 uint8 BGRA array.

### 3.3 `bass.py` and the Bass scene setup

- Everything is a filled polygon with scissor-cut edges, a pure function of its arguments and
  integer seeds. Keep a seed constant over a shot and the edges never boil.
- Conventions (module docstring): draw in world coordinates; progress arguments `u`/`p` run 0..1
  and are clamped; `*_pts` return outlines, `*_path` add to the current path (for clips), plain
  names fill.
- Sections: fonts and hand-cut titles (`draw_title`, `title_glyphs`, built on the Inter Display
  Black font, roughened); scissor cuts (`scissor`, `cut`, `cut_rect`, `cut_ellipse`, `ring_pts`);
  animation helpers (`stagger`, `snap`, `slide`, `spin`, `pop`, `settle`, `on_twos`,
  `shuffle_step`); motifs (`bars`, `spiral`, `disc`, `ring`, `rings`, `iris_path`, `hole`,
  `binoculars`, `aperture`, `jagged_arm`, `pointing_hand`, `draw_cutout`, `draw_crowd`, `grid`,
  `triangles`, `panels`, `slash`, `heartbeat`, `loop_arrow`, `line_band`, `paper_field`, `tide`);
  `texture`; morphing (`morph_outline`, `outline_of`, `curl_pts`); `poster` presets.
- `bass_scene(f, field=PAPER, paper=0.75, grain=None, vignette=0.16, bloom=0.0, flicker=0.006,
  poster_amount=0.0, glow=None, mottle=0.0)` fills the field and sets the post for a printed look:
  paper fibres, light grain (`min(pal.grain, 0.045)` unless given), a whisper of vignette, no
  bloom, and optional ink mottling (`texture`).
- **Film setups.** DOUBLE CROSS `K.scene_setup(f, field=NAVY)` and OPPOSITE full
  `K.scene_setup(f)` (field INK) both call `bass_scene(..., paper=0.85, vignette=0.12,
  mottle=0.035, flicker=0.0)` and set `f.post["grain_fps"] = 12.0`: grain on twos, matching
  figures that move on twos.

### 3.4 `paperdoll.py` and `mocap.py`

- **Paperdoll.** A `Figure` is flat cut shapes (torso, head, hair, accessories) plus limb lengths;
  limbs are drawn each frame as tapered capsules between solved joints (`ik2`). `Walker(fig, x0,
  speed=[(t, px/s)], ...)` precomputes planted footfalls, swing arcs, pelvis bob and stride phase
  at 240 Hz (`HZ = 240.0`), so any frame is a lookup and feet never slide. `Spring` gives hair,
  scarves and coat tails overlapping action. Figures face +x; draw with `facing=-1` to flip.
- **Mocap.** `Clip.load("80_48")` reads `assets/mocap/80_48.bvh` (CMU, cgspeed conversion, 120 fps).
  `Seg(clip, src0, src1, at, speed=1.0, blend=0.25, travel=1.0, lean=0.0, near=None, mods={})`
  plays source seconds `src0..src1` from scene time `at`; `travel=0` keeps the root in place;
  `mods` override an arm. `Performance(fig, segments, facing=1, x=0.0, near="Right")` returns
  `(state, pose)` at `t`. Each frame is seen from the side of the performer's own smoothed
  heading, and arms are solved so the wrist lands where the actor's wrist was.
- **Clips in use** (`assets/mocap/README.md` credits them all): OPPOSITE used 09_01, 76_03, 86_04,
  120_15, 56_02, 56_03, 79_73, 80_48, 90_18, 137_26, 104_02 and 142_16. DOUBLE CROSS uses 104_02,
  16_08, 17_03, 17_08, 22_03, 23_03, 26_10, 77_05, 77_14 and 81_05.

### 3.5 `transitions.py`

`apply(kind, A, B, u, t=0.0, **params)` mixes the outgoing frame A and the incoming frame B at
linear progress `u` (each kind eases internally). Geometry is in 1080×1920 frame px, colours are
RGB 0..1, and each kind costs about 40 ms or less at full size (module docstring).

| Kind | What it does |
|---|---|
| `cut` | B. |
| `dissolve` | Cross-fade. |
| `ink` | An ink-bleed mask grows from A into B. |
| `iris` | A cut circle opens or closes. |
| `bars` | Bass bars sweep across (count, axis, sizes). |
| `shape` | A named path grows (`shape_circle`, `shape_triangle`, `shape_title`, `shape_spiral`, `shape_window`, `shape_binocular`); `invert` reverses it. |
| `scroll` | A and B slide as one strip (up, down, left, right). |
| `flatten` | A posterizes into flat inks, then B un-flattens. |
| `flash` | A fast build to a colour peaking at `at` (A swaps to B there), then a decay. |
| `dip` | Dip to a colour, hold, and out. |
| `whip` | A fast directional scroll with heavy motion blur. |
| `tear` | A torn-paper edge rips across. |
| `slash` | A cut-paper slash splits the frame. |

A transition is declared in the timeline (section 5). The renderer works out the window, renders
both scenes inside their handles and calls `apply`. Named shapes are built once per cut and cached.

### 3.6 `palette.py`

A `Palette` has `ink`, a sky, `fog_stops` (`fog_at(depth)`), `light`, `flame`, `accent` (RED),
`paper`, a `grade` (lift, gain, gamma), `grain` and `vignette`. `RED = (0.84, 0.10, 0.09)` and
`PAPER = (0.94, 0.91, 0.84)`. `opposite`, `opposite_bass` and `opposite_full` share the OPPOSITE
palette. The Bass films keep their working colours as named constants in the film's `kit.py`
(DOUBLE CROSS: `INK`, `PAPER`, `BLUE`, `NAVY`, `STEEL`, `DEEP`, `GOLD`, `POLICE`, `RED`).

---

## 4. The scene contract

A scene is `films/<film>/scenes/sNN_<slug>.py`. The renderer imports the first file matching
`sNN_*.py`.

| Function | Required | Meaning |
|---|---|---|
| `render(f, t, T)` | yes | Draw scene time `t` (seconds) into Frame `f`. `t` may be below 0 or at least `T.duration` inside transition handles. |
| `cues(T)` | no | A list of `engine.timing.Cue` for the sound. |
| `motion_blur(t, T)` | no | Sub-frames at time `t` (default 1). |

- **Cue.** `Cue(t, sfx, gain_db=0.0, pan=0.0, dur=None, **params)` returns a dict. `t` is scene
  time (rounded to 4 decimals), `sfx` is free text describing the sound, `pan` runs -1..1, `dur` is
  for sustained sounds. `python3 -m engine.render --film F --cues` prints every scene's cues on the
  film clock as JSON.
- **Motion blur.** When `motion_blur` returns n > 1, the renderer draws n sub-frames across a 0.5/24 s
  shutter, averages them in scene light (canvas plus glow) and finishes once, using the post of
  the sub-frame nearest `t`. Posterized frames are finished one by one and averaged, so their flat
  tones stay flat. The Bass films return 1: cut paper is crisp.
- **Missing scenes** render as grey slates showing the id, the slug and the time, unless
  `RENDER_PLACEHOLDERS=0`, which makes a missing module an error.
- **Determinism.** No state between frames and no unseeded randomness. Cache static geometry at
  module level or behind `functools.lru_cache`.
- **Budget.** About 1.5 s per full-size frame on one core (`STYLE.md` rule 10).

### The DOUBLE CROSS convention (also OPPOSITE full)

```python
"""sNN SLUG (film a-b). What happens, beat by beat."""
from engine.timing import Cue
from films.double_cross import kit as K

T_HIT = 3.5                       # beats: module-level constants in scene seconds

def motion_blur(t, T):
    return 1

def render(f, t, T):
    K.scene_setup(f, K.NAVY)      # field, paper fibres, grain on twos
    with f.screen() as c:         # frame px, 1080 x 1920, y down
        ...                       # a pure function of t

def cues(T):
    return [Cue(T_HIT, "a fist on the vault door: a huge muffled steel BOOM", gain_db=-4, pan=0.1)]
```

- Beats are module-level constants (`T_SLAM = 12.0`), so the mix and other scenes can import them.
  s07 also defines aliases for the mix (`T_BOOM = T_SLAM`, `T_SPLIT = T_X`, and so on).
- Shot lists are tables: `SHOTS = ((0.0, "match"), (2.85, "pound"), ...)` in s08, and the
  `render` dispatches on the time.
- Scenes import each other for continuity: s07 reuses s06's dial close-up (`S6.CU_DIAL`,
  `S6.TURNS`), s09 imports s02 and s03 and loads every scene it rewinds through by id (`_scene`),
  and s08's last frame is the first frame of s09 (s09's `FREEZES` holds s08 at 12.0, which s08
  draws with its `roll_shot`).
- **v2 scenes with inserts** keep their drawing in `render_plain(f, t, T)`, list their shots as
  `INSERTS`, and render with `S.play(f, t, T, render_plain, INSERTS)` (`films/double_cross/shots.py`;
  SHOT_TYPES.md, Part C). A scene that replays another calls its `render_plain` when it has one.
- Imports: `kit as K` (palette, devices), `plan as P` (the blueprint and the tilting camera),
  `cast as C` (figures), `faces as F` (profile close-ups), `bank as Bk` (the night sets).

---

## 5. Timelines and the beat grid

### 5.1 Building a timeline

Each film's `timeline/build_timeline.py` calls `engine.timing.build(film, scenes, place)`:

- `scenes` is `[(id, slug, duration_s, trans_out)]` in film order. Every duration must be a whole
  number of frames.
- `trans_out` is `None` (a hard cut) or `dict(kind=..., dur=..., align=0.5, **params)`. The window
  is `[cut - dur·align, cut + dur·(1 - align)]`. The outgoing scene's `handle_out` and the incoming
  scene's `handle_in` are derived from it.
- `place` maps each narration line to `(scene_id, scene_local_start)`. `build` refuses lines that
  overlap (they must be at least 0.25 s apart) and a last line that runs past the end of the film.
  Line and word times come from `vo_lines.json` and `vo_words.txt` (the narration take's word
  timings).
- The wordless films pass `PLACE = {}` with an empty `vo_lines.json`. DOUBLE CROSS is eleven scenes
  with `None` for every `trans_out`.

`timeline.json` holds `film`, `fps`, `duration`, `frames`, `vo_src`, `vo` (lines with word times)
and `scenes` (each with `id`, `slug`, `start`, `duration`, `frames`, `prev`, `next`, `trans_in`,
`trans_out`, `handle_in`, `handle_out`, `lines`, `words`). `engine.timing.summary(film)` prints it
as a table. Treat a locked timeline as read-only; agents never edit it.

### 5.2 `SceneTiming` (the `T` every scene receives)

| Attribute or method | Meaning |
|---|---|
| `T.duration`, `T.frames`, `T.start` | Length, frame count and film start of the scene. |
| `T.id`, `T.slug` | From the timeline. |
| `T.at(word, n=0)`, `T.end(word, n=0)` | Scene-local start and end of the n-th match of a narration word. |
| `T.line(n)` | `(t0, t1)` of narration line n. |
| `T.speaking(t, pad=0.0)` | Whether narration is playing at `t`. |
| `T.lines`, `T.words`, `T.text` | The narration overlapping the scene. |
| `T.trans_in`, `T.trans_out`, `T.handle_in`, `T.handle_out` | The transitions and the time rendered before 0 and after the end. |
| `T.prev`, `T.next` | Neighbouring scene ids. |

### 5.3 The beat grid

- Since the OPPOSITE Bass cut the wordless films are cut to **120 bpm**: a beat is 0.5 s and a bar
  2 s. DOUBLE CROSS exposes `K.BPM = 120.0` and `K.BEAT = 0.5`.
- **Scenes start on bar lines** (every DOUBLE CROSS and OPPOSITE full scene starts on an even
  second). The DOUBLE CROSS mix warns about any scene that does not.
- **Picture beats sit on the grid or on deliberate offsets**: DOUBLE CROSS s07's door BOOM is at
  scene 12.0 (film 92.0, a bar line); s10's police cars arrive on 4.0, 4.5, 5.0 and 5.5; s09's Plan
  B police cars arrive on half beats, 9.15–9.75.
- **Film-wide beats** live in the kit: `K.HEIST_T0 = 46.0` (the stopwatch starts) and
  `K.HEIST_STOP = 93.5` (it stops dead). `K.heist_beats(ft)` turns film time into ticks, one per
  beat, each a quick snap with an `outback` settle.
- **Film time = scene start + scene time.** Scene modules work in scene seconds; the mix converts.

---

## 6. The render CLI

`python3 -m engine.render [scenes] --film F [options]`, run from ROOT. Set `RENDER_WORKERS=1` when
several people share the machine; the default pool is one process per CPU.

| Command | Output |
|---|---|
| `--film F s03` | The scene alone, full size: `films/F/out/scenes/s03.mp4`. |
| `--film F s03 --scale 0.5` | Half size: `out/scenes/s03_x0.5.mp4`. |
| `--film F s03 --handles` | Including the transition handles: `out/scenes/s03_h.mp4`. |
| `--film F s03 --frames 24:48` | Only those scene frames. |
| `--film F s03 --times 1.0,2.5` | PNG stills at scene times (default scale 0.5): `films/F/qa/s03/s03_t001.000.png`. |
| `--film F s03 --sheet 12` | A contact sheet of 12 frames at the middles of 12 equal spans (default scale 0.25, 6 columns): `qa/s03_sheet.png`. |
| `--film F s03 --sheet 12 --window 4:6` | 12 frames evenly spaced from 4.0 to 6.0, both ends included: `qa/s03_sheet_4-6.png`. |
| `--film F --cut s03` | The transition into s03, composited, from 1 s before the window to 1 s after: `out/ranges/<t0>-<t1>_x0.5.mp4` (add `--sheet N` for a sheet). |
| `--film F --range 30:42` | Any film-time span, composited (default scale 0.5; 0.25 with `--sheet`). |
| `--film F all` | The whole film (section 6.1): `out/F_master.mp4`. |
| `--film F all --only s05,s06` | Re-render only the segments touching those scenes, then re-join. |
| `--film F all --force` | Re-render every segment. |
| `--film F --cues` | Every scene's cues on the film clock, as JSON. |

Other flags: `--out PATH` overrides the output; `--workers N` overrides `RENDER_WORKERS`. `--force`
only affects `all`: stills and sheets are always rendered fresh. Contact-sheet labels are QA only
and never enter the film.

### 6.1 How `all` works

1. `film_plan` walks every frame and asks `owner(film, t)` what is on screen: a scene `('s', sid)`
   or a transition `('x', a, b)`. Runs of the same owner become segments.
2. Each segment is encoded to `out/seg_x1/{k0:05d}_{label}.mp4` (libx264, CRF 15, preset medium,
   BT.709 tagged, yuv420p). Segments that already exist are kept unless `--only` touches them or
   `--force` is given. Segment files no longer in the plan are deleted.
3. The segments are joined with ffmpeg's concat demuxer and `-c copy` (no re-encode) into
   `out/F_master.mp4`.

With hard cuts only (OPPOSITE full, DOUBLE CROSS) there is exactly one segment per scene, so
`all --only s07` re-renders s07 alone.

---

## 7. The audio pipeline

### 7.1 Shared libraries (`audio/`)

- **`audio/dsp.py`** (1,123 lines): 48 kHz, stereo arrays `(n, 2)`. Oscillators, noise, envelopes,
  RBJ biquads and Butterworth SOS filters, Karplus-Strong, modal resonators, friction models,
  synthesised impulse responses (small room, office, hall, cell, alley, plate, car, court, street),
  convolution reverb, panning, saturation, compression, sidechain ducking, a true-peak look-ahead
  limiter, ITU-R BS.1770-4 loudness (integrated, short-term, momentary), 4× oversampled true peak,
  and WAV I/O.
- **`audio/sfx.py`** (1,667 lines): the procedural SFX catalogue first written for Nobody Has a
  Face. `render(name, dur, params, seed)` returns a sound at a reference loudness
  (`REF_LUFS = -16`) under a true-peak cap; a cue's `gain_db` then places it.

### 7.2 Narrated films (the trilogy)

- Each film's narration (Magnific, ElevenLabs Turbo v2.5) is one file,
  `films/<film>/audio/vo/narration_full.flac`. The WAV is decoded on demand and ignored by git.
- `timeline/vo_lines.json` and `vo_words.txt` give line and word times inside the take;
  `build_timeline.py` places each line on a scene. Scenes sync to words with `T.at(word)`.
- `audio/mix.py` (RED: 470 lines) places each narration line, mixes the score (`score.py`), a
  designed SFX cue sheet (`cuesheet.py`) merged with the scenes' `cues(T)` hints by keyword,
  ambience beds (`ambience.py`), ducks everything under the voice, and masters to **-14 LUFS**,
  true peak at most -1 dBTP. It writes `out/audio_master.wav`, stems, `audio_report.json` and
  `audio_overview.png` (RED's docstring; SALVAGE's mix declares the same targets).

### 7.3 Wordless films (OPPOSITE onward)

Each has one `audio/mix.py` that reads the scene modules and is the score, the foley and the mix at
once: LANTERN 169 lines, OPPOSITE 330, the Bass cut 298, OPPOSITE full 2,772, DOUBLE CROSS 5,862 (v3).
Every wordless mix targets **-16 LUFS**. The true-peak limiter's ceiling is -1.0 dBTP in LANTERN,
OPPOSITE and the Bass cut, -1.2 in OPPOSITE full and -1.3 in DOUBLE CROSS.

### 7.4 The DOUBLE CROSS mix in detail (`films/double_cross/audio/mix.py`)

**Commands** (from ROOT):

```
python3 films/double_cross/audio/mix.py                  # -> films/double_cross/out/audio_master.wav
python3 films/double_cross/audio/mix.py --qa DIR         # ... and the QA report, DIR/qa.json, DIR/overview.png
python3 films/double_cross/audio/mix.py --only s05,s07   # just these sections -> out/audio_only.wav (not mastered to the film)
python3 films/double_cross/audio/mix.py --stems DIR      # ... and the stems at the master's gain
python3 films/double_cross/audio/mix.py --without s06    # treat s06 as missing (played from the bible)
python3 films/double_cross/audio/mix.py --skip-missing   # leave missing scenes silent instead
```

**Output.** 48 kHz stereo, 24-bit PCM, exactly the timeline's 144 s, digital silence from s11's
`T_BLACK` (film 143.5) to the end.

**How a scene is played.** One `section(sid)` function per scene (`s01` … `s11`) places sounds
against that scene's beats.

- **Beat lookup.** Every beat a section uses is found in this order: the module's constant by name
  (`g(S, "T_SLAM", default)`); else the module's own cue whose words match, nearest the bible's
  time; else the bible's time.
- **Stand-ins.** A missing scene module, one that does not import, or one whose `cues()` returns
  nothing yet is played from the bible's beats and cues (`BIBLE_CUES`). `--skip-missing` turns this
  off.
- **Auto-spotting.** Any scene cue that no section answered within a frame is realised from its own
  words by `realize()` and reported. The words before a colon are read first, a set of
  percussive head words (`FOLEY_HEAD`: chalk, tap, tick, tock, clack, thud, clunk, whoosh, knock,
  scratch, ...) picks the sound, and cue gains are trimmed by `CUE_TRIM = -2.0` to the mix's
  levels. So a re-run after the scenes change still covers every cue.
- **Buses:** `music`, `hall` (the music's plate send), `efx`, `amb`, `vox`, `feet`, `tick`, `rew`.
- **Rooms.** `ROOMS` says which reverb each scene's foley sounds in, from which scene time.

**The voices** (v3). The takes are generated once and kept in `films/double_cross/audio/gen/*.mp3`.
`take(name)` decodes one with ffmpeg (mono, 48 kHz, cached), and `take_cut(name, a, b, fin, fout, rms)`
cuts and fades a slice, its loudest 0.3 s brought to an RMS. The grunts and the laugh are cut this
way and placed against their cues, like any foley.

The briefing's murmur is built so that it is never heard as words:

- `LINES` holds each voice's lines as (start, end) s in its take, with the words in comments for
  the record. `VOICE` holds each voice's low-pass and pan.
- `seams(x)` finds a line's syllable boundaries: the dips in its 25 ms level, at least 5 dB deep
  and 0.12 s apart.
- `murmur(who, k, fit, seed)` shuffles the syllables between the first and the last, preferring an
  order where no two neighbours stay side by side. It drops middle syllables until the line fits
  `fit` seconds, joins the pieces with 6 ms crossfades, high-passes at 110 Hz, low-passes at the
  voice's frequency and sets the RMS to -20 dBFS.
- `say(m, who, k, t, gain, fit)` puts the result on the `vox` bus in the scene's room and returns
  where it ends, so the next line can be placed from it.

Only the first line of each murmur cue is labelled. A labelled event claims every cue within a
frame of it, whatever its words, so an unlabelled line cannot claim another cue by accident.

**Mixdown** (`mixdown`): the music and its plate are ducked a little under the breath key (-4 dB);
the stems are summed; then `rewind_pass` builds the rewind.

**The rewind** (`rewind_pass`): for each row of s09's `REWIND` table it cuts the film's own
pre-master mix from the source span and resamples it (band-limited, `resample_poly`) into the
picture's time, reversed when the picture runs backwards. Rows the picture plays forward at about
real speed (`played()`: a speed ratio of 0.8–1.25) go in as they are, "the tape caught". The others
are low-passed at 9 kHz, levelled to -24 dBFS RMS (`REW_RMS`, at most +12 dB of gain) and placed
at `REW_GAIN = -5` dB.

**Mastering** (`master`): a 30 Hz high-pass; a 0.35 s fade into digital silence at 143.5; gain to
-16 LUFS; a true-peak limiter with a **-1.3 dBTP ceiling**, iterated up to five times until the
loudness is within 0.05 LU of the target.

**The score.** Heist jazz at 120 bpm in D minor, swing 0.64 (the off-beat eighth at 64 % of the
beat): walking pizzicato bass, brushes, vibraphone, Harmon-muted trumpets, a cup-muted trombone and
a low felt piano. THE THEME is four bars on the vibraphone; at the betrayal it returns as its exact
mirror inversion about D4 (Phrygian, low); in s09 the inversion is inverted again, upright, in D
major. A dry woodblock ticks every beat from 46.0 to 93.5 (`clock`). The bar-by-bar plan is the
module docstring.

**The QA report** (`--qa DIR`) prints:

- the file's length against the film's, integrated loudness, true peak, sample peak, clipped
  samples, and whether the tail is digitally silent;
- per scene: LUFS, short-term maximum and peak, with per-bus loudness at the master's gain, and the
  same per bus for the whole film;
- THE CLOCK: ticks measured on the tick bus against the ticks wanted;
- the loudest 1 s windows and the placements in them; the biggest peaks into the limiter;
- silences under -60 dBFS longer than 0.5 s;
- a click detector, placements cut off loud at their end, and the largest sample step near each
  cut;
- cue accounting: realised by the sections, auto-spotted, missed;
- sync: the worst cue-to-event offset and the measured onsets of labelled hits;
- music note starts on the swung grid (within 15 ms);
- the rewind rows and the largest sample steps at their joins.

It writes `DIR/qa.json` and `DIR/overview.png`.

**v1 numbers** (the delivered DOUBLE CROSS): -16.01 LUFS, true peak -1.30 dBTP, 0 clipped samples;
420 cues, 389 realised by the sections, 31 auto-spotted (all in s07), 0 missed; worst sync offset
20 ms; every scene played from its module.

**v3 numbers:** -16.01 LUFS, true peak -1.30 dBTP, 0 clipped samples; 449 cues, 421 realised by the
sections, 28 auto-spotted (all in s07: the two grunts are now claimed), 0 missed; worst cue-to-event
offset 25 ms, and no measured onset more than a frame out.

---

## 8. QA practice

We cannot watch video inside the session, so every check is an image or a number.

| Check | How | What it catches |
|---|---|---|
| Key stills | `--times` at scale 0.5–1.0, opened with the Read tool | Composition, hands, edges, readability at phone size |
| Motion | Dense sheets: `--sheet 16 --window a:b --scale 0.2` | Popping, foot sliding, jerky camera, unreadable arcs |
| Cuts | `--cut sNN --sheet 8`, or `tools/qa_cuts.py --film F` | Continuity across a join (outgoing last frame, three across the window, incoming first frame) |
| Red share | `tools/qa_cuts.py` writes `films/F/qa/red_share.json` | RED staying near or under about 8 % of the frame in live scenes (`STYLE.md` rule 5) |
| Smoke | `python3 tools/smoke.py --film F --scale 0.125` | Every scene imports, renders its edge frames (first handle, 0, middle, last, last handle) and returns cues; exit 1 on any failure |
| Glitch scan | A scratchpad tool, `glitch.py VIDEO [timeline.json] [--k 4.0]` (not in the repo) | Single-frame pops (a frame unlike both neighbours while they agree) and jumps (a difference above 2.5·k × the median and above 6), measured on 135×240 grey frames, skipping cut frames |
| Mix | `mix.py --qa DIR` (section 7.4) | Loudness, peaks, clicks, cut-off sounds, sync, missed cues, rewind joins |
| Frame grabs from a master | Scratchpad `vgrab.py VIDEO OUT CELLW COLS t...` (exact frames via ffmpeg `select`) and `mont.py out.png WIDTH files...` (one row; WIDTH is per tile) | Reviewing the delivered encode, not the renderer |

How we review:

- **Full size for anything that matters.** Hands, eyes, seams and small dots only show their faults
  at scale 1.0.
- **One glance per beat.** At phone size, can you tell what happened without the sound?
- **Every flag is explained.** DOUBLE CROSS v1's glitch scan raised 27 flags; each was checked and
  each was deliberate (cuts inside a scene, snaps, flashes).
- **Re-check the neighbours** after changing any scene that another imports (s06 → s07, s02/s03 →
  s09, s08 → s09, s10 → s11).

---

## 9. The delivery encode

1. **Picture master:** `python3 -m engine.render --film F all` → `films/F/out/F_master.mp4`
   (CRF 15 segments joined without re-encoding).
2. **Sound master:** `python3 films/F/audio/mix.py` → `films/F/out/audio_master.wav`.
3. **Preview** (OPPOSITE full, DOUBLE CROSS): a two-pass x264 encode at a fixed bitrate, muxed with
   AAC:

```
P=<scratch dir>/x264pass
ffmpeg -v error -y -i films/F/out/F_master.mp4 -map 0:v:0 \
  -c:v libx264 -preset slow -b:v 7500k -maxrate 11000k -bufsize 15000k -profile:v high -pix_fmt yuv420p \
  -pass 1 -passlogfile $P -an -f mp4 /dev/null
ffmpeg -v error -y -i films/F/out/F_master.mp4 -i films/F/out/audio_master.wav -map 0:v:0 -map 1:a:0 \
  -c:v libx264 -preset slow -b:v 7500k -maxrate 11000k -bufsize 15000k -profile:v high -pix_fmt yuv420p \
  -pass 2 -passlogfile $P -c:a aac -b:a 192k -movflags +faststart -shortest films/F/final/F_preview.mp4
```

Measured on the delivered DOUBLE CROSS preview: 1080×1920, 24 fps, 3,456 frames, 144.000 s, H.264
High at about 7.51 Mb/s, AAC-LC 48 kHz at about 199 kb/s, 7.71 Mb/s overall, 133 MiB (139 MB). After
the AAC encode it measured -16.1 LUFS with a peak of -0.6 dBFS.

**The trilogy's delivery script** is `tools/deliver.py --film {salvage,shadowplay,red}
video|audio|captions|mux|poster|qa|all`. `captions` writes `final/<film>.en.srt` (and an ASS file
in `out/`); `mux` writes a clean master (CRF 18) and a captioned social cut (CRF 20, burned-in
captions) as `final/<film>_9x16.mp4` and `final/<film>_9x16_captioned.mp4`. Captions exist only in
post, never in the master. `deliver.py` only knows those three films. The SHADOW PLAY and RED
files on disk are named `*_9x16_preview.mp4` (about 5 Mb/s video), not what `mux` writes: they
are the previews encoded when the trilogy was paused, with the sound not final (see FILMS.md).

---

## 10. The agent workflow

The director (the main session) writes the bible, builds the foundation, takes scenes itself,
reviews every frame before it is committed, and is the only one who commits. Agents take whole
scenes or the sound.

| Production | Agents | Notes |
|---|---|---|
| Nobody Has a Face | 6 animators + 1 sound | Three scenes each (S14–S15 as a pair); the director made S01, integration and delivery. |
| The trilogy | about 15 agents on 4 cores | Every animator renders with `RENDER_WORKERS=1`, mostly at scale 0.25–0.5. |
| OPPOSITE full | 3 scene agents + 1 audio agent | |
| DOUBLE CROSS | at most 2 at a time (the user's limit) | One animator for s04–s07 and one audio agent; the director made s01–s03 and s08–s11. |
| DOUBLE CROSS v2 (the shot types) | at most 2 in total | The director builds `shots.py` and wires it; a documentation fork writes these docs. |

Rules that came out of it (most are in `ANIMATOR_BRIEF.md`):

- **Own only your files**: your scene modules and your own `_lib_` file. Never edit the engine,
  `cast.py`, sets, the timeline, the bible or anyone else's scene. If a shared module lacks
  something, work around it locally and report it.
- **No state-changing git.** The director reviews frames, then commits. The session's automatic
  safety check also refused to commit agent files that had not been reviewed.
- **`RENDER_WORKERS=1`** when sharing the machine.
- **Determinism**: frames render out of order in many processes.
- **Shared `_lib_` files take targeted edits only.** A whole-file write from a stale copy once
  deleted another scene's exports (RED `_lib_s02_s06.py`, restored in `caa575b`).
- **The final report is the only thing the director reads**: files, beats with times, the exact
  first- and last-frame states, cues, the best QA image paths, seconds per frame, known issues.

---

## 11. Gotchas

| Trap | What happens | Fix |
|---|---|---|
| A zero scale in a cairo transform | `cairo` raises an invalid-matrix error and the frame fails. It happened in s09 `_cops_b` at `t = T_COPS[3] = 9.75`. | Skip the draw: `if k <= 0.0 or g < 1e-3: continue` (s09 line 321). |
| `K.dot` with a small radius | It returns without drawing when `r <= 0.3` (`films/opposite_full/kit.py`, `dot`), so dots vanish inside a scaled-down transform. | Fill `draw.circle_pts` / `bass.ring_pts` directly at that scale. |
| `bass.line_band` on a chalk outline | It resamples at fixed arc steps and rounds corners and small circles. | `K.band_pts` keeps every vertex and mitres the corners. |
| Big circles look polygonal | Scissor-cut must never look low-poly. | Use `n=48..96` facets (the keyhole lesson). |
| `Actor.walk(speed=...)` | The unit is body heights per second, not px/s; px/s teleports the actor. | Convert. |
| Whole-file writes to shared files | They silently drop other people's code. | Targeted edits only. |
| `--force` on stills or sheets | Does nothing: only `all` uses it. | Nothing to fix; stills are always fresh. |
| `tools/smoke.py` with no `--film` | It checks only the trilogy. | Pass `--film double_cross`. |
| `mont.py WIDTH` | WIDTH is per tile, not the whole row. | Size by tile. |
| Relative paths in agent shells | The working directory drifts between calls. | Use absolute paths. |
| A scene another scene imports | Changing s06's dial, s02/s03 or s08's last frame changes s07 or s09 too. | Re-render and re-check the importer. |
| The bible versus the code | Where they differ, the code is what renders and what the mix reads (for example, the bible's loudness note says true peak -1 dB; the master's ceiling is -1.3 dBTP). | Quote the module constants. |
