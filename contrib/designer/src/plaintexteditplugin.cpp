#include "plaintextedit.h"
#include "plaintexteditplugin.h"

#include <QtCore/QtPlugin>

PlainTextEditPlugin::PlainTextEditPlugin(QObject *parent)
    : QObject(parent)
{
    m_initialized = false;
}

void PlainTextEditPlugin::initialize(QDesignerFormEditorInterface * /* core */)
{
    if (m_initialized)
        return;

    // Add extension registrations, etc. here

    m_initialized = true;
}

bool PlainTextEditPlugin::isInitialized() const
{
    return m_initialized;
}

QWidget *PlainTextEditPlugin::createWidget(QWidget *parent)
{
    return new PlainTextEdit(parent);
}

QString PlainTextEditPlugin::name() const
{
    return QLatin1String("PlainTextEdit");
}

QString PlainTextEditPlugin::group() const
{
    return QLatin1String("GOsa");
}

QIcon PlainTextEditPlugin::icon() const
{
    return QIcon(QLatin1String(":/plaintextedit.png"));
}

QString PlainTextEditPlugin::toolTip() const
{
    return QLatin1String("");
}

QString PlainTextEditPlugin::whatsThis() const
{
    return QLatin1String("");
}

bool PlainTextEditPlugin::isContainer() const
{
    return false;
}

QString PlainTextEditPlugin::domXml() const
{
    return QLatin1String("<widget class=\"PlainTextEdit\" name=\"plainTextEdit\">\n</widget>\n");
}

QString PlainTextEditPlugin::includeFile() const
{
    return QLatin1String("plaintextedit.h");
}

