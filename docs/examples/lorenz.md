---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
---

# Lorenz attractor

**Focus: file size.** A growing path is the expensive case, because every frame stores a longer path, and `precision` (decimals kept in coordinates) is the main lever. Here the Lorenz system, integrated with Euler steps and projected onto the x-z plane, is drawn progressively as a growing line with a moving head.

```{code-cell} ipython3
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from svganim import ani_to_svg

s = np.ones((900, 3))
for k in range(899):  # Lorenz system, Euler steps
    x, y, z = s[k]
    s[k + 1] = s[k] + 0.01 * np.array(
        [10 * (y - x), x * (28 - z) - y, x * y - 8 / 3 * z]
    )

fig, ax = plt.subplots(figsize=(5, 3))
ax.set(xlim=(-22, 22), ylim=(0, 52))
ax.axis("off")
(line,) = ax.plot(s[:1, 0], s[:1, 2], lw=0.8, color="tab:purple")
(head,) = ax.plot(s[:1, 0], s[:1, 2], "o", color="tab:red")

def update(i):
    n = 25 * (i + 1)
    line.set_data(s[:n, 0], s[:n, 2])
    head.set_data(s[n - 1 : n, 0], s[n - 1 : n, 2])

plt.close(fig)  # otherwise the notebook also shows the static figure
ani = FuncAnimation(fig, update, frames=36)
svg = ani_to_svg(ani, fps=15, precision=1)
```

The same figure with the default `precision=3` is noticeably larger:

```{code-cell} ipython3
full = ani_to_svg(ani, fps=15)
f"precision=3: {len(full) / 1024:.0f} KiB, precision=1: {len(svg) / 1024:.0f} KiB"
```

`ani_to_svg` returns the SVG as a string that displays itself as an animated image:

```{code-cell} ipython3
svg
```

## What changes in each frame

- `line.set_data(...)` extends the trajectory by 25 points per frame.
- `head.set_data(...)` moves the red dot.

## What svganim animates

The trail's path (`d`) and the head's position (`x`, `y`).

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue

glue("lorenz", svg, display=False)
```
