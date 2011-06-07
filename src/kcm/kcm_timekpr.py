#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# KDE KCModule for configuring timekpr
#
# Copyright (c) 2008, 2010 Timekpr Authors.
# This file is licensed under the General Public License version 3 or later.
# See the COPYRIGHT file for full details. You should have received the COPYRIGHT file along with the program

from os import remove, mkdir, geteuid, getenv
from os.path import isdir, isfile, realpath, dirname, dirname
import sys

from PyQt4.QtGui import *
from PyQt4 import uic, QtCore
from PyQt4.QtCore import *
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *

#If DEVACTIVE is true, it uses files from local directory
DEVACTIVE = False

#IMPORT
if DEVACTIVE:
    from sys import path
    path.append('.')
from timekprpam import *
from timekprcommon import *


#timekpr.conf variables (dictionary variable)
global VAR
VAR = getvariables(DEVACTIVE)    
version = getversion()


#Enum
unlock, lock = range(2)
nobound, bound, noboundtoday = range(3)
nolimit, limit, nolimittoday = range(3)
noreset, reset = range(2)


def sec_to_hr_mn(sec):
    inminutes = int(sec) / 60
    hr, mn = divmod(inminutes , 60)
    return hr, mn
        
def isnormal(username, userid):
#Check if it is a regular user, with userid within UID_MIN and UID_MAX.    
#TODO:Move to timekprcommon?
#FIXME: Hide active user - bug #286529
#SUDO_USER contains the username of the sudo user that launched timekpr
#So this function return yes for all the non-system user and false for the system-user and for the user that launched timekp
    if (getenv('SUDO_USER') and username == getenv('SUDO_USER')):
	return False
    
    #Check if it is in the non-system users range
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





class Timekpr (KCModule):
    def __init__(self, component_data, parent):
        KCModule.__init__(self,component_data, parent)
        
        #Set AboutData
        self.aboutdata = self.MakeAboutData()
        self.setAboutData(self.aboutdata)
        
        
        #Interface initialization
	
	#print basename(sys.argv[0])
        #Loading the UI module        print get_path()
        self.ui = uic.loadUi(unicode(dirname(__file__) + "/ui/main.ui"))
        self.ui.status = uic.loadUi(unicode(dirname(__file__) + "/ui/status.ui"))
        self.ui.grant = uic.loadUi(unicode(dirname(__file__) + "/ui/grant.ui"))
        self.ui.limits = uic.loadUi(unicode(dirname(__file__) + "/ui/limits.ui"))
        
        
        
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
        
        #Set the format of the week
        self.set_week_format()
        
        #Initializing the user combobox
        self.loadUser() 

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
        
	
	#Signal and slots definition 
        self.connect(self.ui.limits.ckLimit, SIGNAL('toggled(bool)'), self.enable_limit)
        self.connect(self.ui.limits.ckBound, SIGNAL('toggled(bool)'), self.enable_bound)        
        self.connect(self.ui.limits.ckLimitDay, SIGNAL('toggled(bool)'), self.toggle_daily_limit)
        self.connect(self.ui.limits.ckBoundDay, SIGNAL('toggled(bool)'), self.toggle_daily_bound)
        self.connect(self.ui.cbActiveUser, SIGNAL('currentIndexChanged(int)'), self.read_settings)
        self.connect(self.timer, SIGNAL('timeout()'), self.update_time_left)
        self.connect(self.ui.grant.btnLockAccount,SIGNAL('clicked()'),self.lockunlock)
        self.connect(self.ui.grant.btnBoundBypass,SIGNAL('clicked()'),self.bypassTimeFrame)
        self.connect(self.ui.grant.btnLimitBypass,SIGNAL('clicked()'),self.bypassAccessDuration)
        self.connect(self.ui.grant.btnResetTime,SIGNAL('clicked()'),self.resetTime)
        self.connect(self.ui.grant.btnAddTime,SIGNAL('clicked()'),self.addTime)
        self.connect(self.ui.grant.btnClearAllRestriction,SIGNAL('clicked()'),self.clearallrestriction)
        self.connect(self.ui.limits.ckLimit, SIGNAL('toggled(bool)'), self.changed)
        self.connect(self.ui.limits.ckBound, SIGNAL('toggled(bool)'), self.changed)        
        self.connect(self.ui.limits.ckLimitDay, SIGNAL('toggled(bool)'), self.changed)
        self.connect(self.ui.limits.ckBoundDay, SIGNAL('toggled(bool)'), self.changed)
        
        for i in range(2):
	    for j in range(7):
		self.connect(self.limitSpin[i][j],SIGNAL('valueChanged(int)'),self.changed)
		self.connect(self.fromSpin[i][j],SIGNAL('valueChanged(int)'),self.changed)
		self.connect(self.toSpin[i][j],SIGNAL('valueChanged(int)'),self.changed)		
		
        #TODO:Delete me, just for testing
        #self.connect(self.ui.grant.btnLockAccount,SIGNAL('clicked()'),self.changed)
        
	#Ensure we have at least one available normal user otherwise we disable all the modules
	if self.ui.cbActiveUser.count() == 0:
	    self.ui.gbStatus.setEnabled(False)
	    self.ui.gbGrant.setEnabled(False)
	    self.ui.gbLimitBound.setEnabled(False)
	    
	#Needed for using KAuth authentication
        self.setNeedsAuthorization(True)
   
