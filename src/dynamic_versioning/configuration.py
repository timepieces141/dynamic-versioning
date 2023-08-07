'''
This module defines the configuration function that must be called sometime
before the call to setup(), even if it provides no changes to the configuration
values.
'''


# core libraries
import os
import pathlib
import inspect


# module level configuration
__configuration__ = {
    "version_path": None,
    "docstring": "'''\nVersion of '{package_name}'\n'''\n\n"
}

def version_path():
    '''
    Helper function for retrieving the path at which the version file should be
    written, or after it has been written, can be found.
    '''
    return __configuration__["version_path"]


def version_docstring():
    '''
    Helper function for retrieving the docstring that should be written at the
    top of the version file.
    '''
    return __configuration__["docstring"]


def _discover_top_level_package(project_dir):
    '''
    Return the path to the top level package - that is, the first directory
    under the project directory with an __init__.py file.
    '''
    for root, _, files in os.walk(project_dir):
        for file in files:
            if file == "__init__.py":
                return root

    raise SystemExit("There does not appear to be a top-level package (containing an __init__.py file) in this or any "
                     "sub-directory.")


def _find_setup_file():
    '''
    Seek out the setup file and return it as a Path.
    '''
    for frame in inspect.stack():
        if pathlib.Path(frame.filename).name == "setup.py":
            return pathlib.Path(frame.filename).expanduser().resolve()

    raise SystemExit("Unable to find the setup.py file!")


def configure(top_level_pkg=None, version_file_name=None, version_docstring_format=None):
    '''
    Accept the configuration values and set the global variables used to create
    the version file.
    '''
    # if top-level directory is given populate that
    if top_level_pkg is not None:
        top_level_package = pathlib.Path(top_level_pkg).expanduser().resolve()

    # otherwise, discover the top-level directory from the location of the
    # setup.py file
    else:
        top_level_package = _discover_top_level_package(_find_setup_file().parent)

    # assemble the version file
    __configuration__["version_path"] = str(
        (pathlib.Path(top_level_package) / (version_file_name or "version.py")).expanduser().resolve()
    )

    # if docstring provided, save it off
    if version_docstring_format is not None:
        __configuration__["docstring"] = version_docstring_format
