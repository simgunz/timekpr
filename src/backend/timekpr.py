#!/usr/bin/env python
""" The daemon service for timekpr.
    Copyright / License: See COPYRIGHT.txt
"""


import sys
import re
from os import popen, mkdir, kill, remove
from os.path import split as splitpath, isfile, isdir, getmtime
from glob import glob
from threading import Timer
from time import strftime, sleep, time as timenow
from datetime import date, time, datetime, timedelta
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

from timekprpam import *
from timekprcommon import *


VAR = get_variables() # timekpr.conf variables (dictionary variable)
THISDAY = strftime("%Y%m%d") # Keep track of todays date
FAKERUN = is_fakerun()

def logkpr(string,clear = 0):
    """Log events to the timekpr log file
    To log: logkpr("Something")
    To clear file and log: logkpr("Something",1)
    """
    nowtime = strftime('%Y-%m-%d %H:%M:%S ')
    if FAKERUN:
        print nowtime + string
    else:
        if VAR['DEBUGME'] != 'True':
            return
        if clear == 1:
            l = open(VAR['LOGFILE'], 'w')
        else:
            l = open(VAR['LOGFILE'], 'a')
        l.write(nowtime + string +'\n')
    
    

def logOut(user, somefile = ''):
    """Log out the user from the system
    """
    logkpr('logOut called with user: %s and somefile: %s' % (user, somefile))
    if somefile != '':
        f = open(somefile, 'w').close()
    if not FAKERUN:
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
'''    
def get_lock_lasts():
    # Returns the VAR['LOCKLASTS'] variable in seconds
    
    t=re.compile('(\d+) (second|minute|hour|day|week|month|year)s?').match(VAR['LOCKLASTS'])
    if not t:
        exit('Error: locklasts value "%s" is badly formatted, should be something like "1 week" or "2 hours"' % VAR['LOCKLASTS'])
    # n = time length
    # m = second|minute|hour|day|week|month|year
    (n,m)=(int(t.group(1)),t.group(2))
    # Variable dictionary: multiply
    multiply = {
        'second': n,
        'minute': n * 60,
        'hour': n * 60 * 60,
        'day': n * 60 * 60 * 24,
        'week': n * 60 * 60 * 24 * 7,
        'month': n * 60 * 60 * 24 * 30
    }
    return multiply[m]

def lock_account(u):
    # Locks user and sets the date in a file
    logkpr('lock_account called for user %s' % u)
    lockfile = VAR['TIMEKPRDIR'] + '/' + u + '.lock'
    f = open(lockfile, 'w')
    f.close()
    lockuser(u) # timekprpam.py

def check_lock_account():
    # Check if user should be unlocked and unlock them
    logkpr('check_lock_account called')
    # Find *.lock in VAR['TIMEKPRDIR']
    s = VAR['TIMEKPRDIR'] + '/*.lock'
    l = glob(s)
    for f in l:
        # Get username from filename - os.path.split
        u = splitpath(f)[1].replace('.lock', '')
        lastmodified = getmtime(f) #Get last modified time from username.lock file
        # Get time when lock should be lifted
        dtlock = float(lastmodified + get_lock_lasts())
        dtnow = float(timenow())
        # If time now is great than or equal to the time when lock should be lifted
        if dtnow >= dtlock:
            logkpr('check_lock_account: %s should be unlocked, unlocking..' % u)
            unlockuser(u)
            logkpr('check_lock_account: removing %s.lock file..' % u)
            remove(f)
'''
def is_file_ok(fname):
    # File exists and is today's?
    if isfile(fname) and from_today(fname):
        return True
    return False

def get_users():
    u = get_cmd_output('users')
    u = u.split()
    return set(u)

def is_session_alive(user):
    """Check if session process still running
    Should it check against username and pid?
    
    Returns:
      True if process is still there (user logged in),
      False if user has logged out
    """
    for u in get_users():
        if u == user:
            return True
    return False
    
def add_time(tfile, username):
    # Adds time to the timefile
    time = get_time(tfile, username) + VAR['POLLTIME']
    f = open(tfile, 'w')
    f.write(str(time))
    return time
    
def get_time(tfile,username):
    # Return time from the timefile
    time = 0
    if is_file_ok(tfile):
        t = open(tfile)
        time = int(t.readline())
        t.close()
    return time
    
def time_left(username):
    # Return the time lef before logout for the user
    try:
        timeleft = logouttime[username] - int(timenow())
    except KeyError:
        timeleft = -1
    return timeleft
    
def thread_it(sleeptime, command, *args):
    # Run a command after a given time
    t = Timer(sleeptime, command, args)
    t.start()
    return t
    
def log_it_out(username,logoutreason):        
    # Check and eventually logout a user after a grace period time
    allowfile = VAR['TIMEKPRWORK'] + '/' + username + '.allow'
    logoutfile = VAR['TIMEKPRWORK'] + '/' + username + '.logout'
    
    if logoutreason == 0:
        logkpr('Exceeded today\'s access login duration for user %s' % username)
        graceperiod=float(VAR['GRACEPERIOD'])
    elif logoutreason == 1:
        logkpr('Current time greater than the time defined in timekprrc for user %s' % username)
        graceperiod=float(VAR['GRACEPERIOD'])
    else:
        logkpr('Current time less than the time defined in timekprrc for user %s' % username)
        graceperiod=0.5
        
        
    if isfile(allowfile) and from_today(allowfile):
        logkpr('Extended login detected - %s.allow exists and is from today' % username)  
    else:
        # User has not been given extended login hours
        logkpr('Extended login not detected - %s.allow file not detected' % (username))
        if isfile(logoutfile) and from_today(logoutfile):
            logkpr('User %s has been kicked out today' % username)
            thread_it(0.5, logOut, username)
        else:
            logkpr('User %s has NOT been kicked out today' % username)
            thread_it(graceperiod, logOut, username, logoutfile)                   
                   
                   
