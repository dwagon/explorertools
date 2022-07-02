#!/usr/local/bin/python
"""
# Script to understand network card details
"""
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: nic.py 4430 2013-02-27 07:38:20Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/nic.py $

import re
import explorerbase
import kstat

_cidrmap = {}


##########################################################################
# Nic ####################################################################
##########################################################################
class Nic(explorerbase.ExplorerBase):
    """ Network interface cards """
    ##########################################################################
    def __init__(self, config, nicname, dev, inst):
        """ TODO """
        explorerbase.ExplorerBase.__init__(self, config)
        self.objname = nicname
        self["interfaces"] = {}
        self["dev"] = dev
        self["inst"] = inst
        self["link_speed"] = ""
        self["link_duplex"] = ""
        self["link_status"] = ""
        self["used"] = False
        if self.config["explorertype"] == "solaris":
            self.parse_solaris()
        elif self.config["explorertype"] == "linux":
            self.parse_linux()

    ##########################################################################
    def parse_linux(self):
        """ TODO """
        try:
            self.parse_linux_ethtool()
        except UserWarning as err:
            self.Warning(err)

    ##########################################################################
    def parse_solaris(self):
        """ TODO """
        self.parse_ndd()

    ##########################################################################
    def parse_linux_ethtool(self):
        """Parse the ethtool output for linux boxes"""
        infh = self.open("sos_commands/networking/ethtool_{self.name()}")
        for line in infh:
            line = line.strip()
            if "Duplex:" in line and "Unknown" not in line:
                self["link_duplex"] = line[line.find(":") + 1:].lower().strip()
            if "Speed" in line and "Unknown" not in line:
                self["link_speed"] = line[line.find(":") + 1:].lower()
        infh.close()

    ##########################################################################
    def post(self):
        """ TODO """
        if "used" not in self:
            self["used"] = False
        for iface in self["interfaces"]:
            self["interfaces"][iface]["cidr"] = self.get_cidr(self["interfaces"][iface])
            self["interfaces"][iface]["network"] = self.get_network(
                self["interfaces"][iface]
            )
            if self["interfaces"][iface]["network"]:
                self["used"] = True

    ##########################################################################
    def analyse(self):
        """ TODO """
        if "used" in self and not self["used"]:
            return
        if "half" in self["link_duplex"] and "normal" not in self["link_duplex"]:
            self.addConcern("duplex", obj=self.objname, text="set to half-duplex")
        for iface in self["interfaces"]:
            if "flags" in self["interfaces"][iface]:
                if "UP" not in self["interfaces"][iface]["flags"]:
                    if "IPv6" in self["interfaces"][iface]["flags"] and iface == "lo0":
                        pass
                    else:
                        self.addConcern("down", obj=self.objname, text="interface down")

    ##########################################################################
    def parse_ndd(self):
        """Parse the ndd results
        Then interpret them into something approaching standards
        link_speed - speed in mbits
        link_duplex - full or half
        link_status - up or down
        """
        nic = re.sub(
            r"(?P<nicname>\D+)(?P<inst>\d+)", r"\g<nicname>.\g<inst>", self.name()
        )
        filelist = self.glob(f"netinfo/ndd/{nic}/*.out")
        for nddfile in filelist:
            if nddfile.endswith("list.out"):
                continue
            infh = self.open(nddfile)
            line = infh.readline()
            infh.close()
            self["ndd_%s" % self.cmdfilename(nddfile)] = line.strip()

        # Every smegging nic type does it differently - thanks sun
        if not self.is_virtual():
            self.get_link_duplex()
            self.get_link_speed()
            self.get_link_status()
            if self["used"] and "link_duplex" in self and self["link_duplex"] == "half":
                self.addConcern("duplex", obj=self.objname, text="set to half-duplex")
            if self["used"] and "link_status" in self and self["link_duplex"] == "down":
                self.addConcern("down", obj=self.objname, text="interface down")

    ##########################################################################
    def get_link_status(self):
        """ TODO """
        if "ndd_link_status" in self:
            self["link_status"] = {"0": "down", "1": "up"}[self["ndd_link_status"]]

    ##########################################################################
    def get_link_speed(self):
        """ TODO """
        if "ndd_link_speed" in self:
            if self["ndd_link_speed"] == "1000":
                self["link_speed"] = 1000
            elif self["ndd_link_speed"] == "100":
                self["link_speed"] = 100
            elif self["ndd_link_speed"] == "10":
                self["link_speed"] = 10
            elif self["ndd_link_speed"] == "1":
                pass  # TODO
            elif self["ndd_link_speed"] == "0":
                pass  # TODO
            else:
                self.Warning(f"Unhandled ndd_link_speed={self['ndd_link_speed']}")

    ##########################################################################
    def get_kstat_duplex(self):
        """Don't use the kstat function - this is way faster - we just want
        something very specific
        """
        if not self.exists("netinfo/kstat-p.out"):
            return "0"
        infh = self.open("netinfo/kstat-p.out")
        for line in infh:
            if "link_duplex" not in line:
                continue
            if not line.startswith(self["dev"]):
                continue
            if (
                ":%s:" % self["inst"] not in line
                and "%s%s" % (self["dev"], self["inst"]) not in line
            ):
                continue
            infh.close()
            return line.split()[-1]
        infh.close()
        return "-1"

    ##########################################################################
    def get_link_duplex(self):
        """ TODO """
        if "ndd_link_mode" in self:
            if self["ndd_link_mode"] == "0":
                self["link_duplex"] = "half"
                return
            if self["ndd_link_mode"] == "1":
                self["link_duplex"] = "full"
                return
            if self["ndd_link_mode"] == "2":
                self["link_duplex"] = "full"
                return
            self.Warning(f"Unhandled ndd_link_mode={self['ndd_link_mode']}")

        if self["dev"] in ("bge", "ixge", "nge"):
            try:
                self["link_duplex"] = {"0": "unknown", "1": "half", "2": "full"}[
                    self["ndd_link_duplex"]
                ]
            except KeyError:
                self["link_duplex"] = "unknown"
        elif self["dev"] in ("ce", "ge"):
            self["link_duplex"] = {
                "-1": "error",
                "0": "unknown",
                "1": "half",
                "2": "full",
            }[self.get_kstat_duplex()]
        elif self["dev"] == "dmfe":
            # Duplex 1 means full; except if patch 116561-04 has been applied then it means half
            # What the hell were Sun thinking?
            pass
        elif self["dev"] in ("lo", "lpfc", "sppp", "aggr", "jnet", "dman"):
            pass
        elif self["dev"] == "eri":  # Should be covered by ndd
            self["link_duplex"] = {
                "-1": "error",
                "0": "unknown",
                "1": "half",
                "2": "full",
            }[self.get_kstat_duplex()]
        elif self["dev"] == "qfe":  # Should be covered by ndd
            self["link_duplex"] = {
                "-1": "error",
                "0": "unknown",
                "1": "half",
                "2": "full",
            }[self.get_kstat_duplex()]
        elif self["dev"] == "ipge":
            self["link_duplex"] = {
                "-1": "error",
                "0": "unknown",
                "1": "half",
                "2": "full",
            }[self.get_kstat_duplex()]
        elif self["dev"] == "e1000g":
            self["link_duplex"] = {
                "-1": "error",
                "0": "unknown",
                "1": "half",
                "2": "full",
            }[self.get_kstat_duplex()]
        elif self["dev"] == "nxge":
            # Comes out as string not a number
            self["link_duplex"] = self.get_kstat_duplex()
            # self.Warning("No duplex info for nxge networks - need dladm output")
        elif self["dev"] == "le":
            self["link_duplex"] = "half (normal)"
        elif self["dev"] == "jnic146x":
            self["link_duplex"] = "full"
        elif self["dev"] == "ixgbe":
            self["link_duplex"] = {
                "-1": "error",
                "0": "unknown",
                "1": "half",
                "2": "full",
            }[self.get_kstat_duplex()]
        else:
            if "ndd_link_duplex" in self:
                self["link_duplex"] = {
                    "-1": "unknown",
                    "0": "half",
                    "1": "half or full",
                    "2": "full",
                }[self["ndd_link_duplex"]]
            else:
                self.Warning(f"Unhandled nic: {self['dev']} in get_link_duplex()")

    ##########################################################################
    def get_network(self, dct):
        """1.2.3.4 / ffffff00 -> 1.2.3.0/24"""
        if "netmask" not in dct:  # ipv6 iface
            return "No netmask"
        try:
            nmsk = int(dct["netmask"], 16)
        except ValueError:
            quads = dct["netmask"].split(".")
            nmsk = int(quads[3]) + 256 * (
                int(quads[2]) + 256 * (int(quads[1]) + 256 * int(quads[0]))
            )
        order = 3
        ip = 0
        for quad in dct["ipaddr"].split("."):
            ip += int(quad) << (8 * order)
            order -= 1
        network = ip & nmsk
        netstr = ""
        for hexmap, shft in [("ff000000", 24), ("ff0000", 16), ("ff00", 8), ("ff", 0)]:
            netstr += "%d." % ((network & int(hexmap, 16)) >> shft)
        return netstr[:-1]

    ##########################################################################
    def add_interface(self, ifname):
        """ TODO """
        self["interfaces"][ifname] = {
            "flags": "",
        }
        return self["interfaces"][ifname]

    ##########################################################################
    def is_virtual(self):
        """ TODO """
        if ":" in self.objname:
            return True
        if "vlan" in self:
            return True
        if self.name().startswith("clprivnet"):
            return True
        if self.name().startswith("dman"):
            return True
        if self.name().startswith("wrsmd"):
            return True
        if self.name().startswith("scman"):
            return True
        if self.name().startswith("lo"):
            return True
        if self.name().startswith("bond"):
            return True
        if self.name().startswith("sppp"):
            return True
        if self.name().startswith("vsw"):
            return True
        if self.name().startswith("vnet"):
            return True
        return False

    ##########################################################################
    def get_cidr(self, dct):
        """From the netmask generate a CIDR"""
        if "netmask" not in dct:
            return
        if not dct["netmask"]:
            return
        if not _cidrmap:
            for i in range(33):
                _cidrmap[pow(2, 32) - pow(2, i)] = 32 - i

        if "." in dct["netmask"]:  # dotted quad netmask
            quads = dct["netmask"].split(".")
            nmsk = int(quads[3]) + 256 * (
                int(quads[2]) + 256 * (int(quads[1]) + 256 * int(quads[0]))
            )
        else:
            nmsk = int(dct["netmask"], 16)  # hex netmask
        if nmsk in _cidrmap:
            return _cidrmap[nmsk]
        return


