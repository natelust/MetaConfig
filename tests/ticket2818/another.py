from ticket2818.define import TestConfig, TestConfigurable

class AnotherConfig(TestConfig):
    pass

class AnotherConfigurable(TestConfigurable):
    ConfigClass = AnotherConfig
