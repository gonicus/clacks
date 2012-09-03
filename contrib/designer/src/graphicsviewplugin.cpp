#include "graphicsview.h"
#include "graphicsviewplugin.h"

#include <QtCore/QtPlugin>

GraphicsViewPlugin::GraphicsViewPlugin(QObject *parent)
    : QObject(parent)
{
    m_initialized = false;
}

void GraphicsViewPlugin::initialize(QDesignerFormEditorInterface * /* core */)
{
    if (m_initialized)
        return;

    // Add extension registrations, etc. here

    m_initialized = true;
}

bool GraphicsViewPlugin::isInitialized() const
{
    return m_initialized;
}

QWidget *GraphicsViewPlugin::createWidget(QWidget *parent)
{
    return new GraphicsView(parent);
}

QString GraphicsViewPlugin::name() const
{
    return QLatin1String("GraphicsView");
}

QString GraphicsViewPlugin::group() const
{
    return QLatin1String("GOsa");
}

QIcon GraphicsViewPlugin::icon() const
{
    return QIcon(QLatin1String(":/graphicsview.png"));
}

QString GraphicsViewPlugin::toolTip() const
{
    return QLatin1String("");
}

QString GraphicsViewPlugin::whatsThis() const
{
    return QLatin1String("");
}

bool GraphicsViewPlugin::isContainer() const
{
    return false;
}

QString GraphicsViewPlugin::domXml() const
{
    return QLatin1String("<widget class=\"GraphicsView\" name=\"graphicsView\">\n</widget>\n");
}

QString GraphicsViewPlugin::includeFile() const
{
    return QLatin1String("graphicsview.h");
}

