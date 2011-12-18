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
    
public:
    enum { ClearAllRestriction, Lock, Bypass, ClearBypass, ResetTime, AddTime };
public slots:
    ActionReply save(const QVariantMap &map);
    ActionReply managepermissions(const QVariantMap &map);
    
private:
    //bool removeuserlimits(QString user);
    //bool adduserlimits(QString user, QString line);
    bool addAndRemoveUserLimits(QString user, Operation op, QString line = "");
    int lockUnlock(QString user, int op);
    int clearAllRestriction(QString root,QString user);
    int resetTime(QString root);
    int addTime(QString root,int rewardTime);
};

#endif
