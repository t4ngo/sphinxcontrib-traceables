"""
The ``matrix`` module: Matrices and lists of traceables
===============================================================================

"""

import types
import six
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.util.texescape import tex_escape_map

from .infrastructure import ProcessorBase, TraceablesFilter


# =============================================================================
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
        ProcessorBase.__init__(self, app, traceable_matrix)

    def process_node(self, matrix_node, doctree, docname):
        relationship = matrix_node["traceables-relationship"]
        if not self.storage.is_valid_relationship(relationship):
            raise self.Error("Invalid relationship: {0}"
                             .format(relationship))
        matrix = self.build_traceable_matrix(relationship)

        option_keys = [("traceables-max-primaries", "max-primaries"),
                       ("traceables-max-secondaries", "max-secondaries")]
        options = dict((key, matrix_node.get(attribute))
                       for (attribute, key) in option_keys)
        format_name = matrix_node.get("traceables-format")
        formatter = self.get_formatter_method(format_name)
        new_node = formatter(matrix, options, docname)
        matrix_node.replace_self(new_node)

    def build_traceable_matrix(self, forward):
        backward = self.storage.get_relationship_opposite(forward)
        matrix = TraceableMatrix(forward, backward)
        traceables = self.storage.traceables_set
        for traceable in traceables:
            relatives = traceable.relationships.get(forward)
            if not relatives:
                continue
            for relative in relatives:
                matrix.add_traceable_pair(traceable, relative)
        return matrix

    def create_list_table(self, matrix, options, docname):
        table = nodes.table()
        tgroup = nodes.tgroup(cols=2, colwidths="auto")
        table += tgroup

        # Add column specifications.
        tgroup += nodes.colspec(colwidth=50)
        tgroup += nodes.colspec(colwidth=50)

        # Add heading row.
        thead = nodes.thead()
        tgroup += thead
        row = nodes.row()
        thead += row
        entry = nodes.entry()
        row += entry
        backward_relationship = matrix.backward_relationship.capitalize()
        entry += nodes.paragraph(backward_relationship,
                                 backward_relationship)
        entry = nodes.entry()
        row += entry
        forward_relationship = matrix.forward_relationship.capitalize()
        entry += nodes.paragraph(forward_relationship,
                                 forward_relationship)

        # Add table body.
        tbody = nodes.tbody()
        tgroup += tbody
        for traceable in matrix.primaries:
            relatives = matrix.get_relatives(traceable)

            # Create first row with a first column.
            row = nodes.row()
            entry = nodes.entry(morerows=len(relatives) - 1)
            row += entry
            paragraph = nodes.paragraph()
            entry += paragraph
            paragraph += traceable.make_reference_node(
                self.app.builder, docname)

            for relative in relatives:
                if not row:
                    # Create subsequent rows without a first column.
                    row = nodes.row()
                tbody += row

                entry = nodes.entry()
                row += entry
                paragraph = nodes.paragraph()
                entry += paragraph
                paragraph += relative.make_reference_node(
                    self.app.builder, docname)

                row = None

        return table

    def create_splittable_cross_table(self, matrix, options, docname):
        max_primaries = options.get("max-primaries")
        max_secondaries = options.get("max-secondaries")
        subtables = []
        for submatrix in matrix.split(max_secondaries, max_primaries):
            subtable = self.create_cross_table(submatrix, options, docname)
            paragraph = nodes.paragraph()
            paragraph += subtable
            subtables.append(paragraph)
        container = nodes.container()
        container.extend(subtables)
        return container

    def create_cross_table(self, matrix, options, docname):
        table = nodes.table()
        table["classes"].append("traceables-crosstable")
        tgroup = nodes.tgroup(cols=len(matrix.secondaries), colwidths="auto")
        table += tgroup

        # Add column specifications.
        tgroup += nodes.colspec(colwidth=1)
        for column in matrix.secondaries:
            tgroup += nodes.colspec(colwidth=1)

        # Add heading row.
        thead = nodes.thead()
        tgroup += thead
        row = nodes.row()
        thead += row
        entry = nodes.entry()
        row += entry
        for secondary in matrix.secondaries:
            entry = nodes.entry()
            row += entry
            container = nodes.container()
            entry += container
            inline = nodes.inline()
            container += inline
            paragraph = nodes.paragraph()
            inline += paragraph
            paragraph += secondary.make_reference_node(
                self.app.builder, docname)

        # Add table body.
        tbody = nodes.tbody()
        tgroup += tbody
        for primary in matrix.primaries:
            row = nodes.row()
            tbody += row
            entry = nodes.entry()
            row += entry
            paragraph = nodes.paragraph()
            entry += paragraph
            paragraph += primary.make_reference_node(
                self.app.builder, docname)

            for is_related in matrix.get_boolean_row(primary):
                entry = nodes.entry()
                row += entry
                if is_related:
                    checkmark = traceable_checkmark()
                    entry += checkmark
                    checkmark += nodes.inline(u"\u2714", u"\u2714")
                else:
                    continue

        container = traceable_matrix_crosstable()
        container += table
        container["matrix"] = matrix
