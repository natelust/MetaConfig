from .config import Config, Field, _joinNamePath, FieldValidationError
import traceback

__all__ = ("ConfigRegistry", "makeConfigRegistry", "AlgorithmRegistry", "makeAlgorithmRegistry", "register", "RegistryField")

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

class _TypeRegistry(object):
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
    
    def add(self, name, item, doReplace=False):
        """Register an item.
        
        @param name: name of item
        @param item: item to add
        @param isNew: is this a new item?
            - if True then adding a new item (the name must not exist)
            - if False then replacing an existing item (the name must exist)
        """
        if name.startswith("_"):
            raise RuntimeError("Name must not start with underscore")
        elif not doReplace and name in self._dict:
            raise RuntimeError("An item already exists with name %r" % (name,))

        self._check(name, item)
        self._dict[name] = item
    
    def _check(self, name, item):
        """Raise an exception if the name or item is invalid
        """
        pass

class ConfigRegistry(_TypeRegistry):
    """A registry of configs (subclasses of pex_config Config)
    
    Each registry should make a subclass of ConfigRegistry with:
    - A doc string describing the API of the algorithms in the registry (if you simply set __doc__
      of the instantiated registry, the information does not appear in help(registry)).
    """
    def __init__(self, baseType=Config):
        """Construct a new ConfigRegistry
        
        @param baseType: all Configs in this registry must be an instance of baseType;
            baseType must itself be a subclass of Config
        """
        _TypeRegistry.__init__(self)
        self._baseType = baseType
        if not issubclass(self._baseType, Config):
            raise TypeError("baseType = %r; must be a subclass of Config" % (self._baseType,))

    def getConfigClass(self, name):
        return self.get(name)

    def _check(self, name, config):
        if not issubclass(config, self._baseType):
            raise TypeError("Config %r with name %r is not a subclass of %r" % (config, name, self._baseType))


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


class AlgorithmRegistry(_TypeRegistry):
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
        _TypeRegistry.__init__(self)
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

class _Registry(dict):
    """A registry of instantiated configs
    
    Contains a typemap of config classes, e.g. ConfigRegistry or AlgorithmRegistry
    
    @typemap must be an instance of _TypeRegistry
    """
    def __init__(self, fullname, types, multi, history=None):
        dict.__init__(self)
        self._fullname = fullname
        self._selection = None
        self._multi=multi
        self.types = types
        self.history = [] if history is None else history

    def _setSelection(self,value):
        if value is None:
            self._selection=None
        elif self._multi:
            for v in value:
                if not v in self.types.keys(): 
                    raise KeyError("Unknown key %s in Registry %s"% (repr(v), self._fullname))
            self._selection=list(value)
        else:
            if value not in self.types.keys():
                raise KeyError("Unknown key %s in Registry %s"% (repr(value), self._fullname))
            self._selection=value
        self.history.append((value, traceback.extract_stack()[:-1]))
    
    def _getNames(self):
        if not self._multi:
            raise AttributeError("Single-selection Registry %s has no attribute 'names'"%self._fullname)
        return self._selection
    def _setNames(self, value):
        if not self._multi:
            raise AttributeError("Single-selection Registry %s has no attribute 'names'"%self._fullname)
        self._setSelection(value)
    def _delNames(self):
        if not self._multi:
            raise AttributeError("Single-selection Registry %s has no attribute 'names'"%self._fullname)
        self._selection = None
    
    def _getName(self):
        if self._multi:
            raise AttributeError("Multi-selection Registry %s has no attribute 'name'"%self._fullname)
        return self._selection
    def _setName(self, value):
        if self._multi:
            raise AttributeError("Multi-selection Registry %s has no attribute 'name'"%self._fullname)
        self._setSelection(value)
    def _delName(self):
        if self._multi:
            raise AttributeError("Multi-selection Registry %s has no attribute 'name'"%self._fullname)
        self._selection=None
   
    """
    In a multi-selection _Registry, list of names of active items
    Disabled In a single-selection _Regsitry)
    """
    names = property(_getNames, _setNames, _delNames)
   
    """
    In a single-selection _Registry, name of the active item
    Disabled In a multi-selection _Regsitry)
    """
    name = property(_getName, _setName, _delName)

    def _getActive(self):
        if self._selection is None:
            return None

        if self._multi:
            return [self[c] for c in self._selection]
        else:
            return self[self._selection]

    """
    Readonly shortcut to access the selected item(s) of the registry.
    for multi-selection _Regsitry, this is equivalent to: [self[name] for [name] in self.names]
    for single-selection _Regsitry, this is equivalent to: self[name]
    """
    active = property(_getActive)
    
    def __getitem__(self, k):
        try:
            dtype = self.types.getConfigClass(k)
        except:
            raise KeyError("Unknown key %s in Registry %s"%(repr(k), self._fullname))
        
        try:
            value = dict.__getitem__(self, k)
        except KeyError:
            value = dtype()
            value._rename(_joinNamePath(name=self._fullname, index=k))
            dict.__setitem__(self, k, value)
        return value

    def __setitem__(self, k, value):
        if k in self.__dict__:
            raise ValueError("Cannot register '%s'. Reserved name")
        
        name=_joinNamePath(name=self._fullname, index=k)
        oldValue = self[k]
        dtype = type(oldValue)
        if type(value) == dtype:
            for field in dtype._fields:
                setattr(oldValue, field, getattr(value, field))
        elif value == dtype:
            for field in dtype._fields.itervalues():
                setattr(oldValue, field.name, field.default)
        else:
            raise ValueError("Cannot set Registry item '%s' to '%s'. Expected type %s"%\
                    (str(name), str(value), dtype.__name__))


