#!/usr/local/bin/python
#
# Script to analyse prtdiag output in explorers for errors
# This also does a lot of non prtdiag analysis for general hardware detection
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: prtdiag.py 3037 2012-10-01 07:23:07Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/prtdiag.py $

# To add a new host you will need to
#  a) add a line to Prtdiag.parse() to detect it from the first line in prtdiag output
#  b) create a function to analyse the contents - see others for examples

import os
import sys
import getopt
import re
sys.path.append('/app/explorer/lib/python/site-packages')
import explorerbase
import drivemap
import cardmap
import hostdet

verbflag = False


##########################################################################
# IoCard #################################################################
##########################################################################
class IoCard(explorerbase.ExplorerBase):
    ##########################################################################
    def __init__(self, config, **kwargs):
        explorerbase.ExplorerBase.__init__(self, config)
        for arg, val in kwargs.items():
            try:
                self[arg] = val.strip()
            except AttributeError:
                self[arg] = val

        if 'combo' in self:
            pass
        else:
            if 'rawmodel' in self:
                self.cardDetails(self['rawmodel'])
            else:
                self['iocard'] = "unknown"

    ##########################################################################
    def __repr__(self):
        return "<IoCard: %s>" % self['iocard']

    ##########################################################################
    def analyse(self):
        pass

    ##########################################################################
    def cardDetails(self, model):
        if model == '':
            return ''
        if model == 'isa':
            # Has to be here as isa matches too many things
            self['fake'] = True
            return True
        for m in cardmap.cards:
            if m in model:
                if 'fake' in cardmap.cards[m] and cardmap.cards[m]['fake']:
                    self['fake'] = True
                    return True
                self['iocard'] = cardmap.cards[m]['iocard']
                self['cardabbrev'] = m
                desc = cardmap.cards[m].get('desc', self['iocard'])
                qty = cardmap.cards[m].get('qty', 1)
                optn = cardmap.cards[m].get('option', "Undefined Option")
                part = cardmap.cards[m].get('part', "Undefined Part")
                self.addPart(
                    desc=desc, qty=qty, option=optn, part=part, component='card')
                return True
        self.Fatal("cardName() Unknown card >%s<" % model)
        self['iocard'] = "unknown_%s" % model
        return False


