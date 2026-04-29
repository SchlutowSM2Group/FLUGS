"""Sphinx configuration for FLUGS."""

import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------

project = "FLUGS"
copyright = "2026, Mark Schlutow, Ray Chew, Mathias Göckede"
author = "Mark Schlutow, Ray Chew, Mathias Göckede"

version = "1.0"
release = "1.0.0"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
language = "en"
exclude_patterns = []
pygments_style = "sphinx"

napoleon_numpy_docstring = True
napoleon_google_docstring = False

autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

# Mock BLDFM if not installed (allows the Sphinx site to build without
# actually installing BLDFM in the documentation environment).
autodoc_mock_imports = ["bldfm"]

html_theme = "furo"
html_title = "FLUGS"
html_logo = "_static/logo.png"
html_theme_options = {"sidebar_hide_name": True}
html_static_path = ["_static"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}
