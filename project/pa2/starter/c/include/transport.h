/*
 * transport.h -- the transport seam (ETP/1 Specification, Section 11), now
 * implemented over ETP-T (ETP-T Specification, Section 9).
 * CSC 4200/5200 PA2 starter (C).
 *
 * These are the same operations as PA1's transport.h, so in the final project
 * your ETP/1 server and client link transport_etpt.c instead of
 * transport_tcp.c and nothing else in them changes. Two helpers are added:
 * tp_set_window and tp_stats.
 */
#ifndef TRANSPORT_H
#define TRANSPORT_H

#include <stddef.h>
#include <stdint.h>

typedef struct tp_listener tp_listener;   /* opaque: defined in transport_etpt.c */
typedef struct tp_conn tp_conn;           /* opaque: defined in transport_etpt.c */

/* Counters and estimates (Specification, Section 10). */
typedef struct {
    unsigned long segments_sent;      /* SYN, data and FIN transmissions, retransmissions included */
    unsigned long retransmissions;
    unsigned long timeouts;
    unsigned long acks_sent;          /* pure ACKs */
    unsigned long rtt_samples;
    unsigned long segments_received;  /* valid SYN, data and FIN segments received */
    unsigned long duplicates;
    unsigned long out_of_order;
    unsigned long checksum_failures;
    unsigned long invalid;
    double        srtt_ms;            /* 0 if no sample yet */
    double        rto_ms;
} tp_stats_t;

/* The sender's window, in segments (1..1024), for connections connected or
 * accepted afterwards: call it before tp_connect or tp_accept. */
void tp_set_window(int w);

/* Bind a UDP socket on bind_addr:port. NULL on failure. */
tp_listener *tp_listen(const char *bind_addr, uint16_t port);

/* Wait for a SYN, acknowledge it, return the session. Writes "ip:port" of the
 * peer into peer[peerlen]. NULL on failure. */
tp_conn *tp_accept(tp_listener *l, char *peer, size_t peerlen);

/* Send a SYN until it is acknowledged. NULL if the peer never answers. */
tp_conn *tp_connect(const char *host, uint16_t port);

/* Returns 0 once every byte has been acknowledged, -1 if the peer stopped responding. */
int tp_send_all(tp_conn *c, const void *buf, size_t n);

/* Receive exactly n bytes into buf.
 * Returns  1  when all n bytes arrived,
 *          0  when the peer's FIN arrived before ANY of them (a clean close),
 *         -1  on error, or when the FIN arrived part-way through. */
int tp_recv_exact(tp_conn *c, void *buf, size_t n);

/* FIN, wait for it to be acknowledged, wait for the peer's FIN, linger, release. */
void tp_close(tp_conn *c);

/* Copy the session's counters. Valid until tp_free_conn. */
void tp_stats(const tp_conn *c, tp_stats_t *out);

/* Free a session after tp_close (and after reading its stats). */
void tp_free_conn(tp_conn *c);

/* Stop listening and free the listener. */
void tp_close_listener(tp_listener *l);

#endif
