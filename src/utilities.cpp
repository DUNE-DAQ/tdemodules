#include "utilities.hpp"
#include <boost/endian/arithmetic.hpp>


namespace dunedaq {
namespace tdemodules {

// Append a 16-bit big-endian value to a buffer
void append_big_uint16(std::vector<uint8_t>& buffer, uint16_t value) {
    boost::endian::big_uint16_t be_val = value;
    uint8_t temp[2];
    std::memcpy(temp, &be_val, sizeof(be_val));
    buffer.insert(buffer.end(), temp, temp + sizeof(be_val));
}

// Append a 32-bit big-endian value to a buffer
void append_big_uint32(std::vector<uint8_t>& buffer, uint32_t value) {
    boost::endian::big_uint32_t be_val = value;
    uint8_t temp[4];
    std::memcpy(temp, &be_val, sizeof(be_val));
    buffer.insert(buffer.end(), temp, temp + sizeof(be_val));
}

}
} // namespace dunedaq