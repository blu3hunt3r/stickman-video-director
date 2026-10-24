# Craft: how we direct these films

This is how we think when we make a film here: how we choose a story, what the pictures are made
of, how one shot hands off to the next, how the camera and the cut keep time, what the sound is for,
where we allow ourselves freedom and where we do not, and how we review. The examples come from the
films themselves, with film times (m:ss.ss). FILMS.md has the stories; SHOT_TYPES.md has the shot
vocabulary; SYSTEM.md has the machinery.

---

## 1. Choosing a story

### Wordless, so the picture has to carry it

The trilogy was narrated, and it leaned on the voice: long dim takes with a sentence doing the work.
When the user said "I dont like the way its been done", we stopped narrating. Since THE LANTERN every
film is wordless. That is a discipline more than a style: if a beat cannot be read from the picture
in one glance, the beat is not finished. It also changes what a story can be. We want stories whose
turns are actions you can see (a look, a slam, a tap on the floor), not facts someone has to say.

### A twist that is shown, not told

Both full films turn on a reversal you watch happen.

- **OPPOSITE.** The watcher becomes the watched. We never say it; at 2:01.5 the camera is over his
  shoulder (s10), looking out of her window, and she is standing in his lit window across the
  street with his phone at her ear. Her look flies to him (2:02.0), his to her (2:02.4), and the two
  sight lines meet tip to tip (2:02.82).
- **DOUBLE CROSS.** He crosses the crew; she had crossed him first. The proof is a frame we already
  saw. The rewind (1:48.15–1:50.75) runs the film backwards, catches at his slam, plays it forward
  (1:50.75–1:51.5) and freezes; a lens snaps round her chalk dot on the sewer line under the vault
  (1:51.5–1:52.2). The twist is not explained, it is replayed.

### Plants and payoffs, played fair

A twist only satisfies if the audience could have seen it coming. Every payoff in DOUBLE CROSS is
planted on screen earlier, usually hidden by something louder:

- The sewer branch is ruled running under the vault in the title (0:06.5). It pays off as the hollow
  knock (1:42.25) and the trapdoor (1:58.9).
- Her dot is laid at 0:34.75, in the same instant the Knight slams his piece down. Everyone is
  looking at him, and in the mix her chalk tap is buried under the thud. The rewind shows it.
- His slam in s02 (0:19.0) makes the other pieces jump. At the end her queen knocks his knight over
  quietly (2:19.85): the same gesture, reversed in force.
- The white title strip lands first and the red crosses over it (0:08.0, 0:08.5). At the end the X
  returns with the white over the red (2:21.5–2:22.0): she crossed him last.

We write the plants into the bible as a table before we draw anything (`films/double_cross/docs/BIBLE.md`,
"Plants and payoffs").

### An object that carries the story

Each film has a thing that the story runs through, so the audience can follow the plot by
following the object.

| Film | Object | What it carries |
|---|---|---|
| SALVAGE | the red air hose | the bond with the father; the client cuts it |
| RED | the red hood | a child offered; the hoods in the trees count the winters |
| THE LANTERN | the lantern | the only light; she thrusts it at the eyes |
| OPPOSITE | the knife, the mug, the telephone | the murder, her witness, her counter-move (she calls from his phone) |
| DOUBLE CROSS | the plan, the chalk, the chess pieces | the plan is the world; the pieces are the people; the queen takes the knight |

### The title says the theme

The title is not a label, it is the first statement of the idea. OPPOSITE splits into OPPO and SITE,
one half upside down. DOUBLE CROSS is an X made of a white strip and a red strip; the X lands on the
vault as the chalk X, and the film ends by lifting that X back into the title with the colours
swapped.

### Size and shape

The two full films are 2:24 (144 s) in 11 scenes of 8–20 s, cut to a 120 bpm grid. That gives us
about one story beat every bar or two, which suits a phone screen: big, readable, quick.

---

## 2. The visual language

### Saul Bass cut paper

Everything looks cut from paper with scissors and laid on a printed field. Edges are scissor-cut
(`bass.scissor`, `bass.cut_rect`, `bass.ring_pts`), fields are flat, colours are few, and nothing is
blurred. We borrow Bass's graphic ideas openly and on purpose:

- the Psycho bars that race across the black (OPPOSITE's title, 0:01.0 in the full film);
- North by Northwest's grid of windows, letters turning into architecture (the Bass cut's title);
- Vertigo's spiral and the fall into an eye (OPPOSITE full s04, her horror, from 0:44.5; the Bass
  cut's eye at 0:08.5);
