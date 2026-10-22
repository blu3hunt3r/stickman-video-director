# SHADOW PLAY: production bible

> **Logline.** A sleepless woman watches the forty windows across the street and sees a
> murder in a window that has been dark for a year. It happens again the next night, to the
> second. It was never a crime. It was a show, staged for the women who watch.
> Run time 2:33.5 (3684 frames at 24 fps), 9:16.

Read this with `STYLE.md` (binding), `engine/API.md` and
`films/shadowplay/timeline/timeline.json` (locked, built by `timeline/build_timeline.py`).

## 1. What the film is about

Watching is not innocent: the one who looks can be looked at. The film plays three shows.
His fake murder for her. Her fake woman for him. And the film itself for **you**, which is
why the last line turns to the audience.

| Motif | Meaning | Where |
|---|---|---|
| **The grid of 40** | Her world, a catalogue of other people's lives (North by Northwest's facade grid) | s01 opens on it. It returns as **his grid of 40 paper dolls** in s11. |
| **The circle**: binoculars (two overlapping circles) | The watcher's eye | Her POV in s02 and s03. In s08 **he** holds her binoculars and looks back. In s12 a binocular glint looks at us. |
| **The shadow on the sheet** | Something for the eye to believe | The murder (s03, s05), her shadow (s07), the trap (s09, s10) |
| **The light switch** | Control | Window 9's light comes on (s03). He switches HER light off (s08). She switches the lamp on (s07). The lamp crashes (s10). |
| **RED** | Her coat (when she acts), the paper blood (the show), the police light's red half | Nothing else is red |

**Structure (the heartbeat).**

1. HOOK: s01, s02. Forty windows, and she watches. "Nobody ever looks up."
2. THE CRIME: s03 to s05. Window 9, a murder, nothing found. It happens again, identical, and the pin joint shows it is a puppet.
3. THE CROSSING: s06, s07. Red coat, the spiral stairs, apartment 9: a lamp, a sheet, two paper dolls.
4. THE TRAP: s08 to s10. Her own window from the other side, with a man in it. Ninety seconds. She gives him a show, he stabs a shadow, and she locks him in.
5. ECHO: s11, s12. Forty dolls, one with binoculars. "Mostly." Someone is watching us.

## 2. Cast: silhouette cards (`films/shadowplay/cast.py`)

| Character | Body / Look | Read by | Acting notes |
|---|---|---|---|
| **Her**, the watcher (narrator, ~35) | `cast.HER`, `cast.her(coat=False/True)` | Bob haircut; later the RED trench coat with the collar up | Still, curled, intent, until s06. Then quick, decisive, frightened but clever. The eyes are her whole performance: wide, unblinking when she watches. |
| **Him**, the killer | `cast.HIM`, `cast.him()` | Bowler hat, long coat: Magritte's faceless man | Never hurries until s10. Small, polite gestures (the wave). His eyes glint once, in s08. |
| **Window people** | `cast.dancer()`, `cast.cat_lady()` (+ `creatures` cat), `cast.crier()` | Ponytail and dress; bun; long hair | Tiny loops of life, inside their lit windows |
| **Cop** | `cast.cop()` | Peaked cap | Flashlight acting (s04) |
| **Paper dolls** | `cast.doll_man()`, `cast.doll_woman()` | Paper-doll mode: cut edges, pin joints, on thin rods | As objects they are PAPER-coloured. Their shadows on the sheet are ink (`ink=None`) and life size. |

## 3. World

Sets live in `films/shadowplay/sets*.py`. See their docstrings:

- the FACADE across the street, with 40 windows;
- her apartment;
- the street, with the police car;
- the spiral stairwell;
- apartment 9 with the lamp and the sheet;
- the killer's room.

**Window numbering** is row-major from the top left, 5 columns × 8 rows:

| Window | Row | Column |
|---|---|---|
| 4 | 1 | 4 |
| 9 | 2 | 4 |
| 12 | 3 | 2 |
| 30 | 6 | 5 |

Night, rain, blue-black world. Lit windows are warm amber boxes. Police light is blue/red.
Lightning only where noted.

**Facade lock** (s01 → s02 handoff and the s11 rhyme). The 40 windows sit on screen at:

- column centers x = 230, 385, 540, 695, 850;
- row centers y = 440, 590, 740, 890, 1040, 1190, 1340, 1490;
- each window about 96×120 px.

## 4. Storyboard

Times are scene-local seconds. `[word@t]` marks the narration word to sync (`T.at('word')`).
Scenes must keep animating through their transition handles (`T.handle_in`,
`T.handle_out`). **IN/OUT** are handoff contracts in screen px.

