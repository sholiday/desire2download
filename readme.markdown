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
* [Kartik Talwar](https://github.com/KartikTalwar)