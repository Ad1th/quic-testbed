#!/bin/bash
# testbed.sh <command...> : builds the namespaces (rootless, via user ns), starts nginx in `server`, runs the command, cleans up.
if [ -z "$IN_TESTBED" ]; then exec unshare -Urnm env IN_TESTBED=1 "$0" "$@"; fi
D=$(cd "$(dirname "$0")/.." && pwd)
mount -t tmpfs none /run
bash "$D/scripts/setup_netns.sh"
sed -e "s#@PROJECT@#$D#g" -e "s#@HOME@#$HOME#g" "$D/conf/nginx.conf" > "$D/logs/nginx.rendered.conf"
ip netns exec server "$HOME/.local/nginx/sbin/nginx" -p "$HOME/.local/nginx" -c "$D/logs/nginx.rendered.conf" -g "pid $D/logs/nginx-$$.pid;" &
NG=$!
trap 'kill $NG 2>/dev/null; wait $NG 2>/dev/null' EXIT
for i in $(seq 50); do ip netns exec client ping -c1 -W1 10.0.0.2 >/dev/null 2>&1 && break; sleep 0.1; done
sleep 1
"$@"
