.. py:currentmodule:: lsst.pex.config

###################################################
Registry and RegistryField for configuring subtasks
###################################################

Example of a `RegistryField` created from a `Registry` object and use of both the `Registry.register` method and the `registerConfigurable` decorator::

    psfDeterminerRegistry = pexConfig.makeRegistry("""A registry of PSF determiner factories""")

    class PcaPsfDeterminerConfig(pexConfig.Config):
        spatialOrder = pexConfig.Field(
                "spatial order for PSF kernel creation", int, 2)
        [...]

    @pexConfig.registerConfigurable("pca", psfDeterminerRegistry)
    class PcaPsfDeterminer(object):
        ConfigClass = PcaPsfDeterminerConfig
            # associate this Configurable class with its Config class for use
            # by the registry
        def __init__(self, config, schema=None):
            [...]
        def determinePsf(self, exposure, psfCandidateList, metadata=None):
            [...]

    psfDeterminerRegistry.register("shapelet", ShapeletPsfDeterminer)

    class MeasurePsfConfig(pexConfig.Config):
        psfDeterminer = measAlg.psfDeterminerRegistry.makeField("PSF determination algorithm", default="pca")
