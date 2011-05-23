include_directories( ${KDE4_INCLUDES} )
 
kde4_add_executable( kcmtimekprhelper helper.cpp )
target_link_libraries( kcmtimekprhelper ${KDE4_KDECORE_LIBS} )
install(TARGETS kcmtimekprhelper DESTINATION ${LIBEXEC_INSTALL_DIR})
kde4_install_auth_helper_files(kcmtimekprhelper org.kde.kcontrol.kcmtimekpr root)
kde4_install_auth_actions(org.kde.kcontrol.kcmtimekpr kcm_timekpr.actions)

