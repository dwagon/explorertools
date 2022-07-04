#!/usr/local/bin/python
"""
# Script to understand misc details
"""
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: misc.py 2398 2012-06-04 02:00:57Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/misc.py $

import re
import time
import explorerbase


##########################################################################
# miscDetails ############################################################
##########################################################################
class miscDetails(explorerbase.ExplorerBase):
    """Class to represent misc details extracted from an explorer"""

    ##########################################################################
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.orighostname = ""
        self.hostname = ""
        self.config = config
        self.parse()

    ##########################################################################
    def parse(self):
        """TODO"""
        self.parse_explorer()

    ##########################################################################
    def get_hostname(self, orighostname):
        """Sosreport returns a different hostname than uname (it strips
        the '-'s from the hostname.
        Also other problems where the prime external name is not the name that
        is returned by uname.
        """
        self.orighostname = orighostname
        self.hostname = orighostname  # Need this for sosreport
        fname = None
        if self.exists("uname"):
            fname = "uname"
        elif self.exists("sysconfig/uname-a.out"):
            fname = "sysconfig/uname-a.out"
        if fname:
            infh = self.open(fname)
            for line in infh:
                if "uname" not in line:
                    hostname = line.split()[1]
            infh.close()
        else:
            hostname = orighostname

        if "." in hostname:
            hostname = hostname[: hostname.index(".")]

        return hostname

    ##########################################################################
    def parse_explorer(self):
        """TODO"""
        self.get_explorer_version()
        if self.config["explorertype"] == "solaris":
            self.get_eeprom()
            self.get_modules()
            self.get_ldoms()
        elif self.config["explorertype"] == "linux":
            pass
        self.get_serial()
        self.get_packages()
        self.get_patches()
        self.get_processes()
        self.get_net_listeners()
        self.get_wwns()
        self.get_fc_info()
        self.get_printers()

    ##########################################################################
    def get_modules(self):
        """TODO"""
        fname = "sysconfig/modinfo-c.out"
        self["modules"] = []
        if not self.exists(fname):
            return
        infh = self.open(fname)
        for line in infh:
            line = line.strip()
            if not line or "Name" in line or "UNINSTALLED" in line:
                continue
            self["modules"].append(line.split()[2])

    ##########################################################################
    def get_printers(self):
        """List which print queues are configured on this server"""
        fname = "lp/printers.conf"
        self["printers"] = []
        if not self.exists(fname):
            return
        infh = self.open(fname)
        for line in infh:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            if line.startswith(":"):
                continue
            printer = line.split(":")[0]
            if "|" in printer:
                printer = printer.split("|")[0]
            self["printers"].append(printer.lower())
        infh.close()

    ##########################################################################
    def get_fc_info(self):
        """Get details about all the FCs attached to the server"""
        fname = "sysconfig/fcinfo.out"
        if not self.exists(fname):
            return
        data = ""
        self["fcinfo"] = []
        infh = self.open(fname)
        for line in infh:
            if line.startswith("No Adapters Found"):
                return
            if line.startswith("HBA"):
                self.parse_fc_info_stanza(data)
                data = line
            else:
                data += line
        self.parse_fc_info_stanza(data)
        infh.close()

    ##########################################################################
    def parse_fc_info_stanza(self, buffer):
        """TODO"""
        if not buffer:
            return
        data = {}
        for line in buffer.splitlines():
            bits = line.strip().split(":", 1)
            data[bits[0]] = bits[1].strip()
        self["fcinfo"].append(data)

    ##########################################################################
    def get_wwns(self):
        """Report on which WWNs are associated with his host
        WWNs are hidden in a few different places.
        """
        wwnset = set()
        if self.exists("sysconfig/fcinfo.out"):
            infh = self.open("sysconfig/fcinfo.out")
            for line in infh:
                if "WWN" in line:
                    wwn = line.split(":")[-1].strip()
                    wwnset.add(wwn)
            infh.close()

        lxlist = self.glob("disks/luxadm_display_*")
        for lf in lxlist:
            infh = self.open(lf)
            for line in infh:
                if "WWN" in line:
                    wwnset.add(line.strip().split()[-1])
            infh.close()

        # JNICs appear here and sometimes no where else
        if self.exists("sysconfig/prtpicl-v.out"):
            infh = self.open("sysconfig/prtpicl-v.out")
            for line in infh:
                if "wwpn" in line:
                    wwnset.add(line.strip().split()[-1])
                if "wwnn" in line:
                    wwnset.add(line.strip().split()[-1])
            infh.close()

        tmp = list(wwnset)
        for x in tmp[:]:
            if x.startswith("0x"):
                tmp.append(x[2:])
                tmp.remove(x)
            if x[0] not in "0123456789abcdef":
                tmp.remove(x)

        self["wwn"] = tmp

    ##########################################################################
    def get_net_listeners(self):
        """Report on what ports that the server is listening on"""
        self["netlisteners"] = {}
        if self.config["explorertype"] == "solaris":
            self.get_solaris_net_listeners()

    ##########################################################################
    def get_solaris_net_listeners(self):
        """TODO"""
        filename = "netinfo/netstat-an.out"
        if not self.exists(filename):
            self.Warning(f"{filename} doesn't exist")
            return
        infh = self.open(filename)
        mode = None
        for line in infh:
            line = line.strip()
            if line.startswith("----"):
                continue
            if line.startswith("Local Address"):
                continue
            if line.startswith("UDP: IPv4"):
                mode = "ipv4_udp"
                self["netlisteners"][mode] = []
            if line.startswith("UDP: IPv6"):
                mode = "ipv6_udp"
                self["netlisteners"][mode] = []
            if line.startswith("TCP: IPv4"):
                mode = "ipv4_tcp"
                self["netlisteners"][mode] = []
            if line.startswith("TCP: IPv6"):
                mode = "ipv6_tcp"
                self["netlisteners"][mode] = []
            if line.startswith("SCTP"):
                break
            if mode == "ipv4_udp":
                if "Idle" in line and line.startswith("*"):
                    bits = line.split()
                    self["netlisteners"][mode].append(bits[0].replace("*.", ""))
            if mode == "ipv6_udp":
                if "Idle" in line and line.startswith("*"):
                    bits = line.split()
                    self["netlisteners"][mode].append(bits[0].replace("*.", ""))
            if mode == "ipv4_tcp":
                if "LISTEN" in line and line.startswith("*"):
                    bits = line.split()
                    self["netlisteners"][mode].append(bits[0].replace("*.", ""))
            if mode == "ipv6_tcp":
                if "LISTEN" in line and line.startswith("*"):
                    bits = line.split()
                    self["netlisteners"][mode].append(bits[0].replace("*.", ""))
        infh.close()

    ##########################################################################
    def get_ldoms(self):
        """Report on any Solaris LDOMs we have
        All systems must have memory so check memory allocation
        is a reasonable way of getting the definitive list
        """
        filename = "sysconfig/ldm_list-devices_-a.out"
        if not self.exists(filename):
            return
        self["ldoms"] = []
        infh = self.open(filename)
        inmemory = False
        for line in infh:
            line = line.strip()
            if line == "MEMORY":
                inmemory = True
                continue
            if line == "IO":
                inmemory = False
            if inmemory:
                try:
                    bound = line.split()[2]
                    if bound not in ("primary", "BOUND", "_sys_"):
                        self["ldoms"].append(bound)
                except IndexError:
                    pass
        infh.close()

    ##########################################################################
    def analyse(self):
        """TODO"""
        if (
            "eeprom" in self
            and "auto-boot?" in self["eeprom"]
            and self["eeprom"]["auto-boot?"] == "false"
        ):
            self.addIssue("autoboot", category="eeprom", text="auto-boot? set to false")

    ##########################################################################
    def get_processes(self):
        """TODO"""
        processes = {}
        mode = None
        if self.config["explorertype"] == "solaris":
            if self.exists("sysconfig/ps-efZ.out"):
                infh = self.open("sysconfig/ps-efZ.out")
                mode = "zone"
            elif self.exists("sysconfig/ps-ef.out"):
                infh = self.open("sysconfig/ps-ef.out")
                mode = "vanilla"
            else:
                self.Warning("No usable ps output")
                return
            psreg = re.compile(r".* \d+:\d\d (.*)$")
            for line in infh:
                line = line.strip()
                proc = {}
                bits = line.split()
                if mode == "zone":
                    if line.startswith("ZONE"):
                        continue
                    proc["zone"] = bits[0]
                    proc["uid"] = bits[1]
                    proc["pid"] = bits[2]
                    proc["ppid"] = bits[3]
                else:
                    if line.startswith("UID"):
                        continue
                    proc["uid"] = bits[0]
                    proc["pid"] = bits[1]
                    proc["ppid"] = bits[2]
                matchobj = psreg.match(line)
                if not matchobj:
                    # Somehow you can get processes with no name
                    proc["cmd"] = "Unnamed"
                else:
                    proc["cmd"] = matchobj.group(1)
                processes[proc["pid"]] = proc
            infh.close()
        elif self.config["explorertype"] == "linux":
            if self.exists("ps"):
                infh = self.open("ps")
                for line in infh:
                    line = line.strip()
                    if line.startswith("USER"):
                        continue
                    bits = line.split()
                    proc = {}
                    proc["uid"] = bits[0]
                    proc["pid"] = bits[1]
                    proc["cmd"] = bits[10]
                    processes[proc["pid"]] = proc
                infh.close()
        self["processes"] = processes

    ##########################################################################
    def get_patches(self):
        """TODO"""
        self["patches"] = {}
        if self.config["explorertype"] == "solaris":
            filename = "patch+pkg/patch_date.out"
            if not self.exists(filename):
                self.Warning("Couldn't read patch dates: %s" % filename)
                return
            infh = self.open(filename)
            for line in infh:
                line = line.strip()
                if line.startswith("total"):
                    continue
                bits = line.split()
                patchnum = bits[-1]
                patchdatestr = " ".join(bits[5:-1])
                # Patch dates are in either of these two formats
                # Jul  9  2008
                # May 18 13:31
                try:
                    patchdate = time.strptime(patchdatestr, "%b %d %Y")
                except ValueError:
                    # Add the year - for files newer than 6 months
                    year = time.localtime()[0]
                    pdate = patchdatestr + " %s" % year
                    d = time.strptime(pdate, "%b %d %H:%S %Y")
                    if time.mktime(d) > time.time():
                        year -= 1
                    pdate = patchdatestr + f" {year}"
                    patchdate = time.strptime(pdate, "%b %d %H:%S %Y")
                self["patches"][patchnum] = time.strftime("%Y-%m-%d", patchdate)
            infh.close()

    ##########################################################################
    def get_packages(self):
        """TODO"""
        self["packages"] = {}
        if self.config["explorertype"] == "solaris":
            if not self.exists("patch+pkg/pkginfo-l.out"):
                return
            infh = self.open("patch+pkg/pkginfo-l.out")
            for line in infh:
                line = line.strip()
                if self.lineSkipper(line, start=["Long pkg", "====="]):
                    continue
                if line.startswith("PKGINST:"):
                    package = line[line.find(":") + 1:].strip()
                if line.startswith("VERSION:"):
                    version = line[line.find(":") + 1:].strip()
                    self["packages"][package] = version
            infh.close()
        elif self.config["explorertype"] == "linux":
            if not self.exists("installed-rpms"):
                return
            infh = self.open("installed-rpms")
            for line in infh:
                line = line.strip()
                if " " in line:
                    line = line.split()[0]
                bits = line.split("-")
                package = ""
                version = ""
                flag = False
                for bit in bits:
                    if bit[0] in "0123456789":
                        flag = True
                    if flag:
                        version += f"{bit}-"
                    else:
                        package += f"{bit}-"
                self["packages"][package[:-1]] = version[:-1]
            infh.close()

    ##########################################################################
    def get_eeprom(self):
        """Check for eeprom settings"""
        self["eeprom"] = {}
        if not self.exists("sysconfig/eeprom.out"):
            self.Warning("Couldn't read eeprom settings")
            return
        infh = self.open("sysconfig/eeprom.out")
        for line in infh:
            line = line.strip()
            if "=" in line:
                bits = line.split("=")
                self["eeprom"][bits[0]] = bits[1]
        infh.close()

    ##########################################################################
    def get_serial(self):
        """TODO"""
        if self.config["explorertype"] == "solaris":
            if self.get_ipmi_serial():
                return
            if self.get_tx_serial():
                return
            if self.get_prtdiag():
                return
        # if self.get_chassis():
        #           return
        if self.config["explorertype"] == "linux":
            if self.get_dmidecode():
                return
            if self.get_hardware_py():
                return

    ##########################################################################
    def get_hardware_py(self):
        """This is for old school linux only - sysreport"""
        if not self.exists("hardware.py"):
            return False
        infh = self.open("hardware.py")
        for line in infh:
            if "asset" in line:
                matchobj = re.search(r"\(system: (?P<system>\S+)\)", line.strip())
                if matchobj:
                    serial = matchobj.group("system")
                    if serial.lower() not in ("xxxxxxx", "serial#"):
                        self["serial"] = serial
                    return True
        infh.close()
        return False

    ##########################################################################
    def get_dmidecode(self):
        """This is for linux only"""
        if not self.exists("dmidecode"):
            return False
        data = []
        infh = self.open("dmidecode")
        for line in infh:
            line = line.strip()
            if line.startswith("Handle"):
                if "System Information" in data:
                    for d in data:
                        if "Serial Number" in d:
                            serial = d.split(":")[1].strip()
                            if "0000000" not in serial and serial not in (
                                "Not Available",
                                "00",
                            ):
                                self["serial"] = serial
                            return True
                data = []
            else:
                data.append(line)
        infh.close()
        return False

    ##########################################################################
    def get_chassis(self):
        """Get the serial number from the 'chassis_serial' file if it exists
        I don't trust this as it takes its input from dubious sources such
        as eeprom settings
        """
        if not self.exists("sysconfig/chassis_serial.out"):
            return False
        infh = self.open("sysconfig/chassis_serial.out")
        line = infh.readline().strip()
        infh.close()
        if line:
            if "unknown" in line:
                return False
            if "_" in line:  # It has sn_sn_sn too often - don't know why
                self["serial"] = line.split("_")[0]
            else:
                self["serial"] = line
            return True
        return False

    ##########################################################################
    def get_prtdiag(self):
        """Get the serial number from prtdiag if available"""
        if not self.exists("sysconfig/prtdiag-v.out"):
            return False
        mode = False
        infh = self.open("sysconfig/prtdiag-v.out")
        for line in infh:
            line = line.strip()
            if "Chassis Serial Number" in line:
                mode = True
                continue
            if mode:
                if not line.startswith("---"):
                    line = line.strip()
                    self["serial"] = self.sanitise_serial(line)
                    # self.Warning("prtdiag serial='%s' -> %s" % (line, self['serial']))
                    return True
        infh.close()
        return False

    ##########################################################################
    def sanitise_serial(self, serial):
        """
        Occassionaly we get wierd serial numbers that have
        0111apo- or other things before them
        """
        if "-" in serial:
            serial = serial[serial.find("-") + 1:]
        return serial.strip()

    ##########################################################################
    def get_tx_serial(self):
        """Get the serial number from hosts that have Tx00 details"""
        if self.exists("Tx000/showplatform_-v"):
            infh = self.open("Tx000/showplatform_-v")
            for line in infh:
                line = line.strip()
                if "Serial Number" in line:
                    self["serial"] = self.sanitise_serial(line.split()[-1])
                    # self.Warning("txA serial='%s' -> %s" % (line, self['serial']))
                    return True
                if "Blade Serial Number:" in line:
                    self["serial"] = self.sanitise_serial(line.split()[-1])
                    # self.Warning("txB serial='%s' -> %s" % (line, self['serial']))
                    return True
            infh.close()

        if not self.exists("Tx000/showfru"):
            return False
        infh = self.open("Tx000/showfru")
        for line in infh:
            line = line.strip()
            if "System_Id" in line:
                serial = line.split(":")[-1]
                # Occassionally they put two numbers on the line
                if len(serial.split()) != 1:
                    serial = serial.split()[0]  # Don't know what the second one is
                self["serial"] = self.sanitise_serial(serial)
                # self.Warning("txC serial='%s' -> %s" % (line, self['serial']))
                return True
        infh.close()
        return False

    ##########################################################################
    def get_ipmi_serial(self):
        """Get the host serial number from hosts that have ipmitool working"""
        if not self.exists("ipmi/ipmitool_fru.out"):
            return False
        infh = self.open("ipmi/ipmitool_fru.out")
        stanza = False
        serial = None
        for line in infh:
            line = line.strip()
            if not line:
                stanza = False
            if line.startswith("FRU Device"):
                if " mb.fru " in line or "Builtin FRU" in line or "/SYS" in line:
                    stanza = True

            if not stanza:
                continue
            if "Product Serial" in line:
                serial = line.split(":")[-1].strip()
                # Occassionally the MAC address gets picked up instead
                if len(serial) < 5:
                    continue
                if serial != "0000000000":
                    self["serial"] = serial.lower()
                    # self.Warning("ipmiA serial='%s' -> %s" % (line, self['serial']))
                    return True
        infh.close()
        return False

    ##########################################################################
    def get_explorer_version(self):
        """TODO"""
        if self.config["explorertype"] == "solaris":
            if not self.exists("README"):
                self.Warning("No README found")
                return
            infh = self.open("README")
            line = infh.readline()
            infh.close()
            matchobj = re.search(r"\(Version (?P<version>.*)\)", line)
            if matchobj:
                self["explorerversion"] = matchobj.group("version").lower()
            else:
                matchobj = re.search(r"Version (?P<version>\S+)\s", line)
                if matchobj:
                    self["explorerversion"] = matchobj.group("version").lower()
        elif self.config["explorertype"] == "linux":
            if self.exists("installed-rpms"):
                infh = self.open("installed-rpms")
                for line in infh:
                    if "sysreport-" in line:
                        bits = line.strip().split("-")
                        self["explorerversion"] = "-".join(bits[0:2])
                        break
                    if "sos-" in line:
                        bits = line.strip().split("-")
                        self["explorerversion"] = "-".join(bits[0:2])
                        break
                infh.close()


# EOF
