set(SRCFILES timekprpam.py timekprcommon.py)

PYKDE4_INSTALL_PYTHON_FILES(${SRCFILES})

install(DIRECTORY etc/ DESTINATION ${SYSCONF_INSTALL_DIR})
install(FILES timekpr.py DESTINATION ${DATA_INSTALL_DIR}/timekpr)
install(PROGRAMS bin/timekprd DESTINATION ${SYSCONF_INSTALL_DIR}/rc.d/)

PYKDE4_ADD_EXECUTABLE(timekpr.py timekpr)