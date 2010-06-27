#!/usr/bin/env python
# coding: utf-8
from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup

setup(
    name=u"opts",
    version=u"0.1.1",
    url=u"http://github.com/DasIch/opts",
    license=u"BSD",
    author=u"Daniel Neuhäuser",
    author_email=u"dasdasich@gmail.com",
    description=u"commandline option parser",
    long_description=open("README").read(),
    keywords="commandline option parser",
    platforms="any",
    zip_safe=False,
    test_suite="tests.suite",
    py_modules=["opts"],
)
