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
    
    /*QString limit = args["limit"].toString();
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
    */

    //Better to check if actually they have been changed
    addAndRemoveUserLimits(args["user"].toString(),REMOVE);
    addAndRemoveUserLimits(args["user"].toString(),ADD,args["bound"].toString());
    
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
    QString root(var["TIMEKPRWORK"].toString() + "/" + user);

    int code = 0;

    switch (subaction) {
	case ClearAllRestriction:
	    code = clearAllRestriction(root,user);
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
    
    //unlockuser(user);
    
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
    
//     if (timeFile.open(QIODevice::ReadOnly))
//     {
// 	QTextStream read(&timeFile);
// 	read >> time;	
// 	timeFile.close();
//     }
    
    //time = time + time * 60;
    
    if (!timeFile.open(QIODevice::WriteOnly|QIODevice::Truncate))
	return false;
    
    QTextStream write(&timeFile);
    write << time;
    timeFile.close();
    return 0;
}


// bool Helper::removeuserlimits(QString user)
// {
//     QFile filer("/etc/security/time.conf");
//     if (!filer.open(QIODevice::ReadOnly))
// 	return false;
//     QTextStream timeconfr(&filer);
//     QString conf = timeconfr.readAll();
//     filer.close();
//     
//     QString regex = "## TIMEKPR START\\n.*(\\*;\\*;" + user + ";[^\\n]*\\n)";
//     QRegExp re(regex);
//     
//     if(re.indexIn(conf) > -1)
// 	conf.replace(re.cap(1),"");
//     else
// 	return false;
//     
//     //TODO:Better to make a backup copy of the file before truncating it
//     QFile filew("/etc/security/time.conf");
//     if (!filew.open(QIODevice::WriteOnly|QIODevice::Truncate))
// 	return false;
//     QTextStream timeconfw(&filew);
//     timeconfw << conf;
//     filew.close();
//     
//     return true;
// }
// 
// bool Helper::adduserlimits(QString user, QString line)
// {
//     QFile filer("/etc/security/time.conf");
//     if (!filer.open(QIODevice::ReadOnly))
// 	return false;
//     QTextStream timeconfr(&filer);
//     QString conf = timeconfr.readAll();
//     filer.close();
//     
//     QString regex = "(## TIMEKPR END)";
//     QRegExp re(regex);
//     
//     if(re.indexIn(conf) > -1)
// 	if(operation == 1)
// 	{
// 	    QString newline = line + re.cap(0);
// 	    conf.replace(re.cap(0),newline);
// 	}
// 	else
// 	    conf.replace(re.cap(1),"");
//     else
// 	return false;
//     
//     //TODO:Better to make a backup copy of the file before truncating it
//     QFile filew("/etc/security/time.conf");
//     if (!filew.open(QIODevice::WriteOnly|QIODevice::Truncate))
// 	return false;
//     QTextStream timeconfw(&filew);
//     timeconfw << conf;
//     filew.close();
//     
//     return true;
// }

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

    
KDE4_AUTH_HELPER_MAIN("org.kde.kcontrol.kcmtimekpr", Helper)
