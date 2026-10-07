"""Rendering a figure to an SVG tree and walking through it."""

from __future__ import annotations

import io
import re
from typing import Any
from xml.etree import ElementTree as ET

import matplotlib as mpl
from matplotlib.figure import Figure

SVG = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG)
ET.register_namespace("xlink", XLINK)

_DEFS = f"{{{SVG}}}defs"
_METADATA = f"{{{SVG}}}metadata"

# Attributes whose numbers are rounded to `precision` decimals.
_NUMERIC = {"d", "transform", "x", "y", "width", "height", "points"}
_FUNCTION = re.compile(r"\w+\([^)]*\)")
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:e[-+]?\d+)?", re.IGNORECASE)


def _render(
    fig: Figure, precision: int, simplify: bool, **savefig_kwargs: Any
) -> ET.Element:
    """Render ``fig`` to a normalized SVG tree (deterministic, vector only)."""
    # A fixed hash salt makes generated ids (clip paths, markers) deterministic.
    # Simplification changes the vertex count from frame to frame, which would
    # make paths impossible to interpolate, so it is off when interpolating.
    with mpl.rc_context(
        {"svg.hashsalt": "svganim", "svg.fonttype": "path", "path.simplify": simplify}
    ):
        buf = io.BytesIO()
        savefig_kwargs.update(format="svg", metadata={"Date": None})
        fig.savefig(buf, **savefig_kwargs)
    root = ET.fromstring(buf.getvalue())
    for child in root.findall(_METADATA):
        root.remove(child)
    for el in list(root.iter()):
        _split_transform(el)
    for el in root.iter():
        for key in _NUMERIC & el.attrib.keys():
            el.set(key, _round(el.get(key, ""), precision))
    return root


def _split_transform(el: ET.Element) -> None:
    """Leave a single transform function on ``el`` and nest the rest inside it.

    SMIL animates one transform function at a time, and matplotlib writes the place
    of a text as ``translate(...) scale(...)``. ``A B`` on a group is the same as
    ``A`` on it and ``B`` on a group around its children.
    """
    functions = _FUNCTION.findall(el.get("transform", ""))
    if len(functions) > 1 and len(el):
        inner = ET.Element(f"{{{SVG}}}g", {"transform": " ".join(functions[1:])})
        inner.extend(el)
        el[:] = [inner]
        el.set("transform", functions[0])
        _split_transform(inner)


def _round(value: str, precision: int) -> str:
    def repl(m: re.Match[str]) -> str:
        text = f"{float(m.group()):.{precision}f}".rstrip("0").rstrip(".")
        return "0" if text in ("", "-0") else text

    return _NUMBER.sub(repl, value)


def _tag(el: ET.Element) -> str:
    return el.tag.rpartition("}")[2]


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
