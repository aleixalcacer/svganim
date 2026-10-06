from __future__ import annotations

import base64
from collections.abc import Callable
from pathlib import Path
from xml.etree import ElementTree as ET

from matplotlib.figure import Figure

from svganim._artists import _extract, _Key, _merge, _put_back, _Tagger
from svganim._diff import _Tracked
from svganim._svg import _Defs, _render


class SvgAnimation(str):
    """The SVG text, which Jupyter and Quarto display as an animated image."""

    __slots__ = ()

    def _repr_html_(self) -> str:
        data = base64.b64encode(self.encode("utf-8")).decode("ascii")
        return f'<img src="data:image/svg+xml;base64,{data}">'


def anim_to_svg(
    fig: Figure,
    update: Callable[[int], object],
    n_frames: int,
    fps: float = 20,
    hold: float = 1.0,
    path: str | Path | None = None,
    *,
    precision: int = 3,
    interpolate: bool = False,
) -> SvgAnimation:
    """Render ``fig`` as a looping SVG animation and return it as a string.

    The result is a :class:`SvgAnimation`, a :class:`str` subclass, so it can be
    written or embedded as is. As the last expression of a Jupyter or Quarto
    cell it is displayed as an animated image.

    ``update(i)`` is called before frame ``i`` is rendered. Frame 0 becomes the
    base document; every attribute that differs in later frames gets a SMIL
    animation, so static parts cost nothing.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to render.
    update : callable
        Called as ``update(i)`` before frame ``i`` is rendered. It should modify
        artists (``set_data``, ``set_offsets``, ``set_visible``, ...). Artists can
        also come and go: show or hide them with ``set_visible``, which keeps
        ``update`` repeatable, or create and remove them. Its return value is
        ignored. The picture must depend only on ``i``: ``update`` is called once
        per frame, in order, so a function that keeps state gives a different
        animation on every call. Compute a simulation beforehand and let
        ``update`` show its state ``i``.
    n_frames : int
        Number of frames.
    fps : float, default 20
        Frames per second.
    hold : float, default 1.0
        Seconds to hold the last frame before the animation loops.
    path : str or pathlib.Path, optional
        If given, the SVG is also written to this file.
    precision : int, default 3
        Decimals kept in coordinates. Lower values give smaller files.
    interpolate : bool, default False
        By default the SVG switches between the rendered frames. With ``True``,
        numeric attributes (paths, positions, colours, opacities) are instead
        interpolated linearly between frames, so shapes glide and colours fade
        from one state to the next, which suits animations that show discrete
        states (algorithm iterations, for example). Matplotlib's path
        simplification is turned off so that paths keep a constant vertex
        count, which makes the file larger. Attributes that cannot be
        interpolated, such as a path whose vertex count changes, keep switching
        stepwise.

    Returns
    -------
    SvgAnimation
        The animated SVG document, as a ``str`` subclass.

    Raises
    ------
    ValueError
        If an argument is out of range, if the figure contains raster images
        (``imshow``, ``rasterized=True``), if an element is of another kind than it
        was in the first frame that has it (the message names the element), if two
        artists share a gid, or if a transform cannot be animated.

    Notes
    -----
    ``update`` changes ``fig`` as it goes, so when the call returns the figure is
    left as the last frame set it. Call ``update(0)`` to go back to the first one.

    An artist that is not drawn in every frame is shown only in the frames where
    matplotlib draws it, and so are the elements that an artist has in some frames
    and not in others at its end: the letters of a text that changes length, the
    points of a scatter plot, the ticks of an axis.

    To follow each artist from frame to frame, svganim gives it a gid while it
    works and takes it off at the end; a gid that you set yourself is kept, and two
    artists cannot share one.

    Examples
    --------
    >>> anim_to_svg(fig, update, n_frames=60, fps=20, path="wave.svg")  # doctest: +SKIP
    """
    if n_frames < 1:
        raise ValueError("n_frames must be at least 1")
    if fps <= 0 or hold < 0:
        raise ValueError("fps must be positive and hold non-negative")

    simplify = not interpolate
    duration = n_frames / fps + hold
    times = [i / fps / duration for i in range(n_frames)]

    # The document and each artist are followed separately, because artists can come
    # and go: the document is what is left once they are cut out of a frame.
    tagger = _Tagger()
    document = _Tracked()
    artists: dict[str, _Tracked] = {}
    orders: dict[ET.Element, list[_Key]] = {}
    try:
        for i in range(n_frames):
            update(i)
            tagger.tag(fig)
            root = _render(fig, precision, simplify)
            # Definitions first: an artist can carry its own (a marker, for one), and
            # they leave with it when it is cut out.
            if i == 0:
                defs = _Defs(root)
            else:
                defs.merge(root)
            found, parents = _extract(root)
            stands_for = document.see(i, root, None)
            for gid, (el, parent) in found.items():
                artists.setdefault(gid, _Tracked()).see(i, el, stands_for[id(parent)])
            for parent, keys in parents:
                _merge(orders.setdefault(stands_for[id(parent)], []), keys)
    finally:
        tagger.restore()

    base = document.element(n_frames, times, duration, interpolate)
    _put_back(
        orders,
        {
            gid: art.element(n_frames, times, duration, interpolate)
            for gid, art in artists.items()
        },
    )

    svg = ET.tostring(base, encoding="unicode")
    if path is not None:
        Path(path).write_text(svg, encoding="utf-8")
    return SvgAnimation(svg)
