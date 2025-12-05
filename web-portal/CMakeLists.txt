cmake_minimum_required(VERSION 3.15)

# Web portal service (Python Flask)
find_program(PYTHON3_EXECUTABLE python3 REQUIRED)
find_program(PIP_EXECUTABLE pip3)

# Python dependencies
set(WEB_PORTAL_REQUIREMENTS ${CMAKE_SOURCE_DIR}/web-portal/requirements.txt)

# Custom target to install Python dependencies
add_custom_target(web-portal-dependencies
    COMMAND ${PIP_EXECUTABLE} install -r ${WEB_PORTAL_REQUIREMENTS}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/web-portal
    COMMENT "Installing web portal Python dependencies"
    VERBATIM
)

# Install web portal files - INCLUDING ALL COMMERCIAL FEATURES
install(DIRECTORY ${CMAKE_SOURCE_DIR}/web-portal/
    DESTINATION ${CMAKE_INSTALL_PREFIX}/web-portal
    FILES_MATCHING
        PATTERN "*.py"
        PATTERN "*.html"
        PATTERN "*.css"
        PATTERN "*.js"
        PATTERN "*.png"
        PATTERN "*.jpg"
        PATTERN "*.jpeg"
        PATTERN "*.ico"
        PATTERN "*.json"
        PATTERN "*.txt"
        PATTERN "*.conf"
        PATTERN "*.service"
        PATTERN "*.md"
    PATTERN "__pycache__" EXCLUDE
        PATTERN "*.pyc" EXCLUDE
        PATTERN ".git" EXCLUDE
        PATTERN "backups" EXCLUDE
)

# CRITICAL: Explicitly install payment and subscription files
install(FILES 
    ${CMAKE_SOURCE_DIR}/web-portal/payment_integrations.py
    ${CMAKE_SOURCE_DIR}/web-portal/secure_auth.py
    ${CMAKE_SOURCE_DIR}/web-portal/email_api.py
    ${CMAKE_SOURCE_DIR}/web-portal/email_mailjet.py
    ${CMAKE_SOURCE_DIR}/web-portal/email_smtp.py
    ${CMAKE_SOURCE_DIR}/web-portal/email_util.py
    ${CMAKE_SOURCE_DIR}/web-portal/mailjet_config.py
    ${CMAKE_SOURCE_DIR}/web-portal/smtp_config.py
    DESTINATION ${CMAKE_INSTALL_PREFIX}/web-portal
    OPTIONAL
)

# Install subscription manager (root level)
install(FILES 
    ${CMAKE_SOURCE_DIR}/subscription-manager.py
    DESTINATION ${CMAKE_INSTALL_PREFIX}
    OPTIONAL
)

# Create gunicorn wrapper script
set(GUNICORN_WRAPPER ${CMAKE_BINARY_DIR}/web-portal/gunicorn-wrapper.sh)
file(WRITE ${GUNICORN_WRAPPER}
    "#!/bin/bash\n"
    "cd ${CMAKE_INSTALL_PREFIX}/web-portal\n"
    "exec ${GUNICORN_EXECUTABLE} --workers 4 --bind 127.0.0.1:5000 --timeout 120 --access-logfile /var/log/phazevpn-portal-access.log --error-logfile /var/log/phazevpn-portal-error.log app:app\n"
)
file(CHMOD ${GUNICORN_WRAPPER} FILE_PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE)

install(PROGRAMS ${GUNICORN_WRAPPER}
    DESTINATION ${CMAKE_INSTALL_PREFIX}/web-portal
    RENAME gunicorn-wrapper.sh
)

# Create directories for logs and data
install(CODE "
    file(MAKE_DIRECTORY \${CMAKE_INSTALL_PREFIX}/web-portal/logs)
    file(MAKE_DIRECTORY \${CMAKE_INSTALL_PREFIX}/web-portal/data)
    file(MAKE_DIRECTORY \${CMAKE_INSTALL_PREFIX}/web-portal/uploads)
")

