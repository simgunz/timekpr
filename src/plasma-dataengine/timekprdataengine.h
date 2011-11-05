 
#ifndef TIMEKPRDATAENGINE_H
#define TIMEKPRDATAENGINE_H

#include <Plasma/DataEngine>
#include <KSharedConfigPtr>
#include <KSharedConfig>
#include <KConfigGroup>

#include <QStringList>
#include <QDate>
#include <QFile>

class TimekprDataEngine : public Plasma::DataEngine
{
    Q_OBJECT

    public:
        TimekprDataEngine(QObject* parent, const QVariantList& args);
	QStringList sources() const;
	
    protected:
        bool sourceRequestEvent(const QString& name);
        bool updateSourceEvent(const QString& source);
    private:
	void init();
	QStringList parseVector(QString vector);
	QStringList m_users;
	QStringList m_keys;
	KSharedConfigPtr m_config;
};

#endif //TIMEKPRDATAENGINE_H
