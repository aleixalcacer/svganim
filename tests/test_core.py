import matplotlib

matplotlib.use("Agg")

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
