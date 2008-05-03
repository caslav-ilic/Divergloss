# -*- coding: UTF-8 -*-

"""
View which shows nothing of the glossary.

@author: Chusslove Illich (Часлав Илић) <caslav.ilic@gmx.net>
@license: GPLv3
"""

from dg.util import p_


def fill_optparser (parser_view):

    pv = parser_view

    pv.set_desc(p_("subcommand description",
                   "Null-view, builds no view of the glossary."))


class Subcommand (object):

    def __init__ (self, options, global_options):

        pass


    def process (self, gloss):

        pass

