from .config import Config, Field, FieldValidationError, _typeStr, _autocast, _joinNamePath
import traceback, copy
import collections


__all__=["ConfigDictField"]

class ConfigDict(collections.MutableMapping):
    def __checkTypes(self, k, x):
        if type(k) != self._field.keytype:
            msg = "Key %r is of type %s, expected type %s"%\
                    (k, _typeStr(k), _typeStr(self._field.keytype))
            raise FieldValidationError(self._field, self._config, msg)
        if type(x) != self._field.itemtype and x != self._field.itemtype:
            msg = "Value %s at key %r is of incorrect type %s. Expected type %s"%\
                    (x, k, _typeStr(x), _typeStr(self._field.itemtype))
            raise FieldValidationError(self._field, self._config, msg)
        
    def __init__(self, config, field, value, at, label):
        self._field = field
        self._config = config
        if value is not None:
            try:
                for k in value:                
                    self.__checkTypes(k,value[k])
            except TypeError:
                msg = "Value %s is of incorrect type %s. Expected a dict-like value"%\
                        (value, _typeStr(value))
                raise FieldValidationError(field, config, msg)
        else:
            value = {}


        self.__dict = {}
        self.__history = self._config._history.setdefault(self._field.name, [])

        self.history.append(("Dict initialized", at, label))
        for k in value:
            self[k]=value[k]

    """
    Read-only history
    """
    history = property(lambda x: x.__history)   

    def __getitem__(self, k): return self.__dict[k]

    def __len__(self): return len(self.__dict)

    def __iter__(self): return iter(self.__dict)

    def __contains__(self, k): return k in self.__dict

    def __setitem__(self, k, x, at=None, label="setitem"):
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, \
                    "Cannot modify a frozen Config")
        self.__checkTypes(k,x)
        
        if at is None:
            at = traceback.extract_stack()[:-1]
        name = _joinNamePath(self._config._name, self._field.name, k)
        oldValue = self.__dict.get(k, None)
        dtype = self._field.itemtype
        if oldValue is None:            
            if x == dtype:
                self.__dict[k] = dtype(__name=name, __at=at, __label=label)
            else:
                self.__dict[k] = dtype(__name=name, __at=at, __label=label, **x._storage)
            self.history.append(("Added item at key %s"%k, at, label))
        else:
            if value == dtype:
                value = dtype()
            oldValue.update(__at=at, __label=label, **value._storage)
            self.history.append(("Modified item at key %s"%k, at, label))


    def __delitem__(self, k):
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, 
                    "Cannot modify a frozen Config")
        
        del self.__dict[k]
        self.history.append(("Removed item at key %s"%k, at, label))

    def __repr__(self): return repr(self.__dict)

    def __str__(self): return str(self.__dict)

    def _rename(self):
        for k,v in self.__dict.iteritems():
            v._rename(_joinNamePath(self._config._name, self._field.name, k))


class ConfigDictField(Field):
    """
    Defines a field which is a mapping of values

    Users can provide two check functions:
    dictCheck - used to validate the dict as a whole, and
    itemCheck - used to validate each item individually    
    """
    def __init__(self, doc, keytype, itemtype, default=None, optional=False, dictCheck=None, itemCheck=None):
        source = traceback.extract_stack(limit=2)[0]
        self._setup( doc=doc, dtype=ConfigDict, default=default, check=None, 
                optional=optional, source=source)
        if keytype not in self.supportedTypes:
            raise ValueError("'keytype' %s is not a supported type"%\
                    _typeStr(keytype))
        elif not issubclass(itemtype, Config):
            raise ValueError("'itemtype' %s is not a supported type"%\
                    _typeStr(itemtype))
        if dictCheck is not None and not hasattr(dictCheck, "__call__"):
            raise ValueError("'dictCheck' must be callable")
        if itemCheck is not None and not hasattr(itemCheck, "__call__"):
            raise ValueError("'itemCheck' must be callable")

        self.keytype = keytype
        self.itemtype = itemtype
        self.dictCheck = dictCheck
        self.itemCheck = itemCheck
  
    def rename(self, instance):
        configDict = self.__get__(instance)
        if configDict is not None:
            configDict._rename()


    def validate(self, instance):
        value = self.__get__(instance)
        if not self.optional and value is None:
            raise FieldValidationError(self, instance, "Required value cannot be None")
        elif value is None:
            return

        if self.dictCheck is not None and not self.dictCheck(value):
            msg = "%s is not a valid value"%str(value)
            raise FieldValidationError(self, instance, msg)
     
        for k, x in value.iteritems():
            x.validate()
            if self.itemCheck is not None and not self.itemCheck(x):
                msg="Item at key %r is not a valid value: %s"%(k, x)
                raise FieldValidationError(self, instance, msg)

    def __set__(self, instance, value, at=None, label="assignment"):
        if instance._frozen:
            raise FieldValidationError(self, instance, 
                    "Cannot modify a frozen Config")
        if at is None:
            at = traceback.extract_stack()[:-1]
        if value is not None:
            value = ConfigDict(instance, self, value, at, label)
        else:
            instance._history[self.name].append(("set to None", at, label))
        instance._storage[self.name] = value
    
    def toDict(self, instance):        
        configDict = self.__get__(instance) 
        if configDict is None:
            return None

        dict_ = {}
        for k, x in configDict.iteritems():
            dict_[k]=x.toDict()

        return dict_

    def save(self, outfile, instance):
        configDict = self.__get__(instance)
        fullname = _joinNamePath(instance._name, self.name)
        if configDict is None:
            print >>outfile, "%s=%r"%(fullname, configDict)
            return

        print >>outfile, "%s=%r"%(fullname, {})
        for v in configDict.itervalues():
            print >>outfile, "%s=%s()"%(v._name, _typeStr(v))
            v._save(outfile)

    def freeze(self, instance):
        configDict = self.__get__(instance)
        if configDict is not None:
            for v in configDict.itervalues():
                v.freeze()
            
