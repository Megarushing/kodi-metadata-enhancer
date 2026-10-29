import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "service.metadataenhancer"))
from resources.lib import oshash  # noqa: E402


def reference(path):
    # verbatim shape of the Python sample on the OpenSubtitles HashSourceCodes wiki
    fmt = "<q"
    bs = struct.calcsize(fmt)
    with open(path, "rb") as f:
        size = os.path.getsize(path)
        h = size
        for _ in range(65536 // bs):
            (v,) = struct.unpack(fmt, f.read(bs))
            h = (h + v) & 0xFFFFFFFFFFFFFFFF
        f.seek(max(0, size - 65536), 0)
        for _ in range(65536 // bs):
            (v,) = struct.unpack(fmt, f.read(bs))
            h = (h + v) & 0xFFFFFFFFFFFFFFFF
    return "%016x" % h


class LocalFile:
    def __init__(self, path):
        self.f = open(path, "rb")

    def size(self):
        return os.fstat(self.f.fileno()).st_size

    def read(self, n):
        return self.f.read(n)

    def seek(self, pos):
        self.f.seek(pos)

    def close(self):
        self.f.close()


class OshashTest(unittest.TestCase):
    def _file(self, size):
        fd, p = tempfile.mkstemp()
        with os.fdopen(fd, "wb") as f:
            f.write(os.urandom(size))
        self.addCleanup(os.remove, p)
        return p

    def test_matches_reference(self):
        for size in (131072, 131073, 5 * 1024 * 1024 + 7):
            p = self._file(size)
            self.assertEqual(oshash.hash_file(p, LocalFile), (size, reference(p)))

    def test_too_small(self):
        p = self._file(131071)
        self.assertEqual(oshash.hash_file(p, LocalFile), (131071, None))

    def test_short_read_gives_none(self):
        self.assertIsNone(oshash.compute(200000, b"\0" * 65536, b"\0" * 100))


if __name__ == "__main__":
    unittest.main()
