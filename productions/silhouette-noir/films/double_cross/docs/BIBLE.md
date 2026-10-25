# DOUBLE CROSS

A 2:54 vertical (1080×1920, 24 fps; 2:32 in v4, 2:24 in v1–v3) heist thriller in the trilogy's cut-paper Saul Bass
language.
Wordless, scored. The film is told through its own blueprint: the plan is drawn in chalk, the plan
rises off the paper into the night, and the story is what happens when someone leaves the line.

## The story in one breath

A bank at night. Chalk marks its front, and the street folds flat into a blueprint: the bank
is the plan, and the X on its vault marks the gold. Under a hanging lamp three hands set three
chess pieces on it: a white QUEEN (the Architect), a gold BISHOP (the old safecracker), and a
red KNIGHT (the muscle). Her gloved finger taps the X, twice: here. His eyes go to the X, and
she sees him look. While she chalks the route she draws a little bell on the side door and taps
it.

Night. The blueprint folds up into the city. Down a manhole, along the sewer and up through a
hatch, the crew follows the chalk dots. They slip past a guard's sweeping flashlight. The
Cracker opens the vault: three gates line up and the door swings open on gold. While the men
bag the bars she opens one small deposit box, lifts out a ruby and pockets it. No one sees.

Then the Knight double-crosses them. He shuts the vault on the other two and spins the dial. His
red line leaves the chalk route in an L, the knight's move, to the side door, and he bursts out
through it with the gold: the bell she drew there rings and rings.

In the dark a match flares. The Cracker pounds the door, but the Architect is calm. She taps the
floor and it sounds hollow. She unrolls a second sheet: tracing paper. The film rewinds to what
we missed. While she was chalking the plan, she dotted the sewer line exactly where it passes
under the vault, and in that dot's lens we see the night before: her on a ladder under the
vault floor, cutting a trapdoor up through it with a torch and setting it back so it looks like
a tile. The overlay slides over the plan and shows PLAN B:
- a trapdoor in the vault floor;
- her own route out by the sewer, the opposite way;
- the alarm on his way out, and the police it brings, closing on his car;
- her real prize, not the gold but one ruby.

The alarm's rings roll out over the city and wake four police cars, which close on the Knight
from all four streets; a red ring snaps round him: checkmate. Boxed in on the street, he lets
the gold drop and puts his hands up in their lights. Two blocks away a manhole lifts, and she
walks off into the night with the Cracker; their two routes cross into an X. The X splits open
on her gloved palm under a street lamp: the ruby. Back at the table her white queen takes the
red knight, and the title's X crosses again, the ruby as the red dot.

**DOUBLE CROSS:** he crosses the crew; she had crossed him before he moved. X marks the spot
twice.

### Plants and payoffs (play fair)

| Plant | Payoff |
|---|---|
| s01: the dashed sewer branch is drawn running right under the vault. | s08 the hollow floor; s09 the trapdoor. |
| s02: his red look goes to the X, and her white look catches him. | s07 the betrayal; s09 the rewind's callout on her eye. |
| s03: as the Knight slams his piece down by the street, her chalk, lifting away from the vault, leaves a small dot on the sewer line under it. | s09: the rewind stops on that frame: the dot and his slam at once. |
| s03: his slam claps the plan's vault door shut on the queen and the bishop. | s07: he shuts the vault on the other two. |
| s02: her finger taps the X over the vault, twice, and the gold under it glints. | s07: the gold he takes and runs with; s10: he drops it in the street. |
| s03: a small bell is drawn on the side door, and she taps it (one damped tink: the alarm's own note). | s07: he bursts out through that door and the bell rings; s10: its rings wake the police. |
| s07: she opens one small deposit box, lifts the ruby out into the light (the close-up) and pockets it. | s11: the ruby on her palm. |
| s08: her heel finds the floor hollow. | s09: the night before, in the dot's lens: she cut that trapdoor from below. |
| s02: his slam makes the other pieces jump. | s11: her queen knocks his knight over, quietly. |
| s01: the white strip lands first and the red crosses over it. | s11: the X comes back with the white over the red. |

## Cast

All figures are cut-paper silhouettes in profile (`films/double_cross/cast.py`, `C`), INK with a
coloured rim (an edge line) that is also their colour on the plan.

| Who | Silhouette | Piece | Colour | Motion (CMU clips in `assets/mocap`) |
|---|---|---|---|---|
| **The Architect** (she) | belted trench coat to the knee; hair in a low chignon with a **pencil through it**; gloves | white QUEEN | `PAPER` (chalk) | 17_03 stealth walk, 18_08 explaining, 13_33 ladder, 69_70 squat to the floor |
| **The Knight** (him) | broad; flat cap; heavy coat; a cigarette ember | red KNIGHT | `RED` | 17_08 heavyset walk, 70_03 carrying a heavy case, 81_05 pushing a heavy object, 80_28 smoking, 16_08 run and sudden stop |
| **The Cracker** (old) | thin and stooped; bowler hat; round spectacles; a stethoscope round his neck | gold BISHOP | `GOLD` | 77_14 careful creeping, 22_03 kneeling, 120_15 startle, 79_73 scared |
| **The Guard** | peaked cap; a flashlight | black PAWN | `INK` | 77_05 looking round with a flashlight, 69_16 turning in place |
| **The cat** | a small black cat; two gold eyes | none | none | procedural |

The police are cars, seen from above (s10), never people.

## The look

### Palette (`films/double_cross/kit.py`)

| Name | Use |
|---|---|
| `BLUE` | The blueprint paper: every plan shot. |
| `GRID` | The blueprint's grid and faint construction lines (`PAPER` at low alpha). |
| `PAPER` | Chalk: walls, routes, numerals, the title, her rim and route. |
| `NAVY` | The night: every exterior field, the sewer, the dark bank. |
| `STEEL` | Moonlit planes and distance at night. |
| `DEEP` | A dark interior (the vault in the dark). |
| `GOLD` | Gold and lamplight: the vault's glow, the table lamp, the match, the Cracker's rim. |
| `RED` | The Knight and what he does: his look, his route, the alarm, the arrest ring, the ruby. Small and burning. |
| `POLICE` | The police light's blue half. s10 only. |
| `INK` | Every silhouette. |

- Nothing else: no gradients, no other hues.
- Translucency is allowed only for light and for the tracing paper, as flat tints: the flashlight
  cone, the lamp pool, the match, the tracing sheet. No blur.

### Paper

- Every scene starts `render` with `K.scene_setup(f, field)`. The field is `K.BLUE` for plan
  shots and `K.NAVY` for night shots.
- Shapes are cut paper (`bass.cut_rect`, `bass.scissor`, `bass.ring_pts`, `K.dot`). Big circles
  need fine facets (`n=48..96`).

### Camera grammar: the TILT

The film has one camera idea. The plan is the world seen from straight above, and the world is
the plan seen from the side. `P.PlanCam(cx, cy, zoom, phi, yaw)` is an orthographic camera over
the plan:

- `phi = 90°` looks straight down: a pure blueprint, with pieces as discs.
- `phi ≈ 55°` is the table view: the plan foreshortened, the pieces standing up like a
  pop-up book.
- `phi → 0` is eye level. The walls extruded from the plan rise into the building
  (`P.draw_walls_3d`).

The film tilts down into the world (s04), up into the plan (s05's stealth map, s07's L), and
back again. From v4 the briefing ends on the same move, from the table's side down onto the plan
(s02 into s03). Cuts between plan and world match on a point: a manhole, the vault door, the X.

Other angles, each used deliberately:
- Profile close-ups (the three faces in s02, her calm in s08).
- Extreme close-ups: the dial, the stethoscope, the match, the ruby.
- A cutaway of the lock: the wheel pack (s06).
- A section through the street into the sewer (s04, s09).
- Side elevation of the corridor (s05).
- The X-split screen (s07).
- The rewind (s09).
- Top-down on the city as a chessboard (s10).

Rules for camera moves:
- Moves are eased. Push-ins snap on the beat or glide; never linear.
- No Dutch tilt except in the Knight's panic (s10).

### Motion

- Cut paper moves crisply, and a figure's own motion is never blurred. Only the fastest camera
  moves are smeared over the frame: the whips (s08's `whip_shot`, s09's whips, box-averaged in the scene)
  and, from v4, s05's pans and whip (its `motion_blur` averages 6 sub-frames on the pans and 10
  on the whip). Every other scene's `motion_blur` returns 1.
