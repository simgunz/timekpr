 
#include "timekprdataengine.h"



TimekprDataEngine::TimekprDataEngine(QObject* parent, const QVariantList& args)
    : Plasma::DataEngine(parent, args)
{
    Q_UNUSED(args)

    setMinimumPollingInterval(1000);
}

void TimekprDataEngine::init()
{
    m_config = KSharedConfig::openConfig("/etc/timekpr/timekprrc",KConfig::SimpleConfig);
    m_users = m_config->groupList();
    m_keys.push_back("time_from_hr");
    m_keys.push_back("time_from_mn");
    m_keys.push_back("time_to_hr");
    m_keys.push_back("time_to_mn");
}

QStringList TimekprDataEngine::sources() const
{
	return m_users;
}

bool TimekprDataEngine::sourceRequestEvent(const QString &name)
{

    
	return updateSourceEvent(name);
}

bool TimekprDataEngine::updateSourceEvent(const QString &name)
{   
    m_config->reparseConfiguration();
    int boundint[4] = {0,0,24,0};
    int limit = 86400;
    KConfigGroup group = m_config->group(name);
    
    
    
    if(group.readEntry("bounded")=="true")
    {
	QStringList bounds[4];
	for (int i = 0; i < 4; i++ )
	{
	    QString entry = group.readEntry(m_keys[i]);
	    bounds[i] = parseVector(entry);
	}
	
	int dayIndex = 0;
	if(group.readEntry("boundedByDay")=="true")
	{
	    QDate today = QDate::currentDate();
	    dayIndex = today.dayOfWeek();
	}
	for (int i = 0; i < 4; i++ )
	    boundint[i] = bounds[i][dayIndex].toInt();
    }
    
    for (int i = 0; i < 4; i++ )
    {
	setData(name,m_keys[i],boundint[i]);
    }
    
    
    QFile filer("/var/lib/timekpr/" + name + ".time");
    if (!filer.open(QIODevice::ReadOnly))
	return false;
    QTextStream timeusedr(&filer);
    QString timeused = timeusedr.readAll();
    filer.close();
    
    if(group.readEntry("limited")=="true")
    {
	QStringList limitHr(parseVector(group.readEntry("limits_hr")));
	QStringList limitMn(parseVector(group.readEntry("limits_mn")));
	
	int dayIndex = 0;
	if(group.readEntry("limitedByDay")=="true")
	{
	    QDate today = QDate::currentDate();
	    dayIndex = today.dayOfWeek();
	}
	limit = limitHr[dayIndex].toInt() * 3600 + limitMn[dayIndex].toInt() * 60;
    }
    

    setData(name,"time_left",limit - timeused.toInt());
    
    
    
    return true;
}


QStringList TimekprDataEngine::parseVector(QString vector)
{
    vector.remove(0,1);
    vector.remove(vector.size()-1.,1);
    return vector.split(", ");
}

K_EXPORT_PLASMA_DATAENGINE(timekpr,TimekprDataEngine)
  
#include "timekprdataengine.moc"