
from nose.tools import eq_, assert_raises
from utils import with_app, pretty_print_xml
from sphinxcontrib.traceables.infrastructure import (Traceable,
                                                     TraceablesStorage)


# =============================================================================
# Tests

@with_app(buildername="xml", srcdir="basics")
def test_infrastructure(app, status, warning):
    app.build()
    storage = TraceablesStorage(app.env)

    # Verify exception on invalid relationship name.
    assert_raises(ValueError, storage.get_relationship_direction, "invalid")
    assert_raises(ValueError, storage.get_relationship_opposite, "invalid")

    # Verify Traceable.__str__() doesn't fail.
    for traceable in storage.traceables_set:
        ignored_output = str(traceable)
