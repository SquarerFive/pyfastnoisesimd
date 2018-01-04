# -*- coding: utf-8 -*-
########################################################################
#
#       pyfastnoisesimd
#       License: BSD
#       Created: August 13, 2017
#       C++ Library Author: Jordan Peck - https://github.com/Auburns
#       Python Extension Author:  Robert A. McLeod - robbmcleod@gmail.com
#
########################################################################

# flake8: noqa
from __future__ import print_function

import os
import platform
import re
import sys

from distutils.command.build import build as _build
from distutils.errors import CCompilerError, DistutilsOptionError
from setuptools import Extension
from setuptools import setup
from glob import glob
from numpy import get_include

# pyfastnoisesimd version
major_ver = 0
minor_ver = 2
nano_ver = 2

branch = ''

VERSION = "%d.%d.%d%s" % (major_ver, minor_ver, nano_ver, branch)

# Create the version.py file
open('pyfastnoisesimd/version.py', 'w').write('__version__ = "%s"\n' % VERSION)

# Sources and headers
sources = [
    'pyfastnoisesimd/fastnoisesimd/FastNoiseSIMD.cpp',
    'pyfastnoisesimd/fastnoisesimd/FastNoiseSIMD_internal.cpp',
    'pyfastnoisesimd/fastnoisesimd/FastNoiseSIMD_neon.cpp',
    'pyfastnoisesimd/wrapper.cpp'
]
inc_dirs = [get_include(), 'pyfastnoisesimd', 'pyfastnoisesimd/fastnoisesimd/']
lib_dirs = []
libs = []
def_macros = []

with open('README.rst') as fh:
    long_desc = fh.read()

if os.name == 'nt':
    extra_cflags = []
    avx512 = {
        'sources': [
            'pyfastnoisesimd/fastnoisesimd/FastNoiseSIMD_avx512.cpp'
        ],
        'cflags': [
            '/arch:AVX512',
        ],
    }
    avx2 = {
        'sources': [
            'pyfastnoisesimd/fastnoisesimd/FastNoiseSIMD_avx2.cpp'
        ],
        'cflags': [
            '/arch:AVX2',
        ]
    }
    sse41 = {
        'sources': [
            'pyfastnoisesimd/fastnoisesimd/FastNoiseSIMD_sse41.cpp'
        ],
        'cflags': [
            '/arch:SSE2',
        ],
    }
    sse2 = {
        'sources': [
            'pyfastnoisesimd/fastnoisesimd/FastNoiseSIMD_sse2.cpp'
        ],
        'cflags': [
            '/arch:SSE2',
        ],
    }
    fma_flags = None
else:  # Linux
    extra_cflags = ['-std=c++11']
    avx512 = {
        'sources': [
            'pyfastnoisesimd/fastnoisesimd/FastNoiseSIMD_avx512.cpp'
        ],
        'cflags': [
            '-mavx512f',
        ],
    }
    avx2 = {
        'sources': [
            'pyfastnoisesimd/fastnoisesimd/FastNoiseSIMD_avx2.cpp'
        ],
        'cflags': [
            '-mavx2',
        ]
    }
    sse41 = {
        'sources': [
            'pyfastnoisesimd/fastnoisesimd/FastNoiseSIMD_sse41.cpp'
        ],
        'cflags': [
            '-msse4.1',
        ],
    }
    sse2 = {
        'sources': [
            'pyfastnoisesimd/fastnoisesimd/FastNoiseSIMD_sse2.cpp'
        ],
        'cflags': [
            '-msse2'
        ],
    }
    fma_flags = ['-mfma']

clibs = [
    ('avx512', avx512),
    ('avx2', avx2),
    ('sse41', sse41),
    ('sse2', sse2),
]


class build(_build):
    user_options = _build.user_options + [
        ('with-avx512=', None, 'Use AVX512 instructions: auto|yes|no'),
        ('with-avx2=', None, 'Use AVX2 instructions: auto|yes|no'),
        ('with-sse41=', None, 'Use SSE4.1 instructions: auto|yes|no'),
        ('with-sse2=', None, 'Use SSE2 instructions: auto|yes|no'),
        ('with-fma=', None, 'Use FMA instructions: auto|yes|no'),
    ]

    def initialize_options(self):
        _build.initialize_options(self)
        self.with_avx512 = 'auto'
        self.with_avx2 = 'auto'
        self.with_sse41 = 'auto'
        self.with_sse2 = 'auto'
        self.with_fma = 'auto'

    def finalize_options(self):
        _build.finalize_options(self)

        disabled_libraries = []
        for name, lib in self.distribution.libraries:
            val = getattr(self, 'with_' + name)
            if val not in ('auto', 'yes', 'no'):
                raise DistutilsOptionError('with_%s flag must be auto, yes, '
                                           'or no, not "%s".' % (name, val))

            if val == 'no':
                disabled_libraries.append(name)
                continue

            is_available = True  # TODO: Actually check compiler.

            if not is_available:
                if val == 'yes':
                    # Explicitly required but not available.
                    raise CCompilerError('%s is not supported by your '
                                         'compiler.' % (name, ))
                disabled_libraries.append(name)

        use_fma = False
        if (self.with_fma != 'no' and
                ('avx512' not in disabled_libraries or
                 'avx2' not in disabled_libraries)):
            if fma_flags is None:
                # No flags required.
                use_fma = True
            else:
                # TODO: Actually check compiler.
                use_fma = True

        self.distribution.libraries = [lib
                                       for lib in self.distribution.libraries
                                       if lib[0] not in disabled_libraries]

        with open('pyfastnoisesimd/fastnoisesimd/x86_flags.h', 'wb') as fh:
            fh.write(b'// This file is generated by setup.py, '
                     b'do not edit it by hand\n')
            for name, lib in self.distribution.libraries:
                fh.write(b'#define FN_COMPILE_%b\n' % (name.upper().encode('ascii', )))
            if use_fma:
                fh.write(b'#define FN_USE_FMA\n')


# List classifiers:
# https://pypi.python.org/pypi?%3Aaction=list_classifiers
classifiers = """\
Development Status :: 5 - Production/Stable
Intended Audience :: Developers
Intended Audience :: Information Technology
License :: OSI Approved :: BSD License
Programming Language :: Python
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Topic :: Software Development :: Libraries :: Python Modules
Topic :: Multimedia :: Graphics :: 3D Modeling
Operating System :: Microsoft :: Windows
Operating System :: Unix
"""

setup(name = "pyfastnoisesimd",
      version = VERSION,
      description = 'Python Fast Noise with SIMD',
      long_description = long_desc,
      classifiers = [c for c in classifiers.split("\n") if c],
      author = 'Robert A. McLeod',
      author_email = 'robbmcleod@gmail.com',
      maintainer = 'Robert A. McLeod',
      maintainer_email = 'robbmcleod@gmail.com',
      url = 'http://github.com/robbmcleod/pyfastnoisesimd',
      license = 'https://opensource.org/licenses/BSD-3-Clause',
      platforms = ['any'],
      libraries = clibs,
      cmdclass = {'build': build},
      ext_modules = [
        Extension( "pyfastnoisesimd.extension",
                   include_dirs=inc_dirs,
                   define_macros=def_macros,
                   sources=sources,
                   library_dirs=lib_dirs,
                   libraries=libs,
                   extra_compile_args=extra_cflags),
        ],
      # tests_require=tests_require,
      packages = ['pyfastnoisesimd'],

)
