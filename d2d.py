#!/usr/bin/env python
# encoding: utf-8
"""
d2d.py

Created by Stephen Holiday on 2011-09-15.
Copyright (c) 2011 Stephen Holiday. All rights reserved.


# desire2download #
[Stephen Holiday](http://stephenholiday.com)

d2d is a tool to download all of the content from the University of Waterloo's
new learning management system which uses Desire2Learn instead of the old Angel
based UWACE.

d2d was inspired by Jamie Wong's fabulous [UWAngel-CLI](https://github.com/phleet/UWAngel-CLI)
written in Ruby.

d2d is somewhat hacky and has not been tested extensively. If you do find a bug,
please [let me know](mailto:stephen.holiday@gmail.com)

## Usage ##
Using d2d is easy:
    ./d2d.py --username scholida -i ".*.wmv"
    Password: 
    Logging In...
    Logged In
    Finding courses...
    ECE 224 - Fall 2011
     + ECE 224 - Fall 2011/Labs/Lab Tools Tutorial.html (1.70K)
     + ECE 224 - Fall 2011/Labs/Lab 1/lab1_checklist-s2010.pdf (107.65K)
     
    ...


d2d will not download a file if it has been already saved.

"""

import getopt
import re

from desire2download import Desire2Download
from desire2download import AuthError
from getpass import getpass
import sys
reload(sys) 
sys.setdefaultencoding("utf-8")

help_message = '''
Desire2Download
===============

Download all of the content from the University of Waterloo's
new learning management system which uses Desire2Learn instead of the old Angel
based UWACE.

d2d was inspired by Jamie Wong's fabulous [UWAngel-CLI](https://github.com/phleet/UWAngel-CLI)
written in Ruby.

d2d is somewhat hacky and has not been tested extensively. If you do find a bug,
please [let me know](mailto:stephen.holiday@gmail.com)

Using d2d is easy:

    d2d --username scholida -i ".*.wmv"
    Password: 
    Logging In...
    Logged In
    Finding courses...
    ECE 224 - Fall 2011
     + ECE 224 - Fall 2011/Labs/Lab Tools Tutorial.html (1.70K)
     + ECE 224 - Fall 2011/Labs/Lab 1/lab1_checklist-s2010.pdf (107.65K)
     
    ...
    
d2d will not download a file if it has been already saved.


Other Options:
    -h                          This help message
    -u, --username [username]   set your username
    -p, --password [password]   set your password
    -i, --ignore  [regular exp] ignore files that match this regex
'''
            
class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hupi:v", ["help", "username=", "password=","ignore="])
        except getopt.error, msg:
            raise Usage(msg)
            
        username = None
        password = None
        ignore_re = list()
        
        # option processing
        for option, value in opts:
            if option == "-v":
                verbose = True
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-u", "--username"):
                username = value
            if option in ("-p", "--password"):
                password = value
            if option in ("-i", "--ignore"):
                try:
                    ignore_re.append(re.compile(value))
                except:
                    print 'Regular Expression "%s" is invalid...'
                    raise Usage(help_message)
                
        if username is None:
            username = raw_input('Username: ')
        if password is None:
            password = getpass()
        
        
        # Start the actual work
        d2d = Desire2Download(username,password)
        d2d.ignore_re = ignore_re
        try:
            d2d.login()
        except AuthError as e:
            print e
            return 1
        links = d2d.get_course_links()
        for link in links:
            print link.text
            document_tree = d2d.get_course_documents(link)
            d2d.download_tree(document_tree, [link.text])
        
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2


if __name__ == "__main__":
    sys.exit(main())
