#!/usr/bin/python
# -*- coding: utf-8 -*-
# The divergloss setup script

from distutils.core import setup

setup(name='divergloss',  
      version='0.1',
      description='The Diversity Glossary Toolkit',
      author='Chusslove Illich',
      author_email='caslav.ilic@gmx.net',
      requires=['lxml'],
      license='GPLv3',
      package_dir={'': 'dgproc'},
      packages=['dg', 'dg.sieve'],
      package_data={'dg': ['doc/html/*'], 
                    'dg.sieve': ['html_extras/style/apricot/*',
                                 ]},
      url='http://groups.google.com/sorta',
      scripts=['dgproc/dgproc.py']
      )
