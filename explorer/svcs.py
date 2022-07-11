#!/usr/local/bin/python
"""
Script to understand svcs output for explorer analysis
"""
# Written by Dougal Scott <dougal.scott@gmail.com>

from explorer import explorerbase


##########################################################################
# Svcs ###################################################################
##########################################################################
class Svcs(explorerbase.ExplorerBase):
    """Understand explorer output with respect to fma"""

    ##########################################################################
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        if not self.exists("sysconfig/svcs-xv.out"):
            return
        self.parse_svcs()

    ##########################################################################
    def analyse(self):
        pass

    ##########################################################################
    def parse_svcs(self):
        """ TODO """
        infh = self.open("sysconfig/svcs-xv.out")
        buf = []
        for line in infh:
            line = line.rstrip()
            if line.startswith("svc:"):
                if buf:
                    subcat = buf[0][buf[0].find("(") + 1: buf[0].rfind(")")].replace(
                        ",", ""
                    )
                    self.add_issue(subcat, obj=buf[0], text=buf)
                    buf = []
            buf.append(line)
        if buf:
            subcat = buf[0][buf[0].find("(") + 1: buf[0].rfind(")")].replace(",", "")
            self.add_issue(subcat, obj=buf[0], text=buf)
        infh.close()


# EOF
