# RED: production bible

> **Logline.** Every child in the village knows the rule: never leave the path. The winter
> she turns seven, a girl in a red hood is sent down it to a "grandmother" she doesn't
> have. A wolf chases her off the path, and saves her life. At the end of the path lives
> the thing the village feeds one child a year. Run time 2:34 (3696 frames at 24 fps), 9:16.

Read with `STYLE.md` (binding), `engine/API.md` and `films/red/timeline/timeline.json`
(locked, built by `timeline/build_timeline.py`).

## 1. What the film is about

The rules that keep us safe can be the ones that feed us to the monster. The wolf, which
everyone fears, is the guardian. The path, which everyone trusts, is the trap. And a
mother who could not save her daughter gave her fire.

| Motif | Meaning | Where |
|---|---|---|
| **The path**: a black Bass line, marked by stakes | The rule, obedience | s01 (Bass line), s02 to s04 (stakes), s05 (she crosses it), s06 (where it ends), s11 (a NEW path of lanterns: a line of light) |
| **The red triangle**: the hood | A child, an offering | Hers; the hoods in the trees (s06); falling at dawn (s09); old Red's; the new child's |
| **Eyes in the dark** | What we fear (s04) is not what we should fear (s07) | The wolf's eyes pace her. The spider's eyes are a cluster of eight, cold white. |
| **Fire**: the lantern | The mother's love | Packed in the basket (s02), revealed (s08), the burning web (s08), lanterns everywhere at the end (s11) |

**Structure (the heartbeat).**

1. HOOK: s01, s02. The rule. The hood is tied and the basket given. Doors close.
2. DESCENT: s03 to s05. The title, the quiet forest, the wolf. Chased off the path and up the ridge, where the wolf waits.
3. REVELATION: s06, s07. The end of the path: the web-wrapped house, red hoods, one for every winter. "Grandmother" comes down on a thread.
4. FIRE: s08. The fight. Bread, wine, and a lantern. The web burns.
5. ECHO: s09 to s11. Dawn, hoods falling, her hand on the wolf. Home, looked at like a monster. Years later she is the grandmother, and a new path is lit.

## 2. Cast: silhouette cards (`films/red/cast.py`; creatures in `engine/creatures.py`)

| Character | Body / Look | Read by | Acting notes |
|---|---|---|---|
| **Red** (narrator as an old woman; on screen, 7 years old) | `cast.RED_GIRL`, `cast.red()` | RED pointed hood and cloak; small, 380 px | Brave in small ways. She walks with the basket on her arm (`reach`/arm keys). She looks back once (s02), runs (s04, s05), falls (s05), stands her ground (s08). |
| **Mother** | `cast.MOTHER`, `cast.mother()` | Kerchief, floor-length dress | Kneels to tie the hood (s02). Her eyes close on "grandmother". Runs and embraces Red (s10). |
| **Villagers** | `cast.villager_m()`, `cast.villager_f()` | Flat caps, kerchiefs, long coats | Watch from doorways, close doors (s02). Recoil (s10). Lanterns raised. |
| **The Wolf** | `engine.creatures` wolf, ~330 px at the shoulder | Huge, shaggy ruff, Limbo eyes | Paces, herds, never bites her. Fights the spider. Wounded at dawn (lies, breathes). Old and grey-muzzled in s11. |
| **Grandmother**, the spider | `engine.creatures` spider | Legs 3–4× her height; a cluster of eyes | Descends on a thread (s07), charges, stabs (s08), burns and retreats. |
| **Old Red** | `cast.OLD_RED`, `cast.old_red()` | Long red cape and hood, stooped, cane (a prop line) | Lights the last lantern (s11). |
| **The new child** | `cast.NEW_CHILD`, `cast.new_child()` | A small red hood and capelet | Walks up the lantern path (s11). |

## 3. World

Sets live in `films/red/sets*.py`. See their docstrings for:

- terrain with `ground_y(x)`: the village street, the path down through the forest, the ridge, the clearing;
- the village;
- the Limbo forest (side-scrolling, 4–5 fog layers);
- the ridge/valley view;
- the cottage and the web;
- the hoods in the trees;
- lanterns.

The world is white-grey fog, ink trees, falling snow, and one red.

