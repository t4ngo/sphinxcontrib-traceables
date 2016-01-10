
import os
from xml.etree import ElementTree
from utils import with_app, pretty_print_xml


# =============================================================================
# Tests

@with_app(buildername="xml", srcdir="matrix", warningiserror=True)
def test_matrix_structure(app, status, warning):
    '''Verify generated XML structure for different matrix formats'''
    app.build()

    # Verify matrix with default format.
    tree = ElementTree.parse(app.outdir / "matrix_default.xml")
    # Verify that the correct number of list items were generated.
    assert len(tree.findall(".//list_item")) == 11

    # Verify matrix with columns format.
    tree = ElementTree.parse(app.outdir / "matrix_columns.xml")
#    pretty_print_xml(tree.getroot())
    # Verify that the correct number of rows and entries were generated.
    rows = tree.findall(".//tbody/row")
    assert len(rows) == 3
    assert len(rows[0].findall("./entry")) == 2

    # Verify matrix with table format.
    tree = ElementTree.parse(app.outdir / "matrix_table.xml")
#    pretty_print_xml(tree.getroot())
    # Verify that the correct number of rows and entries were generated.
    rows = tree.findall(".//tbody/row")
    assert len(rows) == 3
    assert len(rows[0].findall("./entry")) == 3
