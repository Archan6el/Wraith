#ifndef PACKET_H
#define PACKET_H

#include <stdint.h>

#define MAGIC_BYTES 0x0b1e55ed
#define C2_PORT 6969

#define CMD_PING 0x01

struct packet_header {
    uint32_t magic;
    uint32_t command;
    uint32_t cmd_len;
};

#endif 