import traceback
import copy
import sys

__all__ = ["Config", "Field", "RangeField", "ChoiceField", "ListField", "ConfigField", "Registry", "RegistryField"]

def _joinNamePath(prefix=None, name=None, index=None):
    """
    Utility function for generating nested configuration names
    """
    if not prefix and not name:
        raise ValueError("invalid name. cannot be None")
    elif not name:
        name = prefix
    elif prefix and name:
        name = prefix + "." + name

    if index is not None:
        return "%s[%s]"%(name, repr(index))
    else:
        return name

def _typeString(aType):
    """
    Utility function for generating type strings.
    Used internally for saving Config to file
    """
    if aType is None:
        return None
    else:
        return aType.__module__+"."+aType.__name__

class Registry(dict):
    def __init__(self, fullname, typemap, multi, history=None):
        dict.__init__(self)
        self._fullname = fullname
        self._selection = None
        self._multi=multi
        self.types = typemap
        self.history = [] if history is None else history

    def _setSelection(self,value):
        if value is None:
            self._selection=None
        elif self._multi:
            for v in value:
                if not v in self.types: 
                    raise KeyError("Unknown key %s in Registry %s"% (repr(v), self._fullname))
            self._selection=list(value)
        else:
            if value not in self.types:
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
        
    names = property(_getNames, _setNames, _delNames)
    name = property(_getName, _setName, _delName)

    def _getActive(self):
        if self._selection is None:
            return None

        if self._multi:
            return [self[c] for c in self._selection]
        else:
            return self[self._selection]

    active = property(_getActive)
    
    def __getitem__(self, k):
        try:
            dtype = self.types[k]
        except:
            raise KeyError("Unknown key %s in Registry '%s'"%(repr(k), self._fullname))
        
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
        
        #determine type
        name=_joinNamePath(name=self._fullname, index=k)
        oldValue = self[k]
        dtype = self.types[k]
        if type(value) == dtype:
            for field in dtype._fields:
                setattr(oldValue, field, getattr(value, field))
        elif value == dtype:
            for field in dtype._fields.itervalues():
                setattr(oldValue, field.name, field.default)
        else:
            raise ValueError("Cannot set Registry item '%s' to '%s'"%(name, str(value)))

class ConfigMeta(type):
    """A metaclass for Config

    Adds a dictionary containing all Field class attributes
    as a class attribute called '_fields', and adds the name of each field as 
    an instance variable of the field itself (so you don't have to pass the 
    name of the field to the field constructor).

    """

    def __init__(self, name, bases, dict_):
        type.__init__(self, name, bases, dict_)
        self._fields = {}
        for b in bases:
            dict_ = dict(dict_.items() + b.__dict__.items())
        for k, v in dict_.iteritems():
            if isinstance(v, Field):
                v.name = k
                self._fields[k] = v

    def __setattr__(self, name, value):
        if isinstance(value, Field):
            value.name = name
            self._fields[name] = value
        type.__setattr__(self, name, value)

class FieldValidationError(ValueError):
    def __init__(self, fieldtype, fullname, msg):
        error="%s '%s' failed validation: %s" % (fieldtype, fullname, msg)
        ValueError.__init__(self, error)

