# -*- coding: UTF-8 -*-

"""
Update terminology rules file for Pology's C{check-rules} sieve.

Pology's C{check-rules} sieve applies series of pattern rules to messages
in a PO file, reporting all those that matched. Each rule can contain
several matching expressions, applied in different ways, and interlinked
in a boolean-semantic way.

This sieve updates such a rules file (or creates a new one), adding
basic skeletons of new rules for checking terminology; rules must then
be edited manually to make them applicable. This is, in fact, almost
of no value from the point of view of a particular rule, as the core of
the rule must be created by the user. The usefulness of the sieve lies
instead in that it can be used to automatically check if any of
the existing rules needs to be changed due to terminology changes,
and add rules for new terminology as it becomes available,
without having to keep track of it manually.

Within a rule, concept key is stored in the C{ident} field, while the
terminology pair is given by the C{hint} field, in form of
C{"<original-terms> = <target-terms> [<free-hints>]"}.
It is important to keep any free text in the hint within square brackets,
so that the sieve can detect and indicate terminology changes.

Newly added rules will have C{@gloss-new} string in their comment.
Existing rules for which the terminology has changed will get C{@gloss-fuzzy},
while those that no longer have a matching concept will get C{@gloss-obsolete}.

The rule files is expected to be UTF-8 encoded (same as Pology expects).

As the rules files are translation-oriented, the glossary must be
at least bilingual by terms.

@author: Chusslove Illich (Часлав Илић) <caslav.ilic@gmx.net>
@license: GPLv3
"""

import sys
import time
import codecs
import re

from dg.util import p_
from dg.util import error, warning
from dg.textfmt import TextFormatterPlain
from dg.util import langsort


def fill_optparser (parser_view):

    pv = parser_view

    pv.set_desc(p_("subcommand description",
                   "Update rules files for Pology's check-rules sieve."))

    pv.add_subopt("olang", str,
                  metavar=p_("placeholder for parameter value", "LANGKEY"),
                  desc=p_("subcommand option description",
                          "Original language from the rules point of view."))
    pv.add_subopt("tlang", str,
                  metavar=p_("placeholder for parameter value", "LANGKEY"),
                  desc=p_("subcommand option description",
                          "Target language from the rules point of view."))
    pv.add_subopt("file", str,
                  metavar=p_("placeholder for parameter value", "FILE"),
                  desc=p_("subcommand option description",
                          "Rules file to update or create."))
    pv.add_subopt("env", str, defval="",
                  metavar=p_("placeholder for parameter value", "ENVKEY"),
                  desc=p_("subcommand option description",
                          "Environment for which the rules are updated. "
                          "The glossary default environment is used "
                          "if not given."))


