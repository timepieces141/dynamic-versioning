# Dynamic Versioning Utility for Setuptools

This utility provides the capability to dynamically determine the version of a python distribution package at build-time based on the current version (as determined by the most recent git tag) and a "version bumping" policy. It extends functionality in the `setuptools` library and as such requires it as the configured build-backend.

## Functionality

In order to properly hook `setuptools`, Dynamic Versioning needs both a `setup.py` file and a `pyproject.toml` file. Advocates of the use of `setup.py` tend to not want to use `pyproject.toml`, and vice versa. And most would prefer to not use both. However, `setuptools` does not provide a way in `pyproject.toml` to dictate "overrides" of `Command` classes, thus the override of `egg_info` must be defined in `setup.py`. A minimal `setup.py` could be:
```python
from setuptools import setup
import dynamic_versioning
setup(cmdclass={"egg_info": dynamic_versioning.DynamicVersioningEggInfo})
```
... and all other configuration values *could* be defined in `pyproject.toml`.

Meanwhile, PEP 517 front-ends, such as `pip` expect the build-backend to be defined in `pyproject.toml`, so to force the use of `setuptools` as the build-backend, a `pyproject.toml` file is also necessary. A minimal `pyproject.toml` file could be:
```ini
[build-system]
requires = ["setuptools", "dynamic-versioning"]
build-backend = "setuptools.build_meta"
```
... and all other configuration value *could* be defined in `setup.py`.

__Note: A Future version of Dynamic Versioning will provide a command line utility for generating these minimal configuration files.__ This may be helpful to initialize a new project.

## Configuration

The software provides *four* configuration values that define how it will dynamically determine the version at build-time. No change is needed to the command to build - both `python setup.py bdist_wheel|install|...` (soon to be deprecated by `setuptools`) and the more modern `pip wheel .` will trigger the version determination.

### New Version

The first configuration value is "new version" and can be set in one of three ways:

 - In a configuration file named `dynamic_versioning.ini`:
```ini
[dynamic_versioning]
new-version = 1.2.3
```
 - If `dynamic_versioning.ini` is not found, in `pyproject.toml`:
```ini
[tool.dynamic_versioning]
new-version = "1.2.3"
```
 - Or, in the environment variable `DV_NEW_VERSION`

If this configuration value is set, the version will be set to the value - simple as that. This overrides any version set in `setup.py` and/or `pyproject.toml`. If this configuration value is set, all other configuration values will be ignored.

### Version Bump

The second configuration value is "version bump" and is the heart of Dynamic Versioning. This configuration value can be set using `version-bump` in either `dynamic_versioning.ini` or `pyproject.toml`, or the environment variable `DV_VERSION_BUMP`. The value provided must be one of: `PATCH` (`UPDATE` is also accepted), `MINOR`, or `MAJOR` (using any case). When provided, Dynamic Versioning will grab the most recent *annotated* git tag and parse it as the *current* version. It is assumed that tags will follow [semantic versioning](http://semver.org/) format, with an optional prepended "V" (ex. `[v|V]4.2.7`). The portion of the current version designated by the value of "version bump" is then incremented by 1 ("bumped") and the lesser portions are zeroed out.

For example:

 - 1.2.3 bumped by PATCH (or UPDATE) -> 1.2.4
 - 1.2.3 bumped by MINOR -> 1.3.0
 - 1.2.3 bumped by MAJOR -> 2.0.0

If an annotated git tag is not available, the version will be set to `0.0.1` by default. Since the system depends on annotated git tags, it is expected that a tag will be created after an official version has been built and published. This default allows a "bootstrap" to that process. Of course, `new-version` can always be used to bootstrap the process at a different version.

### Current Version

The third configuration value is "current version" and can be set in the same three ways: `current-version` in either `dynamic_versioning.ini` or `pyproject.toml`, or the environment variable `DV_CURRENT_VERSION`. This value is used as a "fall-back" for when the version cannot be found by parsing the most recent annotated git tag. This is useful in circumstances when git *is not available* (or cannot be counted on *to be available*) on the system building the distribution package. This value is required when generating a source distribution, as the `.git` directory will almost certainly *not* be packed inside the source distribution.

### Development Version

The last configuration value provided is "dev version" and can be set in the same three ways: `dev-version` in either `dynamic_versioning.ini` or `pyproject.toml`, or the environment variable `DV_DEV_VERSION`. This allows the developers to denote the build as a development version. This will result in a version that adheres to the [PEP 440](https://www.python.org/dev/peps/pep-0440/#developmental-releases) section on development versioning. While determining the *current version* through the most recent git tag, the number of commits since that tag is also captured. The current version is then "bumped" using the value set by "version bump," defaulting to `MAJOR` when absent. The version is then assembled using the format `{major}.{minor}.{patch}.dev{commit_count}`. For instance, if there have been 12 commits since `4.2.7`, the development version could become: `5.0.0.dev12` (Major), `4.3.0.dev12` (Minor), or `4.2.8.dev12` (Patch).

## Assumptions Made

 - `git` is being used
 - tags are *__annotated__*, or at least the ones that provide version numbers are
 - the annoted tags follow (simple) semantic versioning (`[v|V]{major}.{minor}.{patch}`)

## Logging

A note about logging. If you use `python setup.py ...` (using `setuptools` as *both* a build-frontend and build-backend), and define a logger in your `setup.py` file, this library will log a few things along the way. However, if you use `pip wheel .`, `pip` silences all logging from the build-backend. That is, unless there is an error. `pip` is then quick to tell you it's not `pip`'s fault - check for the error in the build-backend or your build configuration. And when it is doing that, it will allow the logs from `setuptools` and Dynamic Versioning to be seen.

## Development and Testing

In case you want to develop against this code base, or just run the unit tests, here's how you do it:

1. Optionally (but suggested), create a virtual environment (I like `virtualenvwrapper`)
2. Run the tests: `tests/run_tests.sh`. This process will install the software, along with the testing dependencies, run several linters, and then the unit tests.

## The Story Behind

In most places I have developed software, developers forget to update the version field in the `setup.py` file. And then one is faced with making a commit to SCM just to change it, and that commit doesn't represent a change in the *actual* code. In an environment which adopts the CI/CD attitude of: "every commit has the potential to be a release," that doesn't fly so well. Further, when the build server automatically publishes packages, the build process needs to determine the version (dynamically or manually) in order to publish.

Some project managers like to have a human-in-the-loop (usually themselves) and manually kick off the build that actually publishes the package. In this case, a build server configuration that allows providing parameters can be helpful. This software adds a configuration ("new version") so a version can easily be provided, for instance from the build config parameters.

But in other cases, "versions" are cheap - especially when the distribution packages are published to an *internal* artifact server so "plugin" developers, possibly from a different department, the customer, or even a partnered company, have access. But, because of the distinct API lines drawn between these players, "development" versions might be discouraged. The versions published are *official*, but are often-updated and a prime use of the "continuous" part of CI/CD. Either of "version bump" or "dev version" can help accomplish this in a dynamic way.
