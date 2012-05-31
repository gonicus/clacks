CONFIG      += designer plugin debug_and_release
TARGET      = $$qtLibraryTarget(textfieldplugin)
TEMPLATE    = lib

HEADERS     = textfieldplugin.h
SOURCES     = textfieldplugin.cpp
RESOURCES   = icons.qrc
LIBS        += -L. 

target.path = $$[QT_INSTALL_PLUGINS]/designer
INSTALLS    += target

include(textfield.pri)
