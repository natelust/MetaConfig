.. py:currentmodule:: lsst.pex.config

#############################
Types of configuration fields
#############################

.. TODO: improve this page to summarize the purpose of each field, and then have a dedicated section for each field. https://jira.lsstcorp.org/browse/DM-17196

Attributes of the configuration object must be subclasses of `Field`.
A number of these are predefined: `Field`, `RangeField`, `ChoiceField`, `ListField`, `ConfigField`, `ConfigChoiceField`, `RegistryField` and `ConfigurableField`.

Example of `RangeField`:

.. code-block:: python

    class BackgroundConfig(pexConfig.Config):
        """Parameters for controlling background estimation.
        """
        binSize = pexConfig.RangeField(
            doc=("How large a region of the sky should be "
                 "used for each background point."),
            dtype=int, default=256, min=10
        )

Example of `ListField` and `Config` inheritance:

.. code-block:: python

    class OutlierRejectedCoaddConfig(CoaddTask.ConfigClass):
        """Additional parameters for outlier-rejected coadds.
        """
        subregionSize = pexConfig.ListField(
            dtype=int,
            doc=("width, height of stack subregion size; make "
                 "small enough that a full stack of images will "
                 "fit into memory at once."),
            length=2,
            default=(200, 200),
            optional=None,
        )

Examples of `ChoiceField` and `ConfigField` and the use of the `Config` object's `Config.setDefaults` and `Config.validate` methods:

.. code-block:: python

    class InitialPsfConfig(pexConfig.Config):
        """A config that describes the initial PSF used 
        for detection and measurement (before PSF
        determination is done).
        """

        model = pexConfig.ChoiceField(
            dtype=str,
            doc="PSF model type.",
            default="SingleGaussian",
            allowed={
                "SingleGaussian": "Single Gaussian model",
                "DoubleGaussian": "Double Gaussian model",
            },
        )

    class CalibrateConfig(pexConfig.Config):
        """A config to configure the calibration of an Exposure.
        """
        initialPsf = pexConfig.ConfigField(
            dtype=InitialPsfConfig,
            doc=InitialPsfConfig.__doc__)
        detection = pexConfig.ConfigField(
            dtype=measAlg.SourceDetectionTask.ConfigClass,
            doc="Initial (high-threshold) detection phase for calibration."
        )

        def setDefaults(self):
            self.detection.includeThresholdMultiplier = 10.0

        def validate(self):
            pexConfig.Config.validate(self)
            if self.doComputeApCorr and not self.doPsf:
                raise ValueError("Cannot compute aperture correction "
                                 "without doing PSF determination.")
