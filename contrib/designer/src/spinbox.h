#ifndef SPINBOX_H
#define SPINBOX_H

#include <QtGui/QSpinBox>

class SpinBox : public QSpinBox
{
    Q_OBJECT

public:
    SpinBox(QWidget *parent = 0);
};

#endif
