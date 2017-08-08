#
# LSST Data Management System
# Copyright 2017 AURA/LSST.
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

__all__ = ['getCallerFrame', 'getStackFrame', 'StackFrame', 'getCallStack']

import inspect
import linecache


def getCallerFrame(relative=0):
    """Get the frame for the user's caller.

    Parameters
    ----------
    relative : `int`, optional
        Number of frames (0 or more) above the caller to retrieve. Default is 0.

    Returns
    -------
    frame : `__builtin__.Frame`
        Frame for the caller.

    Notes
    -----
    This function is excluded from the frame.
    """
    frame = inspect.currentframe().f_back.f_back  # Our caller's caller
    for ii in range(relative):
        frame = frame.f_back
    return frame


def getStackFrame(relative=0):
    """Get the `StackFrame` for the user's caller.

    Parameters
    ----------
    relative : `int`, optional
        Number of frames (0 or more) above the caller to retrieve.

    Returns
    -------
    frame : `StackFrame`
        Stack frame for the caller.
    """
    frame = getCallerFrame(relative + 1)
    return StackFrame.fromFrame(frame)


class StackFrame:
    """A single element of the stack trace.

    This differs slightly from the standard system mechanisms for getting a
    stack trace by the fact that it does not look up the source code until it
    is absolutely necessary, reducing the I/O.

    Parameters
    ----------
    filename : `str`
        Name of file containing the code being executed.
    lineno : `int`
        Line number of file being executed.
    function : `str`
        Function name being executed.
    content : `str`, optional
        The actual content being executed. If not provided, it will be loaded
        from the file.

    Notes
    -----
    This differs slightly from the standard system mechanisms for getting a
    stack trace by the fact that it does not look up the source code until it
    is absolutely necessary, reducing the I/O.

    See also
    --------
    getStackFrame
    """

    _STRIP = "/python/lsst/"
    """String to strip from the ``filename`` in the constructor."""

    def __init__(self, filename, lineno, function, content=None):
        loc = filename.rfind(self._STRIP)
        if loc > 0:
            filename = filename[loc + len(self._STRIP):]
        self.filename = filename
        self.lineno = lineno
        self.function = function
        self._content = content

    @property
    def content(self):
        """Content being executed (loaded on demand) (`str`).
        """
        if self._content is None:
            self._content = linecache.getline(self.filename, self.lineno).strip()
        return self._content

    @classmethod
    def fromFrame(cls, frame):
        """Construct from a Frame object.

        Parameters
        ----------
        frame : `Frame`
            Frame object to interpret, such as from `inspect.currentframe`.

        Returns
        -------
        stackFrame : `StackFrame`
            A `StackFrame` instance.

        Examples
        --------
        `inspect.currentframe` provides a Frame object. This is a convenience
        constructor to interpret that Frame object:

        >>> import inspect
        >>> stackFrame = StackFrame.fromFrame(inspect.currentframe())
        """
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        function = frame.f_code.co_name
        return cls(filename, lineno, function)

    def __repr__(self):
        return "%s(%s, %s, %s)" % (self.__class__.__name__, self.filename, self.lineno, self.function)

    def format(self, full=False):
        """Format for printing.

        Parameters
        ----------
        full : `bool`, optional
            If `True`, output includes the conentent (`StackFrame.content`) being executed. Default
            is `False`.

        Returns
        -------
        result : `str`
            Formatted string.
        """
        result = "  File %s:%s (%s)" % (self.filename, self.lineno, self.function)
        if full:
            result += "\n    %s" % (self.content,)
        return result


def getCallStack(skip=0):
    """Retrieve the call stack for the caller.

    Parameters
    ----------
    skip : `int`, non-negative
        Number of stack frames above caller to skip.

    Returns
    -------
    output : `list` of `StackFrame`
        The call stack. The `list` is ordered with the most recent frame to
        last.

    Notes
    -----
    This function is excluded from the call stack.
    """
    frame = getCallerFrame(skip + 1)
    stack = []
    while frame:
        stack.append(StackFrame.fromFrame(frame))
        frame = frame.f_back
    return list(reversed(stack))
