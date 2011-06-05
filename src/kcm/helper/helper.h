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

using namespace KAuth;

class Helper : public QObject {
    Q_OBJECT
    
public:
    enum { ClearAllRestriction, Lock, BypassTimeFrame, BypassAccessDuration, ResetTime, AddTime };
    
public slots:
    ActionReply save(const QVariantMap &map);
    ActionReply managepermissions(const QVariantMap &map);
    
private:
    bool removeuserlimits(QString user);
    bool adduserlimits(QString user, QString line);
};

#endif
