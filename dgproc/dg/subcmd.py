# -*- coding: UTF-8 -*-

"""
Handle subcommands and their parameters.

Subcommands are putting main command into different modes of operation.
Main commands with subcommands are typical of package managers, version
control systems, etc. This module provides a handler to conveniently load
subcommands on demand, and parser to extract and route parameters to them
from the command line.

The command line interface consists of having subcommand a free parameter,
and a special collector-option to collect parameters for the subcommand::

    $ cmd -a -b -c \  # command and any usual options
          subcmd \    # subcommand
          -s foo \    # subcommand parameter 'foo', without value (flag)
          -s bar:xyz  # subcommand parameter 'bar', with the value 'xyz'

where C{-s} is the collector-option, repeated for as many subcommand
parameters as needed. The collector-option can be freely positioned in
the command line, before or after the subcommand name, and mixed with
other options.

The format of subcommand barameter is either C{param} for flag parameters, C{param:value} for parameters taking a value, and C{param:value1,value2,...}
for parameters taking a list of values. In the list of values a double-comma
(C{,,}) escapes a comma, so that it can be part of a value.

Several subcommands may be given too, in which case a each subcommand
parameter is routed to every subcommand which expects it. This means that
all those subcommands should place the same semantics into the same-named
parameter they are using. On the other hand, there may be two or more
I{categories} of subcommands, each with its own collector-option::

    $ cmd -a -c -b \
          catx-subcmd \  # subcommand in category z
          -x foo \       # subcommand parameter for category z
          caty-subcmd \  # subcommand in category y
          -y bar:xyz     # subcommand parameter for category y

where again the order of issue of collector-options is insignificant.

There are two ways to handle subcommands and their parameters.
One way is to handle both with the functionality in this module, using the
L{SubcmdHandler}, which puts some organizational and API requirements on
subcommands. Another way is to use only the parameter parsers for subcommands,
the L{SuboptParser} class, and otherwise handle subcommands in a custom manner.

@note: For any of the methods in this module, the order of keyword parameters
is not guaranteed. Always name them in calls.

@author: Chusslove Illich (Часлав Илић) <caslav.ilic@gmx.net>
@license: GPLv3
"""

import os
import re
from textwrap import TextWrapper
import fnmatch

from dg.util import error, p_


