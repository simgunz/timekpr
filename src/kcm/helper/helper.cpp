/*
KDE KCModule for configuring timekpr
Copyright (c) 2008, 2010 Timekpr Authors.
This file is licensed under the General Public License version 3 or later.
See the COPYRIGHT file for full details. You should have received the COPYRIGHT file along with the program
*/
#include "helper.h"


#include <QFile>
#include <QDir>
#include <KConfig>
#include <KConfigGroup>
#include <KStandardDirs>

#include <iostream>
#include <string>


ActionReply Helper::save(const QVariantMap &args)
{ 
    
    QString arg = args["primo"].toString();
    
    int a = 10 + arg.toInt();
    
    QVariantMap retdata;
    retdata["first"] = a;
    
    
    ActionReply reply(ActionReply::SuccessReply);
    reply.setData(retdata);
    
    return reply;
}

KDE4_AUTH_HELPER_MAIN("org.kde.kcontrol.kcmtimekpr", Helper)
