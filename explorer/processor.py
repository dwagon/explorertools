"""
Script to understand processor details
"""
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: processor.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/processor.py $

import re
import math
from explorer import explorerbase


##########################################################################
# Processor ##############################################################
##########################################################################
class Processor(explorerbase.ExplorerBase):
    """ Processor """
    ##########################################################################
    def __init__(self, config, cpunum):
        explorerbase.ExplorerBase.__init__(self, config)
        self.objname = cpunum

    ##########################################################################
    def analyse(self):
        """TODO"""


##########################################################################
# Processors #############################################################
##########################################################################
class Processors(explorerbase.ExplorerBase):
    """ Processors """
    ##########################################################################
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.parse()

    ##########################################################################
    def parse(self):
        """TODO"""
        try:
            if self.config["explorertype"] == "solaris":
                self._parse_solaris_psrinfo()
            elif self.config["explorertype"] == "linux":
                self._parse_linux_cpuinfo()
            else:
                self.fatal(
                    f"Processors - unknown explorertype {self.config['explorertype']}"
                )
        except UserWarning as err:
            self.warning(err)

    ##########################################################################
    def analyse(self):
        """TODO"""
        for cpudets in self.values():
            cpudets.analyse()
            self.inheritIssues(cpudets)

    ##########################################################################
    def _parse_linux_cpuinfo(self):
        """TODO"""
        infh = self.open("proc/cpuinfo")
        for line in infh:
            if line.startswith("processor"):
                cpunum = line.split()[-1]
                cpu = Processor(self.config, cpunum)
                self[cpunum] = cpu
            if line.startswith("model name"):
                cpu["proctype"] = line[line.find(":") + 1:].strip()
            if line.startswith("cpu MHz"):
                # Convert speed to a round number: 1500 rather than 1499.998
                # MHz
                cpu["speed"] = str(
                    int(
                        math.ceil(
                            float(line[line.find(":") + 1:].strip())))
                    )
        infh.close()

    ##########################################################################
    def _parse_solaris_psrinfo(self):
        """
        Analyse psrinfo -v output which looks like:
        Status of processor 0 as of: 11/25/05 14:16:15
          Processor has been on-line since 08/04/05 17:30:21.
          The sparc processor operates at 400 MHz,
                and has a sparc floating point processor.
        """
        infh = self.open("sysconfig/psrinfo-v.out")
        for line in infh:
            line = line.strip()
            matchobj = re.search(r"Status of .*processor (?P<cpunum>\d+) as of: .*", line)
            if matchobj:
                cpunum = int(matchobj.group("cpunum"))
            cpu = Processor(self.config, cpunum)
            matchobj = re.search(
                "The (?P<proctype>.*) processor operates at (?P<speed>.*),", line
            )
            if matchobj:
                cpu["proctype"] = matchobj.group("proctype")
                cpu["speed"] = matchobj.group("speed")
                self[cpunum] = cpu
        infh.close()


# EOF
