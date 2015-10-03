
import os
import ast
from xml.etree import ElementTree
from utils import with_app, pretty_print_xml
from sphinxcontrib.traceables.infrastructure import Traceable


#=============================================================================
# Tests

class FilterError(ValueError):

    def __init__(self, node, message):
        super(FilterError, self).__init__(message)
        self.node = node


class FilterVisitor(ast.NodeVisitor):

    def __init__(self, identifier_values):
        self.identifier_values = identifier_values

    def visit_Module(self, node):
        if len(node.body) != 1:
            raise FilterError("Filter cannot contain multiple expressions")
        return self.visit(node.body[0])

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_Name(self, node):
        identifier = node.id
        if identifier in self.identifier_values:
            return self.identifier_values[identifier]
        else:
            raise FilterError(node, "Invalid identifier: {0}"
                                    .format(identifier))

    def visit_Num(self, node):
        return node.n

    def visit_Str(self, node):
        return node.s

    def visit_List(self, node):
        return tuple(self.visit(element) for element in node.elts)

    def visit_Compare(self, node):
        if len(node.ops) != 1:
            raise FilterError(node,
                              "Filter doesn't support multiple comparators")

        left = self.visit(node.left)
        operator = node.ops[0]
        right = self.visit(node.comparators[0])

        # Operators described here:
        # https://greentreesnakes.readthedocs.org/en/latest/nodes.html#Compare
        if   isinstance(operator, ast.Eq):     return left == right
        elif isinstance(operator, ast.NotEq):  return left != right
        elif isinstance(operator, ast.Lt):     return left < right
        elif isinstance(operator, ast.LtE):    return left <= right
        elif isinstance(operator, ast.Gt):     return left > right
        elif isinstance(operator, ast.GtE):    return left >= right
        elif isinstance(operator, ast.In):     return left in right
        elif isinstance(operator, ast.NotIn):  return left not in right
        else:
            # Unsupported operators: ast.Is, ast.IsNot
            raise FilterError(node, "Invalid operator of type {0}"
                                    .format(operator.__class__.__name__))

    def generic_visit(self, node):
        raise FilterError(node, "Invalid input of type {0}"
                                .format(node.__class__.__name__))


class TraceablesFilter(object):

    def __init__(self, traceables):
        self.traceables = traceables

    def filter(self, expression_string):
        expression_tree = ast.parse(expression_string)
        matches = []
        for traceable in self.traceables:
            if self.filter_traceable(expression_tree, traceable):
                matches.append(traceable)
        return matches

    def filter_traceable(self, expression_tree, traceable):
        identifier_values = {}
        identifier_values.update(traceable.attributes)
        identifier_values["tag"] = traceable.tag
        visitor = FilterVisitor(identifier_values)
        return visitor.visit(expression_tree)


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
    tester.verify("version < 4", ["SAGITTA", "AQUILA"])
    tester.verify("color in ['blue',' green']", ["SAGITTA"])
