# -*- coding: UTF-8 -*-

"""
Create HTML page with bilingual dictionary.

Useful for making compact embeddable dictionaries for web pages.

@author: Chusslove Illich (Часлав Илић) <caslav.ilic@gmx.net>
@license: GPLv3
"""

import os
import shutil

from dg import rootdir
from dg.util import p_
from dg.util import error, warning

from dg.textfmt import TextFormatterPlain, TextFormatterHtml
from dg.textfmt import etag, stag, wtext
from dg.textfmt import LineAccumulator
from dg.util import langsort, langsort_tuples
from dg.util import mkdirpath


_src_style_dir = os.path.join(rootdir(), "sieve", "html_bidict_extras", "style")
_src_dctl_file = os.path.join(rootdir(), "sieve", "html_bidict_extras", "dctl.js")


def fill_optparser (parser_view):

    # Collect available CSS sheets.
    styles = [""]
    for item in os.listdir(_src_style_dir):
        path = os.path.join(_src_style_dir, item)
        if os.path.isfile(path) and path.endswith(".css"):
            p = item.rfind(".css")
            styles.append(item[:p])

    pv = parser_view

    pv.set_desc(p_("subcommand description",
                   "Create HTML page with bilingual dictionary."))

    pv.add_subopt("olang", str,
                  metavar=p_("placeholder for parameter value", "LANGKEY"),
                  desc=p_("subcommand option description",
                          "Original language in the dictionary."))
    pv.add_subopt("tlang", str,
                  metavar=p_("placeholder for parameter value", "LANGKEY"),
                  desc=p_("subcommand option description",
                          "Target language in the dictionary."))
    pv.add_subopt("env", str, defval="",
                  metavar=p_("placeholder for parameter value", "ENVKEY"),
                  desc=p_("subcommand option description",
                          "Environment for which the dictionary is produced. "
                          "If not given, the glossary default is used."))
    pv.add_subopt("file", str,
                  metavar=p_("placeholder for parameter value", "FILE"),
                  desc=p_("subcommand option description",
                          "File to output the HTML page to."))
    pv.add_subopt("style", str, defval="", admvals=styles,
                  metavar=p_("placeholder for parameter value", "STYLE"),
                  desc=p_("subcommand option description",
                          "Style sheet for the HTML page. "
                          "If not given, the page will not be styled."))
    pv.add_subopt("cssfile", str, defval="",
                  metavar=p_("placeholder for parameter value", "FILE"),
                  desc=p_("subcommand option description",
                          "File path where to copy the selected style sheet. "
                          "If not given, the path is constructed as that of "
                          "the HTML page, with extension replaced by .css."))
    pv.add_subopt("jsfile", str, defval="",
                  metavar=p_("placeholder for parameter value", "FILE"),
                  desc=p_("subcommand option description",
                          "File path where to copy the JavaScript functions. "
                          "If not given, the path is constructed as that of "
                          "the HTML page, with extension replaced by .js."))
    pv.add_subopt("header", str, defval="",
                  metavar=p_("placeholder for parameter value", "ENVKEY"),
                  desc=p_("subcommand option description",
                          "File that contains the page header section to use "
                          "instead of the default, including the <body> "
                          "tag and possibly some preface text."))
    pv.add_subopt("footer", str, defval="",
                  metavar=p_("placeholder for parameter value", "ENVKEY"),
                  desc=p_("subcommand option description",
                          "File that contains the page footer section to use "
                          "instead of the default, possibly including some "
                          "closing text before the </body> tag."))


