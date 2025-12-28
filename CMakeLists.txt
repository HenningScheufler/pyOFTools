cmake_minimum_required(VERSION 3.18)

# Set CMake policies for compatibility
if(POLICY CMP0169)
    cmake_policy(SET CMP0169 OLD)
endif()

project(pyOFTools VERSION 0.1.1 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add cmake module path
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

# Configure dependencies with CPM (if Dependencies.cmake exists)
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/cmake/Dependencies.cmake")
    include(Dependencies)
endif()

# Find Python (scikit-build-core sets up Python variables)
if(NOT Python_FOUND)
    find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
endif()

# Find OpenFOAM
find_package(OpenFOAM REQUIRED)

# Add compiler flags for OpenFOAM compatibility
add_compile_options(-Wno-old-style-cast)

if(DEFINED SKBUILD)
    # Let scikit-build-core handle the install locations
    message(STATUS "Building with scikit-build-core")
else()
    # Standalone build - set our own output directories
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/lib")
    set(PYTHON_INSTALL_DIR "${CMAKE_LIBRARY_OUTPUT_DIRECTORY}")
endif()

# Add subdirectories for OpenFOAM integration
add_subdirectory(src/embeddingPython)

# Optional: Add applications and tests
# add_subdirectory(application EXCLUDE_FROM_ALL)
# enable_testing()
# add_subdirectory(testsuite EXCLUDE_FROM_ALL)
