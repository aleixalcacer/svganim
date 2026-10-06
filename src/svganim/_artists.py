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

from svganim._svg import _DEFS, SVG

_SMIL = {f"{{{SVG}}}{name}" for name in ("animate", "animateTransform", "set")}

# How a child is told apart in the order of its parent: by its gid, or as the j-th of
# the ordinary children, which are always in the same place.
_Key = str | tuple[str, int]


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
    ident = el.get("id", "")
    return bool(ident) and re.search(r"_\d+$", ident) is None


def _extract(
    root: ET.Element,
) -> tuple[
    dict[str, tuple[ET.Element, ET.Element]], list[tuple[ET.Element, list[_Key]]]
]:
    """Cut the elements that carry a gid out of ``root``.

    Returns ``{gid: (element, its parent)}`` and, for every parent, the order of its
    children as keys: a gid, or ``("s", j)`` for its j-th ordinary child.
    """
    found: dict[str, tuple[ET.Element, ET.Element]] = {}
    orders: list[tuple[ET.Element, list[_Key]]] = []

    def visit(el: ET.Element) -> None:
        keys: list[_Key] = []
        orders.append((el, keys))
        ordinary = 0
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
                keys.append(("s", ordinary))
                ordinary += 1
                visit(child)

    visit(root)
    return found, orders


def _merge(order: list[_Key], keys: list[_Key]) -> None:
    """Add to ``order`` the keys it lacks, each right after the key before it."""
    for n, key in enumerate(keys):
        if key not in order:
            order.insert(order.index(keys[n - 1]) + 1 if n else 0, key)


def _put_back(
    orders: dict[ET.Element, list[_Key]], elements: dict[str, ET.Element]
) -> None:
    """Return the cut elements to their parents, in the order of the frames."""
    for parent, order in orders.items():
        if all(isinstance(key, tuple) for key in order):
            continue  # nothing was cut out of this parent
        defs = [c for c in parent if c.tag == _DEFS]
        smil = [c for c in parent if c.tag in _SMIL]
        rest = [c for c in parent if c.tag != _DEFS and c.tag not in _SMIL]
        parent[:] = (
            defs
            + [rest[k[1]] if isinstance(k, tuple) else elements[k] for k in order]
            + smil
        )
