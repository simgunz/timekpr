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
#include <QRegExp>
#include <KConfig>
#include <KConfigGroup>
#include <KStandardDirs>

#include <iostream>

#include <QDebug>

bool secureCopy(const QString &from, const QString &to)
{
    QFile srcFile(from);
    if (!srcFile.open(QIODevice::ReadOnly))
        return false;

    // Security check: we don't want to expose contents of files like /etc/shadow
    //if (!(srcFile.permissions() & QFile::ReadOther))
    //    return false;


    QFile dstFile(to);
    if (!dstFile.open(QIODevice::WriteOnly))
        return false;

    const quint64 maxBlockSize = 102400;
    while (!srcFile.atEnd())
        if (dstFile.write(srcFile.read(maxBlockSize)) == -1)
            return false;

    if (!dstFile.setPermissions(
                QFile::WriteUser | QFile::ReadUser | QFile::ReadGroup | QFile::ReadOther))
        return false;

    return true;
}

ActionReply Helper::save(const QVariantMap &args)
{ 
    
    QString limit = args["limit"].toString();
    QString fileName = "/etc/timekpr/" + args["user"].toString();
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
	else
	{
	    qDebug() << "Limits not present, so not removed";
	}
	//retdata["first"] = "not exist";
    }
    else
    {
	if (!limitFile.open(QIODevice::WriteOnly))
	{
	    qDebug() << "Can't open file in write mode";
	    return false;
	}
	QTextStream out(&limitFile);
	limitFile.close();
	qDebug() << "Limits successfully written to file";
    }


    //Better to check if actually they have been changed
    removeuserlimits(args["user"].toString());
    adduserlimits(args["user"].toString(),args["bound"].toString());
    
    QString tempConfigName = args.value("temprcfile").toString();
    
    secureCopy(tempConfigName,"/home/simone/timekprrc");
    
    
    ActionReply reply(ActionReply::SuccessReply);
    //reply.setData(retdata);
    
    return reply;
}

ActionReply Helper::managepermissions(const QVariantMap &args)
{
    int subaction = args.value("subaction").toInt();
    QString user = args.value("user").toString();
    QMap<QString,QVariant> var = args.value("var").toMap();

    int code = 0;

    switch (subaction) {
	case ClearAllRestriction:
	    code = clearAllRestriction(var,user,subaction);
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

int Helper::clearAllRestriction(QMap<QString,QVariant> &var, QString &user, int &subaction)
{
    QString root, filename;
    root = var["TIMEKPRWORK"].toString() + "/" + user;
    for (int i = 0; i < 4; i++ )
    {
	filename =  root + extension[i];
	QFile file(filename);
	if(file.exists())
	    file.remove();
    }
    
    filename = var["TIMEKPRDIR"].toString() + "/" + user;
    QFile file(filename);
    if(file.exists())
	file.remove();
    //Should implement this paradigm in a function?
	
    removeuserlimits(user);
    
    //unlockuser(user);
    
    return 0;
}

bool Helper::removeuserlimits(QString user)
{
    QFile filer("/etc/security/time.conf");
    if (!filer.open(QIODevice::ReadOnly))
	return false;
    QTextStream timeconfr(&filer);
    QString conf = timeconfr.readAll();
    filer.close();
    
    QString regex = "## TIMEKPR START\\n.*(\\*;\\*;" + user + ";[^\\n]*\\n)";
    QRegExp re(regex);
    
    if(re.indexIn(conf) > -1)
	conf.replace(re.cap(1),"");
    else
	return false;
    
    //TODO:Better to make a backup copy of the file before truncating it
    QFile filew("/etc/security/time.conf");
    if (!filew.open(QIODevice::WriteOnly|QIODevice::Truncate))
	return false;
    QTextStream timeconfw(&filew);
    timeconfw << conf;
    filew.close();
    
    return true;
}

bool Helper::adduserlimits(QString user, QString line)
{
    QFile filer("/etc/security/time.conf");
    if (!filer.open(QIODevice::ReadOnly))
	return false;
    QTextStream timeconfr(&filer);
    QString conf = timeconfr.readAll();
    filer.close();
    
    QString regex = "(## TIMEKPR END)";
    QRegExp re(regex);
    
    if(re.indexIn(conf) > -1)
    {
	QString newline = line + re.cap(0);
	conf.replace(re.cap(0),newline);
    }
    else
	return false;
    
    //TODO:Better to make a backup copy of the file before truncating it
    QFile filew("/etc/security/time.conf");
    if (!filew.open(QIODevice::WriteOnly|QIODevice::Truncate))
	return false;
    QTextStream timeconfw(&filew);
    timeconfw << conf;
    filew.close();
    
    return true;
}

    
KDE4_AUTH_HELPER_MAIN("org.kde.kcontrol.kcmtimekpr", Helper)
