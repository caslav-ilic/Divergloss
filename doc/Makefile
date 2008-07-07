#!/bin/sh

all: divergloss.html

%.html: %.docbook
	xmllint --valid $< >/dev/null
	\
date=`date "+%F"`; \
vcsrev=`git log -n1 $< | head -1 | sed 's/^.* //'`; \
cat $< | sed "s/@date@/$$date/" | sed "s/@vcsrev@/$$vcsrev/" > $<.tmp
#	xsltproc /usr/share/xml/docbook/stylesheet/ldp/html/tldp-one-page.xsl $< >$@
	xsltproc /usr/share/xml/docbook/stylesheet/nwalsh/xhtml/docbook.xsl $<.tmp > $@
	rm $<.tmp
	tidy -q -utf8 -xml -w 0 -m $@

clean:
	rm -r *.html
