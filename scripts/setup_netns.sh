#!/bin/bash
# Idempotent: (re)creates netns client/server joined by veth-c <-> veth-s (10.0.0.1 <-> 10.0.0.2).
# Needs CAP_NET_ADMIN; testbed.sh provides it via an unprivileged user namespace, or run under sudo.
set -e
mkdir -p /run/netns
ip netns del client 2>/dev/null || true
ip netns del server 2>/dev/null || true
ip netns add client; ip netns add server
ip link add veth-c type veth peer name veth-s
ip link set veth-c netns client; ip link set veth-s netns server
ip netns exec client ip addr add 10.0.0.1/24 dev veth-c
ip netns exec server ip addr add 10.0.0.2/24 dev veth-s
for ns in client server; do ip netns exec $ns ip link set lo up; done
ip netns exec client ip link set veth-c up
ip netns exec server ip link set veth-s up
