# NOBODY HAS A FACE — Production Bible (Director's Proposal / Phase A)

*A stickman noir in Style 1 Dark · 9:16 vertical · 2:58.8 (18 scenes) · English narration*

Approval note: the user chose to skip the Phase A approval checkpoint ("go straight to production"); this document is the locked proposal every department follows.

---

## 1. Header

| Item | Decision |
|---|---|
| English title | **Nobody Has a Face** (user language is English — no reference translation needed) |
| Logline | In a rain-soaked city where every person looks exactly the same, a detective who catches killers by their habits hunts a vigilante who murders the jurors that freed his partner's killer — until every clue he collects turns out to describe himself. Or someone who learned to wear his habits. |
| Core message (psychological truth) | When nobody has a face, your habits *are* your face — and the hardest face to see is your own. Identity can be read, and it can be copied. |
| Golden hook (0–3 s) | "Seven witnesses saw the killer's face. Not one of them could describe it." — over a police lineup of five identical faceless figures under a swinging bulb. |
| Ratio / duration / style | **9:16** vertical · **178.8 s** (4,292 frames @ 24 fps; under the 3:00 Shorts/Reels cap) · **Style 1 Dark — Classic Minimalist, faceless** (white line figures on a flat pitch-black canvas) |
| Narration | 399 words, one continuous take, first-person noir detective |
| Accent colors (exactly three) | **streetlamp amber** = light in the dark: matches, lamps, windows, embers, clues · **blood crimson** = the killer and guilt: THE red umbrella, red string, pins, X marks · **siren blue** = the law: police lights, badge, police flashlights |
| BGM | Noir felt-piano motif + dark ambient synth pad + sub drone, D minor, 72 BPM, one score identity start to finish; investigation adds brushed kit + upright bass; chase adds a 108 BPM pulse; the twist is scored with silence and a single braam |
| Arc | intrigue → certainty → obsession → the trap → blackout → horror of recognition → resignation → doubt (the copycat) → the question to the audience |

### Voice profile (frozen for the whole video)

Generated once via Magnific → ElevenLabs **Turbo v2.5** (cheap tier), catalog voice **Noah Reed** — stability 0.5, similarity 0.8, speed 0.95, speaker boost on, single continuous take (voice continuity by construction).

```text
One off-screen adult male narrator throughout, speaking in first person as the detective. General American accent, deep husky baritone, low pitch, resonant chest voice with a light natural rasp, no breathiness. Controlled, direct, world-weary delivery with restrained pitch variation, unhurried steady pace with deliberate pauses, and close, dry studio sound. Keep the same vocal timbre, register, accent, pace, and recording quality throughout. Emotional progression belongs to the visuals and music; do not change the narrator's voice or switch to character dialogue.
```

Narration is audio-only: no speech bubbles, captions, subtitles or lip movement in the picture.

### Five-stage heartbeat engine (3-minute allocation)

| Stage | Scenes | Share |
|---|---|---|
| 1 Golden Hook | S1 | 0:00–0:10 |
| 2 Disrupting Assumptions (faces, fingerprints and witnesses are useless here) | S2–S4 | 17% |
| 3 Unveiling Insider Secrets (habits are the only fingerprint: rain, 3:07, left hand, limp, red umbrella, the jury) | S5–S11 | 39% |
| 4 Ultimate Truth Revelation (the trap, the blackout, the mirror, the arrest, the lineup) | S12–S16 | 33% |
| 5 Elevation & Discussion (habits can be learned — "Was I the killer… or the perfect suspect?") | S17–S18 | 12% |

---

## 2. Cast, props and continuity (locked)

**Every figure is the same frozen Style 1 Dark anchor** (hollow circular head, no face, no eyes, no mouth, no hair, no clothing, no filled body, uniform medium white line weight, exactly two arms and two legs, one current pose per limb). Sameness *is* the premise. Characters are told apart only by staging, habits and props:

