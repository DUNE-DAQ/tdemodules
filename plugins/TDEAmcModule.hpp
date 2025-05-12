/**
 * @file TDEAmcModule.hpp
 *
 * Developer(s) of this DAQModule have yet to replace this line with a brief description of the DAQModule.
 *
 * This is part of the DUNE DAQ Software Suite, copyright 2020.
 * Licensing/copyright details are in the COPYING file that you should have
 * received with this code.
 */

#ifndef TDEMODULES_PLUGINS_TDEAMCMODULE_HPP_
#define TDEMODULES_PLUGINS_TDEAMCMODULE_HPP_

#include "appfwk/DAQModule.hpp"
#include "tdemodules/AMCController.hpp"

#include <atomic>
#include <limits>
#include <string>

namespace dunedaq::tdemodules {

class TDEAmcModule : public dunedaq::appfwk::DAQModule
{
public:
  explicit TDEAmcModule(const std::string& name);

  void init(std::shared_ptr<appfwk::ConfigurationManager>) override;

  TDEAmcModule(const TDEAmcModule&) = delete;
  TDEAmcModule& operator=(const TDEAmcModule&) = delete;
  TDEAmcModule(TDEAmcModule&&) = delete;
  TDEAmcModule& operator=(TDEAmcModule&&) = delete;

  ~TDEAmcModule() = default;

protected:
  void generate_opmon_data() override;

private:
  // Commands TDEAmcModule can receive

  // TO tdemodules DEVELOPERS: PLEASE DELETE THIS FOLLOWING COMMENT AFTER READING IT
  // For any run control command it is possible for a DAQModule to
  // register an action that will be executed upon reception of the
  // command. do_conf is a very common example of this; in
  // TDEAmcModule.cpp you would implement do_conf so that members of
  // TDEAmcModule get assigned values from a configuration passed as 
  // an argument and originating from the CCM system.

  void do_conf(const data_t&);
  void do_start(const data_t&);
  void do_stop(const data_t&);

  // TO tdemodules DEVELOPERS: PLEASE DELETE THIS FOLLOWING COMMENT AFTER READING IT 
  // m_total_amount and m_amount_since_last_get_info_call are examples
  // of variables whose values get reported to OpMon
  // (https://github.com/mozilla/opmon) each time get_info() is
  // called. "amount" represents a (discrete) value which changes as TDEAmcModule
  // runs and whose value we'd like to keep track of during running;
  // obviously you'd want to replace this "in real life"

  std::unique_ptr<AMCController> m_ctrl;
  std::atomic<int64_t> m_total_amount {0};
  std::atomic<int>     m_amount_since_last_call {0};
};

} // namespace dunedaq::tdemodules

#endif // TDEMODULES_PLUGINS_TDEAMCMODULE_HPP_
