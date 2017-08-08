from _testLib import *
import lsst.pex.config
InnerConfigObject = lsst.pex.config.makeConfigClass(InnerControlObject)
OuterConfigObject = lsst.pex.config.makeConfigClass(OuterControlObject)
ConfigObject = lsst.pex.config.makeConfigClass(ControlObject)
