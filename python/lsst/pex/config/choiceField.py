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
__all__ = ["ChoiceField"]

from .config import Field, _typeStr
from .callStack import getStackFrame


class ChoiceField(Field):
    """A configuration field (`~lsst.pex.config.Field` subclass) that allows a
    user to select from a predefined set of values.

    Use ``ChoiceField`` when a configuration can only take one of a predefined
    set of values. Each choice must be of the same type.

    Parameters
    ----------
    doc : `str`
        Documentation string that describes the configuration field.
    dtype : class
        The type of the field's choices. For example, `str` or `int`.
    allowed : `dict`
        The allowed values. Keys are the allowed choices (of ``dtype``-type).
        Values are descriptions (`str`-type) of each choice.
    default : ``dtype``-type, optional
        The default value, which is of type ``dtype`` and one of the allowed
        choices.
    optional : `bool`, optional
        If `True`, this configuration field is *optional*. Default is `True`.

    See also
    --------
    ConfigChoiceField
    ConfigDictField
    ConfigField
    ConfigurableField
    DictField
    Field
    ListField
    RangeField
    RegistryField
    """
    def __init__(self, doc, dtype, allowed, default=None, optional=True):
        self.allowed = dict(allowed)
        if optional and None not in self.allowed:
            self.allowed[None] = "Field is optional"

        if len(self.allowed) == 0:
            raise ValueError("ChoiceFields must allow at least one choice")

        Field.__init__(self, doc=doc, dtype=dtype, default=default,
                       check=None, optional=optional)

        self.__doc__ += "\n\nAllowed values:\n\n"
        for choice, choiceDoc in self.allowed.items():
            if choice is not None and not isinstance(choice, dtype):
                raise ValueError("ChoiceField's allowed choice %s is of incorrect type %s. Expected %s" %
                                 (choice, _typeStr(choice), _typeStr(dtype)))
            self.__doc__ += "%s\n  %s\n" % ('``{0!r}``'.format(str(choice)), choiceDoc)

        self.source = getStackFrame()

    def _validateValue(self, value):
        Field._validateValue(self, value)
        if value not in self.allowed:
            msg = "Value {} is not allowed.\n" \
                "\tAllowed values: [{}]".format(value, ", ".join(str(key) for key in self.allowed))
            raise ValueError(msg)
