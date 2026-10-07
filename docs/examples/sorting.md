---
file_format: mystnb
kernelspec:
  name: python3
  display_name: Python 3
---

# Bubble sort

**Focus: one frame per state.** Run the algorithm first and keep every state, then let `update(i)` show state `i`. Here sixteen bars are sorted with bubble sort, one frame per swap, and the colour follows the value so you can watch the order emerge.

```{code-cell} ipython3
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from svganim import ani_to_svg

a = np.random.default_rng(3).permutation(16) + 1
frames = [a.copy()]
for end in range(len(a) - 1, 0, -1):  # bubble sort, one frame per swap
    for j in range(end):
        if a[j] > a[j + 1]:
            a[j], a[j + 1] = a[j + 1], a[j]
            frames.append(a.copy())

fig, ax = plt.subplots(figsize=(5, 3))
bars = ax.bar(range(16), frames[0])
ax.axis("off")

def update(i):
    for bar, h in zip(bars, frames[i], strict=True):
        bar.set_height(h)
        bar.set_color(plt.cm.viridis(h / 16))

plt.close(fig)  # otherwise the notebook also shows the static figure
ani = FuncAnimation(fig, update, frames=len(frames))
svg = ani_to_svg(ani, fps=20)
```

`ani_to_svg` returns the SVG as a string that displays itself as an animated image:

```{code-cell} ipython3
svg
```

## What changes in each frame

- `bar.set_height(h)` resizes each bar.
- `bar.set_color(...)` recolours it from the viridis colormap.

## What svganim animates

Each bar's geometry (`d`) and colour (`fill`, `stroke`). A bar that does not change in a frame adds nothing for that frame, because only changes are stored.

```{code-cell} ipython3
:tags: [remove-cell]

from myst_nb import glue

glue("sorting", svg, display=False)
```
