'''
Test the module dynamic_versioning.commands
'''


# core libraries
import os
import pathlib
from distutils.dist import Distribution, DistributionMetadata

# third party libraries
from setuptools import Command, _normalization
from setuptools.command.egg_info import egg_info

# testing libraries
import pytest

# dynamic versioning libraries
from dynamic_versioning import commands as test_commands
from dynamic_versioning import configuration, utils


@pytest.fixture
def empty_distribution():
    '''
    Create a mock
    '''
    return Distribution()


@pytest.fixture(autouse=True)
def neuter_command(monkeypatch):
    '''
    In this fixture we monkey patch Command's __init__, initialize_options, and
    run methods, as we call them in the code, but we don't need to test those
    here.
    '''
    monkeypatch.setattr(Command, "initialize_options", lambda self: None)
    monkeypatch.setattr(Command, "run", lambda self: None)
    monkeypatch.setattr(egg_info, "_maybe_tag", lambda self, version: version)
    monkeypatch.setattr(_normalization, "best_effort_version", lambda version: version)


def test__read_config(monkeypatch, empty_distribution):
    '''
    Test DynamicVersioningEggInfo's _read_config() method sets the member fields
    with values found in a config file.
    '''
    # patch the call to load_config() to return a dictionary of values we can
    # test later
    monkeypatch.setattr(configuration, "load_config", lambda: {"new-version": "1.0.0", "version-bump": "update", "dev-version": "TRUE"})

    # read the config and check the values
    instance = test_commands.DynamicVersioningEggInfo(empty_distribution)
    instance._read_config()
    assert instance.new_version == "1.0.0"
    assert instance.version_bump == utils.VersionPart.UPDATE
    assert instance.dev_version


def test__read_environment(empty_distribution):
    '''
    Test DynamicVersioningEggInfo's _read_config() method sets the member fields
    with values found in the environment.
    '''
    # set the values in the env
    os.environ["DV_NEW_VERSION"] = "1.0.0"
    os.environ["DV_VERSION_BUMP"] = "Minor"
    os.environ["DV_DEV_VERSION"] = "false"

    # read the config and check the values
    instance = test_commands.DynamicVersioningEggInfo(empty_distribution)
    instance._read_environment()
    assert instance.new_version == "1.0.0"
    assert instance.version_bump == utils.VersionPart.MINOR
    assert not instance.dev_version


def test__validate_fields(monkeypatch, empty_distribution):
    '''
    Test DynamicVersioningEggInfo's _validate_fields() method overwrites the
    new_version field when it is not valid.
    '''
    # patch the call to validate_semantic_versioning() to return False
    monkeypatch.setattr(utils, "validate_semantic_versioning", lambda potential_version: False)

    # test the function
    instance = test_commands.DynamicVersioningEggInfo(empty_distribution)
    instance.new_version = "Doesn't conform to semantic versioning"
    instance._validate_fields()
    assert not instance.new_version


def test_initialize_options(empty_distribution):
    '''
    Test that our attributes are added, as that is all we do in this override.
    '''
    # test the function
    instance = test_commands.DynamicVersioningEggInfo(empty_distribution)
    assert hasattr(instance, "new_version") and instance.new_version == None
    assert hasattr(instance, "version_bump") and instance.version_bump == None
    assert hasattr(instance, "dev_version") and instance.dev_version == False


@pytest.fixture
def neuter_config_funcs(monkeypatch):
    '''
    Monkeypatch DynamicVersioningEggInfo's _read_config(), _read_environment(),
    and _validate_fields(), as they are tested above.
    '''
    monkeypatch.setattr(test_commands.DynamicVersioningEggInfo, "_read_config", lambda self: None)
    monkeypatch.setattr(test_commands.DynamicVersioningEggInfo, "_read_environment", lambda self: None)
    monkeypatch.setattr(test_commands.DynamicVersioningEggInfo, "_validate_fields", lambda self: None)


