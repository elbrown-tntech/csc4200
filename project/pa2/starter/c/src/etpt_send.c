/*
 * etpt_send.c -- the PA2 bulk-transfer sender. GIVEN: you do not need to change it.
 *
 *     ./etpt-send --host HOST --port PORT --file FILE [--window W]
 *
 * Sends FILE over ETP-T using only the transport seam (transport.h), framed as
 * an 8-byte big-endian length followed by the file's bytes, then closes.
 * Prints one ETPT-SEND statistics line (Specification, Section 10).
 * Exit status: 0 success; 2 anything else.
 */
#include <getopt.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "transport.h"

static double mono(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

static void usage(void)
{
    fprintf(stderr, "usage: etpt-send --host HOST --port PORT --file FILE [--window W]\n");
    exit(2);
}

int main(int argc, char **argv)
{
    const char *host = NULL, *path = NULL;
    long port = -1, window = 8;
    static const struct option opts[] = {
        {"host", required_argument, 0, 'h'}, {"port", required_argument, 0, 'p'},
        {"file", required_argument, 0, 'f'}, {"window", required_argument, 0, 'w'},
        {0, 0, 0, 0}};
    int ch;
    while ((ch = getopt_long(argc, argv, "", opts, NULL)) != -1) {
        switch (ch) {
        case 'h': host = optarg; break;
        case 'p': port = strtol(optarg, NULL, 10); break;
        case 'f': path = optarg; break;
        case 'w': window = strtol(optarg, NULL, 10); break;
        default: usage();
        }
    }
    if (host == NULL || path == NULL || port < 1 || port > 65535 || window < 1 || window > 1024)
        usage();

    FILE *f = fopen(path, "rb");
    if (f == NULL) {
        perror("etpt-send: cannot read file");
        return 2;
    }
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (size < 0) {
        perror("etpt-send: cannot size file");
        fclose(f);
        return 2;
    }
    uint8_t *buf = malloc((size_t)size + 8);
    if (buf == NULL) {
        fprintf(stderr, "etpt-send: out of memory\n");
        fclose(f);
        return 2;
    }
    for (int i = 0; i < 8; i++)                       /* 8-byte big-endian length */
        buf[i] = (uint8_t)((uint64_t)size >> (56 - 8 * i));
    if (size > 0 && fread(buf + 8, 1, (size_t)size, f) != (size_t)size) {
        fprintf(stderr, "etpt-send: short read\n");
        return 2;
    }
    fclose(f);

    tp_set_window((int)window);
    tp_conn *c = tp_connect(host, (uint16_t)port);
    if (c == NULL) {
        fprintf(stderr, "etpt-send: transfer failed: no answer from %s:%ld\n", host, port);
        return 2;
    }
    double t0 = mono();
    if (tp_send_all(c, buf, (size_t)size + 8) != 0) {
        fprintf(stderr, "etpt-send: transfer failed: peer is not responding\n");
        return 2;
    }
    double seconds = mono() - t0;
    tp_close(c);
    tp_stats_t st;
    tp_stats(c, &st);
    tp_free_conn(c);
    free(buf);
    if (seconds < 1e-6)
        seconds = 1e-6;
    printf("ETPT-SEND bytes=%ld seconds=%.4f goodput_kbps=%.1f window=%ld segments_sent=%lu "
           "retransmissions=%lu timeouts=%lu rtt_samples=%lu srtt_ms=%.1f rto_ms=%.1f "
           "checksum_failures=%lu\n",
           size, seconds, (double)size * 8.0 / seconds / 1000.0, window, st.segments_sent,
           st.retransmissions, st.timeouts, st.rtt_samples, st.srtt_ms, st.rto_ms,
           st.checksum_failures);
    fflush(stdout);
    return 0;
}