- Figures move on twos (`K.twos(t)`); graphics, routes and the camera move on ones.
- Snaps land on the beat (120 bpm, beat = 0.5 s). Anticipation and settle use `outback`.

## The annotation layer (the plan is the film's handwriting)

| Device | `kit` call | Meaning, colour |
|---|---|---|
| **Chalk line** | `K.chalk_line(c, pts, u)` | Ruled walls and plan lines, drawn on with a scratch. `PAPER`. |
| **Route** | `K.route(c, pts, u, color, tail=0)` | A planned path: chalk dots led by an arrowhead. Plan A is `PAPER`; his deviation is `RED`; Plan B is `PAPER`, drawn as a solid line on the tracing paper. |
| **Footstep dots** | `K.step_dots(...)` | A walk on a diagram, one dot per step, on the footstep sound. |
| **Circled numeral** | `K.circled(c, "3", p, r, u)` | The plan's steps ① to ⑤. The only text besides the title. |
| **X** | `K.xmark(c, p, size, u, color)` | The target. Chalk on the vault; red on the ruby in Plan B. |
| **Sight line** | `K.sight_line(...)` | A look. Hers `PAPER`, his `RED`, the guard's `PAPER`. |
| **Cone** | `K.cone(c, apex, ang, spread, length)` | The guard's flashlight: a flat translucent `PAPER` sector, in plan and in elevation. |
| **Stopwatch** | `K.stopwatch(c, p, r, t, ...)` | The heist clock, top right, from the descent (s04) to the betrayal (s07). One tick per beat. It stops dead when he crosses them and spins back in the rewind. |
| **Ripple** | `K.ripple(...)` | A sound: the clank, the alarm (`RED`), the knock in the floor. |
| **Marker ring** | `K.marker_ring(...)` | "This matters": `RED`. **Once only:** the ring that closes on the Knight's car (s10). |
| **Callout** | `K.callout(...)` | A lens on a leader line. The rewind's reveals (s09). |
| **Tracing paper** | `K.tracing(c, rect, u)` | Plan B: a translucent sheet that slides over the plan. |
| **X-split** | `K.x_split(c, panels, u)` | The frame cut on both diagonals into four triangles (s07). |
| **Rewind** | `K.rewind_marks(c, t)` | Chalk streaks and a double chevron over replayed frames (s09). |

## The world

### The plan (`films/double_cross/plan.py`, `P`)

Plan px with north up, on a sheet that fills the frame at `PlanCam(540, 960, 1.0, 90)`.

| Place | Plan coordinates |
|---|---|
| The sheet | x 70–1010, y 150–1770 |
| BACK STREET | y 230–330, full width; MANHOLE B at (450, 280) |
| BANK footprint | x 170–910, y 380–1300 |
| VAULT | x 360–720, y 430–700 (thick walls). Round door on its south wall, centre (540, 700). The X is at the vault centre (540, 565). |
| Gold | stacked in the vault's west half |
| Deposit wall | the vault's east inner wall, 2 columns × 6 rows (`P.BOXES`, `P.box_rect(col, row)`); the ruby box is column 2, row 2, centre (680, 518) (`P.RUBY`) |
| TRAPDOOR (Plan B only) | (450, 600), on the sewer branch |
| CORRIDOR | x 500–580, from the vault door south to y 1180 |
| INTERSECTION | cross corridor y 860–940, x 200–880; GUARD POST at (240, 900) |
| STORE ROOM | x 200–500, y 980–1300, with the HATCH at (450, 1150) and a door into the corridor at (500, 1150) |
| LOBBY | x 580–910, y 980–1300; front doors on the south wall |
| SIDE DOOR | (910, 1100), with an alarm bell; the ALLEY runs south from it, x 910–1010 |
| FRONT STREET | y 1350–1450; MANHOLE A at (250, 1400); the CAR at (930, 1400), at the alley's mouth |
| SEWER (dashed: underground) | main line along y = 1400. Branch north up x = 450: under the store room (hatch), **under the vault**, to manhole B. |

Shared shots in `plan.py`:

- `P.table(c, cam, lamp_a, sheet, plan_a)`: the table shot (the sheet's shadow, the sheet, the
  lamp's pool; Plan A at strength `plan_a`). The field under it is `K.DEEP`.
- `P.draw_plan_a(c, a, cone_ang=0, prog=None, door=0)`: Plan A as she leaves it in s03 (both
  routes, ①–⑤, the X, the guard's cone (kept inside the corridor's walls) and its timing
  ring, the dial at the vault door, the chalk car, the bell, the dot). `prog` draws its parts
  (`P.PLAN_A_PARTS`) on, as s03 does. `P.draw_pieces(c, cam, P.PIECES_A)`: the pieces where
  s03 leaves them. `P.table(..., on_plan=fn)` draws more chalk under the lamp's pool.
- `P.piece_on(c, cam, kind, p, h, color, edge, lift=...)`: one piece standing on the plan,
  with its shadow cast away from the lamp.
- Cameras: `P.TOP` (straight down), `P.TABLE` (s02), `P.PLAN_CAM` (s03), `P.HANDOFF_34` (s03's
  last frame and s04's first). `PlanCam.lerp(a, b, u)` blends two cameras.

Routes (`P.ROUTE_IN`, `P.ROUTE_OUT`, `P.ROUTE_KNIGHT`, `P.ROUTE_B`):

- **IN (Plan A):** manhole A → the sewer east → the branch north → the hatch → the corridor
  → across the intersection → the vault door → X.
- **OUT (Plan A):** back the same way to manhole A, then east along the front street to the
  car.
- **KNIGHT:** the vault door → south down the corridor → east to the side door → the alley →
  the car. An L.
- **B:** X → the trapdoor → north along the branch → manhole B → west along the back street
  and off the sheet.

### The world at night (the animator's sets; keep them consistent with the plan)

- **Front street (elevation):** the bank's facade (a classical front: steps, columns, a
  pediment, a round clock), the street lamp, the alley mouth on the right, manhole A in the
  road, and the car.
