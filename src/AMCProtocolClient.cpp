#include "tdemodules/AMCProtocolClient.hpp"

#include <boost/lexical_cast.hpp>
#include <fmt/ranges.h>
#include "utilities.hpp"

#include "logging/Logging.hpp"

namespace dunedaq {
namespace tdemodules {


AMCProtocolClient::AMCProtocolClient(const std::string& server_ip, uint16_t port) :
    m_host(server_ip),
    m_port(port),
    m_timeout(50),
    m_io_context(),
    m_socket(m_io_context)
{

    using boost::asio::ip::udp;
    udp::resolver resolver(m_io_context);
    m_server_endpoint= *resolver.resolve(udp::v4(), m_host, std::to_string(m_port)).begin();

    m_socket.open(udp::v4());
    m_socket.non_blocking(true);

}

std::vector<uint8_t>
AMCProtocolClient::send_request(TFTPOpCode opcode, const std::vector<uint8_t>& payload) {

    // Build TFTP RRQ or WRQ packet
    // Switch to uin8_t
    std::vector<uint8_t> request;
    // request.push_back(static_cast<char>(opcode >> 8));
    // request.push_back(static_cast<char>(opcode & 0xFF));
    // append_bigendian(request, opcode);
    append_big_uint16(request, opcode);
    request.insert( request.end(), payload.begin(), payload.end());


    for (size_t i = 0; i < request.size(); ++i) {
        printf("%02x ", static_cast<uint8_t>(request[i]));
    }
    m_socket.send_to(boost::asio::buffer(request), m_server_endpoint);

    std::vector<uint8_t> reply(516); // TFTP packets max ~516 bytes

    boost::asio::ip::udp::endpoint sender_endpoint;
    boost::system::error_code ec;

    size_t len = 0;
    for (int i = 0; i < m_timeout; ++i) { // wait up to ~5 seconds total
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        len = m_socket.receive_from(boost::asio::buffer(reply), sender_endpoint, 0, ec);
        if (!ec) break;
    }

    if (ec) {
        throw AMCProtocolIssue(ERS_HERE, m_log_prefix, "TFTP receive error: " + ec.message());
    }

    if (len < 4) {
        throw AMCProtocolIssue(ERS_HERE, m_log_prefix, "Invalid TFTP reply: too short");
    }

    // uint16_t response_opcode = (static_cast<uint8_t>(reply[0]) << 8) | static_cast<uint8_t>(reply[1]);

    // if (response_opcode == DAT) {
    //     // printf("\nReceived reply: ");
    //     // for (size_t i = 0; i < len; ++i) {
    //     //     printf("%02x ", static_cast<unsigned uint8_t>(reply[i]));
    //     // }
    //     // DATA packet
    //     // Data starts at byte 3
    //     reply.resize(len);
    //     // Remove opcode
    //     reply.erase(reply.begin(), reply.begin() + 2);
    //     printf("\nReceived payload: ");
    //     for (size_t i = 0; i < reply.size(); ++i) {
    //         printf("%02x ", static_cast<uint8_t>(reply[i]));
    //     }

    // } else if (response_opcode == ACK) {
    //   // Do nothing
    // } else if (response_opcode == ERR) {
    //     // ERROR packet
    //     throw std::runtime_error("TFTP server error: " + std::string(reply.begin() + 4, reply.end()));
    // } else {
    //     throw std::runtime_error("Unexpected TFTP opcode: " + std::to_string(response_opcode));
    // }

    // return reply;


    if (reply.size() < 4)
        throw std::runtime_error("Packet too short to be valid");

    // Parse returin code
    boost::endian::big_uint16_t rpl_opcode_be;
    std::memcpy(&rpl_opcode_be, reply.data(), sizeof(rpl_opcode_be));

    // A bit of overcasting here?
    TFTPOpCode rpl_opcode = static_cast<TFTPOpCode>(static_cast<uint16_t>(rpl_opcode_be));

    switch (rpl_opcode) {
        case TFTPOpCode::DAT: {
            if (reply.size() < sizeof(TFTP_Data_Header))
                throw AMCProtocolIssue(ERS_HERE, m_log_prefix, "Incomplete DATA packet");

            TFTP_Data_Header header;
            std::memcpy(&header, reply.data(), sizeof(header));

            TLOG() << "Received DATA packet:\n" <<
                        "  Block #: "<< static_cast<uint16_t>(header.block) << "\n" <<
                        "  Payload size: "<< reply.size() - sizeof(header) <<" bytes\n"; 

            // Data starts at byte 3
            reply.resize(len);
            // Remove opcode
            reply.erase(reply.begin(), reply.begin() + 2);

            return reply;
        }

        case TFTPOpCode::ACK: {
            TFTP_Ack_Header header;
            std::memcpy(&header, reply.data(), sizeof(header));

            ers::info(AMCResponseACK(ERS_HERE, m_log_prefix, static_cast<uint16_t>(header.block)));
            // fmt::print("Received ACK packet:\n");
            // fmt::print("  Block #: {}\n", static_cast<uint16_t>(header.block));
            
            return {};
        }

        case TFTPOpCode::ERR: {
            TFTP_Error_Header header;
            std::memcpy(&header, reply.data(), sizeof(header));

            std::string error_msg(reinterpret_cast<const char*>(reply.data() + sizeof(header)),
                                  reply.size() - sizeof(header));

            ers::error(AMCResponseErr(ERS_HERE, m_log_prefix, static_cast<uint16_t>(header.error_code), error_msg));
            // fmt::print("Received ERROR packet:\n");
            // fmt::print("  Error code: {}\n", static_cast<uint16_t>(header.error_code));
            // fmt::print("  Message: {}\n", error_msg);
            
            return {};
        }

        default:
            ers::error(AMCUnknownOpCode(ERS_HERE, m_log_prefix, static_cast<uint16_t>(opcode)));
            // fmt::print("Unsupported or unexpected opcode: {}\n", static_cast<uint16_t>(opcode));

        return {};
    }
}




} // namespace tdemodules
} // namespace dunedaq

