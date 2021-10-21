'''
This modules is where we define the business logic of the dynamic versioning
options.
'''


# core libraries
import importlib.machinery
import importlib.util
import logging
import re
import subprocess

# configuration
from . import configuration


VERSIONING_OPTIONS = [
    ("new-version=", None, "The value to be used when setting the version of the distribution package"),
    ("version-bump=", None, "One of 'major', 'minor', or 'update', defining the portion of the current version (as "
        "established by the latest git tag) to increment when setting the version of the distribution package"),
    ("dev-version", None, "Version this distribution using a \"dev\" version (ex. 1.0.0.dev8 is 8 commits past the "
        "the most recent version, on the way to the 1.0.0 version)")
]
BOOLEAN_OPTIONS = [
    "dev-version"
]


## UTILITY FUNCTIONS

# error message when there are no annotated tags (common error)
_NO_ANNOTATED_TAGS_ERR = "No names found, cannot describe anything"

# regex used to parse the semantic version out of the git description
_SEMANTIC_VERSIONING_REGEX = r"^[v|V]?(\d+)\.(\d+)(?:\.(\d+))?\-(\d+)\-g\w{,7}$"

def git_describe():
    '''
    Use `git describe --long` to determine the most recent tag.
    '''
    logging.info("Determining the current version through git describe")
    command = ["git", "describe", "--long"]
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        out, err = proc.communicate()

    # exit if we had trouble running the git describe
    if err:
        if _NO_ANNOTATED_TAGS_ERR in err.decode().strip():
            logging.critical("No annotated tags! Please make sure there is at least one annotated tag for this " \
                             "repository.")
            raise SystemExit()

        logging.fatal(err.decode().strip())
        raise SystemExit()

    # parse the current version from the git describe output
    git_desc = out.decode().strip()
    try:
        version_match = re.search(_SEMANTIC_VERSIONING_REGEX, git_desc)
        version_list = list(map(lambda element: int(element) if element else 0, version_match.groups()))

    # AttributeError happens when we attempt to call groups on the None returned
    # when search doesn't find a match
    except AttributeError as err:
        logging.info("The most recent tag '%s' cannot be parsed. Please check that your current tag adheres to " \
                     "simple semantic versioning (major.minor[.patch]).", git_desc)
        raise SystemExit from err

    # check for all zeroes, as that is the only thing we don't support
    if all(num == 0 for num in version_list[:3]):
        logging.critical("The current tag evaluates to 0.0.0. Please check that your current tag adheres to simple " \
                         "semantic versioning (major.minor.[patch]).")
        raise SystemExit()

    logging.info("Current version: %d.%d.%d (with %d additional commits)", *version_list)
    return version_list


def bump_version(major, minor, patch, bump):
    '''
    Create a new version, bumping the correct portion.
    '''
    # bump must be one of 'major', 'minor', or 'patch'
    if bump.lower() not in ["major", "minor", "patch"]:
        logging.info("The value provided to --version-bump ('%s') is invalid. It must be one of: 'major', 'minor', " \
                     "or 'patch'.", bump)
        raise SystemExit()

    # triage the bump
    if bump.lower() == "major":
        return f"{major + 1}.0.0"

    if bump.lower() == "minor":
        return f"{major}.{minor + 1}.0"

    return f"{major}.{minor}.{patch + 1}"

def create_dev_version(major, commits):
    '''
    Create a development version using the provided major version and the number
    of development commits that have been made.
    '''
    # for now, this is as simple as bumping the major version and returning a
    # string formatted in the "dev" format
    return f"{major + 1}.0.0.dev{commits}"


def _read_version_file():
    '''
    Attempt to read the `version.py` file from the top level package.
    '''
    # check for a version file
    version_file = configuration.version_path()

    # load the file as a module
    logging.info("Attempting to open '%s' and read the current version.", version_file)
    loader = importlib.machinery.SourceFileLoader("version_module", version_file)
    spec = importlib.util.spec_from_loader("version_module", loader)
    version_module = importlib.util.module_from_spec(spec)

    # attempt to return the version within
    try:
        loader.exec_module(version_module)
        logging.info("Version file found. Using version '%s' found within.", version_module.__version__)
        return version_module.__version__
    except FileNotFoundError:
        logging.warning("Version file was not found at '%s'. Attempting to determine version another way.",
                        version_file)
    except AttributeError as err:
        logging.error(err)
        logging.warning("Version file was found at '%s', however it did not contain the variable __version__. " \
                        "Attempting to determine version another way.", version_file)

    return None


def write_version_file(version, package_name):
    '''
    Write (or overwrite) the version file with the given version, based on configuration.
    '''
    version_file = configuration.version_path()
    logging.info("Opening '%s' and writing out version %s", version_file, version)
    with open(version_file, "w", encoding="utf-8") as version_fd:
        version_fd.write(
            configuration.version_docstring().format(package_name=package_name) + f"__version__ = \"{version}\"\n"
        )


def default_versioning():
    '''
    This performs the default versioning action, cascading through a few
    scenarios given the current state of the code and repository.

    1. Search for a `version.py` file in the top level package, and if found,
       extract and use the version provided

    2. Create a development version, unless the current commit is also the
       current tag (0 commits since tag)

    3. Use the current tag
    '''
    # read the current version from the version file
    current_version = _read_version_file()
    if current_version is not None:
        return current_version

    # get the most recent tag and the number of commits since
    major, minor, patch, commits = git_describe()

    # if there has been development, create a dev version
    if commits > 0:
        return create_dev_version(major, commits)

    # otherwise, use the version of the current tag
    return f"{major}.{minor}.{patch}"
