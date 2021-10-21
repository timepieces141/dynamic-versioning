'''
Test the module dynamic_versioning.utils
'''


# core libraries
import importlib.machinery
import os
from pathlib import Path
import subprocess

# third parties libraries
from distutils.command.bdist import bdist
from distutils.command.install import install
from distutils.command.sdist import sdist

# testing libraries
import pytest

# local libraries
from dynamic_versioning import configuration

# the module under test
from dynamic_versioning import utils


def test_git_describe_no_tags(monkeypatch, caplog):
    '''
    Test that the system exits when there are no annotated tags in the repo.
    '''
    # monkeypatch the Popen object's communicate method to produce our specific
    # error
    def mock_communicate(self, input=None, timeout=None):
        return (None, b'fatal: No names found, cannot describe anything.\n')
    monkeypatch.setattr(subprocess.Popen, "communicate", mock_communicate)

    # test the function, expecting the error
    with pytest.raises(SystemExit):
        utils.git_describe()
        assert "No annotated tags! Please make sure there is at least one annotated tag for this " \
               "repository." in caplog.text


def test_git_describe_unknown_error(monkeypatch, caplog):
    '''
    Test that the system exits when `git describe` returns an unknown error.
    '''
    # monkeypatch the Popen object's communicate method to produce an error
    def mock_communicate(self, input=None, timeout=None):
        return (None, b'Some other error')
    monkeypatch.setattr(subprocess.Popen, "communicate", mock_communicate)

    # test the function, expecting the error
    with pytest.raises(SystemExit):
        utils.git_describe()
        assert "Some other error" in caplog.text


def test_git_describe_cant_parse(monkeypatch, caplog):
    '''
    Test that the system exits when `git describe` produces an unparseable
    description.
    '''
    # monkeypatch the Popen object's communicate method to produce an error
    def mock_communicate(self, input=None, timeout=None):
        return (b'lskdjfoisfdojl', None)
    monkeypatch.setattr(subprocess.Popen, "communicate", mock_communicate)

    # test the function, expecting the error
    with pytest.raises(SystemExit):
        utils.git_describe()
        assert "The most recent tag 'lskdjfoisfdojl' cannot be parsed. Please check that your current tag adheres to " \
               "simple semantic versioning (major.minor.[patch])." in caplog.text


@pytest.mark.parametrize("description", [
    (b'0.0.0-12-gdeadbee'), # major, minor, patch
    (b'0.0-12-gdeadbee'), # major & minor
])
def test_git_describe_all_zeroes_error(monkeypatch, caplog, description):
    '''
    Test that the system exits when `git describe` evaluates to 0.0.0 as a
    version.
    '''
    # monkeypatch the Popen object's communicate method to produce an error
    def mock_communicate(self, input=None, timeout=None):
        return (description, None)
    monkeypatch.setattr(subprocess.Popen, "communicate", mock_communicate)

    # test the function, expecting the error
    with pytest.raises(SystemExit):
        utils.git_describe()
        assert "The most recent tag evaluates to 0.0.0 (with 12 additional commits). Please check that your current " \
               "tag adhere's to simple semantic versioning (major.minor.[patch])." in caplog.text


@pytest.mark.parametrize("description,expected", [
    (b'0.1-12-gdeadbee', [0, 1, 0, 12]), # major, minor
    (b'0.0.1-12-gdeadbee', [0, 0, 1, 12]), # major, minor, patch
    (b'v0.1-12-gdeadbee', [0, 1, 0, 12]), # "v" major, minor
    (b'v0.0.1-12-gdeadbee', [0, 0, 1, 12]), # "v" major, minor, patch
    (b'V0.1-12-gdeadbee', [0, 1, 0, 12]), # "V" major, minor
    (b'V0.0.1-12-gdeadbee', [0, 0, 1, 12]), # "V" major, minor, patch
])
def test_git_describe(monkeypatch, caplog, description, expected):
    '''
    Test that the git_describe method returns us the current version (as a
    list of major, minor, patch). Here we test lots of descriptions.
    '''
    # monkeypatch the Popen object's communicate method to produce a parseable
    # description
    def mock_communicate(self, input=None, timeout=None):
        return (description, None)
    monkeypatch.setattr(subprocess.Popen, "communicate", mock_communicate)

    # test the function
    assert utils.git_describe() == expected
    assert "Current version: {}.{}.{} (with {} additional commits)".format(*expected) in caplog.text


