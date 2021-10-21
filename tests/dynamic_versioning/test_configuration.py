'''
Test the module dynamic_versioning.configuration
'''


# core libraries
import inspect
import os
from pathlib import Path

# testing libraries
import pytest

# module under test
from dynamic_versioning import configuration


def test__discover_top_level_package_failure():
    '''
    Test the _discover_top_level_package function when the project directory
    given does not contain a directory with an __init__.py somewhere in the tree
    (such as the testing directory we are in).
    '''
    with pytest.raises(SystemExit):
        configuration._discover_top_level_package(os.path.dirname(__file__))

def test__discover_top_level_package():
    '''
    Test the _discover_top_level_package function when given a valid project
    directory, such as OUR project directory.
    '''
    project_dir = Path(os.path.dirname(__file__)) / ".." / ".."
    expected_top_level = project_dir.expanduser().resolve() / "src" / "dynamic_versioning"
    assert expected_top_level.samefile(configuration._discover_top_level_package(project_dir.expanduser().resolve()))

def test_configure_top_level_given():
    '''
    Test the configure() function when the top-level package path has been
    given.
    '''
    # call the configure function with a dummy path
    top_level_dir = "/somewhere"
    configuration.configure(top_level_dir)
    assert str(configuration.version_path()) == "/somewhere/version.py"
    assert configuration.version_docstring() == "'''\nVersion of '{package_name}'\n'''\n\n"

def test_configure_no_top_level_given(monkeypatch):
    '''
    In this test we test what value the system will give
    _discover_top_level_package and make sure it is what is expected. We
    monkeypatch that call to check the incoming, but to also provide a canned
    response (avoiding the error condition) that can be checked when the value
    is used.
    '''

    # define a mock _discover_top_level_package
    def mock_discover_top_level_package(project_dir):
        '''
        Mock _discover_top_level_package function that checks our incoming
        value, then returns a canned value that can be checked later.
        '''
        # the caller is us, so it should be this module's file
        assert project_dir == __file__
        return "/somewhere"

    # patch the call
    monkeypatch.setattr(configuration, "_discover_top_level_package", mock_discover_top_level_package)

    # call the function and test configuration sets
    configuration.configure()
    assert str(configuration.version_path()) == "/somewhere/version.py"
    assert configuration.version_docstring() == "'''\nVersion of '{package_name}'\n'''\n\n"


def test_configure_version_file_given():
    '''
    Test the configure function with a configured version file name. Here we
    provide the top level directory in the simplest of ways, since that
    functionality has already been tested.
    '''
    # call the configure function with a dummy path
    top_level_dir = "/somewhere"
    configuration.configure(top_level_dir, "foobar.py")
    assert str(configuration.version_path()) == "/somewhere/foobar.py"
    assert configuration.version_docstring() == "'''\nVersion of '{package_name}'\n'''\n\n"


def test_configure_docstring_given():
    '''
    Test the configure function with a configured version file docstring. Here
    we provide the top level directory in the simplest of ways, since that
    functionality has already been tested.
    '''
    # call the configure function with a dummy path
    top_level_dir = "/somewhere"
    configuration.configure(top_level_dir, version_docstring_format="description")
    assert str(configuration.version_path()) == "/somewhere/version.py"
    assert configuration.version_docstring() == "description"
