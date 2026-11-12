/*
 * transport.h -- the transport seam (ETP/1 Specification, Section 11).
 * CSC 4200/5200 PA1 starter (C).
 *
 * Your server, client and protocol code reach the network ONLY through these
 * functions. Socket calls live in transport_tcp.c and nowhere else. In the
 * final project you will write transport_etpt.c with the same interface over
 * your PA2 transport and link it instead.
 *
 * You may change these signatures to suit your design. Keep the operations,
 * keep them in files whose names begin with "transport", and keep every
 * socket call inside those files.
 */
#ifndef TRANSPORT_H
#define TRANSPORT_H

#include <stddef.h>
#include <stdint.h>

typedef struct tp_listener tp_listener;   /* opaque: defined in transport_tcp.c */
typedef struct tp_conn tp_conn;           /* opaque: defined in transport_tcp.c */

/* Start accepting sessions on bind_addr:port. NULL on failure.
 * Remember SO_REUSEADDR (Specification, Section 9). */
tp_listener *tp_listen(const char *bind_addr, uint16_t port);

/* Wait for the next session. Writes "ip:port" of the peer into peer[peerlen].
 * NULL on failure. */
tp_conn *tp_accept(tp_listener *l, char *peer, size_t peerlen);

/* Open a session to host:port. NULL on failure. */
tp_conn *tp_connect(const char *host, uint16_t port);

/* Send all n bytes. Returns 0 on success, -1 on failure. Never a partial send.
 * Must not kill the process if the peer has gone (think SIGPIPE). */
int tp_send_all(tp_conn *c, const void *buf, size_t n);

/* Receive exactly n bytes into buf.
 * Returns  1  when all n bytes arrived,
 *          0  when the peer closed cleanly before ANY byte arrived,
 *         -1  on error, or when the peer closed part-way through. */
int tp_recv_exact(tp_conn *c, void *buf, size_t n);

/* Close the session gracefully and free it: shut down the sending side, read
 * and discard anything still arriving until end-of-stream (or about a second
 * passes), then close. Specification, Section 8.2 explains why. */
void tp_close(tp_conn *c);

/* Housekeeping: stop listening and free the listener. */
void tp_close_listener(tp_listener *l);

#endif
