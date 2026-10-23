"""OPPOSITE timeline (wordless film: no narration lines).

    python3 films/opposite/timeline/build_timeline.py      (from the production root)

One continuous camera runs through both scenes (films/opposite/world.py, film time), so the
title flows into s02 without a transition: s01's last frame is s02's first.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from engine.timing import build, summary  # noqa: E402

FILM = "opposite"
SCENES = [
    ("s01", "title", 6.0, None),
    ("s02", "opposite", 26.0, None),
]
PLACE = {}

if __name__ == "__main__":
    build(FILM, SCENES, PLACE)
    print(summary(FILM))
