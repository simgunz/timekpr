 
#ifndef TIMEKPRDATAENGINE_H
#define TIMEKPRDATAENGINE_H

#include <Plasma/DataEngine>
#include <KSharedConfigPtr>
#include <KSharedConfig>
#include <KConfigGroup>

#include <QStringList>
#include <QDate>
#include <QFile>
#include <QFileSystemWatcher>
class TimekprDataEngine : public Plasma::DataEngine
{
    Q_OBJECT

    public:
        TimekprDataEngine(QObject* parent, const QVariantList& args);
	QStringList sources() const;
    protected Q_SLOTS:
	bool updateSourceEvent(const QString& source);
    protected:
        bool sourceRequestEvent(const QString& name);
    private:
	void init();
	QStringList parseVector(QString vector);
	QStringList m_users;
	QStringList m_keys;
	KSharedConfigPtr m_config;
	QFileSystemWatcher m_watcher;
};

#endif //TIMEKPRDATAENGINE_H
