# Lorenz attractor

```{image} /_static/examples/lorenz.svg
:alt: Lorenz attractor
:width: 340px
:align: center
```

The Lorenz system integrated with Euler steps and projected onto the x-z plane, drawn progressively as a growing line with a moving head.

## What changes in each frame

- `line.set_data(...)` extends the trajectory by 25 points per frame.
- `head.set_data(...)` moves the red dot.

## What svganim animates

The trail's path (`d`) and the head's position (`x`, `y`).

36 frames at 15 fps, about 170 KiB. Growing paths are the expensive case, because every frame stores a longer path; `precision=1` keeps the size down.

## Code

```{literalinclude} /../examples/lorenz.py
:language: python
```
