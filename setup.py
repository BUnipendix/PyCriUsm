from setuptools import setup
from Cython.Build import cythonize
from distutils.extension import Extension

setup(
    name='PyCriUsm',
    version='0.1.0',
    description='A Module to decrypt CRIUSM video files',
    author='unipendix',
    ext_modules=cythonize(Extension("decrypt", ["cri_usm_demuxer/decrypt.pyx"])),
    zip_safe=False,
)