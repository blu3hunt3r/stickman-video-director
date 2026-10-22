"""SALVAGE timeline: the storyboard table from docs/bible.md, locked.

    python3 films/salvage/timeline/build_timeline.py      (from the production root)

Scene rows: (id, slug, duration_s, transition out of the scene). Narration rows: line number
-> (scene, scene-local start s). Change timing here, never by hand in timeline.json.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from engine.timing import build, summary  # noqa: E402

FILM = "salvage"
SCENES = [
    ("s01", "red_line",    10.0, dict(kind="scroll", dur=1.5, direction="up")),
    ("s02", "cash",        15.0, dict(kind="scroll", dur=1.25, direction="down")),
    ("s03", "descent",     14.0, dict(kind="flatten", dur=1.0)),
    ("s04", "calm_night",  14.0, dict(kind="ink", dur=1.25)),
    ("s05", "meridian",    13.5, dict(kind="whip", dur=0.5, direction="left")),
    ("s06", "outward",      8.0, None),
    ("s07", "the_price",   11.5, dict(kind="bars", dur=1.0, n=7, orient="h")),
    ("s08", "shaft",       10.0, None),
    ("s09", "birthday",     9.0, dict(kind="dissolve", dur=0.75)),
    ("s10", "own_hand",    10.0, None),
    ("s11", "two_tugs",    10.0, dict(kind="scroll", dur=1.25, direction="up")),
    ("s12", "the_cut",      9.5, dict(kind="scroll", dur=1.0, direction="down")),
    ("s13", "one_breath",  11.0, dict(kind="scroll", dur=1.0, direction="up")),
    ("s14", "the_bell",    11.0, None),
    ("s15", "my_name",      9.0, dict(kind="dip", dur=2.0, color=(0.0, 0.0, 0.0))),
    ("s16", "sea_keeps",   16.0, None),
]
PLACE = {
    1: ("s01", 1.0), 2: ("s01", 5.3),
    3: ("s02", 1.2), 4: ("s02", 7.0), 5: ("s02", 10.0),
    6: ("s03", 10.6),                       # runs over the cut into the s04 graphic
    7: ("s04", 7.8),
    8: ("s05", 1.4), 9: ("s05", 10.4),
    10: ("s06", 0.8),
    11: ("s07", 1.2), 12: ("s07", 6.4),
    13: ("s08", 4.6),
    14: ("s09", 0.8),
    15: ("s10", 0.8),
    16: ("s11", 0.6),
    17: ("s12", 0.8),
    18: ("s13", 1.5), 19: ("s13", 8.2),
    20: ("s14", 1.0), 21: ("s14", 6.4),
    22: ("s15", 1.6), 23: ("s15", 5.2),
    24: ("s16", 1.6), 25: ("s16", 8.6),
}

if __name__ == "__main__":
    build(FILM, SCENES, PLACE)
    print(summary(FILM))
