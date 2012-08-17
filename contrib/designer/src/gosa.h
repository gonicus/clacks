#ifndef GOSA_H
#define GOSA_H

#include <QtDesigner/QtDesigner>
#include <QtCore/qplugin.h>

class GOsa : public QObject, public QDesignerCustomWidgetCollectionInterface
{
    Q_OBJECT
    Q_INTERFACES(QDesignerCustomWidgetCollectionInterface)

public:
    explicit GOsa(QObject *parent = 0);

    virtual QList<QDesignerCustomWidgetInterface*> customWidgets() const;

private:
    QList<QDesignerCustomWidgetInterface*> m_widgets;
};

#endif
