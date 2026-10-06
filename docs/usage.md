# Usage

## How it works

Every frame is rendered to SVG and the first one becomes the base document.
Each later frame is compared with it element by element. Wherever an attribute
or an inline style property changes (`d`, `x`, `y`, `fill`, `transform`, ...), an
`<animate>` child with one value per change is added. Elements that never change
are left untouched, so axes, ticks and static data cost nothing.

Frames are compared as they are rendered and then discarded, so memory stays
roughly constant however many frames you ask for.

## Writing the update function

Create your artists once, keep a reference to them and change them in
`update(i)`:

```python
(line,) = ax.plot(x, y)


def update(i):
    line.set_ydata(...)  # fine: same artist, new data
    # ax.plot(...)           # not fine: adds an element
```

A line whose data grows with `set_data` is fine: the path gets longer but it is
still one element.

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
