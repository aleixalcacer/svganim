"""Following each artist across the frames, by the gid its element carries.

An artist is the same Python object in every frame, while the place of its element in
the SVG shifts when another artist is added or removed. Matching elements by their
position would break exactly when artists come and go, so each artist gets a gid and
is matched by it.
"""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

from matplotlib.artist import Artist
from matplotlib.figure import Figure

from svganim._diff import _record_changes
from svganim._smil import _animation
from svganim._svg import _DEFS, SVG, _props, _tag, _walk

_SMIL = {f"{{{SVG}}}{name}" for name in ("animate", "animateTransform", "set")}


class _Tagger:
    """Gives every artist of a figure a gid, so that its element can be told apart.

    matplotlib numbers the elements it writes (``line2d_3``, ``text_5``) in drawing
    order, so the number of an artist changes when another one is added or removed.
    The Python object is the same in every frame, and its gid is what the SVG carries.
    The gids are taken off again when the animation is done.
    """

    def __init__(self) -> None:
        self.tagged: list[Artist] = []

    def tag(self, fig: Figure) -> None:
        for holder in (fig, *fig.axes):
            for kind in ("lines", "collections", "patches", "texts", "artists"):
                for artist in getattr(holder, kind, ()):
                    if artist.get_gid() is None:
                        name = type(artist).__name__.lower()
                        artist.set_gid(f"svganim-{name}-{len(self.tagged)}")
                        self.tagged.append(artist)

    def restore(self) -> None:
        for artist in self.tagged:
            artist.set_gid(None)


def _is_gid(el: ET.Element) -> bool:
    """Whether the id of ``el`` is a gid, not one of matplotlib's numbered ids."""
    ident = el.get("id")
    return bool(ident) and re.search(r"_\d+$", ident) is None


def _extract(
    root: ET.Element,
) -> tuple[dict[str, tuple[ET.Element, ET.Element]], list[tuple[ET.Element, list]]]:
    """Cut the elements that carry a gid out of ``root``.

    Returns ``{gid: (element, parent)}`` and, for every parent, the order of its
    children as keys: a gid, or ``("s", j)`` for its j-th ordinary child.
    """
    found: dict[str, tuple[ET.Element, ET.Element]] = {}
    orders: list[tuple[ET.Element, list]] = []

    def visit(el: ET.Element) -> None:
        keys: list = []
        for child in list(el):
            if child.tag == _DEFS:
                continue
            if _is_gid(child):
                gid = child.get("id", "")
                if gid in found:
                    raise ValueError(f"the gid {gid!r} belongs to more than one artist")
                found[gid] = (child, el)
                keys.append(gid)
                el.remove(child)
            else:
                keys.append(("s", len([k for k in keys if isinstance(k, tuple)])))
                visit(child)
        orders.append((el, keys))

    visit(root)
    return found, orders


def _merge(order: list, keys: list) -> None:
    """Add to ``order`` the keys it lacks, each right after the key before it."""
    for n, key in enumerate(keys):
        if key not in order:
            order.insert(order.index(keys[n - 1]) + 1 if n else 0, key)


class _Tracked:
    """An artist met under the same gid in every frame in which it is drawn."""

    def __init__(self, frame: int, el: ET.Element, parent: int) -> None:
        self.el, self.parent, self.frames = el, parent, {frame}
        self.walked = list(_walk(el))
        self.props = [_props(node) for node, _ in self.walked]
        self.changes: dict[tuple[int, str], dict[int, str]] = {}

    def see(self, frame: int, el: ET.Element, parent: int) -> None:
        if parent != self.parent:
            gid = self.el.get("id")
            raise ValueError(f"{gid!r} moves to another container in frame {frame}")
        self.frames.add(frame)
        _record_changes(self.changes, frame, list(_walk(el)), self.walked, self.props)

    def element(
        self, n_frames: int, times: list[float], duration: float, interpolate: bool
    ) -> ET.Element:
        """The element with its animations and the frames in which it is shown."""
        for (idx, name), changed in sorted(self.changes.items()):
            initial = last = self.props[idx][name]
            values = []
            for i in range(n_frames):
                # While the artist is not drawn it keeps its last value, so it does
                # not glide towards a made-up one in the frame before it disappears.
                if i in self.frames:
                    last = changed.get(i, initial)
                values.append(last)
            try:
                animation = _animation(name, values, times, duration, interpolate)
            except ValueError as err:
                node, label = self.walked[idx]
                raise ValueError(f"{err} (<{_tag(node)}> in {label!r})") from None
            self.walked[idx][0].append(animation)
        shown = ["visible" if i in self.frames else "hidden" for i in range(n_frames)]
        if len(set(shown)) > 1:
            self.el.set("visibility", shown[0])
            self.el.append(_animation("visibility", shown, times, duration, False))
        return self.el


def _put_back(
    nodes: list[ET.Element],
    orders: dict[int, list],
    elements: dict[str, ET.Element],
) -> None:
    """Return the cut elements to their parents, in the order of the frames."""
    for index, order in orders.items():
        if all(isinstance(key, tuple) for key in order):
            continue  # nothing was cut out of this parent
        parent = nodes[index]
        defs = [c for c in parent if c.tag == _DEFS]
        smil = [c for c in parent if c.tag in _SMIL]
        rest = [c for c in parent if c.tag != _DEFS and c.tag not in _SMIL]
        parent[:] = (
            defs
            + [rest[k[1]] if isinstance(k, tuple) else elements[k] for k in order]
            + smil
        )
