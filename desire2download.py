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

import json
import re
import os
import socket
import urllib2
import mechanize
import BeautifulSoup
from errno import EEXIST

import sys

reload(sys)
sys.setdefaultencoding("utf-8")


class AuthError(Exception):
    """Raised when login credentials fail."""
    pass


class Desire2Download(object):
    base_url = 'https://learn.uwaterloo.ca/d2l/lp/homepage/home.d2l?ou=6606'
    process_login = 'https://learn.uwaterloo.ca/d2l/lp/auth/login/ProcessLoginActions.d2l'
    cas_login = 'https://cas.uwaterloo.ca/cas/login?service=https%3a%2f%2flearn.uwaterloo.ca%2fd2l%2fcustom%2fcas%3ftarget%3d%252fd2l%252fhome'
    ping_url = 'http://jobminestats.appspot.com/Ping/ag5zfmpvYm1pbmVzdGF0c3IMCxIFUGl4ZWwYuRcM.gif'

    def __init__(self, username, password, ignore_re=None, retries=3, skip_existing=True):
        self.username = username
        self.password = password
        self.ignore_re = ignore_re
        self.retries = retries
        self.skip_existing = skip_existing

        self.br = mechanize.Browser(factory=mechanize.RobustFactory())
        self.br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko')]
        self.br.set_handle_refresh(True)
        self.br.set_handle_redirect(True)

        self.br.open(self.ping_url).read()

    def retry(f):
        """Decorator to retry upon timeout. D2L is slow."""

        def retry_it(self, *args, **kwargs):
            attempts = 0
            while attempts < self.retries:
                try:
                    return f(self, *args, **kwargs)
                except urllib2.URLError as e:
                    if isinstance(e.reason, socket.timeout):
                        attempts += 1
                        if attempts >= self.retries:
                            print "Timeout, out of retries."
                            raise e
                        print "Timeout, retrying..."
                    else:
                    # Not a timeout, raise exception
                        print "Unknown exception:", e
                        raise e

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
        self.br.open(self.process_login)
        print 'Logged In'

    def get_course_links(self):
        print 'Finding courses...'
        historicalCourses = json.loads(self.br.open('https://learn.uwaterloo.ca/d2l/api/lp/1.0/enrollments/myenrollments/').read())
        historicalCourses = historicalCourses['Items']
        links = []
        for course in historicalCourses:
            matches = re.match('[A-Z]+ [0-9A-Za-z/\s]{2,45} - [A-Z][a-z]+ 20[0-9]{2}.*', course['OrgUnit']['Name'])
            if matches is not None:
                link = lambda: None
                link.text = course['OrgUnit']['Name']
                link.absolute_url = 'https://learn.uwaterloo.ca/d2l/lp/ouHome/home.d2l?ou=' + str(course['OrgUnit']['Id'])
                links.append(link)
        return links

    def find_module_content(self, content_link, document_tree, path_to_root, top_modules, depth):
        depth += 1
        for module in top_modules:
            page = self.br.open(content_link.absolute_url + '?itemIdentifier=' + module['data-key']).read()
            soup = BeautifulSoup.BeautifulSoup(page)
            module_content = soup.find('div', 'd2l-page-main-padding')

            ## Update path_to_root
            header = module_content.find('h1')
            if header is None:
                continue
            heading = header.getText()

            section_node = new_dir(sanitize_string(heading))
            temp_path = path_to_root
            #crawl down the document tree to the correct location
            for i in range(depth):
                temp_path = temp_path[-1]['children']

            temp_path.append(section_node)
            path_to_module = temp_path[-1]

            is_sub_dir = False
            for node in module_content.findAll('li', 'd2l-datalist-item'):
                dir_header = node.find('div', 'd2l-collapsepane')

                if dir_header is None:
                    #There can be restrictions on files being downloaded, so check first
                    d2l_link = node.find('a', 'd2l-link')
                    if not is_sub_dir and d2l_link:
                        file_node = node_from_link(d2l_link)
                        path_to_module['children'].append(file_node)
                else:
                    is_sub_dir = True

            sub_modules = module.findAll('li', 'd2l-le-TreeAccordionItem')

            self.find_module_content(content_link, document_tree, path_to_root, sub_modules, depth)
        return document_tree


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
                'url': Url to the file download (if file).
                'children': A list of children nodes (if a dir).
            }
        """
        self.br.open(link)                                      # Go to course page
        content_link = self.br.links(text='Content').next()     # Get content link
        page = self.br.follow_link(content_link).read()         # Go to content page
        soup = BeautifulSoup.BeautifulSoup(page)
        contents = soup.find('ul', 'd2l-le-TreeAccordion')

        ## Initial document tree
        document_tree = new_dir(course_name)
        ## Keeps track of current location in tree
        path_to_root = [document_tree]

        all_modules = contents.findAll('li', 'd2l-le-TreeAccordionItem-Root')
        modules = [a for a in all_modules if 'ContentObject.Module' in a['data-key']]

        return self.find_module_content(content_link, document_tree, path_to_root, modules, 0)

    def download_tree(self, root, _path=None):
        """Downloads the entire file tree
        Args:
            root: A dictionary containing the file tree.
            _path: A list representing the path (relative to current dir) to
                download to. Items in list are strings.
        """
        if not _path:
            _path = []
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
            url (str): Address to the direct link.
            path (str): Relative path of file to make.
        """
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno != EEXIST:
                raise

        #Mechanize pukes trying to open the url sometimes...
        try:
            info = self.br.open(url).info()
            #D2L hides the content type here... so we have to do a little bit more work
            if 'content-disposition' in info:
                name = info.dict['content-disposition'].split(';')[-1]
                extension = name[name.rfind("."): -1]
            else:
                extension = '.' + info.subtype
            filename = title + extension
        except ValueError:
            #maybe better to just return?
            filename = title + ".pdf"

        for r in self.ignore_re:
            if r.match(filename) is not None:
                print 'Skipping %s because it matches ignore regex "%s"' % (filename, r.pattern)
                return

        path_and_filename = '%s/%s' % (path, filename.strip('/'))
        if os.path.isdir(os.path.join(os.getcwd(), path_and_filename)): # Handle empty file names
            print ' X %s is a directory, not a file. Skipping.' % path_and_filename
        elif os.path.isfile(
                os.path.join(os.getcwd(), path_and_filename)) and self.skip_existing:  # TODO Can we make this smarter?
            print ' - %s (Already Saved)' % path_and_filename
        else:
            try:
                print ' + %s' % path_and_filename
                self.br.retrieve(url, path_and_filename, self._progress_bar)
            except KeyboardInterrupt:
                # delete the file on a keyboard interrupt
                if os.path.exists(path_and_filename):
                    os.remove(path_and_filename)
                raise
            except urllib2.HTTPError, e:
                if e.code == 404:
                    print " X File does not exist: %s" % filename.strip('/')
                else:
                    print " X HTTP error %s for: %s" % (e.code, filename.strip('/'))
            except Exception:
                # otherwise raise the error
                if os.path.exists(path_and_filename):
                    os.remove(path_and_filename)
                else:
                    raise

    def _progress_bar(self, block_num, bs, size):
        """
            Stolen from https://github.com/KartikTalwar/Coursera/blob/master/coursera.py
        """
        if size > 0:
            if size % bs != 0:
                block_count = size / bs + 1
            else:
                block_count = size / bs

            fraction = block_num * 1.0 / block_count
            width = 50

            stars = '*' * int(width * fraction)
            spaces = ' ' * (width - len(stars))
            progress = ' ' * 3 + '%s [%s%s] (%s%%)' % (convert_bytes(size), stars, spaces, int(fraction * 100))

            if fraction * 100 < 100:
                sys.stdout.write(progress)

                if block_num < block_count:
                    sys.stdout.write('\r')
                else:
                    sys.stdout.write('\n')
            else:
                sys.stdout.write(' ' * int(width * 1.5) + '\r')
                sys.stdout.flush()


