# -*- coding: utf-8 -*-

import sys
import os

# -------------------------------------------------------------------------
# Configure extensions

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.graphviz',
    'sphinx.ext.viewcode',
    'sphinxcontrib.traceables',
]

sys.path.append(os.path.abspath('../../tests'))

# -------------------------------------------------------------------------
# General configuration

project = u'Traceables example project: Requirements'
copyright = u'2016, t4ngo'
version = '0.2'                        # The short X.Y version.
release = '0.2'                        # The full version, incl alpha/beta/rc.

templates_path = ['_templates']
source_suffix = '.txt'                 # The suffix of source filenames.
master_doc = 'index'                   # The master toctree document.
today_fmt = '%Y-%m-%d'
exclude_patterns = ['_build']
pygments_style = 'sphinx'
keep_warnings = True                   # Keep warnings in output documents.

rst_prolog = '''
.. include:: <isoamsa.txt>
'''

# -------------------------------------------------------------------------
# Configure HTML output

html_theme = 'sphinx_rtd_theme'
#html_theme = 'classic'
#html_theme = 'pyramid'
#html_theme = 'haiku'
html_static_path = ['_static']
html_copy_source = True
html_show_sourcelink = True            # Link to source from pages.

#latex_elements = {
#    "preamble": u"""
#\\usepackage{newunicodechar}
#\\newunicodechar{\u2714}{\\checkmark}
#""",
#}

traceables_relationships = [
    ("children", "parents", True),
]