class RegistryField(Field):
    """
    Registry Fields allow the config to choose from a set of possible Config types.
    The set of allowable types is given by the typemap argument to the constructor

    The typemap object must implement getConfigClass(name), and keys()

    While the typemap is shared by all instances of the field, each instance of
    the field has its own instance of a particular sub-config type

    For example:

      class AaaConfig(Config):
        somefield = Field(int, "...")
      REGISTRY = {"A", AaaConfig}
      class MyConfig(Config):
        registry = RegistryField("doc for registry", REGISTRY)
      
      instance = MyConfig()
      instance.registry['AAA'].somefield = 5
      instance.registry = "AAA"
    
    Alternatively, the last line can be written:
      instance.registry.name = "AAA"

    Validation of this field is performed only the "active" selection.
    If active is None and the field is not optional, validation will fail. 
    
    Registries can allow single selections or multiple selections.
    Single selection registries set that selection through property name, and 
    multi-selection registries use the property names. 

    Registries also allow multiple values of the same type:
      instance.registry["CCC"]=AaaConfig
      instance.registry["BBB"]=AaaConfig

    When saving a registry, the entire set is saved, as well as the active selection
    """
    def __init__(self, doc, typemap, default=None, optional=False, multi=False):
        Field._setup(self, doc, _Registry, default=default, check=None, optional=optional)
        if not isinstance(typemap, _TypeRegistry):
            raise TypeError("typemap must be an instance of lsst.pex.config._TypeRegistry")
        self.typemap = typemap
        self.multi=multi
    
    def _getOrMake(self, instance):
        registry = instance._storage.get(self.name)
        if registry is None:
            name = _joinNamePath(instance._name, self.name)
            history = []
            instance._history[self.name] = history
            registry = _Registry(name, self.typemap, self.multi, history)
            registry.__doc__ = self.doc
            instance._storage[self.name] = registry
        return registry


    def __get__(self, instance, owner=None):
        if instance is None or not isinstance(instance, Config):
            return self
        else:
            return self._getOrMake(instance)

    def __set__(self, instance, value):
        registry = self.__get__(instance)
        registry._setSelection(value)


    def rename(self, instance):
        registry = self.__get__(instance)
        for k, v in registry.iteritems():
            fullname = _joinNamePath(instance._name, self.name, k)
            v._rename(fullname)

    def validate(self, instance):
        registry = self.__get__(instance)
        if not registry.active and not self.optional:
            fullname = _joinNamePath(instance._name, self.name)
            fieldType = type(self).__name__
            msg = "Required field cannot be None"
            raise FieldValidationError(fieldType, fullname, msg)
        elif registry.active:
            if self.multi:
                for a in registry.active:
                    a.validate()
            else:
                registry.active.validate()

    def toDict(self, instance):
        registry = self.__get__(instance)

        dict_ = {}
        if self.multi:
            dict_["names"]=registry.names
        else:
            dict_["name"] =registry.name

        for k, v in registry.iteritems():
            dict_[k]=v.toDict()
        
        return dict_

    def save(self, outfile, instance):
        registry = self.__get__(instance)
        fullname = registry._fullname
        for v in registry.itervalues():
            v._save(outfile)
        if self.multi:
            outfile.write("%s.names=%s\n"%(fullname, repr(registry.names)))
        else:
            outfile.write("%s.name=%s\n"%(fullname, repr(registry.name)))

