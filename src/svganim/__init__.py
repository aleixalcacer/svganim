"""Turn a matplotlib figure and an update function into one animated SVG."""

from importlib.metadata import version

from svganim._core import SvgAnimation, anim_to_svg

__version__ = version("svganim")

__all__ = ["SvgAnimation", "anim_to_svg"]
