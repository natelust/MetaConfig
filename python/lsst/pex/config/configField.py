from .config import Config, Field, FieldValidationError, _joinNamePath, _typeStr
import traceback

__all__ = ["ConfigField"]

class ConfigField(Field):
    """
    Defines a field which is itself a Config.

    The behavior of this type of field is much like that of the base Field type.

    Note that dtype must be a subclass of Config.

    If default=None, the field will default to a default-constructed 
    instance of dtype.

    Additionally, to allow for fewer deep-copies, assigning an instance of 
    ConfigField to dtype itself, is considered equivalent to assigning a 
    default-constructed sub-config. This means that the argument default can be 
    dtype, as well as an instance of dtype.

    Assigning to ConfigField will update all of the fields in the config.
    """

    def __init__(self, doc, dtype, default=None, check=None):
        if not issubclass(dtype, Config):
            raise ValueError("dtype=%s is not a subclass of Config" % \
                    _typeStr(dtype))
        if default is None:
            default = dtype
        source = traceback.extract_stack(limit=2)[0]
        self._setup( doc=doc, dtype=dtype, default=default, check=check, 
                optional=False, source=source)
  
    def __get__(self, instance, owner=None):
        if instance is None or not isinstance(instance, Config):
            return self
        else:
            value = instance._storage.get(self.name, None)
            if value is None:
                at = traceback.extract_stack()[:-1]+[self.source]
                self.__set__(instance, self.default, at=at, label="default")
            return value

    def __set__(self, instance, value, at=None, label="assignment"):
        if instance._frozen:
            raise FieldValidationError(self, instance, \
                    "Cannot modify a frozen Config")
        name = _joinNamePath(prefix=instance._name, name=self.name)

        if value != self.dtype and type(value) != self.dtype:
            msg = "Value %s is of incorrect type %s. Expected %s" %\
                    (value, _typeStr(value), _typeStr(self.dtype))
            raise FieldValidationError(self, instance, msg)
        
        if at is None:
            at = traceback.extract_stack()[:-1]

        oldValue = instance._storage.get(self.name, None)
        if oldValue is None:
            if value == self.dtype:
                instance._storage[self.name] = self.dtype(
                        __name=name, __at=at, __label=label)
            else:
                instance._storage[self.name] = self.dtype(
                        __name=name, __at=at, __label=label, **value._storage)
        else:
            if value == self.dtype:
                value = value()
            oldValue.update(__at=at, __label=label, **value._storage)
        history = instance._history.setdefault(self.name, [])
        history.append(("config value set", at, label))

    def rename(self, instance):
        value = self.__get__(instance)
        value._rename(_joinNamePath(instance._name, self.name))
        
    def save(self, outfile, instance):
        value = self.__get__(instance)
        value._save(outfile)

    def freeze(self, instance):
        value = self.__get__(instance)
        value.freeze()

    def toDict(self, instance):
        value = self.__get__(instance)
        return value.toDict()
    
    def validate(self, instance):
        value = self.__get__(instance)
        value.validate()

        if self.check is not None and not self.check(value):
            msg = "%s is not a valid value"%str(value)
            raise FieldValidationError(self, instance, msg)


