"""Film palettes. Every film is a monochrome world (ink silhouettes against fog and light)
plus ONE story accent (red) and at most one light accent. Never invent new hues in a scene:
take them from the film's palette.

Colors are RGB tuples 0..1. `fog_at(depth01)` gives the atmospheric color for a layer
(0 = touching the camera plane, 1 = the far distance).
"""
from .core import lerp, clamp

# The trilogy's shared accent: a Saul Bass vermilion-crimson. Same red in all three films.
RED = (0.84, 0.10, 0.09)
PAPER = (0.94, 0.91, 0.84)      # Saul Bass off-white paper (graphic interludes only)
BLACK = (0.0, 0.0, 0.0)


class Palette:
    def __init__(self, name, **kw):
        self.name = name
        self.__dict__.update(kw)

    def fog_at(self, depth01):
        """Atmospheric color for a layer at normalized depth (0 near .. 1 far)."""
        stops = self.fog_stops
        d = clamp(depth01)
        for (d0, c0), (d1, c1) in zip(stops, stops[1:]):
            if d <= d1:
                return lerp(c0, c1, (d - d0) / max(d1 - d0, 1e-6))
        return stops[-1][1]

    def shade(self, depth01, k=1.0):
        """Silhouette fill for an object at depth01: ink blended toward the fog."""
        return lerp(self.ink, self.fog_at(depth01), clamp(k * self.haze(depth01)))

    def haze(self, depth01):
        """How much of the fog covers an object at depth01 (0 = pure ink)."""
        return clamp(depth01) ** self.haze_gamma


# --------------------------------------------------------------------------- SALVAGE
# Underwater: aqua at the surface, teal mid-water, ink-black in the deep. The helmet lamp,
# cigar and moon are the warm light accent; the air hose / flashback graphics are RED.
SALVAGE = Palette(
    "salvage",
    ink=(0.006, 0.016, 0.022),
    sky_top=(0.10, 0.13, 0.17), sky_bottom=(0.33, 0.37, 0.40),      # night sky over the sea
    surface=(0.50, 0.74, 0.76),                                       # sunlit water just under the surface
    mid=(0.07, 0.25, 0.29),
    deep=(0.010, 0.040, 0.052),
    fog_stops=[(0.0, (0.03, 0.10, 0.12)), (0.5, (0.07, 0.25, 0.29)), (1.0, (0.16, 0.42, 0.45))],
    haze_gamma=0.8,
    light=(1.0, 0.74, 0.42),          # helmet lamp / cigar / lantern: warm amber
    moon=(0.92, 0.94, 0.88),
    accent=RED,
    paper=PAPER,
    grade=dict(lift=(0.000, 0.010, 0.014), gain=(0.97, 1.0, 1.0), gamma=(1.04, 1.0, 0.98)),
    grain=0.045, vignette=0.55,
)

# --------------------------------------------------------------------------- SHADOW PLAY
# Night city in the rain. Windows are warm amber light boxes; everything else is blue-black.
# RED is her coat, the paper blood and the police light; police blue is the cold light.
SHADOWPLAY = Palette(
    "shadowplay",
    ink=(0.010, 0.010, 0.016),
    sky_top=(0.020, 0.026, 0.045), sky_bottom=(0.070, 0.080, 0.115),
    fog_stops=[(0.0, (0.03, 0.035, 0.05)), (0.6, (0.08, 0.09, 0.12)), (1.0, (0.15, 0.16, 0.20))],
    haze_gamma=0.9,
    light=(1.0, 0.76, 0.45),          # window light / lamp: warm amber
    lamp_hot=(1.0, 0.90, 0.72),
    rain=(0.62, 0.66, 0.74),
    lightning=(0.86, 0.90, 1.0),
    police=(0.20, 0.42, 1.0),
    accent=RED,
    paper=PAPER,
    grade=dict(lift=(0.004, 0.006, 0.014), gain=(1.0, 0.98, 0.97), gamma=(1.0, 1.0, 0.97)),
    grain=0.05, vignette=0.6,
)

