#
# LSST Data Management System
# Copyright 2008-2015 AURA/LSST.
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
# see <https://www.lsstcorp.org/LegalNotices/>.
#
__all__ = ("Config", "Field", "FieldValidationError")

import io
import os
import re
import sys
import math
import copy
import tempfile
import shutil
import warnings

from .comparison import getComparisonName, compareScalars, compareConfigs
from .callStack import getStackFrame, getCallStack


def _joinNamePath(prefix=None, name=None, index=None):
    """Generate nested configuration names.
    """
    if not prefix and not name:
        raise ValueError("Invalid name: cannot be None")
    elif not name:
        name = prefix
    elif prefix and name:
        name = prefix + "." + name

    if index is not None:
        return "%s[%r]" % (name, index)
    else:
        return name


def _autocast(x, dtype):
    """Cast a value to a type, if appropriate.

    Parameters
    ----------
    x : object
        A value.
    dtype : tpye
        Data type, such as `float`, `int`, or `str`.

    Returns
    -------
    values : object
        If appropriate, the returned value is ``x`` cast to the given type
        ``dtype``. If the cast cannot be performed the original value of
        ``x`` is returned.
    """
    if dtype == float and isinstance(x, int):
        return float(x)
    return x


def _typeStr(x):
    """Generate a fully-qualified type name.

    Returns
    -------
    `str`
        Fully-qualified type name.

    Notes
    -----
    This function is used primarily for writing config files to be executed
    later upon with the 'load' function.
    """
    if hasattr(x, '__module__') and hasattr(x, '__name__'):
        xtype = x
    else:
        xtype = type(x)
    if (sys.version_info.major <= 2 and xtype.__module__ == '__builtin__') or xtype.__module__ == 'builtins':
        return xtype.__name__
    else:
        return "%s.%s" % (xtype.__module__, xtype.__name__)


class ConfigMeta(type):
    """A metaclass for `lsst.pex.config.Config`.

    Notes
    -----
    ``ConfigMeta`` adds a dictionary containing all `~lsst.pex.config.Field`
    class attributes as a class attribute called ``_fields``, and adds
    the name of each field as an instance variable of the field itself (so you
    don't have to pass the name of the field to the field constructor).
    """

    def __init__(cls, name, bases, dict_):
        type.__init__(cls, name, bases, dict_)
        cls._fields = {}
        cls._source = getStackFrame()

        def getFields(classtype):
            fields = {}
            bases = list(classtype.__bases__)
            bases.reverse()
            for b in bases:
                fields.update(getFields(b))

            for k, v in classtype.__dict__.items():
                if isinstance(v, Field):
                    fields[k] = v
            return fields

        fields = getFields(cls)
        for k, v in fields.items():
            setattr(cls, k, copy.deepcopy(v))

    def __setattr__(cls, name, value):
        if isinstance(value, Field):
            value.name = name
            cls._fields[name] = value
        type.__setattr__(cls, name, value)


class FieldValidationError(ValueError):
    """Raised when a ``~lsst.pex.config.Field`` is not valid in a
    particular ``~lsst.pex.config.Config``.

    Parameters
    ----------
    field : `lsst.pex.config.Field`
        The field that was not valid.
    config : `lsst.pex.config.Config`
        The config containing the invalid field.
    msg : `str`
        Text describing why the field was not valid.
    """

    def __init__(self, field, config, msg):
        self.fieldType = type(field)
        """Type of the `~lsst.pex.config.Field` that incurred the error.
        """

        self.fieldName = field.name
        """Name of the `~lsst.pex.config.Field` instance that incurred the
        error (`str`).

        See also
        --------
        lsst.pex.config.Field.name
        """

        self.fullname = _joinNamePath(config._name, field.name)
        """Fully-qualified name of the `~lsst.pex.config.Field` instance
        (`str`).
        """

        self.history = config.history.setdefault(field.name, [])
        """Full history of all changes to the `~lsst.pex.config.Field`
        instance.
        """

        self.fieldSource = field.source
        """File and line number of the `~lsst.pex.config.Field` definition.
        """

        self.configSource = config._source
        error = "%s '%s' failed validation: %s\n"\
                "For more information see the Field definition at:\n%s"\
                " and the Config definition at:\n%s" % \
            (self.fieldType.__name__, self.fullname, msg,
             self.fieldSource.format(), self.configSource.format())
        super().__init__(error)


