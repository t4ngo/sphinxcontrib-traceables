
import os
from xml.etree import ElementTree
from utils import with_app, pretty_print_xml


#=============================================================================
# Tests

@with_app(buildername="xml", srcdir="list", warningiserror=True)
def test_list(app, status, warning):
    app.build()

    # Verify that basic list has 2 list item nodes.
    tree = ElementTree.parse(app.outdir / "list_basic.xml")
    assert len(tree.findall(".//list_item")) == 2

    # Verify that filtered list has 1 list item node.
    tree = ElementTree.parse(app.outdir / "list_filter.xml")
    assert len(tree.findall(".//list_item")) == 1
