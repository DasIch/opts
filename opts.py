# coding: utf-8
"""
    opts
    ~~~~

    A simple option parser.

    :copyright: 2010 by Daniel Neuhäuser
    :license: BSD, see LICENSE for details.
"""
import sys
from decimal import Decimal
from inspect import getmembers
from itertools import count, izip_longest

__all__ = ["Option", "BooleanOption", "IntOption", "FloatOption",
           "DecimalOption", "MultipleOptions", "Command", "Parser"]

missing = object()
_next_position_hint = count().next

class Missing(object):
    def __nonzero__(self):
        return False

    def __repr__(self):
        return "missing"

#: Represents the absence of a value.
missing = Missing()
del Missing

class cached_property(object):
    """
    A cached property object caches the value returned by the ``getter``.

    :param name:
        The name which should be used for the property, if you don't pass one
        the name of the ``getter`` is used.

    :param doc:
        The docstring which should be used for the property, if no one is
        passed the ``getter``'s docstring is used.
    """
    def __init__(self, getter, name=None, doc=None):
        self.getter = getter
        self.__name__ = name or getter.__name__
        self.__module__ = getter.__module__
        self.__doc__ = doc or getter.__doc__

    def __get__(self, obj, type=None):
        missing = object()
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, missing)
        if value is missing:
            value = self.getter(obj)
            obj.__dict__[self.__name__] = value
        return value

    def __repr__(self):
        return "{0}({1!r}, name={2!r}, doc={3!r})".format(self.getter,
                                                          self.name, self.doc)

def decode_arguments(arguments,
                     encoding=sys.stdin.encoding or sys.getdefaultencoding()):
    """
    If any of the items in the given ``arguments`` list is a byte string it
    will be decoded using the given ``encoding``.
    """
    decoded = []
    for argument in arguments:
        if not isinstance(argument, unicode):
            argument = argument.decode(encoding)
        decoded.append(argument)
    return decoded

def abbreviations(strings):
    """
    Returns a dictionary with abbreviations of the given `strings` as keys for
    those.
    """
    def shorter(s):
        for i in xrange(1, len(s)):
            yield s, s[:-i]

    strings = list(strings)
    string_to_abbs = dict((s, []) for s in strings)
    for abbs in izip_longest(*map(shorter, strings)):
        abbs = dict(a or (strings[i], None) for i, a in enumerate(abbs))
        values = abbs.values()
        for key, value in abbs.iteritems():
            if value is not None and values.count(value) == 1:
                string_to_abbs[key].append(value)

    result = {}
    for string, abbs in string_to_abbs.iteritems():
        for abb in abbs:
            result[abb] = string
    return result

class Node(object):
    """
    Represents an argument passed to your script.

    :param description:
        The description of this argument.
    """
    def __init__(self, description=None):
        self.description = description
        self._position_hint = _next_position_hint()

    def evaluate(self, argument):
        """
        Evaluates the given argument
        """
        raise NotImplementedError(
                "{0}.evaluate(argument)".format(self.__class__.__name__))

    def __repr__(self):
        return "{0}(description={1!r})".format(self.__class__.__name__,
                                               self.description)

class Option(Node):
    """
    Represents a string option.

    :param short:
        A short variant of the option without the prefixed ``-``.

    :param long:
        A long variant of the option without the prefixed ``--``.

    :param default:
        The default value for this option.

    :param description:
        A description of the option.
    """
    #: Set to ``True`` if this option requires an argument for evaluation.
    requires_argument = True

    def __init__(self, short=None, long=None, default=missing,
                 description=None):
        Node.__init__(self, description=description)
        self.short = unicode(short)
        self.long = unicode(long)
        self.default = default

    def evaluate(self, argument=missing):
        """
        Evaluates the argument for this option.
        """
        return argument

    def __repr__(self):
        return "{0}(short={1!r}, long={2!r}, default={3!r}, description={4!r})" \
                .format(self.__class__.__name__, self.short, self.long,
                        self.default, self.description)

class BooleanOption(Option):
    """
    Represents a boolean option, it evaluates always to the opposite of the
    default value.
    """
    requires_argument = False

    def __init__(self, short=None, long=None, default=False, description=None):
        Option.__init__(self, short=short, long=long, default=default,
                        description=description)

    def evaluate(self):
        return not self.default

class IntOption(Option):
    """
    Represents an integer option.
    """
    def evaluate(self, argument):
        return int(argument)

class FloatOption(Option):
    """
    Represents a float option.
    """
    def evaluate(self, argument):
        return float(argument)

class DecimalOption(Option):
    """
    Represents a decimal option.
    """
    def evaluate(self, argument):
        return Decimal(argument)

