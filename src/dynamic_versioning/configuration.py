'''
This module provides utility functions for dealing with loading values from an
INI file (falling back to pyproject.toml).
'''


# core libraries
import configparser
import logging
import os
import pathlib
from typing import Any, Dict

# third party libraries
import toml
from deprecated import deprecated


def _find_config_file(project_dir: pathlib.Path) -> pathlib.Path | None:
    '''
    Search the tree starting at the current working directory for a file called
    dynamic_versioning.ini.
    '''
    for root, _, files in os.walk(project_dir):
        for file in files:
            if file.lower() == "dynamic_versioning.ini":
                return pathlib.Path(root) / file

    # not found
    return None


def load_config() -> Dict[str, Any] | None:
    '''
    Attempt to find a file called dynamic_versioning.ini in the current tree and
    load the configuration. If not found, attempt to load configuration values
    from the pyproject toml file.
    '''
    # search from the project dir
    project_dir = pathlib.Path.cwd()

    # search for a config file
    if dv_config := _find_config_file(project_dir):
        config = configparser.ConfigParser()
        config.read(dv_config)
        config_dict = {}
        for section in config.sections():
            if section == "dynamic_versioning":
                for key, value in config.items(section):
                    config_dict[key] = value
        return config_dict

    # load the pyproject.toml file
    pyproject_toml = project_dir / "pyproject.toml"
    if pyproject_toml.exists():
        project_dict = toml.load(pyproject_toml)
        if dv_section := project_dict.get("tool", {}).get("dynamic_versioning", {}):
            return dv_section

    # no configuration
    return None


# pylint: disable=unused-argument
@deprecated(version="1.1.0",
            reason="All configuration can be provided in dynamic_versioning.ini, pyproject.toml, and/or in the " \
                   "environment")
def configure(top_level_pkg=None,
              version_file_name=None,
              version_docstring_format=None) -> None:
    '''
    Accept the configuration values and set the global variables used to create
    the version file.
    '''
    logging.warning("Dynamic Versioning no longer needs the configure function. Please see documentation on how to " \
                    "use environment variables and/or and INI file (including pyproject.toml) for configuration.")

# pylint: enable=unused-argument
