"""THE LANTERN cast. The girl (about nine) carries the lantern; her scarf is the film's red.

    girl = Actor(cast.GIRL, cast.girl(), x=..., ground=sets.ground_y)
"""
from engine.figure import Body, Look
from engine.palette import RED

GIRL = Body.child(400)          # about nine years old
BROTHER = Body.child(330)       # about five


def girl():
    return Look(hair="ponytail", dress="knee", scarf=True, shoes="boot",
                colors={"scarf": RED}, opts={"flow": 0.6})


def brother():
    return Look(hair="curly", coat="jacket")
