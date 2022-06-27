#!/usr/local/bin/python
#
# Script to understand, represent and verify SDS/LVM configuration based on
# explorers and sosreports
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: volmanager.py 4380 2013-02-22 02:53:51Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/volmanager.py $

import os
import sys
import getopt
import string
import re
import explorerbase
import storage

verbFlag = 0

##########################################################################
# Metadev ################################################################
##########################################################################


class Metadev(explorerbase.ExplorerBase):
    def __init__(self, config, metadev, data, alldata):
        self.objname = metadev
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self.alldata = alldata

    ##########################################################################
    def analyse(self):
        self.mirrorCheck()
        if "use" not in self or not self["use"]:
            self.addConcern(
                "useless metadev",
                obj=self.name(),
                text="No use found for %s %s (devices %s)"
                % (self.name(), self["description"], ", ".join(list(self["devices"]))),
            )

    ##########################################################################
    def mirrorCheck(self):
        """Check for disks that are one-sided mirrors"""
        if self["type"] != "mirror":
            return
        mounts = set()
        # Not enough submirrors to be useful
        if "contains" in self:
            for tmp in self["contains"]:
                try:
                    mounts.update(self.alldata[tmp]["use"])
                except KeyError:
                    self.Warning(
                        "Couldn't find %s in data as in %s's contains"
                        % (tmp, self.name())
                    )
        else:
            if "use" in data:
                mounts.update(self["use"])
            else:
                mounts.update("unknown")
        for mount in mounts:
            numsubs = len(self["submirrors"])
            if numsubs < 2 and not self["protected"]:
                self.addIssue(
                    "onesidedmirror",
                    obj=mount,
                    text="%s (%s) - one sided mirror" % (mount, self.name()),
                )
            elif numsubs > 2:
                self.addConcern(
                    "multiwaymirror",
                    obj=mount,
                    text="%s (%s) - %d way mirror" % (mount, self.name(), numsubs),
                )


##########################################################################
# Volmanager #############################################################
##########################################################################


class Volmanager(explorerbase.ExplorerBase):
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.st = storage.Storage(config)
        for objname, obj in self.st.items():
            if "_type" in obj and obj["_type"] in (
                "metadev",
                "disksuite",
                "metadb",
                "metadb_copy",
            ):
                self[objname] = Metadev(config, objname, obj, self.st)
        self.analyse()

    ##########################################################################
    def analyseLinux_mdstat(self):
        if not self.exists("proc/mdstat"):
            return
        buff = []
        f = self.open("proc/mdstat")
        for line in f:
            line = line.strip()
            if line.startswith("Personalities"):
                continue
            if buff and not line:
                self.analyseLinux_mdstat_chunk(buff)
                buff = []
                continue
            buff.append(line.strip())

        f.close()

    ##########################################################################
    def metaList(self):
        return self.st["volmgt_metadevs"]

    ##########################################################################
    def analyseMetadb(self):
        """Check to see if the metadbs are in a safe configuration"""
        if "metadb" not in self:
            return
        if len(self["metadb"]["copies"]) == 0:
            return

        if len(self["metadb"]["devices"]) < 2:
            self.addIssue(
                "metadb diversity",
                obj="metadb",
                text="Insufficient diversity of metadbs",
            )
        if len(self["metadb"]["copies"]) < 2:  # Should be 3
            self.addIssue(
                "too few metadb",
                obj="metadb",
                text="Insufficient number of metadbs (%d copies)"
                % (len(self["metadb"]["copies"])),
            )

        numdbs = 0
        devs = {}
        for metadb in self["metadb"]["copies"]:
            if set(self[metadb]["flags"]).intersection(string.uppercase):
                self.addIssue(
                    "failed metadb",
                    obj=list(self[metadb]["contains"])[0],
                    text="Failure on metadb: %s" % self[metadb]["flags"],
                )
            if "diskset" in self[metadb] and self[metadb]["diskset"]:
                continue  # TODO - diskset metadbs *sigh*
            numdbs += 1
            dev = list(self[metadb]["contains"])[0]
            devs[dev] = devs.get(dev, 0) + 1

        for dev, count in devs.items():
            # metadbs can be on partitions with other stuff but it isn't
            # recommended
            otheruses = self.st[dev]["use"] - set(["metadb"])
            if otheruses:
                self.addConcern(
                    "mounted metadb",
                    obj=dev,
                    text="Slice used for more than metadb: %s"
                    % ",".join(list(otheruses)),
                )

            if numdbs - count < 2:
                self.addIssue(
                    "too few metadb on failure",
                    obj=dev,
                    text="Insufficient local metadbs if %s failed (%d left)"
                    % (dev, (numdbs - count)),
                )
                continue
            pct = (numdbs - count) / float(numdbs)
            if pct < 0.5:
                self.addIssue(
                    "too low percentage metadb on failure",
                    obj=dev,
                    text="Insufficient local metadbs if %s failed (%d%% left)"
                    % (dev, int(100 * pct)),
                )

    ##########################################################################
    def analyse(self):
        self.analyseMetadb()
        self.analyseLinux_mdstat()
        for md in self.metaList():
            if md not in self:
                self.Warning("md %s doesn't exist in data but in metaList" % md)
                continue
            self[md].analyse()
            self.inheritIssues(self[md])

    ##########################################################################
    def analyseLinux_mdstat_chunk(self, buff):
        for line in buff:
            if line.startswith("md"):
                bits = line.split()
                metadev = bits[0]
                for devbit in bits[4:]:
                    if "(F)" in devbit:
                        self.addIssue(
                            "failed device",
                            obj=metadev,
                            text="Failed metadev: %s" % line,
                        )