##########################################################################
# Prtdiag ################################################################
##########################################################################
class Prtdiag(explorerbase.ExplorerBase):

    ######################################################################
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.badmode = False
        self.buffer = []
        self.foundCpu = False     # These are a primitive coverage check
        self.foundMem = False
        self.foundIo = False
        self.tmpissue = ''
        self['numslots'] = -1
        try:
            self.parse()
            self.removeFalseCards()
            self.aggregateCombos()
            self.getDriveHardware()
            self.inheritParts()
            if not self.foundCpu:
                self.Warning("Didn't find CPU")
            if not self.foundMem:
                self.Warning("Didn't find Memory")
            if not self.foundIo:
                self.Warning("Didn't find IO Cards")
        except UserWarning, err:
            self.Warning(err)

    ##########################################################################
    def parseLinux(self, hardware):
        try:
            self.parseLinux_dmidecode()
        except UserWarning, err:
            pass
        try:
            self.parseLinux_hardwarepy(self.parseLinux_hardwarepy_chunk)
        except UserWarning, err:
            pass
        try:
            self.parseLinux_scsi()
        except UserWarning, err:
            pass
        try:
            self.parseLinux_ide()
        except UserWarning, err:
            pass
        try:
            self.parseLinux_lspci()
        except UserWarning, err:
            pass

        self.pciCards(hardware)

    ##########################################################################
    def pciCards(self, hardware):
        pass

    ##########################################################################
    pcidb = {
        # 0e11 = Compaq
        '0e11:a0f0': {'desc': ''},
        '0e11:a0f7': {'desc': 'PCI Hotplug Controller'},
        '0e11:ae32': {'desc': ''},
        '0e11:b178': {'desc': 'SMART2 Array Controller'},
        '0e11:b203': {'desc': 'Integrated Lights Out Processor'},
        '0e11:b204': {'desc': 'Integrated Lights Out Processor'},
        # 1000=LSI logic
        '1000:0010': {'desc': ''},
        '1000:0020': {'desc': ''},
        '1000:0030': {'desc': 'PCI-X to Ultra320 SCSI Controller'},
        '1000:0050': {'desc': 'PCI-X Fusion-MPT SAS'},
        # 1002=ATI Radeon
        '1002:4752': {'desc': 'ATI On-Board VGA'},
        '1002:4756': {'desc': ''},
        '1002:5159': {'desc': 'Radeon 7000'},
        '1002:515e': {'desc': 'ES1000 Display controller/VGA compatible controller'},
        # 1014=IBM
        '1014:010f': {'desc': ''},
        '1014:01a7': {'desc': 'PCI-X Bridge', 'fake': True},
        '1014:0302': {'desc': ''},
        # 1022=AMD
        '1022:1100': {'desc': 'K8 [Athlon64/Opteron] HyperTransport Technology Configuration', 'fake': True},
        '1022:1101': {'desc': 'K8 [Athlon64/Opteron] Address Map', 'fake': True},
        '1022:1102': {'desc': 'K8 [Athlon64/Opteron] DRAM Controller', 'fake': True},
        '1022:1103': {'desc': 'K8 [Athlon64/Opteron] Miscellaneous Control', 'fake': True},
        '1022:1200': {'desc': 'K10 [Opteron, Athlon64, Sempron] HyperTransport Configuration', 'fake': True},
        '1022:1201': {'desc': 'K10 [Opteron, Athlon64, Sempron] Address Map', 'fake': True},
        '1022:1202': {'desc': 'K10 [Opteron, Athlon64, Sempron] DRAM Controller', 'fake': True},
        '1022:1203': {'desc': 'K10 [Opteron, Athlon64, Sempron] Miscellaneous Control', 'fake': True},
        '1022:1204': {'desc': 'K10 [Opteron, Athlon64, Sempron] Link Control', 'fake': True},
        '1022:2000': {'desc': ''},
        '1022:7450': {'desc': 'PCI-X Bridge', 'fake': True},
        '1022:7451': {'desc': 'PCI_X IOAPIC'},
        '1022:7458': {'desc': 'PCI-X Bridge', 'fake': True},
        '1022:7459': {'desc': 'PCI-X IOAPIC'},
        '1022:7460': {'desc': ''},
        '1022:7464': {'desc': 'USB?'},
        '1022:7468': {'desc': ''},
        '1022:7469': {'desc': 'IDE?'},
        '1022:746a': {'desc': ''},
        '1022:746b': {'desc': ''},
        # 103c
        '103c:3300': {'desc': ''},
        '103c:3302': {'desc': ''},
        # 1033=NEC
        '1033:0035': {'desc': 'USB?'},
        '1033:00e0': {'desc': 'USB2.0?'},
        # 105a
        '105a:3376': {'desc': ''},
        # 1077=QLogic
        '1077:2312': {'desc': 'ISP2312 2Gb Fibre Channel to PIC-X HBA'},
        '1077:2422': {'desc': 'ISP2422 4Gb Fibre Cahnnel to PCI-X HBA'},
        '1077:2432': {'desc': 'ISP2432 4Gb Fibre Channel to PCI Express HBA'},
        # 1095
        '1095:0649': {'desc': ''},
        # 10de=nVidia
        '10de:0051': {'desc': 'CK804 ISA Bridge'},
        '10de:0052': {'desc': 'CK804 SMBus'},
        '10de:0053': {'desc': 'CK804 IDE'},
        '10de:005a': {'desc': ''},
        '10de:005b': {'desc': ''},
        '10de:005c': {'desc': ''},
        '10de:005e': {'desc': ''},
        '10de:00ce': {'desc': ''},
        '10de:00d3': {'desc': ''},
        '10de:00f8': {'desc': ''},
        '10de:00fe': {'desc': ''},
        '10de:0110': {'desc': ''},
        '10de:0258': {'desc': ''},
        '10de:029e': {'desc': ''},
        '10de:0361': {'desc': ''},
        '10de:0364': {'desc': ''},
        '10de:0368': {'desc': ''},
        '10de:0369': {'desc': ''},
        '10de:036c': {'desc': ''},
        '10de:036d': {'desc': ''},
        '10de:0370': {'desc': ''},
        '10de:0373': {'desc': ''},
        '10de:037f': {'desc': ''},
        '10de:2550': {'desc': ''},
        '10de:2551': {'desc': ''},
        '10de:2552': {'desc': ''},
        '10de:2553': {'desc': ''},
        '10de:2554': {'desc': ''},
        # 10df=Emulex
        '10df:fc00': {'desc': ''},
        '10df:fc10': {'desc': ''},
        # 1106
        '1106:0571': {'desc': ''},
        '1106:0686': {'desc': ''},
        '1106:0691': {'desc': ''},
        '1106:3038': {'desc': ''},
        '1106:3057': {'desc': ''},
        '1106:3059': {'desc': ''},
        '1106:3104': {'desc': ''},
        '1106:3189': {'desc': ''},
        # 111d=Integrated Device Technology
        '111d:8018': {'desc': 'PCI Express Switch'},
        '111d:801c': {'desc': 'PCI Express Switch'},
        # 1166 = Broadcom
        '1166:0000': {'desc': 'CMIC-WS Host Bridge', 'fake': True},
        '1166:0009': {'desc': ''},
        '1166:0012': {'desc': 'Broadcom CMIC-LE'},
        '1166:0014': {'desc': 'Broadcom Host Bridge'},
        '1166:0017': {'desc': ''},
        '1166:0036': {'desc': ''},
        '1166:0101': {'desc': 'Broadcom CIOB-X2'},
        '1166:0103': {'desc': 'Broadcom EPB PCI-Express to PCI-X Bridge'},
        '1166:0142': {'desc': ''},
        '1166:0144': {'desc': ''},
        '1166:0201': {'desc': 'Broadcom ISA Bridge'},
        '1166:0203': {'desc': 'Broadcom PCI to ISA Bridge'},
        '1166:0205': {'desc': ''},
        '1166:0212': {'desc': 'Broadcom IDE Interface'},
        '1166:0213': {'desc': 'Broadcom EIDE Controller'},
        '1166:0214': {'desc': ''},
        '1166:0220': {'desc': 'Broadcom OpenHCI Compliant USB Controller'},
        '1166:0221': {'desc': 'Broadcom HCI Compliant USB Controller'},
        '1166:0223': {'desc': ''},
        '1166:0225': {'desc': 'Broadcom PCI Bridge'},
        '1166:0227': {'desc': 'Broadcom PCI Bridge'},
        '1166:0234': {'desc': ''},
        # 14e4 also Broadcom
        '14e4:1648': {'desc': 'NetXtreme Dual Gigabit Adapter'},
        '14e4:164a': {'desc': ''},
        '14e4:164c': {'desc': ''},
        '14e4:1659': {'desc': 'NetXtreme Gigabit Ethernet PCI Express'},
        '14e4:16a6': {'desc': ''},
        '14e4:16a7': {'desc': 'Gigabit Ethernet'},
        '14e4:16a8': {'desc': 'NetXtreme Gigabit Ethernet'},
        '14e4:16ac': {'desc': 'Broadcom Corporation NetXtreme II BCM5708S Gigabit Ethernet'},
        # 15ad = VMWare
        '15ad:0405': {'desc': ''},
        # 1a03 = ASpeed
        '1a03:2000': {'desc': ''},
        # 8086 = Intel
        '8086:0326': {'desc': 'APIC Interrupt Controller A', 'fake': True},
        '8086:0327': {'desc': 'APIC Interrupt Controller B', 'fake': True},
        '8086:0329': {'desc': 'PCI Express-to-PCI Bridge A', 'fake': True},
        '8086:0329': {'desc': 'PCI Express-to-PCI Bridge B', 'fake': True},
        '8086:032a': {'desc': 'PCI Express-to-PCI Bridge B', 'fake': True},
        '8086:0330': {'desc': 'I/O Processor (A-Segment Bridge)', 'fake': True},
        '8086:0332': {'desc': ''},
        '8086:0960': {'desc': ''},
        '8086:100f': {'desc': ''},
        '8086:1010': {'desc': '82545EB Gigabit Ethernet Controller (Copper)'},
        '8086:1026': {'desc': '82545GM Gigabit Ethernet Controller'},
        '8086:1028': {'desc': '82545GM Gigabit Ethernet Controller'},
        '8086:105e': {'desc': ''},
        '8086:1076': {'desc': '82541GI Gigabit Ethernet Controller'},
        '8086:1079': {'desc': ''},
        '8086:107b': {'desc': ''},
        '8086:10bc': {'desc': ''},
        '8086:1229': {'desc': ''},
        '8086:1960': {'desc': ''},
        '8086:1a38': {'desc': ''},
        '8086:244e': {'desc': ''},
        '8086:24d0': {'desc': ''},
        '8086:24d2': {'desc': ''},
        '8086:24d3': {'desc': ''},
        '8086:24d4': {'desc': ''},
        '8086:24db': {'desc': ''},
        '8086:24dd': {'desc': ''},
        '8086:2546': {'desc': ''},
        '8086:2550': {'desc': 'Memory Controller Hub', 'fake': True},
        '8086:2551': {'desc': 'Series RAS Controller'},
        '8086:2552': {'desc': 'PCI-to-AGP Bridge', 'fake': True},
        '8086:2553': {'desc': 'Hub Interface B PCI-to-PCI Bridge', 'fake': True},
        '8086:2554': {'desc': 'Interface B PCI-to-PCI Bridge RAS Controller', 'fake': True},
        '8086:2570': {'desc': ''},
        '8086:2572': {'desc': ''},
        '8086:25a1': {'desc': 'LPC Interface Controller'},
        '8086:25a2': {'desc': 'PATA Storage Controller'},
        '8086:25a4': {'desc': 'SMBus Controller'},
        '8086:25a9': {'desc': '6300ESB USB Universal Host Controller'},
        '8086:25aa': {'desc': '6300ESB USB Universal Host Controller'},
        '8086:25ab': {'desc': '6300ESB Watchdog Timer'},
        '8086:25ac': {'desc': '6300ESB I/O Advanced Programmable Interrupt Controller'},
        '8086:25ae': {'desc': '6300ESB 64-bit PCI-X Bridge'},
        '8086:25c0': {'desc': '5000X Chipset Memonry Controller Hub'},
        '8086:25d8': {'desc': ''},
        '8086:25e2': {'desc': ''},
        '8086:25e3': {'desc': '5000 Series Chipset PCI Express x4 Port 3'},
        '8086:25e4': {'desc': ''},
        '8086:25e5': {'desc': '5000 Series Chipset PCI Express x4 Port 5'},
        '8086:25e6': {'desc': '5000 Series Chipset PCI Express x4 Port 6'},
        '8086:25e7': {'desc': '5000 Series Chipset PCI Express x4 Port 7'},
        '8086:25f0': {'desc': '5000 Series Chipset FSB Registers'},
        '8086:25f1': {'desc': '5000 Series Chipset FSB Reserved Registers'},
        '8086:25f3': {'desc': '5000 Series Chipset FSB Reserved Registers'},
        '8086:25f5': {'desc': '5000 Series Chipset FBD Registers'},
        '8086:25f6': {'desc': '5000 Series Chipset FBD Registers'},
        '8086:25f7': {'desc': '5000 Series Chipset PCI Express x8 Port 2-3'},
        '8086:25f8': {'desc': '5000 Series Chipset PCI Express x8 Port 4-5'},
        '8086:25f9': {'desc': '5000 Series Chipset PCI Express x8 Port 6-7'},
        '8086:3500': {'desc': '6311ESB/6321ESB PCI Express Upstream Port'},
        '8086:350c': {'desc': '6311ESB/6321ESB PCI Express to PCI-X Bridge'},
        '8086:3510': {'desc': '6311ESB/6321ESB PCI Express Downstream Port E1'},
        '8086:3514': {'desc': '6311ESB/6321ESB PCI Express Downstream Port E2'},
        '8086:3590': {'desc': 'E7520 Memory Controller Hub'},
        '8086:3591': {'desc': 'E7525/E7520 Error Reporting Registers'},
        '8086:3595': {'desc': 'E7525/E7520/E7320 PCI Express Port A'},
        '8086:3596': {'desc': 'E7525/E7520/E7320 PCI Express Port A1'},
        '8086:3597': {'desc': 'E7525/E7520 PCI Express Port B'},
        '8086:3598': {'desc': 'E7520 PCI Express Port B1'},
        '8086:3599': {'desc': 'E7520 PCI Express Port C'},
        '8086:359b': {'desc': 'E7525/E7520/E7320 Extended Configuration Registers'},
        '8086:359e': {'desc': 'E7525 Memory Controller Hub'},
        '8086:7110': {'desc': 'PIIX4 ISA'},
        '8086:7111': {'desc': 'PIIX4 IDE'},
        '8086:7113': {'desc': 'PIIX4 ACPI'},
        '8086:7190': {'desc': 'Host bridge', 'fake': True},
        '8086:7191': {'desc': 'AGP bridge', 'fake': True},
        '8086:b154': {'desc': 'PCI-to-PCI bridge', 'fake': True},
        # 9905 = Adaptec
        '9005:0080': {'desc': ''},
        '9005:0250': {'desc': 'ServRAID Controller'},
        '9005:0285': {'desc': 'AAC-RAID'},
        '9005:0286': {'desc': 'AAC-RAID (Rocket)'},
        '9005:801d': {'desc': 'AIC-7902B U320'},
        '9005:801f': {'desc': ''},
        '9005:809d': {'desc': 'AIC-7902(B) U320 w/HostRAID'},
    }

    ##########################################################################
    def parseLinux_lspci(self):
        """ We need the stuff between the 'lspci -n' and the 'lspci -nv' lines
        """
        filename = 'lspci'
        """ 00:00.0 Class 0600: 1166:0014 (rev 33)"""
        reg = re.compile(
            '\d\d:\d\d.\d Class (?P<class>[0-f]{4}): (?P<pciid>[0-f]{4}:[0-f]{4}).*')

        f = self.open(filename)
        for line in f:
            m = reg.match(line)
            if m:
                pciid = m.group('pciid')

                self['pcis'].append(pciid)
                if pciid in self.pcidb:
                    self.Debug("pcidb[%s]=%s" % (pciid, self.pcidb[pciid]))
                else:
                    f = open('/tmp/pci.log', 'a')                  # DEBUG
                    f.write("%s %s\n" % (self.hostname, pciid))  # DEBUG
                    f.close()                                   # DEBUG
                    self.Warning("Unknown pciid=%s" % pciid)
        f.close()

    ##########################################################################
    def parseLinux_hardwarepy_chunk(self, buff, class_):
        if class_ == 'HD':
            if buff.get('bus', 'none') == 'USB':
                return
            model = buff['desc']
            if model.startswith('"') and model.endswith('"'):
                model = model[1:-1]
            self.addDrive(model)
        elif class_ == 'CDROM':
            model = buff['desc']
            if model.startswith('"') and model.endswith('"'):
                model = model[1:-1]
            self.addDrive(model)
        elif class_ == 'AUDIO':
            pass
        elif class_ == 'CPU':
            self.addCpu(desc=buff['model'])
            self.foundCpu = True
        elif class_ == 'USB':
            pass
        elif class_ == 'DMI':
            pass
        elif class_ == 'FLOPPY':
            pass
        elif class_ == 'FIREWIRE':
            pass
        elif class_ == 'IDE':
            pass
        elif class_ == 'INSTALLINFO':
            pass
        elif class_ == 'MEMORY':
            pass
        elif class_ == 'KEYBOARD':
            pass
        elif class_ == 'MOUSE':
            pass
        elif class_ == 'NETINFO':
            pass
        elif class_ == 'NETINTERFACES':
            pass
        elif class_ == 'NETWORK':
            pass
        elif class_ == 'OTHER':
            pass
        elif class_ == 'RAID':
            pass
        elif class_ == 'SCSI':
            pass
        elif class_ == 'VIDEO':
            pass
        elif class_ == 'UNSPEC':
            pass
        else:
            self.Debug("Unhandled hardware class_=%s" % class_)

    ##########################################################################
    def parseLinux_ide(self):
        files = self.glob('proc/ide/*/*/model')
        for f in files:
            mf = self.open(f)
            model = mf.readline().strip()
            mf.close()

    ##########################################################################
    def parseLinux_scsi(self):
        buff = []
        f = self.open('proc/scsi/scsi')
        for line in f:
            if 'Host' in line:
                self.parseLinux_scsi_chunk(buff)
                buff = [line]
            else:
                buff.append(line)
        f.close()
        self.parseLinux_scsi_chunk(buff)

    ##########################################################################
    def addDrive(self, model):
        if model in drivemap.drivemap:
            desc = drivemap.drivemap[model].get('desc', None)
            qty = drivemap.drivemap[model].get('qty', 1)
            optn = drivemap.drivemap[model].get('option', None)
            part = drivemap.drivemap[model].get('part', None)
            if desc or optn or part:
                self.addPart(
                    desc=desc, qty=qty, option=optn, part=part, component='disk')
        else:
            self.Warning("Couldn't find disk %s in drive partslist" % model)

    ##########################################################################
    def parseLinux_scsi_chunk(self, buff):
        # First check to see if we are talking about a real disk
        for line in buff:
            if 'Type:' in line:
                m = re.search('Type:\s+(?P<type>.*?)\s+', line)
                if m.group('type') in ('Direct-Access', 'Enclosure', 'Processor'):
                    return

        for line in buff:
            if 'Model:' in line:
                m = re.search('Model: (?P<model>.*)\s+Rev', line)
                model = m.group('model').strip()
                if model.startswith('"') and model.endswith('"'):
                    model = model[1:-1]
                self.addDrive(model)

    ##########################################################################
    def parseLinux_dmidecode(self):
        f = self.open('dmidecode')
        data = []
        for line in f:
            line = line.strip()
            if line.startswith('Handle'):
                self.parseDmiBundle(data)
                data = []
            if line.endswith('Information'):
                info = " ".join(line.split()[:-1])
            data.append(line)
        f.close()
        self.parseDmiBundle(data)

    ##########################################################################
    def dmiline(self, line):
        data = line[line.find(':') + 1:].strip()
        return data

    ##########################################################################
    def parseDmiBundle(self, data):
        if 'System Information' in data:
            for line in data:
                if 'Product Name' in line:
                    hardware = self.dmiline(line)
                if 'Serial Number' in line:
                    serial = self.dmiline(line)

        # CPUs
        if 'Processor Information' in data:
            for line in data:
                if 'Current Speed' in line:
                    cpuspeed = self.dmiline(line)
                if 'Version' in line:
                    version = self.dmiline(line)
                if 'Status' in line:
                    status = self.dmiline(line)
            if status != 'Unpopulated':
                self.foundCpu = True
                if not self.handleXcpu(version):
                    self.addCpu(desc='%s %s' % (cpuspeed, version))

        # IO Cards
        if 'System Slot Information' in data:
            self.foundIo = True
            if self['numslots'] < 0:
                self['numslots'] = 0
            for line in data:
                if 'Designation' in line:
                    slotdesig = self.dmiline(line)
                if 'Current Usage' in line:
                    inuse = self.dmiline(line)
                    if inuse == 'Available':
                        self['numslots'] += 1

        # Memory Chips
        if 'Memory Device' in data:
            for line in data:
                if 'Size' in line:
                    memsize = self.dmiline(line)
                if 'Form Factor' in line:
                    formfactor = self.dmiline(line)
            if 'No Module Installed' not in memsize:
                self.foundMem = True
                self.addMem(desc='%s %s' % (memsize, formfactor), size=memsize)

    ##########################################################################
    def handleXcpu(self, line):
        """ Match Sun X series CPUs

        This is based on substring searches with the keys of a dictionary,
        so you cannot guarantee the order of comparisons. So put the most specific
        (long strings) in the longmap and the least specific (short strings) in the
        short map. longmap will be searched before shortmap.
        """
        # Check these cpus first as the have other CPUs which are substrings
        longmap = {
            '8220 SE': {'desc': '2.8GHz Opteron 8220 CPU/memory module', 'option': 'X8109A', 'part': '541-2045'},
        }

        shortmap = {
            '1210': {'desc': '1.8GHz Dual Core CPU, AMD Opteron 1210', 'option': '5273A-Z', 'part': '371-1971'},
            '1220': {'desc': '2.8GHz Dual Core Opteron 1220', 'option': '5274A-Z', 'part': '371-2491'},
            '2210': {'desc': '1.8GHz Dual Core CPU, AMD Opteron 2210', 'option': 'X4421A-Z', 'part': '371-2495'},
            '2216': {'desc': '2.4GHz Dual Core CPU, AMD Opteron 2216', 'option': 'X4222A', 'part': '371-2499'},
            '2218': {'desc': '2.6GHz Dual Core CPU, AMD Opteron 2218', 'option': 'X4223A', 'part': '371-2500'},
            '2220': {'desc': '2.8GHz Dual Core CPU, AMD Opteron 2220', 'option': ['X4057A', 'X4224A'], 'part': ['371-2501', '371-1914']},
            '2222': {'desc': '3.0GHz Dual Core CPU, AMD Opteron 2222', 'option': 'X4081A', 'part': '371-2503'},
            '2354': {'desc': '2.2GHz Quad Core CPU, AMD Opteron 2354', 'option': 'X5328A-QC-UP2', 'part': '371-4041'},
            '2356': {'desc': '2.3GHz Quad Core CPU, AMD Opteron 2356', 'option': 'X6305A', 'part': '594-4794'},
            '148': {'desc': '2.2GHz Dual Core CPU, AMD Opteron 148', 'option': 'X8072A', 'part': '370-7940'},
            '248': {'desc': '2.2GHz Dual Core CPU, AMD Opteron 248', 'option': 'X8031A', 'part': '370-7711'},
            '252': {'desc': '2.6GHz Dual Core CPU, AMD Opteron 252', 'option': 'X8033A', 'part': '370-7937'},
            '254': {'desc': '2.8GHz Dual Core CPU, AMD Opteron 254', 'option': 'X8034A', 'part': '370-7962'},
            '275': {'desc': '2.2GHz Dual Core CPU, AMD Opteron 275', 'option': 'X8037A', 'part': '370-7800'},
            '280': {'desc': '2.4GHz Dual Core CPU, AMD Opteron 280', 'option': 'X8044A', 'part': '371-0839'},
            '285': {'desc': '2.6GHz Dual Core CPU, AMD Opteron 285', 'option': 'X8046A', 'part': '371-0856'},
            '8220': {'desc': '2.8GHz Opteron 8220 CPU/memory module', 'option': 'X8113A', 'part': '541-2262'},
            '8222': {'desc': '3.0GHz Opteron 8222 CPU/memory module', 'option': 'X8111A', 'part': '541-2403'},
            '885': {'desc': '2.6GHz Opteron 885 CPU/memory module', 'option': 'X8105A', 'part': '541-1771'},
        }
        self.foundCpu = True

        for map in (longmap, shortmap):
            for key, value in map.items():
                if " %s " % key in line:
                    self.addCpu(
                        desc=value['desc'], option=value['option'], part=value['part'])
                    return True
        for map in (longmap, shortmap):
            for key, value in map.items():
                if key in line:
                    self.addCpu(
                        desc=value['desc'], option=value['option'], part=value['part'])
                    return True

        return False

    ##########################################################################
    def analyse(self):
        for loc in self.allCardLocations():
            for card in self[loc]:
                card.analyse()
                self.inheritIssues(card)

    ##########################################################################
    def inheritParts(self):
        """ Get the parts of the children and make them our own
        """
        for loc in self.allCardLocations():
            for card in self[loc]:
                for part in card.parts:
                    self.addPart(fullpart=part)

    ##########################################################################
    def getDriveHardware(self):
        """ This is not part of Prtdiag analsysis but more part of hardware
        analysis
        """
        if self.config['explorertype'] != 'solaris':
            return
        data = self.parseIostat()
        for dev in data:
            if 'product' not in data[dev]:
                if 'model' in data[dev]:
                    data[dev]['product'] = data[dev]['model'].strip()
                else:
                    self.Warning("No product for %s - %s" % (dev, data[dev]))
                    continue
            self.addDrive(data[dev]['product'])

    ##########################################################################
    def allCardLocations(self):
        return [loc for loc in self.keys() if loc.startswith('loc_')]

    ##########################################################################
    def removeFalseCards(self):
        """ Some listed cards are inbuilt devices and should be removed as
        separately listed cards - this includes devices which are bus controllers
        and similar; that are there to provide function to the card not the user
        """
        for loc in self.allCardLocations():
            for card in self[loc][:]:
                if 'fake' in card and card['fake']:
                    self[loc].remove(card)
            if len(self[loc]) == 0:
                del self.data[loc]

    ##########################################################################
    def parse(self):
        hardwareParser = {
            'ibm_hs20': self.ibm_hs20,
            'sun_4800': self.sun_4800,
            'sun_6800': self.sun_4800,  # Same hardware effectively
            'sun_15k': self.sun_15k,
            'sun_25k': self.sun_25k,
            'sun_280r': self.sun_280r,
            'sun_v480': self.sun_v480,
            'sun_blade100': self.sun_blade100,
            'sun_blade150': self.sun_blade150,
            'sun_blade1000': self.sun_blade1000,
            'sun_blade2000': self.sun_blade2000,
            'sun_cp1500': self.sun_cp1500,
            'sun_cp2000': self.sun_cp2000,
            'sun_e220r': self.sun_e220r,
            'sun_e250': self.sun_e250,
            'sun_e2900': self.sun_e2900,
            'sun_e420r': self.sun_e420r,
            'sun_e450': self.sun_e450,
            'sun_e3500': self.sun_e4500,
            'sun_e4500': self.sun_e4500,
            'sun_e6900': self.sun_e6900,
            'sun_t1': self.sun_t1,
            'sun_m3000': self.sun_m3000,
            'sun_m4000': self.sun_m4000,
            'sun_m9000': self.sun_m9000,
            'sun_netra120': self.sun_v120,
            'sun_netra240': self.sun_v240,
            'sun_t1000': self.sun_t1000,
            'sun_t4_1': self.sun_t4,
            'sun_t4_4': self.sun_t4,
            'sun_t2000': self.sun_t2000,
            'sun_t5220': self.sun_t5220,
            'sun_t6300': self.sun_t6300,
            'sun_t6320': self.sun_t6320,
            'sun_ultra1': self.sun_ultra1,
            'sun_ultra2': self.sun_ultra2,
            'sun_ultra45': self.sun_ultra45,
            'sun_ultra5': self.sun_ultra5,
            'sun_ultra60': self.sun_ultra60,
            'sun_ultra80': self.sun_ultra80,
            'sun_v100': self.sun_v100,
            'sun_v120': self.sun_v120,
            'sun_v125': self.sun_v125,
            'sun_v20z': self.sun_v20z,
            'sun_v40z': self.sun_v40z,
            'sun_v210': self.sun_v210,
            'sun_v215': self.sun_v245,  # v215 and v245 are the same internally
            'sun_v240': self.sun_v240,
            'sun_v245': self.sun_v245,
            'sun_v440': self.sun_v440,
            'sun_v445': self.sun_v445,
            'sun_v1280': self.sun_v1280,
            'sun_v490': self.sun_v490,
            'sun_v60': self.sun_v60,
            'sun_v880': self.sun_v880,
            'sun_v890': self.sun_v890,
            'sun_x1': self.sun_x1,
            'sun_x2100': self.sun_x2100,
            'sun_x2100_m2': self.sun_x2100,
            'sun_x2200_m2': self.sun_x2200,
            'sun_x4100': self.sun_x4100,
            'sun_x4100_m2': self.sun_x4100,
            'sun_x4140': self.sun_x4140,
            'sun_x4200': self.sun_x4200,
            'sun_x4200_m2': self.sun_x4200,
            'sun_x4500': self.sun_x4500,
            'sun_x4600': self.sun_x4600,
            'sun_x6220': self.sun_x6220,
            'vmware': self.vmware,
        }

        self['pcis'] = []
        h = hostdet.Host(self.config)
        hardware = h['hardware']

        # Linux
        if self.config['explorertype'] == 'linux':
            self.parseLinux(hardware)
            return

        # Solaris
        if hardware in hardwareParser:
            try:
                hardwareParser[hardware]()
            except UserWarning, err:
                self.Warning(err)
        else:
            raise UserWarning, "Unhandled hardware type '%s'" % hardware

    ##########################################################################
    def parseIpmi(self):
        """ Parse IPMI output if it is available - it gives more details on those servers
        that don't have useful prtdiags
        """
        ipmi = {}
        filename = 'ipmi/ipmitool_fru.out'
        if self.exists(filename):
            f = self.open(filename)
            self.foundIo = True
            for line in f:
                line = line.strip()
                if line.startswith('FRU Device Description'):
                    name = line.split(
                        ':', 1)[-1].split()[0].strip().replace('.fru', '')
                    ipmi[name] = {}
                    continue
                if ':' not in line:
                    continue
                bits = line.split(':', 1)
                ipmi[name][bits[0].strip()] = bits[1].strip()
            f.close()

        filename = 'ipmi/ipmitool_chassis_status.out'
        if self.exists(filename):
            f = self.open(filename)
            for line in f:
                if 'Main Power Fault' in line and 'true' in line:
                    self.addIssue('Power', text='Main Power Fault')
                if 'Drive Fault' in line and 'true' in line:
                    self.addIssue('Drive', text='Drive Fault')
                if 'Cooling/Fan Fault' in line and 'true' in line:
                    self.addIssue('Fan', text='Cooling/Fan Fault')
            f.close()
        return ipmi

    ##########################################################################
    def aggregateCombos(self):
        """ There should only be one card in each location
        If there are multiple it either means a combination card, or a built in capability
        If we find a combo card then replace all the existing fake cards in that location with the
        combo card
        """
        for loc in self.allCardLocations():
            rv = self.comboCards(loc)
            if rv:
                # Copy bus and other misc data
                newcarddata = self[loc][0].data.copy()
                del newcarddata['rawmodel']
                newcarddata['iocard'] = rv
                newcarddata['combo'] = True
                self[loc] = [IoCard(self.config, **newcarddata)]
            if len(self[loc]) > 1:
                self.Warning("MultiCard loc=%s cards=%s" %
                             (loc, sorted(self[loc])))

    ##########################################################################
    def comboCards(self, loc):
        """ Check for the occurence of combination cards - multiple cards in the same slot
        Either return None, or the name of the matching combo card
        """
        if len(self[loc]) == 1:
            return
        cm = sorted([card['cardabbrev'] for card in self[loc]])
        for combo in cardmap.comboSets:
            if sorted(cardmap.comboSets[combo]['components']) == cm:
                qty = cardmap.comboSets[combo].get('qty', 1)
                optn = cardmap.comboSets[combo].get(
                    'option', "Undefined combo option")
                part = cardmap.comboSets[combo].get(
                    'part', "Undefined combo part")
                self.addPart(
                    desc=combo, qty=qty, option=optn, part=part, component='card')
                return combo
        return None

    ##########################################################################
    def getLoc(self, **kwargs):
        locstr = "loc_"
        if 'board' in kwargs:
            locstr += "Board=%s " % kwargs['board']
        if 'bus' in kwargs:
            locstr += "Bus=%s " % kwargs['bus']
        if 'slot' in kwargs:
            locstr += "Slot=%s " % kwargs['slot']
        if 'busside' in kwargs:
            locstr += "BusSide=%s " % kwargs['busside']
        return locstr.strip()

    ##########################################################################
    def sun_v20z(self):
        ipmi = self.parseIpmi()
        for i in ipmi:
            if 'mem' in i and 'memvrm' not in i:
                if not ipmi[i]:
                    continue
                desc = ipmi[i]['Product Name']
                if '1GB DDR333 (PC2700) ECC' in desc:
                    option = 'X9252A'
                    part = '370-6645'
                    size = '1GB'
                else:
                    self.Warning("Unhandled Mem on V20Z: %s" % desc)
                self.addMem(desc=desc, option=option, part=part, size=size)

        if self.exists('sysconfig/prtpicl-v.out'):
            f = self.open('sysconfig/prtpicl-v.out')
            for line in f:
                if ':brand-string' in line:
                    cpu = line.replace(':brand-string', '').strip()
                    self.foundCpu = True
                    if cpu == 'AMD Opteron(tm) Processor 244':
                        self.addCpu(
                            desc='1.8GHz AMD Opteron (Unknown stepping)', part='370-6783', option='X9835A')
                    elif cpu == 'AMD Opteron(tm) Processor 248':
                        self.addCpu(
                            desc='2.2GHz AMD Opteron (Unknown stepping)', part='370-7711', option='X9856A')
                    else:
                        self.Warning("Unhandled V20Z CPU: %s" % cpu)
            f.close()

    ##########################################################################
    def sun_v40z(self):
        memMap = {
            '1GB DDR333 (PC2700) ECC': {'option': 'X9252A', 'part': '370-6644', 'size': '1GB'},
            '1GB DDR400 (PC3200) ECC': {'option': 'X9296A', 'part': '370-7805', 'size': '1GB'},
            '2GB DDR400 (PC3200) ECC': {'option': 'X9297A', 'part': '370-7806', 'size': '2GB'},
        }
        cpuMap = {
            'AMD Opteron(tm) Processor 848': {'option': '7242A', 'part': '370-7704', 'desc': '2.2GHz CPU, AMD Opteron 848'},
            'AMD Opteron(tm) Processor 850': {'option': '9869A', 'part': '370-7705', 'desc': '2.4GHz CPU, AMD Opteron 850'},
            'AMD Opteron(tm) Processor 852': {'option': '9870A', 'part': '370-7706', 'desc': '2.6GHz CPU, AMD Opteron 852'},
        }
        ipmi = self.parseIpmi()
        for i in ipmi:
            size = ''
            if 'mem' in i and 'memvrm' not in i:
                if not ipmi[i]:
                    continue
                desc = ipmi[i]['Product Name']
                for m in memMap:
                    if m in desc:
                        option = memMap[m]['option']
                        part = memMap[m]['part']
                        size = memMap[m]['size']
                        self.addMem(
                            desc=desc, option=option, part=part, size=size)
                        self.foundMem = True
                if not size:
                    self.Warning("Unhandled Mem on V40Z: %s" % desc)

        if self.exists('sysconfig/prtpicl-v.out'):
            f = self.open('sysconfig/prtpicl-v.out')
            for line in f:
                if ':brand-string' in line:
                    cpu = line.replace(':brand-string', '').strip()
                    if cpu in cpuMap:
                        self.foundCpu = True
                        self.addCpu(
                            desc=cpuMap[cpu]['desc'],
                            part=cpuMap[cpu]['part'],
                            option=cpuMap[cpu]['option'],
                        )
                    else:
                        self.Warning("Unhandled V40Z CPU: %s" % cpu)
            f.close()

    ##########################################################################
    def sun_t6300(self):
        mode = 'unknown'
        envmodeDict = {
            #           'temp': ('System Temperatures','',''),
            #           'indicat': ('System Indicator Status', '', ''),
            #           'disks': ('System Disks:', '', ''),
            #           'fans': ('Fan Status:', '', ''),
            #           'voltage': ('Voltage sensors', '', ''),
            #           'psu': ('Power Supplies', '', ''),
        }
        modeDict = {
            #           'cpu': ('', '== CPUs ==', ''),
            #           'mem': ('', '== Memory Configuration ==', ''),
            'iocards': ('', '== IO Configuration ==', '', self.parseIo),
            'hwrev': ('', '== HW Revisions ==', ''),
            'fan': ('Fan sensors', '', ''),
            'temp': ('Temperature sensors', '', ''),
            #           'current': ('Current sensors', '', ''),
            'voltage': ('Voltage sensors', '', ''),
            'voltindic': ('Voltage indicators', '', ''),
        }
        cpuMap = {}
        memMap = {
            'DDR2 SDRAM, 1024 MB': {'desc': '2 GB (2 x 1GB DDR2 DIMMs)', 'option': 'X5722A', 'part': '540-7311'},
            'DDR2 SDRAM, 2048 MB': {'desc': '4 GB (2 x 2GB DDR2 DIMMs)', 'option': 'X5723A', 'part': '540-7312'},
        }

        # Not all hosts have prtdiag
        if self.exists('sysconfig/prtdiag-v.out'):
            data = self.genericPrtdiag(modeDict)
            self.genericIo(data, ['MB'])

            f = self.open('sysconfig/prtdiag-v.out')
            for line in f:
                line = line.rstrip()
                if mode == 'fan':
                    self.genericCheck("Fan", line, 1, ['-----', 'Status'])
                if mode == 'temp':
                    self.genericCheck("Temp", line, -1, ['-----', 'Status'])
                if mode == 'current':
                    self.genericCheck("Current", line, -1, ['-----', 'Status'])
                if mode == 'voltage':
                    self.genericCheck("Voltage", line, -1, ['-----', 'Status'])
                if mode == 'voltindic':
                    self.genericCheck("Voltage", line, -1, ['-----', 'Status'])
            f.close()

        if self.exists('Tx000/showenvironment'):
            f = self.open('Tx000/showenvironment')
            for line in f:
                line = line.strip()
                mode, skip = self.modeSelect(mode, line, envmodeDict)
                if skip:
                    continue
                if mode == 'temp':
                    self.genericCheck(
                        'Temperature', line, 1, ['-----', 'Status'])
                if mode == 'disks':
                    self.genericCheck(
                        'System Disks', line, 1, ['-----', 'Status', 'NOT PRESENT'])
                if mode == 'fans':
                    self.genericCheck(
                        'Fans', line, 1, ['-----', 'Sensor', 'Revolution'])
                if mode == 'voltage':
                    self.genericCheck('Voltage', line, 1, ['-----', 'Sensor'])
                if mode == 'psu':
                    self.genericCheck(
                        'Power Supply', line, 1, ['-----', 'Supply'])
            f.close()

        self.generic_tx000_showfru('t6300', memMap)

    ##########################################################################
    def sun_t6320(self):
        mode = 'unknown'
        envmodeDict = {
            #           'temp': ('System Temperatures','',''),
            #           'indicat': ('System Indicator Status', '', ''),
            #           'disks': ('System Disks:', '', ''),
            #           'fans': ('Fan Status:', '', ''),
            #           'voltage': ('Voltage sensors', '', ''),
            #           'psu': ('Power Supplies', '', ''),
        }
        modeDict = {
            'cpu': ('', '== Virtual CPUs ==', ''),
            #           'mem': ('', '== Memory Configuration ==', ''),
            'iocards': ('', '== IO Devices ==', '', self.parseIo),
            'hwrev': ('', '== HW Revisions ==', ''),
            'env': ('', '== Environmental Status ==', ''),
            'fan': ('Fan sensors', '', ''),
            'fru': ('', '== FRU Status ==', ''),
            'fan_ind': ('Fan indicators', '', ''),
            'temp': ('Temperature sensors', '', ''),
            'leds': ('LEDs', '', ''),
            'voltage': ('Voltage sensors', '', ''),
            'voltindic': ('Voltage indicators', '', ''),
        }
        cpuMap = {}
        memMap = {
            'DDR2 SDRAM FB-DIMM, 4 GByte': {'desc': '8GB Memory Expansion (2 x 4GB)', 'option': 'X4204A', 'part': '501-7954'},
            'DDR2 SDRAM FB-DIMM, 2 GByte': {'desc': '4GB Memory Expansion (2 x 2GB)', 'option': 'X4203A', 'part': '511-1161'},
            'DDR2 SDRAM FB-DIMM, 1 GByte': {'desc': '2GB Memory Expansion (2 x 1GB)', 'option': 'X4200A', 'part': '501-7952'},
        }

        # Not all hosts have prtdiag
        if self.exists('sysconfig/prtdiag-v.out'):
            data = self.genericPrtdiag(modeDict)
            self.genericIo(data, [
                           'MB/DISPLAY', 'MB/USB1', 'MB/USB0', 'MB/NET1', 'MB/NET0', 'MB/REM/SASHBA', 'MB/PCI-EM0'])

            f = self.open('sysconfig/prtdiag-v.out')
            for line in f:
                line = line.rstrip()
                if mode == 'cpu':
                    # Lots of threads and virtuals make this mostly irrelevent
                    self.foundCpu = True
                if mode == 'fan':
                    self.genericCheck("Fan", line, 1, ['-----', 'Status'])
                if mode == 'fan_ind':
                    self.genericCheck("Fan", line, 1, ['-----', 'Status'])
                if mode == 'temp':
                    self.genericCheck("Temp", line, -1, ['-----', 'Status'])
                if mode == 'current':
                    self.genericCheck("Current", line, -1, ['-----', 'Status'])
                if mode == 'voltage':
                    self.genericCheck("Voltage", line, -1, ['-----', 'Status'])
                if mode == 'voltindic':
                    self.genericCheck("Voltage", line, -1, ['-----', 'Status'])
                if mode == 'leds':
                    self.genericCheck("LEDs", line, -1, ['-----', 'Location'])
                if mode == 'fru':
                    self.genericCheck("LEDs", line, -1, ['-----', 'Location'])
            f.close()

        if self.exists('Tx000/showenvironment'):
            f = self.open('Tx000/showenvironment')
            for line in f:
                line = line.strip()
                mode, skip = self.modeSelect(mode, line, envmodeDict)
                if skip:
                    continue
                if mode == 'temp':
                    self.genericCheck(
                        'Temperature', line, 1, ['-----', 'Status'])
                if mode == 'disks':
                    self.genericCheck(
                        'System Disks', line, 1, ['-----', 'Status', 'NOT PRESENT'])
                if mode == 'fans':
                    self.genericCheck(
                        'Fans', line, 1, ['-----', 'Sensor', 'Revolution'])
                if mode == 'voltage':
                    self.genericCheck('Voltage', line, 1, ['-----', 'Sensor'])
                if mode == 'psu':
                    self.genericCheck(
                        'Power Supply', line, 1, ['-----', 'Supply'])
            f.close()

        self.generic_tx000_showfru('t6320', memMap)

    ##########################################################################
    def sun_t5220(self):
        mode = 'unknown'
        envmodeDict = {
            'temp': ('System Temperatures', '', ''),
            'indicat': ('System Indicator Status', '', ''),
            'disks': ('System Disks:', '', ''),
            'fans': ('Fan Status:', '', ''),
            'voltage': ('Voltage sensors', '', ''),
            'psu': ('Power Supplies', '', ''),
        }
        modeDict = {
            'cpu': ('', '== CPUs ==', ''),
            'mem': ('', '== Memory Configuration ==', ''),
            'iocards': ('', '== IO Configuration ==', '', self.parseIo),
            'hwrev': ('', '== HW Revisions ==', ''),
            'fan': ('Fan sensors', '', ''),
            'temp': ('Temperature sensors', '', ''),
            'current': ('Current sensors', '', ''),
            'voltage': ('Voltage sensors', '', ''),
            'voltindic': ('Voltage indicators', '', ''),
        }
        cpuMap = {}
        memMap = {
            'DDR2 SDRAM FB-DIMM, 1 GByte': {'desc': '2GB Memory Expansion (2 x 1GB)', 'option': 'SESX2A2Z', 'part': '501-7952'},
            'DDR2 SDRAM FB-DIMM, 2 GByte': {'desc': '4GB Memory Expansion (2 x 2GB)', 'option': 'SESX2B2Z', 'part': '501-7953'},
            'DDR2 SDRAM FB-DIMM, 4 GByte': {'desc': '8GB Memory Expansion (2 x 4GB)', 'option': 'SESX2C2Z', 'part': '501-7954'},
            'FBDIMM, 1 GByte': {'desc': '2GB Memory Expansion (2 x 1GB)', 'option': 'SESX2A2Z', 'part': '511-1264'},
        }

        # Not all hosts have prtdiag
        if self.exists('sysconfig/prtdiag-v.out'):
            data = self.genericPrtdiag(modeDict)
            self.genericIo(data, ['MB'])

            f = self.open('sysconfig/prtdiag-v.out')
            for line in f:
                line = line.rstrip()
                if mode == 'fan':
                    self.genericCheck("Fan", line, 1, ['-----', 'Status'])
                if mode == 'temp':
                    self.genericCheck("Temp", line, -1, ['-----', 'Status'])
                if mode == 'current':
                    self.genericCheck("Current", line, -1, ['-----', 'Status'])
                if mode == 'voltage':
                    self.genericCheck("Voltage", line, -1, ['-----', 'Status'])
                if mode == 'voltindic':
                    self.genericCheck("Voltage", line, -1, ['-----', 'Status'])
            f.close()

        if self.exists('Tx000/showenvironment'):
            f = self.open('Tx000/showenvironment')
            for line in f:
                line = line.strip()
                mode, skip = self.modeSelect(mode, line, envmodeDict)
                if skip:
                    continue
                if mode == 'temp':
                    self.genericCheck(
                        'Temperature', line, 1, ['-----', 'Status'])
                if mode == 'disks':
                    self.genericCheck(
                        'System Disks', line, 1, ['-----', 'Status', 'NOT PRESENT'])
                if mode == 'fans':
                    self.genericCheck(
                        'Fans', line, 1, ['-----', 'Sensor', 'Revolution'])
                if mode == 'voltage':
                    self.genericCheck('Voltage', line, 1, ['-----', 'Sensor'])
                if mode == 'psu':
                    self.genericCheck(
                        'Power Supply', line, 1, ['-----', 'Supply'])
            f.close()

        self.generic_tx000_showfru('t5220', memMap)

    ##########################################################################
    def generic_tx000_showfru(self, label="unknown", memMap={}):
        numdimm = 0
        if self.exists('Tx000/showfru'):
            f = self.open('Tx000/showfru')
            for line in f:
                line = line.strip()
                if 'Sun_Part_No' in line or 'Sun_Part_Dash_Rev' in line:
                    partnum = line.split(':')[-1].strip()
                    if 'Rev' in partnum:
                        partnum = partnum[:partnum.index(' Rev')]
                    d, p, o, c = self.lookupPart(partnum)
                    if p:
                        if c == 'cpu':
                            self.foundCpu = True
                        self.addPart(desc=d, part=p, option=o, category=c)
                if '/SPD/Description' in line:
                    desc = line.split(':')[-1].strip()
                    if desc in memMap:
                        if numdimm % 2 == 0:
                            self.addMem(**memMap[desc])
                            self.foundMem = True
                        numdimm += 1
                    else:
                        self.Warning(
                            "Unhandled Memory in %s: %s" % (label, desc))
            f.close()

    ##########################################################################
    def lookupPart(self, partnum):
        """ Tx000 output knows Sun part numbers - use them for the parts
        It should return (description, partnum, option, componenttype)
        or ?, None, ? if it shouldn't be added to the partslist
        """
        partslist = {
            '5111304': ('Service Processor Assembly', '511-1304', None, 'systemboard'),
            '5111098': ('RAID 0/1 Expansion Module', '511-1098', None, 'systemboard'),
            '5017814': ('4-Core 1.2GHz System Board', '541-2867', None, 'cpu'),
            '5412317': ('1.0GHz 6-Core System Board', '541-2317', 'X5705A', 'cpu'),
            '5410569': ('1.0GHz 4-Core System Board', '541-0569', None, 'cpu'),
            '5411454': ('1.0GHz 8-Core System Board', '541-1454', None, 'cpu'),
            '5411455': ('1.0GHz 4-Core System Board', '541-1455', None, 'cpu'),
            '5412150': ('1.2GHz 8-Core System Board', '541-2150', None, 'cpu'),
            '5412153': ('1.2GHz 6-Core System Board', '541-2153', None, 'cpu'),
            '5412155': ('1.4GHz 8-Core System Board', '541-2155', None, 'cpu'),
            '5412409': ('8-Core 1.4GHz System Board', '541-2409', None, 'cpu'),
            '5412515': ('8-Core 1.4GHz System Board', '541-2409', None, 'cpu'),
            '5412514': ('4-Core UltraSPARC T2, 1.2GHz Assembly', '541-2514', None, 'cpu'),
            '5410599': ('6-Core UltraSPARC T1, 1.0GHz Assembly', '541-0599', None, 'cpu'),
            '5411035': ('8-Core UltraSPARC T1, 1.0GHz Assembly', '541-1035', None, 'cpu'),
            # Covered by the 501 part
            '5412156': (None, None, None, None),
            '5412318': ('8 Core 1.4GHz Sun Blade T6300 Server Module', '541-2318', None, 'cpu'),
            '5410570': ('8-Core, UltraSPARC T1, 1.0GHz System + I/O board', '541-0570', None, 'cpu'),
            '5413838': ('8-Core, UltraSPARC T2, 1.4GHz CPU Assembly', '541-3838', None, 'cpu'),
            '5412407':  (None, None, None, None),  # RAM for T6320
            '000-0000-00': (None, None, None, None),
            # This seems to be a duplicate of 5412150 which will also be
            # installed
            '5017781': (None, None, None, None),
            '5017822': ('Service Process Assembly ILOM3.0', None, None, 'systemboard'),
            '5101170': ('Service Process Assembly ILOM3.0', None, None, 'systemboard'),
            '5412073': ('Power Distribution Board', None, None, 'power'),
            '5017697': ('Horizontal Power Distribution Board', None, None, 'power'),
            '5017730': ('8-Slot Disk Backplane', None, None, 'systemboard'),
            '5412211': ('Fan Power Board', None, None, 'power'),
            '5017695': ('Fan Board', None, None, 'power'),
            '5017821': ('RAID Expansion Module', '501-7821', 'X4601A', 'systemboard'),
            '3002030': ('750 Watt Power Supply', '300-2030', 'SEDX9PS31Z', 'powersupply'),
            # 1GB DDRs Should be covered by the desc
            '371-2644-01': (None, None, None, None),
            # 2GB DDRs Should be covered by the desc
            '371-2645-01': (None, None, None, None),
            # Should be covered by the desc
            '501-7952-01': (None, None, None, None),
            # Should be covered by the desc
            '501-7953-01': (None, None, None, None),
            # Should be covered by the desc
            '501-7632-01': (None, None, None, None),
            # Should be covered by the desc
            '501-7954-01': (None, None, None, None),
            # Should be covered by the desc
            '511-1161-01': (None, None, None, None),
            # 1GB DDRs Should be covered by the desc
            '501-7631-01': (None, None, None, None),

        }
        if partnum in partslist:
            return partslist[partnum]
        else:
            self.Warning("Unknown partnumber %s" % partnum)
        return None, None, None, None

    ##########################################################################
    def sun_4800(self):
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'mem': ('', '== Memory Configuration ==', '', self.parseMem),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'acboards': ('', '== Active Boards for Domain ==', ''),
            'hwstatus': ('', '== Hardware Failures ==', ''),
        }
        cpuMap = {
            'US-III @ 750': {'desc': 'CPU/Memory Uniboard w/2x US III Cu 750MHz, 0MB', 'part': '540-6446'},
            'US-III+ @ 750': {'desc': 'CPU/Memory Uniboard w/2x US III Cu 750MHz, 0MB', 'part': '540-6446'},
            'US-III+ @ 1200': {'desc': 'CPU/Memory Uniboard w/2x US III Cu 1.2GHz, 0MB', 'part': '540-6848'},
        }
        memMap = {
            '256MB': {'desc': '1GB (4 x 256MB SDRAM DIMM)', 'option': 'X7053A', 'part': '501-5401', 'size': '256MB'},
            '512MB': {'desc': '2GB (4 x 512MB SDRAM DIMM)', 'option': 'X7051A', 'part': '501-7385', 'size': '512MB'},
            '1024MB': {'desc': '4GB (4 x 1GB SDRAM DIMM)', 'option': 'X7056A', 'part': '501-7386', 'size': '1GB'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, '4800', modulo=2)
        self.genericMem(data, memMap, '4800', modulo=4)
        self.genericIo(data)

    ##########################################################################
    def sun_15k(self):
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'mem': ('', '== Memory Configuration ==', '', self.parseMem),
            'hwrev': ('', '== Diagnostic Information ==', ''),
        }
        cpuMap = {
            'US-IV+ @ 1500': {'desc': 'CPU/Memory Uniboard w 4x US IV+ 1.5GHz, 0MB', 'part': '540-6832'},
            'US-III+ @ 1200': {'desc': 'CPU/Memory Uniboard w 4x US III Cu 1.2GHz, 0MB', 'part': '540-6489'},
        }
        memMap = {
            '1024MB': {'desc': '4 GB (4 x 1GB SDRAM DIMMs)', 'part': '501-7386', 'option': 'X7056A', 'size': '1GB'},
            '512MB': {'desc': '2 GB (4 x 512MB SDRAM DIMMs)', 'part': '501-7385', 'option': 'X7051A', 'size': '512MB'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, '15k', modulo=4)
        self.genericMem(data, memMap, '15k', modulo=4)
        self.genericIo(data)

    ##########################################################################
    def sun_25k(self):
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'mem': ('', '== Memory Configuration ==', '', self.parseMem),
            'hwrev': ('', '== Diagnostic Information ==', ''),
        }
        cpuMap = {
            'US-IV+ @ 1800': {'desc': 'CPU/Memory Uniboard w 4x US IV+ 1.8GHz, 0MB', 'part': '540-6754'},
        }
        memMap = {
            '512MB': {'desc': '4x512MB', 'part': '501-7385', 'option': 'X7051A-Z'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, '25k', modulo=4)
        self.genericMem(data, memMap, '25k', modulo=4)
        self.genericIo(data)

    ##########################################################################
    def ibm_hs20(self):
        # TODO
        # Currently nothing that I can see to extract, yet
        pass

    ##########################################################################
    def sun_m3000(self):
        """
        IO cards are a basket case for the m series
        """
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'mem': ('', '== Memory Configuration ==', '', self.parseMem),
            'hwrev': ('', '== Hardware Revisions ==', ''),
            'iocards': ('', '== IO Devices ==', '', self.parseIo),
        }
        cpuMap = {
            '6 @ 2150': {'desc': '2x SPARC64 VI 2.1GHz CPU Module', 'part': '375-3477', 'option': 'SELX1A1Z'},
            '7 @ 2520': {'desc': '1 x 2.52 GHz CPU Dual Core', 'part': '541-3674'},
        }
        memMap = {
            '1024MB': {'desc': '4x1GB', 'part': '371-1899', 'option': 'SELX2A1Z'},
            '4096MB': {'desc': '4x4GB', 'part': '596-7870', 'option': 'SELX2C1Z'},
            '8192MB': {'desc': '4x8GB', 'part': '371-4591', 'option': 'SEWX2D1Z'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'm3000')
        self.genericIo(data, ['0'])
        self.genericMem(data, memMap, 'm3000')

    ##########################################################################
    def sun_m4000(self):
        """
        IO cards are a basket case for the m series
        """
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'mem': ('', '== Memory Configuration ==', '', self.parseMem),
            'hwrev': ('', '== Hardware Revisions ==', ''),
            'iocards': ('', '== IO Devices ==', '', self.parseIo),
        }
        cpuMap = {
            '6 @ 2150': {'desc': '2x SPARC64 VI 2.1GHz CPU Module', 'part': '375-3477', 'option': 'SELX1A1Z'},
        }
        memMap = {
            '1024MB': {'desc': '1GB DDR2-533', 'part': '371-1899', 'option': 'SELX2A1Z'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'm4000')
        self.genericIo(data, ['0'])
        self.genericMem(data, memMap, 'm4000')

    ##########################################################################
    def sun_m9000(self):
        """
        IO cards are a basket case for the m series
        """
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'mem': ('', '== Memory Configuration ==', '', self.parseMem),
            'hwrev': ('', '== Hardware Revisions ==', ''),
            'iocards': ('', '== IO Devices ==', '', self.parseIo),
        }
        cpuMap = {
            '7 @ 2520': {'desc': '2x SPARC64 VI 2.1GHz CPU Module', 'part': '375-3477', 'option': 'SELX1A1Z'},
            '6 @ 2150': {'desc': '2x SPARC64 VI 2.1GHz CPU Module', 'part': '375-3477', 'option': 'SELX1A1Z'},
        }
        memMap = {
            '1024MB': {'desc': '1GB DDR2-533/DDR2-667 1-Rank DIMM', 'part': '501-7791', 'option': 'SEMx2A1Z'},
            '2048MB': {'desc': '2GB DDR2-667 1-Rank DIMM', 'part': '511-1284', 'option': 'SEMX2B2Z'},
            '4096MB': {'desc': '4GB DDR2-667 2-Rank DIMM', 'part': '501-7793', 'option': 'SEMX2C1Z'},
            '8096MB': {'desc': '8GB DDR2-667 2-Rank DIMM', 'part': '511-1379', 'option': 'SEMX2D1Z'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'm9000')
        self.genericIo(data, ['0'])
        self.genericMem(data, memMap, 'm9000')

    ##########################################################################
    def sun_v125(self):
        self['numslots'] = 1
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Devices ==', '', self.parseIo),
            'hwrev': ('', '== HW Revisions ==', ''),
            'memconf': ('', '== Memory Configuration ==', ''),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            'SUNW,UltraSPARC-IIIi @ 1002': {},
        }
        memMap = {
            1024: {'desc': '256MB DIMM', 'part': '370-4237', 'option': 'X7091A', 'qty': 4, 'size': '256MB'},
            # 2048: { 'desc':'512MB DIMM', 'part':'370-4281', 'option':'X7092A', 'qty':4, 'size':'512MB'},
            # 4096: { 'desc':'1GB DIMM', 'part':'370-4874', 'option':'X7093A',
            # 'qty':4, 'size':'1GB'},
        }
        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'V125')
        self.genericIo(data, ['MB'])
        self.genericMem(data, memMap, 'v125')

    ##########################################################################
    def sun_v120(self):
        self['numslots'] = 1
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'hwrev': ('', '== HW Revisions ==', ''),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            '13 @ 648': {'desc': '650MHz UltraSPARC IIi', 'part': '375-3199'},
            '13 @ 548': {'desc': '550MHz UltraSPARC IIi', 'part': '375-3198'},
        }
        memMap = {
            1024: {'desc': '256MB DIMM', 'part': '370-4237', 'option': 'X7091A', 'qty': 4, 'size': '256MB'},
            2048: {'desc': '512MB DIMM', 'part': '370-4281', 'option': 'X7092A', 'qty': 4, 'size': '512MB'},
            4096: {'desc': '1GB DIMM', 'part': '370-4874', 'option': 'X7093A', 'qty': 4, 'size': '1GB'},
        }
        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'V120')
        self.genericIo(data, ['5', '12'])
        self.genericMem(data, memMap, 'v120')

    ##########################################################################
    def sun_blade100(self):
        self['numslots'] = 3
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Devices ==', '', self.parseIo),
            'mem': ('', '== Memory Configuration ==', '', self.parseMem),
            'environ': ('', '== Environmental Status ==', ''),
            'usb': ('', '== usb Devices ==', ''),
            'hwrev': ('', '== HW Revisions ==', ''),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            'US-IIe @ 502': {'desc': '500MHz UltraSPARC IIe Module', 'part': ['100-6471', '100-7270']},
            'SUNW,UltraSPARC-IIe @ 502': {'desc': '500MHz UltraSPARC IIe Module', 'part': ['100-6471', '100-7270']}
        }
        memMap = {
            '128MB': {'desc': '128MB SDRAM DIMM', 'option': 'X6991A', 'part': '370-4149', 'size': '128MB'},
            '256MB': {'desc': '256MB SDRAM DIMM', 'option': 'X6992A', 'part': '370-4150', 'size': '256MB'},
            '512MB': {'desc': '512MB SDRAM DIMM', 'option': 'X6993A', 'part': '370-4151', 'size': '512MB'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'blade100')
        self.genericMem(data, memMap, 'blade100')
        self.genericIo(data, ['7', '8', '12', '13', '19', '+s/system-board'])
        self.addPart(desc='Mitac 200 Watt Power Supply', part='370-4206')
        self.addPart(desc='0MB FRU w/o UltraSPARC IIe', part='375-3061')

    ##########################################################################
    def sun_blade150(self):
        # self['numslots']=3
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Devices ==', '', self.parseIo),
            'mem': ('', '== Memory Configuration ==', '', self.parseMem),
            'environ': ('', '== Environmental Status ==', ''),
            'usb': ('', '== usb Devices ==', ''),
            'hwrev': ('', '== HW Revisions ==', ''),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            'US-IIe @ 550': {'desc': '550MHz UltraSPARC IIi', 'part': '527-1024'},
            'SUNW,UltraSPARC-IIe @ 550': {'desc': '550MHz UltraSPARC IIi', 'part': '527-1024'},
        }
        memMap = {
            '128MB': {'desc': '128MB SDRAM DIMM', 'part': '370-5676', 'option': 'X6179A'},
            '256MB': {'desc': '256MB SDRAM DIMM', 'part': '370-5677', 'option': 'X6180A'},
            '512MB': {'desc': '512MB SDRAM DIMM', 'part': '370-5678', 'option': 'X6181A'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'blade150')
        self.genericMem(data, memMap, 'blade150')
        self.genericIo(data, ['7', '8', '12', '13', '19', '+s/system-board'])

    ##########################################################################
    def sun_blade1000(self):
        self['numslots'] = 4
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Devices ==', '', self.parseIo),
            'memconf': ('', '== Memory Configuration ==', ''),
            # 'mem': ('Bank Table:', '', '', self.parseMem),     # TODO
            'environ': ('', '== Environmental Status ==', ''),
            'usb': ('', '== usb Devices ==', ''),
            'hwrev': ('', '== HW Revisions ==', ''),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            'SUNW,UltraSPARC-III+ @ 1015': {'desc': '1015MHz UltraSPARC III Cu Module', 'part': '501-6395', 'option': 'X7064A'},
        }
        memMap = {
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'blade1000')
        self.genericMem(data, memMap, 'blade1000')
        self.genericIo(data, ['+s/system-board'])

    ##########################################################################
    def sun_blade2000(self):
        self['numslots'] = 4
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Devices ==', '', self.parseIo),
            'memconf': ('', '== Memory Configuration ==', ''),
            # 'mem': ('Bank Table:', '', '', self.parseMem),     # TODO
            'environ': ('', '== Environmental Status ==', ''),
            'usb': ('', '== usb Devices ==', ''),
            'hwrev': ('', '== HW Revisions ==', ''),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            'SUNW,UltraSPARC-III+ @ 1015': {'desc': '1015MHz UltraSPARC III Cu Module', 'part': '501-6395', 'option': 'X7064A'},
        }
        memMap = {
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'blade2000')
        self.genericMem(data, memMap, 'blade2000')
        self.genericIo(data, ['+s/system-board'])

    ##########################################################################
    def sun_t1000(self):
        memMap = {
            'DDR2 SDRAM, 512 MB': {'desc': '1GB (2 x 512MB DDR2)', 'part': '370-6207', 'option': 'X7800A'},
            'DDR2 SDRAM, 1024 MB': {'desc': 'DDR2 SDRAM, 1024 MB', 'part': '370-6208', 'option': 'X7801A'},
            'DDR2 SDRAM, 2048 MB': {'desc': 'DDR2 SDRAM, 2048 MB', 'part': '370-6209', 'option': 'X7802A'},
        }
        modeDict = {
            'cpu': ('', '== Virtual CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Configuration ==', '', self.parseIo),
            'environ': ('', '== Environmental Status ==', ''),
            'hwrev': ('', '== HW Revisions ==', ''),
        }
        if self.exists('sysconfig/prtdiag-v.out'):
            self.sun_t2000_prtdiag()
        self.sun_t2000_tx000()
        self.generic_tx000_showfru('t1000', memMap)
        data = self.genericPrtdiag(modeDict)
        self.genericIo(data, ['MB'])

    ##########################################################################
    def sun_t2000(self):
        memMap = {
            'DDR2 SDRAM, 512 MB': {'desc': '1GB (2 x 512MB DDR2)', 'part': '370-6207', 'option': 'X7800A'},
            'DDR2 SDRAM, 1024 MB': {'desc': 'DDR2 SDRAM, 1024 MB', 'part': '370-6208', 'option': 'X7801A'},
            'DDR2 SDRAM, 2048 MB': {'desc': 'DDR2 SDRAM, 2048 MB', 'part': '370-6209', 'option': 'X7802A'},
        }
        if self.exists('sysconfig/prtdiag-v.out'):
            self.sun_t2000_prtdiag()
        self.sun_t2000_tx000()
        self.generic_tx000_showfru('t2000', memMap)

    ##########################################################################
    def sun_t2000_tx000(self):
        mode = 'unknown'
        modeDict = {
            'temp': ('System Temperatures', '', ''),
            'indicat': ('System Indicator Status', '', ''),
            'disks': ('System Disks:', '', ''),
            'fans': ('Fans Status:', '', ''),
            'voltage': ('Voltage sensors', '', ''),
            'psu': ('Power Supplies', '', ''),
            'load': ('System Load', '', ''),
            'current': ('Current sensors', '', ''),
        }

        data = self.genericPrtdiag(modeDict)

        f = self.open('Tx000/showenvironment')
        for line in f:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if mode == 'temp':
                self.genericCheck('Temperature', line, 1, ['-----', 'Status'])
            if mode == 'disks':
                self.genericCheck(
                    'System Disks', line, 1, ['-----', 'Status', 'NOT PRESENT'])
            if mode == 'fans':
                self.genericCheck(
                    'Fans', line, 1, ['-----', 'Sensor', 'Revolution'])
            if mode == 'voltage':
                self.genericCheck('Voltage', line, 1, ['-----', 'Sensor'])
            if mode == 'load':
                self.genericCheck('Load', line, 1, ['-----', 'Sensor'])
            if mode == 'psu':
                self.genericCheck('Power Supply', line, 1, ['-----', 'Supply'])
            if mode == 'current':
                self.genericCheck('Current', line, 1, ['-----', 'Sensor'])
        f.close()

    ##########################################################################
    def sun_t2000_prtdiag(self):
        mode = 'unknown'
        self['numslots'] = 5
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Configuration ==', '', self.parseIo),
            'mem': ('', '== Physical Memory Configuration ==', ''),
            'hwrev': ('', '== HW Revisions ==', ''),
        }
        memMap = {
            #           4096:  { 'desc':'512MB DIMM', 'option':'X7800A', 'part':'370-6207', 'size':'512MB' },
            #           8184:  { 'desc':'8x1GB or 16x512MB DIMM', 'option':['X7801A (1GB DIMM)','X7800A (512MB DIMM)'], 'part':['370-6208 (1GB)', '370-6207 (512MB)'], 'size':'512MB or 1GB' },
            #           8192:  { 'desc':'8x1GB or 16x512MB DIMM', 'option':['X7801A (1GB DIMM)','X7800A (512MB DIMM)'], 'part':['370-6208 (1GB)', '370-6207 (512MB)'], 'size':'512MB or 1GB' },
            #           16376:  { 'desc':'8x2GB or 16x1GB DIMM', 'option':['X7801A (1GB DIMM)', 'X7802A (2GB DIMM)'], 'part':['370-6208 (1GB)', '370-6209 (2GB)'], 'size':'1GB or 2GB' },
            #           32640: { 'desc': '8x4GB or 16x2GB DIMM', 'option':['X7802A (2GB DIMM)', 'X7803A (4GB DIMM)'], 'part':['370-6209 (2GB)', '370-6210 (4GB)'], 'size':'2GB or 4GB'},
            #           32760: { 'desc': '8x4GB or 16x2GB DIMM', 'option':['X7802A (2GB DIMM)', 'X7803A (4GB DIMM)'], 'part':['370-6209 (2GB)', '370-6210 (4GB)'], 'size':'2GB or 4GB'},
            # 65536:  { 'desc':'4GB DIMM', 'option':'X7803A',
            # 'part':'370-6210', 'qty':16, 'size':'4GB' },
        }

        data = self.genericPrtdiag(modeDict)
        self.genericIo(data, ['IOBD'])
        return

        if speed == '1000':
            if numcore == 16:
                self.addCpu(desc='4 Core 1.0GHz System Board', part='541-2409')
            elif numcore == 24:
                self.addCpu(desc='6 Core 1.0GHz System Board', part='541-2405')
            elif numcore == 32:
                self.addCpu(desc='8 Core 1.0GHz System Board', part='541-2408')
            else:
                self.Warning(
                    "Unhandled number of cores: %d on T2000" % numcore)
        elif speed == '1400':
            self.addCpu(desc='8 Core 1.4GHz System Board', part='541-2436')
        elif not speed:
            pass        # Didn't get CPU data
        else:
            self.Warning("Unhandled CPU speed on SunFire T2000: %s" % speed)

    ##########################################################################
    def sun_v60(self):
        mode = 'unknown'
        numdimms = 0
        self['numslots'] = 3
        modeDict = {
            'cpu': ('', '== Processor Sockets ==', '', self.parseCpu),
            'mem': ('', '== Memory Device Sockets ==', ''),
            'obd': ('', '== On-Board Devices ==', ''),
        }

        data = self.genericPrtdiag(modeDict)
        self.Fatal(
            "Yet to be refactored ################################################################################")
        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if mode == 'iocards':
                pass
            if mode == 'cpu':
                if self.skipLine(line, ['Version', '----']):
                    continue
                self.foundCpu = True
                if '3.06GHz' in line:
                    self.addCpu(
                        desc='3.06GHz Xeon CPU', option='5121A', part='370-6045')
                elif '2.8GHz' in line:
                    self.addCpu(
                        desc='2.86GHz Xeon CPU', option='5120A', part='370-6044')
                elif '3.2GHz' in line:
                    self.addCpu(
                        desc='3.26GHz Xeon CPU', option='5138A', part='370-6458')
                else:
                    self.Warning("Unhandled CPU in V60: %s" % line)
            if mode == 'mem':
                if 'in use' in line:
                    numdimms += 1

        self.addMem(desc='Unknown dimm', qty=numdimms, option=[
                    '5122A (256MB DIMM)', '5123A (512MB DIMM)', '5124A (1GB DIMM)'], size='256MB or 512MB or 1GB')

    ##########################################################################
    def sun_v100(self):
        mode = 'unknown'
        self['numslots'] = 0
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', ''),      # No cards possible
            'hwrev': ('', '== HW Revisions ==', ''),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            '13 @ 500': {'desc': 'Sun Fire V100 Motherboard (500MHz)', 'part': '375-3090'},
            '13 @ 548': {'desc': 'Sun Fire V100 Motherboard (550MHz)', 'part': '375-3110'},
            '13 @ 550': {'desc': 'Sun Fire V100 Motherboard (550MHz)', 'part': '375-3110'},
            '13 @ 648': {'desc': 'Sun Fire V100 Motherboard (650MHz)', 'part': '375-3115'},
            '13 @ 650': {'desc': 'Sun Fire V100 Motherboard (650MHz)', 'part': '375-3115'},
        }
        memMap = {
            512: {'desc': '128MB DIMM', 'option': 'X7090A', 'part': '370-4289', 'qty': 4, 'size': '128MB'},
            1024: {'desc': '256MB DIMM', 'option': 'X7091A', 'part': '370-4237', 'qty': 4, 'size': '256MB'},
            2048: {'desc': '512MB DIMM', 'option': 'X7092A', 'part': '370-4281', 'qty': 4, 'size': '512MB'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'v100')
        self.genericMem(data, memMap, 'v100')
        self.addPart(desc='80W AC Input Power Supply', part='370-4363')
        # All cards are in the motherboard, no expandability
        self.foundIo = True

    ##########################################################################
    def sun_x1(self):
        self['numslots'] = 0
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', ''),
            'hwrev': ('', '== HW Revisions ==', ''),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            '13 @ 400': {'desc': '400MHz UltraSPARC IIe', 'part': '375-3015'},
            '13 @ 500': {'desc': '500MHz UltraSPARC IIe', 'part': '375-3058'},
        }
        memMap = {
            512: {'desc': '128MB DIMM', 'part': '370-4289', 'option': 'X7090A', 'qty': 4, 'size': '128MB'},
            1024: {'desc': '256MB DIMM', 'part': '370-4237', 'option': 'X7091A', 'qty': 4, 'size': '256MB'},
            2048: {'desc': '512MB DIMM', 'part': '370-4281', 'option': 'X7092A', 'qty': 4, 'size': '512MB'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'x1')
        self.genericMem(data, memMap, 'x1')
        self.foundIo = True       # No additional cards can be installed

    ##########################################################################
    def sun_e220r(self):
        self['numslots'] = 4
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'hwrev': ('', '== HW Revisions ==', ''),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            'US-II @ 360': {'desc': '360MHz UltraSPARC II Module', 'option': 'X1192A', 'part': '501-5552'},
            'US-II @ 450': {'desc': '450MHz UltraSPARC II Module', 'option': 'X1195A', 'part': '501-6071'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'e220r')
        self.genericIo(data, ['On-Board'])
        self.addPart(desc='System Board', part='501-5606')
        self.addPart(
            desc='Lucent 380 Watt Power Supply', option='X9684A', part='300-1449')
        self.addMem(desc='Unknown dimm size (%s)' % data['memsize'], option=[
                    'X7002A (32MB DIMM)', 'X7003A (64MB DIMM)', 'X7004A (128MB DIMM)'], part=['501-2622 (32MB)', '501-2480 (64MB)', '501-3136 (128MB)'])

    ##########################################################################
    def sun_e420r(self):
        self['numslots'] = 4
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'hwrev': ('', '== HW Revisions ==', ''),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            "US-II @ 450": {'desc': "450MHz UltraSPARC II Module", 'part': "501-6071", 'option': "X1195A"},
        }
        self.addPart(desc="System Board", part="501-5168")
        self.addPart(desc="Lucent 380 Watt Power Supply",
                     part="300-1449", option="X9684A", qty=2)
        self.addPart(desc="DC Power Distribution Board", part="501-5506")
        self.addPart(desc="125 Watt DC-DC Converter with Fan", part="300-1407")

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'e420r')
        self.genericIo(data, ['On-Board'])

    ##########################################################################
    def sun_t1(self):
        self['numslots'] = 1
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'hwrev': ('', '== HW Revisions ==', ''),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            '12 @ 440': {'desc': 'System Board (440MHz CPU)', 'part': '540-4258'},
            '13 @ 296': {'desc': '300MHz UltraSPARC II Module', 'part': '501-4849', 'option': 'X1191A'},
            '13 @ 360': {'desc': 'System Board (360MHz CPU)', 'part': '540-4260'},
            '13 @ 500': {'desc': 'System Board (500MHz UltraSPARC IIe)', 'part': '375-0132'},

            'US-II @ 296': {'desc': '300MHz UltraSPARC II Module', 'part': '501-4849', 'option': 'X1191A'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 't1')
        self.genericIo(data, ['5', '8', '12', '13'])

    ##########################################################################
    def sun_ultra1(self):
        self['numslots'] = 3
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            'US-II @ 296': {'desc': '296MHz CPU', 'part': '501-4849'},
        }
        memMap = {
            512: {'desc': '512Mb RAM (4x128Mb)', 'part': '501-3136', 'option': 'X7004A'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'ultra2')
        self.genericMem(data, memMap, 'ultra2')
        self.genericIo(data, ['14'])

    ##########################################################################
    def sun_ultra2(self):
        self['numslots'] = 3
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            'US-I @ 167': {'desc': '167MHz CPU'},
        }
        memMap = {
            128: {'desc': '128Mb RAM'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'ultra1')
        self.genericMem(data, memMap, 'ultra1')
        self.genericIo(data, ['14'])

    ##########################################################################
    def sun_ultra5(self):
        mode = 'unknown'
        self['numslots'] = 3
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            '270': {'desc': '270MHz UltraSPARC IIi Module', 'part': '501-5039'},
            '12 @ 300': {'desc': '300MHz UltraSPARC IIi Module', 'part': '501-5040'},
            '12 @ 333': {'desc': '333MHz UltraSPARC IIi Module', 'part': '501-5568'},
        }
        memMap = {
            128: {'desc': '128MB DIMM, 50ns', 'part': '370-3798', 'option': 'X7038A'},
        }
        data = self.genericPrtdiag(modeDict)

        self.genericCpu(data, cpuMap, 'ultra5')
        self.genericMem(data, memMap, 'ultra5')
        self.genericIo(data)

    ##########################################################################
    def sun_ultra80(self):
        self['numslots'] = 4
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            'US-II @ 450': {'desc': '450MHz UltraSPARC II Module', 'part': '501-6071', 'option': 'X1195A'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'ultra80')
        self.genericIo(data, ['On-Board'])

    ##########################################################################
    def sun_ultra45(self):
        # self['numslots']=4
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            #'US-II @ 450': { 'desc':'450MHz UltraSPARC II Module','option':'X1195A', 'part':'501-6071' },
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'ultra45')
        self.genericIo(data)

    ##########################################################################
    def sun_ultra60(self):
        self['numslots'] = 4
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            'US-II @ 296': {'desc': '296MHz UltraSPARC II Module', 'option': 'Unknown', 'part': 'Unknown'},
            'US-II @ 300': {'desc': '300MHz UltraSPARC II Module', 'option': 'X1191A', 'part': '501-4849'},
            'US-II @ 360': {'desc': '360MHz UltraSPARC II Module', 'option': 'X1192A', 'part': '501-5552'},
            'US-II @ 450': {'desc': '450MHz UltraSPARC II Module', 'option': 'X1195A', 'part': '501-6071'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'ultra60')
        self.genericIo(data)

    ##########################################################################
    def sun_cp1500(self):
        """ These aren't real hosts - rather they are attachments to a 15k or equivalent
        """
        mode = 'unknown'
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', ''),
            'hwrev': ('', '== HW Revisions', ''),
            'nofailures': ('No failures found', '', ''),
        }
        data = self.genericPrtdiag(modeDict)

        self.foundCpu = True
        self.foundMem = True
        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if mode == 'iocards':
                if '-----' in line or 'Name' in line or 'Freq' in line:
                    continue
                bits = line.split()
                if not bits:
                    continue
                self.foundIo = True
                model = " ".join(bits[4:])
                loc = self.getLoc(board=bits[0], bus=bits[1], slot=bits[3])
                self.addCard(
                    loc, rawmodel=model, board=bits[0], bus=bits[1], freq=bits[2], slot=bits[3])
        fh.close()

    ##########################################################################
    def sun_cp2000(self):
        """ These aren't real hosts - rather they are attachments to a 25k or equivalent
        """
        mode = 'unknown'
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', ''),
            'hwrev': ('', '== HW Revisions', ''),
            'nofailures': ('No failures found', '', ''),
        }
        data = self.genericPrtdiag(modeDict)

        self.foundCpu = True
        self.foundMem = True
        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if mode == 'iocards':
                if '-----' in line or 'Name' in line or 'Freq' in line:
                    continue
                bits = line.split()
                if not bits:
                    continue
                self.foundIo = True
                model = " ".join(bits[4:])
                loc = self.getLoc(board=bits[0], bus=bits[1], slot=bits[3])
                self.addCard(
                    loc, rawmodel=model, board=bits[0], bus=bits[1], freq=bits[2], slot=bits[3])
        fh.close()

    ##########################################################################
    def sun_x4500(self):
        mode = 'unknown'
        self['numslots'] = 8
        modeDict = {
            'processor': ('', '== Processor Sockets ==', ''),
            'memory': ('', '== Memory Device Sockets ==', ''),
            'devices': ('', '== On-Board Devices ==', ''),
            'upgrade': ('', '== Upgradeable Slots ==', ''),
        }
        memMap = {
            '2048MB DDR-II 666 (PC2 5300)': {'desc': '2048MB DDR-II 666 (PC2 5300)', 'option': 'X8122A-Z', 'part': '371-2203', 'size': '2GB'},
            '2048MB DDR 400 (PC3200) ECC': {'desc': '2048MB DDR 400 (PC3200) ECC', 'option': 'X8121A-Z', 'part': '594-2687', 'size': '2GB'},
            '4096MB DDR-II 666 (PC2 5300)': {'desc': '4096MB DDR-II 666 (PC2 5300)', 'option': 'X8098A', 'part': '371-4307', 'size': '4GB'},
        }

        self.addPart(
            desc='Graphics Redirect and Service Processor (GRASP) board', part='501-7382')
        self.addPart(desc='System Motherboard', part='501-7588')
        self.addPart(desc='Power Distribution Board', part='501-7052')
        self.addPart(desc='Power Supply 850 or 950W', option=[
                     'X4094A', 'N/A'], part=['300-2013', '300-1971'])
        self.addPart(desc='Fan Assembly', part='371-0094')
        self.addPart(desc='Disk Backplane', part='501-7049')

        ipmi = self.parseIpmi()
        for pnum in range(8):
            for dnum in range(8):
                i = "p%d.d%d" % (pnum, dnum)
                if i not in ipmi:
                    continue
                if ipmi[i]:
                    self.foundMem = True
                    desc = ipmi[i]['Product Name'].replace(
                        ' ADDRESS/COMMAND PARITY/ECC', '')
                    if desc not in memMap:
                        self.Warning(
                            "Unhandled x4500 memory configuration %s" % desc)
                    else:
                        self.addMem(**memMap[desc])
                    if True:
                        pass
                    elif '1024MB DDR 400' in desc:
                        option = 'X8120A-Z'
                        part = '594-2686'
                        size = '1GB'
                    else:
                        self.Warning("Unhandled Mem on X4500: %s" % desc)
                        self.addMem(
                            desc=desc, option=option, part=part, size=size)

        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if mode == 'processor':
                if self.skipLine(line, ['-----', 'Location Tag']):
                    continue
                tag = line.split()[-1]
                version = " ".join(line.split()[:-2])
                self['cpu_%s' % tag] = version
                if not self.handleXcpu(line):
                    self.Warning("Unknown X4500 CPU '%s'" % line)

            if mode == 'upgrade':
                if 'in use' in line:
                    pass

    ##########################################################################
    def sun_x4600(self):
        mode = 'unknown'
        self['numslots'] = 8
        modeDict = {
            'processor': ('', '== Processor Sockets ==', ''),
            'memory': ('', '== Memory Device Sockets ==', ''),
            'devices': ('', '== On-Board Devices ==', ''),
            'upgrade': ('', '== Upgradeable Slots ==', ''),
        }
        memMap = {
            '2048MB DDR-II 666 (PC2 5300)': {'desc': '2048MB DDR-II 666 (PC2 5300)', 'option': 'X8122A-Z', 'part': '371-2203', 'size': '2GB'},
            '2048MB DDR 400 (PC3200) ECC': {'desc': '2048MB DDR 400 (PC3200) ECC', 'option': 'X8121A-Z', 'part': '594-2687', 'size': '2GB'},
            '4096MB DDR-II 666 (PC2 5300)': {'desc': '4096MB DDR-II 666 (PC2 5300)', 'option': 'X8098A', 'part': '371-4307', 'size': '4GB'},
        }

        self.addPart(
            desc='Graphics Redirect and Service Processor (GRASP) board', part='501-7382')
        self.addPart(desc='System Motherboard', part='501-7588')
        self.addPart(desc='Power Distribution Board', part='501-7052')
        self.addPart(desc='Power Supply 850 or 950W', option=[
                     'X4094A', 'N/A'], part=['300-2013', '300-1971'])
        self.addPart(desc='Fan Assembly', part='371-0094')
        self.addPart(desc='Disk Backplane', part='501-7049')

        ipmi = self.parseIpmi()
        for pnum in range(8):
            for dnum in range(8):
                i = "p%d.d%d" % (pnum, dnum)
                if i not in ipmi:
                    continue
                if ipmi[i]:
                    self.foundMem = True
                    desc = ipmi[i]['Product Name'].replace(
                        ' ADDRESS/COMMAND PARITY/ECC', '')
                    if desc not in memMap:
                        self.Warning(
                            "Unhandled x4600 memory configuration %s" % desc)
                    else:
                        self.addMem(**memMap[desc])
                    if True:
                        pass
                    elif '1024MB DDR 400' in desc:
                        option = 'X8120A-Z'
                        part = '594-2686'
                        size = '1GB'
                    else:
                        self.Warning("Unhandled Mem on X4600: %s" % desc)
                        self.addMem(
                            desc=desc, option=option, part=part, size=size)

        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if mode == 'processor':
                if self.skipLine(line, ['-----', 'Location Tag']):
                    continue
                tag = line.split()[-1]
                version = " ".join(line.split()[:-2])
                self['cpu_%s' % tag] = version
                if not self.handleXcpu(line):
                    self.Warning("Unknown X4600 CPU '%s'" % line)

            if mode == 'upgrade':
                if 'in use' in line:
                    pass

    ##########################################################################
    def sun_x4200(self):
        mode = 'unknown'
        numslots = 5
        modeDict = {
            'processor': ('', '== Processor Sockets ==', ''),
            'memory': ('', '== Memory Device Sockets ==', ''),
            'devices': ('', '== On-Board Devices ==', ''),
            'upgrade': ('', '== Upgradeable Slots ==', ''),
        }
        memMap = {
            '2048MB DDR-II 666 (PC2 5300)': {'desc': '2048MB DDR 667 (PC5300)', 'option': 'X4226A-Z', 'part': '371-1920', 'size': '2GB', },
            '2048MB DDR 400 (PC3200) ECC': {'desc': '2048MB DDR 400 (PC3200) ECC', 'option': 'X8023A', 'part': '371-0073', 'size': '2GB', },
            '1024MB DDR 400 (PC3200) ECC': {'desc': '1024MB DDR 400 (PC3200) ECC', 'option': 'X8022A', 'part': '371-0072', 'size': '1GB', },
        }
        self.addPart(desc='Server Fan Board', part='501-6917')
        self.addPart(desc='Fan Module', part='541-0269')
        self.addPart(desc='Rear Fan Tray', part='541-0645')

        ipmi = self.parseIpmi()
        for i in ipmi:
            if not ipmi[i]:
                continue
            if i.startswith('p0.') or i.startswith('p1.'):
                self.foundMem = True
                desc = ipmi[i]['Product Name'].replace(
                    ' ADDRESS/COMMAND PARITY/ECC', '')
                if desc not in memMap:
                    self.Warning(
                        "Unhandled x4200 memory configuration %s" % desc)
                else:
                    self.addMem(**memMap[desc])
