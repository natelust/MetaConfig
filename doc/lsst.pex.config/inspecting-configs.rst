.. py:currentmodule:: lsst.pex.config

#########################
Inspecting configurations
#########################

Field access
------------

Iterating through a `Config` instance yields the names of the `Field` attributes it contains.
The `Config` class also supports many dictionary-like methods: `~Config.keys`, `~Config.items`, `~Config.iterkeys`, `~Config.iteritems`, and `~Config.itervalues`.

History
-------

The `Config.history` attribute contains the history of all changes to the `Config` instance's fields.
Each `Field` instance also has a history.
The `Config.formatHistory` method displays the history of a given `Field` in a more readable format.

Docstrings
----------

Each `Field` instance is required to have a doc string that describes the contents of the field.
Doc strings can be verbose and should give users of the `Config` object a good understanding of what the field is and how it will be interpreted and used.
A doc string should also be provided for the class as a whole.

You can use the built-in `help` function or :command:`pydoc` command to inspect a `Config` instance's doc strings as well as those of its `Field` attributes.