##########################################################################
# storageVolmanager ######################################################
##########################################################################


class storageVolmanager(explorerbase.ExplorerBase):

    """Representation of everything disksuite volume manager based on data
    from explorers
    """

    ##########################################################################

    def __init__(self, config, data={}):
        explorerbase.ExplorerBase.__init__(self, config)
        self.data = data
        self["_setmap"] = {}
        self.parse()

    ##########################################################################
    def didLookup(self, didpath, diskset=""):
        """Return the physical disk of the did specified
        hawk:/dev/did/rdsk/d21 -> [c3t0d0, c2t0d0]
        eagle:/dev/did/rdsk/d21s0 -> [c3t0d0s0, c2t0d0s0]
        """
        did = didpath
        did = did.replace("/dev/did/rdsk/", "")
        did = did.replace("/dev/did/dsk/", "")

        # Strip off servername
        did = did.split(":")[-1]

        if did in self["_didmap"]:
            for dev in self["_didmap"][did]:
                self["_setmap"][dev] = diskset
            return self["_didmap"][did]

        # Try it again without the slices, if any
        slice = did[-2:]
        did = did[:-2]
        if did in self["_didmap"]:
            for dev in self["_didmap"][did]:
                self["_setmap"][dev] = diskset
            return [p + slice for p in self["_didmap"][did]]

        return "unknown_%s" % didpath

    ##########################################################################
    def getDevDesc(self, dev):
        """Return a description of the metadev suitable for use in a
        mountpoint report"""

        ans = ""
        if dev not in self:
            self.Warning("getDevDesc: dev %s not found in data" % dev)
            return
        if "type" not in self[dev]:
            return ans
        if self[dev]["type"] == "concat":
            ans = "Concat: %s" % (", ".join(self[dev]["devices"]))
        elif self[dev]["type"] == "mirror":
            ans = "Submirrors: %s" % (", ".join(self[dev]["submirrors"]))
        elif self[dev]["type"] == "softpar":
            ans = "Softpartition of %s" % self[dev]["master"]
        elif self[dev]["type"] == "partition":
            ans = "Lone Slice: %s" % dev
        elif self[dev]["type"] == "raid":
            ans = "RAID: %s" % (", ".join(self[dev]["devices"]))
        elif self[dev]["type"] == "hotspare":
            ans = "HotSpare"
        elif self[dev]["type"] == "metadb":
            ans = "MetaDB"
        else:
            self.Warning("Unhandled devDesc() type=%s" % self[dev]["type"])
        return ans

    ##########################################################################
    def analyse(self, data):
        pass

    ##########################################################################
    def crossPopulateMetadbs(self, data):
        # Set the use of metadbs
        if "metadb" not in self:
            return
        devcounts = {}
        for mdb in self["metadb"]["copies"]:
            for dev in self[mdb]["devices"]:
                devcounts[dev] = devcounts.get(dev, 0) + 1
        for dev, count in devcounts.items():
            if dev not in data:
                self.Warning("Device %s has a metadb on it but doesn't exist" % dev)
                continue
            data[dev]["use"].add("metadb")
            data[dev]["name"] = "MetaDB (%d copies)" % count

    ##########################################################################
    def crossPopulateDid(self, data):
        """Tell the disks which did they belong to if they do"""
        if not "_didmap" in self:
            return
        for did in data["_didmap"]:
            for disk in data["_didmap"][did]:
                if disk in data:
                    data[disk]["did"] = did
                else:
                    self.Warning("DID %s disk %s doesn't exist" % (did, disk))

    ##########################################################################
    def crossPopulate(self, data):
        self.crossPopulateDid(data)
        self.crossPopulateMetadbs(data)

        # Match metadev/metadbs to their disks
        # data['c0t0d0s0']['partof']='d10'
        for k in self.keys():
            if "type" not in self[k]:
                continue
            slicelist = self[k]["devices"]
            for slice in slicelist:
                if slice in data:
                    data[slice]["partof"].add(k)
                    continue
                baseslice = slice.split("/")[-1]
                if baseslice in data:
                    data[baseslice]["partof"].add(k)
                    continue
                self.Warning("Unmatched md location %s" % slice)
                data[slice] = storage.Storage.initialDict(
                    {
                        "_type": "missing",
                        "missedby": k,
                        "missed_at": "crossPopulate - 1",
                    }
                )

        # Match use to their metadevs
        # data['d50']['use']='/export/home'
        for k in data.keys():
            if "_type" in data[k] and data[k]["_type"] == "filesystem":
                try:
                    device = data[k]["device"]
                except KeyError:
                    continue  # TODO
                    self.prettyPrint(fd=sys.stderr)
                    self.Fatal("k=%s %s" % (k, data[k]))
                if device in self:
                    data[device]["use"].add(k)
                    continue
                basedevice = device.split("/")[-1]
                if basedevice in self:
                    data[basedevice]["use"].add(k)
                    continue

        self.crossPopulateDiskset(data)
        self.crossPopulateProtection(data)
        self.crossPopulateHotspares(data)

        # If a metaslice is actually a submirror - redescribe it as such
        for k in data.keys():
            if "type" in data[k] and data[k]["type"] == "mirror":
                for sm in data[k]["submirrors"]:
                    if data[sm]["description"] == "Metaslice":
                        data[sm]["description"] = "Submirror"

        # Check for unused metadevices
        # Something clever should be done with these TODO
        badlist = set()
        for k in data.keys():
            if "_type" in data[k] and data[k]["_type"] == "disksuite":
                if "use" not in data[k] or not data[k]["use"]:
                    badlist.add(k)

    ##########################################################################
    def crossPopulateHotspares(self, data):
        """If a device is a hotspare it should have its use set appropriately"""
        for objname, obj in data.items():
            if "type" not in obj or obj["type"] != "hotspare":
                continue
            for dev in obj["devices"]:
                data[dev]["use"].add("hotspare")

    ##########################################################################
    def crossPopulateDiskset(self, data):
        # If a metadb/metadev has a diskset, then the partition it lives on
        # belongs to that diskset
        # And the disk itself also has to belong to that diskset
        for objname, obj in data.items():
            if "_type" not in obj or "diskset" not in obj:
                continue
            if obj["_type"] in ("metadb_copy", "disksuite"):
                for dev in obj["devices"]:
                    if dev in data:
                        data[dev]["diskset"] = obj["diskset"]
                        if "disk" in data[dev]:
                            disk = data[dev]["disk"]
                            data[disk]["diskset"] = obj["diskset"]
                        else:
                            self.Warning(
                                "Device %s has no disk associated with it" % dev
                            )
                    else:
                        self.Warning(
                            "Diskset %s %s lives on unknown disk %s"
                            % (obj["diskset"], obj["_type"], dev)
                        )
                        data[dev] = storage.Storage.initialDict(
                            {
                                "_type": "missing",
                                "missedby": "diskset %s %s %s"
                                % (obj["diskset"], obj["_type"], objname),
                                "missed_at": "crossPopulateDiskset",
                            }
                        )

    ##########################################################################
    def crossPopulateProtection(self, data):
        """If something is mirrored or part of a raid then the disks are
        regarded as protected as is what it is used for
        """
        for md in data.keys():
            if "_type" in data[md] and data[md]["_type"] == "disksuite":
                if data[md]["type"] == "mirror" and len(data[md]["submirrors"]) >= 2:
                    data[md]["protected"] = "Mirror"
                    for sm in data[md]["submirrors"]:
                        data[sm]["protected"] = "Mirror"
                elif data[md]["type"] == "raid":
                    data[md]["protected"] = "Raid"
                    for dev in data[md]["devices"]:
                        data[dev]["protected"] = "Raid"

    ##########################################################################
    def parseSolaris_scdidadm(self):
        """Parse the did configuration file for clusters and disksets
        You can have multiple disks on the same host in the same did device
            metaset mirroring
        You should always have multiple hosts in the same did device - that is
            the whole idea

        The resulting self.didmp is a dictionary that looks like:
            d10: ['c0t0d0s0', 'c1t0d0s0']
        """
        self["_didmap"] = {}
        self["_proxy_didmap"] = {}
        filename = "cluster/did/scdidadm-L.out"
        if not self.exists(filename):
            return
        didadm = self.open(filename)
        for line in didadm:
            bits = line.strip().split()
            instance, fullpath, fullname = bits
            path = fullpath.replace("/dev/rdsk/", "")
            path = path.split(":")[-1]  # Take off hostname
            name = fullname.replace("/dev/did/rdsk/", "")
            if name not in self:
                self["did/%s" % name] = storage.Storage.initialDict(
                    {
                        "_type": "did_disk",
                        "_origin": filename,
                        "description": "did disk",
                    }
                )
            if self.hostname in line:
                if name not in self["_didmap"]:
                    self["_didmap"][name] = []
                self["_didmap"][name].append(path)
                self["did/%s" % name]["contains"].add(path)
            else:
                if name not in self["_proxy_didmap"]:
                    self["_proxy_didmap"][name] = []
                self["_proxy_didmap"][name].append(path)

        # Hack to fill in slices
        for did in self["_didmap"]:
            for slice in [0, 2]:
                didslice = "did/%ss%d" % (did, slice)
                self[didslice] = storage.Storage.initialDict(
                    {
                        "_type": "did_slice",
                        "_origin": filename,
                        "description": "did slice",
                    }
                )
                for disk in self["_didmap"][did]:
                    self[didslice]["contains"].add("%ss%d" % (disk, slice))

    ##########################################################################
    def parseLinux_mdstat(self):
        if not self.exists("proc/mdstat"):
            return
        buff = []
        f = self.open("proc/mdstat")
        for line in f:
            line = line.strip()
            if line.startswith("Personalities"):
                continue
            if buff and not line:
                self.parseLinux_mdstat_chunk(buff)
                buff = []
                continue
            buff.append(line.strip())

        f.close()

    ##########################################################################
    def parseLinux_mdstat_chunk(self, buff):
        for line in buff:
            if line.startswith("md"):
                bits = line.split()
                metadev = bits[0]
                if metadev not in self:
                    self[metadev] = storage.Storage.initialDict(
                        {"_type": "metadev", "_origin": "mdstat"}
                    )
                # A colon is bits[1]
                status = bits[2]
                raidlev = bits[3]
                self["volmgt_metadevs"].append(metadev)
                if raidlev == "raid1":
                    self[metadev]["description"] = "LVM Mirror"
                    self[metadev]["submirrors"] = set()
                    self[metadev]["type"] = "mirror"
                    for submirror in bits[4:]:
                        submirror = submirror[: submirror.find("[")]
                        self[metadev]["submirrors"].add(submirror)
                elif raidlev == "raid5":
                    self[metadev]["description"] = "LVM RAID"
                    self[metadev]["protected"] = "RAID"
                    self[metadev]["type"] = "raid"
                else:
                    self.Fatal("Unhandled raidlev: %s" % raidlev)

                for devbit in bits[4:]:
                    dev = devbit[: devbit.find("[")]
                    self[metadev]["contains"].add(dev)

    ##########################################################################
    def parseLinux_lvs(self):
        """Understand the LVS output. The following is very useful:
            http://www.centos.org/docs/5/html/5.1/Cluster_Logical_Volume_Manager/report_object_selection.html

            Volume Labels are for mirrors, where there is a
            pseudo-layer between the volume group and the physical
            volume. This is my terminaology. I don't know what they
            are really called.

        Format 1 (with volume labels):
            LV               VG   Attr   LSize  Origin Snap%  Move Log        Copy%  Devices
            da02             vg00 mwi-ao 58.59G                    da02_mlog  100.00 da02_mimage_0(0),da02_mimage_1(0)
            [da02_mimage_0]  vg00 iwi-ao 58.59G                                      /dev/sde1(0)
            [da02_mimage_1]  vg00 iwi-ao 58.59G                                      /dev/sdd1(2048)
            [da02_mlog]      vg00 lwi-ao  4.00M                                      /dev/sdc1(1)

        Format 2:
            LV       VG         Attr   LSize   Origin Snap%  Move Log Copy%  Convert Devices
            LogVol00 VolGroup00 -wi-ao   1.00G                                       /dev/sda2(0)
            LogVol01 VolGroup00 -wi-ao  15.62G                                       /dev/sda2(3868)
            LogVol03 VolGroup00 -wi-ao   9.78G                                       /dev/sda2(3555)
        """
        lvs_file = "sos_commands/devicemapper/lvs_-a_-o_devices"
        if not self.exists(lvs_file):
            return
        volabels = {}
        buff = []
        f = self.open(lvs_file)
        for line in f:
            line = line.strip()
            if "LSize" in line:
                continue
            if "Found duplicate" in line:
                continue
            if "No volume groups found" in line:
                return
            if "invalid option" in line:
                return
            # Not a failure - device hasn't been removed
            if "read failed" in line:
                continue
            buff.append(line)
            bits = line.split()
            lv = bits[0]
            lvlabel = "LV:%s" % lv
            lvFlag = True
            vg = bits[1]
            vglabel = "VG:%s" % vg
            attrs = bits[2]
            devices = bits[-1].split(",")
            if lv.startswith("["):
                lvFlag = False
                vl = lv[1:-1]  # Strip []
                if vl in volabels:
                    lv = volabels[vl]
                    self[vl] = storage.Storage.initialDict(
                        {
                            "_type": "logvol",
                            "description": "LVM Volume Label",
                            "_origin": lvs_file,
                        }
                    )
                else:
                    # Find the assoicate log vol with the log
                    if attrs.startswith("l"):  # Logs
                        for ln in buff:
                            if vl in ln:
                                lv = ln.split()[0]
                                break
                        self[vl] = storage.Storage.initialDict(
                            {
                                "_type": "logvol",
                                "description": "LVM Mirror Log Volume",
                                "_origin": lvs_file,
                            }
                        )
                self[vl]["partof"].add(vg)
            elif lvlabel not in self:
                self[lvlabel] = storage.Storage.initialDict(
                    {
                        "_type": "logvol",
                        "description": "LVM Logical Volume",
                        "_origin": lvs_file,
                    }
                )
                if attrs.startswith("m"):
                    # self[lv]['type']='mirror'
                    self[lv]["protected"] = "LVM Mirror"
                elif attrs.startswith("-"):
                    # self[lv]['type']='softpar'
                    pass
                else:
                    self.Fatal("Unhandled LVM type %s" % attrs)
            self[lvlabel]["contains"].add(vglabel)
            self[lvlabel]["aliases"] = set(["%s-%s" % (vg, lv)])
            if vglabel not in self:
                self[vglabel] = storage.Storage.initialDict(
                    {
                        "_type": "volgroup",
                        "description": "LVM Volume Group",
                        "_origin": lvs_file,
                    }
                )

            for device in devices:
                device = self.sanitiseDevice(device)
                if device.endswith(")"):
                    device = device[: device.find("(")]
                    # self[vglabel]['contains'].add(device)
                if lvFlag:
                    volabels[device] = lv
            self[vglabel]["partof"].add(lvlabel)
        f.close()
        for k in self.keys():  # ZD
            print("# %s\t%s" % (k, self[k]))

    ##########################################################################
    def parse(self):
        self["volmgt_metadevs"] = []
        if self.config["explorertype"] == "solaris":
            self.parseSolaris_scdidadm()
            self.parseAllMetastatP()
            self.parseFullMetastat()
            self.parseAllMetaDb()
            for metadev in self.metaList():
                if metadev not in self:
                    self.Warning(
                        "Couldn't find metadev %s even though it is in metaList"
                        % metadev
                    )
                    continue
                self[metadev]["devdesc"] = self.getDevDesc(metadev)
        if self.config["explorertype"] == "linux":
            self.parseLinux_lvs()
            self.parseLinux_mdstat()

    ##########################################################################
    def parseAllMetaDb(self):
        self.metadbcopy = 0
        self["metadb"] = storage.Storage.initialDict(
            {
                "_type": "metadb",
                "copies": set(),
                "diskset_copies": set(),
                "description": " ",  # Deliberately single space
                "type": "metadb",
                "use": set(["metadb"]),
            }
        )
        files = self.allFiles("metadb*.out")
        for filename in files:
            try:
                self.parseMetaDb(filename)
            except:
                self.Warning("Failure on parseMetaDb(filename=%s)" % filename)
                raise
        self.crossMatch()

    ##########################################################################
    def whatDiskset(self, filename):
        """Return the diskset that the file belongs to, or the empty string
        if it doesn't belong to any
        """
        f = os.path.basename(filename)
        m = re.match("(?P<cmd>.*)\.(?P<diskset>.*)\.out", f)
        if m:
            return m.group("diskset")
        else:
            return ""

    ##########################################################################
    def parseMetadbProxy(self, filename):
        """Handle a cluster situation where another host knows how the disks on
        this host are layed out

        This has a lock around it because two hosts can be mutually dependent if
        they have two disks sets and each is a master of one - without the lock
        it just ends up infinitely recursing - bail out and admit failure
        """
        if not self.createLock(filename):
            self.Warning("Can't process %s - already locked" % filename)
            return

        proxyhost = None
        diskset = self.whatDiskset(filename)
        f = self.open(filename)
        for line in f:
            line = line.strip()
            if line.startswith("Proxy"):
                proxyhost = line.split(":")[-1].strip()
        f.close()

        # Now get the details from the proxyhost
        foreign = storage.Storage(proxyhost)
        if "diskset_copies" not in foreign["metadb"]:
            self.Warning("No diskset_copies found on %s" % proxyhost)
        else:
            for metadb in foreign["metadb"]["diskset_copies"]:
                if "did_dev" not in foreign[metadb]:
                    self.Warning(
                        "Couldn't find the did_dev in foreign metadb %s from host %s"
                        % (metadb, proxyhost)
                    )
                    break
                did_dev = foreign[metadb]["did_dev"]
                didbit = did_dev.replace("did/", "")
                diddev = didbit[:-2]
                didslice = didbit[-2:]
                if diddev in foreign["_proxy_didmap"]:
                    for dd in foreign["_proxy_didmap"][diddev]:
                        localdevice = "%s%s" % (dd, didslice)
                        copyname = self.addMetadb(
                            localdevice,
                            {
                                "flags": foreign[metadb]["flags"],
                                "diskset": diskset,
                                "foreign": proxyhost,
                                "did_dev": dd,
                            },
                        )
                        self["metadb"]["diskset_copies"].add(copyname)
        self.releaseLock(filename)

    ##########################################################################
    def parseMetaDb(self, filename):
        """Analyse metadb output"""
        diskset = self.whatDiskset(filename)
        f = self.open(filename)
        for line in f:
            line = line.strip()
            if line.startswith("Proxy command"):
                # self.parseMetadbProxy(filename)
                continue
            if self.lineSkipper(
                line,
                start=["rpc"],
                middle=[
                    "not owner of metadevice",
                    "flags",
                    "Miscellaneous tli error",
                    "must be owner of the set",
                ],
            ):
                continue
            bits = line.split()

            if "did" in bits[-1]:
                devlist = [self.sanitiseDevice(d) for d in self.didLookup(bits[-1])]
            else:
                devlist = [self.sanitiseDevice(bits[-1])]

            for device in devlist:
                copyname = self.addMetadb(
                    device,
                    {
                        "first_block": bits[-3],
                        "blockcount": bits[-2],
                        "flags": "".join(bits[:-3]),
                    },
                )
                self[copyname]["_origin"] = filename
                if diskset:
                    self[copyname]["diskset"] = diskset
                    self[copyname]["did_dev"] = self.sanitiseDevice(bits[-1])
                    self["metadb"]["diskset_copies"].add(copyname)
                else:
                    self["metadb"]["contains"].add(copyname)
                    self["metadb"]["copies"].add(copyname)
        f.close()

    ##########################################################################
    def addMetadb(self, device, opts={}):
        copyname = "metadb_%d" % self.metadbcopy
        self.metadbcopy += 1

        self[copyname] = storage.Storage.initialDict(
            {
                "_type": "metadb_copy",
                "type": "metadb",
                "description": "MetaDB instance",
                "partof": set(["metadb"]),
                "use": set(["metadb"]),
            }
        )
        self[copyname].update(opts)
        self[copyname]["contains"] = set([device])
        return copyname

    ##########################################################################
    def parseFullMetastat(self):
        for filename in self.allFiles("metastat.out"):
            metadev = -1
            for line in self.open(filename):
                line = line.rstrip()
                if line.startswith("d"):
                    metadev = line.split(":")[0]
                    self["volmgt_metadevs"].append(metadev)
                if line.find("Maintenance") >= 0:
                    if line.find("State") >= 0 or line.find("Invoke") >= 0:
                        continue

    ##########################################################################
    def allFiles(self, filedesc):
        """Return all files that match the description no matter
        which path they are in
        """
        files = self.glob("disks/svm/%s" % filedesc)
        if not files:
            files = self.glob("disks/sds/%s" % filedesc)
        return files

    ##########################################################################
    def parseAllMetastatP(self):
        files = self.allFiles("metastat-p*.out")
        for filename in files:
            self.parseMetastatP(filename)
        self.crossMatch()

    ##########################################################################
    def createLock(self, filename):
        lockfile = "%s.lock" % filename
        if os.path.exists(lockfile):
            f = open(lockfile)
            pid = f.readline().strip()
            f.close()
            if int(pid) != os.getpid():
                self.Warning(
                    "Releasing stale lock from pid %s (Out PID=%d)" % (pid, os.getpid())
                )
                self.releaseLock(filename)
            else:
                return False
        f = open(lockfile, "w")
        f.write("%s\n" % os.getpid())
        f.close()
        return True

    ##########################################################################
    def releaseLock(self, filename):
        lockfile = "%s.lock" % filename
        os.unlink(lockfile)

    ##########################################################################
    def parseMetastatProxy(self, filename):
        """Handle a cluster situation where another host knows how the disks on
        this host are layed out

        This has a lock around it because two hosts can be mutually dependent if
        they have two disks sets and each is a master of one - without the lock
        it just ends up infinitely recursing - bail out and admit failure
        """

        if not self.createLock(filename):
            self.Warning("Can't process %s - already locked" % filename)
            return

        proxyhost = None
        diskset = self.whatDiskset(filename)
        f = self.open(filename)
        for line in f:
            line = line.strip()
            if line.startswith("Proxy"):
                proxyhost = line.split(":")[-1].strip()
        f.close()

        # Now get the details from the proxyhost
        foreign = storage.Storage(proxyhost)

        for obj in foreign["_diskset_%s" % diskset]:
            for did in foreign[obj]["did_dev"]:
                diddisk = did[:-2]
                didslice = did[-2:]
                if diddisk not in foreign["_proxy_didmap"]:
                    self.Warning(
                        "Couldn't find %s in %s' didmap" % (diddisk, proxyhost)
                    )
                    continue
                localdevs = foreign["_proxy_didmap"][diddisk]
                for ld in localdevs:
                    localslice = "%s%s" % (ld, didslice)

        self.releaseLock(filename)

    ##########################################################################
    def parseMetastatP(self, filename):
        """Parse the metastat -p output which is about configuration not
        state
        """
        f = self.open(filename)
        diskset = self.whatDiskset(filename)
        if diskset:
            self["_diskset_%s" % diskset] = set()
        subline = ""
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "Proxy command" in line:
                # self.parseMetastatProxy(filename)
                continue
            if "no such set" in line:
                continue
            if subline:  # Handle lines split over multiple lines
                line = "%s %s" % (subline, line)
                subline = ""
            if line.endswith("\\"):
                subline = line[:-1]
                continue
            if self.lineSkipper(
                line,
                start=["rpc failure"],
                middle=["Miscellaneous tli error", "must be owner of the set"],
            ):
                continue
            bits = line.split()
            metadevname = bits[0]
            try:
                oper = bits[1]
            except IndexError:  # Occassionally weird stuff exists
                continue
            self[metadevname] = storage.Storage.initialDict(
                {"_type": "disksuite", "_origin": filename}
            )
            metadev = self[metadevname]
            if diskset:
                self["_diskset_%s" % diskset].add(metadevname)
            if metadevname.startswith("hsp") or metadevname.find("/hsp") >= 0:
                self.parseHotspare(metadev, bits[1:], diskset)
            elif oper == "-m":  # Mirror
                self.parseMirror(metadev, bits[2:], diskset)
            elif oper == "-p":  # Soft partition
                self.parseSoftpar(metadev, bits[2:], diskset)
            elif oper == "-r":  # RAID
                self.parseRaid(metadev, bits[2:], diskset)
            elif oper[0] in string.digits:  # Concat/Stripe
                self.parseConcat(metadev, bits[1:], diskset)
            else:
                self.Warning("Unhandled metadev type %s" % oper)
                self.Warning("Line=%s" % line)

        f.close()

    ##########################################################################
    def parseHotspare(self, metadev, bits, diskset):
        metadev["type"] = "hotspare"
        if diskset:
            ans = set()
            for d in bits:
                ans.update(self.didLookup(d, diskset))
        else:
            pass
        metadev["description"] = "Hotspare"

    ##########################################################################
    def parseMirror(self, metadev, bits, diskset):
        # d80 -m d81 d82 1 - config line
        # d81 d82 1 - is passed here
        metadev["type"] = "mirror"
        metadev["submirrors"] = bits[:-1]
        metadev["contains"] = set(bits[:-1])
        if len(metadev["submirrors"]) != 2:
            mirdesc = "%d-way " % (len(metadev["submirrors"]))
        else:
            mirdesc = ""
        metadev["description"] = "%sMirror" % mirdesc

    ##########################################################################
    def metaList(self):
        """Return a list of metadevices"""
        return self["volmgt_metadevs"]

    ##########################################################################
    def crossMatch(self):
        """Match subs etc with masters"""
        for md in self.metaList():
            if md not in self:
                self.Warning("md=%s in metaList but not found in data" % md)
                continue
            if md == "metadb":
                continue
            if self[md]["type"] == "partition":
                continue
            if self[md]["type"] == "mirror":
                for sm in self[md]["submirrors"]:
                    self[sm]["partof"].add(md)

    ##########################################################################
    def parseSoftpar(self, metadev, bits, diskset):
        """Analyse soft partitions in a metastat output
        # d20 -p d15 -o 1 -b 10485760
        """
        metadev["master"] = bits[0]
        metadev["contains"].add(bits[0])
        metadev["type"] = "softpar"
        metadev["description"] = "Soft Partition"
        metadev["extents"] = []
        skipnext = False
        offset = 0
        size = 0
        for idx in range(len(bits[1:])):
            b = bits[idx]
            if skipnext:
                skipnext = False
                continue
            if b == "-o":
                offset = int(bits[idx + 1])
                skipnext = True
            if b == "-b":
                size = int(bits[idx + 1])
                skipnext = True
                metadev["extents"].append((offset, size))

    ##########################################################################
    def parseConcat(self, metadev, bits, diskset):
        """Analyse concat/strip in a metastat output"""
        bits = self.stripExtrabits(bits)
        if bits[0] == "1" and bits[1] == "1":
            metadev["type"] = "partition"
            metadev["description"] = "Metaslice"
        else:
            metadev["type"] = "concat"
            if bits[0] == "1":
                metadev["description"] = "%s-Way Concat" % bits[1]
            elif bits[1] == "1":
                metadev["description"] = "%s-Way Stripe" % bits[0]
            else:
                metadev["description"] = "%s-Way Concat of %s-Way Stripe" % (
                    bits[1],
                    bits[0],
                )
        metadev["did_dev"] = set()

        for bit in bits[2:]:
            try:  # Handle num stripes in concat list
                int(bit)
            except ValueError:
                pass
            else:
                continue
            bit = bit.replace("/dev/dsk/", "")
            if diskset:
                metadev["diskset"] = diskset
                slicelist = self.didLookup(bit, diskset)
                metadev["did_dev"].add(bit)
            else:
                slicelist = [bit]
            metadev["contains"].update(slicelist)

    ##########################################################################
    def stripExtrabits(self, bits):
        """Remove things like interleave and hotspare options"""
        # Remove any interleave data
        if "-i" in bits:
            interleave = bits[bits.index("-i") + 1]
            bits.remove("-i")
            bits.remove(interleave)
        # Remove any  hotspares - we don't care who they are associated with
        if "-h" in bits:
            hsp = bits[bits.index("-h") + 1]
            bits.remove("-h")
            bits.remove(hsp)
        return bits

    ##########################################################################
    def describer(self, obj, data):
        return "volmanager"

    ##########################################################################
    def parseRaid(self, metadev, bits, diskset):
        """Analyse raid definitions in a metastat output"""
        metadev["type"] = "raid"
        metadev["description"] = "RAID5"
        skipnext = False
        for idx in range(len(bits)):
            b = bits[idx]
            if skipnext:
                skipnext = False
                continue
            if b == "-k":  # Don't clear
                pass
            elif b == "-o":  # Original columns
                skipnext = True
            elif b == "-i":  # interlace
                metadev["interlace"] = bits[idx + 1]
                skipnext = True
            elif b == "-h":  # hotspare
                metadev["hotspare"] = bits[idx + 1]
                skipnext = True
            elif b.startswith("c"):
                metadev["contains"].add(b)
            else:
                self.Fatal("Unknown raid line: %s" % b)


# EOF
