#! /usr/bin/env python

import os

from setuptools import setup, Extension,find_packages
#from setuptools import get_python_inc

#incdir = os.path.join(get_python_inc(plat_specific=1), "numpy")
odinlibdir = "Library"

module1 = Extension('oops.odin', 
                     sources = ['oops/odinmodule.c'],
                     #include_dirs=[incdir, odinlibdir],
                     include_dirs=[odinlibdir],
                     library_dirs=[odinlibdir],
                     libraries=["odin"]
)

setup (name = 'oops',
       version = '1.1',
       description="Python interface to the Odin C-library",
       packages = find_packages(),
       author="Michael Olberg",
       author_email="michael.olberg@chalmers.se",
       ext_modules = [module1])