class Field(object):
    """A field in a a Config.

    Instances of Field should be class attributes of Config subclasses:
    Field only supports basic data types (int, float, bool, str)

    class Example(Config):
        myInt = Field(int, "an integer field!", default=0)
    """
    supportedTypes=[str, bool, float, int]

    def __init__(self, doc, dtype, default=None, check=None, optional=False):
        """Initialize a Field.
        
        dtype ------ Data type for the field.  
        doc -------- Documentation for the field.
        default ---- A default value for the field.
        check ------ A callable to be called with the field value that returns 
                     False if the value is invalid.  More complex inter-field 
                     validation can be written as part of Config validate() 
                     method; this will be ignored if set to None.
        optional --- When False, Config validate() will fail if value is None
        """
        if dtype not in self.supportedTypes:
            raise ValueError("Unsuported Field dtype '%s'"%dtype.__name__)
        self._setup(doc, dtype, default, check, optional)


    def _setup(self, doc, dtype, default, check, optional):
        self.dtype = dtype
        self.doc = doc
        self.__doc__ = doc
        self.default = default
        self.check = check
        self.optional = optional

    def rename(self, instance):
        """
        Rename an instance of this field, not the field itself. 
        Only useful for fields which hold sub-configs.
        Fields which hold subconfigs should rename each sub-config with
        the full field name as generated by _joinNamePath
        """
        pass

    def validate(self, instance):
        """
        Base validation for any field.
        Ensures that non-optional fields are not None.
        Ensures type correctness
        Ensures that user-provided check function is valid
        Most derived Field types should call Field.validate if they choose
        to re-implement validate
        """
        value = self.__get__(instance)
        fullname = _joinNamePath(instance._name, self.name)
        fieldType = type(self).__name__
        if not self.optional and value is None:
            msg = "Required value cannot be None"
            raise FieldValidationError(fieldType, fullname, msg)
        if value is not None and not isinstance(value, self.dtype):
            msg = " Expected type '%s', got '%s'"%(self.dtype, type(value))
            raise FieldValidationError(fieldType, fullname, msg)
        if self.check is not None and not self.check(value):
            msg = "%s is not a valid value"%str(value)
            raise FieldValidationError(fieldType, fullname, msg)

    def save(self, outfile, instance):
        """
        Saves an instance of this field to file.
        This is invoked by the owning config object, and should not be called
        directly
        """
        value = self.__get__(instance)
        fullname = _joinNamePath(instance._name, self.name)
        outfile.write("%s=%s\n"%(fullname, repr(value)))
    
    def toDict(self, instance):
        return self.__get__(instance)

    def __get__(self, instance, owner=None):
        if instance is None or not isinstance(instance, Config):
            return self
        else:
            return instance._storage[self.name]


    def __set__(self, instance, value):
        try:
            history = instance._history[self.name]
        except KeyError:
            history = []
            instance._history[self.name] = history
        if value is not None:
            value = self.dtype(value)
        instance._storage[self.name]=value
        traceStack = traceback.extract_stack()[:-1]
        history.append((value, traceStack))


    def __delete__(self, instance):
        self.__set__(instance, None)
   

class Config(object):
    """Base class for control objects.

    A Config object will usually have several Field instances as class 
    attributes; these are used to define most of the base class behavior.  
    Simple derived class should be able to be defined simply by setting those 
    attributes.
    """

    __metaclass__ = ConfigMeta

    def __iter__(self):
        return self._fields.__iter__()

    def keys(self):
        return self._storage.keys()
    def values(self):
        return self._storage.values()
    def items(self):
        return self._storage.items()

    def iteritems(self):
        return self._storage.iteritems()
    def itervalues(self):
        return self.storage.itervalues()
    def iterkeys(self):
        return self.storage.iterkeys()

    def __contains__(self, name):
        return self._storage.__contains__(name)

    def __init__(self, **kw):
        """Initialize the Config.

        Keyword arguments will be used to set field values.
        """
        self._name="root"

        self._storage = {}
        self._history = {}
        # load up defaults
        for field in self._fields.itervalues():
            field.__set__(self, field.default)

        for name, value in kw.iteritems():            
            try:
                setattr(self, name, value)
            except KeyError:
                pass

    @staticmethod
    def load(filename):
        """
        Construct a new Config object by executing the python code in the 
        given file.

        The python script should construct a Config name root.

        For example:
            from myModule import MyConfig

            root = MyConfig()
            root.myField = 5

        When such a file is loaded, an instance of MyConfig would be returned 
        """
        local = {}
        execfile(filename, {}, local)
        return local['root']
   
 
    def save(self, filename):
        """
        Generates a python script, which, when loaded, reproduces this Config
        """
        tmp = self._name
        self._rename("root")
        try:
            outfile = open(filename, 'w')
            self._save(outfile)
            outfile.close()
        finally:
            self._rename(tmp)
    
    def _save(self, outfile):
        """
        Internal use only. Save this Config to file
        """
        outfile.write("import %s\n"%(type(self).__module__))
        outfile.write("%s=%s()\n"%(self._name, _typeString(type(self))))
        for field in self._fields.itervalues():
            field.save(outfile, self)
        
    def toDict(self):
        dict_ = {}
        for name, field in self._fields.iteritems():
            dict_[name] = field.toDict(self)
        return dict_

    def _rename(self, name):
        """
        Internal use only. 
        Rename this Config object to reflect its position in a Config hierarchy
        """
        self._name = name
        for field in self._fields.itervalues():
            field.rename(self)

    def validate(self):
        """
        Validate the Config.

        The base class implementation performs type checks on all fields by 
        calling Field.validate(). 

        Complex single-field validation can be defined by deriving new Field 
        types. As syntactic sugar, some derived Field types are defined in 
        this module which handle recursing into sub-configs 
        (ConfigField, RegistryField)

        Inter-field relationships should only be checked in derived Config 
        classes after calling this method, and base validation is complete
        """
        for field in self._fields.itervalues():
            field.validate(self)
   
    """
    Read-only history property
    """
    history = property(lambda x: x._history)

    def __setattr__(self, attr, value):
        if attr in self._fields:
            # This allows Field descriptors to work.
            self._fields[attr].__set__(self, value)
        elif hasattr(getattr(self.__class__, attr, None), '__set__'):
            # This allows properties and other non-Field descriptors to work.
            return object.__setattr__(self, attr, value)
        elif attr in self.__dict__ or attr == "_name" or attr == "_history" or attr=="_storage":
            # This allows specific private attributes to work.
            self.__dict__[attr] = value
        else:
            # We throw everything else.
            raise AttributeError("%s has no attribute %s"%(type(self).__name__, attr))

    def __eq__(self, other):
        if type(other) == type(self):
            for name in self._fields:
                if getattr(self, name) != getattr(other, name):
                    return False
            return True
        return False
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return str(self.toDict())

    def __repr__(self):
        return repr(self.toDict())

