#
# LSST Data Management System
# Copyright 2008-2013 LSST Corporation.
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

__all__ = ["ConfigField"]

from .config import Config, Field, FieldValidationError, _joinNamePath, _typeStr
from .comparison import compareConfigs, getComparisonName
from .callStack import getCallStack, getStackFrame


class ConfigField(Field):
    """A configuration field (`~lsst.pex.config.Field` subclass) that takes a
    `~lsst.pex.config.Config`-type as a value.

    Parameters
    ----------
    doc : `str`
        A description of the configuration field.
    dtype : `lsst.pex.config.Config`-type
        The type of the field, which must be a subclass of
        `lsst.pex.config.Config`.
    default : `lsst.pex.config.Config`, optional
        If default is `None`, the field will default to a default-constructed
        instance of ``dtype``. Additionally, to allow for fewer deep-copies,
        assigning an instance of ``ConfigField`` to ``dtype`` itself, is
        considered equivalent to assigning a default-constructed sub-config.
        This means that the argument default can be ``dtype``, as well as an
        instance of ``dtype``.
    check : callable, optional
        A callback function that validates the field's value, returning `True`
        if the value is valid, and `False` otherwise.
    deprecated : None or `str`, optional
        A description of why this Field is deprecated, including removal date.
        If not None, the string is appended to the docstring for this Field.

    See also
    --------
    ChoiceField
    ConfigChoiceField
    ConfigDictField
    ConfigurableField
    DictField
    Field
    ListField
    RangeField
    RegistryField

    Notes
    -----
    The behavior of this type of field is much like that of the base `Field`
    type.

    Assigning to ``ConfigField`` will update all of the fields in the
    configuration.
    """

    def __init__(self, doc, dtype, default=None, check=None, deprecated=None):
        if not issubclass(dtype, Config):
            raise ValueError("dtype=%s is not a subclass of Config" %
                             _typeStr(dtype))
        if default is None:
            default = dtype
        source = getStackFrame()
        self._setup(doc=doc, dtype=dtype, default=default, check=check,
                    optional=False, source=source, deprecated=deprecated)

    def __get__(self, instance, owner=None):
        if instance is None or not isinstance(instance, Config):
            return self
        else:
            value = instance._storage.get(self.name, None)
            if value is None:
                at = getCallStack()
                at.insert(0, self.source)
                self.__set__(instance, self.default, at=at, label="default")
            return value

    def __set__(self, instance, value, at=None, label="assignment"):
        if instance._frozen:
            raise FieldValidationError(self, instance,
                                       "Cannot modify a frozen Config")
        name = _joinNamePath(prefix=instance._name, name=self.name)

        if value != self.dtype and type(value) != self.dtype:
            msg = "Value %s is of incorrect type %s. Expected %s" % \
                (value, _typeStr(value), _typeStr(self.dtype))
            raise FieldValidationError(self, instance, msg)

        if at is None:
            at = getCallStack()

        oldValue = instance._storage.get(self.name, None)
        if oldValue is None:
            if value == self.dtype:
                instance._storage[self.name] = self.dtype(__name=name, __at=at, __label=label)
            else:
                instance._storage[self.name] = self.dtype(__name=name, __at=at,
                                                          __label=label, **value._storage)
        else:
            if value == self.dtype:
                value = value()
            oldValue.update(__at=at, __label=label, **value._storage)
        history = instance._history.setdefault(self.name, [])
        history.append(("config value set", at, label))

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
        value = self.__get__(instance)
        value._rename(_joinNamePath(instance._name, self.name))

    def _collectImports(self, instance, imports):
        value = self.__get__(instance)
        value._collectImports()
        imports |= value._imports

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
        value._save(outfile)

    def freeze(self, instance):
        """Make this field read-only.

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
        value = self.__get__(instance)
        value.freeze()

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
        value = self.__get__(instance)
        return value.toDict()

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
        value.validate()

        if self.check is not None and not self.check(value):
            msg = "%s is not a valid value" % str(value)
            raise FieldValidationError(self, instance, msg)

    def _compare(self, instance1, instance2, shortcut, rtol, atol, output):
        """Compare two fields for equality.

        Used by `ConfigField.compare`.

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
            A callable that takes a string, used (possibly repeatedly) to report inequalities.

        Returns
        -------
        isEqual : bool
            `True` if the fields are equal, `False` otherwise.

        Notes
        -----
        Floating point comparisons are performed by `numpy.allclose`.
        """
        c1 = getattr(instance1, self.name)
        c2 = getattr(instance2, self.name)
        name = getComparisonName(
            _joinNamePath(instance1._name, self.name),
            _joinNamePath(instance2._name, self.name)
        )
        return compareConfigs(name, c1, c2, shortcut=shortcut, rtol=rtol, atol=atol, output=output)
