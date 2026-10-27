# The films

Every story made so far, in the order we made it: what it is, how it is built, the devices it uses,
what it added to the system, and where its files are. DOUBLE CROSS is covered in depth in section 9,
its OPPOSITE cut in section 10, and THIN ICE, the latest, in section 11.

Paths are relative to `productions/silhouette-noir/` unless they start with `productions/`.
Film times are given as m:ss.ss (film seconds); "local" means scene seconds. Dates are commit
dates (UTC).

| # | Film | Made | Length | Form | State |
|---|---|---|---|---|---|
| 1 | Nobody Has a Face | 10-21 | 2:58.8 | Stickman noir, narrated, 18 scenes | Delivered (`762a2c6`) |
| 2 | SALVAGE | 10-22 | 3:01.5 | Silhouette noir, narrated, 16 scenes | Paused mid-animation; never rendered |
| 3 | SHADOW PLAY | 10-22 | 2:33.5 | Silhouette noir, narrated, 12 scenes | Preview delivered (picture done, sound not final) |
| 4 | RED | 10-22 | 2:34 | Silhouette noir, narrated, 11 scenes | Preview delivered (picture done, sound not final) |
| 5 | THE LANTERN | 10-23 | 0:26 | Wordless style test (Limbo, then Saul Bass), 2 scenes | Three test previews |
| 6 | OPPOSITE v1–v3 | 10-23 | 0:32–0:34.5 | Wordless thriller test, one continuous camera | Three previews |
| 7 | OPPOSITE, the Bass cut | 10-23 | 0:36 | Pure Saul Bass graphic retelling, one scene | Delivered, two review passes |
| 8 | OPPOSITE (full) | 10-23 | 2:24 | Wordless Bass cut, 11 scenes | Delivered |
| 9 | DOUBLE CROSS | 10-23 | 2:54 (v4 2:32, v1–v3 2:24) | Wordless Bass heist, 11 scenes | v1, v2 (the shot types, `9ea5f1b`), v3 (the review fixes and the voices), v4 (v2's picture again, slower, the guard rebuilt) and v5 (the double cross made easy to follow) delivered |
| 10 | DOUBLE CROSS, the OPPOSITE cut | 10-25 | 2:54 | DOUBLE CROSS v5's story in OPPOSITE's grammar, wordless, 11 scenes | Delivered |
| 11 | THIN ICE | 10-25 | 3:08 | A new story: a wordless winter thriller in Bass cut paper, 12 scenes | Delivered |

---

## 1. Nobody Has a Face (stickman noir)

- **Logline.** A detective in a city where nobody has a face hunts a killer whose habits turn out to
  be his own. ("Seven witnesses saw the killer's face. Not one of them could describe it.")
- **Form.** 2:58.8 (4,292 frames, 178.83 s), 1080×1920, 24 fps, 18 scenes. The skill's **Style 1
  Dark**: white faceless line figures on a flat black canvas with three accents (streetlamp amber,
  blood crimson, siren blue).
- **Structure.** The skill's five-stage heartbeat: hook → disrupted assumptions → insider secrets →
  truth → elevation and a closing question.
- **Sound.** Narration through Magnific with ElevenLabs Turbo v2.5 (catalogue voice "Noah Reed", one
  take, about 312 credits including a voice test). Everything else procedural. Finals measured
  -14.1 LUFS.
- **Team.** The director made S01, integration and delivery; six animator agents made S02–S18; one
  sound agent made the score, SFX, ambience and mixer.
- **Delivered.** A clean master (no text in picture), a captioned social cut, an SRT (124 cues) and a
  poster.
- **What it introduced.** The scene contract `render(f, t, T)` + `cues(T)`; a timeline locked to the
  narration's word timings; the procedural SFX catalogue that became `audio/sfx.py`; BT.709 delivery.
- **Files.** `productions/nobody-has-a-face/` (own `engine/`, `scenes/s01_lineup.py` …
  `s18_verdict.py`, `audio/`, `timeline/`, `tools/`, `docs/production-bible.md`, `final/`).

## 2–4. The silhouette noir trilogy: SALVAGE, SHADOW PLAY, RED

The user asked how to move beyond stick figures, then for "a heavy mix of the tradition of Saul
Bass's thriller titles and the games Limbo and Inside", three stories of at least two minutes,
deeply connected and smooth. That brief built the silhouette engine and `STYLE.md`: ink
silhouettes in fog, volumetric light, Limbo eyes, one red, and flat cut-paper Bass interludes.
All three are narrated (Magnific, ElevenLabs Turbo v2.5) and joined by composited transitions.

**What the trilogy introduced to the system:** the whole engine (`frame.py` layers, light and
glow; `figure.py`, `costume.py`, `motion.py`, `physics.py`, `atmos.py`, `creatures.py`; `bass.py`;
`transitions.py`; segment rendering in `render.py`); `STYLE.md`; `engine/API.md`;
`docs/ANIMATOR_BRIEF.md`; transition handles; per-film red tables; about 15 agents on 4 cores.

### SALVAGE

- **Logline.** A deep-sea diver is paid in cash to bring up a sunken captain's safe for a man who
  never asks his name. The man is the shipowner who sank her. The captain was the diver's father.
- **Form.** 3:01.5 (4,356 frames), 16 scenes, 25 narration lines.
- **Motifs.** The red line (the air hose: life, the father–son bond), the pale line (the lifting
  line: greed), the circle (helmet port, moon, safe dial, lamp spot, the bell's mouth, the hole in
  the hull; "every important transition is a circle becoming another circle").
- **Structure.** HOOK s01–s02 (a flash-forward of him sinking; the cash); DESCENT s03–s05; DISCOVERY
  s06–s10; TWIST s11–s14 (the client cuts the hose; he hauls up the bell, not the safe); ECHO
  s15–s16.
- **Joins.** scroll (down at 0:10.0, up at 0:25.0, and three more in s11–s13), flatten (0:39.0), ink
  (0:53.0), whip (1:06.5), bars (1:26.0), dissolve (1:45.0), a 2 s dip to black (2:45.5), and cuts.
- **State.** Paused at `996e107` with s15 mid-animation and the sound being re-synced. Never
  rendered to a preview; `final/salvage.en.srt` exists.
- **Files.** `films/salvage/` (`docs/bible.md`, `docs/script.txt`, `cast.py`, `sets*.py`,
  `scenes/` with five `_lib_` files, `audio/`).

### SHADOW PLAY

- **Logline.** A sleepless woman watches the forty windows across the street and sees a murder in a
  window that has been dark for a year. It happens again the next night, to the second. It was
  never a crime. It was a show, staged for the women who watch.
- **Form.** 2:33.5 (3,684 frames), 12 scenes, 29 narration lines.
- **Motifs.** The grid of 40 (North by Northwest's facade; it returns as forty paper dolls); the
  binocular circle; the shadow on the sheet; the light switch; RED for her coat, the paper blood
  and the police light's red half.
- **Joins.** flatten (0:09.0), a binocular `shape` (0:24.0, inverted), bars (0:52.5), slash
  (1:06.5), a window `shape` (1:19.5), dip (1:46.5), tear (2:11.5), dissolve (2:21.5), cuts.
- **State.** Preview delivered (`final/shadowplay_9x16_preview.mp4`, `shadowplay.en.srt`) with the
  picture done and the sound mid re-sync.
- **Files.** `films/shadowplay/`.

### RED

- **Logline.** Every child in the village knows the rule: never leave the path. The winter she turns
  seven, a girl in a red hood is sent down it to a "grandmother" she doesn't have. A wolf chases
  her off the path, and saves her life. At the end of the path lives the thing the village feeds
  one child a year.
- **Form.** 2:34 (3,696 frames), 11 scenes, 23 narration lines.
- **Motifs.** The path (a black Bass line), the red triangle (the hood: a child, an offering), eyes in
  the dark, fire (the lantern: the mother's love).
- **Joins.** ink (0:09.0), dissolves (0:24.0, 0:38.0, 1:06.5, 2:05.0), whip (0:52.0), flatten
  (1:21.0), a warm white flash (1:51.0, out of the fire), a 2 s dip to white (2:19.0).
- **State.** Preview delivered (`final/red_9x16_preview.mp4`, `red.en.srt`), picture done, sound not
  final.
- **Files.** `films/red/` (nine `sets*.py` modules, three `_lib_` files, `audio/` split into score,
  SFX, ambience, cue sheet, QA and mix).

### Why we moved on

After the previews the user said: "I dont like the way its been done". The restart pitch proposed
three short wordless stories (FOLLOW, THE LANTERN, HIS SHADOW; only THE LANTERN was made) and drew
these lessons from the trilogy: one look per film; brighter frames; characters at least a third of
the frame tall; about 10–12 big, readable shots instead of long dim takes; continuous camera and
match cuts; test before building a whole film.

---

## 5. THE LANTERN (the style test)

- **Story.** A girl of about nine walks into a dark wood with a lantern (her scarf is the film's red). She stops at her brother's wooden
  horse, takes it and hugs it, and walks on as night falls and the light shrinks. White eyes with
  red pupils open in the dark, pair by pair. She thrusts the lantern; the light swells in rings and
  the eyes snap shut. She runs. Two jagged black legs stab down into the light (The Man with the
  Golden Arm), the light closes to the flame, black.
- **Form.** 0:26 (624 frames): s01 TITLE (6 s: a red cut-paper flame, trunks sliding in, THE
  LANTERN rising between them) and s02 INTO THE WOODS (20 s, one continuous camera).
- **The one transition.** An `iris` opening out of the title's flame at 0:06.0 (1.0 s, centre (540,
  1040)), so the forest begins on the same flame.
- **Three versions.** `b5fe35b` a Limbo forest test (fog layers, `sets.py`); after the user chose
  "Saul Bass, drop the Limbo style", `ed338b9` rebuilt it as pure cut paper; `b840f92` (v2) made it
  fluid on the new paper-figure rig, together with a new story (OPPOSITE).
- **What it introduced.** `engine/paperdoll.py` (precise cut-paper figures on ones, planted feet,
  spring hair and scarf); the pure Bass look as the house style; a title that hands off to the
  scene through a shared shape.
- **Files.** `films/lantern/` (`scenes/s01_title.py`, `scenes/s02_into_the_woods.py`, `sets.py`,
  `cast.py`, `audio/mix.py`); previews `lantern_test`, `lantern_bass_test`, `lantern_v2`.

## 6. OPPOSITE v1–v3 (the wordless thriller test)

- **Story.** A woman at her lit window sips from a mug and hears a quarrel across the street. A
  crash zoom finds the knife. The mug falls. The man sees her and points; he runs; she pulls her
  light's cord. A diagram of the street shows his path down, across and up. Her dark room: light
  under the door, two feet, the handle, the keyhole, his eye. Cut to black.
- **Form.** s01 TITLE (6 s: North by Northwest grid lines, the facades rise, OPPOSITE rides in along
  its rule, the windows light in rhythm) and s02 OPPOSITE (one continuous camera, no cuts). The
  world, light schedule and camera live in `films/opposite/world.py` in film time, so s01's last
  frame is s02's first.
- **Versions.**
  - v1, 32 s (`b54431b`): one continuous camera, the grid title.
  - v2, 33.5 s (`4562e99`): after the user asked for more noises and screams, clearer motion and
    more camera angles: crash zooms, whips, procedural screams and voices.
  - v3, 34.5 s (`d1b59b2`): after the user asked where the footsteps were, why there was a scream at
    the end, what she was holding, why she did not go to the window, and why the fight's range of
    motion was poor: CMU motion capture (`engine/mocap.py`), her walk to the window, a clear mug,
    generated voices and footsteps (Magnific, about 235 credits), the end scream removed.
- **What it introduced.** Motion capture retargeted onto paper figures; camera grammar inside one
  shot (crash zoom, whip, tilt); the generated foley library `films/opposite/audio/gen/` (15 files,
  reused by every later film).
- **Files.** `films/opposite/` (`world.py`, `scenes/`, `audio/mix.py`, `audio/gen/`); previews
  `opposite_test`, `opposite_v2`, `opposite_v3`.

## 7. OPPOSITE, the Bass cut (36 s)

The user asked whether this was "deep Saul Bass" and to be more creative. We retold the same story
the way Bass told stories: flat cut paper, graphic metaphor and rhythm instead of a camera looking
at rooms. Every beat is one graphic idea, and each turns into the next (`films/opposite_bass/world.py`):

| Time | Beat | The idea |
|---|---|---|
| 0:00.0 | TITLE | Psycho bars race; strips assemble OPPOSITE; a red cut splits it; OPPO and SITE part; each letter becomes a window (type into architecture, North by Northwest). |
| 0:05.0 | WINDOWS | Two lit windows face each other. |
| 0:05.6 | SIP | Her profile on her window's amber, drinking; red zigzags of shouting cross the street. |
| 0:08.5 | HER EYE | His window reflected in her eye; we fall into the reflection (Vertigo). |
| 0:11.0 | QUARREL | Anatomy of a Murder cut-outs; the frame jumps closer on the beat. |
| 0:14.0 | KNIFE | Three stabs, each cutting the picture of her open on red (Psycho); bars close the window. |
| 0:16.5 | MUG | She gasps; the mug falls; the hand flies to her mouth. |
| 0:18.5 | ARM | His jagged arm grows across the street to her window (The Man with the Golden Arm). |
| 0:21.5 | OFF | She pulls the cord: the picture flips negative and goes dark. |
| 0:22.5 | PATH | A red line walks down his stairs, across the street, up hers. |
| 0:28.5 | DOOR | Light under her door; his shadow takes it a step at a time; the handle turns twice. |
| 0:31.5 | HIS EYE | His eye at the keyhole, the mirror of hers. |
| 0:33.4 | END | OPPOSITE cut through in red along the slash. Black. |

- **Sound.** A Herrmann-style score on the Psycho chord (B-flat minor with a major seventh) at 120 bpm.
- **Review.** After the user pointed to "little flaws … from hand shape of the lady drinking", two
  full review passes (`805dde7`, `866aa49`) rebuilt her close-up hands, the knife beat, the title,
  the light-off and the keyhole.
- **What it introduced.** The 120 bpm beat grid; figures on twos with graphics and camera on ones;
  Bass-time functions (`tb`) that later films call to reuse shots.
- **Files.** `films/opposite_bass/` (`world.py`, `scenes/s01_bass_cut.py`, `audio/mix.py`); preview
  `final/opposite_bass_cut_preview.mp4`.

## 8. OPPOSITE (the full Bass cut, 2:24)

The user asked for the full version "with such amazing style, emotion effects, camera angles,
detailing and colors and … markers and arrows and dots".

- **Story.** At a quarter to midnight a woman makes tea and stands at her window. Across the street,
  one floor up, a couple quarrel; a red ring circles the knife; he uses it. She drops her mug, he
  sees her, and the same red ring circles her window. She kills her light. He crosses to her
  building; she climbs out onto her fire escape; he passes right under her. While he climbs her
  stairs she crosses and climbs his. The woman on his floor is alive; she dials 9-1-1 on his phone.
  He breaks into her empty room and, from her window, sees her in his. Sirens; every window lights;
  every look in the city converges on him; the red ring closes round him.
- **The twist (OPPOSITE).** The watcher becomes the watched; the hunter ends framed in the window he
  was watching; she ends where he began.
- **Form.** 11 scenes, hard cuts on the beat: s01 title 0:00, s02 amber 0:12, s03 quarrel 0:26, s04
  knife 0:40, s05 seen 0:52, s06 dark 1:06, s07 crossing 1:16, s08 door 1:30, s09 call 1:44, s10
  opposite 1:56, s11 end 2:16.
- **Devices.** The annotation layer (`films/opposite_full/kit.py`): sight lines (hers PAPER, his
  RED), the marker ring (three only: the knife at 0:29.5, her window at 0:55.95, him at 2:12.0),
  footstep dots, arrows, ripples, a heartbeat, hand-cut numerals, the callout lens, her wall clock.
  Section diagrams of both buildings; a split-screen mirror; over-the-shoulder shots that mirror
  each other (hers in s02, his in s10); a straight-down shot and a low angle (s06); Vertigo's
  stairwell (s07); a keyhole POV (s08); one Dutch tilt, in her panic (s04).
- **Reuse.** Bass-cut shots are pure functions of Bass time, called with `tb = <Bass beat> + (t -
  local start)`, and ported onto the night field.
- **Team.** Three scene agents (her room, his room, his gaze) and one audio agent.
- **What it introduced.** The annotation layer as the film's handwriting; the scene-module beat
  constants that the mix imports; a mix that plays missing scenes from the bible; hard cuts only.
- **Files.** `films/opposite_full/` (`docs/BIBLE.md`, `kit.py`, `rooms.py`, `his_room.py`,
  `gaze.py`, `folk.py`, `scenes/`, `audio/mix.py`); preview `final/opposite_full_preview.mp4`.

---

## 9. DOUBLE CROSS (2:54), in depth

The user liked "the way you are connecting things and camera motion and sound effects" and asked
for a new crime thriller, more innovative, with no more than two agents at a time.

**Film times.** Sections 9.2–9.11 give v1–v3's times (2:24). v4 (9.12) runs 2:32: s02's side
shot (0:21–0:28) and s05 (0:56–1:14) are re-timed, and every other time from 0:24 is later, by 4 s
up to s05 and by 8 s from s06 (v1's 1:06). v5 (9.13) runs 2:54: s01, s02, s07, s09 and s10 gain
bars, and against v4 s02 starts 4 s later, s03–s07 6 s, s08–s09 10 s, s10 16 s and s11 22 s.

### 9.1 The story

A blueprint unrolls: a bank drawn in chalk. Under a hanging lamp three hands set three chess pieces
on it: a white QUEEN (the Architect), a gold BISHOP (the old safecracker) and a red KNIGHT (the
muscle). While she chalks the route, his eyes go to the X on the vault, and she sees him look.

Night. The blueprint rises into the city. Down a manhole, along the sewer and up through a hatch,
the crew follows the chalk. They slip past a guard's flashlight. The Cracker opens the vault.

Then the Knight double-crosses them: he shuts the vault on the other two, and his red line leaves
the chalk route in an L, the knight's move, to the car. The alarm rings.

In the dark a match flares. The Cracker pounds the door; the Architect is calm. She taps the floor:
it sounds hollow. She unrolls tracing paper, and the film rewinds to what we missed: while she
chalked the plan, she dotted the sewer line exactly under the vault. The overlay shows PLAN B: a
trapdoor, her own way out by the sewer, the police waiting at his car, and her real prize, one ruby.

Police cars close on the Knight from all four streets: checkmate. Two blocks away a manhole lifts
and she walks away; their two routes cross into an X. The X splits open on her gloved palm: the
ruby. At the table her white queen knocks over the red knight, and the title's X crosses again with
the ruby as its red dot.

**DOUBLE CROSS:** he crosses the crew; she had crossed him before he moved. X marks the spot twice.

### 9.2 Structure

| Act | Scenes | Film time | What it does |
|---|---|---|---|
| The plan | s01 TITLE, s02 CREW, s03 PLAN | 0:00–0:40 | The blueprint, the crew, the route; every plant is laid. |
| The heist | s04 NIGHT, s05 GUARD, s06 SAFE | 0:40–1:20 | The plan rises into the world and works, step by step, under the stopwatch. |
| The cross | s07 CROSS | 1:20–1:36 | The ruby, his look, the X-split, the slam, his L. |
| The reveal | s08 LOCKED, s09 PLAN B | 1:36–2:04 | The match, the hollow floor, the rewind to the plant, Plan B. |
| The payoff | s10 CHECKMATE, s11 END | 2:04–2:24 | The arrest, her exit, the ruby, the queen takes the knight. |

### 9.3 Plants and payoffs (play fair)

| Plant | Where | Payoff | Where |
|---|---|---|---|
| The dashed sewer branch is ruled running right under the vault. | s01, 0:06.5 (the "sewer" group) | The hollow floor; the trapdoor. | s08 1:42.25; s09 1:58.9 |
| His red look goes to the X; her white look catches him. | s02, 0:21.6 and 0:22.5 | The betrayal; the rewind replays it and stops on her eye. | s07; s09 1:52.45–1:54.6 |
| His slam on the plan hides her chalk dot on the sewer line under the vault. | s03, 0:34.75 | The rewind stops on that frame and a lens snaps round the dot. | s09 1:50.75–1:52.2 |
| His slam claps the plan's vault door shut on the queen and the bishop. | s03, 0:34.75 | He shuts the vault on the other two. | s07 1:32.0 |
| A small bell is drawn on the side door. | s03, 0:37.0 | His L goes through that door and the alarm rings. | s07 1:34.5 |
| She opens one small deposit box; something red glints. | s07, 1:21.5 | The ruby. | s11 2:16.55–2:18.45 |
| His slam makes the other pieces jump. | s02, 0:19.0 | Her queen knocks his knight over, quietly. | s11 2:19.85 |
| The white strip lands first; the red crosses over it. | s01, 0:08.0 and 0:08.5 | The X returns with the white over the red: she crossed him last. | s11 2:21.5–2:22.0 |

### 9.4 Cast

All figures are INK cut-paper silhouettes in profile with a rim in their colour (`cast.py`,
`C.RIM`), which is also their colour on the plan.

| Who | Silhouette | Piece, colour | CMU clips used in the code |
|---|---|---|---|
| The Architect | belted trench coat, low chignon with a pencil through it, gloves | white QUEEN, `PAPER` | 17_03 (stealth walk), 104_02 |
| The Knight | broad, flat cap, heavy coat, a cigarette ember | red KNIGHT, `RED` | 17_08 (heavyset walk), 26_10, 81_05 (pushing a heavy object), 16_08 (run, sudden stop) |
| The Cracker | thin, stooped, bowler, round spectacles, stethoscope | gold BISHOP, `GOLD` | 77_14 (careful creep), 22_03 (kneeling), 23_03, 104_02 |
| The Guard | peaked cap, flashlight | black PAWN, `INK` (rim `STEEL`) | 77_05 (looking round with a flashlight), 104_02 |
| The cat | small, black, two gold eyes | none | procedural |

The bible's casting table also named clips the code does not use (18_08, 13_33, 69_70, 70_03, 80_28,
69_16, 120_15, 79_73). The police are cars seen from above, never people. The profile close-ups are
`faces.py`: `F.her` (faces right, on the lamp's gold), `F.cracker` (faces right, on steel),
`F.knight` (faces left, in the dark, lit by his ember) and `F.hand`.

### 9.5 Look and devices

- **Palette** (`kit.py`): `BLUE` the blueprint; `PAPER` chalk; `NAVY` the night; `STEEL` moonlit
  distance; `DEEP` a dark room; `GOLD` gold and lamplight (the Cracker); `RED` the Knight and what
  he does; `POLICE` the police light's blue half (s10 only); `INK` every silhouette. No gradients.
  Translucency only for light and the tracing paper.
- **The camera idea, the TILT.** The plan is the world seen from straight above; the world is the
  plan seen from the side. `P.PlanCam(cx, cy, zoom, phi, yaw)` is orthographic: `phi = 90` is a pure
  blueprint with pieces as discs, `phi ≈ 55` the table view with pieces standing up like a pop-up
  book, `phi → 0` eye level with the walls extruded into a building (`P.draw_walls_3d`). The film
  tilts down into the world (s03 → s04), up into the plan (s05's stealth map, s07's L) and back.
- **The handwriting** (`kit.py`): chalk lines, routes (dotted chalk led by an arrowhead), circled
  step numerals ① to ⑤ (the only text besides the title), the X, the guard's cone, the stopwatch,
  chess pieces, the bell, cars from above with light bars, the match, tracing paper, the X-split,
  rewind marks; plus OPPOSITE's sight lines, marker ring (once: the arrest), ripples, callouts and
  numerals.
- **The world.** `plan.py` holds the plan's geometry (the vault's X at (540, 565), the ruby box at
  (680, 518), the car at (930, 1400), the four routes `ROUTE_IN`, `ROUTE_OUT`, `ROUTE_KNIGHT`,
  `ROUTE_B`). `bank.py` holds the night sets in set px (front street, sewer section, corridor, vault
  door, lock cutaway, vault), each placed by an explicit `Bk.Cam(x, y, zoom)`.

### 9.6 Scene by scene (film times from the scene modules' constants)

This is the v1 picture. The v2 inserts that play over it are listed in 9.10, and v3's changes to
s01–s03, s09 and s10 in 9.11 (withdrawn in v4). v4's s02 and s05 are in 9.12, and v5's changes
in 9.13.

**s01 TITLE (0:00–0:12).** Four chalk dots tick in at the sheet's corners (0:00.5–0:02.0) and dotted
lines join them; the blueprint unrolls (0:02.5–0:04.0); the bank rules itself in, one group per beat
(bank, vault, rooms, streets, manholes, sewer, side door: 0:04.0–0:07.0). A white strip (0:08.0) and a
red strip (0:08.5) slash in and cross into an X; DOUBLE (0:09.0) and CROSS (0:09.5) stamp in. The
words lift (0:10.0), the X shrinks onto the vault and lands as the chalk X (0:11.0), the lamp comes on
(0:10.75) and the camera tilts down to the table (0:10.55–0:12.0), where s02 begins.

**s02 CREW (0:12–0:24).** Three hands set three pieces, each followed by its face, a lens on a leader
line joining face to piece: her queen (0:13.0) and her profile on gold; his bishop (0:16.0), the
Cracker's profile on steel with a glint across his spectacles (0:17.5); the knight slammed down
(0:19.0, the others jump) and the Knight's profile in the dark, his ember flaring (0:20.0). Then the
table from the side under the swinging lamp: his red look to the X (0:21.6), her white look to him
(0:22.5). She picks up the chalk (0:23.5).

**s03 PLAN (0:24–0:40).** One glide over the plan following her chalk; the pieces hop along the route
behind it. ① the "down here" chevron on manhole A (0:24.5); the pawn set on the guard's post (0:28.5);
the cone swept out and its timing ring (0:29.0–0:30.0); a gold lens on the dial turning right, left,
right (0:31.0–0:32.06); the door's clunk (0:32.0); the route reaches the X (0:32.4). His red hand
snatches his knight off the route (0:34.2) and slams it down by the street (0:34.75): the vault door
claps shut on the plan, and her chalk leaves the dot. ⑤ the way out along the street (0:35.5–0:36.4),
the chalk car (0:36.45) and the bell (0:37.0). The camera starts the tilt down (0:38.0).

**s04 NIGHT (0:40–0:52).** The pop-up: the paper goes NAVY, the lamp goes out, the walls rise out of
their chalk lines (0:40.2–0:42.8). The front street; the Knight hooks the manhole lid, heaves it out
and drops it: CLANK (0:45.5). The street opens into its section (0:45.75–0:47.1) and the stopwatch
starts (0:46.0). The sewer; up the hatch shaft; the hatch creaks and falls open (0:51.2, 0:51.5).

**s05 GUARD (0:52–1:06).** The corridor in side elevation: the guard's flashlight clicks on
(0:52.35) and its cone slides over the alcove where the crew hides. The camera tilts up to the
stealth map (0:56.0–0:57.0): the pawn's cone sweeps the intersection and the pieces cross in its
dark gaps; step ③ is circled (1:01.65). Tilt down (1:00.5–1:01.5). The Cracker's stethoscope clanks
on a pipe (1:02.0); the guard spins; two gold eyes in the beam (1:02.65); the cat leaps, tips the can,
and the can clatters (1:03.38). The guard sighs, turns away; the crew slips through; the camera pushes
to the far door's dial (1:04.8–1:05.75).

**s06 SAFE (1:06–1:20).** The camera pulls back off the dial to the door; the Cracker steps in and
sets the stethoscope. Cut to the dial with the lock in cutaway (1:09.0): right, left, right; a gate
rises under the fence at 1:10.5, 1:12.5 and 1:14.5 (clicks low, mid, high); the three dots join, step
④ is circled (1:15.0), the fence drops (1:15.5). Cut to the door (1:16.0): the wheel turns, the twelve
bolts withdraw, he heaves, and the door swings open on gold (1:17.0–1:19.0).

**s07 CROSS (1:20–1:36).** Inside on gold: he bags bars; she opens a small box, a red glint (1:21.5),
pockets it with her back to them. His red look to the bags (1:24.4), a cut-paper turn, then to the
open door. The X-split (1:26.0): four panels cut in round the clock (top: him; right: the Cracker
with a bar; bottom: the door's edge; left: her patting her pocket). He moves (1:28.5): the seams turn
RED; his shadow comes out of the gold in the bottom panel. The panels fly off (1:30.0): he drives the
door shut, and BOOM on the bar line (1:32.0): black, the bolts shooting home in the dark. The dial in
RED (1:32.2–1:33.0): s06's lock run backwards. (v2 replaces the black: two flat red frames, then five
frames of the Knight black on a red sunburst, 1:32.00–1:32.29; the dial follows from 1:32.29.) The plan (1:33.0): the red close-up shrinks to a lens
on the chalk dial, the red knight hops his L; the stopwatch stops dead and its hand turns RED
(1:33.5); the bell rings at the side door (1:34.5) and keeps ringing on every beat.

**s08 LOCKED (1:36–1:48).** Black and the Cracker's breath; a scratch of sparks (1:36.85); the match
strikes (1:37.4) and gold rings of light open on her profile, calm, the Cracker beyond her at the
door. He rears back (1:38.4) and we cut on his first blow (1:38.85) to the shot from behind him:
three muffled BOOMs (1:38.85, 1:39.3, 1:39.75). **Her eye in close-up (1:39.9–1:41.1):** her look
drops to the floor (1:40.3) and the corner of her mouth lifts (1:40.65). The camera whips down after
the look (1:41.1–1:41.35). At floor level her heel taps (1:41.75) and knocks hollow (1:42.25); the
floor opens into a section (1:42.25–1:42.85), the dot glows (1:42.95) and a lens joins it to the plan
(1:43.25). The two-shot: the Cracker turns (1:44.3); she raises the roll, lets it fall open (1:45.45)
and lifts the tracing sheet to us (1:46.1–1:47.2). s09 begins on that sheet.

> The close-up at about 1:40 is the **Architect's** eye and profile (`eye_shot`, drawn with
> `F.her`, which faces right on gold), not the Knight's.

**s09 PLAN B (1:48–2:04).** Held on s08's last frame (to 1:48.15). The rewind (1:48.15–1:50.75):
s08, s07, s06, s05 and s04 run backwards 0.4 s each, then s03, under chalk streaks and a double
chevron, the stopwatch spinning back. Played forward (1:50.75–1:51.5): his slam and her dot. Freeze
(1:51.5–1:52.2) and a lens snaps round the dot. Back into s02 and played (1:52.45–1:54.15): his look,
her look; freeze with a lens on her eye (to 1:54.6). The plan from above: the tracing sheet unrolls
(1:54.6–1:55.15) and Plan B is chalked on it with the camera whipping to each: (1) the trapdoor
(1:55.4), (2) her route north to manhole B (1:55.95–1:56.9), (3) four police cars on the half beats
(1:57.15, 1:57.35, 1:57.55, 1:57.75), (4) a red X on the ruby box (1:58.12). The vault by match light
(1:58.9): she lifts the tile; the Cracker's face (1:59.92), a glint, a grin (2:00.28). Section
(2:00.66): down the ladder into the pipe, north, with Plan B's line lighting ahead (to 2:03.75).

**s10 CHECKMATE (2:04–2:16).** The front street, the alarm ringing: the Knight bursts round the car
(2:04.2), flings the sacks in, slams the door (2:05.32). Close on the car's nose (2:05.46): the engine
coughs (2:05.62–2:05.86), the headlight flares and it catches (2:06.02), the car lurches (2:06.5) and
its light fills the frame (2:06.68–2:06.92). Out of the white, the city from above as a chessboard
(2:06.92): his red car speeds off; four police cars slide in like rooks on the beats 2:08.0, 2:08.5,
2:09.0 and 2:09.5; the red marker ring snaps round him (2:10.0): checkmate; the camera rolls (the
film's one Dutch tilt, 2:10.0–2:10.42). His face in the car window, washed red and blue
(2:10.42–2:11.2). The pull-back: manhole B's lid slides off (2:11.95), she and the Cracker climb out
and walk west; the two routes straighten into an X (2:14.0–2:15.2), held to the cut.

**s11 END (2:16–2:24).** s10's last frame splits along its X into four triangles that fly apart
(2:16.0–2:16.62): her gloved fist under a street lamp. Her fingers open on the ruby (2:16.55–2:17.3);
it glints, an X of light (2:17.5, the one celesta ping); she closes her hand (2:18.45). Dawn at the
table (2:19.0): her queen comes in low and knocks his knight (2:19.85), which lands on its side
(2:20.0). The camera rises to the whole plan; the chalk X lifts and grows into the title X, landing on
the last chord (2:22.0), white over red this time; DOUBLE (2:22.2) and CROSS (2:22.45) slide back in;
the ruby lands as the red dot (2:23.0); black (2:23.5), the dot gone by 2:23.9.

### 9.7 Sound

- **The score.** Heist jazz at 120 bpm in D minor, one piece from the first chalk tap to the last
  chord, every scene starting on a bar line. THE THEME (vibraphone) is played plainly in s02–s03. At
  the betrayal (bars 42–45, from 1:24) it returns in exact mirror inversion, low and minor, and its
  Phrygian close lands as the vault door BOOMs on the bar line at 1:32.0. In s09 the theme returns
  upright in D major (the inversion inverted). The end resolves on D6/9 as the title lands.
- **The clock.** A dry woodblock on every beat from 0:46.0 to 1:33.5, the stopwatch's sound.
- **The rewind** is the film's own mix, cut where the picture rewinds to and played backwards and sped
  up (or forward, where the picture catches).
- **Foley.** All synthesised in `mix.py` (chalk, paper, pieces, the manhole, drips, the hatch, the
  flashlight, the stethoscope, the cat and the can, dial clicks pitched D, F, A, the fence, the bolts,
  the vault's groan and BOOM, gold, the bell, the match, the hollow knock, the tracing paper, the
  engine, sirens), plus breaths and steps cut from `films/opposite/audio/gen/`. v1 and v2 used no
  paid generation; v3 adds the voices (9.11).
- **Measured (v1).** -16.01 LUFS, true peak -1.30 dBTP, no clipping; 420 cues (389 by the sections,
  31 auto-spotted, all in s07; 0 missed); worst sync 20 ms.

### 9.8 Production

- **Team.** The director made the foundation and s01–s03, s08–s11; one animator agent made s04–s07
  and the bank sets (`bank.py`); one audio agent made the score and mix. Never more than two agents
  at once.
- **Commits.** `becc819` bible, palette, timeline, kit → `740653d` plan, tilting camera, cast →
  `0cf43b4` s01–s03 → `b0943d0` s08 → `e353f36` s09–s11 → `0c5ceb9` score and mix → `244c604`
  s04–s07 and the bank set.
- **Delivered v1.** `final/double_cross_preview.mp4`: 3,456 frames, 144.0 s, about 7.7 Mb/s, -16.1
  LUFS after AAC. The glitch scan raised 27 flags, all deliberate.

### 9.9 What it introduced

- The film's own blueprint as the narrator: the story is what happens when someone leaves the line.
- The tilting plan camera (`P.PlanCam`): one camera that is both the diagram and the world.
- A rewind built from pure-function scenes: s09 renders earlier scenes backwards, and the mix plays
  its own audio backwards to match (`REWIND` / `FREEZES` tables read by both).
- The X-split screen (`K.x_split`) and the tracing-paper overlay (`K.tracing`).
- Profile close-ups as a module (`faces.py`) and sets in set px with explicit cameras (`bank.py`).
- A mix that finds beats by name, plays missing scenes from the bible and spots any unanswered cue
  from its words.

### 9.10 v2: the shot types

On 10-24 the user shared a reference listing six shot types, cuts one frame before the beat, and four
transitions, and asked for a new version using them, with no more than two agents in total. What we
adopted, adapted and skipped, and how each is built, is in [SHOT_TYPES.md](SHOT_TYPES.md).

v2 is commit `9ea5f1b`: `films/double_cross/shots.py` plus inserts in seven scenes (the nine rows
below, as in the bible's v2 table). The picture of 9.6 is otherwise unchanged, and so is the sound (every insert sits on a sound already in
the mix). Delivered as `final/double_cross_v2_preview.mp4`: 3,456 frames, 144.0 s, 7.71 Mb/s,
138.85 MB, -16.1 LUFS with a peak of -0.6 dBFS after AAC; the mix is bit-identical to v1's. The
glitch scan raised 35 flags: v1's 27 and 8 at the new inserts, all deliberate.

| Film time | Scene | Insert |
|---|---|---|
| 1:03.38 | s05 | Punch-in ×6 on the tin can as it clatters (5 frames) |
| 1:17.00 | s06 | Gold flash as the seal breaks (2 frames) |
| 1:32.00 | s07 | Red flash on the BOOM (2 frames) |
| 1:32.08 | s07 | The Knight black on a red sunburst (5 frames), in place of v1's black |
| 1:39.29 | s08 | Punch-in ×4 on his fist at the second blow (5 frames) |
| 1:48.17–1:54.17 | s09 | Paper-strip slips at every rewind join (2 frames each; 1 at the last) |
| 2:05.62 | s10 | Punch-in ×4.5 on the dead headlight at the first cough (5 frames) |
| 2:09.92 | s10 | Black flash before checkmate (2 frames) |
| 2:19.88 | s11 | Punch-in ×3, with one red wedge, as the queen knocks the knight over (5 frames) |

### 9.11 v3: the review fixes and the voices

**Withdrawn in v4** (9.12), except the voices.

On 10-24 the user had me review the whole film, then asked "fix it, and do you think voice should
be used?". They chose a murmured briefing plus two touches of voice, and approved 200–250 credits
for it.

**The picture.** Six fixes in s01, s02, s03, s09 and s10. s11 was re-rendered because it opens on
s10's last frame. s04–s08 are as in v2, and the s04–s05 reframing the review raised was left alone.
The bible's v3 table has the details.

| Film time | Scene | Fix |
|---|---|---|
| 0:00–0:07 | s01 | It opens on the bank at night, at s04's eye level. Chalk dots mark the corners of the front (0:00.5–0:02.0) and dotted lines join them. The street folds flat, back to front (s04's pop-up run backwards, 0:02.5–0:03.5), as the camera tilts up to straight down (0:02.75–0:04.0). The outline lies down onto the blueprint and the plan rules itself in from it (0:04.0–0:07.0). |
| 0:11.1 | s01 | A gold lens opens off the landed X on the vault's gold, through its door; s02 closes it. |
| 0:21–0:24 | s02 | The briefing, wide: the crew round the table under the swinging lamp. Her chalk taps the X twice (0:21.25, 0:21.5), his red look goes down to it (0:21.6), hers goes across to him (0:22.5), and her chalk goes in toward manhole A. |
| 0:24–0:35 | s03 | Her chalk hand reads as hers (a bold white edge). Lenses open on step ① (manhole A's lid, 0:25.05–0:26.3) and step ③ (the guard and his light, 0:29.55–0:30.75). |
| 1:58.12–1:58.8 | s09 | Plan B one beat per mark: a hold on the red X, then a whip back to both plans before the cut. |
| 2:11.2–2:13.5 | s10 | Her way out, full frame: the back street looking north. Manhole B's lid is knocked up (2:11.47) and dragged aside. She climbs out, then the Cracker, and they walk west under the street lamp as the police lights pool beyond the roofs. Then back to the board for the X. |

**The voices** (Magnific, ElevenLabs eleven_v3, 114 credits, in `audio/gen/`). These are the film's
first voices, and it stays wordless.

- **The briefing is murmured in three voices** (0:21.05–0:22.45 and 0:24.1–0:34.7), and who speaks
  follows the picture:
  - each line is cut into syllables at the dips in its level, and the inner syllables are
    shuffled, so it keeps its voice and cadence but says nothing;
  - it is low-passed and set about 13–16 dB under the score;
  - the Knight's slam ends it.
- **The Knight's grunts** use his own strained voice, at the bags (1:26.4) and at the vault door
  (1:30.12, held while it swings).
- **Her breath of a laugh** comes as the corner of her mouth lifts (1:40.59).
- **The rewind.** s09's rewind carries the voices, because it is cut from the mix.

**Measured.** -16.01 LUFS, true peak -1.30 dBTP, no clipped samples. 449 cues: 421 realised by the
sections, 28 auto-spotted (all in s07, as before), 0 missed. The worst cue-to-event offset is 25 ms;
no measured onset is more than a frame out.

Delivered as `final/double_cross_v3_preview.mp4`, encoded as in SYSTEM.md section 9: 3,456 frames,
144.0 s, 7.72 Mb/s, 138.9 MB, -16.1 LUFS with a true peak of -0.9 dBFS after AAC. The glitch scan
(run on v2's preview too, for comparison) flags 37 frames against v2's 39. All are at deliberate
cuts, inserts, rewind slips and whips, and none is at a v3 change.

### 9.12 v4: slower, the guard rebuilt, back on the system

On 10-25 the user said of v3: "This version is too fast and it also skips the guard part we kind
of downgraded rather than upgraded also drifting away from our system". They were right on all
four:

- v3 packed new content (a bank opening, a gold lens, step lenses, a back street) into the same
  seconds;
- it skipped the guard's reframing although they had asked for the review's fixes;
- its new shots were not the film's own devices.

**Back to v2's picture.** s01–s03 and s09–s10 are v2's code again (`9ea5f1b`), and s11 is
re-rendered after them. s08 keeps only v3's laugh cue. v3's voices stay.

**Two changes, each made with time, not content.** Both scenes gained two bars.

| Film time | Scene | Change |
|---|---|---|
| 0:21–0:28 | s02 (16 s) | The side shot carries the briefing. The three pieces stand on the plan between them. She leans in, murmuring, and taps the plan twice beside them on the beat (0:22.0, 0:22.5); she straightens, and the Cracker nods with a low hum (0:22.75). His red look (0:23.5) and her white look (0:24.5) each get a bar. She takes the chalk (0:26.0), and the camera tilts down over the table onto the plan (0:26.0–0:28.0), landing on s03's first frame. It is the film's own plan-as-map tilt, so the people and the plan are one place. |
| 0:56–1:14 | s05 (18 s) | Rebuilt to read at phone size: framed close (the figures half the frame, the corridor filling it), one continuous shot with the camera moving with the action. His light clicks on (0:56.5) and the camera pans along the beam to the crew in the doorway as its patch touches the edge (0:59.0). The stealth map (1:00.0–1:05.5) shows the hops (1:01.5, 1:02.5, 1:03.5). The near miss is one beat at a time, 4.5 s from the step to the sigh where v2 had 2.4 s: the step (1:05.5), the breath (1:06.0), the CLANK (1:06.5), a whip to the guard as he spins (1:06.62–1:07.3), his light on two gold eyes (1:08.0), the arch (1:08.5), the leap (1:09.0), the clatter (1:09.5, v2's punch-in), his sigh (1:10.0), and the walk-off as the crew slip into the dark (1:10.5). Then the push to the dial (1:11.5–1:13.0, step 4 at 1:12.5). |

- **The edit.** 2:32, 3,648 frames. The heist clock is now derived from the timeline
  (`K.film_start`), and runs from 0:50.0 to 1:41.5; s06 and s07 take their film times from it.
  s09's rewind rows and freezes follow the new lengths.
- **The sound.** The score is re-timed to the new bars:
  - bar 11: the band drops to a murmur under the briefing;
  - bar 12: the low held D on her look;
  - bar 13: a rising paper whoosh under the tilt, and the bass walks up into the theme;
  - s05: the tiptoe bass from bar 30, walking up to the clank; a whip whoosh; the held breath as
    his light finds the cat; the band back at bar 36.

  Two new s05 cues: a breath held in the doorway (0:58.9) and the whip's whoosh (1:06.62). The
  voices are v3's, placed on v4's picture: her murmur (0:21.25–0:23.3) and the Cracker's hum
  (0:22.75) in s02, the murmur over the plan (0:28.1–0:38.7), the Knight's grunts (1:34.4, 1:38.12)
  and her breath of a laugh (1:48.59).
- **Measured.** -16.01 LUFS, true peak -1.30 dBTP, no clipped samples. 429 cues: 401 realised by
  the sections, 28 auto-spotted (all in s07, as in v2), 0 missed. The worst cue-to-event offset is
  25 ms, and no measured onset is more than a frame out (worst 20.1 ms). The clock's 103 ticks are
  all within 0.5 ms of the beat.

Delivered as `final/double_cross_v4_preview.mp4`, encoded as in SYSTEM.md section 9: 3,648 frames,
152.0 s, 7.71 Mb/s, 146.6 MB, -16.1 LUFS with a true peak of -1.1 dBFS after AAC. The glitch scan
flags 36 frames. Outside s02 and s05 every flag is at a frame v2's preview also flags (aligned to
v4's times), and nothing is new. In s02 the six flags are its designed cuts (table, faces, the
side shot). s05, one continuous shot, has none.

That file played without sound in the Claude app on the user's phone, though its soundtrack
measures normal. A 99 MB copy at 5 Mb/s video, `final/double_cross_v4_phone_preview.mp4`, played
silent too. Both are built like OPPOSITE full's preview, which played with sound on the same
phone, so the cause is on the playback side (SYSTEM.md section 9).

### 9.13 v5: the double cross, easy to follow

On 10-25 the user said of v4: "i find it hard to understand that its a burglary being planned and
the lady initially crosses one and then double crosses the other etc and what is in her hand how
alarm goes off and how the flashback explains the second exit plan and how police comes and
catches first". Asked whether to change the story or keep it and make it clear, they chose to
keep it: the Knight locks the other two in and runs with the gold, she had planned for it, the
police catch him, she and the Cracker leave by the sewer, and she keeps the ruby.

**Each question gets a picture, and each picture its own bars** (v4's lesson: time, not
crowding). The film grows to 2:54 (4,176 frames, 87 bars). The bible's v5 table maps each
question to its answer.

| Film time | Scene | Change |
|---|---|---|
| 0:00–0:16 | s01 (16 s) | v3's opening with a bar for each part: the bank at night, its front marked in chalk (0:00.5–0:02.5) and held; the street folds flat into the blueprint (0:04.0–0:06.0); the plan rules itself in (0:06.0–0:09.0); the title X (0:10.0–0:11.5); the X lands on the vault (0:13.0) and a gold lens opens on the gold it marks, glinting twice (0:13.1–0:14.5). |
| 0:25.9–0:27.9 | s02 (18 s) | A bar close over the plan: her gloved finger taps the X twice (0:26.5, 0:27.0), and the gold beside it glints. |
| 0:47.0–0:47.7 | s03 | She draws the bell on the side door and taps it (0:47.5): it rocks, with one damped tink, the alarm's own note. |
| 1:35.5–1:38.6 | s07 (20 s) | The ruby, close: her glove lifts it out of the box into the light (1:36.7–1:37.3), where it flares, and then it goes into her pocket (1:38.0–1:38.6). |
| 1:50.5–1:54.0 | s07 | His L reaches the side door on the plan and the bell rings (1:50.5). Then the door itself, from the alley: it bursts open (1:51.0), he charges out with the bags, and the bell over it rings and rings as the camera pushes in. |
| 2:10.2–2:14.2 | s09 (22 s) | The night before, in the dot's lens: she is on a ladder under the vault floor, her torch cuts the trapdoor up through the slab (2:10.95–2:12.3), she pushes the block up a crack, her light on the gold (2:12.45), and sets it back as a tile (2:13.15–2:13.45). |
| 2:16.6–2:22.4 | s09 | Plan B, one mark at a time, over a bar of D major: (1) the trapdoor (2:17.4); (2) her route to manhole B (2:17.95–2:18.9); (3) his red L to the side door, the bell ringing there, and the police closing on his car (2:19.2–2:20.75); (4) the red X on the ruby box (2:21.35). |
| 2:30.9–2:36.0 | s10 (18 s) | The alarm calls the police. The bell's rings roll out over the city, one per beat (from 2:31.0). As the first ring reaches each of four dark police cars, its bar switches on (2:32.5, 2:33.0, 2:33.5, 2:34.0), and the first one's lights stop him dead (2:32.55). They slide in like rooks (2:34.0–2:35.5): checkmate (2:36.0). |
| 2:37.2–2:40.9 | s10 | The arrest: the street, boxed in by police cars under the ringing bell. He climbs out with a sack (2:37.62–2:38.3), looks east and west, lets it drop so the gold spills (2:39.0–2:39.12), and puts his hands up in the light (2:39.36–2:39.72). |

- **The edit.** The heist clock runs from 0:56.0 to 1:49.5 (107 ticks). s09's rewind follows s07's
  new length, and the freeze on the dot holds while the night before plays in its lens.
- **The sound.** Two new synths, `bell_tink` (her tap on the bell: the alarm's note, damped) and
  `torch_cut` (the torch's roar, hiss and sparks).
  - The ruby lifts on a rising string harmonic and flares on a glassy shimmer (the celesta stays
    the ruby's in s11).
  - The side door gets a BANG and the bell over it, 4 dB louder over the push in.
  - The night before has a deep whoosh into the lens, drips and a drone, the torch, stone
    grinding, and a reverse whoosh out.
  - s10's police cars each get a clunk, a thump and a siren whoop, his brakes screech, and at the
    arrest the bell, the police engines idling, the sack and the gold, and a held low string note
    under his hands.
- **Measured.**
  - -16.01 LUFS, true peak -1.30 dBTP, no clipped samples; the limiter takes at most 5.3 dB (the
    BANG at 1:51.0).
  - 473 cues: 449 realised by the sections, 24 auto-spotted (all in s07), 0 missed.
  - The worst cue-to-event offset is 30 ms, and no measured onset is more than a frame out
    (worst 20.1 ms).
  - The clock's 107 ticks are all within 0.5 ms of the beat.
- **Fixed on the way.**
  - **s10's first full render crashed.** The arrest's new helper `_door(c, g)` (the driver's door)
    had the same name as the street shot's `_door(t)`, and the later definition replaced the
    earlier, so the street shot called it with the wrong arguments. The stills checked had all been
    in the new shots. It is now `_driver_door`.
  - **The QA's "limiter at most" read -14 dB** that was not there. It divided output by input per
    sample, and the 4 ms fade at the head of v5's near-silent first samples counted as limiting. It
    now reads the limiter's own gain (5.3 dB), and the audio is bit-identical.

Delivered as `final/double_cross_v5_preview.mp4`, encoded as in SYSTEM.md section 9: 4,176
frames, 174.0 s, 7.71 Mb/s, 167.7 MB, -16.1 LUFS with a true peak of -0.8 dBFS after AAC.
The glitch scan flags 35 frames:
- 25 are at frames v4's preview also flags (aligned to v5's times);
- 9 are at v5's new cuts, wipes and whips: s02's tap insert in and out (0:25.92, 0:27.92), s07's
  ruby close-up in and out (1:35.5, 1:38.0), the dot's lens opening over the frame (2:10.42,
  2:10.46), the whip to Plan B's red X (2:21.13, 2:21.21) and the cut to the arrest (2:37.21);
- one is s10's cut to the car's nose (2:29.5), a designed cut that v4's scan let pass.

A phone-size review of every new beat in the delivered file reads clearly.

### 9.14 Files

| Path | What it is |
|---|---|
| `films/double_cross/docs/BIBLE.md` | The bible: story, plants, cast, palette, camera, devices, world, timeline, beats, sound plan. |
| `films/double_cross/kit.py` | Palette, `scene_setup`, the annotation devices, the stopwatch, pieces, cars, tracing, X-split, rewind marks. |
| `films/double_cross/plan.py` | The plan's geometry, routes, `PlanCam`, the table and Plan A drawing. |
| `films/double_cross/bank.py` | The night sets in set px and their camera `Bk.Cam`. |
| `films/double_cross/cast.py`, `faces.py` | The figures, props and profile close-ups. |
| `films/double_cross/shots.py` | The v2 shot-type helpers (SHOT_TYPES.md, Part C). |
| `films/double_cross/scenes/s01_title.py` … `s11_end.py` | The eleven scenes. |
| `films/double_cross/timeline/build_timeline.py`, `timeline.json` | The edit: eleven scenes, hard cuts. |
| `films/double_cross/audio/mix.py` | The score, foley, voices, rewind and master. |
| `films/double_cross/audio/gen/*.mp3` | v3's voice takes: the briefing's lines in three voices, the Knight's grunts, her laugh. |
| `films/double_cross/final/double_cross_preview.mp4` | The delivered v1 preview (not in git). |
| `films/double_cross/final/double_cross_v2_preview.mp4` | The delivered v2 preview, with the shot types (not in git). |
| `films/double_cross/final/double_cross_v3_preview.mp4` | The delivered v3 preview, with the review fixes and the voices (not in git). |
| `films/double_cross/final/double_cross_v4_preview.mp4` | The delivered v4 preview: v2's picture, the briefing given time, the guard rebuilt (not in git). |
| `films/double_cross/final/double_cross_v4_phone_preview.mp4` | A 99 MB copy of the v4 preview at 5 Mb/s, made while chasing the silent playback; it played silent too (not in git). |
| `films/double_cross/final/double_cross_v5_preview.mp4` | The delivered v5 preview: the burglary, the ruby, the alarm, the night before and the arrest made plain (not in git). |

---

## 10. DOUBLE CROSS, the OPPOSITE cut (2:54)

The user asked: "Make a version of double cross with opposite style properly". This is DOUBLE
CROSS v5's story told in OPPOSITE (full)'s grammar, from a new bible
(`films/double_cross_opposite/docs/BIBLE.md`), made with two agents in total.

### 10.1 What it takes from each film

- **From DOUBLE CROSS (v5):** the story, the cast, the plants and payoffs, and v5's clarity. Each
  question the user asked about v4 still gets a picture of its own:
  - the burglary being planned;
  - what is in her hand (the ruby);
  - how the alarm goes off;
  - how the night before explains her way out;
  - how the police come and catch him.
- **From OPPOSITE:** how it is told:
  - the camera is an eye: who looks at what tells the story, each look a dotted sight line in its
    owner's colour;
  - a flat Bass elevation and section of one street, two buildings facing across it;
  - over-the-shoulder shots that mirror each other (hers at the crew's window in s02, his at the
    bank's curb in s10), a split-screen mirror (s03), a dive into an eye (s08), POVs (s07, s09), a
    Vertigo shaft (s04);
  - eased push-ins and jump-ins on the beat; one Dutch tilt (the Cracker's panic, s08);
  - three marker rings (the gold, the vault, him) and the rest of the annotation layer;
  - AMBER lamplight on a teal NIGHT; crisp cut paper; no blur.
- **Left out** (the blueprint version's devices): the tilting plan camera, the pop-up world, the
  chess pieces and the chessboard city, BLUE paper and chalk, circled step numbers, the stopwatch,
  punch-ins, flashes, slips, the sunburst, the X-split, whips, motion blur, the rewind and the
  tracing paper.

### 10.2 The story

Midnight, in a room high in a tenement: three thieves plan. Across the street is the bank, with
its guard's lamp low behind barred windows, an alarm bell over its side door and a manhole in the
road. Her look goes to the guard, the bell, the manhole. On the plan her finger traces the way in,
taps the bell (not that way) and taps the vault twice, and a red ring closes round the gold. His
look goes to the gold and his jagged arm reaches for it. Her look goes into his eye, and then,
when nobody is watching, down to the sewer under the vault. She pulls the lamp's cord.

Down the manhole, along the sewer, up through a hatch, past the guard's flashlight (a clank, a
cat, a tin can). The Cracker opens the vault on gold. She pockets a ruby from one small box, and
no one sees. The Knight shuts the vault on the other two, spins the dial, and bursts out through
the side door with the gold; the alarm bell rings.

A match flares. The Cracker panics; she is calm. Through the walls she hears the bell and smiles.
We dive into her eye, to the night before: she cut a trapdoor up through the vault floor and set
it back as a tile. Her heel knocks: hollow. They go down into the sewer, and above them the
Knight's engine coughs while the bell wakes the street; she passes right under him. The police box
him in, every look in the street converges on him, the third red ring closes round him, and he
puts his hands up. Over his shoulder a manhole lifts at the tenement's curb: she climbs out, meets
his look, pats her pocket and walks away. The ruby opens on her palm.

**DOUBLE CROSS and OPPOSITE:** he crosses the crew, and she had crossed him first. The film's
first look is hers, from the window at the bank; its last is his, from the bank's curb at her
window.

### 10.3 Form and foundation

- **Form.** 11 scenes, hard cuts on the beat (120 bpm), every scene starting on a bar line: s01
  title 0:00, s02 crew 0:14, s03 plan 0:30, s04 night 0:48, s05 guard 1:02, s06 safe 1:20, s07
  cross 1:34, s08 locked 1:54, s09 plan B 2:08, s10 checkmate 2:26, s11 end 2:46. 2:54, 4,176
  frames.
- **`kit.py`:** OPPOSITE's palette (`INK`, `PAPER`, `AMBER`, `RED`, `NIGHT`, `STEEL`, `DEEP`,
  `SHUT`, `POLICE`), `scene_setup`, and OPPOSITE full's annotation devices re-exported.
- **`street.py`:** the one street, in elevation (`St.draw_elevation`) and in section. Every state is
  an argument: the lit windows, the guard's light, the clock, the bell, the side door, the car,
  both manhole lids, the street lamp, the figures, the sewer under the road, the trapdoor's shaft.
  So every scene draws the same street at its own moment.
- **`bank.py`, `cast.py`, `faces.py`:** DOUBLE CROSS's night sets, figures and profiles, forked
  into this palette. **`room.py`:** the crew's room.

### 10.4 Scene by scene (film times from the scene modules' constants)

| Scene | What it shows |
|---|---|
| s01 TITLE (0:00–0:14) | A red dot ticks in the black (0:00.25–0:00.75). The Psycho bars race, DOUBLE and CROSS assemble, and a paper strip and a red strip cross into an X (0:02.75, 0:03.0). The halves part and the letters become windows (0:04.3). Night falls (0:05.5) and the moon drops in. The cutaway: the storeys open from the street up (0:06.75–0:07.75), the road opens down to the sewer (0:08.0–0:09.0) and the vault's gold glows (0:08.5). The city goes to bed light by light (0:09.0–0:10.5), leaving the crew's room, the guard's lamp and the gold. The push in on the crew's room (0:11.5–0:14.0). |
| s02 CREW (0:14–0:30) | The room, wide, at 11:58. Three profile cameos on the beat: her (0:16.0), the Cracker (0:17.5, a glint on his spectacles), the Knight (0:19.0, his ember brightens). Over her shoulder, her look goes to the guard's window (0:21.0), to the bell (0:22.25; a lens and one damped tink at 0:22.6) and to manhole A (0:23.5; a dot ring). She turns from the window (0:24.75), spreads the plan (0:26.0) and begins (0:28.0). |
| s03 PLAN (0:30–0:48) | Straight down on the plan: her finger traces the way in (0:30.5–0:33.25), taps the bell (0:33.75: not that way) and the vault twice (0:34.5, 0:35.0), and the first marker ring closes round the gold (0:35.0–0:35.4). The looks: his to the gold (0:36.0), the Cracker's to the vault door (0:36.5), hers to his face (0:37.25) and then down to the sewer under the vault (0:38.25), where a ripple answers. The golden arm grows across the table (0:39.6–0:40.6) and snaps back (0:41.0). The split mirror (0:42.0): her look crosses into his eye (0:42.6) as the halves press in on the beat. She pulls the lamp's cord (0:46.3): dark. |
| s04 NIGHT (0:48–1:02) | The street at 11:59: the three cross to manhole A, each with footstep dots in their colour; the Knight hooks the lid (0:50.55) and levers it up on edge. Low angle from the road: the lid drops aside (0:51.25) and they go down one a beat (0:51.5, 0:52.0, 0:52.5) as the bank's clock strikes midnight (0:52.0). The Vertigo shaft from above, a dolly zoom, with three splashes (0:53.5–0:54.5). The section, dark: their dots along the sewer; a callout on the hatch, where his hand cracks it open (0:57.75) and opens it (0:58.9); they climb up into the hall's dark corner one a beat (0:59.5–1:00.5); the Cracker shuts the hatch behind them (1:00.65–1:00.95). |
| s05 GUARD (1:02–1:20) | The hall, framed close (DOUBLE CROSS's corridor, mirrored to keep s04's screen direction). The guard's flashlight clicks on (1:02.5) and sweeps every 2 s; in the dark corner the crew show only their rims and eyes, and the light's patch stops at the Knight's nose (1:05.0). They cross in the dark gaps one at a time: her (1:07.15), the Knight (1:08.15), the Cracker (1:09.15), his AMBER heartbeat thudding. The near miss: the Cracker breathes out (1:11.5) and his stethoscope clanks on a pipe (1:12.0); the guard spins round (1:12.25) and a callout finds two AMBER eyes on the crates (1:13.5); the cat arches (1:14.0) and leaps (1:14.5), and the can clatters (1:15.0); the guard sighs (1:15.75) and walks off on his round (1:16.25). Down to the vault door and the push in on its dial (1:18.0–1:20.0). |
| s06 SAFE (1:20–1:34) | The vault door: the Cracker kneels (1:21.25) and sets the stethoscope to the steel (1:21.95). Extreme close-up: two ticks run up the tube as AMBER ripples (1:23.5, 1:24.0). The dial from straight above: right, left, right (from 1:24.75, 1:26.25, 1:27.75), a click and a ripple at each gate (1:26.0, 1:27.5, 1:29.0); the fence drops (1:29.5). The wheel turns (1:30.45), the twelve bolts withdraw (1:30.53–1:30.89) and the door swings open on gold (from 1:31.1). Three looks go in: his RED to the gold (1:32.5), the Cracker's AMBER (1:33.0), hers PAPER to the deposit boxes (1:33.5). |
| s07 CROSS (1:34–1:54) | Inside the vault: the Cracker hands the bars up and the Knight bags them; behind them she opens one small box (1:34.95–1:35.5). The ruby, close (1:35.5–1:38.0): it glints, her gloved hand comes in (1:36.0), takes it (1:36.5), lifts it into the light, where it flares (1:37.0), and takes it away; back on her, it goes into her coat pocket (1:38.4), her back to them. His look: RED to the sacks (1:40.4), over his shoulder to the open door (1:41.1), and to the two of them, their backs turned (1:41.6–1:42.75). He heaves up both sacks (1:43.2) and walks out. His POV through the closing door (1:45.5): his hands drive it shut, the two inside turn too late, and the slot of gold closes: BOOM (1:48.0), black. The dial, in RED, spun (1:48.45–1:48.95). The section at 12:19: the second marker ring closes round the vault with the two in it (1:49.3), and his RED dots run across the hall to the side door (1:49.5–1:50.75). The side door from the street bursts open (1:51.0, the one shake); he runs for his car with the sacks while the alarm bell rings and rings, and the camera pushes in on it (1:51.7–1:54.0). |
| s08 LOCKED (1:54–2:08) | Black; a match strikes (1:55.6) on her calm profile. The Cracker's panic, with the film's one Dutch tilt (1:56.0), and his fists on the door (1:57.5, 1:58.0, 1:58.5). Level again: the bell, faint, through the walls (2:00.0); the corner of her mouth lifts (2:00.9). The dive into her eye (2:02.0–2:02.5), to the night before: she cuts up through the vault floor (2:03.0–2:04.35), pushes the block up into the gold's light (2:04.5) and sets it back as a tile (2:05.2–2:05.5). Out of her eye (2:06.0); her heel taps and the floor knocks hollow (2:06.75). |
| s09 PLAN B (2:08–2:26) | She lifts the tile (2:08.2) and the Cracker's match lights his grin (2:10.4). The shaft, in section: they slide down into the sewer (2:11.2–2:13.6). The street, in section (2:15.0): the Knight flings the sacks into his car and the engine coughs (2:16.0–2:17.7), while the bell's strokes wake the tenement storey by storey (2:17.5–2:19.0). He gets out onto the gully grating and kicks the tyre, and she stops right under him: her view up through the grating at his boots (2:19.0–2:20.55). The engine catches (2:20.0). They climb manhole B's shaft (2:23.0–2:24.35) as the police lights begin to sweep. |
| s10 CHECKMATE (2:26–2:46) | His car lurches off and a police car swings in nose to nose (2:26.45); another slides in behind (2:27.15). His face in the side window, his eyes darting (2:29.0). The section: every look in the street goes to him, the neighbours', the city's and the police light's (2:31.0–2:34.0), and the third marker ring closes round him (2:35.0). The bank's front: he climbs out with a sack, drops it so the gold spills (2:37.75) and puts his hands up (2:38.1). Over his shoulder, manhole B's lid slides off at the tenement's curb (2:39.4); she climbs out and the Cracker after her. Their looks meet (2:41.2); she pats her pocket, a red glint (2:41.8), and walks away. The pull-back to the whole block (2:43.0–2:45.8). |
| s11 END (2:46–2:54) | Her palm opens on the ruby (2:46.4). It glints (2:47.5, the celesta's only note) and her fist closes (2:48.2). The elevation's windows fly into the title (from 2:48.52); DOUBLE CROSS stamps on black (2:49.25) and the strips cross into an X (2:49.5, 2:49.75). The title is cut along the red strip and the halves fly apart (2:50.0–2:50.45). The red dot beats twice (2:51.45, 2:52.05) and is gone (2:52.95). Silence from 2:53.5. |

### 10.5 Sound

`films/double_cross_opposite/audio/mix.py` (3,491 lines, made by the audio agent) is the score, the
foley, the voices and the master in one file. It is locked to the scene modules: every beat a
section uses is read on every run from its scene's constants, or else from its own cue's words.

- **The score.** Herrmann strings at 120 bpm in D minor on the Psycho chord (D F A C#). Her note is
  D, high; his is C#, low, a semitone and octaves under hers.
  - THE THEME (DOUBLE CROSS's tune) is plucked under the plan.
  - At the betrayal it is inverted, low in the cellos and basses, its last D held onto the BOOM
    (1:48.0).
  - It turns upright again from the dive into her eye, and plays in D major at the end.
- **Sources.** Nothing new was generated: there is no paid audio in this film.
  - The strings, harp, bells and celesta are OPPOSITE full's instruments; the foley is DOUBLE
    CROSS's synths.
  - Recordings: OPPOSITE's breaths, gasps, steps, a handle and stairs, and DOUBLE CROSS's voice
    takes (her murmur, its syllables shuffled so it never says a word; the Knight's grunts; her
    breath of a laugh).
  - The police are cars: sirens, engines, brakes, doors.
- **The celesta plays once**, on the ruby's glint in s11 (2:47.5). The mix refuses a second note.
- **Cues.** All 458 scene cues are realised: 347 by the scene sections, 111 from their words. Of
  321 measured hits the worst is 18.9 ms off, none by a frame. Both clocks tick on every beat,
  within 0.7 ms.
- **The master.** 48 kHz stereo 24-bit, 174.000 s: -16.0 LUFS integrated, a true peak of -1.4 dBTP
  (the limiter's ceiling is -1.4, since -1.3 read -1.29 in ffmpeg), digital silence from 2:53.5.
  - It builds from a hushed heist to a loud end. Per scene: s01 -17.5, s02 -19.5, s03 -17.6,
    s04 -20.7, s05 -20.6, s06 -20.1, s07 -15.7, s08 -15.3, s09 -13.7, s10 -14.0, s11 -14.6 LUFS.
- **The floor.** The first master fell to -37.3 LUFS short-term (3 s) in the heist's hush (the
  dial, 1:24.7), quiet enough to sound like a dropout on a phone speaker. The room tone and the
  bank's tick went up 3 dB, and a soft held string bed (D and A, a high A harmonic) now runs under
  the stealth. The lowest short-term reading is -28.9 LUFS, the same as DOUBLE CROSS v5's floor.

### 10.6 Production and what it introduced

- **Team.** The director wrote the bible and the foundation, made s01–s03 and s08–s11, reviewed
  every frame, rendered, encoded and committed. One animator made s04–s07 and one audio agent made
  the mix: two agents in total, the user's limit.
- **Retelling in another film's grammar.** The story and sets come from one film and the camera and
  handwriting from another. The bible lists what is kept from each and what is left out.
- **One street with every state an argument** (`street.py`), drawn by nine of the eleven scenes.
- **The ending runs the opening backwards.** OPPOSITE's title turns letters into windows; s11 turns
  the street's windows back into DOUBLE CROSS's letters.
- **Scenes calling scenes.** s10 turns heads with s09's `_turn`; s11 builds its title from s01's
  glyphs.

**Delivery.** `final/double_cross_opposite_preview.mp4` uses SYSTEM.md's two-pass encode:
- 1080×1920, 24 fps, 4,176 frames, 174.000 s;
- H.264 High at about 7.50 Mb/s, AAC-LC 48 kHz stereo at about 198 kb/s, 7.70 Mb/s overall;
- 167.5 MB;
- after the AAC encode, -16.1 LUFS with a true peak of -0.9 dBFS.

Workflow notes:
- While the agents worked, the director's seven finished scenes were rendered to full-size film
  segments ahead of time (named as `engine.render ... all` names them). The final `all --only
  s08,s09,s10,s11` then drew only s04–s07 plus the four scenes the continuity fixes touched.
- The master's glitch scan flagged 49 frames away from the scene cuts, and each one is designed:
  - 31 are cuts or snaps between shots inside scenes;
  - 18 are fast moves: the title's last bar and its paper strip racing in (0:02.5), the dive into
    her eye and out of it (2:02.25–2:02.46, 2:05.79–2:06.0), and the end title's halves flying
    apart (2:50.67–2:50.83).

### 10.7 Files

| Path | What it is |
|---|---|
| `films/double_cross_opposite/docs/BIBLE.md` | The bible: the story, plants, cast, look, the annotation layer, the world, the timeline, the beats, the sound plan. |
| `films/double_cross_opposite/kit.py` | The palette, `scene_setup`, OPPOSITE full's annotation devices re-exported. |
| `films/double_cross_opposite/street.py` | The street in elevation and in section. |
| `films/double_cross_opposite/bank.py`, `cast.py`, `faces.py` | DOUBLE CROSS's night sets, figures and profiles, in this palette. |
| `films/double_cross_opposite/room.py` | The crew's room. |
| `films/double_cross_opposite/scenes/s01_title.py` … `s11_end.py` | The eleven scenes. |
| `films/double_cross_opposite/timeline/build_timeline.py`, `timeline.json` | The edit: eleven scenes, hard cuts. |
| `films/double_cross_opposite/audio/mix.py` | The score, foley, voices and master, locked to the scene modules (`--qa`, `--only`, `--stems`, `--without`, `--skip-missing`). |
| `films/double_cross_opposite/final/double_cross_opposite_preview.mp4` | The delivered preview (not in git). |

---

## 11. THIN ICE (3:08), in depth

The user asked: "Make a completely new video a new story indepth as a expert now." THIN ICE is a
new story with a new bible (`films/thin_ice/docs/BIBLE.md`), world, cast and score, and the first
film to leave the city. It is a wordless winter thriller in Saul Bass cut paper, made with two
agents in total.

### 11.1 The story

On a winter night a mother carries her small daughter across a frozen border river. A guard
follows them by reading their tracks in the snow. Snow falls on the border: a fence, a watchtower
whose searchlight sweeps the snow, a guardhouse, woods, a frozen river and, on the far bank, one
lit farmhouse window. Two small figures crouch at the fence. **The snow stops.** The moon comes
out, and from now on every step will show. The searchlight passes over them, the girl's music box
springs open on three notes of a lullaby, and her mother slaps it shut. Crawling under the wire,
the mother tears a scrap of her coat on a barb. Two lines of footprints, big and small, run into
the woods.

In the guardhouse the guard opens his pocket watch on a photograph of his own daughter in a
pompom hat, then goes out on his round. His lantern finds the scrap and the prints, and he blows
his whistle: far lanterns wake. In the woods the girl falls and her mother carries her, so the
small prints end. At the river the mother throws a stone onto the band of black ice down its
middle and it punches straight through: **the dark ice is thin.** Upstream, where the ice is white
all the way across, the searchlight sweeps. Behind her the lantern is coming.

So she writes a lie on the page. She walks out to the edge of the black band, then walks back
**in her own footprints**, boot into print, to the fallen trunk beside the trail. She steps up
onto it, where no print shows, and hides in the reeds. The guard follows the one line of prints to
the black ice, sees the farmhouse light beyond it and steps on. **The ice breaks.** Under the
water his lantern sinks away glowing; he fights up to the hole and clings to an edge that keeps
breaking.

The way upstream is open, but the girl won't go. She unwinds her red scarf and holds it up. The
mother crawls out along the trunk and throws it: short, then across his arm. Her boot hooks a
branch stub, and she pulls him out along the red line. On the bank he takes out the watch: it is
wet and stopped, and in its lid is his daughter. He looks from the photograph to the girl. Whistles
sound in the trees. He points upstream (go) and winds the scarf back round the girl's neck. When
the other guards come he points at the hole the trail leads into and shakes his head. One takes
off his hat. **It begins to snow.** The mother carries the girl across the white ice. A farmhouse
door opens on warm light. In the window the lullaby plays all the way through. The snow fills
every footprint until the page is blank, and only the red thread is left.

**The title is the theme.** THIN ICE is the river, the trick and the moral ground every one of them
stands on. The title cracks, and a red thread holds the two halves: the thread is the scarf, the
one line in the film that joins instead of divides.

### 11.2 Plants and payoffs

| Plant | Payoff |
|---|---|
| s01–s02: the snow stops and the moon comes out: every step will show. | s02–s07: the tracks are the hunt. s11: it snows again; s12: the snow covers every track. |
| s02: the scrap of her coat on the barb. | s03: his lantern finds it, then the prints. |
| s02–s04: two lines of prints, big and small; s04: the small line ends where she lifts the girl. | s06: only one line, hers, so the backtrack can work. |
| s05: the stone punches through the black band. | s07–s08: he steps onto it and breaks through. |
| s05: the fallen trunk, which takes no prints. | s06: her way off the trail; s10: her way out to the hole. |
| s05: upstream the ice is white all across, but the searchlight sweeps it. | s11–s12: the light goes to the guards at the hole, and she crosses there unseen. |
| s03: his daughter's photograph in the watch's lid. | s11: the wet photograph, the girl in her pompom hat, his mercy. |
| s01: the red thread across the cracked title; s02: the girl's red scarf. | s09–s10: it becomes the rope; s11: he gives it back; s12: the thread is the last thing on the page. |
| s02: the music box opens on three notes and is slapped shut. | s12: safe, the girl opens it and the lullaby plays to the end. |
| s03: his lantern, the only warm light on the hunt. | s08: it sinks in the black water; s12: the farmhouse door's light takes them in. |
| s03: the whistle wakes the far lanterns. | s11: the lanterns arrive, and he lies to them. |

### 11.3 The look

- **Eleven colours, one job each** (`kit.py`): `INK` figures and trees, `NIGHT` the sky, `STEEL`
  distance, `SNOW` the moonlit page, `SHADOW` footprints and cast shadows, `ICE` the river's white
  ice, `THIN` the black band, `WATER` open water, `PAPER` the moon, the searchlight and breath,
  `AMBER` the lantern and lit windows, `RED` the scarf (and the title's thread) and nothing else.
  The colour script runs cold until the lantern sinks in s08, then the scarf, then the farmhouse
  door's warm light, then the white page and the red thread.
- **The snow is a page, and light reads it.** Every scene moves between two kinds of shot:
  - **the story:** flat profile elevations and sections at eye level, with the fugitives always
    travelling screen right (north);
  - **the page:** straight down on the snow with north up the frame, so the journey climbs the
    9:16 frame from the fence at the bottom to the farmhouse at the top.
  Footprints are the film's handwriting; the moon, the searchlight and the lantern are what read
  it. Prints show crisper inside a light.
- **Camera rules.** Hard cuts on the beat, often matched on a point. Eased moves. One Dutch tilt
  (the break, s08), shake only on impact (the crack and the break), one rising crane (the page
  going blank, s12).
- **Breath is acting.** A `PAPER` puff on every out-breath: panting is quick puffs, a held breath
  none (her breath stops when the moon comes out, and in the reeds).
- **The annotation layer, sparingly, one meaning each:** step pulses (a reused print flashes with
  a ring), dotted sight lines, the heartbeat ring (`PAPER`, never red), crack lines, whistle rays.
- **Paper.** OPPOSITE's settings, grain on twos; crisp cut edges, no blur, no gradients.

### 11.4 Form and foundation

- **Form.** 12 scenes, hard cuts on the beat (120 bpm), every scene starting on a bar line: s01
  title 0:00, s02 fence 0:14, s03 guard 0:32, s04 tracks 0:48, s05 river 1:04, s06 false trail
  1:18, s07 hunter 1:34, s08 ice 1:48, s09 choice 2:02, s10 scarf 2:16, s11 mercy 2:34, s12 other
  side 2:52. 3:08, 4,512 frames, 94 bars.
- **`world.py` (1,453 lines): one world in metres, seen two ways.**
  - The page: `W.Plan(x, n, ppm)` looks straight down with north up. `W.draw_page` lays the snow,
    the river's white ice and its banks, the black band, the holes, the reeds, the trunk, the woods
    with their long moon shadows, the fence, the tower, the guardhouse, the farmhouse and the
    prints.
  - The story views: `W.Dio(u0, z0, ppm, eye, D)` is a diorama cut open along a plane, with
    everything behind it in one-point perspective. `W.draw_river` looks west through the false
    trail, the ice slab in section, thick and white either side of the thin dark band.
    `W.draw_woods` looks west along the path. `W.FenceCam` looks north through the wire.
- **The record of footprints.** `world.py` keeps every route and the prints it leaves (position,
  heading, size, depth). A scene draws `W.prints_before(sid)` plus the prints its own action lays
  on the same positions. So the page is continuous from scene to scene, and the backtrack lands in
  prints that already exist.
- **`kit.py`:** the palette, the paper and OPPOSITE's annotation layer, plus the film's devices,
  all pure functions of time:
  - snow, in elevation and from above, with a density clock so it can stop and start;
  - the moon and its clouds, breath;
  - the searchlight's beam and lit patch, the lantern and its glow;
  - footprints, branching cracks, whistle rays, step pulses.
- **`cast.py`, `faces.py`.**
  - `cast.py` draws the mother, the girl and the guards as paperdoll figures whose coats swing with
    the stride. They stand in the dioramas in metres (`C.draw_at`) and are seen from above with
    their moon shadows (`C.top`). It also has the piggyback carry, the lantern, the stone and the
    watch.
  - `faces.py` has cameo profiles of all three (returning landmarks for breath and sight lines),
    the strip of eyes, the girl face-on (the photograph and the match cut), mittens, gloves, boots,
    the watch, the music box and its paper dancer, and the scrap.
- **Shared scene code.**
  - `scenes/_lib_dir.py` (the director's): the title's crack and floes, the searchlight's clock,
    the fence view, figures from behind that turn, keyed cameras, the Dutch tilt, water (bubbles,
    spray, the waterline, moonlight shafts) and the bank view (`L.Bank`).
  - `scenes/_lib_s04_s07.py` (the animator's): the woods, the river's extras, walkers in metres,
    the paper turn, print flashes, the heart rings.
- **One searchlight clock for the whole film** (`_lib_dir.search_x`). Its lit patch creeps over
  the crossing at 0:19 (going east) and 0:25 (going west), s02's two near misses, and reverses
  with a clank at 0:22.

### 11.5 Scene by scene (film times from the scene modules' constants)

| Scene | What it shows |
|---|---|
| s01 TITLE (0:00–0:14) | Snow falls on `NIGHT`. THIN and ICE land letter by letter (0:00.75–0:02.25). A crack shoots across the title (0:04.0); the halves drift apart like floes over black water (0:04.25–0:05.0) and a red thread snaps taut between them (0:05.0). Paper floods out of the letters (0:05.5–0:06.3) and the crack becomes the river's black band (0:06.0–0:06.5). The map assembles on the beats: the farmhouse window (0:06.5), the woods (0:06.75–0:07.5), the fence and the tower (0:07.0), the guardhouse (0:07.5). The thread fades (0:07.5–0:08.0) as two tiny figures appear at the fence, one with a red fleck at her neck (0:08.0). The snow stops (0:09.7–0:10.0). The push in on the two of them (0:11.0–0:14.0). |
| s02 FENCE (0:14–0:32) | They crouch at a drift, backs to us. Close on her mitten held out: nothing falls; she looks up (0:16.7). The moon slides out (0:17.0–0:17.5), the snow brightens, the posts' shadows grow toward us, and her breath stops (0:17.3). The searchlight's patch comes; she pulls the girl flat (0:18.3–0:18.75) and it rides over them. She lifts the wire and the girl crawls under (0:20.1–0:21.7). The beam reverses with a clank (0:22.0); the music box springs open on three notes (0:22.25) and her mitten slaps it shut (0:23.0). The page: the beam slides back over them, the scarf burning in it (heartbeats 0:24.75, 0:25.25). Her coat snags (0:26.4) and rips (0:26.75): the scrap stays on the barb. They run for the trees; the page: two lines of prints, big and small, into the woods. |
| s03 GUARD (0:32–0:48) | The guardhouse in section: he warms his hands at the stove. The watch, close (0:34.4–0:36.75): it springs open (0:34.5) on 11:58 and a photograph of a girl in a pompom hat; his thumb moves over it; it shuts (0:36.5). He takes his lantern and the wind throws the door open (0:38.2). The fence view: he walks along the wire and stops at the scrap (0:40.7); his glove lifts it off the barb (0:41.45–0:41.95). The page: his lantern's pool slides over the prints; his glove on a small print (0:43.45). He whistles twice (0:44.0, 0:44.4); far lanterns wake (0:45.0, 0:45.25, 0:45.5) and the searchlight swings north (0:44.9–0:45.9). He follows the prints into the woods (0:46.0–0:48.0). |
| s04 TRACKS (0:48–1:04) | The woods in profile: the searchlight's patch crosses among the trunks (0:48.4–0:51.0). The girl stumbles (0:51.25) and falls waist deep (0:51.5); her mother hauls her out and swings her onto her back (0:52.05–0:53.0). The page: two lines of prints; at a trampled patch the small line ends and the big prints go on, deeper; she climbs out of the top of the frame (0:55.1). The guard reaches the patch (0:57.6), crouches, and his look runs along the deeper prints (0:58.35). He goes on; far lanterns wake among the trees (0:59.5, 1:00.0, 1:00.5). She breaks out of the trees and stops at the river bank's edge (1:03.25). |
| s05 RIVER (1:04–1:18) | The river section, wide: the near bank, the white ice, the black band, the far bank and the farmhouse window. She sets the girl down by the trunk's root plate (1:07.1–1:07.95) and looks out at the band (1:08.35–1:08.9). She digs out a stone (1:09.0) and throws it (1:09.4): it punches straight through the black ice (1:10.0); rings spread (1:10.3), the ice booms (1:11.45) and the girl flinches (1:11.5). The page pulls back (1:12.0–1:13.3): the band runs the river's length until, far upstream, the ice is white all across, and the searchlight's disc crosses there (1:13.5). The girl turns, then her mother (1:15.05–1:15.5): the lantern in the trees. Her eyes, close: the band, the trunk, her prints; a blink (1:17.45), the idea (1:17.55). |
| s06 FALSE TRAIL (1:18–1:34) | The page: carrying the girl, she walks out across the white ice and stops at the band's edge (1:21.55). At boot level: her boot lifts straight up out of its print (1:22.3) and lowers back into the one behind, a perfect fit (1:23.55). The page: she walks backward in her own prints, each one flashing with a ring, and steps sideways up onto the trunk (1:27.5–1:27.97). Profile: along the trunk and down into the reeds; she crouches (1:30.05–1:30.4), the girl slides off her back, and from 1:30.45 there is no breath. The page rises (1:31.0–1:33.0): one line of prints out to the black band, the bare trunk beside it, two pairs of eyes in the reeds, and at the bottom the lantern's pool coming (1:32.35). |
| s07 HUNTER (1:34–1:48) | He breaks out of the trees and lowers the lantern to the snow: the trail (1:35.0–1:35.8). The page: his pool moves along the prints, past the trunk, past the reeds. In the reeds, close: the lantern's light slides over their eyes (1:39.3–1:40.7) to the heartbeat. The page: he stops where the prints stop (1:42.65). Profile: he raises the lantern and his look crosses the band to the far window (1:43.6). He looks down at the black ice, up again, and steps onto it (1:45.0–1:45.4); in the reeds she half rises, a mitten out, a stifled gasp (1:45.72). His boot, close: a fine crack runs out from his heel (1:46.85–1:47.6). |
| s08 ICE (1:48–2:02) | His second step: the crack bursts out round his boots (1:48.25), the shake, then a beat of silence (1:48.5–1:49.0). The section: the slab gives (1:49.08) and he drops through, with the film's one Dutch tilt. Under the ice (1:50.0): the lantern slips from his hand (1:50.55) and sinks glowing to the riverbed (1:52.75); the rifle slides off his back (1:51.7). He looks up at the hole (1:53.0) and kicks for it (1:53.5). He bursts up (1:55.0) and grabs the far edge, which breaks off (1:55.45, 1:55.62); up again (1:56.2), he grabs the near edge, and it holds (1:56.45). His face at the edge, close; a piece breaks under his glove (1:58.2). The page, close on him from above (1:59.0), pulling back to the trail running into the hole and, in the reeds, her eyes opening (2:00.4). |
| s09 CHOICE (2:02–2:16) | In the reeds, close: her profile, the girl in front of her in the red scarf. The split (2:04.0): her eyes go up to the far window, the way out (2:04.45); down to his gloves at the hole (2:05.75), where one slips (2:06.35); up again (2:07.15); they narrow (2:07.65). The heartbeat rings spread over all three bands. The bank view (2:08.0): she rises, takes the girl's hand (2:08.5), turns upstream (2:08.86), two steps, and their arms go taut (2:09.88): the girl is looking at the hole (2:10.05). From above: his glove slides under (2:10.86–2:11.42). The girl, close: she unwinds her scarf (2:11.88–2:12.86) and holds it up (2:12.9–2:13.45). The mother, close: she sees it (2:14.32), looks at the hole (2:14.86) and takes it (2:15.12–2:15.45). The heartbeat stops. |
| s10 SCARF (2:16–2:34) | At the root plate, the scarf round the mother's neck: her flat mitten, stay (2:16.42). The section: onto the trunk (2:17.86) and flat on it (2:18.2). The page, the trunk straight up the frame: she crawls toward him beside the false trail. At the tip: the scarf off her neck and round her wrist (2:21.0–2:21.52); the first throw falls short (2:22.39), his glove lunges and the edge breaks under the other (2:22.74). She draws it back and edges out; the second throw lands across his arm (2:24.48). From above: his glove closes on the red (2:24.86). He winds it round his fist and heaves (2:25.72), dragging her toward the hole, until her boot slams into the branch stub (2:26.38). The page: hand over hand; his chest comes up onto the edge (2:27.1), it breaks (2:27.75), and he slides out on his belly along the red line (2:28.1–2:29.5); she has him by the collar (2:29.62). Back along the trunk (2:30.05–2:31.4), off it; he rolls onto his back (2:31.9) and she scrambles back to the girl. |
| s11 MERCY (2:34–2:52) | The bank: he lies hugging himself; she stands between them with the scarf. His glove goes into his coat (2:35.6) and she sweeps the girl behind her; something catches the moon (2:36.6). The watch, close (2:37.0): the lid springs open (2:37.42), water runs out (2:37.6–2:38.8), the hands have stopped; the push in on the wet photograph (2:38.55–2:39.6). The match cut (2:39.6): the photograph's oval becomes the moon behind the real girl, face-on; she blinks (2:40.15). His face (2:40.6); he shuts the watch (2:41.18). The river view (2:41.7): three whistles (2:41.8, 2:42.2, 2:42.62) and lanterns out of the woods; the mother spins round. He gets up on one knee and points upstream: go (2:43.85). The girl takes the scarf from her mother's fist (2:43.95) and holds it out to him; he takes it (2:44.65) and winds it round her neck (2:44.9–2:45.55). She climbs onto her mother's back and they go upstream behind the root plate (2:46.55–2:47.4), the red last to go; he stands alone. The page (2:47.4): the lanterns run down to the head of the false trail, the searchlight finds the hole, and he points at it (2:48.3). The bank view (2:49.4): four of them from behind; he shakes his head (2:49.65); the lanterns lower and the first snow falls (2:50.3); one takes off his hat (2:50.6). |
| s12 OTHER SIDE (2:52–3:08) | The crossing in falling snow, on a long lens: the guards in the searchlight's beam at the head of the false trail, and far out on the white ice beyond them the mother carrying the girl across, her prints filling behind her. The farmhouse (2:56.0): the latch lifts (2:56.25), the door swings in on warm light (2:56.3–2:56.65), a woman in a shawl waves them in, and the door closes (2:58.6–2:58.95). The window (2:59.0): the girl lifts the music box's lid (2:59.1) and the whole lullaby plays; the strings come in under it in A major (3:01.5). The page, rising (3:01.75–3:03.9): the snow fills the trail, the holes, his drag mark and her real prints until the page goes white (3:03.4–3:04.35). The title re-forms (3:04.5–3:04.85): THIN ICE, cracked, held by the red thread. Snow settles over everything but the thread (3:05.7–3:06.5); a slow push in on it. Black and silence (3:07.75). |

### 11.6 Sound

`films/thin_ice/audio/mix.py` (4,359 lines, made by the audio agent) is the score, the foley and the
master in one file, locked to the scene modules. Every beat a section uses is read on every run from
its scene's constants or cues, and every cue no section answers is realised from its words.

- **The score.** Strings and a music box at 120 bpm in A minor, ending in A major.
  - **The lullaby** (E5 C5 | D5 B4 | C5 A4 | B4 E4 | A4 C5 | B4 G#4 | A4) is the theme. The music
    box plays 18 notes of it in all:
    - its first three notes in s02 (0:22.25–0:22.75), before her mitten slaps the box shut;
    - its first note alone in s09 as she takes the scarf (2:15.5), and far off on s11's match cut
      (2:39.6);
    - the whole tune once, in A major, in s12 (from 2:59.25, read from the scene's `NOTES`), with
      the strings coming in under it (3:01.5) and the last chord held under the title.
  - **The hunt** (s03–s07): low strings in A minor, an F aching in them as it closes in; a soft
    pulse on the film's grid that quickens with the chase (a bar, a beat, an eighth); high
    harmonics for the ice; the lullaby's head low in the cellos under the false trail.
  - **s08:** the crack, half a second of digital silence, the break. Under the ice: a murky drone
    and his huge slow heart. It surfaces with him.
  - **s09:** her heart alone at 96 bpm with one trembling E6, both cut dead as she takes the scarf.
  - **s10:** an A pedal swelling under the throws, cut dead on the hook (one low string stab),
    rising again under the slide and releasing on an open A when he is out.
  - **s11:** quiet. The watch clicks open and shut but never ticks. A minor with an aching F under
    the lie, and a glass shimmer for the first snow.
  - **The red thread** is a string harmonic (E6), in s01 and again under s12's last chord.
- **The ice,** the film's signature, is all synthesised:
  - groans and booms;
  - dispersive "pew" chirps (high to low in 0.1–0.4 s, the sound of lake ice);
  - cracks, the break and the plunge;
  - the stone's crack and plop.
- **Foley.**
  - The wind is always there: high in the pines, through the hut's walls, falling away when the
    snow stops, quiet in the farmhouse's lee.
  - Three snow crunches: the mother's felt boots soft and quick, the girl's smaller and quicker,
    the guard's heavy and slow with hobnails.
  - The searchlight's motor and clank; wire, cloth and wool; the stove, the watch, the door, the
    lantern, the whistles; water and bubbles.
- **Sources.** Nothing new was generated: there is no paid audio in this film.
  - The only recordings are OPPOSITE's breaths, gasps and body fall and DOUBLE CROSS's grunt. The
    girl's breath is OPPOSITE's pitched up 3 semitones; the guard's panting and gasps are pitched
    down 5.
  - Everything else is synthesised in numpy/scipy, with OPPOSITE full's strings.
- **Cues.** All 441 scene cues are realised by the sections. Four are approximations:
  - three far calls in s04 are a whistle and a lantern's clink, since there are no voices;
  - s07's far dog is a synthesised bark.
  Of 189 measured hits the worst is 20.3 ms off, none by a frame.
- **The master.** 48 kHz stereo 24-bit, 188.000 s:
  - -16.0 LUFS integrated, a true peak of -1.4 dBTP (the limiter's ceiling, as in the OPPOSITE cut);
  - exact digital zeros through s08's half second after the crack (1:48.5–1:49.0) and from 3:07.75
    to the end;
  - a lowest short-term reading of -23.8 LUFS (the quiet after the run, about 0:29), well above the
    -29 floor;
  - per scene: s01 -16.4, s02 -18.3, s03 -16.4, s04 -16.6, s05 -17.5, s06 -18.3, s07 -16.8, s08
    -13.3, s09 -14.6, s10 -14.2, s11 -16.9, s12 -15.7 LUFS: hushed through the hunt, loudest at
    the break and the rescue.
  Two runs give the same file, byte for byte.
- **From the sound review.** s02's two heartbeats were 0.5 s apart, on the score's grid, so they
  read as part of the music. The second moved to 0:25.375: her heart at 96 bpm, as in s09.
- **On a phone speaker** the low strings and the under-ice roar mostly vanish. Everything that
  carries the story (breath, crunches, cracks, the music box) sits above about 300 Hz.

### 11.7 Production and what it introduced

- **Team.** The director wrote the bible and the foundation, made s01–s03 and s08–s12, reviewed
  every frame, rendered, encoded and committed. One animator made s04–s07 and one audio agent made
  the mix: two agents in total, the user's limit.
- **A world in metres.** Every scene views one map, through the plan camera or a diorama, so
  continuity is geometry, not drawing: the trunk, the hole and the reeds are where they were in
  every shot.
- **The page as a record.** Each scene writes footprints and the next one reads them. The story
  turns on it: the false trail is a lie written on the page, and the snow wipes it clean.
- **Weather as a clock.** The snow stops in s01 (from then on every step shows) and starts again
  in s11, the mercy, on one density function.
- **Rhymes.** The watch's oval becomes the moon behind the real girl (s11). The end title
  rebuilds s01's floes, crack and thread (s12). The music box's three notes in s02 are the first
  three of the lullaby played whole in s12.
- **Found in review and fixed before the render:**
  - in s11, the guard's breath came out of his cheek after a rotation was restored (the marks are
    now converted through device space);
  - his coat ended mid-frame in the close-up;
  - the first snow appeared only at the top of the frame (the density clock; it now fades in over
    the whole frame);
  - the walk-away was too fast and half hidden (it now goes behind the root plate, the red last
    to go);
  - the lantern light tinted the figures brown (the glow is now drawn behind them);
  - the end title had no room to breathe, so s12 got one more bar (16 s; black at 3:07.75).
- **Known small issues, left as they are.** Both are a few pixels on a phone; fixing them would
  mean re-timing the guard in s07 and re-rendering the page shots of s07–s12.
  - On the bank, the guard's prints skip about 1.4 m where his walk out of the woods ends and his
    walk out onto the ice begins (`world.py`: `GUARD_WOODS` ends at (13.04, -3.41), `GUARD_ICE`
    starts at (14.03, -2.38)).
  - His last left print before the black band is missing: two right prints in a row, at n 9.25
    and 10.35, the second on the band and under the hole.

**Delivery.** `final/thin_ice_preview.mp4`:
- 1080×1920, 24 fps, 4,512 frames, 188.000 s;
- H.264 High at about 7.50 Mb/s (SYSTEM.md's two-pass encode), AAC-LC 48 kHz stereo at about
  257 kb/s, 7.76 Mb/s overall;
- 182.4 MB;
- after the AAC encode, -16.1 LUFS with a true peak of -1.2 dBFS, in sync with the master to the
  sample. s08's half second is still exact zeros; the end has a 50 ms tail at -54 dBFS, then zeros.

**The soundtrack's encode.** At SYSTEM.md's 192 kb/s, the AAC encoder's perceptual noise
substitution (PNS) turned the ice breaking after s08's silence into a 20 ms burst of error (-19.9
dBFS, against about -42 for the whole film) with a true peak of +2.3 dBFS. With PNS off
(`-aac_pns 0`) at 256 kb/s the worst burst is -32.5 dBFS and nothing passes -1 dBTP. The first
encode's picture was kept and the new soundtrack muxed in with `-c copy`.

Workflow notes:
- The audio agent's first run was stopped by an API usage limit before it wrote anything. It was
  resumed with a message after the reset, so the film still used two agents in total. The picture
  master, the glitch scan and the first encode pass ran while it worked.
- The master's glitch scan (k = 4) flagged 70 frames away from the scene cuts. Every one is a cut
  between shots inside a scene, at its scene module's constant; there are no single-frame pops.
  At k = 2.5 it adds six fast moves, all designed:
  - the woods' crowns snapping into one canopy (0:07.5–0:07.58);
  - the mitten slapping the music box shut (0:23.0);
  - the watch springing open and shut (0:34.54, 0:36.5).
  The preview's scan (k = 4) flags the same cuts and the watch opening.

### 11.8 Files

| Path | What it is |
|---|---|
| `films/thin_ice/docs/BIBLE.md` | The bible: logline, story, plants and payoffs, cast, look, world, timeline, beats, sound plan. |
| `films/thin_ice/kit.py` | The palette, the paper, the annotation layer and the film's devices (snow, moon, breath, searchlight, lantern, prints, cracks). |
| `films/thin_ice/world.py` | The map in metres, the plan camera, the dioramas (river, woods, fence) and the record of footprints. |
| `films/thin_ice/cast.py`, `faces.py` | The figures in profile and from above, the props; the close-ups. |
| `films/thin_ice/scenes/_lib_dir.py`, `_lib_s04_s07.py` | The director's and the animator's shared scene code. |
| `films/thin_ice/scenes/s01_title.py` … `s12_other_side.py` | The twelve scenes. |
| `films/thin_ice/timeline/build_timeline.py`, `timeline.json` | The edit: twelve scenes, hard cuts. |
| `films/thin_ice/audio/mix.py` | The score, the foley and the master, locked to the scene modules (`--qa`, `--only`, `--stems`, `--without`, `--skip-missing`). |
| `films/thin_ice/final/thin_ice_preview.mp4` | The delivered preview (not in git). |