- Anatomy of a Murder's cut-out figures, every limb a separate piece (the Bass cut's quarrel);
- The Man with the Golden Arm's jagged arm (the Bass cut at 0:18.5; THE LANTERN's legs).

The rule from the Bass cut's review still holds: scissor-cut must never mean low-poly. Big circles
get 48–96 facets.

### Silhouettes

People are ink silhouettes in profile, read by their outline: a hat brim, a bob, a chignon with a
pencil through it, a bowler and round spectacles. In DOUBLE CROSS each figure also has a rim in its
colour on the lit side (`C.RIM`: the Architect PAPER, the Knight RED, the Cracker GOLD, the Guard
STEEL), and the rim is the same colour as their piece on the plan, so the audience links person and
piece without being told. Limbs are staged off the body so a gesture reads.

### Palettes with jobs

A film gets a handful of named colours, and each colour has one job.

- DOUBLE CROSS: `BLUE` is the plan, `PAPER` is chalk, `NAVY` is night, `STEEL` is distance, `DEEP`
  is a dark room, `GOLD` is gold and lamplight, `RED` is the Knight and what he does, `POLICE` is the
  police light (s10 only), `INK` is every silhouette.
- OPPOSITE full: `AMBER` lamplight, `NIGHT` the teal exterior, `RED` him and what he does, `POLICE`
  in s10 only.
- The trilogy: one red per film, given to story objects only, kept to about 8 % of the frame in
  live scenes so it burns (`STYLE.md` rule 5).

When a colour means a person, it means that person everywhere: in DOUBLE CROSS his look, his route,
his piece, the alarm, the arrest ring and the ruby's glow are all RED. That is why the ruby's red
light leaking through her fingers (2:18.45) reads as a victory: she has taken the colour from him.

### Grain and paper

The print look comes from `Frame.finish()`, never from drawing: paper fibres, a light ink mottle, a
whisper of vignette, and grain that changes on twos (`grain_fps = 12`) to match figures animated on
twos. Light is the only translucent thing (lamp pools, the flashlight cone, the match, the tracing
paper), as flat tints.

### Twos and ones

Figures move on twos (12 drawings a second, `K.twos(t)`), like stop-motion paper; graphics, routes
and the camera move on ones. The contrast is part of the look: hand-made people in a precise world.

---

## 3. Connections: how one shot hands off to the next

The user's favourite thing about OPPOSITE full was "the way you are connecting things". These are
the ways we do it.

### Match cuts on a point

Two shots share a point, a shape or a motion, and the cut lands on it.

- **s01 → s02 (0:12.0).** The title's X shrinks onto the vault and lands as the plan's chalk X
  (0:11.0) while the camera tilts down to the table; s02 opens on that table.
- **s03 → s04 (0:40.0).** The camera is still moving at the cut: s03 ends with its elevation falling
  at 15° a second, and s04 starts from the same camera (`P.HANDOFF_34`) at the same rate.
- **The dial (1:33.0).** s07's red close-up of the dial shrinks into a lens and closes onto the
  plan's chalk dial in the same place, and the camera glides off after the red knight.
