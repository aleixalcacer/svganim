"""Building the SMIL animation of an attribute over all the frames."""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

from svganim._svg import _NUMBER, SVG, XLINK

_TRANSFORM = re.compile(r"^(translate|scale|rotate|skewX|skewY)\(([^)]*)\)$")
_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

# Attributes whose values SMIL can interpolate numerically.
_INTERPOLABLE = {
    "d", "points", "transform", "x", "y", "x1", "y1", "x2", "y2",
    "cx", "cy", "r", "rx", "ry", "width", "height", "stroke-width",
    "opacity", "fill-opacity", "stroke-opacity",
}  # fmt: skip
_COLOR = {"fill", "stroke"}


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
