#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Filter and build outputs of a Divergloss XML document.

@author: Chusslove Illich (Часлав Илић) <caslav.ilic@gmx.net>
@license: GPLv3
"""

import sys, os, locale, mimetypes
from optparse import OptionParser

if not "PYTHONPATH" in os.environ:
    os.environ["PYTHONPATH"] = ""
os.environ["PYTHONPATH"] = (  os.path.dirname(sys.argv[0]) + ":"
                            + os.environ["PYTHONPATH"])

from dg.util import p_
from dg.util import error
from dg.util import lstr
import dg.construct
import dg.filter
import dg.view
import dg.subcmd


def main ():

    # Use Psyco specializing compiler if available.
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass

    reload(sys)
    cmdlenc = locale.getdefaultlocale()[1]
    sys.setdefaultencoding(cmdlenc)

    # Setup options and parse the command line.
    usage = p_("command usage; do NOT translate %prog",
               "%prog DGFILE [FILTERS] [VIEWS] [OPTIONS]")
    description = p_("command description",
                     "Filter a Divergloss XML document and "
                     "build various outputs. "
                     "Also fully validates the document, "
                     "past what the DTD only can do.")
    version = p_("command version; do NOT translate %prog",
                 "%prog experimental\n"
                 "Copyright 2008, Chusslove Illich <caslav.ilic@gmx.net>")

    opars = OptionParser(usage=usage, description=description, version=version)
    opars.add_option(
        "--no-check",
        action="store_false", dest="check", default=True,
        help=p_("description of cmdline option",
                "do not check the glossary for validity"))
    opars.add_option(
        "-f", "--filter-par",
        metavar=p_("placeholder for value to cmdline option", "PARSPEC"),
        dest="filter_par", action="append", default=[],
        help=p_("description of cmdline option",
                "specify parameter to filters"))
    opars.add_option(
        "-w", "--view-par",
        metavar=p_("placeholder for value to cmdline option", "PARSPEC"),
        dest="view_par", action="append", default=[],
        help=p_("description of cmdline option",
                "specify parameter to views"))
    opars.add_option(
        "-S", "--list-subcmd",
        action="store_true", dest="list_subcmd", default=False,
        help=p_("description of cmdline option",
                "list available filters and views and exit"))
    opars.add_option(
        "-H", "--help-subcmd",
        action="store_true", dest="help_subcmd", default=False,
        help=p_("description of cmdline option",
                "display help on filters and views and exit"))
    (options, free_args) = opars.parse_args()

    # Register subcommands.
    schandler = dg.subcmd.SubcmdHandler(
        [(dg.filter, p_("category of subcommands", "filter")),
         (dg.view, p_("category of subcommands", "view"))])

    if len(free_args) > 3:
        error(p_("error in command line", "too many free arguments"))

    # If any subcommand listing required, show and exit.
    if options.list_subcmd:
        print p_("header to listing", "Available filters:")
        print "  " + "  \n".join(schandler.subcmd_names(dg.filter))
        print p_("header to listing", "Available views:")
        print "  " + "  \n".join(schandler.subcmd_names(dg.view))
        sys.exit(0)

    # Collect glossary file, filters and views.
    if len(free_args) < 1:
        error(p_("error in command line", "no file given"))
    dgfile = free_args[0]
    if not os.path.isfile(dgfile):
        error(p_("error in command line",
                 "file '%(file)s' does not exists") % dict(file=dgfile))

    # Parse filter names.
    filter_names = ["pass"]
    if len(free_args) >= 2:
        filter_names = [x for x in free_args[1].split(",")]

    # Parse view names.
    # nada
    view_names = ["null"]
    if len(free_args) >= 3:
        view_names = [x for x in free_args[2].split(",")]

    # Create subcommands.
    filters, views = schandler.init_subcmds(
        [(dg.filter, filter_names, options.filter_par),
         (dg.view, view_names, options.view_par)],
        options)

    # If help on subcommands required, show and exit.
    if options.help_subcmd:
        print schandler.help([(dg.filter, filter_names),
                              (dg.view, view_names)])
        sys.exit(0)

    # Construct glossary.
    gloss = dg.construct.from_file(dgfile, validate=options.check)

    # Filter glossary.
    for fl in filters:
        print type(fl)
        gloss = fl.process(gloss)

    # View glossary.
    for vw in views:
        vw.process(gloss)


if __name__ == '__main__':
    main()

