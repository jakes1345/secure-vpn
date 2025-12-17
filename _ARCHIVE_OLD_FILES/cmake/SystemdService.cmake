# CMake module for creating systemd service files

# Function to create a systemd service file
function(create_systemd_service SERVICE_NAME DESCRIPTION WORKING_DIR EXEC_START USER GROUP)
    set(SERVICE_FILE ${CMAKE_BINARY_DIR}/systemd/${SERVICE_NAME}.service)
    
    # Create systemd directory
    file(MAKE_DIRECTORY ${CMAKE_BINARY_DIR}/systemd)
    
    # Write service file
    file(WRITE ${SERVICE_FILE}
        "[Unit]\n"
        "Description=${DESCRIPTION}\n"
        "After=network.target\n"
        "\n"
        "[Service]\n"
        "Type=simple\n"
        "User=${USER}\n"
        "Group=${GROUP}\n"
        "WorkingDirectory=${WORKING_DIR}\n"
        "ExecStart=${EXEC_START}\n"
        "Restart=on-failure\n"
        "RestartSec=5\n"
        "StandardOutput=journal\n"
        "StandardError=journal\n"
        "\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n"
    )
    
    # Install service file
    install(FILES ${SERVICE_FILE}
        DESTINATION ${SYSTEMD_DIR}
        RENAME ${SERVICE_NAME}.service
    )
    
    message(STATUS "Created systemd service: ${SERVICE_NAME}.service")
endfunction()

# Function to create a systemd service with environment variables
function(create_systemd_service_with_env SERVICE_NAME DESCRIPTION WORKING_DIR EXEC_START USER GROUP ENV_VARS)
    set(SERVICE_FILE ${CMAKE_BINARY_DIR}/systemd/${SERVICE_NAME}.service)
    
    # Create systemd directory
    file(MAKE_DIRECTORY ${CMAKE_BINARY_DIR}/systemd)
    
    # Write service file with environment variables
    file(WRITE ${SERVICE_FILE}
        "[Unit]\n"
        "Description=${DESCRIPTION}\n"
        "After=network.target\n"
        "\n"
        "[Service]\n"
        "Type=simple\n"
        "User=${USER}\n"
        "Group=${GROUP}\n"
        "WorkingDirectory=${WORKING_DIR}\n"
    )
    
    # Add environment variables
    foreach(ENV_VAR ${ENV_VARS})
        file(APPEND ${SERVICE_FILE} "Environment=\"${ENV_VAR}\"\n")
    endforeach()
    
    # Add ExecStart and other settings
    file(APPEND ${SERVICE_FILE}
        "ExecStart=${EXEC_START}\n"
        "Restart=on-failure\n"
        "RestartSec=5\n"
        "StandardOutput=journal\n"
        "StandardError=journal\n"
        "\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n"
    )
    
    # Install service file
    install(FILES ${SERVICE_FILE}
        DESTINATION ${SYSTEMD_DIR}
        RENAME ${SERVICE_NAME}.service
    )
    
    message(STATUS "Created systemd service with environment: ${SERVICE_NAME}.service")
endfunction()

