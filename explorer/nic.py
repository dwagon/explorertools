#!/usr/local/bin/python
#
# Script to understand network card details
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: nic.py 4430 2013-02-27 07:38:20Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/nic.py $

import os, sys, getopt, re
import explorer
import explorerbase
import kstat

verbflag=0

_cidrmap={}

################################################################################
# Nic ##########################################################################
################################################################################
class Nic(explorerbase.ExplorerBase):
    ############################################################################
    def __init__(self, config, nicname, dev, inst):
        explorerbase.ExplorerBase.__init__(self, config)
        self.objname=nicname
        self['interfaces']={}
        self['dev']=dev
        self['inst']=inst
        self['link_speed']=''
        self['link_duplex']=''
        self['link_status']=''
        self['used']=False
        if self.config['explorertype']=='solaris':
            self.parse_Solaris()
        elif self.config['explorertype']=='linux':
            self.parse_Linux()

    ############################################################################
    def parse_Linux(self):
        try:
            self.parseLinux_ethtool()
        except UserWarning,err:
            #self.Warning(err)
            pass

    ############################################################################
    def parse_Solaris(self):
        self.parseNdd()

    ############################################################################
    def parseLinux_ethtool(self):
        """ Parse the ethtool output for linux boxes"""
        f=self.open("sos_commands/networking/ethtool_%s" % self.name())
        for line in f:
            line=line.strip()
            if 'Duplex:' in line and 'Unknown' not in line:
                self['link_duplex']=line[line.find(':')+1:].lower().strip()
            if 'Speed' in line and 'Unknown' not in line:
                self['link_speed']=line[line.find(':')+1:].lower()
        f.close()

    ############################################################################
    def post(self):
        if 'used' not in self:
            self['used']=False
        for iface in self['interfaces']:
            self['interfaces'][iface]['cidr']=self.getCIDR(self['interfaces'][iface])
            self['interfaces'][iface]['network']=self.getNetwork(self['interfaces'][iface])
            if self['interfaces'][iface]['network']:
                self['used']=True

    ############################################################################
    def analyse(self):
        if 'used' in self and not self['used']:
            return
        if 'half' in self['link_duplex'] and 'normal' not in self['link_duplex']:
            self.addConcern("duplex", obj=self.objname, text="set to half-duplex")
        for iface in self['interfaces']:
            if 'flags' in self['interfaces'][iface]:
                if 'UP' not in self['interfaces'][iface]['flags'] :
                    if 'IPv6' in self['interfaces'][iface]['flags'] and iface=='lo0':
                        pass
                    else:
                        self.addConcern("down", obj=self.objname, text="interface down")

    ############################################################################
    def parseNdd(self):
        """ Parse the ndd results
        Then interpret them into something approaching standards
        link_speed - speed in mbits
        link_duplex - full or half
        link_status - up or down
        """
        nic=re.sub('(?P<nicname>\D+)(?P<inst>\d+)', '\g<nicname>.\g<inst>', self.name())
        filelist=self.glob('netinfo/ndd/%s/*.out' % nic)
        for nddfile in filelist:
            if nddfile.endswith('list.out'):
                continue
            f=self.open(nddfile)
            line=f.readline()
            f.close()
            self['ndd_%s' % self.cmdfilename(nddfile)]=line.strip()

        # Every smegging nic type does it differently - thanks sun
        if not self.isVirtual():
            self.getLinkDuplex()
            self.getLinkSpeed()
            self.getLinkStatus()
            if self['used'] and 'link_duplex' in self and self['link_duplex']=='half':
                self.addConcern("duplex", obj=self.objname, text="set to half-duplex")
            if self['used'] and 'link_status' in self and self['link_duplex']=='down':
                self.addConcern("down", obj=self.objname, text="interface down")

    ############################################################################
    def getLinkStatus(self):
        if 'ndd_link_status' in self:
            self['link_status']={'0':'down', '1':'up'}[self['ndd_link_status']]

    ############################################################################
    def getLinkSpeed(self):
        if 'ndd_link_speed' in self:
            if self['ndd_link_speed']=='1000':
                self['link_speed']=1000
            elif self['ndd_link_speed']=='100':
                self['link_speed']==100
            elif self['ndd_link_speed']=='10':
                self['link_speed']=10
            elif self['ndd_link_speed']=='1':
                pass    # TODO
            elif self['ndd_link_speed']=='0':
                pass    # TODO
            else:
                self.Warning("Unhandled ndd_link_speed=%s" % self['ndd_link_speed'])

    ############################################################################
    def getKstatDuplex(self):
        """ Don't use the kstat function - this is way faster - we just want
        something very specific
        """
        if not self.exists('netinfo/kstat-p.out'):
            return '0'
        f=self.open('netinfo/kstat-p.out')
        for line in f:
            if 'link_duplex' not in line:
                continue
            if not line.startswith(self['dev']):
                continue
            if ':%s:' % self['inst'] not in line and '%s%s' % (self['dev'], self['inst']) not in line:
                continue
            f.close()
            return line.split()[-1]
        f.close()
        return '-1'

    ############################################################################
    def getLinkDuplex(self):
        if 'ndd_link_mode' in self:
            if self['ndd_link_mode']=='0':
                self['link_duplex']='half'
                return
            elif self['ndd_link_mode']=='1':
                self['link_duplex']='full'
                return
            elif self['ndd_link_mode']=='2':
                self['link_duplex']='full'
                return
            else:
                self.Warning("Unhandled ndd_link_mode=%s" % self['ndd_link_mode'])

        if self['dev'] in ('bge', 'ixge', 'nge'):
            try:
                self['link_duplex']={'0':'unknown', '1':'half', '2':'full'}[self['ndd_link_duplex']]
            except KeyError:
                self['link_duplex']='unknown'
        elif self['dev'] in ('ce', 'ge'):
            self['link_duplex']={'-1': 'error', '0':'unknown', '1':'half', '2':'full'}[self.getKstatDuplex()]
        elif self['dev']=='dmfe':
            # Duplex 1 means full; except if patch 116561-04 has been applied then it means half
            # What the hell were Sun thinking?
            pass
        elif self['dev'] in ('lo', 'lpfc', 'sppp', 'aggr', 'jnet', 'dman'):
            pass
        elif self['dev']=='eri':        # Should be covered by ndd
            self['link_duplex']={'-1': 'error', '0':'unknown', '1':'half', '2':'full'}[self.getKstatDuplex()]
        elif self['dev']=='qfe':        # Should be covered by ndd
            self['link_duplex']={'-1': 'error', '0':'unknown', '1':'half', '2':'full'}[self.getKstatDuplex()]
        elif self['dev']=='ipge':
            self['link_duplex']={'-1': 'error', '0':'unknown', '1':'half', '2':'full'}[self.getKstatDuplex()]
        elif self['dev']=='e1000g':
            self['link_duplex']={'-1': 'error', '0':'unknown', '1':'half', '2':'full'}[self.getKstatDuplex()]
        elif self['dev']=='nxge':
            # Comes out as string not a number
            self['link_duplex']=self.getKstatDuplex()
            #self.Warning("No duplex info for nxge networks - need dladm output")
        elif self['dev']=='le':
            self['link_duplex']='half (normal)'
        elif self['dev']=='jnic146x':
            self['link_duplex']='full'
        elif self['dev']=='ixgbe':
            self['link_duplex']={'-1': 'error', '0':'unknown', '1':'half', '2':'full'}[self.getKstatDuplex()]
        else:
            if 'ndd_link_duplex' in self:
                self['link_duplex']={'-1':'unknown','0':'half', '1':'half or full', '2':'full'}[self['ndd_link_duplex']]
            else:
                self.Warning("Unhandled nic: %s in getLinkDuplex()" % self['dev'])

    ############################################################################
    def getNetwork(self, dct):
        """ 1.2.3.4 / ffffff00 -> 1.2.3.0/24
        """
        if 'netmask' not in dct:        # ipv6 iface
            return "No netmask"
        try:
            nm=int(dct['netmask'], 16)
        except ValueError:
            quads=dct['netmask'].split('.')
            nm=int(quads[3])+256*(int(quads[2])+256*(int(quads[1])+256*int(quads[0])))
        order=3
        ip=0
        for quad in dct['ipaddr'].split('.'):
            ip+=int(quad)<<(8*order)
            order-=1
        network=ip&nm
        netstr=''
        for hexmap,shft in [('ff000000',24), ('ff0000',16), ('ff00',8), ('ff',0)]:
            netstr+="%d." % ((network&int(hexmap,16))>>shft)
        return netstr[:-1]

    ############################################################################
    def addInterface(self, ifname):
        self['interfaces'][ifname]={
                'flags': '',
                }
        return self['interfaces'][ifname]

    ############################################################################
    def isVirtual(self):
        if ':' in self.objname:
            return True
        if 'vlan' in self:
            return True
        if self.name().startswith('clprivnet'):
            return True
        if self.name().startswith('dman'):
            return True
        if self.name().startswith('wrsmd'):
            return True
        if self.name().startswith('scman'):
            return True
        if self.name().startswith('lo'):
            return True
        if self.name().startswith('bond'):
            return True
        if self.name().startswith('sppp'):
            return True
        if self.name().startswith('vsw'):
            return True
        if self.name().startswith('vnet'):
            return True
        return False

    ############################################################################
    def getCIDR(self, dct):
        """ From the netmask generate a CIDR
        """
        if 'netmask' not in dct:
            return
        if not dct['netmask']:
            return
        if not _cidrmap:
            for i in range(33):
                _cidrmap[pow(2,32)-pow(2,i)]=32-i

        if '.' in dct['netmask']:       # dotted quad netmask
            quads=dct['netmask'].split('.')
            nm=int(quads[3])+256*(int(quads[2])+256*(int(quads[1])+256*int(quads[0])))
        else:
            nm=int(dct['netmask'],16)   # hex netmask
        if nm in _cidrmap:
            return _cidrmap[nm]
        return