class SubcmdHandler (object):
    """
    Handle subcommands organized by categories.

    Each category of subcommands is contained in its own package,
    where every submodule is one subcommand.
    The subcommand names as seen by the user are then the submodule names,
    minus the C{.py} extension and every underscore converted to hyphen
    (e.g. module C{my_subcmd.py} becomes C{my-subcmd} subcommand).

    The API expected out of a subcommand module is simple:

      - It must define the function C{fill_optparser(parser_view)}, where it
        registers subcommand description, parameters, etc,; the C{parser_view}
        is a subcommand view from the L{SuboptParser}, see below for its API.

      - A class named C{Subcommand} must be defined. Its constructor takes,
        in order, the options (parameters) to the subcommand itself and the
        global options of the main command; both are simple objects with
        options as their attributes. This object will be constructed
        by the handler and delivered to the client, so the rest of
        its API shold be designed for the particular application.

    """

    def __init__ (self, subcmd_reg_bundle):
        """
        Constructor.

        Registeres the subcommand categories, using a list where every
        element is a tuple specifying a package and category name::

            import subcmds.foo
            import subcmds.bar
            ...
            sch = SubcmdHandler([(subcmds.foo, "Foos"), (subcmds.bar, "Bars")])

        @param subcmd_reg_bundle: subcommand registration bundle
        @type: list of tuples
        """

        # By package:
        self._packs = {} # subcommand packages (dummy true value)
        self._cats = {} # subcommand categories
        self._subcmds = {} # subcommand names
        self._optparsers = {} # suboption parsers

        # Collect available subcommands.
        for pack, cat in subcmd_reg_bundle:

            modfiles = fnmatch.filter(os.listdir(pack.__path__[0]), "[a-z]*.py")
            subcmds = [x.rstrip(".py").replace("_", "-") for x in modfiles]
            self._packs[pack] = True
            self._cats[pack] = cat
            self._subcmds[pack] = subcmds


    def subcmd_names (self, pack):
        """
        Names of all the subcommands found in the given category.

        @param pack: subcommand package (one from the constructor bundle)
        @type pack: module

        @return: names of the subcommands found in the package
        @rtype: list of strings
        """

        subcmds = self._subcmds.get(pack, None)
        if subcmds is None:
            error(p_("error message",
                     "requested names of subcommands from an "
                     "unknown category"))
        return subcmds


    def init_subcmds (self, subcmd_init_bundle, cmdline_options=None):
        """
        Create subcommand objects and parse and route parameters to them.

        After the client has parsed its command line, collected the names
        of issued subcommands and the inbound parameters (specified by
        the collector-options), it calls this function to create the
        subcommands.

        The initialization bundle is a list of tuples. Each tuple states
        the subcommand package of the issued subcommands, list of subcommand
        names from that package, and the raw parameters for those subcommands
        (list of arguments from the collector-option)::

            subcmds = sch.init_subcmds(
                [(subcmds.foo, # package
                  ["foo-alpha", "foo-beta"], # subcommand names
                  ["fpar1", "fpar2:val", "fpar3:val"]), # raw parameters
                 (subcmds.bar,
                  ["bar-sierra"],
                  ["bpar1", "bpar2:val"])])

        The packages given here must be a subset of what has been given
        to the constructor, and subcommands a subset of those that the
        constructor than found inside the packages.

        If everything goes well -- all subcommands exist, no parameter errors --
        then the subcommand objects are created from the subcommand modules,
        and return in a list of lists, according to the ordering of subcommand
        names in the initialization bundle.

        All options that the main command received, in the form of object with
        attributes (e.g. as created by L{optparse.OptionParser}) may also
        be routed to the subcommands if desired. This may be useful for
        subcommands to heed standard options like quiet, verbose, etc.

        @param subcmd_init_bundle: subcommand initialization bundle
        @type subcmd_init_bundle: list of tuples

        @return: subcommand object
        @rtype: list of lists
        """

        scobjs = []

        for pack, subcmds, rawopts in subcmd_init_bundle:


            if pack not in self._packs:
                error(p_("error message",
                         "requested unknown category of subcommands: %(cat)s")
                      % dict(cat=cat))

            cat = self._cats[pack]
            optparser = SuboptParser(cat)
            self._optparsers[pack] = optparser

            # Load modules for requested subcommands in this category.
            mods = {}
            for subcmd in subcmds:
                if subcmd not in self._subcmds[pack]:
                    error(p_("error in command line",
                             "unknown subcommand requested in "
                             "category '%(cat)s': %(cmd)s")
                          % dict(cat=cat, cmd=subcmd))

                mod = self._import_submod(pack, subcmd)
                mod.fill_optparser(optparser.add_subcmd(subcmd))
                mods[subcmd] = mod

            # Parse options in this category.
            subopts = optparser.parse(rawopts, subcmds)

            # Create subcommand objects in this category.
            scobjs.append([])
            for subcmd in subcmds:
                sc = mods[subcmd].Subcommand(subopts[subcmd], cmdline_options)
                scobjs[-1].append(sc)

        return scobjs


    def _import_submod (self, pack, subcmd):

        modname = pack.__name__ + "." + subcmd.replace("-", "_")
        mod = __import__(modname)
        for el in modname.split('.')[1:]:
            mod = getattr(mod, el)
        return mod


    def help (self, help_req_bundle):
        """
        Produces a help string for the given subcommands by packages.

        The request bundle is a list, where each element is a tuple
        stating a subcommand package and list of subcommand names.

        @param help_req_bundle: request bundle
        @type help_req_bundle: list of tuples

        @return: formatted help
        @rtype: string
        """

        fmts = []
        for pack, subcmds in help_req_bundle:
            fmts.append(self._optparsers[pack].help(subcmds))
        return "\n".join(fmts)