class Subcommand (object):

    def __init__ (self, options, global_options):

        self._options = options


    def __call__ (self, gloss):

        self._indent = "  "

        # Resolve languages and environment.
        olang = self._options.olang
        if olang not in gloss.languages:
            error(p_("error message",
                     "origin language '%(lang)s' not present in the glossary")
                    % dict(lang=olang))
        tlang = self._options.tlang
        if tlang not in gloss.languages:
            error(p_("error message",
                     "target language '%(lang)s' not present in the glossary")
                    % dict(lang=tlang))
        env = self._options.env or gloss.env[0]
        if env is not None and env not in gloss.environments:
            error(p_("error message",
                     "environment '%(env)s' not defined by the glossary")
                  % dict(env=env))

        # Select all concepts which have a term in both langenvs.
        concepts = {}
        for ckey, concept in gloss.concepts.iteritems():
            if concept.term(olang, env) and concept.term(tlang, env):
                concepts[ckey] = concept
        if not concepts:
            warning(p_("warning message",
                       "no concepts found which have terms in both "
                       "the origin and the target language and environment"))

        # Prepare text formatters.
        refbase = dict([(ckey, "") for ckey in concepts])
        tfn = TextFormatterPlain(gloss, lang=tlang, env=env)
        tf = TextFormatterHtml(gloss, lang=tlang, env=env, refbase=refbase)
        tfp = TextFormatterHtml(gloss, lang=tlang, env=env, refbase=refbase,
                                wtag="p")

        # Dictionary is presented as follows:
        # - all unique terms in the origin language presented
        # - for each unique origin term, all corresponding unique terms
        #   in the target language presented
        # - for each unique (origin, target) term pair, the descriptions of
        #   all concepts named by it are presented in the target language

        # Collect dict(oterm: dict(tterm: set(ckey)))
        # Collect dict(tterm: dict(gr: set(decl)))
        tdecls = {}
        bidict = {}
        for ckey, concept in concepts.iteritems():
            oterms = concept.term(olang, env)
            tterms = concept.term(tlang, env)
            for oterm in oterms:
                otnom = tfn(oterm.nom.text)
                if otnom not in bidict:
                    bidict[otnom] = {}
                for tterm in tterms:
                    # Target terms.
                    ttnom = tfn(tterm.nom.text)
                    if ttnom not in bidict[otnom]:
                        bidict[otnom][ttnom] = set()
                    bidict[otnom][ttnom].add(ckey)

                    # Declensions.
                    if ttnom not in tdecls:
                        tdecls[ttnom] = {}
                    for decl in tterm.decl:
                        gr = gloss.grammar[decl.gr]
                        grnam = tfn(gr.shortname(tlang, env)[0].text)
                        if grnam not in tdecls[ttnom]:
                            tdecls[ttnom][grnam] = set()
                        ttdecl = tfn(decl.text)
                        tdecls[ttnom][grnam].add(ttdecl)

        # Alphabetically sort origin terms.
        oterms_sorted = bidict.keys()
        langsort(oterms_sorted, olang)

        # Compose the dictionary table.
        accl = LineAccumulator(self._indent, 2)

        accl(stag("table", {"class":"bd-table"}))
        accl()

        anchored = {}
        n_entry = 0
        for oterm in oterms_sorted:
            n_entry += 1

            # Collapse all target terms which have same concepts.
            # Sort them alphabetically within the group,
            # then groups alphabetically by first term in the group.
            tterms_by_ckeygr = {}
            for tterm in bidict[oterm]:
                ckeys = list(bidict[oterm][tterm])
                ckeys.sort()
                ckeygr = tuple(ckeys)
                if ckeygr not in tterms_by_ckeygr:
                    tterms_by_ckeygr[ckeygr] = []
                tterms_by_ckeygr[ckeygr].append(tterm)
            tterms_groups = []
            for ckeys, tterms in tterms_by_ckeygr.iteritems():
                langsort(tterms, tlang)
                tterms_groups.append((tterms[0], tterms, ckeys))
            langsort_tuples(tterms_groups, 0, tlang)
            tterms_ckeys = [x[1:] for x in tterms_groups]

            if n_entry % 2 == 1:
                accl(stag("tr", {"class":"bd-entry-odd"}), 1)
            else:
                accl(stag("tr", {"class":"bd-entry-even"}), 1)

            # Column with origin term and anchors.
            accl(stag("td", {"class":"bd-oterm"}), 2)

            # Dummy anchors, for cross-references in descriptions to work.
            # Add anchors for all concepts covered by this entry,
            # and remember them, to avoid duplicate anchors on synonyms.
            new_ckeys = []
            for tterms, ckeys in tterms_ckeys:
                for ckey in ckeys:
                    if ckey not in anchored:
                        anchored[ckey] = True
                        new_ckeys.append(ckey)
            accl("".join([stag("span", {"id":x}, close=True)
                          for x in new_ckeys]), 3)

            # Origin term.
            accl(wtext(oterm, "p", {"class":"bd-otline"}), 3)
            accl(etag("td"), 2)

            # Column with target terms.
            accl(stag("td", {"class":"bd-tterms"}), 2)

            n_ttgr = 0
            for tterms, ckeys in tterms_ckeys:
                n_ttgr += 1
                accl(stag("div", {"class":"bd-ttgroup"}), 3)

                # Equip each term with extra info.
                tterms_compgr = []
                for tterm in tterms:
                    # Declensions.
                    tdecl = None
                    if tterm in tdecls:
                        lst = []
                        for gr, decls in tdecls[tterm].iteritems():
                            lst2 = list(decls)
                            langsort(lst2, tlang)
                            lst.append((gr, ", ".join(lst2)))
                        langsort_tuples(lst, 0, tlang)
                        tdecl = "; ".join(["<i>%s</i> %s" % x for x in lst])
                    # Compose.
                    if tdecl:
                        ttcgr = p_("term with declensions",
                                   "%(term)s (%(decls)s)") \
                                % dict(term=tterm, decls=tdecl)
                    else:
                        ttcgr = tterm
                    tterms_compgr.append(ttcgr)

                # Collect details for each term.
                has_details = False
                # - descriptions
                descstrs = []
                for ckey in ckeys:
                    for desc in concepts[ckey].desc(tlang, env):
                        if tfn(desc.text):
                            descstrs.append(tfp(desc.text, pclass="bd-desc"))
                            has_details = True
                if len(descstrs) > 1:
                    for i in range(len(descstrs)):
                        dhead = "%d. " % (i + 1)
                        descstrs[i] = descstrs[i].replace(">", ">" + dhead, 1)

                # Entry display control (if any details present).
                details_id = "opt_%d_%d" % (n_entry, n_ttgr)
                if has_details:
                    accl(stag("div", {"class":"bd-edctl"}), 4)
                    accl(wtext("[+]", "a",
                               {"class":"bd-edctl",
                                "title":p_("tooltip", "Show details"),
                                "href":"#",
                                "onclick":"return show_hide(this, '%s')"
                                          % details_id}), 5)
                    accl(etag("div"), 4)

                # Line with terms.
                ttstr = ", ".join(tterms_compgr)
                if len(tterms_ckeys) > 1:
                    ttstr = p_("enumerated target term in the dictionary, "
                               "one of the meanings of the original term",
                               "%(num)d. %(term)s") \
                            % dict(num=n_ttgr, term=ttstr)
                accl(wtext(ttstr, "p", {"class":"bd-ttline"}), 4)

                # Optional details.
                if has_details:
                    accl(stag("div", {"id":details_id,
                                      "style":"display: none;"}), 4)

                    for descstr in descstrs:
                        accl(descstr, 5)

                    accl(etag("div"), 4)

                accl(etag("div"), 3)

            accl(etag("td"), 2)
            accl(etag("tr"), 1)
            accl()

        accl(etag("table"))
        accl()

        # Prepare style file.
        stylepath = None
        if self._options.style:
            if self._options.cssfile:
                stylepath = self._options.cssfile
            else:
                stylepath = _replace_ext(self._options.file, "css")
            stylesrc = os.path.join(_src_style_dir, self._options.style + ".css")
            shutil.copyfile(stylesrc, stylepath)

        # Prepare JavaScript file.
        dctlpath = None
        if self._options.jsfile:
            dctlpath = self._options.jsfile
        else:
            dctlpath = _replace_ext(self._options.file, "js")
        shutil.copyfile(_src_dctl_file, dctlpath)

        # Header.
        accl_head = LineAccumulator(self._indent, 0)
        if not self._options.header:
            gname = tfn(gloss.title(tlang, env)[0].text)
            ename = tfn(gloss.environments[env].name(tlang, env)[0].text)
            title = p_("top page title",
                    "%(gloss)s (%(env)s)") \
                    % dict(gloss=gname, env=ename)
            self._fmt_header(accl_head, tlang, title, stylepath, dctlpath)
        else:
            accl_head.read(self._options.header)

        # Footer.
        accl_foot = LineAccumulator(self._indent, 0)
        if not self._options.footer:
            self._fmt_footer(accl_foot)
        else:
            accl_foot.read(self._options.footer)

        # Collect everything and write out the HTML page.
        accl_all = LineAccumulator(self._indent, 0)
        accl_all(accl_head)
        accl_all(accl)
        accl_all(accl_foot)
        accl_all.write(self._options.file)


    def _fmt_header (self, accl, lang, title, stylepath=None, dctlpath=None):

        accl("<?xml version='1.0' encoding='UTF-8'?>");
        accl(  "<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Strict//EN' "
             + "'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd'>");
        accl(  "<!-- "
             + p_('comment in generated files (warning to user)',
                  '===== AUTOGENERATED FILE, DO NOT EDIT =====')
             + " -->")

        accl(stag("html", {"xmlns":"http://www.w3.org/1999/xhtml",
                           "lang":lang, "xml:lang":lang}))

        accl(stag("head"), 1)

        accl(stag("meta", {"http-equiv":"Content-type",
                           "content":"text/html; charset=UTF-8"},
                  close=True), 2)

        if stylepath:
            accl(stag("link", {"rel":"stylesheet", "type":"text/css",
                               "href":stylepath}, close=True), 2)

        if dctlpath:
            accl(wtext("", "script", {"type":"text/javascript",
                                      "src":dctlpath}), 2)

        accl(wtext(title, "title"), 2)

        accl(etag("head"), 1)

        accl(stag("body"), 1)
        accl()


    def _fmt_footer (self, accl):

        accl(etag("body"), 1)
        accl(etag("html"))


def _replace_ext (fpath, newext):
    """
    Replace extension of the file name with the new one.

    The new extension is added if the original file name has none.
    """

    p = os.path.basename(fpath).rfind(".")
    if p > 0:
        p = fpath.rfind(".")
        nfpath = fpath[:p] + "." + newext
    else:
        fpath = fpath + "." + newext

    return nfpath

