
import os
from xml.etree import ElementTree
from utils import with_app, pretty_print_xml


#=============================================================================
# Tests

@with_app(buildername="xml", srcdir="list", warningiserror=True)
def test_list(app, status, warning):
    app.build()
    tree = ElementTree.parse(app.outdir / "index.xml")
    pretty_print_xml(tree.getroot())

    # Verify that 2 list item nodes are found.
    assert len(tree.findall(".//list_item")) == 2
