# uncompyle6 version 3.8.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 3.7.3 (default, Dec 13 2019, 19:58:14) 
# [Clang 11.0.0 (clang-1100.0.33.17)]
# Embedded file name: /usr/lib/enigma2/python/Plugins/SystemPlugins/PFastScan/plugin.py
# Compiled at: 2021-09-11 21:00:23
import operator, os, urllib2, zipfile
from os import path as os_path, walk as os_walk, unlink as os_unlink
from Plugins.Plugin import PluginDescriptor
from Screens.ServiceInfo import ServiceInfoList, ServiceInfoListEntry
from ServiceReference import ServiceReference
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.config import config, ConfigSelection, ConfigYesNo, getConfigListEntry, ConfigSubsection, ConfigText
from Components.ConfigList import ConfigListScreen
from Components.NimManager import nimmanager
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ServiceList import refreshServiceList
from Components.ActionMap import ActionMap
from Screens import InfoBarGenerics
from Screens.InfoBar import InfoBar
from glob import glob
from enigma import eFastScan, eDVBFrontendParametersSatellite, eDVBDB, eComponentScan, eDVBSatelliteEquipmentControl, eDVBFrontendParametersTerrestrial, eDVBFrontendParametersCable, eConsoleAppContainer, eDVBResourceManager, eServiceReference, eServiceCenter
from Plugins.SystemPlugins.PFastScan.Scan import ServiceScan, SCANVERSION
from . import _
config.misc.pfastscan = ConfigSubsection()
config.misc.pfastscan.last_configuration = ConfigText(default='()')
PLUGINVERSION = '6.2.4'

class FastScan():

    def __init__(self, text, progressbar, scanTuner=0, transponderParameters=None, scanPid=900, keepNumbers=False, keepSettings=False, providerName='Favorites', createRadioBouquet=False):
        self.text = text
        self.progressbar = progressbar
        self.transponderParameters = transponderParameters
        self.scanPid = scanPid
        self.scanTuner = scanTuner
        self.keepNumbers = keepNumbers
        self.keepSettings = keepSettings
        self.providerName = providerName
        self.createRadioBouquet = createRadioBouquet
        self.done = False

    def execBegin(self):
        self.text.setText(_('Scanning %s...') % self.providerName)
        self.progressbar.setValue(0)
        self.scan = eFastScan(self.scanPid, self.providerName, self.transponderParameters, self.keepNumbers, self.keepSettings, self.createRadioBouquet)
        self.scan.scanCompleted.get().append(self.scanCompleted)
        self.scan.scanProgress.get().append(self.scanProgress)
        fstfile = None
        fntfile = None
        for root, dirs, files in os_walk('/tmp/'):
            for f in files:
                if f.endswith('.bin'):
                    if '_FST' in f:
                        fstfile = os_path.join(root, f)
                    elif '_FNT' in f:
                        fntfile = os_path.join(root, f)

        if fstfile and fntfile:
            self.scan.startFile(fntfile, fstfile)
            os_unlink(fstfile)
            os_unlink(fntfile)
        else:
            self.scan.start(self.scanTuner)
        return

    def execEnd(self):
        self.scan.scanCompleted.get().remove(self.scanCompleted)
        self.scan.scanProgress.get().remove(self.scanProgress)
        del self.scan

    def scanProgress(self, progress):
        self.progressbar.setValue(progress)

    def scanCompleted(self, result):
        self.done = True
        if result < 0:
            self.text.setText(_('Scanning failed!'))
        else:
            self.text.setText(_('List version: %d  Found channels: %d') % (self.scan.getVersion(), result))

    def destroy(self):
        pass

    def isDone(self):
        return self.done


