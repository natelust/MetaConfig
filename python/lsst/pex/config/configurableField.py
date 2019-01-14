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
__all__ = ('ConfigurableInstance', 'ConfigurableField')

import copy

from .config import Config, Field, _joinNamePath, _typeStr, FieldValidationError
from .comparison import compareConfigs, getComparisonName
from .callStack import getCallStack, getStackFrame


class ConfigurableInstance:
    """A retargetable configuration in a `ConfigurableField` that proxies
    a `~lsst.pex.config.Config`.

    Notes
    -----
    ``ConfigurableInstance`` implements ``__getattr__`` and ``__setattr__``
    methods that forward to the `~lsst.pex.config.Config` it holds.
    ``ConfigurableInstance`` adds a `retarget` method.

    The actual `~lsst.pex.config.Config` instance is accessed using the
    ``value`` property (e.g. to get its documentation).  The associated
    configurable object (usually a `~lsst.pipe.base.Task`) is accessed
    using the ``target`` property.
    """

    def __initValue(self, at, label):
        """Construct value of field.

        Notes
        -----
        If field.default is an instance of `lsst.pex.config.ConfigClass`,
        custom construct ``_value`` with the correct values from default.
        Otherwise, call ``ConfigClass`` constructor
        """
        name = _joinNamePath(self._config._name, self._field.name)
        if type(self._field.default) == self.ConfigClass:
            storage = self._field.default._storage
        else:
            storage = {}
        value = self._ConfigClass(__name=name, __at=at, __label=label, **storage)
        object.__setattr__(self, "_value", value)

    def __init__(self, config, field, at=None, label="default"):
        object.__setattr__(self, "_config", config)
        object.__setattr__(self, "_field", field)
        object.__setattr__(self, "__doc__", config)
        object.__setattr__(self, "_target", field.target)
        object.__setattr__(self, "_ConfigClass", field.ConfigClass)
        object.__setattr__(self, "_value", None)

        if at is None:
            at = getCallStack()
        at += [self._field.source]
        self.__initValue(at, label)

        history = config._history.setdefault(field.name, [])
        history.append(("Targeted and initialized from defaults", at, label))

    target = property(lambda x: x._target)
    """The targeted configurable (read-only).
    """

    ConfigClass = property(lambda x: x._ConfigClass)
    """The configuration class (read-only)
    """

    value = property(lambda x: x._value)
    """The `ConfigClass` instance (`lsst.pex.config.ConfigClass`-type,
    read-only).
    """

    def apply(self, *args, **kw):
        """Call the configurable.

        Notes
        -----
        In addition to the user-provided positional and keyword arguments,
        the configurable is also provided a keyword argument ``config`` with
        the value of `ConfigurableInstance.value`.
        """
        return self.target(*args, config=self.value, **kw)

    def retarget(self, target, ConfigClass=None, at=None, label="retarget"):
        """Target a new configurable and ConfigClass
        """
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, "Cannot modify a frozen Config")

        try:
            ConfigClass = self._field.validateTarget(target, ConfigClass)
        except BaseException as e:
            raise FieldValidationError(self._field, self._config, e.message)

        if at is None:
            at = getCallStack()
        object.__setattr__(self, "_target", target)
        if ConfigClass != self.ConfigClass:
            object.__setattr__(self, "_ConfigClass", ConfigClass)
            self.__initValue(at, label)

        history = self._config._history.setdefault(self._field.name, [])
        msg = "retarget(target=%s, ConfigClass=%s)" % (_typeStr(target), _typeStr(ConfigClass))
        history.append((msg, at, label))

    def __getattr__(self, name):
        return getattr(self._value, name)

    def __setattr__(self, name, value, at=None, label="assignment"):
        """Pretend to be an instance of ConfigClass.

        Attributes defined by ConfigurableInstance will shadow those defined in ConfigClass
        """
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, "Cannot modify a frozen Config")

        if name in self.__dict__:
            # attribute exists in the ConfigurableInstance wrapper
            object.__setattr__(self, name, value)
        else:
            if at is None:
                at = getCallStack()
            self._value.__setattr__(name, value, at=at, label=label)

    def __delattr__(self, name, at=None, label="delete"):
        """
        Pretend to be an isntance of  ConfigClass.
        Attributes defiend by ConfigurableInstance will shadow those defined in ConfigClass
        """
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, "Cannot modify a frozen Config")

        try:
            # attribute exists in the ConfigurableInstance wrapper
            object.__delattr__(self, name)
        except AttributeError:
            if at is None:
                at = getCallStack()
            self._value.__delattr__(name, at=at, label=label)


