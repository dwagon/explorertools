#!/usr/local/bin/python
#
# Script to understand zone details
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: zones.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/zones.py $

import os
import sys
import getopt
import re
import explorerbase

##########################################################################
# Zone ###################################################################
##########################################################################


class Zone(explorerbase.ExplorerBase):
    ##########################################################################

    def __init__(self, config, zonename):
        explorerbase.ExplorerBase.__init__(self, config)
        self.objname = zonename
        self['zhostname'] = "unknown"
        try:
            self.parseZoneCfg()
            self.parseZoneSysconfig()
            self.parseIfconfigs()
        except UserWarning, err:
            self.Warning(err)

    ##########################################################################
    def parseIfconfigs(self):
        ifc = 'zones/%s/sysconfig/ifconfig-a.out' % self.name()
        if not self.exists(ifc):
            return
        self['ipaddrs'] = []
        f = self.open(ifc)
        for line in f:
            if 'inet' in line:
                m = re.search('inet (?P<ipaddr>\S+) n', line)
                if m:
                    if '127.0.0.1' != m.group('ipaddr'):
                        self['ipaddrs'].append(m.group('ipaddr'))
                else:
                    self.Warning("No match: %s" % line)
        f.close()

    ##########################################################################
    def parseZoneSysconfig(self):
        unam = 'zones/%s/sysconfig/uname-a.out' % self.name()
        if self.exists(unam):
            f = self.open(unam)
            data = f.readline()
            f.close()
            if data:
                self['zhostname'] = data.split()[1]
                return

    ##########################################################################
    def analyse(self):
        pass

    ##########################################################################
    def parseZoneCfg(self):
        f = self.open('sysconfig/zonecfg-z-%s-export.out' % self.name())
        for line in f:
            line = line.strip()
            if line.startswith('set address'):
                m = re.search('set address=(?P<ipaddr>[0-9\.]*)(.*)', line)
                if not 'ipaddr' in self:
                    self['ipaddr'] = []
                self['ipaddr'].append(m.group('ipaddr'))
            if line.startswith('set physical'):
                self['physical'] = line.split('=')[1]
            if line.startswith('set autoboot'):
                self['autoboot'] = line.split('=')[1]
        f.close()

##########################################################################
# Zones ##################################################################
##########################################################################


class Zones(explorerbase.ExplorerBase):

    """Understand explorer output with respect to zones
    """
    ##########################################################################

    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        if not self.exists('zones'):
            return
        try:
            self.parseZones()
        except UserWarning, err:
            self.Warning(err)
            return

    ##########################################################################
    def parseZones(self):
        f = self.open('etc/zones/index')
        for line in f:
            if line.startswith('#'):
                continue
            bits = line.strip().split(':')
            if bits[0] == 'global':
                continue
            zonename = bits[0]
            zone = Zone(self.config, zonename)
            zone['status'] = bits[1]
            if zone['status'] != 'installed':
                self.addConcern('status', obj=zonename, text="Zone %s is not operational status=%s" % (
                    zonename, zone['status']))
            zone['path'] = bits[2]
            self[zonename] = zone
        f.close()

    ##########################################################################
    def zoneNames(self):
        return sorted(self.data.keys())

    ##########################################################################
    def zoneList(self):
        return [self[zone] for zone in self.zoneNames()]

    ##########################################################################
    def analyse(self):
        for zone in self.zoneList():
            zone.analyse()
            self.inheritIssues(zone)

# EOF
