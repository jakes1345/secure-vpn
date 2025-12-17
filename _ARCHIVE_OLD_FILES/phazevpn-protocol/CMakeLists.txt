cmake_minimum_required(VERSION 3.15)

# Python protocol service
find_program(PYTHON3_EXECUTABLE python3 REQUIRED)
find_program(PIP_EXECUTABLE pip3)

# Python dependencies
set(PROTOCOL_REQUIREMENTS ${CMAKE_SOURCE_DIR}/phazevpn-protocol/requirements.txt)

# Custom target to install Python dependencies
add_custom_target(phazevpn-protocol-dependencies
    COMMAND ${PIP_EXECUTABLE} install -r ${PROTOCOL_REQUIREMENTS}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/phazevpn-protocol
    COMMENT "Installing protocol Python dependencies"
    VERBATIM
)

# Install protocol service files
install(DIRECTORY ${CMAKE_SOURCE_DIR}/phazevpn-protocol/
    DESTINATION ${CMAKE_INSTALL_PREFIX}/phazevpn-protocol
    FILES_MATCHING
        PATTERN "*.py"
        PATTERN "*.sh"
        PATTERN "*.json"
        PATTERN "*.txt"
        PATTERN "*.md"
        PATTERN "*.service"
    PATTERN "__pycache__" EXCLUDE
        PATTERN "*.pyc" EXCLUDE
        PATTERN ".git" EXCLUDE
)

# Make Python scripts executable
install(CODE "
    file(GLOB_RECURSE PYTHON_SCRIPTS \${CMAKE_INSTALL_PREFIX}/phazevpn-protocol/*.py)
    file(GLOB_RECURSE SHELL_SCRIPTS \${CMAKE_INSTALL_PREFIX}/phazevpn-protocol/*.sh)
    foreach(SCRIPT \${PYTHON_SCRIPTS} \${SHELL_SCRIPTS})
        file(CHMOD \${SCRIPT} FILE_PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE)
    endforeach()
")

# Create wrapper script for production server
set(PROTOCOL_WRAPPER ${CMAKE_BINARY_DIR}/phazevpn-protocol/phazevpn-protocol-wrapper.sh)
file(WRITE ${PROTOCOL_WRAPPER}
    "#!/bin/bash\n"
    "cd ${CMAKE_INSTALL_PREFIX}/phazevpn-protocol\n"
    "exec ${PYTHON3_EXECUTABLE} phazevpn-server-production.py \"$@\"\n"
)
file(CHMOD ${PROTOCOL_WRAPPER} FILE_PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE)

install(PROGRAMS ${PROTOCOL_WRAPPER}
    DESTINATION ${CMAKE_INSTALL_PREFIX}/phazevpn-protocol
    RENAME phazevpn-protocol-wrapper.sh
)

# Create directories for logs and data
install(CODE "
    file(MAKE_DIRECTORY \${CMAKE_INSTALL_PREFIX}/phazevpn-protocol/logs)
    file(MAKE_DIRECTORY \${CMAKE_INSTALL_PREFIX}/phazevpn-protocol/data)
")