- **s08 → s09 (1:48.0).** s08 ends with her tracing sheet held up to the match; s09 holds that exact
  frame (s08 drawn at its last moment, 12.0, from s09's `FREEZES` table) before the rewind starts.
- **s10 → s11 (2:16.0).** The two routes straighten into an X (2:14.0–2:15.2); s11 splits s10's last
  frame along that X and the pieces fly apart onto her fist.
- **THE LANTERN (0:06.0).** The title's flame is the iris the forest opens through.
- **OPPOSITE full s01 → s02 (0:12.0).** The push-in on her room ends where s02's first frame begins,
  drawn with the real set so the room matches.

### Eyelines and leader lines

A look is drawn: dots fly from the eye to what it sees, led by an arrowhead, then march while the
look lasts (`K.sight_line`). Her looks are PAPER, his are RED. In DOUBLE CROSS s02 his red look goes
down to the X (0:21.6) and her white look goes across to him (0:22.5); nothing else is needed for
the audience to know she has seen him. A **lens on a leader line** (`K.callout`) joins a detail to
its place: in s02 each face is joined to its piece on the plan; in s08 (1:43.25) a lens joins the
glowing dot under her heel to the dot on the plan.

### Numbered callouts

The plan's steps are circled numerals ① to ⑤, chalked as she explains the route in s03. When the
crew carries out a step in the world, the same numeral is circled on the world: step ③ in s05
(1:01.65), step ④ in s06 (1:15.0), the step marks on the section in s04. Plan B's steps are solid
discs where Plan A's are rings, so the two plans never get confused.

### Chalk as the thread

The chalk route stays on screen when the plan becomes the world: in s04 the dotted route is a ghost
layer on the street and its dots brighten as the crew reaches them. The heist stopwatch (top right
from 0:46.0) ties s04–s07 into one continuous clock, stops dead when he crosses them (1:33.5) and
spins back in the rewind.

### The plan as a map

The single most useful idea in DOUBLE CROSS: the plan is the world seen from above, and the world is
the plan seen from the side. So the film can tilt between them instead of cutting: down into the
street (s03 → s04), up into the stealth map (0:56.0) and back down (1:00.5), up into the plan for his
L (1:33.0). Later the same top view becomes Plan B's overlay (1:54.6) and the city as a chessboard
(2:06.92), where the police cars move like rooks.

---

## 4. Camera grammar

- **One camera idea per film.** DOUBLE CROSS has the TILT (`P.PlanCam`). OPPOSITE full has the
  elevation and the section of two buildings. THE LANTERN and OPPOSITE v1–v3 have one continuous
  camera.
- **Each angle is chosen for a reason.** Profile close-ups for faces (the three cameos in s02; her
  calm eye in s08 at 1:39.9). Extreme close-ups for mechanisms (the dial and the lock cutaway in s06,
  1:09.0–1:16.0). Sections to show what is under the ground (s04's street opening into the sewer at
  0:45.75; s09's floor cut away at 2:00.66). Elevation for a corridor (s05). Top-down for strategy
  (s05's stealth map, s10's chessboard).
- **Moves are eased, never linear.** Push-ins either snap on the beat or glide. The trilogy rule
  (`STYLE.md` rule 7) still holds: slow, continuous, eased starts and stops.
- **The Dutch tilt is for panic only, once.** OPPOSITE full rolls to -7° as she reels (s04, from
  0:44.6). DOUBLE CROSS rolls once, when the red ring snaps round the Knight (2:10.0–2:10.42).
- **Shake is earned by an impact.** In s08 the camera shakes with each blow of the Cracker's fists
  (1:38.85, 1:39.3, 1:39.75) and dust falls from the door.
- **Whips follow a look.** In s08 the camera whips down after her glance to the floor
  (1:41.1–1:41.35); in s09 it whips from one Plan B chalk mark to the next.

---

## 5. Rhythm

- **One clock.** Picture and score share 120 bpm: a beat is 0.5 s, a bar is 2 s, every scene starts
  on a bar line. Snaps land on beats; hard cuts land on beats.
- **Stagger.** Repeated actions take one beat each so the eye can count them: the bank's parts rule
  in one per beat (0:04.0–0:07.0); the pieces hop along the route; the four police cars slide in on
  2:08.0, 2:08.5, 2:09.0, 2:09.5. When we want urgency we halve it: Plan B's cars arrive on half
  beats (1:57.15–1:57.75).
- **Anticipation and settle.** Snaps use `outback`; the stopwatch's hand snaps to each tick with a
  short settle (`K.heist_beats`).
- **Holds and black.** The strongest beats get air. In v1 the vault door's BOOM (1:32.0) cut to black
  for 0.2 s while the bolts shot home in the dark. In v2 we spend those frames differently: two flat
  red frames, then five of the Knight cut out against a red sunburst (1:32.00–1:32.29), so the stop
  also says who did it. s08 opens on black and breath for almost a second before the first spark
  (1:36.85). The film ends on black with the red dot alive a breath longer
  (2:23.5–2:23.9).
- **Density.** Big, readable ideas rather than a constant stream (the restart pitch asked for about
  10–12 big readable shots in a short film): each beat must read in one glance at phone size.

---

## 6. Sound

- **The score tells the story's structure.** DOUBLE CROSS's theme is heard plainly while the plan is
  made (s02–s03); at the betrayal it returns in exact mirror inversion, low and minor (from 1:24), and
  its close lands with the vault door's BOOM on the bar line (1:32.0); after the rewind it returns
  inverted again, upright, in D major. You can hear the double cross even with your eyes closed.
- **Diegetic sound becomes music.** The stopwatch is a woodblock on every beat (0:46.0–1:33.5). The
  lock's gates click on D, F and A, the notes of the key chord. The police stabs rise a semitone per
  car, and the sirens are tuned D to A.
- **Silence is punctuation.** In s05 the score drops away to the tick and the building's hum while
  the crew hides; after the stethoscope's clank it "holds its breath" on one low note. In s02 the band
  stops on a held low D at 0:22.0, the moment she knows. Once the picture is black (2:23.5) the sound
  is digital silence.
- **Every visible event has a sound.** Scenes write their own cues in plain words (`Cue(t, "a fist on
  the vault door: a huge muffled steel BOOM", ...)`), and the mix answers every one, either by design
  or by spotting it from its words.
- **Sound can hide a plant.** The chalk tap that leaves her dot (0:34.75) is mixed under the Knight's
  thud, exactly as the picture hides it under his slam.
- **The film's own sound is material.** The rewind plays the film's mix backwards, so what you hear
  rewinding is what you heard happening.
- **Loudness is fixed.** Every wordless film is mastered to -16 LUFS integrated under a true-peak
  limiter (ceiling -1.0 dBTP in the tests, -1.2 in OPPOSITE full, -1.3 in DOUBLE CROSS).
- **Spend nothing new without asking.** Paid generation (Magnific) is for voice and sound only, and
  only after telling the user. DOUBLE CROSS used none: everything is synthesised or reused from
  OPPOSITE's recordings.

---

## 7. Freedom and its limits

We take a lot of freedom inside a film: new devices for each story (the X-split, the tracing paper,
the rewind, the city as a chessboard), new references, new rhythms, a scene re-timed when a beat
needs more air. The limits are what keep that freedom from turning into noise.

- **No lettering in a wordless film.** The only text in picture is the title and hand-cut numerals
  (the plan's step numbers, floor numbers, the dial). No captions, no labels, no sound words.
- **Palette discipline.** No new hues, no gradients. `POLICE` appears only in s10. If a moment seems
  to need a new colour, it needs a better idea instead.
- **Devices keep their meaning.** In DOUBLE CROSS the red marker ring is used once only, for the
  arrest; in OPPOSITE full there are exactly three rings, and they trace the story (the knife, her
  window, him). A device used for decoration stops meaning anything.
- **Effects come from the film's own materials.** A flash is a flat colour from the palette, a
  glitch is paper strips slipping, a speed effect is cut-paper wedges. That is why, when the user
  shared a reference of manga-style shot types, we adapted some and refused others (SHOT_TYPES.md,
  Part B).
- **One red belongs to one person.** The accent is never spent on decoration.

---

## 8. Review discipline

- **Look at real frames at full size.** Contact sheets find problems; full-size stills confirm them.
  Hands, eyes, seams, small dots and edges only show their faults at scale 1.0.
- **One glance per beat.** At phone size, with the sound off, can you tell what happened? If not, the
  beat is not done.
- **Dense sheets for motion.** We cannot watch video in the session, so we judge motion from 16-frame
  windows: no popping, no sliding feet, smooth camera, readable arcs.
- **Measure what can be measured.** The mix's QA report (loudness, peaks, clicks, missed cues, sync),
  the glitch scan (every one of DOUBLE CROSS v1's 27 flags was checked and was deliberate), the red
  share.
- **The user's notes are briefs.** Each note changed the system, not just the shot:
  - "more noises and screams … the range of motion should be a little more clear … the way you
    change the camera angles": OPPOSITE v2's crash zooms, whips and screams;
  - "where are footsteps … why the scream at the end … is that a glass … why is the person not moving
    towards the window … the fight looks very bad": OPPOSITE v3's motion capture, footsteps and mug;
  - "is this deep Saul Bass": the Bass cut, and the house style since;
  - "little flaws … from hand shape of the lady drinking … proper in-depth review": two full review
    passes on the Bass cut;
  - "connecting things and camera motion and sound effects": DOUBLE CROSS's plan-as-map and its
    joined-up sound.
- **Fix causes, then neighbours.** A fix to a scene another scene imports (s06's dial, s02 and s03, s08's
  last frame) means re-checking the importer.
- **Nothing is committed unreviewed.** Agents never commit; the director looks at the frames first.