#        backward = matrix.backward_relationship.capitalize()
#        forward = matrix.forward_relationship.capitalize()
#        container["relationships"] = (forward, backward)
#        container["boolean_matrix"] = 0#boolean_matrix
#        container["secondaries"] = matrix.secondaries
        return container

    def create_bullet_list(self, matrix, options, docname):
        new_node = nodes.bullet_list()
        for traceable in matrix.primaries:
            item_node = nodes.list_item()
            paragraph_node = nodes.paragraph()
            paragraph_node += traceable.make_reference_node(
                self.app.builder, docname)
            item_node += paragraph_node

            sublist_node = nodes.bullet_list()
            for relative in matrix.get_relatives(traceable):
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
               "table": create_splittable_cross_table,
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


# =============================================================================
# Node types

class traceable_list(nodes.General, nodes.Element):
    pass


class traceable_matrix(nodes.General, nodes.Element):
    pass


class traceable_matrix_crosstable(nodes.General, nodes.Element):
    pass


class traceable_checkmark(nodes.General, nodes.Element):
    pass


# =============================================================================
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
        node["traceables-filter"] = self.options.get("filter")
        return [node]


class TraceableMatrixDirective(Directive):

    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "relationship": directives.unchanged_required,
        "format": MatrixProcessor.directive_format_choice,
        "max-columns": directives.nonnegative_int,
        "max-rows": directives.nonnegative_int,
    }

    def run(self):
        env = self.state.document.settings.env
        node = traceable_matrix()
        node.docname = env.docname
#        node.source = env.docname
        node.line = self.lineno
        node["traceables-relationship"] = self.options["relationship"]
        node["traceables-format"] = self.options.get("format")
        node["traceables-max-secondaries"] = self.options.get("max-columns")
        node["traceables-max-primaries"] = self.options.get("max-rows")
        return [node]


# =============================================================================
# Node visitor functions

def visit_passthrough(self, node):
    pass


def depart_passthrough(self, node):
    pass


passthrough = (visit_passthrough, depart_passthrough)


def visit_traceable_matrix_crosstable_latex(self, node):
    matrix = node["matrix"]
    num_columns = len(matrix.secondaries)
    forward_relationship = matrix.forward_relationship.capitalize()
    backward_relationship = matrix.backward_relationship.capitalize()

    lines = []
    lines.append(r"\begin{longtable}{@{} cl*{%d}c @{}}" % num_columns)
    lines.append(r" & & \multicolumn{%d}{c}{%s} \\[2ex]"
                 % (num_columns, latex_escape(forward_relationship)))
    headers = [r"\rotatebox{90}{%s}"
               % latex_escape(head.tag) for head in matrix.secondaries]
    lines.append(r" & & " + r" & ".join(headers) + r"\\")
    lines.append(r"\cmidrule{2-%d}" % (num_columns + 2))
    for index, primary in enumerate(matrix.primaries):
        boolean_row = matrix.get_boolean_row(primary)
        if index > 0:
            # Add horizontal rule above all but the first row.
            lines.append(r"\cmidrule[0.05pt]{2-%d}" % (num_columns + 2))
        checkmarks = [r"\checkmark" if boolean else ""
                      for boolean in boolean_row]
        if index == 0:
            # Add backward relationship name only once.
            lines.append(r"\rotatebox{90}{\llap{%s}}"
                         % latex_escape(backward_relationship))
        lines.append(" & %s & " % latex_escape(primary.tag) +
                     " & ".join(checkmarks) + r"\\")
        lines.append(r"\cmidrule{2-%d}" % (num_columns + 2))
    lines.append(r"\end{longtable}")

    self.body.append("\n".join(lines))
    raise nodes.SkipNode


