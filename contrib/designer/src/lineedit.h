#ifndef LINEEDIT_H
#define LINEEDIT_H

#include <QtGui/QLineEdit>

class LineEdit : public QLineEdit
{
    Q_OBJECT

public:
    LineEdit(QWidget *parent = 0);
};

#endif
