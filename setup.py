'''
Build and distribute the dynamic versioning tool.
'''


# core libraries
from codecs import open as c_open
import logging
import os
from pathlib import Path

# third parties libraries
from setuptools import setup, find_packages


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
SETUP_LOGGER = logging.getLogger("dynamic-versioning")

# classifications for this project - see
# https://pypi.python.org/pypi?%3Aaction=list_classifiers
CLASSIFIERS = [
    # project is in the alpha stage
    'Development Status :: 4 - Beta',

    # MIT license
    'License :: OSI Approved :: MIT License',

    # python 3 supported
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.0',
    'Programming Language :: Python :: 3.1',
    'Programming Language :: Python :: 3.2',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',

    # framework
    'Framework :: Setuptools Plugin',

    # audience
    'Intended Audience :: Developers',

    # topics
    'Topic :: Software Development :: Build Tools',
    'Topic :: System :: Installation/Setup',
    'Topic :: System :: Software Distribution'
]

# packages
PACKAGE_DIR = {"": "src"}
PACKAGE_DATA = {"": ["media/*"]}

# scripts
SCRIPTS = []

# the directory of this setup file
SETUP_DIR = Path(__file__).parent

# README
README = (SETUP_DIR / "README.md").read_text()

# source directory
SRC_DIR = SETUP_DIR / "src"

# installation dependencies
INSTALL_REQUIRES = c_open((SETUP_DIR / "requirements.txt")).readlines()

# call setup with our project-specific values
setup(
    name='dynamic-versioning',
    version="1.0.0",
    description='Provides dynamic versioning of python packages by providing additional options to the standard distutils commands.',
    long_description=README,
    long_description_content_type="text/markdown",
    author='Edward Petersen',
    author_email="edward.petersen@gmail.com",
    url='https://github.com/timepieces141/dynamic-versioning',
    classifiers=CLASSIFIERS,
    license='MIT',
    package_dir=PACKAGE_DIR,
    packages=find_packages(SRC_DIR),
    package_data=PACKAGE_DATA,
    scripts=SCRIPTS,
    install_requires=INSTALL_REQUIRES
)
