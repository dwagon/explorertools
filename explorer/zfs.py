"""
# Understand zfs details
"""
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
    """ TODO """
    def __init__(self, config, pool, data, alldata):
        self.objname = pool
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.alldata = alldata

    ##########################################################################
    def analyse(self):
        """ TODO """
        if self["health"] != "ONLINE":
            self.addIssue(
                "poolhealth",
                obj=self.objname,
                text=f"ZFS pool has health of {self['health']}",
            )


##########################################################################
# Zfs ####################################################################
##########################################################################
class Zfs(explorerbase.ExplorerBase):
    """ TODO """
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.st = storage.Storage(config)
        for objname, obj in self.st.items():
            if "_type" in obj and obj["_type"] == "zfs_pool":
                self[objname] = ZfsPool(config, objname, obj, self.st)
        self.analyse()

    ##########################################################################
    def pool_list(self):
        """ TODO """
        return self.values()

    ##########################################################################
    def analyse(self):
        """ TODO """
        for pool in self.pool_list():
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
        """ TODO """
        self.parse_zpool()
        for pool in self.pool_list():
            self.parse_get(pool)
        self.parse_zpool_iostat()

    ##########################################################################
    def pool_list(self):
        """Return a list of pools that exist on this host"""
        return self["zfspools"]

    ##########################################################################
    def parse_get(self, pool):
        """ TODO """
        self.parse_zpool()
        # Construct a dictionary of the zfs properties in tmpd
        # Key'd on the property, values are a list of the values, source
        self[pool]["properties"] = {}
        tmpd = {}
        olddata = ""
        filename = f"disks/zfs/zfs_get_-rHp_all_{pool}.out"
        infh = self.open(filename)
        for line in infh:
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
                            mntpnt = tmpd["mountpoint"][0]
                            if mntpnt != "/" and mntpnt.endswith("/"):
                                mntpnt = mntpnt[:-1]
                            if (
                                mntpnt not in ("legacy", "none")
                                and mntpnt not in self[pool]["use"]
                                and ".alt.tmp." not in mntpnt
                                and ".alt.initial" not in mntpnt
                            ):
                                self[pool]["use"].add(mntpnt)
                    tmpd = {}
                else:
                    tmpd[bits[1]] = bits[2:]
        infh.close()

    ##########################################################################
    def describer(self, obj, data):
        """ TODO """
        self.parse_zpool()
        return f"obj={obj}"

    ##########################################################################
    def parse_zpool_iostat(self):
        """ TODO """
        self.parse_zpool()
        filename = "disks/zfs/zpool_iostat_-v.out"
        if not self.exists(filename):
            return
        infh = self.open(filename)
        for line in infh:
            if not line.startswith(" "):
                try:
                    pool = line.split()[0]
                except IndexError:
                    pass
            # Full disk
            matchobj = re.search(r"\s+(?P<device>c\d+t[A-F\d]+d\d+)\s", line)
            if matchobj:
                self[pool]["devices"].add(matchobj.group("device"))
                self[pool]["contains"].add(matchobj.group("device"))
                continue
            # Slice of a disk
            matchobj = re.search(r"\s+(?P<device>c\d+t[A-F\d]+d\d+s\d+)\s", line)
            if matchobj:
                self[pool]["devices"].add(matchobj.group("device"))
                self[pool]["contains"].add(matchobj.group("device"))
        infh.close()

    ##########################################################################
    def crossPopulatePool(self, pool, data):
        """ TODO """
        self.parse_zpool()
        # For every mount point in the pool, tell the mount point about it
        data[pool]["partof"].update(self[pool]["use"])

        # The pool should contain the devices that make up that pool
        data[pool]["contains"].update(self[pool]["devices"])

        for mntpnt in self[pool]["use"]:
            if mntpnt in data:
                data[mntpnt]["pool"] = pool
                data[mntpnt]["contains"].add(pool)
            else:
                self.addConcern(
                    "mount",
                    obj=mntpnt,
                    text=f"ZFS pool {pool} has filesystem {mntpnt} which isn't mounted"
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
            data[pool]["protected"] = f"RaidZ - {numdev} devices"

    ##########################################################################
    def check_sub_pools(self, pool, data):
        """ TODO """
        # Filesystems get mounted under pools, not from the pools themselves
        # Eg. from pool01/da01 even though it is using pool01
        for _, fsdata in data.items():
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
    def cross_populate(self, data):
        """ TODO """
        if "zfspools" not in data:  # No ZFS here
            return
        for pool in self.pool_list():
            self.crossPopulatePool(pool, data)
            self.check_sub_pools(pool, data)

    ##########################################################################
    def parse_zpool(self):
        """ TODO """
        filename = "disks/zfs/zpool_list.out"
        infh = self.open(filename)
        for line in infh:
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
            pool = storage.Storage.initialDict(
                {"_type": "zfs_pool", "description": "ZFS Pool", "_origin": filename}
            )
            pool["size"] = bits[1]
            pool["used"] = bits[2]
            pool["avail"] = bits[3]
            pool["cap"] = bits[4]
            pool["health"] = bits[5]
            pool["altroot"] = bits[6]
            self[pool] = pool
        infh.close()


# EOF
