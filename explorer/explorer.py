#!/usr/local/bin/python
#
# Class to make reading explorers easier
# This should encapulate all of the other explorer details
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: explorer.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/explorer.py $

import getopt
import glob
import os
import os.path
import re
import sys
import time
import pickle

import cluster
import disks
import emc
import filesys
import fma
import hostdet
import misc
import nic
import processor
import prtconf
import prtdiag
import reporter
import se3k
import svcs
import swap
import tapes
import volmanager
import vxvm
import zfs
import zones

verbFlag = False
debugFlag = False

explorereg = [
    ("explorer.(?P<hostid>[a-f0-9]{8}).(?P<hostname>.*)-(?P<timedate>(?P<date>\d{4}.\d\d.\d\d).(?P<time>\d\d.\d\d))",
     "solaris"),
    (
        "sosreport-(?P<hostname>.*)-(?P<timedate>(?P<date>\d{4}.\d{2}.\d{2}).(?P<time>\d{2}.\d{2}))", "linux"),
    (
        "sosreport-(?P<hostname>.*?)(?P<timedate>(?P<date>\d{8})(?P<time>\d{4}))\d{2}-\w+", "linux"),
    #    ("sosreport\.(?P<hostname>.*?)\.(?P<timedate>(?P<date>\d{8})(?P<time>\d{4}))\D", "linux"),
    #    ("sosreport\.(?P<hostname>.*?)\.(?P<timedate>(?P<date>\d{8})(?P<time>\d{4}))\d{2}\D", "linux"),

    #    ("sysreport-(?P<hostname>.*)-(?P<timedate>(?P<date>\d{4}.\d{2}.\d{2}).(?P<time>\d{2}.\d{2}))", "linux"),
    #    ("sysreport\.(?P<hostname>.*?).(?P<timedate>(?P<date>\d{8})(?P<time>\d{4}))\D", "linux"),
    #    ("sysreport-root.(?P<hostname>.*)", "linux"),
    #    ("(?P<hostname>.*?)\.(?P<timedate>(?P<date>\d{8})(?P<time>\d{4}))\d{2}-\w+", "linux"),
]

##########################################################################
# Explorer ###############################################################
##########################################################################


class Explorer(object):

    def __init__(self, hostpath):
        self.rootpath = options['datadir']
        self.hostname = self.getHostname(hostpath)
        self.hostpath = hostpath
        self.picklepath = os.path.join(self.hostpath, ".pickle")
        self.config = {
            'hostname': self.hostname,
            'hostpath': hostpath,
            'picklepath': self.picklepath,
            'explorertype': self.explorertype,
            'datadir': options['datadir']
        }
        self.data = {}
        self.issues = []
        self.parts = []
        self.parse()

    ##########################################################################
    def __repr__(self):
        return "<Explorer %s: %s>" % (self.hostname, self.data)

    ##########################################################################
    def keys(self):
        return self.data.keys()

    ##########################################################################
    def getHostname(self, hostpath):
        found = False
        for reg, ostype in explorereg:
            m = re.match(reg, os.path.basename(hostpath))
            if m:
                found = True
                self.explorertype = ostype
                self.reg = reg
                host = m.group('hostname')
                if '.' in host:
                    host = host[:host.find('.')]
                return host
        self.Fatal("Couldn't match %s against explorers" % hostpath)

    ##########################################################################
    def __getitem__(self, key):
        return self.data[key]

    ##########################################################################
    def parse(self):
        if self.loadPickle():
            return
        self.data['explorer'] = misc.miscDetails(self.config)
        self.data['host'] = hostdet.Host(self.config)
        self.data['prtdiag'] = prtdiag.Prtdiag(self.config)
        self.data['zones'] = zones.Zones(self.config)
        self.data['processor'] = processor.Processors(self.config)
        self.data['filesys'] = filesys.Filesystems(self.config)
        self.data['disks'] = disks.Disks(self.config)
        self.data['zfs'] = zfs.Zfs(self.config)
        self.data['swap'] = swap.Swap(self.config)
        self.data['volmanager'] = volmanager.Volmanager(self.config)
        self.data['vxvm'] = vxvm.Vxvm(self.config)
        self.data['nics'] = nic.Nics(self.config)
        self.data['se3k'] = se3k.Se3k(self.config)
        self.data['tapes'] = tapes.Tapes(self.config)
        self.data['prtconf'] = prtconf.Prtconf(self.config)
        self.data['cluster'] = cluster.Cluster(self.config)
        self.data['fma'] = fma.Fma(self.config)
        self.data['svcs'] = svcs.Svcs(self.config)
        self.data['emc'] = emc.EmcDisks(self.config)
        self.calcIssues()
        self.calcParts()
        self.savePickle()

    ##########################################################################
    def savePickle(self):
        try:
            f = open(self.picklepath, 'wb')
            blob = (self.data, self.issues, self.parts)
            pickle.dump(blob, f)
            f.close()
        except IOError:
            pass

    ##########################################################################
    def loadPickle(self):
        if not os.path.exists(self.picklepath):
            return False
        try:
            f = open(self.picklepath)
            blob = pickle.load(f)
            (self.data, self.issues, self.parts) = blob
            f.close()
        except Exception, err:
            self.Warning("loadPickle() Failed %s" % (str(err)))
            return False
        return True

    ##########################################################################
    def Warning(self, msg):
        reporter.Warning(msg)

    ##########################################################################
    def Fatal(self, msg):
        reporter.Fatal(msg)

    ##########################################################################
    def calcParts(self):
        for type_ in self.data.keys():
            if self.data[type_].parts:
                self.parts.extend(self.data[type_].parts)

    ##########################################################################
    def calcIssues(self):
        for type_ in self.data.keys():
            if self.data[type_].issues:
                self.issues.extend(self.data[type_].issues)

    ##########################################################################
    def getCollectionDate(self):
        m = re.match(self.reg, os.path.basename(self.hostpath))
        if m:
            self.collectiondate = m.group('date')
            self.collectiontime = m.group('time')
        else:
            self.Warning("Couldn't get date from %s" % self.hostpath)
            return None, None
        return self.collectiondate, self.collectiontime

