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

Turn a matplotlib figure and a per-frame update function into one
self-contained, looping, animated SVG.

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

What you give up: playback controls, and changes to the number of elements or
the text between frames (see [Limitations](#limitations)). If you need those,
use `HTMLWriter` or `to_jshtml`.

## Install

```bash
pip install svganim
```

## Usage

```python
import matplotlib.pyplot as plt
import numpy as np
from svganim import anim_to_svg

fig, ax = plt.subplots()
x = np.linspace(0, 2 * np.pi, 200)
(line,) = ax.plot(x, np.sin(x))


def update(i):
    line.set_ydata(np.sin(x + i / 10))


anim_to_svg(fig, update, n_frames=60, fps=20, hold=1.0, path="wave.svg")
```

```html
<img src="wave.svg" alt="A moving sine wave">
```

In Jupyter and Quarto, end a cell with the call and the animation is displayed,
also in the rendered HTML. Call `plt.close(fig)` first, or the notebook also
shows matplotlib's static figure.

`update` must change artists that already exist (`set_data`, `set_offsets`,
`set_color`, ...), not create or remove them. A line whose data grows is fine,
so draw trails and curves with `set_data` on a single line.

### `anim_to_svg(fig, update, n_frames, fps=20, hold=1.0, path=None, *, precision=3, interpolate=False)`

| Argument      | Description                                                                                                                               |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `fig`         | The matplotlib figure to render.                                                                                                          |
| `update`      | Called as `update(i)` before frame `i` is rendered.                                                                                       |
| `n_frames`    | Number of frames.                                                                                                                         |
| `fps`         | Frames per second.                                                                                                                        |
| `hold`        | Seconds to hold the last frame before looping.                                                                                            |
| `path`        | If given, the SVG is also written to this file.                                                                                           |
| `precision`   | Decimals kept in coordinates. Lower means smaller files.                                                                                  |
| `interpolate` | If `True`, shapes glide and colours fade between frames instead of switching. See the [k-means example](https://svganim.readthedocs.io/en/latest/examples/kmeans.html). |

Returns the SVG as a string. Raises `ValueError` if the figure breaks a rule
below; the message names the element that changed.

## How it works

Each frame is rendered to SVG and the first one becomes the base document. Later
frames are compared with it, and every attribute that changes gets a
[SMIL](https://developer.mozilla.org/docs/Web/SVG/SMIL) animation. Elements that
never change are left untouched.

## Limitations

- The number of SVG elements must be the same in every frame: no new artists,
  no changing text, no `imshow`.
- There are no playback controls, only a loop.

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
```

## License

MIT
