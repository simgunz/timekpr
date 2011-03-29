#!/usr/bin/python
import dbus
from os import setuid
from subprocess import call

setuid(1000)
try:
    
    screenSaver = dbus.SessionBus().get_object('org.freedesktop.ScreenSaver','/ScreenSaver')
    active = screenSaver.GetActive()
except:
    exit(0)
else:
    exit(active)
