"""
The ``display`` module: Formatting output of individual traceables
===============================================================================

"""


from docutils import nodes
from docutils.parsers.rst import Directive, directives

from .infrastructure import ProcessorBase, Traceable, TraceablesStorage
from .utils import passthrough, latex_escape


# =============================================================================
# Node types

class traceable_display(nodes.General, nodes.Element):
    """Placeholder node for displaying a single traceable.

    Attributes:
        traceable-tag: The tag of the traceable to display.
        traceable-format: The format in which to display the traceable.
        traceable-format-options: Options specific for the display format.

    """

    pass


class traceable_display_table(nodes.General, nodes.Element):
    """Placeholder node to be replaced by a builder-specific table display.

    Attributes:
        traceables-traceable: Instance of :obj:`Traceable` to be presented
            in the output.

    """

    pass


# =============================================================================
# Processors

class TraceableDisplayProcessor(ProcessorBase):

    formatters = {}

    @classmethod
    def register_formatter(cls, name, formatter):
        cls.formatters[name] = formatter

    def __init__(self, app):
        ProcessorBase.__init__(self, app, traceable_display)

    def process_node(self, display_node, doctree, docname):
        tag = display_node["traceable-tag"]
        traceable = self.storage.get_traceable_by_tag(tag)

        format = display_node["traceable-format"]
        format_options = display_node.get("traceable-format-options")
        formatter = self.formatters.get(format)

        if not formatter:
            message = ("Unknown formatter name: '{0}';"
                       " available formatters: {1}"
                       .format(format, ", ".join(self.formatters.keys())))
            self.env.warn_node(message, display_node)
            new_nodes = [nodes.system_message(message=message,
                                              level=2, type="ERROR",
                                              source=display_node["source"],
                                              line=display_node["lineno"])]
            display_node.replace_self(new_nodes)
            return

        new_nodes = formatter.format(self.app, docname, display_node, traceable,
                                     format_options)
        display_node.replace_self(new_nodes)


# =============================================================================
# Built-in formatters

class TraceableDisplayFormatterBase(object):

    def format(self, app, docname, node, traceable, options):
        raise NotImplementedError()

    def create_title_node(self, traceable):
        if traceable.has_title():
            title_content = nodes.inline()
            title_content += nodes.literal(text=traceable.tag)
            title_content += nodes.inline(text=" -- ")
            title_content += nodes.inline(text=traceable.title)
        else:
            title_content = nodes.literal(text=traceable.tag)

        title_node = nodes.inline()
        title_node += title_content

        return [title_node]


# -----------------------------------------------------------------------------

class TraceableDisplayAdmonitionFormatter(TraceableDisplayFormatterBase):

    def format(self, app, docname, node, traceable, options):
        env = app.builder.env

        admonition = nodes.admonition()
        admonition["classes"] += ["traceable"]

        # Assign the traceable's unique ID to the admonition node, so
        # that HTML bookmarks ("somewhere.html#bookmark") work.
        admonition["ids"].append(traceable.target_node["refid"])

        # Add title and attribute list.
        admonition += self.create_title_node(traceable)
        admonition += self.create_attribute_list_node(app, docname, traceable)

        # Fill content of admonition node.
        while node.children:
            admonition += node.children.pop(0)

        return [admonition]

    def create_attribute_list_node(self, app, docname, traceable):
        relationships = traceable.relationships

        # Determine which attributes to list in which order.
        attributes = traceable.attributes.copy()
        for relationship_name in relationships.keys():
            attributes.pop(relationship_name, None)
        attributes.pop("title", None)

        # Create node to contain list of attributes.
        field_list_node = nodes.field_list()

        # Add relationship attributes.
        for relationship_name, relatives in sorted(relationships.items()):
            field_node = nodes.field()
            field_node += nodes.field_name(text=relationship_name)
            content = nodes.inline()
            for relative in sorted(relatives, key=lambda t: t.tag):
                if len(content):
                    content += nodes.inline(text=", ")
                content += relative.make_reference_node(app.builder,
                                                        docname)
            field_node += nodes.field_body("", content)
            field_list_node += field_node

        # Add non-relationship attributes.
        for attribute_name, attribute_value in sorted(attributes.items()):
            field_node = nodes.field()
            field_node += nodes.field_name(text=attribute_name)

            # Prepend space to avoid bug in the LaTeX builder of Sphinx v1.4
            # which can cause \leavevmode to be stuck to following text.
            content = nodes.inline(text=" " + attribute_value)

            field_node += nodes.field_body("", content)
            field_list_node += field_node

        return field_list_node


