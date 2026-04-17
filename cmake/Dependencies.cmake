# Dependencies configuration for pyOFTools.
#
option(PYOFTOOLS_BUILD_TESTS "Build C++ tests (requires internet access for CPM to fetch Catch2)" OFF)

# -- nanobind
#
# Eagerly build the shared `nanobind` target. All NB_SHARED users in this
# project (embeddingPython for nb::object/import_, aggregation for the
# Python module) link to it; once it exists, downstream nanobind_add_module
# calls short-circuit nanobind_build_library and reuse this target. At
# runtime, RPATH on each consumer points at pybFoam's installed
# libnanobind.so so SONAME deduplication keeps the type registry shared
# with pybFoam (matching ABI flags required).
function(add_nanobind)
    find_package(nanobind CONFIG REQUIRED)
    nanobind_build_library(nanobind)
    message(STATUS "Found nanobind; built shared `nanobind` target")
endfunction()

# -- CPM bootstrap (only when tests are requested) ---------------------------
function(bootstrap_cpm)
    set(CPM_DOWNLOAD_VERSION 0.38.3)
    set(CPM_DOWNLOAD_LOCATION "${CMAKE_BINARY_DIR}/cmake/CPM_${CPM_DOWNLOAD_VERSION}.cmake")

    if(NOT EXISTS "${CPM_DOWNLOAD_LOCATION}")
        message(STATUS "Downloading CPM.cmake to ${CPM_DOWNLOAD_LOCATION}")
        file(DOWNLOAD
            https://github.com/cpm-cmake/CPM.cmake/releases/download/v${CPM_DOWNLOAD_VERSION}/CPM.cmake
            "${CPM_DOWNLOAD_LOCATION}"
            EXPECTED_HASH SHA256=cc155ce02e7945e7b8967ddfaff0b050e958a723ef7aad3766d368940cb15494
        )
    endif()

    include("${CPM_DOWNLOAD_LOCATION}")
    set(CPM_USE_LOCAL_PACKAGES ON PARENT_SCOPE)
    set(CPM_LOCAL_PACKAGES_ONLY OFF PARENT_SCOPE)
endfunction()

# -- Catch2 via CPM (tests only) --------------------------------------------
function(add_testing_deps)
    bootstrap_cpm()

    CPMAddPackage(
        NAME Catch2
        GITHUB_REPOSITORY catchorg/Catch2
        VERSION 3.4.0
        OPTIONS
            "CATCH_INSTALL_DOCS OFF"
            "CATCH_INSTALL_EXTRAS OFF"
    )

    if(Catch2_ADDED)
        message(STATUS "Added Catch2 for testing")
    endif()
endfunction()

# Main
function(configure_dependencies)
    message(STATUS "Configuring pyOFTools dependencies...")
    add_nanobind()

    if(PYOFTOOLS_BUILD_TESTS)
        add_testing_deps()
    else()
        message(STATUS "Skipping C++ test deps (pass -DPYOFTOOLS_BUILD_TESTS=ON to enable)")
    endif()

    message(STATUS "Dependencies configuration complete")
endfunction()

configure_dependencies()
