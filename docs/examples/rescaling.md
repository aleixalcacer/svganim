---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
---

# Rescaling axes

**Focus: elements that come and go inside an artist.** A text can change length and an axis can change its ticks: the letters and the ticks that only some frames have are drawn only in those. Here a curve grows, the axes rescale to fit it, and the title counts the points.

```{code-cell} ipython3
import matplotlib.pyplot as plt
import numpy as np

from svganim import anim_to_svg

x = np.linspace(0, 6, 30)
y = np.exp(x / 2)

fig, ax = plt.subplots(figsize=(5, 3))
(line,) = ax.plot([], [], "o-", color="tab:blue")


def update(i):
    line.set_data(x[: i + 1], y[: i + 1])
    ax.relim()
    ax.autoscale_view()  # the limits, and so the ticks, change with the data
    ax.set_title(f"n = {i + 1}")  # from one digit to two


plt.close(fig)  # otherwise the notebook also shows the static figure
svg = anim_to_svg(fig, update, len(x), fps=10)
```

The result is a string that displays itself as an animated image:

```{code-cell} ipython3
svg
```

## What changes in each frame

- `line.set_data(...)` adds a point, which is one more marker at the end of the line.
- `ax.autoscale_view()` changes the limits, and with them the position, the number and the text of the ticks.
- `ax.set_title(...)` changes the text, which gains a letter when the count reaches 10.

## What svganim animates

The path and the markers of the line, the position of the ticks and of their labels, and the title. An element that only some frames have, such as the second digit of the title or a tick that appears when the axis grows, is hidden in the others.

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue

glue("rescaling", svg, display=False)
```
