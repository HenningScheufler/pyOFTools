# Embedding Python library CMakeLists.txt


# Gather all C++ sources and headers
set(EMBED_PYTHON_SOURCES
    pyFunctionObject.cpp
    pyInterp.cpp
    pyPostProcessing.cpp
)
set(EMBED_PYTHON_HEADERS
    pyFunctionObject.hpp
    pyInterp.hpp
    pyPostProcessing.hpp
)

# Create shared library for pybind11/scikit-build
add_library(embeddingPython SHARED ${EMBED_PYTHON_SOURCES})

# Set target properties
set_target_properties(embeddingPython PROPERTIES
    CXX_VISIBILITY_PRESET "hidden"
    VISIBILITY_INLINES_HIDDEN ON
    OUTPUT_NAME "embeddingPython"
)

# Link OpenFOAM and Python libraries
target_link_libraries(embeddingPython PUBLIC
    OpenFOAM::finiteVolume
    Python::Python
    pybind11::embed
)

# Add include directories
target_include_directories(embeddingPython PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Install the library
install(TARGETS embeddingPython
    LIBRARY DESTINATION $ENV{FOAM_USER_LIBBIN}
    ARCHIVE DESTINATION $ENV{FOAM_USER_LIBBIN}
)

# Install headers
install(FILES ${EMBED_PYTHON_HEADERS}
    DESTINATION $ENV{FOAM_USER_LIBBIN}/../include/embeddingPython
)
