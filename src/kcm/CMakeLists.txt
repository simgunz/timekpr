add_subdirectory (helper)

install(FILES kcm_timekpr.py DESTINATION ${DATA_INSTALL_DIR}/kcm_timekpr)
install(FILES ui/main.ui ui/status.ui ui/grant.ui ui/limits.ui DESTINATION ${DATA_INSTALL_DIR}/kcm_timekpr/ui)
install(FILES kcm_timekpr.desktop DESTINATION ${SERVICES_INSTALL_DIR})