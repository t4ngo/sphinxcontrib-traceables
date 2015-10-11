"""
The ``matrix`` module: Matrices and lists of traceables
============================================================================

"""

import types
from docutils import nodes
from docutils.parsers.rst import Directive, directives

from .infrastructure import ProcessorBase, TraceablesFilter


#===========================================================================
# Processors

class ListProcessor(ProcessorBase):

    def __init__(self, app):
        ProcessorBase.__init__(self, app)

    def process_doctree(self, doctree, docname):
        traceables = sorted(self.storage.traceables_set,
                            key=lambda t: t.tag)
        filter = TraceablesFilter(traceables)
        for list_node in doctree.traverse(traceable_list):
            filter_expression = list_node["traceables-filter"]
            if filter_expression:
                filtered_traceables = filter.filter(filter_expression)
            else:
                filtered_traceables = traceables
            new_node = nodes.bullet_list()
            for traceable in filtered_traceables:
                item_node = nodes.list_item()
                item_node += traceable.make_reference_node(
                    self.app.builder, docname)
                new_node += item_node
            list_node.replace_self(new_node)


class MatrixProcessor(ProcessorBase):

    def __init__(self, app):
        ProcessorBase.__init__(self, app)

    def process_doctree(self, doctree, docname):
        traceables = sorted(self.storage.traceables_set,
                            key=lambda t: t.tag)
#        filter = TraceablesFilter(traceables)
        for matrix_node in doctree.traverse(traceable_matrix):
            relationship = matrix_node["traceables-relationship"]
            opposite = self.storage.get_relationship_opposite(relationship)
            matrix = self.get_related_traceables(traceables, relationship)

            format_name = matrix_node.get("traceables-format")
            formatter = self.get_formatter_method(format_name)
            new_node = formatter(matrix, relationship, opposite, docname)
            matrix_node.replace_self(new_node)

    def get_related_traceables(self, traceables, relationship):
        matrix = []
        for traceable in sorted(traceables):
            relatives = traceable.relationships.get(relationship)
            if relatives:
                matrix.append((traceable, tuple(sorted(relatives))))
        return matrix

    def create_list_table(self, matrix, relationship, opposite, docname):
        table = nodes.table()
        tgroup = nodes.tgroup(cols=2, colwidths="auto"); table += tgroup

        # Add column specifications.
        tgroup += nodes.colspec(colwidth=50)
        tgroup += nodes.colspec(colwidth=50)

        # Add heading row.
        thead = nodes.thead(); tgroup += thead
        row = nodes.row(); thead += row
        entry = nodes.entry(); row += entry
        entry += nodes.paragraph(opposite.capitalize(),
                                 opposite.capitalize())
        entry = nodes.entry(); row += entry
        entry += nodes.paragraph(relationship.capitalize(),
                                 relationship.capitalize())

        # Add table body.
        tbody = nodes.tbody(); tgroup += tbody
        for (traceable, relatives) in matrix:
            # Create first row with a first column.
            row = nodes.row()
            entry = nodes.entry(morerows=len(relatives) - 1)
            row += entry
            paragraph = nodes.paragraph(); entry += paragraph
            paragraph += traceable.make_reference_node(
                self.app.builder, docname)

            for relative in relatives:
                if not row:
                    # Create subsequent rows without a first column.
                    row = nodes.row()
                tbody += row

                entry = nodes.entry(); row += entry
                paragraph = nodes.paragraph(); entry += paragraph
                paragraph += relative.make_reference_node(
                    self.app.builder, docname)

                row = None

        return table

    def create_cross_table(self, matrix, relationship, opposite, docname):
        primaries = []
        secondaries = set()
        for (traceable, relatives) in matrix:
            primaries.append(traceable)
            secondaries.update(relatives)
        secondaries = sorted(secondaries)
        boolean_matrix = []
        for (traceable, relatives) in matrix:
            boolean_row = [secondary in relatives
                           for secondary in secondaries]
            boolean_matrix.append((traceable, boolean_row))

        table = nodes.table()
        table["classes"] += ["traceables-crosstable"]
        tgroup = nodes.tgroup(cols=len(secondaries), colwidths="auto")
        table += tgroup

        # Add column specifications.
        tgroup += nodes.colspec(colwidth=1)
        for column in secondaries:
            tgroup += nodes.colspec(colwidth=1)

        # Add heading row.
        thead = nodes.thead(); tgroup += thead
        row = nodes.row(); thead += row
        entry = nodes.entry(); row += entry
        for secondary in secondaries:
            entry = nodes.entry(); row += entry
            container = nodes.container(); entry += container
            inline = nodes.inline(); container += inline
            paragraph = nodes.paragraph(); inline += paragraph
            paragraph += secondary.make_reference_node(
                self.app.builder, docname)

        # Add table body.
        tbody = nodes.tbody(); tgroup += tbody
        for (traceable, boolean_row) in boolean_matrix:
            row = nodes.row(); tbody += row
            entry = nodes.entry(); row += entry
            paragraph = nodes.paragraph(); entry += paragraph
            paragraph += traceable.make_reference_node(
                self.app.builder, docname)

            for boolean in boolean_row:
                entry = nodes.entry(); row += entry
                if boolean:
                    checkmark = traceable_checkmark(); entry += checkmark
                    checkmark += nodes.inline(u"\u2714", u"\u2714")
                else:
                    continue

        return table

    def create_bullet_list(self, matrix, relationship, opposite, docname):
        new_node = nodes.bullet_list()
        for (traceable, relatives) in matrix:
            item_node = nodes.list_item()
            paragraph_node = nodes.paragraph()
            paragraph_node += traceable.make_reference_node(
                self.app.builder, docname)
            item_node += paragraph_node

            sublist_node = nodes.bullet_list()
            for relative in relatives:
                subitem_node = nodes.list_item()
                subparagraph_node = nodes.paragraph()
                subparagraph_node += relative.make_reference_node(
                    self.app.builder, docname)
                subitem_node += subparagraph_node
                sublist_node += subitem_node
            item_node += sublist_node

            new_node += item_node
        return new_node

    default_format_name = "list"
    formats = {
               "list": create_bullet_list,
               "columns": create_list_table,
               "table": create_cross_table,
              }

    def get_formatter_method(self, name):
        if not name:
            name = self.default_format_name
        unbound_formatter = self.formats.get(name)
        if not unbound_formatter:
            raise ValueError("Invalid format: {0}".format(name))
        return types.MethodType(unbound_formatter, self)

    @classmethod
    def directive_format_choice(cls, argument):
        format_names = cls.formats.keys()
        return directives.choice(argument, format_names)


