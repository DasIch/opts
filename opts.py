# coding: utf-8
"""
    opts
    ~~~~

    A simple option parser.

    :copyright: 2010 by Daniel Neuhäuser
    :license: BSD, see LICENSE for details.
"""
import sys
import codecs
from decimal import Decimal
from inspect import getmembers
from itertools import count, izip_longest
from operator import attrgetter, itemgetter

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

def shorter(string):
    for i in xrange(1, len(string)):
        yield string, string[:-1]

def abbreviations(strings):
    """
    Returns a dictionary with abbreviations of the given `strings` as keys for
    those.
    """
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

def matches(beginning, strings):
    """
    Returns every string from the given `strings` starting with the given
    `beginning`.
    """
    for string in strings:
        if string.startswith(beginning):
            yield string

def get_usage(command, callpath):
    result = [u"usage: {0}".format(u" ".join(map(itemgetter(0), callpath)))]
    if command.options:
        result.append(u"[options]")
    if len(command.commands) > 1 or \
            command.commands and u"help" not in command.commands:
        result.append(u"[commands]")
    return u" ".join(result)

class Node(object):
    """
    Represents an argument passed to your script.

    :param short_description:
        A short description no longer than one line.

    :param long_description:
        A longer detailed description.
    """
    def __init__(self, short_description=None, long_description=None):
        self.short_description = short_description
        self.long_description = long_description
        self._position_hint = _next_position_hint()

    @property
    def short_description(self):
        return self._short_description or u"No short description."

    @short_description.setter
    def short_description(self, short_description):
        self._short_description = short_description

    @property
    def long_description(self):
        desc = self._long_description or self._short_description
        return desc or u"No long description."

    @long_description.setter
    def long_description(self, long_description):
        self._long_description = long_description

    def evaluate(self, callpath, argument):
        """
        Evaluates the given argument
        """
        raise NotImplementedError("{0}.evaluate(callpath, argument)" \
                .format(self.__class__.__name__))

    def __repr__(self):
        return "{0}(short_description={1!r}, long_description={2!r})" \
                .format(self.__class__.__name__, self.short_description,
                        self.long_description)

class Option(Node):
    """
    Represents a string option.

    :param short:
        A short variant of the option without the prefixed ``-``.

    :param long:
        A long variant of the option without the prefixed ``--``.

    :param default:
        The default value for this option.

    :param short_description:
        A short one-line description which can be displayed along with
        several other short descriptions by the help command.

    :param long_description:
        A long detailed description.
    """
    #: Set to ``True`` if this option requires an argument for evaluation.
    requires_argument = True

    #: Set this to ``True`` if the option allows an argument but does not
    #: require it.
    allows_optional_argument = False

    def __init__(self, short=None, long=None, default=missing,
                 short_description=None, long_description=None):
        Node.__init__(self, short_description=short_description,
                      long_description=long_description)
        if short is long is None:
            raise ValueError("you need to specify a short and/or long")
        self.short = unicode(short)
        self.long = unicode(long)
        self.default = default

    def evaluate(self, callpath, argument=missing):
        """
        Evaluates the argument for this option.
        """
        return argument

    def __repr__(self):
        return ("{0}(short={1!r}, long={2!r}, default={3!r}, "
                "short_description={4!r}, "
                "long_description={5!r})").format(self.__class__.__name__,
                                                  self.short, self.long,
                                                  self.default,
                                                  self.short_description,
                                                  self.long_description)

class BooleanOption(Option):
    """
    Represents a boolean option, it evaluates always to the opposite of the
    default value.
    """
    requires_argument = False

    def __init__(self, short=None, long=None, default=False,
                 short_description=None, long_description=None):
        Option.__init__(self, short=short, long=long, default=default,
                        short_description=short_description,
                        long_description=long_description)

    def evaluate(self, callpath):
        return not self.default

class IntOption(Option):
    """
    Represents an integer option.
    """
    def evaluate(self, callpath, argument):
        return int(argument)

class FloatOption(Option):
    """
    Represents a float option.
    """
    def evaluate(self, callpath, argument):
        return float(argument)