class FastScanStatus(Screen):
    skin = '\n\t<screen position="150,115" size="420,180" title="Pseudo Fast Scan">\n\t\t<widget name="frontend" pixmap="icons/scan-s.png" position="5,5" size="64,64" transparent="1" alphatest="on" />\n\t\t<widget name="scan_state" position="10,120" zPosition="2" size="400,30" font="Regular;18" />\n\t\t<widget name="scan_progress" position="10,155" size="400,15" pixmap="progress_big.png" borderWidth="2" borderColor="#cccccc" />\n\t</screen>'

    def __init__(self, session, scanTuner=0, transponderParameters=None, scanPid=900, keepNumbers=False, keepSettings=False, providerName='Favorites', createRadioBouquet=False):
        Screen.__init__(self, session)
        self.setTitle(_('Pseudo Fast Scan'))
        self.scanPid = scanPid
        self.scanTuner = scanTuner
        self.transponderParameters = transponderParameters
        self.keepNumbers = keepNumbers
        self.keepSettings = keepSettings
        self.providerName = providerName
        self.createRadioBouquet = createRadioBouquet
        self['frontend'] = Pixmap()
        self['scan_progress'] = ProgressBar()
        self['scan_state'] = Label(_('scan state'))
        self.prevservice = self.session.nav.getCurrentlyPlayingServiceReference()
        self.session.nav.stopService()
        self['actions'] = ActionMap(['OkCancelActions'], {'ok': self.ok, 'cancel': self.cancel})
        self.onFirstExecBegin.append(self.doServiceScan)

    def doServiceScan(self):
        self['scan'] = FastScan(self['scan_state'], self['scan_progress'], self.scanTuner, self.transponderParameters, self.scanPid, self.keepNumbers, self.keepSettings, self.providerName, self.createRadioBouquet)

    def restoreService(self):
        if self.prevservice:
            self.session.nav.playService(self.prevservice)

    def ok(self):
        if self['scan'].isDone():
            refreshServiceList()
            self.restoreService()
            self.close()

    def cancel(self):
        self.restoreService()
        self.close()