class RangeField(Field):
    """
    Defines a Config Field which allows only a range of values.
    The range is defined by providing min and/or max values.
    If min or max is None, the range will be open in that direction
    If inclusive[Min|Max] is True the range will include the [min|max] value
    """
    def __init__(self, doc, dtype, default=None, optional=False, 
            min=None, max=None, inclusiveMin=True, inclusiveMax=False):

        if min is not None and max is not None and min > max:
            swap(min, max)
        self.min = min
        self.max = max

        self.rangeString =  "%s%s,%s%s" % \
                (("[" if inclusiveMin else "("),
                ("-inf" if self.min is None else self.min),
                ("inf" if self.max is None else self.max),
                ("]" if inclusiveMax else ")"))
        doc += "\n\tValid Range = " + self.rangeString
        if inclusiveMax:
            self.maxCheck = lambda x, y: True if y is None else x <= y
        else:
            self.maxCheck = lambda x, y: True if y is None else x < y
        if inclusiveMin:
            self.minCheck = lambda x, y: True if y is None else x >= y
        else:
            self.minCheck = lambda x, y: True if y is None else x > y
        Field.__init__(self, doc=doc, dtype=dtype, default=default, optional=optional) 

    def validate(self, instance):
        Field.validate(self, instance)
        value = instance._storage[self.name]
        if not self.minCheck(value, self.min) or \
                not self.maxCheck(value, self.max):
            fullname = _joinNamePath(instance._name, self.name)
            fieldType = type(self).__name__
            msg = "%s is outside of valid range %s"%(value, self.rangeString)
            raise FieldValidationException(fieldType, fullname, msg)
            
class ChoiceField(Field):
    """
    Defines a Config Field which allows only a set of values
    All allowed must be of the same type.
    Allowed values should be provided as a dict of value, doc string pairs

    """
    def __init__(self, doc, dtype, allowed, default=None, optional=True):
        self.allowed = dict(allowed)
        if optional and None not in self.allowed: 
            self.allowed[None]="Field is optional"

        if len(self.allowed)==0:
            raise ValueError("ChoiceFields must allow at least one choice")
        
        doc += "\nAllowed values:\n"
        for choice, choiceDoc in self.allowed.iteritems():
            if choice is not None and not isinstance(choice, dtype):
                raise ValueError("ChoiceField's allowed choice %s is of type %s. Expected %s"%\
                        (choice, type(choice), dtype))
            doc += "\t%s\t%s\n"%(str(choice), choiceDoc)

        Field.__init__(self, doc=doc, dtype=dtype, default=default, check=None, optional=optional)

    def validate(self, instance):
        Field.validate(self, instance)
        value = self.__get__(instance)
        if value not in self.allowed:
            fullname = _joinNamePath(instance._name, self.name)
            fieldType = type(self).__name__
            msg = "Value ('%s') is not allowed"%str(value)
            raise FieldValidationError(fieldType, fullname, msg) 

