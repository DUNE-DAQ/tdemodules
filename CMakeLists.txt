

# This is a skeleton CMakeLists.txt file, auto-generated on
# Wed Apr 30 23:14:49 CEST 2025.  The developer(s) of this package should delete
# this comment as well as adding dependent targets, packages,
# etc. specific to the package. For details on how to write a package,
# please see
# https://dune-daq-sw.readthedocs.io/en/latest/packages/daq-cmake/

cmake_minimum_required(VERSION 3.12)
project(tdemodules VERSION 1.1.2)

find_package(daq-cmake REQUIRED)

daq_setup_environment()


find_package(appfwk REQUIRED)
find_package(opmonlib REQUIRED)
# find_package(Boost COMPONENTS unit_test_framework REQUIRED)
find_package(Boost COMPONENTS system REQUIRED)
find_package(fmt REQUIRED)

##############################################################################


# See https://dune-daq-sw.readthedocs.io/en/latest/packages/daq-cmake/#daq_protobuf_codegen

daq_protobuf_codegen(opmon/*.proto)

##############################################################################


# See https://dune-daq-sw.readthedocs.io/en/latest/packages/daq-cmake/#daq_add_library

daq_add_library( *.cpp LINK_LIBRARIES Boost::system opmonlib::opmonlib fmt::fmt) 

##############################################################################


# See https://dune-daq-sw.readthedocs.io/en/latest/packages/daq-cmake/#daq_add_python_bindings


daq_add_python_bindings(*.cpp ) # Any additional libraries to link in beyond the main library not yet determined


##############################################################################


# See https://dune-daq-sw.readthedocs.io/en/latest/packages/daq-cmake/#daq_add_plugin

daq_add_plugin(TDEAMCModule duneDAQModule LINK_LIBRARIES tdemodules appfwk::appfwk) # The appfwk library is needed for DAQModule base class

##############################################################################


# See https://dune-daq-sw.readthedocs.io/en/latest/packages/daq-cmake/#daq_add_unit_test

# daq_add_unit_test(Placeholder_test LINK_LIBRARIES)  # Placeholder_test should be replaced with real unit tests

##############################################################################

daq_install()

