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

import os
import re
import sys

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-


class Color(object):
    categories = dict(
        NAME = "blue",
        VALUE = "yellow",
        FILE = "green",
        TEXT = "red",
        FUNCTION_NAME = "blue",
        )

    colors = {
        "black"  : 0,
        "red"    : 1,
        "green"  : 2,
        "yellow" : 3,
        "blue"   : 4,
        "magenta": 5,
        "cyan"   : 6,
        "white"  : 7,
        }

    _colorize = True

    def __init__(self, text, category):
        """Return a string that should display as coloured on a conformant terminal"""
        try:
            color = Color.categories[category]
        except KeyError:
            raise RuntimeError("Unknown category: %s" % category)

        self.rawText = str(text)
        x = color.lower().split(";")
        self.color, bold = x.pop(0), False
        if x:
            props = x.pop(0)
            if props in ("bold",):
                bold = True

        try:
            self._code = "%s" % (30 + Color.colors[self.color])
        except KeyError:
            raise RuntimeError("Unknown colour: %s" % self.color)

        if bold:
            self._code += ";1"

    @staticmethod
    def colorize(val=None):
        """Should I colour strings?  With an argument, set the value"""

        if val is not None:
            Color._colorize = val

            if isinstance(val, dict):
                unknown = []
                for k in val.keys():
                    if Color.categories.has_key(k):
                        if Color.colors.has_key(val[k]):
                            Color.categories[k] = val[k]
                        else:
                            print >> sys.stderr, "Unknown colour %s for category %s" % (val[k], k)
                    else:
                        unknown.append(k)

                if unknown:
                    print >> sys.stderr, "Unknown colourizing category: %s" % " ".join(unknown)

        return Color._colorize

    def __str__(self):
        if not self.colorize():
            return self.rawText

        base = "\033["

        prefix = base + self._code + "m"
        suffix = base + "m"

        return prefix + self.rawText + suffix


def _colorize(text, category):
    text = Color(text, category)
    return str(text)

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

class StackFrame(object):
    def __init__(self, stackTrace):
        self.fileName = stackTrace[0]
        self.lineNumber = stackTrace[1]
        self.functionName = stackTrace[2]
        self.text = stackTrace[3]

        self.fileName = re.sub(r'.*/python/lsst/', "", self.fileName)

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def format(config, name=None, writeSourceLine=True, prefix="", verbose=False):
    """Format the history record for config.name"""

    if name is None:
        for i, name in enumerate(config.history.keys()):
            if i > 0:
                print
            print format(config, name)

    outputs = []
    for value, tb, label in config.history[name]:
        output = []
        for frame in [StackFrame(t) for t in tb]:
            if frame.functionName in ("__new__", "__set__", "__setattr__", "execfile", "wrapper") or \
                    os.path.split(frame.fileName)[1] in ("argparse.py", "argumentParser.py"):
                if not verbose:
                    continue

            line = []
            if writeSourceLine:
                line.append(["%s" % ("%s:%d" % (frame.fileName, frame.lineNumber)), "FILE",])

            line.append([frame.text, "TEXT",])
            if False:
                line.append([frame.functionName, "FUNCTION_NAME",])

            output.append(line)

        outputs.append([value, output])
    #
    # Find the maximum widths of the value and file:lineNo fields
    #
    if writeSourceLine:
        sourceLengths = []
        for value, output in outputs:
            sourceLengths.append(max([len(x[0][0]) for x in output]))
        sourceLength = max(sourceLengths)

    valueLength = len(prefix) + max([len(str(value)) for value, output in outputs])
    #
    # actually generate the config history
    #
    msg = []
    fullname = "%s.%s" %(config._name, name) if config._name is not None else name 
    msg.append(_colorize(re.sub(r"^root\.", "", fullname), "NAME"))
    for value, output in outputs:
        line = prefix + _colorize("%-*s" % (valueLength, value), "VALUE") + " "
        for i, vt in enumerate(output):
            if writeSourceLine:
                vt[0][0] = "%-*s" % (sourceLength, vt[0][0])
            
            output[i] = " ".join([_colorize(v, t) for v, t in vt])

        line += ("\n%*s" % (valueLength + 1, "")).join(output)
        msg.append(line)

    return "\n".join(msg)

