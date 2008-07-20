# -*- coding: UTF-8 -*-
# dg.__init__

"""
Module for handling Divergloss XML glossaries.

@author: Chusslove Illich (Часлав Илић) <caslav.ilic@gmx.net>
@license: GPLv3
"""

import os

def rootdir():
    """
    Get root directory of Dg installation.

    @return: absolute directory path
    @rtype: string
    """

    return __path__[0]

# Global translation object, used internally (only calls exposed in dg.util).
_mo_dir = os.path.join(os.path.dirname(rootdir()), "mo")
if not os.path.isdir(_mo_dir):
    # No repository path, fall back to installed path.
    # FIXME: Synchronize path with installation.
    _mo_dir = "/usr/share/locale"
import gettext
try:
    _tr = gettext.translation("dgproc", _mo_dir)
except IOError:
    _tr = gettext.NullTranslations()

# Path to DTDs.
_dtd_dir = os.path.join(os.path.dirname(rootdir()), "dtd") # FIXME
if not os.path.isdir(_dtd_dir):
    # No repository path, fall back to installed path.
    # FIXME: Synchronize path with installation.
    _dtd_dir = "/usr/share/xml/divergloss"
