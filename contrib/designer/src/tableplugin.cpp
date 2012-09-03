#include "table.h"
#include "tableplugin.h"

#include <QtCore/QtPlugin>

TablePlugin::TablePlugin(QObject *parent)
    : QObject(parent)
{
    m_initialized = false;
}

void TablePlugin::initialize(QDesignerFormEditorInterface * /* core */)
{
    if (m_initialized)
        return;

    // Add extension registrations, etc. here

    m_initialized = true;
}

bool TablePlugin::isInitialized() const
{
    return m_initialized;
}

QWidget *TablePlugin::createWidget(QWidget *parent)
{
    return new Table(parent);
}

QString TablePlugin::name() const
{
    return QLatin1String("Table");
}

QString TablePlugin::group() const
{
    return QLatin1String("GOsa");
}

QIcon TablePlugin::icon() const
{
    return QIcon(QLatin1String(":/table.png"));
}

QString TablePlugin::toolTip() const
{
    return QLatin1String("");
}

QString TablePlugin::whatsThis() const
{
    return QLatin1String("");
}

bool TablePlugin::isContainer() const
{
    return false;
}

QString TablePlugin::domXml() const
{
    return QLatin1String("<widget class=\"Table\" name=\"table\">\n</widget>\n");
}

QString TablePlugin::includeFile() const
{
    return QLatin1String("table.h");
}

