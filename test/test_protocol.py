import unittest
from src.protocol.frame import *
from src.protocol.frame import _frame_header, _frame_header_escape, \
    _frame_escape, _frame_escape_escape, _frame_tail, _frame_tail_escape, \
    _create_general_frame
from src.protocol.util import Packet, FrameReader

class TestProtocol(unittest.TestCase):
    pass