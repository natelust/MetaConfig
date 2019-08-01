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

__all__ = ("Registry", "makeRegistry", "RegistryField", "registerConfig", "registerConfigurable")

import collections.abc
import copy

from .config import Config, FieldValidationError, _typeStr
from .configChoiceField import ConfigInstanceDict, ConfigChoiceField


class ConfigurableWrapper:
    """A wrapper for configurables.

    Used for configurables that don't contain a ``ConfigClass`` attribute,
    or contain one that is being overridden.
    """

    def __init__(self, target, ConfigClass):
        self.ConfigClass = ConfigClass
        self._target = target

    def __call__(self, *args, **kwargs):
        return self._target(*args, **kwargs)


class Registry(collections.abc.Mapping):
    """A base class for global registries, which map names to configurables.

    A registry acts like a read-only dictionary with an additional `register`
    method to add targets. Targets in the registry are configurables (see
    *Notes*).

    Parameters
    ----------
    configBaseType : `lsst.pex.config.Config`-type
        The base class for config classes in the registry.

    Notes
    -----
    A configurable is a callable with call signature ``(config, *args)``
    Configurables typically create an algorithm or are themselves the
    algorithm. Often configurables are `lsst.pipe.base.Task` subclasses, but
    this is not required.

    A ``Registry`` has these requirements:

    - All configurables added to a particular registry have the same call
      signature.
    - All configurables in a registry typically share something important
      in common. For example, all configurables in ``psfMatchingRegistry``
      return a PSF matching class that has a ``psfMatch`` method with a
      particular call signature.

    Examples
    --------
    This examples creates a configurable class ``Foo`` and adds it to a
    registry. First, creating the configurable:

    >>> from lsst.pex.config import Registry, Config
    >>> class FooConfig(Config):
    ...     val = Field(dtype=int, default=3, doc="parameter for Foo")
    ...
    >>> class Foo:
    ...     ConfigClass = FooConfig
    ...     def __init__(self, config):
    ...         self.config = config
    ...     def addVal(self, num):
    ...         return self.config.val + num
    ...

    Next, create a ``Registry`` instance called ``registry`` and register the
    ``Foo`` configurable under the ``"foo"`` key:

    >>> registry = Registry()
    >>> registry.register("foo", Foo)
    >>> print(list(registry.keys()))
    ["foo"]

    Now ``Foo`` is conveniently accessible from the registry itself.

    Finally, use the registry to get the configurable class and create an
    instance of it:

    >>> FooConfigurable = registry["foo"]
    >>> foo = FooConfigurable(FooConfigurable.ConfigClass())
    >>> foo.addVal(5)
    8
    """

    def __init__(self, configBaseType=Config):
        if not issubclass(configBaseType, Config):
            raise TypeError("configBaseType=%s must be a subclass of Config" % _typeStr(configBaseType,))
        self._configBaseType = configBaseType
        self._dict = {}

    def register(self, name, target, ConfigClass=None):
        """Add a new configurable target to the registry.

        Parameters
        ----------
        name : `str`
            Name that the ``target`` is registered under. The target can
            be accessed later with `dict`-like patterns using ``name`` as
            the key.
        target : obj
            A configurable type, usually a subclass of `lsst.pipe.base.Task`.
        ConfigClass : `lsst.pex.config.Config`-type, optional
            A subclass of `lsst.pex.config.Config` used to configure the
            configurable. If `None` then the configurable's ``ConfigClass``
            attribute is used.

        Raises
        ------
        RuntimeError
            Raised if an item with ``name`` is already in the registry.
        AttributeError
            Raised if ``ConfigClass`` is `None` and ``target`` does not have
            a ``ConfigClass`` attribute.

        Notes
        -----
        If ``ConfigClass`` is provided then the ``target`` configurable is
        wrapped in a new object that forwards function calls to it. Otherwise
        the original ``target`` is stored.
        """
        if name in self._dict:
            raise RuntimeError("An item with name %r already exists" % name)
        if ConfigClass is None:
            wrapper = target
        else:
            wrapper = ConfigurableWrapper(target, ConfigClass)
        if not issubclass(wrapper.ConfigClass, self._configBaseType):
            raise TypeError("ConfigClass=%s is not a subclass of %r" %
                            (_typeStr(wrapper.ConfigClass), _typeStr(self._configBaseType)))
        self._dict[name] = wrapper

    def __getitem__(self, key):
        return self._dict[key]

    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        return iter(self._dict)

    def __contains__(self, key):
        return key in self._dict

    def makeField(self, doc, default=None, optional=False, multi=False):
        """Create a `RegistryField` configuration field from this registry.

        Parameters
        ----------
        doc : `str`
            A description of the field.
        default : object, optional
            The default target for the field.
        optional : `bool`, optional
            When `False`, `lsst.pex.config.Config.validate` fails if the
            field's value is `None`.
        multi : `bool`, optional
            A flag to allow multiple selections in the `RegistryField` if
            `True`.

        Returns
        -------
        field : `lsst.pex.config.RegistryField`
            `~lsst.pex.config.RegistryField` Configuration field.
        """
        return RegistryField(doc, self, default, optional, multi)


