"""Following an element over the frames and animating what changes in it."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from svganim._smil import _animation
from svganim._svg import _props, _tag, _walk

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


class _Tracked:
    """An element followed over the frames in which it is drawn.

    The first frame it appears in is the reference. Later ones are compared with it,
    element by element, and each property that differs is kept with its value in that
    frame, so a frame is not kept once it has been compared.
    """

    def __init__(self, frame: int, el: ET.Element, parent: int) -> None:
        self.el, self.parent, self.frames = el, parent, {frame}
        self.walked = list(_walk(el))
        self.props = [_props(node) for node, _ in self.walked]
        self.changes: dict[tuple[int, str], dict[int, str]] = {}

    def see(self, frame: int, el: ET.Element, parent: int) -> None:
        """Compare ``el``, the same element in ``frame``, with the reference."""
        if parent != self.parent:
            raise ValueError(f"{self.el.get('id')!r} moves to another container")
        self.frames.add(frame)
        walked = list(_walk(el))
        if len(walked) != len(self.walked) or any(
            node.tag != ref.tag
            for (node, _), (ref, _) in zip(walked, self.walked, strict=False)
        ):
            raise _structure_error(frame, walked, self.walked)
        for idx, (node, _) in enumerate(walked):
            props, base = _props(node), self.props[idx]
            if props == base:
                continue
            if props.keys() != base.keys():
                missing = props.keys() ^ base.keys()
                if unknown := missing - _DEFAULTS.keys():
                    label = self.walked[idx][1]
                    raise ValueError(
                        f"attribute {min(unknown)!r} of <{_tag(node)}> in {label!r} "
                        f"is missing in some frames"
                    )
                for name in missing:  # whichever side lacks it has its default
                    (base if name in props else props)[name] = _DEFAULTS[name]
            for name, value in props.items():
                if value != base[name]:
                    self.changes.setdefault((idx, name), {})[frame] = value

    def element(
        self, n_frames: int, times: list[float], duration: float, interpolate: bool
    ) -> ET.Element:
        """The element with its animations and, if need be, when it is shown."""
        for (idx, name), changed in sorted(self.changes.items()):
            initial = last = self.props[idx][name]
            values = []
            for i in range(n_frames):
                # Out of the frames it is drawn in, an element keeps its last value, so
                # it does not glide towards a made-up one just before it disappears.
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
