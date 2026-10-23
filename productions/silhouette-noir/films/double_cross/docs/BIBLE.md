# DOUBLE CROSS

A 2:24 vertical (1080×1920, 24 fps) heist thriller in the trilogy's cut-paper Saul Bass language.
Wordless, scored. The film is told through its own blueprint: the plan is drawn in chalk, the plan
rises off the paper into the night, and the story is what happens when someone leaves the line.

## The story in one breath

A blueprint unrolls. A bank, drawn in chalk. Under a hanging lamp three hands set three chess
pieces on it: a white QUEEN (the Architect), a gold BISHOP (the old safecracker), and a red
KNIGHT (the muscle). While she chalks the route, his eyes go to the X on the vault, and she sees
him look.

Night. The blueprint folds up into the city. Down a manhole, along the sewer and up through a
hatch, the crew follows the chalk dots. They slip past a guard's sweeping flashlight. The
Cracker opens the vault: three gates line up and the door swings open on gold.

Then the Knight double-crosses them. He shuts the vault on the other two and spins the dial. His
red line leaves the chalk route in an L, the knight's move, out of the side door to the car. The
alarm rings.

In the dark a match flares. The Cracker pounds the door, but the Architect is calm. She taps the
floor and it sounds hollow. She unrolls a second sheet: tracing paper. The film rewinds to what
we missed. While she was chalking the plan, she dotted the sewer line exactly where it passes
under the vault. The overlay slides over the plan and shows PLAN B:
- a trapdoor in the vault floor;
- her own route out by the sewer, the opposite way;
- the police waiting at his car;
- her real prize, not the gold but one ruby.

Police cars close on the Knight from all four streets and a red ring snaps round him:
checkmate. Two blocks away a manhole lifts, and she walks off into the night. Back at the table
her gloved hand tips the red knight over. Her palm opens on the ruby: the red dot.

**DOUBLE CROSS:** he crosses the crew; she had crossed him before he moved. X marks the spot
twice.

### Plants and payoffs (play fair)

| Plant | Payoff |
|---|---|
| s01: the dashed sewer branch is drawn running right under the vault. | s08 the hollow floor; s09 the trapdoor. |
| s02: his red look goes to the X, and her white look catches him. | s07 the betrayal; s09 the rewind's callout on her eye. |
| s03: as the Knight slams his piece down by the street, her chalk, lifting away from the vault, leaves a small dot on the sewer line under it. | s09: the rewind stops on that frame: the dot and his slam at once. |
| s03: his slam claps the plan's vault door shut on the queen and the bishop. | s07: he shuts the vault on the other two. |
| s03: a small bell is drawn on the side door. | s07: his L route goes through that door, and the alarm rings. |
| s07: she opens one small deposit box, and something red glints. | s11: the ruby. |

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
back again. Cuts between plan and world match on a point: a manhole, the vault door, the X.

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

- Cut paper moves crisply. No motion blur (`motion_blur` returns 1).
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
Each scene module defines its beats as module-level constants and exports `cues(T)`
(`engine.timing.Cue`) for the sound.

| id | slug | film start | length | who | what happens |
|---|---|---|---|---|---|
| s01 | title | 0.0 | 12.0 | me | ticks; the blueprint unrolls; the bank rules itself in chalk; the title strips cross into an X; the X lands on the vault |
| s02 | crew | 12.0 | 12.0 | me | three hands set three pieces; three profiles; the table in elevation; his red look at the X, her white look at him |
| s03 | plan | 24.0 | 16.0 | me | she chalks the route ①–⑤ and the pieces hop along it; the guard's cone and its timing; the car; the bell; the dot under the vault |
| s04 | night | 40.0 | 12.0 | animator | the pop-up: the plan rises into the night street; the manhole; the descent; the sewer section; up through the hatch; the stopwatch starts |
| s05 | guard | 52.0 | 14.0 | animator | the corridor: the guard's cone; hiding; the stealth map from above; the clank; the near miss; the cat |
| s06 | safe | 66.0 | 14.0 | animator | the vault door; the stethoscope; the lock's gates line up; the bolts; the door swings onto gold |
| s07 | cross | 80.0 | 16.0 | animator | the gold; her deposit box (a red glint); his look; the X-split; the door slams; the dial; his red L on the plan; the alarm |
| s08 | locked | 96.0 | 12.0 | me | black; a match; the Cracker pounds; her smile; the hollow knock; the tracing paper |
| s09 | plan_b | 108.0 | 16.0 | me | the rewind to the dot (callout) and her look; the overlay: trapdoor, her route, police at his car, the ruby; down through the floor |
| s10 | checkmate | 124.0 | 12.0 | me | the Knight to the car; the city as a chessboard; four police cars close like rooks; the red ring; pull back: her line walks away; the routes cross into an X |
| s11 | end | 136.0 | 8.0 | me | the ruby in her palm; she tips the knight over; the title; the red dot; black |

