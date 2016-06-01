
import os
import re
from xml.etree import ElementTree
from utils import with_app, pretty_print_xml


# =============================================================================
# Tests

@with_app(buildername="xml", srcdir="graph", warningiserror=True)
def test_graph_xml(app, status, warning):
    app.builder.build_all()
    tree = ElementTree.parse(app.outdir / "index.xml")

    # Verify that 1 graphviz node is found.
    assert len(tree.findall(".//graphviz")) == 1

@with_app(buildername="html", srcdir="graph", warningiserror=True)
def test_graph_html(app, status, warning):
    app.build()

    # Verify that output contains link to graph.
    with (app.outdir / "index.html").open('rb') as index_html_file:
        index_html = index_html_file.read()
    assert re.search('<img src="_images/graphviz-[^"]+.png"', index_html)