class ConfigurableField(Field):
    """A configuration field (`~lsst.pex.config.Field` subclass) that can be
    can be retargeted towards a different configurable (often a
    `lsst.pipe.base.Task` subclass).

    The ``ConfigurableField`` is often used to configure subtasks, which are
    tasks (`~lsst.pipe.base.Task`) called by a parent task.

    Parameters
    ----------
    doc : `str`
        A description of the configuration field.
    target : configurable class
        The configurable target. Configurables have a ``ConfigClass``
        attribute. Within the task framework, configurables are
        `lsst.pipe.base.Task` subclasses)
    ConfigClass : `lsst.pex.config.Config`-type, optional
        The subclass of `lsst.pex.config.Config` expected as the configuration
        class of the ``target``. If ``ConfigClass`` is unset then
        ``target.ConfigClass`` is used.
    default : ``ConfigClass``-type, optional
        The default configuration class. Normally this parameter is not set,
        and defaults to ``ConfigClass`` (or ``target.ConfigClass``).
    check : callable, optional
        Callable that takes the field's value (the ``target``) as its only
        positional argument, and returns `True` if the ``target`` is valid (and
        `False` otherwise).

    See also
    --------
    ChoiceField
    ConfigChoiceField
    ConfigDictField
    ConfigField
    DictField
    Field
    ListField
    RangeField
    RegistryField

    Notes
    -----
    You can use the `ConfigurableInstance.apply` method to construct a
    fully-configured configurable.
    """

    def validateTarget(self, target, ConfigClass):
        """Validate the target and configuration class.

        Parameters
        ----------
        target
            The configurable being verified.
        ConfigClass : `lsst.pex.config.Config`-type or `None`
            The configuration class associated with the ``target``. This can
            be `None` if ``target`` has a ``ConfigClass`` attribute.

        Raises
        ------
        AttributeError
            Raised if ``ConfigClass`` is `None` and ``target`` does not have a
            ``ConfigClass`` attribute.
        TypeError
            Raised if ``ConfigClass`` is not a `~lsst.pex.config.Config`
            subclass.
        ValueError
            Raised if:

            - ``target`` is not callable (callables have a ``__call__``
              method).
            - ``target`` is not startically defined (does not have
              ``__module__`` or ``__name__`` attributes).
        """
        if ConfigClass is None:
            try:
                ConfigClass = target.ConfigClass
            except Exception:
                raise AttributeError("'target' must define attribute 'ConfigClass'")
        if not issubclass(ConfigClass, Config):
            raise TypeError("'ConfigClass' is of incorrect type %s."
                            "'ConfigClass' must be a subclass of Config" % _typeStr(ConfigClass))
        if not hasattr(target, '__call__'):
            raise ValueError("'target' must be callable")
        if not hasattr(target, '__module__') or not hasattr(target, '__name__'):
            raise ValueError("'target' must be statically defined"
                             "(must have '__module__' and '__name__' attributes)")
        return ConfigClass

    def __init__(self, doc, target, ConfigClass=None, default=None, check=None):
        ConfigClass = self.validateTarget(target, ConfigClass)

        if default is None:
            default = ConfigClass
        if default != ConfigClass and type(default) != ConfigClass:
            raise TypeError("'default' is of incorrect type %s. Expected %s" %
                            (_typeStr(default), _typeStr(ConfigClass)))

        source = getStackFrame()
        self._setup(doc=doc, dtype=ConfigurableInstance, default=default,
                    check=check, optional=False, source=source)
        self.target = target
        self.ConfigClass = ConfigClass

    def __getOrMake(self, instance, at=None, label="default"):
        value = instance._storage.get(self.name, None)
        if value is None:
            if at is None:
                at = getCallStack(1)
            value = ConfigurableInstance(instance, self, at=at, label=label)
            instance._storage[self.name] = value
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
            at = getCallStack()
        oldValue = self.__getOrMake(instance, at=at)

        if isinstance(value, ConfigurableInstance):
            oldValue.retarget(value.target, value.ConfigClass, at, label)
            oldValue.update(__at=at, __label=label, **value._storage)
        elif type(value) == oldValue._ConfigClass:
            oldValue.update(__at=at, __label=label, **value._storage)
        elif value == oldValue.ConfigClass:
            value = oldValue.ConfigClass()
            oldValue.update(__at=at, __label=label, **value._storage)
        else:
            msg = "Value %s is of incorrect type %s. Expected %s" % \
                (value, _typeStr(value), _typeStr(oldValue.ConfigClass))
            raise FieldValidationError(self, instance, msg)

    def rename(self, instance):
        fullname = _joinNamePath(instance._name, self.name)
        value = self.__getOrMake(instance)
        value._rename(fullname)

    def save(self, outfile, instance):
        fullname = _joinNamePath(instance._name, self.name)
        value = self.__getOrMake(instance)
        target = value.target

        if target != self.target:
            # not targeting the field-default target.
            # save target information
            ConfigClass = value.ConfigClass
            for module in set([target.__module__, ConfigClass.__module__]):
                outfile.write(u"import {}\n".format(module))
            outfile.write(u"{}.retarget(target={}, ConfigClass={})\n\n".format(fullname,
                                                                               _typeStr(target),
                                                                               _typeStr(ConfigClass)))
        # save field values
        value._save(outfile)

    def freeze(self, instance):
        value = self.__getOrMake(instance)
        value.freeze()

    def toDict(self, instance):
        value = self.__get__(instance)
        return value.toDict()

    def validate(self, instance):
        value = self.__get__(instance)
        value.validate()

        if self.check is not None and not self.check(value):
            msg = "%s is not a valid value" % str(value)
            raise FieldValidationError(self, instance, msg)

    def __deepcopy__(self, memo):
        """Customize deep-copying, because we always want a reference to the
        original typemap.

        WARNING: this must be overridden by subclasses if they change the
        constructor signature!
        """
        return type(self)(doc=self.doc, target=self.target, ConfigClass=self.ConfigClass,
                          default=copy.deepcopy(self.default))

    def _compare(self, instance1, instance2, shortcut, rtol, atol, output):
        """Compare two fields for equality.

        Used by `lsst.pex.ConfigDictField.compare`.

        Parameters
        ----------
        instance1 : `lsst.pex.config.Config`
            Left-hand side config instance to compare.
        instance2 : `lsst.pex.config.Config`
            Right-hand side config instance to compare.
        shortcut : `bool`
            If `True`, this function returns as soon as an inequality if found.
        rtol : `float`
            Relative tolerance for floating point comparisons.
        atol : `float`
            Absolute tolerance for floating point comparisons.
        output : callable
            A callable that takes a string, used (possibly repeatedly) to
            report inequalities. For example: `print`.

        Returns
        -------
        isEqual : bool
            `True` if the fields are equal, `False` otherwise.

        Notes
        -----
        Floating point comparisons are performed by `numpy.allclose`.
        """
        c1 = getattr(instance1, self.name)._value
        c2 = getattr(instance2, self.name)._value
        name = getComparisonName(
            _joinNamePath(instance1._name, self.name),
            _joinNamePath(instance2._name, self.name)
        )
        return compareConfigs(name, c1, c2, shortcut=shortcut, rtol=rtol, atol=atol, output=output)
