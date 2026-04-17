# Embedding Python library CMakeLists.txt
# Links pybFoamEmbed for Python interpreter management.
#
# pybFoamEmbed ships inside the pybFoam wheel under
# site-packages/pybFoam/embed/. Its CMake config lives at
# site-packages/pybFoam/embed/cmake/pybFoamEmbed/ and the .so at
# site-packages/pybFoam/embed/lib/. Locate both via Python_SITELIB so we
# don't depend on a separate install into $FOAM_USER_LIBBIN.

list(APPEND CMAKE_PREFIX_PATH "${Python_SITELIB}/pybFoam/embed/cmake")
find_package(pybFoamEmbed REQUIRED)

add_library(embeddingPython SHARED
    pyFunctionObject.cpp
    pyPostProcessing.cpp
)

# Hardcode pybFoam's lib dirs into RPATH so the loader resolves both
# libpybFoamEmbed.so (under pybFoam/embed/lib/) and libnanobind.so (next
# to the binding modules at pybFoam/) when this library is loaded by an
# OpenFOAM solver / function object.
set_target_properties(embeddingPython PROPERTIES
    OUTPUT_NAME "embeddingPython"
    INSTALL_RPATH "${Python_SITELIB}/pybFoam/embed/lib;${Python_SITELIB}/pybFoam"
    BUILD_RPATH "${Python_SITELIB}/pybFoam/embed/lib;${Python_SITELIB}/pybFoam"
)

# pyFunctionObject uses nanobind directly (nb::object, nb::module_::import_).
# Link the shared `nanobind` target built in Dependencies.cmake so we resolve
# against pybFoam's libnanobind.so at runtime (SONAME match → one process-wide
# nanobind type registry shared with pybFoam_core).
target_link_libraries(embeddingPython PUBLIC
    pybFoamEmbed::pybFoamEmbed
    nanobind
)
target_compile_definitions(embeddingPython PUBLIC NB_SHARED)

target_include_directories(embeddingPython PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)

install(TARGETS embeddingPython
    LIBRARY DESTINATION $ENV{FOAM_USER_LIBBIN}
)
