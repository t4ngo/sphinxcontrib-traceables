"""
The ``traceables`` module: Core traceables functionality
===============================================================================

"""


import collections
import textwrap
from docutils import nodes
from docutils.parsers.rst import Directive, directives
import sphinx
from sphinx import addnodes
from sphinx.locale import _
from sphinx.roles import XRefRole
from sphinx.environment import NoUri
from sphinx.util.compat import make_admonition
from sphinx.util.nodes import make_refnode

from .infrastructure import ProcessorBase, Traceable, TraceablesStorage


# =============================================================================
# Node types

class traceable_display(nodes.General, nodes.Element):
    pass


class traceable_attribute_list(nodes.General, nodes.Element):
    pass


class traceable_xref(nodes.Inline, nodes.Element):
    pass


# =============================================================================
# Utility classes

class DefaultDict(dict):

    def __init__(self, default):
        dict.__init__(self)
        self.default = default

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return self.default

    def __bool__(self):
        return True

    __nonzero__ = __bool__


# =============================================================================
# Directives

class TraceableDirective(Directive):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = DefaultDict(lambda value: value)
    has_content = True

    def create_target_node(self, env, tag, attributes):
        serial = env.new_serialno("traceables")
        target_id = "traceables-{0:d}".format(serial)
        target_node = nodes.target("", "", ids=[target_id])
        target_node["docname"] = env.docname
        target_node["refid"] = target_id
        target_node["lineno"] = self.lineno
        target_node["traceable-tag"] = tag
        target_node["traceable-attributes"] = attributes
        return target_node

    def create_index_node(self, env, tag, attributes):
        if sphinx.version_info[:2] < (1, 4):  # Sphinx earlier than v1.4
            entries = [("single", tag, tag, "")]
        else:  # Sphinx v1.4 and later
            entries = [("single", tag, tag, "", None)]
        index_node = addnodes.index()
        index_node["entries"] = entries
        return index_node

    def run(self):
        env = self.state.document.settings.env
        tag = self.arguments[0]
        attributes = self.options
        format = attributes.pop("format", "admonition")

        target_node = self.create_target_node(env, tag, attributes)
        index_node = self.create_index_node(env, tag, attributes)

        traceable = Traceable(target_node)
        try:
            TraceablesStorage(env).add_traceable(traceable)
        except ValueError, e:
            env.warn_node(e.message, target_node)
            # TODO: Should use error handling similar to this:
            # Error = ExtensionError
            # except self.Error, error:
            #    message = str(error)
            #    self.env.warn_node(message, node)
            #    msg = nodes.system_message(message=message,
            #                               level=2, type="ERROR",
            #                               source=node.source,
            #                               line=node.line)
            #    node.replace_self(msg)

        # Construct placeholder node for traceable display.
        display_node = traceable_display()
        display_node["source"] = env.docname
        display_node["lineno"] = self.lineno
        display_node["traceable-tag"] = tag
        display_node["traceable-format"] = format
        display_node["traceable-options"] = {}

        # Insert remaining content into placeholder.
        self.state.nested_parse(self.content, self.content_offset,
                                display_node)

        return [target_node, index_node, display_node]


# =============================================================================
# Processors

class RelationshipsProcessor(ProcessorBase):

    def process_doctree(self, doctree, docname):
        traceables = self.storage.traceables_set
        relationship_types = self.storage.relationship_types

        relationships = {}
        all_tags = set()
        for relationship_type in relationship_types:
            primary, secondary, directional = relationship_type
            for traceable in traceables:
                all_tags.add(traceable.tag)
                if primary in traceable.attributes:
                    tags_string = traceable.attributes[primary]
                    for tag in traceable.split_tags_string(tags_string):
                        self._add_relationship(relationships, traceable.tag,
                                               tag, primary, secondary)
                        all_tags.add(tag)
                if secondary in traceable.attributes:
                    tags_string = traceable.attributes[secondary]
                    for tag in traceable.split_tags_string(tags_string):
                        self._add_relationship(relationships, tag,
                                               traceable.tag, primary,
                                               secondary)
                        all_tags.add(tag)

        # Add placeholders for unresolved tags.
        for tag in all_tags:
            self.storage.get_or_create_traceable_by_tag(tag)

        # Construct relationships with traceables instead of tags.
        for tag1, name_tag2s in relationships.items():
            traceable = self.storage.get_traceable_by_tag(tag1)
            for name, tag2s in name_tag2s.items():
                traceable.relationships[name] = set()
                for tag2 in tag2s:
                    relative = self.storage.get_traceable_by_tag(tag2)
                    traceable.relationships[name].add(relative)

    def _add_relationship(self, relationships, tag1, tag2, primary, secondary):
        level1 = relationships.setdefault(tag1, {})
        level2 = level1.setdefault(primary, set())
        level2.add(tag2)
        level1 = relationships.setdefault(tag2, {})
        level2 = level1.setdefault(secondary, set())
        level2.add(tag1)


