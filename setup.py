from setuptools import setup
from Cython.Build import cythonize
from distutils.extension import Extension

setup(
    name='PyCriUsm',
    version='0.2.0',
    description='A Module to decrypt CRI USM files',
    author='unipendix',
    ext_modules=cythonize(Extension("pycriusm.fast_core", ["pycriusm/fast_core.pyx"])),
    zip_safe=False,
)