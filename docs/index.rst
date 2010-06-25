.. include:: ../README

Usage
-----
Here's a simple example::

    from opts import Parser, Option, BooleanOption

    parser = Parser(options={
        "filename": Option("f", "--file",
            short_description=u"write report to this file"),
        "verbose": BooleanOption("q", "quiet", default=True,
            short_description=u"don't print status messages")
    })

    options, arguments = parser.evaluate()

`options` will be a dictionary which looks like this::

    # ./script
    {"verbose": True}
    # ./script -q
    {"verbose": False}
    # ./script -f /home/foobar
    {"verbose": True, "file": u"/home/foobar"}
    # ./script -qf /home/foobar or ./script -q -f /home/foobar
    {"verbose": False, "file": u"/home/foobar"}

As you can see options will be decoded, the same goes for any remaining
arguments passed to your application which can be found in the returned
`arguments` list.

There are options for strings, booleans, numbers or even multiple strings
already available but you can easiely create your own option by subclassing.

In case you have a more complicated application you might need so called
commands. A command is similar to an option but it looks like a regular
argument. Every other argument followed by a command will be evaluated by this
command. Let's take a dvcs for example::

    from opts import Parser, Command, BooleanOption

    parser = Parser(description=u"Our own awesome dvcs", commands={
        "add": Command(
            short_description=u"Adds a file to the repository",
            options={
                "dry-run": BooleanOption("n", "dry-run"),
                "interactive": BooleanOption("i", "interactive"),
            },
        ),
        "stack": Command(),
        "stash": Command(),
    })

    print parser.evaluate(["add"])
    # ({"add": ({"dry-run": False, "interactive": False}, [])}, [])

As for the previous example opts automatically provides a help command which
allows you to list every command and option associated with a command or look
at the long, detailed description of a command or option.

Also the user is able to abbreviate commands::

    $ ./git help
    usage: ./git [commands]
    
    Our own awesome dvcs

    Commands:
     add        Adds a file to the repository
     stack      No short description.
     stash      No short description.
     help       Shows this message.

    $ ./git help a # equivalent to ./git help add
    usage: ./git add [options]

    Adds a file to the repository.

    Commands:
     help       Shows this message.

    Options:
     -n --dry-run     No short description.
     -i --interactive No short description.

    $ ./git help s
    usage: ./git help

    The given command "s" does not exist, did you mean?
     - stack
     - stash

Now you know the basic concepts and should be able to make an awesome command
line interface for your application. If you need a more detailed explanation
about a certain feature take a look at the :ref:`api-reference`.

.. _api-reference:

API Reference
-------------

.. module:: opts

.. autoclass:: Option
   :members:

.. autoclass:: BooleanOption
   :members:

.. autoclass:: IntOption
   :members:

.. autoclass:: FloatOption
   :members:

.. autoclass:: DecimalOption
   :members:

.. autoclass:: MultipleOptions
   :members:

.. autoclass:: Command
   :members:

.. autoclass:: Parser
   :members:

License Text
------------

.. include:: ../LICENSE
