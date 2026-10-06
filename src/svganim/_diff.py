"""Comparing the elements of a frame with those of the base document."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from svganim._svg import _props, _tag


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
