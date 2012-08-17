#include "spinbox.h"
#include "spinboxplugin.h"

#include <QtCore/QtPlugin>

SpinBoxPlugin::SpinBoxPlugin(QObject *parent)
    : QObject(parent)
{
    m_initialized = false;
}

void SpinBoxPlugin::initialize(QDesignerFormEditorInterface * /* core */)
{
    if (m_initialized)
        return;

    // Add extension registrations, etc. here

    m_initialized = true;
}

bool SpinBoxPlugin::isInitialized() const
{
    return m_initialized;
}

QWidget *SpinBoxPlugin::createWidget(QWidget *parent)
{
    return new SpinBox(parent);
}

QString SpinBoxPlugin::name() const
{
    return QLatin1String("SpinBox");
}

QString SpinBoxPlugin::group() const
{
    return QLatin1String("GOsa");
}

QIcon SpinBoxPlugin::icon() const
{
    return QIcon(QLatin1String(":/spinbox.png"));
}

QString SpinBoxPlugin::toolTip() const
{
    return QLatin1String("");
}

QString SpinBoxPlugin::whatsThis() const
{
    return QLatin1String("");
}

bool SpinBoxPlugin::isContainer() const
{
    return false;
}

QString SpinBoxPlugin::domXml() const
{
    return QLatin1String("<widget class=\"SpinBox\" name=\"spinBox\">\n</widget>\n");
}

QString SpinBoxPlugin::includeFile() const
{
    return QLatin1String("spinbox.h");
}

