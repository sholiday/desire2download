#!/usr/bin/env python
# encoding: utf-8
"""
desire2download.py

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
"""

import BeautifulSoup
import mechanize
import os
import re
import urllib
import urllib2

import sys
reload(sys)
sys.setdefaultencoding("utf-8")


class AuthError(Exception):
    """Raised when login credentials fail."""
    pass


class Desire2Download(object):
    base_url = 'https://learn.uwaterloo.ca/d2l/home/6606'
    cas_login = 'https://cas.uwaterloo.ca/cas/login?service=http%3a%2f%2flearn.uwaterloo.ca%2fd2l%2forgtools%2fCAS%2fDefault.aspx'
    ping_url = 'http://jobminestats.appspot.com/Ping/ag5zfmpvYm1pbmVzdGF0c3IMCxIFUGl4ZWwYuRcM.gif'

    def __init__(self, username, password, ignore_re=None, retries=3, skip_existing=True):
        self.username = username
        self.password = password
        self.ignore_re = ignore_re
        self.retries = retries
        self.skip_existing = skip_existing

        self.br = mechanize.Browser(factory=mechanize.RobustFactory())
        self.br.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3)\
            AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.65 Safari/537.31')]
        self.br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

        self.br.open(self.ping_url).read()

    def retry(f):
        """Decorator to retry upon timeout. D2L is slow."""
        def retry_it(self, *args, **kargs):
            attempts = 0
            while attempts < self.retries:
                try:
                    return f(self, *args, **kargs)
                except urllib2.URLError as e:
                    if isinstance(e.reason, socket.timeout):
                        attempts += 1
                        if attempts >= self.retries:
                            print "Timeout, out of retries."
                            raise(e)
                        print "Timeout, retrying..."
                    else: 
                        # Not a timeout, raise exception
                        print "Unknown exception:",e
                        raise(e)
        return retry_it

    @retry
    def login(self):
        print 'Logging In...'
        self.br.open(self.cas_login)
        self.br.select_form(nr=0)
        self.br['username'] = self.username
        self.br['password'] = self.password
        response = self.br.submit().read()
        if "Your userid and/or your password are incorrect" in response:
            raise AuthError("Your userid and/or your password are incorrect.")
        if "d2l" in response:
            print 'Logged In'
            return
        raise AuthError("Some other login error occured.")

    def get_course_links(self):
        print 'Finding courses...'
        links = []
        urls = []
        for link in self.br.links():
            if link.text is not None:
                matches = re.match('[A-Z]+ [0-9A-Za-z/\s]{2,45} - [A-Z][a-z]+ 20[0-9]{2}', link.text)
                if matches is not None and link.url not in urls:
                    links.append(link)
                    urls.append(link.url)
        return links

    def convert_bytes(self, bytes):
        """
            Stolen from http://www.5dollarwhitebox.org/drupal/node/84
        """
        bytes = float(bytes)
        if bytes >= 1099511627776:
            terabytes = bytes / 1099511627776
            size = '%.2fT' % terabytes
        elif bytes >= 1073741824:
            gigabytes = bytes / 1073741824
            size = '%.2fG' % gigabytes
        elif bytes >= 1048576:
            megabytes = bytes / 1048576
            size = '%.2fM' % megabytes
        elif bytes >= 1024:
            kilobytes = bytes / 1024
            size = '%.2fK' % kilobytes
        else:
            size = '%.2fb' % bytes
        return size

    @retry
    def get_course_documents(self, link, course_name):
        """Produce a tree of documents for the course.

        Args:
            link (str): A url to the course's page on d2l.
            course_name (str): The name of the course.

        Returns:
            A dict representing a tree:
            {
                'type': Either 'file' or 'dir',
                'name': A string.
                'url': Url to the file preview (if file).
                'children': A list of children nodes (if a dir).
            }
        """
        self.br.follow_link(link)                    # Go to course page
        link = self.br.links(text='Content').next()  # Get content link
        page = self.br.follow_link(link).read()      # Go to content page
        soup = BeautifulSoup.BeautifulSoup(page)

        ## Initial document tree
        document_tree = {
            'type': 'dir',
            'name': course_name,
            'children': []
        }

        for link in self.br.links(url_regex='/d2l/le/content/.+/viewContent/.+/View'):
            ou = re.search('/content/([0-9]+)/', link.url).group(1)
            tId = re.search('/viewContent/([0-9]+)/', link.url).group(1)
            link_href = 'https://learn.uwaterloo.ca/d2l/le/content/%s/%s/downloadfiles/DownloadTopic' % (ou, tId)
            
            document_tree['children'].append({
                'type': 'file',
                'name': link.text,
                'url': link_href
                })

        return document_tree

    def download_tree(self, root, _path=[]):
        """Downloads the entire file tree the

        Args:
            root: A dictionary containing the file tree.
            _path: A list representing the path (relative to current dir) to
                download to. Items in list are strings.
        """
        if root['type'] == 'dir':
            path = _path[:]
            path.append(root['name'])
            for node in root['children']:
                self.download_tree(node, path)
        else:
            path = '/'.join(map(lambda x: x.replace('/', '-'), _path))
            self.download_file(root['name'], root['url'], path)

    def download_file(self, title, url, path):
        """Downloads a file to the specified directory.

        Args:
            title (str): Name of the file.
            url (str): Address to the file preview page.
            path (str): Relative path of file to make.
        """
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno != 17:
                raise e
            pass

        try:
            ret = self.br.open(url)
        except Exception, e:
            print " X Error for %s [%s]" % (url, e)
            return
        
        content_disposition = next(x for x in ret.info().headers if 'Content-Disposition' in x)
        filename = re.findall("filename=(\S+)", content_disposition)[0]
        filename = urllib.unquote(filename).replace('"', '')

        path_and_filename = '%s/%s' % (path, filename.strip('/'))

        if os.path.isfile(path_and_filename) and self.skip_existing:  # TODO Can we make this smarter?
            print ' - %s (Already Saved)' % path_and_filename
            return

        try:
            print ' + %s' % path_and_filename
            self.br.retrieve(url, path_and_filename, self._progressBar)
        except KeyboardInterrupt:
            # delete the file on a keyboard interrupt
            if os.path.exists(path_and_filename):
                os.remove(path_and_filename)
            raise
        except urllib2.HTTPError, e:
            if e.code == 404:
                print " X File does not exist: %s" % file_name.strip('/')
            else:
                print " X HTTP error %s for: %s" % (e.code, file_name.strip('/'))
        except Exception, e:
            # otherwise raise the error
            if os.path.exists(path_and_filename):
                os.remove(path_and_filename)
            else:
                print url
                print e

    def _progressBar(self, blocknum, bs, size):
        """
            Stolen from https://github.com/KartikTalwar/Coursera/blob/master/coursera.py
        """
        if size > 0:
            if size % bs != 0:
                blockCount = size/bs + 1
            else:
                blockCount = size/bs

            fraction = blocknum*1.0/blockCount
            width    = 50

            stars    = '*' * int(width * fraction)
            spaces   = ' ' * (width - len(stars))
            progress = ' ' * 3 + '%s [%s%s] (%s%%)' % (self.convert_bytes(size), stars, spaces, int(fraction * 100))

            if fraction*100 < 100:
                sys.stdout.write(progress)

                if blocknum < blockCount:
                    sys.stdout.write('\r')
                else:
                    sys.stdout.write('\n')
            else:
                sys.stdout.write(' ' * int(width * 1.5) + '\r')
                sys.stdout.flush()

