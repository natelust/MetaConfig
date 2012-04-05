from .config import Config, Field, _typeStr
import traceback

__all__ = ["RangeField"]

class RangeField(Field):
    """
    Defines a Config Field which allows only a range of values.
    The range is defined by providing min and/or max values.
    If min or max is None, the range will be open in that direction
    If inclusive[Min|Max] is True the range will include the [min|max] value
    
    """

    supportedTypes=(int, float)

    def __init__(self, doc, dtype, default=None, optional=False, 
            min=None, max=None, inclusiveMin=True, inclusiveMax=False):
        if dtype not in self.supportedTypes:
            raise ValueError("Unsupported RangeField dtype %s"%(_typeStr(dtype)))
        source = traceback.extract_stack(limit=2)[0]
        if min is None and max is None:
            raise ValueError("min and max cannot both be None")

        if min is not None and max is not None and min > max:
            swap(min, max)
        self.min = min
        self.max = max

        self.rangeString =  "%s%s,%s%s" % \
                (("[" if inclusiveMin else "("),
                ("-inf" if self.min is None else self.min),
                ("inf" if self.max is None else self.max),
                ("]" if inclusiveMax else ")"))
        doc += "\n\tValid Range = " + self.rangeString
        if inclusiveMax:
            self.maxCheck = lambda x, y: True if y is None else x <= y
        else:
            self.maxCheck = lambda x, y: True if y is None else x < y
        if inclusiveMin:
            self.minCheck = lambda x, y: True if y is None else x >= y
        else:
            self.minCheck = lambda x, y: True if y is None else x > y
        self._setup( doc, dtype=dtype, default=default, check=None, optional=optional, source=source) 

    def validateValue(self, value):
        Field.validateValue(self, value)
        if not self.minCheck(value, self.min) or \
                not self.maxCheck(value, self.max):
            msg = "%s is outside of valid range %s"%(value, self.rangeString)
            raise ValueError(msg)
