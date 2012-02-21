import traceback
import sys
import collections
import copy

__all__ = ["Config", "Field", "RangeField", "ChoiceField", "ListField", "DictField", "ConfigField",
           "ConfigInstanceDict", "ConfigChoiceField", "FieldValidationError"]

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

class List(collections.MutableSequence):
    def __init__(self, dtype, value, history):
        self.dtype=dtype
        if value is not None:
            self.value = [dtype(x) if x is not None else None for x in value]
        else:
            self.value = []
        self._history = history if history is not None else {}
        self.__appendHistory()
    """
    Read-only history
    """
    history = property(lambda x: x._history)   

    def __appendHistory(self):
        traceStack = traceback.extract_stack()[:-2]
        self._history.append((list(self.value), traceStack))

    def __contains__(self, x):
        return self.value.__contains__(x)

    def __len__(self):
        return len(self.value)

    def __setitem__(self, i, x):
        if isinstance(i, slice):
            x = [self.dtype(xi) if xi is not None else None for xi in x]
        else:
            x = self.dtype(x)

        try:
            self.value[i]=x
            self.__appendHistory()
        except:
            raise
        
    def __getitem__(self, i):
        return self.value[i]
    
    def __delitem__(self, i):
        try:
            del self.value[i]
            self.__appendHistory()
        except:
            raise

    def __iter__(self):
        return self.value.__iter__()

    def insert(self, i, x):
        if x is not None:
            x = self.dtype(x)
        self[i:i+1]=x

    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)


class Dict(collections.MutableMapping):
    def _checkItemType(self, k, x):
        try:
            k = self.keytype(k)
        except:
            raise TypeError("Key %s is of type %s, expected type %s"%\
                    (k, type(k), self.keytype))
        try:
            x = self.itemtype(x)
        except:
            raise TypeError("Value %s at key %s is of type %s, expected type %s"%\
                    (x, k, type(x), self.itemtype))
        return k, x
    def __appendHistory(self):
        traceStack = traceback.extract_stack()[:-2]
        self._history.append((dict(self.value), traceStack))

    def __init__(self, keytype, itemtype, value, history):
        self.keytype = keytype
        self.itemtype = itemtype
        self.value = {}
        if value is not None:
            for k, x in value.iteritems():                
                k, x = self._checkItemType(k, x)
                self.value[k]=x
        self._history = history if history is not None else []
        self.__appendHistory()

    """
    Read-only history
    """
    history = property(lambda x: x._history)   


   
    def __getitem__(self, k):
        return self.value[k]

    def __len__(self):
        return len(self.value)

    def __iter__(self):
        return self.value.__iter__()

    def __contains__(self, k):
        return self.value.__contains__(k)

    def __setitem__(self, k, x):
        k,x = self._checkItemType(k, x)

        try:
            self.value[k]=x
            self.__appendHistory()
        except:
            raise

    def __delitem__(self, k):
        try:
            del self.value[k]
            self.__appendHistory()
        except:
            raise

    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)
    

