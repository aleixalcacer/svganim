---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
---

# Rescaling axes

**Focus: elements that come and go inside an artist.** A text can change length and an axis can change its ticks: the letters and the ticks that only some frames have are drawn only in those. Here a random walk is drawn while the axes rescale to fit it and the title counts the time.

```{code-cell} ipython3
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from svganim import ani_to_svg

walk = np.cumsum(np.random.default_rng(3).normal(size=60))
time = np.arange(len(walk))

fig, ax = plt.subplots(figsize=(5, 3))
(line,) = ax.plot([], [], color="tab:blue", lw=2)
(head,) = ax.plot([], [], "o", color="tab:red")
ax.grid(alpha=0.3)


def update(i):
    line.set_data(time[: i + 1], walk[: i + 1])
    head.set_data(time[i : i + 1], walk[i : i + 1])
    ax.relim()
    ax.autoscale_view()  # the limits, and so the ticks, change with the data
    ax.set_title(f"t = {i}")  # from one digit to two


plt.close(fig)  # otherwise the notebook also shows the static figure
ani = FuncAnimation(fig, update, frames=len(walk))
svg = ani_to_svg(ani, fps=15)
```

`ani_to_svg` returns the SVG as a string that displays itself as an animated image:

```{code-cell} ipython3
svg
```

## What changes in each frame

- `line.set_data(...)` extends the walk and `head.set_data(...)` moves the red dot.
- `ax.autoscale_view()` changes the limits, and with them the position, the number and the text of the ticks.
- `ax.set_title(...)` changes the text, which gains a letter when the count reaches 10.

## What svganim animates

The path of the walk, the position of the dot, the ticks with their labels and the title. An element that only some frames have, such as the second digit of the title or a tick that appears when the axis grows, is hidden in the others.

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue

glue("rescaling", svg, display=False)
```