def convert_bytes(byte_amt):
    """
        Stolen from http://www.5dollarwhitebox.org/drupal/node/84
    """
    byte_amt = float(byte_amt)
    if byte_amt >= 1099511627776:
        terabytes = byte_amt / 1099511627776
        size = '%.2fT' % terabytes
    elif byte_amt >= 1073741824:
        gigabytes = byte_amt / 1073741824
        size = '%.2fG' % gigabytes
    elif byte_amt >= 1048576:
        megabytes = byte_amt / 1048576
        size = '%.2fM' % megabytes
    elif byte_amt >= 1024:
        kilobytes = byte_amt / 1024
        size = '%.2fK' % kilobytes
    else:
        size = '%.2fb' % byte_amt
    return size


def sanitize_string(string):
    return "".join([x for x in string if x.isalnum() or x.isspace()])


def node_from_link(d2l_link):
    name = sanitize_string(d2l_link.getText())
    try:
        section_number = re.search('/content/([0-9]+)', d2l_link['href']).group(1)
        content_number = re.search('/viewContent/([0-9]+)', d2l_link['href']).group(1)
        link_href = 'https://learn.uwaterloo.ca/d2l/le/content/%s/topics/files/download/%s/DirectFileTopicDownload' % (
            section_number, content_number)
        return new_file(name, link_href)
    except AttributeError:
        #The link isn't associated with Learn, so take the href as is
        return new_file(name, d2l_link['href'])


def new_dir(name):
    node = _new_node('dir', name)
    node['children'] = []
    return node


def new_file(name, url):
    node = _new_node('file', name)
    node['url'] = url
    return node


def _new_node(node_type, name):
    return {
        'type': node_type,
        'name': name
    }
