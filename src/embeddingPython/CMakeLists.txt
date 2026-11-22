# Library loaded by OpenFOAM solvers for the Python function objects.
#
# pybFoamEmbed is a header-only INTERFACE target that ships in the pybFoam
# package and provides pyInterp.hpp and nanobindEmbed.hpp. nanobind is linked
# statically, so the library needs no shared library from pybFoam at load time.
# initEmbeddedNanobind() connects it to pybFoam's type registry after the
# interpreter has started.
#
# importlib.util.find_spec locates pybFoam on sys.path without importing it, so
# this works under PEP 517 build isolation and needs no OpenFOAM symbols.

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

target_link_libraries(embeddingPython PUBLIC
    pybFoamEmbed::pybFoamEmbed
    OpenFOAM::finiteVolume
    nanobind-static
)
target_include_directories(embeddingPython PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)

install(TARGETS embeddingPython
    LIBRARY DESTINATION $ENV{FOAM_USER_LIBBIN}
)
