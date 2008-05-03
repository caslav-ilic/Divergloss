# -*- coding: UTF-8 -*-

"""
Handler for glossary parts which can differ by language and environment.

@author: Chusslove Illich (Часлав Илић) <caslav.ilic@gmx.net>
@license: GPLv3
"""

from dg.util import p_
from dg.util import error


class Dset (object):

    def __init__ (self, gloss, parent=None):

        self.gloss = gloss
        self.parent = parent
        if parent is None:
            self.parent = gloss

        self._data = {}


    def add (self, obj):

        lang = obj.lang
        if lang is None:
            lang = self.parent.lang
        envs = obj.env
        if not envs:
            envs = self.parent.env

        if lang not in self._data:
            self._data[lang] = {}
        for env in envs:
            if env not in self._data[lang]:
                self._data[lang][env] = []
            self._data[lang][env].append(obj)


    def get (self, lang=None, env=None):

        if lang is None:
            lang = self.parent.lang
        if env is None:
            if self.parent.env:
                env = self.parent.env[0]

        if lang not in self._data:
            return None

        if env not in self._data[lang] and self.gloss.environments:
            # Try to select environment by closeness.
            environment = self.gloss.environments[env]
            for close_env in environment.closeto:
                if close_env in self._data[lang]:
                    env = close_env
                    break

        if env not in self._data[lang]:
            return None

        return self._data[lang][env]


    def get_all (self):

        return [z for x in self._data.values() for y in x.values() for z in y]


    def langs (self):

        return self._data.keys()


    def envs (self, lang=None):

        if lang is None:
            lang = self.parent.lang

        if lang not in self._data:
            return None
        return self._data[lang].keys()

