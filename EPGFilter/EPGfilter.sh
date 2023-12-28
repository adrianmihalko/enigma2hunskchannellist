#!/bin/bash

url=("https://raw.githubusercontent.com/adrianmihalko/EPGimport-Sources/main/rytec.channels.xml")

wget -q $url -O /tmp/rytec.channels.xml

wget -q "https://raw.githubusercontent.com/adrianmihalko/enigma2hunskchannellist/main/EPGFilter/FILTERpattern.txt" -O /etc/epgimport/FILTERpattern.txt

/usr/bin/dos2unix /etc/epgimport/FILTERpattern.txt

grep -v -f "/etc/epgimport/FILTERpattern.txt" "/tmp/rytec.channels.xml" > "/etc/epgimport/filtered.channels.xml"
grep -f "/etc/epgimport/FILTERpattern.txt" "/tmp/rytec.channels.xml" > "/etc/epgimport/removed.channels.xml"

if [ -f "/etc/epgimport/rytec.sources.xml" ]; then
    cp -f "/etc/epgimport/rytec.sources.xml" "/etc/epgimport/rytec.sources.xml.org"
    mv -f /etc/epgimport/rytec.sources.xml /etc/epgimport/filtered.sources.xml
    sed -i -E 's/channels="rytec.channels.xml.xz"/channels="filtered.channels.xml"/' "/etc/epgimport/filtered.sources.xml"
fi
