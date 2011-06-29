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

    Plasma::ToolTipContent tooltip("Main text", "SubText", KIcon("timekpr"));
    Plasma::ToolTipManager::self()->setContent(this, tooltip);
    
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
