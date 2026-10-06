from __future__ import annotations

import io
import re
from collections.abc import Callable, Iterator
from pathlib import Path
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
_STRUCTURE_ERROR = "the SVG element structure changes between frames"

# Attributes whose numbers are rounded to `precision` decimals.
_NUMERIC = {"d", "transform", "x", "y", "width", "height", "points"}
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:e[-+]?\d+)?", re.IGNORECASE)
_TRANSFORM = re.compile(r"^(translate|scale|rotate|skewX|skewY)\(([^)]*)\)$")


def anim_to_svg(
    fig: Figure,
    update: Callable[[int], object],
    n_frames: int,
    fps: float = 20,
    hold: float = 1.0,
    path: str | Path | None = None,
    *,
    precision: int = 3,
) -> str:
    """Render ``fig`` as a looping SVG animation and return it as a string.

    ``update(i)`` is called before frame ``i`` is rendered. Frame 0 becomes the
    base document; every attribute that differs in later frames gets a SMIL
    animation with one value per change, so static parts cost nothing.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to render.
    update : callable
        Called as ``update(i)`` before frame ``i`` is rendered. It should modify
        existing artists (``set_data``, ``set_offsets``, ...) and not create or
        remove any. Its return value is ignored.
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

    Returns
    -------
    str
        The animated SVG document.

    Raises
    ------
    ValueError
        If an argument is out of range, if the figure contains raster images
        (``imshow``, ``rasterized=True``), if the number or order of SVG elements
        changes between frames, or if a transform cannot be animated.

    Examples
    --------
    >>> anim_to_svg(fig, update, n_frames=60, fps=20, path="wave.svg")  # doctest: +SKIP
    """
    if n_frames < 1:
        raise ValueError("n_frames must be at least 1")
    if fps <= 0 or hold < 0:
        raise ValueError("fps must be positive and hold non-negative")

    update(0)
    base = _render(fig, precision)
    nodes = list(_walk(base))
    base_props = [_props(el) for el in nodes]
    defs = _Defs(base)

    # Each later frame is compared against the base and then discarded, so only
    # the values that change are kept: {(element index, attribute): {frame: value}}.
    changes: dict[tuple[int, str], dict[int, str]] = {}
    for i in range(1, n_frames):
        update(i)
        root = _render(fig, precision)
        defs.merge(root)
        _record_changes(changes, i, list(_walk(root)), nodes, base_props)

    duration = n_frames / fps + hold
    times = [i / fps / duration for i in range(n_frames)]
    for (idx, name), changed in sorted(changes.items()):
        initial = base_props[idx][name]
        values = [changed.get(i, initial) for i in range(n_frames)]
        nodes[idx].append(_animation(name, values, times, duration))

    svg = ET.tostring(base, encoding="unicode")
    if path is not None:
        Path(path).write_text(svg, encoding="utf-8")
    return svg


def _record_changes(
    changes: dict[tuple[int, str], dict[int, str]],
    frame: int,
    nodes: list[ET.Element],
    base_nodes: list[ET.Element],
    base_props: list[dict[str, str]],
) -> None:
    """Store, for frame ``frame``, every value that differs from the base."""
    if len(nodes) != len(base_nodes):
        raise ValueError(_STRUCTURE_ERROR)
    for idx, (el, ref) in enumerate(zip(nodes, base_nodes, strict=True)):
        if el.tag != ref.tag:
            raise ValueError(_STRUCTURE_ERROR)
        props = _props(el)
        if props == base_props[idx]:
            continue
        if props.keys() != base_props[idx].keys():
            name = min(props.keys() ^ base_props[idx].keys())
            raise ValueError(f"attribute {name!r} is missing in some frames")
        for name, value in props.items():
            if value != base_props[idx][name]:
                changes.setdefault((idx, name), {})[frame] = value


def _render(fig: Figure, precision: int) -> ET.Element:
    """Render ``fig`` to a normalized SVG tree (deterministic, vector only)."""
    # A fixed hash salt makes generated ids (clip paths, markers) deterministic.
    with mpl.rc_context({"svg.hashsalt": "svganim", "svg.fonttype": "path"}):
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


def _walk(el: ET.Element) -> Iterator[ET.Element]:
    """Yield ``el`` and its descendants, skipping ``<defs>`` subtrees."""
    if el.tag == _DEFS:
        return
    yield el
    for child in el:
        yield from _walk(child)


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


def _props(el: ET.Element) -> dict[str, str]:
    """Attributes and inline-style properties of ``el`` in one flat dict."""
    props = {k: v for k, v in el.attrib.items() if k not in ("id", "style")}
    for decl in el.get("style", "").split(";"):
        key, _, val = decl.partition(":")
        if val:
            props[key.strip()] = val.strip()
    return props


def _animation(
    name: str, values: list[str], times: list[float], duration: float
) -> ET.Element:
    """Build a discrete SMIL animation of attribute ``name`` over all frames."""
    # Keep only the frames where the value changes.
    keep = [i for i, v in enumerate(values) if i == 0 or v != values[i - 1]]
    attrs = {
        # ElementTree spells namespaced attributes {uri}name; SMIL wants prefix:name.
        "attributeName": name.replace(f"{{{XLINK}}}", "xlink:"),
        "values": ";".join(values[i] for i in keep),
        "keyTimes": ";".join(f"{times[i]:.6g}" for i in keep),
        "calcMode": "discrete",
        "dur": f"{duration:.6g}s",
        "repeatCount": "indefinite",
    }
    tag = "animate"
    if name == "transform":
        # <animate> cannot target transform; <animateTransform> needs a type.
        tag = "animateTransform"
        attrs["type"], attrs["values"] = _transform_values([values[i] for i in keep])
    return ET.Element(f"{{{SVG}}}{tag}", attrs)


def _transform_values(values: list[str]) -> tuple[str, str]:
    """Split single-function transforms into their common type and arguments."""
    kinds, args = set(), []
    for value in values:
        m = _TRANSFORM.match(value.strip())
        if m is None:
            raise ValueError(f"cannot animate compound transform {value!r}")
        kinds.add(m.group(1))
        args.append(" ".join(m.group(2).replace(",", " ").split()))
    if len(kinds) != 1:
        raise ValueError("the transform type changes between frames")
    return kinds.pop(), ";".join(args)
