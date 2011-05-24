/*
KDE KCModule for configuring timekpr
Copyright (c) 2008, 2010 Timekpr Authors.
This file is licensed under the General Public License version 3 or later.
See the COPYRIGHT file for full details. You should have received the COPYRIGHT file along with the program
*/
#include "helper.h"


#include <QFile>
#include <QTextStream>
#include <QDir>
#include <KConfig>
#include <KConfigGroup>
#include <KStandardDirs>

#include <iostream>
#include <string>

#include <QDebug>

ActionReply Helper::save(const QVariantMap &args)
{ 
    
    QString limit = args["limit"].toString();
    QString fileName("/etc/timekpr/");
    fileName += args["user"].toString();
    QFile limitFile(fileName);
    
    //QVariantMap retdata;
    
    if (limit == "limit=( )")
    {
	if(limitFile.exists())
	{
	    limitFile.remove();
	    //retdata["first"] = "exist";
	    qDebug() << "Limits removed";
	}
	qDebug() << "Limits not present, so not removed";
	//retdata["first"] = "not exist";
    }
    else
    {
	//if (!limitFile.open(QIODevice::WriteOnly|QFile::Truncate))
	if (!limitFile.open(QIODevice::WriteOnly))
	{
	    qDebug() << "Can't open file in write mode";
	    return false;
	}
	QTextStream out(&limitFile);
	qDebug() << limit;
	out << limit << endl;
	limitFile.close();
	qDebug() << "Limits successfully written to file";
    }


    
    
    
    
    ActionReply reply(ActionReply::SuccessReply);
    //reply.setData(retdata);
    
    return reply;
}

ActionReply Helper::managepermissions(const QVariantMap &args)
{
    int subaction = args.value("subaction").toInt();

    int code = 0;

    switch (subaction) {
	case ClearAllRestriction:
	    code = (0);
	    break;
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
