#include "checkboxplugin.h"
#include "comboboxplugin.h"
#include "dateeditplugin.h"
#include "gosaframeplugin.h"
#include "graphicsviewplugin.h"
#include "labelplugin.h"
#include "lineeditplugin.h"
#include "plaintexteditplugin.h"
#include "spinboxplugin.h"
#include "tableplugin.h"
#include "groupboxplugin.h"
#include "gosa.h"

GOsa::GOsa(QObject *parent)
        : QObject(parent)
{
    m_widgets.append(new CheckBoxPlugin(this));
    m_widgets.append(new ComboBoxPlugin(this));
    m_widgets.append(new DateEditPlugin(this));
    m_widgets.append(new GOsaFramePlugin(this));
    m_widgets.append(new GraphicsViewPlugin(this));
    m_widgets.append(new LabelPlugin(this));
    m_widgets.append(new LineEditPlugin(this));
    m_widgets.append(new PlainTextEditPlugin(this));
    m_widgets.append(new SpinBoxPlugin(this));
    m_widgets.append(new TablePlugin(this));
    m_widgets.append(new GroupBoxPlugin(this));

}

QList<QDesignerCustomWidgetInterface*> GOsa::customWidgets() const
{
    return m_widgets;
}

Q_EXPORT_PLUGIN2(gosaplugin, GOsa)