#Function definition
    def MakeAboutData(self):
	aboutdata = KAboutData("kcmtimekpr", "userconfig", ki18n("Timekpr control module"), "0.4",
	    ki18n("User and Group Configuration Tool"),
	    KAboutData.License_GPL,
	    ki18n("Copyright (c) 2008, 2010 Timekpr Authors"))
	aboutdata.addAuthor(ki18n("Simone Gaiarin"), ki18n("Developer"), "simgunz@gmail.com", "")
	aboutdata.addAuthor(ki18n("Even Nedberg"), ki18n("Developer"), "even@nedberg.net", "")
	aboutdata.addAuthor(ki18n("Savvas Radevic"), ki18n("Developer"), "vicedar@gmail.com", "")
	aboutdata.addAuthor(ki18n("Nicolas Laurance"), ki18n("Developer"), "nlaurance@zindep.com", "")
	aboutdata.addAuthor(ki18n("Charles Jackson"), ki18n("Lead tester"), "crjackson@carolina.rr.com", "")
	
	return aboutdata
	
	
    def set_week_format(self):
	locale = KGlobal.locale()
        startday = locale.weekStartDay()
	if startday == 7:
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
    
    
    def loadUser(self):
        passwd = open('/etc/passwd','r').read()
        userinfodb = re.compile('^.+$', re.M).findall(passwd)        
    
        for entry in userinfodb:
            userinfo = re.split(':',entry)
            if isnormal(userinfo[0],int(userinfo[2])):
		self.ui.cbActiveUser.addItem(userinfo[0])               
        self.ui.cbActiveUser.setCurrentIndex(2)
        #TODO:Set index to 0 (just for testing)
    
    
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
    
    
    #TODO:Use plasmadataengine if possible to save file access
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
          
          
    def statusicons(self):
	if not isuserlimitedtoday(self.user) and not self.status['lock']:
	    self.ui.status.lbAllDayLoginStatus.setText("Yes")
	else:
	    self.ui.status.lbAllDayLoginStatus.setText("No")
	
	if self.status['lock']:
	    self.ui.status.lbLockStatus.setText("Yes")
	else:
	    self.ui.status.lbLockStatus.setText("No")
	    
	if self.status['bound'] == bound:
	    self.ui.status.lbBoundStatus.setText("Yes")
	elif self.status['bound'] == nobound:
	    self.ui.status.lbBoundStatus.setText("No")
	else:
	    self.ui.status.lbBoundStatus.setText("No (just for today)")
	    
	if self.status['limit'] == limit:
	    self.ui.status.lbLimitStatus.setText("Yes")
	elif self.status['limit'] == nolimit:
	    self.ui.status.lbLimitStatus.setText("No")
	else:
	    self.ui.status.lbLimitStatus.setText("No (just for today)")
	
	self.update_time_left()


    def buttonstates(self):
	if self.status['lock']:
	    self.ui.grant.btnLockAccount.setText("Unlock account")
	else:
	    self.ui.grant.btnLockAccount.setText("Lock account")
	    
	self.ui.grant.btnBoundBypass.setText("Bypass time frame for today")
	if self.status['bound']:
	    if self.status['bound']==1:
		index = int(strftime("%w"))
		wfrom = self.fromtolimits[0]
		wto = self.fromtolimits[1]
		if wfrom[index] != '0' or wto[index] != '24':
		    self.ui.grant.btnBoundBypass.setEnabled(True)
		else:
		    self.ui.grant.btnBoundBypass.setEnabled(False)
	    else:
		self.ui.grant.btnBoundBypass.setText("Clear bypass time frame for today")
		self.ui.grant.btnBoundBypass.setEnabled(True)
	else:
	    self.ui.grant.btnBoundBypass.setEnabled(False)
	 
	self.ui.grant.btnLimitBypass.setText("Bypass access duration for today") 
	if self.status['limit'] == limit:
	    timefile = VAR['TIMEKPRWORK'] + '/' + self.user + '.time'
            #if isfile(timefile):
            if self.status['reset']==noreset:
		self.ui.grant.btnResetTime.setEnabled(True)
	    else:
		self.ui.grant.btnResetTime.setEnabled(False)
	    #Reward button should add time even if .time is not there?
	    self.ui.grant.btnLimitBypass.setEnabled(True)
	    self.ui.grant.btnAddTime.setEnabled(True)
	    self.ui.grant.sbAddTime.setEnabled(True)
	    self.ui.grant.lbAddTime.setEnabled(True)
	else:
	    self.ui.grant.btnResetTime.setEnabled(False)
	    self.ui.grant.btnAddTime.setEnabled(False)
	    self.ui.grant.sbAddTime.setEnabled(False)
	    self.ui.grant.lbAddTime.setEnabled(False)
	    if self.status['limit'] == nolimit:
		self.ui.grant.btnLimitBypass.setEnabled(False)
	    else:
		self.ui.grant.btnLimitBypass.setText("Clear bypass access duration for today")
		self.ui.grant.btnLimitBypass.setEnabled(True)
	
	if ((self.status['lock'] == lock) or (self.status['bound'] == bound) or (self.status['limit'] == limit)):
	    self.ui.grant.btnClearAllRestriction.setEnabled(True)
	else:
	    self.ui.grant.btnClearAllRestriction.setEnabled(False)
	
	
    #def indexchanged(self):
    #KMessageBox.questionYesNo(this,i18n("<qt>You changed the default component of your choice, do want to save that change now ?</qt>"),QString(),KStandardGuiItem::save(),KStandardGuiItem::discard())==KMessageBox::Yes)
    
    
    def read_settings(self):
	self.user = str(self.ui.cbActiveUser.currentText())
	uislocked = isuserlocked(self.user)
	self.status = {'lock':uislocked,'reset':noreset}
	self.readfromtolimit()
	self.readdurationlimit()
	self.statusicons()
	self.buttonstates()
	self.emit(SIGNAL("changed(bool)"), False)


    def readfromtolimit(self):
	#TODO:Move to timekprcommon?
	#TODO: Why not using a cache file for keeping all the limits even if the checkboxes are unchecked?
        #from-to time limitation (aka boundaries) - time.conf
        #Get user time limits (boundaries) as lists from-to
        self.fromtolimits = getuserlimits(self.user)
        bfrom = self.fromtolimits[0]
        bto = self.fromtolimits[1]
        
        self.status['bound'] = isuserlimited(self.user)
        
        if self.status['bound']:
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
        
        self.status['limit'] = isfile(configFile)
        if self.status['limit']:
            fileHandle = open(configFile)
            self.limits = fileHandle.readline()
            self.limits = self.limits.replace("limit=( ", "")
            self.limits = self.limits.replace(")", "")
            self.limits = self.limits.split(" ")
            #WARNING:The file with the limits must not have a \n at the end
            
            self.ui.limits.ckLimit.setChecked(True)
	    
            #Are all boundaries the same?
            #If they're not same, activate single (per day) limits
            
            sl = False
            for i in range(1, 7):
                if self.limits[i] != self.limits[i-1]:
                    sl = True
                    qDebug(self.limits[i] + " " + self.limits[i-1])
                    
            if sl:
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
     	
	
    def executePermissionsAction(self,args):
	action = KAuth.Action("org.kde.kcontrol.kcmtimekpr.managepermissions")
	action.setHelperID("org.kde.kcontrol.kcmtimekpr")
	args['var'] = VAR
	args['user'] = self.user
	action.setArguments(args)
	reply = action.execute()
	return reply
    
    
    def clearallrestriction(self):
	answer = KMessageBox.warningContinueCancel(self,i18n("All restriction for user " + self.user + " will be cleared"),i18n("Timekpr"))
	if not answer == KMessageBox.Continue:
	    return
	args = {'subaction':0}
	reply = self.executePermissionsAction(args)
	if not reply.failed():
	    self.status['lock'] = unlock
	    self.status['bound'] = nobound
	    self.status['limit'] = nolimit
	    self.buttonstates()
	    self.statusicons()
	    self.read_settings()
	    
    def lockunlock(self):
	args = {'subaction':1}
	if self.status['lock'] == lock:
	    args['operation'] = unlock
	else:
	    args['operation'] = lock
	reply = self.executePermissionsAction(args)
	if not reply.failed():
	    self.status['lock'] = not self.status['lock']
	    self.buttonstates()
	    self.statusicons()
	
	
    def bypassTimeFrame(self):
	args = {'subaction':2}
	if self.status['bound'] == nobound or self.status['bound'] == noboundtoday:
	    args['operation'] = bound
	else:
	    args['operation'] = noboundtoday
	reply = self.executePermissionsAction(args)
	if not reply.failed():
	    if (args['operation'] == noboundtoday):
		self.status['bound'] = noboundtoday
	    else:
		self.status['bound'] = bound
	    self.buttonstates()
	    self.statusicons()


    def bypassAccessDuration(self):
	args = {'subaction':3}
	if self.status['limit'] == nolimit or self.status['limit'] == nolimittoday:
	    args['operation'] = limit
	else:
	    args['operation'] = nolimittoday
	reply = self.executePermissionsAction(args)
	if not reply.failed():
	    if (args['operation'] == nolimittoday):
		self.status['limit'] = nolimittoday
	    else:
		self.status['limit'] = limit
	    self.buttonstates()
	    self.statusicons()
	
	
    def resetTime(self):
	args = {'subaction':4}
	reply = self.executePermissionsAction(args)
	if not reply.failed():
	    self.status['reset'] = reset
	    self.buttonstates()
	    self.statusicons()


    def addTime(self):
	args = {'subaction':5}
	time = self.ui.grant.sbAddTime.value()
	if time:
	    args['time'] = time
	    reply = self.executePermissionsAction(args)
	    if not reply.failed():
		self.ui.grant.sbAddTime.setValue(0)
		self.status['reset'] = noreset
		self.buttonstates()
		self.statusicons()
	
	
    def changed(self):
	#TODO:This function should be removed, it's just for testing
        #If a setting has changed, activate the Apply button
        self.emit(SIGNAL("changed(bool)"), True)


    def defaults(self):
	#TODO:This function is called from defaults button, should set defaults value
	print "Defaults called"	


    def load(self):
	#This function is called from reset button and automatically during construction
	self.read_settings()
	#FIXME:When the module is loaded from kcmshell the Apply button is enabled, should be disabled
	
	
    def save(self):
	space = " "
        limit = "limit=( 86400 86400 86400 86400 86400 86400 86400 )"
        #timekprpam.py adduserlimits() uses lists with numbers as strings
        bFrom = ['0'] * 7
        bTo = ['24'] * 7

	limit = "limit=("
        
        if self.ui.limits.ckLimit.isChecked():
            if self.ui.limits.ckLimitDay.isChecked():
                for i in range(7):
                    limit = limit + space + str(self.limitSpin[0][i].value() * 3600 + self.limitSpin[1][i].value() * 60)
            else:
                for i in range(7):
		    limit = limit + space + str(self.limitSpin[0][0].value() * 3600 + self.limitSpin[1][0].value() * 60)                
        
        limit = limit + space + ")"
                
        bFrom = [['0'] * 7,['0'] * 7]
        bTo = [['24'] * 7,['0'] * 7]
        
        if self.ui.limits.ckBound.isChecked():
	    bFrom = [[],[]]
            bTo = [[],[]]
	    if self.ui.limits.ckBoundDay.isChecked():
                for i in range(2):
		    for j in range(7):
			bFrom[i].append(str(self.fromSpin[i][j].value()))
			bTo[i].append(str(self.toSpin[i][j].value()))
            else:
		for i in range(2):
		    for j in range(7):
			bFrom[i].append(str(self.fromSpin[i][0].value()))
			bTo[i].append(str(self.toSpin[i][0].value()))
	
	bound = mktimeconfline(self.user, bFrom[0], bTo[0]) + "\n"
	helperargs = {"user":self.user,"bound":bound,"limit":limit}
	action = self.authAction()
	action.setArguments(helperargs)
	#getconfsection(f)
	reply = action.execute()
	#content = reply.data()
	#print content
	#print content["first"]
	#print "\n"
	#print content["second"]
	if reply.failed():
	    print "Failed"
	else:
	    print "Success"
	
	self.read_settings()
	self.update_time_left()
 

    
def CreatePlugin(widget_parent, parent, component_data):
    #Create configuration folder if not existing
    if not isdir(VAR['TIMEKPRDIR']):
        mkdir(VAR['TIMEKPRDIR'])
    if not isdir(VAR['TIMEKPRWORK']):
        mkdir(VAR['TIMEKPRWORK'])
    #if not isdir(VAR['TIMEKPRSHARED']):  
    #    exit('Error: Could not find the shared directory %s' % VAR['TIMEKPRSHARED']	
    return Timekpr(component_data, widget_parent)