class TraceableDisplayProcessor(ProcessorBase):

    formatters = {}

    @classmethod
    def register_formatter(cls, name, formatter):
        cls.formatters[name] = formatter

    def process_doctree(self, doctree, docname):
        for old_node in doctree.traverse(traceable_display):
            new_node = self.create_traceable_display(docname, old_node)
            old_node.replace_self(new_node)

    def create_traceable_display(self, docname, display_node):
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
        return formatter.format(self.app, docname, display_node, traceable,
                                format_options)

#        return self.create_title_node(traceable)


class AttributeListsProcessor(ProcessorBase):

    def process_doctree(self, doctree, docname):
        for placeholder_node in doctree.traverse(traceable_attribute_list):
            new_node = self.create_attribute_list_node(docname,
                                                       placeholder_node)
            placeholder_node.replace_self(new_node)

    def create_attribute_list_node(self, docname, placeholder_node):
        tag = placeholder_node["traceable-tag"]
        traceable = self.storage.get_traceable_by_tag(tag)
        relationships = traceable.relationships

        # Determine which attributes to list in which order.
        attributes = placeholder_node["traceable-attributes"].copy()
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
                content += relative.make_reference_node(self.app.builder,
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


class XrefProcessor(ProcessorBase):

    def process_doctree(self, doctree, docname):
        for xref_node in doctree.traverse(traceable_xref):
            tag = xref_node["reftarget"]
            traceable = self.storage.get_or_create_traceable_by_tag(tag)
            if traceable.is_unresolved:
                self.env.warn_node("Traceables: no traceable with tag '{0}'"
                                   " found!".format(tag), xref_node)
            new_node = traceable.make_reference_node(self.app.builder,
                                                     docname)
            xref_node.replace_self(new_node)


# =============================================================================
# Built-in formatters

class TraceableDisplayAdmonitionFormatter(object):

    def format(self, app, docname, node, traceable, options):
        env = app.builder.env

        admonition = nodes.admonition()
        admonition["classes"] += ["traceable"]

        # Assign the traceable's unique ID to the admonition node, so
        # that HTML bookmarks ("somewhere.html#bookmark") work.
        admonition["ids"].append(traceable.target_node["refid"])

        # Construct title node.
        admonition += self.create_title_node(traceable)

        # Construct placeholder node for attribute list.
        attribute_list = traceable_attribute_list()
        attribute_list["traceable-tag"] = traceable.tag
        attribute_list["traceable-target"] = traceable.target_node
        attribute_list["traceable-attributes"] = traceable.attributes
        admonition += attribute_list

        # Fill content of admonition node.
        while node.children:
            admonition += node.children.pop(0)

        return [admonition]

    def create_title_node(self, traceable):
        # Construct title mode.
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

    def create_attribute_list_node(self, traceable):
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
                content += relative.make_reference_node(self.app.builder,
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


class TraceableDisplayBlockFormatter(object):

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

    def create_title_node(self, traceable):
        # Construct title mode.
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

    def create_attribute_list_node(self, traceable):
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
                content += relative.make_reference_node(self.app.builder,
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
    "block", TraceableDisplayBlockFormatter())


# =============================================================================
# Define defaults for config values

default_relationships = [
    ("parents",  "children",    True),
    ("sibling",  "sibling",     False),
    ("output",   "created-in",  True),
    ("used-in",  "input",       True),
    ("create",   "created-by",  True),
]


# =============================================================================
# Setup this extension part

def setup(app):
    app.add_config_value("traceables_relationships",
                         default_relationships, "env")
    app.add_node(traceable_xref)
    app.add_node(traceable_attribute_list)
    app.add_directive("traceable", TraceableDirective)
    app.add_role("traceable", XRefRole(nodeclass=traceable_xref,
                                       innernodeclass=nodes.literal,
                                       warn_dangling=True))
