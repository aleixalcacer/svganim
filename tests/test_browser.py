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
    page.add_style_tag(content="svg * { shape-rendering: crispEdges !important; }")
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


# The pictures are painted without anti-aliasing, so that they are compared pixel by
# pixel and not shade by shade. Chromium smooths the edge of an animated element a
# little differently from that of a static one, which is noise that no threshold on
# the shades separates well. Without it the two pictures of a frame are identical,
# except that a sub-pixel difference can flip a pixel at an edge, as it does for two
# or three in a 3D scatter plot of overlapping markers. A wrong frame differs in
# hundreds.
FEW_PIXELS = 8


def _difference(a, b):
    assert a.shape == b.shape
    return np.abs(a - b).max(axis=2)


def _same(a, b):
    return (_difference(a, b) > 0).sum() <= FEW_PIXELS


# Ten frames at 10 fps with no hold last exactly one second, so the key times
# (i/10) are written without rounding. keyTimes keep six significant digits, which
# for other lengths moves a frame change by microseconds: harmless to watch, but
# enough to put a probe taken right at the change on the wrong side of it.
FRAMES = 10
FPS = 10
# The property cases only need a few steps. Five steps at five frames per second also
# last exactly one second, so their key times are exact too.
STEPS = 5

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


def _coming_and_going():
    """Dots that are drawn from their own frame on, and a line that blinks."""
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.set(xlim=(0, 10), ylim=(0, 10))
    x = np.linspace(0, 10, 50)
    (wave,) = ax.plot(x, 5 + np.sin(x), color="0.6")
    dots = [ax.plot([k + 0.5], [1 + 0.8 * k], "o")[0] for k in range(FRAMES)]
    (blink,) = ax.plot(x, 8 - 0.1 * x, color="tab:red", lw=2)

    def update(i):
        wave.set_ydata(5 + np.sin(x + i / 2))
        for k, dot in enumerate(dots):
            dot.set_visible(k <= i)
        blink.set_visible(i in (2, 3, 4, 7))

    return fig, update, FRAMES


def _property_case(make, setter, values):
    """A figure with one artist whose style property takes ``values``, one per frame."""

    def scenario():
        fig, artist = make()
        return fig, lambda i: setter(artist, values[i]), STEPS

    return scenario


def _line_artist():
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.set_ylim(-1.5, 1.5)
    x = np.linspace(0, 6, 30)
    return fig, ax.plot(x, np.sin(x), lw=3)[0]


def _zigzag_artist():
    """A thick line with sharp corners, where the join of the stroke is plain to see."""
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.set(xlim=(-0.5, 4.5), ylim=(-0.5, 2.5))
    return fig, ax.plot([0, 1, 2, 3, 4], [0, 2, 0, 2, 0], lw=14)[0]


def _scatter_artist():
    fig, ax = plt.subplots(figsize=(3, 2))
    return fig, ax.scatter(np.arange(5), np.arange(5) % 3, s=80)


def _bars_artist():
    fig, ax = plt.subplots(figsize=(3, 2))
    return fig, ax.bar(range(3), [1, 2, 3], edgecolor="k")


def _text_artist():
    fig, ax = plt.subplots(figsize=(3, 2))
    return fig, ax.text(0.4, 0.4, "7", fontsize=40)


def _each_bar(setter):
    return lambda bars, value: [setter(bar, value) for bar in bars]


def _cycle(*items):
    return [items[i % len(items)] for i in range(STEPS)]