def test_bump_version_bad_option(caplog):
    '''
    Test that the bump_version method errors when an invalid value has been
    provided to --version-bump.
    '''
    with pytest.raises(SystemExit):
        utils.bump_version(None, None, None, "foobar")
        assert "The value provided to --version-bump ('foobar') is invalid. It must be one of: 'major', 'minor', or " \
               "'patch'." in caplog.text


@pytest.mark.parametrize("major,minor,patch,bump,expected", [
    (1, 2, 3, "major", "2.0.0"), # major bump
    (1, 2, 3, "MAJOR", "2.0.0"), # MAJOR bump
    (1, 2, 3, "minor", "1.3.0"), # minor bump
    (1, 2, 3, "MINOR", "1.3.0"), # MINOR bump
    (1, 2, 3, "patch", "1.2.4"), # patch bump
    (1, 2, 3, "PATCH", "1.2.4"), # PATCH bump
])
def test_bump_version(caplog, major, minor, patch, bump, expected):
    '''
    Test that the bump_version method bumps the version provided accordingly.
    '''
    assert expected == utils.bump_version(major, minor, patch, bump)


def test_create_dev_version():
    '''
    Test that the create_dev_version returns a "dev" formatted version.
    '''
    assert "2.0.0.dev8" == utils.create_dev_version(1, 8)


def test__read_version_file_not_found(monkeypatch, caplog):
    '''
    Test the _read_version_file method when the version.py file does not exist.
    PyFakeFS does not work with importlib, so here we will just make the
    loader's exec_module() method raise the appropriate exception.
    '''
    # patch loader's exec_module method
    monkeypatch.setattr(importlib.machinery.SourceFileLoader,
                        "exec_module",
                        lambda self, module: (_ for _ in ()).throw(FileNotFoundError()))

    # patch the call to get the version path, so we can test for it in the logging
    version_file = Path("/development") / "project" / "src" / "top_level" / "version.py"
    monkeypatch.setattr(configuration, "version_path", lambda: str(version_file))

    # test the function expecting the error
    assert utils._read_version_file() is None
    assert f"Version file was not found at '{version_file}'. Attempting to determine version another " \
           "way." in caplog.text


def test__read_version_file_missing_attr(monkeypatch, caplog):
    '''
    Test the _read_version_file method when the version.py file exists, but does
    not contain the __version__ "magic" variable. PyFakeFS does not work with
    importlib, so here we will just make importlib.util's module_from_spec
    () method return an object, but on that doesn't have the attribute we are
    looking for. And then, patch the loader's exec_module() to pass, since we
    don't want it to choke on our dummy module.
    '''
    # patch importlib's module_from_spec to return our object with the attribute
    monkeypatch.setattr(importlib.util,
                        "module_from_spec",
                        lambda spec: type('',(object,),{})())

    # patch loader's exec_module to pass
    monkeypatch.setattr(importlib.machinery.SourceFileLoader, "exec_module", lambda self, module: None)

    # patch the call to get the version path, so we can test for it in the logging
    version_file = Path("/development") / "project" / "src" / "top_level" / "version.py"
    monkeypatch.setattr(configuration, "version_path", lambda: str(version_file))

    # test the function expecting the error
    assert utils._read_version_file() is None
    assert f"Version file was found at '{version_file}', however it did not contain the variable __version__. " \
           "Attempting to determine version another way." in caplog.text


