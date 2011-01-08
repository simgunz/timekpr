#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# KDE KCModule for configuring timekpr
#
# Copyright (c) 2008, 2010 Timekpr Authors.
# This file is licensed under the General Public License version 3 or later.
# See the COPYRIGHT file for full details. You should have received the COPYRIGHT file along with the program

from os import remove, mkdir, geteuid, getenv
from os.path import isdir, isfile, realpath, dirname
from pwd import getpwnam
from spwd import getspall
from spwd import getspnam#CANCELLAMI

from PyQt4.QtGui import *
from PyQt4 import uic, QtCore
from PyQt4.QtCore import *
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *

#If DEVACTIVE is true, it uses files from local directory
DEVACTIVE = True

#IMPORT
if DEVACTIVE:
    from sys import path
    path.append('.')
from timekprpam_kde import *
from timekprcommon_kde import *


#timekpr.conf variables (dictionary variable)
global VAR
VAR = getvariables(DEVACTIVE)    
version = getversion()






def sec_to_hr_mn(sec):
    inminutes = int(sec) / 60
    hr, mn = divmod(inminutes , 60)
    return hr, mn
    
    
def isnormal(username):
#Check if it is a regular user, with userid within UID_MIN and UID_MAX.    
#TODO:Move to timekprcommon?
#FIXME: Hide active user - bug #286529
#SUDO_USER contains the username of the sudo user that launched timekpr
#So this function return yes for all the non-system user and false for the system-user and for the user that launched timekp
    if (getenv('SUDO_USER') and username == getenv('SUDO_USER')):
	return False
    
    #Return the user uid and check if it is in the non-system users range
    userid = int(getpwnam(username)[2])
    logindefs = open('/etc/login.defs')
    uidminmax = re.compile('^UID_(?:MIN|MAX)\s+(\d+)', re.M).findall(logindefs.read())
    if uidminmax[0] < uidminmax[1]:
	uidmin = int(uidminmax[0])
	uidmax = int(uidminmax[1])
    else:
	uidmin = int(uidminmax[1])
	uidmax = int(uidminmax[0])
	
    if uidmin <= userid <= uidmax:
	return True
    else:
	return False





class TimekprKDE (KCModule):
    def __init__(self, component_data, parent):
        KCModule.__init__(self,component_data, parent)
        
        #Interface initialization
        
        #Loading the UI module
        self.ui = uic.loadUi(unicode("/usr/share/kde4/apps/timekpr-kde/ui/main.ui"))
        self.ui.status = uic.loadUi(unicode("/usr/share/kde4/apps/timekpr-kde/ui/status.ui"))
        self.ui.grant = uic.loadUi(unicode("/usr/share/kde4/apps/timekpr-kde/ui/grant.ui"))
        self.ui.limits = uic.loadUi(unicode("/usr/share/kde4/apps/timekpr-kde/ui/limits.ui"))
        
        #Create the layout using group box 
        #Since the UI is modular it's possible to change this layout for displaying the UI modules in tab, etc
        self.ui.lyStatus = QVBoxLayout(self.ui.gbStatus)
        self.ui.lyStatus.addWidget(self.ui.status)
        self.ui.lyGrant = QVBoxLayout(self.ui.gbGrant)
        self.ui.lyGrant.addWidget(self.ui.grant)
        self.ui.lyLimitBound = QVBoxLayout(self.ui.gbLimitBound)
        self.ui.lyLimitBound.addWidget(self.ui.limits)            
        self.lyMainLayout = QVBoxLayout(self)
        self.lyMainLayout.addWidget(self.ui)
        
        #Disable the limits by default
        self.ui.limits.wgLimitConfDay.setEnabled(False)
	self.ui.limits.wgBoundConfDay.setEnabled(False)
        
        #Set the format of the week (US or EU)
        self.locale = 'eu'
        self.set_locale()
        
        #Set buttons
        #self.setButtons(KCModule.Apply)
        #self.changed.emit(True)
	
        #Initializing the user combobox
        #Using /etc/shadow spwd module
        #getspall acquire a 8 element struct from all the user in the system, the first element is the username
        for userinfo in getspall():
            if isnormal(userinfo[0]):
                self.ui.cbActiveUser.addItem(userinfo[0])               
        self.ui.cbActiveUser.setCurrentIndex(0)  


        #Initializing an empty list for time limits
        self.limits = []

        ##Timer initializing
        self.timer = QTimer()
        self.timer.setInterval(10000)
        self.timer.start()
        
        #Copying the spinboxes to a list for faster access
        self.get_limit_spin()
        self.get_from_spin()
        self.get_to_spin()
        
        #Needed for using KAuth authentication
        #self.setNeedsAuthorization(True)
        #self.setUseRootOnlyMessage(True)
	
	#Signal and slots definition 
        self.connect(self.ui.limits.ckLimit, SIGNAL('toggled(bool)'), self.enable_limit)
        self.connect(self.ui.limits.ckBound, SIGNAL('toggled(bool)'), self.enable_bound)        
        self.connect(self.ui.limits.ckLimitDay, SIGNAL('toggled(bool)'), self.toggle_daily_limit)
        self.connect(self.ui.limits.ckBoundDay, SIGNAL('toggled(bool)'), self.toggle_daily_bound)
        self.connect(self.ui.cbActiveUser, SIGNAL('currentIndexChanged(int)'), self.read_settings)
        self.connect(self.timer, SIGNAL('timeout()'), self.update_time_left)
        
	#Ensure we have at least one available normal user otherwise we disable all the modules
	if self.ui.cbActiveUser.count() == 0:
	    self.ui.gbStatus.setEnabled(False)
	    self.ui.gbGrant.setEnabled(False)
	    self.ui.gbLimitBound.setEnabled(False)
	else:
	    #Read settings from file in /etc/timekpr and from /etc/security/time.conf
	    self.read_settings()
   
