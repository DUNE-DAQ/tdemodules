/**
 * @file renameme.cpp
 *
 * This is part of the DUNE DAQ Software Suite, copyright 2020.
 * Licensing/copyright details are in the COPYING file that you should have
 * received with this code.
 */

#include "pybind11/pybind11.h"
#include "pybind11/stl.h"

#include "tdemodules/AMCController.hpp"

namespace py = pybind11;

namespace dunedaq::tdemodules::python {

void
register_amc(py::module& m) {
    
    py::class_<AMCController>(m, "AMCController")
    .def(py::init<const std::string&, uint16_t>())
    .def("card_status", &AMCController::card_status)
    .def("card_reset", &AMCController::card_reset)
    .def("card_start", &AMCController::card_start)
    .def("card_stop", &AMCController::card_stop)
    ;
}

} // namespace dunedaq::tdemodules::python
