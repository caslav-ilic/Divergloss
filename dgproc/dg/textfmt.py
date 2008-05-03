# -*- coding: UTF-8 -*-

"""
Format text in glossary for different outputs.

@author: Chusslove Illich (Часлав Илић) <caslav.ilic@gmx.net>
@license: GPLv3
"""

import re
from textwrap import TextWrapper

from dg.construct import Text, Para, Ref, Em, Ol


class TextFormatterPlain (object):
    """
    Format divergloss text into plain text.
    """

    def __init__ (self, gloss, lang=None, env=None,
                        wcol=None, indent=None, first_indent=None,
                        prefix=None, suffix=None):
        """
        Constructor.

        If the language or environment is C{None}, the glossary default is used.

        @param gloss: the glossary to which the text belongs
        @type gloss: L{Glossary}

        @param lang: the language for which the text is formatted
        @type lang: string or C{None}

        @param env: the environment for which the text is formatted
        @type env: string or C{None}

        @param wcol: the column after which the text is wrapped
        @type wcol: int or C{None}

        @param indent: indent for each line of the text
        @type indent: string or C{None}

        @param first_indent: indent for first line of the text
        @type first_indent: string or C{None}

        @param prefix: prefix to add to the text (independent of the indent)
        @type prefix: string or C{None}

        @param suffix: suffix to add to the text
        @type suffix: string or C{None}
        """

        self._gloss = gloss
        self._lang = lang or self._gloss.lang
        self._env = env or (gloss.env and gloss.env[0])

        self._prefix = prefix
        self._suffix = suffix

        self._indent = indent
        self._wrapper = None
        if wcol:
            if indent is None:
                indent = ""
            if first_indent is None:
                first_indent = indent
            self._wrapper = TextWrapper(initial_indent=first_indent,
                                        subsequent_indent=indent,
                                        width=wcol)


    def format (self, text, prefix=None, suffix=None):
        """
        Format the text.

        Prefix and suffix given by the constructor may be overrident here.
        This is useful e.g. for enumerations.

        @param text: the text to be formatted
        @type text: instance of C{Text}

        @param prefix: overriding prefix for the text
        @type prefix: string or C{None}

        @param suffix: overriding suffix for the text
        @type suffix: string or C{None}
        """

        fmt_text = ""

        for seg in text:
            if isinstance(seg, Para):
                fmt_seg = self.format(seg) + "\n\n"
            elif isinstance(seg, Ref):
                # FIXME: Better way to handle reference?
                fmt_seg = self.format(seg) + "°"
            elif isinstance(seg, Em):
                fmt_seg = "*%s*" % self.format(seg)
            elif isinstance(seg, Ol):
                if seg.lang:
                    lnode = self._gloss.languages[seg.lang]\
                                .shortname.get(self._lang, self._env)[0]
                    fmt_seg = "(%s /%s/)" % (self.format(lnode.text),
                                             self.format(seg))
                else:
                    fmt_seg = "(/%s/)" % (self.format(seg))
            elif isinstance(seg, Text):
                # Any unhandled text type.
                fmt_seg = self.format(seg)
            else:
                # Must be a string
                fmt_seg = seg
            fmt_text += fmt_seg

        # Strip superfluous whitespace.
        fmt_text = re.sub("\s+", " ", fmt_text).strip()

        # Prefixate and suffixate if requested.
        prefix = prefix or self._prefix
        if prefix:
            fmt_text = prefix + fmt_text
        suffix = suffix or self._suffix
        if suffix:
            fmt_text = fmt_text + suffix

        # Wrap if requested.
        if self._wrapper:
            fmt_text = self._wrapper.fill(fmt_text)
        elif self._indent:
            fmt_text = self._indent + fmt_text

        return fmt_text

