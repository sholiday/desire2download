#!/usr/bin/env python
# encoding: utf-8
"""
desire2download.py

Created by Stephen Holiday on 2011-09-15.
Copyright (c) 2011 Stephen Holiday. All rights reserved.
"""

import re
import os
import mechanize
import BeautifulSoup

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

def retry(howmany):
    """
        Nifty decorator stolen from http://stackoverflow.com/a/567697/429688
    """
    def tryIt(func, *args, **kwargs):
        def f(*args, **kwargs):
            attempts = 0
            while attempts < howmany:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print 'Exception [%s], retrying' % e
                    attempts += 1
        return f
    return tryIt


class AuthError(Exception):
    """Raised when login credentials fail."""
    pass


class Desire2Download(object):
    base_url = 'https://learn.uwaterloo.ca/d2l/lp/homepage/home.d2l?ou=6606'
    cas_login = 'https://cas.uwaterloo.ca/cas/login?service=http%3a%2f%2flearn.uwaterloo.ca%2fd2l%2forgtools%2fCAS%2fDefault.aspx'
    ping_url = 'http://jobminestats.appspot.com/Ping/ag5zfmpvYm1pbmVzdGF0c3IMCxIFUGl4ZWwYuRcM.gif'

    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.br = mechanize.Browser(factory=mechanize.RobustFactory())
        self.br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
 
        self.br.open(self.ping_url).read()
 
    #@retry(3)
    def login(self):
        print 'Logging In...'
        self.br.open(self.cas_login)
        self.br.select_form(nr=0)
        self.br['username'] = self.username
        self.br['password'] = self.password
        response = self.br.submit().read()
        if "Logged in as" in response:
            print 'Logged In'
        else:
            raise AuthError("Your userid and/or your password are incorrect.")
        
    def get_course_links(self):
        print 'Finding courses...'
        links = []
        for link in self.br.links():
            matches = re.match('[A-Z]+ [0-9]{3} - [A-Z][a-z]+ 20[0-9]{2}', link.text)
            if matches is not None:
                links.append(link)
        return links
        
    def _nice_regex(self, regex, content, group):
        res = re.search(regex, content)
        if res != None:
            return res.group(group)
        else:
            return ''
    
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
    
    @retry(3)
    def get_course_documents(self, link):
        self.br.follow_link(link)
        content_link = None
        for link_j in self.br.links():
            if link_j.text == 'Content':
                if content_link is None:
                    content_link = link_j
                    
        self.br.follow_link(content_link)
        
        print_dl_link = None
        for link_k in self.br.links(url_regex='print_download.d2l'):
            if print_dl_link is not None:
                print_dl_link = link_k
        
        r = self.br.follow_link(print_dl_link)
        
        page = r.read()
        soup = BeautifulSoup.BeautifulSoup(page)
        table = soup.find(id='z_n')
        
        document_tree = {}
        path_to_root = []
        
        rows = table.findAll('tr')
        for row in rows[1:]:
            columns = row.findAll('td')
            
            depth = len(columns) - 2
            
            cell = None
            for column in columns:
                if column.has_key('class') and column['class'] == 'd_gn':
                    cell = column
                   
            cell_str = ''.join(map(lambda x: str(x), cell.contents))
            
            if re.search('href=', cell_str):
                ## Isn't heading
                link = cell.a
                if hasattr(link, 'img'):
                    link.img.extract()
                
                title = ''.join(map(lambda x: str(x), link.contents))

                ou = self._nice_regex('\?ou\=([0-9]+)', link['href'], 1)
                tId = self._nice_regex('\&tId\=([0-9]+)', link['href'], 1)
                
                link_href = 'https://learn.uwaterloo.ca/d2l/lms/content/preview.d2l?tId=%s&ou=%s' % (tId, ou)
                
                cur_tree_node = document_tree
                for cur_path_node in path_to_root:
                    key = cur_path_node['title']
                    if not cur_tree_node.has_key(key):
                        cur_tree_node[key] = {}
                    cur_tree_node = cur_tree_node[key]
                    
                cur_tree_node[title] = link_href
                
            else:
                cell_str = cell_str.replace('&nbsp;', '').strip()
                cell_str = cell_str.replace('<strong>', '').replace('</strong>', '').strip()
                node = {'heading': True, 'title': cell_str}
            
                if len(path_to_root) < depth:
                    path_to_root.append(node)
                else:
                    path_to_root = path_to_root[:depth]
                    path_to_root.append(node)
            
        return document_tree
            
    def download_tree(self, root, _path=[]):
        """Downloads the entire file tree the 

        Args:
            root: A dictionary containing the file tree.
            _path: A list representing the path (relative to current dir) to
                download to. Items in list are strings.
        """
        for item in root:
            path = _path[:]
            
            if type(root[item]) is dict:  ## TODO: type checking is unpythonic
                path.append(item)
                self.download_tree(root[item], path)
            else:
                path = '/'.join(map(lambda x: x.replace('/', '\/'), path))
                self.download_file(item, root[item], path)

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
            print " X Unable to download web-only content %s" % title
            return

        url_path = url.split('?')[0]
        clean_url = 'https://learn.uwaterloo.ca%s' % url_path
        clean_url = clean_url.replace(' ', '%20')
        file_name = os.path.split(url_path)[1]
        for r in self.ignore_re:
            if r.match(file_name) is not None:
                print 'Skipping %s because it matches ignore regex "%s"' % (file_name, r.pattern)
                return

        path_and_filename = '%s/%s' % (path, file_name.strip('/'))
        if os.path.isfile(path_and_filename):  ## TODO Can we make this smarter?
            print ' - %s (Already Saved)' % path_and_filename
        else:
            content = self.br.open_novisit(clean_url).read()
            print ' + %s (%s)' % (path_and_filename, self.convert_bytes(len(content)))
            with open(path_and_filename, 'w') as f:
                f.write(content)
