# DOUBLE CROSS, the OPPOSITE cut

A 2:54 vertical (1080×1920, 24 fps) heist thriller. It tells DOUBLE CROSS's story (v5: the plan,
the guard, the safe, the ruby, the betrayal, the trapdoor, the police, the ruby again) in
OPPOSITE's grammar. Wordless, scored.

- **From DOUBLE CROSS:** the story, the cast, the plants and payoffs, and v5's clarity: every
  question the user asked about v4 still gets a picture of its own.
- **From OPPOSITE:** everything about how it is told:
  - the camera is an **eye**: looks are drawn, a story is told by who looks at what;
  - flat Bass **elevation and section** diagrams of one street, two buildings facing across it;
  - profile and extreme close-ups, over-the-shoulder shots that mirror each other, a split-screen
    mirror, straight-down and low angles, a Vertigo shaft, a dive into an eye, a POV;
  - jump-ins on the beat and eased push-ins; one Dutch tilt, in panic;
  - the annotation layer (sight lines, three marker rings, footstep dots, ripples, heartbeats,
    callouts, a clock);
  - AMBER lamplight on a teal NIGHT; crisp cut paper; no blur.

What this cut does **not** use (it belongs to the blueprint version): the tilting plan camera, the
pop-up world, the chessboard city and the chess pieces, BLUE paper and chalk, circled step numbers,
the heist stopwatch, punch-ins, flashes, slips, the sunburst, the X-split, whips, motion blur, the
rewind and the tracing paper.

## The story in one breath

Midnight. In a room high in a tenement, three thieves plan. She stands at the window. Across the
street is the bank: its guard's lamp low behind barred windows, an alarm bell high over its side
door, a manhole in the road. Her look goes to the guard, to the bell, to the manhole. On the table
the bank's plan lies under the lamp. Her finger traces the way in: down the manhole, along the
sewer, up a hatch into the bank's hall, past the guard, to the vault. She taps the bell on the side
door: not that way. She taps the vault twice, and a red ring closes round the gold. The Knight's
look goes to the gold and his jagged arm reaches for it. Her look goes into his eye: she knows. And
when nobody is watching her, her look slips down from the gold to the sewer line under the vault.
She pulls the lamp's cord.

Down the manhole, along the sewer, up through the hatch. They slip past the guard's sweeping
flashlight; a clank, a cat, a tin can, and the guard walks on. The Cracker opens the vault: AMBER
floods out on gold. While the men bag the bars she opens one small box, lifts out a ruby and
pockets it. No one sees.

Then the Knight double-crosses them. He shuts the vault on the other two and spins the dial. A red
ring closes round the vault. He runs for the side door, bursts out through it with the gold, and
the alarm bell she looked at rings and rings.

In the dark a match flares. The Cracker panics and pounds the door. She is calm. Far off, through
the walls, the bell: the corner of her mouth lifts. We dive into her eye, into the night before:
she is on a ladder under the vault floor, cutting a trapdoor up through it with a torch, setting
it back so it looks like a tile. Her heel taps the floor: hollow.

She lifts the tile, and they go down into the sewer the way only she knew. Above them, the Knight
throws the gold in his car; the engine coughs; the bell wakes the street, window after window.
She passes right under him. The police box him in. Every look in the street converges on him and
a red ring closes round him; he drops the gold and puts his hands up. Over his shoulder, across
the street, a manhole lifts at the tenement's curb, under the dark window where they planned: she
climbs out, looks back at him, pats her pocket, and walks away. The ruby opens on her palm.

**DOUBLE CROSS:** he crosses the crew; she had crossed him before he moved. **OPPOSITE:** the
first look of the film is hers from the window at the bank; the last is his from the bank's curb
at her window. He ends caught in the light of the street they watched; she ends in the dark under
the window where it began.

### Plants and payoffs (play fair)

| Plant | Payoff |
|---|---|
| s01: the cutaway shows the sewer running under the street and on under the bank, right under the vault. | s08 the hollow knock; s09 down through the floor into it. |
| s02: at the window her look goes to the alarm bell over the bank's side door (a lens; one damped tink, the bell's own note). | s07 he bursts out through that door and the bell rings; s09–s10 its ringing wakes the street and brings the police. |
| s03: on the plan her finger taps the bell on the side door (the damped tink): not that way. | s07 he goes that way. |
| s03: her finger taps the vault twice; the first red ring closes round the gold. | s06 the gold; s07 he takes it; s10 he drops it in the street. |
| s03: his red look goes to the gold, his jagged red arm reaches for it; in the mirror her look goes into his eye. | s07 the betrayal; s08 she is calm. |
| s03: from above, her look leaves him and slips down to the sewer line under the vault. Nobody sees it. | s08 her look drops to the floor, the night before, the knock; s09 the trapdoor. |
| s07: she opens one small box and pockets the ruby; no one sees. | s10 she pats the pocket (a red glint); s11 the ruby on her palm. |
| s02: over her shoulder, from the crew's window, the bank. | s10 over his shoulder, from the bank's curb, the tenement, and her at its curb. |
| s01: the red dot ticks in the black. | s11 the red dot is the ruby. |

## Cast

All figures are cut-paper silhouettes in profile, INK with a rim of their colour on the lit side
(`cast.py`, forked from DOUBLE CROSS into this palette). The colour is also their look's colour
and their footsteps'.

