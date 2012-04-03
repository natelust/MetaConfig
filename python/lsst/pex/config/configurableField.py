from .config import Config, Field, _joinNamePath, _typeStr
import traceback, copy

class ConfigurableInstance(object):
    def __initValue(self, at, label):
        """
        if field.default is an instance of ConfigClass, custom construct
        _value with the correct values from default.
        otherwise call ConfigClass constructor
        """    
        if self._value is None:
            name=_joinNamePath(self._config._name, self._field.name)
            if type(self._field.default)==self._ConfigClass:
                storage = self._field.default._storage
            else:
                storage = {}
            value = self._ConfigClass(__name=name, __at=at, __label=label, **storage)
            object.__setattr__(self, "_value", value)
        return self._value

    def __init__(self, config, field, at=None, label="default"):
        object.__setattr__(self, "_config", config)
        object.__setattr__(self, "_field", field)
        object.__setattr__(self, "__doc__", config)
        object.__setattr__(self, "_target", field.target)
        object.__setattr__(self, "_ConfigClass",field.ConfigClass)
        object.__setattr__(self, "_value", None)
 
        if at is None:
            at = traceback.extract_stack()[:-1]
        at += [self._field.source]
        self.__initValue(at, label)

        history = config._history.setdefault(field.name, [])
        history.append(("Targeted and initialized from defaults", at, label))

    """
    Read-only access to the targeted configurable
    """
    target = property(lambda x: x._target)

    def apply(self):        
        return self._target(self._value)
    
    """
    Target a new configurable and ConfigClass
    """
    def retarget(self, target, ConfigClass=None):
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, "Cannot modify a frozen Config")
        if not hasattr(target, '__call__'):
            raise FieldValidationError(self._field, self._config, "target must be callable")

            
        if ConfigClass is None:
            try:
                ConfigClass = target.ConfigClass
            except:
                raise FieldValidationError(self._field, self._config,
                        "target has no attribute ConfigClass.")
        if not issubclass(ConfigClass, Config):
            raise FieldValidationError(self._field, self._config,
                    "ConfigClass if of incorrect type %s. ConfigClass must be a subclass of Config"%\
                    _typeStr(ConfigClass))
        if hasattr(ConfigClass, 'apply') or hasattr(ConfigClass, 'retarget') or \
                hasattr(ConfigClass, 'target'):
            raise FieldValidationError(self._field, self._config, 
                    "ConfigClass must not have attributes 'apply', 'target', or 'retarget'")
        at = traceback.extract_stack()[:-1]
        label="retarget"
        self._target = target
        if ConfigClass != self._ConfigClass:
            self._ConfigClass=ConfigClass
            self.__initValue(at, label)

        history = self._config._history.setdefault(self._field.name, [])
        history.append(("Retargeted", at, label))

    def __getattr__(self, name, at=None, label="default"):
        """
        Pretend to be an isntance of  ConfigClass. 
        Attributes defiend by ConfigurableInstance will shadow those defined in ConfigClass
        """
        if at is None:
            at = traceback.extract_stack()[:-1]
            
        return getattr(self._value, name)

    def __setattr__(self, name, value, at=None, label="assignment"):
        """
        Pretend to be an isntance of  ConfigClass. 
        Attributes defiend by ConfigurableInstance will shadow those defined in ConfigClass
        """
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, "Cannot modify a frozen Config")
        
        if name in self.__dict__: 
            #attribute exists in the ConfigurableInstance wrapper 
            object.__setattr__(self, name, value)
        else:
            if at is None:
                at = traceback.extract_stack()[:-1]
            self._value.__setattr__(name, value, at=at, label=label)

    def __delattr__(self, name, at=None, label="delete"):
        """
        Pretend to be an isntance of  ConfigClass. 
        Attributes defiend by ConfigurableInstance will shadow those defined in ConfigClass
        """
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, "Cannot modify a frozen Config")
        
        try:
            #attribute exists in the ConfigurableInstance wrapper 
            object.__delattr__(self, name)
        except AttributeError:
            if at is None:
                at = traceback.extract_stack()[:-1]
            self._value.__delattr__(name, at=at, label=label)