# Properties that matplotlib leaves out of the SVG when they have their default value,
# so that some frames lack the attribute that others have.
PROPERTIES = {
    "alpha up to 1": _property_case(
        _line_artist, lambda a, v: a.set_alpha(v), np.linspace(0.2, 1, STEPS)
    ),
    "alpha down from 1": _property_case(
        _line_artist, lambda a, v: a.set_alpha(v), np.linspace(1, 0.2, STEPS)
    ),
    "line width down to 1": _property_case(
        _line_artist, lambda a, v: a.set_linewidth(v), np.linspace(3, 1, STEPS)
    ),
    "line width up from 1": _property_case(
        _line_artist, lambda a, v: a.set_linewidth(v), np.linspace(1, 3, STEPS)
    ),
    "line style": _property_case(
        _line_artist, lambda a, v: a.set_linestyle(v), _cycle("-", "--", ":", "-.")
    ),
    "cap style": _property_case(
        _line_artist,
        lambda a, v: a.set_solid_capstyle(v),
        _cycle("butt", "round", "projecting"),
    ),
    "join style": _property_case(
        _zigzag_artist,
        lambda a, v: a.set_solid_joinstyle(v),
        _cycle("miter", "round", "bevel"),
    ),
    "scatter alpha up to 1": _property_case(
        _scatter_artist, lambda a, v: a.set_alpha(v), np.linspace(0.2, 1, STEPS)
    ),
    "scatter edge width": _property_case(
        _scatter_artist, lambda a, v: a.set_linewidths(v), np.linspace(0, 4, STEPS)
    ),
    "bar alpha up to 1": _property_case(
        _bars_artist,
        _each_bar(lambda b, v: b.set_alpha(v)),
        np.linspace(0.2, 1, STEPS),
    ),
    "bar edge width down to 1": _property_case(
        _bars_artist,
        _each_bar(lambda b, v: b.set_linewidth(v)),
        np.linspace(4, 1, STEPS),
    ),
    "text alpha up to 1": _property_case(
        _text_artist, lambda a, v: a.set_alpha(v), np.linspace(0.2, 1, STEPS)
    ),
    "bar face colour through none": _property_case(
        _bars_artist,
        _each_bar(lambda b, v: b.set_facecolor(v)),
        _cycle("none", "tab:red", "none", "tab:blue"),
    ),
    "bar edge colour through none": _property_case(
        _bars_artist,
        _each_bar(lambda b, v: b.set_edgecolor(v)),
        _cycle("none", "k", "none", "tab:red"),
    ),
    "text colour": _property_case(
        _text_artist, lambda a, v: a.set_color(v), _cycle("black", "red", "blue")
    ),
}


def _text_changing_length():
    """A title and a counter whose number of digits goes up and down."""
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    counter = ax.text(0.5, 0.4, "", ha="center", fontsize=30)
    words = ["a", "bb", "ccc", "dddd", "ccc", "bb", "a", "ee", "fffff", "g"]
    numbers = ["9", "10", "99", "100", "1000", "100", "10", "9", "99", "9"]

    def update(i):
        ax.set_title(words[i])
        counter.set_text(numbers[i])

    return fig, update, FRAMES


def _growing_scatter():
    """A scatter that gains points and, later, loses them from the front."""
    points = np.random.default_rng(4).random((FRAMES + 1, 2))
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.set(xlim=(0, 1), ylim=(0, 1))
    scatter = ax.scatter([], [], s=60)

    def update(i):
        scatter.set_offsets(points[: i + 1] if i < 6 else points[i - 4 : i + 1])

    return fig, update, FRAMES


def _growing_markers():
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.set(xlim=(0, 10), ylim=(-2, 2))
    (line,) = ax.plot([], [], "o-")
    x = np.linspace(0, 9, FRAMES)

    def update(i):
        line.set_data(x[: i + 1], np.sin(x[: i + 1]))

    return fig, update, FRAMES


def _zooming_axes():
    """Axis limits that change, and with them the number and the text of the ticks."""
    fig, ax = plt.subplots(figsize=(5, 3))
    x = np.linspace(0, 100, 200)
    ax.plot(x, np.sin(x / 7))
    widths = [100, 80, 55, 30, 12, 6, 3, 8, 40, 100]

    def update(i):
        ax.set_xlim(0, widths[i])

    return fig, update, FRAMES


def _growing_data_with_rescaling_axes():
    fig, ax = plt.subplots(figsize=(5, 3))
    x = np.linspace(0, 10, FRAMES)
    (line,) = ax.plot([], [])

    def update(i):
        line.set_data(x[: i + 1], (x[: i + 1] ** 2) * 10)
        ax.relim()
        ax.autoscale_view()

    return fig, update, FRAMES


def _animated_heatmap():
    data = np.random.default_rng(5).random((FRAMES, 10, 10))
    fig, ax = plt.subplots(figsize=(4, 3))
    image = ax.imshow(data[0], vmin=0, vmax=1)
    return fig, lambda i: image.set_data(data[i]), FRAMES


