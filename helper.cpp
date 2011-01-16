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
    //arg = arg + "9";
    int a = 10 + arg.toInt();
    
    QVariantMap retdata;
    retdata["first"] = a;
    
    ActionReply reply(ActionReply::SuccessReply);
    reply.setData(retdata);
    
    return reply;
}

KDE4_AUTH_HELPER_MAIN("org.kde.kcontrol.timekprkde", Helper)
