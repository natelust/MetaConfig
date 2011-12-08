import traceback
import lsst.pex.logging
from lsst.pex.logging import Log
import sys

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
        self.log = lsst.pex.logging.Log(lsst.pex.logging.Log.getDefaultLog(), "lsst.pex.policy");
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

    def __init__(self, dtype, doc, default=None, check=None, optional=True):
        """Initialize a Field.
        
        dtype ------ Data type for the field.  If this not a subclass of Config, any values
                     will be coerced using 'dtype(value)' during 
        doc -------- Documentation for the field.
        default ---- A simple default for the field.  If the default must be computed, just
                     leave this as None and set the default as part of validate().
        check ------ A simple callable to be called with the field value that returns False if the value
                     is invalid.  More complex multi-field validation can be written as part of the
                     validate() method; this will be ignore if set to None.
        """
        self.dtype = dtype
        self.doc = doc
        self.__doc__ = doc
        self.default = default
        self.check = check
        self.optional=optional

    def __get__(self, instance, dtype=None):
        return instance._storage[self.name]

    def __set__(self, instance, value):
        instance._set(self.name, value)

class ConfigField(Field):
    def __init__(self, dtype, doc, default=None, check=None, optional=True):
        Field.__init__(self, dtype=dtype, doc=doc, default=None, check=check, optional=optional)
        self.default=default if default is not None else dtype

class ListFieldCheck():
    def __init__(self, dtype, optional=True, listCheck=None, itemCheck=None, length=None, minLength=None, maxLength=None):
        self.dtype=dtype
        self.option=optional
        self.listCheck=listCheck
        self.itemCheck=itemCheck
        self.length = length
        self.minLength=minLength
        self.maxLength=maxLength

    def _checkLength(self, value):
        if value is None:
            return self.optional

        result = True
        lenValue =len(value)
        if length is not None:
            result &= (lenValue == length)
        if minLength is not None:
            result &= (lenValue >= minLength)
        if maxLength is not None:
            result &= (lenValue <= maxLength)
        return result

    def __call__(self, value):
        if not self._checkLength(value):
            return false

        if self.listCheck is not None:
            if not self.listCheck(value):
                return false

        if value is not None:
            for v in value:
                if not isinstance(v, self.dype):
                    return false
                if self.itemCheck is not None:
                    if not itemCheck(v):
                        return false
                
class ListField(Field):
    def __init__(self, dtype, doc, default=None, optional=True, listCheck=None, itemCheck=None, length=None, minLength=None, maxLength=None):
        check = ListFieldCheck(dtype, optional, listCheck, itemCheck, length, minLength, maxLength)
        Field.__init__(self, list, doc, default=default, optional=optional, check=check)

    def __setitem__(self, key, value):
        print "going through listField __setitem__"
        raise RuntimeError("ListFields are immutable")

    def __set__(self, instance, value):
        if issubclass(self.check.dtype, Config):
            value = [self.check.dtype(storage=v, name=instance.fieldnames[self.name] + "["+i+"]") for i,v in enumerate(value)]


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
            self._getTargetConfig(key, create=False)
        except:
            return False

        return True

    def __init__(self, storage=None, name=None):
        """Initialize the Config.

        Pure-Python control objects will just use the default constructor, which
        sets up a simple Python dict as the storage for field values.

        Any other object with __getitem__, __setitem__, and __contains__ may be used
        as storage, and is expected to already contain the necessary items if it is
        passed to the constructor.  This is used to support C++ control objects,
        which will implement a storage interface to C++ data members in SWIG.
        """

        self.history = {}
        self.fieldnames = {}
        for field in self.fields.itervalues():
            self.history[field.name] = []
            self.fieldnames[field.name] = field.name if name is None else name + "." + field.name

        self._storage = {}
        if storage is not None:
            for k,v in storage.iteritems():
                self._set(k, v)
        for field in self.fields.itervalues():
            if not field.name in self._storage:
                if isinstance(field, ConfigField) and not field.optional:
                    self._set(field.name, field.default(storage=None, name=name))
                else:
                    self._set(field.name, field.default)

    def save(self, filename):
        f = open(filename, 'w')
        f.write(str(self._storage))
        f.close()
        

    def override(self, dict_):
        """
        Update fields with overrides given as a dictionary.

        Dictionary keys of the form 'foo.bar' may be used to override nested entries.
        """
        for k, v in dict_.iteritems(): 
            self._set(k, v)

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
            fullname = self.fieldnames[field.name]
            if not field.optional and value is None:
                raise ValueError("Field '%s' cannot be None"%fullname)

            if issubclass(field.dtype, Config) and value is not None:                
                try:
                    value.validate()
                except Exception, e:
                    raise ValueError("Config %s failed comlex validation: %s"%(fullname, str(e)))
            elif value is not None:
                try:
                    self.storage_[field.name]=field.type(value)
                except Exception, e:
                    msg = "Incorrect type for field '%s' ('%s' is not a subclass of '%s')"%\
                          (fullname, str(value), field.dtype)
                    raise ValueError(msg)

            if field.check is not None:
                if not field.check(value):
                    raise ValueError("Field '%s' failed simple validation: '%s'" % (fullname, str(value)))

    def getHistory(self, fieldname, limit=0):
        target, name = self._getTargetConfig(fieldname)
        return target.history[name][-limit:]

    
    def _getTargetConfig(self, fieldname, create=False):
        path=fieldname.split(".")
        target = self      
        for name in path[:-1]:            
            if not name in target.fields:
                raise KeyError("Config does not include field '%s'"%fieldname)
            elif not issubclass(target.fields[name].dtype, Config):
                raise ValueError("Field %s is not a subclass of Config."%target.fieldnames[name])
            elif target._storage[name] is None:
                # trying to set a nonexistent sub-config.                
                if not create:
                    raise ValueError("Config has no value for field '%s'"%target.fieldnames[name])
                # default construct target
                target._storage[name] = target.fields[name].default(storage=None, name=target.fieldnames[name])
            #move to subpolicy
            target = target._storage[name]

        name = path[-1]
        if not name in target.fields:
            raise KeyError("Config does not include field '%s'"%fieldname)

        return target, name

    def _set(self, fieldname, value):
        target, name = self._getTargetConfig(fieldname, create=True)
        field = target.fields[name]
        fullname = target.fieldnames[name]
        def setSingleValue(target, field, value, index=None):
            fullname = target.fieldnames[name]
            if index is not None:
                fullname += "[%d]"%index

            try:
                if value is None:
                    if index is None:
                        target._storage[field.name]=None
                    else:
                        target._storage[field.name][index]=None
                elif issubclass(field.dtype, Config):
                    if index is None:
                        target._storage[name] = field.dtype(storage=value, name=fullname)
                    else:
                        target._storage[name][index] = field.dtype(storage=value, name=fullname)
                else:                    
                    if index is None:
                        target._storage[name] = field.dtype(value)
                    else:
                        target._storage[name][index] = field.dtype(value)

            except Exception, e: 
                print e
                msg = "Incorrect type for field '%s' ('%s' is not a subclass of '%s')"%(fullname, str(value), field.dtype)
                raise ValueError(msg)

        if isinstance(field, ListField):
            for i, v in enumerate(value):
                setSingleValue(target, field, v, i)
        else:
            setSingleValue(target, field, value)

        target.history[name].append((value, traceback.extract_stack()[:-2]))
        self.log.log(Log.DEBUG, "Field %s := %s"%(fullname, str(value)))

    def __str__(self):
        return str(self.__class__) + ":" + str(self._storage)

    def __repr__(self):
        return str(self._storage)