#Function definition

    def defaults(self):
	#TODO:This function should be called from reset insted of defaults
	self.read_settings()
  
  
    def save(self):
	#TODO:To implement and connect to Apply button
	print "Saved"
	
	
    def set_locale(self):
	#TODO:Need to find a way to get the kde locale	
	if self.locale == 'us':
	    self.ui.limits.vLineLimit = self.ui.limits.vLine_0
	    self.ui.limits.vLineBound = self.ui.limits.vLine_7
	    self.ui.limits.vLine_6.hide()
	    self.ui.limits.vLine_13.hide()
	else:
	    everydayLimit = self.ui.limits.lyLimitConfDay.takeAt(3)
	    everydayBound = self.ui.limits.lyBoundConfDay.takeAt(3)
	    self.ui.limits.lyLimitConfDay.addItem(everydayLimit)
	    self.ui.limits.lyBoundConfDay.addItem(everydayBound)
	    self.ui.limits.vLineLimit = self.ui.limits.vLine_6
	    self.ui.limits.vLineBound = self.ui.limits.vLine_13
	    self.ui.limits.vLine_0.hide()
	    self.ui.limits.vLine_7.hide()
	
	self.toggle_daily_limit(self.ui.limits.ckLimitDay.isChecked())
	self.toggle_daily_bound(self.ui.limits.ckBoundDay.isChecked())
    
    
    def enable_limit(self,checked):
        if checked:
            self.ui.limits.wgLimitConfDay.setEnabled(True)
        else:
            self.ui.limits.wgLimitConfDay.setEnabled(False)
            
            
    def enable_bound(self,checked):
	if checked:
            self.ui.limits.wgBoundConfDay.setEnabled(True)
        else:
            self.ui.limits.wgBoundConfDay.setEnabled(False)
            
            
    def toggle_daily_limit(self,checked):
        if checked:
	    self.ui.limits.lbLimit_0.setText("Sunday")
            self.ui.limits.wgLimitWeek.show()
            self.ui.limits.vLineLimit.show()
        else:
	    self.ui.limits.lbLimit_0.setText("Every day")
            self.ui.limits.wgLimitWeek.hide()
            self.ui.limits.vLineLimit.hide()
                
                
    def toggle_daily_bound(self,checked):
        if checked:
            self.ui.limits.lbBound_0.setText("Sunday")
            self.ui.limits.wgBoundWeek.show()
            self.ui.limits.vLineBound.show()
        else:
            self.ui.limits.wgBoundWeek.hide()
            self.ui.limits.lbBound_0.setText("Every day")
            self.ui.limits.vLineBound.hide()
        
        
    def get_limit_spin(self):
        self.limitSpin = [list(),list()]
        self.limitSpin[0].append(self.ui.limits.sbLimitHr_0)
        self.limitSpin[0].append(self.ui.limits.sbLimitHr_1)
        self.limitSpin[0].append(self.ui.limits.sbLimitHr_2)
        self.limitSpin[0].append(self.ui.limits.sbLimitHr_3)
        self.limitSpin[0].append(self.ui.limits.sbLimitHr_4)
        self.limitSpin[0].append(self.ui.limits.sbLimitHr_5)
        self.limitSpin[0].append(self.ui.limits.sbLimitHr_6)
        self.limitSpin[1].append(self.ui.limits.sbLimitMn_0)
        self.limitSpin[1].append(self.ui.limits.sbLimitMn_1)
        self.limitSpin[1].append(self.ui.limits.sbLimitMn_2)
        self.limitSpin[1].append(self.ui.limits.sbLimitMn_3)
        self.limitSpin[1].append(self.ui.limits.sbLimitMn_4)
        self.limitSpin[1].append(self.ui.limits.sbLimitMn_5)
        self.limitSpin[1].append(self.ui.limits.sbLimitMn_6)
	    
	    
    def get_from_spin(self):
        self.fromSpin = [list(),list()]
        self.fromSpin[0].append(self.ui.limits.sbFromHr_0)
        self.fromSpin[0].append(self.ui.limits.sbFromHr_1)
        self.fromSpin[0].append(self.ui.limits.sbFromHr_2)
        self.fromSpin[0].append(self.ui.limits.sbFromHr_3)
        self.fromSpin[0].append(self.ui.limits.sbFromHr_4)
        self.fromSpin[0].append(self.ui.limits.sbFromHr_5)
        self.fromSpin[0].append(self.ui.limits.sbFromHr_6)
        self.fromSpin[1].append(self.ui.limits.sbFromMn_0)
        self.fromSpin[1].append(self.ui.limits.sbFromMn_1)
        self.fromSpin[1].append(self.ui.limits.sbFromMn_2)
        self.fromSpin[1].append(self.ui.limits.sbFromMn_3)
        self.fromSpin[1].append(self.ui.limits.sbFromMn_4)
        self.fromSpin[1].append(self.ui.limits.sbFromMn_5)
        self.fromSpin[1].append(self.ui.limits.sbFromMn_6)
        
        
    def get_to_spin(self):
        self.toSpin = [list(),list()]
        self.toSpin[0].append(self.ui.limits.sbToHr_0)
        self.toSpin[0].append(self.ui.limits.sbToHr_1)
        self.toSpin[0].append(self.ui.limits.sbToHr_2)
        self.toSpin[0].append(self.ui.limits.sbToHr_3)
        self.toSpin[0].append(self.ui.limits.sbToHr_4)
        self.toSpin[0].append(self.ui.limits.sbToHr_5)
        self.toSpin[0].append(self.ui.limits.sbToHr_6)
        self.toSpin[1].append(self.ui.limits.sbToMn_0)
        self.toSpin[1].append(self.ui.limits.sbToMn_1)
        self.toSpin[1].append(self.ui.limits.sbToMn_2)
        self.toSpin[1].append(self.ui.limits.sbToMn_3)
        self.toSpin[1].append(self.ui.limits.sbToMn_4)
        self.toSpin[1].append(self.ui.limits.sbToMn_5)
        self.toSpin[1].append(self.ui.limits.sbToMn_6)
    
    
    def readfromtolimit(self):
	#TODO:Move to timekprcommon?
	#TODO: Why not using a cache file for keeping all the limits even if the checkboxes are unchecked?
        #from-to time limitation (aka boundaries) - time.conf
        #Get user time limits (boundaries) as lists from-to
        bfrom = self.fromtolimits[0]
        bto = self.fromtolimits[1]
        
        if isuserlimited(self.user):
	    self.ui.limits.ckBound.setChecked(True)
                       
	    if [bfrom[0]] * 7 != bfrom or [bto[0]] * 7 != bto:
		self.ui.limits.ckBoundDay.setChecked(True)
	    else:
		self.ui.limits.ckBoundDay.setChecked(False)
		
            for i in range(7):
                self.fromSpin[0][i].setValue(int(bfrom[i]))
                self.toSpin[0][i].setValue(int(bto[i]))
        else:
	    self.ui.limits.ckBound.setChecked(False)
	    self.ui.limits.ckBoundDay.setChecked(False)
	    for i in range(7):
                self.fromSpin[0][i].setValue(7)
                self.toSpin[0][i].setValue(22)


    def readdurationlimit(self):
        #time length limitation
        configFile = VAR['TIMEKPRDIR'] + '/' + str(self.user)
        del self.limits[:]
        
        if isfile(configFile):
            fileHandle = open(configFile)
            self.limits = fileHandle.readline()
            self.limits = self.limits.replace("limit=( ", "")
            self.limits = self.limits.replace(" )", "")
            self.limits = self.limits.split(" ")
            #WARNING:The file with the limits must not have a \n at the end
            
            self.ui.limits.ckLimit.setChecked(True)
	    
            #Are all boundaries the same?
            #If they're not same, activate single (per day) limits
            if [self.limits[0]] * 7 != self.limits:
                self.ui.limits.ckLimitDay.setChecked(True)
            else:
		self.ui.limits.ckLimitDay.setChecked(False)
	    	    
            for i in range(7):
		hours, minutes = sec_to_hr_mn(self.limits[i])
                self.limitSpin[0][i].setValue(hours)
                self.limitSpin[1][i].setValue(minutes)
              
        else:
	    self.ui.limits.ckLimit.setChecked(False)
	    self.ui.limits.ckLimitDay.setChecked(False)
	    for i in range(7):
                self.limitSpin[0][i].setValue(3)
                self.limitSpin[1][i].setValue(0)
     	
	
    def update_time_left(self):       
        dayIndex = int(strftime("%w"))
        try:
            limit = int(self.limits[dayIndex])
        except IndexError:
            limit = 86400

        timefile = VAR['TIMEKPRWORK'] + '/' + self.user + '.time'
        used = 0
        if isfile(timefile) and fromtoday(timefile):
            t = open(timefile)
            used = int(t.readline())
            t.close()
        left = limit - used
        hours, minutes = sec_to_hr_mn(left)
        self.ui.status.lbTimeLeftStatus.setText(str(hours) + " hours " + str(minutes) + " min")     
          
          
    def statusicons(self, uislocked):
	if not isuserlimitedtoday(self.user) and not uislocked:
	    self.ui.status.lbAllDayLoginStatus.setText("Yes")
	else:
	    self.ui.status.lbAllDayLoginStatus.setText("No")
	
	if self.ui.limits.ckBound.isChecked():
	    self.ui.status.lbBoundStatus.setText("Yes")
	else:
	    self.ui.status.lbBoundStatus.setText("No")
	    
	if self.ui.limits.ckLimit.isChecked():
	    self.ui.status.lbLimitStatus.setText("Yes")
	else:
	    self.ui.status.lbLimitStatus.setText("No")
	
	if uislocked:
	    self.ui.status.lbLockStatus.setText("Yes")
	else:
	    self.ui.status.lbLockStatus.setText("No")
	
	self.update_time_left()


    def buttonstates(self, uislocked):
	if uislocked:
	    self.ui.grant.btnLockAccount.setText("Unlock account")
	else:
	    self.ui.grant.btnLockAccount.setText("Lock account")
	
	if self.ui.limits.ckLimit.isChecked():
	    timefile = VAR['TIMEKPRWORK'] + '/' + self.user + '.time'
            if isfile(timefile):
		self.ui.grant.btnResetTime.setEnabled(True)
	    else:
		self.ui.grant.btnResetTime.setEnabled(False)
	    #Reward button should add time even if .time is not there?
	    self.ui.grant.btnLimitBypass.setEnabled(True)
	    self.ui.grant.btnAddTime.setEnabled(True)
	    self.ui.grant.sbAddTime.setEnabled(True)
	    self.ui.grant.lbAddTime.setEnabled(True)
	else:
	    self.ui.grant.btnLimitBypass.setEnabled(False)
	    self.ui.grant.btnResetTime.setEnabled(False)
	    self.ui.grant.btnAddTime.setEnabled(False)
	    self.ui.grant.sbAddTime.setEnabled(False)
	    self.ui.grant.lbAddTime.setEnabled(False)
	    
	if self.ui.limits.ckBound.isChecked():
	    index = int(strftime("%w"))
            wfrom = self.fromtolimits[0]
            wto = self.fromtolimits[1]
            if wfrom[index] != '0' or wto[index] != '24':
		self.ui.grant.btnBoundBypass.setEnabled(True)
	    else:
		self.ui.grant.btnBoundBypass.setEnabled(False)
	else:
	    self.ui.grant.btnBoundBypass.setEnabled(False)

    def read_settings(self):
	self.user = str(self.ui.cbActiveUser.currentText())
	uislocked = isuserlocked(self.user)
	self.fromtolimits = getuserlimits(self.user)
	self.readfromtolimit()
	self.readdurationlimit()
	self.statusicons(uislocked)
	self.buttonstates(uislocked)




def CreatePlugin(widget_parent, parent, component_data):
    #Create configuration folder if not existing
    if not isdir(VAR['TIMEKPRDIR']):
        mkdir(VAR['TIMEKPRDIR'])
    if not isdir(VAR['TIMEKPRWORK']):
        mkdir(VAR['TIMEKPRWORK'])
    #if not isdir(VAR['TIMEKPRSHARED']):  
    #    exit('Error: Could not find the shared directory %s' % VAR['TIMEKPRSHARED']
	
    return TimekprKDE(component_data, widget_parent)