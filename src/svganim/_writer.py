"""A matplotlib movie writer, so that ``Animation.save`` can write an animated SVG."""

from __future__ import annotations

import contextlib
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import matplotlib as mpl
from matplotlib.animation import AbstractMovieWriter, Animation, writers
from matplotlib.figure import Figure

from svganim._core import SvgAnimation, _Recorder


@writers.register("svganim")
class SvgAnimWriter(AbstractMovieWriter):
    """Write a matplotlib animation as an animated SVG with ``Animation.save``.

    Importing :mod:`svganim` registers it under the name ``"svganim"``, so an
    existing :class:`~matplotlib.animation.FuncAnimation` or
    :class:`~matplotlib.animation.ArtistAnimation` is saved without changing it::

        ani.save("wave.svg", writer="svganim", fps=20)

    The first frame becomes the base document; every attribute that differs in later
    frames gets a SMIL animation, so static parts cost nothing. The animation loops.

    Parameters
    ----------
    fps : float, default 5
        Frames per second. Pass it here when giving ``save`` an instance, which
        refuses an ``fps`` of its own; with ``writer="svganim"``, ``save(fps=...)``
        sets it, and without one matplotlib takes it from the animation's interval.
    metadata, codec, bitrate
        Accepted for compatibility with ``Animation.save`` and ignored.
    hold : float, default 0
        Seconds to hold the last frame before the animation loops. With 0 it lasts
        ``n_frames / fps``, as in every matplotlib writer.
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

    Raises
    ------
    ValueError
        When saving, if the animation has no frames, if an argument is out of
        range, if an element is of another kind than it was in the first frame that
        has it (the message names the element), if two artists share a gid, or if a
        transform cannot be animated.

    Notes
    -----
    An artist that is not drawn in every frame is shown only in the frames where
    matplotlib draws it, and so are the elements that an artist has in some frames
    and not in others at its end: the letters of a text that changes length, the
    points of a scatter plot, the ticks of an axis.

    To follow each artist from frame to frame, svganim gives it a gid while it
    works and takes it off at the end; a gid that you set yourself is kept, and two
    artists cannot share one.

    matplotlib itself ignores ``bbox_inches="tight"`` when saving an animation, since
    the crop would change from frame to frame.
    """

    def __init__(
        self,
        fps: float = 5,
        metadata: dict[str, str] | None = None,
        codec: str | None = None,
        bitrate: int | None = None,
        *,
        hold: float = 0.0,
        precision: int = 3,
        interpolate: bool = False,
    ) -> None:
        self.fps = fps  # type: ignore[assignment]  # matplotlib types it as int
        self.hold = hold
        self.precision = precision
        self.interpolate = interpolate
        self._recorder: _Recorder | None = None
        self._failed = False

    @classmethod
    def isAvailable(cls) -> bool:
        return True

    def setup(self, fig: Figure, outfile: str | Path, dpi: float | None = None) -> None:
        super().setup(fig, outfile, dpi)
        self._recorder = _Recorder(self.precision, self.interpolate)
        self._failed = False

    @contextlib.contextmanager
    def saving(
        self,
        fig: Figure,
        outfile: str | Path,
        dpi: float | None,
        *args: Any,
        **kwargs: Any,
    ) -> Iterator[SvgAnimWriter]:
        # matplotlib calls ``finish`` also when the animation raised: remember it, so
        # that no half-made file is written.
        # matplotlib draws the figure after each update, before it calls the writer,
        # and a path remembers whether it was simplified when it was drawn first.
        # So the setting has to hold for the whole animation, not only in ``_render``.
        with (
            super().saving(fig, outfile, dpi, *args, **kwargs),
            mpl.rc_context({"path.simplify": not self.interpolate}),
        ):
            try:
                yield self
            except BaseException:
                self._failed = True
                raise

    def grab_frame(self, **savefig_kwargs: Any) -> None:
        assert self._recorder is not None, "setup() has not been called"
        savefig_kwargs.setdefault("dpi", self.dpi)
        self._recorder.grab(self.fig, **savefig_kwargs)

    def finish(self) -> None:
        recorder, self._recorder = self._recorder, None
        if recorder is None:
            return
        try:
            if not self._failed:
                svg = recorder.compose(self.fps, self.hold)
                Path(self.outfile).write_text(svg, encoding="utf-8")
        finally:
            recorder.restore()


def ani_to_svg(
    ani: Animation,
    fps: float = 5,
    hold: float = 0.0,
    *,
    precision: int = 3,
    interpolate: bool = False,
) -> SvgAnimation:
    """Render a matplotlib animation as a looping SVG and return it as a string.

    It is ``ani.save`` with :class:`SvgAnimWriter`, but it returns the result as a
    :class:`SvgAnimation`, which Jupyter and Quarto display as an animated image, so
    it can end a cell. The arguments are those of :class:`SvgAnimWriter`. Unlike
    ``save``, ``fps`` does not default to the animation's interval. To write a file,
    use ``ani.save``.

    ``ani`` changes its figure as it goes, so when the call returns the figure is
    left as the last frame set it.

    Examples
    --------
    >>> ani_to_svg(ani, fps=20)  # doctest: +SKIP
    """
    writer = SvgAnimWriter(fps, hold=hold, precision=precision, interpolate=interpolate)
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "animation.svg"
        ani.save(file, writer=writer)
        svg = SvgAnimation(file.read_text(encoding="utf-8"))
    return svg
