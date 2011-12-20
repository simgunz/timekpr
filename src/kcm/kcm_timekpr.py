#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# KDE KCModule for configuring timekpr
#
# Copyright (c) 2008, 2010 Timekpr Authors.
# This file is licensed under the General Public License version 3 or later.
# See the COPYRIGHT file for full details. You should have received the COPYRIGHT file along with the program

from os import remove, getenv
from os.path import isfile, dirname
import json

from PyQt4.QtGui import *
from PyQt4 import uic, QtCore
from PyQt4.QtCore import *
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *

from timekprpam import *
from timekprcommon import *


#timekpr.conf variables (dictionary variable)
global VAR
VAR = get_variables()   
VERSION = get_version()
        
        
class Timekpr (KCModule):
    def __init__(self, component_data, parent):
        KCModule.__init__(self,component_data, parent)
        
        self.aboutdata = self.make_about_data()
        self.setAboutData(self.aboutdata)
            
        #Interface initialization
    
        #Loading the UI module dynamically
        self.ui = uic.loadUi(unicode(dirname(__file__) + "/ui/main.ui"))
        self.ui.status = uic.loadUi(unicode(dirname(__file__) + "/ui/status.ui"))
        self.ui.grant = uic.loadUi(unicode(dirname(__file__) + "/ui/grant.ui"))
        self.ui.limits = uic.loadUi(unicode(dirname(__file__) + "/ui/limits.ui"))
        # Organizing the modules in a layout
        self.ui.lyStatus.addWidget(self.ui.status)
        self.ui.lyGrant = QVBoxLayout(self.ui.tbGrant)
        self.ui.lyGrant.addWidget(self.ui.grant)
        self.ui.lyLimitBound = QVBoxLayout(self.ui.tbLimitBound)
        self.ui.lyLimitBound.addWidget(self.ui.limits)            
        self.lyMainLayout = QVBoxLayout(self)
        self.lyMainLayout.addWidget(self.ui)
        #Disable the limits by default
        self.ui.limits.wgLimitConf.setEnabled(False)
        self.ui.limits.wgBoundConf.setEnabled(False)
        #Copying the spinboxes to a list for faster access
        self.get_spin()
        #Set the format of the week
        self.set_locale()
        #Initializing the user combobox
        self.load_users() 
        #Initializing an empty list for time limits
        self.limits = []
        self.status = dict()
        #Timer initializing
        self.timer = QTimer()
        self.timer.setInterval(10000)
        self.timer.start()
        #KConfig
        self.config = self.create_temp_config()
        #Signal and slots definition 
        self.connect(self.ui.limits.ckLimit, SIGNAL('toggled(bool)'), self.enable_limit)
        self.connect(self.ui.limits.ckBound, SIGNAL('toggled(bool)'), self.enable_bound)        
        self.connect(self.ui.limits.ckLimitDay, SIGNAL('toggled(bool)'), self.enable_daily_limit)
        self.connect(self.ui.limits.ckBoundDay, SIGNAL('toggled(bool)'), self.enable_daily_bound)
        self.connect(self.ui.cbActiveUser, SIGNAL('currentIndexChanged(int)'), self.read_settings)
        self.connect(self.timer, SIGNAL('timeout()'), self.update_time_left)
        self.connect(self.ui.grant.btnLockAccount,SIGNAL('clicked()'),self.lock_unlock)
        self.connect(self.ui.grant.btnUnlockAccount,SIGNAL('clicked()'),self.lock_unlock)
        self.connect(self.ui.grant.btnBypass,SIGNAL('clicked()'),self.bypass_restrictions)
        self.connect(self.ui.grant.btnClearBypass,SIGNAL('clicked()'),self.clear_bypass)
        self.connect(self.ui.grant.btnResetTime,SIGNAL('clicked()'),self.reset_time)
        self.connect(self.ui.grant.btnAddTime,SIGNAL('clicked()'),self.add_time)
        self.connect(self.ui.grant.btnClearAllRestriction,SIGNAL('clicked()'),self.clear_all_restrictions)
        self.connect(self.ui.limits.ckLimit, SIGNAL('toggled(bool)'), self.changed)
        self.connect(self.ui.limits.ckBound, SIGNAL('toggled(bool)'), self.changed)        
        self.connect(self.ui.limits.ckLimitDay, SIGNAL('toggled(bool)'), self.changed)
        self.connect(self.ui.limits.ckBoundDay, SIGNAL('toggled(bool)'), self.changed)
        for i in range(3):
            for j in range(8):
                self.connect(self.spin[i][j],SIGNAL('timeChanged(QTime)'),self.changed)        
        #Ensure we have at least one available normal user otherwise we disable all the modules
        if not self.ui.cbActiveUser.count():
            self.ui.gbStatus.setEnabled(False)
            self.ui.gbGrant.setEnabled(False)
            self.ui.gbLimitBound.setEnabled(False)
        #Needed for using KAuth authentication
        self.setNeedsAuthorization(True)
      
   
