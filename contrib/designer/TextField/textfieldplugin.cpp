#include "textfield.h"
#include "textfieldplugin.h"

#include <QtPlugin>

TextFieldPlugin::TextFieldPlugin(QObject *parent)
    : QObject(parent)
{
    m_initialized = false;
}

void TextFieldPlugin::initialize(QDesignerFormEditorInterface * /* core */)
{
    if (m_initialized)
        return;
    
    m_initialized = true;
}

bool TextFieldPlugin::isInitialized() const
{
    return m_initialized;
}

QLineEdit *TextFieldPlugin::createWidget(QWidget *parent)
{
    return new TextField(parent);
}

QString TextFieldPlugin::name() const
{
    return QLatin1String("TextField");
}

QString TextFieldPlugin::group() const
{
    return QLatin1String("Qooxdoo");
}

QIcon TextFieldPlugin::icon() const
{
    return QIcon(":/textfield.png");
}

QString TextFieldPlugin::toolTip() const
{
    return QLatin1String("Single line text field");
}

QString TextFieldPlugin::whatsThis() const
{
    return QLatin1String("");
}

bool TextFieldPlugin::isContainer() const
{
    return false;
}

QString TextFieldPlugin::domXml() const
{
    return QLatin1String("<widget class=\"TextField\" name=\"textField\">\n</widget>\n");
}

QString TextFieldPlugin::includeFile() const
{
    return QLatin1String("textfield.h");
}

Q_EXPORT_PLUGIN2(textfieldplugin, TextFieldPlugin)