| Role | How the audience reads him |
|---|---|
| **The Detective / narrator ("I")** | the figure the camera follows. **Strikes matches with his LEFT hand**; **walks with a slight limp** (`rig.walk(limp=0.5)`; the LEFT step is short) — planted from S2 onward, never commented on until S14; carries the matchbook and a pocket watch stopped at 3:07 (broke the night his partner died) |
| The Witness | the trembling foreground pointing hand in S1 and S16; the seated figure in S9 |
| The Partner (flashback S10) | holds up the blue badge; falls |
| The Holloway killer (S10) | walks free out of the courthouse into the rain — just another identical figure |
| The last juror (S12–S13) | never seen: only her amber window, lit until 3:07 |
| The killer (S9, S11) | only ever the **red umbrella**, glimpsed |
| The Copycat (S17) | an identical figure in the crowd who strikes a match left-handed, opens a red umbrella and limps away |

**Props:** THE red umbrella (`props.umbrella(color=CRIMSON)`) — on the coat rack by his office door (S5, S14), on his back seat (S12), at his feet (S13), in the copycat's hand (S17). Matchbook with matches torn from the LEFT side (`missing={0,1,2,...}`). Burnt match + ember = the killer's calling card. Pocket watch stopped at **3:07** (`hour=3, minute=7`). Blue badge (partner, S10). Evidence board (OFFICE set) with victim photos, red string and, hidden at its center, a round mirror (S14).

**Violence:** chalk outlines, falls and a single muzzle flash only. No gore, no blood pools.

---

## 3. Storyboard (18 rows)

Times are global (scene start → end). Beats are scene-relative and anchored to narration words (see `timeline/timeline.json`; use `T.at('word')`).

