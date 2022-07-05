"""
# Script to understand vxvm details
# Ugly vxvm results in ugly code
"""
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: vxvm.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/vxvm.py $
# pylint: disable=too-few-public-methods

import re
from explorer import explorerbase
from explorer import storage


##########################################################################
# VxvmVolume #############################################################
##########################################################################
class VxvmVolume(explorerbase.ExplorerBase):
    """vxvm volume"""

    def __init__(self, config, volume, data, alldata):
        self.objname = volume
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.alldata = alldata

    ##########################################################################
    def analyse(self):
        """TODO"""
        if self["use"] == "Unused":
            self.addConcern("volume", obj=self.name(), text="Volume is not used")


##########################################################################
# VxvmDiskgroup ##########################################################
##########################################################################
class VxvmDiskgroup(explorerbase.ExplorerBase):
    """vxvm disk group"""

    def __init__(self, config, diskgroup, data, alldata):
        self.objname = diskgroup
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.alldata = alldata

    ##########################################################################
    def analyse(self):
        """TODO"""
        if "vxvm_status" in self and self["vxvm_status"] == "error":
            self.addIssue("diskgroup", obj=self.name(), text="Status is 'error'")


##########################################################################
# VxvmDgVolume ###########################################################
##########################################################################
class VxvmDgVolume(explorerbase.ExplorerBase):
    """vxvm disk group volume"""

    def __init__(self, config, dgvol, data, alldata):
        self.objname = dgvol
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.alldata = alldata

    ##########################################################################
    def analyse(self):
        """TODO"""


##########################################################################
# Vxvm ###################################################################
##########################################################################
class Vxvm(explorerbase.ExplorerBase):
    """vxvm"""

    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.st = storage.Storage(config)
        if "vxvm_diskgroups" not in self.st:
            return
        for dg in self.diskgroups_list():
            self[dg] = VxvmDiskgroup(config, dg, self.st[dg], self.st)

        for vol in self.volumes_list():
            self[vol] = VxvmVolume(config, vol, self.st[vol], self.st)

        for dgv in self.dgvols_list():
            self[dgv] = VxvmDgVolume(config, dgv, self.st[dgv], self.st)
        self.analyse()

    ##########################################################################
    def diskgroups_list(self):
        """TODO"""
        return self.st.data.get("vxvm_diskgroups", [])

    ##########################################################################
    def dgvols_list(self):
        """TODO"""
        return self.st.data.get("vxvm_dgvols", [])

    ##########################################################################
    def volumes_list(self):
        """TODO"""
        return self.st.data.get("vxvm_volumes", [])

    ##########################################################################
    def analyse(self):
        """TODO"""
        for dg in self.diskgroups_list():
            self[dg].analyse()
            self.inheritIssues(self[dg])

        for vol in self.volumes_list():
            self[vol].analyse()
            self.inheritIssues(self[vol])

        for dgv in self.dgvols_list():
            self[dgv].analyse()
            self.inheritIssues(self[dgv])


