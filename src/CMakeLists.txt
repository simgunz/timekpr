project(kcm_timekpr)
add_subdirectory (helper)
find_package( KDE4 REQUIRED )
include(KDE4Defaults)
include(FindPythonLibrary)
include(FindPyQt4)
include(FindPyKDE4)

install(FILES kcm_timekpr.py DESTINATION ${DATA_INSTALL_DIR}/kcm_timekpr)
install(FILES ui/main.ui ui/status.ui ui/grant.ui ui/limits.ui DESTINATION ${DATA_INSTALL_DIR}/kcm_timekpr/ui)

#kde4_install_icons(${ICON_INSTALL_DIR})
install(FILES kcm_timekpr.desktop DESTINATION ${SERVICES_INSTALL_DIR})