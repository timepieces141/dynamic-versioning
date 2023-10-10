'''
Common fixtures used in tests across multiple test modules.
'''


# core libraries
import os

# testing libraries
import pytest


@pytest.fixture(autouse=True)
def environment_variables():
    '''
    A fixture that captures the current environment, yields to the test where
    environment variables can be set without consequence, then restores the old
    environment when the test has finished.
    '''
    # capture the current environment as a dictionary
    current_environment = dict(os.environ)

    # run the test
    yield

    # replace the environment
    os.environ.clear()
    os.environ.update(current_environment)
