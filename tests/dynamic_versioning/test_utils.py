'''
Test the module dynamic_versioning.utils
'''


# core libraries
import pathlib
import subprocess
from collections import Counter

# testing libraries
import pytest

# dynamic versioning libraries
from dynamic_versioning import utils as test_utils


@pytest.mark.parametrize("parts,result", [
    ([0, 0, 0], False),
    ([1, 0, 0], True)
])
def test_validate_semantic_versioning(monkeypatch, parts, result):
    '''
    Test the validate_sematic_versioning() function, which just makes sure that
    the list version parts (successfully) returned by parse_version_parts() is
    not 0.0.0.
    '''
    # patch parse_version_parts() to return the given parts
    monkeypatch.setattr(test_utils, "parse_version_parts", lambda potential_version: parts)

    # test the function
    assert result == test_utils.validate_semantic_versioning("doesn't matter")


@pytest.mark.parametrize("potential_version,raise_error", [
    ("foobar", True),
    ("v1.2.3", False),
    ("V1.2.3", False),
    ("1.2.3", False)
])
def test_parse_version_parts(potential_version, raise_error):
    '''
    Test the parse_version_parts() function can parse strings representing
    semantic versions into a list of the three parts, or tries to System Exit if
    it cannot.
    '''
    # if the version would raise an error, catch it here with pytest
    if raise_error:
        with pytest.raises(SystemExit):
            test_utils.parse_version_parts(potential_version)

    # otherwise just test it
    else:
        Counter(sorted([1, 0, 0])) == test_utils.parse_version_parts(potential_version)


@pytest.mark.parametrize("parts,error", [
    ([], TypeError),
    ([1, 2, 3], None),
])
def test_dynamic_version_from_version_string(monkeypatch, parts, error):
    '''
    Test the DynamicVersion's from_version_string() method can construct the
    object via the version string setuptools parses from setup.py /
    pyproject.toml.
    '''
    # patch parse_version_parts() to return the given parts
    monkeypatch.setattr(test_utils, "parse_version_parts", lambda potential_version: parts)

    if error:
        with pytest.raises(error):
            test_utils.DynamicVersion.from_version_string("Doesn't matter")

    else:
        test_utils.DynamicVersion.from_version_string("Doesn't matter")


@pytest.mark.parametrize("version_bump,bumped_version_parts", [
    (test_utils.VersionPart.MAJOR, [2, 0, 0]),
    (test_utils.VersionPart.MINOR, [1, 1, 0]),
    (test_utils.VersionPart.UPDATE, [1, 0, 1]),
    (test_utils.VersionPart.PATCH, [1, 0, 1]),
])
def test_dynamic_version_bump(version_bump, bumped_version_parts):
    '''
    Test the DynamicVersion's bump() method produces the correct version.
    '''
    dynamic_version = test_utils.DynamicVersion(1, 0, 0)
    assert dynamic_version.major == 1
    assert dynamic_version.minor == 0
    assert dynamic_version.patch == 0
    dynamic_version.bump(version_bump)
    assert dynamic_version.major == bumped_version_parts[0]
    assert dynamic_version.minor == bumped_version_parts[1]
    assert dynamic_version.patch == bumped_version_parts[2]


@pytest.mark.parametrize("version_parts,version_string", [
    ([1, 0, 0], "1.0.0"),
    ([1, 1, 0], "1.1.0"),
    ([1, 1, 1], "1.1.1"),
])
def test_dynamic_version_version_string(version_parts, version_string):
    '''
    Test the DynamicVersion's version_string() method produces the correct
    version string.
    '''
    assert version_string == test_utils.DynamicVersion(*version_parts).version_string()


@pytest.mark.parametrize("version_parts,version_string", [
    ([1, 0, 0, 1], "1.0.0.dev1"),
    ([1, 1, 0, 2], "1.1.0.dev2"),
    ([1, 1, 1, 3], "1.1.1.dev3"),
])
def test_dynamic_version_dev_version_string(version_parts, version_string):
    '''
    Test the DynamicVersion's dev_version_string() method produces the correct
    version string.
    '''
    assert version_string == test_utils.DynamicVersion(*version_parts).dev_version_string()


@pytest.mark.parametrize("version1,version2,comparison", [
    (test_utils.DynamicVersion(1, 2, 4), test_utils.DynamicVersion(1, 2, 5), "<"),
    (test_utils.DynamicVersion(1, 2, 4), test_utils.DynamicVersion(1, 3, 0), "<"),
    (test_utils.DynamicVersion(1, 2, 4), test_utils.DynamicVersion(2, 0, 0), "<"),
    (test_utils.DynamicVersion(1, 2, 5), test_utils.DynamicVersion(1, 2, 4), ">"),
    (test_utils.DynamicVersion(1, 3, 0), test_utils.DynamicVersion(1, 2, 4), ">"),
    (test_utils.DynamicVersion(2, 0, 0), test_utils.DynamicVersion(1, 2, 4), ">"),
    (test_utils.DynamicVersion(1, 2, 4), test_utils.DynamicVersion(1, 2, 4), None),
])
def test_dynamic_version_comparison(version1, version2, comparison):
    '''
    Test that DynamicVersion objects can be compared for less than / greater
    than / equals.
    '''
    if comparison == "<":
        assert version1 < version2
    elif comparison == ">":
        assert version1 > version2
    else:
        assert version1 == version2