class DecimalOption(Option):
    """
    Represents a decimal option.
    """
    def evaluate(self, callpath, argument):
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

    def evaluate(self, callpath, argument):
        result = []
        buffer = []
        open_quote = False
        for char in argument:
            if char in [u"'", u'"']:
                if open_quote:
                    result.append(u"".join(buffer))
                    buffer = []
                open_quote = not open_quote
            elif char == u"," and not open_quote:
                result.append(u"".join(buffer))
                buffer = []
            else:
                buffer.append(char)
        if buffer:
            result.append(u"".join(buffer))
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

    #: If the command does not require any arguments additional to the options
    #: and commands, set this to ``False``.
    takes_arguments = True

    use_auto_help = True

    def __init__(self, options=None, commands=None, short_description=None,
                 long_description=None, callback=None,
                 allow_abbreviated_commands=None,
                 allow_abbreviated_options=None,
                 takes_arguments=None):
        Node.__init__(self, short_description=short_description,
                      long_description=long_description)
        self.options = dict(get_option_attributes(self.__class__),
                            **(options or {}))
        self.commands = dict(get_command_attributes(self.__class__),
                             **(commands or {}))
        if self.use_auto_help:
            self.commands.setdefault(u"help", HelpCommand())
        if callback is None or not hasattr(self, "callback"):
            self.callback = callback
        if allow_abbreviated_commands is not None:
            self.allow_abbreviated_commands = allow_abbreviated_commands
        if allow_abbreviated_options is not None:
            self.allow_abbreviated_options = allow_abbreviated_options
        if takes_arguments is not None:
            self.takes_arguments = takes_arguments

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

        if not self.allow_abbreviated_options:
            return long_options
        result = long_options.copy()
        for abbr, long_option in abbreviations(long_options).iteritems():
            result[abbr] = long_options[long_option]
        return result

    @cached_property
    def all_commands(self):
        commands = dict((k, (k, v)) for k, v in self.commands.iteritems())
        if not self.allow_abbreviated_commands:
            return commands.copy()
        for abbr, command in abbreviations(commands).iteritems():
            commands[abbr] = commands[command]
        return commands

    def print_missing_node(self, node, callpath, command):
        write = lambda x: callpath[0][1].out_file.write(x + u"\n")
        write(get_usage(callpath[-1][1], callpath))
        write(u"")
        if node.startswith(u"-"):
            type = u"option"
            possible_items = [option.long for option in command.options.values()]
        else:
            type = u"command"
            possible_items = command.commands.keys()
        for shorter_version in shorter(node):
            items = list(matches(shorter_version, possible_items))
            if items:
                break
        else:
            items = list(matches(node, possible_items))
        if not items:
            write(u"The given {0} \"{1}\" does not exist.".format(type, node))
            return
        write(u"The given {0} \"{1}\" does not exist, did you mean?" \
                .format(type, node))
        for item in items:
            write(u" - {0}".format(item))
        write(u"")

    def evaluate(self, callpath, arguments):
        """
        Evaluates the given list of ``arguments`` and returns a dictionary with
        the options and a list with remaining arguments.
        """
        options = {}
        for name, option in self.options.iteritems():
            if option.default is not missing:
                options[name] = option.default
        result = options, []
        argument_iter = enumerate(arguments)
        for i, argument in argument_iter:
            if argument.startswith(u"--"):
                callpath.append((argument, None))
                options.update(self.evaluate_long_option(callpath,
                                                         argument[2:],
                                                         argument_iter))
            elif argument.startswith(u"-"):
                callpath.append((argument, None))
                options.update(self.evaluate_short_options(callpath,
                                                           list(argument[1:]),
                                                           argument_iter))
            else:
                try:
                    name, command = self.all_commands[arguments[i]]
                except KeyError:
                    if not self.takes_arguments:
                        self.print_missing_node(arguments[i], callpath)
                        return
                    return options, arguments[i:]
                callpath.append((arguments[i], command))
                result = command.evaluate(callpath, arguments[1 + i:])
                if self.callback is not None:
                    self.callback(*result)
                return {name: result}, []
        return result

    def evaluate_short_options(self, callpath, shorts, arguments):
        result = {}
        for short in shorts:
            try:
                name, option = self.short_options[short]
            except KeyError:
                self.print_missing_node(u"-" + short, callpath, self)
                return
            callpath[-1] = (callpath[-1][0], option)
            if option.requires_argument:
                result[name] = option.evaluate(callpath, arguments.next()[1])
            elif option.allows_optional_argument:
                try:
                    argument = arguments.next()[1]
                except StopIteration:
                    result[name] = option.evaluate(callpath)
                else:
                    result[name] = option.evaluate(callpath, argument)
            else:
                result[name] = option.evaluate(callpath)
        return result

    def evaluate_long_option(self, callpath, long, arguments):
        try:
            name, option = self.long_options[long]
        except KeyError:
            self.print_missing_node(callpath[-1][0], callpath, self)
            return
        callpath[-1] = (callpath[-1][0], option)
        used_arguments = []
        if option.requires_argument:
            value = option.evaluate(callpath, arguments.next()[1])
        elif option.allows_optional_argument:
            try:
                argument = arguments.next()[1]
            except StopIteration:
                value = option.evaluate(callpath)
            else:
                value = option.evaluate(callpath, argument)
        else:
            value = option.evaluate(callpath)
        return {name: value}

    def __repr__(self):
        return ("{0}(options={1!r}, commands={2!r}, short_description={2!r}, "
                "long_description={3!r}, callback={4!r})"). \
                        format(self.__class__.__name__, self.options,
                               self.commands, self.short_description,
                               self.long_description, self.callback)

