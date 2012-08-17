#ifndef CHECKBOX_H
#define CHECKBOX_H

#include <QtGui/QCheckBox>

class CheckBox : public QCheckBox
{
    Q_OBJECT

public:
    CheckBox(QWidget *parent = 0);
};

#endif