def test__read_version_file(monkeypatch, caplog):
    '''
    Test the _read_version_file method when the version.py file exists and it
    contains an exported version. PyFakeFS does not work with importlib, so
    here we will just make importlib.util's module_from_spec() method return an
    object that has the attribute we are looking for. And then, patch the
    loader's exec_module() to pass, since we don't want it to choke on our
    dummy module.
    '''
    # patch importlib's module_from_spec to return our object with the attribute
    monkeypatch.setattr(importlib.util,
                        "module_from_spec",
                        lambda spec: type('',(object,),{"__version__": "1.2.3"})())

    # patch loader's exec_module to pass
    monkeypatch.setattr(importlib.machinery.SourceFileLoader, "exec_module", lambda self, module: None)

    # patch the call to get the version path, so we can test for it in the logging
    version_file = Path("/development") / "project" / "src" / "top_level" / "version.py"
    monkeypatch.setattr(configuration, "version_path", lambda: str(version_file))

    # test the function expecting the error
    assert utils._read_version_file() == "1.2.3"
    assert f"Version file found. Using version '1.2.3' found within." in caplog.text


VERSION_FILE_EXPECTED = """'''
Version of 'dynamic-versioning'
'''

__version__ = "1.2.3"
"""

def test_write_version_file(fs, monkeypatch):
    '''
    Test the version file get written correctly.
    '''
    # first patch the call to configuration's version_path function
    top_level_dir = Path("/development") / "project" / "src" / "top_level"
    fs.create_dir(top_level_dir)
    version_file = top_level_dir / "version.py"
    monkeypatch.setattr(configuration, "version_path", lambda: str(version_file))

    # next patch the call to configuration's version_docstring function
    monkeypatch.setattr(configuration, "version_docstring", lambda: "'''\nVersion of '{package_name}'\n'''\n\n")

    # call the function
    utils.write_version_file("1.2.3", "dynamic-versioning")
    assert os.path.exists(version_file)

    # open and compare the file contents with what we expect
    with open(version_file, "r", encoding="utf-8") as version_fd:
        assert VERSION_FILE_EXPECTED == version_fd.read()


VERSION_FILE_EXPECTED2 = """'''
Version of 'Dynamic Versioning'
'''

__version__ = "1.2.3"
"""

def test_write_version_file_custom_description(fs, monkeypatch):
    '''
    Test that when a custom version docstring has been provided through
    configuration (especially one that does NOT provide a format "location" for
    the package name), it is used to create the version.py file.
    '''
    # first patch the call to configuration's version_path function
    top_level_dir = Path("/development") / "project" / "src" / "top_level"
    fs.create_dir(top_level_dir)
    version_file = top_level_dir / "version.py"
    monkeypatch.setattr(configuration, "version_path", lambda: str(version_file))

    # next patch the call to configuration's version_docstring function
    monkeypatch.setattr(configuration, "version_docstring", lambda: "'''\nVersion of 'Dynamic Versioning'\n'''\n\n")

    # call the function
    utils.write_version_file("1.2.3", "this value shouldn't matter")
    assert os.path.exists(version_file)

    # open and compare the file contents with what we expect
    with open(version_file, "r", encoding="utf-8") as version_fd:
        assert VERSION_FILE_EXPECTED2 == version_fd.read()


@pytest.mark.parametrize("read_version_file_return,git_describe_return,create_dev_version_return,expected", [
    ("1.2.3", None, None, "1.2.3"),
    (None, [1, 2, 3, 8], "2.0.0.dev8", "2.0.0.dev8"),
    (None, [1, 2, 3, 0], None, "1.2.3"),
])
def test_default_versioning(monkeypatch, read_version_file_return, git_describe_return, create_dev_version_return, expected):
    '''
    Test the default_versioning method's triage logic. The appropriate calls
    out are patched because each of them are tested elsewhere - we're just
    concerned here with the triage logic.
    '''
    # patch call to _read_version_file
    monkeypatch.setattr(utils, "_read_version_file", lambda: read_version_file_return)

    # patch call to git_describe
    monkeypatch.setattr(utils, "git_describe", lambda: git_describe_return)

    # patch call to create_dev_version
    monkeypatch.setattr(utils, "create_dev_version", lambda major, commits: create_dev_version_return)

    # test the function
    assert utils.default_versioning() == expected
