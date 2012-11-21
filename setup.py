#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='Desire2Download',
    version='0.1.9',
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
)
