"""The transport your programs use. ONE line decides which one it is.

server.py and client.py import this module, never transport_tcp directly. In the
final project you will change the import below to your PA2 transport, and
nothing else in your ETP code changes. That is the transport seam
(Specification, Section 11).
"""
from transport_tcp import *            # noqa: F401,F403  (PA1: TCP)