#===========================================================================
# Node types

class traceable_list(nodes.General, nodes.Element):
    pass


class traceable_matrix(nodes.General, nodes.Element):
    pass


class traceable_checkmark(nodes.General, nodes.Element):
    pass


#===========================================================================
# Directives

class TraceableListDirective(Directive):

    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "filter": directives.unchanged,
    }

    def run(self):
        env = self.state.document.settings.env
        node = traceable_list()
        node.docname = env.docname
        node.lineno = self.lineno
        node["traceables-filter"] = self.options.get("filter") or None
        return [node]


class TraceableMatrixDirective(Directive):

    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "relationship": directives.unchanged_required,
        "format": MatrixProcessor.directive_format_choice,
    }

    def run(self):
        env = self.state.document.settings.env
        node = traceable_matrix()
        node.docname = env.docname
        node.lineno = self.lineno
        node["traceables-relationship"] = self.options["relationship"]
        node["traceables-format"] = self.options.get("format")
        return [node]


#===========================================================================
# Setup and register extension

def visit_passthrough(self, node):
    pass

def depart_passthrough(self, node):
    pass

passthrough = (visit_passthrough, depart_passthrough)

def visit_traceable_checkmark_latex(self, node):
    self.body.append(r"\checkmark")
    raise nodes.SkipNode


#===========================================================================
# Setup and register extension

def setup(app):
    app.add_node(traceable_list)
    app.add_node(traceable_matrix)
    app.add_node(traceable_checkmark,
                 html=passthrough,
                 latex=(visit_traceable_checkmark_latex, None))
    app.add_directive("traceable-list", TraceableListDirective)
    app.add_directive("traceable-matrix", TraceableMatrixDirective)
    app.add_latex_package("amssymb")  # Needed for "\checkmark" symbol.
