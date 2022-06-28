#!/usr/bin/python

# Script to provide an aggregated interface to all sorts of storage
# handled by explorers
# This is so that scripts that need to know about host storage don't
# need to code for all the variations, and new types can be added here
# rather than in a number of other scripts.
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: storage.py 4380 2013-02-22 02:53:51Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/storage.py $

import explorerbase
import disks
import emc
import filesys
import zfs
import swap
import volmanager
import vxvm
import cluster
import prtconf

verbFlag = False

# There are a number of data tags that have more complex meanings or
# more important uses

# use - mountpoint, swap, metadb, etc - the final use of the resource
# name - what to call it if use isn't usable as the name
# protected - If the data is redundantly protected (raid, mirror, etc) and how
# usepoint - the top storage point - i.e. the device that gets mounted
# partof - the list of elements that make use of this element (e.g a submirror is part of a mirror)
# contains - the elements that this element makes use of (e.g. a mirror
# contains a submirror contains a slice)


##########################################################################
# Storage ################################################################
##########################################################################
class Storage(explorerbase.ExplorerBase):
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.cache = {}
        self.parse()

    ##########################################################################
    def parse(self):
        self.initialParse()
        self.clusterCheck()
        self.bootAliases()
        self.crossPopulate()

    ##########################################################################
    def fsList(self):
        return self.genericList("filesystem")

    ##########################################################################
    def bootAliases(self):
        """PROM devaliases"""
        # 'disk1': '/pci@1c,600000/scsi@2/disk@1,0'
        # Also need to check
        # 'disk1': '/pci@1c,600000/scsi@2/sd@1,0'
        prt = prtconf.Prtconf(self.config)
        bootaliases = prt["boot_aliases"]
        for objname, obj in self.items():
            aliases = set()
            if "path" in obj:
                for alias, dev in bootaliases.items():
                    if obj["path"] == dev:
                        aliases.add(alias)
                    elif obj["path"] == dev.replace("disk", "sd"):
                        aliases.add(alias)
                if aliases:
                    self[objname]["bootaliases"] = list(aliases)

    ##########################################################################
    def initialParse(self):
        """Parse the raw sources of data"""
        d = disks.storageDisks(self.config, {})
        self.data.update(d.data)
        self.cache["disks"] = d

        f = filesys.storageFilesystems(self.config, self.data)
        self.data.update(f.data)
        self.cache["filesys"] = f

        z = zfs.storageZfs(self.config, self.data)
        self.data.update(z.data)
        self.cache["zfs"] = z

        s = swap.storageSwap(self.config, self.data)
        self.data.update(s.data)
        self.cache["swap"] = s

        ds = volmanager.storageVolmanager(self.config, self.data)
        self.data.update(ds.data)
        self.cache["volmanager"] = ds

        v = vxvm.storageVxvm(self.config, self.data)
        self.data.update(v.data)
        self.cache["vxvm"] = v

        e = emc.storageEmc(self.config, self.data)
        self.data.update(e.data)
        self.cache["emc"] = e

    ##########################################################################
    @classmethod
    def initialDict(class_=None, d={}):
        """Setup an initial dictionary for most things"""
        id = {
            "_type": "unset",
            "use": set(),
            "protected": False,
            "devices": set(),
            "partof": set(),
            "contains": set(),
        }
        id.update(d)
        return id

    ##########################################################################
    def clusterCheck(self):
        """Get the required details from the cluster module"""
        c = cluster.Cluster(self.config)
        if "clusterfs" in c:
            self["clusterfs"] = c["clusterfs"]
        if "quorum" in c and c["quorum"]:
            quorumdev = c["quorum"].replace("/dev/did/rdsk/", "")
            slice = quorumdev[-2:]
            dev = quorumdev[:-2]
            if dev not in self["_didmap"]:
                self.Warning("Couldn't find quorum disk %s did details" % dev)
                return
            for d in self["_didmap"][dev]:
                qslice = "%s%s" % (d, slice)
                if qslice not in self:
                    self.Warning("Quorum slice %s has no disk defined" % qslice)
                else:
                    self[qslice]["use"] = set(["Cluster %s Quorum" % c["name"]])

    ##########################################################################
    def genericList(self, types):
        ans = []
        if not isinstance(types, list):
            types = [types]
        for objname, obj in self.data.items():
            if "_type" not in obj:
                continue
            if obj["_type"] in types:
                ans.append(objname)
        return sorted(ans)

    ##########################################################################
    def protectionCheck(self):
        """Determine if data is protected by redundancy"""

        for objname, obj in self.items():
            if "_type" not in obj:
                pass
            elif "virtual" in obj and obj["virtual"]:
                pass
            elif "fstype" in obj and obj["fstype"] == "nfs":
                self.protPropogator(objname, True)
            elif "protected" in obj and obj["protected"]:
                self.protPropogator(objname, obj["protected"])

    ##########################################################################
    def protPropogator(self, objname, val):
        """Generic propogator of key=val up the chain"""
        for parent in self[objname]["partof"]:
            if "protected" in self[objname] and self[objname]["protected"]:
                try:
                    self[parent]["protected"] = val
                except KeyError:
                    self.Warning("protPropogator(objname=%s, val=%s)" % (objname, val))
                    raise
            self.protPropogator(parent, val)

    ##########################################################################
    def relationshipMunger(self):
        """Migrate the descriptions up and down the chain using the partof/contains
        keys.

        /opt -> contains d10 -> contains c0t0d0s3
        c0t0d0s0 -> partof d10 -> partof /opt

        If something has a parent then that parent has it as a child
        If something has children then those children have it as a parent
        """
        # Label the relationships with '_relationship'
        # source - this is the original source of the data
        # up - this data should go up the tree only
        # down - this data should go down the tree only
        # This is to stop stuff going up the tree and then down again
        for objname, obj in self.data.items():
            if "partof" not in obj or "contains" not in obj:
                continue
            if "_relationship_source" not in obj:
                obj["_relationship_source"] = obj["partof"].union(obj["contains"])
            if "_relationship_up" not in obj:
                obj["_relationship_up"] = set()
            if "_relationship_down" not in obj:
                obj["_relationship_down"] = set()

        diffs = -1
        # If there are problems with the relationship model then uncomment the
        # following line for a good time
        # self.Debug("data=%s" % self.data.items())
        while diffs:
            diffs = 0
            for objname, obj in self.data.items():
                if "virtual" in obj and obj["virtual"]:
                    continue
                if "partof" in obj and obj["partof"]:
                    diffs += self.upRelations(objname, set([objname]))
                if "contains" in obj and obj["contains"]:
                    diffs += self.downRelations(objname, set([objname]))

    ##########################################################################
    def upRelations(self, objname, val):
        count = 0
        # self.Debug("upRelations(objname=%s, val=%s)" % (objname, val))
        for parent in list(self[objname]["partof"]):
            # self.Debug("parent=%s" % parent)
            for subval in val:
                # self.Debug("up subval=%s" % subval)
                if parent not in self:
                    self.Debug(
                        "upRelations: parent %s doesn't exist. objname=%s val=%s subval=%s"
                        % (parent, objname, val, subval)
                    )
                if subval not in self[parent]["_relationship_down"]:
                    if subval not in self[parent]["contains"]:
                        self[parent]["contains"].add(subval)
                        self[parent]["_relationship_up"].add(subval)
                        count += 1
            try:
                count += self.upRelations(parent, val)
            except RuntimeError as err:
                print("#" * 80)
                for k in self.keys():
                    print("%s\t%s" % (k, self[k]))
                print("#" * 80)
                self.Fatal(
                    "upRelations: objname=%s val=%s %s - %s"
                    % (objname, val, self[objname], str(err))
                )
        return count

    ##########################################################################
    def downRelations(self, objname, val):
        count = 0
        # self.Debug("downRelations(objname=%s, val=%s)" % (objname, val))
        for kid in self[objname]["contains"]:
            # self.Debug("kid=%s" % kid)
            if kid not in self:
                self[kid] = Storage.initialDict(
                    {
                        "_type": "missing",
                        "missedby": objname,
                        "missed_at": "downRelations val=%s" % val,
                        "_relationship_up": set(),
                        "_relationship_down": set(),
                    }
                )
                self.Debug(
                    "kid %s missed by %s in downRelations val=%s" % (kid, objname, val)
                )
            for subval in val:
                # self.Debug("down subval=%s" % subval)
                if subval not in self[kid]["_relationship_up"]:
                    if subval not in self[kid]["partof"]:
                        # self.Debug("kid %s now partof %s" % (kid, subval))
                        self[kid]["partof"].add(subval)
                        self[kid]["_relationship_down"].add(subval)
                        count += 1
            try:
                count += self.downRelations(kid, val)
            except RuntimeError as err:
                print("#" * 80)
                for k in self.keys():
                    print("%s\t%s" % (k, self[k]))
                print("#" * 80)
                self.Fatal(
                    "downRelations: objname=%s val=%s %s - %s"
                    % (objname, val, self[objname], str(err))
                )
            except Exception:
                self.Debug(
                    "downRelations: objname=%s val=%s %s"
                    % (objname, val, self[objname])
                )
                raise
        return count

    ##########################################################################
    def upPropogator(self, objname, val, key):
        """Generic propogator of key=val up the chain"""
        diff = 0
        for parent in self[objname]["partof"]:
            b4 = len(self[parent][key])
            self[parent][key].update(val)
            diff += len(self[parent][key]) - b4
            diff += self.upPropogator(parent, val, key)
        return diff

    ##########################################################################
    def downPropogator(self, objname, val, key):
        """Generic propogator of key=val down the chain"""
        diff = 0
        for kid in self[objname]["contains"]:
            if kid not in self:
                self[kid] = Storage.initialDict(
                    {
                        "_type": "missing",
                        "missedby": objname,
                        "missed_at": "downPropogator key=%s val=%s" % (key, val),
                    }
                )
                self.Debug(
                    "kid %s missed by %s in downPropogator key=%s val=%s"
                    % (kid, objname, key, val)
                )
            b4 = len(self[kid][key])
            self[kid][key].update(val)
            diff += len(self[kid][key]) - b4
            diff += self.downPropogator(kid, val, key)
        return diff

    ##########################################################################
    def useMigrator(self):
        """Move the 'use' field around as appropriate"""
        for objname, obj in self.items():
            if "use" not in obj or not obj["use"]:
                continue
            if "_type" in obj:
                if "virtual" in obj and obj["virtual"]:
                    continue
                self.downPropogator(objname, obj["use"], "use")

    ##########################################################################
    def deviceCleaner(self):
        """Set the devices of an object to the lower type of object available"""
        for objname, obj in self.data.items():
            if "contains" not in obj:
                continue
            s = set()
            typelist = ["slice", "disk"]
            for typ in typelist:
                # The devices should contain only the slices involved
                for o in obj["contains"]:
                    if o not in self:
                        self.Debug(
                            "%s is in contains %s of %s but doesn't exist"
                            % (o, obj["contains"], objname)
                        )
                        continue
                    if self[o]["_type"] == typ:
                        s.add(o)
                if s:
                    break

            obj["devices"] = s

    ##########################################################################
    def crossPopulate(self):
        """Match all of the uses and partitions and set values accordingly"""

        self.relationshipMunger()
        for k in ("volmanager", "swap", "filesys", "zfs", "vxvm", "disks", "emc"):
            self.cache[k].crossPopulate(self.data)
        self.useMigrator()
        self.deviceCleaner()
        for k in ("volmanager", "swap", "filesys", "zfs", "vxvm", "disks", "emc"):
            self.cache[k].crossPopulate(self.data)
        self.protectionCheck()

        # Check to see if the disks are in use - has to be done after all
        # the use calculations
        self.cache["disks"].calculateUsed(self.data)
        self.cache["emc"].calculateUsed(self.data)

        self.allDescriber()

    ##########################################################################
    def allDescriber(self):
        # Work out a description for each object
        for obj in self.keys():
            if "_type" not in self[obj]:
                continue
            if self[obj]["_type"] == "filesystem":
                self[obj]["describer"] = self.cache["filesys"].describer(obj, self.data)
            elif self[obj]["_type"] in ("slice", "disk", "emcpower"):
                self[obj]["describer"] = self.cache["disks"].describer(obj, self.data)
            elif self[obj]["_type"] in (
                "disksuite",
                "metadb_copy",
                "metadb",
                "metadev",
                "logvol",
            ):
                self[obj]["describer"] = self.cache["volmanager"].describer(
                    obj, self.data
                )
            elif self[obj]["_type"] in ("swap", "allswap"):
                self[obj]["describer"] = self.cache["swap"].describer(obj, self.data)
            elif self[obj]["_type"] == "boot_partition":
                self[obj]["describer"] = "Boot Partition"
            elif self[obj]["_type"] in ("zfs_pool", "zfs_subpool"):
                self[obj]["describer"] = self.cache["zfs"].describer(obj, self.data)
            elif self[obj]["_type"] == "missing":
                self[obj]["describer"] = "missing"
            elif self[obj]["_type"] in ("did_slice", "did_disk"):
                self[obj]["describer"] = "DID"
            elif self[obj]["_type"] in ("emcdisk", "emcslice"):
                self[obj]["describer"] = self.cache["emc"].describer(obj, self.data)
            elif self[obj]["_type"] in ("vxvm_diskgroup", "vxvm_volume", "vxvm_dgvol"):
                self[obj]["describer"] = self.cache["vxvm"].describer(obj, self.data)
            else:
                self[obj]["describer"] = "Unhandled %s" % self[obj]["_type"]
                self.Debug("Unhandled describer %s - %s" % (obj, self[obj]["_type"]))

    ##########################################################################
    def poolList(self):
        return self.genericList("zfs_pool")

    ##########################################################################
    def diskList(self):
        """Return the list of disks that are attached to this host"""
        return self.genericList("disk")

    ##########################################################################
    def emcdiskList(self):
        """Return the list of disks that are attached to this host"""
        return self.genericList("emcdisk")

    ##########################################################################
    def sliceList(self, disk):
        """Return the list of slice that the specified disk has"""
        return sorted(self[disk]["slices"])

    @classmethod
    ##########################################################################
    def pluralDescription(class_, val, objlist):
        # Work out a count of the obj to see if it should be plural
        olist = []
        count = 0
        for v1, o1 in objlist:
            if v1 == val:
                count += 1
                olist.append(o1)
        if count > 1:
            plural = "s"
        else:
            plural = ""
        return plural, olist

    ##########################################################################
    def get(self, o, key):
        if not o:
            return ""
        if key in self[o]:
            return self[o][key]
        return ""


# EOF
