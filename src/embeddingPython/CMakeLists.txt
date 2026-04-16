# Embedding Python library CMakeLists.txt
# Links pybFoamEmbed for interpreter management and nanobind bootstrap
#
# Layout:
#   libembeddingPython.so   -> $FOAM_USER_LIBBIN (OpenFOAM function object)
#   libpybFoamEmbed.so      -> $FOAM_USER_LIBBIN (copied from pybFoam wheel)
#   libnanobind.so          -> $FOAM_USER_LIBBIN (copied from pybFoam wheel)
# uv build isolation overwrite the the site-packages path, so we need cannot set an RPATH
# Find pybFoamEmbed — shipped inside the pybFoam wheel (Python_SITELIB)
list(APPEND CMAKE_PREFIX_PATH "${Python_SITELIB}/pybFoam/embed/cmake")
find_package(pybFoamEmbed REQUIRED)

add_library(embeddingPython SHARED
    pyFunctionObject.cpp
    pyPostProcessing.cpp
)

set_target_properties(embeddingPython PROPERTIES
    OUTPUT_NAME "embeddingPython"
    INSTALL_RPATH "$ENV{FOAM_USER_LIBBIN}"
    BUILD_RPATH   "$ENV{FOAM_USER_LIBBIN}"
)

# Everything comes transitively from pybFoamEmbed
target_link_libraries(embeddingPython PUBLIC
    pybFoamEmbed::pybFoamEmbed
)

target_include_directories(embeddingPython PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)

install(TARGETS embeddingPython
    LIBRARY DESTINATION $ENV{FOAM_USER_LIBBIN}
)

# Copy pybFoamEmbed + nanobind shared libs into FOAM_USER_LIBBIN so
# libembeddingPython.so's NEEDED entries resolve via its RPATH.
foreach(_tgt pybFoamEmbed::pybFoamEmbed pybFoamEmbed::nanobind)
    if(TARGET ${_tgt})
        get_target_property(_loc ${_tgt} IMPORTED_LOCATION_RELEASE)
        if(NOT _loc)
            get_target_property(_loc ${_tgt} IMPORTED_LOCATION)
        endif()
        if(_loc)
            install(FILES "${_loc}" DESTINATION $ENV{FOAM_USER_LIBBIN})
        endif()
    endif()
endforeach()