| # | Time | Stage / purpose | Stick-figure scene | Motion, camera, transition | English VO | Key SFX |
|---|---|---|---|---|---|---|
| 1 | 0:00.0–0:09.9 | Golden hook | Police lineup: five identical figures under a swinging bare bulb; a witness's trembling hand points at each, unable to choose | Tilt down the light cone → foreground pointing hand → slow dolly into the center figure's hollow head; bulb dies on "face"; **out: the hollow head ring centered on black** | Seven witnesses saw the killer's face. Not one of them could describe it. Because in this city... nobody has a face. | bulb flicker/hum/creak, sub drop at blackout |
| 2 | 0:09.9–0:18.9 | Assumptions: the city | **In: ring = full moon.** Crane down a rain canyon of towers to a top-down river of identical umbrellas; street-level: one man stops under a lamp and strikes a match with his LEFT hand | Vertical crane with parallax → whip into top-down → cut to street level → push into the flame; **out: match flame close-up** | It rains here most nights. Under an umbrella, every man looks the same. I'm the one they call when that becomes a problem. | rain, distant thunder, whoosh, wet footsteps (uneven), match strike + flare |
| 3 | 0:18.9–0:30.8 | Assumptions shattered | **In: same flame** lights a magnifier — a hand under the lens is just a line; stacked vertical triptych (faces / fingerprints / witnesses); a sketch artist draws only a circle; pull back to a wall of identical circle sketches | Lens insert → panels slide in on each noun → draw-on → pull back → **out: whip tilt up into black** | You'd think crimes get solved with faces, fingerprints, and witnesses. Here, our hands are lines, our faces are circles... and every witness describes everyone. | brush swish, pencil scratch, stamp, paper, whip |
| 4 | 0:30.8–0:40.5 | The crime | **In: whip down** onto a top-down chalk outline in the rain, police strobe; a cop drops a blank file and walks off; vertical scroll through four outlines on the count; burnt match + ember beside the last | Top-down → scroll montage with camera flashes on "Four… Four… One" → macro push-in on the ember → **out: tilt up following the smoke** | So when the rain murders began, the department gave up fast. Four victims. Four rainy nights. One burnt match beside every body. | radio static, shutter flashes on the count, ember sizzle |
| 5 | 0:40.5–0:47.9 | Insider secret | **In: smoke dissolves at the office ceiling** — the office, blind-light stripes, THE red umbrella on the coat rack by the door (plant); he parts a blind slat with his LEFT hand; through the gap three passers-by, each habit circled in amber | Tilt down into office → push through the slat → amber iris rings pop on "habits" → whip down to the desk → **out: pocket watch close-up (3:07)** | But here's what the academy never teaches. People can hide their faces. Nobody can hide their habits. | room tone, blinds rattle/snap, chair creak |
| 6 | 0:47.9–0:54.9 | Clue: rain + 3:07 | **In: watch face → match cut to a street clock** in slow-motion rain at 3:07; four clocks at four scenes, all 3:07; pull back: it's *his* pocket watch, in his LEFT hand, stopped at 3:07 — he pockets it without a glance (plant) | Match cut → stacked clock montage on the beat → synchronized tick → pull-back reveal → **out: his hand into his coat… out with the matchbook** | The killer only worked in the rain. Always at seven minutes past three. Like he was keeping an appointment. | ticks, church bell ×3 on "three", clock stop |
| 7 | 0:54.9–1:03.0 | Clue: left hand | **In: same hand, open matchbook** — the gaps are all on the LEFT; slow-motion LEFT-hand strike and flare; smash to top-down crowd: exactly half the umbrellas light amber on "half" | Macro track → orbiting slow-mo flare → top-down gag → **out: crowd thins, revealing wet pavement** | Every match was torn from the left side of the book. He was left-handed. That narrowed it down to half the city. | paper tear, match strike + flare, walla, pluck on "half" |
| 8 | 1:03.0–1:11.4 | Clue: the limp | **In: same top-down pavement**: a trail of wet footprints; match-light pool follows them; short/long gaps measured; low side shot of *his* legs walking with the same short-long rhythm (plant); pull up into a line map — the amber half shrinks to a quarter | Top-down track → measure graphics → low side insert → map pull-back → **out: push into the amber quadrant** | His footprints told me more. Short step, long step. He walked with a limp. Now it was a quarter of the city. | uneven footsteps, tape measure, impact on "quarter" |
| 9 | 1:11.4–1:20.7 | Clue: the red umbrella | Interrogation bulb; seated witness trembles, shakes head; memory: top-down slow-motion river of white umbrellas — on "red" ONE blooms crimson, moving against the flow | Bulb flicker → slow-mo flashback → color reveal → push in → **out: red canopy fills the frame** | One witness remembered something. Not a face. A color. In a sea of umbrellas... one was red. | bulb hum/flicker, music drops out, stinger + sub on "red" |
| 10 | 1:20.7–1:30.8 | The connection + backstory | **In: red fills frame → pulls back into a taut red string** on the board; strings converge on a jury box of twelve circles — four crossed; gavel; the Holloway killer walks free; flashback: muzzle flash, the partner falls, badge clatters, the detective clutches his LEFT leg, the pocket watch cracks at 3:07 | Pull back → smash cut → flashback (dimmer lines) → **out: the badge spins to a stop, blue glint** | Then I found the thread. All four victims sat on the jury that freed the Holloway killer. The man who murdered my partner. | pins, twang, gavel, distant gunshot, body fall, badge clatter, watch crack |
| 11 | 1:30.8–1:40.9 | Escalation: the chase | **In: blue flicker at the end of an alley** — the red umbrella turns the corner; chase montage: run, fire escape, rooftop leap against the moon, laundry wipe; dead end; a burnt match still warm | Vertical alley perspective → handheld fast cuts → macro of the ember in his LEFT fingers → **out: the ember's glow** | Someone was finishing what the court wouldn't. I chased that red umbrella through every alley in town. All I ever caught was a warm match. | running splashes, metal clangs, leap whoosh, ember sizzle |
| 12 | 1:40.9–1:51.4 | Truth: the trap | **In: ember → match cut to the juror's amber window**; tilt down to his parked car; lightning; inside the car: wipers sweep (foreground wipes), the red umbrella on the back seat (plant), the dashboard clock crawls 3:05 → 3:07, his head nods | Tilt → lightning reveal → car interior → clock macro → **out: SMASH TO BLACK as the minute hand hits 3:07** | One juror was left. Friday, the forecast said rain. So I parked outside her building, and watched the clock crawl toward three-oh-seven. | rain on roof, wipers, ticks, heartbeat, total silence at the cut |
| 13 | 1:51.4–2:02.3 | Truth: the blackout | **In: black** — eyelids open on "blinked"; rack focus; he stands in the rain beside the open car door; dutch angle; her window is now dark; his LEFT hand opens on a cooling burnt match; at his feet the red umbrella rocks in the wind | Eyelid blink → rack focus → tilt up → hand macro → **out: whip pan** | I blinked. Just once. Then I was standing in the rain. Her window was dark. And a burnt match was cooling in my left hand. | tinnitus, rain swells in, ember dying, umbrella flap, whip |
| 14 | 2:02.3–2:16.4 | Truth: the mirror | **In: whip lands on the office board** — rapid clue montage, one hard hit per word (rain, 3:07, left hand, limp, the red umbrella by his own door); all red strings tighten and converge, tearing a photo away to reveal a round mirror | Hit-cuts on each clue → strings converge → dolly zoom into the mirror; his own hollow head inside it → **out: the mirror ring flashes blue** | Rain. Three-oh-seven. A left hand. A limp. A red umbrella by my own door. I'd spent months drawing the killer's portrait. It was a mirror. | five impacts, string tighten, glass ring, BRAAM on "mirror", silence |
| 15 | 2:16.4–2:27.6 | Truth: the arrest | **In: blue** — blue and crimson strobes through the blinds; top-down police cars arrive; the door opens, blue flashlight beams pin him; he raises both hands; the burnt match falls from his LEFT hand in slow motion | Strobe stripes → top-down → beams → hands up → **out: the falling match** | The blue lights came seven minutes later. My own precinct. I didn't run. Where do you run, when the man you're chasing... is you? | sirens approaching, brakes, doors, footsteps, radio |
| 16 | 2:27.6–2:35.9 | Truth: the lineup again | **In: the match lands on the lineup floor** — S1 callback, he stands center; one by one the figures walk the line: even steps… then his: short step, long step; the witness's hand stops trembling and points; the light isolates him | Callback composition → walk test → point → push into his head → **out: his head ring** | They put me in the lineup. The witness couldn't see my face. She didn't need to. She watched me walk. | bulb creak, even vs uneven footsteps (key), stinger on "walk" |
| 17 | 2:35.9–2:46.3 | Elevation: habits can be learned | **In: ring → top of an umbrella seen from above**; the police car leaves the precinct; at the curb, in a crowd of white umbrellas, one man strikes a match LEFT-handed, opens a RED umbrella and limps away into the rain | Match cut → crane down → match flare → red bloom → static wide as the red umbrella recedes → **out: red umbrella swallowed by darkness** | Case closed. Except... habits can be learned. Copied. Worn like a mask. And outside, it was still raining. | car away, the SAME match strike, umbrella open, uneven steps receding |
| 18 | 2:46.3–2:58.8 | Discussion | **In: darkness → cell window with the moon (ring callback)**; behind vertical bars he studies his left hand; split frame: him / the distant red umbrella; final: one match flares in the black, lights a hollow head that could be anyone, and goes out | Bars → split → final flame → black → one last match strike in the dark | In a city without faces, the hardest one to see is your own. So you tell me. Was I the killer... or the perfect suspect? | cell door, drip, match strike, flame out, final strike in silence |

