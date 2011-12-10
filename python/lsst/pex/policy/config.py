import traceback
import sys

__all__ = ["Config", "Field", "ChoiceField", "ConfigField", "ListField", "ConfigListField"]

class ConfigMeta(type):
    """A metaclass for Config

    Right now, this simply adds a dictionary containing all Field class attributes
    as a class attribute called 'fields', and adds the name of each field as an instance
    variable of the field itself (so you don't have to pass the name of the field to the
    field constructor).
    """

    def __init__(self, name, bases, dict_):
        type.__init__(self, name, bases, dict_)
        self.fields = {}
        for k, v in dict_.iteritems():
            if isinstance(v, Field):
                v.name = k
                self.fields[k] = v
class Field(object):
    """A field in a a Config.

    Instances of Field should be class attributes of Config subclasses:

    class Example(Config):
        myInt = Field(int, "an integer field!", default=0)
    """

    def __init__(self, dtype, doc, default=None, check=None, optional=True, callback=None):
        """Initialize a Field.
        
        dtype ------ Data type for the field.  
        doc -------- Documentation for the field.
        default ---- A simple default for the field.  If the default must be computed, just
                     leave this as None and set the default as part of validate().
        check ------ A simple callable to be called with the field value that returns False if the value
                     is invalid.  More complex multi-field validation can be written as part of the
                     validate() method; this will be ignore if set to None.
        """
        if issubclass(dtype, Config) and not \
                (isinstance(self, ConfigField) or isinstance(self, ConfigListField)):
            raise ValueError("Fields cannot have dtypes which are subclasses of config. " \
                             "Use ConfigField or ListConfigField instead")
        self.dtype = dtype
        self.doc = doc
        self.__doc__ = doc
        self.default = default
        self.check = check
        self.optional = optional

    def __get__(self, instance, dtype=None):        
        return instance._storage[self.name]

    def __set__(self, instance, value):
        instance._storage[self.name]=value
        instance.setHistory(self.name)


class Config(object):
    """Base class for control objects.

    A Config object will usually have several Field instances as class attributes;
    these are used to define most of the base class behavior.  Simple derived class should
    be able to be defined simply by setting those attributes.
    """

    __metaclass__ = ConfigMeta
    def __getitem__(self, key):
        target, name = self._getTargetConfig(key, create=False)
        return target.fields[name]

    def __contains__(self, key):
        try:
            self._getTargetConfig(key)
        except:
            return False
        return True

    def iteritems(self):
        return self._storage.iteritems()

    def __init__(self, name=None, storage=None):
        """Initialize the Config.

        Pure-Python control objects will just use the default constructor, which
        sets up a simple Python dict as the storage for field values.

        Any other object with __getitem__, __setitem__, and __contains__ may be used
        as storage, and is expected to already contain the necessary items if it is
        passed to the constructor.  This is used to support C++ control objects,
        which will implement a storage interface to C++ data members in SWIG.
        """
        if name is None or len(name)==0:
            name = "root"
        self.name=name


        self.history = {}
        for field in self.fields.itervalues():
            self.history[field.name] = []

        self._storage = {}
        #load up defaults
        for field in self.fields.itervalues():
            if isinstance(field, ConfigField) and not field.optional:
                value = field.initFunc(name=self.name+"." + field.name)
            else:
                value = field.default
            field.__set__(self, value)

        #apply first batch of overides from the provided storage
        if storage is not None:
            for k,v in storage.iteritems():
                target, name = self._getTargetConfig(k)
                target.fields[name].__set__(target, v)

    def load(self, filename):
        f = open(filename, 'r')
        config = self
        exec(f.read())
        f.close()

    def save(self, filename):
        f = open(filename, 'w')
        for field in self.fields:
            f.write("config.%s=%s;\n"%(field, repr(self._storage[field])))
        f.close()
        

    def override(self, dict_):
        """
        Update fields with overrides given as a dictionary.

        Dictionary keys of the form 'foo.bar' may be used to override nested entries.
        """
        for k, v in dict_.iteritems():
            target, name = self._getTargetConfig(k)
            target.fields[name].__set__(target, v)

    def validate(self):
        """
        Validate the Config and fill any non-trivial defaults.

        The base class implementation performs type checks on all fields, recurses into
        nested Config instances, and does any simple validation defined by passing
        "check" callables to the field constructors.
        This should be called by derived classes even if they do more complex validation.
        """
        for field in self.fields.itervalues():
            value = self._storage[field.name]
            fullname = self.name + "." + field.name
            if not field.optional and value is None:
                raise ValueError("Field '%s' cannot be None"%fullname)

            if isinstance(value, Config):                
                try:
                    value.validate()
                except Exception, e:
                    raise ValueError("Config %s failed comlex validation: %s"%(fullname, str(e)))
            elif value is not None:
                try:
                    self._storage[field.name]=field.dtype(value)
                except Exception, e:
                    msg = "Incorrect type for field '%s' ('%s' is not a subclass of '%s')"%\
                          (fullname, str(value), field.dtype)
                    raise ValueError(msg)

            if field.check is not None:
                if not field.check(value):
                    raise ValueError("%s '%s' failed simple validation: '%s'" % (field.__class__.__name__, fullname, str(value)))

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
                ValueError("Could not find target '%s' in Config %s"%(path, self.name))
        
        name = fieldname[dot+1:]
        if not name in target.fields:
            raise ValueError("Config does not include field '%s'"%fieldname)

        return target, name

    def __str__(self):
        return str(self.__class__) + ":" + str(self._storage)

    def __repr__(self):
        return str(self._storage)