class SuboptParser (object):
    """
    The suboption parser.

    Can be used standalone or through the L{SubcmdHandler}.
    """

    def __init__ (self, category=None):
        """
        Constructor.

        @param category: category of subcommands which the parser serves
        @type category: string or C{None}
        """

        self._category = category
        self._scviews = {}


    def add_subcmd (self, subcmd, desc=None):
        """
        Add a subcommand for which the suboptions may be added afterwards.

        Use double-newline in the description for splitting into paragraphs.
        The description can also be set later, using L{set_desc} method of
        subcommand view.

        @param subcmd: subcommand name
        @type subcmd: string
        @param desc: description of the subcommand
        @type desc: string or C{None}

        @return: subcommand view
        @rtype: L{SubcmdView}
        """

        if subcmd in self._scviews:
            error(p_("error message",
                     "trying to add subcommand '%(cmd)s' once again")
                  % dict(cmd=subcmd))

        self._scviews[subcmd] = SubcmdView(self, subcmd, desc)

        return self._scviews[subcmd]


    def get_view (self, subcmd):
        """
        The view into previously defined subcommand.

        @param subcmd: subcommand name
        @type subcmd: string

        @return: subcommand view
        @rtype: L{SubcmdView}
        """

        scview = self._scviews.get(subcmd, None)
        if scview is None:
            error(p_("error message",
                     "trying to get a view for an unknown "
                     "subcommand '%(cmd)s'") % dict(cmd=subcmd))
        return scview


    def help (self, subcmds, wcol=79):
        """
        Formatted help for requested subcommands.

        @param subcmds: subcommand names
        @type subcmds: list of strings
        @param wcol: column to wrap text at (<= 0 for no wrapping)
        @type wcol: int

        @return: formatted help
        @rtype: string
        """

        fmts = []
        for subcmd in subcmds:
            scview = self._scviews.get(subcmd, None)
            if scview is None:
                error(p_("error message",
                         "trying to get help for an unknown "
                         "subcommand '%(cmd)s'") % dict(cmd=subcmd))
            fmts.append(scview.help())

        return "\n".join(fmts)


    def parse (self, rawopts, subcmds):
        """
        Parse the list of suboptions collected from the command line.

        If the command line had suboptions specified as::

            -sfoo -sbar:xyz -sbaz:10

        then the function call should get the list::

            rawopts=['foo', 'bar:xyz', 'baz:10']

        Result of parsing will be a dictionary of objects by subcommand name,
        where each object has attributes named like subcommand options.
        If an option name is not a non-proper identifier name by itself,
        it will be normalized by replacing all troublesome characters with
        an underscore, collapsing contiguous underscore sequences to a single
        underscore, and prepending an 'x' if it does not start with a letter.

        If an option is parsed which is not accepted by any of the given
        subcommands, an error is signaled.

        @param rawopts: raw suboptions
        @type rawopts: list of strings
        @param subcmds: names of issued subcommands
        @type subcmds: list of strings

        @return: objects with options as attributes
        @rtype: dict of objects by subcommand name
        """

        # Assure only registered subcommands have been issued.
        for subcmd in subcmds:
            if subcmd not in self._scviews:
                error(p_("error in command line (subcommand)",
                         "unregistered subcommand '%(cmd)s' issued")
                      % dict(cmd=subcmd))

        # Parse all given parameters and collect their values.
        subopt_vals = dict([(x, {}) for x in subcmds])
        for opstr in rawopts:
            lst = opstr.split(":", 1)
            lst += [None] * (2 - len(lst))
            subopt, strval = lst

            if subopt in subopt_vals:
                error(p_("error in command line (subcommand)",
                         "parameter '%(par)s' repeated more than once")
                       % dict(par=subopt))

            subopt_accepted = False
            for subcmd in subcmds:
                scview = self._scviews[subcmd]
                if subopt not in scview._otypes:
                    # Current subcommand does not have this option, skip.
                    continue

                otype = scview._otypes[subopt]
                if otype is bool and strval is not None:
                    error(p_("error in command line (subcommand)",
                             "parameter '%(par)s' is a flag, no value expected")
                          % dict(par=subopt))

                val = scview._defvals[subopt]
                if otype is bool:
                    val = not val

                if strval is not None:
                    if not scview._islists[subopt]:
                        try:
                            val = otype(strval)
                        except:
                            error(p_("error in command line (subcommand)",
                                     "cannot convert value '%(val)s' to "
                                     "parameter '%(par)s' into expected "
                                     "type '%(type)s'")
                                  % dict(val=strval, par=subopt, type=otype))
                        val_lst = [val]
                    else:
                        strval = strval.replace(",,", "\x04")
                        tmplst = strval.split(",")
                        tmplst = [x.replace("\x04", ",") for x in tmplst]
                        try:
                            val = [otype(x) for x in tmplst]
                        except:
                            error(p_("error in command line (subcommand)",
                                     "cannot convert value '%(val)s' to "
                                     "parameter '%(par)s' into list of "
                                     "elements of expected type '%(type)s'")
                                  % dict(val=strval, par=subopt, type=otype))
                        val_lst = val

                # Assure admissibility of option values.
                admvals = scview._admvals[subopt]
                if admvals is not None:
                    for val in val_lst:
                        if val not in admvals:
                            avals = self._fmt_admvals(admvals)
                            error(p_("error in command line (subcommand)",
                                     "value '%(val)s' to parameter '%(par)s' "
                                     "not from the admissible set: %(avals)s")
                                  % dict(val=strval, par=subopt, avals=avals))

                subopt_accepted = True
                subopt_vals[subcmd][subopt] = val

            if not subopt_accepted:
                error(p_("error in command line (subcommand)",
                         "parameter '%(par)s' not expected in any of the "
                         "issued subcommands") % dict(par=subopt))


        # Assure that all mandatory parameters have been supplied to each
        # issued subcommand, and set defaults for all optional parameters.
        for subcmd in subcmds:
            scview = self._scviews[subcmd]

            for subopt in scview._otypes:
                if subopt in subopt_vals[subcmd]:
                    # Option explicitly given, skip.
                    continue

                defval = scview._defvals[subopt]
                if defval is None:
                    error(p_("error in command line (subcommand)",
                             "mandatory parameter '%(par)s' to subcommand "
                             "'%(cmd)s' not given")
                          % dict(par=subopt, cmd=subcmd))

                subopt_vals[subcmd][subopt] = defval

        # Create dictionary of option objects.
        class SuboptsTemp (object): pass
        opts = {}
        for subcmd in subcmds:
            opts[subcmd] = SuboptsTemp()
            for subopt, val in subopt_vals[subcmd].iteritems():
                # Construct valid attribute name out option name.
                to_attr_rx = re.compile(r"[^a-z0-9]+", re.I|re.U)
                attr = to_attr_rx.sub("_", subopt)
                if not attr[:1].isalpha():
                    attr = "x" + attr
                opts[subcmd].__dict__[attr] = val

        return opts


    def _fmt_admvals (self, admvals, delim=" "):

        lst = []
        for aval in admvals:
            aval_str = str(aval)
            if aval_str != "":
                lst.append(aval_str)
            else:
                lst.append(p_("the name for an empty string as parameter value",
                              "<empty>"))
        return delim.join(lst)


