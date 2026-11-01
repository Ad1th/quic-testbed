#!/usr/bin/env python3
"""Tiny pcap writer (AF_PACKET) - tcpdump cannot drop privileges inside the rootless user namespace.
usage (inside client netns): pcap_capture.py <iface> <out.pcap>   ; stop with SIGTERM."""
import signal, socket, struct, sys, time
iface, out = sys.argv[1], sys.argv[2]
s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)); s.bind((iface, 0))
f = open(out, "wb"); f.write(struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))
signal.signal(signal.SIGTERM, lambda *a: (f.close(), sys.exit(0)))
while True:
    pkt, _ = s.recvfrom(65535); t = time.time()
    f.write(struct.pack("<IIII", int(t), int((t % 1) * 1e6), len(pkt), len(pkt))); f.write(pkt); f.flush()
