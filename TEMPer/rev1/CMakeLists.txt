cmake_minimum_required (VERSION 2.6)
project (TEMPer)
# The version number.
set (TEMPER_VERSION_MAJOR 1)
set (TEMPER_VERSION_MINOR 0)

SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Werror")

# configure a header file to pass some of the CMake settings
# to the source code
configure_file (
  "${PROJECT_SOURCE_DIR}/TEMPer_config.h.in"
  "${PROJECT_BINARY_DIR}/TEMPer_config.h"
  )
 
# add the binary tree to the search path for include files
# so that we will find TutorialConfig.h
include_directories("${PROJECT_BINARY_DIR}")
 
# add the executable
add_library(temper SHARED TEMPer.cpp 24c02.cpp  fm75.cpp  i2c.cpp  max6675.cpp  serial.cpp)

add_executable (TEMPerMain main.cpp) 
target_link_libraries(TEMPerMain temper)

