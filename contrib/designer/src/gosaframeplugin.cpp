#include "gosaframe.h"
#include "gosaframeplugin.h"

#include <QtCore/QtPlugin>

GOsaFramePlugin::GOsaFramePlugin(QObject *parent)
    : QObject(parent)
{
    m_initialized = false;
}

void GOsaFramePlugin::initialize(QDesignerFormEditorInterface * /* core */)
{
    if (m_initialized)
        return;

    // Add extension registrations, etc. here

    m_initialized = true;
}

bool GOsaFramePlugin::isInitialized() const
{
    return m_initialized;
}

QWidget *GOsaFramePlugin::createWidget(QWidget *parent)
{
    return new GOsaFrame(parent);
}

QString GOsaFramePlugin::name() const
{
    return QLatin1String("GOsaFrame");
}

QString GOsaFramePlugin::group() const
{
    return QLatin1String("GOsa");
}

QIcon GOsaFramePlugin::icon() const
{
    return QIcon(QLatin1String(":/widget.png"));
}

QString GOsaFramePlugin::toolTip() const
{
    return QLatin1String("");
}

QString GOsaFramePlugin::whatsThis() const
{
    return QLatin1String("");
}

bool GOsaFramePlugin::isContainer() const
{
    return false;
}

QString GOsaFramePlugin::domXml() const
{
    return QLatin1String("<widget class=\"GOsaFrame\" name=\"gOsaFrame\">\n</widget>\n");
}

QString GOsaFramePlugin::includeFile() const
{
    return QLatin1String("gosaframe.h");
}

