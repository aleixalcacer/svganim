# Usage

## How it works

Every frame is rendered to SVG and the first one becomes the base document.
Each later frame is compared with it, element by element, and every attribute
that changes (`d`, `x`, `y`, `fill`, `transform`, ...) gets a SMIL animation.
Elements that never change are left untouched, so axes, ticks and static data
cost nothing.

## Writing the update function

Create your artists once, keep a reference to them and change them in
`update(i)`. A complete example:

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

`update(i)` runs before frame `i` is rendered, so it only has to change what
moves. The rule is that it changes existing artists and never adds or removes
any:

```python
(line,) = ax.plot(x, y)


def update(i):
    line.set_ydata(...)  # fine: same artist, new data
    ax.plot(...)  # not fine: adds an element
```

A line whose data grows with `set_data` is fine: the path gets longer but it is
still one element.

`update` is called once per frame, in order, and the picture has to depend only
on `i`. A function that keeps state, such as one that advances a simulation on
every call, gives a different animation each time you call `anim_to_svg`. Compute
the simulation first and let `update` show its state `i`, as the
[k-means](examples/kmeans.md) and [bubble sort](examples/sorting.md) examples do.

`update` changes `fig` as it goes, so when `anim_to_svg` returns the figure is
left as the last frame set it. Call `update(0)` to go back to the first one.

## Notebooks and Quarto

`anim_to_svg` returns a `str` subclass that Jupyter and Quarto know how to
display. End a cell with the call and the animation appears, also in the
rendered HTML:

```python
anim_to_svg(fig, update, n_frames=60)
```

Close the figure with `plt.close(fig)` first, or the notebook also shows
matplotlib's static picture of it. svganim does not close it for you, so you can
keep using `fig` afterwards.
