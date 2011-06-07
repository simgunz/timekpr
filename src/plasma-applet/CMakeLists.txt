add_definitions (${QT_DEFINITIONS} ${KDE4_DEFINITIONS})
include_directories(${CMAKE_SOURCE_DIR} ${CMAKE_BINARY_DIR} ${KDE4_INCLUDES})
 
# We add our source code here
set(timekprapplet_SRCS timekprapplet.cpp)
 
# Now make sure all files get to the right place
kde4_add_plugin(plasma_applet_timekpr ${timekprapplet_SRCS})
target_link_libraries(plasma_applet_timekpr ${KDE4_PLASMA_LIBS} ${KDE4_KDEUI_LIBS} ${KDE4_KCMUTILS_LIBRARY})
 
install(TARGETS plasma_applet_timekpr DESTINATION ${PLUGIN_INSTALL_DIR})
install(FILES plasma-applet-timekpr.desktop DESTINATION ${SERVICES_INSTALL_DIR})
