#!/usr/bin/env python
""" The "daemon service" for timekpr.
    Copyright / License: See COPYRIGHT.txt
"""

import re
from time import strftime, sleep, localtime, mktime, time as timenow
from os.path import split as splitpath, isfile, isdir, getmtime
from os import popen, mkdir, kill, remove
from glob import glob
from threading import Timer
from datetime import date, time, datetime

import sys

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gobject

#If DEVACTIVE is true, it uses files from local directory
DEVACTIVE = False

#IMPORT
if DEVACTIVE:
    from sys import path
    path.append('.')
from timekprpam import * # timekprpam.py
from timekprcommon import * # timekprcommon.py

#timekpr.conf variables (dictionary variable)
VAR = get_variables(DEVACTIVE)

#Check if admin/root
check_if_admin()

#Check if it exists, if not, create it
if not isdir(VAR['TIMEKPRDIR']):
    mkdir(VAR['TIMEKPRDIR'])
if not isdir(VAR['TIMEKPRWORK']):
    mkdir(VAR['TIMEKPRWORK'])

# Lists keeping track of users who has been notified
notifiedusers = []

# Keep track of todays date
THISDAY = strftime("%Y%m%d")

def logkpr(string,clear = 0):
    #To log: logkpr("Something")
    #To clear file and log: logkpr("Something",1)
    if VAR['DEBUGME'] != 'True':
        return
    if clear == 1:
        l = open(VAR['LOGFILE'], 'w')
    else:
        l = open(VAR['LOGFILE'], 'a')
    nowtime = strftime('%Y-%m-%d %H:%M:%S ')
    l.write(nowtime + string +'\n')
    print nowtime + string

def logOut(user, somefile = ''):
    logkpr('logOut called with user: %s and somefile: %s' % (user, somefile))
    if somefile != '':
        f = open(somefile, 'w').close()
    if fakerun != 'True':
	if is_session_alive(user):
	    logkpr('logOut: Attempting killing %s (SIGTERM)...' % user)
	    #this is a pretty bad way of killing a users processes, but we warned 'em
	    get_cmd_output('pkill -SIGTERM -u %s' % user)
	    sleep(5)
	    if is_session_alive(user):
		logkpr('logOut: Process still there, attempting force-killing %s (SIGKILL)...' % user)
		get_cmd_output('pkill -SIGKILL -u %s' % user)
    else:
	logkpr('LOGGED OUT')


## Using Linux-PAM to lock and disable users
def get_lock_lasts():
    #Returns the VAR['LOCKLASTS'] variable in seconds
    t=re.compile('(\d+) (second|minute|hour|day|week|month|year)s?').match(VAR['LOCKLASTS'])
    if not t:
        exit('Error: locklasts value "%s" is badly formatted, should be something like "1 week" or "2 hours"' % VAR['LOCKLASTS'])
    #n = time length
    #m = second|minute|hour|day|week|month|year
    (n,m)=(int(t.group(1)),t.group(2))
    #variable dictionary: multiply
    multiply = {
        'second': n,
        'minute': n * 60,
        'hour': n * 60 * 60,
        'day': n * 60 * 60 * 24,
        'week': n * 60 * 60 * 24 * 7,
        'month': n * 60 * 60 * 24 * 30
    }
    #Return in seconds (integer)
    return multiply[m]

def lock_account(u):
    #Locks user and sets the date in a file
    logkpr('lock_account called for user %s' % u)
    lockfile = VAR['TIMEKPRDIR'] + '/' + u + '.lock'
    f = open(lockfile, 'w')
    f.close()
    lockuser(u) # timekprpam.py

def check_lock_account():
    #Check if user should be unlocked and unlock them
    logkpr('check_lock_account called')
    #Find *.lock in VAR['TIMEKPRDIR']
    s = VAR['TIMEKPRDIR'] + '/*.lock'
    l = glob(s)
    for f in l:
        #Get username from filename - os.path.split
        u = splitpath(f)[1].replace('.lock', '')
        lastmodified = getmtime(f) #Get last modified time from username.lock file
        #Get time when lock should be lifted
        dtlock = float(lastmodified + get_lock_lasts())
        dtnow = float(timenow())
        #If time now is great than or equal to the time when lock should be lifted
        if dtnow >= dtlock:
            logkpr('check_lock_account: %s should be unlocked, unlocking..' % u)
            unlockuser(u)
            logkpr('check_lock_account: removing %s.lock file..' % u)
            remove(f)

## File defs
def is_file_ok(fname):
    #File exists and is today's?
    if isfile(fname) and from_today(fname):
        return True
    return False

