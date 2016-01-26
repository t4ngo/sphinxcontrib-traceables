# -*- coding: utf-8 -*-

import sys
import os
from glob import glob

# -------------------------------------------------------------------------
# Configure extensions

extensions = [
    'sphinx.ext.autodoc',
]

# -------------------------------------------------------------------------
# Helper function for retrieving info from files

def read(*names):
    root_dir = os.path.dirname(__file__)
    path = os.path.join(root_dir, *names)
    with open(path) as f:
        return f.read()

# -------------------------------------------------------------------------
# General configuration

project = u'sphinxcontrib.traceables'
copyright = u'2015, Christo'
release = read('..', 'VERSION.txt')    # The full version, incl alpha/beta/rc.
version = '.'.join(release.split('.')[0:2]) # The short X.Y version.

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
html_show_sourcelink = True            # Link to source from pages.
