""" Understand zone details"""

# Written by Dougal Scott <dwagon@pobox.com>
# $Id: zones.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/zones.py $

import re
import explorer.explorerbase


##########################################################################
# Zone ###################################################################
##########################################################################
class Zone(explorerbase.ExplorerBase):
    """TODO"""

    ##########################################################################
    def __init__(self, config, zonename):
        explorerbase.ExplorerBase.__init__(self, config)
        self.objname = zonename
        self["zhostname"] = "unknown"
        try:
            self.parse_zonecfg()
            self.parse_zone_sysconfig()
            self.parse_ifconfig()
        except UserWarning as err:
            self.warning(err)

    ##########################################################################
    def parse_ifconfig(self):
        """TODO"""
        ifc = f"zones/{self.name()}/sysconfig/ifconfig-a.out"
        if not self.exists(ifc):
            return
        self["ipaddrs"] = []
        infh = self.open(ifc)
        for line in infh:
            if "inet" in line:
                matchobj = re.search(r"inet (?P<ipaddr>\S+) n", line)
                if matchobj:
                    if "127.0.0.1" != matchobj.group("ipaddr"):
                        self["ipaddrs"].append(matchobj.group("ipaddr"))
                else:
                    self.warning(f"No match: {line}")
        infh.close()

    ##########################################################################
    def parse_zone_sysconfig(self):
        """TODO"""
        unam = f"zones/{self.name()}/sysconfig/uname-a.out"
        if self.exists(unam):
            infh = self.open(unam)
            data = infh.readline()
            infh.close()
            if data:
                self["zhostname"] = data.split()[1]
                return

    ##########################################################################
    def analyse(self):
        """TODO"""

    ##########################################################################
    def parse_zonecfg(self):
        """TODO"""
        infh = self.open(f"sysconfig/zonecfg-z-{self.name()}-export.out")
        for line in infh:
            line = line.strip()
            if line.startswith("set address"):
                matchobj = re.search(r"set address=(?P<ipaddr>[0-9\.]*)(.*)", line)
                if "ipaddr" not in self:
                    self["ipaddr"] = []
                self["ipaddr"].append(matchobj.group("ipaddr"))
            if line.startswith("set physical"):
                self["physical"] = line.split("=")[1]
            if line.startswith("set autoboot"):
                self["autoboot"] = line.split("=")[1]
        infh.close()


##########################################################################
# Zones ##################################################################
##########################################################################
class Zones(explorerbase.ExplorerBase):
    """Understand explorer output with respect to zones"""

    ##########################################################################
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        if not self.exists("zones"):
            return
        try:
            self.parse_zones()
        except UserWarning as err:
            self.warning(err)
            return

    ##########################################################################
    def parse_zones(self):
        """TODO"""
        infh = self.open("etc/zones/index")
        for line in infh:
            if line.startswith("#"):
                continue
            bits = line.strip().split(":")
            if bits[0] == "global":
                continue
            zonename = bits[0]
            zone = Zone(self.config, zonename)
            zone["status"] = bits[1]
            if zone["status"] != "installed":
                self.addConcern(
                    "status",
                    obj=zonename,
                    text=f"Zone {zonename} is not operational status={zone['status']}",
                )
            zone["path"] = bits[2]
            self[zonename] = zone
        infh.close()

    ##########################################################################
    def zone_names(self):
        """TODO"""
        return sorted(self.data.keys())

    ##########################################################################
    def zone_list(self):
        """TODO"""
        return [self[zone] for zone in self.zone_names()]

    ##########################################################################
    def analyse(self):
        """TODO"""
        for zone in self.zone_list():
            zone.analyse()
            self.inheritIssues(zone)


# EOF
