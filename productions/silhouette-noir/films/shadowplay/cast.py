"""SHADOW PLAY cast: one Body and Look per character (the silhouette cards in docs/bible.md).

    from films.shadowplay import cast
    her = Actor(cast.HER, cast.her(coat=True), x=..., ground=...)

The killer is Magritte's man: bowler hat and a long coat. The paper dolls are the same rig in
paper-doll mode (Look(paper=True)): cut-paper edges, pin joints, no eyes.
"""
from engine.figure import Body, Look
from engine.palette import RED, PAPER

HER = Body.adult_f(590)                            # the watcher
HIM = Body.adult_m(650, shoulder_w=0.102)          # the killer: tall and narrow
DANCER = Body.adult_f(580)                         # window 4
CAT_LADY = Body.old_f(540)                         # window 12
CRIER = Body.adult_f(585)                          # window 30
COP = Body.adult_m(630)
DOLL_MAN = Body.adult_m(600)                       # the paper dolls (drawn small, on rods)
DOLL_WOMAN = Body.adult_f(580)


def her(coat=False, hair="bob"):
    """At home: bare silhouette, bob hair. coat=True: the red coat (s06 onward)."""
    if coat:
        return Look(hair=hair, coat="trench", shoes="heel", colors={"coat": RED}, opts={"collar": True})
    return Look(hair=hair, shoes="heel")


def him(coat_flow=0.0):
    return Look(hat="bowler", coat="long", opts={"flow": coat_flow})


def dancer():
    return Look(hair="ponytail", dress="knee")


def cat_lady():
    return Look(hair="bun", dress="mid")


def crier():
    return Look(hair="long")


def cop():
    return Look(hat="peaked", coat="jacket")


def doll_man(ink=PAPER):
    """A paper doll as an object (pale paper). Its SHADOW on the sheet uses ink=None."""
    return Look(hat="bowler", coat="jacket", paper=True, eyes=False, ink=ink)


def doll_woman(ink=PAPER):
    return Look(hair="bob", dress="knee", paper=True, eyes=False, ink=ink)
