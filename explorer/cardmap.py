""" Cards for prtdiag analysis """
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: cardmap.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/cardmap.py $

##########################################################################
##########################################################################
##########################################################################
cards = {
    # 'SUNW,qsi-cheerio': { 'fake': True },
    # 'fibre-channel': { 'iocard':'Unknown Fibre channel', 'option': 'SG-XPC1FC-QF2', 'part': '375-3102'},
    "375-3181": {
        "iocard": "XVR-100 Graphics Accelerator (64MB)",
        "part": "375-3181",
        "option": "X3770A",
    },
    "501-3060": {"iocard": "Dual FC-AL Sbus Card", "part": "501-3060"},
    "501-5266": {"iocard": "FC-AL Sbus Card", "option": "X6730A", "part": "501-5266"},
    "FCE-1063": {
        "iocard": "FCE-1063 HBA",
    },
    "FCE-1473-N": {
        "iocard": "FCE-1473 2Gig HBA",
    },
    "FCE-6460-N": {
        "iocard": "FCE-6460-N HBA",
    },
    "FCX-6562": {
        "iocard": "FCX-6562 HBA",
    },
    "FCX2-6562": {
        "iocard": "FCX2-6562 HBA",
    },
    "LP9002S": {
        "iocard": "Emulex LightPulse LP9002S FC-AL",
    },
    "LSI,1064E": {
        "iocard": "LSI SAS Controller",
    },
    "LSI,1068E": {
        "iocard": "LSI PCI Express SAS Controller",
    },
    "QLA2462": {
        "iocard": "Qlogic QLA2462 PCI HBA [Type 4]",
    },
    "QLGC,ISP1000": {
        "iocard": "SCSI Differential Host Adapter Sbus Card",
    },
    "QLGC,ISP1000U": {
        "iocard": "Ultra SCSI Differential Host Adapter Sbus Card",
    },
    "QLGC,ISP10160": {
        "iocard": "SCSI Controller PCI Card ISP10160",
    },
    "QLGC,ISP1040B": {
        "iocard": "SCSI Controller PCI Card ISP1040B",
    },
    "QLGC,qla-pci1077,9.": {
        "iocard": "QLogic QLA ?",
    },
    "QLGC,qlc-pci1077,100": {
        "iocard": "Unknown qlc-pci1077,100",
    },
    "QLGC,qlc-pci1077,134.": {
        "iocard": "QLogic QLA 2462",
    },
    "QLGC,qlc-pci1077,9.": {
        "iocard": "QLogic QLC ?",
    },
    "SUNW,258-7883": {
        "iocard": "X1 Boot PROM",
        "fru": "258-7883",
    },
    "SUNW,375-3126": {
        "iocard": "Sun XVR-100 Graphics Accelerator (32MB)",
        "part": "375-3126",
        "option": "X3769A",
    },
    "SUNW,375-3069": {
        "iocard": "Sun XVR-500 Graphics Accelerator",
        "part": "375-3069",
        "option": "X3685",
    },
    "SUNW,375-3290": {
        "iocard": "Sun XVR-100 Graphics Accelerator (64MB)",
        "part": "375-3290",
        "option": "X7296A",
    },
    "SUNW,501-4790": {
        "iocard": "Creator3D Series 3 (FFB2+)",
        "fru": "501-4790",
    },
    "SUNW,cheerio": {"fake": True},
    "SUNW,emlxs-pci10df": {
        "iocard": "2Gb PCI-X Single GC Host Adapter",
        "option": "SG-XPCI1FC-EM2",
        "part": "375-3304",
    },
    "SUNW,fas/sd": {
        "iocard": "Fast/Wide SCSI bus adaptor",
    },
    "SUNW,hme": {
        "iocard": "100Mbit network card (hme)",
        "option": "X1033A",
        "part": "501-5019",
    },
    "SUNW,isptwo": {
        "iocard": "PCI SunSwift",
    },
    "SUNW,lomh": {
        "iocard": "TODO SUNW,lomh",
    },
    "SUNW,m64B": {
        "iocard": "8-Bit Color Frame Buffer",
        "option": "X3660A",
        "part": "270-2256",
    },
    "SUNW,pci-ce": {
        "iocard": "GigaSwift PCI",
    },
    "SUNW,pci-eri": {
        "iocard": "SUNW,pci-eri",
    },
    "SUNW,pci-gem": {
        "iocard": "PCI Gigabit Ethernet Adapter",
    },
    "SUNW,pci-qfe": {
        "iocard": "SUN PCI Quad Fast Ethernet",
    },
    "SUNW,pci-qge": {
        "iocard": "PCI Quad GigaSwift Ethernet NIC",
    },
    "SUNW,qfe-pci108e,1001": {
        "iocard": "SUN PCI Quad Fast Ethernet",
    },
    "SUNW,qlc-XXX": {
        "iocard": "PCI-X FC HBA",
    },
    "SUNW,qlc-pci1077,1020": {
        "iocard": "QLogic Fast-Wide SCSI",
    },
    "SUNW,qlc-pci1077,2200": {
        "iocard": "QLogic Fibre Channel Adapter",
    },
    "SUNW,qlc-pci1077,2300": {
        "iocard": "QLogic 64 bit Fibre Channel Adapter",
    },
    "pci1077,2312": {
        "iocard": "QLogic Fibre Channel Adapter",
    },
    "SUNW,qlc-pci1077,2422": {
        "iocard": "QLA2460 QLogic PCI to Fibre Channel Adapter",
    },
    "SUNW,qsi-cheerio": {"fake": True},
    "SUNW,sbbc": {"fake": True},
    "SUNW,sbus-gem": {
        "iocard": "Sbus Gigabit Ethernet Adapter",
    },
    "SUNW,sbus-qfe": {
        "iocard": "Sbus Quad Fast Ethernet Adapter",
    },
    "SUNW,sgsbbc": {
        "fake": True,
    },
    "SUNW,smbus": {
        "iocard": "TODO SUNW,smbus",
    },
    "Sbus SunSwift": {
        "iocard": "Sbus SunSwift",
    },
    "Symbios,53C875": {
        "iocard": "Dual PCI SCSI Controller",
        "part": "375-3191",
        "option": "SG-XPCI2SCSI-LM320",
    },
    "Symbios,53C896": {
        "iocard": "Symbios,53C896",
    },
    "TSI,gfxp": {
        "iocard": "PGX32 8/24-Bit Color Frame Buffer",
        "option": "X3668A",
        "part": "370-3753",
    },
    "dma-isadma": {
        "iocard": "TODO dma-isadma",
    },
    "ebus": {"fake": True},
    "ethernet-pci4554": {
        "iocard": "TODO ethernet-pci4554",
    },
    "fcaw/sd": {
        "iocard": "FCW? Card",
    },
    "fibre-channel-pci1077,2300": {
        "iocard": "QLogic 64 bit Fibre Channel Adapter",
    },
    "fibre-channel-pci1077,9": {
        "iocard": "Emulex PCI FC ?",
    },
    "fibre-channel-pci10df,f900": {
        "iocard": "Emulex PCI FC LP9002",
    },
    "fibre-channel-pci10df,f980": {
        "iocard": "Emulex PCI FC LP9802",
    },
    "fibre-channel-pci10df,fd00": {
        "iocard": "Emulex PCI FC ?",
    },
    "firewire-pci108e,1102": {
        "iocard": "Sun PCI Firewire",
    },
    "i2c-i2c-smbus": {
        "iocard": "TODO i2c-i2c-smbus",
    },
    "pci10b9,5229": {
        "iocard": "Ali Corp EIDE Controller",
        "fake": True,
    },
    "isa/rmc-comm": {"fake": True},  # Serial console
    "isa/su": {
        "iocard": "TODO isa/su",
    },
    "lomp": {"fake": True},  # Part of LOM?
    "lpfc-pci10df,f900": {
        "iocard": "Emulex PCI FC LP9002",
    },
    "lpfc-pci10df,f980": {
        "iocard": "Emulex PCI FC LP9802",
    },
    "pci-bridge": {"fake": True},
    "pci-pci1011,22": {"fake": True},  # Dec PCI-PCI Bridge
    "pci-pci1011,24": {"fake": True},  # Dec PCI-PCI Bridge
    "pci-pci1011,25": {"fake": True},  # Dec PCI-PCI Bridge
    "pci-pci1011,26": {"fake": True},  # Dec PCI-PCI Bridge
    "pci-pci104c,ac28": {"fake": True},  # TI PCI-PCI Bridge
    # Alex PCI-PCI Bridge - unconfirmed
    "pci-pci8086,537c": {"fake": True},
    "pci-pci8086,b154": {"fake": True},  # Alex PCI-PCI Bridge
    "pci-x-qge": {
        "iocard": "PCI-X GigaSwift Ethernet NIC",
    },
    "pci1000,21": {
        "iocard": "LSI Ultra SCSI Controller",
    },
    "pci1000,50": {
        "iocard": "LSI Logic 1064 SAS/SATA HBA",
    },
    "pci1000,54": {
        "iocard": "LSI Logic sas-pci1000,54",
    },
    "pci1044,1012": {
        "iocard": "Domino RAID Engine",
    },
    "pci1044,a501": {
        "iocard": "Adaptec SmartRAID V",
    },
    "pci108e,1000": {"fake": True},  # SUN PCI I/O Controller'
    "pci108e,6310": {"iocard": "Unknown pci108e,6310"},
    "pci108e,676a": {"iocard": "Unknown pci108e,676a"},
    "pci108e,1100": {
        "iocard": "SUN RIO EBUS pci108e,1100",
    },
    "pci108e,1648": {
        "iocard": "Unknown pci108e,1648 - network",
    },
    "pci108e,3de7": {
        "iocard": "Unknown pci108e,3de7",
    },
    "pci1095,646": {
        "iocard": "Silicon Image IDE Bus master",
    },
    "pci1095,680": {
        "iocard": "Silicon Image Ultra ATA-133 Host Controller",
    },
    "pci10df,fa00": {
        "iocard": "Emulex PCI FC LP10000",
    },
    "pci114f,1c": {
        "iocard": "Unknown PCI card pci114f,1c - Multiport serial?",
    },
    "pci1242,4643": {
        "iocard": "Unknown JNI PCI 640but fibrechannel card",
    },
    "pci12d4,200": {
        "iocard": "Unknown PCI card pci12d4,200",
    },
    "pci14e4,1648": {
        "iocard": "Gigabit Ethernet",
    },
    "pci14e4,1668": {
        "iocard": "Unknown NetXtreme BCM5714 Gigabit Ethernet",
    },
    "pci8086,1048": {
        "iocard": "Unknown pci8086,1048",
    },
    "pci8086,108e": {
        "iocard": "Unknown pci8086,108e",
    },
    "pciclass,0000": {
        "fake": True,
    },
    "pciclass,0c0010": {
        "fake": True,
    },  # Firewire
    "pciclass,058000": {
        "fake": True,
    },
    "pciclass,068000": {
        "fake": True,
    },
    "pciclass,078000": {
        "fake": True,
    },
    "pciex1077,2432": {"iocard": "QLogic QLE2460 Fibre Channel Card"},
    "pciex108e,abcd": {
        "iocard": "Multithreaded 10 Gigabit Network controller",
    },
    "pciex10b5,8532": {"fake": True},  # PEX 8532 PCI Express Switch
    "pci-pciex10b5,8533": {"fake": True},  # PEX 8533 6-port PCI Express Switch
    "pciex10df,fe00": {
        "iocard": "Emulex PCI FC LPe11000",
    },
    "pciex8086,105e": {
        "iocard": "Intel Gig Networking",
    },
    "pciexclass,060400": {"fake": True},
    # Ali Corp Power Management Controller
    "pmu-pci10b9,7101": {"fake": True},
    "power-acpi-power": {
        "iocard": "TODO power-acpi-power",
    },
    "qla-pci1077,2.": {
        "iocard": "QLogic card - unknown",
    },
    "qlc-pci1077,1016": {
        "iocard": "QLogic Single Channel Ultra3 SCSI Controller",
    },
    "qlc-pci1077,133": {
        "iocard": "Qlogic QLA2460 PCI HBA [Type 1]",
    },
    "qlc-pci1077,140": {
        "iocard": "Qlogic QLA2460 PCI HBA [Type 2]",
    },
    "qlc-pci1077,141": {
        "iocard": "Qlogic QLA2462 PCI HBA [Type 3]",
    },
    "rtc-ds1287": {
        "iocard": "TODO rtc-ds1287",
    },
    "rtc-m5819": {
        "iocard": "TODO rtc-m5819",
    },
    "scsi-pci1000,30": {
        "iocard": "LSI Ultra320 SCSI Controller",
    },
    "scsi-pci1000,b": {
        "iocard": "LSI Dual Channel Wide Ultra2 SCSI Controller",
    },
    "scsi-pci1000,f": {
        "iocard": "LSI Ultra Wide SCSI Controller",
    },
    "serial-su16550": {
        "iocard": "TODO serial-su16550",
    },
    "sound-pci10b9,5451": {
        "iocard": "Sound Card",
    },
    "usb-pci108e,1103": {
        "iocard": "SUN USB Controller",
    },
    "pciclass,0c0310": {
        "iocard": "USB Controller: 0c0310",
    },
    "usb-pciclass,0c0320": {
        "iocard": "USB Controller: 0c0320",
    },
    "XVR-50": {"iocard": "XVR-50 Graphics"},
}

