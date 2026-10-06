from __future__ import annotations

import base64
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

# Attributes whose numbers are rounded to `precision` decimals.
_NUMERIC = {"d", "transform", "x", "y", "width", "height", "points"}
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:e[-+]?\d+)?", re.IGNORECASE)
_TRANSFORM = re.compile(r"^(translate|scale|rotate|skewX|skewY)\(([^)]*)\)$")
_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

# Attributes whose values SMIL can interpolate numerically.
_INTERPOLABLE = {
    "d", "points", "transform", "x", "y", "x1", "y1", "x2", "y2",
    "cx", "cy", "r", "rx", "ry", "width", "height", "stroke-width",
    "opacity", "fill-opacity", "stroke-opacity",
}  # fmt: skip
_COLOR = {"fill", "stroke"}


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
        (``imshow``, ``rasterized=True``), if the number or order of SVG elements
        changes between frames (the message names the element), or if a
        transform cannot be animated.

    Examples
    --------
    >>> anim_to_svg(fig, update, n_frames=60, fps=20, path="wave.svg")  # doctest: +SKIP
    """
    if n_frames < 1:
        raise ValueError("n_frames must be at least 1")
    if fps <= 0 or hold < 0:
        raise ValueError("fps must be positive and hold non-negative")

    update(0)
    simplify = not interpolate
    base = _render(fig, precision, simplify)
    walked = list(_walk(base))
    nodes = [el for el, _ in walked]
    base_props = [_props(el) for el in nodes]
    defs = _Defs(base)

    # Each later frame is compared against the base and then discarded, so only
    # the values that change are kept: {(element index, attribute): {frame: value}}.
    changes: dict[tuple[int, str], dict[int, str]] = {}
    for i in range(1, n_frames):
        update(i)
        root = _render(fig, precision, simplify)
        defs.merge(root)
        _record_changes(changes, i, list(_walk(root)), walked, base_props)

    duration = n_frames / fps + hold
    times = [i / fps / duration for i in range(n_frames)]
    for (idx, name), changed in sorted(changes.items()):
        initial = base_props[idx][name]
        values = [changed.get(i, initial) for i in range(n_frames)]
        try:
            animation = _animation(name, values, times, duration, interpolate)
        except ValueError as err:
            raise ValueError(
                f"{err} (<{_tag(nodes[idx])}> in {walked[idx][1]!r})"
            ) from None
        nodes[idx].append(animation)

    svg = ET.tostring(base, encoding="unicode")
    if path is not None:
        Path(path).write_text(svg, encoding="utf-8")
    return SvgAnimation(svg)


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


def _props(el: ET.Element) -> dict[str, str]:
    """Attributes and inline-style properties of ``el`` in one flat dict."""
    props = {k: v for k, v in el.attrib.items() if k not in ("id", "style")}
    for decl in el.get("style", "").split(";"):
        key, _, val = decl.partition(":")
        if val:
            props[key.strip()] = val.strip()
    return props


def _record_changes(
    changes: dict[tuple[int, str], dict[int, str]],
    frame: int,
    walked: list[tuple[ET.Element, str]],
    base_walked: list[tuple[ET.Element, str]],
    base_props: list[dict[str, str]],
) -> None:
    """Store, for frame ``frame``, every value that differs from the base."""
    if len(walked) != len(base_walked) or any(
        el.tag != ref.tag
        for (el, _), (ref, _) in zip(walked, base_walked, strict=False)
    ):
        raise _structure_error(frame, walked, base_walked)
    for idx, ((el, label), _) in enumerate(zip(walked, base_walked, strict=True)):
        props = _props(el)
        if props == base_props[idx]:
            continue
        if props.keys() != base_props[idx].keys():
            name = min(props.keys() ^ base_props[idx].keys())
            raise ValueError(
                f"attribute {name!r} of <{_tag(el)}> in {label!r} "
                f"is missing in some frames"
            )
        for name, value in props.items():
            if value != base_props[idx][name]:
                changes.setdefault((idx, name), {})[frame] = value


def _structure_error(
    frame: int,
    walked: list[tuple[ET.Element, str]],
    base_walked: list[tuple[ET.Element, str]],
) -> ValueError:
    """Build an error that points at the first element that differs."""
    head = f"the SVG element structure changes between frames (frame {frame})"
    for (el, label), (ref, ref_label) in zip(walked, base_walked, strict=False):
        if el.tag != ref.tag or el.get("id") != ref.get("id"):
            return ValueError(
                f"{head}: found <{_tag(el)}> in {label!r} "
                f"where the base has <{_tag(ref)}> in {ref_label!r}"
            )
    shorter = min(len(walked), len(base_walked))
    if len(walked) > len(base_walked):
        el, label = walked[shorter]
        return ValueError(f"{head}: extra <{_tag(el)}> in {label!r} not in the base")
    ref, label = base_walked[shorter]
    return ValueError(f"{head}: <{_tag(ref)}> in {label!r} is missing")


def _animation(
    name: str,
    values: list[str],
    times: list[float],
    duration: float,
    interpolate: bool = False,
) -> ET.Element:
    """Build the SMIL animation of attribute ``name`` over all frames."""
    tag, shown, kind = "animate", values, None
    if name == "transform":
        # <animate> cannot target transform; <animateTransform> needs a type.
        tag = "animateTransform"
        kind, shown = _transform_values(values)

    last = len(shown) - 1
    if interpolate and _can_interpolate(name, shown):
        # Drop the middle of every run of equal values: interpolating across it
        # changes nothing, so the animation is unchanged and the file smaller.
        keep = [
            i
            for i in range(len(shown))
            if i in (0, last) or not shown[i - 1] == shown[i] == shown[i + 1]
        ]
        mode = "linear"
    else:
        # Switch between the frames where the value changes.
        keep = [i for i, v in enumerate(shown) if i == 0 or v != shown[i - 1]]
        mode = "discrete"
    key_times = [times[i] for i in keep]
    out = [shown[i] for i in keep]
    if mode == "linear":
        # Linear keyTimes must end at 1: repeat the last value to hold it.
        key_times.append(1.0)
        out.append(out[-1])
    attrs = {
        # ElementTree spells namespaced attributes {uri}name; SMIL wants prefix:name.
        "attributeName": name.replace(f"{{{XLINK}}}", "xlink:"),
        "values": ";".join(out),
        "keyTimes": ";".join(f"{t:.6g}" for t in key_times),
        "calcMode": mode,
        "dur": f"{duration:.6g}s",
        "repeatCount": "indefinite",
    }
    if kind is not None:
        attrs["type"] = kind
    return ET.Element(f"{{{SVG}}}{tag}", attrs)


def _transform_values(values: list[str]) -> tuple[str, list[str]]:
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
    return kinds.pop(), args


def _can_interpolate(name: str, values: list[str]) -> bool:
    """Whether SMIL can interpolate ``values`` of attribute ``name``.

    The attribute must be numeric (not a url or ``none``) and every value must
    have the same text around its numbers, which is not the case for paths with
    a different number of vertices.
    """
    if name in _COLOR:
        return all(_HEX_COLOR.match(v) for v in values)
    if name not in _INTERPOLABLE:
        return False
    template = _NUMBER.sub("#", values[0])
    if "#" not in template or re.search("[Aa]", template):  # no numbers, or arcs
        return False
    return all(_NUMBER.sub("#", v) == template for v in values)
