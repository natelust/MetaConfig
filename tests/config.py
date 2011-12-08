from lsst.pex.policy.Config import ConfigField, Config, Field
from lsst.pex.logging import DualLog, Log

class Inner (Config):
    f = Field(float, "Inner.f", default=0.0, check = lambda x: x >= 0)

class Outer(Config):
    i = ConfigField(Inner, "Outer.i", optional=False)         

class PluginConfig(Config):
    algA = ConfigField(Inner, "alg A policy")
    algB = ConfigField(Outer, "alg B policy")
    algChoice = ConfigField(str, "choice between algs A, B", default="A", check=lambda x: x =="A" or x == "B")

    def validate(self):
        Config.validate(self);
        if (self.algChoice == "A" and self.algA is None) or (self.algChoice == "B" and self.algB is None):
            raise ValueError("no policy provided for chosen algorithm " + self.algChoice)


def run():
    DualLog.createDefaultLog("test log", Log.DEBUG, Log.DEBUG);
    o = Outer()

    print o

    print o.i
    print o.i.f
    o.i.f=-5
    print o.i.f
    try:
        o.validate()
    except ValueError, e:
        print "Validation Failed.", e

    print o.i.f
    o.i.f=5
    try:
        o.validate()
    except ValueError, e:
        print "Validation Failed.", e

    print o.i.f

    o.i = Inner()
    print o.i
    try:
        o.validate()
    except ValueError, e:
        print "Validation Failed.", e

    conf = {"i.f":"3"};
    o.override(conf);
    o.validate()

    conf = {"i":{"f":4}}
    o.override(conf);
    o.validate()

    p = PluginConfig()
    try:
        p.validate()
    except ValueError, e:
        print "Validation Failed.", e

    p.algA = Inner()
    try:
        p.validate()
    except ValueError, e:
        print "Validation Failed.", e

    p = PluginConfig()

    p.override({"algB.i.f":4.0, "algChoice":"B"})
    try:
        p.validate()
    except ValueError, e:
        print "Validation Failed.", e

    print p
    print p.algA
    print p.algB
    print p.algB.i.f
    p.save("roundtrip.test")

    f = open("roundtrip.test", 'r')
    dict = eval(f.read())
    pc = PluginConfig(storage=dict)
    print pc


if __name__=='__main__':
    run()