## Scene by scene

Times are scene-local seconds. *Sound cues are in italics.*

### s01 TITLE (0–12)

- **0.0–1.5:** Black. Four chalk dots tick in, one per beat, at the sheet's corners.
  *Chalk tap ×4, dry.*
- **1.5–3.5:** The blueprint unrolls from a roll at the top. *Paper unrolling.* The blue
  sheet and its grid.
- **3.5–8.0:** The plan rules itself in, one group per beat, each line struck on like a
  ruler stroke. *A chalk scratch on each.* Order:
  1. the bank's outline;
  2. the vault;
  3. the corridor and intersection;
  4. the streets;
  5. the manholes;
  6. the dashed sewer, its branch visibly passing **under the vault**;
  7. the side door and alley.
- **8.0–10.0:** Two `PAPER` strips slash across the frame and cross into a big X over the
  vault (8.0, 8.5). *Whoosh-thud, whoosh-thud.* The words DOUBLE (above) and CROSS (below)
  stamp in (9.0, 9.5). *Stamps.*
- **10.0–12.0:** The letters lift away and the X shrinks onto the vault as the chalk X (11.0;
  *thud*). The camera tilts from 90° to the table angle, and the lamp's gold pool fades up on
  the paper. The cut matches into s02.

### s02 CREW (12–24)

- **12.0–13.0:** The table view (`phi ≈ 55`): the plan under the lamp's pool.
- **13.0:** Her gloved hand (`PAPER` rim) sets the white queen on manhole A. *Clack.*
  - 13.5–15.5: Her profile close-up on gold: the chignon and pencil, her eye on the plan.
- **15.5:** An old hand (`GOLD` rim) sets the gold bishop. *Clack.*
  - 16.0–18.0: The Cracker's profile: bowler, spectacles (a glint crosses the lens),
    stethoscope.
- **18.0:** A heavy hand (`RED` rim) slams the red knight down, and the other pieces jump.
  *Thud.*
  - 18.5–20.5: His profile: flat cap, the ember brightens as he draws, smoke curls.
- **20.5–24.0:** The table in elevation: three silhouettes round the plan under the swinging
  lamp. His `RED` sight line runs down to the X; her `PAPER` sight line runs across to his
  face (22.0). *A low held note: she knows.* She picks up the chalk.

### s03 PLAN (24–40)

The plan from above (`phi` 64 → 72), one continuous glide that follows her chalk. The pieces
hop along the route in file (bishop, queen, knight), landing on the beat. Hands are about one
and a half pieces tall.

- **24.0–27.6:** ① Her chalk taps a 'down here' chevron on manhole A (24.5). The route runs
  east along the sewer and north up the branch to the store-room hatch. The pieces join the
  line one by one and hop along behind the chalk.
- **27.6–29.0:** ② Through the store room to the corridor. The Cracker's old hand (gold rim,
  shirt cuff) sets a black pawn, the guard, on his post (28.5). *Clack.*
- **29.0–30.0:** She sweeps his light out from the pawn. A timing ring goes round him, with
  four ticks and a dot that runs round once per swing. The light swings 32° each way, a full
  swing every two seconds, so the crossing is dark on 30.5, 31.5, 32.5 and so on. *A low
  wooden tock at each end of the swing.*
- **29.5–32.5:** ③ The route crosses the corridor, and ④ runs north to the vault door. The
  pieces cross one per dark gap: the bishop (30.5), the queen (31.5), the knight (32.5).
