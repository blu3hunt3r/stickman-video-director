"""RED cast: one Body and Look per character (the silhouette cards in docs/bible.md).

    from films.red import cast
    red = Actor(cast.RED_GIRL, cast.red(), x=..., ground=sets.ground_y)

The hood and cloak are the film's only red. Creatures (wolf, spider) are in engine.creatures.
"""
from engine.figure import Body, Look
from engine.palette import RED

RED_GIRL = Body.child(380)              # seven years old
MOTHER = Body.adult_f(590)
VILLAGER_M = Body.adult_m(620)
VILLAGER_F = Body.adult_f(585)
OLD_RED = Body.old_f(530)               # Red, sixty winters later
NEW_CHILD = Body.child(370)


def red(cloak=True):
    return Look(hood=True, cape="cloak" if cloak else None, dress="knee",
                colors={"hood": RED, "cape": RED})


def mother():
    return Look(hat="kerchief", dress="floor")


def villager_m(hat="flatcap"):
    return Look(hat=hat, coat="long")


def villager_f(hat="kerchief"):
    return Look(hat=hat, dress="floor")


def old_red():
    return Look(hood=True, cape="long", dress="floor", colors={"hood": RED, "cape": RED})


def new_child():
    return Look(hood=True, cape="capelet", dress="knee", colors={"hood": RED, "cape": RED})
