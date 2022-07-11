#!/usr/bin/env python3
"""
Class to make reading explorers easier
"""
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: explorerbase.py 4380 2013-02-22 02:53:51Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/explorerbase.py $

import glob
import math
import os
import re
import sys

from explorer import issue
from explorer import reporter


##########################################################################
# ExplorerBase ###########################################################
##########################################################################
class ExplorerBase:
    """Base class for all other explorer classes to inherit form to give
    basic functionality
    """

    ##########################################################################
    def __init__(self, config):
        self.config = config
        self.hostname = config["hostname"]
        self.data = {}
        self.issues = []
        self.parts = []

    ##########################################################################
    def analyse(self):
        """TODO"""
        if self.__class__.__name__ != "Explorer":
            self.fatal(f"Class {self.__class__.__name__} needs an analyse() method")

    ##########################################################################
    def glob(self, globexpr):
        """TODO"""
        globdir = os.path.join(
            self.config["datadir"], self.config["hostpath"], globexpr
        )
        files = glob.glob(globdir)
        return files

    ##########################################################################
    def pprint(self):
        """TODO"""
        import pprint

        return pprint.pformat(self.data)

    ##########################################################################
    def describer(self, obj, data):
        """Calculate the description of a filesystem object
        based on what it contains"""
        from explorer import storage

        tmp = []
        for thing in data[obj]["contains"]:
            if "partof" in data[thing]:
                tmp.append((len(data[thing]["partof"]), thing))
        tmp.sort()
        desc = ""
        oldv = -1
        for v, o in tmp:
            if oldv != v:
                if "_type" in data[o] and data[o]["_type"] == "missing":
                    continue
                if "description" not in data[o]:
                    self.warning(f"{o} {data[o]} is undescribed")
                    continue
                plural, olist = storage.Storage.pluralDescription(v, tmp)
                # Don't add the names of the disc slices as they should be implicit
                # In some circumstances the list can have mixed types (eg. emcpower path)
                # So strip out the slices as well
                ostr = " ("
                if data[o]["_type"] != "slice":
                    for thing in olist:
                        if data[thing]["_type"] != "slice":
                            ostr += "%s," % thing
                    ostr = ostr[:-1]
                    ostr += ") "
                else:
                    ostr = ""
                desc += "%s%s%s of " % (data[o]["description"], plural, ostr)
                oldv = v
        if desc.endswith(" of "):
            desc = desc[:-4]
        return desc

    ##########################################################################
    def sanitiseDevice(self, dev):
        """Normalise the device names by removing as much path information
        as possible. e.g. /dev/dsk/c0t0d0s0 -> c0t0d0s0
        """
        matchobj = re.match(r"/dev/md/(?P<diskset>\S+)/dsk/(?P<metadev>d\d+)", dev)
        if matchobj:
            dev = "%s/%s" % (matchobj.group("diskset"), matchobj.group("metadev"))
        dev = dev.replace("/dev/did/dsk/", "did/")  # Cluster
        dev = dev.replace("/dev/dsk/", "")
        dev = dev.replace("/dev/vx/dsk/", "")  # VXVM
        dev = dev.replace("/dev/md/dsk/", "")  # Diskssuite
        dev = dev.replace("/dev/zvol/dsk/", "")  # ZFS volume
        dev = dev.replace("/dev/mpath/", "mpath_")  # Linux multipath
        if "/dev/mapper" in dev:
            matchobj = re.search("/dev/mapper/(?P<vg>.*?)-(?P<lv>.*)", dev)
            if matchobj:
                dev = "LV:%s" % matchobj.group("lv")
            else:
                dev = "LV:%s" % dev.replace("/dev/mapper/", "")
        if dev.startswith("/dev/"):
            dev = dev.split("/")[-1]
        dev = dev.replace("cciss/", "")
        return dev

    ##########################################################################
    def __getitem__(self, key):
        """TODO"""
        try:
            return self.data[key]
        except KeyError:
            # self.warning("key=%s Items=%s" % (key, self.data.items()))
            raise

    ##########################################################################
    def keys(self):
        """TODO"""
        return self.data.keys()

    ##########################################################################
    def values(self):
        """TODO"""
        return self.data.values()

    ##########################################################################
    def __delitem__(self, key):
        """TODO"""
        del self.data[key]

    ##########################################################################
    def items(self):
        """TODO"""
        return self.data.items()

    ##########################################################################
    def __contains__(self, key):
        """TODO"""
        return key in self.data

    ##########################################################################
    def __setitem__(self, key, value):
        """TODO"""
        self.data[key] = value

    ##########################################################################
    def cmdfilename(self, filename):
        """Return the filename stripped of everything including the .out
        which generally returns the command name
        """
        fn = os.path.basename(filename)
        fn = fn.replace(".out", "")
        return fn

    ##########################################################################
    def name(self):
        """TODO"""
        if hasattr(self, "objname"):
            return self.objname
        else:
            return self.hostname

    ##########################################################################
    def addCpu(self, *args, **kwargs):
        """TODO"""
        if args:
            kwargs["desc"] = args[0]
        kwargs["component"] = "cpu"
        self.addPart(**kwargs)

    ##########################################################################
    def addMem(self, *args, **kwargs):
        """TODO"""
        if args:
            kwargs["desc"] = args[0]
        kwargs["component"] = "memory"
        self.addPart(**kwargs)

    ##########################################################################
    def addPart(self, **kwargs):
        """TODO"""
        if "fullpart" in kwargs:
            kwargs = kwargs["fullpart"]
        self.parts.append(kwargs)

    ##########################################################################
    def lineSkipper(self, line, start=[], middle=[], end=[]):
        """Convenience function to assist with file parseing
        If any of the strings in start occur at the start of the line then return True
        Similar for middle and end
        """
        if not line:
            return True
        for sstring in start:
            if line.startswith(sstring):
                return True
        for estring in end:
            if line.endswith(estring):
                return True
        for mstring in middle:
            if mstring in line:
                return True
        return False

    ##########################################################################
    def inheritIssues(self, obj):
        """Inherit all the issues from those in obj
        This is uses so a collector object (e.g. Disks) will get the issues
        from the things that it collects (e.g. Disk)
        """
        for iss in obj.issues:
            self.addIssue(iss)

    ##########################################################################
    def addIssue(self, *args, **kwargs):
        """TODO"""
        if args and args[0].__class__.__name__ == "Issue":
            self.issues.append(args[0])
            return
        kwargs["typ"] = "issue"
        if "category" not in kwargs:
            category = self.__class__.__name__
        else:
            category = kwargs["category"]

        i = issue.Issue(category, *args, **kwargs)
        self.issues.append(i)

    ##########################################################################
    def add_concern(self, *args, **kwargs):
        """TODO"""
        kwargs["typ"] = "concern"
        if "category" not in kwargs:
            category = self.__class__.__name__
        else:
            category = kwargs["category"]
        i = issue.Issue(category, *args, **kwargs)
        self.issues.append(i)

    ##########################################################################
    def parse_linux_fdisk(self, func):
        """This lives here because it is called in multiple places"""
        fdisklist = self.glob("sos_commands/filesys/fdisk*")
        for fdiskfile in fdisklist:
            infh = self.open(fdiskfile)
            lines = infh.readlines()
            func(lines)
            infh.close()

    ##########################################################################
    def exists(self, filename):
        """TODO"""
        fullfilepath = os.path.join(
            self.config["datadir"], self.config["hostpath"], filename
        )
        return os.path.exists(fullfilepath) and os.path.getsize(fullfilepath) != 0

    ##########################################################################
    def __repr__(self):
        """TODO"""
        if hasattr(self, "name"):
            return "<%s %s %s>" % (
                self.__class__.__name__,
                self.name(),
                repr(self.data),
            )
        return "<%s %s>" % (self.__class__.__name__, self.data)

    ##########################################################################
    def open(self, filename, mode="r"):
        """TODO"""
        prefix = os.path.join(self.config["datadir"], self.config["hostpath"])
        if filename.startswith(prefix):
            fullfilepath = filename
        else:
            fullfilepath = os.path.join(prefix, filename)
        if not os.path.exists(fullfilepath):
            self.warning(f"Failed to open: {fullfilepath}")
            raise UserWarning(f"File {filename} doesn't exist ({fullfilepath})")
        infh = open(fullfilepath, mode, encoding="utf-8")
        return infh

    ##########################################################################
    def verbose(self, msg):
        """TODO"""
        msg = "%s:%s: %s\n" % (self.hostname, self.__class__.__name__, msg)
        reporter.verbose(msg)

    ##########################################################################
    def warning(self, msg):
        """TODO"""
        reporter.warning(msg)

    ##########################################################################
    def debug(self, msg):
        """TODO"""
        sys.stderr.write(
            f"Debug {self.hostname}:{self.__class__.__name__}: {msg}\n"
        )

    ##########################################################################
    def fatal(self, msg):
        """TODO"""
        reporter.fatal(msg)

    ##########################################################################
    def prettyPrint(self, d=None, indent=0, fd=sys.stdout, keylist=[]):
        """TODO"""
        if d is None and indent == 0:
            d = self.data
        keys = list(d.keys())
        keys.sort()
        istr = " " * (indent * 2)
        for k in keys:
            if indent and keylist and k not in keylist:
                continue
            v = d[k]
            if not v:
                fd.write("%s%-15s\t%s\n" % (istr, k, str(v)))
            elif isinstance(v, dict):
                fd.write("%s%-15s\n" % (istr, k))
                self.prettyPrint(v, indent + 1, fd=fd, keylist=keylist)
            elif isinstance(v, list):
                try:
                    fd.write("%s%-15s\t%s\n" % (istr, k, ", ".join(v)))
                except TypeError:
                    fd.write("%s%-15s\t%s\n" % (istr, k, str(v)))
            elif v is None:
                fd.write("%s%-15s\tNone\n" % (istr, k))
            elif hasattr(v, "prettyPrint"):
                fd.write("%s%-15s\n" % (istr, k))
                self.prettyPrint(v.data, indent + 1, fd=fd, keylist=keylist)
            else:
                fd.write("%s%-15s\t%s\n" % (istr, k, str(v)))

    ##########################################################################
    def sizeStr(self, kbytes):
        """TODO"""
        try:
            if not isinstance(kbytes, int):
                kbytes = int(kbytes)
            for scale, unit in ((1, "Mb"), (2, "Gb"), (3, "Tb"), (4, "Pb")):
                if kbytes < math.pow(1024, scale + 1):
                    return "%0.1f %s" % (kbytes / math.pow(1024, scale), unit)
            return "%d Kb" % kbytes
        except ValueError:
            return kbytes

    ##########################################################################
    def strip_quotes(self, strn):
        """Strip outside quotes no matter which type"""
        for _ in range(2):  # Occassionally lots of nested quotes
            if strn.startswith('"') and strn.endswith('"'):
                strn = strn[1:-1]
            if strn.startswith("'") and strn.endswith("'"):
                strn = strn[1:-1]
        return strn

    ##########################################################################
    def dequoteKV(self, line):
        """Give a line "'a' : 'b'" return a,b
        This occurs quite often in hardware.py
        """
        try:
            bits = line.strip().split(":")
            a = self.strip_quotes(bits[0].strip())
            b = self.strip_quotes(bits[1].strip())
        except IndexError:
            self.fatal(f"dequoteKV issue: line={line}")
        return a, b

    ##########################################################################
    def parse_linux_hardwarepy(self, proc):
        """TODO"""
        if self.exists("hardware.py"):
            infh = self.open("hardware.py")
        elif self.exists("etc/sysconfig/hwconf"):
            infh = self.open("etc/sysconfig/hwconf")
        else:
            return
        buff = {}
        class_ = None
        for line in infh:
            line = line.strip()
            if "hardware.py" in line or "Reading DMI info" in line:
                continue
            if not line or line == "-":
                if buff:
                    proc(buff, class_)
                    buff = {}
                    class_ = None
                continue
            key, val = self.dequoteKV(line)
            if key == "class":
                class_ = val
            buff[key] = val
        infh.close()
        if buff:
            proc(buff, class_)

    ##########################################################################
    def parseIostat(self, filename="disks/iostat_-E.out"):
        """Parse iostat -E output; this would normally belong under disks, but it also
        handles tapes as well
        """
        if not self.exists(filename):
            self.warning(f"Couldn't open {filename}")
            return {}
        infh = self.open(filename)
        datadev = {}
        dev = ""
        for line in infh:
            line = line.strip()
            if not line:
                continue
            matchobj = re.match(
                r"(?P<device>\S+)\s*Soft Errors: (?P<softerrors>\d+) Hard Errors: (?P<harderrors>\d+) Transport Errors: (?P<transerrors>\d+)",
                line,
            )
            if matchobj:
                dev = matchobj.group("device")
                datadev[dev] = {}
                datadev[dev].update(matchobj.groupdict())
                continue
            matchobj = re.match(
                r"Vendor: (?P<vendor>.*?)\s+Product: (?P<product>.*?)\s+Revision: (?P<revision>.*) Serial No:(?P<serial>.*)",
                line,
            )
            if matchobj:
                datadev[dev].update(matchobj.groupdict())
                continue
            # system info version
            matchobj = re.match(
                r"^(?P<vendor>.*?)\s+Product: (?P<product>.*?)\s+Revision: (?P<revision>.*) Serial No:(?P<serial>.*)",
                line,
            )
            if matchobj:
                datadev[dev].update(matchobj.groupdict())
                continue
            matchobj = re.match(
                r"Model: (?P<model>.*) Revision: (?P<revision>.*) Serial No: (?P<serial>.*)",
                line,
            )
            if matchobj:
                datadev[dev].update(matchobj.groupdict())
                continue
            matchobj = re.match(r"Size: (?P<size>\S+) <(?P<bytes>-?\d+) bytes>", line)
            if matchobj:
                datadev[dev].update(matchobj.groupdict())
                continue
            # system info version
            matchobj = re.match(r"^(?P<size>\S+) <(?P<bytes>-?\d+) bytes>", line)
            if matchobj:
                datadev[dev].update(matchobj.groupdict())
                continue
            matchobj = re.match(
                r"Media Error: (?P<mediaerror>\d+) Device Not Ready: (?P<devnotready>\d+)\s+No Device: (?P<nodev>\d+) Recoverable: (?P<recoverable>\d+)",
                line,
            )
            if matchobj:
                datadev[dev].update(matchobj.groupdict())
                continue
            matchobj = re.match(
                r"Illegal Request: (?P<illreq>\d+) Predictive Failure Analysis: (?P<predfail>\d+)",
                line,
            )
            if matchobj:
                datadev[dev].update(matchobj.groupdict())
                continue
            matchobj = re.match(r"Illegal Request: (?P<illreq>\d+)", line)
            if matchobj:
                datadev[dev].update(matchobj.groupdict())
                continue
            matchobj = re.match(
                r"RPM: (?P<rpm>\d+) Heads: (?P<heads>\d+) Size: (?P<size>\S+) <(?P<bytes>-?\d+) bytes>",
                line,
            )
            if matchobj:
                datadev[dev].update(matchobj.groupdict())
                continue
            # system info version
            matchobj = re.match(r"^(?P<disk>c\d+t\d+d\d+)$", line)
            if matchobj:
                dev = matchobj.group("disk")
                datadev[dev] = {}
                datadev[dev].update(matchobj.groupdict())
                continue
            self.Debug(f"Unhandled iostat line >{line}<")
        infh.close()
        return datadev


# EOF
