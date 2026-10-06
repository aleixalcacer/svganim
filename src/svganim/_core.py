from __future__ import annotations

import base64
from collections.abc import Callable
from pathlib import Path
from xml.etree import ElementTree as ET

from matplotlib.figure import Figure

from svganim._artists import _extract, _merge, _put_back, _Tagger, _Tracked
from svganim._diff import _record_changes
from svganim._smil import _animation
from svganim._svg import _Defs, _props, _render, _tag, _walk


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
        (``imshow``, ``rasterized=True``), if the number or order of the SVG
        elements of an artist changes between frames (the message names the
        element), if two artists share a gid, or if a transform cannot be
        animated.

    Notes
    -----
    ``update`` changes ``fig`` as it goes, so when the call returns the figure is
    left as the last frame set it. Call ``update(0)`` to go back to the first one.

    An artist that is not drawn in every frame is shown only in the frames where
    matplotlib draws it. To follow each artist from frame to frame, svganim gives
    it a gid while it works and takes it off at the end; a gid that you set
    yourself is kept, and two artists cannot share one.

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

    # Each later frame is compared against the base and then discarded, so only
    # the values that change are kept: {(element index, attribute): {frame: value}}.
    # Artists are found by their gid instead, since they can come and go.
    changes: dict[tuple[int, str], dict[int, str]] = {}
    tracked: dict[str, _Tracked] = {}
    orders: dict[int, list] = {}
    tagger = _Tagger()
    try:
        for i in range(n_frames):
            update(i)
            tagger.tag(fig)
            root = _render(fig, precision, simplify)
            if i == 0:
                base, defs = root, _Defs(root)
            else:
                defs.merge(root)
            found, parents = _extract(root)
            walked = list(_walk(root))
            index = {id(el): k for k, (el, _) in enumerate(walked)}
            for gid, (el, parent) in found.items():
                if gid in tracked:
                    tracked[gid].see(i, el, index[id(parent)])
                else:
                    tracked[gid] = _Tracked(i, el, index[id(parent)])
            for parent, keys in parents:
                _merge(orders.setdefault(index[id(parent)], []), keys)
            if i == 0:
                base_walked = walked
                base_props = [_props(el) for el, _ in walked]
            else:
                _record_changes(changes, i, walked, base_walked, base_props)
    finally:
        tagger.restore()

    nodes = [el for el, _ in base_walked]
    for (idx, name), changed in sorted(changes.items()):
        initial = base_props[idx][name]
        values = [changed.get(i, initial) for i in range(n_frames)]
        try:
            animation = _animation(name, values, times, duration, interpolate)
        except ValueError as err:
            raise ValueError(
                f"{err} (<{_tag(nodes[idx])}> in {base_walked[idx][1]!r})"
            ) from None
        nodes[idx].append(animation)

    elements = {
        gid: art.element(n_frames, times, duration, interpolate)
        for gid, art in tracked.items()
    }
    _put_back(nodes, orders, elements)

    svg = ET.tostring(base, encoding="unicode")
    if path is not None:
        Path(path).write_text(svg, encoding="utf-8")
    return SvgAnimation(svg)
