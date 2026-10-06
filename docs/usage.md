# Usage

## How it works

Every frame is rendered to SVG and the first one becomes the base document.
Each later frame is compared with it, element by element, and every attribute
that changes (`d`, `x`, `y`, `fill`, `transform`, ...) gets a SMIL animation.
Elements that never change are left untouched, so axes, ticks and static data
cost nothing.

Frames are compared as they are rendered and then discarded, so memory stays
roughly constant however many frames you ask for.

## Writing the update function

Create your artists once, keep a reference to them and change them in
`update(i)`:

```python
(line,) = ax.plot(x, y)


def update(i):
    line.set_ydata(...)  # fine: same artist, new data
    ax.plot(...)  # not fine: adds an element
```

A line whose data grows with `set_data` is fine: the path gets longer but it is
still one element.

## Smooth transitions

By default the SVG switches between the frames you rendered. Pass
`interpolate=True` to glide between them instead:

```python
anim_to_svg(fig, update, n_frames=len(states), fps=2, interpolate=True)
```

Numeric attributes (paths, positions, colours, opacities) are interpolated
linearly from one frame to the next. In the [k-means example](examples/kmeans.md)
the centroids slide to their new position and the points fade to their new
colour. Attributes that cannot be interpolated keep switching stepwise: a path
whose number of vertices changes, a `none` fill or a clip path.

Use it when each frame is a state you want to move between, such as an
iteration of an algorithm. Leave it off when the frames are already small steps
of a continuous motion, where it adds nothing visible.

It makes files larger, because svganim turns off matplotlib's path
simplification (it changes the vertex count between frames, and such paths
cannot be interpolated). The k-means example grows from 44 KiB to 47 KiB.

## Limitations

- The number and order of SVG elements must be identical in every frame, for
  example the same number of lines and markers. Otherwise `ValueError` is
  raised. Path vertex counts may change.
- Text is rendered as glyphs and cannot be animated.
- Transforms must be a single `translate`, `scale`, `rotate` or `skew`.
- Output is vector only. Figures with raster images (`imshow`, `rasterized=True`)
  are rejected with `ValueError`; use `pcolormesh` for grids instead.
- File size grows linearly with the number of frames and the number of animated
  elements.
- Animation uses SMIL, which all current browsers support.
