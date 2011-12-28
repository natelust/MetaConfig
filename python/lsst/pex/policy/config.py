import traceback
import copy
import sys

__all__ = ["Config", "Field", "RangeField", "ChoiceField", "ListField", "ConfigListField", "ConfigField", "RegistryField"]

def joinNamePath(prefix, name, index=None):
    if index is not None:
        return "%s.%s[%s]"%(prefix, name, index)
    else:
        return "%s.%s"%(prefix, name)

class ConfigMeta(type):
    """A metaclass for Config

    Right now, this simply adds a dictionary containing all Field class attributes
    as a class attribute called '_fields', and adds the name of each field as an instance
    variable of the field itself (so you don't have to pass the name of the field to the
    field constructor).
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

class FieldValidationError(ValueError):
    def __init__(self, fieldtype, fullname, msg):
        error="%s '%s' failed validation: %s" % (fieldtype, fullname, msg)
        ValueError.__init__(self, error)

class Field(object):
    """A field in a a Config.

    Instances of Field should be class attributes of Config subclasses:

    class Example(Config):
        myInt = Field(int, "an integer field!", default=0)
    """
    def __init__(self, dtype, doc, default=None, check=None, optional=True):
        """Initialize a Field.
        
        dtype ------ Data type for the field.  
        doc -------- Documentation for the field.
        default ---- A default value for the field.
        check ------ A callable to be called with the field value that returns False if the value
                     is invalid.  More complex multi-field validation can be written as part of Config
                     validate() method; this will be ignored if set to None.
        optional --- When False, Config validate() will fail if value is None
        """
        self.dtype = dtype
        self.doc = doc
        self.__doc__ = doc
        self.default = default
        self.check = check
        self.optional = optional

    def _rename(self, instance, name):
        self.name = name

    def validate(self, instance):
        value = self.__get__(instance)
        fullname = joinNamePath(instance._name, self.name)
        fieldType = type(self).__name__
        if not self.optional and value is None:
            msg = "Required value cannot be None"
            raise FieldValidationError(fieldType, fullname, msg)
        if self.check is not None and not self.check(value):
            msg = "%s is not a valid value"%str(value)
            raise FieldValidationError(fieldType, fullname, msg)


    def save(self, outfile, instance):
        value = self.__get__(instance)
        fullname = joinNamePath(instance._name, self.name)
        outfile.write("%s=%s\n"%(fullname, repr(value)))

    def __get__(self, instance, owner=None):
        if instance is None or not isinstance(instance, Config):
            return self
        else:
            return instance._storage[self.name]

    def __set__(self, instance, value):        
        if value is not None:
            value = self.dtype(value)
        instance._storage[self.name]=value
        instance.setHistory(self.name)
    

class Config(object):
    """Base class for control objects.

    A Config object will usually have several Field instances as class attributes;
    these are used to define most of the base class behavior.  Simple derived class should
    be able to be defined simply by setting those attributes.
    """

    __metaclass__ = ConfigMeta

    def __init__(self, storage=None):
        """Initialize the Config.

        Pure-Python control objects will just use the default constructor, which
        sets up a simple Python dict as the storage for field values.

        Any other object with __getitem__, __setitem__, and __contains__ may be used
        as storage, and is expected to already contain the necessary items if it is
        passed to the constructor.  This is used to support C++ control objects,
        which will implement a storage interface to C++ data members in SWIG.
        """
        self._name="root"

        self.history = {}
        for field in self._fields.itervalues():
            self.history[field.name] = []

        self._storage = {}
        #load up defaults
        for field in self._fields.itervalues():
            field.__set__(self, field.default)

        #apply first batch of overides from the provided storage
        if storage is not None:
            for k,v in storage.iteritems():
                target, name = self._getTargetConfig(k)
                target._fields[name].__set__(target, v)
    @staticmethod
    def load(filename):
        f = open(filename, 'r')
        exec(f.read())
        f.close()
        return root

    def save(self, filename):
        tmp = self._name
        self._rename("root")
        try:
            outfile = open(filename, 'w')
            self._save(outfile)
            outfile.close()
        finally:
            self._rename(tmp)

    def _save(self, outfile):
        outfile.write("from %s import %s\n"%(type(self).__module__, type(self).__name__))
        outfile.write("%s=%s()\n"%(self._name, type(self).__name__))
        for field in self._fields.itervalues():
            field.save(outfile, self)
        

    def _rename(self, name):
        self._name = name
        for field in self._fields.itervalues():
            field._rename(self, field.name)

    def validate(self):
        """
        Validate the Config.

        The base class implementation performs type checks on all fields, recurses into
        nested Config instances, and does any simple validation defined by passing
        "check" callables to the field constructors. More complex validation field behaviors
        can be attained by deriving new Field classes which implement the validate() method.
        As syntactic sugar, some derived Field types are defined in this module.
        This should be called by derived Config classes even if they do more complex validation.
        """
        for field in self._fields.itervalues():
            field.validate(self)
    
    def setHistory(self, fieldname):
        target, name = self._getTargetConfig(fieldname)
        value = target._storage[name]
        target.history[name].append((value, traceback.extract_stack()[:-2]))

    def getHistory(self, fieldname, limit=0):
        target, name = self._getTargetConfig(fieldname)
        return target.history[name][-limit:]

    def _getTargetConfig(self, fieldname):
        dot = fieldname.rfind(".")
        target = self
        if dot > 0: 
            try:
                path = fieldname[:dot]
                target = eval("self."+fieldname[:dot])
            except SyntaxError:
                ValueError("Malformed field name '%s'"%path)
            except AttributeError:
                ValueError("Could not find target '%s' in Config %s"%(path, self._name))
        
        name = fieldname[dot+1:]
        if not name in target._fields:
            raise ValueError("Config does not include field '%s'"%fieldname)

        return target, name

    def __str__(self):
        return str(self.__class__) + ":" + str(self._storage)

class RangeField(Field):
    def __init__(self, dtype, doc, default=None, optional=True, 
            min=None, max=None, inclusiveMin=True, inclusiveMax=False):

        if min is not None and max is not None and min > max:
            swap(min, max)
        self.min = min
        self.max = max

        self.rangeString =  "%s%s,%s%s" % \
                (("[" if inclusiveMin else "(")
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
        Field.__init__(self, dtype, doc, default, optional) 

    def validate(self, instance):
        Field.validate(self, instance)
        value = instance._storage[field.name]
        if not self.checkMin(value, self.min) or not self.checkMax(value, self.max):
            fullname = joinNamePath(instance._name, self.name)
            fieldType = type(self).__name__
            msg = "%s is outside of valid range %s"%(value, self.rangeString)
            raise FieldValidationException(fieldType, fullname, msg)
            
class ChoiceField(Field):
    def __init__(self, dtype, doc, allowed, default=None, optional=True):
        self.allowed = dict(allowed)
        if optional and None not in self.allowed: 
            self.allowed[None]="Field is optional"

        if len(self.allowed)==0:
            raise ValueError("ChoiceFields must have at least one allowed value")
        
        doc += "\nAllowed values:\n"
        for choice, choiceDoc in self.allowed.iteritems():
            doc += "\t%s\t%s\n"%(str(choice), choiceDoc)

        Field.__init__(self, dtype, doc, default=default, check=None, optional=optional)

    def validate(self, instance):
        Field.validate(self, instance)
        value = self.__get__(instance)
        if value not in self.allowed:
            fullname = joinNamePath(instance._name, self.name)
            fieldType = type(self).__name__
            msg = "Value ('%s') is not allowed"%str(value)
            raise FieldValidationError(fieldtype, fullname, msg) 

class ListExpr(object):
    def __init__(self, listfield, config):
        self.name = listfield.name
        self.value = config._storage[self.name]        
        self.itemType = listfield.itemType 
        self.owner = config

    def __len__(self):
        return len(self.value)

    def __getitem__(self, i):
        return self.value[i]

    def __delitem__(self, i):
        del self.value[i]
        self.owner.setHistory(self.name)

    def __setitem__(self, i, x):   
        self.value[i] = self.itemType(x)
        self.owner.setHistory(self.name)

    def __iter__(self):
        return self.value.__iter__()

    def __contains__(self, x):
        return self.value.__contains__(x)

    def index(self, x, i, j):
        return self.value.index(x,i,j)

    def append(self, x):
        self[len(self):len(self)] = [x]

    def extend(self, x):
        self[len(self):len(self)] = x

    def insert(self, i, x):
        self[i:i] = [x]

    def pop(i=None):        
        x = self[i]
        del self[i]
        self.owner.setHistory(self.name)
        return x

    def remove(x):
        del self[self.index(x)]
        self.owner.setHistory(self.name)
    
    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)

class ListField(Field):
    def __init__(self, itemType, doc, default=None, optional=True,
            listCheck=None, itemCheck=None, length=None, minLength=None, maxLength=None):
        Field.__init__(self, list, doc, default=default, optional=optional, check=None)
        self.listCheck = listCheck
        self.itemCheck = itemCheck
        self.length=length
        self.minLength=minLength
        self.maxLength=maxLength
        self.itemType=itemType
    
    def __get__(self, instance, owner=None):
        return ListExpr(self, instance)

    def __set__(self, instance, value):
        if value is not None:
            value = [self.itemType(x) if x is not None else None for x in value]
        Field.__set__(self, instance, value)

    def validate(self, instance):
        Field.validate(self, instance)
        value = self.__get__(instance) 
        if value is not None:
            fullname = joinNamePath(instance._name, self.name)
            fieldType = type(self).__name__
            lenValue =len(value)
            if self.length is not None and not lenValue == self.length:
                msg = "Required list length=%d, got length=%d"%(self.length, lenValue)                
                raise FieldValidationError(fieldtype, fullname, msg)
            elif self.minLength is not None and lenValue < self.minLength:
                msg = "Minimum allowed list length=%d, got length=%d"%(self.minLength, lenValue)                
                raise FieldValidationError(fieldtype, fullname, msg)
            elif self.maxLength is not None and lenValue > self.maxLength:
                msg = "Maximum allowed list length=%d, got length=%d"%(self.maxLength, lenValue)                
                raise FieldValidationError(fieldtype, fullname, msg)
            elif self.listCheck is not None and not self.listCheck(value):
                msg = "%s is not a valid value"%str(value)
                raise FieldValidationError(fieldtype, fullname, msg)
            elif self.itemCheck is not None:
                for i, v in enumerate(value):
                    if not self.itemCheck(value[i]):
                        msg="Invalid value %s at position %d"%(str(v), i)
                        raise FieldValidationError(fieldtype, fullname, msg)

class ConfigListExpr(ListExpr):
    def __setitem__(self, k, x):
        if not isinstance(k, slice):
            start, stop, step = k, k+1, 1
        else:
            start, stop, step = k.indices(len(self))
        
        for i, xi in zip(range(start, stop, step), x):
            itemname = joinNamePath(self.owner.name, self.name, i)
            if isinstance(xi, self.itemType):
                xi = copy.deepcopy(xi)
                xi._rename(itemname)
            elif issubclass(xi, self.itemType):
                xi = xi()
                xi._rename(itemname)
            elif xi is not None:
                raise TypeError("%s is not an instance of %s"%(x, self.itemType))
                
            self.value[i]= xi
        self.owner.setHistory(self.name)

class ConfigListField(ListField):
    @staticmethod
    def itemCheck(config):
        if config is not None:
            config.validate()
        return True

    def __init__(self, configType, doc, default=None, optional=True,
            listCheck=None, length=None, minLength=None, maxLength=None):
        if not issubclass(configType, Config):
            raise TypeError("configType='%s' is not a subclass of Config)"%str(configType))
        
        ListField.__init__(self, configType, doc, default=default, optional=optional,
                listCheck=listCheck, itemCheck=ConfigListField.itemCheck, 
                length=length, minLength=minLength, maxLength=maxLength)
        
    def __set__(self, instance, value):
        if value is not None:
            for i, xi in enumerate(value):
                itemname = joinNamePath(instance._name, self.name, i)
                if isinstance(xi, self.itemType):
                    xi = copy.deepcopy(xi)
                    xi._rename(itemname)
                elif isinstance(xi, type) and issubclass(xi, self.itemType):
                    xi = xi()
                    xi._rename(itemname)
                elif xi is not None:
                    raise TypeError("%s is not an instance of %s"%(xi, self.itemType))
                value[i] = xi
        
        instance._storage[self.name]= value
        instance.setHistory(self.name)
        
    def __get__(self, instance, dtype=None):
        if instance is None:
            return self
        else:
            return ConfigListExpr(self, instance)

    def save(self, outfile, instance):
        types = [type(x) if x is not None else None for x in self.values]
        for t in types:
            outfile.write("from %s import %s\n"%(t.__module__, t.__name__))
        fullname = joinNamePath(instance._name, self.name)
        outfile.write("%s=%s\n"%(fullname, types))
        for x in self.values:
            if x is not None:
                x._save(outfile)

class ConfigRegistry(object):
    def __init__(self, configname, field):
        self.configname = configname
        self.fieldname = field.name
        self.basetype = field.basetype
        self.restricted = field.restricted
        self.active = None 
        self.types = copy.deepcopy(field.typemap) if field.typemap is not None else {}
        self.values = {}

    def __getitem__(self, k):
        if k not in self.types:
            raise KeyError("Unknown key '%s' in ConfigRegistry '%s'"%\
                    (k, joinNamePath(self.configname, self.fieldname)))
        elif k not in self.values or self.values[k] is None:
            value = self.types[k]()
            value._rename(joinNamePath(self.configname, self.fieldname, k))
        
        return self.values[k]

    def __setitem__(self, k, val):
        dtype = self.types.get(k)
        if dtype is None:
            if self.restricted:            
                raise ValueError("Cannot register '%s' in restricted ConfigRegistry %s"%\
                        (str(k), joinNamePath(self.configname, self.fieldname)))
            if isinstance(val, type) and issubclass(val, self.basetype):
                dtype = val
            elif isinstance(val, self.basetype):
                dtype = type(val)
            elif val is None:
                dtype = self.basetype
            else:
                raise ValueError("Invalid type %s. All values in ConfigRegistry '%s' must be of type %s"%\
                        (dtype, joinNamePath(self.configname, self.fieldnam), self.basetype))
            self.types[k] = dtype
        
        if val == dtype:
            val = dtype()
            val._rename(self.fullname)
        elif isinstance(val, dtype):
            val = copy.deepcopy(val)
            val._rename(self.fullname)
        elif val is not None:
            raise ValueError("Invalid type %s. ConfigRegistry entry '%s' must be of type %s"%\
                    (type(val), joinNamePath(self.configname, self.fieldname, k), dtype))
        
        self.values[k] = val
        if self.active is None and val is not None:
            self.active = k 
        #TODO: save history

    def __repr__(self):
        return repr(self.active)
    def __str__(self):
        return self.fullname +"="+str(self.active)


class RegistryField(Field):
    def __init__(self, doc, basetype=Config, default=None, typemap={}, restricted=False, optional=False):
        if len(typemap)==0 and restricted:
            raise ValueError("Cannot instantiate a restricted RegistryField with an empty typemap")
        if not issubclass(basetype, Config):
            raise ValueError("basetype='%s' is not allowed in RegistryField. basetype must be a subclass of Config."%(basetype))
        if default is None and not optional:
            if len(typemap)==0:
                default = basetype
            else:
                default = typemap[0]

        Field.__init__(self, ConfigRegistry, doc, default=default, check=None, optional=optional)
        self.typemap = typemap
        self.restricted=restricted
        self.basetype = basetype if basetype is not None else Config
    
    def _getOrMake(self, instance):
        registry = instance._storage.get(self.name)
        if registry is None:
            fullname = joinNamePath(instance._name, self.name)
            registry = ConfigRegistry(instance._name, self)
            instance._storage[self.name] = registry
        return registry


    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        else:
            return self._getOrMake(instance)

    def __set__(self, instance, value):
        registry = self._getOrMake(instance)
        if value in registry.types or value is None:
            registry.active = value
        else:
            raise KeyError("Unknown key '%s' in RegistryField '%s'"%\
                    (value, joinNamePath(instance._name, self.name)))
                

    def _rename(self, instance, name):
        Field._rename(self, instance, name)
        registry = RegistryField.__get__(self, instance)
        for k, v in registry.values.iteritems():
            fullname = joinNamePath(instance._name, name, k)
            v._rename(fullname)

    def validate(self, instance):
        Field.validate(self, instance)
        registry = RegistryField.__get__(self, instance)
        if registry.active is None and not self.optional:
            fullname = joinNamePath(instance._name, name)
            fieldType = type(self).__name__
            msg = "Required field cannot be None"
            raise FieldValidationError(fieldType, fullname, msg)
        elif registry.active is not None:
            value = registry[registry.active]
            value.validate()
        
    def save(self, outfile, instance):
        registry = RegistryField.__get__(self, instance)
        fullname = joinNamePath(instance._name, self.name)
        for t in registry.types.itervalues():
            outfile.write("from %s import %s\n"%(t.__module__, t.__name__))
        outfile.write("%s.types=%s\n"%(fullname, registry.types))
        for v in registry.values.itervalues():
            v._save(outfile)
        outfile.write("%s=%s\n"%(fullname, str(registry.active)))

class ConfigField(Field):
    def __init__(self, configType, doc, default=None, optional=False):
        if not issubclass(configType, Config):
            raise TypeError("configType='%s' is not a subclass of Config)"%configType)
        if default is None and not optional:
            default = configType
        Field.__init__(self, dtype=configType, doc=doc, default=default, optional=optional)
        
    def __set__(self, instance, value):
        fullname=joinNamePath(instance._name, self.name)
        if isinstance(value, self.dtype):
            value = copy.deepcopy(value)
            value._rename(fullname)
        elif isinstance(value, type) and issubclass(value, self.dtype):
            value = value()
            value._rename(fullname)
        elif value is not None:
            raise ValueError("Cannot set ConfigField '%s' to '%s'"%(fullname, str(value)))

        instance._storage[self.name]=value
        instance.setHistory(self.name)
    
    def save(self, outfile, instance):
        fullname = joinNamePath(instance._name, self.name)
        value = self.__get__(instance)
        outfile.write("from %s import %s\n"%(self.dtype.__module__, self.dtype.__name__))
        if value is not None:
            value._save(outfile)
        else:
            outfile.write("%s=%s\n"%(fullname, None))

