# OPPOSITE — the full Bass cut

A 2:24 vertical (1080×1920, 24 fps) thriller told in Saul Bass's graphic language. It extends
the 36-second Bass cut (`films/opposite_bass`) into the whole story. Wordless, scored.

## The story in one breath

At a quarter to midnight a woman makes tea and stands at her window. Across the street, one
floor up, a couple quarrel. A red ring circles the knife on their counter. He uses it.
She drops her mug, and he turns and sees her. His look crosses the street, and the same red
ring now circles her window. She kills her light.

He comes down his stairs and across the street. She climbs out onto her fire escape. He
passes right under her, goes in, and climbs her stairs. Meanwhile she crosses the street
and climbs HIS. He reaches her door, she reaches his room. The woman on his floor is alive:
her hand closes on hers. She dials 9-1-1 on his telephone.

He breaks in, finds her room empty and goes to her open window. Across the street, in his
own lit window, she stands with his telephone at her ear, looking back at him. Sirens.
Window after window lights up, and every look in the city converges on him. The red ring
closes round HIM.

**OPPOSITE:** the watcher becomes the watched; the hunter ends framed in the window he was
watching; she ends where he began.

## The look

### Palette (`films/opposite_full/kit.py`)

| Name | Use |
|---|---|
| `INK` | Every silhouette, building, piece of furniture. |
| `PAPER` | Cream paper: titles, eyes, her marks. |
| `AMBER` | Lamplight: lit rooms and windows, her close-ups' field. |
| `RED` | Him and what he does: his marks, his path, the knife's cuts, blood. Keep it small and burning. |
| `NIGHT` | The teal night: every exterior field (sky, street). |
| `STEEL` | The far city, moonlit distance. |
| `DEEP` | A dark room at night. |
| `SHUT` | An unlit window at night. |
| `POLICE` | The police light's blue half. Used in s10 only. |

