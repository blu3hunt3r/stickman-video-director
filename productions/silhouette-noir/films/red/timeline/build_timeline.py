"""RED timeline: the storyboard table from docs/bible.md, locked.

    python3 films/red/timeline/build_timeline.py      (from the production root)

Scene rows: (id, slug, duration_s, transition out of the scene). Narration rows: line number
-> (scene, scene-local start s). Change timing here, never by hand in timeline.json.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from engine.timing import build, summary  # noqa: E402

FILM = "red"
SCENES = [
    ("s01", "the_rule",      9.0, dict(kind="ink", dur=1.25)),
    ("s02", "the_hood",     15.0, dict(kind="dissolve", dur=1.5)),
    ("s03", "the_path",     14.0, dict(kind="dissolve", dur=1.0)),
    ("s04", "the_wolf",     14.0, dict(kind="whip", dur=0.5, direction="left")),
    ("s05", "deep_snow",    14.5, None),
    ("s06", "red_hoods",    14.5, dict(kind="flatten", dur=1.0, pal="red")),
    ("s07", "grandmother",  13.0, None),
    ("s08", "fire",         17.0, dict(kind="flash", dur=1.0, color=(1.0, 0.93, 0.85))),
    ("s09", "dawn",         14.0, dict(kind="dissolve", dur=1.5)),
    ("s10", "monster",      14.0, dict(kind="dip", dur=2.0, color=(0.95, 0.95, 0.94))),
    ("s11", "grandmother_house", 15.0, None),
]
PLACE = {
    1: ("s01", 1.4), 2: ("s01", 5.0),
    3: ("s02", 1.0), 4: ("s02", 8.4),
    5: ("s03", 6.2),
    6: ("s04", 1.0), 7: ("s04", 3.6),
    8: ("s05", 0.8),
    9: ("s06", 0.6), 10: ("s06", 4.0), 11: ("s06", 7.6),
    12: ("s07", 1.0),
    13: ("s08", 3.0), 14: ("s08", 8.0), 15: ("s08", 10.2),
    16: ("s09", 2.0), 17: ("s09", 6.6), 18: ("s09", 10.4),
    19: ("s10", 1.5), 20: ("s10", 5.0),
    21: ("s11", 1.5), 22: ("s11", 6.0), 23: ("s11", 10.4),
}

if __name__ == "__main__":
    build(FILM, SCENES, PLACE)
    print(summary(FILM))
