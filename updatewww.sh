#!/bin/sh

mkdir tmpwww
ln -s ../doc/html tmpwww/doc
touch -d 2010-12-06 tmpwww/favicon.gif tmpwww/favicon.ico
echo '<?php header("Location: http://divergloss.nedohodnik.net/doc/");?>' > tmpwww/index.php
touch -d 2010-12-06 tmpwww/index.php
rsync -raLv --delete tmpwww/ www-divergloss:divergloss.nedohodnik.net/
rm -rf tmpwww