- Nothing else: no gradients, no other hues.
- Translucency is allowed only for light (window beams, the lamp's cone, police sweeps), as flat
  tints. No blur.

### Paper

- Every scene starts its `render` with `K.scene_setup(f)` (paper, grain on twos, vignette).
- Shapes are cut paper: `bass.cut_rect`, `bass.scissor`, `bass.ring_pts`, `K.dot`, and so on.
- Big circles need fine facets: `n=48..96` (the keyhole lesson). Scissor-cut must never mean
  low-poly.

### Figures

Use the Bass cut's paperdoll cut-outs (`B.figs()` → her, him, the victim) and its motion-capture
performances.

- **Her:** a bob and a slim dress.
- **Him:** a hat and a long coat.
- **The victim:** long hair down her back and a full skirt.

They are always in profile, drawn with `B.draw_cutout(...)`. Figures move on twos
(`K.twos(t)`); graphics and camera moves run on ones.

### Camera

No shot is a "camera looking at a room". Each shot is a graphic composition, and the film
uses a deliberate range of angles:

- Flat Bass elevation and section diagrams.
- Profile close-ups and extreme close-ups (an eye, a dial, a chain, two hands).
- Over-the-shoulder: hers in s02, and his mirroring it in s10.
- A straight-down high angle (s06).
- A low angle up the fire escape (s06).
- Vertigo's stairwell, seen from above (s07).
- A split-screen mirror (s05).
- POV through a keyhole (s08).
- A pull-back to the whole street (s10).

Rules for camera moves:

- Moves are eased. Push-ins jump on the beat (Bass) or glide, never linear.
- A Dutch tilt only in panic (s04).

### Motion

- Cut paper moves crisply. No motion blur.
- Snaps on the beat (120 bpm, beat = 0.5 s).
- Anticipation and settle use `outback`.

## The annotation layer (the film's handwriting)

The film marks up its own story like a detective's photograph. These devices are the
signature of the full version. Use them where the bible says, consistently.

| Device | `kit` call | Meaning, colour |
|---|---|---|
| **Sight line** | `K.sight_line(c, eye, target, t, t0, color, off=...)` | A look. Dots fly from the eye to what it sees, led by an arrowhead, then march while the look lasts. Hers is `PAPER`, his `RED`, the neighbours' `PAPER`, the police `POLICE`. |
| **Marker ring** | `K.marker_ring(c, centre, rx, ry, u, RED)` | "This matters." A red marker-pen loop drawn on over about 0.4 s. It circles the knife (s03), then her window (s05), then him (s10). Three rings only. Never use it for anything else. |
| **Footstep dots** | `K.step_dots(c, pts, times, t, color, line=(w, color))` | A walk on a diagram: one dot per footfall, on the footstep sound. His are `RED`, hers `PAPER`. |
| **Arrow** | `K.arrow`, `bass.loop_arrow` | Direction of a movement: the dial turning, a route. |
| **Ripple** | `K.ripple(c, p, t, t0, color)` | A sound or a listener: he listens, the phone rings. |
| **Heartbeat** | `K.heartbeat(c, p, t, color, bpm)` | Her heart. |
| **Numerals** | `K.numeral(c, "4", p, h, color)` | Floor numbers, the dial. Hand-cut figures. No other text in picture except the title. |
| **Callout** | `K.callout(c, anchor, centre, r, inside, u)` | A lens on a leader line that magnifies a detail of a diagram. |
| **Clock** | `K.clock_face(c, p, r, hh, mm)` | Her wall clock: 11:46 → 11:48. |

## The street

- **Elevation** (`K.draw_elevation(c, tb)`): the Bass cut's two slabs on the night field.
  - Her window is low on the left building.
  - His window is high on the right building.
  - The figures in the windows come from the Bass cut at Bass time `tb`.
- **Section** (`K.draw_section(c, t, ...)`): the same two buildings cut open.
  - **Hers** (`K.HER_B`): on the left, 5 storeys. Her room is storey 4, `K.her_room()`. Its window
    is in the right wall, facing the street.
  - **His** (`K.HIS_B`): on the right, 6 storeys. His room is storey 5, `K.his_room()`, one
    floor higher, so her looks go up and his come down.
  - **Stairs:** each stairwell runs up the side away from the street. `b.stair_route(n0, n1)`
    gives the footstep path.
  - **Doors:** the street doors are at ground level in the street walls.
  - **Fire escape:** her fire escape hangs over the sidewalk under her windows.
    `K.escape_route()` gives its path; `ladder=` drops the ladder.
  - **Street furniture:** a street lamp stands on his side. The moon is over the gap.

### Her room (side stage)

The section's room seen close, in profile. Agent A builds it in `films/opposite_full/rooms.py`
and everyone reuses it.

- **Layout:** door on the left wall (to the stair landing), window on the right wall (to the
  street).
- **Furniture, left to right:** the stove with the kettle, the small table with the rotary
  phone, a pendant lamp hanging from the ceiling with a pull cord near the window, the wall
  clock on the back wall, a curtain on a rod inside the window.
- **Lighting:** lit, the room is `AMBER` with `INK` furniture. Dark, it is `DEEP`, the window a
  `NIGHT` slot, edges caught in cold light.
- **Floor:** the stage floor line is at y = 1560, the same line as the Bass cut's room shot.

### His room

The Bass cut's room shot (`B.draw_room`): an amber stage, the floor at y = 1560, the
figures at `B.ROOM_FS`. The full version adds:

- **The counter** (right of the victim), where the knife lies.
- **A chair** (overturned after the killing).
- **A small table with his telephone** (used in s09).

Agent B owns it.

## The timeline

All scenes run back to back with hard cuts on the beat. Film time = scene start + scene
time. Each scene module defines its beats as module-level constants (`T_RING = 3.5`, and so
on) and exports `cues(T)` (`engine.timing.Cue`) for the sound. The mix imports the scene
modules and places sounds at `start + constant`.

| id | slug | film start | length | what happens |
|---|---|---|---|---|
| s01 | title | 0.0 | 12.0 | the red dot; the Bass title; night falls; the cutaway; the city goes to bed; push in on her room |
| s02 | amber | 12.0 | 14.0 | kettle, pour, to the window, the sip, over her shoulder: her look across |
| s03 | quarrel | 26.0 | 14.0 | along her look into his window; the quarrel; the knife ringed; her eye; his hand takes the knife |
| s04 | knife | 40.0 | 12.0 | the Psycho cuts; the mug; her heart and vertigo; the silent street |
| s05 | seen | 52.0 | 14.0 | he turns; his eye; his look crosses the street and rings her window; the mirror; the arm; lights off |
| s06 | dark | 66.0 | 10.0 | her in the dark; straight down: he crosses toward her; the chain; out of the window |
| s07 | crossing | 76.0 | 14.0 | the section diagram: the near miss under her fire escape; the mirrored race up two stairwells |
| s08 | door | 90.0 | 14.0 | her door from inside: shadow, feet, the handle twice; the keyhole; his eye; his view: an empty room |
| s09 | call | 104.0 | 12.0 | his room: she finds the victim alive; the dial: 9-1-1; it rings |
| s10 | opposite | 116.0 | 20.0 | the door bursts; the empty room; over his shoulder: she is in his window; sirens; the neighbours' looks converge; the ring on him; pull back |
| s11 | end | 136.0 | 8.0 | the windows become the title; the red cut; the red dot; black |

### Reusing the Bass cut

Bass-cut shots are pure functions of Bass time `tb`. Call them with `tb = <Bass beat> +
(t - <your local start>)`. Bass beats are in `films/opposite_bass/world.py` (B):

- title 0.0–5.0
- sip 5.6–7.0
- her eye 8.5–11.0
- room 11.0–14.0
- knife 14.0–16.5
- mug 16.5–18.5
- arm 18.5–21.5
- off 21.5–22.5
- door 28.5–31.5
- keyhole 31.5–33.4
- end 33.4–35.0

**Exteriors must be on the night field.** The Bass cut's street shots fill PAPER. Port them:
copy the shot function into your scene and draw the street with `K.draw_elevation(c, tb)`.

**If a Bass shot needs new beats or a longer hold, copy it and re-time it.** Never edit
`films/opposite_bass/` (the Bass cut is finished).

## Scene by scene

Times are scene-local seconds. Sound cues in *italics*.

### s01 TITLE (0–12)

1. **0.00–1.00:** Black. A red dot (r ≈ 16) pops in the centre at 0.25 and ticks larger on 0.5
   and 0.75 (*tick, tick, tick*). It shrinks away by 1.0.
2. **1.00–5.40:** The Bass title at `tb = t - 1.0`:
   - the bars race;
   - OPPOSITE assembles;
   - the red cut at 3.0 (*whip*);
   - the halves part;
   - the paper floods;
   - the letters become windows.
3. **5.40–6.40:** NIGHT FALLS. Teal bars slide over the paper field. The two lit windows
   snap amber. The moon drops in with an outback bounce. The steel city rises behind
   (*a low gong, a pizz descent*).
4. **6.40–8.40:** THE CUTAWAY. The slabs become the section buildings. Storey by storey
   from the bottom, the interiors snap in: floors, stairs, rooms (*a click per storey*).
5. **8.40–10.40:** THE CITY GOES TO BED.
   - Many rooms are lit, with little lives in them.
   - Floor numbers pop beside the buildings.
   - The lights go out one by one on the beat (*a plucked note each, descending*).
   - Only hers (storey 4) and his (storey 5) stay lit. Their numerals turn PAPER (4) and
     RED (5). Their window beams cross the street.
6. **10.40–12.00:** A push in on her room, about 3.2×, eased (*a rising tremolo*). Cut.

### s02 AMBER (12–26)

1. **0.0–3.0:** Wide on her room, lit (it continues the push).
   - The kettle on the stove steams; she stands at it.
   - The wall clock reads 11:46, and the minute hand ticks on the beat (*clock ticks*).
   - At 2.0 she lifts the kettle (*whistle* 0.3–2.0).
2. **3.0–5.0:** Close on the pour. The spout tips over her mug. An INK stream falls; steam
   rises (*pouring*).
3. **5.0–8.0:** Wide. She walks to the window with the mug and stops at the glass (mocap
   137_26, *her steps*). She looks up and across.
4. **8.0–10.0:** The sip, the Bass sip close-up at `tb = 5.6 + (t - 8.0)`, then held until
   10.0 (*the sip*).
5. **10.0–14.0:** OVER HER SHOULDER.
   - Her bob and shoulders, from behind, fill the left and bottom of the frame.
   - Through her window frame: the night street, his building, his lit window one floor up,
     the couple small in it.
   - At 10.6 her PAPER sight line flies from her head to his window, then marches.
   - At 12.6 the first red zigzag of shouting jumps out of his window (*a muffled shout*).

### s03 QUARREL (26–40)

1. **0.0–1.5:** ALONG HER LOOK. We fly along her dotted line. The dots rush past, huge, and
   his amber window grows to fill the frame (*whoosh*).
2. **1.5–8.0:** THE QUARREL, the Bass room look extended.
   - The Anatomy-of-a-Murder cut-outs argue (mocap 80_48 for both).
   - Red zigzags fly mouth to face on the quarrel's onsets.
   - The frame jumps closer on the beat.
   - NEW: the counter at the right with the knife on it (a PAPER blade, an INK handle).
     - 3.5: the RED MARKER RING draws round the knife (*a sting: a high harmonic and a marker
       squeak*).
     - 5.5: his RED sight line to the knife, held for 1 s.
     - 6.5: she slaps him (a PAPER starburst at his cheek, his head snaps) (*slap*). She
       turns her back on him.
3. **8.0–10.0:** HER EYE, the Bass eye shot at `tb = 8.5 + (t - 8.0)`: his window reflected in
   her iris, the ring visible in the reflection (*tremolo*).
4. **10.0–14.0:** THE KNIFE INSERT. A low angle along the counter top.
   - The knife lies huge in the foreground in its red ring. Beyond it, small, her back, and
     him behind her.
   - 11.5: his hand comes into frame and closes on the handle.
   - 12.2: the knife lifts out of the ring. The ring snaps open and its two arcs fall away
     (*scrape, low thud*).
   - 13.0: the empty counter. Cut.

### s04 KNIFE (40–52)

1. **0.0–2.5:** The Bass knife shot at `tb = 14.0 + t`: the raise, three stabs, the Psycho tears,
   she falls through the floor, the bars close (*shrieks, scream, impacts*).
2. **2.5–4.5:** The Bass mug shot at `tb = 16.5 + (t - 2.5)` (*gasp, smash*).
3. **4.5–9.0:** HER HORROR. Her profile, hand over her mouth.
   - Red heartbeat rings thud out of her chest, the bpm rising from 90 to 140.
   - Behind her the amber field turns into a slow Vertigo spiral (`bass.spiral`), which
     zooms while she stays still: the dolly-zoom feeling.
   - The frame tilts to −7° (Dutch). Her hand trembles on twos (*heartbeat, a high held
     string*).
4. **9.0–12.0:** THE SILENT STREET.
   - The night elevation: her window lit, her hand at her mouth.
   - His window lit: he stands alone, his back to the street.
   - The camera eases toward his window (*silence, his breath*).

### s05 SEEN (52–66)

1. **0.0–2.0:** His window, closer. He turns (on twos) to face the street (*a low string swell*).
2. **2.0–3.5:** His eye, an extreme close-up in the style of the Bass cut's `draw_his_eye`
   (red iris). It opens on her; the pupil snaps small (*stinger*).
3. **3.5–5.5:** THE LOOK.
   - On the wide night elevation, his RED sight line zips from his window to hers in 0.3 s.
   - The RED MARKER RING draws round her window in 0.4 s (*zip; marker squeak; a low brass
     braam*).
4. **5.5–8.0:** THE MIRROR.
   - The frame splits down a red line.
   - Left: her profile, facing right, eye wide, hand at her mouth (`B.draw_her_profile`).
   - Right: his profile, facing left: hat brim, a red-irised eye.
   - Their eyes are level; his red dots cross the split into her eye.
   - The halves press in (*heartbeat, a sustained dissonance*).
5. **8.0–11.0:** THE ARM: the Bass arm shot at `tb = 18.5 + (t - 8.0)`, ported to the night field.
   His jagged arm grows across the street to her window and snaps back (*braam*).
6. **11.0–14.0:** LIGHTS OFF: the Bass off shot at `tb = 21.5 + (t - 11.0)`, on the night field.
   - The cord; the negative flash; dark (*click*).
   - Hold on the dark street.
   - The red ring round her dark window is the brightest thing left, and it throbs with her
     heart.

### s06 DARK (66–76)

1. **0.0–2.0:** Her dark room, from the floor.
   - The window is a NIGHT slot.
   - Her silhouette rises to peek over the sill, an INK shape against the teal.
   - Two small PAPER eyes (*her breath*).
2. **2.0–5.0:** STRAIGHT DOWN (her view from the 4th floor).
   - The street from above: the lamp's AMBER pool, the curbs.
   - His door opens and throws a slab of light. He steps out: a top-down silhouette, hat
     brim and shoulders.
   - He crosses toward her building, RED footstep dots behind him.
   - Under the lamp he stops and looks up: two tiny red glints (*his steps on the street*).
3. **5.0–6.5:** THE CHAIN, close. Her hand slides the door chain (a line of links) into its
   slot, trembling (*chain*).
4. **6.5–10.0:** THE WINDOW.
   - She lifts the sash (mocap 56_03, lift open window) and climbs out.
   - Then a LOW ANGLE from the street: the fire escape zig-zags in silhouette against the
     night and the moon, and her silhouette steps out onto the platform (*sash, iron creak,
     wind*).

### s07 CROSSING (76–90)

The section diagram, dark. Only his room is lit: the victim on the floor, tiny. A dim bulb
dot hangs at each stair landing.

1. **0.0–2.0:**
   - Her PAPER dots go down the fire escape from storey 4 to storey 2.
   - His RED dots come across the street to her street door.
2. **2.0–4.0:** THE NEAR MISS.
   - He stands at her door, right under her platform. Both stop.
   - PAPER ripples spread from him: he listens. Her dot trembles.
   - A CALLOUT lens shows the detail: her shoes on the iron grating, and through it, below,
     the top of his hat (*silence, one held breath, a heartbeat; a far car horn releases it*).
3. **4.0–4.5:** He goes in.
4. **4.5–12.0:** THE MIRRORED RACE.
   - His RED dots climb her stairs. Her building's floor numbers turn RED as he passes.
   - Her ladder drops. Her PAPER dots go down to the street and across it, crossing his old
     red path in an X (OPPOSITE), through his open street door and up his stairs. His
     building's numbers turn PAPER as she passes.
   - At about 8.0 a callout shows Vertigo's stairwell from above, his hand on the rail.
   - *A canon of plucked notes, each climb a semitone a step.*
5. **12.0–14.0:**
   - He is at her door (her storey 4); she is at his (his storey 5).
   - A RED ring round his dot and a PAPER ring round hers, small (these are dot rings, not
     the marker rings). Hold.

### s08 DOOR (90–104)

1. **0.0–6.0:** The Bass door shot at `tb = 28.5 + t * 0.5…`, re-timed to 6 s.
   - The light under the door; his shadow takes it a step at a time; his feet.
   - The handle is tried twice. Her chain goes taut across the gap each time (*steps,
     handle, chain*).
2. **6.0–9.0:** The keyhole push-in and his eye, the Bass key shot re-timed.
3. **9.0–14.0:** HIS VIEW THROUGH THE KEYHOLE.
   - A keyhole-shaped window in black. Inside, her dark room: the window wide open, the
     curtain billowing in on the teal light, nobody there.
   - Back on his eye at 12.5: it narrows (*wind, curtain, a low stinger*).

### s09 CALL (104–116)

1. **0.0–2.0:** His room, amber.
   - The overturned chair; the knife on the floor; the victim lying on the floor; a small
     flat red pool.
   - His door opens; her silhouette stands in it and freezes (*door creak*).
2. **2.0–5.0:** Close on the hands.
   - The victim's hand lies on the floor; hers reaches in.
   - The victim's fingers twitch and close on hers: alive.
   - One faint PAPER ring pulses from the victim's wrist (*a faint breath*).
3. **5.0–10.0:** THE DIAL, from straight above, filling the frame.
   - The dial: a PAPER number ring with hand-cut 1–0 and ten finger holes.
   - Her finger turns 9 to the stop, releases, and it spins back.
   - Then 1, then 1.
   - A loop arrow shows the turn (*real dial pulses: 9 clicks, 1, 1*).
4. **10.0–12.0:** The receiver at her ear. PAPER ripples ring from the earpiece twice; the
   ringing stops; she lifts her eyes to the window (*ringback, click*).

### s10 OPPOSITE (116–136)

1. **0.0–2.5:** THE BURST, from the floor of her dark room.
   - The door bursts in. The chain snaps and its links fly as PAPER dots.
   - A wedge of amber light floods the floor with his long shadow in it; his hat in the
     doorway (*impact, chain jingle*).
2. **2.5–5.5:** The empty room. He steps in and looks round. The curtain billows at the open
   window. He crosses to it (*curtain, steps*).
3. **5.5–9.5:** OVER HIS SHOULDER, the mirror of s02.
   - His hat and shoulders, from behind, fill the RIGHT of the frame.
   - Through her window: his own lit window across the street, one floor up. In it, SHE
     stands with his receiver at her ear, looking back at him.
   - 6.0: her PAPER look flies to him. 6.4: his RED look to her. The two lines meet (*held
     note*).
4. **9.5–12.5:** SIRENS.
   - A low angle up both facades on the night field.
   - Police light sweeps (RED and POLICE, flat rotating beams) cross the walls.
   - Two police-car silhouettes with light bars at the bottom (*sirens rising*).
5. **12.5–16.5:** THE NEIGHBOURS, on the section, wide.
   - Windows light up AMBER one after another in both buildings and in the city (*a plucked
     melody, one note per window*).
   - A silhouette appears in each. From each, a PAPER sight line flies to HIM in her
     window: a converging web.
   - 16.0: the RED MARKER RING closes round him (*swell; the squeak; a stab*).
6. **16.5–20.0:** THE PULL BACK.
   - Out to the whole block: every window lit, every line on his small ringed figure.
   - She stands in his window. The police lights strobe. Hold (*resolution*).

### s11 END (136–144)

1. **0.0–3.0:** The lit windows fly out of the section and reassemble as OPPOSITE: paper on
   black, the reverse of the title (*title stamp*).
2. **3.0–5.0:** The red slash cuts the title and the halves slide apart along it (the Bass end
   card) (*whip, the last chord*).
3. **5.0–8.0:** Black. The red dot pops once in the centre and pulses like a heart; it is gone by
   7.0. Silence at 8.0.

## Sound plan (for the mix)

- **Score:** the Bass cut's Herrmann strings on the Psycho chord at 120 bpm (`films/opposite_bass/audio/mix.py`
  has the instruments: bowed ostinato, pizz, tremolo, shrieks, chords).
  - s02: a tender music-box or celesta motif over pizz, and the clock ticks on the beat.
  - s03 drives in sixteenths.
  - s04 is the shrieks, then a heartbeat solo.
  - s05 is braams and dissonance.
  - s06–s08 are sparse: heartbeat, breath, steps.
  - The s07 race is a plucked canon.
  - s10: sirens, the neighbours' melody, and the strings resolve. Bb minor finally lands on
    the major.
