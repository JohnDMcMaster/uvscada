cmake_minimum_required (VERSION 2.6)

SET(requiredPackages usb-1.0)

project (mu800)

add_library(mu800 SHARED
	mu800.cpp
)

target_link_libraries(usb-1.0)

