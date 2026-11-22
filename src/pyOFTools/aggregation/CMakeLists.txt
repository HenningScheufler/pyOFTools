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
# aggregation accepts Foam::Field<T> / Foam::labelList parameters whose Python
# types are registered by pybFoam_core. The static nanobind code finds that
# registry through the internals stored in the interpreter, which requires the
# same nanobind ABI as pybFoam.
nanobind_add_module(aggregation NB_STATIC ${AGGREGATION_SOURCES})

# Set target properties
set_target_properties(aggregation PROPERTIES
    CXX_VISIBILITY_PRESET "hidden"
    VISIBILITY_INLINES_HIDDEN ON
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
