"""THE LANTERN timeline (wordless film: no narration lines).

    python3 films/lantern/timeline/build_timeline.py      (from the production root)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from engine.timing import build, summary  # noqa: E402

FILM = "lantern"
SCENES = [
    ("s01", "title", 6.0, dict(kind="iris", dur=1.0, mode="open", center=(540.0, 1040.0), ring=0.0)),
    ("s02", "into_the_woods", 20.0, None),
]
PLACE = {}

if __name__ == "__main__":
    build(FILM, SCENES, PLACE)
    print(summary(FILM))
