#!/usr/local/bin/python
"""
Script to understand kstat output
"""
# Written by Dougal Scott <dougal.scott@gmail.com>

from explorer import explorerbase


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
    def add_val(self, stat, val):
        """TODO"""
        if stat == "class":
            self.class_ = val
        elif stat == "snaptime":
            self.snaptime = val
        else:
            self[stat] = val

    ##########################################################################
    def __repr__(self):
        return f"<Chain: module={self.module} name={self.objname} instance={self.instance} class_={self.class_}>"

    ##########################################################################
    def print_link(self):
        """TODO"""
        strg = ""
        for k in sorted(self.data.keys()):
            strg += f"{k}={self[k]}\n"
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
        self._parse_kstat()

    ##########################################################################
    def _parse_kstat(self):
        """TODO"""
        if not self.exists("netinfo/kstat-p.out"):
            return
        infh = self.open("netinfo/kstat-p.out")
        for line in infh:
            line = line.strip()
            try:  # Start of new instances don't have data
                idn, val = line.split("\t")
            except ValueError:
                continue
            bits = idn.split(":")
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
            self[module][name][instance].add_val(statistic, val)

        infh.close()

    ##########################################################################
    def _module_list(self):
        """TODO"""
        return sorted(self.keys())

    ##########################################################################
    def _name_list(self, module=None):
        """TODO"""
        names = []
        if module is None:
            modlist = self._module_list()
        else:
            modlist = [module]
        for mod in modlist:
            names.extend(self[mod].keys())
        return sorted(names)

    ##########################################################################
    def instance_list(self, module, name):
        """Return the instances that belong to the"""
        return self[module][name].keys()

    ##########################################################################
    def class_chains(self, class_, module=None):
        """Return all the chains that belong to the specified class_
        module can legitimately be '' - so can't check for Falsehood
        """
        if module is None:
            modlist = self._module_list()
        else:
            modlist = [module]
        classlist = []
        for mod in modlist:
            for nam in self._name_list(mod):
                for i in self[mod][nam]:
                    if self[mod][nam][i].class_ == class_:
                        classlist.append(self[mod][nam][i])
        return classlist

    ##########################################################################
    def chain(self, module, name, instance):
        """TODO"""
        chn = self[module][name][instance]
        return chn


# EOF
