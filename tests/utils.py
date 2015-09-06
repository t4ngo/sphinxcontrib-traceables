
import os
import sphinx_testing
from xml.etree import ElementTree
from xml.dom import minidom


#=============================================================================
# Utility functions

def srcdir(name):
    test_root = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(test_root, "data", name)

def pretty_print_xml(node):
    output = minidom.parseString(ElementTree.tostring(node)).toprettyxml(indent="  ")
    lines = [line for line in output.splitlines() if line.strip()]
    print "\n".join(lines)

def with_app(*args, **kwargs):
    kwargs = kwargs.copy()
    if "srcdir" in kwargs:
        kwargs["srcdir"] = srcdir(kwargs["srcdir"])
    return sphinx_testing.with_app(*args, **kwargs)
