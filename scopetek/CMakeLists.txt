cmake_minimum_required (VERSION 2.6)
project (uvscopetek)

# some issues on 64 bit still
SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Werror -m32")

SET( EXECUTABLE_OUTPUT_PATH ${PROJECT_BINARY_DIR}/bin)
SET( LIBRARY_OUTPUT_PATH ${PROJECT_BINARY_DIR}/bin)

include_directories("${PROJECT_BINARY_DIR}")

add_subdirectory(capture)
add_subdirectory(decode)

