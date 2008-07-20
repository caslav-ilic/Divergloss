#!/bin/sh

wdir=`pwd`
cdir=`dirname $0`
potbase=dgproc

mode=all
if test -n "$1"; then
    mode=$1
fi

if test $mode = all || test $mode = extract; then
    echo ">>> Extracting POT..."
    cd $cdir/..
    srcfiles=`find -iname \*.py | sort`
    potfile=po/$potbase.pot
    xgettext --no-wrap \
        -k_:1 -kp_:1c,2 -kn_:1,2 -knp_:1c,2 \
        -o $potfile $srcfiles
    cd $wdir
fi

if test $mode = all || test $mode = merge; then
    echo ">>> Merging POs..."
    potfile=$cdir/$potbase.pot
    pofiles=`echo $cdir/*.po`
    for pofile in $pofiles; do
        echo -n "$pofile  "
        msgmerge -U --backup=none --no-wrap --previous $pofile $potfile
    done
fi

# Generate sr@latin PO if sr present.
if test -f $cdir/sr.po; then
    recode-sr-latin <$cdir/sr.po >$cdir/sr@latin.po
fi

if test $mode = all || test $mode = compile; then
    echo ">>> Compiling MOs..."
    modir=$cdir/../mo
    pofiles=`echo $cdir/*.po`
    for pofile in $pofiles; do
        # Build MO alongside PO, for distribution.
        echo -n "$pofile  "
        pobase=`basename $pofile`
        lang=${pobase/.po/}
        msgfmt -c --statistics $pofile -o $cdir/$lang.mo

        # Copy MO to local hierarchy, for use from within the repository.
        molocal=$modir/$lang/LC_MESSAGES/$potbase.mo
        mkdir -p `dirname $molocal`
        cp $cdir/$lang.mo $molocal
    done
fi
