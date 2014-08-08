#!/usr/local/bin/python
#
# Script to understand svcs output for explorer analysis
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: svcs.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/svcs.py $

import explorerbase

##########################################################################
# Svcs ###################################################################
##########################################################################


class Svcs(explorerbase.ExplorerBase):

    """Understand explorer output with respect to fma
    """
    ##########################################################################

    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        if not self.exists('sysconfig/svcs-xv.out'):
            return
        self.parseSVCS()

    ##########################################################################
    def analyse(self):
        pass

    ##########################################################################
    def parseSVCS(self):
        f = self.open('sysconfig/svcs-xv.out')
        buf = []
        for line in f:
            line = line.rstrip()
            if line.startswith('svc:'):
                if buf:
                    subcat = buf[0][
                        buf[0].find('(') + 1:buf[0].rfind(')')].replace(',', '')
                    self.addIssue(subcat, obj=buf[0], text=buf)
                    buf = []
            buf.append(line)
        if buf:
            subcat = buf[0][
                buf[0].find('(') + 1:buf[0].rfind(')')].replace(',', '')
            self.addIssue(subcat, obj=buf[0], text=buf)
        f.close()

# EOF
