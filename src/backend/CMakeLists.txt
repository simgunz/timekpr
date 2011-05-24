install(DIRECTORY python-support/ DESTINATION /usr/share/python-support/timekpr)
install(DIRECTORY etc/ DESTINATION ${CONFIG_INSTALL_DIR})
install(PROGRAMS bin/timekpr bin/timekpr.postinst bin/timekpr.postrm DESTINATION ${BIN_INSTALL_DIR})
install(PROGRAMS bin/timekprd DESTINATION /etc/rc.d/)
