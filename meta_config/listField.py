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

__all__ = ["ListField"]

import collections.abc

from .config import Field, FieldValidationError, _typeStr, _autocast, _joinNamePath
from .comparison import compareScalars, getComparisonName
from .callStack import getCallStack, getStackFrame


class List(collections.abc.MutableSequence):
    """List collection used internally by `ListField`.

    Parameters
    ----------
    config : `lsst.pex.config.Config`
        Config instance that contains the ``field``.
    field : `ListField`
        Instance of the `ListField` using this ``List``.
    value : sequence
        Sequence of values that are inserted into this ``List``.
    at : `list` of `lsst.pex.config.callStack.StackFrame`
        The call stack (created by `lsst.pex.config.callStack.getCallStack`).
    label : `str`
        Event label for the history.
    setHistory : `bool`, optional
        Enable setting the field's history, using the value of the ``at``
        parameter. Default is `True`.

    Raises
    ------
    FieldValidationError
        Raised if an item in the ``value`` parameter does not have the
        appropriate type for this field or does not pass the
        `ListField.itemCheck` method of the ``field`` parameter.
    """

    def __init__(self, config, field, value, at, label, setHistory=True):
        self._field = field
        self._config = config
        self._history = self._config._history.setdefault(self._field.name, [])
        self._list = []
        self.__doc__ = field.doc
        if value is not None:
            try:
                for i, x in enumerate(value):
                    self.insert(i, x, setHistory=False)
            except TypeError:
                msg = "Value %s is of incorrect type %s. Sequence type expected" % (value, _typeStr(value))
                raise FieldValidationError(self._field, self._config, msg)
        if setHistory:
            self.history.append((list(self._list), at, label))

    def validateItem(self, i, x):
        """Validate an item to determine if it can be included in the list.

        Parameters
        ----------
        i : `int`
            Index of the item in the `list`.
        x : object
            Item in the `list`.

        Raises
        ------
        FieldValidationError
            Raised if an item in the ``value`` parameter does not have the
            appropriate type for this field or does not pass the field's
            `ListField.itemCheck` method.
        """

        if not isinstance(x, self._field.itemtype) and x is not None:
            msg = "Item at position %d with value %s is of incorrect type %s. Expected %s" % \
                (i, x, _typeStr(x), _typeStr(self._field.itemtype))
            raise FieldValidationError(self._field, self._config, msg)

        if self._field.itemCheck is not None and not self._field.itemCheck(x):
            msg = "Item at position %d is not a valid value: %s" % (i, x)
            raise FieldValidationError(self._field, self._config, msg)

    def list(self):
        """Sequence of items contained by the `List` (`list`).
        """
        return self._list

    history = property(lambda x: x._history)
    """Read-only history.
    """

    def __contains__(self, x):
        return x in self._list

    def __len__(self):
        return len(self._list)

    def __setitem__(self, i, x, at=None, label="setitem", setHistory=True):
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config,
                                       "Cannot modify a frozen Config")
        if isinstance(i, slice):
            k, stop, step = i.indices(len(self))
            for j, xj in enumerate(x):
                xj = _autocast(xj, self._field.itemtype)
                self.validateItem(k, xj)
                x[j] = xj
                k += step
        else:
            x = _autocast(x, self._field.itemtype)
            self.validateItem(i, x)

        self._list[i] = x
        if setHistory:
            if at is None:
                at = getCallStack()
            self.history.append((list(self._list), at, label))

    def __getitem__(self, i):
        return self._list[i]

    def __delitem__(self, i, at=None, label="delitem", setHistory=True):
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config,
                                       "Cannot modify a frozen Config")
        del self._list[i]
        if setHistory:
            if at is None:
                at = getCallStack()
            self.history.append((list(self._list), at, label))

    def __iter__(self):
        return iter(self._list)

    def insert(self, i, x, at=None, label="insert", setHistory=True):
        """Insert an item into the list at the given index.

        Parameters
        ----------
        i : `int`
            Index where the item is inserted.
        x : object
            Item that is inserted.
        at : `list` of `lsst.pex.config.callStack.StackFrame`, optional
            The call stack (created by
            `lsst.pex.config.callStack.getCallStack`).
        label : `str`, optional
            Event label for the history.
        setHistory : `bool`, optional
            Enable setting the field's history, using the value of the ``at``
            parameter. Default is `True`.
        """
        if at is None:
            at = getCallStack()
        self.__setitem__(slice(i, i), [x], at=at, label=label, setHistory=setHistory)

    def __repr__(self):
        return repr(self._list)

    def __str__(self):
        return str(self._list)

    def __eq__(self, other):
        try:
            if len(self) != len(other):
                return False

            for i, j in zip(self, other):
                if i != j:
                    return False
            return True
        except AttributeError:
            # other is not a sequence type
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __setattr__(self, attr, value, at=None, label="assignment"):
        if hasattr(getattr(self.__class__, attr, None), '__set__'):
            # This allows properties to work.
            object.__setattr__(self, attr, value)
        elif attr in self.__dict__ or attr in ["_field", "_config", "_history", "_list", "__doc__"]:
            # This allows specific private attributes to work.
            object.__setattr__(self, attr, value)
        else:
            # We throw everything else.
            msg = "%s has no attribute %s" % (_typeStr(self._field), attr)
            raise FieldValidationError(self._field, self._config, msg)


