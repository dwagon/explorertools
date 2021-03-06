#!/usr/local/bin/python
#
# Script to understand misc details
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: misc.py 2398 2012-06-04 02:00:57Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/misc.py $

import os
import sys
import getopt
import re
import time
import explorer
import explorerbase

##########################################################################
# miscDetails ############################################################
##########################################################################


class miscDetails(explorerbase.ExplorerBase):

    """ Class to represent misc details extracted from an explorer
    """
    ##########################################################################

    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.config = config
        self.parse()

    ##########################################################################
    def parse(self):
        self.parseExplorer()

    ##########################################################################
    def getHostname(self, orighostname):
        """ Sosreport returns a different hostname than uname (it strips
        the '-'s from the hostname.
        Also other problems where the prime external name is not the name that
        is returned by uname.
        """
        self.orighostname = orighostname
        self.hostname = orighostname      # Need this for sosreport
        fname = None
        if self.exists('uname'):
            fname = 'uname'
        elif self.exists('sysconfig/uname-a.out'):
            fname = 'sysconfig/uname-a.out'
        if fname:
            f = self.open(fname)
            for line in f:
                if 'uname' not in line:
                    hostname = line.split()[1]
            f.close()
        else:
            hostname = orighostname

        if '.' in hostname:
            hostname = hostname[:hostname.index('.')]

        return hostname

    ##########################################################################
    def parseExplorer(self):
        self.getExplorerVersion()
        if self.config['explorertype'] == 'solaris':
            self.getEeprom()
            self.getModules()
            self.getLdoms()
        elif self.config['explorertype'] == 'linux':
            pass
        self.getSerial()
        self.getPackages()
        self.getPatches()
        self.getProcesses()
        self.getNetListeners()
        self.getWWNs()
        self.getFCinfo()
        self.getPrinters()

    ##########################################################################
    def getModules(self):
        fname = 'sysconfig/modinfo-c.out'
        self['modules'] = []
        if not self.exists(fname):
            return
        f = self.open(fname)
        for line in f:
            line = line.strip()
            if not line or 'Name' in line or 'UNINSTALLED' in line:
                continue
            self['modules'].append(line.split()[2])

    ##########################################################################
    def getPrinters(self):
        """ List which print queues are configured on this server
        """
        fname = 'lp/printers.conf'
        self['printers'] = []
        if not self.exists(fname):
            return
        f = self.open(fname)
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                continue
            if line.startswith(':'):
                continue
            printer = line.split(':')[0]
            if '|' in printer:
                printer = printer.split('|')[0]
            self['printers'].append(printer.lower())
        f.close()

    ##########################################################################
    def getFCinfo(self):
        """ Get details about all the FCs attached to the server
        """
        fname = 'sysconfig/fcinfo.out'
        if not self.exists(fname):
            return
        data = ""
        self['fcinfo'] = []
        f = self.open(fname)
        for line in f:
            if line.startswith('No Adapters Found'):
                return
            if line.startswith('HBA'):
                self.parseFcinfo_stanza(data)
                data = line
            else:
                data += line
        self.parseFcinfo_stanza(data)
        f.close()

    ##########################################################################
    def parseFcinfo_stanza(self, buffer):
        if not buffer:
            return
        data = {}
        for line in buffer.splitlines():
            bits = line.strip().split(':', 1)
            data[bits[0]] = bits[1].strip()
        self['fcinfo'].append(data)

    ##########################################################################
    def getWWNs(self):
        """ Report on which WWNs are associated with his host
            WWNs are hidden in a few different places.
        """
        wwnset = set()
        if self.exists('sysconfig/fcinfo.out'):
            f = self.open('sysconfig/fcinfo.out')
            for line in f:
                if 'WWN' in line:
                    wwn = line.split(':')[-1].strip()
                    wwnset.add(wwn)
            f.close()

        lxlist = self.glob('disks/luxadm_display_*')
        for lf in lxlist:
            f = self.open(lf)
            for line in f:
                if 'WWN' in line:
                    wwnset.add(line.strip().split()[-1])
            f.close()

        # JNICs appear here and sometimes no where else
        if self.exists('sysconfig/prtpicl-v.out'):
            f = self.open('sysconfig/prtpicl-v.out')
            for line in f:
                if 'wwpn' in line:
                    wwnset.add(line.strip().split()[-1])
                if 'wwnn' in line:
                    wwnset.add(line.strip().split()[-1])
            f.close()

        tmp = list(wwnset)
        for x in tmp[:]:
            if x.startswith('0x'):
                tmp.append(x[2:])
                tmp.remove(x)
            if x[0] not in '0123456789abcdef':
                tmp.remove(x)

        self['wwn'] = tmp

    ##########################################################################
    def getNetListeners(self):
        """ Report on what ports that the server is listening on
        """
        self['netlisteners'] = {}
        if self.config['explorertype'] == 'solaris':
            self.getSolarisNetListeners()

    ##########################################################################
    def getSolarisNetListeners(self):
        filename = 'netinfo/netstat-an.out'
        if not self.exists(filename):
            self.Warning("%s doesn't exist" % filename)
            return
        f = self.open(filename)
        mode = None
        for line in f:
            line = line.strip()
            if line.startswith('----'):
                continue
            if line.startswith('Local Address'):
                continue
            if line.startswith('UDP: IPv4'):
                mode = 'ipv4_udp'
                self['netlisteners'][mode] = []
            if line.startswith('UDP: IPv6'):
                mode = 'ipv6_udp'
                self['netlisteners'][mode] = []
            if line.startswith('TCP: IPv4'):
                mode = 'ipv4_tcp'
                self['netlisteners'][mode] = []
            if line.startswith('TCP: IPv6'):
                mode = 'ipv6_tcp'
                self['netlisteners'][mode] = []
            if line.startswith('SCTP'):
                break
            if mode == 'ipv4_udp':
                if 'Idle' in line and line.startswith('*'):
                    bits = line.split()
                    self['netlisteners'][mode].append(
                        bits[0].replace('*.', ''))
            if mode == 'ipv6_udp':
                if 'Idle' in line and line.startswith('*'):
                    bits = line.split()
                    self['netlisteners'][mode].append(
                        bits[0].replace('*.', ''))
            if mode == 'ipv4_tcp':
                if 'LISTEN' in line and line.startswith('*'):
                    bits = line.split()
                    self['netlisteners'][mode].append(
                        bits[0].replace('*.', ''))
            if mode == 'ipv6_tcp':
                if 'LISTEN' in line and line.startswith('*'):
                    bits = line.split()
                    self['netlisteners'][mode].append(
                        bits[0].replace('*.', ''))
        f.close()

    ##########################################################################
    def getLdoms(self):
        """ Report on any Solaris LDOMs we have
        All systems must have memory so check memory allocation
        is a reasonable way of getting the definitive list
        """
        filename = 'sysconfig/ldm_list-devices_-a.out'
        if not self.exists(filename):
            return
        self['ldoms'] = []
        f = self.open(filename)
        inmemory = False
        for line in f:
            line = line.strip()
            if line == 'MEMORY':
                inmemory = True
                continue
            if line == 'IO':
                inmemory = False
            if inmemory:
                try:
                    bound = line.split()[2]
                    if bound not in ('primary', 'BOUND', '_sys_'):
                        self['ldoms'].append(bound)
                except IndexError:
                    pass
        f.close()

    ##########################################################################
    def analyse(self):
        if 'eeprom' in self and 'auto-boot?' in self['eeprom'] and self['eeprom']['auto-boot?'] == 'false':
            self.addIssue(
                'autoboot', category='eeprom', text='auto-boot? set to false')

    ##########################################################################
    def getProcesses(self):
        processes = {}
        mode = None
        if self.config['explorertype'] == 'solaris':
            if self.exists('sysconfig/ps-efZ.out'):
                f = self.open('sysconfig/ps-efZ.out')
                mode = 'zone'
            elif self.exists('sysconfig/ps-ef.out'):
                f = self.open('sysconfig/ps-ef.out')
                mode = 'vanilla'
            else:
                self.Warning("No usable ps output")
                return
            psreg = re.compile('.* \d+:\d\d (.*)$')
            for line in f:
                line = line.strip()
                p = {}
                bits = line.split()
                if mode == 'zone':
                    if line.startswith('ZONE'):
                        continue
                    p['zone'] = bits[0]
                    p['uid'] = bits[1]
                    p['pid'] = bits[2]
                    p['ppid'] = bits[3]
                else:
                    if line.startswith('UID'):
                        continue
                    p['uid'] = bits[0]
                    p['pid'] = bits[1]
                    p['ppid'] = bits[2]
                m = psreg.match(line)
                if not m:
                    # Somehow you can get processes with no name
                    p['cmd'] = 'Unnamed'
                else:
                    p['cmd'] = m.group(1)
                processes[p['pid']] = p
            f.close()
        elif self.config['explorertype'] == 'linux':
            if self.exists('ps'):
                f = self.open('ps')
                for line in f:
                    line = line.strip()
                    if line.startswith('USER'):
                        continue
                    bits = line.split()
                    p = {}
                    p['uid'] = bits[0]
                    p['pid'] = bits[1]
                    p['cmd'] = bits[10]
                    processes[p['pid']] = p
                f.close()
        self['processes'] = processes

    ##########################################################################
    def getPatches(self):
        self['patches'] = {}
        if self.config['explorertype'] == 'solaris':
            filename = 'patch+pkg/patch_date.out'
            if not self.exists(filename):
                self.Warning("Couldn't read patch dates: %s" % filename)
                return
            f = self.open(filename)
            for line in f:
                line = line.strip()
                if line.startswith('total'):
                    continue
                bits = line.split()
                patchnum = bits[-1]
                patchdatestr = " ".join(bits[5:-1])
                # Patch dates are in either of these two formats
                # Jul  9  2008
                # May 18 13:31
                try:
                    patchdate = time.strptime(patchdatestr, '%b %d %Y')
                except ValueError:
                    # Add the year - for files newer than 6 months
                    year = time.localtime()[0]
                    pdate = patchdatestr + " %s" % year
                    d = time.strptime(pdate, '%b %d %H:%S %Y')
                    if time.mktime(d) > time.time():
                        year -= 1
                    pdate = patchdatestr + " %s" % year
                    patchdate = time.strptime(pdate, '%b %d %H:%S %Y')
                self['patches'][patchnum] = time.strftime(
                    '%Y-%m-%d', patchdate)
            f.close()

    ##########################################################################
    def getPackages(self):
        self['packages'] = {}
        if self.config['explorertype'] == 'solaris':
            if not self.exists('patch+pkg/pkginfo-l.out'):
                return
            f = self.open('patch+pkg/pkginfo-l.out')
            for line in f:
                line = line.strip()
                if self.lineSkipper(line, start=['Long pkg', '=====']):
                    continue
                if line.startswith('PKGINST:'):
                    package = line[line.find(':') + 1:].strip()
                if line.startswith('VERSION:'):
                    version = line[line.find(':') + 1:].strip()
                    self['packages'][package] = version
            f.close()
        elif self.config['explorertype'] == 'linux':
            if not self.exists('installed-rpms'):
                return
            f = self.open('installed-rpms')
            for line in f:
                line = line.strip()
                if ' ' in line:
                    line = line.split()[0]
                bits = line.split('-')
                package = ''
                version = ''
                flag = False
                for b in bits:
                    if b[0] in '0123456789':
                        flag = True
                    if flag:
                        version += "%s-" % b
                    else:
                        package += "%s-" % b
                self['packages'][package[:-1]] = version[:-1]
            f.close()

    ##########################################################################
    def getEeprom(self):
        """ Check for eeprom settings
        """
        self['eeprom'] = {}
        if not self.exists('sysconfig/eeprom.out'):
            self.Warning("Couldn't read eeprom settings")
            return
        f = self.open('sysconfig/eeprom.out')
        for line in f:
            line = line.strip()
            if '=' in line:
                bits = line.split('=')
                self['eeprom'][bits[0]] = bits[1]
        f.close()

    ##########################################################################
    def getSerial(self):
        if self.config['explorertype'] == 'solaris':
            if self.getIpmiSerial():
                return
            if self.getTxSerial():
                return
            if self.getPrtdiag():
                return
        # if self.getChassis():
        #           return
        if self.config['explorertype'] == 'linux':
            if self.getDmidecode():
                return
            if self.getHardwarePy():
                return

    ##########################################################################
    def getHardwarePy(self):
        """ This is for old school linux only - sysreport
        """
        if not self.exists('hardware.py'):
            return False
        f = self.open('hardware.py')
        for line in f:
            if 'asset' in line:
                m = re.search('\(system: (?P<system>\S+)\)', line.strip())
                if m:
                    sn = m.group('system')
                    if sn.lower() not in ('xxxxxxx', 'serial#'):
                        self['serial'] = sn
                    return True
        f.close()
        return False

    ##########################################################################
    def getDmidecode(self):
        """ This is for linux only """
        if not self.exists('dmidecode'):
            return False
        data = []
        f = self.open('dmidecode')
        for line in f:
            line = line.strip()
            if line.startswith('Handle'):
                if 'System Information' in data:
                    for d in data:
                        if 'Serial Number' in d:
                            sn = d.split(':')[1].strip()
                            if '0000000' not in sn and sn not in ('Not Available', '00'):
                                self['serial'] = sn
                            return True
                data = []
            else:
                data.append(line)
        f.close()
        return False

    ##########################################################################
    def getChassis(self):
        """ Get the serial number from the 'chassis_serial' file if it exists
        I don't trust this as it takes its input from dubious sources such
        as eeprom settings
        """
        if not self.exists('sysconfig/chassis_serial.out'):
            return False
        f = self.open('sysconfig/chassis_serial.out')
        line = f.readline().strip()
        f.close()
        if line:
            if 'unknown' in line:
                return False
            if '_' in line:     # It has sn_sn_sn too often - don't know why
                self['serial'] = line.split('_')[0]
            else:
                self['serial'] = line
            return True
        return False

    ##########################################################################
    def getPrtdiag(self):
        """ Get the serial number from prtdiag if available
        """
        if not self.exists('sysconfig/prtdiag-v.out'):
            return False
        mode = False
        f = self.open('sysconfig/prtdiag-v.out')
        for line in f:
            line = line.strip()
            if 'Chassis Serial Number' in line:
                mode = True
                continue
            if mode:
                if not line.startswith('---'):
                    line = line.strip()
                    self['serial'] = self.sanitiseSerial(line)
                    #self.Warning("prtdiag serial='%s' -> %s" % (line, self['serial']))
                    return True
        f.close()
        return False

    ##########################################################################
    def sanitiseSerial(self, sn):
        """
        Occassionaly we get wierd serial numbers that have 
        0111apo- or other things before them
        """
        if '-' in sn:
            sn = sn[sn.find('-') + 1:]
        return sn.strip()

    ##########################################################################
    def getTxSerial(self):
        """ Get the serial number from hosts that have Tx00 details
        """
        if self.exists("Tx000/showplatform_-v"):
            f = self.open("Tx000/showplatform_-v")
            for line in f:
                line = line.strip()
                if "Serial Number" in line:
                    self['serial'] = self.sanitiseSerial(line.split()[-1])
                    #self.Warning("txA serial='%s' -> %s" % (line, self['serial']))
                    return True
                if "Blade Serial Number:" in line:
                    self['serial'] = self.sanitiseSerial(line.split()[-1])
                    #self.Warning("txB serial='%s' -> %s" % (line, self['serial']))
                    return True
            f.close()

        if not self.exists("Tx000/showfru"):
            return False
        f = self.open("Tx000/showfru")
        for line in f:
            line = line.strip()
            if 'System_Id' in line:
                sn = line.split(':')[-1]
                # Occassionally they put two numbers on the line
                if len(sn.split()) != 1:
                    sn = sn.split()[0]    # Don't know what the second one is
                self['serial'] = self.sanitiseSerial(sn)
                #self.Warning("txC serial='%s' -> %s" % (line, self['serial']))
                return True
        f.close()
        return False

    ##########################################################################
    def getIpmiSerial(self):
        """ Get the host serial number from hosts that have ipmitool working"""
        if not self.exists('ipmi/ipmitool_fru.out'):
            return False
        f = self.open('ipmi/ipmitool_fru.out')
        stanza = False
        serial = None
        for line in f:
            line = line.strip()
            if not line:
                stanza = False
            if line.startswith('FRU Device'):
                if ' mb.fru ' in line or 'Builtin FRU' in line or '/SYS' in line:
                    stanza = True

            if not stanza:
                continue
            if 'Product Serial' in line:
                serial = line.split(':')[-1].strip()
                # Occassionally the MAC address gets picked up instead
                if len(serial) < 5:
                    continue
                if serial != '0000000000':
                    self['serial'] = serial.lower()
                    #self.Warning("ipmiA serial='%s' -> %s" % (line, self['serial']))
                    return True
        f.close()
        return False

    ##########################################################################
    def getExplorerVersion(self):
        if self.config['explorertype'] == 'solaris':
            if not self.exists('README'):
                self.Warning('No README found')
                return
            f = self.open('README')
            line = f.readline()
            f.close()
            m = re.search('\(Version (?P<version>.*)\)', line)
            if m:
                self['explorerversion'] = m.group('version').lower()
            else:
                m = re.search('Version (?P<version>\S+)\s', line)
                if m:
                    self['explorerversion'] = m.group('version').lower()
        elif self.config['explorertype'] == 'linux':
            if self.exists('installed-rpms'):
                f = self.open('installed-rpms')
                for line in f:
                    if 'sysreport-' in line:
                        bits = line.strip().split('-')
                        self['explorerversion'] = "-".join(bits[0:2])
                        break
                    if 'sos-' in line:
                        bits = line.strip().split('-')
                        self['explorerversion'] = "-".join(bits[0:2])
                        break
                f.close()

# EOF
