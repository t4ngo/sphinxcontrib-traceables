"""
The ``list`` module: Lists of traceables
===============================================================================

"""

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from .infrastructure import FormatProcessorBase, TraceablesFilter


# =============================================================================
# Node types

class traceable_list(nodes.General, nodes.Element):
    """Placeholder node to be replaced by a list of traceables.

    Attributes:
        traceable-filter: The filter expression to determine which
            traceables to include in the output.

    """

    pass


# =============================================================================
# Processors

class ListProcessor(FormatProcessorBase):

    def __init__(self, app):
        FormatProcessorBase.__init__(self, app, traceable_list)

    def process_node_with_formatter(self, list_node, formatter,
                                    doctree, docname):
        traceables = sorted(self.storage.traceables_set,
                            key=lambda t: t.tag)

        filter = TraceablesFilter(traceables)
        filter_expression = list_node["traceables-filter"]
        if filter_expression:
            filtered_traceables = filter.filter(filter_expression)
        else:
            filtered_traceables = traceables

        options = {
            "format": list_node.get("traceables-format"),
            "filter": list_node.get("traceables-filter"),
            "attributes": list_node.get("traceables-attributes"),
        }

        new_nodes = formatter.format(self.app, docname, list_node,
                                     filtered_traceables, options)
        list_node.replace_self(new_nodes)


# =============================================================================
# Built-in formatters

class ListFormatterBase(object):

    def format(self, app, docname, node, traceables, options):
        raise NotImplementedError()


# -----------------------------------------------------------------------------

class TableListFormatter(ListFormatterBase):

    def format(self, app, docname, node, traceables, options):
        additional_attributes = options.get("attributes") or []
        columns = ["tag", "title"] + additional_attributes

        table = nodes.table()
        table["classes"].append("traceables-listtable")
        tgroup = nodes.tgroup(cols=len(columns), colwidths="auto")
        table += tgroup

        # Add column specifications.
        for attribute_name in columns:
            tgroup += nodes.colspec(colwidth=1)

        # Add heading row.
        thead = nodes.thead()
        tgroup += thead
        row = nodes.row()
        thead += row
        for attribute_name in columns:
            entry = nodes.entry()
            row += entry
            container = nodes.container()
            entry += container
            text = attribute_name.capitalize()
            inline = nodes.inline(text, text)
            container += inline

        # Add table body.
        tbody = nodes.tbody()
        tgroup += tbody
        for traceable in traceables:
            row = nodes.row()
            tbody += row

            for attribute_name in columns:
                entry = nodes.entry()
                row += entry
                if attribute_name == "tag":
                    inline = nodes.inline()
                    inline += traceable.make_reference_node(
                        app.builder, docname)
                elif attribute_name == "title":
                    text = traceable.title if traceable.has_title else ""
                    inline = nodes.inline(text, text)
                else:
                    text = traceable.attributes.get(attribute_name, "")
                    inline = nodes.inline(text, text)
                entry += inline

        return table

#        container = traceable_matrix_crosstable()
#        container += table
#        container["traceables-matrix"] = matrix
#        return container


# -----------------------------------------------------------------------------

class BulletListFormatter(ListFormatterBase):

    def format(self, app, docname, node, traceables, options):
        new_node = nodes.bullet_list()
        for traceable in traceables:
            item_node = nodes.list_item()
            new_node += item_node
            inline = nodes.inline()
            item_node += inline
            inline += traceable.make_reference_node(
                app.builder, docname)
            if traceable.has_title:
                title = u" " + traceable.title
                inline += nodes.inline(title, title)

        return new_node


# =============================================================================
# Directives

def list_of_attributes(argument):
    if not argument:
        return []
    return filter(None, (attribute.strip()
                         for attribute in argument.split(",")))


class TraceableListDirective(Directive):

    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "format": ListProcessor.directive_format_choice,
        "filter": directives.unchanged,
        "attributes": list_of_attributes,
    }

    def run(self):
        env = self.state.document.settings.env

        node = traceable_list()
        node["source"] = env.docname
        node["line"] = self.lineno
        for option in self.option_spec.keys():
            node["traceables-" + option] = self.options.get(option)

        return [node]


# =============================================================================
# Setup this extension part

ListProcessor.register_formatter("table", TableListFormatter(), default=True)
ListProcessor.register_formatter("bullets", BulletListFormatter())

def setup(app):
    app.add_node(traceable_list)
    app.add_directive("traceable-list", TraceableListDirective)