Optional post-production overlays (never generated inside scenes; social cut only): S1 tail "NOBODY HAS A FACE" (center, title-safe); S18 tail "GUILTY OR FRAMED?" (center, above the bottom UI zone).

---

## 4. Scene beat sheets (for the animators)

Scene-relative seconds. "→" marks the required boundary state shared with the neighbor scene. Every scene: three beats, ≥ 4 devices, a visual change every 2–3 s, no idle figures.

### S01 — The Lineup (9.875 s) · golden hook
* 0–0.35: black → the bulb clicks on (flicker).
* 0.35–3.3 "Seven witnesses saw the killer's face.": start tight on the swinging bulb (`sets.LINEUP`, swing ±16°, period ~3.2 s), tilt down the amber cone onto the height-chart wall and the five figures (`breathe`), the cone sweeping across them (`f.lit` + `Light.cone` from the bulb).
* 3.3–6.0 "Not one of them could describe it.": the witness's arm enters big from the bottom foreground (slightly blurred, near layer) — trembling finger moves figure → figure, never settling.
* 6.0–9.875 "Because in this city... nobody has a face.": slow dolly into the CENTER figure's head; neighbors slide out of frame; bulb flickers on "nobody", dies on "face" (8.58) → darkness except the hollow head circle. **→ OUT: white ring centered at screen (540, 960), on-screen radius ≈ 260 px, black elsewhere.**

