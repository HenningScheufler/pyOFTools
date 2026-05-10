# Configuration file for the Sphinx documentation builder.
import locale
import os

# OpenFOAM's dictionary parser uses strtod, which fails on locales that use
# ',' as the decimal separator (de_DE, etc.): ``version 2.0`` becomes
# unparseable. Force the C locale before any OpenFOAM call.
locale.setlocale(locale.LC_NUMERIC, "C")

# OpenFOAM enables SIGFPE trapping by default; matplotlib and numpy probes
# hit it during gallery execution. Disable before the first OpenFOAM init.
os.environ.setdefault("FOAM_SIGFPE", "false")

project = "pyOFTools"
copyright = "2025-2026, Henning Scheufler"
author = "Henning Scheufler"
release = "0.3.0"

# -- General configuration ---------------------------------------------------

# Gallery scripts execute at build time by default (so rendered pages show
# real output and matplotlib figures). Set PYOFTOOLS_DOCS_DRY=1 to skip
# execution and mock the C++-backed packages — useful for a doc-only CI
# path where OpenFOAM isn't sourced.
_DRY = os.environ.get("PYOFTOOLS_DOCS_DRY") == "1"
if _DRY:
    autodoc_mock_imports = ["pybFoam", "pyOFTools.aggregation"]

extensions = [
    "sphinx.ext.autodoc",
    "sphinxcontrib.mermaid",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "sphinx_sitemap",
    "sphinx_gallery.gen_gallery",
]

autosectionlabel_prefix_document = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- sphinx-gallery ----------------------------------------------------------

sphinx_gallery_conf = {
    "examples_dirs": ["../examples/tutorials", "../examples/how-to"],
    "gallery_dirs": ["auto_tutorials", "auto_how_to"],
    "filename_pattern": r"/example_",
    # Only build pages for example_*.py files; baseline cases, helpers and
    # Allrun scripts live alongside them and must be ignored.
    "ignore_pattern": r"^(?!example_).*\.py$",
    "remove_config_comments": True,
    "download_all_examples": False,
    # Execute every example and capture its output in the rendered page.
    # Set PYOFTOOLS_DOCS_DRY=1 to render source without executing.
    "plot_gallery": "False" if _DRY else "True",
}

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
}

html_static_path = ["_static"]
html_baseurl = "https://henning.github.io/pyOFTools/"


# Sphinx-gallery auto-generates `auto_tutorials/index.rst` and
# `auto_how_to/index.rst`. We list each tutorial / how-to individually
# in `index.rst` instead of going through these gallery indices, but
# the indices still exist on disk. Marking them `:orphan:` keeps them
# reachable by URL while excluding them from the sidebar — otherwise
# furo renders both the gallery index *and* the per-page entries,
# which produces an expandable parent group on child pages.
_GALLERY_INDEX_DOCS = {"auto_tutorials/index", "auto_how_to/index"}


def _orphan_gallery_indices(app, docname, source):
    if docname in _GALLERY_INDEX_DOCS and not source[0].lstrip().startswith(":orphan:"):
        source[0] = ":orphan:\n\n" + source[0]


def setup(app):
    app.connect("source-read", _orphan_gallery_indices)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
