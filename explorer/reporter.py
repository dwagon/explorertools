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
toaddr = ["dougal.scott@tollgroup.com"]

##########################################################################


class complaintHandler(object):

    """Decorator to make sure that any complaints, tracebacks etc. get captured
    and sent off to the appropriate authorities
    """

    def __init__(self, fn):
        self.fn = fn
        self.fd = tmpfile

    ##########################################################################
    def __call__(self, *args):
        try:
            self.fn(*args)
        except Exception as err:
            traceback.print_exc(file=self.fd)
        self.report()

    ##########################################################################
    def report(self):
        tmpfile.flush()
        tmpfile.seek(0)
        data = tmpfile.read()
        tmpfile.close()
        if not data:
            return
        f = open("/tmp/explorerlog_%d.log" % os.getpid(), "w")
        f.write("%s\n" % " ".join(sys.argv))
        f.write(data)
        f.close()
        msgbody = "ExplorerTools: Report"
        subject = "ExplorerTools: Report"
        msg = (
            "From: %s\r\nX-Generated-by: $Id: reporter.py 4431 2013-02-27 07:38:45Z dougals $\r\nTo: %s\r\nSubject: %s\r\n\r\n%s"
            % (fromaddr, ", ".join(toaddr), subject, msgbody)
        )
        try:
            server = smtplib.SMTP("localhost")
            server.sendmail(fromaddr, toaddr, data)
            server.quit()
        except:
            pass


##########################################################################


def Log(msg, fd=sys.stderr):
    fd.write("%s\n" % msg)
    tmpfile.write("%s %s\n" % (sys.argv[0], msg))


##########################################################################


def Warning(msg, fd=sys.stderr):
    fd.write("Warning: %s\n" % msg)
    tmpfile.write("Warning: %s %s\n" % (sys.argv[0], msg))


##########################################################################


def Verbose(msg, fd=sys.stderr):
    fd.write("%s\n" % msg)
    tmpfile.write("%s %s\n" % (sys.argv[0], msg))


##########################################################################


def Fatal(msg, fd=sys.stderr):
    fd.write("Fatal: %s\n" % msg)
    tmpfile.write("Fatal: %s %s\n" % (sys.argv[0], msg))
    sys.exit(255)


# EOF
