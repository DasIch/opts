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

from opts import (Node, Option, BooleanOption, IntOption, FloatOption,
                  DecimalOption, Command, Parser)

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
        self.assertEqual(o.evaluate([("-b", o)]), True)
        o = BooleanOption(short="b", default=True)
        self.assertEqual(o.evaluate([("-b", o)]), False)

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
        for i in range:
            self.assertEqual(o.evaluate([(u'-o', o)], unicode(i)), i)

class TestCommand(unittest.TestCase):
    def test_remaining_arguments(self):
        c = Command(options={'a': Option('a')})
        cp = [u'script_name']
        self.assertEqual(c.evaluate(cp, [u'foo']), ({}, [u'foo']))
        self.assertEqual(c.evaluate(cp, [u'-a', u'foo']), ({'a': u'foo'}, []))
        self.assertEqual(c.evaluate(cp, [u'-a', u'foo', u'bar']),
                         ({'a': u'foo'}, [u'bar']))

    def test_options(self):
        class TestDeclarative(Command):
            spam = Option('a', 'asomething')
            eggs = Option('b', 'bsomething')
        a = TestDeclarative()
        b = Command(options={
            'spam': Option('a', 'asomething'),
            'eggs': Option('b', 'bsomething')})
        cp = [u'script_name']
        for c in [a, b]:
            self.assertEqual(c.evaluate(cp, [u'-a', u'foo']),
                             ({u'spam': u'foo'}, []))
            self.assertEqual(c.evaluate(cp, [u'--asomething', u'foo']),
                             ({u'spam': u'foo'}, []))
            self.assertEqual(c.evaluate(cp, [u'-b', u'foo']),
                             ({u'eggs': u'foo'}, []))
            self.assertEqual(c.evaluate(cp, [u'--bsomething', u'foo']),
                             ({u'eggs': u'foo'}, []))

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
            self.assertEqual(c.evaluate(cp, [u'spam']), ({u'spam': ({}, [])}, []))
            self.assertEqual(c.evaluate(cp, [u'eggs']), ({u'eggs': ({}, [])}, []))

    def test_abbreviations(self):
        c = Command(
            options={
                'stack': Option(long='stack'),
                'stash': Option(long='stash')},
            commands={
                'stack': Command(),
                'stash': Command()})

        cp = [u'script_name']
        for s in [u's', u'st', u'sta']:
            result = ({}, [s])
            self.assertEqual(c.evaluate(cp, [s]), result)
            self.assertEqual(c.evaluate(cp, [s]), result)
            self.assertEqual(c.evaluate(cp, [s]), result)

        self.assertEqual(c.evaluate(cp, [u'stac']), ({u'stack': ({}, [])}, []))
        self.assertEqual(c.evaluate(cp, [u'stas']), ({u'stash': ({}, [])}, []))

        self.assertEqual(c.evaluate(cp, [u'--stac', u'foo']),
                         ({u'stack': u'foo'}, []))
        self.assertEqual(c.evaluate(cp, [u'--stas', u'foo']),
                         ({u'stash': u'foo'}, []))

class TestParser(unittest.TestCase):
    def test_default_evaluate_arguments(self):
        import sys
        old_argv = sys.argv
        enc = sys.stdin.encoding or sys.getdefaultencoding()
        sys.argv = [s.encode(enc) for s in [u'script_name', u'foo', u'bar']]
        p = Parser()
        self.assertEqual(p.evaluate(), ({}, [u'foo', u'bar']))
        sys.argv = old_argv

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestNode))
    suite.addTest(unittest.makeSuite(TestOption))
    suite.addTest(unittest.makeSuite(TestBooleanOption))
    suite.addTest(unittest.makeSuite(TestNumberOptions))
    suite.addTest(unittest.makeSuite(TestCommand))
    suite.addTest(unittest.makeSuite(TestParser))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='suite')
