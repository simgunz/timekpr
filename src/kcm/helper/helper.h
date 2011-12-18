/*
KDE KCModule for configuring timekpr
Copyright (c) 2008, 2010 Timekpr Authors.
This file is licensed under the General Public License version 3 or later.
See the COPYRIGHT file for full details. You should have received the COPYRIGHT file along with the program
*/

#ifndef KDM_HELPER_H
#define KDM_HELPER_H

#include <kauth.h>
#include <QString> //needed?

enum Operation {ADD, REMOVE};

using namespace KAuth;

const QString extension[] = {".logout",".late",".allow"};

class Helper : public QObject {
    Q_OBJECT

public slots:
    ActionReply save(const QVariantMap &map);
    
private:
    bool savelimits(const QVariantMap &args);
    bool managepermissions(const QVariantMap &args);
    bool addAndRemoveUserLimits(QString user, Operation op, QString line = "");
    bool lockUnlock(QString user, int op);
    bool clearAllRestriction(QString root,QString user);
    bool bypass(QString root,QString user);
    bool clearBypass(QString root,QString user);
    bool resetTime(QString root);
    bool addTime(QString root,int rewardTime);
    enum { ClearAllRestriction, Lock, Bypass, ClearBypass, ResetTime, AddTime };
};

#endif
