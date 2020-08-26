from setuptools import setup, Extension
import numpy
from Cython.Build import cythonize
"""
setup( 
    ext_modules = cythonize(
                        Extension(
                            "newlighting",
                            sources=["newlighting.pyx", "libset.cc"],
                            language="c++"
                        ),
                        annotate=True
                    ),
    include_dirs=[numpy.get_include()]
    )

"""
setup(
    ext_modules = cythonize("newlighting.pyx",annotate=True),
    include_dirs=[numpy.get_include()],   
)