class ConfigurableField(Field):
    """
    A variant of a ConfigField which has a known configurable target

    Behaves just like a ConfigField except that it can be 'retargeted' to point
    at a different configurable. Further you can 'apply' to construct a fully
    configured configurable.


    """

    def __init__(self, doc, target, ConfigClass=None, default=None, check=None):
        """
        @param target is the configurable target. Must be callable, and the first
                parameter will be the value of this field
        @param ConfigClass is the class of Config object expected by the target.
                If not provided by target.ConfigClass it must be provided explicitly in this argument
        """
        if ConfigClass is None:
            try:
                ConfigClass=target.ConfigClass
            except:
                raise AttributeError("ConfigurableField constructor argument 'target' must define attribute"\
                        "'ConfigClass' when 'configClass' is None")
        if not issubclass(ConfigClass, Config):
            raise TypeError("ConfigClass if of incorrect type %s. ConfigClass must be a subclass of Config"%\
                    _typeStr(ConfigClass))
        if not hasattr(target, '__call__'):
            raise ValueError ("target must be callable")
        if default is None: 
            default=ConfigClass
        if default != ConfigClass and type(default) != ConfigClass:
            raise TypeError("default argument is of incorrect type %s. Expected %s"%\
                    (_typeStr(default), _typeStr(ConfigClass)))

        source = traceback.extract_stack(limit=2)[0]
        self._setup(doc=doc, dtype=ConfigurableInstance, default=default, \
                check=check, optional=False, source=source)
        self.target = target
        self.ConfigClass = ConfigClass

    def __getOrMake(self, instance, at=None, label="default"):
        value = instance._storage.get(self.name, None)
        if value is None:
            if at is None:
                at = traceback.extract_stack()[:-2]
            value = ConfigurableInstance(instance, self, at=at, label=label)
            instance._storage[self.name]=value
        return value

    def __get__(self, instance, owner=None, at=None, label="default"):
        if instance is None or not isinstance(instance, Config):
            return self
        else:
            return self.__getOrMake(instance, at=at, label=label)

    def __set__(self, instance, value, at=None, label="assignment"):
        if instance._frozen:
            raise FieldValidationError(self, instance, "Cannot modify a frozen Config")
        if at is None: 
            at = traceback.extract_stack()[:-1]
        oldValue = self.__getOrMake(instance, at=at)

        if isinstance(value, ConfigurableInstance):
            oldValue._target = value._target
            storage = value._value._storage 
            if value._ConfigClass != oldValue._ConfigClass:
                oldValue._value = value._ConfigClass(
                    __name=_joinNamePath(instance._name, self.name),
                    __at=at, __label=label, 
                    **storage)
            else:
                oldValue._value.update(__at=at, __label=label, **storage)
            oldValue._ConfigClass = value._ConfigClass
            history.append(("ConfigurableField retargeted", at, label))
        elif type(value)==oldValue._ConfigClass:
            oldValue._value.update(__at=at, __label=label, **value._storage)
        elif value == oldValue._ConfigClass:
            value = oldValue._ConfigClass()
            oldValue._value.update(__at=at, __label=label, **value._storage)
        else:
            msg = "Value %s if of incorrect type %s. Expected %s" %\
                    (value, _typeStr(value), _typeStr(oldValue._ConfigClass))
            raise FieldValidationError(self, instance, msg)
    
    def rename(self, instance):
        fullname = _joinNamePath(instance._name, self.name)
        value = self.__getOrMake(instance)._value
        value._rename(fullname)
        
    def save(self, outfile, instance):
        value = self.__getOrMake(instance)._value
        value._save(outfile)

    def freeze(self, instance):
        value = self.__getOrMake(instance)._value
        value.freeze()

    def toDict(self, instance):
        value = self.__get__(instance)._value
        return value.toDict()
    
    def validate(self, instance):
        value = self.__get__(instance)._value
        value.validate()

        if self.check is not None and not self.check(value):
            msg = "%s is not a valid value"%str(value)
            raise FieldValidationError(self, instance, msg)

    def __deepcopy__(self, memo):
        """Customize deep-copying, because we always want a reference to the original typemap.

        WARNING: this must be overridden by subclasses if they change the constructor signature!
        """
        return type(self)(doc=self.doc, target=self.target, ConfigClass=self.ConfigClass, 
                default=copy.deepcopy(self.default))