- **Sewer (section):** the street cut open. The pipe is a long `NAVY` tunnel with a black
  water line and drips. Iron rungs lead up to the hatch.
- **Corridor (side elevation):** the intersection with the guard's post on the left, a
  doorway alcove to hide in, pipes on the wall (the clank), and crates (the cat).
- **The vault door (elevation):** a great round door with a spoked wheel, the dial and
  radial bolts. **The lock (cutaway):** three wheels with gates, a fence and the bolt.
- **The vault (interior):** the gold field, gold bars, the deposit wall and one small box.

## The timeline

All scenes run back to back with hard cuts on the beat. Film time = scene start + scene time.
These are v5's starts (2:54, 4,176 frames, 87 bars). v4 gave s02 and s05 two more bars each. v5
gives s01 two more (16 s), s02 one more (18 s), s07 two more (20 s), and s09 and s10 three more
each (22 s and 18 s). So against v4, s02 starts 4 s later, s03–s07 6 s later, s08–s09 10 s
later, s10 16 s later and s11 22 s later.
Each scene module defines its beats as module-level constants and exports `cues(T)`
(`engine.timing.Cue`) for the sound.

| id | slug | film start | length | who | what happens |
|---|---|---|---|---|---|
| s01 | title | 0.0 | 16.0 | me | the bank at night, its front marked in chalk; the street folds flat into the blueprint; the plan rules itself in; the title strips cross into an X; the X lands on the vault and a gold lens opens on the gold it marks |
| s02 | crew | 16.0 | 18.0 | me | three hands set three pieces; three profiles; the table from the side: her briefing, and close over the plan her gloved finger taps the X twice (the gold glints); the Cracker nods; his red look at the X, her white look at him; the tilt down onto the plan |
| s03 | plan | 34.0 | 16.0 | me | she chalks the route ①–⑤ and the pieces hop along it; the guard's cone and its timing; the car; the bell, and her tap on it; the dot under the vault |
| s04 | night | 50.0 | 12.0 | animator | the pop-up: the plan rises into the night street; the manhole; the descent; the sewer section; up through the hatch; the stopwatch starts |
| s05 | guard | 62.0 | 18.0 | animator, rebuilt in v4 | the corridor framed close: the guard's light; the crew hiding; the stealth map from above; the clank; the near miss, one beat at a time; the cat; the push to the dial |
| s06 | safe | 80.0 | 14.0 | animator | the vault door; the stethoscope; the lock's gates line up; the bolts; the door swings onto gold |
| s07 | cross | 94.0 | 20.0 | animator; v5's beats by me | the gold; her deposit box and the ruby, close (she lifts it out and pockets it); his look; the X-split; the door slams; the dial; his red L on the plan; the side door bursts open under the ringing bell |
| s08 | locked | 114.0 | 12.0 | me | black; a match; the Cracker pounds; her smile; the hollow knock; the tracing paper |
| s09 | plan_b | 126.0 | 22.0 | me | the rewind to the dot (lens); in the dot's lens, the night before: she cuts the trapdoor from below; her look; the overlay, a bar a mark: the trapdoor and her route, his L and the bell and the police, the ruby; down through the floor |
| s10 | checkmate | 148.0 | 18.0 | me | the Knight to the car; the city as a chessboard; the bell's rings wake four police cars, which close like rooks; the red ring; his face; boxed in on the street, he drops the gold and puts his hands up; pull back: her line walks away; the routes cross into an X |
| s11 | end | 166.0 | 8.0 | me | the X splits open on her palm: the ruby; the queen takes the knight; the X lifts off the plan into the title; the red dot; black |

## Scene by scene

Times are scene-local seconds. *Sound cues are in italics.*

### s01 TITLE (0–16)

v3's opening, given time in v5: v3 ran it in 12 s, which read as rushed, so each part now has a
bar of its own.

- **0.0–4.0:** The bank at night, at s04's eye level, in from black. Four chalk dots tick in at
  the corners of its front, one per beat (0.5, 1.0, 1.5, 2.0), and dotted lines join them
  (2.0–2.5): the bank, marked, held a bar while the camera pushes in. *Chalk tap ×4; the night
  air; a low string note under bar 1.*
- **4.0–6.0:** The street folds flat, back to front: s04's pop-up run backwards (the moon, the
  neighbours, the alley and the lamp at 4.0, then the clock, the pediment, and the portico and
  front, 4.25–4.75). The camera tilts up over it to straight down (4.25–6.0), the chalk outline
  lies down with the front onto the paper that was under the street all along (4.3–5.95), and
  the night lifts off it (4.5–5.9). *The pop-ups folding flat; a rising paper whoosh.*
- **6.0–9.75:** The outline is the bank's on the plan, and the plan rules itself in from it, one
  group per beat, each struck on like a ruler stroke. *A chalk scratch and a vibraphone note on
  each; the bass walks in.* Order:
  1. the bank (6.0);
  2. the vault (6.5);
  3. the corridor and intersection (7.0);
  4. the streets (7.5);
  5. the manholes (8.0);
  6. the dashed sewer (8.5), its branch visibly passing **under the vault**;
  7. the side door and alley (9.0).

  The plan dims under the title (9.75).
- **10.0–12.0:** A white strip slashes across the frame (10.0), and a red one crosses it
  (10.5): a big X over the vault. *Whoosh-thud, whoosh-thud.* The words DOUBLE (above) and
  CROSS (below) stamp in (11.0, 11.5). *Stamps.*
- **12.0–13.0:** The letters lift away and the X shrinks onto the vault, landing as the plan's
  chalk X (13.0; *thud*).
- **13.1–14.5:** A gold lens opens off the X on what it marks: the vault's gold, through its
  door, held with the plan still. The top bar glints on the beat, twice (13.5, 14.5). *A
  vibraphone roll as the lens opens; a ting on each glint.*
- **14.5–16.0:** The camera tilts down to the table, and the lamp comes on (14.75). s02 begins
  there and closes the lens.

### s02 CREW (16–34)

Film times (the module's beats plus 16 s).

- **16.0–17.5:** The table, close, under the lamp's pool. Her gloved hand (`PAPER` rim) sets the
  white queen on manhole A (17.0). *Clack.*
  - 17.5–19.5: Her profile close-up on gold: the chignon and pencil, her eye on the plan; a
    lens joins her to her queen (18.0).
- **19.5–20.5:** An old hand (`GOLD` rim) sets the gold bishop (20.0). *Clack.*
  - 20.5–22.5: The Cracker's profile: bowler, spectacles (a glint crosses the lens, 21.5),
    stethoscope.
- **22.5–23.5:** A heavy hand (`RED` rim) slams the red knight down (23.0), and the other pieces
  jump. *Thud.*
  - 23.5–25.0: His profile in the dark: the ember brightens as he draws (24.0), smoke curls.
- **25.0–34.0:** The table from the side under the swinging lamp, the three pieces standing on
  the plan at her end.
  - The briefing: she leans in over the plan (25.4–25.95), murmuring, and we cut in close over
    the plan (25.9–27.9). Her gloved fingers come in over the vault and tap the X twice, on the
    beat (26.5, 27.0): here. The gold beside it glints on the second tap. *Her low voice, no
    words; two finger taps on the paper; a ting.*
  - Back at the side, she straightens (27.9–28.4) and the Cracker nods (28.25). *His low hum.*
  - His `RED` sight line runs down to the X (29.5). Her `PAPER` sight line runs across to his
    face (30.5). *A low held note: she knows.*
  - She reaches for the chalk (31.5) and has it (32.0). The camera tilts down over the table
    onto the plan (32.0–34.0) and lands on s03's first frame. *A rising paper whoosh; the bass
    walks up into the theme.*

### s03 PLAN (34–50)

The plan from above (`phi` 64 → 72), one continuous glide that follows her chalk. The pieces
hop along the route in file (bishop, queen, knight), landing on the beat. Hands are about one
and a half pieces tall.

- **34.0–37.6:** ① Her chalk taps a 'down here' chevron on manhole A (34.5). The route runs
  east along the sewer and north up the branch to the store-room hatch. The pieces join the
  line one by one and hop along behind the chalk.
- **37.6–39.0:** ② Through the store room to the corridor. The Cracker's old hand (gold rim,
  shirt cuff) sets a black pawn, the guard, on his post (38.5). *Clack.*