| Scene | Light |
|---|---|
| s02 | night with warm windows |
| s03, s04 | pale flat winter light with shafts |
| s07, s08 | darker; fire is the only warm light |
| s09 | dawn (`pal.dawn`) |
| s10 | grey morning |
| s11 | dusk with lanterns |

Footprints in the snow are welcome (sets helper). Feet and paws must plant on `ground_y`
(`engine.motion` does it when you pass the ground function).

## 4. Storyboard

Times are scene-local seconds. `[word@t]` marks the narration word to sync (`T.at('word')`).
Scenes keep animating through their transition handles. **IN/OUT** are handoff contracts in
screen px.

---

### s01 · THE RULE · 9.0 s · Bass · film 0:00

- **Beats.**
  - **0.0–1.4.** PAPER-white field with paper texture. A black Bass line, the path seen from above, draws itself from the top of the frame to the bottom, winding gently down the center (cut-paper edge, ~18 px wide).
  - **1.4–3.7.** L1: *"Every child in our village knew the rule."*
    - On [child@1.77] a small RED triangle (the hood, from above) appears at the top of the line and glides down along it.
    - On [rule@3.23] short black stakes pop up along both sides of the line (stagger, outback).
  - **5.0–7.3.** L2: *"Never... leave the path."*
    - On [Never@5.00] black thicket blots grow beside the path, and pairs of glowing eyes open in them.
    - On [leave@6.18] the triangle stops.
    - On [path@6.70] the eyes blink out.
  - **7.3–9.0.** The top-down view tilts to a side view: the path line rotates down to become a ground line at y≈1500. The triangle sits on it as the girl's hood. The white field above is the sky.
- **OUT** (ink, 1.25 s). The black ground and thickets bleed into s02's night village.

### s02 · THE HOOD · 15.0 s · village at night · film 0:09

