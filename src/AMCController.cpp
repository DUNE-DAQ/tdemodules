#include "tdemodules/AMCController.hpp"
#include "tdemodules/AMCProtocolClient.hpp"
#include "utilities.hpp"

#include <iostream>
#include <fmt/core.h>

#include "logging/Logging.hpp"

namespace dunedaq {
namespace tdemodules {


AMCController::AMCController(const std::string& ip, uint16_t data_port) :
m_ctrl_ip(ip),
m_data_port(data_port) {

// Initialize status command payload
m_status_cmd.clear();
append_big_uint32(m_status_cmd, 0x0);
append_big_uint32(m_status_cmd, 0x0);

// Initialise start command payload
append_big_uint32(m_start_cmd, data_port);
append_big_uint32(m_start_cmd, kCmdStart);
append_big_uint32(m_start_cmd, 0x0);
append_big_uint32(m_start_cmd, 0x0);


// Initialise stop command payload
append_big_uint32(m_stop_cmd, data_port);
append_big_uint32(m_stop_cmd, kCmdStop);
append_big_uint32(m_stop_cmd, 0x0);
append_big_uint32(m_stop_cmd, 0x0);


// Initialise reset command payload
append_big_uint32(m_reset_cmd, data_port);
append_big_uint32(m_reset_cmd, kCmdReset);
append_big_uint32(m_reset_cmd, 0x0);
append_big_uint32(m_reset_cmd, 0x0);

}

std::vector<uint8_t> AMCController::send_cmd(const std::vector<uint8_t>& cmd) {
  std::vector<uint8_t> reply;
  try {
  
      auto client = AMCProtocolClient(m_ctrl_ip, m_ctrl_port);
  
      reply = client.send_wrq(cmd);
  
  } catch (const std::exception& e) {
    auto msg = AMCCommandIssue(ERS_HERE, m_ctrl_ip, m_data_port, e.what());
    ers::error(msg);
    throw msg;
  }
  return reply;
}

void
AMCController::card_reset() {
  send_cmd(m_reset_cmd);
}

void
AMCController::card_start() {
  send_cmd(m_start_cmd);
}

void
AMCController::card_stop() {
  send_cmd(m_stop_cmd);
}

void
AMCController::card_status() {
  std::vector<uint8_t> reply = send_cmd(m_status_cmd);

  if (reply.empty()) {
    TLOG() << "Recieved an empty reply.";
    return;
  }

  // Take the first 4 bytes 
  boost::endian::big_uint32_t word0_be;
  uint32_t word0;

  std::memcpy(&word0_be, reply.data(), sizeof(word0_be));
  fmt::print("word0 {:08x}\n", word0_be);

  // word0 = ntohl(word0);
  word0 = word0_be;
  fmt::print("word0 {:08x}\n", word0);

  uint32_t status  = (word0>>16) & 0xffff;
  uint32_t version = (word0) & 0xffff;

  // # meaning of error bits
  // ErrorBits = { 0:"ADC_CHIPID_ERR",
  //               1:"ADC_SPEED_GRADE_ERR",
  //               2:"ADC_ALIGN_0_ERR",
  //               3:"ADC_ALIGN_1_ERR",
  //               4:"ADC_SERIAL_CTRL_ERR",
  //               5:"ADC_SAMPLE_RATE_ERR",
  //               6:"ADC_OUTPUT_MODE_ERR",
  //               7:"ADC_TEST_MODE_ERR",
  //               8:"WRLEN_AMC_TIME_VALID_ERR",
  //               9:"WRLEN_BITSLIP_ERR" }

  fmt::print("status {:04x}, version {:04x}\n", status, version);

}
  

} // namespace tdemodules
} // namespace dunedaq