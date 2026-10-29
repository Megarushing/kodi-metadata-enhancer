"""OpenSubtitles movie hash: file size + 64-bit sum of the first and last 64 KiB.

Spec: https://trac.opensubtitles.org/projects/opensubtitles/wiki/HashSourceCodes
"""
import struct

CHUNK = 65536
_WORDS = CHUNK // 8


def _sum(buf):
    return sum(struct.unpack("<%dq" % _WORDS, buf))


def compute(size, head, tail):
    """size: file size in bytes; head/tail: the first and last CHUNK bytes.
    Returns the 16-hex hash, or None when the inputs can't make a valid one."""
    if size < CHUNK * 2 or len(head) != CHUNK or len(tail) != CHUNK:
        return None
    return "%016x" % ((size + _sum(head) + _sum(tail)) & 0xFFFFFFFFFFFFFFFF)


def hash_file(path, opener):
    """opener(path) -> object with size(), read(n), seek(pos) and close().
    Returns (size, hash or None)."""
    f = opener(path)
    try:
        size = f.size()
        if size < CHUNK * 2:
            return size, None
        head = f.read(CHUNK)
        f.seek(size - CHUNK)
        tail = f.read(CHUNK)
        return size, compute(size, head, tail)
    finally:
        f.close()
