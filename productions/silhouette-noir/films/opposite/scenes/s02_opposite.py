"""s02 · OPPOSITE: one continuous camera (no cuts) from her lit window across the street to
the quarrel and the knife, back to her (the cup falls), the man at his window pointing at
her, her light off, the wide diagram of the street (his descent, the red path, his climb),
and into her dark room: the line of light under the door, two feet, the handle, the keyhole,
the eye. Black.

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
    return [Cue(s(Wd.T_SLASH), "knife slash, string stab", gain_db=-6),
            Cue(s(Wd.T_SHATTER), "cup shatters on a wooden floor", gain_db=-10),
            Cue(s(Wd.T_HER_OFF), "light switch click, room tone drops", gain_db=-8),
            Cue(s(Wd.T_KNOB[0]), "door handle tried, twice", gain_db=-8),
            Cue(s(Wd.T_EYE), "low sting as the eye opens", gain_db=-6)]
