cmake_minimum_required(VERSION 3.15)

# PhazeBrowser build (Python/GTK)
find_program(PYTHON3_EXECUTABLE python3 REQUIRED)

# Browser dependencies
set(BROWSER_REQUIREMENTS ${CMAKE_SOURCE_DIR}/browser/requirements.txt)

# Check if requirements.txt exists, if not create one
if(NOT EXISTS ${BROWSER_REQUIREMENTS})
    file(WRITE ${BROWSER_REQUIREMENTS}
        "PyGObject>=3.42.0\n"
        "requests>=2.31.0\n"
    )
endif()

# Custom target to install browser dependencies
find_program(PIP_EXECUTABLE pip3)
if(PIP_EXECUTABLE)
    add_custom_target(browser-dependencies
        COMMAND ${PIP_EXECUTABLE} install -r ${BROWSER_REQUIREMENTS}
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        COMMENT "Installing browser Python dependencies"
        VERBATIM
    )
endif()

# Install browser files (phazebrowser.py is in root)
if(EXISTS ${CMAKE_SOURCE_DIR}/phazebrowser.py)
    install(FILES ${CMAKE_SOURCE_DIR}/phazebrowser.py
        DESTINATION ${CMAKE_INSTALL_PREFIX}/browser
        PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
    )
endif()

# Also check browser subdirectory
if(EXISTS ${CMAKE_SOURCE_DIR}/browser/phazebrowser.py)
    install(FILES ${CMAKE_SOURCE_DIR}/browser/phazebrowser.py
        DESTINATION ${CMAKE_INSTALL_PREFIX}/browser
        PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
    )
endif()

# Install browser extension if it exists
if(EXISTS ${CMAKE_SOURCE_DIR}/browser-extension)
    install(DIRECTORY ${CMAKE_SOURCE_DIR}/browser-extension/
        DESTINATION ${CMAKE_INSTALL_PREFIX}/browser/browser-extension
        FILES_MATCHING
            PATTERN "*.js"
            PATTERN "*.html"
            PATTERN "*.json"
            PATTERN "*.png"
            PATTERN "*.css"
    )
endif()

# Create desktop entry
if(EXISTS ${CMAKE_SOURCE_DIR}/assets/desktop/phazevpn.desktop)
    install(FILES ${CMAKE_SOURCE_DIR}/assets/desktop/phazevpn.desktop
        DESTINATION ${CMAKE_INSTALL_PREFIX}/browser
    )
endif()

# Create launcher script
set(BROWSER_LAUNCHER ${CMAKE_BINARY_DIR}/browser/phazebrowser-launcher.sh)
file(WRITE ${BROWSER_LAUNCHER}
    "#!/bin/bash\n"
    "cd ${CMAKE_INSTALL_PREFIX}/browser\n"
    "exec ${PYTHON3_EXECUTABLE} phazebrowser.py \"$@\"\n"
)
file(CHMOD ${BROWSER_LAUNCHER} FILE_PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE)

install(PROGRAMS ${BROWSER_LAUNCHER}
    DESTINATION ${CMAKE_INSTALL_PREFIX}/browser
    RENAME phazebrowser-launcher.sh
)

