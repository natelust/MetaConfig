from _testLib import *
import lsst.pex.config
import sys
module = sys.modules[__name__]
InnerConfigObject = lsst.pex.config.makeConfigClass(InnerControlObject, module=module)
OuterConfigObject = lsst.pex.config.makeConfigClass(OuterControlObject, module=module)
ConfigObject = lsst.pex.config.makeConfigClass(ControlObject, module=module)
