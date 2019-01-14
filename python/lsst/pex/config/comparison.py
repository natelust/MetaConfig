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
"""Helper functions for comparing `lsst.pex.config.Config` instancess.

Theses function should be use for any comparison in a `lsst.pex.Config.compare`
or `lsst.pex.config.Field._compare` implementation, as they take care of
writing messages as well as floating-point comparisons and shortcuts.
"""

import numpy

__all__ = ("getComparisonName", "compareScalars", "compareConfigs")


def getComparisonName(name1, name2):
    """Create a comparison name that is used for printed output of comparisons.

    Parameters
    ----------
    name1 : `str`
        Name of the first configuration.
    name2 : `str`
        Name of the second configuration.

    Returns
    -------
    name : `str`
        When ``name1`` and ``name2`` are equal, the returned name is
        simply one of the names. When they are different the returned name is
        formatted as ``"{name1} / {name2}"``.
    """
    if name1 != name2:
        return "%s / %s" % (name1, name2)
    return name1


def compareScalars(name, v1, v2, output, rtol=1E-8, atol=1E-8, dtype=None):
    """Compare two scalar values for equality.

    This function is a helper for `lsst.pex.config.Config.compare`.

    Parameters
    ----------
    name : `str`
        Name to use when reporting differences, typically created by
        `getComparisonName`.
    v1 : object
        Left-hand side value to compare.
    v2 : object
        Right-hand side value to compare.
    output : callable or `None`
        A callable that takes a string, used (possibly repeatedly) to report
        inequalities (for example, `print`). Set to `None` to disable output.
    rtol : `float`, optional
        Relative tolerance for floating point comparisons.
    atol : `float`, optional
        Absolute tolerance for floating point comparisons.
    dtype : class, optional
        Data type of values for comparison. May be `None` if values are not
        floating-point.

    Returns
    -------
    areEqual : `bool`
        `True` if the values are equal, `False` if they are not.

    See also
    --------
    lsst.pex.config.compareConfigs

    Notes
    -----
    Floating point comparisons are performed by `numpy.allclose`.
    """
    if v1 is None or v2 is None:
        result = (v1 == v2)
    elif dtype in (float, complex):
        result = numpy.allclose(v1, v2, rtol=rtol, atol=atol) or (numpy.isnan(v1) and numpy.isnan(v2))
    else:
        result = (v1 == v2)
    if not result and output is not None:
        output("Inequality in %s: %r != %r" % (name, v1, v2))
    return result


def compareConfigs(name, c1, c2, shortcut=True, rtol=1E-8, atol=1E-8, output=None):
    """Compare two `lsst.pex.config.Config` instances for equality.

    This function is a helper for `lsst.pex.config.Config.compare`.

    Parameters
    ----------
    name : `str`
        Name to use when reporting differences, typically created by
        `getComparisonName`.
    v1 : `lsst.pex.config.Config`
        Left-hand side config to compare.
    v2 : `lsst.pex.config.Config`
        Right-hand side config to compare.
    shortcut : `bool`, optional
        If `True`, return as soon as an inequality is found. Default is `True`.
    rtol : `float`, optional
        Relative tolerance for floating point comparisons.
    atol : `float`, optional
        Absolute tolerance for floating point comparisons.
    output : callable, optional
        A callable that takes a string, used (possibly repeatedly) to report
        inequalities. For example: `print`.

    Returns
    -------
    areEqual : `bool`
        `True` when the two `lsst.pex.config.Config` instances are equal.
        `False` if there is an inequality.

    See also
    --------
    lsst.pex.config.compareScalars

    Notes
    -----
    Floating point comparisons are performed by `numpy.allclose`.

    If ``c1`` or ``c2`` contain `~lsst.pex.config.RegistryField` or
    `~lsst.pex.config.ConfigChoiceField` instances, *unselected*
    `~lsst.pex.config.Config` instances will not be compared.
    """
    assert name is not None
    if c1 is None:
        if c2 is None:
            return True
        else:
            if output is not None:
                output("LHS is None for %s" % name)
            return False
    else:
        if c2 is None:
            if output is not None:
                output("RHS is None for %s" % name)
            return False
    if type(c1) != type(c2):
        if output is not None:
            output("Config types do not match for %s: %s != %s" % (name, type(c1), type(c2)))
        return False
    equal = True
    for field in c1._fields.values():
        result = field._compare(c1, c2, shortcut=shortcut, rtol=rtol, atol=atol, output=output)
        if not result and shortcut:
            return False
        equal = equal and result
    return equal