class Field:
    """A field in a `~lsst.pex.config.Config` that supports `int`, `float`,
    `complex`, `bool`, and `str` data types.

    Parameters
    ----------
    doc : `str`
        A description of the field for users.
    dtype : type
        The field's data type. ``Field`` only supports basic data types:
        `int`, `float`, `complex`, `bool`, and `str`. See
        `Field.supportedTypes`.
    default : object, optional
        The field's default value.
    check : callable, optional
        A callable that is called with the field's value. This callable should
        return `False` if the value is invalid. More complex inter-field
        validation can be written as part of the
        `lsst.pex.config.Config.validate` method.
    optional : `bool`, optional
        This sets whether the field is considered optional, and therefore
        doesn't need to be set by the user. When `False`,
        `lsst.pex.config.Config.validate` fails if the field's value is `None`.
    deprecated : None or `str`, optional
        A description of why this Field is deprecated, including removal date.
        If not None, the string is appended to the docstring for this Field.

    Raises
    ------
    ValueError
        Raised when the ``dtype`` parameter is not one of the supported types
        (see `Field.supportedTypes`).

    See also
    --------
    ChoiceField
    ConfigChoiceField
    ConfigDictField
    ConfigField
    ConfigurableField
    DictField
    ListField
    RangeField
    RegistryField

    Notes
    -----
    ``Field`` instances (including those of any subclass of ``Field``) are used
    as class attributes of `~lsst.pex.config.Config` subclasses (see the
    example, below). ``Field`` attributes work like the `property` attributes
    of classes that implement custom setters and getters. `Field` attributes
    belong to the class, but operate on the instance. Formally speaking,
    `Field` attributes are `descriptors
    <https://docs.python.org/3/howto/descriptor.html>`_.

    When you access a `Field` attribute on a `Config` instance, you don't
    get the `Field` instance itself. Instead, you get the value of that field,
    which might be a simple type (`int`, `float`, `str`, `bool`) or a custom
    container type (like a `lsst.pex.config.List`) depending on the field's
    type. See the example, below.

    Examples
    --------
    Instances of ``Field`` should be used as class attributes of
    `lsst.pex.config.Config` subclasses:

    >>> from lsst.pex.config import Config, Field
    >>> class Example(Config):
    ...     myInt = Field("An integer field.", int, default=0)
    ...
    >>> print(config.myInt)
    0
    >>> config.myInt = 5
    >>> print(config.myInt)
    5
    """

    supportedTypes = set((str, bool, float, int, complex))
    """Supported data types for field values (`set` of types).
    """

    def __init__(self, doc, dtype, default=None, check=None, optional=False, deprecated=None):
        if dtype not in self.supportedTypes:
            raise ValueError("Unsupported Field dtype %s" % _typeStr(dtype))

        source = getStackFrame()
        self._setup(doc=doc, dtype=dtype, default=default, check=check, optional=optional, source=source,
                    deprecated=deprecated)

    def _setup(self, doc, dtype, default, check, optional, source, deprecated):
        """Set attributes, usually during initialization.
        """
        self.dtype = dtype
        """Data type for the field.
        """

        # append the deprecation message to the docstring.
        if deprecated is not None:
            doc = f"{doc} Deprecated: {deprecated}"
        self.doc = doc
        """A description of the field (`str`).
        """

        self.deprecated = deprecated
        """If not None, a description of why this field is deprecated (`str`).
        """

        self.__doc__ = f"{doc} (`{dtype.__name__}`"
        if optional or default is not None:
            self.__doc__ += f", default ``{default!r}``"
        self.__doc__ += ")"

        self.default = default
        """Default value for this field.
        """

        self.check = check
        """A user-defined function that validates the value of the field.
        """

        self.optional = optional
        """Flag that determines if the field is required to be set (`bool`).

        When `False`, `lsst.pex.config.Config.validate` will fail if the
        field's value is `None`.
        """

        self.source = source
        """The stack frame where this field is defined (`list` of
        `lsst.pex.config.callStack.StackFrame`).
        """

    def rename(self, instance):
        """Rename the field in a `~lsst.pex.config.Config` (for internal use
        only).

        Parameters
        ----------
        instance : `lsst.pex.config.Config`
            The config instance that contains this field.

        Notes
        -----
        This method is invoked by the `lsst.pex.config.Config` object that
        contains this field and should not be called directly.

        Renaming is only relevant for `~lsst.pex.config.Field` instances that
        hold subconfigs. `~lsst.pex.config.Fields` that hold subconfigs should
        rename each subconfig with the full field name as generated by
        `lsst.pex.config.config._joinNamePath`.
        """
        pass

    def validate(self, instance):
        """Validate the field (for internal use only).

        Parameters
        ----------
        instance : `lsst.pex.config.Config`
            The config instance that contains this field.

        Raises
        ------
        lsst.pex.config.FieldValidationError
            Raised if verification fails.

        Notes
        -----
        This method provides basic validation:

        - Ensures that the value is not `None` if the field is not optional.
        - Ensures type correctness.
        - Ensures that the user-provided ``check`` function is valid.

        Most `~lsst.pex.config.Field` subclasses should call
        `lsst.pex.config.field.Field.validate` if they re-implement
        `~lsst.pex.config.field.Field.validate`.
        """
        value = self.__get__(instance)
        if not self.optional and value is None:
            raise FieldValidationError(self, instance, "Required value cannot be None")

    def freeze(self, instance):
        """Make this field read-only (for internal use only).

        Parameters
        ----------
        instance : `lsst.pex.config.Config`
            The config instance that contains this field.

        Notes
        -----
        Freezing is only relevant for fields that hold subconfigs. Fields which
        hold subconfigs should freeze each subconfig.

        **Subclasses should implement this method.**
        """
        pass

    def _validateValue(self, value):
        """Validate a value.

        Parameters
        ----------
        value : object
            The value being validated.

        Raises
        ------
        TypeError
            Raised if the value's type is incompatible with the field's
            ``dtype``.
        ValueError
            Raised if the value is rejected by the ``check`` method.
        """
        if value is None:
            return

        if not isinstance(value, self.dtype):
            msg = "Value %s is of incorrect type %s. Expected type %s" % \
                (value, _typeStr(value), _typeStr(self.dtype))
            raise TypeError(msg)
        if self.check is not None and not self.check(value):
            msg = "Value %s is not a valid value" % str(value)
            raise ValueError(msg)

    def _collectImports(self, instance, imports):
        """This function should call the _collectImports method on all config
        objects the field may own, and union them with the supplied imports
        set.

        Parameters
        ----------
        instance : instance or subclass of `lsst.pex.config.Config`
            A config object that has this field defined on it
        imports : `set`
            Set of python modules that need imported after persistence
        """
        pass

    def save(self, outfile, instance):
        """Save this field to a file (for internal use only).

        Parameters
        ----------
        outfile : file-like object
            A writeable field handle.
        instance : `Config`
            The `Config` instance that contains this field.

        Notes
        -----
        This method is invoked by the `~lsst.pex.config.Config` object that
        contains this field and should not be called directly.

        The output consists of the documentation string
        (`lsst.pex.config.Field.doc`) formatted as a Python comment. The second
        line is formatted as an assignment: ``{fullname}={value}``.

        This output can be executed with Python.
        """
        value = self.__get__(instance)
        fullname = _joinNamePath(instance._name, self.name)

        # write full documentation string as comment lines (i.e. first character is #)
        doc = "# " + str(self.doc).replace("\n", "\n# ")
        if isinstance(value, float) and (math.isinf(value) or math.isnan(value)):
            # non-finite numbers need special care
            outfile.write(u"{}\n{}=float('{!r}')\n\n".format(doc, fullname, value))
        else:
            outfile.write(u"{}\n{}={!r}\n\n".format(doc, fullname, value))

    def toDict(self, instance):
        """Convert the field value so that it can be set as the value of an
        item in a `dict` (for internal use only).

        Parameters
        ----------
        instance : `Config`
            The `Config` that contains this field.

        Returns
        -------
        value : object
            The field's value. See *Notes*.

        Notes
        -----
        This method invoked by the owning `~lsst.pex.config.Config` object and
        should not be called directly.

        Simple values are passed through. Complex data structures must be
        manipulated. For example, a `~lsst.pex.config.Field` holding a
        subconfig should, instead of the subconfig object, return a `dict`
        where the keys are the field names in the subconfig, and the values are
        the field values in the subconfig.
        """
        return self.__get__(instance)

    def __get__(self, instance, owner=None, at=None, label="default"):
        """Define how attribute access should occur on the Config instance
        This is invoked by the owning config object and should not be called
        directly

        When the field attribute is accessed on a Config class object, it
        returns the field object itself in order to allow inspection of
        Config classes.

        When the field attribute is access on a config instance, the actual
        value described by the field (and held by the Config instance) is
        returned.
        """
        if instance is None or not isinstance(instance, Config):
            return self
        else:
            return instance._storage[self.name]

    def __set__(self, instance, value, at=None, label='assignment'):
        """Set an attribute on the config instance.

        Parameters
        ----------
        instance : `lsst.pex.config.Config`
            The config instance that contains this field.
        value : obj
            Value to set on this field.
        at : `list` of `lsst.pex.config.callStack.StackFrame`
            The call stack (created by
            `lsst.pex.config.callStack.getCallStack`).
        label : `str`, optional
            Event label for the history.

        Notes
        -----
        This method is invoked by the owning `lsst.pex.config.Config` object
        and should not be called directly.

        Derived `~lsst.pex.config.Field` classes may need to override the
        behavior. When overriding ``__set__``, `~lsst.pex.config.Field` authors
        should follow the following rules:

        - Do not allow modification of frozen configs.
        - Validate the new value **before** modifying the field. Except if the
          new value is `None`. `None` is special and no attempt should be made
          to validate it until `lsst.pex.config.Config.validate` is called.
        - Do not modify the `~lsst.pex.config.Config` instance to contain
          invalid values.
        - If the field is modified, update the history of the
          `lsst.pex.config.field.Field` to reflect the changes.

        In order to decrease the need to implement this method in derived
        `~lsst.pex.config.Field` types, value validation is performed in the
        `lsst.pex.config.Field._validateValue`. If only the validation step
        differs in the derived `~lsst.pex.config.Field`, it is simpler to
        implement `lsst.pex.config.Field._validateValue` than to reimplement
        ``__set__``. More complicated behavior, however, may require
        reimplementation.
        """
        if instance._frozen:
            raise FieldValidationError(self, instance, "Cannot modify a frozen Config")

        history = instance._history.setdefault(self.name, [])
        if value is not None:
            value = _autocast(value, self.dtype)
            try:
                self._validateValue(value)
            except BaseException as e:
                raise FieldValidationError(self, instance, str(e))

        instance._storage[self.name] = value
        if at is None:
            at = getCallStack()
        history.append((value, at, label))

    def __delete__(self, instance, at=None, label='deletion'):
        """Delete an attribute from a `lsst.pex.config.Config` instance.

        Parameters
        ----------
        instance : `lsst.pex.config.Config`
            The config instance that contains this field.
        at : `list` of `lsst.pex.config.callStack.StackFrame`
            The call stack (created by
            `lsst.pex.config.callStack.getCallStack`).
        label : `str`, optional
            Event label for the history.

        Notes
        -----
        This is invoked by the owning `~lsst.pex.config.Config` object and
        should not be called directly.
        """
        if at is None:
            at = getCallStack()
        self.__set__(instance, None, at=at, label=label)

    def _compare(self, instance1, instance2, shortcut, rtol, atol, output):
        """Compare a field (named `Field.name`) in two
        `~lsst.pex.config.Config` instances for equality.

        Parameters
        ----------
        instance1 : `lsst.pex.config.Config`
            Left-hand side `Config` instance to compare.
        instance2 : `lsst.pex.config.Config`
            Right-hand side `Config` instance to compare.
        shortcut : `bool`, optional
            **Unused.**
        rtol : `float`, optional
            Relative tolerance for floating point comparisons.
        atol : `float`, optional
            Absolute tolerance for floating point comparisons.
        output : callable, optional
            A callable that takes a string, used (possibly repeatedly) to
            report inequalities.

        Notes
        -----
        This method must be overridden by more complex `Field` subclasses.

        See also
        --------
        lsst.pex.config.compareScalars
        """
        v1 = getattr(instance1, self.name)
        v2 = getattr(instance2, self.name)
        name = getComparisonName(
            _joinNamePath(instance1._name, self.name),
            _joinNamePath(instance2._name, self.name)
        )
        return compareScalars(name, v1, v2, dtype=self.dtype, rtol=rtol, atol=atol, output=output)


