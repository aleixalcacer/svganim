# svganim

Turn a matplotlib animation into one self-contained, looping, animated SVG. No
GIFs, no JavaScript. The source is on [GitHub](https://github.com/aleixalcacer/svganim).

```{image} _static/sorting.svg
:alt: Bubble sort: sixteen bars changing height and colour
:align: center
```

```{toctree}
:hidden:

usage
examples/index
api
releasing
```

## Install

```bash
pip install svganim
```

## Quick start

Keep your `FuncAnimation` as it is and save it with `SvgAnimWriter`:

```python
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from svganim import SvgAnimWriter

fig, ax = plt.subplots()
x = np.linspace(0, 2 * np.pi, 200)
(line,) = ax.plot(x, np.sin(x))


def update(i):
    line.set_ydata(np.sin(x + i / 10))


ani = FuncAnimation(fig, update, frames=60)
ani.save("wave.svg", writer=SvgAnimWriter(fps=20))
```

Embed the result anywhere an image goes:

```html
<img src="wave.svg" alt="A moving sine wave">
```
