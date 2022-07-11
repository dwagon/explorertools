"""
Script to understand tape details
"""
# Written by Dougal Scott <dougal.scott@gmail.com>

import os
from explorer import explorerbase


##########################################################################
# Tapedrive ##############################################################
##########################################################################
class Tapedrive(explorerbase.ExplorerBase):
    """ Tape drives """
    ##########################################################################
    def __init__(self, config, tapename):
        explorerbase.ExplorerBase.__init__(self, config)
        self.objname = tapename

    ##########################################################################
    def analyse(self):
        """ TODO """
        pass

    ##########################################################################
    def parse_mode_page(self):
        """ TODO """
        infh = self.open("tapes/%s/ModePage_00.out" % self.name())
        for line in infh:
            if line.startswith("device name:"):
                self["device"] = line.split(":")[-1].strip()
            if line.startswith("device vendor id:"):
                self["hardware"] = line.split(":")[-1].strip()
            if line.startswith("Tape motion hours"):
                self["motionhours"] = int(line.split()[-1].strip())
            if line.startswith("Power-on hours"):
                self["powerhours"] = int(line.split()[-1].strip())
            if line.startswith("Tape motion duty cycle"):
                self["dutycycle"] = float(line.split()[-1].strip())
        infh.close()


##########################################################################
# Tapes ##################################################################
##########################################################################
class Tapes(explorerbase.ExplorerBase):
    """Understand explorer output with respect to tape drives"""

    ##########################################################################
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        if not self.exists("tapes"):
            return
        devlist = self.parse_iostat("tapes/iostat-En.out")
        for dev in devlist:
            if dev.startswith("rmt") or dev.startswith("st"):
                newname = dev.replace("/", "_")
                self[newname] = Tapedrive(config, newname)
                for key, val in devlist[dev].items():
                    self[newname][key] = val
                self[newname]["hardware"] = "%s %s" % (
                    self[newname]["vendor"],
                    self[newname]["product"],
                )

        for drv in self.glob("tapes/rmt*"):
            tape = os.path.basename(drv)
            if tape not in self:
                self[tape] = Tapedrive(config, tape)
            self[tape].parse_mode_page()

    ##########################################################################
    def analyse(self):
        """ TODO """
        for tape in self.tape_list():
            self[tape].analyse()
            self.inherit_issues(self[tape])

    ##########################################################################
    def tape_list(self):
        """ TODO """
        return sorted(self.data.keys())

# EOF