class SubcmdView (object):
    """
    The view of a particular subcommand in an suboption parser.
    """

    def __init__ (self, parent, subcmd, desc=None):
        """
        Constructor.

        @param parent: the parent suboption parser.
        @type parent: L{SuboptParser}
        @param subcmd: subcommand name
        @type subcmd: string
        """

        self._parent = parent
        self._subcmd = subcmd
        self._desc = desc

        # Maps by option name.
        self._otypes = {}
        self._defvals = {}
        self._admvals = {}
        self._metavars = {}
        self._islists = {}
        self._descs = {}

        # Option names in the order in which they were added.
        self._ordered = []


    def set_desc (self, desc):
        """
        Set description of the subcommand.
        """

        self._desc = desc


    def add_subopt (self, subopt, otype,
                    defval=None, admvals=None,
                    metavar=None, islist=False, desc=None):
        """
        Define a suboption.

        Different subcommands handled by the same parser share the semantics
        of a same-named option. This means the option type must be the same
        across subcommands, while its default value and descriptive elements
        may differ.

        If default value is C{None}, it means the option is mandatory.
        If option type is boolean, then the default value has a special
        meaning: the option is always given without an argument (a flag),
        and its value will become be negation of the default.

        Option can also be a comma-separated list of element values, in which
        case the parsed option will be a list of elements of requested type.
        Then the default value should be a list too (or None).
        To have a comma inside an element of the list, it can be escaped by
        double-comma in the command line.

        Use double-newline in the description for splitting into paragraphs.

        @param subopt: option name
        @type subopt: string
        @param otype: type of the expected argument
        @type otype: type
        @param defval: default value for the argument
        @type defval: instance of C{otype} or C{None}
        @param admvals: admissible values for the argument
        @type admvals: list of C{otype} elements or C{None}
        @param metavar: name for option's value
        @type metavar: string or C{None}
        @param islist: whether the option value should be parsed as list
        @type islist: bool
        @param desc: description of the option
        @type desc: string or C{None}
        """

        if defval is not None and not isinstance(defval, otype):
            error(p_("error message",
                     "trying to add suboption '%(opt)s' to "
                     "subcommand '%(cmd)s' with default value '%(val)s' "
                     "different from its stated type '%(type)s'")
                  % dict(opt=subopt, cmd=self._subcmd, val=defval, type=otype))

        if defval is not None and admvals is not None and defval not in admvals:
            error(p_("error message",
                     "trying to add suboption '%(opt)s' to "
                     "subcommand '%(cmd)s' with default value '%(val)s' "
                     "not from the admissible set: %(avals)s")
                  % dict(opt=subopt, cmd=self._subcmd, val=defval,
                         avals=self._parent._fmt_admvals(admvals)))

        if subopt in self._otypes:
            error(p_("error message",
                     "trying to add suboption '%(opt)s' to subcommand "
                     "'%(cmd)s' once again")
                  % dict(opt=subopt, cmd=self._subcmd))

        if islist and defval is None:
            defval = []
        if islist and not isinstance(defval, (tuple, list)):
            error(p_("error message",
                     "suboption '%(opt)s' to subcommand '%(cmd)s' "
                     "stated to be list-valued, but the default value "
                     "is not given as a list")
                  % dict(opt=subopt, cmd=self._subcmd))

        general_otype = None
        general_islist = None
        for scview in self._parent._scviews.itervalues():
            general_otype = scview._otypes.get(subopt, None)
            general_islist = scview._islists.get(subopt, None)

        if general_otype is not None and otype is not general_otype:
            error(p_("error message",
                     "trying to add suboption '%(opt)s' to "
                     "subcommand '%(cmd)s' with a type different from "
                     "other subcommands in the category '%(cat)s'")
                  % dict(opt=subopt, cmd=subcmd, cat=self._parent._category))

        if general_islist is not None and islist is not general_islist:
            error(p_("error message",
                     "trying to add suboption '%(opt)s' to "
                     "subcommand '%(cmd)s' with a list-indicator different "
                     "from other subcommands in the category '%(cat)s'")
                  % dict(opt=subopt, cmd=subcmd, cat=self._parent._category))


        self._otypes[subopt] = otype
        self._defvals[subopt] = defval
        self._admvals[subopt] = admvals
        self._metavars[subopt] = metavar
        self._islists[subopt] = islist
        self._descs[subopt] = desc

        self._ordered.append(subopt)


    def help (self, wcol=79):
        """
        Formatted help for the subcommand.

        @param wcol: column to wrap text at (<= 0 for no wrapping)
        @type wcol: int

        @return: formatted help
        @rtype: string
        """

        # Split parameters into mandatory and optional.
        m_subopts = []
        o_subopts = []
        for subopt in self._ordered:
            if self._defvals[subopt] is None:
                m_subopts.append(subopt)
            else:
                o_subopts.append(subopt)

        # Format output.

        def fmt_wrap (text, indent=""):
            wrapper = TextWrapper(initial_indent=indent,
                                  subsequent_indent=indent,
                                  width=wcol)
            paras = text.split("\n\n")
            fmtparas = []
            for para in paras:
                fmtparas.append(wrapper.fill(para))
            return "\n\n".join(fmtparas)

        def fmt_opt (subopt, indent=""):
            s = ""
            s += indent + "  " + subopt
            otype = self._otypes[subopt]
            if otype is bool:
                s += " "*1 + p_("subcommand help: somewhere near the suboption "
                                "name, indicates the suboption is a flag",
                                "[flag]")
            else:
                metavar = self._metavars[subopt]
                if metavar is None:
                    metavar = p_("subcommand help: default name for the "
                                 "suboptions' parameter; do keep uppercase",
                                 "ARG")
                s += ":%s" % metavar
            defval = self._defvals[subopt]
            if otype is not bool and str(defval):
                s += " "*1 + p_("subcommand help: somewhere near the "
                                "suboption name, states the default value "
                                "of its argument",
                                "[default %(arg)s=%(val)s]") \
                             % dict(arg=metavar, val=defval)
            admvals = self._admvals[subopt]
            if otype is not bool and admvals is not None:
                avals = self._parent._fmt_admvals(admvals)
                s += " "*1 + p_("subcommand help: somewhere near the "
                                "suboption name, states the admissible values "
                                "for its argument",
                                "[%(arg)s is one of: %(avals)s]") \
                             % dict(arg=metavar, avals=avals)
            s += "\n"
            desc = self._descs[subopt]
            if desc:
                s += fmt_wrap(desc, indent + "    ") + "\n"
            return s

        s = ""
        if not self._parent._category:
            s += p_("subcommand help: header", "Subcommand:") + "\n"
        else:
            s += p_("subcommand help: header", "Subcommand (%(cat)s):") \
                 % dict(cat=self._parent._category) + "\n"
        s += "  " + self._subcmd + "\n"
        if self._desc:
            s +=  fmt_wrap(self._desc, "    ") + "\n"

        if m_subopts:
            s += "\n"
            s += "  " + p_("subcommand help: header",
                           "Mandatory parameters:") + "\n"
            for subopt in m_subopts:
                s += fmt_opt(subopt, "  ")

        if o_subopts:
            s += "\n"
            s += "  " + p_("subcommand help: header",
                           "Optional parameters:") + "\n"
            for subopt in o_subopts:
                s += fmt_opt(subopt, "  ")

        return s

