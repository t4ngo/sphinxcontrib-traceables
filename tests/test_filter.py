
import os
import ast
from xml.etree import ElementTree
from utils import with_app, pretty_print_xml
from sphinxcontrib.traceables.filter import FilterVisitor, ExpressionMatcher
from sphinxcontrib.traceables.infrastructure import Traceable, TraceablesFilter


#=============================================================================
# Tests for filter expression handling

def test_filter():
    identifier_values = {
        "color": "red",
        "version": 1.2,
    }
    visitor = FilterVisitor(identifier_values)
    def pv(expression_input):
        expression_tree = ast.parse(expression_input)
        return visitor.visit(expression_tree)

    # Operator "=="
    assert True  == pv("color == 'red'")
    assert False == pv("color == 'blue'")
    assert True  == pv("'red' == color")
    assert False == pv("'blue' == color")
    assert True  == pv("'red' == 'red'")
    assert False == pv("'blue' == 'red'")
    assert False == pv("'blue' == 4.2")

    # Operator "!="
    assert False == pv("color != 'red'")
    assert True  == pv("color != 'blue'")

    # Operator ">"
    assert False == pv("version > 2")
    assert True  == pv("version > 1.1")


#=============================================================================
# Tests for filtering of traceables

class FilterTester(object):

    def __init__(self, traceables_input):
        self.traceables = []
        for tag, attributes in traceables_input:
            self.traceables.append(Traceable(None, tag))
            self.traceables[-1].attributes = attributes
        self.filter = TraceablesFilter(self.traceables)

    def verify(self, expression, expected_tags):
        matches = self.filter.filter(expression)
        matched_tags = [traceable.tag for traceable in matches]
        unexpected_tags = [tag for tag in matched_tags
                           if tag not in expected_tags]
        missing_tags = [tag for tag in expected_tags
                        if tag not in matched_tags]
        message_parts = []
        if unexpected_tags:
            message_parts.append("Unexpected but matched tag(s): {0}"
                                 .format(", ".join(unexpected_tags)))
        if missing_tags:
            message_parts.append("Expected but not matched tag(s): {0}"
                                 .format(", ".join(missing_tags)))
        if message_parts:
            message_parts.insert(0, "Filter expression {0!r}"
                                    .format(expression))
            raise Exception("; ".join(message_parts))


def test_filter_traceables():
    traceables_input = [
        ("SAGITTA",    {"title": "Sagitta", "color": "blue",
                        "version": 1.0}),
        ("AQUILA",     {"title": "Aquila", "parent": "SAGITTA",
                        "color": "red", "version": 0.8}),
    ]
    tester = FilterTester(traceables_input)
    tester.verify("color == 'blue'", ["SAGITTA"])
    tester.verify("color == 'red'", ["AQUILA"])
    tester.verify("color >= 'blue'", ["SAGITTA", "AQUILA"])
    tester.verify("version > -1", ["SAGITTA", "AQUILA"])
    tester.verify("version > 0.8", ["SAGITTA"])
    tester.verify("version > 1", [])
    tester.verify("version >= -1", ["SAGITTA", "AQUILA"])
    tester.verify("version >= 0.8", ["SAGITTA", "AQUILA"])
    tester.verify("version >= 1", ["SAGITTA"])
    tester.verify("version < 4", ["SAGITTA", "AQUILA"])
    tester.verify("version < 1", ["AQUILA"])
    tester.verify("version < -0.1", [])
    tester.verify("color in ['blue',' green']", ["SAGITTA"])
