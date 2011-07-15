#!/usr/bin/env python
""" Common variables and definitions for timekpr.
    Copyright / License: See COPYRIGHT.txt
"""

try:
    # python3
    import configparser
except ImportError:
    # python2.x
    import ConfigParser as configparser

from os.path import isfile, getmtime
from os import geteuid
from time import strftime, localtime
from timekprpam import *

def get_version():
    return '0.4.0'

def check_if_admin():
    if geteuid() != 0:
        exit('Error: You need to have administrative privileges to run timekpr')

def get_variables(DEVACTIVE):
    #Read timekpr.conf
    fconf = '/etc/timekpr.conf'
    if DEVACTIVE:
        fconf = './etc/timekpr.conf'
    if not isfile(fconf):
        exit('Error: Could not find configuration file %s' % fconf)

    conf = configparser.ConfigParser()
    try:
        conf.read(fconf)
    except configparser.ParsingError:
        exit('Error: Could not parse the configuration file properly %s' % fconf)

    #Creating a dictionary file
    var = dict()
    #VARIABLES
    #VERSION GRACEPERIOD POLLTIME DEBUGME LOCKLASTS LOGFILE TIMEKPRDIR TIMEKPRWORK TIMEKPRSHARED
    #Exits or sets default if not found

    try:
        var['VERSION'] = conf.get("general", "version")
    except configparser.NoOptionError:
        exit('Error: Could not detect variable version in configuration file %s' % fconf)
    if var['VERSION'] < '0.2.0':
        exit('Error: You have an old /etc/timekpr.conf - remove and reinstall timekpr')

    try:
        var['GRACEPERIOD'] = int(conf.get("variables", "graceperiod"))
    except configparser.NoOptionError:
        var['GRACEPERIOD'] = 120

    try:
        var['POLLTIME'] = int(conf.get("variables", "polltime"))
    except configparser.NoOptionError:
        var['POLLTIME'] = 45

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

    try:
        var['TIMEKPRSHARED'] = conf.get("directories", "timekprshared")
    except configparser.NoOptionError:
        var['TIMEKPRSHARED'] = '/usr/share/timekpr'
    if DEVACTIVE:
        var['TIMEKPRSHARED'] = './gui'

    return var

def get_cmd_output(cmd):
    #TODO: timekpr-gui.py: Use it for "/etc/init.d/timekpr status" and a button enable/disable
    from os import popen
    #Execute a command, returns its output
    out = popen(cmd)
    return out.read()

def from_today(fname):
    # Returns True if a file was last modified today
    fdate = strftime("%Y%m%d", localtime(getmtime(fname)))
    today = strftime("%Y%m%d")
    return fdate == today

def is_late(bto, allowfile):
    # Get current day index and hour of day
    index = int(strftime("%w"))
    hour = int(strftime("%H"))
    if (hour > bto[index]):
        if isfile(allowfile):
            if not fromtoday(allowfile):
                return True
            else:
                return False
        else:
            return True
    else:
        return False

def is_past_time(limits, time):
    index = int(strftime("%w"))
    if (time > limits[index]):
        return True
    else:
        return False

def is_early(bfrom, allowfile):
    # Get current day index and hour of day
    index = int(strftime("%w"))
    hour = int(strftime("%H"))
    if (hour < bfrom[index]):
        if isfile(allowfile):
            if not fromtoday(allowfile):
                return True
            else:
                return False
        else:
            return True
    else:
        return False

def is_restricted_user(username, limit):
    if not isuserlimited(username) and limit == 86400:
        return False
    else:
        return True

def read_user_settings(user = None, confFile = None):   

    limits = [list(),list()]
    time_from = [list(),list()]
    time_to = [list(),list()]
    limits[0] = [3, 3, 3, 3, 3, 3, 3]
    limits[1] = [0, 0, 0, 0, 0, 0, 0]
    time_from[0] = [0, 0, 0, 0, 0, 0, 0]
    time_from[1] = [0, 0, 0, 0, 0, 0, 0]
    time_to[0] = [24, 24, 24, 24, 24, 24, 24]
    time_to[1] = [0, 0, 0, 0, 0, 0, 0]
    
    
    if confFile:
	config = ConfigParser()
	config.read("/home/simone/timekprrc")
    
	if config.has_section(user):
	    for i in range(7):
		time_from[0][i] = config.getint(user,"fromHr_" + str(i))
		time_from[1][i] = config.getint(user,"fromMn_" + str(i))
		time_to[0][i] = config.getint(user,"toHr_" + str(i))
		time_to[1][i] = config.getint(user,"toMn_" + str(i))
		limits[0][i] = config.getint(user,"limitHr_" + str(i))
		limits[1][i] = config.getint(user,"limitMn_" + str(i))

    return limits, time_from, time_to
