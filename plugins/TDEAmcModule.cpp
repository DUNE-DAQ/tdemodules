/**
 * @file TDEAmcModule.cpp
 *
 * Implementations of TDEAmcModule's functions
 *
 * This is part of the DUNE DAQ Software Suite, copyright 2020.
 * Licensing/copyright details are in the COPYING file that you should have
 * received with this code.
 */

#include "TDEAmcModule.hpp"

#include "tdemodules/opmon/tdeamcmodule_info.pb.h"

#include <string>

namespace dunedaq::tdemodules {

TDEAmcModule::TDEAmcModule(const std::string& name)
  : dunedaq::appfwk::DAQModule(name)
{
  register_command("conf", &TDEAmcModule::do_conf);
}

void
TDEAmcModule::init(std::shared_ptr<appfwk::ConfigurationManager> /* mcfg */)
{}

void
TDEAmcModule::generate_opmon_data()
{
  opmon::TDEAmcModuleInfo info;
  info.set_total_amount(m_total_amount.load());
  info.set_amount_since_last_call(m_amount_since_last_call.exchange(0));
  publish(std::move(info));
}

void
TDEAmcModule::do_conf(const data_t& /* do not pass an argument*/ )
{
}

} // namespace dunedaq::tdemodules

DEFINE_DUNE_DAQ_MODULE(dunedaq::tdemodules::TDEAmcModule)
