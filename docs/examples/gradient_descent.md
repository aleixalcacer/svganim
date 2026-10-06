# Gradient descent

```{image} /_static/examples/gradient_descent.svg
:alt: Gradient descent
:width: 440px
:align: center
```

Gradient descent on f(x, y) = x² + 10y². The valley is much steeper in `y` than in `x`, so the optimizer zig-zags before settling at the minimum. The filled contours are drawn once.

## What changes in each frame

- `trail.set_data(...)` extends the path with the points visited so far.
- `dot.set_data(...)` moves the current position.

## What svganim animates

The trail's path (`d`) and the dot's position (`x`, `y`). The trail is **one** line whose data grows: its path gets longer, but the number of elements never changes, which is what svganim needs. Creating a new line per frame would raise `ValueError`.

40 frames at 10 fps, about 100 KB. Most of the size is the static contour fills.

## Code

```{literalinclude} /../examples/gradient_descent.py
:language: python
```
