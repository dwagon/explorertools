#!/usr/bin/env python
#
# Script to understand se3k disk array details
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: se3k.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/se3k.py $

import os
import re
import string
import explorer.explorerbase


##########################################################################
# storedge ###############################################################
##########################################################################
class Storedge(explorerbase.ExplorerBase):
    ##########################################################################
    def __init__(self, config, arrayname):
        explorerbase.ExplorerBase.__init__(self, config)
        self.objname = arrayname
        self["disks"] = {}
        self["hwimage"] = ""
        self["logicaldrives"] = {}
        self.parseShowDisks()
        self.parseShowConfiguration()
        self.parseShowEnclosureStatus()
        self.parseShowLogicalDrives()
        self.getHwimage()

    ##########################################################################
    def getHwimage(self):
        tbl = {
            "SUN StorEdge 3310": "3310.png",
            "SUN StorEdge 3510": "3510.png",
            "SUN StorEdge 3511": "3511.png",
        }
        if self["hardware"] in tbl:
            self["hwimage"] = tbl[self["hardware"]]

    ##########################################################################
    def parseShowConfiguration(self):
        fname = "disks/se3k/sccli/%s/show_configuration.out" % self.name()
        if not self.exists(fname):
            return
        f = self.open(fname)
        mode = None
        for line in f:
            try:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("* FRUs"):
                    mode = "fru"
                    continue
                if line.startswith("* enclosure-status"):
                    mode = "status"
                    continue
                if line.startswith("Enclosure Component Status:"):
                    mode = "component"
                    continue
                if mode == "fru":
                    if line.startswith("Name:"):
                        fru = line.split(":")[1]
                    if line.startswith("FRU Status:"):
                        status = line.split(":")[1].strip()
                        if status != "OK":
                            self.addIssue(
                                "SE3k_FRU",
                                obj="%s %s" % (self.name(), fru),
                                text="FRU (%s) %s has status %s"
                                % (self.name(), fru, status),
                            )
                if mode == "status":
                    if line.startswith("----") or line.startswith("Id"):
                        continue
                    if line.split()[-1].strip() != "OK":
                        self.addIssue(
                            "SE3k_Enclosure",
                            obj="%s" % self.name(),
                            text="Enclosure (%s) has status %s"
                            % (self.name(), line.split()[-1]),
                        )
                if mode == "component":
                    if (
                        line.startswith("----")
                        or line.startswith("Type")
                        or line.startswith("Enclosure SCSI")
                    ):
                        continue
                    bits = line.split()
                    status = bits[2].strip()
                    component = " ".join(bits[0:2])
                    if status not in ("OK", "Unknown"):
                        self.addIssue(
                            "SE3k_Component",
                            obj="%s %s" % (self.name(), component),
                            text="Component %s has status %s" % (component, status),
                        )
            except Exception as exc:
                self.warning("Parser failure on %s: %s: %s" % (fname, line, str(exc)))
                raise

    ##########################################################################
    def parseShowLogicalDrives(self):
        fname = "disks/se3k/sccli/%s/show_logical-drives.out" % self.name()
        if not self.exists(fname):
            return
        f = self.open(fname)
        for line in f:
            line = line.strip()
            if line.startswith("ld"):
                bits = line.split()
                self["logicaldrives"][bits[0]] = {
                    "size": bits[2],
                    "assign": bits[3],
                    "type": bits[4],
                    "disks": bits[5],
                    "spare": bits[6],
                    "failed": bits[7],
                    "status": bits[8],
                }
                if bits[8] != "Good":
                    self.addIssue(
                        "logical",
                        obj="%s %s" % (self.name(), bits[0]),
                        text="Logical Drive (%s) %s has status %s"
                        % (self["controller"], bits[0], bits[8]),
                    )
        f.close()

    ##########################################################################
    def parseShowEnclosureStatus(self):
        if not self.exists(
            "disks/se3k/sccli/%s/show_enclosure-status.out" % self.name()
        ):
            return
        f = self.open("disks/se3k/sccli/%s/show_enclosure-status.out" % self.name())
        header = ""
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("sccli"):
                continue
            if line.startswith("Ch"):
                continue
            if line.startswith("Type"):
                header = line
                continue
            if line.startswith("Enclosure"):
                continue
            if line.startswith("--------"):
                continue
            if line[0] in string.digits:
                continue
            bits = line.split()
            if bits[2] not in ("OK", "Unknown"):
                self.addIssue(
                    "component",
                    obj="%s %s" % (bits[0], bits[1]),
                    text="%s\n%s" % (header, line),
                )
        f.close()

    ##########################################################################
    def getDetails(self, line):
        m = re.search(
            r"sccli: selected device /dev/(rdsk|es)/(?P<device>\S+) \[(?P<hardware>.*) (?P<serial>SN#.*)\]",
            line,
        )
        if m:
            self["controller"] = m.group("device")
            self["hardware"] = m.group("hardware")
            self["serial"] = m.group("serial")
        elif "device not supported" in line:
            return
        else:
            self.fatal("Unknown se3k details: %s" % line)

    ##########################################################################
    def analyse(self):
        pass

    ##########################################################################
    def parseShowDisks(self):
        f = self.open("disks/se3k/sccli/%s/show_disks.out" % self.name())
        for line in f:
            if line.startswith("sccli"):
                self.getDetails(line)
                continue
            if line.startswith("Ch"):
                continue
            if line.startswith("-----"):
                continue
            if line.strip().startswith("S/N"):
                continue
            if line.strip().startswith("WWNN"):
                continue
            bits = line.strip().split()
            id = bits[1]
            size = bits[2]
            status = bits[5]
            if status not in ("ONLINE", "STAND-BY"):
                self.addIssue(
                    "disk",
                    obj=id,
                    text="Array %s-%s disk %s has status %s"
                    % (self.name(), self["controller"], id, status),
                )
            self["disks"][id] = {"size": size, "status": status}
        f.close()


##########################################################################
# se3k ###################################################################
##########################################################################


class Se3k(explorerbase.ExplorerBase):

    """Understand explorer output with respect to se3k disk arrays"""

    ##########################################################################

    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        if not self.exists("disks/se3k/rev"):
            return
        for arr in self.glob("disks/se3k/sccli/*"):
            array = os.path.basename(arr)
            self[array] = Storedge(config, array)
            for i in self[array].issues:
                self.addIssue(i)

    ##########################################################################
    def analyse(self):
        for arr in self.arrayList():
            arr.analyse()
            self.inheritIssues(arr)

    ##########################################################################
    def arrayList(self):
        return sorted([self[a] for a in self.keys()])


# EOF
