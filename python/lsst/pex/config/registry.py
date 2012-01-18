from .config import Config

__all__ = ("makeConfigRegistry", "register")

class ConfigRegistryBase(dict):
    """A dictionary used to map names to Config classes, used as the backend for a RegistryField.
    
    ConfigRegistryBase adds to dict:
     - a check that all keys are strings and all values are subclasses of some class
       (which may just be Config),
     - (optionally) an additional user-defined check, given as a callable that returns
       False for invalid items.

    A ConfigRegistryBase should not be instantiated directly, as this does not allow use to add
    a per-instance docstring.  Instead, use the makeConfigRegistry function to easily create
    a subclass of ConfigRegistryBase with a custom docstring:

    registry = makeConfigRegistry(doc, basetype, check)

    """

    def __new__(cls, basetype=Config, check=None):
        self = dict.__new__(cls)
        if not issubclass(basetype, Config):
            raise TypeError("Base type for registries must be a subclass of Config.")
        self.basetype = basetype
        self.check = None
        return self

    def __init__(self, *args, **kwds):
        dict.__init__(self)

    def __setitem__(self, key, value):
        if not isinstance(key, basestring):
            raise TypeError("Registry key '%r' is not a string." % key)
        if not issubclass(value, self.basetype):
            raise TypeError("Registry item '%r' with name '%s' is not a subclass of '%r'."
                            % (value, key, self.basetype))
        if self.check is not None and not self.check(value):
            raise TypeError("Registry item '%s' with name '%s' does not meet check requirements for registry."
                            % (value, key))
        dict.__setitem__(self, key, value)

    def setitem(self, key, value):
        try:
            return self[key]
        except KeyError:
            self[key] = value
            return value

    def update(self, *args, **kwds):
        tmp = dict(*args, **kwds)
        for k, v in tmp.iteritems():
            self[k] = v

def makeConfigRegistry(doc, basetype=Config, check=None):
    """Make a custom dictionary used to map names to Config types.

    Arguments:
      basetype ------ Base class for Config classes in the registry.  Attempting to add
                      a class that is not a subclass of this class will raise TypeError.
      check --------- A single-argument callable that returns True if a given Config
                      class can be added to the registry, and False otherwise.  Ignored
                      if set to None (the default).

    This creates a anonymous subclass of ConfigRegistryBase, installs a custom doc string,
    and returns an instance of the anonymous type.  The type is anonymous because this the
    registry should be a singleton; there should be no need to ever make another instance
    of the same type.
    """
    t = type("ConfigRegistry", (ConfigRegistryBase,), {"__doc__": doc})
    return t(basetype, check)

def register(name, registry):
    """A parameterized decorator for subconfigs.  Use it like this:
    
    @register("FOO", registry)
    class FooAstrometryConfig(Config):
        bar = Field("bar field for Foo algorithm", float)

    This will automatically do:

    registry["FOO"] = FooAstrometryConfig
    """
    def decorate(cls):
        registry[name] = cls
        cls.name = name
        return cls
    return decorate
