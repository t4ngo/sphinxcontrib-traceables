
import os
from xml.etree import ElementTree
from utils import with_app, pretty_print_xml


# =============================================================================
# Tests

@with_app(buildername="xml", srcdir="graph", warningiserror=True)
def test_graph(app, status, warning):
    app.build()
    tree = ElementTree.parse(app.outdir / "index.xml")

    # Verify that 1 graphviz node is found.
    assert len(tree.findall(".//graphviz")) == 1
