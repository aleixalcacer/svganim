"""Sphinx configuration.

The API reference is built from the docstrings, and the example animations are
regenerated from ``examples/*.py`` on every build, so the docs follow the code.
"""

import os
import runpy
import shutil
from importlib.metadata import version as _version
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")  # headless builds

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
STATIC = Path(__file__).resolve().parent / "_static"
GENERATED = STATIC / "examples"
ASSETS = ROOT / "assets"

# The logo lives in assets/ (the README uses it too); the theme reads it from _static.
for _logo in ("logo.svg", "logo-text.svg", "logo-text-dark.svg"):
    shutil.copy(ASSETS / _logo, STATIC / _logo)

project = "svganim"
author = "Aleix Alcacer Sales"
release = _version("svganim")

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "myst_parser",
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


def generate_examples(app):
    """Run every example script and publish its SVG under ``_static/examples``."""
    GENERATED.mkdir(parents=True, exist_ok=True)
    cwd = Path.cwd()
    os.chdir(EXAMPLES)  # scripts write their SVG with a relative path
    try:
        for script in sorted(EXAMPLES.glob("*.py")):
            runpy.run_path(str(script), run_name="__main__")
            shutil.copy(script.with_suffix(".svg"), GENERATED / f"{script.stem}.svg")
    finally:
        os.chdir(cwd)


def setup(app):
    app.connect("builder-inited", generate_examples)