### S02 — The City (9.042 s)
* **IN: same ring at (540, 960) r≈260 = full moon**; thin cloud wisps cross it; rain starts.
* 0–2.8 "It rains here most nights.": crane down from the moon through a canyon of towers (2–3 parallax depths, amber windows, `wet reflections`).
* 2.8–6.0 "Under an umbrella, every man looks the same.": whip (`f.whip`, motion blur) into a straight-down view of a crosswalk river of identical white umbrellas (`sets.crowd_top`).
* 6.0–9.042 "I'm the one they call when that becomes a problem.": street level under a streetlamp: the detective stops, raises the matchbook and strikes with his LEFT hand on "I'm" (6.07) — flare lights his hollow head from below; one limping step; push into the flame. **→ OUT: the lit match flame at screen ≈ (540, 1150), flame ≈ 100 px tall.**

### S03 — Useless Evidence (11.917 s)
* **IN: the same flame** at the same screen spot; a magnifying glass slides into its light.
* 0–5.8 "...faces, fingerprints, and witnesses.": lens insert (`f.clipped`) shows a stick hand = just a line; three stacked panels (9:16 triptych) slide in on "faces" (2.38) / "fingerprints" (3.31) / "witnesses" (4.29): an empty circle head · a brush dusting glass revealing only one straight line · a witness shrugging.
* 5.8–9.0 "Here, our hands are lines, our faces are circles...": a hand stamps an ink line; a sketch artist's pencil draws a circle on a blank sheet (draw-on) on "circles".
* 9.0–11.917 "...and every witness describes everyone.": fast pull back — the sketch is one of dozens of identical circle sketches covering a precinct wall. **→ OUT: whip tilt UP into black (streaks).**

### S04 — The Rain Murders (9.667 s)
* **IN: whip down from black** onto top-down wet pavement.
* 0–4.4 "...the department gave up fast.": a chalk outline in the rain (`fx.chalk_outline`), ripples, police strobe glow pulsing at the frame edge (blue/crimson `siren`); a cop figure drops a blank folder into a puddle and walks off.
* 4.4–6.8 "Four victims. Four rainy nights.": vertical scroll through four outlines in four places (cobbles, bridge rail, stairwell, parking lines), each landing on its word with a white camera-flash pop.
* 6.8–9.667 "One burnt match beside every body.": macro on a burnt match by the outline's hand — ember glows, smoke curls; four 0.25 s inserts of the same match at each scene. **→ OUT: tilt up following the smoke wisp at screen center.**

### S05 — Habits (7.417 s)
* **IN: smoke wisp at center dissolving at the office ceiling.**
* 0–2.4: tilt down into `sets.office` (blind stripes, lamp, THE red umbrella on the coat rack by the door — visible, not emphasized). The detective stands at the window; his LEFT hand parts a blind slat.
* 2.4–5.1 "People can hide their faces.": push through the gap: the street below, three identical passers-by under umbrellas.
* 5.1–7.417 "Nobody can hide their habits.": amber iris rings pop around a habit on each (checks a watch · taps a foot · a hitch in the step); slat snaps back; whip down to the desk. **→ OUT: pocket watch close-up on the desk at 3:07, face centered, r ≈ 300 px.**

### S06 — Three-Oh-Seven (7.0 s)
* **IN: the same watch face, same size and position → match cut to a street clock** in the rain.
* 0–2.4 "The killer only worked in the rain.": slow-motion rain streaks and splashes across the clock face at 3:07.
* 2.4–4.4 "Always at seven minutes past three.": stacked montage of four clocks (tower, stairwell wall clock, station clock, a clock on a wet wall) all at 3:07; bell tolls three on "three" (3.90).
* 4.4–7.0 "Like he was keeping an appointment.": every minute hand ticks in sync; pull back from the last face: his pocket watch in his LEFT hand; he pockets it without a look. **→ OUT: his hand dips toward his coat; frame darkens on the hand.**

### S07 — Left Hand (8.083 s)
* **IN: the same hand comes up holding the open matchbook** (macro).
* 0–3.2: track right→left along the matches; the torn stubs on the LEFT glow amber on "left" (2.01); magnifier passes.
* 3.2–4.9 "He was left-handed.": slow-mo LEFT-hand tear and strike — flare, sparks, slight orbit (roll 0→8°).
* 4.9–8.083 "...half the city.": smash to top-down crowd; on "half" (6.22) every umbrella on the left half of the frame turns amber (`highlight=lambda i,x,y: x<540`). **→ OUT: crowd thinning, top-down, revealing wet pavement.**

