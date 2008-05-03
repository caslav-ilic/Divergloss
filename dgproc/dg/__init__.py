# -*- coding: UTF-8 -*-
# dg.__init__

"""
Module for handling Divergloss XML glossaries.

@author: Chusslove Illich (Часлав Илић) <caslav.ilic@gmx.net>
@license: GPLv3
"""

import os


# Global translation object, used internally (only calls exposed in dg.util).
_mo_dir = os.path.join(os.path.dirname(__path__[0]), "mo") # FIXME
import gettext
try:
    _tr = gettext.translation("dgproc", _mo_dir)
except IOError:
    _tr = gettext.NullTranslations()

# Path to DTDs.
_dtd_dir = os.path.join(os.path.dirname(__path__[0]), "dtd") # FIXME

