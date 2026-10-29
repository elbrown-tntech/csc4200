/*
 * etp.h -- ETP/1 protocol constants and message helpers.
 * CSC 4200/5200 PA1 starter (C). Constants are copied from the ETP/1
 * Specification v1.0. The message functions are yours to design and write;
 * the prototypes below are a suggestion, not a requirement.
 */
#ifndef ETP_H
#define ETP_H

#include <stddef.h>
#include <stdint.h>

#include "transport.h"

#define ETP_VERSION      1
#define ETP_HEADER_SIZE  8
#define ETP_MAX_LEN      (16u * 1024u * 1024u)    /* 16,777,216 */

/* Message types (Specification, Section 4). A response is request | 0x80. */
enum {
    ETP_HELLO = 0x01, ETP_LIST = 0x02, ETP_GET = 0x03, ETP_PUT = 0x04, ETP_BYE = 0x05,
    ETP_HELLO_OK = 0x81, ETP_LIST_OK = 0x82, ETP_GET_OK = 0x83, ETP_PUT_OK = 0x84,
    ETP_BYE_OK = 0x85, ETP_ERROR = 0xFF
};

/* Error codes (Specification, Section 8), carried in STATUS. */
enum {
    ETP_E_BAD_VERSION = 1, ETP_E_BAD_TYPE = 2, ETP_E_NOT_FOUND = 3, ETP_E_BAD_NAME = 4,
    ETP_E_TOO_LARGE = 5, ETP_E_BAD_REQUEST = 6, ETP_E_NOT_READY = 7, ETP_E_SERVER_ERROR = 8
};

/* A decoded header. */
typedef struct {
    uint8_t  version;
    uint8_t  type;
    uint8_t  status;
    uint8_t  reserved;
    uint32_t length;          /* host byte order after decoding */
} etp_header;

/* Send one complete message (header + payload). 0 on success, -1 on failure. */
int etp_send(tp_conn *c, uint8_t type, uint8_t status, const void *payload, uint32_t len);

/* Read and decode one 8-byte header. Same return convention as tp_recv_exact.
 * Think about Specification Section 8.1: what must be checked before reading
 * the payload, and why? */
int etp_read_header(tp_conn *c, etp_header *h);

/* 1 if name[0..len) is a valid ETP file name (Specification, Section 7). */
int etp_valid_name(const uint8_t *name, size_t len);

/* SHA-256 of data[0..len) into out[32], via OpenSSL EVP. 0 on success. */
int etp_sha256(const void *data, size_t len, uint8_t out[32]);

#endif
