import matplotlib

matplotlib.use("Agg")

from xml.etree import ElementTree as ET

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import pytest

from svganim import SvgAnimation, SvgAnimWriter, ani_to_svg


def _wave():
    fig, ax = plt.subplots()
    x = np.linspace(0, 2 * np.pi, 50)
    (line,) = ax.plot(x, np.sin(x))
    return fig, line, x


def _n_values(svg):
    """How many values the one animation of the path has."""
    (values,) = {
        a.get("values")
        for a in ET.fromstring(svg).iter("{http://www.w3.org/2000/svg}animate")
        if a.get("attributeName") == "d"
    }
    return len(values.split(";"))


def test_registered_under_its_name():
    assert "svganim" in animation.writers.list()
    assert animation.writers["svganim"] is SvgAnimWriter


@pytest.mark.parametrize(
    "frames", [5, range(5), np.linspace(0, 1, 5), [(i, "a") for i in range(5)]]
)
def test_kinds_of_frames(tmp_path, frames):
    fig, line, x = _wave()

    def update(frame):
        shift = frame if np.isscalar(frame) else frame[0]
        line.set_ydata(np.sin(x + shift))

    out = tmp_path / "a.svg"
    animation.FuncAnimation(fig, update, frames=frames).save(
        out, writer=SvgAnimWriter(fps=10)
    )
    svg = out.read_text(encoding="utf-8")
    assert ET.fromstring(svg).tag.endswith("svg")
    assert _n_values(svg) == 5
    assert 'dur="0.5s"' in svg
    plt.close(fig)


def test_generator_with_save_count(tmp_path):
    fig, line, x = _wave()

    def gen():
        i = 0
        while True:
            yield i
            i += 1

    out = tmp_path / "a.svg"
    animation.FuncAnimation(
        fig, lambda i: line.set_ydata(np.sin(x + i)), frames=gen, save_count=4
    ).save(out, writer="svganim", fps=10)
    assert _n_values(out.read_text(encoding="utf-8")) == 4
    plt.close(fig)


def test_fargs_and_init_func(tmp_path):
    fig, line, x = _wave()
    calls = []

    def init():
        calls.append("init")
        line.set_ydata(np.zeros_like(x))

    def update(i, scale):
        calls.append(i)
        line.set_ydata(scale * np.sin(x + i))

    out = tmp_path / "a.svg"
    animation.FuncAnimation(fig, update, frames=3, fargs=(2,), init_func=init).save(
        out, writer="svganim"
    )
    assert calls[0] == "init"
    assert np.allclose(line.get_ydata(), 2 * np.sin(x + 2))
    plt.close(fig)


def test_artist_animation(tmp_path):
    fig, ax = plt.subplots()
    frames = [[ax.plot([0, 1], [0, i])[0]] for i in range(3)]
    out = tmp_path / "a.svg"
    animation.ArtistAnimation(fig, frames).save(out, writer="svganim", fps=1)
    svg = out.read_text(encoding="utf-8")
    assert svg.count('attributeName="visibility"') >= 2
    plt.close(fig)


def test_gids_are_taken_off_and_the_user_ones_kept(tmp_path):
    fig, ax = plt.subplots()
    x = np.arange(4)
    (kept,) = ax.plot(x, x)
    kept.set_gid("mine")
    (other,) = ax.plot(x, x[::-1])

    def update(i):
        other.set_ydata(x[::-1] + i)

    out = tmp_path / "a.svg"
    animation.FuncAnimation(fig, update, frames=3).save(out, writer="svganim")
    assert kept.get_gid() == "mine"
    assert other.get_gid() is None
    plt.close(fig)


def test_exception_leaves_no_file_and_no_gids(tmp_path):
    fig, line, x = _wave()

    def update(i):
        if i == 3:
            raise RuntimeError("boom")
        line.set_ydata(np.sin(x + i))

    out = tmp_path / "a.svg"
    with pytest.raises(RuntimeError, match="boom"):
        animation.FuncAnimation(fig, update, frames=6).save(out, writer="svganim")
    assert not out.exists()
    assert line.get_gid() is None
    plt.close(fig)


def test_one_frame_is_a_still_svg(tmp_path):
    fig, line, x = _wave()
    out = tmp_path / "a.svg"
    animation.FuncAnimation(fig, lambda i: None, frames=1).save(out, writer="svganim")
    svg = out.read_text(encoding="utf-8")
    assert "<animate" not in svg
    plt.close(fig)


@pytest.mark.filterwarnings("ignore:Can not start iterating")
def test_no_frames_is_an_error_and_no_file(tmp_path):
    fig, line, x = _wave()
    out = tmp_path / "a.svg"
    ani = animation.FuncAnimation(
        fig, lambda i: None, frames=lambda: iter(()), save_count=1
    )
    with pytest.raises(ValueError, match="no frames"):
        ani.save(out, writer="svganim")
    assert not out.exists()
    plt.close(fig)


def test_saving_twice_gives_the_same_file(tmp_path):
    fig, line, x = _wave()
    ani = animation.FuncAnimation(
        fig, lambda i: line.set_ydata(np.sin(x + i)), frames=4
    )
    a, b = tmp_path / "a.svg", tmp_path / "b.svg"
    ani.save(a, writer="svganim")
    ani.save(b, writer="svganim")
    assert a.read_text(encoding="utf-8") == b.read_text(encoding="utf-8")
    assert line.get_gid() is None
    plt.close(fig)


def test_ani_to_svg_returns_what_the_writer_writes(tmp_path):
    fig, line, x = _wave()
    ani = animation.FuncAnimation(
        fig, lambda i: line.set_ydata(np.sin(x + i)), frames=4
    )
    svg = ani_to_svg(ani, fps=10)
    ani.save(tmp_path / "a.svg", writer=SvgAnimWriter(fps=10))
    assert isinstance(svg, SvgAnimation)
    assert svg == (tmp_path / "a.svg").read_text(encoding="utf-8")
    plt.close(fig)


def test_interpolating_keeps_the_number_of_vertices_of_a_path(tmp_path):
    # matplotlib draws the figure after each update, which would simplify the paths
    # and make their vertex count change from frame to frame.
    fig, ax = plt.subplots()
    x = np.linspace(0, 6, 200)
    (line,) = ax.plot(x, np.sin(x))
    ani = animation.FuncAnimation(
        fig, lambda i: line.set_ydata(np.sin(x + i / 10)), frames=5
    )
    out = tmp_path / "a.svg"
    ani.save(out, writer=SvgAnimWriter(fps=5, interpolate=True))
    (values,) = {
        a.get("values")
        for a in ET.fromstring(out.read_text(encoding="utf-8")).iter(
            "{http://www.w3.org/2000/svg}animate"
        )
        if a.get("attributeName") == "d"
    }
    assert {v.count("L") for v in values.split(";")} == {199}
    plt.close(fig)
