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

if test $mode = all || test $mode = compile; then
    echo ">>> Compiling MOs..."
    modir=$cdir/../mo
    pofiles=`echo $cdir/*.po`
    for pofile in $pofiles; do
        echo -n "$pofile  "
        pobase=`basename $pofile`
        lang=${pobase/.po/}
        mofile=$modir/$lang/LC_MESSAGES/$potbase.mo
        mkdir -p `dirname $mofile`
        msgfmt -c --statistics $pofile -o $mofile

        # Special handling for sr->sr@latin.
        if test `basename $pofile` = sr.po; then
            mofile_lat=${mofile/\/sr/\/sr@latin}
            mkdir -p `dirname $mofile_lat`
            recode-sr-latin < $pofile | msgfmt -o $mofile_lat -
        fi
    done
fi