class ConfigInstanceDict(collections.Mapping):
    """A dict of instantiated configs, used to populate a ConfigChoiceField.
    
    typemap must support the following:
    - typemap[name]: return the config class associated with the given name
    """
    def __init__(self, fullname, types, multi, history=None):
        collections.Mapping.__init__(self)
        self._dict = dict()
        self._fullname = fullname
        self._selection = None
        self._multi = multi
        self.types = types
        self.history = [] if history is None else history

    def __contains__(self, k): return k in self._dict

    def __len__(self): return len(self._dict)

    def __iter__(self): return iter(self._dict)

    def _setSelection(self,value):
        if value is None:
            self._selection=None
        # JFB:  Changed to ensure selection is present in this instance (and add it if it is not),
        #       rather than just checking if it is present in self.types.
        elif self._multi:
            for v in value:
                if v not in self._dict:
                    r = self[v] # just invoke __getitem__ to make sure it's present
            self._selection = tuple(value)
        else:
            if value not in self._dict:
                r = self[value] # just invoke __getitem__ to make sure it's present
            self._selection = value
        self.history.append((value, traceback.extract_stack()[:-1]))
    
    def _getNames(self):
        if not self._multi:
            raise AttributeError("Single-selection field %s has no attribute 'names'"%self._fullname)
        return self._selection
    def _setNames(self, value):
        if not self._multi:
            raise AttributeError("Single-selection field %s has no attribute 'names'"%self._fullname)
        self._setSelection(value)
    def _delNames(self):
        if not self._multi:
            raise AttributeError("Single-selection field %s has no attribute 'names'"%self._fullname)
        self._selection = None
    
    def _getName(self):
        if self._multi:
            raise AttributeError("Multi-selection field %s has no attribute 'name'"%self._fullname)
        return self._selection
    def _setName(self, value):
        if self._multi:
            raise AttributeError("Multi-selection field %s has no attribute 'name'"%self._fullname)
        self._setSelection(value)
    def _delName(self):
        if self._multi:
            raise AttributeError("Multi-selection field %s has no attribute 'name'"%self._fullname)
        self._selection=None
   
    """
    In a multi-selection ConfigInstanceDict, list of names of active items
    Disabled In a single-selection _Regsitry)
    """
    names = property(_getNames, _setNames, _delNames)
   
    """
    In a single-selection ConfigInstanceDict, name of the active item
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
    for multi-selection _Registry, this is equivalent to: [self[name] for name in self.names]
    for single-selection _Registry, this is equivalent to: self[name]
    for multi-selection _Registry, this is equivalent to: [self[name] for [name] in self.names]
    for single-selection _Registry, this is equivalent to: self[name]
    """
    active = property(_getActive)

    def __getitem__(self, k):
        try:
            value = self._dict[k]
        except KeyError:
            try:
                dtype = self.types[k]
            except:
                raise KeyError("Unknown key %s in field %s"%(repr(k), self._fullname))
            value = self._dict.setdefault(k, dtype())
        return value

    def __setitem__(self, k, value):
        name = _joinNamePath(name=self._fullname, index=k)
        try:
            dtype = self.types[k]
        except:
            raise KeyError("Unknown key %s in field %s"%(repr(k), self._fullname))

        if value != dtype and type(value) != dtype:
            raise TypeError("Cannot set ConfigField %s: type(%r) is not %r" % (name, value, dtype))

        oldValue = self._dict.get(k, None)
        if oldValue is None:
            if value == dtype:
                self._dict[k] = value()
            else:
                self._dict[k] = copy.deepcopy(value)
            self._dict[k]._rename(name)
        else:
            if value == dtype:
                value = value()
            oldValue.update(**value._storage)

    def _rename(self, fullname):
        self._fullname=fullname
        for k, v in self._dict.iteritems():
            v._rename(_joinNamePath(name=fullname, index=k))

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
        def getFields(classtype):
            fields = {}
            bases=list(classtype.__bases__)
            bases.reverse()
            for b in bases:
                fields.update(getFields(b))

            for k, v in classtype.__dict__.iteritems():
                if isinstance(v, Field):
                    fields[k] = v
            return fields

        fields = getFields(self)
        for k, v in fields.iteritems():            
            setattr(self, k, copy.deepcopy(v))

    def __setattr__(self, name, value):
        if isinstance(value, Field):
            value.name = name
            self._fields[name] = value
        type.__setattr__(self, name, value)

class FieldValidationError(ValueError):
    def __init__(self, fieldtype, fullname, msg):
        error="%s '%s' failed validation: %s" % (fieldtype.__name__, fullname, msg)
        ValueError.__init__(self, error)