class ChoiceCheck(object):
    def __init__(self, choices, check=None):
        self.choices=choices
        self.check = check

    def __call__(self, x):
        if x not in self.choices:
            return False

        if self.check is not None:
            return self.check(x)

        return True

class ChoiceField(Field):
    def __init__(self, dtype, doc, allowed, default=None, check=None, optional=True, callback=None):
        if optional: 
            allowed[None]="Field is optional"

        if len(allowed)==0:
            raise ValueError("ChoiceFields must have at least one allowed value")
        
        doc += "Allowed values:\n"
        for choice in allowed:
            doc += "\t%s\t%s\n"%(str(choice), allowed[choice])
            if choice is not None and not isinstance(choice, dtype):
                raise ValueError("Allowed value %s is not a subclass of type %s"%(str(choice), dtype))

        choiceCheck = ChoiceCheck(allowed,check) 
        Field.__init__(self, dtype, doc, default=default, check=choiceCheck, optional=optional, callback=callback)


class ConfigField(Field):
    def __init__(self, configType, doc, initFunc=None, check=None, optional=True, callback=None):
        if not issubclass(configType, Config):
            raise TypeError("configType='%s' is not a subclass of Config)"%str(configType))

        Field.__init__(self, dtype=configType, doc=doc, default=None, check=check, 
                optional=optional, callback=callback)
        self.initFunc=initFunc if initFunc is not None else configType

    def __set__(self, instance, value):
        fullname = instance.name + "." + self.name
        if isinstance(value, self.dtype):            
            value = value.__class__(name=fullname, storage=value)
        else:
            value = self.dtype(name=fullname, storage=value)
        instance._storage[self.name]=value
        instance.setHistory(self.name)

class ListCheck(object):
    def __init__(self, itemType, optional=True, listCheck=None, itemCheck=None, length=None, minLength=None, maxLength=None):
        self.itemType=itemType
        self.optional=optional
        self.listCheck=listCheck
        self.itemCheck=itemCheck
        self.length = length
        self.minLength=minLength
        self.maxLength=maxLength

    def _checkLength(self, value):
        if value is None:
            return self.optional

        lenValue =len(value)
        if (self.length is not None and not lenValue == self.length) or \
               (self.minLength is not None and lenValue < self.minLength) or \
               (self.maxLength is not None and lenValue > self.maxLength):
            return False

        return True

    def __call__(self, value):
        if not self._checkLength(value):
            print "here length"
            return False

        if self.listCheck is not None:
            if not self.listCheck(value):
                print "here listcheck"
                return false

        if value is not None:
            for i, v in enumerate(value):
                if isinstance(v, Config):
                    v.validate()
                else:
                    try:
                        value[i] = self.itemType(v)
                    except:
                        print "here itemtype"
                        return False

                if self.itemCheck is not None and not self.itemCheck(value[i]):
                    print "here itemcheck"
                    return False
        return True

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
        self.value[i] =x
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
        x = self.value.pop(i)
        self.owner.setHistory(self.name)
        return x

    def remove(x):
        self.value.remove(x)
        self.owner.setHistory(self.name)
    
    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)

class ListField(Field):
    def __init__(self, itemType, doc, default=None, optional=True, callback=None,
            listCheck=None, itemCheck=None, length=None, minLength=None, maxLength=None):        
        check = ListCheck(itemType, optional=optional, listCheck=listCheck, itemCheck=itemCheck, 
                length=length, minLength=minLength, maxLength=maxLength)
        Field.__init__(self, list, doc, default=default, optional=optional, check=check, callback=callback)
        self.itemType=itemType
    
    def __get__(self, instance, dtype=None):
        return ListExpr(self, instance)


class ConfigListExpr(ListExpr):
    def __setitem__(self, k, x):  
        if isinstance(k, slice):
            start, stop, step = k.indices(len(self))
            fullname = self.owner.name + "." + self.name        
            for i, xi in zip(range(start, stop, step), x):
                itemname = "%s[%d]"%(fullname, i)
                if isinstance(xi, self.dtype):            
                    x[i] = xi.__class__(name=itemname, storage=xi)
                else:
                    x[i] = self.dtype(name=itemname, storage=xi)
        ListExpr.__setitem__(self, k, x)
        self.owner.setHistory(self.name)

class ConfigListField(ListField, ConfigField):
    def __init__(self, configType, doc, default=None, optional=True, callback=None,
            listCheck=None, itemCheck=None, length=None, minLength=None, maxLength=None):
        if not issubclass(configType, Config):
            raise TypeError("configType='%s' is not a subclass of Config)"%str(configType))

        ListField.__init__(self, configType, doc, default=default, optional=optional, callback=callback,
                listCheck=listCheck, itemCheck=itemCheck, length=length, minLength=minLength, maxLength=maxLength)

        
    def __set__(self, instance, value):
        fullname = instance.name + "." + self.name
        if value is not None:
            for i, x in enumerate(value):
                itemname = "%s[%d]"%(fullname, i)
                if isinstance(x, self.itemtype):            
                    value[i] = x.__class__(name=itemname, storage=x)
                else:
                    value[i] = self.itemtype(name=itemname, storage=x)
        instance._storage[self.name]= value
        instance.setHistory(self.name)
        
    def __get__(self, instance, dtype=None):
        return ConfigListExpr(self, instance)
