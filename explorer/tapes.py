#!/usr/local/bin/python
# 
# Script to understand tape details
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: tapes.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/tapes.py $

import os, sys, getopt, re
import explorerbase

################################################################################
# Tapedrive ####################################################################
################################################################################
class Tapedrive(explorerbase.ExplorerBase):
    ############################################################################
    def __init__(self, config, tapename):
        explorerbase.ExplorerBase.__init__(self, config)
        self.objname=tapename

    ############################################################################
    def analyse(self):
        pass

    ############################################################################
    def parseModePage(self):
        f=self.open('tapes/%s/ModePage_00.out' % self.name())
        for line in f:
            if line.startswith('device name:'):
                self['device']=line.split(':')[-1].strip()
            if line.startswith('device vendor id:'):
                self['hardware']=line.split(':')[-1].strip()
            if line.startswith('Tape motion hours'):
                self['motionhours']=int(line.split()[-1].strip())
            if line.startswith('Power-on hours'):
                self['powerhours']=int(line.split()[-1].strip())
            if line.startswith('Tape motion duty cycle'):
                self['dutycycle']=float(line.split()[-1].strip())
        f.close()

################################################################################
# Tapes ########################################################################
################################################################################
class Tapes(explorerbase.ExplorerBase):
    """Understand explorer output with respect to tape drives
    """
    ############################################################################
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        if not self.exists('tapes'):
            return
        devlist=self.parseIostat('tapes/iostat-En.out')
        for dev in devlist:
            if dev.startswith('rmt') or dev.startswith('st'):
                newname=dev.replace('/','_')
                self[newname]=Tapedrive(config, newname)
                for k,v in devlist[dev].items():
                    self[newname][k]=v
                self[newname]['hardware']="%s %s" % (self[newname]['vendor'], self[newname]['product'])

        for drv in self.glob('tapes/rmt*'):
            tape=os.path.basename(drv)
            if tape not in self:
                self[tape]=Tapedrive(config, tape)
            self[tape].parseModePage()

    ############################################################################
    def analyse(self):
        for tape in self.tapeList():
            self[tape].analyse()
            self.inheritIssues(self[tape])

    ############################################################################
    def tapeList(self):
        return sorted(self.data.keys())

#EOF
