#! /usr/bin/env python

import sys
import storage_calculator

from setuptools import setup, find_packages

setup(name='storage_calculator',
    version=storage_calculator.__version__,
    description="""Storage cost calculator for SciComp.""",
    author='Brian Hodges',
    author_email='bhodges@fhcrc.org',
    packages=find_packages(),
    entry_points = {
        'console_scripts':
        ['xxxxx = storage_calculator.scripts.calc'],
    },
    test_suite='storage_calculator.test',
    license="TBD",
    )

