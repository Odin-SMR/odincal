#!/usr/bin/python
# vim: set fileencoding=utf-8 :
from setuptools import setup,find_packages
from os.path import join

setup(
    name='odincal',
    version='0.0.3',
    description = 'Odin calibration project',
    long_description=open("README.txt").read() + "\n" +
    open(join("docs", "CHANGELOG.txt")).read(),

    packages = find_packages(exclude=['tests','db']),
    include_package_data=True,
    test_suite='tests',
    zip_safe=True,
    entry_points= {"console_scripts": [
            "ac2db = odincal.level0:ac2db",
            "fba2db = odincal.level0:fba2db",
            "att2db = odincal.level0:att2db",
            "shk2db = odincal.level0:shk2db",
            "ac_level1a_importer = odincal.ac_level1a_importer:ac_level1a_importer",
            "att_level1_importer = odincal.att_level1_importer:att_level1_importer",
            "shk_level1_importer = odincal.shk_level1_importer:shk_level1_importer",
            "level1b_importer = odincal.level1b_importer:level1b_importer",
            "level1b_exporter = odincal.level1b_exporter:level1b_exporter",
    ],},

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
