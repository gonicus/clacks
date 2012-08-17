#include "dateedit.h"
#include "dateeditplugin.h"

#include <QtCore/QtPlugin>

DateEditPlugin::DateEditPlugin(QObject *parent)
    : QObject(parent)
{
    m_initialized = false;
}

void DateEditPlugin::initialize(QDesignerFormEditorInterface * /* core */)
{
    if (m_initialized)
        return;

    // Add extension registrations, etc. here

    m_initialized = true;
}

bool DateEditPlugin::isInitialized() const
{
    return m_initialized;
}

QWidget *DateEditPlugin::createWidget(QWidget *parent)
{
    return new DateEdit(parent);
}

QString DateEditPlugin::name() const
{
    return QLatin1String("DateEdit");
}

QString DateEditPlugin::group() const
{
    return QLatin1String("GOsa");
}

QIcon DateEditPlugin::icon() const
{
    return QIcon(QLatin1String(":/dateedit.png"));
}

QString DateEditPlugin::toolTip() const
{
    return QLatin1String("");
}

QString DateEditPlugin::whatsThis() const
{
    return QLatin1String("");
}

bool DateEditPlugin::isContainer() const
{
    return false;
}

QString DateEditPlugin::domXml() const
{
    return QLatin1String("<widget class=\"DateEdit\" name=\"dateEdit\">\n</widget>\n");
}

QString DateEditPlugin::includeFile() const
{
    return QLatin1String("dateedit.h");
}

