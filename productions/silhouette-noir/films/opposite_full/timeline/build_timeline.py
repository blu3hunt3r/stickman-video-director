"""OPPOSITE, the full Bass cut: timeline (wordless; eleven scenes, hard cuts on the beat).

    python3 films/opposite_full/timeline/build_timeline.py      (from the production root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from engine.timing import build, summary  # noqa: E402

FILM = "opposite_full"
SCENES = [
    ("s01", "title", 12.0, None),
    ("s02", "amber", 14.0, None),
    ("s03", "quarrel", 14.0, None),
    ("s04", "knife", 12.0, None),
    ("s05", "seen", 14.0, None),
    ("s06", "dark", 10.0, None),
    ("s07", "crossing", 14.0, None),
    ("s08", "door", 14.0, None),
    ("s09", "call", 12.0, None),
    ("s10", "opposite", 20.0, None),
    ("s11", "end", 8.0, None),
]
PLACE = {}

if __name__ == "__main__":
    build(FILM, SCENES, PLACE)
    print(summary(FILM))
