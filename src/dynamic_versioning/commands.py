'''
This module provides the extension to the distutils install command class.
'''


# core libraries
import logging

# third parties libraries
from distutils.command.bdist import bdist
from distutils.command.build import build
from distutils.command.install import install
from distutils.command.sdist import sdist
from wheel.bdist_wheel import bdist_wheel

# local libraries
from . import utils


# pylint: disable=no-member, attribute-defined-outside-init
class DynamicVersionBase:
    '''
    The base class that holds the overrides to distutils initialization and run
    methods.
    '''
    def initialize_options(self):
        '''
        Override of initialize_options that sets our three new fields. Here we
        dish off to the utiltity function.
        '''
        # call super - it should be there, but we make sure
        try:
            super_init_opts = getattr(super(), "initialize_options")
            if super_init_opts and callable(super_init_opts):
                super_init_opts()
        except AttributeError as err:
            logging.critical("Programming error - please report this bug!")
            raise SystemExit() from err

        # we have no choice but to define these here
        self.new_version = None
        self.version_bump = None
        self.dev_version = None

    def run(self):
        '''
        Overrides the run method so we can sneak in and set the
        `self.distribution.metadata.version` value, and where appropriate
        creating the version.py file, before the command is executed.
        '''
        # grab super.run(), since we are a mixin with technically no parent
        try:
            super_run = getattr(super(), "run")
        except AttributeError as err:
            logging.critical("Programming error - please report this bug!")
            raise SystemExit() from err

        # if none of the new options are given, perform the default action
        if all(opt is None for opt in [self.new_version, self.version_bump, self.dev_version]):
            self.distribution.metadata.version = utils.default_versioning()
            utils.write_version_file(self.distribution.metadata.version, self.distribution.metadata.name)
            super_run()
            return

        # if --new-version has been provided it takes precendence over other fields
        if self.new_version is not None:
            self.distribution.metadata.version = self.new_version
            utils.write_version_file(self.new_version, self.distribution.metadata.name)
            super_run()
            return

        # from here on out we need git describe values
        major, minor, patch, commits = utils.git_describe()

        # version bumping
        if self.version_bump is not None:
            self.distribution.metadata.version = utils.bump_version(major, minor, patch, self.version_bump)
            utils.write_version_file(self.distribution.metadata.version, self.distribution.metadata.name)
            super_run()
            return

        # development version
        if self.dev_version is not None:
            self.distribution.metadata.version = utils.create_dev_version(major, commits)
            utils.write_version_file(self.distribution.metadata.version, self.distribution.metadata.name)
            super_run()
            return

# pylint: enable=no-member, attribute-defined-outside-init


class DynamicVersionBDist(DynamicVersionBase, bdist):
    '''
    Custom "bdist" command subclass which accepts optional arguments.
    '''
    user_options = bdist.user_options + utils.VERSIONING_OPTIONS
    boolean_options = bdist.boolean_options + utils.BOOLEAN_OPTIONS


class DynamicVersionBuild(DynamicVersionBase, build):
    '''
    Custom "build" command subclass which accepts optional arguments.
    '''
    user_options = build.user_options + utils.VERSIONING_OPTIONS
    boolean_options = build.boolean_options + utils.BOOLEAN_OPTIONS


class DynamicVersionInstall(DynamicVersionBase, install):
    '''
    Custom "install" command subclass which accepts optional arguments.
    '''
    user_options = install.user_options + utils.VERSIONING_OPTIONS
    boolean_options = install.boolean_options + utils.BOOLEAN_OPTIONS


class DynamicVersionSDist(DynamicVersionBase, sdist):
    '''
    Custom "sdist" command subclass which accepts optional arguments.
    '''
    user_options = sdist.user_options + utils.VERSIONING_OPTIONS
    boolean_options = sdist.boolean_options + utils.BOOLEAN_OPTIONS


class DynamicVersionBDistWheel(DynamicVersionBase, bdist_wheel):
    '''
    Custom "bdist_wheel" command subclass which accepts optional arguments.
    '''
    user_options = bdist_wheel.user_options + utils.VERSIONING_OPTIONS
    boolean_options = bdist_wheel.boolean_options + utils.BOOLEAN_OPTIONS
