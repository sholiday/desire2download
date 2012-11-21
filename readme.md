# Desire2Download

Desire 2 Download is a tool to download all of the content from the University of Waterloo's
new learning management system which uses Desire2Learn instead of the old Angel
based UWACE.

d2d was inspired by Jamie Wong's fabulous [UWAngel-CLI](https://github.com/phleet/UWAngel-CLI)
written in Ruby.

d2d is somewhat hacky and has not been tested extensively. If you do find a bug,
please [let us know](https://github.com/sholiday/desire2download/issues)


## Installation

**Automagic**

```sh
pip install desire2download
```

**Hipster**

```sh
wget https://github.com/sholiday/Desire2Download/archive/master.zip
unzip master && cd desire2download-master
python setup.py install
```


## Usage


|    **Parameters**   |    **Description**    |
|:-------------------:|:---------------------:|
| **u** or *username* | Your quest userid     |
| **p** or *password* | Your quest password   |
| **i** or *ignore*   | Ignore certain files  |
| **c** or *courses*  | Ignore certain courses|


Just browse to the folder you want to download the files in, type `d2d` and hit enter!


**Basic Usage**

```
ktalwar@ubuntu:~/Desktop$ d2d
```


**Username filled out**

```sh
$ d2d -u ktalwar
```


**Username and password filled out**

```sh
$ d2d -u ktalwar -p icanhazcatz
```

**Ignore certain files**

```sh
$ d2d -i ".*.ppt"
```

**Ignore certain courses**

Ignores anything starting with `M`

```sh
$ d2d -c "M+"
```

Ignores anything starting with `M` or `P`

```sh
$ d2d -c "^[MP]+"
```


Ignores anything containing `22`

```sh
d2d -c ".+(22).+"
```


**Full complex example**

```sh
d2d -u scholida -p hecanhazcatz -i ".*.ppt" -c "CS+"
```

```
Logging In...
Logged In
Finding courses...
ECE 224 - Fall 2011
 + ECE 224 - Fall 2011/Labs/Lab Tools Tutorial.html (1.70K)
 + ECE 224 - Fall 2011/Labs/Lab 1/lab1_checklist-s2010.pdf (107.65K)
   ...
```

*d2d will not download a file if it has been already saved.*



## Credits

* [Stephen Holiday](http://stephenholiday.com)
* [Ansis Brammanis](https://github.com/aibram)
* [Kartik Talwar](http://kartikt.com)
* [Jacob Parry](https://www.jacobparry.ca)


## Legal Stuff

See [LICENSE](https://github.com/sholiday/desire2download/blob/master/LICENSE) for details.
