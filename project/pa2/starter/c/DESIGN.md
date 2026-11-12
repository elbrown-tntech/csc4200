# PA2 Design — ETP-T

_One to two pages. Short, specific answers beat long general ones. Every section
should be true of the code you submit. Delete these italic prompts when you write._

## 1. Architecture

_Which file holds the segment codec, which holds the transport, and what calls
what. Where is the one loop that waits for a datagram or a timer? Which state
does a connection keep for sending, and which for receiving?_

## 2. Segments and the checksum

_How you build and check a segment. Where the checks of Specification §6.1
happen, and in what order. How you tested your checksum before you trusted it._

## 3. The sender: window, timer, Go-Back-N

_How the window opens and slides. When the timer starts, restarts and stops.
What exactly happens on a timeout. What happens to an ACK that is old, repeated
or corrupted._

## 4. The retransmission timeout

_How you compute SRTT, RTTVAR and RTO. Which segments give RTT samples and which
do not (Karn), and how you know. How the RTO behaves after a timeout._

## 5. The receiver

_In-order delivery, cumulative ACKs, and what you do with duplicates and
out-of-order segments (discard or buffer — say which, and why)._

## 6. Opening and closing

_SYN and its ACK; FIN in each direction; the linger. What goes wrong if a SYN,
a FIN or the last ACK is lost, and how your code copes. Name one weakness of
starting every connection at segment 0, and who could exploit it._

## 7. Toward the project

_In the project your PA1 ETP/1 client and server run over this transport. What
already works in both directions, and what you would still have to change? Name
one thing your PA1 code assumed about TCP that ETP-T does differently._

## 8. Testing

_What did you test beyond `make check`? How? Name one bug your testing found,
how you found it, and the fix._
