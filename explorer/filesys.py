#!/usr/bin/env python3
"""
Script to understand filesystem details
"""
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: filesys.py 4431 2013-02-27 07:38:45Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/filesys.py $

import re
from explorer import explorerbase
from explorer import storage


##########################################################################
# Filesystem #############################################################
##########################################################################
class Filesystem(explorerbase.ExplorerBase):
    """ TODO """
    ##########################################################################
    def __init__(self, config, flsys, data, alldata):
        self.objname = flsys
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.alldata = alldata

    ##########################################################################
    def analyse(self):
        """ TODO """
        if not self["protected"]:
            self.addIssue(
                "unprotected", obj=self.name(), text=f"{self.name()} is not redundant"
            )

    ##########################################################################
    def get_notes(self):
        """ TODO """
        return self["describer"]


##########################################################################
# Filesystems ############################################################
##########################################################################
class Filesystems(explorerbase.ExplorerBase):
    """ TODO """
    def __init__(self, config):
        """ TODO """
        explorerbase.ExplorerBase.__init__(self, config)
        self.st = storage.Storage(config)
        for flsys in self.st.keys():
            if "_type" in self.st[flsys] and self.st[flsys]["_type"] == "filesystem":
                self[flsys] = Filesystem(config, flsys, self.st[flsys], self.st)
        self.analyse()

    ##########################################################################
    def analyse(self):
        """ TODO """
        for flsys in self.fs_list():
            flsys.analyse()
            self.inheritIssues(flsys)

    ##########################################################################
    def fs_list(self):
        """ TODO """
        return [self[flsys] for flsys in sorted(self.keys())]

    ##########################################################################
    def capacity(self):
        """ TODO """
        used = 0
        capac = 0
        for mntpnt in self.fs_list():
            if mntpnt["fstype"] in ("zfs", "nfs"):
                continue
            if "kbytes" in mntpnt:
                capac += mntpnt["kbytes"]
            if "used" in mntpnt:
                used += mntpnt["used"]
        return (used, capac)