#Function definition
    def make_about_data(self):
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
    
    def set_locale(self):
        # Move the Sunday position in the UI based on locale
        locale = KGlobal.locale()
        startday = locale.weekStartDay()  
        if startday != 7:
            sundayLimit = self.ui.limits.lyLimitWeek.takeAt(0)
            self.ui.limits.lyLimitWeek.addItem(sundayLimit)
            sundayBound = self.ui.limits.lyBoundWeek.takeAt(0)
            self.ui.limits.lyBoundWeek.addItem(sundayBound)
            for i in range(3):
                for j in range(8):
                    self.spin[i][j].setDisplayFormat("hh:mm")
        self.enable_daily_limit(self.ui.limits.ckLimitDay.isChecked())
        self.enable_daily_bound(self.ui.limits.ckBoundDay.isChecked())

    def is_normal_user(self,username, userid):
        # Check if the user is in the non-system users range
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
        
    def load_users(self):
        # Fill the combobox with the users
        passwd = open('/etc/passwd','r').read()
        userinfodb = re.compile('^.+$', re.M).findall(passwd)        
        for entry in userinfodb:
            userinfo = re.split(':',entry)
            if self.is_normal_user(userinfo[0],int(userinfo[2])):
                self.ui.cbActiveUser.addItem(userinfo[0])               
                self.ui.cbActiveUser.setCurrentIndex(0)
                
    def enable_limit(self,checked):
        if checked:
            self.ui.limits.wgLimitConf.setEnabled(True)
        else:
            self.ui.limits.wgLimitConf.setEnabled(False)            
                       
    def enable_bound(self,checked):
        if checked:
            self.ui.limits.wgBoundConf.setEnabled(True)
        else:
            self.ui.limits.wgBoundConf.setEnabled(False)
            
    def enable_daily_limit(self,checked):
        if checked:
            self.ui.limits.wgLimitWeek.show()
            self.ui.limits.wgLimitSunday.show()
            self.ui.limits.wgLimitEveryDay.hide()
        else:
            self.ui.limits.wgLimitWeek.hide()
            self.ui.limits.wgLimitSunday.hide()
            self.ui.limits.wgLimitEveryDay.show()
    
    def enable_daily_bound(self,checked):
        if checked:
            self.ui.limits.wgBoundWeek.show()
            self.ui.limits.wgBoundSunday.show()
            self.ui.limits.wgBoundEveryDay.hide()
        else:
            self.ui.limits.wgBoundWeek.hide()
            self.ui.limits.wgBoundSunday.hide()
            self.ui.limits.wgBoundEveryDay.show()    
    
    def get_spin(self):
        # Put all the time spinboxes into an array to permit an easier access
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

    def get_limit(self):
        # Return the duration limit of the user for today in seconds
        limit = 86400
        dayIndex = 7
        if self.status['limited']:
            if self.status['limitedByDay']:
                dayIndex = int(strftime("%w"))
            limit = convert_limits(self.limits,dayIndex)
        return limit

    def get_used_time(self):
        # Return the overall logon time of the user for today in seconds
        timefile = VAR['TIMEKPRWORK'] + '/' + self.user + '.time'
        used = 0
        if is_file_ok(timefile):
            t = open(timefile)
            used = int(t.readline())
            t.close()
        return used

    def sec_to_hhmm(self,sec):
        inminutes = int(sec) / 60
        hr, mn = divmod(inminutes, 60)
        return str(hr) + ':' + str(mn).zfill(2)
        
    def get_time_left(self):
        # Return the usage time left of the user for today or the time from now till midnight if lower
        #TODO:Use datetime to be more precise or a timer better
        limit = self.get_limit()
        used = self.get_used_time()
        left = limit - used
        left = max(0,left)
        currentime = int(strftime("%H")) * 3600 + int(strftime("%M")) * 60
        lefttoday = 86400 - currentime 
        left = min(lefttoday,left)
        return self.sec_to_hhmm(left)
        
    def update_time_left(self):
        # Update the time left label, it is called everytime the timer expire
        if self.status['limited'] != BOUND:
            self.ui.status.lbTimeLeftStatus.setText(i18n("Not limited"))     
        else:
            timeleft = self.get_time_left()
            self.ui.status.lbTimeLeftStatus.setText(timeleft)
            self.reset_button_state()
  
    def update_status_icons(self):
        if self.status['bounded'] == BOUND or self.status['locked']:
            self.ui.status.ldAllDayLoginStatus.off()
        else:
            self.ui.status.ldAllDayLoginStatus.on()
                    
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
                
    def update_buttons_state(self):
        if self.status['locked'] or self.status['bounded'] or self.status['limited']:
            self.ui.grant.btnClearAllRestriction.setEnabled(True)
        else:
            self.ui.grant.btnClearAllRestriction.setEnabled(False)
            
        if self.status['locked']:
            self.ui.grant.btnLockAccount.setEnabled(False)
            self.ui.grant.btnUnlockAccount.setEnabled(True)
        else:
            self.ui.grant.btnLockAccount.setEnabled(True)
            self.ui.grant.btnUnlockAccount.setEnabled(False)
                    
        if self.status['limited'] == LIMIT:
            timefile = VAR['TIMEKPRWORK'] + '/' + self.user + '.time'
            self.reset_button_state()
            self.ui.grant.btnAddTime.setEnabled(True)
            self.ui.grant.sbAddTime.setEnabled(True)
            self.ui.grant.lbAddTime.setEnabled(True)
        else:
            self.ui.grant.btnResetTime.setEnabled(False)
            self.ui.grant.btnAddTime.setEnabled(False)
            self.ui.grant.sbAddTime.setEnabled(False)
            self.ui.grant.lbAddTime.setEnabled(False)
        
        if self.status['bypass'] == DISABLED:
            self.ui.grant.btnBypass.setEnabled(False)
            self.ui.grant.btnClearBypass.setEnabled(False)
        elif self.status['bypass'] == OFF:
            self.ui.grant.btnBypass.setEnabled(True)
            self.ui.grant.btnClearBypass.setEnabled(False)
        else:
            self.ui.grant.btnBypass.setEnabled(False)
            self.ui.grant.btnClearBypass.setEnabled(True)                            

    def load_module_values(self):
        self.ui.limits.ckLimit.setChecked(self.status['limited'])
        self.ui.limits.ckLimitDay.setChecked(self.status['limitedByDay'])
        self.ui.limits.ckBound.setChecked(self.status['bounded'])
        self.ui.limits.ckBoundDay.setChecked(self.status['boundedByDay'])        
        for i in range(8):
            self.spin[0][i].setTime(QTime.fromString(self.limits[i],'hhmm'))
            self.spin[1][i].setTime(QTime.fromString(self.time_from[i],'hhmm'))
            self.spin[2][i].setTime(QTime.fromString(self.time_to[i],'hhmm'))
            
    def bypass_status(self):
        # Bypass can be active, unactive or disabled if the user is not limited
        allowfile = VAR['TIMEKPRWORK'] + '/' + self.user + '.allow'
        if is_file_ok(allowfile):
            self.status['bypass'] = ON
        elif self.status['limited'] or self.status['bounded']:
            self.status['bypass'] = OFF
        else:
            self.status['bypass'] = DISABLED
            
    def read_settings(self):
        # Get the user setting from timekprrc and update the UI
        self.user = str(self.ui.cbActiveUser.currentText())
        self.limits, self.time_from, self.time_to,self.status = read_user_settings(self.user,VAR['TIMEKPRDIR'] + '/timekprrc')
        self.load_module_values()
        self.bypass_status()
        self.update_status_icons()
        self.update_buttons_state()
        self.emit(SIGNAL("changed(bool)"), False)
    
    def executePermissionsAction(self,args):
        # Add the common paramenter to all the actions and invoke the module root action
        action = self.authAction()
        args['action'] = 'permissions';
        args['var'] = VAR
        args['user'] = self.user
        action.setArguments(args)
        reply = action.execute()
        return reply

    def clear_all_restrictions(self):
        answer = KMessageBox.warningContinueCancel(self,i18n("All restriction for user %1 will be cleared",self.user),i18n("Timekpr"))
        if answer != KMessageBox.Continue:
            return
        args = {'subaction':0}
        reply = self.executePermissionsAction(args)
        if not reply.failed():
            self.status['locked'] = UNLOCK
            self.status['bounded'] = NOBOUND
            self.status['limited'] = NOLIMIT
            self.load_module_values()
            self.save()
            self.update_buttons_state()
            self.update_status_icons()

    def lock_unlock(self):
        args = {'subaction':1}
        if self.status['locked']:
            args['operation'] = UNLOCK
        else:
            args['operation'] = LOCK
        reply = self.executePermissionsAction(args)
        if not reply.failed():
            self.status['locked'] = not self.status['locked']
            self.update_buttons_state()
            self.update_status_icons()

    def bypass_restrictions(self):
        args = {'subaction':2}
        reply = self.executePermissionsAction(args)
        if not reply.failed():
            self.status['bounded'] = NOBOUNDTODAY
            self.status['limited'] = NOLIMITTODAY
            self.status['bypass'] = ON
            self.update_buttons_state()
            self.update_status_icons()
            
    def clear_bypass(self):
        args = {'subaction':3}
        reply = self.executePermissionsAction(args)
        if not reply.failed():
            self.status['bounded'] = BOUND
            self.status['limited'] = LIMIT        
            self.status['bypass'] = OFF
            self.update_buttons_state()
            self.update_status_icons()
            
    def reset_time(self):
        args = {'subaction':4}
        reply = self.executePermissionsAction(args)
        if not reply.failed():
            self.update_buttons_state()
            self.update_status_icons()

    def add_time(self):
        args = {'subaction':5}
        rewardtime = self.ui.grant.sbAddTime.value() * 60
        if not rewardtime:
            return
        limit = self.get_limit()
        used = self.get_used_time() 
        time = used - rewardtime
        currenttime = int(strftime("%H")) * 3600 + int(strftime("%M")) * 60
        lefttoday = 86400 - currenttime     
        # Limit the maximum amount of time to add or subtract from the usage time to stay into the day bound
        time = max(time,limit - lefttoday)
        time = min(time,limit)
        
        args['time'] = time
        reply = self.executePermissionsAction(args)
        if not reply.failed():
            self.ui.grant.sbAddTime.setValue(0)
            self.update_buttons_state()
            self.update_status_icons()
        
    def changed(self):
        # If a setting has changed, activate the Apply button
        self.emit(SIGNAL("changed(bool)"), True)
    
    #TODO:def index_changed(self):
    #KMessageBox.questionYesNo(this,i18n("<qt>You changed the default component of your choice, 
    #do want to save that change now ?</qt>"),QString(),KStandardGuiItem::save(),KStandardGuiItem::discard())==KMessageBox::Yes)
    
    def defaults(self):
        # Called when the defaults button is pushed
        self.user = str(self.ui.cbActiveUser.currentText())
        self.limits, self.time_from, self.time_to,self.status = read_user_settings()
        self.load_module_values()
        self.bypass_status()
        self.update_status_icons()
        self.update_buttons_state()
    
    def load(self):
        # Called when the reset button is pushed and automatically during construction
        self.read_settings()    

    def create_temp_config(self):
        # Create a temporary KConfig file that can be modified without privilege
        tempconfigfile = KTemporaryFile()
        tempconfigfile.open()
        tempconfigname = tempconfigfile.fileName()
        systemconfig = KConfig(VAR['TIMEKPRDIR'] + '/timekprrc', KConfig.SimpleConfig)
        tempconfig = systemconfig.copyTo(tempconfigname)
        QFile.setPermissions(tempconfigname, tempconfigfile.permissions() | QFile.ReadOther);
        return tempconfig
    
    def save_temp_config(self):
        usergroup = self.config.group(self.user)
        #TODO:usergroup.writeEntry("locked",self.status['locked'])
        usergroup.writeEntry("limited",self.ui.limits.ckLimit.isChecked())
        usergroup.writeEntry("limitedByday",self.ui.limits.ckLimitDay.isChecked())
        usergroup.writeEntry("bounded",self.ui.limits.ckBound.isChecked())
        usergroup.writeEntry("boundedByDay",self.ui.limits.ckBoundDay.isChecked())
        labels = ['limits','time_from','time_to']
        for i in range(3):
            vector = list()
            for j in range(8):
                vector.append(str(self.spin[i][j].time().toString("hhmm")))
                usergroup.writeEntry(labels[i],json.dumps(vector))        
        self.config.sync()
        
    def save(self):
        # Called whe the apply button is pushed. Move the temporary config file to the system wide config file
        self.save_temp_config()
        settings = read_user_settings(self.user,self.config.name()) 
        lims, bFrom, bTo = parse_settings(settings)
        if bFrom:
            bound = mk_time_conf_line(self.user, map(str,bFrom), map(str,bTo)) + "\n"
        else:
            bound = ''
        temprcfile = self.config.name()
        helperargs = {"action":"save","user":self.user,"bound":bound,"temprcfile":temprcfile,"var":VAR}
        action = self.authAction()
        action.setArguments(helperargs)    
        reply = action.execute()
        #TODO:Manage the case of errors
        self.read_settings()
        if not (self.status['limited'] or self.status['bounded']):
            self.clear_bypass()        
        
    
def CreatePlugin(widget_parent, parent, component_data):
    # Called from systemsettings or kcmshell4 to create the module
    return Timekpr(component_data, widget_parent)