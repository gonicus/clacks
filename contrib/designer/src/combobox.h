#ifndef COMBOBOX_H
#define COMBOBOX_H

#include <QtGui/QComboBox>

class ComboBox : public QComboBox
{
    Q_OBJECT

public:
    ComboBox(QWidget *parent = 0);
};

#endif
