import re
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
# Input checking utilities.

identifier_re = re.compile(r"^[^\d\W]\w*\Z")


def is_valid_traceable_attribute_name(input):
    if identifier_re.match(input):
        return True
    else:
        return False


# =============================================================================
# Latex-related utilities.

def latex_escape(text):
    return six.text_type(text).translate(tex_escape_map)
