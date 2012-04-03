from .config import Config, Field, _typeStr
import traceback

__all__ = ["ChoiceField"]

class ChoiceField(Field):
    """
    Defines a Config Field which allows only a set of values
    All allowed must be of the same type.
    Allowed values should be provided as a dict of value, doc string pairs

    """
    def __init__(self, doc, dtype, allowed, default=None, optional=True):
        self.allowed = dict(allowed)
        if optional and None not in self.allowed: 
            self.allowed[None]="Field is optional"

        if len(self.allowed)==0:
            raise ValueError("ChoiceFields must allow at least one choice")
        
        doc += "\nAllowed values:\n"
        for choice, choiceDoc in self.allowed.iteritems():
            if choice is not None and not isinstance(choice, dtype):
                raise ValueError("ChoiceField's allowed choice %s is of incorrect type %s. Expected %s"%\
                        (choice, _typeStr(choice), _typeStr(dtype)))
            doc += "\t%s\t%s\n"%(str(choice), choiceDoc)

        Field.__init__(self, doc=doc, dtype=dtype, default=default, check=None, optional=optional)
        self.source = traceback.extract_stack(limit=2)[0]

    def validateValue(self, value):
        Field.validateValue(self, value)
        if value not in self.allowed:
            msg = "Value %s is not in the set of allowed values"%value
            raise ValueError(msg) 

