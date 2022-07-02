#!/usr/bin/env python3
"""
Class to make reading explorers easier
This should encapulate all of the other explorer details
"""

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


OPTIONS = {
        "verbFlag":  False,
        "debugFlag":  False
        }

explorereg = [
    (
        r"explorer.(?P<hostid>[a-f0-9]{8}).(?P<hostname>.*)-(?P<timedate>(?P<date>\d{4}.\d\d.\d\d).(?P<time>\d\d.\d\d))",
        "solaris",
    ),
    (
        r"sosreport-(?P<hostname>.*)-(?P<timedate>(?P<date>\d{4}.\d{2}.\d{2}).(?P<time>\d{2}.\d{2}))",
        "linux",
    ),
    (
        r"sosreport-(?P<hostname>.*?)(?P<timedate>(?P<date>\d{8})(?P<time>\d{4}))\d{2}-\w+",
        "linux",
    ),
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
class Explorer:
    """ TODO """
    def __init__(self, hostpath):
        self.rootpath = OPTIONS["datadir"]
        self.hostname = self.get_hostname(hostpath)
        self.hostpath = hostpath
        self.picklepath = os.path.join(self.hostpath, ".pickle")
        self.config = {
            "hostname": self.hostname,
            "hostpath": hostpath,
            "picklepath": self.picklepath,
            "explorertype": self.explorertype,
            "datadir": OPTIONS["datadir"],
        }
        self.data = {}
        self.issues = []
        self.parts = []
        self.parse()

    ##########################################################################
    def __repr__(self):
        """ TODO """
        return f"<Explorer {self.hostname}: {self.data}>"

    ##########################################################################
    def keys(self):
        """ TODO """
        return self.data.keys()

    ##########################################################################
    def get_hostname(self, hostpath):
        """ TODO """
        for reg, ostype in explorereg:
            matchobj = re.match(reg, os.path.basename(hostpath))
            if matchobj:
                self.explorertype = ostype
                self.reg = reg
                host = matchobj.group("hostname")
                if "." in host:
                    host = host[: host.find(".")]
                return host
        self.Fatal(f"Couldn't match {hostpath} against explorers")
        return ""

    ##########################################################################
    def __getitem__(self, key):
        return self.data[key]

    ##########################################################################
    def parse(self):
        """ TODO """
        if self.load_pickle():
            return
        self.data["explorer"] = misc.miscDetails(self.config)
        self.data["host"] = hostdet.Host(self.config)
        self.data["prtdiag"] = prtdiag.Prtdiag(self.config)
        self.data["zones"] = zones.Zones(self.config)
        self.data["processor"] = processor.Processors(self.config)
        self.data["filesys"] = filesys.Filesystems(self.config)
        self.data["disks"] = disks.Disks(self.config)
        self.data["zfs"] = zfs.Zfs(self.config)
        self.data["swap"] = swap.Swap(self.config)
        self.data["volmanager"] = volmanager.Volmanager(self.config)
        self.data["vxvm"] = vxvm.Vxvm(self.config)
        self.data["nics"] = nic.Nics(self.config)
        self.data["se3k"] = se3k.Se3k(self.config)
        self.data["tapes"] = tapes.Tapes(self.config)
        self.data["prtconf"] = prtconf.Prtconf(self.config)
        self.data["cluster"] = cluster.Cluster(self.config)
        self.data["fma"] = fma.Fma(self.config)
        self.data["svcs"] = svcs.Svcs(self.config)
        self.data["emc"] = emc.EmcDisks(self.config)
        self.calc_issues()
        self.calc_parts()
        self.save_pickle()

    ##########################################################################
    def save_pickle(self):
        """ TODO """
        try:
            f = open(self.picklepath, "wb")
            blob = (self.data, self.issues, self.parts)
            pickle.dump(blob, f)
            f.close()
        except IOError:
            pass

    ##########################################################################
    def load_pickle(self):
        """ TODO """
        if not os.path.exists(self.picklepath):
            return False
        try:
            f = open(self.picklepath)
            blob = pickle.load(f)
            (self.data, self.issues, self.parts) = blob
            f.close()
        except Exception as err:
            self.Warning("load_pickle() Failed %s" % (str(err)))
            return False
        return True

    ##########################################################################
    def Warning(self, msg):
        """ TODO """
        reporter.Warning(msg)

    ##########################################################################
    def Fatal(self, msg):
        """ TODO """
        reporter.Fatal(msg)

    ##########################################################################
    def calc_parts(self):
        """ TODO """
        for type_ in self.data.keys():
            if self.data[type_].parts:
                self.parts.extend(self.data[type_].parts)

    ##########################################################################
    def calc_issues(self):
        """ TODO """
        for type_ in self.data.keys():
            if self.data[type_].issues:
                self.issues.extend(self.data[type_].issues)

    ##########################################################################
    def getCollectionDate(self):
        """ TODO """
        matchobj = re.match(self.reg, os.path.basename(self.hostpath))
        if matchobj:
            self.collectiondate = matchobj.group("date")
            self.collectiontime = matchobj.group("time")
        else:
            self.Warning("Couldn't get date from %s" % self.hostpath)
            return None, None
        return self.collectiondate, self.collectiontime


##########################################################################
def read_config(cfg=None):
    """Read the config file
    The name of the file can be specified in this order:
     * On the command line with the -c option
     * Using the EXPLORERTOOLS environment variable
     * /app/explorer/etc/explorertools.cfg
    """
    import configparser

    options = {}
    defaults = {
        # agedcare: Send old files to an old directory rather than delete
        "agedcare": True,
        # bindir: Where the explorer tools executables are kept
        "bindir": "/app/explorer/bin",
        # changelog: Write a log of the changes generated for this host
        "changelog": False,
        # changelogdir: Where to put the changelogs
        "changelogdir": "/app/explorer/changelog",
        # datadir: Where to look for the data files
        "datadir": "/app/explorer/data",
        "hostinfo": True,  # hostinfo: Generate hostinfo updates
        # Where hostinfo commands are installed
        "hostinfodir": "/app/hostinfo/bin",
        # oldage: how many days old an explorer is before it is ignored
        "oldage": 365,
        # outputdir: Where to create the HTML outputs
        "outputdir": "/app/explorer/output",
        # retain_compressed: How many compressed files to keep
        "retain_compressed": 1,
        "retain_dir": 1,  # retain_dir: How many extracted directories to keep
    }
    if not cfg:
        if "EXPLORERTOOLS" in os.environ:
            cfg = os.environ["EXPLORERTOOLS"]
        else:
            cfg = "/usr/local/etc/explorertools.cfg"
    if not os.path.exists(cfg):
        Fatal(f"Couldn't read config file: {cfg}")
    config = configparser.ConfigParser(defaults)
    config.read(cfg)
    options["configfile"] = os.path.realpath(cfg)

    options["outputdir"] = config.get("Paths", "outputdir")
    options["datadir"] = config.get("Paths", "datadir")
    options["changelogdir"] = config.get("Paths", "changelogdir")
    options["bindir"] = config.get("Paths", "bindir")
    options["hostinfodir"] = config.get("Paths", "hostinfodir")
    options["agedcare"] = config.getboolean("Options", "agedcare")
    options["changelog"] = config.getboolean("Options", "changelog")
    options["hostinfo"] = config.getboolean("Options", "hostinfo")
    options["oldage"] = config.getint("Options", "oldage")
    options["retain_compressed"] = config.getint("Retention", "retain_compressed")
    options["retain_dir"] = config.getint("Retention", "retain_dir")

    return options


############################################################################
def Fatal(msg):
    """ TODO """
    reporter.Fatal(msg)


############################################################################
def all_explorers(reg=""):
    """Return a list of all explorer hosts that match the reg; by default all hosts
    Only return the latest explorer per host
    """
    hostlist = {}
    globstr = os.path.join(OPTIONS["datadir"], "*%s*" % reg)
    files = [
        f.replace("%s/" % OPTIONS["datadir"], "")
        for f in glob.glob(globstr)
        if os.path.splitext(f)[1] not in (".gz", ".bz2", ".md5")
    ]
    for fname in files:
        fullfile = os.path.join(OPTIONS["datadir"], fname)
        for reg, ostype in explorereg:
            matchobj = re.match(reg, fname)
            if matchobj:
                break
        if not matchobj:
            sys.stderr.write(f"all_explorers: Couldn't match {fname} against explorers\n")
            continue
        host = matchobj.group("hostname")
        if "." in host:
            host = host[: host.find(".")]
        try:
            d = matchobj.group("date")
        # sosreport on linux doesn't have the date encoded :(
        except IndexError:
            d = time.strftime(
                "%Y.%m.%d.%H.%M.%s", time.localtime(os.path.getmtime(fullfile))
            )
        if host not in hostlist:
            hostlist[host] = (d, fname, fullfile)
        else:
            if hostlist[host][0] < d:  # Update if new file is fresher
                hostlist[host] = (d, fname, fullfile)
    return hostlist


##########################################################################
def main():
    """ TODO """
    cfgfile = None
    global OPTIONS
    try:
        opts, args = getopt.getopt(sys.argv[1:], "vc:", ["cfg="])
    except getopt.GetoptError as err:
        sys.stderr.write("Error: %s\n" % str(err))
        sys.exit(1)

    for o, a in opts:
        if o == "-v":
            OPTIONS["verbFlag"] = True
        if o in ("-c", "--cfg"):
            cfgfile = a

    OPTIONS = read_config(cfgfile)

    if args:
        arg = args[0]
    else:
        arg = ""

    allexp = all_explorers(arg)
    for host in allexp:
        e = Explorer(allexp[host][-1])
        print(f"Hostname={e.hostname}")
        print(f"Explorertype={e.explorertype}")
        print(f"Data={e.data}")


##########################################################################
if __name__ == "__main__":
    main()

# EOF
