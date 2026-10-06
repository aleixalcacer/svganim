"""Rendering a figure to an SVG tree and walking through it."""

from __future__ import annotations

import io
import re
from collections.abc import Iterator
from xml.etree import ElementTree as ET

import matplotlib as mpl
from matplotlib.figure import Figure

SVG = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG)
ET.register_namespace("xlink", XLINK)

_DEFS = f"{{{SVG}}}defs"
_IMAGE = f"{{{SVG}}}image"
_METADATA = f"{{{SVG}}}metadata"

# Attributes whose numbers are rounded to `precision` decimals.
_NUMERIC = {"d", "transform", "x", "y", "width", "height", "points"}
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:e[-+]?\d+)?", re.IGNORECASE)


def _render(fig: Figure, precision: int, simplify: bool) -> ET.Element:
    """Render ``fig`` to a normalized SVG tree (deterministic, vector only)."""
    # A fixed hash salt makes generated ids (clip paths, markers) deterministic.
    # Simplification changes the vertex count from frame to frame, which would
    # make paths impossible to interpolate, so it is off when interpolating.
    rc = {"svg.hashsalt": "svganim", "svg.fonttype": "path", "path.simplify": simplify}
    with mpl.rc_context(rc):
        buf = io.BytesIO()
        fig.savefig(buf, format="svg", metadata={"Date": None})
    root = ET.fromstring(buf.getvalue())
    if next(root.iter(_IMAGE), None) is not None:
        raise ValueError(
            "the figure contains raster images (imshow, rasterized artists, ...); "
            "svganim only produces vector output. Use pcolormesh instead of imshow "
            "and remove rasterized=True"
        )
    for child in root.findall(_METADATA):
        root.remove(child)
    for el in root.iter():
        for key in _NUMERIC & el.attrib.keys():
            el.set(key, _round(el.get(key, ""), precision))
    return root


def _round(value: str, precision: int) -> str:
    def repl(m: re.Match[str]) -> str:
        text = f"{float(m.group()):.{precision}f}".rstrip("0").rstrip(".")
        return "0" if text in ("", "-0") else text

    return _NUMBER.sub(repl, value)


def _tag(el: ET.Element) -> str:
    return el.tag.rpartition("}")[2]


def _walk(el: ET.Element, label: str = "") -> Iterator[tuple[ET.Element, str]]:
    """Yield ``(element, label)`` for ``el`` and its descendants, skipping defs.

    The label is the id of the closest element that has one (matplotlib names
    its artists, e.g. ``line2d_3``), used to say where something went wrong.
    """
    if el.tag == _DEFS:
        return
    label = el.get("id", label)
    yield el, label
    for child in el:
        yield from _walk(child, label)


class _Defs:
    """Collects definitions that only appear in later frames into the base."""

    def __init__(self, base: ET.Element) -> None:
        target = base.find(_DEFS)
        if target is None:
            target = ET.Element(_DEFS)
            base.insert(0, target)
        self.target = target
        self.known = {el.get("id") for el in base.iter() if el.get("id")}

    def merge(self, root: ET.Element) -> None:
        for defs in root.iter(_DEFS):
            for child in defs:
                ident = child.get("id")
                if ident and ident not in self.known:
                    self.known.add(ident)
                    self.target.append(child)


# Chromium drops a whole SMIL animation that goes through ``none``, in the frames that
# have it and in those that do not. The same picture is written with a value it does
# animate: a fully transparent paint, and a dash array of zero, which SVG treats as
# none.
_ANIMATABLE_NONE = {
    "fill": "transparent",
    "stroke": "transparent",
    "stroke-dasharray": "0",
}


def _props(el: ET.Element) -> dict[str, str]:
    """Attributes and inline-style properties of ``el`` in one flat dict."""
    props = {k: v for k, v in el.attrib.items() if k not in ("id", "style")}
    for decl in el.get("style", "").split(";"):
        key, _, val = decl.partition(":")
        if val:
            props[key.strip()] = val.strip()
    return {
        k: _ANIMATABLE_NONE.get(k, v) if v == "none" else v for k, v in props.items()
    }