##########################################################################
# Nics ###################################################################
##########################################################################
class Nics(explorerbase.ExplorerBase):
    ##########################################################################
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.parseIfconfig()
        self.parseHosts()
        for nic in self.nicList():
            nic.post()
        self.parse_kstats()
        self.analyse()

    ##########################################################################
    def parse_kstats(self):
        if self.config["explorertype"] != "solaris":
            return
        virtchains = [
            "fcip",
            "ipdrop",
            "chipinfo",
            "mii",
            "statistics",
            "parameters",
            "phydata",
            "driverinfo",
            "zero_copy",
            "dmfe_events",
            "chipid",
            "inbound",
            "outbound",
            "tcpstat_g",
            "mac",
            "serdes",
            "FFLP Stats",
            "IPP Stats",
            "MMAC Stats",
            "Port Stats",
            "RDC Channel",
            "RDC System Stats",
            "TDC Channel",
            "TXC Stats",
            "ZCP Stats",
            "driver-debug",
            "vsw",
        ]
        k = kstat.Kstat(self.config)
        for link in k.classChains("net"):
            # Strip out the chains that aren't actually real NICs
            if link.name().endswith("stat"):
                continue
            if link.name().startswith("vnetldc"):
                continue
            real = True
            for vc in virtchains:
                if link.name().startswith(vc):
                    real = False
                    break
            if not real:
                continue

            nicname, vlan, dev, inst = self.calcVlan(link.name())

            # If the name isn't a nic we have seen before it isn't in use
            # We also have to check interfaces for VLAN names
            if nicname in self:
                continue
            found = False
            for nic in self.nicList():
                for iface in nic["interfaces"]:
                    if nicname == iface:
                        found = True
                        break
            if not found:
                self[nicname] = Nic(self.config, nicname, link.module, link.instance)
                self[nicname]["used"] = False

    ##########################################################################
    def nicNames(self):
        """Return a list of the names of all the nics, sorted alphabetically"""
        return sorted(self.data.keys())

    ##########################################################################
    def nicList(self):
        """Return all the nic objects in a list, sorted by the name"""
        return [self.data[nic] for nic in self.nicNames()]

    ##########################################################################
    def analyse(self):
        for nic in self.nicList():
            nic.analyse()
            self.inheritIssues(nic)

    ##########################################################################
    def calcVlan(self, ifname):
        vlan = 0
        matchobj = re.match(r"(?P<dev>\D.+?)(?P<inst>\d+)(?P<vip>:\d+)?$", ifname)
        if not matchobj:
            self.Fatal(f"Unknown interface name: {ifname}")
        dev = matchobj.group("dev")
        inst = int(matchobj.group("inst"))
        if inst > 1000:
            vlan = inst / 1000
            inst = inst % 1000
            nicname = "%s%d" % (dev, inst)
        else:
            nicname = "%s%d" % (dev, inst)
        return nicname, vlan, dev, inst

    ##########################################################################
    def parseHosts(self):
        """
        See if we can match up hostnames with ip addresses based on /etc/hosts
        /etc/hostname.* files can be difficult to parse because of all the options
        """
        if not self.exists("etc/hosts"):
            return
        ipmap = {}
        infh = self.open("etc/hosts")
        for line in infh:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if "#" in line:
                line = line[: line.find("#")]
            bits = line.split()
            ipmap[bits[0]] = bits[1:]
        infh.close()

        for nic in self.nicList():
            for iface in nic["interfaces"]:
                if (
                    "ipaddr" in nic["interfaces"][iface]
                    and nic["interfaces"][iface]["ipaddr"] in ipmap
                ):
                    nic["interfaces"][iface]["hostname"] = ipmap[
                        nic["interfaces"][iface]["ipaddr"]
                    ]

    ##########################################################################
    def parseIfconfig(self):
        """
        Analyse ifconfig -a output:
        """
        try:
            if self.config["explorertype"] == "solaris":
                self.parse_solaris_ifconfig()
            elif self.config["explorertype"] == "linux":
                self.parse_linux_ifconfig()
                self.parse_linux_bond()
        except UserWarning as err:
            self.Warning(err)

    ##########################################################################
    def parse_linux_bond(self):
        """Check for bonded interfaces"""
        bondfiles = self.glob("proc/net/bonding/bond*")
        for bondfile in bondfiles:
            bond = bondfile.split("/")[-1]
            self[bond]["slaves"] = []
            infh = self.open(bondfile)
            for line in infh:
                if "Interface" in line:
                    slave = line.split()[-1]
                    self[bond]["slaves"].append(slave)
                    self[slave]["master"] = bond
                    self[slave]["used"] = True
                    self[slave]["notes"] = "Slave of %s" % bond
            self[bond]["notes"] = "Bond Master of %s" % (
                ", ".join(self[bond]["slaves"])
            )
            infh.close()

    ##########################################################################
    def parse_linux_ifconfig(self):
        infh = self.open("ifconfig")
        data = []
        for line in infh:
            line = line.rstrip()
            if "/sbin/ifconfig" in line:
                continue
            if not line:
                continue
            if line[0] == " ":
                data.append(line)
            else:
                self.parse_linux_ifconfig_interface(data)
                data = [line]
        infh.close()
        self.parse_linux_ifconfig_interface(data)

    ##########################################################################
    def parse_linux_ifconfig_interface(self, data):
        if not data:
            return
        line = data[0]
        ifname = line.split()[0]
        matchobj = re.match(r"(?P<fulldevice>(?P<dev>\D+)(?P<inst>\d*))", ifname)
        nicname = matchobj.group("fulldevice")
        if nicname not in self:
            self[nicname] = Nic(self.config, nicname, matchobj.group("dev"), matchobj.group("inst"))

        upflag = False
        for line in data:
            if "UP" in line:
                upflag = True

        if not upflag:
            return

        nicobj = self[nicname].add_interface(ifname)
        for line in data:
            matchobj = re.search(
                r"inet addr:(?P<ipaddr>.*?)\s+Bcast:(?P<broadcast>.*?)\s+Mask:(?P<mask>.*)",
                line,
            )
            if matchobj:
                nicobj["ipaddr"] = matchobj.group("ipaddr")
                nicobj["broadcast"] = matchobj.group("broadcast")
                nicobj["netmask"] = matchobj.group("mask")
                continue
            matchobj = re.search(r"inet6 addr:(?P<inet6>.*)\s+Scope:", line)
            if matchobj:
                nicobj["inet6"] = matchobj.group("inet6").strip()
                continue
            matchobj = re.search(r"inet addr:(?P<ipaddr>.*?)\s+Mask:(?P<mask>.*)", line)
            if matchobj:
                nicobj["ipaddr"] = matchobj.group("ipaddr")
                nicobj["netmask"] = matchobj.group("mask")
                continue
            matchobj = re.search(
                r".*Link encap:(?P<linkencap>.*?)\s+HWaddr (?P<hwaddr>.*)", line
            )
            if matchobj:
                nicobj["linkencap"] = matchobj.group("linkencap").strip()
                nicobj["hwaddr"] = matchobj.group("hwaddr")
                continue
            matchobj = re.search(r".*Link encap:(?P<linkencap>.*?)", line)
            if matchobj:
                nicobj["linkencap"] = matchobj.group("linkencap").strip()
                continue
            matchobj = re.search(
                r"(?P<flags>.*)MTU:(?P<mtu>\d+)\s+Metric:(?P<metric>\d+)", line
            )
            if matchobj:
                nicobj["flags"] = matchobj.group("flags").strip()
                nicobj["mtu"] = matchobj.group("mtu")
                nicobj["metric"] = matchobj.group("metric")

    ##########################################################################
    def parse_solaris_ifconfig(self):
        infh = self.open("sysconfig/ifconfig-a.out")
        nicobj = {}
        for line in infh:
            line = line.rstrip()
            if line[0] == "\t":
                matchobj = re.search(
                    r"inet (?P<ipaddr>.*) netmask (?P<netmask>.*) broadcast (?P<broadcast>.*)",
                    line,
                )
                if matchobj:
                    nicobj["ipaddr"] = matchobj.group("ipaddr")
                    nicobj["netmask"] = matchobj.group("netmask")
                    nicobj["broadcast"] = matchobj.group("broadcast")
                    if "-->" in nicobj["ipaddr"]:  # Point to point link
                        nicobj["ipaddr"] = nicobj["ipaddr"].split()[0]
                    continue
                matchobj = re.search("inet (?P<ipaddr>.*) netmask (?P<netmask>.*)", line)
                if matchobj:
                    nicobj["ipaddr"] = matchobj.group("ipaddr")
                    nicobj["netmask"] = matchobj.group("netmask")
                    if "-->" in nicobj["ipaddr"]:  # Point to point link
                        nicobj["ipaddr"] = nicobj["ipaddr"].split()[0]
                    continue
                matchobj = re.search("zone (?P<zone>.*)", line)
                if matchobj:
                    nicobj["zone"] = matchobj.group("zone")
                    continue
                matchobj = re.search("ether (?P<ether>.*)", line)
                if matchobj:
                    nicobj["ether"] = matchobj.group("ether")
                    continue
                matchobj = re.search("groupname (?P<groupname>.*)", line)
                if matchobj:
                    nicobj["groupname"] = matchobj.group("groupname")
                    continue
                matchobj = re.search("inet6 (?P<inet6>.*)", line)
                if matchobj:
                    nicobj["inet6"] = matchobj.group("inet6")
                    continue
            else:
                matchobj = re.search(
                    r"(?P<ifname>.*): flags=(?P<flagbits>.*)<(?P<flags>.*)> mtu (?P<mtu>\d+)( index (?P<index>\d+))?",
                    line,
                )
                if not matchobj:
                    self.Fatal(f"Unhandled nic line: '{line}'")
                ifname = matchobj.group("ifname")
                nicname, vlan, dev, inst = self.calcVlan(ifname)
                if nicname not in self:
                    self[nicname] = Nic(self.config, nicname, dev, inst)
                    self[nicname]["used"] = True
                nicobj = self[nicname].add_interface(ifname)
                nicobj["flags"] = matchobj.group("flags")
                nicobj["flagbits"] = matchobj.group("flagbits")
                nicobj["mtu"] = matchobj.group("mtu")
                if "index" in matchobj.groupdict():
                    nicobj["index"] = matchobj.group("index")
                if vlan:
                    nicobj["vlan"] = vlan
        infh.close()


# EOF