### S08 — The Limp (8.375 s)
* **IN: same top-down pavement**; the last umbrellas leave, revealing a trail of wet footprints up the frame.
* 0–2.8: a match-light pool (`Light.radial`) follows the prints from the bottom.
* 2.8–5.5 "Short step, long step. He walked with a limp.": short gap measured on "Short" (2.80), long on "long" (3.66) — a white measuring line with tick marks (no numbers); a low side insert of the detective's own legs walking the same short-long rhythm (plant, no comment).
* 5.5–8.375 "Now it was a quarter of the city.": pull up into a white line street map; the amber half shrinks to one quadrant on "quarter" (6.71). **→ OUT: push into the amber quadrant.**

### S09 — The Red Umbrella (9.333 s)
* 0–3.3: interrogation room — single bulb, table, the witness seated (`rig.sit`), the detective standing in shadow (dim). The witness's trembling hand rises to the head.
* 3.3–5.6 "Not a face. A color.": head shake on "Not a face"; bulb flickers on "color".
* 5.6–9.333 "In a sea of umbrellas... one was red.": memory — top-down river of white umbrellas in slow motion; on "red" (7.73) ONE umbrella blooms crimson (amount 0→1 in 0.25 s) walking against the flow; push in. **→ OUT: the red canopy fills the frame.**

### S10 — The Thread (10.083 s)
* **IN: frame full of crimson → pulls back into a taut red string** on the office board.
* 0–2.1 "Then I found the thread.": his LEFT hand pins string from photo to photo.
* 2.1–6.4 "All four victims sat on the jury that freed the Holloway killer.": strings converge on a jury card — 12 circles in two rows, four get crimson X marks on "four" (2.50); smash to a courtroom: gavel slams on "freed" (4.66); a figure walks out of tall doors into the rain, free.
* 6.4–10.083 "The man who murdered my partner.": flashback (dimmer lines, slight blur): alley, rain; the partner holds up the blue badge; muzzle flash from the dark; on "murdered" (8.04) he falls; the badge clatters and spins; the detective lunges, clutching his LEFT leg; his pocket watch hits the ground, glass cracks, hands at 3:07. **→ OUT: badge spins to a stop — blue glint.**

### S11 — The Chase (10.167 s)
* **IN: blue flicker at the far end of a vertical alley** (police light).
* 0–3.3: the detective at the mouth of the alley; the red umbrella turns the corner at the far end.
* 3.3–7.3 "I chased that red umbrella through every alley in town.": chase montage ~1 s per cut, handheld: run toward camera (limp), fire-escape zigzag climb, rooftop leap silhouetted against the moon with the red umbrella crossing far below, laundry sheets wipe the frame.
* 7.3–10.167 "All I ever caught was a warm match.": dead end, nobody; a burnt match on the ground still smoking; he picks it up with his LEFT hand; macro: the ember glows on "warm match". **→ OUT: the amber ember dot, centered.**

### S12 — The Trap (10.458 s)
* **IN: ember → match cut to the juror's lit window** (`sets.apartment`), high on the facade.
* 0–2.6 "One juror was left.": tilt down the facade to his parked car across the street (`props.car_side`).
* 2.6–5.4 "Friday, the forecast said rain.": lightning (`fx.lightning` + `Light.full` flash) reveals the street; rain doubles.
* 5.4–10.458 "...watched the clock crawl toward three-oh-seven.": car interior: wipers sweep across the windshield as foreground wipes; her amber window through the glass; THE red umbrella on the back seat (glimpse); dashboard clock macro crawling 3:05 → 3:06 → 3:07, landing on "seven" (9.04); his head nods. **→ OUT: smash to black ≈ 9.7 s, black to the end of the scene.**

### S13 — Blackout (10.917 s)
* **IN: black.**
* 0–3.9 "I blinked. Just once.": eyelid half-opens on "blinked" (1.20) on blurry rain, closes; opens fully on "once" (2.58) with a rack focus (blur 18 → 0).
* 3.9–7.5 "Then I was standing in the rain. Her window was dark.": he stands in the rain beside the open car door; slow dutch roll (−8° → +6°); tilt up — her window is dark on "dark" (6.88).
* 7.5–10.917 "And a burnt match was cooling in my left hand.": his LEFT hand opens: burnt match, ember dying, smoke; reveal at his feet the red umbrella lying open, rocking in the wind. **→ OUT: whip pan (streak to the left).**

