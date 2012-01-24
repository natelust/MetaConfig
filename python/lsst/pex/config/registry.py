from .config import Config

__all__ = ("ConfigRegistry", "makeConfigRegistry", "AlgorithmRegistry", "makeAlgorithmRegistry", "register")

# 
# LSST Data Management System
# Copyright 2008, 2009, 2010 LSST Corporation.
# 
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the LSST License Statement and 
# the GNU General Public License along with this program.  If not, 
# see <http://www.lsstcorp.org/LegalNotices/>.
#
class _BaseRegistry(object):
    """A registry that can be used in a RegistryField
    
    All registries must support two methods:
    - keys(): return all names
    - getConfigClass(name): return the Config class associated with the given name
    
    Subclasses must implement getConfigClass and may override _check.
    """
    def __init__(self):
        """Construct a registry of items
        """
        self._dict = dict()
    
    def keys(self):
        """Return a list of item names
        """
        return self._dict.keys()
    
    def get(self, name):
        """Get an item by name
        """
        return self._dict[name]
    
    def getConfigClass(self, name):
        """Get the config class for an item
        
        Subclasses must override
        """
        raise NotImplementedError()
    
    def add(self, name, item, isNew=True):
        """Register an item.
        
        @param name: name of item
        @param item: item to add
        @param isNew: is this a new item?
            - if True then adding a new item (the name must not exist)
            - if False then replacing an existing item (the name must exist)
        """
        if name.startswith("_"):
            raise RuntimeError("Name must not start with underscore")
        elif bool(isNew) == bool(name in self._dict):
            if isNew:
                raise RuntimeError("An item already exists with name %r" % (name,))
            else:
                raise RuntimeError("Could not find item %r to replace" % (name,))
        self._check(name, item)
        self._dict[name] = item
    
    def _check(self, name, item):
        """Raise an exception if the name or item is invalid
        """
        pass
    

class ConfigRegistry(_BaseRegistry):
    """A registry of configs (subclasses of pex_config Config)
    
    Each registry should make a subclass of AlgorithmRegistry with:
    - A doc string describing the API of the algorithms in the registry (if you simply set __doc__
      of the instantiated registry, the information does not appear in help(registry)).
    """
    def __init__(self, baseType=Config):
        """Construct a new ConfigRegistry
        
        @param baseType: all Configs in this registry must be an instance of baseType;
            baseType must itself be a subclass of Config
        """
        _BaseRegistry.__init__(self)
        self._baseType = baseType
        if not issubclass(self._baseType, Config):
            raise TypeError("baseType = %r; must be a subclass of Config" % (self._baseType,))

    def getConfigClass(self, name):
        return self.get(name)

    def _check(self, name, config):
        if not issubclass(config, self._baseType):
            raise TypeError("Config %r with name %r is not a subclass of %r" % (config, key, self._baseType))


def makeConfigRegistry(doc, baseType=Config):
    """Make a ConfigRegistry

    @param doc: doc string for registry
    @param baseType: Base class for Config classes in the registry.  Attempting to add
                     a class that is not a subclass of this class will raise TypeError.

    This creates a subclass of ConfigRegistryBase, installs a custom doc string,
    and returns an instance of the type.
    
    A convenience to save a bit of typing (simply intantiating a ConfigRegistry
    does not supply the proper doc string).
    """
    t = type("configRegistry", (ConfigRegistry,), {"__doc__": doc})
    return t(baseType)


class AlgorithmRegistry(_BaseRegistry):
    """A registry of algorithms, each of which has the same basic API
    
    Each registry should make a subclass of AlgorithmRegistry with:
    - A doc string describing the API of the algorithms in the registry (if you simply set __doc__
      of the instantiated registry, the information does not appear in help(registry)).
    - A suitable value for _requiredAttributes, if such checking is desired

    Every algorithm needs an attribute ConfigClass, which should be a subclass of pexConfig.Config
    """
    def __init__(self, requiredAttributes=()):
        """Construct an AlgorithmRegistry
        
        @param requiredAttributes: a list of required attribute names for each algorithm;
            these are checked in addition to ConfigClass
        """
        _BaseRegistry.__init__(self)
        self._requiredAttributes = ("ConfigClass",) + tuple(requiredAttributes)

    def getConfigClass(self, name):
        """Get an algorithm's config by name

        @raise KeyError if item is not found.
        """
        return self._dict[name].ConfigClass
    
    def _check(self, name, alg):
        for attrName in self._requiredAttributes:
            if not hasattr(alg, attrName):
                raise TypeError("Algorithm %r with name %r has no attribute %r" % (alg, name, attrName))


def makeAlgorithmRegistry(doc, requiredAttributes=()):
    """Make a AlgorithmRegistry

    @param doc: doc string for registry
    @param requiredAttributes: a tuple of attribute names required for each algorithm.

    This creates a subclass of AlgorithmRegistry, installs a custom doc string,
    and returns an instance of the type.
    
    A convenience to save a bit of typing (simply intantiating a AlgorithmRegistry
    does not supply the proper doc string).
    """
    t = type("algorithmRegistry", (AlgorithmRegistry,), {"__doc__": doc})
    return t(requiredAttributes=requiredAttributes)


def register(name, registry):
    """A parameterized decorator for items.  Use it like this:
    
    @register("foo", registry)
    class FooAstrometryConfig(Config):
        bar = Field("bar field for Foo algorithm", float)

    This will automatically do:

    registry["foo"] = FooAstrometryConfig
    """
    def decorate(cls):
        registry.add(name, cls)
        cls.name = name
        return cls
    return decorate
