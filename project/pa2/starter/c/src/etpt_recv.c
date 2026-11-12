/*
 * etpt_recv.c -- the PA2 bulk-transfer receiver. GIVEN: you do not need to change it.
 *
 *     ./etpt-recv --port PORT --out FILE [--bind ADDR]
 *
 * Accepts one ETP-T session, reads an 8-byte big-endian length and then that
 * many bytes, expects the peer to close, writes FILE, closes, and prints one
 * ETPT-RECV statistics line (Specification, Section 10).
 * Exit status: 0 success; 2 anything else.
 */
#include <getopt.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "transport.h"

#define MAX_FILE (1ULL << 30)

static void usage(void)
{
    fprintf(stderr, "usage: etpt-recv --port PORT --out FILE [--bind ADDR]\n");
    exit(2);
}

int main(int argc, char **argv)
{
    const char *out = NULL, *bind_addr = "127.0.0.1";
    long port = -1;
    static const struct option opts[] = {
        {"port", required_argument, 0, 'p'}, {"out", required_argument, 0, 'o'},
        {"bind", required_argument, 0, 'b'}, {0, 0, 0, 0}};
    int ch;
    while ((ch = getopt_long(argc, argv, "", opts, NULL)) != -1) {
        switch (ch) {
        case 'p': port = strtol(optarg, NULL, 10); break;
        case 'o': out = optarg; break;
        case 'b': bind_addr = optarg; break;
        default: usage();
        }
    }
    if (out == NULL || port < 1 || port > 65535)
        usage();

    tp_listener *l = tp_listen(bind_addr, (uint16_t)port);
    if (l == NULL) {
        fprintf(stderr, "etpt-recv: cannot listen on %s:%ld\n", bind_addr, port);
        return 2;
    }
    char peer[64];
    tp_conn *c = tp_accept(l, peer, sizeof peer);
    if (c == NULL) {
        fprintf(stderr, "etpt-recv: accept failed\n");
        return 2;
    }
    uint8_t hdr[8];
    if (tp_recv_exact(c, hdr, 8) != 1) {
        fprintf(stderr, "etpt-recv: the stream ended before the length arrived\n");
        return 2;
    }
    uint64_t size = 0;
    for (int i = 0; i < 8; i++)
        size = (size << 8) | hdr[i];
    if (size > MAX_FILE) {
        fprintf(stderr, "etpt-recv: announced size %llu is too large\n", (unsigned long long)size);
        return 2;
    }
    uint8_t *data = malloc(size > 0 ? (size_t)size : 1);
    if (data == NULL) {
        fprintf(stderr, "etpt-recv: out of memory\n");
        return 2;
    }
    if (size > 0 && tp_recv_exact(c, data, (size_t)size) != 1) {
        fprintf(stderr, "etpt-recv: the stream ended before the whole file arrived\n");
        return 2;
    }
    uint8_t extra;
    int r = tp_recv_exact(c, &extra, 1);
    if (r == 1) {
        fprintf(stderr, "etpt-recv: the sender sent more bytes than it announced\n");
        return 2;
    }
    if (r < 0) {
        fprintf(stderr, "etpt-recv: the stream ended part-way, or the sender stopped responding\n");
        return 2;
    }
    FILE *f = fopen(out, "wb");
    if (f == NULL || (size > 0 && fwrite(data, 1, (size_t)size, f) != (size_t)size)) {
        perror("etpt-recv: cannot write output");
        return 2;
    }
    fclose(f);
    tp_close(c);
    tp_stats_t st;
    tp_stats(c, &st);
    tp_free_conn(c);
    tp_close_listener(l);
    free(data);
    printf("ETPT-RECV bytes=%llu segments_received=%lu duplicates=%lu out_of_order=%lu "
           "checksum_failures=%lu invalid=%lu acks_sent=%lu\n",
           (unsigned long long)size, st.segments_received, st.duplicates, st.out_of_order,
           st.checksum_failures, st.invalid, st.acks_sent);
    fflush(stdout);
    return 0;
}
