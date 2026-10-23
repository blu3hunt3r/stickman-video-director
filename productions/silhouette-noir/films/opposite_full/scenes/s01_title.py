"""s01 · TITLE (0-12): placeholder while the scene is built (the section at rest)."""
from engine.timing import Cue
from films.opposite_full import kit as K


def render(f, t, T):
    K.scene_setup(f)
    with f.screen() as c:
        K.draw_section(c, t, numbers={K.HER_B: {4: K.PAPER}, K.HIS_B: {5: K.RED}})


def motion_blur(t, T):
    return 1


def cues(T):
    return []