| Who | Silhouette | Colour | Motion (CMU clips in `assets/mocap`) |
|---|---|---|---|
| **The Architect** (she) | belted trench coat to the knee; hair in a low chignon with a pencil through it; gloves | `PAPER` | 17_03 stealth walk, 18_08 explaining, 13_33 ladder, 69_70 squat to the floor |
| **The Knight** (him) | broad; flat cap; heavy coat; a cigarette ember | `RED` | 17_08 heavyset walk, 70_03 carrying a heavy case, 81_05 pushing a heavy object, 80_28 smoking, 16_08 run and sudden stop |
| **The Cracker** (old) | thin and stooped; bowler hat; round spectacles; a stethoscope round his neck | `AMBER` | 77_14 careful creeping, 22_03 kneeling, 120_15 startle, 79_73 scared |
| **The Guard** | peaked cap; a flashlight | `STEEL` rim; his light `PAPER` | 77_05 looking round with a flashlight, 69_16 turning in place |
| **The cat** | a small black cat; two `AMBER` eyes | none | procedural |
| **The neighbours** | OPPOSITE's little lives (`films/opposite_full/folk.py`: a bun, curls, a bald head, a cloth cap) | `PAPER` looks | |

The police are cars and lights, never people.

## The look

### Palette (`kit.py`): OPPOSITE's

| Name | Use |
|---|---|
| `INK` | Every silhouette, building, piece of furniture. |
| `PAPER` | Cream paper: the title, the plan's sheet, eyes, her rim, her looks and footsteps. |
| `AMBER` | Lamplight and gold: lit rooms and windows, the gold's glow, the match, the Cracker's rim and looks. |
| `RED` | The Knight and what he does: his look, his footsteps, his arm, the alarm's rings, the marker rings, the ruby. Keep it small and burning. |
| `NIGHT` | The teal night: every exterior field (sky, street), the sewer's air. |
| `STEEL` | The far city, moonlit stone and iron, the guard's rim. |
| `DEEP` | A dark room at night; the earth in section is `INK`. |
| `SHUT` | An unlit window at night. |
| `POLICE` | The police light's blue half. s09's end and s10 only. |

- Nothing else: no gradients, no other hues.
- Translucency only for light (window beams, the lamp's pool, the guard's cone, the police
  sweeps, the match), as flat tints. No blur.

### Paper

- Every scene starts its `render` with `K.scene_setup(f, field)` (paper fibres, grain on twos,
  vignette): OPPOSITE's settings.
- Shapes are cut paper: `bass.cut_rect`, `bass.scissor`, `bass.ring_pts`, `K.dot`. Big circles
  need fine facets (`n=48..96`). Scissor-cut never means low-poly.

### Figures

DOUBLE CROSS's cut-outs (`C.draw`), always in profile, figures on twos (`K.twos(t)`); graphics
and camera moves run on ones. Profiles for close-ups are `faces.py` (her, the Cracker, the
Knight), forked into this palette.

### Camera

No shot is "a camera looking at a room". Each shot is a graphic composition, and the film uses a
deliberate range of angles:

- Flat Bass elevation and section diagrams of the street (`street.py`).
- Profile cameos and extreme close-ups: three faces, an eye, a dial, a stethoscope, a match, a
  ruby, a palm.
- Over-the-shoulder: hers at the crew's window in s02, looking at the bank; his at the bank's
  curb in s10, looking back at the tenement. The two shots mirror each other.
- Straight down: the plan on the table (s03), the dial (s06), the palm (s11).
- Low angle: up from the road at the manhole (s04), up both facades in the sirens (s10).
- Vertigo: the manhole shaft from above, its rungs spiralling down (s04); the spiral behind the
  Cracker's panic (s08).
- A split-screen mirror: her profile and his across a red line (s03).
- A dive into her eye (s08), into the night before.
- POV: his, through the gap of the closing vault door (s07); hers, up through a gully grating
  at his boots (s09).
- The pull-back to the whole block (s10).

Rules for camera moves:

- Moves are eased. Push-ins jump on the beat (Bass) or glide, never linear.
- **One Dutch tilt, in panic:** the Cracker's, locked in the vault (s08).
- No tilting through space. Cuts and jumps, not whips.

### Motion

- Cut paper moves crisply. No motion blur anywhere: every `motion_blur` returns 1.
- Snaps on the beat (120 bpm, beat = 0.5 s). Anticipation and settle use `outback`.
- A shake only on a blow: the Cracker's fists on the door (s08), the side door's BANG (s07).

## The annotation layer (the film's handwriting)

OPPOSITE's devices, re-exported by `kit.py` from `films/opposite_full/kit.py`. Use them where the
bible says, consistently.

| Device | `kit` call | Meaning, colour |
|---|---|---|
| **Sight line** | `K.sight_line(c, eye, target, t, t0, color, off=...)` | A look: dots fly from the eye, led by an arrowhead, then march while the look lasts. Hers `PAPER`, his `RED`, the Cracker's `AMBER`, the guard's `PAPER` (with his cone), the neighbours' `PAPER`, the police `POLICE`. |
| **Marker ring** | `K.marker_ring(c, centre, rx, ry, u, K.RED)` | "This matters." A red marker-pen loop drawn on over about 0.4 s. **Three only:** round the gold on the plan (s03), round the vault with the two locked in it (s07), round him (s10). Never for anything else. |
| **Footstep dots** | `K.step_dots(c, pts, times, t, color)` | A walk on a diagram, one dot per footfall, on the footstep sound. Hers `PAPER`, the Cracker's `AMBER`, his `RED`. |
| **Dot ring** | `bass.ring` (thin) | A small ring round a person's dot or a spot she marks (the manhole in s02). Not a marker ring. |
| **Arrow** | `K.arrow`, `bass.loop_arrow` | The dial's turns. |
| **Ripple** | `K.ripple(c, p, t, t0, color)` | A sound or a listener: the bell (`RED` when it rings for real, `PAPER` for the damped tink), the clank, the knock, the stethoscope, the engine. |
| **Heartbeat** | `K.heartbeat(c, p, t, color, bpm)` | A heart: the Cracker's (`AMBER`) past the guard and locked in; the Knight's (`RED`) boxed in. |
| **Numerals** | `K.numeral(c, "4", p, h, color)` | The dial's numbers, the clocks, floor numbers. Hand-cut figures. No other text in picture except the title. |
| **Callout** | `K.callout(c, anchor, centre, r, inside, u)` | A lens on a leader line: the bell (s02), the hatch (s04), the cat's eyes (s05), the grating (s09). |
| **Clock** | `K.clock_face(c, p, r, hh, mm)` | The crew's wall clock, 11:58 (s02); the bank's clock, 11:59 → 12:00 (s04). |
| **Golden arm** | `bass.jagged_arm` | Bass's Man with the Golden Arm: his greed, once (s03). |

