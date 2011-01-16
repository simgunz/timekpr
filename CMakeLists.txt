PROJECT(timekprkde)

FIND_PACKAGE(Qt4 REQUIRED)
FIND_PACKAGE(KDE4 REQUIRED)
FIND_PACKAGE(PyQt4 REQUIRED)
FIND_PACKAGE(PyKDE4 REQUIRED)

#INSTALL(FILES README DESTINATION ${DATA_INSTALL_DIR}/timekpr-kde/root)

#INSTALL(FILES timekpr-kde.desktop DESTINATION ${SERVICES_INSTALL_DIR})

include(KDE4Defaults)
 
include_directories( ${KDE4_INCLUDES} )
 
kde4_add_executable( timekprkdehelper helper.cpp )
 
target_link_libraries( timekprkdehelper ${KDE4_KDEUI_LIBS} ${KDE4_KPARTS_LIBS} )

#kde4_add_executable(timekprkdehelper timekprkdehelper.cpp)

#install(FILES helper.py DESTINATION ${LIBEXEC_INSTALL_DIR})

#kde4_install_auth_actions(org.kde.kcontrol.timekprkde kcm_timekprkde.actions)

#kde4_install_auth_helper_files(timekprkdehelper org.kde.kcontrol.timekprkde root)