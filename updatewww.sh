#!/bin/sh
#
# Updates the exported WWW directory for divergloss.

DATE="2010-12-06"
DIR=tmpwww

mkdir $DIR
ln -s ../doc/html $DIR/doc
touch -d $DATE $DIR/favicon.gif $DIR/favicon.ico
echo \
  '<?php header("Location: http://divergloss.nedohodnik.net/doc/");?>' \
  > $DIR/index.php
touch -d $DATE $DIR/index.php
rsync -raLv --delete $DIR/ www-divergloss:divergloss.nedohodnik.net/
rm -rf $DIR
