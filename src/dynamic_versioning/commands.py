'''
This module provides the extension to the setuptools egg_info class/command.
'''


# core libraries
import logging
import os

# third party libraries
from setuptools import _normalization  # type: ignore
from setuptools.command.egg_info import egg_info

# local libraries
from . import configuration, utils


# pylint: disable=attribute-defined-outside-init
class DynamicVersioningEggInfo(egg_info):
    '''
    An extention of the egg_info Command class that gives the user the ability
    to dynamically determine the version via a defined cascading policy.
    '''

    def _read_config(self) -> None:
        '''
        Load possible config files and load those values into instance fields.
        '''
        if config := configuration.load_config():
            if "new-version" in config:
                self.new_version: str | None = config["new-version"]
            if "current-version" in config:
                self.current_version: str | None = config["current-version"]
            if "version-bump" in config:
                self.version_bump: utils.VersionPart | None = utils.VersionPart[config["version-bump"].upper()]
            if "dev-version" in config:
                self.dev_version: bool = config["dev-version"].lower() in ("true", "t")


    def _read_environment(self) -> None:
        '''
        Check the environment for our environment variables and load those
        values into instance fields.
        '''
        if new_version := os.environ.get("DV_NEW_VERSION", None):
            self.new_version = new_version
        if current_version := os.environ.get("DV_CURRENT_VERSION", None):
            self.current_version = current_version
        if version_bump := os.environ.get("DV_VERSION_BUMP", None):
            self.version_bump = utils.VersionPart[version_bump.upper()]
        if dev_version := os.environ.get("DV_DEV_VERSION", ""):
            self.dev_version = dev_version.lower() in ("true", "t")


    def _validate_fields(self) -> None:
        '''
        Validate the final values that have landed in our instance fields.
        '''
        # if new version exists, validate it as a semantic version (not 0.0.0)
        if self.new_version:
            if not utils.validate_semantic_versioning(self.new_version):
                self.new_version = None

        # if current version exists, validate it as a semantic version (not 0.0.0)
        if self.current_version:
            if not utils.validate_semantic_versioning(self.current_version):
                self.current_version = None


    def initialize_options(self) -> None:
        '''
        Override of initialize_options function to initialize the fields used to
        determine the version dynamically.
        '''
        # call super, then add our fields
        super().initialize_options()
        self.new_version = None
        self.current_version = None
        self.version_bump = None
        self.dev_version = False


    def tagged_version(self) -> str:
        '''
        Override of the function that determines the version of the software.
        Here we grab the value returned by the normal means, then use our
        cascading policy to augment or accept that version.

        1. If none of our values were provided through config or env, just call
           super.
        2. new-version is used above all, as long as it meets the semantic
           versioning regex and is not 0.0.0.
        3. Attempt a version bump of the portion defined in version-bump. This
           entails getting the current version from git via the most recent tag,
           then bumping. The higher of that or the version found in setup,py /
           pyproject.toml (through the distribution object) wins.
        3a. If the current version cannot be determined because no annotated git
           tag exists (call to git was successful, but there were no tags), then
           the version is assumed to be 0.0.0 and will be bumped accordingly.
        3b. If the current version cannot be determined because the call to git
           failed, then the statically defined current-version will be used,
           where possible, and will be bumped accordingly.
        4. Create a dev version, which bumps to the next version (as dictated by
           version_bump, defaults to MAJOR) and appends .dev and the number of
           commits since the last version.

        '''
        # load config, then environment
        self._read_config()
        self._read_environment()
        self._validate_fields()

        # if we're not being used, just pass through
        if all(member is None for member in [self.new_version, self.version_bump]) and not self.dev_version:
            logging.info("Dynamic Versioning is disabled")
            return super().tagged_version()

        # if new_version exists, we use that
        if self.new_version:

            # call the same methods setuptools tagged_version calls, but with
            # our version instead of the one parsed from the version field of
            # setup.py or pyproject.toml
            logging.info("Dynamic Versioning set to the new version '%s'", self.new_version)
            tagged = self._maybe_tag(self.new_version) # type: ignore
            return _normalization.best_effort_version(tagged)

        # retrieve the current version via git tag
        dynamic_version = utils.get_version_from_git(self.current_version)

        # if we're bumping, bump and compare
        if self.version_bump and not self.dev_version:

            # get the version as parsed by setuptools
            st_version = utils.DynamicVersion.from_version_string(
                self._maybe_tag(self.distribution.metadata.get_version())) # type: ignore

            # bump our version
            dynamic_version.bump(self.version_bump)

            # return the highest value - this covers bumping to next minor or
            # major just by setting it setup,py or pyproject.toml
            if st_version > dynamic_version:
                logging.info("Version found in setup.py / pyproject.toml ('%s') is greater than the bumped version " \
                             "('%s') of the last git tag. Selecting '%s'",
                             st_version.version_string(), dynamic_version.version_string(), st_version.version_string())
                return _normalization.best_effort_version(st_version.version_string())

            logging.info("Git tag version '%s' portion bumped, resulting in new version '%s'",
                         self.version_bump.name.title(), dynamic_version.version_string())
            return _normalization.best_effort_version(dynamic_version.version_string())

        # we're doing a dev version, so bump our version according to
        # version_bump, default to the next major version
        dynamic_version.bump(self.version_bump or utils.VersionPart.MAJOR)

        # run it through setuptools
        logging.info("Git tag version '%s' portion bumped, resulting in development version '%s'",
                     self.version_bump.name.title() if self.version_bump else "Major",
                     dynamic_version.dev_version_string())
        tagged = self._maybe_tag(dynamic_version.dev_version_string()) # type: ignore
        return _normalization.best_effort_version(tagged)

# pylint: enable=attribute-defined-outside-init
