#!/usr/local/bin/python
# 
# Script to understand cluster details
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: cluster.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/cluster.py $

import os, sys, getopt, re
import explorerbase

################################################################################
# Cluster ######################################################################
################################################################################
class Cluster(explorerbase.ExplorerBase):
    """Understand explorer output with respect to clusters, both Sun
       and Veritas Clusters.
       Different Sun version have wildly different configurations
    """
    ############################################################################
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.parse()

    ############################################################################
    def parse(self):
        if self.parse_suncluster():
            self['clustertype']='sun'
            self['incluster']=True
        elif self.parse_vcscluster():
            self['clustertype']='vcs'
            self['incluster']=True
        else:
            self['incluster']=False
        
    ############################################################################
    def parse_vcscluster(self):
        found=False
        filename='sysconfig/modinfo.out'
        if not self.exists(filename):
            return False
        f=self.open(filename)
        for line in f:
            if 'GAB device' in line:
                found=True
        return found

    ############################################################################
    def parse_suncluster(self):
        incluster=False
        self['nodes']=[]
        self['clusterfs']=set()
        if self.exists('cluster/etc/opt/SUNWcluster/conf/ccd.database'):
            self.parseCcd()
            incluster=True
        if self.exists('cluster/etc/cluster/ccr/infrastructure'):
            self.parseInfrastructure()
            incluster=True
            self['clustertype']='sun'
        if self.exists('cluster/config/scrgadm-pvv.out'):
            self.parseClusterFilesystems()
        return incluster

    ############################################################################
    def analyse(self):
        pass

    ############################################################################
    def parseClusterFilesystems(self):
        """ Clusters mount filesystems from the cluster management as shared
        resources, not from vfstab
        """
        f=self.open('cluster/config/scrgadm-pvv.out')
        for line in f:
            if 'FilesystemMountPoints' in line and 'property value' in line:
                fslist=set(line.strip().split(':')[-1].split())
                fslist.discard('<NULL>')
                self['clusterfs'].update(fslist)
        f.close()

    ############################################################################
    def parseInfrastructure(self):
        f=self.open('cluster/etc/cluster/ccr/infrastructure')
        for line in f:
            if line.startswith('cluster.name'):
                self['name']=line.split()[-1]
                
            m=re.match('cluster.nodes.\d+.name\s+(?P<name>\S+)', line.strip())
            if m:
                if m.group('name')!=self.hostname:
                    self['nodes'].append(m.group('name'))

            m=re.match('cluster.quorum_devices.\d+.properties.gdevname\s+(?P<gdevname>\S+)', line.strip())
            if m:
                self['quorum']=m.group('gdevname')
        f.close()

    ############################################################################
    def parseCcd(self):
        f=self.open('cluster/etc/opt/SUNWcluster/conf/ccd.database')
        for line in f:
            if line.startswith('LOGHOST:'):
                bits=line.split(':')
                lname=bits[1]
                self['nodes']=[node for node in bits[2].split(',') if node!=self.hostname]
        f.close()

#EOF