def visit_traceable_checkmark_latex(self, node):
    self.body.append(r"\checkmark")
    raise nodes.SkipNode


def latex_escape(text):
    return six.text_type(text).translate(tex_escape_map)


# =============================================================================
# Helper class for traceable relationships

class TraceableMatrix(object):

    def __init__(self, forward_relationship, backward_relationship):
        self._forward_relationship = forward_relationship
        self._backward_relationship = backward_relationship
        self._primaries = set()
        self._secondaries = set()
        self._relationships = {}

    def ascii_table(self):
        column_widths = [max(len(t.tag) for t in self.primaries)]
        column_widths.extend(len(t.tag) for t in self.secondaries)
        parts = [" " * column_widths[0]]
        parts.extend(t.tag for t in self.secondaries)
        lines = ["| " + " | ".join(parts) + " |"]
        for primary in self.primaries:
            parts = ["{0:{1}}".format(primary.tag, column_widths[0])]
            for (is_related, width) in zip(self.get_boolean_row(primary),
                                           column_widths[1:]):
                symbol = "x" if is_related else " "
                parts.append("{0:^{1}}".format(symbol, width))
            lines.append("| " + " | ".join(parts) + " |")
        return "\n".join(lines)

    def add_primary(self, primary):
        self._primaries.add(primary)

    def add_secondary(self, secondary):
        self._secondaries.add(secondary)

    def add_traceable_pair(self, primary, secondary):
        self._primaries.add(primary)
        self._secondaries.add(secondary)
        self._relationships.setdefault(primary, set()).add(secondary)

    @property
    def forward_relationship(self):
        return self._forward_relationship

    @property
    def backward_relationship(self):
        return self._backward_relationship

    @property
    def primaries(self):
        return sorted(self._primaries)

    @property
    def secondaries(self):
        return sorted(self._secondaries)

    def get_relatives(self, primary):
        return sorted(self._relationships.get(primary, ()))

    def get_boolean_row(self, primary):
        boolean_row = []
        relatives = self.get_relatives(primary)
        for secondary in self.secondaries:
            boolean_row.append(secondary in relatives)
        return boolean_row

    def split(self, max_secondaries, max_primaries=None):
        secondary_ranges = self.calculate_ranges(len(self._secondaries),
                                                 max_secondaries)
        primary_ranges = self.calculate_ranges(len(self._primaries),
                                               max_primaries)
        matrices = []
        for (primary_start, primary_end) in primary_ranges:
            range_primaries = self.primaries[primary_start:primary_end]
            for (secondary_start, secondary_end) in secondary_ranges:
                range_secondaries = self.secondaries[secondary_start:
                                                     secondary_end]
                submatrix = TraceableMatrix(self.forward_relationship,
                                            self.backward_relationship)
                for primary in range_primaries:
                    submatrix.add_primary(primary)
                for secondary in range_secondaries:
                    submatrix.add_secondary(secondary)
                for primary in range_primaries:
                    for secondary in self.get_relatives(primary):
                        if secondary in range_secondaries:
                            submatrix.add_traceable_pair(primary, secondary)
                matrices.append(submatrix)
        return matrices

    def calculate_ranges(self, total_length, max_range_length):
        ranges = []
        if max_range_length and max_range_length > 0:
            range_index = 0
            while range_index * max_range_length < total_length:
                range_start = range_index * max_range_length
                range_end = min((range_index + 1) * max_range_length,
                                total_length)
                ranges.append((range_start, range_end))
                range_index += 1
        else:
            ranges.append((0, total_length))
        return ranges


# =============================================================================
# Setup extension

def setup(app):
    app.add_node(traceable_list)
    app.add_node(traceable_matrix)
    app.add_node(traceable_matrix_crosstable,
                 html=passthrough,
                 latex=(visit_traceable_matrix_crosstable_latex, None))
    app.add_node(traceable_checkmark,
                 html=passthrough,
                 latex=(visit_traceable_checkmark_latex, None))
    app.add_directive("traceable-list", TraceableListDirective)
    app.add_directive("traceable-matrix", TraceableMatrixDirective)
    app.add_latex_package("amssymb")  # Needed for "\checkmark" symbol.
    app.add_latex_package("booktabs")  # Needed for "\cmidrule" command.
