# Shot types and transitions

The shot vocabulary of these films: what we already had (Part A), what we took from the reference
edit the user shared on 10-24 and what we left (Part B), and how each adopted type is built in code
for DOUBLE CROSS v2 (Part C).

Film times are m:ss.ss (film seconds); "local" means scene seconds. Paths are relative to
`productions/silhouette-noir/`. A bare `sNN` is a DOUBLE CROSS scene; a scene of any other film
carries the film's name. In DOUBLE CROSS, scene modules are `films/double_cross/scenes/sNN_*.py`
and `K`, `P`, `C`, `F`, `Bk`, `S` are `kit`, `plan`, `cast`, `faces`, `bank` and `shots`.

---

## Part A. The vocabulary we already use

### A.1 Shots

| Shot | What it is | Examples | Built with |
|---|---|---|---|
| **Profile cameo** (silhouette on a bold field) | A face in profile, cut like a cameo, alone on one flat colour | DOUBLE CROSS s02: her on the lamp's gold (0:13.5–0:15.5), the Cracker on steel (0:16.5–0:18.5), the Knight in the dark lit by his ember (0:19.5–0:21.0). OPPOSITE Bass cut: her sip on her window's amber (0:05.6). OPPOSITE full s05: her profile and his, mirrored across a red split (0:57.5) | `F.her`, `F.cracker`, `F.knight` (each returns its landmarks in frame px: eye, mouth, nose and ear, or the Knight's cigarette tip in place of the ear); s02 `face_shot`; OPPOSITE `films/opposite_full/gaze.py` |
| **Extreme close-up on a mechanism** | A dial, a lock, a hand, filling the frame | s06 the dial with the lock cut away beneath it (1:09.0–1:16.0); s07 the same dial in RED, the lock run backwards (1:32.2–1:33.0; from 1:32.29 in v2); OPPOSITE full s09 the rotary dial from above (1:49.0–1:54.0) | s06 `closeup`, `Bk.dial_face`, `Bk.lock_cutaway`; s07 `shot_dial` |
| **Hand insert** | A hand doing the one thing that matters | s02 the three hands setting the pieces (0:13.0, 0:16.0, 0:19.0); s11 her fist opening on the ruby (2:16.55–2:18.45); OPPOSITE full s09 the victim's fingers closing on hers (1:47.85) | `F.hand`; s11 `palm_shot` |
| **The plan, top-down** | The blueprint seen straight down, pieces as discs or standing | s03 the whole glide (0:24–0:40); s05 the stealth map (0:56.0–1:00.5); s07 his red L (1:33.0–1:36.0); s09 Plan B (1:54.6–1:58.9); s10 the city as a chessboard (2:06.92–2:16.0) | `P.PlanCam(cx, cy, zoom, phi, yaw)`, `P.draw_plan`, `P.draw_plan_a`, `P.draw_pieces`, `K.route`, `K.circled`; s10 `board_shot`, `draw_board` |
| **The tilt** (plan ↔ world) | One camera tilting between the diagram and the place | s01 up off the night street to the plan as the street folds flat (v3, 0:02.75–0:04.0); s01 → s02 down to the table (0:10.55–0:12.0); s03 → s04 down into the street (0:38.0–0:43.0, the walls rising out of their chalk lines on the way down); s05 up to the map and back (0:56.0–0:57.0, 1:00.5–1:01.5) | `PlanCam.lerp`, `P.draw_walls_3d`, `P.HANDOFF_34`; s04 `tilt_cam`; s05 `_tilt` |
| **Elevation** (a set seen side-on) | The night world as a flat stage | s01 the bank's front at night (v3, 0:00–0:02.75); s04 the front street (0:43.0–0:45.75); s05 the corridor (0:52.0–0:56.0, 1:01.5–1:06.0); s06 the vault door (1:06.0–1:09.0, 1:16.0–1:20.0); s10 the street (2:04.0–2:05.46) and, in v3, the back street looking north (2:11.2–2:13.5) | `Bk.front_street`, `Bk.corridor`, `Bk.vault_door`, each placed by `Bk.Cam(x, y, zoom)`; s10 `escape_shot`, `_back_street` |
| **Section** (the ground cut open) | A cutaway through the street or floor | s04 the street opens into the sewer (0:45.75–0:47.1); s08 the floor opens under her heel (1:42.25–1:42.85); s09 down through the trapdoor (from 2:00.66); OPPOSITE full s07, both buildings cut open for the race (1:16–1:30) | s04 `_cut`, `Bk.sewer`; s08 `floor_shot`, `_section`; OPPOSITE `K.draw_section` |
| **Split screen** | The frame cut into panels that run at once | s07 the X-split, the frame cut on both diagonals into four triangles (1:26.0–1:30.26); OPPOSITE full s05 the mirror split down a red line (0:57.5–1:00.0) | `K.x_split(c, panels, ...)`; s07 `shot_x`, `x_out` |
| **Over the shoulder** | A head and shoulders filling one side, the subject through a window | OPPOSITE full s02, hers (0:22.0); s10, his, the mirror of it (2:01.5) | OPPOSITE scenes |
| **POV** | What a character sees, shaped by what they see through | OPPOSITE full s08 through the keyhole (1:39.0–1:42.5); the Bass cut's keyhole (0:31.5) | OPPOSITE scenes |
| **Callout lens** | A detail magnified in a ring on a leader line | s01 the gold under the landed X (v3, from 0:11.1); s02 face → piece; s03 steps ① and ③ (v3: manhole A's lid 0:25.05–0:26.3, the guard and his light 0:29.55–0:30.75) and the dial (0:31.0–0:32.06); s08 the heel's dot → the plan (1:43.25); s09 the dot (from 1:51.55) and her eye (from 1:54.05); s10 manhole B in v1–v2 (2:11.85–2:13.85; v3 cuts to the back street instead); OPPOSITE full s07 the near miss (1:18.3–1:19.9) | `K.callout(c, anchor, center, r, inside, u=1.0, ...)`, defined in `films/opposite_full/kit.py` and re-exported by the DOUBLE CROSS kit |
| **Freeze** | A held frame with a lens snapping onto it | s09: 1:48.0–1:48.15, 1:51.5–1:52.2, 1:54.15–1:54.6 | s09 `FREEZES`, `shown` |
| **Rewind** | The film running backwards under chalk streaks and a double chevron | s09 1:48.15–1:50.75 and 1:52.2–1:52.45 | s09 `REWIND`, `shown` and its own `_rewind_marks` (streaks, chevrons, the heist clock running back; the kit's `K.rewind_marks` is not called anywhere); the earlier scenes' own `render_plain` at decreasing times |
| **Light fills the frame** | A light grows until it is the whole frame, and we come out of it elsewhere | s10 the headlight (2:06.68–2:06.92) into the chessboard | s10 `nose_shot` |
| **Black** | A cut to black as punctuation | s07 after the BOOM in v1 (1:32.0–1:32.2; v2 fills it, see Part C); s11 the end (2:23.5) | s07 `Bk.fill_all(c, K.INK)`; s11 `K.fill(c, K.INK)` with the red dot (`_dot`) drawn over it |
| **Title graphics** | Hand-cut letters and strips | DOUBLE CROSS s01 (0:08.0–0:11.0) and its reprise in s11 (2:21.5–2:23.0); OPPOSITE's bars, letters and red slash | s01 `_strips`, `_words`; `bass.draw_title`, `bass.bars`, `bass.slash` |

### A.2 Camera moves and accents

| Move | Use | Examples |
|---|---|---|
| **Glide** | Follow the action continuously | s03 follows her chalk (0:24–0:40); s07 after the red knight (1:33.3–1:35.5) |
| **Push-in** | Lean into the beat; eased | s05 down the corridor to the dial (1:04.8–1:05.75); s06 onto the gold (1:17.2–1:20.0); OPPOSITE full s01 into her room, ending at zoom 3.2 on the section (0:10.5–0:12.0, `rooms.S01_END`) |
| **Jump in on the beat** | A cut closer, timed to the music | OPPOSITE full s03, the quarrel (`JUMPS`, from 0:27.5); OPPOSITE full s05 onto him (0:53.5) and into her window (1:01.5); OPPOSITE full s09 onto her eye (1:55.5) |
| **Pull-back** | Reveal the whole situation | s09 off the red X to both plans (v3, 1:58.58–1:58.8); s10 from his face back to the board, where manhole B opens (v1–v2, from 2:11.2; v3 cuts to the back street first and returns to the board at 2:13.5); OPPOSITE full s10 to the whole block (2:12.5–2:15.5) |
| **Whip** | Follow a look or jump between marks | s08 down after her glance (1:41.1–1:41.35, `whip_shot`); s09 between Plan B's marks; OPPOSITE (`films/opposite`) s02, back to her as the mug falls |
| **Dive** | Fall into an eye or reflection (Vertigo) | OPPOSITE full s03 into her eye's reflection (0:35.5); OPPOSITE full s08 into his pupil at the keyhole (1:38.45) |
| **Roll (Dutch)** | Panic, once per film | OPPOSITE full s04 to -7° (from 0:44.6); DOUBLE CROSS s10 (2:10.0–2:10.42) |
| **Shake** | An impact | s08 with each blow on the door (1:38.85, 1:39.3, 1:39.75) |

### A.3 Joins between shots inside a scene

OPPOSITE full and DOUBLE CROSS have no composited scene transitions: every scene join is a hard cut
on the beat, and the transitions happen inside the scenes.

| Join | Example |
|---|---|
| **The world folds into the plan** | v3 s01: the night street folds flat, back to front (s04's pop-up run backwards), as the camera tilts up, and the bank's chalk outline lies down onto the blueprint that was under the street all along (0:02.5–0:03.95). |
| **Match on a point** | The title X lands on the vault (0:11.0) and becomes the plan's chalk X; s07's red dial shrinks to a lens on the plan's chalk dial in the same place (1:33.0–1:33.32). |
| **Camera carried across the cut** | s03 ends tilting at 15°/s; s04 starts from `P.HANDOFF_34` at the same rate (0:40.0). |
| **The last frame held** | s09 opens on s08's last frame, held (`FREEZES[0]`: s08 at 12.0, drawn by s08's own `render_plain`, 1:48.0–1:48.15), then runs it backwards. |
| **Split along a shape** | s11 splits s10's last frame along its X and the four triangles fly off (2:16.0–2:16.62, s11 `_split`). |
| **Panels fly off** | The X-split's panels fly away and the bottom one becomes the frame (1:30.0–1:30.26, s07 `x_out`). |
| **The window becomes the frame** | OPPOSITE full s03: along her look into his window until it is the room (0:26.0–0:27.5). |
| **Iris out of a shape** | THE LANTERN: the title's flame opens into the forest (0:06.0). |
| **Out of a light** | s10's headlight whites out into the chessboard (2:06.92). |

### A.4 Composited scene transitions (`engine/transitions.py`)

Used by the narrated trilogy and THE LANTERN, declared in each film's timeline (`trans_out`) and
composited by the renderer from both scenes' handles (SYSTEM.md, sections 3.5 and 5).

| Kind | Used at |
|---|---|
| `scroll` | SALVAGE 0:10.0 (down, 1.5 s), 0:25.0 (up), 2:05.0, 2:14.5, 2:25.5 |
| `flatten` | SALVAGE 0:39.0; SHADOW PLAY 0:09.0; RED 1:21.0 |
| `ink` | SALVAGE 0:53.0; RED 0:09.0 |
| `whip` | SALVAGE 1:06.5; RED 0:52.0 (both 0.5 s, left) |
| `bars` | SALVAGE 1:26.0 (7 vertical bars); SHADOW PLAY 0:52.5 (2 horizontal) |
| `dissolve` | SALVAGE 1:45.0; SHADOW PLAY 2:21.5; RED 0:24.0, 0:38.0, 1:06.5, 2:05.0 |
| `dip` | SALVAGE 2:45.5 (2 s to black); SHADOW PLAY 1:46.5 (black); RED 2:19.0 (2 s to white) |
| `shape` | SHADOW PLAY 0:24.0 (binocular, inverted), 1:19.5 (a window) |
| `slash` | SHADOW PLAY 1:06.5 |
| `tear` | SHADOW PLAY 2:11.5 |
| `flash` | RED 1:51.0 (1 s, warm white, out of the fire) |
| `iris` | THE LANTERN 0:06.0 (open, centre (540, 1040)) |

---

## Part B. The reference edit: adopt, adapt or skip

On 10-24 the user pasted a description of a reference edit and asked whether we wanted to use any of
it. It listed six shot types (a silhouette over a bold background; an extreme close-up with speed
lines and shake for 4–6 frames; a manga cut-out over a new background; a flash frame of 2–6 frames
of flat colour with a sound word; a storm panel; a glitch of 1–4 frames), noted that its cuts land
one frame before the beat, and named four transitions (rings blooming onto the title; red dots
flooding the screen; the storm shrinking into the sun; dissolving to blank paper dot by dot).

The test for each item: does it come from this film's own materials (paper, chalk, light, its
palette), and does it serve a beat that is already there? DOUBLE CROSS is wordless, cut paper, and
spends RED on one person.

| Reference item | Verdict | What we do instead, and why |
|---|---|---|
| **Silhouette over a bold background** | **ADOPT** (already ours) | It is the profile cameo (Part A): s02's three faces each alone on one flat colour. New in v2: at the slam, five frames of the Knight black on a red sunburst, held in the lunge that shut them in (1:32.08). |
| **Extreme close-up with speed lines and shake, 4–6 frames** | **ADAPT** | Five-frame punch-ins on four hits. No manga speed lines: cut-paper wedges rush in from the frame's edges (Bass's radiating strips). The scene is re-rendered as vectors at the zoom rather than enlarged as pixels, so its lines thicken as it comes in. It shakes hard on the hit and settles. |
| **Manga cut-out over a new background** | **SKIP** | Our figures are already cut-outs, and lifting one onto a pasted-in background is a comic-book idiom, not Bass. The one place we want a figure on a new ground, the slam, is the sunburst insert above. |
| **Flash frame, 2–6 frames of flat colour with a sound word** | **ADAPT** | Two frames of one flat palette colour (gold, red, black) on the hit, with the film's paper and grain. No sound words: there is no lettering in a wordless film. |
| **Storm panel** | **SKIP** | There is no storm in this story, and nothing in the palette for one. Its job (chaos in one image) is done by the X-split and the rewind. |
| **Glitch, 1–4 frames** | **ADAPT** | Only inside the s09 rewind, where the film is literally being scrubbed: strips of the frame slip sideways like a bad splice, two frames at each join, heavier the further back it goes. No colour split: the palette holds. Nowhere else in the film. |
| **Cuts one frame before the beat** | **SKIP** | Picture and sound run on one clock. Scenes start on bar lines of the 120 bpm score (`K.BPM`), the big hits are placed on the grid (the BOOM on the bar line at 1:32.0, checkmate at 2:10.0), and the mix places every sound at the scene's own time constants. The inserts start on the frame of the hit they belong to, so cutting a frame early would only pull the picture off its own sound. |
| **Rings blooming onto the title** | **SKIP** | Our title is built from the plan (chalk dots, ruled lines, two crossing strips) and returns the same way at the end. Rings already bloom where they mean something: the match's light (1:37.4), the alarm's red ripples (from 1:34.5). |
| **Red dots flooding the screen** | **SKIP** | RED belongs to the Knight and what he does, and the bible keeps it "small and burning". Our one red dot is the ruby landing at the crossing of the X (2:23.0). |
| **The storm shrinking into the sun** | **SKIP** | Goes with the storm panel. |
| **Dissolving to blank paper dot by dot** | **SKIP** | We keep our ending: black, with the ruby's red dot a breath longer (2:23.5–2:23.9). |

---

## Part C. How the adopted types are built (DOUBLE CROSS v2)

The code is `films/double_cross/shots.py` (208 lines) and the scene changes in commit `9ea5f1b`
("DOUBLE CROSS v2: punch-ins, flash frames, the Knight on a red sunburst, rewind slips"). The bible's
new section "v2: the borrowed shot types" lists the same placements.

### C.1 The mechanism: `render_plain`, `INSERTS` and `S.play`

Each scene that has inserts renamed its old `render` to `render_plain` and now renders through
`S.play`:

```python
from films.double_cross import shots as S

INSERTS = (S.Flash(T_SWING[0], 2, K.GOLD),)          # s06: the seal breaks: gold, flat

def render(f, t, T):
    S.play(f, t, T, render_plain, INSERTS)

def render_plain(f, t, T):
    ...                                              # the scene's drawing, unchanged
```

- **Shot records** are namedtuples: `Punch(t0, n, at, zoom, seed=0, accent=None)`,
  `Flash(t0, n, colour)`, `Slip(t0, n, amount, seed=0)`, `Insert(t0, n, draw)`. The list is called
  `INSERTS` because some scenes already use `SHOTS` for their cut lists.
- **Which frames.** `S.frame_k(t, t0, n)` returns the shot's frame index, `round(t·24) −
  ceil(t0·24)`, or `None` outside it: a shot covers `n` frames starting with the first frame at or
  after `t0`. The scenes put `t0` on the hit (or 0.01 s before it), so the insert starts on the hit's
  frame.
- **What `play` does.** `S.active(t, shots)` finds the first non-Slip shot covering `t`. If there
  is none, `render_plain` draws the frame. Otherwise a `Flash` draws a flat field, an `Insert` calls
  its own `draw(f, t, k)`, and a `Punch` re-renders the plain frame through a lens. Then every `Slip`
  covering `t` is applied on top.
- **The rewind replays scenes plain.** s09 now calls `getattr(mod, "render_plain", mod.render)` for
  the scenes it rewinds through, so each insert plays once, in its own scene, and never in the
  rewind.
- **Sound is unchanged.** Every insert sits on a sound already in the mix: the clatter, the door's
  swing, the BOOM, the second blow, the rewind's scrubbing, the cough, the click of the queen on the
  knight. The black flash before checkmate is the two frames just before its ring and stab. The v2
  commit did not touch `audio/mix.py`.

### C.2 `Punch`: the extreme close-up

```python
S.Punch(t0, n, at, zoom, seed=0, accent=None)
```

- **`at`** is the detail in frame px, or a function `t -> (x, y)` when the detail moves (each scene
  defines one: `_can_frame`, `_fist_frame`, `_headlight_frame`, `_hit_frame`).
- **The lens** (`S.punch_matrix(at, zoom, k, n, seed)`), for frame `k` of `n`:
  - the zoom snaps in: 0.82 of `zoom` on the first frame, 0.99 on the second, all of it from the
    third (`out3` over `k / 1.5`), then keeps creeping, 5 % more by the last frame;
  - the window is clamped to the frame so nothing beyond the scene's edges shows;
  - a shake of up to ±28 px and ±1.8°, seeded per frame (`hash01(seed, k, ...)`), decaying as
    `(1 − u)^1.5` across the shot.
- **Vector, not pixels.** `S.viewed(f, m)` temporarily replaces `f.screen()` so that everything the
  scene draws goes through the lens matrix; then `render_plain` runs as usual. Because the frame is
  redrawn at the zoom, strokes and edges get thicker as it comes in instead of getting soft. This
  works because DOUBLE CROSS draws everything through `f.screen()`. The flat field is painted by
  `f.fill` with the identity matrix, so the lens does not touch it; the field's ink mottle is drawn
  through `f.screen()` (in `bass.bass_scene`), so it is magnified with the rest.
- **The wedges** (`S.wedges(c, p, u, seed, n=16, colour=K.INK, accent=None)`) are drawn after the
  plain frame, in frame px rather than through the lens, converging on where the detail lands on
  screen (`p = m.transform_point(*at)`, so they follow it as it shakes). Sixteen cut-paper wedges in
  INK reach in from outside the frame toward `p`. Each has a hand-cut kink in both long edges. The
  tips stop short of `p`: at 0.8 of `min(R, 1150)` from it on the first frame and 0.5 by the last,
  where `R` is the distance from `p` to the farthest corner plus 80 px. Each tip's reach jitters
  between 0.85 and 1.2 of that from frame to frame. With `accent`, one wedge is cut in that colour
  instead (s11 uses RED).

### C.3 `Flash`: the flat frame

```python
S.Flash(t0, n, colour)
```

`S.flash(f, colour)` is just `K.scene_setup(f, colour)` with nothing drawn: the film's own field in
one palette colour, with its paper fibres, ink mottle and grain. The engine's `f.post["flash"]`
would not do this: it mixes toward its colour after the grain, so its frame comes out grainless
(SYSTEM.md, 3.2). No lettering is ever drawn on it.

### C.4 `Slip`: the rewind's glitch

```python
S.Slip(t0, n, amount, seed=0)
```

`S.slip(f, amount, seed)` works on the drawn canvas (`f.surf`) after the scene has drawn and before
`finish()` adds paper fibres, grain and vignette, so the post lies evenly over the damage:

- the frame is cut into horizontal strips 6–98 px tall (scaled with the render);
- a strip slides sideways (wrapping round) with probability `0.62 × amount`, by up to
  `30 + 260 × amount` px; 45 % of the slid strips get a 2 px PAPER hairline at their top seam;
- a few strips (probability `0.08 × amount`) get a flat band of PAPER or INK up to 14 px tall;
- at `amount >= 0.7` the whole picture first jumps vertically by up to ±36 px (the tape's hold);
- colours are only ever the frame's own, PAPER or INK: there is no RGB split.

### C.5 `Insert` and the sunburst: a silhouette on a loud ground

```python
S.Insert(t0, n, draw)              # draw(f, t, k) draws the whole frame
S.sunburst(c, p, colours, n=28, rot=0.0, r=3200.0)
```

`S.sunburst` fills `n` rays from `p`, alternating through `colours`. s07's `knight_burst(f, t, k)` is
the only `Insert`:

- `K.scene_setup(f, K.RED)`; the rays (26 of them) alternate `K.RED` and `WINE` (RED 32 % of the way
  to INK), centred behind his shoulders at (420, 900) and turning 3° a frame; the whole picture
  breathes in 1.4 % a frame;
- an INK floor below y = 1500, and the vault door as a huge INK disc (r = 1100) at his hands, with a
  thin PAPER arc for its rim;
- the Knight at scale 1.55, facing left, INK with a PAPER rim, frozen in the lunge from s07's door
  shot (`door_knight` at `T_SHOVE[0] + 0.28`, creeping 0.02 s a frame).

### C.6 Where they are

Exact frames, as `frame_k` resolves them (film frame times; each frame lasts 1/24 s):

| Film time | Scene, local | Shot | Detail | What is on screen |
|---|---|---|---|---|
| 1:03.38–1:03.58 | s05, 11.375 (frames 273–277) | `Punch(T_CLATTER - 0.01, 5, _can_frame, 6.0, seed=51)` | ×6 | The tin can hitting the floor as the clatter sounds (`T_CLATTER = 11.38`). |
| 1:17.00–1:17.08 | s06, 11.0 (264–265) | `Flash(T_SWING[0], 2, K.GOLD)` | gold | The seal breaks as the door starts to swing open on gold. |
| 1:32.00–1:32.08 | s07, 12.0 (288–289) | `Flash(T_SLAM, 2, K.RED)` | red | The vault door's BOOM on the bar line. |
| 1:32.08–1:32.29 | s07, 12.083 (290–294) | `Insert(T_SLAM + 2/24, 5, knight_burst)` | sunburst | Who did it: the Knight on the red rays. These 7 frames replace v1's 0.2 s of black after the BOOM and the red dial's first two frames, so the dial now appears at 1:32.29. |
| 1:39.29–1:39.50 | s08, 3.29 (79–83) | `Punch(THUDS[1] - 0.01, 5, _fist_frame, 4.0, seed=81)` | ×4 | His near fist on the door at the second blow (`THUDS[1] = 3.3`); the lens holds where the fist lands. |
| 1:48.17–1:54.21 | s09, every rewind join | `Slip(j, 2, 0.3 → 1.0, seed=90…101)`, last `Slip(6.15, 1, 0.3, seed=99)` | 13 slips | Two-frame slips at the twelve joins of `REWIND` (1:48.17, 1:48.58, 1:48.96, 1:49.38, 1:49.75, 1:50.17, 1:50.46, 1:50.75, 1:51.50, 1:52.21, 1:52.33, 1:52.46), the amount rising from 0.30 at the first join to 1.00 at the last (the tape's vertical jump from 1:50.75, where the amount passes 0.7); one light frame at the freeze on her eye (1:54.17). Each frame's pattern is seeded `seed * 7 + k`. The last slip reuses seed 99 (also the 1:52.21 slip's), which is harmless because the two amounts differ. |
| 2:05.62–2:05.83 | s10, 1.625 (39–43) | `Punch(T_COUGH[0], 5, _headlight_frame, 4.5, seed=101)` | ×4.5 | The dead headlight on the first cough (it flares at 2:06.02). |
| 2:09.92–2:10.00 | s10, 5.917 (142–143) | `Flash(T_MATE - 2/24, 2, K.INK)` | black | Two black frames, then the checkmate ring at 2:10.0. |
| 2:19.88–2:20.08 | s11, 3.875 (93–97) | `Punch(T_HIT, 5, _hit_frame, 3.0, seed=111, accent=K.RED)` | ×3, one red wedge | The lens rides the knight's fall as the queen's base knocks him over (`T_HIT = 3.85`). |

Against the plan we started from: the tin can (1:03), the gold flash (about 1:17), the red flash and
the sunburst Knight at the slam (about 1:32), the rewind joins (1:48–1:54), the cough (about 2:05),
black before checkmate (2:10) and the queen taking the knight (about 2:20) all landed where planned.
The fist punch-in planned for "1:42" is at **1:39.29**, the second of the three blows (1:38.85, 1:39.3,
1:39.75); 1:42.25 is her heel's hollow knock.

### C.7 Adding an insert

1. Make sure the scene renders through `S.play` (its drawing in `render_plain`, an `INSERTS` tuple).
2. Put `t0` on a hit that already has a sound (a module beat constant, or its cue time). Use
   `t0 = hit - 0.01` if the hit can fall a hair before a frame boundary.
3. Use palette colours only (`K.GOLD`, `K.RED`, `K.INK`, ...). No lettering.
4. For a `Punch` whose subject moves, give `at` as a function of `t` returning frame px, computed from
   the same camera the shot uses (`cam.to_frame(...)`, `table_cam(t).to_view(...)`).
5. Check the frames as stills: `RENDER_WORKERS=1 python3 -m engine.render --film double_cross sNN
   --times a,b,c --scale 1.0`, with times inside the shot (first frame at or after `t0`).
6. If the scene is rewound in s09, nothing else is needed: the rewind calls `render_plain`.
7. Re-render the segments that touch the scene and re-join the film: `python3 -m engine.render
   --film double_cross all --only sNN` (`--only` re-renders those segments even when they exist).
   If the insert sits on an existing sound, the mix does not change: mux and encode as in SYSTEM.md,
   section 9.
