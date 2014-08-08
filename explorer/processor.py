#!/usr/local/bin/python
#
# Script to understand processor details
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: processor.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/processor.py $

import os
import sys
import getopt
import re
import math
import explorerbase

verbflag = 0

##########################################################################
# Processor ##############################################################
##########################################################################


class Processor(explorerbase.ExplorerBase):
    ##########################################################################

    def __init__(self, config, cpunum):
        explorerbase.ExplorerBase.__init__(self, config)
        self.objname = cpunum

    ##########################################################################
    def analyse(self):
        pass

##########################################################################
# Processors #############################################################
##########################################################################


class Processors(explorerbase.ExplorerBase):
    ##########################################################################

    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.parse()

    ##########################################################################
    def parse(self):
        try:
            if self.config['explorertype'] == 'solaris':
                self.parseSolaris_psrinfo()
            elif self.config['explorertype'] == 'linux':
                self.parseLinux_cpuinfo()
            else:
                self.Fatal("Processors - unknown explorertype %s" %
                           self.config['explorertype'])
        except UserWarning, err:
            self.Warning(err)

    ##########################################################################
    def analyse(self):
        for cpu in self.keys():
            self[cpu].analyse()
            self.inheritIssues(self[cpu])

    ##########################################################################
    def parseLinux_cpuinfo(self):
        f = self.open('proc/cpuinfo')
        for line in f:
            if line.startswith('processor'):
                cpunum = line.split()[-1]
                cpu = Processor(self.config, cpunum)
                self[cpunum] = cpu
            if line.startswith('model name'):
                cpu['proctype'] = line[line.find(':') + 1:].strip()
            if line.startswith('cpu MHz'):
                # Convert speed to a round number: 1500 rather than 1499.998
                # MHz
                cpu['speed'] = "%s" % int(
                    math.ceil(float(line[line.find(':') + 1:].strip())))
        f.close()

    ##########################################################################
    def parseSolaris_psrinfo(self):
        """
        Analyse psrinfo -v output which looks like:
        Status of processor 0 as of: 11/25/05 14:16:15
          Processor has been on-line since 08/04/05 17:30:21.
          The sparc processor operates at 400 MHz,
                and has a sparc floating point processor.
        """
        f = self.open('sysconfig/psrinfo-v.out')
        for line in f:
            line = line.strip()
            m = re.search(
                'Status of .*processor (?P<cpunum>\d+) as of: .*', line)
            if m:
                cpunum = int(m.group('cpunum'))
            cpu = Processor(self.config, cpunum)
            m = re.search(
                'The (?P<proctype>.*) processor operates at (?P<speed>.*),', line)
            if m:
                cpu['proctype'] = m.group('proctype')
                cpu['speed'] = m.group('speed')
                self[cpunum] = cpu
        f.close()

# EOF
