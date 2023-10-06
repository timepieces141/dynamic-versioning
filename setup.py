'''
Build and distribute the dynamic versioning tool.
'''


# core libraries
import logging
import os
import pathlib

# third parties libraries
from setuptools import setup, find_packages


# setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')


# classifications for this project - see
# https://pypi.python.org/pypi?%3Aaction=list_classifiers
CLASSIFIERS = [
    # project is in the alpha stage
    'Development Status :: 4 - Beta',

    # MIT license
    'License :: OSI Approved :: MIT License',

    # python 3.10 & 3.11 supported
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',

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

# scripts
SCRIPTS = []

# the directory of this setup file
SETUP_DIR = pathlib.Path(__file__).parent

# README
README = (SETUP_DIR / "README.md").read_text()

# source directory
SRC_DIR = SETUP_DIR / "src"


def get_install_requires():
    '''
    Read the requirements file in as a list of project/version requirement
    specifications.
    '''
    with open((SETUP_DIR / "requirements.txt")) as install_fp:
        install_requires = install_fp.read().split("\n")
    return [req for req in install_requires if req]


def get_extras_require():
    '''
    Retrieves the various "extra" dependencies.
    '''
    extras = {}
    for extra in ["dev", "dist", "docs"]:
        with open((SETUP_DIR / f"{extra}-requirements.txt")) as extra_fp:
            requires = extra_fp.read().split("\n")
            extras[extra] = [req for req in requires if req]

    return extras


# call setup with our project-specific values
setup(
    name="dynamic-versioning",
    version="1.1.0",
    description="Provides dynamic versioning of python packages by providing additional options to the standard " \
                "setuptools commands.",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Edward Petersen",
    author_email="edward.petersen@gmail.com",
    url="https://github.com/timepieces141/dynamic-versioning",
    classifiers=CLASSIFIERS,
    license="MIT",
    package_dir=PACKAGE_DIR,
    packages=find_packages(SRC_DIR),
    scripts=SCRIPTS,
    install_requires=get_install_requires(),
    extras_require=get_extras_require()
)
