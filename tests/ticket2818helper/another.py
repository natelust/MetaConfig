from ticket2818helper.define import TestConfig, TestConfigurable

class AnotherConfig(TestConfig):
    pass

class AnotherConfigurable(TestConfigurable):
    ConfigClass = AnotherConfig
