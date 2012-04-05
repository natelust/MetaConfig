from .config import Field, FieldValidationError, _typeStr, _autocast
import traceback, copy
import collections

__all__ = ["ListField"]

class List(collections.MutableSequence):
    def __appendHistory(self):
        traceStack = traceback.extract_stack()[:-2]
        self.__history.append((list(self.__value), traceStack))

    def __init__(self, config, field, value):
        self._field = field
        self._config = config
        if value is not None:
            try:
                self.__value = [_autocast(xi, self._field.itemtype) for xi in value]
            except:
                msg = "Value %s is of incorrect type %s. Expected a sequence"%(value, _typeStr(value))
                raise FieldValidationError(self._field, self._config, msg)
        else:
            self.__value = []

        self.__history = self._config._history.setdefault(self._field.name, [])

    """
    Read-only history
    """
    history = property(lambda x: x._history)   

    def __contains__(self, x): return x in self.__value

    def __len__(self): return len(self.__value)

    def __setitem__(self, i, x):
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, \
                    "Cannot modify a frozen Config")

        if isinstance(i, slice):
            k, stop, step = i.indices(len(self))
            for j, xj in enumerate(x):
                xj=_autocast(xj, self._field.itemtype)
                try:
                    self._field.validateItem(k, xj)
                except BaseException, e:
                    raise FieldValidationError(self._field, self._config, e.message)
                x[j]=xj
                k += step
        else:
            x = _autocast(x, self._field.itemtype)
            try:
                self._field.validateItem(i, x)
            except BaseException, e:
                raise FieldValidationError(self._field, self._config, e.message)
            
        self.__value[i]=x
        self.__appendHistory()
        
    def __getitem__(self, i): return self.__value[i]
    
    def __delitem__(self, i):
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, \
                    "Cannot modify a frozen Config")
        del self.__value[i]
        self.__appendHistory()

    def __iter__(self): return iter(self.__value)

    def insert(self, i, x): self[i:i]=[x]

    def __repr__(self): return repr(self.__value)

    def __str__(self): return str(self.__value)

    def __eq__(self, other):
        try:
            if len(self) != len(other):
                return False

            for i,j in zip(self, other):
                if i != j: return False
            return True
        except:
            False


class ListField(Field):
    """
    Defines a field which is a container of values of type dtype

    If length is not None, then instances of this field must match this length 
    exactly.
    If minLength is not None, then instances of the field must be no shorter 
    then minLength
    If maxLength is not None, then instances of the field must be no longer 
    than maxLength
    
    Additionally users can provide two check functions:
    listCheck - used to validate the list as a whole, and
    itemCheck - used to validate each item individually    
    """
    def __init__(self, doc, dtype, default=None, optional=False,
            listCheck=None, itemCheck=None, 
            length=None, minLength=None, maxLength=None):
        if dtype not in Field.supportedTypes:
            raise ValueError("Unsupported dtype %s"%_typeStr(dtype))
        if length is not None:
            if length <= 0:
                raise ValueError("'length' (%d) must be positive"%length)
            minLength=None
            maxLength=None
        else:
            if maxLength is not None and maxLength <= 0:
                raise ValueError("'maxLength' (%d) must be positive"%maxLength)
            if minLength is not None and maxLength is not None \
                    and minLength >=maxLength:
                raise ValueError("'maxLength' (%d) must be greater than 'minLength' (%d)"%(maxLength, minLegth))
        
        if listCheck is not None and not hasattr(listCheck, "__call__"):
            raise ValueError("'listCheck' must be callable")
        if itemCheck is not None and not hasattr(itemCheck, "__call__"):
            raise ValueError("'itemCheck' must be callable")

        source = traceback.extract_stack(limit=2)[0]
        self._setup( doc=doc, dtype=List, default=default, check=None, optional=optional, source=source)
        self.listCheck = listCheck
        self.itemCheck = itemCheck
        self.itemtype = dtype
        self.length=length
        self.minLength=minLength
        self.maxLength=maxLength
   
    def validateItem(self, i, x):
        if not isinstance(x, self.itemtype) and x is not None:
            msg="Item at position %d with value %s is of incorrect type %s. Expected %s"%\
                    (i, x, _typeStr(x), _typeStr(self.itemtype))
            raise TypeError(msg)
                
        if self.itemCheck is not None and not self.itemCheck(x):
            msg="Item at position %d is not a valid value: %s"%(i, x)
            raise ValueError(msg)

    def validateValue(self, value):
        Field.validateValue(self, value)
        if value is None:
            return

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
        
        for i, x in enumerate(value):
            self.validateItem(i,x)

    def __set__(self, instance, value, at=None, label="assignment"):
        if instance._frozen:
            raise FieldValidationError(self, instance, "Cannot modify a frozen Config")
        if at is None:
            at = traceback.extract_stack()[:-1]
        if value is not None:
            value = List(instance, self, value)
        Field.__set__(self, instance, value, at=at, label=label)

    
    def toDict(self, instance):        
        value = self.__get__(instance)        
        return list(value) if value is not None else None
