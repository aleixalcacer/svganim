# svganim

Turn a matplotlib figure and a per-frame update function into one
self-contained, looping, animated SVG. No GIFs, no JavaScript. The source is on
[GitHub](https://github.com/aleixalcacer/svganim).

```{image} _static/sorting.svg
:alt: Bubble sort: sixteen bars changing height and colour
:align: center
```

```{toctree}
:hidden:

usage
examples/index
api
```

## Install

```bash
pip install svganim
```

## Quick start

```python
import matplotlib.pyplot as plt
import numpy as np
from svganim import anim_to_svg

fig, ax = plt.subplots()
x = np.linspace(0, 2 * np.pi, 200)
(line,) = ax.plot(x, np.sin(x))


def update(i):
    line.set_ydata(np.sin(x + i / 10))


anim_to_svg(fig, update, n_frames=60, fps=20, path="wave.svg")
```

Embed the result anywhere an image goes:

```html
<img src="wave.svg" alt="A moving sine wave">
```
