project(timekpr)

find_package(KDE4 REQUIRED)
include(KDE4Defaults)
include(FindPythonLibrary)
include(FindPyQt4)
include(FindPyKDE4)

add_subdirectory (backend)
add_subdirectory (kcm)
add_subdirectory (plasma-applet)
add_subdirectory (plasma-dataengine)
add_subdirectory (icons)