class MultipleOptions(Option):
    """
    Represents multiple values which are evaluated using the given
    ``sub_option``.

    The values are seperated by commas, strings containing commas can be
    represented using single and double quotes::

        "foo,bar,baz"   -> ["foo", "bar", "baz"]
        "foo,'bar,bar'" -> ["foo", "bar,baz"]
        'foo,"bar,baz"' -> ["foo", "bar,baz"]
    """
    def __init__(self, sub_option=Option, short=None, long=None,
                 default=missing, description=None):
        Option.__init__(self, short=short, long=long, default=default,
                        description=description)
        self.sub_option = sub_option()

    def evaluate(self, argument):
        result = []
        buffer = []
        open_quote = False
        for char in argument:
            if char in [u"'", u'"']:
                if open_quote:
                    result.append(u''.join(buffer))
                    buffer = []
                open_quote = not open_quote
            elif char == u',' and not open_quote:
                result.append(u''.join(buffer))
                buffer = []
            else:
                buffer.append(char)
        if buffer:
            result.append(u''.join(buffer))
        return map(self.sub_option.evaluate, result)

def get_option_attributes(obj):
    return getmembers(obj, lambda x: isinstance(x, Option))

def get_command_attributes(obj):
    return getmembers(obj, lambda x: isinstance(x, Command))

class Command(Node):
    """
    Represents a command which unlike an option is not prefixed. A command can
    have several options and/or commands.

    Options or commands can be defined by passing them to the constructor in
    a dictionary or by defining them declerativley on a subclass.

    :param callback:
        A function which get's called with the result of the evaluation instead
        of returning it.
    """
    #: If ``True`` allows commands to be abbreviated e.g. you can pass ``he``
    #: instead of ``help`` as long as there is no conflict with other commands.
    allow_abbreviated_commands = True

    #: The same as :attr:`allow_abbreviated_commands` for long options.
    allow_abbreviated_options = True

    def __init__(self, options=None, commands=None, description=None,
                 callback=None, allow_abbreviated_commands=True,
                 allow_abbreviated_options=True):
        Node.__init__(self, description=description)
        self.options = dict(get_option_attributes(self.__class__),
                            **(options or {}))
        self.commands = dict(get_command_attributes(self.__class__),
                             **(commands or {}))
        if callback is None or not hasattr(self, "callback"):
            self.callback = callback
        if allow_abbreviated_commands != self.allow_abbreviated_commands:
            self.allow_abbreviated_commands = allow_abbreviated_commands
        if allow_abbreviated_options != self.allow_abbreviated_options:
            self.allow_abbreviated_options = allow_abbreviated_options

        if self.allow_abbreviated_commands:
            commands = dict((k, (k, v)) for k, v in self.commands.iteritems())
            for key, value in abbreviations(self.commands).iteritems():
                commands[key] = (value, self.commands[value])
            self.commands = commands

    @cached_property
    def short_options(self):
        """
        A dictionary mapping the short variants of the options to a tuple of
        the name of the option and the option itself.
        """
        result = {}
        for name, option in self.options.iteritems():
            result[option.short] = (name, option)
        return result

    @cached_property
    def long_options(self):
        """
        A dictionary mapping the long variants of the options to a tuple of
        the name of the option and the option itself.
        """
        long_options = {}
        for name, option in self.options.iteritems():
            long_options[option.long] = (name, option)

        result = long_options.copy()
        for abbr, long_option in abbreviations(long_options).iteritems():
            result[abbr] = long_options[long_option]
        return result

    def evaluate(self, arguments=None):
        """
        Evaluates the given list of ``arguments`` and returns a dictionary with
        the options and a list with remaining arguments.
        """
        if arguments is None:
            arguments = []
        else:
            arguments = decode_arguments(arguments)
        options = {}
        for name, option in self.options.iteritems():
            if option.default is not missing:
                options[name] = option.default
        result = options, []
        argument_iter = enumerate(arguments)
        for i, argument in argument_iter:
            if argument.startswith(u'--'):
                options.update(self.evaluate_long_option(argument[2:],
                                                         argument_iter))
            elif argument.startswith(u'-'):
                options.update(self.evaluate_short_options(list(argument[1:]),
                                                           argument_iter))
            else:
                try:
                    name, command = self.commands[arguments[i]]
                except KeyError:
                    return options, arguments[i:]
                result = command.evaluate(arguments[1 + i:])
                if self.callback is not None:
                    self.callback(*result)
                return {name: result}
        return result

    def evaluate_short_options(self, shorts, arguments):
        result = {}
        for short in shorts:
            name, option = self.short_options[short]
            if option.requires_argument:
                result[name] = option.evaluate(arguments.next()[1])
            else:
                result[name] = option.evaluate()
        return result

    def evaluate_long_option(self, long, arguments):
        name, option = self.long_options[long]
        used_arguments = []
        if option.requires_argument:
            value = option.evaluate(arguments.next()[1])
        else:
            value = option.evaluate()
        return {name: value}

    def __repr__(self):
        return "{0}(options={1!r}, commands={2!r}, description={2!r}, callback={3!r})" \
                .format(self.__class__.__name__, self.options, self.commands,
                        self.description, self.callback)

class Parser(Command):
    def evaluate(self, arguments=None):
        """
        Evaluates the given list of ``arguments`` and returns a dictionary with
        the options and a list with the remaining arguments.
        """
        return Command.evaluate(self, arguments or sys.argv[1:])
