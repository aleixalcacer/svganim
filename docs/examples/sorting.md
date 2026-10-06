# Bubble sort

```{image} /_static/examples/sorting.svg
:alt: Bubble sort
:width: 440px
:align: center
```

Sixteen bars sorted with bubble sort, one frame per swap. The colour follows the value, so you can watch the order emerge.

## What changes in each frame

- `bar.set_height(h)` resizes each bar.
- `bar.set_color(...)` recolours it from the viridis colormap.

## What svganim animates

Each bar's geometry (`d`) and colour (`fill`, `stroke`). A bar that does not change in a frame adds nothing for that frame, because only changes are stored.

72 frames at 20 fps, about 26 KiB.

## Code

```{literalinclude} /../examples/sorting.py
:language: python
```
