
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

    def parse_and_visit(self, filter_input):
        self.input = filter_input
        syntax_tree = ast.parse(filter_input)
        return self.visit(syntax_tree)

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

    def visit_Str(self, node):
        return node.s

    def visit_Num(self, node):
        return node.n

    def visit_Compare(self, node):
        if len(node.ops) != 1:
            raise FilterError(node,
                              "Filter doesn't support multiple comparators")

        left = self.visit(node.left)
        operator = node.ops[0]
        right = self.visit(node.comparators[0])

        if   isinstance(operator, ast.Eq):     return left == right
        elif isinstance(operator, ast.NotEq):  return left != right
        else:
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
        try:
            for traceable in self.traceables:
                if self.filter_traceable(expression_tree, traceable):
                    matches.append(traceable)
        except FilterError, error:
            message = self.format_error(error, expression_string)
            error.args = (message,)
            error.message = message
            raise
        return matches

    def filter_traceable(self, expression_tree, traceable):
        identifier_values = {}
        identifier_values.update(traceable.attributes)
        identifier_values["tag"] = traceable.tag
        visitor = FilterVisitor(identifier_values)
        return visitor.visit(expression_tree)

    def format_error(self, error, expression_string):
        offset = error.node.col_offset
        input_string = expression_string[offset:]
        if offset > 0:
            input_string = "... " + input_string
        if len(input_string) > 12:
            input_string = input_string[:8].strip() + " ..."
        return ('{0} ("{1}")'
                .format(error.message, input_string))


def test_filter():
    identifier_values = {
        "color": "red",
        "version": 1.2,
    }
    visitor = FilterVisitor(identifier_values)
    pv = visitor.parse_and_visit

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

#    # Operator ">"
#    assert False == pv("version > 2")
#    assert True  == pv("version > 1.1")


def test_filter_traceables():
    traceables_input = [
        ("SAGITTA",    {"title": "Sagitta", "color": "blue",
                        "version": 1.0}),
        ("AQUILA",     {"title": "Aquila", "parent": "SAGITTA",
                        "color": "red", "version": 0.8}),
    ]

    traceables = []
    for tag, attributes in traceables_input:
        traceables.append(Traceable(None, tag))
        traceables[-1].attributes = attributes

    filter = TraceablesFilter(traceables)
    for traceable in filter.filter("color > 'blue'"):
        print traceable, traceable.attributes
