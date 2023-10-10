'''
This modules is where we define the business logic of the dynamic versioning
options.
'''


# core libraries
import enum
import logging
import pathlib
import re
import subprocess
from functools import total_ordering
from typing import Type, TypeVar, cast


# error message when there are no annotated tags (common error)
_NO_ANNOTATED_TAGS_ERR = "No names found, cannot describe anything"

# regex used to parse the semantic version out of the git description
_SEMANTIC_VERSIONING_REGEX = r"^[v|V]?(\d+)\.(\d+)\.(\d+)$"
_GIT_DESCRIBE_VERSION_TAG_REGEX = r"^[v|V]?(\d+)\.(\d+)\.(\d+)\-(\d+)\-g\w{,7}$"


def validate_semantic_versioning(potential_version: str) -> bool:
    '''
    Validate the potential version as conforming to semantic versioning. Also
    that it does not represent 0.0.0.
    '''
    parts = parse_version_parts(potential_version)
    return not all(part == 0 for part in parts)


def parse_version_parts(potential_version: str) -> list[int]:
    '''
    Parse a potential semantic version string to a list of the major, minor, and
    patch (update) portions.
    '''
    try:
        version_match = cast(re.Match[str], re.search(_SEMANTIC_VERSIONING_REGEX, potential_version))
        return [int(element) for element in version_match.groups()]

    # AttributeError happens when we attempt to call groups on the None returned
    # when search doesn't find a match
    except AttributeError as err:
        logging.info("The potential version provided '%s' cannot be parsed as a semantic version.", potential_version)
        raise SystemExit from err


class VersionPart(enum.Enum):
    '''
    The parts of semantic versioning.
    '''
    MAJOR = 0
    MINOR = 1
    PATCH = 3
    UPDATE = 3


# forward reference
T = TypeVar("T", bound="DynamicVersion")

@total_ordering
class DynamicVersion:
    '''
    Encapsulation of a version.
    '''
    def __init__(self, major: int, minor: int, patch: int, commits: int=0):
        '''
        Construct the version from the three version parts.
        '''
        self.major = major
        self.minor = minor
        self.patch = patch
        self.commits = commits


    @classmethod
    def from_version_string(cls: Type[T], version_str: str) -> T:
        '''
        Construct a DynamicVersion object given a string that follows semantic
        versioning.
        '''
        return cls(*parse_version_parts(version_str))


    def bump(self, part: VersionPart) -> None:
        '''
        Bump the corresponding part of this version, cascading where necessary.
        '''
        if part == VersionPart.MAJOR:
            self.major += 1
            self.minor = 0
            self.patch = 0

        if part == VersionPart.MINOR:
            self.minor += 1
            self.patch = 0

        if part in [VersionPart.PATCH, VersionPart.UPDATE]:
            self.patch += 1


    def version_string(self) -> str:
        '''
        Provide the version as a string
        '''
        return f"{self.major}.{self.minor}.{self.patch}"


    def dev_version_string(self) -> str:
        '''
        Provide the development version as a string.
        '''
        return f"{self.major}.{self.minor}.{self.patch}.dev{self.commits}"


    def __lt__(self, other) -> bool:
        '''
        Check if this version is less than another version.
        '''
        if self.major < other.major:
            return True
        if self.major == other.major and self.minor < other.minor:
            return True
        if self.major == other.major and self.minor == other.minor and self.patch < other.patch:
            return True

        return False


    def __eq__(self, other) -> bool:
        '''
        Check if this version is equal to another.
        '''
        return (
            self.major == other.major and
            self.minor == other.minor and
            self.patch == other.patch
        )


def _git_fetch(project_dir: pathlib.Path) -> None:
    '''
    Perform a git fetch to pull down the latest tags.
    '''
    # perform a fetch first - make sure we don't miss any tags
    with subprocess.Popen(["git", "fetch"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=project_dir) as proc:
        _, err = proc.communicate()

    # exit if we had trouble running the git fetch
    if err:
        logging.fatal(err.decode().strip())
        raise SystemExit()


class DynamicVersioningError(Exception):
    '''
    Parent exception for all exceptions raised in Dynamic Versioning.
    '''


class NoAnnotatedTagError(DynamicVersioningError):
    '''
    Exception raised when `git describe` cannot find any candidate annotated
    tags from which to parse a version.
    '''


class GitDescribeError(DynamicVersioningError):
    '''
    Exception raised when `git describe` cannot be performed successfully.
    '''


def _git_describe(project_dir: pathlib.Path) -> str:
    '''
    Perform a git describe --long and return the output.
    '''
    # perform the git describe
    command = ["git", "describe", "--long"]
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=project_dir) as proc:
        out, err = proc.communicate()

    # check for errors, but catch a specific case
    if err:
        if _NO_ANNOTATED_TAGS_ERR in err.decode().strip():
            raise NoAnnotatedTagError()

        logging.fatal(err.decode().strip())
        raise GitDescribeError()

    # return the describe line as a string
    return out.decode().strip()


def get_version_from_git(fallback_current_version: str | None=None) -> DynamicVersion:
    '''
    Determine the version from the most recent annotated tag.
    '''
    # the current working directory will always be the project root
    project_dir = pathlib.Path.cwd()

    # git fetch to get the latest tags
    _git_fetch(project_dir)

    # git describe to get the most recent annotated tag
    logging.info("Determining the current version through 'git describe'")
    try:
        git_desc = _git_describe(project_dir)
    except NoAnnotatedTagError:
        logging.info("No annotated git tags could be found. Version 0.0.0 will be bumped accordingly.")
        return DynamicVersion(0, 0, 0)
    except GitDescribeError:
        # if current version has been statically defined, use that
        if fallback_current_version is not None:
            logging.warning("Encountered an error when attemting to find the most recent annotated git tag.")
            logging.info("However, a fallback current version has been defined. Version '%s' will be bumped " \
                         "accordingly.", fallback_current_version)
            return DynamicVersion.from_version_string(fallback_current_version)

    # parse the describe line
    try:
        version_match = cast(re.Match[str], re.search(_GIT_DESCRIBE_VERSION_TAG_REGEX, git_desc))
        version_list = [int(element) for element in version_match.groups()]

    ## TODO: Consider walking back through tags to the first one that matches a
    ## semantic version

    # AttributeError happens when we attempt to call groups on the None returned
    # when search doesn't find a match
    except AttributeError as err:
        logging.info("The most recent tag '%s' cannot be parsed. Please check that your current tag adheres to " \
                     "simple semantic versioning ([v|V]major.minor.patch).", git_desc)
        raise SystemExit from err

    # check for all zeroes, as we don't support a current tag of 0.0.0
    if all(num == 0 for num in version_list[:3]):
        logging.critical("The current tag evaluates to 0.0.0. Please check that your current tag adheres to simple " \
                         "semantic versioning ([v|V]major.minor.patch).")
        raise SystemExit()

    logging.info("Current version: %d.%d.%d (with %d additional commits)", *version_list)
    return DynamicVersion(*version_list)
