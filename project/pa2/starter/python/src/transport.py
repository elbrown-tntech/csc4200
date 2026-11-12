"""The transport your programs use. ONE line decides which one it is.

etpt_send.py and etpt_recv.py import this module, never transport_etpt
directly. In the final project, your PA1 ETP/1 programs will import a module
like this one that selects transport_etpt, and nothing else in them changes.
That is the transport seam (ETP/1 Specification, Section 11).
"""
from transport_etpt import *            # noqa: F401,F403  (PA2: ETP-T over UDP)
