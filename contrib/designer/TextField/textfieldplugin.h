#ifndef TEXTFIELDPLUGIN_H
#define TEXTFIELDPLUGIN_H

#include <QDesignerCustomWidgetInterface>
#include <QLineEdit>

class TextFieldPlugin : public QObject, public QDesignerCustomWidgetInterface
{
    Q_OBJECT
    Q_INTERFACES(QDesignerCustomWidgetInterface)
    
public:
    TextFieldPlugin(QObject *parent = 0);
    
    bool isContainer() const;
    bool isInitialized() const;
    QIcon icon() const;
    QString domXml() const;
    QString group() const;
    QString includeFile() const;
    QString name() const;
    QString toolTip() const;
    QString whatsThis() const;
    QLineEdit *createWidget(QWidget *parent);
    void initialize(QDesignerFormEditorInterface *core);
    
private:
    bool m_initialized;
};

#endif
