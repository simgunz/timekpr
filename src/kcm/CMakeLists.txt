add_subdirectory (helper)
PYKDE4_INSTALL_PYTHON_FILES(kcm_timekpr.py)
install(DIRECTORY ui/ DESTINATION ${DATA_INSTALL_DIR}/timekpr-kde/ui)
install(FILES kcm_timekpr.desktop DESTINATION ${SERVICES_INSTALL_DIR})