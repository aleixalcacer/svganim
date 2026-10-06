import matplotlib

matplotlib.use("Agg")

import base64
from xml.etree import ElementTree as ET

import matplotlib.pyplot as plt
import numpy as np
import pytest

from svganim import anim_to_svg


def _wave():
    fig, ax = plt.subplots()
    x = np.linspace(0, 2 * np.pi, 100)
    (line,) = ax.plot(x, np.sin(x))

    def update(i):
        line.set_ydata(np.sin(x + i / 10))

    return fig, update


def test_only_the_line_is_animated():
    fig, update = _wave()
    svg = anim_to_svg(fig, update, n_frames=10)
    assert svg.count("<animate ") == 1
    assert 'attributeName="d"' in svg
    assert svg.count(";") > 10  # one value per frame
    plt.close(fig)


def test_notebook_display_is_an_img_with_the_svg():
    fig, update = _wave()
    svg = anim_to_svg(fig, update, n_frames=3)
    assert isinstance(svg, str)
    html = svg._repr_html_()
    assert html.startswith('<img src="data:image/svg+xml;base64,')
    payload = html.split("base64,")[1].rstrip('">')
    assert base64.b64decode(payload).decode() == svg
    plt.close(fig)


def test_output_is_reproducible():
    fig, update = _wave()
    a = anim_to_svg(fig, update, n_frames=5)
    b = anim_to_svg(fig, update, n_frames=5)
    assert a == b
    plt.close(fig)


def test_writes_file(tmp_path):
    fig, update = _wave()
    out = tmp_path / "wave.svg"
    svg = anim_to_svg(fig, update, n_frames=3, path=out)
    assert out.read_text(encoding="utf-8") == svg
    plt.close(fig)


def test_changing_vertex_count_is_fine():
    fig, ax = plt.subplots()
    (line,) = ax.plot([0, 1], [0, 1])
    anim_to_svg(fig, lambda i: line.set_data(range(i + 2), range(i + 2)), 4)
    plt.close(fig)


def test_scatter_animates_positions_and_colors():
    fig, ax = plt.subplots()
    sc = ax.scatter([0, 1], [0, 1], c=["red", "blue"])
    ax.set_xlim(-1, 5)

    def update(i):
        sc.set_offsets([[i, 0], [1, i]])
        sc.set_facecolor(["red", "blue"] if i % 2 else ["blue", "red"])

    svg = anim_to_svg(fig, update, n_frames=4)
    assert 'attributeName="x"' in svg and 'attributeName="fill"' in svg
    plt.close(fig)


def test_structure_change_raises():
    fig, ax = plt.subplots()
    ax.set_xlim(0, 5)

    def update(i):
        ax.plot([0, 1], [0, i])

    with pytest.raises(ValueError, match="structure"):
        anim_to_svg(fig, update, n_frames=3)
    plt.close(fig)


def test_invalid_arguments():
    fig, update = _wave()
    with pytest.raises(ValueError):
        anim_to_svg(fig, update, n_frames=0)
    plt.close(fig)


def test_raster_images_are_rejected():
    fig, ax = plt.subplots()
    ax.imshow(np.zeros((4, 4)))
    with pytest.raises(ValueError, match="raster"):
        anim_to_svg(fig, lambda i: None, n_frames=2)
    plt.close(fig)


def test_rasterized_artists_are_rejected():
    fig, ax = plt.subplots()
    ax.scatter([0, 1], [0, 1], rasterized=True)
    with pytest.raises(ValueError, match="raster"):
        anim_to_svg(fig, lambda i: None, n_frames=2)
    plt.close(fig)


def test_pcolormesh_is_vector():
    fig, ax = plt.subplots()
    mesh = ax.pcolormesh(np.zeros((3, 3)), vmin=0, vmax=3)
    svg = anim_to_svg(fig, lambda i: mesh.set_array(np.full((3, 3), i)), n_frames=3)
    assert "<image" not in svg and 'attributeName="fill"' in svg
    plt.close(fig)


def test_bars_animate_geometry():
    fig, ax = plt.subplots()
    bars = ax.bar([0, 1], [1, 1])
    ax.set_ylim(0, 5)

    def update(i):
        for bar, h in zip(bars, (1 + i, 4 - i), strict=True):
            bar.set_height(h)

    svg = anim_to_svg(fig, update, n_frames=4)
    assert 'attributeName="d"' in svg
    plt.close(fig)


def test_translate_uses_animate_transform():
    from svganim._core import _animation

    el = _animation("transform", ["translate(1, 2)", "translate(3,4)"], [0, 0.5], 1)
    assert el.tag.endswith("animateTransform")
    assert el.get("type") == "translate"
    assert el.get("values") == "1 2;3 4"


def test_compound_transform_raises():
    from svganim._core import _animation

    with pytest.raises(ValueError, match="compound"):
        _animation(
            "transform", ["translate(1 2) scale(3)", "translate(1 2)"], [0, 1], 1
        )


