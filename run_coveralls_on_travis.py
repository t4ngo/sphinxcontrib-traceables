#!/usr/bin/env python

"""
Script to run coveralls only when executed on Travis-CI.

"""


import os
import subprocess


if __name__ == "__main__":
    if "TRAVIS" in os.environ:
        code = subprocess.call("coveralls")
        raise SystemExit(code)
