 
#ifndef TIMEKPRDATAENGINE_H
#define TIMEKPRDATAENGINE_H

#include <Plasma/DataEngine>

class TimekprDataEngine : public Plasma::DataEngine
{
    Q_OBJECT

    public:
        TimekprDataEngine(QObject* parent, const QVariantList& args);
	QStringList sources() const;
	
    protected:
        bool sourceRequestEvent(const QString& name);
        bool updateSourceEvent(const QString& source);
};

#endif //TIMEKPRDATAENGINE_H
