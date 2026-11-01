#!/bin/bash
# netem profiles on the client<->server veth link. netem is applied on BOTH ends' egress:
# delay = RTT/2 each way, loss/loss-model applied per direction. Usable as `netem.sh <profile> [args]` or sourced.
half() { awk -v r="$1" 'BEGIN{printf "%g", r/2}'; }
apply() {  # apply <netem args...> on both ends
  netem_clear   # del+add: `replace` would keep stale params (e.g. rate) from the previous profile
  ip netns exec client tc qdisc add dev veth-c root netem "$@"
  ip netns exec server tc qdisc add dev veth-s root netem "$@"
}
netem_clear() {
  ip netns exec client tc qdisc del dev veth-c root 2>/dev/null || true
  ip netns exec server tc qdisc del dev veth-s root 2>/dev/null || true
}
# static <rtt_ms> <loss_pct>   (uniform random loss; 1gbit link rate - without a rate cap QUIC's line-rate bursts
# overflow the client's 208KB UDP rcvbuf (RcvbufErrors => phantom loss that only hits h3))
netem_static() {
  local d; d=$(half "$1"); local a=(delay "${d}ms" rate 1gbit)
  awk -v l="$2" 'BEGIN{exit !(l>0)}' && a+=(loss "${2}%")
  apply "${a[@]}"
}
# loss_burst <avg_loss_pct> <r_pct> [rtt_ms=0] [rate]
# Gilbert-Elliott with 1-h=100%, 1-k=0%: bad-state prob = p/(p+r) = avg loss  =>  p = r*avg/(100-avg)
netem_loss_burst() {
  local avg=$1 r=$2 rtt=${3:-0} rate=$4
  local p; p=$(awk -v a="$avg" -v r="$r" 'BEGIN{printf "%.4f", r*a/(100-a)}')
  local a=(); [ "$rtt" != 0 ] && a+=(delay "$(half "$rtt")ms")
  a+=(loss gemodel "${p}%" "${r}%" 100% 0%)
  [ -n "$rate" ] && a+=(rate "$rate")
  apply "${a[@]}"
}
# india_4g / india_5g: RTT, jitter and bandwidth CALIBRATED from real measurements (ping -c100 + Speedtest on Airtel,
# 28 Oct 2026; evidence in docs/Network_Measurement_Evidence.docx). LOSS IS MODELED, not measured: ICMP loss was 0% on both
# networks, so a modest loss component (5G 0.3% uniform, 4G 1% bursty) is kept to represent bursty application-layer loss.
# Values are per direction (apply() puts them on both ends): 5G 24ms +-10ms each way (measured RTT 48.1ms, mdev 20.2ms),
# 4G 25ms +-14ms each way (measured RTT 50.5ms, mdev 27.4ms). 4G loss is Gilbert-Elliott with 1% AVERAGE loss, r=20%: netem's
# first gemodel arg is the good->bad transition prob p, so p = r*avg/(100-avg) = 20*1/99 (a literal "gemodel 1% 20%" would
# give ~4.8% avg loss).
netem_india_4g() {
  local p; p=$(awk 'BEGIN{printf "%.4f", 20*1/99}')
  apply delay 25ms 14ms distribution normal loss gemodel "${p}%" 20% 100% 0% rate 22mbit
}
netem_india_5g() { apply delay 24ms 10ms distribution normal loss 0.3% rate 35mbit; }
# india_4g_congested (my choice): ~120ms +-80ms RTT, bursty ~3% avg loss (r=15%), 5mbit
netem_india_4g_congested() {
  local p; p=$(awk 'BEGIN{printf "%.4f", 15*3/97}')
  apply delay 60ms 40ms distribution normal loss gemodel "${p}%" 15% 100% 0% rate 5mbit
}
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  f="netem_$1"; shift
  declare -F "$f" >/dev/null || { echo "unknown profile; use: static loss_burst india_4g india_5g india_4g_congested clear" >&2; exit 2; }
  "$f" "$@"
fi
