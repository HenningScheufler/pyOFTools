# Embedding Python library CMakeLists.txt
# Links pybFoamEmbed for interpreter management and nanobind bootstrap

# Find pybFoamEmbed (installed by pybFoam)
list(APPEND CMAKE_PREFIX_PATH "$ENV{FOAM_USER_LIBBIN}/../lib/cmake")
find_package(pybFoamEmbed REQUIRED)

add_library(embeddingPython SHARED
    pyFunctionObject.cpp
    pyPostProcessing.cpp
)

set_target_properties(embeddingPython PROPERTIES
    OUTPUT_NAME "embeddingPython"
    INSTALL_RPATH "$ENV{FOAM_USER_LIBBIN}"
    BUILD_RPATH "$ENV{FOAM_USER_LIBBIN}"
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
