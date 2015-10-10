
import os
from xml.etree import ElementTree
from utils import with_app, pretty_print_xml


#=============================================================================
# Tests

@with_app(buildername="xml", srcdir="matrix", warningiserror=True)
def test_list(app, status, warning):
    app.build()

    # Verify that ...
    tree = ElementTree.parse(app.outdir / "matrix_basic.xml")
    pretty_print_xml(tree.getroot())
    assert len(tree.findall(".//list_item")) == 2
