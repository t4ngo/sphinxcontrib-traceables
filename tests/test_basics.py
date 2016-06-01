
import os
from xml.etree import ElementTree
from utils import with_app, pretty_print_xml
from HTMLParser import HTMLParser


# =============================================================================
# Tests

@with_app(buildername="xml", srcdir="basics")
def test_xml_basics(app, status, warning):
    app.builder.build_all()
    tree = ElementTree.parse(app.outdir / "index.xml")

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
    app.builder.build_all()
#    with open(app.outdir / "Python.tex") as index_file:
#        index_tex = index_file.read()
