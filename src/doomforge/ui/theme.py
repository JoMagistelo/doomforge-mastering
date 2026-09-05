"""Visual tokens for DoomForge's desktop UI.

The palette is intentionally restrained: charcoal metal, warm off-white and a
small amount of electric violet.  Keeping all tokens in one module makes the
interface easy to re-theme later without coupling presentation to DSP code.
"""

BLACK = "#07060A"
BLACK_2 = "#0C0911"
SURFACE = "#100D16"
SURFACE_2 = "#17121F"
SURFACE_3 = "#20182B"
BORDER = "#32263F"
BORDER_STRONG = "#4D3764"

PURPLE = "#8B5CF6"
PURPLE_HOT = "#A855F7"
PURPLE_DARK = "#5B21B6"
PURPLE_SOFT = "#C4B5FD"
PURPLE_FAINT = "#2A1A3A"

WHITE = "#F8F6FA"
WHITE_SOFT = "#E8E2EC"
MUTED = "#A69BAD"
MUTED_2 = "#756B7C"

GREEN = "#71D6A1"
AMBER = "#F3C969"
RED = "#FF7A86"
CYAN = "#71D5E8"

# Backwards-compatible names used by older UI code/tests.
PANEL = SURFACE
PANEL_2 = SURFACE_2
