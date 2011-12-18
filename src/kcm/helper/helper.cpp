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
    //Better to check if actually they have been changed
    QMap<QString,QVariant> var = args.value("var").toMap();
    QString timekprdir(var["TIMEKPRDIR"].toString());
    
    addAndRemoveUserLimits(args["user"].toString(),REMOVE);
    addAndRemoveUserLimits(args["user"].toString(),ADD,args["bound"].toString());
    
    QString tempConfigName = args.value("temprcfile").toString();
    
    secureCopy(tempConfigName,timekprdir + "/timekprrc");
    
    
    ActionReply reply(ActionReply::SuccessReply);
    //reply.setData(retdata);
    
    return reply;
}

ActionReply Helper::managepermissions(const QVariantMap &args)
{
    int subaction = args.value("subaction").toInt();
    QString user = args.value("user").toString();
    QMap<QString,QVariant> var = args.value("var").toMap();
    QString root(var["TIMEKPRWORK"].toString() + "/" + user);

    int code = 0;

    switch (subaction) {
	case ClearAllRestriction:
	    code = clearAllRestriction(root,user);
	    break;
	case Lock:
	    code = lockUnlock(args["user"].toString(),args.value("operation").toInt());
	    break;
	case Bypass:
	    code = (0);
	    break;
	case ClearBypass:
	    code = (0);
	    break;
	case ResetTime:
	    code = resetTime(root);
	    break;
	case AddTime:
	    code = addTime(root,args.value("time").toInt());
	    break;
	default:
	    return ActionReply::HelperError;
    }

    return ActionReply::SuccessReply;
    //return createReply(code);
}

int Helper::clearAllRestriction(QString root,QString user)
{
    QString filename;
    //root = var["TIMEKPRWORK"].toString() + "/" + user;
    for (int i = 0; i < 3; i++ )
    {
	filename =  root + extension[i];
	QFile file(filename);
	if(file.exists())
	    file.remove();
    }
    
//     filename = var["TIMEKPRDIR"].toString() + "/" + user;
//     QFile file(filename);
//     if(file.exists())
// 	file.remove();
    //Should implement this paradigm in a function?
	
    addAndRemoveUserLimits(user,REMOVE);
    lockUnlock(user, 0);
    
    return 0;
}

int Helper::resetTime(QString root)
{
    QString fileName;
    fileName = root + ".time";
    QFile timeFile(fileName);
    if(timeFile.exists())
	timeFile.remove();
    return 0;
}

int Helper::addTime(QString root,int time)
{
    QString fileName;
    fileName = root + ".time";
    //int time = 0;
    QFile timeFile(fileName);
    
    if (!timeFile.open(QIODevice::WriteOnly|QIODevice::Truncate))
	return false;
    
    QTextStream write(&timeFile);
    write << time;
    timeFile.close();
    return 0;
}

bool Helper::addAndRemoveUserLimits(QString user, Operation op, QString line)
{
    QFile filer("/etc/security/time.conf");
    if (!filer.open(QIODevice::ReadOnly))
	return false;
    QTextStream timeconfr(&filer);
    QString conf = timeconfr.readAll();
    filer.close();
    
    QString regex;
    if(op == ADD)
	regex = "(## TIMEKPR END)";
    else
	regex = "## TIMEKPR START\\n.*(\\*;\\*;" + user + ";[^\\n]*\\n)";
    
    QRegExp re(regex);
    
    if(re.indexIn(conf) > -1)
	if(op == ADD)
	{
	    QString newline = line + re.cap(0);
	    conf.replace(re.cap(0),newline);
	}
	else
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

int Helper::lockUnlock(QString user, int op)
{
    QFile filer("/etc/security/access.conf");
    if (!filer.open(QIODevice::ReadOnly))
	return false;
    QTextStream accessconfr(&filer);
    QString conf = accessconfr.readAll();
    filer.close();
    
    QString regex;
    if(op == 1)
	regex = "(## TIMEKPR END)";
    else
	regex = "## TIMEKPR START\\n.*(-:" + user + ":ALL\\n)";
    
    QRegExp re(regex);
    
    if(re.indexIn(conf) > -1)
	if(op == 1)
	{
	    QString newline = "-:" + user + ":ALL\n" + re.cap(0);
	    conf.replace(re.cap(0),newline);
	}
	else
	    conf.replace(re.cap(1),"");
    else
	return false;
    
    QFile filew("/etc/security/access.conf");
    if (!filew.open(QIODevice::WriteOnly|QIODevice::Truncate))
	return false;
    QTextStream accessconfw(&filew);
    accessconfw << conf;
    filew.close();
    
    return true;
}

KDE4_AUTH_HELPER_MAIN("org.kde.kcontrol.kcmtimekpr", Helper)