### S14 — The Mirror (14.083 s)
* **IN: whip lands on the office evidence board.**
* 0–7.4: one hard cut per clue word, each card flashing amber as named: "Rain" (0.35) rain-cloud icon · "Three-oh-seven" (1.50) his pocket watch at 3:07, pinned · "A left hand" (3.08) he raises his left hand, a burnt match in it · "A limp" (4.58) a short-long footprint pair · "A red umbrella by my own door" (5.69) whip to the coat rack: THE red umbrella by his door, crimson pulse.
* 7.4–11.5 "I'd spent months drawing the killer's portrait.": back to the board — every red string tightens and converges on the center, tearing a photo away to reveal a round mirror.
* 11.5–14.083 "It was a mirror.": he steps close; inside the mirror his own hollow head; dolly zoom; on "mirror" (12.03) the mirror ring fills the frame (S1 ring callback); hold in near-silence. **→ OUT: the ring flashes blue.**

### S15 — Blue Lights (11.208 s)
* **IN: blue.** 0–3.7: office, blue/crimson strobe stripes through the blinds (`window_light` alternating with `siren(t)`, animate `stripes_offset`); he stands motionless as they sweep over him.
* 3.7–6.8 "My own precinct. I didn't run.": top-down: three police cars pull in, light bars strobing; figures with blue flashlight beams approach; inside, the door opens (`door_open`, `door_light=BLUE`), beams pin him.
* 6.8–11.208 "Where do you run, when the man you're chasing... is you?": he raises both hands (interpolate to `rig.hands_up`); on "is you?" (9.75) the burnt match slips from his LEFT hand and tumbles in slow motion through the beams. **→ OUT: the falling match, mid-frame.**

### S16 — The Lineup, Again (8.292 s)
* **IN: the match lands on the lineup floor**, then the S1 composition: same bulb, same wall, he stands at the center position.
* 0–2.3 "They put me in the lineup.": quick tilt down the cone (faster echo of S1).
* 2.3–5.6 "The witness couldn't see my face. She didn't need to.": the witness's trembling hand rises in the foreground; the figures step forward and walk the line one at a time — even gaits.
* 5.6–8.292 "She watched me walk.": his walk: short step, long step (`limp=0.85`); the hand stops trembling and points at him on "walk" (6.38); the bulb stops swinging, light isolates him; push into his head. **→ OUT: his head ring centered, r ≈ 200 px.**

### S17 — Habits Can Be Learned (10.417 s)
* **IN: the ring → top of an umbrella from above.** 0–1.8 "Case closed.": pull up — a police car (lights off) drives away from the precinct steps into the rain.
* 1.8–7.4 "Except... habits can be learned. Copied. Worn like a mask.": crane down to the curb: a crowd of identical figures with white umbrellas; one, center, raises a matchbook on "learned" (3.76), strikes LEFT-handed on "Copied" (4.60) — amber flare on his hollow head — and opens a RED umbrella on "Worn like a mask" (5.59).
* 7.4–10.417 "And outside, it was still raining.": he walks away up the frame with a limp; static wide shot; the flame goes out; only the red umbrella recedes into the dark. **→ OUT: red umbrella small, top of frame, swallowed by darkness.**

### S18 — Your Verdict (12.5 s)
* 0–5.4 "In a city without faces, the hardest one to see is your own.": jail cell — vertical bars, a bench, a small high barred window with the moon ring and rain; he lifts his left hand and studies it.
* 5.4–8.6 "So you tell me. Was I the killer...": vertical split — him behind bars (top) / the distant red umbrella crossing a street (bottom); light alternates amber on him, crimson on the umbrella.
* 8.6–12.5 "...or the perfect suspect?": black; one match strikes at center, lights a hollow head that could be anyone; hold; the flame goes out ≈ 11.4; black. Final sound: one more match strike in the dark (no light) ≈ 12.1.

---

## 5. Continuity connections (both sides named)

