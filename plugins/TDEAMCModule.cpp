/**
 * @file TDEAMCModule.cpp
 *
 * Implementations of TDEAMCModule's functions
 *
 * This is part of the DUNE DAQ Software Suite, copyright 2020.
 * Licensing/copyright details are in the COPYING file that you should have
 * received with this code.
 */

#include "appmodel/TDEAMCModule.hpp"
#include "appmodel/TdeAmcDetDataSender.hpp"
#include "appmodel/NWDetDataSender.hpp"
#include "confmodel/NetworkInterface.hpp"
#include "TDEAMCModule.hpp"
#include "tdemodules/AMCController.hpp"

#include "tdemodules/opmon/tdeamcmodule_info.pb.h"

#include <string>

namespace dunedaq::tdemodules {

TDEAMCModule::TDEAMCModule(const std::string& name)
  : dunedaq::appfwk::DAQModule(name)
{
  register_command("conf", &TDEAMCModule::do_conf);
  register_command("start", &TDEAMCModule::do_start);
  register_command("stop", &TDEAMCModule::do_stop);
}

void
TDEAMCModule::init(std::shared_ptr<appfwk::ConfigurationManager> mcfg)
{
    m_dal = mcfg->get_dal<appmodel::TDEAMCModule>(get_name());
    m_session = mcfg->get_session();
}

void
TDEAMCModule::generate_opmon_data()
{
  opmon::TDEAMCModuleInfo info;
  info.set_total_amount(m_total_amount.load());
  info.set_amount_since_last_call(m_amount_since_last_call.exchange(0));
  publish(std::move(info));
}

void
TDEAMCModule::do_conf(const CommandData_t& /* do not pass an argument*/)
{
    uint32_t data_port = m_dal->get_amc()->get_port();
    std::string ip = m_dal->get_amc()->get_control_endpoint()[0].get_ip_address()[0];

    // Create the AMC controller
    m_ctrl = std::make_unique<AMCController>(ip, data_port);
    std::cout << "Created conroller for AMC " << ip << std::endl;
    
    if(!m_dal->get_amc()->is_disabled(*m_session))
    {
        m_ctrl->card_stop(); // stop AMC from taking data in case TDE readout was not gracefully stopped
        m_ctrl->card_status();
    }

    // probably want some checks here, e.g. (AMC is pingable?)
}

void
TDEAMCModule::do_start(const CommandData_t& /* do not pass an argument*/)
{
    if(!m_dal->get_amc()->is_disabled(*m_session))
    {
        m_ctrl->card_start();
    }
}

void
TDEAMCModule::do_stop(const CommandData_t& /* do not pass an argument*/)
{
    if(!m_dal->get_amc()->is_disabled(*m_session))
    {
        m_ctrl->card_stop();
    }
}

void
TDEAMCModule::do_scrap(const CommandData_t& /* do not pass an argument*/)
{
    if(!m_dal->get_amc()->is_disabled(*m_session))
    {
        m_ctrl->card_stop();
    }
}

} // namespace dunedaq::tdemodules

DEFINE_DUNE_DAQ_MODULE(dunedaq::tdemodules::TDEAMCModule)
