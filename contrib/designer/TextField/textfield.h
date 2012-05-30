#ifndef TEXTFIELD_H
#define TEXTFIELD_H

#include <QLineEdit>
#include <QWidget>

class TextField : public QLineEdit
{
    Q_OBJECT
    
public:
    TextField(QWidget *parent = 0);
};

#endif
