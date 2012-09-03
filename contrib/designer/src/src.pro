CONFIG      += designer plugin
TARGET      = $$qtLibraryTarget(gosaplugin)
TEMPLATE    = lib

HEADERS     = checkboxplugin.h comboboxplugin.h dateeditplugin.h gosaframeplugin.h graphicsviewplugin.h labelplugin.h lineeditplugin.h plaintexteditplugin.h spinboxplugin.h tableplugin.h groupboxplugin.h gosa.h
SOURCES     = checkboxplugin.cpp comboboxplugin.cpp dateeditplugin.cpp gosaframeplugin.cpp graphicsviewplugin.cpp labelplugin.cpp lineeditplugin.cpp plaintexteditplugin.cpp spinboxplugin.cpp tableplugin.cpp groupboxplugin.cpp gosa.cpp
RESOURCES   = icons.qrc
LIBS        += -L. 

target.path = $$[QT_INSTALL_PLUGINS]/designer
INSTALLS    += target

include(plaintextedit.pri)
include(label.pri)
include(combobox.pri)
include(gosaframe.pri)
include(checkbox.pri)
include(spinbox.pri)
include(lineedit.pri)
include(groupbox.pri)
include(dateedit.pri)
include(graphicsview.pri)
include(table.pri)
