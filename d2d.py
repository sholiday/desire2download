#!/usr/bin/env python
# encoding: utf-8
"""
d2d.py

Copyright 2012 Stephen Holiday

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

# Desire2Download

Download all of the content from the University of Waterloo's
new learning management system which uses Desire2Learn instead of the old Angel
based UWACE.

d2d was inspired by Jamie Wong's fabulous [UWAngel-CLI](https://github.com/phleet/UWAngel-CLI)
written in Ruby.

d2d is somewhat hacky and has not been tested extensively. If you do find a bug,
please [let us know](https://github.com/sholiday/desire2download/issues)

To install, just do either:

   - python setup.py install
   - pip install desire2download

To use d2d, just browse to the folder you want to download the files in, type
d2d and hit enter! d2d will not download a file if it has been already saved.

Examples:
   - d2d
   - d2d --username ktalwar
   - d2d -u ktalwar -p icanhazcatz
   - d2d -i ".*.ppt"
   - d2d -u scholida -p hecanhazcatz -i ".*.ppt" -c "CS+"

Result:
   Username: scholida
   Password:
   Logging In...
   Logged In
   Finding courses...
   ECE 224 - Fall 2011
    + ECE 224 - Fall 2011/Labs/Lab Tools Tutorial.html (1.70K)
    + ECE 224 - Fall 2011/Labs/Lab 1/lab1_checklist-s2010.pdf (107.65K)
      ...

Credits: Stephen Holiday, Ansis Brammanis, Kartik Talwar and Jacob Parry
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
please [let us know](https://github.com/sholiday/desire2download/issues)

To use d2d, just browse to the folder you want to download the files in, type
d2d and hit enter! d2d will not download a file if it has been already saved.

Examples:
    - d2d
    - d2d --username ktalwar
    - d2d -u ktalwar -p icanhazcatz
    - d2d -i ".*.ppt"
    - d2d -u scholida -p hecanhazcatz -i ".*.ppt" -c "CS+"

Options:
    -h  --help                  This help message
    -u, --username [username]   set your username
    -p, --password [password]   set your password
    -i, --ignore  [regular exp] ignore files that match this regex
    -c, --courses [regular exp] ignore courses that match this regex
'''
            
class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hupi:c:v", ["help", "username=", "password=","ignore=","courses="])
        except getopt.error, msg:
            raise Usage(msg)
            
        username = None
        password = None
        ignore_re = list()
        ignore_course = list()
        
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
            if option in ("-c", "--courses"):
                try:
                    ignore_course.append(re.compile(value))
                except:
                    print 'Regular Expression "%s" is invalid...'
                    raise Usage(help_message)
                
        if username is None:
            username = raw_input('Username: ')
        if password is None:
            password = getpass()
        
        
        # Start the actual work
        d2d = Desire2Download(username, password, ignore_re=ignore_re)
        try:
            d2d.login()
        except (AuthError, Exception) as e:  ## TODO: replace Exception
            print e
            return 2
        links = d2d.get_course_links()
        for link in links:
            is_skip = False # Use a flag to avoid nasty loop-breaking
            for r in ignore_course:
                if r.match(link.text) is not None:
                    print 'Skipping %s because it matches regex "%s"' % (link.text, r.pattern)
                    is_skip = True
            
            if not is_skip:
                print link.text
                try:
                    document_tree = d2d.get_course_documents(link, link.text)
                    d2d.download_tree(document_tree)
                except Exception as e: ## TODO: replace Exception
                    print 'Failed to load course:', e
                    #return 2 #don't want to fail just because of one course
        
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2


if __name__ == "__main__":
    sys.exit(main())