class FastScanScreen(ConfigListScreen, Screen):
    skin = '\n\t<screen position="100,115" size="520,290" title="Pseudo Fast Scan">\n\t\t<widget name="config" position="10,10" size="500,250" scrollbarMode="showOnDemand" />\n\t\t<widget name="introduction" position="10,265" size="500,25" font="Regular;20" halign="center" />\n\t</screen>'

    def __init__(self, session, nimList, dbver):
        Screen.__init__(self, session)
        self.prevservice = self.session.nav.getCurrentlyPlayingServiceReference()
        self.setTitle(_('(P)seudo Fast Scan'))
        self.providers = {}
        thexmltxtdir = '/usr/lib/enigma2/python/Plugins/SystemPlugins/PFastScan/xml/'
        allxmlfiles = filter(lambda x: x.endswith('.xml'), os.listdir(thexmltxtdir))
        allxmlfiles = filter(lambda x: x.startswith('@'), allxmlfiles)
        for pxmlname in allxmlfiles:
            cleanfname = pxmlname.rsplit('.', 1)[0]
            if os.path.isfile(thexmltxtdir + cleanfname.lower() + '.txt'):
                if os.path.isfile(thexmltxtdir + cleanfname.lower() + '.xml'):
                    self.providers[cleanfname.title()] = (
                     0, 900, True)

        self.providers['Skylink Czech Republic'] = (
         1, 30, False)
        self.providers['Skylink Slovak Republic'] = (1, 31, False)
        self.providers['FreeSAT CZ Thor'] = (2, 82, False)
        self.providers['FreeSAT SK Thor'] = (2, 83, False)
        self.providers['FocusSAT Thor'] = (2, 84, False)
        self.providers['Direct One Thor'] = (2, 81, False)
        self.providers['Canal Digitaal Astra1'] = (0, 900, True)
        self.providers['Canal Digitaal'] = (1, 900, True)
        self.providers['TV Vlaanderen Astra1'] = (0, 910, True)
        self.providers['TV Vlaanderen'] = (1, 910, True)
        self.providers['TeleSAT'] = (0, 920, True)
        self.providers['TeleSAT Astra3'] = (1, 920, True)
        self.providers['HD Austria'] = (0, 950, False)
        self.providers['HD Austria Astra3'] = (1, 950, False)
        self.providers['Diveo'] = (0, 960, False)
        self.providers['Diveo Astra3'] = (1, 960, False)
        self.providers['KabelKiosk'] = (0, 970, False)
        self.transponders = (
         (12515000,
          22000000,
          eDVBFrontendParametersSatellite.FEC_5_6,
          192,
          eDVBFrontendParametersSatellite.Polarisation_Horizontal,
          eDVBFrontendParametersSatellite.Inversion_Unknown,
          eDVBFrontendParametersSatellite.System_DVB_S,
          eDVBFrontendParametersSatellite.Modulation_QPSK,
          eDVBFrontendParametersSatellite.RollOff_alpha_0_35,
          eDVBFrontendParametersSatellite.Pilot_Off),
         (12070000,
          27500000,
          eDVBFrontendParametersSatellite.FEC_3_4,
          235,
          eDVBFrontendParametersSatellite.Polarisation_Horizontal,
          eDVBFrontendParametersSatellite.Inversion_Unknown,
          eDVBFrontendParametersSatellite.System_DVB_S,
          eDVBFrontendParametersSatellite.Modulation_QPSK,
          eDVBFrontendParametersSatellite.RollOff_alpha_0_35,
          eDVBFrontendParametersSatellite.Pilot_Off),
         (11727000,
          28000000,
          eDVBFrontendParametersSatellite.FEC_7_8,
          3592,
          eDVBFrontendParametersSatellite.Polarisation_Vertical,
          eDVBFrontendParametersSatellite.Inversion_Unknown,
          eDVBFrontendParametersSatellite.System_DVB_S,
          eDVBFrontendParametersSatellite.Modulation_QPSK,
          eDVBFrontendParametersSatellite.RollOff_alpha_0_35,
          eDVBFrontendParametersSatellite.Pilot_Off))
        self.session.postScanService = session.nav.getCurrentlyPlayingServiceOrGroup()
        self['actions'] = ActionMap(['SetupActions', 'MenuActions'], {'ok': self.keyGo, 'save': self.keyGo, 
           'cancel': self.keyCancel, 
           'menu': self.closeRecursive}, -2)
        providerList = list(x[0] for x in sorted(self.providers.iteritems(), key=operator.itemgetter(0)))
        lastConfiguration = eval(config.misc.pfastscan.last_configuration.value)
        if not lastConfiguration:
            lastConfiguration = (
             nimList[0][0],
             providerList[0],
             True,
             False,
             False,
             True)
        self.scan_nims = ConfigSelection(default=lastConfiguration[0], choices=nimList)
        self.scan_provider = ConfigSelection(default=lastConfiguration[1], choices=providerList)
        self.scan_hd = ConfigYesNo(default=lastConfiguration[2])
        self.scan_keepnumbering = ConfigYesNo(default=lastConfiguration[3])
        self.scan_keepsettings = ConfigYesNo(default=lastConfiguration[4])
        self.scan_createRadioBouquet = ConfigYesNo(default=lastConfiguration[5])
        self.list = []
        self.tunerEntry = getConfigListEntry(_('Tuner'), self.scan_nims)
        self.list.append(self.tunerEntry)
        self.scanProvider = getConfigListEntry(_('Provider'), self.scan_provider)
        self.list.append(self.scanProvider)
        self.scanHD = getConfigListEntry(_('HD list'), self.scan_hd)
        self.list.append(self.scanHD)
        self.list.append(getConfigListEntry(_('Use fastscan channel numbering'), self.scan_keepnumbering))
        self.list.append(getConfigListEntry(_('Use fastscan channel names'), self.scan_keepsettings))
        self.list.append(getConfigListEntry(_('Create seperate radio userbouquet'), self.scan_createRadioBouquet))
        self.list.append(getConfigListEntry(''))
        self.list.append(getConfigListEntry(_('Version') + ' DB:  ' + dbver))
        self.list.append(getConfigListEntry(_('Version') + ' Plugin:  ' + PLUGINVERSION))
        self.list.append(getConfigListEntry(_('Version') + ' Scan:  ' + SCANVERSION))
        ConfigListScreen.__init__(self, self.list)
        self['config'].list = self.list
        self['config'].l.setList(self.list)
        self.finished_cb = None
        self['introduction'] = Label(_('Select your provider and press OK to start the scan'))
        return

    def addSatTransponder(self, tlist, frequency, symbol_rate, polarisation, fec, inversion, orbital_position, system, modulation, rolloff, pilot, is_id, pls_mode, pls_code):
        parm = eDVBFrontendParametersSatellite()
        parm.modulation = modulation
        parm.system = system
        parm.frequency = frequency * 1000
        parm.symbol_rate = symbol_rate * 1000
        parm.polarisation = polarisation
        parm.fec = fec
        parm.inversion = inversion
        parm.orbital_position = orbital_position
        parm.rolloff = rolloff
        parm.pilot = pilot
        parm.is_id = is_id
        parm.pls_mode = pls_mode
        parm.pls_code = pls_code
        tlist.append(parm)

    def restoreService(self):
        if self.prevservice:
            self.session.nav.playService(self.prevservice)

    def readXML(self, xml):
        global ret
        ret = [
         '#NAME Bouquets (TV)\n']
        self.session.nav.stopService()
        tlist = []
        eDVBDB.getInstance().reloadBouquets()
        lastscannedfname = '/etc/enigma2/userbouquet.LastScanned.tv'
        bouquetstvfname = '/etc/enigma2/bouquets.tv'
        lastscannedline = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.LastScanned.tv" ORDER BY bouquet'
        if os.path.isfile(bouquetstvfname):
            bouqtv1r = open(bouquetstvfname, 'r')
            ret = bouqtv1r.read().split('\n')
            bouqtv1r.close()
            if lastscannedline in ret:
                nb1index = ret.index(lastscannedline)
                ret.pop(nb1index)
        ls1w = open(lastscannedfname, 'w')
        ls1w.write('#NAME Last Scanned\n')
        ls1w.close()
        nb1list = [lastscannedline]
        nb1list.extend(ret)
        bouqtv1w = open(bouquetstvfname, 'w')
        bouqtv1w.write(('\n').join(map(lambda x: str(x), nb1list)))
        bouqtv1w.close()
        eDVBDB.getInstance().reloadBouquets()
        import xml.dom.minidom as minidom
        try:
            xmldoc = '/usr/lib/enigma2/python/Plugins/SystemPlugins/PFastScan/xml/' + xml + '.xml'
            xmldoc = minidom.parse(xmldoc)
            transp_list = xmldoc.getElementsByTagName('transponder')
            for single_transp in transp_list:
                orbpos = single_transp.getAttribute('orbpos')
                frequency = single_transp.getAttribute('frequency')
                symbolrate = single_transp.getAttribute('symbolrate')
                fec = single_transp.getAttribute('fec')
                pol = single_transp.getAttribute('pol')
                system = single_transp.getAttribute('system')
                modulation = single_transp.getAttribute('modulation')
                self.frequency = frequency
                self.symbolrate = symbolrate
                if pol == 'H':
                    pol = 0
                elif pol == 'V':
                    pol = 1
                elif pol == 'L':
                    pol = 2
                elif pol == 'R':
                    pol = 3
                self.polarization = pol
                if fec == 'Auto':
                    fec = 0
                elif fec == '1/2':
                    fec = 1
                elif fec == '2/3':
                    fec = 2
                elif fec == '3/4':
                    fec = 3
                elif fec == '5/6':
                    fec = 4
                elif fec == '7/8':
                    fec = 5
                elif fec == '8/9':
                    fec = 6
                elif fec == '3/5':
                    fec = 7
                elif fec == '4/5':
                    fec = 8
                elif fec == '9/10':
                    fec = 9
                self.fec = fec
                self.inversion = 2
                self.orbpos = orbpos
                if system == 'DVBS':
                    system = 0
                elif system == 'DVBS2':
                    system = 1
                self.system = system
                if modulation == 'QPSK':
                    modulation = 1
                elif modulation == '8PSK':
                    modulation = 2
                self.modulation = modulation
                self.rolloff = 0
                self.pilot = 2
                self.addSatTransponder(tlist, int(self.frequency), int(self.symbolrate), int(self.polarization), int(fec), int(self.inversion), int(orbpos), int(self.system), int(self.modulation), int(self.rolloff), int(self.pilot), eDVBFrontendParametersSatellite.No_Stream_Id_Filter, eDVBFrontendParametersSatellite.PLS_Gold, 0)

            self.session.openWithCallback(self.bouqmake, ServiceScan, [
             {'transponders': tlist, 'feid': int(self.scan_nims.value), 
                'flags': 0, 
                'networkid': 0}])
        except:
            self.session.open(MessageBox, xml + _('.xml file is missing!'), MessageBox.TYPE_ERROR)

    def bouqmake(self, session):
        prov = self.scan_provider.value.replace(' ', '')
        lastscannedfname = '/etc/enigma2/userbouquet.LastScanned.tv'
        newbouqfname = '/etc/enigma2/userbouquet.' + prov + '.tv'
        bouquetstvfname = '/etc/enigma2/bouquets.tv'
        newbouqLine = '#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.' + prov + '.tv" ORDER BY bouquet\r'
        newbouqName = '#NAME ' + self.scan_provider.value + '\r'
        newbouqFnameonly = '"userbouquet.' + prov + '.tv"'
        try:
            txtdocfname = '/usr/lib/enigma2/python/Plugins/SystemPlugins/PFastScan/xml/' + self.scan_provider.value.lower() + '.txt'
            txtdocfile = open(txtdocfname, 'r')
            txt_channel_list = txtdocfile.read().split('\n')
            txtdocfile.close()
            tmp_array = []
            array_channel_list = []
            for txt_channel_line in txt_channel_list:
                if txt_channel_line.count('|') == 2:
                    tmp_array = txt_channel_line.split('|')
                    array_channel_list.append(tmp_array[2].rstrip())
                else:
                    array_channel_list.append(txt_channel_line.rstrip())

            lsr = open(lastscannedfname, 'r')
            lastscanned_raw = lsr.read().split('\n')
            lsr.close()
            i = 1
            list_chnl_final = [newbouqName]
            list_chnl_srvid = [newbouqName]
            if lastscanned_raw[1].startswith('#SERVICE'):
                while i + 1 < len(lastscanned_raw):
                    self.updateServiceName(int(i))
                    if sname.rstrip() in array_channel_list:
                        list_chnl_srvid.append(sname.rstrip() + ' ' + lastscanned_raw[i])
                    i += 1

                for txt_channel_line_raw in txt_channel_list:
                    for s in list_chnl_srvid:
                        line_chnl_srvid = s.rsplit('#', 1)
                        channel_name = line_chnl_srvid[0].rstrip()
                        if txt_channel_line_raw.count('|') == 2:
                            tmp_array = txt_channel_line_raw.split('|')
                            purename = tmp_array[2]
                            pureseek = tmp_array[1]
                        else:
                            purename = txt_channel_line_raw
                            pureseek = ''
                        if channel_name == purename.rstrip():
                            s1 = '#' + line_chnl_srvid[1]
                            if s1.startswith('#SERVICE'):
                                if pureseek != '':
                                    if s1.count(pureseek) == 1:
                                        list_chnl_final.append(s1)
                                else:
                                    list_chnl_final.append(s1)

                nbw = open(newbouqfname, 'w')
                nbw.write(('\n').join(map(lambda x: str(x), list_chnl_final)))
                nbw.write('\n')
                nbw.close()
                rety = []
                for bqt in ret:
                    if newbouqFnameonly in bqt:
                        print _('No service added')
                    else:
                        rety.append(bqt)

                rety[1:1] = [
                 newbouqLine]
                flw = open(bouquetstvfname, 'w')
                flw.write(('\n').join(map(lambda x: str(x), rety)))
                flw.close()
                eDVBDB.getInstance().reloadBouquets()
            else:
                flw = open(bouquetstvfname, 'w')
                flw.write(('\n').join(map(lambda x: str(x), ret)))
                flw.close()
                eDVBDB.getInstance().reloadBouquets()
                self.keyCancel()
        except:
            self.session.open(MessageBox, _('Error, value in ') + self.scan_provider.value.lower() + _('.txt file not found'), MessageBox.TYPE_ERROR)

    def searchNumberHelper(self, serviceHandler, num, bouquet):
        servicelist = self.serviceHandler.list(bouquet)
        if servicelist is not None:
            while num:
                serviceIterator = servicelist.getNext()
                if not serviceIterator.valid():
                    break
                playable = not serviceIterator.flags & (eServiceReference.isMarker | eServiceReference.isDirectory)
                if playable:
                    num -= 1

            if not num:
                return (serviceIterator, 0)
        return (
         None, num)

    def updateServiceName(self, number):
        global sname
        bouquet = InfoBar.instance.servicelist.bouquet_root
        service = None
        self.serviceHandler = eServiceCenter.getInstance()
        serviceHandler = self.serviceHandler
        bouquetlist = serviceHandler.list(bouquet)
        if bouquetlist is not None:
            while number:
                bouquet = bouquetlist.getNext()
                if not bouquet.valid():
                    break
                if bouquet.flags & eServiceReference.isDirectory:
                    service, number = self.searchNumberHelper(serviceHandler, number, bouquet)

        if service is not None:
            info = serviceHandler.info(service)
            sname = info.getName(service).replace('\x86', '').replace('\x87', '')
        else:
            sname = _('Unknown service')
        return

    def keyGo(self):
        prov = self.scan_provider.value.lower()
        if prov.startswith('@'):
            config.misc.pfastscan.last_configuration.value = `(
             self.scan_nims.value,
             self.scan_provider.value,
             self.scan_hd.value,
             self.scan_keepnumbering.value,
             self.scan_keepsettings.value,
             self.scan_createRadioBouquet.value)`
            config.misc.pfastscan.save()
            self.readXML(self.scan_provider.value.lower())
        else:
            config.misc.pfastscan.last_configuration.value = `(
             self.scan_nims.value,
             self.scan_provider.value,
             self.scan_hd.value,
             self.scan_keepnumbering.value,
             self.scan_keepsettings.value,
             self.scan_createRadioBouquet.value)`
            config.misc.pfastscan.save()
            self.startScan()

    def getTransponderParameters(self, number):
        transponderParameters = eDVBFrontendParametersSatellite()
        transponderParameters.frequency = self.transponders[number][0]
        transponderParameters.symbol_rate = self.transponders[number][1]
        transponderParameters.fec = self.transponders[number][2]
        transponderParameters.orbital_position = self.transponders[number][3]
        transponderParameters.polarisation = self.transponders[number][4]
        transponderParameters.inversion = self.transponders[number][5]
        transponderParameters.system = self.transponders[number][6]
        transponderParameters.modulation = self.transponders[number][7]
        transponderParameters.rolloff = self.transponders[number][8]
        transponderParameters.pilot = self.transponders[number][9]
        transponderParameters.is_id = eDVBFrontendParametersSatellite.No_Stream_Id_Filter
        transponderParameters.pls_mode = eDVBFrontendParametersSatellite.PLS_Gold
        transponderParameters.pls_code = 0
        return transponderParameters

    def startScan(self):
        pid = self.providers[self.scan_provider.value][1]
        if self.scan_hd.value and self.providers[self.scan_provider.value][2]:
            pid += 1
        if self.scan_nims.value:
            self.session.open(FastScanStatus, scanTuner=int(self.scan_nims.value), transponderParameters=self.getTransponderParameters(self.providers[self.scan_provider.value][0]), scanPid=pid, keepNumbers=self.scan_keepnumbering.value, keepSettings=self.scan_keepsettings.value, providerName=self.scan_provider.getText(), createRadioBouquet=self.scan_createRadioBouquet.value)

    def keyCancel(self):
        self.restoreService()
        self.close()


