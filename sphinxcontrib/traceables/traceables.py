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
from .display import traceable_display
from .utils import is_valid_traceable_attribute_name


# =============================================================================
# Node types

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
        target_node["traceables-tag"] = tag
        target_node["traceables-attributes"] = attributes
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
        messages = []

        # Verify the supplied attributes are valid.
        attributes = {}
        for name, value in self.options.items():
            if is_valid_traceable_attribute_name(name):
                attributes[name] = value
            else:
                message = ("Traceable attribute has invalid syntax: {0!r}"
                           .format(name))
                env.warn(env.docname, message, self.lineno)
                msg = nodes.system_message(message=message,
                                           level=2, type="ERROR",
                                           source=env.docname,
                                           line=self.lineno)
                messages.append(msg)

        # Determine traceable display format.
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
        display_node["line"] = self.lineno
        display_node["traceables-tag"] = tag
        display_node["traceables-format"] = format
        display_node["traceables-options"] = {}

        # Insert remaining content into placeholder.
        self.state.nested_parse(self.content, self.content_offset,
                                display_node)

        return [target_node, index_node, display_node] + messages


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
    # 3-tuples: (name-at-source-traceable,
    #            name-at-destination-traceable,
    #            directional-or-not)
    ("children", "parents",     True),
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
    app.add_directive("traceable", TraceableDirective)
    app.add_role("traceable", XRefRole(nodeclass=traceable_xref,
                                       innernodeclass=nodes.literal,
                                       warn_dangling=True))
