// Minimal HTTP/3 static file server on quic-go: a third, independent QUIC sender (Go, mature, used in production by
// e.g. Caddy) to test whether HTTP/3's slowdown under loss is specific to nginx/ngtcp2 and aioquic.
// QLOGDIR=<dir> enables per-connection qlog.
package main

import (
	"flag"
	"log"
	"net/http"

	"github.com/quic-go/quic-go"
	"github.com/quic-go/quic-go/http3"
	"github.com/quic-go/quic-go/qlog"
)

func main() {
	addr := flag.String("addr", "10.0.0.2:443", "listen address (UDP)")
	root := flag.String("root", "/srv/content", "document root")
	cert := flag.String("cert", "/srv/certs/server.crt", "certificate")
	key := flag.String("key", "/srv/certs/server.key", "private key")
	flag.Parse()
	srv := &http3.Server{
		Addr:       *addr,
		Handler:    http.FileServer(http.Dir(*root)),
		QUICConfig: &quic.Config{Tracer: qlog.DefaultConnectionTracer},
	}
	log.Printf("quic-go %s serving %s on %s", "http3", *root, *addr)
	log.Fatal(srv.ListenAndServeTLS(*cert, *key))
}
