#!/bin/bash
# Phase 7: capture one h2 and one h3 request (fresh connection) with tcpdump + TLS key log.
# usage: scripts/testbed.sh scripts/capture_handshake.sh [rtt_ms=100]
D=$(cd "$(dirname "$0")/.." && pwd)
RTT=${1:-100}
OUT=$D/data/captures
source "$D/scripts/netem.sh"
netem_static "$RTT" 0
export SSLKEYLOGFILE=$OUT/keys.log
: > "$SSLKEYLOGFILE"
: > "$OUT/handshake_timing.txt"
CURL=$HOME/.local/bin/curl; CERT=$HOME/srv/certs/server.crt
for p in h2 h3; do
  flag=--http2; [ $p = h3 ] && flag=--http3-only
  ip netns exec client python3 "$D/scripts/pcap_capture.py" veth-c "$OUT/$p.pcap" &
  TP=$!; sleep 1
  ip netns exec client $CURL -s -o /dev/null --cacert "$CERT" $flag \
    -w "$p rtt=${RTT}ms connect=%{time_connect} handshake=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total} http=%{http_version}\n" \
    https://10.0.0.2/1MB.bin | tee -a "$OUT/handshake_timing.txt"
  sleep 1; kill $TP; wait $TP 2>/dev/null
done
netem_clear