| Cut | End of scene | Start of next |
|---|---|---|
| 1→2 | hollow head ring centered, r≈260 | the same ring is the full moon |
| 2→3 | lit match flame close-up | the same flame lights the magnifier |
| 3→4 | whip tilt up into black | whip down from black onto the chalk outline |
| 4→5 | smoke wisp rising, tilt up | smoke dissolving at the office ceiling, tilt down |
| 5→6 | pocket watch face at 3:07 | match cut: a street clock face at 3:07 |
| 6→7 | his left hand into his coat | the same hand out with the matchbook |
| 7→8 | top-down crowd thinning | same top-down camera: wet pavement + footprints |
| 8→9 | push into the amber quadrant | the amber interrogation bulb |
| 9→10 | red canopy fills the frame | pull back into the red string |
| 10→11 | badge's blue glint | blue police flicker at the end of the alley |
| 11→12 | amber ember dot | the juror's amber window |
| 12→13 | smash to black at 3:07 | black, then eyelids open |
| 13→14 | whip pan | whip lands on the board |
| 14→15 | mirror ring flashes blue | blue strobes through the blinds |
| 15→16 | burnt match falling | the match lands on the lineup floor |
| 16→17 | his head ring | top of an umbrella seen from above |
| 17→18 | red umbrella swallowed by dark | cell window moon in the dark |

---

## 6. Ambience map (sound designer; continuous beds under each scene)

| Scene | Space | Rain bed (0–1) | Extra bed |
|---|---|---|---|
| S1 | interior lineup | 0.25 muffled | bulb hum, room tone |
| S2 | exterior city | 0.9 | distant traffic, far thunder |
| S3 | interior precinct | 0.2 muffled | room tone, faint walla |
| S4 | exterior crime scenes | 0.7 | police radio bursts |
| S5 | interior office | 0.35 muffled (on window) | room tone |
| S6 | exterior clocks → interior at 4.4 s | 0.6 → 0.3 | — |
| S7 | interior macro → exterior crowd at 4.9 s | 0.3 → 0.8 | walla from 4.9 s |
| S8 | exterior | 0.6 | — |
| S9 | interior interrogation → memory exterior at 5.6 s (slowed, muffled) | 0.2 → 0.8 | bulb hum |
| S10 | office → courtroom (4.6 s, dry) → flashback alley (6.4 s) | 0.3 → 0.1 → 0.8 | — |
| S11 | exterior alleys | 1.0 | far siren |
| S12 | exterior → car interior at 5.4 s (rain on roof) → **silence at 9.7 s** | 0.8 → 0.8 close/muffled → 0 | — |
| S13 | silence + tinnitus → exterior rain fades in from 1.2 s | 0 → 1.0 | — |
| S14 | interior office; **silence 12.1–13.5 s** after the braam | 0.3 | room tone |
| S15 | interior office + sirens outside | 0.3 | sirens |
| S16 | interior lineup (as S1) | 0.25 muffled | bulb hum |
| S17 | exterior street | 0.9 | — |
| S18 | interior cell (high window) → silence at the end | 0.25 → 0 | drip |

## 7. Score plan (one identity, 72 BPM, D minor)

* **Instruments (BGM lock):** felt piano (motif), dark ambient synth pad, sub drone. Investigation layer: brushed snare + upright bass plucks (S5–S9). Tension pulse (S4, S10–S12). Chase pulse 108 BPM (S11 3.5 s → 8.0 s). Heartbeat (S12–S13). Strings swell (S10 flashback, S15, S18).
* **Motif ("No Face"):** A3 – D4 – F4 – E4 (rise, then a falling semitone). Statements: S1 on "nobody has a face"; S5 in the investigation groove; S10 slow and low (mourning); S16 on the point; **S17 the copycat variant — the last note bends to E-flat (wrong, unresolved)**; S18 final, unresolved, fading.
* **Hits:** S1 sub drop at the blackout (8.6); S4 three soft hits on "Four / Four / One"; S9 music drops to silence at 5.6 → stinger + sub on "red" (7.73); S11 chase ends dead at "caught"; S12 everything cuts to silence at the smash to black (~9.7); S13 dissonant swell from 3.9; S14 five clue hits, braam on "mirror" (12.03), then silence; S17 motif variant on "Copied"; S18 final chord ≈ 9.5, fade by 12.0.
* **Mix:** voice-first. Music ducked ≈ −9 dB under narration, SFX ≈ −3 dB under narration except designed hits. Master −14 LUFS integrated, ≤ −1 dBTP, 48 kHz stereo.
