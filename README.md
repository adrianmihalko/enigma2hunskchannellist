# enigma2hunskchannellist
DirectOne (UPC, Freesat) csatornalista

Célom egy friss csatornalista létrehozása 0.8W fokon Digi és DirectOne (Freesat, UPC) szolgáltatókhoz, amely teljes mértékben kompatibilis az EPGImport és Rytec forrásokkal, mindenféle állítgatás nélkül.

Miért?

Az EPGImport segítségével részletes EPG-t tudunk letölteni 5 napra előre, minden csatornához, automatikusan. Sokszor előfordult velem, hogy az automatikus felvételeim nem indultak el amikor pár napig nem néztük a TV-t, ezért a friss EPG nem tudott letöltődni (ahhoz ugyanis kapcsolgatni kéne a csatornák közt, alvó módban nem működik).

A lista aktualizálását nem a hagyományos bouquetek megosztásával fog történni (ami felülírná az aktuális bouquet gyűjteményedet), nyugodtan maradhatnak a mostani listáid/beállításaid.

Ehhez a projekthez Pseudo Fast Scan plugint használom, ami két fájlt használ egy adott bouquet létrehozásához:

- @bouquet neve.txt
- @bouquet neve.xml

A .txt fájlban vannak a csatornák nevei elrendezési sorrendben, az .xml-ben pedig a lekeresendő transzponderek.

Hogy jövök én ide?

Alapból a plugin, igaz, hogy tartalmazza a DirectOne (Freesat, UPC) szolgáltatót, de nem túl összeszedett módon. 

Amit én hozzáadtam:

- Digi HU - teljes magyar csomag, a szolgáltató elrendezése alapján
- DirectOne HU (@directone hungary upc) - teljes magyar és szlovák csomag:
    - http://musor.tv kategóriák alapján rendezve 
    - HD csatornák elöl, SD csatornák utána
    - Magyar csatornák elöl, szlovák csatornák alul
- Kombinált lista (@hungary slovakia combined) - a kedvencem. Digi és DirectOne csatornák összefésülve. DirectOne hangsúlyos, tehát csak azok a Digi csatornák lettek hozzáadva, amik a DirectOne-nél nem szerepelnek.

A .txt listát kedvedre szerkesztheted, törölheted (pl. 18+ csatornák), mozgathatod a sorokat a végső bouquet ez alapján a fájl alapján lesz generálva.

## Követelmények:

- OpenPli - az EPG importálás miatt (nem próbáltam más image alatt)
- [Pseudo Fast Scan](http://www.ab-forum.info/viewtopic.php?f=468&t=76382) - kompatibilitást lásd a posztban

## Használat:

Sajnos a Pseudo Fast Scan pluginban találtam egy olyan hibát, hogy a fájlnevet amit alapból használ "(p)csatornalista.txt" a zárójel miatt az OpenPli nem szereti. Konkrétan nem lehet a bouquetet szerkeszteni a boxon (csatornát mozgatni, törölni, stb.). Egy kis módosítás után én a "@" fájlnevet használom és minden működik, ahogy kell. Próbáltam elérni a plugin gazdáját, sajnos még nem válaszolt. Addig is módosítanunk kell majd magát a plugint.

1. Telepítsük a Pseudo Fast Scan plugin
2. Navigáljunk el ide a plugin mappájába:
`/usr/lib/enigma2/python/Plugins/SystemPlugins/PFastScan` 
3. plugin.pyo ha létezik töröljük, ez a következő újraindítás után újra létrejön
4. hozzunk létre egy üres **offline** nevű fájlt, így a plugin nem frissül majd automatikusan
5. Másoljuk innen az oldalról a **PFastScan** mappából a **plugin.py** fájlt a fent nevezett mappába
6. Másoljuk innen az oldalról a **PFastScan/xml** mappából a fájlokat az xml mappába.

Most már csak le kell keresnünk az kívánt csatornalistát. 

`Menu - Beállítások - Tunerek és keresés - Pseudo Fast Scan`

[[screenshot/pseudofastscansettings.jpg|PSEUDOFASTSCAN]]

Válasszuk ki a listát amit szeretnénk (@-al kezdődik) majd nyomjunk egy OK-t.

## EPG importálás beállítása

Telepítsük az EPGImport és EPGImport Rytec csomagokat.

[[screenshot/epgimportsettings.jpg|EPGIMPORT]]

Ezeket a forrásokat engedélyezzük:

- Rytec General XMLTV
    - News Channels (xz)
    - Erotic (xz)
    - Miscallaneous XMLTV (xz)
- Rytec Ceska/Slovensko XMLTV
    - Slovensko - Bazicky (xz)
    - Ceska - Bazicky (xz)
    - Ceska/Slovensko - Rozdeleny (xz)
    - Ceska/Slovensko - Sportove/Filmy (xz)
  - Rytec Magyarorszag XMLTV
    - Magyarorszag - Basic (xz)
    - Magyarorszag - Sport/Film (xz)
  - Rytec Romania XMLTV
    - Romania Baza (xz)

Sajnos, sok csatornának ugyan az a szolgáltatói azonosítója, ezért ki kell szűrnünk azokat, amiket nem szeretnénk.

Ehhez az **EPGfilter.sh** szkriptet fogjuk használni

Másoljuk az EPGfilter mappából a fájlokat az `/etc/epgimport/` mappába. Engedélyezzük a futtatását `chmod +x /etc/EPGfilter.sh` paranccsal. 

Futtasuk is le, ezután létre kell jönniük az alábbi fájloknak:

- filtered.channels.xml (módosított/szűrt csatornalista)
- filtered.sources.xml (módosított sources fájl)
- removed.channels.xml (eltávolított csatornák, ellenőrizzük nem üres -e)
- rytec.sources.xml.org (eredeti sources fájl)

Az **FILTERpattern.txt** fájl tartalmazza azokat a csatornákat, amiket nem szeretnénk, hogy az EPGImport importáljon.

Az EPGImportban futtassunk le egy manuális importálást (sárga gomb) és ellenőrizzük, hogy rendben van -e minden.
