# Minimum required CMake version
cmake_minimum_required(VERSION 3.12)

# Project declaration (C language)
project(cookie_store_demo C)

# ====================== Basic Configuration ======================
set(CMAKE_C_STANDARD 11)          # Require C11 standard
set(CMAKE_C_STANDARD_REQUIRED ON) # Enforce C11 compliance

# ====================== Platform Detection ======================
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
    if(CMAKE_HOST_SYSTEM_PROCESSOR STREQUAL "x86_64")
        set(KN_TARGET "linuxX64")
    elseif(CMAKE_HOST_SYSTEM_PROCESSOR STREQUAL "aarch64")
        set(KN_TARGET "linuxArm64")
    else()
        message(FATAL_ERROR "Unsupported Linux architecture: ${CMAKE_HOST_SYSTEM_PROCESSOR}")
    endif()
elseif(CMAKE_SYSTEM_NAME MATCHES "Darwin")
    if(CMAKE_HOST_SYSTEM_PROCESSOR STREQUAL "x86_64")
        set(KN_TARGET "macosX64")
    elseif(CMAKE_HOST_SYSTEM_PROCESSOR STREQUAL "arm64")
        set(KN_TARGET "macosArm64")
    else()
        message(FATAL_ERROR "Unsupported macOS architecture: ${CMAKE_HOST_SYSTEM_PROCESSOR}")
    endif()
elseif(CMAKE_SYSTEM_NAME MATCHES "Windows")
    set(KN_TARGET "mingwX64")
else()
    message(FATAL_ERROR "Unsupported system: ${CMAKE_SYSTEM_NAME}")
endif()

# ====================== Protobuf-C Runtime Detection ======================
# Primary detection method using pkg-config
find_package(PkgConfig QUIET)
if(PKG_CONFIG_FOUND)
    pkg_check_modules(PC_PROTOBUF_C QUIET libprotobuf-c)
endif()

# Set search paths for protobuf-c
set(PROTOBUF_C_PATHS
    ${PC_PROTOBUF_C_INCLUDEDIR}
    ${PC_PROTOBUF_C_INCLUDE_DIRS}
    /usr/include
    /usr/local/include
    /opt/homebrew/include  # macOS ARM Homebrew location
)

# Find protobuf-c header location
find_path(PROTOBUF_C_INCLUDE_DIR protobuf-c/protobuf-c.h
    PATHS ${PROTOBUF_C_PATHS}
    DOC "Protobuf-C include directory"
)

# Find protobuf-c library
find_library(PROTOBUF_C_LIBRARY
    NAMES protobuf-c libprotobuf-c
    PATHS ${PC_PROTOBUF_C_LIBDIR}
          ${PC_PROTOBUF_C_LIBRARY_DIRS}
          /usr/lib
          /usr/local/lib
          /opt/homebrew/lib
    DOC "Protobuf-C library"
)

if(PROTOBUF_C_INCLUDE_DIR AND PROTOBUF_C_LIBRARY)
    set(PROTOBUF_C_FOUND TRUE)
    set(PROTOBUF_C_LIBRARIES ${PROTOBUF_C_LIBRARY})
    set(PROTOBUF_C_INCLUDE_DIRS ${PROTOBUF_C_INCLUDE_DIR})
    message(STATUS "Found Protobuf-C: ${PROTOBUF_C_LIBRARY}")
else()
    message(WARNING "Protobuf-C runtime not found, attempting to use bundled")
    # Fallback to bundled protobuf-c implementation could be added here
endif()

# ====================== Main Library Configuration ======================
# Library naming conventions per platform
if(WIN32)
    set(LIB_PREFIX "")
    set(LIB_EXT ".dll")
elseif(APPLE)
    set(LIB_PREFIX "lib")
    set(LIB_EXT ".dylib")
else()
    set(LIB_PREFIX "lib")
    set(LIB_EXT ".so")
endif()

# Build type handling
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()
string(TOLOWER "${CMAKE_BUILD_TYPE}" BUILD_TYPE_LOWER)
if(BUILD_TYPE_LOWER MATCHES "debug")
    set(LIB_SUFFIX "debugShared")
else()
    set(LIB_SUFFIX "releaseShared")
endif()

# Main library path configuration
set(BASE_LIB_DIR "${CMAKE_SOURCE_DIR}/../../build/bin/${KN_TARGET}")
set(COOKIE_LIB_DIR "${BASE_LIB_DIR}/${LIB_SUFFIX}")

# Locate the main library
find_library(COOKIE_MANAGER_LIB
    NAMES ${LIB_PREFIX}kcookie_store${LIB_EXT} ${LIB_PREFIX}kcookie_store
    PATHS ${COOKIE_LIB_DIR}
    NO_DEFAULT_PATH
    REQUIRED
)

# ====================== Executable Configuration ======================
add_executable(cookie_store_demo  # Changed to match project name
    main.c
    cookie_store.pb-c.c  # Use your manually generated protobuf file
)

# Include directories
target_include_directories(cookie_store_demo PRIVATE
    ${CMAKE_SOURCE_DIR}/../../include
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${PROTOBUF_C_INCLUDE_DIRS}
)

# Link libraries
target_link_libraries(cookie_store_demo  # Updated target name
    ${COOKIE_MANAGER_LIB}
    ${PROTOBUF_C_LIBRARIES}  # Link against protobuf-c runtime
)

# ====================== Post-Processing ======================
if(WIN32)
    # Windows DLL handling
    add_custom_command(TARGET cookie_store_demo POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy
            "${COOKIE_LIB_DIR}/${LIB_PREFIX}kcookie_store${LIB_EXT}"
            "$<TARGET_FILE_DIR:cookie_store_demo>"
        COMMENT "Copying DLL to output directory"
    )

    if(PROTOBUF_C_LIBRARY AND LIB_EXT STREQUAL ".dll")
        add_custom_command(TARGET cookie_store_demo POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy
                "${PROTOBUF_C_LIBRARY}"
                "$<TARGET_FILE_DIR:cookie_store_demo>"
            COMMENT "Copying Protobuf-C DLL"
        )
    endif()
endif()