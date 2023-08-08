# Dynamic Versioning Utility for Setuptools

This utility provides additional options to classes defined in setuptools and used by setuptools to install and create packages.

## Functionality

This package provides three new options to some of the standard `setuptools` commands, such as `install`, `sdist`, etc.

### New Version

The first option is `--new-version`. This allows the caller to provide a version at the command line:

```bash
jgambolputty@dev-box:~$ python setup.py sdist --new-version 4.2.7
```

This will create a `version.py` file exporting the version in the top level package of the software [¹](#footnotes). And it will update the field populated by the `version` argument in the call to `setup()`. The field can be ommited or, to denote the dynamic nature that it will be filled, included and set to `None`:

```python
setup(
	name='Neat Tool',
	description='A neat new tool you won\'t want to miss',
	...
	version=None,
	...
)
```

### Version Bump

The second option is `--version-bump`. This allows the caller to provide one of `major`, `minor`, or `patch` and *that* portion of the semantic version will be "bumped." The current version is determined by checking for the latest annotated tag. It is assumed that tags will follow the semantic versioning format, with an optional prepended "V" (`[v|V]4.2.7`). If no tag is found, an error message will be shown and the process will end before any packaging is done.

__Note__: In future versions, if no annotated tag is found, version `0.0.1` will be assumed.

### Development Version

The last option provided is `--dev-version`. This allows the caller to denote the build as a development version. This will result in a version that adheres to the [PEP 440](https://www.python.org/dev/peps/pep-0440/#developmental-releases) section on development versioning. The number of commits since the lastest version is determined. Then, the *next* version is assumed to be the next major version (ex. `4.2.7` -> `5.0.0`). And finally, the development version is assembled. For instance, if there have been 12 commits since `4.2.7`, the development version would become `5.0.0.dev12`.

__Note: Future versions of this option may include `major`, `minor`, and `patch` modifiers to adjust the *assumed next version*.__ But for now, using `--new-version` is always powerful enough for any scenario not covered by the default behavior of either `--version-bump` or `--dev-version`.

### Default Behavior

If none of the options are provided, one of two things will happen. First, the system will search for a `version.py` file in the top-level package. If one has been found, and it contains the version value (using the standard `__version__ = "1.0.0"` format), that is the version that will be used. However, if no version can be determined in this manner, the system defaults to creating a development version. Further, if the system defaults to creating a development version, and there have been __*no commits*__ since the last annotated tag, the version dictated by the tag will be used. In this way, if the standard `python setup.py [command]` is used, a version already determined will be used, or a development version is assumed, and if there have been no development commits, then the current tag/version is used.

__Note__: If you use multiple setuptools commands at once, the new option should modify the *first* command. For example:

```bash
jgambolputty@dev-box:~$ python setup.py sdist --new-version 4.2.7 bdist_wheel
```
If the option is found later, the first command will trigger the default behavior and it may be too late to engage the dynamic version system.

## Assumptions Made

 - `git` is being used
 - tags are annotated, or at least the ones that provide version numbers are
 - the annoted tags follow (simple) semantic versioning (\[v|V\]\{major\}.\{minor\}\[\{patch\}\])

## Usage

To use these new flags, just import the `dynamic-versioning` library in your `setup.py` file. This package will need to be installed in the environment, so you can either install it computer-wide (never suggested), or you can include it in a "requirements" file and install it in your `venv`. I like to add it to the `testing-requirements.txt` file, since running the unit tests is what I usually do before pushing to the server. Generally knowing what version *might* be the next one seems like a good idea, even if it will be dynamically determined by a build server.

Just make a call to `configure()`, set your version to `None` (or omit the field), and override the command class(es) in the call to `setup()`:

```python
import dynamic_versioning

[other code]

# configure dynamic versioning
dynamic_versioning.configure()

[other code]

setup(
	name='Neat Tool',
	description='A neat new tool you won\'t want to miss',
	...
	cmdclass={
		"bdist_egg": dynamic_versioning.DynamicVersionBDist,
		"build_py": dynamic_versioning.DynamicVersionBuild,
		"install": dynamic_versioning.DynamicVersionInstall,
		"sdist": dynamic_versioning.DynamicVersionSDist,
		"sdist": dynamic_versioning.DynamicVersionSDist,
		"bdist_wheel": dynamic_versioning.DynamicVersionBDistWheel
	}
)
```

Now when those commands are used, the `dynamic-versioning` subclasses will be used instead and the new options will be available.

If you declare a logger in your `setup.py`, this library will log a few things along the way.

## Configuration

Certain assumptions are also made about the structure of your repository, such as the presence of a *single* top-level directory (nested under other directories, such as a `src` directory is ok) that houses an `__init__.py` file. If the directory from which you call `python setup.py [command]` does not have a predictable pathway to your top-level package, you will need to provide values to the `dynamic_versioning.configure()` function call. This could be if you have several directories, each with their own siloed code base. Also, the creation of the "version" file, its path (top-level package directory), and its name (`version.py`) are assumed. See the documentation for more information.

## Development and Testing

In case you want to develop against this code base, or just run the unit tests, here's how you do it:

1. Optionally (but suggested), create a virtual environment (I like `virtualenvwrapper`)
2. Install the testing requirements: `pip install -r testing-requirements.txt`
3. Install this package: `pip install -e .`
4. Run the tests: `tests/run_tests.sh`, optionally giving `-s -v[v...]` to enable logging and increase verbosity

## The Story Behind

In most places I have developed software, developers forget to update the version field in the `setup.py` file. And then one is faced with making a commit to SCM just to change it, and that commit doesn't represent a change in the *actual* code. In an environment which adopts the CI/CD attitude of: "every commit has the potential to be a release," that doesn't fly so well. Further, when the build server automatically publishes packages, the build process needs to determine the version (dynamically or manually) in order to publish.

Some project managers like to have a human-in-the-loop (usually themselves) and manually kick off the build that actually publishes the package. In this case, a build server configuration that allows providing parameters can be helpful. This package adds an option `--new-version` so a version can easily be provided, for instance from the build config parameters.

But in other cases, "versions" are cheap - especially when the packages are published to an *internal* artifact server so "plugin" developers, possibly from a different department, the customer, or even a partnered company, have access. But, because of the distinct API lines drawn between these players, "development" versions might be discouraged. The versions published are official, but are often-updated and a prime use of the "continuous" part of CI/CD. Either of `--version-bump` or `--dev-version` can help accomplish this in a dynamic way.

<br></br>
---
<a name="footnotes"></a>
<span style="color:blue">1</span>: Some software packages like to know their own version, and although you *can* grab that from `pkg_resources` or `importlib` metadata, having it locally can be simpler
