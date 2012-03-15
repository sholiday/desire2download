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

# desire2download #

d2d is a tool to download all of the content from the University of Waterloo's
new learning management system which uses Desire2Learn instead of the old Angel
based UWACE.

d2d was inspired by Jamie Wong's fabulous [UWAngel-CLI](https://github.com/phleet/UWAngel-CLI)
written in Ruby.

d2d is somewhat hacky and has not been tested extensively. If you do find a bug,
please [let me know](mailto:stephen.holiday@gmail.com)

## Installation ##
To install, just do:

    easy_install desire2download

## Usage ##
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

## Credits ##
* [Stephen Holiday](http://stephenholiday.com)
* [Ansis Brammanis](https://github.com/aibram)

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
        d2d = Desire2Download(username, password, ignore_re=ignore_re)
        try:
            d2d.login()
        except (AuthError, Exception) as e:  ## TODO: replace Exception
            print e
            return 2
        links = d2d.get_course_links()
        for link in links:
            print link.text
            try:
                document_tree = d2d.get_course_documents(link, link.text)
            except Exception as e: ## TODO: replace Exception
                print e
                return 2
            d2d.download_tree(document_tree)
        
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2


if __name__ == "__main__":
    sys.exit(main())