##########################################################################
# storageFilesystems #####################################################
##########################################################################
class storageFilesystems(explorerbase.ExplorerBase):
    """Understand explorer output with respect to all filesystems and their ilk"""

    ##########################################################################
    def __init__(self, config, data=None):
        explorerbase.ExplorerBase.__init__(self, config)
        if data is None:
            data = {}
        self.data = data
        self.parse()

    ##########################################################################
    def parse(self):
        """ TODO """
        self["filesystems"] = set()
        self.parse_mount()
        self.parse_fstab()
        self.parse_df()
        self.virtual_check()

    ##########################################################################
    def parse_df(self):
        """Provide to the filesystem class:
        device - device filesystem is mount on
        kbytes - total capacity in kbytes
        used - space used up in kbytes
        avail - space left to use in kbytes
        pct - % used
        """

        if self.config["explorertype"] == "solaris":
            dffile = None
            for fname in ["disks/df-klZ.out", "disks/df-kl.out", "disks/df-k.out"]:
                if self.exists(fname):
                    dffile = fname
                    break
            if not dffile:
                self.warning("No usable df file")
                return
        elif self.config["explorertype"] == "linux":
            dffile = "df"
        else:
            self.fatal(
                f"parse_df - unsupported explorer type {self.config['explorertype']}"
            )
        self.parse_df_real(dffile)

    ##########################################################################
    def virtual_check(self):
        """Go through all the filesystems and calculate whether they are virtual
        filesystems or not
        """
        for flsys in self["filesystems"].copy():
            if self.is_virtual(flsys):
                del self[flsys]
                self["filesystems"].remove(flsys)
            else:
                self[flsys]["description"] = "Filesystem"

    ##########################################################################
    def is_virtual(self, flsys):
        """ TODO """
        # mvfs - Multi Version File System - ClearCase
        # odm - Oracle Disk Manager
        if "fstype" not in self[flsys]:
            return False
        if self[flsys]["fstype"] in (
            "mntfs",
            "proc",
            "fd",
            "devfs",
            "objfs",
            "ctfs",
            "tmpfs",
            "lofs",
            "rpc_pipefs",
            "devpts",
            "usbfs",
            "binfmt_misc",
            "sysfs",
            "sharefs",
            "iso9660",
            "usbdevfs",
            "hsfs",
            "oracleasmfs",
            "shmfs",
            "shm",
            "mvfs",
            "autofs",
            "odm",
            # 'nfs', 'nfsd',
        ):
            return True
        if "/libc_" in flsys:
            return True
        if "device" in self[flsys] and self[flsys]["device"] == "mnttab":
            return True
        return False

    ##########################################################################
    def dehumanise(self, strn: str) -> int:
        """Convert a string generated by a -h option (e.g. 37M, 1.7G) into
        kbytes
        """
        num = float(strn[:-1])
        units = strn[-1]
        if units == "G":
            return int(num * 1024 * 1024)
        if units == "M":
            return int(num * 1024)
        self.fatal(f"dehumanise - unknown units {units}")
        return 0

    ##########################################################################
    def parse_df_real(self, dffile):
        """ TODO """
        infh = self.open(dffile)
        oldline = None
        for line in infh:
            if line.startswith("Filesystem"):
                continue
            if line.startswith("/bin/df"):
                continue
            if oldline and line.startswith(" "):
                line = f"{oldline} {line}"
                oldline = None
            bits = line.split()
            if len(bits) == 1:
                oldline = line
                continue
            mntpnt = bits[-1]
            if mntpnt not in self.data:
                continue
            flsys = self[mntpnt]
            if "device" not in flsys or not flsys["device"]:
                flsys["device"] = bits[0]
            try:
                flsys["kbytes"] = int(bits[1])  # Capacity
            except ValueError:
                flsys["kbytes"] = self.dehumanise(bits[1])
            try:
                flsys["used"] = int(bits[2])  # K used
            except ValueError:
                flsys["used"] = self.dehumanise(bits[2])
            try:
                flsys["avail"] = int(bits[3])  # K available
            except ValueError:
                flsys["avail"] = self.dehumanise(bits[3])

            flsys["pct"] = bits[4]
        infh.close()

    ##########################################################################
    def fs_list(self):
        """ TODO """
        return self["filesystems"]

    ##########################################################################
    def parse_mount(self):
        """Parse the mounted filesystems
        Need to create new filesystems if found and set the following attributes
                device - the physical device used
                fstype - the type of filesystem (ufs, ext3, etc)
        """
        if self.config["explorertype"] == "solaris":
            self.parse_solaris_mount()
            self.parse_solaris_mnttab()
        elif self.config["explorertype"] == "linux":
            self.parse_linux_mount()
        else:
            self.fatal(
                f"parse_mount - unsupported explorer type {self.config['explorertype']}"
            )

    ##########################################################################
    def parse_linux_mount(self):
        """ TODO """
        infh = self.open("mount")
        for line in infh:
            line = line.strip()
            if line == "/bin/mount":
                continue
            matchobj = re.search(
                r"(?P<dev>\S+) on (?P<mp>\S+) type (?P<fstype>\S+) \((?P<opts>.*)\)",
                line,
            )
            mntpnt = matchobj.group("mp")
            dev = self.sanitiseDevice(matchobj.group("dev"))
            self[mntpnt] = storage.Storage.initialDict(
                {"_type": "filesystem", "usepoint": "", "_origin": "mount"}
            )
            self["filesystems"].add(mntpnt)
            self[mntpnt]["fstype"] = matchobj.group("fstype")
            if self[mntpnt]["fstype"] == "nfs":
                self[mntpnt]["protected"] = True
            self[mntpnt]["device"] = dev
            self[mntpnt]["usepoint"] = dev
            self[mntpnt]["contains"].add(dev)
            self[mntpnt]["use"].add(mntpnt)
            self[mntpnt]["opts"] = matchobj.group("opts")
        infh.close()

    ##########################################################################
    def parse_solaris_mnttab(self):
        """ TODO """
        filename = "etc/mnttab"
        if not self.exists(filename):
            return
        infh = self.open(filename)
        for line in infh:
            if ":vold" in line:
                continue
            bits = line.split()
            mntpnt = bits[1]
            if mntpnt not in self:
                self[mntpnt] = storage.Storage.initialDict(
                    {"_type": "filesystem", "_origin": filename}
                )
                self["filesystems"].add(mntpnt)
                self[mntpnt]["device"] = bits[0]
            if "fstype" not in self[mntpnt] or not self[mntpnt]["fstype"]:
                self[mntpnt]["fstype"] = bits[2]
            if self[mntpnt]["fstype"] == "nfs":
                self[mntpnt]["device"] = bits[0]
                self[mntpnt]["protected"] = "NFS"
        infh.close()

    ##########################################################################
    def parse_solaris_mount(self):
        """ TODO """
        filename = None
        for fname in ("disks/mount-v.out", "disks/mount.out"):
            if self.exists(fname):
                filename = fname
                break
        if not filename:
            self.warning("No usable mount output")
            return
        infh = self.open(filename)
        for line in infh:
            if line.find("zone=") >= 0:
                continue
            bits = line.split()
            # If the mount-v is unavailable, then this isn't what we want
            if "-v" in filename:
                mntpnt = bits[2]
                if mntpnt not in self:
                    self[mntpnt] = storage.Storage.initialDict(
                        {"_type": "filesystem", "usepoint": "", "_origin": filename}
                    )
                    self["filesystems"].add(mntpnt)
                flsys = self[mntpnt]
                flsys["device"] = self.sanitiseDevice(bits[0])
                flsys["usepoint"] = flsys["device"]
                flsys["fstype"] = bits[4]
                flsys["contains"].add(flsys["device"])
            else:
                mntpnt = bits[1]
                if mntpnt not in self:
                    self[mntpnt] = storage.Storage.initialDict(
                        {
                            "_type": "filesystem",
                            "usepoint": "",
                            "_origin": filename,
                            "fstype": "",
                        }
                    )
                    self["filesystems"].add(mntpnt)
                flsys = self[mntpnt]
                flsys["device"] = self.sanitiseDevice(bits[0])
                flsys["usepoint"] = flsys["device"]
                flsys["fstype"] = bits[2]
                flsys["contains"].add(flsys["device"])
                flsys["use"].add(mntpnt)
        infh.close()

    ##########################################################################
    def parse_fstab(self):
        """ TODO """
        try:
            if self.config["explorertype"] == "solaris":
                self.parse_solaris_vfstab()
            elif self.config["explorertype"] == "linux":
                self.parse_linux_fstab()
            else:
                self.fatal(
                    f"parse_fstab - unsupported explorer type {self.config['explorertype']}"
                )
        except UserWarning as err:
            self.warning(err)

    ##########################################################################
    def parse_linux_fstab(self):
        """ TODO """
        # TO DO - currently ignored
        infh = self.open("etc/fstab")
        for line in infh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            bits = line.split()
            # dev = bits[0]
            # mntpnt = bits[1]
            fstype = bits[2]
            try:
                _ = bits[3]
            except IndexError:
                if fstype != "nfs":
                    self.warning(f"Malformed fstab line: {line}")
        infh.close()

    ##########################################################################
    def parse_solaris_vfstab(self):
        """
        Analyse vfstab output
        Only do real filesystems, no swap
        """
        infh = self.open("etc/vfstab")
        for line in infh:
            line = line.rstrip()
            if not line or line.startswith("#"):
                continue
            bits = line.split()
            if len(bits) < 4:
                self.warning(f"Unhandled vfstab line: {line}")
                continue
            mntpnt = bits[2]
            if mntpnt == "-":
                continue
            # Have seen this which causes problems
            if mntpnt.endswith("/") and mntpnt != "/":
                mntpnt = mntpnt[:-1]
            if "/dsk/" in bits[1]:  # Should always be /rdsk/
                self.addIssue(
                    "vfstab", obj=mntpnt, text=f"FSCK device misconfigured for {mntpnt}"
                )
            if mntpnt not in self:
                self.addConcern(
                    "vfstab", obj=mntpnt, text="Mounted filesystem is not in vfstab"
                )
                self[mntpnt] = storage.Storage.initialDict(
                    {"_type": "filesystem", "_origin": "etc/vfstab"}
                )
            flsys = self[mntpnt]
            newdev = self.sanitiseDevice(bits[0])
            if "device" in flsys and flsys["device"] != newdev:
                self.addIssue(
                    "vfstab",
                    obj=mntpnt,
                    text=f"Mounted device {flsys['device']} disagrees with vfstab device {newdev}"
                )
            flsys["device"] = self.sanitiseDevice(bits[0])
            flsys["usepoint"] = flsys["device"]
            flsys["use"].add(mntpnt)
            flsys["contains"].add(flsys["device"])
            flsys["fstype"] = bits[3]
            self["filesystems"].add(mntpnt)
            self[mntpnt] = flsys
        infh.close()

    ##########################################################################
    # TO DO: Add code to add up filesystem size +  cap
    # TO DO: access zfs details to get userd + kbytes.
    def cross_populate(self, data):
        """ TODO """
        # TO DO - filesystems that we only know from the cluster resourcing
        for cfs in self["clusterfs"]:
            if cfs not in self:
                self.debug(f"Thinking about adding cluster fs={cfs}")
                # self[cfs]=storage.Storage.initialDict({'_type': 'filesystem', 'usepoint':'', 'cluster':True})
            else:
                self[cfs]["cluster"] = True
        for flsys in self.fs_list():
            for dev in data[flsys]["devices"]:
                if dev in data:
                    data[dev]["use"].add(flsys)

                    # If the device is protected then the filesytem on it is
                    # also protected
                    if "protected" in data[dev]:
                        data[flsys]["protected"] = data[dev]["protected"]
                        # self.warning("Filesystem %s is protected (%s) as it is on %s" % (flsys, data[dev]['protected'], dev))
                else:
                    self.warning(f"FS {flsys} relies on non existant device {dev}")


# EOF
