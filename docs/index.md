# svganim

Turn a matplotlib figure and a per-frame update function into one
self-contained, looping, animated SVG. No GIFs, no JavaScript.

```{image} _static/examples/wave.svg
:alt: A moving sine wave with two moving points
:width: 420px
```

```{toctree}
:maxdepth: 2

usage
examples/index
api
```

## Install

```bash
pip install svganim
```

## Quick start

```{literalinclude} ../examples/wave.py
:language: python
```

Embed the result anywhere an image goes:

```html
<img src="wave.svg" alt="A moving sine wave">
```
