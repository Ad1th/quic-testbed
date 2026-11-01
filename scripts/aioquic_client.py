#!/usr/bin/env python3
"""Secondary HTTP/3 client (aioquic) - cross-check that h3 results are not a curl/ngtcp2 artefact.
Run inside the client netns:  ip netns exec client python3 aioquic_client.py https://10.0.0.2/1MB.bin
Prints: handshake_s ttfb_s total_s bytes   (exit 1 on failure/timeout)."""
import asyncio, os, ssl, sys, time
from urllib.parse import urlparse
from aioquic.asyncio.client import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import DataReceived, HeadersReceived
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import ProtocolNegotiated

CERT = os.path.expanduser("~/srv/certs/server.crt")


class Client(QuicConnectionProtocol):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.h3 = None; self.waiter = None; self.n = 0; self.t_first = None; self.t_hs = None

    def quic_event_received(self, event):
        if isinstance(event, ProtocolNegotiated):
            self.h3 = H3Connection(self._quic); self.t_hs = time.time()
        if self.h3:
            for e in self.h3.handle_event(event):
                if isinstance(e, HeadersReceived) and self.t_first is None:
                    self.t_first = time.time()
                if isinstance(e, DataReceived):
                    self.n += len(e.data)
                    if e.stream_ended and not self.waiter.done():
                        self.waiter.set_result(None)

    async def get(self, host, path):
        sid = self._quic.get_next_available_stream_id()
        self.h3.send_headers(sid, [(b":method", b"GET"), (b":scheme", b"https"), (b":authority", host.encode()),
                                   (b":path", path.encode())], end_stream=True)
        self.waiter = asyncio.get_event_loop().create_future()
        self.transmit()
        await self.waiter


async def main(url, max_time):
    u = urlparse(url)
    cfg = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN, cafile=CERT, server_name=u.hostname)
    t0 = time.time()
    async with connect(u.hostname, u.port or 443, configuration=cfg, create_protocol=Client) as c:
        await asyncio.wait_for(c.get(u.hostname, u.path or "/"), max_time)
        t1 = time.time()
        print(f"{c.t_hs - t0:.6f} {c.t_first - t0:.6f} {t1 - t0:.6f} {c.n}")


if __name__ == "__main__":
    mt = float(sys.argv[2]) if len(sys.argv) > 2 else 40
    try:
        asyncio.run(main(sys.argv[1], mt))
    except Exception as e:
        print("error:", repr(e), file=sys.stderr); sys.exit(1)
