#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name = 'mir-profiler',
      author = 'Daniel Miller',
      author_email = 'dmiller15@uchicago.edu',
      version = 0.2,
      description = 'BCGSC miRNA Profiling Tools',
      url = 'https://github.com/dmiller15/mirna-profiler',
      license = 'Apache 2.0',
      packages = find_packages(),
      install_requires = [
          'pandas',
          'sqlalchemy',
          'psycopg2>=2.6.1'
      ],
      classifiers = [
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
      ],
)
