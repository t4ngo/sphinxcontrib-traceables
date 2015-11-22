
import infrastructure
import traceables
import matrix
import graph


# ==========================================================================
# Setup and register extension

def setup(app):
    # Perform import within this function to avoid an import circle.
    from sphinxcontrib import traceables

    # Allow extension parts to set themselves up.
    traceables.infrastructure.setup(app)
    traceables.traceables.setup(app)
    traceables.matrix.setup(app)
    traceables.graph.setup(app)

    # Register business logic of extension parts. This is done explicitly
    # here to ensure correct ordering during processing.
    traceables.infrastructure.ProcessorManager.register_processor_classes([
        traceables.traceables.RelationshipsProcessor,
        traceables.traceables.AttributeListsProcessor,
        traceables.traceables.XrefProcessor,
        traceables.matrix.ListProcessor,
        traceables.matrix.MatrixProcessor,
        traceables.graph.GraphProcessor,
    ])

    return {"version": "0.0"}