- **31.0–32.1:** The bishop reaches the door. A gold lens on a leader line opens on the dial,
  which turns right, left, right (a numbered gold arrow for each turn: s06's three gates).
  *Clunk* (32.0): the door swings open. The chalk runs in to the X (32.4), and the bishop and
  the queen hop in.
- **34.2–34.75:** The Knight's own red hand snatches his piece off the route at the door and
  slams it down out on the street (34.75, *THUD*). The others jump, and the vault door on the
  plan claps shut on them. In that same instant her hand, lifting away from the vault,
  touches the sewer line under it and leaves a dot. That is the plant, hidden by the slam:
  everyone is looking at him, and the tap is buried under the thud.
- **35.5–37.3:** ⑤ She draws the way out along the street to him, a chalk car beside him, and
  a small bell on the side door (37.0, no one remarks it).
- **38.0–40.0:** The plan is done and the light settles. The camera starts to tilt down (phi
  is falling at 15°/s at the cut), and s04 carries on the move from `P.HANDOFF_34`.

### s04 NIGHT (40–52)

- **40.0–43.0:** The pop-up. The camera tilts from about 50° to eye level. The walls extrude
  from the chalk lines (`P.draw_walls_3d`), the paper darkens to `NAVY` night, the moon pops
  up, and the street lamps stand. The plan's dotted route remains as a ghost layer on the
  world.
- **43.0–46.0:** Front street. The three arrive along the curb: she stealthily, the Cracker
  creeping, the Knight heavy with empty bags. He lifts manhole A (*iron scrape, clank*), and
  they go down one per beat.
- **46.0–52.0:** The camera sinks through the road into the section. The tunnel. They move
  along the pipe while the chalk dots of the route brighten as they reach them. *Drips;
  their steps in water.* Up the rungs, and the hatch opens (*creak*). The stopwatch appears
  top right and starts at 46.0 (one tick per beat).

### s05 GUARD (52–66)

- **52.0–56.0:** The corridor in side elevation. The guard walks with his flashlight. The cone
  slides over the wall and the crew stand in an alcove, black on black, only their rims
  showing. The cone passes the alcove's edge. *The score drops to the tick.*
- **56.0–61.0:** The stealth map: the camera tilts up to top-down. The guard is the black
  pawn and his cone sweeps the intersection. The three pieces cross in the cone's shadow
  gaps, one per beat.
- **61.0–66.0:** Back in elevation. The Cracker's stethoscope swings and clanks on a pipe
  (*clank*, with a ripple). The guard spins and the cone swings at them. From a crate in the
  beam a cat leaps (two gold eyes) and a can rolls (*clatter*). The guard breathes out and
  walks on, and the crew slips through.

### s06 SAFE (66–80)

- **66.0–69.0:** The vault door fills the frame. The Cracker kneels and sets the stethoscope
  to the door.
- **69.0–76.0:** The dial in close-up, with the lock in cutaway under it: three wheels with
  their gates. The dial turns right, left, right. As each gate comes under the fence a chalk
  dot pops. *Clicks pitched low, mid, high; a ripple into his ear each time.* When the third
  gate arrives, the three dots join in a straight chalk line and the fence drops. *Clunk.*
- **76.0–80.0:** The bolts withdraw round the rim (*a rolling metallic run*). The door swings
  (the circle narrows to an ellipse) and gold light floods out over three silhouettes.
  *A brass swell.*

### s07 CROSS (80–96)

- **80.0–84.0:** Inside the vault, on gold. The Knight fills the bags with bars while the
  Cracker stacks them. She goes to the deposit wall and opens one small box. A tiny `RED`
  glint shows, she pockets it with her back to them, and no one sees.
- **84.0–86.0:** His `RED` sight line goes from the bags to the open door.
- **86.0–90.0:** The X-split. The frame is cut on both diagonals:
  - top: him lifting two full bags;
  - left: her at the box wall;
  - right: the Cracker admiring a bar;
  - bottom: the door's edge.

  He moves, and the X seams turn `RED`.
- **90.0–93.0:** He swings the door shut from outside. The ellipse widens back to a circle,
  the two inside turn too late, and BOOM: black. The dial spins in `RED` and the cutaway
  bolts shoot home (s06's diagram run backwards).
- **93.0–96.0:** The plan, top-down. His `RED` route leaves the chalk route in an L: south,
  east, then down the alley to the car. The red knight hops along it. As he passes the bell
  on the side door, the alarm sends red ripples over the plan (*alarm bell*). The stopwatch
  stops and its hand turns `RED`. *The theme, inverted.*

### s08 LOCKED (96–108)

- **96.0–98.85:** Black, and the Cracker's ragged breath. A match scratches (sparks, no
  flame), then strikes (*flare*), and gold rings of light open on her profile, calm, with the
  Cracker beyond her, leaning on the round door. He rears back, fists up.
- **98.85–99.9:** We cut on his first blow to the shot from behind him: his back and bowler,
  both fists pounding the door at head height (*three muffled BOOMs*). Each blow rings on the
  steel and shakes dust down; the camera shakes. His shadow looms over him on the door. The
  flame shivers.
- **99.9–101.35:** Her eye in close-up, steady. Her look drops to the floor as a white dotted
  sight line and the corner of her mouth lifts (*vibraphone, upright*). The camera whips down
  after the look.
- **101.35–104.0:** At floor level, the sight line lands in a chalk ring at her heel. She taps:
  a click, then a hollow knock. The floor opens top-down into a blueprint section (the slab,
  the earth, the sewer pipe) and the knock rings down through it. A gold plumb line drops from
  her heel to the chalk dot on the pipe, and a lens joins it to the dot on the plan (the vault,
  its X and the dot).
- **104.0–108.0:** The two-shot. The Cracker turns round to her (a cut-paper turn). She brings
  a roll up from her coat to her eye and lets it fall open before her face, then lifts the
  sheet toward the camera until it fills the frame, the match glowing through the paper. s09
  begins on this sheet (`S8.roll_shot(c, S8.T_END)`).

### s09 PLAN B (108–124)

- **108.0–111.0:** The rewind. Reversed snippets of s07, s06, s05, s04 and s03, about 0.4 s
  each, under chalk streaks and a double chevron, with the stopwatch spinning back. It lands
  in s03 at the plant, played forward. A callout lens snaps round the chalk dot under the
  vault. *Tape-rewind whoosh; a ting.*
- **111.0–113.0:** s02's elevation: his red look at the X and her white look at him. A
  callout on her eye.
- **113.0–118.0:** The plan with the tracing sheet sliding over it from the top. Plan B
  appears in solid chalk:
  1. the trapdoor square at the dot;
  2. her route down through it and north along the branch to manhole B, then off the sheet;
  3. four police cars round his car (`POLICE`/`RED`);
  4. a `RED` X on the ruby box, where the chalk X was on the gold.
- **118.0–124.0:** The vault by match light. She lifts a floor tile, and below is black. The
  Cracker stares, then grins. Section: they drop through to the sewer and walk north while
  the solid route lights ahead. *The theme returns upright, in the major.*

### s10 CHECKMATE (124–136)

- **124.0–127.0:** Front street at night. The Knight bursts from the alley with two heavy bags
  and heaves them into the car. The headlights flare and the engine coughs.
- **127.0–131.0:** The city from above as a chessboard: the blocks are its squares and the
  bank is in the middle. His red car moves, trailing red dots. From the four ends of the
  streets four police cars slide in like rooks, their bars turning `POLICE`/`RED`, one per
  beat, *each with a stab*. The red marker ring closes round his car: checkmate. *Sirens
  braid.*
- **131.0–136.0:** The pull-back. Manhole B lifts two blocks north and two small chalk
  figures walk away. The camera tilts to top-down and the two routes, his red and her white,
  straighten into two strokes crossing over the bank: an X.

### s11 END (136–144)

- **136.0–139.0:** Her gloved hand opens under a street lamp: the ruby, a faceted `RED` cut
  stone. It glints (*a celesta ping*), and she closes her fist.
- **139.0–142.0:** The table at dawn-dark. Her hand tips the red knight over beside the
  standing queen. *Clack, roll.*
- **142.0–144.0:** The title again, DOUBLE CROSS on the X, with the ruby as the red dot at the
  crossing. Black from 143.5.

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
- **No new paid generation.** Everything is synthesized or reused.
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
