"""SHADOW PLAY timeline: the storyboard table from docs/bible.md, locked.

    python3 films/shadowplay/timeline/build_timeline.py      (from the production root)

Scene rows: (id, slug, duration_s, transition out of the scene). Narration rows: line number
-> (scene, scene-local start s). Change timing here, never by hand in timeline.json.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from engine.timing import build, summary  # noqa: E402

FILM = "shadowplay"
SCENES = [
    ("s01", "forty_windows", 9.0, dict(kind="flatten", dur=1.0, pal="shadowplay")),
    ("s02", "the_watcher",  15.0, dict(kind="shape", dur=1.0, invert=True, shape="binocular",
                                                 shape_args=dict(center=(540, 960), r=300, sep=330, seed=0))),
    ("s03", "window_nine",  17.0, None),
    ("s04", "nothing",      11.5, dict(kind="bars", dur=1.0, n=2, axis="h", color=None)),
    ("s05", "again",        14.0, dict(kind="slash", dur=0.75)),
    ("s06", "crossing",     13.0, dict(kind="shape", dur=1.0, shape="window",
                                                 shape_args=dict(rect0=(444, 840, 636, 1080)))),
    ("s07", "the_show",     12.5, None),
    ("s08", "other_side",   14.5, dict(kind="dip", dur=0.75, color=(0.0, 0.0, 0.0))),
    ("s09", "ninety_seconds", 14.0, None),
    ("s10", "the_trap",     11.0, dict(kind="tear", dur=1.0)),
    ("s11", "forty_dolls",  10.0, dict(kind="dissolve", dur=1.25)),
    ("s12", "mostly",       12.0, None),
]
PLACE = {
    1: ("s01", 1.5), 2: ("s01", 5.6),
    3: ("s02", 0.8), 4: ("s02", 7.8), 5: ("s02", 10.6),
    6: ("s03", 0.6), 7: ("s03", 4.8), 8: ("s03", 13.0),
    9: ("s04", 0.8), 10: ("s04", 6.2),
    11: ("s05", 0.8), 12: ("s05", 6.0), 13: ("s05", 10.6),
    14: ("s06", 0.8), 15: ("s06", 4.6),
    16: ("s07", 1.4), 17: ("s07", 7.6),
    18: ("s08", 1.0), 19: ("s08", 6.0), 20: ("s08", 9.0), 21: ("s08", 11.6),
    22: ("s09", 0.6), 23: ("s09", 4.0), 24: ("s09", 10.6),
    25: ("s11", 1.0), 26: ("s11", 6.0),
    27: ("s12", 1.0), 28: ("s12", 4.2), 29: ("s12", 7.2),
}

if __name__ == "__main__":
    build(FILM, SCENES, PLACE)
    print(summary(FILM))
