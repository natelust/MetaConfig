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

import io
import traceback
import sys
import math
import collections
import copy

__all__ = ("Config", "Field", "FieldValidationError")

def _joinNamePath(prefix=None, name=None, index=None):
    """
    Utility function for generating nested configuration names
    """
    if not prefix and not name:
        raise ValueError("Invalid name: cannot be None")
    elif not name:
        name = prefix
    elif prefix and name:
        name = prefix + "." + name

    if index is not None:
        return "%s[%r]"%(name, index)
    else:
        return name

def _autocast(x, dtype):
    if dtype==float and type(x)==int:
        return float(x)
    return x

def _typeStr(x):
    if hasattr(x, '__module__') and hasattr(x, '__name__'):
        xtype = x
    else:
        xtype = type(x)
    if xtype.__module__ == '__builtin__':
        return xtype.__name__
    else:
        return "%s.%s"%(xtype.__module__, xtype.__name__)

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
        self._source = traceback.extract_stack(limit=2)[0]
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
    def __init__(self, field, config, msg):
        self.fieldType = type(field)
        self.fieldName = field.name
        self.fullname  = _joinNamePath(config._name, field.name)
        self.history = config.history.setdefault(field.name, [])
        self.fieldSource = field.source
        self.configSource = config._source
        error="%s '%s' failed validation: %s\n"\
                "For more information read the Field definition at:\n%s"\
                "And the Config definition at:\n%s"%\
              (self.fieldType.__name__, self.fullname, msg, 
                      traceback.format_list([self.fieldSource])[0],
                      traceback.format_list([self.configSource])[0])
        ValueError.__init__(self, error)


