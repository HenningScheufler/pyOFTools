# aggregation module CMakeLists.txt

set(AGGREGATION_SOURCES
    bind_aggregation.cpp
    aggregation.cpp
)

set(AGGREGATION_HEADERS
    bind_aggregation.hpp
)

# Create the nanobind module.
#
# NB_SHARED is required so this module shares pybFoam's nanobind type
# registry: aggregation accepts Foam::Field<T> / Foam::labelList parameters
# whose Python types are registered by pybFoam_core. Static linking would
# give us a private nanobind runtime → registry isolation → TypeError or
# segfault when arguments cross the module boundary.
#
# The Linux loader resolves DT_NEEDED libnanobind.so by SONAME against
# pybFoam's already-loaded copy (importing pyOFTools triggers `import
# pybFoam` first via dependency); the RPATH below is the fallback path
# in case nothing has loaded it yet.
nanobind_add_module(aggregation NB_SHARED ${AGGREGATION_SOURCES})

# Set target properties
set_target_properties(aggregation PROPERTIES
    CXX_VISIBILITY_PRESET "hidden"
    VISIBILITY_INLINES_HIDDEN ON
    INSTALL_RPATH "$ORIGIN/../pybFoam"
)

# Link OpenFOAM libraries
target_link_libraries(aggregation PRIVATE
    OpenFOAM::finiteVolume
)

# Add include directories specific to this module
target_include_directories(aggregation PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Install the module
if(DEFINED SKBUILD)
    # scikit-build-core manages the installation
    install(TARGETS aggregation
        LIBRARY DESTINATION pyOFTools
        COMPONENT python
    )
else()
    # Standalone build - install to Python site-packages
    install(TARGETS aggregation
        LIBRARY DESTINATION "${Python_SITELIB}/pyOFTools"
    )
endif()
