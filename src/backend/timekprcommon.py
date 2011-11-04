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

import json

#Enum
UNLOCK, LOCK = range(2)
NOBOUND, BOUND, NOBOUNDTODAY = range(3)
NOLIMIT, LIMIT, NOLIMITTODAY = range(3)
NORESET, RESET = range(2)
HR, MN = range(2)
LABELS = ['limits','time_from','time_to']


def get_version():
    return '0.4.0'

def check_if_admin():
    if geteuid() != 0:
        exit('Error: You need to have administrative privileges to run timekpr')

def get_variables(DEVACTIVE = False):
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
            if not from_today(allowfile):
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
            if not from_today(allowfile):
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


def convert_limits(limits,index):
    hr,mn = map(int,limits[index].split(':'))
    lims = hr * 3600 + mn * 60
    return lims


def getuserlimits(u):
    """Gets user from-to time limitations defined in time.conf
    
    Argument: username
    Return example:
        [0] = from ['0', '0', '0', '0', '0', '0', '0']
        [1] = to ['24', '24', '24', '24', '24', '24', '24']

    """
    hrFrom = ['0', '0', '0', '0', '0', '0', '0']
    hrTo =  ['24', '24', '24', '24', '24', '24', '24']
    mnFrom = ['0', '0', '0', '0', '0', '0', '0']
    mnTo = ['0', '0', '0', '0', '0', '0', '0']
    
    config = ConfigParser()
    var = get_variables()
    config.read(var['TIMEKPRDIR'] + '/timekprrc')
    
    if config.has_section(u):
	for i in range(7):
	    hrFrom[i] = config.getint(u,"fromHr_" + str(i))
	    mnFrom[i] = config.getint(u,"fromMn_" + str(i))
	    hrTo[i] = config.getint(u,"toHr_" + str(i))
	    mnTo[i] = config.getint(u,"toMn_" + str(i))

    #ls = parseutlist(parsetimeconf())
    #for user, [bfrom, bto] in ls:
    #    if u == user:
    #        return [bfrom, bto]
    return [hrFrom, hrTo, mnFrom, mnTo]
    
    
def read_user_settings(user = None, conffile = None):  
    limits = []
    time_from = []
    time_to = []
    status = dict()
    default = True
    
    if conffile:
	config = configparser.ConfigParser()
	config.read(str(conffile))
	if config.has_section(user):
	    default = False
	
    if default:
	config = configparser.ConfigParser()
	var = get_variables()
	config.read(str(var['TIMEKPRDIR'] + '/timekprdefault'))
	user = 'default'
    
    limits    = json.loads( config.get(user,LABELS[0]).replace("'",'"') )
    time_from = json.loads( config.get(user,LABELS[1]).replace("'",'"') )
    time_to   = json.loads( config.get(user,LABELS[2]).replace("'",'"') )   
    #status['locked'] = config.getboolean(user,'locked')
    status['locked'] = isuserlocked(user)
    status['limited'] = config.getboolean(user,'limited')
    status['limitedByDay'] = config.getboolean(user,'limitedByDay')
    status['bounded'] = config.getboolean(user,'bounded')
    status['boundedByDay'] = config.getboolean(user,'boundedByDay')
	    
    return limits, time_from, time_to, status
    
    
def parse_settings(settings):
    if settings[3]['limited']:
	if settings[3]['limitedByDay']:
	    limits = settings[0]
	    limits.pop(0)
	else:
	    limits = [settings[0][0]]*7
	    print limits
    else:
	limits = ['24:00']*7
	
    if settings[3]['bounded']:
	if settings[3]['boundedByDay']:
	    time_from = settings[1]
	    time_to =   settings[2]
	    time_from.pop(0)
	    time_to.pop(0)
	else:
	    time_from = [settings[1][0]]*7 
	    time_to =   [settings[2][0]]*7
    else:
	time_from = ['00:00']*7
	time_to =   ['24:00']*7
    return limits, time_from, time_to