def get_users():
    u = get_cmd_output('users')
    u = u.split()
    return set(u)
    #u = set(u)
    #return list(u)

#def get_users():
    #users = list()
    #rawusers = get_cmd_output('last')
    #rawloggedusers = re.findall('(^.*)still logged in',rawusers,re.M)
    #for i in rawloggedusers:
	#users.append(re.split(' ',i)[0])
    #users = set(users)
    #return users

def is_session_alive(user):
    # Checking if session process still running
    # Should it check against username and pid?
    # Returns:    True if process is still there (user logged in),
    #        False if user has logged out
    for u in get_users():
        if u == user:
            return True
    return False

    
def add_time(tfile, username):
    #Adds time to the timefile
    time = get_time(tfile, username) + VAR['POLLTIME']
    f = open(tfile, 'w')
    f.write(str(time))
    return time
    
def get_time(tfile,username):
    time = 0
    if is_file_ok(tfile):
        t = open(tfile)
        time = int(t.readline())
        t.close()
    return time
    
def time_left(username):
    try:
	timeleft = logouttime[username] - int(timenow())
    except KeyError:
	timeleft = -1
    return timeleft
    
def thread_it(sleeptime, command, *args):
    t = Timer(sleeptime, command, args)
    t.start()
    return t

def add_notified(u):
    #Adds username to notifiedusers list, so it does not re-notify them
    try:
        notifiedusers.index(u)
    except ValueError:
        notifiedusers.append(u)

def is_notified(u):
    #Checks if username is already in notifiedusers list
    try:
        notifiedusers.index(u)
    except ValueError:
        return False
    return True

def remove_notified(u):
    #Removes username from notifiedusers list, so it does not re-notify them
    try:
        notifiedusers.index(u)
    except ValueError:
        return
    notifiedusers.remove(u)

logkpr('Starting timekpr version %s' % get_version())
logkpr('Variables: GRACEPERIOD: %s POLLTIME: %s DEBUGME: %s LOCKLASTS: %s' % (\
        VAR['GRACEPERIOD'],
        VAR['POLLTIME'],
        VAR['DEBUGME'],
        VAR['LOCKLASTS']))
logkpr('Directories: LOGFILE: %s TIMEKPRDIR: %s TIMEKPRWORK: %s TIMEKPRSHARED: %s' % (\
        VAR['LOGFILE'],
        VAR['TIMEKPRDIR'],
        VAR['TIMEKPRWORK'],
        VAR['TIMEKPRSHARED']))

def logitout(username,late):        
    
    allowfile = VAR['TIMEKPRWORK'] + '/' + username + '.allow'
    latefile = VAR['TIMEKPRWORK'] + '/' + username + '.late'
    logoutfile = VAR['TIMEKPRWORK'] + '/' + username + '.logout'
		    
    # Kicked out because time frame is over
    if not late:
	logkpr('Current hour greater than the defined hour in conffile for user %s' % username)
	# Has the user been given extended login hours?
	if isfile(allowfile):
	    if not from_today(allowfile):
		logkpr('Extended login hours detected from %s.allow, but not from today' % username)
		# Has the user been late-kicked today?
		if isfile(latefile):
		    if from_today(latefile):
			logkpr('User %s has been late-kicked today' % username)
			
			thread_it(0.5, logOut, username)
			remove(allowfile)
			#Lock account
			#lock_account(username)
		    else:
			logkpr('User %s has NOT been late-kicked today' % username)
			
			thread_it(float(VAR['GRACEPERIOD']), logOut, username, latefile)
			thread_it(float(VAR['GRACEPERIOD']), remove, allowfile)
			add_notified(username)
			thread_it(VAR['GRACEPERIOD'], remove_notified, username)
			#lock_account(username)
            else:
		logkpr('Extended login hours detected - %s.allow is from today' % username)
        else:
	    # User has not been given extended login hours
	    logkpr('Extended hours and %s.allow file not detected, %s not in allowed period from-to' % (username, username))
	    if isfile(latefile) and from_today(latefile):
		logkpr('User %s has been late-kicked today' % username)
		
		thread_it(0.5, logOut, username)
		#Lock account
		#lock_account(username)
            else:
		logkpr('User %s has NOT been late-kicked today' % username)
		
		thread_it(float(VAR['GRACEPERIOD']), logOut, username, latefile)
		add_notified(username)
		thread_it(VAR['GRACEPERIOD'], remove_notified, username)
		#lock_account(username)

    # Kicked out because limit exeeded
    else:
	logkpr('Exceeded today\'s access login duration user %s' % username)
	# Has the user already been kicked out?
	if isfile(logoutfile):
	    logkpr('Found %s.logout' % username)
	    # Was he kicked out today?
	    if from_today(logoutfile):
		logkpr('%s has been kicked out today' % username)
		
		thread_it(0.5, logOut, username)
		#Lock account
		#lock_account(username)
            else:
		# The user has not been kicked out today
		logkpr('%s has been kicked out, but not today' % username)
		
		thread_it(float(VAR['GRACEPERIOD']), logOut, username, logoutfile)
		add_notified(username)
		thread_it(VAR['GRACEPERIOD'], remove_notified, username)
		#lock_account(username)
        else:
	    # The user has not been kicked out before
	    logkpr('Not found: %s.logout' % username)
	    
	    thread_it(float(VAR['GRACEPERIOD']), logOut, username, logoutfile)
	    add_notified(username)
	    thread_it(VAR['GRACEPERIOD'], remove_notified, username)
	    #lock_account(username)
                   
                   
