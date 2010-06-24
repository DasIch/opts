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

from opts import *

class TestCommand(unittest.TestCase):
    def test_remaining_arguments(self):
        c = Command(options={'a': Option('a')})
        self.assertEqual(c.evaluate([u'foo']), ({}, [u'foo']))
        self.assertEqual(c.evaluate([u'-a', u'foo']), ({'a': u'foo'}, []))
        self.assertEqual(c.evaluate([u'-a', u'foo', u'bar']),
                         ({'a': u'foo'}, [u'bar']))

    def test_options(self):
        class TestDeclarative(Command):
            spam = Option('a', 'asomething')
            eggs = Option('b', 'bsomething')
        a = TestDeclarative()
        b = Command(options={
            'spam': Option('a', 'asomething'),
            'eggs': Option('b', 'bsomething')})
        for c in [a, b]:
            self.assertEqual(c.evaluate([u'-a', u'foo']),
                             ({u'spam': u'foo'}, []))
            self.assertEqual(c.evaluate([u'--asomething', u'foo']),
                             ({u'spam': u'foo'}, []))
            self.assertEqual(c.evaluate([u'-b', u'foo']),
                             ({u'eggs': u'foo'}, []))
            self.assertEqual(c.evaluate([u'--bsomething', u'foo']),
                             ({u'eggs': u'foo'}, []))

    def test_commands(self):
        class TestDeclarative(Command):
            spam = Command()
            eggs = Command()
        a = TestDeclarative()
        b = Command(commands={
            'spam': Command(),
            'eggs': Command()})
        for c in [a, b]:
            self.assertEqual(c.evaluate([u'spam']), {u'spam': ({}, [])})
            self.assertEqual(c.evaluate([u'eggs']), {u'eggs': ({}, [])})

    def test_abbreviations(self):
        c = Command(
            options={
                'stack': Option(long='stack'),
                'stash': Option(long='stash')},
            commands={
                'stack': Command(),
                'stash': Command()})

        for s in [u's', u'st', u'sta']:
            result = ({}, [s])
            self.assertEqual(c.evaluate([s]), result)
            self.assertEqual(c.evaluate([s]), result)
            self.assertEqual(c.evaluate([s]), result)

        self.assertEqual(c.evaluate([u'stac']), {u'stack': ({}, [])})
        self.assertEqual(c.evaluate([u'stas']), {u'stash': ({}, [])})

        self.assertEqual(c.evaluate([u'--stac', u'foo']),
                         ({u'stack': u'foo'}, []))
        self.assertEqual(c.evaluate([u'--stas', u'foo']),
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
    suite.addTest(unittest.makeSuite(TestCommand))
    suite.addTest(unittest.makeSuite(TestParser))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='suite')
