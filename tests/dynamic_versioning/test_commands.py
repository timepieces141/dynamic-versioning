'''
Test the module dynamic_versioning.commands
'''


# third parties libraries
from distutils.cmd import Command

# testing libraries
import pytest

# local libraries
from dynamic_versioning import utils

# module under test
from dynamic_versioning import commands


@pytest.fixture
def neuter_command(monkeypatch):
    '''
    In this fixture we monkey patch Command's __init__, initialize_options, and
    run methods, as we call them in the code, but we don't need to test those
    here.
    '''
    monkeypatch.setattr(Command, "__init__", lambda self, dist: None)
    monkeypatch.setattr(Command, "initialize_options", lambda self: None)
    monkeypatch.setattr(Command, "run", lambda self: None)


def test_no_super(caplog):
    '''
    We should really never get this, as we use the mixin properly, but here we
    test that if for some reason we made that mistake, we would at least be
    notified.
    '''
    with pytest.raises(SystemExit):
        instance = commands.DynamicVersionBase()
        instance.initialize_options()
        assert "Programming error - please report this bug!" in caplog.text

    with pytest.raises(SystemExit):
        instance = commands.DynamicVersionBase()
        instance.run()
        assert "Programming error - please report this bug!" in caplog.text


@pytest.mark.parametrize("test_cls", [
    (commands.DynamicVersionBDist),
    (commands.DynamicVersionBuild),
    (commands.DynamicVersionInstall),
    (commands.DynamicVersionSDist),
    (commands.DynamicVersionBDistWheel),
])
def test_initialize_options(neuter_command, test_cls):
    '''
    Test that our attributes are added, as that is all we do in this override.
    '''
    # test the function
    instance = test_cls(None)
    instance.initialize_options()
    assert hasattr(instance, "new_version") and instance.new_version == None
    assert hasattr(instance, "version_bump") and instance.version_bump == None
    assert hasattr(instance, "dev_version") and instance.dev_version == None


@pytest.fixture
def dummy_command():
    '''
    Here we create a dummy command to act as the mixin's base, so we can avoid
    the pitfalls of trying to patch our specific way of seaking out the super
    class and its run method.
    '''
    class DummyCommand:
        def __init__(self):
            metadata = type('',(object,),{"version": None, "name": None})()
            self.distribution = type('',(object,),{"metadata": metadata})()
        def initialize_options(self):
            pass
        def run(self):
            pass

    class Mixed(commands.DynamicVersionBase, DummyCommand):
        pass

    return Mixed()

@pytest.mark.parametrize("new_version,version_bump,dev_version,default_return,git_describe_return,bump_version_return,dev_version_return,expected", [
    (None, None, None, "default", None, None, None, "default"),
    ("new-version", None, None, None, None, None, None, "new-version"),
    (None, "MAJOR", None, None, [1, 2, 3, 8], "2.0.0", None, "2.0.0"),
    (None, None, True, None, [1, 2, 3, 8], None, "2.0.0.dev8", "2.0.0.dev8"),
])
def test_run_triage(monkeypatch, dummy_command, new_version, version_bump, dev_version, default_return, git_describe_return, bump_version_return, dev_version_return, expected):
    '''
    Test the run method triage logic. We've tested the calls out to utils
    elsewhere, so here we just test that our the inputs provided hit the
    correct triage point.
    '''
    # patch all our calls to utils
    monkeypatch.setattr(utils, "write_version_file", lambda version, package_name: None)
    monkeypatch.setattr(utils, "default_versioning", lambda: default_return)
    monkeypatch.setattr(utils, "git_describe", lambda: git_describe_return)
    monkeypatch.setattr(utils, "bump_version", lambda major, minor, patch, bump: bump_version_return)
    monkeypatch.setattr(utils, "create_dev_version", lambda major, commits: dev_version_return)

    # set up the instance
    dummy_command.initialize_options()
    dummy_command.new_version = new_version
    dummy_command.version_bump = version_bump
    dummy_command.dev_version = dev_version

    # test the function
    dummy_command.run()
    assert dummy_command.distribution.metadata.version == expected
