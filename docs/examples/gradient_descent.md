---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
---

# Gradient descent

**Focus: data that grows.** Draw a trail as **one** line and extend it with `set_data`, instead of adding a line for every step. Here gradient descent on f(x, y) = x² + 10y² zig-zags down a valley that is much steeper in `y` than in `x`. The filled contours are drawn once.

```{code-cell} ipython3
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from svganim import ani_to_svg

x, y = np.meshgrid(np.linspace(-3, 3, 90), np.linspace(-1.5, 1.5, 45))
p, steps = np.array([-2.8, 1.2]), []
for _ in range(40):  # f(x, y) = x^2 + 10 y^2
    steps.append(p)
    p = p - 0.09 * np.array([2 * p[0], 20 * p[1]])
steps = np.array(steps)

fig, ax = plt.subplots(figsize=(5, 3))
ax.contourf(x, y, x**2 + 10 * y**2, 12, cmap="Blues")
(trail,) = ax.plot(*steps[:1].T, "-", color="k", lw=1)
(dot,) = ax.plot(*steps[:1].T, "o", color="tab:red")

def update(i):
    trail.set_data(*steps[: i + 1].T)
    dot.set_data(*steps[i : i + 1].T)

plt.close(fig)  # otherwise the notebook also shows the static figure
ani = FuncAnimation(fig, update, frames=len(steps))
svg = ani_to_svg(ani, fps=10)
```

`ani_to_svg` returns the SVG as a string that displays itself as an animated image:

```{code-cell} ipython3
svg
```

## What changes in each frame

- `trail.set_data(...)` extends the path with the points visited so far.
- `dot.set_data(...)` moves the current position.

## What svganim animates

The trail's path (`d`) and the dot's position (`x`, `y`). The trail is **one** line whose data grows: its path gets longer, but it stays one element, which is much smaller than a new line in every frame.

Most of the file is the static contour fills, which are written once.

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue

glue("gradient_descent", svg, display=False)
```
