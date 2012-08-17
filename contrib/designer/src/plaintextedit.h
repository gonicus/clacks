#ifndef PLAINTEXTEDIT_H
#define PLAINTEXTEDIT_H

#include <QtGui/QPlainTextEdit>

class PlainTextEdit : public QPlainTextEdit
{
    Q_OBJECT

public:
    PlainTextEdit(QWidget *parent = 0);
};

#endif
