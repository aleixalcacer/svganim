---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
---

# Constellation

**Focus: artists that come and go.** Create each artist once and show or hide it with `set_visible`. matplotlib leaves a hidden artist out of the SVG, and svganim shows it only in the frames where it is drawn. Here Cassiopeia is drawn star by star over a sky that does not change.

```{code-cell} ipython3
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from svganim import ani_to_svg

rng = np.random.default_rng(7)
sky = rng.random((90, 2))
stars = np.array([[0.08, 0.30], [0.27, 0.72], [0.50, 0.42], [0.72, 0.75], [0.92, 0.33]])

fig, ax = plt.subplots(figsize=(5, 3), facecolor="#0b1026")
ax.set(xlim=(0, 1), ylim=(0, 1))
ax.axis("off")
ax.scatter(*sky.T, s=rng.random(90) * 6 + 1, color="white", alpha=0.6)
glows = [ax.plot(*star, "o", ms=26, color="#ffd479", alpha=0.18)[0] for star in stars]
dots = [ax.plot(*star, "o", ms=7, color="#fff3c4")[0] for star in stars]
lines = [ax.plot(*stars[k : k + 2].T, color="#9fb4ff", lw=1.5)[0] for k in range(4)]


def update(i):
    for k, (glow, dot) in enumerate(zip(glows, dots)):
        glow.set_visible(i >= k)  # star k is lit from frame k on
        dot.set_visible(i >= k)
    for k, line in enumerate(lines):
        line.set_visible(i > k)  # and joined to the previous one a frame later


plt.close(fig)  # otherwise the notebook also shows the static figure
ani = FuncAnimation(fig, update, frames=len(stars))
svg = ani_to_svg(ani, fps=2, hold=2)
```

`ani_to_svg` returns the SVG as a string that displays itself as an animated image:

```{code-cell} ipython3
svg
```

## What changes in each frame

- `glow.set_visible(...)` and `dot.set_visible(...)` light star `k` from frame `k` on.
- `line.set_visible(...)` draws the line that joins star `k` to the next one.

## What svganim animates

The `visibility` of each star, its glow and each line. The sky and the rest of the figure are written once. Hiding and showing keeps `update` repeatable: saving again gives the same animation, which would not hold if `update` created the artists as it went.

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue

glue("constellation", svg, display=False)
```
