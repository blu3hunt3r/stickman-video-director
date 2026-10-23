"""s01 · OPPOSITE, the Bass cut: the whole film is one graphic sequence (see
films/opposite_bass/world.py for the beats). Film time = scene time.
"""
from engine import bass
from engine.timing import Cue
from films.opposite_bass import world as Wd


def render(f, t, T):
    bass.bass_scene(f, field=Wd.INK, paper=0.85, vignette=0.12, mottle=0.035)
    Wd.draw(f, t)


def motion_blur(t, T):
    return Wd.motion_blur_at(t)


def cues(T):
    return [Cue(Wd.T_TITLE_CUT, "red cut through the title", gain_db=-8),
            Cue(Wd.BOLTS[0], "the quarrel through glass, red zigzags on every shout", gain_db=-6),
            Cue(Wd.T_SLASH[0], "three cuts: violin shrieks, her scream", gain_db=-3),
            Cue(Wd.T_SMASH, "the mug smashes", gain_db=-6),
            Cue(Wd.T_GROW, "his arm grows across the street: braam", gain_db=-6),
            Cue(Wd.T_PULL, "light cord click, all dark", gain_db=-8),
            Cue(Wd.T_PATH + 0.3, "footsteps on every jump of the red line", gain_db=-8),
            Cue(Wd.T_KNOB[0], "the handle, twice", gain_db=-6),
            Cue(Wd.T_OPEN, "his eye opens: stinger", gain_db=-4),
            Cue(Wd.T_END, "title stamp, red cut, black", gain_db=-6)]
