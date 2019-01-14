.. py:currentmodule:: lsst.pex.config

.. _lsst.pex.config:

###############
lsst.pex.config
###############

The ``lsst.pex.config`` module provides a configuration system for the LSST Science Pipelines.
The `lsst.pex.config.Config` class is an integral part of the task framework (see :ref:`lsst.pipe.base`), though ``lsst.pex.config`` is also useful on its own.
Configuration parameters can be validated, documented, and even record the history of their values for provenance.

Using lsst.pex.config
=====================

.. toctree::
   :maxdepth: 2

   overview
   field-types
   inspecting-configs
   registry-intro
   wrapping-cpp-control-objects

.. _lsst.pex.config-contributing:

Contributing
============

``lsst.pex.config`` is developed at https://github.com/lsst/pex_config.
You can find Jira issues for this module under the `pex_config <https://jira.lsstcorp.org/issues/?jql=project%20%3D%20DM%20AND%20component%20%3D%20pex_config>`_ component.

.. toctree::
   :maxdepth: 2

   design-notes

.. _lsst.pex.config-pyapi:

Python API reference
====================

.. automodapi:: lsst.pex.config
   :no-main-docstr:
   :no-inheritance-diagram:

.. automodapi:: lsst.pex.config.callStack
   :no-main-docstr:
   :no-inheritance-diagram:

.. automodapi:: lsst.pex.config.history
   :no-main-docstr:
   :no-inheritance-diagram:
