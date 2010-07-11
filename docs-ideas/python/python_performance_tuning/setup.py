from distutils.core import setup, Extension
from Pyrex.Distutils import build_ext
import os
import numpy

os.system('f2py -c src/flaplace.f -m flaplace')

setup(
    name = 'Laplace',
    ext_modules=[ Extension("pyx_lap",
                            ["src/pyx_lap.pyx"],
                            include_dirs = [numpy.get_numpy_include()]) ],
    cmdclass = {'build_ext': build_ext}
    )
