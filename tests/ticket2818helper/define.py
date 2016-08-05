from builtins import object
from lsst.pex.config import Config, ConfigurableField


class TestConfig(Config):
    pass


class TestConfigurable(object):
    ConfigClass = TestConfig

    def __init__(self, config):
        self.config = config

    def what(self):
        return self.__class__.__name__


class BaseConfig(Config):
    test = ConfigurableField(target=TestConfigurable, doc="")
