# Usage

## How it works

Every frame is rendered to SVG and the first one becomes the base document.
Each later frame is compared with it, element by element, and every attribute
that changes (`d`, `x`, `y`, `fill`, `transform`, ...) gets a SMIL animation.
Elements that never change are left untouched, so axes, ticks and static data
cost nothing. Artists are matched from frame to frame by a gid, so they can also
appear and disappear.

## Saving an animation

Write your animation as usual, with `FuncAnimation` or `ArtistAnimation`, and save
it with the `svganim` writer. Importing svganim registers it by name:

```python
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

import svganim  # registers the "svganim" writer

fig, ax = plt.subplots()
x = np.linspace(0, 2 * np.pi, 200)
(line,) = ax.plot(x, np.sin(x))


def update(i):
    line.set_ydata(np.sin(x + i / 10))


ani = FuncAnimation(fig, update, frames=60)
ani.save("wave.svg", writer="svganim", fps=20)
```

Create your artists once, keep a reference to them and change them in `update`. A
line whose data grows with `set_data` is fine: the path gets longer but it is
still one element.

To set options, pass an instance: `SvgAnimWriter(fps=20, interpolate=True)` takes
`hold`, `precision` and `interpolate`. With an instance, `fps` goes to the writer,
because `save` refuses one of its own. With the name, `save(fps=...)` sets it, and
without one matplotlib takes it from the animation's interval. By default the
animation lasts `n_frames / fps`, as with any matplotlib writer; `hold` adds seconds
on the last frame before it loops.

matplotlib decides which frames are drawn: `frames` can be a number, a list of
objects or a generator, and `fargs` and `init_func` work as usual. A generator
without `save_count` is cut at matplotlib's default. `bbox_inches="tight"` is
ignored by `Animation.save`, since the crop would change from frame to frame. Only
`save` is supported: `to_html5_video` and `to_jshtml` are not.

`ani` changes `fig` as it goes, so when `save` returns the figure is left as the
last frame set it. If the animation raises, no file is written.

## Artists that come and go

Create the artist once and show or hide it with `set_visible`. matplotlib leaves a
hidden artist out of the SVG, and svganim shows it only in the frames where it is
drawn:

```python
(label,) = ax.plot(x, y, color="tab:red")


def update(i):
    label.set_visible(i >= 30)  # drawn from frame 30 on
```

The [constellation](examples/constellation.md) example does it with stars and lines.

Creating or removing artists inside `update` works too, but then `update` depends
on how many times it has run: a second `save` starts with the artists the first
one left behind. Showing and hiding does not have that problem.

To follow each artist from frame to frame, svganim gives it a gid while it works
and takes it off at the end. A gid you set yourself with `set_gid` is kept, and
two artists cannot share one.

An artist can also gain or lose elements at its end: the letters of a text that
changes length, the points of a scatter plot, the ticks of an axis whose limits
change. Each one is drawn only in the frames that have it. So a counter can go
from 9 to 10, a plot can grow and rescale its axes, and a scatter plot can get
more points or lose some. Points are told apart by their place in the list, so if
you remove one from the middle with `interpolate=True`, the ones after it glide to
the place of the next, which is only right if they all move that way. Keep their
number fixed and hide the extra ones if they should stay where they are.

## What cannot change

The kind of element in a place cannot change. matplotlib sometimes draws
an artist with other elements when its style changes, as recent versions do with a
scatter plot whose face colour goes through `none`, and then a `ValueError` names
the element. A transparent colour, such as `(1, 0, 0, 0)`, looks the same as `none`
and is drawn with the same elements as any other colour, so use it instead.

## Images

Images, such as `imshow` or a colorbar, are kept as they are. One that does not
change is written once, and one that changes in every frame is stored in every
frame, so a heatmap animation grows with the size of its array and the number of
frames. The [heatmap](examples/heatmap.md) example shows one.

## Notebooks and Quarto

`ani_to_svg` does what `save` does and returns the SVG as a `str` subclass that
Jupyter and Quarto know how to display. End a cell with the call and the animation
appears, also in the rendered HTML:

```python
ani_to_svg(ani, fps=20)
```

It takes the writer's options (`hold`, `precision`, `interpolate`). Unlike `save`,
`fps` does not default to the animation's interval. To write a file, use `save`.

Close the figure with `plt.close(fig)` first, or the notebook also shows
matplotlib's static picture of it. svganim does not close it for you, so you can
keep using `fig` afterwards.
