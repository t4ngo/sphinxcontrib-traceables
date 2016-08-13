
import os
import re
from xml.etree import ElementTree
from utils import with_app, pretty_print_xml


# =============================================================================
# Tests

@with_app(buildername="xml", srcdir="graph", warningiserror=True)
def test_graph_xml(app, status, warning):
    """Verify creation of graphviz nodes

        .. traceable:: TEST-GRAPHXML
            :title: Verify creation of graphviz nodes
            :category: Test
            :test_type: auto
            :parents: REQ-TRACEGRAPHS
            :format: table

            This test case verifies that a graph directive results in
            a graphviz node in XML output. That effectively shows that the
            directive is processed. This test case does not verify that
            the output diagram is generated, because the XML builder doesn't
            do further processing.

        .. traceable-graph::
            :tags: TEST-GRAPHXML
            :relationships: parents
    """

    app.builder.build_all()
    tree = ElementTree.parse(app.outdir / "index.xml")

    # Verify that 1 graphviz node is found.
    assert len(tree.findall(".//graphviz")) == 1

@with_app(buildername="html", srcdir="graph", warningiserror=True)
def test_graph_html(app, status, warning):
    """Verify creation of traceable-graph image files

        .. traceable:: TEST-GRAPHHTML
            :title: Verify creation of traceable-graph image files
            :category: Test
            :test_type: auto
            :parents: REQ-TRACEGRAPHS
            :format: table

            This test case verifies that a graph directive results in
            and output image file in HTML output. That effectively shows
            that the directive is processed, and that graphviz is then
            called and successfully generates an output image file. This
            test case does not verify that the output image is correct.

        .. traceable-graph::
            :tags: TEST-GRAPHHTML
            :relationships: parents
    """

    app.build()

    # Verify that output contains link to graph.
    with (app.outdir / "index.html").open('rb') as index_html_file:
        index_html = index_html_file.read()
    assert re.search('<img src="_images/graphviz-[^"]+.png"', index_html)

@with_app(buildername="html", srcdir="graph_error")
def test_graph_no_valid_start_tags(app, status, warning):
    """Verify error handling of traceable-graph without start tags

        .. traceable:: TEST-GRAPHNOSTARTTAGS
            :title: Verify error handling of traceable-graph without start tags
            :category: Test
            :test_type: auto
            :parents: REQ-TRACEGRAPHS, REQ-ERRORMESSAGES
            :format: table

            This test case verifies that a graph directive, for which no
            valid start tags have been defined, generates a descriptive
            error message.

        .. traceable-graph::
            :tags: TEST-GRAPHNOSTARTTAGS
            :relationships: parents
    """

    app.build()

    # Verify that output contains link to graph.
    with (app.outdir / "index.html").open('rb') as index_html_file:
        index_html = index_html_file.read()
    assert re.search("Traceables: no valid tags for graph,"
                     " so skipping graph", index_html)
