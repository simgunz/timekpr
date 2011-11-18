#!/usr/bin/env python
""" A library timekpr uses to read/edit Linux-PAM configuration files.
    Currently using modules: time, access
    Warning: Not all Linux-PAM possibilities are supported!
    Copyright / License: See COPYRIGHT.txt
"""

import re
from time import strftime
try:
    # python3
    import configparser
except ImportError:
    # python2.x
    import ConfigParser as configparser


def get_conf_section(conffile):
    """
    Returns the content of the timekpr section in a file (access.conf or time.conf).
    Also used to check if the timekpr section is set correctly.
    
    Arguments:
      conffile (string)
    """
    
    s = open(conffile).read()
    check = re.compile('## TIMEKPR START|## TIMEKPR END').findall(s)    
    # If the timekpr section lines '## TIMEKPR START' or '## TIMEKPR END' are not
    # found, exit with an error.
    if not len(check):
        exit("Error: Could not find timekpr section in '%s'" % conffile)
    elif len(check) != 2:
        exit("Error: Incorrect format of timekpr section in '%s'" % conffile)        
    # Otherwise, get and return the content between the section lines.
    m = re.compile('## TIMEKPR START\n(.*)## TIMEKPR END', re.S).findall(s)
    return m[0]

def parse_access_conf(accessfile='/etc/security/access.conf'):
    """
    Parses the timekpr section in access.conf
    
    Returns:
      A list with the (locked) usernames.
      Example: ['niania','wawa']
    """
    s = get_conf_section(accessfile)
    m = re.compile('^-:([^:\s]+):ALL$', re.M).findall(s)
    return m

def convert_time_line(hfrom, hto):
    """Converts a list of hours (from and to limits) into a time.conf line
    Does NOT support all of the features of time.conf, e.g. negation!
    
    Arguments:
      hfrom, hto: lists of 7 strings with the following format: hhmm
        Example: ['0000','0000','0000','1000','1130','1135','2359']
    
    Returns:
      The time part of the time.conf compatible formatted string
      Example: Al0700-2230
               Su0700-2200 | Mo0700-2200 | Tu0700-2200 | We0700-2200 | Th1100-2200 | Fr0700-2200 | Sa0700-2200
    """
    if len(hfrom) != 7 or len(hto) != 7:
        exit('Error: convert_time_line accepts from-to lists of 7 items each')
    # If all same:
    mfrom = re.compile('^(\d+) \\1 \\1 \\1 \\1 \\1 \\1$').search(' '.join(hfrom))
    mto = re.compile('^(\d+) \\1 \\1 \\1 \\1 \\1 \\1$').search(' '.join(hto))
    # Return Al0700-2400
    if mfrom and mto:
        return 'Al' + mfrom.group(1) + '-' + mto.group(1)
    
    #or if all days separate
    su = 'Su' + hfrom[0] + '-' + hto[0]
    mo = 'Mo' + hfrom[1] + '-' + hto[1]
    tu = 'Tu' + hfrom[2] + '-' + hto[2]
    we = 'We' + hfrom[3] + '-' + hto[3]
    th = 'Th' + hfrom[4] + '-' + hto[4]
    fr = 'Fr' + hfrom[5] + '-' + hto[5]
    sa = 'Sa' + hfrom[6] + '-' + hto[6]
    return ' | '.join([su, mo, tu, we, th, fr, sa])

def mk_time_conf_line(username, hfrom, hto):
    """Makes the time.conf line - uses convert_time_line()

    Arguments:
      Example:
        username = 'maria'
        hfrom = ['7000', '7000', '7000', '7000', '7000', '7000', '7000']
        hto = ['2200', '2200', '2200', '2200', '2200', '2200', '2200']
    Returns:
      Example:
        '*;*;maria;Al0700-2200'
    """
    return '*;*;' + username + ';' + convert_time_line(hfrom, hto)
