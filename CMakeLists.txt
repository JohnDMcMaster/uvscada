cmake_minimum_required (VERSION 2.6)
project (uvscopetek)

SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Werror")

include_directories("${PROJECT_BINARY_DIR}")

add_subdirectory(capture)
add_subdirectory(decode)

