"""
The ``matrix`` module: Matrices of traceables
===============================================================================

"""

import types
import six
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.util.texescape import tex_escape_map

from .infrastructure import FormatProcessorBase, TraceablesFilter
from .utils import passthrough, latex_escape


# =============================================================================
# Node types

class traceable_matrix(nodes.General, nodes.Element):
    """Placeholder node to be replaced by a traceables matrix.

    Attributes:
        traceables-relationship: The name of the relationship to display
            between primary and secondary traceables.
        traceables-format: The name of the format with which to display
            the data.
        traceables-filter-primaries: The filter expression to determine
            which traceables are the primary set.
        traceables-filter-secondaries: The filter expression to determine
            which traceables are the secondary set.
        traceables-split-primaries: If set, causes the output to be
            split after the specified number of primary traceables.
        traceables-split-secondaries: If set, causes the output to be
            split after the specified number of secondary traceables.

    """

    pass


class traceable_matrix_crosstable(nodes.General, nodes.Element):
    """Placeholder node to be replaced by a builder-specific matrix.

    Attributes:
        traceables-matrix: Instance of :obj:`TraceableMatrix` storing
            data to be presented in the output.

    """

    pass


class traceable_checkmark(nodes.General, nodes.Element):
    """Placeholder node to be replaced by a builder-specific checkmark symbol.

    This node type has no traceable-specific attributes.

    """

    pass


# =============================================================================
# Processors

class MatrixProcessor(FormatProcessorBase):

    def __init__(self, app):
        FormatProcessorBase.__init__(self, app, traceable_matrix)

    def process_node_with_formatter(self, matrix_node, formatter,
                                    doctree, docname):
        relationship = matrix_node["traceables-relationship"]
        if not self.storage.is_valid_relationship(relationship):
            raise self.Error("Invalid relationship: {0}"
                             .format(relationship))
        filter1 = matrix_node.get("traceables-filter-primaries")
        filter2 = matrix_node.get("traceables-filter-secondaries")
        matrix = self.build_traceable_matrix(relationship, filter1, filter2)

        options = {
            "format": matrix_node.get("traceables-format"),
            "filter-primaries":
                matrix_node.get("traceables-filter-primaries"),
            "filter-secondaries":
                matrix_node.get("traceables-filter-secondaries"),
            "split-primaries":
                matrix_node.get("traceables-split-primaries"),
            "split-secondaries":
                matrix_node.get("traceables-split-secondaries"),
        }
        new_nodes = formatter.format(self.app, docname, matrix_node,
                                     matrix, options)
        matrix_node.replace_self(new_nodes)

    def build_traceable_matrix(self, forward, filter1, filter2):
        # Create empty relationship matrix.
        backward = self.storage.get_relationship_opposite(forward)
        matrix = TraceableMatrix(forward, backward)

        # Prepare for filtering.
        traceables = sorted(self.storage.traceables_set,
                            key=lambda t: t.tag)
        filter = TraceablesFilter(traceables)

        # Apply filter to determine which traceables are valid primaries.
        if filter1:
            valid_primaries = filter.filter(filter1)
            for primary in valid_primaries:
                matrix.add_primary(primary)
        else:
            valid_primaries = traceables

        # Apply filter to determine which traceables are valid secondaries.
        if filter2:
            valid_secondaries = filter.filter(filter2)
            for secondary in valid_secondaries:
                matrix.add_secondary(secondary)
        else:
            valid_secondaries = traceables

        # Add related pairs to the matrix.
        for primary in valid_primaries:
            secondaries = primary.relationships.get(forward) or ()
            for secondary in secondaries:
                if secondary in valid_secondaries:
                    matrix.add_traceable_pair(primary, secondary)

        return matrix


# =============================================================================
# Built-in formatters

class MatrixFormatterBase(object):

    def format(self, app, docname, node, matrix, options):
        raise NotImplementedError()


# -----------------------------------------------------------------------------

class TwoColumnMatrixFormatter(MatrixFormatterBase):

    def format(self, app, docname, node, matrix, options):
