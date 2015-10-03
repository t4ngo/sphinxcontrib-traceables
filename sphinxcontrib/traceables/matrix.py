"""
The ``matrix`` module: Matrices of traceables
============================================================================

"""

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from .infrastructure import ProcessorBase


#===========================================================================
# Node types

class traceable_list(nodes.General, nodes.Element):
    pass


#===========================================================================
# Directives

class TraceableListDirective(Directive):

    required_arguments = 0
    optional_arguments = 0

    def run(self):
        env = self.state.document.settings.env
        node = traceable_list()
        node.docname = env.docname
        node.lineno = self.lineno
        return [node]


#===========================================================================
# Processor

class ListProcessor(ProcessorBase):

    def __init__(self, app):
        ProcessorBase.__init__(self, app)

    def process_doctree(self, doctree, docname):
        traceables = sorted(self.storage.traceables_set,
                            key=lambda t: t.tag)
        for list_node in doctree.traverse(traceable_list):
            new_node = nodes.bullet_list()
            for traceable in traceables:
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