---

### s01 · FORTY WINDOWS · 9.0 s · Bass → facade · film 0:00

- **Beats.**
  - **0.0–1.5.** PAPER field with paper texture. Ink rectangles pop in row by row (stagger 0.03 s, outback), building a 5×8 grid at the facade-lock positions. Grid lines run between them, like the facade lines of North by Northwest.
  - **1.5–4.4.** L1: *"The building across the street has forty windows."* On [forty@3.24] the last window lands and the grid snaps tight.
  - **4.4–5.6.** The field flips from PAPER to night ink-blue. The rectangles invert to dark window holes, and a scatter of 9 lights up amber, flat Bass tones. Grid lines become ledges.
  - **5.6–7.7.** L2: *"I know every one of them by heart."* On [heart@7.17] all lit windows pulse twice, like a heartbeat.
  - **7.7–9.0.** Hold the flat facade. Rain streaks begin as flat diagonal lines.
- **OUT** (flatten reverse, 1.0 s). The flat facade (grid at the lock positions) resolves into the live, full-tone facade of s02.

### s02 · THE WATCHER · 15.0 s · facade → her window → street → facade · film 0:09

One continuous camera path.

- **IN.** The live facade at night in rain, windows at the lock positions, about 9 lit.
- **Beats.**
  - **0.8–6.7.** L3: *"Four dances alone. Twelve talks to her cat. Thirty cries on Sundays."*
    - On [Four@0.80] window 4 brightens: a dancer twirls alone.
    - On [Twelve@2.79] window 12: an old woman on a chair talks to a cat on the sill, and the cat's tail flicks.
    - On [Thirty@4.99] window 30: a woman sits with her head in her hands, shoulders shaking.
    - The camera drifts gently to each one.
  - **6.7–9.8.** L4: *"I don't sleep much. So I watch."* Dolly back across the street and through HER window.
    - Her window frame (mullions, sill, plant) slides in around the edges, with rain on the glass.
    - Her silhouette sits in the dark foreground at the window.
    - On [watch@9.18] she raises the binoculars to her eyes (glint).
  - **10.6–12.4.** L5: *"Nobody ever looks up."* Tilt down past her sill to the wet street far below. Two or three umbrellas pass and reflect in puddles. Nobody looks up.
  - **12.4–15.0.** Tilt back up and push forward toward the facade, as her binocular view.
    - Title **SHADOW PLAY**: hand-cut Bass letters in PAPER slide in along the facade's grid lines (North by Northwest homage). They stop across rows 3 to 5 for about 1.5 s, then slide off along the lines.
- **OUT** (iris, binocular, 1.0 s). A binocular mask (two overlapping circles, black outside) closes onto window 9 (dark), centered at about (540, 960).

### s03 · WINDOW NINE · 17.0 s · binocular POV → her eyes · film 0:24

- **IN.** Binocular view (two-circle mask) on window 9: dark, with a pale sheet behind the glass. Slight handheld drift (`Camera.shaken`, 3 px).
- **Beats.**
  - **0.6–3.9.** L6: *"Window nine had been dark for a year."* Slow push on the dark window.
  - **4.8–8.0.** L7: *"On Tuesday, at eleven, the light came on."* On [light@7.16] the window flickers on: the sheet glows amber from a lamp behind it.
  - **8.0–12.5.** The shadow play on the sheet, in silhouette.
    - A man's shadow (bowler) and a woman's shadow (bob).
    - She turns away. His arm rises: a jagged Bass arm with a knife (The Man with the Golden Arm), and it stabs down three times.
    - On the last stab a RED cut-paper splash bursts across the sheet.
    - The woman's shadow folds and falls.
    - At 12.3 the light snaps OUT.
  - **13.0–16.5.** L8: *"I watched a man kill a woman. Every second of it."*
    - The binocular mask opens wide. Pull back to her at her dark window, the binoculars lowering.
    - Her eyes are wide and do not blink (hold from [Every@15.15]).
- **OUT** (hard cut). Her eyes glow at about (540, 900) in a dark frame.

### s04 · NOTHING · 11.5 s · police · film 0:41

