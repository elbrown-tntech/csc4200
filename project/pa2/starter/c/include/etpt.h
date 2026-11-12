/*
 * etpt.h -- ETP-T segment format: constants and codec.
 * CSC 4200/5200 PA2 starter (C). Constants are copied from the ETP-T
 * Specification v1.0. The functions in etpt.c are yours to write; the
 * prototypes are a suggestion, not a requirement.
 */
#ifndef ETPT_H
#define ETPT_H

#include <stddef.h>
#include <stdint.h>

#define ETPT_VERSION      1
#define ETPT_HEADER_SIZE  16
#define ETPT_MAX_PAYLOAD  1024

/* FLAGS bits (Specification, Section 3) */
#define ETPT_SYN 0x01
#define ETPT_ACK 0x02
#define ETPT_FIN 0x04

/* Timer and protocol constants (Specification, Section 6.4 and Table 2), seconds */
#define ETPT_INIT_RTO      0.5
#define ETPT_MIN_RTO       0.1
#define ETPT_MAX_RTO       2.0
#define ETPT_ALPHA         0.125
#define ETPT_BETA          0.25
#define ETPT_K             4.0
#define ETPT_MAX_RETRIES   8
#define ETPT_LINGER        2.0
#define ETPT_PEER_FIN_WAIT 10.0
#define ETPT_IDLE_TIMEOUT  30.0

/* A decoded segment. payload points into the datagram it was decoded from. */
typedef struct {
    uint8_t        flags;
    uint32_t       seq;
    uint32_t       ack;
    uint16_t       length;
    const uint8_t *payload;
} etpt_seg;

/* Results of etpt_decode, in the order of the checks in Section 6.1 */
enum { ETPT_OK = 0, ETPT_SHORT = 1, ETPT_BADSUM = 2, ETPT_BADHDR = 3 };

/* RFC 1071 Internet checksum of data[0..n): the one's complement of the
 * one's-complement sum of the 16-bit big-endian words (pad an odd byte with 0). */
uint16_t etpt_checksum(const void *data, size_t n);

/* Build one segment into out[0..ETPT_HEADER_SIZE + len). Returns its size. */
size_t etpt_encode(uint8_t *out, uint8_t flags, uint32_t seq, uint32_t ack,
                   const void *payload, uint16_t len);

/* Check and decode a received datagram. Returns ETPT_OK or the first problem. */
int etpt_decode(const uint8_t *dgram, size_t n, etpt_seg *seg);

#endif
