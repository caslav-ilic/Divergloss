#!/bin/sh

cd $(dirname $0)

mode=$1

topdbk=divergloss.docbook

xmllint --valid $topdbk >/dev/null

test "$mode" = "check" && exit 0

rm -rf html && mkdir html
ln -s ../html-data html/data
xsltproc local.xsl $topdbk >html/index.html
tidy -q --show-warnings no -utf8 -w 0 -m html/*.html; test -z
# Remove title= attributes to sectioning classes,
# because they cause a tooltip to be shown wherever the pointer is.
perl -pi -e 's/(<div[^>]*?class="(abstract|article|book|chapter|sect)[^>]*?) *title=".*?"/\1/' html/*.html
