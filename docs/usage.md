# Usage

## How it works

Every frame is rendered to SVG and the first one becomes the base document.
Each later frame is compared with it, element by element, and every attribute
that changes (`d`, `x`, `y`, `fill`, `transform`, ...) gets a SMIL animation.
Elements that never change are left untouched, so axes, ticks and static data
cost nothing. Artists are matched from frame to frame by a gid, so they can also
appear and disappear.

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
moves. A line whose data grows with `set_data` is fine: the path gets longer but
it is still one element.

`update` is called once per frame, in order, and the picture has to depend only
on `i`. A function that keeps state, such as one that advances a simulation on
every call, gives a different animation each time you call `anim_to_svg`. Compute
the simulation first and let `update` show its state `i`, as the
[k-means](examples/kmeans.md) and [bubble sort](examples/sorting.md) examples do.

`update` changes `fig` as it goes, so when `anim_to_svg` returns the figure is
left as the last frame set it. Call `update(0)` to go back to the first one.

## Artists that come and go

Create the artist once and show or hide it with `set_visible`. matplotlib leaves a
hidden artist out of the SVG, and svganim shows it only in the frames where it is
drawn:

```python
(label,) = ax.plot(x, y, color="tab:red")


def update(i):
    label.set_visible(i >= 30)  # drawn from frame 30 on
```

The [appearing points](examples/appearing.md) example does it for sixteen points.

Creating or removing artists inside `update` works too, but then `update` depends
on how many times it has run: a second call to `anim_to_svg` starts with the
artists the first one left behind. Showing and hiding does not have that problem.

To follow each artist from frame to frame, svganim gives it a gid while it works
and takes it off at the end. A gid you set yourself with `set_gid` is kept, and
two artists cannot share one.

What cannot change is the number of elements inside one artist. Text can change
as long as it keeps its length, so a counter whose digits change is fine and a
title that grows is not, and axis limits that add or remove ticks fail too. In
both cases a `ValueError` names the element.

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