- **IN.** The village at night: steep snowy roofs, lit windows, lanterns on posts, falling snow. A warm open doorway at center. The girl stands in it, the ground at y≈1500.
- **Beats.**
  - **1.0–7.0.** L3: *"The winter I turned seven, my mother tied a red hood under my chin, and gave me a basket for my grandmother."*
    - The mother kneels in front of her against the warm doorway (a two-shot in silhouette).
    - On [tied@3.04] the mother's hands go to the girl's chin. On [hood@3.68] the hood is pulled up: a small red triangle in the night.
    - On [basket@5.45] the mother gives her a basket with a cloth over it.
  - **8.4–12.1.** L4: *"I didn't have a grandmother. I didn't know that yet."*
    - The mother stands and turns her face away, and her eyes close on [grandmother@9.12].
    - Across the street villagers watch from their doorways, and one by one they close their doors. The light wedges vanish on [didn't@10.68], [know@10.95] and [yet@11.52].
  - **12.1–15.0.** The girl walks to the village gate and out onto the path (stakes). She looks back once at about 13.5. The mother lifts a hand in the doorway.
- **OUT** (dissolve, 1.5 s). The girl walks right, small, at about (540, 1350), past the gate's last stake.

### s03 · THE PATH · 14.0 s · title + Limbo forest · film 0:24

- **IN.** The girl walking right at about (540, 1350). The forest begins: trunks in 4–5 fog layers.
- **Beats.**
  - **0.5–4.5.** Title **RED**: three hand-cut red paper letters, large (about 300 px), standing between the trunks like they were cut from her hood, slightly misaligned. She walks past them. At 3.5 they fall over into the snow, one, two, three, and fog drifts over them.
  - **4.5–14.0.** The Limbo walk, side-scrolling, with the path stakes and the trail descending into the valley. Light shafts between trunks. Snow falls.
  - **6.2–12.2.** L5: *"The path went down into the valley. The deeper it went, the quieter the world became."*
    - On [deeper@8.78] the fog thickens and the trunks grow darker and closer together.
    - On [quieter@10.39] the snowfall thins to nothing and the shafts fade: a hush.
- **OUT** (dissolve, 1.0 s). She walks right at about (540, 1350), deeper in.

### s04 · THE WOLF · 14.0 s · dark forest · film 0:38

- **IN.** Darker forest with black thickets. She walks right on the path.
- **Beats.**
  - **1.0–2.5.** L6: *"Then the wolf came."* On [wolf@1.49] two glowing eyes open in a thicket to her left, behind. They keep pace, sliding between the trunks.
  - **3.6–7.2.** L7: *"And everybody knows what wolves do to little girls."* Glimpses of something huge moving between trunks: a shoulder, a ruff, a tail. She walks faster, then on [girls@6.49] she RUNS (child_run).
  - **7.2–12.0.** The run. The camera tracks, and the eyes pace her on the left.
  - **12.0–14.0.** The WOLF steps onto the path ahead and blocks it: huge, backlit by fog, head low. She skids to a stop (anticipation, settle).
- **OUT** (whip right, 0.5 s). She bolts off the path to the right.

### s05 · DEEP SNOW · 14.5 s · chase up the ridge · film 0:52

- **IN.** Mid-whip: she runs right and uphill off the path into deep snow. The wolf is behind her.
- **Beats.**
  - **0.8–9.5.** L8: *"It chased me off the path, up the ridge, into the deep snow. And then it stopped... and waited."*
    - On [off@1.53] she crosses the line of stakes: she has left the path.
    - The wolf bounds after her. It herds her and never closes.
    - On [ridge@3.30] the climb begins: the camera cranes up the slope with them.
    - On [snow@5.17] she falls face-down in deep snow and scrambles.
    - On [stopped@7.03] the wolf stops, a few body-lengths behind.
    - On [waited@8.81] it sits in the snow.
  - **9.5–14.5.** She gets up and backs away up to the ridge top. The wolf's head turns to look PAST her, over the ridge. She turns to look where it is looking.
- **OUT** (hard cut). She is at the ridge top, back to the camera, at about (540, 1400), looking over.

### s06 · RED HOODS · 14.5 s · the valley view · film 1:06.5

- **IN.** Her POV from the ridge: the valley in fog below, with the path's stakes winding down to a clearing.
- **Beats.**
  - **0.6–2.5.** L9: *"From up there, I could see where the path ended."* The camera follows the path down (tilt and crane).
  - **4.0–6.7.** L10: *"There was a house. There was no grandmother."* On [house@4.46] the cottage, wrapped in web: white strands catching light, dead still.
  - **7.6–10.7.** L11: *"Only red hoods. One for every winter."* On [hoods@8.33] the trees around the cottage are hung with RED hoods, small, many, swaying. On [winter@10.00] pull back to show how many.
  - **10.7–14.5.** The hoods flatten into a Bass grid of red triangles on white, row after row, counting winters. It pulses once.
- **OUT** (flatten reverse, 1.0 s). The grid becomes live again for s07.

### s07 · GRANDMOTHER · 13.0 s · the ridge edge · film 1:21

- **IN.** The girl at the edge of the trees on the ridge, small, under dark canopy. The forest goes still.
- **Beats.**
  - **1.0–6.3.** L12: *"The village called it Grandmother. They fed it one child a year, so it would leave the rest of them alone."*
    - On [Grandmother@1.86] the first long leg descends from the canopy on a thread, then another and another. Enormous.
    - On [child@3.61] the legs touch the snow around her.
    - The eye cluster opens above her: cold white.
    - Hold on [alone@5.69].
  - **6.3–13.0.** The spider drops fully and CHARGES, a mass of legs. She backs away and falls. At 12.6 the WOLF leaps over her, between her and the legs.
- **OUT** (hard cut on action). The wolf in mid-leap at upper right.

### s08 · FIRE · 17.0 s · the fight · film 1:34

- **Beats.**
  - **0.0–3.0.** The fight. Legs stab, the wolf twists and bites a leg. The girl is knocked down and the basket flies.
  - **3.0–7.2.** L13: *"My mother had packed my basket herself. Bread. Wine."* On [basket@4.07] the basket rolls in the snow; on [Bread@5.65] a loaf tumbles out; on [Wine@6.42] a bottle rolls out.
  - **8.0–9.2.** L14: *"And a lantern."* On [lantern@8.38] the lantern rolls out, glowing amber in the snow.
  - **10.2–13.3.** L15: *"She couldn't save me. But she could give me fire."*
    - The spider pins the wolf.
    - She grabs the lantern, runs to the web strands anchoring the spider's thread, and on [fire@12.66] SMASHES it against the web.
  - **13.3–17.0.** Fire races along the web lines (`atmos` burning line). It runs up the threads into the canopy and down toward the valley. Embers. The spider burns and recoils, and fire light fills the frame.
- **OUT** (flash, warm white, 1.0 s). Fire flares to white, and white becomes dawn.

### s09 · DAWN · 14.0 s · the clearing at dawn · film 1:51

- **IN.** Dawn (`pal.dawn` light), smoke, burnt web hanging in black threads.
- **Beats.**
  - **0.0–2.0.** RED hoods fall from the burnt web and trees, drifting down like leaves through the smoke.
  - **2.0–5.9.** L16: *"Every winter, the wolf chased a child off the path."* The wolf lies wounded in the snow, breathing. She walks to it.
  - **6.6–9.4.** L17: *"And every winter, the child ran back."* She kneels by the wolf.
  - **10.4–13.5.** L18: *"Because we'd all been taught... never leave the path."* On [never@12.21] she reaches out and touches its muzzle. Its eyes open.
- **OUT** (dissolve, 1.5 s).

### s10 · MONSTER · 14.0 s · the village, grey morning · film 2:05

- **IN.** The village gate in grey morning light. She walks home along the path. The wolf is far behind at the forest edge.
- **Beats.**
  - **1.5–4.0.** L19: *"When I walked home, nobody cheered."* Villagers in their doorways, silent.
  - **5.0–8.0.** L20: *"They looked at me like I was the monster."* They recoil and step back. Doors shut. Someone raises a lantern at her.
  - **8.0–14.0.** Her mother runs out, kneels and holds her tight (two silhouettes become one). At the forest edge the wolf turns away.
- **OUT** (dip to snow-white, 2.0 s). Years pass.

### s11 · GRANDMOTHER'S HOUSE · 15.0 s · decades later, dusk · film 2:19

- **IN.** From white: the cottage in the clearing, no web, a warm window. A NEW path of lanterns leads up to it from the forest.
- **Beats.**
  - **1.5–4.8.** L21: *"They told every child she was walking to her grandmother's house."* Old Red (long red cape, cane) at the door. The old wolf, grey-muzzled, lies by the step.
  - **6.0–7.5.** L22: *"So I became one."* She lights the last lantern by the door.
  - **7.5–13.0.** A small child in a red hood walks up the lantern path toward the cottage. Old Red raises a hand, and the old wolf lifts its head.
  - **10.4–13.0.** L23: *"Which path were you told never to leave?"* The camera cranes up over the forest: the lantern path is a line of light through the dark trees.
  - **13.0–15.0.** Flatten to Bass: the line of lanterns becomes the black path line on PAPER, and the small red triangle is at its end. Hold, then cut out.

## 5. Sound plan

- **Score.** Folk-lullaby melody (music box, then solo violin) in A minor, slowed and detuned as the path descends. Low choir drones for Grandmother.
  - The chase (s04, s05): pounding timpani and breath.
  - The fire (s08): the lullaby returns as a full, roaring orchestral statement.
  - Dawn (s09): solo violin.
  - End (s11): the music box, warm.
- **Ambience.** Village: wind, a dog, a creaking sign. The forest: snow hush, branch creaks, crows (s03).
  - **The silence on "quieter"** (s03 10.4) is a mix event: drop to near silence for 3 s.
- **Creatures.** The wolf: breath, low growl, paws in snow, the fight snarl. The spider: dry clicking and skittering, a thread creak as it descends, a hiss.
- **Sync hits.**

  | Scene | Hits |
  |---|---|
  | s02 | door closes ×3 |
  | s04 | the run; the wolf's skid |
  | s05 | the fall in snow |
  | s07 | the legs touch down |
  | s08 | the basket, a bottle roll and clink, the lantern smash, the WHOOSH of fire, crackle |
  | s09 | hoods falling, soft |
  | s10 | doors shutting |
  | s11 | lantern lighting |

- **Narration.** An old woman's memory, warm and dry. Duck music −6 dB under the voice. Mix target −14 LUFS integrated.
