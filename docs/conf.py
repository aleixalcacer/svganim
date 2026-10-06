"""Sphinx configuration.

The API reference is built from the docstrings, and the examples are notebooks
that are executed on every build, so the docs follow the code.
"""

import os
import shutil
from importlib.metadata import version as _version
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")  # headless builds

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "_static"
ASSETS = ROOT / "assets"

# The logos and the home animation live in assets/ (the README uses them too);
# the theme and the pages read them from _static.
for _asset in ("logo.svg", "logo-text.svg", "logo-text-dark.svg", "sorting.svg"):
    shutil.copy(ASSETS / _asset, STATIC / _asset)

project = "svganim"
author = "Aleix Alcacer Sales"
release = _version("svganim")

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "myst_nb",
    "sphinx_design",
]
autodoc_member_order = "bysource"
autodoc_typehints = "description"
napoleon_numpy_docstring = True
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
}
myst_enable_extensions = ["colon_fence"]
myst_heading_anchors = 3
nb_execution_mode = "force"  # always run the examples against the current code
nb_execution_raise_on_error = True

html_theme = "furo"
html_static_path = ["_static"]
html_theme_options = {
    "light_logo": "logo-text.svg",
    "dark_logo": "logo-text-dark.svg",
    "sidebar_hide_name": True,  # the logo already carries the name
}
html_favicon = "_static/logo.svg"
html_css_files = ["gallery.css"]
exclude_patterns = ["_build"]

