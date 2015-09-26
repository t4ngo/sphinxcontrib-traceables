"""
The ``graph`` module: Visualization of traceables
============================================================================

"""

import textwrap
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.ext import graphviz
from graphviz import Digraph

from .infrastructure import ProcessorBase


#===========================================================================
# Node types

class traceable_graph(nodes.General, nodes.Element):
    pass


#===========================================================================
# Directives

class TraceableGraphDirective(Directive):

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        "start": directives.unchanged_required,
    }
    has_content = True

    def run(self):
        env = self.state.document.settings.env
        node = traceable_graph()
        node.docname = env.docname
        node.lineno = self.lineno
        node["traceable-start"] = self.options["start"]
        return [node]


#===========================================================================
# Processor

class GraphProcessor(ProcessorBase):

    def __init__(self, app):
        ProcessorBase.__init__(self, app)
        self.graph_styles = default_graph_styles.copy()
        self.graph_styles.update(self.config.traceables_graph_styles)

    def process_doctree(self, doctree, docname):
        for graph_node in doctree.traverse(traceable_graph):
            # Find start traceable.
            tag = graph_node["traceable-start"]
            try:
                traceable = self.storage.get_traceable_by_tag(tag)
            except KeyError:
                self.env.warn_node("Traceables: no traceable with tag '{0}' found!"
                                   .format(tag), graph_node)
                return

            # Construct relationship specification.
            traceables = set()
            traceables.add(traceable)
            relationships = []
            for name, relateds in traceable.relationships.items():
                dir = self.storage.get_relationship_direction(name)
                for related in relateds:
                    traceables.add(related)
                    relationships.append((traceable, related, dir))
            sorted_traceables = sorted(traceables, key=lambda t: t.tag)

            # Generate diagram input and create output node.
            graphviz_node = graphviz.graphviz()
            graphviz_node["code"] = self.generate_dot(sorted_traceables,
                                                      relationships)
            graphviz_node["options"] = []
            graphviz_node["inline"] = False
#            caption = "Relationship diagram for {0}".format(traceable.tag)
#            figure_node = graphviz.figure_wrapper(self, graphviz_node,
#                                                  caption)
            graph_node.replace_self(graphviz_node)

    def generate_dot(self, traceables, relationships):
        dot = Digraph("Traceable relationships",
                      comment="Traceable relationships")
        dot.body.append("rankdir=LR")
        dot.attr("graph", fontname="helvetica", fontsize="7.5")
        dot.attr("node", fontname="helvetica", fontsize="7.5")
        dot.attr("edge", fontname="helvetica", fontsize="7.5")

        for traceable in traceables:
            self.add_dot_traceable(dot, traceable)
        for traceable1, traceable2, direction in relationships:
            src = traceable1.tag if direction >= 0 else traceable2.tag
            dst = traceable2.tag if direction >= 0 else traceable1.tag
            dot.edge(src, dst)

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


#===========================================================================
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


#===========================================================================
# Setup and register extension

def setup(app):
    app.add_config_value("traceables_graph_styles",
                         default_graph_styles, "env")
    app.add_node(traceable_graph)
    app.add_directive("traceable-graph", TraceableGraphDirective)
