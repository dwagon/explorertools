"""
Drivemap for explorer analysis parts list
"""
# Written by Dougal Scott <dwagon@pobox.com>
# Used by prtdiag
# pylint: disable=too-many-lines
drivemap = {
    # Arrays that are actually separate devices
    "BladeCtlr B210": {
        "desc": "BladeCtlr B210",
        "protected": "Raid Array",
        "nickname": "Array LUN",
    },
    "BladeCtlr BC82": {
        "desc": "BladeCtlr BC82",
        "protected": "Raid Array",
        "nickname": "Array LUN",
    },
    "Emc SYMMETRIX": {"protected": "SAN", "nickname": "SAN volume"},
    "LUN": {"protected": "HW Raid", "nickname": "SAN volume"},
    "LUNZ": {"protected": "HW Raid", "nickname": "SAN volume"},
    "NETAPP LUN": {"protected": "NAS", "nobackupslice": True, "nickname": "SAN volume"},
    "OPEN-E      -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-E": {"protected": "SAN", "nobackupslice": True, "nickname": "SAN volume"},
    "OPEN-E*3": {"protected": "SAN", "nobackupslice": True, "nickname": "SAN volume"},
    "OPEN-V      -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V": {"protected": "SAN", "nobackupslice": True, "nickname": "SAN volume"},
    "OPEN-V-CM": {"protected": "SAN", "nobackupslice": True, "nickname": "SAN volume"},
    "HITACHI OPEN-V": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "HITACHI OPEN-V*2": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "HITACHI OPEN-V*3": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "HITACHI OPEN-V*4": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "HITACHI OPEN-V*5": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "HITACHI OPEN-V*6": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "HITACHI OPEN-V*7": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "HITACHI OPEN-V*8": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*10   -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*11   -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*12   -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*13   -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*14   -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*15   -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*16   -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*17   -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*18   -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*35   -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*36   -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*2    -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*3    -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*4    -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*5    -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*6    -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*7    -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*8    -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPEN-V*9    -SUN": {
        "protected": "SAN",
        "nobackupslice": True,
        "nickname": "SAN volume",
    },
    "OPENstorage D173": {
        "protected": "Raid Array",
        "nobackupslice": True,
        "nickname": "Array LUN",
    },
    "OPENstorage D220": {
        "protected": "Raid Array",
        "nobackupslice": True,
        "nickname": "Array LUN",
    },
    "OPENstorage D280": {
        "protected": "Raid Array",
        "nobackupslice": True,
        "nickname": "Array LUN",
    },
    "STK RAID INT": {"protected": "HW Raid"},
    "SYMMETRIX": {"protected": "SAN", "nobackupslice": True, "nickname": "SAN volume"},
    "StorEDGE A1000": {"protected": "Raid Array", "nickname": "Array LUN"},
    "StorEdge 3310": {
        "protected": "Raid Array",
        "nobackupslice": True,
        "nickname": "Array LUN",
    },
    "StorEdge 3510": {
        "protected": "Raid Array",
        "nobackupslice": True,
        "nickname": "Array LUN",
    },
    "StorEdge 3511": {
        "protected": "Raid Array",
        "nobackupslice": True,
        "nickname": "Array LUN",
    },
    "CSM100_R_FC": {
        "protected": "Raid Array",
        "nobackupslice": True,
        "nickname": "Array LUN",
    },
    "StorEdge": {
        "protected": "Raid Array",
        "nobackupslice": True,
        "nickname": "Array LUN",
    },
    "T300": {"protected": "T300 Array", "nobackupslice": True, "nickname": "Array LUN"},
    "HSV210": {
        "protected": "HP EVA Array",
        "nobackupslice": True,
        "nickname": "HP SAN Volume",
    },
    "HP HSV210": {
        "protected": "HP EVA Array",
        "nobackupslice": True,
        "nickname": "HP SAN Volume",
    },
    "LCSM100_F": {"protected": "Array", "nobackupslice": True, "nickname": "Array LUN"},
    # Internal hardware raid
    "Ibm SERVERAID": {"protected": "Raid Array (Redundant?)"},
    "Lsilogic 1030 IM       IM": {"protected": "Raid Array (Redundant?)"},
    "Lsilogic 1030          IM": {"protected": "Raid Array (Redundant?)"},
    "Lsilogic 1030 IM": {"protected": "Raid Array (Redundant?)"},
    "RAID 10": {"protected": "HW Raid"},
    "RAID 5": {"protected": "HW Raid"},
    "Servera RAID 5": {"protected": "Raid Array (Redundant?)"},
    "Servera RAID1": {"protected": "Raid Array (Redundant?)"},
    # Virtualised devices from X4100 etc. No idea about the physical
    "Ami Virtual Floppy": {"fake": True},
    "Compaq RAID logical disk": {"protected": "Raid Array (Redundant?)"},
    "Logical Volume": {"protected": "Raid Array (Redundant?)"},
    "Lsi Logical Volume": {"protected": "Raid Array (Redundant?)"},
    "Lsilogic Logical Volume": {"protected": "Raid Array (Redundant?)"},
    "Remote Disk": {"fake": True},
    "Virtual CDROM": {"fake": True},
    "Virtual Floppy": {"fake": True},
    "Vmware Virtual disk": {"protected": "Base hardware (Redundant?)"},
    "Ami Virtual CDROM": {"fake": True},
    "AMI Virtual CDROM": {"fake": True},
    "VMware Virtual IDE CDROM Drive": {"fake": True},
    "VMware Virtual disk": {"fake": True},
    "HP Virtual CD-ROM": {"fake": True},
    "HP Virtual DVD-ROM": {"fake": True},
    "VIRTUALCDROM DRIVE": {"fake": True},
    # Tape Drives
    "03592J1A": {
        "desc": "Unknown IBM Tape Drive",
    },
    "3573-TL": {
        "desc": "IBM 3573 Tape Library",
    },
    "4560SLX": {
        "desc": "IBM 4560 Tape Library",
    },
    "C1537A": {
        "desc": "DDS-3 Tape Drive",
        "part": "370-2376",
        "option": "X6912A",
    },
    "C1557A": {"desc": "DDS-3 Tape Drive"},
    "C5683A": {
        "desc": "DDS-4 DAT Tape Drive",
        "part": "390-0027",
    },
    "C7438A": {
        "desc": "HP C7438A DDS-3 Tape Drive",
    },
    "DLT8000": {"desc": "DLT8000 Tape Drive", "option": "CPQ 40/80GB DLT"},
    "SDLT320": {
        "desc": "DLT 320 Tape Drive",
    },
    "SDLT600": {
        "desc": "DLT 600 Tape Drive",
    },
    "SuperDLT1": {
        "desc": "Suprt DLT Tape Drive",
    },
    "ULT3580-TD3": {
        "desc": "LTO3 Tape Drive",
    },
    "ULTRIUM-TD2": {"desc": "Ultrium 2 Tape Drive"},
    "Ultrium 1-SCSI": {
        "desc": "Ultrium 1 Tape Drive",
    },
    "Ultrium 2-SCSI": {
        "desc": "Ultrium 2 Tape Drive",
    },
    "Ultrium 3-SCSI": {
        "desc": "Ultrium 3 Tape Drive",
    },
    "Ultrium-TD3": {
        "desc": "Ultrium 3 Tape Drive",
    },
    "DLT7000": {"desc": "DLT7000 Tape Drive", "part": "599-2127"},
    "T9940B": {"desc": "T9940B Tape Drive"},
    "T10000A": {"desc": "T10000A Tape Drive"},
    # CD/DVD Drives
    "ATAPI CD-ROM52XMAX": {"desc": "52x CD-ROM"},
    "CD-224E": {
        "desc": "24X Slimline CD-ROM",
        "part": "370-4278",
    },
    "CD-ROM CRD-8240B": {
        "desc": "CD-ROM CRD-8240B",
    },
    "CD-ROM CRD-8322B": {
        "desc": "32X EIDE CD-ROM",
        "part": "370-3694",
        "option": "X6171A",
    },
    "CD-ROM CRN-8245B": {
        "desc": "24x CD-ROM Drive",
    },
    "CD-ROM LTN485S": {"desc": "48X EIDE CD-ROM", "part": "370-4152"},
    "CD-ROM LTN486S": {
        "desc": "48X EIDE CD-ROM",
        "part": "370-4152",
    },
    "CD-ROM SN-124": {
        "desc": "Slimline 24X CD-ROM",
        "part": "370-6042",
        "option": "X5130A",
    },
    "CD-ROM SR244W": {
        "desc": "CD-ROM SR244W",
    },
    "CD-ROM XM-1902B": {
        "desc": "CD-ROM Drive",
        "part": "540-4179",
        "option": "X6971A",
    },
    "CD-ROM XM-7002Bc": {
        "desc": "CD-ROM Drive",
        "part": "540-4179",
        "option": "X6971A",
    },
    "CD-RW  CW-8124": {
        "desc": "8x DVD-DROM",
        "part": "390-0320",
    },
    "CD/DVDW TS-H652D": {
        "desc": "DVD-ROM",
        "part": "541-2478",
    },
    "CD/DVDW TS-H552D": {
        "desc": "16X DVD-ROM Writer / 48X CD-ROM Writer",
        "part": "541-1840",
    },
    "CD/DVDW TS-L632D": {
        "desc": "Slimline 8X DVD-ROM",
        "part": "370-4412",
    },
    "CD/DVDW TS-T632A": {
        "desc": "DVD-Writer/CD-Writer",
        "part": "541-2110",
        "option": "X6323A",
    },
    "COMPAQ CD-ROM SN-124": {
        "desc": "Slimline 24X CD-ROM",
        "part": "370-6042",
        "option": "X5130A",
    },
    "DV-28E-B": {
        "desc": "Internal Slimline 8X DVD-ROM",
        "part": "540-5014",
        "option": "X7288A",
    },
    "DV-28E-C": {
        "desc": "Internal Slimline DVD-ROM",
        "option": "X7410A",
        "part": "370-5128",
    },
    "DV-28E-N": {
        "desc": "Interal 8x slimline DVD-ROM",
        "part": "371-1108",
        "option": "X7410A",
    },
    "DV-28SL": {
        "desc": "Slimline ATAPI/IDE DVD-ROM",
        "part": "540-6368",
        "option": "8030A",
    },
    "DV-28S-V": {"desc": "Slimline ATAPI/IDE DVD-ROM"},
    "DV-W28SS-V": {"desc": "SATA DVD-Writer"},
    "TEAC DV-28S-V": {"desc": "Slimline ATAPI/IDE DVD-ROM"},
    "DVD-RAM UJ-841S": {
        "desc": "DVD-RAM UJ-841S",
    },
    "DVD-RAM UJ-845": {
        "desc": "DVD-RAM UJ-845",
    },
    "DVD-RAM UJ-845S": {
        "desc": "DVD-RAM UJ-845S",
    },
    "DVD-RAM UJ-875S": {
        "desc": "DVD-RAM UJ-875S",
    },
    "DVD-RAM UJ875AS": {"desc": "DVD-RAM UJ-875AS", "part": "371-4234"},
    "DVD-RAM UJ-85JS": {
        "desc": "8x DVD-Writer/CD-Writer",
        "part": "Unknown",
        "option": "X8410A-Z",
    },
    "DVD-ROM GDR8082N": {
        "desc": "Slimline DVD-ROM",
        "part": "GDR-8082N",
    },
    "DVD-ROM SD-C2512": {
        "desc": "Slimline 8X DVD-ROM/24X CD-ROM",
        "part": "370-4412",
    },
    "DVD-ROM SD-C2612": {
        "desc": "8X DVD-ROM Drive Assembly",
        "part": "540-5596",
    },
    "DVD-ROM SD-M1401": {
        "desc": "10X DVD-ROM Drive",
        "part": "390-0025",
        "option": "X6168A",
    },
    "DVD-ROM SD-M1711": {
        "desc": "10X DVD-ROM Drive",
        "part": "390-0025",
    },
    "DVD-ROM SD-M1712": {
        "desc": "DVD-ROM Assembly",
        "part": "541-2478",
    },
    "DVD-ROM SR-8177": {
        "desc": "Internal Slimline DVD-ROM",
        "part": "X7410A",
        "option": "370-5128",
    },
    "DVD-ROM SR-8178": {
        "desc": "DVD-ROM Drive",
        "part": "371-2283",
        "option": "X5294A-Z",
    },
    "DVD-ROM TS-H352C": {
        "desc": "16X ATAPRI DVD-ROM Drive",
        "part": "390-0346",
    },
    "DVD-ROM TS-L462C": {
        "desc": "8x DVD-ROM/ 24X CD-ROM",
        "part": "370-4412",
    },
    "DVDRW SHM-165P6S": {
        "desc": "DVD Drive",
    },
    "DW-224SL-R": {
        "desc": "8x DVD-ROM/24x CD-Writer",
        "part": "X8049A-Z",
        "option": "390-0320",
    },
    "HL-DT-ST CD-ROM GCR-8482B": {
        "desc": "GCR-8482B CD-ROM",
    },
    "HL-DT-STCD-RW/DVD DRIVE GCC-4244N": {
        "desc": "24x CD-RW/DVD Drive",
        "part": "Unknown",
    },
    "HL-DT-STCD-RW/DVD DRIVE GCC-T10N": {"desc": "GCC-T10N DVD-ROM"},
    "HL-DT-STDVD-ROM GDR8082N": {
        "desc": "Slimline DVD-ROM",
        "part": "GDR-8082N",
    },
    "HL-DT-ST DVD-ROM GDR-8084N": {
        "desc": "Slimline DVD-ROM",
        "part": "GDR-8084N",
    },
    "Hl-dt-st DVD-ROM GDR8082N": {
        "desc": "Slimline DVD-ROM",
        "part": "GDR-8082N",
    },
    "Hl-dt-st RW/DVD GCC-4244N": {
        "desc": "24x CD-RW/DVD Drive",
        "part": "Unknown",
    },
    "LG CD-ROM CRN-8245B": {
        "desc": "24x CD-ROM Drive",
    },
    "Lg CD-ROM CRN-8245B": {
        "desc": "24x CD-ROM Drive",
    },
    "CD/DVD TS-L532U": {
        "desc": "Slimline 8x DVD-ROM / 24x CD-ROM",
        "part": "370-4412",
    },
    "CD/DVDW TS-L532U": {
        "desc": "Slimline 8x DVD-ROM / 24x CD-ROM",
        "part": "370-4412",
    },
    "MATSHITACD-RW CW-8124": {
        "desc": "8x DVD-DROM",
        "part": "390-0320",
    },
    "MATSHITADVD-ROM SR-8177": {
        "desc": "Internal Slimline DVD-ROM",
        "part": "X7410A",
        "option": "370-5128",
    },
    "ODD-DVD SD-C2732": {
        "desc": "Slimline 8X DVD-ROM/ 24X CD-ROM",
        "part": "370-4412",
    },
    "RW/DVD GCC-4244N": {
        "desc": "24x CD-RW/DVD Drive",
        "part": "Unknown",
    },
    "SAMSUNG CD-ROM SN-124": {
        "desc": "Slimline 24X CD-ROM",
        "part": "370-6042",
        "option": "X5130A",
    },
    "TEAC CD-224E": {
        "desc": "24X Slimline CD-ROM",
        "part": "370-4278",
    },
    "DW-224E-C": {
        "desc": "24X Slimline CD-ROM",
    },
    "HL-DT-ST DVD-ROM GDR-H30N": {
        "desc": "16X DVD-ROM",
    },
    "Tsstcorp CD/DVDW TS-T632A": {
        "desc": "DVD-Writer/CD-Writer",
        "part": "541-2110",
        "option": "X6323A",
    },
    "XM5701TASUN12XCD": {"desc": "SunCD 12 CD-Drive", " part": "370-2817"},
    "XM6201TASUN32XCD": {"desc": "SunCD 32 CD-ROM", "part": "370-3416"},
    "DVD A  DS8A5LH": {"desc": "DVD+RW"},
    "hp DVD A  DS8A5LH": {"desc": "DVD+RW"},
    # USB amd Floppy Drives
    "FD-05PUB": {
        "desc": "Floppy Drive",
        "part": "FD-05PUB",
    },
    "Teac FD-05PUB": {
        "desc": "Floppy Drive",
        "part": "FD-05PUB",
    },
    "Rugged FW/USB": {
        "desc": "USB Drive",
        "part": "unknown",
    },
    # And every drive known to man
    # 2 Gb
    "DCAS32160SUN2.1G": {
        "desc": "2.1GB - 5400 RPM Disk Drive",
        "part": "540-3171",
        "option": "X5175A",
        "nickname": "2GB",
    },
    "ST32550W SUN2.1G": {
        "desc": "2.1GB - 7200 RPM Disk Drive",
        "part": "540-2730",
        "option": "X5153A",
        "nickname": "2GB",
    },
    "VK2275J  SUN2.1G": {
        "desc": "2.1GB - 7200 RPM Disk Drive",
        "part": "540-2730",
        "option": "X5153A",
        "nickname": "2GB",
    },
    # 4 Gb
    "DDRS34560SUN4.2G": {
        "desc": "4.2Gb 7200 RPM Disk Drive",
        "part": "540-2938",
        "option": "X5214A",
        "nickname": "4GB",
    },
    "MAB3045S SUN4.2G": {
        "desc": "4.2Gb 7200 RPM Disk Drive",
        "part": "540-2938",
        "option": "X5214A",
        "nickname": "4GB",
    },
    "RZ1CB-CS (C) DEC": {"desc": "4.3Gb 7200 RPM SCSI Drive", "nickname": "4GB"},
    "RZ29B    (C) DEC": {"desc": "4.3Gb 7200 RPM SCSI Drive", "nickname": "4GB"},
    "ST15230W SUN4.2G": {"desc": "ST15230W SUN4.2G", "nickname": "4GB"},
    "ST34371W SUN4.2G": {
        "desc": "4.2Gb 7200 RPM Disk Drive",
        "part": "540-2938",
        "option": "X5214A",
        "nickname": "4GB",
    },
    # 9 Gb
    "DDRS39130SUN9.0G.0G": {
        "desc": "9.1Gb disk",
        "part": "unknown",
        "option": "unknown",
        "nickname": "9GB",
    },
    "DNES30917SUN9.0G": {
        "desc": "9.1Gb - 7200 RPM Ultra-1 SCSI disk",
        "part": "540-3704",
        "option": "X5229A",
        "nickname": "9GB",
    },
    "MAB3091S SUN9.0G": {
        "desc": "9.1Gb - 7200 RPM Ultra-1 SCSI disk",
        "part": "540-3704",
        "option": "X5229A",
        "nickname": "9GB",
    },
    "MAE3091L SUN9.0G": {
        "desc": "9.1Gb - 7200 RPM Ultra-1 SCSI disk",
        "part": "540-3704",
        "option": "X5229A",
        "nickname": "9GB",
    },
    "MAG3091L SUN9.0G": {
        "desc": "9.1Gb - 10000 RPM disk",
        "option": "X5234A",
        "part": "370-3649",
        "nickname": "9GB",
    },
    "ST19171FCSUN9.0G": {
        "desc": "9.1Gb - 7200 RPM FC-AL Disk Drive",
        "part": "540-3852",
        "option": "X6709A",
        "nickname": "9GB",
    },
    "ST19171W SUN9.0G": {
        "desc": "9.1Gb - 7200 RPM Disk Drive",
        "part": "540-2951",
        "option": "X5251A",
        "nickname": "9GB",
    },
    "ST39102LCSUN9.0G": {
        "desc": "9.1Gb - 10000 RPM disk",
        "part": "370-3649",
        "option": "X5234A",
        "nickname": "9GB",
    },
    "ST39103FCSUN9.0G": {
        "desc": "9.1Gb - 10000 RPM FC-AL Disk Drive",
        "part": "540-3869",
        "option": "X6710A",
        "nickname": "9GB",
    },
    "ST39103LCSUN9.0G": {
        "desc": "9.1Gb - 10000 RPM disk",
        "part": "370-3649",
        "option": "X5234A",
        "nickname": "9GB",
    },
    "ST39140A": {
        "desc": "9.1Gb - 7200 RPM EIDE Disk Drive",
        "part": "370-3693",
        "option": "X5236A",
        "nickname": "9GB",
    },
    "ST39173W SUN9.0G": {
        "desc": "9.1Gb - 7200 RPM Ultra-1 SCSI disk",
        "part": "540-3704",
        "option": "X5229A",
        "nickname": "9GB",
    },
    "ST39204LCSUN9.0G": {
        "desc": "9.1Gb - 10000 RPM disk",
        "option": "X5234A",
        "part": "370-3649",
        "nickname": "9GB",
    },
    # 15 Gb
    "ST315310A": {
        "desc": "15Gb 7200 RPM Ultra ATA Drive",
        "part": "370-4154",
        "option": "X6172A",
        "nickname": "15GB",
    },
    "ST315320A": {
        "desc": "15Gb 7200 RPM Ultra ATA Drive",
        "part": "370-4154",
        "option": "X6172A",
        "nickname": "15GB",
    },
    # 18 Gb
    "DDYST1835SUN18G": {
        "desc": "18.2Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4177",
        "option": "X5237A",
        "nickname": "18GB",
    },
    "MAA3182S SUN18G": {
        "desc": "18.2Gb 7200 RPM Disk Drive",
        "part": "540-3719",
        "option": "X5232A",
        "nickname": "18GB",
    },
    "MAG3182L SUN18G": {
        "desc": "18.2Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4177",
        "option": "X5237A",
        "nickname": "18GB",
    },
    "MAJ3182M SUN18G": {
        "desc": "18.2Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4177",
        "option": "X5237A",
        "nickname": "18GB",
    },
    "MAN3184M SUN18G": {
        "desc": "18.2Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4177",
        "option": "X5237A",
        "nickname": "18GB",
    },
    "ST318203LSUN18G": {
        "desc": "18.2Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4177",
        "option": "X5237A",
        "nickname": "18GB",
    },
    "ST318203FSUN18G": {
        "desc": "18.2Gb - 10000 RPM FC-AL Disk Drive",
        "part": "540-4673",
        "option": "X6728A",
        "nickname": "18GB",
    },
    "ST318305LSUN18G": {
        "desc": "18.2Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4177",
        "option": "X5237A",
        "nickname": "18GB",
    },
    "ST318404LSUN18G": {
        "desc": "18.2Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4177",
        "option": "X5237A",
        "nickname": "18GB",
    },
    "ST318404LC": {
        "desc": "18.2Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4177",
        "option": "X5237A",
        "nickname": "18GB",
    },
    # 20 Gb
    "ST320011A": {
        "desc": "20Gb 7200 RPM Ultra ATA Disk Drive",
        "part": "370-4327",
        "option": "X6174A",
        "nickname": "20GB",
    },
    "ST320413A": {"desc": "ST320413A 20Gb disk drive", "nickname": "20GB"},
    # 36 Gb
    "DK32EJ36NSUN36G": {
        "desc": "36.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4521",
        "option": "X5242A",
        "nickname": "36GB",
    },
    "MAJ3364M SUN36G": {
        "desc": "36.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4521",
        "option": "X5242A",
        "nickname": "36GB",
    },
    "MAN3367M SUN36G": {
        "desc": "36.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4521",
        "option": "X5242A",
        "nickname": "36GB",
    },
    "ST336605LSUN36G": {
        "desc": "36.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4521",
        "option": "X5242A",
        "nickname": "36GB",
    },
    "ST336607LC": {
        "desc": "36.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4904",
        "option": "X5267A",
        "nickname": "36GB",
    },
    "ST336807LC": {"desc": "36.4Gb Disk Drive", "nickname": "36GB"},
    "ST336607LSUN36G": {
        "desc": "36.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4521",
        "option": "X5242A",
        "nickname": "36GB",
    },
    "ST336704LSUN36G": {
        "desc": "36.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4521",
        "option": "X5242A",
        "nickname": "36GB",
    },
    "Seagate ST336607LSUN36G": {
        "desc": "36.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-4521",
        "option": "X5242A",
        "nickname": "36GB",
    },
    "MAF3364L SUN36G": {
        "desc": "36.4Gb - 10000 RPM Disk Drive",
        "part": "540-4263",
        "option": "X5240A",
        "nickname": "36GB",
    },
    "MAP3367N SUN36G": {
        "desc": "36.4Gb - 10000 RPM Disk Drive",
        "part": "540-4689",
        "option": "X5244A",
        "nickname": "36GB",
    },
    "ST136403FSUN36G": {
        "desc": "36.4Gb - 10000 RPM FC-AL Disk Drive",
        "part": "540-4525",
        "option": "X6724A",
        "nickname": "36GB",
    },
    "ST33607LSUN36G": {"desc": "ST33607LSUN36G", "nickname": "36GB"},
    "ST336605FSUN36G": {
        "desc": "36.4Gb - 10000 RPM FC-AL Disk Drive",
        "part": "540-4525",
        "option": "X6724A",
        "nickname": "36GB",
    },
    "ST336607FSUN36G": {
        "desc": "36.4Gb - 10000 RPM FC-AL Disk Drive",
        "part": "540-4525",
        "option": "X6724A",
        "nickname": "36GB",
    },
    "ST336704FSUN36G": {
        "desc": "36.4Gb - 10000 RPM FC-AL Disk Drive",
        "part": "540-4525",
        "option": "X6724A",
        "nickname": "36GB",
    },
    "Ibm-esxs MAU3036NC     FN": {
        "desc": "36Gb 15000 RPM Ultra-320 Disk Drive",
        "part": "Unknown",
        "nickname": "36GB",
    },
    "1030 IM       IM": {
        "desc": "Unknown 36.4Gb 10000 RPM Ultra-320 Disk Drive",
        "part": "540-5462",
        "option": "X5261A",
        "nickname": "36GB",
    },
    "ST336704FC": {
        "desc": "36.4Gb - 10000 RPM FC-AL Disk Drive",
        "part": "540-4525",
        "option": "X6724A",
        "nickname": "36GB",
    },
    # 40 Gb
    "ST340014A": {
        "desc": "40.0Gb - 7200 RPM disk",
        "part": "370-4419",
        "option": "X7096A",
        "nickname": "40GB",
    },
    "WDC WD400BB-22DE": {
        "desc": "40.0Gb - 7200 RPM disk",
        "part": "370-4419",
        "option": "X7096A",
        "nickname": "40GB",
    },
    "ST340016A": {
        "desc": "40.0Gb - 7200 RPM disk",
        "part": "370-4419",
        "option": "X7096A",
        "nickname": "40GB",
    },
    "ST340824A": {
        "desc": "40.0Gb - 7200 RPM disk",
        "part": "370-4419",
        "option": "X7096A",
        "nickname": "40GB",
    },
    # 72 Gb
    "DK32EJ72FSUN72G": {
        "desc": "73.4Gb 10000 RPM FC-AL",
        "part": "390-0123",
        "nickname": "72GB",
    },
    "DK32EJ72NSUN72G": {
        "desc": "73.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-6600",
        "option": "XRA-SC1CB-73G10K",
        "nickname": "72GB",
    },
    "HUS10733ASUN72G": {
        "desc": "73.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-6600",
        "option": "XRA-SC1CB-73G10K",
        "nickname": "72GB",
    },
    "HUS1073FASUN72G": {
        "desc": "73.4Gb - 10000 RPM FC-AL Disk Drive",
        "part": "540-6604",
        "option": "X6805A",
        "nickname": "72GB",
    },
    "Ibm-esxs MAP3735NC     FN": {
        "desc": "73.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-6600",
        "option": "XRA-SC1CB-73G10K",
        "nickname": "72GB",
    },
    "Ibm-esxs MAT3073NC     FN": {
        "desc": "73.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-6600",
        "option": "XRA-SC1CB-73G10K",
        "nickname": "72GB",
    },
    "Ibm-esxs MAW3073NC     FN": {
        "desc": "73.5Gb 10000 RPM Ultra-320 Disk Drive",
        "part": "Unknown",
        "nickname": "72GB",
    },
    "Ibm-esxs ST373453LC    FN": {
        "desc": "ST373453LC",
        "part": "540-5924",
        "nickname": "72GB",
    },
    "MAN3735F SUN72G": {
        "desc": "73.4Gb - 10000 RPM FC-AL Disk Drive",
        "part": "595-6374",
        "option": "X6756A",
        "nickname": "72GB",
    },
    "MAP3735F SUN72G": {
        "desc": "73.4Gb 10000 RPM FC-AL",
        "part": "540-5408",
        "option": "X6808A",
        "nickname": "72GB",
    },
    "MAP3735N SUN72G": {
        "desc": "73.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-6600",
        "option": "XRA-SC1CB-73G10K",
        "nickname": "72GB",
    },
    "MAT3073F SUN72G": {
        "desc": "73.4Gb 10000 RPM FC-AL",
        "part": "540-5408",
        "option": "X6808A",
        "nickname": "72GB",
    },
    "MAT3073N SUN72G": {
        "desc": "73.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-6600",
        "option": "XRA-SC1CB-73G10K",
        "nickname": "72GB",
    },
    "MAV2073RCSUN72G": {
        "desc": "73Gb 10000 RPM SAS Disk Drive",
        "part": "541-0323",
        "option": "XRA-SS2CD-73G10K",
        "nickname": "72GB",
    },
    "MAW3073FCSUN72G": {
        "desc": "73.4Gb - 10000 RPM FC-AL",
        "part": "540-6604",
        "option": "X6805A",
        "nickname": "72GB",
    },
    "MAW3073NCSUN72G": {
        "desc": "73.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-6600",
        "option": "XRA-SC1CB-73G10K",
        "nickname": "72GB",
    },
    "MAY2073RCSUN72G": {
        "desc": "73Gb 10000 RPM SAS Drive",
        "part": "540-6643",
        "option": "XRA-SS2ND-73G10K",
        "nickname": "72GB",
    },
    "H101473SCSUN72G": {"desc": "73Gb 10000 RPM SAS Drive", "nickname": "72GB"},
    "Fujitsu MAY2073RCSUN72G": {
        "desc": "73Gb 10000 RPM SAS Drive",
        "part": "540-6643",
        "option": "XRA-SS2ND-73G10K",
        "nickname": "72GB",
    },
    "ST373207FSUN72G": {
        "desc": "73.4Gb - 10000 RPM FC-AL",
        "part": "540-6604",
        "option": "X6805A",
        "nickname": "72GB",
    },
    "ST373207LSUN72G": {
        "desc": "73.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-6600",
        "option": "XRA-SC1CB-73G10K",
        "nickname": "72GB",
    },
    "ST373307FSUN72G": {
        "desc": "73.4Gb - 10000 RPM FC-AL Disk Drive",
        "part": "540-5408",
        "option": "X6808A",
        "nickname": "72GB",
    },
    "ST373307LSUN72G": {
        "desc": "73.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-6600",
        "option": "XRA-SC1CB-73G10K",
        "nickname": "72GB",
    },
    "ST373405FSUN72G": {
        "desc": "73.4Gb 10000 RPM FC-AL",
        "part": "390-0071",
        "option": "X6742A",
        "nickname": "72GB",
    },
    "ST373453LC    FN": {"desc": "ST373453LC", "part": "540-5924", "nickname": "72GB"},
    "ST373454LSUN72G": {"desc": "ST373454LSUN72G", "nickname": "72GB"},
    "ST973401LSUN72G": {
        "desc": "73Gb 10000 RPM SAS Disk Drive",
        "part": "540-6611",
        "option": "XRA-SS2CD-73G10KZ",
        "nickname": "72GB",
    },
    "Seagate ST973401LSUN72G": {
        "desc": "73Gb 10000 RPM SAS Disk Drive",
        "part": "540-6611",
        "option": "XRA-SS2CD-73G10KZ",
        "nickname": "72GB",
    },
    "ST973402SSUN72G": {
        "desc": "73Gb 10000 RPM SAS Disk Drive",
        "part": "540-6611",
        "option": "XRA-SS2CD-73G10KZ",
        "nickname": "72GB",
    },
    "SEAGATE ST973402SSUN72G": {
        "desc": "73Gb 10000 RPM SAS Disk Drive",
        "part": "540-6611",
        "option": "XRA-SS2CD-73G10KZ",
        "nickname": "72GB",
    },
    "Seagate ST373307LSUN72G": {
        "desc": "73.4Gb - 10000 RPM SCSI Disk Drive",
        "part": "540-6600",
        "option": "XRA-SC1CB-73G10K",
        "nickname": "72GB",
    },
    "Seagate ST373405LC": {
        "desc": "73.4Gb 10000 RPM Ultra-160 Disk Drive",
        "part": "Unknown",
        "nickname": "72GB",
    },
    # 80 Gb
    "Maxtor 6Y080L0": {
        "desc": "80Gb 7200 RPM ATA Disk Drive",
        "part": "Unknown",
        "nickname": "80GB",
    },
    "ST380011A": {
        "desc": "80Gb 7200 RPM ATA Disk Drive",
        "part": "Unknown",
        "nickname": "80GB",
    },
    "HITACHI HDS7280": {
        "desc": "80Gb 7200 RPM Disk Drive",
        "part": "Unknown",
        "nickname": "80GB",
    },
    "HDS728080PLA380": {
        "desc": "80Gb 7200 RPM Disk Drive",
        "part": "Unknown",
        "nickname": "80GB",
    },
    # 146 Gb
    "DK32EJ14NSUN146G": {"desc": "DK32EJ14NSUN146G", "nickname": "146GB"},
    "FUJITSU MBB2147RCSUN146G": {
        "desc": "146Gb - 10000 RPM SAS Disk Drive",
        "part": "540-7151",
        "option": "XRA-SS2CD-146G10KZ",
        "nickname": "146GB",
    },
    "H101414SCSUN146G": {
        "desc": "146Gb - 10000 RPM SAS Disk Drive",
        "part": "540-7355",
        "option": "SESX3C11Z",
        "nickname": "146GB",
    },
    "H103014SCSUN146G ": {
        "desc": "146Gb - 10000 RPM SAS Disk Drive",
        "part": "540-7868",
        "option": "XRB-SS2CF-146G10K",
        "nickname": "146GB",
    },
    "H103014SCSUN146G": {"desc": "H103014SCSUN146G", "nickname": "146GB"},
    "HUS10143ASUN146G": {"desc": "HUS10143ASUN146G", "nickname": "146GB"},
    "HUS1014FASUN146G": {
        "desc": "146Gb - 10000 RPM FC-AL Disk Drive",
        "part": "540-6605",
        "option": "XRA-FC1CB-146G10K",
        "nickname": "146GB",
    },
    "HUS15143ASUN146G": {
        "desc": "146.8 15000 RPM SCSI Disk Drive",
        "nickname": "146GB",
    },
    "HUS1514FBSUN146G": {
        "desc": "146.8 15000 RPM FC-AL Disk Drive",
        "part": "594-3779",
        "option": "X6885A",
        "nickname": "146GB",
    },
    "MAP3147N SUN146G": {
        "desc": "146.8Gb 10000 RPM Ultra-320 Disk Drive",
        "part": "540-6064",
        "nickname": "146GB",
    },
    "MAT3147F SUN146G": {
        "desc": "146Gb - 10000 RPM FC-AL Disk Drive",
        "part": "540-5459",
        "option": "X6858A",
        "nickname": "146GB",
    },
    "MAT3147N SUN146G": {
        "desc": "146.8Gb 10000 RPM Ultra-320 Disk Drive",
        "part": "540-6064",
        "nickname": "146GB",
    },
    "MAW3147FCSUN146G": {
        "desc": "146Gb - 10000 RPM FC-AL Disk Drive",
        "part": "540-6605",
        "option": "XRA-FC1CB-146G10K",
        "nickname": "146GB",
    },
    "MAW3147NCSUN146G": {
        "desc": "146.8Gb - 10000 RPM Disk Drive",
        "part": "540-6602",
        "option": "X5268A",
        "nickname": "146GB",
    },
    "MAX3147FCSUN146G": {
        "desc": "146Gb - 15000 RPM FC-AL Disk Drive",
        "part": "540-6487",
        "option": "XRA-FC1CB-146GB15KZ",
        "nickname": "146GB",
    },
    "MAX3147NCSUN146G": {
        "desc": "146Gb - 15000 RPM Ultra-320 Disk Drive",
        "part": "540-6607",
        "option": "XRA-SC1NB-146GB15KZ",
        "nickname": "146GB",
    },
    "MBB2147RC": {
        "desc": "146Gb - 10000 RPM SAS Disk Drive",
        "nickname": "146GB",
        "part": "540-7151",
        "option": "XRB-SS2CD-146G10KZ",
    },
    "MBB2147RCSUN146G": {
        "desc": "146Gb - 10000 RPM SAS Disk Drive",
        "part": "540-7151",
        "option": "XRA-SS2CD-146G10KZ",
        "nickname": "146GB",
    },
    "MBD2147RC": {"desc": "MBD2147RC", "nickname": "146GB"},
    "ST314655FSUN146G": {
        "desc": "146Gb - 15000 RPM FC-AL Disk Drive",
        "part": "540-6487",
        "option": "XRA-FC1CB-146G15KZ",
        "nickname": "146GB",
    },
    "ST314655LSUN146G": {
        "desc": "146Gb Disk Drive",
        "part": "unknown",
        "option": "unknown",
        "nickname": "146GB",
    },
    "ST3146707LC": {
        "desc": "146.8Gb - 10000 RPM Disk Drive",
        "part": "540-6602",
        "option": "X5268A",
        "nickname": "146GB",
    },
    "ST314670FSUN146G": {
        "desc": "146Gb - 10000 RPM FC-AL Disk Drive",
        "part": "540-6605",
        "option": "XRA-FC1CB-146G10K",
        "nickname": "146GB",
    },
    "ST314670LSUN146G": {
        "desc": "146.8Gb - 10000 RPM Disk Drive",
        "part": "540-6602",
        "option": "X5268A",
        "nickname": "146GB",
    },
    "ST314680FSUN146G": {
        "desc": "146Gb - 10000 RPM FC-AL Disk Drive",
        "part": "540-5459",
        "option": "X6858A",
        "nickname": "146GB",
    },
    "ST314685FSUN146G": {
        "desc": "146Gb - 15000 RPM FC-AL Disk Drive",
        "part": "540-6487",
        "option": "XRA-FC1CB-146GB15KZ",
        "nickname": "146GB",
    },
    "ST314685LSUN146G": {
        "desc": "146Gb - 15000 RPM Ultra-320 Disk Drive",
        "part": "540-6461",
        "option": "XRA-SC1CB-146GB15KZ",
        "nickname": "146GB",
    },
    "ST914602SSUN146G": {
        "desc": "146Gb - 10000 RPM SAS Disk Drive",
        "part": "540-7151",
        "option": "XRA-SS2CD-146G10KZ",
        "nickname": "146GB",
    },
    "ST914603SSUN146G": {
        "desc": "146Gb - 10000 RPM SAS Disk Drive",
        "part": "540-7864",
        "option": "XRB-SS2CD-146G10K",
        "nickname": "146GB",
    },
    # 250Gb
    "SEAGATE ST32500": {
        "desc": "250Gb Disk Drive",
        "part": "540-6485",
        "option": "250Gb - 7200 RPM SATA",
        "nickname": "250GB",
    },
    "SEAGATE ST32500N": {
        "desc": "250Gb Disk Drive",
        "part": "unknown",
        "option": "unknown",
        "nickname": "250GB",
    },
    "ATA SEAGATE ST32500N": {
        "desc": "250Gb Disk Drive",
        "part": "unknown",
        "option": "unknown",
        "nickname": "250GB",
    },
    "HITACHI HDS7225": {
        "desc": "250Gb - 7200 RPM SATA Disk Drive",
        "part": "540-6596",
        "option": "X8078A",
        "nickname": "250GB",
    },
    "HITACHI HDS7225S": {
        "desc": "250Gb - 7200 RPM SATA Disk Drive",
        "part": "540-6596",
        "option": "X8078A",
        "nickname": "250GB",
    },
    # 500 Gb disks
    "HITACHI HDS7250S": {
        "desc": "500Gb - 7200 RPM SATA Disk Drive",
        "part": "541-1467",
        "option": "XTA-ST1NG-500G7K",
        "nickname": "500GB",
    },
    "HITACHI HUA7250S": {
        "desc": "500Gb - 7200 RPM SATA Disk Drive",
        "part": "541-1467",
        "option": "XTA-ST1NG-500G7K",
        "nickname": "500GB",
    },
    # 600 Gb disks
    "ST960005SSUN600G": {
        "desc": "600Gb - 10000RPM RPM SAS Disk",
        "part": "542-0287",
        "option": "SE6X3K11Z",
        "nickname": "600GB",
    },
    "H106060SDSUN600G": {
        "desc": "600Gb - 10000RPM RPM SAS Disk",
        "part": "542-0287",
        "option": "SE6X3K11Z",
        "nickname": "600GB",
    },
    # Unknown
    "IC35L036UCD210-0": {
        "desc": "Unknown Drive IC35L036UCD210-0",
    },
    "Ibm-esxs DTN036C3UCDY10FN": {
        "desc": "Unknown Drive IBM DTN036",
        "part": "Unknown",
    },
    "Ibm-esxs DTN073C3UCDY10FN": {
        "desc": "Unknown Drive IBM DTN073",
        "part": "Unknown",
    },
    "Universal Xport": {
        "desc": "Unknown Drive Universal Xport",
    },
    "WDC WD800JB-00CRA1": {
        "desc": "Unknown Drive WDC WD800JB-00CRA1",
        "part": "Unknown",
    },
}
