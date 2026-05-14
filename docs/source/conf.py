# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import inspect
import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.abspath("../.."))

project = 'PDG API'
copyright = '2024, Particle Data Group'
author = 'Particle Data Group'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    # "sphinx.ext.viewcode",
    "sphinx.ext.linkcode",
    "sphinx_rtd_theme",
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'
html_show_sourcelink = False
html_title = 'PDG API'
html_static_path = ['_static']
html_js_files = [
    'matomo.js',
]
html_css_files = [
    'pdg_sphinx.css',
]

## The below concatenates the class and __init__ docstrings
## (default is to just include the class's docstring)
autoclass_content = 'both'

## However, explicitly listing __init__ may be clearer
# autodoc_default_options = {
#     'members': True,
#     'special-members': '__init__',
#     'undoc-members': False,
# }

def linkcode_resolve(domain, info):
    if domain != 'py':
        return None
    if not info['module']:
        return None

    module = sys.modules.get(info['module'])
    if module is None:
        return None

    obj = module
    for part in info['fullname'].split('.'):
        try:
            obj = getattr(obj, part)
        except AttributeError:
            return None

    # Unwrap properties to get the underlying function
    if isinstance(obj, property):
        obj = obj.fget

    try:
        obj = inspect.unwrap(obj)
        filename = inspect.getsourcefile(obj)
        source, lineno = inspect.getsourcelines(obj)
    except (TypeError, OSError):
        return None

    if filename is None:
        return None

    # Make path relative to the repo root
    start = Path(__file__).parent.parent.parent
    filename = os.path.relpath(filename, start=start)

    repo = os.getenv('PDGAPI_REPO', 'particledatagroup/api')
    branch = os.getenv('PDGAPI_BRANCH', 'main')
    return f"https://github.com/{repo}/blob/{branch}/{filename}#L{lineno}-L{lineno + len(source) - 1}"
