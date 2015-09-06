
import infrastructure
import traceables
import graph


#===========================================================================
# Setup and register extension

def setup(app):
    # Perform import within this function to avoid an import circle.
    from sphinxcontrib import traceables

    # Allow extension parts to set themselves up.
    traceables.infrastructure.setup(app)
    traceables.traceables.setup(app)
    traceables.graph.setup(app)

    # Register business logic of extension parts. This is done explicitly
    # here to ensure correct ordering during processing.
    traceables.infrastructure.ProcessorManager.register_processor_classes([
        traceables.traceables.TraceablesProcessor,
        traceables.traceables.RelationshipsProcessor,
        traceables.traceables.AttributeListsProcessor,
        traceables.traceables.XrefProcessor,
        traceables.graph.GraphProcessor,
    ])

    return {"version": "0.0"}
