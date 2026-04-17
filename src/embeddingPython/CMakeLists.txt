# Embedding Python library CMakeLists.txt
# Links pybFoamEmbed for Python interpreter management.
#
# pybFoamEmbed ships inside the pybFoam wheel at <pybFoam>/embed/. We
# need <pybFoam>'s on-disk path. Under PEP 517 build isolation, pip/uv
# may either (a) run the build in an overlay venv whose sysconfig purelib
# IS the pybFoam site-packages, or (b) keep sys.prefix = target env and
# inject the overlay via PYTHONPATH — in which case purelib is wrong but
# pybFoam is still on sys.path. importlib.util.find_spec handles both
# cases: it walks sys.path to locate pybFoam without executing its
# __init__.py, so no OpenFOAM symbols, no ABI issues, no teardown
# segfaults — purely a filesystem lookup.

execute_process(
    COMMAND ${Python_EXECUTABLE} -c
        "import importlib.util, pathlib; s = importlib.util.find_spec('pybFoam'); assert s and s.submodule_search_locations, 'pybFoam not found on sys.path'; print(pathlib.Path(s.submodule_search_locations[0]) / 'embed')"
    OUTPUT_VARIABLE PYBFOAM_EMBED_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE PYBFOAM_EMBED_RESULT
)
if(NOT PYBFOAM_EMBED_RESULT EQUAL 0)
    message(FATAL_ERROR
        "Could not locate pybFoam via ${Python_EXECUTABLE}. "
        "Ensure pybFoam is installed or on PYTHONPATH in the build environment.")
endif()
if(NOT IS_DIRECTORY "${PYBFOAM_EMBED_DIR}")
    message(FATAL_ERROR
        "Expected pybFoam at ${PYBFOAM_EMBED_DIR} but that directory does not exist.")
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