class Field(object):
    """A field in a a Config.

    Instances of Field should be class attributes of Config subclasses:
    Field only supports basic data types (int, float, complex, bool, str)

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
            raise ValueError("Unsupported Field dtype %s"%_typeStr(dtype))
        source = traceback.extract_stack(limit=2)[0]
        self._setup(doc=doc, dtype=dtype, default=default, check=check, optional=optional, source=source)
        

    def _setup(self, doc, dtype, default, check, optional, source):
        self.dtype = dtype
        self.doc = doc
        self.__doc__ = doc
        self.default = default
        self.check = check
        self.optional = optional
        self.source = source

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
        if not self.optional and value is None:
            raise FieldValidationError(self, instance, "Required value cannot be None")
   
    def freeze(self, instance):
        pass

    def _validateValue(self, value):
        """
        Validate a value that is not None
    
        This is called from __set__
        This is not part of the Field API. However, simple derived field types
            may benifit from implementing _validateValue
        """
        if value is None:
            return

        if not isinstance(value, self.dtype):
            msg = "Value %s is of incorrect type %s. Expected type %s"%\
                    (value, _typeStr(value), _typeStr(self.dtype))
            raise TypeError(msg)
        if self.check is not None and not self.check(value):
            msg = "Value %s is not a valid value"%str(value)
            raise ValueError(msg)

    def save(self, outfile, instance):
        """
        Saves an instance of this field to file.
        This is invoked by the owning config object, and should not be called directly
        """
        value = self.__get__(instance)
        fullname = _joinNamePath(instance._name, self.name)
        if isinstance(value, float) and (math.isinf(value) or math.isnan(value)):
            # non-finite numbers need special care
            print >> outfile, "%s=float('%r')"%(fullname, value)
        else:
            print >> outfile, "%s=%r"%(fullname, value)
    
    def toDict(self, instance):
        """
        Convert the field value so that it can be set as the value of an item in a dict
        """
        return self.__get__(instance)

    def __get__(self, instance, owner=None, at=None, label="default"):
        if instance is None or not isinstance(instance, Config):
            return self
        else:
            return instance._storage[self.name]

    def __set__(self, instance, value, at=None, label='assignment'):
        if instance._frozen:
            raise FieldValidationError(self, instance, "Cannot modify a frozen Config")

        history = instance._history.setdefault(self.name, [])
        if value is not None:
            value = _autocast(value, self.dtype)
            try:
                self._validateValue(value)
            except BaseException, e:
                raise FieldValidationError(self, instance, e.message)
        
        instance._storage[self.name] = value
        if at is None:
            at = traceback.extract_stack()[:-1]
        history.append((value, at, label))

    def __delete__(self, instance, at=None, label='deletion'):
        if at is None:
            at = traceback.extract_stack()[:-1]
        self.__set__(instance, None, at=at, label=label)
   

class RecordingImporter(object):
    """An Importer (for sys.meta_path) that records which modules are being imported

    This class makes no effort to do any importing itself.
    """
    def __init__(self):
        """Create and install the Importer"""
        self._modules = set()
        self.origMetaPath = sys.meta_path
        sys.meta_path = sys.meta_path + [self]

    def uninstall(self):
        """Uninstall the Importer"""
        sys.meta_path = self.origMetaPath

    def find_module(self, fullname, path=None):
        """Called as part of the 'import' chain of events.

        We return None because we don't do any importing.
        """
        self._modules.add(fullname)
        return None

    def getModules(self):
        """Return the set of modules that were imported."""
        return self._modules

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
        name=kw.pop("__name", None)
        at=kw.pop("__at", traceback.extract_stack()[:-1])
        label=kw.pop("__label", "default")

        instance = object.__new__(cls)
        instance._frozen=False
        instance._name=name
        instance._storage = {}
        instance._history = {}
        instance._imports = set()
        # load up defaults
        for field in instance._fields.itervalues():           
            instance._history[field.name]=[]
            field.__set__(instance, field.default, at=at+[field.source], label="default")
        # set custom default-overides
        instance.setDefaults()
        # set constructor overides 
        instance.update(__at=at, **kw)
        return instance

    def __reduce__(self):
        """Reduction for pickling (function with arguments to reproduce).

        We need to condense and reconstitute the Config, since it may contain lambdas
        (as the 'check' elements) that cannot be pickled.
        """
        stream = io.BytesIO()
        self.saveToStream(stream)
        return (unreduceConfig, (self.__class__, stream.getvalue()))

    def setDefaults(self):
        """
        Derived config classes that must compute defaults rather than using the 
        Field defaults should do so here. 
        To correctly use inherited defaults, implementations of setDefaults() 
        must call their base class' setDefaults()
        """
        pass
            
    def update(self, **kw):
        at=kw.pop("__at", traceback.extract_stack()[:-1])
        label = kw.pop("__label", "update")

        for name, value in kw.iteritems():            
            try:
                field = self._fields[name]
                field.__set__(self, value, at=at, label=label)
            except KeyError, e:
                raise KeyError("No field of name %s exists in config type %s"%(name, _typeStr(self)))

    def load(self, filename, root="root"):
        """
        modify this config in place by executing the python code in the 
        given file.

        The file should modify a Config named root

        For example:
            root.myField = 5
        """
        importer = RecordingImporter()
        local = {root:self}
        execfile(filename, {}, local)
        self._imports.update(importer.getModules())
        importer.uninstall()
 
    def loadFromStream(self, stream, root="root"):
        """
        Modify this config in place by executign the python code in the
        provided stream.

        The stream should modify a Config named 'root', e.g.: root.myField = 5
        """
        importer = RecordingImporter()
        local = {root: self}
        exec stream in {}, local
        self._imports.update(importer.getModules())
        importer.uninstall()

    def save(self, filename, root="root"):
        """
        Generates a python script at the given filename, which, when loaded,
        reproduces this Config.

        @param filename [in] name of file to write to
        @param root [in] name to use for the root config variable
            If not "root", must match what is used in load())
        """
        with open(filename, 'w') as outfile:
            self.saveToStream(outfile, root)

    def saveToStream(self, outfile, root="root"):
        """
        Generates a python script to the given open file object, which, when
        loaded, reproduces this Config.

        @param outfile [inout] open file object to write to
        @param root [in] name to use for the root config variable
            If not "root", must match what is used in load())
        """
        tmp = self._name
        self._rename(root)
        try:
            configType = type(self)
            typeString = _typeStr(configType)
            print >> outfile, "import %s"%(configType.__module__) 
            print >> outfile, "assert(type(%s)==%s)"%(root, typeString) 
            self._save(outfile)
        finally:
            self._rename(tmp)

    def freeze(self):
        self._frozen=True
        for field in self._fields.itervalues():
            field.freeze(self)

    def _save(self, outfile):
        """
        Internal use only. Save this Config to file object
        """
        for imp in self._imports:
            if sys.modules[imp] is not None:
                print >> outfile, "import %s" % imp
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
   
    def formatHistory(self, name, **kwargs):
        import lsst.pex.config.history as pexHist
        return pexHist.format(self, name, **kwargs)

    """
    Read-only history property
    """
    history = property(lambda x: x._history)

    def __setattr__(self, attr, value, at=None, label="assignment"):
        if attr in self._fields:
            if at is None:
                at=traceback.extract_stack()[:-1]
            # This allows Field descriptors to work.
            self._fields[attr].__set__(self, value, at=at, label=label)
        elif hasattr(getattr(self.__class__, attr, None), '__set__'):
            # This allows properties and other non-Field descriptors to work.
            return object.__setattr__(self, attr, value)
        elif attr in self.__dict__ or attr in ("_name", "_history", "_storage", "_frozen", "_imports"):
            # This allows specific private attributes to work.
            self.__dict__[attr] = value
        else:
            # We throw everything else.
            raise AttributeError("%s has no attribute %s"%(_typeStr(self), attr))

    def __delattr__(self, attr, at=None, label="deletion"):
        if attr in self._fields:
            if at is None:
                at=traceback.extract_stack()[:-1]
            self._fields[attr].__delete__(self, at=at, label=label)
        else:
            object.__delattr__(self, attr)
            
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
            _typeStr(self), 
            ", ".join("%s=%r" % (k, v) for k, v in self.toDict().iteritems() if v is not None)
            )


def unreduceConfig(cls, stream):
    config = cls()
    config.loadFromStream(stream)
    return config

