---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
---

# Sine wave

**Focus: the basic idea.** Create the artists once, change their data in `update`, and svganim animates only what changes. Here a line and two scatter markers move at the same time.

```{code-cell} ipython3
import matplotlib.pyplot as plt
import numpy as np

from svganim import anim_to_svg

fig, ax = plt.subplots(figsize=(5, 3))
x = np.linspace(0, 2 * np.pi, 200)
(line,) = ax.plot(x, np.sin(x))
ax.set_ylim(-1.2, 1.2)
sc = ax.scatter([1, 2], [0, 0], c=["r", "b"], zorder=3)

def update(i):
    line.set_ydata(np.sin(x + i / 10))
    sc.set_offsets([[1 + i / 20, 0.5], [2, -0.5 + i / 60]])

plt.close(fig)  # otherwise the notebook also shows the static figure
svg = anim_to_svg(fig, update, n_frames=60, fps=20, hold=1.0)
```

The result is a string that displays itself as an animated image:

```{code-cell} ipython3
svg
```

## What changes in each frame

- `line.set_ydata(...)` shifts the sine wave.
- `sc.set_offsets(...)` moves the two markers.

## What svganim animates

The line's path (`d`) and the markers' position (`x`, `y`). Axes, ticks and labels are written once and never touched.

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue

glue("wave", svg, display=False)
```
