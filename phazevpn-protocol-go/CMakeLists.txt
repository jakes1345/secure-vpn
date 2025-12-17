cmake_minimum_required(VERSION 3.15)

# Go protocol server build
if(NOT GO_EXECUTABLE)
    message(FATAL_ERROR "Go executable not found. Install Go to build protocol server.")
endif()

# Go build configuration
set(GO_BUILD_DIR ${CMAKE_BINARY_DIR}/phazevpn-protocol-go)
set(GO_OUTPUT ${GO_BUILD_DIR}/phazevpn-server-go)
set(GO_OUTPUT_LINUX ${GO_BUILD_DIR}/phazevpn-server-go-linux)

# Create build directory
file(MAKE_DIRECTORY ${GO_BUILD_DIR})

# Custom command to build Go server
add_custom_command(
    OUTPUT ${GO_OUTPUT}
    COMMAND ${CMAKE_COMMAND} -E chdir ${CMAKE_SOURCE_DIR}/phazevpn-protocol-go
        ${GO_EXECUTABLE} build -o ${GO_OUTPUT} -ldflags "-s -w" .
    DEPENDS ${CMAKE_SOURCE_DIR}/phazevpn-protocol-go/main.go
            ${CMAKE_SOURCE_DIR}/phazevpn-protocol-go/go.mod
    COMMENT "Building PhazeVPN Protocol Server (Go)"
    VERBATIM
)

# Custom command to build Linux cross-compile
add_custom_command(
    OUTPUT ${GO_OUTPUT_LINUX}
    COMMAND ${CMAKE_COMMAND} -E chdir ${CMAKE_SOURCE_DIR}/phazevpn-protocol-go
        env GOOS=linux GOARCH=amd64 ${GO_EXECUTABLE} build -o ${GO_OUTPUT_LINUX} -ldflags "-s -w" .
    DEPENDS ${CMAKE_SOURCE_DIR}/phazevpn-protocol-go/main.go
            ${CMAKE_SOURCE_DIR}/phazevpn-protocol-go/go.mod
    COMMENT "Building PhazeVPN Protocol Server (Go) for Linux"
    VERBATIM
)

# Custom target
add_custom_target(phazevpn-protocol-go-build
    DEPENDS ${GO_OUTPUT} ${GO_OUTPUT_LINUX}
    COMMENT "PhazeVPN Protocol Server (Go) build target"
)

# Install Go binary
install(PROGRAMS ${GO_OUTPUT}
    DESTINATION ${CMAKE_INSTALL_PREFIX}/phazevpn-protocol-go
    RENAME phazevpn-server-go
)

# Install Go source files
install(DIRECTORY ${CMAKE_SOURCE_DIR}/phazevpn-protocol-go/
    DESTINATION ${CMAKE_INSTALL_PREFIX}/phazevpn-protocol-go
    FILES_MATCHING
        PATTERN "*.go"
        PATTERN "go.mod"
        PATTERN "go.sum"
        PATTERN "*.md"
        PATTERN "Makefile"
    PATTERN "*.service" EXCLUDE
    PATTERN "*.json" EXCLUDE
)

# Install configuration files
install(FILES ${CMAKE_SOURCE_DIR}/phazevpn-protocol/phazevpn-users.json
    DESTINATION ${CMAKE_INSTALL_PREFIX}/phazevpn-protocol-go
    OPTIONAL
)

