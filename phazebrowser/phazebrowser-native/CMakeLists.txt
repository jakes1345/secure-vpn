cmake_minimum_required(VERSION 3.16)
project(PhazeBrowser VERSION 2.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Qt6
find_package(Qt6 REQUIRED COMPONENTS Core Widgets WebEngineWidgets WebEngineCore Network)

# Enable automatic MOC, UIC, RCC
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

# Source files
set(SOURCES
    src/main.cpp
    src/mainwindow.cpp
    src/browserwindow.cpp
    src/vpnmanager.cpp
    src/privacyengine.cpp
    src/datamanager.cpp
    src/downloadmanager.cpp
    src/searchmanager.cpp
    src/devtools.cpp
    src/faviconmanager.cpp
    src/downloaddialog.cpp
    src/settingsdialog.cpp
    src/privacydashboard.cpp
    src/passworddialog.cpp
    src/bookmarksdialog.cpp
    src/historydialog.cpp
)

set(HEADERS
    src/mainwindow.h
    src/browserwindow.h
    src/vpnmanager.h
    src/privacyengine.h
    src/datamanager.h
    src/downloadmanager.h
    src/searchmanager.h
    src/devtools.h
    src/faviconmanager.h
    src/downloaddialog.h
    src/settingsdialog.h
    src/privacydashboard.h
    src/passworddialog.h
    src/bookmarksdialog.h
    src/historydialog.h
)

# Create executable (no UI files or resources - everything is programmatic)
add_executable(phazebrowser ${SOURCES} ${HEADERS})

# Link Qt libraries
# Note: QJson classes (QJsonArray, QJsonObject, etc.) are part of Qt6::Core
target_link_libraries(phazebrowser
    Qt6::Core
    Qt6::Widgets
    Qt6::WebEngineWidgets
    Qt6::WebEngineCore
    Qt6::Network
)

# Install
install(TARGETS phazebrowser DESTINATION bin)

# Desktop entry
install(FILES phazebrowser.desktop DESTINATION share/applications)