## The world (`street.py`; the bank's interiors in `bank.py`)

One street, seen two ways, like OPPOSITE's:

- **ELEVATION:** the two facades on the night field, flat, the street a gap between them.
  - Left, the **tenement**: five storeys of windows; the crew's room high up (storey 4).
  - Right, the **bank**: a stone front with a cornice, a pediment and its clock; barred windows on
    the ground floor, lit low by the guard's lamp; the **side door** in its street wall and the
    **alarm bell** high over it.
  - The street: the lamp on the tenement's side, **manhole A** in the road, **manhole B** at the
    tenement's curb, the Knight's car at the bank's curb, the moon, the steel city behind.
- **SECTION:** the same street cut across like a doll's house, the diagram the heist is drawn on.
  - The tenement's rooms, stairs and neighbours; the crew's room.
  - The bank's ground floor is one **hall**: the hatch by the street wall (in the dark corner by
    the side door), the guard's desk and lamp in the middle, crates (the cat), and at the far end
    the **vault** behind its thick wall and round door: the gold stacked inside, the deposit
    boxes on the back wall, the floor tile over the trapdoor. Dark offices above.
  - Under the road and on under the bank runs the **sewer**, one tunnel the whole width: manhole
    B's shaft rises to the tenement's curb, manhole A's to the middle of the road, the hatch's
    into the hall, and its end lies right under the vault.

The routes, as the section draws them:

- **The way in** (s03 on the plan; s04–s05 for real): manhole A → down → right along the sewer →
  up the hatch into the hall's dark corner → across the hall in the dark gaps of the guard's sweep
  → the vault door.
- **His way out** (s07): the vault → across the hall → the side door, under the bell → the car.
- **Her way out** (s09): the trapdoor in the vault floor → down → left along the sewer, under the
  bank's street wall, under his car and the road → up manhole B at the tenement's curb.
- He goes up into the light; she goes down into the dark, the same way, right under him.

The interiors, close, are DOUBLE CROSS's sets forked into this palette (`bank.py`): the hall is
`corridor` (guard's post left, the vault's mouth right, crates, pipes), `vault_door`, `vault`,
`door_inside`, `sewer`, the props (sacks, bars, stethoscope, tin can, ladder poses). The crew's
room is `room.py`.

## The timeline

All scenes run back to back with hard cuts on the beat; every scene starts on a bar line. Film
time = scene start + scene time.

| id | slug | film start | length | who | what happens |
|---|---|---|---|---|---|
| s01 | title | 0.0 | 14.0 | director | the red dot; the Bass title, an X; night falls on the street; the cutaway down to the sewer and the vault's gold; the city goes to bed; push in on the crew's room |
| s02 | crew | 14.0 | 16.0 | director | the crew's room; three profiles; over her shoulder: the bank, the guard, the bell, the manhole; the plan spread on the table |
| s03 | plan | 30.0 | 18.0 | director | straight down on the plan: the way in, the bell tapped, the vault tapped, the first ring round the gold; the looks; his golden arm; the mirror; lights out |
| s04 | night | 48.0 | 14.0 | animator | the dark street; the manhole; the Vertigo shaft; the section: the sewer, the hatch, up into the hall |
| s05 | guard | 62.0 | 18.0 | animator | the hall framed close: the guard's sweep; across in the dark gaps; the clank, the cat, the can; the guard walks on; the push to the dial |
| s06 | safe | 80.0 | 14.0 | animator | the vault door; the stethoscope; the dial from straight above; the bolts; the door swings onto gold |
| s07 | cross | 94.0 | 20.0 | animator | the gold; the ruby, close; his look; the door shut on them (his POV); the red dial; the second ring round the vault; the side door bursts open and the bell rings |
| s08 | locked | 114.0 | 14.0 | director | black; a match; the Cracker's panic (the Dutch tilt), his fists on the door; the far bell, her eye, her smile; the dive into her eye: the night before; the hollow knock |
| s09 | plan_b | 128.0 | 18.0 | director | the tile lifted; his grin; down into the sewer; the section: the bell wakes the street, his engine coughs, she passes right under him (the grating), up manhole B's shaft |
| s10 | checkmate | 146.0 | 20.0 | director | sirens: the police box him in; his face; every look converges on him; the third ring; hands up; over his shoulder: she climbs out, the two looks meet, her pocket; the pull-back |
| s11 | end | 166.0 | 8.0 | director | the ruby on her palm; the windows become the title; the X again; the red dot; black |

2:54, 4,176 frames, 87 bars.

## Scene by scene

Times are scene-local seconds. *Sound cues are in italics.*

### s01 TITLE (0–14)

