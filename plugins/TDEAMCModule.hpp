/**
 * @file TDEAMCModule.hpp
 *
 * Developer(s) of this DAQModule have yet to replace this line with a brief description of the DAQModule.
 *
 * This is part of the DUNE DAQ Software Suite, copyright 2020.
 * Licensing/copyright details are in the COPYING file that you should have
 * received with this code.
 */

#ifndef TDEMODULES_PLUGINS_TDEAMCMODULE_HPP_
#define TDEMODULES_PLUGINS_TDEAMCMODULE_HPP_

#include "appmodel/TDEAMCModule.hpp"
#include "appfwk/DAQModule.hpp"
#include "tdemodules/AMCController.hpp"

#include <atomic>
#include <limits>
#include <string>

namespace dunedaq::tdemodules {

class TDEAMCModule : public dunedaq::appfwk::DAQModule
{
public:
  explicit TDEAMCModule(const std::string& name);

  void init(std::shared_ptr<appfwk::ConfigurationManager>) override;

  TDEAMCModule(const TDEAMCModule&) = delete;
  TDEAMCModule& operator=(const TDEAMCModule&) = delete;
  TDEAMCModule(TDEAMCModule&&) = delete;
  TDEAMCModule& operator=(TDEAMCModule&&) = delete;

  ~TDEAMCModule() = default;

protected:
  void generate_opmon_data() override;

private:
  // Commands TDEAMCModule can receive

  // TO tdemodules DEVELOPERS: PLEASE DELETE THIS FOLLOWING COMMENT AFTER READING IT
  // For any run control command it is possible for a DAQModule to
  // register an action that will be executed upon reception of the
  // command. do_conf is a very common example of this; in
  // TDEAMCModule.cpp you would implement do_conf so that members of
  // TDEAMCModule get assigned values from a configuration passed as 
  // an argument and originating from the CCM system.

  void do_conf(const CommandData_t&);
  void do_start(const CommandData_t&);
  void do_stop(const CommandData_t&);

  // TO tdemodules DEVELOPERS: PLEASE DELETE THIS FOLLOWING COMMENT AFTER READING IT 
  // m_total_amount and m_amount_since_last_get_info_call are examples
  // of variables whose values get reported to OpMon
  // (https://github.com/mozilla/opmon) each time get_info() is
  // called. "amount" represents a (discrete) value which changes as TDEAMCModule
  // runs and whose value we'd like to keep track of during running;
  // obviously you'd want to replace this "in real life"

  std::unique_ptr<AMCController> m_ctrl;
  std::atomic<int64_t> m_total_amount {0};
  std::atomic<int>     m_amount_since_last_call {0};

  const appmodel::TDEAMCModule* m_dal;
  const confmodel::Session* m_session;

};

} // namespace dunedaq::tdemodules

#endif // TDEMODULES_PLUGINS_TDEAMCMODULE_HPP_
