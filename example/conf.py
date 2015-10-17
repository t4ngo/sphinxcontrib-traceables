# -*- coding: utf-8 -*-

import sys
import os

# -------------------------------------------------------------------------
# Configure extensions

extensions = [
    'sphinx.ext.graphviz',
    'sphinxcontrib.traceables',
]

# -------------------------------------------------------------------------
# General configuration

project = u'Traceables example project'
copyright = u'2015, t4ngo'
version = '0.7'                        # The short X.Y version.
release = '0.7'                        # The full version, incl alpha/beta/rc.

templates_path = ['_templates']
source_suffix = '.txt'                 # The suffix of source filenames.
master_doc = 'index'                   # The master toctree document.
today_fmt = '%Y-%m-%d'
exclude_patterns = ['_build']
pygments_style = 'sphinx'
keep_warnings = True                   # Keep warnings in output documents.

# -------------------------------------------------------------------------
# Configure HTML output

html_theme = 'sphinx_rtd_theme'
html_theme = 'classic'
html_static_path = ['_static']
html_show_sourcelink = True            # Link to source from pages.

latex_elements = {
    "preamble": u"""
\\usepackage{newunicodechar}
\\newunicodechar{\u2714}{\\checkmark}
""",
}
