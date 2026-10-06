"""Comparing the elements of a frame with those of the base document."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from svganim._svg import _props, _tag

# matplotlib leaves a property out of the SVG when it has the value the document would
# give it anyway, so a frame without one of these has that value, which is what the
# animation needs. They are SVG's initial values, except for the two that matplotlib's
# own style sheet sets: ``*{stroke-linejoin: round; stroke-linecap: butt}``.
_DEFAULTS = {
    "opacity": "1",
    "fill-opacity": "1",
    "stroke-opacity": "1",
    "stroke-width": "1",
    "stroke-dasharray": "0",
    "stroke-dashoffset": "0",
    "stroke-linecap": "butt",
    "stroke-linejoin": "round",
    "fill": "#000000",
    "stroke": "transparent",
}


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
        props, base = _props(el), base_props[idx]
        if props == base:
            continue
        if props.keys() != base.keys():
            missing = props.keys() ^ base.keys()
            if unknown := missing - _DEFAULTS.keys():
                raise ValueError(
                    f"attribute {min(unknown)!r} of <{_tag(el)}> in {label!r} "
                    f"is missing in some frames"
                )
            for name in missing:  # whichever side lacks it has its default
                (base if name in props else props)[name] = _DEFAULTS[name]
        for name, value in props.items():
            if value != base[name]:
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
