#include "label.h"
#include "labelplugin.h"

#include <QtCore/QtPlugin>

LabelPlugin::LabelPlugin(QObject *parent)
    : QObject(parent)
{
    m_initialized = false;
}

void LabelPlugin::initialize(QDesignerFormEditorInterface * /* core */)
{
    if (m_initialized)
        return;

    // Add extension registrations, etc. here

    m_initialized = true;
}

bool LabelPlugin::isInitialized() const
{
    return m_initialized;
}

QWidget *LabelPlugin::createWidget(QWidget *parent)
{
    return new Label(parent);
}

QString LabelPlugin::name() const
{
    return QLatin1String("Label");
}

QString LabelPlugin::group() const
{
    return QLatin1String("GOsa");
}

QIcon LabelPlugin::icon() const
{
    return QIcon(QLatin1String(":/label.png"));
}

QString LabelPlugin::toolTip() const
{
    return QLatin1String("");
}

QString LabelPlugin::whatsThis() const
{
    return QLatin1String("");
}

bool LabelPlugin::isContainer() const
{
    return false;
}

QString LabelPlugin::domXml() const
{
    return QLatin1String("<widget class=\"Label\" name=\"label\">\n</widget>\n");
}

QString LabelPlugin::includeFile() const
{
    return QLatin1String("label.h");
}

