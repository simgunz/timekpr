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
import json

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
VAR = get_variables(DEVACTIVE)    
version = get_version()


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
        self.ui.lyStatus.addWidget(self.ui.status)
        self.ui.lyGrant = QVBoxLayout(self.ui.tbGrant)
        self.ui.lyGrant.addWidget(self.ui.grant)
        self.ui.lyLimitBound = QVBoxLayout(self.ui.tbLimitBound)
        self.ui.lyLimitBound.addWidget(self.ui.limits)            
        #self.ui.lyLimitBound.insertStretch(-1)
        self.lyMainLayout = QVBoxLayout(self)
        self.lyMainLayout.addWidget(self.ui)
        #self.lyMainLayout.insertStretch(-1)
        
        #Disable the limits by default
        self.ui.limits.wgLimitConf.setEnabled(False)
	self.ui.limits.wgBoundConf.setEnabled(False)
	#self.ui.limits.wgLabels.setEnabled(False)
        
        #Initializing the user combobox
        self.loadUser() 

        #Initializing an empty list for time limits
        self.limits = []
        self.status = dict()
        
        #Set the format of the week
        self.set_week_format()

        ##Timer initializing
        self.timer = QTimer()
        self.timer.setInterval(10000)
        self.timer.start()
        
        #Copying the spinboxes to a list for faster access
	self.get_spin()
	
	#KConfig
	self.config = self.createTempConfig()
	
	#Signal and slots definition 
        self.connect(self.ui.limits.ckLimit, SIGNAL('toggled(bool)'), self.enable_limit)
        self.connect(self.ui.limits.ckBound, SIGNAL('toggled(bool)'), self.enable_bound)        
        self.connect(self.ui.limits.ckLimitDay, SIGNAL('toggled(bool)'), self.toggle_daily_limit)
        self.connect(self.ui.limits.ckBoundDay, SIGNAL('toggled(bool)'), self.toggle_daily_bound)
        self.connect(self.ui.cbActiveUser, SIGNAL('currentIndexChanged(int)'), self.read_settings)
        self.connect(self.timer, SIGNAL('timeout()'), self.update_time_left)
        self.connect(self.ui.grant.btnLockAccount,SIGNAL('clicked()'),self.lockunlock)
        self.connect(self.ui.grant.btnUnlockAccount,SIGNAL('clicked()'),self.lockunlock)
        self.connect(self.ui.grant.btnBoundBypass,SIGNAL('clicked()'),self.bypass_time_frame)
        self.connect(self.ui.grant.btnClearBoundBypass,SIGNAL('clicked()'),self.bypass_time_frame)
        self.connect(self.ui.grant.btnLimitBypass,SIGNAL('clicked()'),self.bypassAccessDuration)
        self.connect(self.ui.grant.btnClearLimitBypass,SIGNAL('clicked()'),self.bypassAccessDuration)
        self.connect(self.ui.grant.btnResetTime,SIGNAL('clicked()'),self.resetTime)
        self.connect(self.ui.grant.btnAddTime,SIGNAL('clicked()'),self.addTime)
        self.connect(self.ui.grant.btnClearAllRestriction,SIGNAL('clicked()'),self.clear_all_restrictions)
        self.connect(self.ui.limits.ckLimit, SIGNAL('toggled(bool)'), self.changed)
        self.connect(self.ui.limits.ckBound, SIGNAL('toggled(bool)'), self.changed)        
        self.connect(self.ui.limits.ckLimitDay, SIGNAL('toggled(bool)'), self.changed)
        self.connect(self.ui.limits.ckBoundDay, SIGNAL('toggled(bool)'), self.changed)
        
        for i in range(3):
	    for j in range(8):
		self.connect(self.spin[i][j],SIGNAL('timeChanged(QTime)'),self.changed)		
		
        
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
	if startday != 7:
	    sundayLimit = self.ui.limits.lyLimitWeek.takeAt(0)
	    self.ui.limits.lyLimitWeek.addItem(sundayLimit)
	    sundayBound = self.ui.limits.lyBoundWeek.takeAt(0)
	    self.ui.limits.lyBoundWeek.addItem(sundayBound)
	
	self.toggle_daily_limit(self.ui.limits.ckLimitDay.isChecked())
	self.toggle_daily_bound(self.ui.limits.ckBoundDay.isChecked())
    
    
    def loadUser(self):
        passwd = open('/etc/passwd','r').read()
        userinfodb = re.compile('^.+$', re.M).findall(passwd)        
    
        for entry in userinfodb:
            userinfo = re.split(':',entry)
            if isnormal(userinfo[0],int(userinfo[2])):
		self.ui.cbActiveUser.addItem(userinfo[0])               
        self.ui.cbActiveUser.setCurrentIndex(0)
    
    
    def enable_limit(self,checked):
        if checked:
            self.ui.limits.wgLimitConf.setEnabled(True)
        else:
            #self.ui.limits.ckLimitDay.setChecked(False)
            self.ui.limits.wgLimitConf.setEnabled(False)            
            
                        
    def enable_bound(self,checked):
	if checked:
            self.ui.limits.wgBoundConf.setEnabled(True)
        else:
	    #self.ui.limits.ckBoundDay.setChecked(False)
            self.ui.limits.wgBoundConf.setEnabled(False)
            
            
    def toggle_daily_limit(self,checked):
        if checked:
            self.ui.limits.wgLimitEveryDay.hide()
            self.ui.limits.wgLimitWeek.show()
            self.ui.limits.wgLimitSunday.show()
        else:
            self.ui.limits.wgLimitWeek.hide()
            self.ui.limits.wgLimitSunday.hide()
            self.ui.limits.wgLimitEveryDay.show()

                
    def toggle_daily_bound(self,checked):
        if checked:
            self.ui.limits.wgBoundEveryDay.hide()
            self.ui.limits.wgBoundWeek.show()
            self.ui.limits.wgBoundSunday.show()
        else:
            self.ui.limits.wgBoundWeek.hide()
            self.ui.limits.wgBoundSunday.hide()
            self.ui.limits.wgBoundEveryDay.show()	
    
    
    def get_spin(self):
	self.spin = [list(),list(),list()]
	
	self.spin[0].append(self.ui.limits.sbLimit_0)
        self.spin[0].append(self.ui.limits.sbLimit_1)
        self.spin[0].append(self.ui.limits.sbLimit_2)
        self.spin[0].append(self.ui.limits.sbLimit_3)
        self.spin[0].append(self.ui.limits.sbLimit_4)
        self.spin[0].append(self.ui.limits.sbLimit_5)
        self.spin[0].append(self.ui.limits.sbLimit_6)
        self.spin[0].append(self.ui.limits.sbLimit_7)
        
        self.spin[1].append(self.ui.limits.sbFrom_0)
        self.spin[1].append(self.ui.limits.sbFrom_1)
        self.spin[1].append(self.ui.limits.sbFrom_2)
        self.spin[1].append(self.ui.limits.sbFrom_3)
        self.spin[1].append(self.ui.limits.sbFrom_4)
        self.spin[1].append(self.ui.limits.sbFrom_5)
        self.spin[1].append(self.ui.limits.sbFrom_6)
        self.spin[1].append(self.ui.limits.sbFrom_7)
        
        self.spin[2].append(self.ui.limits.sbTo_0)
        self.spin[2].append(self.ui.limits.sbTo_1)
        self.spin[2].append(self.ui.limits.sbTo_2)
        self.spin[2].append(self.ui.limits.sbTo_3)
        self.spin[2].append(self.ui.limits.sbTo_4)
        self.spin[2].append(self.ui.limits.sbTo_5)
        self.spin[2].append(self.ui.limits.sbTo_6)
        self.spin[2].append(self.ui.limits.sbTo_7)
    
    
    #TODO:Use plasmadataengine if possible to save file access
    def update_time_left(self):       
	if self.status['limited'] != 1:
	    self.ui.status.lbTimeLeftStatus.setText("Not limited")     
	else:
	    left = self.get_time_left()
	    hours, minutes = sec_to_hr_mn(left)
	    self.ui.status.lbTimeLeftStatus.setText(str(hours) + " hr " + str(minutes) + " min")     
	    self.reset_button_state()
    
    
    def get_time_left(self):
	limit = self.get_limit()
	used = self.get_used_time()
	return limit - used
	
                
    def get_limit(self):
	limit = 86400
        if self.status['limited']:
	    if self.status['limitedByDay']:
		dayIndex = int(strftime("%w"))
		limit = convert_limits(self.limits,dayIndex)
	    else:
		limit = convert_limits(self.limits,7)
	return limit
	    
	    
    def get_used_time(self):
	timefile = VAR['TIMEKPRWORK'] + '/' + self.user + '.time'
        used = 0
        if isfile(timefile) and from_today(timefile):
            t = open(timefile)
            used = int(t.readline())
            t.close()
        return used
          
    def statusicons(self):
	if (not self.status['bounded'] or self.status['bounded']==2) and not self.status['locked']:
	    self.ui.status.ldAllDayLoginStatus.on()
	else:
	    self.ui.status.ldAllDayLoginStatus.off()
	
	if self.status['locked']:
	    self.ui.status.ldLockStatus.on()
	else:
	    self.ui.status.ldLockStatus.off()
	    
	if self.status['bounded'] == BOUND:
	    self.ui.status.ldBoundStatus.on()
	elif self.status['bounded'] == NOBOUND:
	    self.ui.status.ldBoundStatus.off()
	else:
	    self.ui.status.ldBoundStatus.off()
	    #TODO:Add just for today label
	    
	if self.status['limited'] == LIMIT:
	    self.ui.status.ldLimitStatus.on()
	elif self.status['limited'] == NOLIMIT:
	    self.ui.status.ldLimitStatus.off()
	else:
	    self.ui.status.ldLimitStatus.off()
	    #TODO:Add just for today label
	
	self.update_time_left()
	    
	    
    def reset_button_state(self):
	if self.status['limited'] and self.get_used_time():
	    self.ui.grant.btnResetTime.setEnabled(True)
	else:
	    self.ui.grant.btnResetTime.setEnabled(False)
	    
	    
    def buttonstates(self):
	if self.status['locked']:
	    self.ui.grant.btnLockAccount.setEnabled(False)
	    self.ui.grant.btnUnlockAccount.setEnabled(True)
	else:
	    self.ui.grant.btnLockAccount.setEnabled(True)
	    self.ui.grant.btnUnlockAccount.setEnabled(False)
	    
	
	if self.status['bounded']:
	    if self.status['bounded'] == BOUND:
		index = int(strftime("%w"))
		wfrom = self.time_from
		wto = self.time_to
		if wfrom[index] != '00:00' or wto[index] != '24:00':
		    self.ui.grant.btnBoundBypass.setEnabled(True)
		    self.ui.grant.btnClearBoundBypass.setEnabled(False)
		else:
		    self.ui.grant.btnBoundBypass.setEnabled(False)
		    self.ui.grant.btnClearBoundBypass.setEnabled(True)
	    else:
		self.ui.grant.btnBoundBypass.setEnabled(False)
		self.ui.grant.btnClearBoundBypass.setEnabled(True)
	else:
	    self.ui.grant.btnBoundBypass.setEnabled(False)
	    self.ui.grant.btnClearBoundBypass.setEnabled(False)
	
	
	
	if self.status['limited'] == LIMIT:
	    timefile = VAR['TIMEKPRWORK'] + '/' + self.user + '.time'
            #if isfile(timefile):
	    self.reset_button_state()
	    #Reward button should add time even if .time is not there?
	    self.ui.grant.btnLimitBypass.setEnabled(True)
	    self.ui.grant.btnClearLimitBypass.setEnabled(False)
	    self.ui.grant.btnAddTime.setEnabled(True)
	    self.ui.grant.sbAddTime.setEnabled(True)
	    self.ui.grant.lbAddTime.setEnabled(True)
	else:
	    self.ui.grant.btnResetTime.setEnabled(False)
	    self.ui.grant.btnAddTime.setEnabled(False)
	    self.ui.grant.sbAddTime.setEnabled(False)
	    self.ui.grant.lbAddTime.setEnabled(False)
	    if self.status['limited'] == NOLIMIT:
		self.ui.grant.btnLimitBypass.setEnabled(False)
		self.ui.grant.btnClearLimitBypass.setEnabled(False)
	    else:
		self.ui.grant.btnLimitBypass.setEnabled(False)
		self.ui.grant.btnClearLimitBypass.setEnabled(True)
		
	if ((self.status['locked'] == LOCK) or (self.status['bounded']) or (self.status['limited'])):
	    self.ui.grant.btnClearAllRestriction.setEnabled(True)
	else:
	    self.ui.grant.btnClearAllRestriction.setEnabled(False)
	
	
    #def indexchanged(self):
    #KMessageBox.questionYesNo(this,i18n("<qt>You changed the default component of your choice, do want to save that change now ?</qt>"),QString(),KStandardGuiItem::save(),KStandardGuiItem::discard())==KMessageBox::Yes)
    
    
    def read_settings(self):
	self.user = str(self.ui.cbActiveUser.currentText())
	#uislocked = isuserlocked(self.user)
	#self.status = {'locked':uislocked,'reset':NORESET}
	
	self.limits, self.time_from, self.time_to ,self.status = read_user_settings(self.user,VAR['TIMEKPRDIR'] + '/timekprrc')
	self.load_module_values()
	self.statusicons()
	self.buttonstates()
	self.emit(SIGNAL("changed(bool)"), False)
	
    def executePermissionsAction(self,args):
	action = KAuth.Action("org.kde.kcontrol.kcmtimekpr.managepermissions")
	action.setHelperID("org.kde.kcontrol.kcmtimekpr")
	args['var'] = VAR
	args['user'] = self.user
	action.setArguments(args)
	reply = action.execute()
	return reply
    
    
    def clear_all_restrictions(self):
	answer = KMessageBox.warningContinueCancel(self,i18n("All restriction for user " + self.user + " will be cleared"),i18n("Timekpr"))
	if not answer == KMessageBox.Continue:
	    return
	args = {'subaction':0}
	reply = self.executePermissionsAction(args)
	if not reply.failed():
	    self.status['locked'] = UNLOCK
	    self.status['bounded'] = NOBOUND
	    self.status['limited'] = NOLIMIT
	    self.load_module_values()
	    self.save()
	    self.buttonstates()
	    self.statusicons()
	    
    def lockunlock(self):
	args = {'subaction':1}
	if self.status['locked'] == LOCK:
	    args['operation'] = UNLOCK
	else:
	    args['operation'] = LOCK
	reply = self.executePermissionsAction(args)
	if not reply.failed():
	    self.status['locked'] = not self.status['locked']
	    self.buttonstates()
	    self.statusicons()
	
	
    def bypass_time_frame(self):
	args = {'subaction':2}
	if self.status['bounded'] == NOBOUND or self.status['bounded'] == NOBOUNDTODAY:
	    args['operation'] = BOUND
	else:
	    args['operation'] = NOBOUNDTODAY
	reply = self.executePermissionsAction(args)
	if not reply.failed():
	    if (args['operation'] == NOBOUNDTODAY):
		self.status['bounded'] = NOBOUNDTODAY
	    else:
		self.status['bounded'] = BOUND
	    self.buttonstates()
	    self.statusicons()


    def bypassAccessDuration(self):
	args = {'subaction':3}
	if self.status['limited'] == NOLIMIT or self.status['limited'] == NOLIMITTODAY:
	    args['operation'] = LIMIT
	else:
	    args['operation'] = NOLIMITTODAY
	reply = self.executePermissionsAction(args)
	if not reply.failed():
	    if (args['operation'] == NOLIMITTODAY):
		self.status['limited'] = NOLIMITTODAY
	    else:
		self.status['limited'] = LIMIT
	    self.buttonstates()
	    self.statusicons()
	
	
    def resetTime(self):
	args = {'subaction':4}
	reply = self.executePermissionsAction(args)
	if not reply.failed():
	    self.buttonstates()
	    self.statusicons()


    def addTime(self):
	args = {'subaction':5}
	rewardtime = self.ui.grant.sbAddTime.value() * 60
	if not rewardtime:
	    return
	limit = self.get_limit()
	used = self.get_used_time()
	time = used - rewardtime
	time = max(time,limit - 86400)
	time = min(time,limit)
	
	args['time'] = time
	reply = self.executePermissionsAction(args)
	if not reply.failed():
	    self.ui.grant.sbAddTime.setValue(0)
	    self.buttonstates()
	    self.statusicons()
	
	
    def changed(self):
	#TODO:This function should be removed, it's just for testing
        #If a setting has changed, activate the Apply button
        self.emit(SIGNAL("changed(bool)"), True)


    def defaults(self):
	#self.read_limit_status(True)
	self.limits, self.time_from, self.time_to,self.status = read_user_settings()
	self.load_module_values()
	

    def load(self):
	#This function is called from reset button and automatically during construction
	self.read_settings()
	#FIXME:When the module is loaded from kcmshell the Apply button is enabled, should be disabled
    
   	
    def save(self):
	
	self.temp_config_save()
	settings = read_user_settings(self.user,self.config.name()) 
	lims, bFrom, bTo = parse_settings(settings)
	bound = mktimeconfline(self.user, map(str,bFrom), map(str,bTo) ) + "\n"
	temprcfile = self.config.name()
	helperargs = {"user":self.user,"bound":bound,"temprcfile":temprcfile,"var":VAR}
	action = self.authAction()
	action.setArguments(helperargs)	
	reply = action.execute()
	
	self.read_settings()
	self.update_time_left()
 
 
    def createTempConfig(self):
	tempConfigFile = KTemporaryFile()
	tempConfigFile.open()
	tempConfigName = tempConfigFile.fileName()
	systemConfig = KConfig(VAR['TIMEKPRDIR'] + '/timekprrc', KConfig.SimpleConfig)
	tempConfig = systemConfig.copyTo(tempConfigName)
	QFile.setPermissions(tempConfigName, tempConfigFile.permissions() | QFile.ReadOther);
	return tempConfig
	
    
    def temp_config_save(self):
	userGroup = self.config.group(self.user)
	
	#userGroup.writeEntry("locked",self.status['locked'])
	userGroup.writeEntry("limited",self.ui.limits.ckLimit.isChecked())
	userGroup.writeEntry("limitedByday",self.ui.limits.ckLimitDay.isChecked())
	userGroup.writeEntry("bounded",self.ui.limits.ckBound.isChecked())
	userGroup.writeEntry("boundedByDay",self.ui.limits.ckBoundDay.isChecked())
	
	for i in range(3):
	    vector = list()
	    for j in range(8):
		vector.append(str(self.spin[i][j].time().toString("hhmm")))
	    userGroup.writeEntry(LABELS[i],json.dumps(vector))

	
	self.config.sync()
    
    
    def load_module_values(self):
	self.ui.limits.ckLimit.setChecked(self.status['limited'])
	self.ui.limits.ckLimitDay.setChecked(self.status['limitedByDay'])
	self.ui.limits.ckBound.setChecked(self.status['bounded'])
	self.ui.limits.ckBoundDay.setChecked(self.status['boundedByDay'])	
	
	for i in range(8):
	    self.spin[0][i].setTime(QTime.fromString(self.limits[i],'hhmm'))
	    self.spin[1][i].setTime(QTime.fromString(self.time_from[i],'hhmm'))
	    self.spin[2][i].setTime(QTime.fromString(self.time_to[i],'hhmm'))
    
    
def CreatePlugin(widget_parent, parent, component_data):
    return Timekpr(component_data, widget_parent)