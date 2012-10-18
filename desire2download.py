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

import re
import os
import urllib2
import mechanize
import BeautifulSoup

import sys
reload(sys)
sys.setdefaultencoding("utf-8")


class AuthError(Exception):
    """Raised when login credentials fail."""
    pass


class Desire2Download(object):
    base_url = 'https://learn.uwaterloo.ca/d2l/lp/homepage/home.d2l?ou=6606'
    cas_login = 'https://cas.uwaterloo.ca/cas/login?service=http%3a%2f%2flearn.uwaterloo.ca%2fd2l%2forgtools%2fCAS%2fDefault.aspx'
    ping_url = 'http://jobminestats.appspot.com/Ping/ag5zfmpvYm1pbmVzdGF0c3IMCxIFUGl4ZWwYuRcM.gif'

    def __init__(self, username, password, ignore_re=None, retries=3):
        self.username = username
        self.password = password
        self.ignore_re = ignore_re
        self.retries = retries

        self.br = mechanize.Browser(factory=mechanize.RobustFactory())
        self.br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

        self.br.open(self.ping_url).read()

    def retry(f):
        """Decorator to retry upon timeout. D2L is slow."""
        def retry_it(self, *args, **kargs):
            attempts = 0
            while attempts < self.retries:
                try:
                    return f(self, *args, **kargs)
                except Exception as e:  # TODO: Important! should only catch timeouts
                    attempts += 1
                    if attempts >= self.retries:
                        print "Timeout, out of retries."
                        raise(e)
                    print "Timeout, retrying..."
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
        print 'Logged In'

    def get_course_links(self):
        print 'Finding courses...'
        links = []
        urls = []
        for link in self.br.links():
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
        table = soup.find(id='z_n')

        ## Initial document tree
        document_tree = {
            'type': 'dir',
            'name': course_name,
            'children': []
        }
        ## Keeps track of current location in tree
        path_to_root = [document_tree]

        rows = table.findAll('tr')
        for row in rows[1:]:
            ## Update path_to_root
            columns = row.findAll('td')
            depth = len(columns) - 1
            if len(path_to_root) >= depth:
                path_to_root = path_to_root[:depth]

            cell = row.find('td', 'd_gn')
            link = cell.find("a")

            ## Generate new node, whether a file or dir, and append it
            ## to the children of the current level (last in path_to_root)
            if link:
                ou = re.search('\?ou\=([0-9]+)', link['href']).group(1)
                tId = re.search('\&tId\=([0-9]+)', link['href']).group(1)
                link_href = 'https://learn.uwaterloo.ca/d2l/lms/content/preview.d2l?tId=%s&ou=%s' % (tId, ou)
                node = {
                    'type': 'file',
                    'name': link.getText(),
                    'url': link_href,
                }
                path_to_root[-1]['children'].append(node)
            else:
                node = {
                    ## Spaces and periods are stripped from both ends of a dir
                    ## name to avoid weirdness caused by "bullets"
                    'type': 'dir',
                    'name': cell.getText().replace('&nbsp;', ' ').strip(". "),
                    'children': [],
                }
                path_to_root[-1]['children'].append(node)
                path_to_root.append(node)  # "cd" into the new directory

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

        page = self.br.open(url).read()
        soup = BeautifulSoup.BeautifulSoup(page)
        url = soup.find('iframe')['src']

        ## TODO: How should this be handled. These seem to be custom pages
        ## with content loaded via javascript, at least this one
        ## url = https://learn.uwaterloo.ca/d2l/lor/viewer/view.d2l?ou=16733&loId=0&loIdentId=245
        if '/d2l/common/dialogs/' in url or \
            'https://learn.uwaterloo.ca/d2l/lor/viewer' in url:
            print " X Unable to download web-only content: %s" % title
            return

        url_path = url.split('?')[0]
        if url_path.find('http') == 0:
            # If this link is actually to the outside world, let it be.
            # Technically this could be to ftp:// as well as many others.
            clean_url = url_path
        else:
            clean_url = 'https://learn.uwaterloo.ca%s' % url_path
        clean_url = clean_url.replace(' ', '%20')
        file_name = os.path.split(url_path)[1]
        for r in self.ignore_re:
            if r.match(file_name) is not None:
                print 'Skipping %s because it matches ignore regex "%s"' % (file_name, r.pattern)
                return

        path_and_filename = '%s/%s' % (path, file_name.strip('/'))
        if os.path.isdir(path_and_filename): # Handle empty file names
            print ' X %s is a directory, not a file. Skipping.' % path_and_filename
        elif os.path.isfile(path_and_filename):  # TODO Can we make this smarter?
            print ' - %s (Already Saved)' % path_and_filename
        else:
            try:
                print ' + %s' % path_and_filename
                self.br.retrieve(clean_url, path_and_filename, self._progressBar)
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
                    raise

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

