"""OPPOSITE, the Bass cut: timeline (wordless film, one scene).

    python3 films/opposite_bass/timeline/build_timeline.py      (from the production root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from engine.timing import build, summary  # noqa: E402

FILM = "opposite_bass"
SCENES = [
    ("s01", "bass_cut", 36.0, None),
]
PLACE = {}

if __name__ == "__main__":
    build(FILM, SCENES, PLACE)
    print(summary(FILM))
