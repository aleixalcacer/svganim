"""Check the animation in a real browser.

The other tests inspect the SVG markup. These ones check what matters: at the
moment of frame ``i`` the browser paints the same picture as the plain,
non-animated SVG that matplotlib writes for that frame. Both pictures come from
the same engine, so any difference is the animation's, not the renderer's.

They need Playwright and a Chromium build (``uv run --group browser playwright
install chromium-headless-shell``) and are skipped when either is missing.
"""

import matplotlib

matplotlib.use("Agg")

import io
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
from PIL import Image

from svganim import anim_to_svg

# The CI sets this, so that a missing browser fails there instead of skipping.
REQUIRED = bool(os.environ.get("SVGANIM_REQUIRE_BROWSER"))

if REQUIRED:
    from playwright import sync_api
else:
    sync_api = pytest.importorskip("playwright.sync_api")


@pytest.fixture(scope="module")
def page():
    with sync_api.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except sync_api.Error as err:
            if REQUIRED:
                raise
            pytest.skip(f"no Chromium available: {str(err).splitlines()[0]}")
        yield browser.new_page(viewport={"width": 1000, "height": 800})
        browser.close()


def _paint(page, svg, time=None):
    """Screenshot ``svg``, frozen at ``time`` seconds when it is animated."""
    page.set_content(f'<body style="margin:0;background:#fff">{svg}</body>')
    page.evaluate(
        """time => {
            const svg = document.querySelector('svg');
            svg.pauseAnimations();
            if (time !== null) svg.setCurrentTime(time);
        }""",
        time,
    )
    png = page.locator("svg").first.screenshot()
    return np.asarray(Image.open(io.BytesIO(png)).convert("RGB"), dtype=int)


def _plain_frame(page, fig, update, i, simplify):
    """What matplotlib itself draws for frame ``i``, with no animation."""
    update(i)
    buf = io.BytesIO()
    with mpl.rc_context({"svg.fonttype": "path", "path.simplify": simplify}):
        fig.savefig(buf, format="svg")
    return _paint(page, buf.getvalue().decode())


# Largest per-channel gap, out of 255, that still counts as anti-aliasing noise at
# a marker or path edge. Chromium's rasteriser is not fully deterministic: over
# about two thousand comparisons the gap was at most 10, and above 16 for no pixel.
# A frame that is wrong differs by 34 to 255, over hundreds of pixels.
NOISE = 16


def _difference(a, b):
    assert a.shape == b.shape
    return np.abs(a - b).max(axis=2)


# Ten frames at 10 fps with no hold last exactly one second, so the key times
# (i/10) are written without rounding. keyTimes keep six significant digits, which
# for other lengths moves a frame change by microseconds: harmless to watch, but
# enough to put a probe taken right at the change on the wrong side of it.
FRAMES = 10
FPS = 10

# How long after a key time an interpolated animation is sampled. At the key time
# itself the browser's clock resolution (about 1e-7 s) can leave an attribute that
# switches stepwise on the previous frame, and much later the interpolated ones
# have visibly moved towards the next. Measured here, 2e-7 and 4e-7 s work for
# every scenario, while 1e-8 s does not and 1e-6 s already shifts bars.
AFTER = 2e-7


def _wave():
    fig, ax = plt.subplots(figsize=(5, 3))
    x = np.linspace(0, 6, 200)
    (line,) = ax.plot(x, np.sin(x))

    def update(i):
        line.set_ydata(np.sin(x + i / 10))

    return fig, update, FRAMES


def _bars():
    heights = np.random.default_rng(3).integers(1, 17, size=(FRAMES, 12))
    fig, ax = plt.subplots(figsize=(5, 3))
    bars = ax.bar(range(12), heights[0])
    ax.axis("off")

    def update(i):
        for bar, h in zip(bars, heights[i], strict=True):
            bar.set_height(h)
            bar.set_color(plt.cm.viridis(h / 16))

    return fig, update, len(heights)


