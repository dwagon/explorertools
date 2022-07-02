#!/usr/bin/env python
#
# Module to assist with reporting any problems with the explorer tools
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: reporter.py 4431 2013-02-27 07:38:45Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/reporter.py $

import os
import sys
import tempfile
import smtplib
import traceback

tmpfile = tempfile.TemporaryFile()
fromaddr = "explorer-analysis"
toaddr = ["dougal.scott@gmail.com"]


##########################################################################
class ComplaintHandler:
    """Decorator to make sure that any complaints, tracebacks etc. get captured
    and sent off to the appropriate authorities
    """
    def __init__(self, fn):
        self.fn = fn
        self.fd = tmpfile

    ##########################################################################
    def __call__(self, *args):
        """ TODO """
        try:
            self.fn(*args)
        except Exception:
            traceback.print_exc(file=self.fd)
            raise
        self.report()

    ##########################################################################
    def report(self):
        """ TODO """
        tmpfile.flush()
        tmpfile.seek(0)
        data = tmpfile.read()
        tmpfile.close()
        if not data:
            return
        with open(f"/tmp/explorerlog_{os.getpid()}.log", "w", encoding="utf-8") as outfh:
            outfh.write("%s\n" % " ".join(sys.argv))
            outfh.write(data)
        msgbody = "ExplorerTools: Report"
        subject = "ExplorerTools: Report"
        msg = (
            "From: %s\r\nX-Generated-by: $Id: reporter.py 4431 2013-02-27 07:38:45Z dougals $\r\nTo: %s\r\nSubject: %s\r\n\r\n%s"
            % (fromaddr, ", ".join(toaddr), subject, msgbody)
        )
        print(f"{msg}")
        try:
            server = smtplib.SMTP("localhost")
            server.sendmail(fromaddr, toaddr, data)
            server.quit()
        except Exception:
            pass


##########################################################################
def Log(msg, fd=sys.stderr):
    """ TODO """
    fd.write("%s\n" % msg)
    tmpfile.write("%s %s\n" % (sys.argv[0], msg))


##########################################################################
def Warning(msg, fd=sys.stderr):
    """ TODO """
    fd.write("Warning: %s\n" % msg)
    tmpfile.write("Warning: %s %s\n" % (sys.argv[0], msg))


##########################################################################
def Verbose(msg, fd=sys.stderr):
    """ TODO """
    fd.write("%s\n" % msg)
    tmpfile.write("%s %s\n" % (sys.argv[0], msg))


##########################################################################
def Fatal(msg, fd=sys.stderr):
    """ TODO """
    fd.write("Fatal: %s\n" % msg)
    tmpfile.write("Fatal: %s %s\n" % (sys.argv[0], msg))
    sys.exit(255)


# EOF