class Field(object):
    """A field in a a Config.

    Instances of Field should be class attributes of Config subclasses:
    Field only supports basic data types (int, float, bool, str)

    class Example(Config):
        myInt = Field(int, "an integer field!", default=0)
    """
    supportedTypes=(str, bool, float, int, complex)

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
            raise ValueError("Unsuported Field dtype '%s'"%(dtype))
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
        try:
            self.validateValue(value)
        except BaseException, e:
            fullname = _joinNamePath(instance._name, self.name)
            fieldType = type(self)
            raise FieldValidationError(fieldType, fullname, e.message)
    
    def validateValue(self, value):
        if not self.optional and value is None:
            msg = "Required value cannot be None"
            raise ValueError(msg)
        if value is not None and not isinstance(value, self.dtype):
            msg = "Incorrect type. Expected type '%s', got '%s'"%(self.dtype, type(value))
            raise TypeError(msg)
        if self.check is not None and not self.check(value):
            msg = "%s is not a valid value"%str(value)
            raise ValueError(msg)

    def save(self, outfile, instance):
        """
        Saves an instance of this field to file.
        This is invoked by the owning config object, and should not be called directly
        """
        value = self.__get__(instance)
        fullname = _joinNamePath(instance._name, self.name)
        print >> outfile, "%s=%s"%(fullname, repr(value))
    
    def toDict(self, instance):
        """
        Convert the field value so that it can be set as the value of an item in a dict
        """
        return self.__get__(instance)

    def __get__(self, instance, owner=None):
        if instance is None or not isinstance(instance, Config):
            return self
        else:
            return instance._storage[self.name]

    def __set__(self, instance, value):
        history = instance._history.setdefault(self.name, [])
        if value is not None:
            value = self.dtype(value)
            self.validateValue(value)
        
        instance._storage[self.name] = value
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

    def __new__(cls, *args, **kw):
        instance = object.__new__(cls, *args, **kw)
        instance._name="root"
        instance._storage = {}
        instance._history = {}
        # load up defaults
        for field in instance._fields.itervalues():
            field.__set__(instance, field.default)
        return instance

    def __init__(self, **kw):
        """Initialize the Config.

        Keyword arguments will be used to override field values.
        """
        self.setDefaults()
        self.update(**kw)

    def setDefaults(self):
        """
        Derived config classes that must compute defaults rather than using the 
        Field defaults should do so here.
        """
        pass
            
    def update(self, **kw):
        for name, value in kw.iteritems():            
            try:
                setattr(self, name, value)
            except KeyError:
                pass

    def load(self, filename, root="root"):
        """
        modify this config in place by executing the python code in the 
        given file.

        The file should modify a Config named root

        For example:
            root.myField = 5
        """
        local = {root:self}
        execfile(filename, {}, local)
 
    def save(self, filename, root="root"):
        
        """
        Generates a python script, which, when loaded, reproduces this Config
        """
        tmp = self._name
        self._rename(root)
        try:
            outfile = open(filename, 'w')
            configType = type(self)
            typeString = configType.__module__+"."+configType.__name__
            print >> outfile, "import %s"%(configType.__module__) 
            print >> outfile, "assert(type(%s)==%s)"%(root, typeString) 
            self._save(outfile)
            outfile.close()
        finally:
            self._rename(tmp)
    
    def _save(self, outfile):
        """
        Internal use only. Save this Config to file
        """
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
        (ConfigField, ConfigChoiceField)

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
            raise AttributeError("%s has no attribute %s"%(type(self), attr))

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
        return "%s(%s)" % (
            type(self).__name__, 
            ", ".join("%s=%r" % (k, v) for k, v in self.toDict().iteritems() if v is not None)
            )

class RangeField(Field):
    """
    Defines a Config Field which allows only a range of values.
    The range is defined by providing min and/or max values.
    If min or max is None, the range will be open in that direction
    If inclusive[Min|Max] is True the range will include the [min|max] value
    
    """

    supportedTypes=(int, float)

    def __init__(self, doc, dtype, default=None, optional=False, 
            min=None, max=None, inclusiveMin=True, inclusiveMax=False):
        if min is None and max is None:
            raise ValueError("min and max cannot both be None")

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

    def validateValue(self, value):
        Field.validateValue(self, value)
        if not self.minCheck(value, self.min) or \
                not self.maxCheck(value, self.max):
            msg = "%s is outside of valid range %s"%(value, self.rangeString)
            raise ValueError(msg)
            
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

    def validateValue(self, value):
        Field.validateValue(self, value)
        if value not in self.allowed:
            msg = "Value ('%s') is not in the set of allowed values"%str(value)
            raise ValueError(msg) 

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
        if dtype not in Field.supportedTypes:
            raise ValueError("Unsuported Field dtype '%s'"%dtype)
        Field._setup(self, doc=doc, dtype=List, default=default, optional=optional, check=None)
        self.listCheck = listCheck
        self.itemCheck = itemCheck
        self.itemType = dtype
        self.length=length
        self.minLength=minLength
        self.maxLength=maxLength
    
    def validateValue(self, value):
        Field.validateValue(self, value)
        if value is not None:
            lenValue =len(value)
            if self.length is not None and not lenValue == self.length:
                msg = "Required list length=%d, got length=%d"%(self.length, lenValue)                
                raise ValueError(msg)
            elif self.minLength is not None and lenValue < self.minLength:
                msg = "Minimum allowed list length=%d, got length=%d"%(self.minLength, lenValue)
                raise ValueError(msg)
            elif self.maxLength is not None and lenValue > self.maxLength:
                msg = "Maximum allowed list length=%d, got length=%d"%(self.maxLength, lenValue)
                raise ValueError(msg)
            elif self.listCheck is not None and not self.listCheck(value):
                msg = "%s is not a valid value"%str(value)
                raise ValueError(msg)
            
            for i, v in enumerate(value):
                if not isinstance(v, self.itemType):
                    msg="Incorrect item type at position %d. Expected '%s', got '%s'"%\
                            (i, type(v), self.itemType)
                    raise TypeError(msg)
                        
                if self.itemCheck is not None and not self.itemCheck(value[i]):
                    msg="Item at position %s is not a valid value: %s"%(i, str(v))
                    raise ValueError(msg)

    def __set__(self, instance, value):
        history = instance._history.setdefault(self.name, [])
        if value is not None:
            instance._storage[self.name] = List(self.itemType, value, history)
        else:
            Field.__set__(self, instance, None)

    
    def toDict(self, instance):        
        value = self.__get__(instance)        
        return list(value) if value is not None else None

