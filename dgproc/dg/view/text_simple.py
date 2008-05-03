# -*- coding: UTF-8 -*-

"""
A simple text view (just an example).

@author: Chusslove Illich (Часлав Илић) <caslav.ilic@gmx.net>
@license: GPLv3
"""

import sys

from dg.util import p_
from dg.util import error
from dg.textfmt import TextFormatterPlain


def fill_optparser (parser_view):

    pv = parser_view

    pv.set_desc(p_("subcommand description",
                   "Simple text view as a demonstration of writing views."))

    pv.add_subopt("lang", str, defval="",
                  metavar=p_("placeholder for parameter value", "LANGKEY"),
                  desc=p_("subcommand option description",
                          "Pivotal language for the view. The glossary "
                          "default language is used if not given."))
    pv.add_subopt("env", str, defval="",
                  metavar=p_("placeholder for parameter value", "ENVKEY"),
                  desc=p_("subcommand option description",
                          "Pivotal environment for the view. The glossary "
                          "default environment is used if not given."))
    pv.add_subopt("file", str, defval="",
                  metavar=p_("placeholder for parameter value", "FILE"),
                  desc=p_("subcommand option description",
                          "File to output the text into (defaults to stdout)."))
    pv.add_subopt("wcol", int, defval=70,
                  metavar=p_("placeholder for parameter value", "COLUMN"),
                  desc=p_("subcommand option description",
                          "Wrap text after this column."))


class Subcommand (object):

    def __init__ (self, options, global_options):

        self._options = options


    def process (self, gloss):

        # Resolve language and environment.
        lang = self._options.lang or gloss.lang
        if lang is not None and lang not in gloss.languages:
            error(p_("error message",
                     "language '%(lang)s' does not exits in the glossary")
                    % dict(lang=lang))

        env = self._options.env or gloss.env[0]
        if env is not None and env not in gloss.environments:
            error(p_("error message",
                     "environment '%(env)s' does not exits in the glossary")
                  % dict(env=env))

        # Select all concepts which have a term in this langenv.
        # Collect terms for lexicographical ordering.
        concepts = {}
        ordering_links = []
        for ckey, concept in gloss.concepts.iteritems():
            terms = concept.term.get(lang, env)
            if terms:
                concepts[ckey] = concept
                # Use first of the synonymous terms for ordering.
                ordering_links.append((terms[0], ckey))

        ordering_links.sort(lambda x, y: cmp(x[0], y[0]))

        # Format glossary metadata for output.
        fmt_header = ""
        tfm = TextFormatterPlain(gloss, lang=lang, env=env)
        fmt_title = tfm.format(gloss.title.get(lang, env)[0].text)
        if env is not None:
            fmt_envname = tfm.format(gloss.environments[env]\
                                          .name.get(lang, env)[0].text)
            fmt_title = "%s (%s)" % (fmt_title, fmt_envname)
        fmt_header += fmt_title + "\n"
        fmt_header += "-" * len(fmt_title) + "\n"

        # Format concepts for output.
        fmt_concepts = []
        for concept in [concepts[x[1]] for x in ordering_links]:
            fmt = ""

            # Terms for this langenv.
            tft = TextFormatterPlain(gloss, lang=lang, env=env)
            terms = concept.term.get(lang, env)
            fmt += "  "
            fmt += ", ".join([tft.format(x.nom.text) for x in terms])
            # Also terms in other languages, but the same environment.
            fmt_ots = []
            for olang in [x for x in gloss.languages if x != lang]:
                oterms = concept.term.get(olang, env)
                lname = gloss.languages[olang].shortname.get(lang, env)
                if oterms and lname:
                    l = tft.format(lname[0].text)
                    ts = ", ".join([tft.format(x.nom.text) for x in oterms])
                    fmt_ots.append("%s /%s/" % (l, ts))
            if fmt_ots:
                fmt += " (%s)" % ("; ".join(fmt_ots))
            fmt += "\n"

            # All descriptions for this langenv.
            tfd = TextFormatterPlain(gloss, lang=lang, env=env, indent="    ",
                                     wcol=self._options.wcol)
            descs = concept.desc.get(lang, env)
            if descs:
                fmt_ds = []
                if len(descs) == 1:
                    fmt_ds.append(tfd.format(descs[0].text))
                elif len(descs) > 1:
                    # Enumerate descriptions.
                    for i in range(len(descs)):
                        fmt_ds.append(tfd.format(descs[i].text,
                                                 prefix=("%d. " % (i + 1))))
                fmt += "\n\n".join(fmt_ds)

            # Done formatting concept.
            fmt_concepts.append(fmt)

        # Output formatted concepts to requested stream.
        outf = sys.stdout
        if self._options.file:
            outf = open(self._options.file, "w")

        outf.write(fmt_header + "\n")
        outf.write("\n\n".join(fmt_concepts)+"\n\n")

        if outf is not sys.stdout:
            outf.close()

        # All done.

