
import os
import sphinx_tests_util
from xml.etree import ElementTree
from xml.dom import minidom


# =============================================================================
# Utility functions

def srcdir(name):
    test_root = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(test_root, "data", name)


def pretty_print_xml(node):
    minidom_xml = minidom.parseString(ElementTree.tostring(node))
    output = minidom_xml.toprettyxml(indent="  ")
    lines = [line for line in output.splitlines() if line.strip()]
    print "\n".join(lines)


def with_app(*args, **kwargs):
    kwargs = kwargs.copy()

    # Expand test data directory.
    if "srcdir" in kwargs:
        kwargs["srcdir"] = srcdir(kwargs["srcdir"])

    # By default use a fresh build environment.
    if "freshenv" not in kwargs:
        kwargs["freshenv"] = True

    return sphinx_tests_util.with_app(*args, **kwargs)
