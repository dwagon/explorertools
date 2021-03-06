#!/usr/bin/env python
#
# Script to provide an issue class for explorer analysis
#
# Written by Dougal Scott <dwagon@pobox.com>
# $Id: issue.py 2393 2012-06-01 06:38:17Z dougals $
# $HeadURL: http://svn/ops/unix/explorer/trunk/explorer/issue.py $

import sys

##########################################################################


class Issue:

    def __init__(self, *args, **kwargs):
        self.category = args[0]
        try:
            self.subcategory = args[1]
        except IndexError:
            self.subcategory = ''

        if 'text' in kwargs:
            if type(kwargs['text']) == type([]):
                self.text = "\n".join(kwargs['text'])
            elif type(kwargs['text']) != type(''):
                self.text = str(kwargs['text'])
            else:
                self.text = kwargs['text']
        else:
            self.text = ''

        if 'obj' in kwargs:
            self.obj = kwargs['obj']
        else:
            self.obj = ''
        if 'typ' in kwargs:
            self.typ = kwargs['typ']
        else:
            self.type = 'issue'

    ##########################################################################
    def isIssue(self):
        if self.typ == 'issue':
            return True
        return False

    ##########################################################################
    def isConcern(self):
        if self.typ == 'concern':
            return True
        return False

    ##########################################################################
    def __repr__(self):
        return "Issue %s:%s %s" % (self.category, self.subcategory, self.obj)

# EOF
