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
import urlparse
from urllib import urlencode
import mechanize
import BeautifulSoup

import sys
reload(sys) 
sys.setdefaultencoding("utf-8")
def retry(howmany):
    '''
        Nifty decorator stolen from http://stackoverflow.com/a/567697/429688
    '''
    def tryIt(func, *args, **kwargs):
        def f(*args, **kwargs):
            attempts = 0
            while attempts < howmany:
                try:
                    return func(*args, **kwargs)
                except Exception, e:
                    print 'Exception [%s], retrying'%e
                    attempts += 1
        return f
    return tryIt
class Desire2Download(object):
    base_url = 'https://learn.uwaterloo.ca/d2l/lp/homepage/home.d2l?ou=6606'
    cas_login = 'https://cas.uwaterloo.ca/cas/login?service=http%3a%2f%2flearn.uwaterloo.ca%2fd2l%2forgtools%2fCAS%2fDefault.aspx'
    ping_url = 'http://jobminestats.appspot.com/Ping/ag5zfmpvYm1pbmVzdGF0c3IMCxIFUGl4ZWwYuRcM.gif'
    def __init__(self, username, password):
        self.username=username
        self.password=password
        
        self.br = mechanize.Browser(factory=mechanize.RobustFactory())
        self.br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
        #self.br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071635 Fedora/4.0.1-1.fc9 Firefox/4.0.1')]
        
        self.br.open(self.ping_url).read()
        
    def safe_unicode(self,obj):
        try:
            return str(obj)
        except UnicodeEncodeError:
            # obj is unicode
            return unicode(obj).encode('utf-8')
    
    @retry(3)
    def login(self):
        print 'Logging In...'
        
        #self.br.open("https://learn.uwaterloo.ca/")
        self.br.open(self.cas_login)
        
        self.br.select_form(nr=0)
        self.br['username']=self.username
        self.br['password']=self.password
        response = self.br.submit().read()
        print 'Logged In'
        
        
    
            
    def get_course_links(self):
        print 'Finding courses...'
        links=list()
        for link in self.br.links():
            matches=re.match('[A-Z]+ [0-9]{3} - [A-Z][a-z]+ 20[0-9]{2}', link.text)
            if matches is not None:
                links.append(link)
        return links
        
    def _nice_regex(self,regex,content,group):
        res=re.search(regex,content)
        if res!=None:
            return res.group(group)
        else:
            return ''
    
    def convert_bytes(self, bytes):
        '''
            Stolen from http://www.5dollarwhitebox.org/drupal/node/84
        '''
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
        content_link=None
        for link_j in self.br.links():
            
            if link_j.text == 'Content':
                if content_link is None:
                    content_link=link_j
                    
        self.br.follow_link(content_link)
        
        print_dl_link=None
        for link_k in self.br.links(url_regex='print_download.d2l'):
            if print_dl_link is not None:
                print_dl_link = link_k
        
        r = self.br.follow_link(print_dl_link)
        
        
        page = r.read()
        #print page
        soup = BeautifulSoup.BeautifulSoup(page)
        table = soup.find(id='z_n')
        
        document_tree={}
        path_to_root = list()
        
        rows=table.findAll('tr')
        for row in rows[1:]:
            columns = row.findAll('td')
            
            depth = len(columns)-2
            
            cell = None
            for column in columns:
                if column.has_key('class') and column['class'] == 'd_gn':
                    cell = column
                   
            cell_str = ''.join(map(lambda x: x.__str__(), cell.contents ))
            
            is_heading = True
            if re.search('href=', cell_str):
                is_heading = False
                link = cell.a
                if hasattr(link, 'img'):
                    link.img.extract()
                
                title = ''.join(map(lambda x: x.__str__(), link.contents ))

                ou = self._nice_regex('\?ou\=([0-9]+)', link['href'], 1)
                tId = self._nice_regex('\&tId\=([0-9]+)', link['href'], 1)
                
                link_href = 'https://learn.uwaterloo.ca/d2l/lms/content/preview.d2l?tId=%s&ou=%s'%(tId, ou)
                
                
                cur_tree_node = document_tree
                for cur_path_node in path_to_root:
                    key = cur_path_node['title']
                    if not cur_tree_node.has_key(key):
                        cur_tree_node[key]=dict()
                    cur_tree_node=cur_tree_node[key]
                    
                cur_tree_node[title]=link_href
                
            else:
                cell_str = cell_str.replace('&nbsp;','').strip()
                cell_str = cell_str.replace('<strong>','').replace('</strong>','').strip()
                node = {'heading':True, 'title':cell_str}
                    
            
                if len(path_to_root) < depth:
                    path_to_root.append(node)
                else:
                    path_to_root=path_to_root[:depth]
                    path_to_root.append(node)
            
            
        return document_tree
            
    def download_tree(self, root, _path=list()):
        for k in root:
            path=_path[:]
            
            node = root[k]
            
            if type(node) is dict:
                path.append(k)
                self.download_tree(node, path)
            else:
                title = k
                url = node
                path = '/'.join(map(lambda x: x.replace('/','\/'), path))
                
                try:
                    os.makedirs(path)
                except:
                    pass
                    
                #print url
                page = self.br.open(url).read()
                soup = BeautifulSoup.BeautifulSoup(page)
                url = soup.find('iframe')['src']
                url_path = url.split('?')[0]
                split = urlparse.urlsplit(url_path)
                if split.netloc == '':
                    url = 'https://learn.uwaterloo.ca%s'%url_path
                else:
                    url = url_path
                    url_path = split.path
                    
                clean_url =  url.replace(' ', '%20')
                
                if 'https://learn.uwaterloo.ca/d2l/common/dialogs/' in url \
                    or 'https://learn.uwaterloo.ca/d2l/lor/viewer/view.d2l' in url:
                    pass
                
                else:
                    
                    file_name = os.path.split(url_path)[1]
                    
                    skip = False
                    for r in self.ignore_re:
                        if r.match(file_name) is not None:
                            print 'Skipping %s because it matches ignore regex "%s"'%(file_name, r.pattern)
                            skip = True
                    
                    if not skip:
                        path_and_filename = '%s/%s'%(path,file_name.strip('/'))
                    
                        if os.path.isfile(path_and_filename):
                            print ' - %s (Already Saved)'%path_and_filename
                        else:
                            content = self.br.open_novisit(clean_url).read()
                        
                            f = open(path_and_filename, 'w')
                            f.write(content)
                            f.close()
                        
                            print ' + %s (%s)'%(path_and_filename, self.convert_bytes(len(content)))
