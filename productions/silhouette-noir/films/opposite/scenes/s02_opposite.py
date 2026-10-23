"""s02 · OPPOSITE: one continuous camera (no cuts) from her lit window (she sips from a mug,
hears them, walks to the glass) across the street to the quarrel and the knife (a crash
zoom), a whip back to her (the mug falls), the man at his
window pointing at her (the frame tilts), his run, a whip to her pulling her light's cord,
the wide diagram of the street (his descent, the red path, his climb), and into her dark
room: the line of light under the door, two feet, the handle, the keyhole, the eye. Hard
cut to black. The figures move on retargeted CMU motion capture (engine/mocap.py).

Beat times are film times in films/opposite/world.py (this scene starts at film 6.0).
"""
from engine import bass
from engine.timing import Cue
from films.opposite import world as Wd

T0 = 6.0


def render(f, t, T):
    bass.bass_scene(f, field=Wd.FIELD, paper=0.8, vignette=0.16, mottle=0.04)
    Wd.draw(f, T0 + t)


def motion_blur(t, T):
    return Wd.motion_blur_at(T0 + t)


def cues(T):
    s = lambda ft: ft - T0
    return [Cue(s(Wd.T_RAISE + 0.12), "her scream through his window", gain_db=-3),
            Cue(s(Wd.T_SLASH), "knife slash, string shrieks", gain_db=-6),
            Cue(s(Wd.T_SHATTER), "mug smashes on a wooden floor", gain_db=-10),
            Cue(s(Wd.T_HER_OFF), "light switch click, room tone drops", gain_db=-8),
            Cue(s(Wd.T_KNOB[0]), "door handle tried, twice", gain_db=-8),
            Cue(s(Wd.T_EYE), "low sting as the eye opens", gain_db=-6),
            Cue(s(Wd.T_BLACK), "hard cut to black, one low hit", gain_db=-6)]
