# Sine wave

```{image} /_static/examples/wave.svg
:alt: Sine wave
:width: 420px
:align: center
```

The simplest animation: create the artists once and change their data in `update`. A line and two scatter markers move at the same time.

## What changes in each frame

- `line.set_ydata(...)` shifts the sine wave.
- `sc.set_offsets(...)` moves the two markers.

## What svganim animates

The line's path (`d`) and the markers' position (`x`, `y`). Axes, ticks and labels are written once and never touched.

60 frames at 20 fps, about 91 KiB.

## Code

```{literalinclude} /../examples/wave.py
:language: python
```
