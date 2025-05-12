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
#include "tdemodules/AMCController.hpp"

#include "tdemodules/opmon/tdeamcmodule_info.pb.h"

#include <string>

namespace dunedaq::tdemodules {

TDEAmcModule::TDEAmcModule(const std::string& name)
  : dunedaq::appfwk::DAQModule(name)
{
  register_command("conf", &TDEAmcModule::do_conf);
}

void
TDEAmcModule::init(std::shared_ptr<appfwk::ConfigurationManager> mcfg)
{
    //! appmodel::TDEAmcModule does not 
    // m_dal = mcfg->get_dal<appmodel::TDEAmcModule>(get_name());
    // m_session = mcfg->session();
}

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
    //! placehodler for now, source id, ip and port should come from the configuration manager
    int amc_id = 2;
    std::string ip = "10.73.32." + std::to_string(amc_id);
    int data_port = 54321 + amc_id;

    // Create the AMC controller
    m_ctrl = std::make_unique<AMCController>(ip, data_port);
    std::cout << "Created conroller for AMC " << std::to_string(amc_id) << std::endl;
    m_ctrl->card_status();

    // probably want some checks here, e.g. (AMC is pingable)
}

void
TDEAmcModule::do_start(const data_t& /* do not pass an argument*/ )
{
    m_ctrl->card_start();
}

void
TDEAmcModule::do_stop(const data_t& /* do not pass an argument*/ )
{
    m_ctrl->card_stop();
}

} // namespace dunedaq::tdemodules

DEFINE_DUNE_DAQ_MODULE(dunedaq::tdemodules::TDEAmcModule)
