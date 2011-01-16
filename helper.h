#ifndef KDM_HELPER_H
#define KDM_HELPER_H

#include <kauth.h>

using namespace KAuth;

class Helper : public QObject {
    Q_OBJECT

public slots:
    ActionReply save(const QVariantMap &map);

};

#endif
