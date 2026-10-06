---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
---

# Pendulum

**Focus: timing and loops.** `fps` sets the speed and `hold` the pause on the last frame before the loop restarts. A rod and a bob swing for two periods; the angle is a cosine sampled over exactly two periods, so the last frame leads straight into the first and `hold=0` gives a seamless loop.

```{code-cell} ipython3
import matplotlib.pyplot as plt
import numpy as np

from svganim import anim_to_svg

theta = 0.8 * np.cos(np.linspace(0, 4 * np.pi, 80, endpoint=False))  # two swings

fig, ax = plt.subplots(figsize=(5, 3))
ax.set(xlim=(-1.2, 1.2), ylim=(-1.4, 0.2), aspect="equal")
ax.axis("off")
(rod,) = ax.plot([0, 0], [0, -1], "k", lw=2)
(bob,) = ax.plot([0], [-1], "o", ms=24, color="tab:red")

def update(i):
    x, y = np.sin(theta[i]), -np.cos(theta[i])
    rod.set_data([0, x], [0, y])
    bob.set_data([x], [y])

plt.close(fig)  # otherwise the notebook also shows the static figure
svg = anim_to_svg(fig, update, len(theta), fps=30, hold=0)
```

The result is a string that displays itself as an animated image:

```{code-cell} ipython3
svg
```

## What changes in each frame

- `rod.set_data(...)` moves the end of the rod.
- `bob.set_data(...)` moves the bob.

## What svganim animates

The rod's path (`d`) and the bob's position (`x`, `y`). It uses the small-angle approximation, not the full nonlinear equation.

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue

glue("pendulum", svg, display=False)
```