##########################################################################
##########################################################################
##########################################################################
comboSets = {
    "SCSI RAID Controller (SRC/P)": {
        "components": ["pci1044,1012", "pci1044,a501"],
        "option": "X6542A",
        "part": "375-0082",
    },
    "Dual Channel Ultra2 SCSI (53C875 model)": {
        "components": ["Symbios,53C875", "Symbios,53C875"],
    },
    "Dual Channel Ultra2 SCSI (53C896 model)": {
        "components": ["Symbios,53C896", "Symbios,53C896"],
    },
    "PCI Dual Ultra3 SCSI Host Adapter": {
        "components": ["QLGC,ISP10160", "QLGC,ISP10160"],
        "option": "X6758A",
        "part": "375-3057",
    },
    "Emulex PCI Dual Channel LP9002 FC": {
        "components": ["lpfc-pci10df,f900", "lpfc-pci10df,f900"],
    },
    "Emulex PCI Dual Channel FC": {
        "components": ["SUNW,emlxs-pci10df", "SUNW,emlxs-pci10df"],
    },
    "PCI Dual FC Host Adapter": {
        "components": ["SUNW,qlc-pci1077,2200", "SUNW,qlc-pci1077,2200"],
        "option": "X6727A",
        "part": "375-3030",
    },
    "SUN PCI Quad Fast Ethernet [Type 1]": {
        "components": [
            "SUNW,qfe-pci108e,1001",
            "SUNW,qfe-pci108e,1001",
            "SUNW,qfe-pci108e,1001",
            "SUNW,qfe-pci108e,1001",
        ],
    },
    "SUN PCI Quad Fast Ethernet [Type 2]": {
        "components": ["SUNW,pci-qfe", "SUNW,pci-qfe", "SUNW,pci-qfe", "SUNW,pci-qfe"],
    },
    "PCI Quad GigaSwift Ethernet NIC": {
        "components": ["SUNW,pci-qge", "SUNW,pci-qge", "SUNW,pci-qge", "SUNW,pci-qge"],
    },
    "PCI-X FC Quad Port 2Gb/sec HBA": {
        "components": ["pci1077,2312", "pci1077,2312", "pci1077,2312", "pci1077,2312"],
    },
    "PCI Express Quad Gigabit Ethernet UTP": {
        "components": [
            "pciex108e,abcd",
            "pciex108e,abcd",
            "pciex108e,abcd",
            "pciex108e,abcd",
        ],
        "option": "X4447A",
        "part": "501-7607",
    },
    "2Gb PCI Dual FC Host Adapter": {
        "components": ["pci1077,2312", "pci1077,2312"],
        "option": "SG-XPCI2FC-QF2-Z",
        "part": "375-3363",
    },
    "PCI-X Quad GigaSwift Ethernet NIC": {
        "components": ["pci-x-qge", "pci-x-qge", "pci-x-qge", "pci-x-qge"],
        "option": "X4445A",
        "part": "501-6738",
    },
    "SBus Quad Fast Ethernet": {
        "components": [
            "SUNW,sbus-qfe",
            "SUNW,sbus-qfe",
            "SUNW,sbus-qfe",
            "SUNW,sbus-qfe",
        ],
    },
    "Sbus SunSwift": {
        "components": ["SUNW,hme", "SUNW,fas/sd"],
    },
    "PCI Dual Ultra320 SCSI Adapter": {
        "components": ["scsi-pci1000,30", "scsi-pci1000,30"],
        "option": "SG-XPCI2SCSILM320-Z",
        "part": "375-3365",
    },
    "Dual Single/Ended or Differential Ultra/Wide SCSI": {
        "components": ["scsi-pci1000,f.", "scsi-pci1000,f."],
        "option": ["X6540A", "X6541A"],
        "part": ["375-0005", "375-0006"],
    },
    "Sun Dual FastEthernet and Dual SCSI/P Adapter": {
        "components": [
            "SUNW,pci-ce",
            "SUNW,pci-ce",
            "scsi-pci1000,30",
            "scsi-pci1000,30",
        ],
    },
    "PCI Express Dual Gigabit Ethernet UTP": {
        "components": ["pciex8086,105e", "pciex8086,105e"],
        "part": "371-0905",
        "option": "X7280A-2",
    },
    "Dual QLA2462 HBA": {
        "components": ["qlc-pci1077,141", "qlc-pci1077,141"],
    },
    "4 Gigabit/sec PCI Express Single FC Host Adaptor": {
        "components": ["pciex1077,2432", "pciex1077,2432"],
        "part": "375-3355",
        "option": "SG-XPCIE1FC-QF4",
    },
    "4Gb/sec PCI Express Dual FC / Dual Gigabit Ethernet ExpressModule Host Adapter, QLogic": {
        "components": [
            "pciex8086,105e",
            "pciex8086,105e",
            "pciex1077,2432",
            "pciex1077,2432",
        ],
        "part": "371-4017",
        "option": "SG-XPCIE2FCGBE-Q-Z",
    },
    "unknown combo #1 (ebus,eri,firewire,usb)": {
        "components": [
            "pci108e,1100",
            "SUNW,pci-eri",
            "firewire-pci108e,1102",
            "usb-pci108e,1103",
        ],
    },
    "unknown combo #2 (eri, usb)": {
        "components": ["SUNW,pci-eri", "usb-pci108e,1103"],
    },
    "unknown combo #3 (eri, firewire)": {
        "components": ["SUNW,pci-eri", "firewire-pci108e,1102"],
    },
    "unknown combo #4 (dma, 2*serial)": {
        "components": ["serial-su16550", "serial-su16550", "dma-isadma"],
    },
    "unknown combo #5 (ce,ebus,eri,firewire,usb)": {
        "components": [
            "SUNW,pci-ce",
            "pci108e,1100",
            "SUNW,pci-eri",
            "firewire-pci108e,1102",
            "usb-pci108e,1103",
        ],
    },
    "unknown combo #6 (ebus, eri, firewire, usb)": {
        "components": [
            "pci108e,1100",
            "SUNW,pci-eri",
            "firewire-pci108e,1102",
            "usb-pci108e,1103",
        ],
    },
    "unknown combo #7 (dma, 2*serial)": {
        "components": [
            "serial-su16550",
            "serial-su16550",
            "dma-isadma",
            "serial-su16550",
            "serial-su16550",
            "dma-isadma",
        ],
    },
    "unknown combo #8 (ce*2, scsi*2)": {
        "components": [
            "SUNW,pci-ce",
            "SUNW,pci-ce",
            "scsi-pci1000,b",
            "scsi-pci1000,b",
        ],
    },
    "unknown combo #9 (eri, usb, fca)": {
        "components": ["SUNW,pci-eri", "usb-pci108e,1103", "SUNW,qlc-pci1077,2300"],
    },
    "unknown combo #10 (hme, 3de7)": {
        "components": ["pci108e,3de7", "SUNW,hme"],
    },
    "unknown combo #11 (ce*2, scsi*2)": {
        "components": [
            "SUNW,pci-ce",
            "SUNW,pci-ce",
            "scsi-pci1000,b",
            "scsi-pci1000,b",
        ],
    },
    "unknown combo #12 (hme, 3de7)": {
        "components": ["pci1095,646", "SUNW,hme"],
    },
    "unknown combo #13 (qfe, scsi*2)": {
        "components": ["scsi-pci1000,f.", "scsi-pci1000,f.", "SUNW,pci-qfe"],
    },
    "unknown combo #14 (hba*2)": {
        "components": ["pci10df,fa00", "pci10df,fa00"],
    },
    "unknown combo #15 (gig*2, scsi*2)": {
        "components": ["pci1000,21", "pci1000,21", "pci14e4,1648", "pci14e4,1648"],
    },
    "unknown combo #16 (ce, scsi*2)": {
        "components": ["pci1000,21", "pci1000,21", "SUNW,pci-ce"],
    },
    "unknown combo #17 (hme, scsi*2)": {
        "components": ["SUNW,hme", "Symbios,53C875", "Symbios,53C875"],
    },
    "unknown combo #18 (ata, scsi*2)": {
        "components": ["scsi-pci1000,30", "scsi-pci1000,30", "pci1095,680"],
    },
    "unknown combo #19 (hme,scsi)": {
        "components": ["SUNW,hme", "QLGC,ISP1040B"],
    },
    "unknown combo #20 (hba*2)": {
        "components": ["lpfc-pci10df,f980", "lpfc-pci10df,f980"]
    },
    "unknown combo #21 (ce*2)": {
        "components": ["SUNW,pci-ce", "SUNW,pci-ce"],
    },
    "unknown combo #22 (scsi*2)": {
        "components": ["scsi-pci1000,f", "scsi-pci1000,f"],
    },
    "unknown combo #23 (hme*2, scsi*2)": {
        "components": ["Symbios,53C875", "Symbios,53C875", "SUNW,hme", "SUNW,hme"],
    },
    "unknown combo #24 (hba*2)": {
        "components": ["SUNW,qlc-pci1077,2300", "SUNW,qlc-pci1077,2300"]
    },
    "unknown combo #25 (hba*2)": {"components": ["QLA2462", "QLA2462"]},
    "unknown combo #26 (network*4, scsi*2)": {
        "components": [
            "pci108e,1648",
            "pci108e,1648",
            "pci108e,1648",
            "pci108e,1648",
            "pci10df,fa00",
            "pci10df,fa00",
        ]
    },
    "unknown combo #27 (network*4, scsi*2)": {
        "components": [
            "pci108e,1648",
            "pci108e,1648",
            "pci108e,1648",
            "pci108e,1648",
            "pci1000,21",
            "pci1000,21",
        ]
    },
    "unknown combo #28 (hba*4)": {
        "components": [
            "pciex1077,2432",
            "pciex1077,2432",
            "pciex1077,2432",
            "pciex1077,2432",
        ]
    },
    "unknown combo #29 (hba, nic*2)": {
        "components": ["pci1000,50", "pci14e4,1648", "pci14e4,1648"]
    },
    "unknown combo #30 (hba*2)": {"components": ["FCX2-6562", "FCX2-6562"]},
    "unknown combo #31 (hba*2)": {
        "components": ["SUNW,qlc-pci1077,2422", "SUNW,qlc-pci1077,2422"]
    },
    "unknown combo #32 (hba*2)": {
        "components": ["fibre-channel-pci10df,f980", "fibre-channel-pci10df,f980"]
    },
}

##########################################################################

# EOF
