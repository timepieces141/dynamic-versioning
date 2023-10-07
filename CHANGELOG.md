# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [1.1.0] - 2023-10-06

### Added

- Added a new `Command` called `DynamicVersioningEggInfo`, extending the `setuptools` `egg_info` `Command` class. Now, the only command class needed.
- New code linters, configurations for them, and an updated test script to call them (expecting a perfect score).

### Changed

- Refactor for PEP 517 (and related) - the last version was ... short-sighted. I did not really understand the length and breadth of what would be needed to properly hook the `setuptools` build process with the first two versions of this library, especially given the contents of PEP 517 (of which I was unaware).
- Instead of attempting to extend *all* of the setuptools `Command` classes, I now just extend the `egg_info` class, since that is where the version is decided, and all other commands further down the execution change take the value decided there. This means there is only *one* `Command` class to override in the `setup.py` file:
```
from setuptools import setup
import dynamic_versioning
...
setup(
	...
	cmdclass={"egg_info": dynamic_versioning.DynamicVersioningEggInfo}
	...
)
```
- To provide the "new version", "version bump", and/or "dev version" values to the system, the values can be defined in `dynamic_versioning.ini`, `pyproject.toml` (under the section `tool.dynamic_versioning`), or as environment variables. See documentation for more information.
- To conform to PEP 517, a build-backend needs to be declared. When running `python setup.py ...`, `setuptools` as the build-backend was obvious. But since direct calls to invoke `setup.py` is being deprecated itself in favor of `pip wheel .`, the build-backend must be declared in `pyproject.toml`. See documentation for more information.

### Deprecated

- The `configure()` function from the `dynamic_versioning.configuration` package is now deprecated. It was a required call to make in the `setup.py` file, but the configuration values provided are now all OBE because PEP 517 ensures `CWD` is the directory that holds `setup.py` and/or `pyproject.toml`.

### Removed

- Removed class extensions for `bdist_egg`, `build_py`, `install`, `sdist`, and `bdist_wheel` commands. See the [Changed](#changed) section for more detail.
- In addition to removing the unecessary extensions of distutils/setuptools `Command` classes, *our* new `Command` class `egg_info` does not create the additional `--new-version`, `--version-bump`, and `--dev-version` command line options the way those previous extensions did. See the [Changed](#changed) section for more detail.
- The presence of a `version.py` module in the top-level package no longer has any effect on the policy to determine the version dynamically.
- A `version.py` file is no longer created as a result of the version being dynamically determined. This feature may return in a future version if it can be added without issue. 

### Fixed

- This new approach should fix the recursion bug created in 1.0.1 when attempting to use `pip wheel .`


## [1.0.1] - 2023-08-07

### Added

- New code for discovering the `setup.py` file in the stack.
- Added block in `setup.py` in an attempt to start using dynamic-versioning ourselves - we'll see how that goes.
- Additional logging.
- New tests for the new functionality.
- Added Circle CI config to run the tests.
- Added Read the Docs documentation generation.

### Changed

- Refactor to use the `setuptools` `Command` extension classes instead of the `distutils` base classes - hopes this will future-proof us for a little while.
- Old code for discovering the `setup.py` file in the stack removed, as it was not working correctly after the `distutils` -> `setuptools` refactor.
- Upgraded to the latest version of `wheel`.
- Updated the `.pylintrc` file to the latest version, then reset some of our changes, given some configs were out of date.

## [1.0.0] - 2021-10-21

### Added

- Initial version.
