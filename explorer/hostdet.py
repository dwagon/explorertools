#!/usr/bin/env python3
"""
Script to understand host details
"""
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: hostdet.py 3035 2012-10-01 07:19:27Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/hostdet.py $

import re
from explorer import explorerbase
from explorer import hardware


##########################################################################
# Host ###################################################################
##########################################################################
class Host(explorerbase.ExplorerBase):
    """Understand explorer output with respect to details about hosts"""

    ##########################################################################
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.parse()

    ##########################################################################
    def parse(self):
        """TODO"""
        self["osrev"] = ""
        self._parse_uname()
        self._parse_ram()
        self._parse_hardware()
        self._parse_solaris_sysdef()
        self._parse_uptime()
        self._parse_reboot()
        self._parse_release()

    ##########################################################################
    def _parse_release(self):
        """TODO"""
        if self.config["explorertype"] == "solaris":
            if not self.exists("etc/release"):
                self["osrelease"] = ""
                return
            infh = self.open("etc/release")
        if self.config["explorertype"] == "linux":
            if self.exists("etc/redhat-release"):
                infh = self.open("etc/redhat-release")
            else:
                self.warning("No release details available")
                return
        data = infh.readline()
        infh.close()
        self["osrelease"] = data.strip().lower()

    ##########################################################################
    def _parse_reboot(self):
        """TODO"""
        if self.config["explorertype"] != "solaris":
            return
        try:
            infh = self.open("sysconfig/last-20-reboot.out")
            data = infh.readline()
            infh.close()
            self["reboot"] = " ".join(data.split()[3:])
        except UserWarning as err:
            self.warning(err)

    ##########################################################################
    def analyse(self):
        """TODO"""

    ##########################################################################
    def _parse_uptime(self):
        """TODO"""
        self["uptime"] = "unknown"
        try:
            if self.config["explorertype"] == "solaris":
                infh = self.open("sysconfig/uptime.out")
            if self.config["explorertype"] == "linux":
                infh = self.open("uptime")
            for line in infh:
                line = line.strip()
                matchobj = re.search(r".* up (?P<uptime>.*),\s+\d+ user.*", line)
                if matchobj:
                    self["uptime"] = matchobj.group("uptime")
            infh.close()
        except UserWarning as err:
            self.warning(err)

    ##########################################################################
    def _parse_solaris_sysdef(self):
        """TODO"""
        if self.config["explorertype"] != "solaris":
            return
        try:
            infh = self.open("sysconfig/sysdef.out")
            mode = ""
            for line in infh:
                if "Hostid" in line:
                    mode = "hostid"
                if mode == "hostid" and not line.startswith("*"):
                    self["hostid"] = line.strip()
                    mode = ""
            infh.close()
        except UserWarning as err:
            self.warning(err)

    ##########################################################################
    def _short_hwdesc(self, fulldesc):
        """Convert the full, rather wordy, description to a more terse version"""
        if "(" in fulldesc:
            fulldesc = re.sub(r"(.*)\(.*?\)(.*)", r"\1\2", fulldesc)
        hwdesc = fulldesc.strip()
        hwdesc = hwdesc.replace("Sun Microsystems, Inc.", "")
        hwdesc = hwdesc.replace("oracle corporation", "")
        hwdesc = hwdesc.replace("Sun Microsystems", "")
        hwdesc = hwdesc.replace("UPA/PCI", "")
        hwdesc = hwdesc.replace("sun4u", "")
        hwdesc = hwdesc.strip().lower()
        return hwdesc

    ##########################################################################
    def _parse_linux_hardwarepy(self):
        """TODO"""
        infh = self.open("hardware.py")
        for line in infh:
            line = line.strip()
            if line.startswith("'system'"):
                hware = line.split(":")[-1].strip()[1:-1]
                hwtype, hwname = self.get_hardware(hware)
                self["hwtype"] = hwtype
                self["hardware"] = hwname
            if line.startswith("'bios_version'"):
                self["bios"] = line.split(":")[-1].strip()[1:-1].strip()

    ##########################################################################
    def _parse_linux_dmidecode(self):
        """TODO"""
        data = []
        infh = self.open("dmidecode")
        for line in infh:
            line = line.strip()
            if line.startswith("Handle"):
                if "System Information" in data:
                    for dataline in data:
                        if "Product Name" in dataline:
                            hwdesc = dataline.split(":")[1].strip()
                            hwtype, hwname = self.get_hardware(hwdesc)
                            self["hwdesc"] = hwdesc
                            self["hwtype"] = hwtype
                            self["hardware"] = hwname
                elif "BIOS Information" in data:
                    for dataline in data:
                        if "Version" in dataline:
                            self["bios"] = dataline.split(":")[1].strip()
                data = []
            else:
                data.append(line)
        infh.close()

    ##########################################################################
    def parse_linux(self):
        """TODO"""
        try:
            self._parse_linux_dmidecode()
        except UserWarning:
            pass
        try:
            self._parse_linux_hardwarepy()
        except UserWarning:
            pass

    ##########################################################################
    def _parse_hardware(self):
        """Try all the various methods to get the type of hardware that this
        box is
        """
        self["obp"] = ""
        self["post"] = ""
        self["hardware"] = ""
        try:
            if self.config["explorertype"] == "linux":
                self.parse_linux()
                return
            if self.exists("sysconfig/prtdiag-v.out"):
                self.parse_prtdiag()
            if self.exists("Tx000/showhost"):
                self.parse_showhost()
            if self.exists("Tx000/showplatform_-v"):
                self.parse_showplatform()
            if self.exists("ipmi/ipmitool_fru.out"):
                self.parse_ipmitool()
            if self.exists("sysconfig/smbios.out"):
                self.parse_smbios()
            if not self["hardware"]:
                self.parse_uname_hw()
            self.check_for_ldom()
        except UserWarning as err:
            self.warning(err)

    ##########################################################################
    def check_for_ldom(self):
        """An LDOM doesn't know it is an ldom - except that it does have
        some modules loadded into the kernel that phyicals don't. E.g.
        vdc - virtual disc controller

        New ldoms (v2.?) have a command called virtinfo which does know that
        it is a virtual and also knows control domain :)
        # DOMAINROLE|impl=LDoms|control=true|io=true|service=true|root=true
        # DOMAINROLE|impl=LDoms|control=false|io=false|service=false|root=false
        """
        if self.exists("sysconfig/virtinfo-a-p.out"):
            isldom = False
            infh = self.open("sysconfig/virtinfo-a-p.out")
            for line in infh:
                if line.startswith("DOMAINROLE"):
                    if "true" not in line:
                        isldom = True
                        self["hwtype"] = "virtual"
                        self["vmtype"] = "ldom"
                if line.startswith("DOMAINCONTROL"):
                    name = line.split("|")[1].split("=")[1]
                    if isldom:
                        self["virtualmaster"] = name.strip()
            infh.close()
            return

        if not self.exists("sysconfig/modinfo-c.out"):
            return
        infh = self.open("sysconfig/modinfo-c.out")
        for line in infh:
            if "vdc" in line and "LOADED/INSTALLED" in line:
                self["hwtype"] = "virtual"
                break
        infh.close()

    ##########################################################################
    def parse_smbios(self):
        """TODO"""
        if self["hardware"]:
            return
        infh = self.open("sysconfig/smbios.out")
        for line in infh:
            if "Product:" in line:
                hwname = line.split(":")[1].strip()
                hwtype, hwname = self.get_hardware(hwname)
                self["hwtype"] = hwtype
                self["hardware"] = hwname
        infh.close()

    ##########################################################################
    def parse_uname_hw(self):
        """TODO"""
        if self["hardware"]:
            return
        infh = self.open("sysconfig/uname-a.out")
        data = infh.readline()
        infh.close()
        hwuname = data.strip().split()[-1]
        hwtype, hwname = self.get_hardware(hwuname)
        self["hwtype"] = hwtype
        self["hardware"] = hwname
        infh.close()

    ##########################################################################
    def parse_ipmitool(self):
        """TODO"""
        if self["hardware"]:
            return
        infh = self.open("ipmi/ipmitool_fru.out")
        mode = False
        for line in infh:
            line = line.strip()
            if line.startswith("FRU Device Description"):
                name = line.split(":", 1)[-1].split()[0].strip().replace(".fru", "")
                mode = name in ("mb", "Builtin")
            if mode and "Product Name" in line:
                hwname = line.split(":")[-1].strip()
                if hwname in ("ilom", "ILOM"):
                    continue
                hwtype, hwname = self.get_hardware(hwname)
                self["hwtype"] = hwtype
                self["hardware"] = hwname
        infh.close()

    ##########################################################################
    def parse_showplatform(self):
        """TODO"""
        if self["hardware"]:
            return
        infh = self.open("Tx000/showplatform_-v")
        for line in infh:
            line = line.strip()
            if line.startswith("SUNW,"):
                hwtype, hwname = self.get_hardware(line)
                self["hwtype"] = hwtype
                self["hardware"] = hwname
        infh.close()

    ##########################################################################
    def parse_showhost(self):
        """TODO"""
        infh = self.open("Tx000/showhost")
        for line in infh:
            line = line.strip()
            if line.startswith("Hypervisor"):
                self["hypervisor"] = " ".join(line.split()[:2])
            if line.startswith("OBP"):
                self["obp"] = " ".join(line.split()[:2])
            if line.startswith("POST"):
                self["post"] = " ".join(line.split()[:2])
        infh.close()

    ##########################################################################
    def parse_prtdiag(self):
        """TODO"""
        infh = self.open("sysconfig/prtdiag-v.out")
        datestr = r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}"
        for line in infh:
            line = line.strip()
            if line.startswith("Memory Size"):
                bits = line.split(":")
                ram = bits[1]
                self["ram"] = ram
                continue
            if line.startswith("System Configuration"):
                hwdesc = self._short_hwdesc(line.split(":")[-1])
                hwtype, hwname = self.get_hardware(hwdesc)
                self["hwtype"] = hwtype
                self["hardware"] = hwname
                self["hwdesc"] = hwdesc.replace(" ", "_")
            if "OBP" in line:
                matchobj = re.search(
                    rf"(?P<obp>OBP\s+\S+) {datestr}\s+(?P<post>POST\s+\S+) {datestr}",
                    line
                )
                if matchobj:
                    self["obp"] = matchobj.group("obp")
                    self["post"] = matchobj.group("post")
                else:
                    matchobj = re.search(rf"(?P<obp>OBP \S+) {datestr}", line)
                    if matchobj:
                        self["obp"] = matchobj.group("obp")
            if line.startswith("BIOS Configuration"):
                self["bios"] = line.split(":", 1)[-1].strip()
        infh.close()

    ##########################################################################
    def _parse_ram(self):
        """TODO"""
        try:
            if self.config["explorertype"] == "solaris":
                self["os"] = "solaris"
                infh = self.open("sysconfig/prtconf-vp.out")
                for line in infh:
                    if line.startswith("Memory size"):
                        ram = line.split()[-2]
                        self["ram"] = ram
                infh.close()
            elif self.config["explorertype"] == "linux":
                self["os"] = "linux"
                infh = self.open("free")
                for line in infh:
                    if line.startswith("Mem:"):
                        self["ram"] = int(line.split()[1]) / 1024
                infh.close()
        except UserWarning as err:
            self.warning(err)
            self["ram"] = 0

    ##########################################################################
    def _parse_uname(self):
        """
        Analyse uname output
        """
        self["arch"] = ""
        if self.config["explorertype"] == "solaris":
            infh = self.open("sysconfig/uname-a.out")
            line = infh.readline()
            infh.close()
            self["uname"] = line.strip()
            if self.exists("sysconfig/uname-X.out"):
                infh = self.open("sysconfig/uname-X.out")
                for line in infh:
                    line = line.rstrip()
                    if line.startswith("Release"):
                        self["osrev"] = line.split()[-1]
                    if line.startswith("KernelID"):
                        self["kernelpatch"] = line.split()[-1]
                    if line.startswith("Machine"):
                        self["arch"] = line.split()[-1]
                infh.close()
            elif self.exists("sysconfig/uname-a.out"):
                infh = self.open("sysconfig/uname-a.out")
                line = infh.readline()
                infh.close()
                bits = line.strip().split()
                self["osrev"] = bits[2]
                self["kernelpatch"] = bits[3]
                self["arch"] = bits[4]
            else:
                self.warning("No solaris uname output to analyse")
                return

        elif self.config["explorertype"] == "linux":
            if not self.exists("uname"):
                self.warning("No linux uname output to analyse")
                return
            infh = self.open("uname")
            for line in infh:
                if "uname" in line:
                    continue
                bits = line.strip().split()
                self["osrev"] = bits[2]
                self["kernelpatch"] = ""
                self["arch"] = bits[-2]
                self["uname"] = line.strip()
            infh.close()

    ##########################################################################
    def get_hardware(self, hwdesc):
        """TODO"""
        hwdesc = hwdesc.replace("IBM IBM", "IBM")
        hwdesc = hwdesc.replace("sun4u", "")
        if hwdesc.startswith('"') or hwdesc.startswith("'"):
            hwdesc = hwdesc[1:]
        if hwdesc.endswith('"') or hwdesc.endswith("'"):
            hwdesc = hwdesc[:-1]
        hwdesc = hwdesc.strip()
        try:
            hwtype, hwname = hardware.get_hardware(hwdesc)
        except hardware.UnknownHardware:
            self.warning(f"Unknown hardware: {hwdesc}")
            hwtype = "unknown"
            hwname = "unknown"
        return hwtype, hwname


# EOF
