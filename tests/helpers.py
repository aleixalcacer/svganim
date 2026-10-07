from matplotlib.animation import FuncAnimation

from svganim import ani_to_svg


def anim_to_svg(fig, update, n_frames, fps=20, hold=1.0, **options):
    """The SVG of ``update(i)`` for ``i`` in ``range(n_frames)``."""
    # FuncAnimation draws a first frame by itself unless it has an init_func; the
    # tests count the calls to ``update``, so it gets an empty one.
    ani = FuncAnimation(fig, update, frames=n_frames, init_func=lambda: ())
    return ani_to_svg(ani, fps, hold, **options)
