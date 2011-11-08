 
#include "timekprdataengine.h"


TimekprDataEngine::TimekprDataEngine(QObject* parent, const QVariantList& args)
    : Plasma::DataEngine(parent, args)
{
    Q_UNUSED(args)

    setPollingInterval(0); //Polling disabled
}

void TimekprDataEngine::init()
{
    m_config = KSharedConfig::openConfig("/etc/timekpr/timekprrc",KConfig::SimpleConfig);
    m_users = m_config->groupList();
    m_keys.push_back("time_from");
    m_keys.push_back("time_to");
    m_watcher.addPath("/etc/timekpr/timekprrc");
    connect(&m_watcher, SIGNAL(fileChanged(const QString)), this, SLOT(updateAllSources()));
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
    QString boundsingle[2] = {"00,00","24:00"};
    int limit = 86400;
    KConfigGroup group = m_config->group(name);
    
    
    
    if(group.readEntry("bounded")=="true")
    {
	QStringList bounds[2];
	for (int i = 0; i < 2; i++ )
	{
	    QString entry = group.readEntry(m_keys[i]);
	    bounds[i] = parseVector(entry);
	}
	
	int dayIndex = 7;
	if(group.readEntry("boundedByDay")=="true")
	{
	    QDate today = QDate::currentDate();
	    dayIndex = today.dayOfWeek();
	}
	for (int i = 0; i < 2; i++ )
	    boundsingle[i] = bounds[i][dayIndex];
    }
    
    for (int i = 0; i < 2; i++ )
    {
	setData(name,m_keys[i],boundsingle[i]);
    }
    
    
    QFile filer("/var/lib/timekpr/" + name + ".time");
    if (!filer.open(QIODevice::ReadOnly))
	return false;
    
    QTextStream timeusedr(&filer);
    QString timeused = timeusedr.readAll();
    filer.close();
    
    if(group.readEntry("limited")=="true")
    {
	QStringList limits(parseVector(group.readEntry("limits")));
	
	int dayIndex = 7;
	if(group.readEntry("limitedByDay")=="true")
	{
	    QDate today = QDate::currentDate();
	    dayIndex = today.dayOfWeek();
	}
	limit = limits[dayIndex].left(2).toInt() * 3600 + limits[dayIndex].right(2).toInt() * 60;
    }
    
    setData(name,"time_left",limit - timeused.toInt());
    
    qDebug() << limit - timeused.toInt();
    
    return true;
}


QStringList TimekprDataEngine::parseVector(QString vector)
{
    vector.remove(0,2);
    vector.remove(vector.size()-2.,2);
    return vector.split("\", \"");
}

K_EXPORT_PLASMA_DATAENGINE(timekpr,TimekprDataEngine)
  
#include "timekprdataengine.moc"