1. **0.00–1.00:** Black. A red dot (r ≈ 16) pops in the centre at 0.25 and ticks larger on 0.5
   and 0.75 (*tick, tick, tick*). It shrinks away by 1.0. (It is the ruby; nobody knows yet.)
2. **1.00–5.50:** The Bass title.
   - The bars race (Psycho's).
   - DOUBLE and CROSS assemble from cut letters.
   - A `PAPER` strip slashes across (2.75) and a `RED` strip crosses it (3.0): an X
     (*whoosh-thud, whoosh-thud*).
   - The halves part along the strips (3.4); the paper floods round two slabs standing in the
     dark; the letters become windows (4.2–5.0).
3. **5.50–6.50:** NIGHT FALLS. Teal bars slide over the paper; the windows snap `AMBER`; the moon
   drops in with an outback bounce; the steel city rises behind (*a low gong, a pizzicato
   descent*).
4. **6.50–9.00:** THE CUTAWAY. The slabs become the section.
   - Storey by storey from the street up, the interiors snap in (*a click per storey*): the
     tenement's rooms with their little lives, the bank's hall and dark offices.
   - Then down (8.0–9.0): the road opens, the earth, the **sewer** the width of the street and on
     under the bank, the shafts of manholes A and B; the **vault** at the bank's far end, and its
     **gold glowing `AMBER`** (*a deep cello note; a soft shimmer*).
5. **9.00–11.50:** THE CITY GOES TO BED. The lights go out one by one on the beat (*a plucked
   note each, descending*); the far city's too. Left lit: the crew's room (tenement, storey 4),
   the guard's lamp in the bank's hall, and the gold's glow in the vault, three lights in a line
   down across the street.
6. **11.50–14.00:** A push in on the crew's room, eased, about 3.2× (*a rising tremolo*). Cut.

### s02 CREW (14–30)

1. **0.0–2.0:** Wide on the crew's room (the stage, in profile; where the push ended). The
   pendant lamp over the table swings a little. The Cracker sits at the table (bowler,
   spectacles), the Knight leans by the door smoking (his ember), and she stands at the window,
   her back to the room, looking out. The wall clock reads 11:58; its minute hand ticks on the
   beat (*clock ticks; the lamp's chain*).
2. **2.0–6.5:** THE THREE, profile cameos, 1.5 s each, cut on the beat:
   - 2.0 her, on `AMBER`: the chignon and pencil, her eye to the window (looking right);
   - 3.5 the Cracker, on `STEEL`: a glint crosses his spectacles (4.25), the stethoscope;
   - 5.0 the Knight, in the dark (`DEEP`): his ember brightens as he draws (5.6), smoke curls.
   - *A pizzicato note each: hers high, the Cracker's middle, his low.*
3. **6.5–11.5:** OVER HER SHOULDER (the film's first look).
   - Her head (chignon, pencil) and shoulders, from behind, fill the left and bottom. Through
     her window: the night street below and the **bank** across it (the far elevation): the
     stone front, the pediment and clock, the barred ground-floor windows lit low by the guard's
     lamp, the side door, the **alarm bell** high over it, the Knight's car at the curb, manhole A
     in the road, the street lamp.
   - 7.0 her `PAPER` sight line flies from her eye to the lit window; inside, small, the guard
     walks past with his flashlight (*a far footstep*).
   - 8.25 her look moves up to the bell: a CALLOUT lens opens on it, the dome, the hammer
     (*one damped tink: the alarm's own note, muted*).
   - 9.5 her look drops to manhole A: a small `PAPER` dot ring round its lid.
   - 10.75 she turns from the window.
4. **11.5–16.0:** THE TABLE, from the side, under the lamp. She comes to the table and spreads the
   plan (12.0–12.75, *paper*); the Cracker leans in, the Knight comes off the wall to the table's
   end. She leans over it and begins (14.0): *her low voice, no words* (the murmur). Cut on the
   bar to straight down.

### s03 PLAN (30–48)

1. **0.0–6.0:** STRAIGHT DOWN on the table, in the lamp's `AMBER` pool.
   - The sheet is the bank's plan in `INK` lines on `PAPER`: the street and its curbs, manholes A
     and B, the sewer dashed under the road and on under the bank, the bank's walls, the side
     door with a small bell drawn on it, the hall and the guard's desk, the vault with its gold
     drawn as five bars.
   - Round the table, seen from above: the Knight's cap (left), the Cracker's bowler (top), her
     chignon (right), each with its rim; their hands on the table's edge. (Screen direction
     carries on from s02's table, where he stands at the left end and she at the right: the top
     shot looks down with the table's far side at the top.)
   - 0.5–3.5 her gloved finger traces the way in and `PAPER` dots follow it: from manhole A down,
     along the sewer, up the hatch into the hall; at the guard's desk a small `PAPER` cone swings,
     and the dots cross in its dark; on to the vault door. *The murmur; the Cracker's hum.*
   - 3.75 her finger taps the bell on the side door: it rocks, a small `PAPER` ripple (*the
     damped tink*). Not that way.
   - 4.5, 5.0 she taps the vault twice (*two taps on paper*): THE FIRST RED MARKER RING draws
     round the gold (5.0–5.4) (*a sting: a high harmonic and a marker squeak*); the gold glints.
2. **6.0–9.0:** THE LOOKS, still from above.
   - 6.0 the Knight's `RED` sight line runs from his eyes to the ringed gold and holds, marching
     (*his low note*).
   - 6.5 the Cracker's `AMBER` sight line goes to the vault door.
   - 7.25 her `PAPER` sight line goes to the Knight's face and holds; at 8.25 it leaves him and
     slips down to the sewer line under the vault, where a small ripple answers. Nobody sees her
     look (*a low held note*).
3. **9.0–12.0:** THE GOLDEN ARM. The table from the side, the three round the lamp. The Knight's
   jagged `RED` arm grows across the table to the gold on the plan (9.6–10.6), its claw closes
   over the ring, and it snaps back (11.0) (*braam*). She watches him.
4. **12.0–15.5:** THE MIRROR. A red line splits the frame: his profile on the left facing right
   (the ember), hers on the right facing left, eyes level (the faces are mirrored to keep the
   table's sides). His dots run down out of the frame
   toward the gold; hers cross the split into his eye (12.6). The halves press in on the beat
   (13.0, 13.5, 14.0, 14.5) (*the clock louder; a sustained dissonance*). She knows.
5. **15.5–18.0:** LIGHTS OUT. The room, wide: she reaches up for the lamp's cord (15.75) and pulls
   it (16.5): a snap to dark, no flash (*click*). Hold on the dark room: the window a `NIGHT`
   slot, three shapes going to the door, two small `PAPER` eyes. Cut.

### s04 NIGHT (48–62)

1. **0.0–3.0:** The elevation, the dark street. The crew's window is dark now. The bank's clock
   reads 11:59; the guard's light moves behind the barred windows. The tenement's street door
   opens without a light; three shapes slip out and cross the road to manhole A, footstep dots
   behind them: `PAPER` (her), `AMBER` (the Cracker), `RED` (the Knight) (*soft steps; the night
   air*).
2. **3.0–5.0:** LOW ANGLE from the road. The Knight levers manhole A's lid up on edge and drags it
   aside (*iron scrape, clank*). Behind them the bank's clock reaches 12:00 (*one deep chime*).
   They go down one per beat (3.5, 4.0, 4.5).
3. **5.0–7.0:** THE VERTIGO SHAFT, straight down the manhole from above: the iron rungs recede in a
   spiral; three rims sink into the dark while the shaft stretches (the dolly-zoom feeling)
   (*the shaft's echo; drips*).
4. **7.0–14.0:** THE SECTION, dark: only the guard's lamp and the gold are lit.
   - Their three dots go right along the sewer (*steps in water; drips*), under the bank's street
     wall, to the hatch.
   - 9.5–11.0 a CALLOUT lens: the Knight's hand pushes the hatch up a crack, and the hall's
     lamplight slices in (*a creak*).
   - 11.5–13.0 they climb up into the hall's dark corner by the side door, one per beat. The
     guard's `PAPER` cone sweeps the hall. Hold on them, pressed in the dark.

### s05 GUARD (62–80)

The hall, framed close (`bank.corridor` in this palette): the figures about half the frame's
height, the camera easing with the action, jump-ins on the beat.

1. **0.0–4.0:** The guard at his post; his flashlight clicks on (0.5) and its `PAPER` cone sweeps
   the hall, a full swing every 2 s. In the dark corner the crew stand pressed in file, black on
   black: only their rims, and her two `PAPER` eyes. The light's patch slides along the wall to
   the corner's edge (3.0) and falls away (*the beat ticks; a held breath*).
2. **4.0–9.5:** In the dark gaps of the sweep they cross toward the vault's mouth, one at a time
   on the beat: she (5.5), the Knight (6.5), the Cracker (7.5). The Cracker's `AMBER` heartbeat
   rings thud out (*a tiptoe pizzicato; his heart*).
3. **9.5–15.5:** THE NEAR MISS, one beat at a time:
   - the Cracker, last in, stops to get his breath (9.5); his stethoscope swings and CLANKS on a
     pipe (10.0, a ripple);
   - the guard spins round (10.25); his `PAPER` look and cone swing to the noise (10.5) and stop
     on the crates: a CALLOUT lens, two `AMBER` eyes in the dark (11.5);
   - the cat arches (12.0) and leaps down (12.5), tipping the tin can, which hits the floor
     (13.0, *clatter*) as the cat streaks between his feet;
   - he breathes out, half a laugh (13.75), lowers his light, turns away and walks off on his
     round (14.25).
4. **15.5–18.0:** The crew slip out of the mouth's dark to the vault door; the camera pushes in on
   its dial (16.0–18.0). s06 opens on the dial.

### s06 SAFE (80–94)

1. **0.0–3.0:** The vault door fills the frame (`bank.vault_door`). The Cracker kneels and sets the
   stethoscope to the steel; she holds the light; the Knight watches the way they came.
2. **3.0–4.5:** EXTREME CLOSE-UP: the stethoscope's bell on the steel; `AMBER` ripples run up the
   tube into his ear (*a soft tick*).
3. **4.5–10.0:** THE DIAL, from straight above, filling the frame: the dial and its hand-cut
   numerals. His fingers turn it right, left, right; a loop arrow shows each turn; at each gate a
   click and a ripple (*clicks pitched low, mid, high*); the fence drops (*clunk*).
4. **10.0–14.0:** The bolts withdraw round the rim (*a rolling metallic run*); he hauls on the
   wheel; the door swings (the circle narrows to an ellipse) and `AMBER` light floods out over
   three silhouettes. Three looks go in: `RED` to the gold, `AMBER` to the gold, `PAPER` to the
   deposit boxes (*a string swell*).

### s07 CROSS (94–114)

1. **0.0–6.0:** Inside the vault, in the gold's light (`bank.vault`). The Knight drops bars into a
   sack while the Cracker, kneeling, hands them over; behind them she goes to the deposit wall
   and opens one small box (0.35–1.5).
   - **1.5–4.0, THE RUBY, extreme close-up:** a ruby on a dark cushion, glowing red; it glints.
     Her gloved hand comes in (2.0), finger and thumb close on it (2.5–2.7), she lifts it into
     the light (2.7–3.3), where it flares (3.0), and her hand takes it away (3.65–4.0) (*a glove's
     creak; a soft rising string harmonic; a glassy shimmer on the flare*).
   - 4.0–4.6 back on her: she slips it into her coat pocket, her back to them. No one sees.
2. **6.0–9.0:** HIS LOOK. He pulls the second sack shut; his `RED` sight line goes to the two full
   sacks (6.4), then to the open door (7.1), then to the two of them, their backs turned (7.6)
   (*his low note; a cello pedal*).
3. **9.0–11.5:** He heaves up both sacks (9.2, *his grunt*) and steps out through the door.
4. **11.5–14.0:** HIS POV through the closing door. Outside, he drives the great door shut with a
   lunge (*his grunt, held*): through the narrowing gap the two inside turn round, too late; the
   gap narrows to a slot of gold and closes. **BOOM on the bar line (14.0):** black.
5. **14.0–15.0:** The dial, close, in `RED`: his gloved hand spins it, the lock run backwards (*a
   spin; clicks*).
6. **15.0–17.0:** THE SECTION. THE SECOND RED MARKER RING closes round the vault with two tiny
   figures in it (15.3) (*the squeak; a low stab*). His `RED` footstep dots run from the vault
   door across the hall to the side door (15.5–16.75), the sacks swinging.
7. **17.0–20.0:** THE ALARM. The side door from the street: it bursts open (17.0, *BANG*; the
   frame shakes once) and the Knight charges out with the two sacks; over the door the alarm
   bell rings and rings, `RED` ripples on every beat (*the bell, loud*); he runs for the car, and
   the camera pushes in on the bell (17.7–20.0).

### s08 LOCKED (114–128)

1. **0.0–2.0:** Black, and the Cracker's ragged breath. A match scratches (sparks, 1.2) and strikes
   (1.6, *flare*): `AMBER` rings of light open on her profile, calm, with the Cracker beyond her by
   the door.
2. **2.0–6.0:** THE CRACKER'S PANIC (OPPOSITE's horror beat).
   - His profile, eyes wide; `AMBER` heartbeat rings thud out of his chest, faster and faster.
   - Behind him the field turns into a slow Vertigo spiral (`bass.spiral`) that zooms while he
     stays still. The frame tilts to −7°: the film's one Dutch tilt (*heartbeat; a high held
     string*).
   - He turns and pounds the door. From behind, against the round steel door's inside face (its
     bolt work spoked out from the hub), his fists strike: left (3.5), right (4.0), both (4.5),
     each ringing out across the steel in `AMBER` ripples and shaking the frame, his shadow,
     thrown up onto the door by her match, pounding with him (*three muffled BOOMs*). Then he
     sags, his fists sliding down the steel.
3. **6.0–8.0:** Far off, through the walls, the alarm bell: faint `RED` ripples come through the
   vault's wall. HER EYE in extreme close-up, level and steady, the match flame in her iris. The
   corner of her mouth lifts (6.9) (*the faint bell; her breath of a laugh*).
4. **8.0–8.5:** THE DIVE into her eye: the flame in her iris grows, a Vertigo spiral round it (*a
   deep whoosh*).
5. **8.5–12.0:** THE NIGHT BEFORE (in her eye; the colours of the section): the vault floor in
   section and the shaft under it. She is on a ladder under the slab. Her torch cuts up through
   it, two cuts in a shower of sparks (9.0–9.6, 9.75–10.35). She pushes the cut block up a crack
   (10.5–10.9) and gold light falls on her; she sets it back (11.2–11.5): from above it is only a
   floor tile (*the torch's roar and hiss; stone grinding; a shimmer on the gold*). Out of the eye
   (11.75–12.0, *a reverse whoosh*).
6. **12.0–14.0:** Back in the vault: her `PAPER` look drops to the floor at her heel (12.1); she
   taps: a click, then a HOLLOW KNOCK (12.75); ripples ring down through the floor; the Cracker
   turns to her (13.25). Cut.

### s09 PLAN B (128–146)

1. **0.0–2.0:** From straight above, by the Cracker's match: the vault's floor tiles, the top of
   her head at the foot of the frame, her arms up to the cut block. She lifts it toward us
   (0.2–0.5), its shadow sliding off it, and lays it aside off to the left (0.5–0.9): below is
   black, the shaft's top rungs going down, and far below a glint of the match on the water. His
   hand brings the match in over the hole (1.4) (*stone grinding; the block set down; a breath of
   cold air*).
2. **2.0–3.0:** The Cracker's face lit from below by the match he holds low: the light crosses his
   spectacles (2.1, *a glassy tick*), and he grins (2.4, *a dry chuckle*).
3. **3.0–7.0:** THE SECTION, close: the vault's floor with the hole in it, the block laid aside, the
   shaft, its iron ladder, the sewer and its water, lit only by his match. She is on the top rung;
   she slides down the ladder into the dark (3.2–4.2) and splashes into the sewer (4.2), her two
   eyes in the dark. He steps down into the hole and follows, sliding one-handed with the match
   held up (4.5–5.6, *splash*). She turns left, toward the street, and they wade off (5.8, 6.0)
   (*splashes, drips, the shaft's echo*). The camera follows them down and left.
4. **7.0–18.0:** THE STREET IN SECTION, wide (OPPOSITE's mirrored race).
   - Above, from 7.0: the alarm bell rings over the side door, its `RED` ripples rolling out over
     the street on every beat. The Knight, by his car at the bank's curb, flings the sacks in
     over its flank (7.3), slams the door (7.6, *the slam*) and ducks in; the engine coughs and
     dies (8.0, 8.5, 9.1, 9.7).
   - The street wakes: the tenement's windows light up `AMBER` storey by storey (9.5, 10.0,
     10.5, 11.0) with heads at the glass, their light thrown across the street; then the city's
     windows (11.5) (*a plucked note per window*).
   - Below: her `PAPER` and the Cracker's `AMBER` footstep dots go left along the sewer, under the
     bank's street wall, toward the street, the match's small pool of light going with them.
   - **10.2–12.0, the near miss:** his door is flung open (10.2) and he is out again, on the gully's
     grating by the tyre: he looks round at the bank, at the lit windows, and kicks the tyre
     (11.3, *a thud; his grunt*). She has stopped right under him (10.8): her `PAPER` look goes up
     the gully's shaft, and a CALLOUT lens (11.0–12.55) shows her view up through the bars: his
     boots on them, red at the edges, one swinging at the tyre; the car's flank and its tail light
     pulsing. He gets back in (11.6–11.9, *the door, right overhead*) and the engine catches (12.0,
     *a roar over their heads*): exhaust drifts over the bars, a drip falls at her.
   - 12.6–16.3 they go on under the road, under manhole A, to manhole B by the tenement's curb
     (the camera pushes in); he shakes the match out (14.95); they climb its shaft, she first, and
     she stops under the lid.
   - 16.0–18.0 `RED` and `POLICE` light begins to sweep the street from both ends as the camera
     pulls back to the whole section (*the first siren, far*). Cut.

### s10 CHECKMATE (146–166)

1. **0.0–3.0:** SIRENS. OPPOSITE's worm's-eye construction on the night field: the tenement and
   the bank lean in over the road, the moon low between them, the bank's bell rocking `RED` over
   its side door. His car lurches off the curb (0.3) and headlights swing in dead ahead: a police
   car, nose to nose (0.8) (*brakes; a siren whoop*); a second slides in behind, its bar over the
   frame's foot (1.15–1.5). The light bars sweep `RED` and `POLICE` across the walls (*sirens
   rising, braiding*).
2. **3.0–5.0:** His face in the car's side window, washed red and blue by turns (the strobe swaps
   the rims), his eyes darting (3.2–4.6), one nervous drag on the cigarette (4.35); `RED`
   heartbeat rings off his chest (*a heartbeat, the sirens muffled by the glass*).
3. **5.0–10.0:** THE WEB, on the section, wide. The windows are already lit (s09's waking).
   - From each neighbour at a lit window (storeys 5, 3, 2: 5.25, 5.75, 6.25), then from the city's
     lit windows (6.75–7.25), a `PAPER` sight line flies to HIM in his car: a converging web
     (*her theme plucked, one note per look*). One `POLICE` look from the first car's bar (8.0).
   - Down manhole B's shaft, under the road, she and the Cracker wait on the ladder; her small
     `PAPER` eye blinks (7.3). No line goes to her.
   - 9.0: THE THIRD RED MARKER RING closes round him (*swell; the squeak; a stab*).
4. **10.0–13.0:** THE ARREST, the bank's front face on, the police cars boxing his car nose and
   tail. He shoves the door open (10.3), climbs out with a sack (10.5–11.0), looks at one car
   (11.2) and the other (11.5) (`RED` lines), and lets it go: it thumps down and the gold spills on
   the road (11.75–11.9). He turns into the headlights and puts both hands up in a V (12.1–12.5)
   while the camera glides in, the bell still ringing over the side door (*the door; boots; the
   sack's thump and the gold; a held low string note*).
5. **13.0–17.0:** OVER HIS SHOULDER, the mirror of hers in s02.
   - His cap and head from behind at the right of the frame, both hands up by his head, open
     (four fingers and a thumb each), rimmed `PAPER` on one side and strobing `RED`/`POLICE` on
     the other. Across the street: the tenement, the crew's dark windows on storey 4, the
     neighbours lit; at its curb, manhole B's lid grinds off (13.4); she climbs out (13.7), and the
     Cracker after her (14.1).
   - 14.5 her `PAPER` look flies to him and lands on the back of his head; 14.9 his `RED` look to
     her; the two lines meet (15.2: a `PAPER` ripple and a `RED` one) (*her high note and his low
     one, a semitone apart, in a chime*).
   - She pats her coat pocket twice (15.8–16.1): a `RED` glint. She turns away (16.3; her line
     goes out, his follows her), the Cracker after her (16.45).
6. **17.0–20.0:** THE PULL BACK, face on to the block from up the street (17.4–19.8): the tenement,
   the houses either side with every window lit, the far city behind. Every watcher's `PAPER`
   line goes to his small figure, hands up behind his car at the near curb between the two
   police cars (their `POLICE` lines too), the third ring held round him. She and the Cracker
   walk off left along the far curb, under the lamp and out of its light into the dark (19–20)
   (*the theme upright, in the major; their heels fading with the light*). Storey 1's shop
   windows stay dark in the face-on views.

### s11 END (166–174)

1. **0.0–2.5:** From straight above: her gloved fist under the street lamp, over the pavement
   (the kerb along the frame's diagonal, a puddle holding the lamp). The fingers open one after
   another, the index first, red light escaping: the ruby on her palm (0.4–1.2) (*the glove
   creaks*). At 1.5 it glints, an X of light along the frame's diagonals (*the one celesta
   ping*). At 2.2 she closes her hand on it; the red leaks between her fingers and dies by the
   cut (*the glove creaks*).
2. **2.5–5.0:** The street's elevation as the title left it: the street awake now, his car gone,
   the bank's side door open, its clock at 12:25. The windows the letters became snap back to
   paper, turn back into their letters and fly up into the title, DOUBLE over CROSS, paper on
   black, the reverse of the opening (2.52–3.25), while black slides over the street (2.78–3.1)
   (*a rising run of plucks; the title stamp at 3.25*). The `PAPER` strip and the `RED` strip
   cross over it again, an X (3.5, 3.75, *whoosh-thud ×2*). On the last chord (4.0) the title is
   cut along the red strip and the halves slide apart along it and away, DOUBLE up and right,
   CROSS down and left (4.0–4.95); the red strip draws in to the centre (4.55–5.0).
3. **5.0–8.0:** Black. The red strip pops as the red dot in the centre (5.0) and it beats twice
   like a heart (5.45, 6.05: the ruby); it is gone by 7.0. Silence from 7.5.

## Sound plan (for the mix)

- **Score: OPPOSITE's language, DOUBLE CROSS's key.** Herrmann strings at 120 bpm (bowed
  ostinato, pizzicato, tremolo, braams, chords; the instruments of `films/opposite_bass/audio/mix.py`
  and `films/opposite_full/audio/mix.py`), in **D minor on the Psycho chord** (D F A C#: minor
  with a major seventh).
  - **Two notes for two people**, as in OPPOSITE: hers is D, high; his is C#, low, the chord's
    major seventh, a semitone (and octaves) under her.
  - **THE THEME** (her plan, four bars) is heard plucked in s02–s03. At the betrayal (s07) it
    returns in **mirror inversion**, low and dark. In s08–s09, from the dive into her eye, the
    inversion is inverted again: upright. In s10 it resolves into **D major**.
  - s01 as OPPOSITE's title (soft dot notes, the title, a low gong, a pizzicato descent, a click
    per storey, a note per light going out, the tremolo into the room).
  - s02–s03: the wall clock ticks on the beat; the murmur sits low under the theme; the sting on
    the first ring; his low note under his look; a braam under the arm; a sustained dissonance in
    the mirror; the click and silence at the lights.
  - s04–s06: sparse: steps, the iron, the shaft's echo, drips; a tiptoe pizzicato past the
    guard; the Cracker's heart; the clank, the can; the dial's clicks; a swell onto the gold.
  - s07: the ruby's harmonic and shimmer; his low note; the theme inverted; the grunts; the BOOM;
    the red dial; the squeak and stab on the ring; BANG and the bell, loud.
  - s08: breath, the match, the Cracker's heart and the Dutch-tilt string, the three BOOMs; the
    far bell; her breath of a laugh; a deep whoosh into the eye; the torch; a reverse whoosh;
    the knock.
  - s09: stone, his chuckle, splashes, drips; the bell rolling out, the engine coughing; a plucked
    note per waking window; the engine over their heads at the grating; the first siren.
  - s10: brakes, sirens braiding; his heartbeat; her theme plucked one note per window; the ring;
    the sack and the gold; her high D and his low C# in a chime as the looks meet; the theme
    upright in D major on the pull-back.
  - s11: **the one celesta ping** on the ruby's glint (the celesta is reserved for it: nothing
    else in the film uses a celesta); the stamp; the last chord, D major with the major seventh;
    the dot's two heartbeats; silence.
- **Foley:** DOUBLE CROSS's synthesised sounds (`films/double_cross/audio/mix.py`: the manhole,
  drips and water steps, the hatch, the flashlight click, the stethoscope clank, the cat and the
  can, dial clicks, the fence, the bolt run, the vault door's groan and BOOM, gold clinks, the
  alarm bell and its damped tink, the match, the hollow knock, the torch, the car's engine and
  door, sirens) and OPPOSITE's recordings (`films/opposite/audio/gen`: breaths, gasps, steps).
- **Voices:** only the takes already made for DOUBLE CROSS (`films/double_cross/audio/gen`): the
  briefing's murmur (never heard as words), the Knight's grunts, her breath of a laugh. **No new
  paid generation.**
- **Mix:** −16 LUFS integrated, true-peak ceiling −1.3 dBTP, digital silence from s11 7.5 to the
  end.

## Technical

- **Package:** `films/double_cross_opposite/` (`--film double_cross_opposite`).
- **Scene files:** `scenes/sNN_slug.py` with:
  - `render(f, t, T)`, which calls `K.scene_setup(f, field)` first and then draws inside
    `with f.screen() as c:`;
  - `cues(T)`, a list of `engine.timing.Cue`;
  - `motion_blur(t, T)`, which returns 1;
  - beat constants at module level (`T_BOOM = 14.0`, and so on).
- **Imports:**
  - `from films.double_cross_opposite import kit as K` (palette, annotation layer, devices);
  - `from films.double_cross_opposite import street as St` (the street: elevation, section);
  - `from films.double_cross_opposite import bank as Bk` (the interiors, props);
  - `from films.double_cross_opposite import cast as C`, `faces as F`, `room as R`.
- **Stills:** `RENDER_WORKERS=1 python3 -m engine.render --film double_cross_opposite sNN --times=1.0,2.5 --scale 1.0`
  (outputs in `films/double_cross_opposite/qa/sNN/`).
- **Contact sheet:** `RENDER_WORKERS=1 python3 -m engine.render --film double_cross_opposite sNN --sheet 12 --window 2:6 --scale 0.25`.
- **Budget:** at most 1.5 s per full-size frame. Deterministic: no unseeded random.
- **Text:** no text in picture except the title and hand-cut numerals.
- **Self-review:** look at frames at full size. Check hands, edges, seams, popping, readability at
  phone size, and that every beat reads in one glance without the sound.
