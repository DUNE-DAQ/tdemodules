#ifndef __DUNEDAQ_TDEMODULES_INCLUDE_AMCCONTROLLER_HPP___
#define __DUNEDAQ_TDEMODULES_INCLUDE_AMCCONTROLLER_HPP___

#include <vector>
#include <cstdint>
#include <string>

namespace dunedaq {
namespace tdemodules {


class AMCController {
  public:
  
    enum CmdCode :  uint32_t {
      kCmdStop =0,
      kCmdStart=1,
      kCmdReset=4
    };
  
    AMCController(const std::string& ip, uint16_t data_port);

    void card_start();
    void card_stop();
    void card_status();
    void card_reset();
  
  private:
    std::string m_ctrl_ip;
    uint16_t m_ctrl_port = 325;
    uint16_t m_data_port;

  
    std::vector<uint8_t> m_status_cmd;
    std::vector<uint8_t> m_start_cmd;
    std::vector<uint8_t> m_stop_cmd;
    std::vector<uint8_t> m_reset_cmd;
  
  
  };
        


} // namespace tdemodules
} // namespace dunedaq

#endif // __DUNEDAQ_TDEMODULES_INCLUDE_AMCCONTROLLER_HPP___