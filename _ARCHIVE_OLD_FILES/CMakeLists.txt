cmake_minimum_required(VERSION 3.15)
project(PhazeVPN VERSION 1.0.0 LANGUAGES C CXX Go)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Build options
option(BUILD_PROTOCOL_GO "Build Go-based protocol server" ON)
option(BUILD_WEB_PORTAL "Build web portal service" ON)
option(BUILD_PROTOCOL_PYTHON "Build Python protocol service" ON)
option(BUILD_BROWSER "Build PhazeBrowser" ON)
option(INSTALL_SYSTEMD_SERVICES "Install systemd service files" ON)
option(INSTALL_TO_SYSTEM "Install to system directories" OFF)

# Installation directories
# Default VPS installation path
if(INSTALL_TO_SYSTEM)
    set(CMAKE_INSTALL_PREFIX "/opt/phaze-vpn")
    set(SYSTEMD_DIR "/etc/systemd/system")
    # Also support /opt/secure-vpn for backward compatibility
    if(EXISTS "/opt/secure-vpn" AND NOT EXISTS "/opt/phaze-vpn")
        set(CMAKE_INSTALL_PREFIX "/opt/secure-vpn")
    endif()
else()
    set(CMAKE_INSTALL_PREFIX "${CMAKE_BINARY_DIR}/install")
    set(SYSTEMD_DIR "${CMAKE_BINARY_DIR}/systemd")
endif()
set(INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX})

# Output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# Find required programs
find_program(PYTHON3_EXECUTABLE python3 REQUIRED)
find_program(GO_EXECUTABLE go)
find_program(GUNICORN_EXECUTABLE gunicorn)
find_program(SYSTEMCTL_EXECUTABLE systemctl)

# Check for Go if building protocol server
if(BUILD_PROTOCOL_GO)
    if(NOT GO_EXECUTABLE)
        message(WARNING "Go not found. Protocol Go server will not be built.")
        set(BUILD_PROTOCOL_GO OFF)
    endif()
endif()

# Include subdirectories
if(BUILD_PROTOCOL_GO)
    add_subdirectory(phazevpn-protocol-go)
endif()

if(BUILD_WEB_PORTAL)
    add_subdirectory(web-portal)
endif()

if(BUILD_PROTOCOL_PYTHON)
    add_subdirectory(phazevpn-protocol)
endif()

if(BUILD_BROWSER)
    if(EXISTS ${CMAKE_SOURCE_DIR}/browser/CMakeLists.txt)
        add_subdirectory(browser)
    else()
        message(WARNING "Browser CMakeLists.txt not found, skipping browser build")
    endif()
endif()

# Include CMake modules
list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")

# Create systemd service files
if(INSTALL_SYSTEMD_SERVICES)
    include(SystemdService)
    
    if(BUILD_WEB_PORTAL)
        create_systemd_service(
            phazevpn-portal
            "PhazeVPN Web Portal (Gunicorn)"
            "${INSTALL_PREFIX}/web-portal"
            "${GUNICORN_EXECUTABLE} --workers 4 --bind 127.0.0.1:5000 --timeout 120 --access-logfile /var/log/phazevpn-portal-access.log --error-logfile /var/log/phazevpn-portal-error.log app:app"
            "www-data"
            "www-data"
        )
    endif()
    
    if(BUILD_PROTOCOL_PYTHON)
        create_systemd_service(
            phazevpn-protocol
            "PhazeVPN Protocol Server - Custom VPN Implementation"
            "${INSTALL_PREFIX}/phazevpn-protocol"
            "${PYTHON3_EXECUTABLE} phazevpn-server-production.py"
            "root"
            "root"
        )
    endif()
    
    if(BUILD_PROTOCOL_GO)
        create_systemd_service(
            phazevpn-protocol-go
            "PhazeVPN Protocol Server (Go)"
            "${INSTALL_PREFIX}/phazevpn-protocol-go"
            "${INSTALL_PREFIX}/phazevpn-protocol-go/phazevpn-server-go"
            "root"
            "root"
        )
    endif()
endif()

# Installation - CRITICAL COMMERCIAL FILES
install(DIRECTORY config/ DESTINATION ${INSTALL_PREFIX}/config
    FILES_MATCHING PATTERN "*.conf"
)
install(DIRECTORY certs/ DESTINATION ${INSTALL_PREFIX}/certs
    FILES_MATCHING PATTERN "*"
)
install(DIRECTORY client-configs/ DESTINATION ${INSTALL_PREFIX}/client-configs
    FILES_MATCHING PATTERN "*.ovpn"
)

# CRITICAL: Install subscription manager and payment files
install(FILES 
    ${CMAKE_SOURCE_DIR}/subscription-manager.py
    DESTINATION ${INSTALL_PREFIX}
    OPTIONAL
)

# Install VPN management scripts
install(FILES 
    ${CMAKE_SOURCE_DIR}/vpn-manager.py
    ${CMAKE_SOURCE_DIR}/vpn-gui.py
    DESTINATION ${INSTALL_PREFIX}
    PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
    OPTIONAL
)

# Create data directories for commercial features
install(CODE "
    file(MAKE_DIRECTORY \${CMAKE_INSTALL_PREFIX}/logs)
    file(MAKE_DIRECTORY \${CMAKE_INSTALL_PREFIX}/data)
")

# Print summary
message(STATUS "")
message(STATUS "=== PhazeVPN Build Configuration ===")
message(STATUS "Build Protocol Go: ${BUILD_PROTOCOL_GO}")
message(STATUS "Build Web Portal: ${BUILD_WEB_PORTAL}")
message(STATUS "Build Protocol Python: ${BUILD_PROTOCOL_PYTHON}")
message(STATUS "Build Browser: ${BUILD_BROWSER}")
message(STATUS "Install Systemd Services: ${INSTALL_SYSTEMD_SERVICES}")
message(STATUS "Install Prefix: ${INSTALL_PREFIX}")
message(STATUS "====================================")
message(STATUS "")

