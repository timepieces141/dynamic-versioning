'''
Exports the distutil class extensions and the configuration function.
'''


# distutils extended classes
from .commands import (
    DynamicVersionBDist,
    DynamicVersionBuild,
    DynamicVersionInstall,
    DynamicVersionSDist,
    DynamicVersionBDistWheel,
)

# configuration
from .configuration import configure