- **39.0–40.0:** She sweeps his light out from the pawn. A timing ring goes round him, with
  four ticks and a dot that runs round once per swing. The light swings 32° each way, a full
  swing every two seconds, so the crossing is dark on 40.5, 41.5, 42.5 and so on. *A low
  wooden tock at each end of the swing.*
- **39.5–42.5:** ③ The route crosses the corridor, and ④ runs north to the vault door. The
  pieces cross one per dark gap: the bishop (40.5), the queen (41.5), the knight (42.5).
- **41.0–42.1:** The bishop reaches the door. A gold lens on a leader line opens on the dial,
  which turns right, left, right (a numbered gold arrow for each turn: s06's three gates).
  *Clunk* (42.0): the door swings open. The chalk runs in to the X (42.4), and the bishop and
  the queen hop in.
- **44.2–44.75:** The Knight's own red hand snatches his piece off the route at the door and
  slams it down out on the street (44.75, *THUD*). The others jump, and the vault door on the
  plan claps shut on them. In that same instant her hand, lifting away from the vault,
  touches the sewer line under it and leaves a dot. That is the plant, hidden by the slam:
  everyone is looking at him, and the tap is buried under the thud.
- **45.5–47.7:** ⑤ She draws the way out along the street to him, a chalk car beside him, and
  a small bell on the side door (47.0). Then she taps the bell with her chalk (47.5): it rocks,
  with a ripple (v5: the plant for the alarm s07 rings). No one remarks it. *A tiny chalk
  scratch; one damped tink, the alarm bell's own note, muted.*
- **48.0–50.0:** The plan is done and the light settles. The camera starts to tilt down (phi
  is falling at 15°/s at the cut), and s04 carries on the move from `P.HANDOFF_34`.

### s04 NIGHT (50–62)

- **50.0–53.0:** The pop-up. The camera tilts from about 50° to eye level. The walls extrude
  from the chalk lines (`P.draw_walls_3d`), the paper darkens to `NAVY` night, the moon pops
  up, and the street lamps stand. The plan's dotted route remains as a ghost layer on the
  world.
- **53.0–56.0:** Front street. The three arrive along the curb: she stealthily, the Cracker
  creeping, the Knight heavy with empty bags. He lifts manhole A (*iron scrape, clank*), and
  they go down one per beat.
- **56.0–62.0:** The camera sinks through the road into the section. The tunnel. They move
  along the pipe while the chalk dots of the route brighten as they reach them. *Drips;
  their steps in water.* Up the rungs, and the hatch opens (*creak*). The stopwatch appears
  top right and starts at 56.0 (one tick per beat).

### s05 GUARD (62–80)

Rebuilt in v4 to read at phone size. A 9:16 frame cannot hold the guard and the crew at a size
that reads, so the corridor is framed close (the figures half the frame's height, the corridor
floor to ceiling filling it) and the camera moves with the action, in one continuous shot.
Film times (the module's beats plus 62 s).

- **62.0–66.0:** The corridor in side elevation, dark, close on the guard. He walks out to his
  post and his flashlight clicks on (62.5); it sweeps on the plan's clock (a full swing every
  2 s). The camera pans right along his beam to the dark doorway (63.9–65.4), where the crew
  stand pressed in file, black on black, only their rims showing, as its patch slides up to the
  doorway's edge (65.0) and falls away. *The score drops to the tick; a breath held.*
- **66.0–71.5:** The stealth map: the camera tilts up into the plan (66.0–67.0). The crew sink
  into their pieces and the guard into his pawn, whose cone sweeps the intersection. In the dark
  gaps they hop across one at a time, on the beat (she 67.5, the Knight 68.5, the Cracker 69.5).
  The camera tilts back down, close on the doorway (70.5–71.5). *A tiptoe bass; a vibraphone note
  for each piece.*
- **71.5–77.5:** The near miss, one beat at a time:
  - the Cracker, last in, steps to the mouth (71.5) and stops to get his breath (72.0); his
    stethoscope swings and CLANKS on the pipe (72.5, a ripple);
  - the camera whips left to the guard as he spins round (72.62–73.3); his light swings toward
    the noise and stops on the crates: two gold eyes (74.0);
  - the cat arches (74.5) and leaps down past him (75.0), its tail tipping the tin can, which
    hits the floor (75.5, *clatter*, the v2 punch-in) as the cat streaks between his feet;
  - he breathes out, half a laugh (76.0), lowers his light, turns away and walks off west
    (76.5); the camera drifts back to the doorway as the crew slip into the dark.
- **77.5–80.0:** The camera pushes down the black corridor to the far door (77.5–79.0): a chalk
  dot and the plan's ring on its dial (step 4, 78.5). s06 opens on that dial. *The band creeps
  back.*

### s06 SAFE (80–94)

- **80.0–83.0:** The vault door fills the frame. The Cracker kneels and sets the stethoscope
  to the door.
- **83.0–90.0:** The dial in close-up, with the lock in cutaway under it: three wheels with
  their gates. The dial turns right, left, right. As each gate comes under the fence a chalk
  dot pops. *Clicks pitched low, mid, high; a ripple into his ear each time.* When the third
  gate arrives, the three dots join in a straight chalk line and the fence drops. *Clunk.*
- **90.0–94.0:** The bolts withdraw round the rim (*a rolling metallic run*). The door swings
  (the circle narrows to an ellipse) and gold light floods out over three silhouettes.
  *A brass swell.*

### s07 CROSS (94–114)

v5 cuts in close on the ruby (1.5–4.0) and ends on the side door bursting open under the bell
(17.0–20.0). Film times (the module's beats plus 94 s).

- **94.0–102.0:** Inside the vault, on gold. The Knight drops bars into a sack while the
  Cracker, kneeling, hands them over; behind them she goes to the deposit wall and opens one
  small box (94.35–95.5), and the camera eases in on her.
  - **95.5–98.0, the ruby, close:** a ruby on a dark cushion, glowing red; it glints. Her gloved
    hand comes in (96.0), finger and thumb close on it (96.5–96.7), and she lifts it out into
    the light (96.7–97.3), where it flares (97.0); her hand takes it away (97.65–98.0). *A
    glove's creak; a soft rising string harmonic; a bright glassy shimmer on the flare.*
  - Back on her: she slips it into her coat pocket with her back to them (98.0–98.6). No one
    sees.
  - The camera eases over to him (99.15–100.1): he pulls the sack shut and stands over the two
    full bags. His `RED` look goes to the bags (100.4); he turns (a cut-paper turn), and it goes
    to the open door (101.1), carrying the camera.
- **102.0–106.0:** The X-split. The four panels cut in round the clock and the frame is split on
  both diagonals:
  - top: him heaving up the two bags;
  - right: the Cracker kneeling, turning a bar in the light;
  - bottom: the door's edge from the corridor, the gold beyond;
  - left: her shutting the little box and patting her pocket (a red glint, 103.3).

  He moves off toward the door (104.5), the X seams turn `RED`, and his shadow comes out of the
  gold in the bottom panel.
- **106.0–108.0:** The panels fly off and the bottom one is the frame. Outside, he drives the
  great door shut with a lunge, lets go and steps back to watch it swing; the ellipse widens
  back to a circle, and the two inside turn too late. BOOM on the bar line (108.0): black, and
  in the dark the rim's bolts shoot home.
- **108.2–109.0:** The dial, close, in `RED`: s06's lock run backwards. His gloved hand on the
  knob, the bolt shoots home, the fence lifts, the gates' line is rubbed out and the dial spins
  the gates away.
- **109.0–111.0:** Matched on the dial, the plan comes up round the red close-up, which shrinks
  into the plan's chalk dial. The red knight hops along his `RED` route: down the chalk route,
  then off it in an L (east, then down the alley) to the car. The stopwatch stops dead as he
  turns off the route (109.5) and its hand turns `RED`. Landing at the side door (110.5) he
  sets off the bell she chalked there in s03: it rings red. *The theme, inverted.*
- **111.0–114.0, the alarm:** the side door itself, from the alley. It bursts open (111.0),
  and the Knight charges out with the two bags and runs for the street. Over the door the alarm
  bell rings and rings, with red ripples on every beat, and the camera pushes in on it
  (111.7–114.0). *BANG: the door against the wall; the bell, nearer and louder as the camera
  pushes in; his heavy run, the gold clinking in the bags.*

### s08 LOCKED (114–126)

- **114.0–116.85:** Black, and the Cracker's ragged breath. A match scratches (sparks, no
  flame), then strikes (*flare*), and gold rings of light open on her profile, calm, with the
  Cracker beyond her, leaning on the round door. He rears back, fists up.
- **116.85–117.9:** We cut on his first blow to the shot from behind him: his back and bowler,
  both fists pounding the door at head height (*three muffled BOOMs*). Each blow rings on the
  steel and shakes dust down; the camera shakes. His shadow looms over him on the door. The
  flame shivers.
- **117.9–119.35:** Her eye in close-up, steady. Her look drops to the floor as a white dotted
  sight line and the corner of her mouth lifts (*vibraphone, upright*). The camera whips down
  after the look.
- **119.35–122.0:** At floor level, the sight line lands in a chalk ring at her heel. She taps:
  a click, then a hollow knock. The floor opens top-down into a blueprint section (the slab,
  the earth, the sewer pipe) and the knock rings down through it. A gold plumb line drops from
  her heel to the chalk dot on the pipe, and a lens joins it to the dot on the plan (the vault,
  its X and the dot).
- **122.0–126.0:** The two-shot. The Cracker turns round to her (a cut-paper turn). She brings
  a roll up from her coat to her eye and lets it fall open before her face, then lifts the
  sheet toward the camera until it fills the frame, the match glowing through the paper. s09
  begins on this sheet (`S8.roll_shot(c, S8.T_END)`).

### s09 PLAN B (126–148)

The scene's `REWIND` and `FREEZES` tables say which scene is on screen when, so the mix can run
that scene's own sound backwards and forwards with the picture. v5 adds the night before in the
dot's lens (4.2–8.2) and gives each of Plan B's marks a beat or more of its own. Film times (the
module's beats plus 126 s).

- **126.0–126.15:** Held on s08's last frame (the sheet held up to the match).
- **126.15–128.75:** The rewind. The film runs backwards through s08, s07, s06, s05 and s04,
  0.4 s each, and into s03, under chalk streaks and a double chevron, with the heist stopwatch
  spinning back (its hand red while past the stop). *Tape-rewind whoosh.*
- **128.75–129.5:** Played forward (chalk corners round the frame): the Knight slams his piece
  down and her chalk, lifting off the vault, leaves the dot. *A tape click.*
- **129.5–130.2:** Freeze. A lens snaps round the dot (129.55). Magnified, it sits on the sewer
  line inside the vault, with a gold ripple on it. *A ting.*
- **130.2–134.2, the night before:** the lens opens over the whole frame (130.2–130.7), onto the
  floor of the vault in section and the shaft under it. She is on the ladder under the slab, and
  her torch cuts up through it, two cuts in a shower of sparks (130.95–131.55, 131.7–132.3).
  She pushes the cut block up a crack (132.45–132.85), and her light falls on the gold above;
  she sets it back (133.15–133.45): from above it is only a floor tile. The lens closes back
  onto the dot (133.7–134.2). *A deep soft whoosh down into the dark; drips and a low drone; the
  torch's roar, hiss and sparks; stone grinding; a faint shimmer on the gold; a reverse whoosh.*
- **134.2–136.6:** Back again into s02, then played: his red look at the X, her white look at
  him. Freeze, and a lens on her eye with his red look glinting in it (136.05).
- **136.6–142.9:** The plan from above. Her tracing sheet unrolls down over it (136.6–137.15,
  *paper*; the band turns to D major under it). Plan B is chalked on it in solid lines and
  numbered in solid discs (Plan A's numbers are rings), one mark at a time, the camera whipping
  from one to the next:
  1. the trapdoor square at the dot (137.4–137.85);
  2. her route down through it, north along the branch to manhole B (ringed) and west off the
     sheet (137.95–138.9);
  3. his red L, struck out fast to the side door and his car (139.2–139.9); the bell there rings
     red as the line passes it (139.62, *the alarm, small and far*), and four police cars slide
     in nose first at his car, from the west, north, east and south, their bars flashing, one
     per half beat (140.0–140.75, *trumpet stabs*);
  4. a `RED` X on the ruby box (141.35–141.55).

  Pull back: both plans at once (141.75–142.4). *The theme returns upright, in the major
  (142.0).*
- **142.9–143.92:** The vault by match light, close. Kneeling, she lifts the floor tile over the
  trapdoor (143.12–143.8) and lays it aside: below is black. The match grazes the floor and the
  tile's underside.
- **143.92–144.66:** The Cracker's face, lit from below. He stares, the light crosses his
  spectacles (144.0, *ting*), and he grins (144.28, *a dry chuckle*).
- **144.66–148.0:** Section. The floor is cut away under the vault: the shaft under the
  trapdoor, its iron ladder, the branch pipe and its water. The camera pulls back as she steps
  into the hole, slides down the ladder with the match held up and splashes into the pipe; he
  follows. She turns north and they wade off left, with Plan B's solid line lighting the way
  ahead of them. The cut runs on north along the pipe to manhole B (146.1–147.7), and the line
  lights up its shaft to the back street and rings there (147.15–147.75).

### s10 CHECKMATE (148–166)

Scene times. v5 makes the alarm call the police (2.92–8.0) and adds the arrest on the street
(9.2–12.92).

- **0.0–1.46:** The front street at night, the alarm bell ringing red high in the alley. The
  Knight bursts round the car's tail with two heavy sacks (the mocap's run and sudden stop,
  0.2), swings them up (0.95–1.12) and flings them in through the open rear door (1.12–1.26),
  and slams it (1.32–1.42). *Bell, running steps, a skid, a grunt, the bags, the slam.*
- **1.46–2.92:** Close on the car's nose: the engine coughs twice (1.62–1.86), the headlight
  flares and the engine catches (2.02), the car lurches off west (2.5–2.9) and its light fills
  the frame (2.68–2.92).
- **2.92–8.42:** Out of the white, the city from above as a chessboard: the blocks are its
  squares and the bank, in the middle, is the blueprint. His red car speeds along the front
  street at the end of his red trail (3.15–3.55).
  - The bell by the bank's side door rings red, and its rings run out over the city, one per
    beat (from 3.0). *The bell ringing on, a ring a beat rolling outward.*
  - Four police cars wait dark down the four streets round him. As the first ring reaches each,
    its bar switches on, one per beat (4.5, 5.0, 5.5, 6.0: W, N, E, S, exactly as she chalked
    them in Plan B). *A clunk and a siren whoop each.* The first one's lights, dead ahead, stop
    him (4.55, *brakes screeching*).
  - They slide in nose first like rooks, one per beat (6.0, 6.5, 7.0, 7.5), *each with a stab*.
    The red marker ring snaps round his car at 8.0: checkmate. The camera rolls (his panic, the
    film's one Dutch tilt, 8.0–8.42). *Sirens braid.*
- **8.42–9.2:** His face in the car's side window, washed red and blue by turns, his eyes
  darting. *A heartbeat.*
- **9.2–12.92, the arrest:** the street again, boxed in. A police car is nose to nose with his
  and one nose to tail, the third's bar flashes over his roof from the alley, every lamp is on
  him, and the bell still rings above. He shoves the door open (9.62) and climbs out with a sack
  (9.8–10.3), looks east (10.5) and west (10.82), and lets the sack go: it thumps down and the
  gold spills on the road (11.0–11.12). The camera cuts in close as it topples (11.3), and he
  puts his hands up in the light (11.36–11.72). *The bell above the street and the police
  engines idling; the door, a heavy step, a gasp; the sack's thump and the gold; a held low
  string note as his hands go up.*
- **12.92–18.0:** The pull-back (*D major comes up*). Manhole B's lid slides off two blocks north
  (13.67–13.97), she climbs out and the Cracker follows (13.92–14.17); a lens on the manhole
  (13.57–15.57) shows the two small figures walking west, her white route lighting up behind
  them. From 15.72 to 16.92 the two routes, his red and her white, straighten into two strokes
  crossing over the bank: an X, held to the cut.

### s11 END (166–174)

- **0.0–0.62:** The X splits the frame along its own strokes: s10's last frame breaks into four
  triangles that crack apart and fly off, each carrying half of the strokes on its edges. *A paper
  rip; the sirens cut off.* In the gap, from straight above: her gloved fist under a street lamp,
  over the pavement (the kerb along the red stroke's diagonal, the lamp in a puddle).
- **0.55–1.3:** Her fingers open one after another, the index first, red light escaping: the ruby,
  a cut stone on her palm exactly where the X crossed. At **1.5** it glints, an X of light along
  the frame's diagonals (*the one celesta ping*). **2.45–2.75:** she closes her hand on it, and the
  red light leaks between her fingers and dies. *The glove creaks.*
- **3.0–4.35:** Dawn at the table, the lamp low and a cold wash from the window. The red knight
  stands where he set it by the car in s03, inside the red ring and Plan B's chalk police. Her
  gloved hand brings the white queen in low from the west; its base knocks his (3.85, *click*), he
  goes over to the east and lands on his side (4.0, *clack, roll*), and the queen is set down on
  his square: the queen takes the knight. Her hand lets go and leaves.
- **4.35–5.5:** The camera rises off the table to the whole plan, straight down (s01's top view).
- **5.5–6.0:** The chalk X lifts off the vault and grows into the title X (s01's landing run
  backwards), landing on the last chord at 6.0. This time the white strip lies over the red: she
  crossed him last.
- **6.2, 6.45:** DOUBLE and CROSS slide back in from the top and the bottom, where the opening's
  flew out. **7.0:** the ruby lands as the red dot at the crossing (*the film's last chalk tap*).
- **7.5:** Black, the red dot a breath longer, gone by 7.9.

## v2: the borrowed shot types

The scene times in this section are v2's; the last column gives where each insert plays in v5
(v4 rebuilt s05, whose punch-in is now at s05 13.49; v5 moved s07's BOOM to 14.0 and s10's
checkmate to 8.0, and the inserts moved with them).

Four of the reference edit's shot types, cut to this film's paper (the reasoning, and what was
left out, is in `docs/SHOT_TYPES.md`). The helpers are `films/double_cross/shots.py`. Each scene
keeps its drawing as `render_plain` and lists its `INSERTS`. The s09 rewind replays the scenes
plain, so each insert plays once, in its own scene.

| Film time (v2) | Scene, local time (v2) | Shot | What it does | Film time (v5) |
|---|---|---|---|---|
| 1:03.4 | s05, 11.375 (5 frames) | Punch-in ×6 | The tin can hitting the floor, its clatter rings, the shake. | 1:15.5 |
| 1:17.0 | s06, 11.0 (2 frames) | Flash, gold | The seal breaks and the gold floods out. | 1:31.0 |
| 1:32.0 | s07, 12.0 (2 frames) | Flash, red | The vault door's BOOM. | 1:48.0 |
| 1:32.1 | s07, 12.083 (5 frames) | Silhouette on a sunburst | The Knight black on red rays, held in the lunge that shut them in. | 1:48.1 |
| 1:39.3 | s08, 3.29 (5 frames) | Punch-in ×4 | His fist on the door at the second blow, the steel's rings. | 1:57.3 |
| 1:48–1:54 | s09, every rewind join (2 frames) | Slip | Strips of the frame slide sideways, heavier the deeper back it goes. | 2:06–2:16 |
| 2:05.6 | s10, 1.625 (5 frames) | Punch-in ×4.5 | The dead headlight on the first cough (it flares at 2.02). | 2:29.6 |
| 2:09.9 | s10, 5.917 (2 frames) | Flash, black | Black, then checkmate. | 2:35.9 |
| 2:19.9 | s11, 3.875 (5 frames) | Punch-in ×3 | The lens rides the knight's fall as the queen knocks him over. | 2:49.9 |

- **Punch-ins** are redrawn as vectors at the zoom, so their lines thicken as they come in.
- **The cut-paper wedges** rush in from the edges in place of manga speed lines.
- **Flashes** carry no lettering, because the film is wordless.
- **Slips** keep the palette (no colour split).
- **Sound:** every insert lands on a hit that is already in the mix, so the sound is unchanged.

## v3: the review fixes and the voices

**Withdrawn in v4** (below): v4 restored v2's picture and kept only v3's voices. The times in this
section are v3's.

After v2 the user asked for the whole-film review's fixes, and whether the film should have
voices. The picture changes are in s01, s02, s03, s09 and s10 (s11 is re-rendered because it
opens on s10's last frame). s04–s08 are unchanged; s07 and s08 gain the voices below. The
reframing of s04–s05 that the review also raised was left alone.

| Film time | Scene, local time | What changed |
|---|---|---|
| 0:00–0:07 | s01, 0.0–7.0 | It opens on the bank at night, at s04's eye level. Four chalk dots tick in at the corners of its front (0.5–2.0), and dotted lines join them (2.0–2.5): the bank, marked. The street folds flat, back to front: s04's pop-up run backwards (2.5–3.5). The camera tilts up to straight down (2.75–4.0), and the chalk outline lies down onto the paper that was under the street all along, as the night lifts off it (3.0–3.9). The plan rules itself in from that outline (4.0–7.0). |
| 0:11.1–0:12 | s01, 11.1 | As the X lands, a gold lens opens off it on what it marks: the vault's gold, through its door (a glint at 11.45). s02 closes it. |
| 0:21–0:24 | s02, 9.0–12.0 | The briefing, wide. The table is seen from its south side, a little above, with the crew round it under the swinging lamp: her at the west end, the Cracker bent over it from the far side, the Knight at the east end. Her chalk taps the X twice (9.25, 9.5), his red look goes down to it (9.6), and hers goes across to him (10.5). She takes the chalk off the X and in toward manhole A (11.0–12.45), where s03 picks it up. |
| 0:24–0:35 | s03 | Her chalk hand reads as hers: the glove has a bold white edge (three times the others' rim) and a wider cuff line, and the Cracker's cuff is in his gold. Lenses open on step ① (1.05–2.3: manhole A's iron lid in the road, with SEWER cast on it) and on step ③ (5.55–6.75: the guard at his post, his light swinging). |
| 1:58.1–1:58.8 | s09, 10.12–10.8 | Each of Plan B's marks gets a beat. The camera holds on the red X (10.12–10.58), then whips back to both plans (10.58–10.8) and rests on them a breath before the cut. |
| 2:11.2–2:13.5 | s10, 7.2–9.5 | Her way out, full frame: the back street, looking north. Manhole B's lid is knocked up off its seat (7.47) and dragged aside (7.6–7.88). She climbs out with her hands planted on the road, then the Cracker. They walk west under the street lamp, with the police lights pooling blue and red on the wall beyond the roofs. Then back to the board (9.5), where the routes straighten into the X (10.0–11.2). |

### The voices

These are the film's only voices. They were generated once (Magnific, ElevenLabs eleven_v3, 114
credits) and are kept in `audio/gen/`. The words they say are in `mix.py`'s `LINES`, for the
record.

- **The briefing's murmur** (s02 9.05–10.45; s03 0.1–10.7). Three voices: hers (a low whisper),
  the Cracker's (dry and old) and the Knight's (low).
  - They speak the plan, but the mix never lets it be heard as words. Each line is cut into
    syllables at the dips in its level, and the syllables between its first and last are
    shuffled. The line is then low-passed (at 1.3, 1.05 and 0.9 kHz) and put in the table's room,
    about 13–16 dB under the score.
  - Their voices, pace and cadence survive, but nothing is said, so the film stays wordless.
  - Who speaks follows the picture. She starts over the X and stops on her look. In s03 she
    leads down the route; the Cracker hums, then asks as he sets the guard. She answers through
    the light's sweep, and through right, left, right at the dial. He has opened worse. The
    Knight cuts in as his hand comes in, and his slam ends it.
- **The Knight's grunts** (s07 6.4 and 10.12). His own strained voice replaces the synthesised
  grunt twice: as he heaves up the bags (the gold shifting inside them), and as he throws his
  weight against the vault door, held for 1.5 s as it swings.
- **Her breath of a laugh** (s08 4.59). Through her nose, soft and close, as the corner of her
  mouth lifts, just ahead of the theme's two notes.
- **The rewind.** The rewind carries the voices too: s09 plays the briefing backwards, and plays
  it forward at his slam.

## v4: slower, the guard rebuilt, back on the system

The user's verdict on v3: it was too fast, it skipped the guard part, it was a downgrade rather
than an upgrade, and it drifted away from the system. They were right on all four. v3 packed new
content into the same seconds (a bank opening, a gold lens, step lenses, a back street), and it
left the guard's reframing undone although they had asked for it.

So v4 starts again from v2's picture: s01–s03 and s09–s10 are v2's code (`9ea5f1b`), and s08
keeps only v3's laugh cue. It keeps v3's voices, and makes two changes. Each gives a beat time
instead of more content:

| Film time | Scene | What changed |
|---|---|---|
| 0:21–0:28 | s02, 9.0–16.0 | s02 runs 16 s (two more bars), and the side shot carries the briefing. The pieces stand on the plan between them. She leans in, murmuring, and taps it twice beside the pieces on the beat (10.0, 10.5); she straightens and the Cracker nods (10.75). His look (11.5) and hers (12.5) each get a bar. She takes the chalk (14.0), and the camera tilts down over the table onto the plan (14.0–16.0), landing on s03's first frame: the film's own tilt, so the people and the plan are one place. |
| 0:56–1:14 | s05 | s05 runs 18 s (two more bars) and is rebuilt to read at phone size (see s05 above). It is framed close, with the camera moving with the action: the pan along his beam to the crew, the map, the whip to the guard on the clank, his light on the cat, the drift back, and the push to the dial. The near miss, from the Cracker's step to the guard's sigh, takes 4.5 s on the beat grid, where v2 had 2.4 s. |

- **The edit.** From s03 every scene starts 4 s later, and from s06 8 s later. The film is 2:32
  (3,648 frames). The heist clock is derived from the timeline (`K.film_start`): it starts at
  0:50 and stops dead at 1:41.5, and s06 and s07 take their film times from it too. s09's
  rewind rows and freezes follow s02's and s05's new lengths.
- **The sound.** The score is re-timed to the new bars:
  - bar 11, the briefing: the band drops to a murmur of its own under her voice;
  - bar 12, her look: the low held D;
  - bar 13: a rising paper whoosh under the tilt, and the bass walks up into s03's theme;
  - s05: the tiptoe bass runs from bar 30 and walks up to the clank; a whip whoosh; the held
    breath as his light finds the cat; the band creeps back at bar 36.
  - Two new cues in s05: a breath held in the doorway as the light's patch touches its edge
    (2.9), and the whip's whoosh (10.62).
- **The voices in v4.** Her murmur under the briefing (s02 9.25–11.3, line 0) and the Cracker's
  hum at his nod (10.75, his "Hm."); the murmur over the plan (s03 0.1–10.7, now a module beat,
  `T_MURMUR`); the Knight's grunts (s07 6.4, 10.12); her breath of a laugh (s08 4.59).

## v5: the double cross, easy to follow

The user's verdict on v4: hard to follow. They could not tell that a burglary was being planned,
who crosses whom, what was in her hand, how the alarm goes off, how the flashback explains her
second way out, or how the police come and catch the Knight. Asked whether to change the story
or keep it, they chose to keep it and make it clear: the Knight locks the other two in and runs
with the gold, she had planned for it, the police catch him, she and the Cracker leave by the
sewer, and she keeps the ruby.

Each question gets a picture, and each picture gets time of its own (a bar each, v4's lesson),
so the film grows from 2:32 to 2:54:

| Question | v5's answer | Scene, local time |
|---|---|---|
| Is a burglary being planned? | The bank's front is marked in chalk and folds flat into the plan; the X lands on the vault and a gold lens opens on the gold under it. At the briefing, close over the plan, her finger taps the X twice and the gold glints. | s01 0.0–16.0; s02 9.9–11.9 |
| What is in her hand? | The ruby, close: her glove lifts it out of the box into the light, where it flares, and she pockets it. | s07 1.5–4.6 |
| How does the alarm go off? | She chalks a bell on the side door and taps it (a damped tink: the alarm's own note). His L runs through that door; it bursts open and the bell rings over it. | s03 13.0–13.7; s07 16.5–20.0 |
| How does the flashback explain her way out? | In the dot's lens, the night before: she cuts a trapdoor up through the vault floor from below and sets it back as a tile. Plan B then shows its marks one at a time. | s09 4.2–8.2, 10.6–16.4 |
| How do the police come and catch him? | Plan B's third mark shows it in chalk first: his L, the bell, the police. Then the bell's rings roll out over the city and wake four police cars, which box him in, and on the street he drops the gold and puts his hands up. | s09 13.2–14.75; s10 2.92–12.92 |

- **The edit.** s01 gains two bars (16 s), s02 one (18 s), s07 two (20 s), and s09 and s10
  three each (22 s, 18 s): 2:54, 4,176 frames, 87 bars. The heist clock starts at 0:56 and
  stops dead at 1:49.5 (107 ticks). s09's rewind follows s07's new length (its s07 row runs
  20.0 → 0.0), and the freeze on the dot holds while the night before plays in its lens
  (3.5–8.2).
- **The picture.**
  - s01 is v3's opening (the bank marked, the fold, the gold lens) with a bar for each part.
  - s02 cuts in close for the tap on the X.
  - s03's bell is tapped.
  - s07 cuts in close on the ruby, and ends on the side door from the alley.
  - s09 shows the night before, under the slab, and redraws Plan B's third mark as his L, the bell
    and the police.
  - s10's rings wake the police cars and his brakes stop him, then the arrest street.
- **The sound.** Two new synths: `bell_tink` (the alarm's note, damped by her chalk) and
  `torch_cut` (a cutting torch's roar, hiss and sparks).
  - s01: a low string note under the marked bank; the fold's paper; a vibraphone note with
    each chalk group; a vibraphone roll as the gold lens opens and a ting on each glint (the
    celesta stays the ruby's, in s11).
  - s02: her two finger taps and a ting on the glint.
  - s03: the bell's damped tink, in place of v4's ting.
  - s07: the ruby gets a glove creak, a rising string harmonic as it lifts and a glassy shimmer
    on the flare. The alarm rings small on the plan, then BANG: the door, and the bell over it,
    4 dB louder over the push in. His run has the gold clinking in the bags.
  - s09: the night before has a deep whoosh into the lens, the shaft's drips and drone, the
    torch, stone grinding as the block goes up, a shimmer on the gold, and a reverse whoosh out.
    Under Plan B: a bar of D major under the sheet, his semitone under the red L, the alarm
    small and far, and the stabs.
  - s10: the bell rings a ring a beat over the city, and each police car gets a clunk, a thump
    and a siren whoop; his brakes. At the arrest: the bell above the street and the police
    engines idling, the door, his step, a gasp, the sack and the gold, and a held low string note
    under his hands. D major comes up on the pull-back.
- **Measured.**
  - -16.01 LUFS, true peak -1.30 dBTP, no clipped samples; the limiter takes at most 5.3 dB (the
    BANG, 1:51.0).
  - 473 cues: 449 realised by the sections, 24 auto-spotted (all in s07, as before), 0 missed.
  - The worst cue-to-event offset is 30 ms, and no measured onset is more than a frame out.
  - The clock's 107 ticks are all within 0.5 ms of the beat.
  - The QA's "limiter at most" now reads the limiter's own gain. The old out/in ratio per sample
    read the 4 ms head fade on v5's near-silent first samples as -14 dB of limiting.

## Sound plan (for the mix)

- **Score: heist jazz at 120 bpm in D minor.**
  - Instruments: a walking pizzicato bass, brushed snare, vibraphone, muted trumpet stabs, a
    low piano. The clock is a dry woodblock tick on every beat from s04 to s07.
  - **THE DOUBLE CROSS** is in the music. The four-bar theme (vibraphone) is heard plainly
    in s02–s03. At the betrayal (s07) it returns in **mirror inversion**, low and minor.
  - In s09 the score **rewinds with the picture**: the actual mix of the earlier scenes is
    played reversed and sped up under the scrub. Then the theme returns **upright in D
    major**, the inversion inverted. In s10 it braids with the sirens.
  - The end resolves on D major, with one celesta ping on the ruby.
- **Foley:** reuse the library in `films/opposite/audio/gen` (steps, breaths, gasps, door,
  handle) and synthesize the rest:
  - chalk scratches and taps, paper unroll, wooden piece clacks;
  - the manhole scrape, sewer drips and water steps, the hatch creak;
  - the flashlight click, the stethoscope clank, the cat's can;
  - dial clicks (three pitches), the fence clunk, the bolt run, the vault door's groan and
    BOOM, gold clinks;
  - the alarm bell, the match strike, the hollow knock, the tracing-paper slide;
  - the rewind whoosh, the car engine and door, sirens.
- **Paid generation: voices only, from v3.** v1 and v2 used none, and everything else is
  synthesized or reused. v3 adds the voices' takes (114 credits; see v3 above); v4 and v5 add
  none.
- **Mix:** −16 LUFS, true peak −1 dB.

## Technical

- **Scene files:** `films/double_cross/scenes/sNN_slug.py` with:
  - `render(f, t, T)`, which calls `K.scene_setup(f, field)` first and then draws inside
    `with f.screen() as c:`;
  - `cues(T)`, a list of `engine.timing.Cue`;
  - `motion_blur(t, T)`, which returns 1;
  - beat constants at module level (`T_SLAM = 10.5`, and so on).
- **Imports:**
  - `from films.double_cross import kit as K` (palette, devices);
  - `from films.double_cross import plan as P` (plan geometry, camera, plan drawing);
  - `from films.double_cross import cast as C` (the figures);
  - the Bass world's helpers are available as `K.B`.
- **Stills:** `RENDER_WORKERS=1 python3 -m engine.render --film double_cross sNN --times=1.0,2.5 --scale 1.0 --force`
  (the default scale is 0.5). Outputs go to `films/double_cross/qa/sNN/`.
- **Contact sheet:** `RENDER_WORKERS=1 python3 -m engine.render --film double_cross sNN --sheet 12 --window 2:6 --scale 0.25`.
- **Budget:** at most 1.5 s per full-size frame. Deterministic: no unseeded random.
- **Text:** no text in picture except the title and hand-cut numerals.
- **Self-review:** look at your frames at full size. Check hands, edges, seams, popping,
  readability at phone size, and that every beat reads in one glance.
