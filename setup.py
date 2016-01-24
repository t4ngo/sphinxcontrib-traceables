
from setuptools import setup, find_packages
from pip.req import parse_requirements
from pip.download import PipSession
import os


# --------------------------------------------------------------------------
# Setup package.

root_dir = os.path.dirname(__file__)


def read(*names):
    path = os.path.join(root_dir, *names)
    with open(path) as f:
        return f.read()


def get_version():
    version_string = read("VERSION.txt").strip()
    return version_string


def get_requirements():
    requirements = parse_requirements("requirements.txt",
                                      session=PipSession())
    return [str(r.req) for r in requirements]


setup(
      name="sphinxcontrib-traceables",
      version=get_version(),
      description="Sphinx extension that adds traceability within "
                  "documentation",
      author="Christo Butcher",
      author_email="",
      url="https://github.com/t4ngo/sphinxcontrib-traceables",
      license="Apache 2.0",
      long_description=read("README.rst"),
      packages=find_packages(),
      include_package_data=True,
      install_requires=get_requirements(),
      platforms="any",

      classifiers=[
                   "Development Status :: 3 - Alpha",
                   "Environment :: Other Environment",
                   "Environment :: Plugins",
                   "Framework :: Sphinx :: Extension",
                   "Intended Audience :: Developers",
                   "Intended Audience :: Information Technology",
                   "Intended Audience :: Science/Research",
                   "Intended Audience :: System Administrators",
                   "License :: OSI Approved :: Apache Software License",
                   "Natural Language :: English",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   "Topic :: Software Development :: Documentation",
                   "Topic :: Software Development :: Libraries :: "
                        "Python Modules",
                  ],
     )
