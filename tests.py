#!/usr/bin/env python
# coding: utf-8
"""
    tests
    ~~~~~

    Provides the tests for opts.

    :copyright: 2010 by Daniel Neuhäuser
    :license: BSD, see LICENSE for details
"""
import unittest
from decimal import Decimal
from StringIO import StringIO

from opts import (Node, Option, BooleanOption, IntOption, FloatOption,
                  DecimalOption, MultipleOptions, Command, Parser)

def xrange(*args):
    if len(args) == 1:
        start, stop, step = 0, args[0], 1
    elif len(args) == 2:
        start, stop, step = args[0], args[1], 1
    else:
        start, stop, step = args
    i = start
    while i <= stop:
        yield i
        i += step

class TestNode(unittest.TestCase):
    def test_short_description_fallback(self):
        n = Node()
        self.assertEqual(n.short_description, u"No short description.")

    def test_long_description_fallback(self):
        n = Node()
        self.assertEqual(n.long_description, u"No long description.")

    def test_long_description_fallback_to_short(self):
        n = Node(short_description=u"Foobar")
        self.assertEqual(n.long_description, u"Foobar")

class TestOption(unittest.TestCase):
    def test_valueerror_on_init(self):
        self.assertRaises(ValueError, Option)

class TestBooleanOption(unittest.TestCase):
    def test_evaluate(self):
        o = BooleanOption(short="b")
        p = Parser(options=dict(b=o))
        self.assertEqual(p.evaluate([u'-b']), ({'b': True}, []))
        o = BooleanOption(short="b", default=True)
        p = Parser(options=dict(b=o))
        self.assertEqual(p.evaluate(['-b']), ({'b': False}, []))

class TestNumberOptions(unittest.TestCase):
    def test_intoption_evaluate(self):
        self.make_test(xrange(-10, 10), IntOption(short='o'))

    def test_floatoption_evaluate(self):
        self.make_test(xrange(-10.0, 10.0, 0.5), FloatOption(short='o'))

    def test_decimaloption_evaluate(self):
        self.make_test(
            xrange(Decimal('-10.0'), Decimal('10.0'), Decimal('0.5')),
            DecimalOption(short='o')
        )

    def make_test(self, range, o):
        p = Parser(options=dict(o=o))
        for i in range:
            self.assertEqual(p.evaluate([u'-o', unicode(i)]), ({'o': i}, []))

class TestMultipleOptions(unittest.TestCase):
    def test_evaluate_no_quotes(self):
        o = MultipleOptions(short='o')
        p = Parser(options=dict(o=o))
        self.assertEqual(
            p.evaluate([u'-o', u'foo,bar,baz']),
            ({'o': [u'foo', u'bar', u'baz']}, [])
        )

    def test_evaluate_with_quotes(self):
        o = MultipleOptions(short='o')
        p = Parser(options=dict(o=o))
        self.assertEqual(
            p.evaluate([u'-o', u'foo,"bar,baz"']),
            ({'o': [u'foo', u'bar,baz']}, [])
        )
        self.assertEqual(
            p.evaluate([u'-o', u'"foo,bar",baz']),
            ({'o': [u'foo,bar', u'baz']}, [])
        )

