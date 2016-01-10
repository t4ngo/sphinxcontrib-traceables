
from nose.tools import eq_, assert_raises
from utils import with_app, pretty_print_xml


# =============================================================================
# Tests

@with_app(buildername="html", srcdir="matrix", warningiserror=True)
def test_builder_html(app, status, warning):
    '''Verify that HTML builder doesn't fail'''
    app.build()

@with_app(buildername="latex", srcdir="matrix", warningiserror=True)
def test_latex_builder(app, status, warning):
    '''Verify that Latex builder doesn't fail'''
    app.build()
