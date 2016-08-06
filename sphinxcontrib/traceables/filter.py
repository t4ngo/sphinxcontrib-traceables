"""
The ``filter`` module: Filter expression processing
===============================================================================

"""

import os
import re
import ast


# =============================================================================
# Custom error class

class FilterError(ValueError):

    def __init__(self, node, message):
        super(FilterError, self).__init__(message)
        self.node = node


class FilterFail(ValueError):

    def __init__(self, node, message):
        super(FilterFail, self).__init__(message)
        self.node = node


# =============================================================================
# Filter class

class ExpressionMatcher(object):

    identifier_re = re.compile(r"^[^\d\W]\w*\Z")

    def __init__(self, expression_string):
        self.expression_string = expression_string
        try:
            self.expression_tree = ast.parse(expression_string)
        except SyntaxError, error:
            raise FilterError(None, "Invalid filter syntax")

    def matches(self, identifier_values):
        # Verify that the supplied identifiers have a valid syntax.
        for identifier in identifier_values.keys():
            if not self.identifier_re.match(identifier):
                raise FilterError(None, "Invalid identifier syntax: {0!r}"
                                        .format(identifier))

        # Perform matching.
        visitor = FilterVisitor(identifier_values)
        return visitor.visit(self.expression_tree)


# =============================================================================
# AST visitor class for filter expressions

class FilterVisitor(ast.NodeVisitor):

    def __init__(self, identifier_values):
        self.identifier_values = identifier_values

    def visit_Module(self, node):
        if len(node.body) == 0:
            raise FilterError(node, "Filter invalid because it is empty")
        elif len(node.body) != 1:
            raise FilterError(node, "Filter invalid because it has multiple"
                                    " expressions")
        return self.visit(node.body[0])

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_Name(self, node):
        identifier = node.id
        if identifier in self.identifier_values:
            return self.identifier_values[identifier]
        else:
            raise FilterFail(node, "Unknown identifier: {0}"
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
        if isinstance(operator, ast.Eq):
            return left == right
        elif isinstance(operator, ast.NotEq):
            return left != right
        elif isinstance(operator, ast.Lt):
            return left < right
        elif isinstance(operator, ast.LtE):
            return left <= right
        elif isinstance(operator, ast.Gt):
            return left > right
        elif isinstance(operator, ast.GtE):
            return left >= right
        elif isinstance(operator, ast.In):
            return left in right
        elif isinstance(operator, ast.NotIn):
            return left not in right
        else:
            # Unsupported operators: ast.Is, ast.IsNot
            raise FilterError(node, "Invalid operator of type {0}"
                                    .format(operator.__class__.__name__))

    def visit_BoolOp(self, node):
        # Operators described here:
        # https://greentreesnakes.readthedocs.org/en/latest/nodes.html#BoolOp
        values = [self.visit(child) for child in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        elif isinstance(node.op, ast.Or):
            return any(values)
        else:
            # No other operators are  present in Python, but just in case.
            raise FilterError(node, "Invalid operator of type {0}"
                                    .format(operator.__class__.__name__))

    def generic_visit(self, node):
        raise FilterError(node, "Invalid input of type {0}"
                                .format(node.__class__.__name__))
