"""Following an element over the frames and animating what changes in it."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from svganim._smil import _animation
from svganim._svg import _DEFS, _props, _tag

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


def _children(el: ET.Element) -> list[ET.Element]:
    return [child for child in el if child.tag != _DEFS]


class _Tracked:
    """An element followed over the frames in which it is drawn.

    The first frame it appears in is the reference. Later ones are compared with it,
    child by child, and each property that differs is kept with its value in that
    frame, so a frame is not kept once it has been compared. A frame can also have
    more children than the reference, or fewer: the ones at the end that only some
    frames have, such as the letters of a text that changes length, are kept with the
    frames in which they are drawn and hidden in the others.
    """

    def __init__(self) -> None:
        self.el: ET.Element | None = None
        self.parent: ET.Element | None = None
        self.up: dict[ET.Element, ET.Element | None] = {}
        self.frames: dict[ET.Element, set[int]] = {}
        self.labels: dict[ET.Element, str] = {}
        self.props: dict[ET.Element, dict[str, str]] = {}
        self.changes: dict[ET.Element, dict[str, dict[int, str]]] = {}

    def see(
        self, frame: int, el: ET.Element, parent: ET.Element | None
    ) -> dict[int, ET.Element]:
        """Compare ``el``, this element in ``frame``, with the reference.

        Returns the reference element that each element of ``el`` stands for, by id.
        """
        stands_for: dict[int, ET.Element] = {}
        if self.el is None:
            self.el, self.parent = el, parent
            self._adopt(el, None, frame, "", stands_for)
        elif parent is not self.parent:
            raise ValueError(f"{self.el.get('id')!r} moves to another container")
        else:
            self._merge(self.el, el, frame, "", stands_for)
        return stands_for

    def _adopt(
        self,
        el: ET.Element,
        up: ET.Element | None,
        frame: int,
        label: str,
        stands_for: dict[int, ET.Element],
    ) -> None:
        label = el.get("id", label)
        self.up[el], self.frames[el], self.labels[el] = up, {frame}, label
        self.props[el] = _props(el)
        stands_for[id(el)] = el
        for child in _children(el):
            self._adopt(child, el, frame, label, stands_for)

    def _merge(
        self,
        ref: ET.Element,
        el: ET.Element,
        frame: int,
        label: str,
        stands_for: dict[int, ET.Element],
    ) -> None:
        label = el.get("id", label)
        if el.tag != ref.tag:
            raise ValueError(
                f"the SVG element structure changes between frames (frame {frame}): "
                f"found <{_tag(el)}> in {label!r} where the base has <{_tag(ref)}>"
            )
        stands_for[id(el)] = ref
        self.frames[ref].add(frame)
        self._compare(ref, _props(el), frame)
        kept = _children(ref)
        for k, child in enumerate(_children(el)):
            if k < len(kept):
                self._merge(kept[k], child, frame, label, stands_for)
            else:  # an element the reference did not have yet
                ref.append(child)
                self._adopt(child, ref, frame, label, stands_for)

    def _compare(self, ref: ET.Element, props: dict[str, str], frame: int) -> None:
        base = self.props[ref]
        if props.keys() != base.keys():
            missing = props.keys() ^ base.keys()
            if unknown := missing - _DEFAULTS.keys():
                raise ValueError(
                    f"attribute {min(unknown)!r} of <{_tag(ref)}> in "
                    f"{self.labels[ref]!r} is missing in some frames"
                )
            for name in missing:  # whichever side lacks it has its default
                (base if name in props else props)[name] = _DEFAULTS[name]
        for name, value in props.items():
            if value != base[name]:
                self.changes.setdefault(ref, {}).setdefault(name, {})[frame] = value

    def element(
        self, n_frames: int, times: list[float], duration: float, interpolate: bool
    ) -> ET.Element:
        """The element with its animations and, where need be, when it is shown."""
        assert self.el is not None
        for node, frames in self.frames.items():
            for name, changed in sorted(self.changes.get(node, {}).items()):
                initial = last = self.props[node][name]
                values = []
                for i in range(n_frames):
                    # Out of the frames it is drawn in, an element keeps its last
                    # value, so it does not glide towards a made-up one just before
                    # it disappears.
                    if i in frames:
                        last = changed.get(i, initial)
                    values.append(last)
                try:
                    animation = _animation(name, values, times, duration, interpolate)
                except ValueError as err:
                    raise ValueError(
                        f"{err} (<{_tag(node)}> in {self.labels[node]!r})"
                    ) from None
                node.append(animation)
            up = self.up[node]
            # Inside a parent that is not drawn, an element is not drawn either.
            if frames != (set(range(n_frames)) if up is None else self.frames[up]):
                shown = [
                    "visible" if i in frames else "hidden" for i in range(n_frames)
                ]
                node.set("visibility", shown[0])
                node.append(_animation("visibility", shown, times, duration, False))
        return self.el
