"""Draw the svganim logo with matplotlib and save it as assets/logo*.svg.

Three layouts, each in a light and a dark theme:

* ``logo``: the icon alone, on a square canvas.
* ``logo-text``: the icon with the name below it, on a square canvas.
* ``logo-horizontal``: the icon with the name to its right.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Circle, PathPatch
from matplotlib.path import Path as MplPath
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D

# Lead dot first, then the fading trail. "svg" takes the wave colour, "anim" its own.
THEMES = {
    "light": {
        "wave": "#26663A",
        "dots": ["#8FDB35", "#C5E8A0", "#DDF2C8", "#EEF8E4"],
        "word": ("#26663A", "#6DB31F"),
    },
    "dark": {
        "wave": "#4FB36B",
        "dots": ["#8FDB35", "#6E9F3C", "#4E7435", "#3A5530"],
        "word": ("#4FB36B", "#8FDB35"),
    },
}
FONT = FontProperties(family=["Avenir Next", "DejaVu Sans"], weight="bold")
GAP = 14  # transparent border around each dot

# Icon bounds in logo units (stroke and dots included).
X0, X1, Y0, Y1, MARGIN = 7, 483, 79, 360, 24
ICON_CENTER_Y = 222

# Wordmark size and placement for each layout.
STACKED_SIZE, STACKED_BASELINE = 120, 485
HORIZONTAL_SIZE, HORIZONTAL_GAP = 170, 56


def wordmark(size):
    """Paths for "svg" and "anim", the offset of "anim", and the extents."""
    full = TextPath((0, 0), "svganim", size=size, prop=FONT)
    anim = TextPath((0, 0), "anim", size=size, prop=FONT)
    svg = TextPath((0, 0), "svg", size=size, prop=FONT)
    box = full.get_extents()
    # "anim" ends where the whole word ends, which fixes where it starts.
    return svg, anim, box.x1 - anim.get_extents().x1, box


def layout_icon():
    side = max(X1 - X0, Y1 - Y0) + 2 * MARGIN
    cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
    return None, (cx - side / 2, cx + side / 2, cy - side / 2, cy + side / 2)


def layout_stacked():
    svg, anim, anim_x, box = wordmark(STACKED_SIZE)
    shift = (X0 + X1) / 2 - (box.x0 + box.x1) / 2
    text = (svg, shift, anim, shift + anim_x, STACKED_BASELINE)
    bottom = STACKED_BASELINE - box.y0  # the descender of the "g" is the lowest point
    side = max(X1 - X0, bottom - Y0) + 2 * MARGIN
    cx, cy = (X0 + X1) / 2, (Y0 + bottom) / 2
    return text, (cx - side / 2, cx + side / 2, cy - side / 2, cy + side / 2)


def layout_horizontal():
    svg, anim, anim_x, box = wordmark(HORIZONTAL_SIZE)
    shift = X1 + HORIZONTAL_GAP - box.x0
    baseline = (
        ICON_CENTER_Y + 0.26 * HORIZONTAL_SIZE
    )  # centres the x-height on the wave
    text = (svg, shift, anim, shift + anim_x, baseline)
    top = min(Y0, baseline - box.y1)
    bottom = max(Y1, baseline - box.y0)
    return text, (X0 - MARGIN, shift + box.x1 + MARGIN, top - MARGIN, bottom + MARGIN)


LAYOUTS = {
    "logo": layout_icon,
    "logo-text": layout_stacked,
    "logo-horizontal": layout_horizontal,
}


def clip_without(circles, bounds):
    """Clip path covering the whole canvas except the given (cx, cy, r) discs."""
    left, right, top, bottom = bounds
    box = MplPath.make_compound_path(
        MplPath(
            [(left, top), (right, top), (right, bottom), (left, bottom), (left, top)]
        )
    )
    unit = MplPath.unit_circle()
    holes = [
        # Mirroring flips the winding so the disc is subtracted, not added.
        MplPath(unit.vertices * [-r, r] + [cx, cy], unit.codes)
        for cx, cy, r in circles
    ]
    return MplPath.make_compound_path(box, *holes)


def draw(name, theme, layout):
    text, bounds = LAYOUTS[layout]()
    left, right, top, bottom = bounds

    fig = plt.figure(figsize=((right - left) / 100, (bottom - top) / 100), dpi=100)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(left, right)
    ax.set_ylim(bottom, top)
    ax.axis("off")

    cy, step = 112, 54
    dots = [
        (293 + step * i, 33 if i == 0 else 36 - 2 * i, color)
        for i, color in enumerate(theme["dots"])
    ]
    halos = [(cx, cy, r + GAP) for cx, r, _ in dots]

    x = np.linspace(22, 460, 400)
    y = 225 - 120 * np.cos(2 * np.pi * (x - 80) / 213)
    (wave,) = ax.plot(
        x,
        y,
        color=theme["wave"],
        lw=22,
        solid_capstyle="round",
        solid_joinstyle="round",
    )
    # Only the lead dot's halo reaches the wave. Overlapping holes would fill back in
    # (non-zero winding), so the others are left out.
    wave.set_clip_path(clip_without(halos[:1], bounds), ax.transData)

    # Each dot is cut by the halo of the dot to its left, leaving crescents.
    for i, (cx, r, color) in enumerate(dots):
        patch = ax.add_patch(Circle((cx, cy), r, color=color, lw=0))
        patch.set_clip_path(
            clip_without(halos[max(i - 1, 0) : i], bounds), ax.transData
        )

    if text:
        svg, svg_x, anim, anim_x, baseline = text
        for path, px, color in (
            (svg, svg_x, theme["word"][0]),
            (anim, anim_x, theme["word"][1]),
        ):
            flip = Affine2D().scale(1, -1).translate(px, baseline)
            ax.add_patch(PathPatch(path, fc=color, lw=0, transform=flip + ax.transData))

    fig.savefig(Path(__file__).with_name(name), format="svg", transparent=True)
    plt.close(fig)


for mode, theme in THEMES.items():
    suffix = "" if mode == "light" else "-dark"
    for layout in LAYOUTS:
        draw(f"{layout}{suffix}.svg", theme, layout)