def test__git_fetch_error(monkeypatch, caplog):
    '''
    Test the _git_fetch() function when an error is returned by `git fetch`.
    '''
    # monkeypatch the Popen object's communicate method to produce our specific
    # error
    def mock_communicate(self, input=None, timeout=None):
        return (None, b'an error\n')
    monkeypatch.setattr(subprocess.Popen, "communicate", mock_communicate)

    # test the function, expecting an error
    with pytest.raises(SystemExit):
        test_utils._git_fetch(pathlib.Path.cwd())
    assert "an error" in caplog.text


@pytest.mark.parametrize("communicate_out_err,error", [
    ((None, b'fatal: No names found, cannot describe anything.\n'), test_utils.NoAnnotatedTagError),
    ((None, b'fatal: Some other error.\n'), SystemExit),
    ((b'1.0.1-0-g876ff07', None), None),
])
def test__git_describe(monkeypatch, communicate_out_err, error):
    '''
    Test the _git_describe() function returns the correct value or raises the
    correct exception, depending on the return of Popen's communicate().
    '''
    # monkeypatch the Popen object's communicate method to produce our specific
    # output and/or error
    def mock_communicate(self, input=None, timeout=None):
        return communicate_out_err
    monkeypatch.setattr(subprocess.Popen, "communicate", mock_communicate)

    # test the function when there is an error
    if error:
        with pytest.raises(error):
            test_utils._git_describe(pathlib.Path.cwd())

    # otherwise just test the function
    else:
        test_utils._git_describe(pathlib.Path.cwd())


def test_get_version_from_git_no_annotated_tags(monkeypatch, caplog):
    '''
    Test the get_version_from_git() function when no annotated tags were found
    from calling _git_describe().
    '''
    # patch _git_fetch and _git_describe to produce our error
    monkeypatch.setattr(test_utils, "_git_fetch", lambda project_dir: None)
    monkeypatch.setattr(test_utils, "_git_describe", lambda project_dir: (_ for _ in ()).throw(test_utils.NoAnnotatedTagError()))

    # test the function
    assert "0.0.0" == test_utils.get_version_from_git().version_string()
    assert "Determining the current version through 'git describe'" in caplog.text
    assert "No annotated git tags could be found. Version 0.0.0 will be bumped accordingly." in caplog.text


def test_get_version_from_git_current_version(monkeypatch, caplog):
    '''
    Test the get_version_from_git() function when _git_describe() returns a
    string not parseable with the REGEX, but a "fallback" current-version has
    been defined.
    '''
    # patch _git_fetch, then _git_describe to raise an error like when git is
    # not available
    monkeypatch.setattr(test_utils, "_git_fetch", lambda project_dir: None)
    monkeypatch.setattr(test_utils, "_git_describe", lambda project_dir: (_ for _ in ()).throw(SystemExit()))

    # test the function with a fallback current version
    assert "1.2.3" == test_utils.get_version_from_git("1.2.3").version_string()
    assert "Determining the current version through 'git describe'" in caplog.text
    assert "Encountered an error when attemting to find the most recent annotated git tag." in caplog.text
    assert "However, a fallback current version has been defined. Version '1.2.3' will be bumped accordingly." in caplog.text


def test_get_version_from_git_bad_git_describe(monkeypatch, caplog):
    '''
    Test the get_version_from_git() function when _git_describe() returns a
    string not parseable with the REGEX.
    '''
    # patch _git_fetch and _git_describe to produce our output
    monkeypatch.setattr(test_utils, "_git_fetch", lambda project_dir: None)
    monkeypatch.setattr(test_utils, "_git_describe", lambda project_dir: "This does not produce a version")

    # test the function expecting an error
    with pytest.raises(SystemExit):
        test_utils.get_version_from_git()
    assert "Determining the current version through 'git describe'" in caplog.text
    assert "The most recent tag 'This does not produce a version' cannot be parsed" in caplog.text


def test_get_version_from_git_zero_tag(monkeypatch, caplog):
    '''
    Test the get_version_from_git() function when _git_describe() returns a
    string that represents the version 0.0.0.
    '''
    # patch _git_fetch and _git_describe to produce our output
    monkeypatch.setattr(test_utils, "_git_fetch", lambda project_dir: None)
    monkeypatch.setattr(test_utils, "_git_describe", lambda project_dir: "0.0.0-20-g876ff07")

    # test the function expecting an error
    with pytest.raises(SystemExit):
        test_utils.get_version_from_git()
    assert "Determining the current version through 'git describe'" in caplog.text
    assert "The current tag evaluates to 0.0.0" in caplog.text


def test_get_version_from_git(monkeypatch, caplog):
    '''
    Test the get_version_from_git() function when _git_describe() returns a
    valid version.
    '''
    # patch _git_fetch and _git_describe to produce our output
    monkeypatch.setattr(test_utils, "_git_fetch", lambda project_dir: None)
    monkeypatch.setattr(test_utils, "_git_describe", lambda project_dir: "1.0.1-20-g876ff07")

    # test the function
    test_utils.get_version_from_git()
    assert "Determining the current version through 'git describe'" in caplog.text
    assert "Current version: 1.0.1 (with 20 additional commits)" in caplog.text