##########################################################################
# storageVxvm ############################################################
##########################################################################
class storageVxvm(explorerbase.ExplorerBase):
    """Understand explorer output with respect to vxvm"""

    def __init__(self, config, data=None):
        if data is None:
            data = {}
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        if not self.exists("disks/vxvm/vxdg-q-list.out"):
            return
        self["vxvm_diskgroups"] = set()
        self["vxvm_volumes"] = set()
        self["vxvm_dgvols"] = set()
        self.parse()

    ##########################################################################
    def parse(self):
        """TODO"""
        self.parse_vxdg()
        self.parseVxDisk()
        self.parse_vxprint()
        self.parse_dev_tree()

    ##########################################################################
    def foreign_disklist(self, data):
        """Disks exist on the system that belong to diskgroups on other systems
        Not sure how it works
        """
        disks = self.glob("disks/vxvm/disks/vxdisk_list*.out")
        for disk in disks:
            hostid, dev, group = self.check_foreigndisk(disk)
            if hostid and hostid != self.hostname:
                if dev not in data:
                    self.Warning(f"VXVM referring to an unknown disk {dev}")
                    continue
                if "disk" not in self[dev]:
                    self.Warning(f"VXVM referring to something unusual for disk {dev}")
                    continue
                disk = data[dev]["disk"]
                data[disk]["use"] = set([f"VXVM diskgroup {group} on server {hostid}"])

    ##########################################################################
    def check_foreigndisk(self, diskfile):
        """TODO"""
        dev = None
        hostid = None
        group = None
        infh = self.open(diskfile)
        for line in infh:
            if line.startswith("Device:"):
                dev = line.split()[-1]
            if line.startswith("hostid:"):
                hostid = line.split()[-1]
            if line.startswith("group:"):
                matchobj = re.search(r".*name=(?P<name>\S*) id=.*", line)
                if matchobj:
                    group = matchobj.group("name")
                else:
                    self.Fatal(f"Couldn't match line {line}")
        infh.close()
        return hostid, dev, group

    ##########################################################################
    def parse_dev_tree(self):
        """Have seen this a couple of times - an alias in the device tree
        for a diskgroup

        /dev/vx/dsk:
        total 6
        lrwxrwxrwx 1 root root 5 Aug  1  2007 bootdg -> sysdg
        lrwxrwxrwx 1 root root 49 Jun 30  2008 ssedb802p-dg -> /global/.devices/node@1//dev/vx/rdsk/ssedb802p-dg
        """
        infh = self.open("disks/vxvm/ls-lR_dev_vx.out")
        gameon = False
        for line in infh:
            line = line.strip()
            if line.startswith("/dev/vx/dsk"):
                gameon = True
            elif line.startswith("/"):
                gameon = False
            if gameon:
                if line.startswith("l"):
                    bits = line.split()[-3:]
                    vol = bits[2]
                    alias = bits[0]
                    if vol.startswith("/"):  # Not a dg alias
                        continue
                    self[alias] = self[vol].copy()
                    self["vxvm_diskgroups"].add(alias)
        infh.close()

    ##########################################################################
    def parse_vxprint(self):
        """TODO"""
        filename = "disks/vxvm/vxprint-h.out"
        infh = self.open(filename)
        for line in infh:
            line = line.strip()
            if line.startswith("Disk group"):
                diskgroup = line.split()[-1]
                self[diskgroup]["volumes"] = set()
            if line.startswith("v"):
                volume = line.split()[1]
                self[diskgroup]["volumes"].add(volume)
                self[volume] = storage.Storage.initialDict(
                    {
                        "_type": "vxvm_volume",
                        "_origin": filename,
                        "diskgroup": diskgroup,
                        "description": "VXVM Volume",
                        "contains": set([diskgroup]),
                    }
                )
                self["vxvm_volumes"].add(volume)
                # These are also referred to by diskgroup/volume
                dgvolname = f"{diskgroup}/{volume}"
                self[dgvolname] = storage.Storage.initialDict(
                    {
                        "_type": "vxvm_dgvol",
                        "_origin": filename,
                        "diskgroup": diskgroup,
                        "description": "VXVM Volume",
                        "volume": volume,
                        "contains": set([diskgroup]),
                    }
                )
                self["vxvm_dgvols"].add(dgvolname)
        infh.close()

    ##########################################################################
    def parse_vxdg(self):
        """TODO"""
        filename = "disks/vxvm/vxdg-q-list.out"
        infh = self.open(filename)
        for line in infh:
            bits = line.split()
            name = bits[0]
            self[name] = storage.Storage.initialDict(
                {
                    "_type": "vxvm_diskgroup",
                    "_origin": filename,
                    "description": "VXVM Diskgroup",
                }
            )
            self["vxvm_diskgroups"].add(name)
        infh.close()

    ##########################################################################
    def diskgroups_list(self):
        """TODO"""
        return self["vxvm_diskgroups"]

    ##########################################################################
    def dgvols_list(self):
        """TODO"""
        return self["vxvm_dgvols"]

    ##########################################################################
    def volumes_list(self):
        """TODO"""
        return self["vxvm_volumes"]

    ##########################################################################
    def cross_populate(self, data):
        """Match VXVM data with other storage data"""
        if "vxvm_diskgroups" not in data:  # No VXVM
            return

        for dg in self.diskgroups_list():
            self[dg]["devdesc"] = "VXVM diskgroup %s: %s" % (
                dg,
                ", ".join(self[dg]["devices"]),
            )
            if len(self[dg]["devices"]) >= 2:
                self[dg]["protected"] = "VXVM"

        for o in self.dgvols_list():
            diskgroup = self[o]["diskgroup"]
            self[o]["devices"] = self[diskgroup]["devices"]
            self[o]["devdesc"] = "VXVM DiskgroupVol: %s" % ", ".join(
                self[diskgroup]["devices"]
            )
            if len(self[o]["devices"]) >= 2:
                self[o]["protected"] = "VXVM"

        for o in self.volumes_list():
            diskgroup = self[o]["diskgroup"]
            self[o]["devices"] = self[diskgroup]["devices"]
            self[o]["devdesc"] = "VXVM Volume: %s" % ", ".join(
                self[diskgroup]["devices"]
            )
            if len(self[o]["devices"]) >= 2:
                self[o]["protected"] = "VXVM"

        for diskgroup in self.diskgroups_list():
            for dev in self[diskgroup]["devices"]:
                if dev not in data:
                    self.Warning("VXVM referring to unknown disk: %s" % dev)
                    self[dev] = storage.Storage.initialDict(
                        {
                            "_type": "missing",
                            "missedby": diskgroup,
                            "missed_at": "cross_populate",
                        }
                    )
                else:
                    data[dev]["partof"].add(diskgroup)

                if "disk" in data[dev]:
                    disk = data[dev]["disk"]
                    data[disk]["use"].add(diskgroup)
                    data[disk]["use"].update(data[diskgroup]["use"])

        self.foreign_disklist(data)

    ##########################################################################
    def parseVxDisk(self):
        """TODO"""
        infh = self.open("disks/vxvm/vxdisk-list.out")
        ctdnameFlag = False
        for line in infh:
            if line.startswith("DEVICE"):
                if "c#t#d#_NAME" in line or "OS_NATIVE_NAME" in line:
                    ctdnameFlag = True
                continue
            bits = line.split()
            device = bits[0]
            diskgroup = bits[3]

            if diskgroup.startswith("("):
                diskgroup = diskgroup[1:-1]
                if diskgroup not in self:
                    self[diskgroup] = storage.Storage.initialDict(
                        {
                            "_type": "vxvm_diskgroup",
                            "volumes": set(),
                            "description": "Unimported VXVM diskgroup %s" % diskgroup,
                        }
                    )
                    self.Warning("Unimported diskgroup %s" % diskgroup)

            if ctdnameFlag:
                status = " ".join(bits[4:-1])
                device = bits[-1]
            else:
                status = " ".join(bits[4:])

            if diskgroup not in self and diskgroup != "-":
                self.Warning("Previously unknown diskgroup %s" % diskgroup)
            if diskgroup != "-":
                self[diskgroup]["contains"].add(device)
            if device not in self:
                self.Warning("VXVM refering to an unknown disk %s" % device)
                self[device] = storage.Storage.initialDict(
                    {
                        "_type": "missing",
                        "missedby": diskgroup,
                        "missed_at": "parseVxDisk",
                    }
                )
            self[device].update({"diskgroup": diskgroup, "vxvm_status": status})
        infh.close()


# EOF
