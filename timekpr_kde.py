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
from timekprpamDV import *
from timekprcommonDV import *


#timekpr.conf variables (dictionary variable)
global VAR
VAR = getvariables(DEVACTIVE)    
version = getversion()



class TimekprKDE (KCModule):
    def __init__(self, component_data, parent):
        KCModule.__init__(self,component_data, parent)
        
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
        
        #Code for the tab mode, need to change the main.ui
        #self.ui.statusLayout = QVBoxLayout(self.ui.tab)
        #self.ui.statusLayout.addWidget(self.ui.status)
        #statusSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        #self.ui.statusLayout.addItem(statusSpacer)
        #self.ui.limitsLayout = QVBoxLayout(self.ui.tab_2)
        #self.ui.limitsLayout.addWidget(self.ui.limits)
        #limitsSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        #self.ui.limitsLayout.addItem(limitsSpacer)
        
        self.lyMainLayout = QVBoxLayout(self)
        self.lyMainLayout.addWidget(self.ui)
        
        #Set buttons
        #self.setButtons(KCModule.Apply)
        #self.changed.emit(True)
        
        #Interface initialization
        self.ui.limits.wgLimitConfDay.setEnabled(False)
        self.ui.limits.wgBoundConfDay.setEnabled(False)
        
        self.ui.limits.wgLimitWeek.hide()
        self.ui.limits.wgBoundWeek.hide()
        
        
        ##Timer
        self.minutesLeft = 10
        
        self.timer = QTimer()
        self.timer.setInterval(10000)
        self.timer.start()
        
        #Signal and slots definition
        self.connect(self.ui.limits.ckLimit, SIGNAL('clicked()'), self.enable_limit)
        self.connect(self.ui.limits.ckBound, SIGNAL('clicked()'), self.enable_bound)
        
        self.connect(self.ui.limits.ckLimitDay, SIGNAL('clicked()'), self.toggle_daily_limit)
        self.connect(self.ui.limits.ckBoundDay, SIGNAL('clicked()'), self.toggle_daily_bound)
        
        self.connect(self.timer, SIGNAL('timeout()'), self.update_time_left)
        
        self.connect(self.timer, SIGNAL('timeout()'), self.get_limit_spin)
        
        self.connect(self.ui.cbActiveUser, SIGNAL('currentIndexChanged(int)'), self.read_settings)
        
        
        self.set_locale()
        
        self.get_limit_spin()
        self.get_from_spin()
        self.get_to_spin()
        
        self.setNeedsAuthorization(True)
        #self.setUseRootOnlyMessage(True)
        #Using /etc/shadow spwd module
        #getspall acquisisce la struct di 8 elementi di tutti gli utenti del sistema
        #il primo elemento rappresenta il nome utente
        for userinfo in getspall():
            if isnormal(userinfo[0]):
                self.ui.cbActiveUser.addItem(userinfo[0])
                self.ui.cbActiveUser.setCurrentIndex(0)  
	
	#Ensure we have at least one available normal user
	if self.ui.cbActiveUser.count() == 0:
	    self.ui.gbStatus.setEnabled(False)
	    self.ui.gbGrant.setEnabled(False)
	    self.ui.gbLimitBound.setEnabled(False)
	
	self.read_settings()
   