#               if '1024MB DDR 400' in desc:
#                   option='X8022A'
#                   part='371-0072'
#                   size='1GB'

        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if mode == 'processor':
                if not line or '-------' in line or 'Location Tag' in line:
                    continue
                tag = line.split()[-1]
                version = " ".join(line.split()[:-2])
                self['cpu_%s' % tag] = version

                if not self.handleXcpu(line):
                    self.Warning("Unknown X4200 CPU '%s'" % line)
            if mode == 'upgrade':
                if 'in use' in line:
                    pass

    ##########################################################################
    def sun_x4140(self):
        mode = 'unknown'
        self['numslots'] = 3
        modeDict = {
            'processor': ('', '== Processor Sockets ==', ''),
            'memory': ('', '== Memory Device Sockets ==', ''),
            'devices': ('', '== On-Board Devices ==', ''),
            'upgrade': ('', '== Upgradeable Slots ==', ''),
        }
        memMap = {
            '2048MB DDR-II 666 (PC2 5300)': {'desc': '2048MB DDR-II 666 (PC2 5300)', 'option': 'X6321A', 'part': '540-7599', 'size': '2GB', },
            '4096MB DDR-II 666 (PC2 5300)': {'desc': '4096MB DDR-II 666 (PC2 5300)', 'option': 'X6322A', 'part': '540-7600', 'size': '2GB'},
        }

        ipmi = self.parseIpmi()
        for pnum in range(8):
            for dnum in range(8):
                i = "p%d.d%d" % (pnum, dnum)
                if i not in ipmi:
                    continue
                if ipmi[i]:
                    self.foundMem = True
                    desc = ipmi[i]['Product Name'].replace(
                        ' ADDRESS/COMMAND PARITY/ECC', '')
                    if desc not in memMap:
                        self.Warning(
                            "Unhandled x4140 memory configuration %s" % desc)
                    else:
                        self.addMem(**memMap[desc])
