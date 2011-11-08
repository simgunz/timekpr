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

#include "timekprapplet.h"

//QT
#include <QPainter>
#include <QFontMetrics>
#include <QSizeF>

//Plasma
#include <plasma/svg.h>
#include <plasma/theme.h>
#include <Plasma/DataEngine>
#include <Plasma/Extender>
#include <Plasma/ExtenderItem>
#include <Plasma/TextBrowser>
#include <Plasma/Label>
#include <Plasma/ToolTipContent>
#include <Plasma/ToolTipManager>

//KDE
#include <KLocale>
#include <KGlobal>
#include <KStandardDirs>
#include <KNotification>
#include <KCModuleInfo>
#include <KConfigDialog>
#include <KCModuleProxy>

#include <QDebug>
#include <QTimer>
#include <QTime>

TimekprApplet::TimekprApplet(QObject *parent, const QVariantList &args)
    : Plasma::PopupApplet(parent, args),
    m_theme(this),
    m_icon("timekpr")
{
    // this will get us the standard applet background, for free!
    setBackgroundHints(StandardBackground);
    setAspectRatioMode(Plasma::ConstrainedSquare );
    setHasConfigurationInterface(true);  
    setPopupIcon(m_icon);
    //resize(200, 200);
    //resize(graphicsWidget()->minimumSize());

    m_theme.setImagePath("widgets/battery-oxygen");
    m_theme.setContainsMultipleImages(true);
}


TimekprApplet::~TimekprApplet()
{
    if (hasFailedToLaunch()) {
        // Do some cleanup here
    } else {
        // Save settings
    }
}

void TimekprApplet::init()
{
    // A small demonstration of the setFailedToLaunch function
    m_user = getenv("USER");
    m_dataengine = dataEngine("timekpr");
    extender()->setEmptyExtenderMessage(i18n("Timekpr not running..."));
    if (m_icon.isNull()) {
        setFailedToLaunch(true, i18n("No world to say hello"));
    }

    if (!extender()->hasItem("InfoProvider"))
    {
	Plasma::ExtenderItem *eItem = new Plasma::ExtenderItem(extender());
	eItem->setName("InfoProvider");
	eItem->setTitle("InfoProvider");
	initExtenderItem(eItem);
    }

    m_tooltip.setMainText("Time left for user " + m_user);
    m_tooltip.setImage(KIcon("timekpr"));
    m_tooltip.setAutohide(true);
    Plasma::ToolTipManager::self()->setContent(this,m_tooltip);
    
    
    m_tooltiptimer.setInterval(1000);
    connect(&m_tooltiptimer, SIGNAL(timeout()), this, SLOT(updateTooltip()));
    
    //Plasma::DataEngine::Data data = m_dataengine->query(m_user);
    m_dataengine->connectSource(m_user,this);
}

void TimekprApplet::dataUpdated(const QString &sourceName, const Plasma::DataEngine::Data &data)
{
    m_timelimit = data["time_left"].toInt();
    m_timeelapsed.restart();
}

void TimekprApplet::createConfigurationInterface(KConfigDialog *parent)
{
    m_timekprSettingsWidget = new KCModuleProxy("kcm_timekpr");

    parent->addPage(m_timekprSettingsWidget, m_timekprSettingsWidget->moduleInfo().moduleName(),
                    m_timekprSettingsWidget->moduleInfo().icon());

    //parent->setButtons( KDialog::Ok | KDialog::Cancel);
    //connect(parent, SIGNAL(okClicked()), this, SLOT(configAccepted()));
}

void TimekprApplet::toolTipAboutToShow()
{
    //KNotification::event(KNotification::Notification, "Titolo","Tempo scaduto", KIcon("timekpr_kde").pixmap(QSize(32,32)));
    //KNotification::event(KNotification::Catastrophe, "Titolo","Tempo scaduto", KIcon("timekpr_kde").pixmap(QSize(32,32)));    
    updateTooltip();
    m_tooltiptimer.start();
}

void TimekprApplet::toolTipHidden()
{
    m_tooltiptimer.stop();
    //m_timeleft = 0;
}

void TimekprApplet::updateTooltip()
{
    QTime timeleft(0,0,0);
    timeleft = timeleft.addSecs(m_timelimit - m_timeelapsed.elapsed()/1000);
    /*int tleft = m_timeleft%3600;
    int hr = tleft/3600;
    tleft%=3600;
    int mn=tleft/60;
    int ss=tleft%60;
    QString hour, minute, second;
    hour.append(QString("%1").arg(hr));
    minute.append(QString("%1").arg(mn));
    second.append(QString("%1").arg(ss));
    m_timeleft--;*/
    m_tooltip.setSubText("<div style=\"margin-top: 5px\" align=\"center\">" + timeleft.toString("hh:mm:ss") + "</div>");
    Plasma::ToolTipManager::self()->setContent(this, m_tooltip);
}

void TimekprApplet::initExtenderItem(Plasma::ExtenderItem *item)
{
    //Create a Meter widget and wrap it in the ExtenderItem

    Plasma::Label *label = new Plasma::Label();
    label->setText("TestO");
    label->setAlignment(Qt::AlignHCenter);
    label->setMinimumSize(QSizeF(80, 80));

    //often, you'll want to connect dataengines or set properties
    //depending on information contained in item->config().
    //In this situation that won't be necessary though.
    item->setWidget(label);

    //Job names are not unique across plasma restarts (kuiserver
    //engine just starts with Job1 again), so avoid problems and
    //just don't give reinstantiated items a name.
    item->setName("Primo extenderItem");

    //Show a close button.
    //item->showCloseButton();
}
//void TimekprApplet::paintInterface(QPainter *p, const QStyleOptionGraphicsItem *option, const QRect &contentsRect)
//{
//    m_theme.paint(p, contentsRect, "Battery");
//    m_theme.paint(p, contentsRect, "Fill80");
//    Q_UNUSED( option );

//}

// This is the command that links your applet to the .desktop file
K_EXPORT_PLASMA_APPLET(timekpr, TimekprApplet)

#include "timekprapplet.moc"
