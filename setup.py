#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='Desire2Download',
    version='0.1.7',
    description='Download all of the content from the University of Waterloo\'s Desire2Learn LMS',
    author='Stephen Holiday',
    author_email='stephen.holiday@gmail.com',
    url='https://github.com/sholiday/desire2download',
    py_modules=['desire2download'],
    install_requires=(
        'mechanize',
        'BeautifulSoup',
   ),
   scripts=['d2d.py'],
   entry_points={
       'console_scripts': [
           'd2d = d2d:main',
       ]
   },
   classifiers=[
         'Development Status :: 3 - Alpha',
         'Environment :: Console',
         'Intended Audience :: Developers',
         'Intended Audience :: Education',
         'Intended Audience :: End Users/Desktop',
         'License :: OSI Approved :: Apache Software License',
         'Operating System :: MacOS :: MacOS X',
         'Operating System :: POSIX',
         'Operating System :: Unix',
         'Programming Language :: Python :: 2.6',
         'Programming Language :: Python :: 2.7',
         'Programming Language :: Python',
         'Topic :: Education',
   ],
   long_description="""

   d2d is a tool to download all of the content from the University of Waterloo's
   new learning management system which uses Desire2Learn instead of the old Angel
   based UWACE.

   d2d was inspired by Jamie Wong's fabulous UWAngel-CLI (https://github.com/phleet/UWAngel-CLI)
   written in Ruby.

   d2d is somewhat hacky and has not been tested extensively. If you do find a bug,
   please let me know (stephen.holiday@gmail.com).

   To install, just do:

       python setup.py install

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

   Credits: Stephen Holiday, Ansis Brammanis and Kartik Talwar
   """
)
