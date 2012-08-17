#ifndef DATEEDIT_H
#define DATEEDIT_H

#include <QtGui/QDateEdit>

class DateEdit : public QDateEdit
{
    Q_OBJECT

public:
    DateEdit(QWidget *parent = 0);
};

#endif
