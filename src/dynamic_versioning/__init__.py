'''
Exports the distutil class extensions and the configuration function.
'''


# setuptools extended classes
from .commands import (
    DynamicVersionBDist,
    DynamicVersionBuild,
    DynamicVersionInstall,
    DynamicVersionSDist,
    DynamicVersionBDistWheel,
)

# configuration
from .configuration import configure
