SET( CMAKE_C_FLAGS, -g)

add_executable (uvscopetek main.cpp) 
target_link_libraries(uvscopetek usb-1.0)