class RecordingImporter:
    """Importer (for `sys.meta_path`) that records which modules are being
    imported.

    *This class does not do any importing itself.*

    Examples
    --------
    Use this class as a context manager to ensure it is properly uninstalled
    when done:

    >>> with RecordingImporter() as importer:
    ...     # import stuff
    ...     import numpy as np
    ... print("Imported: " + importer.getModules())
    """

    def __init__(self):
        self._modules = set()

    def __enter__(self):
        self.origMetaPath = sys.meta_path
        sys.meta_path = [self] + sys.meta_path
        return self

    def __exit__(self, *args):
        self.uninstall()
        return False  # Don't suppress exceptions

    def uninstall(self):
        """Uninstall the importer.
        """
        sys.meta_path = self.origMetaPath

    def find_module(self, fullname, path=None):
        """Called as part of the ``import`` chain of events.
        """
        self._modules.add(fullname)
        # Return None because we don't do any importing.
        return None

    def getModules(self):
        """Get the set of modules that were imported.

        Returns
        -------
        modules : `set` of `str`
            Set of imported module names.
        """
        return self._modules


class Config(metaclass=ConfigMeta):
    """Base class for configuration (*config*) objects.

    Notes
    -----
    A ``Config`` object will usually have several `~lsst.pex.config.Field`
    instances as class attributes. These are used to define most of the base
    class behavior.

    ``Config`` implements a mapping API that provides many `dict`-like methods,
    such as `keys`, `values`, `items`, `iteritems`, `iterkeys`, and
    `itervalues`. ``Config`` instances also support the ``in`` operator to
    test if a field is in the config. Unlike a `dict`, ``Config`` classes are
    not subscriptable. Instead, access individual fields as attributes of the
    configuration instance.

    Examples
    --------
    Config classes are subclasses of ``Config`` that have
    `~lsst.pex.config.Field` instances (or instances of
    `~lsst.pex.config.Field` subclasses) as class attributes:

    >>> from lsst.pex.config import Config, Field, ListField
    >>> class DemoConfig(Config):
    ...     intField = Field(doc="An integer field", dtype=int, default=42)
    ...     listField = ListField(doc="List of favorite beverages.", dtype=str,
    ...                           default=['coffee', 'green tea', 'water'])
    ...
    >>> config = DemoConfig()

    Configs support many `dict`-like APIs:

    >>> config.keys()
    ['intField', 'listField']
    >>> 'intField' in config
    True

    Individual fields can be accessed as attributes of the configuration:

    >>> config.intField
    42
    >>> config.listField.append('earl grey tea')
    >>> print(config.listField)
    ['coffee', 'green tea', 'water', 'earl grey tea']
    """

    def __iter__(self):
        """Iterate over fields.
        """
        return self._fields.__iter__()

    def keys(self):
        """Get field names.

        Returns
        -------
        names : `list`
            List of `lsst.pex.config.Field` names.

        See also
        --------
        lsst.pex.config.Config.iterkeys
        """
        return list(self._storage.keys())

    def values(self):
        """Get field values.

        Returns
        -------
        values : `list`
            List of field values.

        See also
        --------
        lsst.pex.config.Config.itervalues
        """
        return list(self._storage.values())

    def items(self):
        """Get configurations as ``(field name, field value)`` pairs.

        Returns
        -------
        items : `list`
            List of tuples for each configuration. Tuple items are:

            0. Field name.
            1. Field value.

        See also
        --------
        lsst.pex.config.Config.iteritems
        """
        return list(self._storage.items())

    def iteritems(self):
        """Iterate over (field name, field value) pairs.

        Yields
        ------
        item : `tuple`
            Tuple items are:

            0. Field name.
            1. Field value.

        See also
        --------
        lsst.pex.config.Config.items
        """
        return iter(self._storage.items())

    def itervalues(self):
        """Iterate over field values.

        Yields
        ------
        value : obj
            A field value.

        See also
        --------
        lsst.pex.config.Config.values
        """
        return iter(self.storage.values())

    def iterkeys(self):
        """Iterate over field names

        Yields
        ------
        key : `str`
            A field's key (attribute name).

        See also
        --------
        lsst.pex.config.Config.values
        """
        return iter(self.storage.keys())

    def __contains__(self, name):
        """!Return True if the specified field exists in this config

        @param[in] name  field name to test for
        """
        return self._storage.__contains__(name)

    def __new__(cls, *args, **kw):
        """Allocate a new `lsst.pex.config.Config` object.

        In order to ensure that all Config object are always in a proper state
        when handed to users or to derived `~lsst.pex.config.Config` classes,
        some attributes are handled at allocation time rather than at
        initialization.

        This ensures that even if a derived `~lsst.pex.config.Config` class
        implements ``__init__``, its author does not need to be concerned about
        when or even the base ``Config.__init__`` should be called.
        """
        name = kw.pop("__name", None)
        at = kw.pop("__at", getCallStack())
        # remove __label and ignore it
        kw.pop("__label", "default")

        instance = object.__new__(cls)
        instance._frozen = False
        instance._name = name
        instance._storage = {}
        instance._history = {}
        instance._imports = set()
        # load up defaults
        for field in instance._fields.values():
            instance._history[field.name] = []
            field.__set__(instance, field.default, at=at + [field.source], label="default")
        # set custom default-overides
        instance.setDefaults()
        # set constructor overides
        instance.update(__at=at, **kw)
        return instance

    def __reduce__(self):
        """Reduction for pickling (function with arguments to reproduce).

        We need to condense and reconstitute the `~lsst.pex.config.Config`,
        since it may contain lambdas (as the ``check`` elements) that cannot
        be pickled.
        """
        # The stream must be in characters to match the API but pickle requires bytes
        stream = io.StringIO()
        self.saveToStream(stream)
        return (unreduceConfig, (self.__class__, stream.getvalue().encode()))

    def setDefaults(self):
        """Subclass hook for computing defaults.

        Notes
        -----
        Derived `~lsst.pex.config.Config` classes that must compute defaults
        rather than using the `~lsst.pex.config.Field` instances's defaults
        should do so here. To correctly use inherited defaults,
        implementations of ``setDefaults`` must call their base class's
        ``setDefaults``.
        """
        pass

    def update(self, **kw):
        """Update values of fields specified by the keyword arguments.

        Parameters
        ----------
        kw
            Keywords are configuration field names. Values are configuration
            field values.

        Notes
        -----
        The ``__at`` and ``__label`` keyword arguments are special internal
        keywords. They are used to strip out any internal steps from the
        history tracebacks of the config. Do not modify these keywords to
        subvert a `~lsst.pex.config.Config` instance's history.

        Examples
        --------
        This is a config with three fields:

        >>> from lsst.pex.config import Config, Field
        >>> class DemoConfig(Config):
        ...     fieldA = Field(doc='Field A', dtype=int, default=42)
        ...     fieldB = Field(doc='Field B', dtype=bool, default=True)
        ...     fieldC = Field(doc='Field C', dtype=str, default='Hello world')
        ...
        >>> config = DemoConfig()

        These are the default values of each field:

        >>> for name, value in config.iteritems():
        ...     print(f"{name}: {value}")
        ...
        fieldA: 42
        fieldB: True
        fieldC: 'Hello world'

        Using this method to update ``fieldA`` and ``fieldC``:

        >>> config.update(fieldA=13, fieldC='Updated!')

        Now the values of each field are:

        >>> for name, value in config.iteritems():
        ...     print(f"{name}: {value}")
        ...
        fieldA: 13
        fieldB: True
        fieldC: 'Updated!'
        """
        at = kw.pop("__at", getCallStack())
        label = kw.pop("__label", "update")

        for name, value in kw.items():
            try:
                field = self._fields[name]
                field.__set__(self, value, at=at, label=label)
            except KeyError:
                raise KeyError("No field of name %s exists in config type %s" % (name, _typeStr(self)))

    def load(self, filename, root="config"):
        """Modify this config in place by executing the Python code in a
        configuration file.

        Parameters
        ----------
        filename : `str`
            Name of the configuration file. A configuration file is Python
            module.
        root : `str`, optional
            Name of the variable in file that refers to the config being
            overridden.

            For example, the value of root is ``"config"`` and the file
            contains::

                config.myField = 5

            Then this config's field ``myField`` is set to ``5``.

            **Deprecated:** For backwards compatibility, older config files
            that use ``root="root"`` instead of ``root="config"`` will be
            loaded with a warning printed to `sys.stderr`. This feature will be
            removed at some point.

        See also
        --------
        lsst.pex.config.Config.loadFromStream
        lsst.pex.config.Config.save
        lsst.pex.config.Config.saveFromStream
        """
        with open(filename, "r") as f:
            code = compile(f.read(), filename=filename, mode="exec")
            self.loadFromStream(stream=code, root=root)

    def loadFromStream(self, stream, root="config", filename=None):
        """Modify this Config in place by executing the Python code in the
        provided stream.

        Parameters
        ----------
        stream : file-like object, `str`, or compiled string
            Stream containing configuration override code.
        root : `str`, optional
            Name of the variable in file that refers to the config being
            overridden.

            For example, the value of root is ``"config"`` and the file
            contains::

                config.myField = 5

            Then this config's field ``myField`` is set to ``5``.

            **Deprecated:** For backwards compatibility, older config files
            that use ``root="root"`` instead of ``root="config"`` will be
            loaded with a warning printed to `sys.stderr`. This feature will be
            removed at some point.
        filename : `str`, optional
            Name of the configuration file, or `None` if unknown or contained
            in the stream. Used for error reporting.

        See also
        --------
        lsst.pex.config.Config.load
        lsst.pex.config.Config.save
        lsst.pex.config.Config.saveFromStream
        """
        with RecordingImporter() as importer:
            try:
                local = {root: self}
                exec(stream, {}, local)
            except NameError as e:
                if root == "config" and "root" in e.args[0]:
                    if filename is None:
                        # try to determine the file name; a compiled string has attribute "co_filename",
                        # an open file has attribute "name", else give up
                        filename = getattr(stream, "co_filename", None)
                        if filename is None:
                            filename = getattr(stream, "name", "?")
                    print(f"Config override file {filename!r}"
                          " appears to use 'root' instead of 'config'; trying with 'root'", file=sys.stderr)
                    local = {"root": self}
                    exec(stream, {}, local)
                else:
                    raise

        self._imports.update(importer.getModules())

    def save(self, filename, root="config"):
        """Save a Python script to the named file, which, when loaded,
        reproduces this config.

        Parameters
        ----------
        filename : `str`
            Desination filename of this configuration.
        root : `str`, optional
            Name to use for the root config variable. The same value must be
            used when loading (see `lsst.pex.config.Config.load`).

        See also
        --------
        lsst.pex.config.Config.saveToStream
        lsst.pex.config.Config.load
        lsst.pex.config.Config.loadFromStream
        """
        d = os.path.dirname(filename)
        with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=d) as outfile:
            self.saveToStream(outfile, root)
            # tempfile is hardcoded to create files with mode '0600'
            # for an explantion of these antics see:
            # https://stackoverflow.com/questions/10291131/how-to-use-os-umask-in-python
            umask = os.umask(0o077)
            os.umask(umask)
            os.chmod(outfile.name, (~umask & 0o666))
            # chmod before the move so we get quasi-atomic behavior if the
            # source and dest. are on the same filesystem.
            # os.rename may not work across filesystems
            shutil.move(outfile.name, filename)

    def saveToStream(self, outfile, root="config"):
        """Save a configuration file to a stream, which, when loaded,
        reproduces this config.

        Parameters
        ----------
        outfile : file-like object
            Destination file object write the config into. Accepts strings not
            bytes.
        root
            Name to use for the root config variable. The same value must be
            used when loading (see `lsst.pex.config.Config.load`).

        See also
        --------
        lsst.pex.config.Config.save
        lsst.pex.config.Config.load
        lsst.pex.config.Config.loadFromStream
        """
        tmp = self._name
        self._rename(root)
        try:
            self._collectImports()
            # Remove self from the set, as it is handled explicitly below
            self._imports.remove(self.__module__)
            configType = type(self)
            typeString = _typeStr(configType)
            outfile.write(u"import {}\n".format(configType.__module__))
            outfile.write(u"assert type({})=={}, 'config is of type %s.%s ".format(root, typeString))
            outfile.write(u"instead of {}' % (type({}).__module__, type({}).__name__)\n".format(typeString,
                                                                                                root,
                                                                                                root))
            for imp in self._imports:
                if imp in sys.modules and sys.modules[imp] is not None:
                    outfile.write(u"import {}\n".format(imp))
            self._save(outfile)
        finally:
            self._rename(tmp)

    def freeze(self):
        """Make this config, and all subconfigs, read-only.
        """
        self._frozen = True
        for field in self._fields.values():
            field.freeze(self)

    def _save(self, outfile):
        """Save this config to an open stream object.

        Parameters
        ----------
        outfile : file-like object
            Destination file object write the config into. Accepts strings not
            bytes.
        """
        for field in self._fields.values():
            field.save(outfile, self)

    def _collectImports(self):
        """Adds module containing self to the list of things to import and
        then loops over all the fields in the config calling a corresponding
        collect method. The field method will call _collectImports on any configs
        it may own and return the set of things to import. This returned set
        will be merged with the set of imports for this config class.
        """
        self._imports.add(self.__module__)
        for name, field in self._fields.items():
            field._collectImports(self, self._imports)

    def toDict(self):
        """Make a dictionary of field names and their values.

        Returns
        -------
        dict_ : `dict`
            Dictionary with keys that are `~lsst.pex.config.Field` names.
            Values are `~lsst.pex.config.Field` values.

        See also
        --------
        lsst.pex.config.Field.toDict

        Notes
        -----
        This method uses the `~lsst.pex.config.Field.toDict` method of
        individual fields. Subclasses of `~lsst.pex.config.Field` may need to
        implement a ``toDict`` method for *this* method to work.
        """
        dict_ = {}
        for name, field in self._fields.items():
            dict_[name] = field.toDict(self)
        return dict_

    def names(self):
        """Get all the field names in the config, recursively.

        Returns
        -------
        names : `list` of `str`
            Field names.
        """
        #
        # Rather than sort out the recursion all over again use the
        # pre-existing saveToStream()
        #
        with io.StringIO() as strFd:
            self.saveToStream(strFd, "config")
            contents = strFd.getvalue()
            strFd.close()
        #
        # Pull the names out of the dumped config
        #
        keys = []
        for line in contents.split("\n"):
            if re.search(r"^((assert|import)\s+|\s*$|#)", line):
                continue

            mat = re.search(r"^(?:config\.)?([^=]+)\s*=\s*.*", line)
            if mat:
                keys.append(mat.group(1))

        return keys

    def _rename(self, name):
        """Rename this config object in its parent `~lsst.pex.config.Config`.

        Parameters
        ----------
        name : `str`
            New name for this config in its parent `~lsst.pex.config.Config`.

        Notes
        -----
        This method uses the `~lsst.pex.config.Field.rename` method of
        individual `lsst.pex.config.Field` instances.
        `lsst.pex.config.Field` subclasses may need to implement a ``rename``
        method for *this* method to work.

        See also
        --------
        lsst.pex.config.Field.rename
        """
        self._name = name
        for field in self._fields.values():
            field.rename(self)

    def validate(self):
        """Validate the Config, raising an exception if invalid.

        Raises
        ------
        lsst.pex.config.FieldValidationError
            Raised if verification fails.

        Notes
        -----
        The base class implementation performs type checks on all fields by
        calling their `~lsst.pex.config.Field.validate` methods.

        Complex single-field validation can be defined by deriving new Field
        types. For convenience, some derived `lsst.pex.config.Field`-types
        (`~lsst.pex.config.ConfigField` and
        `~lsst.pex.config.ConfigChoiceField`) are defined in `lsst.pex.config`
        that handle recursing into subconfigs.

        Inter-field relationships should only be checked in derived
        `~lsst.pex.config.Config` classes after calling this method, and base
        validation is complete.
        """
        for field in self._fields.values():
            field.validate(self)

    def formatHistory(self, name, **kwargs):
        """Format a configuration field's history to a human-readable format.

        Parameters
        ----------
        name : `str`
            Name of a `~lsst.pex.config.Field` in this config.
        kwargs
            Keyword arguments passed to `lsst.pex.config.history.format`.

        Returns
        -------
        history : `str`
            A string containing the formatted history.

        See also
        --------
        lsst.pex.config.history.format
        """
        import lsst.pex.config.history as pexHist
        return pexHist.format(self, name, **kwargs)

    history = property(lambda x: x._history)
    """Read-only history.
    """

    def __setattr__(self, attr, value, at=None, label="assignment"):
        """Set an attribute (such as a field's value).

        Notes
        -----
        Unlike normal Python objects, `~lsst.pex.config.Config` objects are
        locked such that no additional attributes nor properties may be added
        to them dynamically.

        Although this is not the standard Python behavior, it helps to protect
        users from accidentally mispelling a field name, or trying to set a
        non-existent field.
        """
        if attr in self._fields:
            if self._fields[attr].deprecated is not None:
                fullname = _joinNamePath(self._name, self._fields[attr].name)
                warnings.warn(f"Config field {fullname} is deprecated: {self._fields[attr].deprecated}",
                              FutureWarning)
            if at is None:
                at = getCallStack()
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
            raise AttributeError("%s has no attribute %s" % (_typeStr(self), attr))

    def __delattr__(self, attr, at=None, label="deletion"):
        if attr in self._fields:
            if at is None:
                at = getCallStack()
            self._fields[attr].__delete__(self, at=at, label=label)
        else:
            object.__delattr__(self, attr)

    def __eq__(self, other):
        if type(other) == type(self):
            for name in self._fields:
                thisValue = getattr(self, name)
                otherValue = getattr(other, name)
                if isinstance(thisValue, float) and math.isnan(thisValue):
                    if not math.isnan(otherValue):
                        return False
                elif thisValue != otherValue:
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
            ", ".join("%s=%r" % (k, v) for k, v in self.toDict().items() if v is not None)
        )

    def compare(self, other, shortcut=True, rtol=1E-8, atol=1E-8, output=None):
        """Compare this configuration to another `~lsst.pex.config.Config` for
        equality.

        Parameters
        ----------
        other : `lsst.pex.config.Config`
            Other `~lsst.pex.config.Config` object to compare against this
            config.
        shortcut : `bool`, optional
            If `True`, return as soon as an inequality is found. Default is
            `True`.
        rtol : `float`, optional
            Relative tolerance for floating point comparisons.
        atol : `float`, optional
            Absolute tolerance for floating point comparisons.
        output : callable, optional
            A callable that takes a string, used (possibly repeatedly) to
            report inequalities.

        Returns
        -------
        isEqual : `bool`
            `True` when the two `lsst.pex.config.Config` instances are equal.
            `False` if there is an inequality.

        See also
        --------
        lsst.pex.config.compareConfigs

        Notes
        -----
        Unselected targets of `~lsst.pex.config.RegistryField` fields and
        unselected choices of `~lsst.pex.config.ConfigChoiceField` fields
        are not considered by this method.

        Floating point comparisons are performed by `numpy.allclose`.
        """
        name1 = self._name if self._name is not None else "config"
        name2 = other._name if other._name is not None else "config"
        name = getComparisonName(name1, name2)
        return compareConfigs(name, self, other, shortcut=shortcut,
                              rtol=rtol, atol=atol, output=output)


def unreduceConfig(cls, stream):
    """Create a `~lsst.pex.config.Config` from a stream.

    Parameters
    ----------
    cls : `lsst.pex.config.Config`-type
        A `lsst.pex.config.Config` type (not an instance) that is instantiated
        with configurations in the ``stream``.
    stream : file-like object, `str`, or compiled string
        Stream containing configuration override code.

    Returns
    -------
    config : `lsst.pex.config.Config`
        Config instance.

    See also
    --------
    lsst.pex.config.Config.loadFromStream
    """
    config = cls()
    config.loadFromStream(stream)
    return config
