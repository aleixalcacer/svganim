# Pendulum

```{image} /_static/examples/pendulum.svg
:alt: Pendulum
:width: 260px
:align: center
```

A rod and a bob swinging for two periods. The angle is a cosine sampled over exactly two periods, so the last frame leads straight into the first and `hold=0` gives a seamless loop.

## What changes in each frame

- `rod.set_data(...)` moves the end of the rod.
- `bob.set_data(...)` moves the bob.

## What svganim animates

The rod's path (`d`) and the bob's position (`x`, `y`). It uses the small-angle approximation, not the full nonlinear equation.

80 frames at 30 fps, about 7 KB.

## Code

```{literalinclude} /../examples/pendulum.py
:language: python
```
