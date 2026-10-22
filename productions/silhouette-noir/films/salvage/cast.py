"""SALVAGE cast: one Body and Look per character (the silhouette cards in docs/bible.md).

    from films.salvage import cast
    diver = Actor(cast.DIVER, cast.diver(), x=..., ground=...)
    client = Actor(cast.CLIENT, cast.client(), ...)

Every scene builds its characters from here so they read the same in every shot.
"""
from engine import draw
from engine.figure import Body, Look, head_point
from engine.palette import SALVAGE

GLASS = (0.10, 0.20, 0.22)         # helmet port glass: a dark teal disc the eyes glow through

# ----------------------------------------------------------------------------- bodies
DIVER = Body.adult_m(620)                  # broad, heavy in the suit
CLIENT = Body.adult_m(640, shoulder_w=0.112)   # tall, square shoulders under the trench
CAPTAIN = Body.heavy_m(630)                # the father (flashback cut-outs and the photo)
BOY = Body.child(380)                      # the diver as a boy (the photo)


# ----------------------------------------------------------------------------- looks
def diver(helmet=True, weights=True, boots=True):
    """The diver. helmet=False: suited, bare-headed (on deck before the dive).
    weights/boots=False after he sheds them to rise (s13)."""
    return Look(helmet="diver" if helmet else None, hair=None if helmet else "short",
                shoes="lead" if boots else "shoe", limb_scale=1.32, gloves=True,
                opts={"glass": GLASS, "weights": weights, "collar": not helmet})


def cigar(ember=1.0):
    """Look extra: a cigar in the mouth with an emissive ember (ember 0..1.5: draw on it)."""
    def ex(ctx, sk, f, look):
        if sk.side_w > 0.85:                    # facing camera: the cigar points at us, skip
            return
        a = head_point(sk, 0.50, 0.24, front_x=0.10, front_y=0.22)
        b = head_point(sk, 0.86, 0.22, front_x=0.16, front_y=0.20)
        draw.capsule(ctx, a, b, 0.006 * sk.H, 0.0055 * sk.H)
        ctx.set_source_rgb(*SALVAGE.ink)
        ctx.fill()
        if ember > 0:
            with f.emit() as G:
                draw.circle(G, b, 0.006 * sk.H * (0.8 + 0.4 * ember))
                G.set_source_rgba(*SALVAGE.light, min(1.0, 0.6 + 0.4 * ember))
                G.fill()
    return ex


def client(ember=1.0, coat_flow=0.0):
    """The client: fedora, trench coat with the collar up, cigar. (The knife on his belt is a
    prop: films/salvage sets.)"""
    return Look(hat="fedora", coat="trench", extras=[cigar(ember)],
                opts={"collar": True, "flow": coat_flow})


def captain():
    return Look(hat="peaked", beard=True, coat="jacket")


def boy():
    return Look(hair="curly")