- **IN.** Inside apartment 9, dark. The door bursts open and flashlight beams cut in (`atmos.beam`). Blue/red police wash through the window.
- **Beats.**
  - **0.8–5.0.** L9: *"The police found nothing. No body. No blood. No woman."* Each beam lands on emptiness:
    - [body@2.70] the bare floor;
    - [blood@3.52] a bare wall where the sheet hung (no sheet now);
    - [woman@4.48] the bare window.
  - **6.2–9.7.** L10: *"The apartment had been empty for a year. They said I dreamed it."*
    - Cut inside the shot to the street outside: a crane down the facade to the police car.
    - A cop on the street shines his flashlight up at HER window across the street. She is caught in the beam.
    - On [dreamed@8.96] she steps back into the dark. The police car pulls away, its light bar strobing.
- **OUT** (bars, 2 horizontal, 1.0 s). Two horizontal panels wipe in: the stacked split screen of s05.

### s05 · AGAIN · 14.0 s · stacked split screen · film 0:52.5

- **IN.** Two stacked panels, each a 1080×960 view of window 9's sheet (dark), separated by a thin ink bar. Top is TUESDAY, bottom is WEDNESDAY.
- **Beats.**
  - **0.8–4.8.** L11: *"On Wednesday, at eleven... he killed her again."*
    - The top panel replays Tuesday.
    - On [Wednesday@1.04] the bottom panel lights. Both shadow plays run in perfect sync, and the knife falls on [again@4.22] in both.
  - **6.0–9.6.** L12: *"Same second. Same arm. Same silent scream."*
    - [second@6.34] a thin RED line ties identical moments across both panels.
    - [arm@7.49] the bottom panel slides up over the top one: a perfect overlay, the two arms one.
    - [scream@8.91] the woman's shadow throws her head back, mouth open, silent.
  - **10.6–12.8.** L13: *"People don't die the same way twice."* Push into the arm's elbow. The shadow has a round pin-joint notch and a thin rod line attached: a puppet. The pin turns.
  - **12.8–14.0.** Hold on the pin, then the arm raises for one last stab.
- **OUT** (slash, 0.75 s). The stab becomes a diagonal slash cut.

### s06 · CROSSING · 13.0 s · her apartment → stairwell → street → up the facade · film 1:06.5

- **IN.** Her apartment, dark. She pulls the RED coat from a hook and swings it on, and it flares. Red enters the film.
- **Beats.**
  - **0.8–3.8.** L14: *"So I did the one thing a watcher never does."* Coat on, collar up. Out of the door.
  - **3.8–7.0.** The spiral stairwell seen from straight above, with a Vertigo zoom (dolly-zoom plus rotation). A small red figure spirals down the square stairs into the dark.
  - **4.6–5.7.** L15: *"I crossed the street."* Out into the rain. She crosses the wet street, red coat and red reflection, between headlight-less parked cars.
  - **7.0–13.0.** One continuous crane up the facade of the other building, past lit windows, rising to window 9 (dark). Rain.
- **OUT** (iris rect, 1.0 s). Window 9's rectangle, centered at (540, 960), grows to fill the frame into s07's room.

### s07 · THE SHOW · 12.5 s · apartment 9 · film 1:19.5

- **IN.** Inside apartment 9, dark. The door opens and a wedge of hall light falls across the floor. She enters, red coat.
- **Beats.**
  - **1.4–6.4.** L16: *"There was no murder. Just a lamp... a sheet... and two paper dolls."* She strikes a match, and a small warm flame moves through the room.
    - [lamp@3.08] the bare-bulb lamp on its stand;
    - [sheet@4.14] the hanging sheet;
    - [dolls@5.78] two paper dolls on rods on the table, with red paper splash scraps.
  - **7.6–10.3.** L17: *"It was never a crime. It was a show."* She switches the lamp on: the sheet lights up, and her own giant shadow is thrown across it on [show@9.63].
  - **10.3–12.5.** She turns from the sheet to the window.
- **OUT** (hard cut). She stands at window 9, looking out, three-quarter back.

### s08 · THE OTHER SIDE · 14.5 s · from window 9 · film 1:32

- **IN.** Over her shoulder through window 9: across the street, HER building. Her own window is LIT (she left it dark).
- **Beats.**
  - **1.0–5.0.** L18: *"And for the first time, I saw my own window from the other side."* Slow push toward her window over the street. Rain.
  - **6.0–7.4.** L19: *"Someone was standing in it."* A man in a bowler stands in her lit window, holding her binoculars up at her (glint).
  - **7.4–9.0.** He lowers them and WAVES, slowly.
  - **9.0–11.1.** L20: *"He doesn't kill the women in the windows."*
  - **11.6–13.9.** L21: *"He kills the women who watch."* On [watch@13.31] he switches off her light, and her window goes black.
- **OUT** (dip to black, 0.75 s).

### s09 · NINETY SECONDS · 14.0 s · apartment 9 · film 1:46.5