def _clusters():
    rng = np.random.default_rng(0)
    points = rng.random((60, 2))
    labels = rng.integers(0, 3, size=(FRAMES, 60))
    centers = rng.random((FRAMES, 3, 2))
    colors = np.array(["#4c72b0", "#dd8452", "#55a868"])
    fig, ax = plt.subplots(figsize=(5, 3))
    scatter = ax.scatter(*points.T, c=colors[labels[0]], s=14)
    stars = ax.scatter(*centers[0].T, c=colors, marker="X", s=120, zorder=3)
    ax.axis("off")

    def update(i):
        scatter.set_facecolor(colors[labels[i]])
        stars.set_offsets(centers[i])

    return fig, update, len(labels)


def _growing_trail():
    steps = np.cumsum(np.random.default_rng(1).normal(size=(FRAMES, 2)), axis=0)
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.set(xlim=(steps[:, 0].min() - 1, steps[:, 0].max() + 1))
    ax.set(ylim=(steps[:, 1].min() - 1, steps[:, 1].max() + 1))
    (trail,) = ax.plot(*steps[:1].T, "-", color="k")
    (dot,) = ax.plot(*steps[:1].T, "o", color="tab:red")

    def update(i):
        trail.set_data(*steps[: i + 1].T)
        dot.set_data(*steps[i : i + 1].T)

    return fig, update, len(steps)


SCENARIOS = {
    "wave": _wave,
    "bars": _bars,
    "clusters": _clusters,
    "growing trail": _growing_trail,
}


@pytest.mark.parametrize("interpolate", [False, True], ids=["stepwise", "interpolate"])
@pytest.mark.parametrize("name", SCENARIOS)
def test_each_frame_is_painted_as_matplotlib_draws_it(page, name, interpolate):
    fig, update, n = SCENARIOS[name]()
    # A high precision keeps rounding out of the comparison: what is left is the
    # animation itself, which has to match the plain frame pixel for pixel.
    svg = anim_to_svg(
        fig, update, n, fps=FPS, hold=0, precision=6, interpolate=interpolate
    )
    for i in range(n):
        # Stepwise frames last 1/fps, so sample the middle of each. Interpolated
        # ones are exact at their key time, so sample just after it (see AFTER).
        time = i / FPS + AFTER if interpolate else (i + 0.5) / FPS
        drawn = _paint(page, svg, time)
        expected = _plain_frame(page, fig, update, i, simplify=not interpolate)
        assert _difference(drawn, expected).max() <= NOISE, f"frame {i} differs"
    plt.close(fig)


def test_the_last_frame_is_held_before_the_loop_restarts(page):
    fig, update, n = _wave()
    svg = anim_to_svg(fig, update, n, fps=FPS, hold=2.0, precision=6)
    held = _paint(page, svg, n / FPS + 1.0)
    expected = _plain_frame(page, fig, update, n - 1, simplify=True)
    assert _difference(held, expected).max() <= NOISE
    plt.close(fig)


def test_the_comparison_can_tell_frames_apart(page):
    # Guards the test itself: if both pictures were blank, everything above
    # would pass without checking anything.
    fig, update, n = _wave()
    svg = anim_to_svg(fig, update, n, fps=FPS, hold=0, precision=6)
    first = _paint(page, svg, 0.05)
    last = _paint(page, svg, (n - 1) / FPS + 0.05)
    assert _difference(first, last).max() > 100
    plt.close(fig)


def test_default_precision_stays_close_to_the_plain_frame(page):
    # Rounding to 3 decimals moves glyph edges by a fraction of a pixel, so only
    # a loose bound holds: a handful of edge pixels, never a different picture.
    fig, update, n = _wave()
    svg = anim_to_svg(fig, update, n, fps=FPS, hold=0)
    for i in (0, n - 1):
        drawn = _paint(page, svg, (i + 0.5) / FPS)
        difference = _difference(drawn, _plain_frame(page, fig, update, i, True))
        assert (difference > 32).mean() < 0.01
    plt.close(fig)