#                   elif '4096MB DDR-II 666' in desc:
#                       option='X6322A'
#                       part='540-7600'
#                       size='4GB'
#                   else:
#                       self.Warning("Unhandled Mem on X4140: %s" % desc)
#                   self.addMem(desc=desc, option=option, part=part, size=size)

        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if mode == 'processor':
                if not line or '-------' in line or 'Location Tag' in line:
                    continue
                tag = line.split()[-1]
                version = " ".join(line.split()[:-2])
                self['cpu_%s' % tag] = version
                if not self.handleXcpu(line):
                    self.Warning("Unknown X4140 CPU '%s'" % line)
            if mode == 'upgrade':
                if 'in use' in line:
                    pass

    ##########################################################################
    def sun_t4(self):
        mode = 'unknown'
        self['numslots'] = 0
        modeDict = {
            'cpu': ('', '== Virtual CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Devices ==', '', self.parseIo),
            'environ': ('', '== Environmental Status ==', ''),
            'fan': ('Fan sensors', '', ''),
            'temp': ('Temperature sensors', '', ''),
            'tempind': ('Temperature indicators', '', ''),
            'current': ('Current sensors', '', ''),
            'currentind': ('Current indicators', '', ''),
            'voltage': ('Voltage sensors', '', ''),
            'voltageind': ('Voltage indicators', '', ''),
            'led': ('LEDs', '', ''),
            'fru': ('', '== FRU Status ==', ''),
            'hwrev': ('', '== FW Revisions ==', ''),
        }
        if self.exists('sysconfig/prtdiag-v.out'):
            fh = self.open('sysconfig/prtdiag-v.out')
            for line in fh:
                line = line.strip()
                mode, skip = self.modeSelect(mode, line, modeDict)
                if skip:
                    continue
                if mode == 'fan':
                    self.genericCheck(
                        'Fan', line, 2, ['Location', '-------', '======'])
                if mode == 'temp':
                    self.genericCheck(
                        'TempSensor', line, 2, ['Location', '-------', '======'])
                if mode == 'tempind':
                    self.genericCheck(
                        'TempIndicator', line, 2, ['Location', '-------', '======'])
                if mode == 'current':
                    self.genericCheck(
                        'CurrentSensor', line, 2, ['Location', '-------', '======'])
                if mode == 'currentind':
                    self.genericCheck(
                        'CurrentIndicator', line, 2, ['Location', '-------', '======'])
                if mode == 'voltage':
                    self.genericCheck(
                        'VoltageSensor', line, 2, ['Location', '-------', '======'])
                if mode == 'voltageind':
                    self.genericCheck(
                        'VoltageIndicator', line, 2, ['Location', '-------', '======'])
                if mode == 'fru':
                    self.genericCheck(
                        'FRU', line, [1, 2], ['Location', '-------', '======'])

    ##########################################################################
    def sun_x6220(self):
        mode = 'unknown'
        self['numslots'] = 0
        modeDict = {
            'processor': ('', '== Processor Sockets ==', ''),
            'memory': ('', '== Memory Device Sockets ==', ''),
            'devices': ('', '== On-Board Devices ==', ''),
            'upgrade': ('', '== Upgradeable Slots ==', ''),
        }
        memMap = {
            '1024MB DDR-II 666 (PC2 5300)': {'desc': '1024MB DDR-II 666 (PC2 5300)', 'option': 'X4298A', 'part': '540-7255', 'size': '2GB'}
        }

        ipmi = self.parseIpmi()
        for i in ipmi:
            if not ipmi[i]:
                continue
            if i.startswith('p0.') or i.startswith('p1.'):
                desc = ipmi[i]['Product Name'].replace(
                    ' ADDRESS/COMMAND PARITY/ECC', '')
                if desc not in memMap:
                    self.Warning(
                        "Unhandled x6220 memory configuration %s" % desc)
                else:
                    self.addMem(**memMap[desc])
                self.foundMem = True

        if self.exists('sysconfig/prtdiag-v.out'):
            fh = self.open('sysconfig/prtdiag-v.out')
            for line in fh:
                line = line.strip()
                mode, skip = self.modeSelect(mode, line, modeDict)
                if skip:
                    continue
                if mode == 'processor':
                    if not line or '-------' in line or 'Location Tag' in line:
                        continue
                    tag = line.split()[-1]
                    version = " ".join(line.split()[:-2])
                    self['cpu_%s' % tag] = version
                    if not self.handleXcpu(line):
                        self.Warning("Unknown X6220 CPU '%s'" % line)
                if mode == 'upgrade':
                    if 'in use' in line:
                        pass

    ##########################################################################
    def sun_x2100(self):
        mode = 'unknown'
        self['numslots'] = 2
        modeDict = {
            'processor': ('', '== Processor Sockets ==', ''),
            'memory': ('', '== Memory Device Sockets ==', ''),
            'devices': ('', '== On-Board Devices ==', ''),
            'upgrade': ('', '== Upgradeable Slots ==', ''),
        }
        memMap = {}

        ipmi = self.parseIpmi()
        for i in ipmi:
            if not ipmi[i]:
                continue
            if i.startswith('p0.') or i.startswith('p1.'):
                desc = ipmi[i]['Product Name'].replace(
                    ' ADDRESS/COMMAND PARITY/ECC', '')
                if desc not in memMap:
                    self.Warning(
                        "Unhandled x2100 memory configuration %s" % desc)
                else:
                    self.addMem(**memMap[desc])
                self.foundMem = True
                if '2048MB DDR 400' in desc:
                    option = 'X8023A'
                    part = '371-0073'
                    size = '2GB'
                elif '1024MB DDR 400' in desc:
                    option = 'X8022A'
                    part = '371-0072'
                    size = '1GB'
                elif '4096MB DDR 400' in desc:
                    option = 'X8024A'
                    part = '371-1460'
                    size = '4GB'
                elif '1024MB DDR-II 666' in desc:
                    option = 'X4225'
                    part = '371-1919'
                    size = '1GB'
                elif '2048MB DDR-II 666' in desc:
                    option = 'X4226A'
                    part = '371-1920'
                    size = '2GB'
                elif '4096MB DDR-II 666' in desc:
                    option = 'X4233A'
                    part = '371-4322'
                    size = '4GB'
                else:
                    self.Warning("Unhandled Mem on X2100: %s" % desc)
                self.addMem(desc=desc, option=option, part=part, size=size)

        if self.exists('sysconfig/prtdiag-v.out'):
            fh = self.open('sysconfig/prtdiag-v.out')
            for line in fh:
                line = line.strip()
                mode, skip = self.modeSelect(mode, line, modeDict)
                if skip:
                    continue
                if mode == 'processor':
                    if not line or '-------' in line or 'Location Tag' in line:
                        continue
                    tag = line.split()[-1]
                    version = " ".join(line.split()[:-2])
                    self['cpu_%s' % tag] = version
                    if not self.handleXcpu(line):
                        self.Warning("Unknown X2100 CPU '%s'" % line)
                if mode == 'upgrade':
                    if 'in use' in line:
                        pass

    ##########################################################################
    def sun_x2200(self):
        mode = 'unknown'
        self['numslots'] = 2
        modeDict = {
            'processor': ('', '== Processor Sockets ==', ''),
            'memory': ('', '== Memory Device Sockets ==', ''),
            'devices': ('', '== On-Board Devices ==', ''),
            'upgrade': ('', '== Upgradeable Slots ==', ''),
        }
        memMap = {}

        ipmi = self.parseIpmi()
        for i in ipmi:
            if not ipmi[i]:
                continue
            if i.startswith('p0.') or i.startswith('p1.'):
                desc = ipmi[i]['Product Name'].replace(
                    ' ADDRESS/COMMAND PARITY/ECC', '')
                if desc not in memMap:
                    self.Warning(
                        "Unhandled x2200 memory configuration %s" % desc)
                else:
                    self.addMem(**memMap[desc])
                self.foundMem = True
                if '2048MB DDR 400' in desc:
                    option = 'X8023A'
                    part = '371-0073'
                    size = '2GB'
                elif '1024MB DDR 400' in desc:
                    option = 'X8022A'
                    part = '371-0072'
                    size = '1GB'
                elif '4096MB DDR 400' in desc:
                    option = 'X8024A'
                    part = '371-1460'
                    size = '4GB'
                elif '1024MB DDR-II 666' in desc:
                    option = 'X4225'
                    part = '371-1919'
                    size = '1GB'
                elif '2048MB DDR-II 666' in desc:
                    option = 'X4226A'
                    part = '371-1920'
                    size = '2GB'
                elif '4096MB DDR-II 666' in desc:
                    option = 'X4233A'
                    part = '371-4322'
                    size = '4GB'
                else:
                    self.Warning("Unhandled Mem on X2200: %s" % desc)
                self.addMem(desc=desc, option=option, part=part, size=size)

        if self.exists('sysconfig/prtdiag-v.out'):
            fh = self.open('sysconfig/prtdiag-v.out')
            for line in fh:
                line = line.strip()
                mode, skip = self.modeSelect(mode, line, modeDict)
                if skip:
                    continue
                if mode == 'processor':
                    if not line or '-------' in line or 'Location Tag' in line:
                        continue
                    tag = line.split()[-1]
                    version = " ".join(line.split()[:-2])
                    self['cpu_%s' % tag] = version
                    if not self.handleXcpu(line):
                        self.Warning("Unknown X2200 CPU '%s'" % line)
                if mode == 'upgrade':
                    if 'in use' in line:
                        pass

    ##########################################################################
    def vmware(self):
        """ Virtualised server - no cpu or memory or any other details
        are reliable
        """
        return

    ##########################################################################
    def sun_x4100(self):
        mode = 'unknown'
        self['numslots'] = 2
        modeDict = {
            'processor': ('', '== Processor Sockets ==', ''),
            'memory': ('', '== Memory Device Sockets ==', ''),
            'devices': ('', '== On-Board Devices ==', ''),
            'upgrade': ('', '== Upgradeable Slots ==', ''),
        }
        memMap = {
            '1024MB DDR 400 (PC3200) ECC': {'desc': '1024MB DDR 400 (PC3200) ECC', 'option': 'X8022A', 'part': '371-0072', 'size': '1GB'},
            '1024MB DDR-II 666 (PC2 5300)': {'desc': '1024MB DDR-II 666 (PC2 5300)', 'option': 'X4225A-Z', 'part': '371-1919', 'size': '1GB'},
            '4096MB DDR-II 666 (PC2 5300)': {'desc': '4096MB DDR-II 666 (PC2 5300)', 'option': 'X4233A', 'part': '371-4322', 'size': '4GB'},
            '2048MB DDR-II 666 (PC2 5300)': {'desc': '2048MB DDR-II 666 (PC2 5300)', 'option': 'X4226A', 'part': '371-1920', 'size': '2GB'},
            '2048MB DDR 400 (PC3200) ECC': {'desc': '2048MB DDR 400 (PC3200) ECC', 'option': 'X8023A', 'part': '371-0073', 'size': '2GB'},
            '4096MB DDR 400 (PC3200) ECC': {'desc': '4096MB DDR 400 (PC3200) ECC', 'option': 'X8024A', 'part': '371-1460', 'size': '4GB'},
        }

        ipmi = self.parseIpmi()
        for i in ipmi:
            if not ipmi[i]:
                continue
            if i.startswith('p0.') or i.startswith('p1.'):
                self.foundMem = True
                desc = ipmi[i]['Product Name'].replace(
                    ' ADDRESS/COMMAND PARITY/ECC', '')
                if desc not in memMap:
                    self.Warning(
                        "Unhandled x4100 memory configuration %s" % desc)
                else:
                    self.addMem(**memMap[desc])

        if self.exists('sysconfig/prtdiag-v.out'):
            fh = self.open('sysconfig/prtdiag-v.out')
            for line in fh:
                line = line.strip()
                mode, skip = self.modeSelect(mode, line, modeDict)
                if skip:
                    continue
                if mode == 'processor':
                    if not line or '-------' in line or 'Location Tag' in line:
                        continue
                    tag = line.split()[-1]
                    version = " ".join(line.split()[:-2])
                    self['cpu_%s' % tag] = version
                    if not self.handleXcpu(line):
                        self.Warning("Unknown X4100 CPU '%s'" % line)
                if mode == 'upgrade':
                    if 'in use' in line:
                        pass

    ##########################################################################
    def sun_v480(self):
        mode = 'unknown'
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'mem': ('', '== Memory Configuration ==', '', self.parseMem),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'environ': ('', '==  Environmental Status ==', ''),
            'hwrev': ('', '== HW Revisions ==', ''),
            'temp': ('System Temperatures', '', ''),
            'disk': ('Disk Status:', '', ''),
            'fsp': ('Front Status Panel:', '', ''),
            'fan': ('Fan Status', '', ''),
            'psu': ('Power Supplies:', '', ''),
        }
        cpuMap = {
            "US-III+ @ 900": {'desc': 'CPU/Memory Board w/ 2x US III Cu 900MHz', 'part': '501-6676', 'option': 'X7028A'},
            "US-III+ @ 1050": {'desc': 'CPU/Memory Board w/ 2x US III Cu 1050MHz', 'part': '501-6163', 'option': 'X6894A'},
            "US-III+ @ 1200": {'desc': 'CPU/Memory Board w/ 2x US III Cu 1200MHz', 'part': '501-6164', 'option': 'X6895A'},
        }
        memMap = {
            '256MB': {'desc': '1GB (4 x 256MB SDRAM DIMM)', 'option': 'X7053A', 'part': '501-5401', 'size': '256MB'},
            '512MB': {'desc': '2GB (4 x 512MB SDRAM DIMM)', 'option': 'X7051A', 'part': '501-7385', 'size': '512MB'},
            '1024MB': {'desc': '4GB (4 x 1GB SDRAM DIMM)', 'option': 'X7056A', 'part': '501-7386', 'size': '1GB'},
        }
        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'v480')
        self.genericMem(data, memMap, 'v480')
        self.genericIo(data)

        self.addPart(desc='Centerplane', part='501-5819')
        self.addPart(desc='2-Slot FC-AL Disk Backplane', part='501-5822')
        self.addPart(desc='PCI I/O Riser Board', part='501-5820')
        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue

            if mode == 'temp':
                self.genericCheck(
                    'Temp', line, 2, ['Status', '-------', '======'])
            if mode == 'disk':
                self.genericCheck('Disk', line, 2, ['-----', '======='])
            if mode == 'fan':
                self.genericCheck(
                    'Fan', line, 3, ['Status', '-----', '======='])
            if mode == 'psu':
                self.genericCheck(
                    'Power Supply', line, 1, ['Status', '-----', '======='])
                if line.startswith('PS'):
                    self.addPart(
                        desc='Tyco 1184 Watt Power Supply', part='300-1480')
        fh.close()

    ##########################################################################
    def sun_280r(self):
        mode = 'unknown'
        self['numslots'] = 4
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'mem': ('', '== Memory Configuration ==', '', self.parseMem),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'environ': ('', '== Environmental Status ==', ''),
            'hwrev': ('', '== HW Revisions ==', ''),
            'disk': ('Disk Status:', '', ''),
            'fan': ('Fan Bank', '', ''),
            'psu': ('Power Supplies:', '', ''),
        }
        cpuMap = {
            'US-III @ 750': {'desc': '750MHz UltraSPARC III Cu Module', 'option': 'X6990A', 'part': '501-5675'},
            'US-III+ @ 750': {'desc': '750MHz UltraSPARC III Cu Module', 'option': 'X6990A', 'part': '501-5675'},
            'US-III+ @ 900': {'desc': '900MHz UltraSPARC III Cu Module', 'option': 'X7009A', 'part': '501-6747'},
            'US-III+ @ 1200': {'desc': '1200MHz UltraSPARC III Cu Module', 'option': 'X7310A', 'part': '501-6750'},
        }
        memMap = {
            '128MB': {'desc': '512MB (4 x 128MB SDRAM DIMMs)', 'option': 'X7050A', 'part': '501-4489', 'size': '128MB'},
            '256MB': {'desc': '1 GB (4 x 256MB SDRAM DIMMs)', 'option': 'X7053A', 'part': '501-5401', 'size': '256MB'},
            '512MB': {'desc': '2 GB (4 x 512MB SDRAM DIMMs)', 'option': 'X7051A', 'part': '501-7385', 'size': '512MB'},
            '1024MB': {'desc': '4 GB (4 x 1GB SDRAM DIMMs)', 'option': 'X7052A', 'part': '501-5031', 'size': '1024MB'},
        }
        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'e280r')
        self.genericMem(data, memMap, 'e280r')
        self.genericIo(data)

        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if mode == 'disk':
                self.genericCheck(
                    'Disk', line, 3, ['Presence', '-----', '======='])
            if mode == 'fan':
                self.genericCheck(
                    'Fan', line, 1, ['Status', '-----', '======='])
            if mode == 'psu':
                self.genericCheck(
                    'Power Supply', line, 1, ['Status', '-----', '======='])
        fh.close()

    ##########################################################################
    def sun_v490(self):
        mode = 'unknown'
        self['numslots'] = 6
        intable = False
        numdimm = 0
        modeDict = {
            'temp': ('System Temperatures', '', ''),
            'fsp': ('Front Status Panel:', '', ''),
            'disk': ('Disk Status:', '', ''),
            'fan': ('Fan Status:', '', ''),
            'psu': ('Power Supplies:', '', ''),
            'hwrev': ('', '== HW Revisions ==', ''),
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'enviro': ('', '==  Environmental Status ==', ''),
            'mem': ('', '== Memory Configuration ==', '', self.parseMem),
        }
        cpuMap = {
            # TODO
            'US-IV @ 1350': {'desc': 'CPU/Memory Board w/2 x USIV+ 1.35GHz', 'option': ['X7275A', 'X7270A'], 'part': '501-6962'},
            'US-IV+ @ 1500': {'desc': 'CPU/Memory Board w/2 x USIV+ 1.5GHz', 'option': ['X7274A', 'X7273A'], 'part': '501-7058'},
            'US-IV+ @ 1800': {'desc': 'CPU/Memory Board w/2 x USIV+ 1.8GHz', 'option': ['X7303A', 'X7301A'], 'part': '501-7506'},
        }
        memMap = {
            '512MB': {'desc': '4 x 512MB SDRAM DIMM', 'option': 'X7051A', 'part': '501-7385', 'size': '512MB'},
            '1024MB': {'desc': '4 x 1024MB SDRAM DIMM', 'option': 'X7056A', 'part': '501-7386', 'size': '1GB'},
            '2048MB': {'desc': '4 x 2048MB SDRAM DIMM', 'option': 'X7058A', 'part': '501-6242', 'size': '2GB'}
        }

        data = self.genericPrtdiag(modeDict)

        self.genericCpu(data, cpuMap, 'v490', modulo=2)
        self.genericMem(data, memMap, 'v490', modulo=4)
        self.genericIo(data)

        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if mode == 'temp':
                self.genericCheck(
                    'Temp', line, 2, ['Status', '--------', '======='])
            if mode == 'disk':
                self.genericCheck('Disk', line, 2, ['--------', '======='])
            if mode == 'fan':
                self.genericCheck(
                    'Fan', line, 3, ['Status', '--------', '======='])
            if mode == 'psu':
                self.genericCheck(
                    'PSU', line, 1, ['Status', '--------', '======='])
        fh.close()

    ##########################################################################
    def skipLine(self, line, skipable):
        """ Generic helper function to return true if we should skip this line
        because it contains skipable strings
        """
        if not line:
            return True
        for s in skipable:
            if s in line:
                return True
        return False

    ##########################################################################
    def sun_v440(self):
        """ Analyse V440 prtdiag -v output
        """
        mode = 'unknown'
        self['numslots'] = 6
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iodevs': ('', '== IO Devices ==', '', self.parseIo),
            'iodcards': ('', '== IO Cards ==', '', self.parseIo),
            'hwrev': ('', '== HW Revisions ==', ''),
            'mem': ('', '== Memory Configuration ==', ''),
            'bankt': ('Bank Table:', '', ''),
            'memmodule': ('Memory Module Groups:', '', '', self.parseMemmod),
            'fans': ('Fan Speeds:', '', ''),
            'temp': ('Temperature sensors:', '', ''),
            'current': ('Current sensors:', '', ''),
            'voltage': ('Voltage sensors:', '', ''),
            'keyswitch': ('Keyswitch:', '', ''),
            'fru': ('Fru Operational Status:', '', ''),
        }
        # Three different ways of saying the same thing
        cpuMap = {
            'SUNW,UltraSPARC-IIIi @ 1062': {'desc': '1.062GHz US-IIIi CPU', 'option': 'X7415A', 'part': '501-6461'},
            'SUNW,UltraSPARC-IIIi @ 1281': {'desc': '1.28GHz US-IIIi CPU', 'option': ['X7416A', 'X7443A'], 'part': ['501-6533', '501-7202']},
            'SUNW,UltraSPARC-IIIi @ 1593': {'desc': '1.593GHz US-IIIi CPU', 'option': ['X7445A', 'X7446A', 'X7444A'], 'part': ['501-6789', '501-6786', '501-7093']},

            'US-IIIi @ 1062': {'desc': '1.062GHz US-IIIi CPU', 'option': 'X7415A', 'part': '501-6461'},
            'US-IIIi @ 1281': {'desc': '1.28GHz US-IIIi CPU', 'option': ['X7416A', 'X7443A'], 'part': ['501-6533', '501-7202']},
            'US-IIIi @ 1593': {'desc': '1.593GHz US-IIIi CPU', 'option': ['X7445A', 'X7446A', 'X7444A'], 'part': ['501-6789', '501-6786', '501-7093']},

            '16 @ 1593': {'desc': '1.593GHz US-IIIi CPU', 'option': ['X7445A', 'X7446A', 'X7444A'], 'part': ['501-6789', '501-6786', '501-7093']},
        }

        cpuBoardMap = {
            '1062': {'desc': '1.062GHz CPU Board Assembly', 'part': '501-6369'},
            '1281': {'desc': '1.28GHz CPU Board Assembly', 'part': '501-7029'},
            '1593': {'desc': '1.593GHz CPU Board Assembly', 'part': '501-6788'},
        }

        memMap = {
            256: {'desc': '256MB Memory Module', 'size': '256MB'},
            512: {'desc': '512MB Memory Module', 'option': ['X7403A', 'X7603A', 'X7703'], 'part': ['371-1116', '370-4939', '370-6202', '370-7671'], 'size': '512MB'},
            1024: {'desc': '1024MB Memory Module', 'option': ['X7704A', 'X7404A', 'X7704A'], 'part': ['370-7973', '371-1117', '370-4940', '370-6203', '370-7671'], 'size': '1GB'},
            2048: {'desc': '2048MB Memory Module', 'option': ['X7711A', 'X7604A', 'X7711A'], 'part': ['370-7672', '370-7974', '370-6203', '370-7672'], 'size': '2GB'},
        }

        data = self.genericPrtdiag(modeDict)

        self.genericCpu(data, cpuMap, 'v440')
        self.genericMem(data, memMap, 'v440')
        self.genericIo(data, ['MB'])

        for cpu in data['cpu']:
            if cpu['speed'] in cpuBoardMap:
                self.addPart(**cpuBoardMap[cpu['speed']])

        self.addPart(desc='Motherboard Assembly', part=[
                     '540-5418', '540-6336', '540-6682', '540-6276'])
        self.addPart(desc='Power Supply', part=['300-1501', '300-1851'])
        self.addPart(
            desc='Advanced Lights Out Manager (ALOM) Card', part=['501-6346', '501-7337'])
        self.addPart(
            desc='PCI Fan Tray Assembly', part=['540-5258', '540-6862'])
        self.addPart(
            desc='CPU Fan Tray Assembly', part=['540-5385', '540-6674'])
        self.addPart(
            desc='4-Slot SCSI Disk Backplane', part=['501-6335', '501-7338'])

        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if mode == 'fans':
                self.genericCheck('Fan', line, 2, ['Status', '----'])
            if mode == 'temp':
                self.genericCheck('Temp', line, [2, 7], ['Status', '----'])
            if mode == 'current':
                self.genericCheck('Current', line, [2, 7], ['Status', '----'])
            if mode == 'voltage':
                self.genericCheck('Voltage', line, [2, 7], ['Status', '----'])
            if mode == 'fru':
                self.genericCheck('FRU', line, 1, ['Status', '----'])
        fh.close()

    ##########################################################################
    def sun_v445(self):
        """ Analyse V445 prtdiag -v output
        """
        mode = 'unknown'
        self['numslots'] = 8
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iodevs': ('', '== IO Devices ==', '', self.parseIo),
            'hwrev': ('', '== HW Revisions ==', ''),
            'mem': ('', '== Memory Configuration ==', ''),
            'memmodule': ('Memory Module Groups:', '', '', self.parseMemmod),
            'usb': ('', '== usb Devices ==', ''),
            'environ': ('', '== Environmental Status ==', ''),
            'fans': ('Fan Status:', '', ''),
            'temp': ('Temperature sensors:', '', ''),
            'current': ('Current sensors:', '', ''),
            'voltage': ('Voltage sensors:', '', ''),
            'keyswitch': ('Keyswitch:', '', ''),
            'fru': ('Fru Operational Status:', '', ''),

        }

        # Fixed CPU/Memory boards
        memMap = {
            512: {'desc': '1.593GHz CPU/Memory Module with 2GB Memory', 'part': '501-7368', 'option': 'X7451A'},
            1024: {'desc': '1.593GHz CPU/Memory Module with 4GB Memory', 'part': '501-7287', 'option': 'X7452A'},
            2048: {'desc': '1.593GHz CPU/Memory Module with 8GB Memory', 'part': '501-7369', 'option': 'X7453A'},
        }

        data = self.genericPrtdiag(modeDict)

        #self.genericCpu(data, cpuMap, 'v445')
        self.genericMem(data, memMap, 'v445', modulo=4)
        self.genericIo(data, ['MB'])

        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if mode == 'fans':
                self.genericCheck('Fan', line, 2, ['Status', '----'])
            if mode == 'temp':
                self.genericCheck('Temp', line, [2, 7], ['Status', '----'])
            if mode == 'current':
                self.genericCheck('Current', line, [2, 7], ['Status', '----'])
            if mode == 'voltage':
                self.genericCheck('Voltage', line, [2, 7], ['Status', '----'])
            if mode == 'fru':
                self.genericCheck('FRU', line, 1, ['Status', '----'])
        fh.close()

    ##########################################################################
    def genericCheck(self, chk, line, col, ignore=[]):
        if self.ignoreLines(line, ignore):
            return
        if self.checkColumn(col, line):
            self.tmpissue = line.split()[0]
            self.badmode = True

    ##########################################################################
    def sun_v210(self):
        """ Parse the prtdiag -v output for V210s
        * There are (at least) three different fan output formats, one of which doesn't
          have any status information - hence badfan - Sun's fault not mine
        """
        mode = 'unknown'
        self['numslots'] = 1
        badfan = False
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'hwrev': ('', '== HW Revisions ==', ''),
            'iocards': ('', '== IO Devices ==', '', self.parseIo),
            'mem': ('', '== Memory Configuration ==', ''),
            'bankt': ('Bank Table', '', ''),
            'memmodule': ('Memory Module Groups', '', '', self.parseMemmod),
            'env': ('', '== Environmental Status ==', ''),
            'fru': ('Fru Operational Status:', '', ''),
            'temp': ('Temperature sensors:', '', ''),
            'fans': ('Fan Speeds:', '', ''),
            'boards': ('Board Status:', '', ''),
            'current': ('Current sensors:', '', ''),
            'voltage': ('Voltage sensors:', '', ''),
            'led': ('Led State:', '', ''),
        }

        cpuMap = {
            "US-IIIi @ 1002": {'desc': "1GHz processor for V210/V240", 'part': '595-7222', 'option': 'X7406A'},
            "US-IIIi @ 1336": {'desc': "1.336GHz processor for V210/V240", 'part': '527-1277'},
            "SUNW,UltraSPARC-IIIi @ 1336": {'desc': "1.336GHz processor for V210/V240", 'part': '527-1277'},

            "SUNW,UltraSPARC-IIIi @ 1002": {'desc': "1GHz processor for V210/V240", 'part': '595-7222', 'option': 'X7406A'},
        }
        mbMap = {
            ('1002', 1): {'desc': "Motherboard w/1 x US IIIi 1GHz", 'part': '375-3149'},
            ('1002', 2): {'desc': "Motherboard w/2 x US IIIi 1GHz", 'part': '375-3150'},
            ('1336', 1): {'desc': "Motherboard w/1 x US IIIi 1.336GHz", 'part': '375-3225'},
            ('1336', 2): {'desc': "Motherboard w/2 x US IIIi 1.336GHz", 'part': '375-3226'},
        }

        memMap = {
            256: {'desc': '512MB DDR Memory Option (2x256MB DIMMs)', 'option': 'X7402A', 'part': '370-5565', 'size': '256MB'},
            512: {'desc': '1GB DDR Memory Option (2x512MB DIMMs)', 'option': 'X7703A-4', 'part': '370-7972', 'size': '512MB'},
            1024: {'desc': '2GB DDR1 Memory Option (2x1GB DIMMs)', 'option': 'X7704A-4', 'part': '370-7973', 'size': '1GB'},
        }
        data = self.genericPrtdiag(modeDict)

        # CPU
        self.genericCpu(data, cpuMap, 'v210')

        # Mother boards
        if 'cpu' in data:
            key = (data['cpu'][0]['speed'], len(data['cpu']))
            if key in mbMap:
                self.addPart(**mbMap[key])
            else:
                self.Warning(
                    "Unhandled V210 motherboard: speed=%s, numcpu=%s" % key)

        self.genericMem(data, memMap, 'v210')
        self.genericIo(data, ['MB', '7', '13', '2', '10'])
        self.addPart(desc="320W AC Input Power Supply", part='300-1566')
        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue

            if mode == 'temp':
                self.genericCheck('Temp', line, -1, ['Status', '-----'])
            if mode == 'current':
                self.genericCheck('Current', line, -1, ['Status', '-----'])
            if mode == 'voltage':
                self.genericCheck('Voltage', line, -1, ['Status', '-----'])
            if mode == 'fans' and not badfan:
                if line.find('Location') >= 0 and line.find('Status') < 0:
                    badfan = True
                    continue
                self.genericCheck('Fans', line, 2, ['Status', '-----'])
            if mode == 'boards':
                self.genericCheck('Boards', line, 1, ['Status', '-----'])
            if mode == 'fru':
                self.genericCheck('FRUs', line, 1, ['Status', '-----'])
        fh.close()

    ##########################################################################
    def sun_v245(self):
        """ Parse the prtdiag -v output for V245s
        """
        mode = 'unknown'
        self['numslots'] = 4
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iocards': ('', '== IO Devices ==', '', self.parseIo),
            'hwrev': ('', '== HW Revisions ==', ''),
            'memconf': ('', '== Memory Configuration ==', ''),
            'fans1': ('Fan Status:', '', ''),
            'membank': ('Bank Table:', '', ''),
            'memmodule': ('Memory Module Groups:', '', '', self.parseMemmod),
            'fru': ('Fru Operational Status:', '', ''),
            'temp': ('Temperature sensors:', '', ''),
            'current': ('Current sensors:', '', ''),
            'voltage': ('Voltage sensors:', '', ''),
            'keyswitch': ('Keyswitch:', '', ''),
        }
        mbMap = {
            ('1504', 1): {'desc': 'Motherboard w/ 1x US IIIi 1.5GHz', 'part': '375-3464'},
            ('1504', 2): {'desc': 'Motherboard w/ 2x US IIIi 1.5GHz', 'part': '375-3463'}
        }
        memMap = {
            512: {'desc': '1GB Memory FRU (2x512MB DIMMs)', 'option': 'X8703A', 'part': '540-6466', 'size': '512MB'},
            1024: {'desc': '2GB Memory FRU (2x1GB DIMMs)', 'option': 'X8704A', 'part': '540-6467', 'size': '1GB'},
            2048: {'desc': '4GB Memory FRU (2x2GB DIMMs)', 'option': 'X8711A', 'part': '540-6468', 'size': '2GB'},
        }
        data = self.genericPrtdiag(modeDict)

        # Mother boards
        key = (data['cpu'][0]['speed'], len(data['cpu']))
        if key in mbMap:
            self.addPart(**mbMap[key])
        else:
            self.Warning(
                "Unhandled V245 motherboard: speed=%s, numcpu=%s" % key)

        self.genericMem(data, memMap, 'v245')
        self.genericIo(data, ['MB'])

        self.addPart(desc='DC Power Distribution Board', part='370-5138')
        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue

            if mode == 'temp':
                self.genericCheck('Temp', line, [2, 7], ['Status', '-----'])
            if mode == 'fans1':
                self.genericCheck('Fan', line, 2, ['Status', '-----'])
            if mode == 'current':
                self.genericCheck('Current', line, [2, 7], ['Status', '-----'])
            if mode == 'voltage':
                self.genericCheck('Voltage', line, [2, 7], ['Status', '-----'])

            if mode == 'fru':
                self.genericCheck('FRU', line, 1, ['Status', '-----'])
                if line.startswith('PS'):
                    self.addPart(
                        desc='500 Watt, Type A203 Power Supply', option='X8428A-Z', part='300-1945')

    ##########################################################################
    def sun_v240(self):
        """ Parse the prtdiag -v output for V240s
        """
        mode = 'unknown'
        self['numslots'] = 3
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'iodevs': ('', '== IO Devices ==', '', self.parseIo),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'hwrev': ('', '== HW Revisions ==', ''),
            'memconf': ('', '== Memory Configuration ==', ''),
            'fans1': ('Fan Status:', '', ''),
            'fans2': ('Fan Speeds:', '', ''),
            'membank': ('Bank Table:', '', ''),
            'memmodule': ('Memory Module Groups:', '', '', self.parseMemmod),
            'fru': ('Fru Operational Status:', '', ''),
            'temp': ('Temperature sensors:', '', ''),
            'current': ('Current sensors:', '', ''),
            'voltage': ('Voltage sensors:', '', ''),
            'keyswitch': ('Keyswitch:', '', ''),
        }
        # Different ways of saying the same thing
        cpuMap = {
            'SUNW,UltraSPARC-IIIi @ 1336': {'desc': '1.336GHz processor for V240', 'part': '375-3225'},
            'SUNW,UltraSPARC-IIIi @ 1002': {'desc': '1GHz processor for V240', 'part': '595-7222', 'option': 'X7406A'},
            'SUNW,UltraSPARC-IIIi @ 1280': {'desc': '1.28GHz processor for V240', 'part': '595-7223', 'option': 'X7412A'},
            'SUNW,UltraSPARC-IIIi @ 1503': {'desc': 'Motherboard w/2 x US IIIi 1.503GHz', 'part': '375-3227'},

            'US-IIIi @ 1002': {'desc': '1GHz processor for V240', 'part': '595-7222', 'option': 'X7406A'},
            'US-IIIi @ 1280': {'desc': '1.28GHz processor for V240', 'part': '595-7223', 'option': 'X7412A'},
            'US-IIIi @ 1336': {'desc': '1.336GHz processor for V240', 'part': '375-3225'},
            'US-IIIi @ 1503': {'desc': 'Motherboard w/2 x US IIIi 1.503GHz', 'part': '375-3227'},

            '16 @ 1002': {'desc': '1GHz processor for V240', 'part': '595-7222', 'option': 'X7406A'},
            '16 @ 1280': {'desc': '1.28GHz processor for V240', 'part': '595-7223', 'option': 'X7412A'},
            '16 @ 1336': {'desc': '1.336GHz processor for V240', 'part': '375-3225'},
            '16 @ 1503': {'desc': 'Motherboard w/2 x US IIIi 1.503GHz', 'part': '375-3227'},
        }
        memMap = {
            256: {'desc': '512MB DDR Memory Option (2x256MB DIMMs)', 'option': 'X7402A', 'part': '370-5565', 'size': '256MB'},
            512: {'desc': '1GB DDR Memory Option (2x512MB DIMMs)', 'option': 'X7403A', 'part': '370-4939', 'size': '512MB'},
            1024: {'desc': '2GB DDR Memory Option (2x1GB DIMMs)', 'option': 'X7404A', 'part': '370-4940', 'size': '1GB'},
            2048: {'desc': '4GB DDR Memory Option (2x2GB DIMMs)', 'option': 'X7711A', 'part': '370-7672', 'size': '2GB'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'v240')
        self.genericMem(data, memMap, 'v240')
        self.genericIo(data, ['MB', '7', '10'])

        self.addPart(desc='DC Power Distribution Board', part='370-5138')
        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue

            if mode == 'temp':
                self.genericCheck('Temp', line, [2, 7], ['Status', '-----'])
            if mode == 'fans1':
                self.genericCheck('Fan', line, 2, ['Status', '-----'])
            if mode == 'fans2':
                self.genericCheck('Fan', line, 2, ['Status', '-----'])
            if mode == 'current':
                self.genericCheck('Current', line, [2, 7], ['Status', '-----'])
            if mode == 'voltage':
                self.genericCheck('Voltage', line, [2, 7], ['Status', '-----'])
            if mode == 'fru':
                self.genericCheck('FRU', line, 1, ['Status', '-----'])
                if line.startswith('PS'):
                    self.addPart(desc='400WAC Input Power Supply Type A178 or A192', option=[
                                 'X7407A', 'X7428A'], part=['300-1568', '300-1674'])

        fh.close()

    ##########################################################################
    def sun_v890(self):
        mode = 'unknown'
        self['numslots'] = 9
        modeDict = {
            'mem': ('', '== Memory Configuration ==', '', self.parseMem),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'environ': ('', '== Environmental Status ==', ''),
            'hwrev': ('', '== HW Revisions ==', ''),
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'fans': ('Fan Bank', '', ''),
            'fsp': ('Front Status Panel:', '', ''),
            'psu': ('Power Supplies:', '', ''),
            'temp': ('System Temperatures', '', ''),
            'nofailure': ('No failures found', '', ''),
        }
        cpuMap = {
            # TODO check diff between IV/IV+
            'US-IV @ 1200': {'desc': 'CPU/Memory Board w/ 2xUS IV+ 1.2GHz', 'option': 'X7269A', 'part': '501-6636'},
            'US-IV @ 1350': {'desc': 'CPU/Memory Board w/ 2xUS IV+ 1.35GHz', 'option': 'X7275A', 'part': '501-6962'},
            'US-IV+ @ 1500': {'desc': 'CPU/Memory Board w/ 2xUS IV+ 1.5GHz', 'option': 'X7273A', 'part': '501-7058'},
            'US-IV+ @ 1800': {'desc': 'CPU/Memory Board w/ 2xUS IV+ 1.8GHz', 'option': 'X7303A', 'part': ['501-7506', '501-7691', '501-7881']},
            'US-IV+ @ 2100': {'desc': 'CPU/Memory Board w/ 2xUS IV+ 2.1GHz', 'part': '501-7713'},
        }
        memMap = {
            '512MB': {'desc': '512MB SDRAM DIMM', 'option': 'X7051A', 'part': '501-7385', 'size': '512MB'},
            '1024MB': {'desc': '1024MB SDRAM DIMM', 'option': 'X7056A', 'part': '501-7386', 'size': '1GB'},
            '2048MB': {'desc': '2048MB SDRAM DIMM', 'option': 'X7058A', 'part': '501-6242', 'size': '2GB'},
        }
        data = self.genericPrtdiag(modeDict)

        self.genericCpu(data, cpuMap, 'v890', modulo=2)
        self.genericMem(data, memMap, 'v890')
        self.genericIo(data, ['MB'])

        self.addPart(
            desc='CPU Fan Tray', part='541-0134', qty=len(data['cpu']) / 2)
        self.addPart(desc='Mother Board', part='501-7199')
        self.addPart(desc='Power Distribution Board', part='375-3173')
        self.addPart(
            desc='Advanced Lights Out Manager Plus Card', part='501-6767')
        self.addPart(desc='I/O Board', part='501-7225')
        self.addPart(desc='80MM Motherboard Fan Tray', part='540-4025')
        self.addPart(desc='PCI I/O Fan Tray', part='540-3615')
        self.addPart(desc='6 Slot FC Base/Expansion Backplane',
                     qty=0, part='501-6759', option='X7858A')
        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if not line:
                continue

            if mode == 'iocards':
                self.genericCheck(
                    'IO Cards', line, 8, ['Bus', 'Freq', '-----'])
            if mode == 'temp':
                self.genericCheck(
                    'Temp', line, [1, 2], ['Status', '-----', '======='])
            if mode == 'fans':
                self.genericCheck(
                    'Fan', line, 3, ['Status', '-----', 'RPMS', '======'])
            if mode == 'psu':
                self.genericCheck(
                    'Power Supply', line, 1, ['Status', '-----', 'Current'])
                if line.startswith('PS'):
                    self.addPart(desc='Power Supply', part='300-1622')
        fh.close()

    ##########################################################################
    def genericMem(self, data, memMap, label="Unknown", modulo=1):
        if 'mem' in data:
            for dimm in data['mem']:
                if dimm['dimmsize'] in memMap:
                    Warning("dimm=%s" % dimm)
                    for i in range(dimm.get('qty', 1)):
                        self.addMem(**memMap[dimm['dimmsize']])
                        self.foundMem = True
                else:
                    self.Warning("Unhandled %s memory size %s" %
                                 (label, dimm['dimmsize']))
        elif 'memmodule' in data:
            dimmsize = data['memsize'] / data['memmodule']
            if dimmsize in memMap:
                memMap[dimmsize]['qty'] = data['memmodule'] / modulo
                self.addMem(**memMap[dimmsize])
                self.foundMem = True
            else:
                self.Warning("Unhandled %s memory size %d" % (label, dimmsize))
        elif 'memsize' in data:
            if data['memsize'] in memMap:
                self.addMem(**memMap[data['memsize']])
                self.foundMem = True
        else:
            self.Warning("data=%s" % data)
            self.Warning("Unknown %s memory" % label)

    ##########################################################################
    def genericIo(self, data, ignoreslots=[]):
        try:
            for io in data.get('iocards', []) + data.get('iodevs', []):
                if io['slot'] not in ignoreslots:
                    if 'board' in io:
                        loc = self.getLoc(slot=io['slot'], board=io['board'])
                    else:
                        loc = self.getLoc(slot=io['slot'])
                    if 'bus' in io:
                        bus = io['bus']
                    elif 'board' in io:
                        bus = io['board']
                    else:
                        bus = 'unknown'

                    self.addCard(loc, rawmodel=io['rawmodel'], bus=bus)
        except KeyError, err:
            self.Warning("genericIo missing %s on io=%s" % (str(err), io))
            raise

    ##########################################################################
    def genericCpu(self, data, cpuMap, label="Unknown", mode='speed', modulo=1):
        if 'cpu' not in data:
            return

        cpus = {}
        for cpu in data['cpu']:
            cpukey = "%s @ %s" % (cpu['impl'], cpu['speed'])
            cpus[cpukey] = cpus.get(cpukey, 0) + 1

        for key in cpus:
            # Look for  'num x impl @ speed'
            cpukey = "%d x %s" % (cpus[key] / modulo, key)
            if cpukey in cpuMap:
                self.addCpu(**cpuMap[cpukey])
                self.foundCpu = True
            # Look for  'impl @ speed'
            elif key in cpuMap:
                for i in range(cpus[key] / modulo):
                    self.addCpu(**cpuMap[key])
                self.foundCpu = True
            else:
                self.Warning("Unhandled %s CPU '%s'" % (label, key))

    ##########################################################################
    def sun_v880(self):
        mode = 'unknown'
        self['numslots'] = 9
        modeDict = {
            'mem': ('', '== Memory Configuration ==', '', self.parseMem),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'environ': ('', '== Environmental Status ==', ''),
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'hwrev': ('', '== HW Revisions ==', ''),
            'fans': ('Fan Bank', '', ''),
            'fsp': ('Front Status Panel:', '', ''),
            'psu': ('Power Supplies:', '', ''),
            'temp': ('System Temperatures', '', ''),
            'nofailure': ('No failures found', '', ''),
        }
        cpuMap = {
            # TODO
            'US-III @ 750': {'desc': 'CPU/Memory Board w/ 2x US III Cu 750MHz', 'option': 'X7047A', 'part': '501-6360'},
            'US-III+ @ 900': {'desc': 'CPU/Memory Board w/ 2x US III Cu 900MHz', 'option': 'X7028A', 'part': ['501-6731', '501-6334']},
            'US-III+ @ 1050': {'desc': 'CPU/Memory Board w/ 2x US III Cu 1050MHz', 'option': 'X6894A', 'part': '501-6163'},
            'US-III+ @ 1200': {'desc': 'CPU/Memory Board w/ 2x US III Cu 1200MHz', 'option': 'X6895A', 'part': '501-6164'},
        }
        memMap = {
            '128MB': {'desc': '128MB SDRAM DIMM', 'option': 'X7050A', 'part': '501-4489', 'size': '128MB'},
            '256MB': {'desc': '256MB SDRAM DIMM', 'option': 'X7053A', 'part': '501-5401', 'size': '256MB'},
            '512MB': {'desc': '512MB SDRAM DIMM', 'option': 'X7051A', 'part': '501-7385', 'size': '512MB'},
            '1024MB': {'desc': '1GB SDRAM DIMM', 'option': 'X7056A', 'part': '501-7386', 'size': '1GB'},
        }
        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'V880')
        self.genericMem(data, memMap, 'V880')
        self.genericIo(data, ['MB'])

        self.addPart(desc='Motherboard', part='501-4300')
        self.addPart(desc='80MM Motherboard Fan Tray', part='540-4025')
        self.addPart(desc='PCI I/O Fan Tray', part='540-3615')
        self.addPart(desc='Power Distribution Board', part='375-0071')
        self.addPart(
            desc='Remote System Control (RSC2) Board', part='501-5856')
        self.addPart(desc='I/O Board', part=['501-5142', '501-6524'])
        self.addPart(desc='6 Slot FC Base/Expansion Backplane',
                     qty=0, part=['501-5993', '501-6665'])
        numcpu = 0
        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue

            if mode == 'temp':
                self.genericCheck(
                    'Temp', line, 2, ['Status', '-----', '======='])
            if mode == 'fans':
                self.genericCheck(
                    'Fan', line, 3, ['Status', '-----', 'RPMS', '======'])
                if line.startswith('CPU') and '_PRIM_FAN' in line:
                    self.addPart(desc='CPU Fan Tray', part='540-3614')
            if mode == 'psu':
                self.genericCheck(
                    'Power Supply', line, 1, ['Status', '-----', 'Current'])
                if line.startswith('PS'):
                    self.addPart(desc='Power Supply', part='300-1353')
            if mode == 'environ':
                self.genericCheck(
                    'System Temperatures', line, 2, ['Status', '-----'])
                if line.startswith('IOB'):
                    self.addPart(
                        desc='I/O Board', part=['501-5142', '501-6524'])
        fh.close()

    ##########################################################################
    def sun_e2900(self):
        mode = 'unknown'
        modeDict = {
            'mem': ('', '== Memory Configuration ==', ''),
            'bankt': ('Bank Table:', '', ''),
            'memmodule': ('Memory Module Groups:', '', '', self.parseMemmod),
            'iocards': ('', '== IO Devices ==', '', self.parseIo),
            'environ': ('', '== Environmental Status ==', ''),
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'led': ('Led State:', '', ''),
            'hwrev': ('', '== HW Revisions ==', ''),
            'fru': ('', '== FRU Operational Status ==', ''),
            'fans': ('Fan Status:', '', ''),
            'temp': ('Temperature sensors', '', ''),
            'volt': ('Voltage sensors', '', ''),
        }
        cpuMap = {
            'SUNW,UltraSPARC-IV+ @ 1800': {'desc': 'CPU/Memory UniBoard w/4x US IV+ 1.8GHz, 0MB', 'part': '540-7531'},
        }
        memMap = {
            512: {'desc': '2GB (4x512MB SDRAM DIMMs)', 'option': 'X7051A', 'part': '501-7385', 'size': '512MB'},
            1024: {'desc': '4GB (4x1GB SDRAM DIMMs)', 'option': 'X7056A', 'part': '501-7386', 'size': '1GB'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'e2900', modulo=4)
        self.genericMem(data, memMap, 'e2900', modulo=4)
        self.genericIo(data)

        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if mode == 'fru':
                self.genericCheck('FRU', line, -1, ['Status', '-----'])
            if mode == 'volt':
                self.genericCheck('Voltage', line, -1, ['Status', '-----'])
            if mode == 'temp':
                self.genericCheck('Temp', line, -1, ['Status', '-----'])
            if mode == 'fans':
                self.genericCheck(
                    'Fan', line, 2, ['Status', '-----', 'self-regulating'])
        fh.close()

    ##########################################################################
    def sun_v1280(self):
        mode = 'unknown'
        self['numslots'] = 6
        tmpline = ''
        splitiomode = False
        cpumode = 'normal'
        memmode = 'normal'
        modeDict = {
            'memconf': ('', '== Memory Configuration ==', ''),
            'bankt': ('Bank Table:', '', ''),
            'memmodule': ('Memory Module Groups:', '', '', self.parseMemmod),
            'iocards': ('', '== IO Devices ==', '', self.parseIo),
            'environ': ('', '== Environmental Status ==', ''),
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'led': ('Led State:', '', ''),
            'hwrev': ('', '== HW Revisions ==', ''),
            'fru': ('', '== FRU Operational Status ==', ''),
            'fans': ('Fan Speeds:', '', ''),
            'temp': ('Temperature sensors', '', ''),
            'volt': ('Voltage sensors', '', ''),
        }

        cpuMap = {
            'SUNW,UltraSPARC-III+ @ 1200': {'desc': 'CPU/Memory Board w/ 4x US III Cu 1200MHz, 0MB', 'part': '540-5849'},
            'US-III+ @ 1200': {'desc': 'CPU/Memory Board w/ 4x US III Cu 1200MHz, 0MB', 'part': '540-5849'},
        }
        memMap = {
            1024: {'desc': '4GB (4x1GB SDRAM DIMMs)', 'option': 'X7056A', 'part': '501-7386', 'size': '1GB'},
            512: {'desc': '2GB (4x512MB SDRAM DIMMs)', 'option': 'X7051A', 'part': '501-7385', 'size': '512MB'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'v1280', modulo=4)
        self.genericMem(data, memMap, 'v1280', modulo=4)
        self.genericIo(data)

#       dimmsize=data['memsize']/data['memmodule']
#       if dimmsize in memMap:
#           memMap[dimmsize]['qty']=data['memmodule']/4
#           self.addMem(**memMap[dimmsize])
#       else:
#           self.Warning("Unhandled V1280 memory size %d" % dimmsize)

        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if mode == 'fru':
                self.genericCheck('FRU', line, -1, ['Status', '-----'])
            if mode == 'volt':
                self.genericCheck('Voltage', line, -1, ['Status', '-----'])
            if mode == 'temp':
                self.genericCheck('Temp', line, -1, ['Status', '-----'])
            if mode == 'fans':
                self.genericCheck(
                    'Fan', line, 2, ['Status', '-----', 'self-regulating'])
        fh.close()

    ##########################################################################
    def modeSelect(self, mode, line, modeDict):
        """ Return the mode based on the line
        """
        found = False
        for k, v in modeDict.items():
            if len(v) == 3:
                pre, mid, post = v
            else:
                pre, mid, post, proc = v
            if pre and line.startswith(pre):
                found = True
                break
            if post and line.endswith(post):
                found = True
                break
            if mid and line.find(mid) >= 0:
                found = True
                break
        if found:
            if self.tmpissue:
                self.addIssue(mode, obj=self.tmpissue, text=self.buffer)
                self.tmpissue = ''
            self.buffer = [line]
            self.badmode = False
            return k, 1
        self.buffer.append(line)
        return mode, 0

    ##########################################################################
    def sun_e250(self):
        mode = 'unknown'
        self['numslots'] = 4
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'mem': ('', '== Memory ==', '', self.parseMem),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'environ': ('', '== Environmental Status ==', ''),
            'hwrev': ('', '== HW Revisions ==', ''),
            'fans': ('Fans:', '', ''),
            'psu': ('Power Supplies:', '', ''),
            'temp': ('System Temperatures:', '', ''),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            'US-II @ 296': {'desc': '300MHz UltraSPARC II Module', 'part': '501-4849', 'option': 'X1191A'},
            'US-II @ 400': {'desc': '400MHz UltraSPARC II Module', 'part': '501-5445', 'option': 'X1194A'},
        }
        memMap = {
            '64': {'desc': '64MB DIMM', 'part': '501-5691', 'option': 'X7043A', 'size': '64MB'},
            '128': {'desc': '128MB DIMM', 'part': '501-3136', 'option': 'X7004A', 'size': '128MB'},
        }

        data = self.genericPrtdiag(modeDict)

        self.genericCpu(data, cpuMap, 'e250')
#       for cpu in data['cpu']:
#           if cpu['speed'] in cpuMap:
#               self.addCpu(**cpuMap[cpu['speed']])
#           else:
#               self.Warning("Unhandled E250 CPU speed %s" % cpu['speed'])

        self.genericIo(data)
#       for io in data['iocards']:
#           loc=self.getLoc(board=io['board'], slot=io['slot'])
#           self.addCard(loc, rawmodel=io['rawmodel'], bus=io['bus'])

        self.genericMem(data, memMap, 'e250')
#       for mem in data['mem']:
#           if mem['dimmsize'] in memMap:
#               self.addMem(**memMap[mem['dimmsize']])
#           else:
#               self.Warning("Unhandled E250 Memory size %s" % mem['dimmsize'])

        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue

            if mode == 'fans':
                self.genericCheck('Fan', line, 2, ['Status', '-----'])
            if mode == 'psu':
                self.genericCheck(
                    'Power Supply', line, [1, 4], ['Status', '-----'])
        fh.close()

    ##########################################################################
    def parseCpu(self, buff):
        headers = []
        cpus = []
        inheaders = True
        for line in buff:
            if not line:
                continue
            if '-----' in line:
                inheaders = False
                continue
            if inheaders:
                headers.extend(line.split())
                continue
            bits = line.split()
            if headers == ['CPU', 'CPU', 'Location', 'CPU', 'Freq', 'Implementation', 'Mask']:
                cpus.append(
                    {'board': bits[0], 'speed': bits[2], 'impl': bits[4]})
            elif headers == ['Run', 'E$', 'CPU', 'CPU', 'Brd', 'CPU', 'MHz', 'MB', 'Impl.', 'Mask']:
                cpus.append({'board': bits[
                            0], 'speed': bits[-4], 'cache': bits[-3], 'impl': bits[-2], 'mask': bits[-1]})
                #                     Run   Ecache   CPU    CPU
                # Brd  CPU   Module   MHz     MB    Impl.   Mask
                # ---  ---  -------  -----  ------  ------  ----
                #  0     0     0      500     0.2   13       1.4
            elif headers == ['Run', 'Ecache', 'CPU', 'CPU', 'Brd', 'CPU', 'Module', 'MHz', 'MB', 'Impl.', 'Mask']:
                cpus.append({'board': bits[0], 'speed': bits[3], 'cache': bits[
                            4], 'impl': bits[5], 'mask': bits[6]})
                #                E$          CPU                  CPU    Temperature
                # CPU  Freq      Size        Implementation       Mask   Die   Amb.  Location
                # ---  --------  ----------  -------------------  -----  ----
                # 0  1002 MHz  1MB         SUNW,UltraSPARC-IIIi   2.4    -
                # -    MB/P0
            elif headers == ['E$', 'CPU', 'CPU', 'Temperature', 'CPU', 'Freq', 'Size', 'Implementation', 'Mask', 'Die', 'Amb.', 'Location']:
                cpus.append(
                    {'speed': bits[1], 'cache': bits[3], 'impl': bits[4], 'mask': bits[5]})
                #                E$          CPU                  CPU     Temperature
                # CPU  Freq      Size        Implementation       Mask    Die   Amb.  Status      Location
                # ---  --------  ----------  -------------------  -----   ----
                # 0  1002 MHz  1MB         SUNW,UltraSPARC-IIIi   2.4     -
                # -    online      MB/P0
            elif headers == ['E$', 'CPU', 'CPU', 'Temperature', 'CPU', 'Freq', 'Size', 'Implementation', 'Mask', 'Die', 'Amb.', 'Status', 'Location']:
                cpus.append({'speed': bits[1], 'cache': bits[3], 'impl': bits[
                            4], 'mask': bits[5], 'status': bits[8]})
                self.genericCheck('CPU', line, 8)
                #                       E$          CPU     CPU       Temperature         Fan
                #        CPU  Freq      Size        Impl.   Mask     Die    Ambient   Speed   Unit
                #        ---  --------  ----------  ------  ----  --------  --------  -----   ----
                # MB/P0  1002 MHz  1MB         US-IIIi  2.4       -        -
            elif headers == ['E$', 'CPU', 'CPU', 'Temperature', 'Fan', 'CPU', 'Freq', 'Size', 'Impl.', 'Mask', 'Die', 'Ambient', 'Speed', 'Unit']:
                cpus.append(
                    {'speed': bits[1], 'cache': bits[3], 'impl': bits[4], 'mask': bits[5]})
                #           CPU      Run    E$    CPU     CPU
                # Slot ID    ID      MHz    MB   Impl.    Mask
                # --------  -------  ----  ----  -------  ----
                # /SB03/P0   96      1200   8.0  US-III+  11.0
                # The CPU ID can either be one or two words so we count from
                # the back
            elif headers == ['CPU', 'Run', 'E$', 'CPU', 'CPU', 'Slot', 'ID', 'ID', 'MHz', 'MB', 'Impl.', 'Mask']:
                cpus.append(
                    {'speed': bits[-4], 'cache': bits[-3], 'impl': bits[-2], 'mask': bits[-1]})
                #                E$          CPU                    CPU
                # CPU  Freq      Size        Implementation         Mask    Status      Location
                # ---  --------  ----------  ---------------------  -----   ---
                # 0    1503 MHz  1MB         SUNW,UltraSPARC-IIIi    3.4
                # on-line     MB/P0
            elif headers == ['E$', 'CPU', 'CPU', 'CPU', 'Freq', 'Size', 'Implementation', 'Mask', 'Status', 'Location']:
                cpus.append({'speed': bits[1], 'cache': bits[3], 'impl': bits[
                            4], 'mask': bits[5], 'status': bits[6]})
                self.genericCheck('CPU', line, 6)
                #                E$          CPU     CPU       Temperature
                # CPU  Freq      Size        Impl.   Mask     Die    Ambient
                # ---  --------  ----------  ------  ----  --------  --------
                #  0    502 MHz  256KB       US-IIe   1.4     62 C     35 C
            elif headers == ['E$', 'CPU', 'CPU', 'Temperature', 'CPU', 'Freq', 'Size', 'Impl.', 'Mask', 'Die', 'Ambient']:
                cpus.append(
                    {'speed': bits[1], 'cache': bits[3], 'impl': bits[4], 'mask': bits[5]})
                #             CPU      Run    E$   CPU      CPU
                # FRU Name     ID      MHz    MB   Impl.    Mask
                # ----------  -------  ----  ----  -------  ----
                # /N0/SB4/P2   18      1200   8.0  US-III+  11.0
            elif headers == ['CPU', 'Run', 'E$', 'CPU', 'CPU', 'FRU', 'Name', 'ID', 'MHz', 'MB', 'Impl.', 'Mask']:
                cpus.append(
                    {'speed': bits[2], 'cache': bits[3], 'impl': bits[4], 'mask': bits[5]})
                #             Port  Run    E$   CPU      CPU
                # FRU Name     ID   MHz    MB   Impl.    Mask
                # ----------  ----  ----  ----  -------  ----
                # /N0/SB3/P2   14   1200   8.0  US-III+  6.0
            elif headers == ['Port', 'Run', 'E$', 'CPU', 'CPU', 'FRU', 'Name', 'ID', 'MHz', 'MB', 'Impl.', 'Mask']:
                cpus.append(
                    {'speed': bits[2], 'cache': bits[3], 'impl': bits[4], 'mask': bits[5]})
                # CPU ID Frequency Implementation         Status
                # ------ --------- ---------------------- -------
                # 0      1200 MHz  SUNW,UltraSPARC-T1     on-line
            elif headers == ['CPU', 'ID', 'Frequency', 'Implementation', 'Status']:
                self.genericCheck('CPU', line, 4)
                cpus.append(
                    {'speed': bits[1], 'impl': bits[3], 'status': bits[4]})
                #        CPU              CPU            Run       L2$       CPU      CPU
                # LSB    Chip              ID            MHz        MB       Impl.    Mask
                # ---    ----      --------------------  ----      ---       -----    ----
                # 00      0          0,   1,   2,   3   2150      5.0
                # 6      146
            elif headers == ['CPU', 'CPU', 'Run', 'L2$', 'CPU', 'CPU', 'LSB', 'Chip', 'ID', 'MHz', 'MB', 'Impl.', 'Mask']:
                cpus.append(
                    {'speed': bits[-4], 'impl': bits[-2], 'mask': bits[-1], 'cache': bits[-3]})
            else:
                self.Fatal("parseCpu: Unhandled CPU format: %s" % headers)
        if cpus:
            self.foundCpu = True
        return cpus

    ##########################################################################
    def parseIo(self, buff):
        iocards = []
        headers = []
        inheaders = True

        for line in buff:
            if not line:
                continue
            bits = line.split()
            if '-----' in line:
                inheaders = False
                continue
            if inheaders:
                headers.extend(bits)
                continue

            bits = line.split()
            if headers == ['Bus', 'Dev,', 'Freq', 'Func', 'ID', 'IO', 'MHz', 'Max', 'Model', 'Name', 'Port', 'Side', 'Slot', 'State', 'Type']:
                self.genericCheck('IO Card', line, 7)
                iocards.append({'bus': bits[0], 'port': bits[1], 'side': bits[2], 'slot': bits[
                               3], 'freq': bits[4], 'maxfreq': bits[5], 'status': bits[7], 'rawmodel': " ".join(bits[8:])})
                #               Bus     Freq  Slot +      Name +
                #               Type    MHz   Status      Path                          Model
                #               ------  ----  ----------  ---------------------
                #               pci     66    MB          pci108e,abba (network)        SUNW,pci-ce
                # okay        /pci@1c,600000/network@2
            elif headers == ['Bus', 'Freq', 'Slot', '+', 'Name', '+', 'Type', 'MHz', 'Status', 'Path', 'Model']:
                iocards = self.parseMultilineIO(buff, headers)
                break
                #                                Bus  Max
                #            IO   Port Bus       Freq Bus  Dev,
                #       Brd  Type  ID  Side Slot MHz  Freq Func State Name                              Model
                #       ---- ---- ---- ---- ---- ---- ---- ---- ----- ---------
                # I/O  PCI   9    B    6    33   33  2,0  ok
                # pci-pci8086,b154.0/pci (pci)      PCI-BRIDGE
            elif headers == ['Bus', 'Max', 'IO', 'Port', 'Bus', 'Freq', 'Bus', 'Dev,', 'Brd', 'Type', 'ID', 'Side', 'Slot', 'MHz', 'Freq', 'Func', 'State', 'Name', 'Model']:
                iocards.append({'board': bits[0], 'bus': bits[1], 'port': bits[2], 'side': bits[3], 'slot': bits[
                               4], 'freq': bits[5], 'maxfreq': bits[6], 'status': bits[8], 'rawmodel': " ".join(bits[9:])})
                self.genericCheck('IO Card', line, 8)
                #                   IO
                #       Location    Type  Slot Path                                          Name                      Model
                #       ----------- ----- ---- --------------------------------
                # MB/PCIE      PCIE   MB
                # /pci@0/pci@0/pci@1/pci@0/pci@1/pci@0
                # pci-pciexclass,060400
            elif headers == ['IO', 'Location', 'Type', 'Slot', 'Path', 'Name', 'Model']:
                iocards.append(
                    {'board': bits[0], 'slot': bits[2], 'rawmodel': " ".join(bits[3:])})
                #                     Bus  Max
                #  IO  Port Bus       Freq Bus  Dev,
                # Type  ID  Side Slot MHz  Freq Func State Name                              Model
                # ---- ---- ---- ---- ---- ---- ---- ----- --------------------
                # PCI   8    A    0    66   66  1,0  ok
                # pci-pci8086,b154.0/pci (pci)      PCI-BRIDGE
            elif headers == ['Bus', 'Max', 'IO', 'Port', 'Bus', 'Freq', 'Bus', 'Dev,', 'Type', 'ID', 'Side', 'Slot', 'MHz', 'Freq', 'Func', 'State', 'Name', 'Model']:
                iocards.append({'board': bits[0], 'side': bits[2], 'slot': bits[3], 'freq': bits[
                               4], 'maxfreq': bits[5], 'status': bits[7], 'rawmodel': " ".join(bits[8:])})
                self.genericCheck("IO Card", line, 7)
                #      Bus   Freq
                # Brd  Type  MHz   Slot  Name                              Model
                # ---  ----  ----  ----  --------------------------------  ----
                # 0   PCI    66     5   network-pci108e,1101
                # SUNW,pci-eri
            elif headers == ['Bus', 'Freq', 'Brd', 'Type', 'MHz', 'Slot', 'Name', 'Model']:
                modelslice = 4
                slot = bits[3]
                # Sometimes this can be '2' or 'PCI 2' or 'PCI 2 66', etc.
                if slot == 'PCI':
                    if bits[5] in ('33', '66'):
                        slot = " ".join(bits[3:6])
                        modelslice = 6
                    else:
                        slot = " ".join(bits[3:5])
                        modelslice = 5
                    #self.Warning("Using more for slot %s" % slot)
                iocards.append({'board': bits[0], 'bus': bits[1], 'freq': bits[
                               2], 'slot': slot, 'rawmodel': " ".join(bits[modelslice:])})
                #                            Bus  Max
                #             IO   Port Bus  Freq Bus  Dev,
                # Slot ID     Type  ID  Side MHz  Freq Func State Name                              Model
                # ----------  ---- ---- ---- ---- ---- ---- ----- -------------
                # /IO03/C5V0  PCI  124   B    33   33  1,0  ok    pci-pci8086,b154.0/network (netw+ pci-bridge
            elif headers == ['Bus', 'Max', 'IO', 'Port', 'Bus', 'Freq', 'Bus', 'Dev,', 'Slot', 'ID', 'Type', 'ID', 'Side', 'MHz', 'Freq', 'Func', 'State', 'Name', 'Model']:
                self.genericCheck("IO Card", line, 7)
                iocards.append({'slot': bits[0], 'bus': bits[1], 'side': bits[3], 'freq': bits[
                               4], 'maxfreq': bits[5], 'status': bits[7], 'rawmodel': " ".join(bits[8:])})
                # Bus#  Freq
                # Brd  Type  MHz   Slot  Name                              Model
                # ---  ----  ----  ----  --------------------------------  ----
                #  0   PCI-1  33     1   ebus
            elif headers == ['Bus#', 'Freq', 'Brd', 'Type', 'MHz', 'Slot', 'Name', 'Model']:
                iocards.append({'board': bits[0], 'bus': bits[1], 'freq': bits[
                               2], 'slot': bits[3], 'rawmodel': " ".join(bits[4:])})

                #                                 Bus  Max
                #             IO   Port Bus       Freq Bus  Dev,
                # FRU Name    Type  ID  Side Slot MHz  Freq Func State Name                              Model
                # ----------  ---- ---- ---- ---- ---- ---- ---- ----- --------
                # /N0/IB8/P0  PCI   28   B    1    33   33  2,0  ok    SUNW,emlxs-pci10df,fc00/fp (fp)   LP10000-S
            elif headers == ['Bus', 'Max', 'IO', 'Port', 'Bus', 'Freq', 'Bus', 'Dev,', 'FRU', 'Name', 'Type', 'ID', 'Side', 'Slot', 'MHz', 'Freq', 'Func', 'State', 'Name', 'Model']:
                self.genericCheck("IO Card", line, 8)
                iocards.append({'bus': bits[1], 'side': bits[3], 'slot': bits[4], 'freq': bits[
                               5], 'maxfreq': bits[6], 'status': bits[8], 'rawmodel': " ".join(bits[9:])})
                #     IO                                                Lane/Frq
                # LSB Type  LPID   RvID,DvID,VnID       BDF       State Act,  Max   Name                           Model
                # --- ----- ----   ------------------   --------- ----- -------
                #     Logical Path
                #     ------------
                # 00  PCIe  0      bc, 8532, 10b5       2,  0,  0  okay     8,    8  pci-pciex10b5,8532             N/A
                #     /pci@0,600000/pci@0
            elif headers == ['IO', 'Lane/Frq', 'LSB', 'Type', 'LPID', 'RvID,DvID,VnID', 'BDF', 'State', 'Act,', 'Max', 'Name', 'Model']:
                iocards = self.parseMultilineIO(buff, headers)
                break
                # Slot +            Bus   Name +                            Model
                # Status            Type  Path
                # ----------------------------------------------------------------------------
                # MB/REM/SASHBA     PCIE  LSILogic,sas-pciex1000,58         LSI,1068E
                #                            /pci@0/pci@0/pci@2/LSILogic,sas@0
            elif headers == ['Slot', '+', 'Bus', 'Name', '+', 'Model', 'Status', 'Type', 'Path']:
                iocards = self.parseMultilineIO(buff, headers)
            else:
                self.Fatal("Unhandled IO headers: %s" % headers)

        self.foundIo = True
        return iocards

    ##########################################################################
    def parseMultilineIO(self, buff, headers):
        iocards = []
        inheader = True
        tmpline = ''
        for line in buff:
            if '-----' in line:
                inheader = False
                continue
            if inheader:
                continue
            if 'Logical Path' in line:  # m4000 specialness
                continue
            if not tmpline:
                tmpline = line
                continue
            if tmpline:
                if headers == ['Bus', 'Freq', 'Slot', '+', 'Name', '+', 'Type', 'MHz', 'Status', 'Path', 'Model']:
                    self.genericCheck('IO Card', line, 0)
                    status = line.split()[0]
                    line = " ".join(line.split()[1:])     # Take out status
                line = "%s %s" % (tmpline, line)
                tmpline = ''
            bits = line.split()
            if headers == ['Bus', 'Freq', 'Slot', '+', 'Name', '+', 'Type', 'MHz', 'Status', 'Path', 'Model']:
                model = " ".join(bits[3:])
                iocards.append({'bus': bits[0], 'freq': bits[1], 'slot': bits[
                               2], 'rawmodel': model, 'status': status})
            elif headers == ['IO', 'Lane/Frq', 'LSB', 'Type', 'LPID', 'RvID,DvID,VnID', 'BDF', 'State', 'Act,', 'Max', 'Name', 'Model']:
                model = " ".join(bits[12:-1]).replace('N/A', '')
                iocards.append(
                    {'bus': bits[1], 'status': bits[9], 'rawmodel': model, 'slot': bits[2]})
            elif headers == ['Slot', '+', 'Bus', 'Name', '+', 'Model', 'Status', 'Type', 'Path']:
                iocards.append(
                    {'slot': bits[0], 'bus': bits[1], 'rawmodel': " ".join(bits[2:])})
            else:
                self.Fatal("Unhandled Multiline IO headers: %s" % headers)
        return iocards

    ##########################################################################
    def parseMem(self, buff):
        inheaders = True
        headers = []
        dimms = []

        for line in buff:
            if not line:
                continue
            if line.startswith('Memory Interleave Factor ='):
                continue
            bits = line.split()
            if '-----' in line:
                inheaders = False
                continue
            if inheaders:
                headers.extend(line.split())
                continue
            if headers == ['Logical', 'Logical', 'Logical', 'MC', 'Bank', 'Bank', 'Bank', 'DIMM', 'Interleave', 'Interleaved', 'Brd', 'ID', 'num', 'size', 'Status', 'Size', 'Factor', 'with']:
                self.genericCheck('Memory', line, 4)
                lbsize = int(bits[3][:-2])        # Logical Bank Size
                size = int(bits[5][:-2])          # DIMM Size
                qty = lbsize / size
                dimms.append({'dimmsize': bits[5], 'status': bits[
                             4], 'board': bits[0], 'lbsize': bits[3], 'qty': qty})

                #                    Logical  Logical  Logical
                #              Port  Bank     Bank     Bank       DIMM   Interleave  Interleave
                # Slot ID       ID   Number   Size     Status     Size   Factor      Segment
                # -----------  ----  -------  -------  --------  ------  ------
                # /SB03/P0/B0   96      0     1024MB   okay       512MB     8-way         0
            elif headers == ['Logical', 'Logical', 'Logical', 'Port', 'Bank', 'Bank', 'Bank', 'DIMM', 'Interleave', 'Interleave', 'Slot', 'ID', 'ID', 'Number', 'Size', 'Status', 'Size', 'Factor', 'Segment']:
                self.genericCheck('Memory', line, 4)
                lbsize = int(bits[3][:-2])        # Logical Bank Size
                size = int(bits[5][:-2])          # DIMM Size
                qty = lbsize / size
                dimms.append({'dimmsize': bits[5], 'status': bits[
                             4], 'board': bits[0], 'lbsize': bits[3], 'qty': qty})

                #        Interlv.  Socket   Size
                # Bank    Group     Name    (MB)  Status
                # ----    -----    ------   ----  ------
                #   0      none      1901   256      OK
            elif headers == ['Interlv.', 'Socket', 'Size', 'Bank', 'Group', 'Name', '(MB)', 'Status']:
                dimms.append({'dimmsize': bits[3], 'status': bits[4]})
                self.genericCheck('Memory', line, 4)

                # Segment Table:
                # -----------------------------------------------------------------------
                # Base Address       Size       Interleave Factor  Contains
                # -----------------------------------------------------------------------
                # 0x0                256MB             1           Label -
            elif headers == ['Segment', 'Table:']:
                if self.skipLine(line, ['Factor', '----']):
                    continue
                dimms.append({'dimmsize': bits[1]})
                #                      Logical  Logical  Logical
                #                Port  Bank     Bank     Bank         DIMM    Interleave  Interleave
                # FRU Name        ID   Num      Size     Status       Size    Factor      Segment
                # -------------  ----  ----     ------   -----------  ------  -
                # /N0/SB4/P2/B0   18    0      1024MB    pass          512MB     8-way       0
            elif headers == ['Logical', 'Logical', 'Logical', 'Port', 'Bank', 'Bank', 'Bank', 'DIMM', 'Interleave', 'Interleave', 'FRU', 'Name', 'ID', 'Num', 'Size', 'Status', 'Size', 'Factor', 'Segment']:
                self.genericCheck('Memory', line, 4)
                lbsize = int(bits[3][:-2])        # Logical Bank Size
                size = int(bits[5][:-2])          # DIMM Size
                qty = lbsize / size
                dimms.append({'dimmsize': bits[5], 'status': bits[
                             4], 'board': bits[0], 'lbsize': bits[3], 'qty': qty})
                #                                               Intrlv.  Intrlv.
                # Brd   Bank   MB    Status   Condition  Speed   Factor   With
                # ---  -----  ----  -------  ----------  -----  -------  ------
                #  0     0    1024   Active      OK       60ns    8-way     A
            elif headers == ['Intrlv.', 'Intrlv.', 'Brd', 'Bank', 'MB', 'Status', 'Condition', 'Speed', 'Factor', 'With']:
                self.genericCheck('Memory', line, 3)
                dimms.append({'dimmsize': bits[2], 'status': bits[3]})
                #        Memory  Available           Memory     DIMM      Number of
                # LSB    Group   Size                Status     Size      DIMMs
                # ---    ------  ------------------  -------    ------    -----
                # 00    A         8192MB            okay       1024MB
                # 8
            elif headers == ['Memory', 'Available', 'Memory', 'DIMM', 'Number', 'of', 'LSB', 'Group', 'Size', 'Status', 'Size', 'DIMMs']:
                self.genericCheck('Memory', line, 3)
                dimms.append(
                    {'dimmsize': bits[4], 'status': bits[3], 'qty': int(bits[-1])})
            # Memory  Available           Memory     DIMM    # of  Mirror  Interleave
            # LSB    Group   Size                Status     Size    DIMMs Mode    Factor
            # ---    ------  ------------------  -------    ------  ----- -----
            # 00    A         8192MB            okay       2048MB      4 no
            # 2-way
            elif headers == ['Memory', 'Available', 'Memory', 'DIMM', '#', 'of', 'Mirror', 'Interleave', 'LSB', 'Group', 'Size', 'Status', 'Size', 'DIMMs', 'Mode', 'Factor']:
                self.genericCheck('Memory', line, 3)
                dimms.append(
                    {'dimmsize': bits[4], 'status': bits[3], 'qty': int(bits[5])})
            else:
                self.Fatal("parseMem: unhandled headers: %s" % headers)
        self.foundMem = True
        return dimms

    ##########################################################################
    def parseMemmod(self, buff):
        """
    --------------------------------------------------
    ControllerID   GroupID  Labels         Status
    --------------------------------------------------
    0              0        MB/P0/B0/D0
    ...
    1              1        MB/P1/B1/D1
        """

        numdimms = 0
        for line in buff:
            if not line:
                continue
            if line[0].isdigit():
                numdimms += 1
        if numdimms:
            self.foundMem = True
        return numdimms

    ##########################################################################
    def dehumanise(self, str):
        """ Convert a string like 4GB into 4096
        1024 Megabytes -> 1024
        i.e. into megabytes
        """
        if str.endswith('GB'):
            return float(str.replace('GB', '')) * 1024
        elif str.endswith('MB'):
            return float(str.replace('MB', ''))
        elif str.endswith('Mb'):
            return float(str.replace('Mb', ''))
        elif str.endswith('Megabytes'):
            return float(str.replace('Megabytes', ''))
        else:
            self.Warning("Unhandled dehumanise: %s" % str)

    ##########################################################################
    def genericPrtdiag(self, modeDict):
        mode = 'unknown'
        oldmode = mode
        buff = []
        data = {}
        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.rstrip()
            if 'Memory size' in line:
                data['memsize'] = self.dehumanise(line.split(':')[-1])
            mode, skip = self.modeSelect(mode, line, modeDict)
            if mode != oldmode:
                if oldmode in modeDict and len(modeDict[oldmode]) >= 4:
                    data[oldmode] = modeDict[oldmode][3](buff)
                buff = []
                oldmode = mode
            else:
                buff.append(line)
        fh.close()

        # Debugging output below
#       for k in data.keys():
#           if type(data[k])==type([]):
#               self.Debug("genericPrtdiag: data[%s]=" % k)
#               for v in data[k]:
#                   self.Debug("genericPrtdiag:     %s" % v)
#           else:
#               self.Debug("genericPrtdiag: data[%s]=%s" % (k, data[k]))

        return data

    ##########################################################################
    def sun_e450(self):
        mode = 'unknown'
        self['numslots'] = 10
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'mem': ('', '== Memory ==', '', self.parseMem),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'environ': ('', '== Environmental Status ==', ''),
            'hwrev': ('', '== HW Revisions ==', ''),
            'fans': ('Fans:', '', ''),
            'psu': ('Power Supplies:', '', ''),
            'temp': ('System Temperatures:', '', ''),
            'nofailures': ('No failures found', '', ''),
        }
        cpuMap = {
            'US-II @ 248': {'desc': '250MHz UltraSPARC II Module', 'part': '501-4857', 'option': 'X2230A'},
            'US-II @ 296': {'desc': '300MHz UltraSPARC II Module', 'part': '501-4849', 'option': 'X2240A'},
            'US-II @ 400': {'desc': '400MHz UltraSPARC II Module', 'part': '501-5446', 'option': 'X2244A'},
            'US-II @ 480': {'desc': '480MHz UltraSPARC II Module', 'part': '501-5729', 'option': 'X2248A'},
        }
        memMap = {
            '128': {'desc': '128MB DIMM', 'part': '501-3136', 'option': 'X7004A', 'size': '128MB'},
            '256': {'desc': '256MB DIMM', 'part': '501-6005', 'option': 'X7005A', 'size': '256MB'},
            '64': {'desc': '64MB DIMM', 'part': '501-2480', 'option': 'X7003A', 'size': '64MB'},
        }

        data = self.genericPrtdiag(modeDict)

        self.genericCpu(data, cpuMap, 'e450')
