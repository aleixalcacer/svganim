"""Turn a matplotlib animation into one animated SVG."""

from importlib.metadata import version

from svganim._core import SvgAnimation
from svganim._writer import SvgAnimWriter, ani_to_svg

__version__ = version("svganim")

__all__ = ["SvgAnimWriter", "SvgAnimation", "ani_to_svg"]
