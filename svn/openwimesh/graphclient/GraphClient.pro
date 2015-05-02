TEMPLATE = app
CONFIG += console
CONFIG -= app_bundle
CONFIG -= qt
TARGET = GraphClient

SOURCES += \
    src/arpInfo.c \
    src/graphClient.c \
    src/associations.c \
    src/paramprocess.c

HEADERS += \
    src/arpInfo.h \
#    src/version.h \
    src/associations.h \
    src/paramprocess.h

LIBS += -lnl-3 -lnl-genl-3

QMAKE_CFLAGS += -Wno-unused-parameter -Wno-unused-but-set-variable -I/usr/include/libnl3

# Creating the version file based on git's version information
#VERSION_GIT  = $$system(sh -c 'cd .. ; git describe --abbrev=4 --dirty --always')
#message($$VERSION_GIT)
#VERSION_FILE = $${PWD}/src/version.h
#message($$VERSION_FILE)
#VERSION_DEFINE = "echo \"$${LITERAL_HASH}define GIT_VERSION $${VERSION_GIT}\" > $${VERSION_FILE}"
#message ($$VERSION_DEFINE)
#system($$VERSION_DEFINE)
