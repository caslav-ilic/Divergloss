#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
The divergloss setup script

Used to make the source archive, the distribution, or to install
divergloss.  It uses the distutils tools which provide standard means
of installation for the python modules.
"""
import os
import sys
import re
from glob import glob
from distutils.core import setup


if os.name != "posix":
    print "Installing on non-POSIX systems not implemented yet."
    sys.exit(1)


doc_destination_dir_pattern = os.path.join('share', 'doc', 'divergloss', '%s')
mo_source_dir = os.path.join('dgproc', 'mo')
locale_destination_path = os.path.join('share', 'locale', '%s', 'LC_MESSAGES')
xml_destination_dir = os.path.join('share','xml','divergloss')
xml_source_dir = os.path.join('dgproc','dtd','*.dtd')
html_files_pattern = os.path.join('doc', '*.html')
css_files_pattern = os.path.join('doc', '*.css')
epydoc_files_pattern = os.path.join('dgproc','dg','doc','html','*')
html_source_files = glob(html_files_pattern) + glob(css_files_pattern)

data_files = []
data_files += [(xml_destination_dir, glob(xml_source_dir))]
data_files += [(doc_destination_dir_pattern % 'guide', html_source_files)]
data_files += [(doc_destination_dir_pattern % 'api',glob(epydoc_files_pattern))]

for langdir in os.listdir(mo_source_dir):
    mofile = os.path.join(mo_source_dir, langdir, 'LC_MESSAGES', 'dgproc.mo')
    if os.path.isfile(mofile):
        modestdir =  locale_destination_path % langdir
        data_files += [(modestdir, [mofile])]


setup(name='divergloss',  
      version='0.1',
      description='The Diversity Glossary Toolkit',
      author='Chusslove Illich',
      author_email='caslav.ilic@gmx.net',
      requires=['lxml'],
      license='GPLv3',
      package_dir={'': 'dgproc'},
      packages=['dg', 'dg.sieve'],
      package_data={'dg.sieve': ['html_extras/style/apricot/*']},
      url='http://groups.google.com/sorta',
      scripts=['dgproc/dgproc.py'],
      data_files=data_files,
      )
