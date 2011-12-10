from lsst.pex.policy import *
import os

class Inner (Config):
    f = Field(float, "Inner.f", default=0.0, check = lambda x: x >= 0)

class Outer(Config):
    i = ConfigField(Inner, "Outer.i", optional=False)         

class PluginConfig(Config):
    algA = ConfigField(Inner, "alg A policy")
    algB = ConfigField(Outer, "alg B policy")
    algChoice = Field(str, "choice between algs A, B", default="A", check=lambda x: x =="A" or x == "B")

    def validate(self):
        Config.validate(self);
        if (self.algChoice == "A" and self.algA is None) or (self.algChoice == "B" and self.algB is None):
            raise ValueError("no policy provided for chosen algorithm " + self.algChoice)

class ListConfig(Config):
    li = ListField(int, "list of ints", default = [1,2,3], optional=False, length=3, itemCheck=lambda x: x > 0)
    lc = ConfigListField(Inner, "list of inners", default = None, optional=True)

class ChoiceTest(Config):
    ci = ChoiceField(int, "choice of ints", {0:"can be zero", 9:"the special 9"}, default=0, optional=True)

def run():
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

    roundTrip = PluginConfig();
    roundTrip.load("roundtrip.test")
    #os.remove("roundtrip.test")
    print roundTrip

    listConfig = ListConfig()
    listConfig.validate()
    print listConfig
    listConfig.li[1]=5
    listConfig.lc = []
    listConfig.lc.append(Inner())
    print listConfig
    print listConfig.getHistory("li")

    choices = ChoiceTest(storage={"ci":3})
    print choices
    choices.validate()

    
if __name__=='__main__':
    run()
