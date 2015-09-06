
import os
from xml.etree import ElementTree
from utils import with_app, pretty_print_xml


#=============================================================================
# Tests

@with_app(buildername="xml", srcdir="graph")
def test_graph(app, status, warning):
    app.build()
    tree = ElementTree.parse(app.outdir / "index.xml")
    pretty_print_xml(tree.getroot())

    # Verify that 1 graphviz node is found.
    assert len(tree.findall(".//graphviz")) == 1
