#ifndef __DUNEDAQ_TDEMODULES_SRC_UTILITIES_HPP___
#define __DUNEDAQ_TDEMODULES_SRC_UTILITIES_HPP___

#include <vector>
#include <cstdint>

namespace dunedaq {
namespace tdemodules {

void append_big_uint16(std::vector<uint8_t>& buffer, uint16_t value);
void append_big_uint32(std::vector<uint8_t>& buffer, uint16_t value);

} // namespace tdemodules
} // namespace dunedaq

#endif // __DUNEDAQ_TDEMODULES_SRC_UTILITIES_HPP___