class RegistryAdaptor(collections.abc.Mapping):
    """Private class that makes a `Registry` behave like the thing a
    `~lsst.pex.config.ConfigChoiceField` expects.

    Parameters
    ----------
    registry : `Registry`
        `Registry` instance.
    """

    def __init__(self, registry):
        self.registry = registry

    def __getitem__(self, k):
        return self.registry[k].ConfigClass

    def __iter__(self):
        return iter(self.registry)

    def __len__(self):
        return len(self.registry)

    def __contains__(self, k):
        return k in self.registry


class RegistryInstanceDict(ConfigInstanceDict):
    """Dictionary of instantiated configs, used to populate a `RegistryField`.

    Parameters
    ----------
    config : `lsst.pex.config.Config`
        Configuration instance.
    field : `RegistryField`
        Configuration field.
    """

    def __init__(self, config, field):
        ConfigInstanceDict.__init__(self, config, field)
        self.registry = field.registry

    def _getTarget(self):
        if self._field.multi:
            raise FieldValidationError(self._field, self._config,
                                       "Multi-selection field has no attribute 'target'")
        return self._field.typemap.registry[self._selection]

    target = property(_getTarget)

    def _getTargets(self):
        if not self._field.multi:
            raise FieldValidationError(self._field, self._config,
                                       "Single-selection field has no attribute 'targets'")
        return [self._field.typemap.registry[c] for c in self._selection]

    targets = property(_getTargets)

    def apply(self, *args, **kw):
        """Call the active target(s) with the active config as a keyword arg

        If this is a multi-selection field, return a list obtained by calling
        each active target with its corresponding active config.

        Additional arguments will be passed on to the configurable target(s)
        """
        if self.active is None:
            msg = "No selection has been made.  Options: %s" % \
                (" ".join(list(self._field.typemap.registry.keys())))
            raise FieldValidationError(self._field, self._config, msg)
        if self._field.multi:
            retvals = []
            for c in self._selection:
                retvals.append(self._field.typemap.registry[c](*args, config=self[c], **kw))
            return retvals
        else:
            return self._field.typemap.registry[self.name](*args, config=self[self.name], **kw)

    def __setattr__(self, attr, value):
        if attr == "registry":
            object.__setattr__(self, attr, value)
        else:
            ConfigInstanceDict.__setattr__(self, attr, value)


class RegistryField(ConfigChoiceField):
    """A configuration field whose options are defined in a `Registry`.

    Parameters
    ----------
    doc : `str`
        A description of the field.
    registry : `Registry`
        The registry that contains this field.
    default : `str`, optional
        The default target key.
    optional : `bool`, optional
        When `False`, `lsst.pex.config.Config.validate` fails if the field's
        value is `None`.
    multi : `bool`, optional
        If `True`, the field allows multiple selections. The default is
        `False`.

    See also
    --------
    ChoiceField
    ConfigChoiceField
    ConfigDictField
    ConfigField
    ConfigurableField
    DictField
    Field
    ListField
    RangeField
    """

    instanceDictClass = RegistryInstanceDict
    """Class used to hold configurable instances in the field.
    """

    def __init__(self, doc, registry, default=None, optional=False, multi=False):
        types = RegistryAdaptor(registry)
        self.registry = registry
        ConfigChoiceField.__init__(self, doc, types, default, optional, multi)

    def __deepcopy__(self, memo):
        """Customize deep-copying, want a reference to the original registry.

        WARNING: this must be overridden by subclasses if they change the
        constructor signature!
        """
        other = type(self)(doc=self.doc, registry=self.registry,
                           default=copy.deepcopy(self.default),
                           optional=self.optional, multi=self.multi)
        other.source = self.source
        return other


def makeRegistry(doc, configBaseType=Config):
    """Create a `Registry`.

    Parameters
    ----------
    doc : `str`
        Docstring for the created `Registry` (this is set as the ``__doc__``
        attribute of the `Registry` instance.
    configBaseType : `lsst.pex.config.Config`-type
        Base type of config classes in the `Registry`
        (`lsst.pex.config.Registry.configBaseType`).

    Returns
    -------
    registry : `Registry`
        Registry with ``__doc__`` and `~Registry.configBaseType` attributes
        set.
    """
    cls = type("Registry", (Registry,), {"__doc__": doc})
    return cls(configBaseType=configBaseType)


def registerConfigurable(name, registry, ConfigClass=None):
    """A decorator that adds a class as a configurable in a `Registry`
    instance.

    Parameters
    ----------
    name : `str`
        Name of the target (the decorated class) in the ``registry``.
    registry : `Registry`
        The `Registry` instance that the decorated class is added to.
    ConfigClass : `lsst.pex.config.Config`-type, optional
        Config class associated with the configurable. If `None`, the class's
        ``ConfigClass`` attribute is used instead.

    See also
    --------
    registerConfig

    Notes
    -----
    Internally, this decorator runs `Registry.register`.
    """
    def decorate(cls):
        registry.register(name, target=cls, ConfigClass=ConfigClass)
        return cls
    return decorate


def registerConfig(name, registry, target):
    """Decorator that adds a class as a ``ConfigClass`` in a `Registry` and
    associates it with the given configurable.

    Parameters
    ----------
    name : `str`
        Name of the ``target`` in the ``registry``.
    registry : `Registry`
        The registry containing the ``target``.
    target : obj
        A configurable type, such as a subclass of `lsst.pipe.base.Task`.

    See also
    --------
    registerConfigurable

    Notes
    -----
    Internally, this decorator runs `Registry.register`.
    """
    def decorate(cls):
        registry.register(name, target=target, ConfigClass=cls)
        return cls
    return decorate