class DictField(Field):
    """
    Defines a field which is a mapping of values

    Users can provide two check functions:
    dictCheck - used to validate the dict as a whole, and
    itemCheck - used to validate each item individually    
    """
    def __init__(self, doc, keytype, itemtype, default=None, optional=False, dictCheck=None, itemCheck=None):
        Field._setup(self, doc=doc, dtype=Dict, default=default, optional=optional, check=None)
        if keytype not in self.supportedTypes:
            raise ValueError("key type '%s' is not a supported type"%keytype)
        elif itemtype not in self.supportedTypes:
            raise ValueError("item type '%s' is not a supported type"%itemtype)

        self.keytype = keytype
        self.itemtype = itemtype
        self.dictCheck = dictCheck
        self.itemCheck = itemCheck
    
    def validateValue(self, value):
        Field.validateValue(self, value)
        if value is not None:
            if self.dictCheck is not None and not self.dictCheck(value):
                msg = "%s is not a valid value"%str(value)
                raise ValueError(msg)
            
            for k, v in value.iteritems():
                value._checkItemType(k, v)
                        
                if self.itemCheck is not None and not self.itemCheck(v):
                    msg="Item at key %s is not a valid value: %s"%(k, str(v))
                    raise ValueError(msg)

    def __set__(self, instance, value):
        history = instance._history.setdefault(self.name, [])
        if value is not None:
            instance._storage[self.name] = Dict(self.keytype, self.itemtype, value, history)
        else:
            Field.__set__(self, instance, None)
    
    def toDict(self, instance):        
        value = self.__get__(instance)        
        return dict(value) if value is not None else None

class ConfigField(Field):
    """
    Defines a field which is itself a Config.

    The behavior of this type of field is much like that of the base Field type.

    Note that dtype must be a subclass of Config.

    If optional=False, and default=None, the field will default to a default-constructed
    instance of dtype.

    Additionally, to allow for fewer deep-copies, assigning an instance of ConfigField to dtype itself,
    is considered equivalent to assigning a default-constructed sub-config.  This means that the
    argument default can be dtype, rather than an instance of dtype.

    Assigning to ConfigField will replace the current sub-config object with a deep copy of the new object
    with the history of the old object merged in.
    """

    def __init__(self, doc, dtype, default=None, check=None):
        if not issubclass(dtype, Config):
            raise ValueError("dtype '%s' is not a subclass of Config" % dtype)
        if default is None:
            default = dtype
        Field._setup(self, doc=doc, dtype=dtype, check=check, default=default, optional=False)
  
    def __get__(self, instance, owner=None):
        if instance is None or not isinstance(instance, Config):
            return self
        else:
            value = instance._storage.get(self.name, None)
            if value is None:
                self.__set__(instance, self.default)
            return value

    def __set__(self, instance, value):
        name = _joinNamePath(prefix=instance._name, name=self.name)
        if value != self.dtype and type(value) != self.dtype:
            raise TypeError("Cannot set ConfigField %s: type(%r) is not %r" % (name, value,dtype))

        oldValue = instance._storage.get(self.name, None)
        if oldValue is None:
            if value == self.dtype:
                instance._storage[self.name] = value()
            else:
                instance._storage[self.name] = copy.deepcopy(value)
            instance._storage[self.name]._rename(name)
        else:
            if value == self.dtype:
                value = value()
            oldValue.update(**value._storage)

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

        if self.check is not None and not self.check(value):
            fieldType = ConfigField
            fullname = value._name
            msg = "%s is not a valid value"%str(value)
            raise FieldValidationError(fieldType, fullname, msg)

