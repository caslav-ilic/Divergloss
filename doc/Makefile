#!/bin/sh

all: divergloss.html

%.html: %.docbook
	xmllint --valid $< >/dev/null
#	xsltproc /usr/share/xml/docbook/stylesheet/ldp/html/tldp-one-page.xsl $< >$@
	xsltproc /usr/share/xml/docbook/stylesheet/nwalsh/xhtml/docbook.xsl $< >$@

clean:
	rm *.html
