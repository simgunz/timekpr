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

ActionReply Helper::managepermissions(const QVariantMap &args)
{
    int subaction = args.value("subaction").toInt();

    int code = 0;

    switch (subaction) {
    case Lock:
        code = (0);
        break;
    case BypassTimeFrame:
        code = (0);
        break;
    case BypassAccessDuration:
        code = (0);
        break;
    case ResetTime:
        code = (0);
        break;
    case AddTime:
        code = (0);
        break;
    default:
        return ActionReply::HelperError;
    }

    return ActionReply::SuccessReply;
    //return createReply(code);
}

KDE4_AUTH_HELPER_MAIN("org.kde.kcontrol.kcmtimekpr", Helper)