class ConfigChoiceField(Field):
    """
    ConfigChoiceFields allow the config to choose from a set of possible Config types.
    The set of allowable types is given by the typemap argument to the constructor

    The typemap object must implement typemap[name], which must return a Config subclass.

    While the typemap is shared by all instances of the field, each instance of
    the field has its own instance of a particular sub-config type

    For example:

      class AaaConfig(Config):
        somefield = Field(int, "...")
      TYPEMAP = {"A", AaaConfig}
      class MyConfig(Config):
          choice = ConfigChoiceField("doc for choice", TYPEMAP)
      
      instance = MyConfig()
      instance.choice['AAA'].somefield = 5
      instance.choice = "AAA"
    
    Alternatively, the last line can be written:
      instance.choice.name = "AAA"

    Validation of this field is performed only the "active" selection.
    If active is None and the field is not optional, validation will fail. 
    
    ConfigChoiceFields can allow single selections or multiple selections.
    Single selection fields set selection through property name, and 
    multi-selection fields use the property names. 

    ConfigChoiceFields also allow multiple values of the same type:
      TYPEMAP["CCC"] = AaaConfig
      TYPEMAP["BBB"] = AaaConfig

    When saving a config with a ConfigChoiceField, the entire set is saved, as well as the active selection    
    """
    instanceDictClass = ConfigInstanceDict
    def __init__(self, doc, typemap, default=None, optional=False, multi=False):
        Field._setup(self, doc, self.instanceDictClass, default=default, check=None, optional=optional)
        self.typemap = typemap
        self.multi = multi
    
    def _getOrMake(self, instance):
        instanceDict = instance._storage.get(self.name)
        if instanceDict is None:
            name = _joinNamePath(instance._name, self.name)
            history = []
            instance._history[self.name] = history
            instanceDict = self.dtype(name, self.typemap, self.multi, history)
            instanceDict.__doc__ = self.doc
            instance._storage[self.name] = instanceDict
        return instanceDict

    def __get__(self, instance, owner=None):
        if instance is None or not isinstance(instance, Config):
            return self
        else:
            return self._getOrMake(instance)

    def __set__(self, instance, value):        
        instanceDict = self.__get__(instance)
        if isinstance(value, self.instanceDictClass):
            for k in value:                    
                instanceDict[k] = value[k]
            instanceDict._setSelection(value._selection)
        else:
            instanceDict._setSelection(value)

    def rename(self, instance):
        instanceDict = self.__get__(instance)
        fullname = _joinNamePath(instance._name, self.name)
        instanceDict._rename(fullname)

    def validate(self, instance):
        instanceDict = self.__get__(instance)
        if not instanceDict.active and not self.optional:
            fullname = _joinNamePath(instance._name, self.name)
            fieldType = type(self)
            msg = "Required field cannot be None"
            raise FieldValidationError(fieldType, fullname, msg)
        elif instanceDict.active:
            if self.multi:
                for a in instanceDict.active:
                    a.validate()
            else:
                instanceDict.active.validate()

    def toDict(self, instance):
        instanceDict = self.__get__(instance)

        dict_ = {}
        if self.multi:
            dict_["names"]=instanceDict.names
        else:
            dict_["name"] =instanceDict.name
        
        values = {}
        for k, v in instanceDict.iteritems():
            values[k]=v.toDict()
        dict_["values"]=values

        return dict_

    def save(self, outfile, instance):
        instanceDict = self.__get__(instance)
        fullname = instanceDict._fullname
        for v in instanceDict.itervalues():
            v._save(outfile)
        if self.multi:
            print >> outfile, "%s.names=%s"%(fullname, repr(instanceDict.names))
        else:
            print >> outfile, "%s.name=%s\n"%(fullname, repr(instanceDict.name))

