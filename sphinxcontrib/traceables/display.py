"""
The ``display`` module: Formatting output of individual traceables
===============================================================================

"""


from docutils import nodes
from docutils.parsers.rst import Directive, directives

from .infrastructure import ProcessorBase, Traceable, TraceablesStorage


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
            return [nodes.system_message(message=message,
                                         level=2, type="ERROR",
                                         source=display_node["source"],
                                         line=display_node["lineno"])]

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


TraceableDisplayProcessor.register_formatter(
    "admonition", TraceableDisplayAdmonitionFormatter())


class TraceableDisplayBlockFormatter(TraceableDisplayFormatterBase):

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

        return [table]


TraceableDisplayProcessor.register_formatter(
    "block", TraceableDisplayBlockFormatter())


# =============================================================================
# Setup this extension part

def setup(app):
    app.add_node(traceable_display)
