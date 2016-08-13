
import os
from xml.etree import ElementTree
from utils import with_app, pretty_print_xml
from HTMLParser import HTMLParser


# =============================================================================
# Tests

@with_app(buildername="xml", srcdir="basics")
def test_xml_basics(app, status, warning):
    """Verify definition of and linking between traceables

        .. traceable:: TEST-TRACEDEF
            :title: Verify definition of and linking between traceables
            :category: Test
            :test_type: auto
            :parents: REQ-TRACEDIRECTIVE, REQ-ERRORMESSAGES
            :format: table

            This test case verifies that traceable directives result in
            the expected output using the XML builder. It also checks that
            links between traceables are output as expected, including that
            a helpful error message is generated when the input references
            a nonexistent traceable.

        .. traceable-graph::
            :tags: TEST-TRACEDEF
            :relationships: parents
    """

    app.builder.build_all()
    tree = ElementTree.parse(app.outdir / "index.xml")
#    print pretty_print_xml(tree.getroot())

    # Verify that 2 traceables are found.
    assert len(tree.findall(".//target")) == 2
    assert len(tree.findall(".//index")) == 2
    assert len(tree.findall(".//admonition")) == 2
    assert len(tree.findall(".//admonition")) == 2

    # Verify that children-parents relationship are made.
    assert len(tree.findall(".//field_list")) == 2
    parents_fields, children_fields = tree.findall(".//field_list")
    for field in parents_fields:
        field_name = field.findall("./field_name")[0]
        if field_name.text == "children":
            break
    else:
        assert False, "Parent's children field not found!"
    for field in children_fields:
        field_name = field.findall("./field_name")[0]
        if field_name.text == "parents":
            break
    else:
        assert False, "Child's parents field not found!"

    # Verify that a warning is emitted for unknown traceable tag.
    assert (warning.getvalue().find(
        "WARNING: Traceables: no traceable with tag"
        " 'NONEXISTENT' found!") > 0)


@with_app(buildername="html", srcdir="basics")
def test_html_builder(app, status, warning):
    """Verify that html builder runs without errors

        .. traceable:: TEST-HTMLBUILD
            :title: Verify that html builder runs without errors
            :category: Test
            :test_type: auto
            :format: table

            This test case verifies that the html builder can be run
            for basic usage of this extension. This test case also
            checks some basic aspects of the output HTML.

        .. traceable-graph::
            :tags: TEST-HTMLBUILD
            :relationships: parents
    """

    app.builder.build_all()
    with open(app.outdir / "index.html") as index_file:
        index_html = index_file.read()

    # Verify that all traceable's have an ID.
    verifier = HTMLTraceableIdVerifier()
    verifier.feed(index_html)


class HTMLTraceableIdVerifier(HTMLParser):

    def handle_starttag(self, tag, attribute_list):
        # Process only the divs of traceable definitions.
        if tag != "div":
            return
        attributes = dict(attribute_list)
        classes = attributes.get("class", "").split()
        if "admonition" not in classes or "traceable" not in classes:
            return

        # Verify that the traceable's div has an ID attribute.
        assert "id" in attributes, (
               'Expected traceable directive div to have an "id" '
               'attribute, but none found: {0!r}'
               .format(self.get_starttag_text()))


@with_app(buildername="latex", srcdir="basics")
def test_latex_builder(app, status, warning):
    """Verify that latex builder runs without errors

        .. traceable:: TEST-LATEXBUILD
            :title: Verify that latex builder runs without errors
            :category: Test
            :test_type: auto
            :format: table

            This test case verifies that the latex builder can be run
            for basic usage of this extension. This test case only
            checks that the builder runs without error; it does not
            check any of the output.

        .. traceable-graph::
            :tags: TEST-LATEXBUILD
            :relationships: parents
    """

    app.builder.build_all()
#    with open(app.outdir / "Python.tex") as index_file:
#        index_tex = index_file.read()
