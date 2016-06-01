"""
The ``graph`` module: Visualization of traceables
===============================================================================

"""

import textwrap
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.ext import graphviz
from graphviz import Digraph

from .infrastructure import ProcessorBase, Traceable


# =============================================================================
# Node types

class traceable_graph(nodes.General, nodes.Element):
    pass


# =============================================================================
# Directives

class TraceableGraphDirective(Directive):

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        "tags": directives.unchanged_required,
        "relationships": directives.unchanged_required,
        "caption": directives.unchanged,
    }
    has_content = True

    def run(self):
        env = self.state.document.settings.env
        node = traceable_graph()
        node.docname = env.docname
        node.lineno = self.lineno
        node["traceable-tags"] = self.options["tags"]
        node["traceable-relationships"] = self.options.get("relationships")
        caption = self.options.get("caption") or "Traceable graph"
        node["traceable-caption"] = caption
        figure_node = graphviz.figure_wrapper(self, node, caption)
        return [figure_node]


# =============================================================================
# Processor

class GraphProcessor(ProcessorBase):

    def __init__(self, app):
        ProcessorBase.__init__(self, app)
        self.graph_styles = default_graph_styles.copy()
        self.graph_styles.update(self.config.traceables_graph_styles)

    def process_doctree(self, doctree, docname):
        for graph_node in doctree.traverse(traceable_graph):
            # Determine graph's starting traceables.
            start_tags = graph_node["traceable-tags"]
            start_traceables = self.get_start_traceables(start_tags,
                                                         graph_node)
            if not start_traceables:
                self.env.warn_node("Traceables: no valid tags for graph,"
                                   " so skipping graph", node)
                continue

            # Determine relationships to include in graph.
            input = graph_node.get("traceable-relationships")
            relationship_length_pairs = self.parse_relationships(input)

            # Construct input for graph.
            graph_input = self.construct_graph_input(start_traceables,
                                                     relationship_length_pairs)

            # Generate diagram input and create output node.
            graphviz_node = graphviz.graphviz()
            graphviz_node["code"] = self.generate_dot(graph_input)
            graphviz_node["options"] = {}
            caption = graph_node.get("traceable-caption", "Traceables graph")
            graphviz_node["alt"] = caption
            graph_node.replace_self(graphviz_node)

    def get_start_traceables(self, tags_string, node):
        tags = Traceable.split_tags_string(tags_string)
        traceables = []
        for tag in tags:
            try:
                traceable = self.storage.get_traceable_by_tag(tag)
                traceables.append(traceable)
            except KeyError:
                self.env.warn_node("Traceables: no traceable with tag '{0}'"
                                   " found!".format(tag), node)
        return traceables

    def parse_relationships(self, input):
        relationships = []
        if input:
            for part in input.split(","):
                pair = part.split(":", 1)
                if len(pair) == 2:
                    relationship = pair[0].strip()
                    try:
                        max_length = int(pair[1].strip())
                    except:
                        raise ValueError("Invalid maximum length: '{0}'"
                                         .format(part))
                else:
                    relationship = part.strip()
                    max_length = None
                if not self.storage.is_valid_relationship(relationship):
                    raise self.Error("Invalid relationship: {0}"
                                     .format(relationship))
                dir = self.storage.get_relationship_direction(relationship)
                relationships.append((relationship, dir, max_length))
        else:
            all_relationship_dirs = self.storage.relationship_directions
            for (relationship, dir) in all_relationship_dirs.items():
                relationships.append((relationship, dir, None))
        return [(relationship, max_length)
                for (relationship, dir, max_length) in relationships]

    def construct_graph_input(self, traceables, relationship_length_pairs):
        graph_input = GraphInput(self.storage, relationship_length_pairs)
        for traceable in traceables:
            graph_input.add_traceable_walk(traceable)
        return graph_input

    def generate_dot(self, graph_input):
        dot = Digraph("Traceable relationships",
                      comment="Traceable relationships")
        dot.body.append("rankdir=LR")
        dot.attr("graph", fontname="helvetica", fontsize="7.5")
        dot.attr("node", fontname="helvetica", fontsize="7.5")
        dot.attr("edge", fontname="helvetica", fontsize="7.5")

        for traceable in graph_input.traceables:
            self.add_dot_traceable(dot, traceable)
        for relationship_info in graph_input.relationships:
            traceable1, traceable2, relationship, direction = relationship_info
            src = traceable1.tag if direction >= 0 else traceable2.tag
            dst = traceable2.tag if direction >= 0 else traceable1.tag
            reverse = self.storage.get_relationship_opposite(relationship)
            dot.edge(src, dst, headlabel=reverse, taillabel=relationship,
                     labelfontsize="7.0", labelfontcolor="#999999")

        return dot.source

    def add_dot_traceable(self, dot, traceable):
        # Construct attributes for dot node.
        if traceable.is_unresolved:
            style = self.graph_styles["__unresolved__"].copy()
        else:
            style = self.graph_styles["__default__"].copy()

        category = traceable.attributes.get("category")
        if category:
            style.update(self.graph_styles.get(category, {}))

        self.add_dot_node(dot, traceable.tag, traceable.title, style)

    def add_dot_node(self, dot, tag, title, style):
        # Process line wrapping.
        line_wrap = style.pop("textwrap", False)
        if line_wrap:
            title = " \\n ".join(textwrap.wrap(title, line_wrap))

        # Add dot node.
        dot.node(tag, title, **style)


# =============================================================================
# Container class for storing graph input

class GraphInput(object):

    def __init__(self, storage, relationship_length_pairs):
        self.storage = storage
        self.relationship_length_pairs = relationship_length_pairs
        self._traceables = set()
        self._relationships = set()

    def add_traceable_walk(self, traceable):
        self._walk_traceable(traceable, 0)

        # Make all relationships forward in direction.
        for relationship_info in self._relationships.copy():
            traceable1, traceable2, relationship, direction = relationship_info
            if direction == -1:
                opposite = self.storage.get_relationship_opposite(relationship)
                reversed_info = (traceable2, traceable1, opposite, 1)
                self._relationships.remove(relationship_info)
                self._relationships.add(reversed_info)

    def _walk_traceable(self, traceable, length):
        self._traceables.add(traceable)
        for relationship, max_length in self.relationship_length_pairs:
            if max_length and length >= max_length:
                continue
            direction = self.storage.get_relationship_direction(relationship)
            relatives = traceable.relationships.get(relationship, ())
            for relative in relatives:
                relationship_info = (traceable, relative, relationship,
                                     direction)
                if relationship_info not in self._relationships:
                    self._relationships.add(relationship_info)
                    self._walk_traceable(relative, length + 1)

    @property
    def traceables(self):
        return sorted(self._traceables)

    @property
    def relationships(self):
        return sorted(self._relationships)


# =============================================================================
# Define defaults for config values

default_graph_styles = {
    "__default__": {
        "shape": "box",
        "textwrap": 16,
    },
    "__unresolved__": {
        "shape": "box",
        "style": "filled, setlinewith(0.1)",
        "color": "gray80",
        "fillcolor": "white",
        "fontcolor": "gray30",
    },
}


# =============================================================================
# Setup extension

def setup(app):
    app.add_config_value("traceables_graph_styles",
                         default_graph_styles, "env")
    app.add_node(traceable_graph)
    app.add_directive("traceable-graph", TraceableGraphDirective)
