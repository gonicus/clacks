#ifndef GRAPHICSVIEW_H
#define GRAPHICSVIEW_H

#include <QtGui/QGraphicsView>

class GraphicsView : public QGraphicsView
{
    Q_OBJECT

public:
    GraphicsView(QWidget *parent = 0);
};

#endif