- **Foley:** the generated library in `films/opposite/audio/gen`:
  - quarrel, scream_a/b, gasp_a/b, her_breath, his_breath, stifled, mug_smash, handle,
    stairs_up/down, her_steps, street_run, body_fall.
  - Synthesize the rest: kettle whistle, clock tick, pour, rotary-dial pulses, ringback,
    chain rattle, window sash, iron creak, wind, sirens, the door burst.
- **Mix:** −16 LUFS, true peak −1 dB.

## Technical

- **Scene files:** `films/opposite_full/scenes/sNN_slug.py` with:
  - `render(f, t, T)`, which calls `K.scene_setup(f)` first and then draws inside
    `with f.screen() as c:`;
  - `cues(T)`;
  - `motion_blur(t, T)`, which returns 1;
  - beat constants at module level.
- **Imports:** `from films.opposite_full import kit as K` and
  `from films.opposite_bass import world as B`.
- **Stills:** `RENDER_WORKERS=1 python3 -m engine.render --film opposite_full sNN --times=1.0,2.5 --scale 1.0`
  (the default scale is 0.5). Outputs go to `films/opposite_full/qa/sNN/`.
- **Contact sheet:** `RENDER_WORKERS=1 python3 -m engine.render --film opposite_full sNN --sheet 12 --window 2:6 --scale 0.25`
  (N frames spread over the window). It writes to `films/opposite_full/qa/`.
- **Budget:** at most 1.5 s per full-size frame. Deterministic: no unseeded random.
- **Self-review:** look at your frames at full size (`--scale 1.0`). Check hands, edges,
  seams, hairlines, popping, readability at phone size, and that every beat reads in one
  glance.
