from scapy.all import *

cmd = b"hello"

# Have magic first
msg = (0x0b1e55ed).to_bytes(4, "big")
msg += (0x01).to_bytes(4, "big")
msg += len(cmd).to_bytes(4, "big")
msg += cmd
msg += b"\0"

# Craft a raw TCP packet with magic bytes as payload
pkt = IP(dst="172.30.48.197") / TCP(dport=7000, sport=54321, flags="PA") / Raw(load=msg)

send(pkt, iface="lo")
