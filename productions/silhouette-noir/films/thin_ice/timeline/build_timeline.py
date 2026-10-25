"""THIN ICE: timeline (wordless; twelve scenes, hard cuts on the beat).

    python3 films/thin_ice/timeline/build_timeline.py      (from the production root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from engine.timing import build, summary  # noqa: E402

FILM = "thin_ice"
SCENES = [
    ("s01", "title", 14.0, None),
    ("s02", "fence", 18.0, None),
    ("s03", "guard", 16.0, None),
    ("s04", "tracks", 16.0, None),
    ("s05", "river", 14.0, None),
    ("s06", "false_trail", 16.0, None),
    ("s07", "hunter", 14.0, None),
    ("s08", "ice", 14.0, None),
    ("s09", "choice", 14.0, None),
    ("s10", "scarf", 18.0, None),
    ("s11", "mercy", 18.0, None),
    ("s12", "other_side", 16.0, None),
]
PLACE = {}

if __name__ == "__main__":
    build(FILM, SCENES, PLACE)
    print(summary(FILM))
