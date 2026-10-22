# Silhouette Noir: the style contract

This is a trilogy of vertical (1080×1920, 24 fps) thriller shorts: **SALVAGE**, **SHADOW PLAY** and **RED**.
All three share one look: **Saul Bass title design × Limbo × Inside**. Every scene, set,
creature and graphic follows these rules. Read them before you draw anything.

1. **Silhouettes, not drawings.**
   - Every character, creature, prop and set piece is a filled shape in the film's ink (`pal.ink`).
   - It is read by its outline. Do not draw interior detail lines, strokes for form, or outlines around shapes.
   - Detail lives in the outline: a hat brim, a hood point, helmet ports, a coat flare, fingers when they matter, holes you can see light through.

2. **Depth comes from fog.**
   - Farther layers are drawn in ink, then fogged and blurred: `f.layer(par, blur, fog)`. The layer applies `pal.fog_at(fog)` and depth-of-field blur.
   - Typical stack, back to front:
     1. Sky or backdrop.
     2. Two to four far layers (`par` 0.2–0.7, fog 0.85→0.35, blur 8→2).
     3. Haze bands (`f.haze`).
     4. The **action plane** (`par` 1, sharp, pure ink).
     5. Foreground occluders (`par` 1.3–1.8, blur 12–24, pure ink, framing the shot).
   - Never fog the action plane. Silhouettes at different depths must separate by tone.

3. **Light.** Apart from the accent, light is the only "color".
   - Use additive beams, shafts and glows with `f.light()`, and emissive cores (eyes, bulbs, windows, flames, a cigar tip) with `f.emit()`.
   - Light is warm amber (`pal.light`) unless the palette names another light: moon, police blue, lightning, dawn.
   - **Backlight the action plane.** A silhouette reads best against the brightest part of the frame, so put the brightest fog or light behind the subject.

4. **Eyes.**
   - People and the wolf have Limbo eyes: two small bright dots with a soft halo. See `figure.draw_eyes`, and the `eyes` dict on a Pose.
   - The eyes are the face. Opening and closing them (`open`), dimming them (`glow`) and moving the gaze (`look`) are your acting tools.
   - Eyes vanish when a figure turns its back.

5. **RED** (`palette.RED` = (0.84, 0.10, 0.09)) is the trilogy's only accent, and it belongs to story objects only:

   | Film | What may be red |
   |---|---|
   | SALVAGE | the diver's air hose / line; the flashback cut-paper graphics |
   | SHADOW PLAY | her coat; the paper blood; the police light's red half |
   | RED | the hoods (hers, her cloak, the hoods hanging at the house); the cut-paper title and graphics |

   - Never use red for anything else, and never introduce other saturated hues.
   - In live scenes keep red small (about 8 % of the frame or less) so it burns.

6. **Saul Bass graphics.** Interludes, titles and transitions are flat cut paper:
   - **Shapes:** hard-edged geometry (bars, circles, spirals, jagged arms, pointing hands, silhouette cut-outs).
   - **Edges:** scissor-cut (`draw.cut_paper`, `draw.cut_circle`).
   - **Fields:** flat `PAPER`, ink and `RED`.
   - **Finish:** paper texture (`f.post['paper']`) and posterize (`f.post['poster']`).
   - **Movement is graphic:** shapes slide, snap, rotate, stack, split and multiply. Use staggered timing and crisp eases (`out3`, `inout5`, `outback`). Nothing goes mushy.
   - **Titles** are hand-cut letters (Inter Display Black, roughened), slightly misaligned. They must never look typed.

7. **Camera (9:16).**
   - Compose vertically. Favor vertical journeys: descents, ascents, cranes, tilts.
   - Favor tall frames: sky above and abyss below, a figure small in a tall space, splits by a waterline or rows of windows.
   - Keep key action inside the safe area `SAFE = (90, 240, 990, 1500)`.
   - Moves are slow and continuous, with eased starts and stops (never linear). Tense moments get a gentle drift (`Camera.shaken`, 4 px or less).
   - **A scene is one continuous shot** unless the bible says otherwise. Continuity comes from moving through one world.

8. **Motion is weighty and physical** (Inside).
   - Anticipation, follow-through and settle.
   - Feet plant without sliding: use `engine.motion`.
   - Stage actions in profile, and keep acting limbs off the torso so the silhouette reads.

9. **Texture.**
   - Grain, vignette, bloom, flicker and the grade come from `Frame.finish()`. Do not add your own.
   - No text in picture except the Bass titles and graphics the bible specifies. Captions are added in post.

10. **Performance.**
    - A full-resolution frame (scale 1.0) should render in about 1.5 s or less on one core. Each blurred layer costs roughly 30–60 ms.
    - Cache static geometry.
    - Everything must be deterministic: a pure function of `t` and seeds. Use `core.hash01` / `noise1` / `noise2`, never unseeded `random`.

## Units and conventions

- **World units** are frame pixels at camera zoom 1, with y pointing down.
- `f.t` is scene-local time in seconds.
  - Scenes may be asked for `t < 0` and `t > T`. These are handles for composited transitions, and the scene should keep animating naturally through them.
- **Palettes** live in `engine/palette.py`. Use `pal.ink`, `pal.fog_at(d)`, `pal.shade(d)` and `pal.light`, never ad-hoc colors.
- **Human scale:** an adult is about 600 px tall at zoom 1, and a 7-year-old about 380 px.
