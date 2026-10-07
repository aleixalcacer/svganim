from __future__ import annotations

import base64
from typing import Any
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


class _Recorder:
    """Collects the rendered frames of a figure and turns them into one SVG.

    The matplotlib writer calls :meth:`grab` once per frame,
    in order, then :meth:`compose`, and :meth:`restore` whatever happens.
    """

    def __init__(self, precision: int, interpolate: bool) -> None:
        self.precision = precision
        self.interpolate = interpolate
        self.n_frames = 0
        # The document and each artist are followed separately, because artists can
        # come and go: the document is what is left once they are cut out of a frame.
        self.tagger = _Tagger()
        self.document = _Tracked()
        self.artists: dict[str, _Tracked] = {}
        self.orders: dict[ET.Element, list[_Key]] = {}
        self.defs: _Defs | None = None

    def grab(self, fig: Figure, **savefig_kwargs: Any) -> None:
        """Render ``fig`` as the next frame."""
        i = self.n_frames
        self.tagger.tag(fig)
        root = _render(fig, self.precision, not self.interpolate, **savefig_kwargs)
        # Definitions first: an artist can carry its own (a marker, for one), and
        # they leave with it when it is cut out.
        if self.defs is None:
            self.defs = _Defs(root)
        else:
            self.defs.merge(root)
        found, parents = _extract(root)
        stands_for = self.document.see(i, root, None)
        for gid, (el, parent) in found.items():
            self.artists.setdefault(gid, _Tracked()).see(i, el, stands_for[id(parent)])
        for parent, keys in parents:
            _merge(self.orders.setdefault(stands_for[id(parent)], []), keys)
        self.n_frames += 1

    def restore(self) -> None:
        """Take off the gids that were set."""
        self.tagger.restore()

    def compose(self, fps: float, hold: float) -> str:
        """The animated SVG of the frames grabbed so far."""
        n = self.n_frames
        if n < 1:
            raise ValueError("there are no frames to animate")
        if fps <= 0 or hold < 0:
            raise ValueError("fps must be positive and hold non-negative")
        duration = n / fps + hold
        times = [i / fps / duration for i in range(n)]
        args = (n, times, duration, self.interpolate)
        base = self.document.element(*args)
        _put_back(
            self.orders, {gid: art.element(*args) for gid, art in self.artists.items()}
        )
        return ET.tostring(base, encoding="unicode")
