# Embedding Python library CMakeLists.txt
# Links pybFoamEmbed for Python interpreter management.
#
# pybFoamEmbed ships inside the pybFoam wheel at a fixed layout:
# <site-packages>/pybFoam/embed/. Query the build interpreter for its
# site-packages via sysconfig (no pybFoam import needed — avoids loading
# OpenFOAM symbols or triggering any pybFoam runtime initialization) and
# append the known pybFoam/embed suffix.

execute_process(
    COMMAND ${Python_EXECUTABLE} -c
        "import sysconfig; print(sysconfig.get_path('purelib'))"
    OUTPUT_VARIABLE PYBFOAM_SITE_PACKAGES
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE PYBFOAM_SITE_RESULT
)
if(NOT PYBFOAM_SITE_RESULT EQUAL 0)
    message(FATAL_ERROR
        "Could not query site-packages via ${Python_EXECUTABLE}.")
endif()

set(PYBFOAM_EMBED_DIR "${PYBFOAM_SITE_PACKAGES}/pybFoam/embed")
if(NOT IS_DIRECTORY "${PYBFOAM_EMBED_DIR}")
    message(FATAL_ERROR
        "Expected pybFoam at ${PYBFOAM_EMBED_DIR} but that directory does "
        "not exist. Ensure pybFoam is installed into the Python environment "
        "used for the build (Python_EXECUTABLE=${Python_EXECUTABLE}).")
endif()

list(APPEND CMAKE_PREFIX_PATH "${PYBFOAM_EMBED_DIR}/cmake")
find_package(pybFoamEmbed REQUIRED)

add_library(embeddingPython SHARED
    pyFunctionObject.cpp
    pyPostProcessing.cpp
)

# RPATH = $ORIGIN so the installed library resolves libpybFoamEmbed.so
# and libnanobind.so from $FOAM_USER_LIBBIN (where the install rules
# below drop them). Avoids baking the build Python's site-packages path,
# which is a pip build-isolation overlay that disappears after build.
set_target_properties(embeddingPython PROPERTIES
    OUTPUT_NAME "embeddingPython"
    INSTALL_RPATH "$ORIGIN"
    BUILD_RPATH "${PYBFOAM_EMBED_DIR}/lib;${PYBFOAM_EMBED_DIR}/.."
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

# Copy pybFoam's shared libs next to embeddingPython so $ORIGIN RPATH
# can find them. SONAME dedup in the dynamic loader keeps a single
# libnanobind.so resident across the process even when pybFoam_core.so
# loads its own copy from site-packages/pybFoam/ later.
install(FILES
    "${PYBFOAM_EMBED_DIR}/lib/libpybFoamEmbed.so"
    "${PYBFOAM_EMBED_DIR}/../libnanobind.so"
    DESTINATION $ENV{FOAM_USER_LIBBIN}
)
