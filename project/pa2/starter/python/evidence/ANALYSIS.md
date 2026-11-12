# PA2 Analysis

_Your evidence is `evidence/measurements.csv` and `evidence/throughput.svg` (from
`make measure`) and `evidence/pa2-capture.pcap`. Every number below comes from
those files and from your own profile. Formulas and their symbols are in the
PA2 brief, Section 4.3._

## Our profile and how we measured

_Paste the output of `python3 ~/csc4200-course/project/pa2/etpt_relay.py
--show-profile OWNER` (the repository owner's username), the commit `make measure` recorded, and anything
unusual about your runs._

## Facts

_Fill in every value. Use your profile for the first five and your
measurements.csv for the last three. Decimal numbers to at least two decimal
places; units as named. Do not change the key names or the `etpt-facts` label:
a script reads this block._

```etpt-facts
profile_delay_ms:          # one-way delay d from your profile, ms
profile_rate_kbps:         # bottleneck rate R from your profile, kbit/s
d_trans_ms:                # transmission delay of one full segment, L/R, ms
sw_predicted_kbps:         # predicted stop-and-wait goodput, kbit/s
w_fill_segments:           # window that just fills the link, segments
sw_measured_kbps:          # median goodput at W = 1, loss 0, from your CSV
plateau_kbps:              # highest median goodput at loss 0, from your CSV
plateau_window:            # the W at which it occurred (on a tie, the smaller W)
```

## Q1. Your segments on the wire

_From your capture, decode the header of the SYN, of the ACK that answers it,
and of the first data segment, field by field (give the frame numbers). Then
verify the first data segment's checksum: show the one's-complement sum of the
eight 16-bit header words with CHECKSUM taken as zero, and combine it with the
payload's sum (your own code may compute that part; say so). Finally: UDP
already has a checksum, so why does ETP-T need its own? (Think about where the
relay sits.)_

## Q2. The window and the bandwidth-delay product

_Describe your loss-0 curve. Compare it, window by window, with
min(W x stop-and-wait goodput, bottleneck capacity for file data). Where does it
stop growing, and how does that compare with w_fill_segments? Your plateau is
what fraction of the capacity line, and where does the rest go?_

## Q3. Stop-and-wait

_Compare sw_measured_kbps with sw_predicted_kbps. Account for the difference:
what does the formula leave out that your real system does?_

## Q4. Loss, Go-Back-N and the queue

_How do 1% and 5% loss change goodput at small and large windows? Why does
Go-Back-N suffer more at large windows? Look at W = 128: what happened even at
loss 0? Use the fwd_dropped_queue and retransmissions columns, and say what a
sender would need to do to avoid it._

## Q5. The timer

_Using the srtt_ms and rto_ms columns, explain how your RTO relates to your round
trip at small windows and at W = 64, and why it changed. What does Karn's rule
protect against? What would happen in your profile with a fixed RTO of 20 ms,
and with a fixed RTO of 2 s?_
