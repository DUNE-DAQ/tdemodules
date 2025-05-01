#include "tdemodules/AMCController.hpp"
#include "tdemodules/AMCProtocolClient.hpp"
#include "utilities.hpp"

#include <iostream>
#include <fmt/core.h>

namespace dunedaq {
namespace tdemodules {


AMCController::AMCController(const std::string& ip, uint16_t port) :
m_ctrl_ip(ip),
m_ctrl_port(port) {

// Initialize status command payload
append_big_uint32(m_status_cmd, 0x0);
append_big_uint32(m_status_cmd, 0x0);

// Initialise start command payload
append_big_uint32(m_start_cmd, port);
append_big_uint32(m_start_cmd, kCmdStart);
append_big_uint32(m_start_cmd, 0x0);
append_big_uint32(m_start_cmd, 0x0);


// Initialise stop command payload
append_big_uint32(m_stop_cmd, port);
append_big_uint32(m_stop_cmd, kCmdStop);
append_big_uint32(m_stop_cmd, 0x0);
append_big_uint32(m_stop_cmd, 0x0);


// Initialise reset command payload
append_big_uint32(m_reset_cmd, port);
append_big_uint32(m_reset_cmd, kCmdReset);
append_big_uint32(m_reset_cmd, 0x0);
append_big_uint32(m_reset_cmd, 0x0);

}

void
AMCController::card_reset() {
std::vector<uint8_t> reply;
try {

    auto client = AMCProtocolClient(m_ctrl_ip, m_ctrl_port);

    reply = client.send_wrq(m_reset_cmd);

} catch (const std::exception& e) {
    std::cerr << "Exception: " << e.what() << "\n";
}


}

void
AMCController::card_start() {

std::vector<uint8_t> reply;
try {

    auto client = AMCProtocolClient(m_ctrl_ip, m_ctrl_port);

    reply = client.send_wrq(m_start_cmd);

} catch (const std::exception& e) {
    std::cerr << "Exception: " << e.what() << "\n";
}

// 
}

void
AMCController::card_stop() {
std::vector<uint8_t> reply;
try {

  auto client = AMCProtocolClient(m_ctrl_ip, m_ctrl_port);

  reply = client.send_wrq(m_stop_cmd);

} catch (const std::exception& e) {
  std::cerr << "Exception: " << e.what() << "\n";
}
}

void
AMCController::card_status() {

  std::vector<uint8_t> reply;
  try {

      auto client = AMCProtocolClient(m_ctrl_ip, m_ctrl_port);

      reply = client.send_rrq(m_status_cmd);

  } catch (const std::exception& e) {
      std::cerr << "Exception: " << e.what() << "\n";
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