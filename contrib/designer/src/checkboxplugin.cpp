#include "checkbox.h"
#include "checkboxplugin.h"

#include <QtCore/QtPlugin>

CheckBoxPlugin::CheckBoxPlugin(QObject *parent)
    : QObject(parent)
{
    m_initialized = false;
}

void CheckBoxPlugin::initialize(QDesignerFormEditorInterface * /* core */)
{
    if (m_initialized)
        return;

    // Add extension registrations, etc. here

    m_initialized = true;
}

bool CheckBoxPlugin::isInitialized() const
{
    return m_initialized;
}

QWidget *CheckBoxPlugin::createWidget(QWidget *parent)
{
    return new CheckBox(parent);
}

QString CheckBoxPlugin::name() const
{
    return QLatin1String("CheckBox");
}

QString CheckBoxPlugin::group() const
{
    return QLatin1String("GOsa");
}

QIcon CheckBoxPlugin::icon() const
{
    return QIcon(QLatin1String(":/checkbox.png"));
}

QString CheckBoxPlugin::toolTip() const
{
    return QLatin1String("");
}

QString CheckBoxPlugin::whatsThis() const
{
    return QLatin1String("");
}

bool CheckBoxPlugin::isContainer() const
{
    return false;
}

QString CheckBoxPlugin::domXml() const
{
    return QLatin1String("<widget class=\"CheckBox\" name=\"checkBox\">\n</widget>\n");
}

QString CheckBoxPlugin::includeFile() const
{
    return QLatin1String("checkbox.h");
}

