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

    def create_presentation_node(self, env, tag, attributes, target_node):
        # Initialize admonition node.
        admonition_node = nodes.admonition()
        admonition_node["classes"] += ["traceable"]

        # Assign the traceable's unique ID to the admonition node, so
        # that HTML bookmarks ("somewhere.html#bookmark") work.
        admonition_node["ids"].append(target_node["refid"])

        # Construct title node.
        admonition_node += self.create_title_node(env, tag, attributes)

        # Construct placeholder node for attribute list.
        attribute_list_node = traceable_attribute_list()
        attribute_list_node["traceable-tag"] = tag
        attribute_list_node["traceable-target"] = target_node
        attribute_list_node["traceable-attributes"] = attributes
        admonition_node += attribute_list_node

        # Finalize admonition node.
        self.state.nested_parse(self.content, self.content_offset,
                                admonition_node)
        return admonition_node

    def create_title_node(self, env, tag, attributes):
        # Sanitize title.
        title_attribute = attributes.get("title", "")
        if title_attribute is None:
            title_attribute = ""
        title_attribute = title_attribute.strip()

        # Construct title mode.
        messages = []
        if title_attribute:
            parsed_title_nodes, new_messages = \
                self.state.inline_text(title_attribute, self.lineno)
            messages.extend(new_messages)
            title_content = nodes.inline()
            title_content += nodes.literal(text=tag)
            title_content += nodes.inline(text=" -- ")
            title_content += parsed_title_nodes
        else:
            title_content = nodes.literal(text=tag)

        title_node = nodes.title(tag, "", title_content)
        title_node.source, title_node.line = (
            self.state_machine.get_source_and_line(self.lineno))

        return [title_node] + messages

    def run(self):
        env = self.state.document.settings.env
        tag = self.arguments[0]
        attributes = self.options

        target_node = self.create_target_node(env, tag, attributes)
        index_node = self.create_index_node(env, tag, attributes)
        presentation_node = self.create_presentation_node(env, tag,
                                                          attributes,
                                                          target_node)

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

        return [target_node, index_node, presentation_node]


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
