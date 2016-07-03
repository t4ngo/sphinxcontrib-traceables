import six
from sphinx.util.texescape import tex_escape_map


# =============================================================================
# Node visiting utilities.

def visit_passthrough(translator, node):
    pass


def depart_passthrough(translator, node):
    pass


passthrough = (visit_passthrough, depart_passthrough)


# =============================================================================
# Latex-related utilities.

def latex_escape(text):
    return six.text_type(text).translate(tex_escape_map)