# -----------------------------------------------------------------------------

class TraceableDisplayTableFormatter(TraceableDisplayFormatterBase):

    def format(self, app, docname, node, traceable, options):
        env = app.builder.env

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
        entry = nodes.entry(morecols=1)
        row += entry
        entry += self.create_title_node(traceable)

        # Add table body.
        tbody = nodes.tbody()
        tgroup += tbody

        # Determine which attributes to list in which order.
        relationships = traceable.relationships
        attributes = traceable.attributes.copy()
        for relationship_name in relationships.keys():
            attributes.pop(relationship_name, None)
        attributes.pop("title", None)

        # Add relationship attributes.
        for relationship_name, relatives in sorted(relationships.items()):
            first = True
            for relative in sorted(relatives, key=lambda t: t.tag):
                row = nodes.row()
                tbody += row

                entry = nodes.entry()
                row += entry
                if first:
                    entry += nodes.inline(text=" " + relationship_name)
                    first = False

                entry = nodes.entry()
                row += entry
                entry += relative.make_reference_node(app.builder,
                                                      docname)

        # Add non-relationship attributes.
        for attribute_name, attribute_value in sorted(attributes.items()):
            row = nodes.row()
            tbody += row

            entry = nodes.entry()
            row += entry
            entry += nodes.inline(text=" " + attribute_name)

            entry = nodes.entry()
            row += entry
            # Prepend space to avoid bug in the LaTeX builder of Sphinx v1.4
            # which can cause \leavevmode to be stuck to following text.
            content = nodes.inline(text=" " + attribute_value)
            entry += content

        wrapper = traceable_display_table()
        wrapper["traceables-traceable"] = traceable
        wrapper += table

        return [wrapper] + node.children

    @staticmethod
    def visit_latex(translator, node):
        traceable = node["traceables-traceable"]

        lines = []
#        lines.append(r"\setlength\LTleft{0pt}")
#        lines.append(r"\setlength\LTright{0pt}")
        lines.append(r"\begin{longtable}{ll}")
        lines.append(r"\hline")
        lines.append(r"\multicolumn{2}{l}{\textbf{\textsc{%s} -- %s}} \\"
                     % (latex_escape(traceable.tag.lower()),
                        latex_escape(traceable.title)))
        lines.append(r"\hline")

        # Determine which attributes to list in which order.
        relationships = traceable.relationships
        attributes = traceable.attributes.copy()
        for relationship_name in relationships.keys():
            attributes.pop(relationship_name, None)
        attributes.pop("title", None)

        # Add relationship attributes.
        for relationship_name, relatives in sorted(relationships.items()):
            first = True
            for relative in sorted(relatives, key=lambda t: t.tag):
                if first:
                    lines.append(r"{%s} & {\textsc{%s}%s} \\"
                                 % (latex_escape(relationship_name),
                                    latex_escape(relative.tag.lower()),
                                    latex_escape(" -- " + relative.title)))
                    first = False
                else:
                    lines.append(r" & {\textsc{%s}%s} \\"
                                 % (latex_escape(relative.tag.lower()),
                                    latex_escape(" -- " + relative.title)))

        # Add non-relationship attributes.
        for attribute_name, attribute_value in sorted(attributes.items()):
            lines.append(r"{%s} & {%s} \\"
                         % (latex_escape(attribute_name),
                            latex_escape(attribute_value)))

        lines.append(r"\hline")
        lines.append(r"\end{longtable}")

        translator.body.append("\n".join(lines))
        raise nodes.SkipNode



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

        translator.body.append("\n".join(lines))
        raise nodes.SkipNode


# -----------------------------------------------------------------------------

class TraceableDisplayHiddenFormatter(TraceableDisplayFormatterBase):

    def format(self, app, docname, node, traceable, options):
        return []


# =============================================================================
# Setup this extension part

TraceableDisplayProcessor.register_formatter("admonition",
    TraceableDisplayAdmonitionFormatter())
TraceableDisplayProcessor.register_formatter("table",
    TraceableDisplayTableFormatter())
TraceableDisplayProcessor.register_formatter("hidden",
    TraceableDisplayHiddenFormatter())

def setup(app):

    app.add_node(traceable_display)
    app.add_node(traceable_display_table,
         html=passthrough,
         latex=(TraceableDisplayTableFormatter.visit_latex,
                None))
