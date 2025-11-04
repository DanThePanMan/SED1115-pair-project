# necessary for type checking on CPython target
# without affecting micropython 
if 0: from typing import Iterable

def split_packet(packet: bytes) -> list[str]:
    """
    Split a packet formatted as b'a1,a2,...,aN;' into ['a1', 'a2', ..., 'aN']
    """
    packet = packet[:-1]
    split = packet.split(b',')
    return list(map(lambda i: i.decode(), split))

def format_packet(packet: 'Iterable[str]') -> bytes:
    """
    Take a ['a1', 'a2', ..., 'aN'] packet and format it as b'a1,a2,...,aN;'
    """
    return f"{",".join(packet)};".encode("utf-8")