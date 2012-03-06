#!/usr/bin/python
# vim: set fileencoding=utf-8 :
from setuptools import setup,find_packages
from os.path import join

setup(
    name='odincal',
    version='0.0.1',
    description = 'Odin calibration project',
    long_description=open("README.txt").read() + "\n" +
    open(join("docs", "CHANGELOG.txt")).read(),

    packages = find_packages(exclude=['tests']),
    include_package_data=True,
    test_suite='tests',
    zip_safe=True,
    author='Joakim Möller',
    author_email='joakim.moller@molflow.com',
    url='http://www.molflow.com/odincal',
    install_requires=[
        'numpy',
        'matplotlib',
        'PyGreSQL',
        'setuptools',
    ],
    #tests_require=['setuptools'],
)