def test_changing_transform_type_raises():
    from svganim._core import _animation

    with pytest.raises(ValueError, match="type"):
        _animation("transform", ["translate(1 2)", "scale(2)"], [0, 1], 1)


def _animations(svg):
    root = ET.fromstring(svg)
    return [el for el in root.iter() if el.tag.rpartition("}")[2].startswith("animate")]


def _by_name(svg, name):
    (found,) = [a for a in _animations(svg) if a.get("attributeName") == name]
    return found


def _moving_marker(n, x_of):
    fig, ax = plt.subplots()
    sc = ax.scatter([0], [0])
    ax.set(xlim=(0, 40), ylim=(-1, 1))
    return fig, lambda i: sc.set_offsets([[x_of(i), 0]]), n


def test_default_is_stepwise():
    fig, update, n = _moving_marker(30, lambda i: i)
    svg = anim_to_svg(fig, update, n)
    assert {a.get("calcMode") for a in _animations(svg)} == {"discrete"}
    plt.close(fig)


def test_interpolate_uses_linear_mode():
    fig, update, n = _moving_marker(30, lambda i: i)
    x = _by_name(anim_to_svg(fig, update, n, interpolate=True), "x")
    assert x.get("calcMode") == "linear"
    assert x.get("keyTimes").startswith("0;") and x.get("keyTimes").endswith(";1")
    plt.close(fig)


def test_held_states_only_glide_before_the_jump():
    fig, update, n = _moving_marker(20, lambda i: 0 if i < 10 else 20)
    x = _by_name(anim_to_svg(fig, update, n, interpolate=True), "x")
    values = x.get("values").split(";")
    # frames 0, 9 | 10, 19 | held last value: runs of equal values are trimmed
    assert len(values) == 5
    assert values[0] == values[1] != values[2] == values[3] == values[4]
    plt.close(fig)


def test_colour_fade_is_interpolated():
    fig, ax = plt.subplots()
    sc = ax.scatter([0], [0])
    svg = anim_to_svg(
        fig,
        lambda i: sc.set_facecolor((1 - i / 11, 0, i / 11)),
        n_frames=12,
        interpolate=True,
    )
    fill = _by_name(svg, "fill")
    assert fill.get("calcMode") == "linear"
    assert fill.get("values").startswith("#ff0000")
    plt.close(fig)


def test_changing_vertex_count_stays_stepwise():
    fig, ax = plt.subplots()
    (line,) = ax.plot([0, 1], [0, 1])
    ax.set(xlim=(0, 6), ylim=(0, 6))
    update = lambda i: line.set_data(range(i + 2), range(i + 2))  # noqa: E731
    d = _by_name(anim_to_svg(fig, update, 5, interpolate=True), "d")
    assert d.get("calcMode") == "discrete"
    plt.close(fig)


def test_keytimes_are_valid_for_every_animation():
    fig, ax = plt.subplots()
    x = np.linspace(0, 6, 50)
    (line,) = ax.plot(x, np.sin(x))
    sc = ax.scatter([0], [0], c=["red"])

    def update(i):
        line.set_ydata(np.sin(x + i / 5))
        sc.set_offsets([[i / 4, 0]])
        sc.set_facecolor((1 - i / 19, 0, i / 19))

    for interpolate in (False, True):
        svg = anim_to_svg(fig, update, 20, interpolate=interpolate)
        for a in _animations(svg):
            times = [float(t) for t in a.get("keyTimes").split(";")]
            assert len(times) == len(a.get("values").split(";"))
            assert times[0] == 0
            assert all(b > a_ for a_, b in zip(times, times[1:], strict=False))
            if a.get("calcMode") == "linear":
                assert times[-1] == 1
    plt.close(fig)


def test_translate_is_interpolated():
    from svganim._core import _animation

    values = [f"translate({i} {2 * i})" for i in range(6)]
    times = [i / 6 for i in range(6)]
    el = _animation("transform", values, times, 1, interpolate=True)
    assert el.get("calcMode") == "linear"
    assert el.get("values") == "0 0;1 2;2 4;3 6;4 8;5 10;5 10"


def test_non_numeric_attributes_stay_stepwise():
    from svganim._core import _animation

    for name, values in (
        ("clip-path", ["url(#a1)", "url(#b2)", "url(#c3)"]),
        ("fill", ["none", "#ffffff", "#000000"]),
    ):
        el = _animation(name, values, [0, 0.3, 0.6], 1, interpolate=True)
        assert el.get("calcMode") == "discrete"


def test_structure_error_names_the_element():
    fig, ax = plt.subplots()
    ax.set(xlim=(0, 5), ylim=(0, 5))
    with pytest.raises(ValueError, match=r"frame 1.*found <g> in 'line2d_\d+'"):
        anim_to_svg(fig, lambda i: ax.plot([0, 1], [0, i]), n_frames=3)
    plt.close(fig)