class ListField(Field):
    """A configuration field (`~lsst.pex.config.Field` subclass) that contains
    a list of values of a specific type.

    Parameters
    ----------
    doc : `str`
        A description of the field.
    dtype : class
        The data type of items in the list.
    default : sequence, optional
        The default items for the field.
    optional : `bool`, optional
        Set whether the field is *optional*. When `False`,
        `lsst.pex.config.Config.validate` will fail if the field's value is
        `None`.
    listCheck : callable, optional
        A callable that validates the list as a whole.
    itemCheck : callable, optional
        A callable that validates individual items in the list.
    length : `int`, optional
        If set, this field must contain exactly ``length`` number of items.
    minLength : `int`, optional
        If set, this field must contain *at least* ``minLength`` number of
        items.
    maxLength : `int`, optional
        If set, this field must contain *no more than* ``maxLength`` number of
        items.
    deprecated : None or `str`, optional
        A description of why this Field is deprecated, including removal date.
        If not None, the string is appended to the docstring for this Field.

    See also
    --------
    ChoiceField
    ConfigChoiceField
    ConfigDictField
    ConfigField
    ConfigurableField
    DictField
    Field
    RangeField
    RegistryField
    """
    def __init__(self, doc, dtype, default=None, optional=False,
                 listCheck=None, itemCheck=None,
                 length=None, minLength=None, maxLength=None,
                 deprecated=None):
        if dtype not in Field.supportedTypes:
            raise ValueError("Unsupported dtype %s" % _typeStr(dtype))
        if length is not None:
            if length <= 0:
                raise ValueError("'length' (%d) must be positive" % length)
            minLength = None
            maxLength = None
        else:
            if maxLength is not None and maxLength <= 0:
                raise ValueError("'maxLength' (%d) must be positive" % maxLength)
            if minLength is not None and maxLength is not None \
                    and minLength > maxLength:
                raise ValueError("'maxLength' (%d) must be at least"
                                 " as large as 'minLength' (%d)" % (maxLength, minLength))

        if listCheck is not None and not hasattr(listCheck, "__call__"):
            raise ValueError("'listCheck' must be callable")
        if itemCheck is not None and not hasattr(itemCheck, "__call__"):
            raise ValueError("'itemCheck' must be callable")

        source = getStackFrame()
        self._setup(doc=doc, dtype=List, default=default, check=None, optional=optional, source=source,
                    deprecated=deprecated)

        self.listCheck = listCheck
        """Callable used to check the list as a whole.
        """

        self.itemCheck = itemCheck
        """Callable used to validate individual items as they are inserted
        into the list.
        """

        self.itemtype = dtype
        """Data type of list items.
        """

        self.length = length
        """Number of items that must be present in the list (or `None` to
        disable checking the list's length).
        """

        self.minLength = minLength
        """Minimum number of items that must be present in the list (or `None`
        to disable checking the list's minimum length).
        """

        self.maxLength = maxLength
        """Maximum number of items that must be present in the list (or `None`
        to disable checking the list's maximum length).
        """

    def validate(self, instance):
        """Validate the field.

        Parameters
        ----------
        instance : `lsst.pex.config.Config`
            The config instance that contains this field.

        Raises
        ------
        lsst.pex.config.FieldValidationError
            Raised if:

            - The field is not optional, but the value is `None`.
            - The list itself does not meet the requirements of the `length`,
              `minLength`, or `maxLength` attributes.
            - The `listCheck` callable returns `False`.

        Notes
        -----
        Individual item checks (`itemCheck`) are applied when each item is
        set and are not re-checked by this method.
        """
        Field.validate(self, instance)
        value = self.__get__(instance)
        if value is not None:
            lenValue = len(value)
            if self.length is not None and not lenValue == self.length:
                msg = "Required list length=%d, got length=%d" % (self.length, lenValue)
                raise FieldValidationError(self, instance, msg)
            elif self.minLength is not None and lenValue < self.minLength:
                msg = "Minimum allowed list length=%d, got length=%d" % (self.minLength, lenValue)
                raise FieldValidationError(self, instance, msg)
            elif self.maxLength is not None and lenValue > self.maxLength:
                msg = "Maximum allowed list length=%d, got length=%d" % (self.maxLength, lenValue)
                raise FieldValidationError(self, instance, msg)
            elif self.listCheck is not None and not self.listCheck(value):
                msg = "%s is not a valid value" % str(value)
                raise FieldValidationError(self, instance, msg)

    def __set__(self, instance, value, at=None, label="assignment"):
        if instance._frozen:
            raise FieldValidationError(self, instance, "Cannot modify a frozen Config")

        if at is None:
            at = getCallStack()

        if value is not None:
            value = List(instance, self, value, at, label)
        else:
            history = instance._history.setdefault(self.name, [])
            history.append((value, at, label))

        instance._storage[self.name] = value

    def toDict(self, instance):
        """Convert the value of this field to a plain `list`.

        `lsst.pex.config.Config.toDict` is the primary user of this method.

        Parameters
        ----------
        instance : `lsst.pex.config.Config`
            The config instance that contains this field.

        Returns
        -------
        `list`
            Plain `list` of items, or `None` if the field is not set.
        """
        value = self.__get__(instance)
        return list(value) if value is not None else None

    def _compare(self, instance1, instance2, shortcut, rtol, atol, output):
        """Compare two config instances for equality with respect to this
        field.

        `lsst.pex.config.config.compare` is the primary user of this method.

        Parameters
        ----------
        instance1 : `lsst.pex.config.Config`
            Left-hand-side `~lsst.pex.config.Config` instance in the
            comparison.
        instance2 : `lsst.pex.config.Config`
            Right-hand-side `~lsst.pex.config.Config` instance in the
            comparison.
        shortcut : `bool`
            If `True`, return as soon as an **inequality** is found.
        rtol : `float`
            Relative tolerance for floating point comparisons.
        atol : `float`
            Absolute tolerance for floating point comparisons.
        output : callable
            If not None, a callable that takes a `str`, used (possibly
            repeatedly) to report inequalities.

        Returns
        -------
        equal : `bool`
            `True` if the fields are equal; `False` otherwise.

        Notes
        -----
        Floating point comparisons are performed by `numpy.allclose`.
        """
        l1 = getattr(instance1, self.name)
        l2 = getattr(instance2, self.name)
        name = getComparisonName(
            _joinNamePath(instance1._name, self.name),
            _joinNamePath(instance2._name, self.name)
        )
        if not compareScalars("isnone for %s" % name, l1 is None, l2 is None, output=output):
            return False
        if l1 is None and l2 is None:
            return True
        if not compareScalars("size for %s" % name, len(l1), len(l2), output=output):
            return False
        equal = True
        for n, v1, v2 in zip(range(len(l1)), l1, l2):
            result = compareScalars("%s[%d]" % (name, n), v1, v2, dtype=self.dtype,
                                    rtol=rtol, atol=atol, output=output)
            if not result and shortcut:
                return False
            equal = equal and result
        return equal
