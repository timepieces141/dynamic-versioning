'''
Test the module dynamic_versioning.configuration
'''


# core libraries
import pathlib
import warnings

# testing libraries
import pytest

# dynamic versioning libraries
from dynamic_versioning import configuration as test_configuration


def test__find_config_file(fs):
    '''
    Test the _find_config_file() function can find the config in a directory
    tree.
    '''
    # create a testing directory tree
    project_dir = pathlib.Path("/project")
    deep_dir = project_dir / "foo" / "bar" / "baz"
    fs.create_dir(str(deep_dir))

    # test the function when the file is not found
    assert not test_configuration._find_config_file(project_dir)

    # place a file a the last level and test
    baz_file = deep_dir / "dynamic_versioning.ini"
    fs.create_file(baz_file)
    assert baz_file == test_configuration._find_config_file(project_dir)

    # place a file a the next level and test
    bar_file = deep_dir.parent / "DYNAMIC_VERSIONING.ini"
    fs.create_file(bar_file)
    assert bar_file == test_configuration._find_config_file(project_dir)

    # place a file a the next level and test
    foo_file = deep_dir.parent.parent / "dynamic_versioning.INI"
    fs.create_file(foo_file)
    assert foo_file == test_configuration._find_config_file(project_dir)

    # place a file a the top level and test
    project_file = project_dir / "DYNAMIC_VERSIONING.INI"
    fs.create_file(project_file)
    assert project_file == test_configuration._find_config_file(project_dir)


# a format for writing an INI file
TEST_INI_CONTENTS_FORMAT = '''
[dynamic_versioning]
new-version = {new_version}
version-bump = {version_bump}
dev-version = {dev_version}
'''


def test_load_config_dynamic_versioning_ini(monkeypatch, fs):
    '''
    Test the load_config() function will return the
    dynamic_versioning.ini file contents if the _find_config_file() function
    returns a valid path.
    '''
    # patch the call to _find_config_file to find it
    project_dir = pathlib.Path("/")
    ini_file = project_dir / "dynamic_versioning.ini"
    monkeypatch.setattr(test_configuration, "_find_config_file", lambda project_dir: ini_file)

    # fill that file with some contents we can check on later
    formatted = TEST_INI_CONTENTS_FORMAT.format(new_version="1.0.0",
                                                version_bump="update",
                                                dev_version="TRUE")
    fs.create_file(ini_file, contents=formatted)

    # test the function
    config = test_configuration.load_config()
    assert "1.0.0" == config["new-version"]
    assert "update" == config["version-bump"]
    assert "TRUE" == config["dev-version"]


# a format for writing an INI file
TEST_TOML_CONTENTS_FORMAT = '''
[project]
name = "example-project"
dependencies = []
dynamic = ["version"]


[tool.dynamic_versioning]
new-version = "{new_version}"
version-bump = "{version_bump}"
dev-version = "{dev_version}"
'''


def test_load_config_pyproject_toml(monkeypatch, fs):
    '''
    Test the load_config() function will return the dynamic_versioning section
    of the pyproject.toml file if the _find_config_file() function returns None.
    '''
    # patch the call to _find_config_file to find nothing
    project_dir = pathlib.Path("/")
    monkeypatch.setattr(test_configuration, "_find_config_file", lambda project_dir: None)

    # fill the toml file with some contents we can check on later
    toml_file = project_dir / "pyproject.toml"
    formatted = TEST_TOML_CONTENTS_FORMAT.format(new_version="1.0.0",
                                                 version_bump="update",
                                                 dev_version="TRUE")
    fs.create_file(toml_file, contents=formatted)

    # test the function
    config = test_configuration.load_config()
    assert "1.0.0" == config["new-version"]
    assert "update" == config["version-bump"]
    assert "TRUE" == config["dev-version"]


def test_load_config_none(monkeypatch, fs):
    '''
    Test the load_config() function will return None if the _find_config_file()
    function returns None and the pyproject.toml file cannot be found.
    '''
    # patch the call to _find_config_file to find nothing
    project_dir = pathlib.Path("/")
    monkeypatch.setattr(test_configuration, "_find_config_file", lambda project_dir: None)

    # test the function
    assert not test_configuration.load_config()


def test_deprecated_configure():
    '''
    Test that the configure() function emits a DeprecatedWarning.
    '''
    with warnings.catch_warnings(record=True) as warns:
        warnings.simplefilter("always")
        test_configuration.configure()
        assert len(warns) == 1
        assert warns[0].category == DeprecationWarning
        assert "All configuration can be provided in dynamic_versioning.ini, pyproject.toml, and/or in the " \
               "environment" in str(warns[0].message)