class TestCommand(unittest.TestCase):
    def test_remaining_arguments(self):
        c = Command(options={'a': Option('a')})
        p = Parser(commands=dict(c=c))
        self.assertEqual(
            p.evaluate([u'c', u'foo']),
            ({'c': ({}, [u'foo'])}, [])
        )
        self.assertEqual(
            p.evaluate([u'c', u'-a', u'foo']),
            ({'c': ({'a': u'foo'}, [])}, [])
        )
        self.assertEqual(
            p.evaluate([u'c', u'-a', u'foo', u'bar']),
            ({u'c': ({'a': u'foo'}, [u'bar'])}, [])
        )

    def test_options(self):
        class TestDeclarative(Command):
            spam = Option('a', 'asomething')
            eggs = Option('b', 'bsomething')
        a = TestDeclarative()
        b = Command(options={
            'spam': Option('a', 'asomething'),
            'eggs': Option('b', 'bsomething')})
        for c in [a, b]:
            p = Parser(commands=dict(c=c))
            self.assertEqual(
                p.evaluate([u'c', u'-a', u'foo']),
                ({'c': ({'spam': u'foo'}, [])}, [])
            )
            self.assertEqual(
                p.evaluate([u'c', u'--asomething', u'foo']),
                ({'c': ({'spam': u'foo'}, [])}, [])
            )
            self.assertEqual(
                p.evaluate([u'c', u'-b', u'foo']),
                ({'c': ({u'eggs': u'foo'}, [])}, [])
            )
            self.assertEqual(
                p.evaluate([u'c', u'--bsomething', u'foo']),
                ({'c': ({u'eggs': u'foo'}, [])}, [])
            )

    def test_commands(self):
        class TestDeclarative(Command):
            spam = Command()
            eggs = Command()
        a = TestDeclarative()
        b = Command(commands={
            'spam': Command(),
            'eggs': Command()})
        cp = [u'script_name']
        for c in [a, b]:
            p = Parser(commands=dict(c=c))
            self.assertEqual(
                p.evaluate([u'c', u'spam']),
                ({'c': ({u'spam': ({}, [])}, [])}, [])
            )
            self.assertEqual(
                p.evaluate([u'c', u'eggs']),
                ({'c': ({'eggs': ({}, [])}, [])}, [])
            )

    def test_abbreviations(self):
        c = Command(
            options={
                'stack': Option(long='stack'),
                'stash': Option(long='stash')},
            commands={
                'stack': Command(),
                'stash': Command()})

        p = Parser(commands=dict(c=c))
        cp = [u'script_name']
        for s in [u's', u'st', u'sta']:
            cmd = [u'c', s]
            result = ({'c': ({}, [s])}, [])
            self.assertEqual(p.evaluate(cmd), result)
            self.assertEqual(p.evaluate(cmd), result)
            self.assertEqual(p.evaluate(cmd), result)

        self.assertEqual(
            p.evaluate([u'c', u'stac']),
            ({'c': ({u'stack': ({}, [])}, [])}, [])
        )
        self.assertEqual(
            p.evaluate([u'c', u'stas']),
            ({'c': ({u'stash': ({}, [])}, [])}, [])
        )
        self.assertEqual(
            p.evaluate([u'c', u'--stac', u'foo']),
            ({'c': ({u'stack': u'foo'}, [])}, [])
        )
        self.assertEqual(
            p.evaluate([u'c', u'--stas', u'foo']),
            ({'c': ({u'stash': u'foo'}, [])}, [])
        )

    def test_disallow_abbreviated_commands(self):
        class NewCommand(Command):
            allow_abbreviated_commands = False
        c = NewCommand(commands={
            'foo': Command()
        })
        p = Parser(commands=dict(c=c))
        self.assertEqual(p.evaluate([u'c', u'f']), ({'c': ({}, [u'f'])}, []))

class TestParser(unittest.TestCase):
    def test_default_evaluate_arguments(self):
        import sys
        old_argv = sys.argv
        enc = sys.stdin.encoding or sys.getdefaultencoding()
        sys.argv = [s.encode(enc) for s in [u'script_name', u'foo', u'bar']]
        p = Parser()
        self.assertEqual(p.evaluate(), ({}, [u'foo', u'bar']))
        sys.argv = old_argv

class TestParserOutput(unittest.TestCase):
    def setUp(self):
        self.out_file = StringIO()

    def tearDown(self):
        self.out_file.truncate(0)
        self.out_file.seek(0)

    def assertContains(self, container, item):
        if item not in container:
            raise AssertionError("{0!r} not in {1!r}".format(item, container))

    def test_alternative_commands(self):
        p = Parser(
            commands={
                'stack': Command(),
                'stash': Command(),
            },
            out_file=self.out_file,
            takes_arguments=False
        )
        for cmd in [u's', u'st', u'sta']:
            p.evaluate([cmd])
            output = self.out_file.getvalue()
            self.assertContains(
                output,
                u'command "{0}" does not exist'.format(cmd)
            )
            self.assertContains(output, u'stack')
            self.assertContains(output, u'stash')

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestNode))
    suite.addTest(unittest.makeSuite(TestOption))
    suite.addTest(unittest.makeSuite(TestBooleanOption))
    suite.addTest(unittest.makeSuite(TestNumberOptions))
    suite.addTest(unittest.makeSuite(TestMultipleOptions))
    suite.addTest(unittest.makeSuite(TestCommand))
    suite.addTest(unittest.makeSuite(TestParser))
    suite.addTest(unittest.makeSuite(TestParserOutput))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='suite')
