#!/usr/local/bin/python
"""
Script to understand kstat output
"""
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: kstat.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/kstat.py $

import explorer.explorerbase as explorerbase


##########################################################################
# Chain ##################################################################
##########################################################################
class Chain(explorerbase.ExplorerBase):
    """All the kstat information for a single module:name pair"""

    ##########################################################################
    def __init__(self, config, module, name, instance):
        """TODO"""
        explorerbase.ExplorerBase.__init__(self, config)
        self.module = module
        self.objname = name
        self.instance = instance
        self.class_ = None
        self.snaptime = None

    ##########################################################################
    def addVal(self, stat, val):
        """TODO"""
        if stat == "class":
            self.class_ = val
        elif stat == "snaptime":
            self.snaptime = val
        else:
            self[stat] = val

    ##########################################################################
    def __repr__(self):
        return "<Chain: module=%s name=%s instance=%s class_=%s>" % (
            self.module,
            self.objname,
            self.instance,
            self.class_,
        )

    ##########################################################################
    def printLink(self):
        """TODO"""
        strg = ""
        for k in sorted(self.data.keys()):
            strg += "%s=%s\n" % (k, self[k])
        return strg


##########################################################################
# Kstat ##################################################################
##########################################################################
class Kstat(explorerbase.ExplorerBase):
    """Understand explorer output with respect to kstat"""

    ##########################################################################
    def __init__(self, config):
        """TODO"""
        explorerbase.ExplorerBase.__init__(self, config)
        self.parseKstat()

    ##########################################################################
    def parseKstat(self):
        """TODO"""
        if not self.exists("netinfo/kstat-p.out"):
            return
        f = self.open("netinfo/kstat-p.out")
        for line in f:
            line = line.strip()
            try:  # Start of new instances don't have data
                id, val = line.split("\t")
            except ValueError:
                continue
            bits = id.split(":")
            module = bits[0]
            instance = bits[1]
            statistic = bits[-1]
            name = ":".join(bits[2:-1])  # Sigh, so much for a clean concept
            if module not in self:
                self[module] = {}
            if name not in self[module]:
                self[module][name] = {}
            if instance not in self[module][name]:
                self[module][name][instance] = Chain(
                    self.config, module, name, instance
                )
            self[module][name][instance].addVal(statistic, val)

        f.close()

    ##########################################################################
    def moduleList(self):
        """TODO"""
        return sorted(self.keys())

    ##########################################################################
    def nameList(self, module=None):
        """TODO"""
        names = []
        if module is None:
            modlist = self.moduleList()
        else:
            modlist = [module]
        for mod in modlist:
            names.extend(self[mod].keys())
        return sorted(names)

    ##########################################################################
    def instanceList(self, module, name):
        """Return the instances that belong to the"""
        return self[module][name].keys()

    ##########################################################################
    def classChains(self, class_, module=None):
        """Return all the chains that belong to the specified class_
        module can legitimately be '' - so can't check for Falsehood
        """
        if module is None:
            modlist = self.moduleList()
        else:
            modlist = [module]
        classlist = []
        for m in modlist:
            for n in self.nameList(m):
                for i in self[m][n]:
                    if self[m][n][i].class_ == class_:
                        classlist.append(self[m][n][i])
        return classlist

    ##########################################################################
    def chain(self, module, name, instance):
        """TODO"""
        c = self[module][name][instance]
        return c


# EOF
