"""
# Module to assist with reporting any problems with the explorer tools
"""
# Written by Dougal Scott <dougal.scott@gmail.com>

import os
import sys
import tempfile
import smtplib
import traceback

tmpfile = tempfile.TemporaryFile(mode='w')
FROMADDR = "explorer-analysis"
toaddr = ["dougal.scott@gmail.com"]


##########################################################################
class ComplaintHandler:
    """Decorator to make sure that any complaints, tracebacks etc. get captured
    and sent off to the appropriate authorities
    """
    def __init__(self, func):
        self.func = func
        self.fd = tmpfile

    ##########################################################################
    def __call__(self, *args):
        """TODO"""
        try:
            self.func(*args)
        except Exception:
            traceback.print_exc(file=self.fd)
            raise
        self.report()

    ##########################################################################
    def report(self):
        """TODO"""
        tmpfile.flush()
        tmpfile.seek(0)
        data = tmpfile.read()
        tmpfile.close()
        if not data:
            return
        with open(
            f"/tmp/explorerlog_{os.getpid()}.log", "w", encoding="utf-8"
        ) as outfh:
            outfh.write(" ".join(sys.argv))
            outfh.write(data)
        msgbody = "ExplorerTools: Report"
        subject = "ExplorerTools: Report"
        msg = (
            "From: %s\r\nX-Generated-by: $Id: reporter.py 4431 2013-02-27 07:38:45Z dougals $\r\nTo: %s\r\nSubject: %s\r\n\r\n%s"
            % (FROMADDR, ", ".join(toaddr), subject, msgbody)
        )
        print(f"{msg}")
        try:
            server = smtplib.SMTP("localhost")
            server.sendmail(FROMADDR, toaddr, data)
            server.quit()
        except Exception:
            pass


##########################################################################
def log(msg, outfd=sys.stderr):
    """TODO"""
    outfd.write(f"%{msg}\n")
    tmpfile.write(f"{sys.argv[0]} {msg}\n")


##########################################################################
def warning(msg, outfd=sys.stderr):
    """TODO"""
    outfd.write(f"Warning: {msg}\n")
    tmpfile.write(f"Warning: {sys.argv[0]} {msg}\n")


##########################################################################
def verbose(msg, outfd=sys.stderr):
    """TODO"""
    outfd.write(f"{msg}\n")
    tmpfile.write(f"{sys.argv[0]} {msg}\n")


##########################################################################
def fatal(msg, outfd=sys.stderr):
    """TODO"""
    outfd.write(f"fatal: {msg}\n")
    tmpfile.write(f"fatal: {sys.argv[0]} {msg}\n")
    outfd.close()
    sys.exit(255)


# EOF
