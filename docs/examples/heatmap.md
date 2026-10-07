---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
---

# Heatmap

**Focus: images.** `imshow` and the colorbar are raster images, and svganim keeps them as they are: the colorbar does not change, so it is written once, and the heatmap is stored in every frame it changes. Here heat spreads from a hot spot over a plate.

```{code-cell} ipython3
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from svganim import ani_to_svg

# Heat spreading over a 20 x 20 plate, one state per frame.
plate = np.zeros((20, 20))
plate[8:12, 8:12] = 1
states = [plate]
for _ in range(29):
    plate = plate + 0.2 * (
        np.roll(plate, 1, 0) + np.roll(plate, -1, 0)
        + np.roll(plate, 1, 1) + np.roll(plate, -1, 1) - 4 * plate
    )
    states.append(plate)

fig, ax = plt.subplots(figsize=(5, 3.6))
image = ax.imshow(states[0], vmin=0, vmax=1, cmap="inferno")
fig.colorbar(image, label="temperature")
ax.axis("off")


def update(i):
    image.set_data(states[i])


plt.close(fig)  # otherwise the notebook also shows the static figure
ani = FuncAnimation(fig, update, frames=len(states))
svg = ani_to_svg(ani, fps=10)
```

`ani_to_svg` returns the SVG as a string that displays itself as an animated image:

```{code-cell} ipython3
svg
```

## What changes in each frame

- `image.set_data(...)` replaces the temperatures.

## What svganim animates

The heatmap, which is a new image in each frame and is shown only in its own. The colorbar and the rest of the figure do not change and are written once.

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue

glue("heatmap", svg, display=False)
```
