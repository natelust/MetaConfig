from .config import Config, Field, FieldValidationError, _typeStr, _autocast 
import traceback, copy
import collections

__all__=["DictField"]

class Dict(collections.MutableMapping):
    def __appendHistory(self):
        traceStack = traceback.extract_stack()[:-2]
        self.__history.append((dict(self.__value), traceStack))

    def __init__(self, config, field, value):
        self._field = field
        self._config = config
        self.__value = {}
        if value is not None:
            try:
                for k,v in value.iteritems():
                    k = _autocast(k,self._field.keytype)
                    v = _autocast(v,self._field.itemtype)
                    self.__value[k]=v
            except BaseException, e:
                msg = "Value %s is of incorrect type %s." \
                        " Expected a dict-like value"%(value, _typeStr(value))
                raise FieldValidationError(self._field, self._config, msg)

        self.__history = self._config._history.setdefault(self._field.name, [])

    """
    Read-only history
    """
    history = property(lambda x: x.__history)   

    def __getitem__(self, k): return self.__value[k]

    def __len__(self): return len(self.__value)

    def __iter__(self): return iter(self.__value)

    def __contains__(self, k): return k in self.__value

    def __setitem__(self, k, x):
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, \
                    "Cannot modify a frozen Config")
        k = _autocast(k, self._field.keytype)
        x = _autocast(x, self._field.itemtype)
        try:
            self._field.validateItem(k, x)
        except BaseException, e:
            raise FieldValidationError(self._field, self._config, e.message)

        self.__value[k]=x
        self.__appendHistory()

    def __delitem__(self, k):
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, 
                    "Cannot modify a frozen Config")
        
        del self.__value[k]
        self.__appendHistory()

    def __repr__(self): return repr(self.__value)

    def __str__(self): return str(self.__value)



class DictField(Field):
    """
    Defines a field which is a mapping of values

    Users can provide two check functions:
    dictCheck - used to validate the dict as a whole, and
    itemCheck - used to validate each item individually    
    """
    def __init__(self, doc, keytype, itemtype, default=None, optional=False, dictCheck=None, itemCheck=None):
        source = traceback.extract_stack(limit=2)[0]
        self._setup( doc=doc, dtype=Dict, default=default, check=None, 
                optional=optional, source=source)
        if keytype not in self.supportedTypes:
            raise ValueError("'keytype' %s is not a supported type"%\
                    _typeStr(keytype))
        elif itemtype not in self.supportedTypes:
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
   
    def validateItem(self, k, x):
        if type(k) != self.keytype:
            raise TypeError("Key %r is of type %s, expected type %s"%\
                    (k, _typeStr(k), _typeStr(self.keytype)))
        if type(x) != self.itemtype and x is not None:
            raise TypeError("Value %s at key %r is of incorrect type %s."
                    "Expected type %s"%\
                    (x, k, _typeStr(x), _typeStr(self.itemtype)))
        if self.itemCheck is not None and not self.itemCheck(x):
                msg="Item at key %r is not a valid value: %s"%(k, x)
                raise ValueError(msg)

    def validateValue(self, value):
        Field.validateValue(self, value)
        if value is None:
            return

        if self.dictCheck is not None and not self.dictCheck(value):
            msg = "%s is not a valid value"%str(value)
            raise ValueError(msg)
     
        for k, x in value.iteritems():
            self.validateItem(k, x)

    def __set__(self, instance, value, at=None, label="assignment"):
        if instance._frozen:
            raise FieldValidationError(self, instance, 
                    "Cannot modify a frozen Config")
        if at is None:
            at = traceback.extract_stack()[:-1]
        if value is not None:
            value = Dict(instance, self, value)
        Field.__set__(self, instance, value, at=at,label=label)
    
    def toDict(self, instance):        
        value = self.__get__(instance)        
        return dict(value) if value is not None else None
