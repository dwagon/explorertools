#!/usr/local/bin/python
#
# Script to understand host details
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: hostdet.py 3035 2012-10-01 07:19:27Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/hostdet.py $

import os
import sys
import getopt
import re
import explorerbase
import hardware

##########################################################################
# Host ###################################################################
##########################################################################


class Host(explorerbase.ExplorerBase):

    """Understand explorer output with respect to details about hosts
    """
    ##########################################################################

    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.parse()

    ##########################################################################
    def parse(self):
        self['osrev'] = ''
        self.parseUname()
        self.parseRam()
        self.parseHardware()
        self.parseSolaris_sysdef()
        self.parseUptime()
        self.parseReboot()
        self.parseRelease()

    ##########################################################################
    def parseRelease(self):
        if self.config['explorertype'] == 'solaris':
            if not self.exists('etc/release'):
                self['osrelease'] = ""
                return
            f = self.open('etc/release')
        if self.config['explorertype'] == 'linux':
            if self.exists('etc/redhat-release'):
                f = self.open('etc/redhat-release')
            else:
                self.Warning("No release details available")
                return
        data = f.readline()
        f.close()
        self['osrelease'] = data.strip().lower()

    ##########################################################################
    def parseReboot(self):
        if self.config['explorertype'] != 'solaris':
            return
        try:
            f = self.open('sysconfig/last-20-reboot.out')
            data = f.readline()
            f.close()
            self['reboot'] = " ".join(data.split()[3:])
        except UserWarning, err:
            self.Warning(err)

    ##########################################################################
    def analyse(self):
        pass

    ##########################################################################
    def parseUptime(self):
        self['uptime'] = 'unknown'
        try:
            if self.config['explorertype'] == 'solaris':
                f = self.open('sysconfig/uptime.out')
            if self.config['explorertype'] == 'linux':
                f = self.open('uptime')
            for line in f:
                line = line.strip()
                m = re.search('.* up (?P<uptime>.*),\s+\d+ user.*', line)
                if m:
                    self['uptime'] = m.group('uptime')
            f.close()
        except UserWarning, err:
            self.Warning(err)

    ##########################################################################
    def parseSolaris_sysdef(self):
        if self.config['explorertype'] != 'solaris':
            return
        try:
            f = self.open('sysconfig/sysdef.out')
            mode = ''
            for line in f:
                if 'Hostid' in line:
                    mode = 'hostid'
                if mode == 'hostid' and not line.startswith('*'):
                    self['hostid'] = line.strip()
                    mode = ''
            f.close()
        except UserWarning, err:
            self.Warning(err)

    ##########################################################################
    def shortHwdesc(self, fulldesc):
        """ Convert the full, rather wordy, description to a more terse version"""
        if '(' in fulldesc:
            fulldesc = re.sub('(.*)\(.*?\)(.*)', r'\1\2', fulldesc)
        hwdesc = fulldesc.strip()
        hwdesc = hwdesc.replace('Sun Microsystems, Inc.', '')
        hwdesc = hwdesc.replace('oracle corporation', '')
        hwdesc = hwdesc.replace('Sun Microsystems', '')
        hwdesc = hwdesc.replace('UPA/PCI', '')
        hwdesc = hwdesc.replace('sun4u', '')
        hwdesc = hwdesc.strip().lower()
        return hwdesc

    ##########################################################################
    def parseLinux_hardwarepy(self):
        f = self.open('hardware.py')
        for line in f:
            line = line.strip()
            if line.startswith("'system'"):
                hware = line.split(':')[-1].strip()[1:-1]
                hwtype, hwname = self.getHardware(hware)
                self['hwtype'] = hwtype
                self['hardware'] = hwname
            if line.startswith("'bios_version'"):
                self['bios'] = line.split(':')[-1].strip()[1:-1].strip()

    ##########################################################################
    def parseLinux_dmidecode(self):
        data = []
        f = self.open('dmidecode')
        for line in f:
            line = line.strip()
            if line.startswith('Handle'):
                if 'System Information' in data:
                    for d in data:
                        if 'Product Name' in d:
                            hwdesc = d.split(':')[1].strip()
                            hwtype, hwname = self.getHardware(hwdesc)
                            self['hwdesc'] = hwdesc
                            self['hwtype'] = hwtype
                            self['hardware'] = hwname
                elif 'BIOS Information' in data:
                    for d in data:
                        if 'Version' in d:
                            self['bios'] = d.split(':')[1].strip()
                data = []
            else:
                data.append(line)
        f.close()

    ##########################################################################
    def parseLinux(self):
        try:
            self.parseLinux_dmidecode()
        except UserWarning, err:
            pass
        try:
            self.parseLinux_hardwarepy()
        except UserWarning, err:
            pass

    ##########################################################################
    def parseHardware(self):
        """ Try all the various methods to get the type of hardware that this
        box is
        """
        self['obp'] = ''
        self['post'] = ''
        self['hardware'] = ''
        try:
            if self.config['explorertype'] == 'linux':
                self.parseLinux()
                return
            if self.exists('sysconfig/prtdiag-v.out'):
                self.parsePrtdiag()
            if self.exists('Tx000/showhost'):
                self.parseShowhost()
            if self.exists('Tx000/showplatform_-v'):
                self.parseShowplatform()
            if self.exists('ipmi/ipmitool_fru.out'):
                self.parseIpmitool()
            if self.exists('sysconfig/smbios.out'):
                self.parseSmbios()
            if not self['hardware']:
                self.parseUnameHW()
            self.checkForLdom()
        except UserWarning, err:
            self.Warning("%s" % err)

    ##########################################################################
    def checkForLdom(self):
        """ An LDOM doesn't know it is an ldom - except that it does have
        some modules loadded into the kernel that phyicals don't. E.g. 
        vdc - virtual disc controller

        New ldoms (v2.?) have a command called virtinfo which does know that
        it is a virtual and also knows control domain :)
        # DOMAINROLE|impl=LDoms|control=true|io=true|service=true|root=true
        # DOMAINROLE|impl=LDoms|control=false|io=false|service=false|root=false
        """
        if self.exists('sysconfig/virtinfo-a-p.out'):
            isldom = False
            for line in self.open('sysconfig/virtinfo-a-p.out'):
                if line.startswith('DOMAINROLE'):
                    if 'true' not in line:
                        isldom = True
                        self['hwtype'] = 'virtual'
                        self['vmtype'] = 'ldom'
                if line.startswith('DOMAINCONTROL'):
                    name = line.split('|')[1].split('=')[1]
                    if isldom:
                        self['virtualmaster'] = name.strip()
            return

        if not self.exists('sysconfig/modinfo-c.out'):
            return
        f = self.open('sysconfig/modinfo-c.out')
        for line in f:
            if 'vdc' in line and 'LOADED/INSTALLED' in line:
                self['hwtype'] = 'virtual'
                break

    ##########################################################################
    def parseSmbios(self):
        if self['hardware']:
            return
        f = self.open('sysconfig/smbios.out')
        for line in f:
            if 'Product:' in line:
                hwname = line.split(':')[1].strip()
                hwtype, hwname = self.getHardware(hwname)
                self['hwtype'] = hwtype
                self['hardware'] = hwname
        f.close()

    ##########################################################################
    def parseUnameHW(self):
        if self['hardware']:
            return
        f = self.open('sysconfig/uname-a.out')
        data = f.readline()
        f.close()
        hwuname = data.strip().split()[-1]
        hwtype, hwname = self.getHardware(hwuname)
        self['hwtype'] = hwtype
        self['hardware'] = hwname
        f.close()

    ##########################################################################
    def parseIpmitool(self):
        if self['hardware']:
            return
        f = self.open('ipmi/ipmitool_fru.out')
        mode = False
        for line in f:
            line = line.strip()
            if line.startswith('FRU Device Description'):
                name = line.split(
                    ':', 1)[-1].split()[0].strip().replace('.fru', '')
                if name in ('mb', 'Builtin'):
                    mode = True
                else:
                    mode = False
            if mode and 'Product Name' in line:
                hwname = line.split(':')[-1].strip()
                if hwname in ('ilom', 'ILOM'):
                    continue
                hwtype, hwname = self.getHardware(hwname)
                self['hwtype'] = hwtype
                self['hardware'] = hwname
        f.close()

    ##########################################################################
    def parseShowplatform(self):
        if self['hardware']:
            return
        f = self.open('Tx000/showplatform_-v')
        for line in f:
            line = line.strip()
            if line.startswith('SUNW,'):
                hwtype, hwname = self.getHardware(line)
                self['hwtype'] = hwtype
                self['hardware'] = hwname
        f.close()

    ##########################################################################
    def parseShowhost(self):
        f = self.open('Tx000/showhost')
        for line in f:
            line = line.strip()
            if line.startswith('Hypervisor'):
                self['hypervisor'] = " ".join(line.split()[:2])
            if line.startswith('OBP'):
                self['obp'] = " ".join(line.split()[:2])
            if line.startswith('POST'):
                self['post'] = " ".join(line.split()[:2])
        f.close()

    ##########################################################################
    def parsePrtdiag(self):
        f = self.open('sysconfig/prtdiag-v.out')
        datestr = "\d{4}/\d{2}/\d{2} \d{2}:\d{2}"
        for line in f:
            line = line.strip()
            if line.startswith('Memory Size'):
                bits = line.split(':')
                ram = bits[1]
                self['ram'] = ram
                continue
            if line.startswith('System Configuration'):
                hwdesc = self.shortHwdesc(line.split(':')[-1])
                hwtype, hwname = self.getHardware(hwdesc)
                self['hwtype'] = hwtype
                self['hardware'] = hwname
                self['hwdesc'] = hwdesc.replace(' ', '_')
            if 'OBP' in line:
                m = re.search(
                    '(?P<obp>OBP\s+\S+) %s\s+(?P<post>POST\s+\S+) %s' % (datestr, datestr), line)
                if m:
                    self['obp'] = m.group('obp')
                    self['post'] = m.group('post')
                else:
                    m = re.search('(?P<obp>OBP \S+) %s' % datestr, line)
                    if m:
                        self['obp'] = m.group('obp')
            if line.startswith('BIOS Configuration'):
                self['bios'] = line.split(':', 1)[-1].strip()
        f.close()

    ##########################################################################
    def parseRam(self):
        try:
            if self.config['explorertype'] == 'solaris':
                self['os'] = 'solaris'
                f = self.open('sysconfig/prtconf-vp.out')
                for line in f:
                    if line.startswith('Memory size'):
                        ram = line.split()[-2]
                        self['ram'] = ram
                f.close()
            elif self.config['explorertype'] == 'linux':
                self['os'] = 'linux'
                f = self.open('free')
                for line in f:
                    if line.startswith('Mem:'):
                        self['ram'] = int(line.split()[1]) / 1024
                f.close()
        except UserWarning, err:
            self.Warning(err)
            self['ram'] = 0

    ##########################################################################
    def parseUname(self):
        """
        Analyse uname output
        """
        self['arch'] = ''
        if self.config['explorertype'] == 'solaris':
            f = self.open('sysconfig/uname-a.out')
            line = f.readline()
            f.close()
            self['uname'] = line.strip()
            if self.exists('sysconfig/uname-X.out'):
                f = self.open('sysconfig/uname-X.out')
                for line in f:
                    line = line.rstrip()
                    if line.startswith('Release'):
                        self['osrev'] = line.split()[-1]
                    if line.startswith('KernelID'):
                        self['kernelpatch'] = line.split()[-1]
                    if line.startswith('Machine'):
                        self['arch'] = line.split()[-1]
                f.close()
            elif self.exists('sysconfig/uname-a.out'):
                f = self.open('sysconfig/uname-a.out')
                line = f.readline()
                f.close()
                bits = line.strip().split()
                self['osrev'] = bits[2]
                self['kernelpatch'] = bits[3]
                self['arch'] = bits[4]
            else:
                self.Warning("No solaris uname output to analyse")
                return

        elif self.config['explorertype'] == 'linux':
            if not self.exists('uname'):
                self.Warning("No linux uname output to analyse")
                return
            f = self.open('uname')
            for line in f:
                if 'uname' in line:
                    continue
                bits = line.strip().split()
                self['osrev'] = bits[2]
                self['kernelpatch'] = ''
                self['arch'] = bits[-2]
                self['uname'] = line.strip()
            f.close()

    ##########################################################################
    def getHardware(self, hwdesc):
        hwdesc = hwdesc.replace('IBM IBM', 'IBM')
        hwdesc = hwdesc.replace('sun4u', '')
        if hwdesc.startswith('"') or hwdesc.startswith("'"):
            hwdesc = hwdesc[1:]
        if hwdesc.endswith('"') or hwdesc.endswith("'"):
            hwdesc = hwdesc[:-1]
        hwdesc = hwdesc.strip()
        try:
            hwtype, hwname = hardware.getHardware(hwdesc)
        except hardware.UnknownHardware:
            self.Warning("Unknown hardware: %s" % hwdesc)
            hwtype = "unknown"
            hwname = "unknown"
        return hwtype, hwname

# EOF
