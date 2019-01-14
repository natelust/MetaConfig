.. py:currentmodule:: lsst.pex.config

#########################
Design of lsst.pex.config
#########################

This page is a collection of notes describing the design of :ref:`lsst.pex.config` and the `pex_config`_ package in general.

Design goals
============

- Enable configuration of plug-in algorithms provided at runtime.

- Allow setting of one `Field` to affect the values and the validation of others.

- Collocate the `Config` definition with the code using the `Config`.

- Provide a "Pythonic" interface.

- Record the file and line of `Field` instance definitions and all changes to `Field` instances, including setting default values.

- Set defaults before overriding with user-specified values.

- Support parameters with no (nonexistent) values, including overriding existing default values.

- Enable closely-related `Config` objects to be represented efficiently, with a minimum of duplication.

- Have all user-modifiable `Config` instances be part of a hierarchical tree.

- Validate the contents of `Field` instances as soon as possible.

- Be able to "freeze" a `Config` instance to make it read-only.

- Be able to persist a `Config` instance to a file and restore it identically.

- Allow C++ control objects to be created from `Config` objects, with documentation and validation specified exactly once.

- Support lists of parameter values.

Relationship to pex\_policy
===========================

The `lsst.pex.Policy` and `lsst.pex.PolicyDictionary` classes in the `pex_policy`_ package provided many of the features of `pex_config`_ in C++ and, via SWIG wrapping, Python.
`pex_config`_ (which contains the :ref:`lsst.pex.config` module) was developed to provide additional features and remove
some shortcomings.

`pex_policy`_ is being replaced with `pex_config`_ in the LSST Data Management System codebase.
To aid the transition, the `makePolicy` a utility function converts a `Config` to a `~lsst.pex.policy.Policy`.

Architecture
============

`Config` uses a metaclass to record the `Field` attributes within each `Config` object in an internal dictionary.
The storage and history for the fields is also maintained in the `Config` object, not the `Field` instance itself.
This allows `Field` classes to be easily inherited.

.. _pex_config: https://github.com/lsst/pex_config
.. _pex_policy: https://github.com/lsst/pex_policy
