cmake_minimum_required (VERSION 2.6)
project (uvscopetek)

SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Werror")

SET( EXECUTABLE_OUTPUT_PATH ${PROJECT_BINARY_DIR}/bin)
SET( LIBRARY_OUTPUT_PATH ${PROJECT_BINARY_DIR}/bin)

include_directories("${PROJECT_BINARY_DIR}")

add_subdirectory(capture)
add_subdirectory(decode)