#       for cpu in data['cpu']:
#           if cpu['speed'] in cpuMap:
#               self.addCpu(**cpuMap[cpu['speed']])
#           else:
#               self.Warning("Unhandled E450 CPU speed %s" % cpu['speed'])

        self.genericIo(data)
#       for io in data['iocards']:
#           loc=self.getLoc(board=io['board'], slot=io['slot'])
#           self.addCard(loc, rawmodel=io['rawmodel'], bus=io['bus'])

        self.genericMem(data, memMap, 'e450')
#       for mem in data['mem']:
#           if mem['dimmsize'] in memMap:
#               self.addMem(**memMap[mem['dimmsize']])
#           else:
#               self.Warning("Unhandled E450 Memory size %s" % mem['dimmsize'])

        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue
            if mode == 'mem':
                self.genericCheck(
                    'Memory', line, 4, ['Socket', 'Status', '-----', 'Interleave'])
            if mode == 'fans':
                self.genericCheck('Fan', line, 2, ['Status', '-----'])
            if mode == 'psu':
                self.genericCheck('Power Supply', line, 4, ['Status', '-----'])
        fh.close()

    ##########################################################################
    def addCard(self, loc, **kwargs):
        c = IoCard(self.config, **kwargs)
        if loc in self:
            self[loc].append(c)
        else:
            self[loc] = [c]

    ##########################################################################
    def sun_e4500(self):
        cardcount = 0
        # numslots depends on the boards that are plugged in: sbus=3,
        # graphics=2, pci=2
        mode = 'unknown'
        ecache = 0
        errbuffer = []
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'mem': ('', '== Memory ==', '', self.parseMem),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'environ': ('', '== Environmental Status ==', ''),
            'fans': ('Fans:', '', ''),
            'temp': ('System Temperatures', '', ''),
            'psu': ('Power Supplies:', '', ''),
            'hwrev': ('', '== Revisions ==', ''),
            'hwrev2': ('', '== HW Revisions ==', ''),
            'asic': ('ASIC Revisions', '', ''),
            'prom': ('System Board PROM revisions', '', ''),
            'detached': ('Detached Boards', '', ''),
            'nofailures': ('No failures found', '', ''),
            'yesfailures': ('Detected System Faults', '', ''),
            'badfru': ('Failed Field Replaceable Units', '', ''),
            'failureanalysis': ('Analysis of most recent', '', ''),
        }

        cpuMap = {
            "US-II @ 336": {'desc': "336Hz UltraSPARC II Module", 'part': "501-4363", 'option': "X2560A"},
            "US-II @ 400": {'desc': "400Hz UltraSPARC II Module", 'part': "501-6624", 'option': "X2580A"},
            "US-II @ 464": {'desc': "464Hz UltraSPARC II Module", 'part': "501-6623", 'option': "X2590A"},
        }
        memMap = {
            "64": {'desc': "64MB (8x8MB DIMMS)", 'part': "501-2652", 'option': "X7021A", 'size': '8MB'},
            "256": {'desc': "256MB (8x32MB DIMMS)", 'part': "501-2653", 'option': "X7022A", 'size': '32MB'},
            "1024": {'desc': "1GB (8x128MB DIMMS)", 'part': "501-2654", 'option': "X7023A", 'size': '128MB'},
            "2048": {'desc': "2GB (8x256MB DIMMS)", 'part': "501-5658", 'option': "X7026A", 'size': '256MB'},
        }

        data = self.genericPrtdiag(modeDict)

        self.genericCpu(data, cpuMap, 'e4500')
        self.genericMem(data, memMap, 'e4500')
        self.genericIo(data)

        fh = self.open('sysconfig/prtdiag-v.out')
        for line in fh:
            line = line.strip()
            mode, skip = self.modeSelect(mode, line, modeDict)
            if skip:
                continue

            if mode in ('yesfailures', 'failureanalysis', 'badfru'):
                errbuffer.append(line)
            if mode == 'fans':
                self.genericCheck('Fans', line, 1, ['Unit', '-----'])
            if mode == 'temp':
                self.genericCheck('Temp', line, 1, ['State', '-----'])
            if mode == 'psu':
                self.genericCheck('PSU', line, -1, ['Status', '-----'])
                if self.skipLine(line, ['Status', '----']):
                    continue
                if line[0] in "0123456789":
                    self.addPart(
                        desc="Power Supply", part=["300-1444", "300-1301"], option=["X954A", "X958A"])
            if mode == 'asic':
                if self.skipLine(line, ['ASIC', 'Attributes', '-------']):
                    continue
                if 'CPU' in line:
                    if ecache == '8.0':
                        self.addCpu(
                            desc="CPU/Memory Board (8MB Cache)", part='501-4312', option="X2601A", cache='8MB')
                    elif ecache == '2.0':
                        self.addCpu(
                            desc="CPU/Memory Board (2MB Cache)", part='501-2976', option="X2600A", cache='2MB')
                    else:
                        self.addCpu(
                            desc="CPU/Memory Board (??? Cache)", part='501-4882', option="X2602A")
                        self.Warning(
                            "Unknown CPU board type for E4500 (ecache=%s)" % ecache)
                elif 'Dual-SBus-SOC' in line:
                    self.addPart(desc="SBus I/O Board with SOC+",
                                 part=['501-4266', '501-4883'], option=["X2611A", "X2612A"])
                elif 'UPA-SBus-SOC+' in line:
                    self.addPart(desc="SBus I/O Board with SOC+",
                                 part=['501-4266', '501-4883'], option=["X2611A", "X2612A"])
                else:
                    self.Warning("Unknown E4500 Board: %s" % line)

            if mode == 'detached':
                if 'No failures found' in line:
                    mode = 'unknown'
                    continue
                errbuffer.append(line)

        if errbuffer:
            self.addIssue("Hardware Problem", text=errbuffer)

    ##########################################################################
    def sun_e6900(self):
        modeDict = {
            'cpu': ('', '== CPUs ==', '', self.parseCpu),
            'mem': ('', '== Memory Configuration ==', '', self.parseMem),
            'iocards': ('', '== IO Cards ==', '', self.parseIo),
            'activeb': ('', '== Active Boards for Domain ==', ''),
        }
        cpuMap = {
            'US-IV+ @ 1800': {'desc': "CPU/Memory Uniboard w/4x US IV+ 1.8GHz, 0MB", 'part': "540-7527"},
        }
        memMap = {
            '2048MB': {'desc': "8 GB (4x2GB DIMMS)", 'part': "540-6489", 'option': "X7058A-Z", 'size': '2Gb'},
        }

        data = self.genericPrtdiag(modeDict)
        self.genericCpu(data, cpuMap, 'e6900', modulo=4)
        self.genericMem(data, memMap, 'e6900')
        self.genericIo(data)

    ##########################################################################
    def ignoreLines(self, line, listofignores):
        """ Return true if any of the listofignores occurs in the line
        """
        line = line.strip()
        if not line:
            return True
        for ignore in listofignores:
            if ignore in line:
                return True
        return False

    ##########################################################################
    def parse_Solaris_prtfru(self):
        filename = 'fru/prtfru_-x.out'
        if not self.exists(filename):
            return
        f = self.open(filename)
        f.close()

    ##########################################################################
    def checkColumn(self, colnum, line):
        bits = line.split()
        if type(colnum) == type(1):
            colnum = [colnum]
        check = True
        for col in colnum:
            try:
                if bits[col] in ('OK', 'no_status', 'GOOD', 'on-line', 'okay', 'present', 'online', '[NO_FAULT]', 'ok', '[NO_FAULT', 'unknown', '-', 'pass', '[OK'):
                    return False
            except IndexError:
                continue
        return True

# EOF
