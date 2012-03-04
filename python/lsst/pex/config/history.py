import os
import re

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

colors = dict(
    value = "yellow",
    file = "green",
    text = "red",
    functionName = "blue",
    )


def _colorize(text, color):
    """Return a string that should display as coloured on a conformant terminal"""
    base = "\033["
    colorKeys = {
        "black"  : 0,
        "red"    : 1,
        "green"  : 2,
        "yellow" : 3,
        "blue"   : 4,
        "magenta": 5,
        "cyan"   : 6,
        "white"  : 7,
        }

    x = color.lower().split(";")
    color, bold = x.pop(0), False
    if x:
        props = x.pop(0)
        if props in ("bold",):
            bold = True

    try:
        _code = "%s" % (30 + colorKeys[color])
    except KeyError:
        raise RuntimeError("Unknown colour: %s" % color)

    if bold:
        _code += ";1"

    prefix = base + _code + "m"
    suffix = base + "m"

    return prefix + str(text) + suffix

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

class StackFrame(object):
    def __init__(self, stackTrace):
        self.fileName = stackTrace[0]
        self.lineNumber = stackTrace[1]
        self.functionName = stackTrace[2]
        self.text = stackTrace[3]

        self.fileName = re.sub(r'.*/python/lsst/', "", self.fileName)

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def format(config, name, writeSourceLine=True, prefix="", verbose=False):
    """Format the history record for config.name"""

    outputs = []
    for value, tb in config.history[name]:
        output = []
        for frame in [StackFrame(t) for t in tb]:
            if frame.functionName in ("__new__", "__set__", "__setattr__", "execfile", "wrapper") or \
                    os.path.split(frame.fileName)[1] in ("argparse.py", "argumentParser.py"):
                if not verbose:
                    continue

            line = []
            if writeSourceLine:
                line.append(["%s" % ("%s:%d" % (frame.fileName, frame.lineNumber)), "file",])

            line.append([frame.text, "text",])
            if False:
                line.append([frame.functionName, "functionName",])

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
    msg.append("%s.%s:" % (re.sub(r"^root\.", "", config._name), name))
    for value, output in outputs:
        line = prefix + _colorize("%-*s" % (valueLength, value), colors["value"]) + " "
        for i, vt in enumerate(output):
            if writeSourceLine:
                vt[0][0] = "%-*s" % (sourceLength, vt[0][0])
            
            output[i] = " ".join([_colorize(v, colors[t]) for v, t in vt])

        line += ("\n%*s" % (valueLength + 1, "")).join(output)
        msg.append(line)

    return "\n".join(msg)