class ListField(Field):    
    """
    Defines a field which is a container of values of type dtype

    If length is not None, then instances of this field must match this length exactly
    If minLength is not None, then instances of the field must be no shorter then minLength
    If maxLength is not None, then instances of the field must be no longer than maxLength
    
    Additionally users can provide two check functions:
    listCheck - used to validate the list as a whole, and
    itemCheck - used to validate each item individually    
    """
    def __init__(self, doc, dtype, default=None, optional=False,
            listCheck=None, itemCheck=None, length=None, minLength=None, maxLength=None):
        Field._setup(self, doc=doc, dtype=tuple, default=default, optional=optional, check=None)
        self.listCheck = listCheck
        self.itemCheck = itemCheck
        self.itemType = dtype
        self.length=length
        self.minLength=minLength
        self.maxLength=maxLength
    
    def validate(self, instance):
        Field.validate(self, instance)
        value = self.__get__(instance) 
        if value is not None:
            fullname = _joinNamePath(instance._name, self.name)
            fieldType = type(self).__name__
            lenValue =len(value)
            if self.length is not None and not lenValue == self.length:
                msg = "Required list length=%d, got length=%d"%(self.length, lenValue)                
                raise FieldValidationError(fieldType, fullname, msg)
            elif self.minLength is not None and lenValue < self.minLength:
                msg = "Minimum allowed list length=%d, got length=%d"%(self.minLength, lenValue)                
                raise FieldValidationError(fieldType, fullname, msg)
            elif self.maxLength is not None and lenValue > self.maxLength:
                msg = "Maximum allowed list length=%d, got length=%d"%(self.maxLength, lenValue)                
                raise FieldValidationError(fieldType, fullname, msg)
            elif self.listCheck is not None and not self.listCheck(value):
                msg = "%s is not a valid value"%str(value)
                raise FieldValidationError(fieldType, fullname, msg)
            
            for i, v in enumerate(value):
                if not isinstance(v, self.itemType):
                    msg="Invalid value %s at position %d"%(str(v), i)
                    raise FieldValidationError(fieldType, fullname, msg)
                        
                if not self.itemCheck(value[i]):
                    msg="Invalid value %s at position %d"%(str(v), i)
                    raise FieldValidationError(fieldType, fullname, msg)

    def __set__(self, instance, value):
        value = [self.itemType(v) for v in value]
        Field.__set__(self, instance, value)

class ConfigField(Field):
    """
    Defines a field which is itself a Config.

    The behavior of this type of field is much like that of the base Field type.

    Note that dtype must be a subclass of Config.

    If optional=False, and default=None, the field will default to a default-constructed
    instance of dtype

    Additionally, to allow for fewer deep-copies, assigning an instance of ConfigField to dtype istelf,
    rather then an instance of dtype, will in fact reset defaults.

    This means that the argument default can be dtype, rather than an instance of dtype
    """

    def __init__(self, doc, dtype, default=None, check=None):        
        if not issubclass(dtype, Config):
            raise TypeError("configType='%s' is not a subclass of Config)"%dtype)
        if default is None:
            default = dtype
        Field._setup(self, doc=doc, dtype=dtype, check=check, default=default, optional=False)
  
    def __get__(self, instance, owner=None):
        if instance is None or not isinstance(instance, Config):
            return self
        else:
            value = instance._storage.get(self.name, None)
            if value is None:
                value = self.default()
                value._rename(_joinNamePath(instance._name, self.name))
                instance._storage[self.name]=value
                instance._history[self.name]={}
            return value


    def __set__(self, instance, value):
        name=_joinNamePath(prefix=instance._name, name=self.name)
        oldValue = self.__get__(instance)
        if type(value) == self.dtype:
            for field in self.dtype._fields:
                setattr(oldValue, field, getattr(value, field))
        elif value == self.dtype:
            for field in self.dtype._fields.itervalues():
                setattr(oldValue, field.name, field.default)
        else:
            raise ValueError("Cannot set ConfigField '%s' to '%s'"%(name, str(value)))

    def rename(self, instance):
        value = self.__get__(instance)
        value._rename(_joinNamePath(instance._name, self.name))
        
    def save(self, outfile, instance):
        fullname = _joinNamePath(instance._name, self.name)
        value = self.__get__(instance)
        value._save(outfile)

    def toDict(self, instance):
        value = self.__get__(instance)
        return value.toDict()

    def validate(self, instance):
        value = self.__get__(instance)
        value.validate()

class RegistryField(Field):
    """
    Registry Fields allow the config to choose from a set of possible Config types.
    The set of allowable types is given by the typemap argument to the constructor

    The typemap object must implement __getitem__, and __iter__ (e.g. a dict)

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
    def __init__(self, doc, typemap, default=None, multi=False, optional=False):
        Field._setup(self, doc, Registry, default=default, check=None, optional=optional)
        self.typemap = typemap
        self.multi=multi
    
    def _getOrMake(self, instance):
        registry = instance._storage.get(self.name)
        if registry is None:
            name = _joinNamePath(instance._name, self.name)
            history = []
            instance._history[self.name] = history
            registry = Registry(name, self.typemap, self.multi, history)
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