- **IN.** Apartment 9 lit only by the lamp behind the sheet (amber through the sheet). She is frozen.
- **Beats.**
  - **0.6–3.0.** L22: *"I had ninety seconds. Maybe less."* She moves fast.
  - **4.0–9.7.** L23: *"He'd shown me how it works. A light. A sheet. Something for the eye to believe."*
    - [light@5.90] she sets the lamp behind the sheet;
    - [sheet@6.93] she pulls the sheet straight;
    - [believe@9.04] she clamps the woman doll on its rod in front of the lamp, and on the sheet a life-size woman's shadow stands.
  - **10.6–12.2.** L24: *"So I gave him a show."* She flattens herself behind the open door, in shadow.
  - **12.2–14.0.** Footsteps on the stairs. A line of light under the door, the shadow of two feet stops outside, and the handle starts to turn.
- **OUT** (hard cut). The turning handle.

### s10 · THE TRAP · 11.0 s · apartment 9 / hallway, wordless · film 2:00.5

- **Beats.**
  - **0.0–1.0.** Silence. The handle turns.
  - **1.0–2.0.** The door bursts open, hiding her behind it. He charges in, knife raised (the jagged arm).
  - **2.0–4.5.** He stabs through the sheet at the woman's shadow. The sheet tears in cut-paper slashes, and there is only the paper doll on its rod.
  - **4.5–5.5.** She slips out from behind the door, slams it and turns the key. He hammers on it.
  - **5.5–7.5.** From the hallway: light leaks under the door. The lamp CRASHES inside, light flickers and whirls, and it goes dark.
  - **7.5–11.0.** Sirens. Blue/red light floods the hallway window. She slides down against the door, the key in her fist, eyes wide.
- **OUT** (paper tear, 1.0 s).

### s11 · FORTY DOLLS · 10.0 s · the killer's room · film 2:11.5

- **IN.** A dark room. A cop's flashlight beam finds a wall pinned with 40 PAPER dolls in a 5×8 grid. The grid sits at the facade-lock positions: the rhyme with s01.
- **Beats.**
  - **1.0–4.7.** L25: *"They found forty paper dolls in his room. One for every window."* The beam sweeps the grid. Each doll is a different silhouette: the dancer, the cat lady, the crier, and so on. On [window@4.03] the grid flashes in the facade layout.
  - **6.0–7.9.** L26: *"One of them was holding binoculars."* Push in to one doll holding binoculars. Her paper coat is RED, the only red in the grid.
- **OUT** (dissolve, 1.25 s).

### s12 · MOSTLY · 12.0 s · her window · film 2:21.5

- **IN.** Her apartment, her window, rain. She stands at the glass.
- **Beats.**
  - **1.0–2.9.** L27: *"I don't watch the windows anymore."* She draws the curtain closed.
  - **4.2–4.9.** L28: *"Mostly."* Her fingers part the curtain a crack, and one eye glints. Across the street a new window lights up, warm.
  - **7.2–9.8.** L29: *"Be honest... would you have crossed the street?"* The camera pulls back out through her window into the rain over the street and turns to face the facade. In one dark window, the glint of binoculars looks straight at US.
  - **10.0–12.0.** The windows go dark one by one in a Bass stagger. Black.

## 5. Sound plan

- **Score.** Nocturnal, Bernard Herrmann-ish strings: pizzicato clock-tick motif, muted brass stabs.
  - The **ticking** (her sleeplessness, the clock at eleven) runs under s02 to s05.
  - The shadow murder is scored with a shrill string stab (Psycho echo) on each blow, then silence.
  - s06 stairwell: a spiralling Vertigo arpeggio.
  - s09: the ticking returns, faster (ninety seconds).
  - s10 is wordless and scored with silence, then hits.
- **Ambience.** Rain on glass and asphalt, gutters, distant traffic, a radiator tick.
- **Sync hits.**

  | Scene | Hits |
  |---|---|
  | s03 | the light switch on; the stabs; the light out |
  | s04 | door burst; police radio; siren whoop |
  | s05 | pin-joint creak |
  | s06 | coat flare; door; footsteps on the spiral stairs; rain swells outside |
  | s07 | match strike; lamp switch |
  | s08 | her light switching off, heard as a click from across the street |
  | s09 | footsteps on the stairs |
  | s10 | the door handle, the burst, the sheet tearing, the door slam, the key, hammering, the lamp crash, sirens |
  | s12 | curtain rings |

- **Narration.** Dry and close. Duck music −6 dB under the voice. Mix target −14 LUFS integrated.
