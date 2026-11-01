#!/usr/bin/env python3
"""Minimal aioquic HTTP/3 server: GET anything -> N zero bytes. Used to test whether h3 slowness under loss is
specific to nginx's QUIC sender. Run in the server netns:  ip netns exec server python3 aioquic_server.py [port]"""
import asyncio, os, sys
from aioquic.asyncio import QuicConnectionProtocol, serve
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import HeadersReceived
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import ProtocolNegotiated

BODY = b"\0" * (1 << 20)
D = os.path.expanduser("~/srv/certs")

class Srv(QuicConnectionProtocol):
    h3 = None
    def quic_event_received(self, ev):
        if isinstance(ev, ProtocolNegotiated):
            self.h3 = H3Connection(self._quic)
        if self.h3:
            for e in self.h3.handle_event(ev):
                if isinstance(e, HeadersReceived):
                    self.h3.send_headers(e.stream_id, [(b":status", b"200"), (b"content-length", str(len(BODY)).encode())])
                    self.h3.send_data(e.stream_id, BODY, end_stream=True)
                    self.transmit()

async def main(port):
    cfg = QuicConfiguration(is_client=False, alpn_protocols=H3_ALPN)
    cfg.load_cert_chain(f"{D}/server.crt", f"{D}/server.key")
    await serve("10.0.0.2", port, configuration=cfg, create_protocol=Srv)
    await asyncio.Event().wait()

asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 4433))
