"""
The ``matrix`` module: Matrices and lists of traceables
============================================================================

"""

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from .infrastructure import ProcessorBase, TraceablesFilter


#===========================================================================
# Node types

class traceable_list(nodes.General, nodes.Element):
    pass


#===========================================================================
# Directives

class TraceableListDirective(Directive):

    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "filter": directives.unchanged,
    }

    def run(self):
        env = self.state.document.settings.env
        node = traceable_list()
        node.docname = env.docname
        node.lineno = self.lineno
        node["traceables-filter"] = self.options.get("filter", None) or None
        return [node]


#===========================================================================
# Processor

class ListProcessor(ProcessorBase):

    def __init__(self, app):
        ProcessorBase.__init__(self, app)

    def process_doctree(self, doctree, docname):
        traceables = sorted(self.storage.traceables_set,
                            key=lambda t: t.tag)
        filter = TraceablesFilter(traceables)
        for list_node in doctree.traverse(traceable_list):
            filter_expression = list_node["traceables-filter"]
            if filter_expression:
                filtered_traceables = filter.filter(filter_expression)
            else:
                filtered_traceables = traceables
            new_node = nodes.bullet_list()
            for traceable in filtered_traceables:
                item_node = nodes.list_item()
                item_node += traceable.make_reference_node(
                    self.app.builder, docname)
                new_node += item_node
            list_node.replace_self(new_node)


#===========================================================================
# Setup and register extension

def setup(app):
    app.add_node(traceable_list)
    app.add_directive("traceable-list", TraceableListDirective)
