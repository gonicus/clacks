#include "lineedit.h"
#include "lineeditplugin.h"

#include <QtCore/QtPlugin>

LineEditPlugin::LineEditPlugin(QObject *parent)
    : QObject(parent)
{
    m_initialized = false;
}

void LineEditPlugin::initialize(QDesignerFormEditorInterface * /* core */)
{
    if (m_initialized)
        return;

    // Add extension registrations, etc. here

    m_initialized = true;
}

bool LineEditPlugin::isInitialized() const
{
    return m_initialized;
}

QWidget *LineEditPlugin::createWidget(QWidget *parent)
{
    return new LineEdit(parent);
}

QString LineEditPlugin::name() const
{
    return QLatin1String("LineEdit");
}

QString LineEditPlugin::group() const
{
    return QLatin1String("GOsa");
}

QIcon LineEditPlugin::icon() const
{
    return QIcon(QLatin1String(":/lineedit.png"));
}

QString LineEditPlugin::toolTip() const
{
    return QLatin1String("");
}

QString LineEditPlugin::whatsThis() const
{
    return QLatin1String("");
}

bool LineEditPlugin::isContainer() const
{
    return false;
}

QString LineEditPlugin::domXml() const
{
    return QLatin1String("<widget class=\"LineEdit\" name=\"lineEdit\">\n</widget>\n");
}

QString LineEditPlugin::includeFile() const
{
    return QLatin1String("lineedit.h");
}

