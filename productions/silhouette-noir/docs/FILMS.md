# The films

Every story made so far, in the order we made it: what it is, how it is built, the devices it uses,
what it added to the system, and where its files are. DOUBLE CROSS, the latest, is covered in depth
at the end.

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
| 9 | DOUBLE CROSS | 10-23 | 2:32 (v1–v3 2:24) | Wordless Bass heist, 11 scenes | v1, v2 (the shot types, `9ea5f1b`), v3 (the review fixes and the voices) and v4 (v2's picture again, slower, the guard rebuilt) delivered |

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

## 9. DOUBLE CROSS (2:32), in depth

The user liked "the way you are connecting things and camera motion and sound effects" and asked
for a new crime thriller, more innovative, with no more than two agents at a time.

**Film times.** Sections 9.2–9.11 give v1–v3's times (2:24). v4 (9.12) runs 2:32: s02's side
shot (0:21–0:28) and s05 (0:56–1:14) are re-timed, and every other time from 0:24 is later, by 4 s
up to s05 and by 8 s from s06 (v1's 1:06).

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
s01–s03, s09 and s10 in 9.11 (withdrawn in v4). v4's s02 and s05 are in 9.12.

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

### 9.13 Files

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