##########################################################################


def readConfig(cfg=None):
    """ Read the config file
    The name of the file can be specified in this order:
     * On the command line with the -c option
     * Using the EXPLORERTOOLS environment variable
     * /app/explorer/etc/explorertools.cfg
    """

    import ConfigParser

    global options
    options = {}
    defaults = {
        # agedcare: Send old files to an old directory rather than delete
        'agedcare': True,
        # bindir: Where the explorer tools executables are kept
        'bindir': '/app/explorer/bin',
        # changelog: Write a log of the changes generated for this host
        'changelog': False,
        # changelogdir: Where to put the changelogs
        'changelogdir': '/app/explorer/changelog',
        # datadir: Where to look for the data files
        'datadir': '/app/explorer/data',
        'hostinfo': True,  # hostinfo: Generate hostinfo updates
        # Where hostinfo commands are installed
        'hostinfodir': '/app/hostinfo/bin',
        # oldage: how many days old an explorer is before it is ignored
        'oldage': 365,
        # outputdir: Where to create the HTML outputs
        'outputdir': '/app/explorer/output',
        # retain_compressed: How many compressed files to keep
        'retain_compressed': 1,
        'retain_dir': 1,  # retain_dir: How many extracted directories to keep
    }
    if not cfg:
        if 'EXPLORERTOOLS' in os.environ:
            cfg = os.environ['EXPLORERTOOLS']
        else:
            cfg = '/usr/local/etc/explorertools.cfg'
    if not os.path.exists(cfg):
        Fatal("Couldn't read config file: %s" % cfg)
    config = ConfigParser.ConfigParser(defaults)
    config.read(cfg)
    options['configfile'] = os.path.realpath(cfg)

    options['outputdir'] = config.get('Paths', 'outputdir')
    options['datadir'] = config.get('Paths', 'datadir')
    options['changelogdir'] = config.get('Paths', 'changelogdir')
    options['bindir'] = config.get('Paths', 'bindir')
    options['hostinfodir'] = config.get('Paths', 'hostinfodir')
    options['agedcare'] = config.getboolean('Options', 'agedcare')
    options['changelog'] = config.getboolean('Options', 'changelog')
    options['hostinfo'] = config.getboolean('Options', 'hostinfo')
    options['oldage'] = config.getint('Options', 'oldage')
    options['retain_compressed'] = config.getint(
        'Retention', 'retain_compressed')
    options['retain_dir'] = config.getint('Retention', 'retain_dir')

    return options

############################################################################


def Fatal(msg):
    reporter.Fatal(msg)

############################################################################


def allExplorers(reg=''):
    """ Return a list of all explorer hosts that match the reg; by default all hosts
        Only return the latest explorer per host
    """
    hostlist = {}
    globstr = os.path.join(options['datadir'], "*%s*" % reg)
    files = [f.replace('%s/' % options['datadir'], '')
             for f in glob.glob(globstr) if os.path.splitext(f)[1] not in ('.gz', '.bz2', '.md5')]
    for fn in files:
        fullfile = os.path.join(options['datadir'], fn)
        for reg, ostype in explorereg:
            m = re.match(reg, fn)
            if m:
                break
        if not m:
            sys.stderr.write(
                "allExplorers: Couldn't match %s against explorers\n" % fn)
            continue
        host = m.group('hostname')
        if '.' in host:
            host = host[:host.find('.')]
        try:
            d = m.group('date')
        # sosreport on linux doesn't have the date encoded :(
        except IndexError:
            d = time.strftime(
                "%Y.%m.%d.%H.%M.%s", time.localtime(os.path.getmtime(fullfile)))
        if host not in hostlist:
            hostlist[host] = (d, fn, fullfile)
        else:
            if hostlist[host][0] < d:     # Update if new file is fresher
                hostlist[host] = (d, fn, fullfile)
    return hostlist

##########################################################################


def main(arg):
    allexp = allExplorers(arg)
    for host in allexp:
        e = Explorer(allexp[host][-1])
        print "Hostname=%s" % e.hostname
        print "Explorertype=%s" % e.explorertype
        print "Data=%s" % e.data

##########################################################################
if __name__ == "__main__":
    cfgfile = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "vc:", ["cfg="])
    except getopt.GetoptError, err:
        sys.stderr.write("Error: %s\n" % str(err))
        usage()
        sys.exit(1)

    for o, a in opts:
        if o == "-v":
            verbFlag = True
        if o in ('-c', '--cfg'):
            cfgfile = a

    global options
    options = readConfig(cfgfile)

    if args:
        arg = args[0]
    else:
        arg = ''

    main(arg)

# EOF