if __name__ == '__main__':
    logkpr('Starting timekpr version %s' % get_version())
    logkpr('Variables: GRACEPERIOD: %s POLLTIME: %s DEBUGME: %s LOCKLASTS: %s' % (\
            VAR['GRACEPERIOD'],
            VAR['POLLTIME'],
            VAR['DEBUGME'],
            VAR['LOCKLASTS']))
    logkpr('Directories: LOGFILE: %s TIMEKPRDIR: %s TIMEKPRWORK: %s' % (\
            VAR['LOGFILE'],
            VAR['TIMEKPRDIR'],
            VAR['TIMEKPRWORK']))

    if not isdir(VAR['TIMEKPRWORK']):
        mkdir(VAR['TIMEKPRWORK'])
       
    users = set()
    timers = dict()
    logouttime = dict()

    while (True):
        # Check if any accounts should be unlocked and re-activate them
        #TODO: Manage lock policy
        #check_lock_account()
        
        # Get the usernames and PIDs of sessions
        usr = get_users()
        
        # Managing everythin with Timers 99% of the times this block is skipped and no unuseful check is done
        if users ^ usr: #someone has login or logout
            newusers = usr - users
            goneusers = users - usr
            stillusers = usr & users
        
            # Parse new users
            for username in newusers:
                logkpr('New user %s have logged in' %username)
                    
                # Read lists: from, to and limit
                settings = read_user_settings(username, VAR['TIMEKPRDIR'] + '/timekprrc')
                limits, bfrom, bto = parse_settings(settings)
            
                # If limits and bfrom are both null the user is not limited
                if limits or bfrom:                   
                    timebeforelogut = None
                    # Get current day index and hour of day
                    dayindex = int(strftime("%w"))
                    logkpr('User: %s Day-Index: %s' % (username, dayindex))
                    
                    # If limits is not null, the time before logout is calculated parsing the time limit of the user
                    if limits:
                        timefile = VAR['TIMEKPRWORK'] + '/' + username + '.time'
                        time = int(get_time(timefile, username))
                        lims = convert_limits(limits,dayindex)
                        limit_lefttime = lims - time
                        timebeforelogut = max(0,limit_lefttime)
                        logoutreason = 0                    
                    
                    # If bfrom is not null, the time before logout is calculated parsing the time frame of the user
                    if bfrom:
                        fromHM = bfrom[dayindex]
                        toHM = bto[dayindex]
                        
                        # If fromHM == toHM the user can login all day long, so it is not actually limited
                        if fromHM != toHM:
                            nowdatetime = datetime.now()
                            todaydate = datetime.date(nowdatetime)
                            timefrom = datetime.combine(todaydate,datetime.time(datetime.strptime(fromHM,'%H%M')))
                            timeto = datetime.combine(todaydate,datetime.time(datetime.strptime(toHM,'%H%M')))
                            
                            # If timefrom less than timeto means that the allowed time frame straddles the midnight
                            # If current time greater than timefrom means that timeto falls is in the next day
                            if timeto < timefrom:
                                if nowdatetime > timefrom:
                                    tomorrow = datetime.date(nowdatetime + timedelta(days=1))
                                    timeto = datetime.combine(tomorrow,datetime.time(datetime.strptime(toHM,'%H%M')))
                            
                            bound_lefttime = max(0,(timeto - nowdatetime).total_seconds())
                            logoutreason = 1
                        
                            # Determine the minimum time before logout between limit and bound left time
                            if timebeforelogut is not None:
                                timebeforelogut = min(bound_lefttime, timebeforelogut)
                                if bound_lefttime > limit_lefttime:
                                    logoutreason = 0
                            else:
                                timebeforelogut = bound_lefttime
                        
                            # Check if current time is less than the from time
                            # In case of timeto < timefrom an early login will be considered as a late login
                            if timeto > timefrom:
                                if nowdatetime < timefrom:
                                    timebeforelogut = 0
                                    logoutreason = 2

                    if timebeforelogut is not None:
                        timers[username] = thread_it(timebeforelogut,log_it_out,username,logoutreason)
                        logouttime[username] = int(timenow()) + timebeforelogut

            # Parse gone users    
            for username in goneusers:
                try:
                    timers[username].cancel()
                    logouttime.pop(username)
                    logkpr('User: %s is gone from the system, logout action canceled' %username)
                except KeyError:
                    logkpr('User: %s is gone from the system, but no logout action was running' %username)
        
        # If users == usr none has login or logout
        else:
            stillusers = users
        
        users = usr
        
        for username in stillusers:
            timefile = VAR['TIMEKPRWORK'] + '/' + username + '.time'
            #TODO:Add but not get
            time = add_time(timefile, username)
            logkpr('User: %s Seconds-passed: %s' % (username, time))
                
        # Done checking all users, sleeping
        logkpr('Finished checking all users, sleeping for %s seconds' % VAR['POLLTIME'])
        sleep(VAR['POLLTIME'])

