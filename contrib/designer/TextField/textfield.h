#ifndef TEXTFIELD_H
#define TEXTFIELD_H

#include <QLineEdit>
#include <QWidget>

class TextField : public QLineEdit
{
    Q_OBJECT
    Q_PROPERTY(QList<QString> Actions READ getActions WRITE setActions)
    Q_PROPERTY(int test READ getTest WRITE setTest)

  public:
    TextField(QWidget *parent = 0);
    QList<QString> getActions () const;
    int getTest () const;

  public slots:
    void setActions (const QList<QString> &actions);
    void setTest (const int test);

  private:
    QList<QString> actions;
    int test;

  signals:
    void actionsChanged(const QList<QString> &actions);
    void testChanged(const int test);

};

#endif
