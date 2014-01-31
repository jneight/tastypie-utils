# coding=utf-8


from setuptools import setup, find_packages

import mailfactory_extras as me

setup(
    name='tastypie-utils',
    version=me.__version__,
    url='https://github.com/jneight/tastypie-utils',
    install_requires=['django-tastypie'],
    description="Custom fields, resources and other utilities for tastypie.",
    author=me.__author__,
    author_email=me.__email__,
    include_package_data=True,
    packages=find_packages(),
    license=me.__license__,
    test_suite="tests",
)
