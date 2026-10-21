"""Nobody Has a Face - Style 1 Dark noir stickman engine.

Typical scene module imports:
    from engine import *            # core, Camera, Light, Frame, draw, rig, props, fx, sets, Cue
"""
from .core import *  # noqa: F401,F403
from .frame import Camera, Light, Frame  # noqa: F401
from .timing import SceneTiming, Cue, timeline  # noqa: F401
from . import draw, rig, props, fx, sets  # noqa: F401
from .rig import Pose  # noqa: F401
