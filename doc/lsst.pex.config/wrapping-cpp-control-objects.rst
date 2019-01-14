.. py:currentmodule:: lsst.pex.config

############################
Wrapping C++ control objects
############################

C++ control objects defined using the ``LSST_CONTROL_FIELD`` macro in `lsst/pex/config.h` can be wrapped using pybind11 and the functions in `lsst.pex.config.wrap`, creating an equivalent Python `Config` object.
The `Config` will automatically create and set values in the C++ object, will provide access to the doc strings from C++, and will even call the C++ class's ``validate`` method, if one exists.
This helps to minimize duplication of code.

For example, here is a C++ control object:

.. code-block:: c++

    struct FooControl {
        LSST_CONTROL_FIELD(bar, int, "documentation for field 'bar'");
        LSST_CONTROL_FIELD(baz, double, "documentation for field 'baz'");
        
        FooControl() : bar(0), baz(0.0) {}
    };

Note that only ``bool``, ``int``, ``double``, and ``std::string`` fields, along with ``std::list`` and ``std::vector`` objects of those types, are fully supported.
Nested control objects are not supported.

After using pybind11, the preferred way to create the `Config` is via the `wrap` decorator:

.. code-block:: python

    import lsst.pex.config as pexConfig

    @pexConfig.wrap(FooControl)
    class FooConfig(pexConfig.Config):
        pass