#        env = app.builder.env

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
            paragraph += traceable.make_reference_node(app.builder, docname)

            for relative in relatives:
                if not row:
                    # Create subsequent rows without a first column.
                    row = nodes.row()
                tbody += row

                entry = nodes.entry()
                row += entry
                paragraph = nodes.paragraph()
                entry += paragraph
                paragraph += relative.make_reference_node(app.builder, docname)

                row = None

        return table


# -----------------------------------------------------------------------------

class TableMatrixFormatter(MatrixFormatterBase):

    def format(self, app, docname, node, matrix, options):
#        env = app.builder.env

        max_primaries = options.get("split-primaries")
        max_secondaries = options.get("split-secondaries")
        subtables = []
        for submatrix in matrix.split(max_secondaries, max_primaries):
            subtable = self.create_cross_table(app, docname, node,
                submatrix, options)
            paragraph = nodes.paragraph()
            paragraph += subtable
            subtables.append(paragraph)
        container = nodes.container()
        container.extend(subtables)
        return container

    def create_cross_table(self, app, docname, node, matrix, options):
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
            paragraph += secondary.make_reference_node(app.builder, docname)

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
            paragraph += primary.make_reference_node(app.builder, docname)

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
        container["traceables-matrix"] = matrix
#        backward = matrix.backward_relationship.capitalize()
#        forward = matrix.forward_relationship.capitalize()
#        container["relationships"] = (forward, backward)
#        container["boolean_matrix"] = 0#boolean_matrix
#        container["secondaries"] = matrix.secondaries
        return container


# -----------------------------------------------------------------------------

class BulletMatrixFormatter(MatrixFormatterBase):

    def format(self, app, docname, node, matrix, options):
        new_node = nodes.bullet_list()

        for traceable in matrix.primaries:
            item_node = nodes.list_item()
            paragraph_node = nodes.paragraph()
            paragraph_node += traceable.make_reference_node(
                app.builder, docname)
            item_node += paragraph_node

            sublist_node = nodes.bullet_list()
            for relative in matrix.get_relatives(traceable):
                subitem_node = nodes.list_item()
                subparagraph_node = nodes.paragraph()
                subparagraph_node += relative.make_reference_node(
                    app.builder, docname)
                subitem_node += subparagraph_node
                sublist_node += subitem_node
            item_node += sublist_node

            new_node += item_node

        return new_node


# =============================================================================
# Directives

class TraceableMatrixDirective(Directive):

    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "format": MatrixProcessor.directive_format_choice,
        "relationship": directives.unchanged_required,
        "filter-primaries": directives.unchanged,
        "filter-secondaries": directives.unchanged,
        "split-primaries": directives.nonnegative_int,
        "split-secondaries": directives.nonnegative_int,
    }

    def run(self):
        env = self.state.document.settings.env
        node = traceable_matrix()
#        node.docname = env.docname
        node["source"] = env.docname
        node["line"] = self.lineno
        for option in self.option_spec.keys():
            node["traceables-" + option] = self.options.get(option)
        return [node]


# =============================================================================
# Node visitor functions

def visit_traceable_matrix_crosstable_latex(self, node):
    matrix = node["traceables-matrix"]
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


# =============================================================================
# Helper class for traceable relationship matrices

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
# Setup this extension part

MatrixProcessor.register_formatter(
    "table", TableMatrixFormatter(), default=True)
MatrixProcessor.register_formatter(
    "columns", TwoColumnMatrixFormatter())
MatrixProcessor.register_formatter(
    "list", BulletMatrixFormatter())

def setup(app):
    app.add_node(traceable_matrix)
    app.add_node(traceable_matrix_crosstable,
                 html=passthrough,
                 latex=(visit_traceable_matrix_crosstable_latex, None))
    app.add_node(traceable_checkmark,
                 html=passthrough,
                 latex=(visit_traceable_checkmark_latex, None))
    app.add_directive("traceable-matrix", TraceableMatrixDirective)
    app.add_latex_package("amssymb")  # Needed for "\checkmark" symbol.
    app.add_latex_package("booktabs")  # Needed for "\cmidrule" command.