def _heatmap_with_colorbar():
    """The colorbar is an image too, and does not change."""
    data = np.random.default_rng(6).random((FRAMES, 8, 8))
    fig, ax = plt.subplots(figsize=(4, 3))
    image = ax.imshow(data[0], vmin=0, vmax=1)
    fig.colorbar(image)
    return fig, lambda i: image.set_data(data[i]), FRAMES


def _rotating_surface():
    fig = plt.figure(figsize=(3, 3))
    ax = fig.add_subplot(projection="3d")
    x, y = np.meshgrid(np.linspace(-2, 2, 12), np.linspace(-2, 2, 12))
    ax.plot_surface(x, y, np.sin(x) * np.cos(y), cmap="viridis")
    return fig, lambda i: ax.view_init(elev=25, azim=36 * i), FRAMES


SCENARIOS = {
    "wave": _wave,
    "bars": _bars,
    "clusters": _clusters,
    "growing trail": _growing_trail,
    "coming and going": _coming_and_going,
    "text changing length": _text_changing_length,
    "growing scatter": _growing_scatter,
    "growing markers": _growing_markers,
    "zooming axes": _zooming_axes,
    "rescaling axes": _growing_data_with_rescaling_axes,
    "animated heatmap": _animated_heatmap,
    "heatmap with colorbar": _heatmap_with_colorbar,
    "rotating 3D surface": _rotating_surface,
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
        assert _same(drawn, expected), f"frame {i} differs"
    plt.close(fig)


def test_the_last_frame_is_held_before_the_loop_restarts(page):
    fig, update, n = _wave()
    svg = anim_to_svg(fig, update, n, fps=FPS, hold=2.0, precision=6)
    held = _paint(page, svg, n / FPS + 1.0)
    expected = _plain_frame(page, fig, update, n - 1, simplify=True)
    assert _same(held, expected)
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


def _recording(fig, update, simplify):
    """Wrap ``update`` so that each frame is also drawn plainly, as it happens.

    ``update`` below creates and removes artists, so it cannot be called again
    afterwards to redraw a frame: the figure would already be in its final state.
    """
    plains = []

    def recording(i):
        update(i)
        buf = io.BytesIO()
        with mpl.rc_context({"svg.fonttype": "path", "path.simplify": simplify}):
            fig.savefig(buf, format="svg")
        plains.append(buf.getvalue().decode())

    return recording, plains


@pytest.mark.parametrize("replace", [False, True], ids=["created", "redrawn"])
def test_artists_created_and_removed_in_update(page, replace):
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.set(xlim=(0, 10), ylim=(0, 10))
    x = np.linspace(0, 10, 50)
    ax.plot(x, 5 + np.sin(x), color="0.6")
    made = {}

    def update(i):
        if replace:  # clear and draw again, which is how many people animate
            if "line" in made:
                made["line"].remove()
            made["line"] = ax.plot(x, 2 + np.cos(x + i / 2), color="tab:red")[0]
        else:
            if i == 3:
                made["a"] = ax.plot(x, 8 - 0.2 * x, color="tab:red", lw=2)[0]
            if i == 5:
                made["b"] = ax.scatter(x[::7], 1 + 0.5 * x[::7] % 3, color="tab:green")
            if i == 8:
                made["a"].remove()

    recording, plains = _recording(fig, update, simplify=True)
    svg = anim_to_svg(fig, recording, FRAMES, fps=FPS, hold=0, precision=6)
    for i in range(FRAMES):
        drawn = _paint(page, svg, (i + 0.5) / FPS)
        assert _same(drawn, _paint(page, plains[i])), f"frame {i}"
    plt.close(fig)


@pytest.mark.parametrize("interpolate", [False, True], ids=["stepwise", "interpolate"])
@pytest.mark.parametrize("name", PROPERTIES)
def test_a_property_that_reaches_its_default_value_is_painted_right(
    page, name, interpolate
):
    fig, update, n = PROPERTIES[name]()
    svg = anim_to_svg(
        fig, update, n, fps=n, hold=0, precision=6, interpolate=interpolate
    )
    for i in range(n):
        time = i / n + AFTER if interpolate else (i + 0.5) / n
        drawn = _paint(page, svg, time)
        expected = _plain_frame(page, fig, update, i, simplify=not interpolate)
        assert _same(drawn, expected), f"frame {i} differs"
    plt.close(fig)
