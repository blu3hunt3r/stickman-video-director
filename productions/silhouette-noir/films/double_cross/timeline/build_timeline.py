"""DOUBLE CROSS: timeline (wordless; eleven scenes, hard cuts on the beat).

    python3 films/double_cross/timeline/build_timeline.py      (from the production root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from engine.timing import build, summary  # noqa: E402

FILM = "double_cross"
SCENES = [
    ("s01", "title", 16.0, None),
    ("s02", "crew", 18.0, None),
    ("s03", "plan", 16.0, None),
    ("s04", "night", 12.0, None),
    ("s05", "guard", 18.0, None),
    ("s06", "safe", 14.0, None),
    ("s07", "cross", 20.0, None),
    ("s08", "locked", 12.0, None),
    ("s09", "plan_b", 22.0, None),
    ("s10", "checkmate", 18.0, None),
    ("s11", "end", 8.0, None),
]
PLACE = {}

if __name__ == "__main__":
    build(FILM, SCENES, PLACE)
    print(summary(FILM))