class HelpCommand(Command):
    use_auto_help = False

    def __init__(self, options=None, commands=None,
                 short_description=u"Shows this message.",
                 long_description=u"Displays every command and option.",
                 callback=None,
                 allow_abbreviated_commands=None,
                 allow_abbreviated_options=None):
        Command.__init__(self, options=options, commands=commands,
                         short_description=short_description,
                         long_description=long_description, callback=callback,
                         allow_abbreviated_commands=allow_abbreviated_commands,
                         allow_abbreviated_options=allow_abbreviated_options)

    def evaluate(self, callpath, arguments):
        command = callpath[-2][1]
        try:
            argument = arguments[0]
        except IndexError:
            argument, node = callpath[-2]
            callpath = callpath[:-1]
        else:
            if argument.startswith(u'--'):
                try:
                    node = command.long_options[argument[2:]][1]
                except KeyError:
                    self.print_missing_node(argument, callpath, command)
                    return
                else:
                    argument = argument[2:]
            if argument.startswith(u'-'):
                try:
                    node = command.short_options[argument[1:]][1]
                except KeyError:
                    self.print_missing_node(argument, callpath, command)
                    return
                else:
                    argument = argument[1:]
            else:
                try:
                    node = command.all_commands[argument][1]
                except KeyError:
                    self.print_missing_node(argument, callpath, command)
                    return
            callpath = callpath[:-1] + [(argument, None)]

        write = lambda x: callpath[0][1].out_file.write(x + u"\n")
        write(get_usage(node, callpath))
        write(u"")
        write(node.long_description)
        write(u"")
        if not isinstance(node, Command):
            return
        commands = sorted(node.commands.items(),
                          key=lambda x: x[1]._position_hint)
        options = sorted(node.options.values(),
                         key=attrgetter("_position_hint"))
        nodes = []
        get_length = lambda nodes: max(10, max(len(n[0]) for n in nodes))
        if commands:
            nodes.append((u"Commands:", get_length(commands), commands))
        if options:
            commands = [
                (u"-{0} --{1}".format(o.short, o.long), o) for o in options]
            nodes.append((u"Commands:", get_length(commands), commands))
        for label, max_node_length, nodes in nodes:
            write(label)
            for node_name, node in nodes:
                write(u" {0} {1}".format(node_name.ljust(max_node_length),
                                         node.short_description))
            write("")

class Parser(Command):
    def __init__(self, options=None, commands=None, script_name=sys.argv[0],
                 description=None, out_file=sys.stdout, takes_arguments=None):
        Command.__init__(self, options=options, commands=commands,
                         long_description=description,
                         takes_arguments=takes_arguments)
        self.script_name = script_name
        self.out_file = out_file

    @property
    def out_file(self):
        """
        A file-like object to which any output is being written.
        """
        return self._out_file

    @out_file.setter
    def out_file(self, fobj):
        if isinstance(fobj, codecs.StreamReaderWriter):
            self._out_file = fobj
        encoding = getattr(fobj, "encoding", None)
        if encoding is None:
            encoding = "ascii"
            errors = "replace"
        else:
            errors = "strict"
        codec_info = codecs.lookup(encoding)
        self._out_file = codecs.StreamReaderWriter(fobj,
                                                   codec_info.streamreader,
                                                   codec_info.streamwriter,
                                                   errors)

    def evaluate(self, arguments=None):
        """
        Evaluates the given list of ``arguments`` and returns a dictionary with
        the options and a list with the remaining arguments.
        """
        if arguments is None:
            arguments = sys.argv[1:]
        arguments = decode_arguments(arguments)
        return Command.evaluate(self, [(self.script_name, self)], arguments)

    def __repr__(self):
        return "{0}(script_name={1!r}, description={2!r})" \
                .format(self.__class__.__name__, self.script_name,
                        self.long_description)
