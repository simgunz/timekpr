 
#include "timekprdataengine.h"

#include <QDateTime>

TimekprDataEngine::TimekprDataEngine(QObject* parent, const QVariantList& args)
    : Plasma::DataEngine(parent, args)
{
    Q_UNUSED(args)

    setMinimumPollingInterval(1000);
}

QStringList TimekprDataEngine::sources() const
{
	return QStringList() << "Number";
}

bool TimekprDataEngine::sourceRequestEvent(const QString &name)
{
    if ( name != "Number" )
		return false;
	
	qsrand( QDateTime::currentDateTime().toTime_t() );
    
	return updateSourceEvent(name);
}

bool TimekprDataEngine::updateSourceEvent(const QString &name)
{
    if ( name != "Number" )
		return false;
	
	setData( name, "Random", qrand() );
    
    return true;
}

K_EXPORT_PLASMA_DATAENGINE(timekpr,TimekprDataEngine)
  
#include "timekprdataengine.moc"