def test_tagged_version_disabled(monkeypatch, caplog, empty_distribution, neuter_config_funcs):
    '''
    Test DynamicVersioningEggInfo's tagged_version() method when there are no
    values for our dynamic version fields.
    '''
    # patch the call to super tagged_version, no need to test their code
    monkeypatch.setattr(egg_info, "tagged_version", lambda self: "1.2.3")

    # test the function
    instance = test_commands.DynamicVersioningEggInfo(empty_distribution)
    assert "1.2.3" == instance.tagged_version()
    assert "Dynamic Versioning is disabled" in caplog.text


def test_new_version(monkeypatch, caplog, empty_distribution, neuter_config_funcs):
    '''
    Test DynamicVersioningEggInfo's tagged_version() method when the new_version
    field is set.
    '''
    # create the instance and set the new version value
    instance = test_commands.DynamicVersioningEggInfo(empty_distribution)
    instance.new_version = "1.2.3"

    # test the function
    assert "1.2.3" == instance.tagged_version()
    assert "Dynamic Versioning set to the new version '1.2.3'" in caplog.text


@pytest.fixture
def version_from_git(monkeypatch):
    '''
    A fixture that patches the call to utils.get_version_from_git() to return a
    canned DynamicVersion object.
    '''
    monkeypatch.setattr(utils, "get_version_from_git", lambda: utils.DynamicVersion(1, 2, 3, 20))


@pytest.mark.parametrize("dist_version,bump,final_version,log_output", [
    ("0.0.1", utils.VersionPart.UPDATE, "1.2.4", "Git tag version 'Update' portion bumped, resulting in new version '1.2.4'"),
    ("0.0.1", utils.VersionPart.PATCH, "1.2.4", "Git tag version 'Update' portion bumped, resulting in new version '1.2.4'"),
    ("0.0.1", utils.VersionPart.MINOR, "1.3.0", "Git tag version 'Minor' portion bumped, resulting in new version '1.3.0'"),
    ("0.0.1", utils.VersionPart.MAJOR, "2.0.0", "Git tag version 'Major' portion bumped, resulting in new version '2.0.0'"),
    ("1.3.0", utils.VersionPart.UPDATE, "1.3.0", "Version found in setup.py / pyproject.toml ('1.3.0') is greater than the bumped version ('1.2.4') of the last git tag. Selecting '1.3.0'"),
])
def test_bumped_version(monkeypatch, caplog, empty_distribution, neuter_config_funcs, version_from_git, dist_version, bump, final_version, log_output):
    '''
    Test DynamicVersioningEggInfo's tagged_version() method when the
    version_bump is set (but not dev_version).
    '''
    # patch the call to get the version from setup.py and/or pyproject.toml
    monkeypatch.setattr(DistributionMetadata, "get_version", lambda self: dist_version)

    # create the instance and set the version bump value
    instance = test_commands.DynamicVersioningEggInfo(empty_distribution)
    instance.version_bump = bump

    # test the function
    assert final_version == instance.tagged_version()
    assert log_output in caplog.text


@pytest.mark.parametrize("bump,final_version,log_output", [
    (None, "2.0.0.dev20", "Git tag version 'Major' portion bumped, resulting in development version '2.0.0.dev20'"),
    (utils.VersionPart.UPDATE, "1.2.4.dev20", "Git tag version 'Update' portion bumped, resulting in development version '1.2.4.dev20'"),
    (utils.VersionPart.PATCH, "1.2.4.dev20", "Git tag version 'Update' portion bumped, resulting in development version '1.2.4.dev20'"),
    (utils.VersionPart.MINOR, "1.3.0.dev20", "Git tag version 'Minor' portion bumped, resulting in development version '1.3.0.dev20'"),
    (utils.VersionPart.MAJOR, "2.0.0.dev20", "Git tag version 'Major' portion bumped, resulting in development version '2.0.0.dev20'"),
])
def test_dev_version(monkeypatch, caplog, empty_distribution, neuter_config_funcs, version_from_git, bump, final_version, log_output):
    '''
    Test DynamicVersioningEggInfo's tagged_version() method when the dev_version
    is set, both with and without the version_bump being set.
    '''
    # create the instance and set the version bump value
    instance = test_commands.DynamicVersioningEggInfo(empty_distribution)
    instance.version_bump = bump
    instance.dev_version = True

    # test the function
    assert final_version == instance.tagged_version()
    assert log_output in caplog.text
