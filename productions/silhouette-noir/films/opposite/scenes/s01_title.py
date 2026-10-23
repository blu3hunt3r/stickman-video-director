"""s01 · TITLE: North by Northwest grid lines slide in, the two facades rise out of the
street, OPPOSITE rides in along its rule, the windows light one by one in rhythm, and the
camera pushes toward her window (it keeps going into s02: one continuous camera).

The world, the light schedule and the camera live in films/opposite/world.py (film time).
"""
from engine import bass
from engine.timing import Cue
from films.opposite import world


def render(f, t, T):
    bass.bass_scene(f, field=world.FIELD, paper=0.8, vignette=0.16, mottle=0.04)
    world.draw(f, t)


def motion_blur(t, T):
    return world.motion_blur_at(t)


def cues(T):
    return [Cue(0.1, "grid lines sliding in: soft paper swishes", gain_db=-14, dur=1.4),
            Cue(1.3, "buildings rising: low wooden thuds", gain_db=-12, dur=1.0),
            Cue(2.7, "window lights clicking on in rhythm", gain_db=-14, dur=1.5)]