class Subcommand (object):

    def __init__ (self, options, global_options):

        self._options = options


    def __call__ (self, gloss):

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
        rulefile = self._options.file

        # Formatters for resolving glossary into plain text.
        tft = TextFormatterPlain(gloss, lang=tlang, env=env)
        tdelim = "|" # to be able to send terms to regex too

        def format_terms (concept):

            oterms = [tft(x.nom.text) for x in concept.term(olang, env)]
            langsort(oterms, olang)
            otermsall = tdelim.join(oterms)

            tterms = [tft(x.nom.text) for x in  concept.term(tlang, env)]
            langsort(tterms, tlang)
            ttermsall = tdelim.join(tterms)

            return otermsall, ttermsall

        # Select all concepts which have a term in both langenvs.
        concepts = {}
        for ckey, concept in gloss.concepts.iteritems():
            oterms = concept.term(olang, env)
            tterms = concept.term(tlang, env)
            if oterms and tterms:
                concepts[ckey] = concept

        if not concepts:
            warning(p_("warning message",
                       "no concepts found for PO view that have terms in both "
                       "the requested origin and target language"))

        # Parse rules file.
        rules, rmap, plines, elines = self._load_rules(rulefile)

        # Flag all existing rules.
        for rkey, rule in rmap.iteritems():

            if rkey not in concepts:
                rule.set_flag("obsolete")
                continue

            oterms, tterms = format_terms(concepts[rkey])
            if oterms != rule.oterms or tterms != rule.tterms:
                note = "%s = %s" % (oterms, tterms)
                rule.set_flag("fuzzy", note)
                continue

            if not rule.has_flag("new"):
                rule.set_flag("")

        # Add new rules, in lexicographical order by keys.
        ckeys = concepts.keys()
        ckeys.sort()
        last_ins_pos = -1
        for ckey in ckeys:
            if ckey in rmap:
                continue

            nrule = self._Rule()
            nrule.ckey = ckey
            nrule.oterms, nrule.tterms = format_terms(concepts[ckey])
            nrule.disabled = True
            # Add all fields for establishing ordering;
            # some will get their real values on sync.
            if tdelim not in nrule.oterms:
                topmatch = "{\\b%s}" % nrule.oterms
            else:
                topmatch = "{\\b(%s)}" % nrule.oterms
            if nrule.oterms.islower():
                topmatch += "i"
            nrule.lines.append(topmatch)
            nrule.lines.append("id=\"\"")
            nrule.lines.append("hint=\"\"")
            if tdelim not in nrule.tterms:
                valmatch = "valid msgstr=\"\\b%s\"" % nrule.tterms
            else:
                valmatch = "valid msgstr=\"\\b(%s)\"" % nrule.tterms
            nrule.lines.append(valmatch)
            nrule.lines.append("disabled=\"1\"")
            nrule.set_flag("new")

            inserted = False
            for i in range(last_ins_pos + 1, len(rules)):
                if ckey < rules[i].ckey:
                    last_ins_pos = i
                    rules.insert(i, nrule)
                    inserted = True
                    break
            if not inserted:
                last_ins_pos = len(rules)
                rules.append(nrule)
            rmap[ckey] = nrule

        # Write rules back.
        ofl = codecs.open(rulefile, "w", "UTF-8")
        ofl.writelines([x + "\n" for x in plines])
        for rule in rules:
            ofl.writelines(rule.format_lines())
        ofl.writelines([x + "\n" for x in elines])
        ofl.close()

        # All done.


    class _Rule:

        hint_rx = re.compile(r"^\s*hint\s*=\s*\"(.*)\"")
        free_hint_rx = re.compile(r"\[(.*)\]")
        ident_rx = re.compile(r"^\s*id\s*=\s*\"(.*)\"")
        disabled_rx = re.compile(r"^\s*disabled\s*=\s*\"(.*)\"")

        flag_pref = "@gloss-"
        flag_rx = re.compile(r"^\s*#\s*%s(\w+)" % flag_pref)

        def __init__ (self):

            self.ckey = u""
            self.oterms = u""
            self.tterms = u""
            self.freehint = None
            self.disabled = False

            self.lines = []


        def set_flag (self, flag, note=None):

            flag_cmnt = ""
            if flag:
                flag_cmnt = "# " + self.flag_pref + flag
                if note is not None:
                    flag_cmnt += " [%s]" % note
            self.set_line(lambda x: x.startswith("#") and self.flag_pref in x,
                          flag_cmnt, 0)


        def has_flag (self, flag):

            for line in self.lines:
                m = self.flag_rx.search(line)
                if m:
                    cflag = m.group(1)
                    if cflag == flag:
                        return True

            return False


        def sync_lines (self):

            # Create or remove ident.
            identstr = ""
            if self.ckey:
                identstr = "id=\"%s\"" % self.ckey
            self.set_line(lambda x: self.ident_rx.search(x), identstr)

            # Create or remove hint.
            hintstr = ""
            if self.oterms and self.tterms and self.freehint is not None:
                hintstr = "hint=\"%s = %s [%s]\"" % (self.oterms, self.tterms,
                                                     self.freehint)
            elif self.oterms and self.tterms:
                hintstr = "hint=\"%s = %s\"" % (self.oterms, self.tterms)
            elif self.freehint is not None:
                hintstr = "hint=\"%s\"" % self.freehint
            self.set_line(lambda x: self.hint_rx.search(x), hintstr)

            # Create or remove disabled state.
            disabledstr = ""
            if self.disabled:
                disabledstr = "disabledstr=\"1\""
            self.set_line(lambda x: self.disabled_rx.search(x), disabledstr)


        def set_line (self, check, nline, defpos=None):

            inspos = -1
            i = 0
            while i < len(self.lines):
                if check(self.lines[i]):
                    if inspos < 0:
                        inspos = i
                    self.lines.pop(i)
                else:
                    i += 1
            if inspos < 0:
                if defpos is None:
                    inspos = len(self.lines)
                else:
                    inspos = defpos
            if nline:
                self.lines.insert(inspos, nline)


        def format_lines (self):

            self.sync_lines()

            flines = [x + "\n" for x in self.lines]
            flines.append("\n")

            return flines


    def _load_rules (self, fpath):
        """
        Loads rules files in a simplified format.

        For each rule the needed fields are parsed (e.g. ident, hint),
        and the rest is just kept as a bunch of lines.

        Return list of parsed rule objects and dictionary mapping to
        it for rules recognized as glossary concepts (by concept key).
        Also the file prologue and epilogue as lists of lines.
        """

        # The syntax of rules files is a bit ad-hoc;
        # hence some of the parsing below may be strange.

        ifl = codecs.open(fpath, "UTF-8")

        hint_rx = self._Rule.hint_rx
        free_hint_rx = self._Rule.free_hint_rx
        ident_rx = self._Rule.ident_rx
        disabled_rx = self._Rule.disabled_rx

        prologue = []
        rules = []
        rmap = {}

        in_prologue = True
        crule = self._Rule()
        for line in ifl:
            line = line.rstrip("\n")

            if line.startswith("#"): # comment
                if in_prologue:
                    prologue.append(line)
                else:
                    crule.lines.append(line)
                continue

            if not line: # rule finished
                if in_prologue: # last line of file prologue
                    in_prologue = False
                    prologue.append(line)
                    continue
                if not crule.lines: # empty rule, shouldn't have, but...
                    continue
                rules.append(crule)
                crule = self._Rule()
                continue

            m = ident_rx.search(line)
            if m:
                crule.ckey = m.group(1).strip()
                rmap[crule.ckey] = crule

            m = hint_rx.search(line)
            if m:
                hintstr = m.group(1)
                orig_hintstr = hintstr

                m = free_hint_rx.search(hintstr)
                if m:
                    crule.freehint = m.group(1)
                hintstr = free_hint_rx.sub("", hintstr)

                p = hintstr.find("=")
                if p >= 0:
                    crule.oterms = hintstr[:p].strip()
                    crule.tterms = hintstr[p+1:].strip()
                else:
                    crule.freehint = orig_hintstr

            m = disabled_rx.search(line)
            if m:
                crule.disabled = str2bool(m.group(1).strip())

            crule.lines.append(line)

        # Last rule actually contains file epilogue.
        epilogue = crule.lines

        ifl.close()

        return rules, rmap, prologue, epilogue

