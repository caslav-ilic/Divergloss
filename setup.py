#!/usr/bin/python
# -*- coding: utf-8 -*-
# The divergloss setup script

import os
import sys
import re
from glob import glob
from distutils.core import setup


if os.name != "posix":
    print "Installing on non-POSIX systems not implemented yet."
    sys.exit(1)


data_files = []

data_files += [('share/xml/divergloss',
                glob('dgproc/dtd/*.dtd'))] # + glob('dgproc/dtd/catalog*')

docdestbase = 'share/doc/divergloss-doc/%s'
data_files += [(docdestbase % 'guide',
                glob('doc/*.html') + glob('doc/*.css'))]
data_files += [(docdestbase % 'api',
                glob('dgproc/dg/doc/html/*'))]

mosrcbase = 'dgproc/mo'
for langdir in os.listdir(mosrcbase):
    mofile = mosrcbase + '/' + langdir + '/LC_MESSAGES/dgproc.mo'
    if os.path.isfile(mofile):
        modestdir = 'share/locale/%s/LC_MESSAGES' % langdir
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
      package_data={'dg.sieve': ['html_extras/style/apricot/*',
                                 ]},
      url='http://groups.google.com/sorta',
      scripts=['dgproc/dgproc.py'],
      data_files=data_files,
      )