# --------------------------------------------------------------------------- RED
# Winter forest, Limbo greyscale: white fog and snow, ink trees. RED is the hood (and the
# hoods in the trees); firelight amber is the only other color (lanterns, torches, fire).
RED_FILM = Palette(
    "red",
    ink=(0.012, 0.012, 0.012),
    sky_top=(0.60, 0.61, 0.61), sky_bottom=(0.86, 0.86, 0.85),
    fog_stops=[(0.0, (0.30, 0.30, 0.30)), (0.45, (0.62, 0.62, 0.62)), (1.0, (0.90, 0.90, 0.89))],
    haze_gamma=0.75,
    snow=(0.95, 0.95, 0.94),
    light=(1.0, 0.62, 0.26),          # firelight / lantern amber
    dawn=(0.90, 0.80, 0.74),
    accent=RED,
    paper=PAPER,
    grade=dict(lift=(0.008, 0.008, 0.008), gain=(1.0, 1.0, 0.99), gamma=(1.0, 1.0, 1.0)),
    grain=0.06, vignette=0.65,
)

# --------------------------------------------------------------------------- THE LANTERN
# Limbo sepia-grey forest, no snow. Mid-grey fog keeps frames readable (never murky black);
# the lantern's amber pool is the only warm light. RED is the girl's scarf and the Bass titles.
LANTERN = Palette(
    "lantern",
    ink=(0.020, 0.018, 0.016),
    sky_top=(0.50, 0.48, 0.43), sky_bottom=(0.80, 0.77, 0.70),
    fog_stops=[(0.0, (0.26, 0.25, 0.23)), (0.45, (0.50, 0.48, 0.44)), (1.0, (0.78, 0.75, 0.69))],
    haze_gamma=0.75,
    light=(1.0, 0.72, 0.38),          # the lantern: warm amber
    flame=(1.0, 0.88, 0.62),
    accent=RED,
    paper=PAPER,
    grade=dict(lift=(0.010, 0.009, 0.006), gain=(1.0, 0.99, 0.95), gamma=(1.0, 1.0, 1.02)),
    grain=0.065, vignette=0.6,
)

# --------------------------------------------------------------------------- OPPOSITE
# Saul Bass cut paper: warm paper sky, ink facades, amber windows; RED only for the threat.
OPPOSITE = Palette(
    "opposite",
    ink=(0.020, 0.018, 0.016),
    sky_top=(0.80, 0.765, 0.70), sky_bottom=(0.80, 0.765, 0.70),
    fog_stops=[(0.0, (0.26, 0.25, 0.23)), (0.45, (0.50, 0.48, 0.44)), (1.0, (0.78, 0.75, 0.69))],
    haze_gamma=0.75,
    light=(0.95, 0.66, 0.24),
    flame=(1.0, 0.88, 0.62),
    accent=RED,
    paper=PAPER,
    grade=dict(lift=(0.010, 0.009, 0.006), gain=(1.0, 0.99, 0.95), gamma=(1.0, 1.0, 1.02)),
    grain=0.045, vignette=0.5,
)

# --------------------------------------------------------------------------- DOUBLE CROSS
# A heist told on its own blueprint: cyanotype blue paper and chalk for the plan, a navy night
# for the world it rises into; gold for the vault and the lamp; RED for the double-crosser.
DOUBLE_CROSS = Palette(
    "double_cross",
    ink=(0.018, 0.020, 0.026),
    sky_top=(0.05, 0.09, 0.16), sky_bottom=(0.05, 0.09, 0.16),
    fog_stops=[(0.0, (0.05, 0.09, 0.16)), (0.5, (0.11, 0.19, 0.30)), (1.0, (0.16, 0.26, 0.38))],
    haze_gamma=0.75,
    light=(0.95, 0.66, 0.24),
    flame=(1.0, 0.88, 0.62),
    accent=RED,
    paper=PAPER,
    grade=dict(lift=(0.008, 0.009, 0.012), gain=(1.0, 1.0, 0.99), gamma=(1.0, 1.0, 1.0)),
    grain=0.045, vignette=0.5,
)

PALETTES = {"salvage": SALVAGE, "shadowplay": SHADOWPLAY, "red": RED_FILM, "lantern": LANTERN, "opposite": OPPOSITE,
            "opposite_bass": OPPOSITE, "opposite_full": OPPOSITE,
            "double_cross": DOUBLE_CROSS}