def FastScanMain(session, **kwargs):
    SRVVER = 'https://www.dropbox.com/s/elxrh53j5pbrnm7/serverversion.txt?dl=1'
    SRVSOFT = 'https://www.dropbox.com/s/1ilfmk729nef8x3/serversoftware.zip?dl=1'
    DBVERSION = ''
    DBVERSIONSRV = ''
    OFFLINE = ''
    forceupdate = False
    needrestart = False
    tmpzipfilename = '/tmp/pseudofastscanupdate.zip'
    extractallto = '/usr/lib/enigma2/python/Plugins/SystemPlugins/PFastScan/'
    deletelistfile = extractallto + 'deletefile.txt'
    try:
        dbverfilename = extractallto + 'dbversion.txt'
        dbverfile = open(dbverfilename, 'r')
        vertext = dbverfile.read()
        dbverfile.close()
        if len(vertext) == 8 and vertext.isdigit:
            DBVERSION = str(vertext)
    except:
        pass

    if os.path.isfile('/usr/lib/enigma2/python/Plugins/SystemPlugins/PFastScan/offline'):
        OFFLINE = ' OFFLINE'
    if len(OFFLINE) == 0:
        try:
            responsevers = urllib2.urlopen(SRVVER, timeout=2)
            serververs = responsevers.read()
            responsevers.close()
            if len(serververs) == 8 and serververs.isdigit:
                DBVERSIONSRV = str(serververs)
            if DBVERSIONSRV > DBVERSION:
                forceupdate = True
        except:
            pass

    if forceupdate:
        try:
            responsesoft = urllib2.urlopen(SRVSOFT, timeout=2)
            serversoft = responsesoft.read()
            responsesoft.close()
            zipsoft = open(tmpzipfilename, 'w')
            zipsoft.write(serversoft)
            zipsoft.close()
            zip_ref = zipfile.ZipFile(tmpzipfilename, 'r')
            zip_ref.extractall(extractallto)
            zip_ref.close()
            if os.path.exists(tmpzipfilename):
                os.remove(tmpzipfilename)
            if os.path.exists(deletelistfile):
                with open(deletelistfile) as (dlfle):
                    delcontent = dlfle.read().splitlines()
                for item in delcontent:
                    if item.strip()[:1] == '.' or item.strip()[:1] == '\\' or item.strip()[:1] == '/' or len(item.strip()) == 0:
                        pass
                    elif os.path.exists(extractallto + item):
                        os.remove(extractallto + item)

            DBVERSION = DBVERSIONSRV
            needrestart = True
        except:
            pass

    restarttext = ''
    readmetext = _('Pseudo Fast Scan') + '\n\n'
    messagewait = 10
    if needrestart:
        restarttext = _('Pseudo Fast Scan has been updated!!!') + '\n' + _('PLEASE RESTART ENIGMA2 BOX!!!') + '\n\n'
        messagewait = 15
    try:
        readmetxtfilename = extractallto + 'readme.txt'
        readmetxt = open(readmetxtfilename, 'r')
        readmetext = readmetxt.read()
        readmetxt.close()
    except:
        pass

    session.open(MessageBox, _(restarttext + readmetext), MessageBox.TYPE_INFO, messagewait)
    if session.nav.RecordTimer.isRecording():
        session.open(MessageBox, _('A recording is currently running. Please stop the recording before trying to scan.'), MessageBox.TYPE_ERROR)
    else:
        nimList = []
        try:
            for n in nimmanager.nim_slots:
                if not n.isCompatible('DVB-S'):
                    continue
                if n.config.dvbs.configMode == 'nothing':
                    continue
                if n.config.dvbs.configMode in ('loopthrough', 'satposdepends'):
                    root_id = nimmanager.sec.getRoot(n.slot_id, int(n.config.dvbs.connectedTo.value))
                    if n.type == nimmanager.nim_slots[root_id].type:
                        continue
                nimList.append((str(n.slot), n.friendly_full_description))

        except:
            for n in nimmanager.nim_slots:
                if not n.isCompatible('DVB-S'):
                    continue
                if n.config_mode == 'nothing':
                    continue
                if n.config_mode in ('loopthrough', 'satposdepends'):
                    root_id = nimmanager.sec.getRoot(n.slot_id, int(n.config.connectedTo.value))
                    if n.type == nimmanager.nim_slots[root_id].type:
                        continue
                nimList.append((str(n.slot), n.friendly_full_description))

        if nimList:
            session.open(FastScanScreen, nimList, DBVERSION + OFFLINE)
        else:
            session.open(MessageBox, _('No suitable sat tuner found!'), MessageBox.TYPE_ERROR)


Session = None

def FastScanStart(menuid, **kwargs):
    from Components.About import about
    if menuid == 'scan':
        return [
         (_('Pseudo Fast Scan'),
          FastScanMain,
          'pseudofastscan',
          None)]
    else:
        return []
        return


def Plugins(**kwargs):
    if nimmanager.hasNimType('DVB-S'):
        return PluginDescriptor(name=_('Pseudo Fast Scan'), description=_('Scan different sat provider'), where=PluginDescriptor.WHERE_MENU, fnc=FastScanStart)
    else:
        return []
# okay decompiling plugin.pyo
