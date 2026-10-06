---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
---

# Appearing points

**Focus: artists that come and go.** Create each artist once and show or hide it with `set_visible`. matplotlib leaves a hidden artist out of the SVG, and svganim shows it only in the frames where it is drawn. Here sixteen points appear one by one, and a ring marks the last one at the end.

```{code-cell} ipython3
import matplotlib.pyplot as plt
import numpy as np

from svganim import anim_to_svg

points = np.random.default_rng(2).random((16, 2))

fig, ax = plt.subplots(figsize=(5, 3))
ax.set(xlim=(0, 1), ylim=(0, 1))
ax.axis("off")
dots = [
    ax.plot(*point, "o", ms=14, color=plt.cm.viridis(k / 15))[0]
    for k, point in enumerate(points)
]
(ring,) = ax.plot(*points[-1], "o", ms=26, mfc="none", mec="tab:red", mew=2)


def update(i):
    for k, dot in enumerate(dots):
        dot.set_visible(k <= i)  # point k is drawn from frame k on
    ring.set_visible(i == len(dots) - 1)


plt.close(fig)  # otherwise the notebook also shows the static figure
svg = anim_to_svg(fig, update, len(dots), fps=6)
```

The result is a string that displays itself as an animated image:

```{code-cell} ipython3
svg
```

## What changes in each frame

- `dot.set_visible(k <= i)` shows point `k` from frame `k` on.
- `ring.set_visible(...)` shows the ring only in the last frame.

## What svganim animates

The `visibility` of each point and of the ring. Axes and the rest of the figure are written once. Hiding and showing keeps `update` repeatable: calling `anim_to_svg` again gives the same animation, which would not hold if `update` created the points as it went.

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue

glue("appearing", svg, display=False)
```
