#include "textfield.h"

TextField::TextField(QWidget *parent) :
    QLineEdit(parent)
{
}

void TextField::setActions(const QList<QString> &actions)
{
  this->actions = actions;
  emit this->actionsChanged(actions);
}

QList<QString> TextField::getActions() const
{
  return this->actions;
}

void TextField::setTest(const int test)
{
  this->test = test;
  emit this->testChanged(test);
}

int TextField::getTest() const
{
  return this->test;
}
