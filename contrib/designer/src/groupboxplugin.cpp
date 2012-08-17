#include "groupbox.h"
#include "groupboxplugin.h"

#include <QtCore/QtPlugin>

GroupBoxPlugin::GroupBoxPlugin(QObject *parent)
    : QObject(parent)
{
    m_initialized = false;
}

void GroupBoxPlugin::initialize(QDesignerFormEditorInterface * /* core */)
{
    if (m_initialized)
        return;

    // Add extension registrations, etc. here

    m_initialized = true;
}

bool GroupBoxPlugin::isInitialized() const
{
    return m_initialized;
}

QWidget *GroupBoxPlugin::createWidget(QWidget *parent)
{
    return new GroupBox(parent);
}

QString GroupBoxPlugin::name() const
{
    return QLatin1String("GroupBox");
}

QString GroupBoxPlugin::group() const
{
    return QLatin1String("GOsa");
}

QIcon GroupBoxPlugin::icon() const
{
    return QIcon(QLatin1String(":/groupbox.png"));
}

QString GroupBoxPlugin::toolTip() const
{
    return QLatin1String("");
}

QString GroupBoxPlugin::whatsThis() const
{
    return QLatin1String("");
}

bool GroupBoxPlugin::isContainer() const
{
    return false;
}

QString GroupBoxPlugin::domXml() const
{
    return QLatin1String("<widget class=\"GroupBox\" name=\"groupBox\">\n</widget>\n");
}

QString GroupBoxPlugin::includeFile() const
{
    return QLatin1String("groupbox.h");
}

