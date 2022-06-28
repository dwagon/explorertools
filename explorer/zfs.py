#!/usr/local/bin/python
#
# Script to understand zfs details
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: zfs.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/zfs.py $

import re
import explorerbase
import storage

##########################################################################
# ZfsPool ################################################################
##########################################################################


class ZfsPool(explorerbase.ExplorerBase):
    def __init__(self, config, pool, data, alldata):
        self.objname = pool
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.alldata = alldata

    ##########################################################################
    def analyse(self):
        if self["health"] != "ONLINE":
            self.addIssue(
                "poolhealth",
                obj=self.objname,
                text="ZFS pool has health of %s" % self["health"],
            )


##########################################################################
# Zfs ####################################################################
##########################################################################


class Zfs(explorerbase.ExplorerBase):
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.st = storage.Storage(config)
        for objname, obj in self.st.items():
            if "_type" in obj and obj["_type"] == "zfs_pool":
                self[objname] = ZfsPool(config, objname, obj, self.st)
        self.analyse()

    ##########################################################################
    def poolList(self):
        return self.values()

    ##########################################################################
    def analyse(self):
        for pool in self.poolList():
            pool.analyse()
            self.inheritIssues(pool)


##########################################################################
# storageZfs #############################################################
##########################################################################


class storageZfs(explorerbase.ExplorerBase):

    """Understand explorer output with respect to zfs"""

    ##########################################################################

    def __init__(self, config, data):
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        if not self.exists("disks/zfs/zpool_list.out"):
            return
        self["zfspools"] = set()
        self.parse()

    ##########################################################################
    def parse(self):
        self.parseZpool()
        for pool in self.poolList():
            self.parseGet(pool)
        self.parseZpoolIostat()

    ##########################################################################
    def poolList(self):
        """Return a list of pools that exist on this host"""
        return self["zfspools"]

    ##########################################################################
    def parseGet(self, pool):
        # Construct a dictionary of the zfs properties in tmpd
        # Key'd on the property, values are a list of the values, source
        self[pool]["properties"] = {}
        tmpd = {}
        olddata = ""
        filename = "disks/zfs/zfs_get_-rHp_all_%s.out" % pool
        f = self.open(filename)
        for line in f:
            bits = line.strip().split()
            # name      property        value source
            subpool = bits[0]
            if "@" in subpool:  # Ignore snapshots etc.
                continue
            if subpool == pool:
                self[pool]["properties"][bits[1]] = bits[2]
            else:
                if subpool not in self:
                    self[subpool] = storage.Storage.initialDict(
                        {
                            "_type": "zfs_subpool",
                            "description": "ZFS SubPool",
                            "contains": set([pool]),
                            "_origin": filename,
                        }
                    )
                    self[subpool]["properties"] = {}
                    self[pool]["partof"].add(subpool)
                self[subpool]["properties"][bits[1]] = bits[2]
                if bits[0] != olddata:
                    olddata = bits[0]
                    if "mountpoint" in tmpd:
                        # Ignore unmounted filesystems
                        if "mounted" in tmpd and tmpd["mounted"][0] == "no":
                            pass
                        # Zoned filesystems appear in the zone, not the global
                        elif "zoned" in tmpd and tmpd["zoned"][0] != "off":
                            pass
                        else:
                            mp = tmpd["mountpoint"][0]
                            if mp != "/" and mp.endswith("/"):
                                mp = mp[:-1]
                            if (
                                mp not in ("legacy", "none")
                                and mp not in self[pool]["use"]
                                and ".alt.tmp." not in mp
                                and ".alt.initial" not in mp
                            ):
                                self[pool]["use"].add(mp)
                    tmpd = {}
                else:
                    tmpd[bits[1]] = bits[2:]
        f.close()

    ##########################################################################
    def describer(self, obj, data):
        return "obj=%s" % obj

    ##########################################################################
    def parseZpoolIostat(self):
        filename = "disks/zfs/zpool_iostat_-v.out"
        if not self.exists(filename):
            return
        f = self.open(filename)
        for line in f:
            if not line.startswith(" "):
                try:
                    pool = line.split()[0]
                except IndexError:
                    pass
            # Full disk
            m = re.search(r"\s+(?P<device>c\d+t[A-F\d]+d\d+)\s", line)
            if m:
                self[pool]["devices"].add(m.group("device"))
                self[pool]["contains"].add(m.group("device"))
                continue
            # Slice of a disk
            m = re.search(r"\s+(?P<device>c\d+t[A-F\d]+d\d+s\d+)\s", line)
            if m:
                self[pool]["devices"].add(m.group("device"))
                self[pool]["contains"].add(m.group("device"))
        f.close()

    ##########################################################################
    def crossPopulatePool(self, pool, data):
        # For every mount point in the pool, tell the mount point about it
        data[pool]["partof"].update(self[pool]["use"])

        # The pool should contain the devices that make up that pool
        data[pool]["contains"].update(self[pool]["devices"])

        for mp in self[pool]["use"]:
            if mp in data:
                data[mp]["pool"] = pool
                data[mp]["contains"].add(pool)
            else:
                self.addConcern(
                    "mount",
                    obj=mp,
                    text="ZFS pool %s has filesystem %s which isn't mounted"
                    % (pool, mp),
                )

        # Every device used by the pool gets the use of the pool
        for dev in self[pool]["devices"]:
            data[dev]["use"].update([pool])

        # The pool inherits the protection of its devices
        for dev in data[pool]["devices"]:
            if "protected" in data[dev]:
                data[pool]["protected"] = data[dev]["protected"]

        # If multiple devices are in the pool then it is redundant
        numdev = max(len(data[pool]["devices"]), len(data[pool]["devices"]))
        if numdev >= 2:
            data[pool]["protected"] = "RaidZ - %d devices" % numdev

    ##########################################################################
    def checkSubPools(self, pool, data):
        # Filesystems get mounted under pools, not from the pools themselves
        # Eg. from pool01/da01 even though it is using pool01
        for fsname, fsdata in data.items():
            if "_type" in fsdata and fsdata["_type"] == "filesystem":
                # fsdata is the filesystem that uses the pool
                if fsdata["device"] != pool and fsdata["device"].startswith(pool):
                    # Remove the 'pool01/da01' device (which doesn't really exist)
                    # and replace with 'pool01'
                    oldname = fsdata["device"]
                    fsdata["origdevice"] = oldname  # Not used, yet.
                    fsdata["device"] = pool
                    if oldname in fsdata["contains"]:
                        fsdata["contains"].remove(oldname)
                        fsdata["contains"].add(pool)
                    #                   if oldname in fsdata['devices']:
                    #                       fsdata['devices'].remove(oldname)
                    #                       fsdata['devices'].add(pool)
                    fsdata["pool"] = pool

    ##########################################################################
    def crossPopulate(self, data):
        if "zfspools" not in data:  # No ZFS here
            return
        for pool in self.poolList():
            self.crossPopulatePool(pool, data)
            self.checkSubPools(pool, data)

    ##########################################################################
    def parseZpool(self):
        filename = "disks/zfs/zpool_list.out"
        f = self.open(filename)
        for line in f:
            line = line.strip()
            if line.startswith("NAME"):
                continue
            if line.startswith("no pools available"):
                return
            if "/sbin/zpool: not found" in line:
                return
            bits = line.split()
            pool = bits[0]
            self["zfspools"].add(pool)
            p = storage.Storage.initialDict(
                {"_type": "zfs_pool", "description": "ZFS Pool", "_origin": filename}
            )
            p["size"] = bits[1]
            p["used"] = bits[2]
            p["avail"] = bits[3]
            p["cap"] = bits[4]
            p["health"] = bits[5]
            p["altroot"] = bits[6]
            self[pool] = p
        f.close()


# EOF
