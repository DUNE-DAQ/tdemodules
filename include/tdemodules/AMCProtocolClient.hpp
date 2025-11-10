#ifndef __DUNEDAQ_TDEMODULES_INCLUDE_AMCPROTOCOLCLIENT_HPP___
#define __DUNEDAQ_TDEMODULES_INCLUDE_AMCPROTOCOLCLIENT_HPP___

#include <vector>
#include <cstdint>

#include <boost/endian/arithmetic.hpp>
#include <boost/asio.hpp>

#include "logging/Logging.hpp"

namespace dunedaq {


ERS_DECLARE_ISSUE(
    tdemodules, 
    AMCProtocolIssue,
    prefix << "AMCProtocolResponse: " << text,
    ((std::string)prefix)((std::string)text)
);

ERS_DECLARE_ISSUE(
    tdemodules, 
    TFTPReceiveError,
    prefix << "TFTPReceiveError: " << text,
    ((std::string)prefix)((std::string)text)
);

ERS_DECLARE_ISSUE(
    tdemodules, 
    TFTPReplyTooShort,
    prefix << "TFTPReplyTooShort: " << text,
    ((std::string)prefix)((std::string)text)
);

ERS_DECLARE_ISSUE(
    tdemodules, 
    PacketError,
    prefix << "PacketError: " << text,
    ((std::string)prefix)((std::string)text)
);

ERS_DECLARE_ISSUE(
    tdemodules, 
    AMCResponseErr,
    prefix << "Received Error packet:" << "\n" << "Error code:" << code << "\nMessage: " << text,
    ((std::string)prefix)((uint16_t)code)((std::string)text)
);

ERS_DECLARE_ISSUE(
    tdemodules, 
    AMCUnknownOpCode,
    prefix << "Unknown opcode recived: " << opcode,
    ((std::string)prefix)((uint16_t)opcode)
);

namespace tdemodules {

class AMCProtocolClient {
  public:
    enum TFTPOpCode : uint16_t {
        RRQ = 1,
        WRQ = 2,
        DAT = 3,
        ACK = 4,
        ERR = 5,
    };
  
  
    #pragma pack(push, 1)
    struct TFTP_Data_Header {
      boost::endian::big_uint16_t opcode;
      boost::endian::big_uint16_t block;
    };
  
    struct TFTP_Error_Header {
      boost::endian::big_uint16_t opcode;
      boost::endian::big_uint16_t error_code;
    };
  
    struct TFTP_Ack_Header {
      boost::endian::big_uint16_t opcode;
      boost::endian::big_uint16_t block;
    };
    #pragma pack(pop)
  
  
  
    AMCProtocolClient(const std::string& server_ip, uint16_t port);
  
    std::vector<uint8_t> send_request(TFTPOpCode opcode, const std::vector<uint8_t>& payload);
  
    std::vector<uint8_t> send_rrq(const std::vector<uint8_t>& payload) {
        return send_request(RRQ, payload);
    }
  
    std::vector<uint8_t> send_wrq(const std::vector<uint8_t>& payload) {
        return send_request(WRQ, payload);
      }
  
  private:
  
    std::string m_host;
    uint16_t m_port;
    uint16_t m_timeout;
  
    const std::string m_log_prefix = "AMC with ip:" + m_host + " and port: " + std::to_string(m_port) + " | ";

    boost::asio::io_context m_io_context;
    boost::asio::ip::udp::socket m_socket;
    boost::asio::ip::udp::endpoint m_server_endpoint;
  
  };
    
} // namespace tdemodules
} // namespace dunedaq

#endif // __DUNEDAQ_TDEMODULES_INCLUDE_AMCPROTOCOLCLIENT_HPP___