#Main code begin

fakerun = sys.argv[1]

users = set()
timers = dict()
logouttime = dict()
stillusers = set()

while (True):
    # Check if any accounts should be unlocked and re-activate them
    check_lock_account()
    
    # Get the usernames and PIDs of sessions
    usrs = get_users()
    
    if users ^ usrs: #someone has login or logout
	newusers = usrs - users
	goneusers = users - usrs
	stillusers = usrs & users
	
	for username in newusers:
	    logkpr('New user %s have logged in' %username)
	    conffile = VAR['TIMEKPRDIR'] + '/' + username
		    
	    if not is_notified(username):
		# Read lists: from, to and limit
		settings = read_user_settings(username, VAR['TIMEKPRDIR'] + '/timekprrc')
		limited = settings[3]['limited']
		bounded = settings[3]['bounded']
		
		if limited or bounded:
		    limits, bfrom, bto = parse_settings(settings)
		    
		    timefile = VAR['TIMEKPRWORK'] + '/' + username + '.time'
		    #allowfile = VAR['TIMEKPRWORK'] + '/' + username + '.allow'
		    #latefile = VAR['TIMEKPRWORK'] + '/' + username + '.late'
		    #logoutfile = VAR['TIMEKPRWORK'] + '/' + username + '.logout'
		    time = int(get_time(timefile, username))
		    '''Is the user allowed to be logged in at this time?
		    We take it for granted that if they are allowed to login all day ($default_limit) then
		    they can login whenever they want, ie they are normal users'''
	    
		    # Get current day index and hour of day
		    index = int(strftime("%w"))
		    #hour = int(strftime("%H"))
		    #minute = int(strftime("%M"))
		    
		    logkpr('User: %s Day-Index: %s' % (username, index))
		    
		    lims = convert_limits(limits,index)
		    fromHM = bfrom[index]
		    toHM = bto[index]
		    toHMS = toHM + '59'
		    #fromHR,fromMN = convert_bounds(bfrom,index)
		    #toHR,toMN = convert_bounds(bto,index)
		    nowtime  = datetime.now()
		    today = datetime.date(nowtime)
		    timefrom = datetime.combine(today,datetime.time(datetime.strptime(fromHM,'%H%M')))
		    timeto   = datetime.combine(today,datetime.time(datetime.strptime(toHMS,'%H%M%S')))
		    #timefrom = datetime.combine(datetime.date(nowtime),timefrom)
		    #timeto   = datetime.combine(datetime.date(nowtime),timeto)
		    leftwindow = (timeto - nowtime).total_seconds()
		    lefttime = lims - time
		    timebeforelogut = min(leftwindow, lefttime)
		    if leftwindow > lefttime:
			late = 1
		    else:
			late = 0
		
		    timers[username] = thread_it(timebeforelogut,logitout,username,late)
		    logouttime[username] = int(timenow()) + timebeforelogut
	    
	for username in goneusers:
	    try:
		timers[username].cancel()
		logouttime.pop(username)
		logkpr('User: %s is gone from the system, logout action canceled' %username)
	    except KeyError:
		logkpr('User: %s is gone from the system, but no logout action was running' %username)
    else:
	stillusers = users
	
    users = usrs
	
    for username in stillusers:
	timefile = VAR['TIMEKPRWORK'] + '/' + username + '.time'
	#TODO:Add but not get
	time = add_time(timefile, username)
	logkpr('User: %s Seconds-passed: %s' % (username, time))
            
    # Done checking all users, sleeping
    logkpr('Finished checking all users, sleeping for %s seconds' % VAR['POLLTIME'])
    sleep(VAR['POLLTIME'])

