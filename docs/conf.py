# Configuration file for the Sphinx documentation builder.

project = "pyOFTools"
copyright = "2025-2026, Henning Scheufler"
author = "Henning Scheufler"
release = "0.2.0"

# -- General configuration ---------------------------------------------------


# Mock pybFoam to prevent OpenFOAM initialization during doc build.
# API reference (autodoc) will be empty — build with OpenFOAM sourced for full API docs.
autodoc_mock_imports = ["pybFoam", "pyOFTools.aggregation"]

extensions = [
    "sphinx.ext.autodoc",
    "sphinxcontrib.mermaid",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "sphinx_sitemap",
]

autosectionlabel_prefix_document = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
}

html_static_path = ["_static"]
html_baseurl = "https://henning.github.io/pyOFTools/"
