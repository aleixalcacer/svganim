---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
---

# k-means

**Focus: `interpolate`.** By default the SVG jumps from one frame to the next. With `interpolate=True` shapes glide and colours fade between frames, which suits animations where each frame is a state, such as the iterations of Lloyd's algorithm. The algorithm runs first and its states are stored; `update` then replays them, one frame per iteration, until the centroids stop moving.

```{code-cell} ipython3
import matplotlib.pyplot as plt
import numpy as np

from svganim import anim_to_svg

rng = np.random.default_rng(0)
X = np.vstack([rng.normal(c, 0.8, (60, 2)) for c in ([0, 0], [4, 1], [1, 4])])
centers = X[rng.choice(len(X), 3, replace=False)]
states = []
for _ in range(20):  # Lloyd's algorithm, keeping every iteration until it converges
    labels = np.linalg.norm(X[:, None] - centers, axis=2).argmin(axis=1)
    states.append((labels, centers))
    new_centers = np.array([X[labels == j].mean(axis=0) for j in range(3)])
    if np.allclose(new_centers, centers):
        break
    centers = new_centers

colors = np.array(["#4c72b0", "#dd8452", "#55a868"])
fig, ax = plt.subplots(figsize=(5, 3))
points = ax.scatter(*X.T, c=colors[states[0][0]], s=14)
stars = ax.scatter(
    *states[0][1].T, c=colors, marker="X", s=160, edgecolors="black", zorder=3
)
ax.axis("off")

def update(i):
    labels, centers = states[i]
    points.set_facecolor(colors[labels])
    stars.set_offsets(centers)

plt.close(fig)  # otherwise the notebook also shows the static figure
svg = anim_to_svg(fig, update, len(states), fps=1.5, interpolate=True)
```

For comparison, the same figure without `interpolate`, which switches abruptly between states:

```{code-cell} ipython3
anim_to_svg(fig, update, len(states), fps=1.5)
```

The result is a string that displays itself as an animated image:

```{code-cell} ipython3
svg
```

## What changes in each frame

- `points.set_facecolor(colors[labels])` recolours the points by cluster.
- `stars.set_offsets(centers)` moves the three centroids.

## What svganim animates

The colour (`fill`, `stroke`) of the points that change cluster at some
point, and the position of the centroids (`x`, `y`).

With `interpolate=True` the centroids slide to their next position and the
points fade to their new colour. Numeric attributes (paths, positions, colours,
opacities) are interpolated linearly; the rest keep switching stepwise, such as
a path whose number of vertices changes, a `none` fill or a clip path.

Use it when each frame is a state you want to move between. Leave it off when
the frames are already small steps of a continuous motion, where it adds nothing
visible. It makes files slightly larger, because svganim turns off matplotlib's
path simplification: it changes the vertex count between frames, and such paths
cannot be interpolated.

The loop stops when the algorithm converges: later iterations would be identical frames and only add dead time.

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue

glue("kmeans", svg, display=False)
```
