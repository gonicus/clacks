#ifndef TABLE_H
#define TABLE_H

#include <QtGui/QTableWidget>

class Table : public QTableWidget
{
    Q_OBJECT

public:
    Table(QWidget *parent = 0);
};

#endif
