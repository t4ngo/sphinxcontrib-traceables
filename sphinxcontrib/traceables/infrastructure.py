"""
The ``infrastructure`` module: Infrastructure for processing traceables
============================================================================

"""

import collections
import textwrap
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx import addnodes
from sphinx.locale import _
from sphinx.roles import XRefRole
from sphinx.environment import NoUri
from sphinx.util.compat import make_admonition
from sphinx.util.nodes import make_refnode


#===========================================================================
# Information storage classes

class TraceablesStorage(object):

    def __init__(self, env):
        self.env = env
        self.config = env.config
        self.analyze_relationship_types()

    def analyze_relationship_types(self):
        self.relationship_types = self.config.traceables_relationships
        self.relationship_directions = {}
        for relationship_type in self.relationship_types:
            primary, secondary, directional = relationship_type
            if directional:
                self.relationship_directions[primary] = 1
                self.relationship_directions[secondary] = -1
            else:
                self.relationship_directions[primary] = 0
                self.relationship_directions[secondary] = 0

    def purge(self, docname):
        # Iterate over a copy of the list and remove from the original.
        for node in set(self.traceables_set):
            if node["docname"] == docname:
                self.traceables_set.remove(node)

    def add_traceable(self, node):
        self.traceables_set.add(node)

    @property
    def traceables_set(self):
        if not hasattr(self.env, "traceables_traceables_set"):
            self.env.traceables_traceables_set = set()
        return self.env.traceables_traceables_set

    @property
    def traceables_dict(self):
        traceables_dict = {}
        for traceable in self.traceables_set:
            traceables_dict[traceable.tag] = traceable
        return traceables_dict

    def get_traceable_by_tag(self, tag):
        return self.traceables_dict[tag]

    def get_or_create_traceable_by_tag(self, tag):
        traceable = self.traceables_dict.get(tag)
        if not traceable:
            traceable = Traceable(None, tag)
            self.add_traceable(traceable)
        return traceable

    def get_relationship_direction(self, name):
        return self.relationship_directions[name]


#===========================================================================
# Processor

class Traceable(object):

    def __init__(self, target_node, unresolved_tag=None):
        if target_node and not unresolved_tag:
            self.target_node = target_node
            self.tag = target_node["traceable-tag"]
            self.attributes = target_node["traceable-attributes"]
        elif unresolved_tag and not target_node:
            self.target_node = None
            self.tag = unresolved_tag
            self.attributes = {}
        else:
            raise Exception("Must specify only one of target_node"
                            " and unresolved_tag")

        self.relationships = {}

    def __str__(self):
        arguments = [self.tag]
        if self.is_unresolved:
            arguments.append("unresolved")
        return "<{0}({1})>".format(self.__class__.__name__,
                                   ", ".join(arguments))

    @property
    def title(self):
        title = self.attributes.get("title")
        return title if title else self.tag

    @property
    def is_unresolved(self):
        return self.target_node == None

    def make_reference_node(self, builder, docname):
        text_node = nodes.literal(text=self.tag)
        if self.target_node:
            try:
                return make_refnode(builder,
                                    docname,
                                    self.target_node["docname"],
                                    self.target_node["refid"],
                                    text_node,
                                    self.tag)
            except NoUri:
                builder.env.warn_node("Traceables: No URI for '{0}' available!"
                                      .format(self.tag), self.target_node)
                return text_node
        else:
            return text_node

    def split_tags_string(self, tags_string):
        if not tags_string:
            return []
        return filter(None, (tag.strip() for tag in tags_string.split(",")))


class ProcessorManager(object):

    processor_classes = []

    @classmethod
    def register_processor_classes(cls, processors):
        cls.processor_classes.extend(processors)

    def __init__(self, app):
        self.app = app

        self.processors = []
        for processor_class in self.processor_classes:
            self.processors.append(processor_class(app))

    def process_doctree(self, doctree, docname):
        for processor in self.processors:
            processor.process_doctree(doctree, docname)


class ProcessorBase(object):

    def __init__(self, app):
        self.app = app
        self.env = self.app.builder.env
        self.config = self.app.builder.config
        self.storage = TraceablesStorage(self.env)

    def process_doctree(self, doctree, docname):
        pass


#===========================================================================
# Signal handling functions

def process_doctree(app, doctree, docname):
    processor_manager = ProcessorManager(app)
    processor_manager.process_doctree(doctree, docname)

def purge_docname(app, env, docname):
    storage = TraceablesStorage(env)
    storage.purge(docname)


#===========================================================================
# Setup and register extension

def setup(app):
    app.connect("doctree-resolved", process_doctree)
    app.connect("env-purge-doc", purge_docname)
