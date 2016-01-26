"""
The ``infrastructure`` module: Infrastructure for processing traceables
===============================================================================

"""

import os
import glob
import collections
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx import addnodes
from sphinx.locale import _
from sphinx.roles import XRefRole
from sphinx.environment import NoUri
from sphinx.errors import ExtensionError
from sphinx.util.compat import make_admonition
from sphinx.util.nodes import make_refnode
from sphinx.util.osutil import copyfile

from .filter import ExpressionMatcher


# =============================================================================
# Information storage classes

class TraceablesStorage(object):

    def __init__(self, env):
        self.env = env
        self.config = env.config
        self.analyze_relationship_types()

    def analyze_relationship_types(self):
        self.relationship_types = self.config.traceables_relationships
        self.relationship_opposites = {}
        self.relationship_directions = {}
        for relationship_type in self.relationship_types:
            primary, secondary, directional = relationship_type
            self.relationship_opposites[primary] = secondary
            self.relationship_opposites[secondary] = primary
            if directional:
                self.relationship_directions[primary] = 1
                self.relationship_directions[secondary] = -1
            else:
                self.relationship_directions[primary] = 0
                self.relationship_directions[secondary] = 0

    def purge(self, docname):
        # Iterate over a copy of the list and remove from the original.
        for traceable in set(self.traceables_set):
            if traceable.target_node["docname"] == docname:
                self.traceables_set.remove(traceable)

    def add_traceable(self, node):
        known_tags = [t.tag for t in self.traceables_set]
        if node.tag in known_tags:
            raise ValueError("More than one traceable with tag '{0}' "
                             "found!".format(node.tag))
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

    def is_valid_relationship(self, name):
        return name in self.relationship_opposites

    def get_relationship_opposite(self, name):
        try:
            return self.relationship_opposites[name]
        except KeyError:
            raise ValueError("Unknown relationship name: '{0}'".format(name))

    def get_relationship_direction(self, name):
        try:
            return self.relationship_directions[name]
        except KeyError:
            raise ValueError("Unknown relationship name: '{0}'".format(name))


# =============================================================================
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

    def __lt__(self, other):
        if not isinstance(other, Traceable):
            raise ValueError("Cannot compare Traceable instance with other"
                             " type {0}"
                             .format(other.__class__.__name__))
        return self.tag < other.tag

    @property
    def title(self):
        title = self.attributes.get("title")
        return title if title else self.tag

    @property
    def is_unresolved(self):
        return self.target_node is None

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

    @classmethod
    def split_tags_string(cls, tags_string):
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

    Error = ExtensionError

    def __init__(self, app, process_node_type=None):
        self.app = app
        self.env = self.app.builder.env
        self.config = self.app.builder.config
        self.storage = TraceablesStorage(self.env)
        self.process_node_type = process_node_type

    def process_doctree(self, doctree, docname):
        for node in doctree.traverse(self.process_node_type):
            try:
                self.process_node(node, doctree, docname)
            except self.Error, error:
                message = str(error)
                self.env.warn_node(message, node)
                msg = nodes.system_message(message=message,
                                           level=2, type="ERROR",
                                           source=node.source,
                                           line=node.line)
                node.replace_self(msg)

    def process_node(self, node, doctree, docname):
        pass


# =============================================================================
# Filtering class

class TraceablesFilter(object):

    def __init__(self, traceables):
        self.traceables = traceables

    def filter(self, expression_string):
        matcher = ExpressionMatcher(expression_string)
        matching_traceables = []
        for traceable in self.traceables:
            if self.traceable_matches(matcher, traceable):
                matching_traceables.append(traceable)
        return matching_traceables

    def traceable_matches(self, matcher, traceable):
        identifier_values = {}
        identifier_values.update(traceable.attributes)
        identifier_values["tag"] = traceable.tag
        return matcher.matches(identifier_values)


# =============================================================================
# Signal handling functions

def add_static_files(app):
    base_directory = os.path.dirname(__file__)
    static_directory = os.path.join(base_directory, "static")

    stylesheet_glob = os.path.join(static_directory, "*.css")
    for stylesheet_path in glob.glob(stylesheet_glob):
        basename = os.path.basename(stylesheet_path)
        app.add_stylesheet(basename)


def copy_static_files(app, exception):
    if app.builder.name != "html" or exception:
        return

    base_directory = os.path.dirname(__file__)
    static_directory = os.path.join(base_directory, "static")

    for filename in os.listdir(static_directory):
        source_path = os.path.join(static_directory, filename)
        destination_path = os.path.join(app.builder.outdir, "_static",
                                        filename)
        copyfile(source_path, destination_path)


def process_doctree(app, doctree, docname):
    processor_manager = ProcessorManager(app)
    processor_manager.process_doctree(doctree, docname)


def purge_docname(app, env, docname):
    storage = TraceablesStorage(env)
    storage.purge(docname)


# =============================================================================
# Setup extension

def setup(app):
    app.connect("builder-inited", add_static_files)
    app.connect("build-finished", copy_static_files)
    app.connect("doctree-resolved", process_doctree)
    app.connect("env-purge-doc", purge_docname)
