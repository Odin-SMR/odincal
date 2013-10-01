#!/usr/bin/python
# vim: set fileencoding=utf-8 :
from setuptools import setup,find_packages
from os.path import join

setup(
    name='odincal',
    version='0.1.9',
    description = 'Odin calibration project',
    long_description=open("README.txt").read() + "\n" +
    open(join("docs", "CHANGELOG.txt")).read(),

    packages = find_packages(exclude=['tests']),
    include_package_data=True,
    test_suite='tests',
    zip_safe=False,
    package_data={
        'db':['create.sql'],
    },
    entry_points= {"console_scripts": [
            'create_datamodel = db.admin_tools:create_datamodel',
            'download_level0 = util.tools:download_level0',
            "level0file2db = odincal.level0_file_importer:main",
            "level0file_server = odincal.test_serv:main",
            "level0data2db = odincal.level0:level0data2db",
            "level1data2db = odincal.calibration_preprocess:main",
            "level1b_importer = odincal.level1b_importer:level1b_importer",
            "level1b_window_importer = odincal.level1b_window_importer2:level1b_importer",
            "level1b_exporter = odincal.level1b_exporter:level1b_exporter",
            "odinlogserver = odincal.logserver:main",
	    "process_level0_or_calibrate = odincal.process_level0_or_calibrate:main",
	    "ac_average_data_import = odincal.ac_average_data_import:main",
	    "ac_average_datafit_import = odincal.ac_average_datafit_import:main",
    ],},

    author='Joakim Möller',
    author_email='joakim.moller@molflow.com',
    url='http://www.molflow.com/odincal',
    install_requires=[
        'numpy>=1.6.2',
        'matplotlib',
        'PyGreSQL',
        'setuptools',
    ],
    #tests_require=['setuptools'],
)
