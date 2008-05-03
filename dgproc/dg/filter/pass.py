# -*- coding: UTF-8 -*-

"""
Filter which just passes glossary unchanged.

@author: Chusslove Illich (Часлав Илић) <caslav.ilic@gmx.net>
@license: GPLv3
"""

from dg.util import p_


def fill_optparser (parser_view):

    pv = parser_view

    pv.set_desc(p_("subcommand description",
                   "Pass-through filter, changes nothing in the glossary."))


class Subcommand (object):

    def __init__ (self, options, global_options):

        pass


    def process (self, gloss):

        return gloss

