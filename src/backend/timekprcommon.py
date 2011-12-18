#!/usr/bin/env python
""" Common variables and definitions for timekpr.
    Copyright / License: See COPYRIGHT.txt
"""

from os import popen
from os.path import isfile, getmtime
from time import strftime, localtime
import json
try:
    # python3
    import configparser
except ImportError:
    # python2.x
    import ConfigParser as configparser
    
from timekprpam import *


# Constants
UNLOCK, LOCK = range(2)
NOBOUND, BOUND, NOBOUNDTODAY = range(3)
NOLIMIT, LIMIT, NOLIMITTODAY = range(3)
NORESET, RESET = range(2)
HR, MN = range(2)


def get_version():
    return '0.4.0-alpha'

def get_variables():
    """Return a dictionary containing the following variables:
    VERSION GRACEPERIOD POLLTIME DEBUGME LOCKLASTS LOGFILE TIMEKPRDIR TIMEKPRWORK TIMEKPRSHARED
    """
    fconf = '/etc/timekpr/timekpr.conf'
    if not isfile(fconf):
        exit('Error: Could not find configuration file %s' % fconf)

    conf = configparser.ConfigParser()
    try:
        conf.read(fconf)
    except configparser.ParsingError:
        exit('Error: Could not parse the configuration file properly %s' % fconf)

    var = dict()

    try:
        var['VERSION'] = conf.get("general", "version")
    except configparser.NoOptionError:
        exit('Error: Could not detect variable version in configuration file %s' % fconf)

    try:
        var['GRACEPERIOD'] = int(conf.get("variables", "graceperiod"))
    except configparser.NoOptionError:
        var['GRACEPERIOD'] = 120

    try:
        var['POLLTIME'] = int(conf.get("variables", "polltime"))
    except configparser.NoOptionError:
        var['POLLTIME'] = 15

    try:
        var['LOCKLASTS'] = conf.get("variables", "locklasts")
    except configparser.NoOptionError:
        var['LOCKLASTS'] = '1 hour'

    try:
        var['DEBUGME'] = conf.get("variables", "debugme")
    except configparser.NoOptionError:
        var['DEBUGME'] = 'True'

    try:
        var['LOGFILE'] = conf.get("directories", "logfile")
    except configparser.NoOptionError:
        var['LOGFILE'] = '/var/log/timekpr.log'

    try:
        var['TIMEKPRDIR'] = conf.get("directories", "timekprdir")
    except configparser.NoOptionError:
        var['TIMEKPRDIR'] = '/etc/timekpr'

    try:
        var['TIMEKPRWORK'] = conf.get("directories", "timekprwork")
    except configparser.NoOptionError:
        var['TIMEKPRWORK'] = '/var/lib/timekpr'

    return var

def is_fakerun():
    if isfile('/etc/timekpr/fakerun'):
        return 1
    return 0
    
def get_cmd_output(cmd):
    # Execute a shell command and returns its output
    out = popen(cmd)
    return out.read()

def from_today(fname):
    # Returns True if a file was last modified today
    fdate = strftime("%Y%m%d", localtime(getmtime(fname)))
    today = strftime("%Y%m%d")
    return fdate == today

def convert_limits(limits,index):
    # Return the duration limit expressed in minute
    hr = int(limits[index][0:2])
    mn = int(limits[index][2:4])
    lims = hr * 3600 + mn * 60
    return lims
    
def convert_bounds(bounds,index):
    # Return the bound time string as integer
    hr = int(bounds[index][0:2])
    mn = int(bounds[index][2:4])
    return hr,mn 
    
def read_user_settings(user=None, conffile=None):  
    """Read user settings from timekprrc file
    limits, time_from, time_to are lists of 8 strings
    the first 7 element are the time values corresponding to the 7 days of the week
    the 8th element is the time value corresponding to the every day configuration
    """
    limits = []
    time_from = []
    time_to = []
    status = dict()
    
    if conffile:
        config = configparser.ConfigParser()
        config.read(str(conffile))
    #If the user section is not found default value is loaded from a default-value file
    if not config.has_section(user):
        config = configparser.ConfigParser()
        var = get_variables()
        config.read(str(var['TIMEKPRDIR'] + '/timekprdefault'))
        user = 'default'
    
    # Get json dumped array from the conf file and convert it to array
    limits = json.loads(config.get(user,'limits').replace("'",'"'))
    time_from = json.loads(config.get(user,'time_from').replace("'",'"'))
    time_to = json.loads(config.get(user,'time_to').replace("'",'"'))
    
    #TODO: Get locked from the conffile
    status['locked'] = isuserlocked(user)
    status['limited'] = config.getboolean(user,'limited')
    status['limitedByDay'] = config.getboolean(user,'limitedByDay')
    status['bounded'] = config.getboolean(user,'bounded')
    status['boundedByDay'] = config.getboolean(user,'boundedByDay')
        
    return limits, time_from, time_to, status
    
def parse_settings(settings):
    # settings[0] is the limits vector
    # settings[1] is the time_from vector
    # settings[1] is the time_to vector
    # settings[3] is the status vector
    # limits can be 0 if the user is not limited or 
    if settings[3]['limited']:
        if settings[3]['limitedByDay']:
            limits = settings[0]
            limits.pop()
        else:
            limits = [settings[0][7]]*7
    else:
        limits = 0
    
    if settings[3]['bounded']:
        if settings[3]['boundedByDay']:
            time_from = settings[1]
            time_to = settings[2]
            time_from.pop()
            time_to.pop()
        else:
            time_from = [settings[1][7]]*7 
            time_to = [settings[2][7]]*7
    else:
        time_from = 0
        time_to = 0
    
    return limits, time_from, time_to
