/***************************************************************************
 *   Copyright (C) 2010 by Simone Gaiarin <simgunz@gmail.com>                            *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program; if not, write to the                         *
 *   Free Software Foundation, Inc.,                                       *
 *   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA .        *
 ***************************************************************************/

// Here we avoid loading the header multiple times
#ifndef TIMEKPRAPPLET_H
#define TIMEKPRAPPLET_H

#include <KIcon>
// We need the Plasma Applet headers
#include <Plasma/Applet>
#include <Plasma/PopupApplet>
#include <Plasma/DataEngine>
#include <Plasma/Svg>
#include <KCModuleProxy>
#include <Plasma/ToolTipContent>

#include <QTimer>
#include <QElapsedTimer>


class QSizeF;

// Define our plasma Applet
class TimekprApplet : public Plasma::PopupApplet
{
    Q_OBJECT
public:
    // Basic Create/Destroy
    TimekprApplet(QObject *parent, const QVariantList &args);
    ~TimekprApplet();

    // The paintInterface procedure paints the applet to the desktop
   // void paintInterface(QPainter *painter, const QStyleOptionGraphicsItem *option,
                       // const QRect& contentsRect);
    void init();

public Q_SLOTS:
    void toolTipAboutToShow();
    void toolTipHidden();
    void updateTooltip();
    void dataUpdated(const QString &sourceName, const Plasma::DataEngine::Data &data);
protected:
    void initExtenderItem(Plasma::ExtenderItem *item);
    void createConfigurationInterface(KConfigDialog *parent);
private:
    Plasma::DataEngine *m_dataengine;
    Plasma::ToolTipContent m_tooltip;
    KIcon m_icon;
    QString m_user;
    QTimer m_tooltiptimer;
    QElapsedTimer m_timeelapsed;
    int m_timelimit;
    Plasma::Svg m_theme;
    KCModuleProxy *m_timekprSettingsWidget;
};

#endif
