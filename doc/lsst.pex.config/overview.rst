.. py:currentmodule:: lsst.pex.config

###########################
Overview of lsst.pex.config
###########################

The ``lsst.pex.config`` module provides a configuration system for the LSST Science Pipelines.

Key concepts: configuration objects and field attributes
========================================================

Configurations are hierarchical trees of parameters used to control the execution of code.
They should not be confused with input data.

Configurations are stored in instances of a "config" object, which are subclasses of the `Config` class.
Different configuration sets are associated with different subclasses of `Config`.
For example, in the task framework each task is associated with a specific `Config` subclass.

Configuration objects have **fields** that are discrete settings.
These fields are attributes on config classes.
Fields are themselves objects, usually an instance of the `Field` class, or a subclass of `Field`.
Fields have hooks for validation and documentation, and can even have their values recorded for provenance.
`Field` and `Field` subclasses are specialized for storing different types of configuration values, from simple integers to lists and mappings, and even other configuration objects or *configurable* objects.
See :doc:`field-types` for more information.

.. note::

   Fields are attributes of config *classes*, not *instances*.
   When you access a field on a config instance, you don't get the `Field` instance itself, but rather an object that represents the *value* of that field, like an `int` or a specialized container (like `lsst.pex.config.List`).
   Think of field attributes like `property` attributes of classes, which implement custom getters and setters on otherwise simple attributes.
   For more background on the architecture of fields, see the Notes section of the `Field` class reference.

Example config class and usage
==============================

Here is a config class that includes five fields:

.. code-block:: python

   import lsst.pex.config as pexConfig
   
   class IsrTaskConfig(pexConfig.Config):
       doWrite = pexConfig.Field(
           doc="Write output?",
           dtype=bool,
           default=True)
       fwhm = pexConfig.Field(
           doc="FWHM of PSF (arcsec)",
           dtype=float,
           default=1.0)
       saturatedMaskName = pexConfig.Field(
           doc="Name of mask plane to use in saturation detection",
           dtype=str,
           default="SAT")
       flatScalingType = pexConfig.ChoiceField(
           doc="The method for scaling the flat on the fly.",
           dtypye=str,
           default='USER',
           allowed={
               "USER": "User defined scaling",
               "MEAN": "Scale by the inverse of the mean",
               "MEDIAN": "Scale by the inverse of the median",
           })
       keysToRemoveFromAssembledCcd = pexConfig.ListField(
           doc="fields to remove from the metadata of the assembled ccd.",
           dtype=str,
           default=[])

Fields are attributes on the config class.
The ``doWrite``, ``fwhm``, and ``saturatedMaskName`` fields are of `Field` type, which supports values with simple types like `int`, `float`, `str`, and `bool`.
The ``flatScalingType`` field is a `ChoiceField` type.
In this case, a user can only set ``flatScalingType`` to a value of ``"USER"``, ``"MEAN"``, OR ``"MEDIAN"``.

In code, a config object might be used like this:

.. code-block:: python

   def doIsrTask(ccd, configOverrideFilename=None):
       config = IsrTaskConfig()
       if configOverrideFilename is not None:
           config.load(configOverrideFilename)
           # Note: config override files are Python code with .py extensions
           # by convention
       config.validate()
       config.freeze()

       detectSaturation(ccd, config.fwhm, config.saturatedMaskName)
       # Note: methods typically do not need the entire config; they should be
       # passed only relevant parameters
       for k in config.keysToRemoveFromAssembledCcd:
           ccd.metadata.remove(k)
       if config.doWrite:
           ccd.write()

Notice how configuration field values are accessible as attributes on the ``config`` instance.

Also notice the `~Config.load` method.
This is a way of loading configuration values from a file.
A configuration override file for ``IsrTaskConfig`` might look like this:

.. code-block:: python

   config.doWrite = False
   config.fwhm = 0.8
   config.saturatedMaskName = 'SATUR'
   config.flatScalingType = 'MEAN'
   config.keysToRemoveFromAssembledCcd = ['AMPNAME']

This override file looks like Python code because *it is*.
The ``root`` variable refers to the config instance that called its `~Config.load` method, which is the ``config`` variable in the ``doIsrTask`` example.
In more advanced cases a configuration field's value can itself be a config instance, so there will be a hierarchical namespace of configurations, like:

.. code-block:: python

   config.configField.fieldOnConfigField = 'value'

Principles for using lsst.pex.config
====================================

:ref:`lsst.pex.config` arose from a desire to have a configuration object holding key-value pairs that also allows for (arbitrarily simple or complex) validation of configuration values.

To configure code using :ref:`lsst.pex.config`, you create a subclass of the `Config` class.
The subclass specifies the available `Field` attributes, their default values (if any), and their validation, if necessary.

`Config` configuration objects are hierarchical (see `ConfigField`), so calling code can embed the configuration definitions of called code.

Configurations are *not* input data.
They should not be used in place of function or method arguments, nor are they intended to replace ordinary dictionary data structures.
A good rule of thumb is that if a particular parameter does not have a useful default, it is probably an input rather than a
configuration parameter.
Another rule of thumb is that configuration parameters should generally not be set in algorithmic code, only in initialization or user interface code.
In fact, changing configuration after a configurable object (such as `~lsst.pipe.base.Task`) has been initialized can lead to incorrect behavior.

You create a configuration object by instantiating the `Config` subclass.
If any default `Field` values need to be overridden, you can assign new values to the configuration object's `Field` attributes.
For example: ``config.param1 = 3.14``).
Often you can override defaults of either a config base class or a nested config in the `Config.setDefaults` method, or by loading an external file with the `Config.load` method.
Overrides should never be used to set already-existing default values

You code then uses the configuration values by accessing the object's `Field` attributes.
For example, ``x = config.param1``.

A `Config` instance can also be frozen so that any attempt to change the values of field raises an exception.
This is useful to expose bugs that change configuration values after none should happen.

Finally, the contents of `Config` objects may easily be dumped, for provenance or debugging purposes.
See :doc:`inspecting-configs` for details.
