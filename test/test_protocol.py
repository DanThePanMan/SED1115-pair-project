import unittest
from src.protocol import escape_content, unescape_content, _frame_escape, _frame_header

class TestEscapeFunctions(unittest.TestCase):
    def test_no_escapes(self):
        data = b"Hello, world!"
        escaped = escape_content(data)
        unescaped = unescape_content(escaped)

        self.assertEqual(escaped, data)
        self.assertEqual(escaped, unescaped)
        
    def test_escaped_header(self):
        data = b"Hello,%b World!" % _frame_header.to_bytes()

        escaped = escape_content(data)
        unescaped = unescape_content(escaped)

        self.assertNotEqual(escaped, data)
        self.assertEqual(data, unescaped)

    def test_escaped_escape(self):
        data = b"Hello,%b World!" % _frame_escape.to_bytes()

        escaped = escape_content(data)
        unescaped = unescape_content(escaped)

        self.assertNotEqual(escaped, data)
        self.assertEqual(data, unescaped)

    def test_escaped_on_bounds(self):
        data = b"%bHello, world%b" % (_frame_escape.to_bytes(), _frame_header.to_bytes())

        escaped = escape_content(data)
        unescaped = unescape_content(escaped)

        self.assertNotEqual(escaped, data)
        self.assertEqual(data, unescaped)