#Function definition

    #Need to find a way to get the kde locale
    def set_locale(self):
	self.locale = 'it'
	
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
	
	self.toggle_daily_limit()
	self.toggle_daily_bound()
	
    def update_time_left(self):
        self.minutesLeft -= 1
        label = QString.number(self.minutesLeft) + " min"
        self.ui.status.lbTimeLeftStatus.setText(label)
   
    def enable_limit(self):
        if self.ui.limits.ckLimit.isChecked():
            self.ui.limits.wgLimitConfDay.setEnabled(True)
        else:
            self.ui.limits.wgLimitConfDay.setEnabled(False)
            
    def enable_bound(self):
        if self.ui.limits.ckBound.isChecked():
            self.ui.limits.wgBoundConfDay.setEnabled(True)
        else:
            self.ui.limits.wgBoundConfDay.setEnabled(False)
            
    def toggle_daily_limit(self):
        if self.ui.limits.ckLimitDay.isChecked():
	    self.ui.limits.lbLimit_0.setText("Sunday")
            self.ui.limits.wgLimitWeek.show()
            self.ui.limits.vLineLimit.show()
        else:
	    self.ui.limits.lbLimit_0.setText("Every day")
            self.ui.limits.wgLimitWeek.hide()
            self.ui.limits.vLineLimit.hide()
            
            
    def toggle_daily_bound(self):
        if self.ui.limits.ckBoundDay.isChecked():
            self.ui.limits.lbBound_0.setText("Sunday")
            self.ui.limits.wgBoundWeek.show()
            self.ui.limits.vLineBound.show()
        else:
            self.ui.limits.wgBoundWeek.hide()
            self.ui.limits.lbBound_0.setText("Every day")
            self.ui.limits.vLineBound.hide()
            
            
           
      
    def hours_to_minutes(self):
        self.ui.limits.sbAccHrMon.getvalue()
        
    def minutes_to_hours(self):
        print "ciao"
        
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

    def read_settings(self):
	self.user = self.ui.cbActiveUser.currentText()
	uislocked = isuserlocked(self.user)
	self.fromtolimits = getuserlimits(self.user)
	self.readfromtolimit()
    
    def defaults(self):
	self.read_settings()
	
    def save(self):
	print "salvato"
    
    def readfromtolimit(self):
        #from-to time limitation (aka boundaries) - time.conf
        #TODO:Sostituisci vittima con self.user ma prima converti in stringa
        if isuserlimited('vittima'):
            #Get user time limits (boundaries) as lists from-to
            bfrom = self.fromtolimits[0]
            bto = self.fromtolimits[1]
            
            for i in range(7):
                self.fromSpin[0][i].setValue(float(bfrom[i]))
                self.toSpin[0][i].setValue(float(bto[i]))
            # Use boundaries?
'''            
            ub = True
            # Single boundaries? (set per day)
            sb = False
            #Are all boundaries the same?
            #If they're not same, activate single (per day) boundaries
            if [bfrom[0]] * 7 != bfrom or [bto[0]] * 7 != bto:
                sb = True
            #Even if boundaries are Al0000-2400, return False
            if not sb and bfrom[0] == '0' and bto[0] == '24':
                ub = False
            self.boundariesCheck.set_active(ub)
            self.singleBoundaries.set_active(sb)
        else:
            for i in range(7):
                self.fromSpin[i].set_value(7)
                self.toSpin[i].set_value(22)
            self.boundariesCheck.set_active(False)
            self.singleBoundaries.set_active(False)
'''

#Check if it is a regular user, with userid within UID_MIN and UID_MAX.
def isnormal(username):
#FIXME: Hide active user - bug #286529
#SUDO_USER contains the username of the sudo user that launched timekpr
#So this function return yes for all the non-system user and false for the system-user and for the user that launched timekp
    if (getenv('SUDO_USER') and username == getenv('SUDO_USER')):
	return False
    
    #Ritorna l'uid dell'utente e controlla che sia nel range degli uid assegnabili a utenti normali (non di sistema)
    userid = int(getpwnam(username)[2])
    logindefs = open('/etc/login.defs')
    uidminmax = re.compile('^UID_(?:MIN|MAX)\s+(\d+)', re.M).findall(logindefs.read())
    #Perche maggiore invertito?
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

def CreatePlugin(widget_parent, parent, component_data):
    #Create configuration folder if not existing
    if not isdir(VAR['TIMEKPRDIR']):
        mkdir(VAR['TIMEKPRDIR'])
    if not isdir(VAR['TIMEKPRWORK']):
        mkdir(VAR['TIMEKPRWORK'])
    #if not isdir(VAR['TIMEKPRSHARED']):  
    #    exit('Error: Could not find the shared directory %s' % VAR['TIMEKPRSHARED']
	
    return TimekprKDE(component_data, widget_parent)