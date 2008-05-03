# -*- coding: UTF-8 -*-

"""
Various utilities.

@author: Chusslove Illich (Часлав Илић) <caslav.ilic@gmx.net>
@license: GPLv3
"""

import sys, os, locale

_cmdname = os.path.basename(sys.argv[0])

# --------------------------------------
# Error reporting.

def error (msg, code=1):

    cmdname = _cmdname
    print p_("error message", "%(cmdname)s: error: %(msg)s") % vars()
    sys.exit(code)


def warning (msg):

    cmdname = _cmdname
    print p_("error message", "%(cmdname)s: warning: %(msg)s") % vars()


# --------------------------------------
# Internationalization.

from dg import _tr

# Wrappers for gettext calls.
# As of Python 2.5, module gettext has no knowledge of Gettext's contexts.
# Implement them in the same way Gettext does; do not use pygettext to
# extract POT, but Gettext's native xgettext (>= 0.16).

# Left out: want contexts for all translatable strings.
"""
# Basic call.
def _(msgid):

    msgstr = _tr.ugettext(msgid)
    return msgstr
"""

# Context call.
def p_(msgctxt, msgid):

    cmsgid = msgctxt + "\x04" + msgid
    msgstr = _tr.ugettext(cmsgid)
    p = msgstr.find("\x04")
    if p > 0:
        msgstr = msgstr[p+1:]
    return msgstr


# Left out: want contexts for all translatable strings.
"""
# Plural call.
def n_(msgid, msgid_plural, n):

    msgstr = _tr.ungettext(msgid, msgid_plural, n)
    return msgstr
"""

# Plural with context call.
def np_(msgctxt, msgid, msgid_plural, n):

    cmsgid = msgctxt + "\x04" + msgid
    msgstr = _tr.ungettext(cmsgid, msgid_plural, n)
    p = msgstr.find("\x04")
    if p > 0:
        msgstr = msgstr[p+1:]
    return msgstr


# --------------------------------------
# Miscellaneous.

# Convert object into string using local encoding
def lstr (obj):

    cmdlenc = locale.getdefaultlocale()[1]
    return repr(obj).decode("unicode_escape").encode(cmdlenc)