################################################################################
# Nics #########################################################################
################################################################################
class Nics(explorerbase.ExplorerBase):
    ############################################################################
    def __init__(self, config):
        explorerbase.ExplorerBase.__init__(self, config)
        self.parseIfconfig()
        self.parseHosts()
        for nic in self.nicList():
            nic.post()
        self.parseKstats()
        self.analyse()

    ############################################################################
    def parseKstats(self):
        if self.config['explorertype']!='solaris':
            return
        virtchains=['fcip', 'ipdrop','chipinfo','mii','statistics', 'parameters', 'phydata', 'driverinfo', 'zero_copy', 'dmfe_events', 'chipid', 'inbound', 'outbound', 'tcpstat_g', 'mac', 'serdes', 'FFLP Stats','IPP Stats', 'MMAC Stats', 'Port Stats', 'RDC Channel', 'RDC System Stats', 'TDC Channel', 'TXC Stats', 'ZCP Stats', 'driver-debug', 'vsw']
        k=kstat.Kstat(self.config)
        for link in k.classChains('net'):
            # Strip out the chains that aren't actually real NICs
            if link.name().endswith('stat'):
                continue
            if link.name().startswith('vnetldc'):
                continue
            real=True
            for vc in virtchains:
                if link.name().startswith(vc):
                    real=False
                    break
            if not real:
                continue

            nicname,vlan,dev,inst=self.calcVlan(link.name())

            # If the name isn't a nic we have seen before it isn't in use
            # We also have to check interfaces for VLAN names
            if nicname in self:
                continue
            found=False
            for nic in self.nicList():
                for iface in nic['interfaces']:
                    if nicname==iface:
                        found=True
                        break
            if not found:
                self[nicname]=Nic(self.config, nicname, link.module, link.instance)
                self[nicname]['used']=False

    ############################################################################
    def nicNames(self):
        """ Return a list of the names of all the nics, sorted alphabetically
        """
        return sorted(self.data.keys())

    ############################################################################
    def nicList(self):
        """ Return all the nic objects in a list, sorted by the name
        """
        return [self.data[nic] for nic in self.nicNames()]

    ############################################################################
    def analyse(self):
        for nic in self.nicList():
            nic.analyse()
            self.inheritIssues(nic)

    ############################################################################
    def calcVlan(self, ifname):
        vlan=0
        m=re.match('(?P<dev>\D.+?)(?P<inst>\d+)(?P<vip>:\d+)?$', ifname)
        if not m:
            self.Fatal("Unknown interface name: %s" % ifname)
        dev=m.group('dev')
        inst=int(m.group('inst'))
        if inst>1000:
            vlan=inst/1000
            inst=inst%1000
            nicname="%s%d" % (dev, inst)
        else:
            nicname="%s%d" % (dev, inst)
        return nicname,vlan, dev,inst

    ############################################################################
    def parseHosts(self):
        """
        See if we can match up hostnames with ip addresses based on /etc/hosts
        /etc/hostname.* files can be difficult to parse because of all the options
        """
        if not self.exists('etc/hosts'):
            return
        ipmap={}
        f=self.open('etc/hosts')
        for line in f:
            line=line.strip()
            if line.startswith('#') or not line:
                continue
            if '#' in line:
                line=line[:line.find('#')]
            bits=line.split()
            ipmap[bits[0]]=bits[1:]
        f.close()

        for nic in self.nicList():
            for iface in nic['interfaces']:
                if 'ipaddr' in nic['interfaces'][iface] and nic['interfaces'][iface]['ipaddr'] in ipmap:
                    nic['interfaces'][iface]['hostname']=ipmap[nic['interfaces'][iface]['ipaddr']]

    ############################################################################
    def parseIfconfig(self):
        """
        Analyse ifconfig -a output:
        """
        try:
            if self.config['explorertype']=='solaris':
                self.parseSolaris_ifconfig()
            elif self.config['explorertype']=='linux':
                self.parseLinux_ifconfig()
                self.parseLinux_bond()
        except UserWarning,err:
            self.Warning(err)

    ############################################################################
    def parseLinux_bond(self):
        """ Check for bonded interfaces
        """
        bondfiles=self.glob('proc/net/bonding/bond*')
        for bondfile in bondfiles:
            bond=bondfile.split('/')[-1]
            self[bond]['slaves']=[]
            f=self.open(bondfile)
            for line in f:
                if 'Interface' in line:
                    slave=line.split()[-1]
                    self[bond]['slaves'].append(slave)
                    self[slave]['master']=bond
                    self[slave]['used']=True
                    self[slave]['notes']="Slave of %s" % bond
            self[bond]['notes']="Bond Master of %s" % (", ".join(self[bond]['slaves']))
            f.close()

    ############################################################################
    def parseLinux_ifconfig(self):
        f=self.open('ifconfig')
        data=[]
        for line in f:
            line=line.rstrip()
            if '/sbin/ifconfig' in line:
                continue
            if not line:
                continue
            if line[0]==' ':
                data.append(line)
            else:
                self.parseLinux_ifconfig_interface(data)
                data=[line]
        f.close()
        self.parseLinux_ifconfig_interface(data)

    ############################################################################
    def parseLinux_ifconfig_interface(self, data):
        if not data:
            return
        line=data[0]
        ifname=line.split()[0]
        m=re.match('(?P<fulldevice>(?P<dev>\D+)(?P<inst>\d*))', ifname)
        nicname=m.group('fulldevice')
        if nicname not in self:
            self[nicname]=Nic(self.config, nicname, m.group('dev'), m.group('inst'))

        upflag=False
        for line in data:
            if 'UP' in line:
                upflag=True

        if not upflag:
            return

        nicobj=self[nicname].addInterface(ifname)
        for line in data:
            m=re.search('inet addr:(?P<ipaddr>.*?)\s+Bcast:(?P<broadcast>.*?)\s+Mask:(?P<mask>.*)', line)
            if m:
                nicobj['ipaddr']=m.group('ipaddr')
                nicobj['broadcast']=m.group('broadcast')
                nicobj['netmask']=m.group('mask')
                continue
            m=re.search('inet6 addr:(?P<inet6>.*)\s+Scope:', line)
            if m:
                nicobj['inet6']=m.group('inet6').strip()
                continue
            m=re.search('inet addr:(?P<ipaddr>.*?)\s+Mask:(?P<mask>.*)', line)
            if m:
                nicobj['ipaddr']=m.group('ipaddr')
                nicobj['netmask']=m.group('mask')
                continue
            m=re.search('.*Link encap:(?P<linkencap>.*?)\s+HWaddr (?P<hwaddr>.*)', line)
            if m:
                nicobj['linkencap']=m.group('linkencap').strip()
                nicobj['hwaddr']=m.group('hwaddr')
                continue
            m=re.search('.*Link encap:(?P<linkencap>.*?)', line)
            if m:
                nicobj['linkencap']=m.group('linkencap').strip()
                continue
            m=re.search('(?P<flags>.*)MTU:(?P<mtu>\d+)\s+Metric:(?P<metric>\d+)', line)
            if m:
                nicobj['flags']=m.group('flags').strip()
                nicobj['mtu']=m.group('mtu')
                nicobj['metric']=m.group('metric')

    ############################################################################
    def parseSolaris_ifconfig(self):
        f=self.open('sysconfig/ifconfig-a.out')
        nicname=''
        for line in f:
            line=line.rstrip()
            if line[0]=='\t':
                m=re.search('inet (?P<ipaddr>.*) netmask (?P<netmask>.*) broadcast (?P<broadcast>.*)', line)
                if m:
                    nicobj['ipaddr']=m.group('ipaddr')
                    nicobj['netmask']=m.group('netmask')
                    nicobj['broadcast']=m.group('broadcast')
                    if '-->' in nicobj['ipaddr']:       # Point to point link
                        nicobj['ipaddr']=nicobj['ipaddr'].split()[0]
                    continue
                m=re.search('inet (?P<ipaddr>.*) netmask (?P<netmask>.*)', line)
                if m:
                    nicobj['ipaddr']=m.group('ipaddr')
                    nicobj['netmask']=m.group('netmask')
                    if '-->' in nicobj['ipaddr']:       # Point to point link
                        nicobj['ipaddr']=nicobj['ipaddr'].split()[0]
                    continue
                m=re.search('zone (?P<zone>.*)', line)
                if m:
                    nicobj['zone']=m.group('zone')
                    continue
                m=re.search('ether (?P<ether>.*)', line)
                if m:
                    nicobj['ether']=m.group('ether')
                    continue
                m=re.search('groupname (?P<groupname>.*)', line)
                if m:
                    nicobj['groupname']=m.group('groupname')
                    continue
                m=re.search('inet6 (?P<inet6>.*)', line)
                if m:
                    nicobj['inet6']=m.group('inet6')
                    continue
            else:
                m=re.search('(?P<ifname>.*): flags=(?P<flagbits>.*)<(?P<flags>.*)> mtu (?P<mtu>\d+)( index (?P<index>\d+))?', line)
                if not m:
                    self.Fatal("Unhandled nic line: '%s'" % line)
                ifname=m.group('ifname')
                nicname,vlan,dev,inst=self.calcVlan(ifname)
                if nicname not in self:
                    self[nicname]=Nic(self.config, nicname, dev, inst)
                    self[nicname]['used']=True
                nicobj=self[nicname].addInterface(ifname)
                nicobj['flags']=m.group('flags')
                nicobj['flagbits']=m.group('flagbits')
                nicobj['mtu']=m.group('mtu')
                if 'index' in m.groupdict():
                    nicobj['index']=m.group('index')
                if vlan:
                    nicobj['vlan']=vlan
        f.close()

#EOF
