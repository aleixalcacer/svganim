<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/aleixalcacer/svganim/main/assets/logo-horizontal-dark.svg">
    <img src="https://raw.githubusercontent.com/aleixalcacer/svganim/main/assets/logo-horizontal.svg" alt="svganim logo" width="360">
  </picture>
</div>

<div align="center">
  <a href="https://pypi.org/project/svganim/"><img src="https://img.shields.io/pypi/v/svganim" alt="PyPI version"></a>
  <a href="https://github.com/aleixalcacer/svganim/actions/workflows/ci.yml"><img src="https://github.com/aleixalcacer/svganim/actions/workflows/ci.yml/badge.svg" alt="CI status"></a>
  <a href="https://svganim.readthedocs.io"><img src="https://readthedocs.org/projects/svganim/badge/?version=latest" alt="Documentation status"></a>
</div>

Turn a matplotlib animation into one self-contained, looping, animated SVG.

<div align="center">
  <img src="https://raw.githubusercontent.com/aleixalcacer/svganim/main/assets/sorting.svg" alt="Bubble sort: sixteen bars changing height and colour">
</div>

## Why svganim

- **A real image.** One SVG file that works in an `<img>` tag and in GitHub
  READMEs. No JavaScript, no HTML page, no player.
- **Vector.** Sharp at any size, unlike a GIF.
- **Only what changes is animated.** Axes, labels and static data are written
  once, so files stay small.
- **Reproducible.** Same code and matplotlib version, same bytes.

What you give up: playback controls (see [Limitations](#limitations)). If you need
those, use `HTMLWriter` or `to_jshtml`.

## Install

```bash
pip install svganim
```

## Usage

Keep your `FuncAnimation` (or `ArtistAnimation`) as it is and save it with the
`SvgAnimWriter`:

```python
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from svganim import SvgAnimWriter

fig, ax = plt.subplots()
x = np.linspace(0, 2 * np.pi, 200)
(line,) = ax.plot(x, np.sin(x))


def update(i):
    line.set_ydata(np.sin(x + i / 10))


ani = FuncAnimation(fig, update, frames=60)
ani.save("wave.svg", writer=SvgAnimWriter(fps=20))
```

```html
<img src="wave.svg" alt="A moving sine wave">
```

The options go in the writer: `SvgAnimWriter(fps=20, interpolate=True)`. Importing
svganim also registers it under the name `"svganim"`, so
`ani.save("wave.svg", writer="svganim", fps=20)` works too.

In Jupyter and Quarto, `ani_to_svg(ani, fps=20)` returns the SVG as a string that
is displayed as an animated image when it ends a cell. Call `plt.close(fig)` first,
or the notebook also shows matplotlib's static figure.

`update` changes the artists (`set_data`, `set_offsets`, `set_color`, ...). A line
whose data grows is fine, so draw trails and curves with `set_data` on a single
line. Artists can also come and go: create them once and show or hide them with
`set_visible`.

### `SvgAnimWriter(fps=5, *, hold=0, precision=3, interpolate=False)`

| Argument      | Description                                                                                                                               |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `fps`         | Frames per second.                                                                                                                        |
| `hold`        | Seconds to hold the last frame before looping.                                                                                            |
| `precision`   | Decimals kept in coordinates. Lower means smaller files.                                                                                  |
| `interpolate` | If `True`, shapes glide and colours fade between frames instead of switching. See the [k-means example](https://svganim.readthedocs.io/en/latest/examples/kmeans.html). |

`ani_to_svg(ani, fps=5, hold=0, *, precision=3, interpolate=False)`
takes the same options and returns the SVG as a string. Both raise `ValueError`
for an invalid argument or when an element changes kind (see
[Limitations](#limitations)); the message names the element.

## How it works

Each frame is rendered to SVG and the first one becomes the base document. Later
frames are compared with it, and every attribute that changes gets a
[SMIL](https://developer.mozilla.org/docs/Web/SVG/SMIL) animation. Elements that
never change are left untouched, and those that only some frames have, such as the
letters of a text that changes length, are shown only in those.

## Limitations

- An element cannot change kind, which matplotlib sometimes makes it do when a style
  changes (a scatter plot whose face colour goes through `none`, in recent
  versions: use a transparent colour instead).
- There are no playback controls, only a loop.
- The animations are checked against Chromium. SMIL is supported by all current
  browsers, but other engines are not part of the tests yet.

## Examples and docs

The documentation has a gallery of notebooks that explain each example, plus an
API reference built from the docstrings. It also shows how animations display
in Jupyter and Quarto.

## Development

```bash
uv run pytest
# the browser tests render every frame in Chromium, and are skipped without it
uv run --group browser playwright install chromium-headless-shell
uv run --group browser pytest tests/test_browser.py
uv run sphinx-build -W docs docs/_build/html
uv run ruff check && uv run ruff format --check && uv run mypy src
```

## License

MIT
