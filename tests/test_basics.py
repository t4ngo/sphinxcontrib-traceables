
import os
from xml.etree import ElementTree
from utils import with_app, pretty_print_xml


# =============================================================================
# Tests

@with_app(buildername="xml", srcdir="basics")
def test_basics(app, status, warning):
    app.build()
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
