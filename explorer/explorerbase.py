#!/usr/local/bin/python
#
# Class to make reading explorers easier
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: explorerbase.py 4380 2013-02-22 02:53:51Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/explorerbase.py $

import glob
import math
import os
import re
import sys

import issue
import reporter

verbFlag = False
debugFlag = False

##########################################################################
# ExplorerBase ###########################################################
##########################################################################


class ExplorerBase(object):

    """ Base class for all other explorer classes to inherit form to give
    basic functionality
    """
    ##########################################################################

    def __init__(self, config):
        self.config = config
        self.hostname = config['hostname']
        self.data = {}
        self.issues = []
        self.parts = []

    ##########################################################################
    def analyse(self):
        if self.__class__.__name__ != 'Explorer':
            self.Fatal("Class %s needs an analyse() method" %
                       (self.__class__.__name__))

    ##########################################################################
    def glob(self, globexpr):
        globdir = os.path.join(
            self.config['datadir'], self.config['hostpath'], globexpr)
        files = glob.glob(globdir)
        return files

    ##########################################################################
    def pprint(self):
        import pprint
        return pprint.pformat(self.data)

    ##########################################################################
    def describer(self, filesys, data):
        """ Calculate the description of a filesystem object
        based on what it contains"""
        import storage

        tmp = []
        for obj in data[filesys]['contains']:
            if 'partof' in data[obj]:
                tmp.append((len(data[obj]['partof']), obj))
        tmp.sort()
        desc = ''
        oldv = -1
        for v, o in tmp:
            if oldv != v:
                if '_type' in data[o] and data[o]['_type'] == 'missing':
                    continue
                if 'description' not in data[o]:
                    self.Warning("%s %s is undescribed" % (o, data[o]))
                    continue
                plural, olist = storage.Storage.pluralDescription(v, tmp)
                # Don't add the names of the disc slices as they should be implicit
                # In some circumstances the list can have mixed types (eg. emcpower path)
                # So strip out the slices as well
                ostr = ' ('
                if data[o]['_type'] != 'slice':
                    for obj in olist:
                        if data[obj]['_type'] != 'slice':
                            ostr += "%s," % obj
                    ostr = ostr[:-1]
                    ostr += ") "
                else:
                    ostr = ''
                desc += "%s%s%s of " % (data[o]['description'], plural, ostr)
                oldv = v
        if desc.endswith(' of '):
            desc = desc[:-4]
        return desc

    ##########################################################################
    def sanitiseDevice(self, dev):
        """ Normalise the device names by removing as much path information
        as possible. e.g. /dev/dsk/c0t0d0s0 -> c0t0d0s0
        """
        origdev = dev
        m = re.match('/dev/md/(?P<diskset>\S+)/dsk/(?P<metadev>d\d+)', dev)
        if m:
            dev = "%s/%s" % (m.group('diskset'), m.group('metadev'))
        dev = dev.replace('/dev/did/dsk/', 'did/')  # Cluster
        dev = dev.replace('/dev/dsk/', '')
        dev = dev.replace('/dev/vx/dsk/', '')      # VXVM
        dev = dev.replace('/dev/md/dsk/', '')      # Diskssuite
        dev = dev.replace('/dev/zvol/dsk/', '')    # ZFS volume
        dev = dev.replace('/dev/mpath/', 'mpath_')  # Linux multipath
        if '/dev/mapper' in dev:
            m = re.search('/dev/mapper/(?P<vg>.*?)-(?P<lv>.*)', dev)
            if m:
                dev = "LV:%s" % m.group('lv')
            else:
                dev = "LV:%s" % dev.replace('/dev/mapper/', '')
        if dev.startswith('/dev/'):
            dev = dev.split('/')[-1]
        dev = dev.replace('cciss/', '')
        return dev

    ##########################################################################
    def __getitem__(self, key):
        try:
            return self.data[key]
        except KeyError:
            #self.Warning("key=%s Items=%s" % (key, self.data.items()))
            raise

    ##########################################################################
    def keys(self):
        return self.data.keys()

    ##########################################################################
    def values(self):
        return self.data.values()

    ##########################################################################
    def __delitem__(self, key):
        del self.data[key]

    ##########################################################################
    def items(self):
        return self.data.items()

    ##########################################################################
    def __contains__(self, key):
        return key in self.data

    ##########################################################################
    def __setitem__(self, key, value):
        self.data[key] = value

    ##########################################################################
    def cmdfilename(self, filename):
        """ Return the filename stripped of everything including the .out
        which generally returns the command name
        """
        fn = os.path.basename(filename)
        fn = fn.replace('.out', '')
        return fn

    ##########################################################################
    def name(self):
        if hasattr(self, 'objname'):
            return self.objname
        else:
            return self.hostname

    ##########################################################################
    def addCpu(self, *args, **kwargs):
        if args:
            kwargs['desc'] = args[0]
        kwargs['component'] = 'cpu'
        self.addPart(**kwargs)

    ##########################################################################
    def addMem(self, *args, **kwargs):
        if args:
            kwargs['desc'] = args[0]
        kwargs['component'] = 'memory'
        self.addPart(**kwargs)

    ##########################################################################
    def addPart(self, **kwargs):
        if 'fullpart' in kwargs:
            kwargs = kwargs['fullpart']
        self.parts.append(kwargs)

    ##########################################################################
    def lineSkipper(self, line, start=[], middle=[], end=[]):
        """ Convenience function to assist with file parseing
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
        if args and args[0].__class__.__name__ == "Issue":
            self.issues.append(args[0])
            return
        kwargs['typ'] = 'issue'
        if 'category' not in kwargs:
            category = self.__class__.__name__
        else:
            category = kwargs['category']

        i = issue.Issue(category, *args, **kwargs)
        self.issues.append(i)

    ##########################################################################
    def addConcern(self, *args, **kwargs):
        kwargs['typ'] = 'concern'
        if 'category' not in kwargs:
            category = self.__class__.__name__
        else:
            category = kwargs['category']
        i = issue.Issue(category, *args, **kwargs)
        self.issues.append(i)

    ##########################################################################
    def parseLinux_fdisk(self, func):
        """ This lives here because it is called in multiple places
        """
        fdisklist = self.glob("sos_commands/filesys/fdisk*")
        for fdiskfile in fdisklist:
            f = self.open(fdiskfile)
            lines = f.readlines()
            func(lines)
            f.close()

    ##########################################################################
    def exists(self, filename):
        fullfilepath = os.path.join(
            self.config['datadir'], self.config['hostpath'], filename)
        return os.path.exists(fullfilepath) and os.path.getsize(fullfilepath) != 0

    ##########################################################################
    def __repr__(self):
        if hasattr(self, 'name'):
            return "<%s %s %s>" % (self.__class__.__name__, self.name(), repr(self.data))
        else:
            return "<%s %s>" % (self.__class__.__name__, self.data)

    ##########################################################################
    def open(self, filename, mode='r'):
        fullfilepath = os.path.join(
            self.config['datadir'], self.config['hostpath'], filename)
        if not os.path.exists(fullfilepath):
            Warning("Failed to open: %s" % fullfilepath)
            raise UserWarning, "File %s doesn't exist (%s)" % (
                filename, fullfilepath)
        f = open(fullfilepath, mode)
        return f

    ##########################################################################
    def Verbose(self, msg):
        msg = "%s:%s: %s\n" % (self.hostname, self.__class__.__name__, msg)
        reporter.Verbose(msg)

    ##########################################################################
    def Warning(self, msg):
        reporter.Warning(msg)

    ##########################################################################
    def Debug(self, msg):
        if debugFlag:
            sys.stderr.write("Debug %s:%s: %s\n" %
                             (self.hostname, self.__class__.__name__, msg))

    ##########################################################################
    def Fatal(self, msg):
        reporter.Fatal(msg)

    ##########################################################################
    def prettyPrint(self, d=None, indent=0, fd=sys.stdout, keylist=[]):
        if d == None and indent == 0:
            d = self.data
        keys = d.keys()
        keys.sort()
        istr = " " * (indent * 2)
        for k in keys:
            if indent and keylist and k not in keylist:
                continue
            v = d[k]
            if not v:
                fd.write("%s%-15s\t%s\n" % (istr, k, `v`))
            elif type(v) == type({}):
                fd.write("%s%-15s\n" % (istr, k))
                self.prettyPrint(v, indent + 1, fd=fd, keylist=keylist)
            elif type(v) == type([]):
                try:
                    fd.write("%s%-15s\t%s\n" % (istr, k, ", ".join(v)))
                except TypeError:
                    fd.write("%s%-15s\t%s\n" % (istr, k, str(v)))
            elif type(v) == type(None):
                fd.write("%s%-15s\tNone\n" % (istr, k))
            elif hasattr(v, 'prettyPrint'):
                fd.write("%s%-15s\n" % (istr, k))
                self.prettyPrint(v.data, indent + 1, fd=fd, keylist=keylist)
            else:
                fd.write("%s%-15s\t%s\n" % (istr, k, `v`))

    ##########################################################################
    def sizeStr(self, kbytes):
        try:
            if type(kbytes) != type(int):
                kbytes = int(kbytes)
            for scale, unit in ((1, "Mb"), (2, 'Gb'), (3, 'Tb'), (4, 'Pb')):
                if kbytes < math.pow(1024, scale + 1):
                    return "%0.1f %s" % (kbytes / math.pow(1024, scale), unit)
            return "%d Kb" % kbytes
        except ValueError:
            return kbytes

    ##########################################################################
    def stripQuotes(self, str):
        for i in range(2):      # Occassionally lots of nested quotes
            if str.startswith('"') and str.endswith('"'):
                str = str[1:-1]
            if str.startswith("'") and str.endswith("'"):
                str = str[1:-1]
        return str

    ##########################################################################
    def dequoteKV(self, line):
        """ Give a line "'a' : 'b'" return a,b
        This occurs quite often in hardware.py
        """
        try:
            bits = line.strip().split(':')
            a = self.stripQuotes(bits[0].strip())
            b = self.stripQuotes(bits[1].strip())
        except IndexError:
            self.Fatal("dequoteKV issue: line=%s" % line)
        return a, b

    ##########################################################################
    def parseLinux_hardwarepy(self, proc):
        if self.exists('hardware.py'):
            f = self.open('hardware.py')
        elif self.exists('etc/sysconfig/hwconf'):
            f = self.open('etc/sysconfig/hwconf')
        else:
            return
        buff = {}
        class_ = None
        for line in f:
            line = line.strip()
            if 'hardware.py' in line or 'Reading DMI info' in line:
                continue
            if not line or line == '-':
                if buff:
                    proc(buff, class_)
                    buff = {}
                    class_ = None
                continue
            key, val = self.dequoteKV(line)
            if key == 'class':
                class_ = val
            buff[key] = val
        f.close()
        if buff:
            proc(buff, class_)

    ##########################################################################
    def parseIostat(self, filename='disks/iostat_-E.out'):
        """ Parse iostat -E output; this would normally belong under disks, but it also
        handles tapes as well
        """
        if not self.exists(filename):
            self.Warning("Couldn't open %s" % filename)
            return {}
        f = self.open(filename)
        datadev = {}
        dev = ''
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = re.match(
                "(?P<device>\S+)\s*Soft Errors: (?P<softerrors>\d+) Hard Errors: (?P<harderrors>\d+) Transport Errors: (?P<transerrors>\d+)", line)
            if m:
                dev = m.group('device')
                datadev[dev] = {}
                datadev[dev].update(m.groupdict())
                continue
            m = re.match(
                "Vendor: (?P<vendor>.*?)\s+Product: (?P<product>.*?)\s+Revision: (?P<revision>.*) Serial No:(?P<serial>.*)", line)
            if m:
                datadev[dev].update(m.groupdict())
                continue
            # system info version
            m = re.match(
                "^(?P<vendor>.*?)\s+Product: (?P<product>.*?)\s+Revision: (?P<revision>.*) Serial No:(?P<serial>.*)", line)
            if m:
                datadev[dev].update(m.groupdict())
                continue
            m = re.match(
                "Model: (?P<model>.*) Revision: (?P<revision>.*) Serial No: (?P<serial>.*)", line)
            if m:
                datadev[dev].update(m.groupdict())
                continue
            m = re.match("Size: (?P<size>\S+) <(?P<bytes>-?\d+) bytes>", line)
            if m:
                datadev[dev].update(m.groupdict())
                continue
            # system info version
            m = re.match("^(?P<size>\S+) <(?P<bytes>-?\d+) bytes>", line)
            if m:
                datadev[dev].update(m.groupdict())
                continue
            m = re.match(
                "Media Error: (?P<mediaerror>\d+) Device Not Ready: (?P<devnotready>\d+)\s+No Device: (?P<nodev>\d+) Recoverable: (?P<recoverable>\d+)", line)
            if m:
                datadev[dev].update(m.groupdict())
                continue
            m = re.match(
                "Illegal Request: (?P<illreq>\d+) Predictive Failure Analysis: (?P<predfail>\d+)", line)
            if m:
                datadev[dev].update(m.groupdict())
                continue
            m = re.match("Illegal Request: (?P<illreq>\d+)", line)
            if m:
                datadev[dev].update(m.groupdict())
                continue
            m = re.match(
                "RPM: (?P<rpm>\d+) Heads: (?P<heads>\d+) Size: (?P<size>\S+) <(?P<bytes>-?\d+) bytes>", line)
            if m:
                datadev[dev].update(m.groupdict())
                continue
            # system info version
            m = re.match("^(?P<disk>c\d+t\d+d\d+)$", line)
            if m:
                dev = m.group('disk')
                datadev[dev] = {}
                datadev[dev].update(m.groupdict())
                continue
            self.Debug("Unhandled iostat line >%s<" % line)
        f.close()
        return datadev

# EOF
